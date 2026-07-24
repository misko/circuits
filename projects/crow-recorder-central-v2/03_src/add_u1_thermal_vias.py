#!/usr/bin/env python3
"""add_u1_thermal_vias — F1 closure (external review 2026-07-24, EXT-F1).

The XU316 exposed-pad thermal grid was modeled as 16 duplicate-numbered
thru-hole PADS in the footprint; those emit under a ComponentDrill tool in
the Excellon PTH file, and JLC may read them as OPEN plated component holes
under the pasted EP (wicking/voiding/reverse-side solder, consigned-part
rejection risk). A thermal hole under an EP is a VIA: this step deletes
nothing (the footprint no longer carries the pads) and ADDS 16 real
0.30/0.15 GND via objects on the 4x4 grid (+/-0.55 / +/-1.65 mm, rotated
with U1) so they emit under the ViaDrill tool and can be ordered as
epoxy-filled + capped via-in-pad.

Runs deterministically in rebuild_reuse.sh after `import` (before stitch,
so every downstream pass and the DRC gate see them as normal GND copper).

    /usr/bin/python3 03_src/add_u1_thermal_vias.py [board.kicad_pcb]

STOPGAP (canon M8, 03_src contract): this is a declared generic-backend gap.
The config schema that would replace it is a route.yaml stitch block, e.g.
  ep_thermal_vias: [{ref: U1, grid: [-1.65,-0.55,0.55,1.65], size: 0.30,
                     drill: 0.15, net: GND}]
plus a board-setup `via_protection: {capping: yes, filling: yes}` key.
The SECOND board needing an EP-thermal-via seed promotes this into
route_and_stitch_generic.

Second mode — `--seal-fab-flags` — runs LAST in the rebuild (after the
final pcbnew save): text-patches the board `setup` via-protection tokens to
`(capping yes)` / `(filling yes)`, matching the filled+capped via-in-pad
process ORDER_README orders from JLC (board-level, as JLC applies the
process board-wide). Kept as a text patch because it must survive as the
final bytes; any earlier pcbnew save would rewrite state.
"""
import sys
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BOARD = os.path.join(HERE, "..", "04_kicad",
                             "crow_recorder_central_v2.kicad_pcb")

GRID = [-1.65, -0.55, 0.55, 1.65]   # mm, U1-local EP thermal grid
VIA_SIZE_MM = 0.30
VIA_DRILL_MM = 0.15


def add_vias(bp):
    import pcbnew
    board = pcbnew.LoadBoard(bp)
    u1 = board.FindFootprintByReference("U1")
    if u1 is None:
        sys.exit("add_u1_thermal_vias: no U1 on the board")
    gnd = board.FindNet("GND")
    if gnd is None or gnd.GetNetCode() <= 0:
        sys.exit("add_u1_thermal_vias: no GND net")
    pos = u1.GetPosition()
    rot = u1.GetOrientationDegrees()
    import math
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    # refuse to double-add
    have = 0
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            dx = (t.GetPosition().x - pos.x) / 1e6
            dy = (t.GetPosition().y - pos.y) / 1e6
            if abs(dx) <= 2.0 and abs(dy) <= 2.0:
                have += 1
    if have:
        sys.exit(f"add_u1_thermal_vias: {have} vias already inside U1's EP "
                 f"window — refusing to double-add (regenerate the board "
                 f"first)")
    n = 0
    for gx in GRID:
        for gy in GRID:
            # KiCad footprint local -> board: rotate by orientation
            bx = pos.x + int(round((gx * c + gy * s) * 1e6))
            by = pos.y + int(round((-gx * s + gy * c) * 1e6))
            v = pcbnew.PCB_VIA(board)
            v.SetViaType(pcbnew.VIATYPE_THROUGH)
            v.SetPosition(pcbnew.VECTOR2I(bx, by))
            v.SetWidth(int(VIA_SIZE_MM * 1e6))
            v.SetDrill(int(VIA_DRILL_MM * 1e6))
            v.SetNet(gnd)
            board.Add(v)
            n += 1
    pcbnew.SaveBoard(bp, board)
    print(f"add_u1_thermal_vias: {n} GND {VIA_SIZE_MM}/{VIA_DRILL_MM} "
          f"thermal vias added under U1 EP at ({pos.x/1e6:.2f},"
          f"{pos.y/1e6:.2f}) rot {rot:g}")


def seal_fab_flags(bp):
    src = open(bp).read()
    out, n1 = re.subn(r"\(capping no\)", "(capping yes)", src)
    out, n2 = re.subn(r"\(filling no\)", "(filling yes)", out)
    if n1 + n2 == 0:
        if "(capping yes)" in out and "(filling yes)" in out:
            print("add_u1_thermal_vias --seal-fab-flags: already set")
            return
        sys.exit("add_u1_thermal_vias: no capping/filling tokens found in "
                 "the board setup — KiCad format changed, fix the patch")
    open(bp, "w").write(out)
    print(f"add_u1_thermal_vias --seal-fab-flags: capping({n1}) / "
          f"filling({n2}) -> yes (filled+capped via-in-pad, board-level)")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--seal-fab-flags"]
    bp = args[0] if args else DEFAULT_BOARD
    if "--seal-fab-flags" in sys.argv:
        seal_fab_flags(bp)
    else:
        add_vias(bp)
