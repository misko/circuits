#!/usr/bin/env python3
"""Grade every realized PCB via against the selected fab-tier aspect limit.

The route-entry tier preflight grades configured drill families.  This late
gate reads the exact saved board, inventories every ``PCB_VIA`` mechanical
drill, and compares it with the actual KiCad board thickness.  For blind or
buried vias the whole-board thickness is deliberately conservative until a
fabricator stackup supplies a smaller plated span.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pcbnew

from fab_tier_util import FabTierError, resolve as resolve_tier
from tier_preflight import board_scoped


def grade_rows(rows: list[dict[str, Any]], thickness_mm: float,
               limit: float) -> dict[str, Any]:
    """Pure aspect-ratio grader used by the CLI and focused fixtures."""
    failures: list[dict[str, Any]] = []
    census: dict[str, int] = {}
    graded = []
    for row in rows:
        drill = float(row["drill_mm"])
        ratio = float(thickness_mm) / drill if drill > 0 else float("inf")
        item = {**row, "span_mm": round(float(thickness_mm), 6),
                "aspect_ratio": round(ratio, 6),
                "limit": float(limit)}
        graded.append(item)
        key = f"{float(row['diameter_mm']):.3f}/{drill:.3f}"
        census[key] = census.get(key, 0) + 1
        if drill <= 0 or ratio > float(limit) + 1e-9:
            failures.append(item)
    return {
        "verdict": "FAIL" if failures else "PASS",
        "coverage": {"graded": len(graded), "total": len(rows)},
        "thickness_mm": float(thickness_mm),
        "max_pth_aspect_ratio": float(limit),
        "census": dict(sorted(census.items())),
        "failures": failures,
        "vias": graded,
    }


def _project_for(board_path: Path) -> Path:
    for parent in board_path.resolve().parents:
        if (parent / "03_src").is_dir():
            return parent
    raise ValueError(f"cannot locate project root above {board_path}")


def _board_thickness_mm(board: Any) -> float:
    settings = board.GetDesignSettings()
    raw = settings.GetBoardThickness()
    thickness = float(pcbnew.ToMM(raw))
    if thickness <= 0:
        raise ValueError("KiCad board thickness is absent or non-positive")
    return thickness


def inspect(board_path: Path, project: Path | None = None,
            board_name: str | None = None) -> dict[str, Any]:
    board_path = board_path.resolve()
    project = (project or _project_for(board_path)).resolve()
    nets_path, nets_note = board_scoped(
        project, "rules/nets.yaml", board_name)
    try:
        tier = resolve_tier(project, nets_path=nets_path)
    except FabTierError as exc:
        raise ValueError(str(exc)) from exc
    subject = {
        "path": str(board_path),
        "sha256": hashlib.sha256(board_path.read_bytes()).hexdigest(),
        "size": board_path.stat().st_size,
    }
    if tier is None:
        return {
            "schema": 1, "kind": "realized-via-aspect-v1",
            "verdict": "N-A", "subject": subject,
            "tier": None, "tier_source": nets_note,
            "reason": "board declares no fab_tier",
            "coverage": {"graded": 0, "total": 0},
            "census": {}, "failures": [], "vias": [],
        }
    limit = tier.get("max_pth_aspect_ratio")
    if limit is None:
        return {
            "schema": 1, "kind": "realized-via-aspect-v1",
            "verdict": "N-A", "subject": subject,
            "tier": tier.get("name"), "tier_source": nets_note,
            "reason": "selected fab tier declares no PTH aspect limit",
            "coverage": {"graded": 0, "total": 0},
            "census": {}, "failures": [], "vias": [],
        }

    board = pcbnew.LoadBoard(str(board_path))
    rows = []
    for item in board.GetTracks():
        if item.GetClass() != "PCB_VIA":
            continue
        pos = item.GetPosition()
        rows.append({
            "uuid": item.m_Uuid.AsString(),
            "net": str(item.GetNetname() or ""),
            "at_mm": [round(pcbnew.ToMM(pos.x), 6),
                      round(pcbnew.ToMM(pos.y), 6)],
            "diameter_mm": round(
                pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu)), 6),
            "drill_mm": round(pcbnew.ToMM(item.GetDrill()), 6),
            "span_basis": "conservative whole-board thickness",
        })
    result = grade_rows(rows, _board_thickness_mm(board), float(limit))
    return {
        "schema": 1, "kind": "realized-via-aspect-v1",
        "subject": subject, "tier": tier.get("name"),
        "tier_source": nets_note, **result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--board-name")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect(args.board, args.project, args.board_name)
    except (OSError, ValueError) as exc:
        print(f"R-VIA-ASPECT INCOMPLETE: {exc}")
        return 2
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
    coverage = report["coverage"]
    print(f"R-VIA-ASPECT {report['verdict']}: {coverage['graded']}/"
          f"{coverage['total']} exact via(s) graded; tier={report.get('tier')}")
    if report["verdict"] == "N-A":
        print(f"  {report['reason']}")
    for row in report.get("failures", [])[:20]:
        print(f"  FAIL {row['net'] or '(no net)'} at {row['at_mm']}: "
              f"{row['span_mm']:g}/{row['drill_mm']:g} = "
              f"{row['aspect_ratio']:.3f}:1 > {row['limit']:g}:1")
    return 1 if report["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
