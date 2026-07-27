# SUPERSEDED: use the jlcpcb-fab skill (export_jlc_package.py) — adds the
# JLC upload zip and KiCad 7/10 inner-layer extension handling. Kept only so
# older references resolve.
"""JLC fab exports: gerbers, PTH/NPTH drills, BOM + CPL.

    /usr/bin/python3 export_fab_jlc.py BOARD.kicad_pcb OUTDIR [--layers 4]

- Parts whose Value contains the substring "DNP" are excluded from BOM/CPL
  (still in gerbers) — a real MPN containing "DNP" would be dropped; adjust
  the test if that ever applies. Reference prefix H* is skipped as mounting
  holes — rename heatsinks/headers if your project uses H* for real parts.
- Bottom-side CPL coordinates are NOT mirrored here; JLC's uploader handles
  bottom parts, but bottom ROTATIONS are the classic CPL failure — verify
  polarized bottom parts against JLC's preview before ordering.
- LCSC part numbers are carried over from an existing OUTDIR/bom_jlc.csv
  keyed by (Comment, Footprint) so order-time fills survive regeneration.
- Run only AFTER your audit gate and classified DRC pass.
- Order-time reminders: verify LCSC stock for every line; JLC's advanced
  (small-via) option is required if the board uses <0.45/0.2 vias;
  spot-check CPL rotations against JLC's conventions for polarized parts.
"""
import argparse
import csv
from pathlib import Path

import pcbnew

ap = argparse.ArgumentParser()
ap.add_argument("board")
ap.add_argument("outdir")
ap.add_argument("--layers", type=int, default=4, choices=(2, 4, 6))
args = ap.parse_args()

board = pcbnew.LoadBoard(args.board)
out = Path(args.outdir)
out.mkdir(parents=True, exist_ok=True)

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
    with open(bom_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("LCSC"):
                old_lcsc[(row["Comment"], row["Footprint"])] = row["LCSC"]

groups, cpl = {}, []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref.startswith("H"):
        continue
    val = fp.GetValue()
    if "DNP" in val:
        continue
    fpname = str(fp.GetFPID().GetLibItemName())
    groups.setdefault((val, fpname), []).append(ref)
    pos = fp.GetPosition()
    cpl.append([ref, val, fpname,
                round(pcbnew.ToMM(pos.x), 3), round(-pcbnew.ToMM(pos.y), 3),
                "top" if fp.GetLayer() == pcbnew.F_Cu else "bottom",
                round(fp.GetOrientationDegrees(), 1)])

with open(bom_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Comment", "Designator", "Footprint", "LCSC"])
    for (val, fpname), refs in sorted(groups.items()):
        w.writerow([val, ",".join(sorted(refs)), fpname,
                    old_lcsc.get((val, fpname), "")])
with open(out / "cpl_jlc.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Val", "Package", "Mid X", "Mid Y", "Layer",
                "Rotation"])
    for row in sorted(cpl):
        w.writerow(row)

print(f"gerbers: {len(LAYERS)} layers + drills -> {out}")
print(f"BOM: {len(groups)} lines; CPL: {len(cpl)} parts; "
      f"LCSC carried: {sum(1 for k in groups if k in old_lcsc)}")
