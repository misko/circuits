#!/usr/bin/env python3
"""JLC digital twin: verify that what JLCPCB will assemble matches our board.

For every BOM line with an LCSC code, fetch JLC's OWN footprint + 3D model
(easyeda2kicad), then:
  1. pad-correspondence: best-fit our footprint's pads against JLC's over
     rotation {0,90,180,270} x mirror. MIRRORED fit = mirror-numbered land
     pattern = dead board (this check found a live one on its first run).
  2. rotation audit: the fitted angle IS the CPL rotation offset JLC needs;
     compare against jlc_rotations_db.csv and print suggested rows.
  3. twin render: mount JLC's 3D models on OUR board at the fitted transform
     and render top/bottom - a local preview of what JLC's viewer will show.

usage: jlc_twin.py board.kicad_pcb bom.csv outdir [--cpl fab/cpl.csv]
Exit 1 on any MIRRORED, PAD-MISMATCH, PAD-GEOM, MODEL-REG, NO-BODY or
POLARITY-FIT finding.

MOUNTED ON A FIT IT HAD JUST REJECTED (2026-07-26). On PAD-MISMATCH this tool
recorded "no correspondence" and then mounted the body at that same rejected
fit's angle, so the render — the artifact a human is explicitly told to inspect
("VERIFY leads sit on pads visually") — was corrupted by the failure it was
supposed to help adjudicate. crow-recorder-central-v2 v1.5: J2, the board's
only USB-C, reported `PAD-MISMATCH best=(4.5947, False, 90)` and rendered 90
DEGREES ROTATED (7.555 x 8.940 mm where the part is 8.940 x 7.555) into two
sealed releases and past four review lenses. A failed fit is not evidence of an
angle; the mount now falls back to JLC's OWN footprint transform — offset 0,
their model rot_z, which this file already reads and already calls
"authoritative" — and says so as MOUNT-FALLBACK. The render is now gated
against that transform by `twin_overlay.py` (canon A-RENDER), which measures
the body in PIXELS so it cannot agree with a wrong mount by construction.

MOUNT HANDEDNESS INCIDENT (2026-07-25) — the SECOND half of the bug below.
Fixing `xform()` in 1b69760 left FOUR more hand-inlined copies of the wrong
form: the render mount's offset, its z-rotation, and the model-frame rotation
in BOTH `reg_check()` and `model_self_check()`. Because MODEL-REG used the
same wrong form as the mount, it graded the mount with the mount's own method
(canon M1, again) — so a TRUE 14.37 mm finding on a shipped XT60 was waived as
a false alarm and usb-hub-3s-v3 v1.5 sealed with every 90/270 part rendered
180 deg out. All five sites now route through ONE operator each
(`xform` / `local_to_board` / `model_rot`), each pinned against an authority
outside this file: pcbnew for pad geometry, `kicad-cli pcb render` for the
model frame. `board_to_local()` is a LEGITIMATE inverse whose literal text
matches the bug — match on the FRAMES a site maps between, never on the
expression.

HANDEDNESS INCIDENT (2026-07-25) — `xform()` was WRONG and every `jlc_offset`
this tool reported before that date is NEGATED. `xform()` used the opposite
handedness to `local_to_board()`. Measured against pcbnew itself over 72 pads
on rotated footprints (`pad.GetFPRelativePosition()` vs `pad.GetPosition()`):
local_to_board's form is EXACT (max error 0.000000 mm on all 72); the old
xform form was off by up to 23.926763 mm, losing every 90 deg sample (26) and
every 270 deg sample (4) and tying at 180 (42), where the two forms are
mathematically identical. That tie is why it hid for so long: 0/180 are
sign-invariant, 90/270 negate into each other, so the error was invisible on
more than half the fleet and exactly 180 deg wrong on the rest.

Consequences, all paid: six rows of `jlc_lcsc_rotations.csv` had been
populated FROM this function and were all 180 deg wrong; a SEALED release that
was correct (crow-recorder-central-v2 v1.2) was "fixed" into a wrong one
(v1.3) on that evidence; and an external reviewer reading the table was misled
by it. Canon M1, twice over — the authority table WAS the checker's output, so
every consumer inherited the same negation and nothing independent could
object.

STILL HELD as a consequence: promoting ROT-DB-SUGGEST to blocking, and the
A-ROT release gate. Neither may rank this table as AUTHORITY. A rotation gate
must re-derive the angle from the BOARD plus JLC's cached model with an
operator VERIFIED against pcbnew — never from `jlc_offset`, and never from a
table populated by it. The fix is pinned by `t1_jlc_twin.py`
(`t_xform_matches_pcbnew`, `t_fit_offset_handedness`), both RED-verified
against the pre-fix form.

Checks beyond the fit itself:
  - PAD-GEOM: pairwise pad-center distances (rotation/translation-invariant,
    so no best-fit can smear them) must agree between our footprint and
    JLC's within PAD_GEOM_TOL. A disagreement means the two land patterns
    differ dimensionally - the model WILL render off our pads by part of
    that delta, and someone must decide which pattern matches the part
    datasheet (adjudicate with evidence). Found via a DPAK whose tab-to-lead
    distance differed 0.65mm; the fit split it into an unexplained 0.43mm
    residual (2026-07-16).
  - NO-BODY (BLOCKING, own adjudication key): after mounting, every CPL
    designator is walked, its 3D model path expanded through KiCad's OWN
    ${VAR} table, and required to be a file with size > 0. Deliberately
    independent of the fit path — it asks the filesystem, not the fitter.
    Headline `bodies mounted: N/M`, and `missing_models.txt` is GENERATED
    from this pass. A PAD-MISMATCH / FETCH-FAILED waiver CANNOT discharge it.
  - PAD-MULTIPLICITY (non-fatal): a pad number named a different number of
    times on the two footprints. Those numbers are fitted by CENTROID instead
    of discarding the whole part (which is what used to happen).
  - POLARITY-CHECK: 2-pad polarized parts (electrolytics, diodes, LEDs)
    where 0 and 180 fit the pads equally - the pad fit cannot orient the
    model, so its polarity marking in the render is unverified and must be
    checked against our silk + the JLC order preview.
  - --assembly 03_src/rules/assembly.yaml: pull the ref->LCSC pairs for
    parts that are CODED but NOT ASSEMBLED (and for consigned parts) out of
    the ONE declared home, so those bodies render and their land patterns are
    checked too. This REPLACES hand-typing `--also REF=LCSC`: a hand-typed
    list is a second home for the population set and drifts from the first
    (cooksense v1.1's MANIFEST and CPL disagreed on 12 refs for exactly that
    reason). `--also` still works for an ad-hoc probe.
    A not-assembled entry may instead declare `twin_body: {source: board}`
    to retain the board footprint's exact local model, or
    `twin_body: {source: file, model: PATH}` to mount a project-owned model.
    These manual-install bodies are included in the NO-BODY denominator even
    though they are deliberately absent from the CPL. A declared local body
    always wins over an LCSC code: a catalog near-match must never replace the
    intended mechanical body merely because it can be fetched.
  - --also REF=LCSC[,REF=LCSC..]: include hand-solder/uncoded parts with
    known LCSC codes so their bodies render too (connector overhang and
    orientation checks otherwise never run for exactly the parts a human
    solders by eye).

Run with the KiCad-bundled python (/usr/bin/python3, pcbnew importable).
Requires easyeda2kicad (pip); resolved from $EASYEDA2KICAD or known venvs.
"""
import argparse
import csv
import glob
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jlc_rotation_resolve import load_lcsc_rotations  # noqa: E402

E2K_CANDIDATES = [os.environ.get("EASYEDA2KICAD", ""),
                  shutil.which("easyeda2kicad") or "",
                  os.path.expanduser("~/virtual-envs/spf/bin/easyeda2kicad"),
                  os.path.expanduser("~/.local/bin/easyeda2kicad")]
E2K = next((c for c in E2K_CANDIDATES if c and os.path.exists(c)), None)

RIGHT_ANGLES = (0, 90, 180, 270)
FIT_TOL = 0.5      # mm max per-pad error for a "fit"
MIRROR_MARGIN = 1.0  # mirrored fit must beat non-mirrored by this to accuse
PAD_GEOM_TOL = 0.3   # mm max pairwise pad-distance disagreement ours vs JLC
POLARIZED_FP = ("CP_", "C_Elec", "D_", "LED", "Diode")  # 0/180-ambiguity check


# A network/API failure is NOT evidence that a part has no CAD. Conflating the
# two let a twin run exit 0 having verified almost nothing: lipo3s-usb-hub v1.0
# lost 11 parts (XT60, USB-C, 3x USB-A, 6 FETs, ICs) to EasyEDA API errors, every
# one recorded as "NO-CAD", and the gate passed (2026-07-20). The same blind spot
# would hide a real mirrored footprint. Transient failures are now a DISTINCT,
# BLOCKING state (FETCH-FAILED) with a partial-retry hint.
TRANSIENT_PAT = re.compile(
    r"failed to fetch|timed?\s?out|timeout|connection|network|temporar|"
    r"rate.?limit|429|50[234]|max retries|ssl|certificate|resolve|unreachable",
    re.I)

