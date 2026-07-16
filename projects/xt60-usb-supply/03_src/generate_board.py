#!/usr/bin/env python3
"""Generate 04_kicad/xt60-usb-supply.kicad_pcb from the exported netlist +
the floorplan below. Places footprints, binds pad nets, draws the outline,
adds mounting holes and all copper zones (GND planes + priority-1 power
pours). Produces a TRACK-FREE, UNFILLED board — routing is a later stage.

Run with /usr/bin/python3 (pcbnew). Never writes .kicad_pro (generate_rules
merges it afterwards; rules run LAST in the chain).

Hard rules honored: missing footprint = raise; zero-yield parse = raise.
"""
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
    "CVCC1": (152.0, 122.8, 0),
    "CBS1": (154.3, 124.5, 0),
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
    "CVCC2": (152.0, 150.8, 0),
    "CBS2": (154.3, 152.5, 0),
    "RFC1": (154.5, 154.4, 0),
    "RFC2": (158.0, 154.4, 0),
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
        (128.0, 108.0), (151.6, 108.0), (151.6, 154.0), (122.5, 154.0),
        (122.5, 128.2), (128.0, 128.2)], 0.5),
    # switch nodes: minimal pours, converter LX pad -> inductor pad 1.
    # South edge clears the EN signal pad row (y=119.0/147.0 + clearance).
    ("SW_A", "F.Cu", 1, (152.3, 113.5, 161.5, 118.85), 0.5),
    ("SW_C", "F.Cu", 1, (152.3, 141.5, 161.5, 146.85), 0.5),
    # 5V_A: east block feeding the three USB-A ports + FB-sense finger
    # west to the divider. SW notch below y=143.5 leaves room for 5V_C.
    ("5V_A", "F.Cu", 1, [
        (164.5, 106.0), (190.5, 106.0), (190.5, 148.2), (172.0, 148.2),
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

# Designed tracks (net, layer, width_mm, [(x,y), ...]) — deterministic
# taps that pour-served nets need and no router should improvise:
# EN pins tap VBAT_P around the signal row; CBS bootstrap caps tap their
# SW pour. Widths satisfy the netclass floors (nets.yaml).
DESIGNED_TRACKS = [
    # EN taps: first (vertical) segment lives inside the EN_TAP_A/C rule
    # areas (scoped 0.2mm floor, nets.yaml exemptions) because a 0.5mm
    # track cannot pass the QFN signal row; the horizontal run is 0.5.
    ("VBAT_P", "F.Cu", 0.25, [(153.13, 119.30), (153.13, 121.60)]),
    ("VBAT_P", "F.Cu", 0.5, [(153.13, 121.60), (151.00, 121.60)]),
    ("VBAT_P", "F.Cu", 0.25, [(153.13, 147.30), (153.13, 149.60)]),
    ("VBAT_P", "F.Cu", 0.5, [(153.13, 149.60), (151.00, 149.60)]),
    ("SW_A", "F.Cu", 0.5, [(155.06, 124.50), (155.06, 118.50)]),
    ("SW_C", "F.Cu", 0.5, [(155.06, 152.50), (155.06, 146.50)]),
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
    comps, nets = parse_netlist(NETLIST)

    board = pcbnew.NewBoard(str(BOARD))
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
        board.Add(fp)

    # zones
    for net, layer, prio, rect, minw in ZONES:
        if net not in netinfo:
            raise SystemExit(f"ERROR: zone net {net} not in netlist")
        add_zone(board, netinfo[net].GetNetCode(), layer, prio, rect, minw)

    # named rule areas
    for name, layer, (ax, ay, bx, by) in RULE_AREAS:
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

    # designed tap tracks
    for net, layer, width, pts in DESIGNED_TRACKS:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(VECTOR2I(FromMM(ax), FromMM(ay)))
            t.SetEnd(VECTOR2I(FromMM(bx), FromMM(by)))
            t.SetWidth(FromMM(width))
            t.SetLayer(board.GetLayerID(layer))
            t.SetNet(netinfo[net])
            board.Add(t)

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
