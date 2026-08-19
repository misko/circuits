#!/usr/bin/env python3
"""T1: JLCPCB PCBA availability/allocation is distinct from catalog stock."""
from __future__ import annotations

import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/jlcpcb-fab/scripts"))
import jlc_pcba_availability as pcba  # noqa: E402
import manufacturing_readiness  # noqa: E402
import release_freshness_check as freshness  # noqa: E402

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def policy_file(root, *, line_cash="0", total_cash="0", line_surplus="0",
                total_surplus="0", assembly_excess="0"):
    path = root / "procurement-policy.yaml"
    path.write_text(
        "schema: 1\ncurrency: USD\nlimits:\n"
        f"  max_line_preorder_cash: {line_cash}\n"
        f"  max_total_preorder_cash: {total_cash}\n"
        f"  max_line_surplus_cost: {line_surplus}\n"
        f"  max_total_surplus_cost: {total_surplus}\n"
        f"  max_total_assembly_excess_cost: {assembly_excess}\n"
        "warnings:\n  surplus_ratio: 20\n", encoding="utf-8")
    return path


def fixture(*, phase="prelayout", status="AVAILABLE", resolved="C100",
            available="20", checked="2026-08-18T11:00:00Z",
            economics=None, limits=None):
    root = tmpdir("pcba_")
    bom = root / "bom.csv"
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n"
        "10k,R1,R_0402,C100\n"
        "10k,R2,R_0402,C100\n"
        "1uF,C1,C_0402,C200\n", encoding="utf-8")
    policy = policy_file(root, **(limits or {}))
    request = pcba.prepare(bom, build_quantity=5, phase=phase,
                           procurement_policy=policy,
                           generated_at=NOW)
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    response = root / "response.csv"
    with response.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=pcba.RESPONSE_FIELDS)
        writer.writeheader()
        base = {"Fulfillment": "PUBLIC_STOCK",
                "Economic Status": "NO_MINIMUM_COST",
                "Public Stock Qty": available, "My Parts Qty": "0",
                "Attrition Qty": "0", "MOQ": "0", "Order Multiple": "0",
                "Preorder Purchase Qty": "0", "Preorder Part Subtotal": "0",
                "Preorder Fees": "0", "Assembly Charged Qty": "0",
                "Assembly Part Subtotal": "0", "Currency": "USD"}
        first = {**base, **(economics or {})}
        writer.writerow({"Requested LCSC": "C100", "Resolved LCSC": resolved,
                         "PCBA Status": status, "Available Qty": available,
                         "Checked At": checked, "Evidence": "JLC upload row 1",
                         **first})
        writer.writerow({"Requested LCSC": "C200", "Resolved LCSC": "C200",
                         "PCBA Status": ("ALLOCATED" if phase == "order" else
                                         "AVAILABLE"),
                         "Available Qty": "10", "Checked At": checked,
                         "Evidence": "JLC upload row 2",
                         **{**base, "Public Stock Qty": "10"}})
    receipt = pcba.grade(request_path, response, max_age_hours=24, now=NOW)
    receipt_path = root / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    return root, bom, request, response, receipt, receipt_path


@test("prelayout request expands exact codes by placements and board quantity")
def t_quantity_expansion():
    _, _, request, _, receipt, _ = fixture()
    rows = {row["requested_lcsc"]: row for row in request["rows"]}
    eq(rows["C100"]["per_board_qty"], 2, "per-board grouped quantity")
    eq(rows["C100"]["required_qty"], 10, "order quantity expansion")
    eq(receipt["verdict"], "ACCEPTED", "available preliminary BOM")
    check("catalog" not in receipt["authority"],
          "catalog authority leaked into PCBA receipt")


@test("prelayout request reads Circuit JSON and excludes declared manual refs")
def t_circuit_source_and_manual_exclusion():
    root = tmpdir("pcba_circuit_")
    circuit = root / "circuit.json"
    circuit.write_text(json.dumps([
        {"type": "source_component", "name": "U1",
         "supplier_part_numbers": {"jlcpcb": ["C100"]}},
        {"type": "source_component", "name": "F1",
         "supplier_part_numbers": {"jlcpcb": []}},
    ]), encoding="utf-8")
    assembly = root / "assembly.yaml"
    assembly.write_text(
        "not_assembled:\n  - refs: [F1]\n    reason: user_supplied\n",
        encoding="utf-8")
    request = pcba.prepare(
        circuit, build_quantity=3, phase="prelayout", assembly=assembly,
        procurement_policy=policy_file(root), generated_at=NOW)
    eq([row["requested_lcsc"] for row in request["rows"]], ["C100"],
       "PCBA population set")
    eq(request["excluded_refs"], ["F1"], "manual exclusion")


