#!/usr/bin/env python3
"""t1_copper_length — R-LEN: realized COPPER length, measured off the board.

THE DEFECT THIS SUITE PINS (measured 2026-07-29, before the gate existed).
`policy_audit.py`'s R-LEN row was:

    has_len = bool(re.search(r"length|spread", audit_src, re.I))
    rows.append(("R-LEN", "PASS" if has_len else "N-A", ...))

so R-LEN PASSED if the word "length" or "spread" appeared ANYWHERE in the
project's `03_src/audit_board.py` — a COMMENT satisfied it. Fleet state at that
moment: smc0985-cooksense PASS on two comments about a CREEPAGE SLOT being
lengthened; pluto-rx2-8way PASS on comments plus an I3 check that measures
pad-centre RADIUS (placement) and whose own text says
`STAGE-6 OBLIGATION: equalise ROUTED length to +/-0.10mm` with nothing
enforcing it; crow-recorder-central-v2 PASS honestly (it sums
`t.GetLength()`); and **pluto-cal-switch — the board whose release artifact IS
a published length delta — N-A, "no timing-critical nets declared"**.

`t_prefix_rlen_passes_on_a_comment` re-measures that vacuity against the REAL
cooksense source on every run, so it cannot quietly come back.

RED-VERIFIED, EVERY KNOWN-BAD, 2026-07-29. A brand-new gate has no "pre-fix
code" to swap back in, so the equivalent was done: each check was NEUTERED in
`copper_length_audit.py` one at a time and its own fixture re-run, then the file
was byte-restored (`diff -q` clean). Measured pre-fix output in every case:
`0 passed, 1 failed` / `0 known-bad`, i.e. the fixture stopped biting.

| neutered | fixture that went red |
|---|---|
| `if tol != "report" and spread > float(tol)` -> `if False` | the 1.5 mm spread |
| `if drift > float(pin["tol_mm"])` -> `if False` | the pin drift |
| `if d.get("no_vias") and gg["n_via"]` -> `if False` | the one via on one arm |
| `unm = [m for m in members if not m["measured"]]` -> `unm = []` | the zone / unpriced via / branch trio |
| `if ghosts:` -> `if False:` | the unrouted board |
| `if not d.get("congruent_pads"):` -> `if False:` | the incongruent-pads spread |
| `raise AuditError("unparseable (segment ...)")` -> `continue` | the truncated segment |
| `if not d.get(req):` -> `if False:` | the seven malformed declarations |

The other headline is the M1 independence claim:
`t_reader_agrees_with_pcbnew` measures this gate's pcbnew-free reader against
pcbnew's own `PCB_TRACK.GetLength()` on four real routed boards. Measured at
landing: **351 nets, 0 disagreements above 1 um.**
"""
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, SCRIPTS, KPY, check, contains, eq, main, must_fail,
                     must_pass, not_contains, run, test, tmpdir)

LEN = SCRIPTS / "copper_length_audit.py"

# Real routed copper. All read-only. The sealed release sources are IMMUTABLE
# and are used deliberately (canon M-SHIP: grade the shipped bytes) — and
# because smc0985-cooksense's live 04_kicad board was track-free and mid-rebuild
# when this suite landed, so depending on it would have been a flake.
ROUTED = [
    ROOT / "projects/crow-mic-pod-v2/04_kicad/crow_mic_pod_v2.kicad_pcb",
    ROOT / "projects/crow-recorder-central-v2/04_kicad/"
           "crow_recorder_central_v2.kicad_pcb",
    ROOT / "projects/usb-hub-3s-v3/07_releases/v1.12-2026-07-28/source/"
           "usb_hub_3s_v2.kicad_pcb",
    ROOT / "projects/smc0985-cooksense/07_releases/cooksense-v1.6-2026-07-27/"
           "source/cooksense.kicad_pcb",
]

LAYERS = """\
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(4 "In1.Cu" signal)
\t\t(6 "In2.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(25 "Edge.Cuts" user)
\t)
"""


