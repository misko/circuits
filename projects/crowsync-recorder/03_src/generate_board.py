#!/usr/bin/env python3
"""Generate 04_kicad/crowsync_recorder.kicad_pcb from the netlist + floorplan.

65x42mm 4-layer. Placement: USB-C west edge (opening overhangs W), codec
center-west with USB pins NW / analog pins SW, crystal east of codec,
low-noise analog region east/south (preamp, bias, dividers), JST GH mic +
PPS on the east edge (opening east), LDO south-west. 4x M2.5 at 4mm corner
insets. Zones: full GND on F/In1/B (In1 = THE continuous plane, ADR-0004),
In2 power islands VBUS_5V (west) + 3V3A (east). Missing footprint = HARD
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
NETLIST = HERE.parent / "06_build" / "netlists" / "crowsync_recorder.net"
PCB = K / "crowsync_recorder.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "crowsync_recorder.pretty")

X0, Y0, W, H = 50.0, 50.0, 65.0, 42.0


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
            '  (lib (name "crowsync_recorder")(type "KiCad")(uri "${KIPRJMOD}/../03_src/lib/crowsync_recorder.pretty")(options "")(descr "project footprints"))']
    for lib in sorted(libs - {"crowsync_recorder"}):
        rows.append(f'  (lib (name "{lib}")(type "KiCad")(uri "{STD}/{lib}.pretty")(options "")(descr "system"))')
    rows.append(')')
    (K / "fp-lib-table").write_text("\n".join(rows) + "\n")


def load_fp(fpid):
    lib, name = fpid.split(":")
    root = PROJ if lib == "crowsync_recorder" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
# ref -> (x, y, rot). rot sense: opening S at 0, E at 90, N at 180, W at 270
ANCHOR = {
    # west: USB-C (opening overhangs W edge), ESD, CC pulldowns, bulk
    "J1": (53.2, 71.0, 270),
    "D1": (60.5, 64.0, 0),
    "R4": (58.5, 79.5, 0), "R5": (58.5, 82.0, 0),
    "C12": (58.5, 61.0, 90), "C13": (61.5, 61.0, 90),
    # power LED (south-west, edge-visible)
    "R18": (58.5, 85.0, 0), "D4": (58.5, 88.0, 0),
    # LDO
    "U3": (67.5, 84.5, 0), "C14": (62.5, 84.0, 90), "C15": (72.0, 84.0, 90),
    # codec + USB series/pullup + VBUS filter
    "U1": (77.0, 67.5, 0),
    "R1": (68.5, 60.5, 0), "R2": (68.5, 63.0, 0), "R3": (68.5, 58.0, 0),
    "R7": (67.0, 55.0, 0), "C11": (71.5, 55.0, 0),
    # codec decouplers: west column (VCCCI pin 10 y~69.2)
    "C1": (71.5, 65.5, 90), "C2": (72.5, 76.0, 0),
    # east column (VDDI 27, VCCXI 23, VCCP2 19, VCCP1 17)
    "C3": (83.0, 59.5, 0), "C4": (83.5, 65.0, 90),
    "C7": (83.0, 69.5, 90), "C8": (86.0, 72.5, 0),
    # suspend LED (north of crystal, clear of analog)
    "R17": (83.0, 56.5, 0), "D3": (87.5, 56.5, 0),
    # crystal cluster east of codec pins 20/21
    "Y1": (89.0, 66.5, 0), "C5": (89.0, 62.5, 0), "C6": (89.0, 70.0, 0),
    "R6": (93.0, 66.5, 90),
    # analog east: preamp + networks
    "U2": (97.0, 79.5, 0),
    "R11": (92.0, 79.0, 90), "R12": (92.0, 84.0, 90), "C20": (95.0, 86.5, 0),
    "R13": (91.0, 74.5, 0), "C21": (87.0, 76.5, 0), "C9": (80.5, 76.0, 0),
    "R10": (101.5, 84.0, 90), "C19": (103.0, 79.0, 90), "C16": (101.5, 76.0, 0),
    # mic entry (east edge north) + bias
    "J2": (111.3, 62.0, 90),
    "D2": (104.5, 70.5, 0),
    "FB1": (95.5, 60.0, 0), "C17": (95.5, 63.0, 0), "C18": (95.5, 66.0, 0),
    "R8": (100.5, 63.0, 0), "R9": (105.5, 65.5, 0),
    # PPS entry (east edge south) + divider
    "J3": (111.3, 80.0, 90),
    "R14": (105.0, 84.0, 0), "R15": (105.0, 86.5, 0), "R16": (108.5, 86.5, 90),
    "C10": (101.0, 88.0, 0),
}
MOUNT = [(54.0, 54.0), (111.0, 54.0), (54.0, 88.0), (111.0, 88.0)]


def main():
    comps, pad_net, nets = parse_netlist(NETLIST)
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

    # mounting holes: M2.5 (2.7mm drill), clear of connector bodies (audited)
    for i, (hx, hy) in enumerate(MOUNT, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty", "MountingHole_2.7mm_M2.5")
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

    # netlist->board completeness: every netted pad landed
    board_pads = {(f.GetReference(), p.GetNumber())
                  for f in board.GetFootprints() for p in f.Pads()}
    missing = [k for k in pad_net if k not in board_pads]
    if missing:
        raise RuntimeError(f"netlist pads missing on board: {missing}")

    # connector orientation asserts (opening = body-centroid minus pad-centroid)
    for ref, want in (("J1", (-1, 0)), ("J2", (1, 0)), ("J3", (1, 0))):
        f = board.FindFootprintByReference(ref)
        bb = f.GetBoundingBox(False, False)
        bcx, bcy = bb.Centre().x, bb.Centre().y
        pads = [p.GetPosition() for p in f.Pads()]
        pcx = sum(p.x for p in pads) / len(pads)
        pcy = sum(p.y for p in pads) / len(pads)
        vx, vy = bcx - pcx, bcy - pcy
        dot = vx * want[0] + vy * want[1]
        if dot <= 0:
            raise RuntimeError(f"{ref} opening faces the wrong way (v=({vx/1e6:.2f},{vy/1e6:.2f}))")

    # ---------------------------------------------------- legalize passives
    KEEP = {r for r in ANCHOR if r[0] in "JQUY"}
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
        if not (X0 + 0.8 + w2 < x < X0 + W - 0.8 - w2 and Y0 + 0.8 + h2 < y < Y0 + H - 0.8 - h2):
            return False
        for hx, hy in holes:
            if max(abs(x - hx) - w2, abs(y - hy) - h2, 0) < 3.0:
                return False
        for r2, f2 in fps.items():
            if r2 == skip or r2.startswith("H"):
                continue
            L, T, R, B = bbox(f2)
            if not (x + w2 + 0.35 <= L or R <= x - w2 - 0.35 or
                    y + h2 + 0.35 <= T or B <= y - h2 - 0.35):
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

    # design rules floor (JLC 4L advanced)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.15)
    ds.m_MinClearance = int(0.10e6)
    ds.m_ViasMinAnnularWidth = int(0.045e6)
    ds.m_HoleClearance = int(0.15e6)
    ds.m_HoleToHoleMin = int(0.15e6)
    ds.m_CopperEdgeClearance = int(0.10e6)
    ds.m_ViasMinSize = pcbnew.FromMM(0.25)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.15)

    # ------------------------------------------------------------- zones
    def add_zone(net, layer, pts, prio, minw=0.25, clr=0.25, name=None, full=False):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        if net:
            z.SetNet(netmap[net])
        z.SetAssignedPriority(prio)
        z.SetMinThickness(pcbnew.FromMM(minw))
        z.SetLocalClearance(pcbnew.FromMM(clr))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full
                           else pcbnew.ZONE_CONNECTION_THERMAL)
        if name:
            z.SetZoneName(name)
        z.Outline().NewOutline()
        for x, y in pts:
            z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
        board.Add(z)
        return z

    FULL = [(X0, Y0), (X0 + W, Y0), (X0 + W, Y0 + H), (X0, Y0 + H)]
    for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
        add_zone("GND", lay, FULL, 0)
    # In1: THE continuous ground plane (ADR-0004) - full connection, no splits
    add_zone("GND", pcbnew.In1_Cu, FULL, 0, full=True)
    # In2 power islands
    add_zone("VBUS_5V", pcbnew.In2_Cu, [(50, 50), (72, 50), (72, 92), (50, 92)],
             2, minw=0.3, full=True)
    add_zone("3V3A", pcbnew.In2_Cu, [(88, 50), (115, 50), (115, 92), (88, 92)],
             2, minw=0.3, full=True)

    for fp in board.GetFootprints():
        ref = fp.Reference()
        ref.SetLayer(pcbnew.B_Fab if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Fab)
        ref.SetTextSize(pcbnew.VECTOR2I_MM(0.5, 0.5))
        ref.SetTextThickness(int(0.08e6))
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(MOUNT)} holes; zones; saved {PCB.name}")


if __name__ == "__main__":
    main()
