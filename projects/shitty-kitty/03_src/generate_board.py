#!/usr/bin/env python3
"""Generate 04_kicad/shitty_kitty.kicad_pcb from the netlist + floorplan.

130x75mm 4-layer (ADR-0003): F.Cu parts+routing, In1 solid GND plane,
In2 power pours (12V east L-shape / 5V south-center / 3V3 west L-shape),
B.Cu routing + GND pour. Placement: electrode headers J3/J4 north edge with
their MPR121s adjacent (short stubs); ESP32 module center-south, antenna
overhangs the SOUTH edge; USB-C west edge; 12V entry NE corner -> buck ->
TMC2209 -> motor XH on the east edge. Missing footprint = HARD ERROR.

Run with KiCad-bundled python: /usr/bin/python3 03_src/generate_board.py
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
K = HERE.parent / "04_kicad"
NETLIST = HERE.parent / "06_build" / "netlists" / "shitty_kitty.net"
PCB = K / "shitty_kitty.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "shitty_kitty.pretty")

X0, Y0, W, H = 50.0, 50.0, 130.0, 75.0
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
    root = PROJ if lib == "shitty_kitty" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
ANCHOR = {
    # north edge: electrode headers (pin1 west, row horizontal) + MPR121s
    "J3": (58.0, 54.5, 270), "J4": (100.0, 54.5, 270),
    "U3": (64.0, 63.5, 0), "U4": (79.0, 63.5, 0),
    "U5": (106.0, 63.5, 0), "U6": (121.0, 63.5, 0),
    # per-chip support (legalizer may nudge)
    "C30": (58.5, 69.0, 0), "C31": (61.5, 71.5, 0), "R20": (64.5, 69.0, 0), "R21": (67.5, 71.5, 0),
    "C32": (73.5, 69.0, 0), "C33": (76.5, 71.5, 0), "R22": (79.5, 69.0, 0), "R23": (82.5, 71.5, 0),
    "C34": (100.5, 69.0, 0), "C35": (103.5, 71.5, 0), "R24": (106.5, 69.0, 0), "R25": (109.5, 71.5, 0),
    "C36": (115.5, 69.0, 0), "C37": (118.5, 71.5, 0), "R26": (121.5, 69.0, 0), "R27": (124.5, 71.5, 0),
    # I2C pullups + accel
    "R12": (91.0, 76.0, 0), "R13": (91.0, 79.0, 0),
    "U7": (95.0, 84.0, 0), "C18": (99.5, 82.0, 0), "C19": (99.5, 86.0, 90),
    # USB-C west edge + ESD
    "J2": (54.2, 95.0, 270), "D1": (64.0, 88.0, 0),
    "R4": (62.0, 99.5, 0), "R5": (62.0, 102.0, 0), "C8": (62.0, 104.5, 0),
    # ESP32: antenna overhangs SOUTH edge (rot 180)
    "U1": (95.0, 118.5, 180),
    "C9": (107.5, 106.0, 90), "C10": (107.5, 110.0, 90),
    "R6": (76.0, 104.0, 0), "C11": (76.0, 107.0, 0),
    "SW2": (70.0, 96.0, 0), "SW1": (70.0, 112.0, 0),
    "R7": (66.0, 84.0, 0), "D5": (66.0, 80.5, 0),
    # 12V entry NE (hole-safe: J1 at y=70)
    "J1": (172.5, 70.0, 0),
    "F1": (163.0, 63.0, 0), "Q1": (162.0, 74.0, 270), "R1": (154.0, 74.0, 0),
    "D3": (155.0, 63.0, 0), "C40": (170.0, 80.5, 0), "C25": (162.0, 80.5, 0),
    # buck (SW loop tight) + LDO
    "U8": (146.0, 88.0, 0), "C1": (140.0, 83.0, 0), "C2": (140.0, 86.0, 0),
    "C5": (152.0, 83.0, 0), "L1": (146.0, 96.5, 0),
    "C3": (140.0, 102.5, 0), "C4": (140.0, 105.5, 0),
    "U9": (128.0, 100.0, 0), "C6": (122.0, 96.0, 0), "C7": (122.0, 104.0, 0),
    "R3": (130.0, 108.5, 0), "D2": (134.5, 108.5, 0),
    # TMC2209 + support, sense, motor + endstop connectors east edge
    "U2": (160.0, 103.0, 0),
    "C14": (153.5, 98.0, 0), "C15": (166.5, 98.0, 0), "C41": (172.0, 88.5, 0),
    "C12": (166.5, 108.0, 0), "C26": (153.5, 108.0, 0), "C13": (153.5, 111.0, 0),
    "C16": (153.5, 114.0, 0), "R8": (153.5, 117.0, 0), "R9": (157.0, 117.0, 90),
    "R30": (160.5, 96.0, 0), "R31": (160.5, 110.5, 0),
    "J5": (176.0, 103.0, 90), "J6": (176.0, 116.5, 90),
    "R10": (166.5, 111.5, 0), "C17": (166.5, 114.5, 0), "R11": (166.5, 117.5, 0),
    # host header south edge (east of module antenna span)
    "J8": (118.0, 121.0, 270),
}
MOUNT = [(55.5, 55.5), (174.5, 55.5), (55.5, 119.5), (174.5, 119.5)]

SILK = [
    # electrode pin numbering (J3/J4 pins at 2.54 pitch from pin1 x)
    *[(f"{n}", 58.0 + 2.54 * (n - 1), 51.2, 0.7) for n in range(1, 13)],
    ("G", 58.0 + 2.54 * 12, 51.2, 0.7),
    *[(f"{n}", 100.0 + 2.54 * (n - 1), 51.2, 0.7) for n in range(1, 13)],
    ("G", 100.0 + 2.54 * 12, 51.2, 0.7),
    ("ELECTRODES INNER 1-12 + G", 73.0, 58.5, 1.0),
    ("ELECTRODES OUTER 1-12 + G", 115.0, 58.5, 1.0),
    # power entry
    ("12V IN", 172.5, 61.5, 1.0), ("2.1mm CENTER +", 170.0, 63.5, 0.7),
    # motor + endstop (J5 pins vertical from pin1 y=99.25)
    ("MOTOR", 171.5, 96.5, 1.0),
    ("A1", 172.6, 99.3, 0.7), ("A2", 172.6, 101.8, 0.7),
    ("B1", 172.6, 104.3, 0.7), ("B2", 172.6, 106.8, 0.7),
    ("ENDSTOP", 170.0, 111.5, 0.9), ("SIG", 171.5, 114.8, 0.65), ("GND", 171.5, 118.3, 0.65),
    # host header pins (vertical column at x=118, pin1 y=121? see anchor rot)
    ("HOST UART+5V", 121.5, 113.5, 0.9), ("5V MAX 1.5A", 121.5, 115.2, 0.7),
    # usb
    ("USB-C DATA ONLY", 57.0, 87.5, 0.7), ("POWER FROM 12V", 57.0, 89.0, 0.7),
    ("RESET", 70.0, 92.2, 0.8), ("BOOT", 70.0, 108.2, 0.8),
    ("PWR", 138.0, 108.5, 0.7), ("STATUS", 66.0, 77.5, 0.7),
    ("shitty-kitty v1.0", 95.0, 100.0, 1.0),
    ("MOTOR OFF AT BOOT: ENN PULLUP R8", 128.0, 118.7, 0.6),
]


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)

    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    for (xa, ya, xb, yb) in [(X0, Y0, X1, Y0), (X1, Y0, X1, Y1),
                             (X1, Y1, X0, Y1), (X0, Y1, X0, Y0)]:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        seg.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.15))
        board.Add(seg)

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

    # ---- orientation asserts ----
    def pads_of(ref):
        f = board.FindFootprintByReference(ref)
        return {p.GetNumber(): p.GetPosition() for p in f.Pads() if p.GetNumber()}

    def centv(ref):
        f = board.FindFootprintByReference(ref)
        bb = f.GetBoundingBox(False, False)
        pads = [p.GetPosition() for p in f.Pads()]
        pcx = sum(p.x for p in pads) / len(pads)
        pcy = sum(p.y for p in pads) / len(pads)
        return bb.Centre().x - pcx, bb.Centre().y - pcy

    # electrode headers: pin1 west, horizontal row near N edge
    for ref in ("J3", "J4"):
        jp = pads_of(ref)
        if not (jp["1"].x < jp["13"].x and abs(jp["1"].y - jp["13"].y) < 1000):
            raise RuntimeError(f"{ref} pins must run west->east")
        if abs(jp["1"].y / 1e6 - 54.5) > 1.0:
            raise RuntimeError(f"{ref} not at the north row")
    # J5 motor + J6 endstop: vertical columns on east edge; J8 host: vertical
    j5 = pads_of("J5")
    if not (j5["1"].y < j5["4"].y and abs(j5["1"].x - j5["4"].x) < 1000):
        raise RuntimeError("J5 pins must run north->south")
    j8 = pads_of("J8")
    if not (j8["1"].y < j8["6"].y and abs(j8["1"].x - j8["6"].x) < 1000):
        raise RuntimeError("J8 pins must run north->south")
    # USB-C opening W
    vx, vy = centv("J2")
    if vx >= 0:
        raise RuntimeError(f"J2 opening faces the wrong way v=({vx/1e6:.2f},{vy/1e6:.2f})")
    # barrel jack opening E
    vx, vy = centv("J1")
    if vx <= 0:
        raise RuntimeError(f"J1 opening faces the wrong way v=({vx/1e6:.2f},{vy/1e6:.2f})")
    # endstop terminal opening E
    vx, vy = centv("J6")
    if vx <= 0:
        raise RuntimeError(f"J6 opening faces the wrong way v=({vx/1e6:.2f},{vy/1e6:.2f})")
    # module antenna: pad1/40 row must be the SOUTH end (rot 180), antenna off-board
    p1 = pads_of("U1")
    if not (p1["1"].y > p1["14"].y and abs(p1["1"].y - p1["40"].y) < 1000):
        raise RuntimeError("U1 rotation wrong: pads 1/40 must be the south end")
    body_bot = p1["1"].y / 1e6 + 6.75
    if body_bot - 6.0 < Y1 - 0.05:
        raise RuntimeError(f"U1 antenna area starts at y={body_bot-6.0:.2f} — must be >= {Y1} (off-board)")

    # polarity asserts (part.yaml facts)
    POL = [("C40", "1", "VIN_12V"), ("C41", "1", "VIN_12V"),
           ("D2", "1", "GND"), ("D5", "1", "GND"),
           ("D3", "1", "VIN_12V"),          # TVS cathode to +12V
           ("Q1", "2", "VIN_F"),            # P-FET drain (tab) = input side
           ("Q1", "3", "VIN_12V")]          # source = load side
    for ref, pad, want in POL:
        f = board.FindFootprintByReference(ref)
        got = {p.GetNumber(): p.GetNetname() for p in f.Pads()}[pad]
        if got != want:
            raise RuntimeError(f"POLARITY {ref} pad{pad} net {got} != {want}")
    # cat-safety: ENN pullup exists 3V3->ENN
    r8 = {p.GetNumber(): p.GetNetname() for p in
          board.FindFootprintByReference("R8").Pads()}
    if sorted(r8.values()) != ["3V3", "ENN"]:
        raise RuntimeError(f"R8 must pull ENN to 3V3 (motor off at boot), got {r8}")

    # ---------------------------------------------------- legalize passives
    KEEP = {r for r in ANCHOR if r[0] in "JQU" or r.startswith("SW")}
    def bbox(f):
        if f.GetReference() == "U1":
            return (86.0, 105.7, 104.0, Y1)  # tight body box, on-board part
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

    # design rules floor (JLC 4-layer standard tier)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.127)
    ds.m_MinClearance = int(0.127e6)
    ds.m_ViasMinAnnularWidth = int(0.075e6)
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
    add_zone("GND", pcbnew.F_Cu, FULL, 0, full=True)
    add_zone("GND", pcbnew.B_Cu, FULL, 0)
    add_zone("GND", pcbnew.In1_Cu, FULL, 0, full=True)   # THE return plane
    # In2 power pours (non-overlapping partition)
    add_zone("VIN_12V", pcbnew.In2_Cu,
             [(138, 50), (180, 50), (180, 125), (154, 125), (154, 96), (138, 96)],
             2, minw=0.3, full=True)
    add_zone("5V", pcbnew.In2_Cu,
             [(108, 96), (154, 96), (154, 125), (108, 125)], 2, minw=0.3, full=True)
    add_zone("3V3", pcbnew.In2_Cu,
             [(50, 50), (138, 50), (138, 96), (108, 96), (108, 125), (50, 125)],
             2, minw=0.3, full=True)

    # ------------------------------------------------------------- silk text
    for txt, x, y, size in SILK:
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
