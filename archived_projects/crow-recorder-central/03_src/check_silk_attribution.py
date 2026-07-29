#!/usr/bin/env python3
"""Nearest-neighbor silk refdes ATTRIBUTION check (ported from crow-mic-pod's
red-verified generator check; pod learnings/verify.md, candidate-canon I13).

A legally de-collided F.SilkS refdes label can still land closer to a
NEIGHBOR's body than to its own part — the pod's fresh-eyes render review
read exactly that as a swap (C3/R3) on a shipped gerber. This checker flags
every visible silk refdes whose text is nearer another same-scale footprint's
bbox than its own part's bbox.

The central board ships the PROMOTED route artifact (silk baked in), so the
check runs on the FINAL 04_kicad board — the artifact that ships — not
inside generate_board.py's regen guard.

RED-FIXTURE HOOK (tests/README: a gate that cannot fail is worthless):
CRC_SILK_CHECK_POISON=<ref> relocates that ref's label onto its nearest
same-scale neighbor's body IN MEMORY (no save); the check must then FAIL.

Exit 0 = every visible silk refdes attributes to its own part.
"""
import json
import os
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
PCB = HERE.parent / "04_kicad" / "crow_recorder_central.kicad_pcb"
MM = pcbnew.ToMM

AREA_RATIO = 4.0   # confusion is a same-scale phenomenon (pod rule)
TOL = 0.05         # mm — ties go to the part


def bbox_dist(tx, ty, f):
    bb = f.GetBoundingBox(False, False)
    x0, y0 = MM(bb.GetLeft()), MM(bb.GetTop())
    x1, y1 = MM(bb.GetRight()), MM(bb.GetBottom())
    dx = max(x0 - tx, 0, tx - x1)
    dy = max(y0 - ty, 0, ty - y1)
    return (dx * dx + dy * dy) ** 0.5


def area(f):
    bb = f.GetBoundingBox(False, False)
    return max(MM(bb.GetWidth()) * MM(bb.GetHeight()), 1e-3)


def main():
    board = pcbnew.LoadBoard(str(PCB))
    fps = {f.GetReference(): f for f in board.GetFootprints()
           if not f.GetReference().startswith("H")}

    poison = os.environ.get("CRC_SILK_CHECK_POISON")
    if poison and poison in fps:
        me = fps[poison]
        best = min((f for r, f in fps.items() if r != poison
                    and area(f) <= AREA_RATIO * area(me)),
                   key=lambda f: bbox_dist(MM(me.GetPosition().x),
                                           MM(me.GetPosition().y), f))
        me.Reference().SetPosition(best.GetPosition())  # in memory only

    checked, skipped, ambiguous = 0, [], []
    for r, f in sorted(fps.items()):
        ref = f.Reference()
        if not ref.IsVisible() or ref.GetLayer() != pcbnew.F_SilkS:
            skipped.append(r)
            continue
        checked += 1
        tx, ty = MM(ref.GetPosition().x), MM(ref.GetPosition().y)
        own = bbox_dist(tx, ty, f)
        for r2, f2 in fps.items():
            if r2 == r or area(f2) > AREA_RATIO * area(f):
                continue
            d2 = bbox_dist(tx, ty, f2)
            if d2 < own - TOL:
                ambiguous.append((r, r2, round(own, 2), round(d2, 2)))
                break

    out = HERE.parent / "06_build" / "silk_attribution.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"checked": checked,
                               "skipped_not_on_silk": sorted(skipped),
                               "ambiguous": ambiguous}, indent=1))
    print(f"silk attribution: {checked} visible silk refdes checked, "
          f"{len(skipped)} not-on-silk skipped, {len(ambiguous)} ambiguous")
    if ambiguous:
        print("AMBIGUOUS (ref, nearer-neighbor, d_own, d_neighbor): "
              f"{ambiguous[:12]}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
