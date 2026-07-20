#!/usr/bin/env python3
"""Prepare the KRT routing input: copy the freshly generated (track-free,
unfilled) board to 06_build/route/r0.kicad_pcb (+ .kicad_pro/.kicad_dru,
canon R1) with User.2 keepouts:
- screw-head squares around the four NPTH mounting holes;
- a board-perimeter keep-away band (KRT has no edge concept);
- the DIGITAL keep-out over the analog corner for DAT/CLK/RATE_SEL routing
  is enforced post-route by the audit (I-AN); the analog corner stubs are
  short and KRT wave 1 routes them first (hardest-first).

Writes nets_an.txt (wave 1: BRIDGE + AVDD loop) and nets_sig.txt (wave 2).
Run: /usr/bin/python3 03_src/route_prep.py, then 03_src/route_waves.sh."""
import shutil
import sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

SRC = HERE.parent / "04_kicad" / "cook_loadcell.kicad_pcb"
OUT = HERE.parent / "06_build" / "route" / "r0.kicad_pcb"
OUT.parent.mkdir(parents=True, exist_ok=True)

b = pcbnew.LoadBoard(str(SRC))
tracks = [t for t in b.GetTracks()]
assert not tracks, f"route_prep expects a track-free board, found {len(tracks)}"
for z in b.Zones():
    z.UnFill()


def keepout_rect(x0, y0, x1, y1, layer=None):
    for lay in ([pcbnew.User_2, pcbnew.User_3] if layer is None else [layer]):
        poly = pcbnew.PCB_SHAPE(b)
        poly.SetShape(pcbnew.SHAPE_T_POLY)
        pts = pcbnew.VECTOR_VECTOR2I(
            [pcbnew.VECTOR2I_MM(x0, y0), pcbnew.VECTOR2I_MM(x1, y0),
             pcbnew.VECTOR2I_MM(x1, y1), pcbnew.VECTOR2I_MM(x0, y1)])
        poly.SetPolyPoints(pts)
        poly.SetLayer(lay)
        poly.SetFilled(False)
        poly.SetWidth(pcbnew.FromMM(0.05))
        b.Add(poly)


R = 3.0  # M3 screw head + margin
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            x, y = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            keepout_rect(x - R, y - R, x + R, y + R)

# board-perimeter keep-away band (copper_edge_clearance floor is 0.3)
EB = 0.7
for (x0, y0, x1, y1) in [
        (G.X0, G.Y0, G.X1, G.Y0 + EB), (G.X0, G.Y1 - EB, G.X1, G.Y1),
        (G.X0, G.Y0, G.X0 + EB, G.Y1), (G.X1 - EB, G.Y0, G.X1, G.Y1)]:
    keepout_rect(x0, y0, x1, y1)

# ANALOG GUARD (D5/§3.7e, audit I-AN): the whole digital EAST region —
# RATE_SEL belt (U1.15 -> JP1), DAT/CLK corridor (U1 -> J6), TP/ESD pocket —
# is keepout for the BRIDGE wave ONLY (User.3). Bridge nets are confined to
# the west side + the y<30 north strip (their only east destinations are the
# J5 pads at y24.2); a notch at x<47 keeps the J4 pad pocket escapable.
# Later waves use User.2 (no guard) — U1's digital pins all sit on the EAST
# pad column, so they never need the analog west side.
keepout_rect(42.0, 30.0, G.X1, 56.0, layer=pcbnew.User_3)
keepout_rect(47.0, 56.0, G.X1, 65.0, layer=pcbnew.User_3)

b.Save(str(OUT))
shutil.copy(SRC.with_suffix(".kicad_pro"), OUT.with_suffix(".kicad_pro"))
shutil.copy(SRC.with_suffix(".kicad_dru"), OUT.with_suffix(".kicad_dru"))

EXCLUDE = (lambda n: n == "GND" or n.startswith("unconnected"))
AN = ["E_PLUS", "S_PLUS", "S_MINUS",
      "RING_12", "RING_23", "RING_34", "RING_41", "AVDD_FB", "BASE"]
PWR = ["5V", "3V3"]     # 0.5 wave, no analog guard (must reach J6 in the SE)
allnets = sorted({p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
                 - {""})
sig = [n for n in allnets if not EXCLUDE(n) and n not in AN + PWR]
(OUT.parent / "nets_an.txt").write_text(" ".join(AN) + "\n")
(OUT.parent / "nets_pwr.txt").write_text(" ".join(PWR) + "\n")
(OUT.parent / "nets_sig.txt").write_text(" ".join(sig) + "\n")
print(f"wrote {OUT} (keepouts User.2 + analog-guard User.3, zones unfilled); "
      f"waves: {len(AN)} analog + {len(PWR)} pwr + {len(sig)} sig nets")
