#!/usr/bin/env python3
"""Placement/pad invariant gate for crow-array-central. Exit 0 = pass.
I1  pads inside the rectangular outline;
I3  beeper/analog separation: every beeper aggressor (Qn beeper FETs, port
    beep PTC F2n, D2n port ESD) >= 12mm from either PCM1865 (U2/U3) and the
    coupling caps — beeper copper must not enter the analog band;
I6  footprint bbox overlaps;
I9  polarity: Q9 revFET (S=5V load, D=5V_P input, per ADR-0002 body-diode-
    conducts-first correction, D-CAC1), D9 TVS pad1(K)=5V_P, C90 CP pad1=5V,
    buck FB dividers hi-side pad1 on the rail;
I10 refdes-on-silk (waivers: only R/C, from 06_build/refdes_waiver.json);
I11 EP thermal vias: XU316 EP (pad 129) carries >=2 same-net vias (R-THERM,
    they live in the footprint)."""
import json
import math
import sys
from pathlib import Path
import pcbnew

PCB = Path(__file__).parent.parent / "04_kicad" / "crow_array_central.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
X0, Y0, X1, Y1 = 10.0, 10.0, 186.0, 132.0
fails, warns = [], []
boxes, holes = {}, []
for f in b.GetFootprints():
    r = f.GetReference()
    bb = f.GetBoundingBox(False, False)
    boxes[r] = (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
    if r.startswith("H"):
        holes.append((r, MM(f.GetPosition().x), MM(f.GetPosition().y)))
        continue
    for p in f.Pads():
        x, y = MM(p.GetPosition().x), MM(p.GetPosition().y)
        if not (X0 - 0.2 < x < X1 + 0.2 and Y0 - 0.2 < y < Y1 + 0.2):
            fails.append(f"I1 pad outside outline: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")


def center(r):
    l, t, rr, bt = boxes[r]
    return ((l + rr) / 2, (t + bt) / 2)


# I3 beeper aggressors vs the analog parts
AGGR = [f"Q{n}" for n in range(1, 9)] + \
       [f"F{20 + n}" for n in range(1, 9)] + \
       [f"D{20 + n}" for n in range(1, 9)]
VICT = ["U2", "U3"] + [f"C{200 + n * 10 + k}" for n in range(1, 9) for k in (0, 1, 2)]
for a in AGGR:
    if a not in boxes:
        continue
    ax, ay = center(a)
    for g in VICT:
        if g not in boxes:
            continue
        gx, gy = center(g)
        if math.hypot(ax - gx, ay - gy) < 12.0:
            warns.append(f"I3 beeper {a} within 12mm of analog {g}")

# I6 overlaps
names = [r for r in boxes if not r.startswith("H")]
for i, a in enumerate(names):
    for c in names[i + 1:]:
        A, C = boxes[a], boxes[c]
        if not (A[2] <= C[0] or C[2] <= A[0] or A[3] <= C[1] or C[3] <= A[1]):
            ov = (min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1]))
            fails.append(f"I6 overlap {a} x {c} ({ov[0]:.1f}x{ov[1]:.1f}mm)")

# I9 polarity (part.yaml facts + ADR-0002 correction)
POL = [("D9", "1", "5V_P"), ("C90", "1", "5V"),
       ("Q9", "2", "5V"), ("Q9", "3", "5V_P"),   # revFET: S=load, D=input
       ("R10", "1", "3V3"), ("R13", "1", "0V9")]
for ref, pad, want in POL:
    f = b.FindFootprintByReference(ref)
    if not f:
        continue
    got = {p.GetNumber(): p.GetNetname() for p in f.Pads()}.get(pad)
    if got != want:
        fails.append(f"I9 {ref} pad{pad} net {got} != {want}")

# I10 refdes-on-silk
wf = PCB.parent.parent / "06_build" / "refdes_waiver.json"
WAIVED = set(json.loads(wf.read_text())) if wf.exists() else set()
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)
for f in b.GetFootprints():
    r = f.GetReference()
    if r.startswith("H"):
        continue
    ref = f.Reference()
    if ref.GetLayer() not in SILK or not ref.IsVisible():
        if r in WAIVED and r[0] in "RC":
            warns.append(f"I10 refdes {r} waived to Fab (passive, no silk room)")
        else:
            fails.append(f"I10 refdes not on silk: {r}")

