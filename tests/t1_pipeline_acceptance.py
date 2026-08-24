#!/usr/bin/env python3
"""Focused regressions for placement, route, manufacturing and seal receipts."""
import hashlib
import json
import sys
from pathlib import Path
from unittest import mock

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


@test("source-prep authority compiles from board-observed facts in shadow")
def t_source_prep_authority_shadow():
    root = tmpdir("source_authority_")
    stack = root / "stackup.yaml"
    plan = root / "route_plan.yaml"
    circuit = root / "circuit.json"
    stack.write_text(yaml.safe_dump({
        "schema": "stackup-v1",
        "copper": [
            {"name": "F.Cu", "thickness_um": 35, "role": "signal"},
            {"name": "B.Cu", "thickness_um": 35, "role": "signal"},
        ],
        "routing_classes": {
            "signal": {"allowed_layers": ["F.Cu", "B.Cu"]},
        },
    }, sort_keys=False))
    plan.write_text(yaml.safe_dump({
        "schema": "route-plan-v1",
        "groups": {"all": "rest"},
        "waves": [{"name": "all", "group": "all",
                   "routing_class": "signal"}],
        "exclusions": [], "deterministic_owners": [],
    }, sort_keys=False))
    circuit.write_text(json.dumps([{
        "type": "source_component", "name": "U1",
        "manufacturer_part_number": "EXACT-IC",
    }]))
    board = FakeBoard([FakeFootprint("U1", [("1", "SIG")])])
    report = placement_routability_preflight._source_authority_shadow(
        stack, plan, None, board, circuit)
    eq(report["status"], "PASS", "source authority shadow status")
    eq(report["authority"], "SHADOW", "source authority rollout")
    eq(report["report"]["live"]["mpns"], ["EXACT-IC"],
       "independent exact MPN observation")


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


@test("route acceptance reports PASS and N-A as separate denominators")
def t_route_acceptance_optional_na():
    checks = {
        "native_drc": {"status": "PASS"},
        "route_base": {"status": "N-A"},
    }
    verdict, coverage, required_not_pass = route_acceptance_gate._admission(
        checks, ["native_drc"])
    eq(verdict, "ACCEPTED", "optional N-A admission")
    eq(coverage["pass"], 1, "executed pass count")
    eq(coverage["non_applicable"], 1, "N-A count")
    eq(coverage["passing"], 1, "legacy passing key excludes N-A")
    eq(required_not_pass, [], "required closure")


@test("shadow route admission cannot tighten legacy acceptance")
def t_route_acceptance_shadow_is_observational():
    original = route_acceptance_gate.route_acceptance_core.admit
    route_acceptance_gate.route_acceptance_core.admit = lambda *_args, **_kwargs: {
        "verdict": "INCOMPLETE", "required_not_pass": ["invented_shadow_gap"]}
    try:
        verdict, coverage, required_not_pass = route_acceptance_gate._admission(
            {"native_drc": {"status": "PASS"}}, ["native_drc"])
    finally:
        route_acceptance_gate.route_acceptance_core.admit = original
    eq(verdict, "ACCEPTED", "legacy admission remains authoritative")
    eq(coverage["required_pass"], 1, "legacy required denominator")
    eq(required_not_pass, [], "shadow findings stay outside authority")


@test("route shadow failure becomes diagnostic INCOMPLETE")
def t_route_acceptance_shadow_exception_is_contained():
    original = route_acceptance_gate.route_acceptance_core.admit
    route_acceptance_gate.route_acceptance_core.admit = lambda *_args, **_kwargs: (
        (_ for _ in ()).throw(RuntimeError("shadow exploded")))
    try:
        shadow = route_acceptance_gate._shadow_admission(
            {"native_drc": {"status": "PASS"}}, ["native_drc"], "full")
    finally:
        route_acceptance_gate.route_acceptance_core.admit = original
    eq(shadow["authority"], "SHADOW", "shadow authority label")
    eq(shadow["status"], "INCOMPLETE", "shadow exception status")
    check("shadow exploded" in shadow["detail"], "shadow failure detail")


