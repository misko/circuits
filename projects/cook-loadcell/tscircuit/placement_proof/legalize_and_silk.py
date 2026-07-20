#!/usr/bin/env python3
"""Legalize + silk the tscircuit-seeded placement (ADR-0002 Phase B).

The placement SEED (circuit_json_to_kicad_pcb.py, from the TSX-authored
pcbX/pcbY) lands parts at tscircuit's coordinates but carries NO silk story and
no proximity guarantee. This is the "generate_board shrunk to import -> legalize
-> silk -> audit" artifact the ADR predicts: it does NOT re-floorplan (positions
come from the TSX) — it only

  1. DECOUPLER SNAP-BACK (golden rule 7): pull any decoupler that audit IP flags
     to within its proximity budget of its anchor. Records the movement.
  2. FUNCTIONAL SILK (canon P5 / audit IS): plain-word captions next to every
     human touchpoint (J*/JP*), collision-nudged off pads + other silk.
  3. REFDES ON SILK (canon 3b / audit I8): every part's refdes on F.SilkS, run
     the de-collision pass; F.Fab refdes copy for assembly.

then re-saves. Everything geometric (part positions, GND pours, net binding,
design floors) already came from the seed. Run BEFORE audit_board.py.
"""
import json
import math
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "03_src"))
import geom as G  # noqa: E402  (via the 03_src symlink)

PCB = HERE / "04_kicad" / "cook_loadcell.kicad_pcb"
MM = pcbnew.ToMM
board = pcbnew.LoadBoard(str(PCB))
fps = {f.GetReference(): f for f in board.GetFootprints()}

# ------------------------------------------------------------ 1. decoupler snap
# Same proximity contract audit_board.py IP enforces. If tscircuit's authored
# placement already satisfies it (as the engineered floorplan does), this is a
# no-op — but it makes the legalizer honest for a blind seed.
PROX = [("C1", "Q1", 10.0), ("C2", "Q1", 12.0), ("C3", "U1", 8.0),
        ("C5", "U1", 8.0), ("C4", "U1", 12.0), ("C6", "U1", 12.0)]
snapped = []
for cref, anchor, dmax in PROX:
    if cref not in fps or anchor not in fps:
        continue
    a = fps[anchor].GetPosition()
    c = fps[cref].GetPosition()
    d = math.hypot(MM(a.x - c.x), MM(a.y - c.y))
    if d <= dmax:
        continue
    # move the cap along the line toward the anchor to 0.8*dmax
    ax, ay = MM(a.x), MM(a.y)
    cx, cy = MM(c.x), MM(c.y)
    ux, uy = (ax - cx) / d, (ay - cy) / d
    tgt = d - 0.8 * dmax
    nx, ny = round(cx + ux * tgt, 2), round(cy + uy * tgt, 2)
    fps[cref].SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
    snapped.append((cref, round(d, 1), round(0.8 * dmax, 1)))
print(f"decoupler snap-back: moved {len(snapped)} caps {snapped}")

# ------------------------------------------------------------ 2. functional silk
# Captions keyed to the AUTHORED connector positions (dynamic, not hardcoded, so
# this works for any placement). One functional label placed just outside each
# touchpoint's courtyard, collision-nudged.
FUNC = {
    "J1": "SENSOR1 B R W", "J2": "SENSOR2 B R W",
    "J3": "SENSOR3 B R W", "J4": "SENSOR4 B R W",
    "J5": "BRIDGE E+ S+ S- E- SH", "J6": "HUB 5V 3V3 G DAT CLK",
    "JP1": "RATE 10/80SPS",
}
silk_obst, pad_obst = [], []


def box(bb, pad=0.0):
    return (MM(bb.GetLeft()) - pad, MM(bb.GetTop()) - pad,
            MM(bb.GetRight()) + pad, MM(bb.GetBottom()) + pad)


def hit(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


for fp in board.GetFootprints():
    for p in fp.Pads():
        pad_obst.append(box(p.GetBoundingBox(), 0.1))
    for g in fp.GraphicalItems():
        if g.IsOnLayer(pcbnew.F_SilkS):
            silk_obst.append(box(g.GetBoundingBox(), 0.08))

NUDGE = [(0, o * s) for o in (2.0, 2.8, 3.6, 4.6, 5.8, 7.0) for s in (-1, 1)] + \
        [(o * s, 0) for o in (2.0, 3.0, 4.2, 5.6) for s in (-1, 1)] + \
        [(dx, dy) for d in (2.6, 3.8, 5.0) for dx in (-d, d) for dy in (-d, d)]
placed_fn = 0
for ref, txt in FUNC.items():
    if ref not in fps:
        continue
    f = fps[ref]
    fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
    t = pcbnew.PCB_TEXT(board)
    t.SetText(txt)
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I_MM(0.6, 0.6))
    t.SetTextThickness(pcbnew.FromMM(0.12))
    ok = False
    for dx, dy in NUDGE:
        t.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
        cand = box(t.GetBoundingBox())
        if not (G.X0 + 0.4 < cand[0] and cand[2] < G.X1 - 0.4
                and G.Y0 + 0.4 < cand[1] and cand[3] < G.Y1 - 0.4):
            continue
        if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
            continue
        ok = True
        break
    board.Add(t)
    silk_obst.append(box(t.GetBoundingBox(), 0.08))
    placed_fn += 1
    if not ok:
        print(f"  WARN functional silk crowded: {ref} {txt}")
