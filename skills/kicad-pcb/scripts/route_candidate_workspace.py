#!/usr/bin/env python3
"""Grade one route candidate under immutable prepared-board rule authority.

Candidate-adjacent project/rule files are never trusted.  The helper creates a
fresh relocatable workspace, copies the candidate PCB under a new basename,
installs the exact prepared ``.kicad_pro`` and ``.kicad_dru`` sidecars, runs
the shared route-base, via-in-pad, physical-DRC and requested-connectivity
checks, then writes one receipt: ACCEPTED, REJECTED, or INCOMPLETE.

    route_candidate_workspace.py grade --prepared r0.kicad_pcb \
      --candidate r7.kicad_pcb --workspace 06_build/route/grades/r7 \
      --required-net I2C_SCL --required-net I2C_SDA
    route_candidate_workspace.py verify WORKSPACE/receipt.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import route_acceptance_core
import copper_graph
from process_runner import run_bounded


HARD_DRC_TYPES = {
    "annular_width", "board_edge", "clearance", "copper_edge_clearance",
    "diff_pair_uncoupled_length_too_long", "drill_out_of_range",
    "hole_clearance", "hole_to_hole", "shorting_items", "track_width",
    "through_hole_pad_without_hole", "via_diameter", "via_in_pad",
}

@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str


Runner = Callable[[list[str], Path], CommandResult]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    return {"sha256": sha256_file(path), "size": path.stat().st_size}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def _receipt_digest(receipt: dict[str, Any]) -> str:
    payload = copy.deepcopy(receipt)
    payload.pop("binding", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _run(command: list[str], cwd: Path, timeout_s: int = 300) -> CommandResult:
    """Adapt the repository's sole bounded process owner to this API."""
    completed = run_bounded(
        command, cwd=cwd, timeout_s=timeout_s,
        heartbeat_s=min(10.0, max(1.0, timeout_s / 4)),
        label="route-candidate-child", echo=False)
    return CommandResult(completed.returncode, completed.output)


def _check(status: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "detail": detail, **extra}


def _process_status(returncode: int) -> str:
    """0=pass, ordinary gate rejection=fail, tool/usage crash=incomplete."""
    return "PASS" if returncode == 0 else "FAIL" if returncode == 1 else "INCOMPLETE"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return value


def _materialize(prepared: Path, candidate: Path, workspace: Path,
                 mutation_baseline: Path | None = None) \
        -> tuple[Path, dict[str, Any]]:
    if workspace.exists():
        raise ValueError(f"workspace already exists; use a fresh path: {workspace}")
    if not prepared.is_file() or not candidate.is_file():
        raise ValueError("prepared and candidate PCB files must exist")
    sidecars = [prepared.with_suffix(".kicad_pro"),
                prepared.with_suffix(".kicad_dru")]
    missing = [path for path in sidecars if not path.is_file()]
    if missing:
        raise ValueError("prepared rule authority is incomplete; missing " +
                         ", ".join(str(path) for path in missing))

    workspace.mkdir(parents=True)
    baseline = workspace / "baseline.kicad_pcb"
    subject = workspace / "subject.kicad_pcb"
    shutil.copy2(prepared, baseline)
    shutil.copy2(candidate, subject)
    if mutation_baseline is not None:
        if not mutation_baseline.is_file():
            raise ValueError(
                f"mutation baseline PCB file is missing: {mutation_baseline}")
        shutil.copy2(mutation_baseline,
                     workspace / "mutation_baseline.kicad_pcb")
    for source in sidecars:
        shutil.copy2(source, workspace / f"baseline{source.suffix}")
        shutil.copy2(source, workspace / f"subject{source.suffix}")
    # Library tables are not rule authority, but copying a prepared sibling
    # table when present keeps model/library lookup reproducible without ever
    # accepting the candidate's potentially altered table.
    table = prepared.parent / "fp-lib-table"
    if table.is_file():
        shutil.copy2(table, workspace / table.name)
    origins = {
        "prepared": {"display_path": str(prepared), **_file_record(prepared)},
        "candidate": {"display_path": str(candidate), **_file_record(candidate)},
        "prepared_project": {"display_path": str(sidecars[0]),
                             **_file_record(sidecars[0])},
        "prepared_rules": {"display_path": str(sidecars[1]),
                           **_file_record(sidecars[1])},
    }
    if mutation_baseline is not None:
        origins["mutation_baseline"] = {
            "display_path": str(mutation_baseline),
            **_file_record(mutation_baseline),
        }
    return subject, origins


