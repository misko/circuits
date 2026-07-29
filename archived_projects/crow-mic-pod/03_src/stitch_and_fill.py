#!/usr/bin/env python3
"""Post-route: width-floor backstop, GND stitch grid + pad-service vias,
via janitor, zone fill, pad-bearing-island rescue. Every via site
collide-checked; FAILS (before save) if a mandatory step comes up short.
Adapted from the esp32-laser-timing stitcher (2-layer: B.Cu pour = THE
return plane)."""
import math
import os
import sys
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_mic_pod.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)

X0, Y0, X1, Y1 = 50.0, 50.0, 144.5, 94.5
RCUT = 6.25
failures = []

# pre-pass: dedupe same-net twin vias from pass chaining
vinfo = [(t, t.GetNetCode(), t.GetPosition().x, t.GetPosition().y)
         for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
dead = set()
for i, (v1, n1, x1, y1) in enumerate(vinfo):
    if i in dead:
        continue
    for j in range(i + 1, len(vinfo)):
        v2, n2, x2, y2 = vinfo[j]
        if j not in dead and n1 == n2 and abs(x1 - x2) < 450000 and abs(y1 - y2) < 450000:
            dead.add(j)
for j in dead:
    b.Remove(vinfo[j][0])
print(f"deduped {len(dead)} twin vias")

# remove zero-length stub artifacts
stubs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
         and math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) < 50000]
for t in stubs:
    b.Remove(t)
print(f"removed {len(stubs)} micro-stubs (<0.05mm)")

# dedupe exact-duplicate track segments (v1.1: KRT emitted a 0.1mm A_OUT
# stub TWICE — each twin "touches" the other, hiding both from the
# dangling check while DRC still flags the stacked free end)
seen = set()
dups = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK":
        continue
    s, e = t.GetStart(), t.GetEnd()
    key = (t.GetNetCode(), t.GetLayer(), t.GetWidth(),
           min((s.x, s.y), (e.x, e.y)), max((s.x, s.y), (e.x, e.y)))
    if key in seen:
        dups.append(t)
    else:
        seen.add(key)
for t in dups:
    b.Remove(t)
print(f"removed {len(dups)} duplicate segments")

# remove short WHISKER stubs (<=0.3mm KRT litter; v1.1: a 0.1mm A_OUT tail
# tripped track_dangling). A whisker has one end EXACTLY anchored on a
# node and a free end whose only copper overlaps are with items already
# present at that same node — removal cannot break continuity. Bridges
# whose ends overlap-connect DIFFERENT items are load-bearing and stay.
# NB: `t2 is me` NEVER matches (GetTracks() yields fresh SWIG proxies) —
# compare m_Uuid.
def _seg_pt_d(pt, a, bpt):
    ax, ay, bx, by = a.x, a.y, bpt.x, bpt.y
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t_ = 0 if L2 == 0 else max(0.0, min(1.0, ((pt.x - ax) * dx + (pt.y - ay) * dy) / L2))
    return math.hypot(pt.x - ax - t_ * dx, pt.y - ay - t_ * dy)


def _exact_items(pt, net, me_uuid, pad_acc):
    """pad_acc: pad HitTest accuracy (nm) — a stub end sitting ON a pad
    EDGE is still electrically the pad tap (v1.1: an AUDIO_P tap whose end
    grazed R13.2's edge was removed as a 'whisker', breaking the net)."""
    out = set()
    for t2 in b.GetTracks():
        if t2.m_Uuid == me_uuid or t2.GetNetCode() != net:
            continue
        if t2.GetClass() == "PCB_VIA":
            if (t2.GetPosition() - pt).EuclideanNorm() <= 1000:
                out.add(t2.m_Uuid.AsString())
        elif (t2.GetStart() - pt).EuclideanNorm() <= 1000 \
                or (t2.GetEnd() - pt).EuclideanNorm() <= 1000:
            out.add(t2.m_Uuid.AsString())
    for fp2 in b.GetFootprints():
        for p2 in fp2.Pads():
            if p2.GetNetCode() == net and p2.HitTest(pt, pad_acc):
                out.add(f"{fp2.GetReference()}.{p2.GetNumber()}")
    return out