@test("route CLI records a pending shadow without executing shared policy")
def t_route_cli_shadow_is_pending_only():
    project = tmpdir("route_pending_shadow_")
    (project / "03_src/rules").mkdir(parents=True)
    route = project / "03_src/route.yaml"
    nets = project / "03_src/rules/nets.yaml"
    board = project / "board.kicad_pcb"
    route.write_text("route: {}\n")
    nets.write_text("schema: 1\n")
    board.write_text("board")
    output = project / "route.json"
    receipt = {
        "schema": 1, "kind": "route-acceptance-receipt-v1",
        "mode": "quick", "verdict": "ACCEPTED", "subject": record(board),
        "inputs": {"board": record(board), "route": record(route),
                   "nets": record(nets)},
        "checks": {}, "required_checks": [], "required_not_pass": [],
        "coverage": {"pass": 0, "non_applicable": 0, "fail": 0,
                     "incomplete": 0, "required": 0,
                     "required_pass": 0, "total": 0, "passing": 0},
    }
    with mock.patch("route_acceptance_gate.grade", return_value=receipt), \
         mock.patch("route_acceptance_gate.verify", return_value=(True, [])), \
         mock.patch("route_acceptance_gate.route_acceptance_core.admit",
                    side_effect=AssertionError("shadow policy executed")):
        rc = route_acceptance_gate.main([
            "grade", str(project), "--board", str(board), "--mode", "quick",
            "--json", str(output),
        ])
    eq(rc, 0)
    shadow = json.loads((project / "route.shadow.json").read_text())
    eq(shadow["status"], "INCOMPLETE")
    check("separate bounded task" in shadow["requested"]["detail"],
          "pending route shadow overclaimed execution")


@test("route CLI never publishes a receipt that fails its fresh reopen",
      kind="known_bad")
def t_route_cli_failed_reopen_is_not_canonical():
    project = tmpdir("route_failed_reopen_")
    (project / "03_src/rules").mkdir(parents=True)
    route = project / "03_src/route.yaml"
    nets = project / "03_src/rules/nets.yaml"
    board = project / "board.kicad_pcb"
    route.write_text("route: {}\n")
    nets.write_text("schema: 1\n")
    board.write_text("board")
    output = project / "route.json"
    receipt = {
        "schema": 1, "kind": "route-acceptance-receipt-v1",
        "mode": "quick", "verdict": "ACCEPTED", "subject": record(board),
        "inputs": {"board": record(board), "route": record(route),
                   "nets": record(nets)},
        "checks": {}, "required_checks": [], "required_not_pass": [],
        "coverage": {"pass": 0, "non_applicable": 0, "fail": 0,
                     "incomplete": 0, "required": 0,
                     "required_pass": 0, "total": 0, "passing": 0},
    }
    with mock.patch("route_acceptance_gate.grade", return_value=receipt), \
         mock.patch("route_acceptance_gate.verify",
                    return_value=(False, ["forged row"])):
        rc = route_acceptance_gate.main([
            "grade", str(project), "--board", str(board), "--mode", "quick",
            "--json", str(output),
        ])
    eq(rc, 2, "failed receipt reopen did not stop the route gate")
    check(not output.exists(), "unverified ACCEPTED receipt became canonical")
    check(not (project / "route.shadow.json").exists(),
          "shadow request was emitted for an unverified receipt")
    check(not list(project.glob(".route.json.verify-*")),
          "failed provisional receipt was retained as authority-like evidence")


@test("required route check cannot become accepted N-A", kind="known_bad")
def t_route_acceptance_required_na():
    checks = {
        "critical_copper_length": {"status": "N-A"},
        "native_drc": {"status": "PASS"},
    }
    verdict, coverage, required_not_pass = route_acceptance_gate._admission(
        checks, ["critical_copper_length", "native_drc"])
    eq(verdict, "INCOMPLETE", "required N-A admission")
    eq(coverage["required_pass"], 1, "required-pass denominator")
    eq(required_not_pass, ["critical_copper_length"],
       "required N-A diagnosis")


@test("full high-speed route derives length and plane as required")
def t_route_acceptance_high_speed_required():
    cfg = {"route": {"preflight_critical_pairs": [
        {"p": "USB_P", "n": "USB_N"}]}}
    required = route_acceptance_gate._required_checks(
        "full", ["USB_N", "USB_P"], cfg, None)
    check("critical_copper_length" in required,
          "high-speed length was not required")
    check("reference_plane" in required,
          "high-speed reference plane was not required")
    check("route_base" not in required,
          "absent optional inheritance subject became required")


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


@test("accepted prelayout readiness emits only an incomplete S-PART request")
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
    eq(stage["status"], "INCOMPLETE", "part-freeze promotion status")
    eq(stage["outputs"], [], "part-freeze request has no accepted symbol")
    check(not (project / "bundle-parent/accepted").exists(),
          "part-freeze request replaced an accepted bundle")


