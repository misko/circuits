"""Board placement/pad invariant gates (I1-I7) — parameterized template.

    /usr/bin/python3 audit_template.py BOARD.kicad_pcb --config audit.json
    /usr/bin/python3 audit_template.py BOARD.kicad_pcb --config audit.json --update-baseline

Copy audit.json per project (this file documents the schema); commit it and
the baseline next to the board. Run on EVERY revision — these gates exist
because each one caught a real defect at least once:
  I1 pads inside the configured RECTANGLE (non-rectangular outlines need a
     custom check)                  I2 no parts parked off-board
  I3 edge connectors overhang their declared mate edge
  I4 screw-head keepouts            I5 unnetted pads only where whitelisted
  I6 bbox overlaps (warn)           I7 classified-DRC counts vs baseline
                                       (fail on real regressions, warn margin)

audit.json schema:
{
  "frame": [50.0, 50.0, 100.0, 65.0],          // X0, Y0, W, H (mm)
  "edge_margin": 0.3,
  "screw_head_r": 3.2,
  "fab_floor": 0.10,
  "mate": {"J1": "W", "J4": "E", "J7": "S"},   // connector -> overhang edge
  "float_ok": [["U4", "13"]],                   // intentionally unnetted pads
  "float_ok_numbers": ["MP", "S1"],             // pad NUMBERS always exempt (shells);
                                                 // default shown - override per project
  "baseline": "drc_baseline.json"               // relative to config
}
"""
import argparse
import collections
import json
import os
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
ap.add_argument("--config", required=True)
ap.add_argument("--update-baseline", action="store_true")
args = ap.parse_args()

cfg = json.loads(Path(args.config).read_text())
X0, Y0, W, H = cfg["frame"]
M = cfg.get("edge_margin", 0.3)
SR = cfg.get("screw_head_r", 3.2)
FLOOR = cfg.get("fab_floor", 0.10)
MATE = cfg.get("mate", {})
FLOAT_OK = {tuple(x) for x in cfg.get("float_ok", [])}
FLOAT_OK_NUMS = set(cfg.get("float_ok_numbers", ["MP", "S1"]))
BASELINE = Path(args.config).parent / cfg.get("baseline", "drc_baseline.json")

fails, warns = [], []
board = pcbnew.LoadBoard(args.board)
fps = {f.GetReference(): f for f in board.GetFootprints()}
mm = pcbnew.ToMM

for r, f in fps.items():
    c = f.GetPosition()
    if not (X0 <= mm(c.x) <= X0 + W and Y0 <= mm(c.y) <= Y0 + H):
        fails.append(f"I2 parked-off-board: {r}")
    for p in f.Pads():
        pos, hx, hy = p.GetPosition(), p.GetSizeX() / 2, p.GetSizeY() / 2
        if (mm(pos.x) - mm(int(hx)) < X0 + M or
                mm(pos.x) + mm(int(hx)) > X0 + W - M or
                mm(pos.y) - mm(int(hy)) < Y0 + M or
                mm(pos.y) + mm(int(hy)) > Y0 + H - M):
            fails.append(f"I1 pad-off-board: {r}/{p.GetNumber()}")

for r, side in MATE.items():
    f = fps.get(r)
    if f is None:
        continue
    bb = f.GetBoundingBox(False, False)
    over = {"W": X0 - mm(bb.GetLeft()), "E": mm(bb.GetRight()) - (X0 + W),
            "N": Y0 - mm(bb.GetTop()),
            "S": mm(bb.GetBottom()) - (Y0 + H)}[side]
    if over < -1.0:
        fails.append(f"I3 mate-direction: {r} declared {side}, body "
                     f"{-over:.1f}mm short (rotated wrong?)")

holes = [f.GetPosition() for rr, f in fps.items() if rr.startswith("H")]
for r, f in fps.items():
    if r.startswith("H"):
        continue
    for p in f.Pads():
        for hp in holes:
            if max(abs(mm(p.GetPosition().x) - mm(hp.x)),
                   abs(mm(p.GetPosition().y) - mm(hp.y))) < SR:
                fails.append(f"I4 screw-head: {r}/{p.GetNumber()}")
    bb = f.GetBoundingBox(False, False)
    for hp in holes:
        if (mm(bb.GetLeft()) < mm(hp.x) < mm(bb.GetRight()) and
                mm(bb.GetTop()) < mm(hp.y) < mm(bb.GetBottom())):
            warns.append(f"I4w body-over-hole: {r}")

for r, f in fps.items():
    if r.startswith("H"):
        continue
    for p in f.Pads():
        num = p.GetNumber()
        if (num and p.GetNetCode() <= 0 and (r, num) not in FLOAT_OK
                and num not in FLOAT_OK_NUMS):
            warns.append(f"I5 unnetted: {r} pad {num}")