def board_text(segs=(), vias=(), arcs=(), zones=()):
    """A minimal but REAL KiCad 9 board body. Fixtures are built by breaking a
    good one in exactly one way, so every geometric number here is exact and
    the expected length is arithmetic, not a golden file."""
    out = ['(kicad_pcb', '\t(version 20241229)', '\t(generator "t1_copper")',
           '\t(general', '\t\t(thickness 1.6)', '\t)', LAYERS.rstrip("\n")]
    for net, (x1, y1), (x2, y2), layer in segs:
        out += [f'\t(segment', f'\t\t(start {x1} {y1})', f'\t\t(end {x2} {y2})',
                '\t\t(width 0.35)', f'\t\t(layer "{layer}")',
                f'\t\t(net "{net}")', '\t)']
    for net, (x1, y1), (mx, my), (x2, y2), layer in arcs:
        out += [f'\t(arc', f'\t\t(start {x1} {y1})', f'\t\t(mid {mx} {my})',
                f'\t\t(end {x2} {y2})', '\t\t(width 0.35)',
                f'\t\t(layer "{layer}")', f'\t\t(net "{net}")', '\t)']
    for net, (x, y), la, lb in vias:
        out += ['\t(via', f'\t\t(at {x} {y})', '\t\t(size 0.6)',
                '\t\t(drill 0.3)', f'\t\t(layers "{la}" "{lb}")',
                f'\t\t(net "{net}")', '\t)']
    for net in zones:
        out += ['\t(zone', '\t\t(layers "In1.Cu")', f'\t\t(net_name "{net}")',
                '\t\t(polygon (pts (xy 0 0) (xy 5 0) (xy 5 5) (xy 0 5)))', '\t)']
    out.append(')')
    return "\n".join(out) + "\n"


def scratch(decl, segs=(), vias=(), arcs=(), zones=(), name="fix"):
    """A project tree: 03_src/rules/nets.yaml + 04_kicad/<name>.kicad_pcb."""
    d = tmpdir("ct_len_")
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "04_kicad").mkdir()
    (d / "03_src" / "rules" / "nets.yaml").write_text(decl)
    (d / "04_kicad" / f"{name}.kicad_pcb").write_text(
        board_text(segs, vias, arcs, zones))
    return d


def pair_decl(tol=1.0, pin=None, no_vias=True, topology="chain",
              congruent=True, stackup=None, extra=""):
    lines = ["classes: {}", "length_match:", "  RF_PAIR:", "    adr: 0011",
             "    intent: >", "      the two arms of the calibration loopback;"
             " the arm-to-arm delta is a", "      PUBLISHED release artifact.",
             "    members:", "      ARM1: [ARM1_A, ARM1_B]",
             "      ARM2: [ARM2_A, ARM2_B]", f"    topology: {topology}",
             f"    max_spread_mm: {tol}"]
    if no_vias:
        lines.append("    no_vias: true")
    if congruent:
        lines.append("    congruent_pads: true")
    if stackup:
        lines.append(f"    stackup_mm: {stackup}")
    if pin:
        lines += ["    pin:", f"      spread_mm: {pin[0]}",
                  f"      tol_mm: {pin[1]}", "      measured_on: v1.0"]
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


def straight(net, y, length, x0=0.0, layer="F.Cu"):
    return (net, (x0, y), (x0 + length, y), layer)


# =============================================================== THE VACUITY
@test("THE PRE-FIX R-LEN PREDICATE PASSES ON NOTHING BUT THE WORD 'length' IN "
      "A COMMENT — re-measured against the REAL cooksense source",
      kind="known_bad")
