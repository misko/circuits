#!/usr/bin/env python3
"""Route the sense/tap connections KRT could not see (pour/plane-fed nets whose
tap parts sit outside any copper of their net). Every hop is exact-collision-
checked (Toolkit.joinpath / collides); widths are net-class floors, no thin
fallback. B.Cu is the fallback layer - it is nearly empty here.

Runs AFTER import_krt, BEFORE stitch_and_fill. FAILS before save if any
connection cannot be made."""
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

# SW tap-tree fragments that graze the VSW drain pads inside the notches:
# both their ends live in pour-covered copper, so the fill carries the net -
# the fragments only contribute sub-0.1mm clearance violations. Delete them.
_notches = [(93.3, 53.4, 96.6, 56.9), (93.3, 93.4, 96.6, 96.9)]
_nk = []
for _t in b.GetTracks():
    if _t.GetClass() == "PCB_TRACK" and _t.GetNetname() in ("SW_A", "SW_B"):
        for _pt in (_t.GetStart(), _t.GetEnd()):
            if any(x0 <= _pt.x/1e6 <= x1 and y0 <= _pt.y/1e6 <= y1 for x0, y0, x1, y1 in _notches):
                _nk.append(_t)
                break
# plus sub-0.12mm SW crumbs left at the pour band edges by the notch deletion
for _t in b.GetTracks():
    if (_t.GetClass() == "PCB_TRACK" and _t.GetNetname() in ("SW_A", "SW_B")
            and _t.GetLength() < 120000 and _t not in _nk):
        _mx = (_t.GetStart().x + _t.GetEnd().x) / 2e6
        _my = (_t.GetStart().y + _t.GetEnd().y) / 2e6
        if 91.3 <= _mx <= 99.5 and (53.3 <= _my <= 54.1 or 93.3 <= _my <= 94.1):
            _nk.append(_t)
for _t in _nk:
    b.Remove(_t)
print(f"removed {len(_nk)} notch-grazing SW fragments")

# SW tap bits below the 0.15 tap floor (KRT neckdown artifacts)
for _t in b.GetTracks():
    if (_t.GetClass() == "PCB_TRACK" and _t.GetNetname() in ("SW_A", "SW_B")
            and _t.GetWidth() < 150000):
        _t.SetWidth(150000)


# KRT overshoot tails in the controller boxes: a track with one free end may
# still CARRY the net mid-body (in-pad vias touch tails 0.05mm off-axis, other
# tracks tee into them) - deleting such tails severed ILIM_B and PGOOD_A
# (2026-07-16). Correct treatment: TRIM the free end back to the furthest
# contact; delete only when there is no contact at all on a both-ends-free track.
_boxes = [(63.0, 52.5, 99.0, 63.4), (63.0, 92.5, 99.0, 103.4)]

def _proj(px, py, ax, ay, bx, by):
    dx, dy = bx-ax, by-ay
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return 0.0, (px-ax)**2 + (py-ay)**2
    t = max(0.0, min(1.0, ((px-ax)*dx + (py-ay)*dy) / L2))
    return t, (px - ax - t*dx)**2 + (py - ay - t*dy)**2

def _tkey(t):
    """stable identity: SWIG hands out a fresh proxy per iteration, so id()
    NEVER matches across loops (found 2026-07-16 - it made every self-endpoint
    a 'contact' and disabled the whole trimmer)"""
    if t.GetClass() == "PCB_VIA":
        return ("v", t.GetPosition().x, t.GetPosition().y)
    return ("t", t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y, t.GetLayer())

_items = []      # (x, y, touch radius, owner-key, netcode) - SAME-NET contacts only:
# a track crossing a foreign or NC pad is a SHORT, not a connection
for _t in b.GetTracks():
    if _t.GetClass() == "PCB_VIA":
        _items.append((_t.GetPosition().x, _t.GetPosition().y, _t.GetWidth()/2 + 60000, _tkey(_t), _t.GetNetCode()))
    else:
        for _e in (_t.GetStart(), _t.GetEnd()):
            _items.append((_e.x, _e.y, _t.GetWidth()/2 + 60000, _tkey(_t), _t.GetNetCode()))
_foreign_pads = []   # small pads: an endpoint INSIDE one of another net = r5 garbage
for _fp in b.GetFootprints():
    for _p in _fp.Pads():
        _items.append((_p.GetPosition().x, _p.GetPosition().y,
                       max(_p.GetSize(pcbnew.F_Cu).x, _p.GetSize(pcbnew.F_Cu).y)/2 + 60000, 0, _p.GetNetCode()))
        if max(_p.GetSize(pcbnew.F_Cu).x, _p.GetSize(pcbnew.F_Cu).y) < 1.2e6:
            _lay = pcbnew.F_Cu if _p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            _foreign_pads.append((_p.GetBoundingBox(), _p.GetNetCode(), _lay))

