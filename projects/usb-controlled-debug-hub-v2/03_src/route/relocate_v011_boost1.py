#!/usr/bin/env python3
"""Apply the bounded v0.1.1 HUB_BOOST1 placement/route repair.

The settled candidate already contains the reviewed USB and control routing.
Only R_BOOST1 moves: its former remote placement required a cross-board route
through the channel-4 USB field.  This delta is deliberately strict so it
cannot silently modify another footprint or retain stale BOOST1 copper.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.input))
    fp = board.FindFootprintByReference("R_BOOST1")
    if fp is None:
        raise SystemExit("R_BOOST1 is absent")

    old = fp.GetPosition()
    old_xy = (round(old.x / MM, 3), round(old.y / MM, 3))
    allowed = {(127.5, 62.0), (99.3, 61.25)}
    if old_xy not in allowed:
        raise SystemExit(f"unexpected R_BOOST1 position {old_xy}")

    for item in list(board.GetTracks()):
        if item.GetNetname() == "HUB_BOOST1":
            board.Remove(item)

    fp.SetPosition(point(99.3, 61.25))
    fp.SetOrientationDegrees(0)

    track = pcbnew.PCB_TRACK(board)
    track.SetStart(point(97.4125, 61.25))
    track.SetEnd(point(98.79, 61.25))
    track.SetWidth(round(0.18 * MM))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(board.FindNet("HUB_BOOST1"))
    board.Add(track)

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"moved R_BOOST1 {old_xy} -> (99.3, 61.25); replaced HUB_BOOST1 copper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
