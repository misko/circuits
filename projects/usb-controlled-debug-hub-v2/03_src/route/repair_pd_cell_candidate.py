#!/usr/bin/env python3
"""Rebase the settled route after the bounded PD-cell placement correction.

Only copper whose endpoint moved is replaced.  Every unrelated track and via
is copied from the already accepted full-route artifact by ``rebase_prefix``.
The output remains a candidate until full route acceptance promotes it.
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


def track(board, net: str, width: float, *points, layer: str = "F.Cu") -> None:
    for start, end in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetStart(point(*start)); item.SetEnd(point(*end))
        item.SetWidth(round(width * MM)); item.SetLayer(board.GetLayerID(layer))
        item.SetNet(board.FindNet(net)); board.Add(item)


def via(board, net: str, at, size: float = 0.46, drill: float = 0.20) -> None:
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(point(*at)); item.SetWidth(round(size * MM))
    item.SetDrill(round(drill * MM)); item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet(net)); board.Add(item)


def xy(item) -> tuple[float, float]:
    pos = item.GetPosition()
    return round(pos.x / MM, 3), round(pos.y / MM, 3)


def vector_xy(pos) -> tuple[float, float]:
    return round(pos.x / MM, 3), round(pos.y / MM, 3)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    board = pcbnew.LoadBoard(str(args.input))

    # These three small nets terminate only in the corrected PD cell.  Remove
    # the old realization completely so no stale stub can survive the rebase.
    for item in list(board.GetTracks()):
        if item.GetNetname() in {"PD_VDD", "PD_SW", "PD_BOOT"}:
            board.Remove(item)
            continue
        if item.GetNetname() != "GND":
            continue
        if isinstance(item, pcbnew.PCB_VIA) and xy(item) in {
                (39.46, 114.0), (53.48, 103.0)}:
            board.Remove(item)
            continue
        if not isinstance(item, pcbnew.PCB_VIA):
            ends = {vector_xy(item.GetStart()), vector_xy(item.GetEnd())}
            if ends == {(38.48, 114.0), (39.46, 114.0)}:
                board.Remove(item)

    # CH224K VDD resistor, three same-net supply pins and the now-local 1 uF.
    track(board, "PD_VDD", 0.18, (35.51, 110.8), (37.0, 111.0),
          (41.5, 109.0), (44.0, 107.0))
    track(board, "PD_VDD", 0.18, (44.0, 105.0), (44.0, 107.0),
          (45.32, 106.5))

    # TPS56637 switch/boot loop and direct connection into the moved inductor.
    track(board, "PD_SW", 0.25, (50.41, 108.75), (52.10, 108.75))
    track(board, "PD_SW", 0.60, (52.10, 108.75), (53.50, 109.50))
    track(board, "PD_SW", 1.50, (53.50, 109.50), (54.625, 110.50))
    track(board, "PD_SW", 0.25, (52.00, 109.00), (52.00, 111.48),
          (50.90, 111.48))
    track(board, "PD_BOOT", 0.18, (50.91, 109.40), (50.90, 110.52))
    track(board, "P5V_REG", 1.50, (61.375, 110.50), (62.875, 109.00))

    # The two relocated decoupler returns drop inside their GND lands.  The
    # complete 0.20 mm family is filled/capped by the release process contract.
    via(board, "GND", (46.28, 106.50))
    via(board, "GND", (52.78, 104.50))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: replaced only the moved PD-cell copper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
