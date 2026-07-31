#!/usr/bin/env python3
"""S-OCCL — schematic text occlusion, measured as GEOMETRY.

usage: /usr/bin/python3 sch_occlusion.py SHEET.kicad_sch [--max N] [--verbose]
                                         [--json OUT]

Grades one `.kicad_sch`: every glyph the sheet draws is placed on the page, and
a finding is raised where a piece of TEXT lands on top of something else — a
second text, a symbol body, a pin line, a ground/power glyph. Exit 1 if the
finding count exceeds `--max` (default 0), or if any drawable object could not
be placed (an unplaced object is not a pass — canon M-COVER).

Consumed by `policy_audit.py` as the S-OCCL row; runnable alone on any sheet.

THE DEFECT THIS REPLACES (MEASURED 2026-07-31). The shipped model, inline in
`policy_audit.py`, built a label's rectangle like this:

    if ang == 180:   # plate extends left of anchor
        items.append((gx - wlen, gy - CH_H / 2, gx, gy + CH_H / 2, ...))
    else:
        items.append((gx,        gy - CH_H / 2, gx + wlen, gy + CH_H / 2, ...))

Two facts about KiCad make that wrong, and both were measured from rendered ink
rather than reasoned about (canon M1 — the emitter must not grade its own
angles; `tests/t1_occlusion.py t_kicad_geometry_is_measured` re-derives the
whole table on every run from `kicad-cli sch export svg`):

  * A global_label's ANGLE selects only the AXIS. KiCad normalises the
    180-degree component away and `justify` ALONE selects the sense:
        (0|180, left)  -> RIGHT      (90|270, left)  -> UP
        (0|180, right) -> LEFT       (90|270, right) -> DOWN
    and a label with NO `justify` renders exactly as `left`.
    So the `else` branch above sends 90 AND 270 — the whole vertical axis — off
    to `+x`, and it reads `justify` nowhere at all, so `(0, 'right')` (a plate
    reaching LEFT) also comes out `+x`.
  * A placed symbol's local geometry is rotated CCW and then y-flipped. The old
    model had no symbol geometry of any kind: bodies, pins and ground glyphs
    were simply not on the page, so a label plate lying across a chip was
    invisible to it.

WHAT THAT COST, on the sheets themselves. Fleet-wide 68 of 1507 global labels
sit at 90/270 and were modelled on the wrong axis. On pluto-rx2-8way-v2 the old
model reads 4 findings before the converter fix at 948ef54d and 4 after, while
3 of the 4 are DIFFERENT findings — it cannot distinguish the broken sheet from
the repaired one. This model reads 88 before and 11 after on the same two
sheets; smc0985-cooksense's interposer goes 58 -> 0.

TWO INHERITED CONSTANTS WERE WRONG AND BOTH ARE NOW MEASURED, one in each
direction, neither chosen to hit a number. Over 347 visible property texts and
386 rendered plates on three real sheets: a plate's CROSS-axis extent is
2.5408 mm exactly, with ZERO spread, against the shipped 2.2 (13% narrow, so
the old model was silent about real overlaps); and a property text's height is
1.0573x its font size, against a shipped HALF-height of 0.9, i.e. a box 70%
TOO TALL — which manufactured findings, and two of this model's own first-draft
findings (`label VMID x Reference R4`, `label VREF2 x Reference C_vref2b`) were
refuted against the render and disappeared when it was corrected. `CH_W` and
`PROP_W` survived the same measurement unchanged.

FALSIFIED IN BOTH DIRECTIONS against `kicad-cli sch export svg`, on four
post-fix sheets, by matching each finding to the objects KiCad actually drew
(a label's PLATE is a 6-point polyline; a property is a `stroked-text` run):
68 of 68 text-vs-text findings CONFIRMED as real ink overlaps, 0 unconfirmed.
The converse sweep — every drawn pair whose ink overlaps that the model did NOT
report — is the declared blind spot below.

VACUITY: PIN NAME and PIN NUMBER text is not placed, so this gate PASSES a
sheet whose pin-name text is completely covered by a label plate. KiCad derives
those positions from the body edge, `pin_names (offset N)`, the hide flags and
the instance rotation, and modelling them wrongly would invent findings on
every board; the honest move is to name the gap. MEASURED by the converse ink
sweep on the post-fix sheets: 4 unreported ink-overlapping pairs on
pluto-rx2-8way-v2, 17 on pluto-cal-switch, 66 on crow-recorder-central-v2, 0 on
crow-mic-pod-v2 — and all but a few are pin-NUMBER against pin-NUMBER inside
one dense auto-generated symbol, a symbol-layout problem rather than a label
one. Fixtured by `tests/t1_occlusion.py t_vac_soccl_pin_name_text_is_not_placed`,
which asserts the gate PASSES a plate laid across a pin's NAME and then FAILS
the same plate moved onto the BODY — the contrast that separates a blind spot
from a fact the model cannot represent.

DECLARED SCOPE LIMIT, and it is the one that matters most on this fleet: this
grades the `.kicad_sch`. Under ADR-0002 Phase A the artifact a HUMAN reads is
tscircuit's own render, shipped as `pdf/schematic.pdf`, and NOTHING grades that
file. A clean verdict here is a statement about the machine artifact and the
KiCad gate stack that reads it, not about the schematic anyone opens. That is
exactly the premise pluto-rx2-8way-v2's withdrawn S-OCCL waiver rested on, and
the reason it was withdrawn was that nobody had checked whether the two files
agreed.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

# ------------------------------------------------------------------ geometry
#: (global_label angle, justify) -> the unit direction its plate REACHES, on a
#: y-DOWN KiCad sheet. MEASURED from `kicad-cli sch export svg` ink, not
#: derived; re-measured every test run.
PLATE_DIR = {(0, "left"): (1, 0), (180, "left"): (1, 0),
             (0, "right"): (-1, 0), (180, "right"): (-1, 0),
             (90, "left"): (0, -1), (270, "left"): (0, -1),
             (90, "right"): (0, 1), (270, "right"): (0, 1)}

#: a global_label with no `justify` renders identically to `justify left`
#: (MEASURED on the same probe sheet, all four angles).
DEFAULT_JUSTIFY = "left"

#: plate metrics, in mm at the 1.27 mm font every emitter here uses.
CH_W = 1.05          # per-char extent ALONG the reach; (len + 2) * CH_W.
                     # MEASURED 0.9751x the rendered plate over 386 real
                     # plates (0.796 - 1.068) — kept, it is the emitter's own
                     # constant and it is right to 2.5%.
CH_H = 2.5408        # extent ACROSS the reach. MEASURED: KiCad draws EXACTLY
                     # 2.5408 mm on all 386, with zero spread. The shipped
                     # model said 2.2 and was 13% narrow.

#: property-text metrics: width per char and HALF-height, each as a fraction
#: of the font size. MEASURED over 347 visible Reference/Value texts on three
#: real sheets: width/(chars*size) = 0.8123 mean (0.390 - 1.010), so 0.82 is
#: right; height/size = 1.0573 mean (1.000 - 1.381), so the HALF-height is
#: 0.53 and the shipped 0.9 made every property box 70% TOO TALL. That is a
#: false-positive source, and it manufactured two of this model's first-draft
#: findings (`label VMID x Reference R4`, `label VREF2 x Reference C_vref2b`),
#: both refuted against the render.
PROP_W = 0.82
PROP_H = 0.53

#: An overlap smaller than this is not one. A label plate ATTACHES at a wire
#: end, which is a pin tip, so an abutment of exactly 0 is the normal case and
#: float noise pushes it either side of zero; 605 of 605 cooksense "findings"
#: in the first draft of this model were that abutment, at 2e-15 mm.
#: The fleet count is FLAT from 1e-6 mm to 0.1 mm (measured), so no verdict on
#: this fleet turns on the value.
OVERLAP_EPS_MM = 0.05


def xf(lx, ly, ang):
    """Symbol-LOCAL (y-up) -> sheet OFFSET from the instance origin (y-down).

    Rotate CCW by `ang` in symbol space, then negate y for the sheet. MEASURED
    against rendered ink for all four rotations with an asymmetric probe
    rectangle (local (1,2)-(7,4) lands at rel (1,-4)-(7,-2) / (-4,-7)-(-2,-1) /
    (-7,2)-(-1,4) / (2,1)-(4,7)); see `t_kicad_geometry_is_measured`.
    """
    if ang == 0:
        return (lx, -ly)
    if ang == 90:
        return (-ly, -lx)
    if ang == 180:
        return (-lx, ly)
    if ang == 270:
        return (ly, lx)
    raise ValueError(f"unmodelled symbol rotation {ang}")


def seg_len_in_box(p, q, box):
    """Length of segment p->q lying inside an axis-aligned box (Liang-Barsky).

    A pin is a LINE, not a rectangle, and giving it a rectangular halo is what
    turned every label's own attachment point into a finding. Asking how much
    of the line the text actually covers answers the real question and makes
    abutment exactly zero.
    """
    x0, y0, x1, y1 = box
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]),
                   (-dy, p[1] - y0), (dy, y1 - p[1])):
        if abs(pp) < 1e-12:
            if qq < 0:
                return 0.0
        else:
            r = qq / pp
            if pp < 0:
                if r > t1:
                    return 0.0
                t0 = max(t0, r)
            else:
                if r < t0:
                    return 0.0
                t1 = min(t1, r)
    return max(0.0, t1 - t0) * math.hypot(dx, dy)


def boxes_overlap(a, b, eps=OVERLAP_EPS_MM):
    return (min(a[2], b[2]) - max(a[0], b[0]) > eps and
            min(a[3], b[3]) - max(a[1], b[1]) > eps)


# ------------------------------------------------------------------- parsing
def _forms(body):
    """Direct s-expression children of a body string, by bracket matching."""
    out, depth, start = [], 0, None
    for i, c in enumerate(body):
        if c == "(":
            if depth == 0:
                start = i
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                out.append(body[start:i + 1])
    return out


def _block(text, head):
    """The full `(head ...)` form, brackets matched, or None."""
    i = text.find(head)
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    return None


_RE_RECT = re.compile(r"\(rectangle \(start ([-\d.]+) ([-\d.]+)\) "
                      r"\(end ([-\d.]+) ([-\d.]+)\)")
_RE_POLY = re.compile(r"\(polyline \(pts ((?:\(xy [-\d.]+ [-\d.]+\)\s*)+)\)")
_RE_XY = re.compile(r"\(xy ([-\d.]+) ([-\d.]+)\)")
_RE_CIRC = re.compile(r"\(circle \(center ([-\d.]+) ([-\d.]+)\) "
                      r"\(radius ([\d.]+)\)")
_RE_PIN = re.compile(r"\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\) "
                     r"\(length ([\d.]+)\)(.*?)\(number \"([^\"]+)\"", re.S)
_RE_INST = re.compile(r"^  \(symbol \(lib_id \"([^\"]+)\"\) "
                      r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)(.*?)^  \)$", re.S | re.M)
_RE_PROP = re.compile(
    r"\(property \"(Reference|Value)\" \"([^\"]*)\" \(at ([-\d.]+) ([-\d.]+) \d+\)\s*"
    r"\(effects \(font \(size ([\d.]+) [\d.]+\)\)(?: \(justify ([\w ]+)\))?(.{0,24}?)\)")
_RE_GLABEL = re.compile(r"\(global_label \"([^\"]*)\"(.{0,240}?)\(uuid", re.S)
_RE_OTHER_LABEL = re.compile(r"^\s*\((label|hierarchical_label|text|text_box) "
                             r"\"([^\"]*)\"", re.M)


def lib_symbols(stxt):
    """lib_symbol name -> {'rects', 'polys', 'pins'} in symbol-local coords."""
    blk = _block(stxt, "(lib_symbols")
    if blk is None:
        return {}
    out = {}
    for sym in _forms(blk[len("(lib_symbols"):-1]):
        nm = re.match(r'\(symbol "([^"]+)"', sym)
        if not nm:
            continue
        g = {"rects": [], "polys": [], "pins": []}
        for r in _RE_RECT.finditer(sym):
            g["rects"].append(tuple(float(r.group(k)) for k in (1, 2, 3, 4)))
        for p in _RE_POLY.finditer(sym):
            g["polys"].append([(float(a), float(b))
                               for a, b in _RE_XY.findall(p.group(1))])
        for c in _RE_CIRC.finditer(sym):
            cx, cy, rr = (float(c.group(k)) for k in (1, 2, 3))
            g["rects"].append((cx - rr, cy - rr, cx + rr, cy + rr))
        for p in _RE_PIN.finditer(sym):
            g["pins"].append((float(p.group(1)), float(p.group(2)),
                              int(p.group(3)), float(p.group(4)),
                              p.group(6), " hide" in p.group(5)))
        out[nm.group(1)] = g
    return out


def _justify_sense(raw):
    """`(justify left top)` -> 'left'. Only left/right selects the sense."""
    for tok in (raw or "").split():
        if tok in ("left", "right"):
            return tok
    return DEFAULT_JUSTIFY


def _prop_box(txt, gx, gy, fs, just):
    w = len(txt) * fs * PROP_W
    if just == "right":
        return (gx - w, gy - fs * PROP_H, gx, gy + fs * PROP_H)
    if just == "left":
        return (gx, gy - fs * PROP_H, gx + w, gy + fs * PROP_H)
    return (gx - w / 2, gy - fs * PROP_H, gx + w / 2, gy + fs * PROP_H)


def plate_box(name, gx, gy, ang, just):
    """The rectangle a global_label's plate occupies, from its ANCHOR."""
    ux, uy = PLATE_DIR[(ang, just)]
    reach = (len(name) + 2) * CH_W
    if ux:
        return (min(gx, gx + ux * reach), gy - CH_H / 2,
                max(gx, gx + ux * reach), gy + CH_H / 2)
    return (gx - CH_H / 2, min(gy, gy + uy * reach),
            gx + CH_H / 2, max(gy, gy + uy * reach))


