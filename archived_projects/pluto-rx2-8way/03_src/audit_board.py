#!/usr/bin/python3
"""pluto-rx2-8way — the ONE permitted per-board gate (03_src/contracts.md).

WHY IT EXISTS, and it is not to make policy_audit's P-POL/P-KEEP go green.
Six of this board's load-bearing claims are invisible to every SHARED gate,
and each one was named as ungraded in an ADR or in the stage-4 handoff before
this file existed:

  * ADR-0008's 2.0 mm J_USB -> U_ESD proximity. P-ADJ grades `keep_short`
    NET SPANS and ignores `adjacency:` refdes pairs entirely; the netlist is
    byte-identical at 2 mm and at 8 mm. The arithmetic it protects: 6 nH per
    10 mm x 0.5 mm at dI/dt = 24 A/ns is +144 V per leg, which turns a 17 V
    clamp into a 305 V one. A port protected only in the designer's belief.
  * The >= D3.5 mm bottom/inner-plane antipad under every SMA centre barrel.
    It is carried by the FOOTPRINT as a 0.80 mm local pad clearance
    (1.9 + 2 x 0.8 = 3.5), so a footprint substitution or an edit that drops
    the override is silent. Recomputed cost of losing it: RL 14.5 dB vs
    8.9 dB at 6 GHz, i.e. 5.6 dB (stage 2 corrected the brief's ~9 dB).
  * The nine radial arms being EQUAL. Equal length is equal phase BY
    CONSTRUCTION and that is the entire AoA claim (ADR-0006/0007). Nothing in
    the netlist, the DRC or the parity check can see an arm that moved.
  * R_T1/R_T2 at IDENTICAL rotation and RADIAL, with RX1_TAP_MID inside
    lambda_g/20. The stage-3 floorplan had them at the JACK rotation (valid
    only for the 4-fold post square) which measured 2.66 mm against a 1.37 mm
    bound - the pickoff would have stopped being a lumped element on the one
    path this board publishes.
  * LED polarity. The KENTO drawing numbers its terminals OPPOSITE to KiCad's
    footprint, and a reversed LED at V_R 5 V on a 3.3 V rail is DARK AND
    UNDAMAGED: the board arrives, works, and has two dead lights nobody can
    explain.
  * The USB-C mouth. `body_offset` in floorplan.yaml checks the SIGN; this
    checks the vendor DATUM (pad row 6.86 mm inside the y1 edge) and that the
    body actually overhangs.
  * ADDED 2026-07-29 (stage 6) — THREE GROUND VIAS AT THREE PADS (I8). U_SW.1
    (LS, an RF ground per Table 3 fn 1 AND a hard logic 0 per Table 5 fn 1) and
    Y_XTAL.2 / Y_XTAL.4 (the crystal can's return, INSIDE the oscillator loop)
    are sentences about a BARREL, and no pad-to-pad span metric can express
    one: the partner is a plane. PE42482A-X's `SW_LS <= 2 mm` keep_short was
    DELETED for exactly this reason rather than re-pointed at GND, where the
    anchor metric would have measured U_SW.1 -> C_SW1.2 = 6.956 mm, a real
    number about the wrong thing.

Every threshold below is CITED to the ADR or datasheet section that set it.
Run: /usr/bin/python3 03_src/audit_board.py  (from the project root)
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

MM = pcbnew.ToMM
ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / "04_kicad" / "pluto_rx2_8way.kicad_pcb"

FAILS, NOTES = [], []


def fail(cid, msg):
    FAILS.append(f"{cid}: {msg}")


def note(cid, msg):
    NOTES.append(f"{cid}: {msg}")


def pads(fp):
    return {p.GetNumber(): p for p in fp.Pads()}


def xy(p):
    return (MM(p.GetPosition().x), MM(p.GetPosition().y))


def pad_box(p):
    bb = p.GetBoundingBox()
    return (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def box_gap(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def main():
    board = pcbnew.LoadBoard(str(BOARD))
    fps = {f.GetReference(): f for f in board.GetFootprints()}

    # ---------------------------------------------------------------- I1
    # PAD-1 NET POLARITY. Each row is (ref, pad, expected net, why).
    # A polarised part whose pad 1 lands on the wrong net is a part fitted
    # backwards, and on three of these five the board still powers up.
    POLARITY = [
        ("D_TVS",   "1", "VBUS_F",
         "SMBJ6.0A is UNIDIRECTIONAL: pad 1 is the CATHODE (band) and must sit "
         "on the protected node. Reversed it is a forward diode across the rail"),
        ("F_IN",    "1", "VBUS",
         "ADR-0004: the PPTC is the FIRST element on VBUS. Pad 1 toward the "
         "connector is what makes 'upstream of every clamp' true"),
        ("U_ESD",   "5", "VBUS_F",
         "ADR-0008: the array's Transil leg sinks an I/O strike into VBUS_F, "
         "where C_BULK and D_TVS live. On raw VBUS it would be behind F_IN"),
        ("LED_PWR", "1", "GND",
         "KT-0603R's own drawing prints '+' at terminal 1 and KiCad's pad 1 is "
         "the CATHODE. Ballast is on the ANODE side, so pad 1 returns to GND; "
         "reversed, the LED is dark and undamaged and nobody can explain it"),
        ("LED_ST",  "1", "GND", "as LED_PWR"),
    ]
    for ref, pad, want, why in POLARITY:
        f = fps.get(ref)
        if not f:
            fail("I1", f"{ref} not on the board")
            continue
        p = pads(f).get(pad)
        if p is None:
            fail("I1", f"{ref} has no pad {pad}")
            continue
        got = p.GetNetname()
        if got != want:
            fail("I1", f"POLARITY {ref}.{pad} is on {got!r}, expected {want!r} - {why}")
    note("I1", f"{len(POLARITY)} pad-1/polarity nets checked")

    # ---------------------------------------------------------------- I2
    # SMA ANTIPAD. The >=D3.5mm clearing must open in EVERY ground plane
    # under each centre barrel, and it is carried as a per-pad local
    # clearance on pad 1 of the footprint. 1.9mm pad + 2 x 0.8mm = 3.5mm.
    NEED_CLR = 0.80
    jacks = [r for r in fps if r.startswith(("J_ANT", "J_RX"))]
    bad = []
    for r in sorted(jacks):
        p = pads(fps[r]).get("1")
        if p is None:
            bad.append(f"{r}: no pad 1")
            continue
        c = p.GetLocalClearance()
        c = MM(c) if isinstance(c, int) else (MM(c.value) if c is not None and
                                              getattr(c, "value", None) is not None else 0.0)
        if c + 1e-6 < NEED_CLR:
            bad.append(f"{r}.1 local clearance {c:.3f}mm < {NEED_CLR}")
    if bad:
        fail("I2", "SMA bottom-plane antipad < D3.5mm: " + "; ".join(bad) +
             " - worth 5.6 dB of return loss at 6 GHz (RL 14.5 vs 8.9, stage-2 "
             "recompute). No DRC, netlist or parity check can see this")
    note("I2", f"{len(jacks)} SMA centre pins carry the >=D3.5mm antipad override")

    # ---------------------------------------------------------------- I3
    # THE NINE RADIAL ARMS ARE EQUAL. Measured switch-pad-to-jack-pin, which
    # is the quantity ADR-0007 derived (17.85mm at r=20).
    # THIS IS A PLACEMENT PROXY AND SAYS SO, 2026-07-29. It measures PAD
    # CENTRES; phase is a property of COPPER, and the copper is graded by the
    # SHARED gate skills/kicad-pcb/scripts/copper_length_audit.py against the
    # `length_match: RF_RADIAL_STAR` block in 03_src/rules/nets.yaml (canon
    # R-LEN). The two are deliberately different lenses on the same claim: this
    # one reads pcbnew pad positions, that one is an independent
    # s-expression reader over the shipped board text (canon M1).
    # THE +/-0.10mm OBLIGATION THIS NOTE USED TO CARRY IS WITHDRAWN. 0.10mm is
    # 1.3 deg at 6 GHz on this stackup (13.19 deg/mm), which is INSIDE
    # PE42482A-X's own published 13.2 deg part-to-part relative-insertion-phase
    # window (Table 3, PDF p8) and below the ~2 deg per-fillet mounting-
    # inductance asymmetry of ADR-0006(d); KRT has no inter-net skew machinery
    # to deliver it either. ADR-0006 rejected "match all eight to within X mm"
    # in prose from the start - what the board owes is CONSTANCY. The
    # replacement is a 1.0mm DRIFT ceiling plus a pinned measured spread; the
    # full derivation is in nets.yaml's length_match header.
    ARMS = {"ANT1": ("U_SW", "24", "J_ANT1"), "ANT2": ("U_SW", "2", "J_ANT2"),
            "ANT3": ("U_SW", "4", "J_ANT3"), "ANT4": ("U_SW", "6", "J_ANT4"),
            "ANT5": ("U_SW", "13", "J_ANT5"), "ANT6": ("U_SW", "15", "J_ANT6"),
            "ANT7": ("U_SW", "17", "J_ANT7"), "RX2_OUT": ("U_SW", "22", "J_RX2"),
            "RX1_TAP": ("U_SW", "19", "J_ANT8")}
    lens = {}
    for name, (sref, spad, jref) in ARMS.items():
        sp = pads(fps[sref]).get(spad)
        jp = pads(fps[jref]).get("1")
        if sp is None or jp is None:
            fail("I3", f"{name}: missing pad")
            continue
        (ax, ay), (bx, by) = xy(sp), xy(jp)
        lens[name] = math.hypot(ax - bx, ay - by)
    # THE PROPERTY PLACEMENT ACTUALLY OWNS is the JACK RING: ten centre pins
    # at exactly r = 20.000 from the star centre. The pad-centre-to-pin spread
    # below is NOT zero and CANNOT be, because the jacks sit on a CIRCLE and
    # the QFN's pads sit on a SQUARE: pin 24 is at r = 2.274 from the package
    # centre and pin 2 at r = 2.043, a 0.231 mm difference the placement has
    # no way to remove. ADR-0007's "17.85 mm per arm, identical by
    # construction" used r ~= 2.15, the AVERAGE. So this gate measures the
    # ring (which must be exact) and REPORTS the pad-ring residue as the
    # length budget stage 6 has to absorb in copper - equalising ROUTED
    # length, not centre distance, is what makes the phases equal.
    ring_bad = []
    for jref in sorted(set(v[2] for v in ARMS.values()) | {"J_RX1"}):
        jp = pads(fps[jref]).get("1")
        if jp is None:
            ring_bad.append(f"{jref}: no pad 1")
            continue
        x, y = xy(jp)
        r = math.hypot(x - 46.0, y - 46.0)
        if abs(r - 20.0) > 0.005:
            ring_bad.append(f"{jref} r={r:.4f}")
    if ring_bad:
        fail("I3", "jack ring is not r = 20.000: " + "; ".join(ring_bad) +
             " - equal radius is what makes equal length possible at all")
    if lens:
        lo, hi = min(lens.values()), max(lens.values())
        # 0.35mm = the irreducible square-pad-ring residue (0.324 measured)
        # plus 0.03 of slack. Exceeding it means something MOVED.
        if hi - lo > 0.35:
            fail("I3", f"radial arm spread {hi - lo:.3f}mm > 0.35mm "
                       f"({min(lens, key=lens.get)} {lo:.3f} .. "
                       f"{max(lens, key=lens.get)} {hi:.3f}) - larger than the "
                       f"QFN pad-ring residue, so a jack or the switch has moved")
        note("I3", f"{len(lens)} radial arms, pad-to-pad {lo:.3f}..{hi:.3f}mm "
                   f"(spread {hi - lo:.4f}mm = the square-pad-ring residue, "
                   f"{(hi - lo) * 13.19:.2f} deg at 6 GHz). PLACEMENT PROXY: the "
                   f"copper is graded by copper_length_audit.py against "
                   f"length_match: RF_RADIAL_STAR (ceiling 1.0mm of DRIFT "
                   f"spread, not a +/-0.10mm matching target - see nets.yaml)")

    # ---------------------------------------------------------------- I4
    # THE PICKOFF. Identical rotation (never mirrored - ADR-0006(d) calls the
    # ~0.1 nH mounting asymmetry ~2 deg at 6 GHz and a CPL fact), radial, and
    # RX1_TAP_MID inside lambda_g/20 = 1.37mm so it stays a LUMPED element.
    r1, r2 = fps.get("R_T1"), fps.get("R_T2")
    if r1 and r2:
        a1, a2 = r1.GetOrientationDegrees() % 360, r2.GetOrientationDegrees() % 360
        if abs(a1 - a2) > 1e-6:
            fail("I4", f"R_T1 rotation {a1} != R_T2 {a2} - ADR-0006(d) requires "
                       f"IDENTICAL rotation; mirroring turns fillet asymmetry "
                       f"into calibration error on the published path")
        if r1.IsFlipped() != r2.IsFlipped():
            fail("I4", "R_T1/R_T2 are on different sides (mirrored)")
        # radial: the part's long axis must lie along the theta=75 radius
        cx, cy = 46.0, 46.0
        p1, p2 = pads(r1), pads(r2)
        for ref, pd in (("R_T1", p1), ("R_T2", p2)):
            (x1, y1), (x2, y2) = xy(pd["1"]), xy(pd["2"])
            ex, ey = x2 - x1, y2 - y1
            fx, fy = ((x1 + x2) / 2 - cx), ((y1 + y2) / 2 - cy)
            cosang = abs(ex * fx + ey * fy) / (math.hypot(ex, ey) * math.hypot(fx, fy))
            off = math.degrees(math.acos(min(1.0, cosang)))
            if off > 5.0:
                fail("I4", f"{ref} long axis is {off:.1f} deg off the radius - the "
                           f"series pickoff must lie ALONG the arm (the stage-3 "
                           f"floorplan had 60 deg here and measured RX1_TAP_MID "
                           f"at 2.66mm against a 1.37mm bound)")
        mid = [p for f in (r1, r2) for p in f.Pads()
               if p.GetNetname() == "RX1_TAP_MID"]
        if len(mid) == 2:
            (ax, ay), (bx, by) = xy(mid[0]), xy(mid[1])
            span = math.hypot(ax - bx, ay - by)
            if span > 1.37:
                fail("I4", f"RX1_TAP_MID pad span {span:.3f}mm > 1.37mm "
                           f"(lambda_g/20 at 6 GHz, ADR-0006): the two-arm "
                           f"pickoff stops being a lumped element")
            note("I4", f"RX1_TAP_MID pad span {span:.3f}mm (bound 1.37)")
    else:
        fail("I4", "R_T1/R_T2 missing")

    # ---------------------------------------------------------------- I5
    # ADR-0008 PROXIMITY, the one NO shared gate grades. Measured as the
    # quantity ST DocID11265 sec 2.2 actually bounds: PAD-EDGE to PAD-EDGE on
    # the D+/D- legs, not refdes centre to refdes centre (which is
    # unsatisfiable against a connector whose origin is its body centre).
    ADJ = [("J_USB", ["A6", "B6"], "U_ESD", ["1"], 2.0, "USB_DP into the clamp"),
           ("J_USB", ["A7", "B7"], "U_ESD", ["3"], 2.0, "USB_DM into the clamp"),
           ("U_ESD", ["5"], "C_ESD", ["1"], 2.0, "CBUS at the VBUS pin, ST Figure 18"),
           ("J_USB", ["A5"], "R_CC1", ["1"], 4.0, "CC1 pull-down at the contact"),
           ("J_USB", ["B5"], "R_CC2", ["1"], 4.0, "CC2 pull-down at the contact")]
    for ar, ap, br, bp, lim, why in ADJ:
        fa, fb = fps.get(ar), fps.get(br)
        if not fa or not fb:
            fail("I5", f"{ar}/{br} missing")
            continue
        pa = [pads(fa)[n] for n in ap if n in pads(fa)]
        pb = [pads(fb)[n] for n in bp if n in pads(fb)]
        if not pa or not pb:
            fail("I5", f"{ar}{ap}/{br}{bp}: pad not found")
            continue
        g = min(box_gap(pad_box(x), pad_box(y)) for x in pa for y in pb)
        if g > lim + 1e-6:
            fail("I5", f"{ar}{ap} -> {br}{bp} pad gap {g:.3f}mm > {lim}mm ({why}) - "
                       f"6 nH per 10 mm at dI/dt 24 A/ns is +144 V per leg, which "
                       f"turns a 17 V clamp into 305 V")
        else:
            note("I5", f"{ar}{ap} -> {br}{bp} pad gap {g:.3f}mm (bound {lim})")

    # ---------------------------------------------------------------- I6
    # THE USB-C MOUTH AND THE BOARD EDGE. floorplan.yaml's body_offset assert
    # checks the SIGN; this checks the vendor DATUM and the overhang. HRO's
    # RECOMMEND P.C.B LAYOUT puts the PCB EDGE 5.79mm from the alignment-hole
    # line and the pad row 1.07mm from it => 6.86mm pad row to edge.
    j = fps.get("J_USB")
    if j:
        # GetBoardEdgesBoundingBox() includes the Edge.Cuts LINE WIDTH, so the
        # bbox bottom sits half a line beyond the outline centreline. Measured:
        # 92.05 against an outline y1 of 92.00 at edge_width 0.1. Correct for
        # it or the vendor datum reads 0.05 mm long for a cosmetic reason.
        bb = board.GetBoardEdgesBoundingBox()
        ew = max((MM(d.GetWidth()) for d in board.GetDrawings()
                  if d.GetLayer() == pcbnew.Edge_Cuts), default=0.0)
        y1 = MM(bb.GetBottom()) - ew / 2.0
        row = [MM(p.GetPosition().y) for p in j.Pads() if p.GetNumber() == "A6"]
        if row:
            d = y1 - row[0]
            if abs(d - 6.86) > 0.05:
                fail("I6", f"J_USB pad row sits {d:.3f}mm inside the y1 edge, "
                           f"expected 6.86 (= HRO 5.79 alignment-line-to-PCB-EDGE "
                           f"+ 1.07 pad-row-to-alignment-line)")
            note("I6", f"J_USB pad row {d:.3f}mm inside the y1 edge (vendor 6.86)")
        # the BODY, not the bounding box: F.Fab is the 8.94 x 7.35 mm shell
        # outline. The bbox would report the COURTYARD (+4.15) and overstate
        # the overhang by half a millimetre.
        fabys = [MM(g.GetBoundingBox().GetBottom()) for g in j.GraphicalItems()
                 if g.GetLayer() == pcbnew.F_Fab]
        over = (max(fabys) if fabys else MM(j.GetBoundingBox(False, False).GetBottom())) - y1
        if over < 0:
            fail("I6", f"J_USB body ends {-over:.3f}mm INSIDE the board edge - a "
                       f"right-angle receptacle's mouth must reach the edge or a "
                       f"plug cannot seat")
        note("I6", f"J_USB overhangs the y1 edge by {over:.3f}mm")

    # ---------------------------------------------------------------- I7
    # SCREW KEEPOUT. Four M3 through the laminate with ten cabled SMA ports
    # pulling on it: nothing may sit under a washer. 3.2mm hole + M3 washer
    # (7.0mm OD) => 3.5mm radius of reserved surface.
    # Measured on the COURTYARD POLYGON, not its bounding box. The AABB of a
    # 7.5 mm square rotated 45 degrees is 10.6 mm across, which put J_ANT1 and
    # J_RX1 at a phantom 2.50 mm from their corner screws when the real flange
    # metal is 7.16 mm away - the same false-positive class as the generator's
    # P-COLLIDE PINNED-LAP warnings that kicad-cli DRC cleared.
    WASHER_R = 3.5
    holes = [(MM(f.GetPosition().x), MM(f.GetPosition().y))
             for f in board.GetFootprints()
             if f.GetAttributes() & pcbnew.FP_BOARD_ONLY]
    close = []
    for f in board.GetFootprints():
        if f.GetAttributes() & pcbnew.FP_BOARD_ONLY:
            continue
        sp = f.GetCourtyard(pcbnew.F_CrtYd)
        pts = []
        for i in range(sp.OutlineCount()):
            o = sp.Outline(i)
            pts += [(MM(o.CPoint(k).x), MM(o.CPoint(k).y))
                    for k in range(o.PointCount())]
        if not pts:
            b = f.GetBoundingBox(False, False)
            pts = [(MM(b.GetLeft()), MM(b.GetTop())), (MM(b.GetRight()), MM(b.GetBottom()))]
        for hx, hy in holes:
            n = len(pts)
            inside = False
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 > hy) != (y2 > hy) and hx < x1 + (hy - y1) / (y2 - y1 + 1e-12) * (x2 - x1):
                    inside = not inside
            d = 0.0 if inside else min(
                _seg_dist(hx, hy, pts[i][0], pts[i][1],
                          pts[(i + 1) % n][0], pts[(i + 1) % n][1]) for i in range(n))
            if d < WASHER_R:
                close.append(f"{f.GetReference()} {d:.2f}mm")
    if close:
        fail("I7", f"under an M3 washer footprint ({WASHER_R}mm): {close[:8]}")
    note("I7", f"{len(holes)} M3 keepouts clear of all {len(fps)} parts "
               f"(washer radius {WASHER_R}mm)")

    # ---------------------------------------------------------------- I8
    # GROUND VIA *AT* THE PAD — three obligations that are sentences about a
    # VIA, not about a span, and which therefore no pad-to-pad metric can see.
    # ADDED 2026-07-29 (stage 6) when PE42482A-X's `SW_LS <= 2 mm` keep_short
    # was DELETED rather than re-pointed: LS is on GND (ADR-0005), and the
    # anchor metric would have compared U_SW.1 to the nearest other-footprint
    # GND pad, MEASURED at 6.956 mm (C_SW1.2) — a real number about the wrong
    # thing. GND here is a four-layer pour; pin 1 reaches it through a barrel.
    #   * U_SW.1 (LS): Table 3 fn 1 (PDF p9) makes pin 1 an RF ground whose
    #     quality moves IL and isolation, and Table 5 fn 1 (p10) makes it a
    #     logic 0 against a 1 Mohm internal pull-up. 0.5 mm is the figure
    #     ADR-0007's adjacency table and policy_waivers.yaml (c) already
    #     declared for it.
    #   * Y_XTAL.2 / Y_XTAL.4: ABM8-272-T3's own keep_short `why` says "each
    #     GND pad takes its OWN via to L2 at the pad" — the oscillator loop is
    #     XIN -> C2 -> ground -> C3 -> XOUT, so the ground path is IN the loop.
    #     The budget it is written beside (`GND <= 3 mm`) grades the pad span
    #     and PASSES at 2.457/2.291 mm; the per-pad via is the part of the
    #     sentence that span cannot express, and the two vias must be DISTINCT.
    #     1.0 mm: pad half-height 0.40 + via radius 0.125 leaves room for a
    #     neck but not for a trip to a stitch elsewhere.
    # PRE-ROUTE BEHAVIOUR IS STATED, NOT SILENT: on a board with NO vias at all
    # this is UNREACHED and prints as such (canon M-COVER). It cannot be dodged
    # that way — a board with no vias also fails R-THERM and R-DRC.
    VIA_AT_PAD = [("U_SW", "1", 0.5,
                   "LS is an RF ground (Table 3 fn 1) AND a hard logic 0 "
                   "(Table 5 fn 1) - both sentences ask for a barrel at the pad"),
                  ("Y_XTAL", "2", 1.0,
                   "the crystal can's ground return is INSIDE the oscillator "
                   "loop (ABM8 keep_short GND); its own via, not a neck"),
                  ("Y_XTAL", "4", 1.0, "as Y_XTAL.2, and it must be a DIFFERENT via")]
    gnd_vias = [(MM(t.GetPosition().x), MM(t.GetPosition().y))
                for t in board.Tracks()
                if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == "GND"]
    if not gnd_vias:
        note("I8", "UNREACHED: the board carries 0 GND vias, so the three "
                   "via-at-pad obligations (U_SW.1, Y_XTAL.2, Y_XTAL.4) are "
                   "NOT graded here. This is the pre-stitch state; it is a "
                   "FAIL at R-THERM and R-DRC, never a pass here")
    else:
        chosen = {}
        for ref, pn, lim, why in VIA_AT_PAD:
            f = fps.get(ref)
            p = pads(f).get(pn) if f else None
            if p is None:
                fail("I8", f"{ref}.{pn} not on the board")
                continue
            px, py = xy(p)
            d, best = min(((math.hypot(px - vx, py - vy), (vx, vy))
                           for vx, vy in gnd_vias), key=lambda t: t[0])
            if d > lim + 1e-6:
                fail("I8", f"{ref}.{pn}: nearest GND via is {d:.3f}mm away "
                           f"(bound {lim}mm) - {why}")
            else:
                note("I8", f"{ref}.{pn} GND via at {d:.3f}mm (bound {lim})")
            chosen[f"{ref}.{pn}"] = best
        y2, y4 = chosen.get("Y_XTAL.2"), chosen.get("Y_XTAL.4")
        if y2 is not None and y2 == y4:
            fail("I8", f"Y_XTAL pads 2 and 4 share ONE via at {y2} - ABM8's "
                       f"sentence is 'each GND pad takes its own via', because "
                       f"a shared barrel puts both load-capacitor returns "
                       f"through one inductance inside the oscillator loop")
        elif y2 is not None and y4 is not None:
            note("I8", f"Y_XTAL pads 2 and 4 take DISTINCT GND vias "
                       f"({math.hypot(y2[0] - y4[0], y2[1] - y4[1]):.3f}mm apart)")

    # ---------------------------------------------------------------- out
    for n in NOTES:
        print(f"  note {n}")
    if FAILS:
        print(f"AUDIT-BOARD: FAIL ({len(FAILS)})")
        for f in FAILS:
            print(f"  FAIL {f}")
        return 1
    print(f"AUDIT-BOARD: PASS (8 invariant groups, {len(NOTES)} measurements)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
