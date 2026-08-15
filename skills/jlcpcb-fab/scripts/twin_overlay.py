#!/usr/bin/env python3
"""twin_overlay.py — GRADE the twin render: is the PICTURE faithful to the
BOARD? Draws the courtyards too, but the drawing is the by-product.

    twin_overlay.py BOARD.kicad_pcb TWIN.png --side top|bottom
                    [--twin-dir DIR] [--bom fab/bom.csv]
                    [--assembly 03_src/rules/assembly.yaml]
                    [--out DIR] [--twin-report twin_report.csv]
                    [--bare SAME_CAMERA_BARE.png]
                    [--crop-flagged] [--report MD] [--tol MM] [--draw-only]

WHAT THIS FILE USED TO BE, AND WHY THAT WAS WORSE THAN NOTHING (2026-07-26).
It carried a checker's docstring and computed NO BODY POSITION ANYWHERE. It
projected courtyards out of the board and drew boxes; its only non-zero exits
concerned the IMAGE (no green region, anisotropy over tol). It was wired into
no pipeline stage, had no contract Audit row, and had no known-bad fixture —
so nothing could observe that it graded nothing. Run against `twin_bottom.png`
it exited 0 printing "orthographic, projection valid" while drawing all 203
F.CrtYd boxes UN-MIRRORED onto an x-mirrored render (J2's boxes landed 10.0 mm
from its part). That is the `bom_source_check.row_kind` class: a sweep that
silently covers a fraction of its input while printing PASS.

THE PROPERTY THIS GATES, and the two constraints that decide it:

    expected = mesh bbox x JLC's OWN footprint model transform x our board
               placement                                          (GEOMETRY)
    measured = connected-component bbox of the populated-minus-bare
               image delta, or the legacy body-colour classifier when no
               same-camera bare render is supplied                       (PIXELS)
    FAIL if the two disagree by more than --tol

(A) CANON M1 — the checker and the checked must not share a method. The
    artifact under test is the RENDER. If the `measured` side were computed
    analytically from the mesh plus the mount transform, it would share a
    method with `jlc_twin`'s mount and would AGREE WITH A WRONG MOUNT — which
    is precisely the defect that shipped (J2 below). So `measured` comes from
    PIXELS: preferably the changed-pixel component between TWO renders made
    with the same camera and board (models present vs every model removed),
    seeded at the expected centre. This sees green terminal blocks, tan
    capacitors, black moulding and disconnected metal alike; the old
    saturation classifier saw only grey/metal and therefore measured one
    capacitor end cap or one terminal screw as the complete body. Nothing on
    the measured side reads twin.kicad_pcb, twin_report.csv, or any jlc_twin
    geometry output. The bare image is an observation of the renderer, not an
    analytic body expectation.

(B) THE REFERENCE IS THE EXPECTED POSITION, NOT THE COURTYARD. Gating
    body-vs-courtyard makes J1 fail on every run forever — JLC's barrel-jack
    mesh is genuinely 5.686 mm off the courtyard centre because the mesh is
    4.26 mm off its own origin — which produces a waiver, and an inherited
    waiver is how the refdes-on-silk defect propagated across three boards
    (canon M4). Body-vs-courtyard is REPORTED as a model-quality number and
    gates nothing. The classification a reviewer actually needs is:

        body outside courtyard + render faithful  -> MODEL defect, no board
                                                     exposure (J1)
        render disagrees with the geometry        -> the PICTURE is lying, and
                                                     every visual review done
                                                     on it is void (J2)

MEASURED ACCEPTANCE, crow-recorder-central-v2 v1.5 (203 footprints, edge
9.950..180.050 x 9.950..130.050 mm, twin_top.png at 5.6790 px/mm x /
5.6869 px/mm y, anisotropy 0.9986):

  - J1 barrel jack (C381116, anchor 24.0000,102.0000 rot 0): mesh bbox centre
    is model-local (-3.6500,+2.2000); expected body centre (23.200,100.700);
    courtyard centre (18.000,103.000) -> a 5.686 mm courtyard excursion that
    is REPORTED, not gated. Pixel-measured 16.113..30.200 x 96.113..105.256
    against expected 16.000..30.400 x 96.050..105.350: centre delta 0.043 mm,
    outward excursion 0.113 mm. J1 PASSES.
  - J2 USB-C (C3020560, anchor 90.0000,126.0000 rot 0): the pad fit FAILED
    (PAD-MISMATCH best=(4.5947, False, 90), PAD-GEOM pad 1<->2 ours 0.80 mm vs
    JLC 8.64 mm) and jlc_twin mounted the body at that failed fit's 90 deg
    anyway. Expected (JLC's own transform, the only defensible mount for an
    unfitted part) 83.755..92.695 x 119.408..126.963; pixel-measured
    85.491..93.239 x 117.917..126.709 -> centre delta 1.435 mm, outward
    excursion 1.491 mm. J2 FAILS. That is this gate's headline acceptance:
    run it on the SEALED v1.5 render and it fails on J2; run it after the
    jlc_twin mount fix and it passes.

WHY THE TOLERANCE IS 1.00 mm, from the measurement and not from taste. 22 of
this board's 177 refs with an expected body clear the resolvability
precondition. Their readings, with J2 taken out as the known defect (n=21):

    centre delta   median 0.160  max 0.248 (F6)
    outward        median 0.145  max 0.217 (Q1)

and the two ends of the J2 case:

    J2 as SEALED (mounted at the rejected fit)   1.435 / 1.491   <- must FAIL
    J2 after the jlc_twin mount fix              0.543 / 0.025   <- must PASS

So the empty band runs from 0.543 (the largest legitimate reading anywhere on
the board) to 1.435 (the defect), and 1.00 mm is within 0.01 mm of its
arithmetic midpoint. It is 4.0x the worst clean centre delta, 4.6x the worst
clean outward excursion, 0.70x the defect — and 5.68 px at this render scale,
comfortably over the 2 px an erosion/dilation round trip can cost an edge. A
tolerance of 0.50 mm would condemn the CORRECTED J2; 1.50 mm would acquit the
sealed one. The choice is made by the data, not by preference.

CALIBRATION IS MEASURED, NOT ASSUMED, and a render this tool cannot trust is
REFUSED rather than drawn on: a misleading overlay is believed exactly as
readily as a correct one (the I-HW geodesic encoded the wrong physics rather
than none and was believed because it produced a number). Refusals, all four
measured on this release: no green board region; anisotropy over tol
(twin_iso_nw 0.9458, twin_iso_se 0.9141, twin_edge_west 6.2564 — sampling
every pixel; the old every-second-pixel scan read 0.9499 and 51.9765, refusing
either way); `--side bottom` on a board whose B.CrtYd layer is empty while 203
footprints sit on F.CrtYd; and `--side top` on a file named `twin_bottom.png`,
which is the exact invocation that used to exit 0 while drawing all 203 boxes
un-mirrored. The mirror itself is pinned in pixels: flip J1 to B.Cu and its
B.CrtYd box must land at px x 601.7..658.6 of the synthetic fixture, 459 px
from where the un-mirrored projection would put it.

VACUITY: (canon G-VACUOUS — the input class on which this gate PASSES while the
fact it grades is FALSE, fixtured by `t1_twin_overlay.py`
`t_vacuity_a_body_under_the_resolvability_floor_is_excluded_not_graded`.)

A-RENDER's verdict is `fails = {r: g for r, g in graded.items() if ...}` — over
the GRADED SUBSET only. Two exclusions run BEFORE that dict is built and NEITHER
can fail: `unresolvable` (an expected body under `MIN_BODY_MM = 2.0` in either
dimension, reported as "Not measurable by construction") and `no_model` (no JLC
footprint cached). `unmeasured` — big enough to resolve and no pixels found — is
correctly a hard FAIL; the other two are quiet.

MEASURED on the sealed crow-recorder-central-v2 v1.5 release this suite fixtures
against: `COVERAGE: 2 measured / 23 with an expected body; 21 unresolvable, 0
resolvable-but-unmeasured, 162 no-model, 203 courtyards drawn`. **The verdict
rests on 2 of 203 parts.** So A-RENDER can exit 0 with any 0402 or 0603 on the
board rotated 180 degrees, mis-swapped, or absent — 1.0 x 0.5 mm is under the
2.0 mm floor by construction, and those are exactly the parts that get rotated.
The denominator is printed on every run, which is why this is discoverable at
all; what is missing is any gate that reads it.

A SECOND, SMALLER MOUTH, in the other direction and NOT this gate's vacuity:
`MIN_BODY_PX = 20` and `EROSION = 2` are PIXEL floors sitting beside a
millimetre tolerance (`--tol`, default 1.00 mm), while jlc_twin hard-codes
`--width 1600 --height 1000` — 8.34 px/mm on the 188.1 mm cooksense board.
Measured there: the two A-RENDER FAILs at that scale (`U_LDO` centre delta
1.248 mm, `Q_SWDRVRHA` 13 body px against the floor of 20) BOTH VANISH at
15.3961 px/mm — 0.111 mm and 872 px, exit 0. The render was faithful and the
SEGMENTATION was resolution-limited (cross-checked by an independent PIL column
scan, canon M1). That makes the low-resolution verdict a FALSE FAIL, not a false
pass, so it is a defect to fix and not a vacuity condition; it is recorded here
because the two were reported as one thing and are not.
"""
import argparse
import csv
import glob
import hashlib
import math
import re
import sys
from collections import deque
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("twin_overlay: needs Pillow (PIL)")