def _artifact_records(workspace: Path) -> dict[str, Any]:
    records = {}
    for path in sorted(workspace.iterdir()):
        if path.is_file() and path.name != "receipt.json":
            records[path.name] = _file_record(path)
    return records


def semantic_copper_evidence(prepared: Path, mutation_baseline: Path,
                             subject: Path,
                             touched_nets: list[str]) -> dict[str, Any]:
    """Compute both semantic shadows from one shared board inventory set.

    This helper is deliberately pure policy.  Its caller owns process
    isolation and timeout; promotion authority does not depend on it.
    """
    mutation_inventory = copper_graph.canonical_copper_inventory(
        mutation_baseline)
    prepared_inventory = (mutation_inventory if prepared == mutation_baseline
                          else copper_graph.canonical_copper_inventory(prepared))
    subject_inventory = copper_graph.canonical_copper_inventory(subject)
    return {
        "schema": 1,
        "kind": "route-semantic-copper-shadow-v1",
        "copper_delta": copper_graph.diff_copper(
            mutation_inventory, subject_inventory,
            touched=touched_nets if touched_nets else None),
        "source_copper_equivalence":
            copper_graph.source_owned_copper_equivalence(
                prepared_inventory, subject_inventory),
    }


def _semantic_copper_shadow(prepared: Path, mutation_baseline: Path,
                            subject: Path, workspace: Path,
                            touched_nets: list[str], kicad_python: str,
                            timeout_s: int) -> dict[str, Any]:
    report = workspace / "semantic_copper_shadow.json"
    command = [
        kicad_python, str(Path(__file__).resolve()), "semantic-copper",
        "--prepared", str(prepared),
        "--mutation-baseline", str(mutation_baseline),
        "--subject", str(subject), "--json", str(report),
    ]
    for net in touched_nets:
        command.extend(["--touched-net", net])
    completed = _run(command, workspace, timeout_s=timeout_s)
    if completed.returncode != 0:
        raise RuntimeError(
            completed.output[-2000:].strip() or
            f"semantic copper child exited {completed.returncode}")
    if not report.is_file():
        raise RuntimeError("semantic copper child wrote no JSON report")
    result = _read_json(report)
    if (result.get("kind") != "route-semantic-copper-shadow-v1" or
            not isinstance(result.get("copper_delta"), dict) or
            not isinstance(result.get("source_copper_equivalence"), dict)):
        raise ValueError("semantic copper child report is incomplete")
    return result


