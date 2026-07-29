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
import sys
from pathlib import Path

import pcbnew

MM = pcbnew.ToMM

# refdes that MUST be nearer their own footprint than any other footprint.
# Scoped deliberately: 163 of 228 refdes on this board sit >3 mm from their
# part and 16 are nearer a different part — re-anchoring all of them is a
# generator change, not a board change.  These are the ones where the
# designator is a documented SAFETY mitigation.
OWNERSHIP_FIX = ("J_DOOR", "J_ESTOP", "J_MODE")
# NOT in that list, and the omission is MEASURED, not an oversight: `J_ISOLOOP`
# was also reported (R-04: its label is 0.80 mm from J_RH_EXHAUST).  A full sweep
# of every legal silk position for it returns 31 candidates and the BEST lead any
# of them achieves is **-2.955 mm** — there is nowhere on this board where that
# label is nearer J_ISOLOOP than J_RH_EXHAUST, because the only clear silk band
# (y ~101) lies west of J_ISOLOOP and south of J_RH_EXHAUST.  It is also not the
# same hazard class: J_ISOLOOP is a KF350 4-pole screw terminal and
# J_RH_EXHAUST is a 5-pin GH — they cannot be cross-plugged into each other, so
# the designator is not a mitigation for anything there.  Recorded as a residual
# P2 rather than "fixed" by moving a label 5 mm and calling it better.

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
SAFETY_CONNECTORS = ("J_ESTOP", "J_DOOR", "J_MODE", "J_ISOLOOP")
# The identity TOKEN of each — the word a human reads off the board and matches
# against the harness in their hand.
SAFETY_TOKENS = {"ESTOP": "J_ESTOP", "DOOR": "J_DOOR",
                 "MODE": "J_MODE", "ISOLOOP": "J_ISOLOOP"}
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

# Candidate offsets, RADIUS-SORTED.  The generator walks a fixed ladder and
# takes the first free slot, which is how a J_MODE label ended up 11 mm north of
# J_MODE (and inside a notch); this pass takes the NEAREST valid slot instead,
# because "which part does this designator belong to" is the property being
# repaired.  0.25 mm grid out to 8 mm.
OFF = sorted(((dx * 0.25, dy * 0.25) for dx in range(-32, 33) for dy in range(-32, 33)),
             key=lambda p: (round((p[0] ** 2 + p[1] ** 2) ** 0.5, 4), abs(p[0]), abs(p[1])))
# a designator further than this from its part is not a designator
MAX_ANCHOR_MM = 6.0
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

    # ---- obstacle sets, built the way the generator builds them ------------
    def obstacles(exclude_ref):
        pad_obst, silk_obst = [], []
        for f in board.GetFootprints():
            for p in f.Pads():
                pad_obst.append(box(p.GetBoundingBox(), PAD_CLEAR_MM))
            for g in f.GraphicalItems():
                if g.IsOnLayer(pcbnew.F_SilkS):
                    silk_obst.append(box(g.GetBoundingBox(), PAD_CLEAR_MM * 0.5))
            pad_obst.append(box(f.GetBoundingBox(False, False), 0.05))
            t = f.Reference()
            if f.GetReference() != exclude_ref and t.IsVisible() \
                    and t.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(t.GetBoundingBox(), PAD_CLEAR_MM * 0.5))
        for d in board.GetDrawings():
            if d.GetClass() == "PCB_TEXT" and d.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(d.GetBoundingBox(), PAD_CLEAR_MM * 0.5))
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
        if worst[0] is not None and worst[1] < own + MIN_OWNERSHIP_MARGIN_MM:
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

    def place(ref, need_owner, need_crossname=False):
        f = fps[ref]
        t = f.Reference()
        before = box(t.GetBoundingBox())
        before_pos = (MM(t.GetPosition().x), MM(t.GetPosition().y))
        before_rot = t.GetTextAngleDegrees()
        before_sz = MM(t.GetTextSize().x)
        pad_obst, silk_obst = obstacles(ref)
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
        for dx, dy in OFF:                      # radius-sorted: NEAREST first
            for sz, rot in ((0.6, 0), (0.6, 90), (0.45, 0), (0.45, 90)):
                t.SetTextAngleDegrees(rot)
                t.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
                t.SetTextThickness(int(max(0.13, sz * 0.2) * 1e6))
                t.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
                cand = box(t.GetBoundingBox())
                if not inside((cand[0] - EDGE_CLEAR_MM, cand[1] - EDGE_CLEAR_MM,
                               cand[2] + EDGE_CLEAR_MM, cand[3] + EDGE_CLEAR_MM)):
                    continue
                if any(hit(cand, o) for o in pad_obst) or \
                   any(hit(cand, o) for o in silk_obst):
                    continue
                own = box_gap(cand, fp_boxes[ref])
                if own > MAX_ANCHOR_MM:
                    continue
                if need_crossname:
                    # a CROSS-NAMED label wants the NEAREST slot that stops
                    # naming the wrong housing — it is not competing for
                    # prominence, it is getting out of somebody else's
                    # connector and back onto its own part.
                    if not crossname_ok(ref, cand)[0]:
                        continue
                    if need_owner and not owner_ok(ref, cand)[0]:
                        continue
                    best = (rot, sz, fx + dx, fy + dy, cand, own)
                    break
                if need_owner:
                    ok, oc, rival, rd = owner_ok(ref, cand)
                    if not ok:
                        continue
                    cands.append((rd - oc, -own, rot, sz, fx + dx, fy + dy, cand, own))
                    continue
                best = (rot, sz, fx + dx, fy + dy, cand, own)
                break
            if best:
                break
        if need_owner and cands:
            cands.sort(reverse=True)
            lead, _, rot, sz, px, py, cand, own = cands[0]
            print(f"             {ref}: {len(cands)} legal positions clear the "
                  f"{MIN_OWNERSHIP_MARGIN_MM} mm lead; best is {lead:+.3f} mm")
            best = (rot, sz, px, py, cand, own)
        if not best:
            # restore and record the failure — never ship a silent non-fix
            t.SetTextAngleDegrees(before_rot)
            t.SetTextSize(pcbnew.VECTOR2I_MM(before_sz, before_sz))
            t.SetPosition(pcbnew.VECTOR2I_MM(*before_pos))
            failures.append(ref)
            return
        rot, sz, px, py, cand, own = best
        t.SetTextAngleDegrees(rot)
        t.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
        t.SetTextThickness(int(max(0.13, sz * 0.2) * 1e6))
        t.SetPosition(pcbnew.VECTOR2I_MM(px, py))
        moves.append((ref, before_pos, (px, py), before, cand, sz, rot, own))

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
    for ref in OWNERSHIP_FIX:
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
        place(ref, True)

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
              f"{rd:.3f} mm from {rival}  -> "
              f"{'OWNS ITS LABEL' if ok else 'STILL AMBIGUOUS'}")
        if not ok:
            bad.append(f"{ref} label is nearer {rival}")
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
