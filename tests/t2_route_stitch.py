#!/usr/bin/env python3
"""T2: route_and_stitch_generic.py — the generic router/stitcher.

Every assertion here is a PROPERTY, never a byte. KRT is stochastic (two
routes of cook-loadcell in one session produced 223 and 234 segments, both
DRC-clean), so a golden .kicad_pcb would be permanently broken. What is
stable: exit codes, the KRT command line, pass ORDER, node sets, and
whether a gate bites.

The KRT invocation tests drive a STUB router (`stub_krt()`) that records
its argv and copies input to output. That keeps the suite hermetic and
fast while still pinning the flags the real router receives — which is the
part that has actually shipped broken (`route_prep` handing KRT a bare
Default-0.2mm .kicad_pro, so ampacity floors were never in force).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, board_nodes, check, contains,  # noqa: E402
                     edit_board, eq, main, must_fail, must_pass, run, test,
                     tmpdir)

RS = SCRIPTS / "route_and_stitch_generic.py"
GEN = SCRIPTS / "generate_board_generic.py"
LC = ROOT / "projects" / "cook-loadcell"
STEM = "cook_loadcell"

_BOARD_CACHE = []


def _cached_board():
    """Generate the cook-loadcell board once per suite run; every test gets
    a private copy (stitch mutates in place)."""
    if not _BOARD_CACHE:
        d = tmpdir("t2_seed_")
        out = d / f"{STEM}.kicad_pcb"
        must_pass(run([KPY, GEN, LC / "03_src" / "floorplan.yaml", "-o", out],
                      cwd=LC), "seed board generation")
        _BOARD_CACHE.append(out)
    return _BOARD_CACHE[0]


def scratch(mutate=None, with_board=True):
    """A project tree with 03_src/route.yaml + 04_kicad/<board>. Known-bad
    fixtures are this GOOD tree broken in exactly one way."""
    import yaml
    d = tmpdir("t2_")
    (d / "03_src").mkdir()
    (d / "04_kicad").mkdir()
    cfg = yaml.safe_load((LC / "03_src" / "route.yaml").read_text())
    if with_board:
        shutil.copy(_cached_board(), d / "04_kicad" / f"{STEM}.kicad_pcb")
        for ext in (".kicad_pro", ".kicad_dru"):
            src = LC / "04_kicad" / f"{STEM}{ext}"
            if src.is_file():
                shutil.copy(src, d / "04_kicad" / f"{STEM}{ext}")
    if mutate:
        mutate(cfg, d)
    p = d / "03_src" / "route.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p


def stub_krt(d, exit_code=0, write_output=True):
    """A fake KRT that records argv and copies input->output. Hermetic
    stand-in for the real router; also the failure-injection seam."""
    k = d / "krt"
    k.mkdir(exist_ok=True)
    (k / "route.py").write_text(
        "import sys, shutil, json, pathlib\n"
        "a = sys.argv[1:]\n"
        "log = pathlib.Path(__file__).parent / 'calls.jsonl'\n"
        "log.open('a').write(json.dumps(a) + '\\n')\n"
        f"if {write_output}:\n"
        "    o = a[a.index('--output') + 1]\n"
        "    shutil.copy(a[0], o)\n"
        f"sys.exit({exit_code})\n")
    return k


def krt_calls(k):
    f = k / "calls.jsonl"
    return [json.loads(l) for l in f.read_text().splitlines()] if f.is_file() else []


def use_stub(cfg, d, **kw):
    cfg["route"]["krt"] = str(stub_krt(d, **kw))
    cfg["route"]["python"] = sys.executable
    cfg["route"].pop("final", None)


def prep(p, cwd=None):
    return run([KPY, RS, "prep", p], cwd=cwd)


def stitch(p):
    return run([KPY, RS, "stitch", p])


# =========================================================== CLEAN ======
@test("route-prep writes a track-free r0 with keepouts and wave net lists")
def t_prep():
    d, p = scratch()
    r = must_pass(prep(p), "prep")
    contains(r.out, "canon R1: rules ride along", "prep stdout")
    contains(r.out, "an(9)", "wave grouping")
    contains(r.out, "pwr(2)", "wave grouping")
    r0 = d / "06_build" / "route" / "r0.kicad_pcb"
    check(r0.is_file(), "no r0 written")
    for ext in (".kicad_pro", ".kicad_dru"):
        check(r0.with_suffix(ext).is_file(),
              f"canon R1: r0{ext} missing beside the route input")
    # the `rest` group must claim exactly the unclaimed, non-excluded nets
    sig = (d / "06_build" / "route" / "nets_sig.txt").read_text().split()
    check("GND" not in sig, "GND leaked into a routed wave — GND is pours")
    check(sig, "the rest-group is empty")


@test("route-prep draws keepouts on every configured layer")
def t_prep_keepout_layers():
    d, p = scratch()
    must_pass(prep(p), "prep")
    r0 = d / "06_build" / "route" / "r0.kicad_pcb"
    code = ("import pcbnew,sys,json\nb=pcbnew.LoadBoard(sys.argv[1])\no={}\n"
            "for g in b.GetDrawings():\n"
            "  if g.GetClass()=='PCB_SHAPE':\n"
            "    n=b.GetLayerName(g.GetLayer()); o[n]=o.get(n,0)+1\n"
            "print('@@'+json.dumps(o))\n")
    r = must_pass(run([KPY, "-c", code, r0]), "count keepouts")
    got = json.loads(r.out.split("@@", 1)[1].strip())
    check(got.get("User.2", 0) >= 8, f"User.2 keepouts missing: {got}")
    check(got.get("User.3", 0) >= 8,
          f"the analog-guard layer got no keepouts: {got}")


@test("the KRT command line carries the geometry, keepouts and per-wave overrides")
def t_krt_cmdline():
    d, p = scratch(use_stub)
    must_pass(prep(p), "prep")
    r = must_pass(run([sys.executable, RS, "route", p]), "route (stub KRT)")
    calls = krt_calls(d / "krt")
    check(len(calls) == 3, f"expected 3 waves, got {len(calls)}")
    for c in calls:
        for flag in ("--layers", "--via-size", "--via-drill", "--fab-tier",
                     "--no-stub-layer-swap", "--keepout", "--nets"):
            check(flag in c, f"wave missing {flag}: {c}")
        check(c[c.index("--clearance") + 1] == "0.21",
              "the hole-to-hole-safe clearance did not reach KRT")
    # wave 1 is the analog-guard wave; waves 2-3 use the normal keepout layer
    check(calls[0][calls[0].index("--keepout-layer") + 1] == "User.3",
          "the bridge wave lost its analog-guard keepout layer")
    check(calls[1][calls[1].index("--keepout-layer") + 1] == "User.2",
          "a later wave inherited the analog guard")
    check(calls[2][calls[2].index("--track-width") + 1] == "0.25",
          "the signal wave lost its per-wave track width")
    contains(r.out, "waves done", "route stdout")


@test("KRT waves are CHAINED: each wave routes the previous wave's output")
def t_krt_chaining():
    """Routing every wave from r0 instead of the previous output throws away
    earlier waves — the whole point of hardest-first ordering."""
    d, p = scratch(use_stub)
    must_pass(prep(p), "prep")
    must_pass(run([sys.executable, RS, "route", p]), "route (stub KRT)")
    calls = krt_calls(d / "krt")
    ins = [Path(c[0]).name for c in calls]
    outs = [Path(c[c.index("--output") + 1]).name for c in calls]
    check(ins == ["r0.kicad_pcb", "r1.kicad_pcb", "r2.kicad_pcb"],
          f"waves not chained: inputs were {ins}")
    check(outs == ["r1.kicad_pcb", "r2.kicad_pcb", "r3.kicad_pcb"],
          f"unexpected chain outputs {outs}")


@test("stitch runs the passes in the CONFIGURED order and gates clean")
def t_stitch_order():
    d, p = scratch()
    r = must_pass(stitch(p), "stitch")
    order = [l.strip(" -") for l in r.out.splitlines()
             if l.startswith("-- ") and l.endswith(" --")]
    import yaml
    want = [x for x in yaml.safe_load(p.read_text())["stitch"]["passes"]]
    check(order == want, f"pass order drifted:\n got {order}\nwant {want}")
    contains(r.out, "gate: clean", "stitch verdict")


@test("stitch NEVER changes connectivity: same node set in, same node set out")
def t_stitch_preserves_nodes():
    """The regression this pins: drop_dangling's first cut had no T-junction
    test and deleted segments whose end sat mid-body of another — 8 pads
    went unconnected on a board that had routed 100%."""
    d, p = scratch()
    board = d / "04_kicad" / f"{STEM}.kicad_pcb"
    before = board_nodes(board)
    must_pass(stitch(p), "stitch")
    after = board_nodes(board)
    check(before == after,
          f"stitch changed connectivity: "
          f"{sorted(set(before.items()) ^ set(after.items()))[:10]}")


@test("stitching twice agrees on CONNECTIVITY, not on bytes")
def t_stitch_determinism():
    outs = []
    for _ in (1, 2):
        d, p = scratch()
        must_pass(stitch(p), "stitch")
        outs.append(board_nodes(d / "04_kicad" / f"{STEM}.kicad_pcb"))
    check(outs[0] == outs[1], "two stitch runs produced different connectivity")


@test("a removal pass is followed by a fresh-interpreter barrier")
def t_swig_barrier():
    """board.Remove() poisons the board's SWIG iterators for the rest of the
    interpreter. Without the automatic barrier the NEXT pass raised
    'SwigPyObject is not iterable' and the run saved a half-applied board."""
    def mutate(cfg, d):
        cfg["stitch"]["passes"] = ["drop_micro_fragments", "drop_dangling",
                                   "fill", "gate"]
    d, p = scratch(mutate)
    board = d / "04_kicad" / f"{STEM}.kicad_pcb"
    # a real removal must happen or the barrier is never exercised
    edit_board(board,
               "n=b.FindNet('GND')\n"
               "t=pcbnew.PCB_TRACK(b)\n"
               "t.SetStart(pcbnew.VECTOR2I_MM(30.0,30.0))\n"
               "t.SetEnd(pcbnew.VECTOR2I_MM(30.05,30.0))\n"
               "t.SetWidth(pcbnew.FromMM(0.25))\nt.SetLayer(pcbnew.F_Cu)\n"
               "t.SetNetCode(n.GetNetCode())\nb.Add(t)\n")
    before = board_nodes(board)
    r = must_pass(stitch(p), "stitch with back-to-back removal passes")
    contains(r.out, "removed 1 dangling micro-fragment", "removal did not happen")
    contains(r.out, "SWIG barrier", "barrier did not fire")
    contains(r.out, "gate: clean", "stitch verdict")
    check(before == board_nodes(board),
          "the barrier run changed connectivity")


# ======================================================== KNOWN-BAD =====
@test("route-prep REFUSES a board that still has tracks", kind="known_bad")
def t_kb_tracked_input():
    """KRT re-parses pcbnew tracks wrong and routes straight through them
    (400+ silent crossings, observed twice). The router reports success."""
    d, p = scratch()
    edit_board(d / "04_kicad" / f"{STEM}.kicad_pcb",
               "t=pcbnew.PCB_TRACK(b)\n"
               "t.SetStart(pcbnew.VECTOR2I_MM(30.0,30.0))\n"
               "t.SetEnd(pcbnew.VECTOR2I_MM(32.0,30.0))\n"
               "t.SetWidth(pcbnew.FromMM(0.25))\nt.SetLayer(pcbnew.F_Cu)\n"
               "b.Add(t)\n")
    must_fail(prep(p), "prep on a tracked board", "TRACK-FREE")


@test("route-prep REFUSES to hand KRT a netclass-less project (canon R1)",
      kind="known_bad")
def t_kb_no_netclasses():
    """The fleet audit found EVERY board's route input carrying only
    Default 0.2mm, so ampacity floors were enforced only by the post-route
    DRC — the router never knew about them."""
    d, p = scratch()
    pro = d / "04_kicad" / f"{STEM}.kicad_pro"
    j = json.loads(pro.read_text())
    j["net_settings"] = {"classes": [{"name": "Default"}],
                         "netclass_patterns": []}
    pro.write_text(json.dumps(j))
    must_fail(prep(p), "prep with no netclasses", "canon R1")


@test("a wave naming a net the board does not have is a hard error",
      kind="known_bad")
def t_kb_unknown_wave_net():
    """A typo'd net name silently routes one net fewer; nothing downstream
    compares the wave lists against the board."""
    def mutate(cfg, d):
        cfg["prep"]["waves"]["groups"]["an"] = ["E_PLUS", "S_PLUZ"]
    d, p = scratch(mutate)
    must_fail(prep(p), "prep with a typo'd wave net", "S_PLUZ")


@test("a KRT wave that exits nonzero blocks the chain", kind="known_bad")
def t_kb_krt_nonzero():
    def mutate(cfg, d):
        use_stub(cfg, d, exit_code=3)
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_fail(run([sys.executable, RS, "route", p]), "route with a failing KRT",
              "exited 3")


@test("a KRT wave that exits 0 but writes NO output is caught", kind="known_bad")
def t_kb_krt_lies():
    """'Believing an autorouter's 0 fails without an import + DRC ground
    truth' is in the failure museum. The cheapest version of that lie is a
    router that reports success and produces nothing."""
    def mutate(cfg, d):
        use_stub(cfg, d, write_output=False)
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_fail(run([sys.executable, RS, "route", p]),
              "route with a silent KRT", "produced no")


@test("importing onto a board that ALREADY has tracks is a hard error",
      kind="known_bad")
def t_kb_double_import():
    """Re-importing a KRT output into a tracked board DOUBLES everything
    (holes_co_located x69, 2026-07)."""
    d, p = scratch()
    board = d / "04_kicad" / f"{STEM}.kicad_pcb"
    edit_board(board,
               "t=pcbnew.PCB_TRACK(b)\n"
               "t.SetStart(pcbnew.VECTOR2I_MM(30.0,30.0))\n"
               "t.SetEnd(pcbnew.VECTOR2I_MM(32.0,30.0))\n"
               "t.SetWidth(pcbnew.FromMM(0.25))\nt.SetLayer(pcbnew.F_Cu)\n"
               "b.Add(t)\n")
    chain = d / "06_build" / "route" / "r9.kicad_pcb"
    chain.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(_cached_board(), chain)
    import yaml
    cfg = yaml.safe_load(p.read_text())
    cfg["route"]["final"] = str(chain)
    p.write_text(yaml.safe_dump(cfg))
    must_fail(run([KPY, RS, "import", p]), "import onto a tracked board",
              "DOUBLES")


@test("import REFUSES a chain file that does not exist", kind="known_bad")
def t_kb_missing_chain():
    def mutate(cfg, d):
        cfg["route"]["final"] = "03_src/route/nope.kicad_pcb"
    d, p = scratch(mutate)
    must_fail(run([KPY, RS, "import", p]), "import with no chain file",
              "not found")


@test("an unknown stitch pass name is a hard error, not a skipped pass",
      kind="known_bad")
def t_kb_unknown_pass():
    """Silently ignoring a misspelled pass ships a board that never got
    stitched — and every board-internal gate still passes."""
    def mutate(cfg, d):
        cfg["stitch"]["passes"] = ["dedupe_vias", "stich_grid", "fill", "gate"]
    d, p = scratch(mutate)
    must_fail(stitch(p), "stitch with a misspelled pass", "unknown stitch pass")


@test("a pass list with no `fill` is a hard error", kind="known_bad")
def t_kb_no_fill():
    """An unfilled board's DRC is a lie: the pours that carry GND are not
    there, so unconnected/clearance results mean nothing."""
    def mutate(cfg, d):
        cfg["stitch"]["passes"] = ["dedupe_vias", "stitch_grid", "gate"]
    d, p = scratch(mutate)
    must_fail(stitch(p), "stitch with no fill", "no 'fill'")


@test("an unknown KRT option is a hard error, not a silently dropped flag",
      kind="known_bad")
def t_kb_unknown_krt_flag():
    """Guessing a flag name (or silently dropping one) is how a board gets
    routed at the wrong geometry while the config claims otherwise."""
    def mutate(cfg, d):
        use_stub(cfg, d)
        cfg["route"]["common"]["trackwidth"] = 0.3     # real name: track_width
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_fail(run([sys.executable, RS, "route", p]),
              "route with an unknown option", "unknown KRT option")


@test("the stitch grid MINIMUM bites when the grid comes up short",
      kind="known_bad")
def t_kb_grid_min():
    """A stitch grid that placed almost nothing (every site blocked) is a
    return-path problem, not a warning. Nothing else in the chain notices:
    DRC has no concept of stitch density."""
    def mutate(cfg, d):
        cfg["stitch"]["stitch_grid"]["min"] = 9999
    d, p = scratch(mutate)
    must_fail(stitch(p), "stitch with an unreachable grid minimum",
              "stitch grid too sparse")


@test("pad_rescue `require: all` bites when a plane pad stays unserved",
      kind="known_bad")
def t_kb_pad_rescue_require():
    """Force every via site to be rejected (an inset larger than the board),
    then demand every GND pad be served. The gate must fail rather than ship
    a board whose return path is whatever the pour happens to reach."""
    def mutate(cfg, d):
        cfg["stitch"]["keepin"]["inset"] = 40.0
        cfg["stitch"]["pad_rescue"]["require"] = "all"
        cfg["stitch"]["passes"] = ["pad_rescue", "fill", "gate"]
    d, p = scratch(mutate)
    must_fail(stitch(p), "stitch with an unsatisfiable pad-rescue requirement",
              "pad rescue")


@test("power_stitch bites when a pour-fed net gets too few plane bonds",
      kind="known_bad")
def t_kb_power_stitch_min():
    """A power net whose routed copper never bonds to its plane island is
    fed through a single thin trace. DRC sees a connected net and says
    nothing."""
    def mutate(cfg, d):
        cfg["stitch"]["passes"] = ["power_stitch", "fill", "gate"]
        cfg["stitch"]["power_stitch"] = {"plane_layer": "In2.Cu",
                                         "jobs": [{"net": "5V", "min": 4}]}
    d, p = scratch(mutate)
    must_fail(stitch(p), "stitch with an unmet power-stitch minimum",
              "power stitch 5V")


@test("a failed gate deletes the resume state so a rerun cannot start midway",
      kind="known_bad")
def t_kb_no_stale_resume():
    """The stitcher re-execs across SWIG barriers and remembers where it
    was. If a gate failure left that marker behind, the next run would skip
    every pass before it and 'pass' on a half-stitched board."""
    def mutate(cfg, d):
        # a removal pass FIRST so a barrier actually writes the marker,
        # then a gate that cannot pass
        cfg["stitch"]["passes"] = ["drop_micro_fragments", "stitch_grid",
                                   "fill", "gate"]
        cfg["stitch"]["stitch_grid"]["min"] = 9999
    d, p = scratch(mutate)
    board = d / "04_kicad" / f"{STEM}.kicad_pcb"
    edit_board(board,
               "n=b.FindNet('GND')\n"
               "t=pcbnew.PCB_TRACK(b)\n"
               "t.SetStart(pcbnew.VECTOR2I_MM(30.0,30.0))\n"
               "t.SetEnd(pcbnew.VECTOR2I_MM(30.05,30.0))\n"
               "t.SetWidth(pcbnew.FromMM(0.25))\nt.SetLayer(pcbnew.F_Cu)\n"
               "t.SetNetCode(n.GetNetCode())\nb.Add(t)\n")
    r = must_fail(stitch(p), "gate failure")
    contains(r.out, "SWIG barrier", "no barrier fired, so no marker was written")
    stale = Path(str(board) + ".stitch_state.json")
    check(not stale.is_file(),
          "a failed run left a resume marker — the next run would skip passes")
    contains(r.out, "FAILURES", "gate output")


# ================================= FAB-TIER CAPABILITY FLOORS (Phase A) ==
def declare_tier(d, tier="jlc_4layer_standard"):
    """Give a scratch tree the nets.yaml fab_tier declaration the generic
    backend derives capability floors from."""
    (d / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
    (d / "03_src" / "rules" / "nets.yaml").write_text(f"fab_tier: {tier}\n")


@test("route derives missing via/clearance geometry from the declared fab tier")
def t_tier_derived_route_geometry():
    """The clean-room 3S board declared jlc_4layer_standard but the route
    config's hardcoded 0.6/0.3 examples were copied anyway — nothing derived
    geometry from the tier. With via_size/via_drill/clearance ABSENT, the
    KRT command line must carry the tier's floors (0.45/0.3, min_space)."""
    def mutate(cfg, d):
        use_stub(cfg, d)
        declare_tier(d)
        for k in ("via_size", "via_drill", "clearance"):
            cfg["route"]["common"].pop(k, None)
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_pass(run([sys.executable, RS, "route", p]), "route (stub KRT)")
    for c in krt_calls(d / "krt"):
        eq(c[c.index("--via-size") + 1], "0.45", "tier-derived via size")
        eq(c[c.index("--via-drill") + 1], "0.3", "tier-derived via drill")
        eq(c[c.index("--clearance") + 1], "0.127", "tier-derived clearance")