def t_prefix_rlen_passes_on_a_comment():
    """THE DEFECT ITSELF (policy_audit.py:1078, until 2026-07-29). R-LEN was
    `re.search(r"length|spread", audit_src, re.I)` over the project's
    audit_board.py, so a comment satisfied it. This test runs the PRE-FIX
    predicate — not a description of it — against:

      1. a file whose ONLY content is `# the slot is length-adjusted`;
      2. smc0985-cooksense's REAL 03_src/audit_board.py, whose two matching
         lines are both CREEPAGE comments ("the true, slot-lengthened
         creepage", "the H4 notch ... lengthens it") with no net anywhere.

    Both make the pre-fix R-LEN print `PASS`. Then the NEW gate is run on a
    tree carrying the same comment-only audit_board.py and must NOT claim a
    pass: it reports N-A with a zero denominator, because a comment declares
    no matched group. Measured pre-fix output for both inputs: `R-LEN PASS
    "length-spread audit present in 03_src"`."""
    prefix = lambda src: bool(re.search(r"length|spread", src, re.I))

    comment_only = "# the slot is length-adjusted for creepage\n"
    check(prefix(comment_only),
          "the pre-fix predicate should PASS a bare comment — if it does not, "
          "this test is no longer reproducing the defect")

    real = ROOT / "projects/smc0985-cooksense/03_src/audit_board.py"
    src = real.read_text(encoding="utf-8-sig")
    check(prefix(src), f"{real} no longer trips the pre-fix predicate")
    hits = [l.strip() for l in src.splitlines()
            if re.search(r"length|spread", l, re.I)]
    check(all(l.lstrip().startswith("#") for l in hits),
          f"cooksense's matching lines are supposed to be COMMENTS; got {hits}")
    check(all("net" not in l.lower() for l in hits),
          f"a matching line mentions a net after all: {hits}")

    # the new gate, same tree, and it refuses to call that a pass
    d = scratch("classes: {}\n")
    (d / "03_src" / "audit_board.py").write_text(comment_only)
    r = must_pass(run([KPY, LEN, d]), "new gate on a comment-only tree")
    contains(r.out, "N-A: no `length_match:`", "the new gate says N-A")
    contains(r.out, "0 group(s) graded / 0 declared", "with a denominator")
    not_contains(r.out, "PASS R-LEN", "a comment must not produce a PASS")


# ================================================================ THE CLEAN HALF
@test("a genuinely matched pair PASSES: two 20.000 mm arms, spread 0.0000 mm")
def t_matched_pair_passes():
    d = scratch(pair_decl(tol=1.0),
                segs=[straight("ARM1_A", 1.0, 8.0),
                      straight("ARM1_B", 2.0, 12.0),
                      straight("ARM2_A", 3.0, 12.0),
                      straight("ARM2_B", 4.0, 8.0)])
    r = must_pass(run([KPY, LEN, d, "--strict"]), "matched pair")
    contains(r.out, "PASS R-LEN", "verdict")
    contains(r.out, "spread=0.0000 mm", "the measured spread")
    contains(r.out, "2 member path(s) measured / 2", "coverage denominator")
    contains(r.out, "1 group(s) graded / 1 declared", "group denominator")
    # both arms are 20.000 mm even though the NET SPLIT differs (8+12 vs 12+8):
    # a member is a CHAIN of nets, which is the thing declaring only the first
    # net would have got wrong.
    contains(r.out, "20.0000 mm", "per-member realized length")


@test("the phase conversion is reported, not just the millimetres")
def t_phase_reported():
    d = scratch(pair_decl(tol="report"),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0), straight("ARM2_B", 4, 10.5)])
    r = must_pass(run([KPY, LEN, d]), "phase report")
    contains(r.out, "spread=0.5000 mm", "spread")
    # 0.5 mm * 13.19 deg/mm = 6.60 deg at 6 GHz; 0.5 * 6.105 = 3.053 ps
    contains(r.out, "6.59 deg at 6 GHz", "degrees at 6 GHz")
    contains(r.out, "3.053 ps", "picoseconds")
    contains(r.out, "ceiling=report", "`report` is a legal, stated ceiling")


@test("an ARC's centreline is measured as r*theta, not chord to chord")
def t_arc_length():
    # semicircle, r = 1.0, from (0,0) through (1,1) to (2,0): pi mm, not 2 mm.
    d = scratch(pair_decl(tol=1.0),
                segs=[straight("ARM1_B", 2.0, 0.0001),
                      straight("ARM2_A", 3.0, 3.1416), straight("ARM2_B", 4, 0.0001)],
                arcs=[("ARM1_A", (0, 0), (1, 1), (2, 0), "F.Cu")])
    r = must_pass(run([KPY, LEN, d]), "arc")
    contains(r.out, "3.1417", f"ARM1 = the arc's pi ({math.pi:.4f}) + one "
                              f"0.0001 stub")
    not_contains(r.out, "2.0001", "the 2.0000 start->end CHORD is not the answer")


