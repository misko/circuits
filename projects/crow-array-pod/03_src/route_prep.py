#!/usr/bin/env python3
"""Prepare the KRT routing input: copy the freshly generated (track-free,
unfilled) board to 06_build/route/r0.kicad_pcb + r0.kicad_pro/.kicad_dru
(canon R1: netclass rules ride INTO the router), with screw-head keepout
squares on User.2 around the four mounting holes and a corner-cutout
keepout at each notched corner.

Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh."""
import shutil
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
SRC = HERE.parent / "04_kicad" / "crow_array_pod.kicad_pcb"
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


R = 2.8  # #2 screw head ~4.4mm dia + margin
for f in b.GetFootprints():
    if not f.GetReference().startswith("H"):
        continue
    x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
    keepout_rect(x - R, y - R, x + R, y + R)

# corner cutouts: keep the router away from the concave arcs
X0, Y0, X1, Y1 = 50.0, 50.0, 144.5, 94.5
C = 6.8
keepout_rect(X0, Y0, X0 + C, Y0 + C)
keepout_rect(X1 - C, Y0, X1, Y0 + C)
keepout_rect(X0, Y1 - C, X0 + C, Y1)
keepout_rect(X1 - C, Y1 - C, X1, Y1)

b.Save(str(OUT))
# rules ride into the router (R-RULES): copy the pro + dru beside r0
shutil.copy(SRC.with_suffix(".kicad_pro"), OUT.with_suffix(".kicad_pro"))
shutil.copy(SRC.with_suffix(".kicad_dru"), OUT.with_suffix(".kicad_dru"))
print(f"wrote {OUT} (keepouts on User.2, zones unfilled) + r0.kicad_pro/.kicad_dru")
