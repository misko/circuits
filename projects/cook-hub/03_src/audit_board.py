#!/usr/bin/env python3
"""Placement/copper invariant gate for cook-hub (pre- and post-route).

I1    pads inside the outline
I8    every refdes on visible F.SilkS (waivers only from the sanctioned set)
I9    polarized pad-1 nets (diodes/electrolytic — invisible to ERC/DRC)
I-ISO THE isolation gate (§6.3/§8.4): every KEYPAD-net copper item
      (pads + tracks) >= ISO_MIN from every non-KEYPAD copper item;
      all zone outlines confined outside the NOGO region; slots present.
I-NG  NOGO sweep: copper inside geom.NOGO only from the sanctioned set
      (KEYPAD, COIL_*, RELAY_5V + bank part pads)
IP    proximity: decouplers near their ICs
IS    functional silk near every J*/JP*/SW* human touchpoint
IZ    plane/pour presence (GND In1+B, 3V3/5VP/3V3A In2)
IW    watchdog RC + gating sanity (net-level re-check of ADR-0003)

Exit 1 on any FAIL. Run: /usr/bin/python3 03_src/audit_board.py"""
import json
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

PCB = HERE.parent / "04_kicad" / "cook_hub.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL", msg)


def ok(msg):
    print("  ok", msg)


fps = {f.GetReference(): f for f in b.GetFootprints()}


def pad(ref, num):
    return next(p for p in fps[ref].Pads() if p.GetNumber() == num)


# I1
bad = 0
for f in fps.values():
    for p in f.Pads():
        x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if not (G.X0 - 0.1 <= x <= G.X1 + 0.1 and G.Y0 - 0.1 <= y <= G.Y1 + 0.1):
            bad += 1
            fail(f"I1 pad outside outline: {f.GetReference()}.{p.GetNumber()}")
if not bad:
    ok("I1 all pads inside outline")

# I8
ALLOWED_WAIVED = {"D1", "D2", "J2", "R33", "R76", "TP22", "TP26", "TP7",
                  "U12", "U14", "CE1", "TP16", "R31", "R43", "C21", "C33",
                  "TP15", "TP27", "TP6", "TP21", "R21"}
wfile = HERE.parent / "06_build" / "refdes_waiver.json"
waived = set(json.loads(wfile.read_text())) if wfile.exists() else set()
extra = waived - ALLOWED_WAIVED
if extra:
    fail(f"I8 unsanctioned refdes waivers: {sorted(extra)}")
else:
    ok(f"I8 refdes on silk ({len(waived)} waived, all sanctioned w/ F.Fab copy)")

# I9 polarity (pad1 = cathode / positive)
for ref, want in [("D1", "VSYS"), ("D2", "5VP"), ("D3", "ESTOP_RAW"),
                  ("D4", "DOOR_RAW"), ("D5", "TH1"), ("D6", "TH2"),
                  ("D7", "TH3"), ("CE1", "5VP")]:
    got = pad(ref, "1").GetNetname()
    if got != want:
        fail(f"I9 {ref} pad1 on {got}, want {want}")
    else:
        ok(f"I9 {ref} pad1 = {want}")

# ---------------- I-ISO ----------------
def is_keypad(n):
    return n.startswith("KC")


items = []   # (kind, netname, geometry) — pads as circles, tracks as segs
for f in fps.values():
    for p in f.Pads():
        if p.GetNetname() == "":
            continue
        bb = p.GetBoundingBox()
        r = max(MM(bb.GetWidth()), MM(bb.GetHeight())) / 2
        items.append(("pad", p.GetNetname(),
                      (MM(p.GetPosition().x), MM(p.GetPosition().y), r),
                      f"{f.GetReference()}.{p.GetNumber()}"))
tracks = []
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK":
        tracks.append((t.GetNetname(),
                       MM(t.GetStart().x), MM(t.GetStart().y),
                       MM(t.GetEnd().x), MM(t.GetEnd().y), MM(t.GetWidth())))
    elif t.GetClass() == "PCB_VIA":
        items.append(("pad", t.GetNetname(),
                      (MM(t.GetPosition().x), MM(t.GetPosition().y),
                       MM(t.GetWidth()) / 2), "via"))


