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

usage: jlc_twin.py board.kicad_pcb bom_jlc.csv outdir
Exit 1 on any MIRRORED, PAD-MISMATCH, or PAD-GEOM finding.

Checks beyond the fit itself:
  - PAD-GEOM: pairwise pad-center distances (rotation/translation-invariant,
    so no best-fit can smear them) must agree between our footprint and
    JLC's within PAD_GEOM_TOL. A disagreement means the two land patterns
    differ dimensionally - the model WILL render off our pads by part of
    that delta, and someone must decide which pattern matches the part
    datasheet (adjudicate with evidence). Found via a DPAK whose tab-to-lead
    distance differed 0.65mm; the fit split it into an unexplained 0.43mm
    residual (2026-07-16).
  - POLARITY-CHECK: 2-pad polarized parts (electrolytics, diodes, LEDs)
    where 0 and 180 fit the pads equally - the pad fit cannot orient the
    model, so its polarity marking in the render is unverified and must be
    checked against our silk + the JLC order preview.
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


def pads_of(fp):
    d = {}
    for p in fp.Pads():
        n = str(p.GetNumber())
        if n:
            d.setdefault(n, []).append((p.GetPosition().x / 1e6,
                                        p.GetPosition().y / 1e6))
    return d


def centroid(d):
    xs = [x for v in d.values() for x, _ in v]
    ys = [y for v in d.values() for _, y in v]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def centered(d):
    cx, cy = centroid(d)
    return {k: [(x - cx, y - cy) for x, y in v] for k, v in d.items()}


