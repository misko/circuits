#!/usr/bin/env python3
"""Grade projected foreign copper beneath declared high-speed routes.

This is deliberately narrower than a field-solver or a zone-connectivity
proof.  It closes one concrete release-gate gap: DRC can accept a legal track
on an inner plane layer even when that track/antipad cuts directly beneath an
outer-layer USB/RF route.  Boards opt in through ``reference_plane_checks`` in
their nets YAML; unconfigured boards retain their existing behavior.
"""
import argparse
import json
import math
from pathlib import Path

import pcbnew
import yaml


def _xy(point):
    return point.x / 1e6, point.y / 1e6


def _point_segment_distance(point, start, end):
    px, py = point
    ax, ay = start
    bx, by = end
    vx, vy = bx - ax, by - ay
    length2 = vx * vx + vy * vy
    t = 0.0 if length2 == 0 else max(
        0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / length2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _segment_distance(a, b, c, d):
    den = ((b[0] - a[0]) * (d[1] - c[1])
           - (b[1] - a[1]) * (d[0] - c[0]))
    if abs(den) > 1e-12:
        t = ((c[0] - a[0]) * (d[1] - c[1])
             - (c[1] - a[1]) * (d[0] - c[0])) / den
        u = ((c[0] - a[0]) * (b[1] - a[1])
             - (c[1] - a[1]) * (b[0] - a[0])) / den
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
            return 0.0
    return min(_point_segment_distance(a, c, d),
               _point_segment_distance(b, c, d),
               _point_segment_distance(c, a, b),
               _point_segment_distance(d, a, b))


def _segment_row(board, item):
    return {
        "net": item.GetNetname(),
        "layer": board.GetLayerName(item.GetLayer()),
        "start_mm": [round(v, 6) for v in _xy(item.GetStart())],
        "end_mm": [round(v, 6) for v in _xy(item.GetEnd())],
        "width_mm": round(item.GetWidth() / 1e6, 6),
    }


def inspect(board_path, config_path):
    board = pcbnew.LoadBoard(str(board_path))
    source = yaml.safe_load(Path(config_path).read_text()) or {}
    checks = source.get("reference_plane_checks")
    if checks is None:
        return {
            "schema": 1,
            "scope": "projected foreign tracks/vias; not a field solve or full zone proof",
            "board": str(board_path),
            "config": str(config_path),
            "checks": {},
            "verdict": "N-A",
            "reason": "reference_plane_checks not declared",
        }
    if not isinstance(checks, dict) or not checks:
        raise ValueError("reference_plane_checks must be a non-empty mapping when present")

    board_nets = {str(name) for name in board.GetNetsByName().keys()}
    results, failures = {}, []
    for name, cfg in checks.items():
        required = ("signal_layer", "reference_layer", "reference_net",
                    "signal_nets", "min_track_clearance_mm",
                    "min_via_clearance_mm")
        missing = [key for key in required if key not in cfg]
        if missing:
            raise ValueError(f"{name}: missing {', '.join(missing)}")
        signal_nets = set(cfg["signal_nets"])
        reference_net = str(cfg["reference_net"])
        unknown = sorted(signal_nets.union({reference_net}) - board_nets)
        if unknown:
            raise ValueError(f"{name}: unknown nets: {', '.join(unknown)}")
        signal_layer = str(cfg["signal_layer"])
        reference_layer = str(cfg["reference_layer"])
        signal_lid = board.GetLayerID(signal_layer)
        reference_lid = board.GetLayerID(reference_layer)
        if signal_lid < 0 or reference_lid < 0:
            raise ValueError(f"{name}: unknown layer in {signal_layer}/{reference_layer}")

        signal_tracks = [item for item in board.GetTracks()
                         if item.GetClass() != "PCB_VIA"
                         and item.GetLayer() == signal_lid
                         and item.GetNetname() in signal_nets]
        if not signal_tracks:
            raise ValueError(f"{name}: no declared signal tracks on {signal_layer}")
        allowed = signal_nets | {reference_net} | set(cfg.get("allowed_nets", []))
        foreign_tracks = [item for item in board.GetTracks()
                          if item.GetClass() != "PCB_VIA"
                          and item.GetLayer() == reference_lid
                          and item.GetNetname() not in allowed]
        foreign_vias = [item for item in board.GetTracks()
                        if item.GetClass() == "PCB_VIA"
                        and item.GetLayerSet().Contains(reference_lid)
                        and item.GetNetname() not in allowed]

        nearest_track = None
        nearest_via = None
        violations = []
        track_floor = float(cfg["min_track_clearance_mm"])
        via_floor = float(cfg["min_via_clearance_mm"])
        for signal in signal_tracks:
            sa, sb = _xy(signal.GetStart()), _xy(signal.GetEnd())
            sw = signal.GetWidth() / 1e6
            for obstacle in foreign_tracks:
                edge = (_segment_distance(sa, sb, _xy(obstacle.GetStart()),
                                          _xy(obstacle.GetEnd()))
                        - (sw + obstacle.GetWidth() / 1e6) / 2.0)
                row = {
                    "kind": "track", "clearance_mm": round(edge, 6),
                    "signal": _segment_row(board, signal),
                    "obstacle": _segment_row(board, obstacle),
                }
                if nearest_track is None or edge < nearest_track[0]:
                    nearest_track = (edge, row)
                if edge + 1e-9 < track_floor:
                    violations.append(row)
            for obstacle in foreign_vias:
                edge = (_point_segment_distance(_xy(obstacle.GetPosition()), sa, sb)
                        - (sw + obstacle.GetWidth(reference_lid) / 1e6) / 2.0)
                row = {
                    "kind": "via", "clearance_mm": round(edge, 6),
                    "signal": _segment_row(board, signal),
                    "obstacle": {
                        "net": obstacle.GetNetname(),
                        "at_mm": [round(v, 6) for v in _xy(obstacle.GetPosition())],
                        "diameter_mm": round(obstacle.GetWidth(reference_lid) / 1e6, 6),
                    },
                }
                if nearest_via is None or edge < nearest_via[0]:
                    nearest_via = (edge, row)
                if edge + 1e-9 < via_floor:
                    violations.append(row)

        result = {
            "signal_layer": signal_layer,
            "reference_layer": reference_layer,
            "reference_net": reference_net,
            "signal_track_count": len(signal_tracks),
            "foreign_track_count": len(foreign_tracks),
            "foreign_via_count": len(foreign_vias),
            "min_track_clearance_mm": track_floor,
            "min_via_clearance_mm": via_floor,
            "nearest_foreign_track": nearest_track[1] if nearest_track else None,
            "nearest_foreign_via": nearest_via[1] if nearest_via else None,
            "violations": sorted(violations, key=lambda row: row["clearance_mm"]),
            "verdict": "FAIL" if violations else "PASS",
        }
        results[name] = result
        failures.extend((name, row) for row in violations)

    return {
        "schema": 1,
        "scope": "projected foreign tracks/vias; not a field solve or full zone proof",
        "board": str(board_path),
        "config": str(config_path),
        "checks": results,
        "verdict": "FAIL" if failures else "PASS",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("board", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    try:
        report = inspect(args.board, args.config)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(payload)
    print(payload, end="")
    raise SystemExit(0 if report["verdict"] in ("PASS", "N-A") else 1)


if __name__ == "__main__":
    main()