def grade_candidate(prepared: Path, candidate: Path, workspace: Path,
                    *, required_nets: list[str] | None = None,
                    touched_nets: list[str] | None = None,
                    mutation_baseline: Path | None = None,
                    shadow_native_drc: bool = False,
                    shadow_semantic_copper: bool = False,
                    semantic_copper_timeout_s: int = 120,
                    kicad_python: str = "/usr/bin/python3",
                    kicad_cli: str = "kicad-cli",
                    runner: Runner = _run) -> dict[str, Any]:
    prepared, candidate, workspace = (prepared.resolve(), candidate.resolve(),
                                      workspace.resolve())
    if workspace.exists():
        # An attempt directory is immutable evidence.  Reject a retry before
        # reading optional shadow inputs or writing even a diagnostic byte.
        raise ValueError(f"workspace already exists; use a fresh path: {workspace}")
    shadow_mutation_baseline: dict[str, Any] | None = None
    if mutation_baseline is not None:
        # Mutation scope is a pending shadow request.  Do not stat, open, or
        # hash it in the authoritative transaction's time budget.
        shadow_mutation_baseline = {
            "display_path": str(mutation_baseline),
            "status": "PENDING",
        }
    required_nets = sorted(set(required_nets or []))
    touched_nets = sorted(set(touched_nets or []))
    checks: dict[str, dict[str, Any]] = {}
    shadow_checks: dict[str, dict[str, Any]] = {}
    origins: dict[str, Any] = {}
    subject: Path | None = None
    scripts = Path(__file__).resolve().parent

    try:
        subject, origins = _materialize(prepared, candidate, workspace, None)
        prepared_local = workspace / "baseline.kicad_pcb"
        base = runner([kicad_python, str(scripts / "promoted_route_check.py"),
                       "--prepared", str(prepared_local),
                       "--chain", str(subject)],
                      workspace)
        checks["route_base"] = _check(
            _process_status(base.returncode),
            base.output[-2000:].strip() or f"exit {base.returncode}",
            process_exit=base.returncode)

        via_report = workspace / "via_in_pad.json"
        via = runner([kicad_python, str(scripts / "via_in_pad_guard.py"),
                      str(prepared_local), str(subject), "--json",
                      str(via_report)],
                     workspace)
        if not via_report.is_file():
            via_status = "INCOMPLETE"
        else:
            via_payload = _read_json(via_report)
            via_process = _process_status(via.returncode)
            via_status = ("INCOMPLETE" if via_process == "INCOMPLETE" else
                          "FAIL" if (via_process == "FAIL" or
                                     via_payload.get("verdict") != "PASS") else
                          "PASS")
        checks["via_in_pad"] = _check(
            via_status,
            via.output[-2000:].strip() or f"exit {via.returncode}",
            process_exit=via.returncode)

        # Preserve the exact legacy candidate invocation and hard-finding
        # predicate as admission authority during migration.
        drc_report = workspace / "physical_drc.json"
        drc = runner([
            kicad_cli, "pcb", "drc", "--severity-all", "--format", "json", "-o",
            str(drc_report), str(subject)], workspace)
        if not drc_report.is_file():
            checks["physical_drc"] = _check(
                "INCOMPLETE", "kicad-cli wrote no JSON report",
                process_exit=drc.returncode)
        else:
            payload = _read_json(drc_report)
            hits = [row for row in payload.get("violations", [])
                    if row.get("type") in HARD_DRC_TYPES]
            process = _process_status(drc.returncode)
            status = ("INCOMPLETE" if process == "INCOMPLETE" else
                      "FAIL" if hits or process == "FAIL" else "PASS")
            checks["physical_drc"] = _check(
                status,
                (f"{len(hits)} hard / {len(payload.get('violations', []))} "
                 "partial-stage violation(s)"),
                hard_types=sorted({str(row.get("type")) for row in hits}),
                process_exit=drc.returncode)

        if required_nets:
            connectivity_report = workspace / "connectivity.json"
            command = [kicad_python, str(Path(__file__).resolve()),
                       "connectivity", str(subject), "--json",
                       str(connectivity_report)]
            for net in required_nets:
                command.extend(["--net", net])
            connected = runner(command, workspace)
            if not connectivity_report.is_file():
                checks["connectivity"] = _check(
                    "INCOMPLETE", "connectivity checker wrote no JSON report",
                    process_exit=connected.returncode)
            else:
                payload = _read_json(connectivity_report)
                connected_process = _process_status(connected.returncode)
                connected_status = (
                    "INCOMPLETE" if connected_process == "INCOMPLETE" else
                    "FAIL" if (connected_process == "FAIL" or
                               payload.get("verdict") != "PASS") else "PASS")
                checks["connectivity"] = _check(
                    connected_status,
                    f"{len(payload.get('failures') or [])} failed required net(s)",
                    required_nets=required_nets,
                    process_exit=connected.returncode)
        else:
            checks["connectivity"] = _check(
                "N-A", "no required nets were declared")

        # Shadow work is never executed inside the authoritative candidate
        # transaction.  Even an explicit request becomes a separate pending
        # diagnostic, so it cannot consume this stage's timeout or alter its
        # receipt identity.  Standalone native-DRC and semantic-copper commands
        # remain available to a separately budgeted canary runner.
        shadow_checks["native_drc_delta"] = {
            "status": "INCOMPLETE" if shadow_native_drc else "N-A",
            "detail": ("requested; run in a separate bounded shadow task"
                       if shadow_native_drc else
                       "opt-in full native DRC dual-run was not requested"),
            "authority": "SHADOW",
        }
        for name in ("copper_delta", "source_copper_equivalence"):
            shadow_checks[name] = {
                "status": "INCOMPLETE" if shadow_semantic_copper else "N-A",
                "detail": ("requested; run in a separate bounded shadow task"
                           if shadow_semantic_copper else
                           "opt-in semantic copper shadow was not requested"),
                "authority": "SHADOW",
            }
    except Exception as exc:
        checks.setdefault("workspace", _check("INCOMPLETE", str(exc)))
        if not workspace.exists():
            workspace.mkdir(parents=True, exist_ok=True)

    statuses = {row["status"] for row in checks.values()}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses
               else "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    receipt = {
        "schema": 1,
        "verdict": verdict,
        "subject": "subject.kicad_pcb" if subject else None,
        "origins": origins,
        "required_nets": required_nets,
        "checks": checks,
        "artifacts": _artifact_records(workspace),
        "relocatable": True,
    }
    receipt["binding"] = {
        "algorithm": "sha256",
        "receipt_sha256": _receipt_digest(receipt),
    }
    _atomic_json(workspace / "receipt.json", receipt)
    try:
        _atomic_json(workspace / "shadow_receipt.json", {
            "schema": 1, "kind": "route-candidate-shadow-v1",
            "authority": "SHADOW", "subject": receipt["subject"],
            "authoritative_receipt": _file_record(workspace / "receipt.json"),
            "requested": {
                "native_drc_delta": bool(shadow_native_drc),
                "semantic_copper": bool(shadow_semantic_copper),
                "touched_nets": touched_nets,
                "mutation_baseline": shadow_mutation_baseline,
                "semantic_copper_timeout_s": int(semantic_copper_timeout_s),
                "kicad_python": str(kicad_python),
                "kicad_cli": str(kicad_cli),
            },
            "checks": shadow_checks,
        })
    except Exception:
        # The authoritative receipt is already durable. Optional diagnostics
        # may disappear, but they may never change the function result or
        # make the live candidate transaction fail.
        pass
    return receipt


