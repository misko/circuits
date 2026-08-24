#!/usr/bin/env python3
"""Compose the existing cheap schematic battery into E-CLOSURE evidence.

This script deliberately contains no electrical formulas.  The specialist
gates remain authoritative for net survival, invariants, corner calculations,
topology, margins, off-control, component census, source-value identity, and
declared cross-device operating-state compatibility.
E-CLOSURE only supplies a non-vacuous denominator and one hash-bound pipeline
boundary so a later stage cannot accidentally omit one member of the battery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

KICAD_SCRIPTS = Path(__file__).resolve().parent
SKILLS = KICAD_SCRIPTS.parents[1]
FAB_SCRIPTS = SKILLS / "jlcpcb-fab" / "scripts"
PCB_PIPELINE = SKILLS / "pcb-design" / "scripts"
if str(PCB_PIPELINE) not in sys.path:
    sys.path.insert(0, str(PCB_PIPELINE))

from pipeline_identity import TypedIdentityInput, subject_identity  # noqa: E402
from pipeline_applicability import (  # noqa: E402
    APPLIES, DECISION_KIND, INCOMPLETE as APPLICABILITY_INCOMPLETE,
    NOT_APPLICABLE, RECEIPT_KIND,
    SHADOW_AUTHORITY as APPLICABILITY_SHADOW_AUTHORITY,
    verify_applicability,
)
from pipeline_stage_evidence import (  # noqa: E402
    require_safe_output_layout, write_shadow_stage_result,
)
from process_runner import run_bounded  # noqa: E402

import operating_state_check  # noqa: E402


OPERATING_STATE_CHECK = "operating_state_compatibility"
OPERATING_STATE_PROMOTION_CHECK = "operating_state_applicability_authority"
APPLICABILITY_MODES = frozenset({"legacy", "shadow", "authoritative"})


def _record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    completed = run_bounded(
        command, cwd=cwd, timeout_s=180, heartbeat_s=10,
        label="electrical-closure-specialist", echo=False)
    status = "PASS" if completed.returncode == 0 else (
        "FAIL" if completed.returncode == 1 else "INCOMPLETE")
    return {"status": status, "returncode": completed.returncode,
            "elapsed_s": round(completed.elapsed_s, 6),
            "output": completed.output[-8000:]}


def _canonical_circuit(project: Path) -> Path:
    found = [path for path in (
        project / "03_tscircuit/build/circuit.json",
        project / "03_tscircuit/dist/circuit.json",
    ) if path.is_file()]
    if len(found) != 1:
        raise ValueError(f"expected one canonical circuit.json, found {found}")
    return found[0]


def _inputs(project: Path) -> dict[str, Path]:
    paths = []
    for pattern in ("03_src/rules/*.yaml", "02_parts/*/part.yaml"):
        paths.extend(sorted(project.glob(pattern)))
    paths.append(_canonical_circuit(project))
    netlists = sorted((project / "06_build/netlists").glob("*.net"))
    if len(netlists) != 1:
        raise ValueError(f"expected one generated netlist, found {netlists}")
    paths.append(netlists[0])
    unique = []
    seen = set()
    for path in paths:
        resolved = path.resolve(strict=True)
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return {path.relative_to(project).as_posix(): path for path in unique}


def commands(project: Path, *, include_operating_state: bool | None = None
             ) -> list[tuple[str, list[str]]]:
    py = "/usr/bin/python3"
    battery = [
        ("net_label_survival", [py, str(KICAD_SCRIPTS / "net_label_survival.py"), "."]),
        ("electrical_invariants", [py, str(KICAD_SCRIPTS / "electrical_invariants.py"), "."]),
        ("adr_coverage", [py, str(KICAD_SCRIPTS / "electrical_invariants.py"), ".", "--adr-coverage"]),
        ("design_and_corner_models", [py, str(KICAD_SCRIPTS / "early_design_check.py"), "."]),
        ("power_topology", [py, str(KICAD_SCRIPTS / "power_topology.py"), "."]),
        ("power_margin", [py, str(KICAD_SCRIPTS / "power_topology.py"), ".", "--margin"]),
        ("power_off_control", [py, str(KICAD_SCRIPTS / "power_topology.py"), ".", "--off-control"]),
        ("component_census", [py, str(KICAD_SCRIPTS / "count_parity.py"), ".", "--pre-board"]),
        ("source_value_identity", [
            py, str(FAB_SCRIPTS / "bom_source_check.py"), "--circuit-only",
            str(_canonical_circuit(project)), "--parts", str(project / "02_parts")]),
    ]
    # Compatibility authority is exact: before the applicability migration,
    # this authored file opted E-STATE into the legacy closure battery.  Keep
    # that nine-or-ten-check behavior until a separately reviewed authority
    # change replaces it.  Callers may force the command only for an isolated
    # promotion experiment; they may not force it out of the legacy battery.
    state_present = (
        project / "03_src/rules/operating_states.yaml").is_file()
    include_state = state_present or include_operating_state is True
    if include_state:
        battery.append(("operating_state_compatibility", [
            py, str(KICAD_SCRIPTS / "operating_state_check.py"), ".",
            "--manifest", "03_src/rules/operating_state_manifest.yaml",
            "--evidence-root", ".",
            "--json", "06_build/verification/operating_state.json",
        ]))
    return battery


def _applicability_decision(
        value: Mapping[str, Any] | None,
        exact_inputs: Mapping[str, Any] | None,
        *, require_verified: bool,
        ) -> tuple[dict[str, Any] | None, list[str]]:
    """Resolve the E-STATE decision without trusting a forged receipt."""
    if value is None:
        return None, ["compiled E-STATE applicability decision is absent"]
    kind = value.get("kind") if isinstance(value, Mapping) else None
    if kind == RECEIPT_KIND:
        valid, failures = verify_applicability(value, exact_inputs)
        if (require_verified and
                value.get("authority") == APPLICABILITY_SHADOW_AUTHORITY):
            failures = [*failures,
                        "compiled applicability is SHADOW: owner receipts and "
                        "a pinned requirements registry are not reopened"]
            valid = False
        decisions = value.get("decisions") or {}
        decision = decisions.get(OPERATING_STATE_CHECK)
        if not isinstance(decision, Mapping):
            failures = [*failures,
                        f"applicability receipt has no {OPERATING_STATE_CHECK} decision"]
            decision = None
        return (dict(decision) if decision is not None else None,
                [] if valid and decision is not None else failures)
    if kind == DECISION_KIND and not require_verified:
        if value.get("id") != OPERATING_STATE_CHECK:
            return None, ["shadow applicability decision has the wrong id"]
        return dict(value), []
    if kind == DECISION_KIND:
        return None, [
            "authoritative applicability requires an exact-input-verified receipt"]
    return None, ["unsupported E-STATE applicability mapping"]


def _state_row(project: Path, command: list[str], *,
               runner: Callable[[list[str], Path], dict[str, Any]],
               decision: Mapping[str, Any] | None,
               decision_failures: list[str], authoritative: bool,
               execute: bool = True,
               ) -> dict[str, Any]:
    """Grade an applicable state contract or retain a typed N/A/incomplete."""
    if decision_failures:
        return {
            "status": "INCOMPLETE", "returncode": None, "elapsed_s": 0.0,
            "output": "; ".join(decision_failures), "applicability": decision,
        }
    status = decision.get("status") if isinstance(decision, Mapping) else None
    if status == NOT_APPLICABLE:
        return {
            "status": "N-A", "returncode": 0, "elapsed_s": 0.0,
            "output": f"typed reason={decision.get('reason')}",
            "applicability": dict(decision),
        }
    if status == APPLICABILITY_INCOMPLETE:
        return {
            "status": "INCOMPLETE", "returncode": None, "elapsed_s": 0.0,
            "output": f"typed reason={decision.get('reason')}",
            "applicability": dict(decision),
        }
    if status != APPLIES:
        return {
            "status": "INCOMPLETE", "returncode": None, "elapsed_s": 0.0,
            "output": f"invalid applicability status {status!r}",
            "applicability": decision,
        }
    required = [
        project / "03_src/rules/operating_states.yaml",
        project / "03_src/rules/operating_state_manifest.yaml",
    ]
    missing = [path.relative_to(project).as_posix()
               for path in required if not path.is_file()]
    if missing:
        return {
            "status": "INCOMPLETE", "returncode": None, "elapsed_s": 0.0,
            "output": "applicable E-STATE configuration is missing: "
                      + ", ".join(missing),
            "applicability": dict(decision),
        }
    if not execute:
        return {
            "status": "INCOMPLETE", "returncode": None, "elapsed_s": 0.0,
            "output": ("applicable E-STATE requested; run it in a separate "
                       "bounded shadow task"),
            "applicability": dict(decision),
        }
    row = runner(command, project)
    row["applicability"] = dict(decision)
    if authoritative and row.get("status") == "PASS":
        receipt_path = project / "06_build/verification/operating_state.json"
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
            valid, failures = operating_state_check.verify_receipt(receipt)
            if (receipt.get("authority") != "AUTHORITATIVE" or
                    (receipt.get("evidence") or {}).get("authority") !=
                    "VERIFIED"):
                valid = False
                failures = [*failures,
                            "operating-state endpoints lack typed extractor "
                            "receipt authority"]
        except Exception as exc:
            valid, failures = False, [f"receipt cannot be reopened: {exc}"]
        if not valid:
            row = dict(row)
            row["status"] = "INCOMPLETE"
            row["returncode"] = None
            row["output"] = (row.get("output", "") + "\n" +
                             "; ".join(failures))[-8000:]
            row["evidence_reopen_failures"] = failures
    return row


def grade(project: Path, *,
          runner: Callable[[list[str], Path], dict[str, Any]] = _run,
          operating_state_applicability: Mapping[str, Any] | None = None,
          applicability_inputs: Mapping[str, Any] | None = None,
          applicability_mode: str = "legacy"
          ) -> dict[str, Any]:
    project = project.resolve()
    if applicability_mode not in APPLICABILITY_MODES:
        raise ValueError(
            f"applicability_mode must be one of {sorted(APPLICABILITY_MODES)}")
    authoritative = applicability_mode == "authoritative"
    inputs = _inputs(project)
    base_commands = commands(project)
    checks = {name: runner(command, project)
              for name, command in base_commands}
    if authoritative:
        decision, decision_failures = _applicability_decision(
            operating_state_applicability, applicability_inputs,
            require_verified=True)
        state_command = dict(commands(
            project, include_operating_state=True))[OPERATING_STATE_CHECK]
        state = _state_row(
            project, state_command, runner=runner, decision=decision,
            decision_failures=decision_failures, authoritative=True,
            execute=True)
        checks[OPERATING_STATE_PROMOTION_CHECK] = state
    statuses = {row["status"] for row in checks.values()}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
               "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    return {
        "schema": 1, "kind": "electrical-closure-receipt-v1",
        "verdict": verdict,
        "subject": {name: _record(path) for name, path in inputs.items()},
        "checks": checks,
        "coverage": {
            "passing": sum(row["status"] in {"PASS", "N-A"}
                           for row in checks.values()),
            "total": len(checks),
        },
    }


def _state_shadow_request(
        project: Path, subject: Mapping[str, Any],
        operating_state_applicability: Mapping[str, Any] | None,
        applicability_inputs: Mapping[str, Any] | None) -> dict[str, Any]:
    """Build a non-executing E-STATE request beside the legacy receipt."""
    project = project.resolve()
    decision, failures = _applicability_decision(
        operating_state_applicability, applicability_inputs,
        require_verified=False)
    command = dict(commands(
        project, include_operating_state=True))[OPERATING_STATE_CHECK]
    state = _state_row(
        project, command, runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("shadow E-STATE execution is forbidden")),
        decision=decision, decision_failures=failures,
        authoritative=False, execute=False)
    state["authority"] = "SHADOW"
    return {
        "schema": 1, "kind": "electrical-closure-shadow-v1",
        "authority": "SHADOW", "subject": dict(subject),
        "applicability": {
            "decision": decision, "verification_failures": failures,
            "source_authority": (
                operating_state_applicability.get("authority")
                if isinstance(operating_state_applicability, Mapping)
                else None),
        },
        "checks": {OPERATING_STATE_CHECK: state},
    }


def _pending_state_shadow_request(
        subject: Mapping[str, Any], *,
        applicability_path: Path | None,
        applicability_inputs_path: Path | None) -> dict[str, Any]:
    """Record a shadow request without reading or executing shadow inputs."""

    return {
        "schema": 1, "kind": "electrical-closure-shadow-v1",
        "authority": "SHADOW", "subject": dict(subject),
        "requested": {
            "operating_state_applicability": (
                str(applicability_path) if applicability_path else None),
            "applicability_inputs": (
                str(applicability_inputs_path)
                if applicability_inputs_path else None),
        },
        "checks": {OPERATING_STATE_CHECK: {
            "status": "INCOMPLETE", "returncode": None,
            "elapsed_s": 0.0, "authority": "SHADOW",
            "output": ("pending separate bounded applicability verification "
                       "and E-STATE canary; no shadow input was opened"),
            "applicability": None,
        }},
    }


def _publish(receipt: dict[str, Any], receipt_path: Path,
             bundle_path: Path, stage_path: Path) -> None:
    """Emit a typed shadow request; never replace an accepted bundle."""
    del receipt_path, bundle_path
    semantic = {
        "legacy_verdict": receipt.get("verdict"),
        "inputs": {name: record["sha256"]
                   for name, record in sorted(
                       (receipt.get("subject") or {}).items())},
    }
    authoritative_bytes = json.dumps(
        semantic, sort_keys=True, separators=(",", ":")).encode("utf-8")
    identity = subject_identity("electrical-closure", 1, [TypedIdentityInput(
        "closure", "mapping", semantic, authoritative_bytes)])
    coverage = receipt.get("coverage") or {"total": 0}
    write_shadow_stage_result(
        stage_id="E-CLOSURE", subject=identity,
        stage_result_path=stage_path, total=coverage["total"],
        finding_code="E-CLOSURE-PROMOTION-DISABLED",
        finding_detail=(
            "legacy receipt composition is not an independently regraded, "
            "single-transaction authority; accepted bundle unchanged"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--stage-bundle", type=Path)
    parser.add_argument("--stage-result", type=Path)
    parser.add_argument("--applicability-mode", choices=sorted(APPLICABILITY_MODES),
                        default="legacy")
    parser.add_argument("--operating-state-applicability", type=Path)
    parser.add_argument("--applicability-inputs", type=Path)
    args = parser.parse_args(argv)
    if bool(args.stage_bundle) != bool(args.stage_result):
        parser.error("--stage-bundle and --stage-result must be supplied together")
    shadow_path = args.json.with_name(f"{args.json.stem}.shadow.json")
    output_paths = {"receipt": args.json, "shadow": shadow_path}
    if args.stage_bundle:
        output_paths.update({"stage_bundle": args.stage_bundle,
                             "stage_result": args.stage_result})
    try:
        require_safe_output_layout(
            output_paths,
            directory_outputs=("stage_bundle",) if args.stage_bundle else (),
            protected_paths={"project": args.project},
        )
    except ValueError as exc:
        print(f"E-CLOSURE INCOMPLETE: {exc}")
        return 2
    applicability_receipt = applicability_inputs = None
    if args.applicability_mode == "authoritative":
        try:
            applicability_receipt = (json.loads(
                args.operating_state_applicability.read_text(
                    encoding="utf-8-sig"))
                if args.operating_state_applicability else None)
            applicability_inputs = (json.loads(
                args.applicability_inputs.read_text(encoding="utf-8-sig"))
                if args.applicability_inputs else None)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"E-CLOSURE INCOMPLETE: applicability input: {exc}")
            return 2
    try:
        receipt = grade(
            args.project,
            operating_state_applicability=applicability_receipt,
            applicability_inputs=applicability_inputs,
            applicability_mode=args.applicability_mode)
    except Exception as exc:
        print(f"E-CLOSURE INCOMPLETE: {exc}")
        return 2
    try:
        require_safe_output_layout(
            output_paths,
            directory_outputs=("stage_bundle",) if args.stage_bundle else (),
            protected_paths={
                "project": args.project,
                **{f"input_{name}": Path(record["path"])
                   for name, record in (receipt.get("subject") or {}).items()},
            },
        )
    except ValueError as exc:
        print(f"E-CLOSURE INCOMPLETE: {exc}")
        return 2
    _atomic_json(args.json, receipt)
    if args.applicability_mode == "shadow":
        try:
            shadow = _pending_state_shadow_request(
                receipt["subject"],
                applicability_path=args.operating_state_applicability,
                applicability_inputs_path=args.applicability_inputs)
            _atomic_json(shadow_path, shadow)
        except Exception as exc:
            print(f"E-CLOSURE SHADOW INCOMPLETE: {exc}")
    if args.stage_bundle:
        try:
            _publish(receipt, args.json.resolve(), args.stage_bundle.resolve(),
                     args.stage_result.resolve())
        except Exception as exc:
            print(f"E-CLOSURE INCOMPLETE: shadow stage evidence: {exc}")
            # Optional stage publication remains shadow authority. Preserve
            # the legacy closure verdict and any prior accepted bundle.
    coverage = receipt["coverage"]
    print(f"E-CLOSURE {receipt['verdict']}: {coverage['passing']}/"
          f"{coverage['total']} specialist gates pass; receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[receipt["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
