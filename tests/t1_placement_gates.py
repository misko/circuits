#!/usr/bin/env python3
"""T1: the shared placement-stage gates (skills/kicad-pcb/scripts/
placement_gates.py) — P-OUT pads-inside-outline and P-CAP corridor
crossing-demand vs capacity.

Both checks exist because the smc0985-cooksense placement->routing D-BACK
(2026-07-23, journal 01_docs/journal/routing_cooksense.md) consumed ~13 hours
proving two facts NO static gate then checked:
  * J_PI laid 34/40 pins 1..43mm OFF the board outline — the placement audit
    had no pads-inside-outline check (I-EDGE only measures the connector
    mouth), so a 600k-iteration KRT run was the checker.
  * the placement journal under-counted corridor crossings 8x (capacity 6 vs
    demand 26) — no static crossing-demand estimate existed.

RED-verification (tests/README.md §Adding a regression): placement_gates.py
is a NEW gate, so the pre-fix code is its ABSENCE — every known-bad fixture
here was run with the script removed (mv away, run, restore) and the suite
FAILED (script not found), and t_out_blind_spot additionally proves the
strongest pre-existing gate (audit_template I1, a RECTANGLE check) exits 0 on
the same board the new P-OUT fails: the fixture pins a defect no prior gate
could see, not one that was merely unwired.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

PG = SCRIPTS / "placement_gates.py"
AUDIT_T = SCRIPTS / "audit_template.py"

# The historical defect board: cooksense placement gate #1 (commit 18392f2),
# the exact state that passed every audit of its day and then burned ~13h of
# routing. Extracted READ-ONLY from git history — never regenerated, so this
# fixture cannot drift with the generators.
PREREDO_COMMIT = "18392f2"
PREREDO_PATH = "projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb"


def preredo_board():
    d = tmpdir("pg_hist_")
    out = d / "cooksense_preredo.kicad_pcb"
    cp = subprocess.run(["git", "show", f"{PREREDO_COMMIT}:{PREREDO_PATH}"],
                        cwd=ROOT, capture_output=True)
    check(cp.returncode == 0 and len(cp.stdout) > 100000,
          f"git show of the historical defect board failed: {cp.stderr[:200]}")
    out.write_bytes(cp.stdout)
    return d, out


# ---------------------------------------------------------------- builder
def synth_board(d, off_outline_part=False, gap_mm=1.2, wires=10):
    """A synthetic two-cluster board, built from scratch for full control:

      * L-SHAPED outline (0,0)-(60,50) with the (45..60, 30..50) corner
        notched away — so 'inside the bounding rectangle' and 'inside the
        outline' genuinely differ (the blindness of a rect check is testable).
      * NORTH cluster (y=10) and SOUTH cluster (y=40) of 2-pad SMD parts,
        `wires` nets each running one pad north -> one pad south.
      * a rule-area WALL across y=20..30 with a single `gap_mm` corridor at
        x~27 — the pour-keepout kind, exactly like the cooksense isolation
        strip (tracks NOT forbidden on the zone; the constraint is intent).

    off_outline_part=True adds RX at (52,40): inside the bounding rect,
    OUTSIDE the L outline — the J_PI class of defect on a shape where only a
    true polygon test can see it.
    """
    out = d / "synth.kicad_pcb"
    code = f"""
import pcbnew
V = pcbnew.VECTOR2I_MM
b = pcbnew.CreateEmptyBoard()

pts = [(0,0),(60,0),(60,30),(45,30),(45,50),(0,50)]
for i in range(len(pts)):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i+1)%len(pts)]))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(pcbnew.FromMM(0.1))
    b.Add(s)

nets = {{}}
def net(nm):
    if nm not in nets:
        ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni); nets[nm] = ni
    return nets[nm]

def part(ref, x, y, n1, n2):
    f = pcbnew.FOOTPRINT(b)
    f.SetReference(ref)
    ps = []
    for i, nm in ((1, n1), (2, n2)):
        p = pcbnew.PAD(f)
        p.SetNumber(str(i))
        p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetSize(V(1.0, 1.0))
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetLayerSet(pcbnew.PAD.SMDMask())
        f.Add(p); ps.append((p, i, nm))
    b.Add(f)
    f.SetPosition(V(x, y))
    for p, i, nm in ps:
        p.SetPosition(V(x + (-1.0 if i == 1 else 1.0), y))
        if nm: p.SetNet(net(nm))

W = {wires}
for k in range(W):
    part(f"RN{{k}}", 4 + 4*k, 10, f"STUB_N{{k}}", f"X{{k}}")   # north cluster
    part(f"RS{{k}}", 4 + 4*k, 40, f"X{{k}}", f"STUB_S{{k}}")   # south cluster