def xform(d, ang, mir):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    out = {}
    for k, v in d.items():
        pts = [(-x if mir else x, y) for x, y in v]
        out[k] = sorted((round(x * c - y * s, 3), round(x * s + y * c, 3))
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


def fit_err(a, b):
    common = set(a) & set(b)
    if not common:
        return None
    errs = []
    for k in common:
        if len(a[k]) != len(b[k]):
            return None
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
    mrot = math.radians(jm.m_Rotation.z)
    cm, sm = math.cos(mrot), math.sin(mrot)
    xs, ys = [], []
    for mx in (mb[0], mb[2]):
        for my in (mb[1], mb[3]):
            rx = mx * cm - my * sm
            ry = mx * sm + my * cm
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
    # model frame (y-up) -> JLC footprint frame (y-down), incl. entry offset/rot
    mrot = math.radians(jm.m_Rotation.z)
    cm, sm = math.cos(mrot), math.sin(mrot)
    corners = []
    for mx in (model_bbox[0], model_bbox[2]):
        for my in (model_bbox[1], model_bbox[3]):
            rx = mx * cm - my * sm            # R(+theta) y-up CCW - the sense
            ry = mx * sm + my * cm            # KiCad actually renders (verified)
            jx = rx * jm.m_Scale.x + jm.m_Offset.x
            jy = -(ry * jm.m_Scale.y + jm.m_Offset.y)   # to y-down
            # JLC frame -> our footprint local frame (fit transform)
            c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            lx = (jx - jc[0]) * c - (jy - jc[1]) * sn + oc[0]
            ly = (jx - jc[0]) * sn + (jy - jc[1]) * c + oc[1]
            # our local -> board (KiCad footprint rotation th: (x,y)->R(-th))
            th = math.radians(rot)
            bx = lx * math.cos(th) + ly * math.sin(th) + fpos.x / 1e6
            by = -lx * math.sin(th) + ly * math.cos(th) + fpos.y / 1e6
            corners.append((bx, by))
    mnx = min(c[0] for c in corners); mxx = max(c[0] for c in corners)
    mny = min(c[1] for c in corners); mxy = max(c[1] for c in corners)
    mcx, mcy = (mnx + mxx) / 2, (mny + mxy) / 2
    ccx, ccy = cb.Centre().x / 1e6, cb.Centre().y / 1e6
    delta = math.hypot(mcx - ccx, mcy - ccy)
    area_m = max(1e-6, (mxx - mnx) * (mxy - mny))
    area_c = max(1e-6, cb.GetWidth() / 1e6 * cb.GetHeight() / 1e6)
    return delta, area_m / area_c, (ccx, ccy)


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
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--adjudications", default="",
                    help="YAML list of reviewed findings to accept: "
                         "[{lcsc, refs: [..], status, why}]")
    ap.add_argument("--also", default="",
                    help="REF=LCSC[,REF=LCSC..]: mount+check hand-solder/"
                         "uncoded parts with known codes (e.g. J1=C98732)")
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

    lines = [r for r in csv.DictReader(open(args.bom)) if r.get("LCSC")]
    for pair in [p for p in args.also.split(",") if p.strip()]:
        ref, _, code = pair.partition("=")
        if not code:
            sys.exit(f"--also expects REF=LCSC, got: {pair}")
        lines.append({"Designator": ref.strip(), "LCSC": code.strip()})
    findings, criticals, twin, padgeom = [], [], {}, {}
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
            fp.SetOrientationDegrees(rot)
            # center BOTH sets on the COMMON numbered pads only: centering
            # each on its own full set biases the fit/mount whenever one side
            # names extra pads (XT60 pegs, FET drain fingers) - the XT60 model
            # rendered 7mm off its holes before this (2026-07-16)
            jraw = pads_of(jfp)
            for src, dst in pad_alias.get(lcsc, {}).items():
                if src in jraw:
                    jraw.setdefault(dst, []).extend(jraw.pop(src))
                    jraw[dst] = sorted(jraw[dst])
            common = set(opads_raw) & set(jraw)
            if not common:
                findings.append((lcsc, ref, "PAD-MISMATCH", "no common pad numbers"))
                criticals.append(ref)
                continue
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
                # still mount the model at the best NON-mirrored fit: the
                # render is exactly where a human adjudicates these
                nm = [x for x in fits if not x[1]]
                if nm:
                    twin[ref] = (jfp, nm[0][2], oc, _jca, lcsc)
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
            db_off = next((off for _, pat, off in db if pat.search(fpname)), 0.0)
            status = "OK" if (ang - db_off) % 360 == 0 else "ROT-DB-SUGGEST"
            findings.append((lcsc, ref, status,
                             f"fit={e:.2f}mm jlc_offset={ang} db={db_off}"
                             + (f" -> add: {fpname},{ang}" if status != "OK" else "")))
            twin[ref] = (jfp, ang, oc, _jca, lcsc)

    # ---- twin render: JLC models mounted on OUR board
    if not args.no_render and twin:
        tb = pcbnew.LoadBoard(args.board)
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
                    findings.append((lcsc, ref, "MODEL-REG",
                                     f"body center {rc[0]:.1f}mm off courtyard, "
                                     f"area ratio {rc[1]:.2f}{pgnote}{hint}"))
                elif rc:
                    findings.append((lcsc, ref, "MODEL-REG-OK",
                                     f"body on courtyard ({rc[0]:.2f}mm)"))
                jm0.m_Rotation.z = saved
            fp.Models().clear()
            c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            for jm in jmodels:
                m = pcbnew.FP_3DMODEL()
                m.m_Filename = jm.m_Filename
                m.m_Scale = jm.m_Scale
                m.m_Rotation = jm.m_Rotation
                # frames: our footprint = JLC footprint rotated by `ang` (the
                # pad-fit angle, board y-down convention) with JLC's pad
                # centroid mapped onto ours. Model offsets are y-UP mm.
                mjx, mjy = jm.m_Offset.x, -jm.m_Offset.y        # -> board frame
                bx = (mjx - jc[0]) * c - (mjy - jc[1]) * sn + oc[0]
                by = (mjx - jc[0]) * sn + (mjy - jc[1]) * c + oc[1]
                m.m_Offset.x = bx
                m.m_Offset.y = -by                              # -> back to y-up
                m.m_Offset.z = jm.m_Offset.z
                # z-rotation is +ang, NOT -ang: verified by pixel-measuring the
                # rendered XT60 against both courtyards (-ang flipped the body
                # 180deg: flush with the edge instead of 9mm overhung). The
                # per-part adjudication override composes on top.
                m.m_Rotation.z = (jm.m_Rotation.z + ang
                                  + mrotz.get(ref, 0.0)) % 360
                fp.Models().push_back(m)
        tb.Save(str(out / "twin.kicad_pcb"))
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
        for name, extra in VIEWS:
            subprocess.run(["kicad-cli", "pcb", "render",
                            "--width", "1600", "--height", "1000",
                            "-o", str(out / f"twin_{name}.png"),
                            *extra, str(out / "twin.kicad_pcb")],
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
        if why and status in ("MIRRORED", "PAD-MISMATCH", "PAD-GEOM", "NO-CAD", "FETCH-FAILED"):
            for r in str(ref).split(","):
                if r.strip() in criticals:
                    criticals.remove(r.strip())
            out_f.append((lcsc, ref, f"ADJUDICATED-{status}", why))
        else:
            out_f.append((lcsc, ref, status, detail))
    findings = out_f
    order = {"FETCH-FAILED": -1, "MIRRORED": 0, "PAD-MISMATCH": 1, "PAD-GEOM": 2, "MODEL-SELF": 3, "MODEL-REG": 3,
             "POLARITY-CHECK": 4, "ROT-DB-SUGGEST": 5, "NO-CAD": 6,
             "NOT-ON-BOARD": 7, "MODEL-REG-OK": 8, "OK": 9}
    for f in sorted(findings, key=lambda x: order.get(x[2], 9)):
        print("  ".join(str(x) for x in f))
    n_ok = sum(1 for f in findings if f[2] == "OK")
    print(f"\n{n_ok} OK / {len(findings)} checked; report + renders -> {out}")
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
