#!/usr/bin/env python3
"""Post-route: stitch F.Cu power pours to their In2 planes, rescue pads
swallowed inside differently-netted pours, GND grid, fill zones.
Every via site collide-checked; script FAILS (before save) if any rescue
or mandatory cluster comes up short."""
import os, sys, math
from pathlib import Path
# skills scripts: repo-relative first (standalone clone), else machine-global
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "usb_power_3s.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.15)

# pre-pass 1: KRT pass-chaining leaves same-net twin vias ~0.3mm apart (h2h fail)
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
# pre-pass 2b: KRT tap segments east of the tap areas must meet class floors
FLOOR = {"SW_A": 0.3, "SW_B": 0.3, "VBATT_RAW": 0.25, "VBATT_F": 0.25,
         "FE_MID": 0.25, "VSW": 0.25, "5V_A": 0.25, "5V_C": 0.25}
for tr in b.GetTracks():
    if tr.GetClass() != "PCB_TRACK":
        continue
    fl = FLOOR.get(tr.GetNetname())
    if fl and tr.GetWidth() < int(fl*1e6) - 1000:
        if min(tr.GetStart().x, tr.GetEnd().x) > int(93.5e6):
            tr.SetWidth(int(fl*1e6))
# pre-pass 2c: KRT left the ILIM1 tail overshooting R16.1 by 1.5mm with a free
# end; retarget the endpoint onto the pad center
for tr in b.GetTracks():
    if tr.GetClass() == "PCB_TRACK" and tr.GetNetname() == "ILIM1":
        for get, set_ in ((tr.GetStart, tr.SetStart), (tr.GetEnd, tr.SetEnd)):
            p = get()
            if abs(p.x - int(121.2e6)) < 5000 and abs(p.y - int(62.0e6)) < 5000:
                set_(pcbnew.VECTOR2I_MM(121.49, 63.5))
# pre-pass 2: KRT emitted one 0.088mm HG_FE segment; lift to 0.13
for tr in b.GetTracks():
    if tr.GetClass() == "PCB_TRACK" and tr.GetWidth() < 90000:
        tr.SetWidth(130000)