@test("structural placement receipt cannot publish accepted P-FEASIBILITY")
def t_placement_feasibility_stage_evidence():
    project = tmpdir("placement_feasibility_")
    board = project / "board.kicad_pcb"
    route = project / "route.yaml"
    nets = project / "nets.yaml"
    board.write_text("(kicad_pcb)\n")
    route.write_text("route: {}\n")
    nets.write_text("schema: 1\n")
    receipt_path = project / "placement.json"
    checks = {
        name: {"status": "PASS", "detail": "fixture pass"}
        for name in placement_routability_preflight.AUTHORITATIVE_CHECKS
    }
    checks["endpoint_topology"]["rows"] = []
    receipt = {
        "schema": 1, "kind": "placement-routability-receipt-v1",
        "verdict": "ACCEPTED", "subject": record(board),
        "inputs": {"board": record(board), "route": record(route),
                   "nets": record(nets)},
        "checks": checks,
        "coverage": {"passing": len(checks), "total": len(checks)},
        "shadow_checks": {
            "functional_cells": {"status": "INCOMPLETE",
                                 "detail": "diagnostic only"}},
        "shadow_coverage": {"passing": 0, "total": 1},
    }
    receipt_path.write_text(json.dumps(receipt))
    (project / "bundle-parent").mkdir()
    stage_path = project / "feasibility.stage.json"
    stage_path.write_text('{"status":"PASS","outputs":["unsafe"]}\n')
    placement_routability_preflight._publish_feasibility(
        receipt, receipt_path, project / "bundle-parent/accepted",
        stage_path)
    stage = json.loads(stage_path.read_text())
    eq(stage["stage_id"], "P-FEASIBILITY", "feasibility stage id")
    eq(stage["status"], "INCOMPLETE", "structural receipt cannot pass")
    eq(stage["outputs"], [], "no accepted feasibility output")
    check(not (project / "bundle-parent/accepted").exists(),
          "structural receipt created an accepted bundle")
    first_subject = stage["subject"]

    # Changing only a shadow diagnostic must not churn the authoritative stage
    # identity or leak into the accepted measurement.
    receipt["shadow_checks"]["functional_cells"]["status"] = "PASS"
    receipt_path.write_text(json.dumps(receipt))
    (project / "bundle-parent-2").mkdir()
    placement_routability_preflight._publish_feasibility(
        receipt, receipt_path, project / "bundle-parent-2/accepted",
        project / "feasibility-2.stage.json")
    second = json.loads((project / "feasibility-2.stage.json").read_text())
    eq(second["subject"], first_subject, "shadow-isolated feasibility subject")
    eq(second["status"], "INCOMPLETE", "second shadow result remains blocked")
    check(not (project / "bundle-parent-2/accepted").exists(),
          "shadow-only change created an accepted bundle")


@test("placement rejects stage-result alias before grading", kind="known_bad")
def t_placement_output_alias_is_rejected():
    project = tmpdir("placement_alias_")
    board = project / "board.kicad_pcb"
    board.write_text("board sentinel")
    output = project / "placement.json"
    output.write_text("receipt sentinel")
    with mock.patch("placement_routability_preflight.grade") as grade:
        rc = placement_routability_preflight.main([
            "grade", str(project), "--board", str(board),
            "--json", str(output),
            "--stage-bundle", str(project / "bundle"),
            "--stage-result", str(output),
        ])
    eq(rc, 2, "placement output alias was accepted")
    grade.assert_not_called()
    eq(output.read_text(), "receipt sentinel", "placement receipt overwritten")


@test("route rejects native DRC alias before grading", kind="known_bad")
def t_route_output_alias_is_rejected():
    project = tmpdir("route_alias_")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "03_src/route.yaml").write_text("route: {}\n")
    (project / "03_src/rules/nets.yaml").write_text("schema: 1\n")
    board = project / "board.kicad_pcb"
    board.write_text("board sentinel")
    output = project / "route.json"
    output.write_text("receipt sentinel")
    with mock.patch("route_acceptance_gate.grade") as grade:
        rc = route_acceptance_gate.main([
            "grade", str(project), "--board", str(board), "--mode", "full",
            "--drc-json", str(output), "--json", str(output),
        ])
    eq(rc, 2, "route output alias was accepted")
    grade.assert_not_called()
    eq(output.read_text(), "receipt sentinel", "route receipt overwritten")


@test("route rejects native DRC hardlink to its board", kind="known_bad")
def t_route_output_hardlink_is_rejected():
    project = tmpdir("route_hardlink_")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "03_src/route.yaml").write_text("route: {}\n")
    (project / "03_src/rules/nets.yaml").write_text("schema: 1\n")
    board = project / "board.kicad_pcb"
    board.write_text("board sentinel")
    drc = project / "drc.json"
    drc.hardlink_to(board)
    output = project / "route.json"
    with mock.patch("route_acceptance_gate.grade") as grade:
        rc = route_acceptance_gate.main([
            "grade", str(project), "--board", str(board), "--mode", "full",
            "--drc-json", str(drc), "--json", str(output),
        ])
    eq(rc, 2, "hardlinked DRC output was accepted")
    grade.assert_not_called()
    eq(board.read_text(), "board sentinel", "hardlink truncated live board")
    check(not output.exists(), "receipt was written after hardlink rejection")


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


