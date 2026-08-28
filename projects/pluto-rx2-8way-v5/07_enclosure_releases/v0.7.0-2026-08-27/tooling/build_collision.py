#!/usr/bin/env python3
"""Build a hash-bound exact STEP-component/enclosure collision receipt.

The assembled-case STL must describe the enclosure in installed coordinates,
not a print-oriented lid or an exploded/render assembly.  CadQuery/OCP imports
the exact STEP solids; the inspector's PCB-solid census determines which STEP
solids are components.  The inspector mesh is retained as a bound audit
companion but is not substituted for the exact STEP geometry.
"""
from __future__ import annotations

import argparse
import math
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, atomic_output, load_json, reject_symlink_path,
    sha256_file, stable_input_snapshot, stl_metrics, validate_output_path,
    write_json,
)


KIND = "pcb-enclosure-collision-v1"


def _binding(path: Path) -> dict[str, Any]:
    return {"path": path.name, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def _binding_named(path: Path, name: str) -> dict[str, Any]:
    return {"path": name, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def _metrics_named(path: Path, name: str) -> dict[str, Any]:
    """Measure staged mesh bytes while recording their published filename."""
    metrics = stl_metrics(path)
    metrics["path"] = name
    return metrics


def _snapshot_binding(record: Mapping[str, Any]) -> dict[str, Any]:
    return {"path": Path(record["path"]).name,
            "sha256": record["sha256"], "size": record["size"]}


def _require_binding(path: Path, record: Any, where: str) -> None:
    if not path.is_file() or path.is_symlink() or \
            not isinstance(record, Mapping) or \
            record.get("sha256") != sha256_file(path) or \
            record.get("size") != path.stat().st_size:
        raise EnclosureError(f"{where}: bound size/hash differs from actual file")


def _empty_marker(path: Path) -> None:
    # STL has no portable zero-triangle representation accepted by the strict
    # verifier.  One explicitly recorded zero-area triangle is an honest,
    # zero-volume carrier for an exact empty BRep result.
    path.write_text(
        "solid exact_empty_intersection\n"
        "  facet normal 0 0 0\n"
        "    outer loop\n"
        "      vertex 0 0 0\n"
        "      vertex 0 0 0\n"
        "      vertex 0 0 0\n"
        "    endloop\n"
        "  endfacet\n"
        "endsolid exact_empty_intersection\n",
        encoding="ascii")


def _build_snapshots(
        step_path: Path, step_report_path: Path, component_mesh_path: Path,
        generation_path: Path, case_mesh_path: Path, source_path: Path,
        board_bottom_z: float, output: Path, report_path: Path,
        originals: Mapping[str, Path],
        bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    try:
        import cadquery as cq
        import OCP
        from OCP.BRepBuilderAPI import (BRepBuilderAPI_MakeSolid,
                                        BRepBuilderAPI_Sewing)
        from OCP.StlAPI import StlAPI_Reader
        from OCP.TopoDS import TopoDS, TopoDS_Shape
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise EnclosureError(
            "CadQuery/OCP is not installed; exact collision is unavailable") from exc

    if not math.isfinite(board_bottom_z):
        raise EnclosureError("board-bottom Z must be finite")

    generation = load_json(generation_path)
    if generation.get("kind") != "pcb-enclosure-generation-v1":
        raise EnclosureError("generation receipt has wrong kind")
    installed_case = generation.get("installed_case")
    if not isinstance(installed_case, Mapping) or \
            installed_case.get("selector") != "installed_case" or \
            installed_case.get("path") != "assembled-case.stl":
        raise EnclosureError("generation receipt lacks the fixed installed_case selector")
    _require_binding(case_mesh_path, installed_case,
                     "generation installed-case artifact")
    source_record = generation.get("source")
    if not isinstance(source_record, Mapping) or \
            not isinstance(source_record.get("path"), str) or \
            Path(source_record["path"]).name != source_record["path"]:
        raise EnclosureError("generation receipt lacks its CAD source identity")
    _require_binding(source_path, source_record, "generation CAD source")
    command = installed_case.get("command")
    engine = generation.get("engine")
    expected_tail = ["-D", 'part="installed_case"', "-D",
                     "show_reference_board=false"]
    if not isinstance(engine, Mapping) or not isinstance(command, list) or \
            len(command) != 8 or \
            command[1] != "-o" or Path(command[2]).resolve() != \
            originals["case_mesh"] or \
            command[3:7] != expected_tail or \
            Path(command[7]).resolve() != originals["source"] or \
            engine.get("executable") != command[0]:
        raise EnclosureError("generation installed_case command is not canonical")

    inspection = load_json(step_report_path)
    if inspection.get("kind") != "pcb-enclosure-step-inspection-v1" or \
            inspection.get("status") != "COMPLETE":
        raise EnclosureError("STEP inspection must be COMPLETE")
    _require_binding(step_path, inspection.get("step"), "STEP inspection subject")
    geometry = inspection.get("geometry")
    if not isinstance(geometry, Mapping) or geometry.get("status") != "COMPLETE":
        raise EnclosureError("STEP exact geometry report is not COMPLETE")
    _require_binding(component_mesh_path, geometry.get("component_mesh"),
                     "STEP component mesh")
    registration = geometry.get("case_registration_translate_mm_at_board_z0")
    if not isinstance(registration, list) or len(registration) != 3 or any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) for value in registration):
        raise EnclosureError("STEP inspection has invalid case registration")
    solid_count = geometry.get("solid_count")
    excluded = geometry.get("pcb_related_solid_indices")
    component_count = geometry.get("component_solid_count")
    if isinstance(solid_count, bool) or not isinstance(solid_count, int) or \
            solid_count <= 0 or not isinstance(excluded, list) or \
            any(isinstance(index, bool) or not isinstance(index, int) or
                index < 0 or index >= solid_count for index in excluded) or \
            len(set(excluded)) != len(excluded):
        raise EnclosureError("STEP inspection lacks a valid PCB-solid census")
    expected_components = solid_count - len(excluded)
    if component_count != expected_components or expected_components <= 0:
        raise EnclosureError("STEP inspection component-solid census is inconsistent")

    case_metrics = stl_metrics(case_mesh_path)
    if not case_metrics["edge_manifold"] or \
            not case_metrics["orientation_consistent"] or \
            case_metrics["component_absolute_volume_mm3"] <= 0:
        raise EnclosureError("assembled-case STL is not a closed oriented solid mesh")

    imported = cq.importers.importStep(str(step_path))
    step_solids = imported.solids().vals()
    if len(step_solids) != solid_count:
        raise EnclosureError(
            "exact STEP solid census changed since the inspection receipt")
    excluded_set = set(excluded)
    component_solids = [solid for index, solid in enumerate(step_solids)
                        if index not in excluded_set]
    applied_translate = [float(registration[0]), float(registration[1]),
                         float(registration[2]) + board_bottom_z]
    component_shape = cq.Compound.makeCompound(component_solids).translate(
        tuple(applied_translate))

    raw_case = TopoDS_Shape()
    if not StlAPI_Reader().Read(raw_case, str(case_mesh_path)):
        raise EnclosureError("OCP could not read assembled-case STL")
    sewing = BRepBuilderAPI_Sewing(1e-6, True, True, True, False)
    sewing.Add(raw_case)
    sewing.Perform()
    sewed = cq.Shape.cast(sewing.SewedShape())
    shells = sewed.Shells()
    if not shells:
        raise EnclosureError("assembled-case STL produced no sewable shell")
    case_solids = []
    for index, shell in enumerate(shells):
        if not shell.Closed() or not shell.isValid():
            raise EnclosureError(f"assembled-case shell {index} is open or invalid")
        maker = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(shell.wrapped))
        solid = cq.Shape.cast(maker.Solid())
        if not maker.IsDone() or not solid.isValid() or solid.Volume() <= 0:
            raise EnclosureError(f"assembled-case shell {index} did not make a valid solid")
        case_solids.append(solid)
    case_shape = (case_solids[0] if len(case_solids) == 1 else
                  cq.Compound.makeCompound(case_solids))

    intersection = case_shape.intersect(component_shape)
    if not intersection.isValid():
        raise EnclosureError("OCP intersection result is invalid")
    exact_volume = sum(abs(solid.Volume()) for solid in intersection.Solids())
    with atomic_output(
            output, where="collision mesh", root=output.parent,
            inputs=[*originals.values(), report_path],
            temporary_suffix=".stl") as (temporary, stream):
        stream.flush()
        if exact_volume <= 1e-12:
            _empty_marker(temporary)
            result = "EMPTY"
            representation = "zero-area-marker-for-empty-brep"
        else:
            cq.exporters.export(intersection, str(temporary), tolerance=0.01,
                                angularTolerance=0.1)
            if not temporary.is_file() or temporary.stat().st_size == 0:
                raise EnclosureError("CadQuery wrote no intersection mesh")
            result = "INTERSECTION"
            representation = "tessellation-of-exact-brep-common"
        collision_metrics = _metrics_named(temporary, output.name)
        collision_record = _binding_named(temporary, output.name)
    receipt = {
        "schema": 1,
        "kind": KIND,
        "status": "COMPLETE",
        "backend": {
            "name": "cadquery-ocp-brep-common",
            "cadquery_version": getattr(cq, "__version__", "unknown"),
            "ocp_version": getattr(OCP, "__version__", "unknown"),
        },
        "inputs": {
            "step_inspection": _snapshot_binding(bindings["step_report"]),
            "step": _snapshot_binding(bindings["step"]),
            "component_mesh": _snapshot_binding(bindings["component_mesh"]),
            "generation": _snapshot_binding(bindings["generation"]),
            "assembled_case_mesh": dict(installed_case),
        },
        "transform": {
            "case_registration_translate_mm_at_board_z0": [
                float(value) for value in registration],
            "board_bottom_z_mm": board_bottom_z,
            "applied_component_translate_mm": applied_translate,
        },
        "selection": {
            "step_solid_count": solid_count,
            "pcb_related_solid_count": len(excluded),
            "component_solid_count": expected_components,
        },
        "result": {
            "classification": result,
            "exact_brep_volume_mm3": exact_volume,
            "representation": representation,
            "collision_mesh": collision_record,
            "mesh_metrics": collision_metrics,
        },
    }
    write_json(
        report_path, receipt,
        inputs=[*originals.values(), output],
        root=report_path.parent, where="collision receipt")
    return receipt


