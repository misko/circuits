#!/usr/bin/env python3
"""Generate 04_kicad/ble_bus_bar.kicad_pcb from the netlist + floorplan.

164x64mm 2-layer 2oz (ADR-0002). Six 19mm port slices east (stud N, shunt,
fuse, trunk band S), electronics west, ESP32-C3 antenna at the west edge
with an all-layer keepout. Power = pours only (priority over GND, solid
connection); sense/corridor tracks are drawn by route_channels.py; west
zone routed by KRT. Missing footprint = HARD ERROR. Refdes de-collision
prints every reference on F.SilkS (canon 3b) + functional silk (P5).

Run with KiCad-bundled python: /usr/bin/python3 03_src/generate_board.py
"""
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
NETLIST = HERE.parent / "06_build" / "netlists" / "ble_bus_bar.net"
PCB = K / "ble_bus_bar.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "bbar.pretty")


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
    root = PROJ if lib == "bbar" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
ANCHOR = {}
for i in range(1, 7):
    cx = G.CX[i - 1]
    ANCHOR[f"J{i}"] = (cx, G.STUD_Y, 0)
    ANCHOR[f"RS{i}"] = (cx + G.SHUNT_X, G.SHUNT_Y, 0)
    ANCHOR[f"F{i}"] = (cx, G.FUSE_Y, 0)
    ANCHOR[f"RP{i}"] = (cx + G.RP_X, G.RP_Y, 90)   # pad1 south = VF tap
    ANCHOR[f"RN{i}"] = (cx + G.RN_X, G.RN_Y, 90)   # pad1 south = VP tap
    ANCHOR[f"CD{i}"] = (cx + G.CD_X, G.CD_Y, 0)    # pads bridge KA/KB verticals
    ANCHOR[f"U{i}"] = (cx + G.INA_X, G.INA_Y, 180)
    ANCHOR[f"CB{i}"] = (cx + G.CB_X, G.CB_Y, 90)  # pad1 SOUTH on the 3V3 rail

ANCHOR.update({
    "J7": (*G.STUD_IN, 0), "J8": (*G.STUD_GND, 0),
    "U7": (*G.MODULE_XY, 90),          # antenna west
    "J9": (54.0, 84.0, 270),           # USB-C mouth west
    "U10": (61.5, 77.1, 0),            # USBLC6
    "U9": (66.0, 90.0, 0),             # AMS1117
    "C11": (60.5, 93.5, 0), "C12": (73.1, 93.5, 0), "C13": (60.5, 90.0, 0),
    "R22": (63.0, 80.6, 0), "R23": (63.0, 83.2, 0),
    "D8": (74.0, 90.0, 0),
    "U8": (86.0, 79.0, 0),             # buck
    "D11": (80.0, 79.0, 0), "L1": (86.5, 73.0, 0),
    "C4": (91.2, 76.2, 90), "C5": (81.5, 73.0, 90), "C6": (78.5, 73.0, 90),
    "C1": (91.0, 82.0, 90), "C2": (91.0, 86.0, 90), "C3": (86.5, 83.5, 0),
    "D10": (81.5, 86.5, 0),
    "R24": (74.5, 79.0, 90), "R25": (74.5, 82.5, 90),
    "R26": (77.5, 86.5, 90), "R27": (74.5, 86.5, 90),
    "F7": (68.0, 103.0, 90), "D7": (68.0, 97.6, 0), "D9": (76.0, 101.0, 90),
    "U11": (79.0, 59.0, 0),            # W25Q64
    "C9": (79.0, 63.0, 0),
    "R18": (86.0, 53.0, 0), "R19": (86.0, 55.5, 0), "R20": (86.0, 58.0, 0),
    "R21": (75.8, 72.8, 0), "C10": (79.9, 72.8, 0),
    "SW1": (69.5, 73.6, 0), "SW2": (69.5, 81.2, 0),
    "C7": (77.6, 66.0, 0), "C8": (63.2, 73.4, 0),
    "LED1": (93.0, 52.3, 0), "LED2": (93.0, 55.1, 0),
    "R28": (93.0, 57.7, 0), "R29": (93.0, 60.2, 0),
    "J10": (96.5, 53.0, 0),
    # corridor boundary parts (pad1 south on lane terminals)
    "R15": (G.BOUND_X["SDA"], G.BOUND_Y, 90),
    "R16": (G.BOUND_X["SCL"], G.BOUND_Y, 90),
    "R17": (G.BOUND_X["ALERT"], G.BOUND_Y, 90),
    "C14": (G.BOUND_X["3V3"], G.BOUND_Y, 90),
})

