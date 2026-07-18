#!/usr/bin/env python3
"""Surgical footprint fixups on the promoted route artifact
(03_src/route/final.kicad_pcb). The shipped board is copied FROM this
artifact (rebuild_all.sh), so footprint-identity fixes must live here, not
only in generate_schematic.

1. U6 SHT40: FPID -> cac: and keepout flags (tracks/vias allowed) so the
   instance matches the vendored cac footprint (kills lib_footprint_mismatch;
   the stock lib ships tracks/vias not_allowed and route/stitch flip them).
2. J9 barrel jack: FPID -> cac: and clamp the west barrel-body F.SilkS lines
   from board x=9.2 (0.8mm past the x=10 board edge) to x=10.2, matching the
   vendored edge-trimmed cac footprint (kills silk_edge_clearance AND the
   mismatch a bare FPID swap would introduce).

Idempotent: safe to re-run (clamps only x<9.5, sets flags already-set).
"""
import math
import os
import sys
from pathlib import Path
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent / "route" / "final.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
NM = 1_000_000

for f in b.GetFootprints():
    ref = f.GetReference()
    if ref == "U6":
        f.SetFPIDAsString("cac:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad")
        for z in f.Zones():
            if z.GetIsRuleArea():
                z.SetDoNotAllowTracks(False)
                z.SetDoNotAllowVias(False)
        print("U6 -> cac:Sensirion (keepout tracks/vias allowed)")
    elif ref == "J9":
        f.SetFPIDAsString("cac:BarrelJack_Horizontal")
        n = 0
        for g in f.GraphicalItems():
            if g.GetClass() != "PCB_SHAPE" or g.GetLayer() != pcbnew.F_SilkS:
                continue
            for getter, setter in (("GetStart", "SetStart"), ("GetEnd", "SetEnd")):
                p = getattr(g, getter)()
                if p.x < int(9.5 * NM):
                    getattr(g, setter)(pcbnew.VECTOR2I(int(10.2 * NM), p.y))
                    n += 1
        print(f"J9 -> cac:BarrelJack_Horizontal, clamped {n} west silk endpoints to x=10.2")

# 3. TDO/TDI escape pair: KRT dropped both as via-in-pad on the U1 south row
# (pads 36 TDI / 37 TDO, 0.4mm pitch). Even as 0.30/0.15 small vias their
# drills sit 0.18mm apart (< the 0.2 JLC via-to-copper floor: 6x hole_clearance).
# Dogbone TDO out of pad 37 straight SOUTH into the escape channel (~0.75mm)
# so the TDO drill clears the TDI via and pad 38; TDI stays put. The move site
# and the F.Cu dogbone are exact-collide checked at 0.30/0.15.
tk = Toolkit(b, 0.1)
LAY = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.In3_Cu, pcbnew.In4_Cu, pcbnew.B_Cu)
tdo = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "TDO"]
v = min(tdo, key=lambda z: (z.GetPosition().x / NM - 95.4) ** 2 + (z.GetPosition().y / NM - 107.662) ** 2)
vx, vy = v.GetPosition().x / NM, v.GetPosition().y / NM
nc = v.GetNetCode()
pad = None
for f in b.GetFootprints():
    if f.GetReference() == "U1":
        for p in f.Pads():
            if p.GetNetCode() == nc and (p.GetPosition().x / NM - vx) ** 2 + (p.GetPosition().y / NM - vy) ** 2 < 0.3 ** 2:
                pad = p
pcx, pcy = pad.GetPosition().x / NM, pad.GetPosition().y / NM
if (vx - pcx) ** 2 + (vy - pcy) ** 2 > 0.4 ** 2:
    print("TDO via already relocated (>0.4mm from pad 37) - skip")
    b.Save(PCB)
    sys.exit(0)
placed = None
for ang in (90, 75, 105, 60, 120):
    for step in range(3, 24):
        d = step * 0.05
        nx = round(pcx + d * math.cos(math.radians(ang)), 3)
        ny = round(pcy + d * math.sin(math.radians(ang)), 3)
        if tk.via_site_ok(nx, ny, nc, size=0.30, drill=0.15, hole_to_copper=0.205, layers=LAY) \
           and not tk.collides(pcx, pcy, nx, ny, 0.2, nc, pcbnew.F_Cu, clr=0.1):
            placed = (nx, ny)
            break
    if placed:
        break
if placed is None:
    sys.exit("FAIL: no TDO escape site")
nx, ny = placed
# require the B.Cu bridge (new via -> old via position, where the escape
# starts) to be collision-free too, else the escape reshaping shorts a
# neighbour (a 3V3 via 2mm away). Keep the original B.Cu escape geometry
# untouched; only bridge the gap the via move opened.
if tk.collides(nx, ny, vx, vy, 0.2, nc, pcbnew.B_Cu, clr=0.1):
    sys.exit("FAIL: TDO B.Cu bridge collides")
v.SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
v.SetWidth(int(0.30 * NM))
v.SetDrill(int(0.15 * NM))
for lay, a, bpt in ((pcbnew.F_Cu, (pcx, pcy), (nx, ny)),   # dogbone pad37 -> via
                    (pcbnew.B_Cu, (nx, ny), (vx, vy))):    # bridge via -> old escape start
    seg = pcbnew.PCB_TRACK(b)
    seg.SetStart(pcbnew.VECTOR2I_MM(*a))
    seg.SetEnd(pcbnew.VECTOR2I_MM(*bpt))
    seg.SetWidth(int(0.2 * NM))
    seg.SetLayer(lay)
    seg.SetNetCode(nc)
    b.Add(seg)
print(f"TDO via {vx:.3f},{vy:.3f} -> {nx},{ny} (F.Cu dogbone + B.Cu bridge) — clears TDI pair")

b.Save(PCB)
print("route fixups saved")