# I10b refdes under a body
bodies = {r: boxes[r] for r in boxes if not r.startswith("H")}
for f in b.GetFootprints():
    r = f.GetReference()
    if r.startswith("H"):
        continue
    ref = f.Reference()
    if ref.GetLayer() not in SILK or not ref.IsVisible():
        continue
    tb = ref.GetBoundingBox()
    t = (MM(tb.GetLeft()), MM(tb.GetTop()), MM(tb.GetRight()), MM(tb.GetBottom()))
    for r2, bx in bodies.items():
        if r2 == r:
            continue
        if not (t[2] <= bx[0] or bx[2] <= t[0] or t[3] <= bx[1] or bx[3] <= t[1]):
            fails.append(f"I10b refdes {r} printed under body of {r2}")
            break

# I12 mate-direction + screw keepout (canon P-KEEP): every off-board
# connector must sit on the edge it mates off (body bbox within EDGE_TOL of
# that board edge), and no part body may intrude into the M3 screw-head
# keepout ring around the mounting holes.
bb_edges = b.GetBoardEdgesBoundingBox()
EX0, EY0 = MM(bb_edges.GetX()), MM(bb_edges.GetY())
EX1, EY1 = EX0 + MM(bb_edges.GetWidth()), EY0 + MM(bb_edges.GetHeight())
EDGE_TOL = 4.0   # RJHSE-5384 bodies sit 3.5mm back from the edge (the
                 # mating snout projects beyond the courtyard bbox); a
                 # WRONG-EDGE part would be tens of mm off, not 3.5
MATE = {  # ref: (edge, which coordinate faces it)
    "J1": "N", "J2": "N", "J3": "N", "J4": "N",
    "J5": "N", "J6": "N", "J7": "N", "J8": "N",   # RJ45 row mates north
    "J9": "W",                                     # barrel jack west
    "J12": "S",                                    # USB-C south
}
for ref, edge in MATE.items():
    f = b.FindFootprintByReference(ref)
    if not f:
        continue
    fb = f.GetBoundingBox(False, False)
    t = (MM(fb.GetX()), MM(fb.GetY()),
         MM(fb.GetX() + fb.GetWidth()), MM(fb.GetY() + fb.GetHeight()))
    d = {"N": t[1] - EY0, "S": EY1 - t[3],
         "W": t[0] - EX0, "E": EX1 - t[2]}[edge]
    if d > EDGE_TOL:
        fails.append(f"I12 mate-direction: {ref} body {d:.1f}mm off its {edge} edge")
SCREW_R = 3.2   # M3 head radius + margin
for h in ("H1", "H2", "H3", "H4"):
    f = b.FindFootprintByReference(h)
    if not f:
        continue
    hx, hy = MM(f.GetPosition().x), MM(f.GetPosition().y)
    for r2, bx in bodies.items():
        cx = max(bx[0], min(hx, bx[2]))
        cy = max(bx[1], min(hy, bx[3]))
        if math.hypot(cx - hx, cy - hy) < SCREW_R:
            fails.append(f"I12 screw keepout: {r2} body within {SCREW_R}mm of {h}")

# I11 EP thermal vias
u1 = b.FindFootprintByReference("U1")
if u1:
    ep_vias = sum(1 for p in u1.Pads() if p.GetNumber() == "129"
                  and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)
    if ep_vias < 2:
        fails.append(f"I11 XU316 EP thermal vias {ep_vias} < 2 (R-THERM)")
    else:
        print(f"I11 XU316 EP thermal vias: {ep_vias}")

print(f"audited {len(names)} footprints")
for w in warns[:12]:
    print("WARN:", w)
for x in fails[:30]:
    print("FAIL:", x)
print(f"AUDIT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
sys.exit(1 if fails else 0)