# I8 refdes-on-silk: every part's reference must PRINT on the physical
# board (F.SilkS or B.SilkS, visible). F.Fab-only refdes shipped once -
# the board had functional labels but no U/R/C names for probing/debug.
# Exceptions (e.g. tiny passives the user waives) go in cfg["ref_silk_ok"].
REF_SILK_OK = set(cfg.get("ref_silk_ok", []))
for r, f in fps.items():
    if r.startswith("H") or r in REF_SILK_OK:
        continue
    ref = f.Reference()
    lay = ref.GetLayerName() if hasattr(ref, "GetLayerName") else ""
    if "Silk" not in lay or not ref.IsVisible():
        fails.append(f"I8 refdes-not-on-silk: {r} (layer={lay}, "
                     f"visible={ref.IsVisible()})")

boxes = [(r, f.GetBoundingBox(False, False)) for r, f in fps.items()
         if not r.startswith("H")]
ov = [(boxes[i][0], boxes[j][0]) for i in range(len(boxes))
      for j in range(i + 1, len(boxes)) if boxes[i][1].Intersects(boxes[j][1])]
if ov:
    warns.append(f"I6 bbox-overlaps ({len(ov)}): {ov[:10]}")

# I6c COURTYARD OVERLAP — a hard FAIL, independently of DRC.
# I6 above is bounding-BOX and warn-only: a bbox is the part's rectangular
# extent including silk, so it over-reports on any dense board and could
# never be promoted to a fail. The COURTYARD is the assembly-clearance
# polygon, and two overlapping courtyards mean the parts cannot both be
# placed — that is unambiguously broken. This used to be caught only via
# I7's `courtyards_overlap` DRC counter, which is silent whenever the
# baseline file is missing (a fresh project) or was captured dirty.
cy = []
for r, f in fps.items():
    if r.startswith("H"):
        continue
    for side, lay in (("F", pcbnew.F_CrtYd), ("B", pcbnew.B_CrtYd)):
        poly = f.GetCourtyard(lay)
        if poly and poly.OutlineCount():
            cy.append((r, side, poly))
cy_ov = []
for i in range(len(cy)):
    for j in range(i + 1, len(cy)):
        ra, sa, pa = cy[i]
        rb, sb, pb = cy[j]
        if sa != sb:
            continue                    # opposite board sides never collide
        test = pcbnew.SHAPE_POLY_SET(pa)
        test.BooleanIntersection(pb)
        if test.OutlineCount():
            cy_ov.append(f"{ra}~{rb}({sa})")
if cy_ov:
    fails.append(f"I6c courtyard-overlap ({len(cy_ov)}): {sorted(cy_ov)[:10]}")

# pid-suffixed: the old fixed /tmp/audit_drc.txt collided across concurrent
# sessions (a live clean-room canary's audit clobbered a test-suite run's
# report mid-read, 2026-07-21 — two t4 flakes with impossible categories)
rpt = f"/tmp/audit_drc.{os.getpid()}.txt"
_write_drc_report(board, args.board, rpt)
txt = Path(rpt).read_text()
blocks = re.split(r"\[(\w+)\]: ", txt)
counts = collections.Counter(re.findall(r"\[(\w+)\]", txt))
counts = {k: v for k, v in counts.items()
          if k in ("copper_edge_clearance", "courtyards_overlap",
                   "holes_co_located", "shorting_items", "unconnected_items",
                   "starved_thermal", "solder_mask_bridge", "silk_overlap")}
for cat in ("clearance", "hole_clearance"):
    real = margin = 0
    for i in range(1, len(blocks) - 1, 2):
        if blocks[i] != cat:
            continue
        m = re.search(r"actual ([0-9.]+) mm", blocks[i + 1])
        v = float(m.group(1)) if m else -1.0
        nets = set(re.findall(r"\[([A-Za-z0-9_/.+-]+)\]", blocks[i + 1]))
        if len(nets) > 1 and 0 <= v < FLOOR:
            real += 1
        else:
            margin += 1
    counts[cat + "_real"] = real
    counts[cat + "_margin"] = margin

if args.update_baseline:
    BASELINE.write_text(json.dumps(counts, indent=1, sort_keys=True))
    print("baseline updated:", counts)
elif BASELINE.exists():
    base = json.loads(BASELINE.read_text())
    for k, v in counts.items():
        if v > base.get(k, 0):
            msg = f"I7 DRC-regression: {k} {base.get(k, 0)} -> {v}"
            (warns if k.endswith("_margin") else fails).append(msg)
else:
    warns.append("I7 no baseline — run --update-baseline once clean")

for w in warns:
    print("WARN:", w)
for x in sorted(set(fails)):
    print("FAIL:", x)
print("AUDIT:", "FAIL" if fails else "PASS",
      f"({len(set(fails))} fails, {len(warns)} warns)")
sys.exit(1 if fails else 0)
