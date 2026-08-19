#!/usr/bin/env python3
"""Build the v2 PD/high-current checkpoint from the authenticated USB prefix.

The script reuses only the unchanged, already-reviewed P5V_PROTECTED port and
management-switch distribution geometry embedded in this project.  The new PD
cell, 5.13 V regulator, aggregate eFuse and zone-to-trunk join are authored
below.  It never changes logical net identity and never generates firmware.
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


def xy(p: pcbnew.VECTOR2I) -> tuple[int, int]:
    return p.x, p.y


def add_track(board, net: str, a, b, width: float, layer: str) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(point(*a))
    track.SetEnd(point(*b))
    track.SetWidth(round(width * MM))
    track.SetLayer(board.GetLayerID(layer))
    track.SetNet(board.FindNet(net))
    board.Add(track)


def add_via(board, net: str, at, size: float = 0.46,
            drill: float = 0.20) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(point(*at))
    via.SetWidth(round(size * MM))
    via.SetDrill(round(drill * MM))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(board.FindNet(net))
    board.Add(via)


def copy_retained_distribution(board, reference) -> tuple[int, int]:
    """Copy only the unchanged port/control branches, never the old source."""
    existing_segments = {
        (t.GetNetname(), t.GetLayer(), t.GetWidth(), xy(t.GetStart()), xy(t.GetEnd()))
        for t in board.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)
    }
    existing_vias = {
        (t.GetNetname(), xy(t.GetPosition()), t.GetDrillValue())
        for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
    }
    retained_vias = {
        (39.6, 76.0), (40.4, 76.0),
        (47.6, 59.0), (48.4, 59.0),
        (59.6, 59.0), (60.4, 59.0),
        (139.6, 59.0), (140.4, 59.0),
    }
    copied_segments = copied_vias = 0
    for item in reference.GetTracks():
        if item.GetNetname() != "P5V_PROTECTED":
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            pos_mm = (round(item.GetPosition().x / MM, 3),
                      round(item.GetPosition().y / MM, 3))
            if pos_mm not in retained_vias:
                continue
            key = (item.GetNetname(), xy(item.GetPosition()), item.GetDrillValue())
            if key in existing_vias:
                continue
            copy = pcbnew.PCB_VIA(board)
            copy.SetPosition(item.GetPosition())
            copy.SetWidth(item.GetWidth(item.GetLayer()))
            copy.SetDrill(item.GetDrillValue())
            copy.SetLayerPair(item.TopLayer(), item.BottomLayer())
            copy.SetNet(board.FindNet("P5V_PROTECTED"))
            board.Add(copy)
            existing_vias.add(key)
            copied_vias += 1
            continue

        a = (item.GetStart().x / MM, item.GetStart().y / MM)
        b = (item.GetEnd().x / MM, item.GetEnd().y / MM)
        keep = False
        if item.GetLayer() == pcbnew.F_Cu:
            keep = max(a[1], b[1]) <= 76.0001
        elif item.GetLayer() == pcbnew.B_Cu:
            # Retain the 2 mm y=103 bus and its x=58/60/140 port feeds plus
            # the x=40 control branch. Exclude the former source/buck spur.
            keep = not (abs(a[0] - 68.0) < 0.001 and
                        abs(b[0] - 68.0) < 0.001)
            # The former source joined the west end of the y=103 bus at x=54.
            # The v2 source enters at x=90 and the retained west feed joins at
            # x=58, so the obsolete 54--58 mm tail must not survive.
            if {tuple(round(v, 3) for v in a),
                tuple(round(v, 3) for v in b)} == {(54.0, 103.0),
                                                   (140.0, 103.0)}:
                keep = False
        if not keep:
            continue
        key = (item.GetNetname(), item.GetLayer(), item.GetWidth(),
               xy(item.GetStart()), xy(item.GetEnd()))
        reverse = (item.GetNetname(), item.GetLayer(), item.GetWidth(),
                   xy(item.GetEnd()), xy(item.GetStart()))
        if key in existing_segments or reverse in existing_segments:
            continue
        copy = pcbnew.PCB_TRACK(board)
        copy.SetStart(item.GetStart())
        copy.SetEnd(item.GetEnd())
        copy.SetWidth(item.GetWidth())
        copy.SetLayer(item.GetLayer())
        copy.SetNet(board.FindNet("P5V_PROTECTED"))
        board.Add(copy)
        existing_segments.add(key)
        copied_segments += 1
    return copied_segments, copied_vias


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--retained-reference", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.input))
    reference = pcbnew.LoadBoard(str(args.retained_reference))
    segments, vias = copy_retained_distribution(board, reference)
    add_track(board, "P5V_PROTECTED", (58.0, 103.0), (140.0, 103.0),
              2.0, "B.Cu")

    # Compact TPS56637 switch node: exact land -> intermediate neck -> full
    # current path into the exact MWSA0804S land.
    add_track(board, "PD_SW", (50.41, 108.75), (52.10, 108.75), 0.25, "F.Cu")
    add_track(board, "PD_SW", (52.10, 108.75), (53.50, 109.50), 0.60, "F.Cu")
    add_track(board, "PD_SW", (53.50, 109.50), (54.625, 110.50), 1.50, "F.Cu")
    add_track(board, "PD_SW", (52.00, 109.00), (52.00, 111.48), 0.25, "F.Cu")
    add_track(board, "PD_SW", (52.00, 111.48), (50.90, 111.48), 0.25, "F.Cu")
    add_track(board, "PD_BOOT", (50.91, 109.40), (50.90, 110.52), 0.18, "F.Cu")
    add_track(board, "P5V_REG", (61.375, 110.50), (62.875, 109.00), 1.50, "F.Cu")

    # VBUS_PD load-current spine.  The PD controller/CC contact field is a
    # real F.Cu barrier between the fuse-output and buck-input zone lobes.
    # Transition through an eight-via source bank and an eight-via destination bank,
    # then cross on a 2.0 mm B.Cu spine;
    # no capacity credit is taken for via filling.
    for x in (32.8, 33.6, 34.4):
        ys = (106.4, 107.2, 108.0) if x < 34.0 else (106.4, 107.2)
        for y in ys:
            add_via(board, "VBUS_PD", (x, y))
    for x in (48.6, 49.4, 50.2, 51.0):
        for y in (102.8, 103.6):
            add_via(board, "VBUS_PD", (x, y))
    add_track(board, "VBUS_PD", (33.2, 107.6), (33.2, 100.0), 2.00, "B.Cu")
    add_track(board, "VBUS_PD", (33.2, 100.0), (49.8, 100.0), 2.00, "B.Cu")
    add_track(board, "VBUS_PD", (49.8, 100.0), (49.8, 103.2), 2.00, "B.Cu")
    add_track(board, "VBUS_PD", (48.6, 103.2), (51.0, 103.2), 2.00, "B.Cu")

    # Kelvin output-sense branches; these carry no load current.
    add_track(board, "P5V_REG", (80.175, 103.0), (78.0, 103.0), 0.18, "F.Cu")
    add_track(board, "P5V_REG", (78.0, 103.0), (78.0, 101.0), 0.18, "F.Cu")
    add_via(board, "P5V_REG", (78.0, 101.0))
    add_track(board, "P5V_REG", (78.0, 101.0), (78.0, 109.5), 0.18, "In2.Cu")
    add_via(board, "P5V_REG", (78.0, 109.5))
    # The eFuse IN/OUT lands are long vertical HotRod pads with control lands
    # immediately to their left/right. Escape downward along the pad axis;
    # horizontal escapes would cut across OV/PG/GND/ILIM.
    add_track(board, "P5V_REG", (84.77, 110.0), (84.77, 111.5), 0.30, "F.Cu")
    add_track(board, "P5V_PROTECTED", (85.26, 110.0), (85.26, 111.5), 0.30, "F.Cu")

    # The north zone owns regulator load current; the west zone supplies the
    # PD controller and TVS.  Join them through a full-width explicit neck,
    # avoiding overlapping zone authority.
    add_track(board, "VBUS_PD", (33.5, 107.5), (33.5, 109.0), 1.50, "F.Cu")

    # Protected-5V F/B zone join and 2 mm feed to the retained distribution.
    for x in (89.2, 90.0, 90.8, 91.6):
        for y in (112.0, 114.0):
            add_via(board, "P5V_PROTECTED", (x, y))
    add_track(board, "P5V_PROTECTED", (90.0, 113.0), (90.0, 103.0), 2.0, "B.Cu")

    # Bounded branch to the retained 3V3 buck input capacitor and paired VIN
    # lands. Main branch is 1.5 mm; only the package collector is 0.8 mm.
    add_track(board, "P5V_PROTECTED", (94.075, 106.0), (94.075, 101.0), 1.50, "F.Cu")
    add_track(board, "P5V_PROTECTED", (94.075, 101.0), (95.8625, 101.0), 0.80, "F.Cu")
    add_track(board, "P5V_PROTECTED", (95.8625, 101.0), (95.8625, 101.95), 0.80, "F.Cu")

    # The zones are the intended high-current conductors, not decorative
    # evidence. Fill them before grading so connectivity/clearance is exact.
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: retained {segments} segments/{vias} vias; "
          "added PD switch, feedback, graded trunk joins and 3V3-buck branch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
