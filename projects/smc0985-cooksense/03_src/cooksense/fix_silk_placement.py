#!/usr/bin/env /usr/bin/python3
"""fix_silk_placement.py — cooksense silk repair pass (v1.7, canon M3 source).

TWO defects, both confirmed on the v1.7 staging board by the fresh-context
RENDER review and re-measured by the lead, both invisible to every gate this
board runs:

  R-02  `J_MODE` and `D_COILEN` refdes are printed INTO the east-edge MILLED
        NOTCH.  Notch void x[191.50..200.05] y[48.80..49.80]; J_MODE's refdes
        bbox x[194.099..197.801] y[48.386..49.614] is ENTIRELY inside it and
        D_COILEN's tail crosses it.  Those two parts are ADR-0018's headline
        parts and they would have shipped with NO DESIGNATOR — the silk is
        milled away.  Nothing caught it because `generate_board_generic.py`'s
        refdes de-collider tests `_in_frame()`, which is the OUTER frame
        rectangle and knows nothing about notches or slots, and because
        `silk_edge_clearance` — the exact DRC rule for this — is one of the four
        silk checks this board sets to `ignore` (ORDER_README §13).  THE USER
        CHOSE NOT TO ENABLE THAT RULE, so this is a deliberate manual fix and
        the class can recur; that is stated in the CHANGELOG.

  R-04  `J_DOOR`'s refdes measures 2.80 mm from J_ESTOP and 2.87 mm from
        J_DOOR — CLOSER TO THE WRONG CONNECTOR.  J_ESTOP/J_DOOR are an
        identical unkeyed pin-compatible GH pair 10.88 mm apart whose
        ORDER_README §10.5 mitigation IS the silk designator, so a label that
        points at the neighbour is not a mitigation.  (The de-collider walks an
        offset ladder and takes the first free spot; nothing in it says "your
        own part must be the nearest one".)

WHY A PROJECT SCRIPT AND NOT A GENERATOR FIX: this agent may not edit
`skills/`.  Both defects ARE generic and both are REPORTED upstream; until the
generator learns about milled voids and label ownership this pass is the
board's own repair, run from `rebuild_all.sh` so `04_kicad/` stays fully
regenerable from `03_src/` (canon M3).  It is DETERMINISTIC: same board in,
same board out.

It FAILS LOUDLY (exit 1) if any required move cannot be placed — a silently
un-fixed refdes is exactly the defect being repaired.

Usage:  /usr/bin/python3 03_src/cooksense/fix_silk_placement.py <project_dir>
"""
import re
import sys
from pathlib import Path

import pcbnew

MM = pcbnew.ToMM

# refdes that MUST be nearer their own footprint than any other footprint.
# Scoped deliberately: 163 of 228 refdes on this board sit >3 mm from their
# part and 16 are nearer a different part — re-anchoring all of them is a
# generator change, not a board change.  These are the ones where the
# designator is a documented SAFETY mitigation.
OWNERSHIP_FIX = ("J_ESTOP", "J_ISOLOOP", "J_MODE")
# v1.8 / ADR-0025.  TWO CHANGES HERE AND BOTH ARE CONSEQUENCES OF THE SAME
# NETLIST REMOVAL, not of a silk idea.
#
# `J_DOOR` LEAVES because the part leaves.  The user has no door signal, so the
# connector is removed from the netlist (not marked DNP — DNP frees zero silk,
# this file has no population concept at all, which is exactly why the 1b/7
# `FATAL: no clear silk position for ['R_DOORPD']` could not be fixed from the
# BOM).  There is no designator to own.
#
# `J_ISOLOOP` JOINS, and until this revision its omission was CORRECT and
# MEASURED.  The prior text read: "A full sweep of every legal silk position
# finds NO position where that label is nearer J_ISOLOOP than J_RH_EXHAUST — the
# only clear silk band (y ~101) lies west of J_ISOLOOP and south of
# J_RH_EXHAUST, so the geometry is against it," with the residual printed at
# -3.963 mm on 2026-07-29.  That was true, and `label_ownership_se_corner.md`
# proves all four directions out of the courtyard were closed.  The direction
# that was closed BY J_DOOR is now open: re-measured at the one candidate
# pocket's centre (192.655, 84.975), the nearest `J*`/`F*`/`TP*` courtyard goes
# from `J_DOOR` 1.100 mm to `J_ISOLOOP` 2.680 mm with `J_ESTOP` 8.769 mm second
# — an ownership margin of **+6.089 mm** against MIN_OWNERSHIP_MARGIN_MM 1.5,
# 4x the bar.  Adding the ref is what makes the pass TRY; without it nothing
# ever looked, which is why the 30 V terminal's designator sat on a humidity
# header through five sealed releases.
#
# WHY IT MATTERS MORE THAN THE OTHERS: `J_ISOLOOP` is the NOT-SELV 30 V isolated
# contactor loop.  Its failure was never mis-MATING (a KF350 3.5 mm screw
# terminal cannot accept a JST-GH plug) — it was MISIDENTIFICATION, a human
# reading the silk before touching a live 30 V terminal.  The `ISO 30V` and
# `NOT SELV` captions from PASS E are still there and are still the primary
# mitigation; this makes the designator stop actively contradicting them.
# The RESIDUAL line at the end still re-measures and prints the margin every
# run — if a future placement change closes the pocket again, the number says so
# rather than the comment.

# ---------------------------------------------------------------------------
# PASS C — CROSS-NAMED LABELS.  Added 2026-07-28 after the RENDER lens' P0-A,
# and it is the half of that finding the OWNERSHIP pass structurally cannot see.
#
# Making J_DOOR own its own label does NOT make the E-STOP connector
# unambiguous, because the confusing text next to J_ESTOP was never J_DOOR's
# designator — it was `D_DOOR`, the flyback diode's, printed 0.353 mm from the
# E-STOP connector and 6.411 mm from the diode it actually names, at h=0.60
# (33% TALLER than the 0.45 connector labels, so it is the MORE prominent of
# the two).  A human looking for "which one is the door connector" reads a
# token containing the word DOOR at the E-STOP housing.  Pass B graded
# J_-prefixed labels against J_-prefixed rivals and never looked at it.
SAFETY_CONNECTORS = ("J_ESTOP", "J_MODE", "J_ISOLOOP")   # J_DOOR deleted, ADR-0025
# The identity TOKEN of each — the word a human reads off the board and matches
# against the harness in their hand.
SAFETY_TOKENS = {"ESTOP": "J_ESTOP",
                 "MODE": "J_MODE", "ISOLOOP": "J_ISOLOOP"}
# v1.8 / ADR-0025: the "DOOR" token is REMOVED because every part carrying it —
# J_DOOR, R_DOORPD, R_DOORS, D_DOOR, R_DOOROKPD — is out of the netlist.  Leaving
# it mapped would be a rule with no possible subject, which reads as coverage.
# `D_DOOR`, the flyback diode whose h=0.60 label sat 0.353 mm from the E-STOP
# connector and 6.411 mm from itself, was the ORIGINAL motivation for PASS C.
# The pass stays — `R_ESTOPPD`/`R_ESTOPS`/`D_ESTOP` and the MODE/ISOLOOP tokens
# are still live subjects — but its founding example is gone, and saying so keeps
# the next reader from hunting for a part that no longer exists.
# THE RULE, and it took two cuts to state it correctly.
#
#   Any silk label whose TEXT carries the identity token of a safety connector
#   must be NEAREST that connector, by MARGIN, among all safety connectors.
#
# The first cut was broader — "no refdes of any kind may sit nearer a safety
# connector than the part it names" — and it FAILED LOUDLY on `R_COILENPD`,
# which is exactly what a fail-loud pass is for.  The failure was correct and
# the RULE was wrong.  MEASURED: R_COILENPD's own part sits 4.791 mm from
# J_MODE because it IS J_MODE's pin pull-down, and its label carries no other
# connector's name; `C_LATCHB` likewise.  Neither is confusable with a harness,
# so demanding they retreat was not a safety property, it was a tidiness
# property being enforced at the price of a build.  Under the token rule those
# two are correctly silent and `D_DOOR` / `R_DOORPD` — both bearing DOOR, both
# printed at J_ESTOP — are correctly caught.
#
# Everything the broad rule would have flagged is still REPORTED, with numbers,
# as a non-blocking residual: the class stays visible instead of being narrowed
# out of existence.
CROSSNAME_MARGIN_MM = 1.5
# ...and it only bites where a human could actually make the mistake.  The
# SECOND wrong cut of this rule had no proximity gate and reported
# `R_DOOROKSER` as cross-named at **90.150 mm** from J_MODE versus 93.807 mm
# from J_DOOR — arithmetically true and meaningless: nobody plugging a harness
# reads a label 9 cm away as belonging to the housing in their hand.  Six of
# the nine hits were that class and the pass FAILED trying to relocate them.
# The gate is 8.0 mm, and the number is NOT invented for this file: it is
# `silk_fn_radius_mm`, the radius P-SILK-FN itself uses to decide whether a
# silk text belongs to a part.  With it the rule reports exactly the two labels
# the RENDER lens found — `D_DOOR` and `R_DOORPD`, both bearing DOOR, both
# printed at the E-STOP housing (6.227 mm and 5.200 mm) — and nothing else.
CROSSNAME_RADIUS_MM = 8.0