_segs_bynet = {}
for _t in b.GetTracks():
    if _t.GetClass() == "PCB_TRACK":
        _segs_bynet.setdefault(_t.GetNetCode(), []).append(
            (_t.GetStart().x, _t.GetStart().y, _t.GetEnd().x, _t.GetEnd().y,
             _tkey(_t), _t.GetWidth()/2))

_trimmed = _deleted = 0
_degen = []
for _t in list(b.GetTracks()):
    if _t.GetClass() != "PCB_TRACK":
        continue
    _s, _e = _t.GetStart(), _t.GetEnd()
    xs, ys_ = sorted((_s.x/1e6, _e.x/1e6)), sorted((_s.y/1e6, _e.y/1e6))
    if not any(x0 <= xs[0] and xs[1] <= x1 and y0 <= ys_[0] and ys_[1] <= y1 for x0, y0, x1, y1 in _boxes):
        continue
    # contact params along the segment (0=start, 1=end), excluding self-endpoints
    # endpoint inside a small foreign pad = fanout garbage shorting that pad
    if any(bb2.Contains(pt) and nc2 != _t.GetNetCode() and lay2 == _t.GetLayer()
           for pt in (_s, _e) for bb2, nc2, lay2 in _foreign_pads):
        _degen.append(_t)
        continue
    _c = []
    for ix, iy, ir, _own, _nc in _items:
        if _own == _tkey(_t) or _nc != _t.GetNetCode():
            continue  # only our net's copper counts as a contact
        t, d2 = _proj(ix, iy, _s.x, _s.y, _e.x, _e.y)
        if d2 <= (ir + _t.GetWidth()/2) ** 2:
            _c.append(t)
    s_free = not any(t < 0.02 for t in _c)
    e_free = not any(t > 0.98 for t in _c)
    # an endpoint lying on ANOTHER same-net segment's BODY is not free either
    # (the mirror T-junction case - missing this severed EN_A/HO_B 2026-07-16)
    if s_free or e_free:
        for _u in _segs_bynet.get(_t.GetNetCode(), []):
            if _u[4] == _tkey(_t):
                continue
            for _which, _pt in (("s", _s), ("e", _e)):
                _tt, _d2 = _proj(_pt.x, _pt.y, _u[0], _u[1], _u[2], _u[3])
                if _d2 <= (_u[5] + _t.GetWidth()/2) ** 2:
                    if _which == "s":
                        s_free = False
                    else:
                        e_free = False
    if not (s_free or e_free):
        continue
    if not _c:
        if s_free and e_free:
            b.Remove(_t); _deleted += 1
        continue
    _L = max(_t.GetLength(), 1)
    _ov = min(0.3, 150000 / _L)   # overshoot 0.15mm past the contact: trimming
    # exactly TO a projected via-center left the end 0.07mm short of the barrel
    if e_free and max(_c) < 0.95:
        _tc = min(1.0, max(_c) + _ov)
        _t.SetEnd(pcbnew.VECTOR2I(int(_s.x + (_e.x-_s.x)*_tc), int(_s.y + (_e.y-_s.y)*_tc)))
        _trimmed += 1
    elif s_free and min(_c) > 0.05:
        _tc = max(0.0, min(_c) - _ov)
        _t.SetStart(pcbnew.VECTOR2I(int(_s.x + (_e.x-_s.x)*_tc), int(_s.y + (_e.y-_s.y)*_tc)))
        _trimmed += 1
    if _t.GetLength() < 50000:  # degenerate after trim - batch for later
        _degen.append(_t)
for _t in _degen:
    b.Remove(_t)
    _deleted += 1
print(f"controller boxes: trimmed {_trimmed} overshoot tails, deleted {_deleted} orphans")

# hair gaps: KRT sometimes ends a track 0.05-0.1mm short of its own via's
# center; KiCad connectivity then splits the net. Snap such ends onto the via.
_vias_bynet = {}
for _t in b.GetTracks():
    if _t.GetClass() == "PCB_VIA":
        _vias_bynet.setdefault(_t.GetNetCode(), []).append(_t.GetPosition())
_snapped = 0
for _t in b.GetTracks():
    if _t.GetClass() != "PCB_TRACK":
        continue
    for _get, _set in ((_t.GetStart, _t.SetStart), (_t.GetEnd, _t.SetEnd)):
        _p = _get()
        for _vp in _vias_bynet.get(_t.GetNetCode(), []):
            d2 = (_p.x-_vp.x)**2 + (_p.y-_vp.y)**2
            if 0 < d2 <= 120000**2:
                _set(pcbnew.VECTOR2I(_vp.x, _vp.y))
                _snapped += 1
                break
_zl = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK" and t.GetLength() == 0]
for _t in _zl:
    b.Remove(_t)
print(f"snapped {_snapped} hair-gap ends onto vias; dropped {len(_zl)} zero-length")