@test("saved prelayout request reproduces only against its exact current inputs")
def t_request_freshness():
    root = tmpdir("pcba_request_fresh_")
    bom = root / "bom.csv"
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n10k,R1,R_0402,C100\n",
        encoding="utf-8")
    policy = policy_file(root)
    request = pcba.prepare(
        bom, build_quantity=5, phase="prelayout",
        procurement_policy=policy, generated_at=NOW)
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    valid, failures, _ = pcba.verify_request(
        request_path, bom=bom, build_quantity=5, phase="prelayout",
        procurement_policy=policy)
    check(valid and not failures, f"fresh request refused: {failures}")


@test("saved prelayout request fails after its BOM changes", kind="known_bad")
def t_request_stale_after_bom_change():
    root = tmpdir("pcba_request_stale_")
    bom = root / "bom.csv"
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n10k,R1,R_0402,C100\n",
        encoding="utf-8")
    policy = policy_file(root)
    request = pcba.prepare(
        bom, build_quantity=5, phase="prelayout",
        procurement_policy=policy, generated_at=NOW)
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n10k,R1,R_0402,C999\n",
        encoding="utf-8")
    valid, failures, _ = pcba.verify_request(
        request_path, bom=bom, build_quantity=5, phase="prelayout",
        procurement_policy=policy)
    check(not valid, "stale request passed after BOM changed")
    check(any("subject" in failure or "rows" in failure for failure in failures),
          f"stale request diagnosis missing: {failures}")


@test("catalog availability cannot clear an unavailable JLCPCB PCBA row",
      kind="known_bad")
def t_catalog_is_not_pcba():
    _, _, _, _, receipt, _ = fixture(status="UNAVAILABLE", available="999999")
    eq(receipt["verdict"], "REJECTED", "JLCPCB unavailable verdict")
    failed = [row for row in receipt["rows"] if row["status"] == "FAIL"]
    eq([row["requested_lcsc"] for row in failed], ["C100"], "blocked code")


@test("JLC-resolved substitution fails closed", kind="known_bad")
def t_substitution():
    _, _, _, _, receipt, _ = fixture(resolved="C999")
    eq(receipt["verdict"], "INCOMPLETE", "substitution verdict")
    check("resolved code C999" in receipt["rows"][0]["detail"],
          "substitution diagnosis missing")


@test("insufficient JLCPCB quantity rejects the exact line", kind="known_bad")
def t_insufficient_quantity():
    _, _, _, _, receipt, _ = fixture(available="9")
    eq(receipt["verdict"], "REJECTED", "quantity verdict")
    check("available 9 < required 10" in receipt["rows"][0]["detail"],
          "required quantity diagnosis missing")


@test("order phase requires ALLOCATED rather than AVAILABLE", kind="known_bad")
def t_order_requires_allocation():
    _, _, _, _, receipt, _ = fixture(phase="order", status="AVAILABLE")
    eq(receipt["verdict"], "REJECTED", "order availability is not allocation")
    check("requires ALLOCATED" in receipt["rows"][0]["detail"],
          "allocation diagnosis missing")


@test("exact final BOM allocation receipt verifies")
def t_order_allocation_clean():
    _, bom, _, _, _, receipt_path = fixture(phase="order", status="ALLOCATED")
    valid, failures, receipt = pcba.verify_receipt(
        receipt_path, bom=bom, required_phase="order", now=NOW)
    check(valid and not failures, f"clean allocation receipt refused: {failures}")
    eq(receipt["verdict"], "ACCEPTED", "allocation receipt")


@test("stale JLCPCB UI evidence is incomplete", kind="known_bad")
def t_stale():
    _, _, _, _, receipt, _ = fixture(checked="2026-08-16T11:00:00Z")
    eq(receipt["verdict"], "INCOMPLETE", "stale verdict")
    check("older than 24 hours" in receipt["rows"][0]["detail"],
          "stale diagnosis missing")


