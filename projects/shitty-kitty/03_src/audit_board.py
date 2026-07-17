#!/usr/bin/env python3
"""Placement/pad invariant gate for shitty-kitty. Exit 0 = pass.
I1 pads inside outline (J1 barrel, J2 USB-C, U1 module antenna exempt);
I2 connector orientations (J1/J6 open E; J2 opens W; J3/J4 pin1-west rows
at the N edge; J5/J8 vertical columns; bodies near their edges);
I3 antenna keepout SOUTH: no copper in the guard strip below the module's
pad row within the module x-span (all layers; the antenna itself is
off-board — generator asserts);
I4 body-over-mounting-hole; I5 screw-head keepout warn; I6 bbox overlaps;
I7 cap-sense separation: MPR121s + electrode headers >= 18mm from the
aggressors (U2 driver, U8 buck, L1); post-route: no ELEC-net copper south
of y=80 or east of x=137;
I8 (post-route) electrode stub length: every INNER*/OUTER* routed length
< 45mm;
I9 polarized parts + cat-safety ENN pullup (same facts as the generator:
C40/C41 pad1=VIN_12V, D2/D5 pad1=GND, D3 pad1=VIN_12V, Q1 pad2=VIN_F,
R8 = {3V3, ENN})."""
import sys
import math
from pathlib import Path
import pcbnew

PCB = Path(__file__).parent.parent / "04_kicad" / "shitty_kitty.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
X0, Y0, X1, Y1 = 50.0, 50.0, 180.0, 125.0
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
            if r in ("J1", "J2", "U1"):
                continue
            fails.append(f"I1 pad outside outline: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")

def pads_of(r):
    f = b.FindFootprintByReference(r)
    return {p.GetNumber(): p.GetPosition() for p in f.Pads() if p.GetNumber()}

def centv(r):
    f = b.FindFootprintByReference(r)
    bb = f.GetBoundingBox(False, False)
    pads = [p.GetPosition() for p in f.Pads()]
    pcx = sum(p.x for p in pads) / len(pads)
    pcy = sum(p.y for p in pads) / len(pads)
    return (bb.Centre().x - pcx) / 1e6, (bb.Centre().y - pcy) / 1e6

# I2
for ref, want in [("J1", (1, 0)), ("J6", (1, 0)), ("J2", (-1, 0))]:
    vx, vy = centv(ref)
    if vx * want[0] + vy * want[1] <= 0:
        fails.append(f"I2 {ref} opening faces the wrong way v=({vx:.2f},{vy:.2f})")
for ref in ("J3", "J4"):
    jp = pads_of(ref)
    if not (jp["1"].x < jp["13"].x and abs(jp["1"].y - jp["13"].y) < 1000):
        fails.append(f"I2 {ref} pins must run west->east")
    if MM(jp["1"].y) - Y0 > 6.0:
        fails.append(f"I2 {ref} must hug the N edge (pin row at y={MM(jp['1'].y):.1f})")
for ref, last in [("J5", "4"), ("J8", "6")]:
    jp = pads_of(ref)
    if not (jp["1"].y < jp[last].y and abs(jp["1"].x - jp[last].x) < 1000):
        fails.append(f"I2 {ref} pins must run north->south")

# I3 antenna guard strip (south): module x-span, from pad row down to edge
u1 = b.FindFootprintByReference("U1")
p1 = {p.GetNumber(): p.GetPosition() for p in u1.Pads() if p.GetNumber()}
ax0, ax1 = min(p1["1"].x, p1["40"].x) / 1e6 - 1.0, max(p1["1"].x, p1["40"].x) / 1e6 + 1.0
guard_y = p1["1"].y / 1e6 + 0.9
body_bot = p1["1"].y / 1e6 + 6.75
if body_bot - 6.0 < Y1 - 0.05:
    fails.append(f"I3 antenna area starts on-board at y={body_bot-6.0:.2f} (< {Y1})")
for t in b.GetTracks():
    x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
    if ax0 < x < ax1 and guard_y < y < Y1 + 0.01:
        fails.append(f"I3 copper in antenna guard strip at ({x:.1f},{y:.1f})")

