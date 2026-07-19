#!/usr/bin/env python3
"""Generate 04_kicad/crow_array_pod.kicad_pcb from the netlist + floorplan.

94.5x44.5mm 2-layer = the Hammond 1551WY drawing's MAXIMUM P.C. BOARD
(01_docs/hammond_1551wy_rev2023-08-31.pdf): concave R6.25 corner cutouts
(clear the #4 lid-screw bosses; drawing straight spans 82.00/32.00) and
four Ø2.7 holes on the 75.00x35.00 boss pattern inset (9.75, 4.75).

Placement (ARCHITECTURE.md + ADR-0004): J1 RJ45 jack at the WEST end,
mate-opening facing WEST toward the gland wall; jack body AND the exposed
plug volume must sit inside the 1551WY lid's 81x31 full-height recess
(board x 56.75-137.75, y 56.75-87.75; only 7.9mm headroom under the
perimeter band — ADR-0004 clearance math). Beeper block SW (max
separation from the mic), 5VF filter south-center, OPA1678 center-east,
mic pads at the FAR EAST (§3A: mic and transducer at opposite ends),
midpoint divider SE.
Zones: GND pours both sides (B.Cu = the return plane). Missing footprint =
HARD ERROR. Refdes de-collision pass prints every reference on F.SilkS.

Run with KiCad-bundled python: /usr/bin/python3 03_src/generate_board.py
"""
import json
import math
import re
from pathlib import Path

import pcbnew

HERE = Path(__file__).parent
K = HERE.parent / "04_kicad"
NETLIST = HERE.parent / "06_build" / "netlists" / "crow_array_pod.net"
PCB = K / "crow_array_pod.kicad_pcb"
STD = "/usr/share/kicad/footprints"
PROJ = str(HERE / "lib" / "pod.pretty")

X0, Y0, W, H = 50.0, 50.0, 94.5, 44.5
X1, Y1 = X0 + W, Y0 + H
RCUT = 6.25          # concave corner cutout radius (>= drawing notch)
HOLES = [(X0 + 9.75, Y0 + 4.75), (X0 + 84.75, Y0 + 4.75),
         (X0 + 9.75, Y0 + 39.75), (X0 + 84.75, Y0 + 39.75)]


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
    root = PROJ if lib == "pod" else f"{STD}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(root, name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid} in {root}")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


# ------------------------------------------------------------- floorplan
ANCHOR = {
    # RJ45 jack (ADR-0004): rot 270 => mating face WEST, pin 1 north.
    # Anchor = pad 1. Body spans x 69.7-86.6, y 57.8-77.4 (inside the lid
    # recess); exposed plug needs ~12mm west of the face, also in-recess.
    "J1": (78.0, 64.0, 270),
    # entry ESD near J1 contact tails 1/2 (east side of the jack)
    "D1": (88.0, 62.0, 0),
    # shield-bond reserve, north strip (J1 SH tails at x 77.1)
    "TP6": (65.5, 52.8, 0), "R15": (70.5, 52.8, 0),
    # audio-pair TPs, north strip
    "TP1": (75.0, 52.8, 0), "TP2": (80.5, 52.8, 0),
    # beeper block SW (opposite end from the mic)
    "R12": (63.0, 79.0, 0), "BZ1": (72.0, 84.0, 0),
    "D2": (81.0, 81.0, 0), "D3": (81.0, 86.0, 0),
    # 5VF filter, south-center
    "R1": (86.0, 88.5, 0), "C1": (92.5, 88.5, 0), "C2": (98.5, 88.5, 0),
    # amplifier center-east
    "U1": (102.0, 66.0, 0),
    "C6": (107.5, 61.5, 0), "C7": (96.0, 59.5, 0),
    "R6": (98.5, 77.5, 0), "R7": (105.0, 77.5, 0),
    "R8": (98.5, 81.0, 0), "R9": (105.0, 81.0, 0),
    # mic conditioning close to +IN_A (short AIN, low-Z MIC runs east)
    "C3": (104.0, 70.5, 0), "R3": (104.0, 74.0, 0), "R2": (124.0, 66.0, 0),
    # mic wire pads, far east
    "J2": (139.5, 70.5, 0),
    # midpoint reference SE
    "R4": (114.0, 84.0, 0), "R5": (120.5, 84.0, 0),
    "C4": (114.0, 87.5, 0), "C5": (120.5, 87.5, 0), "TP3": (126.5, 85.5, 0),
    # output isolation + choke reserve, between amp and the jack's rear
    "R10": (96.0, 63.0, 0), "R11": (96.0, 66.5, 0),
    "L1": (92.0, 64.0, 0), "R13": (92.0, 60.0, 0), "R14": (92.0, 68.0, 0),
    # rail TPs
    "TP4": (103.0, 88.5, 0), "TP5": (108.5, 88.5, 0),
}

