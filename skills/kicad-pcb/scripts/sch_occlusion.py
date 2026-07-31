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
the repaired one.

=====================================================================
THE WIDTH MODEL WAS A FIXED-WIDTH MODEL OVER A PROPORTIONAL FONT
(MEASURED 2026-07-31, and it is the FOURTH inherited constant in this file
found wrong)
=====================================================================

`CH_W = 1.05` charged every character the same 1.05 mm and built a plate as
`(len(name) + 2) * CH_W`. KiCad's stroke font is PROPORTIONAL. DERIVED HERE,
independently, from 294 plates KiCad rendered itself (98 characters x 3 name
lengths, `scratchpad/derive.py` -> `t_kicad_geometry_is_measured`): every
character's advance is an EXACT integer twenty-first of the font size, k from
8 (`` ` ``) to 28 (`m`) — a 3.5x spread the flat model cannot represent. The
residual against integer k is below 0.0008 mm on all 98, which is the SVG's own
4-decimal quantisation and nothing else.

The flat model therefore errs in BOTH directions, and one of them is fatal:

    IIII                    flat 6.300 mm   true 3.753 mm   +2.547 too WIDE
    MMMMMMMM                flat 10.500     true 12.945     -2.445 too NARROW
    3V3_ANALOG_SENSE_RTN    flat 22.050     true 26.518     -4.468 too NARROW
    (the fleet's longest, 20 chars of capitals)

Too WIDE invents findings. Too NARROW makes a REAL ink composite INVISIBLE —
the gate reports a clean sheet while KiCad draws one plate through another —
and that is the direction the fleet's own names take it: 1507 global labels
over 8 sheets are drawn from `[0-9A-Z_]` only, whose advances run 20/21 and
21/21 and 22/21 of the font size against a flat model charging 1.05/1.27 =
17.4/21. THE FLAT MODEL IS TOO NARROW FOR EVERY CAPITAL LETTER IN THE FLEET.

INDEPENDENCE (canon M1). `circuit_json_to_kicad_sch.py` carries its own k/21
table, derived by the agent that wrote the de-collision pass. This one was
derived from scratch against `kicad-cli sch export svg` WITHOUT reading it,
because a checker that inherits the checked module's table is not a second
measurement. The two AGREE on all 95 printable ASCII characters. This table
additionally measures `°` (16/21), `µ` (22/21) and `Ω` (24/21) — and `Ω`
appears in fleet property text, where the converter's table would have to fall
back on its widest entry.

THREE MORE THINGS THE OLD MODEL COULD NOT SEE, all measured in the same sweep:

  * PLATE SHAPE. `PLATE_BASE` is not one number. MEASURED at three font sizes
    x three name lengths: `passive` 1.3341 mm, `input`/`output` 2.4454 mm,
    `bidirectional`/`tri_state` 3.5567 mm at the 1.27 mm font — the arrow point
    is part of the reach. Every fleet label is `passive`, so this changes no
    fleet number; it stops a non-passive sheet from being graded 1.1 to 2.2 mm
    SHORT per plate, silently.
  * FONT SIZE. The old model assumed 1.27 mm and never read the label's
    `(font (size ...))`. MEASURED: plate reach and cross extent scale EXACTLY
    linearly with size (cross/size = 2.0006 at 0.635, 1.27 and 2.54 mm). The
    size is now read; a label that does not declare one is UNPLACED, not
    guessed.
  * PROPERTY TEXT was the same defect twice over. `PROP_W = 0.82` per character
    is flat — 0.82/1.0 of the font against a true 20/21 to 24/21 for capitals,
    so `AVDD_MCU_3V3_RAIL` was modelled 17.702 mm wide against a true 19.171,
    1.47 mm SHORT. And `PROP_H = 0.53` was a SYMMETRIC half-height, while the
    ink is not symmetric about the anchor and not constant per character:
    MEASURED per character, up to 0.8719 mm above (`{`) and 1.0633 mm below
    (`)`), and on strings the FLEET ACTUALLY DRAWS up to 0.7509 above and
    1.0029 below — against 0.53 x 1.27 = 0.6731 both ways. The property box was
    0.078 mm short above and 0.330 mm short BELOW every descender on the fleet.
    Both are now per-character envelopes over the same measured table.

UPPER BOUND, ASSERTED RATHER THAN IMPLIED. A width model that can under-report
is the failure being repaired here, so the property is explicit and tested
(`t_the_model_is_an_upper_bound_on_ink`, `t_the_width_table_is_measured_from_ink`):
  * the model's plate box CONTAINS every stroke KiCad draws for that label —
    the 6-point plate polyline exactly (MEASURED: worst edge disagreement
    0.000210 mm over all 1507 fleet plates), and the glyph run strictly inside
    it with the 0.1524 mm pen counted (MEASURED: minimum margin 0.4029 mm);
  * THE ADVANCE SUM ALONE IS NOT AN UPPER BOUND, and assuming it was is how
    this file nearly shipped the same defect at one tenth the size. MEASURED
    per character: `\\` draws 0.0098 mm left of its pen origin and 0.2321 mm
    past its advance, and `_` — the fleet's commonest label character, 1234 of
    them — draws 0.1112 mm past its advance. `text_pad` carries those three
    numbers and `prop_box` applies them, so the box bounds INK rather than
    pen travel;
  * a character this table has never measured makes the object UNPLACED (a
    FAIL naming the character), not silently modelled. MEASURED: 0 such
    characters across all 8 fleet sheets.

THE MODEL IS A CENTRELINE MODEL, and that is a named residual rather than a
hidden one. KiCad strokes every glyph and every plate with a 0.1524 mm pen
(MEASURED from the render), so visible ink extends 0.0762 mm beyond every
centreline — on BOTH sides of every comparison this gate makes. Two objects
whose centreline boxes overlap therefore certainly overlap in ink; two whose
centrelines clear each other by less than 0.1524 mm may still touch in ink and
are NOT reported. The eps below is calibrated on centrelines for the same
reason: inflating the boxes instead would make every label overlap the pin it
attaches to by exactly the pen width.

TWO EARLIER CONSTANTS WERE ALSO WRONG AND BOTH ARE NOW MEASURED, one in each
direction, neither chosen to hit a number. Over 347 visible property texts and
386 rendered plates on three real sheets: a plate's CROSS-axis extent is
2.5408 mm exactly, with ZERO spread, against the shipped 2.2 (13% narrow, so
the old model was silent about real overlaps); and a property text's height is
1.0573x its font size, against a shipped HALF-height of 0.9, i.e. a box 70%
TOO TALL — which manufactured findings, and two of this model's own first-draft
findings (`label VMID x Reference R4`, `label VREF2 x Reference C_vref2b`) were
refuted against the render and disappeared when it was corrected.

FALSIFIED IN BOTH DIRECTIONS against `kicad-cli sch export svg`, on four
post-fix sheets, by matching each finding to the objects KiCad actually drew
(a label's PLATE is a 6-point polyline, a property is a `stroked-text` run):
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

A GREEN VERDICT HERE IS NOT EVIDENCE THAT LABELS POINT AT THE RIGHT PIN. Run
`circuit_json_to_kicad_sch.py`'s de-collision pass over the PRE-FIX direction
derivation (948ef54d, where 1504 of 1504 labels carried an `anchor_side`
exactly opposite `center - anchor_position`) and the sheet emerges with ZERO
collisions while every plate still names the wrong pin: the pass MOVES plates
until nothing overlaps, and a plate fired across its own part is as movable as
any other. Legibility and correctness are different questions and this gate
answers only the first.

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

#: the font size every metric below was MEASURED at. Everything scales exactly
#: linearly with size (MEASURED at 0.635, 1.27 and 2.54 mm: plate cross extent
#: / size = 2.0009 / 2.0006 / 2.0002, i.e. constant to the SVG's own rounding).
FONT_REF = 1.27

#: KiCad newstroke ADVANCE per character, in TWENTY-FIRSTS of the font size.
#: The font's em is 21 units, so every one of the 98 measured advances is an
#: exact integer and the table is LOSSLESS — the largest residual against an
#: integer over the whole sweep is 0.0008 mm, which is the SVG's 4-decimal
#: quantisation. DERIVED HERE from 294 rendered plates (98 characters x name
#: lengths 1/3/9, advance = (L9 - L1) / 8, cross-checked against (L3 - L1) / 2
#: on every character); NOT copied from `circuit_json_to_kicad_sch.py`, which
#: carries its own table for the same font — see the INDEPENDENCE note above.
ADV21 = {}
for _k, _cs in {8: "`", 10: "!',.:;Iij", 11: "l", 12: "^ft", 13: "r",
                14: "()[\\]{}", 15: "~", 16: " \"*JT_vy°", 17: "Lksxz",
                18: "?AFVYce", 19: "Eabdghnopqu", 20: "$0123456789SXZ|",
                21: "#BCDGKPR", 22: "/HNOQUwµ", 24: "%MWΩ", 26: "&+-<=>",
                27: "@", 28: "m"}.items():
    for _c in _cs:
        ADV21[_c] = _k

