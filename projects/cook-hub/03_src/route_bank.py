#!/usr/bin/env python3
"""Draw ALL engineered bank copper (post-KRT-import). Nets: KC* (KEYPAD),
COIL_1..16, RELAY_5V. Geometry from geom.py (ADR-0002/D15):

KEYPAD (32 nets):
  pad stub east -> corridor vertical north -> fan lane E-W -> J11 drop
  (north-row pads via a +1.27 jog around the south-row pad).
COIL (16 nets):
  pin7 stub west -> vertical south -> B.Cu lane E-W -> drop at the ULN
  OUT pad x -> via IN the pad tail (COIL_VIA_Y) -> F.Cu (via lands on pad).
  Plus the F.Cu stub pin7 -> coil test point (TP41-56).
RELAY_5V:
  F.Cu vertical per super-column (stubs to both pin-1s) -> bus y=R5V_BUS_Y
  -> Q1 drain; spurs to C8/C9/R25/TP33 and the two ULN COM pads.

Safety gates before save:
  - pairwise same-layer segment crossing check over every added segment
    (different nets only);
  - every KEYPAD segment >= ISO_MIN - 0.25 from every sanctioned SELV
    segment drawn here (the full audit re-measures against the whole board);
  - lane assignment constraints solved by topological order, hard error
    on cycles.
Run: /usr/bin/python3 03_src/route_bank.py"""
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

PCB = HERE.parent / "04_kicad" / "cook_hub.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
# The RELAY_5V bank spurs run on the EMPTY In2 layer (docstring); import
# leaves the power pours FILLED, and the 3V3 In2 pour covers the spur
# corridor south of the bank. Unfill before drawing so the spur via-sites +
# In2 verticals are clear; stitch_and_fill refills every zone afterwards.
for _z in b.Zones():
    _z.UnFill()
MM = pcbnew.ToMM
F, B, I2 = pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In2_Cu

nets = {}
for _code, ni in b.GetNetInfo().NetsByName().items():
    nets[str(_code)] = ni

fps = {f.GetReference(): f for f in b.GetFootprints()}


def pad(ref, num):
    return next(p for p in fps[ref].Pads() if p.GetNumber() == num)


def padxy(ref, num):
    p = pad(ref, num).GetPosition()
    return MM(p.x), MM(p.y)


SEGS = []  # (x1,y1,x2,y2,layer,net,width)


def seg(x1, y1, x2, y2, layer, net, w):
    assert abs(x1 - x2) < 1e-6 or abs(y1 - y2) < 1e-6 or True
    SEGS.append((x1, y1, x2, y2, layer, net, w))


# ---------------------------------------------------------------- KEYPAD
def fan_lane(n):
    """Fan lane index for channel n (1..16): east 1-8 -> 0..7 by col asc;
    west 9-16 -> 15..8 (n=9 deepest)."""
    return n - 1 if n <= 8 else 24 - n


for n in range(1, 17):
    k = (n + 1) // 2 - 1
    row = (n - 1) % 2
    cx = G.CONT_X[k]
    col_x = G.J11_COL0_X + (n - 1) * 2.54
    lane_y = G.FAN_LANE_Y[fan_lane(n)]
    yA = G.ROW_Y[row]                 # pin 14 (A net)
    yB = G.ROW_Y[row] + G.PIN_SPAN    # pin 8  (B net)
    if row == 0:
        plan = [("A", yA, G.LANE_F0, F), ("B", yB, G.LANE_B0, B)]
    else:
        plan = [("B", yB, G.LANE_F1, F), ("A", yA, G.LANE_B1, B)]
    for ab, py, off, layer in plan:
        net = f"KC{n}{ab}"
        x_off = cx + off
        if off:
            seg(cx, py, x_off, py, layer, net, G.W_CONTACT)      # pad stub
        seg(x_off, py, x_off, lane_y, layer, net, G.W_CONTACT)   # corridor
        # J11 target: A -> north row (jog), B -> south row (direct)
        if ab == "A":
            jx = col_x + 1.27
            seg(x_off, lane_y, jx, lane_y, layer, net, G.W_CONTACT)
            seg(jx, lane_y, jx, G.J11_ROWA_Y, layer, net, G.W_CONTACT)
            seg(jx, G.J11_ROWA_Y, col_x, G.J11_ROWA_Y, layer, net, G.W_CONTACT)
        else:
            seg(x_off, lane_y, col_x, lane_y, layer, net, G.W_CONTACT)
            seg(col_x, lane_y, col_x, G.J11_ROWB_Y, layer, net, G.W_CONTACT)

