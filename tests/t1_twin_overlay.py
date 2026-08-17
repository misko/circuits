#!/usr/bin/env python3
"""T1: twin_overlay.py — canon A-RENDER, the gate that asks whether the twin
RENDER is faithful to the BOARD.

THE INCIDENT (2026-07-26). `twin_overlay.py` shipped with a checker's
docstring and computed NO BODY POSITION ANYWHERE. It projected courtyards out
of the board and drew boxes; its only non-zero exits concerned the IMAGE. It
was wired into no pipeline stage, had no contract Audit row, and had no
known-bad fixture, so nothing could observe that it graded nothing. Meanwhile
the thing it claimed to catch had already shipped twice: crow-recorder-central-
v2 v1.4 and v1.5 sealed with J2, the board's only USB-C, rendered 90 DEGREES
ROTATED, because `jlc_twin` mounted the body at a pad fit it had ITSELF
rejected in the same breath (`PAD-MISMATCH best=(4.5947, False, 90)`).

Two constraints decide whether this suite is worth anything:

  (A) CANON M1 — the measured side must come from PIXELS. A gate that
      recomputed the body position from the mesh and the mount transform
      would AGREE WITH A WRONG MOUNT, which is the defect itself.
  (B) The reference is the EXPECTED POSITION, never the courtyard. J1's
      barrel-jack mesh really is 5.686 mm off its courtyard centre; gating
      that would fail J1 forever and produce a waiver, and an inherited
      waiver is how the refdes-on-silk defect crossed three boards (canon M4).

RED-VERIFIED against the pre-fix code. Every known-bad below was run against
`git show HEAD~:skills/jlcpcb-fab/scripts/twin_overlay.py` (the 232-line
drawing tool) and the outcome recorded in the test's own docstring. The
headline: on the SEALED v1.5 render the pre-fix tool exits **0** with
"OVERLAY OK: 203 courtyards, 16 flagged, 15 crops"; the gate exits **1** with
"OVERLAY FAIL: 1 unfaithful ref(s): J2 (centre 1.44mm, outward 1.49mm)".

FIXTURES. The board, the BOM, the CPL and the renders are read from the SEALED
v1.5 release, read-only, never written. JLC's own CAD for the six LCSC codes
the tests need is vendored under `fixtures/twin_overlay/` — see its
PROVENANCE.md, including the one deliberate byte-level edit.
"""
import math
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

OVL = FAB_SCRIPTS / "twin_overlay.py"
FIX = Path(__file__).resolve().parent / "fixtures" / "twin_overlay"
REL = (ROOT / "projects/crow-recorder-central-v2/07_releases"
              "/crow-recorder-central-v2-v1.5-2026-07-25")
BOARD = REL / "source/crow_recorder_central_v2.kicad_pcb"
BOM = REL / "fab/bom.csv"
ASSY = REL / "verification/assembly.yaml"
TOP = REL / "verification/twin_top.png"
BOTTOM = REL / "verification/twin_bottom.png"
ISO = REL / "verification/twin_iso_nw.png"
TWIN_REPORT = REL / "verification/twin_report.csv"

# The board's own edge, from its Edge.Cuts. Written here rather than read so
# the fixture generator and the checker do not share a source.
EDGE = (9.95, 9.95, 180.05, 130.05)


def gate(*extra, out=None, png=TOP, board=BOARD, side="top", bom=BOM,
         bare=None, adjudications=None):
    d = out or tmpdir("ovl_")
    args = [KPY, OVL, board, png, "--side", side,
            "--twin-dir", FIX, "--out", d / "ov", "--report", d / "r.md"]
    if bom:
        args += ["--bom", bom, "--assembly", ASSY]
    if bare:
        args += ["--bare", bare]
    if adjudications:
        args += ["--adjudications", adjudications]
    return run(args + [str(a) for a in extra]), d


def synth_render(path, px_box=(100, 150, 700, 573), size=(800, 600),
                 bodies=(), edge=EDGE, body_color=(90, 90, 90),
                 mirror=False):
    """A minimal stand-in for a kicad-cli render: a SATURATED green rectangle
    for the board (which is all the calibrator needs) plus DESATURATED grey
    rectangles for bodies, in mm, projected with the caller's own arithmetic.

    Deliberately not produced by importing twin_overlay's projector — the
    fixture must be able to disagree with the checker, or it proves nothing.
    """
    from PIL import Image
    W, H = size
    x0, y0, x1, y1 = px_box
    im = Image.new("RGB", (W, H), (18, 18, 18))
    p = im.load()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p[x, y] = (76, 110, 55)          # sat 0.50, hue ~85 -> "board"
    sx = (x1 - x0 + 1) / (edge[2] - edge[0])
    sy = (y1 - y0 + 1) / (edge[3] - edge[1])
    for (bx0, by0, bx1, by1) in bodies:
        if mirror:
            bx0, bx1 = edge[2] - bx1 + edge[0], edge[2] - bx0 + edge[0]
        for y in range(int(y0 + (by0 - edge[1]) * sy),
                       int(y0 + (by1 - edge[1]) * sy) + 1):
            for x in range(int(x0 + (bx0 - edge[0]) * sx),
                           int(x0 + (bx1 - edge[0]) * sx) + 1):
                if 0 <= x < W and 0 <= y < H:
                    p[x, y] = body_color
    im.save(path)
    return sx, sy


