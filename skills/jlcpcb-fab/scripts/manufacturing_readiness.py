#!/usr/bin/env python3
"""Compose exact-code manufacturing readiness into one hash-bound receipt.

Selection mode runs before part freeze and proves that every source component
has exactly one JLC code or an explicit unassembled/manual disposition, that
every declared MPN resolves to one exact dossier, and that the existing part-
facts and source-value gates pass.  Prelayout mode additionally requires a
quantity-expanded JLCPCB PCBA receipt whose availability and procurement-cost
predicates both pass. Order mode requires a fresh ALLOCATED receipt and quote
for the exact release BOM instead of treating catalog stock, raw MOQ, or an
earlier AVAILABLE result as permanent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


SCRIPTS = Path(__file__).resolve().parent
PCB_PIPELINE = SCRIPTS.parents[1] / "pcb-design" / "scripts"
if str(PCB_PIPELINE) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PCB_PIPELINE))
KICAD_SCRIPTS = SCRIPTS.parents[1] / "kicad-pcb" / "scripts"
if str(KICAD_SCRIPTS) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(KICAD_SCRIPTS))

from pipeline_identity import TypedIdentityInput, subject_identity  # noqa: E402
from pipeline_stage_evidence import (  # noqa: E402
    require_safe_output_layout, write_shadow_stage_result,
)
from process_runner import run_bounded  # noqa: E402


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
    completed = run_bounded(
        command, cwd=cwd, timeout_s=900, heartbeat_s=10,
        label=f"manufacturing-readiness-{label}", echo=False)
    status = "PASS" if completed.returncode == 0 else (
        "FAIL" if completed.returncode == 1 else "INCOMPLETE")
    return {"status": status, "detail": f"exit {completed.returncode}",
            "elapsed_s": round(time.monotonic() - started, 6),
            "output": completed.output[-8000:]}


def _pcba_check(receipt: Path | None, *, phase: str,
                bom: Path | None = None,
                predicate: str = "availability") -> dict[str, Any]:
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
    if predicate == "availability":
        verdict = data.get("availability_verdict", data.get("verdict"))
    elif predicate == "economics":
        verdict = data.get("economics_verdict")
        if verdict is None:
            checked.update(
                status="INCOMPLETE",
                detail="legacy PCBA receipt has no procurement economics",
                output="schema-v2 MOQ/cost evidence and policy are required")
            return checked
    else:
        return {"status": "INCOMPLETE", "detail": f"unknown predicate {predicate}",
                "output": ""}
    if verdict != "ACCEPTED":
        checked["status"] = "FAIL" if verdict == "REJECTED" else "INCOMPLETE"
        checked["detail"] = f"JLCPCB PCBA {predicate} verdict {verdict}"
    else:
        checked["detail"] = f"JLCPCB PCBA {predicate} accepted"
    return checked


def _catalog_prelayout_check(request_path: Path | None,
                             evidence_path: Path | None,
                             decision_path: Path | None) -> dict[str, Any]:
    """Verify a user-accepted public-catalog pre-layout negative filter.

    This deliberately cannot be used for the order phase.  It proves only
    exact-code catalog coverage for the requested build quantity and binds the
    explicit project decision that defers allocation/economics to the uploader.
    """
    if not all((request_path, evidence_path, decision_path)):
        return {"status": "INCOMPLETE",
                "detail": "catalog prelayout requires request, evidence, and decision",
                "output": "public catalog evidence is not order allocation"}
    try:
        request = json.loads(request_path.read_text(encoding="utf-8-sig"))
        evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        decision = decision_path.read_text(encoding="utf-8-sig")
    except Exception as exc:
        return {"status": "INCOMPLETE", "detail": f"catalog evidence unreadable: {exc}",
                "output": ""}
    failures = []
    if request.get("phase") != "prelayout" or request.get("schema") != 2:
        failures.append("request is not a schema-v2 prelayout request")
    if evidence.get("verdict") != "PASS":
        failures.append(f"catalog verdict is {evidence.get('verdict')!r}, not PASS")
    if evidence.get("predicts_jlc_assembly_allocation") is not False:
        failures.append("catalog evidence does not preserve its non-allocation scope")
    try:
        generated = datetime.fromisoformat(str(evidence.get("generated_at") or "").replace("Z", "+00:00"))
        if generated.tzinfo is None:
            raise ValueError("timezone missing")
        age = datetime.now(timezone.utc) - generated.astimezone(timezone.utc)
        if age < timedelta(0) or age > timedelta(hours=24):
            failures.append("catalog evidence is future-dated or older than 24 hours")
    except ValueError as exc:
        failures.append(f"catalog generated_at is invalid: {exc}")
    wanted = {row.get("requested_lcsc"): row for row in request.get("rows") or []}
    observed = {row.get("lcsc"): row for row in evidence.get("lines") or []}
    if not wanted or set(wanted) != set(observed):
        failures.append("catalog code set does not exactly match the request")
    for code, row in wanted.items():
        got = observed.get(code) or {}
        if got.get("status") != "OK":
            failures.append(f"{code}: catalog status {got.get('status')!r}")
            continue
        try:
            per_board = int(got.get("qty"))
            stock = int(got.get("stock"))
        except (TypeError, ValueError):
            failures.append(f"{code}: qty/stock is not integral")
            continue
        if per_board != int(row.get("per_board_qty") or -1):
            failures.append(f"{code}: per-board quantity disagrees with request")
        if stock < int(row.get("required_qty") or 0):
            failures.append(f"{code}: catalog stock {stock} below required quantity")
    required_decision_terms = ("public-catalog", "pre-layout", "DO-NOT-ORDER")
    if any(term not in decision for term in required_decision_terms):
        failures.append("decision does not explicitly bound catalog use to pre-layout/DO-NOT-ORDER")
    return {
        "status": "FAIL" if failures else "PASS",
        "detail": ("; ".join(failures) if failures else
                   f"{len(wanted)}/{len(wanted)} exact public-catalog lines cover the build; "
                   "user accepted for pre-layout only"),
        "output": "public catalog negative filter only; final JLC uploader allocation and economics remain mandatory",
    }


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
            footprint = dossier[1].get("footprint")
            if disposition == "jlc" and (
                    not isinstance(footprint, str) or not footprint.strip()):
                failures.append(
                    f"{ref}: JLC-assembled exact MPN {mpn!r} has no frozen "
                    "footprint in its dossier")
        rows.append({"ref": ref, "mpn": mpn or None, "jlc_codes": codes,
                     "supplier_handles": handles,
                     "disposition": disposition,
                     "dossier": str(dossier[0].resolve()) if dossier else None,
                     "footprint": (dossier[1].get("footprint")
                                   if dossier else None)})
    return ({
        "status": "FAIL" if failures else "PASS",
        "detail": f"{len(rows)}/{len(components)} source component(s) graded",
        "coverage": {"graded": len(rows), "total": len(components)},
        "manual_refs": sorted(manual), "rows": rows, "findings": failures,
    }, sorted(set(used_dossiers)))


def grade(project: Path, *, phase: str, release: Path | None = None,
          pcba_receipt: Path | None = None,
          catalog_request: Path | None = None,
          catalog_evidence: Path | None = None,
          catalog_decision: Path | None = None) -> dict[str, Any]:
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
        if pcba_receipt is not None:
            checks["jlc_pcba_availability"] = _pcba_check(
                pcba_receipt, phase="prelayout", predicate="availability")
            checks["procurement_exposure"] = _pcba_check(
                pcba_receipt, phase="prelayout", predicate="economics")
        else:
            checks["public_catalog_prelayout"] = _catalog_prelayout_check(
                catalog_request, catalog_evidence, catalog_decision)
            checks["procurement_exposure"] = {
                "status": checks["public_catalog_prelayout"]["status"],
                "detail": ("deferred to final JLC uploader under explicit user decision"
                           if checks["public_catalog_prelayout"]["status"] == "PASS"
                           else "catalog acceptance decision is incomplete"),
                "output": "no preorder, MOQ, allocation, or payment is authorized by this pre-layout result",
            }
            for name, path in (("catalog_request", catalog_request),
                               ("catalog_evidence", catalog_evidence),
                               ("catalog_decision", catalog_decision)):
                if path is not None and path.is_file():
                    inputs[name] = _record(path.resolve())

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
            pcba_receipt, phase="order", bom=release / "fab/bom.csv",
            predicate="availability")
        checks["order_procurement_exposure"] = _pcba_check(
            pcba_receipt, phase="order", bom=release / "fab/bom.csv",
            predicate="economics")
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


def _publish_part_freeze(result: dict[str, Any], receipt_path: Path,
                         bundle_path: Path, stage_path: Path) -> None:
    """Emit a typed shadow request; never replace an accepted bundle."""
    if result.get("phase") != "prelayout":
        raise ValueError("S-PART-FREEZE publication requires phase prelayout")
    if result.get("verdict") != "ACCEPTED":
        raise ValueError("S-PART-FREEZE cannot publish non-accepted evidence")
    semantic = {
        "phase": result["phase"], "project": result.get("project"),
        "legacy_verdict": result.get("verdict"),
        "inputs": {name: record.get("sha256")
                   for name, record in sorted(
                       (result.get("inputs") or {}).items())},
    }
    payload = json.dumps(
        semantic, sort_keys=True, separators=(",", ":")).encode("utf-8")
    identity = subject_identity("part-freeze", 1, [TypedIdentityInput(
        "readiness", "mapping", semantic, payload)])
    del receipt_path, bundle_path
    coverage = result["coverage"]
    write_shadow_stage_result(
        stage_id="S-PART-FREEZE", subject=identity,
        stage_result_path=stage_path, total=coverage["total"],
        finding_code="S-PART-PROMOTION-DISABLED",
        finding_detail=(
            "manufacturing-readiness receipt is legacy authority; accepted "
            "bundle unchanged until one atomic pointer-last transaction exists"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    grade_parser = sub.add_parser("grade")
    grade_parser.add_argument("project", type=Path)
    grade_parser.add_argument("--phase", choices=("selection", "prelayout", "order"),
                              default="selection")
    grade_parser.add_argument("--release", type=Path)
    grade_parser.add_argument("--pcba-receipt", type=Path)
    grade_parser.add_argument("--catalog-request", type=Path)
    grade_parser.add_argument("--catalog-evidence", type=Path)
    grade_parser.add_argument("--catalog-decision", type=Path)
    grade_parser.add_argument("--json", type=Path, required=True)
    grade_parser.add_argument("--stage-bundle", type=Path)
    grade_parser.add_argument("--stage-result", type=Path)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        valid, failures = verify(args.receipt)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"MANUFACTURING-READINESS RECEIPT {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1
    if bool(args.stage_bundle) != bool(args.stage_result):
        print("MANUFACTURING-READINESS INCOMPLETE: --stage-bundle and "
              "--stage-result must be supplied together")
        return 2
    output_paths = {"receipt": args.json}
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
        print(f"MANUFACTURING-READINESS INCOMPLETE: {exc}")
        return 2
    try:
        result = grade(args.project, phase=args.phase, release=args.release,
                       pcba_receipt=args.pcba_receipt,
                       catalog_request=args.catalog_request,
                       catalog_evidence=args.catalog_evidence,
                       catalog_decision=args.catalog_decision)
    except Exception as exc:
        print(f"MANUFACTURING-READINESS INCOMPLETE: {exc}")
        return 2
    try:
        require_safe_output_layout(
            output_paths,
            directory_outputs=("stage_bundle",) if args.stage_bundle else (),
            protected_paths={
                "project": args.project,
                **{f"input_{name}": Path(record["path"])
                   for name, record in (result.get("inputs") or {}).items()},
            },
        )
    except ValueError as exc:
        print(f"MANUFACTURING-READINESS INCOMPLETE: {exc}")
        return 2
    _atomic_json(args.json, result)
    if args.stage_bundle:
        try:
            _publish_part_freeze(result, args.json.resolve(),
                                 args.stage_bundle.resolve(),
                                 args.stage_result.resolve())
        except Exception as exc:
            print(f"MANUFACTURING-READINESS INCOMPLETE: shadow stage evidence: {exc}")
            # Optional part-freeze publication remains shadow authority.
            # Preserve the legacy readiness verdict and prior accepted bundle.
    coverage = result["coverage"]
    print(f"MANUFACTURING-READINESS {result['verdict']}: "
          f"{coverage['passing']}/{coverage['total']} checks pass; "
          f"phase={result['phase']}; receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
