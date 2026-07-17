#!/usr/bin/env python3
"""Generate 04_kicad/esp32_laser_timing.kicad_pcb from the netlist + floorplan.

92x62mm 2-layer. Placement: WROOM-1 north-center with the ANTENNA (top 6mm
of module, part.yaml gotcha) overhanging the north edge; USB-C west edge
(opening overhangs W); LDO + laser FET corner SW; LM339 + PD networks SE;
laser terminals (SW) + photodiode terminals (SE) on the south edge; button
terminals east edge; OLED female header NE; BOOT/RESET tactiles south of
the module. 4x M3 at 5.5mm corner insets. Zones: full GND on F+B (B = THE
return plane), 3V3 pour patch under the LDO tab. Missing footprint = HARD
ERROR (never a warning).

Run with KiCad-bundled python: /usr/bin/python3 03_src/generate_board.py
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
K = HERE.parent / "04_kicad"
NETLIST = HERE.parent / "06_build" / "netlists" / "esp32_laser_timing.net"
PCB = K / "esp32_laser_timing.kicad_pcb"
STD = "/usr/share/kicad/footprints"

X0, Y0, W, H = 50.0, 50.0, 92.0, 62.0
X1, Y1 = X0 + W, Y0 + H


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
    fp = pcbnew.FootprintLoad(f"{STD}/{lib}.pretty", name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
# ref -> (x, y, rot). Terminal rot sense (Phoenix PT, wire opening):
# 0 = S, 90 = E, 180 = N, 270 = W (asserted below via body-vs-pad centroid).
ANCHOR = {
    # MCU module: antenna overhangs north edge (top 6mm of body off-board)
    "U1": (96.0, 56.0, 0),
    # MCU support: 3V3 decouplers near pad 2 (west col top), EN RC near pad 3
    "C4": (82.0, 52.5, 90), "C5": (82.0, 56.0, 90),
    "R3": (78.0, 60.0, 0), "C1": (78.0, 63.0, 0),
    "SW2": (75.0, 76.0, 0), "SW1": (85.0, 76.0, 0),
    # USB-C west edge, opening W; ESD + CC pulldowns behind it
    "J1": (54.2, 64.0, 270),
    "D1": (63.5, 57.0, 0),
    "R1": (61.5, 70.5, 0), "R2": (61.5, 73.0, 0),
    # power LED
    "R4": (60.0, 80.0, 0), "D2": (65.5, 80.0, 0),
    # LDO + caps
    "U2": (64.0, 88.5, 0), "C2": (56.5, 88.5, 90), "C3": (71.5, 88.5, 90),
    # laser FET corner (SW): gate series north, pulldowns beside, FETs, terminals
    "R10": (62.5, 94.0, 0), "R12": (71.0, 94.0, 0), "R14": (79.5, 94.0, 0),
    "R11": (62.5, 96.5, 0), "R13": (71.0, 96.5, 0), "R15": (79.5, 96.5, 0),
    "Q1": (63.0, 100.5, 0), "Q2": (71.5, 100.5, 0), "Q3": (80.0, 100.5, 0),
    "J4": (61.5, 107.0, 0), "J5": (70.0, 107.0, 0), "J6": (78.5, 107.0, 0),
    # 5V bulk near laser terminals
    "C11": (86.5, 101.5, 90), "C12": (86.5, 96.5, 0),
    # comparator block (SE)
    "U3": (104.0, 88.0, 0),
    "J7": (97.0, 107.0, 0), "J8": (105.5, 107.0, 0), "J9": (114.0, 107.0, 0),
    "R20": (96.0, 100.5, 0), "R21": (104.5, 100.5, 0), "R22": (113.0, 100.5, 0),
    "R23": (112.0, 80.5, 0), "R26": (112.0, 83.0, 0),
    "R24": (112.0, 86.0, 0), "R27": (112.0, 88.5, 0),
    "R25": (112.0, 91.5, 0), "R28": (112.0, 94.0, 0),
    "R29": (120.0, 80.5, 0), "R32": (120.0, 83.0, 0),
    "R30": (120.0, 86.0, 0), "R33": (120.0, 88.5, 0),
    "R31": (120.0, 91.5, 0), "R34": (120.0, 94.0, 0),
    "C6": (98.5, 81.0, 0),
    # test points
    "TP1": (126.0, 80.5, 0), "TP2": (126.0, 86.0, 0), "TP3": (126.0, 91.5, 0),
    "TP4": (89.0, 93.0, 0), "TP5": (84.0, 70.0, 0), "TP6": (92.0, 99.0, 0),
    # buttons east edge (opening E) + networks
    "J10": (137.8, 66.0, 90), "J11": (137.8, 78.0, 90), "J12": (137.8, 90.0, 90),
    "R40": (128.0, 63.5, 0), "C8": (128.0, 66.0, 0), "R43": (128.0, 68.5, 0),
    "R41": (128.0, 75.5, 0), "C9": (128.0, 78.0, 0), "R44": (128.0, 80.5, 0),
    "R42": (128.0, 87.5, 0), "C10": (128.0, 90.0, 0), "R45": (128.0, 92.5, 0),
    # OLED header NE, pins W->E (GND VCC SCL SDA)
    "J2": (122.0, 54.5, 90),
    "R50": (114.0, 58.0, 0), "R51": (114.0, 60.5, 0), "C7": (114.0, 63.0, 0),
}
MOUNT = [(55.5, 55.5), (136.5, 55.5), (55.5, 106.5), (136.5, 106.5)]

# plain-words silkscreen (P8/P10). (text, x, y, size, bold)
SILK = [
    ("LASER 1", 61.5, 102.9, 0.9), ("LASER 2", 70.0, 102.9, 0.9), ("LASER 3", 78.5, 102.9, 0.9),
    ("PHOTODIODE 1", 97.0, 102.9, 0.75), ("PHOTODIODE 2", 105.5, 102.9, 0.75), ("PHOTODIODE 3", 114.0, 102.9, 0.75),
    ("5V", 59.8, 104.5, 0.7), ("SW", 63.3, 104.5, 0.7),
    ("5V", 68.3, 104.5, 0.7), ("SW", 71.8, 104.5, 0.7),
    ("5V", 76.8, 104.5, 0.7), ("SW", 80.3, 104.5, 0.7),
    ("5V", 95.3, 104.5, 0.7), ("PD", 98.8, 104.5, 0.7),
    ("5V", 103.8, 104.5, 0.7), ("PD", 107.3, 104.5, 0.7),
    ("5V", 112.3, 104.5, 0.7), ("PD", 115.8, 104.5, 0.7),
    ("BUTTON 1", 133.5, 61.5, 0.8), ("BUTTON 2", 133.5, 73.5, 0.8), ("BUTTON 3", 133.5, 85.5, 0.8),
    ("IN", 134.8, 64.2, 0.7), ("GND", 134.8, 67.8, 0.7),
    ("IN", 134.8, 76.2, 0.7), ("GND", 134.8, 79.8, 0.7),
    ("IN", 134.8, 88.2, 0.7), ("GND", 134.8, 91.8, 0.7),
    # OLED header words + swapped-module warning (P8: prominent)
    ("GND", 122.0, 52.2, 0.8), ("VCC", 124.5, 52.2, 0.8),
    ("SCL", 127.0, 52.2, 0.8), ("SDA", 129.5, 52.2, 0.8),
    ("OLED 3V3", 125.0, 57.0, 0.9),
    ("CHECK MODULE PINOUT!", 125.0, 58.8, 0.9),
    ("SOME OLEDS SWAP GND/VCC", 125.0, 60.5, 0.75),
    # tactiles + LED + USB
    ("RESET", 75.0, 71.8, 0.9), ("BOOT", 85.0, 71.8, 0.9),
    ("PWR", 65.5, 78.2, 0.7),
    ("USB-C 5V", 55.5, 58.0, 0.8),
    # test points
    ("COMP1", 129.5, 80.5, 0.7), ("COMP2", 129.5, 86.0, 0.7), ("COMP3", 129.5, 91.5, 0.7),
    ("5V", 89.0, 91.3, 0.7), ("3V3", 84.0, 68.3, 0.7), ("GND", 92.0, 97.3, 0.7),
    # pin map (P7: silkscreened)
    ("PIN MAP", 78.0, 82.5, 0.9),
    ("COMP1-3 = IO4 IO5 IO6", 78.0, 84.2, 0.7),
    ("LASER1-3 = IO7 IO15 IO16", 78.0, 85.7, 0.7),
    ("BTN1-3 = IO17 IO18 IO21", 78.0, 87.2, 0.7),
    ("SDA=IO1 SCL=IO2", 78.0, 88.7, 0.7),
    ("esp32-laser-timing v1.0", 96.0, 71.0, 0.9),
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

    # outline
    for (xa, ya, xb, yb) in [(X0, Y0, X1, Y0), (X1, Y0, X1, Y1),
                             (X1, Y1, X0, Y1), (X0, Y1, X0, Y0)]:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        seg.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.15))
        board.Add(seg)

    # mounting holes: M3 (3.2mm drill)
    for i, (hx, hy) in enumerate(MOUNT, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty", "MountingHole_3.2mm_M3")
        mh.SetReference(f"H{i}")
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        mh.SetPosition(pcbnew.VECTOR2I_MM(hx, hy))
        board.Add(mh)

    placed = 0
    for ref, (fpid, val) in sorted(comps.items()):
        if not fpid:
            raise RuntimeError(f"{ref} has no footprint in the netlist - "
                               f"fix generate_schematic.py footprint maps")
        if ref not in ANCHOR:
            raise RuntimeError(f"{ref} has no floorplan anchor")
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(val)
        x, y, rot = ANCHOR[ref]
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

    # netlist->board completeness: every netted pad landed
    board_pads = {(f.GetReference(), p.GetNumber())
                  for f in board.GetFootprints() for p in f.Pads()}
    missing = [k for k in pad_net if k not in board_pads]
    if missing:
        raise RuntimeError(f"netlist pads missing on board: {missing}")

    # ---- orientation asserts ----
    def centv(ref):
        f = board.FindFootprintByReference(ref)
        bb = f.GetBoundingBox(False, False)
        pads = [p.GetPosition() for p in f.Pads()]
        pcx = sum(p.x for p in pads) / len(pads)
        pcy = sum(p.y for p in pads) / len(pads)
        return bb.Centre().x - pcx, bb.Centre().y - pcy

    # USB-C opening must overhang W
    vx, vy = centv("J1")
    if vx >= 0:
        raise RuntimeError(f"J1 opening faces the wrong way v=({vx/1e6:.2f},{vy/1e6:.2f})")
    # terminals: wire opening toward its board edge
    for ref, want in [("J4", (0, 1)), ("J5", (0, 1)), ("J6", (0, 1)),
                      ("J7", (0, 1)), ("J8", (0, 1)), ("J9", (0, 1)),
                      ("J10", (1, 0)), ("J11", (1, 0)), ("J12", (1, 0))]:
        vx, vy = centv(ref)
        if vx * want[0] + vy * want[1] <= 0:
            raise RuntimeError(f"{ref} wire opening faces the wrong way v=({vx/1e6:.2f},{vy/1e6:.2f})")
    # module antenna: pad-1 end (antenna) must point north; antenna area off-board
    u1 = board.FindFootprintByReference("U1")
    p1 = {p.GetNumber(): p.GetPosition() for p in u1.Pads() if p.GetNumber()}
    if not (p1["1"].y < p1["14"].y and abs(p1["1"].y - p1["40"].y) < 1000):
        raise RuntimeError("U1 rotation wrong: pads 1/40 must be the north end")
    ant_end = p1["1"].y / 1e6 - 1.5 + 0.4   # pad1 center ~1.5mm below body-top+6mm? conservative:
    # body top = pad1.y - 6.75 (pad1 at 6.75mm below module top edge per fig 11-1);
    body_top = p1["1"].y / 1e6 - 6.75
    if body_top + 6.0 > Y0 + 0.05:
        raise RuntimeError(f"U1 antenna area ends at y={body_top+6.0:.2f} — must be <= {Y0} (off-board)")
    # OLED header pin order W->E
    j2 = board.FindFootprintByReference("J2")
    jp = {p.GetNumber(): p.GetPosition() for p in j2.Pads()}
    if not (jp["1"].x < jp["4"].x and abs(jp["1"].y - jp["4"].y) < 1000):
        raise RuntimeError("J2 pins must run west->east (GND VCC SCL SDA)")

    # electrolytic polarity: C11 pad 1 (positive) must carry 5V
    c11 = board.FindFootprintByReference("C11")
    for p in c11.Pads():
        if p.GetNumber() == "1" and p.GetNetname() != "5V":
            raise RuntimeError("C11 pad1 (+) must be 5V — polarity fact from part.yaml")

    # ---------------------------------------------------- legalize passives
    KEEP = {r for r in ANCHOR if r[0] in "JQU" or r.startswith("SW") or r.startswith("TP")}
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
        if not (X0 + 0.8 + w2 < x < X1 - 0.8 - w2 and Y0 + 0.8 + h2 < y < Y1 - 0.8 - h2):
            return False
        for hx, hy in holes:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < 2.6:
                return False
        for r2, f2 in fps.items():
            if r2 == skip or r2.startswith("H"):
                continue
            L, T, R, B = bbox(f2)
            if not (x + w2 + 0.3 <= L or R <= x - w2 - 0.3 or
                    y + h2 + 0.3 <= T or B <= y - h2 - 0.3):
                return False
        return True
    moved = 0
    for r in sorted(fps):
        f = fps[r]
        if r in KEEP or r.startswith("H"):
            continue
        if clear_at(f, pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y), r):
            continue
        ox, oy = pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y)
        done = False
        for ring in [0.5 * k for k in range(1, 30)]:
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
            raise RuntimeError(f"legalizer: no clear spot for {r} within 15mm")
    print(f"legalized {moved} small parts")

    # design rules floor (JLC 2-layer standard)
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
    def add_zone(net, layer, pts, prio, minw=0.25, clr=0.25, full=False):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(netmap[net])
        z.SetAssignedPriority(prio)
        z.SetMinThickness(pcbnew.FromMM(minw))
        z.SetLocalClearance(pcbnew.FromMM(clr))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full
                           else pcbnew.ZONE_CONNECTION_THERMAL)
        z.Outline().NewOutline()
        for x, y in pts:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)
        return z

    FULL = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
    add_zone("GND", pcbnew.F_Cu, FULL, 0)
    add_zone("GND", pcbnew.B_Cu, FULL, 0, full=False)
    # 3V3 thermal patch under the LDO tab (tab = VOUT = 3V3, part.yaml gotcha)
    add_zone("3V3", pcbnew.F_Cu, [(66, 84), (76, 84), (76, 93), (66, 93)], 2,
             minw=0.3, full=True)

    # ------------------------------------------------------------- silk text
    for entry in SILK:
        txt, x, y, size = entry
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(max(0.13, size * 0.16)))
        board.Add(t)

    for fp in board.GetFootprints():
        ref = fp.Reference()
        ref.SetLayer(pcbnew.F_Fab)
        ref.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
        ref.SetTextThickness(int(0.08e6))
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(MOUNT)} holes; zones; silk; saved {PCB.name}")


if __name__ == "__main__":
    main()
