#!/usr/bin/env python3
"""S-OCCL — the direction-aware schematic occlusion model (`sch_occlusion.py`).

THE DEFECT THESE FIXTURES PIN. The shipped S-OCCL, inline in `policy_audit.py`,
modelled every global_label plate as a HORIZONTAL box and sent every non-180
angle to `+x`:

    if ang == 180: (gx - wlen, ..., gx, ...)   else: (gx, ..., gx + wlen, ...)

`justify` was read nowhere, the vertical axis did not exist, and no symbol
geometry of any kind was on the page. MEASURED on pluto-rx2-8way-v2: 4 findings
before the converter fix at 948ef54d and 4 after, with 3 of the 4 REPLACED — a
gate that could see neither the defect nor its repair.

THE RED SIDE IS RE-MEASURED EVERY RUN, not asserted in a docstring: `prefix()`
below EXTRACTS the pre-fix block from `git show 948ef54d:...policy_audit.py`
and RUNS it, so every known-bad here is a live comparison against the real
shipped bytes rather than against a paraphrase of them.

FOUR AXES, BOTH DIRECTIONS. A fixture exercising only the horizontal axis is
exactly the blind spot under repair, so each known-bad appears four times —
left, right, up, down — in two shapes: a plate fired INTO a symbol body (which
the old model cannot see at all, having no bodies), and a plate-vs-plate
overlap the old model MISSES BECAUSE IT POINTS THE PLATE THE WRONG WAY (which
is the direction defect proper, with symbol geometry taken out of the argument).

GIT-SWAP RED-VERIFIED, 2026-07-31, in addition to the per-run extraction above:
`occlusions()` was replaced wholesale by the block from
`git show 948ef54d:policy_audit.py` and this suite run — **4 passed / 12 failed
/ 0 known-bad**, with ALL NINE known-bad fixtures red and the vacuity fixture
red with them. Restored: **16 / 0 / 9 known-bad + 1 vacuity**. The four that
survive the swap are the ones that do not consult the direction model at all
(the ink measurement, the ink falsification, the fleet denominator, and the
prototype-exclusion check, which reads `parse_sheet` directly).

=====================================================================
THE SECOND DEFECT THESE FIXTURES PIN: A FIXED-WIDTH MODEL OVER A
PROPORTIONAL FONT (2026-07-31)
=====================================================================

`CH_W = 1.05` charged every character the same width and built a plate as
`(len(name) + 2) * CH_W`. KiCad's stroke font is PROPORTIONAL, and the flat
model is wrong in BOTH directions — MEASURED against the boxes KiCad itself
draws, on all 1507 real fleet plates: **too SHORT on 596 (worst 1.6654 mm),
too WIDE on 911 (worst 1.1173 mm), and EXACT ON ZERO OF THEM.** The corrected
model matches the rendered box to 0.000210 mm on all 1507, which is the SVG's
own 4-decimal quantisation and nothing else.

Too WIDE invents findings; too SHORT makes a REAL ink composite INVISIBLE, and
the fleet's own names take it that way: every capital letter advances 20/21 to
22/21 of the font size against a flat 1.05/1.27 = 17.4/21.

The red side of BOTH new fixtures is the REAL SHIPPED BYTES, exactly as above:
`flat()` loads `git show c90c51c3:sch_occlusion.py` — the whole module, direction
model and symbol geometry included, differing from HEAD in the WIDTH model
alone — and runs it, so each fixture is a live A/B against the flat model rather
than against a paraphrase of it. Two shapes, because the defect has two:

  * `t_flat_width_hides_a_real_overlap` — a 17-character capitalised name whose
    plate genuinely runs into its neighbour IN KiCad'S OWN INK, which the flat
    model scores CLEAN;
  * `t_flat_width_invents_an_overlap` — the mirror, an `IIII`-class narrow name
    the flat model scores DIRTY and whose plates KiCad draws 0.2469 mm APART.

GIT-SWAP RED-VERIFIED for the width fix, 2026-07-31: `sch_occlusion.py` was
replaced wholesale by `git show c90c51c3:...` and this suite run — **17 passed
/ 5 failed**, restored **22 / 0 / 11 known-bad + 1 vacuity**. Four of the five
red on the MEASUREMENT (missed overlap, invented overlap, a 1.6654 mm box
disagreement, a guessed character), one on the absence of the table itself; the
counts and the reasoning are recorded in `t_flat_width_hides_a_real_overlap`.
"""
import re
import subprocess
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

sys.path.insert(0, str(SCRIPTS))
import sch_occlusion as SO                                     # noqa: E402

TOOL = SCRIPTS / "sch_occlusion.py"

#: the commit that carries the pre-fix S-OCCL bytes. A PINNED COMMIT is the
#: strongest oracle available (tests/README, "which real bytes may a fixture
#: read") — the path is only a locator and nothing in the working tree can
#: move it.
PREFIX_COMMIT = "948ef54d"

#: the commit that carries the FLAT-WIDTH `sch_occlusion.py`: direction model
#: and symbol geometry already correct, `CH_W = 1.05` still in place. The two
#: width fixtures below A/B against this file, so what they refute is the real
#: shipped module and not a re-typing of its arithmetic.
FLAT_COMMIT = "c90c51c3"


# --------------------------------------------------------- the pre-fix model
def prefix(stxt):
    """Run the REAL pre-fix S-OCCL model, extracted from git, on a sheet.

    The block is lifted verbatim out of `policy_audit.py` as it stood at
    PREFIX_COMMIT and exec'd with `stxt` bound, so what the known-bads below
    compare against is the shipped algorithm, not a re-typing of it."""
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         f"{PREFIX_COMMIT}:skills/kicad-pcb/scripts/policy_audit.py"],
        capture_output=True, text=True)
    check(blob.returncode == 0, f"git show {PREFIX_COMMIT} failed: {blob.stderr}")
    m = re.search(r"\n(        items = \[\].*?)\n        thr = int\(cfg",
                  blob.stdout, re.S)
    check(m is not None, "the pre-fix S-OCCL block is no longer locatable in "
                         f"{PREFIX_COMMIT}:policy_audit.py — this fixture "
                         "would silently stop measuring the red side")
    src = "\n".join(ln[8:] for ln in m.group(1).splitlines())
    check("if ang == 180:" in src and "gx + wlen" in src,
          "the extracted block is not the +x model this suite exists to "
          f"refute:\n{src[:400]}")
    ns = {"re": re, "stxt": stxt}
    exec(src, ns)                                             # noqa: S102
    return ns["occl"]


_FLAT_CACHE = []


