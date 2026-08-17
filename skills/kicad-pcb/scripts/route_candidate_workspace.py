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
import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


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
    subject = workspace / "subject.kicad_pcb"
    shutil.copy2(candidate, subject)
    for source in sidecars:
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
                    kicad_python: str = "/usr/bin/python3",
                    kicad_cli: str = "kicad-cli",
                    runner: Runner = _run) -> dict[str, Any]:
    prepared, candidate, workspace = (prepared.resolve(), candidate.resolve(),
                                      workspace.resolve())
    required_nets = sorted(set(required_nets or []))
    checks: dict[str, dict[str, Any]] = {}
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

        drc_report = workspace / "physical_drc.json"
        drc = runner([kicad_cli, "pcb", "drc", "--severity-all", "--format",
                      "json", "-o", str(drc_report), str(subject)], workspace)
        if not drc_report.is_file():
            checks["physical_drc"] = _check(
                "INCOMPLETE", "kicad-cli wrote no JSON report",
                process_exit=drc.returncode)
        else:
            payload = _read_json(drc_report)
            hits = [row for row in payload.get("violations", [])
                    if row.get("type") in HARD_DRC_TYPES]
            checks["physical_drc"] = _check(
                "FAIL" if hits else "PASS",
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
    if receipt.get("verdict") == "ACCEPTED":
        bad = [name for name, row in (receipt.get("checks") or {}).items()
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
        reached = set(conn.GetConnectedItems(pads[0]))
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
            required_nets=args.required_net, kicad_python=args.kicad_python,
            kicad_cli=args.kicad_cli)
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
