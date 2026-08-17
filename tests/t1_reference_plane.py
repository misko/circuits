#!/usr/bin/env python3
"""Focused red/green fixtures for projected reference-plane interruptions."""
import importlib.util
from pathlib import Path

from harness import (KPY, SCRIPTS, check, contains, eq, main, must_fail,
                     must_pass, run, test, tmpdir)


SPEC = importlib.util.spec_from_file_location(
    "reference_plane_check", SCRIPTS / "reference_plane_check.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
GATE = SCRIPTS / "reference_plane_check.py"


def board_fixture(crossing=True):
    d = tmpdir("refplane_")
    board = d / "fixture.kicad_pcb"
    config = d / "nets.yaml"
    obstacle_x = 5.0 if crossing else 20.0
    code = f"""
import pcbnew
b = pcbnew.CreateEmptyBoard(); b.SetCopperLayerCount(4)
nets = {{}}
for name in ('HS_P', 'GND', 'CTRL'):
    n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
def track(net, layer, a, z, width):
    t = pcbnew.PCB_TRACK(b); t.SetNet(nets[net]); t.SetLayer(layer)
    t.SetStart(pcbnew.VECTOR2I_MM(*a)); t.SetEnd(pcbnew.VECTOR2I_MM(*z))
    t.SetWidth(pcbnew.FromMM(width)); b.Add(t)
track('HS_P', pcbnew.B_Cu, (0, 5), (10, 5), 0.2)
track('GND', pcbnew.In2_Cu, (30, 0), (30, 1), 0.2)
track('CTRL', pcbnew.In2_Cu, ({obstacle_x}, 0), ({obstacle_x}, 10), 0.2)
pcbnew.SaveBoard(r'{board}', b)
"""
    must_pass(run([KPY, "-c", code]), "reference-plane fixture builder")
    config.write_text("""reference_plane_checks:
  HS:
    signal_layer: B.Cu
    reference_layer: In2.Cu
    reference_net: GND
    signal_nets: [HS_P]
    min_track_clearance_mm: 0.30
    min_via_clearance_mm: 0.15
""")
    return board, config


@test("reference-plane geometry reports a direct crossing", kind="known_bad")
def t_crossing_segments_are_zero_distance():
    eq(MOD._segment_distance((0, 0), (10, 0), (5, -2), (5, 2)), 0.0)


@test("reference-plane geometry measures parallel clearance")
def t_separated_segments_report_exact_margin():
    got = MOD._segment_distance((0, 0), (10, 0), (0, 1), (10, 1))
    check(abs(got - 1.0) < 1e-9, f"expected 1.0, got {got}")


@test("reference-plane geometry measures endpoint projection")
def t_endpoint_projection_is_not_missed():
    got = MOD._segment_distance((0, 0), (2, 0), (3, 1), (3, 4))
    check(abs(got - 2 ** 0.5) < 1e-9, f"expected sqrt(2), got {got}")


@test("reference-plane gate rejects the reproduced inner-track crossing",
      kind="known_bad")
def t_gate_rejects_crossing():
    board, config = board_fixture(crossing=True)
    result = must_fail(run([KPY, GATE, board, "--config", config]),
                       "crossing reference-plane fixture")
    contains(result.out, '"verdict": "FAIL"', "fail verdict")
    contains(result.out, '"clearance_mm": -0.2', "measured overlap")


@test("reference-plane gate accepts a clear foreign inner track")
def t_gate_accepts_clearance():
    board, config = board_fixture(crossing=False)
    result = must_pass(run([KPY, GATE, board, "--config", config]),
                       "clear reference-plane fixture")
    contains(result.out, '"verdict": "PASS"', "pass verdict")


if __name__ == "__main__":
    main()
