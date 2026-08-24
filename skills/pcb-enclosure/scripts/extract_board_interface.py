#!/usr/bin/env python3
"""Extract an exact, hash-bound PCB mechanical interface with pcbnew.

The extractor inventories every footprint and drilled pad. Access-candidate
selection is deliberately conservative assistance, not semantic proof; callers
may add required refs with ``--access-ref`` and the enclosure config must
disposition every resulting candidate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    import pcbnew
except ImportError as exc:  # pragma: no cover - host dependency
    raise SystemExit("run with /usr/bin/python3 (pcbnew is unavailable)") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import INTERFACE_KIND, EnclosureError, sha256_file  # noqa: E402


AUTO_ACCESS_RE = re.compile(r"^(?:J|P|CN|USB|SW|F|TP)\d", re.I)


def mm(value: Any) -> float:
    return round(float(pcbnew.ToMM(value)), 6)


def _point(value: Any, cx: float, cy: float) -> list[float]:
    return [round(mm(value.x) - cx, 6), round(cy - mm(value.y), 6)]


def _outline(board: Any) -> tuple[dict[str, Any], float, float]:
    polygons = pcbnew.SHAPE_POLY_SET()
    if not board.GetBoardPolygonOutlines(polygons, False):
        raise EnclosureError("board outline is open or invalid")
    if polygons.OutlineCount() == 0:
        raise EnclosureError("board outline denominator is zero")
    bbox = polygons.BBox()
    left, top = mm(bbox.GetX()), mm(bbox.GetY())
    width, height = mm(bbox.GetWidth()), mm(bbox.GetHeight())
    cx, cy = left + width / 2.0, top + height / 2.0
    contours = []
    for index in range(polygons.OutlineCount()):
        contour = polygons.Outline(index)
        points = [_point(contour.CPoint(pi), cx, cy)
                  for pi in range(contour.PointCount())]
        if len(points) < 3:
            raise EnclosureError(f"outline contour {index} has <3 points")
        contours.append(points)
    return ({
        "contours_mm": contours,
        "bbox_mm": [round(-width / 2, 6), round(-height / 2, 6),
                    round(width / 2, 6), round(height / 2, 6)],
        "size_mm": [width, height],
    }, cx, cy)


def _pad_attribute(pad: Any) -> str:
    attr = pad.GetAttribute()
    if attr == pcbnew.PAD_ATTRIB_NPTH:
        return "NPTH"
    if attr == pcbnew.PAD_ATTRIB_PTH:
        return "PTH"
    return "SMD"


def extract(board_path: Path, required_access: Sequence[str]) -> dict[str, Any]:
    board = pcbnew.LoadBoard(str(board_path))
    if board is None:
        raise EnclosureError(f"cannot load board {board_path}")
    outline, cx, cy = _outline(board)
    footprints = []
    drills = []
    mounting = []
    by_ref = {}
    for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
        ref = str(fp.GetReference())
        pos = _point(fp.GetPosition(), cx, cy)
        bbox = fp.GetBoundingBox(False, False)
        fp_row = {
            "ref": ref,
            "value": str(fp.GetValue()),
            "footprint": str(fp.GetFPID().GetLibItemName()),
            "position_mm": pos,
            "rotation_deg": round(float(fp.GetOrientationDegrees()), 6),
            "side": "back" if fp.IsFlipped() else "front",
            "bbox_mm": [
                round(mm(bbox.GetX()) - cx, 6),
                round(cy - mm(bbox.GetBottom()), 6),
                round(mm(bbox.GetRight()) - cx, 6),
                round(cy - mm(bbox.GetY()), 6),
            ],
            "model_declared": len(fp.Models()) > 0,
        }
        footprints.append(fp_row)
        by_ref[ref] = fp_row
        for pad in fp.Pads():
            drill = pad.GetDrillSize()
            if drill.x <= 0 and drill.y <= 0:
                continue
            row = {
                "ref": ref,
                "pad": str(pad.GetNumber()),
                "position_mm": _point(pad.GetPosition(), cx, cy),
                "drill_mm": [mm(drill.x), mm(drill.y)],
                "attribute": _pad_attribute(pad),
            }
            drills.append(row)
            if (ref.upper().startswith(("H", "MH")) or
                    row["attribute"] == "NPTH" and
                    min(row["drill_mm"]) >= 2.0):
                mounting.append(row)
    if not footprints:
        raise EnclosureError("footprint denominator is zero")
    if not mounting:
        raise EnclosureError("mounting-hole denominator is zero")

    required = list(dict.fromkeys(required_access))
    missing = sorted(set(required) - set(by_ref))
    if missing:
        raise EnclosureError("required access refs absent from board: " +
                             ", ".join(missing))
    automatic = [row["ref"] for row in footprints
                 if AUTO_ACCESS_RE.match(row["ref"])]
    candidate_refs = list(dict.fromkeys(required + automatic))
    candidates = [{
        "ref": ref,
        "position_mm": by_ref[ref]["position_mm"],
        "value": by_ref[ref]["value"],
        "footprint": by_ref[ref]["footprint"],
        "selection": "required" if ref in required else "conservative-prefix",
    } for ref in candidate_refs]
    payload = {
        "schema": 1,
        "kind": INTERFACE_KIND,
        "subject": {"board": {
            "name": board_path.name,
            "sha256": sha256_file(board_path),
            "size": board_path.stat().st_size,
        }},
        "frame": {
            "units": "mm",
            "origin": "outline_bbox_center",
            "board_to_case": [
                [1, 0, 0, round(-cx, 6)],
                [0, -1, 0, round(cy, 6)],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
            "z_zero": "pcb_back_surface",
            "z_positive": "front",
        },
        "board": {
            "thickness_mm": mm(board.GetDesignSettings().GetBoardThickness()),
            "outline": outline,
            "drills": drills,
            "mounting_holes": mounting,
            "footprints": footprints,
            "access_candidates": candidates,
        },
        "coverage": {
            "footprints": len(footprints),
            "drills": len(drills),
            "mounting_holes": len(mounting),
            "access_candidates": len(candidates),
        },
    }
    return payload


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--access-ref", action="append", default=[],
                        help="refdes that must be dispositioned; repeatable")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        board = args.board.resolve(strict=True)
        payload = extract(board, args.access_ref)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    except (OSError, EnclosureError) as exc:
        print(f"INTERFACE EXTRACTION ERROR — input: {args.board}: {exc}",
              file=sys.stderr)
        return 1
    coverage = payload["coverage"]
    print(
        f"INTERFACE GENERATED — input: {board} — "
        f"{coverage['footprints']}/{coverage['footprints']} footprints, "
        f"{coverage['mounting_holes']}/{coverage['mounting_holes']} mounting holes, "
        f"{coverage['access_candidates']}/{coverage['access_candidates']} access candidates")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
