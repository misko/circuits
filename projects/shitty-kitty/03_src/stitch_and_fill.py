#!/usr/bin/env python3
"""Post-route: width-floor backstop, EPAD thermal vias (U1 module, U2
driver), power-net stitch vias into the In2 pours, GND stitch grid +
pad-service vias, via janitor, zone fill, pad-bearing-island rescue.
Every via site collide-checked; FAILS (before save) if a mandatory step
comes up short. 4-layer adaptation: In1 = THE GND return plane, In2 =
power pours (VIN_12V / 5V / 3V3); through vias touch all four layers.
Derived from the crowsync-recorder (4L) + esp32-laser-timing stitchers."""
import os, sys, math
from pathlib import Path
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "shitty_kitty.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)

X0, Y0, X1, Y1 = 50.0, 50.0, 180.0, 125.0
failures = []

# In1 must be plane-clean (no tracks)
in1_tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
              and t.GetLayer() == pcbnew.In1_Cu]
if in1_tracks:
    failures.append(f"{len(in1_tracks)} tracks on In1 (GND plane must stay clean)")

# antenna guard strip (south, no vias)
u1 = b.FindFootprintByReference("U1")
_p1 = {p.GetNumber(): p.GetPosition() for p in u1.Pads() if p.GetNumber()}
ANT = (min(_p1["1"].x, _p1["40"].x) / 1e6 - 1.0,
       max(_p1["1"].x, _p1["40"].x) / 1e6 + 1.0,
       _p1["1"].y / 1e6 + 0.9)   # x0, x1, y_from (guard extends south to edge)

# pre-pass: dedupe same-net twin vias
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

stubs = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"
         and math.hypot(t.GetEnd().x - t.GetStart().x, t.GetEnd().y - t.GetStart().y) < 50000]
for t in stubs:
    b.Remove(t)
print(f"removed {len(stubs)} micro-stubs (<0.05mm)")

# width-floor backstop (EXACT nm compare — dru gotcha)
FLOOR = {"VIN_RAW": 0.3, "VIN_F": 0.3, "VIN_12V": 0.3,
         "MOT_A1": 0.35, "MOT_A2": 0.35, "MOT_B1": 0.35, "MOT_B2": 0.35,
         "BRA": 0.3, "BRB": 0.3, "5V": 0.4, "SW_BUCK": 0.4, "BST": 0.4,
         "3V3": 0.25}
lifted = 0
for tr in b.GetTracks():
    if tr.GetClass() != "PCB_TRACK":
        continue
    fl = FLOOR.get(tr.GetNetname())
    if fl and tr.GetWidth() < int(fl*1e6):
        tr.SetWidth(int(fl*1e6))
        lifted += 1
print(f"lifted {lifted} segments to class floor")

