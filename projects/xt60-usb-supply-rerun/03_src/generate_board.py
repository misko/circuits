#!/usr/bin/env python3
"""Generate 04_kicad/xt60-usb-supply.kicad_pcb from the exported netlist +
the floorplan below. Places footprints, binds pad nets, draws the outline,
adds mounting holes and all copper zones (GND planes + priority-1 power
pours). Produces a TRACK-FREE, UNFILLED board — routing is a later stage.

Run with /usr/bin/python3 (pcbnew). Never writes .kicad_pro (generate_rules
merges it afterwards; rules run LAST in the chain).

Hard rules honored: missing footprint = raise; zero-yield parse = raise.
"""
import argparse
import sys
from pathlib import Path

import pcbnew
from pcbnew import VECTOR2I, FromMM

PROJ = Path(__file__).resolve().parent.parent
KICAD = PROJ / "04_kicad"
BOARD = KICAD / "xt60-usb-supply.kicad_pcb"
NETLIST = PROJ / "06_build" / "netlists" / "xt60-usb-supply.net"

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from schwriter import _tokenize, _parse_sexpr  # noqa: E402

STD_LIB = Path("/usr/share/kicad/footprints")
PROJ_LIB = PROJ / "03_src" / "lib"

# ---------------- board geometry ----------------
X0, Y0, X1, Y1 = 100.0, 100.0, 192.0, 162.0   # outline (92 x 62 mm)

MOUNTING_HOLES = [(104.5, 104.5), (104.5, 157.5), (166.0, 104.5), (144.0, 158.0)]

# ref: (x, y, rot_deg). rot is CCW in KiCad UI convention.
FLOORPLAN = {
    # input chain, west (J1 pegs sit 6mm inboard of the blade row)
    "J1":  (107.5, 134.6, 90),    # XT60, nose overhangs west edge
    "F1":  (114.8, 127.4, 0),
    "Q1":  (124.0, 124.0, 90),    # tab (drain) north, G/S leads south
    "R1":  (120.0, 133.0, 90),    # PFET gate bleed
    "D1":  (125.5, 137.8, 0),
    "CB1": (134.0, 134.0, 0),
    "CB2": (134.0, 144.0, 0),
    "LED1": (127.0, 155.5, -90),
    "R2":  (127.0, 151.5, 90),
    # buck A (north center): rot 180 -> signal row south, IN west, LX east
    "U1":  (152.0, 118.0, 180),
    "CIN_A1": (149.0, 114.5, 90),
    "CIN_A2": (149.0, 121.5, 90),
    "CVCC1": (151.8, 123.6, 0),
    "CBS1": (154.6, 125.3, 0),
    "RFA1": (154.5, 127.2, 0),
    "RFA2": (158.0, 127.2, 0),
    "L1":  (163.0, 118.0, 0),
    "COUT_A1": (170.5, 110.0, 0),
    "COUT_A2": (170.5, 114.5, 0),
    "COUT_A3": (170.5, 121.5, 0),
    "COUT_A4": (170.5, 126.0, 0),
    # buck C (south center), mirror at y ~ +28
    "U2":  (152.0, 146.0, 180),
    "CIN_C1": (149.0, 142.5, 90),
    "CIN_C2": (149.0, 149.5, 90),
    "CVCC2": (151.8, 151.6, 0),
    "CBS2": (154.6, 153.3, 0),
    "RFC1": (154.5, 155.1, 0),
    "RFC2": (158.0, 155.1, 0),
    "L2":  (163.0, 146.0, 0),
    "COUT_C1": (166.0, 151.2, 0),
    "COUT_C2": (166.0, 154.6, 0),
    "COUT_C3": (166.0, 158.0, 0),
    "COUT_C4": (171.0, 158.0, 0),
    # USB-A east edge (rot +90 -> opening east, front overhangs edge)
    "J2":  (180.0, 112.5, 90),
    "J3":  (180.0, 129.9, 90),
    "J4":  (180.0, 147.3, 90),
    "U3":  (176.0, 109.0, 0),
    "U4":  (176.0, 126.4, 0),
    "U5":  (176.0, 143.8, 0),
    # USB-C southeast (rot +90 -> opening east)
    "J5":  (186.0, 158.2, 0),
    "U6":  (178.0, 156.0, 0),
    "R3":  (178.0, 153.4, 0),
    "R4":  (173.6, 153.8, 0),
    # indicators
    "LED2": (173.0, 105.5, 0),
    "R5":  (177.0, 105.5, 0),
    "LED3": (176.6, 151.0, 0),
    "R6":  (172.8, 151.0, 0),
}

