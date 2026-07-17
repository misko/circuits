#!/usr/bin/env python3
"""Placement/pad invariant gate. Exit 0 = pass.
I1 pads inside outline; I2 connector mate-direction (J1 overhangs W; J2/J3
openings within 1.5mm of E edge); I3 In1 carries nothing but the GND zone
(ADR-0004 continuous plane); I4 body-over-mounting-hole; I5 screw-head
keepout warn; I6 footprint bbox overlaps; I7 analog/aggressor separation
(preamp+mic parts >= 5mm from Y1 crystal and DP/DM parts)."""
import sys
from pathlib import Path
import pcbnew

PCB = Path(__file__).parent.parent / "04_kicad" / "crowsync_recorder.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
X0, Y0, X1, Y1 = 50.0, 50.0, 115.0, 92.0
fails, warns = [], []
boxes = {}
holes = []
for f in b.GetFootprints():
    r = f.GetReference()
    bb = f.GetBoundingBox(False, False)
    boxes[r] = (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
    if r.startswith("H"):
        holes.append((r, MM(f.GetPosition().x), MM(f.GetPosition().y)))
        continue
    for p in f.Pads():
        x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if not (X0 - 0.1 < x < X1 + 0.1 and Y0 - 0.1 < y < Y1 + 0.1):
            if r == "J1":
                continue  # USB-C overhangs its mate edge
            fails.append(f"I1 pad outside outline: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")

# I2 mate directions
l, t, rr, bt = boxes["J1"]
if not l < X0:
    fails.append(f"I2 J1 must overhang the W edge (body {l:.1f}..{rr:.1f})")
for ref in ("J2", "J3"):
    l, t, rr, bt = boxes[ref]
    if X1 - rr > 1.5:
        fails.append(f"I2 {ref} opening must sit within 1.5mm of the E edge (body ends {rr:.1f})")

# I3: In1 = continuous GND only
for z in b.Zones():
    if z.GetLayerSet().Contains(pcbnew.In1_Cu) and z.GetNetname() != "GND":
        fails.append(f"I3 non-GND zone on In1: {z.GetNetname()}")
for tr in b.GetTracks():
    if tr.GetClass() == "PCB_TRACK" and tr.GetLayer() == pcbnew.In1_Cu:
        fails.append("I3 track routed on In1 (continuous plane, ADR-0004)")
        break

for hr, hx, hy in holes:
    for r, (l, t, rr, bt) in boxes.items():
        if r.startswith("H"):
            continue
        if l < hx < rr and t < hy < bt:
            fails.append(f"I4 body over mounting hole: {r} covers {hr}")
        elif l - 2.8 < hx < rr + 2.8 and t - 2.8 < hy < bt + 2.8:
            warns.append(f"I5 screw-head near {r} at {hr}")

names = [r for r in boxes if not r.startswith("H")]
for i, a in enumerate(names):
    for c in names[i + 1:]:
        A, C = boxes[a], boxes[c]
        if not (A[2] <= C[0] or C[2] <= A[0] or A[3] <= C[1] or C[3] <= A[1]):
            ov = min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1])
            fails.append(f"I6 overlap {a} x {c} ({ov[0]:.1f}x{ov[1]:.1f}mm)")

# I7: analog parts vs aggressors (crystal + USB entry parts)
ANALOG = ["U2", "R9", "R10", "R11", "R12", "C19", "C20", "C9", "R13", "C21", "J2"]
AGGR = ["Y1", "R1", "R2", "D1"]
def center(r):
    l, t, rr, bt = boxes[r]
    return ((l + rr) / 2, (t + bt) / 2)
for a in ANALOG:
    ax, ay = center(a)
    for g in AGGR:
        gx, gy = center(g)
        d = ((ax - gx) ** 2 + (ay - gy) ** 2) ** 0.5
        if d < 5.0:
            fails.append(f"I7 analog {a} within {d:.1f}mm of aggressor {g}")

print(f"pads audited across {len(names)} footprints")
for w in warns[:8]:
    print("WARN:", w)
for x in fails[:25]:
    print("FAIL:", x)
print(f"AUDIT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
sys.exit(1 if fails else 0)
