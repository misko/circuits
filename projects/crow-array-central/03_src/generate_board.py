#!/usr/bin/env python3
"""Generate 04_kicad/crow_array_central.kicad_pcb from the netlist + floorplan.

4-layer board (ADR-0001): F.Cu signal / In1 solid GND / In2 power islands /
B.Cu signal+GND. ~175x105mm. Floorplan (ARCHITECTURE.md "Layout zones"):
  north edge   : 8 RJ45 ports J1..J8 + their beeper current path (feeds,
                 FETs, returns) — beeper copper never enters the analog band.
  analog band  : both PCM1865 + coupling networks + XC6227 (center).
  digital south: XU316, flash, crystal, buffer; USB-C at the south edge.
  power SW     : entry, protection, both bucks, both LDOs (>=25mm from ADCs).

Big anchors are placed explicitly; passives are seeded near their functional
group centroid and then legalized (ring-search) so nothing overlaps. Missing
footprint = HARD ERROR (contract). Refdes printed on F.SilkS, de-collided
(I10/I10b). EP thermal vias live in the footprint (make_lib). Zones: In1
solid GND, F/B/In2 GND pours (power islands cut in during routing).

Run with KiCad-bundled python: /usr/bin/python3 03_src/generate_board.py
"""
import json
import math
import re
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
K = HERE.parent / "04_kicad"
NETLIST = HERE.parent / "06_build" / "netlists" / "crow_array_central.net"
PCB = K / "crow_array_central.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "cac.pretty")

X0, Y0, W, H = 10.0, 10.0, 176.0, 104.0
X1, Y1 = X0 + W, Y0 + H
HOLES = [(X0 + 5.0, Y0 + 5.0), (X1 - 5.0, Y0 + 5.0),
         (X0 + 5.0, Y1 - 5.0), (X1 - 5.0, Y1 - 5.0)]


def parse_netlist(path):
    s = path.read_text()
    comps = {}
    for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)', s, re.S):
        ref, body = m.group(1), m.group(2)
        fp = re.search(r'\(footprint\s+"([^"]*)"\)', body)
        val = re.search(r'\(value\s+"([^"]*)"\)', body)
        comps[ref] = (fp.group(1) if fp else "", val.group(1) if val else "")
    if not comps:
        raise RuntimeError(f"parsed 0 components from {path}")
    pad_net, nets = {}, set()
    for m in re.finditer(r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|\Z)', s, re.S):
        name, body = m.group(1), m.group(2)
        nets.add(name)
        for r, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body):
            pad_net[(r, p)] = name
    if not nets:
        raise RuntimeError(f"parsed 0 nets from {path}")
    return comps, pad_net, nets


def load_fp(fpid):
    lib, name = fpid.split(":")
    root = PROJ if lib == "cac" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
# 8 RJ45 ports across the north edge (pitch 20mm), openings north.
PORT_PITCH = 20.0
PORT_X0 = X0 + 14.0
PORT_Y = Y0 + 12.0


def port_x(n):
    return PORT_X0 + (n - 1) * PORT_PITCH


