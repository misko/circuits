"""Severity-classified DRC report: real vs margin vs same-net.

    /usr/bin/python3 classified_drc.py BOARD.kicad_pcb [--fab-floor 0.10] [--refill]

Real = different-net AND below the fab floor -> exit 1.
WARNING: --refill SAVES THE INPUT BOARD IN PLACE (fill + save). Omit it to
keep the gate read-only. Note "margin" here = different-net >= floor;
same-net items are counted separately (audit_template.py lumps same-net
into *_margin — don't compare baselines across the two scripts).
Margin (>= floor) and same-net items are reported but do not fail.
Remember: GUI DRC remains authoritative for zone-fill-dependent checks
(starved_thermal); this is the scriptable gate, not a replacement.
"""
import argparse
import collections
import re
import sys
from pathlib import Path

import pcbnew

def _write_drc_report(board, board_path, rpt):
    if hasattr(pcbnew, "EDA_UNITS_MILLIMETRES"):
        # KiCad 7/8: in-process report works headless
        pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, False)
    else:
        # KiCad >= 9: WriteDRCReport segfaults without the GUI Pgm() instance;
        # kicad-cli (v8+) emits the same [type]-tagged report format
        import subprocess
        subprocess.run(
            ["kicad-cli", "pcb", "drc", "--severity-all", "--refill-zones",
             "--format", "report", "-o", rpt, str(board_path)],
            check=True, capture_output=True)


ap = argparse.ArgumentParser()
ap.add_argument("board")
ap.add_argument("--fab-floor", type=float, default=0.10,
                help="fab clearance floor in mm (JLC 4L+: 0.10)")
ap.add_argument("--refill", action="store_true",
                help="refill zones (and save) before DRC")
args = ap.parse_args()

board = pcbnew.LoadBoard(args.board)
if args.refill:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(args.board)
    board = pcbnew.LoadBoard(args.board)

rpt = "/tmp/classified_drc.txt"
_write_drc_report(board, args.board, rpt)
txt = Path(rpt).read_text()

blocks = re.split(r"\[(\w+)\]: ", txt)
cats = collections.Counter(blocks[1::2])
real, margin, samenet = [], 0, 0
for i in range(1, len(blocks) - 1, 2):
    cat, body = blocks[i], blocks[i + 1]
    if cat not in ("clearance", "hole_clearance"):
        continue
    m = re.search(r"actual ([0-9.]+) mm", body)
    v = float(m.group(1)) if m else -1.0
    nets = set(re.findall(r"\[([A-Za-z0-9_/.+-]+)\]", body))
    if len(nets) > 1 and 0 <= v < args.fab_floor:
        real.append((cat, round(v, 3), sorted(nets)))
    elif len(nets) > 1:
        margin += 1
    else:
        samenet += 1

print("categories:", dict(cats.most_common()) or "NONE")
print(f"unconnected: {cats.get('unconnected_items', 0)}  "
      f"shorts: {cats.get('shorting_items', 0)}")
print(f"clearance-class items: REAL={len(real)}  margin(>= {args.fab_floor})="
      f"{margin}  same-net={samenet}")
for r in real[:20]:
    print("  REAL:", r)
fail = bool(real) or cats.get("unconnected_items", 0) or \
    cats.get("shorting_items", 0)
print("VERDICT:", "FAIL" if fail else "PASS")
sys.exit(1 if fail else 0)
