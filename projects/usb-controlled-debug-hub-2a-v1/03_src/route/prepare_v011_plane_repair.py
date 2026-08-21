#!/usr/bin/env python3
"""Prepare the bounded v0.1.1 USB reference-plane routing ECO.

The v0.1.0 promoted route used In2.Cu for low-speed signals even where that
layer is the adjacent return plane for B.Cu USB.  This producer removes only
the explicitly selected low-speed nets from an exact reviewed board.  KRT can
then re-route those nets on the outer layers without disturbing the accepted
USB and high-current copper.

This file is a candidate producer, not an acceptance waiver.  Its output must
still pass native DRC/parity, critical-route, copper-length, reference-plane,
and promoted-route lineage checks before it can replace route/final.kicad_pcb.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, "/usr/lib/python3/dist-packages")
import pcbnew  # type: ignore  # noqa: E402


MM = 1_000_000


def _point_mm(item: pcbnew.PCB_TRACK) -> tuple[tuple[float, float], tuple[float, float]]:
    start, end = item.GetStart(), item.GetEnd()
    return ((start.x / MM, start.y / MM), (end.x / MM, end.y / MM))


def _same_segment(
    item: pcbnew.PCB_TRACK,
    start: tuple[float, float],
    end: tuple[float, float],
    tolerance_mm: float = 0.001,
) -> bool:
    actual = _point_mm(item)

    def close(a: tuple[float, float], b: tuple[float, float]) -> bool:
        return abs(a[0] - b[0]) <= tolerance_mm and abs(a[1] - b[1]) <= tolerance_mm

    return (close(actual[0], start) and close(actual[1], end)) or (
        close(actual[0], end) and close(actual[1], start)
    )


def _add_segment(
    board: pcbnew.BOARD,
    net_name: str,
    start: tuple[float, float],
    end: tuple[float, float],
    layer_name: str,
    width_mm: float = 0.2332,
) -> None:
    item = pcbnew.PCB_TRACK(board)
    item.SetStart(pcbnew.VECTOR2I_MM(*start))
    item.SetEnd(pcbnew.VECTOR2I_MM(*end))
    item.SetWidth(pcbnew.FromMM(width_mm))
    item.SetLayer(board.GetLayerID(layer_name))
    item.SetNet(board.FindNet(net_name))
    board.Add(item)


def _add_protected_via(
    board: pcbnew.BOARD, net_name: str, at: tuple[float, float]
) -> None:
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(pcbnew.VECTOR2I_MM(*at))
    item.SetWidth(pcbnew.FromMM(0.46))
    item.SetDrill(pcbnew.FromMM(0.20))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet(net_name))
    item.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)
    item.SetFillingMode(pcbnew.FILLING_MODE_FILLED)
    board.Add(item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("nets", nargs="*")
    parser.add_argument(
        "--layer",
        help="remove only track segments on this layer; preserve vias and "
        "already accepted outer-layer copper",
    )
    parser.add_argument(
        "--open-upstream-middle",
        action="store_true",
        help="remove the exact F.Cu pair span that crosses the In1 power bridge",
    )
    parser.add_argument(
        "--restore-bank-a-bridge",
        action="store_true",
        help="restore the three exact In1 bank-A bridge primitives after the "
        "delta router's foreign-net reassignment safeguard fires",
    )
    parser.add_argument(
        "--install-upstream-crossover",
        action="store_true",
        help="replace the opened pair span with the exact matched F/B/F "
        "crossover that preserves an adjacent GND reference",
    )
    parser.add_argument(
        "--install-port4-meander",
        action="store_true",
        help="replace one exact P4_HUB_P B.Cu span with the bounded "
        "2.90-mm skew-correction meander",
    )
    parser.add_argument(
        "--install-stitch-collision-repairs",
        action="store_true",
        help="move the exact bank-B power primitive that collides only when "
        "deterministic stitch seeds are replayed",
    )
    parser.add_argument(
        "--install-prtpwr4-detour",
        action="store_true",
        help="move the exact legacy In2 PRTPWR4 primitive around the OCS1 via",
    )
    parser.add_argument(
        "--install-ocs1-outer",
        action="store_true",
        help="replace OCS1's first B.Cu transition with a bounded F.Cu fanout",
    )
    parser.add_argument(
        "--install-port-input-zone-necks",
        action="store_true",
        help="replace the two exact rectangular port-input zones with their "
        "source-owned necked outlines so refill cannot retain padless slivers",
    )
    parser.add_argument(
        "--install-final-drc-cleanups",
        action="store_true",
        help="remove four exact post-prune dead branches, normalize one exact "
        "legacy via, and replay source-owned pad zone overrides",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.input))
    copper_items = list(board.GetTracks())
    requested = set(args.nets)
    known = {net.GetNetname() for net in board.GetNetInfo().NetsByNetcode().values()}
    absent = sorted(requested - known)
    if absent:
        raise SystemExit(f"unknown net(s): {', '.join(absent)}")

    removed_tracks = 0
    removed_vias = 0
    for item in copper_items:
        if item.GetNetname() not in requested:
            continue
        if args.layer:
            if isinstance(item, pcbnew.PCB_VIA):
                continue
            if item.GetLayerName() != args.layer:
                continue
        if isinstance(item, pcbnew.PCB_VIA):
            removed_vias += 1
        else:
            removed_tracks += 1
        board.Remove(item)

    if args.open_upstream_middle:
        exact = {
            "UP_HUB_P": ((50.221, 61.692), (73.421, 61.692)),
            "UP_HUB_N": ((50.379, 61.308), (73.579, 61.308)),
        }
        matched: set[str] = set()
        for item in copper_items:
            if isinstance(item, pcbnew.PCB_VIA) or item.GetLayerName() != "F.Cu":
                continue
            expected = exact.get(item.GetNetname())
            if expected and _same_segment(item, *expected):
                board.Remove(item)
                matched.add(item.GetNetname())
        missing = sorted(set(exact) - matched)
        if missing:
            raise SystemExit(
                "exact upstream middle segment(s) absent: " + ", ".join(missing)
            )

    if args.install_upstream_crossover:
        if not args.open_upstream_middle:
            raise SystemExit(
                "--install-upstream-crossover requires --open-upstream-middle"
            )
        geometry = {
            "UP_HUB_P": [
                ("F.Cu", (50.221, 61.692), (53.0, 63.5)),
                ("B.Cu", (53.0, 63.5), (76.0, 64.5)),
                ("F.Cu", (76.0, 64.5), (73.421, 61.692)),
            ],
            "UP_HUB_N": [
                ("F.Cu", (50.379, 61.308), (53.0, 62.5)),
                ("B.Cu", (53.0, 62.5), (76.0, 63.5)),
                ("F.Cu", (76.0, 63.5), (73.579, 61.308)),
            ],
        }
        for net_name, segments in geometry.items():
            for layer_name, start, end in segments:
                _add_segment(board, net_name, start, end, layer_name)
            _add_protected_via(board, net_name, segments[0][2])
            _add_protected_via(board, net_name, segments[1][2])

    if args.install_port4_meander:
        start = (111.570637, 65.9084)
        end = (126.070637, 65.9084)
        matches = [
            item
            for item in copper_items
            if not isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname() == "P4_HUB_P"
            and item.GetLayerName() == "B.Cu"
            and _same_segment(item, start, end)
        ]
        if len(matches) != 1:
            raise SystemExit(
                f"exact P4_HUB_P meander span matched {len(matches)}/1 primitives"
            )
        board.Remove(matches[0])
        points = [
            start,
            (111.8, 65.9084),
            (111.8, 64.4584),
            (114.8, 64.4584),
            (114.8, 65.9084),
            end,
        ]
        for a, b in zip(points, points[1:]):
            _add_segment(board, "P4_HUB_P", a, b, "B.Cu")

    if args.restore_bank_a_bridge:
        exact = [
            ((63.0, 54.6), (69.0, 64.4), 3.0),
            ((74.0, 54.4), (72.0, 57.0), 1.5),
            ((72.0, 57.0), (70.0, 66.0), 3.0),
        ]
        net = board.FindNet("P5V_A_PROTECTED")
        if not net:
            raise SystemExit("missing P5V_A_PROTECTED")
        restored = 0
        for start, end, width in exact:
            matches = [
                item
                for item in copper_items
                if not isinstance(item, pcbnew.PCB_VIA)
                and item.GetLayerName() == "In1.Cu"
                and _same_segment(item, start, end)
            ]
            if len(matches) > 1:
                raise SystemExit("duplicate bank-A bridge geometry")
            if matches:
                item = matches[0]
                if abs(item.GetWidth() / MM - width) > 0.001:
                    raise SystemExit("bank-A bridge width differs from source contract")
                item.SetNet(net)
            else:
                item = pcbnew.PCB_TRACK(board)
                item.SetStart(pcbnew.VECTOR2I_MM(*start))
                item.SetEnd(pcbnew.VECTOR2I_MM(*end))
                item.SetWidth(pcbnew.FromMM(width))
                item.SetLayer(board.GetLayerID("In1.Cu"))
                item.SetNet(net)
                board.Add(item)
            restored += 1
        if restored != len(exact):
            raise SystemExit(
                f"bank-A bridge restore matched {restored}/{len(exact)} primitives"
            )

    if args.install_stitch_collision_repairs:
        # The original direct 3-mm bank-B bridge was electrically sound but
        # ran through two outer-layer control vias.  Keep the same endpoints,
        # width and layer while moving its centreline around that local via
        # cluster.  This is power-copper geometry, not a signal-layer waiver.
        old_power = ((113.4, 54.4), (139.8, 64.4))
        power_matches = [
            item
            for item in list(board.GetTracks())
            if not isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname() == "P5V_B_PROTECTED"
            and item.GetLayerName() == "In1.Cu"
            and _same_segment(item, *old_power)
        ]
        if len(power_matches) != 1:
            raise SystemExit(
                f"exact bank-B bridge matched {len(power_matches)}/1 primitives"
            )
        board.Remove(power_matches[0])
        power_points = [
            old_power[0],
            (120.0, 56.9),
            (122.0, 53.0),
            (128.0, 53.0),
            (128.0, 60.0),
            old_power[1],
        ]
        for start, end in zip(power_points, power_points[1:]):
            _add_segment(
                board,
                "P5V_B_PROTECTED",
                start,
                end,
                "In1.Cu",
                width_mm=3.0,
            )

    if args.install_prtpwr4_detour:
        # HUB_OCS1_N's reviewed outer-layer transition pierced one legacy
        # HUB_PRTPWR4 In2 segment.  Keep the status route unchanged and move
        # only that low-speed PRTPWR segment to the east of the through-via.
        old_prtpwr4_segments = [
            ("In2.Cu", (91.4, 71.7), (91.4, 73.8)),
            ("In2.Cu", (91.4, 73.8), (92.3, 74.7)),
        ]
        for layer_name, start, end in old_prtpwr4_segments:
            matches = [
                item
                for item in list(board.GetTracks())
                if not isinstance(item, pcbnew.PCB_VIA)
                and item.GetNetname() == "HUB_PRTPWR4"
                and item.GetLayerName() == layer_name
                and _same_segment(item, start, end)
            ]
            if len(matches) != 1:
                raise SystemExit(
                    f"exact HUB_PRTPWR4 segment {start}->{end} matched "
                    f"{len(matches)}/1 primitives"
                )
            board.Remove(matches[0])
        prtpwr4_points = [
            (91.4, 71.7),
            (89.8, 72.3),
            (89.8, 74.2),
            (92.3, 74.7),
        ]
        for start, end in zip(prtpwr4_points, prtpwr4_points[1:]):
            _add_segment(board, "HUB_PRTPWR4", start, end, "In2.Cu", 0.18)

    if args.install_ocs1_outer:
        old_segments = [
            ("B.Cu", (94.3, 70.6), (94.1, 70.8)),
            ("B.Cu", (94.1, 70.8), (94.0, 70.8)),
            ("B.Cu", (94.0, 70.8), (91.2, 73.6)),
            ("F.Cu", (91.2, 73.6), (91.1, 73.5)),
        ]
        for layer_name, start, end in old_segments:
            matches = [
                item
                for item in list(board.GetTracks())
                if not isinstance(item, pcbnew.PCB_VIA)
                and item.GetNetname() == "HUB_OCS1_N"
                and item.GetLayerName() == layer_name
                and _same_segment(item, start, end)
            ]
            if len(matches) != 1:
                raise SystemExit(
                    f"exact HUB_OCS1_N segment {start}->{end} matched "
                    f"{len(matches)}/1 primitives"
                )
            board.Remove(matches[0])
        for x, y in ((94.3, 70.6), (91.2, 73.6)):
            matches = []
            for item in list(board.GetTracks()):
                if not isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() != "HUB_OCS1_N":
                    continue
                position = item.GetPosition()
                if abs(position.x / MM - x) <= 0.001 and abs(position.y / MM - y) <= 0.001:
                    matches.append(item)
            if len(matches) != 1:
                raise SystemExit(
                    f"exact HUB_OCS1_N via {(x, y)} matched {len(matches)}/1 primitives"
                )
            board.Remove(matches[0])
        _add_segment(board, "HUB_OCS1_N", (94.3, 70.6), (91.1, 73.5), "F.Cu", 0.18)

    if args.install_port_input_zone_necks:
        replacements = {
            (101.0, 52.0, 4.0, 4.0): [
                (101.0, 52.0), (102.75, 52.0), (102.75, 53.55),
                (105.0, 53.55), (105.0, 56.0), (101.0, 56.0),
            ],
            (129.0, 52.0, 4.0, 4.0): [
                (129.0, 52.0), (130.75, 52.0), (130.75, 53.55),
                (133.0, 53.55), (133.0, 56.0), (129.0, 56.0),
            ],
        }
        matched = set()
        for zone in board.Zones():
            if zone.GetNetname() != "P5V_B_PROTECTED" or zone.GetLayerName() != "F.Cu":
                continue
            bbox = zone.Outline().BBox()
            key = (
                round(bbox.GetX() / MM, 3),
                round(bbox.GetY() / MM, 3),
                round(bbox.GetWidth() / MM, 3),
                round(bbox.GetHeight() / MM, 3),
            )
            points = replacements.get(key)
            if points is None:
                continue
            outline = zone.Outline()
            outline.RemoveAllContours()
            outline.NewOutline()
            for x, y in points:
                outline.Append(pcbnew.VECTOR2I_MM(x, y))
            matched.add(key)
        if matched != set(replacements):
            raise SystemExit(
                f"port-input zones matched {len(matched)}/{len(replacements)} exact outlines"
            )

    if args.install_final_drc_cleanups:
        copper_snapshot = list(board.GetTracks())
        dead_segments = [
            ("3V3_MAIN", "F.Cu", (86.4, 60.8), (86.5, 60.7)),
            ("3V3_MAIN", "B.Cu", (82.5, 48.5), (81.2, 47.2)),
            ("VBUS_CTRL", "F.Cu", (80.2, 75.0), (79.2, 74.0)),
            ("VBUS_CTRL", "F.Cu", (103.9, 77.2), (101.3, 74.6)),
        ]
        dead_items = []
        for net_name, layer_name, start, end in dead_segments:
            matches = [
                item
                for item in copper_snapshot
                if not isinstance(item, pcbnew.PCB_VIA)
                and item.GetNetname() == net_name
                and item.GetLayerName() == layer_name
                and _same_segment(item, start, end)
            ]
            if len(matches) != 1:
                raise SystemExit(
                    f"exact dead branch {net_name} {start}->{end} matched "
                    f"{len(matches)}/1 primitives"
                )
            dead_items.append(matches[0])

        legacy_vias = []
        for item in copper_snapshot:
            if not isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() != "3V3_MAIN":
                continue
            position = item.GetPosition()
            if (
                abs(position.x / MM - 100.9) <= 0.001
                and abs(position.y / MM - 60.0) <= 0.001
            ):
                legacy_vias.append(item)
        if len(legacy_vias) != 1:
            raise SystemExit(
                f"exact legacy 3V3_MAIN via matched {len(legacy_vias)}/1 primitives"
            )
        legacy_vias[0].SetWidth(pcbnew.FromMM(0.46))
        legacy_vias[0].SetDrill(pcbnew.FromMM(0.20))

        old_boost = ((96.5, 60.4), (103.4, 60.4))
        boost_matches = [
            item
            for item in copper_snapshot
            if not isinstance(item, pcbnew.PCB_VIA)
            and item.GetNetname() == "HUB_BOOST0"
            and item.GetLayerName() == "In2.Cu"
            and _same_segment(item, *old_boost)
        ]
        if len(boost_matches) != 1:
            raise SystemExit(
                f"exact HUB_BOOST0 inner segment matched {len(boost_matches)}/1 primitives"
            )
        dead_items.append(boost_matches[0])
        boost_points = [
            old_boost[0],
            (99.8, 60.8),
            (101.5, 60.8),
            (101.5, 60.4),
            old_boost[1],
        ]
        for start, end in zip(boost_points, boost_points[1:]):
            _add_segment(board, "HUB_BOOST0", start, end, "In2.Cu", 0.18)

        for ref, pad_number in (("R_BOOST1", "2"), ("C_AND_DATA", "2"), ("U_PWR4", "5")):
            footprint = board.FindFootprintByReference(ref)
            pad = footprint.FindPadByNumber(pad_number) if footprint else None
            if pad is None:
                raise SystemExit(f"missing pad override subject {ref}.{pad_number}")
            pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        gnd_drop = [(75.09, 53.77), (74.75, 53.75), (74.50, 54.00), (74.50, 56.00)]
        for start, end in zip(gnd_drop, gnd_drop[1:]):
            _add_segment(board, "GND", start, end, "F.Cu", 0.18)
        _add_protected_via(board, "GND", (74.50, 56.00))
        _add_segment(board, "P5V_B_PROTECTED", (131.77, 54.0), (131.77, 56.52), "F.Cu", 0.30)
        for item in dead_items:
            board.Remove(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(
        f"wrote {args.output}: removed {removed_tracks} track(s) and "
        f"{removed_vias} via(s) from {len(requested)} selected net(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