@test("stitch derives missing via geometry from the declared fab tier")
def t_tier_derived_stitch_geometry():
    """stitch.via with no size/drill must emit vias at the tier's floor, not
    the hardcoded 0.6/0.3 example values."""
    def mutate(cfg, d):
        declare_tier(d, "jlc_2layer_default")     # floors 0.6/0.3
        for k in ("size", "drill"):
            cfg["stitch"]["via"].pop(k, None)
    d, p = scratch(mutate)
    r = must_pass(stitch(p), "stitch with tier-derived via geometry")
    contains(r.out, "gate: clean", "stitch verdict")
    vn = via_nets(d / "04_kicad" / f"{STEM}.kicad_pcb")
    check(sum(vn.values()) > 0, "no stitch vias to measure")
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "bad=[t for t in b.GetTracks() if t.GetClass()=='PCB_VIA'"
            " and (t.GetWidth()<599000 or t.GetDrill()<299000)]\n"
            "print('SUBFLOOR' if bad else 'ALL-AT-FLOOR')\n")
    r = must_pass(run([KPY, "-c", code, d / "04_kicad" / f"{STEM}.kicad_pcb"]),
                  "via geometry scan")
    contains(r.out, "ALL-AT-FLOOR", "a stitch via was emitted below the tier floor")


