#!/usr/bin/env python3
"""Placement/pad invariant gate. Exit 0 = pass.
I1 pads inside outline; I2 connector mate-direction (edge overhang east/west);
I4 body-over-mounting-hole (screw access); I5 screw-head keepout;
I6 footprint bbox overlaps (courtyard proxy);
I9 polarized parts: pad-1 net asserted against 02_parts part.yaml facts
(canon P2: XT60 pad1='-', TVS/LED pad1=cathode/K, CP_Elec pad1='+')."""
import sys
from pathlib import Path
import pcbnew

PCB = Path(__file__).parent.parent / "04_kicad" / "usb_power_3s.kicad_pcb"
b = pcbnew.LoadBoard(str(PCB))
MM = pcbnew.ToMM
X0, Y0, X1, Y1 = 50.0, 50.0, 150.0, 110.0
EDGE = {"J1": "W", "J2": "E", "J3": "E", "J4": "E", "J5": "N"}
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
            if r in EDGE:  # connectors may overhang their mate edge
                continue
            fails.append(f"I1 pad outside outline: {r}.{p.GetNumber()} at ({x:.1f},{y:.1f})")
for r, side in EDGE.items():
    l, t, rr, bt = boxes[r]
    ok = (side == "W" and l < X0) or (side == "E" and rr > X1) or (side == "N" and t < Y0)
    if not ok:
        fails.append(f"I2 {r} must overhang the {side} edge (body {l:.0f}..{rr:.0f})")
for hr, hx, hy in holes:
    for r, (l, t, rr, bt) in boxes.items():
        if r.startswith("H"):
            continue
        if l < hx < rr and t < hy < bt:
            fails.append(f"I4 body over mounting hole: {r} covers {hr}")
        elif l - 3.2 < hx < rr + 3.2 and t - 3.2 < hy < bt + 3.2:
            warns.append(f"I5 screw-head near {r} at {hr}")
names = [r for r in boxes if not r.startswith("H")]
for i, a in enumerate(names):
    for c in names[i + 1:]:
        A, C = boxes[a], boxes[c]
        if not (A[2] <= C[0] or C[2] <= A[0] or A[3] <= C[1] or C[3] <= A[1]):
            ov = min(A[2], C[2]) - max(A[0], C[0]), min(A[3], C[3]) - max(A[1], C[1])
            fails.append(f"I6 overlap {a} x {c} ({ov[0]:.1f}x{ov[1]:.1f}mm)")
# I9 polarized parts (canon P2). Expected pad-1 net comes from the part.yaml
# polarity FACTS in 02_parts (pins: blocks quoted in each tuple's comment):
#   XT60PW-M      pad1 = '-' blade        -> GND        ("PIN 1 IS NEGATIVE")
#   SMBJ16A/5.0A  pad1 = K (cathode,band) -> + rail     (unidirectional TVS)
#   KT-0805G LED  pad1 = K (cathode)      -> GND
#   EEHZA1V101P / 6SVPC220MV pad1 = '+'   -> + rail     (CP_Elec convention)
POLARITY = [
    # (ref, pad, expected_net, why)
    ("J1", "1", "GND", "XT60 '-' blade to GND (XT60PW-M pad1=minus)"),
    ("J1", "2", "VBATT_RAW", "XT60 '+' blade to battery rail"),
    ("D1", "1", "VBATT_F", "SMBJ16A cathode to protected +rail"),
    ("D2", "1", "5V_A", "SMBJ5.0A cathode to 5V_A"),
    ("D3", "1", "5V_C", "SMBJ5.0A cathode to 5V_C"),
    ("D4", "1", "GND", "LED cathode to GND (KT-0805G pad1=K)"),
    ("D5", "1", "GND", "LED cathode to GND (KT-0805G pad1=K)"),
    ("CE1", "1", "VSW", "EEHZA1V101P '+' to VSW (CP_Elec pad1=+)"),
    ("CA7", "1", "5V_C", "6SVPC220MV '+' to buck-A output"),
    ("CB7", "1", "5V_A", "6SVPC220MV '+' to buck-B output"),
]
npol = 0
for ref, pad, want, why in POLARITY:
    fp = b.FindFootprintByReference(ref)
    if fp is None:
        fails.append(f"I9 polarized part {ref} missing from board")
        continue
    got = {p.GetNumber(): p.GetNetname() for p in fp.Pads()}.get(pad)
    if got != want:
        fails.append(f"I9 polarity: {ref} pad{pad} on {got}, want {want} ({why})")
    else:
        npol += 1
print(f"I9 POLARITY: {npol}/{len(POLARITY)} pad-1 net checks pass")

print(f"pads audited across {len(names)} footprints")
for w in warns[:8]:
    print("WARN:", w)
for x in fails[:25]:
    print("FAIL:", x)
print(f"AUDIT: {'PASS' if not fails else 'FAIL'} ({len(fails)} fails, {len(warns)} warns)")
sys.exit(1 if fails else 0)