def build(step_path: Path, step_report_path: Path, component_mesh_path: Path,
          generation_path: Path, case_mesh_path: Path, board_bottom_z: float,
          output: Path, report_path: Path) -> dict[str, Any]:
    """Snapshot every authority used by the multi-pass exact collision run."""
    input_paths = {
        "step": reject_symlink_path(step_path, "STEP input").resolve(strict=True),
        "step_report": reject_symlink_path(
            step_report_path, "STEP inspection input").resolve(strict=True),
        "component_mesh": reject_symlink_path(
            component_mesh_path, "component mesh input").resolve(strict=True),
        "generation": reject_symlink_path(
            generation_path, "generation input").resolve(strict=True),
        "case_mesh": reject_symlink_path(
            case_mesh_path, "assembled-case input").resolve(strict=True),
    }
    if not math.isfinite(board_bottom_z):
        raise EnclosureError("board-bottom Z must be finite")
    output = validate_output_path(
        output, where="collision mesh", root=output.parent,
        inputs=[*input_paths.values(), report_path])
    report_path = validate_output_path(
        report_path, where="collision receipt", root=output.parent,
        inputs=[*input_paths.values(), output])
    if report_path.parent != output.parent:
        raise EnclosureError(
            "collision mesh and receipt must share one build directory")
    for key in ("step_report", "component_mesh", "generation", "case_mesh"):
        if input_paths[key].parent != output.parent:
            raise EnclosureError(
                "STEP report, component mesh, generation receipt, and case "
                "mesh must share the output build directory")
    all_paths = [*input_paths.values(), output, report_path]
    if len(set(all_paths)) != len(all_paths):
        raise EnclosureError("collision inputs and outputs must be distinct files")
    for index, first in enumerate(all_paths):
        if not first.exists():
            continue
        for second in all_paths[index + 1:]:
            if second.exists() and first.samefile(second):
                raise EnclosureError(
                    "collision inputs and outputs must not be hardlink aliases")

    with ExitStack() as stack:
        snapshots: dict[str, Path] = {}
        bindings: dict[str, Mapping[str, Any]] = {}
        for key, path in input_paths.items():
            snapshot, binding = stack.enter_context(
                stable_input_snapshot(path, f"collision {key} input"))
            snapshots[key] = snapshot
            bindings[key] = binding
        generation = load_json(snapshots["generation"])
        source_record = generation.get("source")
        if not isinstance(source_record, Mapping) or \
                not isinstance(source_record.get("path"), str) or \
                Path(source_record["path"]).name != source_record["path"]:
            raise EnclosureError("generation receipt lacks its CAD source identity")
        source_original = reject_symlink_path(
            input_paths["generation"].parent / source_record["path"],
            "generation CAD source").resolve(strict=True)
        if source_original.parent != output.parent:
            raise EnclosureError(
                "generation CAD source must share the output build directory")
        validate_output_path(
            output, where="collision mesh", root=output.parent,
            inputs=[*input_paths.values(), source_original, report_path])
        validate_output_path(
            report_path, where="collision receipt", root=output.parent,
            inputs=[*input_paths.values(), source_original, output])
        source_snapshot, source_binding = stack.enter_context(
            stable_input_snapshot(source_original, "generation CAD source"))
        originals = {**input_paths, "source": source_original}
        bindings["source"] = source_binding
        return _build_snapshots(
            snapshots["step"], snapshots["step_report"],
            snapshots["component_mesh"], snapshots["generation"],
            snapshots["case_mesh"], source_snapshot, board_bottom_z,
            output, report_path, originals, bindings)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--step-inspection", type=Path, required=True)
    parser.add_argument("--component-mesh", type=Path, required=True)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--assembled-case-mesh", type=Path, required=True)
    parser.add_argument("--board-bottom-z-mm", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        receipt = build(
            reject_symlink_path(args.step, "STEP input").resolve(strict=True),
            reject_symlink_path(args.step_inspection,
                                "STEP inspection input").resolve(strict=True),
            reject_symlink_path(args.component_mesh,
                                "component mesh input").resolve(strict=True),
            reject_symlink_path(args.generation,
                                "generation input").resolve(strict=True),
            reject_symlink_path(args.assembled_case_mesh,
                                "assembled-case input").resolve(strict=True),
            args.board_bottom_z_mm, args.output, args.report)
    except (OSError, EnclosureError) as exc:
        print(f"ENCLOSURE COLLISION ERROR — {exc}", file=sys.stderr)
        return 1
    result = receipt["result"]
    print(
        f"ENCLOSURE COLLISION {result['classification']} — "
        f"{result['exact_brep_volume_mm3']:.9g} mm^3")
    print(f"wrote {args.output}")
    print(f"wrote {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
