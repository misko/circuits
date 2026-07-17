#!/usr/bin/env python3
"""Prepare the KRT routing input: copy the freshly generated (track-free,
unfilled) board to 06_build/route/r0.kicad_pcb with screw-head keepout
squares on User.2 around the four M2.5 mounting holes.

Run: /usr/bin/python3 03_src/route_prep.py
Then the KRT waves (see 03_src/route_waves.sh) — KRT is only needed to
re-route from scratch; the committed board carries the imported result.
"""
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
SRC = HERE.parent / "04_kicad" / "crowsync_recorder.kicad_pcb"
OUT = HERE.parent / "06_build" / "route" / "r0.kicad_pcb"
OUT.parent.mkdir(parents=True, exist_ok=True)

b = pcbnew.LoadBoard(str(SRC))
# safety: must be track-free; unfill any zone
tracks = [t for t in b.GetTracks()]
assert not tracks, f"route_prep expects a track-free board, found {len(tracks)}"
for z in b.Zones():
    z.UnFill()

R = 3.0  # keepout half-size (screw head ~5.5mm dia + margin)
for f in b.GetFootprints():
    if not f.GetReference().startswith("H"):
        continue
    x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
    poly = pcbnew.PCB_SHAPE(b)
    poly.SetShape(pcbnew.SHAPE_T_POLY)
    pts = pcbnew.VECTOR_VECTOR2I(
        [pcbnew.VECTOR2I_MM(x - R, y - R), pcbnew.VECTOR2I_MM(x + R, y - R),
         pcbnew.VECTOR2I_MM(x + R, y + R), pcbnew.VECTOR2I_MM(x - R, y + R)])
    poly.SetPolyPoints(pts)
    poly.SetLayer(pcbnew.User_2)
    poly.SetFilled(False)
    poly.SetWidth(pcbnew.FromMM(0.05))
    b.Add(poly)

b.Save(str(OUT))
print(f"wrote {OUT} (keepouts on User.2, zones unfilled)")