#: INK extent of a text run ABOVE / BELOW its anchor, per character, in mm at
#: FONT_REF. MEASURED one character at a time from the rendered `stroked-text`
#: run: the values quantise to exact 1/21 steps of the font size, and the
#: strings the FLEET draws need up to 0.7509 above and 1.0029 below — against
#: the shipped SYMMETRIC 0.53 x 1.27 = 0.6731, which was 0.078 mm short above
#: and 0.330 mm short below every descender on every board.
#: A run's envelope is the MAX over its characters, so it is tight (a box that
#: is too tall invents findings — that is what `PROP_H = 0.9` did) and never
#: short. A blank glyph (space) contributes 0 ink, which is correct.
INK_UP, INK_DN = {}, {}
for _v, _cs in {0.8719: "$(){}", 0.8114: "#[\\]|", 0.7509: "/4^`",
                0.6905: "!\"%&'*012356789?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                        "bdfhijklt°Ω",
                0.4486: "@", 0.3881: "+", 0.2671: "<>acegmnopqrsuvwxyzµ",
                0.2067: ":;", 0.0857: "=", 0.0252: "~", 0.0: " ",
                -0.0957: "-", -0.4586: ".", -0.5191: ",", -0.7005: "_"}.items():
    for _c in _cs:
        INK_UP[_c] = _v
