#!/usr/bin/env python3
"""Generate 04_kicad/cook_hub.kicad_pcb from the netlist + floorplan.

185x112mm 4-layer (L1 sig / In1 GND / In2 power pours / L4 sig). NE
quadrant = relay bank + isolated keypad comb (ADR-0002/D15): 8 super-columns
x 2 rows of DIP05-1A72-12L, J11 2x16 IDC in the north strip, milled slots
between columns. NO SELV plane/pour/KRT copper inside geom.NOGO; the
sanctioned bank copper (contact comb, coil verticals/lanes, RELAY_5V bus)
is drawn post-route by route_bank.py. Missing footprint = HARD ERROR.
Refdes de-collision prints every reference on F.SilkS (canon 3b) +
functional silk (P5) incl. the silk-labelled isolation boundary (§8.4).

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
NETLIST = HERE.parent / "06_build" / "netlists" / "cook_hub.net"
PCB = K / "cook_hub.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "cookhub.pretty")
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
    root = PROJ if lib == "cookhub" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
ANCHOR = {}
# relay bank: Kn center = (COIL_X[k]+3.81, ROW_Y[row]+7.62)
for n in range(1, 17):
    k = (n + 1) // 2 - 1
    row = (n - 1) % 2
    ANCHOR[f"K{n}"] = (G.COIL_X[k] + 3.81, G.ROW_Y[row] + 7.62, 0)
    # coil test point: on the coil net, straight south of pin 7
    ANCHOR[f"TP{40 + n}"] = (G.COIL_X[k], G.ROW_Y[row] + G.PIN_SPAN + 1.85, 0)
ANCHOR["J11"] = (*G.J11_XY, 0)
ANCHOR["J2"] = (*G.PICO_XY, 0)
ANCHOR["U5"] = (*G.ULN1_XY, None)      # rot resolved by assert below
ANCHOR["U6"] = (*G.ULN2_XY, None)
ANCHOR.update({
    # west edge connectors (north->south)
    "J5": (25.0, 33.0, 90), "J15": (37.0, 23.2, 270),
    "J3": (24.5, 46.0, 90), "J4": (24.5, 62.0, 90), "J14": (24.5, 78.0, 90),
    "J7": (24.5, 92.0, 90), "J8": (24.5, 101.0, 90),
    # south edge connectors (row Y1-4 = y136; respaced along the wider south edge)
    "J1": (37.0, 129.0, 270), "J9": (55.0, 136.0, 0), "J6": (76.0, 136.0, 0),
    "J10": (99.0, 136.0, 0), "J12": (116.0, 136.0, 0), "J13": (137.0, 136.0, 0),
    # power entry / rails — SW corner power column (freed by moving logic east)
    "F1": (28.0, 117.0, 90), "Q3": (34.0, 117.0, 0), "D2": (40.0, 117.0, 0),
    "CE1": (46.0, 121.0, 0), "U12": (56.0, 122.0, 0),  # U12 +3mm E: SOT-223 tab was shorting CE1 GND pad (ADR-0006 power column extends to x60)
    "D1": (34.0, 122.0, 0), "FB1": (28.0, 26.0, 0),
    # analog corner
    "U1": (34.0, 33.0, 0),
    # safety/watchdog chain around Q1 (original layout — route_bank RELAY_5V
    # spurs are tuned for these C8/C9/R25/TP33 via-sites; the coil-driver
    # squeeze this ADR fixes was in the east strip, not here)
    "U7": (66.5, 110.0, 0), "U8": (66.5, 118.0, 0), "U9": (75.0, 110.0, 0),
    "Q2": (74.0, 118.0, 0), "Q1": (*G.Q1_XY, 0), "R23": (52.0, 110.5, 0),
    # C8 (Q1 output decoupler) stays in the Q1 pocket (IP<=6mm); the other
    # RELAY_5V bus parts distribute east into clear inter-column gaps so their
    # bus spurs get uncontested In2 lanes and free the pocket for WD_PULSE
    "C8": (61.5, 112.5, 0), "C9": (124.0, 109.0, 0), "R25": (128.0, 109.0, 0),
    "TP33": (132.0, 109.0, 0),
    # coil-drive shift registers -> EAST strip, each south-east of its ULN
    # (decouplers pinned: dense TP/logic cluster pushed floaters off-limit)
    "U3": (112.0, 120.0, 0), "U4": (170.0, 120.0, 0),
    "C12": (112.0, 124.5, 0), "C13": (170.0, 124.5, 0),
    # U7 watchdog trio pinned (390k R11 + timing C14 + decoupler C11): the
    # SC70 + 3 passives in one pocket is too tight for the ring-legalizer
    # loosened out of the U7 pad-field into the free pocket S/E of U7 (NOGO y<=106.8
    # forbids going N; U8 y117 bounds S). All keep IP<=6mm to U7: R11 4.3, C14 4.95, C11 2.3.
    "R11": (66.5, 114.3, 0), "C14": (70.0, 113.5, 0), "C11": (71.5, 110.0, 90),
    # contactor opto + ESD, above J10
    "U10": (99.0, 127.0, 0), "U15": (110.0, 127.0, 0),
    # I2C ESD (C21 pinned at U14: crowded I2C1 cluster pushed it as a floater)
    # C21 was landing pad1 on J2 Pico socket pad1 (SDA0); moved N of its IC U14 (IP 3mm)
    "U13": (30.2, 48.0, 0), "U14": (30.2, 64.0, 0), "C21": (30.2, 61.0, 0),
    # estop/door schmitt (east-south open area; RC caps seed alongside)
    "U11": (90.0, 120.0, 0),
    "SW1": (56.0, 94.0, 0),
})

# floater seeds (ring-legalized): near their electrical neighbours
SEED = {
    "R12": (37, 122), "C4": (43, 124), "C5": (47, 124), "C1": (56, 124),
    "C2": (53, 125), "C3": (39, 121), "C6": (28, 29), "C7": (30.5, 26),
    "C10": (37, 124), "TP1": (44, 128), "TP2": (50, 128), "TP3": (30.5, 29),
    "TP4": (31, 124), "TP5": (176, 124),
    "C11": (73, 113), "C14": (67, 114), "R21": (71, 116),
    "R22": (72, 121), "R24": (79, 114),
    "C15": (62, 121), "C16": (78, 113),
    "TP20": (108, 116), "TP21": (58, 118), "TP22": (63, 116),
    "C12": (112, 124), "C13": (170, 124), "TP17": (106, 124), "TP18": (116, 124),
    "TP19": (110, 116),
    "R26": (103, 124), "TP28": (99, 131), "C22": (108, 124),
    "TP15": (176, 116), "TP16": (164, 124),
    "C20": (31.5, 51), "R41": (36, 44), "R42": (36, 46.5), "R71": (37, 50),
    "R72": (40, 50), "R73": (43, 50), "R74": (46, 50), "JP1": (37, 54),
    "TP6": (34, 46), "TP7": (34, 48.5),
    "C21": (31.5, 61.5), "R43": (36, 64), "R44": (36, 66.5), "R75": (29, 68),
    "R76": (31.5, 68), "R77": (29, 70.5), "R78": (31.5, 70.5), "JP2": (29.5, 74),
    "TP8": (29, 72.8), "TP9": (31.5, 72.8),
    "R61": (28.5, 37), "R62": (31, 37), "C61": (33.5, 37), "C62": (36, 37),
    "C63": (38.5, 37), "C18": (41, 33), "C19": (43.5, 33), "TP34": (41, 29.5),
    "TP35": (44, 29.5), "TP10": (37, 26.5), "TP11": (40, 26.5), "TP12": (43, 26.5),
    "TP13": (46, 26.5), "TP14": (49, 26.5),
    "R51": (30, 108), "R54": (33, 108), "C51": (36, 108), "D5": (39, 108),
    "TP25": (42, 108), "R52": (30, 111), "R55": (33, 111), "C52": (36, 111),
    "D6": (39, 111), "TP26": (42, 111), "R53": (30, 105), "R56": (33, 105),
    "C53": (36, 105), "D7": (39, 105), "TP27": (42, 105),
    # door/estop ESD stay at their west connectors; RC filters move to the
    # schmitt U11 (receiver-side filtering) in the east-south open area
    "D4": (29.5, 90), "SJ1": (32, 88), "JP5": (29.5, 85), "TP23": (94, 124),
    "R33": (88, 116), "R34": (90, 116), "C33": (92, 116),
    "R31": (86, 124), "R32": (88, 124), "C31": (90, 124), "D3": (29.5, 103),
    "C17": (96, 120), "TP24": (84, 124),
    "TP29": (56, 88), "TP30": (56, 91), "TP31": (56, 85), "TP32": (56, 82),
}

# refs with exact engineered positions — legalizer must not move them
KEEP = set(ANCHOR)

# plain-words silkscreen (P-SILK-FN + §8.4/§8.5). (text, x, y, size[, rot])
SILK = [
    ("EXT 5V 2A IN", 34.0, 128.7, 0.9), ("CENTER PIN +5V", 34.0, 130.4, 0.7),
    ("NTC: PORT GND ENCL GND SPARE GND", 55.0, 131.0, 0.6),
    ("J9 THERMISTORS", 55.0, 132.6, 0.8),
    ("LOADCELL DIGITAL", 76.0, 131.0, 0.8), ("5V 3V3 G DAT CLK", 76.0, 132.6, 0.7),
    ("CONTACTOR OUT", 99.0, 131.0, 0.8), ("C  E  30V 50mA MAX", 99.0, 132.6, 0.7),
    ("TURNTABLE ENC (DNP)", 116.0, 131.0, 0.7), ("3V3 G A B HOME", 116.0, 132.6, 0.65),
    ("STEP DIR EN G (DNP)", 137.0, 131.0, 0.7),
    ("TC K-TYPE", 25.2, 27.8, 0.9), ("YEL+  RED-", 25.2, 29.4, 0.8),
    ("MAX31865 DNP", 43.0, 20.9, 0.7), ("3V3A G SCK MOSI MISO CS1", 43.0, 25.0, 0.6),
    ("I2C0 MLX90640+SHT45", 33.0, 40.2, 0.8), ("3V3 G SDA SCL", 24.7, 48.4, 0.7),
    ("I2C1 EXHAUST SHT45", 33.5, 58.5, 0.8), ("3V3 G SDA SCL", 24.7, 64.4, 0.7),
    ("SPARE I2C0+GP4", 25.2, 80.5, 0.8),
    ("DOOR NC+EOL", 30.5, 90.5, 0.8), ("HALL RAW GND", 24.7, 94.6, 0.65),
    ("E-STOP NC", 30.0, 103.8, 0.8),
    ("PICO 2 MODULE - USB TO PI 5", 42.0, 111.5, 0.9),
    ("JP1: I2C0 PU 1-2=2k2 2-3=4k7", 40.0, 56.5, 0.6),
    ("JP2: I2C1 PU 1-2=2k2 2-3=4k7", 36.5, 74.5, 0.6),
    ("JP5 1-2: HALL PWR", 30.5, 79.5, 0.6),
    ("SJ1: DOOR EOL->ADC2 (unfit TH3)", 33.5, 88.7, 0.55),
    ("RUN", 56.0, 91.7, 0.7),
    ("cook-hub v1.0  SMC0985KS PHASE-1 HUB", 150.0, 132.0, 1.0),
    ("HW WATCHDOG", 70.0, 108.8, 0.7),
    ("RELAY COIL DRIVERS", 140.0, 115.5, 0.8),
    ("E-STOP+DOOR SCHMITT", 90.0, 114.0, 0.6),
    # isolation boundary story (§8.4)
    ("ISOLATED KEYPAD ZONE - UNKNOWN VOLTAGE", 132.0, 22.3, 1.2),
    ("NO SELV COPPER / NO PROBING IN ENCLOSURE", 132.0, 24.4, 0.8),
    ("J11 KEYPAD: CH n = PINS 2n-1,2n  (CH1 WEST)", 140.0, 36.6, 0.8),
    ("SELV SIDE", 55.0, 24.0, 0.9, 90),
    ("BOUNDARY: >=6MM CREEPAGE + MILLED SLOTS", 132.0, 99.5, 0.8),
]
for n in (1, 8, 9, 16):
    SILK.append((f"CH{n}", G.J11_COL0_X + (n - 1) * 2.54, 26.2, 0.6))
for k in range(G.NSC):
    SILK.append(("KEYPAD", G.CONT_X[k] + 1.1, 48.8, 0.55, 90))


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)

    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    def edge_seg(xa, ya, xb, yb):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)

    edge_seg(G.X0, G.Y0, G.X1, G.Y0)
    edge_seg(G.X1, G.Y0, G.X1, G.Y1)
    edge_seg(G.X1, G.Y1, G.X0, G.Y1)
    edge_seg(G.X0, G.Y1, G.X0, G.Y0)

    # milled isolation slots (Edge.Cuts closed rectangles, 2mm wide)
    def slot(xc, y0, y1):
        h = G.SLOT_W / 2
        edge_seg(xc - h, y0, xc + h, y0)
        edge_seg(xc + h, y0, xc + h, y1)
        edge_seg(xc + h, y1, xc - h, y1)
        edge_seg(xc - h, y1, xc - h, y0)

    for sx in G.SLOT_X:
        slot(sx, G.SLOT_Y0, G.SLOT_Y1)
    slot(G.WSLOT_X, G.WSLOT_Y0, G.WSLOT_Y1)

    # NPTH mounting holes (nylon standoffs)
    for i, (hx, hy) in enumerate(G.HOLES, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty",
                                  "MountingHole_3.2mm_M3")
        if mh is None:
            raise RuntimeError("mounting hole footprint missing")
        mh.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        mh.SetReference(f"H{i}")
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        mh.SetPosition(pcbnew.VECTOR2I_MM(hx, hy))
        # mounting-hole ref off the silkscreen: it sits at the hole centre near
        # the board edge (silk_edge_clearance) and it is not needed on silk
        # (no part to identify). Keep an F.Fab copy for the assembly drawing.
        mhref = mh.Reference()
        mhref.SetVisible(False)
        mhref.SetLayer(pcbnew.F_Fab)
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
        elif ref in SEED:
            x, y = SEED[ref]
            rot = 0
        else:
            raise RuntimeError(f"{ref} has no anchor and no seed")
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        # Schematic-parity: the SJ symbol is in_bom yes but the KiCad
        # SolderJumper footprint ships exclude_from_bom set -> footprint_symbol_
        # mismatch. Clear ONLY SJ*'s BOM-exclude flag to match its symbol
        # (route/net artifact, not a schematic edit). Test points / mounting
        # holes keep their exclude flag (their symbols are in_bom no).
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
        raise RuntimeError(f"netlist pads missing on board: {missing}")

    fps = {f.GetReference(): f for f in board.GetFootprints()}

    def padpos(ref, num):
        p = next(p for p in fps[ref].Pads() if p.GetNumber() == num)
        return MM(p.GetPosition().x), MM(p.GetPosition().y)

    def padnet(ref, num):
        return next(p for p in fps[ref].Pads()
                    if p.GetNumber() == num).GetNetname()

    # ULN rotation: find the angle putting pad 18 (OUT1) at west-north
    for ref, (ux, uy) in (("U5", G.ULN1_XY), ("U6", G.ULN2_XY)):
        ok = False
        for ang in (90, 270, 0, 180):
            fps[ref].SetOrientationDegrees(ang)
            x18, y18 = padpos(ref, "18")
            x10, y10 = padpos(ref, "10")
            x1, y1 = padpos(ref, "1")
            if (abs(x18 - (ux - 5.08)) < 0.05 and y18 < uy - 4
                    and abs(x10 - (ux + 5.08)) < 0.05 and y10 < uy - 4
                    and y1 > uy + 4):
                ok = True
                break
        if not ok:
            raise RuntimeError(f"{ref}: no rotation puts OUT1 west-north")

    # J15: pin-1-origin header must run EAST along the top edge
    okj = False
    for ang in (270, 90, 0, 180):
        fps["J15"].SetOrientationDegrees(ang)
        x1j, y1j = padpos("J15", "1")
        x6j, y6j = padpos("J15", "6")
        if x6j > x1j + 10 and abs(y6j - y1j) < 0.01:
            okj = True
            break
    if not okj:
        raise RuntimeError("J15 pads not running east")

    # Q1: drain (pad 3) must face NORTH into the pocket tongue
    okq = False
    for ang in (0, 180, 90, 270):
        fps["Q1"].SetOrientationDegrees(ang)
        _, y3 = padpos("Q1", "3")
        if y3 < G.Q1_XY[1] - 0.5:
            okq = True
            break
    if not okq:
        raise RuntimeError("Q1 drain not north")

    # J1 barrel: rotation whose bbox reaches the south edge (mouth south)
    j1 = fps["J1"]
    best = None
    for ang in (0, 90, 180, 270):
        j1.SetOrientationDegrees(ang)
        bb = j1.GetBoundingBox(False, False)
        if best is None or MM(bb.GetBottom()) > best[1]:
            best = (ang, MM(bb.GetBottom()))
    j1.SetOrientationDegrees(best[0])
    if best[1] < G.Y1 - 8.0:
        raise RuntimeError(f"J1 mouth not reaching south edge (bottom {best[1]:.1f})")

    # ---- engineered-position asserts (part.yaml facts; audit re-checks) ----
    for n in range(1, 17):
        k = (n + 1) // 2 - 1
        row = (n - 1) % 2
        assert padnet(f"K{n}", "1") == "RELAY_5V", f"K{n} pin1"
        assert padnet(f"K{n}", "7") == f"COIL_{n}", f"K{n} pin7"
        assert padnet(f"K{n}", "14") == f"KC{n}A", f"K{n} pin14"
        assert padnet(f"K{n}", "8") == f"KC{n}B", f"K{n} pin8"
        x1, y1 = padpos(f"K{n}", "1")
        assert abs(x1 - G.COIL_X[k]) < 0.01 and abs(y1 - G.ROW_Y[row]) < 0.01, \
            f"K{n} pin1 at ({x1},{y1})"
        x14, _ = padpos(f"K{n}", "14")
        assert abs(x14 - G.CONT_X[k]) < 0.01, f"K{n} pin14 x {x14}"
    for c in range(1, 17):
        xa, ya = padpos("J11", str(2 * c - 1))
        assert abs(xa - (G.J11_COL0_X + (c - 1) * 2.54)) < 0.01, f"J11 ch{c}"
        assert abs(ya - G.J11_ROWA_Y) < 0.01
        assert padnet("J11", str(2 * c - 1)) == f"KC{c}A"
        assert padnet("J11", str(2 * c)) == f"KC{c}B"
    # Pico: pin1 NW, pin 40 NE
    x, y = padpos("J2", "1")
    assert abs(x - (G.PICO_XY[0] - 8.89)) < 0.01 and abs(y - (G.PICO_XY[1] - 24.13)) < 0.01
    assert padnet("J2", "39") == "VSYS" and padnet("J2", "3") == "GND"
    # polarized pad-1 nets (D_* pad1 = cathode; CP_Elec pad1 = +)
    for ref, want in [("D1", "VSYS"), ("D2", "5VP"), ("D3", "ESTOP_RAW"),
                      ("D4", "DOOR_RAW"), ("D5", "TH1"), ("D6", "TH2"),
                      ("D7", "TH3"), ("CE1", "5VP")]:
        got = padnet(ref, "1")
        if got != want:
            raise RuntimeError(f"{ref} pad1 net {got} != {want}")
    # FET sanity (SOT-23 1=G 2=S 3=D)
    assert padnet("Q1", "2") == "5VP" and padnet("Q1", "3") == "RELAY_5V"
    assert padnet("Q3", "3") == "5V_D" and padnet("Q3", "2") == "5VP"
    assert padnet("Q2", "2") == "GND" and padnet("Q2", "3") == "Q1G"
    # ULN pairing (IN1 opposite corner from OUT1)
    assert padnet("U5", "18") == "COIL_1" and padnet("U5", "1") == "DRV1"
    assert padnet("U6", "18") == "COIL_9" and padnet("U6", "10") == "RELAY_5V"

    # ---------------------------------------------------- legalize floaters
    def bbox(f):
        bb = f.GetBoundingBox(False, False)
        return (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))

    holes = [(hx, hy) for hx, hy in G.HOLES]

    def clear_at(f, x, y, skip):
        old = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        l, t, r_, bt = bbox(f)
        f.SetPosition(old)
        w2, h2 = (r_ - l) / 2, (bt - t) / 2
        if not (G.X0 + 1.0 + w2 < x < G.X1 - 1.0 - w2 and
                G.Y0 + 1.0 + h2 < y < G.Y1 - 1.0 - h2):
            return False
        # keep floaters out of the NOGO bank region + KRT keepouts
        for (nx0, ny0, nx1, ny1) in [G.NOGO] + list(G.KRT_KEEPOUTS):
            if not (x + w2 < nx0 - 0.3 or x - w2 > nx1 + 0.3 or
                    y + h2 < ny0 - 0.3 or y - h2 > ny1 + 0.3):
                return False
        for hx, hy in holes:
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
        if r in KEEP or r.startswith("H"):
            continue
        ox, oy = MM(f.GetPosition().x), MM(f.GetPosition().y)
        if clear_at(f, ox, oy, r):
            continue
        done = False
        for ring in [0.5 * k for k in range(1, 100)]:
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
            raise RuntimeError(f"legalizer: no clear spot for {r} within 50mm")
    print(f"legalized {moved} small parts")

    # design rules floor (JLC 4-layer standard: 0.09/0.09 capability,
    # 0.45/0.2 via floor; we run 0.6/0.3 vias, 0.2 tracks, 0.127 clearance)
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

    # ------------------------------------------------------------- zones
    def add_zone(net, layer, pts, prio, minw=0.3, clr=0.3, full=False):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(netmap[net])
        z.SetAssignedPriority(prio)
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

    # SELV L-shape: whole board minus the NOGO/keypad NE region
    nx0, ny0, nx1, ny1 = G.NOGO
    LSHAPE = [(G.X0, G.Y0), (nx0, G.Y0), (nx0, ny1), (G.X1, ny1),
              (G.X1, G.Y1), (G.X0, G.Y1)]
    add_zone("GND", pcbnew.In1_Cu, LSHAPE, 0)                 # THE plane
    add_zone("GND", pcbnew.B_Cu, LSHAPE, 0)
    add_zone("3V3", pcbnew.In2_Cu, LSHAPE, 1, minw=0.4)
    # 5VP In2 pour stays WEST of x53: the x57-66 In2 corridor is reserved for
    # the RELAY_5V bank spurs (route_bank C8/C9/R25/TP33 -> bus). Q1 source 5VP
    # is routed by KRT (F.Cu west to the pour edge), not covered by the pour.
    add_zone("5VP", pcbnew.In2_Cu,
             [(26, 110), (53, 110), (53, 134), (26, 134)], 2, minw=0.4)
    add_zone("3V3A", pcbnew.In2_Cu,
             [(21, 21), (52, 21), (52, 40), (21, 40)], 2, minw=0.4)

    # ------------------------------------------------------------- silk text
    # NOTE: fixed functional SILK labels are placed LATER, through the unified
    # obstacle-aware de-collision placer (silk campaign 2026-07-19), so they
    # never land on pads / over the edge+slots / on other silk. Only the
    # structural boundary lines are drawn here (they are the §8.4 story).

    # isolation boundary comb outline on silk (§8.4): strip + corridors
    def silk_line(xa, ya, xb, yb, w=0.3):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(pcbnew.F_SilkS)
        s.SetWidth(pcbnew.FromMM(w))
        board.Add(s)

    sx0, sy0, sx1, sy1 = G.STRIP_RECT
    silk_line(sx0, sy1, sx0, sy0)
    silk_line(sx0, sy0, sx1, sy0)
    silk_line(sx1, sy0, sx1, min(sy1, 57.0))
    # corridor combs along each contact column (between strip and bank rows)
    for k in range(G.NSC):
        cx = G.CONT_X[k]
        silk_line(cx - 0.9, sy1, cx - 0.9, 56.5)
        silk_line(cx + 2.6, sy1, cx + 2.6, 56.5)

    # ============================================================ SILK CAMPAIGN
    # Unified obstacle-aware de-collision for ALL silk text (fixed functional
    # labels + refdes + TP net labels). Text floor = 0.6mm (min_text_height);
    # text never lands on a pad, over the board edge / milled slots, on
    # footprint silk, or on other text. (2026-07-19: kills text_height +
    # text-driven silk_over_copper / silk_overlap / silk_edge_clearance.)
    TH, THK, CLR = 0.6, 0.12, 0.16
    SILK_MIN = 0.6                      # min_text_height DRU floor
    PADM = 0.08                        # pad keep-away for silk (min_silk_clr=0)

    def box(bb, pad=0.0):
        return (MM(bb.GetLeft()) - pad, MM(bb.GetTop()) - pad,
                MM(bb.GetRight()) + pad, MM(bb.GetBottom()) + pad)

    def hit(a, b):
        return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])

    # obstacle: exposed pad copper (all footprints)
    pad_obst, body_obst = [], []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pad_obst.append(box(p.GetBoundingBox(), PADM))
        if not fp.GetReference().startswith("H"):
            body_obst.append(box(fp.GetBoundingBox(False, False), 0.05))
    # obstacle: Edge.Cuts (board outline + milled isolation slots) keep-away
    edge_obst = []
    for g in board.GetDrawings():
        if g.GetClass() == "PCB_SHAPE" and g.IsOnLayer(pcbnew.Edge_Cuts):
            edge_obst.append(box(g.GetBoundingBox(), 0.30))

    # SILK-TRIM: drop footprint F.SilkS graphics that overlap any exposed pad
    # or are clipped by the board edge/slots — silk over copper doesn't print
    # and F.Fab retains the body outline for assembly. Deterministic.
    edge_trim = [box(g.GetBoundingBox(), 0.12) for g in board.GetDrawings()
                 if g.GetClass() == "PCB_SHAPE" and g.IsOnLayer(pcbnew.Edge_Cuts)]
    # the §8.4 boundary silk lines (board drawings) are structural and MUST stay
    # legible; footprint silk that overlaps them (relay/connector outlines near
    # the isolation comb) is trimmed instead (silk_overlap).
    board_silk_trim = [box(g.GetBoundingBox(), 0.0) for g in board.GetDrawings()
                       if g.GetClass() == "PCB_SHAPE" and g.IsOnLayer(pcbnew.F_SilkS)]
    def safe_box(item, pad=0.0):
        try:
            bb = item.GetBoundingBox()
            return box(bb, pad)
        except Exception:
            return None

    # SILK-TRIM: footprint library outlines that cross a pad (or are clipped by
    # the board edge / milled slots) are removed from the board copy. Silk over
    # exposed copper does NOT print (it's a manufacturing defect), and F.Fab
    # keeps the full body outline for the assembly drawing, so the trim is the
    # CORRECT fab outcome. It desyncs the board footprint from its library copy
    # -> the release documents an evidence-backed `lib_footprint_mismatch:
    # ignore` severity policy (generate_rules.py); it does NOT touch schematic
    # parity (that checks symbol/footprint ATTRIBUTES, not graphics). Removals
    # are batched to the very end (fp.Remove poisons SWIG GraphicalItems
    # iterators mid-session, kicad-pcb skill).
    trim_list = []            # (fp, graphic) removed just before save
    silk_obst = []            # boundary lines + SURVIVING footprint silk
    for t in board.GetDrawings():
        if t.IsOnLayer(pcbnew.F_SilkS) and t.GetClass() in ("PCB_TEXT", "PCB_SHAPE"):
            gb = safe_box(t, CLR * 0.5)
            if gb:
                silk_obst.append(gb)
    for fp in board.GetFootprints():
        for g in fp.GraphicalItems():
            if not g.IsOnLayer(pcbnew.F_SilkS):
                continue
            gb = safe_box(g)
            if gb is None:
                continue
            if (any(hit(gb, po) for po in pad_obst)
                    or any(hit(gb, eo) for eo in edge_trim)
                    or any(hit(gb, bo) for bo in board_silk_trim)):
                trim_list.append((fp, g))         # over pad / clipped by edge / on boundary silk
            else:
                silk_obst.append(box(g.GetBoundingBox(), PADM))
    trimmed = len(trim_list)

    OFF = [(0, 0)] + \
          [(0, o * s) for o in (1.0, 1.6, 2.2, 2.9, 3.6, 4.4, 5.2, 6.0, 7.0, 8.0) for s in (-1, 1)] + \
          [(o * s, 0) for o in (1.3, 2.0, 2.8, 3.6, 4.5, 5.4, 6.2, 7.4, 8.6, 10.0, 11.5) for s in (-1, 1)] + \
          [(dx, dy) for d in (1.4, 2.2, 3.0, 4.0, 5.0, 6.0, 7.2, 8.4) for dx in (-d, d) for dy in (-d, d)]
    # nudge for fixed captions — try tight first (stay in the lane) then widen
    # progressively so a crowded caption relocates near its connector rather
    # than being dropped (functional silk P5 must survive).
    SILK_OFF = [(0, 0)] + \
        [(o * s, 0) for o in (0.7, 1.2, 1.8, 2.5, 3.3, 4.2, 5.2, 6.4, 7.8) for s in (-1, 1)] + \
        [(0, o * s) for o in (0.7, 1.2, 1.8, 2.5, 3.3, 4.2, 5.2, 6.4) for s in (-1, 1)] + \
        [(dx, dy) for d in (1.0, 1.8, 2.8, 4.0, 5.4, 7.0) for dx in (-d, d) for dy in (-d, d)]

    def try_place(t, ax, ay, sizes, offs, avoid_body=False, rots=None):
        # rots: orientations to try (deg). Default keeps the text's current
        # angle, then a 90deg rotation so a caption/refdes can stand up in a
        # tall narrow gap (west connector column) instead of being dropped.
        if rots is None:
            base = t.GetTextAngleDegrees()
            rots = [base, (base + 90) % 360]
        for rot in rots:
            t.SetTextAngleDegrees(rot)
            for sz in sizes:
                t.SetTextSize(pcbnew.VECTOR2I_MM(sz, sz))
                t.SetTextThickness(pcbnew.FromMM(max(0.13, sz * 0.16)))
                for dx, dy in offs:
                    t.SetPosition(pcbnew.VECTOR2I_MM(ax + dx, ay + dy))
                    cand = box(t.GetBoundingBox())
                    if not (G.X0 + 0.3 < cand[0] and cand[2] < G.X1 - 0.3
                            and G.Y0 + 0.3 < cand[1] and cand[3] < G.Y1 - 0.3):
                        continue
                    if any(hit(cand, o) for o in pad_obst):
                        continue
                    if any(hit(cand, o) for o in edge_obst):
                        continue
                    if any(hit(cand, o) for o in silk_obst):
                        continue
                    if avoid_body and any(hit(cand, o) for o in body_obst):
                        continue
                    silk_obst.append(cand)
                    return True
        return False

    # F.Fab refdes copy for EVERY part (assembly drawing), independent of silk.
    for fp in board.GetFootprints():
        fab = pcbnew.PCB_TEXT(board)
        fab.SetText(fp.GetReference())
        fab.SetLayer(pcbnew.F_Fab)
        fab.SetPosition(fp.GetPosition())
        fab.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
        fab.SetTextThickness(int(0.08e6))
        board.Add(fab)

    def place_refdes(fp):
        r = fp.GetReference()
        ref = fp.Reference()
        if r.startswith("H"):
            ref.SetVisible(False)
            return True
        ref.SetLayer(pcbnew.F_SilkS)
        ref.SetVisible(True)
        fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
        if try_place(ref, fx, fy, (TH, SILK_MIN), OFF, avoid_body=True):
            return True
        ref.SetVisible(False)
        return False

    # Placement priority: connector/IC refdes (must-place) -> functional
    # captions -> passive refdes (waivable tiny parts) -> TP labels. This keeps
    # the crowded west column's human-critical text (Jxx names + captions)
    # while letting a few tiny 0402 refdes fall back to F.Fab only.
    def is_major(fp):
        r = fp.GetReference()
        return r[0] in "UJKQ" or r.startswith("SW")

    waived = []
    for fp in sorted((f for f in board.GetFootprints() if is_major(f)),
                     key=lambda f: f.GetReference()):
        if not place_refdes(fp):
            waived.append(fp.GetReference())

    # ---- fixed functional SILK labels (nudged off collisions; near anchor)
    silk_dropped = []
    for entry in SILK:
        txt, x, y, size = entry[:4]
        rot = entry[4] if len(entry) > 4 else 0
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        if rot:
            t.SetTextAngleDegrees(rot)
        sizes = list(dict.fromkeys([round(max(size, SILK_MIN), 2), SILK_MIN]))
        # tight nudge first (stay in the lane), then the wide grid (relocate
        # into clear board interior — still within the audit's 14mm of the part)
        if try_place(t, x, y, sizes, SILK_OFF) or try_place(t, x, y, sizes, OFF):
            board.Add(t)
        else:
            silk_dropped.append(txt)

    for fp in sorted((f for f in board.GetFootprints()
                      if not is_major(f) and not f.GetReference().startswith("H")),
                     key=lambda f: f.GetReference()):
        if not place_refdes(fp):
            waived.append(fp.GetReference())

    # ---- TP net-name labels (functional silk P5): min-height floor, near TP
    TP_LABEL = {f.GetReference(): f.GetValue().replace("TP ", "")
                for f in board.GetFootprints() if f.GetReference().startswith("TP")}
    tp_labeled = 0
    for r, lbl in sorted(TP_LABEL.items()):
        f = fps[r]
        t = pcbnew.PCB_TEXT(board)
        t.SetText(lbl)
        t.SetLayer(pcbnew.F_SilkS)
        if try_place(t, MM(f.GetPosition().x), MM(f.GetPosition().y),
                     (SILK_MIN,), OFF):
            board.Add(t)
            tp_labeled += 1

    (HERE.parent / "06_build").mkdir(exist_ok=True)
    (HERE.parent / "06_build" / "refdes_waiver.json").write_text(json.dumps(sorted(waived)))
    print(f"silk-trim: removed {trimmed} fp silk graphics over pads/edge")
    print(f"refdes on silk: {placed - len(waived)}/{placed} placed, "
          f"{len(waived)} waived: {sorted(waived)}")
    print(f"SILK labels dropped (couldn't place): {len(silk_dropped)}: {silk_dropped}")
    print(f"TP labels placed: {tp_labeled}/{len(TP_LABEL)}")
    # batched SILK-TRIM removal — LAST, so no GraphicalItems iterator runs
    # after the first fp.Remove (SWIG poisoning trap, kicad-pcb skill).
    for fp, g in trim_list:
        fp.Remove(g)
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(G.HOLES)} holes; "
          f"{len(G.SLOT_X) + 1} slots; zones; saved {PCB.name}")


if __name__ == "__main__":
    main()
