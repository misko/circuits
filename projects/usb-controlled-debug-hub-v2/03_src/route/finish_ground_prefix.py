#!/usr/bin/env python3
"""Close the small residual GND set after the bounded generic stitch pass.

These sites are explicit because broad obstacle-aware A* recovery was both
slow and opaque.  Unchanged USB-switch returns reuse the exact v1 dogbones;
all other sites are direct plane drops or one local package connection.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402

MM = 1_000_000


def point(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(round(x * MM), round(y * MM))


def track(board, a, b, width=0.25, layer="F.Cu") -> None:
    item = pcbnew.PCB_TRACK(board)
    item.SetStart(point(*a)); item.SetEnd(point(*b))
    item.SetWidth(round(width * MM)); item.SetLayer(board.GetLayerID(layer))
    item.SetNet(board.FindNet("GND")); board.Add(item)


def via(board, at, size=0.46, drill=0.20) -> None:
    target = point(*at)
    for existing in board.GetTracks():
        if (isinstance(existing, pcbnew.PCB_VIA)
                and existing.GetNetname() == "GND"
                and existing.GetPosition() == target):
            return
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(target); item.SetWidth(round(size * MM))
    item.SetDrill(round(drill * MM)); item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet("GND")); board.Add(item)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path); ap.add_argument("output", type=Path)
    args = ap.parse_args(); board = pcbnew.LoadBoard(str(args.input))

    # TPS56637 exposed GND land to the already-plane-served pin-3 land.
    track(board, (48.64, 108.25), (49.83, 108.25), 0.25)

    # Exact direct plane drops.  All unchanged sites are present in the v1
    # DRC-clean board; the two new power-cell sites are separately regraded.
    for at in ((50.48, 69.0), (54.51, 85.0),
               (90.48, 71.0), (102.48, 68.0),
               (105.51, 66.5), (105.51, 68.0), (105.51, 69.5),
               (110.51, 70.0),
               (113.51, 70.0), (114.51, 92.0), (125.01, 62.0),
               (125.48, 84.0)):
        via(board, at)

    # The aggregate-eFuse GND land is boxed between ILIM and DVDT.  Escape
    # through the measured gap before dropping to the planes; a via in this
    # narrow land misses the ILIM clearance by 0.01 mm.
    track(board, (85.91, 109.23), (88.0, 109.4), 0.18)
    track(board, (88.0, 109.4), (88.0, 110.5), 0.18)
    track(board, (88.0, 110.5), (91.6, 110.5), 0.18)
    via(board, (91.6, 110.5))

    # Exact v1 hub-core decoupler dogbone, retained because the hub-side
    # signal fanout leaves no safe via-in-pad at C_HUB_18.
    track(board, (93.25, 71.88), (92.5, 71.8), 0.25)
    via(board, (92.5, 71.8))

    # Exact island scan identified this legal cross-plane stitch at the small
    # hub-core In2 remnant; unlike a coarse grid site it is derived from the
    # filled-zone geometry.
    via(board, (89.15, 57.84))

    # U_AND_PWR.7 owns the one remaining filled F.Cu island.  Reuse its exact
    # v1 package-axis dogbone to the unobstructed plane at x=102.58.
    track(board, (101.1375, 87.95), (102.58, 87.95), 0.25)
    via(board, (102.58, 87.95))

    # Bottom-side FSUSB42 ground lands: follow the long land axis and change
    # layer only in the same open fields proven by the v1 exact board.
    for a, mid, end in (
        ((59.1, 44.0), (60.3, 44.0), (61.0, 43.0)),
        ((84.1, 44.0), (85.3, 44.0), (86.0, 43.0)),
        ((102.9, 45.0), (104.35, 45.0), (104.35, 45.0)),
        ((123.9, 45.0), (125.35, 45.0), (125.35, 45.0)),
    ):
        track(board, a, mid, 0.18, "B.Cu")
        if mid != end:
            track(board, mid, end, 0.18, "B.Cu")
        via(board, end)

    # C_HUB_18PLL sits over the P3 B.Cu pair, so a local via is forbidden.
    # Preserve its short F.Cu spoke into the surrounding top ground pour.
    for a, b in (((90.2, 57.92), (89.97, 57.7)),
                 ((89.97, 57.7), (88.77, 57.7)),
                 ((88.77, 57.7), (88.47, 57.4))):
        track(board, a, b, 0.30, "F.Cu")

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: explicit residual GND closure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