USED = {(v.GetPosition().x/1e6, v.GetPosition().y/1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"}
# PTH drill guard: via_site_ok skips same-net copper, so a via can land
# overlapping a same-net PTH HOLE (fuse clip, found 2026-07-16). Track all
# plated holes and enforce hole-edge to hole-edge >= 0.3 ourselves.
PTH = [(p.GetPosition().x/1e6, p.GetPosition().y/1e6, p.GetDrillSize().x/2e6)
       for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]
failures = []

def try_via(net, x, y, size=0.6, drill=0.3):
    # via_site_ok SKIPS same-net copper, so it approves a via stacked on an
    # identical via - dedupe by coordinate ourselves (found 2026-07-16).
    # Falls back to the 0.45/0.2 advanced-tier via in tight spots.
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

PLANE_POLYS = {"GND": [[(51, 51), (149, 51), (149, 109), (51, 109)]]}

def _in_poly0(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            inside = not inside
    return inside

for z in b.Zones():
    if z.GetLayerSet().Contains(pcbnew.In2_Cu) and z.GetNetname():
        o = z.Outline().COutline(0)
        PLANE_POLYS.setdefault(z.GetNetname(), []).append(
            [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())])

def over_plane(netname, x, y):
    if netname not in PLANE_POLYS:
        return True  # pour-to-pour bond (SW bridges): no plane involved
    return any(_in_poly0(x, y, pp) for pp in PLANE_POLYS[netname])

def cluster(netname, cx, cy, n, size=0.6, drill=0.3):
    net = b.FindNet(netname)
    placed = 0
    for ring in [0.8 * k for k in range(1, 10)]:
        for ang in range(0, 360, 45):
            if placed >= n:
                return placed
            x = round(cx + ring * math.cos(math.radians(ang)), 2)
            y = round(cy + ring * math.sin(math.radians(ang)), 2)
            if over_plane(netname, x, y) and try_via(net, x, y, size, drill):
                placed += 1
        if placed >= n:
            break
    return placed

# ---- pour -> plane stitch clusters (VSW/5V_C/5V_A have In2 planes)
JOBS = [("VSW", 84.5, 73.5, 6),    # FE output pour -> VSW plane
        ("VSW", 84.5, 86.0, 4),    # FE output pour, south end
        ("VSW", 84.0, 53.3, 3),    # R4/R5 tap strip
        ("VBATT_F", 56.5, 96.5, 3),  # D1/C15 arm -> In2 island
        ("5V_C", 112.0, 57.5, 6),  # LA1 out -> 5V_C plane
        ("5V_C", 126.5, 57.5, 4),  # near USB-C
        ("5V_A", 112.0, 98.5, 6),  # LB1 out -> 5V_A plane
        ("5V_A", 124.0, 95.5, 4),  # near TPS bank
        ("5V_A", 116.5, 90.0, 2),  # CB7 lobe
        ("5V_A", 124.5, 66.0, 2), ("5V_A", 124.5, 83.5, 2)]  # TPS IN pours
for netname, x, y, n in JOBS:
    got = cluster(netname, x, y, n)
    print(f"{netname} @({x},{y}): {got}/{n} vias")
    if got < (n + 1) // 2:
        failures.append(f"cluster {netname}@({x},{y}) {got}/{n}")

# ---- explicit via ladders (fixed sites, current-carrying necks)
EXPLICIT = [
    # Q2 source patch (VSW, 8A FE output) -> In2 VSW plane; gate pad + HG_FE
    # traces cross y85, so sites live north and at the far south end
    ("VSW", [(74.45, 81.0), (74.45, 81.8), (74.45, 82.6), (74.45, 85.6),
             (74.45, 86.4), (74.45, 87.2), (74.45, 88.0), (74.45, 88.7)], 4),
    # VBATT_F In2 island -> F.Cu pour, south of the F1 input clips (y66)
    ("VBATT_F", [(62.0, 69.3), (63.4, 69.3), (64.8, 69.3), (66.2, 69.3),
                 (67.6, 69.3), (69.0, 69.3), (70.4, 69.3)], 4),
    # QA1/QB1 drain notch patches (VSW, 6A) -> In2 VSW plane
    ("VSW", [(93.9, 52.5), (94.7, 52.5), (95.5, 52.5), (96.3, 52.5),
             (93.9, 53.3), (95.1, 53.3), (96.3, 53.3)], 3),
    ("VSW", [(93.9, 92.5), (94.7, 92.5), (95.5, 92.5), (96.3, 92.5),
             (93.9, 93.3), (95.1, 93.3), (96.3, 93.3)], 3),
    # SW island bonds - one ladder per FILL ISLAND (gate traces slice the pours;
    # islands mapped 2026-07-16): NW source piece, main block, south strip
    ("SW_A", [(91.75, 54.0), (92.55, 53.9), (91.75, 54.8), (92.3, 54.6)], 0),      # island NW (sources)
    ("SW_A", [(91.75, 57.4), (92.55, 58.1), (91.75, 58.2), (92.55, 57.3)], 0),     # island main
    ("SW_A", [(92.8, 61.2), (92.8, 62.0), (92.8, 62.8), (91.8, 61.5), (91.8, 62.6)], 0),  # island south strip
    ("SW_B", [(91.75, 94.0), (92.55, 93.9), (91.75, 94.8), (92.3, 94.6)], 0),
    ("SW_B", [(91.75, 97.7), (92.2, 98.2), (91.75, 98.4), (92.2, 99.4), (91.75, 100.0)], 0),
    ("SW_B", [(92.8, 94.2), (92.8, 96.0), (92.8, 97.0), (92.8, 101.0), (92.8, 102.2)], 0),
    # 5V_C main pour -> its lobe B-bond patch (the lobe via comes from the island pass)
    ("5V_C", [(116.0, 63.3), (114.5, 63.3), (117.5, 63.3), (115.2, 62.6)], 1),
    # VBATT_F island under Q1 sources (8A!) -> In2 finger
    ("VBATT_F", [(72.5, 73.2), (73.3, 73.2), (72.5, 75.8), (73.3, 75.8), (72.5, 76.6), (74.1, 76.6)], 1),
    # FE_MID island bonds (8A Q1->Q2 path runs island3 -> B patch -> island0)
    ("FE_MID", [(76.3, 73.4), (77.1, 73.4), (76.3, 74.2), (77.1, 74.2)], 3),   # island: Q1 drain
    ("FE_MID", [(77.3, 80.2), (78.1, 80.2), (77.3, 81.0), (78.1, 81.0), (78.05, 79.4)], 3),  # island: Q2 drain side
    ("FE_MID", [(76.05, 76.5), (76.05, 77.3), (76.05, 78.0)], 1),              # island: U1 sense
    ("FE_MID", [(78.05, 77.9), (78.5, 77.9)], 1),                              # island: C1 tie
    # EP thermal vias (EP pads are unreachable by pour spokes inside the pin ring)
    ("GND", [(85.0, 57.6), (85.0, 58.4), (84.5, 58.0), (85.5, 58.0), (84.4, 57.2),
             (85.6, 57.2), (84.4, 58.8), (85.6, 58.8), (85.0, 59.1)], 2),   # U2 EP
    ("GND", [(85.0, 97.6), (85.0, 98.4), (84.5, 98.0), (85.5, 98.0), (84.4, 97.2),
             (85.6, 97.2), (84.4, 98.8), (85.6, 98.8), (85.0, 99.1)], 2),   # U3 EP
    # (U1 EP: B.Cu under it is solid gate routing - no via fits; the EP reaches
    # GND through the F pour ring, which DRC confirms - no ladder needed)
    # R16.2 GND is jailed by ILIM1's route: via-in-pad (0402, 0.2 drill - ORDER_README notes it)
    ("GND", [(122.51, 63.5), (122.4, 63.4), (122.62, 63.6), (122.4, 63.6), (122.62, 63.4)], 1),
    # CB4.2 same: walled by grid-B routing; via-in-pad
    ("GND", [(69.48, 98.8), (69.35, 98.7), (69.6, 98.9)], 1),
    # U2.12 same: only legal site is essentially in-pad
    ("GND", [(83.6, 56.2), (83.65, 56.25), (83.7, 56.3)], 1),
]
for netname, sites, need in EXPLICIT:
    net = b.FindNet(netname)
    got = sum(try_via(net, x, y, 0.6, 0.3) for x, y in sites if over_plane(netname, x, y))
    print(f"{netname} ladder: {got}/{len(sites)} (need {need})")
    if got < need:
        failures.append(f"ladder {netname} {got}<{need}")

# ---- GND stitching grid
gnd = b.FindNet("GND")
g = sum(try_via(gnd, float(gx), float(gy)) for gx in range(54, 148, 8) for gy in range(54, 108, 8))
print(f"GND grid: {g} vias")

# ---- pad rescue: SMD pads swallowed inside a differently-netted F.Cu pour,
# plus known stranded plane-net pads. Via + short track to the pad's plane.
# (found 2026-07-16: 28 unconnected GND pads, all bank caps inside rail pours)
PLANE_NETS = {"GND", "VSW", "5V_C", "5V_A"}
pour_polys = []  # (net, prio, poly) - only prio>=3 power patches can swallow a pad;
# the full-board GND pour fills AROUND foreign pads and swallows nothing
for z in b.Zones():
    if z.GetNetname() and z.GetLayerSet().Contains(pcbnew.F_Cu) and not z.GetIsRuleArea():
        o = z.Outline().COutline(0)
        pour_polys.append((z.GetNetname(), z.GetAssignedPriority(),
                           [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())]))

def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            inside = not inside
    return inside

# pads that a same-net track END already touches are fed - skip them
track_fed = set()
for _t in b.GetTracks():
    if _t.GetClass() != "PCB_TRACK":
        continue
    for _e in (_t.GetStart(), _t.GetEnd()):
        for fp in b.GetFootprints():
            pass  # (filled below without O(n^2) - see map)
_pad_map = {}
for fp in b.GetFootprints():
    for pad in fp.Pads():
        _pad_map.setdefault((round(pad.GetPosition().x/1e6, 1), round(pad.GetPosition().y/1e6, 1)), []).append(pad)
for _t in b.GetTracks():
    if _t.GetClass() == "PCB_VIA":
        # a same-net via overlapping the pad also feeds it (overlap-site pattern)
        _p = _t.GetPosition()
        for _dx in (-0.1, 0, 0.1):
            for _dy in (-0.1, 0, 0.1):
                for pad in _pad_map.get((round(_p.x/1e6 + _dx, 1), round(_p.y/1e6 + _dy, 1)), []):
                    if pad.GetNetCode() == _t.GetNetCode():
                        pp = pad.GetPosition()
                        if abs(pp.x - _p.x) < 620000 and abs(pp.y - _p.y) < 620000:
                            track_fed.add((pp.x/1e6, pp.y/1e6))
        continue
    for _e in (_t.GetStart(), _t.GetEnd()):
        for pad in _pad_map.get((round(_e.x/1e6, 1), round(_e.y/1e6, 1)), []):
            if pad.GetNetCode() == _t.GetNetCode():
                track_fed.add((pad.GetPosition().x/1e6, pad.GetPosition().y/1e6))

FORCE_RESCUE = {  # (U2.20/U3.20 VIN are KRT tap-wave routed now - TAPU/TAPV)
                ("CA1", "2"), ("RA1", "2"), ("RA4", "2"),  # grid-A GND, cut off by congestion
                ("CB2", "2"),                 # grid-B GND, same
                ("D2", "1"), ("R22", "1")}    # 5V_A parts south/east of pours (plane below)
# deeply-boxed GND pads (U2.12/U3.12/CB4.2/R16.2) are L/Z-rescued in route_taps
# inner-plane coverage per net: a rescue via only helps if the plane is under it
plane_polys = {"GND": [[(51, 51), (149, 51), (149, 109), (51, 109)]]}
for z in b.Zones():
    if z.GetLayerSet().Contains(pcbnew.In2_Cu) and z.GetNetname():
        o = z.Outline().COutline(0)
        plane_polys.setdefault(z.GetNetname(), []).append(
            [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())])
