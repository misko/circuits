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

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crow_array_pod.kicad_pcb")
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
    if any((x - ux) ** 2 + (y - uy) ** 2 < 0.75 ** 2 for ux, uy in USED):
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
                    if rescued:
                        added += 1
                    else:
                        failures.append(f"GND island ({bb.GetLeft()/1e6:.1f},{bb.GetTop()/1e6:.1f}) unstitchable")
print(f"island stitch vias: {added}")

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
