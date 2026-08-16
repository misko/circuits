#!/usr/bin/env python3
"""T1: generate_board_generic.py — the generic board generator.

Clean cases: parts land where the config says. Must-fail cases: a missing
FPID is a HARD ERROR (the defect that matters most — a silently un-placed
part is an electrically-wrong board that still passes DRC).
"""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, board_nodes, check, contains, eq,  # noqa: E402
                     main, must_fail, must_pass, run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
MODEL_COVERAGE = SCRIPTS / "model_coverage_check.py"
LC = ROOT / "archived_projects" / "cook-loadcell"
HUB4 = ROOT / "projects" / "usb-hub-3s-v4"
PLUTO_RX2 = ROOT / "projects" / "pluto-rx2-8way"


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


@test("model_override is source-bound and the independent model coverage gate "
      "fails after that body disappears", kind="known_bad")
def t_model_override_and_coverage():
    import yaml
    d = tmpdir("gbg_model_")
    body = d / "body.step"
    body.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n")
    cfg = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    cfg["project"]["netlist"] = str(LC / cfg["project"]["netlist"])
    if cfg["project"].get("parts_dir"):
        cfg["project"]["parts_dir"] = str(LC / cfg["project"]["parts_dir"])
    cfg["placement"].setdefault("patterns", []).append({
        "match": "*", "model_override": {
            "file": "${KIPRJMOD}/body.step",
            "offset": [1.25, -2.5, 0.1],
            "scale": [1, 1, 1],
            "rotate": [0, 0, 270],
        }})
    floorplan = d / "floorplan.yaml"
    floorplan.write_text(yaml.safe_dump(cfg))
    board = d / "board.kicad_pcb"
    built = gen(floorplan, board)
    contains(built.out, "3D model overrides: 29 footprints",
             "generator model-override coverage")

    clean = run([KPY, MODEL_COVERAGE, board])
    must_pass(clean, "model coverage on resolvable local bodies")
    # The cook-loadcell fixture has 29 generated component footprints, seven
    # deliberately excluded from its fitted BOM population.
    contains(clean.out, "PASS MODEL-COVERAGE: 22/22", "coverage verdict")

    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "m=list(b.FindFootprintByReference('U1').Models())[0]\n"
            "print('@@',m.m_Offset.x,m.m_Offset.y,m.m_Offset.z,"
            "m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z)\n")
    probe = must_pass(run([KPY, "-c", code, board]),
                      "probe explicit model transform")
    contains(probe.out, "@@ 1.25 -2.5 0.1 0.0 0.0 270.0",
             "model_override mapping transform")

    body.unlink()
    broken = run([KPY, MODEL_COVERAGE, board])
    must_fail(broken, "model coverage after its source body is removed",
              "FAIL MODEL-COVERAGE: 0/22")


@test("placement.sides flips only named footprints and validates its closed "
      "top/bottom vocabulary", kind="known_bad")
def t_explicit_placement_sides():
    import yaml
    d, cfgp = scratch_config(
        lambda cfg: cfg["placement"].update({"sides": {"U1": "bottom"}}),
        "bottom.yaml")
    board = d / "bottom.kicad_pcb"
    built = gen(cfgp, board)
    contains(built.out, "placed 1 footprint(s) on B.Cu",
             "explicit bottom-side count")
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "print('@@',b.FindFootprintByReference('U1').IsFlipped(),"
            "b.FindFootprintByReference('J1').IsFlipped())\n")
    probe = must_pass(run([KPY, "-c", code, board]), "probe footprint sides")
    contains(probe.out, "@@ True False", "one bottom and one default-top part")

    bad_d, bad_cfg = scratch_config(
        lambda cfg: cfg["placement"].update({"sides": {"U1": "inner"}}),
        "bad-side.yaml")
    bad = gen(bad_cfg, bad_d / "bad.kicad_pcb", expect_ok=False)
    must_fail(bad, "invalid placement side", "accepts only top|bottom")

    ghost_d, ghost_cfg = scratch_config(
        lambda cfg: cfg["placement"].update(
            {"sides": {"U_NOT_PRESENT": "bottom"}}), "ghost-side.yaml")
    ghost = gen(ghost_cfg, ghost_d / "ghost.kicad_pcb", expect_ok=False)
    must_fail(ghost, "unknown side refdes", "names unknown refdes")


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


@test("post_anchors moves only reviewed refs after legalization, preserving "
      "every other footprint position")
def t_post_anchors_preserve_legalizer_result():
    import yaml
    d = tmpdir("gbg_post_")
    base = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    base["project"]["netlist"] = str(LC / base["project"]["netlist"])
    if base["project"].get("parts_dir"):
        base["project"]["parts_dir"] = str(LC / base["project"]["parts_dir"])
    p0, p1 = d / "base.yaml", d / "post.yaml"
    p0.write_text(yaml.safe_dump(base))
    changed = yaml.safe_load(yaml.safe_dump(base))
    changed["placement"]["post_anchors"] = {"R1": [30.0, 39.5, 0]}
    p1.write_text(yaml.safe_dump(changed))
    b0, b1 = d / "base.kicad_pcb", d / "post.kicad_pcb"
    gen(p0, b0)
    r = gen(p1, b1)
    contains(r.out, "post-anchored 1 reviewed local part(s)",
             "generator stdout")
    code = (
        "import pcbnew,sys\n"
        "def poses(p):\n"
        " b=pcbnew.LoadBoard(p)\n"
        " return {f.GetReference():(f.GetPosition().x,f.GetPosition().y,"
        "round(f.GetOrientationDegrees(),6)) for f in b.GetFootprints()}\n"
        "a,c=poses(sys.argv[1]),poses(sys.argv[2])\n"
        "print('@@'+','.join(sorted(r for r in a if a[r]!=c[r])))\n")
    rr = must_pass(run([KPY, "-c", code, b0, b1]), "compare post anchors")
    eq(rr.out.split("@@", 1)[1].strip(), "R1",
       "post_anchors changed a footprint other than the named ref")


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


