#!/usr/bin/env python3
"""Bind Pluto RX2 candidate-envelope, insertion, and exact-STEP evidence."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

REPO_ROOT = Path(__file__).resolve().parents[4]
COMMON = REPO_ROOT / "skills/pcb-enclosure/scripts"
sys.path.insert(0, str(COMMON))
from enclosure_common import (  # noqa: E402
    load_yaml, sha256_file, stl_metrics,
)
import inspect_step as step_inspector  # noqa: E402

KIND = "pluto-rx2-antenna-clearance-v1"
REPORT_NAME = "antenna-clearance.json"
ANTENNA_NAME = "rx2_antenna_reference.stl"
CABLE_NAME = "rx2_cable_reference.stl"
SELECTOR_SENTINEL = "PCB_ENCLOSURE_SELECTOR:"
SELECTOR_OK_SENTINEL = "PCB_ENCLOSURE_SELECTOR_OK:"
FACTS_SENTINEL = "PCB_ENCLOSURE_FACTS:"
SAFE_SELECTOR = re.compile(r"^[a-z][a-z0-9_]*$")
EMPTY_SELECTORS = (
    "antenna_vs_mount_lid",
    "antenna_vs_fasteners",
    "antenna_vs_board",
    "antenna_vs_cable",
    "cable_vs_mount_lid",
    "insertion_sweep_vs_mount",
    "interference",
)
SOLID_SELECTORS = ("rx2_antenna_reference", "rx2_cable_reference")
EVALUATED_SELECTORS = EMPTY_SELECTORS + SOLID_SELECTORS
FACT_KEYS = (
    "board_bottom_z", "case_top_z", "mount_h", "mount_roof",
    "mount_wall", "mount_half_x", "mount_center_y", "body_d",
    "lower_upright_d", "upper_upright_d", "body_axis_z",
    "body_south_y", "stalk_y", "transition_start_z",
    "transition_end_z", "stalk_top_z", "body_radial_clearance",
    "stalk_radial_clearance", "relief_x", "relief_y", "rail_gap",
    "rail_t", "cable_d", "cable_core_d", "flare_length", "flare_d",
    "insertion_sweep", "cable_tail_length", "mount_south_y",
    "mount_north_y", "service_right_x", "service_north_y",
    "north_label_y", "antenna_label_size", "outer_half_y",
)


def absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def reject_symlink_chain(path: Path, *, allow_missing_leaf: bool = False) -> None:
    """Reject symlinks in the leaf or any existing ancestor, without resolve()."""
    path = absolute(path)
    current = Path(path.anchor)
    parts = path.parts[1:] if path.anchor else path.parts
    for index, part in enumerate(parts):
        current /= part
        is_leaf = index == len(parts) - 1
        if current.is_symlink():
            raise RuntimeError(f"symlink path is forbidden: {current}")
        if not current.exists():
            if is_leaf and allow_missing_leaf:
                return
            raise RuntimeError(f"path component does not exist: {current}")


def require_input(path: Path) -> Path:
    path = absolute(path)
    reject_symlink_chain(path)
    if not path.is_file():
        raise RuntimeError(f"evidence input is not a regular file: {path}")
    return path


def binding(path: Path) -> dict[str, Any]:
    path = absolute(path)
    try:
        display = path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        display = str(path)
    return {"path": display, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def strict_json(path: Path) -> Mapping[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise RuntimeError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"invalid strict JSON evidence {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError(f"JSON evidence must be an object: {path}")
    return payload


def exact_keys(value: Any, expected: Iterable[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{label} must be an object")
    expected_set = set(expected)
    actual_set = set(value)
    if actual_set != expected_set:
        missing = sorted(expected_set - actual_set)
        extra = sorted(actual_set - expected_set)
        raise RuntimeError(
            f"{label} has wrong key census (missing={missing}, extra={extra})")
    return value


def finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RuntimeError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise RuntimeError(f"{label} must be a finite number")
    return result


def require_close(actual: Any, expected: Any, label: str,
                  tolerance: float = 1e-6) -> None:
    if abs(finite_number(actual, label) - finite_number(expected, label)) > tolerance:
        raise RuntimeError(f"{label} differs: {actual!r} != {expected!r}")


def numeric_vector(value: Any, length: int, label: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise RuntimeError(f"{label} must be a {length}-element array")
    return [finite_number(item, f"{label}[{index}]")
            for index, item in enumerate(value)]


def snapshot_inputs(inputs: Mapping[str, Path]) -> dict[str, dict[str, Any]]:
    return {
        name: {"sha256": sha256_file(path), "size": path.stat().st_size}
        for name, path in inputs.items()
    }


def require_unchanged_inputs(inputs: Mapping[str, Path],
                             snapshot: Mapping[str, Mapping[str, Any]]) -> None:
    for name, path in inputs.items():
        reject_symlink_chain(path)
        if not path.is_file():
            raise RuntimeError(f"input disappeared during run: {name}")
        current = {"sha256": sha256_file(path), "size": path.stat().st_size}
        if current != snapshot[name]:
            raise RuntimeError(f"input changed during verification: {name}")


def png_size(path: Path) -> list[int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or \
            header[12:16] != b"IHDR":
        raise RuntimeError("visual reference is not a valid PNG IHDR")
    return list(struct.unpack(">II", header[16:24]))


def local_subject(subject: Mapping[str, Any], parent: Path,
                  supplied: Path, label: str) -> None:
    relative = subject.get("path")
    if not isinstance(relative, str) or Path(relative).name != relative or \
            relative != supplied.name:
        raise RuntimeError(f"{label}.path must be one local basename")
    if subject.get("sha256") != sha256_file(supplied) or \
            subject.get("size") != supplied.stat().st_size:
        raise RuntimeError(f"{label} hash/size binding is stale")


def binary_stl_unique_vertices(path: Path) -> int:
    payload = path.read_bytes()
    if len(payload) < 84:
        raise RuntimeError("holder STL is too short for binary STL")
    triangles = struct.unpack_from("<I", payload, 80)[0]
    if len(payload) != 84 + triangles * 50:
        raise RuntimeError("holder STL is not the recorded binary STL form")
    vertices: set[tuple[float, float, float]] = set()
    for index in range(triangles):
        values = struct.unpack_from("<9f", payload, 84 + index * 50 + 12)
        vertices.add((values[0], values[1], values[2]))
        vertices.add((values[3], values[4], values[5]))
        vertices.add((values[6], values[7], values[8]))
    return len(vertices)


def private_input_snapshots(inputs: Mapping[str, Path], build_dir: Path,
                            initial: Mapping[str, Mapping[str, Any]]) -> tuple[
        tempfile.TemporaryDirectory[str], dict[str, Path],
        dict[str, dict[str, Any]]]:
    owner = tempfile.TemporaryDirectory(prefix=".antenna-inputs-", dir=build_dir)
    root = Path(owner.name)
    os.chmod(root, 0o700)
    copied: dict[str, Path] = {}
    for name, source in inputs.items():
        folder = root / name
        folder.mkdir(mode=0o700)
        destination = folder / source.name
        shutil.copyfile(source, destination, follow_symlinks=False)
        os.chmod(destination, 0o500 if name == "openscad_binary" else 0o400)
        copied[name] = destination
    copied_snapshot = snapshot_inputs(copied)
    for name in inputs:
        if initial[name] != copied_snapshot[name]:
            owner.cleanup()
            raise RuntimeError(f"private input snapshot differs for {name}")
    require_unchanged_inputs(inputs, initial)
    return owner, copied, copied_snapshot


def trusted_openscad(requested: str) -> str:
    system = Path("/usr/bin/openscad")
    require_input(system)
    candidate_name = shutil.which(requested)
    if candidate_name is None:
        raise RuntimeError(f"OpenSCAD executable was not found: {requested}")
    candidate = require_input(Path(candidate_name))
    if not os.path.samefile(candidate, system):
        raise RuntimeError(
            "custom OpenSCAD executables/wrappers are forbidden for authority")
    return str(system)


def validate_holder_measurement(path: Path, holder_stl: Path,
                                holder_png: Path) -> Mapping[str, Any]:
    doc = strict_json(path)
    exact_keys(doc, (
        "schema", "kind", "recorded_date", "status", "subjects", "mesh",
        "measured_holder_geometry", "interpretation", "method",
        "excluded_claims"), "holder measurement")
    if doc["schema"] != 1 or \
            doc["kind"] != "pluto-rx2-user-antenna-holder-measurement-v1" or \
            doc["status"] != "DERIVED_GEOMETRY_EVIDENCE":
        raise RuntimeError("holder measurement has wrong schema/kind/status")
    if not isinstance(doc["recorded_date"], str):
        raise RuntimeError("holder measurement recorded_date must be a string")

    subjects = exact_keys(doc["subjects"], ("holder_stl", "visual_reference"),
                          "holder measurement.subjects")
    holder = exact_keys(subjects["holder_stl"], (
        "path", "original_attachment_name", "sha256", "size", "format",
        "units", "units_authority"), "holder measurement.subjects.holder_stl")
    visual = exact_keys(subjects["visual_reference"], (
        "path", "original_attachment_name", "sha256", "size", "pixel_size",
        "relationship"), "holder measurement.subjects.visual_reference")
    local_subject(holder, path.parent, holder_stl, "holder_stl")
    local_subject(visual, path.parent, holder_png, "visual_reference")
    if holder["format"] != "binary-stl" or holder["units"] != "mm":
        raise RuntimeError("holder measurement STL format/units changed")
    if numeric_vector(visual["pixel_size"], 2, "visual pixel_size") != \
            [float(item) for item in png_size(holder_png)]:
        raise RuntimeError("visual reference PNG dimensions differ from receipt")

    mesh = exact_keys(doc["mesh"], (
        "triangles", "unique_vertices", "components", "watertight",
        "edge_manifold", "orientation_consistent", "degenerate_facets",
        "signed_volume_mm3", "bbox_mm"), "holder measurement.mesh")
    bbox = exact_keys(mesh["bbox_mm"], ("min", "max", "size"),
                      "holder measurement.mesh.bbox_mm")
    holder_metrics = stl_metrics(holder_stl)
    for key in ("triangles", "components", "degenerate_facets"):
        if mesh[key] != holder_metrics[key]:
            raise RuntimeError(f"holder STL recomputed {key} differs")
    if isinstance(mesh["unique_vertices"], bool) or \
            not isinstance(mesh["unique_vertices"], int) or \
            mesh["unique_vertices"] <= 0 or \
            mesh["unique_vertices"] != binary_stl_unique_vertices(holder_stl):
        raise RuntimeError("holder STL recomputed unique-vertex census differs")
    if mesh["edge_manifold"] is not holder_metrics["edge_manifold"] or \
            mesh["orientation_consistent"] is not \
            holder_metrics["orientation_consistent"]:
        raise RuntimeError("holder STL recomputed topology differs")
    watertight = (holder_metrics["boundary_edges"] == 0 and
                  holder_metrics["nonmanifold_edges"] == 0)
    if mesh["watertight"] is not watertight:
        raise RuntimeError("holder STL recomputed watertight status differs")
    require_close(mesh["signed_volume_mm3"], holder_metrics["signed_volume_mm3"],
                  "holder STL signed volume", 1e-5)
    for key in ("min", "max", "size"):
        recorded = numeric_vector(bbox[key], 3, f"holder bbox {key}")
        actual = numeric_vector(holder_metrics["bbox_mm"][key], 3,
                                f"actual holder bbox {key}")
        for index in range(3):
            require_close(recorded[index], actual[index],
                          f"holder bbox {key}[{index}]", 1e-5)

    measured = exact_keys(doc["measured_holder_geometry"], (
        "station_centers_xy_mm", "station_pitch_mm", "main_arm_width_mm",
        "horizontal_open_tunnel", "vertical_grip", "outer_clip",
        "fastener_holes"), "holder measurement.measured_holder_geometry")
    if not isinstance(measured["station_centers_xy_mm"], list) or \
            len(measured["station_centers_xy_mm"]) != 5:
        raise RuntimeError("holder station center census must contain five rows")
    for index, row in enumerate(measured["station_centers_xy_mm"]):
        numeric_vector(row, 2, f"holder station center {index}")
    if finite_number(measured["station_pitch_mm"], "holder station pitch") <= 0 or \
            finite_number(measured["main_arm_width_mm"], "holder arm width") <= 0:
        raise RuntimeError("holder station pitch/arm width must be positive")
    tunnel = exact_keys(measured["horizontal_open_tunnel"], (
        "diameter_mm", "radius_mm", "centerline_z_mm", "roof_z_mm",
        "entry_blend_radius_mm", "entry_width_at_z0_mm", "section",
        "disposition", "station_orientation"), "holder horizontal tunnel")
    for key in ("diameter_mm", "radius_mm", "centerline_z_mm", "roof_z_mm",
                "entry_blend_radius_mm", "entry_width_at_z0_mm"):
        if finite_number(tunnel[key], f"holder tunnel {key}") <= 0:
            raise RuntimeError(f"holder tunnel {key} must be positive")
    require_close(tunnel["radius_mm"], tunnel["diameter_mm"] / 2,
                  "holder tunnel radius")
    require_close(tunnel["roof_z_mm"],
                  tunnel["centerline_z_mm"] + tunnel["radius_mm"],
                  "holder tunnel roof")
    require_close(tunnel["entry_width_at_z0_mm"],
                  tunnel["diameter_mm"]
                  + 2 * tunnel["entry_blend_radius_mm"],
                  "holder tunnel entry width")
    for key in ("section", "disposition", "station_orientation"):
        if not isinstance(tunnel[key], str) or not tunnel[key].strip():
            raise RuntimeError(f"holder tunnel {key} must be a nonempty string")
    vertical = exact_keys(measured["vertical_grip"], (
        "lower_bore_diameter_mm", "lower_bore_top_z_mm", "capture_taper",
        "top_throat_diameter_mm", "top_throat_start_z_mm", "top_z_mm"),
        "holder vertical grip")
    taper = exact_keys(vertical["capture_taper"], (
        "start_z_mm", "end_z_mm", "start_diameter_mm", "end_diameter_mm"),
        "holder capture taper")
    for key in ("lower_bore_diameter_mm", "lower_bore_top_z_mm",
                "top_throat_diameter_mm", "top_throat_start_z_mm", "top_z_mm"):
        if finite_number(vertical[key], f"holder vertical {key}") <= 0:
            raise RuntimeError(f"holder vertical {key} must be positive")
    for key in ("start_z_mm", "end_z_mm", "start_diameter_mm",
                "end_diameter_mm"):
        if finite_number(taper[key], f"holder taper {key}") <= 0:
            raise RuntimeError(f"holder taper {key} must be positive")
    require_close(taper["start_z_mm"], vertical["lower_bore_top_z_mm"],
                  "holder taper/lower grip transition")
    require_close(taper["end_z_mm"], vertical["top_throat_start_z_mm"],
                  "holder taper/top throat transition")
    require_close(taper["start_diameter_mm"], vertical["lower_bore_diameter_mm"],
                  "holder taper start diameter")
    require_close(taper["end_diameter_mm"], vertical["top_throat_diameter_mm"],
                  "holder taper end diameter")
    outer = exact_keys(measured["outer_clip"], (
        "base_plate_top_z_mm", "base_blend_radius_mm", "straight_diameter_mm",
        "straight_start_z_mm", "straight_end_z_mm", "crown_blend_radius_mm",
        "flat_top_diameter_mm", "flat_top_z_mm"), "holder outer clip")
    for key, value in outer.items():
        if finite_number(value, f"holder outer clip {key}") <= 0:
            raise RuntimeError(f"holder outer clip {key} must be positive")
    holes = exact_keys(measured["fastener_holes"],
                       ("diameter_mm", "centers_xy_mm"), "holder fasteners")
    if not isinstance(holes["centers_xy_mm"], list) or \
            len(holes["centers_xy_mm"]) != 4:
        raise RuntimeError("holder fastener census must contain four rows")
    if finite_number(holes["diameter_mm"], "holder fastener diameter") <= 0:
        raise RuntimeError("holder fastener diameter must be positive")
    for index, row in enumerate(holes["centers_xy_mm"]):
        numeric_vector(row, 2, f"holder fastener center {index}")

    interpretation = exact_keys(doc["interpretation"], (
        "classification", "not_an_antenna_solid", "candidate_antenna_envelope",
        "reference_holder_nested_fit", "feature_frame_comparison",
        "production_rigid_mount", "prewired_cable_loading_path"),
        "holder measurement.interpretation")
    candidate = exact_keys(interpretation["candidate_antenna_envelope"], (
        "authority", "horizontal_lower_body_diameter_mm",
        "perpendicular_lower_upright_diameter_mm", "upright_transition",
        "upper_upright_diameter_mm"), "candidate antenna envelope")
    transition = exact_keys(candidate["upright_transition"], (
        "start_z_mm", "end_z_mm", "start_diameter_mm", "end_diameter_mm"),
        "candidate upright transition")
    nested = exact_keys(interpretation["reference_holder_nested_fit"], (
        "kind", "d10_vs_lower_grip_radial_interference_mm",
        "d10_vs_retention_lip_radial_interference_mm",
        "d8_75_upper_vs_d8_75_throat_nominal_radial_delta_mm", "result",
        "note"), "reference holder nested fit")
    frame = exact_keys(interpretation["feature_frame_comparison"], (
        "source_station_center_xyz_mm", "source_to_mount_local_translate_mm",
        "source_to_mount_local_rotation_deg", "mapped_station_center_xyz_mm",
        "source_channel_exit_y_mm", "mapped_channel_exit_y_mm",
        "mount_hood_south_edge_y_mm", "result", "authority"),
        "feature frame comparison")
    production = exact_keys(interpretation["production_rigid_mount"], (
        "candidate_lower_diameter_mm", "minimum_radial_clearance_mm",
        "modeled_lower_cavity_diameter_mm", "rectangular_underside_relief_mm",
        "rectangular_underside_relief_extents_xy_mm",
        "upright_through_aperture_diameter_mm",
        "upright_aperture_north_extent_mm",
        "roof_hung_locator_rail_thickness_mm", "roof_hung_locator_gap_mm",
        "closed_lid_body_floor_clearance_mm", "result"),
        "production rigid mount")
    cable = exact_keys(interpretation["prewired_cable_loading_path"], (
        "loading_method", "threading_required", "cable_exit_direction",
        "candidate_cable_diameter_mm", "open_bottom_u_channel",
        "pcb_lid_below_mount", "insertion_sweep_mm", "authority"),
        "prewired cable loading path")
    channel = exact_keys(cable["open_bottom_u_channel"], (
        "core_width_mm", "centerline_z_above_lid_mm",
        "core_crown_z_above_lid_mm", "outer_entry_flare_length_mm",
        "outer_entry_flare_width_mm", "roof_ligament_at_flare_mm"),
        "pre-wired assembly U-arch")
    if interpretation["not_an_antenna_solid"] is not True or \
            not isinstance(interpretation["classification"], str):
        raise RuntimeError("holder classification must remain not-an-antenna")
    if candidate["authority"] != \
            "conservative derived envelope; not a measured antenna or vendor drawing":
        raise RuntimeError("candidate antenna authority statement changed")
    for key in ("horizontal_lower_body_diameter_mm",
                "perpendicular_lower_upright_diameter_mm",
                "upper_upright_diameter_mm"):
        if finite_number(candidate[key], f"candidate envelope {key}") <= 0:
            raise RuntimeError(f"candidate envelope {key} must be positive")
    for key in ("start_z_mm", "end_z_mm", "start_diameter_mm",
                "end_diameter_mm"):
        if finite_number(transition[key], f"candidate transition {key}") <= 0:
            raise RuntimeError(f"candidate transition {key} must be positive")
    require_close(transition["start_diameter_mm"],
                  candidate["perpendicular_lower_upright_diameter_mm"],
                  "candidate transition start diameter")
    require_close(transition["end_diameter_mm"],
                  candidate["upper_upright_diameter_mm"],
                  "candidate transition end diameter")
    if nested["kind"] != "intentional-flex-interference-not-disjoint-collision" or \
            nested["result"] != "PASS_EXPECTED_COMPLIANT_RETENTION":
        raise RuntimeError("nested holder-fit semantics changed")
    if not isinstance(nested["note"], str) or not nested["note"].strip():
        raise RuntimeError("nested holder-fit note must be a nonempty string")
    for key in ("d10_vs_lower_grip_radial_interference_mm",
                "d10_vs_retention_lip_radial_interference_mm",
                "d8_75_upper_vs_d8_75_throat_nominal_radial_delta_mm"):
        finite_number(nested[key], f"nested holder fit {key}")
    for key in ("source_station_center_xyz_mm",
                "source_to_mount_local_translate_mm",
                "source_to_mount_local_rotation_deg",
                "mapped_station_center_xyz_mm"):
        numeric_vector(frame[key], 3, f"feature frame {key}")
    for key in ("source_channel_exit_y_mm", "mapped_channel_exit_y_mm",
                "mount_hood_south_edge_y_mm"):
        finite_number(frame[key], f"feature frame {key}")
    if frame["result"] != "FEATURE_FRAMES_AGREE_WITHIN_0.25_MM":
        raise RuntimeError("feature-frame result changed")
    if not isinstance(frame["authority"], str) or not frame["authority"].strip():
        raise RuntimeError("feature-frame authority must be a nonempty string")
    for key in ("candidate_lower_diameter_mm", "minimum_radial_clearance_mm",
                "modeled_lower_cavity_diameter_mm",
                "upright_through_aperture_diameter_mm",
                "upright_aperture_north_extent_mm",
                "roof_hung_locator_rail_thickness_mm",
                "roof_hung_locator_gap_mm",
                "closed_lid_body_floor_clearance_mm"):
        if finite_number(production[key], f"production mount {key}") <= 0:
            raise RuntimeError(f"production mount {key} must be positive")
    numeric_vector(production["rectangular_underside_relief_mm"], 2,
                   "production relief size")
    relief_extents = production["rectangular_underside_relief_extents_xy_mm"]
    if not isinstance(relief_extents, list) or len(relief_extents) != 2:
        raise RuntimeError("production relief extents must contain X/Y rows")
    for index, row in enumerate(relief_extents):
        numeric_vector(row, 2, f"production relief extents {index}")
    if production["result"] != "PASS_CANDIDATE_CLEARANCE_NO_FLEX_REQUIRED":
        raise RuntimeError("production rigid-mount result changed")
    if cable["threading_required"] is not False:
        raise RuntimeError("prewired cable path must not require threading")
    expected_cable_text = {
        "loading_method": (
            "complete L-shaped antenna and already-attached cable translate "
            "vertically through one rectangular underside opening as the "
            "adapter is lowered"),
        "cable_exit_direction": (
            "south / negative Y, horizontal on the exterior/top side of the "
            "PCB enclosure"),
        "pcb_lid_below_mount": (
            "closed except for the two insert/screw fastener stacks; no "
            "antenna-cable pass-through"),
    }
    for key, expected_text in expected_cable_text.items():
        if cable[key] != expected_text:
            raise RuntimeError(f"prewired cable {key} topology changed")
    if not isinstance(cable["authority"], str) or not cable["authority"].strip():
        raise RuntimeError("prewired cable authority must be a nonempty string")
    for key in ("candidate_cable_diameter_mm", "insertion_sweep_mm"):
        if finite_number(cable[key], f"prewired cable {key}") <= 0:
            raise RuntimeError(f"prewired cable {key} must be positive")
    for key in ("core_width_mm", "centerline_z_above_lid_mm",
                "core_crown_z_above_lid_mm", "outer_entry_flare_length_mm",
                "outer_entry_flare_width_mm", "roof_ligament_at_flare_mm"):
        if finite_number(channel[key], f"prewired U-channel {key}") <= 0:
            raise RuntimeError(f"prewired U-channel {key} must be positive")
    method = exact_keys(doc["method"],
                        ("topology", "dimensions", "nested_fit_rule"),
                        "holder measurement.method")
    for key, value in method.items():
        if not isinstance(value, str) or not value.strip():
            raise RuntimeError(f"holder measurement method {key} must be text")
    if not isinstance(doc["excluded_claims"], list) or not all(
            isinstance(item, str) for item in doc["excluded_claims"]):
        raise RuntimeError("holder measurement excluded_claims must be strings")
    return doc


def validate_candidate_contract(path: Path, measurement_path: Path) -> tuple[
        Mapping[str, Any], dict[str, float], Mapping[str, Any]]:
    doc = strict_json(path)
    exact_keys(doc, (
        "schema", "kind", "status", "status_reason", "authority", "subjects",
        "facts", "reference_meshes", "derived_assertions", "excluded_claims"),
        "candidate contract")
    if doc["schema"] != 1 or \
            doc["kind"] != "pluto-rx2-antenna-adapter-candidate-contract-v1" or \
            doc["status"] != "INCOMPLETE":
        raise RuntimeError("candidate contract has wrong schema/kind/status")
    subjects = exact_keys(doc["subjects"], ("holder_measurement",),
                          "candidate contract.subjects")
    subject = exact_keys(subjects["holder_measurement"],
                         ("path", "sha256", "size"),
                         "candidate contract holder measurement")
    local_subject(subject, path.parent, measurement_path, "holder_measurement")
    facts_doc = exact_keys(doc["facts"], FACT_KEYS, "candidate contract.facts")
    facts = {key: finite_number(facts_doc[key], f"contract fact {key}")
             for key in FACT_KEYS}
    meshes = exact_keys(doc["reference_meshes"], ("antenna", "cable"),
                        "candidate contract.reference_meshes")
    for name, expected_selector in (
            ("antenna", "rx2_antenna_reference"),
            ("cable", "rx2_cable_reference")):
        spec = exact_keys(meshes[name], (
            "selector", "bbox_min_mm", "bbox_max_mm", "absolute_volume_mm3",
            "bbox_tolerance_mm", "volume_tolerance_mm3"),
            f"candidate contract.reference_meshes.{name}")
        if spec["selector"] != expected_selector:
            raise RuntimeError(f"candidate contract {name} selector changed")
        numeric_vector(spec["bbox_min_mm"], 3, f"{name} bbox_min_mm")
        numeric_vector(spec["bbox_max_mm"], 3, f"{name} bbox_max_mm")
        for key in ("absolute_volume_mm3", "bbox_tolerance_mm",
                    "volume_tolerance_mm3"):
            if finite_number(spec[key], f"{name} {key}") <= 0:
                raise RuntimeError(f"candidate contract {name} {key} must be positive")
    for key in ("derived_assertions", "excluded_claims"):
        if not isinstance(doc[key], list) or not all(
                isinstance(item, str) for item in doc[key]):
            raise RuntimeError(f"candidate contract {key} must be strings")
    return doc, facts, meshes


def validate_selector_name(name: str) -> None:
    if not SAFE_SELECTOR.fullmatch(name):
        raise RuntimeError(f"unsafe selector token: {name!r}")
    if name not in EVALUATED_SELECTORS:
        raise RuntimeError(f"selector is absent from the evaluated census: {name}")


def validate_selector_census(names: Iterable[str]) -> tuple[str, ...]:
    rows = tuple(names)
    if len(rows) != len(set(rows)):
        raise RuntimeError("duplicate selector in evaluated census")
    for name in rows:
        if not SAFE_SELECTOR.fullmatch(name):
            raise RuntimeError(f"unsafe selector token: {name!r}")
    return rows


def run_openscad(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, check=False, timeout=120)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("OpenSCAD selector timed out after 120 seconds") from exc


def anchored_echoes(output: str, prefix: str) -> list[str]:
    pattern = re.compile(r'^ECHO: "' + re.escape(prefix) + r'([^"\r\n]*)"$', re.M)
    return pattern.findall(output)


def parse_facts(output: str, selector_name: str) -> dict[str, float]:
    rows = anchored_echoes(output, FACTS_SENTINEL)
    if len(rows) != 1:
        raise RuntimeError(
            f"selector {selector_name} emitted {len(rows)} machine-fact rows")
    result: dict[str, float] = {}
    for field in rows[0].split(";"):
        if field.count("=") != 1:
            raise RuntimeError(f"malformed SCAD fact for {selector_name}: {field!r}")
        key, raw = field.split("=", 1)
        if key in result:
            raise RuntimeError(f"duplicate SCAD fact for {selector_name}: {key}")
        try:
            value = float(raw)
        except ValueError as exc:
            raise RuntimeError(
                f"non-numeric SCAD fact for {selector_name}: {field!r}") from exc
        if not math.isfinite(value):
            raise RuntimeError(f"non-finite SCAD fact for {selector_name}: {key}")
        result[key] = value
    exact_keys(result, FACT_KEYS, f"SCAD facts for {selector_name}")
    return result


def require_clean_diagnostics(output: str, selector_name: str) -> dict[str, float]:
    if "ERROR:" in output or "WARNING:" in output:
        raise RuntimeError(
            f"selector {selector_name} emitted ERROR/WARNING diagnostics:\n"
            + output[-2000:])
    selector_rows = anchored_echoes(output, SELECTOR_SENTINEL)
    ok_rows = anchored_echoes(output, SELECTOR_OK_SENTINEL)
    if selector_rows != [selector_name] or ok_rows != [selector_name]:
        raise RuntimeError(
            f"selector {selector_name} did not emit exactly one matching "
            "selector and selector-OK sentinel")
    return parse_facts(output, selector_name)


def selector(openscad: str, scad: Path, name: str,
             expect_empty: bool, directory: Path) -> tuple[
                 dict[str, Any], dict[str, float]]:
    validate_selector_name(name)
    target = directory / f"{name}.stl"
    command = [openscad, "--hardwarnings", "-o", str(target), "-D",
               f'part="{name}"', str(scad)]
    result = run_openscad(command)
    facts = require_clean_diagnostics(result.stdout, name)
    generated = target.is_file() and target.stat().st_size > 0
    empty_diagnostic = "Current top level object is empty" in result.stdout
    if expect_empty:
        passed = result.returncode in {0, 1} and not generated and empty_diagnostic
    else:
        passed = result.returncode == 0 and generated and not empty_diagnostic
    if not passed:
        raise RuntimeError(
            f"selector {name} did not produce expected "
            f"{'EMPTY' if expect_empty else 'SOLID'} result (rc="
            f"{result.returncode}):\n" + result.stdout[-2000:])
    return {
        "selector": name,
        "expectation": "EMPTY" if expect_empty else "SOLID",
        "result": "EMPTY" if expect_empty else "SOLID",
        "returncode": result.returncode,
        "hardwarnings": True,
        "evaluation_sentinel": f"{SELECTOR_SENTINEL}{name}",
        "success_sentinel": f"{SELECTOR_OK_SENTINEL}{name}",
    }, facts


def unknown_selector_probe(openscad: str, scad: Path,
                           directory: Path) -> dict[str, Any]:
    name = "totally_missing_selector"
    target = directory / f"{name}.stl"
    result = run_openscad([
        openscad, "--hardwarnings", "-o", str(target), "-D",
        f'part="{name}"', str(scad),
    ])
    generated = target.is_file() and target.stat().st_size > 0
    selector_rows = anchored_echoes(result.stdout, SELECTOR_SENTINEL)
    ok_rows = anchored_echoes(result.stdout, SELECTOR_OK_SENTINEL)
    expected_reason = f"Unknown enclosure part selector: {name}"
    if result.returncode == 0 or generated or "ERROR:" not in result.stdout or \
            expected_reason not in result.stdout or selector_rows != [name] or ok_rows:
        raise RuntimeError("unknown-selector known-bad probe was not rejected")
    return {"probe": "unknown_selector", "result": "REJECTED",
            "returncode": result.returncode, "generated_mesh": generated}


def known_bad_probes(openscad: str, scad: Path,
                     directory: Path) -> list[dict[str, Any]]:
    rows = [unknown_selector_probe(openscad, scad, directory)]
    try:
        validate_selector_name('bad";cube(1)')
    except RuntimeError:
        rows.append({"probe": "unsafe_selector_token", "result": "REJECTED"})
    else:
        raise RuntimeError("unsafe-selector known-bad probe was accepted")
    try:
        validate_selector_census((*EVALUATED_SELECTORS, EVALUATED_SELECTORS[0]))
    except RuntimeError:
        rows.append({"probe": "duplicate_selector_census", "result": "REJECTED"})
    else:
        raise RuntimeError("duplicate-selector known-bad probe was accepted")
    with tempfile.TemporaryDirectory(prefix="pluto-rx2-symlink-probe-") as tmp:
        root = Path(tmp)
        target = root / "target"
        target.write_text("sentinel", encoding="utf-8")
        link = root / "link"
        os.symlink(target, link)
        try:
            reject_symlink_chain(link)
        except RuntimeError:
            rows.append({"probe": "symlink_output_path", "result": "REJECTED"})
        else:
            raise RuntimeError("symlink-path known-bad probe was accepted")
    return rows


def atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    reject_symlink_chain(path, allow_missing_leaf=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink():
            raise RuntimeError(f"report destination became a symlink: {path}")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def atomic_install(source: Path, destination: Path) -> None:
    reject_symlink_chain(destination, allow_missing_leaf=True)
    if destination.is_symlink():
        raise RuntimeError(f"mesh destination became a symlink: {destination}")
    os.replace(source, destination)


def brep_from_stl(path: Path, cq: Any) -> Any:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
    from OCP.StlAPI import StlAPI_Reader
    from OCP.TopoDS import TopoDS, TopoDS_Shape

    raw = TopoDS_Shape()
    if not StlAPI_Reader().Read(raw, str(path)):
        raise RuntimeError(f"OCP could not read selector STL: {path}")
    sewing = BRepBuilderAPI_Sewing(1e-6, True, True, True, False)
    sewing.Add(raw)
    sewing.Perform()
    sewed = cq.Shape.cast(sewing.SewedShape())
    shells = sewed.Shells()
    if not shells:
        raise RuntimeError(f"selector STL produced no sewable shell: {path}")
    solids = []
    for index, shell in enumerate(shells):
        if not shell.Closed() or not shell.isValid():
            raise RuntimeError(f"selector STL shell {index} is open or invalid")
        maker = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(shell.wrapped))
        solid = cq.Shape.cast(maker.Solid())
        if not maker.IsDone() or not solid.isValid() or solid.Volume() <= 0:
            raise RuntimeError(f"selector STL shell {index} did not form a solid")
        solids.append(solid)
    return solids[0] if len(solids) == 1 else cq.Compound.makeCompound(solids)


def exact_volume(shape: Any) -> float:
    return sum(abs(solid.Volume()) for solid in shape.Solids())


def validate_mesh_against_contract(name: str, metrics: Mapping[str, Any],
                                   spec: Mapping[str, Any]) -> None:
    if not metrics["edge_manifold"] or \
            not metrics["orientation_consistent"] or \
            metrics["components"] != 1 or metrics["boundary_edges"] != 0 or \
            metrics["nonmanifold_edges"] != 0:
        raise RuntimeError(f"{name} is not one closed oriented manifold mesh")
    bbox_tolerance = finite_number(spec["bbox_tolerance_mm"],
                                   f"{name} bbox tolerance")
    for key, spec_key in (("min", "bbox_min_mm"), ("max", "bbox_max_mm")):
        actual = numeric_vector(metrics["bbox_mm"][key], 3, f"{name} bbox {key}")
        expected = numeric_vector(spec[spec_key], 3, f"{name} expected bbox {key}")
        for index in range(3):
            require_close(actual[index], expected[index],
                          f"{name} bbox {key}[{index}]", bbox_tolerance)
    require_close(metrics["absolute_volume_mm3"], spec["absolute_volume_mm3"],
                  f"{name} absolute volume",
                  finite_number(spec["volume_tolerance_mm3"],
                                f"{name} volume tolerance"))


def mesh_known_bad_probes(name: str, metrics: Mapping[str, Any],
                          spec: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    translated = json.loads(json.dumps(metrics))
    for key in ("min", "max"):
        translated["bbox_mm"][key][2] += 1000.0
    try:
        validate_mesh_against_contract(name, translated, spec)
    except RuntimeError:
        rows.append({"probe": f"{name}_translated_1000mm",
                     "result": "REJECTED"})
    else:
        raise RuntimeError(f"translated {name} known-bad probe was accepted")
    substituted = json.loads(json.dumps(metrics))
    substituted["absolute_volume_mm3"] *= 0.5
    try:
        validate_mesh_against_contract(name, substituted, spec)
    except RuntimeError:
        rows.append({"probe": f"{name}_substituted_volume",
                     "result": "REJECTED"})
    else:
        raise RuntimeError(f"substituted {name} known-bad probe was accepted")
    return rows


def validate_facts(actual: Mapping[str, float], expected: Mapping[str, float],
                   config: Mapping[str, Any],
                   measurement: Mapping[str, Any]) -> None:
    exact_keys(actual, FACT_KEYS, "SCAD machine facts")
    exact_keys(expected, FACT_KEYS, "candidate-contract facts")
    for key in FACT_KEYS:
        require_close(actual[key], expected[key], f"SCAD fact {key}")

    geometry = exact_keys(config.get("geometry"), (
        "topology", "xy_clearance_mm", "wall_mm", "floor_mm", "roof_mm",
        "corner_radius_mm", "board_bottom_z_mm", "inside_top_z_mm", "seam_z_mm",
        "panel_thickness_mm", "panel_capture_mm", "panel_clearance_mm",
        "corner_post_mm", "lid_column_board_gap_mm"), "enclosure geometry")
    require_close(actual["board_bottom_z"], geometry["board_bottom_z_mm"],
                  "board bottom config/fact")
    require_close(actual["case_top_z"],
                  finite_number(geometry["inside_top_z_mm"], "inside top")
                  + finite_number(geometry["roof_mm"], "roof"),
                  "case top config/fact")

    interpretation = measurement["interpretation"]
    candidate = interpretation["candidate_antenna_envelope"]
    transition = candidate["upright_transition"]
    production = interpretation["production_rigid_mount"]
    cable = interpretation["prewired_cable_loading_path"]
    channel = cable["open_bottom_u_channel"]
    measured = measurement["measured_holder_geometry"]
    tunnel = measured["horizontal_open_tunnel"]
    vertical_grip = measured["vertical_grip"]
    nested = interpretation["reference_holder_nested_fit"]
    frame = interpretation["feature_frame_comparison"]
    comparisons = {
        "body_d": candidate["horizontal_lower_body_diameter_mm"],
        "lower_upright_d": candidate["perpendicular_lower_upright_diameter_mm"],
        "upper_upright_d": candidate["upper_upright_diameter_mm"],
        "transition_start_z": transition["start_z_mm"],
        "transition_end_z": transition["end_z_mm"],
        "body_radial_clearance": production["minimum_radial_clearance_mm"],
        "relief_x": production["rectangular_underside_relief_mm"][0],
        "relief_y": production["rectangular_underside_relief_mm"][1],
        "rail_gap": production["roof_hung_locator_gap_mm"],
        "rail_t": production["roof_hung_locator_rail_thickness_mm"],
        "cable_d": cable["candidate_cable_diameter_mm"],
        "cable_core_d": channel["core_width_mm"],
        "flare_length": channel["outer_entry_flare_length_mm"],
        "flare_d": channel["outer_entry_flare_width_mm"],
        "insertion_sweep": cable["insertion_sweep_mm"],
    }
    for key, value in comparisons.items():
        require_close(actual[key], value, f"measurement/fact {key}")
    require_close(transition["start_diameter_mm"], actual["lower_upright_d"],
                  "candidate transition/fact start diameter")
    require_close(transition["end_diameter_mm"], actual["upper_upright_d"],
                  "candidate transition/fact end diameter")
    require_close(production["candidate_lower_diameter_mm"], actual["body_d"],
                  "production candidate lower diameter")
    cavity_d = actual["lower_upright_d"] \
        + 2 * actual["stalk_radial_clearance"]
    require_close(production["modeled_lower_cavity_diameter_mm"], cavity_d,
                  "production lower cavity derivation")
    require_close(production["upright_through_aperture_diameter_mm"], cavity_d,
                  "production upright aperture derivation")
    expected_relief_extents = [
        [-actual["relief_x"] / 2, actual["relief_x"] / 2],
        [actual["mount_center_y"] - actual["relief_y"] / 2,
         actual["mount_center_y"] + actual["relief_y"] / 2],
    ]
    recorded_extents = production["rectangular_underside_relief_extents_xy_mm"]
    for axis in range(2):
        for endpoint in range(2):
            require_close(recorded_extents[axis][endpoint],
                          expected_relief_extents[axis][endpoint],
                          f"production relief extent {axis}/{endpoint}")
    require_close(production["upright_aperture_north_extent_mm"],
                  actual["stalk_y"] + cavity_d / 2,
                  "production upright north extent")
    require_close(production["closed_lid_body_floor_clearance_mm"],
                  actual["body_axis_z"] - actual["body_d"] / 2,
                  "production body floor clearance")
    require_close(channel["centerline_z_above_lid_mm"], actual["body_axis_z"],
                  "U-channel centerline/fact")
    require_close(channel["core_crown_z_above_lid_mm"],
                  actual["body_axis_z"] + actual["cable_core_d"] / 2,
                  "U-channel core crown derivation")
    require_close(channel["roof_ligament_at_flare_mm"],
                  actual["mount_h"]
                  - (actual["body_axis_z"] + actual["flare_d"] / 2),
                  "U-channel roof ligament derivation")
    require_close(nested["d10_vs_lower_grip_radial_interference_mm"],
                  (actual["body_d"] - tunnel["diameter_mm"]) / 2,
                  "nested lower-grip interference")
    require_close(nested["d10_vs_retention_lip_radial_interference_mm"],
                  (actual["body_d"]
                   - vertical_grip["top_throat_diameter_mm"]) / 2,
                  "nested retention-lip interference")
    require_close(
        nested["d8_75_upper_vs_d8_75_throat_nominal_radial_delta_mm"],
        (actual["upper_upright_d"]
         - vertical_grip["top_throat_diameter_mm"]) / 2,
        "nested upper-throat delta")
    source = numeric_vector(frame["source_station_center_xyz_mm"], 3,
                            "feature-frame source")
    translate = numeric_vector(frame["source_to_mount_local_translate_mm"], 3,
                               "feature-frame translate")
    mapped = numeric_vector(frame["mapped_station_center_xyz_mm"], 3,
                            "feature-frame mapped")
    for index in range(3):
        require_close(source[index] + translate[index], mapped[index],
                      f"feature-frame mapping axis {index}")
    require_close(mapped[1], actual["stalk_y"], "feature-frame stalk Y")
    require_close(mapped[2], actual["body_axis_z"], "feature-frame body Z")
    require_close(frame["mapped_channel_exit_y_mm"],
                  frame["source_channel_exit_y_mm"] + translate[1],
                  "feature-frame channel exit mapping")
    require_close(frame["mount_hood_south_edge_y_mm"], actual["mount_south_y"],
                  "feature-frame mount south edge")

    # Machine-derive internal relationships that a matching echo alone could
    # otherwise misstate.
    require_close(actual["body_axis_z"], actual["body_d"] / 2 + 0.2,
                  "body axis from body diameter/floor gap")
    require_close(actual["rail_gap"],
                  actual["body_d"] + 2 * actual["body_radial_clearance"],
                  "locator rail gap derivation")
    require_close(actual["cable_core_d"],
                  actual["body_d"] + 2 * actual["body_radial_clearance"],
                  "full-antenna arch derivation")
    require_close(actual["flare_d"], actual["cable_core_d"],
                  "full-antenna arch entry derivation")
    require_close(actual["mount_south_y"],
                  actual["mount_center_y"]
                  - (actual["mount_north_y"] - actual["mount_south_y"]) / 2,
                  "mount south/center derivation")


def validate_step_inspection(inspection: Mapping[str, Any], step: Path,
                             interface_path: Path,
                             config: Mapping[str, Any]) -> tuple[
                                 Mapping[str, Any], list[int], list[float]]:
    exact_keys(inspection, (
        "schema", "kind", "status", "step", "interface",
        "occurrence_coverage", "geometry"), "STEP inspection")
    if inspection.get("schema") != 1 or \
            inspection.get("kind") != "pcb-enclosure-step-inspection-v1" or \
            inspection.get("status") != "COMPLETE":
        raise RuntimeError("STEP inspection has wrong schema/kind/status")
    geometry = inspection.get("geometry")
    if not isinstance(geometry, Mapping) or geometry.get("status") != "COMPLETE":
        raise RuntimeError("exact STEP geometry inspection must be COMPLETE")
    step_binding = inspection.get("step")
    if not isinstance(step_binding, Mapping) or \
            step_binding.get("sha256") != sha256_file(step) or \
            step_binding.get("size") != step.stat().st_size:
        raise RuntimeError("STEP differs from inspection subject")
    interface_binding = inspection.get("interface")
    if not isinstance(interface_binding, Mapping) or \
            interface_binding.get("sha256") != sha256_file(interface_path) or \
            interface_binding.get("size") != interface_path.stat().st_size:
        raise RuntimeError("interface differs from STEP inspection subject")
    configured_step = config.get("subject", {}).get("step", {})
    if configured_step.get("sha256") != sha256_file(step) or \
            configured_step.get("size") != step.stat().st_size:
        raise RuntimeError("STEP differs from enclosure subject binding")
    configured_interface = config.get("subject", {}).get("interface", {})
    if configured_interface.get("sha256") != sha256_file(interface_path) or \
            configured_interface.get("size") != interface_path.stat().st_size:
        raise RuntimeError("interface differs from enclosure subject binding")
    coverage = exact_keys(inspection.get("occurrence_coverage"), (
        "status", "zero_modeled_denominator", "expected_modeled_refs",
        "observed_designators", "covered_modeled_refs", "missing_modeled_refs",
        "unmodeled_access_refs"), "STEP occurrence coverage")
    for key in ("expected_modeled_refs", "observed_designators",
                "covered_modeled_refs"):
        if isinstance(coverage[key], bool) or not isinstance(coverage[key], int) or \
                coverage[key] < 0:
            raise RuntimeError(f"STEP occurrence {key} is invalid")
    if not isinstance(coverage["missing_modeled_refs"], list) or \
            not isinstance(coverage["unmodeled_access_refs"], list):
        raise RuntimeError("STEP occurrence exception lists are invalid")
    if coverage["status"] != "COMPLETE" or \
            coverage["zero_modeled_denominator"] is not False or \
            coverage["expected_modeled_refs"] <= 0 or \
            coverage["covered_modeled_refs"] != coverage["expected_modeled_refs"] or \
            coverage["missing_modeled_refs"] != [] or \
            coverage["unmodeled_access_refs"] != []:
        raise RuntimeError("STEP occurrence coverage is incomplete or inconsistent")
    solid_count = geometry.get("solid_count")
    excluded = geometry.get("pcb_related_solid_indices")
    component_count = geometry.get("component_solid_count")
    if isinstance(solid_count, bool) or not isinstance(solid_count, int) or \
            solid_count <= 0:
        raise RuntimeError("STEP inspection solid_count is invalid")
    if not isinstance(excluded, list) or not excluded or \
            any(isinstance(item, bool) or not isinstance(item, int)
                or item < 0 or item >= solid_count for item in excluded) or \
            len(excluded) != len(set(excluded)):
        raise RuntimeError("STEP inspection PCB solid indices are invalid")
    if component_count != solid_count - len(excluded):
        raise RuntimeError("STEP inspection component solid census is inconsistent")
    registration = numeric_vector(
        geometry.get("case_registration_translate_mm_at_board_z0"), 3,
        "STEP registration")
    return geometry, excluded, registration


def require_same_step_geometry(supplied: Mapping[str, Any],
                               fresh: Mapping[str, Any]) -> None:
    for key in ("solid_count", "component_solid_count",
                "pcb_outline_candidate_indices", "pcb_related_solid_indices"):
        if supplied.get(key) != fresh.get(key):
            raise RuntimeError(f"supplied STEP inspection differs from regrade: {key}")
    supplied_registration = numeric_vector(
        supplied.get("case_registration_translate_mm_at_board_z0"), 3,
        "supplied STEP registration")
    fresh_registration = numeric_vector(
        fresh.get("case_registration_translate_mm_at_board_z0"), 3,
        "fresh STEP registration")
    for index in range(3):
        require_close(supplied_registration[index], fresh_registration[index],
                      f"STEP registration regrade axis {index}", 1e-7)


def interface(config: Mapping[str, Any], interface_id: str) -> Mapping[str, Any]:
    rows = config.get("interfaces")
    if not isinstance(rows, list):
        raise RuntimeError("enclosure interfaces must be an array")
    matches = [row for row in rows
               if isinstance(row, Mapping) and row.get("id") == interface_id]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one configured interface {interface_id}")
    return matches[0]


def derive_candidate_evidence(facts: Mapping[str, float],
                              config: Mapping[str, Any]) -> tuple[
                                  dict[str, Any], dict[str, float],
                                  dict[str, float]]:
    aperture_d = facts["lower_upright_d"] + 2 * facts["stalk_radial_clearance"]
    relief_extents = [
        [-facts["relief_x"] / 2, facts["relief_x"] / 2],
        [facts["mount_center_y"] - facts["relief_y"] / 2,
         facts["mount_center_y"] + facts["relief_y"] / 2],
    ]
    assembly = {
        "kind": "single-axis-complete-prewired-assembly-sweep",
        "direction": "+Z through adapter underside",
        "travel_mm": facts["insertion_sweep"],
        "start_upright_top_below_adapter_underside_mm":
            facts["insertion_sweep"] - facts["stalk_top_z"],
        "rectangular_relief_mm": [facts["relief_x"], facts["relief_y"]],
        "relief_extents_xy_mm": relief_extents,
        "upright_aperture_d_mm": aperture_d,
        "upright_north_extent_y_mm": facts["stalk_y"] + aperture_d / 2,
        "roof_hung_rail_gap_mm": facts["rail_gap"],
        "prewired_assembly_u_arch": {
            "open_bottom": True,
            "core_d_mm": facts["cable_core_d"],
            "governing_envelope_d_mm": facts["body_d"],
            "center_z_above_lid_mm": facts["body_axis_z"],
            "entry_flare_length_mm": facts["flare_length"],
            "entry_flare_d_mm": facts["flare_d"],
            "threading_required": False,
        },
        "selector_result": "EMPTY",
    }
    if assembly["start_upright_top_below_adapter_underside_mm"] <= 0:
        raise RuntimeError("insertion witness does not begin fully below adapter")

    north_rows = [row for row in config["interfaces"]
                  if row.get("role") == "rf-coax" and row.get("side") == "north"]
    side_rows = [row for row in config["interfaces"]
                 if row.get("role") == "rf-coax" and row.get("side") in {"west", "east"}]
    if not north_rows or not side_rows:
        raise RuntimeError("configured SMA access census is incomplete")
    north_gap = min(
        finite_number(row["center_mm"][1], "north SMA center y")
        - finite_number(row["plug_envelope_mm"][1], "north SMA plug y") / 2
        - facts["mount_north_y"] for row in north_rows)
    side_gap = min(
        abs(finite_number(row["center_mm"][0], "side SMA center x"))
        - finite_number(row["plug_envelope_mm"][0], "side SMA plug x") / 2
        - facts["mount_half_x"] for row in side_rows)
    usb = interface(config, "usb-c-power")
    usb_arch_top = (finite_number(usb["center_mm"][2], "USB center z")
                    + finite_number(usb["opening_mm"][1], "USB opening height") / 2)
    analytic = {
        "north_sma_plug_to_mount": north_gap,
        "side_sma_plug_to_mount": side_gap,
        "cable_lower_surface_above_usb_arch_top":
            facts["case_top_z"] + facts["body_axis_z"]
            - facts["cable_d"] / 2 - usb_arch_top,
        "u_arch_to_service_opening_y":
            facts["mount_south_y"] - facts["service_north_y"],
        "mount_to_service_opening":
            facts["mount_south_y"] - facts["service_north_y"],
        "mount_to_north_label":
            facts["north_label_y"] - facts["antenna_label_size"] / 2
            - facts["mount_north_y"],
        "cable_witness_beyond_south_case_edge":
            facts["cable_tail_length"] - facts["outer_half_y"],
    }
    if min(analytic.values()) <= 0:
        raise RuntimeError(f"non-positive derived access clearance: {analytic}")
    clearances = {
        "rigid_body_radial": facts["body_radial_clearance"],
        "body_above_lid": facts["body_axis_z"] - facts["body_d"] / 2,
        "body_below_roof": facts["mount_h"] - facts["mount_roof"]
            - (facts["body_axis_z"] + facts["body_d"] / 2),
        "total_vertical_play": facts["mount_h"] - facts["mount_roof"]
            - facts["body_d"],
        "full_antenna_arch_radial":
            (facts["cable_core_d"] - facts["body_d"]) / 2,
        "cable_radial_within_arch":
            (facts["cable_core_d"] - facts["cable_d"]) / 2,
        "arch_entry_over_full_antenna_radial":
            (facts["flare_d"] - facts["body_d"]) / 2,
        "u_entry_roof_ligament":
            facts["mount_h"] - (facts["body_axis_z"] + facts["flare_d"] / 2),
    }
    if min(clearances.values()) <= 0:
        raise RuntimeError(f"non-positive candidate clearance: {clearances}")
    return assembly, analytic, clearances


def require_generation(config_path: Path, config: Mapping[str, Any],
                       generation_path: Path, generation: Mapping[str, Any],
                       scad: Path) -> None:
    exact_keys(config, (
        "schema", "kind", "name", "mode", "subject", "process", "cad",
        "geometry", "fasteners", "interfaces", "thermal",
        "physical_validation"), "enclosure config")
    if config.get("schema") != 1 or \
            config.get("kind") != "pcb-enclosure-config-v1" or \
            config.get("mode") != "derived":
        raise RuntimeError("enclosure config has wrong schema/kind/mode")
    if generation.get("schema") != 1 or \
            generation.get("kind") != "pcb-enclosure-generation-v1":
        raise RuntimeError("generation receipt has wrong schema/kind")
    if generation.get("config", {}).get("raw_sha256") != sha256_file(config_path):
        raise RuntimeError("generation receipt is stale for enclosure config")
    source = generation.get("source")
    if not isinstance(source, Mapping) or source.get("sha256") != sha256_file(scad) or \
            source.get("size") != scad.stat().st_size:
        raise RuntimeError("generation receipt is stale for authored SCAD")
    authored = config.get("cad", {}).get("source", {})
    if authored.get("sha256") != sha256_file(scad) or \
            authored.get("size") != scad.stat().st_size:
        raise RuntimeError("config authored-SCAD binding is stale")
    printable = config.get("cad", {}).get("printable_parts")
    if printable != [
            "base", "lid", "insert_coupon", "rx2_antenna_mount",
            "rx2_antenna_fit_gauge"]:
        raise RuntimeError("enclosure printable-part census changed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--scad", type=Path, required=True)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--step-inspection", type=Path, required=True)
    parser.add_argument("--holder-stl", type=Path, required=True)
    parser.add_argument("--holder-png", type=Path, required=True)
    parser.add_argument("--holder-measurement", type=Path, required=True)
    parser.add_argument("--candidate-contract", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--openscad", default="openscad")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    openscad = trusted_openscad(args.openscad)
    inputs = {
        "config": require_input(args.config),
        "generation": require_input(args.generation),
        "scad": require_input(args.scad),
        "step": require_input(args.step),
        "step_inspection": require_input(args.step_inspection),
        "holder_stl": require_input(args.holder_stl),
        "holder_png": require_input(args.holder_png),
        "holder_measurement": require_input(args.holder_measurement),
        "candidate_contract": require_input(args.candidate_contract),
        "verification_script": require_input(Path(__file__)),
        "step_inspection_script": require_input(COMMON / "inspect_step.py"),
        "enclosure_common": require_input(COMMON / "enclosure_common.py"),
        "openscad_binary": require_input(Path(openscad)),
    }
    preliminary_config = load_yaml(inputs["config"])
    if not isinstance(preliminary_config, Mapping):
        raise RuntimeError("enclosure config must be an object")
    interface_relative = preliminary_config.get("subject", {}).get(
        "interface", {}).get("path")
    if not isinstance(interface_relative, str):
        raise RuntimeError("enclosure config has no bound subject interface path")
    project_root = inputs["config"].parents[2]
    interface_path = absolute(project_root / interface_relative)
    try:
        interface_path.relative_to(project_root)
    except ValueError as exc:
        raise RuntimeError("configured interface escapes the project root") from exc
    inputs["interface"] = require_input(interface_path)
    build_dir = absolute(args.build_dir)
    reject_symlink_chain(build_dir)
    if not build_dir.is_dir():
        raise RuntimeError("build directory must already exist")
    initial_input_snapshot = snapshot_inputs(inputs)
    snapshot_owner, work_inputs, work_input_snapshot = private_input_snapshots(
        inputs, build_dir, initial_input_snapshot)
    report = absolute(args.report)
    if report.parent != build_dir or report.name != REPORT_NAME:
        raise RuntimeError(f"report must be {build_dir / REPORT_NAME}")
    antenna_stl = build_dir / ANTENNA_NAME
    cable_stl = build_dir / CABLE_NAME
    outputs = (report, antenna_stl, cable_stl)
    for output in outputs:
        reject_symlink_chain(output, allow_missing_leaf=True)
    if len(set(outputs)) != len(outputs) or any(
            output in inputs.values() for output in outputs):
        raise RuntimeError("outputs must be mutually distinct from every input")
    for output in outputs:
        if output.exists() and any(
                os.path.samefile(output, value) for value in inputs.values()):
            raise RuntimeError("output aliases an evidence input")

    config = load_yaml(work_inputs["config"])
    if not isinstance(config, Mapping):
        raise RuntimeError("enclosure config must be an object")
    generation = strict_json(work_inputs["generation"])
    require_generation(work_inputs["config"], config, work_inputs["generation"],
                       generation, work_inputs["scad"])
    validate_selector_census(EVALUATED_SELECTORS)
    measurement = validate_holder_measurement(
        work_inputs["holder_measurement"], work_inputs["holder_stl"],
        work_inputs["holder_png"])
    candidate_contract, contract_facts, mesh_contracts = \
        validate_candidate_contract(
            work_inputs["candidate_contract"], work_inputs["holder_measurement"])

    inspection = strict_json(work_inputs["step_inspection"])

    with tempfile.TemporaryDirectory(
            prefix=".antenna-clearance-", dir=build_dir) as tmp_name:
        tmp = Path(tmp_name)
        fresh_component_mesh = tmp / "fresh-step-components.stl"
        fresh_inspection = step_inspector.inspect(
            work_inputs["step"], work_inputs["interface"], fresh_component_mesh)
        fresh_geometry, excluded_indices, registration = validate_step_inspection(
            fresh_inspection, work_inputs["step"], work_inputs["interface"], config)
        supplied_geometry, _, _ = validate_step_inspection(
            inspection, work_inputs["step"], work_inputs["interface"], config)
        require_same_step_geometry(supplied_geometry, fresh_geometry)
        geometry = fresh_geometry
        require_unchanged_inputs(work_inputs, work_input_snapshot)
        bad_probes = known_bad_probes(
            str(work_inputs["openscad_binary"]), work_inputs["scad"], tmp)
        selector_rows: list[dict[str, Any]] = []
        observed_facts: list[dict[str, float]] = []
        for name in EMPTY_SELECTORS:
            row, facts = selector(
                str(work_inputs["openscad_binary"]), work_inputs["scad"],
                name, True, tmp)
            require_unchanged_inputs(work_inputs, work_input_snapshot)
            validate_facts(facts, contract_facts, config, measurement)
            selector_rows.append(row)
            observed_facts.append(facts)
        exported: dict[str, tuple[Path, dict[str, Any], dict[str, Any]]] = {}
        for name, filename in zip(SOLID_SELECTORS, (ANTENNA_NAME, CABLE_NAME)):
            row, facts = selector(
                str(work_inputs["openscad_binary"]), work_inputs["scad"],
                name, False, tmp)
            require_unchanged_inputs(work_inputs, work_input_snapshot)
            validate_facts(facts, contract_facts, config, measurement)
            selector_rows.append(row)
            observed_facts.append(facts)
            mesh = tmp / f"{name}.stl"
            mesh_stat = os.lstat(mesh)
            if not stat.S_ISREG(mesh_stat.st_mode) or stat.S_ISLNK(mesh_stat.st_mode):
                raise RuntimeError(f"{name} export is not a regular no-link file")
            if any(os.path.samefile(mesh, path) for path in (
                    *inputs.values(), *work_inputs.values())):
                raise RuntimeError(f"{name} export aliases an evidence input")
            metrics = stl_metrics(mesh)
            contract_name = "antenna" if name == "rx2_antenna_reference" else "cable"
            validate_mesh_against_contract(
                name, metrics, mesh_contracts[contract_name])
            bad_probes.extend(mesh_known_bad_probes(
                name, metrics, mesh_contracts[contract_name]))
            exported[name] = (mesh, row, metrics)
        if os.path.samefile(
                exported["rx2_antenna_reference"][0],
                exported["rx2_cable_reference"][0]):
            raise RuntimeError("antenna and cable exports alias each other")
        if any(facts != observed_facts[0] for facts in observed_facts[1:]):
            raise RuntimeError("SCAD machine facts changed between selector runs")
        facts = observed_facts[0]
        assembly_path, analytic_clearances, candidate_clearances = \
            derive_candidate_evidence(facts, config)

        import cadquery as cq
        import OCP

        imported = cq.importers.importStep(str(work_inputs["step"]))
        solids = imported.solids().vals()
        if len(solids) != geometry["solid_count"]:
            raise RuntimeError("STEP solid census differs from inspection")
        excluded = set(excluded_indices)
        components = [solid for index, solid in enumerate(solids)
                      if index not in excluded]
        if len(components) != geometry["component_solid_count"]:
            raise RuntimeError("fresh STEP component census differs from inspection")
        board_bottom_z = facts["board_bottom_z"]
        transform = [registration[0], registration[1],
                     registration[2] + board_bottom_z]
        component_shape = cq.Compound.makeCompound(components).translate(
            tuple(transform))
        antenna_local = brep_from_stl(
            exported["rx2_antenna_reference"][0], cq)
        cable_local = brep_from_stl(exported["rx2_cable_reference"][0], cq)
        exact_mesh_subjects = {
            name: {
                "sha256": row[2]["sha256"],
                "size": row[2]["size"],
            }
            for name, row in exported.items()
        }
        antenna_installed = antenna_local.translate((0, 0, facts["case_top_z"]))
        cable_installed = cable_local.translate((0, 0, facts["case_top_z"]))
        exact = {
            "antenna_vs_step_components_mm3": exact_volume(
                antenna_installed.intersect(component_shape)),
            "cable_vs_step_components_mm3": exact_volume(
                cable_installed.intersect(component_shape)),
            "antenna_vs_cable_mm3": exact_volume(
                antenna_local.intersect(cable_local)),
        }
        if any(value > 1e-9 for value in exact.values()):
            raise RuntimeError(f"exact candidate collision found: {exact}")

        # No input may drift between selector export, exact STEP evaluation,
        # and publication of the validated meshes.
        require_unchanged_inputs(inputs, initial_input_snapshot)
        require_unchanged_inputs(work_inputs, work_input_snapshot)
        # Install only fully validated meshes. os.replace replaces a link name
        # itself rather than following it; the preceding checks reject aliases.
        atomic_install(exported["rx2_antenna_reference"][0], antenna_stl)
        atomic_install(exported["rx2_cable_reference"][0], cable_stl)

    for mesh in (antenna_stl, cable_stl):
        mesh_stat = os.lstat(mesh)
        if not stat.S_ISREG(mesh_stat.st_mode) or stat.S_ISLNK(mesh_stat.st_mode):
            raise RuntimeError(f"installed reference mesh is not regular: {mesh}")
        if any(os.path.samefile(mesh, path) for path in inputs.values()):
            raise RuntimeError("installed reference mesh aliases an evidence input")
    if os.path.samefile(antenna_stl, cable_stl):
        raise RuntimeError("installed antenna and cable meshes alias each other")
    antenna_metrics = stl_metrics(antenna_stl)
    cable_metrics = stl_metrics(cable_stl)
    installed_metrics = {
        "rx2_antenna_reference": antenna_metrics,
        "rx2_cable_reference": cable_metrics,
    }
    for name, expected in exact_mesh_subjects.items():
        actual = installed_metrics[name]
        if actual["sha256"] != expected["sha256"] or \
                actual["size"] != expected["size"]:
            raise RuntimeError(
                f"installed {name} differs from exact-collision subject")
    validate_mesh_against_contract(
        "rx2_antenna_reference", antenna_metrics, mesh_contracts["antenna"])
    validate_mesh_against_contract(
        "rx2_cable_reference", cable_metrics, mesh_contracts["cable"])
    require_unchanged_inputs(inputs, initial_input_snapshot)
    require_unchanged_inputs(work_inputs, work_input_snapshot)
    version = run_openscad([str(work_inputs["openscad_binary"]), "--version"])
    if version.returncode != 0 or not version.stdout.strip():
        raise RuntimeError("could not identify OpenSCAD backend")
    receipt = {
        "schema": 1,
        "kind": KIND,
        "status": "INCOMPLETE",
        "run_status": "COMPLETE",
        "candidate_collision": "PASS",
        "status_reason": (
            "candidate envelope is collision-free, but the actual antenna/cable "
            "profile and physical retention/rattle/print fit are not evidenced"),
        "backend": {
            "openscad": version.stdout.strip(),
            "cadquery": getattr(cq, "__version__", "unknown"),
            "ocp": getattr(OCP, "__version__", "unknown"),
        },
        "inputs": {name: binding(path) for name, path in inputs.items()},
        "machine_contract": {
            "kind": candidate_contract["kind"],
            "status": candidate_contract["status"],
            "scad_facts": facts,
            "fact_census": list(FACT_KEYS),
            "result": "PASS",
        },
        "selector_contract": {
            "evaluated_census": list(EVALUATED_SELECTORS),
            "sentinel_prefix": SELECTOR_SENTINEL,
            "success_sentinel_prefix": SELECTOR_OK_SENTINEL,
            "known_bad_probes": bad_probes,
        },
        "candidate_antenna_reference": {
            **binding(antenna_stl), "selector": "rx2_antenna_reference",
            "printable": False, "mesh_metrics": antenna_metrics,
        },
        "candidate_cable_reference": {
            **binding(cable_stl), "selector": "rx2_cable_reference",
            "printable": False, "mesh_metrics": cable_metrics,
        },
        "assembly_path": assembly_path,
        "openscad_checks": selector_rows,
        "exact_step_checks": {
            "authority": (
                "private byte-snapshot SCAD selector meshes sewn to OCP solids; "
                "component transform/classification freshly regraded from the "
                "private STEP and bound PCB interface"),
            "fresh_step_regrade": {
                "status": fresh_inspection["status"],
                "coverage": fresh_inspection["occurrence_coverage"],
                "supplied_geometry_match": "PASS",
            },
            "reference_mesh_subjects": exact_mesh_subjects,
            "step_solid_count": len(solids),
            "pcb_related_solid_count": len(excluded),
            "component_solid_count": len(components),
            "board_bottom_z_mm_from_config": board_bottom_z,
            "case_top_z_mm_from_config": facts["case_top_z"],
            "applied_component_translate_mm": transform,
            **exact,
            "result": "EMPTY",
        },
        "analytic_access_clearances_mm": analytic_clearances,
        "candidate_clearances_mm": candidate_clearances,
        "excluded_claims": [
            "No actual antenna or cable dimension is inferred from holder voids.",
            "Clearance does not prove retention, rattle resistance, or physical fit.",
            "No board drop-in, interface-mating, or antenna fit test was performed.",
        ],
    }
    require_unchanged_inputs(inputs, initial_input_snapshot)
    require_unchanged_inputs(work_inputs, work_input_snapshot)
    atomic_json(report, receipt)
    snapshot_owner.cleanup()
    print(f"ANTENNA CANDIDATE PASS / STATUS INCOMPLETE — wrote {report}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        print(f"ANTENNA CLEARANCE ERROR — {exc}", file=sys.stderr)
        raise SystemExit(1)