rescued = 0
for fp in b.GetFootprints():
    for pad in fp.Pads():
        nn = pad.GetNetname()
        if nn not in PLANE_NETS or not pad.IsOnLayer(pcbnew.F_Cu):
            continue
        if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        px, py = pad.GetPosition().x/1e6, pad.GetPosition().y/1e6
        forced = (fp.GetReference(), str(pad.GetNumber())) in FORCE_RESCUE
        if (px, py) in track_fed:
            continue  # a routed same-net track/via already feeds this pad (even forced)
        if not forced:
            here = [(pr, n2) for n2, pr, poly in pour_polys if in_poly(px, py, poly)]
            winner = max(here)[1] if here else None  # highest-priority pour wins
            if winner == nn:
                continue  # its own pour feeds it
            if not (bool(here) and max(here)[0] >= 3 and winner != nn):
                continue  # not swallowed either
        net = pad.GetNet()
        fx, fy = fp.GetPosition().x/1e6, fp.GetPosition().y/1e6
        dx, dy = px - fx, py - fy
        L = math.hypot(dx, dy) or 1.0
        base = math.degrees(math.atan2(dy, dx))
        ok = False
        for off in (0.7, 0.8, 0.9, 1.1, 1.5, 2.0, 2.6, 3.2, 3.8, 0.5, 0.3):  # near rings LAST (they pinch fill necks)
            for dang in (0, 30, -30, 60, -60, 90, -90, 120, -120, 150, -150, 180):
                a = math.radians(base + dang)
                vx, vy = round(px + off*math.cos(a), 2), round(py + off*math.sin(a), 2)
                if not (51.2 < vx < 148.8 and 51.2 < vy < 108.8):
                    continue  # edge guard
                if not any(in_poly(vx, vy, pp) for pp in plane_polys.get(nn, [])):
                    continue  # no plane under this site - a via would dangle
                tw = next((w for w in (0.35, 0.25) if not tk.collides(px, py, vx, vy, w, net.GetNetCode(), pcbnew.F_Cu)), None)
                if tw is None:
                    continue  # rescue track path would cross something
                if try_via(net, vx, vy):
                    tr = pcbnew.PCB_TRACK(b)
                    tr.SetStart(pcbnew.VECTOR2I_MM(px, py))
                    tr.SetEnd(pcbnew.VECTOR2I_MM(vx, vy))
                    tr.SetWidth(pcbnew.FromMM(tw)); tr.SetLayer(pcbnew.F_Cu); tr.SetNet(net)
                    b.Add(tr)
                    rescued += 1; ok = True
                    break
            if ok:
                break
        if not ok:
            failures.append(f"rescue {fp.GetReference()}.{pad.GetNumber()} ({nn}) at ({px:.1f},{py:.1f})")