# plain-words silkscreen (P-SILK-FN). (text, x, y, size)
SILK = [
    ("NOT ETHERNET - CUSTOM 5V PINOUT", 100.0, 51.6, 1.1),
    # jack-side warning, permanently visible above the plug zone (ADR-0004d)
    ("NOT ETHERNET", 61.0, 58.2, 0.8),
    # T568B function legend in the plug zone west of the jack (readable
    # during field crimping/bring-up; covered only once a plug is seated)
    ("RJ45: 1 AUD+ 2 AUD-", 62.8, 64.2, 0.65),
    ("3 5V-BEEP 6 BEEP-RET", 62.8, 66.2, 0.65),
    ("4/7 5V  5/8 GND", 62.8, 68.2, 0.65),
    ("CUSTOM 5V PINOUT", 62.8, 70.4, 0.65),
    # beeper block
    ("BEEPER", 72.0, 78.5, 0.7), ("FLYBACK", 84.0, 78.4, 0.6),
    ("TVS DNP", 80.8, 90.2, 0.6),
    # mic
    ("MIC PADS", 139.5, 66.2, 0.7), ("MIC+", 135.8, 70.5, 0.6),
    ("MIC-", 135.8, 73.04, 0.6),
    # TPs
    ("SHIELD", 65.5, 54.7, 0.6), ("AUD+", 75.0, 54.7, 0.6),
    ("AUD-", 80.5, 54.7, 0.6), ("2V5", 126.5, 87.6, 0.6),
    ("5V", 103.0, 90.6, 0.6), ("GND", 108.5, 90.6, 0.6),
    ("crow-array-pod v1.1", 100.0, 92.8, 0.9),
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

    # outline: rect with concave quarter-arc corner cutouts (R6.25)
    def seg(xa, ya, xb, yb):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I_MM(xa, ya))
        s.SetEnd(pcbnew.VECTOR2I_MM(xb, yb))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.15))
        board.Add(s)

    def arc(cx, cy, ax, ay, bx, by):
        """Concave arc centered at the rect corner from (ax,ay) to (bx,by)."""
        a = pcbnew.PCB_SHAPE(board)
        a.SetShape(pcbnew.SHAPE_T_ARC)
        mangle = math.atan2((ay + by) / 2 - cy, (ax + bx) / 2 - cx)
        mx, my = cx + RCUT * math.cos(mangle), cy + RCUT * math.sin(mangle)
        a.SetArcGeometry(pcbnew.VECTOR2I_MM(ax, ay), pcbnew.VECTOR2I_MM(mx, my),
                         pcbnew.VECTOR2I_MM(bx, by))
        a.SetLayer(pcbnew.Edge_Cuts)
        a.SetWidth(pcbnew.FromMM(0.15))
        board.Add(a)

    R = RCUT
    seg(X0 + R, Y0, X1 - R, Y0)          # top
    seg(X1, Y0 + R, X1, Y1 - R)          # right
    seg(X0 + R, Y1, X1 - R, Y1)          # bottom
    seg(X0, Y0 + R, X0, Y1 - R)          # left
    arc(X0, Y0, X0 + R, Y0, X0, Y0 + R)  # NW
    arc(X1, Y0, X1, Y0 + R, X1 - R, Y0)  # NE
    arc(X1, Y1, X1 - R, Y1, X1, Y1 - R)  # SE
    arc(X0, Y1, X0, Y1 - R, X0 + R, Y1)  # SW

    # mounting holes: Ø2.7 for the #2 self-tapping post screws
    for i, (hx, hy) in enumerate(HOLES, 1):
        mh = pcbnew.FootprintLoad(f"{STD}/MountingHole.pretty", "MountingHole_2.7mm_M2.5")
        if mh is None:
            raise RuntimeError("mounting hole footprint missing")
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
            # J1 GND tails: SOLID zone connection on both layers — the
            # B.Cu plane's thermal spokes starve in the dense tail field
            # (v1.1: zone-to-zone unconnected + 0.10mm connection_width),
            # and the jack is hand-soldered anyway (thermal relief moot)
            if ref == "J1" and pad_net.get(key) == "GND":
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        board.Add(fp)
        placed += 1

    board_pads = {(f.GetReference(), p.GetNumber())
                  for f in board.GetFootprints() for p in f.Pads()}
    missing = [k for k in pad_net if k not in board_pads]
    if missing:
        raise RuntimeError(f"netlist pads missing on board: {missing}")

    # ---- orientation asserts ----
    # J1 RJ45 (ADR-0004): mating face WEST (LED-tail pads 9-12 mark the
    # mating face and must sit west of the contact pads), pin 1 north,
    # body + exposed-plug volume inside the 1551WY lid's 81x31 recess.
    j1 = board.FindFootprintByReference("J1")
    jp = {p.GetNumber(): p.GetPosition() for p in j1.Pads() if p.GetNumber()}
    if not jp["9"].x < min(jp[str(n)].x for n in range(1, 9)):
        raise RuntimeError("J1 mating face must point WEST (LED tails west of contacts)")
    if not jp["1"].y < jp["8"].y:
        raise RuntimeError("J1 contacts must run north->south, pin 1 north")
    RECESS = (56.75, 56.75, 137.75, 87.75)   # lid full-height recess (ADR-0004c)
    PLUG_MM = 12.0                           # exposed rigid plug west of the face
    bbj = j1.GetBoundingBox(False, False)
    jx0, jy0 = pcbnew.ToMM(bbj.GetLeft()), pcbnew.ToMM(bbj.GetTop())
    jx1, jy1 = pcbnew.ToMM(bbj.GetRight()), pcbnew.ToMM(bbj.GetBottom())
    if not (jx0 - PLUG_MM >= RECESS[0] and jy0 >= RECESS[1]
            and jx1 <= RECESS[2] and jy1 <= RECESS[3]):
        raise RuntimeError(
            f"J1 body+plug outside the lid recess: bbox ({jx0:.1f},{jy0:.1f})-"
            f"({jx1:.1f},{jy1:.1f}), plug to x={jx0 - PLUG_MM:.1f}, recess {RECESS}")
    # BZ1 polarity: pad 1 (+) is the top-left pad
    bz = board.FindFootprintByReference("BZ1")
    bp = {p.GetNumber(): p.GetPosition() for p in bz.Pads()}
    if not (bp["1"].y < bp["2"].y and bp["1"].x < bp["3"].x):
        raise RuntimeError("BZ1 rotated: pad1 (+) must be top-left")
    # J2 pin order: MIC+ north
    j2 = board.FindFootprintByReference("J2")
    j2p = {p.GetNumber(): p.GetPosition() for p in j2.Pads()}
    if not j2p["1"].y < j2p["2"].y:
        raise RuntimeError("J2 pin1 (MIC+) must be north")
    # polarized parts: pad-1 nets (part.yaml facts; audit re-checks as I9)
    for ref, pad, want in [("C1", "1", "5VF"), ("D2", "1", "BZ_P"),
                           ("D3", "1", "BZ_P"), ("BZ1", "1", "BZ_P")]:
        f = board.FindFootprintByReference(ref)
        got = {p.GetNumber(): p.GetNetname() for p in f.Pads()}[pad]
        if got != want:
            raise RuntimeError(f"{ref} pad{pad} net {got} != {want} (polarity)")

    # ---------------------------------------------------- legalize passives
    KEEP = {r for r in ANCHOR if r[0] in "JUB" or r.startswith("TP")}

    def bbox(f):
        bb = f.GetBoundingBox(False, False)
        return (pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()),
                pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    holes = [(pcbnew.ToMM(f.GetPosition().x), pcbnew.ToMM(f.GetPosition().y))
             for r, f in fps.items() if r.startswith("H")]

    def corner_ok(x, y, w2, h2):
        for cx, cy in [(X0, Y0), (X1, Y0), (X0, Y1), (X1, Y1)]:
            # nearest point of the part bbox to the corner
            nx = max(abs(x - cx) - w2, 0)
            ny = max(abs(y - cy) - h2, 0)
            if math.hypot(nx, ny) < RCUT + 0.3:
                return False
        return True

    def clear_at(f, x, y, skip):
        old = f.GetPosition()
        f.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        l, t, r_, bt = bbox(f)
        f.SetPosition(old)
        w2, h2 = (r_ - l) / 2, (bt - t) / 2
        if not (X0 + 0.8 + w2 < x < X1 - 0.8 - w2 and Y0 + 0.8 + h2 < y < Y1 - 0.8 - h2):
            return False
        if not corner_ok(x, y, w2, h2):
            return False
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
    add_zone("GND", pcbnew.F_Cu, FULL, 0, full=True)   # solid (2L thermal starvation)
    add_zone("GND", pcbnew.B_Cu, FULL, 0, full=False)  # THE return plane

    # ------------------------------------------------------------- silk text
    for txt, x, y, size in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        t.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
        t.SetTextThickness(pcbnew.FromMM(max(0.13, size * 0.16)))
        board.Add(t)

    # refdes on silk, de-collided (golden rule 3b / audit I10)
    MM = pcbnew.ToMM
    TH = 0.6
    THK = 0.12
    CLR = 0.16

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
        # part BODY is an obstacle too: silk under a body is invisible on
        # the assembled board (U1 refdes shipped under the SOIC in review)
        if not fp.GetReference().startswith("H"):
            pad_obst.append(box(fp.GetBoundingBox(False, False), 0.05))
    for t in board.GetDrawings():
        if t.GetClass() == "PCB_TEXT" and t.IsOnLayer(pcbnew.F_SilkS):
            silk_obst.append(box(t.GetBoundingBox(), CLR * 0.5))
    # cathode marks: "K" beside pad 1 of D2/D3 (flyback/TVS polarity is
    # load-bearing — ADR-0002; the D_SMA bar alone graded too subtle)
    for dref in ("D2", "D3"):
        dfp = board.FindFootprintByReference(dref)
        p1 = next(p for p in dfp.Pads() if p.GetNumber() == "1")
        px, py = MM(p1.GetPosition().x), MM(p1.GetPosition().y)
        KOFF = [(0, -2.4), (0, 2.4), (0, -2.1), (0, 2.1), (-1.6, -1.7), (-1.6, 1.7), (-2.4, 0),
                (0, -2.6), (0, 2.6), (-1.2, -2.4), (-1.2, 2.4), (1.2, -2.4),
                (1.2, 2.4), (0, -3.2), (0, 3.2), (-2.0, -2.0), (-2.0, 2.0)]
        for dx, dy in KOFF:
            kt = pcbnew.PCB_TEXT(board)
            kt.SetText("K")
            kt.SetLayer(pcbnew.F_SilkS)
            kt.SetPosition(pcbnew.VECTOR2I_MM(px + dx, py + dy))
            kt.SetTextSize(pcbnew.VECTOR2I_MM(0.6, 0.6))
            kt.SetTextThickness(pcbnew.FromMM(0.13))
            cand = box(kt.GetBoundingBox())
            if (X0 + 0.2 < cand[0] and cand[2] < X1 - 0.2
                    and Y0 + 0.2 < cand[1] and cand[3] < Y1 - 0.2
                    and not any(hit(cand, o) for o in pad_obst)
                    and not any(hit(cand, o) for o in silk_obst)):
                board.Add(kt)
                silk_obst.append(cand)
                break
        else:
            raise RuntimeError(f"no clear spot for {dref} cathode K mark")

    OFF = [(0, o * s) for o in (1.0, 1.6, 2.2, 2.9, 3.6, 4.4, 5.2, 6.0) for s in (-1, 1)] + \
          [(o * s, 0) for o in (1.3, 2.0, 2.8, 3.6, 4.5, 5.4, 6.2) for s in (-1, 1)] + \
          [(dx, dy) for d in (1.4, 2.2, 3.0, 4.0, 5.0) for dx in (-d, d) for dy in (-d, d)] + \
          [(0, o * s) for o in (7.0, 8.0, 9.0, 10.0, 11.0) for s in (-1, 1)] + \
          [(o * s, 0) for o in (7.2, 8.2, 9.2, 10.2) for s in (-1, 1)] + \
          [(dx, dy) for d in (6.0, 7.0, 8.0, 9.0) for dx in (-d, d) for dy in (-d, d)]
    waived = []

    def prio(fp):
        r = fp.GetReference()
        return (0 if r[0] in "UJDB" or r.startswith("TP") else 1, r)
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
            continue
        ref.SetLayer(pcbnew.F_SilkS)
        ref.SetVisible(True)
        fx, fy = MM(fp.GetPosition().x), MM(fp.GetPosition().y)
        placed_ok = False
        for dx, dy in OFF:
            ref.SetPosition(pcbnew.VECTOR2I_MM(fx + dx, fy + dy))
            cand = box(ref.GetBoundingBox())
            if not (X0 + 0.2 < cand[0] and cand[2] < X1 - 0.2
                    and Y0 + 0.2 < cand[1] and cand[3] < Y1 - 0.2):
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
    (HERE.parent / "06_build" / "refdes_waiver.json").write_text(
        json.dumps(sorted(waived)))
    print(f"refdes on silk: {placed - len(waived)}/{placed} placed, "
          f"{len(waived)} waived to Fab: {sorted(waived)}")
    board.Save(str(PCB))
    print(f"placed {placed} footprints + {len(HOLES)} holes; zones; silk; saved {PCB.name}")


if __name__ == "__main__":
    main()
