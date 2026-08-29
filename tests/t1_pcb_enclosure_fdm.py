#!/usr/bin/env python3
"""FDM structural contract, mesh-section probes, replay, and fleet policy."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
import shutil
import sys
from pathlib import Path

import yaml

from harness import check, contains, eq, main, must_fail, run, test, tmpdir


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills/pcb-enclosure/scripts/fdm_structural_audit.py"
FLEET = ROOT / "skills/pcb-enclosure/scripts/fdm_audit_fleet.py"
GENERATOR = ROOT / "skills/pcb-enclosure/scripts/generate_enclosure.py"
V2_PATH = ROOT / "skills/pcb-enclosure/scripts/enclosure_v2.py"
KPY = "/usr/bin/python3"

sys.path.insert(0, str(SCRIPT.parent))
import fdm_structural_audit as fdm  # noqa: E402
import build_collision as collision_builder  # noqa: E402
import enclosure_v2 as v2  # noqa: E402
import verify_enclosure_release as release_verify  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding(root: Path, path: Path) -> dict:
    return {"path": path.relative_to(root).as_posix(), "sha256": _sha(path),
            "size": path.stat().st_size}


def _write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _scad_mesh(root: Path, geometry: str) -> tuple[Path, Path]:
    source = root / "case.scad"
    mesh = root / "lid.stl"
    source.write_text(geometry, encoding="utf-8")
    result = run(["/usr/bin/openscad", "-o", mesh, source])
    check(result.rc == 0, result.out)
    return source, mesh


def _fixture(*, reinforced: bool = True) -> dict:
    root = tmpdir("enclosure-fdm-")
    if reinforced:
        geometry = (
            "$fn=64; union(){"
            "translate([-20,-15,0]) cube([40,30,2.4]);"
            "translate([12,8,0]) cube([14,10,8]);}\n")
    else:
        # Pluto-v0.7-style corner condition: a circular closure member centered
        # outside both roof edges with only a shallow corner intersection.
        geometry = (
            "$fn=128; union(){"
            "translate([-20,-15,0]) cube([40,30,2.4]);"
            "translate([24,19,0]) cylinder(h=8,r=7);}\n")
    source, lid_mesh = _scad_mesh(root, geometry)
    base_mesh = root / "base.stl"
    coupon_mesh = root / "insert_coupon.stl"
    installed_case_mesh = root / "assembled-case.stl"
    component_mesh = root / "step-components.stl"
    shutil.copyfile(lid_mesh, base_mesh)
    shutil.copyfile(lid_mesh, coupon_mesh)
    shutil.copyfile(lid_mesh, installed_case_mesh)
    shutil.copyfile(lid_mesh, component_mesh)
    subject = root / "subject"
    subject.mkdir()
    pcb = subject / "board.kicad_pcb"
    step = subject / "board.step"
    interface = subject / "board-interface.json"
    manifest = subject / "MANIFEST.txt"
    pcb.write_text("(kicad_pcb (version 20240108))\n", encoding="utf-8")
    step.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
    collision_step = root / step.name
    shutil.copyfile(step, collision_step)
    holes = [
        {"ref": ref, "pad": "", "position_mm": position,
         "drill_mm": [3.2, 3.2], "attribute": "NPTH"}
        for ref, position in (("H1", [-25.0, -15.0]),
                              ("H2", [25.0, -15.0]),
                              ("H3", [-25.0, 15.0]),
                              ("H4", [25.0, 15.0]))
    ]
    footprints = [
        {"ref": row["ref"], "value": row["ref"],
         "footprint": "Synthetic_" + row["ref"],
         "position_mm": row["position_mm"], "rotation_deg": 0.0,
         "side": "front",
         "bbox_mm": [row["position_mm"][0] - 2,
                     row["position_mm"][1] - 2,
                     row["position_mm"][0] + 2,
                     row["position_mm"][1] + 2],
         "model_declared": False}
        for row in holes
    ] + [{"ref": "J1", "value": "J1", "footprint": "Synthetic_J1",
          "position_mm": [0.0, -18.0], "rotation_deg": 0.0,
          "side": "front", "bbox_mm": [-2.0, -20.0, 2.0, -16.0],
          "model_declared": True}]
    interface_value = {
        "schema": 1, "kind": "pcb-enclosure-interface-v1",
        "subject": {"board": {"name": pcb.name, "sha256": _sha(pcb),
                                 "size": pcb.stat().st_size}},
        "frame": {"units": "mm", "origin": "outline_bbox_center",
                  "board_to_case": [[1, 0, 0, 0], [0, 1, 0, 0],
                                    [0, 0, 1, 0], [0, 0, 0, 1]],
                  "z_zero": "pcb_back_surface", "z_positive": "front"},
        "board": {
            "thickness_mm": 1.6,
            "outline": {"contours_mm": [[[-30, -20], [30, -20],
                                           [30, 20], [-30, 20]]],
                        "bbox_mm": [-30, -20, 30, 20],
                        "size_mm": [60, 40]},
            "drills": holes, "mounting_holes": holes,
            "footprints": footprints,
            "access_candidates": [{"ref": "J1",
                                    "position_mm": [0.0, -18.0],
                                    "value": "J1",
                                    "footprint": "Synthetic_J1",
                                    "selection": "required"}],
        },
        "coverage": {"footprints": len(footprints), "drills": 4,
                     "mounting_holes": 4, "access_candidates": 1},
    }
    interface.write_text(json.dumps(interface_value, indent=2) + "\n",
                         encoding="utf-8")
    collision_interface = root / interface.name
    shutil.copyfile(interface, collision_interface)
    manifest.write_text(
        f"{_sha(pcb)}  board.kicad_pcb\n{_sha(step)}  board.step\n",
        encoding="utf-8")
    config = {
        "schema": 1, "kind": "pcb-enclosure-config-v1",
        "name": "synthetic-fdm-enclosure", "mode": "derived",
        "subject": {
            "release": "v1.0.0-test",
            "release_manifest": _binding(root, manifest),
            "pcb": _binding(root, pcb), "step": _binding(root, step),
            "interface": _binding(root, interface),
        },
        "process": {"method": "fdm", "material": "PETG", "nozzle_mm": 0.4,
                    "layer_mm": 0.2, "support_policy": "forbid_when_practical",
                    "minimum_wall_mm": 1.2},
        "cad": {"engine": "openscad", "minimum_version": "2021.01",
                "printable_parts": ["base", "lid", "insert_coupon"],
                "source": {"kind": "authored_scad", **_binding(root, source)}},
        "geometry": {"topology": "split_shell", "xy_clearance_mm": 1.0,
                     "wall_mm": 2.4, "floor_mm": 2.4, "roof_mm": 2.4,
                     "corner_radius_mm": 4.0, "board_bottom_z_mm": 8.0,
                     "inside_top_z_mm": 20.0, "seam_z_mm": 15.0,
                     "panel_thickness_mm": 2.4, "panel_capture_mm": 1.2,
                     "panel_clearance_mm": 0.25, "corner_post_mm": 8.0,
                     "lid_column_board_gap_mm": 0.2},
        "fasteners": {
            "strategy": "separate_perimeter", "thread": "M3-0.5",
            "board_holes": ["H1", "H2", "H3", "H4"],
            "case_holes_mm": [[-25, -20], [25, -20], [-25, 20], [25, 20]],
            "boss_d_mm": 8.0, "case_post_d_mm": 9.0,
            "minimum_radial_wall_mm": 0.8,
            "insert": {"family": "fixture-M3", "installation": "cold_press",
                       "hole_d_mm": 4.0, "body_d_mm": 4.2,
                       "flange_d_mm": 5.5, "flange_recess_d_mm": 6.0,
                       "flange_recess_depth_mm": 0.8, "length_mm": 4.0,
                       "bottom_clearance_mm": 0.2},
            "screw": {"clearance_d_mm": 3.4, "head_d_mm": 6.0,
                      "head_recess_depth_mm": 1.0, "board_length_mm": 6.0,
                      "lid_length_mm": 8.0, "minimum_engagement_mm": 3.0,
                      "minimum_tip_clearance_mm": 0.5}},
        "interfaces": [{"id": "internal", "ref": "J1", "role": "internal",
                        "side": "north", "disposition": "internal",
                        "center_mm": [0, 0, 0], "shape": "none",
                        "opening_mm": [0, 0], "plug_envelope_mm": [0, 0, 0],
                        "clearance_mm": 0}],
        "thermal": {"risk": "low", "physical_soak_required": False,
                    "load_case": "fixture", "vents": []},
        "physical_validation": {"insert_coupon_required": True,
                                "board_drop_in_required": True,
                                "all_interfaces_mated_required": True,
                                "thermal_soak_required": False},
    }
    config_path = root / "enclosure.yaml"
    _write_yaml(config_path, config)
    installed_case = {
        "path": installed_case_mesh.name,
        "sha256": _sha(installed_case_mesh),
        "size": installed_case_mesh.stat().st_size,
        "selector": "installed_case",
        "command": ["/usr/bin/openscad", "-o", installed_case_mesh.name,
                    "-D", 'part="installed_case"', "-D",
                    "show_reference_board=false", source.name],
    }
    generation = {
        "schema": 1, "kind": "pcb-enclosure-generation-v1",
        "config": {"path": "enclosure.yaml",
                   "semantic_sha256": fdm.semantic_sha256(config),
                   "raw_sha256": _sha(config_path)},
        "authority": {"kind": "authored_scad", "binding": {
            key: config["cad"]["source"][key]
            for key in ("path", "sha256", "size")}},
        "engine": {"executable": "/usr/bin/openscad"},
        "source": {"path": source.name, "sha256": _sha(source),
                   "size": source.stat().st_size},
        "parts": [{"part": part, "path": f"{part}.stl", "sha256": _sha(path),
                   "size": path.stat().st_size}
                  for part, path in (("base", base_mesh), ("lid", lid_mesh),
                                     ("insert_coupon", coupon_mesh))],
        "installed_case": installed_case,
    }
    generation_path = root / "generation.json"
    generation_path.write_text(json.dumps(generation, indent=2) + "\n")
    inspection_path = root / "step-inspection.json"
    inspection_path.write_text(json.dumps({
        "schema": 1, "kind": "pcb-enclosure-step-inspection-v1",
        "status": "COMPLETE",
        "step": {"path": collision_step.name, "sha256": _sha(collision_step),
                 "size": collision_step.stat().st_size},
        "interface": {"path": collision_interface.name,
                      "sha256": _sha(collision_interface),
                      "size": collision_interface.stat().st_size},
        "geometry": {
            "status": "COMPLETE",
            "component_mesh": {
                "path": component_mesh.name, "sha256": _sha(component_mesh),
                "size": component_mesh.stat().st_size,
            },
            "case_registration_translate_mm_at_board_z0": [0, 0, 0],
            "solid_count": 2, "pcb_related_solid_indices": [0],
            "component_solid_count": 1,
        },
    }, indent=2) + "\n")
    collision_mesh = root / "clearance-intersection.stl"
    collision_builder._empty_marker(collision_mesh)
    collision_metrics = collision_builder.stl_metrics(collision_mesh)
    collision_metrics["path"] = collision_mesh.name
    collision_path = root / "collision.json"
    collision_path.write_text(json.dumps({
        "schema": 1, "kind": "pcb-enclosure-collision-v1",
        "status": "COMPLETE",
        "builder": {
            "path": collision_builder.COLLISION_BUILDER_SOURCE_PATH,
            "sha256": _sha(Path(collision_builder.__file__)),
            "size": Path(collision_builder.__file__).stat().st_size,
        },
        "enclosure_common": {
            "path": collision_builder.ENCLOSURE_COMMON_SOURCE_PATH,
            "sha256": _sha(Path(collision_builder.__file__).with_name(
                "enclosure_common.py")),
            "size": Path(collision_builder.__file__).with_name(
                "enclosure_common.py").stat().st_size,
        },
        "step_inspector": {
            "path": collision_builder.STEP_INSPECTOR_SOURCE_PATH,
            "sha256": _sha(Path(collision_builder.__file__).with_name(
                "inspect_step.py")),
            "size": Path(collision_builder.__file__).with_name(
                "inspect_step.py").stat().st_size,
        },
        "process_runner": {
            "path": collision_builder.PROCESS_RUNNER_SOURCE_PATH,
            "sha256": _sha(ROOT / collision_builder.PROCESS_RUNNER_SOURCE_PATH),
            "size": (ROOT / collision_builder.PROCESS_RUNNER_SOURCE_PATH)
                .stat().st_size,
        },
        "pipeline_runtime": {
            "path": collision_builder.PIPELINE_RUNTIME_SOURCE_PATH,
            "sha256": _sha(ROOT / collision_builder.PIPELINE_RUNTIME_SOURCE_PATH),
            "size": (ROOT / collision_builder.PIPELINE_RUNTIME_SOURCE_PATH)
                .stat().st_size,
        },
        "backend": {"name": "cadquery-ocp-brep-common",
                    "cadquery_version": "2.8.0", "ocp_version": "7.9.3.1"},
        "inputs": {
            "step_inspection": {
                "path": inspection_path.name, "sha256": _sha(inspection_path),
                "size": inspection_path.stat().st_size,
            },
            "step": {"path": collision_step.name,
                     "sha256": _sha(collision_step),
                     "size": collision_step.stat().st_size},
            "component_mesh": {
                "path": component_mesh.name, "sha256": _sha(component_mesh),
                "size": component_mesh.stat().st_size,
            },
            "interface": {
                "path": collision_interface.name,
                "sha256": _sha(collision_interface),
                "size": collision_interface.stat().st_size,
            },
            "generation": {
                "path": generation_path.name, "sha256": _sha(generation_path),
                "size": generation_path.stat().st_size,
            },
            "assembled_case_mesh": installed_case,
        },
        "transform": {
            "case_registration_translate_mm_at_board_z0": [0, 0, 0],
            "board_bottom_z_mm": 8.0,
            "applied_component_translate_mm": [0, 0, 8.0],
        },
        "selection": {"step_solid_count": 2,
                      "pcb_related_solid_count": 1,
                      "component_solid_count": 1},
        "result": {
            "classification": "EMPTY", "exact_brep_volume_mm3": 0,
            "representation": "zero-area-marker-for-empty-brep",
            "collision_mesh": {
                "path": collision_mesh.name, "sha256": _sha(collision_mesh),
                "size": collision_mesh.stat().st_size,
            },
            "mesh_metrics": collision_metrics,
        },
    }, indent=2) + "\n")

    def synthetic_process(command, *, cwd):
        receipt_arg = ("--replay-receipt" if "--replay-receipt" in command
                       else "--validate-receipt")
        collision_builder.validate_collision_receipt(
            Path(command[command.index(receipt_arg) + 1]))

    v2._COLLISION_PROCESS_RUNNER = synthetic_process
    identity = [[1, 0, 0, 0], [0, 1, 0, 0],
                [0, 0, 1, 0], [0, 0, 0, 1]]
    config = yaml.safe_load(config_path.read_text())
    contract = {
        "schema": 1, "kind": fdm.CONTRACT_KIND, "name": config["name"],
        "design_fingerprint": fdm.design_fingerprint(config),
        "process_profiles": [{"id": "production", **config["process"],
                              "slicer": None}],
        "parts": [
            {"id": "base", "process_profile": "production",
             "mesh_to_build": identity,
             "structural_disposition": "no_critical_attachment",
             "structural_reason": "Fixture base reuses mesh; no installed joint.",
             "attachment_ids": [], "support_exception_ids": []},
            {"id": "lid", "process_profile": "production",
             "mesh_to_build": identity, "structural_disposition": "audited",
             "structural_reason": None, "attachment_ids": ["closure_root"],
             "support_exception_ids": []},
            {"id": "insert_coupon", "process_profile": "production",
             "mesh_to_build": identity,
             "structural_disposition": "no_critical_attachment",
             "structural_reason": "Standalone process coupon.",
             "attachment_ids": [], "support_exception_ids": []},
        ],
        "load_cases": [{"id": "lid_handling", "description": "Fixture load",
                        "direction_local": [0, 0, 1],
                        "application": "Applied at closure member",
                        "reaction": "Reacted into roof"}],
        "attachments": [{
            "id": "closure_root", "part": "lid", "scope": "shell",
            "host": "roof", "member": "closure member",
            "function": "transfer handling load", "load_cases": ["lid_handling"],
            "root_sections": [
                {"id": "root", "plane": {"origin_mm": [19.5, 0, 0],
                                            "normal": [1, 0, 0],
                                            "u_axis": [0, 1, 0]},
                 "roi_uv_mm": [7, -0.1, 19, 8.1], "minimum_area_mm2": 50,
                 "throat": {"axis": "u", "coordinate_mm": 4,
                            "interval_mm": [7, 19],
                            "minimum_material_span_mm": 8}},
                {"id": "member", "plane": {"origin_mm": [24, 0, 0],
                                              "normal": [1, 0, 0],
                                              "u_axis": [0, 1, 0]},
                 "roi_uv_mm": [7, -0.1, 19, 8.1], "minimum_area_mm2": 50,
                 "throat": {"axis": "u", "coordinate_mm": 4,
                            "interval_mm": [7, 19],
                            "minimum_material_span_mm": 6}},
            ],
            "reinforcement": {"kind": "continuous_section",
                              "root_section": "root",
                              "member_section": "member",
                              "minimum_area_ratio": 0.9},
            "overlap": {"disposition": "section_proved",
                        "section_id": "root", "reason": None},
            "exception_id": None,
        }],
        "support_exceptions": [], "flexure_exceptions": [],
    }
    contract_path = root / "fdm-contract.yaml"
    _write_yaml(contract_path, contract)
    return {"root": root, "config": config_path, "contract": contract_path,
            "generation": generation_path, "collision": collision_path,
            "source": source,
            "collision_mesh": collision_mesh,
            "collision_step": collision_step,
            "step_inspection": inspection_path,
            "component_mesh": component_mesh,
            "collision_interface": collision_interface,
            "installed_case": installed_case_mesh,
            "meshes": {"base": base_mesh, "lid": lid_mesh,
                       "insert_coupon": coupon_mesh},
            "output": root / "fdm-audit.json"}


def _command(fixture: dict) -> list:
    command = [KPY, SCRIPT, fixture["contract"], "--config", fixture["config"],
               "--root", fixture["root"], "--generation", fixture["generation"]]
    for part, path in fixture["meshes"].items():
        command.extend(["--mesh", f"{part}={path}"])
    return [*command, "--output", fixture["output"]]


def _manufacturing_value(fixture: dict) -> dict:
    return {
        "contract": _binding(fixture["root"], fixture["contract"]),
        "receipt": _binding(fixture["root"], fixture["output"]),
        "generation": _binding(fixture["root"], fixture["generation"]),
        "collision": _binding(fixture["root"], fixture["collision"]),
        "collision_subject": {"mode": "subject_step"},
        "meshes": [{"part": part, **_binding(fixture["root"], path)}
                   for part, path in fixture["meshes"].items()],
    }


def _bound_manufacturing_fixture() -> tuple[dict, dict, dict]:
    fixture = _fixture()
    receipt = fdm.audit_paths(
        fixture["contract"], fixture["config"], fixture["generation"],
        fixture["meshes"], root=fixture["root"])
    fixture["output"].write_text(json.dumps(receipt, indent=2) + "\n")
    return fixture, receipt, _manufacturing_value(fixture)


def _manufacturing_validation_report_fixture() -> tuple[dict, dict, dict, dict]:
    fixture, _, value = _bound_manufacturing_fixture()
    cad_design = yaml.safe_load(fixture["config"].read_text())
    manufacturing = v2._validate_manufacturing_audit(
        value, fixture["root"], fixture["config"], cad_design,
        {"shell": {"required": True}}, {})
    raw = {"schema": 2, "kind": "synthetic-report-authority"}
    loaded = {
        "cad_design": {"interfaces": []},
        "bindings": {"manufacturing_audit": manufacturing["bindings"]},
        "scope_readiness_ceilings": {"shell": "INCOMPLETE"},
        "service_envelopes": {}, "interface_assemblies": {},
    }
    report = v2.config_validation_report(raw, loaded, fixture["root"])
    return fixture, raw, loaded, report


def _stale_validation_binding_bites(field: str) -> None:
    fixture, raw, loaded, report = _manufacturing_validation_report_fixture()
    stale = copy.deepcopy(report)
    stale["bindings"]["manufacturing_audit"][field]["sha256"] = "0" * 64
    try:
        v2.validate_config_validation_report(
            stale, raw, loaded, fixture["root"])
    except v2.V2Error as exc:
        contains(str(exc), "differs from the canonical fresh regrade")
        return
    check(False, f"stale validation {field} binding unexpectedly passed")


@test("exact collision receipt independently replays with pinned CadQuery")
def t_real_collision_replay_canary():
    root = tmpdir("collision-replay-canary-")
    uv = shutil.which("uv")
    check(uv is not None, "uv is required for exact collision replay")
    interface_fixture = _fixture()
    interface = root / "board-interface.json"
    shutil.copyfile(interface_fixture["collision_interface"], interface)
    step = root / "board.step"
    make_step = run([
        uv, "run", "--offline", "--with", "cadquery==2.8.0", "python",
        "-B", "-c",
        ("import cadquery as cq; "
         "b=cq.Workplane('XY').box(60,40,1.6).translate((0,0,0.8)).val(); "
         "c=cq.Workplane('XY').box(2,2,2).translate((0,0,3)).val(); "
         f"cq.exporters.export(cq.Compound.makeCompound([b,c]), {str(step)!r})"),
    ])
    check(make_step.rc == 0, make_step.out)
    source = root / "enclosure.scad"
    source.write_text("translate([100,0,0]) cube([2,2,2]);\n")
    case = root / "assembled-case.stl"
    component = root / "step-components.stl"
    generated = run(["/usr/bin/openscad", "-o", case, source])
    check(generated.rc == 0, generated.out)
    generation = root / "generation.json"
    installed = {
        "path": case.name, "sha256": _sha(case), "size": case.stat().st_size,
        "selector": "installed_case",
        "command": ["/usr/bin/openscad", "-o", case.name, "-D",
                    'part="installed_case"', "-D",
                    "show_reference_board=false", source.name],
    }
    generation.write_text(json.dumps({
        "schema": 1, "kind": "pcb-enclosure-generation-v1",
        "engine": {"executable": "/usr/bin/openscad"},
        "source": {"path": source.name, "sha256": _sha(source),
                   "size": source.stat().st_size},
        "installed_case": installed,
    }) + "\n")
    geometry_report = root / "step-geometry.json"
    inspected = run([
        uv, "run", "--offline", "--with", "cadquery==2.8.0", "python",
        "-B", Path(collision_builder.__file__).with_name("inspect_step.py"),
        step, "--interface", interface, "--output", geometry_report,
        "--component-mesh", component, "--geometry-only",
    ], timeout=180)
    check(inspected.rc == 0, inspected.out)
    geometry_value = json.loads(geometry_report.read_text())
    inspection = root / "step-inspection.json"
    inspection.write_text(json.dumps({
        "schema": 1, "kind": "pcb-enclosure-step-inspection-v1",
        "status": "COMPLETE",
        "step": geometry_value["step"],
        "interface": geometry_value["interface"],
        "occurrence_coverage": {"status": "COMPLETE"},
        "geometry": geometry_value["geometry"],
    }) + "\n")
    collision_mesh = root / "clearance-intersection.stl"
    report = root / "collision.json"
    built = run([
        uv, "run", "--offline", "--with", "cadquery==2.8.0", "python",
        "-B", Path(collision_builder.__file__),
        "--step", step, "--step-inspection", inspection,
        "--component-mesh", component, "--interface", interface,
        "--generation", generation,
        "--assembled-case-mesh", case, "--board-bottom-z-mm", "0",
        "--output", collision_mesh, "--report", report,
    ], timeout=180)
    check(built.rc == 0, built.out)
    replayed = collision_builder.replay_collision_receipt(report)
    eq(replayed, json.loads(report.read_text()))
    eq(replayed["result"]["classification"], "EMPTY")


@test("reinforced attachment passes the mesh-visible structural screen")
def t_reinforced_fixture():
    fixture = _fixture(reinforced=True)
    result = run(_command(fixture))
    eq(result.rc, 2, "honest missing-slicer exit")
    receipt = json.loads(fixture["output"].read_text())
    eq(receipt["status"], "INCOMPLETE")
    eq(receipt["domains"]["structural_load_path_screen"]["status"], "PASS")
    eq(receipt["domains"]["slicer_toolpath_evidence"]["status"], "INCOMPLETE")
    eq(receipt["maximum_claim"], "CAD_READY")
    check(receipt["physical_evidence_consumed"] is False,
          "physical evidence boundary")


@test("Pluto-style shallow circular corner lug fails root/throat screen",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_shallow_corner_lug_bites():
    fixture = _fixture(reinforced=False)
    result = must_fail(run(_command(fixture)), "shallow corner lug")
    receipt = json.loads(fixture["output"].read_text())
    eq(receipt["status"], "FAIL")
    eq(receipt["domains"]["structural_load_path_screen"]["status"], "FAIL")
    contains(result.out, "FDM STRUCTURAL AUDIT FAIL")


@test("off-mesh section probe records its contour failure without crashing",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_off_mesh_section_probe_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    contract["attachments"][0]["root_sections"][0]["plane"]["origin_mm"] = \
        [1000, 0, 0]
    _write_yaml(fixture["contract"], contract)
    result = must_fail(run(_command(fixture)), "off-mesh section probe")
    receipt = json.loads(fixture["output"].read_text())
    eq(receipt["status"], "FAIL")
    contains("\n".join(receipt["findings"]), "zero mesh intersection")
    check("UnboundLocalError" not in result.out,
          "probe failure escaped as an uninitialised-local compiler crash")


@test("mesh-to-build refuses scale, shear, reflection, and zero transforms",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_nonrigid_transform_bites():
    fixture = _fixture()
    base = yaml.safe_load(fixture["contract"].read_text())
    bad_matrices = [
        [[2, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        [[1, .2, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        [[0, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
    ]
    config = yaml.safe_load(fixture["config"].read_text())
    for matrix in bad_matrices:
        contract = copy.deepcopy(base)
        next(row for row in contract["parts"] if row["id"] == "lid") \
            ["mesh_to_build"] = matrix
        try:
            fdm.validate_contract(contract, config)
        except fdm.AuditError:
            continue
        check(False, f"nonrigid transform unexpectedly passed: {matrix}")


@test("root and member reinforcement witnesses must be independently distinct",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_same_probe_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    attachment = contract["attachments"][0]
    attachment["root_sections"][1] = copy.deepcopy(
        attachment["root_sections"][0])
    attachment["root_sections"][1]["id"] = "member"
    try:
        fdm.validate_contract(
            contract, yaml.safe_load(fixture["config"].read_text()))
    except fdm.AuditError as exc:
        contains(str(exc), "semantically identical")
        return
    check(False, "identical root/member probes unexpectedly passed")


@test("shifted probes through one straight member cannot masquerade as a root",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_indistinguishable_measured_sections_bite():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    attachment = contract["attachments"][0]
    attachment["root_sections"][0]["plane"]["origin_mm"] = [21.0, 0, 0]
    attachment["root_sections"][1]["plane"]["origin_mm"] = [22.0, 0, 0]
    _write_yaml(fixture["contract"], contract)
    result = must_fail(run(_command(fixture)), "same measured member")
    receipt = json.loads(fixture["output"].read_text())
    findings = "\n".join(receipt["findings"])
    contains(findings,
             "attachment-to-host transition is not independently witnessed")
    check("area ratio 1 < 0.9" not in findings,
          "indistinguishable sections fabricated a false ratio failure")
    contains(result.out, "FDM STRUCTURAL AUDIT FAIL")


@test("sub-resolution shifted planes cannot witness independent root/member",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_subresolution_shifted_taper_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    attachment = contract["attachments"][0]
    attachment["root_sections"][1]["plane"]["origin_mm"] = [19.51, 0, 0]
    _write_yaml(fixture["contract"], contract)
    result = must_fail(run(_command(fixture)), "sub-resolution shifted taper")
    contains(result.out, "signed normal separation is only 0.01 mm")
    contains(result.out, "process-resolution step (0.2 mm)")


@test("parallel probes reject tangential-only origin displacement",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_tangential_plane_shift_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    attachment = contract["attachments"][0]
    attachment["root_sections"][1]["plane"]["origin_mm"] = [19.5, 0, 0.2]
    try:
        fdm.validate_contract(
            contract, yaml.safe_load(fixture["config"].read_text()))
    except fdm.AuditError as exc:
        contains(str(exc), "0.2 mm tangential offset")
        contains(str(exc), "no tangential displacement")
        return
    check(False, "same geometric plane shifted tangentially unexpectedly passed")


@test("a tiny plane tilt is not a nonparallel root/member witness",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_tiny_plane_angle_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    member = contract["attachments"][0]["root_sections"][1]["plane"]
    angle = 5.0 * math.pi / 180.0
    member["normal"] = [math.cos(angle), 0, math.sin(angle)]
    member["u_axis"] = [0, 1, 0]
    try:
        fdm.validate_contract(
            contract, yaml.safe_load(fixture["config"].read_text()))
    except fdm.AuditError as exc:
        contains(str(exc), "plane angle is only 5")
        contains(str(exc), "at least 30 degrees")
        return
    check(False, "five-degree probe tilt unexpectedly passed")


@test("sub-process taper output cannot establish section independence",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_process_scaled_material_delta_bites():
    fixture = _fixture()
    original_loops = fdm._section_loops
    original_area = fdm._section_area
    original_span = fdm._material_span
    areas = iter((140.00504, 140.00532))
    spans = iter((14.000504, 14.000532))
    fdm._section_loops = lambda triangles, plane: []
    fdm._section_area = lambda loops, roi: next(areas)
    fdm._material_span = lambda loops, **kwargs: next(spans)
    try:
        receipt = fdm.audit_paths(
            fixture["contract"], fixture["config"], fixture["generation"],
            fixture["meshes"], root=fixture["root"])
    finally:
        fdm._section_loops = original_loops
        fdm._section_area = original_area
        fdm._material_span = original_span
    eq(receipt["domains"]["structural_load_path_screen"]["status"], "FAIL")
    findings = "\n".join(receipt["findings"])
    contains(findings, "sub-process material change")
    contains(findings, "0.00028 mm^2 < 0.08 mm^2")
    contains(findings, "2.8e-05 mm < 0.2 mm")


@test("printable orientation refuses floating and below-bed transforms",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_build_plate_bites():
    for z in (-1.0, 1.0):
        fixture = _fixture()
        contract = yaml.safe_load(fixture["contract"].read_text())
        for part in contract["parts"]:
            part["mesh_to_build"][2][3] = z
        _write_yaml(fixture["contract"], contract)
        result = must_fail(run(_command(fixture)), f"build Z {z}")
        receipt = json.loads(fixture["output"].read_text())
        eq(receipt["domains"]["orientation_and_process_contract"]["status"],
           "FAIL")
        contains("\n".join(receipt["findings"]),
                 "below Z=0" if z < 0 else "floats")
        contains(result.out, "FDM STRUCTURAL AUDIT FAIL")


@test("generation/mesh binding drift is a hard failure",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_stale_mesh_bites():
    fixture = _fixture()
    generation = json.loads(fixture["generation"].read_text())
    generation["parts"][0]["sha256"] = "0" * 64
    fixture["generation"].write_text(json.dumps(generation) + "\n")
    must_fail(run(_command(fixture)), "stale generation mesh", "differs")


@test("generation receipt is byte-stable across disposable build directories")
def t_generation_receipt_relocates():
    fixture = _fixture()
    receipts = []
    for name in ("replay-a", "replay-b"):
        build = fixture["root"] / name
        result = run([KPY, GENERATOR, fixture["config"], "--root",
                      fixture["root"], "--build-dir", build])
        eq(result.rc, 0, f"generation in {name}")
        receipts.append((build / "generation.json").read_bytes())
    eq(receipts[0], receipts[1], "generation receipt byte replay")


@test("generation config path and bytes are exact audit inputs",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_stale_generation_config_bites():
    for field, value in (("path", "some/other/config.yaml"),
                         ("raw_sha256", "0" * 64),
                         ("semantic_sha256", "0" * 64)):
        fixture = _fixture()
        generation = json.loads(fixture["generation"].read_text())
        generation["config"][field] = value
        fixture["generation"].write_text(json.dumps(generation) + "\n")
        must_fail(run(_command(fixture)), f"stale generation config {field}",
                  "generation config identity differs")


@test("strict v1 validator rejects extra CAD config fields",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_malformed_v1_bites():
    fixture = _fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["unreviewed_escape_hatch"] = True
    _write_yaml(fixture["config"], config)
    must_fail(run(_command(fixture)), "extra v1 config field", "unknown")


@test("zero structural denominator cannot certify no-joint printables",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_zero_attachment_denominator_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    contract["attachments"] = []
    lid = next(row for row in contract["parts"] if row["id"] == "lid")
    lid.update({"structural_disposition": "no_critical_attachment",
                "structural_reason": "Attempted vacuous declaration",
                "attachment_ids": []})
    _write_yaml(fixture["contract"], contract)
    must_fail(run(_command(fixture)), "zero attachment denominator",
              "denominator is zero")


@test("every declared load case must reach at least one attachment",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_unused_load_case_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    contract["load_cases"].append({
        "id": "decorative_unreacted_load",
        "description": "Attempted denominator inflation without a load path.",
        "direction_local": [1, 0, 0],
        "application": "Applied nowhere in the attachment census.",
        "reaction": "Reacted nowhere in the attachment census.",
    })
    _write_yaml(fixture["contract"], contract)
    must_fail(run(_command(fixture)), "unused load case",
              "load-case census differs from attachment references")


@test("post-publication regrade removes only its own stale output inode",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_post_publish_regrade_bites():
    root = tmpdir("fdm-publish-")
    protected = root / "input.txt"
    protected.write_text("stable\n")
    output = root / "receipt.json"
    calls = 0

    def regrade():
        nonlocal calls
        calls += 1
        return {"status": "INCOMPLETE" if calls == 1 else "FAIL"}

    try:
        fdm.write_json(output, {"status": "INCOMPLETE"},
                       inputs=[protected], regrade=regrade)
    except fdm.AuditError as exc:
        contains(str(exc), "removed only")
    else:
        check(False, "drifting post-publication regrade unexpectedly passed")
    check(not output.exists(), "writer left its stale published inode")


@test("post-publication audit detects contract, config, and mesh drift",
      kind="known_bad", gate="fdm_structural_audit.py")
def t_named_input_drift_bites():
    for name in ("contract.yaml", "config.yaml", "lid.stl"):
        root = tmpdir("fdm-input-drift-")
        subjects = [root / item for item in
                    ("contract.yaml", "config.yaml", "lid.stl")]
        for subject in subjects:
            subject.write_text("A\n")
        target = root / name
        output = root / "receipt.json"
        calls = 0

        def regrade():
            nonlocal calls
            calls += 1
            if calls == 2:
                target.write_text("B\n")
                return {"status": "FAIL"}
            return {"status": "INCOMPLETE"}
        try:
            fdm.write_json(output, {"status": "INCOMPLETE"},
                           inputs=subjects, regrade=regrade)
        except fdm.AuditError:
            pass
        else:
            check(False, f"{name} drift unexpectedly published")
        check(not output.exists(), f"{name} drift left stale output")


@test("v2 independently regrades a bound manufacturing audit")
def t_v2_manufacturing_regrade():
    fixture, receipt, value = _bound_manufacturing_fixture()
    result = v2._validate_manufacturing_audit(
        value, fixture["root"], fixture["config"],
        yaml.safe_load(fixture["config"].read_text()),
        {"shell": {"required": True}}, {})
    eq(result["status"], "INCOMPLETE")
    eq(result["receipt"], receipt)
    eq(result["bindings"]["collision"]["path"], fixture["collision"])


@test("v2 validation rejects a stale FDM compiler binding",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_v2_validation_stale_fdm_compiler_bites():
    _stale_validation_binding_bites("compiler")


@test("v2 validation rejects a stale FDM contract binding",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_v2_validation_stale_fdm_contract_bites():
    _stale_validation_binding_bites("contract")


@test("v2 validation rejects a stale schema helper binding",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_v2_validation_stale_fdm_helper_bites():
    _stale_validation_binding_bites("enclosure_common")


@test("v2 validation rejects a stale FDM receipt binding",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_v2_validation_stale_fdm_receipt_bites():
    _stale_validation_binding_bites("receipt")


@test("v2 validation reports cannot retain temporary absolute paths",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_v2_validation_absolute_temp_path_bites():
    fixture, raw, loaded, report = _manufacturing_validation_report_fixture()
    stale = copy.deepcopy(report)
    stale["bindings"]["manufacturing_audit"]["receipt"]["path"] = \
        "/tmp/stale-build/fdm-audit.json"
    try:
        v2.validate_config_validation_report(
            stale, raw, loaded, fixture["root"])
    except v2.V2Error as exc:
        contains(str(exc), "differs from the canonical fresh regrade")
        return
    check(False, "absolute temporary report path unexpectedly passed")


@test("declared manufacturing audit requires an exact collision binding",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_missing_collision_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    value.pop("collision")
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "missing=['collision']")
        return
    check(False, "manufacturing audit without collision unexpectedly passed")


@test("declared manufacturing audit requires an explicit collision subject",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_missing_collision_subject_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    value.pop("collision_subject")
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "missing=['collision_subject']")
        return
    check(False, "manufacturing audit without collision subject passed")


@test("hand-written minimal COMPLETE/EMPTY collision is not authority",
      kind="known_bad", gate="build_collision.py")
def t_v2_fabricated_minimal_collision_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    fixture["collision"].write_text(json.dumps({
        "schema": 1, "kind": "pcb-enclosure-collision-v1",
        "status": "COMPLETE",
        "inputs": {"generation": {
            "path": fixture["generation"].name,
            "sha256": _sha(fixture["generation"]),
            "size": fixture["generation"].stat().st_size,
        }},
        "result": {"classification": "EMPTY",
                   "exact_brep_volume_mm3": 0},
    }) + "\n")
    value["collision"] = _binding(fixture["root"], fixture["collision"])
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "receipt.builder")
        return
    check(False, "fabricated minimal collision unexpectedly passed")


@test("collision authority reopens STEP, component, mesh, and builder bytes",
      kind="known_bad", gate="build_collision.py")
def t_v2_collision_authority_drift_bites():
    for subject in ("collision_step", "component_mesh", "collision_mesh",
                    "builder"):
        fixture, _, value = _bound_manufacturing_fixture()
        if subject == "builder":
            collision = json.loads(fixture["collision"].read_text())
            collision["builder"]["sha256"] = "d" * 64
            fixture["collision"].write_text(json.dumps(collision) + "\n")
            value["collision"] = _binding(
                fixture["root"], fixture["collision"])
        else:
            fixture[subject].write_text(
                fixture[subject].read_text() + "\n")
        try:
            v2._validate_manufacturing_audit(
                value, fixture["root"], fixture["config"],
                yaml.safe_load(fixture["config"].read_text()),
                {"shell": {"required": True}}, {})
        except v2.V2Error as exc:
            if subject == "builder":
                contains(str(exc), "builder bytes differ")
            else:
                contains(str(exc), "bound size/hash differs")
            continue
        check(False, f"stale collision authority {subject} unexpectedly passed")


@test("collision interface is subordinate to the audited CAD subject",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_forged_collision_interface_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    fake_interface = fixture["root"] / "fake-board-interface.json"
    fake_interface.write_text("{}\n")
    inspection = json.loads(fixture["step_inspection"].read_text())
    inspection["interface"] = {
        "path": fake_interface.name, "sha256": _sha(fake_interface),
        "size": fake_interface.stat().st_size,
    }
    fixture["step_inspection"].write_text(json.dumps(inspection) + "\n")
    collision = json.loads(fixture["collision"].read_text())
    collision["inputs"]["interface"] = dict(inspection["interface"])
    collision["inputs"]["step_inspection"] = {
        "path": fixture["step_inspection"].name,
        "sha256": _sha(fixture["step_inspection"]),
        "size": fixture["step_inspection"].stat().st_size,
    }
    fixture["collision"].write_text(json.dumps(collision) + "\n")
    value["collision"] = _binding(fixture["root"], fixture["collision"])
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "CAD subject interface")
        return
    check(False, "forged collision interface unexpectedly passed")


@test("subject-step collision cannot substitute another STEP",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_forged_collision_subject_step_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    alternate = fixture["root"] / "alternate-board.step"
    alternate.write_bytes(fixture["collision_step"].read_bytes() + b"\n")
    inspection = json.loads(fixture["step_inspection"].read_text())
    inspection["step"] = {
        "path": alternate.name, "sha256": _sha(alternate),
        "size": alternate.stat().st_size,
    }
    fixture["step_inspection"].write_text(json.dumps(inspection) + "\n")
    collision = json.loads(fixture["collision"].read_text())
    collision["inputs"]["step"] = dict(inspection["step"])
    collision["inputs"]["step_inspection"] = {
        "path": fixture["step_inspection"].name,
        "sha256": _sha(fixture["step_inspection"]),
        "size": fixture["step_inspection"].stat().st_size,
    }
    fixture["collision"].write_text(json.dumps(collision) + "\n")
    value["collision"] = _binding(fixture["root"], fixture["collision"])
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "subject_step collision STEP differs")
        return
    check(False, "substitute subject collision STEP unexpectedly passed")


@test("collision replay independently rejects forged inspector selection",
      kind="known_bad", gate="build_collision.py")
def t_collision_forged_inspector_selection_bites():
    fixture = _fixture()
    inspection = json.loads(fixture["step_inspection"].read_text())
    inspection["geometry"]["solid_count"] = 3
    inspection["geometry"]["pcb_related_solid_indices"] = [0, 1]
    inspection["geometry"]["component_solid_count"] = 1
    fixture["step_inspection"].write_text(json.dumps(inspection) + "\n")
    collision = json.loads(fixture["collision"].read_text())
    collision["inputs"]["step_inspection"] = {
        "path": fixture["step_inspection"].name,
        "sha256": _sha(fixture["step_inspection"]),
        "size": fixture["step_inspection"].stat().st_size,
    }
    collision["selection"] = {
        "step_solid_count": 3, "pcb_related_solid_count": 2,
        "component_solid_count": 1,
    }
    fixture["collision"].write_text(json.dumps(collision) + "\n")

    def inspector_truth(command, *, cwd):
        if "--geometry-only" not in command:
            check(False, "collision build ran after inspector mismatch")
        output = Path(command[command.index("--output") + 1])
        sealed = json.loads(Path(
            command[command.index("--step-inspection") + 1]
            if "--step-inspection" in command else
            fixture["step_inspection"]).read_text())
        geometry = copy.deepcopy(sealed["geometry"])
        geometry["pcb_related_solid_indices"] = [0]
        geometry["component_solid_count"] = 2
        output.write_text(json.dumps({
            "schema": 1, "kind": "pcb-enclosure-step-geometry-regrade-v1",
            "status": "COMPLETE", "step": sealed["step"],
            "interface": sealed["interface"], "geometry": geometry,
        }) + "\n")

    try:
        collision_builder.replay_collision_receipt(
            fixture["collision"], runner=inspector_truth)
    except collision_builder.EnclosureError as exc:
        contains(str(exc), "selection does not reproduce")
        return
    check(False, "forged inspector component selection unexpectedly replayed")


@test("stale manufacturing collision bytes are rejected",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_stale_collision_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    fixture["collision"].write_text(fixture["collision"].read_text() + " \n")
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "bound size/hash differs")
        return
    check(False, "stale manufacturing collision unexpectedly passed")


@test("manufacturing collision cannot bind an alternate generation",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_alternate_collision_generation_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    alternate = fixture["root"] / "alternate-generation.json"
    shutil.copyfile(fixture["generation"], alternate)
    collision = json.loads(fixture["collision"].read_text())
    collision["inputs"]["generation"] = {
        "path": alternate.name, "sha256": _sha(alternate),
        "size": alternate.stat().st_size,
    }
    fixture["collision"].write_text(json.dumps(collision) + "\n")
    value["collision"] = _binding(fixture["root"], fixture["collision"])
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "different generation receipt")
        return
    check(False, "alternate collision generation unexpectedly passed")


@test("manufacturing collision must use the generated installed case",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_wrong_collision_case_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    collision = json.loads(fixture["collision"].read_text())
    collision["inputs"]["assembled_case_mesh"]["sha256"] = "e" * 64
    fixture["collision"].write_text(json.dumps(collision) + "\n")
    value["collision"] = _binding(fixture["root"], fixture["collision"])
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "assembled case differs")
        return
    check(False, "collision for a different installed case unexpectedly passed")


@test("manufacturing collision must be an exact empty BRep result",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_intersection_collision_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    collision = json.loads(fixture["collision"].read_text())
    collision["result"]["classification"] = "INTERSECTION"
    collision["result"]["exact_brep_volume_mm3"] = 0.25
    collision["result"]["representation"] = \
        "tessellation-of-exact-brep-common"
    fixture["collision"].write_text(json.dumps(collision) + "\n")
    value["collision"] = _binding(fixture["root"], fixture["collision"])
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "must prove EMPTY")
        return
    check(False, "intersecting manufacturing collision unexpectedly passed")


@test("release replay requires exact FDM compiler and schema helper closure",
      kind="known_bad", gate="enclosure_v2.py")
def t_release_helper_binding_bites():
    fixture = _fixture()
    receipt = fdm.audit_paths(
        fixture["contract"], fixture["config"], fixture["generation"],
        fixture["meshes"], root=fixture["root"])
    release = tmpdir("fdm-release-closure-")
    tooling = release / "tooling"
    tooling.mkdir()
    compiler = tooling / "fdm_structural_audit.py"
    helper = tooling / "enclosure_common.py"
    shutil.copyfile(SCRIPT, compiler)
    shutil.copyfile(SCRIPT.parent / "enclosure_common.py", helper)
    compiler_binding = {"path": "tooling/fdm_structural_audit.py",
                        "sha256": _sha(compiler), "size": compiler.stat().st_size}
    helper_binding = {"path": "tooling/enclosure_common.py",
                      "sha256": _sha(helper), "size": helper.stat().st_size}
    module, _, _ = v2._fdm_audit_compiler_module(
        receipt["inputs"]["compiler"], receipt["inputs"]["enclosure_common"],
        release_root=release, release_binding=compiler_binding,
        release_helper_binding=helper_binding)
    check(hasattr(module, "audit_paths"), "sealed replay compiler API")
    helper.write_text(helper.read_text() + "\n# injected drift\n")
    try:
        v2._fdm_audit_compiler_module(
            receipt["inputs"]["compiler"],
            receipt["inputs"]["enclosure_common"], release_root=release,
            release_binding=compiler_binding,
            release_helper_binding=helper_binding)
    except v2.V2Error:
        return
    check(False, "mutated release schema helper unexpectedly passed")


@test("release mesh, collision, and FDM evidence share one generation",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_generation_closure_bites():
    fixture = _fixture()
    release = tmpdir("fdm-generation-closure-")
    verification = release / "verification"
    verification.mkdir()
    copied_names = (
        "generation", "collision", "step_inspection", "component_mesh",
        "installed_case", "collision_step", "collision_mesh", "source",
    )
    copied = {}
    for name in copied_names:
        source = fixture[name]
        target = verification / source.name
        shutil.copyfile(source, target)
        copied[name] = target
    generation_path = copied["generation"]
    generation = _binding(release, generation_path)
    local_generation = {
        "path": "generation.json", "sha256": generation["sha256"],
        "size": generation["size"],
    }
    collision_path = copied["collision"]
    selected_collision = _binding(release, collision_path)
    parent_collision_path = verification / "parent-step-collision.json"
    parent_collision_path.write_text(json.dumps({
        "kind": "pcb-enclosure-collision-v1",
        "result": {"classification": "INTERSECTION",
                   "exact_brep_volume_mm3": 2.5},
    }) + "\n")
    parent_collision_file = {
        "path": parent_collision_path.name,
        "sha256": _sha(parent_collision_path),
        "size": parent_collision_path.stat().st_size,
    }
    generic_path = verification / "verification.json"

    def write_generic() -> None:
        generic_path.write_text(json.dumps({
            "kind": "pcb-enclosure-verification-v1",
            "checks": [
                {"name": "printable_meshes",
                 "status": "PASS",
                 "evidence": {"generation_file": local_generation}},
                {"name": "exact_solid_clearance", "status": "FAIL",
                 "evidence": {
                    "generation_file": local_generation,
                    "collision_report_file": parent_collision_file,
                }},
            ],
        }) + "\n")

    write_generic()

    def payloads() -> dict:
        return {path.relative_to(release).as_posix(): _binding(release, path)
                for path in (*copied.values(), parent_collision_path,
                             generic_path)}

    result = release_verify._validate_fdm_generation_evidence_closure(
        release, generation, selected_collision, payloads())
    eq(result["generation"], "verification/generation.json")
    eq(result["collision"], "verification/collision.json")

    collision = json.loads(collision_path.read_text())
    collision["inputs"]["generation"] = {
        **local_generation, "sha256": "b" * 64,
    }
    collision_path.write_text(json.dumps(collision) + "\n")
    selected_collision = _binding(release, collision_path)
    try:
        release_verify._validate_fdm_generation_evidence_closure(
            release, generation, selected_collision, payloads())
    except release_verify.ReleaseError as exc:
        contains(str(exc), "different generation receipt")
        return
    check(False, "split collision/manufacturing generation unexpectedly passed")


@test("release generator replay reproduces every sealed enclosure output",
      kind="known_bad", gate="verify_enclosure_release.py")
def t_release_generator_replay_bites_on_substituted_case():
    original = _fixture()
    release = tmpdir("fdm-generator-replay-")
    for directory in ("source/subject", "tooling", "verification", "meshes"):
        (release / directory).mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(original["config"].read_text())
    source_files = {
        "release_manifest": original["root"] / "subject/MANIFEST.txt",
        "pcb": original["root"] / "subject/board.kicad_pcb",
        "step": original["root"] / "subject/board.step",
        "interface": original["root"] / "subject/board-interface.json",
    }
    copied_subjects = {}
    for field, source in source_files.items():
        target = release / "source/subject" / source.name
        shutil.copyfile(source, target)
        copied_subjects[field] = target
        config["subject"][field] = _binding(release, target)
    authored = release / "source/case.scad"
    shutil.copyfile(original["source"], authored)
    config["cad"]["source"] = {
        "kind": "authored_scad", **_binding(release, authored)}
    cad_config = release / "source/enclosure.yaml"
    _write_yaml(cad_config, config)

    tooling_sources = {
        "enclosure_generator": GENERATOR,
        "enclosure_common": SCRIPT.parent / "enclosure_common.py",
        "process_runner": ROOT / collision_builder.PROCESS_RUNNER_SOURCE_PATH,
        "pipeline_runtime": ROOT / collision_builder.PIPELINE_RUNTIME_SOURCE_PATH,
    }
    tool_names = {
        "enclosure_generator": "generate_enclosure.py",
        "enclosure_common": "enclosure_common.py",
        "process_runner": "process_runner.py",
        "pipeline_runtime": "pipeline_runtime.py",
    }
    tools = {}
    for role, source in tooling_sources.items():
        target = release / "tooling" / tool_names[role]
        shutil.copyfile(source, target)
        tools[role] = {"role": role, **_binding(release, target)}

    seed = release / "seed"
    generated = run([
        KPY, release / "tooling/generate_enclosure.py", cad_config,
        "--root", release, "--build-dir", seed,
    ], timeout=180)
    check(generated.rc == 0, generated.out)
    generation = release / "verification/generation.json"
    generation_source = release / "verification/enclosure.scad"
    installed_case = release / "verification/assembled-case.stl"
    shutil.copyfile(seed / "generation.json", generation)
    shutil.copyfile(seed / "enclosure.scad", generation_source)
    shutil.copyfile(seed / "assembled-case.stl", installed_case)
    audit_meshes = []
    for part in config["cad"]["printable_parts"]:
        target = release / "meshes" / f"{part}.stl"
        shutil.copyfile(seed / f"{part}.stl", target)
        audit_meshes.append({"part": part, **_binding(release, target)})
    audit = {"meshes": audit_meshes}
    cad_binding = _binding(release, cad_config)
    v2_config = {"subject": {
        "release": config["subject"]["release"],
        "release_manifest": config["subject"]["release_manifest"],
        "pcb": config["subject"]["pcb"], "step": config["subject"]["step"],
        "interface": config["subject"]["interface"],
        "mechanical_intent": cad_binding, "cad_design": cad_binding,
    }}

    def payloads():
        return {
            path.relative_to(release).as_posix(): _binding(release, path)
            for path in release.rglob("*") if path.is_file()
        }

    generation_binding = _binding(release, generation)
    clean = release_verify._validate_generation_replay(
        release, v2_config, audit, generation_binding, tools, payloads())
    eq(clean["parts"], sorted(config["cad"]["printable_parts"]))

    forged = json.loads(generation.read_text())
    forged["installed_case"]["sha256"] = "f" * 64
    generation.write_text(json.dumps(forged, indent=2, sort_keys=True) + "\n")
    generation_binding = _binding(release, generation)
    try:
        release_verify._validate_generation_replay(
            release, v2_config, audit, generation_binding, tools, payloads())
    except release_verify.ReleaseError as exc:
        contains(str(exc), "does not reproduce byte-exact")
        return
    check(False, "substituted installed-case generation unexpectedly replayed")


@test("intentional flexure exceptions require the exact v2 print test",
      kind="known_bad", gate="enclosure_v2.py")
def t_flexure_test_crosslink_bites():
    fixture = _fixture()
    contract = yaml.safe_load(fixture["contract"].read_text())
    contract["attachments"][0]["exception_id"] = "closure_flexure"
    contract["flexure_exceptions"] = [{
        "id": "closure_flexure", "type": "intentional_flexure",
        "attachment_id": "closure_root",
        "rationale": "Fixture controlled compliance.",
        "hard_stop": "Rigid stop limits travel before yield.",
        "physical_test_id": "closure_flexure_cycle",
    }]
    _write_yaml(fixture["contract"], contract)
    receipt = fdm.audit_paths(
        fixture["contract"], fixture["config"], fixture["generation"],
        fixture["meshes"], root=fixture["root"])
    fixture["output"].write_text(json.dumps(receipt, indent=2) + "\n")
    value = _manufacturing_value(fixture)
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "physical test closure_flexure_cycle is absent")
        return
    check(False, "unqualified intentional flexure unexpectedly passed v2")


@test("v2 final reopen detects receipt replacement after successful regrade",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_receipt_swap_bites():
    fixture = _fixture()
    receipt = fdm.audit_paths(
        fixture["contract"], fixture["config"], fixture["generation"],
        fixture["meshes"], root=fixture["root"])
    fixture["output"].write_text(json.dumps(receipt, indent=2) + "\n")
    value = _manufacturing_value(fixture)
    original = v2._fdm_audit_compiler_module

    def injected(*args, **kwargs):
        module, compiler, helper = original(*args, **kwargs)
        real = module.audit_paths_with_contract

        def mutate(*audit_args, **audit_kwargs):
            result = real(*audit_args, **audit_kwargs)
            fixture["output"].write_text("{}\n")
            return result
        module.audit_paths_with_contract = mutate
        return module, compiler, helper

    v2._fdm_audit_compiler_module = injected
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {},
            release_fdm_compiler=None, release_fdm_helper=None)
    except v2.V2Error as exc:
        contains(str(exc), "bound size/hash differs")
    else:
        check(False, "receipt swap after regrade unexpectedly passed")
    finally:
        v2._fdm_audit_compiler_module = original


@test("v2 final reopen detects collision replacement after FDM regrade",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_collision_swap_bites():
    fixture, _, value = _bound_manufacturing_fixture()
    original = v2._fdm_audit_compiler_module

    def injected(*args, **kwargs):
        module, compiler, helper = original(*args, **kwargs)
        real = module.audit_paths_with_contract

        def mutate(*audit_args, **audit_kwargs):
            result = real(*audit_args, **audit_kwargs)
            fixture["collision"].write_text("{}\n")
            return result
        module.audit_paths_with_contract = mutate
        return module, compiler, helper

    v2._fdm_audit_compiler_module = injected
    try:
        v2._validate_manufacturing_audit(
            value, fixture["root"], fixture["config"],
            yaml.safe_load(fixture["config"].read_text()),
            {"shell": {"required": True}}, {})
    except v2.V2Error as exc:
        contains(str(exc), "bound size/hash differs")
    else:
        check(False, "collision swap after FDM regrade unexpectedly passed")
    finally:
        v2._fdm_audit_compiler_module = original


@test("fleet audit counts only declared release meshes and grandfathers predecessors")
def t_fleet_policy():
    result = run([KPY, FLEET, "--root", ROOT])
    eq(result.rc, 0, "real fleet audit")
    contains(result.out, "releases=")
    report = fdm_audit_fleet_report()
    check(report["release_count"] >= 12, "established enclosure releases disappeared")
    check(report["printable_count"] >= 48, "established printable census shrank")
    check(report["legacy_incomplete_release_count"] >= 12,
          "predecessors were silently newly certified")
    check(report["excluded_nonprintable_stl_count"] > 0,
          "verification/reference STL exclusion denominator is zero")


def fdm_audit_fleet_report() -> dict:
    spec = importlib.util.spec_from_file_location("fdm_audit_fleet_test", FLEET)
    check(spec is not None and spec.loader is not None, "fleet module load")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Earlier synthetic manufacturing fixtures replace the collision process
    # runner so their deliberately tiny fake STEP inputs never enter CadQuery.
    # The real fleet audit must not inherit that test-only process hook: doing
    # so routes a later release's composition receipt through the synthetic
    # collision validator and makes test order affect the result.
    previous_runner = v2._COLLISION_PROCESS_RUNNER
    v2._COLLISION_PROCESS_RUNNER = None
    try:
        return module.audit_fleet(ROOT)
    finally:
        v2._COLLISION_PROCESS_RUNNER = previous_runner


if __name__ == "__main__":
    sys.exit(main())