def _workspace_file(root: Path, value: Any, what: str) -> Path:
    relative = _safe_relative(value, what)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{what} traverses a symlink: {relative}")
    try:
        current.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{what} escapes workspace: {relative}") from exc
    return current


def verify_receipt(receipt_path: Path) -> tuple[bool, list[str]]:
    receipt_path = Path(receipt_path)
    if receipt_path.is_symlink():
        return False, ["receipt may not be a symlink"]
    receipt_path = receipt_path.resolve()
    workspace = receipt_path.parent
    failures: list[str] = []
    try:
        receipt = _read_json(receipt_path)
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"]
    if receipt.get("schema") != 1 or receipt.get("verdict") not in {
            "ACCEPTED", "REJECTED", "INCOMPLETE"}:
        failures.append("receipt schema/verdict is invalid")
    binding = receipt.get("binding")
    if (not isinstance(binding, dict) or binding.get("algorithm") != "sha256"
            or binding.get("receipt_sha256") != _receipt_digest(receipt)):
        failures.append("receipt content binding changed")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        failures.append("receipt has no artifact hash map")
        artifacts = {}
    for relative, expected in sorted(artifacts.items()):
        try:
            path = _workspace_file(workspace, relative, "receipt artifact")
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if not path.is_file():
            failures.append(f"artifact missing: {relative}")
            continue
        actual = _file_record(path)
        if actual != expected:
            failures.append(f"artifact changed: {relative}")

    origins = receipt.get("origins") or {}
    equivalences = {
        "prepared": "baseline.kicad_pcb",
        "candidate": "subject.kicad_pcb",
        "prepared_project": "baseline.kicad_pro",
        "prepared_rules": "baseline.kicad_dru",
    }
    baseline_origin = isinstance(origins, dict) and "mutation_baseline" in origins
    baseline_artifact = "mutation_baseline.kicad_pcb" in artifacts
    if baseline_origin != baseline_artifact:
        failures.append("mutation baseline origin/artifact presence disagrees")
    if baseline_origin:
        equivalences["mutation_baseline"] = "mutation_baseline.kicad_pcb"
    for origin_name, artifact_name in equivalences.items():
        origin = origins.get(origin_name) if isinstance(origins, dict) else None
        artifact = artifacts.get(artifact_name) if isinstance(artifacts, dict) else None
        if not isinstance(origin, dict) or not isinstance(artifact, dict) or any(
                origin.get(key) != artifact.get(key) for key in ("sha256", "size")):
            failures.append(
                f"origin/local artifact binding disagrees: {origin_name}")

    checks = receipt.get("checks") or {}
    expected_check_names = {
        "route_base", "via_in_pad", "physical_drc", "connectivity"}
    if not isinstance(checks, dict):
        failures.append("receipt has no authoritative checks")
        checks = {}
    elif set(checks) != expected_check_names:
        failures.append(
            "authoritative check census disagrees: expected "
            f"{sorted(expected_check_names)}, got {sorted(checks)}")
    for name, row in checks.items():
        if (not isinstance(row, dict) or row.get("status") not in
                {"PASS", "FAIL", "INCOMPLETE", "N-A"}):
            failures.append(f"authoritative check is malformed: {name}")
    statuses = {row.get("status") for row in checks.values()
                if isinstance(row, dict)}
    derived_verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
                       "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    if receipt.get("verdict") != derived_verdict:
        failures.append("receipt verdict disagrees with authoritative checks")

    def check_row(name: str) -> dict[str, Any]:
        row = checks.get(name)
        return row if isinstance(row, dict) else {}

    def recorded_exit(name: str) -> int | None:
        value = check_row(name).get("process_exit")
        if isinstance(value, bool) or not isinstance(value, int):
            failures.append(f"{name} has no integer process_exit")
            return None
        return value

    route_exit = recorded_exit("route_base")
    if route_exit is not None and check_row("route_base").get(
            "status") != _process_status(route_exit):
        failures.append("route_base status disagrees with process exit")

    via_exit = recorded_exit("via_in_pad")
    try:
        via_path = _workspace_file(workspace, "via_in_pad.json", "via evidence")
        via_payload = _read_json(via_path)
        via_process = (_process_status(via_exit)
                       if via_exit is not None else "INCOMPLETE")
        expected_via = ("INCOMPLETE" if via_process == "INCOMPLETE" else
                        "FAIL" if (via_process == "FAIL" or
                                   via_payload.get("verdict") != "PASS") else
                        "PASS")
        if check_row("via_in_pad").get("status") != expected_via:
            failures.append("via_in_pad status disagrees with evidence")
    except Exception as exc:
        failures.append(f"via-in-pad report cannot be regraded: {exc}")

    drc_exit = recorded_exit("physical_drc")
    try:
        drc_path = _workspace_file(
            workspace, "physical_drc.json", "physical DRC evidence")
        payload = _read_json(drc_path)
        hard = [row for row in payload.get("violations", [])
                if row.get("type") in HARD_DRC_TYPES]
        drc_process = (_process_status(drc_exit)
                       if drc_exit is not None else "INCOMPLETE")
        expected_drc = ("INCOMPLETE" if drc_process == "INCOMPLETE" else
                        "FAIL" if hard or drc_process == "FAIL" else "PASS")
        if check_row("physical_drc").get("status") != expected_drc:
            failures.append("physical_drc status disagrees with evidence")
    except Exception as exc:
        failures.append(f"physical DRC report cannot be regraded: {exc}")

    required_nets = receipt.get("required_nets") or []
    if (not isinstance(required_nets, list) or
            any(not isinstance(net, str) for net in required_nets)):
        failures.append("required_nets must be a string list")
        required_nets = []
    if required_nets:
        connectivity_exit = recorded_exit("connectivity")
        try:
            connectivity_path = _workspace_file(
                workspace, "connectivity.json", "connectivity evidence")
            payload = _read_json(connectivity_path)
            connectivity_process = (
                _process_status(connectivity_exit)
                if connectivity_exit is not None else "INCOMPLETE")
            expected_connectivity = (
                "INCOMPLETE" if connectivity_process == "INCOMPLETE" else
                "FAIL" if (connectivity_process == "FAIL" or
                           payload.get("verdict") != "PASS") else "PASS")
            if (check_row("connectivity").get("status") !=
                    expected_connectivity):
                failures.append("connectivity status disagrees with evidence")
            if sorted(set(payload.get("required_nets") or required_nets)) != \
                    sorted(set(required_nets)):
                failures.append("connectivity required-net scope disagrees")
        except Exception as exc:
            failures.append(f"connectivity report cannot be regraded: {exc}")
    elif check_row("connectivity").get("status") != "N-A":
        failures.append("connectivity must be N-A without required nets")
    if receipt.get("verdict") == "ACCEPTED":
        bad = [name for name, row in checks.items()
               if not isinstance(row, dict) or
               row.get("status") not in {"PASS", "N-A"}]
        if bad:
            failures.append(f"accepted receipt contains non-passing checks: {bad}")
    return not failures, failures