@test("a 6-layer board places inner GND planes on In3.Cu and In4.Cu")
def t_six_layer_inner_planes():
    """The mixed-signal-audio-hub (crow-recorder-central-v2) needs a 6-layer
    In1+In4 GND-plane stackup. generate_board_generic's LAYER_NAMES/INNER_LAYERS
    must know In3.Cu/In4.Cu — before they did not, and a declared In4.Cu plane
    failed 'zone on GND on unknown layer In4.Cu' (the error that surfaced
    building central-v2). This is the GREEN half; reverting the In3/In4 rows in
    LAYER_NAMES/INNER_LAYERS turns it RED (verified 2026-07-23)."""
    def mutate(cfg):
        cfg["board"]["layers"] = 6
        cfg["zones"].append({"net": "GND", "layers": ["In3.Cu", "In4.Cu"],
                             "priority": 0})
    d, p = scratch_config(mutate)
    out = d / "b.kicad_pcb"
    gen(p, out)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "ls=set()\n"
            "for z in b.Zones():\n"
            "  if not z.GetIsRuleArea():\n"
            "    ls|={b.GetLayerName(l) for l in z.GetLayerSet().Seq()}\n"
            "print('@@'+','.join(sorted(ls)))\n")
    r = must_pass(run([KPY, "-c", code, out]), "probe inner planes")
    got = r.out.split("@@")[1].strip()
    contains(got, "In3.Cu", "GND plane on In3.Cu")
    contains(got, "In4.Cu", "GND plane on In4.Cu")


@test("an In4.Cu plane on a 4-layer board is a hard error", kind="known_bad")
def t_in4_needs_six_layers():
    """In4.Cu is in LAYER_NAMES but INNER_LAYERS requires >=6 copper layers;
    declaring it on a 4-layer board must be REJECTED by check_layer, not
    silently dropped onto a layer the stackup lacks (the same failure class as
    t_zone_layer_not_in_stackup, one layer up)."""
    def mutate(cfg):
        cfg["board"]["layers"] = 4
        cfg["zones"].append({"net": "GND", "layers": ["In4.Cu"], "priority": 0})
    d, p = scratch_config(mutate)
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generator with an In4 plane on a 4-layer board",
              "not in the stackup")


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


@test("an fp-lib-table is emitted BY DEFAULT beside the output board")
def t_fp_lib_table_default():
    """Emission used to be opt-in and the v4 canary never opted in: 116
    lib_footprint_issues at first DRC, one per footprint. A fresh board must
    get the table with no config at all; `fp_lib_table: false` opts out; the
    env var must match the RUNNING KiCad major (a ${KICAD9_*} table on
    KiCad 10 resolves only through back-compat luck)."""
    d = tmpdir("gbg_")
    out = d / "b.kicad_pcb"
    gen(LC / "03_src" / "floorplan.yaml", out)
    table = d / "fp-lib-table"
    check(table.is_file(), "no fp-lib-table emitted by default")
    txt = table.read_text()
    for lib in ("Capacitor_SMD", "Resistor_SMD", "MountingHole"):
        contains(txt, f'(name "{lib}")', "fp-lib-table rows")
    r = must_pass(run([KPY, "-c",
                       "import pcbnew,re;"
                       "print('@@'+re.match(r'\\d+', pcbnew.Version()).group())"]),
                  "kicad major")
    major = r.out.split("@@")[1].strip()
    contains(txt, "${KICAD%s_FOOTPRINT_DIR}" % major,
             "the env var must match the running KiCad major")
    # explicit opt-out still works
    def mutate(cfg):
        cfg["project"]["fp_lib_table"] = False
    d2, p2 = scratch_config(mutate)
    gen(p2, d2 / "b.kicad_pcb")
    check(not (d2 / "fp-lib-table").exists(),
          "fp_lib_table: false must suppress emission")


@test("DRC's lib_footprint_issues class is EMPTY on a fresh board, and "
      "would not be without the table", kind="known_bad")
def t_kb_lib_footprint_issues():
    """The v4 composition: 116 of 648 first-DRC findings were 'The current
    configuration does not include the footprint library X'. Both ways: with
    the emitted table the class is empty; DELETE the table and the same DRC
    reports the class for every footprint — proving the detection has teeth
    and the fix is the table, not a quieter checker."""
    d = tmpdir("gbg_")
    out = d / "b.kicad_pcb"
    gen(LC / "03_src" / "floorplan.yaml", out)

    def lib_issues():
        import json
        outj = d / "drc.json"
        run(["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json",
             "-o", outj, out])
        g = json.loads(outj.read_text())
        return sum(1 for v in g["violations"]
                   if v["type"] == "lib_footprint_issues")
    eq(lib_issues(), 0, "lib_footprint_issues on a fresh board WITH its table")
    (d / "fp-lib-table").unlink()
    n = lib_issues()
    check(n >= 33, f"deleting the table must expose the class for every "
                   f"footprint (29 parts + 4 holes), got {n}")


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


@test("the board's silk DRC constraints derive from the declared tier "
      "(not KiCad's 0.8mm default)")
def t_silk_constraints_from_tier():
    """pcbnew's fresh-BOARD default m_MinSilkTextHeight is 0.8mm, ABOVE the
    0.6mm refdes this generator emits — so a fresh tiered board failed its
    own silk at first DRC (112 text_height findings on the v4 112-part
    board, 2026-07-21; the shipped 2-layer boards only pass because their
    sealed .kicad_pro was hand-set to 0.6). The constraint must derive from
    the same tier the text heights are floored at. RED-verified against the
    pre-fix generator (git show HEAD swap, 2026-07-21): it leaves 0.8/0.08
    and this test fails."""
    d, p = _tiered_silk_tree(0.45)
    out = d / "b.kicad_pcb"
    gen(p, out)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "ds=b.GetDesignSettings()\n"
            "print('@@%.6f,%.6f' % (ds.m_MinSilkTextHeight/1e6,"
            " ds.m_MinSilkTextThickness/1e6))\n")
    r = must_pass(run([KPY, "-c", code, out]), "probe silk constraints")
    h, t = [float(v) for v in r.out.split("@@")[1].strip().split(",")]
    want_h, want_t = _tier_silk_floors()
    check(abs(h - want_h) < 1e-6,
          f"silk height constraint is {h}, want the tier floor {want_h}")
    check(abs(t - want_t) < 1e-6,
          f"silk stroke constraint is {t}, want the tier floor {want_t}")
    # and no emitted silk text may sit below the constraint it now carries
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\nbad=[]\n"
            "silk={pcbnew.F_SilkS,pcbnew.B_SilkS}\n"
            "def scan(t,who):\n"
            "  if not callable(getattr(t,'GetTextSize',None)): return\n"
            "  if t.GetLayer() not in silk: return\n"
            "  if hasattr(t,'IsVisible') and not t.IsVisible(): return\n"
            f"  if t.GetTextSize().y<{int(want_h*1e6)-1000} or "
            f"t.GetTextThickness()<{int(want_t*1e6)-1000}:\n"
            "    bad.append((who,t.GetTextSize().y/1e6,t.GetTextThickness()/1e6))\n"
            "for f in b.GetFootprints():\n"
            "  scan(f.Reference(),f.GetReference()); scan(f.Value(),f.GetReference())\n"
            "  for g in f.GraphicalItems(): scan(g,f.GetReference())\n"
            "for g in b.GetDrawings(): scan(g,'board')\n"
            "print('@@'+repr(bad))\n")
    r = must_pass(run([KPY, "-c", code, out]), "scan silk text floors")
    got = r.out.split("@@")[1].strip()
    check(got == "[]", f"silk text below the tier floors survived: {got}")