@test("via barrel z-length is priced from a DECLARED stackup and only then")
def t_via_z_from_declared_stackup():
    """0.2104 + 0.9792 = 1.1896 mm for an F.Cu -> In2.Cu hop on
    JLC04161H-7628. The board carries no (stackup) block, so this number can
    only come from the declaration — and if it is absent the member is
    UNREACHED (t_via_without_stackup_is_unreached), never treated as 0."""
    d = scratch(pair_decl(tol=2.0, no_vias=False,
                          stackup="[0.2104, 0.9792, 0.2104]"),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0),
                      straight("ARM2_B", 4, 8.8104, layer="In2.Cu")],
                vias=[("ARM2_B", (0, 4), "F.Cu", "In2.Cu")])
    r = must_pass(run([KPY, LEN, d, "--strict"]), "via z priced")
    contains(r.out, "PASS R-LEN", "verdict")
    # 8.8104 + 1.1896 = 10.0000 -> spread 0.0000
    contains(r.out, "spread=0.0000 mm",
             "the via barrel is 1.1896 mm of real copper and it closes the gap")


@test("the pcbnew-free reader AGREES WITH PCBNEW on four real routed boards "
      "(canon M1: the checker may not share a method with the checked)")
def t_reader_agrees_with_pcbnew():
    """pcbnew generated and imported every millimetre of this copper, so pcbnew
    is not allowed to be the authority on how long it is. This measures the
    claim rather than asserting it: per-net track+arc totals from the text
    reader against `PCB_TRACK.GetLength()`, on crow-mic-pod-v2,
    crow-recorder-central-v2, usb-hub-3s-v3 v1.12 (sealed) and cooksense v1.6
    (sealed). Measured at landing: 351 nets, 0 disagreements above 1 um."""
    probe = (
        "import sys, collections, json\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import pcbnew\n"
        "from copper_length_audit import read_copper, net_geometry\n"
        "b = sys.argv[2]\n"
        "nets, order, _ = read_copper(b)\n"
        "mine = {n: net_geometry(e, order, None)['track_mm']\n"
        "        for n, e in nets.items() if e['segs']}\n"
        "brd = pcbnew.LoadBoard(b)\n"
        "theirs = collections.defaultdict(float)\n"
        "for t in brd.GetTracks():\n"
        "    if t.GetClass() == 'PCB_VIA': continue\n"
        "    theirs[t.GetNetname()] += pcbnew.ToMM(t.GetLength())\n"
        "theirs = {k: v for k, v in theirs.items() if v > 0}\n"
        "ks = set(mine) | set(theirs)\n"
        "bad = [(k, mine.get(k), theirs.get(k)) for k in ks\n"
        "       if abs((mine.get(k) or 0) - (theirs.get(k) or 0)) > 1e-6]\n"
        "print('@@' + json.dumps([len(ks), bad[:5]]))\n")
    import json
    total, nbad = 0, 0
    for b in ROUTED:
        check(b.exists(), f"routed fixture missing: {b}")
        r = must_pass(run([KPY, "-c", probe, SCRIPTS, b]), f"probe {b.name}")
        n, bad = json.loads(r.out.split("@@", 1)[1].strip())
        total += n
        nbad += len(bad)
        check(not bad, f"{b.name}: reader disagrees with pcbnew on {bad}")
    check(total > 300, f"fixture too small to be evidence: {total} nets")
    check(nbad == 0, f"{nbad} of {total} nets disagree")


@test("the census measures the ONE honest bespoke length check in the fleet — "
      "crow-recorder-central-v2's USB pair — and reproduces its number")