@test("an explicit route via_drill below the tier floor is a hard error "
      "naming the tier", kind="known_bad")
def t_kb_route_via_below_tier():
    """The clean-room 3S incident (2026-07-20): router-emitted vias below the
    declared tier's drill floor surfaced only as 2 drill_out_of_range DRC
    violations after routing. Pre-fix, the sub-floor value passed straight to
    KRT."""
    def mutate(cfg, d):
        use_stub(cfg, d)
        declare_tier(d)                            # floor 0.45/0.3
        cfg["route"]["common"]["via_drill"] = 0.2
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_fail(run([sys.executable, RS, "route", p]),
              "route with a sub-tier via drill", "jlc_4layer_standard")


@test("an explicit stitch via size below the tier floor is a hard error "
      "naming the tier", kind="known_bad")
def t_kb_stitch_via_below_tier():
    def mutate(cfg, d):
        declare_tier(d)                            # floor 0.45/0.3
        cfg["stitch"]["via"]["size"] = 0.4
    d, p = scratch(mutate)
    must_fail(stitch(p), "stitch with a sub-tier via size",
              "jlc_4layer_standard")


# ================================ NETCLASS-DERIVED WAVE WIDTHS (item 1) ==
def declare_classes(d):
    """A nets.yaml whose classes floor the pwr wave's nets at 0.4mm — the
    SAME file generate_rules_generic emits the .kicad_dru floors from."""
    (d / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
    (d / "03_src" / "rules" / "nets.yaml").write_text(
        "classes:\n"
        "  PWR:\n"
        "    nets: [5V, 3V3]\n"
        "    min_width: 0.4mm\n")


@test("a wave with NO track_width derives it from the member nets' "
      "netclass floor")
def t_wave_width_derived():
    """The v4 usb-hub-3s first DRC carried 157 track_width findings: waves
    routed at widths the netclass .kicad_dru floors reject, because nothing
    derived the KRT width from the class the nets were already declared in.
    With the pwr wave's track_width ABSENT, the KRT command line must carry
    the PWR class floor (0.4); the classless sig wave keeps its explicit
    width untouched."""
    def mutate(cfg, d):
        use_stub(cfg, d)
        declare_classes(d)
        for wv in cfg["route"]["waves"]:
            if wv["name"] == "pwr":
                wv.pop("track_width", None)
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_pass(run([sys.executable, RS, "route", p]), "route (stub KRT)")
    calls = krt_calls(d / "krt")
    eq(calls[1][calls[1].index("--track-width") + 1], "0.4",
       "the pwr wave's derived netclass-floor width")
    eq(calls[2][calls[2].index("--track-width") + 1], "0.25",
       "the classless sig wave's explicit width")


@test("a wave configured BELOW its member nets' class floor fails PREP "
      "naming the class", kind="known_bad")
def t_kb_wave_width_below_class():
    """The silent ride-under: an explicit wave width below a member net's
    netclass floor routes the whole class thin, and every segment becomes a
    track_width DRC finding after the KRT cycle is already spent (the v4
    composition: 157 of 648). Must die at PREP, naming the class.
    RED-verified against the pre-fix router (git stash swap, 2026-07-21):
    the old prep accepts the sub-floor wave and exits 0."""
    def mutate(cfg, d):
        declare_classes(d)
        for wv in cfg["route"]["waves"]:
            if wv["name"] == "pwr":
                wv["track_width"] = 0.2            # PWR floor is 0.4
    d, p = scratch(mutate)
    r = must_fail(prep(p), "prep with a sub-class-floor wave width", "PWR")
    contains(r.out, "min_width 0.4", "the failure must cite the floor")


# ======================================= ROUTE RACE (stochastic router) ==
def stub_krt_race(d):
    """A stub router with per-candidate QUALITY: candidate 1 'routes' by
    connecting two 5V pads on its first wave (via the KiCad interpreter);
    candidate 0 copies input through unchanged. The measurable difference
    quick must see: candidate 1 has strictly fewer routed-net unconnected."""
    k = d / "krt"
    k.mkdir(exist_ok=True)
    (k / "route.py").write_text(
        "import sys, os, shutil, json, pathlib, subprocess\n"
        "a = sys.argv[1:]\n"
        "log = pathlib.Path(__file__).parent / 'calls.jsonl'\n"
        "log.open('a').write(json.dumps(a) + '\\n')\n"
        "out = a[a.index('--output') + 1]\n"
        "shutil.copy(a[0], out)\n"
        "if os.environ.get('ROUTE_RACE_CANDIDATE') == '1' "
        "and out.endswith('r1.kicad_pcb'):\n"
        "    code = ('import pcbnew,sys\\n'\n"
        "            'b=pcbnew.LoadBoard(sys.argv[1])\\n'\n"
        "            'n=b.FindNet(\"5V\")\\n'\n"
        "            'pads=[p for f in b.GetFootprints() for p in f.Pads()'\n"
        "            ' if p.GetNetname()==\"5V\"]\\n'\n"
        "            't=pcbnew.PCB_TRACK(b)\\n'\n"
        "            't.SetStart(pads[0].GetPosition())\\n'\n"
        "            't.SetEnd(pads[1].GetPosition())\\n'\n"
        "            't.SetWidth(pcbnew.FromMM(0.5))\\n'\n"
        "            't.SetLayer(pcbnew.F_Cu)\\n'\n"
        "            't.SetNetCode(n.GetNetCode())\\n'\n"
        "            'b.Add(t)\\nb.Save(sys.argv[1])\\n')\n"
        f"    subprocess.run(['{KPY}', '-c', code, out], check=True)\n"
        "sys.exit(0)\n")
    return k


@test("route --race picks the MEASURABLY better of two stub candidates")
def t_race_picks_better():
    """KRT is stochastic, so N concurrent attempts differ; the race must
    keep the quick-measured best (fewest routed-net unconnected), record
    every candidate's numbers in race_log.json, and point FINAL at the
    winner's chain. Candidate 1's stub connects two 5V pads; candidate 0
    routes nothing — race must choose 1 for a measured reason, not by
    position (0 wins ties, so a tie would expose a broken comparison).
    RED-verified against the pre-race router (git show HEAD swap,
    2026-07-21): --race is an unknown argument there."""
    def mutate(cfg, d):
        cfg["route"]["krt"] = str(stub_krt_race(d))
        cfg["route"]["python"] = sys.executable
        cfg["route"].pop("final", None)
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    r = must_pass(run([sys.executable, RS, "route", p, "--race", "2"]),
                  "route --race 2 (stub KRT)")
    contains(r.out, "race winner: c1", "the measured-better candidate wins")
    log = json.loads(
        (d / "06_build" / "route" / "race_log.json").read_text())
    eq(log["chosen"], 1, "race_log chosen candidate")
    c0, c1 = log["candidates"]["0"], log["candidates"]["1"]
    check(c1["unconnected"] < c0["unconnected"],
          f"candidate 1 must measure strictly better: {c0} vs {c1}")
    final = Path((d / "06_build" / "route" / "FINAL").read_text().strip())
    check("c1" in final.parts[-2], f"FINAL must point into c1: {final}")
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "print('@@', sum(1 for t in b.GetTracks()"
            " if t.GetClass()=='PCB_TRACK'))\n")
    rr = must_pass(run([KPY, "-c", code, final]), "probe winner chain")
    check(int(rr.out.split("@@")[1].strip()) >= 1,
          "the winning chain lost its routed track")


