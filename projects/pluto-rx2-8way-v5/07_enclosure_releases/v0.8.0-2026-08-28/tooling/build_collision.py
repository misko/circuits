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
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, atomic_output, load_json, reject_symlink_path,
    run_bounded, sha256_file, stable_input_snapshot, stl_metrics,
    validate_output_path, write_json,
)


KIND = "pcb-enclosure-collision-v1"
COLLISION_BUILDER_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/build_collision.py")
ENCLOSURE_COMMON_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/enclosure_common.py")
STEP_INSPECTOR_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/inspect_step.py")
PROCESS_RUNNER_SOURCE_PATH = (
    "skills/kicad-pcb/scripts/process_runner.py")
PIPELINE_RUNTIME_SOURCE_PATH = (
    "skills/pcb-design/scripts/pipeline_runtime.py")


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


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EnclosureError(f"{where}: expected mapping")
    return value


def _exact(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    item = _mapping(value, where)
    actual = set(item)
    if actual != fields:
        raise EnclosureError(
            f"{where}: fields differ; missing={sorted(fields - actual)}, "
            f"unknown={sorted(actual - fields)}")
    return item


def _finite(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or \
            not math.isfinite(value):
        raise EnclosureError(f"{where}: expected finite number")
    return float(value)


def _integer(value: Any, where: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or \
            (positive and value <= 0):
        raise EnclosureError(
            f"{where}: expected {'positive ' if positive else ''}integer")
    return value


def _vector(value: Any, where: str) -> list[float]:
    if not isinstance(value, list) or len(value) != 3:
        raise EnclosureError(f"{where}: expected three-element vector")
    return [_finite(item, f"{where}[{index}]")
            for index, item in enumerate(value)]


def _local_bound_file(root: Path, record: Any, where: str) -> Path:
    binding = _exact(record, {"path", "sha256", "size"}, where)
    name = binding["path"]
    if not isinstance(name, str) or not name or Path(name).name != name:
        raise EnclosureError(f"{where}.path: expected basename-local path")
    path = reject_symlink_path(root / name, where).resolve(strict=True)
    if path.parent != root:
        raise EnclosureError(f"{where}.path: escaped receipt directory")
    _require_binding(path, binding, where)
    return path


def _runtime_tool_path(builder_path: Path, filename: str,
                       source_path: str) -> Path:
    sibling = builder_path.with_name(filename)
    if sibling.is_file():
        return sibling
    return builder_path.resolve().parents[3] / source_path


def validate_collision_receipt(
        report_path: Path, *, builder_path: Path | None = None,
        helper_path: Path | None = None,
        inspector_path: Path | None = None,
        process_runner_path: Path | None = None,
        pipeline_runtime_path: Path | None = None) -> dict[str, Any]:
    """Validate and stable-reopen every authority named by one receipt.

    This is deliberately a receipt validator rather than a mesh shortcut.  It
    closes the exact schema emitted below, the STEP inspector's component
    selection and transform, the generated installed case, the generation CAD
    source, and the published collision mesh.  Callers separately decide
    whether an EMPTY or INTERSECTION result is admissible.
    """
    report_path = reject_symlink_path(
        report_path, "collision receipt").resolve(strict=True)
    root = report_path.parent
    receipt = load_json(report_path)
    top = _exact(receipt, {
        "schema", "kind", "status", "builder", "enclosure_common",
        "step_inspector", "process_runner", "pipeline_runtime", "backend",
        "inputs", "transform", "selection", "result",
    }, "collision receipt")
    if top["schema"] != 1 or isinstance(top["schema"], bool) or \
            top["kind"] != KIND or top["status"] != "COMPLETE":
        raise EnclosureError(
            "collision receipt must be schema 1, the canonical kind, and "
            "COMPLETE")

    builder = _exact(
        top["builder"], {"path", "sha256", "size"},
        "collision receipt.builder")
    if builder["path"] != COLLISION_BUILDER_SOURCE_PATH:
        raise EnclosureError(
            "collision receipt builder does not name the canonical source")
    actual_builder = reject_symlink_path(
        builder_path or Path(__file__), "collision builder").resolve(strict=True)
    _require_binding(actual_builder, builder, "collision receipt builder")
    helper = _exact(
        top["enclosure_common"], {"path", "sha256", "size"},
        "collision receipt.enclosure_common")
    if helper["path"] != ENCLOSURE_COMMON_SOURCE_PATH:
        raise EnclosureError(
            "collision receipt helper does not name canonical enclosure_common")
    actual_helper = reject_symlink_path(
        helper_path or actual_builder.with_name("enclosure_common.py"),
        "collision schema helper").resolve(strict=True)
    _require_binding(actual_helper, helper, "collision receipt enclosure_common")
    inspector = _exact(
        top["step_inspector"], {"path", "sha256", "size"},
        "collision receipt.step_inspector")
    if inspector["path"] != STEP_INSPECTOR_SOURCE_PATH:
        raise EnclosureError(
            "collision receipt inspector does not name canonical inspect_step")
    actual_inspector = reject_symlink_path(
        inspector_path or actual_builder.with_name("inspect_step.py"),
        "collision STEP inspector").resolve(strict=True)
    _require_binding(
        actual_inspector, inspector, "collision receipt step_inspector")
    runtime_records = {
        "process_runner": (PROCESS_RUNNER_SOURCE_PATH, "process_runner.py",
                           process_runner_path),
        "pipeline_runtime": (PIPELINE_RUNTIME_SOURCE_PATH,
                             "pipeline_runtime.py", pipeline_runtime_path),
    }
    runtime_paths: dict[str, Path] = {}
    for name, (canonical, filename, override) in runtime_records.items():
        record = _exact(
            top[name], {"path", "sha256", "size"},
            f"collision receipt.{name}")
        if record["path"] != canonical:
            raise EnclosureError(
                f"collision receipt {name} has noncanonical source path")
        actual_path = reject_symlink_path(
            override or _runtime_tool_path(actual_builder, filename, canonical),
            f"collision {name}").resolve(strict=True)
        _require_binding(actual_path, record, f"collision receipt {name}")
        runtime_paths[name] = actual_path

    backend = _exact(
        top["backend"], {"name", "cadquery_version", "ocp_version"},
        "collision receipt.backend")
    if backend["name"] != "cadquery-ocp-brep-common" or any(
            not isinstance(backend[field], str) or not backend[field]
            for field in ("cadquery_version", "ocp_version")):
        raise EnclosureError("collision receipt has invalid backend authority")

    inputs = _exact(top["inputs"], {
        "step_inspection", "step", "component_mesh", "generation",
        "assembled_case_mesh", "interface",
    }, "collision receipt.inputs")
    paths = {
        name: _local_bound_file(root, inputs[name],
                                f"collision receipt.inputs.{name}")
        for name in ("step_inspection", "step", "component_mesh",
                     "generation", "interface")
    }
    generation = load_json(paths["generation"])
    if generation.get("schema") != 1 or generation.get("kind") != \
            "pcb-enclosure-generation-v1":
        raise EnclosureError("collision generation has wrong schema/kind")
    installed_case = _mapping(
        generation.get("installed_case"), "collision generation.installed_case")
    if dict(inputs["assembled_case_mesh"]) != dict(installed_case):
        raise EnclosureError(
            "collision assembled case differs from generation installed_case")
    if installed_case.get("selector") != "installed_case" or \
            installed_case.get("path") != "assembled-case.stl":
        raise EnclosureError(
            "collision generation lacks the fixed installed_case selector")
    case_path = _local_bound_file(
        root, {key: installed_case.get(key)
               for key in ("path", "sha256", "size")},
        "collision generation.installed_case")
    source = _mapping(
        generation.get("source"), "collision generation.source")
    source_path = _local_bound_file(
        root, {key: source.get(key) for key in ("path", "sha256", "size")},
        "collision generation.source")

    inspection = load_json(paths["step_inspection"])
    if inspection.get("schema") != 1 or inspection.get("kind") != \
            "pcb-enclosure-step-inspection-v1" or \
            inspection.get("status") != "COMPLETE":
        raise EnclosureError(
            "collision STEP inspection must be schema 1 and COMPLETE")
    if inspection.get("step") != inputs["step"]:
        raise EnclosureError(
            "collision STEP differs from the inspection subject")
    if inspection.get("interface") != inputs["interface"]:
        raise EnclosureError(
            "collision interface differs from the inspection authority")
    geometry = _mapping(
        inspection.get("geometry"), "collision STEP inspection.geometry")
    if geometry.get("status") != "COMPLETE" or \
            geometry.get("component_mesh") != inputs["component_mesh"]:
        raise EnclosureError(
            "collision component mesh differs from COMPLETE STEP inspection")
    registration = _vector(
        geometry.get("case_registration_translate_mm_at_board_z0"),
        "collision STEP registration")
    solid_count = _integer(
        geometry.get("solid_count"), "collision STEP solid_count", positive=True)
    excluded = geometry.get("pcb_related_solid_indices")
    if not isinstance(excluded, list) or any(
            isinstance(index, bool) or not isinstance(index, int) or
            index < 0 or index >= solid_count for index in excluded) or \
            len(excluded) != len(set(excluded)):
        raise EnclosureError("collision STEP PCB-solid census is invalid")
    component_count = solid_count - len(excluded)
    if component_count <= 0 or \
            geometry.get("component_solid_count") != component_count:
        raise EnclosureError("collision STEP component census is inconsistent")

    transform = _exact(top["transform"], {
        "case_registration_translate_mm_at_board_z0", "board_bottom_z_mm",
        "applied_component_translate_mm",
    }, "collision receipt.transform")
    recorded_registration = _vector(
        transform["case_registration_translate_mm_at_board_z0"],
        "collision receipt.transform.case_registration")
    board_bottom = _finite(
        transform["board_bottom_z_mm"],
        "collision receipt.transform.board_bottom_z_mm")
    applied = _vector(
        transform["applied_component_translate_mm"],
        "collision receipt.transform.applied_component_translate_mm")
    expected_applied = [registration[0], registration[1],
                        registration[2] + board_bottom]
    if recorded_registration != registration or applied != expected_applied:
        raise EnclosureError(
            "collision transform differs from STEP inspection/board Z")

    selection = _exact(top["selection"], {
        "step_solid_count", "pcb_related_solid_count", "component_solid_count",
    }, "collision receipt.selection")
    expected_selection = {
        "step_solid_count": solid_count,
        "pcb_related_solid_count": len(excluded),
        "component_solid_count": component_count,
    }
    if dict(selection) != expected_selection:
        raise EnclosureError(
            "collision selection differs from STEP inspection census")

    result = _exact(top["result"], {
        "classification", "exact_brep_volume_mm3", "representation",
        "collision_mesh", "mesh_metrics",
    }, "collision receipt.result")
    collision_path = _local_bound_file(
        root, result["collision_mesh"], "collision receipt.result.collision_mesh")
    volume = _finite(
        result["exact_brep_volume_mm3"],
        "collision receipt.result.exact_brep_volume_mm3")
    classification = result["classification"]
    representation = result["representation"]
    if classification == "EMPTY":
        if volume != 0 or representation != "zero-area-marker-for-empty-brep":
            raise EnclosureError("EMPTY collision result has invalid semantics")
    elif classification == "INTERSECTION":
        if volume <= 1e-12 or \
                representation != "tessellation-of-exact-brep-common":
            raise EnclosureError(
                "INTERSECTION collision result has invalid semantics")
    else:
        raise EnclosureError("collision result has unknown classification")
    expected_metrics = stl_metrics(collision_path)
    expected_metrics["path"] = collision_path.name
    if result["mesh_metrics"] != expected_metrics:
        raise EnclosureError(
            "collision mesh metrics differ from exact published mesh bytes")

    # Reopen every authority after validation.  This catches ordinary drift
    # and makes the validator a safe post-regrade boundary for v2 publication.
    _require_binding(actual_builder, builder, "collision receipt builder")
    _require_binding(actual_helper, helper, "collision receipt enclosure_common")
    _require_binding(
        actual_inspector, inspector, "collision receipt step_inspector")
    for name, path in runtime_paths.items():
        _require_binding(path, top[name], f"collision receipt {name}")
    for name in ("step_inspection", "step", "component_mesh", "generation",
                 "interface"):
        _require_binding(paths[name], inputs[name],
                         f"collision receipt.inputs.{name}")
    _require_binding(case_path, installed_case,
                     "collision generation.installed_case")
    _require_binding(source_path, source, "collision generation.source")
    _require_binding(collision_path, result["collision_mesh"],
                     "collision receipt.result.collision_mesh")
    if load_json(report_path) != receipt:
        raise EnclosureError("collision receipt changed during validation")
    return receipt


def _run_replay_command(command: Sequence[str], *, cwd: Path,
                        timeout_s: float = 600.0):
    """Use the one bounded pipeline runtime for release-local replay."""
    result = run_bounded(
        command, cwd=cwd, timeout_s=timeout_s,
        max_output_bytes_per_stream=1_000_000)
    if result.returncode != 0:
        raise EnclosureError(
            f"collision replay exited {result.returncode}; "
            f"output tail:\n{result.stdout[-4000:]}")
    return result


def replay_collision_receipt(
        report_path: Path, *, builder_path: Path | None = None,
        helper_path: Path | None = None, inspector_path: Path | None = None,
        process_runner_path: Path | None = None,
        pipeline_runtime_path: Path | None = None,
        runner: Any = None) -> dict[str, Any]:
    """Rebuild collision evidence in a private directory and require equality.

    The pinned CadQuery version is taken from the sealed receipt.  ``--offline``
    makes missing runtime authority a hard failure instead of a network fetch.
    A runner seam exists solely for closed synthetic unit fixtures; production
    callers omit it and execute the exact builder bytes through uv.
    """
    builder_path = reject_symlink_path(
        builder_path or Path(__file__), "collision replay builder") \
        .resolve(strict=True)
    receipt = validate_collision_receipt(
        report_path, builder_path=builder_path, helper_path=helper_path,
        inspector_path=inspector_path, process_runner_path=process_runner_path,
        pipeline_runtime_path=pipeline_runtime_path)
    report_path = reject_symlink_path(
        report_path, "collision replay receipt").resolve(strict=True)
    source_root = report_path.parent
    inputs = receipt["inputs"]
    generation = load_json(source_root / inputs["generation"]["path"])
    source = generation["source"]
    collision_mesh = receipt["result"]["collision_mesh"]
    names = [inputs[name]["path"] for name in (
        "step", "step_inspection", "component_mesh", "generation",
        "assembled_case_mesh", "interface")]
    names.extend((source["path"], collision_mesh["path"], report_path.name))
    if len(names) != len(set(names)):
        raise EnclosureError(
            "collision replay inputs and outputs must have distinct basenames")
    cadquery_version = receipt["backend"]["cadquery_version"]
    if not cadquery_version or any(
            char not in "0123456789." for char in cadquery_version):
        raise EnclosureError(
            "collision replay requires a numeric pinned CadQuery version")
    uv = shutil.which("uv")
    if uv is None:
        raise EnclosureError("collision replay requires uv in PATH")

    with tempfile.TemporaryDirectory(prefix="pcb-enclosure-collision-replay-") \
            as temporary_name:
        temporary = Path(temporary_name)
        copied: dict[str, Path] = {}
        for name in (*inputs,):
            if name == "assembled_case_mesh":
                continue
            record = inputs[name]
            source_path = source_root / record["path"]
            target = temporary / record["path"]
            shutil.copyfile(source_path, target)
            _require_binding(target, record, f"replay copy {name}")
            copied[name] = target
        case_record = inputs["assembled_case_mesh"]
        case_target = temporary / case_record["path"]
        shutil.copyfile(source_root / case_record["path"], case_target)
        _require_binding(case_target, case_record, "replay copy installed case")
        source_target = temporary / source["path"]
        shutil.copyfile(source_root / source["path"], source_target)
        _require_binding(source_target, source, "replay copy generation source")

        # Recompute the inspector's exact PCB/component selection before
        # trusting its indices in the collision build. Occurrence coverage may
        # be owned by a project-specific compose receipt, but exact geometry,
        # selection, and component mesh must reproduce under canonical code.
        inspector_regrade = temporary / "inspector-regrade"
        inspector_regrade.mkdir()
        regenerated_inspection_path = inspector_regrade / \
            inputs["step_inspection"]["path"]
        regenerated_component_path = inspector_regrade / \
            inputs["component_mesh"]["path"]
        inspector_executable = reject_symlink_path(
            inspector_path or builder_path.with_name("inspect_step.py"),
            "collision replay STEP inspector").resolve(strict=True)
        inspect_command = [
            uv, "run", "--offline", "--with",
            f"cadquery=={cadquery_version}", "python", "-B",
            str(inspector_executable), str(copied["step"]),
            "--interface", str(copied["interface"]),
            "--output", str(regenerated_inspection_path),
            "--component-mesh", str(regenerated_component_path),
            "--geometry-only",
        ]
        (runner or _run_replay_command)(inspect_command, cwd=inspector_regrade)
        regenerated_inspection = load_json(regenerated_inspection_path)
        sealed_inspection = load_json(copied["step_inspection"])
        for field in ("schema", "status", "step", "interface", "geometry"):
            if regenerated_inspection.get(field) != sealed_inspection.get(field):
                raise EnclosureError(
                    "STEP inspection exact geometry/selection does not "
                    f"reproduce at field {field}")
        _require_binding(
            regenerated_component_path, inputs["component_mesh"],
            "regenerated STEP component mesh")

        output = temporary / collision_mesh["path"]
        regenerated_report = temporary / report_path.name
        command = [
            uv, "run", "--offline", "--with",
            f"cadquery=={cadquery_version}", "python", "-B",
            str(builder_path),
            "--step", str(copied["step"]),
            "--step-inspection", str(copied["step_inspection"]),
            "--component-mesh", str(copied["component_mesh"]),
            "--interface", str(copied["interface"]),
            "--generation", str(copied["generation"]),
            "--assembled-case-mesh", str(case_target),
            "--board-bottom-z-mm",
            str(receipt["transform"]["board_bottom_z_mm"]),
            "--output", str(output), "--report", str(regenerated_report),
        ]
        (runner or _run_replay_command)(command, cwd=temporary)
        regenerated = validate_collision_receipt(
            regenerated_report, builder_path=builder_path,
            helper_path=helper_path, inspector_path=inspector_path,
            process_runner_path=process_runner_path,
            pipeline_runtime_path=pipeline_runtime_path)
        if regenerated != receipt:
            raise EnclosureError(
                "collision receipt does not reproduce exactly from its bound "
                "STEP/generation/case/builder inputs")
        _require_binding(output, collision_mesh,
                         "regenerated collision mesh")
    # Reopen the selected evidence after the independent replay.
    return validate_collision_receipt(
        report_path, builder_path=builder_path, helper_path=helper_path,
        inspector_path=inspector_path, process_runner_path=process_runner_path,
        pipeline_runtime_path=pipeline_runtime_path)


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
        interface_path: Path, generation_path: Path, case_mesh_path: Path,
        source_path: Path,
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
    replay_stable_command = (
        isinstance(command, list) and len(command) == 8 and
        command[2] == installed_case.get("path") and
        command[7] == source_record.get("path"))
    legacy_absolute_command = (
        isinstance(command, list) and len(command) == 8 and
        Path(command[2]).resolve() == originals["case_mesh"] and
        Path(command[7]).resolve() == originals["source"])
    if not isinstance(engine, Mapping) or not isinstance(command, list) or \
            len(command) != 8 or \
            command[1] != "-o" or \
            command[3:7] != expected_tail or \
            not (replay_stable_command or legacy_absolute_command) or \
            engine.get("executable") != command[0]:
        raise EnclosureError("generation installed_case command is not canonical")

    inspection = load_json(step_report_path)
    if inspection.get("kind") != "pcb-enclosure-step-inspection-v1" or \
            inspection.get("status") != "COMPLETE":
        raise EnclosureError("STEP inspection must be COMPLETE")
    _require_binding(step_path, inspection.get("step"), "STEP inspection subject")
    _require_binding(
        interface_path, inspection.get("interface"),
        "STEP inspection interface")
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
        "builder": {
            "path": COLLISION_BUILDER_SOURCE_PATH,
            "sha256": bindings["builder"]["sha256"],
            "size": bindings["builder"]["size"],
        },
        "enclosure_common": {
            "path": ENCLOSURE_COMMON_SOURCE_PATH,
            "sha256": bindings["enclosure_common"]["sha256"],
            "size": bindings["enclosure_common"]["size"],
        },
        "step_inspector": {
            "path": STEP_INSPECTOR_SOURCE_PATH,
            "sha256": bindings["step_inspector"]["sha256"],
            "size": bindings["step_inspector"]["size"],
        },
        "process_runner": {
            "path": PROCESS_RUNNER_SOURCE_PATH,
            "sha256": bindings["process_runner"]["sha256"],
            "size": bindings["process_runner"]["size"],
        },
        "pipeline_runtime": {
            "path": PIPELINE_RUNTIME_SOURCE_PATH,
            "sha256": bindings["pipeline_runtime"]["sha256"],
            "size": bindings["pipeline_runtime"]["size"],
        },
        "backend": {
            "name": "cadquery-ocp-brep-common",
            "cadquery_version": getattr(cq, "__version__", "unknown"),
            "ocp_version": getattr(OCP, "__version__", "unknown"),
        },
        "inputs": {
            "step_inspection": _snapshot_binding(bindings["step_report"]),
            "step": _snapshot_binding(bindings["step"]),
            "component_mesh": _snapshot_binding(bindings["component_mesh"]),
            "interface": _snapshot_binding(bindings["interface"]),
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
          interface_path: Path, generation_path: Path, case_mesh_path: Path,
          board_bottom_z: float, output: Path,
          report_path: Path) -> dict[str, Any]:
    """Snapshot every authority used by the multi-pass exact collision run."""
    input_paths = {
        "step": reject_symlink_path(step_path, "STEP input").resolve(strict=True),
        "step_report": reject_symlink_path(
            step_report_path, "STEP inspection input").resolve(strict=True),
        "component_mesh": reject_symlink_path(
            component_mesh_path, "component mesh input").resolve(strict=True),
        "interface": reject_symlink_path(
            interface_path, "board interface input").resolve(strict=True),
        "generation": reject_symlink_path(
            generation_path, "generation input").resolve(strict=True),
        "case_mesh": reject_symlink_path(
            case_mesh_path, "assembled-case input").resolve(strict=True),
        "builder": reject_symlink_path(
            Path(__file__), "collision builder").resolve(strict=True),
        "enclosure_common": reject_symlink_path(
            Path(__file__).with_name("enclosure_common.py"),
            "collision schema helper").resolve(strict=True),
        "step_inspector": reject_symlink_path(
            Path(__file__).with_name("inspect_step.py"),
            "collision STEP inspector").resolve(strict=True),
        "process_runner": reject_symlink_path(
            _runtime_tool_path(
                Path(__file__), "process_runner.py",
                PROCESS_RUNNER_SOURCE_PATH),
            "collision process runner").resolve(strict=True),
        "pipeline_runtime": reject_symlink_path(
            _runtime_tool_path(
                Path(__file__), "pipeline_runtime.py",
                PIPELINE_RUNTIME_SOURCE_PATH),
            "collision pipeline runtime").resolve(strict=True),
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
    for key in ("step_report", "component_mesh", "interface", "generation",
                "case_mesh"):
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
            snapshots["component_mesh"], snapshots["interface"],
            snapshots["generation"],
            snapshots["case_mesh"], source_snapshot, board_bottom_z,
            output, report_path, originals, bindings)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=Path)
    parser.add_argument("--step-inspection", type=Path)
    parser.add_argument("--component-mesh", type=Path)
    parser.add_argument("--interface", type=Path)
    parser.add_argument("--generation", type=Path)
    parser.add_argument("--assembled-case-mesh", type=Path)
    parser.add_argument("--board-bottom-z-mm", type=float)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--validate-receipt", type=Path)
    modes.add_argument("--replay-receipt", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if args.validate_receipt is not None:
            validate_collision_receipt(args.validate_receipt)
            print(f"ENCLOSURE COLLISION RECEIPT VALID — {args.validate_receipt}")
            return 0
        if args.replay_receipt is not None:
            replay_collision_receipt(args.replay_receipt)
            print(f"ENCLOSURE COLLISION REPLAY EXACT — {args.replay_receipt}")
            return 0
        required = {
            "--step": args.step, "--step-inspection": args.step_inspection,
            "--component-mesh": args.component_mesh,
            "--interface": args.interface,
            "--generation": args.generation,
            "--assembled-case-mesh": args.assembled_case_mesh,
            "--board-bottom-z-mm": args.board_bottom_z_mm,
            "--output": args.output, "--report": args.report,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise EnclosureError(
                "collision build is missing required arguments: " +
                ", ".join(missing))
        receipt = build(
            reject_symlink_path(args.step, "STEP input").resolve(strict=True),
            reject_symlink_path(args.step_inspection,
                                "STEP inspection input").resolve(strict=True),
            reject_symlink_path(args.component_mesh,
                                "component mesh input").resolve(strict=True),
            reject_symlink_path(args.interface,
                                "board interface input").resolve(strict=True),
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
