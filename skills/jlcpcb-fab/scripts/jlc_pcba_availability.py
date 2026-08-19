#!/usr/bin/env python3
"""Create and grade hash-bound JLCPCB PCBA availability/economics receipts.

This tool deliberately does not query LCSC catalog stock.  It prepares the
exact quantity-expanded request an operator must check in JLCPCB, then grades
the saved JLCPCB response. Selection/pre-layout receipts prove AVAILABLE and
acceptable MOQ/minimum-cost exposure; order receipts prove ALLOCATED against
the exact BOM, build quantity, procurement policy and current quote.
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
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import yaml


REQUEST_KIND_V1 = "jlc-pcba-availability-request-v1"
RECEIPT_KIND_V1 = "jlc-pcba-availability-receipt-v1"
REQUEST_KIND = "jlc-pcba-availability-request-v2"
RECEIPT_KIND = "jlc-pcba-availability-receipt-v2"
PHASES = ("selection", "prelayout", "order")
RESPONSE_FIELDS_V1 = (
    "Requested LCSC", "Resolved LCSC", "PCBA Status", "Available Qty",
    "Checked At", "Evidence",
)
RESPONSE_FIELDS = (
    "Requested LCSC", "Resolved LCSC", "PCBA Status", "Available Qty",
    "Fulfillment", "Economic Status", "Public Stock Qty", "My Parts Qty",
    "Attrition Qty", "MOQ", "Order Multiple", "Preorder Purchase Qty",
    "Preorder Part Subtotal", "Preorder Fees", "Assembly Charged Qty",
    "Assembly Part Subtotal", "Currency", "Checked At", "Evidence",
)
STATUS_VOCAB = {"AVAILABLE", "ALLOCATED", "UNAVAILABLE", "INSUFFICIENT",
                "NOT_FOUND", "UNKNOWN"}
FULFILLMENT_VOCAB = {"PUBLIC_STOCK", "MY_PARTS", "PREORDER",
                     "GLOBAL_SOURCING", "CONSIGN"}
ECONOMIC_STATUS_VOCAB = {"NO_MINIMUM_COST", "QUOTED", "UNKNOWN"}
LIMIT_KEYS = (
    "max_line_preorder_cash", "max_total_preorder_cash",
    "max_line_surplus_cost", "max_total_surplus_cost",
    "max_total_assembly_excess_cost",
)


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def _decimal(raw: Any, label: str, *, blank_zero: bool = False) -> Decimal:
    text = "" if raw is None else str(raw).strip()
    if blank_zero and not text:
        return Decimal(0)
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{label} is not a decimal") from exc
    if not value.is_finite() or value < 0:
        raise ValueError(f"{label} must be a non-negative finite decimal")
    return value


def _integer(raw: Any, label: str, *, blank_zero: bool = False) -> int:
    text = "" if raw is None else str(raw).strip()
    if blank_zero and not text:
        return 0
    try:
        value = int(text)
    except ValueError as exc:
        raise ValueError(f"{label} is not a non-negative integer") from exc
    if value < 0:
        raise ValueError(f"{label} is not a non-negative integer")
    return value


def _load_policy(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("procurement policy must be a schema-1 mapping")
    currency = str(data.get("currency") or "").strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("procurement policy currency must be a three-letter code")
    raw_limits = data.get("limits") or {}
    if not isinstance(raw_limits, dict):
        raise ValueError("procurement policy limits must be a mapping")
    limits = {key: _money(_decimal(raw_limits.get(key), f"limits.{key}"))
              for key in LIMIT_KEYS}
    raw_warning = (data.get("warnings") or {}).get("surplus_ratio", 0)
    warning = _decimal(raw_warning, "warnings.surplus_ratio")
    return {"schema": 1, "currency": currency, "limits": limits,
            "warnings": {"surplus_ratio": _money(warning)}}


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
            procurement_policy: Path | None = None,
            generated_at: datetime | None = None) -> dict[str, Any]:
    if build_quantity <= 0:
        raise ValueError("build quantity must be positive")
    if phase not in PHASES:
        raise ValueError(f"unsupported phase {phase!r}")
    if procurement_policy is None or not procurement_policy.is_file():
        raise ValueError(
            "schema-v2 request requires --procurement-policy; financial "
            "limits may not be inferred")
    policy = _load_policy(procurement_policy)
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
        "schema": 2, "kind": REQUEST_KIND, "phase": phase,
        "authority_required": ("jlcpcb_order_interface" if phase == "order"
                               else "jlcpcb_pcba_interface"),
        "required_status": "ALLOCATED" if phase == "order" else "AVAILABLE",
        "generated_at": when.isoformat(), "build_quantity": build_quantity,
        "subject": _record(bom),
        "subject_role": "circuit" if bom.suffix.lower() == ".json" else "bom",
        "assembly": _record(assembly) if assembly is not None else None,
        "procurement_policy": _record(procurement_policy),
        "procurement_policy_value": policy,
        "excluded_refs": sorted(excluded),
        "coverage": {"graded": len(output_rows),
                                             "total": len(output_rows)},
        "rows": output_rows,
    }


def write_response_template(path: Path, request: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        fields = RESPONSE_FIELDS if request.get("schema") == 2 else RESPONSE_FIELDS_V1
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in request["rows"]:
            writer.writerow({"Requested LCSC": row["requested_lcsc"]})


def verify_request(path: Path, *, bom: Path, build_quantity: int, phase: str,
                   assembly: Path | None = None,
                   procurement_policy: Path | None = None
                   ) -> tuple[bool, list[str], dict[str, Any]]:
    """Prove that preserved operator input still describes current sources."""
    failures: list[str] = []
    try:
        saved = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"request cannot be read: {exc}"], {}
    if not isinstance(saved, dict):
        return False, ["request is not a JSON object"], {}
    try:
        generated_at = _timestamp(str(saved.get("generated_at") or ""))
        current = prepare(
            bom, build_quantity=build_quantity, phase=phase,
            assembly=assembly, procurement_policy=procurement_policy,
            generated_at=generated_at)
    except Exception as exc:
        return False, [f"request cannot be reproduced: {exc}"], saved
    if saved != current:
        for key in sorted(set(saved) | set(current)):
            if saved.get(key) != current.get(key):
                failures.append(f"request field {key!r} is stale or changed")
    return not failures, failures, saved


def _read_response(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(
                "response columns must be exactly: " + ", ".join(fields))
        return [{key: str(value or "").strip() for key, value in row.items()}
                for row in reader]


def grade(request_path: Path, response_path: Path, *, max_age_hours: float,
          now: datetime | None = None) -> dict[str, Any]:
    if max_age_hours <= 0:
        raise ValueError("max age must be positive")
    request = json.loads(request_path.read_text(encoding="utf-8-sig"))
    schema = request.get("schema")
    supported = ((schema == 1 and request.get("kind") == REQUEST_KIND_V1) or
                 (schema == 2 and request.get("kind") == REQUEST_KIND))
    if not supported:
        raise ValueError("unsupported request schema/kind")
    policy = request.get("procurement_policy_value") if schema == 2 else None
    if schema == 2:
        if not isinstance(policy, dict):
            raise ValueError("schema-v2 request has no procurement policy value")
        policy_record = request.get("procurement_policy") or {}
        policy_path = Path(str(policy_record.get("path") or ""))
        candidates = [policy_path, request_path.resolve().parent / policy_path.name]
        matched_policies = [
            path for path in candidates
            if path.is_file() and _sha256(path) == policy_record.get("sha256")
            and path.stat().st_size == policy_record.get("size")]
        if not matched_policies:
            raise ValueError("procurement policy moved or changed")
        if _load_policy(matched_policies[0]) != policy:
            raise ValueError("embedded procurement policy disagrees with saved policy")
    expected = {row["requested_lcsc"]: row for row in request.get("rows") or []}
    if not expected:
        raise ValueError("request has zero rows")
    fields = RESPONSE_FIELDS if schema == 2 else RESPONSE_FIELDS_V1
    response_rows = _read_response(response_path, fields)
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
            availability_status = "INCOMPLETE"
            availability_detail = "; ".join(problems)
        elif status != required_status:
            availability_status = "FAIL"
            availability_detail = f"requires {required_status}, observed {status}"
        elif available is None or available < wanted["required_qty"]:
            availability_status = "FAIL"
            availability_detail = (
                f"available {available} < required {wanted['required_qty']}")
        else:
            availability_status = "PASS"
            availability_detail = "exact code and quantity confirmed"
        result.update(availability_status=availability_status,
                      availability_detail=availability_detail)

        if schema == 1:
            result.update(status=availability_status, detail=availability_detail)
            graded_rows.append(result)
            continue

        economic_problems = []
        fulfillment = row["Fulfillment"].upper()
        economic_state = row["Economic Status"].upper()
        currency = row["Currency"].upper()
        if fulfillment not in FULFILLMENT_VOCAB:
            economic_problems.append(f"unknown fulfillment {fulfillment!r}")
        if economic_state not in ECONOMIC_STATUS_VOCAB:
            economic_problems.append(f"unknown economic status {economic_state!r}")
        if economic_state == "UNKNOWN":
            economic_problems.append("minimum-cost economics are unknown")
        numeric: dict[str, Any] = {}
        integer_fields = {
            "public_stock_qty": "Public Stock Qty",
            "my_parts_qty": "My Parts Qty", "attrition_qty": "Attrition Qty",
            "moq": "MOQ", "order_multiple": "Order Multiple",
            "preorder_purchase_qty": "Preorder Purchase Qty",
            "assembly_charged_qty": "Assembly Charged Qty",
        }
        money_fields = {
            "preorder_part_subtotal": "Preorder Part Subtotal",
            "preorder_fees": "Preorder Fees",
            "assembly_part_subtotal": "Assembly Part Subtotal",
        }
        for key, column in integer_fields.items():
            try:
                numeric[key] = _integer(row[column], column, blank_zero=True)
            except ValueError as exc:
                economic_problems.append(str(exc))
                numeric[key] = 0
        for key, column in money_fields.items():
            try:
                numeric[key] = _decimal(row[column], column, blank_zero=True)
            except ValueError as exc:
                economic_problems.append(str(exc))
                numeric[key] = Decimal(0)
        if currency != policy["currency"]:
            economic_problems.append(
                f"currency {currency or '<blank>'} != policy {policy['currency']}")
        if fulfillment in {"PREORDER", "GLOBAL_SOURCING"} and economic_state != "QUOTED":
            economic_problems.append(f"{fulfillment} requires QUOTED economics")
        purchase = numeric["preorder_purchase_qty"]
        moq = numeric["moq"]
        multiple = numeric["order_multiple"]
        need = wanted["required_qty"] + numeric["attrition_qty"]
        if purchase and purchase < moq:
            economic_problems.append(f"purchase quantity {purchase} < MOQ {moq}")
        if purchase and multiple and purchase % multiple:
            economic_problems.append(
                f"purchase quantity {purchase} is not a multiple of {multiple}")
        if fulfillment in {"PREORDER", "GLOBAL_SOURCING"} and purchase <= 0:
            economic_problems.append(f"{fulfillment} requires a purchase quantity")
        if (purchase > 0 and
                not row["Preorder Part Subtotal"].strip()):
            economic_problems.append(
                "purchase quantity requires exact Preorder Part Subtotal")
        if purchase == 0 and (numeric["preorder_part_subtotal"] or
                              numeric["preorder_fees"]):
            economic_problems.append("preorder cost exists with zero purchase quantity")
        if (numeric["assembly_charged_qty"] > 0 and
                not row["Assembly Part Subtotal"].strip()):
            economic_problems.append(
                "assembly charged quantity requires exact Assembly Part Subtotal")
        if (economic_state == "QUOTED" and purchase == 0 and
                numeric["assembly_charged_qty"] == 0):
            economic_problems.append(
                "QUOTED economics has neither preorder nor assembly charge")
        if (economic_state == "NO_MINIMUM_COST" and
                availability_status == "PASS" and
                fulfillment in {"PUBLIC_STOCK", "MY_PARTS"} and
                numeric["public_stock_qty"] + numeric["my_parts_qty"] < need):
            economic_problems.append(
                "NO_MINIMUM_COST public/My Parts quantities do not cover need")
        if economic_state == "NO_MINIMUM_COST" and any((
                purchase, numeric["preorder_part_subtotal"],
                numeric["preorder_fees"], numeric["assembly_charged_qty"],
                numeric["assembly_part_subtotal"])):
            economic_problems.append(
                "NO_MINIMUM_COST row contains purchase or minimum-charge values")
        shortfall = max(
            0, need - numeric["public_stock_qty"] - numeric["my_parts_qty"])
        surplus_qty = max(0, purchase - shortfall)
        preorder_subtotal = numeric["preorder_part_subtotal"]
        preorder_cash = preorder_subtotal + numeric["preorder_fees"]
        surplus_cost = ((preorder_subtotal * Decimal(surplus_qty) / Decimal(purchase))
                        if purchase else Decimal(0))
        charged = numeric["assembly_charged_qty"]
        assembly_excess_qty = max(0, charged - need)
        assembly_subtotal = numeric["assembly_part_subtotal"]
        assembly_excess_cost = (
            assembly_subtotal * Decimal(assembly_excess_qty) / Decimal(charged)
            if charged else Decimal(0))
        surplus_ratio = ((Decimal(purchase) / Decimal(max(shortfall, 1)))
                         if purchase else Decimal(0))
        metrics = {
            **{key: (_money(value) if isinstance(value, Decimal) else value)
               for key, value in numeric.items()},
            "fulfillment": fulfillment or None,
            "economic_state": economic_state or None,
            "currency": currency or None,
            "need_with_attrition": need, "preorder_shortfall": shortfall,
            "preorder_surplus_qty": surplus_qty,
            "preorder_cash_outlay": _money(preorder_cash),
            "preorder_surplus_cost": _money(surplus_cost),
            "assembly_excess_qty": assembly_excess_qty,
            "assembly_excess_cost": _money(assembly_excess_cost),
            "minimum_cost_exposure": _money(preorder_cash + assembly_excess_cost),
            "surplus_ratio": _money(surplus_ratio),
        }
        limits = {key: Decimal(str(value)) for key, value in policy["limits"].items()}
        economic_failures = []
        if preorder_cash > limits["max_line_preorder_cash"]:
            economic_failures.append(
                f"preorder cash {_money(preorder_cash)} exceeds line limit "
                f"{_money(limits['max_line_preorder_cash'])}")
        if surplus_cost > limits["max_line_surplus_cost"]:
            economic_failures.append(
                f"surplus cost {_money(surplus_cost)} exceeds line limit "
                f"{_money(limits['max_line_surplus_cost'])}")
        if economic_problems:
            economic_status = "INCOMPLETE"
            economic_detail = "; ".join(economic_problems)
        elif economic_failures:
            economic_status = "FAIL"
            economic_detail = "; ".join(economic_failures)
        else:
            economic_status = "PASS"
            economic_detail = "fulfillment and minimum-cost exposure confirmed"
        warnings = []
        warning_ratio = Decimal(str(policy["warnings"]["surplus_ratio"]))
        if warning_ratio and surplus_ratio > warning_ratio:
            warnings.append(
                f"surplus ratio {_money(surplus_ratio)} exceeds advisory "
                f"{_money(warning_ratio)}")
        result.update(economics_status=economic_status,
                      economics_detail=economic_detail,
                      economics=metrics, warnings=warnings)
        statuses = {availability_status, economic_status}
        composite = ("INCOMPLETE" if "INCOMPLETE" in statuses else
                     "FAIL" if "FAIL" in statuses else "PASS")
        detail = f"availability: {availability_detail}; economics: {economic_detail}"
        result.update(status=composite, detail=detail)
        graded_rows.append(result)

    procurement_summary = None
    if schema == 2:
        totals = {
            "preorder_cash_outlay": sum(
                Decimal(row["economics"]["preorder_cash_outlay"])
                for row in graded_rows if row.get("economics")),
            "preorder_surplus_cost": sum(
                Decimal(row["economics"]["preorder_surplus_cost"])
                for row in graded_rows if row.get("economics")),
            "assembly_excess_cost": sum(
                Decimal(row["economics"]["assembly_excess_cost"])
                for row in graded_rows if row.get("economics")),
            "minimum_cost_exposure": sum(
                Decimal(row["economics"]["minimum_cost_exposure"])
                for row in graded_rows if row.get("economics")),
        }
        limits = {key: Decimal(str(value)) for key, value in policy["limits"].items()}
        aggregate_checks = (
            ("preorder_cash_outlay", "max_total_preorder_cash"),
            ("preorder_surplus_cost", "max_total_surplus_cost"),
            ("assembly_excess_cost", "max_total_assembly_excess_cost"),
        )
        aggregate_findings = []
        for metric, limit_key in aggregate_checks:
            if totals[metric] > limits[limit_key]:
                aggregate_findings.append(
                    f"aggregate {metric} {_money(totals[metric])} exceeds "
                    f"{limit_key} {_money(limits[limit_key])}")
        findings.extend({"status": "FAIL", "lcsc": "<aggregate>",
                         "detail": detail} for detail in aggregate_findings)
        procurement_summary = {
            "currency": policy["currency"],
            "totals": {key: _money(value) for key, value in totals.items()},
            "limits": policy["limits"],
            "status": ("INCOMPLETE" if any(
                row.get("economics_status") in {None, "INCOMPLETE"}
                for row in graded_rows)
                else "FAIL" if aggregate_findings or any(
                    row.get("economics_status") == "FAIL" for row in graded_rows)
                else "PASS"),
        }

    incomplete = bool(any(row["status"] == "INCOMPLETE" for row in graded_rows)
                      or any(row["status"] == "INCOMPLETE" for row in findings))
    failed = bool(any(row["status"] == "FAIL" for row in graded_rows)
                  or any(row["status"] == "FAIL" for row in findings))
    verdict = "INCOMPLETE" if incomplete else "REJECTED" if failed else "ACCEPTED"
    passed = sum(row["status"] == "PASS" for row in graded_rows)
    checked_times = [_timestamp(str(row["checked_at"])) for row in graded_rows
                     if row.get("checked_at") and row["status"] != "INCOMPLETE"]
    valid_until = ((min(checked_times) + timedelta(hours=max_age_hours))
                   if checked_times else current)
    receipt = {
        "schema": schema,
        "kind": RECEIPT_KIND if schema == 2 else RECEIPT_KIND_V1,
        "phase": request["phase"],
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
    if schema == 2:
        receipt.update(
            procurement_policy=request.get("procurement_policy"),
            procurement_policy_value=policy,
            availability_verdict=(
                "INCOMPLETE" if any(row["availability_status"] == "INCOMPLETE"
                                    for row in graded_rows)
                else "REJECTED" if any(row["availability_status"] == "FAIL"
                                       for row in graded_rows)
                else "ACCEPTED"),
            economics_verdict=(
                "INCOMPLETE" if procurement_summary["status"] == "INCOMPLETE"
                else "REJECTED" if procurement_summary["status"] == "FAIL"
                else "ACCEPTED"),
            procurement=procurement_summary)
    return receipt


def verify_receipt(path: Path, *, bom: Path | None = None,
                   required_phase: str | None = None,
                   now: datetime | None = None) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"], {}
    schema = receipt.get("schema")
    supported = ((schema == 1 and receipt.get("kind") == RECEIPT_KIND_V1) or
                 (schema == 2 and receipt.get("kind") == RECEIPT_KIND))
    if not supported:
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
    if schema == 2:
        for name in ("availability_verdict", "economics_verdict"):
            if receipt.get(name) not in {"ACCEPTED", "REJECTED", "INCOMPLETE"}:
                failures.append(f"receipt {name} is invalid")
        if verdict == "ACCEPTED" and receipt.get("economics_verdict") != "ACCEPTED":
            failures.append("accepted receipt has non-accepted economics")
    if not failures and set(evidence_paths) == {"request", "response"}:
        try:
            regenerated = grade(
                evidence_paths["request"], evidence_paths["response"],
                max_age_hours=float(receipt.get("max_age_hours")),
                now=_timestamp(str(receipt.get("generated_at") or "")))
            stable = ("schema", "kind", "phase", "authority", "verdict", "generated_at",
                      "max_age_hours", "valid_until", "build_quantity",
                      "subject", "subject_role", "assembly", "coverage",
                      "rows", "findings", "scope")
            if schema == 2:
                stable += ("procurement_policy", "procurement_policy_value",
                           "availability_verdict", "economics_verdict",
                           "procurement")
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
    p_prepare.add_argument("--procurement-policy", type=Path, required=True,
                           help="durable project financial limits")
    p_prepare.add_argument("--out", type=Path, required=True)
    p_prepare.add_argument("--response-template", type=Path)
    p_grade = commands.add_parser("grade")
    p_grade.add_argument("request", type=Path)
    p_grade.add_argument("response", type=Path)
    p_grade.add_argument("--max-age-hours", type=float, default=24)
    p_grade.add_argument("--out", type=Path, required=True)
    p_verify_request = commands.add_parser("verify-request")
    p_verify_request.add_argument("request", type=Path)
    p_verify_request.add_argument("--bom", type=Path, required=True)
    p_verify_request.add_argument("--build-quantity", type=int, required=True)
    p_verify_request.add_argument("--phase", choices=PHASES, required=True)
    p_verify_request.add_argument("--assembly", type=Path)
    p_verify_request.add_argument("--procurement-policy", type=Path,
                                  required=True)
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
                             phase=args.phase, assembly=args.assembly,
                             procurement_policy=args.procurement_policy)
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
        if args.command == "verify-request":
            valid, failures, request = verify_request(
                args.request, bom=args.bom,
                build_quantity=args.build_quantity, phase=args.phase,
                assembly=args.assembly,
                procurement_policy=args.procurement_policy)
            for failure in failures:
                print(f"  FAIL {failure}")
            print(f"JLC-PCBA REQUEST {'PASS' if valid else 'FAIL'}: "
                  f"phase={request.get('phase', 'UNREADABLE')}")
            return 0 if valid else 1
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
