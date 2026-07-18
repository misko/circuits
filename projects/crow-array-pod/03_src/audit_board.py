#!/usr/bin/env python3
"""Placement/pad invariant gate. Exit 0 = pass.
I1 pads inside outline INCLUDING the concave corner cutouts;
I2 J1 mate direction (wire openings W, body near the W edge, pin1 N);
I3 beeper/mic separation: beeper block (BZ1,D2,D3,R12) >= 15mm from the
   mic/high-Z parts (J2,R2,C3,R3) and >= 12mm from U1;
I4 body over mounting hole; I5 screw-head keepout warn;
I6 footprint bbox overlaps;
I8 mic high-Z node length: routed AIN < 30mm total (post-route only);
I9 polarized parts: C1 pad1=5VF, D2/D3 pad1=BZ_P (cathode to supply side),
   BZ1 pad1=BZ_P (the + pad);
I10 refdes-on-silk (waivers from 06_build/refdes_waiver.json)."""
import json
import math
import sys
from pathlib import Path
import pcbnew

PCB = Path(__file__).parent.parent / "04_kicad" / "crow_array_pod.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
X0, Y0, X1, Y1 = 50.0, 50.0, 144.5, 94.5
RCUT = 6.25
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
            fails.append(f"I1 pad outside outline: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")
        for cx, cy in [(X0, Y0), (X1, Y0), (X0, Y1), (X1, Y1)]:
            if math.hypot(x - cx, y - cy) < RCUT + 0.3:
                fails.append(f"I1 pad in corner cutout: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")

# I2 J1: opening W, pin1 N, body reaches within 4mm of the W edge
j1 = b.FindFootprintByReference("J1")
bbj = j1.GetBoundingBox(False, False)
pads = [p.GetPosition() for p in j1.Pads()]
pcx = sum(p.x for p in pads) / len(pads)
vx = (bbj.Centre().x - pcx) / 1e6
if vx >= 0:
    fails.append(f"I2 J1 wire opening faces the wrong way (vx={vx:.2f})")
if MM(bbj.GetLeft()) - X0 > 4.0:
    fails.append(f"I2 J1 body must be near the W edge (starts {MM(bbj.GetLeft()):.1f})")
jp = {p.GetNumber(): p.GetPosition() for p in j1.Pads()}
if not jp["1"].y < jp["8"].y:
    fails.append("I2 J1 pin1 must be the north end")

# I3 beeper aggressors vs mic/amp high-Z region
def center(r):
    l, t, rr, bt = boxes[r]
    return ((l + rr) / 2, (t + bt) / 2)
for a in ["BZ1", "D2", "D3", "R12"]:
    ax, ay = center(a)
    for g, dmin in [("J2", 15.0), ("R2", 15.0), ("C3", 15.0), ("R3", 15.0), ("U1", 12.0)]:
        gx, gy = center(g)
        d = math.hypot(ax - gx, ay - gy)
        if d < dmin:
            fails.append(f"I3 beeper part {a} within {d:.1f}mm of {g} (min {dmin})")

for hr, hx, hy in holes:
    for r, (l, t, rr, bt) in boxes.items():
        if r.startswith("H"):
            continue
        if l < hx < rr and t < hy < bt:
            fails.append(f"I4 body over mounting hole: {r} covers {hr}")
        elif l - 2.4 < hx < rr + 2.4 and t - 2.4 < hy < bt + 2.4:
            warns.append(f"I5 screw-head near {r} at {hr}")

names = [r for r in boxes if not r.startswith("H")]
for i, a in enumerate(names):
    for c in names[i + 1:]:
        A, C = boxes[a], boxes[c]
        if not (A[2] <= C[0] or C[2] <= A[0] or A[3] <= C[1] or C[3] <= A[1]):
            ov = min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1])
            fails.append(f"I6 overlap {a} x {c} ({ov[0]:.1f}x{ov[1]:.1f}mm)")

# I8 mic node length (routed boards only): AIN is the 100k node. Bar =
# 30mm: minimal escape-true path is ~14mm, the router settles ~25mm; at
# x3 system gain over a continuous GND pour the pickup on 25mm is
# negligible (bar exists to catch a PLACEMENT regression, e.g. the mic
# conditioning drifting away from +IN_A, not to shave router slack).
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
if tracks:
    L = 0.0
    for t in tracks:
        if t.GetNetname() == "AIN":
            L += math.hypot((t.GetEnd().x - t.GetStart().x) / 1e6,
                            (t.GetEnd().y - t.GetStart().y) / 1e6)
    if L > 30.0:
        fails.append(f"I8 AIN routed length {L:.1f}mm > 30 (high-Z node)")
    else:
        print(f"I8 AIN routed length {L:.1f}mm")

# I9 polarized parts (part.yaml facts: CP pad1=+, D_SMA pad1=K, CMT pad1=+)
for ref, pad, want in [("C1", "1", "5VF"), ("D2", "1", "BZ_P"),
                       ("D3", "1", "BZ_P"), ("BZ1", "1", "BZ_P")]:
    f = b.FindFootprintByReference(ref)
    got = {p.GetNumber(): p.GetNetname() for p in f.Pads()}[pad]
    if got != want:
        fails.append(f"I9 {ref} pad{pad} net {got} != {want} (polarity)")

# I10 refdes-on-silk
wf = PCB.parent.parent / "06_build" / "refdes_waiver.json"
WAIVED = set(json.loads(wf.read_text())) if wf.exists() else set()
SILK_LAYERS = (pcbnew.F_SilkS, pcbnew.B_SilkS)
for f in b.GetFootprints():
    r = f.GetReference()
    if r.startswith("H"):
        continue
    ref = f.Reference()
    if ref.GetLayer() not in SILK_LAYERS or not ref.IsVisible():
        if r in WAIVED and r[0] in "RC":
            warns.append(f"I10 refdes {r} waived to Fab (no clear silk spot)")
        else:
            fails.append(f"I10 refdes not on silk: {r} "
                         f"(layer={ref.GetLayerName()}, vis={ref.IsVisible()})")

print(f"pads audited across {len(names)} footprints")
for w in warns[:8]:
    print("WARN:", w)
for x in fails[:25]:
    print("FAIL:", x)
print(f"AUDIT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
sys.exit(1 if fails else 0)
