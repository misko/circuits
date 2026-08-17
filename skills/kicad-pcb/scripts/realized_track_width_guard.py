#!/usr/bin/env python3
"""Assert a realized copper-width contract on explicitly named routed nets.

This is deliberately an output-board measurement, not an assertion about the
router command line.  A router may receive the intended width and subsequently
neck, rewrite, or otherwise emit thinner geometry.  The contract distinguishes
the nominal field width from a fabrication-safe absolute floor and strictly
bounds the count and total length of any local sub-nominal discontinuities.
"""
import argparse
import json
from pathlib import Path

import pcbnew


def inspect(board_path, nets, nominal_mm, minimum_mm,
            max_subnominal_length_mm, max_subnominal_segments):
    board = pcbnew.LoadBoard(str(board_path))
    wanted = set(nets)
    board_nets = {str(name) for name in board.GetNetsByName().keys()}
    unknown = sorted(wanted - board_nets)
    measured = {name: [] for name in wanted}
    floor_violations = []
    subnominal = {name: {"segments": 0, "length_mm": 0.0,
                         "minimum_mm": None}
                  for name in wanted}
    tol = 1e-6

    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            continue
        name = item.GetNetname()
        if name not in wanted:
            continue
        width_mm = item.GetWidth() / 1e6
        measured[name].append(width_mm)
        length_mm = item.GetLength() / 1e6
        if width_mm < nominal_mm - tol:
            row = subnominal[name]
            row["segments"] += 1
            row["length_mm"] += length_mm
            row["minimum_mm"] = (width_mm if row["minimum_mm"] is None
                                 else min(row["minimum_mm"], width_mm))
        if width_mm < minimum_mm - tol:
            start = item.GetStart()
            end = item.GetEnd()
            floor_violations.append({
                "net": name,
                "layer": board.GetLayerName(item.GetLayer()),
                "width_mm": round(width_mm, 6),
                "start_mm": [round(start.x / 1e6, 6),
                             round(start.y / 1e6, 6)],
                "end_mm": [round(end.x / 1e6, 6),
                           round(end.y / 1e6, 6)],
            })

    unmeasured = sorted(name for name, widths in measured.items() if not widths)
    minima = {name: round(min(widths), 6)
              for name, widths in measured.items() if widths}
    for row in subnominal.values():
        row["length_mm"] = round(row["length_mm"], 6)
        if row["minimum_mm"] is not None:
            row["minimum_mm"] = round(row["minimum_mm"], 6)
    budget_violations = []
    for name, row in sorted(subnominal.items()):
        if row["segments"] > max_subnominal_segments:
            budget_violations.append({
                "net": name, "kind": "segment_count",
                "actual": row["segments"],
                "maximum": max_subnominal_segments})
        if row["length_mm"] > max_subnominal_length_mm + tol:
            budget_violations.append({
                "net": name, "kind": "total_length_mm",
                "actual": row["length_mm"],
                "maximum": max_subnominal_length_mm})

    return {
        "schema": 1,
        "board": str(board_path),
        "nets": sorted(wanted),
        "contract": {
            "nominal_mm": nominal_mm,
            "minimum_mm": minimum_mm,
            "max_subnominal_length_per_net_mm": max_subnominal_length_mm,
            "max_subnominal_segments_per_net": max_subnominal_segments,
        },
        "measured_segment_count": sum(len(v) for v in measured.values()),
        "measured_minimum_mm": minima,
        "unknown_nets": unknown,
        "unmeasured_nets": unmeasured,
        "subnominal_by_net": subnominal,
        "floor_violations": floor_violations,
        "budget_violations": budget_violations,
        "verdict": ("FAIL" if unknown or unmeasured or floor_violations
                    or budget_violations else "PASS"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board", type=Path)
    ap.add_argument("--nets", nargs="+", required=True)
    ap.add_argument("--nominal-width", type=float, required=True)
    ap.add_argument("--min-width", type=float, required=True)
    ap.add_argument("--max-subnominal-length-per-net", type=float,
                    required=True)
    ap.add_argument("--max-subnominal-segments-per-net", type=int,
                    required=True)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    if args.nominal_width <= 0 or args.min_width <= 0:
        ap.error("widths must be positive")
    if args.min_width > args.nominal_width:
        ap.error("--min-width cannot exceed --nominal-width")
    if args.max_subnominal_length_per_net < 0:
        ap.error("--max-subnominal-length-per-net cannot be negative")
    if args.max_subnominal_segments_per_net < 0:
        ap.error("--max-subnominal-segments-per-net cannot be negative")

    report = inspect(
        args.board, args.nets, args.nominal_width, args.min_width,
        args.max_subnominal_length_per_net,
        args.max_subnominal_segments_per_net)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if report["verdict"] == "PASS":
        thin_nets = sum(1 for row in report["subnominal_by_net"].values()
                        if row["segments"])
        print("realized track width: PASS "
              f"({report['measured_segment_count']} segments, "
              f"nominal {args.nominal_width:g} mm, floor "
              f"{args.min_width:g} mm, {thin_nets} net(s) use a bounded "
              "neck)")
        return 0

    print("realized track width: FAIL")
    if report["unknown_nets"]:
        print("  board has no net(s): " + ", ".join(report["unknown_nets"]))
    if report["unmeasured_nets"]:
        print("  no track geometry for net(s): "
              + ", ".join(report["unmeasured_nets"]))
    for finding in report["floor_violations"][:20]:
        print(f"  {finding['net']} {finding['layer']} "
              f"{finding['width_mm']:.6f} mm < {args.min_width:g} mm "
              f"at {finding['start_mm']} -> {finding['end_mm']}")
    if len(report["floor_violations"]) > 20:
        print(f"  ... {len(report['floor_violations']) - 20} more")
    for finding in report["budget_violations"]:
        print(f"  {finding['net']} sub-nominal {finding['kind']} "
              f"{finding['actual']} > {finding['maximum']}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
