#!/usr/bin/env python3
"""Rebase the settled route onto the TPS259804 aggregate-power placement.

The old promoted board used a different aggregate eFuse package and three
obsolete threshold-divider nets.  Start from the current generated placement,
copy only compatible settled copper, and deliberately leave the new aggregate
cell for an explicit local route pass.  This prevents stale package-local
copper from being mistaken for a reviewed route.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402


OBSOLETE_NETS = {"AGG_UV", "AGG_OV"}
REBUILD_NETS = {"AGG_ILIM", "AGG_TIMER", "AGG_DVDT"}
LOCAL_POWER_NETS = {"P5V_REG", "P5V_PROTECTED", "GND"}
LOCAL_BOX_MM = (79.0, 102.0, 93.0, 116.0)


def xy(point: pcbnew.VECTOR2I) -> tuple[int, int]:
    return point.x, point.y


def inside_local(point: pcbnew.VECTOR2I) -> bool:
    x0, y0, x1, y1 = (pcbnew.FromMM(v) for v in LOCAL_BOX_MM)
    return x0 <= point.x <= x1 and y0 <= point.y <= y1


def skip_old_item(item: pcbnew.BOARD_ITEM) -> bool:
    net = item.GetNetname()
    if net in OBSOLETE_NETS or net in REBUILD_NETS:
        return True
    if net not in LOCAL_POWER_NETS:
        return False
    if isinstance(item, pcbnew.PCB_VIA):
        # The protected-output via bank lands wholly inside the new zone and
        # remains package-independent; it is the reviewed F/B trunk join.
        if net == "P5V_PROTECTED":
            return False
        if net == "P5V_REG" and abs(item.GetPosition().x - pcbnew.FromMM(78.0)) <= pcbnew.FromMM(0.1):
            return True
        return inside_local(item.GetPosition())
    # Retire the former UV-divider launch stub; its load no longer exists.
    if net == "P5V_REG":
        endpoints = (item.GetStart(), item.GetEnd())
        if item.GetLayer() == pcbnew.In2_Cu and all(
            pcbnew.FromMM(77.9) <= p.x <= pcbnew.FromMM(78.1)
            and pcbnew.FromMM(101.0) <= p.y <= pcbnew.FromMM(109.5)
            for p in endpoints
        ):
            return True
        if all(
            pcbnew.FromMM(77.0) <= p.x <= pcbnew.FromMM(81.0)
            and pcbnew.FromMM(102.5) <= p.y <= pcbnew.FromMM(103.5)
            for p in endpoints
        ):
            return True
        if item.GetLayer() == pcbnew.F_Cu and all(
            pcbnew.FromMM(77.9) <= p.x <= pcbnew.FromMM(78.1)
            and pcbnew.FromMM(101.0) <= p.y <= pcbnew.FromMM(103.0)
            for p in endpoints
        ):
            return True
    # Preserve trunks that merely enter/leave the cell; remove only copper
    # wholly owned by the obsolete package-local implementation.
    return inside_local(item.GetStart()) and inside_local(item.GetEnd())


def point_mm(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def pad_point(board: pcbnew.BOARD, reference: str, number: str) -> pcbnew.VECTOR2I:
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise SystemExit(f"missing footprint {reference}")
    for pad in footprint.Pads():
        if pad.GetNumber() == number:
            return pad.GetPosition()
    raise SystemExit(f"missing pad {reference}.{number}")


def nearest_pad_point(
    board: pcbnew.BOARD,
    reference: str,
    number: str,
    origin: pcbnew.VECTOR2I,
) -> pcbnew.VECTOR2I:
    footprint = board.FindFootprintByReference(reference)
    if footprint is None:
        raise SystemExit(f"missing footprint {reference}")
    candidates = [p.GetPosition() for p in footprint.Pads() if p.GetNumber() == number]
    if not candidates:
        raise SystemExit(f"missing pad {reference}.{number}")
    return min(candidates, key=lambda p: (p.x - origin.x) ** 2 + (p.y - origin.y) ** 2)


def add_segment(
    board: pcbnew.BOARD,
    net_name: str,
    start: pcbnew.VECTOR2I,
    end: pcbnew.VECTOR2I,
    width_mm: float,
    layer: int = pcbnew.F_Cu,
) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start)
    track.SetEnd(end)
    track.SetWidth(pcbnew.FromMM(width_mm))
    track.SetLayer(layer)
    track.SetNet(board.FindNet(net_name))
    board.Add(track)


def add_via(
    board: pcbnew.BOARD,
    net_name: str,
    position: pcbnew.VECTOR2I,
    diameter_mm: float = 0.46,
    drill_mm: float = 0.20,
) -> None:
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(position)
    via.SetWidth(pcbnew.FromMM(diameter_mm))
    via.SetDrill(pcbnew.FromMM(drill_mm))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(board.FindNet(net_name))
    board.Add(via)


def route_new_aggregate_cell(board: pcbnew.BOARD) -> None:
    """Route only the new TPS259804 cell; coordinates are support waypoints."""

    # Output lead bank into the protected F.Cu zone.  Pins 17--21 already
    # overlap the zone; this bar collects the three north-west output pins.
    add_segment(
        board, "P5V_PROTECTED", pad_point(board, "U_AGG", "24"),
        point_mm(85.30, 107.0875), 0.40,
    )

    # The secondary IN lead (16) is locally joined to the split IN PowerPAD.
    in16 = pad_point(board, "U_AGG", "16")
    add_segment(
        board, "P5V_REG", in16,
        nearest_pad_point(board, "U_AGG", "25", in16), 0.30,
    )

    # Restore the package-independent protected-power drop into the existing
    # B.Cu distribution trunk.
    add_segment(
        board, "P5V_PROTECTED", point_mm(90.00, 103.00),
        point_mm(90.00, 113.00), 2.00, pcbnew.B_Cu,
    )

    # Timing/programming components.  Waypoints keep the three independent
    # nets separated instead of relying on an autorouter.
    ilim_u = pad_point(board, "U_AGG", "8")
    ilim_r = pad_point(board, "R_AGG_ILIM", "1")
    ilim_u_via = point_mm(84.25, 111.55)
    ilim_r_via = point_mm(80.65, 113.525)
    add_segment(board, "AGG_ILIM", ilim_u, ilim_u_via, 0.18)
    add_via(board, "AGG_ILIM", ilim_u_via)
    add_segment(board, "AGG_ILIM", ilim_u_via, ilim_r_via, 0.18, pcbnew.B_Cu)
    add_via(board, "AGG_ILIM", ilim_r_via)
    add_segment(board, "AGG_ILIM", ilim_r_via, ilim_r, 0.18)

    timer_u = pad_point(board, "U_AGG", "7")
    timer_c = pad_point(board, "C_AGG_TIMER", "1")
    add_segment(board, "AGG_TIMER", timer_u, point_mm(83.75, 112.00), 0.18)
    add_segment(board, "AGG_TIMER", point_mm(83.75, 112.00), timer_c, 0.18)

    dvdt_u = pad_point(board, "U_AGG", "15")
    dvdt_c = pad_point(board, "C_AGG_DVDT", "1")
    dvdt_u_via = point_mm(87.65, 109.25)
    dvdt_c_via = point_mm(87.80, 104.40)
    add_segment(board, "AGG_DVDT", dvdt_u, dvdt_u_via, 0.18)
    add_via(board, "AGG_DVDT", dvdt_u_via)
    add_segment(board, "AGG_DVDT", dvdt_u_via, dvdt_c_via, 0.18, pcbnew.B_Cu)
    add_via(board, "AGG_DVDT", dvdt_c_via)
    add_segment(board, "AGG_DVDT", dvdt_c_via, dvdt_c, 0.18)

    # Short local ground escapes into the continuous ground planes.
    for reference, number in (
        ("R_AGG_ILIM", "2"),
        ("C_AGG_TIMER", "2"),
        ("U_AGG", "14"),
        ("C_TRUNK_HF", "2"),
    ):
        add_via(board, "GND", pad_point(board, reference, number))
    # C_PD_OUT3's old ground escape enters the aggregate-region bounding box
    # but belongs to the PD cell, so reproduce its terminal via explicitly.
    add_via(board, "GND", point_mm(79.03, 109.63))


def remove_near_duplicate_copper(board: pcbnew.BOARD) -> int:
    """Retire legacy 1-nm duplicate primitives while keeping current r0 first.

    Earlier route producers emitted geometrically identical seed segments with
    endpoints differing by one internal unit.  KiCad DRC treats them as
    harmless same-net overlap, but topology grading correctly sees a loop.
    Quantizing only at 10 internal units (0.00001 mm) removes that serialization
    noise without merging any manufacturable geometric distinction.
    """

    quantum = 10

    def q(value: int) -> int:
        return round(value / quantum) * quantum

    seen: set[tuple] = set()
    remove: list[pcbnew.BOARD_ITEM] = []
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            pos = item.GetPosition()
            key = (
                "via", item.GetNetname(), q(pos.x), q(pos.y),
                item.GetDrillValue(), item.GetWidth(item.GetLayer()),
                item.TopLayer(), item.BottomLayer(),
            )
        else:
            a = (q(item.GetStart().x), q(item.GetStart().y))
            b = (q(item.GetEnd().x), q(item.GetEnd().y))
            key = (
                "track", item.GetNetname(), item.GetLayer(), item.GetWidth(),
                *sorted((a, b)),
            )
        if key in seen:
            remove.append(item)
        else:
            seen.add(key)
    for item in remove:
        board.Remove(item)
    return len(remove)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("reviewed", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.base))
    reviewed = pcbnew.LoadBoard(str(args.reviewed))
    segments = {
        (track.GetNetname(), track.GetLayer(), track.GetWidth(),
         xy(track.GetStart()), xy(track.GetEnd()))
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA)
    }
    vias = {
        (track.GetNetname(), xy(track.GetPosition()), track.GetDrillValue())
        for track in board.GetTracks()
        if isinstance(track, pcbnew.PCB_VIA)
    }

    copied_segments = copied_vias = skipped = absent = 0
    for item in reviewed.GetTracks():
        if skip_old_item(item):
            skipped += 1
            continue
        net = item.GetNetname()
        target_net = board.FindNet(net)
        if not target_net:
            absent += 1
            continue
        if isinstance(item, pcbnew.PCB_VIA):
            key = (net, xy(item.GetPosition()), item.GetDrillValue())
            if key in vias:
                continue
            copy = pcbnew.PCB_VIA(board)
            copy.SetPosition(item.GetPosition())
            copy.SetWidth(item.GetWidth(item.GetLayer()))
            copy.SetDrill(item.GetDrillValue())
            copy.SetLayerPair(item.TopLayer(), item.BottomLayer())
            copy.SetNet(target_net)
            board.Add(copy)
            vias.add(key)
            copied_vias += 1
            continue
        key = (net, item.GetLayer(), item.GetWidth(),
               xy(item.GetStart()), xy(item.GetEnd()))
        reverse = (net, item.GetLayer(), item.GetWidth(),
                   xy(item.GetEnd()), xy(item.GetStart()))
        if key in segments or reverse in segments:
            continue
        copy = pcbnew.PCB_TRACK(board)
        copy.SetStart(item.GetStart())
        copy.SetEnd(item.GetEnd())
        copy.SetWidth(item.GetWidth())
        copy.SetLayer(item.GetLayer())
        copy.SetNet(target_net)
        board.Add(copy)
        segments.add(key)
        copied_segments += 1

    route_new_aggregate_cell(board)
    deduplicated = remove_near_duplicate_copper(board)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(
        f"wrote {args.output}: copied {copied_segments} segments/"
        f"{copied_vias} vias; deliberately skipped {skipped}; "
        f"ignored {absent} absent-net items; removed {deduplicated} "
        "near-duplicate primitives"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
