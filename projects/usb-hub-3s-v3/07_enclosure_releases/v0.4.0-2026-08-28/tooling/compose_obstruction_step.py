#!/usr/bin/env python3
"""Compose and independently replay the USB-hub obstruction STEP subject.

The selected composite STEP is byte-bound because it is the exact input to the
collision receipt.  A fresh CadQuery export is not required to reproduce those
serializer bytes.  Replay instead closes every source/tool identity, exact
occurrence and solid-selection census, a quantized per-solid geometry
signature, and the byte-exact component mesh derived from that selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if (SCRIPT_DIR / "enclosure_common.py").is_file():
    ENCLOSURE_TOOLS = SCRIPT_DIR
else:
    ENCLOSURE_TOOLS = (
        SCRIPT_DIR.parents[3] / "skills" / "pcb-enclosure" / "scripts")
if str(ENCLOSURE_TOOLS) not in sys.path:
    sys.path.insert(0, str(ENCLOSURE_TOOLS))

from enclosure_common import (  # noqa: E402
    EnclosureError,
    atomic_output,
    load_json,
    reject_symlink_path,
    run_bounded,
    sha256_file,
    stable_file_digest,
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
EXPECTED_MODELED_COUNT = 121
EXPECTED_OBSERVED_COUNT = 122
CADQUERY_VERSION = "2.8.0"
COMPOSITION_REPLAY_KIND = "usb-hub-v1.12-obstruction-composition-replay-v1"
VALIDATOR_SOURCE_PATH = (
    "projects/usb-hub-3s-v3/03_src/mechanical/compose_obstruction_step.py")
ENCLOSURE_COMMON_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/enclosure_common.py")
STEP_INSPECTOR_SOURCE_PATH = "skills/pcb-enclosure/scripts/inspect_step.py"
PROCESS_RUNNER_SOURCE_PATH = "skills/kicad-pcb/scripts/process_runner.py"
PIPELINE_RUNTIME_SOURCE_PATH = "skills/pcb-design/scripts/pipeline_runtime.py"


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EnclosureError(f"{where}: expected mapping")
    return value


def _exact(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    item = _mapping(value, where)
    if set(item) != fields:
        raise EnclosureError(
            f"{where}: fields differ; missing={sorted(fields - set(item))}, "
            f"unknown={sorted(set(item) - fields)}")
    return item


def _integer(value: Any, where: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or \
            (positive and value <= 0):
        raise EnclosureError(
            f"{where}: expected {'positive ' if positive else ''}integer")
    return value


def _identity(record: Mapping[str, Any]) -> tuple[Any, Any]:
    return record.get("sha256"), record.get("size")


def _require_identity(first: Any, second: Any, where: str) -> None:
    left = _mapping(first, f"{where} first binding")
    right = _mapping(second, f"{where} second binding")
    if _identity(left) != _identity(right):
        raise EnclosureError(f"{where}: size/hash identity differs")


def _basename_binding(path: Path) -> dict[str, Any]:
    return {"path": path.name, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def _canonical_binding(path: Path, canonical: str) -> dict[str, Any]:
    _, info, digest = stable_file_digest(path, f"tool {canonical}")
    return {"path": canonical, "sha256": digest, "size": info.st_size}


def _deployment_root() -> Path:
    """Return the project root live and the closure root when copied to tooling."""
    if (SCRIPT_DIR / "enclosure_common.py").is_file():
        return SCRIPT_DIR.parent.resolve(strict=True)
    project_root = SCRIPT_DIR.parents[1].resolve(strict=True)
    if project_root.name != "usb-hub-3s-v3":
        raise EnclosureError(
            "composition validator is outside the canonical USB-hub project")
    return project_root


def _runtime_tool(filename: str, canonical: str) -> Path:
    sibling = SCRIPT_DIR / filename
    if sibling.is_file():
        return reject_symlink_path(sibling, f"composition tool {filename}") \
            .resolve(strict=True)
    repository = SCRIPT_DIR.parents[3]
    return reject_symlink_path(
        repository / canonical, f"composition tool {filename}") \
        .resolve(strict=True)


def _tool_bindings() -> dict[str, dict[str, Any]]:
    records = {
        "validator": (Path(__file__).resolve(strict=True), VALIDATOR_SOURCE_PATH),
        "enclosure_common": (
            _runtime_tool("enclosure_common.py", ENCLOSURE_COMMON_SOURCE_PATH),
            ENCLOSURE_COMMON_SOURCE_PATH),
        "step_inspector": (
            _runtime_tool("inspect_step.py", STEP_INSPECTOR_SOURCE_PATH),
            STEP_INSPECTOR_SOURCE_PATH),
        "process_runner": (
            _runtime_tool("process_runner.py", PROCESS_RUNNER_SOURCE_PATH),
            PROCESS_RUNNER_SOURCE_PATH),
        "pipeline_runtime": (
            _runtime_tool("pipeline_runtime.py", PIPELINE_RUNTIME_SOURCE_PATH),
            PIPELINE_RUNTIME_SOURCE_PATH),
    }
    return {name: _canonical_binding(path, canonical)
            for name, (path, canonical) in records.items()}


def _root_binding(path: Path, root: Path, *, digest: str | None = None,
                  size: int | None = None, where: str) -> dict[str, Any]:
    absolute = reject_symlink_path(path, where).resolve(strict=True)
    safe_root = reject_symlink_path(root, f"{where} root").resolve(strict=True)
    try:
        relative = absolute.relative_to(safe_root).as_posix()
    except ValueError as exc:
        raise EnclosureError(f"{where}: file is outside composition root") from exc
    if digest is None or size is None:
        _, info, actual_digest = stable_file_digest(absolute, where)
        digest = actual_digest
        size = info.st_size
    return {"path": relative, "sha256": digest, "size": size}


def _bound_root_file(root: Path, raw: Any, where: str) -> Path:
    record = _exact(raw, {"path", "sha256", "size"}, where)
    relative = record["path"]
    if not isinstance(relative, str) or not relative or \
            Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise EnclosureError(f"{where}.path: expected safe root-relative path")
    root = reject_symlink_path(root, f"{where} root").resolve(strict=True)
    path = reject_symlink_path(root / relative, where).resolve(strict=True)
    if not path.is_relative_to(root):
        raise EnclosureError(f"{where}: path escaped composition root")
    _, info, digest = stable_file_digest(path, where)
    if (digest, info.st_size) != _identity(record):
        raise EnclosureError(f"{where}: size/hash differs from bound file")
    return path


def require_bound(record: Any, actual: Mapping[str, Any], where: str) -> None:
    if not isinstance(record, Mapping) or _identity(record) != _identity(actual):
        raise EnclosureError(f"{where}: size/hash mismatch")


def _quantized(value: float, quantum: float, where: str) -> int:
    if not math.isfinite(value):
        raise EnclosureError(f"{where}: non-finite geometry value")
    return int(round(value / quantum))


def _geometry_signature(root_shape: Any, solids: Sequence[Any]) -> dict[str, Any]:
    """Hash stable semantic descriptors, not nondeterministic STEP text."""
    linear_quantum = 1e-6
    volume_quantum = 1e-6
    area_quantum = 1e-6
    descriptors: list[dict[str, Any]] = []
    for index, solid in enumerate(solids):
        box = solid.BoundingBox()
        center = solid.Center()
        descriptors.append({
            "index": index,
            "bbox_q": [_quantized(item, linear_quantum, "solid bbox") for item in (
                float(box.xmin), float(box.ymin), float(box.zmin),
                float(box.xmax), float(box.ymax), float(box.zmax))],
            "center_q": [_quantized(item, linear_quantum, "solid center")
                         for item in (float(center.x), float(center.y),
                                      float(center.z))],
            "volume_q": _quantized(float(solid.Volume()), volume_quantum,
                                    "solid volume"),
            "area_q": _quantized(float(solid.Area()), area_quantum,
                                  "solid area"),
        })
    encoded = json.dumps(
        descriptors, sort_keys=True, separators=(",", ":")).encode("ascii")
    root_box = root_shape.BoundingBox()
    return {
        "method": "ordered-solid-bbox-center-volume-area-v1",
        "linear_quantum_mm": linear_quantum,
        "volume_quantum_mm3": volume_quantum,
        "area_quantum_mm2": area_quantum,
        "solid_count": len(descriptors),
        "assembly_bbox_q": [
            _quantized(item, linear_quantum, "assembly bbox") for item in (
                float(root_box.xmin), float(root_box.ymin), float(root_box.zmin),
                float(root_box.xmax), float(root_box.ymax), float(root_box.zmax))],
        "solid_descriptors_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def compose(parent_step: Path, supplement_step: Path, interface_path: Path,
            augmentation_receipt_path: Path, output_step: Path,
            component_mesh: Path, report_path: Path, *,
            binding_root: Path | None = None) -> dict[str, Any]:
    try:
        import cadquery as cq
        import OCP
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise EnclosureError("CadQuery/OCP is required for exact composition") from exc

    if cq.__version__ != CADQUERY_VERSION:
        raise EnclosureError(
            f"composition requires cadquery=={CADQUERY_VERSION}, got "
            f"{cq.__version__}")
    root = (binding_root or _deployment_root()).resolve(strict=True)
    sources = [parent_step, supplement_step, interface_path,
               augmentation_receipt_path]
    tools = _tool_bindings()
    tool_paths = [
        _runtime_tool(filename, tools[name]["path"])
        for filename, name in (
            ("enclosure_common.py", "enclosure_common"),
            ("inspect_step.py", "step_inspector"),
            ("process_runner.py", "process_runner"),
            ("pipeline_runtime.py", "pipeline_runtime"),
        )
    ]
    protected = [*sources, *tool_paths, Path(__file__).resolve(strict=True)]

    with ExitStack() as stack:
        parent_snapshot, parent_record = stack.enter_context(
            stable_input_snapshot(parent_step, "parent STEP"))
        supplement_snapshot, supplement_record = stack.enter_context(
            stable_input_snapshot(supplement_step, "supplemental STEP"))
        interface_snapshot, interface_record = stack.enter_context(
            stable_input_snapshot(interface_path, "board interface"))
        augmentation_snapshot, augmentation_record = stack.enter_context(
            stable_input_snapshot(augmentation_receipt_path,
                                  "augmentation receipt"))

        interface = validate_interface(load_json(interface_snapshot))
        augmentation = load_json(augmentation_snapshot)
        if augmentation.get("kind") != \
                "usb-hub-v1.12-obstruction-augmentation-receipt-v1" or \
                augmentation.get("status") != "COMPLETE" or \
                augmentation.get("scope") != "supplemental_obstruction_solids":
            raise EnclosureError(
                "augmentation receipt is not COMPLETE supplemental evidence")
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
        observed = parent_occurrences | supplement_occurrences
        if len(expected_modeled) != EXPECTED_MODELED_COUNT or \
                observed & expected_modeled != expected_modeled or \
                len(observed) != EXPECTED_OBSERVED_COUNT or \
                "SW1" not in supplement_occurrences:
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
                inputs=protected, temporary_suffix=".step") as (temporary, stream):
            stream.flush()
            cq.exporters.export(composite, str(temporary), exportType="STEP")
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise EnclosureError("CadQuery wrote no composite STEP")

        composite_import = cq.importers.importStep(str(output_step))
        composite_shape = composite_import.val()
        composite_solids = composite_import.solids().vals()
        expected_solid_count = len(parent_solids) + len(supplement_solids)
        if len(composite_solids) != expected_solid_count:
            raise EnclosureError(
                f"composite solid census changed: {len(composite_solids)} != "
                f"{expected_solid_count}")
        board = interface["board"]
        geometry = _cadquery_geometry(
            output_step, component_mesh, board["outline"]["size_mm"],
            board["thickness_mm"], [*protected, output_step, report_path])
        if geometry.get("status") != "COMPLETE" or \
                geometry.get("solid_count") != expected_solid_count:
            raise EnclosureError(
                f"composite exact geometry failed: "
                f"{geometry.get('reason', geometry)}")
        covered = sorted(expected_modeled & observed)
        input_bindings = {
            "parent_step": _root_binding(
                parent_step, root, digest=parent_record["sha256"],
                size=parent_record["size"], where="parent STEP"),
            "supplement_step": _root_binding(
                supplement_step, root, digest=supplement_record["sha256"],
                size=supplement_record["size"], where="supplemental STEP"),
            "interface": _root_binding(
                interface_path, root, digest=interface_record["sha256"],
                size=interface_record["size"], where="board interface"),
            "augmentation_receipt": _root_binding(
                augmentation_receipt_path, root,
                digest=augmentation_record["sha256"],
                size=augmentation_record["size"],
                where="augmentation receipt"),
        }
        output_bindings = {
            "composite_step": _root_binding(
                output_step, root, where="composite STEP"),
            "component_mesh": _root_binding(
                component_mesh, root, where="component mesh"),
        }
        report = {
            "schema": 1,
            "kind": "pcb-enclosure-step-inspection-v1",
            "status": "COMPLETE",
            "step": _basename_binding(output_step),
            "interface": {
                "path": interface_record["name"],
                "sha256": interface_record["sha256"],
                "size": interface_record["size"],
            },
            "occurrence_coverage": {
                "status": "COMPLETE",
                "zero_modeled_denominator": False,
                "expected_modeled_refs": len(expected_modeled),
                "observed_designators": len(observed),
                "covered_modeled_refs": len(covered),
                "missing_modeled_refs": [],
                "unmodeled_access_refs": [],
                "supplemented_access_refs": ["SW1"],
            },
            "geometry": geometry,
            "composition": {
                "kind": "pcb-enclosure-obstruction-composition-v1",
                "parent_step": {
                    "path": parent_record["name"],
                    "sha256": parent_record["sha256"],
                    "size": parent_record["size"],
                    "solid_count": len(parent_solids),
                },
                "supplemental_step": {
                    "path": supplement_record["name"],
                    "sha256": supplement_record["sha256"],
                    "size": supplement_record["size"],
                    "solid_count": len(supplement_solids),
                    "refs": sorted(supplement_occurrences),
                },
                "augmentation_receipt": {
                    "path": augmentation_record["name"],
                    "sha256": augmentation_record["sha256"],
                    "size": augmentation_record["size"],
                },
                "solid_count": expected_solid_count,
                "coverage_union_complete": True,
            },
            "composition_replay": {
                "schema": 1,
                "kind": COMPOSITION_REPLAY_KIND,
                "tooling": tools,
                "backend": {
                    "name": "cadquery-ocp-step-composition",
                    "cadquery_version": cq.__version__,
                    "ocp_version": OCP.__version__,
                },
                "inputs": input_bindings,
                "outputs": output_bindings,
                "selection": {
                    "parent_solid_count": len(parent_solids),
                    "supplement_solid_count": len(supplement_solids),
                    "composite_solid_count": expected_solid_count,
                    "pcb_outline_candidate_indices":
                        geometry["pcb_outline_candidate_indices"],
                    "pcb_related_solid_indices":
                        geometry["pcb_related_solid_indices"],
                    "component_solid_count": geometry["component_solid_count"],
                },
                "occurrences": {
                    "parent_refs": sorted(parent_occurrences),
                    "supplement_refs": sorted(supplement_occurrences),
                    "covered_modeled_refs": covered,
                    "supplemented_access_refs": ["SW1"],
                },
                "geometry_signature": _geometry_signature(
                    composite_shape, composite_solids),
            },
        }
        write_json(
            report_path, report,
            inputs=[*protected, output_step, component_mesh],
            root=report_path.parent, where="composite STEP inspection")
    return validate_composition_receipt(report_path, binding_root=root)


def _validate_tooling(raw: Any) -> dict[str, Mapping[str, Any]]:
    expected = _tool_bindings()
    tooling = _exact(raw, set(expected), "composition replay tooling")
    for name, actual in expected.items():
        record = _exact(
            tooling[name], {"path", "sha256", "size"},
            f"composition replay tooling.{name}")
        if dict(record) != actual:
            raise EnclosureError(
                f"composition replay tooling.{name}: canonical bytes differ")
    return dict(tooling)


def validate_composition_receipt(
        report_path: Path, *, binding_root: Path | None = None) -> dict[str, Any]:
    """Stable-validate every selected input, output, tool, and census."""
    report_path = reject_symlink_path(
        report_path, "composition receipt").resolve(strict=True)
    root = (binding_root or _deployment_root()).resolve(strict=True)
    if not report_path.is_relative_to(root):
        raise EnclosureError("composition receipt is outside composition root")
    receipt = load_json(report_path)
    top = _exact(receipt, {
        "schema", "kind", "status", "step", "interface",
        "occurrence_coverage", "geometry", "composition",
        "composition_replay",
    }, "composition receipt")
    if top["schema"] != 1 or isinstance(top["schema"], bool) or \
            top["kind"] != "pcb-enclosure-step-inspection-v1" or \
            top["status"] != "COMPLETE":
        raise EnclosureError(
            "composition receipt must be the COMPLETE STEP-inspection v1 kind")
    replay = _exact(top["composition_replay"], {
        "schema", "kind", "tooling", "backend", "inputs", "outputs",
        "selection", "occurrences", "geometry_signature",
    }, "composition replay")
    if replay["schema"] != 1 or isinstance(replay["schema"], bool) or \
            replay["kind"] != COMPOSITION_REPLAY_KIND:
        raise EnclosureError("composition replay has wrong schema/kind")
    _validate_tooling(replay["tooling"])
    backend = _exact(
        replay["backend"], {"name", "cadquery_version", "ocp_version"},
        "composition replay backend")
    if backend["name"] != "cadquery-ocp-step-composition" or \
            backend["cadquery_version"] != CADQUERY_VERSION or \
            not isinstance(backend["ocp_version"], str) or \
            not backend["ocp_version"]:
        raise EnclosureError("composition replay backend is not pinned/valid")

    inputs = _exact(replay["inputs"], {
        "parent_step", "supplement_step", "interface",
        "augmentation_receipt",
    }, "composition replay inputs")
    input_paths = {
        name: _bound_root_file(root, record,
                               f"composition replay inputs.{name}")
        for name, record in inputs.items()
    }
    outputs = _exact(
        replay["outputs"], {"composite_step", "component_mesh"},
        "composition replay outputs")
    output_paths = {
        name: _bound_root_file(root, record,
                               f"composition replay outputs.{name}")
        for name, record in outputs.items()
    }
    all_paths = [*input_paths.values(), *output_paths.values(), report_path]
    if len(all_paths) != len(set(all_paths)):
        raise EnclosureError("composition receipt inputs/outputs must be distinct")

    step = _exact(top["step"], {"path", "sha256", "size"},
                  "composition receipt.step")
    interface = _exact(top["interface"], {"path", "sha256", "size"},
                       "composition receipt.interface")
    if step["path"] != output_paths["composite_step"].name or \
            interface["path"] != input_paths["interface"].name:
        raise EnclosureError("composition receipt local output/input names differ")
    _require_identity(step, outputs["composite_step"],
                      "selected composite STEP")
    _require_identity(interface, inputs["interface"],
                      "selected board interface")

    augmentation = load_json(input_paths["augmentation_receipt"])
    if augmentation.get("schema") != 1 or augmentation.get("kind") != \
            "usb-hub-v1.12-obstruction-augmentation-receipt-v1" or \
            augmentation.get("status") != "COMPLETE" or \
            augmentation.get("scope") != "supplemental_obstruction_solids" or \
            set(augmentation.get("installed_refs", [])) != EXPECTED_SUPPLEMENT_ALL:
        raise EnclosureError("bound augmentation receipt semantics changed")
    require_bound(augmentation.get("parent", {}).get("step"),
                  inputs["parent_step"], "augmentation parent STEP")
    require_bound(augmentation.get("outputs", {}).get("step"),
                  inputs["supplement_step"], "augmentation supplemental STEP")

    board_interface = validate_interface(load_json(input_paths["interface"]))
    expected_modeled = sorted(
        row["ref"] for row in board_interface["board"]["footprints"]
        if row["model_declared"])
    parent_refs = sorted(set(step_designators(input_paths["parent_step"])))
    supplement_refs = sorted(set(step_designators(input_paths["supplement_step"])))
    observed = sorted(set(parent_refs) | set(supplement_refs))
    if len(expected_modeled) != EXPECTED_MODELED_COUNT or \
            set(supplement_refs) != EXPECTED_SUPPLEMENT_ALL or \
            len(observed) != EXPECTED_OBSERVED_COUNT or \
            set(expected_modeled) - set(observed):
        raise EnclosureError("bound occurrence coverage changed")
    coverage = _exact(top["occurrence_coverage"], {
        "status", "zero_modeled_denominator", "expected_modeled_refs",
        "observed_designators", "covered_modeled_refs",
        "missing_modeled_refs", "unmodeled_access_refs",
        "supplemented_access_refs",
    }, "composition occurrence coverage")
    expected_coverage = {
        "status": "COMPLETE", "zero_modeled_denominator": False,
        "expected_modeled_refs": EXPECTED_MODELED_COUNT,
        "observed_designators": EXPECTED_OBSERVED_COUNT,
        "covered_modeled_refs": EXPECTED_MODELED_COUNT,
        "missing_modeled_refs": [], "unmodeled_access_refs": [],
        "supplemented_access_refs": ["SW1"],
    }
    if dict(coverage) != expected_coverage:
        raise EnclosureError("composition occurrence coverage is not 121/121 + SW1")
    occurrences = _exact(replay["occurrences"], {
        "parent_refs", "supplement_refs", "covered_modeled_refs",
        "supplemented_access_refs",
    }, "composition replay occurrences")
    expected_occurrences = {
        "parent_refs": parent_refs,
        "supplement_refs": supplement_refs,
        "covered_modeled_refs": expected_modeled,
        "supplemented_access_refs": ["SW1"],
    }
    if dict(occurrences) != expected_occurrences:
        raise EnclosureError("composition replay occurrence identities changed")

    composition = _exact(top["composition"], {
        "kind", "parent_step", "supplemental_step", "augmentation_receipt",
        "solid_count", "coverage_union_complete",
    }, "composition receipt composition")
    if composition["kind"] != "pcb-enclosure-obstruction-composition-v1" or \
            composition["coverage_union_complete"] is not True:
        raise EnclosureError("composition receipt composition semantics changed")
    parent_comp = _exact(composition["parent_step"], {
        "path", "sha256", "size", "solid_count",
    }, "composition parent STEP")
    supplement_comp = _exact(composition["supplemental_step"], {
        "path", "sha256", "size", "solid_count", "refs",
    }, "composition supplemental STEP")
    augmentation_comp = _exact(composition["augmentation_receipt"], {
        "path", "sha256", "size",
    }, "composition augmentation receipt")
    for record, input_name, path in (
            (parent_comp, "parent_step", input_paths["parent_step"]),
            (supplement_comp, "supplement_step", input_paths["supplement_step"]),
            (augmentation_comp, "augmentation_receipt",
             input_paths["augmentation_receipt"])):
        if record["path"] != path.name:
            raise EnclosureError(f"composition {input_name} basename changed")
        _require_identity(record, inputs[input_name],
                          f"composition {input_name}")
    if supplement_comp["refs"] != sorted(EXPECTED_SUPPLEMENT_ALL):
        raise EnclosureError("composition supplemental reference list changed")

    geometry = _mapping(top["geometry"], "composition geometry")
    if geometry.get("status") != "COMPLETE":
        raise EnclosureError("composition exact geometry is not COMPLETE")
    component_binding = _exact(
        geometry.get("component_mesh"), {"path", "sha256", "size"},
        "composition geometry component mesh")
    if component_binding["path"] != output_paths["component_mesh"].name:
        raise EnclosureError("composition component mesh basename changed")
    _require_identity(component_binding, outputs["component_mesh"],
                      "selected component mesh")
    selection = _exact(replay["selection"], {
        "parent_solid_count", "supplement_solid_count",
        "composite_solid_count", "pcb_outline_candidate_indices",
        "pcb_related_solid_indices", "component_solid_count",
    }, "composition replay selection")
    solid_count = _integer(selection["composite_solid_count"],
                           "composition composite solid count", positive=True)
    parent_count = _integer(selection["parent_solid_count"],
                            "composition parent solid count", positive=True)
    supplement_count = _integer(selection["supplement_solid_count"],
                                "composition supplement solid count", positive=True)
    pcb_related = selection["pcb_related_solid_indices"]
    pcb_candidates = selection["pcb_outline_candidate_indices"]
    if not isinstance(pcb_related, list) or not isinstance(pcb_candidates, list) or \
            any(isinstance(index, bool) or not isinstance(index, int) or
                index < 0 or index >= solid_count for index in pcb_related) or \
            any(isinstance(index, bool) or not isinstance(index, int) or
                index < 0 or index >= solid_count for index in pcb_candidates) or \
            len(pcb_related) != len(set(pcb_related)) or \
            len(pcb_candidates) != len(set(pcb_candidates)):
        raise EnclosureError("composition PCB/component selection is invalid")
    component_count = _integer(
        selection["component_solid_count"],
        "composition component solid count", positive=True)
    if parent_count != parent_comp["solid_count"] or \
            supplement_count != supplement_comp["solid_count"] or \
            solid_count != parent_count + supplement_count or \
            solid_count != composition["solid_count"] or \
            geometry.get("solid_count") != solid_count or \
            geometry.get("pcb_outline_candidate_indices") != pcb_candidates or \
            geometry.get("pcb_related_solid_indices") != pcb_related or \
            geometry.get("component_solid_count") != component_count or \
            component_count != solid_count - len(pcb_related):
        raise EnclosureError("composition solid/PCB/component selection differs")

    signature = _exact(replay["geometry_signature"], {
        "method", "linear_quantum_mm", "volume_quantum_mm3",
        "area_quantum_mm2", "solid_count", "assembly_bbox_q",
        "solid_descriptors_sha256",
    }, "composition replay geometry signature")
    if signature["method"] != "ordered-solid-bbox-center-volume-area-v1" or \
            signature["linear_quantum_mm"] != 1e-6 or \
            signature["volume_quantum_mm3"] != 1e-6 or \
            signature["area_quantum_mm2"] != 1e-6 or \
            signature["solid_count"] != solid_count or \
            not isinstance(signature["assembly_bbox_q"], list) or \
            len(signature["assembly_bbox_q"]) != 6 or \
            any(isinstance(item, bool) or not isinstance(item, int)
                for item in signature["assembly_bbox_q"]) or \
            not isinstance(signature["solid_descriptors_sha256"], str) or \
            len(signature["solid_descriptors_sha256"]) != 64:
        raise EnclosureError("composition geometry signature is malformed")

    # Stable-reopen every authority and selected output after all checks.
    for name, record in inputs.items():
        _bound_root_file(root, record, f"composition reopen input {name}")
    for name, record in outputs.items():
        _bound_root_file(root, record, f"composition reopen output {name}")
    _validate_tooling(replay["tooling"])
    if load_json(report_path) != receipt:
        raise EnclosureError("composition receipt changed during validation")
    return receipt


def _run_replay_command(command: Sequence[str], *, cwd: Path) -> None:
    result = run_bounded(
        command, cwd=cwd, timeout_s=1200,
        max_output_bytes_per_stream=1_000_000)
    if result.returncode != 0:
        raise EnclosureError(
            f"composition replay exited {result.returncode}; "
            f"output tail:\n{result.stdout[-4000:]}")


def replay_composition_receipt(report_path: Path) -> dict[str, Any]:
    """Recompose in a private pinned CadQuery process and compare semantics."""
    report_path = reject_symlink_path(
        report_path, "composition replay receipt").resolve(strict=True)
    root = _deployment_root()
    sealed = validate_composition_receipt(report_path, binding_root=root)
    replay = sealed["composition_replay"]
    inputs = replay["inputs"]
    outputs = replay["outputs"]
    input_paths = {
        name: _bound_root_file(root, record,
                               f"composition replay source {name}")
        for name, record in inputs.items()
    }
    output_paths = {
        name: _bound_root_file(root, record,
                               f"composition replay selected {name}")
        for name, record in outputs.items()
    }
    names = [path.name for path in input_paths.values()]
    names.extend(path.name for path in output_paths.values())
    names.append(report_path.name)
    if len(names) != len(set(names)):
        raise EnclosureError(
            "composition replay requires distinct input/output basenames")
    uv = shutil.which("uv")
    if uv is None:
        raise EnclosureError("composition replay requires uv in PATH")

    with tempfile.TemporaryDirectory(
            prefix="usb-hub-obstruction-composition-replay-") as raw_temp:
        temporary = Path(raw_temp)
        copied: dict[str, Path] = {}
        for name, source in input_paths.items():
            target = temporary / source.name
            shutil.copyfile(source, target)
            expected = inputs[name]
            _, info, digest = stable_file_digest(target, f"replay copy {name}")
            if (digest, info.st_size) != _identity(expected):
                raise EnclosureError(f"replay copy {name}: identity changed")
            copied[name] = target
        regenerated_step = temporary / output_paths["composite_step"].name
        regenerated_component = temporary / output_paths["component_mesh"].name
        regenerated_report = temporary / report_path.name
        command = [
            uv, "run", "--offline", "--with",
            f"cadquery=={replay['backend']['cadquery_version']}",
            "python", "-B", str(Path(__file__).resolve(strict=True)),
            "--parent-step", str(copied["parent_step"]),
            "--supplement-step", str(copied["supplement_step"]),
            "--interface", str(copied["interface"]),
            "--augmentation-receipt", str(copied["augmentation_receipt"]),
            "--output-step", str(regenerated_step),
            "--component-mesh", str(regenerated_component),
            "--report", str(regenerated_report),
            "--receipt-root", str(temporary),
        ]
        _run_replay_command(command, cwd=temporary)
        regenerated = validate_composition_receipt(
            regenerated_report, binding_root=temporary)
        regenerated_replay = regenerated["composition_replay"]

        for field in ("interface", "occurrence_coverage", "geometry",
                      "composition"):
            if regenerated[field] != sealed[field]:
                raise EnclosureError(
                    f"composition semantic replay differs at {field}")
        for field in ("tooling", "backend", "selection", "occurrences",
                      "geometry_signature"):
            if regenerated_replay[field] != replay[field]:
                raise EnclosureError(
                    f"composition semantic replay differs at {field}")
        for name in inputs:
            _require_identity(
                regenerated_replay["inputs"][name], inputs[name],
                f"regenerated composition input {name}")
        _require_identity(
            regenerated_replay["outputs"]["component_mesh"],
            outputs["component_mesh"], "regenerated component mesh")
        # Deliberately do not compare regenerated composite STEP bytes.  The
        # exact selected output was already reopened above; semantic geometry
        # and the derived component mesh are independently reproduced here.
        if regenerated_step == output_paths["composite_step"]:
            raise EnclosureError("composition replay did not use a private output")
    return validate_composition_receipt(report_path, binding_root=root)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent-step", type=Path)
    parser.add_argument("--supplement-step", type=Path)
    parser.add_argument("--interface", type=Path)
    parser.add_argument("--augmentation-receipt", type=Path)
    parser.add_argument("--output-step", type=Path)
    parser.add_argument("--component-mesh", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--receipt-root", type=Path, help=argparse.SUPPRESS)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--validate-receipt", type=Path)
    modes.add_argument("--replay-receipt", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.validate_receipt is not None:
            validate_composition_receipt(args.validate_receipt)
            print(f"OBSTRUCTION COMPOSITION RECEIPT VALID: {args.validate_receipt}")
            return 0
        if args.replay_receipt is not None:
            replay_composition_receipt(args.replay_receipt)
            print(f"OBSTRUCTION COMPOSITION REPLAY EXACT: {args.replay_receipt}")
            return 0
        required = {
            "--parent-step": args.parent_step,
            "--supplement-step": args.supplement_step,
            "--interface": args.interface,
            "--augmentation-receipt": args.augmentation_receipt,
            "--output-step": args.output_step,
            "--component-mesh": args.component_mesh,
            "--report": args.report,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise EnclosureError(
                "obstruction composition is missing required arguments: " +
                ", ".join(missing))
        for output in (args.output_step, args.component_mesh, args.report):
            validate_output_path(
                output, where="composition output", root=output.parent,
                inputs=[args.parent_step, args.supplement_step,
                        args.interface, args.augmentation_receipt])
        report = compose(
            reject_symlink_path(args.parent_step, "parent STEP")
                .resolve(strict=True),
            reject_symlink_path(args.supplement_step, "supplemental STEP")
                .resolve(strict=True),
            reject_symlink_path(args.interface, "board interface")
                .resolve(strict=True),
            reject_symlink_path(args.augmentation_receipt,
                                "augmentation receipt").resolve(strict=True),
            args.output_step, args.component_mesh, args.report,
            binding_root=args.receipt_root)
    except (EnclosureError, OSError, RuntimeError, ValueError) as exc:
        print(f"OBSTRUCTION COMPOSITION FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "OBSTRUCTION COMPOSITION COMPLETE: "
        f"{report['occurrence_coverage']['covered_modeled_refs']}/"
        f"{report['occurrence_coverage']['expected_modeled_refs']} modeled "
        f"refs + SW1; {report['geometry']['component_solid_count']} "
        "component solids")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