def _tiny_text_tree():
    """A scratch tree with a declared tier and ONE part on a project-local
    library whose footprint carries a 0.3mm F.SilkS user text — the
    footprint-INTERNAL text nothing policed (the library never declared a
    tier, so generation must normalize, not error)."""
    import yaml
    d = tmpdir("gbg_tiny_")
    net = (LC / "06_build" / "netlists" / "cook_loadcell.net").read_text()
    broken = net.replace('(footprint "Capacitor_SMD:C_0805_2012Metric")',
                         '(footprint "local:C_0805_2012Metric")', 1)
    check(broken != net, "fixture netlist rewrite failed")
    (d / "06_build").mkdir()
    (d / "06_build" / "tiny.net").write_text(broken)
    pretty = d / "03_src" / "lib" / "local.pretty"
    pretty.mkdir(parents=True)
    mod = Path("/usr/share/kicad/footprints/Capacitor_SMD.pretty/"
               "C_0805_2012Metric.kicad_mod").read_text()
    tiny = ('\t(fp_text user "TINY"\n\t\t(at 0 2.6 0)\n'
            '\t\t(layer "F.SilkS")\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size 0.3 0.3)\n\t\t\t\t(thickness 0.05)\n'
            '\t\t\t)\n\t\t)\n\t)\n)\n')
    body = mod.rstrip()
    (pretty / "C_0805_2012Metric.kicad_mod").write_text(
        body[:body.rfind(")")] + tiny)
    cfg = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    cfg["project"]["netlist"] = str(d / "06_build" / "tiny.net")
    if cfg["project"].get("parts_dir"):
        cfg["project"]["parts_dir"] = str(LC / cfg["project"]["parts_dir"])
    libs = cfg.get("libraries") or ["/usr/share/kicad/footprints"]
    cfg["libraries"] = [{"lib": "local",
                         "path": "03_src/lib/local.pretty"}] + list(libs)
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "03_src" / "rules" / "nets.yaml").write_text(
        "fab_tier: jlc_2layer_default\n")
    p = d / "fp.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p


@test("footprint-INTERNAL 0.3mm silk text is normalized to the tier floor "
      "at generation")
def t_fp_internal_text_normalized():
    """silk_h() floors what the generator EMITS; this pins what it PLACES: a
    library footprint arriving with sub-floor silk text of its own must come
    out at the tier floor (v4 evidence: 112 text_height findings, all on
    footprint fields). RED-verified against the pre-fix generator (git show
    HEAD swap, 2026-07-21): the 0.3mm text survives and this test fails."""
    d, p = _tiny_text_tree()
    out = d / "b.kicad_pcb"
    r = gen(p, out)
    contains(r.out, "normalized", "generation must report the normalization")
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "hits=[]\n"
            "for f in b.GetFootprints():\n"
            "  for g in f.GraphicalItems():\n"
            "    if callable(getattr(g,'GetText',None)) and g.GetText()=='TINY':\n"
            "      hits.append((g.GetTextSize().y/1e6, g.GetTextThickness()/1e6))\n"
            "print('@@'+repr(hits))\n")
    rr = must_pass(run([KPY, "-c", code, out]), "probe TINY text")
    hits = eval(rr.out.split("@@")[1].strip())
    check(hits, "the TINY fixture text is missing from the board")
    h, t = hits[0]
    check(abs(h - 0.45) < 1e-6,
          f"footprint-internal text height is {h}, want normalized 0.45")
    _, want_t = _tier_silk_floors()
    check(t >= want_t - 1e-9,
          f"footprint-internal text stroke is {t}, want >= {want_t}")


@test("an explicit design_rules silk constraint below the tier floor FAILS "
      "naming the tier", kind="known_bad")
def t_kb_silk_constraint_below_tier():
    """A sub-tier DRC constraint means DRC stops policing sub-floor silk —
    the check would exist but could not bite. RED-verified against the
    pre-fix generator (git show HEAD swap, 2026-07-21): the old code has no
    silk_text_height key and rejects it as unknown, but with the key mapped
    it applied any value without consulting the tier."""
    def mutate(cfg):
        cfg["design_rules"] = dict(cfg.get("design_rules") or {},
                                   silk_text_height=0.3)
    d, p = scratch_config(mutate)
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "03_src" / "rules" / "nets.yaml").write_text(
        "fab_tier: jlc_2layer_default\n")
    r = run([KPY, GEN, p, "-o", d / "b.kicad_pcb"], cwd=LC)
    must_fail(r, "generate with a sub-tier silk DRC constraint",
              "jlc_2layer_default")
    contains(r.out, "min_silk_text_height", "the failure must cite the floor")


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




def _tier_silk_floors(tier="jlc_4layer_advanced"):
    """Read the floors FROM fab_tiers.yaml. These tests are named "derive from
    the declared tier" and used to pin the literal 0.15 instead — so when
    G-SELFCON (ADR-0007) corrected the stroke floor to the value the 0.45 height
    can actually carry, both went red for the one reason a derivation test must
    not: the config it derives from changed, exactly as intended."""
    import yaml
    d = yaml.safe_load((ROOT / "skills" / "kicad-pcb" / "references" /
                        "fab_tiers.yaml").read_text())
    e = d["tiers"][tier]
    return float(e["min_silk_text_height"]), float(e["min_silk_stroke"])


# ------------------------------------------------- the stroke/height coupling
@test("the EMITTED stroke follows the generator's own formula: 0.60mm text "
      "gets 0.13, and 0.15 needs 0.9375mm")