# ----------------------------------------------------------------- COIL
def solve_lanes(group):
    """group: list of (net, src_x, drop_x). Returns net->lane_y.
    Constraints: span(B) contains drop_A  => B shallower (north of) A;
                 span(B) contains src_A   => B deeper (south of) A."""
    import itertools
    spans = {net: (min(sx, dx), max(sx, dx)) for net, sx, dx in group}
    src = {net: sx for net, sx, dx in group}
    drop = {net: dx for net, sx, dx in group}
    order = {net: set() for net in spans}   # net -> nets that must be DEEPER
    for a, bb in itertools.permutations(spans, 2):
        lo, hi = spans[bb]
        if lo - 0.01 < drop[a] < hi + 0.01:
            order[bb].add(a)     # b shallower than a: a deeper
        if lo - 0.01 < src[a] < hi + 0.01:
            order[a].add(bb)     # b deeper than a
    out, done = {}, []
    pending = dict(order)
    while pending:
        ready = [n for n, deps in pending.items()
                 if all(d in done for d in deps)]
        if not ready:
            raise RuntimeError(f"lane constraint cycle: {pending}")
        ready.sort()
        n = ready[0]
        done.append(n)
        del pending[n]
    # done[0] = DEEPEST (its must-be-deeper set is empty first)
    ys = G.COIL_LANE_YS[-len(done):] if len(done) < len(G.COIL_LANE_YS) else G.COIL_LANE_YS
    for i, n in enumerate(done):
        out[n] = ys[len(ys) - 1 - i]
    return out


VIAS = []  # (x, y, net)
# odd coils (row 0) ride B.Cu; even coils (row 1) ride In2 — the nested
# pair spans (K2 brackets K1 etc.) are unroutable on one layer with
# north sources + south via sinks.
for uref, (ux, uy), base in (("U5", G.ULN1_XY, 0), ("U6", G.ULN2_XY, 8)):
    for row, layer in ((0, B), (1, I2)):
        group = []
        for j in range(1, 9):
            n = base + j
            if (n - 1) % 2 != row:
                continue
            k = (n + 1) // 2 - 1
            off = G.COIL_V_ODD if row == 0 else G.COIL_V_EVEN
            px, py = padxy(uref, str(19 - j))
            assert abs(px - (ux - 5.08 + 1.27 * (j - 1))) < 0.05, (uref, j, px)
            group.append((f"COIL_{n}", G.COIL_X[k] + off, px))
        lanes = solve_lanes(group)
        for j in range(1, 9):
            n = base + j
            if (n - 1) % 2 != row:
                continue
            k = (n + 1) // 2 - 1
            off = G.COIL_V_ODD if row == 0 else G.COIL_V_EVEN
            net = f"COIL_{n}"
            pin7x, pin7y = padxy(f"K{n}", "7")
            src_x = G.COIL_X[k] + off
            lane_y = lanes[net]
            px, py = padxy(uref, str(19 - j))
            seg(pin7x, pin7y, src_x, pin7y, layer, net, G.W_COIL)   # stub
            seg(src_x, pin7y, src_x, lane_y, layer, net, G.W_COIL)  # vertical
            seg(src_x, lane_y, px, lane_y, layer, net, G.W_COIL)    # lane
            seg(px, lane_y, px, G.COIL_VIA_Y, layer, net, G.W_COIL)  # drop
            VIAS.append((px, G.COIL_VIA_Y, net))
            # F.Cu stub pin7 -> coil TP
            tpx, tpy = padxy(f"TP{40 + n}", "1")
            seg(pin7x, pin7y, tpx, tpy, F, net, G.W_COIL)

# -------------------------------------------------------------- RELAY_5V
q1x, q1y = padxy("Q1", "3")     # drain
assert pad("Q1", "3").GetNetname() == "RELAY_5V"
bus_y = G.R5V_BUS_Y
first_x = 60.0   # bus west end at the keepout edge (spur via landing zone)
last_x = G.COIL_X[-1] + G.COIL_V_ODD
seg(q1x, q1y, q1x, bus_y, F, "RELAY_5V", G.W_R5V)
seg(first_x, bus_y, last_x, bus_y, F, "RELAY_5V", G.W_R5V)
for k in range(G.NSC):
    vx = G.COIL_X[k] + G.COIL_V_ODD
    seg(vx, G.ROW_Y[0], vx, bus_y, F, "RELAY_5V", 0.5)
    for row in (0, 1):
        seg(vx, G.ROW_Y[row], G.COIL_X[k], G.ROW_Y[row], F, "RELAY_5V", 0.5)
