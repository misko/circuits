#!/usr/bin/env python3
"""Create and grade hash-bound JLCPCB PCBA availability receipts.

This tool deliberately does not query LCSC catalog stock.  It prepares the
exact quantity-expanded request an operator must check in JLCPCB, then grades
the saved JLCPCB response.  Selection/pre-layout receipts prove AVAILABLE;
order receipts prove ALLOCATED for one exact BOM and build quantity.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


REQUEST_KIND = "jlc-pcba-availability-request-v1"
RECEIPT_KIND = "jlc-pcba-availability-receipt-v1"
PHASES = ("selection", "prelayout", "order")
RESPONSE_FIELDS = (
    "Requested LCSC", "Resolved LCSC", "PCBA Status", "Available Qty",
    "Checked At", "Evidence",
)
STATUS_VOCAB = {"AVAILABLE", "ALLOCATED", "UNAVAILABLE", "INSUFFICIENT",
                "NOT_FOUND", "UNKNOWN"}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _record(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "sha256": _sha256(path),
            "size": path.stat().st_size}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return parsed


def _designators(raw: str) -> list[str]:
    return [token.strip() for token in re.split(r"[,;]", raw or "")
            if token.strip()]


def _source_rows(source: Path) -> list[dict[str, str]]:
    if source.suffix.lower() != ".json":
        return list(csv.DictReader(source.open(encoding="utf-8-sig", newline="")))
    data = json.loads(source.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("Circuit JSON must contain a list")
    rows = []
    for item in data:
        if not isinstance(item, dict) or item.get("type") != "source_component":
            continue
        supplier = ((item.get("supplier_part_numbers") or {}).get("jlcpcb") or [])
        if isinstance(supplier, str):
            supplier = [supplier]
        codes = [str(value).strip() for value in supplier
                 if re.fullmatch(r"C\d+", str(value).strip())]
        rows.append({"LCSC": codes[0] if len(codes) == 1 else "",
                     "Designator": str(item.get("name") or ""),
                     "Comment": str(item.get("ftype") or item.get("value") or "")})
    return rows


def _excluded_refs(assembly: Path | None) -> set[str]:
    if assembly is None:
        return set()
    data = yaml.safe_load(assembly.read_text(encoding="utf-8-sig")) or {}
    return {str(ref) for row in data.get("not_assembled") or []
            if isinstance(row, dict) for ref in row.get("refs") or []}


def prepare(bom: Path, *, build_quantity: int, phase: str,
            assembly: Path | None = None,
            generated_at: datetime | None = None) -> dict[str, Any]:
    if build_quantity <= 0:
        raise ValueError("build quantity must be positive")
    if phase not in PHASES:
        raise ValueError(f"unsupported phase {phase!r}")
    rows = _source_rows(bom)
    if not rows:
        raise ValueError("BOM has zero data rows")
    excluded = _excluded_refs(assembly)
    grouped: dict[str, dict[str, Any]] = {}
    uncoded = []
    for index, row in enumerate(rows, 2):
        code = str(row.get("LCSC") or "").strip()
        refs = [ref for ref in _designators(str(row.get("Designator") or ""))
                if ref not in excluded]
        if not refs:
            continue
        if not refs:
            raise ValueError(f"BOM row {index} has no designators")
        if not re.fullmatch(r"C\d+", code):
            uncoded.append({"row": index, "designators": refs,
                            "value": str(row.get("Comment") or "")})
            continue
        entry = grouped.setdefault(code, {"requested_lcsc": code,
                                          "designators": []})
        entry["designators"].extend(refs)
    if uncoded:
        names = ", ".join(ref for row in uncoded for ref in row["designators"])
        raise ValueError(
            f"{len(uncoded)} BOM row(s) have no exact LCSC code ({names}); "
            "remove non-PCBA/manual rows before preparing the JLC request")
    if not grouped:
        raise ValueError("BOM has zero coded PCBA rows")
    output_rows = []
    for code, row in sorted(grouped.items()):
        refs = sorted(set(row["designators"]))
        output_rows.append({"requested_lcsc": code, "designators": refs,
                            "per_board_qty": len(refs),
                            "required_qty": len(refs) * build_quantity})
    when = generated_at or _now()
    return {
        "schema": 1, "kind": REQUEST_KIND, "phase": phase,
        "authority_required": ("jlcpcb_order_interface" if phase == "order"
                               else "jlcpcb_pcba_interface"),
        "required_status": "ALLOCATED" if phase == "order" else "AVAILABLE",
        "generated_at": when.isoformat(), "build_quantity": build_quantity,
        "subject": _record(bom),
        "subject_role": "circuit" if bom.suffix.lower() == ".json" else "bom",
        "assembly": _record(assembly) if assembly is not None else None,
        "excluded_refs": sorted(excluded),
        "coverage": {"graded": len(output_rows),
                                             "total": len(output_rows)},
        "rows": output_rows,
    }


def write_response_template(path: Path, request: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=RESPONSE_FIELDS)
        writer.writeheader()
        for row in request["rows"]:
            writer.writerow({"Requested LCSC": row["requested_lcsc"]})


def _read_response(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != RESPONSE_FIELDS:
            raise ValueError(
                "response columns must be exactly: " + ", ".join(RESPONSE_FIELDS))
        return [{key: str(value or "").strip() for key, value in row.items()}
                for row in reader]


def grade(request_path: Path, response_path: Path, *, max_age_hours: float,
          now: datetime | None = None) -> dict[str, Any]:
    if max_age_hours <= 0:
        raise ValueError("max age must be positive")
    request = json.loads(request_path.read_text(encoding="utf-8-sig"))
    if request.get("schema") != 1 or request.get("kind") != REQUEST_KIND:
        raise ValueError("unsupported request schema/kind")
    expected = {row["requested_lcsc"]: row for row in request.get("rows") or []}
    if not expected:
        raise ValueError("request has zero rows")
    response_rows = _read_response(response_path)
    seen: dict[str, dict[str, str]] = {}
    findings: list[dict[str, str]] = []
    for row in response_rows:
        code = row["Requested LCSC"]
        if code in seen:
            findings.append({"status": "INCOMPLETE", "lcsc": code,
                             "detail": "duplicate response row"})
            continue
        seen[code] = row
        if code not in expected:
            findings.append({"status": "INCOMPLETE", "lcsc": code,
                             "detail": "response row was not requested"})
    current = now or _now()
    required_status = request["required_status"]
    graded_rows = []
    for code, wanted in sorted(expected.items()):
        row = seen.get(code)
        result = {**wanted, "resolved_lcsc": None, "pcba_status": None,
                  "available_qty": None, "checked_at": None,
                  "evidence": None, "status": "INCOMPLETE", "detail": ""}
        if row is None:
            result["detail"] = "missing response row"
            graded_rows.append(result)
            continue
        resolved = row["Resolved LCSC"]
        status = row["PCBA Status"].upper()
        result.update(resolved_lcsc=resolved or None, pcba_status=status or None,
                      checked_at=row["Checked At"] or None,
                      evidence=row["Evidence"] or None)
        problems = []
        if status not in STATUS_VOCAB:
            problems.append(f"unknown PCBA status {status!r}")
        if resolved != code:
            problems.append(f"resolved code {resolved or '<blank>'} != requested {code}")
        try:
            available = int(row["Available Qty"])
            if available < 0:
                raise ValueError
            result["available_qty"] = available
        except ValueError:
            problems.append("Available Qty is not a non-negative integer")
            available = None
        try:
            checked = _timestamp(row["Checked At"])
            age = current - checked.astimezone(timezone.utc)
            if age < timedelta(0):
                problems.append("Checked At is in the future")
            elif age > timedelta(hours=max_age_hours):
                problems.append(f"evidence is older than {max_age_hours:g} hours")
        except (TypeError, ValueError):
            problems.append("Checked At is not an RFC3339 timestamp")
        if not row["Evidence"]:
            problems.append("Evidence is blank")
        if problems:
            result.update(status="INCOMPLETE", detail="; ".join(problems))
        elif status != required_status:
            result.update(status="FAIL",
                          detail=f"requires {required_status}, observed {status}")
        elif available is None or available < wanted["required_qty"]:
            result.update(
                status="FAIL",
                detail=f"available {available} < required {wanted['required_qty']}")
        else:
            result.update(status="PASS", detail="exact code and quantity confirmed")
        graded_rows.append(result)
    incomplete = bool(any(row["status"] == "INCOMPLETE" for row in graded_rows)
                      or findings)
    failed = any(row["status"] == "FAIL" for row in graded_rows)
    verdict = "INCOMPLETE" if incomplete else "REJECTED" if failed else "ACCEPTED"
    passed = sum(row["status"] == "PASS" for row in graded_rows)
    checked_times = [_timestamp(str(row["checked_at"])) for row in graded_rows
                     if row.get("checked_at") and row["status"] != "INCOMPLETE"]
    valid_until = ((min(checked_times) + timedelta(hours=max_age_hours))
                   if checked_times else current)
    return {
        "schema": 1, "kind": RECEIPT_KIND, "phase": request["phase"],
        "authority": request["authority_required"], "verdict": verdict,
        "generated_at": current.isoformat(),
        "max_age_hours": max_age_hours,
        "valid_until": valid_until.isoformat(),
        "build_quantity": request["build_quantity"],
        "subject": request["subject"], "subject_role": request["subject_role"],
        "assembly": request.get("assembly"), "request": _record(request_path),
        "response": _record(response_path),
        "coverage": {"passing": passed, "graded": len(graded_rows),
                     "total": len(expected)},
        "rows": graded_rows, "findings": findings,
        "scope": ("JLCPCB PCBA interface evidence for this exact BOM and "
                  "build quantity; LCSC catalog stock is not an authority"),
    }


def verify_receipt(path: Path, *, bom: Path | None = None,
                   required_phase: str | None = None,
                   now: datetime | None = None) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"], {}
    if receipt.get("schema") != 1 or receipt.get("kind") != RECEIPT_KIND:
        failures.append("unsupported receipt schema/kind")
    if required_phase and receipt.get("phase") != required_phase:
        failures.append(
            f"receipt phase {receipt.get('phase')!r} != required {required_phase!r}")
    expected_authority = ("jlcpcb_order_interface" if receipt.get("phase") == "order"
                          else "jlcpcb_pcba_interface")
    if receipt.get("authority") != expected_authority:
        failures.append("receipt authority does not match its phase")
    evidence_paths: dict[str, Path] = {}
    for name in ("request", "response"):
        record = receipt.get(name) or {}
        recorded = Path(str(record.get("path") or ""))
        candidates = [recorded, path.resolve().parent / recorded.name]
        matched = any(candidate.is_file()
                      and candidate.stat().st_size == record.get("size")
                      and _sha256(candidate) == record.get("sha256")
                      for candidate in candidates)
        if not matched:
            failures.append(f"{name} evidence moved or changed")
        else:
            evidence_paths[name] = next(
                candidate for candidate in candidates if candidate.is_file()
                and candidate.stat().st_size == record.get("size")
                and _sha256(candidate) == record.get("sha256"))
    if bom is not None:
        if not bom.is_file() or _sha256(bom) != (receipt.get("subject") or {}).get("sha256"):
            failures.append("receipt is not bound to the current subject/BOM")
    try:
        if (now or _now()) > _timestamp(str(receipt.get("valid_until") or "")):
            failures.append("receipt is stale")
    except ValueError:
        failures.append("receipt valid_until is invalid")
    rows = receipt.get("rows") or []
    coverage = receipt.get("coverage") or {}
    if not rows or coverage.get("graded") != coverage.get("total") or len(rows) != coverage.get("total"):
        failures.append("receipt coverage is partial or zero")
    verdict = receipt.get("verdict")
    if verdict not in {"ACCEPTED", "REJECTED", "INCOMPLETE"}:
        failures.append("receipt verdict is invalid")
    if verdict == "ACCEPTED" and any(row.get("status") != "PASS" for row in rows):
        failures.append("accepted receipt contains a non-passing row")
    if not failures and set(evidence_paths) == {"request", "response"}:
        try:
            regenerated = grade(
                evidence_paths["request"], evidence_paths["response"],
                max_age_hours=float(receipt.get("max_age_hours")),
                now=_timestamp(str(receipt.get("generated_at") or "")))
            stable = ("phase", "authority", "verdict", "generated_at",
                      "max_age_hours", "valid_until", "build_quantity",
                      "subject", "subject_role", "assembly", "coverage",
                      "rows", "findings", "scope")
            if any(receipt.get(key) != regenerated.get(key) for key in stable):
                failures.append("receipt does not reproduce from saved evidence")
        except (TypeError, ValueError) as exc:
            failures.append(f"receipt cannot be reproduced: {exc}")
    return not failures, failures, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p_prepare = commands.add_parser("prepare")
    p_prepare.add_argument("bom", type=Path)
    p_prepare.add_argument("--build-quantity", type=int, required=True)
    p_prepare.add_argument("--phase", choices=PHASES, required=True)
    p_prepare.add_argument("--assembly", type=Path,
                           help="assembly.yaml; not_assembled refs are excluded")
    p_prepare.add_argument("--out", type=Path, required=True)
    p_prepare.add_argument("--response-template", type=Path)
    p_grade = commands.add_parser("grade")
    p_grade.add_argument("request", type=Path)
    p_grade.add_argument("response", type=Path)
    p_grade.add_argument("--max-age-hours", type=float, default=24)
    p_grade.add_argument("--out", type=Path, required=True)
    p_verify = commands.add_parser("verify")
    p_verify.add_argument("receipt", type=Path)
    p_verify.add_argument("--bom", type=Path)
    p_verify.add_argument("--phase", choices=PHASES)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            occupied = [path for path in (args.out, args.response_template)
                        if path is not None and path.exists()]
            if occupied:
                raise ValueError(
                    "refusing to overwrite existing request/operator evidence: "
                    + ", ".join(str(path) for path in occupied))
            result = prepare(args.bom, build_quantity=args.build_quantity,
                             phase=args.phase, assembly=args.assembly)
            _atomic_json(args.out, result)
            if args.response_template:
                write_response_template(args.response_template, result)
            print(f"JLC-PCBA REQUEST PASS: {len(result['rows'])}/"
                  f"{len(result['rows'])} exact code(s); phase={result['phase']}")
            return 0
        if args.command == "grade":
            if args.out.exists():
                raise ValueError(f"refusing to overwrite existing receipt: {args.out}")
            result = grade(args.request, args.response,
                           max_age_hours=args.max_age_hours)
            _atomic_json(args.out, result)
            count = result["coverage"]
            print(f"JLC-PCBA {result['verdict']}: {count['passing']}/"
                  f"{count['total']} line(s) pass; receipt={args.out.resolve()}")
            return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[result["verdict"]]
        valid, failures, receipt = verify_receipt(
            args.receipt, bom=args.bom, required_phase=args.phase)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"JLC-PCBA RECEIPT {'PASS' if valid else 'FAIL'}: "
              f"verdict={receipt.get('verdict', 'UNREADABLE')}")
        return 0 if valid else 1
    except Exception as exc:
        print(f"JLC-PCBA INCOMPLETE: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
