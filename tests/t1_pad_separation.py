#!/usr/bin/env python3
"""T1: inter-footprint copper and paste separation gate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

GATE = SCRIPTS / "pad_separation.py"


def board_fixture(*, distance_mm=1.20, same_footprint=False,
                  paste_margin_mm=0.0, add_track=False):
    d = tmpdir("padsep_")
    out = d / "fixture.kicad_pcb"
    code = f"""
import pcbnew
V = pcbnew.VECTOR2I_MM
b = pcbnew.CreateEmptyBoard()
net = pcbnew.NETINFO_ITEM(b, "SIG"); b.Add(net)

def footprint(ref):
    f = pcbnew.FOOTPRINT(b); f.SetReference(ref); b.Add(f); return f

def pad(owner, number, x):
    p = pcbnew.PAD(owner); p.SetNumber(str(number))
    p.SetShape(pcbnew.PAD_SHAPE_RECT); p.SetSize(V(1.0, 1.0))
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD); p.SetLayerSet(pcbnew.PAD.SMDMask())
    p.SetPosition(V(x, 10.0)); p.SetNet(net)
    p.SetLocalSolderPasteMargin(pcbnew.FromMM({paste_margin_mm}))
    owner.Add(p); return p

a = footprint("R1")
c = a if {same_footprint!r} else footprint("U1")
p1 = pad(a, 1, 10.0)
p2 = pad(c, 2, 10.0 + {distance_mm})
if {add_track!r}:
    t = pcbnew.PCB_TRACK(b); t.SetLayer(pcbnew.F_Cu); t.SetNet(net)
    t.SetWidth(pcbnew.FromMM(0.20)); t.SetStart(p1.GetPosition())
    t.SetEnd(p2.GetPosition()); b.Add(t)
pcbnew.SaveBoard(r"{out}", b)
"""
    must_pass(run([KPY, "-c", code]), "pad-separation fixture builder")
    return out


def gate(board, gap=0.10):
    return run([KPY, GATE, board, "--min-gap-mm", str(gap)])


@test("P-PADSEP accepts separated same-net pads joined by an explicit track")
def t_clean_explicit_connection():
    board = board_fixture(distance_mm=1.20, add_track=True)
    r = must_pass(gate(board), "separated pads")
    contains(r.out, "P-PADSEP PASS", "clean verdict")
    contains(r.out, "1 inter-footprint pad pair", "coverage denominator")


@test("P-PADSEP rejects positive but sub-floor pad clearance", kind="known_bad")
def t_sub_floor_gap():
    r = must_fail(gate(board_fixture(distance_mm=1.05)), "0.05 mm pad gap",
                  "P-PAD-GAP")
    contains(r.out, "0.050 mm < 0.100 mm", "measured gap")


@test("P-PADSEP rejects exact edge contact", kind="known_bad")
def t_zero_distance_touch():
    must_fail(gate(board_fixture(distance_mm=1.0)), "touching pad edges",
              "P-PAD-TOUCH")


@test("P-PADSEP rejects same-net copper overlap", kind="known_bad")
def t_same_net_overlap():
    r = must_fail(gate(board_fixture(distance_mm=0.75)),
                  "same-net overlapping pads", "P-PAD-OVERLAP")
    contains(r.out, "intersection", "overlap area evidence")


@test("P-PADSEP allows composite pads within one footprint")
def t_same_footprint_composite_is_allowed():
    r = must_pass(gate(board_fixture(distance_mm=0.0, same_footprint=True)),
                  "same-footprint composite land")
    contains(r.out, "0 inter-footprint pad pair", "earned zero denominator")


@test("P-PADSEP rejects a stencil aperture over foreign copper",
      kind="known_bad")
def t_paste_intrusion():
    # Copper clears by 0.20 mm; R1's +0.30 mm paste expansion crosses U1.
    r = must_fail(gate(board_fixture(distance_mm=1.20,
                                     paste_margin_mm=0.30)),
                  "paste over foreign land", "P-PASTE-INTRUSION")
    check("P-PAD-GAP" not in r.out and "P-PAD-OVERLAP" not in r.out,
          f"fixture did not isolate paste from copper spacing:\n{r.out}")


@test("the photographed RX2 v4 geometry is pinned in immutable release v1.0",
      kind="known_bad")
def t_real_rx2_module_overlap():
    project = (Path(__file__).resolve().parents[1] / "archived_projects" /
               "pluto-rx2-8way-v4")
    board = (project / "07_releases" / "v1.0-2026-08-01" / "source" /
             "pluto_rx2_8way_v4.kicad_pcb")
    r = must_fail(run([KPY, GATE, board, "--project", project]),
                  "RX2 resistor/module overlap", "P-PAD-OVERLAP")
    for ref in ("R_S1", "R_S2", "R_S3", "R_S4", "R_LED", "U_MCU"):
        contains(r.out, ref, "RX2 exact refs")


if __name__ == "__main__":
    sys.exit(main())