@test("stocked basic part ignores preorder MOQ when no preorder is used")
def t_stocked_basic_moq_is_zero_exposure():
    _, _, _, _, receipt, _ = fixture(
        available="7154521",
        economics={"Public Stock Qty": "7154521", "MOQ": "1195"})
    row = next(row for row in receipt["rows"]
               if row["requested_lcsc"] == "C100")
    eq(receipt["economics_verdict"], "ACCEPTED", "economic verdict")
    eq(row["economics"]["preorder_surplus_qty"], 0, "surplus quantity")
    eq(row["economics"]["preorder_surplus_cost"], "0.000000",
       "surplus cost")


@test("cheap high-MOQ preorder is graded by gross surplus cost")
def t_cheap_preorder():
    _, _, _, _, receipt, _ = fixture(
        economics={
            "Fulfillment": "PREORDER", "Economic Status": "QUOTED",
            "Public Stock Qty": "0", "MOQ": "1195", "Order Multiple": "1",
            "Preorder Purchase Qty": "1195",
            "Preorder Part Subtotal": "1.195", "Preorder Fees": "0"},
        limits={"line_cash": "2", "total_cash": "2",
                "line_surplus": "2", "total_surplus": "2"})
    row = next(row for row in receipt["rows"]
               if row["requested_lcsc"] == "C100")
    eq(receipt["economics_verdict"], "ACCEPTED", "cheap preorder verdict")
    eq(row["economics"]["preorder_surplus_qty"], 1185, "surplus quantity")
    eq(row["economics"]["preorder_surplus_cost"], "1.185000",
       "gross surplus cost")


@test("expensive high-MOQ preorder fails monetary policy", kind="known_bad")
def t_expensive_preorder():
    _, _, _, _, receipt, _ = fixture(
        economics={
            "Fulfillment": "PREORDER", "Economic Status": "QUOTED",
            "Public Stock Qty": "0", "MOQ": "1195", "Order Multiple": "1",
            "Preorder Purchase Qty": "1195",
            "Preorder Part Subtotal": "298.75", "Preorder Fees": "0"},
        limits={"line_cash": "50", "total_cash": "50",
                "line_surplus": "50", "total_surplus": "50"})
    eq(receipt["economics_verdict"], "REJECTED", "expensive MOQ verdict")
    row = next(row for row in receipt["rows"]
               if row["requested_lcsc"] == "C100")
    check("surplus cost" in row["economics_detail"],
          "monetary rejection did not name surplus cost")


@test("aggregate preorder cash limit catches individually acceptable line",
      kind="known_bad")
def t_aggregate_preorder_limit():
    _, _, _, _, receipt, _ = fixture(
        economics={
            "Fulfillment": "PREORDER", "Economic Status": "QUOTED",
            "Public Stock Qty": "0", "MOQ": "20", "Order Multiple": "1",
            "Preorder Purchase Qty": "20",
            "Preorder Part Subtotal": "2", "Preorder Fees": "0"},
        limits={"line_cash": "3", "total_cash": "1",
                "line_surplus": "3", "total_surplus": "3"})
    eq(receipt["economics_verdict"], "REJECTED", "aggregate cash verdict")
    check(any("aggregate preorder_cash_outlay" in row["detail"]
              for row in receipt["findings"]), "aggregate finding absent")


@test("assembly minimum excess is costed separately", kind="known_bad")
def t_assembly_excess_cost():
    _, _, _, _, receipt, _ = fixture(
        economics={
            "Economic Status": "QUOTED", "MOQ": "1195",
            "Assembly Charged Qty": "1195",
            "Assembly Part Subtotal": "1.195"},
        limits={"assembly_excess": "1"})
    eq(receipt["economics_verdict"], "REJECTED", "assembly excess verdict")
    row = next(row for row in receipt["rows"]
               if row["requested_lcsc"] == "C100")
    eq(row["economics"]["assembly_excess_cost"], "1.185000",
       "nonrecoverable assembly excess cost")


@test("unknown minimum-cost economics is incomplete", kind="known_bad")
def t_unknown_economics():
    _, _, _, _, receipt, _ = fixture(
        economics={"Economic Status": "UNKNOWN"})
    eq(receipt["economics_verdict"], "INCOMPLETE", "unknown cost verdict")