@test("a race where EVERY candidate fails is a hard error, not a silent "
      "promote", kind="known_bad")
def t_kb_race_all_fail():
    """A failing lane is disqualified; all lanes failing must fail route —
    promoting a chain that never routed would ship the r0 board and every
    downstream gate would blame the stitcher."""
    def mutate(cfg, d):
        use_stub(cfg, d, exit_code=3)
    d, p = scratch(mutate)
    must_pass(prep(p), "prep")
    must_fail(run([sys.executable, RS, "route", p, "--race", "2"]),
              "race with all candidates failing", "all 2 race candidates")


# ============================================= QUICK (loop cheapener) ====
def quick_scratch():
    """A scratch tree whose 04_kicad board is a COPY of the sealed
    (routed + stitched, DRC-clean) cook-loadcell board, with its rules
    sidecars — the post-route state `quick` evaluates. Sealed files are
    only ever read."""
    d, p = scratch(with_board=False)
    for ext in (".kicad_pcb", ".kicad_pro", ".kicad_dru"):
        src = LC / "04_kicad" / f"{STEM}{ext}"
        if src.is_file():
            shutil.copy(src, d / "04_kicad" / f"{STEM}{ext}")
    return d, p


def quick(p, d):
    return run([KPY, RS, "quick", p])


@test("quick passes a fully-routed board and reports the split in seconds")
def t_quick_clean():
    d, p = quick_scratch()
    r = must_pass(quick(p, d), "quick on the sealed-equivalent board")
    contains(r.out, "quick verdict: CLEAN", "quick verdict")
    contains(r.out, "0 ratsnest", "unconnected headline")
    j = json.loads((d / "06_build" / "route" / "quick.json").read_text())
    eq(j["verdict"], "CLEAN", "json verdict")
    eq(j["unconnected"]["routed_total"], 0, "routed-net unconnected")
    check(not j["violations"], f"copper violations on a clean board: "
                               f"{j['violations']}")


@test("quick CATCHES a planted unconnected net (routed-net open -> exit 1)",
      kind="known_bad")
def t_kb_quick_unconnected():
    """Delete one routed 5V segment from a clean board: the net opens, and
    quick must fail naming it — this is the signal a routing iteration
    actually needs, at seconds-cost instead of the full rebuild + DRC cycle
    (~8-10 min on the v4 board). GND stays deferred: pours own it.
    RED-verified against the pre-quick router (git show HEAD swap,
    2026-07-21): the subcommand does not exist there and all three quick
    tests fail."""
    d, p = quick_scratch()
    edit_board(d / "04_kicad" / f"{STEM}.kicad_pcb",
               "segs=[t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK'"
               " and t.GetNetname()=='5V']\n"
               "assert segs, 'fixture: no 5V segment to remove'\n"
               "b.Remove(segs[0])\n")
    r = must_fail(quick(p, d), "quick on a board with an opened 5V",
                  "quick verdict: DIRTY")
    contains(r.out, "ROUTED-NET OPEN: 5V", "the opened net must be named")
    j = json.loads((d / "06_build" / "route" / "quick.json").read_text())
    check(j["unconnected"]["routed"].get("5V", 0) >= 1,
          f"5V missing from the routed-net split: {j['unconnected']}")


@test("quick CATCHES a planted sub-floor track (track_width -> exit 1)",
      kind="known_bad")
def t_kb_quick_subfloor_track():
    """A 0.1mm segment on 5V, whose netclass .kicad_dru floor is 0.4mm. The
    board's rules ride along (canon R1), so quick sees the same floor the
    full gate enforces — a wave that rode under its class is caught in
    seconds, not at the end of the chain."""
    d, p = quick_scratch()
    edit_board(d / "04_kicad" / f"{STEM}.kicad_pcb",
               "n=b.FindNet('5V')\n"
               "segs=[t for t in b.GetTracks() if t.GetClass()=='PCB_TRACK'"
               " and t.GetNetname()=='5V']\n"
               "e=segs[0].GetEnd()\n"
               "t=pcbnew.PCB_TRACK(b)\n"
               "t.SetStart(e)\n"
               "t.SetEnd(pcbnew.VECTOR2I(e.x+pcbnew.FromMM(1.5),e.y))\n"
               "t.SetWidth(pcbnew.FromMM(0.1))\n"
               "t.SetLayer(segs[0].GetLayer())\n"
               "t.SetNetCode(n.GetNetCode())\nb.Add(t)\n")
    r = must_fail(quick(p, d), "quick on a board with a sub-floor track",
                  "track_width")
    j = json.loads((d / "06_build" / "route" / "quick.json").read_text())
    check(j["violations"].get("track_width", {}).get("count", 0) >= 1,
          f"track_width missing from the quick report: {j['violations']}")


# ================================================== TAPS (canon M8) ======
# A tiny 2-layer board: two SIG pads 20mm apart, plus optional other-net
# blocking strips so strategy 1 (same-layer join) can be forced to fail and
# strategy 2 (via hop) or the whole tap can be forced to fail. Hermetic —
# every emitted segment/via is toolkit-collision-checked, so the assertions
# are net/via-count PROPERTIES.
_MK_TAP = r'''
import pcbnew, sys, json
out = sys.argv[1]; blockers = json.loads(sys.argv[2])
BX, BY = 30.0, 15.0
b = pcbnew.BOARD()
for (x1,y1),(x2,y2) in [((0,0),(BX,0)),((BX,0),(BX,BY)),((BX,BY),(0,BY)),((0,BY),(0,0))]:
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I_MM(x1,y1)); s.SetEnd(pcbnew.VECTOR2I_MM(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
def mknet(n): x=pcbnew.NETINFO_ITEM(b,n); b.Add(x); return x
nets={"SIG":mknet("SIG"), "GND":mknet("GND")}
for i,(x,y) in enumerate([(5.0,7.5),(25.0,7.5)],1):
    fp=pcbnew.FOOTPRINT(b); fp.SetReference("U%d"%i)
    fp.SetPosition(pcbnew.VECTOR2I_MM(x,y))
    p=pcbnew.PAD(fp); p.SetShape(pcbnew.PAD_SHAPE_RECT)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetSize(pcbnew.VECTOR2I_MM(1.0,1.0)); p.SetLayerSet(pcbnew.PAD.SMDMask())
    p.SetPosition(pcbnew.VECTOR2I_MM(x,y)); p.SetNumber("1"); p.SetNet(nets["SIG"])
    fp.Add(p); b.Add(fp)
for blk in blockers:
    t=pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I_MM(blk["x1"],blk["y1"]))
    t.SetEnd(pcbnew.VECTOR2I_MM(blk["x2"],blk["y2"]))
    t.SetWidth(pcbnew.FromMM(blk.get("w",1.0)))
    t.SetLayer(getattr(pcbnew, blk.get("layer","F.Cu").replace(".","_")))
    t.SetNetCode(nets["GND"].GetNetCode())
    b.Add(t)
b.Save(out)
'''


def tap_scratch(blockers, connections, tap_via=None):
    """A scratch project whose route.yaml has ONLY project + taps."""
    import yaml
    d = tmpdir("t2_tap_")
    (d / "03_src").mkdir()
    (d / "04_kicad").mkdir()
    board = d / "04_kicad" / "tap.kicad_pcb"
    must_pass(run([KPY, "-c", _MK_TAP, board, json.dumps(blockers)]),
              "build tap board")
    taps = {"clearance": 0.15, "connections": connections}
    if tap_via:
        taps["via"] = tap_via
    cfg = {"project": {"name": "tap", "board": "04_kicad/tap.kicad_pcb"},
           "taps": taps}
    p = d / "03_src" / "route.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p, board


def taps_cmd(p):
    return run([KPY, RS, "taps", p])


# F.Cu wall spanning the whole board height at x=15 — every same-layer
# join candidate between x=5 and x=25 must cross it
_WALL_F = {"x1": 15.0, "y1": -1.0, "x2": 15.0, "y2": 16.0, "w": 1.0,
           "layer": "F.Cu"}
_WALL_B = dict(_WALL_F, layer="B.Cu")


@test("a clear tap routes on the pad layer with NO vias (strategy 1)")
def t_tap_direct():
    d, p, board = tap_scratch([], [{"net": "SIG", "from": "U1.1",
                                    "to": "U2.1", "width": 0.3}])
    r = must_pass(taps_cmd(p), "taps (clear board)")
    contains(r.out, "OK joinpath", "strategy 1 verdict")
    eq(via_nets(board).get("SIG", 0), 0, "a direct tap must not spend vias")
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "n=sum(1 for t in b.GetTracks() if t.GetClass()=='PCB_TRACK'"
            " and t.GetNetname()=='SIG')\nprint('SEGS',n)\n")
    r = must_pass(run([KPY, "-c", code, board]), "count tap segments")
    check("SEGS 0" not in r.out, "no tap copper was emitted")