def t_census_reproduces_the_bespoke_check():
    """CANON M8 (two-strike promotion). crow-recorder-central-v2's
    `03_src/audit_board.py` sums `t.GetLength()` over USB_DP/USB_DN and floors
    the spread at 1 mm — a bespoke per-board implementation of exactly this
    check, and the second board needing it (the pluto matched pair) converts it
    into shared backend. The shared reader must reproduce the bespoke number on
    the real board or the promotion is not sound: 23.6209 / 23.5110 mm,
    spread 0.1099 mm, well inside that board's own 1 mm floor.

    Both nets are 3 COMPONENTS with 0 branches — the pad-join artifact. That is
    why `topology: chain` is verified on branches and cycles and NOT on
    component count; failing this net would have been the gate penalising the
    board for the reader's blindness."""
    proj = ROOT / "projects/crow-recorder-central-v2"
    r = must_pass(run([KPY, LEN, proj, "--census"]), "census")
    contains(r.out, "USB_DP", "the pair is measured")
    dp = [l for l in r.out.splitlines() if l.strip().startswith("USB_DP")][0]
    dn = [l for l in r.out.splitlines() if l.strip().startswith("USB_DN")][0]
    a, bb = float(dp.split()[1]), float(dn.split()[1])
    check(abs(a - 23.6209) < 1e-3, f"USB_DP measured {a}, expected 23.6209")
    check(abs(bb - 23.5110) < 1e-3, f"USB_DN measured {bb}, expected 23.5110")
    check(abs(abs(a - bb) - 0.1099) < 1e-3,
          f"pair spread {abs(a - bb):.4f}, expected 0.1099 mm "
          f"(the board's own bespoke floor is 1 mm)")
    contains(r.out, "via barrel(s) NOT priced",
             "the unpriced via z is DECLARED, not silently zero")
    contains(r.out, "net(s) measured /", "census carries a denominator")


# ================================================================= KNOWN-BAD
@test("two arms differing by a DECLARED-INTOLERABLE amount FAIL, with the "
      "delta converted to degrees", kind="known_bad")
def t_spread_over_ceiling_fails():
    """The whole point. 21.5 vs 20.0 mm is 1.5 mm of unmatched copper = 19.8 deg
    at 6 GHz, against a declared 1.0 mm drift ceiling. Nothing else in this repo
    can see it: DRC is clean, ERC is clean, parity is 0, and A-SYM reports
    0.0 um because the PLACEMENT is still perfectly mirrored."""
    d = scratch(pair_decl(tol=1.0),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0), straight("ARM2_B", 4, 11.5)])
    r = must_fail(run([KPY, LEN, d]), "spread over ceiling", "R-LEN-SPREAD")
    contains(r.out, "1.5000 mm exceeds max_spread_mm 1.0", "the measured delta")
    contains(r.out, "19.79 deg at 6 GHz", "converted to phase")
    contains(r.out, "ARM1=20.0000", "both members are named with their numbers")
    contains(r.out, "ARM2=21.5000", "both members are named with their numbers")


@test("the PIN bites: copper that MOVED off the published number FAILS even "
      "though the spread is inside the ceiling", kind="known_bad")
def t_pin_drift_fails():
    """THE CHECK THAT ACTUALLY GUARDS A RELEASE. A calibration board's
    requirement is that the delta be KNOWN, STABLE and REPRODUCIBLE — not zero.
    KRT is stochastic, so a re-route silently invalidates every published
    picosecond. Here the spread is 0.6 mm, comfortably inside the 1.0 mm
    ceiling, and the release published 0.0 +-0.05 mm: the ceiling PASSES and the
    pin FAILS, which is the pair of verdicts disagreeing on purpose."""
    d = scratch(pair_decl(tol=1.0, pin=(0.0, 0.05)),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0), straight("ARM2_B", 4, 10.6)])
    r = must_fail(run([KPY, LEN, d]), "pin drift", "R-LEN-PIN")
    contains(r.out, "measured spread 0.6000 mm vs pinned 0.0", "the drift")
    contains(r.out, "re-measure and re-publish", "the instruction")
    not_contains(r.out, "R-LEN-SPREAD",
                 "the 1.0 mm ceiling is NOT what caught this — the pin is")


@test("ONE VIA ON ONE ARM FAILS a group declared no_vias — the pure "
      "differential error nothing in the router prevents", kind="known_bad")
