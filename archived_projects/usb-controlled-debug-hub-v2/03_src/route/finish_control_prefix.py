#!/usr/bin/env python3
"""Add v2-local regulator and control copper to the replayed core prefix."""
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
        item.SetWidth(round(width * MM))
        item.SetLayer(board.GetLayerID(layer))
        item.SetNet(board.FindNet(net)); board.Add(item)


def via(board, net, at, size=0.46, drill=0.20):
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(point(*at)); item.SetWidth(round(size * MM))
    item.SetDrill(round(drill * MM))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet(net)); board.Add(item)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.input))

    # Retained AP63203 3V3 converter, relocated with the new power cell.
    track(board, "SW_3V3", 0.40, (98.138, 101.0), (99.2, 101.0),
          (99.68, 101.48), (100.1, 101.48), (100.6, 101.48),
          (101.6, 101.0))
    track(board, "BST_3V3", 0.40, (98.138, 100.05), (99.2, 100.05),
          (99.68, 100.52), (100.1, 100.52))
    track(board, "3V3_MAIN", 0.40, (104.6, 101.0), (107.525, 101.0),
          (107.525, 106.0))
    track(board, "3V3_MAIN", 0.18, (95.862, 100.05), (94.8, 99.0),
          (94.8, 97.5), (104.6, 97.5), (104.6, 101.0))
    # Stay left of the inherited command fanout and use a very short B.Cu
    # underpass only at DATA_OK1; the protected 5 V B.Cu trunk is farther
    # south and remains untouched.
    track(board, "3V3_MAIN", 0.40, (107.525, 106.0), (108.5, 105.0),
          (108.5, 99.0))
    via(board, "3V3_MAIN", (108.5, 99.0))
    track(board, "3V3_MAIN", 0.40, (108.5, 99.0), (100.0, 99.0),
          (100.0, 90.0), layer="B.Cu")
    via(board, "3V3_MAIN", (100.0, 90.0))
    track(board, "3V3_MAIN", 0.40, (100.0, 90.0), (100.0, 89.25),
          (105.6, 89.25))

    # TPS56637 quiet feedback network. The high-impedance FB node remains
    # beside pin 2; only the P5V_REG Kelvin sense legs run around the cell's
    # quiet board-edge perimeter.
    track(board, "PD_FB_TOP", 0.18, (44.51, 111.0), (45.99, 111.0))
    track(board, "PD_FB", 0.18, (48.64, 107.75), (47.3, 107.75),
          (47.3, 110.2), (47.01, 111.0), (48.49, 111.0))
    track(board, "PD_FB", 0.18, (47.01, 111.0), (47.0, 113.5),
          (46.98, 113.5))
    track(board, "PD_FF", 0.18, (44.51, 113.5), (46.02, 113.5))
    track(board, "P5V_REG", 0.18, (63.0, 116.0), (63.0, 117.5),
          (42.8, 117.5), (42.8, 113.5), (43.49, 113.5))
    track(board, "P5V_REG", 0.18, (42.8, 113.5), (42.8, 111.0),
          (43.49, 111.0))

    # Buck UVLO divider. The midpoint crosses below the quiet-feedback bundle
    # on B.Cu rather than cutting through the SW or FB fields.
    track(board, "PD_BUCK_EN", 0.18, (52.51, 116.0), (54.49, 116.0))
    track(board, "PD_BUCK_EN", 0.18, (48.64, 107.25), (47.1, 107.25))
    via(board, "PD_BUCK_EN", (47.1, 107.25))
    track(board, "PD_BUCK_EN", 0.18, (47.1, 107.25), (50.5, 114.5),
          (52.0, 114.5), layer="B.Cu")
    via(board, "PD_BUCK_EN", (52.0, 114.5))
    track(board, "PD_BUCK_EN", 0.18, (52.0, 114.5), (52.51, 116.0))

    # R_PD_UV_TOP is intentionally outside the load-current VBUS_PD zone.
    # Its no-load UVLO sense crosses on B.Cu to preserve the quiet board-edge
    # feedback field and rejoins the main buck-input zone at (54,107).
    track(board, "VBUS_PD", 0.18, (51.49, 116.0), (50.5, 116.0))
    via(board, "VBUS_PD", (50.5, 116.0))
    track(board, "VBUS_PD", 0.18, (50.5, 116.0), (50.5, 117.0),
          (55.0, 117.0), (55.0, 107.0), (54.0, 107.0), layer="B.Cu")
    via(board, "VBUS_PD", (54.0, 107.0))

    # Aggregate eFuse thresholds and timing are package-local low-current
    # controls; fills clear around these explicit sense paths.
    track(board, "AGG_UV", 0.18, (84.09, 108.1), (83.2, 107.2),
          (83.2, 103.0), (83.175, 103.0), (81.825, 103.0))
    track(board, "AGG_OV", 0.18, (84.09, 108.77), (80.0, 108.77),
          (80.0, 106.5), (76.5, 106.5), (76.5, 100.0),
          (86.175, 100.0), (86.175, 103.0))
    track(board, "AGG_OV", 0.18, (84.825, 103.0), (86.175, 103.0))
    track(board, "AGG_TIMER", 0.18, (85.91, 108.1), (88.0, 108.1))
    via(board, "AGG_TIMER", (88.0, 108.1))
    track(board, "AGG_TIMER", 0.18, (88.0, 108.1), (87.3, 112.8), layer="B.Cu")
    via(board, "AGG_TIMER", (87.3, 112.8))
    track(board, "AGG_TIMER", 0.18, (87.3, 112.8), (88.225, 113.0))
    track(board, "AGG_DVDT", 0.18, (85.91, 109.9), (87.2, 109.9))
    via(board, "AGG_DVDT", (87.2, 109.9))
    track(board, "AGG_DVDT", 0.18, (87.2, 109.9), (86.5, 107.0),
          (86.5, 105.8), layer="B.Cu")
    via(board, "AGG_DVDT", (86.5, 105.8))
    track(board, "AGG_DVDT", 0.18, (86.5, 105.8), (87.225, 105.0))
    track(board, "AGG_ILIM", 0.18, (85.91, 108.77), (87.2, 108.77),
          (89.0, 108.825))

    # PD-controller VDD and VBUS detector local routes.
    track(board, "PD_VDD", 0.18, (44.0, 105.0), (44.0, 107.0),
          (45.32, 106.5))
    track(board, "PD_VDD", 0.18, (44.0, 107.0), (45.0, 107.0),
          (45.32, 106.5))
    track(board, "PD_VDD", 0.18, (35.51, 110.8), (37.0, 111.0),
          (41.5, 109.0), (44.0, 107.0))
    track(board, "PD_VBUS_SENSE", 0.18, (35.51, 109.0), (35.0, 108.0),
          (35.0, 105.0), (38.0, 105.0))

    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: added relocated 3V3 converter copper")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
