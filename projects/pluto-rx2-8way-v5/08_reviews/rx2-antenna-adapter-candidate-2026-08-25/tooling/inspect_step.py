#!/usr/bin/env python3
"""Inspect a bound assembly STEP and compare model coverage to the PCB.

STEP occurrence coverage is always checked. Exact solid bounding boxes and a
component-only collision mesh additionally require CadQuery/OCP; absence of
that backend is reported as INCOMPLETE, never approximated from STEP text.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, load_json, sha256_file, validate_interface, write_json,
)


OCCURRENCE_RE = re.compile(
    r"NEXT_ASSEMBLY_USAGE_OCCURRENCE\s*\(\s*'[^']*'\s*,\s*'([^']*)'",
    re.I | re.S)
DESIGNATOR_RE = re.compile(r"^[A-Za-z]+[0-9]+[A-Za-z0-9_.+-]*$")


def step_designators(step_path: Path) -> list[str]:
    try:
        text = step_path.read_text(encoding="latin-1")
    except OSError as exc:
        raise EnclosureError(f"cannot read STEP {step_path}: {exc}") from exc
    refs = [match.group(1).replace("''", "'") for match in
            OCCURRENCE_RE.finditer(text)]
    return sorted(set(ref for ref in refs if DESIGNATOR_RE.fullmatch(ref)))


def _cadquery_geometry(step_path: Path, mesh_path: Path | None,
                       board_size: Sequence[float],
                       board_thickness: float) -> dict[str, Any]:
    try:
        import cadquery as cq
    except ImportError:
        return {
            "status": "INCOMPLETE",
            "backend": "unavailable",
            "reason": "CadQuery/OCP is not installed; exact STEP solids were not inspected",
        }
    try:
        imported = cq.importers.importStep(str(step_path))
        root_shape = imported.val()
        root_box = root_shape.BoundingBox()
        solids = imported.solids().vals()
        solid_rows = []
        # KiCad STEP assemblies commonly contain board-sized copper, mask, or
        # paste solids in addition to the dielectric substrate.  Treat every
        # board-sized thin solid as PCB material, but identify the substrate
        # only from a thickness close to the declared board thickness.  The
        # old upper-bound-only test made each copper sheet look like another
        # complete PCB and failed otherwise valid assemblies.
        board_outline_indices = []
        substrate_indices = []
        for index, solid in enumerate(solids):
            box = solid.BoundingBox()
            size = [float(box.xlen), float(box.ylen), float(box.zlen)]
            solid_rows.append({
                "index": index,
                "min_mm": [float(box.xmin), float(box.ymin), float(box.zmin)],
                "max_mm": [float(box.xmax), float(box.ymax), float(box.zmax)],
                "size_mm": size,
            })
            planar = sorted(size, reverse=True)[:2]
            target = sorted([float(board_size[0]), float(board_size[1])],
                            reverse=True)
            board_sized = (abs(planar[0] - target[0]) <= 1.0 and
                           abs(planar[1] - target[1]) <= 1.0)
            thickness = min(size)
            if board_sized and thickness <= float(board_thickness) + 0.5:
                board_outline_indices.append(index)
                if abs(thickness - float(board_thickness)) <= 0.5:
                    substrate_indices.append(index)
        if not solids:
            raise EnclosureError("CadQuery imported zero STEP solids")
        if len(substrate_indices) != 1:
            raise EnclosureError(
                "could not identify exactly one PCB substrate solid; "
                f"board_outline_candidates={board_outline_indices} "
                f"substrate_candidates={substrate_indices}")
        board_row = solid_rows[substrate_indices[0]]
        # PCB STEP exports also contain pads, tracks, mask, and plated features
        # as many small solids.  Anything wholly inside the substrate slab
        # (with a small fabrication-layer allowance on each face) is PCB
        # material rather than a component clearance body.  Components which
        # protrude above or below that slab remain in the collision subject.
        slab_margin = 0.1
        board_related_indices = [
            row["index"] for row in solid_rows
            if (row["min_mm"][2] >= board_row["min_mm"][2] - slab_margin and
                row["max_mm"][2] <= board_row["max_mm"][2] + slab_margin)
        ]
        component_indices = [index for index in range(len(solids))
                             if index not in board_related_indices]
        mesh_record = None
        if mesh_path is not None:
            if not component_indices:
                raise EnclosureError("STEP contains no component solids after PCB removal")
            mesh_path.parent.mkdir(parents=True, exist_ok=True)
            compound = cq.Compound.makeCompound([solids[index]
                                                 for index in component_indices])
            cq.exporters.export(compound, str(mesh_path), tolerance=0.03,
                                angularTolerance=0.1)
            if not mesh_path.is_file() or mesh_path.stat().st_size == 0:
                raise EnclosureError("CadQuery wrote no component mesh")
            mesh_record = {
                "path": mesh_path.name,
                "sha256": sha256_file(mesh_path),
                "size": mesh_path.stat().st_size,
            }
        registration = [
            -((board_row["min_mm"][0] + board_row["max_mm"][0]) / 2),
            -((board_row["min_mm"][1] + board_row["max_mm"][1]) / 2),
            -board_row["min_mm"][2],
        ]
        return {
            "status": "COMPLETE",
            "backend": "cadquery-step-exact",
            "solid_count": len(solids),
            "component_solid_count": len(component_indices),
            "pcb_outline_candidate_indices": board_outline_indices,
            "pcb_related_solid_indices": board_related_indices,
            "assembly_bbox_mm": {
                "min": [float(root_box.xmin), float(root_box.ymin), float(root_box.zmin)],
                "max": [float(root_box.xmax), float(root_box.ymax), float(root_box.zmax)],
                "size": [float(root_box.xlen), float(root_box.ylen), float(root_box.zlen)],
            },
            "pcb_solid": board_row,
            "case_registration_translate_mm_at_board_z0": registration,
            "component_mesh": mesh_record,
        }
    except Exception as exc:
        return {"status": "FAIL", "backend": "cadquery-step-exact",
                "reason": str(exc)}


def inspect(step_path: Path, interface_path: Path,
            mesh_path: Path | None) -> dict[str, Any]:
    interface = validate_interface(load_json(interface_path))
    occurrences = step_designators(step_path)
    occurrence_set = set(occurrences)
    expected = sorted(row["ref"] for row in interface["board"]["footprints"]
                      if row["model_declared"])
    missing = sorted(set(expected) - occurrence_set)
    access_refs = {row["ref"] for row in interface["board"]["access_candidates"]}
    unmodeled_access = sorted(row["ref"] for row in interface["board"]["footprints"]
                              if row["ref"] in access_refs and
                              not row["model_declared"])
    geometry = _cadquery_geometry(
        step_path, mesh_path, interface["board"]["outline"]["size_mm"],
        interface["board"]["thickness_mm"])
    zero_denominator = len(expected) == 0
    coverage_status = ("COMPLETE" if not zero_denominator and not missing and
                       not unmodeled_access else "FAIL")
    if coverage_status == "FAIL" or geometry["status"] == "FAIL":
        status = "FAIL"
    elif geometry["status"] != "COMPLETE":
        status = "INCOMPLETE"
    else:
        status = "COMPLETE"
    return {
        "schema": 1,
        "kind": "pcb-enclosure-step-inspection-v1",
        "status": status,
        "step": {"path": step_path.name, "sha256": sha256_file(step_path),
                 "size": step_path.stat().st_size},
        "interface": {"path": interface_path.name,
                      "sha256": sha256_file(interface_path),
                      "size": interface_path.stat().st_size},
        "occurrence_coverage": {
            "status": coverage_status,
            "zero_modeled_denominator": zero_denominator,
            "expected_modeled_refs": len(expected),
            "observed_designators": len(occurrences),
            "covered_modeled_refs": len(set(expected) & occurrence_set),
            "missing_modeled_refs": missing,
            "unmodeled_access_refs": unmodeled_access,
        },
        "geometry": geometry,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", type=Path)
    parser.add_argument("--interface", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--component-mesh", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        report = inspect(args.step.resolve(strict=True),
                         args.interface.resolve(strict=True),
                         args.component_mesh)
        write_json(args.output, report)
    except (OSError, EnclosureError) as exc:
        print(f"STEP INSPECTION ERROR — input: {args.step}: {exc}", file=sys.stderr)
        return 1
    coverage = report["occurrence_coverage"]
    print(
        f"STEP INSPECTION {report['status']} — input: {args.step} — "
        f"{coverage['covered_modeled_refs']}/{coverage['expected_modeled_refs']} "
        "modeled footprint refs covered")
    if coverage["missing_modeled_refs"]:
        print("missing modeled refs: " + ", ".join(coverage["missing_modeled_refs"]))
    if coverage["unmodeled_access_refs"]:
        print("unmodeled access refs: " + ", ".join(coverage["unmodeled_access_refs"]))
    if coverage["zero_modeled_denominator"]:
        print("modeled footprint denominator is zero")
    print(f"wrote {args.output}")
    return {"COMPLETE": 0, "FAIL": 1, "INCOMPLETE": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
