"""Import KiCadRoutingTools output (KiCad-9 dialect) into a pcbnew board.

    /usr/bin/python3 import_krt.py KRT_OUT.kicad_pcb BASE.kicad_pcb OUT.kicad_pcb \
        [--nets NET1 NET2 ...] [--min-clearance 0.10] [--no-fill]

Hard-fails on layers it doesn't know (routing on In3/In4 needs the map
extended — silently dumping them on F.Cu would be a shorts factory). Via
dedupe is same-net only. If the KRT via syntax gains attributes between
(layers ...) and (net ...), the via regex stops matching — the import
count will drop; compare counts against KRT's summary.

BASE should be the segment-free pcbnew board the KRT chain started from.
Source-owned vias (for example thermal via-in-pad arrays) may already exist
and are preserved; matching copies inherited by the KRT chain are deduped
against them. Import the COMPLETE final chain file in one shot — partial
merges of multiple passes create duplicate/conflicting copper. --nets
restricts the import to specific nets (for the repair workflow). Zones are
refilled and the result saved to OUT; run classified_drc.py on it as the
green check.
"""
import argparse
import re
from pathlib import Path

import pcbnew

ap = argparse.ArgumentParser()
ap.add_argument("krt_file")
ap.add_argument("base")
ap.add_argument("out")
ap.add_argument("--nets", nargs="*", default=None)
ap.add_argument("--min-clearance", type=float, default=0.10)
ap.add_argument("--no-fill", action="store_true")
args = ap.parse_args()

src = Path(args.krt_file).read_text(encoding="utf-8-sig")
netname = dict(re.findall(r'\(net (\d+) "([^"]+)"\)', src))
board = pcbnew.LoadBoard(args.base)
LAY = {"F.Cu": pcbnew.F_Cu, "B.Cu": pcbnew.B_Cu,
       "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu,
       "In3.Cu": pcbnew.In3_Cu, "In4.Cu": pcbnew.In4_Cu}
want = set(args.nets) if args.nets else None
nseg = nvia = 0
# pcbnew exposes both routed segments and vias through GetTracks().  The base
# is deliberately allowed to contain source-owned vias (thermal arrays are
# geometry, not router output). Seed the dedupe table from those vias so a
# KRT chain that inherited the base cannot add a second barrel on top.
seen = []
base_seen = []
for item in board.GetTracks():
    if item.GetClass() != "PCB_VIA":
        continue
    pos = item.GetPosition()
    row = (pos.x, pos.y, item.GetNetCode(),
           item.GetWidth(pcbnew.F_Cu), item.GetDrill())
    seen.append(row[:3])
    base_seen.append(row)
for m in re.finditer(
        r'\(segment\s+\(start ([\d.-]+) ([\d.-]+)\)\s+\(end ([\d.-]+) '
        r'([\d.-]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+'
        r'\(net (?:(\d+)|"([^"]+)")\)', src):
    x1, y1, x2, y2, w, lay, nn, nname = m.groups()
    # KRT emits numeric net ids when fed KiCad-7 boards and QUOTED NET NAMES
    # when fed KiCad-10 boards - accept both (found the hard way, 2026-07)
    name = nname if nname is not None else netname.get(nn, "")
    if want is not None and name not in want:
        continue
    net = board.FindNet(name)
    if net is None or net.GetNetCode() <= 0:
        continue
    if lay not in LAY:
        raise SystemExit(f"unknown layer {lay!r} — extend LAY before importing")
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I_MM(float(x1), float(y1)))
    t.SetEnd(pcbnew.VECTOR2I_MM(float(x2), float(y2)))
    t.SetWidth(pcbnew.FromMM(float(w)))
    t.SetLayer(LAY[lay])
    t.SetNet(net)
    board.Add(t)
    nseg += 1
for m in re.finditer(
        r'\(via\s+\(at ([\d.-]+) ([\d.-]+)\)\s+\(size ([\d.]+)\)\s+'
        r'\(drill ([\d.]+)\)\s+\(layers "[^"]+" "[^"]+"\)[\s\S]*?\(net (?:(\d+)|"([^"]+)")\)',
        src):
    x, y, s, dr, nn, nname = m.groups()
    name = nname if nname is not None else netname.get(nn, "")
    if want is not None and name not in want:
        continue
    px, py = pcbnew.FromMM(float(x)), pcbnew.FromMM(float(y))
    net = board.FindNet(name)
    if net is None or net.GetNetCode() <= 0:
        continue
    size, drill = pcbnew.FromMM(float(s)), pcbnew.FromMM(float(dr))
    inherited = [v for v in base_seen
                 if abs(v[0] - px) <= 1000 and abs(v[1] - py) <= 1000
                 and v[2] == net.GetNetCode()]
    if inherited:
        if any(abs(v[3] - size) > 1000 or abs(v[4] - drill) > 1000
               for v in inherited):
            raise SystemExit(
                f"KRT/base via geometry disagrees at ({float(x):.6f}, "
                f"{float(y):.6f}) on {name}: KRT {float(s):.3f}/"
                f"{float(dr):.3f} mm versus source-owned "
                f"{inherited[0][3] / 1e6:.3f}/{inherited[0][4] / 1e6:.3f} mm")
        continue
    if any(abs(v[0] - px) < 100000 and abs(v[1] - py) < 100000
           and v[2] == net.GetNetCode() for v in seen):
        continue  # same-net duplicate only — different nets colliding is
                  # a REAL problem the DRC green check must surface
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(px, py))
    v.SetWidth(size)
    v.SetDrill(drill)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    board.Add(v)
    seen.append((px, py, net.GetNetCode()))
    nvia += 1
ds = board.GetDesignSettings()
ds.m_MinClearance = pcbnew.FromMM(args.min_clearance)
if not args.no_fill:
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(args.out)
print(f"imported {nseg} segments, {nvia} vias -> {args.out}")
print("next: classified_drc.py + your audit gate")