@test("a blocked tap hops through vias to the hop layer (strategy 2)")
def t_tap_via_hop():
    """An other-net F.Cu wall blocks every same-layer candidate; the tap must
    escape by stub -> via -> B.Cu join -> via, all collision-checked — the
    clean-room 3S route_taps.py 'via_b' move, now config."""
    d, p, board = tap_scratch([_WALL_F], [{"net": "SIG", "from": "U1.1",
                                           "to": "U2.1", "width": 0.3}])
    r = must_pass(taps_cmd(p), "taps (F.Cu wall)")
    contains(r.out, "OK via_hop", "strategy 2 verdict")
    eq(via_nets(board).get("SIG", 0), 2, "a via hop is exactly two vias")


@test("a tap that CANNOT be routed is a hard error, not a silent skip",
      kind="known_bad")
def t_kb_tap_unroutable():
    """Walls on BOTH layers: no join exists. Pre-promotion, a failed bespoke
    tap script printed FAIL and the open only resurfaced as a DRC unconnected
    item after fill; the generic step must refuse to save."""
    d, p, board = tap_scratch([_WALL_F, _WALL_B],
                              [{"net": "SIG", "from": "U1.1", "to": "U2.1",
                                "width": 0.3}])
    must_fail(taps_cmd(p), "taps with both layers walled", "unrouted taps")


@test("a tap endpoint naming a missing pad / wrong net is a hard error",
      kind="known_bad")
def t_kb_tap_bad_endpoint():
    d, p, board = tap_scratch([], [{"net": "SIG", "from": "U9.1",
                                    "to": "U2.1", "width": 0.3}])
    must_fail(taps_cmd(p), "tap from a missing footprint", "no footprint")
    # wrong-net pad: U2.1 is SIG, the tap says GND — must never bridge.
    # (the corner stub keeps the padless GND net from being pruned on save)
    d, p, board = tap_scratch([{"x1": 1.0, "y1": 1.0, "x2": 2.0, "y2": 1.0,
                                "w": 0.3, "layer": "B.Cu"}],
                              [{"net": "GND", "from": "U1.1",
                                "to": "U2.1", "width": 0.3}])
    must_fail(taps_cmd(p), "tap onto a pad of another net", "never bridge")


@test("taps.via below the declared tier floor is a hard error naming the "
      "tier", kind="known_bad")
def t_kb_tap_via_below_tier():
    d, p, board = tap_scratch([_WALL_F],
                              [{"net": "SIG", "from": "U1.1", "to": "U2.1",
                                "width": 0.3}],
                              tap_via={"size": 0.3, "drill": 0.2})
    declare_tier(d)                                # floor 0.45/0.3
    must_fail(taps_cmd(p), "taps with a sub-tier via", "jlc_4layer_standard")


# ============================ 4-LAYER PLANE FIXTURES (GAP A / GAP B) =====
# cook-loadcell is 2-layer, so the plane machinery (per-pad rescue to an inner
# solid plane, plane-drop stub floors) was never exercised in T2. These build a
# tiny synthetic 4-layer board (In1=GND solid plane, In2=VIN power plane) with
# unbonded SMD pads — the clean-room 3S power board's exact shape. Assertions
# are DRC counts + via-per-net: PROPERTIES, not bytes.
_MK_4L = r'''
import pcbnew, sys, json
out = sys.argv[1]; cfg = json.loads(sys.argv[2])
BX, BY = 30.0, 20.0
b = pcbnew.BOARD(); b.SetCopperLayerCount(4)
for (x1,y1),(x2,y2) in [((0,0),(BX,0)),((BX,0),(BX,BY)),((BX,BY),(0,BY)),((0,BY),(0,0))]:
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I_MM(x1,y1)); s.SetEnd(pcbnew.VECTOR2I_MM(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
def mknet(n): x=pcbnew.NETINFO_ITEM(b,n); b.Add(x); return x
nets={"GND":mknet("GND"), "VIN":mknet("VIN")}
def plane(net, layer):
    z=pcbnew.ZONE(b); z.SetNet(net)
    ls=pcbnew.LSET(); (getattr(ls,"AddLayer",None) or getattr(ls,"addLayer"))(layer)
    z.SetLayer(layer); z.SetLayerSet(ls); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.Outline().NewOutline()
    for x,y in [(0.3,0.3),(BX-0.3,0.3),(BX-0.3,BY-0.3),(0.3,BY-0.3)]:
        z.Outline().Append(pcbnew.VECTOR2I_MM(x,y))
    b.Add(z)
plane(nets["GND"], pcbnew.In1_Cu); plane(nets["VIN"], pcbnew.In2_Cu)
n=0
for netname, pads in cfg.items():
    for entry in pads:
        x, y = float(entry[0]), float(entry[1])
        thermal = len(entry) > 2 and entry[2] == "thermal"
        n+=1; fp=pcbnew.FOOTPRINT(b); fp.SetReference("U%d"%n)
        fp.SetPosition(pcbnew.VECTOR2I_MM(x,y))
        p=pcbnew.PAD(fp); p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetSize(pcbnew.VECTOR2I_MM(1.2,1.2)); p.SetLayerSet(pcbnew.PAD.SMDMask())
        p.SetPosition(pcbnew.VECTOR2I_MM(x,y)); p.SetNumber("1"); p.SetNet(nets[netname])
        fp.Add(p); b.Add(fp)
        if thermal:
            # a footprint-native thermal via grid INSIDE the SMD pad outline
            # (the 3S clean-room HTSSOP-20 EP shape, scaled down)
            for k, dx in enumerate((-0.3, 0.3)):
                q=pcbnew.PAD(fp); q.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
                q.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
                q.SetSize(pcbnew.VECTOR2I_MM(0.6,0.6))
                q.SetDrillSize(pcbnew.VECTOR2I_MM(0.3,0.3))
                q.SetLayerSet(pcbnew.PAD.PTHMask())
                q.SetPosition(pcbnew.VECTOR2I_MM(x+dx,y))
                q.SetNumber("%d"%(100+k)); q.SetNet(nets[netname])
                fp.Add(q)
b.Save(out)
'''


def four_layer_scratch(pads, pad_rescue, passes=("pad_rescue", "fill", "gate"),
                       dru_floor=3.7, keepin_inset=0.5):
    """A scratch project: a 4-layer synthetic board + a route.yaml whose stitch
    runs `pad_rescue`. `pads` is {net: [[x,y],...]}. The .kicad_dru carries a
    3.7mm VIN trunk floor (the ampacity floor a plane-drop stub violates)."""
    import yaml
    d = tmpdir("t2_4l_")
    (d / "03_src").mkdir(); (d / "04_kicad").mkdir(); (d / "06_build").mkdir()
    board = d / "04_kicad" / "syn4.kicad_pcb"
    must_pass(run([KPY, "-c", _MK_4L, board, json.dumps(pads)]), "build 4L board")
    (d / "04_kicad" / "syn4.kicad_dru").write_text(
        "(version 1)\n(rule width_vin\n  (condition \"A.NetName == 'VIN'\")\n"
        f"  (constraint track_width (min {dru_floor}mm)))\n")
    cfg = {"project": {"name": "syn4", "board": "04_kicad/syn4.kicad_pcb",
                       "build_dir": "06_build"},
           "stitch": {"clearance": 0.15,
                      "via": {"size": 0.6, "drill": 0.3, "spacing": 0.62},
                      "keepin": {"inset": keepin_inset}, "passes": list(passes),
                      "pad_rescue": pad_rescue}}
    p = d / "03_src" / "route.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p, board


def drc_counts(board):
    """kicad-cli DRC -> {track_width, unconnected, isolated}. Reads the
    <stem>.kicad_dru beside the board (the trunk floor + any scoped sub-floor
    pad_rescue appended)."""
    from collections import Counter
    outj = Path(board).parent / "drc.json"
    run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
         "--format", "json", "-o", str(outj), str(board)])
    g = json.loads(outj.read_text())
    c = Counter(v["type"] for v in g["violations"])
    return {"track_width": c.get("track_width", 0),
            "unconnected": len(g["unconnected_items"]),
            "isolated": c.get("isolated_copper", 0)}


def via_nets(board):
    """netname -> via count on the board."""
    code = ("import pcbnew,sys,json\nb=pcbnew.LoadBoard(sys.argv[1])\no={}\n"
            "for t in b.GetTracks():\n"
            "  if t.GetClass()=='PCB_VIA':\n"
            "    n=t.GetNetname(); o[n]=o.get(n,0)+1\n"
            "print('@@'+json.dumps(o))\n")
    r = must_pass(run([KPY, "-c", code, str(board)]), "via_nets")
    return json.loads(r.out.split("@@", 1)[1].strip())


@test("pad_rescue via-bonds EVERY configured plane net (GAP A: two inner planes)")
def t_pad_rescue_multiplane():
    """A 4-layer board with In1=GND and In2=VIN needs BOTH plane-nets rescued
    per-pad. The single-net stitcher served one and left the other's pads to
    fall through to stitch_grid — a chunk of the clean-room 3S board's 52
    unconnected. Property: both planes' pads end up via-bonded, DRC 0
    unconnected. (RED against pre-fix: VIN gets 0 rescue vias.)"""
    d, p, board = four_layer_scratch(
        {"GND": [[7, 15], [23, 15]], "VIN": [[7, 10], [23, 10]]},
        {"nets": [{"net": "GND", "layer": "In1.Cu"},
                  {"net": "VIN", "layer": "In2.Cu"}],
         "via_in_pad": False, "stub_width": 0.3})
    must_pass(stitch(p), "multi-plane pad rescue")
    vn = via_nets(board)
    check(vn.get("GND", 0) >= 2 and vn.get("VIN", 0) >= 2,
          f"a plane net got no rescue vias (single-net stitcher): {vn}")
    counts = drc_counts(board)
    check(counts["unconnected"] == 0,
          f"multi-plane rescue left {counts['unconnected']} unconnected: {counts}")


