#!/usr/bin/env python3
"""Close the intentionally new/relocated low-speed signal nets in v2."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402

MM = 1_000_000


def point(x, y):
    return pcbnew.VECTOR2I(round(x * MM), round(y * MM))


def track(board, net, width, *points, layer="F.Cu"):
    for a, b in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetStart(point(*a)); item.SetEnd(point(*b))
        item.SetWidth(round(width * MM)); item.SetLayer(board.GetLayerID(layer))
        item.SetNet(board.FindNet(net)); board.Add(item)


def via(board, net, at, size=0.46, drill=0.20):
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(point(*at)); item.SetWidth(round(size * MM))
    item.SetDrill(round(drill * MM)); item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet(net)); board.Add(item)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path); ap.add_argument("output", type=Path)
    args = ap.parse_args(); board = pcbnew.LoadBoard(str(args.input))

    # USB-C power CC paths.  CC2 uses a B.Cu underpass because connector and
    # controller pin order are reversed; CC1 stays direct and visible on F.Cu.
    track(board, "PD_CC1", 0.18, (27.32, 103.75), (33.0, 103.75),
          (35.0, 104.0), (38.0, 104.0))
    track(board, "PD_CC2", 0.18, (27.32, 106.75), (30.0, 106.75))
    via(board, "PD_CC2", (30.0, 106.75))
    # The high-current VBUS_PD spine now owns B.Cu in this cell.  Keep the
    # short low-speed CC2 order-correction on In2, outside every USB corridor.
    track(board, "PD_CC2", 0.18, (30.0, 106.75), (30.0, 105.5),
          (36.5, 105.5),
          (37.0, 103.0), layer="In2.Cu")
    via(board, "PD_CC2", (37.0, 103.0))
    track(board, "PD_CC2", 0.18, (37.0, 103.0), (38.0, 103.0))

    # Data-only USB-C configuration and VBUS-presence detector.
    track(board, "DATA_CC1", 0.18, (27.32, 55.75), (32.3, 55.75),
          (32.3, 53.0), (34.0, 52.51))
    track(board, "DATA_CC2", 0.18, (27.32, 58.75), (30.0, 58.75),
          (30.0, 62.0), (33.5, 63.51))
    track(board, "USB_UP_VBUS", 0.30, (27.32, 54.6), (29.0, 54.6),
          (29.0, 51.0), (31.0, 49.5), (39.0, 49.5))
    via(board, "USB_UP_VBUS", (39.0, 49.5))
    track(board, "USB_UP_VBUS", 0.30, (27.32, 59.4), (28.0, 59.4))
    via(board, "USB_UP_VBUS", (28.0, 59.4))
    track(board, "USB_UP_VBUS", 0.30, (28.0, 59.4), (29.5, 60.5),
          (29.5, 64.5), (39.0, 64.5), (39.0, 63.51),
          (39.0, 49.5), layer="B.Cu")
    via(board, "USB_UP_VBUS", (39.0, 63.51))
    track(board, "USB_UP_VBUS", 0.30, (39.0, 63.51), (38.0, 63.51))

    # Port-1 power-enable fabric: preserve the reviewed v1 trunk geometry but
    # replace its obsolete connector-field detour with a direct local launch.
    track(board, "PWR_EN1", 0.18, (46.55, 54.975), (47.0, 55.65),
          (51.0, 59.65), (52.0, 61.0), (52.0, 64.5),
          (50.0, 64.5), (50.0, 63.51))
    track(board, "PWR_EN1", 0.18, (51.0, 59.65), (62.2, 70.65), (62.2, 71.0),
          (62.85, 71.65))
    via(board, "PWR_EN1", (62.85, 71.65))
    track(board, "PWR_EN1", 0.18, (62.85, 71.65), (63.2, 71.65),
          (71.45, 79.9), (98.55, 79.9), (104.0, 85.35), layer="B.Cu")
    via(board, "PWR_EN1", (104.0, 85.35))
    track(board, "PWR_EN1", 0.18, (101.1375, 85.35), (104.0, 85.35))
    track(board, "PWR_EN1", 0.18, (104.0, 85.35), (106.15, 87.5),
          (106.15, 88.7), (106.55, 89.1), (107.25, 89.1),
          (107.85, 89.7), layer="B.Cu")
    via(board, "PWR_EN1", (107.85, 89.7))
    track(board, "PWR_EN1", 0.18, (107.85, 89.7), (113.5, 84.05),
          (117.1375, 84.05))

    # Crystal shunt capacitors were moved but the crystal/resistor core was
    # retained; these are deliberately short, branch-only connections.
    track(board, "XTAL1", 0.18, (82.99, 52.0), (83.0, 54.0),
          (86.0, 54.0), (85.52, 52.0))
    track(board, "XTAL1", 0.18, (86.0, 54.0), (86.5, 55.4),
          (87.4, 56.35))
    track(board, "XTAL2", 0.18, (84.01, 52.0), (85.0, 50.0), (88.02, 50.0))
    track(board, "XTAL2", 0.18, (88.02, 50.0), (89.0, 51.0),
          (89.6, 54.65))

    # The connector-local VBUS divider drives a low-speed hub detector.  Use
    # the same bounded In2 crossing strategy as v1 so the long detector route
    # does not cut any USB pair on the outer layers.
    track(board, "HUB_VBUS_SENSE", 0.18, (38.0, 62.49), (36.5, 62.49),
          (36.5, 68.0), (38.0, 68.0), (38.0, 66.51))
    via(board, "HUB_VBUS_SENSE", (36.5, 68.0))
    track(board, "HUB_VBUS_SENSE", 0.18, (36.5, 68.0), (40.0, 64.0),
          (75.0, 64.0), (79.75, 63.0), (83.5, 66.75),
          (85.0, 66.75), (88.25, 63.5), (95.25, 63.5),
          (95.5, 63.25), (98.0, 63.25), (98.15, 63.35), layer="In2.Cu")
    via(board, "HUB_VBUS_SENSE", (98.15, 63.35))
    track(board, "HUB_VBUS_SENSE", 0.18, (98.15, 63.35), (98.05, 63.25),
          (97.4125, 63.25))

    # Close the intentional 1 mm aggregate-eFuse input neck to its P5V_REG
    # zone/track launch.
    track(board, "P5V_REG", 0.30, (84.77, 108.9), (84.77, 110.0))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: closed v2 low-speed signal set")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
