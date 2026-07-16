#!/usr/bin/env python3
"""Generate 04_kicad/usb_power_3s.kicad_pcb from the netlist + floorplan.

90x60mm 4-layer. Placement: XT60+fuse+FE west, buck A north-center, buck B
south-center, TPS2557 bank east-center, USB-C north-east edge, 3x USB-A
east edge. Mounting holes placed CLEAR of connector bodies (audited).
Creates GND pours (F/In1/B), In2 power planes, F.Cu power pour patches for
SW nodes and rail necks, and named rule areas SW_TAP_A/B for the dru
exemptions. Missing footprint = HARD ERROR (never a warning).

Run with KiCad-bundled python: /usr/bin/python3 03_src/generate_board.py
Then: python3 03_src/generate_rules.py  (netclasses+dru), and route.
"""
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
K = HERE.parent / "04_kicad"
NETLIST = HERE.parent / "06_build" / "netlists" / "usb_power_3s.net"
PCB = K / "usb_power_3s.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "usb_power_3s.pretty")

X0, Y0, W, H = 50.0, 50.0, 100.0, 60.0

# ---------------------------------------------------------------- netlist
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


def write_lib_table(libs):
    rows = ['(fp_lib_table', '  (version 7)',
            '  (lib (name "usb_power_3s")(type "KiCad")(uri "${KIPRJMOD}/../03_src/lib/usb_power_3s.pretty")(options "")(descr "project footprints"))']
    for lib in sorted(libs - {"usb_power_3s"}):
        rows.append(f'  (lib (name "{lib}")(type "KiCad")(uri "{STD}/{lib}.pretty")(options "")(descr "system"))')
    rows.append(')')
    (K / "fp-lib-table").write_text("\n".join(rows) + "\n")


def load_fp(fpid):
    lib, name = fpid.split(":")
    root = PROJ if lib == "usb_power_3s" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
# ANCHOR: ref -> (x, y, rot). Connectors on edges; power flow west->east.
ANCHOR = {
    # west: input (XT60 opening overhangs W edge; fuse holder vertical)
    "J1": (57.6, 80.0, 90),
    "F1": (66.0, 66.0, 90),
    "D1": (56.0, 95.5, 0), "C15": (56.0, 99.0, 0),
    # front-end
    "Q1": (76.0, 74.0, 0), "Q2": (76.0, 84.0, 0),
    "U1": (68.0, 79.0, 0),
    "C1": (82.0, 78.0, 90), "C2": (82.0, 83.0, 90), "C3": (82.0, 88.0, 90),
    "R1": (63.0, 91.5, 0), "R2": (67.0, 91.5, 0), "R3": (71.0, 91.5, 0),
    "C16": (75.0, 91.5, 0),
    "CE1": (88.0, 76.5, 0),
    # buck A (north): controller west of FETs, inductor east, out bank further east
    "U2": (85.0, 58.0, 0),
    "QA1": (93.5, 55.0, 0), "QA2": (93.5, 62.0, 0),
    "LA1": (103.0, 58.0, 0),
    "CA51": (90.5, 68.5, 90), "CA52": (95.5, 68.5, 90), "CA53": (100.5, 68.5, 90),
    "CA61": (114.5, 54.0, 90), "CA62": (118.5, 54.0, 90),
    "CA63": (114.5, 60.0, 90), "CA64": (118.5, 60.0, 90),
    "CA7": (112.0, 68.3, 180),
    "R4": (77.5, 52.5, 0), "R5": (77.5, 55.0, 0),
    "R21": (77.5, 61.0, 0), "R33": (77.5, 63.5, 0), "R34": (77.5, 66.0, 0),
    # buck B (south)
    "U3": (85.0, 98.0, 0),
    "QB1": (93.5, 95.0, 0), "QB2": (93.5, 102.0, 0),
    "LB1": (103.0, 98.0, 0),
    "CB51": (90.5, 88.5, 90), "CB52": (95.5, 88.5, 90), "CB53": (100.5, 88.5, 90),
    "CB61": (114.5, 95.0, 90), "CB62": (118.5, 95.0, 90),
    "CB63": (114.5, 100.5, 90), "CB64": (118.5, 100.5, 90),
    "CB7": (117.0, 88.7, 0),
    # TPS2557 bank (west of jack bodies at x>=133) + RC column
    "U4": (127.0, 66.0, 0), "R16": (122.0, 63.5, 0), "C20": (122.0, 66.0, 0), "C30": (127.5, 71.5, 0),
    "U5": (127.0, 83.5, 0), "R17": (122.0, 81.0, 0), "C21": (122.0, 83.5, 0), "C31": (127.5, 89.0, 0),
    "U6": (127.0, 101.0, 0), "R18": (122.0, 98.5, 0), "C22": (122.0, 101.0, 0), "C32": (127.5, 106.5, 0),
    # USB-A jacks on E edge, rows sized to 14.4mm bodies
    "J2": (144.5, 66.0, 0), "J3": (144.5, 83.5, 0), "J4": (144.5, 101.0, 0),
    # USB-C on N edge (top-mount, opening north)
    "J5": (134.0, 53.2, 180),
    "R19": (124.5, 60.5, 0), "R20": (124.5, 63.0, 0),
    "C33": (119.5, 67.5, 0), "C34": (121.9, 61.9, 0),
    "D3": (118.8, 73.1, 0),
    # rail TVS + LEDs
    "D2": (106.0, 106.0, 0),
    "R22": (133.8, 92.2, 0), "D4": (137.5, 92.2, 0),
    "R23": (133.8, 74.8, 0), "D5": (137.5, 74.8, 0),
}
ZONE_OF = {
    "A": (60.0, 52.5, 3, 4.5, 2.8),
    "B": (60.0, 96.0, 3, 4.5, 2.8),
}
GRID_REFS = {
    "A": ["RA1", "CA1", "CA2", "CA3", "RA2", "CA4",
          "RA3", "RA4", "RA5", "CA8", "CA9", "CA10", "RA6"],
    "B": ["RB1", "CB1", "CB2", "CB3", "RB2", "CB4",
          "RB3", "RB4", "RB5", "CB8", "CB9", "CB10", "RB6"],
}
MOUNT = [(55.0, 55.0), (55.0, 105.0), (146.0, 55.0), (113.0, 106.5)]