# AFFIRMATIVE "the library genuinely has no model for this part" messages.
# Everything else is treated as a fetch failure — see fetch() for why this
# allowlist, not TRANSIENT_PAT, is what decides the disposition.
NOCAD_PAT = re.compile(
    r"no cad data|no 3d model|no footprint|not found|does not exist|"
    r"is not available|no such (component|part)|empty (model|footprint)",
    re.I)


def fetch(lcsc, cachedir, attempts=None):
    """easyeda2kicad --full into a per-code dir.
    Returns (fp_path, None, None) on success, else (None, reason, kind) where
    kind is 'transient' (network/API — NOT checked, must block) or
    'nocad' (the library genuinely has no model for this part)."""
    import time
    if attempts is None:
        attempts = int(os.environ.get("JLC_TWIN_FETCH_ATTEMPTS", "4"))
    d = Path(cachedir) / lcsc
    mods = glob.glob(str(d / "jlc.pretty" / "*.kicad_mod"))
    r = None
    for attempt in range(attempts):
        if mods:
            return mods[0], None, None
        d.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([E2K, "--full", "--lcsc_id", lcsc, "--output",
                            str(d / "jlc.kicad_sym"), "--use-cache"],
                           capture_output=True, text=True)
        mods = glob.glob(str(d / "jlc.pretty" / "*.kicad_mod"))
        if not mods and attempt < attempts - 1:
            time.sleep(4 * (attempt + 1))   # 4s, 8s, 12s … EasyEDA rate-limits bursts
    if mods:
        return mods[0], None, None
    msg = (((r.stderr or r.stdout).strip().splitlines()[-1:]) if r else []) or ["no CAD data"]
    joined = " ".join(msg)
    # FAIL CLOSED. This used to be `transient if TRANSIENT_PAT else nocad`,
    # i.e. any message the pattern didn't recognise was declared "the library
    # has no model" — a DISPOSITION — and exited 0. On 2026-07-20 that let 11
    # unverified parts through on an `HTTP Error 403: Forbidden`, which
    # matches neither pattern. A part we could not fetch was never checked,
    # so the only safe default is to BLOCK. NO-CAD now requires the tool to
    # say so affirmatively (NOCAD_PAT); a non-zero exit is never NO-CAD.
    if TRANSIENT_PAT.search(joined):
        kind = "transient"
    elif NOCAD_PAT.search(joined) and (r is None or r.returncode == 0):
        kind = "nocad"
    else:
        kind = "transient"
        msg = list(msg) + [f"(unrecognised fetcher failure, rc="
                           f"{'?' if r is None else r.returncode}; treated as "
                           f"FETCH-FAILED because an unfetched part is an "
                           f"UNCHECKED part)"]
    return None, msg, kind


def canonical_pad_number(value):
    """Normalize formatting-only decimal zeros, preserve alphanumeric pins.

    EasyEDA/JLC connector CAD commonly names pads ``01``..``09`` while the
    KiCad footprint names the same physical identities ``1``..``9``. Without
    normalization J7's ten-pin header appeared to share only pad 10, so a
    one-point 'fit' falsely reported offset 0 against the independently
    measured 270-degree authority row.
    """
    value = str(value).strip().strip('"')
    return str(int(value)) if value.isdigit() else value


def pads_of(fp):
    d = {}
    for p in fp.Pads():
        n = canonical_pad_number(p.GetNumber())
        if n:
            d.setdefault(n, []).append((p.GetPosition().x / 1e6,
                                        p.GetPosition().y / 1e6))
    return d


def apply_pad_alias(jraw, alias):
    """Rename JLC pad NUMBERS by {jlc_pad: our_pad}, as ONE SIMULTANEOUS
    permutation.

    It must be simultaneous. The previous implementation mutated `jraw` in
    place while iterating the alias, so each rename saw the results of the
    ones before it — which makes a 2-WAY SWAP impossible to express. For
    {'3':'4','4':'3'}: step one moved pad 3's coords onto key 4 (now holding
    BOTH), step two moved key 4 — both entries — onto key 3, leaving pad 4
    gone and pad 3 doubled. Measured on crow-mic-pod-v2's LS1 (C22359707),
    whose true correspondence to JLC's BUZ-SMD_4P footprint IS a 3<->4 swap
    of the two NC dummy pads; the swap could not be written down, so the
    sealed waiver asserted a 1<->2 swap instead — a mapping that fits the
    geometry at NO rotation (rms 7.1007mm at all four angles, vs 0.1414mm
    for the true one).

    A dict comprehension over a SNAPSHOT also makes the identity alias
    (5->5) harmless without a special case, so the old `src != dst` guard
    is gone with the bug it was guarding.
    """
    if not alias:
        return jraw
    out = {}
    for num, coords in jraw.items():
        out.setdefault(alias.get(num, num), []).extend(coords)
    return {k: sorted(v) for k, v in out.items()}


def centroid(d):
    xs = [x for v in d.values() for x, _ in v]
    ys = [y for v in d.values() for _, y in v]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def centered(d):
    cx, cy = centroid(d)
    return {k: [(x - cx, y - cy) for x, y in v] for k, v in d.items()}


def xform(d, ang, mir):
    """Rotate a pad set by `ang` in KiCad's OWN sense (y-down screen frame,
    CCW), optionally mirrored in x.

    HANDEDNESS FIXED 2026-07-25. This used to be `(x*c - y*s, x*s + y*c)` —
    the OPPOSITE handedness to `local_to_board()` below, which is the operator
    KiCad actually applies to a rotated footprint's pads. Measured against
    pcbnew itself over 72 pads on rotated footprints
    (`pad.GetFPRelativePosition()` vs `pad.GetPosition()`): the form used here
    now is EXACT (max error 0.000000 mm on all 72); the old form was off by
    up to 23.926763 mm — it lost every 90 deg sample (26 pads) and every 270
    deg sample (4 pads), and TIED at 180 (42 pads), where the two forms are
    mathematically identical.

    That tie is why the bug survived: 0 and 180 are sign-invariant under this
    negation, so every offset the twin ever reported was correct at 0/180 and
    exactly 180 deg wrong at 90/270. Six rows of `jlc_lcsc_rotations.csv` had
    been populated FROM this function and were all 180 deg wrong; one sealed
    release that was RIGHT (crow-recorder-central-v2 v1.2) was "fixed" into a
    wrong one (v1.3) on its evidence. Canon M1: the authority table WAS the
    checker's output, so every consumer inherited the same error and a review
    that read the table was misled by it.

    Pinned by `t1_jlc_twin.t_xform_matches_pcbnew` (the operator vs pcbnew,
    both handednesses) and `t_fit_offset_handedness` (the fitted offset), both
    RED-verified against the pre-fix form.
    """
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = {}
    for k, v in d.items():
        pts = [(-x if mir else x, y) for x, y in v]
        out[k] = sorted((round(x * c + y * s, 3), round(-x * s + y * c, 3))
                        for x, y in pts)
    return out


def pad_centroids(d):
    return {k: (sum(x for x, _ in v) / len(v), sum(y for _, y in v) / len(v))
            for k, v in d.items()}


def pad_geom_diff(ours, jlc, common):
    """Worst pairwise pad-center distance disagreement between the two
    footprints over the common pad numbers. Rotation/translation-invariant:
    unlike the best-fit residual (which splits a land-pattern disagreement
    across pads and reports an unexplained scalar), this pins the delta to a
    named pad pair. Returns (max_delta_mm, "k1<->k2 ours X vs JLC Y")."""
    oc = pad_centroids({k: ours[k] for k in common})
    jc = pad_centroids({k: jlc[k] for k in common})
    ks = sorted(common)
    worst, detail = 0.0, ""
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            do = math.hypot(oc[ks[i]][0] - oc[ks[j]][0],
                            oc[ks[i]][1] - oc[ks[j]][1])
            dj = math.hypot(jc[ks[i]][0] - jc[ks[j]][0],
                            jc[ks[i]][1] - jc[ks[j]][1])
            if abs(do - dj) > worst:
                worst = abs(do - dj)
                detail = (f"pad {ks[i]}<->{ks[j]} ours {do:.2f}mm "
                          f"vs JLC {dj:.2f}mm")
    return worst, detail


def pad_multiplicity(a, b):
    """Pad numbers the two footprints name a DIFFERENT NUMBER OF TIMES."""
    return sorted(k for k in (set(a) & set(b)) if len(a[k]) != len(b[k]))