def t_silk_stroke_threshold():
    """fab_tiers.yaml declared for one day (ad487df) that 'to reach the
    published 0.15 stroke, text must be >= 0.60mm'. IT IS 0.9375mm. The
    generator emits max(min_silk_stroke, 0.13, 0.16 x size), clamped to KiCad's
    0.25 x size, so 0.60 / 0.70 / 0.80 ALL emit 0.13 and only 0.16 x h >= 0.15
    gets there. MEASURED on shipped output: pluto-rx2-8way's 0.95mm port
    captions print 0.152 and its 0.60mm safety captions print 0.130.

    This test pins the EMITTER; t1_gate_contract pins the RULE FILE that
    documents it, against the same function. Both move together or neither
    does. RED-verified two ways (2026-07-29): against the corollary as written
    (0.60mm emits 0.1300, so the claimed 0.15 is off by 13%), and against the
    pre-fix generator run out of a temp repo copy — it emits **0.1300** for the
    0.45mm caption below, above KiCad's own 0.25 x height clamp of 0.1125, i.e.
    it stored a stroke KiCad cannot plot. The clamp is a no-op at every height
    at or above 0.52mm, which is every height any shipped board uses."""
    def mutate(cfg):
        cfg["silk"]["min_text_height"] = 0.45
        cfg["silk"]["captions"] = [
            {"text": "SIXTENTHS", "at": [45.0, 45.0], "size": 0.6},
            {"text": "REACHES", "at": [45.0, 50.0], "size": 0.9375},
            {"text": "SEVENTENTHS", "at": [55.0, 45.0], "size": 0.7},
            {"text": "CLAMPED", "at": [55.0, 50.0], "size": 0.45},
        ]
    d, p = scratch_config(mutate)
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "03_src" / "rules" / "nets.yaml").write_text(
        "fab_tier: jlc_2layer_default\n")
    out = d / "b.kicad_pcb"
    gen(p, out)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\ng={}\n"
            "for t in b.GetDrawings():\n"
            "  if t.GetClass()=='PCB_TEXT' and t.IsOnLayer(pcbnew.F_SilkS):\n"
            "    g[t.GetText()]=(t.GetTextSize().y/1e6,t.GetTextThickness()/1e6)\n"
            "print('@@'+repr(g))\n")
    r = must_pass(run([KPY, "-c", code, out]), "probe caption strokes")
    got = eval(r.out.split("@@")[1].strip())
    for txt, want_h, want_t in (("SIXTENTHS", 0.6, 0.13),
                                ("SEVENTENTHS", 0.7, 0.13),
                                ("REACHES", 0.9375, 0.15),
                                ("CLAMPED", 0.45, 0.1125)):
        h, t = got[txt]
        check(abs(h - want_h) < 1e-6, f"{txt} height {h} != {want_h}")
        check(abs(t - want_t) < 1e-6,
              f"{txt} at {want_h}mm emits a {t}mm stroke, not {want_t} — the "
              f"fab_tiers.yaml corollary and the emitter disagree")


# ------------------------------------------------------ silk OWNERSHIP (M-COVER)
def _measure_ownership(out):
    """Ownership measured from the SAVED BOARD by code that shares nothing
    with the placer (canon M1): for every visible silk refdes and every board
    silk text, the nearest footprint centroid to the text's box centre.
    Mounting holes/fiducials print no designator, so they do not compete —
    the same exclusion `_ownership` makes, stated rather than shared.
    Returns (mislabelled_refdes, {text: nearest_ref})."""
    code = ("import pcbnew,sys,math,re\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "MM=pcbnew.ToMM\nfps={f.GetReference():f for f in b.GetFootprints()}\n"
            "cen={r:(MM(f.GetPosition().x),MM(f.GetPosition().y))\n"
            "     for r,f in fps.items() if not re.match(r'H\\d|FID',r)}\n"
            "def near(x,y,skip=None):\n"
            "  best=(1e9,None)\n"
            "  for r,(cx,cy) in cen.items():\n"
            "    if r==skip: continue\n"
            "    d=math.hypot(cx-x,cy-y)\n"
            "    if d<best[0]: best=(d,r)\n"
            "  return best\n"
            "def ctr(t):\n"
            "  bb=t.GetBoundingBox()\n"
            "  return (MM((bb.GetLeft()+bb.GetRight())//2),\n"
            "          MM((bb.GetTop()+bb.GetBottom())//2))\n"
            "mis=[]\n"
            "for r,f in sorted(fps.items()):\n"
            "  t=f.Reference()\n"
            "  if not t.IsVisible() or r not in cen: continue\n"
            "  if t.GetLayer() not in (pcbnew.F_SilkS,pcbnew.B_SilkS): continue\n"
            "  x,y=ctr(t); own=math.hypot(cen[r][0]-x,cen[r][1]-y)\n"
            "  d,o=near(x,y,r)\n"
            "  if d<own: mis.append((r,round(own,2),o,round(d,2)))\n"
            "txt={}\n"
            "for g in b.GetDrawings():\n"
            "  if g.GetClass()=='PCB_TEXT' and g.IsOnLayer(pcbnew.F_SilkS):\n"
            "    x,y=ctr(g); d,o=near(x,y); txt[g.GetText()]=(o,round(d,2))\n"
            "print('@@'+repr((mis,txt)))\n")
    r = must_pass(run([KPY, "-c", code, out]), "measure silk ownership")
    return eval(r.out.split("@@")[1].strip())


@test("every silk refdes lands nearer its OWN part than any other, and the "
      "placer reports the ownership denominator")
def t_silk_ownership():
    """THE MISSING OBJECTIVE. The slot search took the first non-colliding
    offset out to ~11mm and never asked whose label it was, so a label naming
    its neighbour was indistinguishable from a correct one. Measured on shipped
    output 2026-07-29: pluto-cal-switch 36 of 73 refdes nearer another part
    than their own, pluto-rx2-8way 40 of 64, and on a board with ten
    near-identical SMA jacks that is a mis-mate hazard, not a cosmetic one.

    RED-VERIFIED against the pre-fix placer (`git show HEAD:...
    generate_board_generic.py` run out of a temp dir with PYTHONPATH into
    skills/kicad-pcb/scripts, 2026-07-29): on cook-loadcell it places **6 of
    29** refdes nearer another part — C7 (own 6.00mm vs SJ1 3.50), J1 (7.00 vs
    Q1 5.09), J6 (3.60 vs D1 1.75), TP6 (7.07 vs D1 3.22), TP7 (6.00 vs D2
    2.83), U1 (6.00 vs C5 5.79) — and prints NO ownership line at all, so both
    assertions here fail. After the term: 0 of 29, and 36/36 owned labels.

    Tightening the METRIC does not substitute for the TERM: pluto-cal-switch
    tried courtyard-edge distance instead of centroid and it rescued ZERO of
    its 36."""
    d = tmpdir("gbg_own_")
    out = d / "b.kicad_pcb"
    r = gen(LC / "03_src" / "floorplan.yaml", out)
    contains(r.out, "silk ownership:", "the placer must report ownership")
    m = re.search(r"silk ownership: (\d+)/(\d+) owned labels", r.out)
    check(m is not None, f"no ownership denominator (canon M-COVER): {r.out[-400:]!r}")
    ok, tot = int(m.group(1)), int(m.group(2))
    check(tot >= 29, f"only {tot} labels graded on a 29-part board — the "
                     f"denominator has gone quiet")
    mis, _ = _measure_ownership(out)
    check(mis == [], f"labels nearer another part than their own: {mis}")
    check(ok == tot, f"placer claims {ok}/{tot} owned but the board measures "
                     f"clean — the report and the board disagree")


