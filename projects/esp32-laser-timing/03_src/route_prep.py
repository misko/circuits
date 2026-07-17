#!/usr/bin/env python3
"""Prepare the KRT routing input: copy the freshly generated (track-free,
unfilled) board to 06_build/route/r0.kicad_pcb with screw-head keepout
squares on User.2 around the four M3 mounting holes and an antenna guard
keepout strip along the module's top pad row.

Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh.
KRT is only needed to re-route from scratch; the standard rebuild imports
the last chain file."""
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
SRC = HERE.parent / "04_kicad" / "esp32_laser_timing.kicad_pcb"
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


R = 3.0  # screw head ~5.5mm dia + margin
for f in b.GetFootprints():
    if not f.GetReference().startswith("H"):
        continue
    x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
    keepout_rect(x - R, y - R, x + R, y + R)

# J1 NPTH alignment pegs: keep tracks/vias clear (hole_clearance/hole_to_hole)
j1 = b.FindFootprintByReference("J1")
for p in j1.Pads():
    if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
        x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
        keepout_rect(x - 1.0, y - 1.0, x + 1.0, y + 1.0)

# USB dive corridor: reserved east of J1 pad A6 for the post-import
# fix_usb_dive.py relocation of KRT's illegal 0.3/0.2 tap via (the router
# emits it at the pad center every run; JLC 2L standard floor is 0.3 drill)
keepout_rect(58.85, 65.85, 59.65, 66.65)

# antenna guard: nothing routes in the strip above the module's top pad row
u1 = b.FindFootprintByReference("U1")
p1 = {p.GetNumber(): p.GetPosition() for p in u1.Pads() if p.GetNumber()}
keepout_rect(p1["1"].x / 1e6 - 1.0, 50.0, p1["40"].x / 1e6 + 1.0, p1["1"].y / 1e6 - 0.9)

b.Save(str(OUT))
print(f"wrote {OUT} (keepouts on User.2, zones unfilled)")