def fit_err(a, b):
    """Max per-pad residual, or None when there is nothing in common.

    MULTIPLICITY FALLBACK (2026-07-25). This used to `return None` the moment
    one pad number appeared a different number of times on the two sides — a
    NAMING CONVENTION, not a geometric disagreement — which made every angle
    unfittable, `best_fit()` empty, and the whole part fall out through
    PAD-MISMATCH: no mount, no body, no rotation audit, no MODEL-REG. Six
    power MOSFETs shipped that way on usb-hub-3s-v3 v1.5 (KiCad's
    PowerPAK_SO-8_Single names five entities "5" — merged paddle + four drain
    fingers — where JLC's DFN-8 names one corner lead "5"), and their absence
    was invisible because the release's own missing-model list was
    hand-authored and said zero. Discarding the rotation audit over a
    numbering convention is strictly worse than measuring the pad-number
    CENTROIDS, which is what the mount is anchored on anyway."""
    common = set(a) & set(b)
    if not common:
        return None
    errs = []
    for k in common:
        if len(a[k]) != len(b[k]):
            (ax, ay), (bx, by) = (pad_centroids({k: a[k]})[k],
                                  pad_centroids({k: b[k]})[k])
            errs.append(math.hypot(ax - bx, ay - by))
            continue
        for (x1, y1), (x2, y2) in zip(sorted(a[k]), sorted(b[k])):
            errs.append(math.hypot(x1 - x2, y1 - y2))
    return max(errs)


def best_fit(ours, jlc):
    """-> (maxerr, ang, mirrored) sorted best-first; non-mirrored wins ties."""
    fits = []
    for mir in (False, True):
        for ang in RIGHT_ANGLES:
            e = fit_err(ours, xform(jlc, ang, mir))
            if e is not None:
                fits.append((e, mir, ang))
    return sorted(fits)


def board_to_local(bdx, bdy, rot_deg):
    """Convert a board-frame nudge (+x east, +y south) to footprint-local
    (rot-0) frame for a part rotated rot_deg on the board. KiCad rotation
    is CCW in the y-down screen frame: local->board is
    (lx*cos+ly*sin, -lx*sin+ly*cos); this is the inverse."""
    th = math.radians(rot_deg)
    return (bdx * math.cos(th) - bdy * math.sin(th),
            bdx * math.sin(th) + bdy * math.cos(th))


def local_to_board(ldx, ldy, rot_deg):
    th = math.radians(rot_deg)
    return (ldx * math.cos(th) + ldy * math.sin(th),
            -ldx * math.sin(th) + ldy * math.cos(th))


def model_rot(mx, my, rot_z_deg):
    """Rotate a point in the 3D MODEL frame (y-UP mm) by a `m_Rotation.z`
    entry, in the sense KiCad's renderer actually applies.

    HANDEDNESS FIXED 2026-07-25 (the same defect as `xform()`, two more
    copies of it: here and in `reg_check`). This used to be
    `(x*cos - y*sin, x*sin + y*cos)` — the mirror of the operator below, and
    therefore exactly 180 deg wrong at rot_z 90/270 and identical at 0/180.
    48 of 400 cached JLC footprints (12%) carry rot_z 90 or 270.

    MEASURED, not derived (canon M1 — the authority is KiCad's renderer, not
    this file). A synthetic asymmetric bar (model frame x 0..8 mm,
    y -1..+1 mm) was mounted at board (20,20) on a 40x40 board and rendered
    with `kicad-cli pcb render --side top` at 19.25 px/mm:

        rot_z  this form predicts  the old form predicts  RENDERED
          0    east                east                   east   (x 20.0->28.0)
         90    SOUTH               north                  SOUTH  (y 20.0->28.0)
        180    west                west                   west   (x 12.0->20.0)
        270    NORTH               south                  NORTH  (y 12.0->20.0)

    Residual against this form <= 0.014 mm (half a pixel) at every angle;
    against the old form 8.000 mm at both 90 and 270. 0 and 180 tie, which is
    why this survived beside three other copies of the same sign error.

    Note the frame: this is `local_to_board`'s operator applied with a
    POSITIVE angle in the y-UP model frame, which is identically the same as
    applying it with a NEGATIVE angle after the flip to the y-down board
    frame. Pinned by `t1_jlc_twin.t_model_rot_matches_render`.
    """
    th = math.radians(rot_z_deg)
    return (mx * math.cos(th) + my * math.sin(th),
            -mx * math.sin(th) + my * math.cos(th))


def model_self_check(jfp, jca):
    """MODEL-SELF: does JLC's 3D model sit on JLC's OWN footprint pads?
    Computed entirely in THEIR frame - no mount math, no land-pattern
    involvement - so it isolates model-internal defects (a DPAK model was
    drawn ~0.95mm off its own pads and every mount-side check misfiled it,
    2026-07-16). Returns (dx, dy) of model plan-bbox center vs the
    common-pad centroid in the JLC footprint frame (y-down), or None."""
    jmodels = list(jfp.Models())
    if not jmodels:
        return None
    mb = wrl_bbox(jmodels[0].m_Filename)
    if not mb:
        return None
    jm = jmodels[0]
    xs, ys = [], []
    for mx in (mb[0], mb[2]):
        for my in (mb[1], mb[3]):
            rx, ry = model_rot(mx, my, jm.m_Rotation.z)
            xs.append(rx * jm.m_Scale.x + jm.m_Offset.x)
            ys.append(-(ry * jm.m_Scale.y + jm.m_Offset.y))
    return ((min(xs) + max(xs)) / 2 - jca[0],
            (min(ys) + max(ys)) / 2 - jca[1])


