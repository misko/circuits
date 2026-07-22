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
    tk = Toolkit(board, clearance_mm=0.15)
    gnd = board.FindNet("GND")
    assert gnd and gnd.GetNetCode() > 0

    # foreign priority-1 pour outlines: a GND via inside one is avoided by
    # the fill (clearance) and just dangles - never place grid vias there
    foreign = [z for z in board.Zones()
               if not z.GetIsRuleArea() and z.GetAssignedPriority() >= 1
               and z.GetNetname() != "GND"
               and z.GetFirstLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)]

    def in_foreign_pour(x, y, margin=0.6, own="GND"):
        pt = pcbnew.VECTOR2I(FromMM(x), FromMM(y))
        # Contains for deep-inside points; Collide(pt, margin) is an
        # edge-proximity test and can miss interior points
        return any(z.Outline().Contains(pt)
                   or z.Outline().Collide(pt, FromMM(margin))
                   for z in foreign if z.GetNetname() != own)

    def not_near_edge(zone, x, y, margin=0.6):
        pt = pcbnew.VECTOR2I(FromMM(x), FromMM(y))
        o = zone.Outline()
        if not o.Contains(pt):
            return False
        # near-edge test: any outline segment within margin
        return not o.CollideEdge(pt, None, FromMM(margin))

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

    # 1. rescue via per SMD GND pad. Inside a foreign pour the via alone
    # is useless (fill avoids it): add a connecting GND track pad->via,
    # collide-checked.
    n_rescue = 0
    unrescued = []
    # group same-numbered pad pieces (a multi-piece QFN belly pad is ONE
    # electrical pad: pieces are net-tied through the package)
    groups = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != "GND":
                continue
            if pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            groups.setdefault((fp.GetReference(), pad.GetNumber()),
                              []).append(pad)
    for (ref, num), pieces in groups.items():
        for piece in pieces:
            fpref = ref
            pad = piece
            c = pad.GetPosition()
            cx, cy = c.x / 1e6, c.y / 1e6
            served = False
            for pc in pieces:
                bb = pc.GetBoundingBox()
                if any(bb.GetLeft() / 1e6 <= vx <= bb.GetRight() / 1e6 and
                       bb.GetTop() / 1e6 <= vy <= bb.GetBottom() / 1e6
                       for vx, vy in placed):
                    served = True
            if served:
                break  # some piece of this pad group carries a via
            inside = in_foreign_pour(cx, cy, 0.0)
            if not inside and too_close(cx, cy, 2.5):
                continue  # nearby GND via + prio-0 pour serve this cluster
            done = False
            for r in (1.0, 1.4, 1.9, 2.4, 2.9, 3.4):
                for k in range(16):
                    a = k * math.pi / 8
                    x, y = cx + r * math.cos(a), cy + r * math.sin(a)
                    if too_close(x, y):
                        continue
                    if not tk.via_site_ok(x, y, gnd.GetNetCode(),
                                          size=VIA_D, drill=VIA_DRILL):
                        continue
                    if inside:
                        # need the track too (0.3mm, F.Cu, pad->via)
                        if tk.collides(cx, cy, x, y, 0.3,
                                       gnd.GetNetCode(), pcbnew.F_Cu):
                            continue
                        tk.add_seg(cx, cy, x, y, gnd, pcbnew.F_Cu, 0.3)
                    tk.add_via(x, y, gnd, size=VIA_D, drill=VIA_DRILL)
                    placed.append((x, y))
                    n_rescue += 1
                    done = True
                    break
                if done:
                    break
            if done:
                break  # one rescue serves the whole pad group
            if not done and inside:
                unrescued.append(f"{fpref}.{num}")
    if unrescued:
        raise SystemExit(f"ERROR: GND pads inside foreign pours with no "
                         f"legal rescue via+track: {unrescued}")

    # 1b. power-net stitching: bond each In2 patch to its F.Cu pour with
    # a via grid (sites must lie well inside the SAME-net F.Cu pour and
    # clear of everything else)
    own_pours = {}
    for z in board.Zones():
        if (not z.GetIsRuleArea() and z.GetAssignedPriority() >= 1
                and z.GetFirstLayer() == pcbnew.F_Cu):
            own_pours.setdefault(z.GetNetname(), []).append(z)
    n_pwr = 0
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetFirstLayer() != pcbnew.In2_Cu:
            continue
        netname = z.GetNetname()
        if netname == "GND":
            continue
        net = board.FindNet(netname)
        bb = z.GetBoundingBox()
        zx0, zy0 = bb.GetLeft() / 1e6 + 1, bb.GetTop() / 1e6 + 1
        zx1, zy1 = bb.GetRight() / 1e6 - 1, bb.GetBottom() / 1e6 - 1
        yy = zy0
        while yy <= zy1:
            xx = zx0
            while xx <= zx1:
                pt = pcbnew.VECTOR2I(FromMM(xx), FromMM(yy))
                # -0.6 margin: strictly inside own F.Cu pour
                inside_own = any(
                    p2.Outline().Collide(pt, FromMM(-0.6)) if False else
                    (p2.Outline().Contains(pt) and
                     not_near_edge(p2, xx, yy))
                    for p2 in own_pours.get(netname, []))
                if (inside_own and not in_foreign_pour(xx, yy, own=netname)
                        and not too_close(xx, yy)
                        and tk.via_site_ok(xx, yy, net.GetNetCode(),
                                           size=VIA_D, drill=VIA_DRILL)):
                    tk.add_via(xx, yy, net, size=VIA_D, drill=VIA_DRILL)
                    placed.append((xx, yy))
                    n_pwr += 1
                xx += 5.0
            yy += 5.0
    print(f"STITCH: {n_pwr} power vias (In2 patches)")

    # 2. stitching grid
    n_grid = 0
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0 = bb.GetLeft() / 1e6 + 3, bb.GetTop() / 1e6 + 3
    x1, y1 = bb.GetRight() / 1e6 - 3, bb.GetBottom() / 1e6 - 3
    y = y0
    while y <= y1:
        x = x0
        while x <= x1:
            if not in_foreign_pour(x, y):
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