def _overlap_items(pt, net, me_uuid, pad_acc):
    out = set()
    for t2 in b.GetTracks():
        if t2.m_Uuid == me_uuid or t2.GetNetCode() != net:
            continue
        if t2.GetClass() == "PCB_VIA":
            if (t2.GetPosition() - pt).EuclideanNorm() <= t2.GetWidth() // 2:
                out.add(t2.m_Uuid.AsString())
        elif _seg_pt_d(pt, t2.GetStart(), t2.GetEnd()) <= t2.GetWidth() / 2:
            out.add(t2.m_Uuid.AsString())
    for fp2 in b.GetFootprints():
        for p2 in fp2.Pads():
            if p2.GetNetCode() == net and p2.HitTest(pt, pad_acc):
                out.add(f"{fp2.GetReference()}.{p2.GetNumber()}")
    return out


dang = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK":
        continue
    if math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) > 300000:
        continue
    net, uu, acc = t.GetNetCode(), t.m_Uuid, t.GetWidth() // 2
    for anchor, free in ((t.GetStart(), t.GetEnd()), (t.GetEnd(), t.GetStart())):
        exact_a = _exact_items(anchor, net, uu, acc)
        if not exact_a or _exact_items(free, net, uu, acc):
            continue
        # safe to drop if everything the free end touches is ALSO touched
        # from the anchor node (exactly or by overlap) — the cluster stays
        # connected without this segment (v1.1: T-span case at U1's A_OUT)
        if _overlap_items(free, net, uu, acc) <= \
                (exact_a | _overlap_items(anchor, net, uu, acc)):
            dang.append(t)
            break
for t in dang:
    b.Remove(t)
print(f"removed {len(dang)} short dangling whiskers")

# pre-pass: lift sub-floor segments to their class floors (dru backstop)
FLOOR = {"5V": 0.4, "5VF": 0.4, "BEEP_5V": 0.4, "BZ_P": 0.4, "BEEP_RET": 0.4,
         "AUDIO_P": 0.3, "AUDIO_N": 0.3, "AUD_P_I": 0.3, "AUD_N_I": 0.3,
         "A_OUT": 0.3, "B_OUT": 0.3, "VMID": 0.3}
lifted = 0
for tr in b.GetTracks():
    if tr.GetClass() != "PCB_TRACK":
        continue
    fl = FLOOR.get(tr.GetNetname())
    if fl and tr.GetWidth() < int(fl * 1e6):  # EXACT nm compare (dru gotcha)
        tr.SetWidth(int(fl * 1e6))
        lifted += 1
print(f"lifted {lifted} segments to class floor")

