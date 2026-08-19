#!/usr/bin/env python3
"""Replay a reviewed copper delta onto a regenerated compatible base board."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402


def xy(p):
    return p.x, p.y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", type=Path)
    ap.add_argument("reviewed", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    board = pcbnew.LoadBoard(str(args.base))
    reviewed = pcbnew.LoadBoard(str(args.reviewed))
    segs = {
        (t.GetNetname(), t.GetLayer(), t.GetWidth(), xy(t.GetStart()), xy(t.GetEnd()))
        for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)
    }
    vias = {
        (t.GetNetname(), xy(t.GetPosition()), t.GetDrillValue())
        for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
    }
    ns = nv = 0
    for item in reviewed.GetTracks():
        net = item.GetNetname()
        if not board.FindNet(net):
            raise SystemExit(f"reviewed copper net absent from new base: {net}")
        if isinstance(item, pcbnew.PCB_VIA):
            key = (net, xy(item.GetPosition()), item.GetDrillValue())
            if key in vias:
                continue
            copy = pcbnew.PCB_VIA(board)
            copy.SetPosition(item.GetPosition())
            copy.SetWidth(item.GetWidth(item.GetLayer()))
            copy.SetDrill(item.GetDrillValue())
            copy.SetLayerPair(item.TopLayer(), item.BottomLayer())
            copy.SetNet(board.FindNet(net))
            board.Add(copy)
            vias.add(key)
            nv += 1
            continue
        key = (net, item.GetLayer(), item.GetWidth(),
               xy(item.GetStart()), xy(item.GetEnd()))
        reverse = (net, item.GetLayer(), item.GetWidth(),
                   xy(item.GetEnd()), xy(item.GetStart()))
        if key in segs or reverse in segs:
            continue
        copy = pcbnew.PCB_TRACK(board)
        copy.SetStart(item.GetStart())
        copy.SetEnd(item.GetEnd())
        copy.SetWidth(item.GetWidth())
        copy.SetLayer(item.GetLayer())
        copy.SetNet(board.FindNet(net))
        board.Add(copy)
        segs.add(key)
        ns += 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: replayed {ns} segments/{nv} vias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
