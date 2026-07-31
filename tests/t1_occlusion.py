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


def sheet(labels=(), symbols=(), libs=(BOX_LIB,), out=None):
    """Write a minimal one-page .kicad_sch.

    labels:  (name, x, y, angle, justify_or_None)
    symbols: (lib_id, x, y, angle, reference, value_or_None)
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
    L += ['  (sheet_instances (path "/" (page "1")))', ')']
    p = (out or (tmpdir("occl_") / "s.kicad_sch"))
    p.write_text("\n".join(L) + "\n")
    return p


#: A body at (100,100) spans (95,95)-(105,105). Each entry fires a 4-char
#: plate (reach 6*1.05 = 6.30 mm) from 10 mm out, so it ends 1.30 mm INSIDE
#: the body — the same overlap on all four axes, so no axis is easier.
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
    eq(sorted(cross), [SO.CH_H],
       "the plate CROSS extent KiCad renders, against the model's CH_H — the "
       "shipped model said 2.2 and was 13% narrow")


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


if __name__ == "__main__":
    sys.exit(main())
