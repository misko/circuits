#!/usr/bin/env python3
"""Prepare the KRT routing input for crow-array-central (4-layer).

Copies the freshly generated (track-free, unfilled) board to
06_build/route/r0.kicad_pcb + r0.kicad_pro/.kicad_dru (canon R1: netclass
rules ride INTO the router), with #2 screw-head keepout squares on User.2
around the four M3 mounting holes so no wave routes under a screw head.

Stackup (ADR-0001): F.Cu signal - In1.Cu SOLID GND (the reference plane,
never routed) - In2.Cu power+signal - B.Cu signal+GND. GND is NOT routed:
In1 plane + F/In2/B pours + stitch vias (stitch_and_fill.py). Power rails
route as floored tracks across F/In2/B (D15: the rails are spatially
intermixed - 3V3+0V9 both dense at the XU316, 3V3 at both ADCs - so a
clean one-island-per-rail In2 partition is not geometrically possible;
the PWR5 0.5mm / RAIL 0.4mm dru floors give ampacity).

Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh."""
import shutil
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
SRC = HERE.parent / "04_kicad" / "crow_array_central.kicad_pcb"
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


R = 2.8  # M3 screw head ~5.5mm dia -> ~2.8mm radius + margin
for f in b.GetFootprints():
    if not f.GetReference().startswith("H"):
        continue
    x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
    keepout_rect(x - R, y - R, x + R, y + R)

# The SHT40 (U6) footprint ships a track/via keepout over the DFN body — but
# it sits ON the sensor's own I2C/3V3 pad approaches, so mirroring it onto
# User.2 blocked the sensor's own connections. Instead strip the track/via
# keepout flags from U6's rule area here (keep it a copper-POUR keepout so
# the GND pour still stays off the sensing area). Fixes items_not_allowed.
for f in b.GetFootprints():
    if f.GetReference() != "U6":
        continue
    for z in f.Zones():
        if z.GetIsRuleArea():
            z.SetDoNotAllowTracks(False)
            z.SetDoNotAllowVias(False)

b.Save(str(OUT))
# rules ride into the router (R-RULES): copy the pro + dru beside r0
shutil.copy(SRC.with_suffix(".kicad_pro"), OUT.with_suffix(".kicad_pro"))
shutil.copy(SRC.with_suffix(".kicad_dru"), OUT.with_suffix(".kicad_dru"))
print(f"wrote {OUT} (keepouts on User.2, zones unfilled) + r0.kicad_pro/.kicad_dru")