RED = (255, 0, 0)
BLUE = (0, 160, 255)
AMBER = (255, 170, 0)
GREEN = (0, 255, 0)
MAGENTA = (255, 0, 255)

# --- resolvability preconditions, measured on crow-recorder-central-v2 v1.5.
# A body smaller than this does not survive the erosion round trip at twin
# render scale (1600x1000 over a 170 mm board = 5.68 px/mm): a 0402 chip is
# 5.7 x 2.8 px, and EROSION=2 removes it entirely. Parts below the bar are
# reported UNRESOLVABLE with the reason; they are never silently passed.
MIN_BODY_MM = 2.0
# Two bodies closer than this merge into one connected component, so the
# measurement would be of the pair, not the part.
CLEAR_MM = 0.5
# Board solder mask + copper measure sat 0.32 with p10 == p90 == 0.32 (a very
# tight distribution); moulded/metal bodies measure sat 0.00. 0.12 sits in the
# empty middle.
SAT_THRESHOLD = 0.12
DIFF_THRESHOLD = 12    # max per-channel RGB delta; same-camera renders are exact
EROSION = 2          # px; removes the 1-3 px silver tendrils of adjacent pads
MIN_BODY_PX = 20     # a component smaller than this cannot define a bbox

PAD_RE = re.compile(r"\(pad\s+(\S+)\s+\S+\s+\S+\s+\(at\s+(-?[\d.]+)\s+(-?[\d.]+)")
MODEL_RE = re.compile(
    r'\(model\s+"?([^"\n]+?)"?\s*\n?\s*\(offset\s*\(xyz\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)\)'
    r'\s*\n?\s*\(scale\s*\(xyz\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)\)'
    r'\s*\n?\s*\(rotate\s*\(xyz\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\)\)', re.S)


# --------------------------------------------------------------------------
# geometry: the EXPECTED side. Deliberately reads JLC's cached .kicad_mod and
# .wrl as TEXT rather than through the same loaders jlc_twin uses, and never
# reads twin.kicad_pcb or twin_report.csv (canon M1).
# --------------------------------------------------------------------------

def rot_ydown(x, y, deg):
    """Rotate by `deg` in KiCad's own sense (CCW in the y-down screen frame).

    This is the SAME operator KiCad applies to a rotated footprint's pads, and
    the same one applied (with a positive angle in the y-UP model frame) to a
    3D model's rot_z. It is written here rather than imported so a sign error
    in one file cannot silently reproduce itself in the other; it is pinned
    against pcbnew's own pad placement by
    `tests/t1_twin_overlay.t_rot_matches_pcbnew`, which is REQUIRED to sample
    90/270 (canon M-DISC: formB(a) == formA(-a) at 0 and 180, so a 0/180-only
    fixture passes the handedness bug).
    """
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (x * c + y * s, -x * s + y * c)


def canonical_pad_number(value):
    """Normalize formatting-only decimal zeros, preserve alphanumeric pins."""
    value = str(value).strip().strip('"')
    return str(int(value)) if value.isdigit() else value


def parse_jlc_footprint(path):
    """(pads {number: [(x,y)...]}, model {file, off, scale, rotz}) from JLC's
    cached .kicad_mod TEXT."""
    txt = Path(path).read_text(errors="ignore")
    pads = {}
    for n, x, y in PAD_RE.findall(txt):
        pads.setdefault(canonical_pad_number(n), []).append((float(x), float(y)))
    m = MODEL_RE.search(txt)
    model = None
    if m:
        model = dict(file=m.group(1),
                     off=(float(m.group(2)), float(m.group(3))),
                     scale=(float(m.group(5)), float(m.group(6))),
                     rotz=float(m.group(10)))
    return pads, model