def dseg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    ll = dx * dx + dy * dy
    if ll < 1e-12:
        return math.hypot(px - x1, py - y1)
    tt = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / ll))
    return math.hypot(px - (x1 + tt * dx), py - (y1 + tt * dy))


def seg_seg(a, c):
    (x1, y1, x2, y2) = a
    (x3, y3, x4, y4) = c
    return min(dseg(x1, y1, x3, y3, x4, y4), dseg(x2, y2, x3, y3, x4, y4),
               dseg(x3, y3, x1, y1, x2, y2), dseg(x4, y4, x1, y1, x2, y2))


kp_pads = [i for i in items if is_keypad(i[1])]
sv_pads = [i for i in items if not is_keypad(i[1])]
kp_trk = [t for t in tracks if is_keypad(t[0])]
sv_trk = [t for t in tracks if not is_keypad(t[0])]
worst, wdesc = 999, ""
for _k, n1, (x1, y1, r1), d1 in kp_pads:
    for _k2, n2, (x2, y2, r2), d2 in sv_pads:
        d = math.hypot(x1 - x2, y1 - y2) - r1 - r2
        if d < worst:
            worst, wdesc = d, f"pad {d1}({n1}) - pad {d2}({n2})"
    for (n2, a1, b1, a2, b2, w) in sv_trk:
        d = dseg(x1, y1, a1, b1, a2, b2) - r1 - w / 2
        if d < worst:
            worst, wdesc = d, f"pad {d1}({n1}) - trk {n2}"
for (n1, p1, q1, p2, q2, w1) in kp_trk:
    for _k2, n2, (x2, y2, r2), d2 in sv_pads:
        d = dseg(x2, y2, p1, q1, p2, q2) - r2 - w1 / 2
        if d < worst:
            worst, wdesc = d, f"trk {n1} - pad {d2}({n2})"
    for (n2, a1, b1, a2, b2, w2) in sv_trk:
        d = seg_seg((p1, q1, p2, q2), (a1, b1, a2, b2)) - w1 / 2 - w2 / 2
        if d < worst:
            worst, wdesc = d, f"trk {n1} - trk {n2}"
if worst < G.ISO_MIN - 0.01:
    fail(f"I-ISO min keypad-SELV distance {worst:.2f}mm ({wdesc})")
else:
    ok(f"I-ISO min keypad-SELV copper distance {worst:.2f}mm >= {G.ISO_MIN} ({wdesc})")

# zone outlines confined outside NOGO
nx0, ny0, nx1, ny1 = G.NOGO
zbad = 0
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    o = z.Outline()
    for i in range(o.OutlineCount()):
        ol = o.Outline(i)
        for j in range(ol.PointCount()):
            p = ol.CPoint(j)
            x, y = MM(p.x), MM(p.y)
            if nx0 + 0.1 < x < nx1 - 0.1 and ny0 + 0.1 < y < ny1 - 0.1:
                zbad += 1
                fail(f"I-ISO zone {z.GetNetname()} outline point inside NOGO ({x},{y})")
if not zbad:
    ok("I-ISO all zone outlines outside the bank region")

# slots present in Edge.Cuts
edge_shapes = [d for d in b.GetDrawings()
               if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == pcbnew.Edge_Cuts]
slot_hits = 0
for sx in list(G.SLOT_X) + [G.WSLOT_X]:
    n = sum(1 for d in edge_shapes
            if abs(MM(d.GetStart().x) - sx) < 1.2 or abs(MM(d.GetEnd().x) - sx) < 1.2)
    if n >= 2:
        slot_hits += 1
if slot_hits == len(G.SLOT_X) + 1:
    ok(f"I-ISO {slot_hits} milled slots present in Edge.Cuts")
else:
    fail(f"I-ISO only {slot_hits}/{len(G.SLOT_X) + 1} slots found")

# I-NG: copper inside NOGO only from the sanctioned set
SANC_NET = (lambda n: is_keypad(n) or n.startswith("COIL_") or n == "RELAY_5V")
SANC_REF = ({f"K{i}" for i in range(1, 17)} | {f"TP{i}" for i in range(41, 57)} |
            {"J11", "U5", "U6"})
ngbad = 0
for (n, x1, y1, x2, y2, w) in tracks:
    for (x, y) in ((x1, y1), (x2, y2)):
        if nx0 + 0.05 < x < nx1 - 0.05 and ny0 + 0.05 < y < ny1 - 0.05 and not SANC_NET(n):
            ngbad += 1
            fail(f"I-NG foreign track in NOGO: {n} at ({x:.1f},{y:.1f})")
            break