for _v, _cs in {1.0633: "(){}", 1.0029: "[]gjpqy|µ", 0.8819: "/",
                0.8214: "#\\", 0.7610: "$,;@", 0.7005: "Q_",
                0.5795: "!%&+.0123456789:?ABCDEFGHIJKLMNOPRSTUVWXYZ"
                        "abcdefhiklmnorstuvwxzΩ",
                0.4586: "<>", 0.2771: "=", 0.0957: "-~", 0.0: " ",
                -0.1462: "*", -0.3276: "°", -0.4486: "\"'",
                -0.5695: "^`"}.items():
    for _c in _cs:
        INK_DN[_c] = _v

#: THE ADVANCE IS NOT ALWAYS THE INK. Three glyphs in 98 draw OUTSIDE their own
#: advance cell, MEASURED one character at a time from the render, in mm at
#: FONT_REF: `\` starts 0.0098 mm left of its pen origin and ends 0.2321 mm past
#: its advance, and `_` ends 0.1112 mm past its advance. Every other character
#: sits strictly inside (side bearings 0.0098 to 0.7159 mm).
#: `_` is the fleet's single commonest label character — 1234 of them — so
#: "advance sum" alone is NOT an upper bound on ink, which is the very claim
#: this model is here to make good.
#: ONLY THE FIRST AND LAST CHARACTER CAN MATTER, and that is arithmetic rather
#: than luck: the largest overhang measured is 0.2321 mm and the SMALLEST
#: advance in the table is 8/21 x 1.27 = 0.4838 mm, so an interior glyph's
#: overhang is swallowed by its neighbour's advance cell with 0.25 mm to spare.
INK_OVER_L = {"\\": 0.0098}
INK_OVER_R = {"\\": 0.2321, "_": 0.1112}