TRIM_VARIANTS = {  # variant name -> (source lib, source name, anchor ref for clip frame)
    "XT60PW-M_EdgeTrim": ("Connector_AMASS", "AMASS_XT60PW-M_1x02_P7.20mm_Horizontal", "J1"),
    "FuseHolder_ATO_FLR_EdgeTrim": ("Fuse", "FuseHolder_Blade_ATO_Littelfuse_FLR_178.6165", "F1"),
}


def vendor_trimmed():
    """Create the edge-trimmed footprint variants in the project lib.
    One SUBPROCESS per variant: PCB_IO save corrupts every other live SWIG
    footprint wrapper in the process (found 2026-07-16)."""
    import subprocess
    for name, (lib, src, ref) in TRIM_VARIANTS.items():
        if (Path(PROJ) / f"{name}.kicad_mod").exists():
            continue
        x, y, rot = ANCHOR[ref]
        code = f"""
import pcbnew
fp = pcbnew.FootprintLoad("{STD}/{lib}.pretty", "{src}")
fp.SetPosition(pcbnew.VECTOR2I_MM({x}, {y}))
fp.SetOrientationDegrees({rot})
for it in list(fp.GraphicalItems()):
    if it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
        bx = it.GetBoundingBox()
        if (bx.GetLeft() < {int((X0+0.15)*1e6)} or bx.GetRight() > {int((X0+W-0.15)*1e6)}
                or bx.GetTop() < {int((Y0+0.15)*1e6)} or bx.GetBottom() > {int((Y0+H-0.15)*1e6)}):
            fp.Remove(it)
fp.SetOrientationDegrees(0)
fp.SetPosition(pcbnew.VECTOR2I(0, 0))
fp.SetFPID(pcbnew.LIB_ID("usb_power_3s", "{name}"))
pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave("{PROJ}", fp)
"""
        subprocess.run([sys.executable, "-c", code], check=True,
                       capture_output=True)


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
    vendor_trimmed()
    write_lib_table({fp.split(":")[0] for fp, _v in comps.values() if fp} | {"MountingHole"})
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)

    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    # outline
    for (xa, ya, xb, yb) in [(X0, Y0, X0 + W, Y0), (X0 + W, Y0, X0 + W, Y0 + H),
                             (X0 + W, Y0 + H, X0, Y0 + H), (X0, Y0 + H, X0, Y0)]:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        seg.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.15))
        board.Add(seg)

    # mounting holes (positions audited against connector bodies)
    for i, (hx, hy) in enumerate(MOUNT, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty", "MountingHole_3.2mm_M3")
        mh.SetReference(f"H{i}")
        mh.SetAttributes(mh.GetAttributes() | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        mh.SetPosition(pcbnew.VECTOR2I_MM(hx, hy))
        board.Add(mh)

    gridpos = {}
    for zone, refs in GRID_REFS.items():
        gx, gy, cols, dx, dy = ZONE_OF[zone]
        for i, ref in enumerate(refs):
            gridpos[ref] = (gx + (i % cols) * dx, gy + (i // cols) * dy, 0)

    placed = 0
    for ref, (fpid, val) in sorted(comps.items()):
        if not fpid:
            raise RuntimeError(f"{ref} has no footprint in the netlist - "
                               f"fix generate_schematic.py footprint maps")
        fp = load_fp(fpid)
        fp.SetReference(ref)
        fp.SetValue(val)
        if ref in ANCHOR:
            x, y, rot = ANCHOR[ref]
        elif ref in gridpos:
            x, y, rot = gridpos[ref]
        else:
            raise RuntimeError(f"{ref} has no anchor and no grid slot - floorplan gap")
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        if rot:
            fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(netmap[pad_net[key]])
        board.Add(fp)
        placed += 1


    # ---------------------------------------------------- legalize passives
    # Big parts stay anchored; small parts (R/C 0402..1206, diodes, LEDs)
    # ring-search to the nearest clear spot if they overlap anything.
    import math
    KEEP = {r for r in ANCHOR if r[0] in "JQLU"} | {"CE1", "CA7", "CB7", "F1"} | \
           {f"C{s}{n}" for s in "AB" for n in ("51", "52", "53", "61", "62", "63", "64")}
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
        if not (X0 + 1 + w2 < x < X0 + W - 1 - w2 and Y0 + 1 + h2 < y < Y0 + H - 1 - h2):
            return False
        for hx, hy in holes:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < 3.4:
                return False
        for r2, f2 in fps.items():
            if r2 == skip or r2.startswith("H"):
                continue
            L, T, R, B = bbox(f2)
            if not (x + w2 + 0.4 <= L or R <= x - w2 - 0.4 or
                    y + h2 + 0.4 <= T or B <= y - h2 - 0.4):
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

    # design rules floor (JLC 4L)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = pcbnew.FromMM(0.127)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.15)
    ds.m_MinClearance = int(0.10e6)
    ds.m_ViasMinAnnularWidth = int(0.045e6)
    ds.m_HoleClearance = int(0.15e6)
    ds.m_HoleToHoleMin = int(0.15e6)
    ds.m_CopperEdgeClearance = int(0.10e6)
    ds.m_ViasMinSize = pcbnew.FromMM(0.25)  # KRT advanced tier emits 0.25/0.15 (JLC advanced option REQUIRED)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.15)

    # ------------------------------------------------------------- zones
    def add_zone(net, layer, pts, prio, minw=0.25, clr=0.25, name=None):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        if net:
            z.SetNet(netmap[net])
        z.SetAssignedPriority(prio)
        z.SetMinThickness(pcbnew.FromMM(minw))
        z.SetLocalClearance(pcbnew.FromMM(clr))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        if name:
            z.SetZoneName(name)
        z.Outline().NewOutline()
        for x, y in pts:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)
        return z

    FULL = [(X0, Y0), (X0 + W, Y0), (X0 + W, Y0 + H), (X0, Y0 + H)]
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.In1_Cu):
        add_zone("GND", lay, FULL, 0)
    # In2 power planes
    for _z in [add_zone("VSW",  pcbnew.In2_Cu, [(72.5, 52), (99, 52), (99, 108), (64, 108), (64, 72.5), (72.5, 72.5)], 2, minw=0.3),
               add_zone("VBATT_F", pcbnew.In2_Cu, [(60, 50.8), (72, 50.8), (72, 71.8), (63.5, 71.8), (63.5, 101.5), (52.3, 101.5), (52.3, 71.8), (60, 71.8)], 2, minw=0.3),
               add_zone("5V_C", pcbnew.In2_Cu, [(99, 50.5), (148, 50.5), (148, 63), (99, 63)], 2, minw=0.3),
               add_zone("5V_A", pcbnew.In2_Cu, [(99.6, 63.5), (148, 63.5), (148, 108), (99, 108), (99, 64.2)], 2, minw=0.3)]:
        _z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    # F.Cu power pours: solid connect for power pads
    def power_patch(net, pts, name=None, prio=3, layer=pcbnew.F_Cu):
        z = add_zone(net, layer, pts, prio, minw=0.3, name=name)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    power_patch("VBATT_RAW", [(52, 63), (69, 63), (69, 86), (52, 86)])
    power_patch("VBATT_F", [(60.5, 67.8), (80, 67.8), (80, 79), (64, 79), (64, 101),
                            (52.5, 101), (52.5, 93.4), (60.5, 93.4)], prio=4)
    # VBATT_RAW second path on B.Cu (J1 blade -> F1 input clips); F.Cu band alone is ~6A
    power_patch("VBATT_RAW", [(52.8, 62.8), (69.5, 62.8), (69.5, 66.9), (56.5, 66.9),
                              (56.5, 86), (52.8, 86)], layer=pcbnew.B_Cu)
    power_patch("FE_MID", [(75.45, 70), (79, 70), (79, 92.2), (73.4, 92.2), (73.4, 89.4), (75.45, 89.4)])
    power_patch("VSW", [(73.7, 80.6), (75.2, 80.6), (75.2, 89.0), (73.7, 89.0)])  # Q2 sources -> In2 via stitch
    power_patch("VSW", [(79.5, 69.3), (101.3, 69.3), (101.3, 70.9), (93, 70.9),
                        (93, 89.1), (101.3, 89.1), (101.3, 90.7), (79.5, 90.7)])  # FE out + CA5x/CB5x VSW pad rows
    power_patch("VSW", [(76, 51.5), (93.3, 51.5), (93.3, 53.2), (88, 53.2), (88, 55.4), (76, 55.4)])  # R4/R5 taps strip
    power_patch("VSW", [(93.5, 51.7), (97.1, 51.7), (97.1, 56.6), (93.5, 56.6)])  # QA1 drain -> In2 vias
    power_patch("VSW", [(93.5, 91.7), (97.1, 91.7), (97.1, 96.6), (93.5, 96.6)])  # QB1 drain -> In2 vias
    power_patch("SW_A", [(91.3, 53.6), (93.2, 53.6), (93.2, 56.9), (97.4, 56.9),
                         (97.4, 53.6), (99.5, 53.6), (99.5, 63.5), (91.3, 63.5)])
    power_patch("SW_A", [(91.4, 53.4), (93.0, 53.4), (93.0, 58.6), (91.4, 58.6)], layer=pcbnew.B_Cu)  # bridge over HO_A slice
    power_patch("SW_B", [(91.3, 93.6), (93.2, 93.6), (93.2, 96.9), (97.4, 96.9),
                         (97.4, 93.6), (99.5, 93.6), (99.5, 103.5), (91.3, 103.5)])
    power_patch("SW_B", [(91.4, 93.4), (93.0, 93.4), (93.0, 98.6), (91.4, 98.6)], layer=pcbnew.B_Cu)  # bridge over HO_B slice
    power_patch("FE_MID", [(75.6, 72.9), (79.0, 72.9), (79.0, 86.2), (75.6, 86.2)], layer=pcbnew.B_Cu)  # B bond: gate/cap traces shred the F pour into 4 islands
    power_patch("5V_C", [(107, 51.5), (139, 51.5), (139, 64.5), (119.3, 64.5),
                         (119.3, 68.9), (110.6, 68.9), (110.6, 64.5), (107, 64.5)])  # lobe: CA7 + and C33
    power_patch("5V_A", [(107, 92.5), (112, 92.5), (112, 87.5), (121, 87.5), (121, 92.5), (131.5, 92.5), (131.5, 108), (107, 108)])  # lobe: CB7
    power_patch("5V_A", [(120.4, 63.9), (126.8, 63.9), (126.8, 68.2), (120.4, 68.2)])  # U4 IN + C20
    power_patch("5V_A", [(120.4, 81.4), (126.8, 81.4), (126.8, 85.7), (120.4, 85.7)])  # U5 IN + C21
    # rule areas for the dru tap exemptions (over the controller side)
    for name, x0, y0, x1, y1 in (("SW_TAP_A", 57, 50.4, 92.9, 70), ("SW_TAP_B", 57, 91, 92.9, 109.6)):
        ra = pcbnew.ZONE(board)
        ra.SetIsRuleArea(True)
        ra.SetZoneName(name)
        for setter in ("SetDoNotAllowTracks", "SetDoNotAllowVias", "SetDoNotAllowZoneFills",
                       "SetDoNotAllowPads", "SetDoNotAllowFootprints"):
            getattr(ra, setter)(False)
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.F_Cu)
        ls.AddLayer(pcbnew.B_Cu)
        ra.SetLayerSet(ls)
        ra.Outline().NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ra.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(ra)

    for fp in board.GetFootprints():
        ref = fp.Reference()
        ref.SetLayer(pcbnew.B_Fab if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Fab)
        ref.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
        ref.SetTextThickness(int(0.08e6))
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(MOUNT)} holes; zones + rule areas; saved {PCB.name}")


if __name__ == "__main__":
    main()
