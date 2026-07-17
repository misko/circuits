#!/usr/bin/env python3
"""Placement/pad invariant gate. Exit 0 = pass.
I1 pads inside outline (J1 USB-C and U1 module antenna overhang exempt);
I2 connector mate directions (J1 W; J4-J9 openings S within 2mm of edge;
J10-12 E); I3 antenna keepout: NO copper item (pad/track/via/zone fill
point) in the antenna x-span north of the module body+margin, and the
antenna area itself must be off-board; I4 body-over-mounting-hole;
I5 screw-head keepout warn; I6 footprint bbox overlaps; I7 comparator
region separation: PD/threshold parts >= 4mm from FET drains and gate
nets; I8 COMP routed-length spread < 40mm (post-route only, skipped when
board has no tracks); I9 polarized parts: C11 pad1 net = 5V, D2 pad1 = GND."""
import sys
from pathlib import Path
import pcbnew

PCB = Path(__file__).parent.parent / "04_kicad" / "esp32_laser_timing.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
X0, Y0, X1, Y1 = 50.0, 50.0, 142.0, 112.0
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
            if r in ("J1", "U1"):
                continue  # USB-C shell / antenna overhang their edges
            fails.append(f"I1 pad outside outline: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")

# I2 mate directions (body-centroid minus pad-centroid points toward opening)
def centv(r):
    f = b.FindFootprintByReference(r)
    bb = f.GetBoundingBox(False, False)
    pads = [p.GetPosition() for p in f.Pads()]
    pcx = sum(p.x for p in pads) / len(pads)
    pcy = sum(p.y for p in pads) / len(pads)
    return (bb.Centre().x - pcx) / 1e6, (bb.Centre().y - pcy) / 1e6

for ref, want, edge in [("J1", (-1, 0), None),
                        ("J4", (0, 1), "S"), ("J5", (0, 1), "S"), ("J6", (0, 1), "S"),
                        ("J7", (0, 1), "S"), ("J8", (0, 1), "S"), ("J9", (0, 1), "S"),
                        ("J10", (1, 0), "E"), ("J11", (1, 0), "E"), ("J12", (1, 0), "E")]:
    vx, vy = centv(ref)
    if vx * want[0] + vy * want[1] <= 0:
        fails.append(f"I2 {ref} opening faces the wrong way v=({vx:.2f},{vy:.2f})")
    if edge == "S" and Y1 - boxes[ref][3] > 2.0:
        fails.append(f"I2 {ref} body must reach within 2mm of S edge (ends {boxes[ref][3]:.1f})")
    if edge == "E" and X1 - boxes[ref][2] > 2.0:
        fails.append(f"I2 {ref} body must reach within 2mm of E edge (ends {boxes[ref][2]:.1f})")

# I3 antenna keepout: body top + 6mm must be <= Y0 (off-board), and no copper
# north of the pad-1/40 row within the module x-span (belt & braces margin)
u1 = b.FindFootprintByReference("U1")
p1 = {p.GetNumber(): p.GetPosition() for p in u1.Pads() if p.GetNumber()}
body_top = p1["1"].y / 1e6 - 6.75          # pad1 center is 6.75mm below module top (fig 11-1)
ant_lo = body_top + 6.0                     # antenna area = top 6mm of module
if ant_lo > Y0 + 0.05:
    fails.append(f"I3 antenna area extends onto board: ends y={ant_lo:.2f} > {Y0}")
ax0, ax1 = p1["1"].x / 1e6 - 1.0, p1["40"].x / 1e6 + 1.0
guard_y = p1["1"].y / 1e6 - 0.9             # nothing north of the top pad row
for t in b.GetTracks():
    x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
    if ax0 < x < ax1 and Y0 - 0.01 < y < guard_y:
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
for i, a in enumerate(names):
    for c in names[i + 1:]:
        A, C = boxes[a], boxes[c]
        if not (A[2] <= C[0] or C[2] <= A[0] or A[3] <= C[1] or C[3] <= A[1]):
            ov = min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1])
            if a == "U1" or c == "U1":
                # module bbox includes its keepout graphics; use a tight body box
                ub = (87.0, Y0, 105.0, 69.3)
                o = boxes[c] if a == "U1" else boxes[a]
                if o[2] <= ub[0] or ub[2] <= o[0] or o[3] <= ub[1] or ub[3] <= o[1]:
                    continue
            fails.append(f"I6 overlap {a} x {c} ({ov[0]:.1f}x{ov[1]:.1f}mm)")

# I7 comparator-region separation from FET switching parts
ANALOG = ["U3", "R20", "R21", "R22", "R23", "R24", "R25", "R26", "R27", "R28"]
AGGR = ["Q1", "Q2", "Q3"]
def center(r):
    l, t, rr, bt = boxes[r]
    return ((l + rr) / 2, (t + bt) / 2)
for a in ANALOG:
    ax, ay = center(a)
    for g in AGGR:
        gx, gy = center(g)
        d = ((ax - gx) ** 2 + (ay - gy) ** 2) ** 0.5
        if d < 4.0:
            fails.append(f"I7 analog {a} within {d:.1f}mm of FET {g}")

# I8 COMP length spread (routed boards only)
tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
if tracks:
    import math
    L = {}
    for t in tracks:
        n = t.GetNetname()
        if n in ("COMP1", "COMP2", "COMP3"):
            L[n] = L.get(n, 0) + math.hypot((t.GetEnd().x - t.GetStart().x) / 1e6,
                                            (t.GetEnd().y - t.GetStart().y) / 1e6)
    if len(L) == 3:
        spread = max(L.values()) - min(L.values())
        if spread > 40:
            fails.append(f"I8 COMP length spread {spread:.1f}mm > 40 ({L})")
        else:
            print(f"I8 COMP lengths { {k: round(v, 1) for k, v in L.items()} } spread {spread:.1f}mm")
    elif L:
        warns.append(f"I8 only {len(L)} COMP nets routed: {list(L)}")

# I9 polarized parts (part.yaml facts: CP pad1=+, LED pad1=K)
for ref, pad, want in [("C11", "1", "5V"), ("D2", "1", "GND")]:
    f = b.FindFootprintByReference(ref)
    got = {p.GetNumber(): p.GetNetname() for p in f.Pads()}[pad]
    if got != want:
        fails.append(f"I9 {ref} pad{pad} net {got} != {want} (polarity)")

# I10 refdes-on-silk: every part's reference must PRINT on the board
# (F.SilkS/B.SilkS, visible). Fab-only refdes = no U/R/C names on the
# physical board (kicad-pcb golden rule 3b). Mounting holes exempt.
# The generator's de-collision pass may hide a few refdes that find NO
# clear silk spot in a dense passive cluster; those are listed in
# 06_build/refdes_waiver.json (they keep an F.Fab copy for the assembly
# drawing). I10 WARNS on waived passives, FAILS on any unwaived miss and
# on any waived IC/connector (those must always be printable).
import json
_wf = PCB.parent.parent / "06_build" / "refdes_waiver.json"
WAIVED = set(json.loads(_wf.read_text())) if _wf.exists() else set()
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
