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
Exit 1 on any MIRRORED or PAD-MISMATCH finding.

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
    args = ap.parse_args()
    adjudicated = []
    if args.adjudications and os.path.exists(args.adjudications):
        import yaml
        adjudicated = yaml.safe_load(open(args.adjudications)) or []

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
    findings, criticals, twin = [], [], {}
    for r in lines:
        lcsc = r["LCSC"]
        fp_path, err = fetch(lcsc, out / "easyeda")
        if err:
            findings.append((lcsc, r["Designator"], "NO-CAD", str(err)))
            continue
        jfp = pcbnew.FootprintLoad(str(Path(fp_path).parent),
                                   Path(fp_path).stem)
        jpads = centered(pads_of(jfp))
        for ref in [d.strip() for d in r["Designator"].split(",")]:
            fp = by_ref.get(ref)
            if fp is None:
                findings.append((lcsc, ref, "NOT-ON-BOARD", ""))
                continue
            # compare in the footprint's own frame (undo board rotation)
            rot = fp.GetOrientationDegrees()
            fp.SetOrientationDegrees(0)
            opads = centered(pads_of(fp))
            oc = centroid(pads_of(fp))
            fp.SetOrientationDegrees(rot)
            fits = best_fit(opads, jpads)
            good = [f for f in fits if f[0] <= FIT_TOL]
            if not good:
                findings.append((lcsc, ref, "PAD-MISMATCH",
                                 f"best={fits[0] if fits else 'none'}"))
                criticals.append(ref)
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
            db_off = next((off for _, pat, off in db if pat.search(fpname)), 0.0)
            status = "OK" if (ang - db_off) % 360 == 0 else "ROT-DB-SUGGEST"
            findings.append((lcsc, ref, status,
                             f"fit={e:.2f}mm jlc_offset={ang} db={db_off}"
                             + (f" -> add: {fpname},{ang}" if status != "OK" else "")))
            twin[ref] = (jfp, ang, oc)

    # ---- twin render: JLC models mounted on OUR board
    if not args.no_render and twin:
        tb = pcbnew.LoadBoard(args.board)
        for ref, (jfp, ang, oc) in twin.items():
            fp = tb.FindFootprintByReference(ref)
            jmodels = list(jfp.Models())
            if not fp or not jmodels:
                continue
            jc = centroid(pads_of(jfp))
            fp.Models().clear()
            for jm in jmodels:
                m = pcbnew.FP_3DMODEL()
                m.m_Filename = jm.m_Filename
                m.m_Scale = jm.m_Scale
                m.m_Rotation = jm.m_Rotation
                m.m_Rotation.z = (jm.m_Rotation.z - ang) % 360
                c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                ox, oy = jm.m_Offset.x, jm.m_Offset.y
                dx, dy = oc[0] - (jc[0] * c - jc[1] * s), oc[1] - (jc[0] * s + jc[1] * c)
                m.m_Offset.x = ox * c - oy * s + dx
                m.m_Offset.y = ox * s + oy * c - dy  # model y is up-positive
                m.m_Offset.z = jm.m_Offset.z
                fp.Models().push_back(m)
        tb.Save(str(out / "twin.kicad_pcb"))
        for side in ("top", "bottom"):
            subprocess.run(["kicad-cli", "pcb", "render", "--side", side,
                            "--width", "1600", "--height", "1000",
                            "-o", str(out / f"twin_{side}.png"),
                            str(out / "twin.kicad_pcb")],
                           capture_output=True)

    with open(out / "twin_report.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LCSC", "Ref", "Status", "Detail"])
        w.writerows(findings)
    # apply the adjudication register: reviewed findings become non-fatal
    out_f = []
    for lcsc, ref, status, detail in findings:
        why = adjudicate(lcsc, ref, status)
        if why and status in ("MIRRORED", "PAD-MISMATCH", "NO-CAD"):
            for r in str(ref).split(","):
                if r.strip() in criticals:
                    criticals.remove(r.strip())
            out_f.append((lcsc, ref, f"ADJUDICATED-{status}", why))
        else:
            out_f.append((lcsc, ref, status, detail))
    findings = out_f
    order = {"MIRRORED": 0, "PAD-MISMATCH": 1, "ROT-DB-SUGGEST": 2,
             "NO-CAD": 3, "NOT-ON-BOARD": 4, "OK": 5}
    for f in sorted(findings, key=lambda x: order.get(x[2], 9)):
        print("  ".join(str(x) for x in f))
    n_ok = sum(1 for f in findings if f[2] == "OK")
    print(f"\n{n_ok} OK / {len(findings)} checked; report + renders -> {out}")
    if criticals:
        print(f"CRITICAL ({len(set(criticals))} refs): {sorted(set(criticals))}")
        sys.exit(1)


if __name__ == "__main__":
    main()