def graded_row(report, ref):
    """The `## Graded refs` row for `ref`, split into cells. Deliberately
    anchored on that heading: the FAIL table above it has a DIFFERENT column
    layout, and reading the wrong one silently shifts every assertion by a
    column."""
    body = report.split("## Graded refs", 1)
    check(len(body) == 2, "the report has no `## Graded refs` section")
    rows = [l for l in body[1].splitlines() if l.startswith(f"| `{ref}` |")]
    check(rows, f"{ref} has no row in the graded table")
    return [c.strip() for c in rows[0].split("|")]


def red_box_px(path):
    """bbox of the pure-red courtyard strokes in an overlay image."""
    from PIL import Image
    im = Image.open(path).convert("RGB")
    p = im.load()
    xs, ys = [], []
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if p[x, y] == (255, 0, 0):
                xs.append(x)
                ys.append(y)
    check(xs, f"no red courtyard stroke drawn in {path}")
    return min(xs), min(ys), max(xs), max(ys)


def flip_j1(dest):
    """The sealed board with J1 alone flipped to B.Cu — a good input broken
    in exactly one way, and the only bottom-side footprint anywhere in this
    fleet (all nine boards measure 0 bottom-side footprints, 2026-07-26)."""
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "fp=b.FindFootprintByReference('J1')\n"
            "fp.Flip(fp.GetPosition(), False)\n"
            "b.Save(sys.argv[2])\n")
    must_pass(run([KPY, "-c", code, BOARD, dest]), "flip_j1")
    return dest


@test("same-camera native-model extraction unions disconnected STEP body islands")
def t_native_multipart_body_union():
    """A connector STEP commonly renders as disconnected shell/housing
    islands.  Native registration owns a one-model coupon, so its measured
    envelope must include every populated-minus-bare island; the general twin
    path must retain nearest-component behavior for crowded boards."""
    probe = (
        "import json,sys\n"
        "from PIL import Image\n"
        f"sys.path.insert(0,{str(FAB_SCRIPTS)!r})\n"
        "from twin_overlay import extract_body\n"
        "bare=Image.new('RGB',(80,40),(70,110,60))\n"
        "pop=bare.copy()\n"
        "p=pop.load()\n"
        "for box in ((10,10,25,25),(45,10,60,25)):\n"
        " x0,y0,x1,y1=box\n"
        " for y in range(y0,y1+1):\n"
        "  for x in range(x0,x1+1): p[x,y]=(220,220,220)\n"
        "kw=dict(size=pop.size,win=(0,0,79,39),seed_px=(18,18),"
        "bare_px=bare.load(),ero=0)\n"
        "nearest=extract_body(pop.load(),**kw)\n"
        "union=extract_body(pop.load(),union_components=True,**kw)\n"
        "print('@@'+json.dumps([nearest[0],union[0]]))\n")
    result = must_pass(run([KPY, "-c", probe]),
                       "multipart native-model extraction probe")
    contains(result.out, "@@[[10, 10, 25, 25], [10, 10, 60, 25]]",
             "native coupons union every disconnected same-camera body island")


@test("A-RENDER independently uses an explicit unique-pad anchor for a "
      "failed duplicate-ground fit", kind="known_bad")
def t_explicit_mount_anchor_geometry():
    """The renderer and the pixel gate must not share mount arithmetic, but
    they must consume the same evidence contract.  This pins A-RENDER's own
    interpretation of the Pluto SMA 1->1 signal-hole datum and its report
    label.  The duplicated JLC pad 2 is deliberately present but is never a
    valid anchor."""
    d = tmpdir("ovl_anchor_")
    adj = d / "adj.yaml"
    adj.write_text(
        "- lcsc: C429844\n"
        "  status: MODEL-REG\n"
        "  mount_anchor: {our_pad: '1', jlc_pad: '1', angle: 0}\n")
    probe = (
        "import json,sys\n"
        f"sys.path.insert(0,{str(FAB_SCRIPTS)!r})\n"
        "from twin_overlay import (read_model_adjudications, "
        "explicit_anchor_geometry, fit_description)\n"
        "a=read_model_adjudications(sys.argv[1])['C429844']['mount_anchor']\n"
        "ours={'1':[(30.0,25.0)], '2':[(27.46,22.46)], "
        "'3':[(32.54,22.46)], '4':[(27.46,27.54)], "
        "'5':[(32.54,27.54)]}\n"
        "jlc={'1':[(0.0,0.0)], '2':[(-2.54,-2.54),(2.54,-2.54),"
        "(-2.54,2.54),(2.54,2.54)]}\n"
        "oc,jc,ang=explicit_anchor_geometry(a,ours,jlc,(30.0,25.0))\n"
        "label=fit_description({'anchored':True,'anchor':a,'ang':ang,"
        "'fit_err':1.796})\n"
        "print('@@'+json.dumps([oc,jc,ang,label]))\n")
    r = must_pass(run([KPY, "-c", probe, adj]),
                  "A-RENDER unique-pad anchor probe")
    contains(r.out, '[[0.0, 0.0], [0.0, 0.0], 0,',
             "pad-1 origins produce a zero mount translation")
    contains(r.out, "ANCHOR 1->1 @0deg (failed fit 1.80mm)",
             "the report distinguishes an anchor from generic fallback")


@test("a selected render representation carries an explicit symmetric plan "
      "envelope without weakening centre registration")
