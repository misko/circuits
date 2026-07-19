#!/usr/bin/env python3
"""GND stitching + zone refill (final copper pass).

- stitch via grid ties the F.Cu GND pour (electronics zone) to the B.Cu
  plane; conservative standoffs from every pad/track/via/hole/keepout
- power zones were created by generate_board (priority: VF/VP 2 over
  VBUS 1 over GND 0; solid pad connections)
- refills ALL zones and saves — the DRC gate re-fills again
  (--refill-zones) as the authoritative check

Run: /usr/bin/python3 03_src/stitch_and_fill.py
"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

PCB = HERE.parent / "04_kicad" / "ble_bus_bar.kicad_pcb"

# ---- pass 0 (own load->remove->save cycle; SWIG Remove() poisoning):
# drop KRT micro-fragments (<0.06mm) and enforce the small-via floor
# (KRT's fine-pitch escapes emit 0.3/0.2 vias; JLC small-hole tier is
# 0.45/0.2 — upsize in place, spacing was cut for the smaller ring so
# the 0.45 ring still clears its 0.5-pitch surroundings at >=0.15)
b = pcbnew.LoadBoard(str(PCB))
kill = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        # threshold BELOW the 0.05 fine-grid step: the r3 wave's tiny jog
        # segments are structural joints, not fragments (eaten once, 2026-07-18)
        if (t.GetStart() - t.GetEnd()).EuclideanNorm() < pcbnew.FromMM(0.02):
            kill.append(t)
for t in kill:
    b.Remove(t)
b.Save(str(PCB))

# micro-patcher: KRT chain imports occasionally leave same-net endpoints a
# hair apart (fine-grid jogs) or an endpoint hovering off another track's
# body. Solder them with tiny same-net segments — always safe (same net),
# and the DRC gate re-verifies everything after.
b = pcbnew.LoadBoard(str(PCB))
tracks2 = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
patches = []
def d2(a, b_):
    return ((a[0]-b_[0])**2 + (a[1]-b_[1])**2) ** 0.5
pts = []
for t in tracks2:
    for e in (t.GetStart(), t.GetEnd()):
        pts.append((e.x/1e6, e.y/1e6, t.GetNetname(), t.GetLayer(), t.GetWidth()))
for i in range(len(pts)):
    for j in range(i+1, len(pts)):
        a, c = pts[i], pts[j]
        if a[2] != c[2] or a[3] != c[3]:
            continue
        d = d2(a, c)
        if 0.001 < d < 0.12:
            patches.append((a[0], a[1], c[0], c[1], a[2], a[3], min(a[4], c[4])))
seen = set()
for (x1, y1, x2, y2, netn, lay, w) in patches:
    key = (round(x1,3), round(y1,3), round(x2,3), round(y2,3))
    if key in seen:
        continue
    seen.add(key)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
    t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
    t.SetWidth(w)
    t.SetLayer(lay)
    t.SetNet(b.FindNet(netn))
    b.Add(t)
# endpoint-to-body: hovering ends get a perpendicular stub
import math
def foot(px, py, x1, y1, x2, y2):
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return None
    tpar = ((px-x1)*dx + (py-y1)*dy) / L2
    if not (0.02 < tpar < 0.98):
        return None
    return (x1 + tpar*dx, y1 + tpar*dy)
npatch2 = 0
for (px, py, netn, lay, w) in pts:
    best = None
    for t in tracks2:
        if t.GetNetname() != netn or t.GetLayer() != lay:
            continue
        f = foot(px, py, t.GetStart().x/1e6, t.GetStart().y/1e6,
                 t.GetEnd().x/1e6, t.GetEnd().y/1e6)
        if f is None:
            continue
        d = d2((px, py), f)
        if 0.05 < d < 0.45 and (best is None or d < best[0]):
            best = (d, f)
    if best:
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(pcbnew.VECTOR2I_MM(px, py))
        t.SetEnd(pcbnew.VECTOR2I_MM(best[1][0], best[1][1]))
        t.SetWidth(w)
        t.SetLayer(lay)
        t.SetNet(b.FindNet(netn))
        b.Add(t)
        npatch2 += 1
# orphan sweep: tracks with BOTH ends >0.1mm from every same-net item
# (router-abandoned probes). Pads approximated by center distance.
allpads = [(p.GetPosition().x/1e6, p.GetPosition().y/1e6, p.GetNetname(),
            max(p.GetSize().x, p.GetSize().y)/2e6)
           for fp in b.GetFootprints() for p in fp.Pads()]
allvias = [(v.GetPosition().x/1e6, v.GetPosition().y/1e6, v.GetNetname())
           for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]
tracks3 = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
def end_served(px, py, netn, lay, me):
    for t in tracks3:
        if t is me or t.GetNetname() != netn or t.GetLayer() != lay:
            continue
        f = ((t.GetStart().x/1e6, t.GetStart().y/1e6), (t.GetEnd().x/1e6, t.GetEnd().y/1e6))
        if d2((px, py), f[0]) < 0.1 or d2((px, py), f[1]) < 0.1:
            return True
        ft = foot(px, py, f[0][0], f[0][1], f[1][0], f[1][1])
        if ft and d2((px, py), ft) < 0.1:
            return True
    for (vx, vy, vn) in allvias:
        if vn == netn and d2((px, py), (vx, vy)) < 0.32:
            return True
    for (qx, qy, qn, r) in allpads:
        if qn == netn and d2((px, py), (qx, qy)) < r + 0.1:
            return True
    return False
orphans = []
for t in tracks3:
    n, lay = t.GetNetname(), t.GetLayer()
    s_ = (t.GetStart().x/1e6, t.GetStart().y/1e6)
    e_ = (t.GetEnd().x/1e6, t.GetEnd().y/1e6)
    if not end_served(*s_, n, lay, t) and not end_served(*e_, n, lay, t):
        orphans.append(t)
for t in orphans:
    b.Remove(t)

# cross-layer solder: an endpoint unserved on its OWN layer that sits on a
# same-net track of the OTHER copper layer gets a via (router layer-change
# left implicit once, 2026-07-18)
nxvia = 0
for t in tracks3:
    if t in orphans:
        continue
    n, lay = t.GetNetname(), t.GetLayer()
    other = pcbnew.B_Cu if lay == pcbnew.F_Cu else pcbnew.F_Cu
    for e in (t.GetStart(), t.GetEnd()):
        px, py = e.x / 1e6, e.y / 1e6
        if end_served(px, py, n, lay, t):
            continue
        hit = False
        for t2 in tracks3:
            if t2.GetNetname() != n or t2.GetLayer() != other:
                continue
            f = foot(px, py, t2.GetStart().x/1e6, t2.GetStart().y/1e6,
                     t2.GetEnd().x/1e6, t2.GetEnd().y/1e6)
            if f and d2((px, py), f) < 0.25:
                hit = True
                break
        if hit:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(e)
            v.SetWidth(pcbnew.FromMM(0.56))
            v.SetDrill(pcbnew.FromMM(0.3))
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetNet(b.FindNet(n))
            b.Add(v)
            allvias.append((px, py, n))
            nxvia += 1
# 3V3 corridor west landing: the routed chain's west tree descends to
# F.Cu at (82.5, 68.6) (KRT chose the lane latitude as its attach row);
# extend the B.Cu lane west to meet it with a via. Deterministic for the
# promoted chain (03_src/route/r3); a fresh re-route re-lands here too
# (the via is an attach anchor).
t3 = pcbnew.PCB_TRACK(b)
t3.SetStart(pcbnew.VECTOR2I_MM(82.5, 68.6))
t3.SetEnd(pcbnew.VECTOR2I_MM(86.5, 68.6))
t3.SetWidth(pcbnew.FromMM(0.5))
t3.SetLayer(pcbnew.B_Cu)
t3.SetNet(b.FindNet("3V3"))
b.Add(t3)
v3 = pcbnew.PCB_VIA(b)
v3.SetPosition(pcbnew.VECTOR2I_MM(82.5, 68.6))
v3.SetWidth(pcbnew.FromMM(0.56))
v3.SetDrill(pcbnew.FromMM(0.3))
v3.SetViaType(pcbnew.VIATYPE_THROUGH)
v3.SetNet(b.FindNet("3V3"))
b.Add(v3)

b.Save(str(PCB))
print(f"pass0: {len(kill)} micro-fragments removed; {len(seen)} joint patches, "
      f"{npatch2} body patches; {len(orphans)} orphans removed; {nxvia} cross-layer vias")

b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM

gnd = b.FindNet("GND")
assert gnd is not None

# obstacles
pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        pads.append((MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()),
                     MM(bb.GetBottom()), p.GetNetname()))
tracks, vias = [], []
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vias.append((MM(t.GetPosition().x), MM(t.GetPosition().y)))
    else:
        tracks.append((MM(t.GetStart().x), MM(t.GetStart().y),
                       MM(t.GetEnd().x), MM(t.GetEnd().y), t.GetNetname()))
holes = list(G.HOLES)


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    cxp, cyp = x1 + t * dx, y1 + t * dy
    return ((px - cxp) ** 2 + (py - cyp) ** 2) ** 0.5


def clear(x, y):
    # inside electronics GND region, generous margins everywhere
    if not (G.X0 + 2 < x < 95.5 and G.Y0 + 2 < y < 101.0):
        return False
    ax0, ax1, ay0, ay1 = G.ANT_KEEPOUT
    if ax0 - 0.6 < x < ax1 + 0.6 and ay0 - 0.6 < y < ay1 + 0.6:
        return False
    for (l, t_, r, bo, n) in pads:
        if l - 0.45 < x < r + 0.45 and t_ - 0.45 < y < bo + 0.45:
            return False
    for (x1, y1, x2, y2, n) in tracks:
        if seg_dist(x, y, x1, y1, x2, y2) < 0.78:
            return False
    for (vx, vy) in vias:
        if (x - vx) ** 2 + (y - vy) ** 2 < 1.0:
            return False
    for (hx, hy) in holes:
        if (x - hx) ** 2 + (y - hy) ** 2 < 3.5 ** 2:
            return False
    return True


n = 0
for gx in range(0, 16):
    for gy in range(0, 19):
        x, y = 52.0 + gx * 3.0, 52.0 + gy * 3.0
        if not clear(x, y):
            continue
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        v.SetWidth(pcbnew.FromMM(G.VIA_STITCH))
        v.SetDrill(pcbnew.FromMM(G.VIA_DRILL))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetNet(gnd)
        b.Add(v)
        vias.append((x, y))
        n += 1

filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())

# ---- island rescue: pour islands survive ONLY when they serve a pad
# (the filler keeps pad-connected islands regardless of area; the rest
# are area-removed). Each unserved island therefore contains a GND SMD
# pad — drop a via-in-pad ON it (ring 0.56 << 0805 pad, so no new
# clearance interactions), tying the island to the B.Cu plane.
gnd_vias = [v.GetPosition() for v in b.GetTracks()
            if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
gnd_smd = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
            gnd_smd.append(p.GetPosition())
gnd_tht = [p.GetPosition() for fp in b.GetFootprints() for p in fp.Pads()
           if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
rescued = 0
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname() != "GND":
        continue
    polys = z.GetFilledPolysList(z.GetLayer())
    for i in range(polys.OutlineCount()):
        outline = polys.Outline(i)
        if any(outline.PointInside(p) for p in gnd_vias):
            continue
        if any(outline.PointInside(p) for p in gnd_tht):
            continue
        target = next((p for p in gnd_smd if outline.PointInside(p)), None)
        if target is None:
            continue   # padless island — the filler's area removal owns it
        v = pcbnew.PCB_VIA(b)
        v.SetPosition(target)
        v.SetWidth(pcbnew.FromMM(0.56))
        v.SetDrill(pcbnew.FromMM(G.VIA_DRILL))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetNet(gnd)
        b.Add(v)
        gnd_vias.append(target)
        rescued += 1
if rescued:
    filler.Fill(b.Zones())
b.Save(str(PCB))
print(f"stitch_and_fill: {n} GND stitch vias + {rescued} island rescues; "
      f"{len(b.Zones())} zones refilled; saved")