@test("historical schema-v1 availability receipt remains reproducible")
def t_v1_backward_compatibility():
    root = tmpdir("pcba_v1_")
    bom = root / "bom.csv"
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n10k,R1,R_0402,C100\n",
        encoding="utf-8")
    request = {
        "schema": 1, "kind": pcba.REQUEST_KIND_V1, "phase": "prelayout",
        "authority_required": "jlcpcb_pcba_interface",
        "required_status": "AVAILABLE", "generated_at": NOW.isoformat(),
        "build_quantity": 5, "subject": pcba._record(bom),
        "subject_role": "bom", "assembly": None, "excluded_refs": [],
        "coverage": {"graded": 1, "total": 1},
        "rows": [{"requested_lcsc": "C100", "designators": ["R1"],
                  "per_board_qty": 1, "required_qty": 5}],
    }
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    response = root / "response.csv"
    with response.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=pcba.RESPONSE_FIELDS_V1)
        writer.writeheader()
        writer.writerow({"Requested LCSC": "C100", "Resolved LCSC": "C100",
                         "PCBA Status": "AVAILABLE", "Available Qty": "5",
                         "Checked At": "2026-08-18T11:00:00Z",
                         "Evidence": "historical uploader row"})
    receipt = pcba.grade(request_path, response, max_age_hours=24, now=NOW)
    receipt_path = root / "receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    valid, failures, _ = pcba.verify_receipt(receipt_path, bom=bom, now=NOW)
    check(valid and not failures, f"schema-v1 receipt regressed: {failures}")


@test("post-grade response mutation invalidates the receipt", kind="known_bad")
def t_response_mutation():
    _, bom, _, response, _, receipt_path = fixture()
    response.write_text(response.read_text() + "\n", encoding="utf-8")
    valid, failures, _ = pcba.verify_receipt(receipt_path, bom=bom, now=NOW)
    check(not valid and any("response evidence moved or changed" in item
                            for item in failures),
          f"mutated operator evidence was accepted: {failures}")


@test("embedded financial limits cannot disagree with saved policy",
      kind="known_bad")
def t_embedded_policy_tamper():
    root, _, request, response, _, _ = fixture()
    request["procurement_policy_value"]["limits"][
        "max_total_preorder_cash"] = "999999.000000"
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    rejected = False
    try:
        pcba.grade(request_path, response, max_age_hours=24, now=NOW)
    except ValueError as exc:
        rejected = "embedded procurement policy disagrees" in str(exc)
    check(rejected, "forged embedded financial limits were accepted")


@test("hand-edited receipt verdict cannot override saved JLC evidence",
      kind="known_bad")
def t_receipt_tamper():
    _, bom, _, _, receipt, receipt_path = fixture(
        phase="order", status="UNAVAILABLE")
    receipt["verdict"] = "ACCEPTED"
    for row in receipt["rows"]:
        row["status"] = "PASS"
        row["detail"] = "forged"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    valid, failures, _ = pcba.verify_receipt(
        receipt_path, bom=bom, required_phase="order", now=NOW)
    check(not valid and any("does not reproduce" in item for item in failures),
          f"edited verdict was trusted: {failures}")


@test("receipt reopens from a self-contained relocated evidence bundle")
def t_relocated_bundle():
    root, bom, _, response, _, receipt_path = fixture()
    request = root / "request.json"
    bundle = root / "release_verification"
    bundle.mkdir()
    for source in (request, response, receipt_path):
        shutil.copy2(source, bundle / source.name)
    shutil.copy2(root / "procurement-policy.yaml",
                 bundle / "procurement-policy.yaml")
    request.unlink()
    response.unlink()
    valid, failures, _ = pcba.verify_receipt(
        bundle / "receipt.json", bom=bom, now=NOW)
    check(valid and not failures, f"relocated bundle refused: {failures}")


@test("release sourcing CLEAR comes from final JLC allocation, not catalog")
def t_release_clear_authority():
    root, bom, _, _, _, receipt_path = fixture(phase="order", status="ALLOCATED")
    release = root / "release"
    (release / "fab").mkdir(parents=True)
    (release / "fab/bom.csv").write_bytes(bom.read_bytes())
    failures, _, state = freshness.check_pcba_availability(release, receipt_path)
    check(not failures, f"clean final allocation was refused: {failures}")
    eq(state["status"], "CLEAR", "authoritative sourcing state")


@test("valid unavailable JLC receipt produces measured BLOCKED-SOURCING",
      kind="known_bad")