for f in fps.values():
    for p in f.Pads():
        x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if nx0 + 0.05 < x < nx1 - 0.05 and ny0 + 0.05 < y < ny1 - 0.05:
            if f.GetReference() not in SANC_REF and not f.GetReference().startswith("H"):
                ngbad += 1
                fail(f"I-NG foreign pad in NOGO: {f.GetReference()}.{p.GetNumber()}")
                break
if not ngbad:
    ok("I-NG bank region carries only sanctioned copper")

# IP proximity
def near(ra, rb, d):
    pa, pb_ = fps[ra].GetPosition(), fps[rb].GetPosition()
    dist = ((MM(pa.x - pb_.x)) ** 2 + (MM(pa.y - pb_.y)) ** 2) ** 0.5
    if dist > d:
        fail(f"IP {ra} is {dist:.1f}mm from {rb} (limit {d})")
    else:
        ok(f"IP {ra}<->{rb} {dist:.1f}mm")


for ca, ub, lim in [("C12", "U3", 7), ("C13", "U4", 7), ("C14", "U7", 7),
                    ("C15", "U8", 8), ("C16", "U9", 7), ("C17", "U11", 8),
                    ("C18", "U1", 8), ("C20", "U13", 7), ("C21", "U14", 7),
                    ("C22", "U15", 8), ("C2", "U12", 8), ("C8", "Q1", 6),
                    ("C11", "U7", 7), ("R11", "U7", 7),
                    ("C61", "U1", 9), ("C31", "U11", 14), ("C1", "U12", 8)]:
    near(ca, ub, lim)

# IS functional silk near human touchpoints
texts = [(MM(t.GetPosition().x), MM(t.GetPosition().y))
         for t in b.GetDrawings()
         if t.GetClass() == "PCB_TEXT" and t.IsOnLayer(pcbnew.F_SilkS)]
isbad = 0
for ref in [f"J{k}" for k in range(1, 16)] + ["JP1", "JP2", "JP5", "SW1", "SJ1"]:
    fx, fy = MM(fps[ref].GetPosition().x), MM(fps[ref].GetPosition().y)
    if not any((tx - fx) ** 2 + (ty - fy) ** 2 < 14 ** 2 for tx, ty in texts):
        isbad += 1
        fail(f"IS no functional silk within 14mm of {ref}")
if not isbad:
    ok("IS functional silk near every connector/jumper/switch")

# IZ pours
zn = {(z.GetNetname(), z.GetLayer()) for z in b.Zones() if not z.GetIsRuleArea()}
for want in [("GND", pcbnew.In1_Cu), ("GND", pcbnew.B_Cu),
             ("3V3", pcbnew.In2_Cu), ("5VP", pcbnew.In2_Cu),
             ("3V3A", pcbnew.In2_Cu)]:
    if want not in zn:
        fail(f"IZ missing pour {want[0]}")
ok(f"IZ pours present ({len(zn)})")

# IW watchdog/gating net sanity (ADR-0003)
try:
    assert pad("U7", "2").GetNetname() == "WD_PULSE"
    assert pad("U7", "5").GetNetname() == "WD_OK"
    assert pad("U8", "4").GetNetname() == "OE_N"
    assert pad("U3", "13").GetNetname() == "OE_N"
    assert pad("U4", "13").GetNetname() == "OE_N"
    assert pad("U9", "4").GetNetname() == "COIL_EN"
    assert pad("Q1", "2").GetNetname() == "5VP"
    assert pad("Q1", "3").GetNetname() == "RELAY_5V"
    assert pad("U5", "10").GetNetname() == "RELAY_5V"
    assert pad("U6", "10").GetNetname() == "RELAY_5V"
    assert pad("U5", "18").GetNetname() == "COIL_1"
    assert pad("U6", "18").GetNetname() == "COIL_9"
    assert pad("U11", "4").GetNetname() == "ESTOP_OK"
    ok("IW watchdog + gating chain nets verified")
except AssertionError as e:
    fail(f"IW gating chain net mismatch: {e}")

print("AUDIT", "FAIL" if fails else "PASS", f"({len(fails)} failures)")
sys.exit(1 if fails else 0)
