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
                     edit_board, main, must_fail, must_pass, run, test, tmpdir)

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
