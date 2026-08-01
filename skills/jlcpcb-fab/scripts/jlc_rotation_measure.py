#!/usr/bin/env python3
"""MEASURE a per-LCSC rotation offset — the tool the A-ROT block tells you to run.

    jlc_rotation_measure.py BOARD.kicad_pcb REF=LCSC [REF=LCSC ...] \
        [--cache DIR ...] [--row]

A-ROT blocks an export until every placement resolves from a MEASURED row.
This is how a row is made, and it exists so the measurement is not re-invented
(and re-broken) once per board. It reports TWO SEPARATE CHANNELS and never
merges them:

  PAD-NUMBER channel   fit our pads against JLC's cached model matching by pad
                       NUMBER. Fast, usually decisive — and structurally unable
                       to see a model whose own numbering differs from ours.
                       On usb-hub-3s-v3's LEDs it returns 180 at a 17.7x margin
                       and is WRONG (canon A-POL). On crow-rv2's USB-C it
                       returns 90 falsely, because JLC numbers the four SHELL
                       POSTS 1-4 while our pads 1-4 are signal contacts.
                       A HIGH FIT MARGIN IS NOT CONFIDENCE.

  NUMBERING-FREE       decide the same question WITHOUT reading a pad number:
  channel                * PIN-1 BODY MARKINGS — our F.Fab chamfer / silk
                           pin-1 dot vs JLC's, matched mark-to-mark;
                         * LANDMARK SIZE CLASS — group pads by SIZE only and
                           require every class to demand the SAME translation;
                           a wrong angle makes the classes contradict.
                       This is the channel canon A-POL requires to be RECORDED
                       in the row.

The operator is `local_to_board`'s handedness — the one VERIFIED AGAINST PCBNEW
ITSELF (pad.GetFPRelativePosition() vs pad.GetPosition(), exact to 0.000000 mm
over 72 pads) — and NOT `jlc_twin.xform()`'s pre-fix form, which was negated:
invisible at 0/180 and exactly 180 wrong at 90/270, and which populated six
table rows that were all 180 deg out (canon M1 / M-PROV, e0d735c + 1b69760).

`--row` prints a paste-ready `jlc_lcsc_rotations.csv` line with the polarity
column already proposed. READ IT before pasting: where the two channels
DISAGREE, or where the numbering-free channel is DEGENERATE, the tool refuses
to propose `two-channel` and proposes `single-channel` instead — which obliges
the JLC order-preview human gate.
"""
import argparse
import glob
import math
import os
import re
import sys
from pathlib import Path

import pcbnew

TOL = 0.02


def canonical_pad_number(value):
    """Normalize numeric pad labels without changing alphanumeric pin names.

    EasyEDA exports some connector pads as ``01``..``09`` while KiCad stores
    the same terminals as ``1``..``9``.  Treating the formatting zeros as part
    of the electrical identity removes the pad-number channel and used to make
    the verdict path crash while doing arithmetic on ``None``.
    """
    value = str(value).strip().strip('"')
    return str(int(value)) if value.isdigit() else value