# (net, layer, priority, outline, min_width_mm)
# outline: rect tuple (x0,y0,x1,y1) OR list of (x,y) polygon points.
ZONES = [
    # full-board GND
    ("GND", "F.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    ("GND", "B.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    ("GND", "In1.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    ("GND", "In2.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    # input trunk pours (F.Cu, prio 1)
    ("VBAT_RAW", "F.Cu", 1, (104.0, 124.4, 112.5, 130.4), 0.5),
    ("VBAT_F", "F.Cu", 1, (114.6, 119.6, 127.4, 128.0), 0.5),
    # VBAT_P: L-shape. Big east rect reaches both bucks' IN pads;
    # west lobe (south of Q1's leads) picks up Q1 source, CBs, D1, R2.
    ("VBAT_P", "F.Cu", 1, [
        (128.0, 108.0), (151.9, 108.0), (151.9, 119.0), (151.6, 119.0),
        (151.6, 136.5), (151.9, 136.5), (151.9, 147.0), (151.6, 147.0),
        (151.6, 154.0), (122.5, 154.0),
        (122.5, 128.2), (128.0, 128.2)], 0.5),
    ("VBAT_P", "In2.Cu", 1, (126.0, 110.0, 153.4, 152.0), 0.5),
    ("5V_A", "In2.Cu", 1, (167.0, 107.0, 189.5, 146.5), 0.5),
    ("5V_C", "In2.Cu", 1, (163.0, 149.5, 189.5, 160.0), 0.5),
    # switch nodes: minimal pours, converter LX pad -> inductor pad 1.
    # South edge clears the EN signal pad row (y=119.0/147.0 + clearance).
    ("SW_A", "F.Cu", 1, (152.3, 113.5, 161.5, 118.85), 0.5),
    ("SW_C", "F.Cu", 1, (152.3, 141.5, 161.5, 146.85), 0.5),
    # 5V_A: east block feeding the three USB-A ports + FB-sense finger
    # west to the divider. SW notch below y=143.5 leaves room for 5V_C.
    ("5V_A", "F.Cu", 1, [
        (164.5, 105.2), (190.5, 105.2), (190.5, 148.2), (172.0, 148.2),
        (172.0, 143.5), (164.5, 143.5), (164.5, 128.8), (153.0, 128.8),
        (153.0, 125.5), (164.5, 125.5)], 0.5),
    # 5V_C: south-east block (USB-C + COUT_C column) + lobe up to L2
    # pad 2 + FB-sense finger west to the divider.
    ("5V_C", "F.Cu", 1, [
        (163.5, 144.5), (168.5, 144.5), (168.5, 148.5), (190.5, 148.5),
        (190.5, 161.0), (162.0, 161.0), (162.0, 156.8), (153.0, 156.8),
        (153.0, 153.5), (162.0, 153.5), (162.0, 148.5), (163.5, 148.5)],
     0.5),
]

# Named rule areas (name, layer, rect) — scoped DRC exemptions that live
# ON THE BOARD (nets.yaml exemptions reference these names).
RULE_AREAS = [
    ("EN_TAP_A", "F.Cu", (152.83, 119.00, 153.43, 121.90)),
    ("EN_TAP_C", "F.Cu", (152.83, 147.00, 153.43, 149.90)),
]

# refdes silk de-collide: ref -> (dx, dy) offset from footprint origin.
# Values live on F.Fab; only these silk refs collided in review renders.
REF_TEXT_OFFSET = {
    "RFA1": (-1.2, 2.0), "RFA2": (1.2, 2.0),
    "RFC1": (-1.2, 2.0), "RFC2": (1.2, 2.0),
    "COUT_C4": (0.0, 2.2), "COUT_C3": (0.0, -2.2),
    "CVCC1": (-3.6, 0.0), "CVCC2": (-3.6, 0.0),
    "CBS1": (2.2, -1.6), "CBS2": (2.2, -1.6),
    "R6": (0.0, 2.0), "R4": (-2.4, 0.0), "R3": (0.0, -1.8),
    "U6": (0.0, 2.4), "LED3": (0.0, -1.8),
    "U1": (0.0, -2.6), "U2": (0.0, -2.6),
}

# Designed vias (net, x, y, dia, drill)
DESIGNED_VIAS = [
    ("GND", 152.23, 120.90, 0.6, 0.3),
    ("GND", 152.23, 148.90, 0.6, 0.3),
    # QFN pad-9 (GND, the thermal pad) is walled in by the VBAT_P and SW
    # pours on F.Cu — in-pad vias bond it to the In1 plane (standard QFN
    # thermal-via practice; 0.55/0.3 fits the 0.555mm pad strip and meets
    # the 0.125 annular floor).
    ("GND", 152.05, 117.00, 0.55, 0.3),
    ("GND", 152.05, 118.00, 0.55, 0.3),
    ("GND", 152.05, 145.00, 0.55, 0.3),
    ("GND", 152.05, 146.00, 0.55, 0.3),
    # FB layer changes
    ("FB_A", 151.45, 121.00, 0.6, 0.3),
    ("FB_A", 154.50, 126.20, 0.6, 0.3),
    ("FB_C", 151.45, 149.00, 0.6, 0.3),
    ("FB_C", 154.45, 154.15, 0.6, 0.3),
    ("BST_A", 149.90, 118.60, 0.6, 0.3),
    ("BST_A", 153.00, 126.35, 0.6, 0.3),
    ("BST_C", 149.90, 146.60, 0.6, 0.3),
    # EN horizontals end in fill pockets the pour cannot reach (designed-
    # copper kill zones seal them): bond them to the VBAT_P In2 patch.
    ("VBAT_P", 152.90, 122.70, 0.6, 0.3),
    ("VBAT_P", 152.90, 150.70, 0.6, 0.3),
    # U6 VBUS pin (pad 5) gets sealed into a pocket by the CC tracks:
    # dedicated via to the 5V_C In2 patch.
    ("5V_C", 180.10, 156.00, 0.6, 0.3),
    # U4/U5 VBUS pins pocket the same way
    ("5V_A", 178.35, 109.00, 0.6, 0.3),
    ("5V_A", 178.35, 126.40, 0.6, 0.3),
    ("5V_A", 178.35, 143.80, 0.6, 0.3),
    # J5 VBUS pads A9/B4 are cut off from the main pour by the CC
    # escapes: two-via In2 feed (3 A share)
    ("5V_C", 183.55, 153.10, 0.6, 0.3),
    ("5V_C", 183.55, 152.35, 0.6, 0.3),
    ("BST_C", 153.84, 152.30, 0.6, 0.3),
]

# Designed tracks (net, layer, width_mm, [(x,y), ...]) — deterministic
# taps that pour-served nets need and no router should improvise:
# EN pins tap VBAT_P around the signal row; CBS bootstrap caps tap their
# SW pour. Widths satisfy the netclass floors (nets.yaml).
DESIGNED_TRACKS = [
    # EN taps: first (vertical) segment lives inside the EN_TAP_A/C rule
    # areas (scoped 0.2mm floor, nets.yaml exemptions) because a 0.5mm
    # track cannot pass the QFN signal row; the horizontal run is 0.5.
    ("VBAT_P", "F.Cu", 0.25, [(153.13, 119.30), (153.13, 121.90)]),
    ("VBAT_P", "F.Cu", 0.5, [(153.13, 121.90), (151.00, 121.90)]),
    ("VBAT_P", "F.Cu", 0.25, [(153.13, 147.30), (153.13, 149.90)]),
    ("VBAT_P", "F.Cu", 0.5, [(153.13, 149.90), (151.00, 149.90)]),
    ("SW_A", "F.Cu", 0.5, [(155.36, 125.30), (155.36, 118.50)]),
    # ILMT (pad 3, tied GND) cannot reach the GND pour between QFN pads:
    # short 0.2 track south out of the row to a via (DESIGNED_VIAS).
    ("GND", "F.Cu", 0.2, [(152.23, 119.30), (152.23, 120.90)]),
    ("GND", "F.Cu", 0.2, [(152.23, 147.30), (152.23, 148.90)]),
    # VCC + FB runs: these pads sit in the QFN signal row between the
    # designed EN/ILMT corridors; no router geometry reaches them.
    # Hand-planned (0.2mm floors): VCC skirts west on F.Cu; FB dives to
    # B.Cu under the EN corridor (In1 GND plane shields it from LX).
    ("VCC_A", "F.Cu", 0.2, [(151.32, 119.30), (151.32, 120.10),
                            (150.40, 120.10), (150.40, 123.60),
                            (151.04, 123.60)]),
    ("VCC_C", "F.Cu", 0.2, [(151.32, 147.30), (151.32, 148.10),
                            (150.40, 148.10), (150.40, 151.60),
                            (151.04, 151.60)]),
    ("FB_A", "F.Cu", 0.2, [(151.78, 119.30), (151.78, 120.60),
                           (151.45, 121.00)]),
    ("FB_A", "B.Cu", 0.2, [(151.45, 121.00), (151.45, 125.45),
                           (154.50, 125.45), (154.50, 126.20)]),
    ("FB_A", "F.Cu", 0.2, [(154.50, 126.20), (155.26, 127.20),
                           (157.24, 127.20)]),
    ("FB_C", "F.Cu", 0.2, [(151.78, 147.30), (151.78, 148.60),
                           (151.45, 149.00)]),
    ("FB_C", "B.Cu", 0.2, [(151.45, 149.00), (151.45, 153.45),
                           (154.45, 153.45), (154.45, 154.15)]),
    ("FB_C", "F.Cu", 0.2, [(154.45, 154.15), (155.26, 155.10),
                           (157.24, 155.10)]),
    # BST runs (BS pin -> bootstrap cap): the QFN row region is saturated
    # with designed corridors, so these are designed too. B.Cu mid-span.
    ("BST_A", "F.Cu", 0.2, [(150.88, 119.30), (150.00, 119.30),
                            (149.90, 118.60)]),
    ("BST_A", "B.Cu", 0.2, [(149.90, 118.60), (149.90, 126.35),
                            (153.00, 126.35)]),
    ("BST_A", "F.Cu", 0.2, [(153.00, 126.35), (153.84, 126.35),
                            (153.84, 125.30)]),
    ("BST_C", "F.Cu", 0.2, [(150.88, 147.30), (150.00, 147.30),
                            (149.90, 146.60)]),
    ("BST_C", "B.Cu", 0.2, [(149.90, 146.60), (149.90, 148.30),
                            (153.84, 148.30), (153.84, 152.30)]),
    ("BST_C", "F.Cu", 0.2, [(153.84, 152.30), (153.84, 153.30)]),
    ("SW_C", "F.Cu", 0.5, [(155.36, 153.30), (155.36, 146.50)]),
    # EN-via bond stubs (EN horizontal -> VBAT_P In2 vias)
    ("VBAT_P", "F.Cu", 0.5, [(152.90, 121.90), (152.90, 122.70)]),
    ("VBAT_P", "F.Cu", 0.5, [(152.90, 149.90), (152.90, 150.70)]),
    ("5V_C", "F.Cu", 0.3, [(179.1375, 156.00), (180.10, 156.00)]),
    ("5V_A", "F.Cu", 0.3, [(177.1375, 109.00), (178.35, 109.00)]),
    ("5V_A", "F.Cu", 0.3, [(177.1375, 126.40), (178.35, 126.40)]),
    ("5V_A", "F.Cu", 0.3, [(177.1375, 143.80), (178.35, 143.80)]),
    ("5V_C", "F.Cu", 0.4, [(183.55, 154.16), (183.55, 152.35)]),
    # J5 BC1.2 DCP short: one track across the tips of the contiguous
    # B6/A7/A6/B7 pad run (ADR 0008)
    ("DCPC", "F.Cu", 0.25, [(185.25, 153.70), (186.75, 153.70)]),
]


def parse_netlist(path):
    """-> (comps {ref: fpid}, nets {net: [(ref,pad)]}). Zero yield = error."""
    tree = _parse_sexpr(_tokenize(path.read_text()))[0]

    def kids(node, tag):
        return [n for n in node if isinstance(n, list) and n and n[0] == tag]

    def val(node, tag):
        k = kids(node, tag)
        return k[0][1] if k else None

    comps, nets = {}, {}
    for comp in kids(kids(tree, "components")[0], "comp"):
        comps[val(comp, "ref")] = (val(comp, "footprint"), val(comp, "value"))
    for net in kids(kids(tree, "nets")[0], "net"):
        name = val(net, "name")
        nodes = [(val(n, "ref"), val(n, "pin")) for n in kids(net, "node")]
        nets[name] = nodes
    if not comps or not nets:
        raise SystemExit("ERROR: netlist parse yielded zero comps/nets")
    return comps, nets


def load_footprint(fpid):
    lib, name = fpid.split(":")
    for base in (PROJ_LIB, STD_LIB):
        libdir = base / f"{lib}.pretty"
        if libdir.exists():
            fp = pcbnew.FootprintLoad(str(libdir), name)
            if fp is not None:
                return fp
    raise SystemExit(f"ERROR: footprint {fpid} NOT FOUND — hard error by contract")


def add_zone(board, netcode, layer_name, prio, rect, min_w):
    z = pcbnew.ZONE(board)
    z.SetLayer(board.GetLayerID(layer_name))
    z.SetNetCode(netcode)
    z.SetAssignedPriority(prio)
    z.SetMinThickness(FromMM(min_w))
    z.SetLocalClearance(FromMM(0.25))
    z.SetThermalReliefGap(FromMM(0.3))
    z.SetThermalReliefSpokeWidth(FromMM(0.5))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if prio >= 1
                       else pcbnew.ZONE_CONNECTION_THERMAL)
    # drop tiny isolated slivers (fully isolated only; islands holding
    # any connection — PTH barrel, via — survive)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_AREA)
    z.SetMinIslandArea(int(5e12))  # nm^2 == 5 mm^2
    if isinstance(rect, tuple):
        x0, y0, x1, y1 = rect
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    else:
        pts = rect
    chain = pcbnew.SHAPE_LINE_CHAIN()
    for x, y in pts:
        chain.Append(VECTOR2I(FromMM(x), FromMM(y)))
    chain.SetClosed(True)
    z.Outline().AddOutline(chain)
    board.Add(z)
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--krt-input", action="store_true",
                    help="emit a TRACK-FREE routing-input board to "
                         "06_build/route/krt_input.kicad_pcb with User.2 "
                         "keepouts over designed corridors + screw heads")
    args = ap.parse_args()
    out_path = BOARD
    if args.krt_input:
        out_path = PROJ / "06_build" / "route" / "krt_input.kicad_pcb"
        out_path.parent.mkdir(parents=True, exist_ok=True)

    comps, nets = parse_netlist(NETLIST)

    board = pcbnew.NewBoard(str(out_path))
    board.SetCopperLayerCount(4)

    # outline
    for (ax, ay, bx, by) in ((X0, Y0, X1, Y0), (X1, Y0, X1, Y1),
                             (X1, Y1, X0, Y1), (X0, Y1, X0, Y0)):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(VECTOR2I(FromMM(ax), FromMM(ay)))
        seg.SetEnd(VECTOR2I(FromMM(bx), FromMM(by)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(FromMM(0.1))
        board.Add(seg)

    # nets
    netinfo = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni

    pad_net = {}   # (ref, pad) -> net name
    for name, nodes in nets.items():
        for ref, pad in nodes:
            pad_net[(ref, str(pad))] = name

    # place parts
    missing_fp, missing_pos = [], []
    for ref, (fpid, value) in sorted(comps.items()):
        if not fpid:
            missing_fp.append(ref)
            continue
        if ref not in FLOORPLAN:
            missing_pos.append(ref)
            continue
        fp = load_footprint(fpid)
        fp.SetReference(ref)
        fp.SetValue(value or "")
        fp.SetFPIDAsString(fpid)   # full lib:name FPID or parity flags it
        x, y, rot = FLOORPLAN[ref]
        fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        fp.SetOrientationDegrees(rot)
        if ref in REF_TEXT_OFFSET:
            dx, dy = REF_TEXT_OFFSET[ref]
            fp.Reference().SetPosition(
                VECTOR2I(FromMM(x + dx), FromMM(y + dy)))
            fp.Reference().SetTextAngleDegrees(0)
        board.Add(fp)
        for pad in fp.Pads():
            pnum = pad.GetNumber()
            if not pnum:
                continue  # NPTH / anchor pads stay unnetted
            key = (ref, pnum)
            if key in pad_net:
                pad.SetNet(netinfo[pad_net[key]])
            # solid zone connections everywhere: kills starved_thermal
            # (reflow SMD + high-current THT; skill drc-discipline)
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
            # a numbered pad with no net entry stays unnetted only if the
            # schematic really has no node for it — schematic parity gates it
    if missing_fp:
        raise SystemExit(f"ERROR: components with no footprint field: {missing_fp}")
    if missing_pos:
        raise SystemExit(f"ERROR: components missing from FLOORPLAN: {missing_pos}")

    # mounting holes: board-only, no BOM/POS
    for i, (x, y) in enumerate(MOUNTING_HOLES, 1):
        fp = load_footprint("MountingHole:MountingHole_3.2mm_M3")
        fp.SetReference(f"H{i}")
        fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        fp.SetAttributes(fp.GetAttributes()
                         | pcbnew.FP_BOARD_ONLY
                         | pcbnew.FP_EXCLUDE_FROM_BOM
                         | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        fp.Reference().SetVisible(False)   # H* refs clipped off-board (review)
        board.Add(fp)

    # zones
    for net, layer, prio, rect, minw in ZONES:
        if net not in netinfo:
            raise SystemExit(f"ERROR: zone net {net} not in netlist")
        add_zone(board, netinfo[net].GetNetCode(), layer, prio, rect, minw)

    # named rule areas (skipped in krt-input mode: not copper, and KRT's
    # parser must see the simplest possible board)
    for name, layer, (ax, ay, bx, by) in ([] if args.krt_input else RULE_AREAS):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetZoneName(name)
        z.SetLayer(board.GetLayerID(layer))
        z.SetDoNotAllowZoneFills(False)
        z.SetDoNotAllowTracks(False)
        z.SetDoNotAllowVias(False)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        chain = pcbnew.SHAPE_LINE_CHAIN()
        for x, y in ((ax, ay), (bx, ay), (bx, by), (ax, by)):
            chain.Append(VECTOR2I(FromMM(x), FromMM(y)))
        chain.SetClosed(True)
        z.Outline().AddOutline(chain)
        board.Add(z)

    # designed tap tracks (NEVER in krt-input mode — KRT mis-parses
    # pcbnew tracks and routes through them)
    for net, layer, width, pts in ([] if args.krt_input else DESIGNED_TRACKS):
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(VECTOR2I(FromMM(ax), FromMM(ay)))
            t.SetEnd(VECTOR2I(FromMM(bx), FromMM(by)))
            t.SetWidth(FromMM(width))
            t.SetLayer(board.GetLayerID(layer))
            t.SetNet(netinfo[net])
            board.Add(t)

    if args.krt_input:
        # keepouts for KRT (--keepout-layer User.2): designed corridors +
        # mounting-hole screw heads
        rects = []
        for dy in (0.0, 28.0):   # rail A, rail C (+28mm mirror)
            rects += [
                (151.70, 116.55 + dy, 152.45, 118.45 + dy),  # in-pad vias
                (152.00, 119.00 + dy, 153.45, 122.20 + dy),  # ILMT+EN vert
                (150.70, 121.60 + dy, 153.45, 122.20 + dy),  # EN horizontal
                (154.80, 118.20 + dy, 155.80, 125.80 + dy),  # CBS SW tap
                (151.07, 119.00 + dy, 151.57, 120.35 + dy),  # VCC stub
                (150.15, 119.85 + dy, 150.65, 123.35 + dy),  # VCC vertical
                (150.40, 122.85 + dy, 151.60, 123.35 + dy),  # VCC pad run
                (151.00, 118.95 + dy, 152.20, 121.55 + dy),  # FB stub + via
                (151.05, 120.65 + dy, 151.85, 125.75 + dy),  # FB B.Cu vert
            ]
        # FB B.Cu horizontals + via-up + divider segments (rail-specific y)
        rects += [
            (151.30, 125.15, 154.90, 125.75),
            (154.10, 125.15, 154.90, 126.70),
            (154.20, 125.90, 155.60, 127.50),
            (155.00, 126.90, 157.50, 127.50),
            (151.30, 153.15, 154.95, 153.75),
            (154.20, 153.60, 155.00, 154.40),
            (154.20, 153.60, 155.60, 155.10),
            (155.00, 154.80, 157.50, 155.40),
            # SW pours: an F.Cu route across them slices them into islands
            (152.10, 113.30, 161.70, 119.05),
            (152.10, 141.30, 161.70, 147.05),
            # BST designed corridors
            (149.35, 118.05, 151.00, 119.60),
            (149.60, 118.50, 150.20, 126.70),
            (149.60, 126.10, 154.10, 126.95),
            (152.60, 125.95, 154.25, 126.80),
            (153.50, 125.00, 154.20, 126.80),
            (149.35, 146.05, 151.00, 147.60),
            (149.60, 146.50, 150.20, 148.70),
            (149.60, 147.90, 154.30, 148.70),
            (153.45, 147.90, 154.25, 152.75),
            (153.40, 151.85, 154.30, 153.45),
            # VBUS rescue corridors (vias + stubs above)
            (176.90, 108.50, 179.00, 109.50),
            (176.90, 125.90, 179.00, 126.90),
            (176.90, 143.30, 179.00, 144.30),
            (179.00, 155.50, 180.60, 156.50),
            (182.70, 151.75, 184.40, 153.80),
            (184.90, 153.40, 187.10, 154.00),   # DCPC short corridor
        ]
        rects += [(x - 3.35, y - 3.35, x + 3.35, y + 3.35)
                  for x, y in MOUNTING_HOLES]
        for (ax, ay, bx, by) in rects:
            sh = pcbnew.PCB_SHAPE(board)
            sh.SetShape(pcbnew.SHAPE_T_POLY)
            pts = pcbnew.VECTOR_VECTOR2I(
                [VECTOR2I(FromMM(ax), FromMM(ay)),
                 VECTOR2I(FromMM(bx), FromMM(ay)),
                 VECTOR2I(FromMM(bx), FromMM(by)),
                 VECTOR2I(FromMM(ax), FromMM(by))])
            sh.SetPolyPoints(pts)
            sh.SetLayer(board.GetLayerID("User.2"))
            sh.SetFilled(True)
            board.Add(sh)
        board.Save(str(out_path))
        print(f"KRT INPUT: wrote {out_path} (track-free, unfilled, "
              f"{len(rects)} keepouts)")
        return

    for net, x, y, dia, drill in DESIGNED_VIAS:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(VECTOR2I(FromMM(x), FromMM(y)))
        v.SetWidth(FromMM(dia))
        v.SetDrill(FromMM(drill))
        v.SetNet(netinfo[net])
        board.Add(v)

    board.Save(str(BOARD))

    # fp-lib-table so the project resolves the vendored lib
    (KICAD / "fp-lib-table").write_text(
        '(fp_lib_table\n  (version 7)\n'
        '  (lib (name "xt60_usb_supply")(type "KiCad")'
        '(uri "${KIPRJMOD}/../03_src/lib/xt60_usb_supply.pretty")'
        '(options "")(descr "project vendored"))\n)\n')

    n_parts = len(board.GetFootprints())
    print(f"BOARD: wrote {BOARD.name}: {n_parts} footprints, "
          f"{len(nets)} nets, {len(ZONES)} zones, outline "
          f"{X1-X0:.0f}x{Y1-Y0:.0f}mm")


if __name__ == "__main__":
    main()
