#!/usr/bin/env python3
"""Rebase settled v2 copper and replace only v0.1.1 power-cell launches.

STOPGAP/backend gap: this is a deterministic project-owned route-delta
producer.  The shared replacement is a route.yaml ``local_cells`` schema that
can exclude obsolete footprint-local copper and emit reviewed polylines/vias.
It starts from the freshly prepared r0 board, copies only compatible settled
copper, removes the superseded TPS2557/PD-cell launches, then authors the new
TPS259470A and negotiated-voltage-gate connections.  Its output is a candidate
until the normal P-ROUTEBASE, DRC/parity and route-acceptance gates pass.
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


def xy(value) -> tuple[float, float]:
    return value.x / MM, value.y / MM


def add_track(board, net: str, width: float, points, layer="F.Cu") -> None:
    if not board.FindNet(net):
        raise ValueError(f"unknown net {net}")
    for start, end in zip(points, points[1:]):
        item = pcbnew.PCB_TRACK(board)
        item.SetStart(point(*start))
        item.SetEnd(point(*end))
        item.SetWidth(round(width * MM))
        item.SetLayer(board.GetLayerID(layer))
        item.SetNet(board.FindNet(net))
        board.Add(item)


def add_via(board, net: str, at, size=0.46, drill=0.20) -> None:
    item = pcbnew.PCB_VIA(board)
    item.SetPosition(point(*at))
    item.SetWidth(round(size * MM))
    item.SetDrill(round(drill * MM))
    item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    item.SetNet(board.FindNet(net))
    board.Add(item)


def item_points(item):
    if isinstance(item, pcbnew.PCB_VIA):
        return [xy(item.GetPosition())]
    return [xy(item.GetStart()), xy(item.GetEnd())]


def in_rect(p, rect) -> bool:
    x, y = p
    x0, y0, x1, y1 = rect
    return x0 <= x <= x1 and y0 <= y <= y1


def copy_settled(base, settled):
    port_centres = (48.0, 76.0, 104.0, 132.0)
    port_nets = {"P5V_PROTECTED", "GND"}
    for channel in range(1, 5):
        port_nets |= {
            f"VBUS{channel}_SW", f"PWR_EN{channel}", f"ILIM{channel}",
            f"HUB_OCS{channel + 1}_N",
        }
    pd_replace = {
        "VBUS_PD", "VBUS_PD_SW", "PD_SW",
    }
    # These low-speed/local nets are intentionally left completely unrouted
    # for the bounded KRT delta waves.  Retaining even one legacy footprint
    # launch can make the router authenticate the wrong endpoint geometry.
    reroute_nets = {
        "PD_VDD", "PD_PROTO", "PD_CC2", "PD_IN_UV", "PD_IN_OV",
        "PD_IN_ILIM", "PD_IN_DVDT", "PD_BOOT", "PD_FB",
        # The former trace crosses the new channel-3 protected-power branch.
        # It is a low-speed static strap and belongs in the bounded control
        # delta wave, not underneath a newly placed current path.
        "HUB_BOOST1",
    }
    for channel in range(1, 5):
        reroute_nets |= {
            f"VBUS{channel}_SW", f"ILIM{channel}",
        }
    output_anchor_vias = {
        ("VBUS1_SW", 49.95, 54.0),
        ("VBUS2_SW", 79.52, 51.2),
        ("VBUS3_SW", 106.15, 54.0),
        ("VBUS4_SW", 134.15, 54.0),
    }

    segments = {
        (t.GetNetname(), t.GetLayer(), t.GetWidth(),
         tuple(round(v, 6) for v in xy(t.GetStart())),
         tuple(round(v, 6) for v in xy(t.GetEnd())))
        for t in base.GetTracks() if not isinstance(t, pcbnew.PCB_VIA)
    }
    vias = {
        (t.GetNetname(), tuple(round(v, 6) for v in xy(t.GetPosition())),
         t.GetDrillValue())
        for t in base.GetTracks() if isinstance(t, pcbnew.PCB_VIA)
    }
    copied_segments = copied_vias = skipped = 0
    for source in settled.GetTracks():
        net = source.GetNetname()
        if not base.FindNet(net):
            raise ValueError(f"settled copper net absent from new base: {net}")
        if net in reroute_nets:
            skipped += 1
            continue
        points = item_points(source)
        replace = net in pd_replace
        if net == "GND" and any(in_rect(p, (27.0, 93.0, 55.0, 117.0))
                                for p in points):
            replace = True
        if net in port_nets:
            for centre, rail_x in zip(port_centres, (45.0, 73.0, 101.4, 129.0)):
                # Preserve the reviewed long enable/overcurrent routes, but
                # retire every former-TPS2557 segment that touches the local
                # switch cell.  The bounded KRT wave reconnects one new
                # TPS259470A land to the surviving trunk instead of replacing
                # tens of centimetres of already settled control copper.
                local_controls = {
                    f"PWR_EN{port_centres.index(centre) + 1}",
                    f"HUB_OCS{port_centres.index(centre) + 2}_N",
                }
                if (net in local_controls and net != "HUB_OCS3_N" and
                        any(in_rect(p, (centre - 2.0, 51.5,
                                       centre + 2.0, 58.0)) for p in points)):
                    replace = True
                # At the USB-required 0.30 mm clearance the former switch's
                # EN/UVLO fanout also blocks the new OUT escape several mm to
                # the east.  Retire the complete old package/resistor cell,
                # not only copper beneath the replacement body; the bounded
                # EN wave reconnects the resistor pad and surviving trunk.
                if (net == f"PWR_EN{port_centres.index(centre) + 1}" and
                        any(in_rect(p, (centre - 7.0, 48.0,
                                       centre + 8.0, 59.0)) for p in points)):
                    replace = True
                if (net == f"HUB_OCS{port_centres.index(centre) + 2}_N" and
                        net != "HUB_OCS3_N" and
                        any(in_rect(p, (centre - 7.0, 48.0,
                                       centre + 8.0, 61.5)) for p in points)):
                    replace = True
                if net == "HUB_OCS3_N":
                    # Keep the settled y=56 B.Cu handoff and F.Cu trunk to
                    # the hub.  Retire only the obsolete upper branch into
                    # the former switch pad; build_port_cells reconnects the
                    # new land at the surviving (78.65,56.00) endpoint.
                    if any(in_rect(p, (73.0, 51.0, 80.0, 56.2))
                           for p in points):
                        replace = True
                if (net == "PWR_EN2"
                        and any(abs(p[0] - 72.5) < 0.001 and
                                abs(p[1] - 53.4) < 0.001 for p in points)):
                    replace = True
                if (net == "HUB_OCS2_N"
                        and any(abs(p[0] - 50.75) < 0.001 and
                                abs(p[1] - 51.85) < 0.001 for p in points)):
                    replace = True
                if (net == "HUB_OCS3_N" and
                        isinstance(source, pcbnew.PCB_VIA) and
                        any(abs(p[0] - 76.5) < 0.001 and
                            abs(p[1] - 66.5) < 0.001 for p in points)):
                    replace = True
                # Retire the complete legacy TPS2557 input fork.  Its old
                # package was about 5 mm west of the replacement, so a filter
                # around only the new footprint leaves electrically live but
                # obsolete 0.50 mm branches behind.
                if (net == "P5V_PROTECTED" and
                        all(in_rect(p, (centre - 6.5, 53.5,
                                       centre - 0.5, 57.1)) for p in points)):
                    replace = True
                # Replace the short rail riser deterministically below; retain
                # the settled full-width y=59 spine and its via field.
                if (net == "P5V_PROTECTED" and
                        all(abs(p[0] - rail_x) < 0.001 and
                            56.999 <= p[1] <= 59.001 for p in points)):
                    replace = True
                if (net not in local_controls and
                        any(in_rect(p, (centre - 2.1, 52.0,
                                       centre + 2.1, 56.2)) for p in points)):
                    replace = True
                    if isinstance(source, pcbnew.PCB_VIA):
                        px, py = points[0]
                        if (net, round(px, 2), round(py, 2)) in output_anchor_vias:
                            replace = False
                    break
        if replace:
            skipped += 1
            continue

        if isinstance(source, pcbnew.PCB_VIA):
            pos = tuple(round(v, 6) for v in xy(source.GetPosition()))
            key = (net, pos, source.GetDrillValue())
            if key in vias:
                continue
            item = pcbnew.PCB_VIA(base)
            item.SetPosition(source.GetPosition())
            item.SetWidth(source.GetWidth(source.GetLayer()))
            item.SetDrill(source.GetDrillValue())
            item.SetLayerPair(source.TopLayer(), source.BottomLayer())
            item.SetNet(base.FindNet(net))
            base.Add(item)
            vias.add(key)
            copied_vias += 1
            continue

        a = tuple(round(v, 6) for v in xy(source.GetStart()))
        b = tuple(round(v, 6) for v in xy(source.GetEnd()))
        key = (net, source.GetLayer(), source.GetWidth(), a, b)
        reverse = (net, source.GetLayer(), source.GetWidth(), b, a)
        if key in segments or reverse in segments:
            continue
        item = pcbnew.PCB_TRACK(base)
        item.SetStart(source.GetStart())
        item.SetEnd(source.GetEnd())
        item.SetWidth(source.GetWidth())
        item.SetLayer(source.GetLayer())
        item.SetNet(base.FindNet(net))
        base.Add(item)
        segments.add(key)
        copied_segments += 1
    return copied_segments, copied_vias, skipped


def build_port_cells(board) -> None:
    cells = [
        # channel, centre, protected-rail anchor, output anchor, enable anchor,
        # OCS far-side anchor and whether that anchor needs a new via.
        (1, 48.0, 45.0, (49.95, 54.0), (47.0, 55.65), (50.75, 51.85), False),
        (2, 76.0, 73.0, (79.52, 51.2), (76.15, 56.6), (76.5, 56.0), False),
        (3, 104.0, 101.4, (106.15, 54.0), (103.6, 50.0), (104.9, 52.45), True),
        (4, 132.0, 129.0, (134.15, 54.0), (130.9, 55.55), (132.9, 52.45), True),
    ]
    for channel, cx, rail_x, out_anchor, en_anchor, ocs_anchor, add_far_via in cells:
        # Input: retain a full-width riser at the y=59 distribution spine,
        # narrow to 0.80 mm only for the short per-port branch, then to the
        # exact 0.30 mm land width inside the package-local rule area.  The
        # branch approaches from the west so it never shares the narrow lane
        # between adjacent IN/OUT HotRod lands.
        add_track(board, "P5V_PROTECTED", 1.50,
                  [(rail_x, 59.0), (rail_x, 58.7)])
        add_track(board, "P5V_PROTECTED", 0.8,
                  [(rail_x, 58.7), (cx - 1.2, 56.52)])
        add_track(board, "P5V_PROTECTED", 0.30,
                  [(cx - 1.2, 56.52), (cx - 0.23, 56.52),
                   (cx - 0.23, 54.0)])

        # C_PWRn_IN pad 2 is source-declared as a solid F.Cu ground-zone
        # contact.  A forced local via here collides with the settled B.Cu USB
        # control field in channel 3; the continuous ground pour and nearby
        # switch ground lands provide the lower-inductance shared return.

        # The router cannot start a 0.50 mm field trace inside the adjacent
        # HotRod land row. Emit the scoped 0.30 mm axial escape here, widen
        # only after clearing the package, and let the bounded delta wave own
        # the remaining multi-point branch.
        add_track(board, f"VBUS{channel}_SW", 0.30,
                  [(cx + 0.26, 54.0), (cx + 0.26, 55.9),
                   (cx + 0.50, 55.9)])
        add_track(board, f"VBUS{channel}_SW", 0.50,
                  [(cx + 0.50, 55.9), (cx + 1.2, 55.9)])

        # EN/UVLO, power-good and ILIM are emitted by the bounded KRT control
        # delta wave after these deterministic current-path launches.

        if channel == 2:
            # Channel 2's OCS land is boxed in on F.Cu by its enable escape,
            # IN bypass and OUT launch.  Cross the two B.Cu USB lines on F.Cu,
            # then rejoin the preserved OCS trunk at (76.50,66.50).  Both via
            # sites are clear on In1/In2; the generic router previously chose
            # (79.80,62.80), directly through In2 HUB_VBUS_SENSE.
            add_track(board, "HUB_OCS3_N", 0.18,
                      [(75.09, 54.90), (75.09, 55.60)])
            add_via(board, "HUB_OCS3_N", (75.09, 55.60))
            add_track(board, "HUB_OCS3_N", 0.18,
                      [(75.09, 55.60), (75.09, 58.80)],
                      layer="B.Cu")
            add_via(board, "HUB_OCS3_N", (75.09, 58.80))
            add_track(board, "HUB_OCS3_N", 0.18,
                      [(75.09, 58.80), (75.09, 61.20)])
            add_via(board, "HUB_OCS3_N", (75.09, 61.20))
            add_track(board, "HUB_OCS3_N", 0.18,
                      [(75.09, 61.20), (75.09, 65.80),
                       (75.80, 66.50), (76.50, 66.50)],
                      layer="B.Cu")


def build_pd_input_cell(board) -> None:
    # The USB-C B5 contact is boxed in by the receptacle's adjacent contact
    # lands and the already-settled CC1/attach-sense field.  Use the quiet
    # back-side corridor to reach the controller from below; the two via sites
    # are outside the USB data keepout and are checked against forbidden
    # In1/In2 copper by exact DRC.
    add_track(board, "PD_CC2", 0.18,
              [(27.32, 106.75), (29.00, 106.75)])
    add_via(board, "PD_CC2", (29.00, 106.75))
    add_track(board, "PD_CC2", 0.18,
              [(29.00, 106.75), (33.50, 106.75), (37.00, 102.30)],
              layer="B.Cu")
    add_via(board, "PD_CC2", (37.00, 102.30))
    add_track(board, "PD_CC2", 0.18,
              [(37.00, 102.30), (37.25, 103.00), (38.00, 103.00)])

    # Controller supply branch. The downstream control/protocol nets are
    # emitted by the bounded low-speed delta wave.
    add_track(board, "VBUS_PD", 0.30,
              [(30.0375, 108.2), (31.2, 108.2)])

    # Load-current gate: narrow only at the 0.30 mm HotRod lands, then enter
    # the source-owned full-width zones.
    add_track(board, "VBUS_PD", 0.30,
              [(45.77, 98.0), (45.77, 99.5), (44.98, 100.15),
               (44.98, 102.2)])
    add_track(board, "VBUS_PD_SW", 0.30,
              [(46.26, 98.0), (46.26, 101.7)])

    # Attach-side high-frequency return, immediately beside the input land.
    add_track(board, "GND", 0.30, [(44.02, 100.15), (43.4, 100.15)])
    add_via(board, "GND", (43.4, 100.15))

    # Negotiated-voltage input sense tap; the divider/control nodes are routed
    # by the low-speed delta wave.
    add_track(board, "VBUS_PD", 0.18,
              [(37.875, 96.0), (37.875, 102.2)])

    # Buck switch/boot loop; full-width copper begins after the package neck.
    add_track(board, "PD_SW", 0.25,
              [(50.41, 108.85), (50.41, 109.7), (49.7, 110.2),
               (49.7, 111.48), (50.9, 111.48)])
    add_track(board, "PD_SW", 0.60,
              [(49.7, 111.48), (52.5, 112.2)])
    add_track(board, "PD_SW", 1.50,
              [(52.5, 112.2), (54.625, 110.5)])


def build_hub_straps(board) -> None:
    # BOOST1 is a static 10 kOhm pulldown.  Locating it beside U_HUB.48 turns
    # the former cross-board, multi-via route into one short same-net axial
    # escape; R_BOOST1.2 is source-declared as a full ground-zone contact.
    # The 0.31 mm edge clearance to adjacent U_HUB.47 remains above the USB
    # field's conservative 0.30 mm routing clearance.
    add_track(board, "HUB_BOOST1", 0.18,
              [(97.4125, 61.25), (98.79, 61.25)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base", type=Path)
    parser.add_argument("settled", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.base))
    settled = pcbnew.LoadBoard(str(args.settled))
    segments, vias, skipped = copy_settled(board, settled)
    build_port_cells(board)
    build_pd_input_cell(board)
    build_hub_straps(board)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    print(f"wrote {args.output}: copied {segments} segments/{vias} vias, "
          f"replaced {skipped} stale local item(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
