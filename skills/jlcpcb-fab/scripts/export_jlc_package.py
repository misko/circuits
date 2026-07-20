"""JLC order package: gerbers + drills + BOM + CPL + upload zip.

    /usr/bin/python3 export_jlc_package.py BOARD.kicad_pcb OUTDIR [--layers 4]

Run with the KiCad-bundled interpreter (import pcbnew must work).
Run only AFTER the audit gate and classified DRC pass (kicad-pcb skill).

- The zip contains gerbers + drills + job file ONLY (JLC's PCB uploader);
  bom_jlc.csv / cpl_jlc.csv upload separately in the assembly step.
- Parts whose Value contains "DNP" are excluded from BOM/CPL (still in
  gerbers). Reference prefix H* is skipped as mounting holes.
- LCSC part numbers are carried over from an existing OUTDIR/bom_jlc.csv
  keyed by (Comment, Footprint) so order-time fills survive regeneration.
- Bottom-side CPL coordinates are NOT mirrored (JLC handles that), but
  bottom ROTATIONS are the classic failure — check the assembly preview.
"""
import argparse
import csv
import re
import time
import zipfile
from pathlib import Path

import pcbnew

run_start = time.time()

# JLC library zero-orientation differs from KiCad per package family — the
# community rotation DB (matthewlai/JLCKicadTools + local additions) maps
# footprint-name regex -> CCW offset added to the CPL rotation. Fixes the
# systematic preview/assembly rotation mismatch for SMD parts; the JLC
# preview must STILL be eyeballed (per-part reel deviations exist).
_ROT_DB = []
_db_path = Path(__file__).parent / "jlc_rotations_db.csv"
if _db_path.exists():
    with open(_db_path) as _f:
        for _row in csv.reader(_f):
            if len(_row) >= 2 and not _row[0].startswith("Footprint"):
                try:
                    _ROT_DB.append((re.compile(_row[0]), float(_row[1])))
                except re.error:
                    pass


def jlc_rotation(fpname, rot):
    for pat, off in _ROT_DB:
        if pat.search(fpname):
            return round((rot + off) % 360, 1), off
    return round(rot % 360, 1), 0

ap = argparse.ArgumentParser()
ap.add_argument("board")
ap.add_argument("outdir")
ap.add_argument("--layers", type=int, default=4, choices=(2, 4, 6))
args = ap.parse_args()

board = pcbnew.LoadBoard(args.board)
# ABSOLUTE outdir: PLOT_CONTROLLER resolves relative paths against the BOARD
# file's directory, silently writing gerbers to <board_dir>/<outdir> while the
# zip step (python cwd-relative) sees only drills (found 2026-07-16)
out = Path(args.outdir).resolve()
out.mkdir(parents=True, exist_ok=True)
stem = Path(args.board).stem

pc = pcbnew.PLOT_CONTROLLER(board)
po = pc.GetPlotOptions()
po.SetOutputDirectory(str(out))
po.SetPlotFrameRef(False)
po.SetAutoScale(False)
po.SetMirror(False)
po.SetUseGerberAttributes(True)
po.SetUseGerberProtelExtensions(True)
po.SetCreateGerberJobFile(True)
po.SetSubtractMaskFromSilk(True)
LAYERS = [("F_Cu", pcbnew.F_Cu), ("B_Cu", pcbnew.B_Cu),
          ("F_Silkscreen", pcbnew.F_SilkS), ("B_Silkscreen", pcbnew.B_SilkS),
          ("F_Mask", pcbnew.F_Mask), ("B_Mask", pcbnew.B_Mask),
          ("F_Paste", pcbnew.F_Paste), ("B_Paste", pcbnew.B_Paste),
          ("Edge_Cuts", pcbnew.Edge_Cuts)]
if args.layers >= 4:
    LAYERS[2:2] = [("In1_Cu", pcbnew.In1_Cu), ("In2_Cu", pcbnew.In2_Cu)]
if args.layers >= 6:
    LAYERS[4:4] = [("In3_Cu", pcbnew.In3_Cu), ("In4_Cu", pcbnew.In4_Cu)]
for name, layer in LAYERS:
    pc.SetLayer(layer)
    pc.OpenPlotfile(name, pcbnew.PLOT_FORMAT_GERBER, name)
    pc.PlotLayer()
pc.ClosePlot()

ew = pcbnew.EXCELLON_WRITER(board)
ew.SetOptions(False, False, board.GetDesignSettings().GetAuxOrigin(), False)
ew.SetFormat(True)
ew.CreateDrillandMapFilesSet(str(out), True, False)

old_lcsc = {}
bom_path = out / "bom_jlc.csv"
if bom_path.exists():
    with open(bom_path) as f:
        for row in csv.DictReader(f):
            if row.get("LCSC"):
                # merged lines join dissimilar comments with " / " — seed
                # carry-over for each original comment AND its first token,
                # so every pre-merge value string still resolves
                for part in row["Comment"].split(" / "):
                    old_lcsc.setdefault((part, row["Footprint"]), row["LCSC"])
                    tok = part.split()[0] if part.split() else ""
                    old_lcsc.setdefault((tok, row["Footprint"]), row["LCSC"])