def t_render_representation_envelope_contract():
    d = tmpdir("ovl_model_representation_")
    adj = d / "adj.yaml"
    adj.write_text(
        "- lcsc: C86462\n"
        "  status: MODEL-REG\n"
        "  render_model_extension: step\n"
        "  plan_bbox_expand_mm: 1.52\n")
    probe = (
        "import json,sys\n"
        f"sys.path.insert(0,{str(FAB_SCRIPTS)!r})\n"
        "from twin_overlay import read_model_adjudications\n"
        "a=read_model_adjudications(sys.argv[1])['C86462']\n"
        "mesh=(-6.0,-12.0,6.0,4.0); e=a['plan_bbox_expand_mm']\n"
        "expanded=(mesh[0]-e,mesh[1]-e,mesh[2]+e,mesh[3]+e)\n"
        "print('@@'+json.dumps([a['render_model_extension'],expanded]))\n")
    r = must_pass(run([KPY, "-c", probe, adj]),
                  "render representation envelope contract")
    contains(r.out, '@@[".step", [-7.52, -13.52, 7.52, 5.52]]',
             "selected extension and symmetric envelope are explicit")

    bad = d / "bad.yaml"
    bad.write_text(
        "- lcsc: C86462\n"
        "  render_model_extension: step\n"
        "  plan_bbox_expand_mm: -1\n")
    rb = run([KPY, "-c", probe, bad])
    must_fail(rb, "negative envelope expansion", "non-negative")


# ===================================================================== clean

@test("A-RENDER passes the CORRECTED twin render and prints its coverage")
def t_corrected_render_passes():
    """The other half of the headline. The same sealed board and the same
    fixture CAD, against a render made after jlc_twin stopped mounting on a
    rejected fit: J2 moves from 1.435/1.491 mm to 0.543/0.025 mm and the gate
    passes. Rendering here would need kicad-cli, so the corrected geometry is
    reproduced the honest way instead — a synthetic render with the body drawn
    at the EXPECTED box, computed by this test from JLC's own transform."""
    d = tmpdir("ovl_ok_")
    png = d / "twin_top.png"
    # J1's expected body and J2's expected body, both at JLC's own transform.
    # Derived in the docstring of twin_overlay.py from the vendored meshes;
    # written here as literals so the fixture cannot inherit a checker bug.
    synth_render(png, bodies=[(16.000, 96.050, 30.400, 105.350),
                              (83.755, 119.408, 92.695, 126.963)])
    r, _ = gate(png=png, out=d)
    must_pass(r, "A-RENDER on a faithful render")
    contains(r.out, "COVERAGE:", "coverage line")
    contains(r.out, "OVERLAY OK", "verdict")


@test("A-RENDER prints N measured / M total on every run, pass or fail")
def t_coverage_always_printed():
    """`bom_source_check`'s row_kind silently dropped 12 of 26 rows while
    printing PASS. A partial sweep that does not print its denominator is the
    same defect wearing a different name."""
    r, _ = gate()
    must_fail(r, "A-RENDER on the sealed render", "COVERAGE:")
    # These are the fixture-cache figures (6 vendored LCSC codes). Against
    # the full 47-code cache the same run reads `22 measured / 177 with an
    # expected body; 155 unresolvable, 0 resolvable-but-unmeasured, 8
    # no-model` — the same J2 verdict, the same J1 numbers. The point of the
    # assertion is that a denominator is ALWAYS printed, never that it is big.
    contains(r.out, "2 measured / 23 with an expected body",
             "the measured coverage figure")
    contains(r.out, "21 unresolvable", "the named unresolvable count")
    contains(r.out, "0 resolvable-but-unmeasured", "the honest-failure count")
    contains(r.out, "162 no-model", "the no-JLC-model count")


@test("A-RENDER names what it could NOT measure, and why, one ref at a time")
def t_unmeasurable_named():
    r, d = gate()
    rep = (d / "r.md").read_text()
    contains(rep, "Not measurable by construction", "the section")
    contains(rep, "`R_cc1` — body 1.00x0.50 mm is under the 2.0 mm "
                  "resolvability floor", "a named 0402 with its measured size")
    contains(rep, "`C_vb` — body 2.00x1.30 mm is under the 2.0 mm "
                  "resolvability floor", "a named 0805 with its measured size")
    contains(rep, "`J3` — C9900035627: no JLC footprint cached",
             "an RJ45 named as having no model at all")
    contains(rep, "No JLC model at all (162)", "the third bucket, counted")
    # 2 graded + 21 unresolvable + 162 no-model = 185 coded refs: every ref is
    # in exactly one bucket and none is silently dropped.
    eq(2 + 21 + 162, 185, "the three buckets must partition the coded refs")


@test("A-RENDER passes J1 while REPORTING its 5.686 mm courtyard excursion")
def t_j1_model_defect_is_reported_not_gated():
    """Constraint (B). JLC's barrel-jack mesh sits 4.26 mm off its own origin,
    so the body really is 5.686 mm from the courtyard centre — and the RENDER
    of it is faithful to 0.046 mm. Gating body-vs-courtyard would fail J1 on
    every run forever and buy a waiver; canon M4 says an inherited waiver is
    how the refdes-on-silk defect crossed three boards. The number is reported
    so a reviewer can classify it as a MODEL defect with no board exposure."""
    r, d = gate()
    rep = (d / "r.md").read_text()
    cells = graded_row(rep, "J1")
    eq(cells[4], "0.046", "J1 centre delta mm")
    eq(cells[5], "0.000", "J1 outward excursion mm")
    eq(cells[8], "5.686", "J1 courtyard excursion mm (reported, not gated)")
    not_contains(r.out, "unfaithful ref(s): J1", "J1 must not be gated")


@test("A-RENDER's same-camera bare channel measures saturated coloured "
      "bodies the legacy grey-pixel channel cannot see")