ANCHOR = {
    # big digital cluster (south-center)
    "U1": (X0 + 90.0, Y0 + 74.0, 0),          # XU316 center
    "U4": (X0 + 66.0, Y0 + 88.0, 0),          # flash SW of XU316
    "Y1": (X0 + 74.0, Y0 + 92.0, 0),          # crystal near XU316
    "U5": (X0 + 108.0, Y0 + 90.0, 0),         # MCLK buffer
    "J12": (X0 + 92.0, Y0 + 100.0, 0),        # USB-C south edge
    "U6": (X0 + 120.0, Y0 + 96.0, 0),         # SHT40
    # analog band (center-north), between the port strip and the XU316
    "U2": (X0 + 64.0, Y0 + 52.0, 0),          # PCM1865 ADC1
    "U3": (X0 + 112.0, Y0 + 52.0, 0),         # PCM1865 ADC2
    "U13": (X0 + 88.0, Y0 + 44.0, 0),         # XC6227 3V3A (analog LDO)
    # power SW corner (>=25mm from ADCs)
    "J9": (X0 + 8.0, Y0 + 90.0, 0),           # barrel
    "J11": (X0 + 8.0, Y0 + 78.0, 0),          # terminal DNP
    "F1": (X0 + 20.0, Y0 + 92.0, 0),          # entry PTC
    "D9": (X0 + 26.0, Y0 + 96.0, 0),          # TVS
    "Q9": (X0 + 26.0, Y0 + 88.0, 0),          # reverse FET
    "U10": (X0 + 34.0, Y0 + 84.0, 0),         # buck 3V3
    "L10": (X0 + 40.0, Y0 + 88.0, 0),
    "U11": (X0 + 34.0, Y0 + 96.0, 0),         # buck 0V9
    "L11": (X0 + 40.0, Y0 + 100.0, 0),
    "U12": (X0 + 46.0, Y0 + 92.0, 0),         # LDO 1V8
    "J10": (X0 + 150.0, Y0 + 96.0, 0),        # injection header (SE)
    "J13": (X0 + 158.0, Y0 + 88.0, 0),        # debug headers
    "J14": (X0 + 168.0, Y0 + 88.0, 0),
}
# 8 RJ45 jacks + per-port cluster centroids
for n in range(1, 9):
    ANCHOR[f"J{n}"] = (port_x(n), PORT_Y, 0)

# functional-group centroid per passive/small-part ref (seed for legalizer)
GROUPS = {}


def grp(refs, cx, cy):
    for r in refs:
        GROUPS[r] = (cx, cy)


# power-entry passives
grp(["R90", "C90", "TP9"], X0 + 20.0, Y0 + 98.0)
grp(["R10", "R11", "C10", "C11", "C12", "R12"], X0 + 30.0, Y0 + 78.0)
grp(["R13", "R14", "C13", "C14", "C15", "R15", "TP11"], X0 + 30.0, Y0 + 100.0)
grp(["C16", "C17"], X0 + 50.0, Y0 + 96.0)
grp(["C18", "C19", "C20", "R16"], X0 + 82.0, Y0 + 40.0)
# XU316 decoupling ring
xu_dec = [f"C1{i:02d}" for i in range(1, 43)] + ["FB3"]
grp([r for r in xu_dec if r in ()], 0, 0)  # placeholder
for i, r in enumerate([f"C1{i:02d}" for i in range(1, 43)]):
    ang = i / 42.0 * 2 * math.pi
    GROUPS[r] = (X0 + 90.0 + 16.0 * math.cos(ang), Y0 + 74.0 + 14.0 * math.sin(ang))
grp(["FB3", "C123"], X0 + 90.0, Y0 + 60.0)
# crystal + flash
grp(["R20", "R21", "C25", "C26"], X0 + 78.0, Y0 + 96.0)
grp(["R30", "C30"], X0 + 60.0, Y0 + 92.0)
# USB
grp(["D10", "R31", "R32", "R33", "R34", "C31"], X0 + 92.0, Y0 + 92.0)
# clock buffer + terminations
grp(["C35", "R40", "R41", "R42", "R43"], X0 + 108.0, Y0 + 82.0)
# reset + i2c + sht
grp(["R50", "C40", "R51", "R52", "C41"], X0 + 120.0, Y0 + 88.0)
# ADC1 support
grp(["C50", "C51", "C52", "C53", "C54", "C55", "C56", "C57",
     "R60", "R61", "R62", "R63"], X0 + 64.0, Y0 + 64.0)
# ADC2 support
grp(["C60", "C61", "C62", "C63", "C64", "C65", "C66", "C67",
     "R64", "R65", "R66", "R67"], X0 + 112.0, Y0 + 64.0)