def t_release_blocked_authority():
    root, bom, _, _, _, receipt_path = fixture(
        phase="order", status="UNAVAILABLE")
    release = root / "release"
    (release / "fab").mkdir(parents=True)
    (release / "fab/bom.csv").write_bytes(bom.read_bytes())
    failures, _, state = freshness.check_pcba_availability(release, receipt_path)
    check(not failures, f"valid blocked measurement became malformed: {failures}")
    eq(state["status"], "BLOCKED", "blocked sourcing state")
    eq(state["blocked"], ["C100"], "blocked exact code")


@test("aggregate MOQ-cost rejection cannot report sourcing CLEAR",
      kind="known_bad")
def t_release_aggregate_cost_blocked():
    root, bom, _, _, _, receipt_path = fixture(
        phase="order", status="ALLOCATED",
        economics={
            "Fulfillment": "PREORDER", "Economic Status": "QUOTED",
            "Public Stock Qty": "0", "MOQ": "20", "Order Multiple": "1",
            "Preorder Purchase Qty": "20",
            "Preorder Part Subtotal": "2", "Preorder Fees": "0"},
        limits={"line_cash": "3", "total_cash": "1",
                "line_surplus": "3", "total_surplus": "3"})
    release = root / "release"
    (release / "fab").mkdir(parents=True)
    (release / "fab/bom.csv").write_bytes(bom.read_bytes())
    failures, _, state = freshness.check_pcba_availability(release, receipt_path)
    check(not failures, f"valid aggregate rejection became malformed: {failures}")
    eq(state["status"], "BLOCKED", "aggregate procurement state")
    check("PROCUREMENT_AGGREGATE" in state["blocked"],
          "aggregate cost blocker missing")


@test("missing final JLC receipt is UNGRADED, never CLEAR", kind="known_bad")
def t_release_missing_authority():
    root = tmpdir("pcba_missing_")
    (root / "fab").mkdir()
    (root / "fab/bom.csv").write_text(
        "Comment,Designator,Footprint,LCSC\n10k,R1,R_0402,C100\n")
    failures, _, state = freshness.check_pcba_availability(root, None)
    check(failures, "missing receipt emitted no finding")
    eq(state["status"], "UNGRADED", "missing sourcing authority")


@test("new manifest opts into JLC authority without retro-changing history")
def t_manifest_authority_migration():
    root = tmpdir("pcba_authority_")
    release = root / "07_releases/v1.0-2026-08-18"
    release.mkdir(parents=True)
    eq(freshness._contract_sourcing_authority(release), "catalog-legacy",
       "unmarked historical release")
    (release / "MANIFEST.txt").write_text(
        "sourcing_authority: jlc-pcba\n", encoding="utf-8")
    eq(freshness._contract_sourcing_authority(release), "jlc-pcba",
       "new release authority")


@test("prepare refuses to overwrite an in-progress operator response",
      kind="known_bad")
def t_non_overwriting_pause():
    root = tmpdir("pcba_no_overwrite_")
    bom = root / "bom.csv"
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n10k,R1,R_0402,C100\n",
        encoding="utf-8")
    request = root / "request.json"
    response = root / "response.csv"
    policy = policy_file(root)
    response.write_text("operator work in progress\n", encoding="utf-8")
    rc = pcba.main(["prepare", str(bom), "--build-quantity", "5",
                    "--phase", "prelayout", "--out", str(request),
                    "--procurement-policy", str(policy),
                    "--response-template", str(response)])
    eq(rc, 2, "non-overwriting prepare exit")
    eq(response.read_text(), "operator work in progress\n",
       "operator response bytes")
    check(not request.exists(), "partial request was written before refusal")


@test("manufacturing readiness accepts the exact prelayout receipt")
def t_manufacturing_composes_prelayout():
    _, _, _, _, _, receipt_path = fixture()
    result = manufacturing_readiness._pcba_check(
        receipt_path, phase="prelayout")
    eq(result["status"], "PASS", "composed prelayout receipt")


@test("manufacturing readiness refuses missing operator evidence",
      kind="known_bad")
def t_manufacturing_missing_prelayout():
    result = manufacturing_readiness._pcba_check(None, phase="prelayout")
    eq(result["status"], "INCOMPLETE", "missing operator receipt")
    check("catalog stock is not" in result["output"],
          "authority distinction missing")


if __name__ == "__main__":
    raise SystemExit(main())