def t_same_camera_bare_delta_measures_coloured_bodies():
    """Regression for programmable-usb2-hub's false-failure set: tan 1210
    capacitors were reduced to one silver end cap and the green terminal block
    to one screw because saturation<0.12 was treated as the body definition.
    The populated-minus-bare observation must see body COLOUR, not assume it."""
    d = tmpdir("ovl_bare_")
    bare = d / "twin_bare_top.png"
    pop = d / "twin_top.png"
    synth_render(bare)
    synth_render(pop, bodies=[(16.000, 96.050, 30.400, 105.350),
                              (83.755, 119.408, 92.695, 126.963)],
                 body_color=(165, 112, 22))  # saturation 0.87: legacy rejects
    r, out = gate(png=pop, bare=bare, out=d)
    must_pass(r, "A-RENDER populated-minus-bare on coloured bodies")
    contains((out / "r.md").read_text(),
             "populated-minus-same-camera-bare RGB delta",
             "the report must name the independent measurement channel")


@test("A-RENDER does not union unchanged legacy pixels into a clean "
      "same-camera delta body")
def t_same_camera_delta_is_not_contaminated_by_legacy_board_pixels():
    """Regression for the four C5334230 USB Type-B bodies on
    pi-usb-port-switch.  Their populated-minus-bare components matched the
    expected mesh to <=0.08 mm, but the old unconditional delta+legacy union
    walked onto unchanged low-saturation board/pad pixels and reported a false
    1.53 mm excursion.  The controlled delta observation must remain primary.
    RED on the old code: the static grey bridge below joins J1's legacy blob
    and pushes it more than the 1.00 mm tolerance outside its true body."""
    from PIL import Image, ImageDraw

    d = tmpdir("ovl_delta_primary_")
    bare = d / "twin_bare_top.png"
    pop = d / "twin_top.png"
    sx, sy = synth_render(bare)
    synth_render(pop, bodies=[(16.000, 96.050, 30.400, 105.350),
                              (83.755, 119.408, 92.695, 126.963)])

    # An unchanged desaturated board marking touches J1's rendered body and
    # extends 3 mm west.  It is visible to the legacy colour heuristic but is
    # exactly absent from populated-minus-bare RGB delta.
    def px(mm_x, mm_y):
        return (100 + int(round((mm_x - EDGE[0]) * sx)),
                150 + int(round((mm_y - EDGE[1]) * sy)))

    for path in (bare, pop):
        im = Image.open(path).convert("RGB")
        draw = ImageDraw.Draw(im)
        draw.rectangle([px(13.0, 99.0), px(16.1, 102.0)],
                       fill=(90, 90, 90))
        im.save(path)

    r, out = gate(png=pop, bare=bare, out=d)
    must_pass(r, "A-RENDER with a clean delta body beside static legacy pixels")
    cells = graded_row((out / "r.md").read_text(), "J1")
    check(float(cells[5]) < 0.50,
          f"unchanged legacy pixels contaminated J1 outward excursion: {cells}")


@test("A-RENDER canonicalizes EasyEDA pad labels 01..09 to KiCad 1..9",
      kind="known_bad")
def t_leading_zero_pad_labels_are_same_identity():
    """J7's ten-pin header shared all ten physical identities, but without
    normalization the checker saw only pad 10 and formed an invalid one-point
    anchor. RED on the old code: canonical_pad_number did not exist."""
    sys.path.insert(0, str(FAB_SCRIPTS))
    from twin_overlay import canonical_pad_number
    eq([canonical_pad_number(x) for x in ("01", "08", "10", "A1")],
       ["1", "8", "10", "A1"], "pad identity normalization")


@test("A-RENDER's rotation operator matches pcbnew, and the fixture can tell "
      "the two handednesses apart (canon M-DISC)")
def t_rot_matches_pcbnew():
    """`formB(a) == formA(-a)` IDENTICALLY, and both equal the identity's own
    reflection at 0 and 180 — so a 0/180-only fixture passes the handedness
    bug silently, forever. Five copies of exactly that bug survived weeks of
    review in jlc_twin.py. This samples 90 and 270 AND asserts the sample set
    separates the two candidate forms."""
    sys.path.insert(0, str(FAB_SCRIPTS))
    from twin_overlay import rot_ydown

    def wrong(x, y, deg):
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        return (x * c - y * s, x * s + y * c)

    # pcbnew itself is the authority: place a pad at a known footprint-local
    # offset, rotate the footprint, and ask where the pad ended up.
    code = ("import pcbnew,sys,json\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "fp=b.FindFootprintByReference('U1')\n"
            "o={}\n"
            "p0=fp.GetPosition()\n"
            "for a in (0,90,180,270):\n"
            "  fp.SetOrientationDegrees(0)\n"
            "  loc=[(pd.GetPosition().x-p0.x, pd.GetPosition().y-p0.y)\n"
            "       for pd in fp.Pads()][:24]\n"
            "  fp.SetOrientationDegrees(a)\n"
            "  got=[(pd.GetPosition().x-p0.x, pd.GetPosition().y-p0.y)\n"
            "       for pd in fp.Pads()][:24]\n"
            "  o[a]=[loc,got]\n"
            "print('@@'+json.dumps(o))\n")
    r = must_pass(run([KPY, "-c", code, BOARD]), "pcbnew pad rotation")
    import json
    data = json.loads(r.out.split("@@", 1)[1].strip())
    worst_ours = worst_wrong = 0.0
    n90 = 0
    for ang, (loc, got) in data.items():
        for (lx, ly), (gx, gy) in zip(loc, got):
            ox, oy = rot_ydown(lx / 1e6, ly / 1e6, float(ang))
            wx, wy = wrong(lx / 1e6, ly / 1e6, float(ang))
            worst_ours = max(worst_ours, math.hypot(ox - gx / 1e6, oy - gy / 1e6))
            worst_wrong = max(worst_wrong, math.hypot(wx - gx / 1e6, wy - gy / 1e6))
        if ang in ("90", "270"):
            n90 += len(loc)
    check(n90 >= 24, f"M-DISC: the fixture must sample 90/270; got {n90} pads")
    check(worst_ours < 1e-6,
          f"rot_ydown disagrees with pcbnew by {worst_ours:.6f} mm")
    check(worst_wrong > 1.0,
          f"M-DISC: this fixture CANNOT tell the two handednesses apart "
          f"(the wrong form is only {worst_wrong:.6f} mm off) — it would "
          f"pass the bug")


