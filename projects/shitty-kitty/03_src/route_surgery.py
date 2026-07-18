#!/usr/bin/env python3
"""Route-campaign surgery on the KRT chain file: delete the congestion-
artifact vias (different-net via pairs closer than legal, vias inside
fine-pitch pad hole-clearance, sub-floor width leftovers), then the caller
re-routes the affected nets with KRT. Runs against 06_build/route/r5 and
writes r5s; invoked by route_waves.sh after the waves.

Deterministic detector (no coordinates hardcoded):
  - via pairs (different nets) with copper gap < 0.09 or hole gap < 0.30
    -> delete BOTH vias' nets' local segments (within 1.5mm) + the vias
  - vias whose hole sits < 0.20 from a foreign SMD pad -> same treatment
  - dangling detection is left to the stitcher (janitor)
Prints the affected net list for the caller's re-route invocation.
"""
import math, sys
from pathlib import Path
import pcbnew

SRC = Path(__file__).parent.parent / "06_build" / "route" / "r5.kicad_pcb"
OUT = SRC.with_name("r5s.kicad_pcb")
b = pcbnew.LoadBoard(str(SRC))

vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
bad = set()          # via objects to remove
nets = set()

def mmx(v): return v.GetPosition().x / 1e6
def mmy(v): return v.GetPosition().y / 1e6

for i, v1 in enumerate(vias):
    for v2 in vias[i+1:]:
        if v1.GetNetCode() == v2.GetNetCode():
            continue
        d = math.hypot(mmx(v1)-mmx(v2), mmy(v1)-mmy(v2))
        gap = d - (v1.GetWidth() + v2.GetWidth()) / 2e6
        hole_gap = d - (v1.GetDrillValue() + v2.GetDrillValue()) / 2e6
        if gap < 0.09 or hole_gap < 0.30:
            bad.update((v1, v2))
            nets.update((v1.GetNetname(), v2.GetNetname()))

for v1 in vias:
    r_hole = v1.GetDrillValue() / 2e6
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == v1.GetNetCode():
                continue
            if p.GetAttribute() not in (pcbnew.PAD_ATTRIB_SMD,):
                continue
            bbox = p.GetBoundingBox()
            px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6
            if abs(px-mmx(v1)) > 2 or abs(py-mmy(v1)) > 2:
                continue
            # conservative: distance from hole edge to pad bbox
            dx = max(bbox.GetLeft()/1e6 - mmx(v1), mmx(v1) - bbox.GetRight()/1e6, 0)
            dy = max(bbox.GetTop()/1e6 - mmy(v1), mmy(v1) - bbox.GetBottom()/1e6, 0)
            if math.hypot(dx, dy) - r_hole < 0.20:
                bad.add(v1)
                nets.add(v1.GetNetname())

# GND vias belong to the stitcher, not the router - never surgical here
bad = {v for v in bad if v.GetNetname() != "GND"}
nets.discard("GND")

# remove bad vias + same-net segments within 1.5mm of each bad via
seg_kill = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK":
        continue
    for v1 in bad:
        if t.GetNetCode() != v1.GetNetCode():
            continue
        for e in (t.GetStart(), t.GetEnd()):
            if math.hypot(e.x/1e6-mmx(v1), e.y/1e6-mmy(v1)) < 1.5:
                seg_kill.append(t)
                break
        else:
            continue
        break
for t in set(seg_kill):
    b.Remove(t)
for v1 in bad:
    b.Remove(v1)
b.Save(str(OUT))
print(f"surgery: removed {len(bad)} vias + {len(set(seg_kill))} segments; "
      f"re-route nets: {' '.join(sorted(nets))}")