def t_no_vias_violation_fails():
    """MEASURED 2026-07-29: no per-net via ban exists at route time.
    `route_and_stitch_generic.py` and both pluto `route.yaml` files have no
    `no_vias` concept; the only mechanism is a per-WAVE `layers: [F.Cu]`
    restriction, which is not per-net and is re-checked by nothing. ADR-0006(c)
    (pluto-rx2-8way) and ADR-0011 (pluto-cal-switch) both forbid vias in an RF
    arm because a via's inductance depends on drill and plating, unspecified
    per hole — so one via on ONE member is a differential error on a published
    delta. This gate is the only place that intent is graded."""
    d = scratch(pair_decl(tol=1.0, stackup="[0.2104, 0.9792, 0.2104]"),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0), straight("ARM2_B", 4, 10.0)],
                vias=[("ARM2_B", (0, 4), "F.Cu", "In1.Cu")])
    r = must_fail(run([KPY, LEN, d]), "no_vias violated", "R-LEN-VIA")
    contains(r.out, "ARM2_B carries 1 via(s)", "names the net and the count")
    contains(r.out, "NOTHING IN THE ROUTER ENFORCES THIS",
             "the report says where the gap is")


@test("a net whose length CANNOT be determined is UNREACHED, never a pass — "
      "a zone, a via with no stackup, and a branch, each on its own",
      kind="known_bad")
def t_undeterminable_is_unreached():
    """canon M-COVER: input a gate cannot measure is a FAIL/UNREACHED, never a
    skip. Three independent reasons, each asserted alone, and `--strict` turns
    UNREACHED into exit 1 so the coverage gap is a red gate rather than a line
    nobody reads. The bottom line must never say `PASS R-LEN` in any of them."""
    base = dict(segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0), straight("ARM2_B", 4, 10.0)])

    # (1) POURED COPPER: current spreads, so there is no path length.
    d = scratch(pair_decl(tol=1.0), zones=["ARM2_B"], **base)
    r = must_fail(run([KPY, LEN, d, "--strict"]), "zone on a phase net",
                  "R-LEN-UNREACHED")
    contains(r.out, "1 zone(s) on this net", "the reason is named")
    contains(r.out, "poured copper has no path length", "and explained")
    not_contains(r.out, "PASS R-LEN", "an UNREACHED group is not a pass")

    # (2) A VIA WITH NO DECLARED STACKUP: the board has no (stackup) block, so
    #     the barrel z-length is not derivable and must not be read as zero.
    d = scratch(pair_decl(tol=1.0, no_vias=False),
                vias=[("ARM2_B", (0, 4), "F.Cu", "B.Cu")], **base)
    r = must_fail(run([KPY, LEN, d, "--strict"]), "via with no stackup",
                  "R-LEN-UNREACHED")
    contains(r.out, "no `stackup_mm:` declared", "the reason")
    not_contains(r.out, "PASS R-LEN", "an UNREACHED group is not a pass")

    # (3) A BRANCH: the net is a TREE, so total != path and the gate refuses to
    #     pick one. Both numbers are printed so the ambiguity has a SIZE.
    d = scratch(pair_decl(tol=1.0),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0),
                      # the trunk is split AT the tap point, so the stub lands on
                      # a real vertex of degree 3. A stub touching the MIDDLE of
                      # a segment is not a graph branch at all — KiCad stores no
                      # vertex there — and a fixture that got that wrong would
                      # have tested nothing.
                      ("ARM2_B", (0.0, 4.0), (5.0, 4.0), "F.Cu"),
                      ("ARM2_B", (5.0, 4.0), (10.0, 4.0), "F.Cu"),
                      ("ARM2_B", (5.0, 4.0), (5.0, 2.0), "F.Cu")])
    r = must_fail(run([KPY, LEN, d, "--strict"]), "branching chain",
                  "R-LEN-UNREACHED")
    contains(r.out, "BRANCH vertex", "the branch is named")
    contains(r.out, "topology: tree", "and the escape hatch is offered")
    not_contains(r.out, "PASS R-LEN", "an UNREACHED group is not a pass")


@test("an UNROUTED board is UNREACHED WITH ITS COUNT, not N-A and not PASS — "
      "which is exactly what both pluto boards report today", kind="known_bad")