@test("a label that CANNOT own its slot is REPORTED with its measured lead, "
      "never silently first-slotted", kind="known_bad")
def t_kb_silk_ownership_degraded():
    """THE HONEST DEGRADATION. Some labels genuinely cannot be nearest their
    own part — cooksense's J_ISOLOOP has its pads at the CENTRE of the body in
    x, so anything printed either side is under the moulding once fitted. The
    failure mode to prevent is not the degradation, it is the SILENCE: the
    pre-fix placer took the first clear slot and said nothing, which is how 36
    of 73 shipped.

    The fixture crowds three caps into the left edge so TP2's 'S+' terminal
    legend has no owned slot in the whole 84-offset search. Note it is a
    FUNCTIONAL label — the safety-legible class — not a refdes.

    Not an exit code, deliberately: a board with an unownable label is still
    buildable, so the contract is an EVIDENCED report with the measured lead
    and a denominator. RED-verified against the pre-fix placer (same temp-dir
    swap as the test above, 2026-07-29): it prints no WARN and no ownership
    line for this fixture, and every assertion below fails; the 'S+' legend
    still lands 3.04mm from R2 against 4.40mm from its own TP2."""
    def mutate(cfg):
        cfg["placement"]["anchors"].update({
            "C1": [20.9, 38.0, 0], "C2": [24.5, 38.0, 0],
            "C3": [20.9, 41.6, 0], "C4": [20.9, 34.4, 0]})
    d, p = scratch_config(mutate)
    out = d / "b.kicad_pcb"
    r = gen(p, out)
    contains(r.out, "WARN silk ownership:", "the degradation must be reported")
    m = re.search(r"WARN silk ownership: (\w+) '([^']+)' for (\w+) lands "
                  r"([\d.]+)mm from \w+ but ([\d.]+)mm from (\w+)", r.out)
    check(m is not None, f"the WARN carries no measured lead: {r.out[-600:]!r}")
    kind, txt, ref, d_own, d_oth, oth = m.groups()
    check(float(d_oth) < float(d_own),
          f"the reported lead is not a degradation: {m.group(0)}")
    dm = re.search(r"silk ownership: (\d+)/(\d+) owned labels sit nearer "
                   r"their own part than any other; (\d+) degraded", r.out)
    check(dm is not None, f"no ownership summary: {r.out[-400:]!r}")
    check(int(dm.group(3)) >= 1, "a degradation happened but 0 were counted")
    # canon M1: the REPORT's claim must survive an independent measurement of
    # the saved board — a gate that grades its own arithmetic proves nothing.
    mis, texts = _measure_ownership(out)
    if kind == "refdes":
        check(any(x[0] == ref for x in mis),
              f"reported {ref} degraded, but the board measures it owned: {mis}")
    else:
        check(texts.get(txt, (None,))[0] == oth,
              f"report says {txt!r} is nearest {oth}; the board says "
              f"{texts.get(txt)}")

# --------------------------------------------- escape corridors (Phase F)
@test("escape_corridors expands to a named footprint/pour rule area")
def t_corridor_clean():
    d, cfg = scratch_config(lambda c: c.update(
        {"escape_corridors": [{"ref": "U1", "side": "N", "depth_mm": 3.0}]}))
    out = d / "b.kicad_pcb"
    gen(cfg, out)
    txt = out.read_text()
    check('esc_U1_N' in txt, "corridor rule area esc_U1_N not on the board")


@test("escape_corridor with an unknown ref is a HARD generation error",
      kind="known_bad")
def t_corridor_bad_ref():
    d, cfg = scratch_config(lambda c: c.update(
        {"escape_corridors": [{"ref": "U99", "side": "N", "depth_mm": 3.0}]}))
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "corridor on unknown ref", "unknown ref")


@test("escape_corridor with a bad side is a HARD generation error",
      kind="known_bad")
def t_corridor_bad_side():
    d, cfg = scratch_config(lambda c: c.update(
        {"escape_corridors": [{"ref": "U1", "side": "Q", "depth_mm": 3.0}]}))
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "corridor with bad side", "side must be")


# ---------------------------------------------------------------- P-COLLIDE
# RED-VERIFIED against the pre-fix generator (2026-07-25): with
# check_placement_collisions() removed from build(), BOTH known-bad cases below
# generate cleanly and exit 0 — which is exactly how smc0985-cooksense v1.3
# committed a board with U_COMP2 anchored ON TOP OF Q_SWA (byte-identical
# anchors [30.0,88.0,0]) and J_ESTOPLOOP inside J_DOOR, shorting the
# opto-isolated 30V contactor loop to 3V3/GND/DOOR_RAW. kicad DRC does catch it
# (6 shorting_items) but nothing forces DRC to run before the router does.

@test("P-COLLIDE passes a placement whose parts do not overlap")
def t_collide_clean():
    d = tmpdir("gbg_")
    r = gen(LC / "03_src" / "floorplan.yaml", d / "b.kicad_pcb")
    contains(r.out, "P-COLLIDE: 0 inter-footprint pad overlaps/shorts, 0 anchored courtyard overlap",
             "generator stdout")


@test("P-COLLIDE FAILS two parts anchored at the SAME coordinate",
      kind="known_bad")
def t_kb_anchor_collision():
    # J2 dropped exactly onto J1: the cooksense U_COMP2/Q_SWA defect, minimised.
    def mutate(c):
        c["placement"]["anchors"]["J2"] = list(
            c["placement"]["anchors"]["J1"])
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "coincident anchors", "P-COLLIDE")
    contains(r.out, "PINNED-LAP", "P-COLLIDE report")
    contains(r.out, "SHORT", "P-COLLIDE report")


@test("P-COLLIDE names BOTH refs and the shorted nets, not just a count")
def t_collide_names_the_nets():
    def mutate(c):
        c["placement"]["anchors"]["J2"] = list(
            c["placement"]["anchors"]["J1"])
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    txt = r.out
    for want in ("J1", "J2"):
        contains(txt, want, "P-COLLIDE names the colliding refs")