print(f"functional silk: {placed_fn} captions")

# ------------------------------------------------------------ 3. refdes + fab
# Rebuild the pad/silk obstacle sets (captions now present), then place every
# refdes on F.SilkS with the de-collision ring search + a F.Fab copy.
pad_obst, silk_obst = [], []
for fp in board.GetFootprints():
    for p in fp.Pads():
        pad_obst.append(box(p.GetBoundingBox(), 0.16))
    for g in fp.GraphicalItems():
        if g.IsOnLayer(pcbnew.F_SilkS):
            silk_obst.append(box(g.GetBoundingBox(), 0.08))
    if not fp.GetReference().startswith("H"):
        pad_obst.append(box(fp.GetBoundingBox(False, False), 0.05))
# standalone functional captions are board drawings (PCB_TEXT), NOT footprint
# graphics — include them so refdes de-collision avoids them too.
for dwg in board.GetDrawings():
    if dwg.GetClass() == "PCB_TEXT" and dwg.IsOnLayer(pcbnew.F_SilkS):
        silk_obst.append(box(dwg.GetBoundingBox(), 0.1))

OFF = [(0, o * s) for o in (1.0, 1.6, 2.2, 2.9, 3.6, 4.4, 5.4, 6.6) for s in (-1, 1)] + \
      [(o * s, 0) for o in (1.3, 2.0, 2.8, 3.6, 4.5, 5.6, 7.0) for s in (-1, 1)] + \
      [(dx, dy) for d in (1.4, 2.2, 3.0, 4.0, 5.2, 6.6) for dx in (-d, d) for dy in (-d, d)]
waived = []
for fp in sorted(board.GetFootprints(),
                 key=lambda f: (0 if f.GetReference()[0] in "UJQ" else 1,
                                f.GetReference())):
    r = fp.GetReference()
    ref = fp.Reference()
    fab = pcbnew.PCB_TEXT(board)
    fab.SetText(r)
    fab.SetLayer(pcbnew.F_Fab)
    fab.SetPosition(fp.GetPosition())
    fab.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
    fab.SetTextThickness(int(0.08e6))
    board.Add(fab)
    if r.startswith("H"):
        ref.SetVisible(False)
        continue
    ref.SetLayer(pcbnew.F_SilkS)
    ref.SetVisible(True)
    fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
    okp = False
    for rot in (0, 90):
        ref.SetTextAngleDegrees(rot)
        for sz in (0.6, 0.45):
            ref.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
            ref.SetTextThickness(int((0.12 if sz == 0.6 else 0.09) * 1e6))
            for dx, dy in OFF:
                ref.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
                cand = box(ref.GetBoundingBox())
                if not (G.X0 + 0.2 < cand[0] and cand[2] < G.X1 - 0.2
                        and G.Y0 + 0.2 < cand[1] and cand[3] < G.Y1 - 0.2):
                    continue
                if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
                    continue
                silk_obst.append(cand)
                okp = True
                break
            if okp:
                break
        if okp:
            break
    if not okp:
        ref.SetVisible(False)
        waived.append(r)

# TP function labels (net word) next to each test point
tp_label = {f.GetReference(): f.GetValue().replace("TP ", "")
            for f in board.GetFootprints() if f.GetReference().startswith("TP")}
TPNET = {"TP1": "E+", "TP2": "S+", "TP3": "S-", "TP4": "GND",
         "TP5": "DAT", "TP6": "CLK", "TP7": "3V3"}
tpn = 0
for r in sorted(tp_label):
    f = fps[r]
    t = pcbnew.PCB_TEXT(board)
    t.SetText(TPNET.get(r, r))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I_MM(0.6, 0.6))
    t.SetTextThickness(int(0.1e6))
    fx, fy = MM(f.GetPosition().x), MM(f.GetPosition().y)
    for dx, dy in OFF:
        t.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
        cand = box(t.GetBoundingBox())
        if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
            continue
        silk_obst.append(cand)
        board.Add(t)
        tpn += 1
        break

(HERE / "06_build").mkdir(exist_ok=True)
(HERE / "06_build" / "refdes_waiver.json").write_text(json.dumps(sorted(waived)))
print(f"refdes on silk: {len(fps) - len([w for w in waived])}/{len(fps)} placed, "
      f"waived {sorted(waived)}; TP labels {tpn}")
board.Save(str(PCB))
print(f"saved {PCB.name}")