# ADC input coupling network (near the two ADCs by channel)
for n in range(1, 9):
    base = 200 + n * 10
    cx = X0 + 64.0 if n <= 4 else X0 + 112.0
    cy = Y0 + 40.0 + ((n - 1) % 4) * 2.0
    grp([f"C{base}", f"R{base}", f"C{base+1}", f"R{base+1}", f"C{base+2}"],
        cx + (n - 1) % 4 * 3 - 5, cy)
grp(["C90i", "R80", "R81"], X0 + 148.0, Y0 + 90.0)
# per-port channel small parts (below each jack)
for n in range(1, 9):
    px = port_x(n)
    grp([f"D{20+n}", f"F{10+n}", f"F{20+n}", f"R{100+n}", f"Q{n}",
         f"C{300+n}", f"R{110+n}", f"TP{20+n}"], px, PORT_Y + 14.0)


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)

    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    # rectangular outline
    def seg(xa, ya, xb, yb):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.15))
        board.Add(s)
    seg(X0, Y0, X1, Y0)
    seg(X1, Y0, X1, Y1)
    seg(X1, Y1, X0, Y1)
    seg(X0, Y1, X0, Y0)

    for i, (hx, hy) in enumerate(HOLES, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty", "MountingHole_3.2mm_M3")
        if mh is None:
            raise RuntimeError("mounting hole footprint missing")
        mh.SetReference(f"H{i}")
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        mh.SetPosition(pcbnew.VECTOR2I_MM(hx, hy))
        board.Add(mh)

    placed = 0
    for ref, (fpid, val) in sorted(comps.items()):
        if not fpid:
            raise RuntimeError(f"{ref} has no footprint in the netlist")
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(val)
        if ref in ANCHOR:
            x, y, rot = ANCHOR[ref]
        elif ref in GROUPS:
            x, y = GROUPS[ref]
            rot = 0
        else:
            raise RuntimeError(f"{ref} has no floorplan anchor or group")
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        if ref.startswith("TP"):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
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
        raise RuntimeError(f"netlist pads missing on board: {missing[:20]}")

    # ---------------------------------------------------- legalize passives
    ANCH = set(ANCHOR)

    def bbox(f):
        bb = f.GetBoundingBox(False, False)
        return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    holes = [(pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y))
             for r, f in fps.items() if r.startswith("H")]

    def clear_at(f, x, y, skip):
        old = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        l, t, r_, bt = bbox(f)
        f.SetPosition(old)
        w2, h2 = (r_ - l) / 2, (bt - t) / 2
        if not (X0 + 0.6 + w2 < x < X1 - 0.6 - w2 and Y0 + 0.6 + h2 < y < Y1 - 0.6 - h2):
            return False
        for hx, hy in holes:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < 2.2:
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
        if r in ANCH or r.startswith("H"):
            continue
        ox, oy = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
        if clear_at(f, ox, oy, r):
            continue
        done = False
        for ring in [0.5 * k for k in range(1, 60)]:
            for ang in range(0, 360, 15):
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
            raise RuntimeError(f"legalizer: no clear spot for {r} within 30mm")
    print(f"legalized {moved} small parts")

    # design-rule floors (JLC 4-layer standard)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.127)
    ds.m_MinClearance = int(0.127e6)
    ds.m_ViasMinAnnularWidth = int(0.05e6)
    ds.m_HoleClearance = int(0.25e6)
    ds.m_HoleToHoleMin = int(0.5e6)
    ds.m_CopperEdgeClearance = int(0.2e6)
    ds.m_ViasMinSize = pcbnew.FromMM(0.45)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.3)

    # ------------------------------------------------------------- zones
    def add_zone(net, layer, prio, full=False):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(netmap[net])
        z.SetAssignedPriority(prio)
        z.SetMinThickness(pcbnew.FromMM(0.25))
        z.SetLocalClearance(pcbnew.FromMM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full
                           else pcbnew.ZONE_CONNECTION_THERMAL)
        z.Outline().NewOutline()
        for x, y in [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)
        return z

    add_zone("GND", pcbnew.F_Cu, 0)
    add_zone("GND", pcbnew.In1_Cu, 0, full=True)   # THE reference plane
    add_zone("GND", pcbnew.In2_Cu, 0)              # power islands cut in at routing
    add_zone("GND", pcbnew.B_Cu, 0)

    # ------------------------------------------------------------ silk text
    SILK = [
        ("NOT ETHERNET - CUSTOM 5V/AUDIO PINOUT", X0 + 88.0, Y0 + 4.0, 1.4),
        ("crow-array-central v1.0", X0 + 88.0, Y1 - 2.5, 1.1),
    ]
    for n in range(1, 9):
        SILK.append((f"PORT {n}" + (" DNP" if n >= 7 else ""),
                     port_x(n), PORT_Y - 9.0, 0.8))
    for txt, x, y, size in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(max(0.13, size * 0.16)))
        board.Add(t)

    # refdes on silk, de-collided (golden rule 3b / audit I10/I10b)
    MM = pcbnew.ToMM

    def box(bb, pad=0.0):
        return (MM(bb.GetLeft()) - pad, MM(bb.GetTop()) - pad,
                MM(bb.GetRight()) + pad, MM(bb.GetBottom()) + pad)

    def hit(a, b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])
    pad_obst, silk_obst = [], []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pad_obst.append(box(p.GetBoundingBox(), 0.12))
        for g in fp.GraphicalItems():
            if g.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(g.GetBoundingBox(), 0.08))
        if not fp.GetReference().startswith("H"):
            pad_obst.append(box(fp.GetBoundingBox(False, False), 0.05))
    for t in board.GetDrawings():
        if t.GetClass() == "PCB_TEXT" and t.IsOnLayer(pcbnew.F_SilkS):
            silk_obst.append(box(t.GetBoundingBox(), 0.08))

    OFF = [(0, o * s) for o in (0.9, 1.5, 2.2, 3.0, 3.9) for s in (-1, 1)] + \
          [(o * s, 0) for o in (1.2, 2.0, 2.9, 3.9) for s in (-1, 1)] + \
          [(dx, dy) for d in (1.3, 2.1, 3.0) for dx in (-d, d) for dy in (-d, d)]
    waived = []

    def prio(fp):
        r = fp.GetReference()
        return (0 if r[0] in "UJDBQ" or r.startswith("TP") else 1, r)
    for fp in sorted(board.GetFootprints(), key=prio):
        r = fp.GetReference()
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I_MM(0.6, 0.6))
        ref.SetTextThickness(int(0.12 * 1e6))
        fab = pcbnew.PCB_TEXT(board)
        fab.SetText(r)
        fab.SetLayer(pcbnew.F_Fab)
        fab.SetPosition(fp.GetPosition())
        fab.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
        fab.SetTextThickness(int(0.08e6))
        board.Add(fab)
        if r.startswith("H"):
            continue
        ref.SetLayer(pcbnew.F_SilkS)
        ref.SetVisible(True)
        fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
        ok = False
        for dx, dy in OFF:
            ref.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
            cand = box(ref.GetBoundingBox())
            if not (X0 + 0.2 < cand[0] and cand[2] < X1 - 0.2
                    and Y0 + 0.2 < cand[1] and cand[3] < Y1 - 0.2):
                continue
            if any(hit(cand, o) for o in pad_obst) or any(hit(cand, o) for o in silk_obst):
                continue
            silk_obst.append(cand)
            ok = True
            break
        if not ok:
            ref.SetVisible(False)
            waived.append(r)
    (HERE.parent / "06_build").mkdir(exist_ok=True)
    (HERE.parent / "06_build" / "refdes_waiver.json").write_text(json.dumps(sorted(waived)))
    print(f"refdes on silk: {placed - len(waived)}/{placed} placed, {len(waived)} waived")
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(HOLES)} holes; 4 zones; saved {PCB.name}")


if __name__ == "__main__":
    main()