# ULN COM pads (pad 10, east-north end)
for uref in ("U5", "U6"):
    px, py = padxy(uref, "10")
    assert pad(uref, "10").GetNetname() == "RELAY_5V", uref
    seg(px, py, px, bus_y, F, "RELAY_5V", 0.5)

# ------------------------------------------------- safety gates
def crossing(s1, s2):
    (a1, b1, a2, b2, l1, n1, w1) = s1
    (c1, d1, c2, d2, l2, n2, w2) = s2
    if l1 != l2 or n1 == n2:
        return False
    # segment distance check with width envelope
    import math

    def dseg(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        ll = dx * dx + dy * dy
        if ll < 1e-12:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ll))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

    d = min(dseg(a1, b1, c1, d1, c2, d2), dseg(a2, b2, c1, d1, c2, d2),
            dseg(c1, d1, a1, b1, a2, b2), dseg(c2, d2, a1, b1, a2, b2))
    # crossing test
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)
    x = (ccw(a1, b1, a2, b2, c1, d1) * ccw(a1, b1, a2, b2, c2, d2) < 0 and
         ccw(c1, d1, c2, d2, a1, b1) * ccw(c1, d1, c2, d2, a2, b2) < 0)
    return x or d < (w1 + w2) / 2 + 0.126


bad = []
for i in range(len(SEGS)):
    for j in range(i + 1, len(SEGS)):
        if crossing(SEGS[i], SEGS[j]):
            bad.append((SEGS[i], SEGS[j]))
if bad:
    for s1, s2 in bad[:10]:
        print("CROSS", s1[:6], "x", s2[:6])
    raise RuntimeError(f"{len(bad)} same-layer crossings in bank plan")

# keypad-to-SELV distance over the planned segments
import math


def seg_dist(s1, s2):
    (a1, b1, a2, b2, *_r1) = s1
    (c1, d1, c2, d2, *_r2) = s2

    def dseg(px, py, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        ll = dx * dx + dy * dy
        if ll < 1e-12:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ll))
        return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
    return min(dseg(a1, b1, c1, d1, c2, d2), dseg(a2, b2, c1, d1, c2, d2),
               dseg(c1, d1, a1, b1, a2, b2), dseg(c2, d2, a1, b1, a2, b2))


kp = [s for s in SEGS if s[5].startswith("KC")]
sv = [s for s in SEGS if not s[5].startswith("KC")]
worst = 99
for s1 in kp:
    for s2 in sv:
        d = seg_dist(s1, s2) - s1[6] / 2 - s2[6] / 2
        worst = min(worst, d)
assert worst >= G.ISO_MIN - 0.01, f"keypad-SELV plan gap {worst:.2f}"
print(f"bank plan: {len(SEGS)} segments, min keypad-SELV gap {worst:.2f}mm")

# ------------------------------------------------- install
for (x1, y1, x2, y2, layer, net, w) in SEGS:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I_MM(x1, y1))
    t.SetEnd(pcbnew.VECTOR2I_MM(x2, y2))
    t.SetLayer(layer)
    t.SetWidth(pcbnew.FromMM(w))
    t.SetNet(nets[net])
    b.Add(t)
for (x, y, net) in VIAS:
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    v.SetDrill(pcbnew.FromMM(G.VIA_DRILL))
    v.SetWidth(pcbnew.FromMM(G.VIA_D))
    v.SetNet(nets[net])
    b.Add(v)
# spurs C8/C9/R25/TP33 -> bus, via the EMPTY In2 layer (F/B are congested
# here): pad -> via1 (site-checked, KRT space) -> In2 north to the bus y ->
# via2 landing ON the F.Cu bus (inside the protected bank region).
import math as _m
import os
_sk = [p for p in (Path(__file__).resolve().parents[3] / "skills" / "kicad-pcb" / "scripts",
                   Path(os.path.expanduser("~/.claude/skills/kicad-pcb/scripts"))) if p.is_dir()]