@test("release rehearsal init states its own blocked-sourcing admission token")
def t_rehearsal_init_declares_blocked_sourcing():
    root = tmpdir("release_rehearsal_init_")
    project = root / "project"
    release = project / "06_build/release_staging/v1.0-2026-08-17"
    (release / "source").mkdir(parents=True)
    (release / "source/fixture.kicad_pcb").write_text("(kicad_pcb)\n")
    (release / "ORDER_README.md").write_text(
        "BLOCKED-SOURCING: order-phase allocation absent.\n")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "04_kicad").mkdir()
    (project / "03_src/rules/assembly.yaml").write_text(
        "service: fixture\nnot_assembled: []\n")
    prior_repo, prior_git = release_rehearsal.REPO, release_rehearsal._git
    try:
        release_rehearsal.REPO = root
        release_rehearsal._git = lambda *args: (
            "0123456789abcdef" if args == ("rev-parse", "HEAD") else "")
        manifest = release_rehearsal.init_manifest(release, project)
    finally:
        release_rehearsal.REPO = prior_repo
        release_rehearsal._git = prior_git
    text = manifest.read_text()
    check("BLOCKED-SOURCING" in text,
          "init emitted a sourcing state its own admission check cannot read")
    check(release_rehearsal._declares_blocked_sourcing(
              manifest, release / "ORDER_README.md"),
          "freshly initialized manifest cannot enter blocked-sourcing rehearsal")


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


@test("S-PART shadow publication failure preserves readiness exit")
def t_part_freeze_shadow_failure_is_nonblocking():
    project = tmpdir("part_freeze_shadow_failure_")
    output = project / "readiness.json"
    receipt = {
        "verdict": "ACCEPTED", "phase": "prelayout",
        "coverage": {"passing": 2, "total": 2}}
    with mock.patch("manufacturing_readiness.grade", return_value=receipt), \
         mock.patch("manufacturing_readiness._publish_part_freeze",
                    side_effect=OSError("shadow disk unavailable")):
        rc = manufacturing_readiness.main([
            "grade", str(project), "--phase", "prelayout",
            "--json", str(output),
            "--stage-bundle", str(project / "bundle"),
            "--stage-result", str(project / "stage.json"),
        ])
    eq(rc, 0, "shadow publisher changed accepted readiness exit")
    check(output.is_file(), "legacy readiness receipt was not retained")


@test("S-PART rejects output aliases before grading", kind="known_bad")
def t_part_freeze_output_alias_is_rejected():
    project = tmpdir("part_freeze_alias_")
    output = project / "readiness.json"
    output.write_text("sentinel")
    with mock.patch("manufacturing_readiness.grade") as grade:
        rc = manufacturing_readiness.main([
            "grade", str(project), "--phase", "prelayout",
            "--json", str(output),
            "--stage-bundle", str(project / "bundle"),
            "--stage-result", str(output),
        ])
    eq(rc, 2, "aliased S-PART output was accepted")
    grade.assert_not_called()
    eq(output.read_text(), "sentinel", "S-PART overwrote aliased receipt")


@test("S-PART stage request leaves prior accepted bundle untouched")
def t_part_freeze_request_never_promotes_bundle():
    project = tmpdir("part_freeze_no_promote_")
    source = project / "source.yaml"
    source.write_text("parts: [U1]\n")
    output = project / "readiness.json"
    stage = project / "stage.json"
    bundle = project / "bundle"
    bundle.mkdir()
    (bundle / "sentinel.txt").write_text("accepted")
    receipt = {
        "schema": 1, "kind": "manufacturing-readiness-receipt-v1",
        "phase": "prelayout", "verdict": "ACCEPTED", "project": "fixture",
        "inputs": {"source": record(source)},
        "checks": {"exact_code_identity": {
            "status": "PASS", "detail": "fixture", "rows": []}},
        "coverage": {"passing": 1, "total": 1},
    }
    with mock.patch("manufacturing_readiness.grade", return_value=receipt):
        rc = manufacturing_readiness.main([
            "grade", str(project), "--phase", "prelayout",
            "--json", str(output), "--stage-bundle", str(bundle),
            "--stage-result", str(stage),
        ])
    eq(rc, 0)
    eq((bundle / "sentinel.txt").read_text(), "accepted")
    eq(json.loads(stage.read_text())["status"], "INCOMPLETE")


if __name__ == "__main__":
    raise SystemExit(main())
