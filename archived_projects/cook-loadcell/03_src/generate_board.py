#!/usr/bin/env python3
"""Generate 04_kicad/cook_loadcell.kicad_pcb. 55x45 2-layer: sensors J1/J2
+ J5 north, J3/J4 + J6 south, HX711 center-west (analog corner W, digital
SE). Missing footprint = HARD ERROR; refdes de-collision on F.SilkS +
functional silk (P5). Run: /usr/bin/python3 03_src/generate_board.py"""
import json
import math
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import geom as G  # noqa: E402

K = HERE.parent / "04_kicad"
NETLIST = HERE.parent / "06_build" / "netlists" / "cook_loadcell.net"
PCB = K / "cook_loadcell.kicad_pcb"
STD = "/usr/share/kicad/footprints"
MM = pcbnew.ToMM


def parse_netlist(path):
    s = path.read_text()
    comps = {}
    for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)', s, re.S):
        ref, body = m.group(1), m.group(2)
        fp = re.search(r'\(footprint\s+"([^"]*)"\)', body)
        val = re.search(r'\(value\s+"([^"]*)"\)', body)
        comps[ref] = (fp.group(1) if fp else "", val.group(1) if val else "")
    if not comps:
        raise RuntimeError("parsed 0 components")
    pad_net, nets = {}, set()
    for m in re.finditer(r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|\Z)', s, re.S):
        name, body = m.group(1), m.group(2)
        nets.add(name)
        for r, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body):
            pad_net[(r, p)] = name
    return comps, pad_net, nets


ANCHOR = {
    # XH footprints are pad-1-origin; pads run +x at rot 0.
    # Respaced 2026-07-19 (twice): the original 9mm pitch overlapped B3B-XH
    # bodies pairwise AND put J1/J3 pad 1 straight onto the corner mounting
    # holes. Measured B3B-XH COURTYARD is 10.99mm wide (26.5-37.49 at x29.5),
    # so the pitch must be >= 11.1: J1/J3 at 30.2 (0.21mm to the H1/H3
    # courtyard), J2/J4 at 41.3 (0.2mm to J5/J6). Zero courtyard waivers.
    "J1": (30.2, 24.2, 0), "J2": (41.3, 24.2, 0), "J5": (52.5, 24.2, 0),
    "J3": (30.2, 60.8, 0), "J4": (41.3, 60.8, 0), "J6": (53.5, 60.8, 0),
    "U1": (38.0, 42.0, 0),
    "Q1": (28.5, 36.0, 0),
    "JP1": (63.0, 42.0, 270),
}
SEED = {
    # R2 moved 2026-07-19: its GND pad kept landing over the S_PLUS B.Cu
    # run (via rescue + top-pour spoke both blocked)
    "R1": (28.5, 39.5), "R2": (26.6, 42.6),
    "C1": (28.5, 44.5), "C2": (28.5, 47),
    "R7": (63, 27.5), "C7": (63, 30), "SJ1": (63, 32.5),
    "C3": (44, 38), "C4": (47, 38), "C5": (44, 46), "C6": (47, 46),
    "D1": (55, 55), "D2": (58, 55),
    "TP1": (24, 32), "TP2": (24, 40), "TP3": (24, 48), "TP4": (24, 55),
    "TP5": (52, 51), "TP6": (56, 51), "TP7": (60, 51),
}

