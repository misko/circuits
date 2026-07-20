#!/usr/bin/env python3
"""E2E (slow tier): regenerate REAL boards with the generic generator and
prove they are electrically identical to the sealed ones.

This is the validation gate from the generic-generator work, kept as a
permanent regression: any change to generate_board_generic.py that alters
connectivity on a shipped board fails here. Sealed 04_kicad boards are read
ONLY — every artifact goes to a scratch dir.

Asserts PROPERTIES (node-for-node parity, audit verdict), never file bytes:
the silk de-collision search is order-dependent and KRT routing is
stochastic, so a golden-file comparison would be permanently broken.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main, must_pass,  # noqa: E402
                     project_copy, run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
PARITY = SCRIPTS / "board_netlist_parity.py"

BOARDS = [
    ("cook-loadcell", "cook_loadcell", 33),
    ("crow-array-pod", "crow_array_pod", 40),
    ("shitty-kitty", "shitty_kitty", 82),
]


def _regen_and_check(project, stem, nparts):
    proj_dir = ROOT / "projects" / project
    d = tmpdir(f"e2e_{stem}_")
    out = d / f"{stem}.kicad_pcb"
    r = must_pass(run([KPY, GEN, proj_dir / "03_src" / "floorplan.yaml", "-o", out],
                      cwd=proj_dir), f"{project}: generate")
    contains(r.out, "saved", "generator stdout")

    sealed = proj_dir / "04_kicad" / f"{stem}.kicad_pcb"
    rp = must_pass(run([KPY, PARITY, out, sealed]), f"{project}: parity")
    contains(rp.out, "BOARD PARITY 0 -> PASS", f"{project} parity verdict")

    # audit_board.py is path-hardcoded to 04_kicad/, so give it a scratch
    # project tree with the candidate board in place of the sealed one.
    scratch = project_copy(project, d / "proj", board=out)
    wv = d / "refdes_waiver.json"
    src_wv = out.parent / "refdes_waiver.json"
    if src_wv.exists():
        shutil.copy(src_wv, scratch / "06_build" / "refdes_waiver.json")
    ra = must_pass(run([KPY, "03_src/audit_board.py"], cwd=scratch),
                   f"{project}: audit_board")
    check("AUDIT PASS" in ra.out or "AUDIT: PASS" in ra.out,
          f"{project}: audit_board did not report PASS\n{ra.out[-2000:]}")
    return r, rp, ra


@test("E2E cook-loadcell: generic generator -> parity 0 + audit PASS", slow=True)
def t_cook_loadcell():
    r, rp, ra = _regen_and_check(*BOARDS[0])
    contains(rp.out, "77 nodes identical", "cook-loadcell parity node count")


@test("E2E crow-array-pod: generic generator -> parity 0 + audit PASS", slow=True)
def t_crow_array_pod():
    r, rp, ra = _regen_and_check(*BOARDS[1])
    contains(rp.out, "90 nodes identical", "crow-array-pod parity node count")


@test("E2E shitty-kitty (4-LAYER): generic generator -> parity 0 + audit PASS",
      slow=True)
def t_shitty_kitty():
    """The 4-layer proof. cook-loadcell and crow-array-pod are both 2-layer
    with a GND pour on each side; neither has an inner plane, a split plane,
    or a rule area, so the generator's plane/isolation code was shipped
    unexercised. This board has all three:
      * In1.Cu solid GND return plane
      * In2.Cu SPLIT power plane — three non-overlapping, non-rectangular
        pours (VIN_12V / 5V / 3V3) at priority 2 with per-zone min fill
      * a rule area spanning ALL FOUR copper layers (ESP32 antenna clearing)
    The last one found a real defect: SetLayer() after SetLayerSet() collapsed
    the rule area to F.Cu alone.
    """
    r, rp, ra = _regen_and_check(*BOARDS[2])
    contains(rp.out, "358 nodes identical", "shitty-kitty parity node count")
    contains(r.out, "asserts: 18 passed", "shitty-kitty asserts")


@test("E2E shitty-kitty: the 4-layer planes and the all-layer rule area "
      "survive to the saved board", slow=True)
def t_shitty_kitty_planes():
    """Parity is node-level, so it cannot see a zone at all: a board with
    every plane silently dropped would still report parity 0. This asserts
    the plane/isolation geometry itself, against the sealed board's."""
    proj = ROOT / "projects" / "shitty-kitty"
    d = tmpdir("e2e_sk_zones_")
    out = d / "shitty_kitty.kicad_pcb"
    must_pass(run([KPY, GEN, proj / "03_src" / "floorplan.yaml", "-o", out],
                  cwd=proj), "shitty-kitty: generate")
    built = _zone_summary(out)
    sealed = _zone_summary(proj / "04_kicad" / "shitty_kitty.kicad_pcb")
    check(built["layers"] == 4, f"copper layer count is {built['layers']}, want 4")
    check(built["pours"] == sealed["pours"],
          "pour zones differ from the sealed board\n"
          f"  built : {built['pours']}\n  sealed: {sealed['pours']}")
    # order-independent: LSET.Seq() enumerates outer layers before inner
    check([(n, sorted(ls)) for n, ls in built["rule_areas"]]
          == [("ANT_KEEPOUT", sorted(["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]))],
          f"antenna rule area is not on all four layers: {built['rule_areas']}")


def _zone_summary(path):
    """(net, layer, priority, min_thickness, pad-connection) per pour, plus
    (name, layers) per rule area. A subprocess so the harness needs no pcbnew."""
    import json
    code = (
        "import pcbnew,sys,json\n"
        "b=pcbnew.LoadBoard(sys.argv[1])\n"
        "o={'layers':b.GetCopperLayerCount(),'pours':[],'rule_areas':[]}\n"
        "for z in b.Zones():\n"
        "  ls=[b.GetLayerName(l) for l in z.GetLayerSet().Seq()]\n"
        "  if z.GetIsRuleArea(): o['rule_areas'].append([z.GetZoneName(),ls])\n"
        "  else: o['pours'].append([z.GetNetname(),ls,z.GetAssignedPriority(),\n"
        "      round(pcbnew.ToMM(z.GetMinThickness()),3),int(z.GetPadConnection())])\n"
        "o['pours'].sort(); o['rule_areas'].sort()\n"
        "print('@@'+json.dumps(o))\n")
    r = must_pass(run([KPY, "-c", code, str(path)]), "zone summary")
    o = json.loads(r.out.split("@@")[1].strip())
    return {"layers": o["layers"],
            "pours": [tuple([p[0], tuple(p[1])] + p[2:]) for p in o["pours"]],
            "rule_areas": [(a[0], a[1]) for a in o["rule_areas"]]}


@test("E2E: regenerating twice gives the same CONNECTIVITY (not the same bytes)",
      slow=True)
def t_determinism():
    """Placement search and silk de-collision may reorder; connectivity may
    not. This is why the suite asserts properties, not file hashes."""
    from harness import board_nodes
    proj_dir = ROOT / "projects" / "cook-loadcell"
    d = tmpdir("e2e_det_")
    outs = []
    for i in (1, 2):
        o = d / f"b{i}.kicad_pcb"
        must_pass(run([KPY, GEN, proj_dir / "03_src" / "floorplan.yaml", "-o", o],
                      cwd=proj_dir), f"regen {i}")
        outs.append(o)
    a, b = board_nodes(outs[0]), board_nodes(outs[1])
    check(a == b, "two runs produced different connectivity")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] + ["--slow"]))