#: plate extent ALONG the reach = PLATE_BASE[shape] + the advance of every
#: character. MEASURED per SHAPE, at three font sizes x three name lengths:
#: the arrow point is part of the reach and a non-passive plate is 1.1 to
#: 2.2 mm longer than a passive one at the 1.27 mm font. Every fleet label is
#: `passive`; this exists so a sheet that uses another shape is graded rather
#: than under-measured.
PLATE_BASE = {"passive": 1.3341, "input": 2.4454, "output": 2.4454,
              "bidirectional": 3.5567, "tri_state": 3.5567}
#: plate extent ACROSS the reach, mm at FONT_REF. MEASURED: KiCad draws EXACTLY
#: 2.5408 mm on all 1507 real fleet plates and on all 45 probe plates, with
#: zero spread and identically for all five shapes. The shipped model said 2.2
#: and was 13% narrow. The relation it encodes is TWICE the font size: MEASURED
#: 1.2706 / 2.5408 / 5.0806 mm at 0.635 / 1.27 / 2.54, so scaling this one
#: constant linearly is right to 0.0010 mm over a 4x size range — and every
#: fleet label is at 1.27, where it is exact.
PLATE_CROSS = 2.5408

#: the pen KiCad strokes every glyph and plate with, MEASURED from the render's
#: own `stroke-width`. This model is a CENTRELINE model; the pen is the named
#: residual, not a correction applied anywhere — see the header.
PEN_MM = 0.1524

#: An overlap smaller than this is not one. A label plate ATTACHES at a wire
#: end, which is a pin tip, so an abutment of exactly 0 is the normal case and
#: float noise pushes it either side of zero; 605 of 605 cooksense "findings"
#: in the first draft of this model were that abutment, at 2e-15 mm.
#: RE-MEASURED under the corrected width model, because a threshold calibrated
#: against a wrong geometry is not calibrated: over the eight fleet sheets the
#: plate-vs-anything overlap distribution is still EMPTY between 0.0008 mm and
#: 0.0677 mm, so the threshold sits in the same two-decade gap and no fleet
#: verdict turns on its value.
OVERLAP_EPS_MM = 0.05


def text_span(s, size=FONT_REF):
    """ADVANCE width of a stroke-font run, mm.

    Usually wider than the ink, because the final character's trailing side
    bearing is advanced over and never drawn — but NOT ALWAYS, which is why
    `text_pad` exists: `\\` and `_` draw past their own advance. Use
    `text_span` + `text_pad` for a box that bounds the ink; `text_span` alone
    is the pen ADVANCE and nothing more.

    Raises KeyError on a character this table has never measured, so the caller
    can report it as UNPLACED rather than guess at it (canon M-COVER).
    """
    return sum(ADV21[c] for c in s) * size / 21.0


def text_pad(s, size=FONT_REF):
    """(left, right) mm of ink that escapes the ADVANCE box of a run — see
    INK_OVER_L / INK_OVER_R. Zero for every string the fleet draws."""
    if not s:
        return (0.0, 0.0)
    return (INK_OVER_L.get(s[0], 0.0) * size / FONT_REF,
            INK_OVER_R.get(s[-1], 0.0) * size / FONT_REF)


def text_updn(s, size=FONT_REF):
    """(ink above, ink below) a text run's anchor, mm. The per-character
    envelope: MAX over the characters present, so it is tight AND never short.
    """
    if not s:
        return (0.0, 0.0)
    return (max(INK_UP[c] for c in s) * size / FONT_REF,
            max(INK_DN[c] for c in s) * size / FONT_REF)


