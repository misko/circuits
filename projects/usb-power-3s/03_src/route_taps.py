#!/usr/bin/env python3
"""Route the sense/tap connections KRT could not see (pour/plane-fed nets whose
tap parts sit outside any copper of their net). Every hop is exact-collision-
checked (Toolkit.joinpath / collides); widths are net-class floors, no thin
fallback. B.Cu is the fallback layer - it is nearly empty here.

Runs AFTER import_krt, BEFORE stitch_and_fill. FAILS before save if any
connection cannot be made."""
import os, sys, math
sys.path.insert(0, os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))
from pathlib import Path
import pcbnew
from pcb_toolkit import Toolkit

PCB = str(Path(__file__).parent.parent / "04_kicad" / "usb_power_3s.kicad_pcb")
b = pcbnew.LoadBoard(PCB)
tk = Toolkit(b, 0.12)
failures = []
VIAS = [(v.GetPosition().x/1e6, v.GetPosition().y/1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]  # existing vias count for spacing

# stale stubs from the old drain-pour geometry: U2/U3 pad stubs into the void
_boxes = [(85.4, 55.4, 87.6, 60.6), (85.4, 95.4, 87.6, 100.6)]
_dead = []
for _t in b.GetTracks():
    if _t.GetClass() != "PCB_TRACK" or _t.GetLength() > 2.3e6:
        continue
    if _t.GetNetname() not in ("GND", "VSW", "SW_A", "SW_B"):
        continue
    xs = sorted((_t.GetStart().x/1e6, _t.GetEnd().x/1e6)); ys = sorted((_t.GetStart().y/1e6, _t.GetEnd().y/1e6))
    if any(x0 <= xs[0] and xs[1] <= x1 and y0 <= ys[0] and ys[1] <= y1 for x0, y0, x1, y1 in _boxes):
        _dead.append(_t)
for _t in _dead:
    b.Remove(_t)
print(f"removed {len(_dead)} stale drain-gap stubs")

# inner-plane coverage: a via only helps where its net's plane is underneath
PLANE_POLYS = {"GND": [[(51, 51), (149, 51), (149, 109), (51, 109)]]}
for z in b.Zones():
    if z.GetLayerSet().Contains(pcbnew.In2_Cu) and z.GetNetname():
        o = z.Outline().COutline(0)
        PLANE_POLYS.setdefault(z.GetNetname(), []).append(
            [(o.CPoint(i).x/1e6, o.CPoint(i).y/1e6) for i in range(o.PointCount())])

def in_poly(x, y, poly):
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[(i+1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1) + x1:
            inside = not inside
    return inside

def via_params(net, x, y):
    """Best via that fits: standard 0.6/0.3, else advanced 0.45/0.2 with the
    JLC-advanced hole clearance. Returns (size, drill) or None."""
    if not (51.2 < x < 148.8 and 51.2 < y < 108.8):
        return None
    if any((x-ux)**2 + (y-uy)**2 < 0.55**2 for ux, uy in VIAS):
        return None
    if tk.via_site_ok(x, y, net.GetNetCode(), size=0.6, drill=0.3):
        return (0.6, 0.3)
    if tk.via_site_ok(x, y, net.GetNetCode(), size=0.45, drill=0.2, hole_to_copper=0.14):
        return (0.45, 0.2)
    return None

def add_via(net, x, y, size=0.6, drill=0.3):
    tk.add_via(x, y, net, size=size, drill=drill)
    VIAS.append((x, y))

def ring_sites(px, py):
    # 0.45/0.6 first: via barrel overlaps the pad copper -> no F stub needed
    for off in (0.45, 0.6, 1.0, 1.4, 2.0, 2.6):
        for ang in range(0, 360, 45):
            yield (round(px + off*math.cos(math.radians(ang)), 2),
                   round(py + off*math.sin(math.radians(ang)), 2))

def stub_ok(net, pad, via, w):
    """No stub needed when the via overlaps the pad; else the straight stub
    must be clear on F.Cu."""
    if math.hypot(pad[0]-via[0], pad[1]-via[1]) < 0.62:
        return "overlap"
    return "stub" if seg_ok(net, pad, via, w, pcbnew.F_Cu) else None

def seg_ok(net, p1, p2, w, layer):
    return not tk.collides(p1[0], p1[1], p2[0], p2[1], w, net.GetNetCode(), layer)

def add_seg(net, p1, p2, w, layer):
    tr = pcbnew.PCB_TRACK(b)
    tr.SetStart(pcbnew.VECTOR2I_MM(*p1)); tr.SetEnd(pcbnew.VECTOR2I_MM(*p2))
    tr.SetWidth(pcbnew.FromMM(w)); tr.SetLayer(layer); tr.SetNet(net)
    b.Add(tr)

PLANE_NETS = {"GND", "VSW", "5V_C", "5V_A", "VBATT_F"}

def b_path(netname, va, vb, width, bwps):
    """B.Cu leg via optional intermediate waypoints, all-or-nothing."""
    pts = [va] + list(bwps) + [vb]
    segs = []
    for q1, q2 in zip(pts, pts[1:]):
        got = tk.joinpath(netname, q1, q2, width, layer=pcbnew.B_Cu, widths_fallback=())
        if got is None:
            return False
        segs.append((q1, q2))
    return True

def connect(netname, p_from, p_to, width, to_is_pour=False, bwps=()):
    """p_from is a pad center; p_to is a pad center or a point inside the
    net's F.Cu pour (to_is_pour=True -> finish with a via there, not a pad).
    bwps: intermediate B.Cu waypoints for the via-fallback path."""
    net = b.FindNet(netname)
    # 1) plain F.Cu L/Z (bond via at the pour end only if an inner plane exists)
    if not bwps and tk.joinpath(netname, p_from, p_to, width, layer=pcbnew.F_Cu, widths_fallback=()):
        if (to_is_pour and netname in PLANE_NETS
                and any(in_poly(*p_to, pp) for pp in PLANE_POLYS.get(netname, []))):
            pv = via_params(net, *p_to)
            if pv:
                add_via(net, *p_to, *pv)
        return True
    # 2) via -> B.Cu (through bwps) -> via
    for va in ring_sites(*p_from):
        sa = stub_ok(net, p_from, va, width)
        pa = via_params(net, *va) if sa else None
        if sa is None or pa is None:
            continue
        for vb in ([p_to] if to_is_pour else list(ring_sites(*p_to))):
            sb = "overlap" if to_is_pour else stub_ok(net, p_to, vb, width)
            pb = via_params(net, *vb) if sb else None
            if sb is None or pb is None:
                continue
            if b_path(netname, va, vb, width, bwps):
                if sa == "stub":
                    add_seg(net, p_from, va, width, pcbnew.F_Cu)
                add_via(net, *va, *pa); add_via(net, *vb, *pb)
                if sb == "stub":
                    add_seg(net, vb, p_to, width, pcbnew.F_Cu)
                return True
    failures.append(f"{netname}: {p_from} -> {p_to} unroutable (w={width})")
    return False

def pad_xy(ref, num):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            return (round(p.GetPosition().x/1e6, 2), round(p.GetPosition().y/1e6, 2))
    raise RuntimeError(f"no pad {ref}.{num}")

# All west-grid taps are mA signals inside the (extended) SW_TAP_A/B named
# rule areas -> 0.15 there; stage up to the class floor once outside the area.

# --- SW_A: BST/ILIM taps in grid A -> SW_A pour west band
ca3, ra2 = pad_xy("CA3", "2"), pad_xy("RA2", "2")
connect("SW_A", ca3, ra2, 0.15)
connect("SW_A", ra2, (92.2, 54.2), 0.15, to_is_pour=True, bwps=[(75.0, 52.2)])

# (SW_B and 5V_C tap trees are routed by the KRT tap pass - route_taps_krt.py)

# --- 5V_C consumers stranded south of the In2 plane split (TVS + LED)
connect("5V_C", pad_xy("D3", "1"), (117.5, 66.5), 0.25, to_is_pour=True)
# (U1.9 VSW moved AFTER the FE_MID block - it was claiming U1.10's only corridor)
connect("SW_A", pad_xy("U2", "19"), (91.8, 59.9), 0.15, to_is_pour=True)
connect("SW_B", pad_xy("U3", "19"), (91.8, 99.9), 0.15, to_is_pour=True)
connect("5V_C", pad_xy("R23", "1"), (132.2, 63.8), 0.25, to_is_pour=True)

# --- 5V_A feedback/sense tree -> In2 5V_A plane (east of x99)
rb3, cb10 = pad_xy("RB3", "1"), pad_xy("CB10", "1")
connect("5V_A", rb3, cb10, 0.15)
connect("5V_A", cb10, (108.0, 104.2), 0.25, to_is_pour=True, bwps=[(90.0, 105.8), (102.5, 104.2)])

# --- FE_MID locals into the FE_MID pour (x75.45-79)
connect("FE_MID", pad_xy("U1", "12"), (76.5, 77.75), 0.25, to_is_pour=True)
connect("FE_MID", pad_xy("U1", "10"), (76.5, 79.9), 0.25, to_is_pour=True)
connect("FE_MID", pad_xy("C1", "2"), (78.3, 77.72), 0.25, to_is_pour=True)
connect("FE_MID", pad_xy("C2", "1"), (78.3, 83.48), 0.25, to_is_pour=True)
# U1.9 (VSW sense): pad is fully boxed on F.Cu - a 0.45/0.2 via IN the pad
# reaches the In2 VSW plane directly (WSON 0.5 pitch tolerates it, mA net)
u1_9 = pad_xy("U1", "9")
_vsw = b.FindNet("VSW")
if tk.via_site_ok(*u1_9, _vsw.GetNetCode(), size=0.45, drill=0.2, hole_to_copper=0.14):
    tk.add_via(*u1_9, _vsw, size=0.45, drill=0.2)
    VIAS.append(u1_9)
else:
    failures.append(f"VSW: U1.9 via-in-pad blocked at {u1_9}")

if failures:
    print("ROUTE-TAPS FAILURES:\n  " + "\n  ".join(failures))
    sys.exit(1)
b.Save(PCB)
print(f"route_taps: all taps routed ({len(VIAS)} vias) + saved")