@test("A-RENDER draws a BOTTOM-side courtyard X-MIRRORED")
def t_bottom_courtyard_is_mirrored():
    """MEASURED. J1 flipped to B.Cu has a B.CrtYd bbox at x 21.955..38.045 mm;
    on the fixture render (601 px over 170.1 mm, origin px 100) the mirrored
    projection is px x 601.7..658.6 and the un-mirrored one is 142.4..199.3 —
    459 px apart, so this assertion cannot be satisfied by accident."""
    d = tmpdir("ovl_bot_")
    b = flip_j1(d / "board.kicad_pcb")
    png = d / "twin_bottom.png"
    synth_render(png)
    r = run([KPY, OVL, b, png, "--side", "bottom",
             "--out", d / "ov", "--report", d / "r.md"])
    must_pass(r, "A-RENDER on a bottom render with a bottom part")
    box = red_box_px(d / "ov" / "twin_bottom_courtyard_overlay.png")
    sx = 601 / (EDGE[2] - EDGE[0])
    want_l = 100 + (EDGE[2] - 38.045) * sx
    want_r = 100 + (EDGE[2] - 21.955) * sx
    check(abs(box[0] - want_l) <= 2 and abs(box[2] - want_r) <= 2,
          f"bottom courtyard drawn at px x {box[0]}..{box[2]}, mirrored "
          f"expectation {want_l:.1f}..{want_r:.1f}")
    # and it must not have graded anything it cannot grade
    contains(r.out, "NOTHING GRADED", "a run that grades nothing must say so")


@test("A-RENDER grades a BOTTOM-side body in the unflipped library frame")
def t_bottom_body_is_expected_and_measured():
    """Flip the asymmetric J1 footprint to B.Cu and draw its body at the
    independently derived bottom-side envelope.  KiCad represents this flip
    as B.Cu plus orientation 180: local Y is side-mirrored, then the 180-degree
    placement rotation makes the realised board envelope an X reflection of
    the top envelope about J1's (24,102) anchor.  Thus
    16.000..30.400 x 96.050..105.350 becomes
    17.600..32.000 x 96.050..105.350; the bottom camera then mirrors board X
    once more.  The fixture fails if either reflection is omitted or doubled."""
    d = tmpdir("ovl_botbody_")
    b = flip_j1(d / "board.kicad_pcb")
    png = d / "twin_bottom.png"
    synth_render(png, bodies=[(17.600, 96.050, 32.000, 105.350)], mirror=True)
    r = run([KPY, OVL, b, png, "--side", "bottom",
             "--twin-dir", FIX, "--bom", BOM, "--assembly", ASSY,
             "--out", d / "ov", "--report", d / "r.md"])
    must_pass(r, "A-RENDER on a faithful bottom-side body")
    contains(r.out, "1 measured / 1 with an expected body",
             "the bottom body participates in the gate denominator")
    contains(r.out, "OVERLAY OK", "the faithful bottom body verdict")


# ================================================================ known-bad

@test("A-RENDER FAILS the SEALED v1.5 render, naming J2 (the defect that "
      "shipped twice)", kind="known_bad")
def t_sealed_v15_fails_on_j2():
    """THE HEADLINE. crow-recorder-central-v2 v1.4 and v1.5 both sealed with
    the board's only USB-C rendered 90 degrees out: 7.555 x 8.940 mm where the
    part is 8.940 x 7.555. `jlc_twin` printed `PAD-MISMATCH
    best=(4.594738839150707, False, 90)` and mounted the body at that same
    rejected 90 anyway, then told the reviewer to "VERIFY leads sit on pads
    visually" against the picture its own failure had corrupted.

    RED-VERIFIED: the pre-fix twin_overlay.py (232 lines, HEAD~) exits 0 here
    printing `OVERLAY OK: 203 courtyards, 16 flagged, 15 crops`. It computes
    no body position anywhere, so no amount of J2 being wrong could move it."""
    r, d = gate()
    must_fail(r, "A-RENDER on the sealed v1.5 render", "OVERLAY FAIL")
    contains(r.out, "unfaithful ref(s): J2", "the named ref")
    rep = (d / "r.md").read_text()
    cells = graded_row(rep, "J2")
    eq(cells[4], "1.435", "J2 centre delta mm")
    eq(cells[5], "1.491", "J2 outward excursion mm")
    contains(rep, "NONE (best 4.59mm) -> JLC's own transform",
             "the report must say the expectation came from JLC's transform, "
             "not from the fit that failed")


@test("A-RENDER FAILS a body displaced 3 mm from where the board puts it",
      kind="known_bad")