def unmeasured(s):
    """The characters of `s` this model has no measurement for."""
    return sorted({c for c in s if c not in ADV21 or c not in INK_UP
                   or c not in INK_DN})


def plate_span(name, size=FONT_REF, shape="passive"):
    """Extent of a global_label's plate ALONG its reach, mm."""
    return PLATE_BASE[shape] * size / FONT_REF + text_span(name, size)


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
    r"\(property \"(Reference|Value)\" \"([^\"]*)\" \(at ([-\d.]+) ([-\d.]+) (\d+)\)\s*"
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


def prop_box(txt, gx, gy, fs, just):
    """The rectangle a Reference/Value text occupies, from its anchor.

    Width is the ADVANCE SUM (an upper bound on ink); the vertical extent is
    the per-character ink envelope, which is NOT symmetric about the anchor —
    a descender reaches 1.0029 mm below at the 1.27 mm font while a capital
    reaches 0.5795 mm.
    """
    w = text_span(txt, fs)
    up, dn = text_updn(txt, fs)
    pl, pr = text_pad(txt, fs)
    if just == "right":
        x0 = gx - w
    elif just == "left":
        x0 = gx
    else:
        x0 = gx - w / 2
    return (x0 - pl, gy - up, x0 + w + pr, gy + dn)


def plate_box(name, gx, gy, ang, just, size=FONT_REF, shape="passive"):
    """The rectangle a global_label's plate occupies, from its ANCHOR."""
    ux, uy = PLATE_DIR[(ang, just)]
    reach = plate_span(name, size, shape)
    half = PLATE_CROSS * size / FONT_REF / 2.0
    if ux:
        return (min(gx, gx + ux * reach), gy - half,
                max(gx, gx + ux * reach), gy + half)
    return (gx - half, min(gy, gy + uy * reach),
            gx + half, max(gy, gy + uy * reach))


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
        sm = re.search(r"\(shape (\w+)\)", blk)
        shape = sm.group(1) if sm else "passive"
        if shape not in PLATE_BASE:
            unmodelled.append(f"global_label {name!r}: shape {shape!r} — the "
                              f"plate base is measured per shape and this one "
                              f"is not in the table")
            continue
        fm = re.search(r"\(font \(size ([\d.]+) [\d.]+\)", blk)
        if not fm:
            unmodelled.append(f"global_label {name!r}: no (font (size ...))")
            continue
        bad = unmeasured(name)
        if bad:
            unmodelled.append(f"global_label {name!r}: unmeasured "
                              f"character(s) {''.join(bad)!r} — the advance "
                              f"table has never seen them")
            continue
        texts.append((plate_box(name, gx, gy, ang, just,
                                float(fm.group(1)), shape),
                      f"label {name}", None))

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
            kind, txt, gx, gy, pang, fs, just, tail = (
                pm.group(1), pm.group(2), float(pm.group(3)),
                float(pm.group(4)), int(pm.group(5)), float(pm.group(6)),
                pm.group(7), pm.group(8))
            if "hide" in tail or not txt:
                continue
            if pang != 0:
                unmodelled.append(f"{kind} {txt!r} on {ref}: rotated {pang} — "
                                  f"the text metrics are measured at 0 only")
                continue
            bad = unmeasured(txt)
            if bad:
                unmodelled.append(f"{kind} {txt!r} on {ref}: unmeasured "
                                  f"character(s) {''.join(bad)!r}")
                continue
            # a property with NO justify is CENTRED on its anchor (unlike a
            # global_label, whose absent justify renders as `left`)
            toks = (just or "").split()
            if any(t in ("top", "bottom") for t in toks):
                unmodelled.append(f"{kind} {txt!r} on {ref}: (justify "
                                  f"{just}) moves the VERTICAL anchor and the "
                                  f"ink envelope is measured centred only")
                continue
            side = next((t for t in toks if t in ("left", "right")), None)
            texts.append((prop_box(txt, gx, gy, fs, side),
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