print(f"pad rescues: {rescued}")

# (micro-stub cleanup removed 2026-07-16: it ate 0.05mm KRT jog connectors
# mid-chain; the route_taps trimmer owns dangler handling now)

if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
# (a hardcoded dangling-via kill list ONCE lived here; on the re-routed board
# its coordinates hit a LIVE HO_A fanout via - never kill copper by stale
# coordinates. Dangling vias are handled case-by-case from DRC output.)

# ---- via janitor: a via is useful iff same-net copper attaches on >= 2
# layers (F: track/pad/F-zone; B: track/B-zone; inner: In1 GND or In2 plane).
# KRT fanout leaves orphans when the net later routes on one layer.
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
                bb = p.GetBoundingBox()  # returned by value - safe to inflate
                bb.Inflate(v.GetWidth() // 2)  # barrel OVERLAP counts, not just center-inside
                if abs(pp.x/1e6-vx) < 2.0 and abs(pp.y/1e6-vy) < 2.0 and bb.Contains(v.GetPosition()):
                    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                        if p.IsOnLayer(lay):
                            attach.add(lay)
    for (znet, zlay), polys in _ztmp.items():
        if znet == nn and any(in_poly(vx, vy, poly) for poly in polys):
            attach.add(zlay)
    if len(attach) < 2:
        _orphans.append((v, nn, round(vx, 2), round(vy, 2)))
for v, nn, vx, vy in _orphans:
    b.Remove(v)
print(f"via janitor removed {len(_orphans)}: {[(n, x, y) for _, n, x, y in _orphans]}")

# ---- fill, then stitch any pad-bearing island that has no via of its net
filler = pcbnew.ZONE_FILLER(b)
filler.Fill(b.Zones())
via_pts = {}
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        via_pts.setdefault(t.GetNetname(), []).append(t.GetPosition())
B_ZONE_POLYS = {}
for z in b.Zones():
    if z.GetNetname() and z.GetLayerSet().Contains(pcbnew.B_Cu) and not z.GetIsRuleArea():
        o = z.Outline().COutline(0)
        B_ZONE_POLYS.setdefault(z.GetNetname(), []).append(
            [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())])
