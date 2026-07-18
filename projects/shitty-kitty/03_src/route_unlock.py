#!/usr/bin/env python3
"""Route-campaign step: rip the congestion web around the two SDA taps the
waves could never close (U4.3, U6.3) on the KRT chain file, so a final KRT
co-route can arbitrate the corridor fresh. Runs on 06_build/route/r5 ->
r5u; route_waves.sh then KRT-routes the ripped nets into the final r5."""
import math, sys
from pathlib import Path
import pcbnew

R = Path(__file__).parent.parent / "06_build" / "route"
b = pcbnew.LoadBoard(str(R / "r5.kicad_pcb"))
CENTERS = [((66.9, 65.5), 2.2, {"SDA", "SCL", "VREG_U3", "MPR_IRQ1"})]
kill = []
for t in b.GetTracks():
    nn = t.GetNetname()
    for (cx, cy), rad, nets in CENTERS:
        if nn not in nets:
            continue
        pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
        if any(math.hypot(p.x/1e6-cx, p.y/1e6-cy) < rad for p in pts):
            kill.append(t)
            break
for t in kill:
    b.Remove(t)
b.Save(str(R / "r5u.kicad_pcb"))
print(f"unlock: ripped {len(kill)} items around the SDA taps")
