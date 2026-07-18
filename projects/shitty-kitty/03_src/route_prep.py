#!/usr/bin/env python3
"""Prepare the KRT routing input: copy the freshly generated (track-free,
unfilled) board to 06_build/route/r0.kicad_pcb with User.2 keepouts:
screw-head squares at the 4 mounting holes, the SOUTH antenna guard strip,
and the barrel-jack hole cluster. KRT routes F.Cu/B.Cu only; In1 (GND
plane) and In2 (power pours) stay track-free.

Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
SRC = HERE.parent / "04_kicad" / "shitty_kitty.kicad_pcb"
OUT = HERE.parent / "06_build" / "route" / "r0.kicad_pcb"
OUT.parent.mkdir(parents=True, exist_ok=True)

b = pcbnew.LoadBoard(str(SRC))
tracks = [t for t in b.GetTracks()]
assert not tracks, f"route_prep expects a track-free board, found {len(tracks)}"
for z in b.Zones():
    z.UnFill()


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


R = 3.0
for f in b.GetFootprints():
    if not f.GetReference().startswith("H"):
        continue
    x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
    keepout_rect(x - R, y - R, x + R, y + R)

# antenna guard strip: module x-span from the south pad row to the edge
u1 = b.FindFootprintByReference("U1")
p1 = {p.GetNumber(): p.GetPosition() for p in u1.Pads() if p.GetNumber()}
ax0 = min(p1["1"].x, p1["40"].x) / 1e6 - 1.0
ax1 = max(p1["1"].x, p1["40"].x) / 1e6 + 1.0
keepout_rect(ax0, p1["1"].y / 1e6 + 0.9, ax1, 125.0)

b.Save(str(OUT))

# canon R1: the ROUTE-INPUT project file must carry the netclasses so KRT
# routes against the real floors, not Default. Run generate_rules against
# 04_kicad, then copy the .kicad_pro/.kicad_dru beside r0.
subprocess.run([sys.executable, str(HERE / "generate_rules.py")], check=True)
for ext in (".kicad_pro", ".kicad_dru"):
    shutil.copy(HERE.parent / "04_kicad" / ("shitty_kitty" + ext),
                OUT.with_name("r0" + ext))
pro = json.loads(OUT.with_name("r0.kicad_pro").read_text())
classes = [c["name"] for c in pro["net_settings"]["classes"]]
assert set(classes) >= {"PWR12", "MOTOR", "ELEC"}, classes
print(f"wrote {OUT} (keepouts on User.2, zones unfilled); route-input rules: {classes}")