def wrl_bbox(path):
    """Plan-view (x,y) bbox of a KiCad WRL model, in mm.
    KiCad VRML convention: 1 VRML unit = 2.54 mm. Returns (minx,miny,maxx,maxy)
    in the MODEL frame (y-up), or None if unparseable."""
    import re
    try:
        txt = open(path, errors="ignore").read()
    except OSError:
        return None
    pts = []
    for m in re.finditer(r"point\s*\[([^\]]*)\]", txt):
        nums = re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", m.group(1))
        for i in range(0, len(nums) - 2, 3):
            pts.append((float(nums[i]), float(nums[i + 1])))
    if not pts:
        return None
    xs = [p[0] * 2.54 for p in pts]
    ys = [p[1] * 2.54 for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def reg_check(model_bbox, jm, ang, jc, oc, fp):
    """Model-registration invariant: the mounted body's plan bbox must sit on
    OUR footprint's courtyard. Returns (center_delta_mm, size_ratio, our_ctr)
    or None when there is no courtyard to compare against."""
    cc = fp.GetCourtyard(pcbnew.F_CrtYd)
    if not cc.OutlineCount():
        return None
    cb = cc.BBox()
    rot = fp.GetOrientationDegrees()
    fpos = fp.GetPosition()
    # THREE frame hops, each through the ONE shared, pcbnew/render-verified
    # operator — never a hand-inlined copy. Until 2026-07-25 the first two
    # hops here were hand-inlined with the OPPOSITE handedness, so MODEL-REG
    # graded the mount using the mount's own error: the check and the checked
    # shared a method (canon M1) and a 14.37 mm real defect was adjudicated
    # away as a false alarm.
    corners = []
    for mx in (model_bbox[0], model_bbox[2]):
        for my in (model_bbox[1], model_bbox[3]):
            # 1. model frame (y-up) -> JLC footprint frame (y-down)
            rx, ry = model_rot(mx, my, jm.m_Rotation.z)
            jx = rx * jm.m_Scale.x + jm.m_Offset.x
            jy = -(ry * jm.m_Scale.y + jm.m_Offset.y)   # to y-down
            # 2. JLC frame -> our footprint local frame (the pad-fit angle)
            lxy = xform({"p": [(jx - jc[0], jy - jc[1])]}, ang, False)["p"][0]
            lx, ly = lxy[0] + oc[0], lxy[1] + oc[1]
            # 3. our local -> board (the footprint's own rotation)
            bx, by = local_to_board(lx, ly, rot)
            corners.append((bx + fpos.x / 1e6, by + fpos.y / 1e6))
    mnx = min(c[0] for c in corners); mxx = max(c[0] for c in corners)
    mny = min(c[1] for c in corners); mxy = max(c[1] for c in corners)
    mcx, mcy = (mnx + mxx) / 2, (mny + mxy) / 2
    ccx, ccy = cb.Centre().x / 1e6, cb.Centre().y / 1e6
    delta = math.hypot(mcx - ccx, mcy - ccy)
    area_m = max(1e-6, (mxx - mnx) * (mxy - mny))
    area_c = max(1e-6, cb.GetWidth() / 1e6 * cb.GetHeight() / 1e6)
    return delta, area_m / area_c, (ccx, ccy)


def kicad_env(board_path):
    """The ${VAR} substitution table KiCad ITSELF would use to resolve a 3D
    model path: its own config's `environment.vars`, then any KICAD* in the
    process environment, then the documented defaults, then KIPRJMOD."""
    import json
    env = {}
    for ver in ("10.0", "9.0", "8.0", "7.0"):
        p = Path.home() / ".config" / "kicad" / ver / "kicad_common.json"
        if p.exists():
            try:
                v = (json.load(open(p, encoding="utf-8-sig")).get("environment") or {}).get("vars")
                env.update({str(k): str(x) for k, x in (v or {}).items()})
            except Exception:
                pass
    env.update({k: v for k, v in os.environ.items() if k.startswith("KICAD")})
    user_3d = Path.home() / ".local" / "share" / "kicad" / "10.0" / "3dmodels"
    system_3d = Path("/usr/share/kicad/3dmodels")
    dflt_3d = str(user_3d if user_3d.is_dir() else system_3d)
    for var, dflt in (("KICAD10_3DMODEL_DIR", dflt_3d),
                      ("KICAD9_3DMODEL_DIR", "/usr/share/kicad/3dmodels"),
                      ("KICAD8_3DMODEL_DIR", "/usr/share/kicad/3dmodels"),
                      ("KISYS3DMOD", dflt_3d)):
        env.setdefault(var, dflt)
    env["KIPRJMOD"] = str(Path(board_path).resolve().parent)
    return env


def resolve_model(filename, env, base):
    """Expand ${VARS} and return the on-disk path, or None. `None` means the
    render shows NOTHING for this model — an unset variable, a default that
    does not exist on this machine, or a file that was never installed."""
    s = str(filename)
    for _ in range(4):
        prev = s
        for k, v in env.items():
            s = s.replace("${%s}" % k, v).replace("$(%s)" % k, v)
        if s == prev:
            break
    if "${" in s or "$(" in s:
        return None
    p = Path(os.path.expanduser(s))
    for cand in ([p] if p.is_absolute() else [Path(base) / p, p]):
        try:
            if cand.is_file() and cand.stat().st_size > 0:
                return str(cand)
        except OSError:
            pass
    return None


def no_body_pass(tb, refs, board_path):
    """TERMINAL gate: after mounting, does every CPL designator actually end
    up with a 3D body a renderer can load?

    Deliberately INDEPENDENT of the fit path (canon M1). It asks the
    filesystem, not the fitter — so a part the fitter skipped, a part whose
    fetch failed, and a part whose KiCad model path points at a library that
    is not installed all land in the same place. Nothing in this tool asked
    that question before 2026-07-25: `wrl_bbox` ran only on refs that already
    HAD a JLC model, so the one file probe in the file could not see an
    unmounted part. usb-hub-3s-v3 v1.5 shipped 7 of 108 placements with no
    body at all (Q1-Q6 + R12) beside a hand-authored `missing_models.txt`
    stating the gap was zero.

    Returns (mounted, missing) where missing is [(ref, reason), ...]."""
    env = kicad_env(board_path)
    base = Path(board_path).resolve().parent
    mounted, missing = [], []
    for ref in sorted(refs):
        fp = tb.FindFootprintByReference(ref)
        if fp is None:
            missing.append((ref, "no footprint on the board"))
            continue
        models = list(fp.Models())
        if not models:
            missing.append((ref, "footprint carries no 3D model entry"))
            continue
        hits = [(m.m_Filename, resolve_model(m.m_Filename, env, base))
                for m in models]
        if any(h[1] for h in hits):
            mounted.append(ref)
        else:
            missing.append((ref, "; ".join(
                f"unresolved model path {f!r}" for f, _ in hits)))
    return mounted, missing


def declared_twin_bodies(assembly, assembly_path=""):
    """Return REF -> twin_body declarations from assembly intent.

    The assembly manifest is the population authority, so it is also the
    only safe place to say that a deliberately non-CPL part is nevertheless
    installed in the finished-product render. Keep this parser independent
    of model mounting so its population result is easy to regression-test.
    """
    bodies = {}
    for key in ("not_assembled", "consigned"):
        for entry in (assembly.get(key) or []):
            body = entry.get("twin_body")
            if not body:
                continue
            if not isinstance(body, dict):
                raise ValueError(f"{key} twin_body must be a mapping")
            source = str(body.get("source") or "").strip()
            if source not in ("board", "file", "part"):
                raise ValueError(
                    f"{key} twin_body.source must be board, file, or part, "
                    f"got {source!r}")
            if source == "file" and not str(body.get("model") or "").strip():
                raise ValueError(f"{key} twin_body source=file requires model")
            if source == "part":
                dossier = str(body.get("dossier") or "").strip()
                if not dossier or not assembly_path:
                    raise ValueError(
                        f"{key} twin_body source=part requires dossier and "
                        f"an assembly path")
                project = Path(assembly_path).resolve().parents[2]
                part_path = project / "02_parts" / dossier / "part.yaml"
                if not part_path.is_file():
                    raise ValueError(f"twin_body dossier not found: {part_path}")
                import yaml
                part = yaml.safe_load(open(part_path, encoding="utf-8-sig")) or {}
                part_body = part.get("twin_body")
                if not isinstance(part_body, dict):
                    raise ValueError(f"{part_path} has no twin_body mapping")
                body = dict(part_body)
                source = str(body.get("source") or "").strip()
                if source not in ("board", "file"):
                    raise ValueError(
                        f"{part_path} twin_body.source must be board or file")
                if source == "file":
                    raw_model = str(body.get("model") or "").strip()
                    if not raw_model:
                        raise ValueError(f"{part_path} twin_body requires model")
                    model = Path(os.path.expanduser(raw_model))
                    if not model.is_absolute():
                        model = (part_path.parent / model).resolve()
                    body["model"] = str(model)
                body["dossier"] = str(part_path)
            for ref in (entry.get("refs") or []):
                ref = str(ref).strip()
                if ref in bodies:
                    raise ValueError(f"duplicate twin_body declaration for {ref}")
                bodies[ref] = dict(body)
    return bodies


def install_declared_twin_bodies(board, bodies, assembly_path, board_path):
    """Apply manual-install body policy and return auditable report rows."""
    rows = []
    base = Path(assembly_path).resolve().parent
    for ref, body in sorted(bodies.items()):
        fp = board.FindFootprintByReference(ref)
        identity = str(body.get("identity") or "installed manual part").strip()
        authority = str(body.get("authority") or "").strip()
        limitation = str(body.get("limitation") or "").strip()
        source = body["source"]
        if fp is None:
            rows.append(("", ref, "LOCAL-BODY",
                         f"source={source}; identity={identity}; footprint missing"))
            continue
        if source == "file":
            model_path = Path(os.path.expanduser(str(body["model"])))
            if not model_path.is_absolute():
                model_path = (base / model_path).resolve()
            model = pcbnew.FP_3DMODEL()
            model.m_Filename = str(model_path)
            fp.Models().clear()
            fp.Models().push_back(model)
            detail = f"source=file model={model_path}"
        else:
            # Deliberately do not clear or re-register the board's model.
            # This branch exists for exact library bodies such as the complete
            # Keystone 3568 holder; a catalog code for one loose clip is not a
            # valid transform authority for the four-hole holder footprint.
            # Headless kicad-cli does not necessarily inherit the GUI's 3D
            # search-path variables. Resolve the filename now, but copy every
            # registration field unchanged: path normalization is not a new
            # mount transform.
            env = kicad_env(board_path)
            base_board = Path(board_path).resolve().parent
            old_models = list(fp.Models())
            fp.Models().clear()
            resolved_count = 0
            for old in old_models:
                model = pcbnew.FP_3DMODEL()
                resolved = resolve_model(old.m_Filename, env, base_board)
                model.m_Filename = resolved or old.m_Filename
                model.m_Scale = old.m_Scale
                model.m_Offset = old.m_Offset
                model.m_Rotation = old.m_Rotation
                fp.Models().push_back(model)
                resolved_count += bool(resolved)
            detail = ("source=board; JLC CAD replacement suppressed; "
                      f"resolved paths={resolved_count}/{len(old_models)}; "
                      "scale/offset/rotation retained")
        provenance = "; ".join(x for x in (
            f"identity={identity}",
            f"authority={authority}" if authority else "",
            f"limitation={limitation}" if limitation else "",
            f"dossier={body.get('dossier')}" if body.get("dossier") else "",
        ) if x)
        rows.append(("", ref, "LOCAL-BODY", f"{detail}; {provenance}"))
    return rows


def marker_side(fp, pads, layers=None):
    """Which pad does this footprint's POLARITY MARKING sit nearest?

    Numbering-free channel for a 2-pad polarized part. Both libraries draw an
    asymmetric silk/fab feature at the polarized end (KiCad chamfers the F.Fab
    outline at pin 1 and its LED_SMD/Diode convention puts the CATHODE there;
    EasyEDA draws a diode glyph and chamfers the silk body at the cathode).
    Project the graphics' extreme point onto the pad1->pad2 axis and report
    which pad it leans toward, plus how decisively.

    Returns (pad_number, margin_mm) or None when the graphics are symmetric
    enough that the answer would be a coin flip."""
    if layers is None:
        layers = (pcbnew.F_SilkS, pcbnew.F_Fab, pcbnew.B_SilkS, pcbnew.B_Fab)
    ks = sorted(pads)
    if len(ks) != 2:
        return None
    (ax, ay), (bx, by) = (pads[ks[0]][0], pads[ks[1]][0])
    ux, uy = bx - ax, by - ay
    L = math.hypot(ux, uy)
    if L < 1e-6:
        return None
    ux, uy = ux / L, uy / L
    mid = ((ax + bx) / 2, (ay + by) / 2)
    proj = []
    for g in fp.GraphicalItems():
        # SHAPES only: reference/value TEXT is placed for legibility, not to
        # mark polarity, and including it would let a refdes position decide
        # which end is the cathode.
        if g.GetLayer() not in layers or not isinstance(g, pcbnew.PCB_SHAPE):
            continue
        for pt in (g.GetStart(), g.GetEnd()):
            px, py = pt.x / 1e6, pt.y / 1e6
            proj.append((px - mid[0]) * ux + (py - mid[1]) * uy)
    if not proj:
        return None
    # the marking is the graphics' OVERHANG: whichever end the outline runs
    # further past the pad. A symmetric outline overhangs both ends equally.
    over_b, over_a = max(proj) - L / 2, -min(proj) - L / 2
    margin = abs(over_b - over_a)
    if margin < 0.15:            # 0.15 mm: below silk line width, not a signal
        return None
    return (ks[1] if over_b > over_a else ks[0]), margin


def rot_db(path):
    import re
    db = []
    if path and os.path.exists(path):
        for row in csv.reader(open(path)):
            if len(row) >= 2 and not row[0].startswith("Footprint"):
                try:
                    db.append((row[0], re.compile(row[0]), float(row[1])))
                except Exception:
                    pass
    return db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("bom")
    ap.add_argument("outdir")
    ap.add_argument("--rotations-db",
                    default=str(Path(__file__).parent / "jlc_rotations_db.csv"))
    ap.add_argument("--lcsc-rotations",
                    default=str(Path(__file__).parent / "jlc_lcsc_rotations.csv"),
                    help="per-LCSC rotation overrides (win over the name DB)")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--adjudications", default="",
                    help="YAML list of reviewed findings to accept: "
                         "[{lcsc, refs: [..], status, why}]")
    ap.add_argument("--also", default="",
                    help="REF=LCSC[,REF=LCSC..]: mount+check hand-solder/"
                         "uncoded parts with known codes (e.g. J1=C98732)")
    ap.add_argument("--cpl", default="",
                    help="fab/cpl.csv — the POPULATION ground truth. The "
                         "NO-BODY gate walks its Designator column, so the "
                         "coverage denominator is the placement count JLC "
                         "will actually run, not the BOM row count.")
    ap.add_argument("--assembly", default="",
                    help="03_src/rules/assembly.yaml — REF=LCSC pairs for "
                         "coded-but-not-assembled and consigned parts, read "
                         "from the ONE declared home instead of hand-typed "
                         "--also (canon A-POP)")
    args = ap.parse_args()
    adjudicated = []
    if args.adjudications and os.path.exists(args.adjudications):
        import yaml
        adjudicated = yaml.safe_load(open(args.adjudications)) or []

    model_rot_override = {a["lcsc"]: float(a["model_rot_z"])
                          for a in adjudicated if a.get("model_rot_z") is not None}
    model_xy_override = {a["lcsc"]: (float(a.get("model_dx", 0)),
                                     float(a.get("model_dy", 0)))
                         for a in adjudicated
                         if a.get("model_dx") is not None
                         or a.get("model_dy") is not None}
    # board-frame nudges: PREFERRED - the tool converts through each ref's
    # rotation, so the adjudicator never does frame math (a hand-converted
    # nudge shipped 90deg wrong once, 2026-07-16)
    board_xy_override = {a["lcsc"]: (float(a.get("board_dx", 0)),
                                     float(a.get("board_dy", 0)))
                         for a in adjudicated
                         if a.get("board_dx") is not None
                         or a.get("board_dy") is not None}
    # pad_alias: {jlc_pad: our_pad} renames JLC pad NUMBERS before the
    # correspondence fit. Naming-convention families (SOT-223 tab: KiCad
    # TabPin2 merges tab+lead as "2", JLC names the tab "4"; DPAK
    # merged-drain variants) otherwise yield PAD-MISMATCH best=none and
    # an unmounted model - the render then shows bare pads and every
    # model-side check (MODEL-REG, rotation, polarity) silently skips.
    pad_alias = {a["lcsc"]: {str(k): str(v)
                             for k, v in a["pad_alias"].items()}
                 for a in adjudicated if a.get("pad_alias")}

    def adjudicate(lcsc, ref, status):
        for a in adjudicated:
            if (a.get("lcsc") == lcsc and status == a.get("status")
                    and (not a.get("refs") or ref in a["refs"])):
                return a.get("why", "adjudicated")
        return None

    if E2K is None:
        sys.exit("easyeda2kicad not found: pip install easyeda2kicad, "
                 "or set $EASYEDA2KICAD")
    out = Path(args.outdir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    board = pcbnew.LoadBoard(args.board)
    by_ref = {fp.GetReference(): fp for fp in board.GetFootprints()}
    db = rot_db(args.rotations_db)
    lcsc_rot = load_lcsc_rotations(args.lcsc_rotations)

    lines = [r for r in csv.DictReader(open(args.bom, encoding="utf-8-sig"))
             if r.get("LCSC")]
    extra = []          # (ref, lcsc) pairs from --assembly / --also
    assembly = {}
    local_bodies = {}
    if args.assembly and os.path.exists(args.assembly):
        import yaml as _yaml
        assembly = _yaml.safe_load(open(args.assembly)) or {}
        try:
            local_bodies = declared_twin_bodies(assembly, args.assembly)
        except ValueError as exc:
            sys.exit(f"assembly twin_body schema: {exc}")
        for _key in ("not_assembled", "consigned"):
            for _e in (assembly.get(_key) or []):
                _code = str(_e.get("lcsc") or "").strip()
                for _r in (_e.get("refs") or []):
                    # An explicit installed-product body is mechanical
                    # authority. Never fetch a catalog near-match for it.
                    if _code and str(_r).strip() not in local_bodies:
                        extra.append((str(_r).strip(), _code))
        print(f"assembly: {len(extra)} coded not-assembled/consigned ref(s) "
              f"and {len(local_bodies)} declared local body ref(s) "
              f"from {args.assembly}")
    for pair in [p for p in args.also.split(",") if p.strip()]:
        ref, _, code = pair.partition("=")
        if not code:
            sys.exit(f"--also expects REF=LCSC, got: {pair}")
        extra.append((ref.strip(), code.strip()))
    # Local-body policy also wins over a code already present on the BOM.
    # Split grouped rows so one manual ref cannot suppress its coded siblings.
    filtered = []
    for row in lines:
        refs = [d.strip() for d in row["Designator"].split(",")
                if d.strip() and d.strip() not in local_bodies]
        if refs:
            copy = dict(row)
            copy["Designator"] = ",".join(refs)
            filtered.append(copy)
    lines = filtered
    on_bom = {d.strip() for r in lines for d in r["Designator"].split(",")}
    for ref, code in extra:
        if ref not in on_bom:       # never double-check a ref already on the BOM
            lines.append({"Designator": ref, "LCSC": code})
    findings, criticals, twin, padgeom = [], [], {}, {}
    mount_fallback = set()   # refs mounted at JLC's own transform, fit failed
    bodies_line = ("bodies mounted: SKIPPED (nothing fitted, so "
                   "nothing was mounted)")
    ref_lcsc = {}          # ref -> LCSC, for NO-BODY rows
    for _r in lines:
        for _d in _r["Designator"].split(","):
            ref_lcsc.setdefault(_d.strip(), _r["LCSC"])
    fetch_failed = set()
    for r in lines:
        lcsc = r["LCSC"]
        fp_path, err, kind = fetch(lcsc, out / "easyeda")
        if err:
            # transient = the part was NEVER CHECKED -> blocking, not a disposition
            status = "FETCH-FAILED" if kind == "transient" else "NO-CAD"
            findings.append((lcsc, r["Designator"], status, str(err)))
            if kind == "transient":
                fetch_failed.add(lcsc)
                criticals.extend(d.strip() for d in r["Designator"].split(","))
            continue
        jfp = pcbnew.FootprintLoad(str(Path(fp_path).parent),
                                   Path(fp_path).stem)
        self_checked = False
        for ref in [d.strip() for d in r["Designator"].split(",")]:
            fp = by_ref.get(ref)
            if fp is None:
                findings.append((lcsc, ref, "NOT-ON-BOARD", ""))
                continue
            # compare in the footprint's own frame (undo board rotation)
            rot = fp.GetOrientationDegrees()
            fp.SetOrientationDegrees(0)
            opads_raw = pads_of(fp)
            # Cache the numbering-free marking in the SAME footprint-local
            # frame as opads_raw.  Restoring the board rotation before calling
            # marker_side mixed global graphics with zero-rotation pad
            # coordinates, so every 180-degree instance of an otherwise
            # identical polarized footprint could report the opposite end
            # (programmable-usb2-hub D2 PASS / D3 FAIL on the same C2128).
            ours_mark_local = marker_side(fp, opads_raw)
            fp.SetOrientationDegrees(rot)
            # center BOTH sets on the COMMON numbered pads only: centering
            # each on its own full set biases the fit/mount whenever one side
            # names extra pads (XT60 pegs, FET drain fingers) - the XT60 model
            # rendered 7mm off its holes before this (2026-07-16)
            jraw = pads_of(jfp)
            jraw = apply_pad_alias(jraw, pad_alias.get(lcsc, {}))
            common = set(opads_raw) & set(jraw)
            if not common:
                findings.append((lcsc, ref, "PAD-MISMATCH", "no common pad numbers"))
                criticals.append(ref)
                continue
            mult = pad_multiplicity(opads_raw, jraw)
            if mult:
                findings.append((lcsc, ref, "PAD-MULTIPLICITY",
                                 f"pad number(s) {','.join(mult)} appear "
                                 f"a different number of times on the two "
                                 f"footprints (ours "
                                 f"{ {k: len(opads_raw[k]) for k in mult} } vs "
                                 f"JLC { {k: len(jraw[k]) for k in mult} }) — "
                                 "a NAMING convention, not a geometry defect; "
                                 "those numbers are fitted by CENTROID. "
                                 "Non-fatal, but PAD-GEOM readings on the "
                                 "affected numbers compare a merged centroid "
                                 "against a single lead"))
            # land-pattern geometry gate: pairwise distances can't be smeared
            # by the fit the way the residual can
            gd, gdet = pad_geom_diff(opads_raw, jraw, common)
            padgeom[ref] = gd
            if gd > PAD_GEOM_TOL:
                findings.append((lcsc, ref, "PAD-GEOM",
                                 f"{gdet} (d{gd:.2f}mm) - land patterns "
                                 "disagree; adjudicate against the part "
                                 "datasheet's recommended pattern"))
                criticals.append(ref)
            # NOTE (2026-07-16, validated by pixel measurement): the mount
            # anchor stays the UNWEIGHTED common-pad centroid. An area-
            # weighted (wetting-force) anchor was tried and made the known
            # PAD-GEOM case WORSE - JLC's big tab pad center sits ~0.3mm
            # off their own tab METAL, so pad-anchoring of any flavor
            # inherits pad-style offsets. When a PAD-GEOM part renders
            # off-pad, the adjudication may set model_dx/model_dy (our
            # footprint-local mm, +x east +y south) with pixel evidence.
            _oca = centroid({k: opads_raw[k] for k in common})
            _jca = centroid({k: jraw[k] for k in common})
            opads = {k: [(x - _oca[0], y - _oca[1]) for x, y in v]
                     for k, v in opads_raw.items()}
            jpads_c = {k: [(x - _jca[0], y - _jca[1]) for x, y in v]
                       for k, v in jraw.items()}
            # FOOTPRINT-LOCAL centroid: model offsets are relative to the
            # footprint origin, not the board (absolute coords put every
            # model ~60mm off its part - found 2026-07-16)
            oc = (_oca[0] - fp.GetPosition().x / 1e6,
                  _oca[1] - fp.GetPosition().y / 1e6)
            if not self_checked:
                self_checked = True
                sc = model_self_check(jfp, _jca)
                if sc and min(abs(sc[0]), abs(sc[1])) > 0.4:
                    findings.append((lcsc, ref, "MODEL-SELF",
                                     f"JLC model bbox center off JLC's OWN "
                                     f"pads by ({sc[0]:+.2f},{sc[1]:+.2f})mm "
                                     "in their frame - model-internal "
                                     "defect; expect the render to need an "
                                     "adjudicated board_dx/board_dy nudge, "
                                     "and distrust bbox MODEL-REG numbers "
                                     "for this part"))
            fits = best_fit(opads, jpads_c)
            good = [f for f in fits if f[0] <= FIT_TOL]
            if not good:
                findings.append((lcsc, ref, "PAD-MISMATCH",
                                 f"best={fits[0] if fits else 'none'}"))
                criticals.append(ref)
                # MOUNT AT JLC'S OWN FOOTPRINT TRANSFORM, NEVER AT THE FIT
                # THAT JUST FAILED (2026-07-26). This used to mount at the
                # best NON-mirrored fit — the same fit the line above declares
                # unusable — and then print "VERIFY leads sit on pads
                # visually", pointing the reviewer at a picture that failed
                # fit had corrupted. MEASURED on crow-recorder-central-v2 v1.5:
                # J2 (USB-C C3020560) reported PAD-MISMATCH best=(4.5947,
                # False, 90) and PAD-GEOM pad 1<->2 ours 0.80mm vs JLC 8.64mm,
                # and the body rendered ROTATED 90 DEGREES — 7.555 x 8.940 mm
                # where the part is 8.940 x 7.555 — into two sealed releases.
                # A residual of 4.59 mm is not a correspondence; the only
                # transform still supported by evidence is the one JLC ships
                # with the part, which this tool already reads and already
                # calls "authoritative" in its own MODEL-REG hint. So: offset
                # 0, JLC's own model rot_z, anchored by mapping JLC's
                # common-pad centroid onto ours.
                twin[ref] = (jfp, 0, oc, _jca, lcsc)
                mount_fallback.add(ref)
                if fits:
                    why = (f"best {fits[0][0]:.2f}mm at {fits[0][2]}deg"
                           f"{'/mirrored' if fits[0][1] else ''}, over "
                           f"{FIT_TOL}mm")
                else:
                    why = "no pad correspondence at any angle"
                findings.append((lcsc, ref, "MOUNT-FALLBACK",
                                 f"{why} — body mounted at JLC's OWN footprint "
                                 f"transform (offset 0, their model rot_z), "
                                 f"NOT at the failed fit. The render is "
                                 f"therefore what JLC's own CAD says, and is "
                                 f"gated as such by twin_overlay"))
                continue
            e, mir, ang = good[0]
            if mir:
                nonmir = [f for f in fits if not f[1]]
                if not nonmir or nonmir[0][0] - e > MIRROR_MARGIN:
                    findings.append((lcsc, ref, "MIRRORED",
                                     f"mirror fit {e:.2f}mm vs non-mirror "
                                     f"{nonmir[0][0]:.2f}mm" if nonmir else
                                     f"mirror-only fit {e:.2f}mm"))
                    criticals.append(ref)
                    continue
                e, mir, ang = nonmir[0]
            # rotation-db audit: fitted ang is the JLC CPL offset
            fpname = str(fp.GetFPID().GetLibItemName())
            # 2-pad polarized parts: the pad-number fit orients the MOUNT,
            # but a 180-flipped MODEL (wrong internal orientation vs JLC's
            # own footprint - the XT60 class) is invisible to both the fit
            # and MODEL-REG when the body bbox is symmetric. The polarity
            # marking in the render is the only signal: check it by eye
            # against our silk, and the CPL rotation in the JLC preview.
            if (len(common) == 2
                    and any(fpname.startswith(p) or f"_{p}" in fpname
                            for p in POLARIZED_FP)):
                findings.append((lcsc, ref, "POLARITY-CHECK",
                                 "2-pad polarized part: verify the model's "
                                 "polarity marking vs our silk in the render "
                                 "(if the model is unmarked, verify via the "
                                 "JLC order preview) - machine checks cannot "
                                 "see a 180-flipped symmetric model"))
                # POLARITY-FIT (2026-07-25, BLOCKING, own adjudication key).
                # The pad-NUMBER fit above cannot see a polarity swap: for a
                # 2-pad collinear part the pads are symmetric, so a library
                # that numbers the CATHODE "2" where we number it "1" fits
                # perfectly at 180 and ships the part REVERSED. This compares
                # the numbering-free MARKING channel instead.
                # MEASURED on C2296/C2297 (KT-0805 LEDs) 2026-07-25: the
                # pad-number fit says 180 at 0.1125mm residual with the next
                # candidate 1.9875mm away (17.7x margin) — confidently and
                # precisely WRONG. JLC numbers pad 1 = ANODE (their F.SilkS
                # diode glyph points its apex WEST, and the silk body is
                # chamfered WEST — two independent channels agreeing), while
                # KiCad's Device:LED symbol is pin1=K/pin2=A and
                # LED_0805_2012Metric chamfers its F.Fab at pin 1. Both draw
                # the cathode at the WEST end, so the PHYSICAL parts already
                # align: the correct CPL offset is 0, not 180.
                ours_mark = ours_mark_local
                jlc_mark = marker_side(jfp, jraw)
                if ours_mark and jlc_mark:
                    if ours_mark[0] != jlc_mark[0]:
                        findings.append((lcsc, ref, "POLARITY-FIT",
                            f"the pad-number fit says offset {ang}, but the "
                            f"MARKING channel disagrees by 180deg: our "
                            f"polarity marking sits at pad {ours_mark[0]} "
                            f"(margin {ours_mark[1]:.2f}mm) while JLC's sits "
                            f"at pad {jlc_mark[0]} (margin {jlc_mark[1]:.2f}mm)"
                            f" — the two libraries NUMBER this part's "
                            f"terminals oppositely, so the pad fit is 180deg "
                            f"wrong PHYSICALLY and offset "
                            f"{(ang + 180) % 360} is what places the part "
                            f"correctly. A pad fit cannot see this: 2 "
                            f"collinear pads are symmetric. RESOLVE against "
                            f"the DATASHEET terminal drawing, put this LCSC "
                            f"on the order-preview human gate, and never let "
                            f"the fitted angle populate the rotation table "
                            f"unchallenged"))
                        criticals.append(ref)
                    else:
                        findings.append((lcsc, ref, "POLARITY-FIT-OK",
                            f"marking channel agrees with the pad fit "
                            f"(both at pad {ours_mark[0]}; margins "
                            f"{ours_mark[1]:.2f}/{jlc_mark[1]:.2f}mm)"))
                else:
                    findings.append((lcsc, ref, "POLARITY-FIT-BLIND",
                        "no usable polarity marking on "
                        + ("our" if not ours_mark else "JLC's")
                        + " footprint — the numbering-free channel cannot "
                          "run, so ONLY the human order-preview gate stands "
                          "between this part and a 180deg reversal"))
            # The exporter resolves per-LCSC FIRST (jlc_lcsc_rotations.csv),
            # then the footprint-name DB — mirror that here so the audit
            # compares the fitted angle against the SAME offset the CPL will
            # actually use. A per-LCSC override wins because JLC's zero-
            # orientation is a per-part fact (two parts sharing a footprint
            # NAME can need different offsets: C79924 vs C7719, both SOT-23-5).
            if lcsc in lcsc_rot:
                db_off, src = lcsc_rot[lcsc], "lcsc"
            else:
                db_off = next((off for _, pat, off in db if pat.search(fpname)), 0.0)
                src = "name-DB"
            status = "OK" if (ang - db_off) % 360 == 0 else "ROT-DB-SUGGEST"
            # Recommend the per-LCSC table (the name key is exactly the bug):
            # a name-DB row would mis-set every OTHER part sharing this name.
            hint = (f" -> add LCSC row {lcsc},{ang} to jlc_lcsc_rotations.csv"
                    if status != "OK" else "")
            findings.append((lcsc, ref, status,
                             f"fit={e:.2f}mm jlc_offset={ang} db={db_off} src={src}"
                             + hint))
            # ROT-DB-SUGGEST stays NON-blocking, but NOT for the reason the
            # comment here used to give. That comment said the block was
            # "pending the xform() handedness fix" — which had ALREADY landed
            # in 1b69760 when it was written, so it read as a live caveat
            # while defending nothing. `ang` is now measured with the
            # pcbnew-verified operator. What still holds is canon A-ROT: the
            # per-LCSC table was POPULATED from this finding, so promoting the
            # finding to blocking would let the table certify itself (canon
            # M1). It lands when the table is re-derived independently.
            twin[ref] = (jfp, ang, oc, _jca, lcsc)

    # ---- twin render: JLC models mounted on OUR board
    if twin or local_bodies:
        tb = pcbnew.LoadBoard(args.board)
        findings.extend(install_declared_twin_bodies(
            tb, local_bodies, args.assembly, args.board))
        mrotz = {}
        for ref, (jfp, ang, oc, jc_common, lcsc) in twin.items():
            if lcsc in model_rot_override:
                mrotz[ref] = model_rot_override[lcsc]
        for ref, (jfp, ang, oc, jc_common, lcsc) in twin.items():
            # adjudicated per-part mount nudge - evidence-backed, for parts
            # whose model mis-seats in the render. board_dx/board_dy are
            # converted per-ref through the part rotation; model_dx/dy are
            # raw footprint-local. Every applied nudge is echoed in BOTH
            # frames so intent vs applied is auditable in the log.
            fp = tb.FindFootprintByReference(ref)
            dx, dy = model_xy_override.get(lcsc, (0.0, 0.0))
            if fp and lcsc in board_xy_override:
                bdx, bdy = board_xy_override[lcsc]
                cdx, cdy = board_to_local(bdx, bdy, fp.GetOrientationDegrees())
                dx, dy = dx + cdx, dy + cdy
            if fp and (dx or dy):
                ebx, eby = local_to_board(dx, dy, fp.GetOrientationDegrees())
                print(f"NUDGE {ref} ({lcsc}): local({dx:+.2f},{dy:+.2f})mm "
                      f"-> board({ebx:+.2f},{eby:+.2f})mm east+/south+ "
                      f"[rot {fp.GetOrientationDegrees():.0f}]")
            oc = (oc[0] + dx, oc[1] + dy)
            jmodels = list(jfp.Models())
            if not fp or not jmodels:
                continue
            jc = jc_common  # common-pad centroid captured at fit time
            # --- model-registration invariant: mounted body bbox must sit on
            # OUR courtyard (catches flipped/shifted/wrong JLC models AND our
            # own mount bugs - an XT60 WRL was 180deg-flipped vs JLC's own
            # footprint, rendering flush instead of 9mm overhung, 2026-07-16)
            mb = wrl_bbox(jmodels[0].m_Filename)
            if mb:
                jm0 = jmodels[0]
                saved = jm0.m_Rotation.z
                jm0.m_Rotation.z = (saved + mrotz.get(ref, 0.0)) % 360
                rc = reg_check(mb, jm0, ang, jc, oc, fp)
                if rc and rc[0] > 1.0:
                    # JLC's OWN footprint model rotation is authoritative: the
                    # twin already mounts at it. bbox-center-vs-courtyard is
                    # UNRELIABLE for asymmetric bodies (connectors with a
                    # mouth) - measure how far the model bbox center sits from
                    # the model origin; a big asymmetry means this metric, and
                    # the "a flip fixes it" arithmetic, are both suspect.
                    jlc_rot = saved                      # from JLC's .kicad_mod
                    asym = math.hypot((mb[0] + mb[2]) / 2, (mb[1] + mb[3]) / 2)
                    jm0.m_Rotation.z = (jm0.m_Rotation.z + 180) % 360
                    rc2 = reg_check(mb, jm0, ang, jc, oc, fp)
                    flip_helps = rc2 and rc2[0] < 1.0
                    # NEVER auto-suggest a rotation that DEVIATES from JLC's
                    # own spec - a USB-C false alarm got a wrong model_rot_z
                    # twice because the old hint chased the metric (2026-07-17,
                    # same red herring as the Q1 DPAK). Only hint a flip when
                    # the body is near-symmetric AND no override is active
                    # (i.e. our WRL genuinely disagrees with JLC's footprint).
                    if flip_helps and asym < 0.5 and ref not in mrotz:
                        hint = (" -> possible 180-flipped WRL vs JLC footprint; "
                                "VERIFY leads-on-pads in the render, then "
                                "{lcsc: %s, model_rot_z: 180}" % lcsc)
                    else:
                        hint = (f" -> DO NOT blind-flip: JLC's footprint mounts "
                                f"this model at rot_z={jlc_rot:.0f} (authoritative); "
                                f"body asymmetric ({asym:.1f}mm bbox-center offset) "
                                f"so this metric is unreliable. VERIFY leads sit "
                                f"on pads visually; if correct, adjudicate as a "
                                f"false alarm with NO rotation override")
                    pg = padgeom.get(ref, 0.0)
                    pgnote = (f", incl. pad_geom_delta={pg:.2f}mm"
                              if pg > 0.1 else "")
                    if ref in mount_fallback:
                        # Say which mount the picture actually shows. "VERIFY
                        # leads sit on pads visually" is an instruction a
                        # reviewer cannot carry out when the pad
                        # correspondence is the thing that failed.
                        hint += (" [MOUNT-FALLBACK: no pad correspondence "
                                 "exists, so this body is at JLC's OWN "
                                 "transform and the leads CANNOT be expected "
                                 "to sit on our pads — the render answers "
                                 "'what does JLC's CAD look like on our "
                                 "board', not 'do the leads land'. Settle the "
                                 "land pattern against the datasheet; the "
                                 "picture cannot]")
                    findings.append((lcsc, ref, "MODEL-REG",
                                     f"body center {rc[0]:.1f}mm off courtyard, "
                                     f"area ratio {rc[1]:.2f}{pgnote}{hint}"))
                    # BLOCKING since 2026-07-25. MODEL-REG was emitted here and
                    # never appended to `criticals`, so it could not fail a run:
                    # usb-hub-3s-v3 v1.5 sealed with a TRUE 14.3 mm finding on
                    # J1 sitting beside a green verdict, waived by prose. A
                    # finding that cannot block is a comment.
                    criticals.append(ref)
                elif rc:
                    findings.append((lcsc, ref, "MODEL-REG-OK",
                                     f"body on courtyard ({rc[0]:.2f}mm)"))
                jm0.m_Rotation.z = saved
            fp.Models().clear()
            for jm in jmodels:
                m = pcbnew.FP_3DMODEL()
                m.m_Filename = jm.m_Filename
                m.m_Scale = jm.m_Scale
                m.m_Rotation = jm.m_Rotation
                # frames: our footprint = JLC footprint rotated by `ang` (the
                # pad-fit angle, board y-down convention) with JLC's pad
                # centroid mapped onto ours. Model offsets are y-UP mm.
                #
                # HANDEDNESS FIXED 2026-07-25. The OFFSET and the Z-ROTATION
                # are one operator and were fixed as ONE change; each is
                # meaningless alone, which is exactly what the deleted comment
                # here had observed and then mis-attributed. The offset was a
                # fourth hand-inlined copy of the mirrored form and now goes
                # through xform(); the z sign follows from it by composition,
                # not by taste:
                #   JLC mounts the body at pose formA(-jm.m_Rotation.z) in the
                #   board frame (see model_rot); our footprint is JLC's turned
                #   by formA(+ang); so the mounted pose must be
                #   formA(ang - jm.m_Rotation.z), and KiCad renders rotation R
                #   as formA(-R), hence R = jm.m_Rotation.z - ang.
                # ACCEPTANCE, measured on this board: J1 (XT60, fit offset 270)
                # renders 6.35 mm overhung past the west edge, matching its
                # F.Fab outline. The pre-fix build rendered it -8.37 mm, i.e.
                # 14.47 mm east of its own pads, and a MODEL-REG finding that
                # correctly reported 14.3 mm was waived as a false alarm.
                mjx, mjy = jm.m_Offset.x, -jm.m_Offset.y        # -> board frame
                bx, by = xform({"p": [(mjx - jc[0], mjy - jc[1])]},
                               ang, False)["p"][0]
                m.m_Offset.x = bx + oc[0]
                m.m_Offset.y = -(by + oc[1])                    # -> back to y-up
                m.m_Offset.z = jm.m_Offset.z
                m.m_Rotation.z = (jm.m_Rotation.z - ang
                                  + mrotz.get(ref, 0.0)) % 360
                fp.Models().push_back(m)

        # ---- NO-BODY: the terminal, fit-independent population gate
        cpl_refs = []
        if args.cpl and os.path.exists(args.cpl):
            with open(args.cpl, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    d = (row.get("Designator") or "").strip()
                    if d:
                        cpl_refs.append(d)
            placed_count = len(cpl_refs)
            cpl_refs = sorted(set(cpl_refs) | set(local_bodies))
            src_desc = (f"{placed_count} CPL placements ({args.cpl}) + "
                        f"{len(local_bodies)} declared manual-install bodies "
                        f"({args.assembly})")
        else:
            cpl_refs = sorted({d.strip() for r in lines
                               for d in r["Designator"].split(",")
                               if d.strip() in by_ref} | set(local_bodies))
            src_desc = (f"{len(cpl_refs)} checked/manual refs (no --cpl given; pass "
                        f"fab/cpl.csv for the population denominator)")
        mounted, missing = no_body_pass(tb, cpl_refs, args.board)
        bodies_line = f"bodies mounted: {len(mounted)}/{len(cpl_refs)}"
        for ref, why in missing:
            findings.append((ref_lcsc.get(ref, ""), ref, "NO-BODY", why))
            criticals.append(ref)
        # missing_models.txt is GENERATED from this pass, never hand-authored.
        # v1.5's copy was written by hand and said the gap was zero while
        # seven placements rendered no body — a counter nobody could falsify.
        with open(out / "missing_models.txt", "w") as f:
            f.write("# GENERATED by jlc_twin.py NO-BODY pass — do not edit.\n"
                    f"# source of the population set: {src_desc}\n"
                    f"# {bodies_line}\n")
            if not missing:
                f.write("\n(none — every CPL designator resolves a 3D body)\n")
            for ref, why in missing:
                f.write(f"{ref}\t{ref_lcsc.get(ref, '')}\t{why}\n")
        print(f"\n{bodies_line}  ->  {out / 'missing_models.txt'}")

        tb.Save(str(out / "twin.kicad_pcb"))
        # A-RENDER's independent pixel channel needs the SAME board, camera,
        # lighting and resolution with one controlled difference: no component
        # models. Comparing the populated render to a separately exported SVG
        # is not valid because its projection and renderer differ. Keep this
        # board beside the twin as reproducible evidence; it is generated from
        # a fresh load so clearing models cannot mutate the populated twin.
        bare = pcbnew.LoadBoard(str(out / "twin.kicad_pcb"))
        for fp in bare.GetFootprints():
            fp.Models().clear()
        bare.Save(str(out / "twin_bare.kicad_pcb"))
        VIEWS = [  # (name, extra kicad-cli render args)
            ("top",      ["--side", "top"]),
            ("bottom",   ["--side", "bottom"]),
            ("iso_nw",   ["--side", "top", "--rotate", "-40,0,35",
                          "--perspective", "--zoom", "0.85"]),
            ("iso_se",   ["--side", "top", "--rotate", "-40,0,215",
                          "--perspective", "--zoom", "0.85"]),
            ("edge_west", ["--side", "left", "--perspective", "--zoom", "0.9"]),
            ("edge_east", ["--side", "right", "--perspective", "--zoom", "0.9"]),
        ]
        for name, extra in ([] if args.no_render else VIEWS):
            subprocess.run(["kicad-cli", "pcb", "render",
                            "--width", "1600", "--height", "1000",
                            "-o", str(out / f"twin_{name}.png"),
                           *extra, str(out / "twin.kicad_pcb")],
                           capture_output=True)
        if not args.no_render:
            for side in ("top", "bottom"):
                subprocess.run(["kicad-cli", "pcb", "render",
                                "--width", "1600", "--height", "1000",
                                "-o", str(out / f"twin_bare_{side}.png"),
                                "--side", side,
                                str(out / "twin_bare.kicad_pcb")],
                               capture_output=True)

    with open(out / "twin_report.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LCSC", "Ref", "Status", "Detail"])
        w.writerows(findings)
    # apply the adjudication register: reviewed findings become non-fatal
    out_f = []
    for lcsc, ref, status, detail in findings:
        why = adjudicate(lcsc, ref, status)
        # backward compat: before FETCH-FAILED existed, every unfetched part was
        # recorded as NO-CAD, so existing registers adjudicate it under that name.
        # Honour those entries (they carry the datasheet-verified land pattern).
        if not why and status == "FETCH-FAILED":
            why = adjudicate(lcsc, ref, "NO-CAD")
        # NO-BODY and MODEL-REG carry their OWN adjudication keys. This is
        # load-bearing: `adjudicate()` matches on the status STRING, so a
        # PAD-MISMATCH or FETCH-FAILED waiver can no longer discharge the
        # question "did a body actually render?". One waiver used to close
        # two unrelated obligations — the land-pattern question and the
        # never-stated visual-verification question (v1.5, 7 refs).
        if why and status in ("MIRRORED", "PAD-MISMATCH", "PAD-GEOM",
                              "NO-CAD", "FETCH-FAILED", "NO-BODY",
                              "MODEL-REG", "POLARITY-FIT"):
            for r in str(ref).split(","):
                if r.strip() in criticals:
                    criticals.remove(r.strip())
            out_f.append((lcsc, ref, f"ADJUDICATED-{status}", why))
        else:
            out_f.append((lcsc, ref, status, detail))
    findings = out_f
    order = {"FETCH-FAILED": -1, "NO-BODY": -1, "MIRRORED": 0,
             "PAD-MISMATCH": 1, "PAD-GEOM": 2, "MODEL-SELF": 3,
             "MODEL-REG": 3, "POLARITY-FIT": 1, "MOUNT-FALLBACK": 1,
             "PAD-MULTIPLICITY": 4,
             "POLARITY-CHECK": 4, "POLARITY-FIT-BLIND": 4,
             "POLARITY-FIT-OK": 8,
             "ROT-DB-SUGGEST": 5, "NO-CAD": 6,
             "NOT-ON-BOARD": 7, "MODEL-REG-OK": 8, "OK": 9}
    for f in sorted(findings, key=lambda x: order.get(x[2], 9)):
        print("  ".join(str(x) for x in f))
    n_ok = sum(1 for f in findings if f[2] == "OK")
    # COVERAGE, not check count. The release line "0 ROT-DB-SUGGEST over 231
    # checks" quoted the number of finding ROWS and read as blanket assurance;
    # the real coverage was 101 of 108 placements, and the 7 uncovered were
    # exactly the ones at CPL 90/270 (usb-hub-3s-v3 v1.5). Always print the
    # denominator that is a POPULATION.
    n_fit = len({f[1] for f in findings
                 if f[2] in ("OK", "ROT-DB-SUGGEST")})
    print(f"\n{n_ok} OK / {len(findings)} finding rows; "
          f"rotation-fitted refs: {n_fit}")
    print(bodies_line)
    print(f"report + renders -> {out}")
    if fetch_failed:
        print(f"\nTRANSIENT FETCH FAILURES ({len(fetch_failed)}): {sorted(fetch_failed)}")
        print("  These are NETWORK/API errors, NOT 'no CAD' — these parts were never checked,")
        print("  so this run does NOT constitute twin verification for them.")
        print("  The per-code cache keeps everything already fetched, so simply RE-RUNNING")
        print("  retries ONLY the failed codes (a partial re-run):")
        print("    " + " ".join(sys.argv))
        print("  If the API is flaky, be more patient:")
        print("    JLC_TWIN_FETCH_ATTEMPTS=8 " + " ".join(sys.argv))
        print("  Only adjudicate FETCH-FAILED if the part is genuinely absent from the")
        print("  library (verify the land pattern against the datasheet + flag order-time preview).")
    if criticals:
        print(f"CRITICAL ({len(set(criticals))} refs): {sorted(set(criticals))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
