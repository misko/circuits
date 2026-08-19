#!/usr/bin/env python3
"""Remove exact obsolete v0.1.1 router reconciliation vias.

The exact v0.1.1 delta reconnects these control nets on only one layer at the
listed coordinates.  KiCad therefore reports the retained reconciliation vias
as dangling.  Power-distribution vias are intentionally absent from this list:
their zone contacts are valid and must not be inferred from track geometry.
Refuse any input whose exact net/coordinate differs.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402

MM = 1_000_000
TARGETS = {
    ("PWR_EN2", round(76.80 * MM), round(67.55 * MM)),
    ("PWR_EN2", round(90.65 * MM), round(79.00 * MM)),
    ("PWR_EN4", round(122.45 * MM), round(90.10 * MM)),
    ("PWR_EN4", round(129.50 * MM), round(84.70 * MM)),
    ("HUB_OCS5_N", round(114.30 * MM), round(70.05 * MM)),
    ("HUB_OCS5_N", round(124.85 * MM), round(57.50 * MM)),
    ("HUB_OCS5_N", round(141.50 * MM), round(61.50 * MM)),
}
TRACK_TARGETS = {
    ("HUB_OCS5_N", "B.Cu",
     round(114.30 * MM), round(70.05 * MM),
     round(116.80 * MM), round(67.55 * MM)),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.input))
    found = {}
    found_tracks = {}
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            pos = item.GetPosition()
            identity = (item.GetNetname(), pos.x, pos.y)
            if identity in TARGETS:
                if identity in found:
                    raise SystemExit(f"duplicate target via: {identity}")
                found[identity] = item
            continue
        a, b = item.GetStart(), item.GetEnd()
        layer = board.GetLayerName(item.GetLayer())
        forward = (item.GetNetname(), layer, a.x, a.y, b.x, b.y)
        reverse = (item.GetNetname(), layer, b.x, b.y, a.x, a.y)
        identity = forward if forward in TRACK_TARGETS else reverse
        if identity in TRACK_TARGETS:
            if identity in found_tracks:
                raise SystemExit(f"duplicate target track: {identity}")
            found_tracks[identity] = item
    missing = TARGETS - set(found)
    if missing:
        raise SystemExit(f"refusing incomplete cleanup target set: {sorted(missing)}")
    missing_tracks = TRACK_TARGETS - set(found_tracks)
    if missing_tracks:
        raise SystemExit(
            f"refusing incomplete cleanup track set: {sorted(missing_tracks)}")
    for item in found.values():
        board.Remove(item)
    for item in found_tracks.values():
        board.Remove(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(
        f"removed {len(found)} exact obsolete control-route vias and "
        f"{len(found_tracks)} dead-end track: "
        f"{args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
