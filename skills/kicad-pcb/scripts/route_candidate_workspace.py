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
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import route_acceptance_core
import copper_graph


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


def _run(command: list[str], cwd: Path) -> CommandResult:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True,
                               timeout=300, check=False)
    return CommandResult(completed.returncode,
                         (completed.stdout or "") + (completed.stderr or ""))


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


def _materialize(prepared: Path, candidate: Path, workspace: Path) -> tuple[Path, dict[str, Any]]:
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
    return subject, origins


def _artifact_records(workspace: Path) -> dict[str, Any]:
    records = {}
    for path in sorted(workspace.iterdir()):
        if path.is_file() and path.name != "receipt.json":
            records[path.name] = _file_record(path)
    return records


def grade_candidate(prepared: Path, candidate: Path, workspace: Path,
                    *, required_nets: list[str] | None = None,
                    touched_nets: list[str] | None = None,
                    shadow_native_drc: bool = False,
                    kicad_python: str = "/usr/bin/python3",
                    kicad_cli: str = "kicad-cli",
                    runner: Runner = _run) -> dict[str, Any]:
    prepared, candidate, workspace = (prepared.resolve(), candidate.resolve(),
                                      workspace.resolve())
    required_nets = sorted(set(required_nets or []))
    touched_nets = sorted(set(touched_nets or []))
    checks: dict[str, dict[str, Any]] = {}
    shadow_checks: dict[str, dict[str, Any]] = {}
    origins: dict[str, Any] = {}
    subject: Path | None = None
    scripts = Path(__file__).resolve().parent

    try:
        subject, origins = _materialize(prepared, candidate, workspace)
        base = runner([kicad_python, str(scripts / "promoted_route_check.py"),
                       "--prepared", str(prepared), "--chain", str(subject)],
                      workspace)
        checks["route_base"] = _check(
            _process_status(base.returncode),
            base.output[-2000:].strip() or f"exit {base.returncode}")

        via_report = workspace / "via_in_pad.json"
        via = runner([kicad_python, str(scripts / "via_in_pad_guard.py"),
                      str(prepared), str(subject), "--json", str(via_report)],
                     workspace)
        checks["via_in_pad"] = _check(
            _process_status(via.returncode),
            via.output[-2000:].strip() or f"exit {via.returncode}")

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
                checks["connectivity"] = _check(
                    "PASS" if payload.get("verdict") == "PASS" else "FAIL",
                    f"{len(payload.get('failures') or [])} failed required net(s)",
                    required_nets=required_nets,
                    process_exit=connected.returncode)
        else:
            checks["connectivity"] = _check(
                "N-A", "no required nets were declared")

        # Full native baseline/current comparison is opt-in while it dual-runs:
        # two extra KiCad invocations must never look like a stalled
        # authoritative grade.  Every failure remains contained in shadow.
        if shadow_native_drc:
            try:
                baseline_report = workspace / "baseline_drc.json"
                baseline_drc = runner([
                    kicad_cli, "pcb", "drc", "--severity-all", "--refill-zones",
                    "--schematic-parity", "--format", "json", "-o",
                    str(baseline_report),
                    str(workspace / "baseline.kicad_pcb")], workspace)
                baseline_payload = (_read_json(baseline_report)
                                    if baseline_report.is_file() else None)
                baseline_grade = route_acceptance_core.classify_native_drc_result(
                    returncode=baseline_drc.returncode,
                    report_path=baseline_report, profile="wave",
                    baseline=baseline_payload, evidence_fresh=True,
                    output=baseline_drc.output)
                full_report = workspace / "shadow_subject_drc.json"
                full_drc = runner([
                    kicad_cli, "pcb", "drc", "--severity-all", "--refill-zones",
                    "--schematic-parity", "--format", "json", "-o",
                    str(full_report), str(subject)], workspace)
                if baseline_grade["status"] != "PASS":
                    shadow_checks["native_drc_delta"] = {
                        "status": "INCOMPLETE",
                        "detail": "prepared-board DRC baseline is not admissible",
                        "baseline": baseline_grade, "authority": "SHADOW"}
                else:
                    shadow_checks["native_drc_delta"] = {
                        **route_acceptance_core.classify_native_drc_result(
                            returncode=full_drc.returncode,
                            report_path=full_report, profile="wave",
                            baseline=baseline_payload, evidence_fresh=True,
                            output=full_drc.output),
                        "authority": "SHADOW",
                    }
            except Exception as exc:
                shadow_checks["native_drc_delta"] = {
                    "status": "INCOMPLETE", "detail": str(exc),
                    "authority": "SHADOW"}
        else:
            shadow_checks["native_drc_delta"] = {
                "status": "N-A",
                "detail": "opt-in full native DRC dual-run was not requested",
                "authority": "SHADOW"}

        # Shadow the new semantic mutation inventory without allowing its
        # approximate real-board connectivity model to own admission yet.
        # The inventory derives changed nets from the exact before/after PCB;
        # caller-declared transaction ownership is only the scope it is
        # compared to; connectivity coverage is a separate input.
        try:
            copper_delta = copper_graph.diff_copper(
                prepared, subject,
                touched=touched_nets if touched_nets else None)
            _atomic_json(workspace / "copper_delta.json", copper_delta)
            status = copper_delta["status"]
            if not touched_nets and copper_delta["changed"]:
                status = "INCOMPLETE"
            shadow_checks["copper_delta"] = {
                "status": status,
                "detail": (f"{copper_delta['counts']['changed_nets']} actual "
                           "changed net(s); mutation scope is "
                           f"{'declared' if touched_nets else 'absent'}"),
                "report": copper_delta, "authority": "SHADOW",
            }
        except Exception as exc:
            shadow_checks["copper_delta"] = {
                "status": "INCOMPLETE", "detail": str(exc),
                "authority": "SHADOW"}
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
        "touched_nets": touched_nets,
        "checks": checks,
        "shadow_checks": shadow_checks,
        "artifacts": _artifact_records(workspace),
        "relocatable": True,
    }
    receipt["binding"] = {
        "algorithm": "sha256",
        "receipt_sha256": _receipt_digest(receipt),
    }
    _atomic_json(workspace / "receipt.json", receipt)
    return receipt


