#!/usr/bin/env python3
"""Post-route: stitch vias (GND grid, power-island clusters), via janitor,
zone fill, pad-bearing-island rescue. Every via site collide-checked; the
script FAILS (before save) if a mandatory cluster comes up short.
Derived from the usb-power-3s stitcher (2026-07), simplified: this board
has no F.Cu power pours — power is routed copper + In2 islands."""
import os, sys, math
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "crowsync_recorder.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)

X0, Y0, X1, Y1 = 50.0, 50.0, 115.0, 92.0
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
        if j not in dead and n1 == n2 and abs(x1-x2) < 450000 and abs(y1-y2) < 450000:
            dead.add(j)
for j in dead:
    b.Remove(vinfo[j][0])
print(f"deduped {len(dead)} twin vias")

# pre-pass: lift sub-floor segments of PWR-class nets to 0.3 (dru floor)
PWR_FLOOR = {"VBUS_5V": 0.3, "VBUS_PCM": 0.3, "3V3A": 0.3, "MIC_BIAS_F": 0.3}
lifted = 0
for tr in b.GetTracks():
    if tr.GetClass() != "PCB_TRACK":
        continue
    fl = PWR_FLOOR.get(tr.GetNetname())
    if fl and tr.GetWidth() < int(fl*1e6) - 1000:
        tr.SetWidth(int(fl*1e6))
        lifted += 1
print(f"lifted {lifted} PWR segments to floor")