# refs with exact engineered positions — the legalizer must not move them
KEEP = ({f"{p}{i}" for i in range(1, 7) for p in
         ("J", "RS", "F", "RP", "RN", "CD", "U", "CB")} |
        {"J7", "J8", "J9", "U7", "U8", "U9", "U10", "U11", "F7", "D7", "D9", "R22", "R23", "R21", "C10", "C7",
         "R15", "R16", "R17", "C14", "L1", "D11", "J10", "SW1", "SW2", "C4", "C8", "C12",
         "R18", "R19", "R20", "LED1", "LED2", "R28", "R29"})

# plain-words silkscreen (P-SILK-FN). (text, x, y, size[, rot])
SILK = [
    ("+12-24V IN", 133.0, 104.0, 1.2), ("M5 LUG", 135.5, 106.5, 0.8),
    ("+", 160.5, 105.8, 3.0), ("+", 141.5, 105.8, 3.0),
    ("GND REF", 58.0, 99.2, 1.0), ("NOT LOAD RETURN", 58.0, 100.7, 0.6),
    ("CHECK POLARITY BEFORE FIRST POWER", 110.0, 112.7, 0.9),
    ("FUSES: ATO/ATC BLADE 30A MAX", 176.0, 112.7, 0.9),
    ("ble-bus-bar v1.0  BLE 12-24V 6x30A", 150.0, 50.7, 0.8),
    ("USB-C", 54.5, 76.6, 0.7), ("5V IN", 54.5, 90.7, 0.6),
    ("RESET", 69.5, 77.4, 0.7), ("BOOT", 69.5, 84.9, 0.7),
    ("PWR", 90.0, 52.3, 0.55), ("ST", 89.8, 55.1, 0.55),
    ("UART", 96.5, 51.05, 0.55),   # pin map: 05_firmware/pinmap.md (1=3V3 2=GND 3=TX 4=RX)
]
for i in range(1, 7):
    cx = G.CX[i - 1]
    SILK.append((f"PORT {i}", cx - 8.35, 57.0, 1.0, 90))
    SILK.append((f"30A MAX", cx - 5.6, 89.0, 0.8, 90))


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)

    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    def seg(xa, ya, xb, yb):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.15))
        board.Add(s)

    seg(G.X0, G.Y0, G.X1, G.Y0)
    seg(G.X1, G.Y0, G.X1, G.Y1)
    seg(G.X1, G.Y1, G.X0, G.Y1)
    seg(G.X0, G.Y1, G.X0, G.Y0)

    # NPTH mounting holes (nylon standoffs — insulated, ADR-0002 corners)
    for i, (hx, hy) in enumerate(G.HOLES, 1):
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
        if ref not in ANCHOR:
            raise RuntimeError(f"{ref} has no floorplan anchor")
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(val)
        x, y, rot = ANCHOR[ref]
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        if ref in ("J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8"):
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
        raise RuntimeError(f"netlist pads missing on board: {missing}")

    # ---- orientation + polarity asserts (part.yaml facts; audit re-checks) ----
    MM = pcbnew.ToMM

    def padpos(ref, num):
        f = board.FindFootprintByReference(ref)
        p = next(p for p in f.Pads() if p.GetNumber() == num)
        return MM(p.GetPosition().x), MM(p.GetPosition().y)

    def padnet(ref, num):
        f = board.FindFootprintByReference(ref)
        return next(p for p in f.Pads() if p.GetNumber() == num).GetNetname()

    # polarized pad-1 nets (KiCad D_*/LED pad1 = cathode; part.yaml)
    for ref, want in [("D7", "VIN_E"), ("D8", "3V3"), ("D9", "VBUS"),
                      ("D10", "VIN_E"), ("D11", "SW"),
                      ("LED1", "GND"), ("LED2", "GND")]:
        got = padnet(ref, "1")
        if got != want:
            raise RuntimeError(f"{ref} pad1 (cathode) net {got} != {want}")
    # D9 cathode pad must sit in the VBUS strip (y>=103), anode in GND pour
    x1, y1 = padpos("D9", "1")
    x2, y2 = padpos("D9", "2")
    if not (y1 >= 103.2 and y2 <= 102.5):
        raise RuntimeError(f"D9 pads misplaced: cathode y {y1}, anode y {y2}")
    xf, yf = padpos("F7", "1")
    if not yf >= 103.2:
        raise RuntimeError(f"F7 pad1 (VBUS) must be in the strip, y={yf}")
    for i in range(1, 7):
        cx = G.CX[i - 1]
        # shunt: pad1 = VF (south), pad2 = VP (north)
        assert padnet(f"RS{i}", "1") == f"VF{i}" and padnet(f"RS{i}", "2") == f"VP{i}"
        _, yp1 = padpos(f"RS{i}", "1")
        _, yp2 = padpos(f"RS{i}", "2")
        if not yp1 > yp2:
            raise RuntimeError(f"RS{i} rotated: pad1 (VF) must be south")
        # fuse: pad1 pair (VBUS) south in the trunk band
        _, yf1 = padpos(f"F{i}", "1")
        _, yf2 = padpos(f"F{i}", "2")
        if not (yf1 > 93.5 and yf2 < 93.5):
            raise RuntimeError(f"F{i} rotated: pad1 (VBUS) must be in the band")
        for rr, nn in ((f"RP{i}", f"VF{i}"), (f"RN{i}", f"VP{i}")):
            r1, r2 = padpos(rr, "1"), padpos(rr, "2")
            assert padnet(rr, "1") == nn and r1[1] > r2[1], f"{rr} pad1 ({nn}) must be south"
        # INA orientation: pad10 (IN+) west col south; pad6 (VS) west col north
        p10 = padpos(f"U{i}", "10")
        p6 = padpos(f"U{i}", "6")
        if not (abs(p10[0] - (cx + 3.9)) < 0.05 and abs(p10[1] - 64.5) < 0.05
                and abs(p6[1] - 62.5) < 0.05):
            raise RuntimeError(f"U{i} orientation wrong: pad10 at {p10}, pad6 at {p6}")
        # CD: pad1 = KP (south); CB: pad1 = 3V3 (north)
        assert padnet(f"CD{i}", "1") == f"KA{i}"
        cd1, cd2 = padpos(f"CD{i}", "1"), padpos(f"CD{i}", "2")
        if not cd1[0] < cd2[0]:
            raise RuntimeError(f"CD{i} rotated: pad1 (KA) must be west, on the KA column")
        cb1, cb2 = padpos(f"CB{i}", "1"), padpos(f"CB{i}", "2")
        if not cb1[1] > cb2[1]:
            raise RuntimeError(f"CB{i} rotated: pad1 (3V3) must be south, on the rail")
    # module: antenna west — pin1 at (mx-6, my+8.75)
    p1 = padpos("U7", "1")
    mx, my = G.MODULE_XY
    if not (abs(p1[0] - (mx - 6)) < 0.05 and abs(p1[1] - (my + 8.75)) < 0.05):
        raise RuntimeError(f"U7 rotation wrong: pin1 at {p1}")
    # USB mouth west: bbox reaches the west board edge
    j9 = board.FindFootprintByReference("J9")
    if MM(j9.GetBoundingBox(False, False).GetLeft()) > G.X0 + 0.6:
        raise RuntimeError("J9 mouth does not reach the west edge")
    # boundary parts: pad1 exactly on its lane terminal
    for ref, lane in [("R15", "SDA"), ("R16", "SCL"), ("R17", "ALERT"), ("C14", "3V3")]:
        px, py = padpos(ref, "1")
        if not (abs(px - G.BOUND_X[lane]) < 0.05 and abs(py - G.BOUND_PAD1_Y) < 0.05):
            raise RuntimeError(f"{ref} pad1 not on lane terminal: ({px},{py})")

    # ---------------------------------------------------- legalize floaters
    def bbox(f):
        bb = f.GetBoundingBox(False, False)
        return (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    holes = [(MM(f.GetPosition().x), MM(f.GetPosition().y))
             for r, f in fps.items() if r.startswith("H")]

    def clear_at(f, x, y, skip):
        old = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        l, t, r_, bt = bbox(f)
        f.SetPosition(old)
        w2, h2 = (r_ - l) / 2, (bt - t) / 2
        # floaters stay in the west electronics zone, clear of keepouts
        if not (G.X0 + 1.0 + w2 < x < 96.0 - w2 and G.Y0 + 1.0 + h2 < y < 102.0 - h2):
            return False
        ax0, ax1, ay0, ay1 = G.ANT_KEEPOUT
        if not (x - w2 > ax1 + 0.3 or y - h2 > ay1 + 0.3 or y + h2 < ay0 - 0.3):
            return False
        if 86.0 - w2 < x and 64.6 - 0.4 - h2 < y < 69.2 + 0.4 + h2:
            return False   # corridor strip
        for hx, hy in holes:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < 2.4:
                return False
        for r2, f2 in fps.items():
            if r2 == skip or r2.startswith("H"):
                continue
            L, T, Rr, B = bbox(f2)
            if not (x + w2 + 0.3 <= L or Rr <= x - w2 - 0.3 or
                    y + h2 + 0.3 <= T or B <= y - h2 - 0.3):
                return False
        return True

    moved = 0
    for r in sorted(fps):
        f = fps[r]
        if r in KEEP or r.startswith("H"):
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
            raise RuntimeError(f"legalizer: no clear spot for {r} within 20mm")
    print(f"legalized {moved} small parts")

    # design rules floor (JLC 2-layer 2oz: 0.16/0.16, pad-pad 0.15)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.16)
    ds.m_MinClearance = int(0.15e6)
    ds.m_ViasMinAnnularWidth = int(0.05e6)
    ds.m_HoleClearance = int(0.2e6)   # JLC NPTH-to-copper floor
    ds.m_HoleToHoleMin = int(0.25e6)   # same-net JLC floor 0.254; diff-net covered by clearance
    ds.m_CopperEdgeClearance = int(0.2e6)
    ds.m_ViasMinSize = pcbnew.FromMM(0.3)       # USB-weave dive vias (JLC: dia >= hole+0.1)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.2)
    ds.m_MinConn = pcbnew.FromMM(0.1)
    ds.m_SolderMaskMinWidth = 0
    ds.m_SolderMaskExpansion = 0

    # ------------------------------------------------------------- zones
    def add_zone(net, layer, pts, prio, minw=0.3, clr=0.3, full=True):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(netmap[net])
        z.SetAssignedPriority(prio)
        if net == "GND":
            # ALWAYS remove padless islands (inter-lane B.Cu slivers are
            # unrescuable: 0.5mm gaps cannot take a via). Pad-serving
            # pockets are not "islands" to the filler; stitch_and_fill
            # gives them rescue vias-in-pad.
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        z.SetMinThickness(pcbnew.FromMM(minw))
        z.SetLocalClearance(pcbnew.FromMM(clr))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full
                           else pcbnew.ZONE_CONNECTION_THERMAL)
        z.Outline().NewOutline()
        for x, y in pts:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)
        return z

    FULL = [(G.X0, G.Y0), (G.X1, G.Y0), (G.X1, G.Y1), (G.X0, G.Y1)]
    add_zone("GND", pcbnew.B_Cu, FULL, 0, full=False)      # THE return plane
    add_zone("GND", pcbnew.F_Cu, G.GND_F, 0, full=True)    # electronics zone
    add_zone("VBUS", pcbnew.F_Cu, G.TRUNK_F, 1, minw=0.5)  # 60A trunk (solid)
    add_zone("VBUS", pcbnew.B_Cu, G.TRUNK_B, 1, minw=0.5)  # paired reinforcement
    for i in range(1, 7):
        cx = G.CX[i - 1]
        for net, (rx0, rx1, ry0, ry1) in [(f"VP{i}", G.VP_POUR), (f"VF{i}", G.VF_POUR)]:
            add_zone(net, pcbnew.F_Cu,
                     [(cx + rx0, ry0), (cx + rx1, ry0), (cx + rx1, ry1), (cx + rx0, ry1)],
                     2, minw=0.5)

    # ------------------------------------------------- rule areas
    def rule_area(pts, layers, name, no_copper):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        z.SetDoNotAllowZoneFills(no_copper)
        z.SetDoNotAllowTracks(no_copper)
        z.SetDoNotAllowVias(no_copper)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        for l in layers:
            ls.addLayer(l)
        z.SetLayerSet(ls)
        z.Outline().NewOutline()
        for x, y in pts:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)
        return z

    ax0, ax1, ay0, ay1 = G.ANT_KEEPOUT
    rule_area([(ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1)],
              [pcbnew.F_Cu, pcbnew.B_Cu], "ANTENNA", True)
    for i in range(1, 7):
        cx = G.CX[i - 1]
        kx0, kx1, ky0, ky1 = G.KELVIN_AREA
        rule_area([(cx + kx0, ky0), (cx + kx1, ky0), (cx + kx1, ky1), (cx + kx0, ky1)],
                  [pcbnew.F_Cu], "KELVIN", False)

    # ------------------------------------------------------------- silk text
    for entry in SILK:
        txt, x, y, size = entry[:4]
        rot = entry[4] if len(entry) > 4 else 0
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(max(0.15, size * 0.16)))
        if rot:
            t.SetTextAngleDegrees(rot)
        board.Add(t)

    # refdes on silk, de-collided (golden rule 3b / audit I8)
    TH, THK, CLR = 0.6, 0.12, 0.16

    def box(bb, pad=0.0):
        return (MM(bb.GetLeft()) - pad, MM(bb.GetTop()) - pad,
                MM(bb.GetRight()) + pad, MM(bb.GetBottom()) + pad)

    def hit(a, b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])
    pad_obst, silk_obst = [], []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pad_obst.append(box(p.GetBoundingBox(), CLR))
        for g in fp.GraphicalItems():
            if g.IsOnLayer(pcbnew.F_SilkS):
                silk_obst.append(box(g.GetBoundingBox(), CLR * 0.5))
        if not fp.GetReference().startswith("H"):
            pad_obst.append(box(fp.GetBoundingBox(False, False), 0.05))
    for t in board.GetDrawings():
        if t.GetClass() == "PCB_TEXT" and t.IsOnLayer(pcbnew.F_SilkS):
            silk_obst.append(box(t.GetBoundingBox(), CLR * 0.5))

    OFF = [(0, o * s) for o in (1.0, 1.6, 2.2, 2.9, 3.6, 4.4, 5.2, 6.0) for s in (-1, 1)] + \
          [(o * s, 0) for o in (1.3, 2.0, 2.8, 3.6, 4.5, 5.4, 6.2) for s in (-1, 1)] + \
          [(dx, dy) for d in (1.4, 2.2, 3.0, 4.0, 5.0, 6.0) for dx in (-d, d) for dy in (-d, d)]
    waived = []

    def prio(fp):
        r = fp.GetReference()
        return (0 if r[0] in "UJDFL" or r.startswith("RS") or r.startswith("SW") else 1, r)
    for fp in sorted(board.GetFootprints(), key=prio):
        r = fp.GetReference()
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I_MM(TH, TH))
        ref.SetTextThickness(int(THK * 1e6))
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
        placed_ok = False
        for dx, dy in OFF:
            ref.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
            cand = box(ref.GetBoundingBox())
            if not (G.X0 + 0.2 < cand[0] and cand[2] < G.X1 - 0.2
                    and G.Y0 + 0.2 < cand[1] and cand[3] < G.Y1 - 0.2):
                continue
            if any(hit(cand, o) for o in pad_obst):
                continue
            if any(hit(cand, o) for o in silk_obst):
                continue
            silk_obst.append(cand)
            placed_ok = True
            break
        if not placed_ok:
            ref.SetVisible(False)
            waived.append(r)
    (HERE.parent / "06_build").mkdir(exist_ok=True)
    (HERE.parent / "06_build" / "refdes_waiver.json").write_text(json.dumps(sorted(waived)))
    print(f"refdes on silk: {placed - len(waived)}/{placed} placed, "
          f"{len(waived)} waived to Fab: {sorted(waived)}")
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(G.HOLES)} holes; zones; rule areas; saved {PCB.name}")


if __name__ == "__main__":
    main()