def wall(x0, x1):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    try: z.SetDoNotAllowCopperPour(True)
    except AttributeError: z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowTracks(False)          # pour-keepout, like the incident
    ls = pcbnew.LSET()
    for L in (pcbnew.F_Cu, pcbnew.B_Cu): ls.AddLayer(L)
    z.SetLayerSet(ls)
    z.Outline().NewOutline()
    for x, y in ((x0,20),(x1,20),(x1,30),(x0,30)):
        z.AppendCorner(V(x, y), -1)
    b.Add(z)

wall(0.0, 27.0)
wall(27.0 + {gap_mm}, 60.0)

if {off_outline_part!r}:
    part("RX", 52, 40, "X0", "STUB_RX")   # in the bbox, OUTSIDE the L

pcbnew.SaveBoard(r"{out}", b)
"""
    must_pass(run([KPY, "-c", code]), "synth board builder")
    return out


def cfg(d, **over):
    p = d / "placement_gates.json"
    p.write_text(json.dumps(over))
    return p


# ------------------------------------------------------------ clean cases
@test("placement_gates PASSes the three current boards as placed")
def t_real_boards_pass():
    """The calibration set: cooksense post-REDO (isolation strip + resident
    keypad nets — the hardest honest PASS), usb-hub-3s-v3, and
    crow-recorder-central-v2. Measured worst demand/capacity ratios at the
    time of writing: 0.14 / 0.02 / 0.07 — vs the defect board's 0.90."""
    for proj, stem in (("smc0985-cooksense", "cooksense"),
                       ("usb-hub-3s-v3", "usb_hub_3s_v2"),
                       ("crow-recorder-central-v2", "crow_recorder_central_v2")):
        board = ROOT / "projects" / proj / "04_kicad" / f"{stem}.kicad_pcb"
        r = must_pass(run([KPY, PG, board]), f"placement_gates on {proj}")
        contains(r.out, "PLACEMENT-GATES: PASS", f"{proj} verdict")


@test("placement_gates PASSes the clean synthetic two-cluster board (wide corridor)")
def t_synth_clean():
    d = tmpdir("pg_")
    b = synth_board(d, gap_mm=12.0)     # generous corridor: 12mm ~ 52 slots
    r = must_pass(run([KPY, PG, b]), "placement_gates on clean synth")
    contains(r.out, "PLACEMENT-GATES: PASS", "synth verdict")


@test("P-CAP whole-check waiver WITH evidence turns the pinched board green")
def t_cap_waiver_with_evidence():
    d = tmpdir("pg_")
    b = synth_board(d)                  # pinched: would FAIL P-CAP
    c = cfg(d, waive={"P-CAP": "measured: KRT routed r3 chain 0-unconnected "
                               "through the 1.2mm gap on 2026-07-23"})
    r = must_pass(run([KPY, PG, b, "--config", c]), "waived P-CAP")
    contains(r.out, "P-CAP WAIVED", "waiver echo")


@test("P-OUT per-ref out_ok waiver exempts a castellated-style part")
def t_out_ok_ref_waiver():
    d = tmpdir("pg_")
    b = synth_board(d, off_outline_part=True, gap_mm=12.0)
    c = cfg(d, out_ok=["RX"])
    r = must_pass(run([KPY, PG, b, "--config", c]), "out_ok-waived P-OUT")
    contains(r.out, "PLACEMENT-GATES: PASS", "verdict")


# --------------------------------------------------------- known-bad cases
@test("P-OUT FAILS a pad outside the outline that a RECT check cannot see",
      kind="known_bad")
def t_out_blind_spot():
    """RX sits in the notch of the L-shaped outline: INSIDE the bounding
    rectangle, OUTSIDE the board. This is the J_PI class (34/40 pins off the
    outline, every audit green). The same board is run through the strongest
    pre-existing gate, audit_template I1 (a configured-RECTANGLE check), with
    the frame set to the outline's bbox — it must PASS, proving the old gate
    is structurally blind here and P-OUT is not a re-wiring but a new check.
    RED: with placement_gates.py removed, this test fails (no gate fires)."""
    d = tmpdir("pg_")
    b = synth_board(d, off_outline_part=True, gap_mm=12.0)
    r = run([KPY, PG, b])
    must_fail(r, "placement_gates on the off-outline pad", "P-OUT RX")
    contains(r.out, "OFF the board outline", "P-OUT message")
    # the pre-existing rectangle gate is blind to the same defect:
    acfg = d / "audit.json"
    acfg.write_text(json.dumps({"frame": [0.0, 0.0, 60.0, 50.0],
                                "edge_margin": 0.3,
                                "float_ok_numbers": ["MP", "S1"]}))
    ra = run([KPY, AUDIT_T, b, "--config", acfg])
    check("I1 pad-off-board: RX" not in ra.out,
          "audit_template I1 unexpectedly sees the notch defect — if the rect "
          "check grew a polygon test, update this fixture's premise")


