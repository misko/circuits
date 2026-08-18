#!/usr/bin/env python3
"""Compose exact-code manufacturing readiness into one hash-bound receipt.

Selection mode runs before part freeze and proves that every source component
has exactly one JLC code or an explicit unassembled/manual disposition, that
every declared MPN resolves to one exact dossier, and that the existing part-
facts and source-value gates pass.  Prelayout mode additionally requires a
quantity-expanded JLCPCB PCBA availability receipt.  Order mode requires a
fresh ALLOCATED receipt for the exact release BOM instead of treating catalog
stock or an earlier AVAILABLE result as permanent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml


SCRIPTS = Path(__file__).resolve().parent


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


def _run(label: str, command: list[str], cwd: Path) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command, cwd=cwd, capture_output=True, text=True,
            timeout=900, check=False)
    except subprocess.TimeoutExpired as exc:
        return {"status": "INCOMPLETE", "detail": f"{label} timed out",
                "elapsed_s": round(time.monotonic() - started, 6),
                "output": ((exc.stdout or "") + (exc.stderr or ""))[-4000:]}
    status = "PASS" if completed.returncode == 0 else (
        "FAIL" if completed.returncode == 1 else "INCOMPLETE")
    return {"status": status, "detail": f"exit {completed.returncode}",
            "elapsed_s": round(time.monotonic() - started, 6),
            "output": ((completed.stdout or "")
                       + (completed.stderr or ""))[-8000:]}


def _pcba_check(receipt: Path | None, *, phase: str,
                bom: Path | None = None) -> dict[str, Any]:
    if receipt is None:
        return {"status": "INCOMPLETE",
                "detail": f"{phase} requires --pcba-receipt",
                "output": "catalog stock is not JLCPCB assembly authority"}
    command = ["/usr/bin/python3", str(SCRIPTS / "jlc_pcba_availability.py"),
               "verify", str(receipt), "--phase", phase]
    if bom is not None:
        command += ["--bom", str(bom)]
    checked = _run("JLCPCB PCBA receipt", command, Path.cwd())
    if checked["status"] != "PASS":
        return checked
    try:
        data = json.loads(receipt.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"status": "INCOMPLETE", "detail": f"receipt unreadable: {exc}",
                "output": checked.get("output", "")}
    if data.get("verdict") != "ACCEPTED":
        checked["status"] = "FAIL" if data.get("verdict") == "REJECTED" else "INCOMPLETE"
        checked["detail"] = f"JLCPCB PCBA receipt verdict {data.get('verdict')}"
    return checked


def _find_circuit(project: Path) -> Path:
    choices = [project / "03_tscircuit/build/circuit.json",
               project / "03_tscircuit/dist/circuit.json"]
    found = [path for path in choices if path.is_file()]
    if len(found) != 1:
        raise ValueError(f"expected one canonical circuit.json, found {found}")
    return found[0]


def exact_code_check(project: Path, circuit: Path,
                     assembly: Path) -> tuple[dict[str, Any], list[Path]]:
    items = json.loads(circuit.read_text(encoding="utf-8-sig"))
    components = [row for row in items
                  if isinstance(row, dict) and row.get("type") == "source_component"]
    assembly_data = yaml.safe_load(assembly.read_text(encoding="utf-8-sig")) or {}
    manual = {str(ref) for row in assembly_data.get("not_assembled") or []
              if isinstance(row, dict) for ref in row.get("refs") or []}
    dossiers: dict[str, tuple[Path, dict[str, Any]]] = {}
    duplicate_mpn = set()
    for path in sorted((project / "02_parts").glob("*/part.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        if not isinstance(data, dict) or not data.get("mpn"):
            continue
        mpn = str(data["mpn"])
        if mpn in dossiers:
            duplicate_mpn.add(mpn)
        dossiers[mpn] = (path, data)
    failures = [f"duplicate exact dossier identity {mpn!r}"
                for mpn in sorted(duplicate_mpn)]
    rows, used_dossiers = [], []
    for component in components:
        ref = str(component.get("name") or "")
        mpn = str(component.get("manufacturer_part_number") or "").strip()
        raw_supplier = ((component.get("supplier_part_numbers") or {})
                        .get("jlcpcb") or [])
        if isinstance(raw_supplier, str):
            raw_supplier = [raw_supplier]
        if not isinstance(raw_supplier, list):
            failures.append(f"{ref}: jlcpcb supplier identity must be a list")
            raw_supplier = []
        supplier_values = [str(value).strip() for value in raw_supplier
                           if str(value).strip()]
        codes = [value for value in supplier_values
                 if re.fullmatch(r"C\d+", value)]
        handles = [value for value in supplier_values if value not in codes]
        disposition = "jlc" if len(codes) == 1 else "manual" if ref in manual else "invalid"
        if len(codes) > 1:
            failures.append(f"{ref}: multiple JLC codes {codes}")
        if codes and handles:
            failures.append(
                f"{ref}: JLC supplier field mixes catalog code(s) and "
                f"non-code handle(s) {handles}")
        if not codes and ref not in manual:
            failures.append(f"{ref}: no JLC code and no not_assembled disposition")
        if ref in manual and codes:
            failures.append(f"{ref}: manual/unassembled ref also declares JLC code {codes}")
        dossier = dossiers.get(mpn) if mpn else None
        if mpn and dossier is None:
            failures.append(f"{ref}: exact MPN {mpn!r} has no dossier")
        if dossier:
            used_dossiers.append(dossier[0])
            sourcing = dossier[1].get("sourcing") or {}
            declared_code = str(sourcing.get("lcsc") or "").strip()
            if codes and declared_code and declared_code != codes[0]:
                failures.append(
                    f"{ref}: source code {codes[0]} disagrees with "
                    f"{mpn} dossier code {declared_code}")
        rows.append({"ref": ref, "mpn": mpn or None, "jlc_codes": codes,
                     "supplier_handles": handles,
                     "disposition": disposition,
                     "dossier": str(dossier[0].resolve()) if dossier else None})
    return ({
        "status": "FAIL" if failures else "PASS",
        "detail": f"{len(rows)}/{len(components)} source component(s) graded",
        "coverage": {"graded": len(rows), "total": len(components)},
        "manual_refs": sorted(manual), "rows": rows, "findings": failures,
    }, sorted(set(used_dossiers)))


def grade(project: Path, *, phase: str, release: Path | None = None,
          pcba_receipt: Path | None = None) -> dict[str, Any]:
    project = project.resolve()
    circuit = _find_circuit(project)
    assembly = project / "03_src/rules/assembly.yaml"
    if not assembly.is_file():
        raise ValueError(f"missing {assembly}")
    checks: dict[str, dict[str, Any]] = {}
    exact, dossiers = exact_code_check(project, circuit, assembly)
    checks["exact_code_identity"] = exact
    checks["source_value_identity"] = _run(
        "source value identity",
        ["/usr/bin/python3", str(SCRIPTS / "bom_source_check.py"),
         "--circuit-only", str(circuit), "--parts", str(project / "02_parts")],
        project)
    inputs = {"circuit": _record(circuit), "assembly": _record(assembly)}
    for index, path in enumerate(dossiers):
        inputs[f"part_{index:03d}"] = _record(path)

    if pcba_receipt is not None:
        pcba_receipt = pcba_receipt.resolve()
        if pcba_receipt.is_file():
            inputs["pcba_receipt"] = _record(pcba_receipt)

    if phase == "prelayout":
        checks["jlc_pcba_availability"] = _pcba_check(
            pcba_receipt, phase="prelayout")

    if phase == "order":
        if release is None or not release.is_dir():
            raise ValueError("order phase requires --release directory")
        release = release.resolve()
        manifest = release / "MANIFEST.txt"
        readme = release / "ORDER_README.md"
        for name, path in (("release_manifest", manifest),
                           ("order_instructions", readme)):
            if not path.is_file():
                raise ValueError(f"missing {path}")
            inputs[name] = _record(path)
        checks["assembly_population"] = _run(
            "assembly population",
            ["/usr/bin/python3", str(SCRIPTS / "assembly_coverage.py"),
             str(release), "--assembly", str(assembly)], project)
        checks["realized_part_facts"] = _run(
            "realized part facts",
            ["/usr/bin/python3", str(SCRIPTS / "part_facts_check.py"),
             str(release), "--parts", str(project / "02_parts"), "--strict"],
            project)
        checks["jlc_order_allocation"] = _pcba_check(
            pcba_receipt, phase="order", bom=release / "fab/bom.csv")
        checks["order_time_sourcing"] = _run(
            "order-time sourcing",
            ["/usr/bin/python3", str(SCRIPTS / "release_freshness_check.py"),
             str(release), "--claim", "sourcing", "--assembly", str(assembly),
             "--sourcing-authority", "jlc-pcba", "--pcba-evidence",
             str(pcba_receipt or "")],
            project)

    statuses = {row["status"] for row in checks.values()}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
               "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    return {
        "schema": 1, "kind": "manufacturing-readiness-receipt-v1",
        "phase": phase, "verdict": verdict, "project": project.name,
        "inputs": inputs, "checks": checks,
        "coverage": {"passing": sum(row["status"] == "PASS"
                                     for row in checks.values()),
                     "total": len(checks)},
    }


def verify(path: Path) -> tuple[bool, list[str]]:
    failures = []
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"]
    if (receipt.get("schema") != 1 or
            receipt.get("kind") != "manufacturing-readiness-receipt-v1"):
        failures.append("unsupported receipt schema/kind")
    for name, record in sorted((receipt.get("inputs") or {}).items()):
        source = Path(str(record.get("path") or ""))
        if not source.is_file() or _record(source) != record:
            failures.append(f"input moved or changed: {name}")
    if receipt.get("verdict") == "ACCEPTED":
        bad = [name for name, row in (receipt.get("checks") or {}).items()
               if row.get("status") != "PASS"]
        if bad:
            failures.append(f"accepted receipt contains bad checks: {bad}")
    return not failures, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    grade_parser = sub.add_parser("grade")
    grade_parser.add_argument("project", type=Path)
    grade_parser.add_argument("--phase", choices=("selection", "prelayout", "order"),
                              default="selection")
    grade_parser.add_argument("--release", type=Path)
    grade_parser.add_argument("--pcba-receipt", type=Path)
    grade_parser.add_argument("--json", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        valid, failures = verify(args.receipt)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"MANUFACTURING-READINESS RECEIPT {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1
    try:
        result = grade(args.project, phase=args.phase, release=args.release,
                       pcba_receipt=args.pcba_receipt)
    except Exception as exc:
        print(f"MANUFACTURING-READINESS INCOMPLETE: {exc}")
        return 2
    _atomic_json(args.json, result)
    coverage = result["coverage"]
    print(f"MANUFACTURING-READINESS {result['verdict']}: "
          f"{coverage['passing']}/{coverage['total']} checks pass; "
          f"phase={result['phase']}; receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