@test("P-COLLIDE FAILS an anchored courtyard overlap with no pad short",
      kind="known_bad")
def t_collide_pinned_lap_fails():
    """Placement owns assembly clearance. Deferring an anchored overlap to
    final DRC allowed the programmable USB hub's resistor/module interference
    to survive until render review. Archived boards remain immutable; every
    newly generated or materially revised board must move the anchors."""
    # slide J2 into J1's courtyard, but not far enough for pads to touch:
    # B3B-XH courtyard is 10.99 wide on an 11.1mm pitch, pads at 2.5mm pitch.
    def mutate(c):
        a = c["placement"]["anchors"]
        a["J2"] = [a["J1"][0] + 10.6, a["J1"][1], a["J1"][2]]
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "anchored courtyard overlap", "P-COLLIDE")
    contains(r.out, "FAIL P-COLLIDE PINNED-LAP", "generator stdout")


@test("P-COLLIDE uses rotated courtyard polygons, not intersecting bboxes")
def t_rotated_courtyard_bbox_is_not_overlap():
    """The Pluto RX2 radial SMA ring has six rotated-jack pairs, plus its
    radial R_T1/R_T2 pair, whose axis-aligned courtyard boxes intersect while
    KiCad's actual polygons are separated.  The pre-fix generator called all
    seven PINNED-LAP and aborted before writing the board.  Preserve those
    electrically-derived anchors and prove the exact predicate on real output.
    """
    d = tmpdir("gbg_pluto_rotated_")
    out = d / "pluto_rx2_8way.kicad_pcb"
    r = gen(PLUTO_RX2 / "03_src" / "floorplan.yaml", out,
            cwd=PLUTO_RX2)
    contains(r.out,
             "P-COLLIDE: 0 inter-footprint pad overlaps/shorts, 0 anchored courtyard overlap",
             "rotated-courtyard generator result")
    code = (
        "import pcbnew,sys\n"
        "b=pcbnew.LoadBoard(sys.argv[1])\n"
        "f={x.GetReference():x for x in b.GetFootprints()}\n"
        "pairs=[('J_ANT2','J_ANT1'),('J_ANT4','J_ANT3'),"
        "('J_ANT6','J_ANT5'),('J_RX1','J_ANT7'),('J_RX1','J_ANT8'),"
        "('J_RX2','J_ANT1'),('R_T2','R_T1')]\n"
        "n=0\n"
        "for a,c in pairs:\n"
        " p=f[a].GetCourtyard(pcbnew.F_CrtYd);q=f[c].GetCourtyard(pcbnew.F_CrtYd)\n"
        " assert p.BBox().Intersects(q.BBox()) and not p.Collide(q),(a,c)\n"
        " n+=1\n"
        "print('@@%d' % n)\n")
    rr = must_pass(run([KPY, "-c", code, out]),
                   "probe rotated courtyard bbox false positives")
    eq(rr.out.split("@@", 1)[1].strip(), "7",
       "rotated bbox-only false-positive denominator")


# ------------------------------------------------------- edge-reaching notch
# A cutout rect that pokes THROUGH a board side is boundary geometry: the side
# has to be split around it. Emitted as a closed rectangle (pre-2026-07-25
# behaviour) the untouched side segment runs straight through it and the board
# has no valid outline at all — kicad DRC `invalid_outline`, "malformed outline
# (self-intersecting)". cooksense v1.3's H4 keypad-isolation notch shipped that
# way into a commit and was measured on "filled copper" that KiCad had healed.

def _outline_probe(board, pts):
    """Ask pcbnew whether the assembled Edge.Cuts polygon is valid, and which
    of `pts` are inside it. Independent of the generator's own geometry code."""
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "s=pcbnew.SHAPE_POLY_SET()\n"
            "ok=b.GetBoardPolygonOutlines(s,False)\n"
            "r=['VALID=%s' % ok, 'RINGS=%d' % s.OutlineCount()]\n"
            "for a in sys.argv[2:]:\n"
            "    x,y=[float(v) for v in a.split(',')]\n"
            "    r.append('IN(%s)=%s' % (a, s.Contains("
            "pcbnew.VECTOR2I_MM(x,y))))\n"
            "print('@@'+';'.join(r))\n")
    rr = must_pass(run([KPY, "-c", code, board] + [f"{x},{y}" for x, y in pts]),
                   "outline probe")
    return dict(kv.split("=") for kv in rr.out.split("@@")[1].strip().split(";"))


@test("an EDGE-REACHING cutout is cut into the boundary, not drawn as an island")
def t_edge_notch_outline():
    # cook-loadcell outline is x[20,75] y[20,65]; notch the EAST side.
    d, cfg = scratch_config(lambda c: c["board"].update(
        {"cutouts": [{"rect": [70.0, 40.0, 76.0, 42.0]}]}))
    out = d / "b.kicad_pcb"
    r = gen(cfg, out)
    contains(r.out, "1 edge notch(es) cut into the boundary", "generator stdout")
    p = _outline_probe(out, [(72.0, 41.0), (68.0, 41.0), (72.0, 38.0)])
    check(p["VALID"] == "True", f"outline not valid: {p}")
    check(p["RINGS"] == "1", f"expected one outer ring, got {p}")
    check(p["IN(72.0,41.0)"] == "False", f"notch interior still board: {p}")
    check(p["IN(68.0,41.0)"] == "True", f"west of notch should be board: {p}")
    check(p["IN(72.0,38.0)"] == "True", f"south of notch should be board: {p}")


@test("an INTERNAL cutout is still an island (no regression)")
def t_internal_cutout_still_island():
    d, cfg = scratch_config(lambda c: c["board"].update(
        {"cutouts": [{"rect": [60.0, 40.0, 64.0, 42.0]}]}))
    out = d / "b.kicad_pcb"
    r = gen(cfg, out)
    check("edge notch" not in r.out,
          f"internal cutout misclassified as a notch: {r.out}")
    p = _outline_probe(out, [(62.0, 41.0), (58.0, 41.0)])
    check(p["VALID"] == "True", f"outline not valid: {p}")
    check(p["IN(62.0,41.0)"] == "False", f"island interior still board: {p}")
    check(p["IN(58.0,41.0)"] == "True", f"outside the island should be board: {p}")


@test("a cutout crossing TWO sides (a corner) is a HARD error, not a guess",
      kind="known_bad")