@test("P-CAP FAILS the synthetic two-cluster pinched-corridor board",
      kind="known_bad")
def t_cap_pinched():
    """10 nets must cross a 1.2mm corridor (~6 track-slots across 2 layers;
    FAIL threshold at factor 0.5 = 3). The wall is a POUR-keepout with tracks
    allowed — exactly the cooksense isolation strip's DRC-invisible kind.
    RED: with the rule-area blockage disabled (cap.keepouts="none"), the same
    board PASSES — asserted below, proving the keepout blockage is the
    load-bearing part of the capacity model, not pad density."""
    d = tmpdir("pg_")
    b = synth_board(d)
    r = run([KPY, PG, b])
    must_fail(r, "placement_gates on the pinched corridor", "P-CAP corridor starved")
    m = re.search(r"crossing demand (\d+) nets > capacity (\d+) tracks", r.out)
    check(m and int(m.group(1)) == 10 and int(m.group(2)) <= 8,
          f"expected demand 10 vs single-digit capacity, got: {m and m.group(0)}")
    # red half: neuter the blockage model -> the gate goes blind again
    c = cfg(d, cap={"keepouts": "none"})
    rb = must_pass(run([KPY, PG, b, "--config", c]),
                   "P-CAP with keepout blockage disabled")
    contains(rb.out, "PLACEMENT-GATES: PASS", "neutered-model verdict")


@test("HISTORICAL: the cooksense pre-REDO board (18392f2) FAILS both gates",
      kind="known_bad")
def t_historical_preredo():
    """The board that cost ~13 hours: placement gate #1 state, extracted
    read-only from git. P-OUT must name J_PI pads off the outline (the audit
    of the day said PASS); P-CAP must declare the y~50..76 corridor starved
    with demand >= 20 (the journal's eyeball estimate was ~3; the routing
    post-mortem measured 26 vs capacity 6). Measured by this gate at the time
    of writing: 37 P-OUT pad fails, worst cut y=58.5 demand 27 vs geometric
    capacity 30 (ratio 0.90; FAIL factor 0.5)."""
    d, b = preredo_board()
    r = run([KPY, PG, b])
    must_fail(r, "placement_gates on the historical defect board")
    contains(r.out, "P-OUT J_PI.", "J_PI off-outline finding")
    contains(r.out, "P-CAP corridor starved at y=", "corridor finding")
    m = re.search(r"P-CAP corridor starved at y=[\d.]+mm: crossing demand (\d+)", r.out)
    check(m and int(m.group(1)) >= 20,
          f"corridor demand should be >=20 (journal: 26), got {m and m.group(1)}")


@test("a waiver WITHOUT evidence is itself a FAIL", kind="known_bad")
def t_waiver_no_evidence():
    """Canon M4: a waiver needs evidence, not rationale — an empty `why` is
    an inherited-defect vector, so the gate refuses it outright."""
    d = tmpdir("pg_")
    b = synth_board(d, gap_mm=12.0)
    c = cfg(d, waive={"P-CAP": "  "})
    r = run([KPY, PG, b, "--config", c])
    must_fail(r, "empty-evidence waiver", "waiver without evidence")


@test("a board with no closed outline FAILS P-OUT", kind="known_bad")
def t_no_outline():
    """P-OUT must not vacuously pass when Edge.Cuts is missing/open — a gate
    that skips silently on bad input is the jlc_twin NO-CAD bug again."""
    d = tmpdir("pg_")
    b = synth_board(d, gap_mm=12.0)
    code = ("import pcbnew,sys\nb=pcbnew.LoadBoard(sys.argv[1])\n"
            "for dr in [x for x in b.GetDrawings()"
            " if x.GetLayer()==pcbnew.Edge_Cuts]:\n"
            "    b.Remove(dr)\nb.Save(sys.argv[1])\n")
    must_pass(run([KPY, "-c", code, b]), "strip Edge.Cuts")
    r = run([KPY, PG, b])
    must_fail(r, "placement_gates without an outline", "P-OUT board has NO closed")


if __name__ == "__main__":
    sys.exit(main())