USED = {(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
PTH = [(p.GetPosition().x / 1e6, p.GetPosition().y / 1e6, p.GetDrillSize().x / 2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]


def in_corner(x, y):
    return any(math.hypot(x - cx, y - cy) < RCUT + 1.0
               for cx, cy in [(X0, Y0), (X1, Y0), (X0, Y1), (X1, Y1)])


def try_via(net, x, y, size=0.6, drill=0.3):
    if not (X0 + 1.2 < x < X1 - 1.2 and Y0 + 1.2 < y < Y1 - 1.2):
        return False
    if in_corner(x, y):
        return False
    # 0.85 spacing: hole_to_hole floor is 0.5 = 0.3 drill + margin (v1.1:
    # a 0.75-spaced grid via landed 0.46 from a KRT via's hole)
    if any((x - ux) ** 2 + (y - uy) ** 2 < 0.85 ** 2 for ux, uy in USED):
        return False
    if any(math.hypot(x - hx, y - hy) < r + drill / 2 + 0.75 for hx, hy, r in PTH):
        return False
    if tk.via_site_ok(x, y, net.GetNetCode(), size=size, drill=drill):
        tk.add_via(x, y, net, size=size, drill=drill)
        USED.add((x, y))
        return True
    return False


def _in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


gnd = b.FindNet("GND")

# ---- GND stitching grid (F pour <-> B pour)
g = sum(try_via(gnd, float(gx), float(gy))
        for gx in range(53, 143, 6) for gy in range(53, 93, 6))
print(f"GND grid: {g} vias")
if g < 40:
    failures.append(f"GND grid too sparse: {g}")

# ---- GND pad service: every GND SMD pad gets a via within 2.5mm
pads_gnd = [(fp.GetReference(), p) for fp in b.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
via_pts = [(v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
           for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
added = 0
for ref, p in pads_gnd:
    px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
    if any(math.hypot(px - vx, py - vy) < 2.5 for vx, vy in via_pts):
        continue
    done = False
    for ring in (0.8, 1.0, 1.3, 1.7, 2.1):
        for ang in range(0, 360, 30):
            x = round(px + ring * math.cos(math.radians(ang)), 2)
            y = round(py + ring * math.sin(math.radians(ang)), 2)
            if try_via(gnd, x, y):
                via_pts.append((x, y))
                added += 1
                done = True
                break
        if done:
            break
print(f"GND pad-service vias: {added}")


def _seg_d2(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return (px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2


# ---- via janitor: remove vias with same-net copper on < 2 layers
_ztmp = {}
for z in b.Zones():
    if z.GetNetname() and not z.GetIsRuleArea():
        o = z.Outline().COutline(0)
        poly = [(o.CPoint(i).x / 1e6, o.CPoint(i).y / 1e6) for i in range(o.PointCount())]
        for lay in z.GetLayerSet().Seq():
            _ztmp.setdefault((z.GetNetname(), lay), []).append(poly)

_orphans = []
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    nn = v.GetNetname()
    vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
    r2 = (v.GetWidth() / 2e6) ** 2
    attach = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
            continue
        if _seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                   t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= r2:
            attach.add(t.GetLayer())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == v.GetNetCode():
                pp = p.GetPosition()
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if abs(pp.x / 1e6 - vx) < 2.5 and abs(pp.y / 1e6 - vy) < 2.5 and bb.Contains(v.GetPosition()):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
    for (znet, zlay), polys in _ztmp.items():
        if znet == nn and any(_in_poly(vx, vy, poly) for poly in polys):
            attach.add(zlay)
    if len(attach) < 2:
        _orphans.append((v, nn, round(vx, 2), round(vy, 2)))
for v, nn, vx, vy in _orphans:
    b.Remove(v)
print(f"via janitor removed {len(_orphans)}: {[(n, x, y) for _, n, x, y in _orphans][:10]}")

# ---- fill, then stitch any pad-bearing GND island without continuity
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
# per-layer MAIN GND fill outlines (area > 20mm2): used for barrel credit
main_fill = {}
for z2 in b.Zones():
    if z2.GetNetname() != "GND" or z2.GetIsRuleArea():
        continue
    for lay2 in z2.GetLayerSet().Seq():
        pl2 = z2.GetFilledPolysList(lay2)
        for k2 in range(pl2.OutlineCount()):
            o2 = pl2.Outline(k2)
            if o2.BBox().GetWidth() * o2.BBox().GetHeight() > int(20e12):
                main_fill.setdefault(lay2, []).append(o2)
via_by_net = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        via_by_net.setdefault(t.GetNetname(), []).append(t.GetPosition())
added = 0
for z in b.Zones():
    nn = z.GetNetname()
    if not nn or z.GetIsRuleArea():
        continue
    for lay in z.GetLayerSet().Seq():
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            bb = o.BBox()
            if bb.GetWidth() < 8e5 or bb.GetHeight() < 8e5:
                continue
            if nn == "GND" and not any(o.PointInside(p) for p in via_by_net.get(nn, [])):
                placed = False
                for fx in range(2, 19, 2):
                    for fy in range(2, 19, 2):
                        x = bb.GetLeft() + bb.GetWidth() * fx // 20
                        y = bb.GetTop() + bb.GetHeight() * fy // 20
                        if not o.PointInside(pcbnew.VECTOR2I(x, y)):
                            continue
                        if try_via(gnd, round(x / 1e6, 2), round(y / 1e6, 2)):
                            via_by_net.setdefault(nn, []).append(pcbnew.VECTOR2I(x, y))
                            added += 1
                            placed = True
                            break
                    if placed:
                        break
                if not placed:
                    inside = [p2 for fp2 in b.GetFootprints() for p2 in fp2.Pads()
                              if p2.GetNetname() == nn and o.PointInside(p2.GetPosition())]
                    if not inside:
                        continue
                    # barrel credit (v1.1): if a THT pad in this island has
                    # its OTHER-layer copper inside the main pour, the pad
                    # barrel already bonds the island — no rescue needed.
                    # (Pad 8's cluster fails this: BOTH layers are islands.)
                    other_lay = pcbnew.B_Cu if lay == pcbnew.F_Cu else pcbnew.F_Cu
                    if any(p2.GetDrillSize().x > 0 and
                           any(o2.PointInside(p2.GetPosition())
                               for o2 in main_fill.get(other_lay, []))
                           for p2 in inside):
                        continue
                    rescued = False
                    for p2 in inside:
                        px, py = p2.GetPosition().x / 1e6, p2.GetPosition().y / 1e6
                        cands = []
                        for v2 in b.GetTracks():
                            if v2.GetClass() == "PCB_VIA" and v2.GetNetname() == nn:
                                qx, qy = v2.GetPosition().x / 1e6, v2.GetPosition().y / 1e6
                                cands.append((math.hypot(px - qx, py - qy), qx, qy))
                        for fp3 in b.GetFootprints():
                            for p3 in fp3.Pads():
                                if p3.GetNetname() == nn and p3 is not p2 and not o.PointInside(p3.GetPosition()):
                                    qx, qy = p3.GetPosition().x / 1e6, p3.GetPosition().y / 1e6
                                    cands.append((math.hypot(px - qx, py - qy), qx, qy))
                        for dqq, qx, qy in sorted(cands)[:8]:
                            if dqq > 4.0:
                                break
                            if not tk.collides(px, py, qx, qy, 0.3, p2.GetNetCode(), lay):
                                tk.add_seg(px, py, qx, qy, b.FindNet(nn), lay, 0.3)
                                rescued = True
                                break
                        if rescued:
                            break
                    # strap rescue (v1.1): the RJ45 GND tails sit in a hole
                    # field where neither a via nor a <=4mm via/pad candidate
                    # exists — ring-sample points inside a LARGE same-layer
                    # GND outline (the main pour) and lay a collision-checked
                    # 0.3mm strap from the trapped pad into it.
                    if not rescued:
                        bigs = [polys.Outline(k) for k in range(polys.OutlineCount())
                                if k != i and polys.Outline(k).BBox().GetWidth() *
                                polys.Outline(k).BBox().GetHeight() > int(20e12)]
                        for p2 in inside:
                            px, py = p2.GetPosition().x / 1e6, p2.GetPosition().y / 1e6
                            for ring in [1.0 + 0.5 * k for k in range(9)]:
                                for ang in range(0, 360, 15):
                                    qx = round(px + ring * math.cos(math.radians(ang)), 2)
                                    qy = round(py + ring * math.sin(math.radians(ang)), 2)
                                    qpt = pcbnew.VECTOR2I_MM(qx, qy)
                                    if not any(bo.PointInside(qpt) for bo in bigs):
                                        continue
                                    if tk.collides(px, py, qx, qy, 0.3, p2.GetNetCode(), lay):
                                        continue
                                    tk.add_seg(px, py, qx, qy, b.FindNet(nn), lay, 0.3)
                                    rescued = True
                                    break
                                if rescued:
                                    break
                            if rescued:
                                break
                    # last resort (v1.1): verified A* from the trapped pad
                    # to a nearby GND via — the RJ45 tail field leaves no
                    # STRAIGHT corridor, but a maze path exists. Vias the
                    # A* drops are pinned to the 0.6/0.3 standard tier.
                    if not rescued:
                        _av, _vs = tk.add_via, tk.via_site_ok

                        def _site_guard(x, y):
                            """try_via's own discipline for A*-dropped vias:
                            no stacking on existing vias, no PTH-hole graze
                            (via_site_ok skips same-net copper — the trap)."""
                            allv = {(t.GetPosition().x / 1e6, t.GetPosition().y / 1e6)
                                    for t in b.GetTracks() if t.GetClass() == "PCB_VIA"}
                            if any((x - ux) ** 2 + (y - uy) ** 2 < 0.85 ** 2 for ux, uy in allv):
                                return False
                            if any(math.hypot(x - hx, y - hy) < r + 0.15 + 0.75 for hx, hy, r in PTH):
                                return False
                            return True
                        tk.add_via = lambda x, y, net, size=0.6, drill=0.3: _av(x, y, net, 0.6, 0.3)
                        tk.via_site_ok = (lambda x, y, nc, size=0.6, drill=0.3, **kw:
                                          _site_guard(x, y) and _vs(x, y, nc, size=0.6, drill=0.3, **kw))
                        try:
                            gvias = sorted(
                                ((math.hypot(px - v.GetPosition().x / 1e6, py - v.GetPosition().y / 1e6),
                                  v.GetPosition().x / 1e6, v.GetPosition().y / 1e6)
                                 for v in b.GetTracks()
                                 if v.GetClass() == "PCB_VIA" and v.GetNetname() == nn))
                            for p2 in inside:
                                px, py = p2.GetPosition().x / 1e6, p2.GetPosition().y / 1e6
                                for _d, qx, qy in gvias[:4]:
                                    if tk.verified_astar(nn, (px, py), (qx, qy), 0.3,
                                                         grid=0.1, viacost=40, window=3.0):
                                        rescued = True
                                        break
                                if rescued:
                                    break
                        finally:
                            tk.add_via, tk.via_site_ok = _av, _vs
                    if rescued:
                        added += 1
                    else:
                        failures.append(f"GND island ({bb.GetLeft()/1e6:.1f},{bb.GetTop()/1e6:.1f}) unstitchable")
print(f"island stitch vias: {added}")

# ---- bridge via-to-pad fill necks: a KRT via parked just off a same-net
# SMD pad leaves a sub-min copper neck between the two (v1.1: B_OUT via
# 0.10mm neck at U1 pad 7). A direct collision-checked 0.3mm stub makes
# the connection full-width; same-net overlap is free.
bridged = 0
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    vx, vy = v.GetPosition().x / 1e6, v.GetPosition().y / 1e6
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() != v.GetNetCode() or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            d = math.hypot(px - vx, py - vy)
            if 0.1 < d < 1.6:
                play = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
                bw = max(0.3, FLOOR.get(v.GetNetname(), 0.3))  # class floor (dru)
                if not tk.collides(vx, vy, px, py, bw, v.GetNetCode(), play):
                    tk.add_seg(vx, vy, px, py, b.FindNet(v.GetNetname()), play, bw)
                    bridged += 1
print(f"via-to-pad neck bridges: {bridged}")

# ---- post-fill dangling-via cleanup
filler.Fill(b.Zones())
fill_polys = {}
for z in b.Zones():
    if z.GetIsRuleArea() or not z.GetNetname():
        continue
    for lay in z.GetLayerSet().Seq():
        fill_polys.setdefault((z.GetNetname(), lay), []).append(z.GetFilledPolysList(lay))
removed = 0
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    nn = v.GetNetname()
    pos = v.GetPosition()
    vx, vy = pos.x / 1e6, pos.y / 1e6
    r2 = (v.GetWidth() / 2e6) ** 2
    attach = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
            continue
        if _seg_d2(vx, vy, t.GetStart().x / 1e6, t.GetStart().y / 1e6,
                   t.GetEnd().x / 1e6, t.GetEnd().y / 1e6) <= r2:
            attach.add(t.GetLayer())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == v.GetNetCode():
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if bb.Contains(pos):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
    for (znet, zlay), plist in fill_polys.items():
        if znet == nn and zlay not in attach:
            if any(pl.Contains(pos) for pl in plist):
                attach.add(zlay)
    if len(attach) < 2:
        b.Remove(v)
        removed += 1
print(f"post-fill dangling-via cleanup removed {removed}")

if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
filler.Fill(b.Zones())
b.Save(PCB)
print("filled + saved")