def flat_module():
    """The FLAT-WIDTH `sch_occlusion.py`, loaded from git and importable.

    Not a re-typing of `(len + 2) * 1.05`: the whole module as it stood at
    FLAT_COMMIT, so the A/B below differs from HEAD in the width model and in
    nothing else."""
    if _FLAT_CACHE:
        return _FLAT_CACHE[0]
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         f"{FLAT_COMMIT}:skills/kicad-pcb/scripts/sch_occlusion.py"],
        capture_output=True, text=True)
    check(blob.returncode == 0,
          f"git show {FLAT_COMMIT} failed: {blob.stderr}")
    check("CH_W = 1.05" in blob.stdout and "(len(name) + 2) * CH_W" in blob.stdout,
          f"{FLAT_COMMIT}:sch_occlusion.py is not the flat-width model these "
          f"fixtures exist to refute — this A/B would silently stop measuring "
          f"the red side")
    p = tmpdir("flatso_") / "flat_sch_occlusion.py"
    p.write_text(blob.stdout, encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location("flat_sch_occlusion", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _FLAT_CACHE.append(mod)
    return mod


def flat(sheet_path):
    """Findings the FLAT-WIDTH model reports on a sheet."""
    return flat_module().occlusions(
        sheet_path.read_text(encoding="utf-8-sig"))[0]


def svg_of(p, d):
    """Render a sheet and return its SVG text — KiCad's own ink."""
    must_pass(run(["kicad-cli", "sch", "export", "svg",
                   "--no-background-color", "-o", d, p]), f"render {p.name}")
    return (d / (p.stem + ".svg")).read_text()


def drawn_plates(svg):
    """(anchor) -> [bbox]. A global_label's plate is a 6-point closed path
    whose FIRST point IS the label's anchor, so plates key by anchor with no
    name matching and no ambiguity between same-named labels."""
    out = {}
    for m in re.finditer(r'<path style="[^"]*"\s*\n?\s*d="M ([^"]+)Z"', svg):
        pts = [(float(a), float(b)) for a, b in
               re.findall(r"([-\d.]+),([-\d.]+)", m.group(1))]
        if len(pts) != 6:
            continue
        out.setdefault((round(pts[0][0], 3), round(pts[0][1], 3)), []).append(
            (min(q[0] for q in pts), min(q[1] for q in pts),
             max(q[0] for q in pts), max(q[1] for q in pts)))
    return out


def drawn_runs(svg):
    """text -> [ink bbox] for every `stroked-text` glyph run KiCad drew."""
    out = {}
    for m in re.finditer(r'<g class="stroked-text"><desc>(.*?)</desc>(.*?)</g>',
                         svg, re.S):
        q = [(float(a), float(b)) for a, b in
             re.findall(r"[ML]\s*([-\d.]+)\s+([-\d.]+)", m.group(2))]
        if q:
            out.setdefault(m.group(1), []).append(
                (min(t[0] for t in q), min(t[1] for t in q),
                 max(t[0] for t in q), max(t[1] for t in q)))
    return out


# ------------------------------------------------------------ sheet building
#: One 10x10 body at local (-5,-5)-(5,5), and ONE pin, deliberately offset to
#: local y=-4 (sheet y=104) so that none of the eight axis anchors below can
#: reach it — a fixture whose axes contaminate each other proves nothing about
#: any one of them.
BOX_LIB = """    (symbol "elt:BOX" (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Value" "BOX" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol "BOX_0_1"
        (rectangle (start -5.0 -5.0) (end 5.0 5.0) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "BOX_1_1"
        (pin passive line (at -12.0 -4.0 0) (length 7.0) (name "IN" (effects (font (size 1.0 1.0)))) (number "1" (effects (font (size 1.0 1.0)))))
      )
    )"""


def sheet(labels=(), symbols=(), libs=(BOX_LIB,), out=None,
          wires=(), junctions=()):
    """Write a minimal one-page .kicad_sch.

    labels:  (name, x, y, angle, justify_or_None)
    symbols: (lib_id, x, y, angle, reference, value_or_None)
    wires:   (x1, y1, x2, y2)
    junctions: (x, y)
    """
    n = [0]

    def uu():
        n[0] += 1
        return "00000000-0000-0000-0000-%012d" % n[0]

    L = ['(kicad_sch (version 20230121) (generator t1_occlusion)',
         '  (uuid "00000000-0000-0000-0000-0000000000ff")',
         '  (paper "User" 420.00 300.00)',
         '  (title_block (title "occl") (date "2026-07-31") (rev "t")', '  )',
         '  (lib_symbols'] + list(libs) + ['  )']
    for (nm, x, y, ang, just) in labels:
        j = f" (justify {just})" if just else ""
        nm = nm.replace("\\", "\\\\").replace('"', '\\"')   # the advance probe
        L.append(f'  (global_label "{nm}" (shape passive) (at {x} {y} {ang})'
                 f' (fields_autoplaced) (effects (font (size 1.27 1.27)){j})'
                 f' (uuid "{uu()}"))')
    for (lib, x, y, ang, ref, val) in symbols:
        L += [f'  (symbol (lib_id "{lib}") (at {x} {y} {ang}) (unit 1)'
              f' (in_bom yes) (on_board yes) (dnp no) (uuid "{uu()}")',
              f'    (property "Reference" "{ref}" (at {x} {y - 12} 0)'
              f' (effects (font (size 1.27 1.27)){"" if val else " hide"}))']
        # ALWAYS emit a Value, hidden when there is none: an instance with no
        # Value property inherits the lib_symbol's, and KiCad then DRAWS it —
        # which put a "GND" text run on top of every ground glyph in the
        # rotation probe and moved its measured centroid.
        L.append(f'    (property "Value" "{val or "?"}" (at {x} {y + 12} 0)'
                 f' (effects (font (size 1.27 1.27)){"" if val else " hide"}))')
        L += [f'    (pin "1" (uuid "{uu()}"))',
              f'    (instances (project "occl" (path "/00000000-0000-0000-'
              f'0000-0000000000ff" (reference "{ref}") (unit 1))))', '  )']
    for (x1, y1, x2, y2) in wires:
        L.append(f'  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))'
                 f' (stroke (width 0) (type default)) (uuid "{uu()}"))')
    for (x, y) in junctions:
        L.append(f'  (junction (at {x} {y}) (diameter 0) (color 0 0 0 0)'
                 f' (uuid "{uu()}"))')
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    p = (out or (tmpdir("occl_") / "s.kicad_sch"))
    # utf-8 EXPLICITLY: the advance probe writes `°`, `µ` and `Ω`, and a
    # locale-dependent default would make the measurement unreproducible.
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    return p


#: A body at (100,100) spans (95,95)-(105,105); each anchor sits 10 mm from the
#: body CENTRE, i.e. 5 mm clear of its edge. Under the measured PROPORTIONAL
#: width model the four names no longer share a reach (the flat model gave every
#: 4-character name 6.30 mm) — MEASURED, in twenty-firsts of the 1.27 mm font:
#:   PRGT 21+21+21+16 = 79  ->  reach 6.1117 mm  ->  1.1117 mm into the body
#:   PLFT 21+17+18+16 = 72  ->  reach 5.6884 mm  ->  0.6884 mm into the body
#:   PUPP 21+22+21+21 = 85  ->  reach 6.4746 mm  ->  1.4746 mm into the body
#:   PDWN 21+21+24+22 = 88  ->  reach 6.6560 mm  ->  1.6560 mm into the body
#: All four are far above OVERLAP_EPS_MM, so every axis still bites; the
#: shallowest (PLFT, 0.6884 mm) is 13x the threshold.
INTO_BODY = {
    "right": ("PRGT", 90.0, 100.0, 0, "left"),
    "left":  ("PLFT", 110.0, 100.0, 0, "right"),
    "up":    ("PUPP", 100.0, 110.0, 90, "left"),
    "down":  ("PDWN", 100.0, 90.0, 90, "right"),
}
#: the same four plates, fired the other way — clear of the body by 10 mm.
AWAY = {
    "right": ("PRGT", 110.0, 100.0, 0, "left"),
    "left":  ("PLFT", 90.0, 100.0, 0, "right"),
    "up":    ("PUPP", 100.0, 90.0, 90, "left"),
    "down":  ("PDWN", 100.0, 110.0, 90, "right"),
}
#: two plates that overlap EACH OTHER along one axis, with no symbol on the
#: sheet at all — so the known-bad turns purely on the plate DIRECTION.
PAIR = {
    "right": [("QQAA", 200.0, 150.0, 180, "left"),
              ("QQBB", 204.0, 150.6, 0, "left")],
    "left":  [("QQAA", 210.0, 150.0, 0, "right"),
              ("QQBB", 206.0, 150.6, 180, "right")],
    "up":    [("QQAA", 200.0, 160.0, 90, "left"),
              ("QQBB", 200.6, 156.0, 270, "left")],
    "down":  [("QQAA", 200.0, 150.0, 90, "right"),
              ("QQBB", 200.6, 154.0, 270, "right")],
}
BOX_AT = [("elt:BOX", 100.0, 100.0, 0, "U1", None)]


def counts(p):
    occl, unm, graded, total = SO.occlusions(p.read_text(encoding="utf-8-sig"))
    return occl, unm, graded, total


# =========================================================== measured truth
@test("the whole KiCad geometry table is MEASURED from rendered ink — plate "
      "direction, the no-justify default, the symbol rotation transform, and "
      "both text metrics")
def t_kicad_geometry_is_measured():
    """Canon M1: this model must not grade its own geometry. Every constant it
    rests on is re-derived here from `kicad-cli sch export svg` INK on a probe
    sheet KiCad renders itself.

    Four things it pins, and TWO of them were wrong in shipped code:
      * a global_label's ANGLE selects only the AXIS; `justify` ALONE selects
        the sense, and NO justify renders as `left`;
      * a placed symbol's local geometry rotates CCW then flips y (checked with
        an ASYMMETRIC probe rectangle, so a wrong handedness cannot pass);
      * a plate's CROSS extent is 2.5408 mm — the shipped model said 2.2;
      * a property text is 1.0573x its font size tall — the shipped model used
        a HALF-height of 0.9, i.e. a box 70% too tall, which INVENTS findings.
    """
    d = tmpdir("dirprobe_")
    labs, gnds, boxes = {}, {}, {}
    L = []
    for i, (a, j) in enumerate([(a, j) for a in (0, 90, 180, 270)
                                for j in ("left", "right", None)]):
        x, y = 40 + (i % 4) * 90, 60 + (i // 4) * 40
        nm = "L%03d%sZZZZ" % (a, (j or "n")[0].upper())
        labs[nm] = (x, y, a, j)
        L.append((nm, x, y, a, j))
    for i, a in enumerate((0, 90, 180, 270)):
        boxes[a] = (60 + i * 90, 200)
    syms = [("elt:BOX", boxes[a][0], boxes[a][1], a, f"X{a}", None)
            for a in boxes]
    for i, a in enumerate((0, 90, 180, 270)):
        gnds[a] = (60 + i * 90, 245)
        syms.append(("elt:GND", gnds[a][0], gnds[a][1], a, f"#PWR{a:03d}", None))
    import schwriter2 as SW                                   # noqa: E402
    p = sheet(L, syms, libs=[BOX_LIB] + list(SW.power_lib_symbols("elt").values()),
              out=d / "probe.kicad_sch")
    must_pass(run(["kicad-cli", "sch", "export", "svg",
                   "--no-background-color", "-o", d, p]), "probe render")
    svg = (d / "probe.svg").read_text()

    def pts(s):
        return [(float(a), float(b)) for a, b in
                re.findall(r"(-?\d+\.?\d*)[ ,](-?\d+\.?\d*)", s)]

    def unit(dx, dy):
        return ((1 if dx > 0 else -1), 0) if abs(dx) > abs(dy) \
            else (0, (1 if dy > 0 else -1))

    # (1) plate direction, all 8 (angle, justify) combinations + no-justify
    seen = 0
    for m in re.finditer(r'<g class="stroked-text"><desc>(L\d{3}[LRN]ZZZZ)'
                         r'</desc>(.*?)</g>', svg, re.S):
        nm = m.group(1)
        if nm not in labs:
            continue
        q = pts(m.group(2))
        check(q, f"{nm}: no ink in the rendered glyph run")
        ax, ay, a, j = labs[nm]
        cx = (min(t[0] for t in q) + max(t[0] for t in q)) / 2
        cy = (min(t[1] for t in q) + max(t[1] for t in q)) / 2
        want = SO.PLATE_DIR[(a, j or SO.DEFAULT_JUSTIFY)]
        eq(unit(cx - ax, cy - ay), want,
           f"KiCad renders (angle {a}, justify {j}) reaching")
        seen += 1
    eq(seen, 12, "label combinations measured out of the render "
                 "(8 explicit + 4 with no justify)")

    # (2) the symbol rotation transform, from the ASYMMETRIC body rectangle
    rects = [(float(r.group(1)), float(r.group(2)),
              float(r.group(1)) + float(r.group(3)),
              float(r.group(2)) + float(r.group(4)))
             for r in re.finditer(r'<rect x="([-\d.]+)" y="([-\d.]+)" '
                                  r'width="([\d.]+)" height="([\d.]+)"', svg)]
    for a, (bx, by) in boxes.items():
        near = [r for r in rects if abs((r[0] + r[2]) / 2 - bx) < 12
                and abs((r[1] + r[3]) / 2 - by) < 12]
        check(near, f"no body rect rendered near the angle-{a} instance")
        got = near[0]
        corners = [SO.xf(x, y, a) for x, y in
                   ((-5, -5), (5, -5), (5, 5), (-5, 5))]
        want = (bx + min(c[0] for c in corners), by + min(c[1] for c in corners),
                bx + max(c[0] for c in corners), by + max(c[1] for c in corners))
        for k in range(4):
            check(abs(got[k] - want[k]) < 0.01,
                  f"symbol rotation {a}: model box {want} vs rendered {got}")

    # (3) the ground glyph, per rotation — the model must place it OUTWARD
    def poly_pts(s):
        return pts(s)
    paths = [poly_pts(mm.group(1)) for mm in
             re.finditer(r'<(?:path|polyline)[^>]*?(?:\bd|points)="([^"]+)"',
                         svg)]
    for a, (gx, gy) in gnds.items():
        acc = [t for pp in paths if pp and all(abs(t[0] - gx) < 6 and
                                               abs(t[1] - gy) < 6 for t in pp)
               for t in pp]
        check(acc, f"GND at angle {a}: no ink found near ({gx}, {gy})")
        want = {0: (0, 1), 90: (1, 0), 180: (0, -1), 270: (-1, 0)}[a]
        eq(unit(sum(t[0] for t in acc) / len(acc) - gx,
                sum(t[1] for t in acc) / len(acc) - gy), want,
           f"elt:GND body direction at rotation {a}")

    # (4) the two text metrics the model carries as constants
    plates = [pp for pp in paths if len(pp) == 6]
    cross = set()
    for nm, (ax, ay, a, j) in labs.items():
        cand = [pp for pp in plates
                if min(abs(min(t[0] for t in pp) - ax),
                       abs(max(t[0] for t in pp) - ax)) < 0.01
                and min(t[1] for t in pp) - .01 <= ay <= max(t[1] for t in pp) + .01] \
            if a in (0, 180) else \
            [pp for pp in plates
             if min(abs(min(t[1] for t in pp) - ay),
                    abs(max(t[1] for t in pp) - ay)) < 0.01
             and min(t[0] for t in pp) - .01 <= ax <= max(t[0] for t in pp) + .01]
        if not cand:
            continue
        pp = cand[0]
        w = max(t[0] for t in pp) - min(t[0] for t in pp)
        h = max(t[1] for t in pp) - min(t[1] for t in pp)
        cross.add(round(h if a in (0, 180) else w, 4))
    # read by BOTH names: the constant was renamed CH_H -> PLATE_CROSS when the
    # width model was corrected, and this fixture is about the MEASUREMENT, not
    # about which identifier holds it — so a module swap cannot red it for a
    # spelling reason and mask what it really grades.
    eq(sorted(cross), [getattr(SO, "PLATE_CROSS", getattr(SO, "CH_H", None))],
       "the plate CROSS extent KiCad renders, against the model's constant — "
       "the shipped model said 2.2 and was 13% narrow")


@test("the WHOLE width table is re-derived from rendered ink every run — 98 "
      "per-character advances, the plate base per SHAPE, the cross extent at "
      "three font sizes, and both property ink envelopes")
def t_the_width_table_is_measured_from_ink():
    """CANON M1, and the reason this test is long rather than a spot check.

    `circuit_json_to_kicad_sch.py` carries its own advance table for the same
    font. If S-OCCL simply imported it, the gate and the emitter would share a
    method and a common error would be invisible: the converter would place a
    plate it believed clear, the gate would agree, and KiCad would draw through
    the neighbour. So the gate carries its OWN table, DERIVED independently —
    and the only thing that keeps two independent tables honest is re-deriving
    one of them from the renderer on every run. That is what this does.

    FOUR MEASUREMENTS:

      1. ADVANCE, per character. Names `H + c*n + H` for n in {1,3,9}: the
         bracketing `H`s make the measurement immune to any leading/trailing
         trimming, and adv = (L9 - L1)/8 is cross-checked against (L3 - L1)/2
         so a non-linear glyph cannot slip through. MEASURED: every advance is
         an EXACT integer twenty-first of the font size, k from 8 to 28,
         residual below 0.0008 mm.
      2. PLATE BASE, per shape. MEASURED: passive 1.3341, input/output 2.4454,
         bidirectional/tri_state 3.5567 mm at the 1.27 mm font. The old model
         had one number and would have under-measured a non-passive plate by
         1.1 to 2.2 mm.
      3. PLATE CROSS, at three font sizes, asserted as a SET so the zero spread
         cannot be averaged away, and asserted to scale linearly with size.
      4. PROPERTY INK, above and below the anchor, per character. MEASURED: not
         symmetric (`p` reaches 1.0029 mm below at the 1.27 mm font, `A` only
         0.5795) and not constant, against the shipped SYMMETRIC 0.53 x 1.27.
    """
    d = tmpdir("advprobe_")
    chars = sorted(SO.ADV21)
    # ---- 1. advances
    items, key = [], {}
    for i, c in enumerate(chars):
        for j, n in enumerate((1, 3, 9)):
            k = i * 3 + j
            x, y = 20.0 + (k % 12) * 33.0, 20.0 + (k // 12) * 6.0
            items.append(("H" + c * n + "H", x, y, 0, "left"))
            key[(round(x, 3), round(y, 3))] = (c, n)
    p = sheet(items, (), out=d / "adv.kicad_sch")
    pl = drawn_plates(svg_of(p, d))
    reach = {}
    for anchor, (c, n) in key.items():
        got = pl.get(anchor)
        check(got, f"KiCad drew no plate for {c!r} x {n} at {anchor}")
        b = got[0]
        reach[(c, n)] = b[2] - b[0]
    off = []
    for c in chars:
        a8 = (reach[(c, 9)] - reach[(c, 1)]) / 8.0
        a2 = (reach[(c, 3)] - reach[(c, 1)]) / 2.0
        check(abs(a8 - a2) < 2e-3,
              f"{c!r}: advance is not linear in count — (L3-L1)/2={a2:.4f} vs "
              f"(L9-L1)/8={a8:.4f}; a per-character table cannot represent it")
        k = a8 * 21.0 / 1.27
        if abs(k - SO.ADV21[c]) > 0.01:
            off.append((c, round(k, 4), SO.ADV21[c]))
    eq(off, [], "characters whose RENDERED advance disagrees with the model's "
                "twenty-firsts (measured, model)")
    eq(len(chars), 98, "characters in the advance table")
    # ...and the base falls out of the same numbers. It is asserted as a RANGE
    # rather than a mean, so a spread cannot be averaged into agreement: over
    # the 294 probe plates it is 1.33372 to 1.33453 (MEASURED), a spread of
    # 0.00081 mm which is the SVG's 4-decimal coordinate quantisation
    # compounded over an 11-character name — 60x below OVERLAP_EPS_MM and 190x
    # below the pen, and the modal value (103 of 294) is the model's 1.3341.
    bases = [reach[(c, n)] - SO.text_span("H" + c * n + "H")
             for c in chars for n in (1, 3, 9)]
    lo, hi = min(bases), max(bases)
    check(hi - lo < 1.5e-3,
          f"the passive plate BASE spreads {hi - lo:.5f} mm over 294 plates "
          f"({lo:.5f} to {hi:.5f}) — that is no longer render quantisation and "
          f"a single constant cannot represent it")
    check(lo - 1e-4 <= SO.PLATE_BASE["passive"] <= hi + 1e-4,
          f"the model's PLATE_BASE {SO.PLATE_BASE['passive']} lies outside the "
          f"measured range {lo:.5f}..{hi:.5f}")

    # ---- 2/3. base per SHAPE and cross at three sizes
    L = ['(kicad_sch (version 20230121) (generator t1_occlusion)',
         '  (uuid "00000000-0000-0000-0000-0000000000ff")',
         '  (paper "User" 420.00 297.00)',
         '  (title_block (title "occl") (date "2026-07-31") (rev "t")', '  )',
         '  (lib_symbols', '  )']
    skey, i = {}, 0
    for sh in sorted(set(SO.PLATE_BASE)):
        for sz in (0.635, 1.27, 2.54):
            for nm in ("A", "AAAA", "MMMMMMMM"):
                x, y = 20.0 + (i % 8) * 50.0, 20.0 + (i // 8) * 12.0
                L.append(f'  (global_label "{nm}" (shape {sh}) (at {x} {y} 0)'
                         f' (fields_autoplaced) (effects (font (size {sz} {sz}))'
                         f' (justify left)) (uuid "00000000-0000-0000-0000-'
                         f'%012d"))' % (i + 1))
                skey[(round(x, 3), round(y, 3))] = (sh, sz, nm)
                i += 1
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    q = d / "shapes.kicad_sch"
    q.write_text("\n".join(L) + "\n", encoding="utf-8")
    pl = drawn_plates(svg_of(q, d))
    cross = {}
    for anchor, (sh, sz, nm) in skey.items():
        got = pl.get(anchor)
        check(got, f"no plate drawn for shape {sh} at size {sz}")
        b = got[0]
        want = SO.plate_span(nm, sz, sh)
        check(abs((b[2] - b[0]) - want) < 2e-3,
              f"shape {sh} at size {sz}, {nm!r}: KiCad reaches "
              f"{b[2] - b[0]:.4f} mm, the model says {want:.4f}")
        cross.setdefault(sz, set()).add(round(b[3] - b[1], 4))
    for sz, vals in sorted(cross.items()):
        # ONE value per size, over 5 shapes x 3 name lengths: the zero spread
        # is the claim, and asserting the SET is what stops it being averaged
        # into agreement.
        eq(len(vals), 1, f"distinct plate CROSS extents at font size {sz} over "
                         f"five shapes and three name lengths — {sorted(vals)}")
        got, want = sorted(vals)[0], SO.PLATE_CROSS * sz / SO.FONT_REF
        # MEASURED across a 4x size range: 1.2706 / 2.5408 / 5.0806 mm at
        # 0.635 / 1.27 / 2.54, i.e. exactly TWICE the font size to within
        # 0.0008 mm. One constant scaled linearly therefore serves every size
        # to 0.0010 mm — and every fleet label is at 1.27, where it is exact.
        check(abs(got - want) < 1.2e-3,
              f"the plate CROSS extent at font size {sz}: KiCad draws {got} mm, "
              f"the model scales to {want:.4f} — linearity in the font size is "
              f"what lets one constant serve every size")
        check(abs(got - 2.0 * sz) < 1e-3,
              f"the plate CROSS extent at font size {sz} is {got} mm, not "
              f"2 x the font size — the relation the constant encodes")

    # ---- 4. property ink envelope, per character
    L = ['(kicad_sch (version 20230121) (generator t1_occlusion)',
         '  (uuid "00000000-0000-0000-0000-0000000000ff")',
         '  (paper "User" 420.00 297.00)',
         '  (title_block (title "occl") (date "2026-07-31") (rev "t")', '  )',
         '  (lib_symbols', BOX_LIB, '  )']
    pkey = {}
    for i, c in enumerate(chars):
        x, y = 25.0 + (i % 10) * 39.0, 25.0 + (i // 10) * 13.0
        esc = c.replace("\\", "\\\\").replace('"', '\\"')
        uu = "00000000-0000-0000-0000-%012d" % (i + 1)
        L += [f'  (symbol (lib_id "elt:BOX") (at {x} {y + 6.5} 0) (unit 1)'
              f' (in_bom yes) (on_board yes) (dnp no) (uuid "{uu}")',
              f'    (property "Reference" "{esc}" (at {x} {y} 0)'
              f' (effects (font (size 1.27 1.27)) (justify left)))',
              f'    (property "Value" "?" (at {x} {y + 6.5} 0)'
              f' (effects (font (size 1.27 1.27)) hide))',
              f'    (instances (project "occl" (path "/00000000-0000-0000-0000-'
              f'0000000000ff" (reference "{esc}") (unit 1))))', '  )']
        pkey[c] = (x, y)
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    q = d / "props.kicad_sch"
    q.write_text("\n".join(L) + "\n", encoding="utf-8")
    svg = svg_of(q, d)
    runs = []
    for m in re.finditer(r'<g class="stroked-text"><desc>(.*?)</desc>(.*?)</g>',
                         svg, re.S):
        t = [(float(a), float(b)) for a, b in
             re.findall(r"[ML]\s*([-\d.]+)\s+([-\d.]+)", m.group(2))]
        if t:
            runs.append((min(v[0] for v in t), min(v[1] for v in t),
                         max(v[0] for v in t), max(v[1] for v in t)))
    bad, blank, escaped, over = [], 0, [], []
    for c in chars:
        x, y = pkey[c]
        cand = [b for b in runs if abs(b[0] - x) < 3.0
                and abs((b[1] + b[3]) / 2 - y) < 2.0]
        if not cand:
            blank += 1                       # a space draws no ink at all
            continue
        b = min(cand, key=lambda q: abs(q[0] - x))
        up, dn = SO.text_updn(c)
        if abs((y - b[1]) - up) > 2e-3 or abs((b[3] - y) - dn) > 2e-3:
            bad.append((c, round(y - b[1], 4), round(up, 4),
                        round(b[3] - y, 4), round(dn, 4)))
        # THE BOX, not the advance: `\` and `_` draw past their own advance
        # cell, so `text_span` alone would under-reach and `text_pad` carries
        # the three measured overhangs that fix it.
        box = SO.prop_box(c, x, y, SO.FONT_REF, "left")
        if b[0] < box[0] - 1e-3 or b[2] > box[2] + 1e-3:
            escaped.append((c, round(box[0] - b[0], 4), round(b[2] - box[2], 4)))
        if c not in SO.INK_OVER_R and b[2] > x + SO.text_span(c) + 1e-3:
            over.append(c)
    eq(bad, [], "characters whose RENDERED ink envelope disagrees with the "
                "model (char, ink_up, model_up, ink_dn, model_dn)")
    eq(blank, 1, "characters that draw no ink at all (the space)")
    eq(escaped, [], "characters whose rendered ink escapes the model's own "
                    "property box (char, left_escape_mm, right_escape_mm)")
    eq(over, [], "characters that draw past their advance but carry NO entry "
                 "in INK_OVER_R — the pad table has gone stale against the "
                 "font and the box is short by that much")


@test("every finding on a real post-converter-fix sheet is a REAL ink overlap "
      "— the model is falsified against KiCad's own render, not trusted")
def t_findings_are_confirmed_in_rendered_ink():
    """The false-positive control. Each text-vs-text finding is matched to the
    objects KiCad actually DREW — a label's plate is a 6-point polyline, a
    property is a `stroked-text` run — and the two drawn boxes must genuinely
    overlap. This is what caught the inherited `PROP_H = 0.9`: it made every
    property box 70% too tall and manufactured `label VMID x Reference R4`,
    which the render refutes."""
    d = tmpdir("inkconf_")
    p = sheet([("AAAA", 100.0, 100.0, 0, "left"),      # reaches right, into U1
               ("BBBB", 100.0, 130.0, 0, "left"),      # clear
               ("CCCC", 105.6, 130.6, 180, "right")],  # overlaps BBBB
              BOX_AT, out=d / "s.kicad_sch")
    occl, unm, graded, total = counts(p)
    eq(unm, [], "every drawable object placed")
    check("label BBBB x label CCCC" in occl,
          f"the plate-vs-plate pair is not reported: {occl}")
    must_pass(run(["kicad-cli", "sch", "export", "svg",
                   "--no-background-color", "-o", d, p]), "render")
    svg = (d / "s.svg").read_text()

    def bb(s):
        q = [(float(a), float(b)) for a, b in
             re.findall(r"(-?\d+\.?\d*)[ ,](-?\d+\.?\d*)", s)]
        return (min(t[0] for t in q), min(t[1] for t in q),
                max(t[0] for t in q), max(t[1] for t in q)) if q else None
    plates = [bb(m.group(1)) for m in
              re.finditer(r'<(?:path|polyline)[^>]*?(?:\bd|points)="([^"]+)"', svg)
              if len(re.findall(r"(-?\d+\.?\d*)[ ,](-?\d+\.?\d*)", m.group(1))) == 6]
    ink = {}
    for m in re.finditer(r'<g class="stroked-text"><desc>(.*?)</desc>(.*?)</g>',
                         svg, re.S):
        b = bb(m.group(2))
        if b:
            ink.setdefault(m.group(1), []).append(b)
    got = {}
    for t in ("BBBB", "CCCC"):
        b = ink[t][0]
        cand = [q for q in plates if q and q[0] <= b[0] + .2 and q[1] <= b[1] + .2
                and q[2] >= b[2] - .2 and q[3] >= b[3] - .2]
        check(cand, f"no rendered plate found around {t}")
        got[t] = min(cand, key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
    a, b = got["BBBB"], got["CCCC"]
    check(min(a[2], b[2]) - max(a[0], b[0]) > 0 and
          min(a[3], b[3]) - max(a[1], b[1]) > 0,
          f"the model reported BBBB x CCCC but KiCad's own plates do not "
          f"overlap: {a} vs {b} — that would be a FALSE POSITIVE")


# ====================================================== four axes, into a body
def _axis_body_known_bad(axis):
    d = tmpdir(f"occl_{axis}_")
    bad = sheet([INTO_BODY[axis]], BOX_AT, out=d / "bad.kicad_sch")
    good = sheet([AWAY[axis]], BOX_AT, out=d / "good.kicad_sch")
    # the OLD model, run from the pinned pre-fix bytes, sees NOTHING either way
    eq(prefix(bad.read_text(encoding="utf-8-sig")), [],
       f"the PRE-FIX +x model on a plate fired {axis.upper()} into a body")
    # the new one names it, on the bad sheet only
    r = must_fail(run([KPY, TOOL, bad, "--verbose"]),
                  f"S-OCCL on a plate fired {axis} into a body",
                  f"{INTO_BODY[axis][0]} x body U1")
    contains(r.out, "graded 2 of 2", "coverage line")
    must_pass(run([KPY, TOOL, good, "--verbose"]),
              f"S-OCCL on the same plate fired {axis} AWAY from the body")


@test("a plate fired RIGHT into a symbol body FAILS — and the pre-fix model, "
      "run from git, passes it", kind="known_bad")
def t_body_right():
    _axis_body_known_bad("right")


@test("a plate fired LEFT into a symbol body FAILS — the pre-fix model reads "
      "(0,'right') as reaching +x and passes it", kind="known_bad")
def t_body_left():
    """LEFT is not the mirror of RIGHT for the old model: it read the ANGLE
    only, so `(0, 'right')` — which KiCad renders reaching LEFT — came out
    pointing the other way entirely, at a patch of empty sheet."""
    _axis_body_known_bad("left")


@test("a plate fired UP into a symbol body FAILS — the axis the pre-fix model "
      "did not have", kind="known_bad")
def t_body_up():
    _axis_body_known_bad("up")


@test("a plate fired DOWN into a symbol body FAILS — the other half of the "
      "axis the pre-fix model did not have", kind="known_bad")
def t_body_down():
    """A fixture that only exercises the horizontal axis is exactly the blind
    spot under repair: 68 of 1507 fleet labels sit at 90/270 and every one of
    them was modelled reaching +x."""
    _axis_body_known_bad("down")


# ============================================ four axes, plate against plate
def _axis_pair_known_bad(axis):
    """No symbol on the sheet at all, so the verdict turns ONLY on which way
    the two plates point."""
    d = tmpdir(f"pair_{axis}_")
    p = sheet(PAIR[axis], (), out=d / "s.kicad_sch")
    eq(prefix(p.read_text(encoding="utf-8-sig")), [],
       f"the PRE-FIX +x model on two plates overlapping {axis.upper()}")
    must_fail(run([KPY, TOOL, p, "--verbose"]),
              f"S-OCCL on two plates overlapping along {axis}",
              "label QQAA x label QQBB")


@test("two plates overlapping to the RIGHT FAIL, with no symbol on the sheet "
      "— the verdict turns only on direction", kind="known_bad")
def t_pair_right():
    _axis_pair_known_bad("right")


@test("two plates overlapping to the LEFT FAIL, with no symbol on the sheet",
      kind="known_bad")
def t_pair_left():
    _axis_pair_known_bad("left")


@test("two plates overlapping UPWARD FAIL, with no symbol on the sheet",
      kind="known_bad")
def t_pair_up():
    _axis_pair_known_bad("up")


@test("two plates overlapping DOWNWARD FAIL, with no symbol on the sheet",
      kind="known_bad")
def t_pair_down():
    _axis_pair_known_bad("down")


# ================================================================ clean cases
@test("all four plates fired OUTWARD from one body is CLEAN, and the same "
      "four fired inward is four findings — one per axis")
def t_all_four_axes_at_once():
    d = tmpdir("occl4_")
    good = sheet(list(AWAY.values()), BOX_AT, out=d / "good.kicad_sch")
    bad = sheet(list(INTO_BODY.values()), BOX_AT, out=d / "bad.kicad_sch")
    occl, unm, graded, total = counts(good)
    eq(occl, [], "the outward sheet")
    eq(unm, [], "unplaced objects on the outward sheet")
    eq((graded, total), (5, 5), "coverage on the outward sheet")
    occl, _, _, _ = counts(bad)
    eq(sorted(occl), sorted(f"label {INTO_BODY[a][0]} x body U1"
                            for a in INTO_BODY),
       "the inward sheet names one finding per axis")
    # ...and the pre-fix model sees ZERO of the four
    eq(prefix(bad.read_text(encoding="utf-8-sig")), [],
       "the PRE-FIX model on all four axes at once")


@test("a label plate ABUTTING the pin it attaches to is not an occlusion — "
      "the segment-inside-box test makes attachment exactly zero")
def t_attachment_is_not_an_occlusion():
    """The first draft of this model gave pins a rectangular halo and reported
    605 of 605 smc0985-cooksense labels as occluding the pin they hang off, at
    an overlap of 2e-15 mm. Every label attaches at a wire end, which IS a pin
    tip, so that abutment is the NORMAL case and a model that reports it is
    unusable. A halo of 0.127 mm and an epsilon of 0.05 mm cannot both be had;
    asking how much of the pin LINE the text covers makes abutment exactly 0."""
    d = tmpdir("abut_")
    # BOX's pin 1 runs (88,104) -> (95,104) on the sheet.
    p = sheet([("AAAA", 88.0, 104.0, 0, "right")], BOX_AT,   # plate goes LEFT
              out=d / "s.kicad_sch")
    occl, unm, _, _ = counts(p)
    eq(occl, [], "a plate ending exactly on the pin tip it attaches to")
    eq(unm, [], "unplaced objects")
    # the CONTRAST, one field changed: the same plate laid ALONG the pin
    q = sheet([("AAAA", 88.0, 104.0, 0, "left")], BOX_AT, out=d / "b.kicad_sch")
    occl, _, _, _ = counts(q)
    check("label AAAA x pin U1.1" in occl,
          f"the same plate laid ALONG the pin must be a finding: {occl}")


@test("the real fleet sheets are graded with a full denominator and the two "
      "GRID-mode boards are clean")
def t_fleet_is_graded_with_a_denominator():
    """A live-bytes read, deliberately: these sheets are regenerated by other
    agents, so what is asserted is a PROPERTY that survives regeneration —
    every drawable object is PLACED (no silent skips) — plus the two boards
    whose emitter is v1's label grid, which has never had a direction defect
    and must stay at zero."""
    n = 0
    for p in sorted((ROOT / "projects").glob("*/04_kicad/*.kicad_sch")):
        occl, unm, graded, total = counts(p)
        eq(unm, [], f"{p.name}: drawable objects this model could not place")
        eq(graded, total, f"{p.name}: coverage")
        check(total > 0, f"{p.name}: nothing drawable found — the parser is "
                         f"reading nothing and would pass anything")
        if p.stem in ("cooksense", "usb_hub_3s_v2"):
            eq(occl, [], f"{p.stem} is a --mode grid sheet and must be clean")
        n += 1
    check(n >= 6, f"only {n} fleet sheets graded")


# =================================================================== coverage
@test("an object this model cannot PLACE is a FAIL naming it, never a pass "
      "(canon M-COVER)", kind="known_bad")
def t_unplaceable_object_fails():
    """`0 occlusions` over a sheet half of which was never placed reads exactly
    like a clean one. Measured 2026-07-31: 0 unplaced across all 8 fleet
    sheets, so this cannot be met by ignoring it."""
    d = tmpdir("unmod_")
    p = sheet([("AAAA", 200.0, 100.0, 0, "left")], BOX_AT, out=d / "s.kicad_sch")
    must_pass(run([KPY, TOOL, p]), "the sheet before the unplaceable object")
    t = p.read_text()
    t = t.replace('(global_label "AAAA" (shape passive) (at 200.0 100.0 0)',
                  '(global_label "AAAA" (shape passive) (at 200.0 100.0 45)')
    p.write_text(t)
    must_fail(run([KPY, TOOL, p]), "a global_label at an unmodelled angle",
              "could not be placed")
    # ...and a LOCAL label, which this model does not place either
    q = sheet([], BOX_AT, out=d / "q.kicad_sch")
    q.write_text(q.read_text().replace(
        '  (sheet_instances',
        '  (label "LOC" (at 200 100 0) (effects (font (size 1.27 1.27))))\n'
        '  (sheet_instances'))
    must_fail(run([KPY, TOOL, q]), "a local label", "global_label only")


@test("a lib_symbol PROTOTYPE is never placed on the page — its local coords "
      "would make every symbol collide with every other")
def t_prototypes_are_not_placed():
    """The shipped model got this right and the note is kept: all lib_symbols
    prototypes sit at the same local origin, so grading them produces pure
    false positives. Asserted rather than assumed, because the new parser walks
    `(lib_symbols ...)` for geometry and could easily place it twice."""
    d = tmpdir("proto_")
    p = sheet(list(AWAY.values()), BOX_AT, out=d / "s.kicad_sch")
    texts, rects, segs, unm, total = SO.parse_sheet(
        p.read_text(encoding="utf-8-sig"))
    eq(len(rects), 1, "body rectangles placed for ONE instance")
    eq(total, 5, "drawable objects: 4 labels + 1 instance, prototype excluded")


# ================================================================== vacuity
@test("VACUITY: a plate that completely covers a pin's NUMBER passes — pin "
      "name and number text is not placed", kind="vacuity",
      gate="sch_occlusion.py")
def t_vac_soccl_pin_name_text_is_not_placed():
    """THE DECLARED BLIND SPOT. KiCad derives a pin name's and number's
    position from the body edge, `pin_names (offset N)`, the hide flags and the
    instance rotation; modelling that wrongly would invent findings on every
    board, so the gap is NAMED rather than guessed.

    MEASURED by an ink sweep over the post-converter-fix sheets — every drawn
    pair whose rendered ink overlaps that this model does NOT report: 4 on
    pluto-rx2-8way-v2, 17 on pluto-cal-switch, 66 on crow-recorder-central-v2,
    0 on crow-mic-pod-v2; all but a few are pin-NUMBER against pin-NUMBER
    inside one dense auto-generated symbol.

    The blind spot is MEASURED here too, not claimed: the fixture renders the
    sheet and asserts that KiCad's pin-number ink really does sit inside the
    plate box that the gate just passed.

    THE CONTRAST comes second, per the vacuity convention: the same plate moved
    onto the pin LINE — one number changed — FAILS. That is what separates a
    blind spot from a fact the model cannot represent at all."""
    d = tmpdir("vacpin_")
    # pin 1 runs (88,104)->(95,104); KiCad draws its NUMBER above the line
    # (ink y 102.62-103.62) and its NAME inside the body. This plate spans
    # x 88.70-95.00, y 101.23-103.77 -> it COVERS the number entirely, abuts
    # the body at exactly 0 mm, and stops 0.23 mm short of the pin line.
    p = sheet([("VVVV", 95.0, 102.5, 0, "right")], BOX_AT, out=d / "s.kicad_sch")
    occl, unm, _, _ = counts(p)
    eq(unm, [], "unplaced objects")
    eq(occl, [], "a plate lying over a pin's NUMBER is not graded — the "
                 "declared blind spot")
    # ...and the number really is under it, per KiCad's own render
    must_pass(run(["kicad-cli", "sch", "export", "svg",
                   "--no-background-color", "-o", d, p]), "render")
    svg = (d / "s.svg").read_text()
    num = None
    for m in re.finditer(r'<g class="stroked-text"><desc>1</desc>(.*?)</g>',
                         svg, re.S):
        q = [(float(a), float(b)) for a, b in
             re.findall(r"(-?\d+\.?\d*)[ ,](-?\d+\.?\d*)", m.group(1))]
        if q and 88 < min(t[0] for t in q) < 95 and 100 < min(t[1] for t in q) < 106:
            num = (min(t[0] for t in q), min(t[1] for t in q),
                   max(t[0] for t in q), max(t[1] for t in q))
    check(num is not None, "KiCad rendered no pin NUMBER — the fixture cannot "
                           "demonstrate the blind spot it declares")
    box = SO.plate_box("VVVV", 95.0, 102.5, 0, "right")
    check(box[0] <= num[0] and box[1] <= num[1] and
          box[2] >= num[2] and box[3] >= num[3],
          f"the pin number ink {num} is not inside the passed plate {box} — "
          f"this fixture would be declaring a blind spot it does not exercise")
    # THE CONTRAST: the same plate on the pin LINE, one number changed.
    q = sheet([("VVVV", 95.0, 104.0, 0, "right")], BOX_AT, out=d / "q.kicad_sch")
    occl, _, _, _ = counts(q)
    check("label VVVV x pin U1.1" in occl,
          f"the CONTRAST: the same plate over the pin LINE must FAIL: {occl}")


# ======================================================== the width model
#: the string whose plate the flat model under-reaches by the most on a real
#: fleet sheet is 20 characters; this one is 17 and is a real central-v2 rail
#: name shape. Flat reach (17+2)*1.05 = 19.9500 mm; MEASURED reach
#: 1.3341 + 19.1710 = 20.5051 mm, i.e. the flat plate stops 0.5551 mm short.
LONGNAME = "AVDD_MCU_3V3_RAIL"


@test("the flat CH_W model scores CLEAN a sheet whose plates KiCad DRAWS "
      "overlapping — a real ink composite made invisible by a width model",
      kind="known_bad")
def t_flat_width_hides_a_real_overlap():
    """THE DANGEROUS DIRECTION, and the one the fleet's names take.

    `CH_W = 1.05` charges 1.05 mm per character. Every capital in the fleet
    advances 20/21, 21/21 or 22/21 of the 1.27 mm font — 1.2095 to 1.3305 mm —
    so the flat plate is SHORT for every all-capitals name, and a plate the
    gate believes stops short of its neighbour is one KiCad draws straight
    through it.

    THIS IS NOT HYPOTHETICAL. Re-grading the eight fleet sheets across this fix
    turned up exactly two findings the flat model was hiding, and BOTH were
    confirmed against KiCad's own render:
      * crow-recorder-central-v2 `label USB_VDD33 x pin FB_u33.1` — the pin
        sits 12.065 mm from the anchor, flat reach 11.550, true 12.159, so
        0.0943 mm of the rendered pin line lies inside the rendered plate;
      * pluto-cal-switch `label HDR_CTRL_ADC x pin U_MCU.19` — pin at 15.240 mm,
        flat reach 14.700, true 15.304: the ENTIRE 1.2700 mm pin line is buried
        under the plate KiCad draws, and the flat model reported nothing.

    RED SIDE: the flat model is not paraphrased here, it is LOADED FROM GIT
    (`flat_module()`, FLAT_COMMIT) and run on the same file — same direction
    model, same symbol geometry, `CH_W = 1.05` the only difference.

    GIT-SWAP RED-VERIFIED, 2026-07-31. `skills/kicad-pcb/scripts/sch_occlusion.py`
    was replaced wholesale by `git show c90c51c3:...` and this suite run —
    **17 passed / 5 failed**; restored **22 passed / 0 failed / 11 known-bad +
    1 vacuity**. The five reds, and FOUR OF THEM RED ON THE MEASUREMENT rather
    than on a crash, which is the only kind of red that proves anything:

      this fixture           "SHOULD HAVE FAILED but exited 0" — the missed
                             overlap itself
      its mirror             "should have exited 0, got 1" — the invented one
      the upper bound        "the model box disagrees with the box KiCad DREW
                             by 1.665400 mm on some plate"
      unmeasured character   "SHOULD HAVE FAILED but exited 0"
      the measured table     AttributeError on `ADV21` — red by ABSENCE, and
                             honestly so: the flat model has no per-character
                             table for the fixture to re-derive.

    Both width fixtures assert through the CLI BEFORE touching any module
    attribute, precisely so the swap cannot red them for a renamed constant and
    leave the real claim untested; the first draft of this file did exactly
    that on five of six and it looked like a pass.

    The nine DIRECTION known-bads and the `label_sides_v` fixture stay GREEN
    under the swap — c90c51c3 already had the direction model right — which is
    the discrimination that makes these five mean "the width model", not "some
    module changed".
    """
    d = tmpdir("flatmiss_")
    # B's plate starts 20.25 mm from A's anchor: past the flat reach (19.95)
    # and inside the measured one (20.5051), so the verdict turns ONLY on the
    # width model. No symbol on the sheet at all.
    p = sheet([(LONGNAME, 100.0, 100.0, 0, "left"),
               ("QQ", 120.25, 100.0, 0, "left")], (), out=d / "s.kicad_sch")
    # THE SUBSTANTIVE ASSERTION COMES FIRST, and it goes through the CLI rather
    # than through any module attribute, so swapping the flat module back in
    # reds this fixture with "SHOULD HAVE FAILED but exited 0" — the missed
    # overlap itself — and not with an AttributeError on a renamed constant.
    must_fail(run([KPY, TOOL, p, "--verbose"]),
              "S-OCCL on the long-name overlap the flat model cannot reach",
              f"label {LONGNAME} x label QQ")
    eq(flat(p), [], "the FLAT-WIDTH model, loaded from git, on a sheet whose "
                    "plates KiCad draws overlapping")
    check(abs(SO.plate_span(LONGNAME) - 20.5051) < 1e-3,
          f"the measured reach moved: {SO.plate_span(LONGNAME):.4f}")
    # ...and KiCad's OWN INK agrees that they overlap
    svg = svg_of(p, d)
    pl = drawn_plates(svg)
    a = pl[(100.0, 100.0)][0]
    b = pl[(120.25, 100.0)][0]
    ov = min(a[2], b[2]) - max(a[0], b[0])
    check(ov > SO.OVERLAP_EPS_MM,
          f"KiCad's own plates overlap by only {ov:.4f} mm — this fixture "
          f"would be asserting a finding the render does not support")
    check(a[2] - 100.0 > (len(LONGNAME) + 2) * 1.05,
          f"the rendered plate reaches {a[2] - 100.0:.4f} mm, not past the "
          f"flat model's {(len(LONGNAME) + 2) * 1.05:.4f} — no defect to pin")


@test("the mirror: an IIII-class narrow name the flat CH_W model scores DIRTY "
      "and KiCad draws 0.2469 mm APART")
def t_flat_width_invents_an_overlap():
    """The other half, and the half that dominates this fleet numerically.

    `I` advances 10/21 of the font = 0.6048 mm against a flat 1.05, so `IIII`
    reaches 3.7531 mm where the flat model claims 6.3000 — 2.5469 mm of plate
    that does not exist. The real fleet version is shorter and commoner: `3V3`
    reaches 4.9627 mm against a flat 5.2500, and that 0.2873 mm of phantom
    plate is what produced 30 of the 34 findings crow-recorder-central-v2 lost
    across this fix (`label 3V3 x body U1`, `x body U3`, `x body U4`, ...).

    47 of the fleet's 1191 flat-model findings were this, against 2 the flat
    model was hiding: the flat model was noisier AND blinder at the same time.
    """
    d = tmpdir("flatinvent_")
    p = sheet([("IIII", 200.0, 100.0, 0, "left"),
               ("IIII", 204.0, 100.0, 0, "left")], (), out=d / "s.kicad_sch")
    # CLI first, for the same reason as the fixture above: swapped back to the
    # flat module this reds with "should have exited 0, got 1" — the invented
    # finding — rather than with an AttributeError.
    must_pass(run([KPY, TOOL, p, "--verbose"]),
              "S-OCCL on two narrow plates the flat model calls colliding")
    fl = flat(p)
    check(fl, "the FLAT-WIDTH model was expected to report this sheet DIRTY — "
              "without that this fixture pins nothing")
    eq(fl, ["label IIII x label IIII"], "what the flat model invents here")
    check(abs(SO.plate_span("IIII") - 3.7531) < 1e-3,
          f"the measured reach moved: {SO.plate_span('IIII'):.4f}")
    # ...and KiCad's OWN INK agrees they do NOT touch
    svg = svg_of(p, d)
    pl = drawn_plates(svg)
    a = pl[(200.0, 100.0)][0]
    b = pl[(204.0, 100.0)][0]
    gap = b[0] - a[2]
    check(gap > 0, f"KiCad's own plates DO overlap by {-gap:.4f} mm — the flat "
                   f"model would be right and this fixture wrong")
    check(abs(gap - 0.2469) < 2e-3, f"rendered gap {gap:.4f} mm, expected "
                                    f"0.2469 mm")


@test("the model NEVER under-reaches the ink: every one of the 1507 real fleet "
      "plates matches the box KiCad DREW, and every glyph run sits inside it")
def t_the_model_is_an_upper_bound_on_ink():
    """A width model that can under-report is the failure under repair, so the
    property is asserted rather than implied — on the REAL fleet, not on a
    probe, because a probe cannot be accused of being chosen.

    THREE CLAIMS, all measured here every run:

      1. `plate_box` equals the plate KiCad draws. MEASURED: worst edge
         disagreement 0.000210 mm over 1507 plates — the SVG's own 4-decimal
         quantisation. The FLAT model, run over the same 1507, is too SHORT on
         596 (worst 1.6654 mm) and too WIDE on 911 (worst 1.1173 mm) and EXACT
         ON ZERO.
      2. the label's own glyph run sits strictly INSIDE its plate box with the
         0.1524 mm pen counted (MEASURED minimum margin 0.4029 mm), so the box
         bounds the ink and not merely the outline.
      3. the advance sum is an upper bound on a run's drawn ink — the last
         character's trailing side bearing is advanced over and never drawn.

    THE RESIDUAL IS NAMED, not hidden. This is a CENTRELINE model: KiCad strokes
    every glyph and plate with a 0.1524 mm pen, so ink reaches 0.0762 mm beyond
    every centreline — on BOTH sides of every comparison. Two objects whose
    centreline boxes overlap therefore certainly overlap in ink; two clearing
    each other by less than 0.1524 mm may still touch and are not reported.
    Inflating instead is not available: it would make every label overlap the
    pin it attaches to by exactly the pen width (see
    `t_attachment_is_not_an_occlusion`).
    """
    d = tmpdir("upperbound_")
    # the pen and the 5-argument `plate_box` call are BOTH deliberate: this
    # fixture must red on the MEASUREMENT when the flat module is swapped back
    # in, not on an AttributeError for a constant that model never had. Every
    # fleet label is `passive` at the 1.27 mm font (asserted below), so the
    # 5-argument form is exactly right for this population.
    half = getattr(SO, "PEN_MM", 0.1524) / 2.0
    n = props = worst = 0
    margin = 1e9
    flat_short = flat_wide = flat_exact = 0
    worst_short = worst_wide = 0.0
    sheets = []
    for p in sorted((ROOT / "projects").glob("*/04_kicad/*.kicad_sch")):
        stxt = p.read_text(encoding="utf-8-sig")
        svg = svg_of(p, d)
        pl, runs = drawn_plates(svg), drawn_runs(svg)
        body = stxt
        lb = SO._block(stxt, "(lib_symbols")
        if lb:
            body = stxt.replace(lb, "")
        for m in SO._RE_GLABEL.finditer(body):
            name, blk = m.group(1), m.group(2)
            am = re.search(r"\(at ([-\d.]+) ([-\d.]+) (\d+)\)", blk)
            jm = re.search(r"\(justify ([\w ]+)\)", blk)
            fm = re.search(r"\(font \(size ([\d.]+) [\d.]+\)", blk)
            sm = re.search(r"\(shape (\w+)\)", blk)
            gx, gy = float(am.group(1)), float(am.group(2))
            ang = int(am.group(3))
            just = SO._justify_sense(jm.group(1) if jm else None)
            eq((fm.group(1), sm.group(1)), ("1.27", "passive"),
               f"{p.name}: a fleet label that is not passive at the 1.27 mm "
               f"font — the 5-argument plate_box call below would be modelling "
               f"the wrong shape or size")
            box = SO.plate_box(name, gx, gy, ang, just)
            got = pl.get((round(gx, 3), round(gy, 3)))
            check(got, f"{p.name}: KiCad drew no plate at ({gx}, {gy}) for "
                       f"{name!r} — the anchor keying is wrong and this test "
                       f"would be measuring nothing")
            g = min(got, key=lambda q: sum(abs(q[k] - box[k]) for k in range(4)))
            worst = max(worst, max(abs(g[k] - box[k]) for k in range(4)))
            ux, _ = SO.PLATE_DIR[(ang, just)]
            rr = (max(g[2] - gx, gx - g[0]) if ux else max(g[3] - gy, gy - g[1]))
            fr = (len(name) + 2) * 1.05
            if fr < rr - 5e-4:
                flat_short += 1
                worst_short = max(worst_short, rr - fr)
            elif fr > rr + 5e-4:
                flat_wide += 1
                worst_wide = max(worst_wide, fr - rr)
            else:
                flat_exact += 1
            cand = [r for r in runs.get(name, [])
                    if box[0] - 1 <= r[0] and r[2] <= box[2] + 1
                    and box[1] - 1 <= r[1] and r[3] <= box[3] + 1]
            if cand:
                r = min(cand, key=lambda q: (q[0] - box[0]) ** 2
                        + (q[1] - box[1]) ** 2)
                margin = min(margin, r[0] - half - box[0], box[2] - r[2] - half,
                             r[1] - half - box[1], box[3] - r[3] - half)
            n += 1
        sheets.append((p, body, runs))
    # THE PLATE CLAIM IS ASSERTED BEFORE THE PROPERTY LOOP RUNS, deliberately:
    # swap the flat module back in and this is what reds, with the measurement
    # in the message. Interleaving the two would let a structural difference in
    # the older module's regexes raise first and mask it.
    check(n >= 1500, f"only {n} fleet plates compared against rendered ink")
    check(worst < 1e-3,
          f"the model box disagrees with the box KiCad DREW by {worst:.6f} mm "
          f"on some plate — the width model is not an upper bound")
    check(margin > 0,
          f"a label's own glyph ink escapes its plate box by {-margin:.4f} mm "
          f"with the pen counted")
    eq(flat_exact, 0, f"plates the flat (len+2)*1.05 model gets right out of "
                      f"{n} — if this is not 0 the defect has changed shape")
    check(flat_short > 0 and flat_wide > 0,
          f"the flat model errs in only one direction here (short {flat_short}, "
          f"wide {flat_wide}) — the two-directional claim would be wrong")
    check(worst_short > 1.0,
          f"worst flat under-reach only {worst_short:.4f} mm")

    for p, body, runs in sheets:
        # PROPERTY text has no plate to hide behind: its box IS the model's
        # own arithmetic, so it is checked against the ink directly.
        for im in SO._RE_INST.finditer(body):
            for pm in SO._RE_PROP.finditer(im.group(5)):
                kind, txt, gx, gy, pang, fs, just, tail = (
                    pm.group(1), pm.group(2), float(pm.group(3)),
                    float(pm.group(4)), int(pm.group(5)), float(pm.group(6)),
                    pm.group(7), pm.group(8))
                if "hide" in tail or not txt or pang:
                    continue
                side = next((t for t in (just or "").split()
                             if t in ("left", "right")), None)
                pb = SO.prop_box(txt, gx, gy, fs, side)
                near = [r for r in runs.get(txt, [])
                        if abs((r[0] + r[2]) / 2 - (pb[0] + pb[2]) / 2) < 1.5
                        and abs((r[1] + r[3]) / 2 - gy) < 1.5]
                if not near:
                    continue
                r = min(near, key=lambda q: abs((q[1] + q[3]) / 2 - gy))
                check(pb[0] <= r[0] + 1e-3 and r[2] <= pb[2] + 1e-3
                      and pb[1] <= r[1] + 1e-3 and r[3] <= pb[3] + 1e-3,
                      f"{p.name}: the rendered ink of {kind} {txt!r} "
                      f"{tuple(round(v, 4) for v in r)} escapes the model's "
                      f"property box {tuple(round(v, 4) for v in pb)}")
                props += 1
    # 1566 is the WHOLE placed-property population of the fleet (70 + 398 +
    # 146 + 128 + 56 + 478 + 46 + 244), MEASURED — every one of them located
    # in the render and contained by the model's box, none skipped.
    check(props >= 1550, f"only {props} fleet property texts compared against "
                         f"rendered ink — the property half of the model would "
                         f"be going ungraded")


@test("a character the advance table has never measured is UNPLACED and named, "
      "never modelled with a guess (canon M-COVER in a geometry model)",
      kind="known_bad")
def t_unmeasured_character_is_unplaced():
    """The table covers 98 characters — all printable ASCII plus the three
    non-ASCII glyphs the fleet draws (`°`, `µ`, `Ω`; `Ω` appears in property
    Values). MEASURED: 0 unmeasured characters across all 8 fleet sheets, so
    this cannot be satisfied by ignoring it.

    A guessed advance is the same defect one level down: a character silently
    charged the wrong width produces a plate box that is wrong in an unknown
    direction, and 'unknown direction' includes 'too short'."""
    d = tmpdir("unmchar_")
    p = sheet([("AAAA", 200.0, 100.0, 0, "left")], BOX_AT, out=d / "s.kicad_sch")
    must_pass(run([KPY, TOOL, p]), "the sheet before the unmeasured character")
    p.write_text(p.read_text().replace('(global_label "AAAA"',
                                       '(global_label "AĀAA"'),
                 encoding="utf-8")
    r = must_fail(run([KPY, TOOL, p]), "a label naming an unmeasured character",
                  "unmeasured character")
    contains(r.out, "could not be placed", "the M-COVER wording")
    contains(r.out, "Ā", "the offending character must be NAMED")


# ============================================ the shipped fixture that was dirty
@test("label_sides_v is clean ONLY because the de-collision pass moves it — "
      "held off, its own plates run through its own Reference and Value")
def t_label_sides_v_is_clean_only_because_the_pass_moves_it():
    """FIXING A SHIPPED FIXTURE THAT WAS PRESENTED AS CLEAN.

    `t1_converter.py t_label_sides_vertical` passes `label_sides_v` and reads
    as a clean bill. It is not one: that test grades plate-vs-BODY and
    plate-vs-PLATE only, and this fixture's defect is plate-vs-PROPERTY. R1 is
    placed vertically, so its Reference and its Value are centred on the same x
    as both vertical plates, and both plates are drawn straight through them.

    MEASURED here, with the converter's `place_labels` held off — which is
    exactly the pre-pass converter, not a synthetic mutation:
        label OUT_MID_LONG_NAME x Value 1k
        label TAP_MID_LONG_NAME x Reference R1
    and 0 with the pass on. `label_sides_h` and `two_resistors` are 0 either
    way, so the pass is not merely reshuffling every sheet it touches.

    WHY THIS FIXTURE IS WORTH ITS RUNTIME. It is the same shape as the finding
    that governs this whole gate: **a repair pass can produce a green verdict
    over a sheet that is still wrong.** Run the pass over the PRE-FIX label
    DIRECTION derivation and the sheet also comes out with zero collisions,
    every plate still pointing at the wrong pin. A green S-OCCL is evidence
    about legibility after the pass, and about nothing before it.
    """
    conv = SCRIPTS / "circuit_json_to_kicad_sch.py"
    d = tmpdir("lsv_")
    shim = d / "no_decollide.py"
    shim.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import circuit_json_to_kicad_sch as C\n"
        "C.place_labels = lambda cands, *a, **k: (cands, [], [], 0, [])\n"
        f"sys.argv = [{str(conv)!r}] + sys.argv[1:]\n"
        "C.main()\n", encoding="utf-8")
    cj = ROOT / "tests" / "fixtures" / "t0" / "label_sides_v" / "circuit.json"
    check(cj.is_file(), f"the shipped fixture is gone: {cj}")

    on = d / "on.kicad_sch"
    must_pass(run([KPY, conv, cj, "-o", on, "--project", "lsv"]), "convert")
    must_pass(run([KPY, TOOL, on, "--verbose"]),
              "S-OCCL on label_sides_v as the pipeline emits it")

    off = d / "off.kicad_sch"
    must_pass(run([KPY, shim, cj, "-o", off, "--project", "lsv"]),
              "convert with the de-collision pass held off")
    occl, unm, graded, total = counts(off)
    eq(unm, [], "unplaced objects on the un-de-collided sheet")
    eq(sorted(occl), ["label OUT_MID_LONG_NAME x Value 1k",
                      "label TAP_MID_LONG_NAME x Reference R1"],
       "what the SHIPPED fixture draws before the pass rescues it")
    # the CONTROL fixtures are clean either way — so the pass is not just
    # moving everything it is handed.
    #
    # `two_resistors` WAS ONE OF THESE AND IS NOT ANY MORE (2026-07-31). Once
    # this model learned to parse a wire, its `MID` plate — anchored
    # (38.100,27.940) reaching +x, with its own wire running to (50.800,27.940)
    # — reads as `label MID x wire`, and the render agrees: 2.7819 mm of
    # conductor through the three glyphs. It was called clean for exactly as
    # long as nothing here had ever seen a wire. `thermal_ep` (7 plates, 0
    # wires) takes its place as the second control.
    for fx in ("label_sides_h", "thermal_ep"):
        q = d / f"{fx}.kicad_sch"
        must_pass(run([KPY, shim, ROOT / "tests" / "fixtures" / "t0" / fx /
                       "circuit.json", "-o", q, "--project", fx]),
                  f"convert {fx} with the pass off")
        eq(counts(q)[0], [], f"{fx} un-de-collided — the control")


# ================================================ wires: population and S-WNET
#: the commit that carries the WIRE-BLIND `sch_occlusion.py` — the module whose
#: `grep -c wire` is 1 and whose one hit is a comment. Pinned rather than
#: `HEAD~1` so the A/B keeps measuring the same red side after this lands.
NOWIRE_COMMIT = "6ef7b516"
_NOWIRE_CACHE = []


def nowire_module():
    """The WIRE-BLIND `sch_occlusion.py`, loaded from git and importable.

    The whole module as it stood at NOWIRE_COMMIT, so the A/B below differs
    from HEAD in the OBJECT SET and in nothing else.
    """
    if _NOWIRE_CACHE:
        return _NOWIRE_CACHE[0]
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         f"{NOWIRE_COMMIT}:skills/kicad-pcb/scripts/sch_occlusion.py"],
        capture_output=True, text=True)
    check(blob.returncode == 0,
          f"git show {NOWIRE_COMMIT} failed: {blob.stderr}")
    # THE GUARD IS THE POINT. A red side that only proves the module CHANGED is
    # worthless; this asserts the pinned bytes are specifically wire-blind, so
    # if someone re-points the constant the A/B says so instead of going quiet.
    check("_RE_WIRE" not in blob.stdout and "wire_net_ambiguity" not in blob.stdout,
          f"{NOWIRE_COMMIT}:sch_occlusion.py already knows about wires — this "
          f"A/B would silently stop measuring the red side")
    nwire = sum(1 for ln in blob.stdout.splitlines()
                if "wire" in ln and not ln.lstrip().startswith("#"))
    check(nwire == 0,
          f"{NOWIRE_COMMIT}:sch_occlusion.py mentions wire on {nwire} "
          f"non-comment line(s) — not the wire-blind model")
    p = tmpdir("nowireso_") / "nowire_sch_occlusion.py"
    p.write_text(blob.stdout, encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location("nowire_sch_occlusion", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _NOWIRE_CACHE.append(mod)
    return mod


#: the commit whose wire exemption forgave ANY wire touching a plate's anchor,
#: regardless of which way it left. Pinned so this A/B keeps measuring the same
#: red side after the direction-scoped rule lands.
GENEROUS_COMMIT = "c0e21fa7"
_GENEROUS_CACHE = []


def generous_module():
    """`sch_occlusion.py` with the DIRECTION-BLIND attachment exemption."""
    if _GENEROUS_CACHE:
        return _GENEROUS_CACHE[0]
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         f"{GENEROUS_COMMIT}:skills/kicad-pcb/scripts/sch_occlusion.py"],
        capture_output=True, text=True)
    check(blob.returncode == 0,
          f"git show {GENEROUS_COMMIT} failed: {blob.stderr}")
    # the guard: the pinned bytes must really carry the OLD exemption, so a
    # re-pointed constant is reported instead of quietly ending the A/B.
    check("_RE_WIRE" in blob.stdout,
          f"{GENEROUS_COMMIT} is wire-blind — that is a different fixture")
    check("PLATE_DIR[(ang, just)]))" not in blob.stdout,
          f"{GENEROUS_COMMIT} already carries the direction-scoped exemption — "
          f"this A/B would silently stop measuring the red side")
    p = tmpdir("genso_") / "generous_sch_occlusion.py"
    p.write_text(blob.stdout, encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location("generous_sch_occlusion", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _GENEROUS_CACHE.append(mod)
    return mod


@test("a wire leaving a plate's anchor FORWARD is drawn through the name and "
      "IS a finding — the direction-blind exemption forgave it", kind="known_bad")
def t_the_attachment_exemption_is_scoped_by_direction():
    """THE EXEMPTION HAD TO EXIST, AND IT WAS TOO WIDE.

    A global_label attaches at a wire END and its plate STARTS there, so the
    conductor it names lies on the plate's base edge and Liang-Barsky charges
    up to a full PLATE_CROSS of it as "inside". Forgiving that is right.
    Forgiving EVERY wire that touches the anchor is not: a wire leaving the
    anchor into the half-space the plate reaches into runs down the plate's own
    centreline, straight through the letters.

    MEASURED, and it is not hypothetical — the shipped `two_resistors` fixture
    draws exactly this: `MID` at (38.100,27.940) reaching +x with its own wire
    running (38.100,27.940)-(50.800,27.940), which is **2.7819 mm of conductor
    through three glyphs in KiCad's own render** and 0 findings from the
    direction-blind model. It counted as a CLEAN CONTROL in two test files.

    THREE CASES ON ONE SHEET, so the exemption is measured on both sides of the
    line it draws rather than only where it now bites:
      * FORWARD  — plate reaching +x from (100,130), wire (100,130)->(120,130):
                   a finding here, forgiven by the pinned module.
      * BEHIND   — same plate, wire (80,130)->(100,130): forgiven by BOTH, and
                   it must be, or every label on every wired sheet moves.
      * PERPENDICULAR — wire (100,120)->(100,130): the base-edge case the
                   exemption exists for; forgiven by BOTH.
    """
    old = generous_module()
    d = tmpdir("fwdwire_")
    cases = [
        ("forward", (100.0, 130.0, 120.0, 130.0), True),
        ("behind", (80.0, 130.0, 100.0, 130.0), False),
        ("perpendicular", (100.0, 120.0, 100.0, 130.0), False),
    ]
    for tag, w, want_finding in cases:
        p = sheet([("AAAA", 100.0, 130.0, 0, "left")], (),
                  wires=[w], out=d / f"{tag}.kicad_sch")
        stxt = p.read_text(encoding="utf-8-sig")
        got = [f for f in SO.occlusions(stxt)[0] if "x wire" in f]
        red = [f for f in old.occlusions(stxt)[0] if "x wire" in f]
        eq(red, [], f"{tag}: the DIRECTION-BLIND model reported a wire finding "
                    f"— it forgives every wire on the anchor, so it cannot")
        if want_finding:
            check(got, f"{tag}: a conductor drawn down the plate's centreline "
                       f"is not reported — the exemption is still too wide")
        else:
            eq(got, [], f"{tag}: the real attachment must stay forgiven, or "
                        f"every label on every wired sheet becomes a finding")


@test("a WIRE drawn through a label plate is a finding — and the wire-blind "
      "model, run from git, reports the sheet CLEAN and FULLY GRADED",
      kind="known_bad")
def t_a_wire_through_a_plate_is_a_finding():
    """THE RED SIDE IS A MEASUREMENT, NOT AN IMPORT ERROR. The pinned module
    does not merely lack a function — it returns 0 findings and a coverage
    ratio of 1 over a sheet with a conductor drawn straight through a name.
    That is what made this class invisible on every wired board in the fleet:
    not a wrong constant, a missing OBJECT SET.

    Geometry: plate `AAAA` anchored (100,130) reaching RIGHT, so it occupies
    x in [100, ~106]; the wire runs x=103 vertically across it."""
    d = tmpdir("wirepop_")
    p = sheet([("AAAA", 100.0, 130.0, 0, "left")], BOX_AT,
              wires=[(103.0, 120.0, 103.0, 140.0)], out=d / "s.kicad_sch")
    # RED: the wire-blind model sees a clean, fully-covered sheet
    occl0, unm0, graded0, total0 = nowire_module().occlusions(
        p.read_text(encoding="utf-8-sig"))
    eq(occl0, [], "the wire-blind model reported a finding it cannot reach")
    eq(unm0, [], "the wire-blind model left something unplaced")
    check(graded0 == total0 == 2,
          f"the wire-blind model graded {graded0} of {total0} — it should see "
          f"exactly the label and the symbol, and NOT the wire")
    # GREEN: the wire is in the population and the finding is named
    occl, unm, graded, total = counts(p)
    eq(unm, [], "unplaced objects")
    check(graded == total == 3,
          f"graded {graded} of {total} — the wire must be counted")
    check(any(f.startswith("label AAAA x wire") for f in occl),
          f"the wire through the plate is not reported: {occl}")


@test("two nets drawn as ONE conductor FAIL S-WNET, and a junction dot is not "
      "offered as the repair", kind="known_bad")
def t_two_nets_one_conductor_fails():
    """The pluto-rx2-8way-v2 defect in miniature, both shapes of it.

    RED SIDE, and it is the same measurement rather than a missing attribute:
    the wire-blind model returns 0 findings and full coverage over this sheet.
    """
    d = tmpdir("wnet_")
    # NETA runs y=100..140 at x=200; NETB runs y=130..160 at the SAME x, so
    # they share 10 mm of ink and NETB's end at y=130 is inside NETA.
    p = sheet([("NETA", 200.0, 100.0, 90, "left"),
               ("NETB", 200.0, 160.0, 90, "right")],
              symbols=(), libs=(),
              wires=[(200.0, 100.0, 200.0, 140.0),
                     (200.0, 130.0, 200.0, 160.0)], out=d / "s.kicad_sch")
    # RED
    occl0, unm0, g0, t0 = nowire_module().occlusions(
        p.read_text(encoding="utf-8-sig"))
    eq(occl0, [], "the wire-blind model reported something here")
    check(g0 == t0 == 2, f"the wire-blind model graded {g0} of {t0} — it "
                         f"counts the two labels and neither wire")
    # GREEN
    bad = SO.wire_net_ambiguity(p.read_text(encoding="utf-8-sig"))
    check(any("share" in f and "collinear ink" in f for f in bad),
          f"the collinear overlap is not reported: {bad}")
    r = must_fail(run([KPY, TOOL, p]), "S-WNET on two nets drawn as one wire",
                  "S-WNET FAIL")
    contains(r.out, "NETA", "the failing message names the nets")
    # ...and the CONTRAST, one field changed: move NETB clear and it is clean
    q = sheet([("NETA", 200.0, 100.0, 90, "left"),
               ("NETB", 210.0, 160.0, 90, "right")],
              symbols=(), libs=(),
              wires=[(200.0, 100.0, 200.0, 140.0),
                     (210.0, 130.0, 210.0, 160.0)], out=d / "ok.kicad_sch")
    eq(SO.wire_net_ambiguity(q.read_text(encoding="utf-8-sig")), [],
       "two nets on DIFFERENT lines must be clean")


@test("a CROSSING is not a T: a net that continues out the far side is not a "
      "finding, and that discriminator is what makes S-WNET usable")
def t_a_crossing_is_not_a_t():
    """THE FALSE-POSITIVE CONTROL, and it carries most of the fleet.

    MEASURED 2026-07-31: without it the fleet reads 8 endpoint-in-interior
    events, of which 5 are ordinary undotted crossings — including
    crow-recorder-central-v2's 3V3-against-0V9 pair, which reads as a POWER
    RAIL SHORT on a raw scan and is a 3V3 wire passing straight through the
    0V9 rail to U1 pin 10 (w169/w170 are collinear and both 3V3). A gate that
    called those defects would be waived within a week."""
    d = tmpdir("cross_")
    # NETB runs horizontally THROUGH NETA's vertical at (200,120), split into
    # two collinear halves at the crossing — exactly what the emitter does.
    p = sheet([("NETA", 200.0, 100.0, 90, "left"),
               ("NETB", 190.0, 120.0, 0, "right")],
              symbols=(), libs=(),
              wires=[(200.0, 100.0, 200.0, 140.0),
                     (190.0, 120.0, 200.0, 120.0),
                     (200.0, 120.0, 210.0, 120.0)], out=d / "s.kicad_sch")
    eq(SO.wire_net_ambiguity(p.read_text(encoding="utf-8-sig")), [],
       "a wire crossing another and carrying on is not an ambiguity")
    # and the CONTRAST: delete the far half and the same point becomes a T
    q = sheet([("NETA", 200.0, 100.0, 90, "left"),
               ("NETB", 190.0, 120.0, 0, "right")],
              symbols=(), libs=(),
              wires=[(200.0, 100.0, 200.0, 140.0),
                     (190.0, 120.0, 200.0, 120.0)], out=d / "t.kicad_sch")
    bad = SO.wire_net_ambiguity(q.read_text(encoding="utf-8-sig"))
    check(any("ends inside" in f for f in bad),
          f"a wire that STOPS on another net's wire must be reported: {bad}")


@test("a junction dot at a SAME-net T clears it, and S-WNET never asks for one "
      "at a different-net T (a dot there is the short, not the annotation)")
def t_the_dot_is_not_the_repair():
    """MEASURED against kicad-cli 10.0.4 on a four-case probe: a junction dot
    MERGES the two nets, a dotless T does not. So dotting a different-net T
    converts a drawing defect into a real short — which is why the emitter's
    remedy is `disambiguate_wires` (drop ink) and never a dot."""
    d = tmpdir("dot_")
    # SAME net either side: one label, so both wires read NETA. Dotted or not,
    # this is never an S-WNET finding — the gate is about net IDENTITY.
    p = sheet([("NETA", 200.0, 100.0, 90, "left")], symbols=(), libs=(),
              wires=[(200.0, 100.0, 200.0, 140.0),
                     (200.0, 120.0, 210.0, 120.0)], out=d / "same.kicad_sch")
    eq(SO.wire_net_ambiguity(p.read_text(encoding="utf-8-sig")), [],
       "a T within ONE net is not two nets drawn as one conductor")
    # DIFFERENT nets, and now WITH a dot: still a finding is wrong, but the
    # dot must not SILENCE it — assert the gate keys on the geometry, and that
    # adding the dot is not a way to make this sheet pass.
    q = sheet([("NETA", 200.0, 100.0, 90, "left"),
               ("NETB", 212.0, 120.0, 0, "left")], symbols=(), libs=(),
              wires=[(200.0, 100.0, 200.0, 140.0),
                     (200.0, 120.0, 212.0, 120.0)], out=d / "diff.kicad_sch")
    check(SO.wire_net_ambiguity(q.read_text(encoding="utf-8-sig")),
          "a different-net T with no dot must be a finding")


@test("the fleet carries NO two-nets-as-one-conductor except the named, "
      "measured exception on a sealed board")
def t_fleet_wire_ambiguity_is_bounded():
    """A live-bytes read over every `04_kicad` sheet. The one exception is
    NAMED rather than thresholded, so a NEW board or a regression cannot hide
    behind a count.

    crow-recorder-central-v2 is SEALED at v1.7 and its `.kicad_sch` is
    byte-identical to `04_kicad` (MEASURED). Its 3 findings are one defect:
    `MID5P` (321.310-323.850) and `ADC5P` (323.215-328.930) share 0.6350 mm at
    y=164.465, a 7.62 mm continuous run carrying two nets while `Rs5P` — the
    series resistor that separates them — is drawn 20.3 mm away at x=344.170.
    The copper is sound (netlist pin sets disjoint), so this is a drawing
    defect on a sealed release and is carried here as a measured fact until a
    release is cut for another reason."""
    EXPECT = {"crow_recorder_central_v2": 3}
    seen = 0
    for p in sorted((ROOT / "projects").glob("*/04_kicad/*.kicad_sch")):
        bad = SO.wire_net_ambiguity(p.read_text(encoding="utf-8-sig"))
        eq(len(bad), EXPECT.get(p.stem, 0),
           f"{p.stem}: two-nets-as-one-conductor findings {bad}")
        seen += 1
    check(seen >= 6, f"only {seen} fleet sheets scanned")


if __name__ == "__main__":
    sys.exit(main())
