#!/usr/bin/env python3
"""circuit_json_to_kicad_pcb — PLACEMENT-AS-CODE seed generator (ADR-0002 Phase B).

Land every part at the placement tscircuit AUTHORED (`pcbX`/`pcbY`/`pcbRotation`
in the TSX, carried in `circuit.json` as `pcb_component.center` / `.rotation` /
`.layer`) into a native KiCad `.kicad_pcb`. This is the placement SEED — NOT a
finished board: our audit + legalize + route certify it downstream. The honest
expectation (kicad-pcb golden rule 7) is that raw/auto tscircuit placement is
electrically blind (decouplers land far from ICs, analog/digital unsegregated),
so this seed will throw audit violations that legalization must close.

The companion to `circuit_json_to_kicad_sch.py`: it reads the SAME
`circuit.json` connectivity model and reuses that converter's FPID resolution
(the baked-in commodity-token map + the `02_parts/*/part.yaml` MPN/LCSC
override), so a part's KiCad footprint identity is IDENTICAL between the
schematic bridge and the placement bridge — the board reaches netlist parity
with the sealed board by construction.

Inputs / outputs:
  * `circuit.json`               — placement (pcb_component) + refdes model.
  * `--netlist <cook.net>`       — the converter-exported netlist: the SAME
    (refdes,pad)->net + per-part FPID vocabulary generate_board consumes, so the
    seed's nets and footprints match the backend exactly. (Placement is the ONLY
    thing taken from circuit.json; connectivity + FPID come from the netlist that
    the converter kicad_sch already produced.)
  * `--outline-from <sealed.kicad_pcb>` — copy the board Edge_Cuts + the NPTH
    mounting-hole footprints from a reference board, and DEFINE the coordinate
    origin as that outline's bbox center. The tscircuit board is authored around
    its own origin (0,0); mapping tsc(0,0) -> the reference outline center drops
    the authored placement into the certified board frame so OUR audit / route
    (which key on that frame + those screw keepouts) apply unchanged. Mounting
    holes are mechanical fixtures — taken from the reference board so the
    legalizer's hardcoded screw keepouts stay consistent with the real holes.
  * `-o <out.kicad_pcb>`.

Coordinate mapping (tscircuit mm, y-UP, origin-centered -> KiCad mm, y-DOWN):
    kx = origin_x + tsc_x
    ky = origin_y - tsc_y                      # y flip
    korient = (-tsc_rotation) mod 360          # mirroring y turns CCW into CW
`pcb_component.layer == "bottom"` flips the footprint to B.Cu.

Missing placement or missing FPID for any electrical refdes is a HARD ERROR
(kicad-pcb: a generator that skips a part as a console warning shipped a board
without its ESD array). GND pours (both layers, unfilled) + the JLC 2-layer
design-setting floors are emitted so the seed is a complete, audit-able board.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew  # noqa: E402
import circuit_json_to_kicad_sch as conv  # reuse FPID map + override loader  # noqa: E402


def parse_netlist(path):
    """(refdes,pad)->net, refdes->(fpid,value), set(nets). Same grammar
    generate_board.parse_netlist uses (KiCad 10 pretty-printed netlist)."""
    s = open(path).read()
    comps = {}
    for m in re.finditer(
            r'\(comp\s+\(ref\s+"([^"]+)"\)(.*?)(?=\(comp\s+\(ref|\(libparts)',
            s, re.S):
        ref, body = m.group(1), m.group(2)
        fp = re.search(r'\(footprint\s+"([^"]*)"\)', body)
        val = re.search(r'\(value\s+"([^"]*)"\)', body)
        comps[ref] = (fp.group(1) if fp else "", val.group(1) if val else "")
    if not comps:
        raise RuntimeError("parsed 0 components from netlist")
    pad_net, nets = {}, set()
    for m in re.finditer(
            r'\(net\s+\(code\s+"\d+"\)\s+\(name\s+"([^"]+)"\)(.*?)(?=\(net\s+\(code|\Z)',
            s, re.S):
        name, body = m.group(1), m.group(2)
        nets.add(name)
        for r, p in re.findall(
                r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', body):
            pad_net[(r, p)] = name
    return comps, pad_net, nets


def load_placement(circuit_json):
    """refdes -> (x, y, rotation_deg, layer) from circuit.json pcb_component."""
    d = json.load(open(circuit_json, encoding="utf-8-sig"))
    src = {e['source_component_id']: e for e in d
           if e.get('type') == 'source_component'}
    place = {}
    for e in d:
        if e.get('type') != 'pcb_component':
            continue
        sc = src.get(e['source_component_id'])
        if not sc:
            continue
        c = e.get('center', {})
        place[sc['name']] = (float(c.get('x', 0.0)), float(c.get('y', 0.0)),
                             float(e.get('rotation', 0.0) or 0.0),
                             e.get('layer', 'top'))
    # mounting holes (non-electrical) carry authored pcbX/pcbY as pcb_hole
    holes = []
    hby_src = {e['source_component_id']: e for e in d
               if e.get('type') == 'source_component'}
    for e in d:
        if e.get('type') == 'pcb_hole':
            holes.append((float(e.get('x', 0.0)), float(e.get('y', 0.0)),
                          e.get('hole_diameter')))
    return place, holes


def copy_outline_and_holes(board, ref_pcb, netmap):
    """Copy Edge_Cuts drawings + NPTH mounting-hole footprints from a reference
    board. Returns the outline bbox center (origin for the tscircuit frame)."""
    ref = pcbnew.LoadBoard(ref_pcb)
    MM = pcbnew.ToMM
    xs, ys = [], []
    for dwg in ref.GetDrawings():
        if dwg.GetLayer() != pcbnew.Edge_Cuts:
            continue
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(dwg.GetStart())
        s.SetEnd(dwg.GetEnd())
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)
        for pt in (dwg.GetStart(), dwg.GetEnd()):
            xs.append(MM(pt.x))
            ys.append(MM(pt.y))
    # NPTH mounting holes: recreate by FPID at the reference positions
    for f in ref.GetFootprints():
        npth = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in f.Pads())
        if not (f.GetReference().startswith("H") and npth):
            continue
        fpid = f.GetFPID()
        lib, name = fpid.GetLibNickname().wx_str(), fpid.GetLibItemName().wx_str()
        std = "/usr/share/kicad/footprints"
        mh = pcbnew.FootprintLoad(f"{std}/{lib}.pretty", name)
        if mh is None:
            raise RuntimeError(f"mounting-hole footprint not found: {lib}:{name}")
        mh.SetFPID(pcbnew.LIB_ID(lib, name))
        mh.SetReference(f.GetReference())
        mh.SetAttributes(mh.GetAttributes()
                         | pcbnew.FP_BOARD_ONLY | pcbnew.FP_EXCLUDE_FROM_BOM)
        mh.SetPosition(f.GetPosition())
        board.Add(mh)
    if not xs:
        raise RuntimeError("reference board has no Edge_Cuts outline")
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, \
        (min(xs), min(ys), max(xs), max(ys))


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("circuit_json")
    ap.add_argument("--netlist", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--outline-from", required=True,
                    help="reference board: copy Edge_Cuts + NPTH holes, define origin")
    ap.add_argument("--parts-dir", default=None,
                    help="02_parts/ for FPID overrides (default: auto-discover)")
    ap.add_argument("--no-pours", action="store_true",
                    help="skip GND pours (audit IZ then fails — for measurement)")
    a = ap.parse_args()

    place, holes = load_placement(a.circuit_json)
    comps, pad_net, nets = parse_netlist(a.netlist)

    parts_dir = a.parts_dir or conv._discover_up(a.circuit_json, ["02_parts"], True)
    overrides = conv.load_part_overrides(parts_dir)

    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    netmap = {}
    for n in sorted(nets):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        netmap[n] = ni

    ox, oy, (bx0, by0, bx1, by1) = copy_outline_and_holes(
        board, a.outline_from, netmap)

    std = "/usr/share/kicad/footprints"
    placed = 0
    off_outline = []
    for ref, (fpid, val) in sorted(comps.items()):
        if ref not in place:
            raise RuntimeError(f"{ref} has no tscircuit placement (pcb_component)")
        if not fpid:
            raise RuntimeError(f"{ref} has no footprint FPID in the netlist")
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(f"{std}/{lib}.pretty", name)
        if fp is None:
            raise RuntimeError(f"footprint not found: {fpid}")
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(val)
        tx, ty, trot, layer = place[ref]
        kx = ox + tx
        ky = oy - ty                       # y flip: tscircuit y-up -> KiCad y-down
        fp.SetPosition(pcbnew.VECTOR2I_MM(round(kx, 4), round(ky, 4)))
        korient = (-trot) % 360            # mirror-y turns CCW into CW
        if korient:
            fp.SetOrientationDegrees(korient)
        if layer == "bottom":
            fp.Flip(fp.GetPosition(), False)
        # SJ symbol is in_bom yes but the KiCad SolderJumper footprint ships
        # exclude_from_bom -> footprint_symbol_mismatch parity. Clear it.
        if ref.startswith("SJ"):
            fp.SetAttributes(fp.GetAttributes() & ~pcbnew.FP_EXCLUDE_FROM_BOM)
        for pad in fp.Pads():
            k = (ref, pad.GetNumber())
            if k in pad_net:
                pad.SetNet(netmap[pad_net[k]])
        board.Add(fp)
        placed += 1
        # note (do NOT fail) any pad landing outside the reference outline
        for pad in fp.Pads():
            px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
            if not (bx0 < px < bx1 and by0 < py < by1):
                off_outline.append(f"{ref}.{pad.GetNumber()}")

    board_pads = {(f.GetReference(), p.GetNumber())
                  for f in board.GetFootprints() for p in f.Pads()}
    missing = [k for k in pad_net if k not in board_pads]
    if missing:
        raise RuntimeError(f"netlist pads missing on board: {missing}")

    # polarity + role asserts (placement-independent, net-binding) — same set as
    # generate_board; proves the seed carries the sealed board's polarity intent.
    fps = {f.GetReference(): f for f in board.GetFootprints()}

    def padnet(ref, num):
        return next(p for p in fps[ref].Pads()
                    if p.GetNumber() == num).GetNetname()
    pol_fail = []
    for ref, want in [("D1", "DAT"), ("D2", "CLK")]:
        if ref in fps and padnet(ref, "1") != want:
            pol_fail.append(f"{ref}.1={padnet(ref, '1')} != {want}")
    for ref, num, want in [("Q1", "2", "5V"), ("Q1", "3", "E_PLUS"),
                           ("U1", "8", "S_PLUS"), ("U1", "7", "S_MINUS"),
                           ("J6", "4", "DAT"), ("J6", "5", "CLK")]:
        if ref in fps and padnet(ref, num) != want:
            pol_fail.append(f"{ref}.{num}={padnet(ref, num)} != {want}")
    if pol_fail:
        raise RuntimeError(f"polarity/role asserts failed: {pol_fail}")

    # JLC 2-layer floors (identical to generate_board)
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

    if not a.no_pours:
        for lyr in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(board)
            z.SetLayer(lyr)
            z.SetNet(netmap["GND"])
            z.SetAssignedPriority(0)
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            z.SetMinThickness(pcbnew.FromMM(0.3))
            z.SetLocalClearance(pcbnew.FromMM(0.3))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            z.Outline().NewOutline()
            for x, y in [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]:
                z.Outline().Append(pcbnew.VECTOR2I_MM(x, y))
            board.Add(z)

    board.Save(a.out)
    print(f"placed {placed} parts from tscircuit pcb_component at origin "
          f"({ox:.1f},{oy:.1f}); {len(off_outline)} pads outside outline"
          + (f": {off_outline[:8]}" if off_outline else ""))
    print(f"  FPID overrides: {len(overrides)} keys from {parts_dir or '(none)'}; "
          f"nets: {len(nets)}; pours: {'no' if a.no_pours else '2 GND'}")


if __name__ == "__main__":
    main()
