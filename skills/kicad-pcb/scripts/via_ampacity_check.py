#!/usr/bin/env python3
"""A-VIA: grade declared series via-transfer banks on an exact PCB.

    /usr/bin/python3 via_ampacity_check.py BOARD.kicad_pcb ROUTE.yaml \
        [--json REPORT.json]

Input is the exact filled board plus ``via_ampacity`` in the route contract.
Each transfer names a net and tight rectangle; the checker inventories every
through via in that window and sums the declared per-finished-hole current
capacity.  Capacity data must name its source and temperature-rise basis.

VACUITY: a same-net via inside a declared rectangle can be counted even when
the real current does not cross it (for example, an isolated or bypassed
barrel). DRC/connectivity and human current-path review must independently
prove that the rectangle is a genuine series boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import pcbnew
import yaml


TOL_MM = 0.001


def _num(value, path):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{path} must be numeric") from exc
    if value <= 0:
        raise ValueError(f"{path} must be positive")
    return value


def _inside(pos, rect):
    x, y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
    return rect[0] - TOL_MM <= x <= rect[2] + TOL_MM \
        and rect[1] - TOL_MM <= y <= rect[3] + TOL_MM


def check(board_path: Path, route_path: Path):
    cfg = yaml.safe_load(route_path.read_text(encoding="utf-8-sig")) or {}
    contract = cfg.get("via_ampacity")
    if contract is None:
        return [], [], "A-VIA N-A: route contract declares no via_ampacity block"
    if not isinstance(contract, dict):
        return ["via_ampacity must be a mapping"], [], None
    failures = []
    source = str(contract.get("source", "")).strip()
    method = str(contract.get("method", "")).strip()
    if not source:
        failures.append("via_ampacity.source is required")
    if not method:
        failures.append("via_ampacity.method is required")
    try:
        rise = _num(contract.get("temperature_rise_c"),
                    "via_ampacity.temperature_rise_c")
    except ValueError as exc:
        failures.append(str(exc)); rise = None
    raw_caps = contract.get("capacity_by_finished_hole_mm")
    capacities = {}
    if not isinstance(raw_caps, dict) or not raw_caps:
        failures.append("via_ampacity.capacity_by_finished_hole_mm must be a non-empty mapping")
    else:
        for key, value in raw_caps.items():
            try:
                capacities[_num(key, f"capacity hole {key!r}")] = \
                    _num(value, f"capacity for {key!r}")
            except ValueError as exc:
                failures.append(str(exc))
    transfers = contract.get("transfers")
    if not isinstance(transfers, list) or not transfers:
        failures.append("via_ampacity.transfers must be a non-empty list")
        transfers = []

    board = pcbnew.LoadBoard(str(board_path))
    vias = [item for item in board.GetTracks()
            if item.GetClass() == "PCB_VIA"]
    rows = []
    names = set()
    for i, transfer in enumerate(transfers):
        path = f"via_ampacity.transfers[{i}]"
        if not isinstance(transfer, dict):
            failures.append(f"{path} must be a mapping")
            continue
        name = str(transfer.get("name", "")).strip()
        net = str(transfer.get("net", "")).strip()
        why = str(transfer.get("why", "")).strip()
        if not name or name in names:
            failures.append(f"{path}.name must be non-empty and unique")
        names.add(name)
        if not net or board.FindNet(net) is None:
            failures.append(f"{path}.net {net!r} is absent from the board")
        if not why:
            failures.append(f"{path}.why must explain the series boundary")
        rect = transfer.get("rect")
        if not isinstance(rect, list) or len(rect) != 4:
            failures.append(f"{path}.rect must be [x0,y0,x1,y1]")
            continue
        try:
            rect = [float(value) for value in rect]
        except (TypeError, ValueError):
            failures.append(f"{path}.rect must contain numbers")
            continue
        if rect[2] <= rect[0] or rect[3] <= rect[1]:
            failures.append(f"{path}.rect must have positive area")
            continue
        try:
            required = _num(transfer.get("required_continuous_a"),
                            f"{path}.required_continuous_a")
        except ValueError as exc:
            failures.append(str(exc)); required = 0.0
        selected = [via for via in vias
                    if via.GetNetname() == net and _inside(via.GetPosition(), rect)]
        groups = Counter()
        credited = 0.0
        unknown = []
        for via in selected:
            drill = pcbnew.ToMM(via.GetDrill())
            match = next((cap for hole, cap in capacities.items()
                          if abs(hole - drill) <= TOL_MM), None)
            groups[round(drill, 3)] += 1
            if match is None:
                unknown.append(drill)
            else:
                credited += match
        min_vias = int(transfer.get("minimum_vias", 1))
        if len(selected) < min_vias:
            failures.append(f"{name}: {len(selected)} via(s) in {rect}, need at least {min_vias}")
        if unknown:
            failures.append(f"{name}: uncredited finished-hole sizes "
                            f"{sorted(round(v, 3) for v in unknown)} mm")
        if credited + 1e-9 < required:
            failures.append(f"{name}: credited {credited:.3f} A below "
                            f"{required:.3f} A continuous requirement")
        rows.append({
            "name": name, "net": net, "rect_mm": rect,
            "required_continuous_a": required,
            "credited_capacity_a": round(credited, 6),
            "via_count": len(selected),
            "finished_hole_census_mm": {
                f"{hole:.3f}": count for hole, count in sorted(groups.items())},
            "why": why,
        })
    report = {
        "schema": 1,
        "gate": "A-VIA",
        "board": str(board_path.resolve()),
        "board_sha256": hashlib.sha256(board_path.read_bytes()).hexdigest(),
        "route_contract": str(route_path.resolve()),
        "source": source,
        "method": method,
        "temperature_rise_c": rise,
        "capacity_by_finished_hole_mm": capacities,
        "transfers": rows,
        "failures": failures,
        "verdict": "FAIL" if failures else "PASS",
    }
    return failures, report, None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("route_config")
    ap.add_argument("--json")
    args = ap.parse_args(argv)
    board, route = Path(args.board), Path(args.route_config)
    failures, report, note = check(board, route)
    if note:
        print(f"A-VIA input: board={board.resolve()} contract={route.resolve()}")
        print("A-VIA coverage: 0/0 declared transfer bank(s) graded")
        print(note)
        return 0
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"A-VIA input: board={board.resolve()} contract={route.resolve()}")
    print(f"A-VIA basis: {report['source']} ({report['method']}, "
          f"{report['temperature_rise_c']:g} C rise)")
    for row in report["transfers"]:
        print(f"  {row['name']}: {row['via_count']} via(s), "
              f"{row['credited_capacity_a']:.3f} A credited / "
              f"{row['required_continuous_a']:.3f} A required; "
              f"holes={row['finished_hole_census_mm']}")
    print(f"A-VIA coverage: {len(report['transfers'])}/"
          f"{len(report['transfers'])} declared transfer bank(s) graded")
    for failure in failures:
        print(f"  FAIL {failure}")
    if failures:
        print(f"A-VIA FAIL: {len(failures)} finding(s)")
        return 1
    print("A-VIA PASS: every declared series via bank meets its continuous-current basis")
    return 0


if __name__ == "__main__":
    sys.exit(main())