def t_kb_corner_cutout():
    d, cfg = scratch_config(lambda c: c["board"].update(
        {"cutouts": [{"rect": [70.0, 60.0, 76.0, 66.0]}]}))
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "corner-crossing cutout", "reaches past 2 board sides")


@test("a cutout spanning a WHOLE side severs the board and is a HARD error",
      kind="known_bad")
def t_kb_severing_cutout():
    d, cfg = scratch_config(lambda c: c["board"].update(
        {"cutouts": [{"rect": [70.0, 15.0, 76.0, 70.0]}]}))
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "board-severing cutout", "not a notch")


@test("a declared physical stackup is emitted, parseable, and preserved")
def t_stackup_roundtrip():
    def mutate(c):
        c["board"]["stackup"] = {
            "nominal_thickness_mm": 1.6,
            "thickness_tolerance_mm": 0.02,
            "copper_finish": "ENIG",
            "dielectric_constraints": True,
            "mask_thickness_mm": 0.01,
            "copper_thickness_mm": [0.035, 0.035],
            "dielectrics": [{
                "type": "core", "thickness_mm": 1.53,
                "material": "FR4", "epsilon_r": 4.4,
                "loss_tangent": 0.02,
            }],
        }
    d, cfg = scratch_config(mutate)
    out = d / "b.kicad_pcb"
    r = gen(cfg, out)
    contains(r.out, "stackup authored: 2 copper layers", "generator stdout")
    text = out.read_text()
    contains(text, "(stackup", "generated board")
    contains(text, '(copper_finish "ENIG")', "generated board")
    contains(text, '(layer "dielectric 1"', "generated board")
    # pcbnew must accept the native block and preserve it through a save.
    rt = d / "roundtrip.kicad_pcb"
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "pcbnew.SaveBoard(sys.argv[2],b)\n"
            "print('@@%.3f' % pcbnew.ToMM(b.GetDesignSettings().GetBoardThickness()))\n")
    rr = must_pass(run([KPY, "-c", code, out, rt]), "stackup roundtrip")
    contains(rr.out, "@@1.600", "stackup roundtrip")
    contains(rt.read_text(), "(stackup", "round-tripped board")


@test("a stackup with the wrong layer cardinality is a hard error",
      kind="known_bad")
def t_kb_stackup_cardinality():
    def mutate(c):
        c["board"]["stackup"] = {
            "nominal_thickness_mm": 1.6,
            "copper_thickness_mm": [0.035],
            "dielectrics": [{
                "type": "core", "thickness_mm": 1.53,
                "material": "FR4", "epsilon_r": 4.4,
                "loss_tangent": 0.02,
            }],
        }
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "one-copper-entry stackup",
              "copper_thickness_mm must contain exactly 2 entries")


@test("board-level via protection emits parseable capping/filling setup tokens")
def t_via_protection():
    def mutate(c):
        c["board"]["via_protection"] = {"capping": True, "filling": True}
    d, cfg = scratch_config(mutate)
    out = d / "b.kicad_pcb"
    r = gen(cfg, out)
    contains(r.out, "via protection authored (board-level): capping=yes, filling=yes",
             "generator stdout")
    text = out.read_text()
    eq(len(re.findall(r"\(capping yes\)", text)), 1,
       "generated board capping token")
    eq(len(re.findall(r"\(filling yes\)", text)), 1,
       "generated board filling token")
    check("(capping no)" not in text and "(filling no)" not in text,
          "generator left contradictory disabled via-protection tokens")
    # The text injection must be native pcbnew state, not a comment-like patch:
    # downstream route/stitch stages load and save the board repeatedly.
    roundtrip = d / "roundtrip.kicad_pcb"
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "pcbnew.SaveBoard(sys.argv[2],b)\n"
            "print('@@%d' % len(list(b.GetFootprints())))\n")
    rr = must_pass(run([KPY, "-c", code, out, roundtrip]),
                   "via-protection roundtrip")
    contains(rr.out, "@@33", "via-protection parse")
    contains(roundtrip.read_text(), "(capping yes)",
             "round-tripped board capping token")
    contains(roundtrip.read_text(), "(filling yes)",
             "round-tripped board filling token")


@test("invalid via-protection values fail before a board can claim a process",
      kind="known_bad")
def t_kb_via_protection_value():
    def mutate(c):
        c["board"]["via_protection"] = {"capping": "sometimes"}
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "invalid via-protection value",
              "board.via_protection.capping must be a boolean (yes/no)")


@test("marked footprint heatsink holes promote to real board vias with exact "
      "geometry and net")
def t_promote_heatsink_pads_to_vias():
    d = tmpdir("gbg_thermal_")
    out = d / "usb_hub_3s_v4.kicad_pcb"
    r = gen(HUB4 / "03_src" / "floorplan.yaml", out, cwd=HUB4)
    contains(r.out, "thermal vias: emitted 48 explicit + promoted 0 marked "
             "heatsink pad(s) across 8 footprint(s)", "promotion coverage")
    code = (
        "import pcbnew,sys,collections\n"
        "b=pcbnew.LoadBoard(sys.argv[1])\n"
        "refs={'U1','U2','U3','U4','U5','U6','U9'}\n"
        "marked=sum(1 for f in b.GetFootprints() if f.GetReference() in refs "
        "for p in f.Pads() if p.GetProperty()==pcbnew.PAD_PROP_HEATSINK "
        "and p.GetDrillSize().x>0)\n"
        "v=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA']\n"
        "linked=[f for f in b.GetFootprints() if f.GetReference() in refs "
        "and f.GetFPIDAsString() and 'generated thermal-via promotion' "
        "not in f.GetLibDescription()]\n"
        "geo=collections.Counter((round(t.GetWidth(pcbnew.F_Cu)/1e6,3),"
        "round(t.GetDrill()/1e6,3),t.GetNetname()) for t in v)\n"
        "prot=collections.Counter((t.GetCappingMode(),t.GetFillingMode()) "
        "for t in v)\n"
        "owned=[]\n"
        "for f in b.GetFootprints():\n"
        "  for p in f.Pads():\n"
        "    if p.GetNumber() in ('17','18','19','20','21','22','25','26','11','2'):\n"
        "      for t in v:\n"
        "        if t.GetNetCode()==p.GetNetCode() and p.HitTest(t.GetPosition(),0,pcbnew.F_Cu):\n"
        "          owned.append((f.GetReference(),p.GetNumber(),t.GetNetname()))\n"
        "print('@@%d|%d|%d|%r|%r|%r' % (marked,len(v),len(linked),"
        "sorted(geo.items()),sorted(owned),sorted(prot.items())))\n")
    rr = must_pass(run([KPY, "-c", code, out]), "probe promoted thermal vias")
    result = rr.out.split("@@", 1)[1].strip()
    check(result.startswith("0|48|7|"),
          f"expected zero drilled heatsink pads, 48 true vias and seven "
          f"library-linked parity-safe footprints, got {result}")
    contains(result, "(0.5, 0.2, '5VA_RAW'), 4",
             "0.20mm eFuse input thermal via family")
    contains(result, "(0.5, 0.2, 'GND'), 44",
             "JLC-compatible 0.20mm ground thermal via family")
    contains(result, "((1, 1), 48)",
             "every explicit thermal via carries item-level Type VII intent")
    contains(result, "('U9', '25', '5VA_RAW')",
             "rotated split input field remains inside U9 pad 25")
    contains(result, "('U9', '26', 'GND')",
             "rotated split ground field remains inside U9 pad 26")
    contains(result, "('C23', '2', 'GND')",
             "cold-socket ground vias remain inside C23 pad 2")