# ======================================================== KNOWN-BAD =====
@test("pad_rescue require:all bites when a SECOND plane's pad stays unserved",
      kind="known_bad")
def t_kb_pad_rescue_second_plane():
    """require:all must fail if ANY configured plane net is unserved, not only
    the first. The board has one VIN pad and no GND pads to rescue, at a site
    where no via fits (huge keepin inset): GND rescues 0/0 cleanly, VIN cannot
    be served. The single-net stitcher only ever looked at GND, so it shipped a
    board with an unconnected VIN pad and a green gate (clean-room 3S, 2026)."""
    d, p, board = four_layer_scratch(
        {"VIN": [[15, 10]]},
        {"nets": [{"net": "GND", "layer": "In1.Cu"},
                  {"net": "VIN", "layer": "In2.Cu"}],
         "require": "all", "via_in_pad": False},
        keepin_inset=40.0)
    must_fail(stitch(p), "require:all with an unserved second plane",
              "VIN pad rescue")


@test("pad_rescue SCOPES the plane-drop stub out of the trunk ampacity floor",
      kind="known_bad")
def t_kb_stub_floor_scoped():
    """A VIN rescue drops a ~0.3mm stub on a net whose trunk floor is 3.7mm;
    DRC flags it as track_width (33 such on the clean-room 3S board). The stub
    is a via drop, not a trunk, so pad_rescue emits a named rule area with a
    relaxed sub-floor (KiCad last-match precedence, the cook-hub u7_taps
    pattern). Proven both ways: scope OFF, the trunk floor STILL bites the
    stub; scope ON, the stub is legal. (RED against pre-fix: no rule area, so
    the stub stays a violation.)"""
    base = {"net": "VIN", "via_in_pad": False, "stub_width": 0.3}
    # teeth: the unscoped stub genuinely violates the 3.7mm floor
    d, p, board = four_layer_scratch({"VIN": [[7, 10], [23, 10]]},
                                     dict(base, stub_scope=False))
    must_pass(stitch(p), "stitch (scope off)")
    off = drc_counts(board)
    check(off["track_width"] >= 2,
          f"the 3.7mm trunk floor did not bite the plane-drop stub: {off}")
    # fix: the rule area exempts exactly the stub, floor untouched elsewhere
    d, p, board = four_layer_scratch({"VIN": [[7, 10], [23, 10]]}, base)
    must_pass(stitch(p), "stitch (scope on)")
    on = drc_counts(board)
    check(on["track_width"] == 0,
          f"the plane-drop stub was NOT scoped out of the floor: "
          f"{on['track_width']} track_width violation(s)")


@test("pad_rescue SKIPS a pad already served by its footprint's own thermal "
      "via grid (zero rescue vias)")
def t_pad_rescue_thermal_grid_skip():
    """Footprints with built-in thermal via grids carry same-net PTH pads
    inside the SMD pad outline; their barrels already bond the pad to the
    plane. Pre-fix, pad_rescue's has_via() only saw TRACK vias, so it dropped
    its own via on/next to the grid — the stacked drills the 3S clean-room
    run's cleanup_vias.py part 1 existed to delete post-hoc (hole_to_hole).
    Property: the grid-served pad gains ZERO rescue vias and still verifies
    connected. RED-VERIFIED against the pre-fix stitcher (git stash swap,
    2026-07-21): the old code emits 1 GND rescue via and this test fails."""
    d, p, board = four_layer_scratch(
        {"GND": [[7, 15, "thermal"]]},
        {"nets": [{"net": "GND", "layer": "In1.Cu"}],
         "via_in_pad": True, "require": "all"})
    must_pass(stitch(p), "pad rescue over a thermal grid")
    eq(via_nets(board).get("GND", 0), 0,
       "a grid-served pad must gain ZERO rescue vias")
    counts = drc_counts(board)
    eq(counts["unconnected"], 0, "the grid must genuinely serve the pad")


# ================================== DANGLING STITCH-VIA PRUNING (item 9) ==
# A 2-layer synthetic board whose GND pour exists on ONE or BOTH layers: a
# stitch via over a single-layer pour connects on one layer only — the DRC
# `via_dangling` class. via_janitor credits the zone OUTLINE, so only a
# filled-poly test catches it (the 3S cleanup_vias.py stray-via deletions).
_MK_POUR = r'''
import pcbnew, sys, json
out = sys.argv[1]; layers = json.loads(sys.argv[2])
BX, BY = 30.0, 20.0
b = pcbnew.BOARD()
for (x1,y1),(x2,y2) in [((0,0),(BX,0)),((BX,0),(BX,BY)),((BX,BY),(0,BY)),((0,BY),(0,0))]:
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I_MM(x1,y1)); s.SetEnd(pcbnew.VECTOR2I_MM(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
gnd=pcbnew.NETINFO_ITEM(b,"GND"); b.Add(gnd)
fp=pcbnew.FOOTPRINT(b); fp.SetReference("U1")
fp.SetPosition(pcbnew.VECTOR2I_MM(4.0,10.0))
p=pcbnew.PAD(fp); p.SetShape(pcbnew.PAD_SHAPE_RECT)
p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
p.SetSize(pcbnew.VECTOR2I_MM(1.2,1.2)); p.SetLayerSet(pcbnew.PAD.SMDMask())
p.SetPosition(pcbnew.VECTOR2I_MM(4.0,10.0)); p.SetNumber("1"); p.SetNet(gnd)
fp.Add(p); b.Add(fp)
for lname in layers:
    lay=getattr(pcbnew, lname.replace(".","_"))
    z=pcbnew.ZONE(b); z.SetNet(gnd)
    ls=pcbnew.LSET(); (getattr(ls,"AddLayer",None) or getattr(ls,"addLayer"))(lay)
    z.SetLayer(lay); z.SetLayerSet(ls)
    z.Outline().NewOutline()
    for x,y in [(0.3,0.3),(BX-0.3,0.3),(BX-0.3,BY-0.3),(0.3,BY-0.3)]:
        z.Outline().Append(pcbnew.VECTOR2I_MM(x,y))
    b.Add(z)
b.Save(out)
'''


def pour_scratch(layers, passes):
    import yaml
    d = tmpdir("t2_pour_")
    (d / "03_src").mkdir()
    (d / "04_kicad").mkdir()
    (d / "06_build").mkdir()
    board = d / "04_kicad" / "pour.kicad_pcb"
    must_pass(run([KPY, "-c", _MK_POUR, board, json.dumps(layers)]),
              "build pour board")
    cfg = {"project": {"name": "pour", "board": "04_kicad/pour.kicad_pcb",
                       "build_dir": "06_build"},
           "stitch": {"clearance": 0.15,
                      "via": {"size": 0.6, "drill": 0.3, "spacing": 0.62},
                      "keepin": {"inset": 0.8}, "passes": list(passes),
                      "stitch_grid": {"net": "GND", "x": [8, 28, 5],
                                      "y": [5, 18, 5]}}}
    p = d / "03_src" / "route.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p, board


_PRUNE_PASSES = ("stitch_grid", "fill", "prune_stitch_dangling", "gate")


@test("prune_stitch_dangling keeps vias that bond two filled pours (control)")
def t_prune_keeps_bonded():
    d, p, board = pour_scratch(["F.Cu", "B.Cu"], _PRUNE_PASSES)
    r = must_pass(stitch(p), "stitch on a two-pour board")
    contains(r.out, "pruned 0 dangling", "nothing should be pruned")
    check(via_nets(board).get("GND", 0) > 0, "grid placed no vias to keep")


@test("prune_stitch_dangling removes ONLY the stitcher's own single-layer "
      "vias, never an imported one")
def t_prune_scope():
    """GND pour on F.Cu only: every grid via connects on one layer (the
    via_dangling DRC class — janitor's OUTLINE credit passes it, the filled
    polys do not). All stitch-emitted vias must go; a pre-existing
    'imported' via at the same kind of site — equally dangling — must
    SURVIVE, because imported-route/footprint vias are design intent.
    RED-VERIFIED against the pre-fix stitcher (git stash swap, 2026-07-21):
    the pass does not exist there and the config errors out."""
    d, p, board = pour_scratch(["F.Cu"], _PRUNE_PASSES)
    edit_board(board,
               "n=b.FindNet('GND')\n"
               "v=pcbnew.PCB_VIA(b)\n"
               "v.SetPosition(pcbnew.VECTOR2I_MM(26.0,16.0))\n"
               "v.SetWidth(pcbnew.FromMM(0.6))\nv.SetDrill(pcbnew.FromMM(0.3))\n"
               "v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)\n"
               "v.SetNetCode(n.GetNetCode())\nb.Add(v)\n")
    r = must_pass(stitch(p), "stitch on a one-pour board")
    check("pruned 0 dangling" not in r.out,
          "the single-layer grid vias were not pruned")
    eq(via_nets(board).get("GND", 0), 1,
       "exactly the imported via must survive")


@test("prune_stitch_dangling REFUSES to run before fill", kind="known_bad")
def t_kb_prune_before_fill():
    """On an unfilled board every stitch via looks dangling — running the
    pruner there would eat the whole grid and the board would still gate
    clean."""
    d, p, board = pour_scratch(["F.Cu", "B.Cu"],
                               ("stitch_grid", "prune_stitch_dangling",
                                "fill", "gate"))
    must_fail(stitch(p), "prune before fill", "AFTER `fill`")


