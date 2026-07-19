#!/usr/bin/env python3
"""Placement/pad invariant gate for ble-bus-bar (run pre-route and post-route).

I1  pads inside the outline
I8  every refdes on visible F.SilkS (waivers only from the sanctioned set)
I9  polarized pad-1 nets (diodes/TVS/LEDs — the un-checkable-by-ERC bug)
IK  I-KELVIN: shunt sense taps attach at the pad INNER edges (machine-
    checkable Kelvin invariant, ADR-0003); tap width <= 0.5mm
IA  antenna keepout free of copper (tracks/vias/foreign pads)
IP  proximity: decouplers near their ICs
IS  P-SILK-FN: functional text near every J*/F*/SW* human touchpoint
IZ  power zones present per power net

Exit 1 on any FAIL. Run: /usr/bin/python3 03_src/audit_board.py
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

PCB = HERE.parent / "04_kicad" / "ble_bus_bar.kicad_pcb"
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


# I1: pads inside outline
bad = 0
for f in fps.values():
    for p in f.Pads():
        x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if not (G.X0 - 0.1 <= x <= G.X1 + 0.1 and G.Y0 - 0.1 <= y <= G.Y1 + 0.1):
            bad += 1
            fail(f"I1 pad outside outline: {f.GetReference()}.{p.GetNumber()} ({x:.1f},{y:.1f})")
if not bad:
    ok("I1 all pads inside outline")

# I8: refdes on silk
ALLOWED_WAIVED = {"J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J9",
                  "SW1", "SW2", "U7", "LED1", "LED2",
                  "C8", "R20"}   # J/SW/U7/LED carry functional silk; C8 sits in the module-pad shadow
wfile = HERE.parent / "06_build" / "refdes_waiver.json"
waived = set(json.loads(wfile.read_text())) if wfile.exists() else set()
extra = waived - ALLOWED_WAIVED
if extra:
    fail(f"I8 unsanctioned refdes waivers: {sorted(extra)}")
else:
    ok(f"I8 refdes on silk (waived to functional labels: {sorted(waived)})")

# I9: polarity pad-1 nets
POL = [("D7", "VIN_E"), ("D8", "3V3"), ("D9", "VBUS"), ("D10", "VIN_E"),
       ("D11", "SW"), ("LED1", "GND"), ("LED2", "GND")]
for ref, want in POL:
    got = pad(ref, "1").GetNetname()
    if got != want:
        fail(f"I9 {ref} pad1 (cathode) on {got}, want {want}")
    else:
        ok(f"I9 {ref} pad1 = {want}")

# IK: Kelvin attach points
for i in range(1, 7):
    cx = G.CX[i - 1]
    for netn, padn, inner_y, name in [
            (f"VF{i}", "1", 75.12, "KP"), (f"VP{i}", "2", 72.88, "KN")]:
        p = pad(f"RS{i}", padn)
        pb = p.GetBoundingBox()
        pl, pt = MM(pb.GetLeft()), MM(pb.GetTop())
        pr, pbm = MM(pb.GetRight()), MM(pb.GetBottom())
        found = None
        for t in b.GetTracks():
            if t.GetClass() != "PCB_TRACK" or t.GetNetname() != netn:
                continue
            for end in (t.GetStart(), t.GetEnd()):
                ex, ey = MM(end.x), MM(end.y)
                if pl <= ex <= pr and pt <= ey <= pbm:
                    found = (ex, ey, MM(t.GetWidth()))
        if not found:
            fail(f"IK {name}{i}: no {netn} tap attaches inside RS{i} pad{padn}")
            continue
        ex, ey, w = found
        if abs(ey - inner_y) > 1.0:
            fail(f"IK {name}{i}: tap at y={ey:.2f} not at inner edge ({inner_y})")
        elif w > 0.5:
            fail(f"IK {name}{i}: tap width {w} > 0.5 (not a sense tap)")
        else:
            ok(f"IK {name}{i} attach ({ex:.2f},{ey:.2f}) w={w}")

# IA: antenna keepout free of copper
ax0, ax1, ay0, ay1 = G.ANT_KEEPOUT
bad = 0
for t in b.GetTracks():
    for end in (t.GetStart(), t.GetEnd()):
        x, y = MM(end.x), MM(end.y)
        if ax0 < x < ax1 and ay0 < y < ay1:
            bad += 1
            fail(f"IA copper in antenna keepout at ({x:.1f},{y:.1f}) net {t.GetNetname()}")
            break
for f in fps.values():
    if f.GetReference().startswith("H"):
        continue   # NPTH mounting holes carry no copper
    for p in f.Pads():
        x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if ax0 < x < ax1 and ay0 < y < ay1:
            bad += 1
            fail(f"IA pad in antenna keepout: {f.GetReference()}.{p.GetNumber()}")
if not bad:
    ok("IA antenna keepout clean")

# IP: proximity
def near(ra, rb, d):
    pa, pb_ = fps[ra].GetPosition(), fps[rb].GetPosition()
    dist = ((MM(pa.x - pb_.x)) ** 2 + (MM(pa.y - pb_.y)) ** 2) ** 0.5
    if dist > d:
        fail(f"IP {ra} is {dist:.1f}mm from {rb} (limit {d})")
    else:
        ok(f"IP {ra}<->{rb} {dist:.1f}mm")


for i in range(1, 7):
    near(f"CB{i}", f"U{i}", 5.0)
    near(f"CD{i}", f"U{i}", 13.0)
near("C8", "U7", 13.5)
near("C4", "U8", 6.0)
near("C9", "U11", 7.0)   # C9 sits 3.7mm from U11 pin 8 (VCC); center distance misleads
near("C1", "U8", 8.0)
near("D11", "U8", 6.5)
near("C12", "U9", 8.5)

# IS: functional silk near human touchpoints
texts = [(MM(t.GetPosition().x), MM(t.GetPosition().y))
         for t in b.GetDrawings()
         if t.GetClass() == "PCB_TEXT" and t.IsOnLayer(pcbnew.F_SilkS)]
for ref in [f"J{k}" for k in range(1, 10)] + [f"F{k}" for k in range(1, 8)] + ["SW1", "SW2"]:
    fx, fy = MM(fps[ref].GetPosition().x), MM(fps[ref].GetPosition().y)
    if not any((tx - fx) ** 2 + (ty - fy) ** 2 < 13 ** 2 for tx, ty in texts):
        fail(f"IS no functional silk within 13mm of {ref}")
ok("IS functional silk checked")

# IZ: power zones present
znets = {z.GetNetname() for z in b.Zones() if not z.GetIsRuleArea()}
for n in ["VBUS", "GND"] + [f"VF{i}" for i in range(1, 7)] + [f"VP{i}" for i in range(1, 7)]:
    if n not in znets:
        fail(f"IZ no pour for power net {n}")
ok(f"IZ power pours present ({len(znets)} zone nets)")

print("AUDIT", "FAIL" if fails else "PASS", f"({len(fails)} failures)")
sys.exit(1 if fails else 0)
