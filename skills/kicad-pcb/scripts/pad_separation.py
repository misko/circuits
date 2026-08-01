#!/usr/bin/env python3
"""P-PADSEP: separate pads owned by different footprints.

Connectivity between components must be explicit copper (track, via, or zone),
not coincident land geometry.  KiCad DRC catches different-net overlap, but it
quite reasonably accepts same-net pads that overlap.  That left a blind spot:
an SMD resistor could be placed partly on a module castellation and every
connectivity-oriented gate would stay green.

This gate grades copper on every shared copper layer.  Pads in the SAME
footprint are excluded so composite/custom lands remain legal.  Pads in
DIFFERENT footprints must clear the selected fabrication tier's ``min_space``;
exact overlap and exact touch get their own finding IDs.  Paste from one
footprint may not intrude onto another footprint's copper land.

The tier floor is read from the project's ``nets.yaml`` when ``--project`` is
given.  Without a declared tier the gate still rejects overlap/touch and says
that positive-gap sizing was not graded; it never invents a manufacturing
number.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import pcbnew

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import fab_tier_util  # noqa: E402


@dataclass(frozen=True)
class PadRecord:
    ref: str
    number: str
    net: str
    pad: object
    copper: tuple[int, ...]

    @property
    def label(self) -> str:
        return f"{self.ref}.{self.number or '<unnumbered>'}"


@dataclass(frozen=True)
class Finding:
    code: str
    left: str
    right: str
    net_left: str
    net_right: str
    layer: str
    measured_mm: float
    required_mm: float
    area_mm2: float = 0.0


def _poly(pad, layer: int) -> object:
    out = pcbnew.SHAPE_POLY_SET()
    pad.TransformShapeToPolygon(
        out, layer, 0, 5000, pcbnew.ERROR_INSIDE)
    return out


def _paste_poly(pad, paste_layer: int, copper_layer: int) -> object:
    """Return the realized stencil aperture, including local/ratio margins.

    ``PAD.GetEffectiveShape(F_Paste)`` returns the base land on KiCad 10 and
    does not apply ``solder_paste_margin``.  KiCad does expose the already-
    combined X/Y margin, so resize a detached clone before polygonizing it.
    This also keeps the checker independent of Gerber export availability at
    the placement gate.
    """
    margin = pad.GetSolderPasteMargin(paste_layer)
    clone = pad.ClonePad()
    size = pad.GetSize()
    resized = pcbnew.VECTOR2I(size.x + 2 * margin.x,
                              size.y + 2 * margin.y)
    if resized.x <= 0 or resized.y <= 0:
        return pcbnew.SHAPE_POLY_SET()  # fully suppressed aperture
    clone.SetSize(resized)
    return _poly(clone, copper_layer)


def _intersection_area_mm2(left, right) -> float:
    intersection = pcbnew.SHAPE_POLY_SET(left)
    intersection.BooleanIntersection(right)
    # pcbnew geometry is in integer nanometres, so area is nm^2.
    return abs(float(intersection.Area())) / 1e12


def _bbox_distance_nm(left, right) -> int:
    """Cheap lower bound used only to skip pairs safely outside the floor."""
    a, b = left.GetBoundingBox(), right.GetBoundingBox()
    dx = max(0, max(a.GetLeft(), b.GetLeft()) - min(a.GetRight(), b.GetRight()))
    dy = max(0, max(a.GetTop(), b.GetTop()) - min(a.GetBottom(), b.GetBottom()))
    # max(dx, dy) is a conservative lower bound on Euclidean shape distance.
    return max(dx, dy)


def _layer_name(board, layer: int) -> str:
    try:
        return board.GetLayerName(layer)
    except Exception:
        return str(layer)


def grade_board(board, min_gap_mm: float) -> tuple[list[Finding], dict[str, int]]:
    pads: list[PadRecord] = []
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            copper = tuple(int(layer) for layer in pad.GetLayerSet().CuStack())
            if not copper:
                continue
            pads.append(PadRecord(
                footprint.GetReference(), str(pad.GetNumber()),
                pad.GetNetname() or "<unnetted>", pad, copper))

    findings: list[Finding] = []
    footprint_pairs: set[tuple[str, str]] = set()
    pair_count = 0
    measured_count = 0
    floor_nm = pcbnew.FromMM(min_gap_mm)
    poly_cache: dict[tuple[int, int], object] = {}

    for i, left in enumerate(pads):
        for right in pads[i + 1:]:
            if left.ref == right.ref:
                continue
            common = sorted(set(left.copper) & set(right.copper))
            if not common:
                continue
            pair_count += 1
            footprint_pairs.add(tuple(sorted((left.ref, right.ref))))
            # A bbox gap >= the requirement proves the real shapes clear it.
            # Equality is legal: the policy is ``gap >= min_space``.
            if _bbox_distance_nm(left.pad, right.pad) >= floor_nm and floor_nm:
                continue

            best_gap = None
            best_layer = None
            best_area = 0.0
            for layer in common:
                measured_count += 1
                a_shape = left.pad.GetEffectiveShape(layer)
                b_shape = right.pad.GetEffectiveShape(layer)
                gap = int(a_shape.GetClearance(b_shape))
                area = 0.0
                if gap <= 0:
                    for record in (left, right):
                        key = (id(record.pad), layer)
                        if key not in poly_cache:
                            poly_cache[key] = _poly(record.pad, layer)
                    area = _intersection_area_mm2(
                        poly_cache[(id(left.pad), layer)],
                        poly_cache[(id(right.pad), layer)])
                if best_gap is None or gap < best_gap or (
                        gap == best_gap and area > best_area):
                    best_gap, best_layer, best_area = gap, layer, area

            assert best_gap is not None and best_layer is not None
            gap_mm = pcbnew.ToMM(best_gap)
            if best_area > 1e-12:
                code = "P-PAD-OVERLAP"
            elif gap_mm <= 0.0:
                code = "P-PAD-TOUCH"
            elif gap_mm + 1e-9 < min_gap_mm:
                code = "P-PAD-GAP"
            else:
                continue
            findings.append(Finding(
                code, left.label, right.label, left.net, right.net,
                _layer_name(board, best_layer), gap_mm, min_gap_mm, best_area))

    # Paste is directional: A's stencil aperture intruding on B's copper is a
    # separate observation from B's aperture intruding on A's copper.
    paste_count = 0
    for pasted in pads:
        sides = []
        if pasted.pad.GetLayerSet().Contains(pcbnew.F_Paste) \
                and pcbnew.F_Cu in pasted.copper:
            sides.append((pcbnew.F_Paste, pcbnew.F_Cu))
        if pasted.pad.GetLayerSet().Contains(pcbnew.B_Paste) \
                and pcbnew.B_Cu in pasted.copper:
            sides.append((pcbnew.B_Paste, pcbnew.B_Cu))
        for paste_layer, copper_layer in sides:
            paste_poly = _paste_poly(pasted.pad, paste_layer, copper_layer)
            for foreign in pads:
                if pasted.ref == foreign.ref or copper_layer not in foreign.copper:
                    continue
                paste_count += 1
                copper_shape = foreign.pad.GetEffectiveShape(copper_layer)
                if not paste_poly.BBox().Intersects(copper_shape.BBox()):
                    continue
                copper_poly = poly_cache.get((id(foreign.pad), copper_layer))
                if copper_poly is None:
                    copper_poly = _poly(foreign.pad, copper_layer)
                    poly_cache[(id(foreign.pad), copper_layer)] = copper_poly
                area = _intersection_area_mm2(paste_poly, copper_poly)
                if area > 1e-12:
                    findings.append(Finding(
                        "P-PASTE-INTRUSION", pasted.label, foreign.label,
                        pasted.net, foreign.net, _layer_name(board, paste_layer),
                        0.0, 0.0, area))

    coverage = {
        "footprints": len({p.ref for p in pads}),
        "pads": len(pads),
        "footprint_pairs": len(footprint_pairs),
        "pad_pairs": pair_count,
        "shape_measurements": measured_count,
        "paste_pairs": paste_count,
    }
    return sorted(findings, key=lambda f: (
        f.code, f.left, f.right, f.layer)), coverage


def _resolve_gap(args) -> tuple[float, str]:
    if args.min_gap_mm is not None:
        if args.min_gap_mm < 0:
            raise ValueError("--min-gap-mm must be >= 0")
        return args.min_gap_mm, "command line"
    if args.project:
        tier = fab_tier_util.resolve(args.project, nets_path=args.nets)
        if tier:
            return float(tier["min_space"]), f"fab tier {tier['name']}"
    return 0.0, "no declared fab tier (overlap/touch only)"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("board", type=Path)
    p.add_argument("--project", type=Path)
    p.add_argument("--nets", type=Path,
                   help="board-scoped nets.yaml for a multi-board project")
    p.add_argument("--min-gap-mm", type=float,
                   help="override the project fab-tier min_space")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if not args.board.is_file():
        print(f"P-PADSEP FAIL: board does not exist: {args.board}")
        return 2
    try:
        min_gap, authority = _resolve_gap(args)
        board = pcbnew.LoadBoard(str(args.board))
        findings, coverage = grade_board(board, min_gap)
    except (ValueError, OSError, RuntimeError, fab_tier_util.FabTierError) as exc:
        print(f"P-PADSEP FAIL: {exc}")
        return 2

    print(f"P-PADSEP coverage: {coverage['pads']} copper pad(s) on "
          f"{coverage['footprints']} footprint(s); "
          f"{coverage['pad_pairs']} inter-footprint pad pair(s) across "
          f"{coverage['footprint_pairs']} footprint pair(s); "
          f"{coverage['paste_pairs']} paste-to-foreign-copper pair(s)")
    print(f"P-PADSEP floor: {min_gap:.3f} mm ({authority})")
    for f in findings:
        nets = f"[{f.net_left}] <-> [{f.net_right}]"
        if f.code in ("P-PAD-OVERLAP", "P-PASTE-INTRUSION"):
            detail = f"intersection {f.area_mm2:.6f} mm^2"
        elif f.code == "P-PAD-TOUCH":
            detail = "copper gap 0.000 mm"
        else:
            detail = (f"copper gap {f.measured_mm:.3f} mm < "
                      f"{f.required_mm:.3f} mm")
        print(f"  {f.code}: {f.left} {nets} {f.right} on {f.layer}: {detail}")
    if findings:
        print(f"P-PADSEP FAIL: {len(findings)} finding(s); move the footprints "
              "apart and join their nets with explicit track/zone copper")
        return 1
    print("P-PADSEP PASS: different-footprint lands are positively separated "
          "and paste does not intrude on foreign copper")
    return 0


if __name__ == "__main__":
    sys.exit(main())
