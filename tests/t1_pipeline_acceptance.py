#!/usr/bin/env python3
"""Focused regressions for placement, route, manufacturing and seal receipts."""
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, eq, main, must_fail, run, test,
                     tmpdir)  # noqa: E402

KICAD = ROOT / "skills" / "kicad-pcb" / "scripts"
FAB = ROOT / "skills" / "jlcpcb-fab" / "scripts"
PCB = ROOT / "skills" / "pcb-design" / "scripts"
for directory in (KICAD, FAB, PCB):
    sys.path.insert(0, str(directory))

import manufacturing_readiness  # noqa: E402
import placement_routability_preflight  # noqa: E402
import realized_via_aspect_check  # noqa: E402
import release_rehearsal  # noqa: E402
import route_acceptance_gate  # noqa: E402


def record(path):
    data = path.read_bytes()
    return {"path": str(path.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


@test("realized-via census accepts a tier-compliant exact drill")
def t_via_aspect_clean():
    report = realized_via_aspect_check.grade_rows(
        [{"diameter_mm": 0.45, "drill_mm": 0.20}], 1.6, 10.0)
    eq(report["verdict"], "PASS", "via verdict")
    eq(report["coverage"], {"graded": 1, "total": 1}, "via denominator")


@test("realized-via census rejects a saved-board drill above tier aspect",
      kind="known_bad")
def t_via_aspect_bad():
    report = realized_via_aspect_check.grade_rows(
        [{"diameter_mm": 0.41, "drill_mm": 0.15}], 1.6, 10.0)
    eq(report["verdict"], "FAIL", "via verdict")
    check(report["failures"][0]["aspect_ratio"] > 10.0,
          "known-bad via did not exceed the configured tier")
    project = tmpdir("via_aspect_cli_")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "03_src/rules/nets.yaml").write_text(
        "fab_tier: jlc_4layer_advanced\n")
    board_path = project / "bad.kicad_pcb"
    board = realized_via_aspect_check.pcbnew.BOARD()
    board.GetDesignSettings().SetBoardThickness(
        realized_via_aspect_check.pcbnew.FromMM(1.6))
    via = realized_via_aspect_check.pcbnew.PCB_VIA(board)
    via.SetWidth(realized_via_aspect_check.pcbnew.FromMM(0.41))
    via.SetDrill(realized_via_aspect_check.pcbnew.FromMM(0.15))
    board.Add(via)
    realized_via_aspect_check.pcbnew.SaveBoard(str(board_path), board)
    must_fail(run([KPY, KICAD / "realized_via_aspect_check.py",
                   board_path, "--project", project]),
              "over-aspect realized-via CLI", expect="R-VIA-ASPECT FAIL")


@test("placement routability can explicitly opt out of topology declarations")
def t_topology_na():
    report = placement_routability_preflight._topology(
        {"route": {"routability": {}}}, None, Path("."))
    eq(report["status"], "N-A", "topology applicability")


@test("required placement topology cannot pass on an empty denominator",
      kind="known_bad")
def t_topology_empty_refused():
    report = placement_routability_preflight._topology(
        {"route": {"routability": {"require_topology": True}}},
        None, Path("."))
    eq(report["status"], "FAIL", "empty required topology")
    check(report["findings"], "empty required topology emitted no diagnosis")


def copper(path, branched):
    tail = ('\t(segment (start 1 0) (end 1 1) (layer "F.Cu") '
            '(net "USB_P"))\n') if branched else ""
    path.write_text(
        '(kicad_pcb\n\t(layers (0 "F.Cu" signal) (31 "B.Cu" signal))\n'
        '\t(segment (start 0 0) (end 1 0) (layer "F.Cu") '
        '(net "USB_P"))\n'
        '\t(segment (start 1 0) (end 2 0) (layer "F.Cu") '
        '(net "USB_P"))\n' + tail + ')\n')


@test("final-route simple-conductor check accepts a chain")
def t_route_chain_clean():
    path = tmpdir("route_chain_") / "chain.kicad_pcb"
    copper(path, False)
    report = route_acceptance_gate._simple_conductor(
        path.parent, path, ["USB_P"])
    eq(report["status"], "PASS", "chain topology")


@test("final-route acceptance rejects a branch on a critical conductor",
      kind="known_bad")
def t_route_branch_bad():
    path = tmpdir("route_branch_") / "branch.kicad_pcb"
    copper(path, True)
    report = route_acceptance_gate._simple_conductor(
        path.parent, path, ["USB_P"])
    eq(report["status"], "FAIL", "branched topology")
    check(report["failures"], "branched conductor emitted no finding")


def manufacturing_tree(codes):
    project = tmpdir("manufacturing_ready_")
    circuit = project / "03_tscircuit/build/circuit.json"
    circuit.parent.mkdir(parents=True)
    circuit.write_text(json.dumps([{
        "type": "source_component", "name": "U1",
        "manufacturer_part_number": "EXACT-IC",
        "supplier_part_numbers": {"jlcpcb": codes},
    }]))
    assembly = project / "03_src/rules/assembly.yaml"
    assembly.parent.mkdir(parents=True)
    assembly.write_text("not_assembled: []\n")
    dossier = project / "02_parts/EXACT-IC/part.yaml"
    dossier.parent.mkdir(parents=True)
    dossier.write_text(yaml.safe_dump({
        "mpn": "EXACT-IC", "sourcing": {"lcsc": "C123"}},
        sort_keys=False))
    return project, circuit, assembly


@test("selection readiness accepts one exact code and one exact dossier")
def t_manufacturing_exact_clean():
    project, circuit, assembly = manufacturing_tree(["C123"])
    report, dossiers = manufacturing_readiness.exact_code_check(
        project, circuit, assembly)
    eq(report["status"], "PASS", "exact-code readiness")
    eq(report["coverage"], {"graded": 1, "total": 1}, "code denominator")
    eq(len(dossiers), 1, "used dossier count")


@test("selection readiness rejects ambiguous supplier-code identity",
      kind="known_bad")
def t_manufacturing_multiple_codes_bad():
    project, circuit, assembly = manufacturing_tree(["C123", "C456"])
    report, _ = manufacturing_readiness.exact_code_check(
        project, circuit, assembly)
    eq(report["status"], "FAIL", "ambiguous supplier identity")
    check(any("multiple JLC codes" in item for item in report["findings"]),
          "ambiguous code diagnosis absent")
    must_fail(run([KPY, FAB / "manufacturing_readiness.py", "grade",
                   project, "--phase", "selection", "--json",
                   project / "receipt.json"]),
              "ambiguous manufacturing selection CLI", expect="REJECTED")


def rehearsal_tree():
    release = tmpdir("release_rehearsal_") / "v1.0-2026-08-17"
    release.mkdir()
    artifact = release / "MANIFEST.txt"
    artifact.write_text("DRAFT fixture\n")
    receipt = release.parent / "receipt.json"
    receipt.write_text(json.dumps({
        "schema": 1, "kind": "release-rehearsal-receipt-v1",
        "verdict": "ACCEPTED", "release": str(release),
        "inputs": {"MANIFEST.txt": record(artifact)},
        "checks": {"fixture": {"status": "PASS"}},
    }))
    return release, artifact, receipt


@test("release rehearsal receipt reopens unchanged staged bytes")
def t_rehearsal_clean():
    _, _, receipt = rehearsal_tree()
    valid, failures = release_rehearsal.verify(receipt)
    check(valid and not failures, f"clean rehearsal refused: {failures}")


@test("release rehearsal goes stale when staged bytes move", kind="known_bad")
def t_rehearsal_stale():
    _, artifact, receipt = rehearsal_tree()
    artifact.write_text("mutated after review\n")
    valid, failures = release_rehearsal.verify(receipt)
    check(not valid and any("moved or changed" in row for row in failures),
          f"stale rehearsal was not rejected: {failures}")
    must_fail(run([KPY, PCB / "release_rehearsal.py", "verify", receipt]),
              "stale release-rehearsal CLI", expect="RECEIPT FAIL")


@test("accepted blocked-sourcing receipts retain a failing informational check")
def t_rehearsal_blocked_sourcing_receipt():
    release, artifact, receipt = rehearsal_tree()
    receipt.write_text(json.dumps({
        "schema": 1, "kind": "release-rehearsal-receipt-v1",
        "verdict": "ACCEPTED", "release": str(release),
        "inputs": {"MANIFEST.txt": record(artifact)},
        "checks": {
            "design": {"status": "PASS", "required_for_seal": True},
            "sourcing": {"status": "FAIL", "required_for_seal": False},
        },
    }))
    valid, failures = release_rehearsal.verify(receipt)
    check(valid and not failures,
          f"declared informational sourcing block refused: {failures}")


if __name__ == "__main__":
    raise SystemExit(main())
