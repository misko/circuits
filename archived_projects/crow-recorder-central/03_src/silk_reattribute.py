#!/usr/bin/env python3
"""ONE-TIME fixup (route_fixups.py precedent: applied once to the PROMOTED
03_src/route/final.kicad_pcb, baked in, committed — NOT re-run by
rebuild_all.sh): attribution-aware re-placement of ambiguous silk refdes.

Port of the crow-mic-pod red-verified nearest-neighbor attribution rule
(pod learnings/verify.md): a de-collided label that lands nearer a
same-scale NEIGHBOR's body than its own part reads as belonging to the
neighbor (the pod's C3/R3 swap on a shipped gerber). The adopted archive
board measured 63/231 such labels (06_build/silk_attribution.json,
2026-07-21) — the archive's de-collision objective was collision-freedom
only.

For each ambiguous visible F.SilkS refdes (per check_silk_attribution.py's
exact metric):
  - try candidate slots ordered nearest-to-own-body first: on the OWN body
    (audit I10b allows own-body overlap; ideal for the RJ45 jacks), then
    rings around the own bbox perimeter;
  - a slot is accepted iff: inside the outline; ATTRIBUTION-correct with
    margin (own dist <= every same-scale neighbor dist - 0.15mm); no bbox
    hit vs any pad, any OTHER footprint body (audit I10b), or any other
    silk text;
  - no slot: R/C refs are HIDDEN (waived to F.Fab — the fab copy exists)
    and recorded in 03_src/rules/silk_attribution_waivers.json (committed;
    generate_board.py merges it into 06_build/refdes_waiver.json for audit
    I10); any other ref class raises — must be placed, widen slots.

Gate afterwards: full rebuild -> check_silk_attribution.py == 0 ambiguous,
audit 0 FAIL, DRC 0 violations / 2 ADR-0010-waived unconnected / 0 parity.
"""
import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
PCB = HERE / "route" / "final.kicad_pcb"
WAIVERS = HERE / "rules" / "silk_attribution_waivers.json"
MM = pcbnew.ToMM

AREA_RATIO = 4.0
CHECK_TOL = 0.05      # the checker's rule: ambiguous iff d2 < own - 0.05
PLACE_MARGIN = 0.15   # stricter at placement time for stability
INFL = 0.12           # obstacle inflation, mm
EDGE_MARGIN = 0.3


def bx(bb):
    return (MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom()))


def hit(a, b, infl=0.0):
    return not (a[2] + infl <= b[0] or b[2] + infl <= a[0]
                or a[3] + infl <= b[1] or b[3] + infl <= a[1])


def bbox_dist_pt(tx, ty, box):
    dx = max(box[0] - tx, 0, tx - box[2])
    dy = max(box[1] - ty, 0, ty - box[3])
    return (dx * dx + dy * dy) ** 0.5