def parse_sheet(stxt):
    """-> (texts, rects, segs, unmodelled, total)

    texts  [(box, desc, owner)]   things that must stay legible
    rects  [(box, desc, owner)]   filled/outlined body graphics
    segs   [((p,q), desc, owner)] pin lines and glyph polylines
    unmodelled [str]              drawable objects this model could not place
    total  int                    every drawable object it met
    """
    libs = lib_symbols(stxt)
    texts, rects, segs, unmodelled = [], [], [], []
    total = 0

    body = stxt
    lb = _block(stxt, "(lib_symbols")
    if lb:                       # prototypes all sit at the same local coords
        body = stxt.replace(lb, "")   # and would be pure false positives

    for m in _RE_GLABEL.finditer(body):
        total += 1
        name, blk = m.group(1), m.group(2)
        am = re.search(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
        if not am:
            unmodelled.append(f"global_label {name!r}: no (at ...)")
            continue
        jm = re.search(r"\(justify ([\w ]+)\)", blk)
        gx, gy, ang = (float(am.group(1)), float(am.group(2)), int(am.group(3)))
        just = _justify_sense(jm.group(1) if jm else None)
        if (ang, just) not in PLATE_DIR:
            unmodelled.append(f"global_label {name!r}: "
                              f"(angle {ang}, justify {just})")
            continue
        texts.append((plate_box(name, gx, gy, ang, just), f"label {name}", None))

    for m in _RE_OTHER_LABEL.finditer(body):
        total += 1
        unmodelled.append(f"{m.group(1)} {m.group(2)!r}: this model places "
                          f"global_label only")

    for im in _RE_INST.finditer(body):
        total += 1
        lib, ix, iy, iang, blk = (im.group(1), float(im.group(2)),
                                  float(im.group(3)), int(im.group(4)),
                                  im.group(5))
        refm = re.search(r'\(property "Reference" "([^"]*)"', blk)
        ref = refm.group(1) if refm else lib.split(":", 1)[-1]
        for pm in _RE_PROP.finditer(blk):
            kind, txt, gx, gy, fs, just, tail = (
                pm.group(1), pm.group(2), float(pm.group(3)),
                float(pm.group(4)), float(pm.group(5)), pm.group(6),
                pm.group(7))
            if "hide" in tail or not txt:
                continue
            # a property with NO justify is CENTRED on its anchor (unlike a
            # global_label, whose absent justify renders as `left`)
            side = next((t for t in (just or "").split()
                         if t in ("left", "right")), None)
            texts.append((_prop_box(txt, gx, gy, fs, side),
                          f"{kind} {txt}", ref))
        g = libs.get(lib) or libs.get(lib.split(":", 1)[-1])
        if g is None:
            unmodelled.append(f"symbol {ref}: no lib_symbol {lib!r} on the sheet")
            continue
        if re.search(r"\(mirror \w+\)", blk):
            unmodelled.append(f"symbol {ref}: mirrored")
            continue
        if iang not in (0, 90, 180, 270):
            unmodelled.append(f"symbol {ref}: rotation {iang}")
            continue
        for (x0, y0, x1, y1) in g["rects"]:
            pts = [xf(x, y, iang)
                   for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            xs = [ix + p[0] for p in pts]
            ys = [iy + p[1] for p in pts]
            rects.append(((min(xs), min(ys), max(xs), max(ys)),
                          f"body {ref}", ref))
        for poly in g["polys"]:
            pts = [(ix + xf(x, y, iang)[0], iy + xf(x, y, iang)[1])
                   for x, y in poly]
            for k in range(len(pts) - 1):
                segs.append(((pts[k], pts[k + 1]), f"glyph {ref}", ref))
        for (px, py, pang, plen, pnum, phide) in g["pins"]:
            if phide or plen <= 0:
                continue
            ex = px + plen * math.cos(math.radians(pang))
            ey = py + plen * math.sin(math.radians(pang))
            a, b = xf(px, py, iang), xf(ex, ey, iang)
            segs.append((((ix + a[0], iy + a[1]), (ix + b[0], iy + b[1])),
                         f"pin {ref}.{pnum}", ref))
    return texts, rects, segs, unmodelled, total


# ------------------------------------------------------------------- grading
def occlusions(stxt):
    """-> (sorted findings, unmodelled, graded, total)

    A finding is one (text, other) PAIR. A ground glyph is four segments and a
    text lying on it is ONE finding, not four.
    """
    texts, rects, segs, unmodelled, total = parse_sheet(stxt)
    found = set()
    for i, (tb, td, towner) in enumerate(texts):
        for ob, od, _ in texts[i + 1:]:
            if boxes_overlap(tb, ob):
                found.add((td, od))
        for ob, od, oowner in rects:
            if towner is not None and towner == oowner:
                continue           # a symbol's own Reference beside its own box
            if boxes_overlap(tb, ob):
                found.add((td, od))
        for (p, q), od, oowner in segs:
            if towner is not None and towner == oowner:
                continue
            if seg_len_in_box(p, q, tb) > OVERLAP_EPS_MM:
                found.add((td, od))
    graded = total - len(unmodelled)
    return sorted(f"{a} x {b}" for a, b in found), unmodelled, graded, total


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sheet", help="the .kicad_sch graded")
    ap.add_argument("--max", type=int, default=0,
                    help="permitted finding count (default 0)")
    ap.add_argument("--verbose", action="store_true",
                    help="print every finding, not the first 12")
    ap.add_argument("--json", default="", help="write the findings here")
    a = ap.parse_args(argv)
    p = Path(a.sheet)
    if not p.is_file():
        print(f"S-OCCL FAIL: no such sheet: {p}")
        return 2
    occl, unm, graded, total = occlusions(p.read_text(encoding="utf-8-sig"))
    print(f"S-OCCL: graded {graded} of {total} drawable object(s) on {p}")
    for f in (occl if a.verbose else occl[:12]):
        print(f"  OCCLUDED  {f}")
    if occl and not a.verbose and len(occl) > 12:
        print(f"  ... and {len(occl) - 12} more (--verbose for all)")
    for u in unm:
        print(f"  UNPLACED  {u}")
    if a.json:
        Path(a.json).write_text(json.dumps(
            {"sheet": str(p), "occlusions": occl, "unmodelled": unm,
             "graded": graded, "total": total}, indent=1), encoding="utf-8")
    if unm:
        print(f"S-OCCL FAIL: {len(unm)} drawable object(s) could not be placed "
              f"— an ungraded glyph is not a clear one (canon M-COVER)")
        return 1
    if len(occl) > a.max:
        print(f"S-OCCL FAIL: {len(occl)} text occlusion(s) (<= {a.max})")
        return 1
    print(f"S-OCCL PASS: {len(occl)} text occlusion(s) (<= {a.max})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