SILK = [
    ("LOAD SENSOR 1  B R W", 30.5, 29.2, 0.7),
    ("SENSOR 2  B R W", 38.8, 31.0, 0.7),
    ("FULL BRIDGE ALT: E+ S+ S- E- SH", 52.0, 29.4, 0.65),
    ("SENSOR 3  B R W", 30.5, 57.2, 0.7), ("SENSOR 4  B R W", 39.5, 55.4, 0.7),
    ("TO COOK-HUB J6: 5V 3V3 G DAT CLK", 54.0, 57.2, 0.65),
    ("JP1 RATE: 1-2=10SPS 2-3=80SPS", 62.0, 37.8, 0.6),
    ("SJ1: SHIELD HARD BOND", 63.0, 34.6, 0.55),
    # title block lives in the SE clearing (JP1 y<=44.5, TP row y=51) — the
    # old centre-board home sat on U1's pads
    ("cook-loadcell v1.0  HX711 PCB C", 57.0, 47.0, 0.7),
    ("MODE = POPULATION: 4x HALF-BRIDGE OR J5", 57.0, 48.7, 0.6),
]


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    def edge(xa, ya, xb, yb):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)

    edge(G.X0, G.Y0, G.X1, G.Y0)
    edge(G.X1, G.Y0, G.X1, G.Y1)
    edge(G.X1, G.Y1, G.X0, G.Y1)
    edge(G.X0, G.Y1, G.X0, G.Y0)

    for i, (hx, hy) in enumerate(G.HOLES, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty", "MountingHole_3.2mm_M3")
        mh.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        mh.SetReference(f"H{i}")
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        mh.SetPosition(pcbnew.VECTOR2I_MM(hx, hy))
        board.Add(mh)

    placed = 0
    for ref, (fpid, val) in sorted(comps.items()):
        if not fpid:
            raise RuntimeError(f"{ref} has no footprint")
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(f"{STD}/{lib}.pretty", name)
        if fp is None:
            raise RuntimeError(f"footprint not found: {fpid}")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(val)
        if ref in ANCHOR:
            x, y, rot = ANCHOR[ref]
        else:
            x, y = SEED[ref]
            rot = 0
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        # SJ symbol is in_bom yes but the KiCad SolderJumper footprint ships
        # exclude_from_bom -> footprint_symbol_mismatch parity. Clear it.
        if ref.startswith("SJ"):
            fp.SetAttributes(fp.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        board.Add(fp)
        placed += 1

    board_pads = {(f.GetReference(), p.GetNumber())
                  for f in board.GetFootprints() for p in f.Pads()}
    missing = [k for k in pad_net if k not in board_pads]
    if missing:
        raise RuntimeError(f"netlist pads missing: {missing}")

    fps = {f.GetReference(): f for f in board.GetFootprints()}

    def padnet(ref, num):
        return next(p for p in fps[ref].Pads() if p.GetNumber() == num).GetNetname()

    # polarity + role asserts
    for ref, want in [("D1", "DAT"), ("D2", "CLK")]:
        if padnet(ref, "1") != want:
            raise RuntimeError(f"{ref} pad1 (cathode) on {padnet(ref, '1')} != {want}")
    assert padnet("Q1", "2") == "5V" and padnet("Q1", "3") == "E_PLUS"
    assert padnet("U1", "8") == "S_PLUS" and padnet("U1", "7") == "S_MINUS"
    assert padnet("J6", "4") == "DAT" and padnet("J6", "5") == "CLK"

    # legalize floaters
    def bbox(f):
        bb = f.GetBoundingBox(False, False)
        return (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))

    def clear_at(f, x, y, skip):
        old = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        l, t, r_, bt = bbox(f)
        f.SetPosition(old)
        w2, h2 = (r_ - l) / 2, (bt - t) / 2
        if not (G.X0 + 1.0 + w2 < x < G.X1 - 1.0 - w2 and
                G.Y0 + 1.0 + h2 < y < G.Y1 - 1.0 - h2):
            return False
        for hx, hy in G.HOLES:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < 2.6:
                return False
        for r2, f2 in fps.items():
            if r2 == skip or r2.startswith("H"):
                continue
            L, T, Rr, B = bbox(f2)
            if not (x + w2 + 0.25 <= L or Rr <= x - w2 - 0.25 or
                    y + h2 + 0.25 <= T or B <= y - h2 - 0.25):
                return False
        return True

    moved = 0
    for r in sorted(fps):
        f = fps[r]
        if r in ANCHOR or r.startswith("H"):
            continue
        ox, oy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        if clear_at(f, ox, oy, r):
            continue
        done = False
        for ring in [0.5 * k for k in range(1, 40)]:
            for ang in range(0, 360, 20):
                nx = round(ox + ring * math.cos(math.radians(ang)), 1)
                ny = round(oy + ring * math.sin(math.radians(ang)), 1)
                if clear_at(f, nx, ny, r):
                    f.SetPosition(pcbnew.VECTOR2I_MM(nx, ny))
                    moved += 1
                    done = True
                    break
            if done:
                break
        if not done:
            raise RuntimeError(f"no spot for {r}")
    print(f"legalized {moved}")

    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.15)
    ds.m_MinClearance = int(0.127e6)
    ds.m_ViasMinAnnularWidth = int(0.13e6)
    ds.m_HoleClearance = int(0.25e6)
    ds.m_HoleToHoleMin = int(0.5e6)
    ds.m_CopperEdgeClearance = int(0.3e6)
    ds.m_ViasMinSize = pcbnew.FromMM(0.45)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.2)
    ds.m_MinConn = 0
    ds.m_SolderMaskMinWidth = 0
    ds.m_SolderMaskExpansion = 0

    # GND pours both sides
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(netmap["GND"])
        z.SetAssignedPriority(0)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetMinThickness(pcbnew.FromMM(0.3))
        z.SetLocalClearance(pcbnew.FromMM(0.3))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.Outline().NewOutline()
        for x, y in [(G.X0, G.Y0), (G.X1, G.Y0), (G.X1, G.Y1), (G.X0, G.Y1)]:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)

    silk_obst, pad_obst = [], []

    def box(bb, pad=0.0):
        return (MM(bb.GetLeft()) - pad, MM(bb.GetTop()) - pad,
                MM(bb.GetRight()) + pad, MM(bb.GetBottom()) + pad)

    def hit(a, b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

    # collect pad + footprint-silk obstacles FIRST so fixed captions can be
    # collision-checked and nudged (they used to land straight on U1/JP1 pads)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pad_obst.append(box(p.GetBoundingBox(), 0.08))
        for g in fp.GraphicalItems():
            if g.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(g.GetBoundingBox(), 0.08))

    SILK_NUDGE = [(0, 0)] + \
        [(o * s_, 0) for o in (0.8, 1.5, 2.3, 3.2, 4.2) for s_ in (-1, 1)] + \
        [(0, o * s_) for o in (0.8, 1.5, 2.3, 3.2, 4.2) for s_ in (-1, 1)] + \
        [(dx, dy) for d in (1.5, 2.6, 3.8) for dx in (-d, d) for dy in (-d, d)]
    for entry in SILK:
        txt, x, y, size = entry[:4]
        size = max(size, 0.6)          # min_text_height floor
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(max(0.13, size * 0.16)))
        placed_ok = False
        for dx, dy in SILK_NUDGE:
            t.SetPosition(pcbnew.VECTOR2I_MM(x + dx, y + dy))
            cand = box(t.GetBoundingBox())
            if not (G.X0 + 0.4 < cand[0] and cand[2] < G.X1 - 0.4
                    and G.Y0 + 0.4 < cand[1] and cand[3] < G.Y1 - 0.4):
                continue
            if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
                continue
            placed_ok = True
            break
        board.Add(t)                    # keep even if crowded (best offset)
        if not placed_ok:
            print(f"WARN silk caption crowded: {txt[:30]}")
        silk_obst.append(box(t.GetBoundingBox(), 0.08))

    for fp in board.GetFootprints():
        for p in fp.Pads():
            pad_obst.append(box(p.GetBoundingBox(), 0.16))
        for g in fp.GraphicalItems():
            if g.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(g.GetBoundingBox(), 0.08))
        if not fp.GetReference().startswith("H"):
            pad_obst.append(box(fp.GetBoundingBox(False, False), 0.05))

    OFF = [(0, o * s) for o in (1.0, 1.6, 2.2, 2.9, 3.6, 4.4, 5.4, 6.6) for s in (-1, 1)] + \
          [(o * s, 0) for o in (1.3, 2.0, 2.8, 3.6, 4.5, 5.6, 7.0) for s in (-1, 1)] + \
          [(dx, dy) for d in (1.4, 2.2, 3.0, 4.0, 5.2, 6.6) for dx in (-d, d) for dy in (-d, d)]
    waived = []
    tp_label = {f.GetReference(): f.GetValue().replace("TP ", "")
                for f in board.GetFootprints() if f.GetReference().startswith("TP")}
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
        for rot in (0, 90):     # 90deg fallback: stand up in narrow gaps
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
    # TP labels
    tpn = 0
    for r, lbl in sorted(tp_label.items()):
        f = fps[r]
        t = pcbnew.PCB_TEXT(board)
        t.SetText(lbl)
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
    (HERE.parent / "06_build").mkdir(exist_ok=True)
    (HERE.parent / "06_build" / "refdes_waiver.json").write_text(json.dumps(sorted(waived)))
    print(f"refdes: {placed - len(waived)}/{placed}, waived {sorted(waived)}; TP labels {tpn}")
    board.Save(str(PCB))
    print(f"saved {PCB.name}: {placed} parts")


if __name__ == "__main__":
    main()