# ============================= POUR-ISLAND AUTO-HEAL (heal_islands) ======
# The v4 usb-hub-3s clean-room canary's tail: 4 of its last 7 gate findings
# were same-net zone splits (unconnected_items "Zone [X] <-> Zone [X]" on
# LX1/LX2/VIN_S/VBUSA3 — priority-2 F.Cu pours sliced by escape tracks,
# 2026-07-21), each bridged BY HAND by an expensive agent. These fixtures
# reproduce the class on a tiny synthetic board: a dumbbell PWR pour on
# F.Cu whose neck is cut by a foreign SIG track, so the fill produces two
# islands. Modes:
#   short_slice — the SIG wall covers only the neck: a same-layer track
#                 bridge exists AROUND it (the next-narrowest-gap search)
#   full_slice  — the SIG wall spans the whole board: every same-layer
#                 path collides; only a via through a B.Cu plane can heal
#   bplane      — adds a whole-board PWR plane on B.Cu (the shared plane)
#   two_nets    — two adjacent single-island zones of DIFFERENT nets and
#                 no split at all: the healer must emit NOTHING
_MK_SPLIT = r'''
import pcbnew, sys, json
out = sys.argv[1]; cfg = json.loads(sys.argv[2])
BX, BY = 30.0, 20.0
b = pcbnew.BOARD()
for (x1,y1),(x2,y2) in [((0,0),(BX,0)),((BX,0),(BX,BY)),((BX,BY),(0,BY)),((0,BY),(0,0))]:
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I_MM(x1,y1)); s.SetEnd(pcbnew.VECTOR2I_MM(x2,y2))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
def mknet(n): x=pcbnew.NETINFO_ITEM(b,n); b.Add(x); return x
nets={"PWR":mknet("PWR"), "SIG":mknet("SIG")}
def zone(net, layer, pts):
    z=pcbnew.ZONE(b); z.SetNet(net)
    ls=pcbnew.LSET(); (getattr(ls,"AddLayer",None) or getattr(ls,"addLayer"))(layer)
    z.SetLayer(layer); z.SetLayerSet(ls)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.Outline().NewOutline()
    for x,y in pts: z.Outline().Append(pcbnew.VECTOR2I_MM(float(x),float(y)))
    b.Add(z)
def pad(ref, net, x, y):
    fp=pcbnew.FOOTPRINT(b); fp.SetReference(ref)
    fp.SetPosition(pcbnew.VECTOR2I_MM(x,y))
    p=pcbnew.PAD(fp); p.SetShape(pcbnew.PAD_SHAPE_RECT)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetSize(pcbnew.VECTOR2I_MM(1.2,1.2)); p.SetLayerSet(pcbnew.PAD.SMDMask())
    p.SetPosition(pcbnew.VECTOR2I_MM(x,y)); p.SetNumber("1"); p.SetNet(nets[net])
    fp.Add(p); b.Add(fp)
mode = cfg["mode"]
if mode == "two_nets":
    zone(nets["PWR"], pcbnew.F_Cu, [(1,2),(13,2),(13,18),(1,18)])
    zone(nets["SIG"], pcbnew.F_Cu, [(17,2),(29,2),(29,18),(17,18)])
    pad("U1","PWR",7.0,10.0); pad("U2","SIG",23.0,10.0)
else:
    # dumbbell PWR pour: two lobes joined by a neck (y 8..12)
    zone(nets["PWR"], pcbnew.F_Cu,
         [(1,2),(13,2),(13,8),(17,8),(17,2),(29,2),(29,18),(17,18),
          (17,12),(13,12),(13,18),(1,18)])
    y0, y1 = (7.0, 13.0) if mode == "short_slice" else (0.5, 19.5)
    t=pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I_MM(15.0,y0)); t.SetEnd(pcbnew.VECTOR2I_MM(15.0,y1))
    t.SetWidth(pcbnew.FromMM(0.4)); t.SetLayer(pcbnew.F_Cu)
    t.SetNet(nets["SIG"]); b.Add(t)
    pad("U1","PWR",7.0,10.0); pad("U2","PWR",23.0,10.0)
    if cfg.get("bplane"):
        zone(nets["PWR"], pcbnew.B_Cu,
             [(0.3,0.3),(BX-0.3,0.3),(BX-0.3,BY-0.3),(0.3,BY-0.3)])
b.Save(out)
'''


