#!/usr/bin/env python3
"""Post-stitch orphan-via sweep in its OWN process (kicad-pcb skill: batch
removals into their own load->remove->save script — the same sweep running
inside stitch_and_fill sees stale in-run state and missed a dangling via).
Removes non-GND vias with no same-net track endpoint / pad within 0.45mm,
then refills zones and saves. Idempotent."""
import math
import sys
from pathlib import Path
import pcbnew

HERE = Path(__file__).parent
PCB = str(HERE.parent / "04_kicad" / "cook_hub.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
MM = pcbnew.ToMM
gnd_nc = b.GetNetInfo().NetsByName()["GND"].GetNetCode()

trk = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        for e in (t.GetStart(), t.GetEnd()):
            trk.setdefault(t.GetNetCode(), []).append((MM(e.x), MM(e.y)))
padbb = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        padbb.setdefault(p.GetNetCode(), []).append(
            (MM(bb.GetLeft()) - 0.1, MM(bb.GetTop()) - 0.1,
             MM(bb.GetRight()) + 0.1, MM(bb.GetBottom()) + 0.1))
# near-duplicate same-net via dedupe (two barrels < 0.45mm apart = one
# hole_to_hole violation and zero electrical value; keep the first)
seen = []
dups = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA":
        continue
    vx, vy, nc = MM(t.GetPosition().x), MM(t.GetPosition().y), t.GetNetCode()
    if any(n == nc and (vx - x) ** 2 + (vy - y) ** 2 < 0.45 ** 2
           for (n, x, y) in seen):
        dups.append(t)
    else:
        seen.append((nc, vx, vy))
for t in dups:
    print(f"post-sweep dup via: ({MM(t.GetPosition().x):.2f},"
          f"{MM(t.GetPosition().y):.2f}) {t.GetNetname()}")
    b.Remove(t)
if dups:
    b.Save(PCB)
    b = pcbnew.LoadBoard(PCB)

orphans = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA" or t.GetNetCode() == gnd_nc:
        continue
    vx, vy = MM(t.GetPosition().x), MM(t.GetPosition().y)
    nc = t.GetNetCode()
    near = any((vx - x) ** 2 + (vy - y) ** 2 < 0.45 ** 2
               for x, y in trk.get(nc, []))
    near = near or any(l <= vx <= r and tp <= vy <= bt
                       for (l, tp, r, bt) in padbb.get(nc, []))
    if not near:
        orphans.append(t)
for t in orphans:
    print(f"post-sweep orphan via: ({MM(t.GetPosition().x):.2f},"
          f"{MM(t.GetPosition().y):.2f}) {t.GetNetname()}")
    b.Remove(t)

# iterative dangling-track pruner (T-junction aware): a segment end is
# CONNECTED if it touches a same-net pad bbox, via barrel, or lies on any
# other same-net segment's span. Ends touching nothing = dead copper (KRT
# repair hairpins); prune until stable. Removing a truly-free end cannot
# disconnect anything.
def p2seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    ll = dx * dx + dy * dy
    if ll < 1e-12:
        return math.hypot(px - x1, py - y1)
    tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ll))
    return math.hypot(px - (x1 + tt * dx), py - (y1 + tt * dy))


pruned = 0
while True:
    segs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    vias = [(t.GetNetCode(), MM(t.GetPosition().x), MM(t.GetPosition().y))
            for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
    padbb = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            bb = p.GetBoundingBox()
            padbb.append((p.GetNetCode(), MM(bb.GetLeft()) - 0.05,
                          MM(bb.GetTop()) - 0.05, MM(bb.GetRight()) + 0.05,
                          MM(bb.GetBottom()) + 0.05))
    dead = []
    for t in segs:
        nc = t.GetNetCode()
        sx, sy = MM(t.GetStart().x), MM(t.GetStart().y)
        ex2, ey2 = MM(t.GetEnd().x), MM(t.GetEnd().y)
        # a segment with MIDSPAN taps is never dead: engineered buses end in
        # a free tip while spur vias / other segments land mid-span (the
        # first pruner version deleted the whole RELAY_5V bus this way).
        midspan_tap = any(vn == nc and p2seg(vx, vy, sx, sy, ex2, ey2) < 0.32
                          for (vn, vx, vy) in vias)
        if not midspan_tap:
            for o in segs:
                if o is t or o.GetNetCode() != nc:
                    continue
                for oe in (o.GetStart(), o.GetEnd()):
                    if p2seg(MM(oe.x), MM(oe.y), sx, sy, ex2, ey2) < 0.08:
                        midspan_tap = True
                        break
                if midspan_tap:
                    break
        if midspan_tap:
            continue
        free = 0
        for e in (t.GetStart(), t.GetEnd()):
            ex, ey = MM(e.x), MM(e.y)
            conn = any(l <= ex <= r and tp <= ey <= bt
                       for (pn, l, tp, r, bt) in padbb if pn == nc)
            conn = conn or any(math.hypot(ex - vx, ey - vy) < 0.32
                               for (vn, vx, vy) in vias if vn == nc)
            if not conn:
                for o in segs:
                    if o is t or o.GetNetCode() != nc or o.GetLayer() != t.GetLayer():
                        continue
                    if p2seg(ex, ey, MM(o.GetStart().x), MM(o.GetStart().y),
                             MM(o.GetEnd().x), MM(o.GetEnd().y)) < 0.08:
                        conn = True
                        break
            if not conn:
                free += 1
        if free:
            dead.append(t)
    if not dead:
        break
    for t in dead:
        print(f"post-sweep dangling track: {t.GetNetname()} "
              f"({MM(t.GetStart().x):.2f},{MM(t.GetStart().y):.2f})->"
              f"({MM(t.GetEnd().x):.2f},{MM(t.GetEnd().y):.2f})")
        b.Remove(t)
        pruned += 1
    # SWIG safety: save+reload between prune iterations
    b.Save(PCB)
    b = pcbnew.LoadBoard(PCB)

if orphans or pruned:
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(PCB)
print(f"post-sweep: removed {len(orphans)} orphan vias, {pruned} dangling tracks")
