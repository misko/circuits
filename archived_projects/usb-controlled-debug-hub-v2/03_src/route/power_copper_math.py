#!/usr/bin/env python3
"""Bound the P5V_PROTECTED distributor loss on the exact power prefix.

This is deliberately a trace-skeleton calculation, not a field solver.  It
checks that every declared trunk segment exists on the exact PCB, applies the
declared distributed load to each shared segment, and reports copper-only
drop/loss at 20 C and 75 C.  Via barrels, package lands, switches and local
zone spreading are excluded and remain first-article measurement obligations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import pcbnew


RHO_OHM_MM_20C = 1.724e-5
COPPER_ALPHA = 0.00393
COPPER_THICKNESS_MM = 0.035


# (layer, start, end, width_mm, current_a).  Loads are intentionally applied
# to shared segments before they branch: four ports at 0.5 A plus the 0.1 A
# management channel cross the bank; the separate 0.6 A 3V3 branch remains on
# the local F.Cu protected zone and does not cross this B.Cu distributor.
PATHS = {
    "pd_input_spine": [
        ("B.Cu", (33.2, 107.6), (33.2, 100), 2.0, 2.1),
        ("B.Cu", (33.2, 100), (49.8, 100), 2.0, 2.1),
        ("B.Cu", (49.8, 100), (49.8, 103.2), 2.0, 2.1),
    ],
    "port1_left_branch": [
        ("B.Cu", (90, 113), (90, 103), 2.0, 2.1),
        ("B.Cu", (90, 103), (60, 103), 2.0, 1.1),
        ("B.Cu", (60, 103), (58, 103), 2.0, 0.6),
        ("B.Cu", (58, 103), (58, 90), 1.5, 0.6),
        ("B.Cu", (58, 90), (48, 90), 1.5, 0.6),
        ("B.Cu", (48, 90), (48, 59), 1.5, 0.5),
    ],
    "port3_right_branch": [
        ("B.Cu", (90, 113), (90, 103), 2.0, 2.1),
        ("B.Cu", (90, 103), (140, 103), 2.0, 1.0),
        ("B.Cu", (140, 103), (140, 59), 1.5, 1.0),
        ("F.Cu", (140, 59), (129, 59), 1.5, 1.0),
        ("F.Cu", (129, 59), (101.4, 59), 1.5, 0.5),
    ],
    "management_left_branch": [
        ("B.Cu", (90, 113), (90, 103), 2.0, 2.1),
        ("B.Cu", (90, 103), (60, 103), 2.0, 1.1),
        ("B.Cu", (60, 103), (58, 103), 2.0, 0.6),
        ("B.Cu", (58, 103), (58, 90), 1.5, 0.6),
        ("B.Cu", (58, 90), (48, 90), 1.5, 0.6),
        ("B.Cu", (48, 90), (40, 90), 1.5, 0.1),
        ("B.Cu", (40, 90), (40, 76), 1.5, 0.1),
    ],
}

PATH_NETS = {"pd_input_spine": "VBUS_PD"}


def near(a, b, tol=0.01):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def contains(track_start, track_end, declared_start, declared_end, tol=0.01):
    """True when the declared interval lies on one longer physical track."""
    vx, vy = track_end[0] - track_start[0], track_end[1] - track_start[1]
    length2 = vx * vx + vy * vy
    if length2 <= tol * tol:
        return False
    for point in (declared_start, declared_end):
        wx, wy = point[0] - track_start[0], point[1] - track_start[1]
        if abs(vx * wy - vy * wx) > tol * math.sqrt(length2):
            return False
        projection = (wx * vx + wy * vy) / length2
        if projection < -tol or projection > 1 + tol:
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--json", required=True)
    args = ap.parse_args()
    board_path = Path(args.board).resolve()
    board = pcbnew.LoadBoard(str(board_path))
    tracks = []
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA" or item.GetNetname() not in {
                "P5V_PROTECTED", "VBUS_PD"}:
            continue
        a, b = item.GetStart(), item.GetEnd()
        tracks.append((item.GetNetname(), item.GetLayerName(),
                       (pcbnew.ToMM(a.x), pcbnew.ToMM(a.y)),
                       (pcbnew.ToMM(b.x), pcbnew.ToMM(b.y)),
                       pcbnew.ToMM(item.GetWidth())))

    failures, rows = [], []
    for path_name, declared in PATHS.items():
        net = PATH_NETS.get(path_name, "P5V_PROTECTED")
        path_rows = []
        for layer, start, end, width, current in declared:
            candidates = [row for row in tracks if row[0] == net
                          and row[1] == layer
                          and abs(row[4] - width) <= 0.01
                          and contains(row[2], row[3], start, end)]
            exact = [row for row in candidates
                     if ((near(row[2], start) and near(row[3], end))
                         or (near(row[2], end) and near(row[3], start)))]
            matches = exact if exact else candidates
            if len(matches) != 1:
                failures.append(
                    f"{path_name}: expected one {layer} {start}->{end} "
                    f"w={width}, found {len(matches)}")
                continue
            length = math.dist(start, end)
            resistance_20 = RHO_OHM_MM_20C * length / (
                width * COPPER_THICKNESS_MM)
            path_rows.append({
                "net": net, "layer": layer,
                "start_mm": start, "end_mm": end,
                "length_mm": round(length, 6), "width_mm": width,
                "current_a": current,
                "resistance_mohm_20c": round(resistance_20 * 1000, 6),
            })
        temp_factor = 1 + COPPER_ALPHA * (75 - 20)
        drop_20 = sum(row["resistance_mohm_20c"] * row["current_a"]
                      for row in path_rows)
        loss_20 = sum(row["resistance_mohm_20c"] / 1000
                      * row["current_a"] ** 2 for row in path_rows)
        rows.append({
            "path": path_name, "segments": path_rows,
            "drop_mv_20c": round(drop_20, 6),
            "drop_mv_75c": round(drop_20 * temp_factor, 6),
            "loss_w_20c": round(loss_20, 6),
            "loss_w_75c": round(loss_20 * temp_factor, 6),
        })

    report = {
        "schema": 1, "gate": "PWR-COPPER-SKELETON",
        "board": str(board_path),
        "board_sha256": hashlib.sha256(board_path.read_bytes()).hexdigest(),
        "copper_thickness_mm": COPPER_THICKNESS_MM,
        "basis": "35 um copper; rho20=1.724e-5 ohm-mm; alpha=0.00393/C",
        "scope_exclusions": [
            "via barrels", "package lands and joints", "power switches",
            "local zone current spreading", "connector contact resistance"],
        "paths": rows, "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    out = Path(args.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for row in rows:
        print(f"{row['path']}: {row['drop_mv_75c']:.2f} mV, "
              f"{row['loss_w_75c']:.3f} W at 75 C copper")
    print(f"PWR-COPPER-SKELETON {report['verdict']}: "
          f"{len(failures)} geometry mismatch(es)")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