def wrl_plan_bbox(path):
    """Plan-view (x,y) bbox of a KiCad WRL mesh, mm, in the MODEL frame (y-up).
    KiCad VRML convention: 1 VRML unit = 2.54 mm."""
    try:
        txt = Path(path).read_text(errors="ignore")
    except OSError:
        return None
    xs, ys = [], []
    for m in re.finditer(r"point\s*\[([^\]]*)\]", txt):
        nums = re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", m.group(1))
        for i in range(0, len(nums) - 2, 3):
            xs.append(float(nums[i]) * 2.54)
            ys.append(float(nums[i + 1]) * 2.54)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def pad_fit(ours_centred, jlc_centred):
    """[(maxerr, ang)] best-first over the four right angles, non-mirrored.

    NOT a copy of jlc_twin's fit for its own sake: this gate must know whether
    a fit EXISTS, because that decides which transform the mount is entitled
    to use. A pad number named a different number of times on the two sides is
    a NAMING convention, so those numbers are compared by centroid.
    """
    common = set(ours_centred) & set(jlc_centred)
    if not common:
        return []
    out = []
    for ang in (0, 90, 180, 270):
        errs = []
        for k in common:
            a = sorted(ours_centred[k])
            b = sorted(rot_ydown(x, y, ang) for x, y in jlc_centred[k])
            if len(a) != len(b):
                ca = (sum(p[0] for p in a) / len(a), sum(p[1] for p in a) / len(a))
                cb = (sum(p[0] for p in b) / len(b), sum(p[1] for p in b) / len(b))
                errs.append(math.hypot(ca[0] - cb[0], ca[1] - cb[1]))
                continue
            for (x1, y1), (x2, y2) in zip(a, b):
                errs.append(math.hypot(x1 - x2, y1 - y2))
        out.append((max(errs), ang))
    return sorted(out)


def expected_bbox(mesh, model, jc, oc, ang, fp_rot, fp_pos):
    """Board-frame mm bbox of the mesh, mounted the way the render is entitled
    to mount it. Three frame hops, each named:

      1. model frame (y-up)  -> JLC footprint frame (y-down), via JLC's OWN
         rot_z / scale / offset — the transform JLC ships with the part;
      2. JLC frame -> our footprint-local frame, by `ang` (0 when no pad fit
         exists), with JLC's common-pad centroid mapped onto ours;
      3. our local frame -> board, by the footprint's own orientation.
    """
    corners = []
    for mx in (mesh[0], mesh[2]):
        for my in (mesh[1], mesh[3]):
            rx, ry = rot_ydown(mx, my, model["rotz"])
            jx = rx * model["scale"][0] + model["off"][0]
            jy = -(ry * model["scale"][1] + model["off"][1])      # -> y-down
            lx, ly = rot_ydown(jx - jc[0], jy - jc[1], ang)
            bx, by = rot_ydown(lx + oc[0], ly + oc[1], fp_rot)
            corners.append((bx + fp_pos[0], by + fp_pos[1]))
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------
# pixels: the MEASURED side
# --------------------------------------------------------------------------

def saturation(p):
    r, g, b = p[:3]
    mx = max(r, g, b)
    return 0.0 if mx == 0 else (mx - min(r, g, b)) / mx


def board_extent_px(im, step=1):
    """(minx, miny, maxx, maxy) of the green board region."""
    W, H = im.size
    px = im.load()
    minx, miny, maxx, maxy = W, H, 0, 0
    for y in range(0, H, step):
        for x in range(0, W, step):
            r, g, b = px[x, y][:3]
            if g > r + 8 and g > b + 8 and g > 25:
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
    if maxx <= minx or maxy <= miny:
        return None
    return minx, miny, maxx, maxy


def extract_body(px, size, win, seed_px, blocked=(), protect=None,
                 ero=EROSION, thr=SAT_THRESHOLD, bare_px=None,
                 diff_thr=DIFF_THRESHOLD):
    """Connected component of body pixels inside `win`, nearest `seed_px`.

    `blocked` is a list of pixel rectangles where a DIFFERENT part's body is
    expected to be; those pixels are forced to background. Without it a 0402
    resistor 0.305 mm off J2's expected shell merges into the same component
    and inflates the measured bbox by 1.3 mm — a FALSE FAIL on the one ref
    this gate exists to grade. The caller never blocks anything inside THIS
    ref's own expected box, so a body that has drifted onto its neighbour is
    still seen (truncated, and therefore still failing) rather than hidden.

    Returns (bbox_px, npx, touched_border) or None. `bbox_px` is dilated back
    by `ero` so it is comparable with an un-eroded expectation.
    """
    W, H = size
    x0, y0, x1, y1 = win
    x0 = max(0, x0); y0 = max(0, y0); x1 = min(W - 1, x1); y1 = min(H - 1, y1)
    if x1 <= x0 or y1 <= y0:
        return None
    mask = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if bare_px is None:
                v = saturation(px[x, y]) < thr
            else:
                here = px[x, y][:3]
                bare = bare_px[x, y][:3]
                v = max(abs(here[i] - bare[i]) for i in range(3)) > diff_thr
            if v and not (protect and protect[0] <= x <= protect[2]
                          and protect[1] <= y <= protect[3]):
                for bx0, by0, bx1, by1 in blocked:
                    if bx0 <= x <= bx1 and by0 <= y <= by1:
                        v = False
                        break
            mask[(x, y)] = v
    for _ in range(ero):
        nxt = {}
        for (x, y), v in mask.items():
            nxt[(x, y)] = v and all(mask.get((x + dx, y + dy), False)
                                    for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        mask = nxt
    sx, sy = seed_px
    best = None
    for (x, y), v in mask.items():
        if v:
            d = (x - sx) ** 2 + (y - sy) ** 2
            if best is None or d < best[0]:
                best = (d, (x, y))
    if best is None:
        return None
    seen = {best[1]}
    q = deque([best[1]])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (x + dx, y + dy)
            if mask.get(p) and p not in seen:
                seen.add(p)
                q.append(p)
    xs = [p[0] for p in seen]
    ys = [p[1] for p in seen]
    touched = (min(xs) <= x0 + ero or max(xs) >= x1 - ero
               or min(ys) <= y0 + ero or max(ys) >= y1 - ero)
    return ((min(xs) - ero, min(ys) - ero, max(xs) + ero, max(ys) + ero),
            len(seen), touched)


# --------------------------------------------------------------------------
# board + inputs
# --------------------------------------------------------------------------

def load_board(path):
    import pcbnew
    return pcbnew.LoadBoard(str(path))


def collect(board, side):
    """[(ref, courtyard bbox mm | None, on_this_side, pos, rot, pads)] + edge."""
    import pcbnew
    bb = board.GetBoardEdgesBoundingBox()
    edge = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
            bb.GetRight() / 1e6, bb.GetBottom() / 1e6)
    layer = pcbnew.F_CrtYd if side == "top" else pcbnew.B_CrtYd
    out = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        cc = fp.GetCourtyard(layer)
        cy = None
        if cc.OutlineCount():
            b = cc.BBox()
            cy = (b.GetLeft() / 1e6, b.GetTop() / 1e6,
                  b.GetRight() / 1e6, b.GetBottom() / 1e6)
        other = fp.GetCourtyard(pcbnew.B_CrtYd if side == "top"
                                else pcbnew.F_CrtYd)
        rot = fp.GetOrientationDegrees()
        pos = (fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6)
        # Pad METAL, as placed. The measured blob may legitimately include it:
        # a HASL/ENIG pad is as desaturated as a moulded body, so a 2-terminal
        # part's exposed pads are part of the same connected component (D1's
        # SMA pads add 0.93 mm on the left and 0.70 mm on the right of the
        # mesh bbox — a 0.935 mm reading against a 1.00 mm tolerance, for a
        # render that is entirely correct).
        pxs, pys = [], []
        for p in fp.Pads():
            pb = p.GetBoundingBox()
            pxs += [pb.GetLeft() / 1e6, pb.GetRight() / 1e6]
            pys += [pb.GetTop() / 1e6, pb.GetBottom() / 1e6]
        padbb = (min(pxs), min(pys), max(pxs), max(pys)) if pxs else None
        fp.SetOrientationDegrees(0)
        pads = {}
        for p in fp.Pads():
            n = canonical_pad_number(p.GetNumber())
            if n:
                pads.setdefault(n, []).append((p.GetPosition().x / 1e6,
                                               p.GetPosition().y / 1e6))
        fp.SetOrientationDegrees(rot)
        out.append(dict(ref=ref, cy=cy, has_other=bool(other.OutlineCount()),
                        pos=pos, rot=rot, pads=pads, padbb=padbb,
                        bottom=fp.GetLayer() != pcbnew.F_Cu,
                        models=len(list(fp.Models())) > 0))
    return out, edge