def t_displaced_body_fails():
    """The generic form of the J2 defect: the geometry says one place, the
    pixels say another. Built by moving J1 3 mm east on a scratch copy of the
    board while leaving the SEALED render alone — so expected moves and
    measured cannot follow.

    RED-VERIFIED 2026-07-26: the pre-fix tool exits 0 printing `OVERLAY OK:
    203 courtyards, 0 flagged, 0 crops` — it draws the courtyard 3 mm east and
    has no opinion about where the body is."""
    d = tmpdir("ovl_disp_")
    b = d / "board.kicad_pcb"
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "fp=b.FindFootprintByReference('J1')\n"
            "p=fp.GetPosition(); p.x += 3000000; fp.SetPosition(p)\n"
            "b.Save(sys.argv[2])\n")
    must_pass(run([KPY, "-c", code, BOARD, b]), "displace J1")
    r, _ = gate(board=b, out=d)
    must_fail(r, "A-RENDER on a 3 mm displaced body", "unfaithful ref(s): J1")


@test("A-RENDER FAILS a ref it SHOULD have been able to measure and could not",
      kind="known_bad")
def t_resolvable_but_unmeasured_fails():
    """Item 4 of the coverage contract. A body that is big enough and isolated
    enough to resolve, but produces no pixels, is a FAILURE — never a quiet
    omission from the covered set. Built by painting J1's body area back to
    board green in a copy of the render.

    RED-VERIFIED 2026-07-26: the pre-fix tool exits 0 printing `OVERLAY OK:
    203 courtyards, 0 flagged, 0 crops` on the erased render — it never looks
    for a body, so erasing one changes nothing it reports."""
    from PIL import Image
    d = tmpdir("ovl_gone_")
    im = Image.open(TOP).convert("RGB")
    p = im.load()
    # J1's body occupies board mm 16.0..30.4 x 96.05..105.35; project with the
    # test's own arithmetic, then paint it board-green.
    minx, miny, sx, sy = 301, 150, 5.6790, 5.6869
    for y in range(int(miny + (95.0 - EDGE[1]) * sy),
                   int(miny + (106.5 - EDGE[1]) * sy)):
        for x in range(int(minx + (15.0 - EDGE[0]) * sx),
                       int(minx + (31.5 - EDGE[0]) * sx)):
            p[x, y] = (76, 110, 55)
    png = d / "twin_top.png"
    im.save(png)
    r, _ = gate(png=png, out=d)
    must_fail(r, "A-RENDER on a render with J1's body erased",
              "resolvable-but-unmeasured")
    contains(r.out, "J1", "the named ref")


@test("A-RENDER REFUSES a perspective render instead of drawing on it",
      kind="known_bad")
def t_perspective_refused():
    """twin_iso_nw.png is rendered with --perspective, so the mm->px map is
    not affine: measured anisotropy 0.9458 (x 5.9142, y 6.2531 px/mm) against
    a 0.02 tolerance. A misleading overlay is believed exactly as readily as a
    correct one. RED-VERIFIED: the pre-fix tool ALSO refused this one — it is
    the one behaviour that survived, and it is kept pinned."""
    r, _ = gate(png=ISO)
    eq(r.rc, 2, "exit code for a refusal")
    contains(r.out, "OVERLAY REFUSED: anisotropy", "the refusal")


@test("A-RENDER REFUSES a bare render made at a different resolution",
      kind="known_bad")
def t_bare_size_mismatch_refused():
    """A pixel delta is meaningful only when both observations share a camera
    and pixel grid. Silently resizing would manufacture edges and could either
    hide or invent a displacement."""
    from PIL import Image
    d = tmpdir("ovl_baresize_")
    bare = d / "twin_bare_top.png"
    Image.new("RGB", (32, 32), (0, 0, 0)).save(bare)
    r, _ = gate(bare=bare, out=d)
    eq(r.rc, 2, "exit code for a refusal")
    contains(r.out, "--bare image size", "the named mismatch")


@test("A-RENDER REFUSES --side top on a file named twin_bottom.png",
      kind="known_bad")
def t_bottom_render_graded_as_top_refused():
    """The exact invocation that exited 0 on v1.5: the tool printed
    "anisotropy 0.9976 ... orthographic, projection valid" and drew all 203
    F.CrtYd boxes UN-MIRRORED on an x-mirrored render. J1's east pad column at
    board x=24.0 appears at image x=166.12 mm (2x95 - 166.12 = 23.88), so
    every box was off by 2x(95-x) — 10.0 mm for J2 — and it was declared
    valid. RED-VERIFIED: the pre-fix tool exits 0 with `OVERLAY OK: 203
    courtyards`."""
    r, _ = gate(png=BOTTOM, side="top")
    eq(r.rc, 2, "exit code for a refusal")
    contains(r.out, "the render is named twin_bottom.png", "the refusal")


@test("A-RENDER REFUSES --side bottom when nothing has a B.CrtYd courtyard",
      kind="known_bad")
def t_bottom_side_with_no_bottom_parts_refused():
    """All 203 of this board's footprints are on the top. Drawing the OTHER
    side's courtyards onto a bottom render is what the pre-fix tool did; the
    only honest answer is to refuse. RED-VERIFIED: the pre-fix tool exits 0
    with `203 courtyards, 16 flagged`."""
    r, _ = gate(png=BOTTOM, side="bottom")
    eq(r.rc, 2, "exit code for a refusal")
    contains(r.out, "no footprint has a courtyard on the B.CrtYd layer",
             "the refusal")


@test("A-RENDER reaches every ref of a MULTI-REF twin finding row",
      kind="known_bad")
