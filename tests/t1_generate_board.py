#!/usr/bin/env python3
"""T1: generate_board_generic.py — the generic board generator.

Clean cases: parts land where the config says. Must-fail cases: a missing
FPID is a HARD ERROR (the defect that matters most — a silently un-placed
part is an electrically-wrong board that still passes DRC).
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, board_nodes, check, contains, eq,  # noqa: E402
                     main, must_fail, must_pass, run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
LC = ROOT / "projects" / "cook-loadcell"


def gen(cfg, out, cwd=LC, expect_ok=True):
    r = run([KPY, GEN, cfg, "-o", out], cwd=cwd)
    return must_pass(r, "generate_board_generic") if expect_ok else r


def scratch_config(mutate, name="fp.yaml"):
    """Copy cook-loadcell's real floorplan and mutate it — a known-bad
    fixture is a GOOD config broken in exactly one way."""
    import yaml
    d = tmpdir("gbg_")
    cfg = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    # the copy lives outside the project, so re-root its relative paths
    cfg["project"]["netlist"] = str(LC / cfg["project"]["netlist"])
    if cfg["project"].get("parts_dir"):
        cfg["project"]["parts_dir"] = str(LC / cfg["project"]["parts_dir"])
    mutate(cfg)
    p = d / name
    p.write_text(yaml.safe_dump(cfg))
    return d, p


@test("generate_board_generic places every netlist part per the config")
def t_places():
    d = tmpdir("gbg_")
    out = d / "b.kicad_pcb"
    r = gen(LC / "03_src" / "floorplan.yaml", out)
    contains(r.out, "placed 29 footprints", "generator stdout")
    contains(r.out, "asserts: 8 passed", "generator stdout")
    check(out.is_file(), "no board written")
    nodes = board_nodes(out)
    # anchored parts must be exactly where the config put them, untouched
    # by the legalizer
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "f=b.FindFootprintByReference('U1')\n"
            "print('@@%.3f,%.3f' % (pcbnew.ToMM(f.GetPosition().x),"
            " pcbnew.ToMM(f.GetPosition().y)))\n")
    rr = must_pass(run([KPY, "-c", code, out]), "probe U1")
    x, y = [float(v) for v in rr.out.split("@@")[1].strip().split(",")]
    check(abs(x - 38.0) < 0.001 and abs(y - 42.0) < 0.001,
          f"anchored U1 moved: ({x},{y}) != (38.0,42.0)")
    check(len(nodes) == 77, f"expected 77 netted pads, got {len(nodes)}")


@test("generate_board_generic writes an F.Fab refdes copy for every part")
def t_fab_copy():
    d = tmpdir("gbg_")
    out = d / "b.kicad_pcb"
    gen(LC / "03_src" / "floorplan.yaml", out)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "n=sum(1 for t in b.GetDrawings() if t.GetClass()=='PCB_TEXT'"
            " and t.IsOnLayer(pcbnew.F_Fab))\nprint('@@',n)\n")
    r = must_pass(run([KPY, "-c", code, out]), "count F.Fab")
    n = int(r.out.split("@@")[1].strip())
    check(n >= 33, f"expected >=33 F.Fab refdes copies (29 parts + 4 holes), got {n}")


@test("MISSING FPID is a hard error, not a silent skip", kind="known_bad")
def t_missing_fpid():
    """The netlist's footprint field is blanked for one part and 02_parts
    has no override. The generator must REFUSE to build the board."""
    d = tmpdir("gbg_")
    net = (LC / "06_build" / "netlists" / "cook_loadcell.net").read_text()
    # blank U1's footprint exactly as a broken schematic footprint-map would
    i = net.index('(ref "U1")')
    j = net.index('(footprint "', i)
    k = net.index('"', j + 12)
    broken = net[:j] + '(footprint ""' + net[k + 1:]
    check(broken != net, "fixture did not actually blank the FPID")
    bad_net = d / "broken.net"
    bad_net.write_text(broken)

    import yaml
    cfg = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    cfg["project"]["netlist"] = str(bad_net)
    cfg["project"].pop("parts_dir", None)     # no override to rescue it
    p = d / "fp.yaml"
    p.write_text(yaml.safe_dump(cfg))

    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator on a blank-FPID netlist", "U1 has no footprint FPID")
    check(not (d / "b.kicad_pcb").exists(),
          "generator wrote a board despite the hard error")


@test("an FPID naming a footprint no library has is a hard error", kind="known_bad")
def t_unknown_footprint():
    d = tmpdir("gbg_")
    net = (LC / "06_build" / "netlists" / "cook_loadcell.net").read_text()
    broken = net.replace("Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
                         "Package_SO:NoSuchFootprint_ZZZ", 1)
    if broken == net:      # netlist uses a different U1 package — blanket swap
        import re as _re
        broken = _re.sub(r'\(footprint "[^"]*SOIC[^"]*"\)',
                         '(footprint "Package_SO:NoSuchFootprint_ZZZ")', net, count=1)
    check(broken != net, "fixture did not inject an unknown footprint")
    bad = d / "broken.net"
    bad.write_text(broken)
    import yaml
    cfg = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    cfg["project"]["netlist"] = str(bad)
    p = d / "fp.yaml"
    p.write_text(yaml.safe_dump(cfg))
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator on an unknown footprint", "footprint not found")


@test("a violated polarity assert blocks the build", kind="known_bad")
def t_bad_assert():
    """Flip a pad-net assert to the wrong net. The generator must refuse
    rather than ship a board with a backwards diode."""
    def mutate(cfg):
        for a in cfg["asserts"]["pad_net"]:
            if a["ref"] == "D1":
                a["net"] = "GND"          # D1 pad1 is really on DAT
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with a wrong polarity assert",
              "POLARITY/ROLE ASSERT: D1 pad 1")


@test("an over-subscribed floorplan fails loudly, not by stacking parts",
      kind="known_bad")
def t_legalizer_gives_up():
    """Shrink the legalizer's search radius to nothing while forcing every
    passive to start on the same point. It must raise, not silently leave
    parts overlapping."""
    def mutate(cfg):
        cfg["placement"]["seeds"] = {k: [38.0, 42.0] for k in cfg["placement"]["seeds"]}
        cfg["placement"]["legalize"]["ring_max"] = 2
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with an impossible floorplan", "no clear spot for")


@test("a zone on a net the netlist does not have is a hard error", kind="known_bad")
def t_bad_zone_net():
    def mutate(cfg):
        cfg["zones"][0]["net"] = "GNDA"       # typo for GND
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with a typo'd zone net", "zone on unknown net")


@test("a multi-layer rule area really lands on every layer it declares")
def t_multilayer_rule_area():
    """The 4-layer plane/isolation path, in a unit test.

    cook-loadcell is 2-layer with no keepouts, so this asked the generator
    for something no existing floorplan did: a rule area on four layers of a
    board that HAS four layers.
    """
    def mutate(cfg):
        cfg["board"]["layers"] = 4
        cfg["keepouts"] = [{"name": "ANT", "deny": ["tracks", "vias", "pours"],
                            "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
                            "rect": [30, 30, 40, 40]}]
    d, p = scratch_config(mutate)
    out = d / "b.kicad_pcb"
    gen(p, out)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "z=[z for z in b.Zones() if z.GetIsRuleArea()][0]\n"
            "print('@@'+','.join(sorted(b.GetLayerName(l) "
            "for l in z.GetLayerSet().Seq())))\n")
    r = must_pass(run([KPY, "-c", code, out]), "probe rule area")
    got = r.out.split("@@")[1].strip()
    eq(got, "B.Cu,F.Cu,In1.Cu,In2.Cu", "rule area layer set")


@test("a PERMISSIVE named rule area forbids nothing (it is a DRU anchor)")
def t_permissive_rule_area():
    """`deny: []` with a name is a real and distinct use: the area exists
    only so generate_rules.py can scope a .kicad_dru rule to
    insideArea('<name>') (cook-hub's u7_taps, usb-power-3s's SW_TAP_A/B).
    An implementation that always denies would silently fence off copper on
    boards whose rules depend on that area being open."""
    def mutate(cfg):
        cfg["keepouts"] = [{"name": "SW_TAP", "deny": [],
                            "layers": ["F.Cu"], "rect": [30, 30, 40, 40]}]
    d, p = scratch_config(mutate)
    out = d / "b.kicad_pcb"
    gen(p, out)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "z=[z for z in b.Zones() if z.GetIsRuleArea()][0]\n"
            "print('@@%s|%s' % (z.GetZoneName(), ','.join(str(int(v)) for v in ("
            "z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(),"
            " z.GetDoNotAllowPads(), z.GetDoNotAllowZoneFills()))))\n")
    r = must_pass(run([KPY, "-c", code, out]), "probe permissive rule area")
    name, flags = r.out.split("@@")[1].strip().split("|")
    eq(name, "SW_TAP", "rule area name (generate_rules scopes .kicad_dru to it)")
    eq(flags, "0,0,0,0", "a permissive rule area must forbid NOTHING")


@test("a rule area on a layer the stackup does not have is a hard error",
      kind="known_bad")
def t_rule_area_layer_not_in_stackup():
    """Found while proving the 4-layer path: `LSET` accepts In1.Cu on a
    2-layer board without complaint, so a rule area (or plane) could be
    declared on a layer that does not exist. It never fills, DRC is clean,
    and the isolation you asked for is simply absent."""
    def mutate(cfg):
        cfg["board"]["layers"] = 2                    # ...but ask for inners
        cfg["keepouts"] = [{"name": "ANT", "deny": ["tracks"],
                            "layers": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
                            "rect": [30, 30, 40, 40]}]
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with a rule area off the stackup",
              "not in the stackup")


@test("a PLANE on a layer the stackup does not have is a hard error",
      kind="known_bad")
def t_zone_layer_not_in_stackup():
    """Same defect on the pour path — an inner GND plane that silently is
    not there is worse than a missing keepout."""
    def mutate(cfg):
        cfg["board"]["layers"] = 2
        cfg["zones"].append({"net": "GND", "layers": ["In1.Cu"], "priority": 0})
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with a plane off the stackup", "not in the stackup")


@test("a bbox_override on a part the legalizer may move is a hard error",
      kind="known_bad")
def t_bbox_override_unpinned():
    """A bbox_override is an ABSOLUTE rect. On a floating part it would go
    stale the moment the legalizer moved it, and every later collision test
    would be computed against empty space."""
    def mutate(cfg):
        cfg["placement"]["bbox_override"] = {"C1": [30, 30, 40, 40]}
        cfg["placement"]["pin"] = ["U*"]          # C1 floats
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with a bbox_override on a floating part",
              "which the legalizer may move")


@test("a connector whose mouth faces the wrong way blocks the build",
      kind="known_bad")
def t_body_offset_assert():
    """`body_offset` is the only check that catches a 180-degree flip of a
    connector whose pads are symmetric — pad_order cannot see it."""
    def mutate(cfg):
        cfg.setdefault("asserts", {})["body_offset"] = [
            {"ref": "J1", "axis": "x", "sign": "+"},
            {"ref": "J1", "axis": "x", "sign": "-"},   # both cannot hold
        ]
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with a contradictory body_offset assert",
              "opening faces the wrong way")


@test("an edge-launch clearing that lands ON the board blocks the build",
      kind="known_bad")
def t_pad_beyond_edge_assert():
    """shitty-kitty's ESP32-S3 is only legal because its antenna keepout
    hangs off the south edge. Creep it inboard and the keepout sits on live
    copper; `pad_beyond_edge` is what refuses."""
    def mutate(cfg):
        cfg.setdefault("asserts", {})["pad_beyond_edge"] = [
            {"ref": "U1", "pad": 1, "offset": 0.0, "edge": "y1"}]
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with an on-board edge clearing", "INSIDE the y1 edge")


@test("netlist parity 0 vs the sealed cook-loadcell board")
def t_parity_loadcell():
    d = tmpdir("gbg_")
    out = d / "cook_loadcell.kicad_pcb"
    gen(LC / "03_src" / "floorplan.yaml", out)
    r = must_pass(run([KPY, SCRIPTS / "board_netlist_parity.py", out,
                       LC / "04_kicad" / "cook_loadcell.kicad_pcb"]),
                  "board_netlist_parity")
    contains(r.out, "BOARD PARITY 0 -> PASS", "parity output")


def _tiered_silk_tree(min_size):
    """A scratch floorplan tree that DECLARES a fab tier (03_src/rules/
    nets.yaml beside the config) with one silk height set explicitly."""
    def mutate(cfg):
        cfg["silk"]["refdes"] = dict(cfg["silk"]["refdes"],
                                     min_size=min_size)
    d, p = scratch_config(mutate)
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "03_src" / "rules" / "nets.yaml").write_text(
        "fab_tier: jlc_2layer_default\n")
    return d, p


@test("silk heights at the declared tier's floor still generate (control)")
def t_silk_at_tier_floor():
    d, p = _tiered_silk_tree(0.45)
    gen(p, d / "ok.kicad_pcb")


@test("an EXPLICIT silk text height below the tier floor FAILS naming the "
      "tier", kind="known_bad")
def t_kb_silk_below_tier():
    """The clean-room 3S run hand-carried its fab's silk floor because
    nothing read the declared tier; sub-floor silk prints illegibly and no
    gate saw it. Explicit sub-floor heights must be a hard error naming the
    tier (defaults are floored, never errored). The control test above
    proves the failure is the height, not the tier scaffolding. RED-verified
    against the pre-fix generator (git stash: the old code generates happily
    at 0.3mm) — 2026-07-21."""
    d, p = _tiered_silk_tree(0.3)
    r = gen(p, d / "bad.kicad_pcb", expect_ok=False)
    must_fail(r, "generate with a sub-tier silk height", "jlc_2layer_default")
    contains(r.out, "min_silk_text_height", "the failure must cite the floor")


if __name__ == "__main__":
    sys.exit(main())