for hr, hx, hy in holes:
    for r, (l, t, rr, bt) in boxes.items():
        if r.startswith("H"):
            continue
        if l < hx < rr and t < hy < bt:
            fails.append(f"I4 body over mounting hole: {r} covers {hr}")
        elif l - 2.9 < hx < rr + 2.9 and t - 2.9 < hy < bt + 2.9:
            warns.append(f"I5 screw-head near {r} at {hr}")

names = [r for r in boxes if not r.startswith("H")]
UB = (86.0, 105.7, 104.0, Y1)  # U1 tight body box (graphics excluded)
for i, a in enumerate(names):
    for c in names[i + 1:]:
        A, C = boxes[a], boxes[c]
        if not (A[2] <= C[0] or C[2] <= A[0] or A[3] <= C[1] or C[3] <= A[1]):
            ov = min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1])
            if a == "U1" or c == "U1":
                o = boxes[c] if a == "U1" else boxes[a]
                if o[2] <= UB[0] or UB[2] <= o[0] or o[3] <= UB[1] or UB[3] <= o[1]:
                    continue
            fails.append(f"I6 overlap {a} x {c} ({ov[0]:.1f}x{ov[1]:.1f}mm)")

# I7 cap-sense separation
CAPSENSE = ["U3", "U4", "U5", "U6", "J3", "J4"]
AGGR = ["U2", "U8", "L1"]
def center(r):
    l, t, rr, bt = boxes[r]
    return ((l + rr) / 2, (t + bt) / 2)
for a in CAPSENSE:
    ax, ay = center(a)
    for g in AGGR:
        gx, gy = center(g)
        d = math.hypot(ax - gx, ay - gy)
        if d < 18.0:
            fails.append(f"I7 cap-sense {a} within {d:.1f}mm of aggressor {g}")
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
ELEC = {f"INNER{i}" for i in range(1, 13)} | {f"OUTER{i}" for i in range(1, 13)}
if tracks:
    L = {}
    for t in tracks:
        n = t.GetNetname()
        if n in ELEC:
            for e in (t.GetStart(), t.GetEnd()):
                x, y = MM(e.x), MM(e.y)
                if y > 80.0 or x > 137.0:
                    fails.append(f"I7 ELEC net {n} copper strays to ({x:.1f},{y:.1f})")
            L[n] = L.get(n, 0) + math.hypot(MM(t.GetEnd().x - t.GetStart().x),
                                            MM(t.GetEnd().y - t.GetStart().y))
    # I8 stub lengths
    for n, ln in sorted(L.items()):
        if ln > 45.0:
            fails.append(f"I8 electrode stub {n} routed length {ln:.1f}mm > 45")
    if L:
        print(f"I8 electrode stubs: {len(L)} routed, max {max(L.values()):.1f}mm")

# I9 polarity + cat-safety
for ref, pad, want in [("C40", "1", "VIN_12V"), ("C41", "1", "VIN_12V"),
                       ("D2", "1", "GND"), ("D5", "1", "GND"),
                       ("D3", "1", "VIN_12V"), ("Q1", "2", "VIN_F"),
                       ("Q1", "3", "VIN_12V")]:
    f = b.FindFootprintByReference(ref)
    got = {p.GetNumber(): p.GetNetname() for p in f.Pads()}[pad]
    if got != want:
        fails.append(f"I9 {ref} pad{pad} net {got} != {want} (polarity)")
r8 = {p.GetNumber(): p.GetNetname() for p in b.FindFootprintByReference("R8").Pads()}
if sorted(r8.values()) != ["3V3", "ENN"]:
    fails.append(f"I9 R8 must pull ENN to 3V3 (motor off at boot), got {r8}")

print(f"pads audited across {len(names)} footprints")
for w in warns[:8]:
    print("WARN:", w)
for x in fails[:25]:
    print("FAIL:", x)
print(f"AUDIT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
sys.exit(1 if fails else 0)