# Toolkit AFTER any deletions: its index would hold freed SWIG wrappers (segfault)
tk = Toolkit(b, 0.12)
failures = []
VIAS = [(v.GetPosition().x/1e6, v.GetPosition().y/1e6)
        for v in b.GetTracks() if v.GetClass() == "PCB_VIA"]  # existing vias count for spacing

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

def try_targets(netname, p_from, cands, tag):
    """cands: list of (p_to, width, bwps, to_is_pour). First success wins."""
    for p_to, w, bwps, pour in cands:
        if connect(netname, p_from, p_to, w, to_is_pour=pour, bwps=bwps):
            return True
        failures.pop()
    failures.append(f"{netname}: {tag} {p_from} unroutable via {len(cands)} candidates")
    return False

def pad_xy(ref, num):
    fp = b.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            return (round(p.GetPosition().x/1e6, 2), round(p.GetPosition().y/1e6, 2))
    raise RuntimeError(f"no pad {ref}.{num}")

# All west-grid taps are mA signals inside the (extended) SW_TAP_A/B named
# rule areas -> 0.15 there; stage up to the class floor once outside the area.

# (SW_A grid taps CA3/RA2 are in the KRT tap wave - TAPW group)

# (SW_B and 5V_C tap trees are routed by the KRT tap pass - route_taps_krt.py)

# --- 5V_C consumers stranded south of the In2 plane split (TVS + LED)
try_targets("5V_C", pad_xy("D3", "1"),
            [((117.5, 66.5), 0.25, (), True), ((115.5, 67.0), 0.25, (), True),
             ((113.0, 66.0), 0.25, (), True), ((112.5, 67.5), 0.25, ((114.5, 71.0),), True)], "D3.1")
# (U1.9 VSW moved AFTER the FE_MID block - it was claiming U1.10's only corridor)
# (U2.19 SW_A sense is routed by the KRT tap pass - TAPW group)

# (SS_A is routed in the KRT chain's hardest-first wave)

# --- deeply-boxed GND pads: no straight-stub via site exists; L/Z + via to In1
# EP joins: a walled QFN GND pin reaches its OWN exposed pad on F.Cu (same
# net); everything else lands a via over In1 (analyzer-verified sites)
EP_JOIN = {(84.6, 57.8), (84.4, 58.4), (84.2, 57.2),
           (84.6, 97.8), (84.4, 98.4), (84.2, 97.2)}
for _ref, _num, _cands in [
    ("U2", "12", [((84.6, 57.8), 0.15), ((84.4, 58.4), 0.15), ((84.2, 57.2), 0.15)]),
    ("U3", "12", [((84.6, 97.8), 0.15), ((84.4, 98.4), 0.15), ((84.2, 97.2), 0.15)]),
    ("CB4", "2", [((69.48, 96.0), 0.15), ((70.6, 97.4), 0.15), ((72.0, 98.8), 0.2)]),
    ("U1", "7", [((69.21, 80.93), 0.15), ((68.9, 80.74), 0.15), ((68.0, 79.0), 0.2)]),
    ("CA2", "2", [((74.48, 52.5), 0.15), ((73.1, 52.68), 0.15), ((74.45, 52.68), 0.15)]),
]:
    _cl = [(p, w, (), p not in EP_JOIN) for p, w in _cands]
    if not try_targets("GND", pad_xy(_ref, _num), _cl, f"{_ref}.{_num}"):
        # soft: the GND pour may reach these with thermal spokes at fill -
        # the DRC gate is the arbiter. If it reports them unconnected, the
        # candidates above need widening, not this warning removed.
        print(f"WARN: no L/Z rescue for {_ref}.{_num}; deferring to pour + DRC")
        failures.pop()
# (U3.19 is in the KRT tap wave - TAPB group)
connect("5V_C", pad_xy("R23", "1"), (132.2, 63.8), 0.25, to_is_pour=True)

# --- 5V_A feedback/sense tree -> In2 5V_A plane (east of x99)
rb3, cb10 = pad_xy("RB3", "1"), pad_xy("CB10", "1")
connect("5V_A", rb3, cb10, 0.15)
connect("5V_A", cb10, (108.0, 104.2), 0.25, to_is_pour=True, bwps=[(90.0, 105.8), (102.5, 104.2)])

# --- FE_MID locals into the FE_MID pour (x75.45-79)
connect("FE_MID", pad_xy("U1", "12"), (76.5, 77.75), 0.25, to_is_pour=True)
# (U1.10 FE_MID is routed by the KRT tap pass - TAPF group)
connect("FE_MID", pad_xy("C1", "2"), (78.3, 77.72), 0.25, to_is_pour=True)
try_targets("FE_MID", pad_xy("C2", "1"),
            [((78.3, 83.48), 0.25, (), True), ((78.3, 82.3), 0.25, (), True),
             ((78.3, 84.8), 0.25, (), True), ((78.3, 83.48), 0.25, ((80.0, 85.5),), True)], "C2.1")
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