def read_twin_findings(path, board_refs):
    """ref -> [(status, detail)], plus the set of keys naming no footprint.

    THE MULTI-REF BUG (fixed 2026-07-26). This used to key on the RAW `Ref`
    string, so the row `J10,J3,J4,J5,J6,J7,J8,J9` — the eight RJ45 connectors,
    the only parts on crow-recorder-central-v2 with no JLC CAD at all, all
    FETCH-FAILED — matched no `fp.GetReference()` and every one of them drew a
    thin RED box as if clean, with no crop. The single most important row in
    the file was the one it could not see. Same defect class as
    `bom_source_check`'s `row_kind`.

    A finding key that matches NO footprint is now returned as an ORPHAN and
    is a hard failure: a finding about a part that is not on the board is a
    bug in one of the two files, never a pass.
    """
    interesting = {"MODEL-REG", "MODEL-SELF", "PAD-GEOM", "PAD-MISMATCH",
                   "MIRRORED", "POLARITY-CHECK", "POLARITY-FIT",
                   "POLARITY-FIT-BLIND", "PAD-MULTIPLICITY", "NO-BODY",
                   "FETCH-FAILED", "MOUNT-FALLBACK", "NOT-ON-BOARD"}
    found, orphans = {}, set()
    if not path or not Path(path).is_file():
        return found, orphans
    for row in csv.DictReader(open(path, encoding="utf-8-sig")):
        st = (row.get("Status") or "").strip()
        if st not in interesting:
            continue
        detail = (row.get("Detail") or "").strip()
        for ref in (row.get("Ref") or "").split(","):
            ref = ref.strip()
            if not ref:
                continue
            if ref not in board_refs:
                orphans.add((ref, st))
                continue
            found.setdefault(ref, []).append((st, detail))
    return found, orphans


def read_ref_lcsc(bom, assembly):
    """ref -> LCSC from the BOM (and the declared assembly home for the coded
    not-assembled / consigned parts, canon A-POP). Never from twin_report.csv:
    that is jlc_twin's OUTPUT, and this gate grades jlc_twin's render."""
    out = {}
    if bom and Path(bom).is_file():
        for r in csv.DictReader(open(bom, encoding="utf-8-sig")):
            code = (r.get("LCSC") or "").strip()
            if not code:
                continue
            for d in (r.get("Designator") or "").split(","):
                if d.strip():
                    out[d.strip()] = code
    if assembly and Path(assembly).is_file():
        try:
            import yaml
            doc = yaml.safe_load(open(assembly)) or {}
        except Exception:
            doc = {}
        for key in ("not_assembled", "consigned"):
            for e in (doc.get(key) or []):
                code = str(e.get("lcsc") or "").strip()
                for r in (e.get("refs") or []):
                    if code:
                        out.setdefault(str(r).strip(), code)
    return out


def index_cache(cachedir):
    """LCSC -> path of the cached JLC .kicad_mod."""
    out = {}
    p = Path(cachedir)
    if not p.is_dir():
        return out
    for d in sorted(p.iterdir()):
        mods = glob.glob(str(d / "jlc.pretty" / "*.kicad_mod"))
        if mods:
            out[d.name] = mods[0]
    return out


def resolve_mesh(model, cache_mod):
    """The .wrl the footprint names, or the same basename beside it (the
    cached path is absolute and written at fetch time, so it breaks the moment
    the tree moves)."""
    f = Path(model["file"])
    if f.is_file():
        return str(f)
    alt = Path(cache_mod).parent.parent / "jlc.3dshapes" / f.name
    return str(alt) if alt.is_file() else None


def gap_mm(a, b):
    """Separation between two mm bboxes; 0 when they overlap."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def read_model_adjudications(path):
    """Per-LCSC display-model transforms from the evidence register.

    These are part of the EXPECTED mount contract, not measurements copied
    from the rendered artifact. `jlc_twin` consumes the same source but the
    frame conversion is intentionally reimplemented here (canon M1).
    """
    if not path:
        return {}
    try:
        import yaml
        rows = yaml.safe_load(Path(path).read_text()) or []
    except Exception as exc:
        raise ValueError(f"cannot read --adjudications {path}: {exc}") from exc
    out = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("lcsc"):
            continue
        dst = out.setdefault(str(row["lcsc"]), {})
        for key in ("model_dx", "model_dy", "board_dx", "board_dy",
                    "model_rot_z", "pad_alias", "mount_anchor"):
            if row.get(key) is not None:
                dst[key] = (dict(row[key]) if key in ("pad_alias",
                                                       "mount_anchor")
                            else float(row[key]))
    for code, row in out.items():
        anchor = row.get("mount_anchor")
        if anchor is None:
            continue
        if anchor.get("our_pad") is None or anchor.get("jlc_pad") is None:
            raise ValueError(f"mount_anchor for {code} requires our_pad and "
                             "jlc_pad")
        try:
            angle = int(anchor.get("angle", 0)) % 360
        except (TypeError, ValueError) as exc:
            raise ValueError(f"mount_anchor for {code} angle must be a "
                             "right-angle integer") from exc
        if angle not in (0, 90, 180, 270):
            raise ValueError(f"mount_anchor for {code} angle {angle} is not "
                             "one of 0, 90, 180, 270")
        row["mount_anchor"] = {"our_pad": str(anchor["our_pad"]),
                               "jlc_pad": str(anchor["jlc_pad"]),
                               "angle": angle}
    return out


def explicit_anchor_geometry(anchor, our_pads, jlc_pads, footprint_pos):
    """Return (our-local datum, JLC-local datum, angle) for a unique-pad
    mount anchor.  Both sides must name exactly one centre: accepting a
    duplicated pad here would recreate the centroid ambiguity this feature
    exists to eliminate."""
    op = our_pads.get(anchor["our_pad"], [])
    jp = jlc_pads.get(anchor["jlc_pad"], [])
    if len(op) != 1 or len(jp) != 1:
        raise ValueError(f"anchor {anchor['our_pad']}->{anchor['jlc_pad']} "
                         f"requires one pad centre on each side; found "
                         f"ours={len(op)}, JLC={len(jp)}")
    oc = (op[0][0] - footprint_pos[0], op[0][1] - footprint_pos[1])
    return oc, jp[0], anchor["angle"]


def fit_description(row):
    if row.get("anchored"):
        a = row["anchor"]
        return (f"ANCHOR {a['our_pad']}->{a['jlc_pad']} @{row['ang']}deg "
                f"(failed fit {row['fit_err']:.2f}mm)")
    if row["fitted"]:
        return f"{row['ang']}deg @{row['fit_err']:.2f}mm"
    return f"NONE (best {row['fit_err']:.2f}mm) -> JLC's own transform"


def board_to_local(bdx, bdy, rot_deg):
    """Inverse of KiCad's footprint-local -> board y-down rotation."""
    th = math.radians(rot_deg)
    return (bdx * math.cos(th) - bdy * math.sin(th),
            bdx * math.sin(th) + bdy * math.cos(th))