def rot(x, y, deg):
    """KiCad's OWN rotation of a footprint-local point (y-down, CCW), the form
    verified against pcbnew over 72 pads. NEVER the negated `xform` form."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (x * c + y * s, -x * s + y * c)


# --------------------------------------------------------------- JLC model
def parse_mod(path):
    """(pads, marks) from a cached EasyEDA/JLC .kicad_mod.

    pads : [{"num","x","y","w","h","shape"}]
    marks: [(x, y, layer)] pin-1 marker CIRCLES only — a small circle outside
           the body is every vendor's pin-1 dot. Lines are body outline and
           carry no orientation on their own.
    """
    t = Path(path).read_text(encoding="utf-8-sig")
    pads = []
    for m in re.finditer(
            r'\(pad\s+("?[^\s")]+"?)\s+(\S+)\s+(\S+)[^)]*?\(at ([-\d.]+) '
            r'([-\d.]+)(?: ([-\d.]+))?\)\s*\(size ([-\d.]+) ([-\d.]+)\)', t):
        pads.append({"num": canonical_pad_number(m.group(1)), "shape": m.group(3),
                     "x": float(m.group(4)), "y": float(m.group(5)),
                     "w": float(m.group(7)), "h": float(m.group(8))})
    marks = []
    for m in re.finditer(r'\(fp_circle \(center ([-\d.]+) ([-\d.]+)\)'
                         r'[^)]*\)[^)]*\(layer ([^)]+)\)', t):
        marks.append((float(m.group(1)), float(m.group(2)),
                      m.group(3).strip('" ')))
    return pads, marks


def find_model(lcsc, roots):
    for r in roots:
        hits = sorted(glob.glob(os.path.join(r, "**", "easyeda", lcsc,
                                             "**", "*.kicad_mod"),
                                recursive=True))
        if hits:
            return hits[0]
    return None


# ------------------------------------------------------------- our footprint
def our_pads(fp):
    out = []
    for p in fp.Pads():
        r = p.GetFPRelativePosition()
        s = p.GetSize()
        out.append({"num": canonical_pad_number(p.GetNumber()),
                    "x": r.x / 1e6, "y": r.y / 1e6,
                    "w": s.x / 1e6, "h": s.y / 1e6})
    return out


def our_marks(fp):
    """Our pin-1 markings, SHAPES only, in the footprint-LOCAL frame. KiCad's
    F.Fab outline is CHAMFERED at pin 1; the chamfer's own corner is the
    marker. A refdes is placed for legibility, not orientation, so text is
    never counted.

    ---- THE FRAME (2026-07-28, smc0985-cooksense J_MODE / C485354) ----------
    `our_pads()` reads `pad.GetFPRelativePosition()`, which is LOCAL — the
    library land, unrotated. A footprint's GRAPHICS have no such accessor on
    this KiCad build (`PCB_SHAPE.GetStart0` does not exist), and
    `GetStart() - fp.GetPosition()` is the BOARD frame, i.e. the local point
    already turned by the placement angle. Mixing the two put the PIN-1-MARK
    channel exactly `board_rot` degrees out of step with every pad channel.

    MEASURED: J_MODE is placed at board_rot 90, so the channel reported its
    minimum at 270 (0.9463 mm) while PAD-NUMBER and PAD-CLOUD both said 180 —
    a DISSENT that is a tool artefact, not a part fact. Un-rotating by
    -board_rot reproduces the .kicad_pcb's own stored local coordinates to
    0.0000 mm and moves that same 0.9463 mm minimum onto 180, where it
    corroborates. Every earlier pin-1-decided row (C6035451, C232798,
    C2762192, C125121) sits at board_rot 0, where the bug is invisible — this
    was the fleet's FIRST non-zero placement to reach the channel.

    A BACK-SIDE placement is additionally mirrored, and this inverse does not
    model that, so a flipped footprint gets NO channel rather than a wrong
    one — the same choice the symmetry guard below makes. Measured 0 flipped
    footprints in 1159 across the 9 fleet boards, so nothing regresses.
    """
    if fp.IsFlipped():
        return []
    brot = fp.GetOrientationDegrees()
    c = fp.GetPosition()
    segs = []
    for d in fp.GraphicalItems():
        if not isinstance(d, pcbnew.PCB_SHAPE):
            continue
        if d.GetLayerName() not in ("F.Fab", "B.Fab"):
            continue
        # KiCad authors an F.Fab body outline EITHER as separate line segments
        # OR as a single closed POLYGON — every SOIC/TSSOP/SSOP land in this
        # fleet uses the polygon form. Reading only GetStart/GetEnd finds
        # nothing there and the channel silently reports "absent", which then
        # reads as "this part HAS no numbering-free channel". A tool gap that
        # looks like a part fact is the worst kind: it would populate the
        # authority table with false SINGLE-CHANNEL declarations.
        pts = []
        try:
            poly = d.GetPolyShape()
            if poly and poly.OutlineCount():
                o = poly.Outline(0)
                pts = [(o.CPoint(i).x, o.CPoint(i).y)
                       for i in range(o.PointCount())]
        except Exception:
            pts = []
        # board-frame offset -> LOCAL, by KiCad's own operator run backwards
        def loc(px, py):
            return rot((px - c.x) / 1e6, (py - c.y) / 1e6, -brot)
        if len(pts) >= 3:
            for i in range(len(pts)):
                a, b = pts[i], pts[(i + 1) % len(pts)]
                segs.append((loc(a[0], a[1]), loc(b[0], b[1])))
            continue
        sp, e = d.GetStart(), d.GetEnd()
        segs.append((loc(sp.x, sp.y), loc(e.x, e.y)))
    if not segs:
        return []
    # ---- SYMMETRY GUARD (2026-07-25, crow-mic-pod-v2 LS1) -------------------
    # A shape that maps onto ITSELF under rotation carries NO orientation
    # information, so it cannot be a pin-1 channel. Without this guard the
    # chamfer search below still returns the furthest corner of a symmetric
    # outline — an ARBITRARY corner — and the caller then reports an exact
    # 0.0000mm match and labels the row `two-channel`, claiming corroboration
    # that does not exist. That is strictly worse than reporting no channel:
    # a wrong answer that LOOKS confirmed. Measured on crow-mic-pod-v2's LS1
    # (CMT-8504 transducer), whose vendored F.Fab is a plain unchamfered
    # square: the tool advised "believe the numbering-free channel: 90", which
    # would have mapped JLC's + drive terminal onto our NC dummy pad and
    # shipped the part soldered and electrically dead. The real channel is the
    # '+' silk mark both libraries carry, and the correct offset is 0.
    pts = []
    for (a, b) in segs:
        pts.extend((a, b))
    if pts:
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        rel = [(p[0] - cx, p[1] - cy) for p in pts]

        def _maps_onto_self(deg):
            th = math.radians(deg)
            co, si = math.cos(th), math.sin(th)
            for (x, y) in rel:
                rx, ry = x * co + y * si, -x * si + y * co
                if not any(abs(rx - u) <= 0.05 and abs(ry - v) <= 0.05
                           for (u, v) in rel):
                    return False
            return True

        for deg in (180, 90):
            if _maps_onto_self(deg):
                # symmetric under `deg` -> cannot distinguish rotations that
                # differ by it. Report NO channel rather than a false one.
                return []
    # the chamfer is the ONE segment that is neither horizontal nor vertical
    out = []
    for (a, b) in segs:
        if abs(a[0] - b[0]) > 0.01 and abs(a[1] - b[1]) > 0.01:
            # the removed corner: (x of one end, y of the other), whichever is
            # further from the centroid
            for corner in ((a[0], b[1]), (b[0], a[1])):
                out.append(corner)
    if out:
        out.sort(key=lambda p: -(p[0] ** 2 + p[1] ** 2))
        return [(out[0][0], out[0][1], "F.Fab chamfer corner")]
    return []


# ------------------------------------------------------------------- fits
def fit_by_number(ours, jlc):
    """{angle: (rms, n)} matching pads by NUMBER, centroid-aligned."""
    on = {p["num"]: p for p in ours}
    jn = {}
    for p in jlc:
        jn.setdefault(p["num"], p)      # first shape wins for split tabs
    common = sorted(set(on) & set(jn))
    if len(common) < 2:
        return {}, common
    res = {}
    for ang in (0, 90, 180, 270):
        jr = {n: rot(jn[n]["x"], jn[n]["y"], ang) for n in common}
        dx = sum(on[n]["x"] - jr[n][0] for n in common) / len(common)
        dy = sum(on[n]["y"] - jr[n][1] for n in common) / len(common)
        res[ang] = (math.sqrt(sum((on[n]["x"] - jr[n][0] - dx) ** 2 +
                                  (on[n]["y"] - jr[n][1] - dy) ** 2
                                  for n in common) / len(common)), len(common))
    return res, common


def fit_by_size_class(ours, jlc):
    """{angle: spread_mm} — group pads by SIZE ONLY (no numbers) and require
    every class to demand the SAME translation. A wrong angle makes the
    classes CONTRADICT each other; the spread IS the contradiction."""
    def classes(ps):
        # keyed on the LONG dimension only, to 0.1mm. Land patterns differ in
        # the short dimension by design (our 1.0mm-wide shell post vs JLC's
        # 1.1mm is a land-vs-model allowance, not a different feature), so a
        # two-dimension key silently loses the channel. The long dimension is
        # what separates the FEATURE FAMILIES (2.1mm post vs 1.8mm post vs
        # 1.15mm contact) and it is read from geometry, never from a number.
        d = {}
        for p in ps:
            d.setdefault(round(max(p["w"], p["h"]), 1), []).append(p)
        return d
    oc, jc = classes(ours), classes(jlc)
    shared = [k for k in oc if k in jc and len(oc[k]) == len(jc[k])]
    if not shared:
        return {}, 0
    res = {}
    for ang in (0, 90, 180, 270):
        deltas = []
        for k in shared:
            ox = sum(p["x"] for p in oc[k]) / len(oc[k])
            oy = sum(p["y"] for p in oc[k]) / len(oc[k])
            jr = [rot(p["x"], p["y"], ang) for p in jc[k]]
            jx = sum(p[0] for p in jr) / len(jr)
            jy = sum(p[1] for p in jr) / len(jr)
            deltas.append((ox - jx, oy - jy))
        cx = sum(d[0] for d in deltas) / len(deltas)
        cy = sum(d[1] for d in deltas) / len(deltas)
        res[ang] = max(math.hypot(d[0] - cx, d[1] - cy) for d in deltas)
    return res, len(shared)


def fit_by_pad_cloud(ours, jlc):
    """{angle: rms_mm} matching pads as an UNLABELLED POINT CLOUD.

    Every pad is matched to the NEAREST JLC pad of the same size class after
    centroid alignment — no pad number is ever read. This is the general
    numbering-free channel: it decides any land whose pad ARRANGEMENT is not
    its own reflection (a 3+2 SOT-553, an L-shaped QFN corner, an offset tab),
    and it goes DEGENERATE — equal at every angle — exactly when the land
    genuinely carries no orientation, which is the honest answer there.
    """
    if len(ours) < 2 or len(jlc) < 2:
        return {}
    def cls(p):
        return (round(min(p["w"], p["h"]), 1), round(max(p["w"], p["h"]), 1))
    ocx = sum(p["x"] for p in ours) / len(ours)
    ocy = sum(p["y"] for p in ours) / len(ours)
    res = {}
    for ang in (0, 90, 180, 270):
        jr = [(rot(p["x"], p["y"], ang), cls(p)) for p in jlc]
        jcx = sum(q[0][0] for q in jr) / len(jr)
        jcy = sum(q[0][1] for q in jr) / len(jr)
        tot, n = 0.0, 0
        for p in ours:
            cands = [q for q in jr if q[1] == cls(p)]
            if not cands:
                cands = jr                      # size class absent: shape-blind
            d = min(math.hypot(q[0][0] - jcx - (p["x"] - ocx),
                               q[0][1] - jcy - (p["y"] - ocy)) for q in cands)
            tot += d * d
            n += 1
        res[ang] = math.sqrt(tot / n)
    return res


def fit_by_pin1_mark(omarks, jmarks):
    """{angle: distance_mm} matching our pin-1 MARKING to JLC's, mark to mark.
    Reads no pad numbers at all."""
    if not omarks or not jmarks:
        return {}, 0
    ox, oy = omarks[0][0], omarks[0][1]
    res = {}
    for ang in (0, 90, 180, 270):
        best = min(math.hypot(rot(m[0], m[1], ang)[0] - ox,
                              rot(m[0], m[1], ang)[1] - oy) for m in jmarks)
        res[ang] = best
    return res, len(jmarks)


def best2(res):
    if not res:
        return None, None, None, None
    order = sorted(res.items(), key=lambda kv: kv[1])
    return order[0][0], order[0][1], order[1][0], order[1][1]


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board")
    ap.add_argument("pairs", nargs="+", help="REF=LCSC")
    ap.add_argument("--cache", action="append", default=[],
                    help="extra dir to search for easyeda/<LCSC>/**.kicad_mod")
    ap.add_argument("--row", action="store_true",
                    help="print a paste-ready jlc_lcsc_rotations.csv line")
    args = ap.parse_args(argv)

    roots = list(args.cache) + [
        str(Path(args.board).resolve().parents[1] / "06_build"),
        str(Path(__file__).resolve().parents[3] / "projects"),
        str(Path(__file__).resolve().parents[3] / "archived_projects"),
        os.path.expanduser("~/.cache/easyeda2kicad"), "/tmp"]

    board = pcbnew.LoadBoard(args.board)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    rc = 0
    for pair in args.pairs:
        ref, _, lcsc = pair.partition("=")
        fp = fps.get(ref)
        if fp is None:
            print(f"{ref}: not on the board")
            rc = 2
            continue
        model = find_model(lcsc, roots)
        if model is None:
            print(f"{ref} {lcsc}: NO cached JLC model found — fetch it with "
                  f"jlc_twin first; a row cannot be made without one")
            rc = 2
            continue
        jpads, jmarks = parse_mod(model)
        opads, omarks = our_pads(fp), our_marks(fp)
        fpname = str(fp.GetFPID().GetLibItemName())
        brot = fp.GetOrientationDegrees()

        num, common = fit_by_number(opads, jpads)
        cls, nshared = fit_by_size_class(opads, jpads)
        cloud = fit_by_pad_cloud(opads, jpads)
        mk, nmk = fit_by_pin1_mark(omarks, jmarks)

        print(f"\n=== {ref}  {lcsc}  {fpname}  board_rot {brot:g}")
        print(f"    model: {model}")
        for label, res, unit in (("PAD-NUMBER  rms", num, "mm"),
                                 ("SIZE-CLASS  spread", cls, "mm"),
                                 ("PAD-CLOUD   rms", cloud, "mm"),
                                 ("PIN-1-MARK  dist", mk, "mm")):
            if not res:
                print(f"    {label:<22} (no channel)")
                continue
            vals = " ".join(f"{a}:{(v[0] if isinstance(v, tuple) else v):8.4f}"
                            for a, v in sorted(res.items()))
            print(f"    {label:<22} {vals}")

        numflat = {a: (v[0] if isinstance(v, tuple) else v)
                   for a, v in num.items()}
        nb, nv, n2, n2v = best2(numflat)
        cb, cv, c2, c2v = best2(cls)
        mb, mv, m2, m2v = best2(mk)
        db, dv, d2, d2v = best2(cloud)

        if nb is None:
            print("    BLOCKED — no common pad-number channel. Check whether "
                  "the two libraries use formatting-only differences or truly "
                  "different terminal names; no rotation row was emitted.")
            rc = 1
            continue

        # ---- the A-POL judgement, stated rather than merged
        free = []
        if cls and c2v > 0 and cv <= TOL and c2v / max(cv, 1e-4) > 3:
            free.append(("size class", cb, cv, c2v))
        # A mark-to-mark match must be CLOSE in absolute terms: the residual
        # is a drawing-style difference (where each library puts its dot),
        # ~1mm, not 2mm+. Without the absolute bar a footprint with any
        # diagonal F.Fab segment — a USB-C shell corner, say — produces a
        # confident and meaningless "pin-1" channel. Ratio alone is not enough.
        if cloud and d2v / max(dv, 1e-4) > 3:
            free.append(("pad cloud", db, dv, d2v))
        # ---- pin-1 MARKING IS NOT NUMBERING-FREE (2026-07-25, usb-hub v1.6) --
        # It matches OUR F.Fab pin-1 chamfer against JLC's fp_circle pin-1 dot.
        # Each library draws its mark at ITS OWN pad 1, so when the two number
        # the part differently BOTH marks move together and the channel
        # CONFIRMS the numbering disagreement it exists to detect. Worse, it
        # used to land in `free` and, being often the only entry, OVERRODE the
        # pad fit. Measured: it proposes 90 for C2296/C2297 (true 0 -> LEDs
        # across their land) and 90 for C2760089/C404363 (true 270 -> all six
        # PowerPAK MOSFETs 180 out).
        # It stays as CORROBORATION — reported, never decisive on its own. A
        # genuine numbering-free mark is one tied to the part's FUNCTION (a
        # cathode band, a '+', a diode-glyph apex, a drain paddle), not to a
        # pad ordinal.
        weak = []
        if mk and m2v / max(mv, 1e-4) > 2 and mv < 1.5:
            weak.append(("pin-1 marking (corroboration only)", mb, mv, m2v))
        # ---- the pad cloud may VETO even when it cannot PROPOSE -------------
        # A degenerate cloud (ratio <= 3) was discarded entirely, throwing away
        # its EXCLUSION power. On the LEDs it refutes 90 at 12.5x and was
        # ignored. Excluding an angle needs far less separation than choosing
        # one: any angle whose cloud residual is >=3x the cloud's own best is
        # REFUTED, and no channel may propose it.
        vetoed = set()
        if cloud:
            for a, v in cloud.items():
                vv = v[0] if isinstance(v, tuple) else v
                if vv >= 3 * max(dv, 1e-4):
                    vetoed.add(a)
        if vetoed:
            dropped = [t for t in free if t[1] in vetoed]
            free = [t for t in free if t[1] not in vetoed]
            for n, a, v, s in dropped:
                print(f"    VETOED  {n} proposed {a} — pad cloud refutes it "
                      f"({(cloud[a][0] if isinstance(cloud[a], tuple) else cloud[a]):.4f}mm "
                      f"vs its own best {dv:.4f}mm)")
            weak = [t for t in weak if t[1] not in vetoed]
        if weak and not free:
            print(f"    pin-1 marking proposes {weak[0][1]} but is NOT a "
                  f"numbering-free channel — not decisive alone")
        if not free:
            pol = "single-channel"
            verdict = (f"NO usable numbering-free channel (size-class "
                       f"{'degenerate' if cls else 'absent'}, pad cloud "
                       f"{'degenerate' if cloud else 'absent'}, pin-1 marking "
                       f"{'inconclusive' if mk else 'absent'}). A-POL: this "
                       f"row is SINGLE-CHANNEL and MUST name the JLC "
                       f"ORDER-PREVIEW human gate.")
            angle = nb
        elif all(a == free[0][1] for _n, a, _v, _s in free) and \
                free[0][1] == nb:
            pol = "two-channel"
            angle = nb
            verdict = ("both channels agree: " +
                       "; ".join(f"{n} -> {a} ({v:.4f}mm vs {s:.4f}mm next)"
                                 for n, a, v, s in free))
        else:
            # A numbering-free channel EXISTS and is decisive, so the row is
            # two-channel — but it DISAGREES with the pad-number fit, which is
            # the A-POL alarm itself. The row keeps the numbering-free answer
            # and is obliged to name the human gate as well.
            pol = "two-channel"
            angle = free[0][1]
            verdict = (f"CHANNELS DISAGREE — pad-NUMBER fit says {nb}, "
                       + "; ".join(f"{n} says {a} ({v:.4f}mm vs {s:.4f}mm "
                                   f"next)" for n, a, v, s in free) +
                       ". A pad-number fit CANNOT see a library that numbers "
                       "the terminals the other way round: BELIEVE THE "
                       "NUMBERING-FREE CHANNEL, resolve against the datasheet "
                       "terminal drawing, and put this code on the JLC "
                       "ORDER-PREVIEW human gate before the first order.")
            rc = 1
        # ---- PIN-1 DISSENT (2026-07-28, C485354) ----------------------------
        # A DECISIVE pin-1 marking that names a DIFFERENT angle from the one
        # this row is about to claim is the A-POL alarm itself: either the two
        # libraries mark pin 1 on opposite terminals, or one of the two marks
        # is drawn wrong. Before this gate the contradiction was printed as
        # four numbers in a channel row and NOTHING ELSE, so noticing it was a
        # human's job — on C485354 a human did notice, and the row still cost a
        # day of arbitration because the report gave no verdict either way.
        # A disagreement now BLOCKS and WITHHOLDS the row: an unresolved row is
        # a better outcome than a confident wrong one.
        dissent = bool(weak) and weak[0][1] != angle
        if dissent:
            print(f"    PIN-1 DISSENT — this row would claim offset {angle}, "
                  f"but the pin-1 marking channel is DECISIVE at "
                  f"{weak[0][1]} ({weak[0][2]:.4f}mm vs {weak[0][3]:.4f}mm "
                  f"next). Resolve against the DATASHEET terminal drawing "
                  f"before any row is written, and put this code on the JLC "
                  f"ORDER-PREVIEW human gate.")
            rc = 1
        print(f"    ==> offset {angle}  polarity={pol}")
        print(f"        {verdict}")
        print(f"        CPL for {ref} = ({brot:g} + {angle}) % 360 = "
              f"{(brot + angle) % 360:g}")
        if args.row:
            ev = (f"{fpname}; measured {__import__('datetime').date.today()} "
                  f"against {Path(model).name} with the pcbnew-verified "
                  f"operator. PAD-NUMBER fit: offset {nb}, rms {nv:.4f}mm vs "
                  f"{n2v:.4f}mm next best over {len(common)} pads. "
                  f"NUMBERING-FREE: {verdict}")
            if dissent:
                print(f'    ROW: (WITHHELD — PIN-1 DISSENT) the fit proposes '
                      f'{angle}; the pin-1 marking says {weak[0][1]}. Nothing '
                      f'here is pasteable until that is settled from the '
                      f'datasheet.')
            elif pol == "single-channel":
                # A SINGLE-CHANNEL row rests on the pad-NUMBER fit alone, and
                # that fit has now been confidently WRONG twice on exactly this
                # class: usb-hub's LEDs (180 at 17.7x, true 0 — JLC numbers
                # pad 1 = ANODE while KiCad's Device:LED is pin 1 = K) and
                # crow-mic-pod's LS1 (a paste-ready `C22359707,90` that would
                # have put JLC's drive terminal on an NC dummy pad — soldered
                # and electrically dead). That row escaped into a sealed
                # archive and had to be quarantined by hand.
                # So: do NOT emit something pasteable. The angle is still
                # printed above for a human to act on WITH the order-preview
                # gate; it must not be copyable into the fleet authority table,
                # because a wrong row there is wrong for every future board.
                print(f'    ROW: (WITHHELD — single-channel) the fit proposes '
                      f'{angle}, but no numbering-free channel confirms it.')
                print(f'         Resolve by MEASURING a FUNCTION-tied mark '
                      f'(cathode band, "+", diode-glyph apex, drain paddle) — '
                      f'NOT a pin-1 dot, which follows pad numbering — then '
                      f'hand-author the row with that evidence and '
                      f'polarity=two-channel.')
            else:
                print(f'    ROW: {lcsc},{angle},"{ev}",{pol}')
    return rc


if __name__ == "__main__":
    sys.exit(main())
