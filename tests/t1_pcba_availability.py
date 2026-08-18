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


def fixture(*, phase="prelayout", status="AVAILABLE", resolved="C100",
            available="20", checked="2026-08-18T11:00:00Z"):
    root = tmpdir("pcba_")
    bom = root / "bom.csv"
    bom.write_text(
        "Comment,Designator,Footprint,LCSC\n"
        "10k,R1,R_0402,C100\n"
        "10k,R2,R_0402,C100\n"
        "1uF,C1,C_0402,C200\n", encoding="utf-8")
    request = pcba.prepare(bom, build_quantity=5, phase=phase,
                           generated_at=NOW)
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    response = root / "response.csv"
    with response.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=pcba.RESPONSE_FIELDS)
        writer.writeheader()
        writer.writerow({"Requested LCSC": "C100", "Resolved LCSC": resolved,
                         "PCBA Status": status, "Available Qty": available,
                         "Checked At": checked, "Evidence": "JLC upload row 1"})
        writer.writerow({"Requested LCSC": "C200", "Resolved LCSC": "C200",
                         "PCBA Status": ("ALLOCATED" if phase == "order" else
                                         "AVAILABLE"),
                         "Available Qty": "10", "Checked At": checked,
                         "Evidence": "JLC upload row 2"})
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
    request = pcba.prepare(circuit, build_quantity=3, phase="prelayout",
                           assembly=assembly, generated_at=NOW)
    eq([row["requested_lcsc"] for row in request["rows"]], ["C100"],
       "PCBA population set")
    eq(request["excluded_refs"], ["F1"], "manual exclusion")


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


@test("post-grade response mutation invalidates the receipt", kind="known_bad")
def t_response_mutation():
    _, bom, _, response, _, receipt_path = fixture()
    response.write_text(response.read_text() + "\n", encoding="utf-8")
    valid, failures, _ = pcba.verify_receipt(receipt_path, bom=bom, now=NOW)
    check(not valid and any("response evidence moved or changed" in item
                            for item in failures),
          f"mutated operator evidence was accepted: {failures}")


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
    response.write_text("operator work in progress\n", encoding="utf-8")
    rc = pcba.main(["prepare", str(bom), "--build-quantity", "5",
                    "--phase", "prelayout", "--out", str(request),
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