def lcsc_for(val, fpname):
    tok = val.split()[0] if val.split() else ""
    return (old_lcsc.get((val, fpname))
            or old_lcsc.get((tok, fpname), ""))

groups, cpl = {}, []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("H"):
        continue
    val = fp.GetValue()
    if "DNP" in val:
        continue
    if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
        # test points / board-only artifacts: not assembled, not placed
        continue
    fpname = str(fp.GetFPID().GetLibItemName())
    groups.setdefault((val, fpname), []).append(ref)
    pos = fp.GetPosition()
    jrot, off = jlc_rotation(fpname, fp.GetOrientationDegrees())
    if off:
        print(f"  rot-correct {ref}: {fp.GetOrientationDegrees():.0f} "
              f"+ {off:.0f} -> {jrot:.0f} ({fpname[:40]})")
    cpl.append([ref, val, fpname,
                round(pcbnew.ToMM(pos.x), 3), round(-pcbnew.ToMM(pos.y), 3),
                "top" if fp.GetLayer() == pcbnew.F_Cu else "bottom",
                jrot])

# ONE BOM LINE PER PART: JLC's uploader warns "multiple lines matched to
# same part" if two lines carry the same LCSC code — merge value-comment
# groups that resolved to the same (code, footprint). Merged Comment is
# the shared value token ("100n BST" + "100n LDO in" -> "100n").
lines = {}
for (val, fpname), refs in sorted(groups.items()):
    code = lcsc_for(val, fpname)
    key = (code, fpname) if code else ("", val, fpname)
    if key in lines:
        line = lines[key]
        line[1].extend(refs)
        t_old = line[0].split()[0] if line[0].split() else line[0]
        t_new = val.split()[0] if val.split() else val
        line[0] = t_old if t_old == t_new else f"{line[0]} / {val}"
    else:
        lines[key] = [val, list(refs), fpname, code]
# Optional OUTDIR/lcsc_mpn_map.csv (LCSC,MPN): adds an exact manufacturer
# part number column — JLC's matcher auto-selects far more reliably with
# the full MPN (a Comment like "LM5145" left C485912 at "No Part Selected";
# "LM5145RGYR" matches).
mpn_map = {}
mpn_path = out / "lcsc_mpn_map.csv"
if mpn_path.exists():
    with open(mpn_path) as f:
        for row in csv.DictReader(f):
            if row.get("LCSC") and row.get("MPN"):
                mpn_map[row["LCSC"]] = row["MPN"]

with open(bom_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "MPN", "LCSC"])
    for val, refs, fpname, code in sorted(lines.values(), key=lambda x: x[0]):
        w.writerow([val, ",".join(sorted(refs)), fpname,
                    mpn_map.get(code, ""), code])
with open(out / "cpl_jlc.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Layer",
                "Rotation"])
    for row in sorted(cpl):
        w.writerow(row)

# Upload zip: gerbers + drills (+ job file when present) — no BOM/CPL inside.
# Inner-layer Protel extensions are VERSION-DEPENDENT: KiCad 7 wrote
# In1/In2 as .g2/.g3; KiCad 10 writes .g1/.g2 — cover .g1-.g6 for both.
# KiCad 10's PLOT_CONTROLLER also stopped emitting the .gbrjob headlessly;
# JLC does not require it.
# Zip ONLY files this run just wrote (mtime >= run start): re-exporting
# under a different KiCad version leaves stale differently-named inner
# layers behind, and a glob-everything zip silently ships BOTH.
FAB_EXT = {".gtl", ".gbl", ".g1", ".g2", ".g3", ".g4", ".g5", ".g6",
           ".gts", ".gbs", ".gtp", ".gbp", ".gto", ".gbo", ".gm1",
           ".drl", ".gbrjob"}
zip_path = out / f"{stem}_gerbers.zip"
fresh, stale = [], []
for p in sorted(out.iterdir()):
    if p.suffix.lower() in FAB_EXT:
        (fresh if p.stat().st_mtime >= run_start else stale).append(p)
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in fresh:
        z.write(p, p.name)
n_zipped = len(zipfile.ZipFile(zip_path).namelist())
if stale:
    print(f"WARNING: {len(stale)} stale fab files in {out} EXCLUDED from zip "
          f"(old KiCad version leftovers?) — delete them: "
          f"{[p.name for p in stale]}")

uncoded = sum(1 for v in lines.values() if not v[3])
groups = lines
print(f"gerbers: {len(LAYERS)} layers + drills -> {out}")
print(f"zip: {zip_path.name} ({n_zipped} files)")
print(f"BOM: {len(groups)} lines ({uncoded} without LCSC); CPL: {len(cpl)} parts")
if uncoded:
    print(f"NEXT: python3 jlc_stock_check.py {bom_path} --search-missing")
