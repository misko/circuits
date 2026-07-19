#!/usr/bin/env python3
"""Prepare the KRT routing input: 06_build/route/r0.kicad_pcb.

- copies the board AFTER route_channels.py (hand tracks present, zones
  UNFILLED). The current KRT respects existing tracks/vias as obstacles
  (wall-crossing probe, 2026-07-18) and completes the west-zone nets —
  including the west portions of SDA/SCL/ALERT/3V3, whose east halves
  the hand corridor already connects — routing AROUND the hand copper.
- keepout rects on User.2 (KRT stays out of the slices/trunk/antenna;
  pours are unfilled and thus invisible to it)
- rules ride INTO the router (canon R1): r0.kicad_pro/.kicad_dru copied.

Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh."""
import shutil
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

SRC = HERE.parent / "04_kicad" / "ble_bus_bar.kicad_pcb"
OUT = HERE.parent / "06_build" / "route" / "r0.kicad_pcb"
OUT.parent.mkdir(parents=True, exist_ok=True)

b = pcbnew.LoadBoard(str(SRC))
nhand = len([t for t in b.GetTracks()])
assert nhand > 100, f"route_prep expects the hand-routed board (route_channels first), found {nhand} tracks"
for z in b.Zones():
    z.UnFill()

# 3V3 spans the corridor boundary and KRT cannot trace connectivity through
# vias — its MST then chases unroutable east-slice pads and starves the west
# edges. Rename the WEST pads to TMP_3V3 (rebuild maps the name back in the
# chain file); the corridor bridge track ends inside R17.2, so the mapped-
# back net is contiguous.
tmp = pcbnew.NETINFO_ITEM(b, "TMP_3V3")
b.Add(tmp)
renamed = 0
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == "3V3" and p.GetPosition().x / 1e6 < 97.5:
            p.SetNet(tmp)
            renamed += 1
print(f"renamed {renamed} west 3V3 pads -> TMP_3V3")


def keepout_rect(x0, y0, x1, y1):
    poly = pcbnew.PCB_SHAPE(b)
    poly.SetShape(pcbnew.SHAPE_T_POLY)
    pts = pcbnew.VECTOR_VECTOR2I(
        [pcbnew.VECTOR2I_MM(x0, y0), pcbnew.VECTOR2I_MM(x1, y0),
         pcbnew.VECTOR2I_MM(x1, y1), pcbnew.VECTOR2I_MM(x0, y1)])
    poly.SetPolyPoints(pts)
    poly.SetLayer(pcbnew.User_2)
    poly.SetFilled(False)
    poly.SetWidth(pcbnew.FromMM(0.05))
    b.Add(poly)


for (x0, y0, x1, y1) in G.KRT_KEEPOUTS:
    keepout_rect(x0, y0, x1, y1)
# screw-head keepouts around the NPTH mounting holes
R = 3.2
for hx, hy in G.HOLES:
    keepout_rect(hx - R, hy - R, hx + R, hy + R)

b.Save(str(OUT))
shutil.copy(SRC.with_suffix(".kicad_pro"), OUT.with_suffix(".kicad_pro"))
shutil.copy(SRC.with_suffix(".kicad_dru"), OUT.with_suffix(".kicad_dru"))
print(f"wrote {OUT} ({nhand} hand tracks kept, keepouts on User.2, zones unfilled)")
