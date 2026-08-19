#!/usr/bin/env python3
"""Close exact v0.1.1 package-local ground and PD power-path islands.

This project-owned delta is deliberately coordinate- and net-bound.  It
refuses a board whose reviewed footprint pads moved, so the short closure
tracks cannot silently attach to a later placement.  Ground closures are
authored here rather than delegated to heuristic island healing: they are
electrical features, not disposable zone-stitch artifacts.
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


def assert_pad(board, ref: str, number: str, net: str,
               at: tuple[float, float]):
    footprint = board.FindFootprintByReference(ref)
    if footprint is None:
        raise SystemExit(f"missing footprint {ref}")
    matches = [pad for pad in footprint.Pads()
               if pad.GetNumber() == number and pad.GetNetname() == net]
    expected = point(*at)
    exact = [pad for pad in matches if pad.GetPosition() == expected]
    if not exact:
        observed = [
            (pad.GetNumber(), pad.GetNetname(),
             pad.GetPosition().x / MM, pad.GetPosition().y / MM)
            for pad in footprint.Pads() if pad.GetNumber() == number
        ]
        raise SystemExit(
            f"{ref}.{number} is not exact {net} pad at {at}: {observed}")
    return exact[0]


def add_track(board, net: str, width: float,
              start: tuple[float, float], end: tuple[float, float],
              layer: str = "F.Cu") -> None:
    netinfo = board.FindNet(net)
    if not netinfo:
        raise SystemExit(f"missing net {net}")
    item = pcbnew.PCB_TRACK(board)
    item.SetStart(point(*start))
    item.SetEnd(point(*end))
    item.SetWidth(round(width * MM))
    item.SetLayer(board.GetLayerID(layer))
    item.SetNet(netinfo)
    board.Add(item)


def add_via(board, net: str, at: tuple[float, float],
            size: float = 0.46, drill: float = 0.20) -> None:
    netinfo = board.FindNet(net)
    if not netinfo:
        raise SystemExit(f"missing net {net}")
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(point(*at))
    item.SetWidth(round(size * MM))
    item.SetDrill(round(drill * MM))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(netinfo)
    board.Add(item)


def remove_exact_tracks(board, net: str, layer: str,
                        segments: set[tuple[float, float, float, float]]) -> None:
    expected = {
        (round(x1 * MM), round(y1 * MM), round(x2 * MM), round(y2 * MM))
        for x1, y1, x2, y2 in segments
    }
    found = {}
    layer_id = board.GetLayerID(layer)
    for item in list(board.GetTracks()):
        if isinstance(item, pcbnew.PCB_VIA):
            continue
        if item.GetNetname() != net or item.GetLayer() != layer_id:
            continue
        start, end = item.GetStart(), item.GetEnd()
        forward = (start.x, start.y, end.x, end.y)
        reverse = (end.x, end.y, start.x, start.y)
        identity = forward if forward in expected else reverse
        if identity in expected:
            if identity in found:
                raise SystemExit(f"duplicate exact {net} track: {identity}")
            found[identity] = item
    missing = expected - set(found)
    if missing:
        raise SystemExit(f"missing exact {net} track(s): {sorted(missing)}")
    for item in found.values():
        board.Remove(item)


def remove_exact_vias(board, net: str,
                      positions: set[tuple[float, float]]) -> None:
    expected = {(round(x * MM), round(y * MM)) for x, y in positions}
    found = {}
    for item in list(board.GetTracks()):
        if not isinstance(item, pcbnew.PCB_VIA) or item.GetNetname() != net:
            continue
        pos = item.GetPosition()
        key = (pos.x, pos.y)
        if key in expected:
            if key in found:
                raise SystemExit(f"duplicate exact {net} via: {key}")
            found[key] = item
    missing = expected - set(found)
    if missing:
        raise SystemExit(f"missing exact {net} via(s): {sorted(missing)}")
    for item in found.values():
        board.Remove(item)


def ensure_rule_area(board, name: str, layer: str,
                     rect: tuple[float, float, float, float]) -> None:
    existing = [z for z in board.Zones()
                if z.GetIsRuleArea() and z.GetZoneName() == name]
    if existing:
        return
    x0, y0, x1, y1 = rect
    zone = pcbnew.ZONE(board)
    zone.SetIsRuleArea(True)
    zone.SetZoneName(name)
    layer_id = board.GetLayerID(layer)
    layers = pcbnew.LSET()
    add_layer = getattr(layers, "AddLayer", None) or getattr(layers, "addLayer")
    add_layer(layer_id)
    zone.SetLayer(layer_id)
    zone.SetLayerSet(layers)
    zone.SetDoNotAllowTracks(False)
    zone.SetDoNotAllowVias(False)
    zone.SetDoNotAllowPads(False)
    zone.Outline().NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        zone.Outline().Append(point(x, y))
    board.Add(zone)


def add_ground_closures(board) -> None:
    # USB-C receptacle ground contacts to their adjacent plated shell stakes.
    assert_pad(board, "J_POWER", "A1", "GND", (27.32, 101.80))
    assert_pad(board, "J_POWER", "A12", "GND", (27.32, 108.20))
    add_track(board, "GND", 0.30, (27.32, 101.80), (26.75, 100.675))
    add_track(board, "GND", 0.30, (27.32, 108.20), (26.75, 109.325))

    # PD controller exposed pad is already tied to two ground vias; join the
    # isolated package-side GND lead to that same low-inductance island.
    assert_pad(board, "U_PD", "9", "GND", (38.00, 106.00))
    assert_pad(board, "U_PD", "11", "GND", (41.00, 105.00))
    add_track(board, "GND", 0.30, (38.00, 106.00), (40.00, 106.00))

    # The buck's narrow package-side grounds cannot receive zone thermals.
    # Join them to the exposed GND land, then bring the local bypass capacitor
    # into the same island without adding an unnecessary transition via.
    assert_pad(board, "U_PD_BUCK", "3", "GND", (48.64, 108.25))
    assert_pad(board, "U_PD_BUCK", "9", "GND", (49.83, 107.35))
    assert_pad(board, "U_PD_BUCK", "10", "GND", (49.11, 106.60))
    bypass_ground = assert_pad(
        board, "C_PD_VDD", "2", "GND", (46.28, 106.50))
    # A thermal on this 0402 pad is geometrically starved by the adjacent
    # bypass pair.  Make the intended local ground connection explicit.
    bypass_ground.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    add_track(board, "GND", 0.25, (48.64, 108.25), (49.83, 108.25))
    add_track(board, "GND", 0.25, (49.11, 106.60), (49.83, 106.60))
    add_track(board, "GND", 0.25, (46.28, 106.50), (49.11, 106.60))
    add_via(board, "GND", (49.83, 106.85))
    add_via(board, "GND", (49.83, 107.85))

    # Short outward spokes give the solid F.Cu ground zone an unobstructed
    # landing beyond the HotRod/VSON pad rows.
    assert_pad(board, "U_PD_IN", "8", "GND", (46.91, 98.23))
    add_track(board, "GND", 0.18, (46.91, 98.23), (47.50, 98.23))

    # Free the only legal horizontal ground-pad exits on channels 1 and 2 by
    # moving their low-speed EN fanout around, not through, the pad row.
    remove_exact_tracks(board, "PWR_EN1", "F.Cu", {
        (43.85, 56.35, 46.35, 53.85),
        (46.35, 53.85, 46.35, 53.45),
        (46.35, 53.45, 46.70, 53.10),
        (46.70, 53.10, 47.10, 53.10),
    })
    add_track(board, "PWR_EN1", 0.18, (43.85, 56.35), (45.80, 54.40))
    add_track(board, "PWR_EN1", 0.18, (45.80, 54.40), (45.80, 53.10))
    add_track(board, "PWR_EN1", 0.18, (45.80, 53.10), (47.10, 53.10))
    remove_exact_tracks(board, "PWR_EN2", "F.Cu", {
        (73.85, 56.20, 74.40, 55.65),
        (74.40, 55.65, 74.40, 54.95),
        (74.40, 54.95, 74.35, 54.90),
        (74.35, 54.90, 74.35, 53.45),
        (74.35, 53.45, 74.70, 53.10),
        (74.70, 53.10, 75.10, 53.10),
        (71.65, 50.75, 74.35, 53.45),
    })
    add_track(board, "PWR_EN2", 0.18, (71.65, 50.75), (73.50, 52.60))
    add_track(board, "PWR_EN2", 0.18, (73.50, 52.60), (73.50, 53.10))
    add_track(board, "PWR_EN2", 0.18, (73.85, 56.20), (73.50, 55.85))
    add_track(board, "PWR_EN2", 0.18, (73.50, 55.85), (73.50, 53.10))
    add_track(board, "PWR_EN2", 0.18, (73.50, 53.10), (75.10, 53.10))

    for channel, centre in enumerate((48.0, 76.0, 104.0, 132.0), 1):
        ref = f"U_PWR{channel}"
        assert_pad(board, ref, "2", "GND", (centre - 0.91, 53.77))
        assert_pad(board, ref, "8", "GND", (centre + 0.91, 54.23))
        if channel == 1:
            left_exit, right_exit = (46.50, 53.77), (49.60, 54.23)
        elif channel == 2:
            left_exit, right_exit = (74.50, 53.77), (77.39, 54.23)
        else:
            left_exit = (centre - 1.35, 53.77)
            right_exit = (centre + 1.35, 54.23)
        add_track(board, "GND", 0.18,
                  (centre - 0.91, 53.77), left_exit)
        add_track(board, "GND", 0.18,
                  (centre + 0.91, 54.23), right_exit)
        if channel <= 2:
            add_via(board, "GND", left_exit)
            add_via(board, "GND", right_exit)

    # The TVS return sits inside the VBUS_PD pour, so an F.Cu spoke cannot
    # reach ground.  Two filled/capped 0.20-mm via-in-pad returns provide a
    # short symmetric transient path into the solid internal ground planes.
    assert_pad(board, "D_PD_TVS", "1", "GND", (35.00, 115.45))
    add_via(board, "GND", (34.65, 115.45))
    add_via(board, "GND", (35.35, 115.45))

    # U_EXP.10 owns the sole remaining top-pour island after exact refill.
    # Join its long TSSOP land to the pre-existing plane stitch at (116.48,77)
    # while staying above the neighbouring VBUS_CTRL route.
    assert_pad(board, "U_EXP", "10", "GND", (119.50, 77.625))
    add_track(board, "GND", 0.18, (119.50, 77.625), (116.48, 77.625))
    add_track(board, "GND", 0.18, (116.48, 77.625), (116.48, 77.00))

    # Channel 1's input-bypass / enable-pulldown pour is separated from its
    # switch-pad island by the protected-rail launch.  The 0402 ground land is
    # large enough for the standard filled/capped via family.
    assert_pad(board, "C_PWR1_IN", "2", "GND", (47.77, 57.48))
    add_via(board, "GND", (47.77, 57.48))


def add_pd_power_closures(board) -> None:
    """Realize the 3 A connector-to-fuse-to-eFuse path in copper.

    The overlapping source zones define copper ownership and heat spreading,
    but they do not substitute for a verified current path: connector pad
    clearances split each zone into multiple filled polygons.  These short
    branches explicitly bridge the resulting islands at package-neck width.
    """
    assert_pad(board, "J_POWER", "A4", "VBUS_PD_RAW", (27.32, 102.60))
    assert_pad(board, "J_POWER", "A9", "VBUS_PD_RAW", (27.32, 107.40))
    assert_pad(board, "F_PD", "1", "VBUS_PD_RAW", (30.60, 105.00))

    # CC2 formerly occupied B.Cu exactly where the pre-fuse power bridge must
    # cross.  Move this static configuration signal to In2.Cu through its
    # existing through vias; the move is outside every USB reference corridor.
    remove_exact_tracks(board, "PD_CC2", "B.Cu", {
        (29.00, 106.75, 33.50, 106.75),
        (33.50, 106.75, 37.00, 102.30),
    })
    remove_exact_tracks(board, "PD_CC2", "F.Cu", {
        (27.32, 106.75, 29.00, 106.75),
    })
    remove_exact_vias(board, "PD_CC2", {(29.00, 106.75)})
    add_track(board, "PD_CC2", 0.18,
              (27.32, 106.75), (29.00, 106.75), "F.Cu")
    add_track(board, "PD_CC2", 0.18,
              (29.00, 106.75), (29.50, 106.35), "F.Cu")
    add_track(board, "PD_CC2", 0.18,
              (29.50, 106.35), (32.20, 106.35), "F.Cu")
    add_via(board, "PD_CC2", (32.20, 106.35))
    add_track(board, "PD_CC2", 0.18,
              (32.20, 106.35), (33.50, 106.75), "In2.Cu")
    add_track(board, "PD_CC2", 0.18,
              (33.50, 106.75), (37.00, 102.30), "In2.Cu")

    # Six standard 0.46/0.20-mm vias on each side give 3.30 A at the declared
    # 0.55 A/via, 10 C-rise evidence limit.  Full-width 1.50-mm B.Cu joins the
    # connector-side zone lobe to the fuse-side lobe; no fill-material credit.
    raw_source = [
        *((x, 102.60) for x in (28.20, 28.80, 29.40)),
        *((x, 107.40) for x in (27.60, 28.20, 28.80)),
    ]
    raw_fuse = [
        (x, y) for y in (104.60, 105.40) for x in (30.20, 30.80, 31.40)
    ]
    for at in raw_source + raw_fuse:
        add_via(board, "VBUS_PD_RAW", at)
    add_track(board, "VBUS_PD_RAW", 1.50,
              (28.20, 102.60), (29.40, 102.60), "B.Cu")
    add_track(board, "VBUS_PD_RAW", 1.50,
              (27.60, 107.40), (28.80, 107.40), "B.Cu")
    add_track(board, "VBUS_PD_RAW", 1.50,
              (28.80, 102.60), (30.80, 105.00), "B.Cu")
    add_track(board, "VBUS_PD_RAW", 1.50,
              (28.20, 107.40), (30.80, 105.00), "B.Cu")
    add_track(board, "VBUS_PD_RAW", 1.50,
              (30.20, 105.00), (31.40, 105.00), "B.Cu")

    # The original low-speed VBUS monitor and controller-supply traces cut
    # across the only full-width F.Cu power corridors.  Preserve their exact
    # endpoints while moving the field portions below the power layer.
    remove_exact_tracks(board, "PD_VBUS_SENSE", "F.Cu", {
        (35.51, 109.00, 35.00, 108.00),
        (35.00, 108.00, 35.00, 105.00),
        (35.00, 105.00, 38.00, 105.00),
    })
    add_via(board, "PD_VBUS_SENSE", (35.51, 109.00))
    add_via(board, "PD_VBUS_SENSE", (38.00, 105.00))
    add_track(board, "PD_VBUS_SENSE", 0.18,
              (35.51, 109.00), (36.50, 107.00), "B.Cu")
    add_track(board, "PD_VBUS_SENSE", 0.18,
              (36.50, 107.00), (38.00, 105.00), "B.Cu")

    remove_exact_tracks(board, "PD_VDD", "F.Cu", {
        (34.15, 109.65, 32.95, 108.45),
        (42.80, 108.20, 37.30, 108.20),
        (37.30, 108.20, 35.85, 109.65),
        (44.00, 107.00, 42.80, 108.20),
        (32.95, 108.45, 32.95, 108.20),
        (35.85, 109.65, 34.15, 109.65),
    })
    add_via(board, "PD_VDD", (32.95, 108.20))
    add_via(board, "PD_VDD", (43.00, 108.50))
    add_track(board, "PD_VDD", 0.30,
              (44.00, 107.00), (43.00, 108.50), "F.Cu")
    add_track(board, "PD_VDD", 0.30,
              (32.95, 108.20), (33.00, 111.00), "B.Cu")
    add_track(board, "PD_VDD", 0.30,
              (33.00, 111.00), (43.00, 111.00), "B.Cu")
    add_track(board, "PD_VDD", 0.30,
              (43.00, 111.00), (43.00, 108.50), "B.Cu")

    assert_pad(board, "F_PD", "2", "VBUS_PD", (33.40, 105.00))
    assert_pad(board, "R_PD_VBUS", "1", "VBUS_PD", (34.49, 109.00))
    ensure_rule_area(board, "pd_vbus_monitor_tap", "F.Cu",
                     (33.90, 108.40, 35.10, 110.30))
    # With the low-speed barriers gone, current remains on F.Cu: full-width
    # fuse neck to the input lobe, plus a separate full-width TVS-lobe bridge.
    add_track(board, "VBUS_PD", 1.50, (33.40, 105.00), (36.00, 105.00))
    add_track(board, "VBUS_PD", 1.50, (40.50, 107.00), (40.50, 109.20))
    # R_PD_VBUS is a no-load-current monitor tap, explicitly bounded by the
    # pd_vbus_monitor_tap scoped floor in nets.yaml.
    add_track(board, "VBUS_PD", 0.18, (34.49, 109.00), (34.49, 110.20))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.input))
    add_ground_closures(board)
    add_pd_power_closures(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"authored exact v0.1.1 ground closures: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
