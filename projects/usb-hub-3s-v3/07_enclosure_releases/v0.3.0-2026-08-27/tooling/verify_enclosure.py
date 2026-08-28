#!/usr/bin/env python3
"""Verify exact subject binding, interface coverage, fasteners, and meshes.

The automated result is deliberately bounded. CAD_READY requires an exact
STEP inspection and an empty STEP-component/case collision result. Printed
fit and thermal status require separate operator evidence.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    PHYSICAL_KIND, EnclosureError, load_bound_config, load_json, load_yaml,
    semantic_sha256, sha256_file, stl_metrics, validate_output_path,
    write_json,
)


def check(name: str, status: str, graded: int, total: int,
          findings: Sequence[str] = (), **evidence: Any) -> dict[str, Any]:
    if status not in {"PASS", "FAIL", "INCOMPLETE", "NOT_APPLICABLE"}:
        raise EnclosureError(f"internal status error for {name}: {status}")
    if total < 0 or graded < 0 or graded > total:
        raise EnclosureError(f"internal denominator error for {name}")
    return {"name": name, "status": status, "graded": graded, "total": total,
            "findings": list(findings), "evidence": evidence}


def _build_record_path(build_dir: Path, record: Any, where: str) -> Path:
    if not isinstance(record, Mapping) or not isinstance(record.get("path"), str):
        raise EnclosureError(f"{where}: missing build-file identity")
    name = record["path"]
    if Path(name).name != name or name in {"", ".", ".."}:
        raise EnclosureError(f"{where}: evidence path is not a build filename")
    path = build_dir / name
    if not path.is_file() or path.is_symlink() or \
            record.get("sha256") != sha256_file(path) or \
            record.get("size") != path.stat().st_size:
        raise EnclosureError(f"{where}: file differs from its receipt")
    return path


def _subject_check(loaded: Mapping[str, Any]) -> dict[str, Any]:
    bindings = loaded["bindings"]
    findings = []
    for name, row in bindings.items():
        if not row.get("matches", False):
            findings.append(f"{name} size/hash mismatch")
    return check("subject_binding", "FAIL" if findings else "PASS",
                 len(bindings) - len(findings), len(bindings), findings,
                 files={name: {key: value for key, value in row.items()
                               if key != "path"}
                        for name, row in bindings.items()})


def _interface_check(config: Mapping[str, Any],
                     interface: Mapping[str, Any]) -> dict[str, Any]:
    candidates = {row["ref"] for row in interface["board"]["access_candidates"]}
    footprints = {row["ref"] for row in interface["board"]["footprints"]}
    rows = {row["ref"]: row for row in config["interfaces"]}
    findings = []
    for ref in sorted(candidates - set(rows)):
        findings.append(f"access candidate {ref} has no disposition")
    for ref in sorted(set(rows) - footprints):
        findings.append(f"configured interface {ref} is absent from PCB")
    opening_rows = []
    board_size = interface["board"]["outline"]["size_mm"]
    inner_half_x = board_size[0] / 2 + config["geometry"]["xy_clearance_mm"]
    inner_half_y = board_size[1] / 2 + config["geometry"]["xy_clearance_mm"]
    floor = config["geometry"]["floor_mm"]
    ceiling = config["geometry"]["inside_top_z_mm"]
    overall_top = ceiling + config["geometry"]["roof_mm"]
    edge_tolerance = max(config["geometry"]["wall_mm"], 5.0)
    for ref, row in sorted(rows.items()):
        if row["disposition"] not in {"opening", "service_opening"}:
            continue
        opening_rows.append(row)
        opening = row["opening_mm"]
        plug = row["plug_envelope_mm"]
        clearance = row["clearance_mm"]
        if (opening[0] + 1e-9 < plug[0] + 2*clearance or
                opening[1] + 1e-9 < plug[1] + 2*clearance):
            findings.append(
                f"{ref} opening {opening} does not clear plug {plug[:2]} "
                f"plus {clearance} mm per side")
        x, y, z = row["center_mm"]
        side = row["side"]
        if side in {"north", "south"}:
            placement_issues = []
            expected_y = board_size[1] / 2 * (1 if side == "north" else -1)
            if abs(y - expected_y) > edge_tolerance:
                placement_issues.append("anchor is not near the named PCB edge")
            if abs(x) + opening[0] / 2 > inner_half_x + 1e-9:
                placement_issues.append("opening exceeds the panel span")
            if placement_issues:
                findings.append(f"{ref} {side} placement: " +
                                "; ".join(placement_issues))
        elif side in {"east", "west"}:
            placement_issues = []
            expected_x = board_size[0] / 2 * (1 if side == "east" else -1)
            if abs(x - expected_x) > edge_tolerance:
                placement_issues.append("anchor is not near the named PCB edge")
            if abs(y) + opening[0] / 2 > inner_half_y + 1e-9:
                placement_issues.append("opening exceeds the panel span")
            if placement_issues:
                findings.append(f"{ref} {side} placement: " +
                                "; ".join(placement_issues))
        else:
            if (abs(x) + opening[0] / 2 > inner_half_x + 1e-9 or
                    abs(y) + opening[1] / 2 > inner_half_y + 1e-9):
                findings.append(f"{ref} top opening exceeds the usable roof")
            if abs(z - ceiling) > 1e-6:
                findings.append(f"{ref} top opening z must equal inside_top_z_mm")
        if side != "top" and (z - opening[1] / 2 < floor - 1e-9 or
                               z + opening[1] / 2 > overall_top + 1e-9):
            findings.append(f"{ref} side opening exceeds the interior height")
    total = len(candidates) + len(rows) + 3 * len(opening_rows)
    graded = max(0, total - len(findings))
    return check("interface_coverage", "FAIL" if findings else "PASS",
                 graded, total, findings, candidates=sorted(candidates),
                 dispositions={ref: row["disposition"] for ref, row in rows.items()})


def _fastener_check(config: Mapping[str, Any],
                    interface: Mapping[str, Any]) -> dict[str, Any]:
    f = config["fasteners"]; g = config["geometry"]
    insert = f["insert"]; screw = f["screw"]
    mount_counts: dict[str, int] = {}
    mount_positions: dict[str, list[list[float]]] = {}
    for row in interface["board"]["mounting_holes"]:
        mount_counts[row["ref"]] = mount_counts.get(row["ref"], 0) + 1
        mount_positions.setdefault(row["ref"], []).append(row["position_mm"])
    findings = []
    evidence = {}
    for ref in f["board_holes"]:
        if mount_counts.get(ref, 0) != 1:
            findings.append(
                f"selected mounting ref {ref} has {mount_counts.get(ref, 0)} holes; expected 1")
    radial = (f["boss_d_mm"] - max(insert["hole_d_mm"],
                                    insert["flange_recess_d_mm"])) / 2
    evidence["boss_radial_wall_mm"] = radial
    if radial + 1e-9 < f["minimum_radial_wall_mm"]:
        findings.append(
            f"boss radial wall {radial:.3f} < {f['minimum_radial_wall_mm']:.3f} mm")
    pocket_bottom = (g["board_bottom_z_mm"] - insert["length_mm"] -
                     insert["bottom_clearance_mm"])
    evidence["board_insert_pocket_bottom_z_mm"] = pocket_bottom
    evidence["pocket_bottom_above_floor_mm"] = pocket_bottom - g["floor_mm"]
    if pocket_bottom + 1e-9 < g["floor_mm"]:
        findings.append("board insert pocket cuts below the interior floor plane")
    if insert["flange_recess_d_mm"] + 1e-9 < insert["flange_d_mm"]:
        findings.append("insert flange does not fit its recess")
    overall = g["inside_top_z_mm"] + g["roof_mm"]
    fixed_checks = 3
    if f["strategy"] == "shared_board":
        bearing = overall - screw["head_recess_depth_mm"]
        distance = bearing - g["board_bottom_z_mm"]
        engagement = screw["lid_length_mm"] - distance
        tip_clearance = insert["length_mm"] - engagement
        evidence.update(lid_head_bearing_z_mm=bearing,
                        lid_thread_engagement_mm=engagement,
                        lid_tip_clearance_mm=tip_clearance)
        if engagement + 1e-9 < screw["minimum_engagement_mm"]:
            findings.append("shared lid screw has insufficient insert engagement")
        if tip_clearance + 1e-9 < screw["minimum_tip_clearance_mm"]:
            findings.append("shared lid screw bottoms in insert")
        fixed_checks += 2
    else:
        case_radial = (f["case_post_d_mm"] - max(
            insert["hole_d_mm"], insert["flange_recess_d_mm"])) / 2
        case_pocket_bottom = (g["inside_top_z_mm"] - insert["length_mm"] -
                              insert["bottom_clearance_mm"])
        board_engagement = (
            screw["board_length_mm"] - interface["board"]["thickness_mm"])
        board_tip = insert["length_mm"] - board_engagement
        case_bearing = overall - screw["head_recess_depth_mm"]
        case_engagement = (
            screw["lid_length_mm"] -
            (case_bearing - g["inside_top_z_mm"]))
        case_tip = insert["length_mm"] - case_engagement
        evidence.update(case_post_radial_wall_mm=case_radial,
                        case_insert_pocket_bottom_z_mm=case_pocket_bottom,
                        board_thread_engagement_mm=board_engagement,
                        board_tip_clearance_mm=board_tip,
                        case_thread_engagement_mm=case_engagement,
                        case_tip_clearance_mm=case_tip)
        if case_radial + 1e-9 < f["minimum_radial_wall_mm"]:
            findings.append(
                f"case-post radial wall {case_radial:.3f} < "
                f"{f['minimum_radial_wall_mm']:.3f} mm")
        if case_pocket_bottom + 1e-9 < g["floor_mm"]:
            findings.append("case insert pocket cuts below the interior floor plane")
        for label, engagement, tip in (
                ("board", board_engagement, board_tip),
                ("case", case_engagement, case_tip)):
            if engagement + 1e-9 < screw["minimum_engagement_mm"]:
                findings.append(f"{label} screw has insufficient insert engagement")
            if tip + 1e-9 < screw["minimum_tip_clearance_mm"]:
                findings.append(f"{label} screw bottoms in insert")
        # Independent screws must also be independent geometry.  Merely
        # naming two groups is insufficient if their posts overlap or reuse
        # the same axis.
        minimum_axis_distance = (f["boss_d_mm"] + f["case_post_d_mm"]) / 2
        axis_distances = []
        for ref in f["board_holes"]:
            if len(mount_positions.get(ref, [])) != 1:
                continue
            board_point = mount_positions[ref][0]
            for case_index, case_point in enumerate(f["case_holes_mm"]):
                distance = math.hypot(board_point[0] - case_point[0],
                                      board_point[1] - case_point[1])
                axis_distances.append({
                    "board_ref": ref,
                    "case_index": case_index,
                    "distance_mm": distance,
                })
                if distance + 1e-9 < minimum_axis_distance:
                    findings.append(
                        f"board screw {ref} and case screw {case_index} axes "
                        f"are {distance:.3f} mm apart; posts require "
                        f">= {minimum_axis_distance:.3f} mm")
        evidence["minimum_board_case_axis_distance_mm"] = minimum_axis_distance
        evidence["board_case_axis_distances"] = axis_distances
        fixed_checks += 6 + len(axis_distances)
    total = fixed_checks + len(f["board_holes"])
    return check("fastener_geometry", "FAIL" if findings else "PASS",
                 max(0, total - len(findings)), total, findings, **evidence)


def _mesh_check(config_path: Path, config: Mapping[str, Any],
                interface: Mapping[str, Any],
                build_dir: Path) -> dict[str, Any]:
    parts = config["cad"]["printable_parts"]
    findings = []
    metrics = {}
    generation_file = None
    generation_contract = None
    generation_path = build_dir / "generation.json"
    try:
        if not generation_path.is_file() or generation_path.is_symlink():
            raise EnclosureError("generation.json is missing or unsafe")
        generation = load_json(generation_path)
        if generation.get("schema") != 1 or \
                generation.get("kind") != "pcb-enclosure-generation-v1":
            raise EnclosureError("generation.json has wrong schema/kind")
        if generation.get("config", {}).get("raw_sha256") != \
                sha256_file(config_path):
            raise EnclosureError("generation.json is stale for requested config bytes")
        if generation["config"].get("semantic_sha256") != semantic_sha256(config):
            raise EnclosureError("generation.json differs from requested config semantics")
        if generation["interface"].get("semantic_sha256") != \
                semantic_sha256(interface):
            raise EnclosureError("generation.json differs from requested interface")
        part_rows = generation.get("parts")
        if not isinstance(part_rows, list) or \
                any(not isinstance(row, Mapping) or
                    not isinstance(row.get("part"), str) for row in part_rows):
            raise EnclosureError("generation.json lacks its printable-part census")
        part_by_name = {row["part"]: row for row in part_rows}
        if len(part_by_name) != len(part_rows) or set(part_by_name) != set(parts):
            raise EnclosureError("generation.json printable-part census differs from config")
        authored = config["cad"].get("source")
        installed_case = generation.get("installed_case")
        if authored is not None and (
                not isinstance(installed_case, Mapping) or
                installed_case.get("canonicalization") !=
                "ascii-stl-facet-order-v1" or any(
                    row.get("canonicalization") != "ascii-stl-facet-order-v1"
                    for row in part_rows)):
            raise EnclosureError(
                "generation.json lacks canonical authored mesh identities")
        mount_by_ref: dict[str, list[list[float]]] = {}
        for row in interface["board"]["mounting_holes"]:
            mount_by_ref.setdefault(row["ref"], []).append(row["position_mm"])
        board_axes = []
        for ref in config["fasteners"]["board_holes"]:
            matches = mount_by_ref.get(ref, [])
            if len(matches) != 1:
                raise EnclosureError(
                    f"cannot derive generated assembly contract for {ref}")
            board_axes.append(matches[0])
        case_axes = config["fasteners"]["case_holes_mm"]
        separate = config["fasteners"]["strategy"] == "separate_perimeter"
        expected_contract = {
            "kind": "pcb-enclosure-assembly-contract-v1",
            "fastener_strategy": config["fasteners"]["strategy"],
            "board_fastener_axes_mm": board_axes,
            "case_fastener_axes_mm": case_axes,
            "shell_closure_axes_mm": case_axes if separate else board_axes,
            "pcb_retained_with_lid_removed": separate,
            "shared_board_shell_axes": not separate,
        }
        generation_contract = generation.get("assembly_contract")
        if generation_contract != expected_contract:
            raise EnclosureError(
                "generation.json assembly contract differs from fastener intent")
        generation_file = {
            "path": generation_path.name,
            "sha256": sha256_file(generation_path),
            "size": generation_path.stat().st_size,
        }
    except (KeyError, OSError, EnclosureError) as exc:
        findings.append(f"generation: {exc}")
        part_by_name = {}
    for part in parts:
        path = build_dir / f"{part}.stl"
        if not path.is_file():
            findings.append(f"{part}: mesh missing")
            continue
        try:
            row = stl_metrics(path)
            metrics[part] = row
        except EnclosureError as exc:
            findings.append(f"{part}: {exc}")
            continue
        if not row["edge_manifold"]:
            findings.append(
                f"{part}: {row['nonmanifold_edges']} non-two-use edge(s)")
        if not row["orientation_consistent"]:
            findings.append(
                f"{part}: {row['orientation_mismatches']} inconsistent edge orientation(s)")
        if row["components"] != 1:
            findings.append(f"{part}: expected 1 component, got {row['components']}")
        if row["absolute_volume_mm3"] <= 1e-6:
            findings.append(f"{part}: zero signed volume")
        if row["degenerate_facets"] / row["triangles"] > 0.002:
            findings.append(
                f"{part}: degenerate facet rate exceeds 0.2 percent")
        record = part_by_name.get(part)
        if record is None or record.get("path") != path.name or \
                record.get("sha256") != sha256_file(path) or \
                record.get("size") != path.stat().st_size:
            findings.append(f"{part}: mesh differs from generation.json")
    failed_parts = {item.split(":", 1)[0] for item in findings
                    if item.split(":", 1)[0] in parts}
    auxiliary_failures = int(any(item.startswith("generation:")
                                 for item in findings))
    total = len(parts) + 1
    return check("printable_meshes", "FAIL" if findings else "PASS",
                 max(0, total - len(failed_parts) - auxiliary_failures),
                 total, findings, parts=metrics,
                 generation_file=generation_file,
                 assembly_contract=generation_contract,
                 support_policy=config["process"]["support_policy"])


def _clearance_check(config_path: Path, config: Mapping[str, Any],
                     step_report_path: Path | None,
                     collision_mesh: Path | None,
                     collision_report_path: Path | None,
                     collision_tolerance: float) -> dict[str, Any]:
    if step_report_path is None or not step_report_path.is_file():
        return check("exact_solid_clearance", "INCOMPLETE", 0, 2,
                     ["exact STEP inspection report is missing"])
    try:
        report = load_json(step_report_path)
    except EnclosureError as exc:
        return check("exact_solid_clearance", "FAIL", 0, 2, [str(exc)])
    report_file = {"path": step_report_path.name,
                   "sha256": sha256_file(step_report_path),
                   "size": step_report_path.stat().st_size}
    findings = []
    if report.get("kind") != "pcb-enclosure-step-inspection-v1":
        findings.append("wrong STEP-inspection report kind")
    if report.get("step", {}).get("sha256") != config["subject"]["step"]["sha256"]:
        findings.append("STEP-inspection report is bound to another STEP")
    if report.get("interface", {}).get("sha256") != \
            config["subject"]["interface"]["sha256"]:
        findings.append("STEP-inspection report is bound to another interface")
    if findings:
        return check("exact_solid_clearance", "FAIL", 0, 2, findings,
                     step_inspection=report, step_inspection_file=report_file)
    if report.get("status") == "FAIL":
        coverage = report.get("occurrence_coverage", {})
        reasons = []
        if coverage.get("zero_modeled_denominator"):
            reasons.append("modeled footprint denominator is zero")
        if coverage.get("missing_modeled_refs"):
            reasons.append("missing=" +
                           ",".join(coverage["missing_modeled_refs"]))
        if coverage.get("unmodeled_access_refs"):
            reasons.append("unmodeled-access=" +
                           ",".join(coverage["unmodeled_access_refs"]))
        findings.append("STEP assembly coverage failed: " +
                        (" ".join(reasons) if reasons else "unspecified report failure"))
        return check("exact_solid_clearance", "FAIL", 1, 2, findings,
                     step_inspection=report, step_inspection_file=report_file)
    if report.get("status") != "COMPLETE":
        return check("exact_solid_clearance", "INCOMPLETE", 1, 2,
                     ["exact STEP geometry backend is unavailable"],
                     step_inspection=report, step_inspection_file=report_file)
    if collision_mesh is None or not collision_mesh.is_file():
        return check("exact_solid_clearance", "INCOMPLETE", 1, 2,
                     ["STEP-component/case intersection mesh is missing"],
                     step_inspection=report, step_inspection_file=report_file)
    if collision_report_path is None or not collision_report_path.is_file():
        return check("exact_solid_clearance", "INCOMPLETE", 1, 2,
                     ["hash-bound exact-collision receipt is missing"],
                     step_inspection=report, step_inspection_file=report_file)
    try:
        collision_report = load_json(collision_report_path)
        collision_report_file = {
            "path": collision_report_path.name,
            "sha256": sha256_file(collision_report_path),
            "size": collision_report_path.stat().st_size,
        }
        if collision_report.get("kind") != "pcb-enclosure-collision-v1" or \
                collision_report.get("status") != "COMPLETE":
            raise EnclosureError("collision receipt is not COMPLETE v1 evidence")
        build_dir = collision_report_path.parent
        inputs = collision_report.get("inputs")
        if not isinstance(inputs, Mapping):
            raise EnclosureError("collision receipt lacks input identities")
        for key in ("step_inspection", "step", "component_mesh", "generation",
                    "assembled_case_mesh"):
            if not isinstance(inputs.get(key), Mapping):
                raise EnclosureError(f"collision receipt lacks {key} identity")
        generation_path = _build_record_path(
            build_dir, inputs.get("generation"), "collision generation receipt")
        generation = load_json(generation_path)
        if generation.get("kind") != "pcb-enclosure-generation-v1":
            raise EnclosureError("collision generation receipt has wrong kind")
        if generation.get("config", {}).get("semantic_sha256") != \
                semantic_sha256(config) or \
                generation.get("config", {}).get("raw_sha256") != \
                sha256_file(config_path):
            raise EnclosureError("collision generation receipt is stale for config")
        source_record = generation.get("source")
        source_path = _build_record_path(
            build_dir, source_record, "collision generation CAD source")
        authority = generation.get("authority")
        authored = config["cad"].get("source")
        if authored is not None:
            expected_authority = {
                "kind": "authored_scad",
                "binding": {key: authored[key]
                            for key in ("path", "sha256", "size")},
            }
            if authority != expected_authority or \
                    source_record.get("sha256") != authored["sha256"] or \
                    source_record.get("size") != authored["size"]:
                raise EnclosureError(
                    "collision generation CAD source differs from authored authority")
        elif not isinstance(authority, Mapping) or \
                authority.get("kind") != "built_in_v1":
            raise EnclosureError("collision generation lacks built-in CAD authority")
        installed_record = generation.get("installed_case")
        if not isinstance(installed_record, Mapping) or \
                installed_record.get("selector") != "installed_case" or \
                installed_record.get("path") != "assembled-case.stl":
            raise EnclosureError(
                "collision generation lacks the fixed installed_case selector")
        case_path = _build_record_path(
            build_dir, installed_record, "generated installed-case mesh")
        command = installed_record.get("command")
        engine = generation.get("engine")
        if not isinstance(engine, Mapping) or not isinstance(command, list) or \
                len(command) != 8 or \
                command[1] != "-o" or Path(command[2]).resolve() != case_path.resolve() or \
                command[3:7] != ["-D", 'part="installed_case"', "-D",
                                  "show_reference_board=false"] or \
                Path(command[7]).resolve() != source_path.resolve() or \
                engine.get("executable") != command[0]:
            raise EnclosureError("generated installed_case command is not canonical")
        if inputs.get("assembled_case_mesh") != installed_record:
            raise EnclosureError(
                "collision assembled-case input differs from generation receipt")
        if inputs.get("step_inspection", {}).get("sha256") != \
                sha256_file(step_report_path) or \
                inputs.get("step_inspection", {}).get("size") != \
                step_report_path.stat().st_size:
            raise EnclosureError("collision receipt binds another STEP inspection")
        if inputs.get("step", {}).get("sha256") != \
                config["subject"]["step"]["sha256"] or \
                inputs.get("step", {}).get("size") != \
                config["subject"]["step"]["size"]:
            raise EnclosureError("collision receipt binds another STEP subject")
        component_record = report.get("geometry", {}).get("component_mesh")
        if not isinstance(component_record, Mapping) or \
                inputs.get("component_mesh") != component_record:
            raise EnclosureError(
                "collision receipt component mesh differs from STEP inspection")
        component_path = _build_record_path(
            build_dir, inputs.get("component_mesh"), "STEP component mesh")
        transform = collision_report.get("transform")
        registration = report.get("geometry", {}).get(
            "case_registration_translate_mm_at_board_z0")
        if not isinstance(transform, Mapping) or \
                transform.get("case_registration_translate_mm_at_board_z0") != registration:
            raise EnclosureError("collision receipt uses another STEP registration")
        board_z = transform.get("board_bottom_z_mm")
        if isinstance(board_z, bool) or not isinstance(board_z, (int, float)) or \
                not math.isclose(float(board_z),
                                 float(config["geometry"]["board_bottom_z_mm"]),
                                 rel_tol=0, abs_tol=1e-9):
            raise EnclosureError("collision receipt uses another board-bottom Z")
        expected_translate = [float(registration[0]), float(registration[1]),
                              float(registration[2]) + float(board_z)]
        applied = transform.get("applied_component_translate_mm")
        if not isinstance(applied, list) or len(applied) != 3 or any(
                isinstance(value, bool) or not isinstance(value, (int, float)) or
                not math.isclose(float(value), expected_translate[index],
                                 rel_tol=0, abs_tol=1e-9)
                for index, value in enumerate(applied)):
            raise EnclosureError("collision receipt has a wrong applied transform")
        result = collision_report.get("result")
        if not isinstance(result, Mapping):
            raise EnclosureError("collision receipt lacks a result")
        collision_path = _build_record_path(
            build_dir, result.get("collision_mesh"), "collision mesh")
        if collision_path.resolve() != collision_mesh.resolve():
            raise EnclosureError("verified collision mesh differs from receipt output")
        mesh = stl_metrics(collision_mesh)
        if result.get("mesh_metrics") != mesh:
            raise EnclosureError("collision mesh metrics differ from receipt")
        volume = result.get("exact_brep_volume_mm3")
        if isinstance(volume, bool) or not isinstance(volume, (int, float)) or \
                not math.isfinite(volume) or volume < 0:
            raise EnclosureError("collision receipt has invalid exact BRep volume")
        classification = result.get("classification")
        if classification == "EMPTY":
            if volume != 0 or \
                    result.get("representation") != \
                    "zero-area-marker-for-empty-brep" or \
                    mesh["component_absolute_volume_mm3"] != 0 or \
                    mesh["degenerate_facets"] < 1:
                raise EnclosureError("empty collision representation is contradictory")
        elif classification == "INTERSECTION":
            if volume <= 0 or result.get("representation") != \
                    "tessellation-of-exact-brep-common":
                raise EnclosureError("nonempty collision representation is contradictory")
        else:
            raise EnclosureError("collision receipt has unknown classification")
    except EnclosureError as exc:
        return check("exact_solid_clearance", "FAIL", 1, 2,
                     [str(exc)],
                     step_inspection=report, step_inspection_file=report_file)
    if volume > collision_tolerance:
        findings.append(
            f"case intersects exact STEP components by {volume:.6g} mm^3 "
            f"> {collision_tolerance:.6g} mm^3")
    return check("exact_solid_clearance", "FAIL" if findings else "PASS",
                 2 if not findings else 1, 2, findings,
                 step_inspection=report, step_inspection_file=report_file,
                 collision_mesh=mesh,
                 collision_report=collision_report,
                 collision_report_file=collision_report_file,
                 generation=generation,
                 generation_file={"path": generation_path.name,
                                  "sha256": sha256_file(generation_path),
                                  "size": generation_path.stat().st_size},
                 component_mesh={"path": component_path.name,
                                 "sha256": sha256_file(component_path),
                                 "size": component_path.stat().st_size},
                 assembled_case_mesh={"path": case_path.name,
                                      "sha256": sha256_file(case_path),
                                      "size": case_path.stat().st_size},
                 collision_volume_tolerance_mm3=collision_tolerance)


def _thermal_check(config: Mapping[str, Any]) -> dict[str, Any]:
    thermal = config["thermal"]
    findings = []
    if thermal["risk"] in {"moderate", "high"} and not \
            thermal["physical_soak_required"]:
        findings.append("moderate/high thermal risk lacks required physical soak")
    if thermal["risk"] == "high" and not thermal["vents"]:
        findings.append("high thermal risk has no declared ventilation")
    return check("thermal_plan", "FAIL" if findings else "PASS",
                 2 - len(findings), 2, findings, risk=thermal["risk"],
                 load_case=thermal["load_case"], vent_groups=len(thermal["vents"]))


def _physical_check(config: Mapping[str, Any], config_hash: str,
                    evidence_path: Path | None) -> tuple[dict[str, Any], bool, bool]:
    required = config["physical_validation"]
    keys = [key for key, value in required.items() if value]
    if evidence_path is None or not evidence_path.is_file():
        return (check("physical_evidence", "INCOMPLETE", 0, len(keys),
                      ["operator physical evidence has not been supplied"]),
                False, False)
    try:
        evidence = load_yaml(evidence_path)
    except EnclosureError as exc:
        return check("physical_evidence", "FAIL", 0, len(keys), [str(exc)]), False, False
    findings = []
    expected_top = {"schema", "kind", "config_semantic_sha256", "tests"}
    if set(evidence) != expected_top:
        findings.append(
            "physical evidence fields differ: "
            f"missing={sorted(expected_top - set(evidence))}, "
            f"unknown={sorted(set(evidence) - expected_top)}")
    if evidence.get("schema") != 1 or evidence.get("kind") != PHYSICAL_KIND:
        findings.append("wrong physical-evidence schema/kind")
    if evidence.get("config_semantic_sha256") != config_hash:
        findings.append("physical evidence is stale for this config")
    tests = evidence.get("tests")
    if not isinstance(tests, Mapping):
        findings.append("physical evidence lacks tests mapping")
        tests = {}
    mapping = {
        "insert_coupon_required": "insert_coupon",
        "board_drop_in_required": "board_drop_in",
        "all_interfaces_mated_required": "all_interfaces_mated",
        "thermal_soak_required": "thermal_soak",
    }
    expected_tests = set(mapping.values())
    if set(tests) != expected_tests:
        findings.append(
            "physical test census differs: "
            f"missing={sorted(expected_tests - set(tests))}, "
            f"unknown={sorted(set(tests) - expected_tests)}")
    normalized_tests: dict[str, Mapping[str, Any]] = {}
    for test_name in sorted(expected_tests & set(tests)):
        row = tests[test_name]
        if not isinstance(row, Mapping) or set(row) != {"status", "evidence"}:
            findings.append(
                f"physical test {test_name} must contain status and evidence only")
            continue
        status = row["status"]
        detail = row["evidence"]
        if status not in {"PASS", "FAIL", "NOT_RUN"}:
            findings.append(f"physical test {test_name} has invalid status")
            continue
        if not isinstance(detail, str) or not detail.strip():
            findings.append(f"physical test {test_name} lacks evidence text")
            continue
        normalized_tests[test_name] = row
        # Even an optional test is represented evidence once supplied.  A
        # recorded physical failure must never be hidden by applicability.
        if status == "FAIL":
            findings.append(f"physical test {test_name} records FAIL")
    passed = 0
    pending = 0
    for requirement in keys:
        test_name = mapping[requirement]
        row = normalized_tests.get(test_name)
        if row is None:
            findings.append(f"physical test {test_name} is missing")
            continue
        status = row["status"]
        if status == "PASS":
            passed += 1
        elif status == "NOT_RUN":
            pending += 1
    print_verified = all(normalized_tests.get(mapping[key], {}).get("status") == "PASS"
                         for key in keys if key != "thermal_soak_required")
    thermal_verified = print_verified and (
        not required["thermal_soak_required"] or
        normalized_tests.get("thermal_soak", {}).get("status") == "PASS")
    status = "FAIL" if findings else ("INCOMPLETE" if pending else "PASS")
    return (check("physical_evidence", status,
                  passed, len(keys),
                  [*findings, *([f"{pending} required physical test(s) NOT_RUN"]
                                if pending else [])],
                  evidence_path=str(evidence_path),
                  sha256=sha256_file(evidence_path),
                  size=evidence_path.stat().st_size),
            print_verified, thermal_verified)


def verify(config_path: Path, root: Path, build_dir: Path,
           step_report: Path | None, collision_mesh: Path | None,
           collision_report: Path | None,
           collision_tolerance: float, physical_evidence: Path | None) -> dict[str, Any]:
    config, loaded = load_bound_config(config_path, root)
    config_hash = semantic_sha256(config)
    checks = [
        _subject_check(loaded),
        _interface_check(config, loaded["interface"]),
        _fastener_check(config, loaded["interface"]),
        _mesh_check(config_path, config, loaded["interface"], build_dir),
        _clearance_check(config_path, config, step_report, collision_mesh,
                         collision_report, collision_tolerance),
        _thermal_check(config),
    ]
    physical, print_verified, thermal_verified = _physical_check(
        config, config_hash, physical_evidence)
    checks.append(physical)
    automated = checks[:-1]
    if any(row["status"] == "FAIL" for row in checks):
        status = "FAIL"
    elif any(row["status"] == "INCOMPLETE" for row in automated):
        status = "INCOMPLETE"
    elif thermal_verified:
        status = "THERMALLY_VERIFIED"
    elif print_verified:
        status = "PRINT_VERIFIED"
    else:
        status = "CAD_READY"
    return {
        "schema": 1,
        "kind": "pcb-enclosure-verification-v1",
        "status": status,
        "config": {"path": str(config_path), "raw_sha256": sha256_file(config_path),
                   "semantic_sha256": config_hash},
        "checks": checks,
        "summary": {
            "passed": sum(row["status"] == "PASS" for row in checks),
            "failed": sum(row["status"] == "FAIL" for row in checks),
            "incomplete": sum(row["status"] == "INCOMPLETE" for row in checks),
            "total": len(checks),
        },
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--step-inspection", type=Path)
    parser.add_argument("--collision-mesh", type=Path)
    parser.add_argument("--collision-report", type=Path)
    parser.add_argument("--collision-tolerance-mm3", type=float, default=1e-4)
    parser.add_argument("--physical-evidence", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--target", choices=("cad", "print", "thermal"), default="cad")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        if not math.isfinite(args.collision_tolerance_mm3) or \
                args.collision_tolerance_mm3 < 0:
            raise EnclosureError("collision tolerance must be finite and >= 0")
        expected_report = (args.build_dir / "verification.json").absolute()
        if args.report.absolute() != expected_report:
            raise EnclosureError(
                f"verification report must be the canonical build artifact "
                f"{expected_report}")
        _, preflight = load_bound_config(args.config, args.root)
        protected: list[Path] = [args.config]
        for record in preflight["bindings"].values():
            if isinstance(record, Mapping) and isinstance(record.get("path"), Path):
                protected.append(record["path"])
        protected.extend(path for path in (
            args.step_inspection, args.collision_mesh, args.collision_report,
            args.physical_evidence) if path is not None)
        if args.build_dir.is_dir():
            protected.extend(path for path in args.build_dir.iterdir()
                             if path.is_file() and
                             path.absolute() != expected_report)
        validate_output_path(
            args.report, where="enclosure verification report",
            inputs=protected)
        report = verify(args.config, args.root, args.build_dir,
                        args.step_inspection, args.collision_mesh,
                        args.collision_report,
                        args.collision_tolerance_mm3, args.physical_evidence)
        write_json(
            args.report, report, inputs=protected,
            where="enclosure verification report")
    except (OSError, EnclosureError) as exc:
        print(f"ENCLOSURE VERIFICATION FAIL — input: {args.config}: 0/1 input valid — {exc}",
              file=sys.stderr)
        return 1
    for row in report["checks"]:
        suffix = (" — " + "; ".join(row["findings"])) if row["findings"] else ""
        print(f"{row['name']}: {row['status']} {row['graded']}/{row['total']}{suffix}")
    summary = report["summary"]
    print(
        f"ENCLOSURE VERDICT {report['status']} — input: {args.config} — "
        f"{summary['passed']}/{summary['total']} checks PASS, "
        f"{summary['failed']} FAIL, {summary['incomplete']} INCOMPLETE")
    print(f"wrote {args.report}")
    ranks = {"FAIL": 0, "INCOMPLETE": 0, "CAD_READY": 1,
             "PRINT_VERIFIED": 2, "THERMALLY_VERIFIED": 3}
    target_rank = {"cad": 1, "print": 2, "thermal": 3}[args.target]
    if report["status"] == "FAIL":
        return 1
    return 0 if ranks[report["status"]] >= target_rank else 2


if __name__ == "__main__":
    sys.exit(main())