def verify_receipt(receipt_path: Path) -> tuple[bool, list[str]]:
    receipt_path = receipt_path.resolve()
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
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            failures.append(f"artifact path escapes workspace: {relative}")
            continue
        path = receipt_path.parent / relative
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
    for origin_name, artifact_name in equivalences.items():
        origin = origins.get(origin_name) if isinstance(origins, dict) else None
        artifact = artifacts.get(artifact_name) if isinstance(artifacts, dict) else None
        if not isinstance(origin, dict) or not isinstance(artifact, dict) or any(
                origin.get(key) != artifact.get(key) for key in ("sha256", "size")):
            failures.append(
                f"origin/local artifact binding disagrees: {origin_name}")

    checks = receipt.get("checks") or {}
    if not isinstance(checks, dict) or not checks:
        failures.append("receipt has no authoritative checks")
        checks = {}
    statuses = {row.get("status") for row in checks.values()
                if isinstance(row, dict)}
    derived_verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
                       "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    if receipt.get("verdict") != derived_verdict:
        failures.append("receipt verdict disagrees with authoritative checks")

    drc_path = receipt_path.parent / "physical_drc.json"
    if drc_path.is_file():
        try:
            payload = _read_json(drc_path)
            hard = [row for row in payload.get("violations", [])
                    if row.get("type") in HARD_DRC_TYPES]
            if receipt.get("verdict") == "ACCEPTED" and hard:
                failures.append("accepted receipt contains hard DRC findings")
        except Exception as exc:
            failures.append(f"physical DRC report cannot be regraded: {exc}")
    via_path = receipt_path.parent / "via_in_pad.json"
    if via_path.is_file() and receipt.get("verdict") == "ACCEPTED":
        try:
            if _read_json(via_path).get("verdict") != "PASS":
                failures.append("accepted receipt contains failing via-in-pad evidence")
        except Exception as exc:
            failures.append(f"via-in-pad report cannot be regraded: {exc}")
    connectivity_path = receipt_path.parent / "connectivity.json"
    if receipt.get("required_nets") and receipt.get("verdict") == "ACCEPTED":
        try:
            if _read_json(connectivity_path).get("verdict") != "PASS":
                failures.append("accepted receipt contains failing connectivity evidence")
        except Exception as exc:
            failures.append(f"connectivity report cannot be regraded: {exc}")
    if receipt.get("verdict") == "ACCEPTED":
        bad = [name for name, row in checks.items()
               if row.get("status") not in {"PASS", "N-A"}]
        if bad:
            failures.append(f"accepted receipt contains non-passing checks: {bad}")
    return not failures, failures


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
    grade.add_argument("--shadow-native-drc", action="store_true")
    grade.add_argument("--kicad-python", default="/usr/bin/python3")
    grade.add_argument("--kicad-cli", default="kicad-cli")
    verify = sub.add_parser("verify")
    verify.add_argument("receipt", type=Path)
    conn = sub.add_parser("connectivity")
    conn.add_argument("board", type=Path)
    conn.add_argument("--net", action="append", required=True)
    conn.add_argument("--json", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "grade":
        receipt = grade_candidate(
            args.prepared, args.candidate, args.workspace,
            required_nets=args.required_net, touched_nets=args.touched_net,
            shadow_native_drc=args.shadow_native_drc,
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

    result = connectivity(args.board, sorted(set(args.net)))
    _atomic_json(args.json, result)
    print(f"ROUTE-CANDIDATE CONNECTIVITY {result['verdict']}: "
          f"{len(result['failures'])} failed net(s)")
    print(f"coverage: {len(result['pad_coverage'])}/{len(result['required_nets'])} "
          "required net(s) inspected")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