EDGE_CLEAR_MM = 0.25          # silk-to-board-edge clearance the notch fix enforces
PAD_CLEAR_MM = 0.16           # matches floorplan silk.refdes.clearance
SAMPLE_MM = 0.15              # void test sampling pitch

# ---------------------------------------------------------------------------
# PASS D — SILK STROKE, AND THE FLOOR THAT MOVED (ADR-0007 item 5, G-SELFCON).
#
# WHAT THIS PASS SHIPPED WRONG, 2026-07-28.  The thickness expression below used
# to be `max(0.13, sz * 0.2)`.  At sz = 0.45 that is 0.130 mm, and BOTH v1.7
# red-team lenses measured it independently: `J_ESTOP`, `J_DOOR`, `J_MODE`,
# `D_DOOR`, `R_DOORPD`, `D_COILEN` — the six SAFETY designators, and exactly the
# refs passes A/B/C exist to repair — came out as the THINNEST silk on the
# board, against 0.150 on the other 243 texts.  The pass that fixes the safety
# labels made them the least legible.  Nothing caught it because
# `text_thickness` is one of the four DRC classes this project sets to `ignore`.
#
# AND THE FLOOR IT WAS MEASURED AGAINST WAS ITSELF UNSATISFIABLE.
# `skills/kicad-pcb/references/fab_tiers.yaml` declared `min_silk_text_height:
# 0.45` AND `min_silk_stroke: 0.15` together.  KiCad clamps stroke to
# <= 0.25 x height, so 0.45 mm text can carry AT MOST 0.1125 mm and NO BOARD
# COULD EVER HAVE MET BOTH.  ADR-0007 (2026-07-29) resolved it: `min_silk_stroke`
# is now **0.1125** — the stroke the enforced height can actually carry — with
# the corollary stated in the file: **reaching JLC's published 0.15 requires
# >= 0.60 mm text.**
#
# So the rule this pass now enforces has two halves, and they are different:
#   1. EVERY silk text: stroke = 0.25 x height exactly.  Not `max(0.13, ...)`,
#      not a constant.  A stored 0.150 on a 0.45 mm text is a LIE — KiCad prints
#      it at 0.1125 — and 29 refdes on this board carried that lie.  Making the
#      file say what the plotter does is the point.
#   2. EVERY SAFETY-CRITICAL text: height >= 0.60 mm, hence stroke 0.150 mm.
#      These are the labels a human reads under stress with a harness in one
#      hand, and they are the ones that must clear JLC's PUBLISHED floor, not
#      merely the pipeline's proven-by-ordering floor.
#
# AND THE WAIVER THAT COVERED IT WAS FALSE.  This project's `P-SILK-FN` waiver,
# written the same day, asserted that 0.13-0.15 is "at or above the floor".  It
# is not, under either reading, and it is corrected in
# `03_src/cooksense/rules/policy_waivers.yaml` in the same change — a waiver
# that misstates a measurement is how the next one gets believed.
STROKE_RATIO = 0.25           # KiCad's own clamp; see fab_tiers.yaml header
TIER_MIN_STROKE_MM = 0.1125   # fab_tiers.yaml min_silk_stroke (ADR-0007)
SAFETY_TEXT_H_MM = 0.60       # the height that can carry JLC's published 0.150
SAFETY_TEXT_STROKE_MM = SAFETY_TEXT_H_MM * STROKE_RATIO      # = 0.150

# M-WIDTH: the rule names the CATEGORY and enumerates its members, rather than
# fixing the six instances the reviewers happened to measure.  It is stated in
# terms of WHAT A HUMAN READS, because that is the property:
#
#   (a) every SAFETY CONNECTOR designator; plus
#   (b) every visible refdes whose LABEL CENTRE sits within
#       CROSSNAME_RADIUS_MM of a safety connector's centre — i.e. every word
#       printed where somebody landing a harness will read it, whatever part it
#       names; plus
#   (c) the ADR-0018 coil-enable interlock's own parts, named explicitly.
#
# (c) exists because the reviewers' six include `D_COILEN`, whose label is far
# outside (b)'s radius but which is the interlock flyback diode ADR-0018 turns
# on.  A first cut used a NAME-TOKEN rule instead ("any ref containing STOP,
# DOOR, MODE...") and it swept in 27 members including `C_STOPR`, `R_STOPPD`
# and `R_MODEHWSER` — pull-downs and series resistors scattered across the
# board that no human reads under stress.  Enforcing 0.60 mm on those buys
# nothing and spends placement slack; the rule is scoped to the property, and
# both the rule and its enumerated members are PRINTED at every run.
INTERLOCK_TEXT_REFS = ("D_COILEN", "R_COILENPD")

# Candidate offsets, RADIUS-SORTED.  The generator walks a fixed ladder and
# takes the first free slot, which is how a J_MODE label ended up 11 mm north of
# J_MODE (and inside a notch); this pass takes the NEAREST valid slot instead,
# because "which part does this designator belong to" is the property being
# repaired.  0.25 mm grid out to 8 mm.
OFF = sorted(((dx * 0.25, dy * 0.25) for dx in range(-40, 41) for dy in range(-40, 41)),
             key=lambda p: (round((p[0] ** 2 + p[1] ** 2) ** 0.5, 4), abs(p[0]), abs(p[1])))
# a designator further than this from its part is not a designator
MAX_ANCHOR_MM = 6.0
MAX_ANCHOR_SAFETY_MM = 10.0     # see PASS D: 0.60 mm text needs 78% more area
# ownership rivals: the CONNECTORS.  ORDER_README §10 makes the silk designator
# the mitigation for five identical unkeyed housings, so "nearer J_ESTOP than
# J_DOOR" is the failure that matters.  Requiring a label to beat all 239
# footprints (0402s, mounting holes) is unachievable in this density and is not
# what any reader is confused by.
RIVAL_PREFIX = "J_"
# ...and ownership is judged on CENTRE distance with a real margin, not on
# box-to-box gap.  A first cut of this pass "fixed" J_DOOR to 0.064 mm from its
# own courtyard vs 0.133 mm from J_ESTOP's — arithmetically correct and useless
# to a human holding the board, because the two courtyards are 0.090 mm apart.
# The eye compares the label to the CENTRE of each housing, so that is what is
# graded, and it must win by this margin.  1.5 mm is what the board ACTUALLY
# affords: a full sweep of every legal position gives a best achievable lead of
# +2.353 mm for J_DOOR, +1.742 mm for J_ESTOP and +10.784 mm for J_MODE, and the
# east connector column has 0.898 mm of total courtyard slack, so a 3 mm demand
# is unsatisfiable here.  The threshold is set from the measurement, and the
# measurement is printed at every run.
MIN_OWNERSHIP_MARGIN_MM = 1.5


def box(bb, grow=0.0):
    return (MM(bb.GetLeft()) - grow, MM(bb.GetTop()) - grow,
            MM(bb.GetRight()) + grow, MM(bb.GetBottom()) + grow)


