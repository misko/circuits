#!/usr/bin/env python3
"""Compose the sealed PCB STEP with hash-bound supplemental obstruction solids."""
from __future__ import annotations

import argparse
import math
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Mapping

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
ENCLOSURE_TOOLS = (SCRIPT_DIR if (SCRIPT_DIR / "enclosure_common.py").is_file()
                   else REPO_ROOT / "skills" / "pcb-enclosure" / "scripts")
if str(ENCLOSURE_TOOLS) not in sys.path:
    sys.path.insert(0, str(ENCLOSURE_TOOLS))

from enclosure_common import (  # noqa: E402
    EnclosureError,
    atomic_output,
    load_json,
    sha256_file,
    stable_input_snapshot,
    validate_interface,
    validate_output_path,
    write_json,
)
from inspect_step import _cadquery_geometry, inspect, step_designators  # noqa: E402


EXPECTED_SUPPLEMENT_MODELED = {
    "F2", "J1", "J2", "J3", "J4", "J5", "Q1", "Q2", "Q3", "Q4",
    "Q5", "Q6", "U3", "U4", "U5",
}
EXPECTED_SUPPLEMENT_ALL = EXPECTED_SUPPLEMENT_MODELED | {"SW1"}


def binding(path: Path) -> dict[str, Any]:
    return {"path": path.name, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def require_bound(record: Any, actual: Mapping[str, Any], where: str) -> None:
    if not isinstance(record, Mapping) or record.get("sha256") != actual["sha256"] \
            or record.get("size") != actual["size"]:
        raise EnclosureError(f"{where}: size/hash mismatch")


def compose(parent_step: Path, supplement_step: Path, interface_path: Path,
            augmentation_receipt_path: Path, output_step: Path,
            component_mesh: Path, report_path: Path) -> dict[str, Any]:
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise EnclosureError("CadQuery/OCP is required for exact composition") from exc

    sources = [parent_step, supplement_step, interface_path,
               augmentation_receipt_path]
    with ExitStack() as stack:
        parent_snapshot, parent_record = stack.enter_context(
            stable_input_snapshot(parent_step, "parent STEP"))
        supplement_snapshot, supplement_record = stack.enter_context(
            stable_input_snapshot(supplement_step, "supplemental STEP"))
        interface_snapshot, interface_record = stack.enter_context(
            stable_input_snapshot(interface_path, "board interface"))
        receipt_snapshot, receipt_record = stack.enter_context(
            stable_input_snapshot(augmentation_receipt_path,
                                  "augmentation receipt"))

        interface = validate_interface(load_json(interface_snapshot))
        augmentation = load_json(receipt_snapshot)
        if augmentation.get("kind") != \
                "usb-hub-v1.12-obstruction-augmentation-receipt-v1" or \
                augmentation.get("status") != "COMPLETE" or \
                augmentation.get("scope") != "supplemental_obstruction_solids":
            raise EnclosureError("augmentation receipt is not COMPLETE supplemental evidence")
        require_bound(augmentation.get("outputs", {}).get("step"),
                      supplement_record, "augmentation supplemental STEP")
        require_bound(augmentation.get("parent", {}).get("step"),
                      parent_record, "augmentation parent STEP")
        if set(augmentation.get("installed_refs", [])) != EXPECTED_SUPPLEMENT_ALL:
            raise EnclosureError("augmentation receipt reference census mismatch")

        parent_report = inspect(parent_snapshot, interface_snapshot, None)
        parent_geometry = parent_report.get("geometry")
        parent_coverage = parent_report.get("occurrence_coverage")
        if not isinstance(parent_geometry, Mapping) or \
                parent_geometry.get("status") != "COMPLETE":
            raise EnclosureError("parent STEP exact geometry is not COMPLETE")
        if not isinstance(parent_coverage, Mapping) or \
                set(parent_coverage.get("missing_modeled_refs", [])) != \
                EXPECTED_SUPPLEMENT_MODELED or \
                set(parent_coverage.get("unmodeled_access_refs", [])) != {"SW1"}:
            raise EnclosureError("parent STEP missing-reference census changed")

        parent_occurrences = set(step_designators(parent_snapshot))
        supplement_occurrences = set(step_designators(supplement_snapshot))
        if supplement_occurrences != EXPECTED_SUPPLEMENT_ALL:
            raise EnclosureError(
                "supplemental STEP occurrence census differs from the 16 bound refs")
        expected_modeled = {
            row["ref"] for row in interface["board"]["footprints"]
            if row["model_declared"]
        }
        if (parent_occurrences | supplement_occurrences) & expected_modeled != \
                expected_modeled or "SW1" not in supplement_occurrences:
            raise EnclosureError("composite occurrence coverage is incomplete")

        parent_import = cq.importers.importStep(str(parent_snapshot))
        supplement_import = cq.importers.importStep(str(supplement_snapshot))
        parent_solids = parent_import.solids().vals()
        supplement_solids = supplement_import.solids().vals()
        if len(parent_solids) != parent_geometry.get("solid_count") or \
                not supplement_solids:
            raise EnclosureError("STEP exact solid census changed")
        composite = cq.Compound.makeCompound(parent_solids + supplement_solids)
        with atomic_output(
                output_step, where="composite STEP", root=output_step.parent,
                inputs=sources, temporary_suffix=".step") as (temporary, stream):
            stream.flush()
            cq.exporters.export(composite, str(temporary), exportType="STEP")
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise EnclosureError("CadQuery wrote no composite STEP")

    composite_import = cq.importers.importStep(str(output_step))
    composite_solids = composite_import.solids().vals()
    expected_solid_count = len(parent_solids) + len(supplement_solids)
    if len(composite_solids) != expected_solid_count:
        raise EnclosureError(
            f"composite solid census changed: {len(composite_solids)} != "
            f"{expected_solid_count}")
    board = interface["board"]
    geometry = _cadquery_geometry(
        output_step, component_mesh, board["outline"]["size_mm"],
        board["thickness_mm"], [*sources, output_step, report_path])
    if geometry.get("status") != "COMPLETE" or \
            geometry.get("solid_count") != expected_solid_count:
        raise EnclosureError(
            f"composite exact geometry failed: {geometry.get('reason', geometry)}")
    covered = sorted(expected_modeled & (parent_occurrences | supplement_occurrences))
    report = {
        "schema": 1,
        "kind": "pcb-enclosure-step-inspection-v1",
        "status": "COMPLETE",
        "step": binding(output_step),
        "interface": {
            "path": interface_record["name"],
            "sha256": interface_record["sha256"],
            "size": interface_record["size"],
        },
        "occurrence_coverage": {
            "status": "COMPLETE",
            "zero_modeled_denominator": False,
            "expected_modeled_refs": len(expected_modeled),
            "observed_designators": len(parent_occurrences | supplement_occurrences),
            "covered_modeled_refs": len(covered),
            "missing_modeled_refs": [],
            "unmodeled_access_refs": [],
            "supplemented_access_refs": ["SW1"],
        },
        "geometry": geometry,
        "composition": {
            "kind": "pcb-enclosure-obstruction-composition-v1",
            "parent_step": {
                "path": parent_record["name"], "sha256": parent_record["sha256"],
                "size": parent_record["size"], "solid_count": len(parent_solids),
            },
            "supplemental_step": {
                "path": supplement_record["name"],
                "sha256": supplement_record["sha256"],
                "size": supplement_record["size"],
                "solid_count": len(supplement_solids),
                "refs": sorted(supplement_occurrences),
            },
            "augmentation_receipt": {
                "path": receipt_record["name"], "sha256": receipt_record["sha256"],
                "size": receipt_record["size"],
            },
            "solid_count": expected_solid_count,
            "coverage_union_complete": True,
        },
    }
    write_json(report_path, report,
               inputs=[parent_step, supplement_step, interface_path,
                       augmentation_receipt_path, output_step, component_mesh],
               root=report_path.parent, where="composite STEP inspection")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-step", type=Path, required=True)
    parser.add_argument("--supplement-step", type=Path, required=True)
    parser.add_argument("--interface", type=Path, required=True)
    parser.add_argument("--augmentation-receipt", type=Path, required=True)
    parser.add_argument("--output-step", type=Path, required=True)
    parser.add_argument("--component-mesh", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        for output in (args.output_step, args.component_mesh, args.report):
            validate_output_path(output, where="composition output",
                                 root=output.parent,
                                 inputs=[args.parent_step, args.supplement_step,
                                         args.interface,
                                         args.augmentation_receipt])
        report = compose(
            args.parent_step, args.supplement_step, args.interface,
            args.augmentation_receipt, args.output_step, args.component_mesh,
            args.report)
    except (EnclosureError, OSError, RuntimeError) as exc:
        print(f"OBSTRUCTION COMPOSITION FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "OBSTRUCTION COMPOSITION COMPLETE: "
        f"{report['occurrence_coverage']['covered_modeled_refs']}/"
        f"{report['occurrence_coverage']['expected_modeled_refs']} modeled refs + SW1; "
        f"{report['geometry']['component_solid_count']} component solids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