def main():
    board = pcbnew.LoadBoard(str(PCB))
    edges = board.GetBoardEdgesBoundingBox()
    X0, Y0 = MM(edges.GetX()) + EDGE_MARGIN, MM(edges.GetY()) + EDGE_MARGIN
    X1 = MM(edges.GetX()) + MM(edges.GetWidth()) - EDGE_MARGIN
    Y1 = MM(edges.GetY()) + MM(edges.GetHeight()) - EDGE_MARGIN

    fps = {f.GetReference(): f for f in board.GetFootprints()
           if not f.GetReference().startswith("H")}
    bodies = {r: bx(f.GetBoundingBox(False, False)) for r, f in fps.items()}
    areas = {r: max((b[2] - b[0]) * (b[3] - b[1]), 1e-3)
             for r, b in bodies.items()}

    pad_obst = [bx(p.GetBoundingBox()) for f in board.GetFootprints()
                for p in f.Pads()]
    SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)
    text_obst = {}   # id -> bbox, so a moved label updates its own entry
    for t in board.GetDrawings():
        if isinstance(t, pcbnew.PCB_TEXT) and t.GetLayer() in SILK:
            text_obst[("board", id(t))] = bx(t.GetBoundingBox())
    for r, f in fps.items():
        for tag, fld in (("ref", f.Reference()), ("val", f.Value())):
            if fld.IsVisible() and fld.GetLayer() in SILK:
                text_obst[(tag, r)] = bx(fld.GetBoundingBox())

    def ambiguous_at(r, tx, ty, margin):
        own = bbox_dist_pt(tx, ty, bodies[r])
        for r2 in fps:
            if r2 == r or areas[r2] > AREA_RATIO * areas[r]:
                continue
            if bbox_dist_pt(tx, ty, bodies[r2]) < own - margin:
                return True
        return False

    def candidates(r, w, h):
        l, t, rr, b = bodies[r]
        out = []
        # on own body (I10b permits own-body overlap) — centers on a grid
        if (rr - l) > w + 0.4 and (b - t) > h + 0.4:
            for fx in (0.5, 0.3, 0.7):
                for fy in (0.5, 0.3, 0.7):
                    out.append((l + fx * (rr - l), t + fy * (b - t)))
        # perimeter rings, nearest first
        for m in (0.18, 0.3, 0.45, 0.6, 0.8, 1.0, 1.25, 1.55, 1.9, 2.3):
            for fx in (0.5, 0.3, 0.7, 0.12, 0.88, -0.1, 1.1):
                out.append((l + fx * (rr - l), t - m - h / 2))   # N
                out.append((l + fx * (rr - l), b + m + h / 2))   # S
            for fy in (0.5, 0.25, 0.75, 0.0, 1.0):
                out.append((l - m - w / 2, t + fy * (b - t)))    # W
                out.append((rr + m + w / 2, t + fy * (b - t)))   # E
            # diagonal corners
            for cx in (l - m - w / 2, rr + m + w / 2):
                for cy in (t - m - h / 2, b + m + h / 2):
                    out.append((cx, cy))
        return out

    moved, hidden, kept = [], [], 0
    for r in sorted(fps):
        f = fps[r]
        ref = f.Reference()
        if not ref.IsVisible() or ref.GetLayer() != pcbnew.F_SilkS:
            continue
        tx, ty = MM(ref.GetPosition().x), MM(ref.GetPosition().y)
        if not ambiguous_at(r, tx, ty, CHECK_TOL):
            kept += 1
            continue
        tb = bx(ref.GetBoundingBox())
        w, h = tb[2] - tb[0], tb[3] - tb[1]
        placed = False
        for cx, cy in candidates(r, w, h):
            ref.SetPosition(pcbnew.VECTOR2I_MM(cx, cy))
            cand = bx(ref.GetBoundingBox())
            if not (X0 < cand[0] and cand[2] < X1 and Y0 < cand[1] and cand[3] < Y1):
                continue
            ccx = (cand[0] + cand[2]) / 2
            ccy = (cand[1] + cand[3]) / 2
            if ambiguous_at(r, ccx, ccy, -PLACE_MARGIN):
                continue
            if any(hit(cand, o, INFL) for o in pad_obst):
                continue
            if any(hit(cand, bodies[r2], 0.0) for r2 in fps if r2 != r):
                continue   # audit I10b: never under ANOTHER body
            if any(hit(cand, o, INFL) for k, o in text_obst.items()
                   if k != ("ref", r)):
                continue
            text_obst[("ref", r)] = cand
            moved.append((r, round(cx - (tb[0] + w / 2), 1),
                          round(cy - (tb[1] + h / 2), 1)))
            placed = True
            break
        if not placed:
            ref.SetPosition(pcbnew.VECTOR2I_MM(tx, ty))   # restore
            # waivable classes: R/C (fleet rule) + TP when its functional
            # rail label (add_silk_fn 'TP <rail>') is already on silk —
            # TP11 is ringed by 6 closer same-scale passives at ~1.5mm,
            # no attribution-correct slot exists (measured 2026-07-21)
            if r[0] in "RC" or r.startswith("TP"):
                ref.SetVisible(False)
                del text_obst[("ref", r)]
                hidden.append(r)
            else:
                raise RuntimeError(f"{r}: no attribution-correct slot and "
                                   f"not R/C-waivable — widen candidates")

    WAIVERS.write_text(json.dumps(sorted(hidden), indent=0) + "\n")
    board.Save(str(PCB))
    print(f"silk re-attribution: {kept} already correct, {len(moved)} moved, "
          f"{len(hidden)} hidden->Fab (waivers file updated)")
    print("moved:", [m[0] for m in moved])
    print("hidden:", hidden)
    return 0


if __name__ == "__main__":
    sys.exit(main())
