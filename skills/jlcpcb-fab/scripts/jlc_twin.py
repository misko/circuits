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


def fetch(lcsc, cachedir):
    """easyeda2kicad --full into a per-code dir; returns (fp_path, None) or
    (None, reason)."""
    import time
    d = Path(cachedir) / lcsc
    mods = glob.glob(str(d / "jlc.pretty" / "*.kicad_mod"))
    for attempt in range(3):          # EasyEDA rate-limits bursts
        if mods:
            return mods[0], None
        d.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([E2K, "--full", "--lcsc_id", lcsc, "--output",
                            str(d / "jlc.kicad_sym"), "--use-cache"],
                           capture_output=True, text=True)
        mods = glob.glob(str(d / "jlc.pretty" / "*.kicad_mod"))
        if not mods:
            time.sleep(4 * (attempt + 1))
    return None, (r.stderr or r.stdout).strip().splitlines()[-1:] or ["no CAD data"]


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
    for r in lines:
        lcsc = r["LCSC"]
        fp_path, err = fetch(lcsc, out / "easyeda")
        if err:
            findings.append((lcsc, r["Designator"], "NO-CAD", str(err)))
            continue
        jfp = pcbnew.FootprintLoad(str(Path(fp_path).parent),
                                   Path(fp_path).stem)
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
            # adjudicated per-part mount nudge (our footprint-local mm,
            # +x east +y south at rot 0) - evidence-backed, for PAD-GEOM
            # parts whose land-pattern disagreement mis-seats the render
            dx, dy = model_xy_override.get(lcsc, (0.0, 0.0))
            oc = (oc[0] + dx, oc[1] + dy)
            fp = tb.FindFootprintByReference(ref)
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
                    # would a 180 flip fix it? then say so in the finding
                    jm0.m_Rotation.z = (jm0.m_Rotation.z + 180) % 360
                    rc2 = reg_check(mb, jm0, ang, jc, oc, fp)
                    hint = (" -> 180-flipped model: add {lcsc: %s, model_rot_z: 180} "
                            "to the adjudications file" % lcsc
                            if rc2 and rc2[0] < 1.0 else "")
                    # decomposition context: any land-pattern disagreement is
                    # PART of this delta - an adjudication must account for
                    # it separately, not file it under "bbox asymmetry"
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
        if why and status in ("MIRRORED", "PAD-MISMATCH", "PAD-GEOM", "NO-CAD"):
            for r in str(ref).split(","):
                if r.strip() in criticals:
                    criticals.remove(r.strip())
            out_f.append((lcsc, ref, f"ADJUDICATED-{status}", why))
        else:
            out_f.append((lcsc, ref, status, detail))
    findings = out_f
    order = {"MIRRORED": 0, "PAD-MISMATCH": 1, "PAD-GEOM": 2, "MODEL-REG": 3,
             "POLARITY-CHECK": 4, "ROT-DB-SUGGEST": 5, "NO-CAD": 6,
             "NOT-ON-BOARD": 7, "MODEL-REG-OK": 8, "OK": 9}
    for f in sorted(findings, key=lambda x: order.get(x[2], 9)):
        print("  ".join(str(x) for x in f))
    n_ok = sum(1 for f in findings if f[2] == "OK")
    print(f"\n{n_ok} OK / {len(findings)} checked; report + renders -> {out}")
    if criticals:
        print(f"CRITICAL ({len(set(criticals))} refs): {sorted(set(criticals))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
