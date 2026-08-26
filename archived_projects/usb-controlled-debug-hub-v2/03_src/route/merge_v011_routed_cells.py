#!/usr/bin/env python3
"""Merge only the reviewed v0.1.1 routed-cell nets into a clean route base.

The donor was routed from the same footprint/net identities.  USB and every
unchanged settled net deliberately remain owned by the clean base, avoiding
the duplicate seed-stub copper that a prior exploratory r0 candidate carried.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402


ROUTED_NETS = {
    *(f"VBUS{i}_SW" for i in range(1, 5)),
    *(f"ILIM{i}" for i in range(1, 5)),
    *(f"PWR_EN{i}" for i in range(1, 5)),
    "HUB_OCS2_N", "HUB_OCS4_N", "HUB_OCS5_N",
    "PD_VDD", "PD_PROTO", "PD_IN_UV", "PD_IN_OV", "PD_IN_ILIM",
    "PD_IN_DVDT", "PD_BOOT", "PD_FB", "VBUS_PD_SW",
}


def clone_track(board, source):
    if isinstance(source, pcbnew.PCB_VIA):
        item = pcbnew.PCB_VIA(board)
        item.SetPosition(source.GetPosition())
        item.SetWidth(source.GetWidth(source.GetLayer()))
        item.SetDrill(source.GetDrillValue())
        item.SetLayerPair(source.TopLayer(), source.BottomLayer())
    else:
        item = pcbnew.PCB_TRACK(board)
        item.SetStart(source.GetStart())
        item.SetEnd(source.GetEnd())
        item.SetWidth(source.GetWidth())
        item.SetLayer(source.GetLayer())
    item.SetNet(board.FindNet(source.GetNetname()))
    board.Add(item)
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("donor", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.base))
    donor = pcbnew.LoadBoard(str(args.donor))
    # Snapshot both SWIG containers before mutating either board.  Iterating a
    # second board after Remove() calls on the first can invalidate pcbnew's
    # transient container proxy even though the C++ board remains valid.
    donor_items = list(donor.GetTracks())
    missing = sorted(n for n in ROUTED_NETS
                     if not board.FindNet(n) or not donor.FindNet(n))
    if missing:
        raise SystemExit(f"routed-cell net(s) absent: {missing}")

    removed = 0
    for item in list(board.GetTracks()):
        if item.GetNetname() in ROUTED_NETS:
            board.Remove(item)
            removed += 1

    copied = 0
    for item in donor_items:
        if item.GetNetname() in ROUTED_NETS:
            clone_track(board, item)
            copied += 1

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"replaced {removed} base items with {copied} reviewed routed-cell items "
          f"across {len(ROUTED_NETS)} nets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