def heal_scratch(mode, bplane=False, passes=("fill", "heal_islands", "gate"),
                 pwr_class_width=0.5):
    """A scratch project whose stitch runs `heal_islands` on the synthetic
    split-pour board. rules/nets.yaml declares a PWR netclass floor so the
    bridge width is measurable (the pass must use the net-class width)."""
    import yaml
    d = tmpdir("t2_heal_")
    (d / "03_src").mkdir()
    (d / "04_kicad").mkdir()
    (d / "06_build").mkdir()
    board = d / "04_kicad" / "split.kicad_pcb"
    must_pass(run([KPY, "-c", _MK_SPLIT, board,
                   json.dumps({"mode": mode, "bplane": bplane})]),
              "build split-pour board")
    if pwr_class_width:
        (d / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
        (d / "03_src" / "rules" / "nets.yaml").write_text(
            "classes:\n  PWR:\n    nets: [PWR]\n"
            f"    min_width: {pwr_class_width}mm\n")
    cfg = {"project": {"name": "split", "board": "04_kicad/split.kicad_pcb",
                       "build_dir": "06_build"},
           "stitch": {"clearance": 0.15,
                      "via": {"size": 0.6, "drill": 0.3, "spacing": 0.62},
                      "keepin": {"inset": 0.8}, "passes": list(passes),
                      "heal_islands": {"min_bbox": 0.8}}}
    p = d / "03_src" / "route.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p, board


def copper_counts(board):
    """(PCB_TRACK count by net, via count by net) — the healer's entire
    observable output is new copper, so these are the no-op meters."""
    code = ("import pcbnew,sys,json\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "t={};v={}\n"
            "for x in b.GetTracks():\n"
            "  d = v if x.GetClass()=='PCB_VIA' else t\n"
            "  n=x.GetNetname(); d[n]=d.get(n,0)+1\n"
            "print('@@'+json.dumps([t,v]))\n")
    r = must_pass(run([KPY, "-c", code, str(board)]), "copper_counts")
    t, v = json.loads(r.out.split("@@", 1)[1].strip())
    return t, v


def bridge_widths(board, net):
    code = ("import pcbnew,sys,json\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "w=[t.GetWidth()/1e6 for t in b.GetTracks()"
            " if t.GetClass()=='PCB_TRACK' and t.GetNetname()==sys.argv[2]]\n"
            "print('@@'+json.dumps(w))\n")
    r = must_pass(run([KPY, "-c", code, str(board), net]), "bridge_widths")
    return json.loads(r.out.split("@@", 1)[1].strip())


@test("heal_islands bridges a split same-net pour: 2 island groups -> 1, "
      "connectivity restored, bridge at the net-class width")
def t_heal_same_layer():
    """The v4 tail class (LX1/LX2/VIN_S/VBUSA3, 2026-07-21) made mechanical:
    a foreign track cuts the pour's neck, the narrowest gaps are all blocked
    by that track, and the healer walks to the NEXT-narrowest gap that is
    collision-clear and bridges there — with a track at the PWR net-class
    width (0.5mm from rules/nets.yaml), never a guessed width. The DRC
    re-check is kicad-cli (a different method than the healer's own
    grouping, canon M1)."""
    d, p, board = heal_scratch("short_slice")
    r = must_pass(stitch(p), "stitch with heal_islands")
    contains(r.out, "heal PWR: track bridge", "the same-layer strategy")
    contains(r.out, "PWR (2->1)", "island group count 2 -> 1")
    ws = bridge_widths(board, "PWR")
    check(len(ws) >= 1, "no bridge track was emitted")
    check(all(abs(w - 0.5) < 1e-6 for w in ws),
          f"bridge not at the PWR net-class width 0.5: {ws}")
    eq(via_nets(board).get("PWR", 0), 0,
       "a same-layer heal must not spend vias")
    counts = drc_counts(board)
    eq(counts["unconnected"], 0,
       f"DRC still sees the split after healing: {counts}")


@test("heal_islands falls back to a via through a shared plane when every "
      "same-layer gap is blocked")
def t_heal_via_plane():
    """The full-height slice leaves NO collision-clear same-layer path, so
    the healer must hop: a via inside each F.Cu island where the whole-board
    B.Cu PWR plane overlaps it (two group merges through the plane = the
    via pair). Every via goes through try_via/via_site_ok."""
    d, p, board = heal_scratch("full_slice", bplane=True)
    r = must_pass(stitch(p), "stitch with heal_islands (walled)")
    contains(r.out, "plane via", "the via strategy verdict")
    check(via_nets(board).get("PWR", 0) >= 2,
          f"expected a via pair, got {via_nets(board)}")
    counts = drc_counts(board)
    eq(counts["unconnected"], 0,
       f"DRC still sees the split after via healing: {counts}")


@test("heal_islands NEVER bridges zones of different nets (no-op on two "
      "adjacent single-island pours)")
def t_heal_no_cross_net():
    """Safety rail (a). Two closest-proximity zones of DIFFERENT nets, no
    split anywhere: the healer must emit NOTHING — a net-blind 'nearest
    island' heal would short PWR to SIG here. RED-VERIFIED 2026-07-21 by
    disabling the net guard (grouping collapsed to one pseudo-net + the
    emit-path netcode die removed): the broken healer emitted 'heal PWR:
    track bridge' INTO the SIG zone and this test failed (the run also
    died at the re-verify, because a cross-net bridge cannot merge the
    per-net groups — defense in depth observed working); guard restored,
    test green."""
    d, p, board = heal_scratch("two_nets")
    r = must_pass(stitch(p), "stitch on two different-net pours")
    contains(r.out, "nothing to heal", "the healer must be a no-op")
    t, v = copper_counts(board)
    check(not t and not v,
          f"the healer emitted copper on a board with no same-net split: "
          f"tracks={t} vias={v}")


@test("heal_islands is IDEMPOTENT: a second run on a healed board emits "
      "nothing")
def t_heal_idempotent():
    """Safety rail (c). After heal + refill the bridge track seats both
    islands in one connectivity group, so a rerun must find nothing to do.
    RED-VERIFIED 2026-07-21 by breaking the island-seating step (the
    union(island, item) call removed): detection then re-reports the healed
    pour as split forever, the run fails its own did-not-reduce check, and
    this test caught it on the FIRST stitch exiting nonzero (a healer that
    silently re-emitted instead would fail the copper-count comparison
    below)."""
    d, p, board = heal_scratch("short_slice")
    must_pass(stitch(p), "first heal")
    t1, v1 = copper_counts(board)
    r = must_pass(stitch(p), "second run on the healed board")
    contains(r.out, "nothing to heal", "second run must be a no-op")
    t2, v2 = copper_counts(board)
    check((t1, v1) == (t2, v2),
          f"second run emitted copper: {t1}/{v1} -> {t2}/{v2}")


@test("a heal path that would violate clearance is rejected, and a board "
      "with NO legal bridge is a hard error", kind="known_bad")
def t_kb_heal_unbridgeable():
    """Safety rail (b). The full-height wall blocks every same-layer gap
    (collides catches each candidate) and there is no shared plane, so no
    legal bridge exists: the healer must ERROR OUT naming the net, never
    emit a violating bridge or silently skip. RED-VERIFIED 2026-07-21 by
    disabling the collision check (`collides(...) is not None: continue`
    removed), 4/4 runs FAIL: the broken healer emitted a bridge straight
    through the SIG wall and this test caught it — and the illegal overlap
    additionally made KiCad's connectivity net-propagation rewire the
    padless SIG wall onto PWR (measured: the wall reloaded as net PWR),
    which is exactly the corruption the collision guard exists to prevent.
    Check restored, test green."""
    d, p, board = heal_scratch("full_slice", bplane=False)
    r = must_fail(stitch(p), "heal with no legal bridge", "no LEGAL bridge")
    contains(r.out, "PWR", "the failure must name the net")
    t, v = copper_counts(board)
    check(not t.get("PWR") and not v.get("PWR"),
          f"a failed heal left PWR bridge copper on disk: {t}/{v}")


@test("heal_islands REFUSES to run before fill", kind="known_bad")
def t_kb_heal_before_fill():
    """On an unfilled board there are no islands, so a pre-fill heal would
    verify nothing and report success on a board whose pours may split at
    the very next fill."""
    d, p, board = heal_scratch("short_slice",
                               passes=("heal_islands", "fill", "gate"))
    must_fail(stitch(p), "heal before fill", "AFTER `fill`")


def _fp_lib_scratch():
    """A scratch cook-loadcell whose netlist puts ONE part on a project-local
    footprint lib (03_src/lib/local.pretty), with project.fp_lib_table set."""
    import yaml
    d = tmpdir("t2_fplib_")
    for sd in ("03_src", "02_parts"):
        if (LC / sd).is_dir():
            shutil.copytree(LC / sd, d / sd)
    (d / "04_kicad").mkdir()
    (d / "06_build" / "netlists").mkdir(parents=True)
    net = (LC / "06_build" / "netlists" / f"{STEM}.net").read_text()
    net = net.replace('(footprint "Capacitor_SMD:C_0805_2012Metric")',
                      '(footprint "local:C_0805_2012Metric")', 1)
    (d / "06_build" / "netlists" / f"{STEM}.net").write_text(net)
    pretty = d / "03_src" / "lib" / "local.pretty"
    pretty.mkdir(parents=True, exist_ok=True)
    shutil.copy("/usr/share/kicad/footprints/Capacitor_SMD.pretty/"
                "C_0805_2012Metric.kicad_mod",
                pretty / "C_0805_2012Metric.kicad_mod")
    cfg = yaml.safe_load((LC / "03_src" / "floorplan.yaml").read_text())
    libs = cfg.get("libraries") or ["/usr/share/kicad/footprints"]
    cfg["libraries"] = [{"lib": "local", "path": "03_src/lib/local.pretty"}] + list(libs)
    cfg["project"]["fp_lib_table"] = "04_kicad/fp-lib-table"
    cfg["project"]["netlist"] = f"06_build/netlists/{STEM}.net"
    p = d / "03_src" / "floorplan.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return d, p


@test("fp-lib-table uses ${KIPRJMOD} for a project-local lib, never an absolute path",
      kind="known_bad")
def t_kb_fp_lib_kiprjmod():
    """A project-local 03_src/lib footprint lib must be ${KIPRJMOD}-relative
    (contract 04_kicad 'fp-lib-table has no absolute paths'; project-structure
    'use ${KIPRJMOD} for local libs'). generate_board_generic emitted the
    RESOLVED absolute path, which breaks the instant the repo is cloned or the
    board moves. (RED against pre-fix: the local row is an absolute path.)"""
    d, p = _fp_lib_scratch()
    must_pass(run([KPY, GEN, p, "-o", d / "04_kicad" / "b.kicad_pcb"], cwd=d),
              "generate with a project-local lib")
    table = (d / "04_kicad" / "fp-lib-table").read_text()
    rows = [l for l in table.splitlines() if '(name "local")' in l]
    check(rows, f"project-local lib row missing from fp-lib-table:\n{table}")
    line = rows[0]
    check("${KIPRJMOD}" in line,
          f"project-local lib is NOT ${{KIPRJMOD}}-relative: {line}")
    check('(uri "/' not in line,
          f"fp-lib-table carries an absolute path for a project-local lib: {line}")


# ============================================================== E2E =====
def _e2e(project, stem, waves):
    """The real validation gate: generate -> rules -> prep -> REAL KRT ->
    import -> stitch -> rules LAST -> DRC. Sealed 04_kicad is read only;
    everything is built in a scratch tree."""
    proj = ROOT / "projects" / project
    d = tmpdir(f"e2e_rs_{stem}_")
    (d / "04_kicad").mkdir()
    (d / "06_build" / "netlists").mkdir(parents=True)
    for sd in ("03_src", "02_parts"):
        if (proj / sd).is_dir():
            shutil.copytree(proj / sd, d / sd)
    for f in (proj / "06_build" / "netlists").glob("*.net"):
        shutil.copy(f, d / "06_build" / "netlists")
    for name in (f"{stem}.kicad_sch", f"{stem}.kicad_pro", f"{stem}.kicad_dru",
                 "fp-lib-table", "sym-lib-table"):
        src = proj / "04_kicad" / name
        if src.is_file():
            shutil.copy(src, d / "04_kicad")
    board = d / "04_kicad" / f"{stem}.kicad_pcb"
    cfg = d / "03_src" / "route.yaml"

    must_pass(run([KPY, GEN, d / "03_src" / "floorplan.yaml", "-o", board],
                  cwd=d), f"{project}: generate")
    must_pass(run(["python3", "03_src/generate_rules.py"], cwd=d),
              f"{project}: rules BEFORE routing (canon R1)")
    must_pass(prep(cfg), f"{project}: prep")
    rr = must_pass(run(["python3", RS, "route", cfg], cwd=d, timeout=1800),
                   f"{project}: KRT waves")
    check(rr.out.count("Single-ended:") == waves,
          f"{project}: expected {waves} waves, got "
          f"{rr.out.count('Single-ended:')}")
    must_pass(run([KPY, RS, "import", cfg]), f"{project}: import")
    rs = must_pass(stitch(cfg), f"{project}: stitch")
    contains(rs.out, "gate: clean", f"{project}: stitch gate")
    # generate_rules LAST — pcbnew saves clobber .kicad_pro netclasses
    must_pass(run(["python3", "03_src/generate_rules.py"], cwd=d),
              f"{project}: rules LAST")

    (d / "06_build" / "drc").mkdir(exist_ok=True)
    run(["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
         "--schematic-parity", "--format", "json",
         "-o", "06_build/drc/gate.json", f"04_kicad/{stem}.kicad_pcb"], cwd=d)
    g = json.loads((d / "06_build" / "drc" / "gate.json").read_text())
    v, u, s = (len(g["violations"]), len(g["unconnected_items"]),
               len(g.get("schematic_parity", [])))
    check((v, u, s) == (0, 0, 0),
          f"{project}: DRC gate is {v} violations / {u} unconnected / "
          f"{s} parity, want 0/0/0\n"
          + "\n".join(f"  {x['type']}: {x.get('description','')[:100]}"
                      for x in g["violations"][:10])
          + "\n" + "\n".join(f"  UNCONN: {x.get('description','')[:100]}"
                             for x in g["unconnected_items"][:10]))
    return d, board


@test("E2E cook-loadcell: generic route+stitch from scratch -> DRC 0/0/0",
      slow=True)
def t_e2e_cook_loadcell():
    d, board = _e2e("cook-loadcell", "cook_loadcell", 3)
    r = must_pass(run([KPY, SCRIPTS / "board_netlist_parity.py", board,
                       LC / "04_kicad" / "cook_loadcell.kicad_pcb"]),
                  "netlist parity vs the sealed board")
    contains(r.out, "BOARD PARITY 0 -> PASS", "parity verdict")


@test("E2E crow-array-pod: generic route+stitch from scratch -> DRC 0/0/0",
      slow=True)
def t_e2e_crow_array_pod():
    _e2e("crow-array-pod", "crow_array_pod", 3)


if __name__ == "__main__":
    sys.exit(main())