def _safe_relative(value: Any, what: str) -> Path:
    relative = Path(str(value or ""))
    if (not relative.parts or relative == Path(".") or relative.is_absolute()
            or ".." in relative.parts):
        raise ValueError(f"{what} is not a safe relative path: {value!r}")
    return relative


def _manifest_digest(manifest: dict[str, Any]) -> str:
    payload = copy.deepcopy(manifest)
    payload.pop("binding", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _verify_bundle_manifest(root: Path, manifest_path: Path) \
        -> tuple[bool, list[str]]:
    failures: list[str] = []
    try:
        manifest = _read_json(manifest_path)
    except Exception as exc:
        return False, [f"accepted bundle manifest cannot be read: {exc}"]
    binding = manifest.get("binding")
    if (manifest.get("schema") != 1 or
            manifest.get("kind") != "route-accepted-bundle-v1"):
        failures.append("accepted bundle schema/kind is invalid")
    if (not isinstance(binding, dict) or binding.get("algorithm") != "sha256"
            or binding.get("sha256") != _manifest_digest(manifest)):
        failures.append("accepted bundle manifest binding changed")
    try:
        receipt_relative = _safe_relative(
            manifest.get("receipt"), "accepted bundle receipt")
        receipt_path = manifest_path.parent / receipt_relative
        expected_receipt = manifest.get("receipt_record") or {}
        if (not receipt_path.is_file() or
                _file_record(receipt_path) != expected_receipt):
            failures.append("accepted bundle receipt moved or changed")
        else:
            valid, receipt_failures = verify_receipt(receipt_path)
            failures.extend(receipt_failures)
            receipt = _read_json(receipt_path)
            receipt_sha = sha256_file(receipt_path)
            if receipt.get("verdict") != "ACCEPTED":
                failures.append("accepted bundle receipt is not ACCEPTED")
            if manifest.get("bundle_id") != receipt_sha:
                failures.append("accepted bundle id differs from receipt hash")
            if manifest.get("artifacts") != receipt.get("artifacts"):
                failures.append("accepted bundle artifact census differs from receipt")
            subject = receipt_path.parent / _safe_relative(
                receipt.get("subject"), "accepted bundle subject")
            if (not subject.is_file() or
                    _file_record(subject) != manifest.get("subject")):
                failures.append("accepted bundle subject moved or changed")
    except Exception as exc:
        failures.append(f"accepted bundle paths are invalid: {exc}")
    try:
        manifest_path.resolve().relative_to(root.resolve())
    except ValueError:
        failures.append("accepted bundle escapes accepted root")
    return not failures, failures


def verify_accepted_bundle(accepted_root: Path) -> tuple[bool, list[str]]:
    """Verify the current pointer, immutable bundle, receipt and subject."""
    root = accepted_root.resolve()
    pointer_path = root / "accepted.json"
    try:
        pointer = _read_json(pointer_path)
    except Exception as exc:
        return False, [f"accepted pointer cannot be read: {exc}"]
    failures: list[str] = []
    if (pointer.get("schema") != 1 or
            pointer.get("kind") != "route-accepted-pointer-v1"):
        failures.append("accepted pointer schema/kind is invalid")
    try:
        manifest_relative = _safe_relative(
            pointer.get("bundle"), "accepted bundle pointer")
        receipt_relative = _safe_relative(
            pointer.get("receipt"), "accepted receipt pointer")
        manifest_path = root / manifest_relative
        receipt_path = root / receipt_relative
        if not manifest_path.is_file():
            failures.append("accepted bundle manifest is missing")
        else:
            valid, bundle_failures = _verify_bundle_manifest(root, manifest_path)
            if not valid:
                failures.extend(bundle_failures)
            manifest = _read_json(manifest_path)
            if pointer.get("bundle_id") != manifest.get("bundle_id"):
                failures.append("accepted pointer bundle id differs from manifest")
            if pointer.get("subject") != manifest.get("subject"):
                failures.append("accepted pointer subject differs from manifest")
            expected_bundle = Path("bundles") / str(pointer.get("bundle_id"))
            if manifest_relative != expected_bundle / "bundle.json" or \
                    receipt_relative != expected_bundle / "receipt.json":
                failures.append("accepted pointer paths differ from bundle id")
        if (not receipt_path.is_file() or
                sha256_file(receipt_path) != pointer.get("receipt_sha256")):
            failures.append("accepted pointer receipt hash changed")
    except Exception as exc:
        failures.append(f"accepted pointer paths are invalid: {exc}")
    return not failures, failures


def publish_accepted_bundle(receipt_path: Path, accepted_root: Path) \
        -> dict[str, Any]:
    """Experimental bundle publisher, currently disabled fail-closed.

    Content bindings catch mutation but do not prove that route-base, via,
    physical, and connectivity checks actually ran.  Until those predicates
    are independently rerun against staged bytes, this API must preserve any
    existing pointer and refuse publication before touching ``accepted_root``.
    """
    del receipt_path, accepted_root
    raise ValueError(
        "accepted bundle promotion is disabled pending independent "
        "authoritative-check regrade")


def connectivity(board_path: Path, nets: list[str]) -> dict[str, Any]:
    import pcbnew
    board = pcbnew.LoadBoard(str(board_path))
    conn = board.GetConnectivity()
    conn.Build(board)
    failures = []
    coverage = {}
    for net in nets:
        pads = [pad for footprint in board.GetFootprints() for pad in footprint.Pads()
                if pad.GetNetname() == net]
        coverage[net] = len(pads)
        if len(pads) < 2:
            failures.append({"net": net, "reason": f"only {len(pads)} pad(s)"})
            continue
        # pcbnew's SWIG wrappers for tracks, vias, and pads are deliberately
        # unhashable in KiCad 10.  Preserve the connectivity result as a
        # sequence and use equality membership instead of attempting to put
        # the wrappers in a set.
        reached = list(conn.GetConnectedItems(pads[0]))
        missing = [f"{pad.GetParentFootprint().GetReference()}.{pad.GetNumber()}"
                   for pad in pads[1:] if pad not in reached]
        if missing:
            failures.append({"net": net, "reason": "unconnected pads",
                             "pads": missing})
    return {"schema": 1, "verdict": "FAIL" if failures else "PASS",
            "required_nets": nets, "pad_coverage": coverage,
            "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    grade = sub.add_parser("grade")
    grade.add_argument("--prepared", type=Path, required=True)
    grade.add_argument("--candidate", type=Path, required=True)
    grade.add_argument("--workspace", type=Path, required=True)
    grade.add_argument("--required-net", action="append", default=[])
    grade.add_argument("--touched-net", action="append", default=[])
    grade.add_argument("--mutation-baseline", type=Path)
    grade.add_argument("--shadow-native-drc", action="store_true")
    grade.add_argument("--shadow-semantic-copper", action="store_true")
    grade.add_argument("--semantic-copper-timeout-s", type=int, default=120)
    grade.add_argument("--kicad-python", default="/usr/bin/python3")
    grade.add_argument("--kicad-cli", default="kicad-cli")
    verify = sub.add_parser("verify")
    verify.add_argument("receipt", type=Path)
    promote = sub.add_parser("promote")
    promote.add_argument("receipt", type=Path)
    promote.add_argument("--accepted-root", type=Path, required=True)
    verify_accepted = sub.add_parser("verify-accepted")
    verify_accepted.add_argument("accepted_root", type=Path)
    conn = sub.add_parser("connectivity")
    conn.add_argument("board", type=Path)
    conn.add_argument("--net", action="append", required=True)
    conn.add_argument("--json", type=Path, required=True)
    semantic = sub.add_parser("semantic-copper")
    semantic.add_argument("--prepared", type=Path, required=True)
    semantic.add_argument("--mutation-baseline", type=Path, required=True)
    semantic.add_argument("--subject", type=Path, required=True)
    semantic.add_argument("--touched-net", action="append", default=[])
    semantic.add_argument("--json", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "grade":
        receipt = grade_candidate(
            args.prepared, args.candidate, args.workspace,
            required_nets=args.required_net, touched_nets=args.touched_net,
            mutation_baseline=args.mutation_baseline,
            shadow_native_drc=args.shadow_native_drc,
            shadow_semantic_copper=args.shadow_semantic_copper,
            semantic_copper_timeout_s=args.semantic_copper_timeout_s,
            kicad_python=args.kicad_python, kicad_cli=args.kicad_cli)
        print(f"ROUTE-CANDIDATE {receipt['verdict']}: "
              f"{args.workspace.resolve() / 'receipt.json'}")
        passed = sum(row.get("status") in {"PASS", "N-A"}
                     for row in receipt["checks"].values())
        print(f"coverage: {passed}/{len(receipt['checks'])} candidate check(s) "
              "passing or non-applicable")
        return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[receipt["verdict"]]
    if args.command == "verify":
        valid, failures = verify_receipt(args.receipt)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"ROUTE-CANDIDATE RECEIPT {'PASS' if valid else 'FAIL'}")
        print("coverage: receipt schema plus every declared artifact hash graded")
        return 0 if valid else 1
    if args.command == "promote":
        try:
            pointer = publish_accepted_bundle(args.receipt, args.accepted_root)
        except Exception as exc:
            print(f"ROUTE-CANDIDATE PROMOTION INCOMPLETE: {exc}")
            return 2
        print(f"ROUTE-CANDIDATE PROMOTED: {pointer['bundle_id']} -> "
              f"{args.accepted_root.resolve() / 'accepted.json'}")
        return 0
    if args.command == "verify-accepted":
        valid, failures = verify_accepted_bundle(args.accepted_root)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"ROUTE-CANDIDATE ACCEPTED {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1

    if args.command == "semantic-copper":
        try:
            result = semantic_copper_evidence(
                args.prepared.resolve(), args.mutation_baseline.resolve(),
                args.subject.resolve(), sorted(set(args.touched_net)))
            _atomic_json(args.json, result)
        except Exception as exc:
            print(f"ROUTE-CANDIDATE SEMANTIC-COPPER INCOMPLETE: {exc}")
            return 2
        print("ROUTE-CANDIDATE SEMANTIC-COPPER PASS")
        return 0

    result = connectivity(args.board, sorted(set(args.net)))
    _atomic_json(args.json, result)
    print(f"ROUTE-CANDIDATE CONNECTIVITY {result['verdict']}: "
          f"{len(result['failures'])} failed net(s)")
    print(f"coverage: {len(result['pad_coverage'])}/{len(result['required_nets'])} "
          "required net(s) inspected")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