added = 0
for z in b.Zones():
    nn = z.GetNetname()
    if not nn or z.GetIsRuleArea() or nn not in (set(PLANE_POLYS) | set(FLOOR) | {"GND"}):
        continue
    for lay in z.GetLayerSet().Seq():
        if lay not in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu):
            continue
        polys = z.GetFilledPolysList(lay)
        for i in range(polys.OutlineCount()):
            o = polys.Outline(i)
            bb = o.BBox()
            if bb.GetWidth() < 8e5 or bb.GetHeight() < 8e5:
                continue  # sliver
            if any(o.PointInside(p) for p in via_pts.get(nn, [])):
                continue  # already stitched
            # a via helps this island only where same-net copper exists on
            # ANOTHER layer directly underneath (plane or B-zone GEOMETRY)
            def _backed(x, y):
                return (over_plane(nn, x, y) if nn in PLANE_POLYS else False) or \
                       any(_in_poly0(x, y, bp) for bp in B_ZONE_POLYS.get(nn, []))
            if lay == pcbnew.In2_Cu and not over_plane(nn, bb.Centre().x/1e6, bb.Centre().y/1e6):
                pass
            placed = False
            backed_sites = 0
            for fx in range(2, 19, 2):
                for fy in range(2, 19, 2):
                    x = (bb.GetLeft() + bb.GetWidth()*fx//20)
                    y = (bb.GetTop() + bb.GetHeight()*fy//20)
                    if not o.PointInside(pcbnew.VECTOR2I(x, y)):
                        continue
                    xm, ym = round(x/1e6, 2), round(y/1e6, 2)
                    if not _backed(xm, ym):
                        continue
                    backed_sites += 1
                    if try_via(b.FindNet(nn), xm, ym):
                        via_pts.setdefault(nn, []).append(pcbnew.VECTOR2I(x, y))
                        added += 1
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                # does this island even hold a pad? pad-free slivers are removable noise
                has_pad = any(fp2.GetReference() for fp2 in b.GetFootprints()
                              for p2 in fp2.Pads()
                              if p2.GetNetname() == nn and o.PointInside(p2.GetPosition()))
                if has_pad:
                    failures.append(f"island {nn} bbox=({bb.GetLeft()/1e6:.1f},{bb.GetTop()/1e6:.1f})-"
                                    f"({bb.GetRight()/1e6:.1f},{bb.GetBottom()/1e6:.1f}) "
                                    f"unstitchable ({backed_sites} backed sites, none placeable)")
print(f"island stitch vias: {added}")
if failures:
    print("FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
filler.Fill(b.Zones())
b.Save(PCB)
print("filled + saved")
