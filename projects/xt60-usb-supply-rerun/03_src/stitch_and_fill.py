#!/usr/bin/env python3
"""Post-routing stitch pass + zone fill.

Zone-semantics fact (skill, 2026-07-16): a pad inside a HIGHER-priority
foreign pour on its layer is DISCONNECTED from its own prio-0 plane fill —
it needs a rescue via to its net's inner plane (GND -> In1). This pass:

1. adds one GND via next to every SMD GND pad (dedupe radius 1.5 mm),
   exact-collide-verified against all copper (both layers, holes),
2. adds a grid of GND stitching vias bonding the F.Cu/B.Cu GND pours to
   the In1 plane in free areas,
3. fills all zones and saves.

Runs inside rebuild_all.sh after routing import. Idempotent: seeds the
dedupe set from the board's existing vias (skill: via_site_ok approves
stacked vias otherwise).
"""
import math
import sys
from pathlib import Path

import pcbnew
from pcbnew import VECTOR2I, FromMM

PROJ = Path(__file__).resolve().parent.parent
BOARD = PROJ / "04_kicad" / "xt60-usb-supply.kicad_pcb"
SKILLS = PROJ.parent.parent / "skills" / "kicad-pcb" / "scripts"
sys.path.insert(0, str(SKILLS))
from pcb_toolkit import Toolkit  # noqa: E402

VIA_D, VIA_DRILL, CLR = 0.6, 0.3, 0.15
GRID = 6.0  # mm stitching grid


def main():
    board = pcbnew.LoadBoard(str(BOARD))
    tk = Toolkit(board)
    gnd = board.FindNet("GND")
    assert gnd and gnd.GetNetCode() > 0

    placed = []   # (x_mm, y_mm) of vias we know about
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            placed.append((p.x / 1e6, p.y / 1e6))

    def too_close(x, y, r=1.5):
        return any((x - a) ** 2 + (y - b) ** 2 < r * r for a, b in placed)

    def try_via(x, y):
        if too_close(x, y):
            return False
        if not tk.via_site_ok(x, y, gnd.GetNetCode(), size=VIA_D,
                              drill=VIA_DRILL):
            return False
        tk.add_via(x, y, gnd, size=VIA_D, drill=VIA_DRILL)
        placed.append((x, y))
        return True

    # 1. rescue via per SMD GND pad
    n_rescue = 0
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND":
                continue
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            c = pad.GetPosition()
            cx, cy = c.x / 1e6, c.y / 1e6
            if too_close(cx, cy, 2.5):
                continue  # a nearby GND via already serves this cluster
            for r in (1.0, 1.4, 1.9):
                hit = False
                for k in range(8):
                    a = k * math.pi / 4
                    if try_via(cx + r * math.cos(a), cy + r * math.sin(a)):
                        n_rescue += 1
                        hit = True
                        break
                if hit:
                    break

    # 2. stitching grid
    n_grid = 0
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0 = bb.GetLeft() / 1e6 + 3, bb.GetTop() / 1e6 + 3
    x1, y1 = bb.GetRight() / 1e6 - 3, bb.GetBottom() / 1e6 - 3
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            if try_via(x, y):
                n_grid += 1
            x += GRID
        y += GRID

    board.Save(str(BOARD))

    # 3. fill in a fresh load (save/reload discipline)
    board2 = pcbnew.LoadBoard(str(BOARD))
    filler = pcbnew.ZONE_FILLER(board2)
    filler.Fill(board2.Zones())
    board2.Save(str(BOARD))
    print(f"STITCH: {n_rescue} rescue vias, {n_grid} grid vias; zones filled")


if __name__ == "__main__":
    main()
