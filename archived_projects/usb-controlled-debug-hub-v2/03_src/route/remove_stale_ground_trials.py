#!/usr/bin/env python3
"""Remove exact one-layer trial barrels before residual GND closure."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402

MM = 1_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path); ap.add_argument("output", type=Path)
    args = ap.parse_args(); board = pcbnew.LoadBoard(str(args.input))
    stale = {("P5V_REG", 83.82, 106.18),
             ("VBUS_PD_RAW", 26.11, 103.2)}
    remove = []
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_VIA):
            continue
        p = item.GetPosition()
        key = (item.GetNetname(), round(p.x / MM, 2), round(p.y / MM, 2))
        if key in stale:
            remove.append(item)
    for item in remove:
        board.Remove(item)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: removed {len(remove)} exact trial barrels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