USED = {(v.GetPosition().x/1e6, v.GetPosition().y/1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
PTH = [(p.GetPosition().x/1e6, p.GetPosition().y/1e6, p.GetDrillSize().x/2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]

def try_via(net, x, y, size=0.6, drill=0.3):
    if not (X0 + 1.2 < x < X1 - 1.2 and Y0 + 1.2 < y < Y1 - 1.2):
        return False
    if any((x-ux)**2 + (y-uy)**2 < 0.55**2 for ux, uy in USED):
        return False
    if any(math.hypot(x-hx, y-hy) < r + drill/2 + 0.3 for hx, hy, r in PTH):
        return False
    if tk.via_site_ok(x, y, net.GetNetCode(), size=size, drill=drill):
        tk.add_via(x, y, net, size=size, drill=drill)
        USED.add((x, y))
        return True
    if tk.via_site_ok(x, y, net.GetNetCode(), size=0.45, drill=0.2, hole_to_copper=0.14):
        tk.add_via(x, y, net, size=0.45, drill=0.2)
        USED.add((x, y))
        return True
    return False

# In2 island polygons per net (a power via only helps over its island)
PLANE_POLYS = {"GND": [[(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]]}
for z in b.Zones():
    if z.GetLayerSet().Contains(pcbnew.In2_Cu) and z.GetNetname():
        o = z.Outline().COutline(0)
        PLANE_POLYS.setdefault(z.GetNetname(), []).append(
            [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())])

def _in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            inside = not inside
    return inside

def over_plane(netname, x, y):
    if netname not in PLANE_POLYS:
        return False
    return any(_in_poly(x, y, pp) for pp in PLANE_POLYS[netname])

# a power via must land ON the routed copper of its net (track pass-through)
def on_net_track(netname, x, y, tol=0.30):
    for t in b.GetTracks():
        if t.GetClass() != "PCB_TRACK" or t.GetNetname() != netname:
            continue
        sx, sy = t.GetStart().x/1e6, t.GetStart().y/1e6
        ex, ey = t.GetEnd().x/1e6, t.GetEnd().y/1e6
        dx, dy = ex-sx, ey-sy
        L2 = dx*dx + dy*dy
        tt = 0 if L2 == 0 else max(0, min(1, ((x-sx)*dx + (y-sy)*dy) / L2))
        if math.hypot(x - sx - tt*dx, y - sy - tt*dy) <= tol + t.GetWidth()/2e6:
            return True
    return False

# ---- power-net stitch: for each PWR net, drop vias where its routed F/B
# copper crosses its In2 island (>= need per net or FAIL)
POWER_JOBS = [("VBUS_5V", 3), ("3V3A", 3)]
for netname, need in POWER_JOBS:
    net = b.FindNet(netname)
    got = 0
    pts = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname:
            for e in (t.GetStart(), t.GetEnd()):
                pts.append((round(e.x/1e6, 2), round(e.y/1e6, 2)))
    for x, y in pts:
        if got >= need + 2:
            break
        if over_plane(netname, x, y) and try_via(net, x, y):
            got += 1
    # fallback ring around each pad of the net
    if got < need:
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() != netname:
                    continue
                px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6
                for ring in (0.8, 1.2, 1.6):
                    for ang in range(0, 360, 30):
                        x = round(px + ring*math.cos(math.radians(ang)), 2)
                        y = round(py + ring*math.sin(math.radians(ang)), 2)
                        if over_plane(netname, x, y) and on_net_track(netname, x, y) and try_via(net, x, y):
                            got += 1
                            break
                    else:
                        continue
                    break
    print(f"{netname}: {got} stitch vias (need {need})")
    if got < need:
        failures.append(f"power stitch {netname}: {got}<{need}")

# ---- GND stitching grid (F pour <-> In1 plane <-> B pour)
gnd = b.FindNet("GND")
g = sum(try_via(gnd, float(gx), float(gy)) for gx in range(53, 114, 7) for gy in range(53, 91, 7))
print(f"GND grid: {g} vias")
if g < 30:
    failures.append(f"GND grid too sparse: {g}")

# ---- GND pad service: every GND pad gets a via within 2.5mm (return path)
pads_gnd = [(fp.GetReference(), p) for fp in b.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == "GND" and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
via_pts = [(v.GetPosition().x/1e6, v.GetPosition().y/1e6)
           for v in b.GetTracks() if v.GetClass() == "PCB_VIA" and v.GetNetname() == "GND"]
added = 0
for ref, p in pads_gnd:
    px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6
    if any(math.hypot(px-vx, py-vy) < 2.5 for vx, vy in via_pts):
        continue
    done = False
    for ring in (0.7, 0.9, 1.2, 1.6, 2.0):
        for ang in range(0, 360, 30):
            x = round(px + ring*math.cos(math.radians(ang)), 2)
            y = round(py + ring*math.sin(math.radians(ang)), 2)
            if try_via(gnd, x, y):
                via_pts.append((x, y))
                added += 1
                done = True
                break
        if done:
            break
print(f"GND pad-service vias: {added}")

# ---- via janitor: remove vias with same-net copper on < 2 layers
def _seg_d2(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L2))
    return (px - ax - t*dx)**2 + (py - ay - t*dy)**2

_ztmp = {}
for z in b.Zones():
    if z.GetNetname() and not z.GetIsRuleArea():
        o = z.Outline().COutline(0)
        poly = [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())]
        for lay in z.GetLayerSet().Seq():
            _ztmp.setdefault((z.GetNetname(), lay), []).append(poly)

_orphans = []
for v in [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]:
    nn = v.GetNetname()
    vx, vy = v.GetPosition().x/1e6, v.GetPosition().y/1e6
    r2 = (v.GetWidth()/2e6) ** 2
    attach = set()
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or t.GetNetCode() != v.GetNetCode():
            continue
        if _seg_d2(vx, vy, t.GetStart().x/1e6, t.GetStart().y/1e6,
                   t.GetEnd().x/1e6, t.GetEnd().y/1e6) <= r2:
            attach.add(t.GetLayer())
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetCode() == v.GetNetCode():
                pp = p.GetPosition()
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if abs(pp.x/1e6-vx) < 2.0 and abs(pp.y/1e6-vy) < 2.0 and bb.Contains(v.GetPosition()):
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

# ---- fill, then stitch any pad-bearing island without a via of its net
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
        if lay not in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu):
            continue
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            bb = o.BBox()
            if bb.GetWidth() < 8e5 or bb.GetHeight() < 8e5:
                continue
            if any(o.PointInside(p) for p in via_by_net.get(nn, [])):
                continue
            has_pad = any(o.PointInside(p2.GetPosition()) for fp2 in b.GetFootprints()
                          for p2 in fp2.Pads() if p2.GetNetname() == nn)
            # try to stitch (needed for pad-bearing islands; harmless else)
            placed = False
            for fx in range(2, 19, 2):
                for fy in range(2, 19, 2):
                    x = bb.GetLeft() + bb.GetWidth()*fx//20
                    y = bb.GetTop() + bb.GetHeight()*fy//20
                    if not o.PointInside(pcbnew.VECTOR2I(x, y)):
                        continue
                    xm, ym = round(x/1e6, 2), round(y/1e6, 2)
                    if nn != "GND" and not over_plane(nn, xm, ym) and lay == pcbnew.In2_Cu:
                        continue
                    if try_via(b.FindNet(nn), xm, ym):
                        via_by_net.setdefault(nn, []).append(pcbnew.VECTOR2I(x, y))
                        added += 1
                        placed = True
                        break
                if placed:
                    break
            if not placed and has_pad:
                failures.append(f"island {nn}/{pcbnew.BOARD.GetStandardLayerName(lay)} "
                                f"({bb.GetLeft()/1e6:.1f},{bb.GetTop()/1e6:.1f}) unstitchable")
print(f"island stitch vias: {added}")

if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
filler.Fill(b.Zones())
b.Save(PCB)
print("filled + saved")