USED = {(v.GetPosition().x/1e6, v.GetPosition().y/1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
PTH = [(p.GetPosition().x/1e6, p.GetPosition().y/1e6, p.GetDrillSize().x/2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]


def try_via(net, x, y, size=0.6, drill=0.3):
    if not (X0 + 1.2 < x < X1 - 1.2 and Y0 + 1.2 < y < Y1 - 1.2):
        return False
    if ANT[0] < x < ANT[1] and y > ANT[2]:
        return False
    if any((x-ux)**2 + (y-uy)**2 < 0.75**2 for ux, uy in USED):
        return False
    if any(math.hypot(x-hx, y-hy) < r + drill/2 + 0.35 for hx, hy, r in PTH):
        return False
    if tk.via_site_ok(x, y, net.GetNetCode(), size=size, drill=drill):
        tk.add_via(x, y, net, size=size, drill=drill)
        USED.add((x, y))
        return True
    return False


# plane/pour polygons per net+layer
PLANE_POLYS = {("GND", pcbnew.In1_Cu): [[(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]]}
for z in b.Zones():
    if z.GetNetname() and not z.GetIsRuleArea():
        o = z.Outline().COutline(0)
        poly = [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())]
        for lay in z.GetLayerSet().Seq():
            PLANE_POLYS.setdefault((z.GetNetname(), lay), []).append(poly)


def _in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            inside = not inside
    return inside


def over_pour(netname, lay, x, y):
    return any(_in_poly(x, y, pp) for pp in PLANE_POLYS.get((netname, lay), []))


gnd = b.FindNet("GND")

# ---- EPAD thermal vias: U1 module EPAD (pad 41), U2 TMC2209 EP (pad 29)
for ref, padnum, grid, need in [("U1", "41", (-1.1, 0, 1.1), 4),
                                ("U2", "29", (-0.95, 0.95), 3)]:
    f = b.FindFootprintByReference(ref)
    ep = next(p for p in f.Pads() if p.GetNumber() == padnum)
    ex, ey = ep.GetPosition().x/1e6, ep.GetPosition().y/1e6
    got = 0
    for dx in grid:
        for dy in grid:
            x, y = round(ex+dx, 2), round(ey+dy, 2)
            if tk.via_site_ok(x, y, gnd.GetNetCode(), size=0.6, drill=0.3):
                tk.add_via(x, y, gnd, size=0.6, drill=0.3)
                USED.add((x, y))
                got += 1
    print(f"{ref} EPAD thermal vias: {got}")
    if got < need:
        failures.append(f"{ref} EPAD vias {got}<{need}")

def on_net_copper(netname, x, y, tol=0.30):
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


# ---- power-net stitch: vias where routed F/B copper sits over the In2 pour
POWER_JOBS = [("VIN_12V", 4), ("5V", 3), ("3V3", 4)]
for netname, need in POWER_JOBS:
    net = b.FindNet(netname)
    got = 0
    pts = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_TRACK" and t.GetNetname() == netname:
            for e in (t.GetStart(), t.GetEnd()):
                pts.append((round(e.x/1e6, 2), round(e.y/1e6, 2)))
    # SMD pads of the net too (via lands next to pad, over the pour)
    seen = set()
    for x, y in pts:
        if got >= need + 3:
            break
        if (x, y) in seen:
            continue
        seen.add((x, y))
        if over_pour(netname, pcbnew.In2_Cu, x, y) and try_via(net, x, y):
            got += 1
    if got < need:
        # ring-search around the net's pads inside the pour
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() != netname or got >= need:
                    continue
                px, py = p.GetPosition().x/1e6, p.GetPosition().y/1e6
                for ring in (1.0, 1.4, 1.8, 2.2):
                    done = False
                    for ang in range(0, 360, 30):
                        x = round(px + ring*math.cos(math.radians(ang)), 2)
                        y = round(py + ring*math.sin(math.radians(ang)), 2)
                        if over_pour(netname, pcbnew.In2_Cu, x, y) and \
                           on_net_copper(netname, x, y) and try_via(net, x, y):
                            got += 1
                            done = True
                            break
                    if done:
                        break
    print(f"{netname} pour stitch vias: {got}")
    if got < need:
        failures.append(f"{netname} pour stitch {got}<{need}")



# ---- GND stitching grid (F pour <-> In1 plane <-> B pour)
g = sum(try_via(gnd, float(gx), float(gy))
        for gx in range(53, 178, 8) for gy in range(53, 123, 8))
print(f"GND grid: {g} vias")
if g < 60:
    failures.append(f"GND grid too sparse: {g}")

# ---- GND pad service: every GND SMD pad gets a via within 2.5mm
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
    for ring in (0.8, 1.0, 1.3, 1.7, 2.1):
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


def _seg_d2(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx + (py-ay)*dy) / L2))
    return (px - ax - t*dx)**2 + (py - ay - t*dy)**2


def via_attach_layers(v):
    """Layers where the via meets same-net copper: tracks, pads, pours/planes."""
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
                bb = p.GetBoundingBox()
                bb.Inflate(v.GetWidth() // 2)
                if bb.Contains(v.GetPosition()):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
    for (znet, zlay), polys in PLANE_POLYS.items():
        if znet == nn and any(_in_poly(vx, vy, poly) for poly in polys):
            attach.add(zlay)
    return attach


orphans = [v for v in b.GetTracks() if v.GetClass() == "PCB_VIA"
           and len(via_attach_layers(v)) < 2]
for v in orphans:
    b.Remove(v)
print(f"via janitor removed {len(orphans)}")

# ---- fill, then rescue GND pad-bearing islands (F/B pours; In1 is whole)
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
via_by_net = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        via_by_net.setdefault(t.GetNetname(), []).append(t.GetPosition())
added = 0
for z in b.Zones():
    nn = z.GetNetname()
    if not nn or z.GetIsRuleArea() or nn != "GND":
        continue
    for lay in z.GetLayerSet().Seq():
        if lay == pcbnew.In1_Cu:
            continue
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            bb = o.BBox()
            if bb.GetWidth() < 8e5 or bb.GetHeight() < 8e5:
                continue
            if any(o.PointInside(p) for p in via_by_net.get(nn, [])):
                continue
            placed = False
            for fx in range(2, 19, 2):
                for fy in range(2, 19, 2):
                    x = bb.GetLeft() + bb.GetWidth()*fx//20
                    y = bb.GetTop() + bb.GetHeight()*fy//20
                    if not o.PointInside(pcbnew.VECTOR2I(x, y)):
                        continue
                    if try_via(gnd, round(x/1e6, 2), round(y/1e6, 2)):
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
                    px, py = p2.GetPosition().x/1e6, p2.GetPosition().y/1e6
                    cands = []
                    for v2 in b.GetTracks():
                        if v2.GetClass() == "PCB_VIA" and v2.GetNetname() == nn:
                            qx, qy = v2.GetPosition().x/1e6, v2.GetPosition().y/1e6
                            cands.append((math.hypot(px-qx, py-qy), qx, qy))
                    for fp3 in b.GetFootprints():
                        for p3 in fp3.Pads():
                            if p3.GetNetname() == nn and p3 is not p2 and not o.PointInside(p3.GetPosition()):
                                qx, qy = p3.GetPosition().x/1e6, p3.GetPosition().y/1e6
                                cands.append((math.hypot(px-qx, py-qy), qx, qy))
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
print(f"island stitch vias/rescues: {added}")

# ---- post-fill dangling-via cleanup (attach must include filled polys)
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
    attach = via_attach_layers(v) - {lay for (zn, lay) in PLANE_POLYS if zn == nn}
    for (znet, zlay), plist in fill_polys.items():
        if znet == nn and any(pl.Contains(pos) for pl in plist):
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