def t_multiref_finding_row_reaches_all_eight():
    """THE ROW_KIND DEFECT. `read_twin_findings` keyed on the RAW `Ref`
    string, so the sealed report's row

        C9900035627,"J10,J3,J4,J5,J6,J7,J8,J9",FETCH-FAILED,...

    — the eight RJ45 connectors, the ONLY parts on this board with no JLC CAD
    at all — matched no `fp.GetReference()`. All eight drew a thin RED box as
    if clean, with no crop. The single most important row in the file was the
    one the tool could not see.

    RED-VERIFIED 2026-07-26: the pre-fix report heads its table `## 16 ref(s)
    flagged by jlc_twin` and carries the literal composite row

        | `J10,J3,J4,J5,J6,J7,J8,J9` | **FETCH-FAILED** | ...

    with NONE of the eight appearing as a key of its own. 16 keys -> 23 refs
    is the whole fix, and `--crop-flagged` produced 15 crops there against 23
    highlighted refs here."""
    r, d = gate("--twin-report", TWIN_REPORT)
    must_fail(r, "A-RENDER on the sealed render", "OVERLAY FAIL")
    rep = (d / "r.md").read_text()
    for ref in ("J3", "J4", "J5", "J6", "J7", "J8", "J9", "J10"):
        contains(rep, f"| `{ref}` | **FETCH-FAILED** |",
                 f"{ref} must appear as a flagged ref in its own right")
    not_contains(rep, "`J10,J3,J4", "the raw composite key must not survive")
    contains(rep, "23 ref(s) flagged by jlc_twin",
             "the flagged count: 16 keys became 23 refs once split")


@test("A-RENDER FAILS a twin finding that names no footprint on the board",
      kind="known_bad")
def t_orphan_finding_fails():
    """A finding about a part that is not there is a bug in one of the two
    files, never a pass — and it is indistinguishable, to a keyed lookup, from
    the multi-ref row above. RED-VERIFIED: the pre-fix tool exits 0; an
    unmatched key simply meant the ref was drawn thin-red as clean.

    RED-VERIFIED 2026-07-26: the pre-fix tool exits 0 and reports `1 flagged` —
    it counted a ref that is not on the board as a flagged ref."""
    d = tmpdir("ovl_orph_")
    tr = d / "twin_report.csv"
    tr.write_text('LCSC,Ref,Status,Detail\n'
                  'C1,J9001,PAD-MISMATCH,invented\n')
    r, _ = gate("--twin-report", tr, out=d)
    must_fail(r, "A-RENDER with an orphan finding",
              "twin finding(s) naming no footprint")
    contains(r.out, "J9001(PAD-MISMATCH)", "the named orphan")


@test("A-RENDER FAILS a footprint with no courtyard on either layer",
      kind="known_bad")
def t_no_courtyard_fails():
    """A courtyard-less footprint is invisible to the whole projection, so it
    can never be graded and must never be counted as covered. RED-VERIFIED:
    the pre-fix tool exits 0 printing `OVERLAY OK: 202 courtyards, 0 flagged`
    — one fewer than the board has, in a line nothing reads."""
    d = tmpdir("ovl_nocy_")
    b = d / "board.kicad_pcb"
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "fp=b.FindFootprintByReference('U1')\n"
            "for g in list(fp.GraphicalItems()):\n"
            "  if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):\n"
            "    fp.Remove(g)\n"
            "b.Save(sys.argv[2])\n")
    must_pass(run([KPY, "-c", code, BOARD, b]), "strip U1's courtyard")
    r, _ = gate(board=b, out=d)
    must_fail(r, "A-RENDER with a courtyard-less footprint",
              "footprint(s) with no courtyard")
    contains(r.out, "U1", "the named ref")


@test("A-RENDER FAILS when --bom resolves no expected body at all",
      kind="known_bad")
def t_nothing_expected_fails():
    """A gate that grades nothing must never print PASS — the shape of the
    jlc_twin exit-0 incident. Point --twin-dir at an EMPTY cache and every
    expectation disappears; the run must say so and fail, not report a clean
    203-courtyard drawing.

    RED-VERIFIED 2026-07-26, with the honest caveat: the pre-fix tool has no
    `--twin-dir`, so this exact scenario cannot be posed to it at all. What
    was measured instead is that it exits 0 on the same board and render with
    every expectation absent — because it never forms one."""
    d = tmpdir("ovl_none_")
    (d / "empty" / "easyeda").mkdir(parents=True)
    r = run([KPY, OVL, BOARD, TOP, "--side", "top",
             "--twin-dir", d / "empty", "--bom", BOM,
             "--out", d / "ov", "--report", d / "r.md"])
    must_fail(r, "A-RENDER with an empty cache", "NOTHING EXPECTED")


@test("A-RENDER FAILS a BOTTOM courtyard drawn UN-mirrored", kind="known_bad")
def t_bottom_mirror_has_teeth():
    """The discrimination assertion for the mirror (canon M-DISC applied to a
    reflection rather than a rotation): if `--side bottom` did NOT mirror, the
    box would land at px x 142.4..199.3 instead of 601.7..658.6. This asserts
    the un-mirrored placement is REJECTED, so a future regression to the
    pre-fix behaviour cannot pass silently.

    RED-VERIFIED 2026-07-26: the pre-fix tool has no `--side` at all. Run on
    this exact fixture it exits 0 with `OVERLAY OK: 203 courtyards` and draws
    J1's B.CrtYd box starting at px x=142 — the UN-MIRRORED position (142.4),
    459 px from where the part actually is."""
    d = tmpdir("ovl_botneg_")
    b = flip_j1(d / "board.kicad_pcb")
    png = d / "twin_bottom.png"
    synth_render(png)
    r = run([KPY, OVL, b, png, "--side", "bottom",
             "--out", d / "ov", "--report", d / "r.md"])
    must_pass(r, "bottom overlay")
    box = red_box_px(d / "ov" / "twin_bottom_courtyard_overlay.png")
    sx = 601 / (EDGE[2] - EDGE[0])
    unmirrored_l = 100 + (21.955 - EDGE[0]) * sx
    check(abs(box[0] - unmirrored_l) > 50,
          f"the bottom courtyard was drawn UN-MIRRORED at px x {box[0]} "
          f"(un-mirrored expectation {unmirrored_l:.1f}) — the mirror is gone")