@test("thermal-via promotion refuses a named footprint with no marked holes",
      kind="known_bad")
def t_kb_promote_heatsink_empty_match():
    def mutate(c):
        c["thermal_vias"] = {"promote_heatsink_pads": ["U1"]}
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "empty heatsink-pad promotion", "has no drilled "
              "pad_prop_heatsink pads")


@test("an explicit thermal-via field refuses an unknown footprint",
      kind="known_bad")
def t_kb_thermal_field_unknown_ref():
    def mutate(c):
        c["thermal_vias"] = {"fields": [{"ref": "U_DOES_NOT_EXIST",
                                           "pad": 1, "size": 0.5,
                                           "drill": 0.2,
                                           "at": [[0, 0]]}]}
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "unknown explicit thermal field", "unknown ref")


@test("an invalid item-level thermal-via process is a hard error",
      kind="known_bad")
def t_kb_thermal_field_bad_protection():
    code = (
        "import pcbnew,sys\n"
        f"sys.path.insert(0,{str(SCRIPTS)!r})\n"
        "from pcb_toolkit import apply_via_protection\n"
        "b=pcbnew.BOARD(); v=pcbnew.PCB_VIA(b)\n"
        "apply_via_protection(v,{'capping':'perhaps'},"
        "'thermal_vias.fields[0].protection')\n")
    r = run([KPY, "-c", code])
    must_fail(r, "invalid item-level via protection",
              "thermal_vias.fields[0].protection.capping must be a boolean")


@test("a self-intersecting zone polygon fails before KiCad can discard its "
      "power-cell fill", kind="known_bad")
def t_kb_zone_polygon_self_intersection():
    def mutate(c):
        z = c["zones"][0]
        z.pop("rect", None)
        z.pop("region", None)
        # Crossed quadrilateral with NONZERO signed area, so this exercises
        # the segment-intersection guard rather than only the area guard.
        z["points"] = [[25, 25], [35, 25], [25, 35], [33, 35]]
    d, cfg = scratch_config(mutate)
    r = gen(cfg, d / "b.kicad_pcb", expect_ok=False)
    must_fail(r, "self-intersecting zone", "self-intersection/overlap")


@test("M-REPRO: two runs from identical source are BYTE-IDENTICAL, and no "
      "two objects share a UUID", kind="known_bad")
def t_uuid_determinism():
    """THE INCIDENT (2026-07-26, usb-hub-3s-v3 v1.6 STAGED-NOT-SEALED).
    Three from-source regenerations of identical source gave 292/294/293
    vias. The generator was deterministic in every VALUE (identical
    footprint hashes across isolated runs) but minted FRESH RANDOM UUIDs
    each run; KiCad serialises footprints in UUID order, so the zone filler
    walked zones in a different order, Clipper tessellated pour boundaries
    differently, and island_rescue inherited all of it. Fixed by seeding
    KiCad's own KIID generator (KIID::SeedGenerator, mt19937 — stable
    across runs AND machines) from the output board name before any object
    is created.

    On byte comparison: tests/README bans GOLDEN files because KRT routing
    is stochastic. This test stores no golden — it compares two FRESH runs
    of the same (KRT-free) generate stage to each other, and byte-identity
    of that pair IS the property under test (canon M-REPRO).

    The uniqueness half is the collision proof the fix's comment promises:
    a deterministic UUID scheme must never assign two objects one identity,
    so |uuid set| must equal |object count| on a real generated board.

    RED-VERIFIED 2026-07-26: with the pre-fix generator (seed_uuids()
    removed) restored, the two runs differ at the first footprint uuid and
    the byte-identity assertion FAILS; confirmed, then the fix restored."""
    d = tmpdir("gbg_")
    # SAME board name in two dirs: the UUID seed is derived from the output
    # board name (identical source => identical name => identical stream),
    # so a differing name is a differing source, not a repro of this run.
    (d / "r1").mkdir(); (d / "r2").mkdir()
    a, b = d / "r1" / "b.kicad_pcb", d / "r2" / "b.kicad_pcb"
    gen(LC / "03_src" / "floorplan.yaml", a)
    gen(LC / "03_src" / "floorplan.yaml", b)
    ba, bb = a.read_bytes(), b.read_bytes()
    check(ba == bb,
          "two generate runs from identical source differ — UUID minting is "
          "nondeterministic again, and every downstream fill/tessellation/"
          "island decision inherits it (the 292/294/293-via class)")
    code = (
        "import pcbnew,sys\n"
        "b=pcbnew.LoadBoard(sys.argv[1])\n"
        "items=[]\n"
        "for f in b.GetFootprints():\n"
        "  items.append(f.m_Uuid.AsString())\n"
        "  items+=[p.m_Uuid.AsString() for p in f.Pads()]\n"
        "  items+=[g.m_Uuid.AsString() for g in f.GraphicalItems()]\n"
        "items+=[t.m_Uuid.AsString() for t in b.GetTracks()]\n"
        "items+=[z.m_Uuid.AsString() for z in b.Zones()]\n"
        "items+=[dr.m_Uuid.AsString() for dr in b.GetDrawings()]\n"
        "print('@@%d,%d' % (len(items), len(set(items))))\n")
    r = must_pass(run([KPY, "-c", code, a]), "uuid uniqueness probe")
    n, uniq = [int(v) for v in r.out.split("@@")[1].strip().split(",")]
    check(n > 100, f"probe saw only {n} objects — the board did not build")
    eq(uniq, n, "UUID set size vs object count (a collision means two "
                "objects share one identity)")


if __name__ == "__main__":
    sys.exit(main())