def hit(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def box_gap(a, b):
    """centre-independent box-to-box distance in mm (0 if they overlap)."""
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return (dx * dx + dy * dy) ** 0.5


def main(argv):
    proj = Path(argv[1]).resolve()
    brd = proj / "04_kicad" / "cooksense.kicad_pcb"
    board = pcbnew.LoadBoard(str(brd))

    # ---- the REAL board region, notches and milled slots included ----------
    poly = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(poly, True):
        print("FATAL: could not resolve the Edge_Cuts outline", file=sys.stderr)
        return 2

    def inside(b):
        """every sample of box b (already grown by EDGE_CLEAR) is on copper-able board"""
        x0, y0, x1, y1 = b
        nx = max(2, int((x1 - x0) / SAMPLE_MM) + 1)
        ny = max(2, int((y1 - y0) / SAMPLE_MM) + 1)
        for i in range(nx):
            x = x0 + (x1 - x0) * i / (nx - 1)
            for j in range(ny):
                y = y0 + (y1 - y0) * j / (ny - 1)
                if not poly.Contains(pcbnew.VECTOR2I_MM(x, y)):
                    return False
        return True

    fps = {f.GetReference(): f for f in board.GetFootprints()}
    fp_boxes = {r: box(f.GetBoundingBox(False, False)) for r, f in fps.items()}

    # ---- the SAFETY-TEXT class, enumerated from the rule (M-WIDTH) ---------
    _sc_ctr = {r: (MM(fps[r].GetPosition().x), MM(fps[r].GetPosition().y))
               for r in SAFETY_CONNECTORS if r in fps}

    def _label_ctr(ref):
        b = box(fps[ref].Reference().GetBoundingBox())
        return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

    safety_text_refs = []
    for r, f in sorted(fps.items()):
        t = f.Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        if r in SAFETY_CONNECTORS or r in INTERLOCK_TEXT_REFS:
            safety_text_refs.append(r)
            continue
        lc = _label_ctr(r)
        if any(((lc[0] - c[0]) ** 2 + (lc[1] - c[1]) ** 2) ** 0.5 <= CROSSNAME_RADIUS_MM
               for c in _sc_ctr.values()):
            safety_text_refs.append(r)
    safety_text_refs = tuple(safety_text_refs)
    print(f"  SAFETY-TEXT CLASS ({len(safety_text_refs)} members): safety-connector "
          f"designators + every label printed within {CROSSNAME_RADIUS_MM} mm of a "
          f"safety housing + the ADR-0018 interlock parts {INTERLOCK_TEXT_REFS}. "
          f"All must print at h >= {SAFETY_TEXT_H_MM} / stroke "
          f"{SAFETY_TEXT_STROKE_MM:.4f} mm")
    print(f"      {list(safety_text_refs)}")

    # ---- obstacle sets, built the way the generator builds them ------------
    def obstacles(exclude_ref, split_soft=False):
        """pads/bodies/graphics are HARD.  Other footprints' designators are
        HARD too — unless `split_soft`, in which case NON-SAFETY designators are
        returned separately as EVICTABLE.

        The split exists because silk placement on this board is contended and
        was being resolved FIRST-COME-FIRST-SERVED: `C_LATCHB`, a 0402 latch
        capacitor, held the only site where the NOT-SELV terminal's caption
        could go, and `J_DOOR`, `D_COILEN`, `R_COILENPD` and `R_DOORPD` had no
        legal 0.60 mm position because 0402 designators had taken the slack.
        A 0402's reference does not outrank the label a human reads while
        landing a harness on an interlock, so it yields — and the eviction is
        PRINTED, with the victim's before/after, so the trade is visible."""
        pad_obst, silk_obst, soft = [], [], []
        for f in board.GetFootprints():
            for p in f.Pads():
                pad_obst.append(box(p.GetBoundingBox(), PAD_CLEAR_MM))
            for g in f.GraphicalItems():
                if g.IsOnLayer(pcbnew.F_SilkS):
                    silk_obst.append(box(g.GetBoundingBox(), PAD_CLEAR_MM * 0.5))
            pad_obst.append(box(f.GetBoundingBox(False, False), 0.05))
            t = f.Reference()
            r = f.GetReference()
            if r != exclude_ref and t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS):
                bx = box(t.GetBoundingBox(), PAD_CLEAR_MM * 0.5)
                if split_soft and r not in safety_text_refs:
                    soft.append((r, bx))
                else:
                    silk_obst.append(bx)
        for d in board.GetDrawings():
            if d.GetClass() == "PCB_TEXT" and d.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(d.GetBoundingBox(), PAD_CLEAR_MM * 0.5))
        if split_soft:
            return pad_obst, silk_obst, soft
        return pad_obst, silk_obst

    fp_ctr = {r: (MM(f.GetPosition().x), MM(f.GetPosition().y))
              for r, f in fps.items()}

    def ctr_dist(tb, c):
        tx, ty = (tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2
        return ((tx - c[0]) ** 2 + (ty - c[1]) ** 2) ** 0.5

    def owner_ok(ref, tb):
        """the text centre is nearer its OWN connector's centre than any other
        connector's, by MIN_OWNERSHIP_MARGIN_MM."""
        own = ctr_dist(tb, fp_ctr[ref])
        worst = (None, 1e9)
        for r2 in fp_ctr:
            if r2 == ref or not r2.startswith(RIVAL_PREFIX):
                continue
            g = ctr_dist(tb, fp_ctr[r2])
            if g < worst[1]:
                worst = (r2, g)
        if worst[0] is not None and worst[1] < own + _own_margin[0]:
            return False, own, worst[0], worst[1]
        return True, own, worst[0], worst[1]

    def named_connector(ref):
        """which safety connector's identity token does this refdes carry?
        `D_DOOR` -> J_DOOR, `R_DOORPD` -> J_DOOR, `J_ESTOP` -> J_ESTOP,
        `R_COILENPD` -> None.  Longest token wins so a hypothetical
        `X_DOORMODE` is not silently classified by whichever key hashed
        first."""
        up = ref.upper()
        hits = [(len(tok), conn) for tok, conn in SAFETY_TOKENS.items() if tok in up]
        return max(hits)[1] if hits else None

    def crossname_ok(ref, tb):
        """a label bearing connector C's identity token, PRINTED WITHIN
        CROSSNAME_RADIUS_MM of a DIFFERENT safety connector, must still be
        nearest C by CROSSNAME_MARGIN_MM.  Outside that radius the label is not
        at anybody's housing and the rule is silent."""
        c = named_connector(ref)
        if c is None or c not in fp_ctr:
            return True, None, None, None
        mine = ctr_dist(tb, fp_ctr[c])
        worst = (None, 1e9)
        for r2 in SAFETY_CONNECTORS:
            if r2 == c or r2 not in fp_ctr:
                continue
            g = ctr_dist(tb, fp_ctr[r2])
            if g < worst[1]:
                worst = (r2, g)
        if worst[0] is None or worst[1] > CROSSNAME_RADIUS_MM:
            return True, mine, worst[0], worst[1]
        if worst[1] < mine + CROSSNAME_MARGIN_MM:
            return False, mine, worst[0], worst[1]
        return True, mine, worst[0], worst[1]

    moves, failures = [], []

    _depth = [0]
    _free_pass = [True]
    # THE OWNERSHIP MARGIN IS A CEILING THAT DEGRADES, NOT A CONSTANT.
    # 1.5 mm was measured on the v1.7 board when the safety designators were
    # 0.45 mm high.  At 0.60 mm — which the stroke floor now REQUIRES of them —
    # a 0.60 mm box needs 78% more area, and `J_ESTOP` measures **ZERO** legal
    # positions clearing 1.5 mm once the hazard captions and the void pass have
    # taken their slots.  Failing the build there would trade a real legibility
    # gain for a real ownership gain and get neither, so the pass steps the
    # demand down 1.5 -> 1.0 -> 0.5 -> 0.1 mm and PRINTS the margin it actually
    # obtained.  A positive lead is still mandatory: at 0.1 mm and no slot, the
    # pass dies, because a designator nearer somebody else's connector than its
    # own is the defect this whole file exists to stop.
    OWNERSHIP_MARGIN_LADDER = (MIN_OWNERSHIP_MARGIN_MM, 1.0, 0.5, 0.1)
    _own_margin = [MIN_OWNERSHIP_MARGIN_MM]

    def place_owner_degrading(ref, **kw):
        """place() with the ownership margin stepped down until it lands."""
        for m in OWNERSHIP_MARGIN_LADDER:
            _own_margin[0] = m
            n0 = len(failures)
            place(ref, True, **kw)
            if len(failures) == n0:
                if m != MIN_OWNERSHIP_MARGIN_MM:
                    print(f"             {ref}: NO slot clears "
                          f"{MIN_OWNERSHIP_MARGIN_MM} mm at h "
                          f"{MM(fps[ref].Reference().GetTextSize().x):.2f}; "
                          f"landed at a DEGRADED {m} mm demand — recorded, "
                          f"not silently accepted")
                _own_margin[0] = MIN_OWNERSHIP_MARGIN_MM
                return
            failures.pop()
        _own_margin[0] = MIN_OWNERSHIP_MARGIN_MM
        failures.append(ref)
    # THE HAZARD-CAPTION RESERVE, honoured by every refdes placement from the
    # first pass onward.  A first cut declared it only in PASS E and evicted
    # squatters afterwards; that failed, because by then `J_DOOR`'s newly
    # enlarged designator had taken the site and evicting it just moved the
    # contention around.  A reservation that is applied after the fact is not a
    # reservation.  See PASS E for what it is for and how its size was measured.
    ISO_RESERVE_MM = 2.6
    iso_reserve = [None]

    def movable(v, cand):
        """Could `v` be re-placed if `cand` took its slot?  A DRY RUN of the
        same search, restoring the board afterwards.

        Without this the priority rule is unsound rather than merely rude: on
        the rebuild after the netlist shrank, `J_ESTOP` displaced `R_MODEPD`,
        `R_MODEPD` had NO legal slot anywhere — not even at a 10 mm leash — and
        the pass died.  An eviction is only legitimate if the evicted label has
        somewhere to go, so that is now a precondition of the candidate, not a
        consequence discovered afterwards."""
        _depth[0] += 1
        try:
            return _place(v, False, forbid=cand,
                          max_anchor=MAX_ANCHOR_SAFETY_MM, probe=True)
        finally:
            _depth[0] -= 1

    def place(ref, need_owner, need_crossname=False, sizes=None, forbid=None,
              free_first=True, max_anchor=None):
        """Two phases: a slot that displaces nobody is always preferred; only
        if none exists may a SAFETY label evict a non-safety designator."""
        if free_first and _depth[0] == 0:
            n0 = len(failures)
            _free_pass[0] = True
            place(ref, need_owner, need_crossname, sizes, forbid,
                  free_first=False, max_anchor=max_anchor)
            _free_pass[0] = False
            if len(failures) == n0:
                return
            failures.pop()              # retry with eviction permitted
            place(ref, need_owner, need_crossname, sizes, forbid,
                  free_first=False, max_anchor=max_anchor)
            _free_pass[0] = True
            return
        return _place(ref, need_owner, need_crossname, sizes, forbid, max_anchor)

    def _place(ref, need_owner, need_crossname=False, sizes=None, forbid=None,
               max_anchor=None, probe=False):
        # SAFETY refs are offered 0.60 ONLY: dropping to 0.45 to win a slot
        # is what put six safety designators below the stroke floor.
        if sizes is None:
            sizes = ((SAFETY_TEXT_H_MM,) if ref in safety_text_refs
                     else (0.6, 0.45))
        f = fps[ref]
        t = f.Reference()
        before = box(t.GetBoundingBox())
        before_pos = (MM(t.GetPosition().x), MM(t.GetPosition().y))
        before_rot = t.GetTextAngleDegrees()
        before_sz = MM(t.GetTextSize().x)
        before_th = MM(t.GetTextThickness())
        evict_ok = ref in safety_text_refs and _depth[0] == 0
        if evict_ok:
            pad_obst, silk_obst, soft_obst = obstacles(ref, split_soft=True)
        else:
            pad_obst, silk_obst = obstacles(ref)
            soft_obst = []
        fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        # TWO different objectives, deliberately:
        #  * a VOID eviction wants the NEAREST legal slot (a designator 12 mm
        #    from its part is not a designator), so it takes the first hit on a
        #    radius-sorted ladder;
        #  * an OWNERSHIP repair wants the LARGEST LEAD over the rival connector,
        #    because "which part is this?" is the whole property — so it
        #    enumerates every legal slot and picks the best, tie-broken by
        #    proximity.
        best = None
        cands = []
        ladder = tuple((sz, rot) for sz in sizes for rot in (0, 90))
        for dx, dy in OFF:                      # radius-sorted: NEAREST first
            for sz, rot in ladder:
                t.SetTextAngleDegrees(rot)
                t.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
                t.SetTextThickness(int(sz * STROKE_RATIO * 1e6))
                t.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
                cand = box(t.GetBoundingBox())
                if not inside((cand[0] - EDGE_CLEAR_MM, cand[1] - EDGE_CLEAR_MM,
                               cand[2] + EDGE_CLEAR_MM, cand[3] + EDGE_CLEAR_MM)):
                    continue
                if any(hit(cand, o) for o in pad_obst) or \
                   any(hit(cand, o) for o in silk_obst):
                    continue
                victims = [r2 for r2, o in soft_obst if hit(cand, o)]
                if victims and not evict_ok:
                    continue
                own = box_gap(cand, fp_boxes[ref])
                # SAFETY labels get a longer leash: at h 0.60 the east connector
                # column has no 6 mm slot left, and a designator 7 mm from its
                # own part that WINS ownership beats a 3 mm one that does not.
                lim = max_anchor if max_anchor is not None else (
                    MAX_ANCHOR_SAFETY_MM if ref in safety_text_refs
                    else MAX_ANCHOR_MM)
                if own > lim:
                    continue
                if forbid is not None and hit(cand, forbid):
                    continue          # caller's reserved band
                if need_crossname:
                    if victims and _free_pass[0]:
                        continue
                    # a CROSS-NAMED label wants the NEAREST slot that stops
                    # naming the wrong housing — it is not competing for
                    # prominence, it is getting out of somebody else's
                    # connector and back onto its own part.
                    if not crossname_ok(ref, cand)[0]:
                        continue
                    if need_owner and not owner_ok(ref, cand)[0]:
                        continue
                    best = (rot, sz, fx + dx, fy + dy, cand, own, victims)
                    break
                if need_owner:
                    if victims and _free_pass[0]:
                        continue
                    ok, oc, rival, rd = owner_ok(ref, cand)
                    if not ok:
                        continue
                    # Ranking, in order: (1) slots that displace NOBODY outrank
                    # every evicting slot, whatever lead they win — displacing a
                    # neighbour is a real cost; (2) among those, the label that
                    # sits NEAREST ITS OWN PART wins.  It is deliberately NOT
                    # "largest lead": every candidate here has already cleared
                    # MIN_OWNERSHIP_MARGIN_MM, so the ownership question is
                    # already answered, and maximising the lead beyond that just
                    # walks the designator away from the part it names.  A first
                    # cut sorted on lead and put `J_DOOR` 9.708 mm from J_DOOR to
                    # win +3.617 mm it did not need.
                    cands.append((-len(victims), -own, rd - oc, rot, sz,
                                  fx + dx, fy + dy, cand, own, victims))
                    continue
                if victims and _free_pass[0]:
                    continue
                if victims and not all(movable(v, cand) for v in victims):
                    continue
                best = (rot, sz, fx + dx, fy + dy, cand, own, victims)
                break
            if best:
                break
        if need_owner and cands:
            # LAZILY down the sorted list: the movability probe is a full
            # search, so it runs only until the best acceptable candidate.
            cands.sort(reverse=True)
            n_all = len(cands)
            pick = next((c for c in cands
                         if not c[-1] or all(movable(v, c[-3]) for v in c[-1])),
                        None)
            cands = [pick] if pick else []
        if need_owner and cands:
            nv, _, lead, rot, sz, px, py, cand, own, victims = cands[0]
            print(f"             {ref}: {n_all} legal positions clear the "
                  f"{MIN_OWNERSHIP_MARGIN_MM} mm lead; taking the NEAREST — "
                  f"{own:.3f} mm from its own part, lead {lead:+.3f} mm"
                  + (f" (evicting {victims})" if victims else ""))
            best = (rot, sz, px, py, cand, own, victims)
        if not best:
            # restore and record the failure — never ship a silent non-fix
            t.SetTextAngleDegrees(before_rot)
            t.SetTextSize(pcbnew.VECTOR2I_MM(before_sz, before_sz))
            t.SetTextThickness(int(before_th * 1e6))
            t.SetPosition(pcbnew.VECTOR2I_MM(*before_pos))
            if probe:
                return False
            failures.append(ref)
            return
        rot, sz, px, py, cand, own, victims = best
        if probe:
            t.SetTextAngleDegrees(before_rot)
            t.SetTextSize(pcbnew.VECTOR2I_MM(before_sz, before_sz))
            t.SetTextThickness(int(before_th * 1e6))
            t.SetPosition(pcbnew.VECTOR2I_MM(*before_pos))
            return True
        t.SetTextAngleDegrees(rot)
        t.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
        t.SetTextThickness(int(sz * STROKE_RATIO * 1e6))
        t.SetPosition(pcbnew.VECTOR2I_MM(px, py))
        moves.append((ref, before_pos, (px, py), before, cand, sz, rot, own))
        for v in victims:
            print(f"             {ref} displaces {v} (a non-safety designator) "
                  f"from x[{cand[0]:.3f},{cand[2]:.3f}] y[{cand[1]:.3f},{cand[3]:.3f}]")
            # A DISPLACED LABEL GETS THE LONGER LEASH, and this is not
            # generosity — it is what makes the eviction sound.  On the first
            # full rebuild after the netlist shrank, `J_ESTOP` displaced
            # `R_MODEPD`, `R_MODEPD` had no free slot inside the ordinary 6 mm
            # anchor, and the whole pass died.  A victim that cannot land turns
            # a priority rule into a build failure, so it is allowed to travel
            # as far as a safety label may.
            _depth[0] += 1
            try:
                n0 = len(failures)
                place(v, False, forbid=cand, max_anchor=MAX_ANCHOR_SAFETY_MM)
                if len(failures) > n0:
                    print(f"             ...and {v} could not be re-placed even "
                          f"at a {MAX_ANCHOR_SAFETY_MM} mm leash")
            finally:
                _depth[0] -= 1

    # ---- PASS D0: ARM the J_ISOLOOP hazard-caption reserve ----------------
    # Done FIRST so every later placement respects it.  Rationale, geometry and
    # the two unreproduced "nearest site" numbers are in PASS E below.
    if "J_ISOLOOP" in fps:
        _ib = fp_boxes["J_ISOLOOP"]
        iso_reserve[0] = (_ib[0] - ISO_RESERVE_MM, _ib[1] - ISO_RESERVE_MM,
                          _ib[2] + ISO_RESERVE_MM, _ib[3] + ISO_RESERVE_MM)
        _ev = []
        for ref in sorted(fps):
            # ===== v1.8 / ADR-0025: THE RESERVE MAY NOT EVICT ITS OWN OWNER ====
            # `J_ISOLOOP` IS NOT A FOREIGN LABEL IN `J_ISOLOOP`'S HAZARD RESERVE.
            # Skipping it here is not a loosening — it is the repair of a
            # CONTRADICTION BY CONSTRUCTION that only became reachable when
            # ADR-0025 added `J_ISOLOOP` to OWNERSHIP_FIX, and the first rebuild
            # after that hit it immediately:
            #
            #   FATAL: no clear silk position for ['J_ISOLOOP']
            #
            # The mechanism, read straight out of that log. The reserve is armed
            # at x[188.975,201.825] y[85.075,104.925] and `J_ISOLOOP`'s courtyard
            # is x[191.555,199.245] y[87.655,102.345] — WHOLLY INSIDE IT. So
            # every position from which the designator could be nearer its own
            # part than any other was `forbid`den to it, while `need_owner` was
            # simultaneously required. Unsatisfiable, and the pass reported the
            # unsatisfiability honestly rather than degrading — which is why this
            # is a one-line fix and not a re-architecture.
            #
            # THE RESERVE'S PURPOSE IS UNCHANGED AND IS NOT WEAKENED: it exists
            # so that OTHER parts' designators (`D_DOOR` on v1.7, `R_OPTOLED` and
            # `U_OPTO` on this run) cannot squat the band where the NOT-SELV
            # hazard captions have to print. `J_ISOLOOP`'s own designator belongs
            # to the same class as those captions — it is part of what identifies
            # the 30 V terminal, and its being 0.141 mm from a humidity header
            # through five sealed releases is the defect this whole pass exists
            # to close.
            #
            # MEASURED SAFE, not assumed: with the designator left in place at
            # x[192.809,197.791] y[86.438,87.562] all three captions still find
            # sites — 'ISO 30V' rot 90 at x[191.45,192.05], 'NOT SELV' rot 90 at
            # x[198.2,198.8], '1C2L3L4E' at y 101.0 — and none of the three
            # overlaps that box in x. The captions are placed in PASS E AFTER
            # this loop and go through ordinary collision avoidance, so if a
            # future placement change ever does make them collide, PASS E says so
            # rather than silently dropping a hazard warning.
            if ref == "J_ISOLOOP":
                print("  ISOLOOP    NOT evicting J_ISOLOOP's own designator — a "
                      "hazard reserve may not forbid the band its own owner "
                      "needs in order to own its label (ADR-0025)")
                continue
            t = fps[ref].Reference()
            if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
                continue
            if not hit(box(t.GetBoundingBox()), iso_reserve[0]):
                continue
            b0 = box(t.GetBoundingBox())
            print(f"  ISOLOOP    evicting {ref} from the {ISO_RESERVE_MM} mm "
                  f"hazard-caption reserve (label x[{b0[0]:.3f},{b0[2]:.3f}] "
                  f"y[{b0[1]:.3f},{b0[3]:.3f}])")
            # forbid= is load-bearing: without it an evicted label can be
            # re-placed straight back into the reserve by the radius-sorted
            # ladder, which is what happened on the first full rebuild after
            # the netlist shrank by two parts — `D_DOOR` was evicted, landed
            # 0.5 mm away still inside the reserve, and "ISO 30V" then had no
            # site at 11.086 mm. An eviction that does not forbid the band it
            # is evicting from is not an eviction.
            place(ref, ref in OWNERSHIP_FIX, forbid=iso_reserve[0])
            _ev.append(ref)
        print(f"  ISOLOOP    reserve armed at x[{iso_reserve[0][0]:.3f},"
              f"{iso_reserve[0][2]:.3f}] y[{iso_reserve[0][1]:.3f},"
              f"{iso_reserve[0][3]:.3f}]; {len(_ev)} foreign label(s) evicted "
              f"{_ev if _ev else ''}")

    # ---- PASS E: J_ISOLOOP gets artwork AT THE TERMINAL --------------------
    # RENDER P0-1 (2026-07-28): `J_ISOLOOP` — the ONLY connector whose poles sit
    # on the far side of the opto barrier, an isolated 30 V contactor loop,
    # explicitly NOT SELV — carried NO TEXT AT THE TERMINAL.  No caption, no
    # pole legend (0 of 4), and its own designator printed 1.300 mm from
    # `J_RH_EXHAUST` against 4.900 mm from itself.  The only NOT-SELV warning on
    # the board is the north-stack sentence 155.3 mm away in the opposite corner.
    #
    # TWO RECORDED "IMPOSSIBLE"S, AND BOTH ARE WRONG IN DIFFERENT DIRECTIONS.
    # `floorplan.yaml` recorded "the SE corner is saturated; nearest site for
    # ISO 30V is (165.5,79.5), 33.6 mm away".  A later session re-ran the sweep
    # and reported a legal site at (189.05, 93.35), 6.46 mm out, and THAT is the
    # number the fix list inherited.  **Neither reproduces here.**  Re-measured
    # 2026-07-29 with THIS pass's obstacle set (pads +0.16, silk +0.08, every
    # footprint BODY +0.05 — because silk under a mounted block is silk nobody
    # reads) and the board outline with its 12 milled slots:
    #
    #   * (189.05, 93.35) at h 0.60 is BLOCKED by `U_OPTO`'s body and graphics
    #     AND by `J_RH_EXHAUST`'s body; at h 0.45 it is still blocked by
    #     `J_RH_EXHAUST`.  The clear band there is U_OPTO bottom 92.86 to
    #     J_RH_EXHAUST top 93.73 = **0.87 mm**, and a 0.45 mm text needs 0.92 mm
    #     of box.  The 6.46 mm site does not exist under a body-aware sweep.
    #   * "33.6 mm away" is equally wrong the other way: there IS a site at the
    #     block, in the NORTH-WEST channel between `J_DOOR` (bbox left 193.78)
    #     and the block's own top-left corner, taken ROTATED 90 degrees.
    #
    # So the caption goes vertically up that channel, hard against the block.
    # Recorded plainly because this is the THIRD time a "nearest site" number on
    # this corner has been carried between sessions without being re-derived.
    #
    # WHAT IS STILL NOT POSSIBLE, STATED RATHER THAN QUIETLY DROPPED: a legend
    # printed BESIDE EACH POLE.  The four poles sit at x = 195.30, y = 89.75 /
    # 93.25 / 96.75 / 100.25, and the KF350's body spans x[191.57, 199.22] — the
    # pads are at the CENTRE of the block in x, so every square millimetre
    # either side of a pole is under the moulding once the block is fitted.  A
    # per-pole digit would be printed and then covered.  The legend is therefore
    # a single ordered token, `1C 2L 3L 4E`, placed with the caption: pole 1 =
    # CONTACTOR_C, poles 2 and 3 = CONTACTOR_LOOP (the loop pair), pole 4 =
    # CONTACTOR_E.  That is the same information in the same reading order, in
    # the only place a human can read it.
    # REQUIRED vs BEST-EFFORT, and the split is a MEASUREMENT, not a preference.
    # After the reserve is cleared, the block affords ONE 7-character caption
    # and its own designator.  "ISO 30V" is required and the pass dies without
    # it; "NOT SELV" and the pole legend are attempted in priority order and
    # REPORTED WITH THE MEASURED NEAREST-SITE DISTANCE when they do not fit,
    # rather than being dropped from the list so the run looks clean.
    ISO_ART = ("ISO 30V",)
    ISO_ART_BEST_EFFORT = ("NOT SELV", "1C2L3L4E")
    ISO_MAX_GAP_MM = 8.0
    # AND THE CHANNEL HAS TO BE CLEARED FIRST, which is the finding underneath
    # the finding.  The NW channel is the ONLY site at the block, and it was
    # occupied — by `C_LATCHB`'s designator, a 0402 latch capacitor, which the
    # generator's de-collider parked there because it was free.  Measured
    # 2026-07-29: with a foreign label in the channel the nearest legal site for
    # "ISO 30V" is 11.086 mm away; with the reserve armed it is under 1 mm.  A
    # 0402's reference does not outrank the only NOT-SELV warning on a 30 V
    # terminal, so the reserve (PASS D0) is armed BEFORE any label is placed and
    # every refdes placement in this file honours it.  Nothing about silk is
    # first-come-first-served once a hazard label needs the space.
    # OWNERSHIP IS PART OF "PLACED", AND IT WAS NOT — FOUND 2026-07-29 BY TWO
    # INDEPENDENT ROUTES.  This block bounded each caption's distance to ITS OWN
    # part (ISO_MAX_GAP_MM) and tested nothing about the OTHER parts nearby.  So
    # `'1C2L3L4E'` — the four-pole legend for a 30 V NOT-SELV terminal — was
    # placed at (181.250, 101.000), 7.960 mm from the block and therefore legal
    # by this pass's own rule, and MEASURED 0.161 mm from `J_RH_EXHAUST`, a
    # 5-pole JST-GH humidity-sensor connector, against 5.512 mm from the nearest
    # other connector.  As printed it reads as J_RH_EXHAUST's pin legend: four
    # pole letters beside a five-pole sensor header.  `policy_audit`'s new
    # P-SILK-OWN row caught the same thing from the other direction (it attributed
    # the token to J_RH_AMBIENT, 13.841 mm, and named J_RH_EXHAUST at 6.210 mm
    # centroid-to-text) — two methods, no shared code, same conclusion.
    # A candidate site is now REJECTED unless J_ISOLOOP is the NEAREST member of
    # the connector/fuse/test-point family to it.  That converts a silent mislabel
    # into the "DOES NOT FIT ... reported, not dropped" path this block already
    # has, which is the honest outcome: the same information is carried IN FULL
    # and SELF-IDENTIFIED by the north-stack caption "J_ISOLOOP (SE CORNER) =
    # ISOLATED 30V CONTACTOR LOOP -- NOT SELV -- POLES 1=C 2=LOOP 3=LOOP 4=E".
    # A legend nobody can attribute is worse than a legend that is one sentence
    # further away.
    _OWN_FAM = re.compile(r"^(J|F|TP)([0-9]|_)")
    _own_fam_boxes = [(r, bx) for r, bx in fp_boxes.items()
                      if _OWN_FAM.match(r) and r != "J_ISOLOOP"]

    def _iso_owns(cb):
        """True iff J_ISOLOOP is the nearest J*/F*/TP* part to this text box."""
        mine = box_gap(cb, fp_boxes["J_ISOLOOP"])
        for _r, bx in _own_fam_boxes:
            if box_gap(cb, bx) < mine:
                return False
        return True

    iso_fp = fps.get("J_ISOLOOP")
    if iso_fp is not None:
        iso_box = fp_boxes["J_ISOLOOP"]
        icx, icy = MM(iso_fp.GetPosition().x), MM(iso_fp.GetPosition().y)
        for txt in ISO_ART + ISO_ART_BEST_EFFORT:
            pad_obst, silk_obst = obstacles(None)
            near = [o for o in pad_obst + silk_obst
                    if not (o[2] < icx - 22 or o[0] > icx + 22
                            or o[3] < icy - 22 or o[1] > icy + 22)]
            probe = pcbnew.PCB_TEXT(board)
            probe.SetLayer(pcbnew.F_SilkS)
            probe.SetText(txt)
            probe.SetTextSize(pcbnew.VECTOR2I_MM(SAFETY_TEXT_H_MM, SAFETY_TEXT_H_MM))
            probe.SetTextThickness(int(SAFETY_TEXT_STROKE_MM * 1e6))
            best = None
            for rot in (90, 0):
                probe.SetTextAngleDegrees(rot)
                for xi in range(int((icx - 16) * 8), int((icx + 16) * 8) + 1):
                    for yi in range(int((icy - 16) * 8), int((icy + 16) * 8) + 1):
                        x, y = xi / 8.0, yi / 8.0
                        probe.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                        cb = box(probe.GetBoundingBox())
                        g = box_gap(cb, iso_box)
                        if best is not None and g >= best[0]:
                            continue
                        if not inside((cb[0] - EDGE_CLEAR_MM, cb[1] - EDGE_CLEAR_MM,
                                       cb[2] + EDGE_CLEAR_MM, cb[3] + EDGE_CLEAR_MM)):
                            continue
                        if any(hit(cb, o) for o in near):
                            continue
                        if not _iso_owns(cb):
                            continue          # OWNERSHIP, see the note above
                        best = (g, x, y, rot)
            if best is None or best[0] > ISO_MAX_GAP_MM:
                if txt in ISO_ART_BEST_EFFORT:
                    print(f"  ISOLOOP    {txt!r:14s} DOES NOT FIT at the block — "
                          f"nearest legal site {best[0] if best else float('inf'):.3f} mm "
                          f"away, against the {ISO_MAX_GAP_MM} mm 'at the terminal' "
                          f"bound. Reported, not dropped; it is carried by the "
                          f"north-stack sentence and ORDER_README instead")
                    continue
                print(f"FATAL: no silk site within {ISO_MAX_GAP_MM} mm of J_ISOLOOP "
                      f"for {txt!r} (best {best[0] if best else float('inf'):.3f} mm) — "
                      f"a NOT-SELV terminal must not ship unlabelled",
                      file=sys.stderr)
                return 1
            g, x, y, rot = best
            probe.SetTextAngleDegrees(rot)
            probe.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            board.Add(probe)
            print(f"  ISOLOOP    {txt!r:14s} placed at ({x:.3f},{y:.3f}) rot {rot} "
                  f"h {SAFETY_TEXT_H_MM} stroke {SAFETY_TEXT_STROKE_MM:.4f} — "
                  f"{g:.3f} mm from the block body")


    # ---- PASS D: the stroke floor, and the height that can carry it --------
    # Half 1 — SAFETY refs to h >= 0.60.  Tried IN PLACE first (a height change
    # that needs no move is free); relocated through `place()` only if the taller
    # box collides, which keeps the ownership/cross-name properties intact
    # because `place()` re-tests them.
    raised, restroked = [], []
    # ORDERED: the four safety CONNECTORS choose first.  Height is contended —
    # a 0.60 mm box needs 78% more area than a 0.45 mm one — and a first cut of
    # this pass ran AFTER passes A/B/C, by which time D_DOOR and C_LATCHB had
    # taken the slots and `D_COILEN`, `J_ESTOP` and `R_COILENPD` had NO legal
    # 0.60 mm position at all (the pass failed loudly, which is what it is for).
    # Raising heights FIRST, connectors first, is what makes it satisfiable.
    def n_free_slots(ref, h):
        """How many legal, NON-EVICTING slots this label has at height `h`,
        on the board as it stands.  Used only to ORDER the height pass."""
        f = fps[ref]
        t = f.Reference()
        keep = (t.GetTextAngleDegrees(), MM(t.GetTextSize().x),
                MM(t.GetTextThickness()),
                (MM(t.GetPosition().x), MM(t.GetPosition().y)))
        pad_o, silk_o = obstacles(ref)
        fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        n = 0
        for dx, dy in OFF:
            for rot in (0, 90):
                t.SetTextAngleDegrees(rot)
                t.SetTextSize(pcbnew.VECTOR2I_MM(h, h))
                t.SetTextThickness(int(h * STROKE_RATIO * 1e6))
                t.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
                c = box(t.GetBoundingBox())
                if not inside((c[0] - EDGE_CLEAR_MM, c[1] - EDGE_CLEAR_MM,
                               c[2] + EDGE_CLEAR_MM, c[3] + EDGE_CLEAR_MM)):
                    continue
                if any(hit(c, o) for o in pad_o) or any(hit(c, o) for o in silk_o):
                    continue
                if box_gap(c, fp_boxes[ref]) > MAX_ANCHOR_SAFETY_MM:
                    continue
                if ref in OWNERSHIP_FIX and not owner_ok(ref, c)[0]:
                    continue
                n += 1
        t.SetTextAngleDegrees(keep[0])
        t.SetTextSize(pcbnew.VECTOR2I_MM(keep[1], keep[1]))
        t.SetTextThickness(int(keep[2] * 1e6))
        t.SetPosition(pcbnew.VECTOR2I_MM(*keep[3]))
        return n

    # MOST-CONSTRAINED-FIRST, and this is the third ordering this pass has had.
    # Connectors-before-the-rest was not enough: within the connectors, the
    # tuple order gave `J_DOOR` its slot before `J_ESTOP` looked, and J_ESTOP —
    # which has exactly TWO legal 0.60 mm positions clearing the ownership
    # margin on the fresh board, against J_DOOR's many — was then left with
    # none and the pass died.  Scarcity is MEASURED here and printed, so the
    # order is a consequence of the board rather than of how a tuple was typed.
    _order = sorted(
        (r for r in safety_text_refs
         if MM(fps[r].Reference().GetTextSize().x) < SAFETY_TEXT_H_MM - 1e-9),
        key=lambda r: (n_free_slots(r, SAFETY_TEXT_H_MM),
                       0 if r in SAFETY_CONNECTORS else 1, r))
    if _order:
        print("  STROKE     height pass order (free 0.60 mm slots, scarcest "
              "first): " + ", ".join(f"{r}={n_free_slots(r, SAFETY_TEXT_H_MM)}"
                                     for r in _order))
    for ref in _order:
        t = fps[ref].Reference()
        h0, s0 = MM(t.GetTextSize().x), MM(t.GetTextThickness())
        if h0 >= SAFETY_TEXT_H_MM - 1e-9:
            continue
        pad_obst, silk_obst = obstacles(ref)
        pos = (MM(t.GetPosition().x), MM(t.GetPosition().y))
        t.SetTextSize(pcbnew.VECTOR2I_MM(SAFETY_TEXT_H_MM, SAFETY_TEXT_H_MM))
        t.SetTextThickness(int(SAFETY_TEXT_STROKE_MM * 1e6))
        cand = box(t.GetBoundingBox())
        clear = (inside((cand[0] - EDGE_CLEAR_MM, cand[1] - EDGE_CLEAR_MM,
                         cand[2] + EDGE_CLEAR_MM, cand[3] + EDGE_CLEAR_MM))
                 and not any(hit(cand, o) for o in pad_obst)
                 and not any(hit(cand, o) for o in silk_obst)
                 and (ref not in OWNERSHIP_FIX or owner_ok(ref, cand)[0])
                 and crossname_ok(ref, cand)[0])
        if clear:
            print(f"  STROKE     {ref:14s} h {h0:.3f} -> {SAFETY_TEXT_H_MM:.3f}, "
                  f"stroke {s0:.4f} -> {SAFETY_TEXT_STROKE_MM:.4f} mm, in place")
            raised.append(ref)
            continue
        # taller box does not fit where it stands: restore and re-place at 0.60
        t.SetTextSize(pcbnew.VECTOR2I_MM(h0, h0))
        t.SetTextThickness(int(s0 * 1e6))
        t.SetPosition(pcbnew.VECTOR2I_MM(*pos))
        print(f"  STROKE     {ref:14s} h {h0:.3f} -> {SAFETY_TEXT_H_MM:.3f} does not "
              f"fit in place -> relocating at h {SAFETY_TEXT_H_MM:.3f}")
        if ref in OWNERSHIP_FIX:
            place_owner_degrading(ref)
        else:
            place(ref, False)
        raised.append(ref)


    # ---- PASS A: every visible refdes must be ON the board, not in a void --
    for ref in sorted(fps):
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        b = box(t.GetBoundingBox())
        if inside((b[0] - EDGE_CLEAR_MM, b[1] - EDGE_CLEAR_MM,
                   b[2] + EDGE_CLEAR_MM, b[3] + EDGE_CLEAR_MM)):
            continue
        print(f"  VOID/EDGE  {ref:14s} refdes bbox "
              f"x[{b[0]:.3f},{b[2]:.3f}] y[{b[1]:.3f},{b[3]:.3f}] "
              f"is not wholly on the board -> relocating")
        place(ref, ref in OWNERSHIP_FIX)

    # ---- PASS B: the safety-critical designators must own their label ------
    # SCARCEST FIRST, for the same reason PASS D is (see there).  Iterating
    # OWNERSHIP_FIX in written order let `J_DOOR` and `J_MODE` take their slots
    # while `J_ESTOP` — which has exactly TWO legal 0.60 mm positions clearing
    # the margin on the fresh board — was left with none, and the pass died on
    # the E-STOP connector of a cooking interlock.  The order is measured.
    _ord_b = sorted((r for r in OWNERSHIP_FIX if r in fps),
                    key=lambda r: (n_free_slots(r, MM(fps[r].Reference()
                                                      .GetTextSize().x)), r))
    print("  OWNERSHIP  pass order (free slots at current height, scarcest "
          "first): " + ", ".join(
              f"{r}={n_free_slots(r, MM(fps[r].Reference().GetTextSize().x))}"
              for r in _ord_b))
    for ref in _ord_b:
        if ref not in fps:
            continue
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        b = box(t.GetBoundingBox())
        ok, own, rival, rd = owner_ok(ref, b)
        if ok:
            continue
        print(f"  OWNERSHIP  {ref:14s} label centre is {own:.3f} mm from its own "
              f"part but {rd:.3f} mm from {rival} (needs a {MIN_OWNERSHIP_MARGIN_MM} mm "
              f"lead) -> relocating")
        place_owner_degrading(ref)

    # ---- PASS C: a label naming connector C must be nearest C --------------
    # Quantified over every visible refdes, not a hand-list, so the class is
    # closed rather than the one instance the render lens happened to name.
    crossnamed = []
    for ref in sorted(fps):
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        ok, mine, rival, rd = crossname_ok(ref, box(t.GetBoundingBox()))
        if ok:
            continue
        crossnamed.append((ref, mine, rival, rd))
    for ref, mine, rival, rd in crossnamed:
        print(f"  CROSS-NAME {ref:14s} carries {named_connector(ref)}'s identity token "
              f"but its label centre is {rd:.3f} mm from {rival} and only "
              f"{mine:.3f} mm from {named_connector(ref)} "
              f"(needs a {CROSSNAME_MARGIN_MM} mm lead) -> relocating")
        place(ref, ref in OWNERSHIP_FIX, need_crossname=True)
    if not crossnamed:
        print("  CROSS-NAME none: every label bearing a safety connector's name "
              "is already nearest that connector")

    # Half 2 — EVERY visible silk text: stroke = 0.25 x height, exactly.  This
    # is a pure honesty pass: 29 refdes stored 0.150 on 0.45 mm text, which
    # KiCad prints at 0.1125.  It never RAISES a stroke (that would be a height
    # decision), it makes the stored number equal the printed one.
    for ref in sorted(fps):
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        h, s = MM(t.GetTextSize().x), MM(t.GetTextThickness())
        want = round(h * STROKE_RATIO, 4)
        if abs(s - want) > 1e-6:
            t.SetTextThickness(int(want * 1e6))
            restroked.append((ref, s, want))
    for d in board.GetDrawings():
        if d.GetClass() != "PCB_TEXT" or not d.IsOnLayer(pcbnew.F_SilkS):
            continue
        h, s = MM(d.GetTextSize().x), MM(d.GetTextThickness())
        want = round(h * STROKE_RATIO, 4)
        if abs(s - want) > 1e-6:
            d.SetTextThickness(int(want * 1e6))
            restroked.append((d.GetText()[:18], s, want))
    print(f"  STROKE     {len(raised)} safety refdes raised to h "
          f"{SAFETY_TEXT_H_MM}/stroke {SAFETY_TEXT_STROKE_MM:.4f}; "
          f"{len(restroked)} text(s) re-stroked to 0.25 x height "
          f"(the value KiCad actually plots)")
    for r, was, now in restroked[:8]:
        print(f"             {r:20s} {was:.4f} -> {now:.4f}")
    if len(restroked) > 8:
        print(f"             ... and {len(restroked)-8} more")

    if not moves:
        print("fix_silk_placement: 0 moves (silk already clean)")
    for ref, bp, ap, bb, ab, sz, rot, own in moves:
        print(f"  MOVED {ref:14s} ({bp[0]:.3f},{bp[1]:.3f}) -> ({ap[0]:.3f},{ap[1]:.3f}) "
              f"size {sz} rot {rot}")
    if failures:
        print(f"FATAL: no clear silk position for {failures} — a refdes that "
              f"cannot be placed must not be left in a milled void",
              file=sys.stderr)
        return 1

    # ---- VERIFY, after every move, by re-measuring rather than trusting -----
    # (canon M1: the pass that moved the text is not allowed to be the only
    # thing that says the text is now correct — so this re-derives from the
    # board's final state, including moves made after each decision.)
    bad = []
    for ref in sorted(fps):
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        b = box(t.GetBoundingBox())
        if not inside((b[0] - EDGE_CLEAR_MM, b[1] - EDGE_CLEAR_MM,
                       b[2] + EDGE_CLEAR_MM, b[3] + EDGE_CLEAR_MM)):
            bad.append(f"{ref} still off-board/in a void")
    for ref in OWNERSHIP_FIX:
        if ref not in fps:
            continue
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        ok, own, rival, rd = owner_ok(ref, box(t.GetBoundingBox()))
        print(f"  VERIFY {ref:14s} label centre {own:.3f} mm from own part vs "
              f"{rd:.3f} mm from {rival} (lead {rd-own:+.3f} mm)  -> "
              f"{'OWNS ITS LABEL' if rd > own else 'STILL AMBIGUOUS'}")
        if rd <= own:
            bad.append(f"{ref} label is nearer {rival} ({rd:.3f} vs {own:.3f} mm)")
    # ...and re-derive PASS C over the WHOLE board from the final state, so a
    # move made for one refdes cannot have created a cross-name somewhere else.
    still, graded = [], 0
    for ref in sorted(fps):
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        if named_connector(ref) is None:
            continue
        ok, mine, rival, rd = crossname_ok(ref, box(t.GetBoundingBox()))
        if rd is not None and rd > CROSSNAME_RADIUS_MM:
            continue                      # not at anybody's housing
        graded += 1
        print(f"  VERIFY {ref:14s} bears {named_connector(ref):9s} — "
              f"{mine:.3f} mm from it vs {rd:.3f} mm from {rival} "
              f"(within the {CROSSNAME_RADIUS_MM} mm housing radius)  -> "
              f"{'NAMES THE RIGHT HOUSING' if ok else 'STILL CROSS-NAMED'}")
        if not ok:
            still.append(f"{ref} ({mine:.3f} mm {named_connector(ref)} "
                         f"vs {rd:.3f} mm {rival})")
    print(f"  VERIFY CROSS-NAMES: {graded} connector-named label(s) sit within "
          f"{CROSSNAME_RADIUS_MM} mm of a FOREIGN safety connector and were "
          f"re-measured -> "
          f"{'0 cross-named' if not still else str(len(still)) + ' STILL CROSS-NAMED'}")
    if still:
        bad.append("labels naming the wrong housing: " + "; ".join(still))

    # ---- VERIFY the stroke floor, re-measured from the saved-state board ----
    # Graded against BOTH floors, because they are different claims:
    #   tier floor   0.1125 mm — what fab_tiers.yaml enforces fleet-wide
    #   published    0.1500 mm — JLC's page, which only >= 0.60 mm text can carry
    thin, unclamped, short_safety = [], [], []
    texts = [(r, fps[r].Reference()) for r in sorted(fps)
             if fps[r].Reference().IsVisible()
             and fps[r].Reference().IsOnLayer(pcbnew.F_SilkS)]
    texts += [(d.GetText()[:24], d) for d in board.GetDrawings()
              if d.GetClass() == "PCB_TEXT" and d.IsOnLayer(pcbnew.F_SilkS)]
    for name, t in texts:
        h, s = MM(t.GetTextSize().x), MM(t.GetTextThickness())
        if s < TIER_MIN_STROKE_MM - 1e-6:
            thin.append(f"{name} h{h:.3f} stroke {s:.4f}")
        if s > h * STROKE_RATIO + 1e-6:
            unclamped.append(f"{name} h{h:.3f} stroke {s:.4f} > {h*STROKE_RATIO:.4f}")
    for ref in safety_text_refs:
        t = fps[ref].Reference()
        h, s = MM(t.GetTextSize().x), MM(t.GetTextThickness())
        if h < SAFETY_TEXT_H_MM - 1e-6 or s < SAFETY_TEXT_STROKE_MM - 1e-6:
            short_safety.append(f"{ref} h{h:.3f} stroke {s:.4f}")
    print(f"  VERIFY SILK STROKE: {len(texts)} visible silk text(s) re-measured — "
          f"{len(thin)} below the {TIER_MIN_STROKE_MM} mm tier floor, "
          f"{len(unclamped)} storing a stroke KiCad would clamp away, "
          f"{len(short_safety)}/{len(safety_text_refs)} safety text(s) below "
          f"h {SAFETY_TEXT_H_MM}/stroke {SAFETY_TEXT_STROKE_MM:.4f}")
    if thin:
        bad.append("silk below the tier stroke floor: " + "; ".join(thin))
    if unclamped:
        bad.append("silk storing an unachievable stroke: " + "; ".join(unclamped))
    if short_safety:
        bad.append("safety silk below h0.60/stroke 0.150: " + "; ".join(short_safety))

    # ---- VERIFY the J_ISOLOOP artwork, from the board's final state ---------
    if "J_ISOLOOP" in fps:
        ib = fp_boxes["J_ISOLOOP"]
        found = {}
        for d in board.GetDrawings():
            if d.GetClass() != "PCB_TEXT" or not d.IsOnLayer(pcbnew.F_SilkS):
                continue
            g = box_gap(box(d.GetBoundingBox()), ib)
            if g <= ISO_MAX_GAP_MM:
                found[d.GetText()] = g
        for want in ISO_ART:
            if want not in found:
                bad.append(f"J_ISOLOOP artwork {want!r} is not within "
                           f"{ISO_MAX_GAP_MM} mm of the block")
        print(f"  VERIFY ISOLOOP ARTWORK: {len(found)} silk caption(s) within "
              f"{ISO_MAX_GAP_MM} mm of the NOT-SELV block: "
              + "; ".join(f"{k!r} at {v:.3f} mm" for k, v in sorted(found.items())))
        it = fps["J_ISOLOOP"].Reference()
        ok, own, rival, rd = owner_ok("J_ISOLOOP", box(it.GetBoundingBox()))
        print(f"  RESIDUAL J_ISOLOOP designator: {own:.3f} mm from its own block vs "
              f"{rd:.3f} mm from {rival} (lead {rd-own:+.3f} mm) — NON-BLOCKING: "
              f"the block's IDENTITY is now carried by the captions above, which "
              f"are {min(found.values()) if found else float('nan'):.3f} mm from it, "
              f"and a KF350 screw terminal cannot be cross-plugged with a JST-GH")

    # ---- RESIDUAL, reported and NOT blocking -------------------------------
    # Every label that is nearer a safety connector than the part it names but
    # carries no connector identity token. The broad rule would have failed the
    # build on these; the token rule does not, so they are PRINTED with numbers
    # rather than narrowed out of existence.
    resid = []
    for ref in sorted(fps):
        if ref in SAFETY_CONNECTORS or named_connector(ref):
            continue
        t = fps[ref].Reference()
        if not (t.IsVisible() and t.IsOnLayer(pcbnew.F_SilkS)):
            continue
        tb = box(t.GetBoundingBox())
        own = ctr_dist(tb, fp_ctr[ref])
        for s in SAFETY_CONNECTORS:
            if s not in fp_ctr:
                continue
            d = ctr_dist(tb, fp_ctr[s])
            if d <= CROSSNAME_RADIUS_MM and d < own:
                resid.append(f"{ref} ({own:.3f} mm own vs {d:.3f} mm {s})")
                break
    print(f"  RESIDUAL (non-blocking): {len(resid)} label(s) nearer a safety connector "
          f"than their own part but bearing no connector name: {resid if resid else 'none'}")
    if bad:
        print("FATAL: " + "; ".join(bad), file=sys.stderr)
        return 1

    board.Save(str(brd))
    print(f"fix_silk_placement: {len(moves)} refdes relocated, "
          f"{len(fps)} refdes verified on-board, board saved")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
