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


class FakePad:
    def __init__(self, number, net):
        self.number, self.net = number, net
    def GetNumber(self):
        return self.number
    def GetNetname(self):
        return self.net


class FakeFootprint:
    def __init__(self, ref, pads):
        self.ref, self.pads = ref, [FakePad(*row) for row in pads]
    def GetReference(self):
        return self.ref
    def Pads(self):
        return self.pads


class FakeBoard:
    def __init__(self, footprints):
        self.footprints = footprints
    def GetFootprints(self):
        return self.footprints


@test("connector lane contract checks ordered physical pad-to-net identity")
def t_connector_lane_clean():
    board = FakeBoard([FakeFootprint("J1", [("A6", "USB_P"),
                                             ("A7", "USB_N")])])
    cfg = {"route": {"routability": {"require_connector_lanes": True,
        "connector_lanes": [{"ref": "J1", "why": "USB lane order",
            "lanes": [{"pad": "A6", "net": "USB_P"},
                      {"pad": "A7", "net": "USB_N"}]}]}}}
    eq(placement_routability_preflight._connector_lanes(cfg, board)["status"],
       "PASS", "connector lane order")


@test("connector lane contract rejects a swapped USB pair", kind="known_bad")
def t_connector_lane_swapped():
    board = FakeBoard([FakeFootprint("J1", [("A6", "USB_N"),
                                             ("A7", "USB_P")])])
    cfg = {"route": {"routability": {"connector_lanes": [{
        "ref": "J1", "why": "USB lane order",
        "lanes": [{"pad": "A6", "net": "USB_P"},
                  {"pad": "A7", "net": "USB_N"}]}]}}}
    report = placement_routability_preflight._connector_lanes(cfg, board)
    eq(report["status"], "FAIL", "swapped lane status")
    check(len(report["findings"]) == 2, "swapped pair was not diagnosed")


@test("series power path proves copper joins and component crossings")
def t_series_power_path_clean():
    board = FakeBoard([
        FakeFootprint("J1", [("1", "VIN")]),
        FakeFootprint("F1", [("1", "VIN"), ("2", "FUSED")]),
        FakeFootprint("U1", [("1", "FUSED")]),
    ])
    cfg = {"route": {"routability": {"series_power_paths": [{
        "id": "input", "why": "fuse cannot be bypassed",
        "transitions": [
            {"kind": "copper", "from": "J1.1", "to": "F1.1"},
            {"kind": "component", "from": "F1.1", "to": "F1.2"},
            {"kind": "copper", "from": "F1.2", "to": "U1.1"},
        ]}]}}}
    eq(placement_routability_preflight._series_power_paths(cfg, board)["status"],
       "PASS", "series power path")


@test("series power path rejects a fuse bypass", kind="known_bad")
def t_series_power_path_bypass():
    board = FakeBoard([
        FakeFootprint("J1", [("1", "VIN")]),
        FakeFootprint("F1", [("1", "VIN"), ("2", "FUSED")]),
        FakeFootprint("U1", [("1", "VIN")]),
    ])
    cfg = {"route": {"routability": {"series_power_paths": [{
        "id": "input", "why": "fuse cannot be bypassed",
        "transitions": [{"kind": "copper", "from": "F1.2", "to": "U1.1"}]
    }]}}}
    report = placement_routability_preflight._series_power_paths(cfg, board)
    eq(report["status"], "FAIL", "bypassed path status")
    check(report["findings"], "bypass emitted no diagnosis")


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
        path.parent, path, ["USB_P"], {})
    eq(report["status"], "PASS", "chain topology")


@test("final-route acceptance rejects a branch on a critical conductor",
      kind="known_bad")
def t_route_branch_bad():
    path = tmpdir("route_branch_") / "branch.kicad_pcb"
    copper(path, True)
    report = route_acceptance_gate._simple_conductor(
        path.parent, path, ["USB_P"], {})
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
        "mpn": "EXACT-IC", "footprint": "Package_SO:SOIC-8",
        "sourcing": {"lcsc": "C123"}},
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


@test("automatic exact part freeze rejects a dossier with no footprint",
      kind="known_bad")
def t_manufacturing_missing_footprint():
    project, circuit, assembly = manufacturing_tree(["C123"])
    dossier = project / "02_parts/EXACT-IC/part.yaml"
    data = yaml.safe_load(dossier.read_text())
    data["footprint"] = None
    dossier.write_text(yaml.safe_dump(data, sort_keys=False))
    report, _ = manufacturing_readiness.exact_code_check(
        project, circuit, assembly)
    eq(report["status"], "FAIL", "missing-footprint readiness")
    check(any("no frozen footprint" in item for item in report["findings"]),
          "missing footprint diagnosis absent")


@test("accepted prelayout readiness can shadow-publish S-PART-FREEZE")
def t_part_freeze_stage_evidence():
    project, circuit, assembly = manufacturing_tree(["C123"])
    receipt = project / "readiness.json"
    result = {
        "schema": 1,
        "kind": "manufacturing-readiness-receipt-v1",
        "phase": "prelayout",
        "verdict": "ACCEPTED",
        "project": project.name,
        "inputs": {"circuit": record(circuit), "assembly": record(assembly)},
        "checks": {
            "exact_code_identity": {
                "status": "PASS", "detail": "1/1", "rows": [{
                    "ref": "U1", "mpn": "EXACT-IC", "jlc_codes": ["C123"],
                    "disposition": "jlc",
                }],
            },
            "procurement_exposure": {"status": "PASS", "detail": "bounded"},
        },
        "coverage": {"passing": 2, "total": 2},
    }
    receipt.write_text(json.dumps(result))
    (project / "bundle-parent").mkdir()
    manufacturing_readiness._publish_part_freeze(
        result, receipt, project / "bundle-parent/accepted",
        project / "part-freeze.stage.json")
    stage = json.loads((project / "part-freeze.stage.json").read_text())
    eq(stage["stage_id"], "S-PART-FREEZE", "part-freeze stage id")
    eq(stage["outputs"], ["part_freeze_report"], "part-freeze symbol")


@test("accepted placement receipt can shadow-publish P-FEASIBILITY")
def t_placement_feasibility_stage_evidence():
    project = tmpdir("placement_feasibility_")
    board = project / "board.kicad_pcb"
    route = project / "route.yaml"
    board.write_text("(kicad_pcb)\n")
    route.write_text("route: {}\n")
    receipt_path = project / "placement.json"
    receipt = {
        "schema": 1, "kind": "placement-routability-receipt-v1",
        "verdict": "ACCEPTED", "subject": record(board),
        "inputs": {"board": record(board), "route": record(route)},
        "checks": {
            "endpoint_topology": {"status": "PASS", "detail": "1/1",
                                  "rows": []},
            "layer_eligibility": {"status": "PASS", "detail": "2 layers"},
        },
        "coverage": {"passing": 2, "total": 2},
    }
    receipt_path.write_text(json.dumps(receipt))
    (project / "bundle-parent").mkdir()
    placement_routability_preflight._publish_feasibility(
        receipt, receipt_path, project / "bundle-parent/accepted",
        project / "feasibility.stage.json")
    stage = json.loads((project / "feasibility.stage.json").read_text())
    eq(stage["stage_id"], "P-FEASIBILITY", "feasibility stage id")
    eq(stage["outputs"], ["placement_feasibility_report"],
       "feasibility symbol")


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
