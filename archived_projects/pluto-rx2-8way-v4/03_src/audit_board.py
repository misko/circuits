#!/usr/bin/env python3
"""Project geometry assertions that DRC alone cannot prove non-vacuously."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "04_kicad" / "pluto_rx2_8way_v4.kicad_pcb"
KEEP_NAME = "mcu_live_underside_pads"
KEEP_RECT = (57.950, 73.650, 59.450, 86.150)
LIVE_RECT = (58.100, 73.800, 59.300, 86.000)
EPS_MM = 1e-6


def mm(value: int) -> float:
    return value / 1_000_000.0


def close(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= EPS_MM


def fail(message: str) -> None:
    raise SystemExit(f"P-GEOM FAIL: {message}")


def segment_box(item: pcbnew.PCB_TRACK) -> tuple[float, float, float, float]:
    start, end = item.GetStart(), item.GetEnd()
    radius = mm(item.GetWidth()) / 2.0
    return (
        min(mm(start.x), mm(end.x)) - radius,
        min(mm(start.y), mm(end.y)) - radius,
        max(mm(start.x), mm(end.x)) + radius,
        max(mm(start.y), mm(end.y)) + radius,
    )


def boxes_overlap(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def segment_endpoints(item: pcbnew.PCB_TRACK) -> set[tuple[float, float]]:
    return {
        (mm(item.GetStart().x), mm(item.GetStart().y)),
        (mm(item.GetEnd().x), mm(item.GetEnd().y)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--routed", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    areas = [z for z in board.Zones() if z.GetZoneName() == KEEP_NAME]
    if len(areas) != 1:
        fail(f"expected exactly one {KEEP_NAME!r} rule area, found {len(areas)}")

    area = areas[0]
    if not area.GetIsRuleArea():
        fail(f"{KEEP_NAME} is not a KiCad rule area")
    layers = set(area.GetLayerSet().Seq())
    if layers != {pcbnew.F_Cu}:
        fail(f"{KEEP_NAME} layers are {layers}, expected F.Cu only")
    bbox = area.GetBoundingBox()
    actual = (mm(bbox.GetX()), mm(bbox.GetY()),
              mm(bbox.GetRight()), mm(bbox.GetBottom()))
    if not all(close(a, e) for a, e in zip(actual, KEEP_RECT)):
        fail(f"{KEEP_NAME} bbox {actual}, expected {KEEP_RECT}")
    if not (KEEP_RECT[0] < LIVE_RECT[0] < LIVE_RECT[2] < KEEP_RECT[2]
            and KEEP_RECT[1] < LIVE_RECT[1] < LIVE_RECT[3] < KEEP_RECT[3]):
        fail("declared keepout does not non-vacuously enclose the live-pad field")
    denials = {
        "tracks": area.GetDoNotAllowTracks(),
        "vias": area.GetDoNotAllowVias(),
        "zone fills": area.GetDoNotAllowZoneFills(),
    }
    missing = [name for name, denied in denials.items() if not denied]
    if missing:
        fail(f"{KEEP_NAME} permits {', '.join(missing)}")

    if not args.routed:
        print(f"P-GEOM PASS: exact live-pad F.Cu rule area {KEEP_RECT}; all copper denied")
        return

    tracks = [t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_TRACK)
              and not isinstance(t, pcbnew.PCB_VIA)]
    if not tracks:
        fail("--routed audit was vacuous: board has no track segments")

    fcu_intruders = [t for t in tracks if t.GetLayer() == pcbnew.F_Cu
                     and boxes_overlap(segment_box(t), KEEP_RECT)]
    if fcu_intruders:
        fail(f"{len(fcu_intruders)} F.Cu track(s) enter {KEEP_NAME}")
    via_intruders = []
    for via in (t for t in board.GetTracks() if isinstance(t, pcbnew.PCB_VIA)):
        pos = via.GetPosition()
        radius = mm(via.GetWidth(pcbnew.F_Cu)) / 2.0
        box = (mm(pos.x) - radius, mm(pos.y) - radius,
               mm(pos.x) + radius, mm(pos.y) + radius)
        if boxes_overlap(box, KEEP_RECT):
            via_intruders.append(via)
    if via_intruders:
        fail(f"{len(via_intruders)} via(s) enter {KEEP_NAME}")

    sw = board.FindNet("SW_V4")
    if not sw:
        fail("SW_V4 net is absent")
    sw_tracks = [t for t in tracks if t.GetNetCode() == sw.GetNetCode()]
    ant4_band = (39.850, 50.250, 40.250, 64.250)
    wrong_layer = [t for t in sw_tracks if t.GetLayer() == pcbnew.F_Cu
                   and boxes_overlap(segment_box(t), ant4_band)]
    if wrong_layer:
        fail(f"SW_V4 has {len(wrong_layer)} F.Cu segment(s) alongside ANT4")
    required_crossing = {(44.700, 56.100), (44.700, 68.200)}
    if not any(t.GetLayer() == pcbnew.In2_Cu
               and segment_endpoints(t) == required_crossing for t in sw_tracks):
        fail("SW_V4 exact In2.Cu ANT4 crossing segment is absent")

    in1_tracks = [t for t in tracks if t.GetLayer() == pcbnew.In1_Cu]
    if in1_tracks:
        fail(f"In1.Cu is not uninterrupted: found {len(in1_tracks)} track(s)")
    in1_gnd = [z for z in board.Zones() if not z.GetIsRuleArea()
               and z.GetNetname() == "GND"
               and z.GetLayerSet().Contains(pcbnew.In1_Cu)]
    if not in1_gnd:
        fail("In1.Cu has no GND plane zone")

    print("P-GEOM PASS: keepout clear; SW_V4 crosses ANT4 on In2.Cu; In1 GND uninterrupted")


if __name__ == "__main__":
    main()
