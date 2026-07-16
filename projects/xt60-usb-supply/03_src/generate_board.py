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

MOUNTING_HOLES = [(104.5, 104.5), (104.5, 157.5), (166.0, 104.5), (166.0, 157.5)]

# ref: (x, y, rot_deg). rot is CCW in KiCad UI convention.
FLOORPLAN = {
    # input chain, west
    "J1":  (101.5, 131.0, 90),    # XT60, mates west (verify render)
    "F1":  (114.0, 131.0, 0),
    "Q1":  (124.0, 131.0, 90),
    "D1":  (133.0, 148.0, 0),
    "CB1": (136.0, 122.0, 90),
    "CB2": (136.0, 140.0, 90),
    "LED1": (106.0, 145.0, 90),
    "R2":  (106.0, 150.0, 90),
    # buck A (north center): LX east, IN west after 180
    "U1":  (152.0, 118.0, 180),
    "CIN_A1": (147.0, 112.0, 0),
    "CIN_A2": (147.0, 124.0, 0),
    "CVCC_A": (146.5, 128.5, 0),
    "CBS_A": (158.0, 112.5, 0),
    "RFA1": (150.0, 132.0, 0),
    "RFA2": (155.0, 132.0, 0),
    "L1":  (163.0, 118.0, 0),
    "COUT_A1": (170.5, 110.0, 0),
    "COUT_A2": (170.5, 114.5, 0),
    "COUT_A3": (170.5, 121.5, 0),
    "COUT_A4": (170.5, 126.0, 0),
    # buck C (south center)
    "U2":  (152.0, 146.0, 180),
    "CIN_C1": (147.0, 140.0, 0),
    "CIN_C2": (147.0, 152.0, 0),
    "CVCC_C": (146.5, 156.5, 0),
    "CBS_C": (158.0, 140.5, 0),
    "RFC1": (150.0, 158.0, 0),
    "RFC2": (155.0, 158.0, 0),
    "L2":  (163.0, 146.0, 0),
    "COUT_C1": (170.5, 138.0, 0),
    "COUT_C2": (170.5, 142.5, 0),
    "COUT_C3": (170.5, 149.5, 0),
    "COUT_C4": (170.5, 154.0, 0),
    # USB-A east edge (mate east)
    "J2":  (188.0, 112.0, -90),
    "J3":  (188.0, 128.0, -90),
    "J4":  (188.0, 144.0, -90),
    "U3":  (178.0, 106.5, 0),
    "U4":  (178.0, 122.5, 0),
    "U5":  (178.0, 138.5, 0),
    # USB-C southeast (mate east)
    "J5":  (188.5, 157.0, -90),
    "U6":  (177.0, 152.0, 0),
    "R3":  (181.0, 148.0, 0),
    "R4":  (181.0, 155.5, 90),
    # indicators
    "LED2": (176.0, 104.5, 0),
    "R5":  (181.0, 104.5, 0),
    "LED3": (172.0, 158.5, 0),
    "R6":  (172.0, 155.0, 0),
}

# (net, layer, priority, rect(x0,y0,x1,y1), min_width_mm)
ZONES = [
    # full-board GND
    ("GND", "F.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    ("GND", "B.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    ("GND", "In1.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    ("GND", "In2.Cu", 0, (X0, Y0, X1, Y1), 0.25),
    # input trunk pours (F.Cu, prio 1)
    ("VBAT_RAW", "F.Cu", 1, (103.0, 126.0, 115.5, 136.0), 0.5),
    ("VBAT_F", "F.Cu", 1, (112.5, 126.0, 125.5, 136.0), 0.5),
    ("VBAT_P", "F.Cu", 1, (122.5, 108.0, 148.5, 154.0), 0.5),
    # VBAT_P reinforcement on In2 under the input block
    ("VBAT_P", "In2.Cu", 1, (124.0, 108.0, 148.0, 154.0), 0.5),
    # switch nodes: minimal pours U LX -> L pad 1
    ("SW_A", "F.Cu", 1, (152.0, 113.5, 161.0, 122.5), 0.5),
    ("SW_C", "F.Cu", 1, (152.0, 141.5, 161.0, 150.5), 0.5),
    # 5V rails to the ports
    ("5V_A", "F.Cu", 1, (166.0, 106.0, 190.5, 146.5), 0.5),
    ("5V_A", "In2.Cu", 1, (166.0, 106.0, 189.0, 146.0), 0.5),
    ("5V_C", "F.Cu", 1, (166.0, 148.5, 190.5, 160.5), 0.5),
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
        comps[val(comp, "ref")] = val(comp, "footprint")
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
    x0, y0, x1, y1 = rect
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
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
    for ref, fpid in sorted(comps.items()):
        if not fpid:
            missing_fp.append(ref)
            continue
        if ref not in FLOORPLAN:
            missing_pos.append(ref)
            continue
        fp = load_footprint(fpid)
        fp.SetReference(ref)
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