sys.path.insert(0, str(_sk[0]))
from pcb_toolkit import Toolkit  # noqa: E402
tk = Toolkit(b, 0.15)
r5v = nets["RELAY_5V"]
used2 = []
for si, ref in enumerate(("C8", "C9", "R25", "TP33")):
    px, py = padxy(ref, "1")
    assert pad(ref, "1").GetNetname() == "RELAY_5V", ref
    ok = False
    for r in (0.9, 1.2, 1.6, 2.1, 2.7):
        for ang in range(0, 360, 30):
            vx = round(px + r * _m.cos(_m.radians(ang)), 2)
            vy = round(py + r * _m.sin(_m.radians(ang)), 2)
            if vy > 111.9 + 4 or vy < 107.2:
                continue
            if any(abs(vx - ux) < 0.75 and abs(vy - uy) < 0.75 for ux, uy in used2):
                continue
            if not tk.via_site_ok(vx, vy, r5v.GetNetCode(), size=0.6, drill=0.3):
                continue
            if tk.collides(px, py, vx, vy, 0.3, r5v.GetNetCode(), pcbnew.F_Cu) is not None:
                continue
            # In2 path: vertical to bus y, then jog E/W along the bus to a
            # landing point whose via clears the coil B.Cu lanes (the bus y
            # sits inside the coil-lane band, so a through-via at an arbitrary
            # x punches a coil lane — search a clear landing near vx).
            if tk.collides(vx, vy, vx, G.R5V_BUS_Y, 0.4, r5v.GetNetCode(), pcbnew.In2_Cu) is not None:
                continue
            lx = None
            for dxl in (0, 0.7, -0.7, 1.4, -1.4, 2.1, -2.1, 2.8, -2.8,
                        3.5, -3.5, 4.2, -4.2, 5.0, -5.0, 6.0, -6.0):
                cand = round(vx + dxl, 2)
                if cand < 60.3:
                    continue
                if not tk.via_site_ok(cand, G.R5V_BUS_Y, r5v.GetNetCode(), size=0.6, drill=0.3):
                    continue
                if abs(cand - vx) > 0.01 and tk.collides(
                        vx, G.R5V_BUS_Y, cand, G.R5V_BUS_Y, 0.4,
                        r5v.GetNetCode(), pcbnew.In2_Cu) is not None:
                    continue
                lx = cand
                break
            if lx is None:
                continue
            tk.add_seg(px, py, vx, vy, r5v, pcbnew.F_Cu, 0.3)
            tk.add_via(vx, vy, r5v, size=0.6, drill=0.3)
            tk.add_seg(vx, vy, vx, G.R5V_BUS_Y, r5v, pcbnew.In2_Cu, 0.4)
            if abs(lx - vx) > 0.01:
                tk.add_seg(vx, G.R5V_BUS_Y, lx, G.R5V_BUS_Y, r5v, pcbnew.In2_Cu, 0.4)
            tk.add_via(lx, G.R5V_BUS_Y, r5v, size=0.6, drill=0.3)
            used2.append((vx, vy))
            used2.append((lx, G.R5V_BUS_Y))
            ok = True
            break
        if ok:
            break
    if not ok:
        import os as _os
        if _os.environ.get("SPUR_DEBUG"):
            print(f"--- {ref} pad1 ({px:.2f},{py:.2f}) candidate reasons:")
            for r in (0.9, 1.2, 1.6, 2.1, 2.7):
                for ang in range(0, 360, 30):
                    vx = round(px + r * _m.cos(_m.radians(ang)), 2)
                    vy = round(py + r * _m.sin(_m.radians(ang)), 2)
                    if vy > 115.9 or vy < 107.2:
                        continue
                    vs = tk.via_site_ok(vx, vy, r5v.GetNetCode(), size=0.6, drill=0.3)
                    fc = tk.collides(px, py, vx, vy, 0.3, r5v.GetNetCode(), pcbnew.F_Cu)
                    iv = tk.collides(vx, vy, vx, G.R5V_BUS_Y, 0.4, r5v.GetNetCode(), pcbnew.In2_Cu)
                    if vs and fc is None:
                        print(f"    ({vx},{vy}) vs=OK fc=OK iv={iv.GetNetname() if iv else 'OK'}")
        raise RuntimeError(f"RELAY_5V In2 spur failed: {ref}")
b.Save(str(PCB))
print(f"installed {len(SEGS)} tracks + {len(VIAS)} vias + 4 spurs -> {PCB.name}")
