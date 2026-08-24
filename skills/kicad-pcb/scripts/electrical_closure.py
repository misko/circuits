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
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

KICAD_SCRIPTS = Path(__file__).resolve().parent
SKILLS = KICAD_SCRIPTS.parents[1]
FAB_SCRIPTS = SKILLS / "jlcpcb-fab" / "scripts"
PCB_PIPELINE = SKILLS / "pcb-design" / "scripts"
if str(PCB_PIPELINE) not in sys.path:
    sys.path.insert(0, str(PCB_PIPELINE))

from pipeline_identity import TypedIdentityInput, subject_identity  # noqa: E402
from pipeline_stage_evidence import publish_stage_evidence  # noqa: E402


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
    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, capture_output=True,
                                   text=True, timeout=180, check=False)
    except subprocess.TimeoutExpired as exc:
        return {"status": "INCOMPLETE", "returncode": None,
                "elapsed_s": round(time.monotonic() - started, 6),
                "output": ((exc.stdout or "") + (exc.stderr or ""))[-8000:]}
    status = "PASS" if completed.returncode == 0 else (
        "FAIL" if completed.returncode == 1 else "INCOMPLETE")
    return {"status": status, "returncode": completed.returncode,
            "elapsed_s": round(time.monotonic() - started, 6),
            "output": (completed.stdout + completed.stderr)[-8000:]}


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


def commands(project: Path) -> list[tuple[str, list[str]]]:
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
    # E-STATE is opt-in during fleet migration.  Its presence is derived from
    # the authored rule, not a require_* switch; projects without the new
    # contract retain the exact legacy nine-predicate composition.  Once
    # present, malformed/empty state coverage fails inside the specialist.
    if (project / "03_src/rules/operating_states.yaml").is_file():
        battery.append(("operating_state_compatibility", [
            py, str(KICAD_SCRIPTS / "operating_state_check.py"), ".",
            "--manifest", "03_src/rules/operating_state_manifest.yaml",
            "--json", "06_build/verification/operating_state.json",
        ]))
    return battery


def grade(project: Path, *, runner: Callable[[list[str], Path], dict[str, Any]] = _run
          ) -> dict[str, Any]:
    project = project.resolve()
    inputs = _inputs(project)
    checks = {name: runner(command, project)
              for name, command in commands(project)}
    statuses = {row["status"] for row in checks.values()}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
               "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    return {
        "schema": 1, "kind": "electrical-closure-receipt-v1",
        "verdict": verdict,
        "subject": {name: _record(path) for name, path in inputs.items()},
        "checks": checks,
        "coverage": {
            "passing": sum(row["status"] == "PASS" for row in checks.values()),
            "total": len(checks),
        },
    }


def _publish(receipt: dict[str, Any], receipt_path: Path,
             bundle_path: Path, stage_path: Path) -> None:
    if receipt.get("verdict") != "ACCEPTED":
        raise ValueError("E-CLOSURE cannot publish non-accepted evidence")
    semantic = {
        "checks": {name: {"status": row["status"]}
                   for name, row in sorted(receipt["checks"].items())},
        "inputs": {name: record["sha256"]
                   for name, record in sorted(receipt["subject"].items())},
    }
    identity = subject_identity("electrical-closure", 1, [TypedIdentityInput(
        "closure", "mapping", semantic, receipt_path.read_bytes())])
    inputs = {name: Path(record["path"])
              for name, record in receipt["subject"].items()}
    coverage = receipt["coverage"]
    publish_stage_evidence(
        stage_id="E-CLOSURE",
        output_symbol="electrical_closure_report",
        producer="electrical_closure.py",
        producer_version="schema-1-shadow",
        subject=identity, inputs=inputs,
        measurement_path=receipt_path,
        measurement_name="electrical_closure.json",
        accepted_dir=bundle_path,
        stage_result_path=stage_path,
        status="PASS", graded=coverage["passing"], total=coverage["total"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--stage-bundle", type=Path)
    parser.add_argument("--stage-result", type=Path)
    args = parser.parse_args(argv)
    if bool(args.stage_bundle) != bool(args.stage_result):
        parser.error("--stage-bundle and --stage-result must be supplied together")
    try:
        receipt = grade(args.project)
    except Exception as exc:
        print(f"E-CLOSURE INCOMPLETE: {exc}")
        return 2
    _atomic_json(args.json, receipt)
    if args.stage_bundle:
        try:
            _publish(receipt, args.json.resolve(), args.stage_bundle.resolve(),
                     args.stage_result.resolve())
        except Exception as exc:
            print(f"E-CLOSURE INCOMPLETE: shadow stage evidence: {exc}")
            return 2
    coverage = receipt["coverage"]
    print(f"E-CLOSURE {receipt['verdict']}: {coverage['passing']}/"
          f"{coverage['total']} specialist gates pass; receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[receipt["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