def t_unrouted_board_is_unreached():
    """THE CURRENT STATE OF THE TWO BOARDS THIS GATE WAS BUILT FOR. Neither
    pluto board is routed (0 segments in 04_kicad on 2026-07-29), so the gate
    cannot measure their arms yet — and saying so with a count is the entire
    difference between this gate and the one it replaces, which reported PASS
    on prose about copper that did not exist."""
    d = scratch(pair_decl(tol=1.0))          # declaration, zero copper
    r = must_fail(run([KPY, LEN, d, "--strict"]), "unrouted board",
                  "R-LEN-UNREACHED")
    contains(r.out, "4 member net(s) carry no copper", "the count")
    contains(r.out, "ARM1_A, ARM1_B, ARM2_A, ARM2_B", "every net is named")
    contains(r.out, "the board is unrouted or partly routed", "the diagnosis")
    contains(r.out, "E-NETREF K12", "and it points at the netlist-side gate")
    contains(r.out, "0 group(s) graded / 1 declared", "the denominator is honest")
    not_contains(r.out, "PASS R-LEN", "nothing was measured, so nothing passed")


@test("a spread measured over members with UNDECLARED pad congruence is "
      "reported and UNREACHED, not graded", kind="known_bad")
def t_incongruent_pads_unreached():
    """The pad-entry term is real copper this reader does not measure, so every
    absolute is a LOWER BOUND. Comparing two lower bounds with different
    unmeasured offsets is not a measurement. `congruent_pads: true` is the
    claim that the offsets are equal — which pluto-cal-switch's A-SYM
    (identical footprints at identical rotation) and pluto-rx2-8way ADR-0006(d)
    already independently require. Without the claim the number still PRINTS,
    because hiding it would be worse; it just is not graded."""
    d = scratch(pair_decl(tol=1.0, congruent=False),
                segs=[straight("ARM1_A", 1, 10.0), straight("ARM1_B", 2, 10.0),
                      straight("ARM2_A", 3, 10.0), straight("ARM2_B", 4, 10.0)])
    r = must_fail(run([KPY, LEN, d, "--strict"]), "no congruent_pads claim",
                  "R-LEN-UNREACHED")
    contains(r.out, "spread 0.0000 mm MEASURED but not graded", "printed anyway")
    contains(r.out, "congruent_pads", "the missing claim is named")


@test("a MALFORMED length_match declaration is UNGRADED (exit 2), never a "
      "silent skip", kind="known_bad")
def t_malformed_declaration_ungraded():
    """canon M-COVER: input the gate cannot parse is a failure, not a skip.
    Five shapes, each broken in exactly one way."""
    cases = [
        ("length_match:\n  G:\n    intent: x\n    members:\n"
         "      A: [N1]\n      B: [N2]\n", "has no `adr:`"),
        ("length_match:\n  G:\n    adr: 1\n    members:\n"
         "      A: [N1]\n      B: [N2]\n", "has no `intent:`"),
        ("length_match:\n  G:\n    adr: 1\n    intent: x\n"
         "    members:\n      A: [N1]\n", "mapping of >= 2 named net chains"),
        ("length_match:\n  G:\n    adr: 1\n    intent: x\n    members:\n"
         "      A: N1\n      B: [N2]\n", "must be an ORDERED list"),
        ("length_match:\n  G:\n    adr: 1\n    intent: x\n    members:\n"
         "      A: [N1]\n      B: [N2]\n    max_spread_mm: tight\n",
         "must be a number or the literal `report`"),
        ("length_match:\n  G:\n    adr: 1\n    intent: x\n    members:\n"
         "      A: [N1]\n      B: [N2]\n    pin:\n      spread_mm: 0\n",
         "needs both `spread_mm:` and `tol_mm:`"),
        ("length_match: [not, a, mapping]\n", "must be a mapping"),
    ]
    for decl, expect in cases:
        d = scratch(decl)
        r = run([KPY, LEN, d])
        eq(r.rc, 2, f"malformed decl ({expect}) must exit 2 UNGRADED")
        contains(r.out, "UNGRADED", "the verdict names itself")
        contains(r.out, expect, "the diagnosis names the field")


@test("a TRUNCATED copper item is UNGRADED, not silently under-measured",
      kind="known_bad")
