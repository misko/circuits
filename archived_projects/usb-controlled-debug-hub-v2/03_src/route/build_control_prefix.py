#!/usr/bin/env python3
"""Replay only pad-identical v1 low-speed copper onto the exact v2 power prefix.

The reviewed v1 board is evidence for unchanged functional-core geometry, not
authority for the new USB-C or power cells.  A net is eligible only when every
connected footprint/pad identity and absolute pad position is identical on
both boards, the v2 checkpoint has no copper on that net, and it is neither a
ground/unconnected net nor one of the explicitly redesigned domains.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402


EXCLUDED = {
    "GND", "UP_HUB_P", "UP_HUB_N", "XTAL1", "XTAL2",
    "P1_HUB_P", "P1_HUB_N", "P1_PORT_P", "P1_PORT_N",
    "P2_HUB_P", "P2_HUB_N", "P2_PORT_P", "P2_PORT_N",
    "P3_HUB_P", "P3_HUB_N", "P3_PORT_P", "P3_PORT_N",
    "P4_HUB_P", "P4_HUB_N", "P4_PORT_P", "P4_PORT_N",
    "MGMT_P", "MGMT_N", "P5V_PROTECTED", "3V3_MAIN",
    "SW_3V3", "BST_3V3", "AGG_UV", "AGG_OV", "AGG_TIMER",
    "AGG_DVDT", "AGG_ILIM", "USB_UP_VBUS", "PWR_EN1",
}


def xy(pos):
    return pos.x, pos.y


def mm_xy(pos):
    return pos.x / 1_000_000, pos.y / 1_000_000


def in_obsolete_3v3_cell(pos):
    x, y = mm_xy(pos)
    return 60.0 <= x <= 84.0 and 85.0 <= y <= 97.0


def pad_signatures(board):
    signatures = defaultdict(list)
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if not net:
                continue
            signatures[net].append((
                footprint.GetReference(), pad.GetNumber(),
                xy(pad.GetPosition()), pad.GetLayerSet().FmtHex()))
    return {net: tuple(sorted(rows)) for net, rows in signatures.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("reviewed", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.input))
    reviewed = pcbnew.LoadBoard(str(args.reviewed))
    current_sig, reviewed_sig = pad_signatures(board), pad_signatures(reviewed)
    current_copper = {item.GetNetname() for item in board.GetTracks()}
    eligible = {
        net for net, signature in current_sig.items()
        if net in reviewed_sig and reviewed_sig[net] == signature
        and net not in EXCLUDED and not net.startswith("unconnected-")
        and net not in current_copper
    }

    segments = vias = 0
    for item in reviewed.GetTracks():
        net = item.GetNetname()
        retained_3v3 = net == "3V3_MAIN"
        if net not in eligible and not retained_3v3:
            continue
        if retained_3v3:
            # Remove the former regulator/inductor/output-cap cell.  The long
            # y=89.25 distribution spine remains as the exact v2 join target.
            if isinstance(item, pcbnew.PCB_VIA):
                if in_obsolete_3v3_cell(item.GetPosition()):
                    continue
            else:
                a, b = mm_xy(item.GetStart()), mm_xy(item.GetEnd())
                exact_spine = ({(round(a[0], 2), round(a[1], 2)),
                                (round(b[0], 2), round(b[1], 2))}
                               == {(83.8, 89.25), (105.6, 89.25)})
                # The v2 regulator join authors only the used 100.0--105.6
                # interval.  Retaining the old 83.8-mm tail leaves a genuine
                # dangling bus end with no v2 load or branch.
                if exact_spine:
                    continue
                if not exact_spine and (in_obsolete_3v3_cell(item.GetStart())
                                        or in_obsolete_3v3_cell(item.GetEnd())):
                    continue
        if isinstance(item, pcbnew.PCB_VIA):
            copy = pcbnew.PCB_VIA(board)
            copy.SetPosition(item.GetPosition())
            copy.SetWidth(item.GetWidth(item.GetLayer()))
            copy.SetDrill(item.GetDrillValue())
            copy.SetLayerPair(item.TopLayer(), item.BottomLayer())
            copy.SetNet(board.FindNet(net))
            board.Add(copy)
            vias += 1
        else:
            copy = pcbnew.PCB_TRACK(board)
            copy.SetStart(item.GetStart())
            copy.SetEnd(item.GetEnd())
            copy.SetWidth(item.GetWidth())
            copy.SetLayer(item.GetLayer())
            copy.SetNet(board.FindNet(net))
            board.Add(copy)
            segments += 1

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: replayed {segments} segments/{vias} vias "
          f"on {len(eligible)} pad-identical nets plus the retained 3V3 tree")
    print("eligible nets: " + " ".join(sorted(eligible)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
