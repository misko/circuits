#!/usr/bin/env python3
"""Prepare the KRT routing input: copy the freshly generated (track-free,
unfilled) board to 06_build/route/r0.kicad_pcb + r0.kicad_pro/.kicad_dru
(canon R1), with keepouts on User.2:
- geom.KRT_KEEPOUTS (relay bank + keypad comb + coil lanes + ULN north row)
- screw-head squares around the NPTH mounting holes
- fences around NPTH posts (J1 barrel) — DRC hole clearance > KRT clearance

Also writes the KRT net lists: nets_pwr.txt (wave 1) and nets_sig.txt
(wave 2). Excluded from KRT entirely: GND (planes+stitch), KEYPAD (KC*),
COIL_*, RELAY_5V (route_bank.py draws all of those).

Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh."""
import shutil
import sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

SRC = HERE.parent / "04_kicad" / "cook_hub.kicad_pcb"
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


for (x0, y0, x1, y1) in G.KRT_KEEPOUTS:
    keepout_rect(x0, y0, x1, y1)

# Reserve the RELAY_5V bank-spur In2 lanes (route_bank drops a via at each of
# C8/C9/R25/TP33 and runs In2 NORTH to the y=101.8 bus). The Q1 pocket is
# otherwise saturated by the east-bound Pico fan-out — KRT's F<->B via barrels
# pass through In2 and block the vertical run. These vertical keepout lanes
# (bus approach down to each pad) force KRT's tracks + vias out of the lane so
# the In2 verticals are clear. Lanes sit clear of Q1's gate pad (x60.55).
for (x0, y0, x1, y1) in [(58.8, 111.9, 60.9, 113.4),   # C8 pad+stub box
                         (58.8, 101.4, 60.2, 111.9),   # C8 north In2 lane
                         (122.8, 101.4, 125.4, 110.0),  # C9 lane (col3-4 gap)
                         (126.8, 101.4, 129.4, 110.0),  # R25 lane (col3-4 gap)
                         (130.8, 101.4, 133.4, 110.0)]:  # TP33 lane (col3-4 gap)
    keepout_rect(x0, y0, x1, y1)

R = 3.0  # M3 screw head + margin
for f in b.GetFootprints():
    if f.GetReference().startswith("H"):
        x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
        keepout_rect(x - R, y - R, x + R, y + R)
    for p in f.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            r = p.GetDrillSize().x / 2e6 + 0.25 + 0.35
            keepout_rect(x - r, y - r, x + r, y + r)

b.Save(str(OUT))
shutil.copy(SRC.with_suffix(".kicad_pro"), OUT.with_suffix(".kicad_pro"))
shutil.copy(SRC.with_suffix(".kicad_dru"), OUT.with_suffix(".kicad_dru"))

# ------------------------------------------------- net lists for the waves
EXCLUDE_PRED = (lambda n: n == "GND" or n.startswith("KC") or
                n.startswith("COIL_") or n == "RELAY_5V" or
                n.startswith("unconnected"))
PWR = ["5V_IN", "5V_D", "5VP", "VSYS", "3V3", "3V3A"]
SPI = ["CS0", "CS1", "SCK", "MISO", "MOSI"]   # boxed-in Pico east-column
allnets = sorted({p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
                 - {""})
sig = [n for n in allnets if not EXCLUDE_PRED(n) and n not in PWR + SPI]
(OUT.parent / "nets_pwr.txt").write_text(" ".join(PWR) + "\n")
(OUT.parent / "nets_spi.txt").write_text(" ".join(SPI) + "\n")
(OUT.parent / "nets_sig.txt").write_text(" ".join(sig) + "\n")
print(f"wrote {OUT} (keepouts User.2, zones unfilled); "
      f"waves: {len(PWR)} pwr + {len(sig)} sig nets")