def t_unparseable_copper_is_ungraded():
    """An under-reported length is the worst possible failure mode here: it is
    a number, it looks measured, and it is short. A `(segment ...)` missing its
    `(end ...)` must stop the audit rather than contribute zero."""
    d = scratch(pair_decl(tol=1.0),
                segs=[straight("ARM1_A", 1, 10.0)])
    b = d / "04_kicad" / "fix.kicad_pcb"
    b.write_text("\n".join(l for l in b.read_text().splitlines()
                           if not l.startswith("\t\t(end ")) + "\n")
    r = run([KPY, LEN, d])
    eq(r.rc, 2, "a truncated segment must exit 2")
    contains(r.out, "unparseable (segment ...)", "the item is named")
    contains(r.out, "refusing to under-report copper", "and the reason")


@test("the schema is self-documenting and the gate obeys G-INPUT/G-COVER")
def t_schema_and_gate_contract():
    r = must_pass(run([KPY, LEN, "--schema"]), "--schema")
    for k in ("length_match:", "members:", "topology: chain", "no_vias:",
              "max_spread_mm:", "pin:", "congruent_pads:", "stackup_mm:"):
        contains(r.out, k, f"the schema documents {k}")
    ga = SCRIPTS / "gate_contract_audit.py"
    r = must_pass(run([KPY, ga, "--root", ROOT]), "gate_contract_audit")
    contains(r.out, "G-CONTRACT OK",
             "the gate-on-gates accepts the new checker: it names its input, "
             "prints an N/M denominator, and has a must_fail fixture here")


# ========================================= the declaration, WHERE IT ENTERS
@test("E-NETREF grades the matched-group declaration as kind K12: a tolerance "
      "addressed to a net the board does not have FAILS", kind="known_bad")
def t_netref_k12_ghost():
    """canon M-ENTRY / ADR-0007 — check a fact where it ENTERS the pipeline, not
    where it shows. A `length_match:` member is a NET REFERENCE, and the sibling
    gate `net_reference_audit.py` (canon E-NETREF) is the enumerated home for
    that class. It has to be: the first E-NETREF fleet sweep measured **64 of
    908 referenced net names absent from their own board's netlist, 39 of them
    written against a DATASHEET reference design's pin function rather than any
    net the board has.** A phase tolerance addressed to a name that does not
    exist is decoration, and the two gates must agree about that.

    Kind K12 is added to `net_reference_audit.py`'s KINDS table in the HARD
    class (a miss is a GHOST and FAILS), with `copper_length_audit.py` as its
    named consumer — the table forbids a kind with no consumer, because the
    consumer is the argument that a miss costs something."""
    NREF = SCRIPTS / "net_reference_audit.py"
    decl = ("classes: {}\nlength_match:\n  RF_PAIR:\n    adr: 0011\n"
            "    intent: the two arms\n    members:\n"
            "      ARM1: [LOOP_ARM1]\n      ARM2: [LOOP_ARM2_TYPO]\n")
    d = scratch(decl)
    nl = d / "06_build" / "netlists"
    nl.mkdir(parents=True)
    (nl / "b.net").write_text(
        '(export (nets\n'
        '  (net (code "1") (name "LOOP_ARM1"))\n'
        '  (net (code "2") (name "LOOP_ARM2"))\n'
        '))\n')
    r = must_fail(run([KPY, NREF, d]), "E-NETREF on a ghost length_match net",
                  "K12")
    contains(r.out, "LOOP_ARM2_TYPO", "the ghost member net is named")
    contains(r.out, "length_match.RF_PAIR.members.ARM2[0]", "with its site")
    contains(r.out, "copper_length_audit", "and its named consumer")
    # the near-miss diagnosis is most of the value: LOOP_ARM2 is one edit away
    contains(r.out, "LOOP_ARM2", "the near-miss candidate is offered")
    # ...and the same declaration with the typo FIXED must RESOLVE. Adjacent
    # property, re-measured every run: a red on a brand-new kind proves only
    # that the kind is new.
    d2 = scratch(decl.replace("LOOP_ARM2_TYPO", "LOOP_ARM2"))
    nl2 = d2 / "06_build" / "netlists"
    nl2.mkdir(parents=True)
    (nl2 / "b.net").write_text((nl / "b.net").read_text())
    r2 = must_pass(run([KPY, NREF, d2]), "E-NETREF with the typo fixed")
    contains(r2.out, "K12", "K12 still appears in the kind table")


if __name__ == "__main__":
    sys.exit(main())