def apply_pad_alias(pads, alias):
    """Rename JLC pad identities exactly as the source adjudication states."""
    out = {str(k): list(v) for k, v in pads.items()}
    for src, dst in (alias or {}).items():
        src, dst = str(src), str(dst)
        if src in out and src != dst:
            out.setdefault(dst, []).extend(out.pop(src))
            out[dst] = sorted(out[dst])
    return out


# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("twin_png")
    ap.add_argument("--side", choices=("top", "bottom"), default="top",
                    help="which side this render shows. A BOTTOM render is "
                         "X-MIRRORED; without this the projection is off by "
                         "2x(board_centre_x - x) at every ref (10.0 mm for J2 "
                         "on crow-recorder-central-v2) and the tool declared "
                         "it valid")
    ap.add_argument("--out", default=None, help="directory for overlay + crops")
    ap.add_argument("--twin-report", default=None, help="twin_report.csv")
    ap.add_argument("--twin-dir", default=None,
                    help="jlc_twin outdir holding easyeda/<LCSC>/ (default: "
                         "the render's own directory)")
    ap.add_argument("--bom", default=None, help="fab/bom.csv — ref -> LCSC")
    ap.add_argument("--assembly", default=None,
                    help="03_src/rules/assembly.yaml — the coded "
                         "not-assembled/consigned refs (canon A-POP)")
    ap.add_argument("--adjudications", default=None,
                    help="evidence-backed twin_adjudications.yaml; display-"
                         "model nudges/rotations become part of the expected "
                         "mount geometry")
    ap.add_argument("--bare", default=None,
                    help="same-camera/same-resolution render of the identical "
                         "board with every 3D model removed. When supplied, "
                         "body pixels are measured from populated-minus-bare "
                         "RGB differences instead of body colour")
    ap.add_argument("--crop-flagged", action="store_true")
    ap.add_argument("--report", default=None, help="write a markdown report here")
    ap.add_argument("--aniso-tol", type=float, default=0.02)
    ap.add_argument("--tol", type=float, default=1.00,
                    help="mm; max centre delta AND max outward excursion of "
                         "the measured body vs the expected one")
    ap.add_argument("--draw-only", action="store_true",
                    help="draw and report, never fail on faithfulness. For "
                         "exploring a render, NOT for a verify stage")
    a = ap.parse_args(argv)

    png = Path(a.twin_png)
    stem = png.stem.lower()
    for word, side in (("bottom", "bottom"), ("top", "top")):
        if word in stem and a.side != side:
            print(f"OVERLAY REFUSED: --side {a.side} but the render is named "
                  f"{png.name}. A bottom render is X-MIRRORED; grading it as a "
                  f"top render silently projects every box to the wrong place "
                  f"(this exact combination exited 0 on v1.5).", file=sys.stderr)
            return 2

    im = Image.open(png).convert("RGB")
    bare_im = None
    if a.bare:
        bare_im = Image.open(a.bare).convert("RGB")
        if bare_im.size != im.size:
            print(f"OVERLAY REFUSED: --bare image size {bare_im.size} does not "
                  f"match populated render size {im.size}. The two renders "
                  "must use the same camera and resolution.", file=sys.stderr)
            return 2
    ext = board_extent_px(im)
    if ext is None:
        print("OVERLAY REFUSED: no green board region found — is this a twin "
              "render?", file=sys.stderr)
        return 2
    minx, miny, maxx, maxy = ext

    board = load_board(a.board)
    parts, edge = collect(board, a.side)
    ex0, ey0, ex1, ey1 = edge
    bw, bh = ex1 - ex0, ey1 - ey0

    sx = (maxx - minx + 1) / bw
    sy = (maxy - miny + 1) / bh
    aniso = sx / sy
    if abs(aniso - 1.0) > a.aniso_tol:
        print(f"OVERLAY REFUSED: anisotropy {aniso:.4f} exceeds tol "
              f"{a.aniso_tol} (x {sx:.4f} px/mm, y {sy:.4f} px/mm). The render "
              f"is not orthographic/straight-on, so courtyard projection would "
              f"be wrong. No image written.", file=sys.stderr)
        return 2

    mirror = (a.side == "bottom")

    def X(mm):
        return minx + ((ex1 - mm) if mirror else (mm - ex0)) * sx

    def Y(mm):
        return miny + (mm - ey0) * sy

    def MMX(p):
        return (ex1 - (p - minx) / sx) if mirror else (ex0 + (p - minx) / sx)

    def MMY(p):
        return ey0 + (p - miny) / sy

    on_side = [p for p in parts if p["cy"] is not None]
    if not on_side:
        other = sum(1 for p in parts if p["has_other"])
        print(f"OVERLAY REFUSED: no footprint has a courtyard on the "
              f"{'F' if a.side == 'top' else 'B'}.CrtYd layer, but {other} have "
              f"one on the other side. Either --side is wrong for this render "
              f"or this board has nothing on the named side; drawing the OTHER "
              f"side's courtyards onto it is what this refusal exists to stop.",
              file=sys.stderr)
        return 2

    board_refs = {p["ref"] for p in parts}
    findings, orphans = read_twin_findings(a.twin_report, board_refs)
    try:
        model_adjudications = read_model_adjudications(a.adjudications)
    except ValueError as exc:
        print(f"OVERLAY REFUSED: {exc}", file=sys.stderr)
        return 2
    no_courtyard = [p["ref"] for p in parts
                    if p["cy"] is None and not p["has_other"]]

    # ---------------- expected bodies (geometry) --------------------------
    twin_dir = Path(a.twin_dir) if a.twin_dir else png.parent
    cache = index_cache(twin_dir / "easyeda")
    ref_lcsc = read_ref_lcsc(a.bom, a.assembly)
    by_ref = {p["ref"]: p for p in parts}

    expected = {}            # ref -> dict(exp, ang, fit_err, fitted, code)
    no_model = {}            # ref -> why
    for ref, code in sorted(ref_lcsc.items()):
        p = by_ref.get(ref)
        if p is None:
            no_model[ref] = f"{code}: on the BOM, not on the board"
            continue
        if p["cy"] is None:
            continue                       # not on the side being rendered
        if p["bottom"]:
            # MEASURED 2026-07-26: jlc_twin cannot mount a body on a
            # bottom-side footprint at all. Flip crow-recorder-central-v2's
            # J1 to B.Cu and its own gate reports `MIRRORED mirror fit 0.00mm
            # vs non-mirror 6.00mm` and refuses the mount — the flip IS a
            # mirror, and the detector that exists to catch a mirror-NUMBERED
            # land pattern cannot tell the two apart. So a bottom render never
            # carries a JLC body today, and this gate has no calibrated
            # mirror for the model transform either. Refusing to compute an
            # expectation is the honest state; INVENTING one and passing it
            # would be the `jlc_twin` exit-0 class over again.
            no_model[ref] = (f"{code}: bottom-side footprint — jlc_twin reads "
                             f"the flip as MIRRORED and mounts no body, and "
                             f"this gate has no calibrated mirror for the "
                             f"model transform. NOT graded, and not counted "
                             f"as covered")
            continue
        mod = cache.get(code)
        if not mod:
            no_model[ref] = f"{code}: no JLC footprint cached (never fetched)"
            continue
        jpads, model = parse_jlc_footprint(mod)
        if not model:
            no_model[ref] = f"{code}: JLC footprint declares no 3D model"
            continue
        mesh_path = resolve_mesh(model, mod)
        mesh = wrl_plan_bbox(mesh_path) if mesh_path else None
        if not mesh:
            no_model[ref] = f"{code}: mesh {Path(model['file']).name} unreadable"
            continue
        adj = model_adjudications.get(code, {})
        jpads = apply_pad_alias(jpads, adj.get("pad_alias"))
        common = set(p["pads"]) & set(jpads)
        if not common:
            no_model[ref] = f"{code}: no common pad numbers — no anchor exists"
            continue
        no = sum(len(p["pads"][k]) for k in common)
        nj = sum(len(jpads[k]) for k in common)
        oc = (sum(x for k in common for x, _ in p["pads"][k]) / no - p["pos"][0],
              sum(y for k in common for _, y in p["pads"][k]) / no - p["pos"][1])
        jc = (sum(x for k in common for x, _ in jpads[k]) / nj,
              sum(y for k in common for _, y in jpads[k]) / nj)
        ours_c = {k: [(x - p["pos"][0] - oc[0], y - p["pos"][1] - oc[1])
                      for x, y in v] for k, v in p["pads"].items()}
        jlc_c = {k: [(x - jc[0], y - jc[1]) for x, y in v]
                 for k, v in jpads.items()}
        fits = pad_fit(ours_c, jlc_c)
        fitted = bool(fits and fits[0][0] <= 0.5)
        ang = fits[0][1] if fitted else 0
        anchored = False
        anchor = adj.get("mount_anchor")
        if not fitted and anchor:
            try:
                oc, jc, ang = explicit_anchor_geometry(
                    anchor, p["pads"], jpads, p["pos"])
            except ValueError as exc:
                print(f"OVERLAY REFUSED: invalid mount_anchor for {code} "
                      f"at {ref}: {exc}", file=sys.stderr)
                return 2
            anchored = True
        ldx = adj.get("model_dx", 0.0)
        ldy = adj.get("model_dy", 0.0)
        if adj.get("board_dx") is not None or adj.get("board_dy") is not None:
            cdx, cdy = board_to_local(adj.get("board_dx", 0.0),
                                      adj.get("board_dy", 0.0), p["rot"])
            ldx += cdx
            ldy += cdy
        oc = (oc[0] + ldx, oc[1] + ldy)
        model_expected = dict(model)
        model_expected["rotz"] = (model_expected["rotz"]
                                   + adj.get("model_rot_z", 0.0)) % 360
        exp = expected_bbox(mesh, model_expected, jc, oc, ang,
                            p["rot"], p["pos"])
        expected[ref] = dict(exp=exp, ang=ang, fitted=fitted,
                             anchored=anchored, anchor=anchor, code=code,
                             fit_err=fits[0][0] if fits else None,
                             adjudicated=bool(adj))

    # ---------------- resolvability, then measurement ---------------------
    # A ref whose body has no expected box (no JLC model) cannot be masked out
    # of a neighbour's window, so it is the one adjacency this gate cannot
    # neutralise; its courtyard stands in for it.
    unmaskable = [(p["ref"], p["cy"]) for p in on_side
                  if p["ref"] not in expected and p["cy"] is not None]
    graded, unresolvable, unmeasured = {}, {}, {}
    for ref, e in sorted(expected.items()):
        exp = e["exp"]
        w, h = exp[2] - exp[0], exp[3] - exp[1]
        if min(w, h) < MIN_BODY_MM:
            unresolvable[ref] = (f"body {w:.2f}x{h:.2f} mm is under the "
                                 f"{MIN_BODY_MM} mm resolvability floor "
                                 f"({min(w, h) * sx:.1f} px, and erosion "
                                 f"costs {2 * EROSION} px)")
            continue
        near = [(r2, gap_mm(exp, c2)) for r2, c2 in unmaskable
                if r2 != ref and gap_mm(exp, c2) < CLEAR_MM]
        if near:
            who = ", ".join(f"{r2} ({g:.2f} mm)" for r2, g in sorted(near)[:3])
            unresolvable[ref] = (f"a part with NO expected body — so nothing "
                                 f"this gate can mask out — sits within "
                                 f"{CLEAR_MM} mm: {who}; the two would merge "
                                 f"into one component")
            continue
        marg = 1.5
        xs = [X(exp[0] - marg), X(exp[2] + marg)]
        ys = [Y(exp[1] - marg), Y(exp[3] + marg)]
        win = (int(round(min(xs))), int(round(min(ys))),
               int(round(max(xs))), int(round(max(ys))))
        seed = (int(round(X((exp[0] + exp[2]) / 2))),
                int(round(Y((exp[1] + exp[3]) / 2))))
        blocked = []
        for r2, e2 in expected.items():
            if r2 == ref or gap_mm(exp, e2["exp"]) > 2.0:
                continue
            b = e2["exp"]
            bxs = sorted([X(b[0]), X(b[2])])
            blocked.append((int(round(bxs[0])), int(round(Y(b[1]))),
                            int(round(bxs[1])), int(round(Y(b[3])))))
        own_xs = sorted([X(exp[0]), X(exp[2])])
        own = (int(round(own_xs[0])), int(round(Y(exp[1]))),
               int(round(own_xs[1])), int(round(Y(exp[3]))))
        got = extract_body(im.load(), im.size, win, seed,
                           blocked=blocked, protect=own,
                           bare_px=bare_im.load() if bare_im else None)
        # The same-camera delta is the independent measurement and therefore
        # wins whenever it resolves a body.  The legacy low-saturation channel
        # is only a recovery path when the delta is absent or below the pixel
        # floor.  Unconditionally UNIONING the two used to let unchanged
        # low-saturation board features contaminate a clean delta component:
        # on pi-usb-port-switch, the four large through-hole USB shells had
        # faithful delta boxes (<=0.08 mm edge error), while the legacy flood
        # reached their exposed shell pads/board pixels and invented a 1.53 mm
        # outward excursion.  A secondary heuristic must not overrule the
        # controlled populated-minus-bare observation.
        if bare_im is not None:
            legacy = extract_body(im.load(), im.size, win, seed,
                                  blocked=blocked, protect=own)
            if (got is None or got[1] < MIN_BODY_PX) and legacy:
                got = legacy
        if got is None:
            unmeasured[ref] = ("no body pixels anywhere in the expected "
                               "window — the render shows bare board where a "
                               "body must be")
            continue
        bpx, npx, touched = got
        if npx < MIN_BODY_PX:
            unmeasured[ref] = (f"only {npx} body pixels found (floor "
                               f"{MIN_BODY_PX}) — not a body")
            continue
        mxs = sorted([MMX(bpx[0]), MMX(bpx[2])])
        mys = sorted([MMY(bpx[1]), MMY(bpx[3])])
        meas = (mxs[0], mys[0], mxs[1], mys[1])
        ctr = math.hypot((meas[0] + meas[2]) / 2 - (exp[0] + exp[2]) / 2,
                         (meas[1] + meas[3]) / 2 - (exp[1] + exp[3]) / 2)
        # Outward excursion, measured against the mesh bbox UNION this ref's
        # own pad metal. The render may show LESS than the mesh bbox (gull
        # leads and metal shells render as separate silver components, and a
        # dark body against a dark pad loses its own edge), and it may show
        # this ref's own PADS, but nothing this ref owns can appear outside
        # that union. Only outward violations are graded.
        pb = by_ref[ref]["padbb"]
        bound = exp if pb is None else (min(exp[0], pb[0]), min(exp[1], pb[1]),
                                        max(exp[2], pb[2]), max(exp[3], pb[3]))
        out = max(bound[0] - meas[0], bound[1] - meas[1],
                  meas[2] - bound[2], meas[3] - bound[3], 0.0)
        graded[ref] = dict(exp=exp, meas=meas, ctr=ctr, out=out, npx=npx,
                           touched=touched, **{k: e[k] for k in
                                               ("ang", "fitted", "anchored",
                                                "anchor", "code",
                                                "fit_err", "adjudicated")})

    fails = {r: g for r, g in graded.items()
             if g["ctr"] > a.tol or g["out"] > a.tol}

    # courtyard excursion — REPORTED, never gated (constraint B)
    excursion = {}
    for ref, e in expected.items():
        cy = by_ref[ref]["cy"]
        if cy is None:
            continue
        exp = e["exp"]
        excursion[ref] = math.hypot((exp[0] + exp[2]) / 2 - (cy[0] + cy[2]) / 2,
                                    (exp[1] + exp[3]) / 2 - (cy[1] + cy[3]) / 2)

    # ---------------- draw ------------------------------------------------
    outdir = Path(a.out) if a.out else png.parent
    outdir.mkdir(parents=True, exist_ok=True)
    d = ImageDraw.Draw(im)
    ebx = sorted([X(ex0), X(ex1)])       # mirrored X() reverses the order
    d.rectangle([ebx[0], Y(ey0), ebx[1], Y(ey1)], outline=BLUE, width=2)
    drawn = 0
    for p in on_side:
        cy = p["cy"]
        col = AMBER if p["ref"] in findings else RED
        w = 3 if p["ref"] in findings else 1
        x0, x1 = sorted([X(cy[0]), X(cy[2])])
        d.rectangle([x0, Y(cy[1]), x1, Y(cy[3])], outline=col, width=w)
        drawn += 1
    for ref, g in graded.items():
        for box, col in ((g["exp"], GREEN), (g["meas"], MAGENTA)):
            x0, x1 = sorted([X(box[0]), X(box[2])])
            d.rectangle([x0, Y(box[1]), x1, Y(box[3])],
                        outline=col, width=3 if ref in fails else 1)
    ov = outdir / (png.stem + "_courtyard_overlay.png")
    im.save(ov)

    crops = []
    if a.crop_flagged:
        want = sorted(set(findings) | set(fails))
        base = Image.open(png).convert("RGB")
        for ref in want:
            p = by_ref.get(ref)
            if not p or p["cy"] is None:
                continue
            cy = p["cy"]
            pad = 40
            cx0, cx1 = sorted([X(cy[0]), X(cy[2])])
            box = (max(0, int(cx0) - pad), max(0, int(Y(cy[1])) - pad),
                   min(im.size[0], int(cx1) + pad),
                   min(im.size[1], int(Y(cy[3])) + pad))
            c = base.crop(box)
            dd = ImageDraw.Draw(c)
            dd.rectangle([cx0 - box[0], Y(cy[1]) - box[1],
                          cx1 - box[0], Y(cy[3]) - box[1]], outline=RED, width=2)
            if ref in graded:
                for bx, col in ((graded[ref]["exp"], GREEN),
                                (graded[ref]["meas"], MAGENTA)):
                    bx0, bx1 = sorted([X(bx[0]), X(bx[2])])
                    dd.rectangle([bx0 - box[0], Y(bx[1]) - box[1],
                                  bx1 - box[0], Y(bx[3]) - box[1]],
                                 outline=col, width=2)
            c = c.resize((c.width * 5, c.height * 5), Image.LANCZOS)
            p2 = outdir / f"overlay_{ref}.png"
            c.save(p2)
            crops.append((ref, p2))

    # ---------------- report ----------------------------------------------
    n_expect = len(expected)
    report_fail = bool(fails or unmeasured or orphans or no_courtyard
                       or (n_expect and not graded)
                       or (a.bom and not n_expect))
    L = []
    L.append(f"# Twin render faithfulness — {png.name} (`--side {a.side}`)\n")
    L.append(f"board_sha256: {hashlib.sha256(Path(a.board).read_bytes()).hexdigest()}")
    L.append(f"a-render_verdict: {'FAIL' if report_fail else 'PASS'}")
    L.append(f"- calibration: **{sx:.4f} px/mm** x, **{sy:.4f} px/mm** y, "
             f"anisotropy **{aniso:.4f}** (tol {a.aniso_tol}) — orthographic, "
             f"projection valid" + ("; X-MIRRORED (bottom side)" if mirror else ""))
    L.append(f"- board edge: {ex0:.3f}..{ex1:.3f} x, {ey0:.3f}..{ey1:.3f} y mm")
    L.append(f"- courtyards drawn ({'F' if a.side == 'top' else 'B'}.CrtYd): "
             f"**{drawn}**; footprints with no courtyard on EITHER layer: "
             f"{len(no_courtyard)}")
    L.append(f"- **COVERAGE: {len(graded)} measured / {n_expect} refs with an "
             f"expected body** "
             f"({len(unresolvable)} unresolvable, {len(unmeasured)} resolvable "
             f"but NOT measured, {len(no_model)} with no JLC model at all)")
    L.append(f"- tolerance: **{a.tol:.2f} mm** on both the centre delta and the "
             f"outward excursion")
    L.append("- pixel measurement: **populated-minus-same-camera-bare RGB "
             f"delta** (threshold {DIFF_THRESHOLD})" if bare_im else
             "- pixel measurement: **legacy low-saturation component** "
             "(--bare not supplied)")
    if model_adjudications:
        L.append(f"- expected-model register: `{Path(a.adjudications).name}` "
                 f"({len(model_adjudications)} LCSC transform entr"
                 f"{'y' if len(model_adjudications) == 1 else 'ies'})")
    L.append(f"- overlay: `{ov.name}`\n")
    L.append("**Red** = footprint courtyard (what gets fabricated). "
             "**Amber** = a ref jlc_twin flagged. **Green** = EXPECTED body "
             "(mesh x JLC's own model transform x board placement). "
             "**Magenta** = MEASURED body (pixels). **Blue** = board edge.\n")
    L.append("A body outside its red box with green and magenta AGREEING is a "
             "**3D-model** defect with no board exposure — gerbers and CPL "
             "derive from pads, never from the model. Green and magenta "
             "DISAGREEING is a **render** defect: the picture is not the "
             "board, and any visual review done on it is void.\n")

    if fails:
        L.append(f"## FAIL — {len(fails)} ref(s): the render disagrees with the "
                 f"geometry\n")
        L.append("| ref | LCSC | centre delta mm | outward mm | expected | measured |")
        L.append("|---|---|---|---|---|---|")
        for ref, g in sorted(fails.items(), key=lambda kv: -kv[1]["ctr"]):
            L.append(f"| `{ref}` | {g['code']} | **{g['ctr']:.3f}** | "
                     f"**{g['out']:.3f}** | "
                     f"{g['exp'][0]:.3f},{g['exp'][1]:.3f}..{g['exp'][2]:.3f},{g['exp'][3]:.3f} | "
                     f"{g['meas'][0]:.3f},{g['meas'][1]:.3f}..{g['meas'][2]:.3f},{g['meas'][3]:.3f} |")
        L.append("")
    if unmeasured:
        L.append(f"## FAIL — {len(unmeasured)} ref(s) that SHOULD have been "
                 f"measurable and were not\n")
        for ref, why in sorted(unmeasured.items()):
            L.append(f"- `{ref}` — {why}")
        L.append("")
    if orphans:
        L.append(f"## FAIL — {len(orphans)} twin finding(s) naming no footprint\n")
        for ref, st in sorted(orphans):
            L.append(f"- `{ref}` ({st}) is in the twin report and not on the board")
        L.append("")
    if no_courtyard:
        L.append(f"## FAIL — {len(no_courtyard)} footprint(s) with no courtyard "
                 f"on either layer\n")
        L.append("- " + ", ".join(f"`{r}`" for r in sorted(no_courtyard)) + "\n")

    L.append(f"## Graded refs ({len(graded)})\n")
    L.append("| ref | LCSC | fit | centre delta mm | outward mm | edge deltas "
             "L,T,R,B mm | body px | courtyard excursion mm |")
    L.append("|---|---|---|---|---|---|---|---|")
    for ref, g in sorted(graded.items(), key=lambda kv: -kv[1]["ctr"]):
        fit = fit_description(g)
        ed = ",".join(f"{g['meas'][i] - g['exp'][i]:+.2f}" for i in range(4))
        L.append(f"| `{ref}` | {g['code']} | {fit} | {g['ctr']:.3f} | "
                 f"{g['out']:.3f} | {ed} | {g['npx']} | "
                 f"{excursion.get(ref, float('nan')):.3f} |")
    L.append("")
    if unresolvable:
        L.append(f"## Not measurable by construction ({len(unresolvable)}) — "
                 f"named, never silently passed\n")
        for ref, why in sorted(unresolvable.items()):
            L.append(f"- `{ref}` — {why}")
        L.append("")
    if no_model:
        L.append(f"## No JLC model at all ({len(no_model)}) — nothing to grade\n")
        for ref, why in sorted(no_model.items()):
            L.append(f"- `{ref}` — {why}")
        L.append("")
    if findings:
        L.append(f"## {len(findings)} ref(s) flagged by jlc_twin\n")
        L.append("| ref | status | detail |")
        L.append("|---|---|---|")
        for ref, fl in sorted(findings.items()):
            for st, detail in fl:
                L.append(f"| `{ref}` | **{st}** | {detail[:190]} |")
        L.append("")
    if crops:
        L.append("## Per-ref crops\n")
        for ref, p2 in crops:
            L.append(f"- `{ref}` -> `{p2.name}`")
        L.append("")
    txt = "\n".join(L) + "\n"
    if a.report:
        Path(a.report).write_text(txt)
    print(txt)

    hard = []
    if fails:
        hard.append(f"{len(fails)} unfaithful ref(s): "
                    + ", ".join(f"{r} (centre {g['ctr']:.2f}mm, outward "
                                f"{g['out']:.2f}mm)"
                                for r, g in sorted(fails.items())))
    if unmeasured:
        hard.append(f"{len(unmeasured)} resolvable-but-unmeasured ref(s): "
                    + ", ".join(sorted(unmeasured)))
    if orphans:
        hard.append(f"{len(orphans)} twin finding(s) naming no footprint: "
                    + ", ".join(f"{r}({s})" for r, s in sorted(orphans)))
    if no_courtyard:
        hard.append(f"{len(no_courtyard)} footprint(s) with no courtyard: "
                    + ", ".join(sorted(no_courtyard)))
    # A gate that grades nothing must never print PASS. This is the shape of
    # the `jlc_twin` exit-0 incident and of `bom_source_check`'s row_kind:
    # both reported success over a sweep that had covered almost none of its
    # input, and in both cases the number that would have exposed it was a
    # COVERAGE denominator nobody printed.
    if n_expect and not graded:
        hard.append(f"NOTHING MEASURED: {n_expect} refs have an expected body "
                    f"and zero were measured — this run graded nothing and "
                    f"must not report PASS")
    if a.bom and not n_expect:
        hard.append(f"NOTHING EXPECTED: --bom {a.bom} was given and not one "
                    f"ref on the {a.side} side resolved a JLC model from "
                    f"{twin_dir / 'easyeda'} — there is nothing to grade, so "
                    f"this run proves nothing about the render")

    print(f"COVERAGE: {len(graded)} measured / {n_expect} with an expected "
          f"body; {len(unresolvable)} unresolvable, {len(unmeasured)} "
          f"resolvable-but-unmeasured, {len(no_model)} no-model, "
          f"{drawn} courtyards drawn -> {ov}")
    if hard and not a.draw_only:
        for h in hard:
            print(f"OVERLAY FAIL: {h}")
        return 1
    if hard:
        for h in hard:
            print(f"OVERLAY FAIL (suppressed by --draw-only): {h}")
        return 0
    if not graded:
        print("OVERLAY: NOTHING GRADED — no ref on this side resolved an "
              "expected body, so this run says NOTHING about whether the "
              "render is faithful. It is a drawing, not a verdict.")
        return 0
    print(f"OVERLAY OK: every one of {len(graded)} measurable bodies renders "
          f"within {a.tol:.2f} mm of where the board puts it")
    return 0


if __name__ == "__main__":
    sys.exit(main())