# ------------------------------------------------- G-VACUOUS (declared blind spot)

@test("G-VACUOUS A-RENDER: the verdict rests on 2 of 203 parts — a body under "
      "the resolvability floor is EXCLUDED, not graded",
      kind="vacuity", gate="twin_overlay.py")
def t_vacuity_a_body_under_the_resolvability_floor_is_excluded_not_graded():
    """THE DECLARED BLIND SPOT (canon G-VACUOUS; the executable half of the
    `VACUITY:` block in twin_overlay.py's docstring).

    This fixture asserts the gate PASSES while the fact it grades — "every
    placed part is where the board says it is" — is FALSE. It is not a
    known_bad; it PINS a defect so it cannot be forgotten, and closing the
    defect is expected to break it (then it becomes a known_bad).

    THE MECHANISM. `fails` is built over `graded` only, and two exclusions run
    first, neither able to fail: `unresolvable` (expected body under
    `MIN_BODY_MM = 2.0` in either dimension) and `no_model`. So a 0402 at
    1.0 x 0.5 mm is outside the verdict BY CONSTRUCTION.

    MEASURED on the sealed v1.5 release this suite fixtures against:

        COVERAGE: 2 measured / 23 with an expected body; 21 unresolvable,
        0 resolvable-but-unmeasured, 162 no-model, 203 courtyards drawn

    Two assertions, and the second is the load-bearing one:

      1. the gate passes a faithful render while reporting that denominator —
         so 201 of 203 parts are ungraded and the exit code does not say so;
      2. a part on the unresolvable list is ungraded EVEN WHEN THE BOARD MOVES
         IT. J1's body is 14.4 x 9.3 mm so it IS graded; the fixture instead
         picks a ref the gate itself listed as unresolvable and displaces it
         3 mm, which is 3x the 1.00 mm tolerance. `t_displaced_body_fails` does
         exactly this to J1 and the gate FAILS. Here it exits 0.

    That contrast is the whole content of the declaration: the same 3 mm
    displacement is caught on a 14 mm part and invisible on a 2 mm one."""
    d = tmpdir("ovl_vac_")
    png = d / "twin_top.png"
    synth_render(png, bodies=[(16.000, 96.050, 30.400, 105.350),
                              (83.755, 119.408, 92.695, 126.963)])
    r, _ = gate(png=png, out=d)
    must_pass(r, "A-RENDER on a faithful render")
    m = re.search(r"COVERAGE: (\d+) measured / (\d+) with an expected body; "
                  r"(\d+) unresolvable, (\d+) resolvable-but-unmeasured, "
                  r"(\d+) no-model, (\d+) courtyards", r.out)
    check(m is not None, f"the coverage line changed shape:\n{r.out[-800:]}")
    meas, exp, unres, unmeas, nomodel, drawn = (int(g) for g in m.groups())
    # The blind spot, stated as arithmetic rather than as prose.
    check(meas < drawn / 10,
          f"A-RENDER graded {meas} of {drawn} courtyards — if this ratio has "
          f"risen the blind spot is CLOSING and this vacuity fixture should "
          f"become a known_bad with a coverage floor")
    check(unres > 0 and unmeas == 0,
          f"the excluded-by-construction set must be non-empty and the "
          f"fail-able set empty for this to be a blind spot: "
          f"{unres} unresolvable, {unmeas} resolvable-but-unmeasured")

    # (2) displace an UNRESOLVABLE ref by 3 mm — 3x the 1.00 mm tolerance —
    #     and the verdict does not move.
    rep = (d / "r.md").read_text()
    sec = rep.split("## Not measurable by construction", 1)
    check(len(sec) == 2, "no unresolvable section in the report")
    tiny = re.findall(r"^[-*|]\s*`([A-Za-z_]+\w*)`", sec[1], re.M)
    check(tiny, f"no unresolvable ref named in the report:\n{sec[1][:600]}")
    ref = tiny[0]
    b = d / "moved.kicad_pcb"
    code = ("import pcbnew,sys\n"
            "b=pcbnew.LoadBoard(sys.argv[1])\n"
            "fp=b.FindFootprintByReference(sys.argv[3])\n"
            "p=fp.GetPosition(); p.x += 3000000; fp.SetPosition(p)\n"
            "b.Save(sys.argv[2])\n")
    must_pass(run([KPY, "-c", code, BOARD, b, ref]), f"displace {ref}")
    r2, _ = gate(png=png, board=b, out=tmpdir("ovl_vac2_"))
    must_pass(r2, f"A-RENDER with the sub-2mm part {ref} displaced 3 mm — THE "
                  f"BLIND SPOT. If this now FAILS, A-RENDER has learned to see "
                  f"small parts: convert this fixture to kind=\"known_bad\"")
    not_contains(r2.out, f"unfaithful ref(s): {ref}",
                 f"{ref} is excluded from the verdict, not graded")


if __name__ == "__main__":
    sys.exit(main())
