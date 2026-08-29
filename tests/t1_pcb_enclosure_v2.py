#!/usr/bin/env python3
"""Schema-v2 enclosure contracts: authority, service, motion, and evidence."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import yaml

from harness import check, contains, eq, main, must_fail, must_pass, run, test, tmpdir


ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / "skills" / "pcb-enclosure" / "scripts" / "enclosure_v2.py"
CONNECTOR_COMPILER = (
    ROOT / "skills" / "pcb-design" / "scripts" /
    "connector_assembly_contract.py")
CONNECTOR_TEMPLATE = (
    ROOT / "skills" / "pcb-design" / "templates" / "03_src" / "rules" /
    "connector_assemblies.yaml")
KPY = "/usr/bin/python3"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _binding(root: Path, path: Path) -> dict:
    return {"path": path.relative_to(root).as_posix(), "sha256": _sha(path),
            "size": path.stat().st_size}


def _write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def _fresh_fixture() -> dict[str, Path]:
    root = tmpdir("pcb_enclosure_v2_")
    subject = root / "subject"
    subject.mkdir()
    pcb = subject / "board.kicad_pcb"
    step = subject / "board.step"
    interface = subject / "board-interface.json"
    antenna = subject / "antenna-measurements.yaml"
    intent_path = root / "mechanical-intent.yaml"
    manifest_path = subject / "release-manifest.yaml"
    cad_design_path = root / "enclosure.yaml"
    config_path = root / "enclosure-v2.yaml"
    pcb.write_text("(kicad_pcb (version 20240108))\n", encoding="utf-8")
    step.write_text("ISO-10303-21;\nEND-ISO-10303-21;\n", encoding="utf-8")
    footprints = [
        {
            "ref": ref, "value": ref, "footprint": f"Synthetic_{ref}",
            "position_mm": list(position), "rotation_deg": 0.0,
            "side": "front",
            "bbox_mm": [position[0] - 2, position[1] - 2,
                        position[0] + 2, position[1] + 2],
            "model_declared": ref == "J1",
        }
        for ref, position in (
            ("H1", (-25.0, -15.0)), ("H2", (25.0, -15.0)),
            ("H3", (-25.0, 15.0)), ("H4", (25.0, 15.0)),
            ("J1", (0.0, -18.0)),
        )
    ]
    holes = [
        {"ref": ref, "pad": "", "position_mm": list(position),
         "drill_mm": [3.2, 3.2], "attribute": "NPTH"}
        for ref, position in (
            ("H1", (-25.0, -15.0)), ("H2", (25.0, -15.0)),
            ("H3", (-25.0, 15.0)), ("H4", (25.0, 15.0)),
        )
    ]
    interface_value = {
        "schema": 1,
        "kind": "pcb-enclosure-interface-v1",
        "subject": {"board": {"name": pcb.name, "sha256": _sha(pcb),
                                 "size": pcb.stat().st_size}},
        "frame": {
            "units": "mm", "origin": "outline_bbox_center",
            "board_to_case": [[1, 0, 0, 0], [0, 1, 0, 0],
                              [0, 0, 1, 0], [0, 0, 0, 1]],
            "z_zero": "pcb_back_surface", "z_positive": "front",
        },
        "board": {
            "thickness_mm": 1.6,
            "outline": {
                "contours_mm": [[[-30, -20], [30, -20], [30, 20], [-30, 20]]],
                "bbox_mm": [-30, -20, 30, 20], "size_mm": [60, 40],
            },
            "drills": holes, "mounting_holes": holes,
            "footprints": footprints,
            "access_candidates": [{
                "ref": "J1", "position_mm": [0.0, -18.0], "value": "J1",
                "footprint": "Synthetic_J1", "selection": "required",
            }],
        },
        "coverage": {"footprints": 5, "drills": 4, "mounting_holes": 4,
                     "access_candidates": 1},
    }
    interface.write_text(json.dumps(interface_value, indent=2) + "\n",
                         encoding="utf-8")
    antenna.write_text(
        "source: measured physical unit\nbody_diameter_mm: 13.0\n",
        encoding="utf-8")

    intent = {
        "schema": 2,
        "kind": "pcb-enclosure-mechanical-intent-v2",
        "name": "pluto-rx2-8way-v5-enclosure",
        "desired_release": {"lifecycle": "draft", "readiness": "CAD_READY"},
        "requirements": {
            "pcb_retained_with_lid_removed": True,
            "cabled_parts": [{
                "id": "reference_antenna_cable", "part": "antenna",
                "cable_pre_attached": True, "threading_permitted": False,
                "bending_permitted": False, "disconnecting_permitted": False,
            }],
        },
        "states": [
            {
                "id": "lid_removed_before_antenna", "purpose": "lid_removed",
                "present_parts": ["base", "pcb"],
                "secured_fastener_groups": ["pcb_screws"],
                "enclosure_closed": False, "pcb_retained": True,
            },
            {
                "id": "lid_removed_antenna_installed", "purpose": "insertion",
                "present_parts": ["base", "pcb", "antenna"],
                "secured_fastener_groups": ["pcb_screws"],
                "enclosure_closed": False, "pcb_retained": True,
            },
            {
                "id": "installed", "purpose": "installed",
                "present_parts": ["base", "pcb", "antenna", "lid"],
                "secured_fastener_groups": ["pcb_screws", "case_screws"],
                "enclosure_closed": True, "pcb_retained": True,
            },
        ],
        "operations": [
            {
                "id": "insert_antenna", "kind": "linear_insert",
                "from_state": "lid_removed_before_antenna",
                "to_state": "lid_removed_antenna_installed",
                "moving_parts": ["antenna"], "direction": [0, 0, 1],
                "travel_mm": 25.0, "cable_condition": "pre_attached",
                "threading_permitted": False, "bending_permitted": False,
                "disconnecting_permitted": False,
                "clearance_case": "antenna_installation",
            },
            {
                "id": "install_lid", "kind": "linear_insert",
                "from_state": "lid_removed_antenna_installed",
                "to_state": "installed", "moving_parts": ["lid"],
                "direction": [0, 0, -1], "travel_mm": 12.0,
                "cable_condition": "pre_attached",
                "threading_permitted": False, "bending_permitted": False,
                "disconnecting_permitted": False,
                "clearance_case": "lid_installation",
            },
        ],
        "unknowns": [],
        "excluded_claims": ["physical_fit", "thermal_performance"],
    }
    _write_yaml(intent_path, intent)
    manifest_path.write_text(
        "MANIFEST — synthetic immutable PCB release\n\nsha256:\n"
        f"  {pcb.name}  {_sha(pcb)}\n"
        f"  {step.name}  {_sha(step)}\n",
        encoding="utf-8")

    v1_subject = {
        "release": "pcb-v0.2.1-2026-08-14",
        "release_manifest": _binding(root, manifest_path),
        "pcb": _binding(root, pcb),
        "step": _binding(root, step),
        "interface": _binding(root, interface),
    }
    cad_design = {
        "schema": 1,
        "kind": "pcb-enclosure-config-v1",
        "name": "pluto-rx2-8way-v5-enclosure",
        "mode": "derived",
        "subject": v1_subject,
        "process": {
            "method": "fdm", "material": "PETG", "nozzle_mm": 0.4,
            "layer_mm": 0.2, "support_policy": "forbid_when_practical",
            "minimum_wall_mm": 1.2,
        },
        "cad": {"engine": "openscad", "minimum_version": "2021.01",
                "printable_parts": ["base", "lid", "insert_coupon"]},
        "geometry": {
            "topology": "split_shell", "xy_clearance_mm": 1.0,
            "wall_mm": 2.4, "floor_mm": 2.4, "roof_mm": 2.4,
            "corner_radius_mm": 4.0, "board_bottom_z_mm": 8.0,
            "inside_top_z_mm": 20.0, "seam_z_mm": 15.0,
            "panel_thickness_mm": 2.4, "panel_capture_mm": 1.2,
            "panel_clearance_mm": 0.25, "corner_post_mm": 8.0,
            "lid_column_board_gap_mm": 0.2,
        },
        "fasteners": {
            "strategy": "separate_perimeter", "thread": "M3-0.5",
            "board_holes": ["H1", "H2", "H3", "H4"],
            "case_holes_mm": [[-35, -25], [35, -25], [-35, 25], [35, 25]],
            "boss_d_mm": 8.0, "case_post_d_mm": 9.0,
            "minimum_radial_wall_mm": 0.8,
            "insert": {
                "family": "synthetic-M3", "installation": "cold_press",
                "hole_d_mm": 4.0, "body_d_mm": 4.2, "flange_d_mm": 5.5,
                "flange_recess_d_mm": 6.0, "flange_recess_depth_mm": 0.8,
                "length_mm": 4.0, "bottom_clearance_mm": 0.2,
            },
            "screw": {
                "clearance_d_mm": 3.4, "head_d_mm": 6.0,
                "head_recess_depth_mm": 1.0, "board_length_mm": 6.0,
                "lid_length_mm": 8.0, "minimum_engagement_mm": 3.0,
                "minimum_tip_clearance_mm": 0.5,
            },
        },
        "interfaces": [{
            "id": "usb", "ref": "J1", "role": "data-and-power",
            "side": "north", "disposition": "opening",
            "center_mm": [0.0, -20.0, 10.0], "shape": "rect",
            "opening_mm": [12.0, 8.0],
            "plug_envelope_mm": [10.0, 6.0, 15.0], "clearance_mm": 1.0,
        }],
        "thermal": {"risk": "low", "physical_soak_required": False,
                    "load_case": "synthetic room-temperature load", "vents": []},
        "physical_validation": {
            "insert_coupon_required": True, "board_drop_in_required": True,
            "all_interfaces_mated_required": True,
            "thermal_soak_required": False,
        },
    }
    _write_yaml(cad_design_path, cad_design)

    config = {
        "schema": 2,
        "kind": "pcb-enclosure-config-v2",
        "name": "pluto-rx2-8way-v5-enclosure",
        "mode": "derived",
        "subject": {
            "release": "pcb-v0.2.1-2026-08-14",
            "release_manifest": _binding(root, manifest_path),
            "pcb": _binding(root, pcb),
            "step": _binding(root, step),
            "interface": _binding(root, interface),
            "mechanical_intent": _binding(root, intent_path),
            "cad_design": _binding(root, cad_design_path),
        },
        "external_subjects": [{
            "id": "reference_antenna", "role": "installed_antenna",
            "source": _binding(root, antenna),
            "authority": {
                "grade": "measured_unit",
                "basis": "Caliper measurements of the unit to be installed.",
                "excluded_claims": ["physical_fit"],
            },
        }],
        "verification_scopes": [
            {"id": "shell", "description": "Base and lid shell",
             "required": True, "depends_on": []},
            {"id": "board_retention", "description": "Independent PCB mount",
             "required": True, "depends_on": ["shell"]},
            {"id": "antenna_accessory", "description": "Prewired top antenna",
             "required": True, "depends_on": ["shell"]},
            {"id": "thermal", "description": "Installed thermal behavior",
             "required": True, "depends_on": ["shell"]},
        ],
        "installed_parts": [
            {"id": "pcb", "role": "pcb",
             "source": {"kind": "subject", "id": "pcb"},
             "scopes": ["shell", "board_retention", "thermal"]},
            {"id": "base", "role": "base",
             "source": {"kind": "generated", "id": "base"},
             "scopes": ["shell", "board_retention", "antenna_accessory"]},
            {"id": "lid", "role": "lid",
             "source": {"kind": "generated", "id": "lid"},
             "scopes": ["shell", "antenna_accessory", "thermal"]},
            {"id": "antenna", "role": "accessory",
             "source": {"kind": "external_subject", "id": "reference_antenna"},
             "scopes": ["antenna_accessory"]},
        ],
        "fastener_policy": {
            "axis_disjoint_tolerance_mm": 0.1,
            "pcb_retained_with_lid_removed": True,
        },
        "fastener_groups": [
            {
                "id": "pcb_screws", "role": "board_retention",
                "axes": [
                    {"id": "h1", "origin_mm": [-25, -15, 0],
                     "direction": [0, 0, 1]},
                    {"id": "h2", "origin_mm": [25, -15, 0],
                     "direction": [0, 0, 1]},
                    {"id": "h3", "origin_mm": [-25, 15, 0],
                     "direction": [0, 0, 1]},
                    {"id": "h4", "origin_mm": [25, 15, 0],
                     "direction": [0, 0, 1]},
                ],
                "retained_parts": ["pcb", "base"],
                "hardware": {"thread": "M3-0.5", "screw_length_mm": 6.0,
                             "minimum_engagement_mm": 3.0,
                             "minimum_tip_clearance_mm": 0.5},
            },
            {
                "id": "case_screws", "role": "case_closure",
                "axes": [
                    {"id": "c1", "origin_mm": [-35, -25, 0],
                     "direction": [0, 0, 1]},
                    {"id": "c2", "origin_mm": [35, -25, 0],
                     "direction": [0, 0, 1]},
                    {"id": "c3", "origin_mm": [-35, 25, 0],
                     "direction": [0, 0, 1]},
                    {"id": "c4", "origin_mm": [35, 25, 0],
                     "direction": [0, 0, 1]},
                ],
                "retained_parts": ["base", "lid"],
                "hardware": {"thread": "M3-0.5", "screw_length_mm": 8.0,
                             "minimum_engagement_mm": 3.0,
                             "minimum_tip_clearance_mm": 0.5},
            },
        ],
        "clearance_cases": [
            {
                "id": "antenna_installation", "scope": "antenna_accessory",
                "operation": "insert_antenna", "opening_id": "bottom_arch",
                "moving_parts": ["antenna"], "obstacles": ["base", "pcb"],
                "envelope_basis": "full_part",
                "method": "linear_sweep_envelope", "minimum_clearance_mm": 0.5,
            },
            {
                "id": "lid_installation", "scope": "shell",
                "operation": "install_lid", "opening_id": "case_seam",
                "moving_parts": ["lid"],
                "obstacles": ["base", "pcb", "antenna"],
                "envelope_basis": "full_part",
                "method": "linear_sweep_exact", "minimum_clearance_mm": 0.2,
            },
        ],
        "service_envelopes": [{
            "id": "usb_service", "interface_id": "usb",
            "scope": "antenna_accessory",
            "simultaneous_group": "installed_rf_service",
            "mated_in_states": [
                "lid_removed_antenna_installed", "installed",
            ],
            "mated_during_operations": ["install_lid"],
            "observation_subject": None,
            "connector_body": {
                "basis": "conservative_candidate",
                "envelope_mm": [12.0, 8.0, 8.0],
            },
            "mated_plug": {
                "basis": "conservative_candidate",
                "envelope_mm": [10.0, 6.0, 15.0],
            },
            "strain_relief": {
                "basis": "conservative_candidate",
                "envelope_mm": [10.0, 6.0, 8.0],
            },
            "cable": {
                "basis": "conservative_candidate", "diameter_mm": 4.0,
                "straight_run_mm": 8.0, "exit_direction": [0, -1, 0],
            },
            "bend": {
                "basis": "conservative_candidate",
                "minimum_radius_mm": 12.0,
                "swept_envelope_mm": [24.0, 24.0, 20.0],
            },
            "installation_sweep": {
                "basis": "conservative_candidate",
                "method": "linear_sweep_envelope",
                "operation": "insert_antenna",
            },
            "allowances": {
                "basis": "conservative_candidate",
                "process_per_side_mm": [0.2, 0.2, 0.2],
                "assembly_per_side_mm": [0.5, 0.5, 0.5],
            },
        }],
        "physical_tests": [
            {"id": "lid_off_retention", "type": "lid_off_pcb_retention",
             "scope": "board_retention", "required_for": "PRINT_VERIFIED",
             "subject_parts": ["base", "pcb"]},
            {"id": "closure_independence",
             "type": "case_closure_independence", "scope": "board_retention",
             "required_for": "PRINT_VERIFIED",
             "subject_parts": ["base", "lid", "pcb"]},
            {"id": "antenna_insertion",
             "type": "accessory_insertion_removal", "scope": "antenna_accessory",
             "required_for": "PRINT_VERIFIED",
             "subject_parts": ["base", "lid", "antenna"]},
            {"id": "antenna_retention",
             "type": "accessory_retention_rattle", "scope": "antenna_accessory",
             "required_for": "PRINT_VERIFIED",
             "subject_parts": ["lid", "antenna"]},
            {"id": "antenna_cable_clearance",
             "type": "cable_strain_clearance", "scope": "antenna_accessory",
             "required_for": "PRINT_VERIFIED",
             "subject_parts": ["base", "lid", "antenna"]},
            {"id": "all_interfaces_mated",
             "type": "all_interfaces_mated", "scope": "antenna_accessory",
             "required_for": "PRINT_VERIFIED",
             "subject_parts": ["base", "lid", "pcb", "antenna"]},
            {"id": "thermal_soak", "type": "thermal_soak", "scope": "thermal",
             "required_for": "THERMALLY_VERIFIED",
             "subject_parts": ["base", "lid", "pcb"]},
        ],
    }
    _write_yaml(config_path, config)
    return {"root": root, "config": config_path, "intent": intent_path,
            "interface": interface, "manifest": manifest_path,
            "antenna": antenna,
            "cad_design": cad_design_path}


def _config(fixture: dict[str, Path]) -> dict:
    return yaml.safe_load(fixture["config"].read_text())


def _intent(fixture: dict[str, Path]) -> dict:
    return yaml.safe_load(fixture["intent"].read_text())


def _rewrite_intent(fixture: dict[str, Path], value: dict) -> None:
    _write_yaml(fixture["intent"], value)
    config = _config(fixture)
    config["subject"]["mechanical_intent"] = _binding(
        fixture["root"], fixture["intent"])
    _write_yaml(fixture["config"], config)


def _rewrite_cad_design(fixture: dict[str, Path], value: dict) -> None:
    _write_yaml(fixture["cad_design"], value)
    config = _config(fixture)
    config["subject"]["cad_design"] = _binding(
        fixture["root"], fixture["cad_design"])
    _write_yaml(fixture["config"], config)


def _add_second_service_interface(fixture: dict[str, Path]) -> None:
    interface = json.loads(fixture["interface"].read_text())
    interface["board"]["footprints"].append({
        "ref": "J2", "value": "J2", "footprint": "Synthetic_J2",
        "position_mm": [10.0, -18.0], "rotation_deg": 0.0,
        "side": "front", "bbox_mm": [8.0, -20.0, 12.0, -16.0],
        "model_declared": True,
    })
    interface["board"]["access_candidates"].append({
        "ref": "J2", "position_mm": [10.0, -18.0], "value": "J2",
        "footprint": "Synthetic_J2", "selection": "required",
    })
    interface["coverage"]["footprints"] += 1
    interface["coverage"]["access_candidates"] += 1
    fixture["interface"].write_text(
        json.dumps(interface, indent=2) + "\n", encoding="utf-8")

    config = _config(fixture)
    interface_binding = _binding(fixture["root"], fixture["interface"])
    cad = yaml.safe_load(fixture["cad_design"].read_text())
    cad["subject"]["interface"] = interface_binding
    second_interface = copy.deepcopy(cad["interfaces"][0])
    second_interface.update({
        "id": "usb2", "ref": "J2", "center_mm": [10.0, -20.0, 10.0],
    })
    cad["interfaces"].append(second_interface)
    _write_yaml(fixture["cad_design"], cad)
    config["subject"]["interface"] = interface_binding
    config["subject"]["cad_design"] = _binding(
        fixture["root"], fixture["cad_design"])
    second_service = copy.deepcopy(config["service_envelopes"][0])
    second_service.update({"id": "usb2_service", "interface_id": "usb2"})
    config["service_envelopes"].append(second_service)
    _write_yaml(fixture["config"], config)


def _add_shared_connector_contract(fixture: dict[str, Path]) -> None:
    """Replace the inline migration row with one fresh shared receipt."""
    contract = fixture["root"] / "03_src" / "rules" / \
        "connector_assemblies.yaml"
    contract.parent.mkdir(parents=True, exist_ok=True)
    evidence = fixture["root"] / "02_parts" / "synthetic-connector" / \
        "part.yaml"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(
        "mpn: SYNTHETIC-CONNECTOR\nmanufacturer: Test Fixture\n",
        encoding="utf-8")
    contract_value = yaml.safe_load(CONNECTOR_TEMPLATE.read_text())
    contract_value["evidence_sources"] = [{
        "id": "synthetic-part-dossier", "kind": "part-dossier",
        "path": "02_parts/synthetic-connector/part.yaml",
    }]
    contract_value["assemblies"][0]["receptacle"]["evidence"] \
        ["source_ids"] = ["synthetic-part-dossier"]
    _write_yaml(contract, contract_value)
    compiled = run([
        KPY, CONNECTOR_COMPILER, "--project", fixture["root"],
    ])
    eq(compiled.rc, 2, "unknown shared connector contract exit")
    receipt = (fixture["root"] / "06_build" / "verification" /
               "connector_assembly_contract.json")
    check(receipt.is_file(), "shared connector receipt exists")

    config = _config(fixture)
    del config["service_envelopes"]
    config["interface_assemblies"] = {
        "receipt": _binding(fixture["root"], receipt),
        "non_enclosure_refs": [],
        "group_state_bindings": [{
            "group_id": "replace-with-service-group",
            "enclosure_state_ids": ["installed"],
        }],
        "mappings": [{
            "id": "usb_service",
            "assembly_id": "replace-with-connector-profile",
            "interface_ids": ["usb"],
            "scope": "antenna_accessory",
            "mated_in_states": [
                "lid_removed_antenna_installed", "installed",
            ],
            "mated_during_operations": ["install_lid"],
        }],
    }
    _write_yaml(fixture["config"], config)
    fixture["connector_contract"] = contract
    fixture["connector_evidence"] = evidence
    fixture["connector_receipt"] = receipt


def _add_wholly_non_enclosure_group(fixture: dict[str, Path]) -> None:
    """Add a two-member receipt group with no case opening or service map."""
    contract = yaml.safe_load(fixture["connector_contract"].read_text())
    profile = contract["assemblies"][0]
    prototype = profile["instances"][0]
    for ref in ("J2", "J3"):
        instance = copy.deepcopy(prototype)
        instance["ref"] = ref
        instance["simultaneous_group_ids"] = ["internal-service-group"]
        profile["instances"].append(instance)
    group = copy.deepcopy(contract["simultaneous_groups"][0])
    group.update({
        "id": "internal-service-group",
        "members": ["J2", "J3"],
        "serviceable_member_refs": ["J2", "J3"],
    })
    contract["simultaneous_groups"].append(group)
    _write_yaml(fixture["connector_contract"], contract)
    _recompile_shared_connector(fixture)


def _non_enclosure_row(ref: str) -> dict[str, str]:
    return {
        "ref": ref,
        "disposition": "no_enclosure_interface",
        "reason": "Internal service connector is intentionally inaccessible "
                  "in this enclosure configuration.",
    }


def _recompile_shared_connector(fixture: dict[str, Path]) -> None:
    result = run([
        KPY, CONNECTOR_COMPILER, "--project", fixture["root"],
    ])
    check(result.rc in {0, 2}, "shared connector recompile succeeds")
    config = _config(fixture)
    config["interface_assemblies"]["receipt"] = _binding(
        fixture["root"], fixture["connector_receipt"])
    _write_yaml(fixture["config"], config)


def _load_v2_module():
    scripts = V2.parent
    sys.path.insert(0, str(scripts))
    try:
        spec = importlib.util.spec_from_file_location(
            "pcb_enclosure_v2_test_module", V2)
        check(spec is not None and spec.loader is not None,
              "schema-v2 module spec")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(scripts))


def _validate_args(fixture: dict[str, Path]) -> list:
    return [KPY, V2, "validate-config", fixture["config"], "--root",
            fixture["root"]]


def _physical_evidence(fixture: dict[str, Path], statuses=None) -> Path:
    config = _config(fixture)
    statuses = statuses or {}
    evidence = {
        "schema": 2,
        "kind": "pcb-enclosure-physical-evidence-v2",
        "config_semantic_sha256": _semantic(config),
        "tests": [{
            "id": row["id"], "type": row["type"], "scope": row["scope"],
            "status": statuses.get(row["id"], "PASS"),
            "evidence": f"synthetic dated evidence for {row['id']}",
        } for row in config["physical_tests"]],
    }
    path = fixture["root"] / "physical-evidence-v2.yaml"
    _write_yaml(path, evidence)
    return path


@test("schema-v2 validates a complete Pluto-like enclosure contract")
def t_v2_clean_contract():
    fixture = _fresh_fixture()
    result = must_pass(run(_validate_args(fixture)), "v2 clean config")
    report = json.loads(result.out)
    eq(report["status"], "VALID")
    eq(report["service_envelope_coverage"], {
        "legacy_omitted": False,
        "legacy_readiness_capped": False,
        "declared": 1,
        "shared_mappings": 0,
        "shared_non_enclosure_refs": 0,
        "shared_receipt_status": None,
        "required_edge_openings": 1,
        "candidate_dimension_census_complete": 1,
    })
    eq(report["scope_readiness_ceilings"]["antenna_accessory"], "INCOMPLETE")


@test("schema-v2 validation report is canonical across project relocation")
def t_v2_validation_report_relocation_clean():
    fixtures = [_fresh_fixture(), _fresh_fixture()]
    reports = []
    for index, fixture in enumerate(fixtures):
        output = fixture["root"] / f"validation-{index}.json"
        must_pass(run([
            *_validate_args(fixture), "--output", output,
        ]), f"relocated v2 validation {index}")
        payload = output.read_bytes()
        check(str(fixture["root"]).encode() not in payload,
              "validation report leaked its absolute project root")
        report = json.loads(payload)
        eq(report["binding_path_base"], ".")
        eq(report["validator"]["path"],
           "skills/pcb-enclosure/scripts/enclosure_v2.py")
        reports.append(payload)
    eq(reports[0], reports[1], "relocation-stable v2 validation bytes")


@test("enclosure schema consumes the fresh shared connector receipt")
def t_v2_shared_connector_receipt():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    result = must_pass(run(_validate_args(fixture)),
                       "v2 shared connector config")
    report = json.loads(result.out)
    eq(report["service_envelope_coverage"]["legacy_omitted"], False)
    eq(report["service_envelope_coverage"]["declared"], 0)
    eq(report["service_envelope_coverage"]["shared_mappings"], 1)
    eq(report["service_envelope_coverage"]["shared_non_enclosure_refs"], 0)
    eq(report["service_envelope_coverage"]["shared_receipt_status"],
       "INCOMPLETE")
    eq(report["scope_readiness_ceilings"]["antenna_accessory"], "INCOMPLETE")


@test("wholly irrelevant connector groups require explicit dispositions")
def t_v2_shared_non_enclosure_group_clean():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    _add_wholly_non_enclosure_group(fixture)
    config = _config(fixture)
    config["interface_assemblies"]["non_enclosure_refs"] = [
        _non_enclosure_row("J2"), _non_enclosure_row("J3"),
    ]
    _write_yaml(fixture["config"], config)
    report = json.loads(must_pass(
        run(_validate_args(fixture)), "v2 explicit non-enclosure group").out)
    eq(report["service_envelope_coverage"]["shared_non_enclosure_refs"], 2)
    eq(report["scope_readiness_ceilings"]["antenna_accessory"], "INCOMPLETE")


@test("a wholly irrelevant connector group cannot disappear from the census",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_whole_group_omission():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    _add_wholly_non_enclosure_group(fixture)
    must_fail(run(_validate_args(fixture)), "v2 omitted whole connector group",
              "missing=['J2', 'J3']")


@test("non-enclosure connector dispositions use a closed literal",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_bad_non_enclosure_disposition():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    _add_wholly_non_enclosure_group(fixture)
    config = _config(fixture)
    bad = _non_enclosure_row("J2")
    bad["disposition"] = "ignore_connector"
    config["interface_assemblies"]["non_enclosure_refs"] = [
        bad, _non_enclosure_row("J3"),
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 bad connector disposition",
              "expected one of ['no_enclosure_interface']")


@test("non-enclosure connector dispositions require a human reason",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_non_enclosure_reason_required():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    _add_wholly_non_enclosure_group(fixture)
    config = _config(fixture)
    blank = _non_enclosure_row("J2")
    blank["reason"] = "  "
    config["interface_assemblies"]["non_enclosure_refs"] = [
        blank, _non_enclosure_row("J3"),
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 blank connector reason",
              "reason: expected non-empty string")


@test("non-enclosure connector dispositions cannot duplicate a ref",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_duplicate_non_enclosure_disposition():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    _add_wholly_non_enclosure_group(fixture)
    config = _config(fixture)
    config["interface_assemblies"]["non_enclosure_refs"] = [
        _non_enclosure_row("J2"), _non_enclosure_row("J2"),
        _non_enclosure_row("J3"),
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 duplicate connector disposition",
              "duplicate connector ref J2")


@test("non-enclosure connector dispositions must cover the complete group",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_partial_non_enclosure_disposition():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    _add_wholly_non_enclosure_group(fixture)
    config = _config(fixture)
    config["interface_assemblies"]["non_enclosure_refs"] = [
        _non_enclosure_row("J2"),
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 partial connector disposition",
              "missing=['J3']")


@test("top-side service openings require the same shared connector authority")
def t_v2_shared_connector_service_opening():
    fixture = _fresh_fixture()
    cad = yaml.safe_load(fixture["cad_design"].read_text())
    cad["interfaces"][0]["disposition"] = "service_opening"
    _rewrite_cad_design(fixture, cad)
    _add_shared_connector_contract(fixture)
    report = json.loads(must_pass(
        run(_validate_args(fixture)), "v2 shared top service connector").out)
    eq(report["service_envelope_coverage"]["required_edge_openings"], 1)
    eq(report["service_envelope_coverage"]["shared_mappings"], 1)


@test("shared connector receipt is recompiled, not trusted as JSON",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_connector_receipt_stale():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    with fixture["connector_contract"].open("a", encoding="utf-8") as stream:
        stream.write("\n# stale source mutation\n")
    receipt = json.loads(fixture["connector_receipt"].read_text())
    receipt["inputs"]["contract"] = _binding(
        fixture["root"], fixture["connector_contract"])
    fixture["connector_receipt"].write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    config = _config(fixture)
    config["interface_assemblies"]["receipt"] = _binding(
        fixture["root"], fixture["connector_receipt"])
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 stale connector receipt",
              "shared connector regrade failed")


@test("shared regrade reopens contract and evidence after compiler execution",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_connector_mid_regrade_input_drift():
    for field, phrase in (
            ("connector_receipt", "connector receipt changed during regrade"),
            ("connector_contract", "connector contract changed during regrade"),
            ("connector_evidence",
             "connector evidence file 0 changed during regrade")):
        fixture = _fresh_fixture()
        _add_shared_connector_contract(fixture)
        module = _load_v2_module()
        original_loader = module._connector_compiler_module
        target = fixture[field]

        def injected_loader(expected, *, _target=target):
            compiler, binding = original_loader(expected)
            original_validate = compiler.validate_receipt

            def injected_validate(receipt, root):
                result = original_validate(receipt, root)
                with _target.open("a", encoding="utf-8") as stream:
                    stream.write("\n# injected mid-regrade drift\n")
                return result

            compiler.validate_receipt = injected_validate
            return compiler, binding

        module._connector_compiler_module = injected_loader
        try:
            raw = module.load_yaml(fixture["config"])
            try:
                module.validate_config_v2(raw, fixture["root"])
            except module.V2Error as exc:
                contains(str(exc), phrase, f"{field} post-regrade drift")
            else:
                raise AssertionError(
                    f"{field} mid-regrade mutation unexpectedly validated")
        finally:
            module._connector_compiler_module = original_loader


@test("shared connector mappings cannot restate dimensions",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_connector_mapping_no_dimensions():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    config = _config(fixture)
    config["interface_assemblies"]["mappings"][0]["tool_clearance_mm"] = 8.0
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 restated connector dimension",
              "unknown=['tool_clearance_mm']")


@test("shared connector mappings must cover every serviced opening",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_connector_opening_coverage():
    fixture = _fresh_fixture()
    _add_second_service_interface(fixture)
    _add_shared_connector_contract(fixture)
    must_fail(run(_validate_args(fixture)), "v2 omitted shared opening",
              "coverage must equal every connector/service opening")


@test("inline and shared connector contracts are mutually exclusive",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_connector_single_authority():
    fixture = _fresh_fixture()
    legacy = copy.deepcopy(_config(fixture)["service_envelopes"])
    _add_shared_connector_contract(fixture)
    config = _config(fixture)
    config["service_envelopes"] = legacy
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 duplicate service authority",
              "are mutually exclusive")


@test("shared connector receipt binding and parse consume one byte subject")
def t_v2_shared_receipt_single_read_subject():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    module = _load_v2_module()
    receipt = fixture["connector_receipt"]
    binding = _binding(fixture["root"], receipt)
    original = module.read_stable_bytes
    receipt_reads = 0

    def counted(path, where):
        nonlocal receipt_reads
        if Path(path) == receipt:
            receipt_reads += 1
        return original(path, where)

    module.read_stable_bytes = counted
    parsed, reopened = module._load_bound_json_bytes(
        binding, fixture["root"], "test receipt")
    eq(receipt_reads, 1, "receipt path read count")
    eq(parsed["subject_sha256"],
       json.loads(receipt.read_text())["subject_sha256"],
       "parsed receipt identity")
    eq(reopened["sha256"], binding["sha256"], "same-byte binding")


@test("receipt-bound compiler bytes are checked before execution",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_compiler_byte_subject():
    module = _load_v2_module()
    compiler = CONNECTOR_COMPILER
    expected = {
        "path": compiler.relative_to(ROOT).as_posix(),
        "sha256": _sha(compiler), "size": compiler.stat().st_size,
    }
    original = module.read_stable_bytes

    def substituted(path, where):
        payload = original(path, where)
        if Path(path) == compiler:
            return payload + b"\n# transient alternate compiler\n"
        return payload

    module.read_stable_bytes = substituted
    try:
        module._connector_compiler_module(expected)
    except module.V2Error as exc:
        contains(str(exc), "identity differs", "compiler substitution failure")
    else:
        raise AssertionError("alternate compiler bytes executed")


@test("shared connector populated neighbors require enclosure association",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_group_populated_member_coverage():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    contract = yaml.safe_load(fixture["connector_contract"].read_text())
    second = copy.deepcopy(contract["assemblies"][0]["instances"][0])
    second["ref"] = "J2"
    contract["assemblies"][0]["instances"].append(second)
    contract["simultaneous_groups"][0]["members"].append("J2")
    _write_yaml(fixture["connector_contract"], contract)
    _recompile_shared_connector(fixture)
    config = _config(fixture)
    config["interface_assemblies"]["non_enclosure_refs"] = [
        _non_enclosure_row("J2"),
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 omitted populated neighbor",
              "omits a populated member from enclosure association")


@test("shared connector groups bind their required population to enclosure states",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_group_state_binding():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    config = _config(fixture)
    config["interface_assemblies"]["group_state_bindings"] = []
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 omitted group state binding",
              "coverage must equal every mapped simultaneous group")


@test("shared connector axes must point through the declared enclosure side",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_axis_side_crosscheck():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    contract = yaml.safe_load(fixture["connector_contract"].read_text())
    contract["assemblies"][0]["instances"][0]["mating_axis_board"] = \
        [0.0, 1.0, 0.0]
    _write_yaml(fixture["connector_contract"], contract)
    _recompile_shared_connector(fixture)
    must_fail(run(_validate_args(fixture)), "v2 flipped connector axis",
              "mating axis contradicts enclosure side north")


@test("schema-v2 report cannot replace shared connector contract",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_input_output_alias():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    before = fixture["connector_contract"].read_bytes()
    must_fail(run([
        *_validate_args(fixture), "--output", fixture["connector_contract"],
    ]), "v2 report aliases connector contract", "destination aliases input file")
    eq(fixture["connector_contract"].read_bytes(), before,
       "connector contract preserved")


@test("schema-v2 report cannot replace shared connector evidence",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_evidence_output_alias():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    before = fixture["connector_evidence"].read_bytes()
    must_fail(run([
        *_validate_args(fixture), "--output", fixture["connector_evidence"],
    ]), "v2 report aliases connector evidence", "destination aliases input file")
    eq(fixture["connector_evidence"].read_bytes(), before,
       "connector evidence preserved")


@test("schema-v2 report cannot replace the shared connector compiler",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_compiler_output_alias():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    before = CONNECTOR_COMPILER.read_bytes()
    must_fail(run([
        *_validate_args(fixture), "--output", CONNECTOR_COMPILER,
    ]), "v2 report aliases connector compiler", "destination aliases input file")
    eq(CONNECTOR_COMPILER.read_bytes(), before, "connector compiler preserved")


@test("schema-v2 output protection includes the exact shared compiler")
def t_v2_shared_compiler_is_protected_input():
    fixture = _fresh_fixture()
    _add_shared_connector_contract(fixture)
    module = _load_v2_module()
    loaded = module.validate_config_v2(
        module.load_yaml(fixture["config"]), fixture["root"])
    protected = set(module._bound_input_paths(loaded))
    check(CONNECTOR_COMPILER.resolve() in protected,
          "shared compiler must be a protected validation input")


@test("published schema-v2 configs may omit the additive service checklist")
def t_v2_legacy_service_envelope_omission():
    fixture = _fresh_fixture()
    config = _config(fixture)
    del config["service_envelopes"]
    _write_yaml(fixture["config"], config)
    result = must_pass(run(_validate_args(fixture)), "v2 legacy service omission")
    report = json.loads(result.out)
    eq(report["service_envelope_coverage"]["legacy_omitted"], True)
    eq(report["service_envelope_coverage"]["legacy_readiness_capped"], True)
    eq(report["service_envelope_coverage"]["declared"], 0)
    eq(report["service_envelope_coverage"]["required_edge_openings"], 1)
    for scope in ("shell", "board_retention", "antenna_accessory", "thermal"):
        eq(report["scope_readiness_ceilings"][scope], "INCOMPLETE")


@test("legacy serviced openings cannot aggregate above INCOMPLETE")
def t_v2_legacy_service_aggregate_ceiling():
    fixture = _fresh_fixture()
    config = _config(fixture)
    del config["service_envelopes"]
    _write_yaml(fixture["config"], config)
    payload = fixture["root"] / "legacy-aggregate.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "CAD_READY", "board_retention": "CAD_READY",
        "antenna_accessory": "CAD_READY", "thermal": "CAD_READY",
    }}) + "\n")
    result = run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ])
    eq(result.rc, 2, "legacy service aggregate exit")
    eq(json.loads(result.out)["status"], "INCOMPLETE")


@test("service envelope separates plug, strain relief, cable, bend, sweep, and allowances",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_envelope_closed_census():
    fixture = _fresh_fixture()
    config = _config(fixture)
    del config["service_envelopes"][0]["strain_relief"]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 partial service envelope",
              "missing=['strain_relief']")


@test("relational physical observations cannot masquerade as dimensions",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_observation_rejects_numeric_envelope():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["service_envelopes"][0]["mated_plug"] = {
        "basis": "physical_observation", "envelope_mm": [10.0, 6.0, 15.0],
    }
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 invented photo dimensions",
              "physical_observation/unknown require a null envelope")


@test("service rows cannot self-assert unbound vendor authority",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_rejects_forged_vendor_basis():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["service_envelopes"][0]["connector_body"]["basis"] = \
        "vendor_authoritative"
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 forged service authority",
              "expected one of ['conservative_candidate', "
              "'physical_observation', 'unknown']")


@test("physical service observations require an exact bound witness",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_observation_requires_bound_subject():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["service_envelopes"][0]["mated_plug"] = {
        "basis": "physical_observation", "envelope_mm": None,
    }
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 unbound fit observation",
              "require a bound first_article_observation external subject")


@test("a dimensionless received-assembly observation caps connector readiness")
def t_v2_service_observation_caps_scope():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["external_subjects"][0]["authority"] = {
        "grade": "first_article_observation",
        "basis": "Synthetic hash-bound physical fit observation.",
        "excluded_claims": [
            "exact_geometry", "clearance", "physical_fit",
            "manufacturing_dimensions",
        ],
    }
    config["service_envelopes"][0]["mated_plug"] = {
        "basis": "physical_observation", "envelope_mm": None,
    }
    config["service_envelopes"][0]["observation_subject"] = \
        "reference_antenna"
    _write_yaml(fixture["config"], config)
    result = must_pass(run(_validate_args(fixture)), "v2 honest fit observation")
    report = json.loads(result.out)
    eq(report["service_envelope_coverage"]
       ["candidate_dimension_census_complete"], 0)
    eq(report["scope_readiness_ceilings"]["antenna_accessory"], "INCOMPLETE")


@test("mated-during operations require both endpoint service states",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_state_linkage():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["service_envelopes"][0]["mated_in_states"] = ["installed"]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 disconnected lid-service cable",
              "does not remain mated in both endpoint states")


@test("mated-during operations require an explicit pre-attached cable",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_operation_cable_condition():
    fixture = _fresh_fixture()
    intent = _intent(fixture)
    intent["operations"][1]["cable_condition"] = "not_applicable"
    _rewrite_intent(fixture, intent)
    must_fail(run(_validate_args(fixture)), "v2 implicit lid-service cable",
              "must declare cable_condition pre_attached")


@test("mated-during operations cannot thread or disconnect the cable",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_operation_forbidden_actions():
    for field, phrase in (
            ("threading_permitted", "cannot thread a cable"),
            ("disconnecting_permitted", "cannot permit disconnecting")):
        fixture = _fresh_fixture()
        intent = _intent(fixture)
        intent["operations"][1][field] = True
        _rewrite_intent(fixture, intent)
        must_fail(run(_validate_args(fixture)),
                  f"v2 mated operation with {field}", phrase)


@test("simultaneous groups share one scope, state census, and operation census",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_simultaneous_group_census():
    mutations = (
        ("scope", "shell", "must share identical scope"),
        ("mated_in_states", [
            "lid_removed_before_antenna",
            "lid_removed_antenna_installed", "installed",
        ], "must share identical mated_in_states"),
        ("mated_during_operations", [],
         "must share identical mated_during_operations"),
    )
    for field, value, phrase in mutations:
        fixture = _fresh_fixture()
        _add_second_service_interface(fixture)
        config = _config(fixture)
        config["service_envelopes"][1][field] = value
        _write_yaml(fixture["config"], config)
        must_fail(run(_validate_args(fixture)),
                  f"v2 split simultaneous group {field}", phrase)


@test("service envelopes cannot hide in an optional scope",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_optional_scope():
    fixture = _fresh_fixture()
    config = _config(fixture)
    for scope in config["verification_scopes"]:
        if scope["id"] == "antenna_accessory":
            scope["required"] = False
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 optional service scope",
              "service-envelope scopes must be required")


@test("service-envelope configs require mating and cable physical tests",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_service_envelope_physical_obligations():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["physical_tests"] = [
        row for row in config["physical_tests"]
        if row["type"] != "all_interfaces_mated"
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 service without mating test",
              "requires PRINT_VERIFIED test all_interfaces_mated")


@test("standalone schema-v2 mechanical intent validates")
def t_v2_clean_intent():
    fixture = _fresh_fixture()
    must_pass(run([KPY, V2, "validate-intent", fixture["intent"]]),
              "v2 clean intent")


@test("derived v2 config requires an exact PCB release manifest",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_derived_manifest_required():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["subject"]["release_manifest"] = None
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 missing release manifest",
              "required for derived mode")


@test("derived release manifest must cover the configured STEP hash",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_manifest_subject_coverage():
    fixture = _fresh_fixture()
    lines = fixture["manifest"].read_text().splitlines()
    fixture["manifest"].write_text("\n".join(lines[:-1]) + "\n")
    config = _config(fixture)
    config["subject"]["release_manifest"] = _binding(
        fixture["root"], fixture["manifest"])
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 incomplete release manifest",
              "subject paths and hashes for ['step']")


@test("derived release manifest binds each selected subject path",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_manifest_wrong_path_bites():
    fixture = _fresh_fixture()
    text = fixture["manifest"].read_text()
    fixture["manifest"].write_text(
        text.replace("board.step", "unrelated.step"), encoding="utf-8")
    config = _config(fixture)
    config["subject"]["release_manifest"] = _binding(
        fixture["root"], fixture["manifest"])
    _write_yaml(fixture["config"], config)
    cad_design = yaml.safe_load(fixture["cad_design"].read_text())
    cad_design["subject"]["release_manifest"] = config["subject"][
        "release_manifest"]
    _rewrite_cad_design(fixture, cad_design)
    config = _config(fixture)
    must_fail(run(_validate_args(fixture)), "v2 wrong-path manifest hash",
              "subject paths and hashes for ['step']")


@test("derived release manifest accepts exact sha256sum path bindings")
def t_v2_sha256sum_manifest():
    fixture = _fresh_fixture()
    rows = []
    for line in fixture["manifest"].read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and len(fields[1]) == 64:
            line = f"{fields[1]}  {fields[0]}"
        rows.append(line)
    fixture["manifest"].write_text("\n".join(rows) + "\n", encoding="utf-8")

    config = _config(fixture)
    config["subject"]["release_manifest"] = _binding(
        fixture["root"], fixture["manifest"])
    _write_yaml(fixture["config"], config)
    cad_design = yaml.safe_load(fixture["cad_design"].read_text())
    cad_design["subject"]["release_manifest"] = config["subject"][
        "release_manifest"]
    _rewrite_cad_design(fixture, cad_design)
    must_pass(run(_validate_args(fixture)), "v2 sha256sum manifest")


@test("sha256sum manifests remain bound to the selected subject path",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_sha256sum_manifest_wrong_path_bites():
    fixture = _fresh_fixture()
    rows = []
    for line in fixture["manifest"].read_text().splitlines():
        fields = line.split()
        if len(fields) == 2 and len(fields[1]) == 64:
            path = "unrelated.step" if fields[0] == "board.step" else fields[0]
            line = f"{fields[1]}  {path}"
        rows.append(line)
    fixture["manifest"].write_text("\n".join(rows) + "\n", encoding="utf-8")

    config = _config(fixture)
    config["subject"]["release_manifest"] = _binding(
        fixture["root"], fixture["manifest"])
    _write_yaml(fixture["config"], config)
    cad_design = yaml.safe_load(fixture["cad_design"].read_text())
    cad_design["subject"]["release_manifest"] = config["subject"][
        "release_manifest"]
    _rewrite_cad_design(fixture, cad_design)
    must_fail(run(_validate_args(fixture)), "v2 sha256sum wrong path",
              "subject paths and hashes for ['step']")


@test("mechanical intent is exactly hash-bound",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_intent_binding_bites():
    fixture = _fresh_fixture()
    fixture["intent"].write_text(fixture["intent"].read_text() + "# changed\n")
    must_fail(run(_validate_args(fixture)), "v2 stale intent binding",
              "bound size/hash differs")


@test("v2 exactly binds the v1 CAD design bytes",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_cad_design_binding_bites():
    fixture = _fresh_fixture()
    fixture["cad_design"].write_text(
        fixture["cad_design"].read_text() + "# changed after binding\n")
    must_fail(run(_validate_args(fixture)), "v2 stale CAD design binding",
              "config.subject.cad_design: bound size/hash differs")


@test("bound v1 CAD design must use the identical PCB-release identity",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_cad_design_release_identity_bites():
    fixture = _fresh_fixture()
    cad_design = yaml.safe_load(fixture["cad_design"].read_text())
    cad_design["subject"]["release"] = "some-other-pcb-release"
    _rewrite_cad_design(fixture, cad_design)
    must_fail(run(_validate_args(fixture)), "v2 mismatched CAD release",
              "v1/v2 release identifiers differ")


@test("bound v1 CAD design cannot substitute a different STEP binding",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_cad_design_step_identity_bites():
    fixture = _fresh_fixture()
    cad_design = yaml.safe_load(fixture["cad_design"].read_text())
    cad_design["subject"]["step"] = cad_design["subject"]["pcb"]
    _rewrite_cad_design(fixture, cad_design)
    must_fail(run(_validate_args(fixture)), "v2 mismatched CAD STEP",
              "v1/v2 step bindings differ")


@test("v2 independent retention must exist in the bound v1 CAD",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_shared_v1_fasteners_bite():
    fixture = _fresh_fixture()
    cad_design = yaml.safe_load(fixture["cad_design"].read_text())
    cad_design["fasteners"]["strategy"] = "shared_board"
    cad_design["fasteners"]["case_holes_mm"] = []
    _rewrite_cad_design(fixture, cad_design)
    must_fail(run(_validate_args(fixture)), "v2 shared v1 screws",
              "requires v1 fasteners.strategy=separate_perimeter")


@test("inspiration geometry must exclude every unsupported claim",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_inspiration_exclusions_bite():
    fixture = _fresh_fixture()
    config = _config(fixture)
    authority = config["external_subjects"][0]["authority"]
    authority["grade"] = "inspiration_only"
    authority["excluded_claims"] = ["exact_geometry", "physical_fit"]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 weak inspiration exclusions",
              "must exclude")


@test("honest inspiration-only installed geometry caps its scope")
def t_v2_inspiration_scope_ceiling():
    fixture = _fresh_fixture()
    config = _config(fixture)
    authority = config["external_subjects"][0]["authority"]
    authority["grade"] = "inspiration_only"
    authority["excluded_claims"] = [
        "exact_geometry", "clearance", "physical_fit",
        "manufacturing_dimensions",
    ]
    _write_yaml(fixture["config"], config)
    result = must_pass(run(_validate_args(fixture)), "v2 honest inspiration")
    report = json.loads(result.out)
    eq(report["scope_readiness_ceilings"]["antenna_accessory"], "INCOMPLETE")


@test("board and closure fastener axes must be disjoint",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_fastener_axes_bite():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["fastener_groups"][1]["axes"][0]["origin_mm"] = [-25, -15, 9]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 shared screw line", "axes overlap")


@test("case closure hardware may not retain the PCB",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_closure_cannot_retain_pcb():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["fastener_groups"][1]["retained_parts"].append("pcb")
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 closure retains PCB",
              "must not retain the PCB")


@test("lid-off state must keep board-retention screws secured",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_lid_off_retention_bites():
    fixture = _fresh_fixture()
    intent = _intent(fixture)
    intent["states"][0]["secured_fastener_groups"] = []
    _rewrite_intent(fixture, intent)
    must_fail(run(_validate_args(fixture)), "v2 unretained lid-off PCB",
              "pcb_retained requires every board_retention group secured")


@test("schema-v2 cannot opt out of independent lid-off PCB retention",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_lid_off_policy_cannot_be_disabled():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["fastener_policy"]["pcb_retained_with_lid_removed"] = False
    intent = _intent(fixture)
    intent["requirements"]["pcb_retained_with_lid_removed"] = False
    _write_yaml(fixture["intent"], intent)
    config["subject"]["mechanical_intent"] = _binding(
        fixture["root"], fixture["intent"])
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 disabled lid-off retention",
              "requires independent lid-off PCB retention")


@test("assembly motion is a checked linear state delta",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_non_linear_motion_bites():
    fixture = _fresh_fixture()
    intent = _intent(fixture)
    intent["operations"][0]["kind"] = "rotate_and_insert"
    _rewrite_intent(fixture, intent)
    must_fail(run(_validate_args(fixture)), "v2 unsupported motion",
              "linear_insert")


@test("prewired no-threading antenna requires full-body clearance",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_cable_only_opening_bites():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["clearance_cases"][0]["envelope_basis"] = "cable_only"
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 cable-only antenna arch",
              "requires full_part")


@test("every assembly operation needs exactly one named clearance case",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_missing_motion_clearance_bites():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["clearance_cases"] = config["clearance_cases"][:1]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 missing lid sweep",
              "every linear operation needs exactly one case")


@test("motion clearance obstacles equal the full source-state assembly",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_partial_obstacle_census_bites():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["clearance_cases"][0]["obstacles"] = ["pcb"]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 omitted base obstacle",
              "must exactly equal every non-moving part")


@test("namespaced custom physical-test types are accepted")
def t_v2_custom_physical_type():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["physical_tests"].append({
        "id": "antenna_torque",
        "type": "custom.pluto.antenna-torque",
        "scope": "antenna_accessory",
        "required_for": "PRINT_VERIFIED",
        "subject_parts": ["lid", "antenna"],
    })
    _write_yaml(fixture["config"], config)
    must_pass(run(_validate_args(fixture)), "v2 custom physical type")


@test("board support clearance is a typed first-article physical test")
def t_v2_board_support_clearance_type():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["physical_tests"].append({
        "id": "board_support_clearance",
        "type": "board_support_clearance",
        "scope": "board_retention",
        "required_for": "PRINT_VERIFIED",
        "subject_parts": ["base", "pcb"],
    })
    _write_yaml(fixture["config"], config)
    must_pass(run(_validate_args(fixture)),
              "v2 board support clearance type")


@test("misspelled physical-test types cannot silently extend the schema",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_bad_physical_type_bites():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["physical_tests"][0]["type"] = "lid_off_retension"
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 mistyped physical test",
              "built-in type or namespaced")


@test("prewired accessory intent requires retention and cable physical tests",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_accessory_physical_obligations_bite():
    fixture = _fresh_fixture()
    config = _config(fixture)
    config["physical_tests"] = [
        row for row in config["physical_tests"]
        if row["type"] != "cable_strain_clearance"
    ]
    _write_yaml(fixture["config"], config)
    must_fail(run(_validate_args(fixture)), "v2 omitted cable physical test",
              "requires PRINT_VERIFIED test cable_strain_clearance")


@test("physical evidence supports extensible print and thermal status")
def t_v2_physical_evidence_status():
    fixture = _fresh_fixture()
    evidence = _physical_evidence(fixture, {"thermal_soak": "NOT_RUN"})
    result = must_pass(run([
        KPY, V2, "validate-evidence", evidence, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 physical evidence")
    report = json.loads(result.out)
    eq(report["status"], "PRINT_VERIFIED")
    eq(report["pending"], ["thermal_soak"])


@test("physical evidence census must exactly match the configuration",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_physical_census_bites():
    fixture = _fresh_fixture()
    evidence = _physical_evidence(fixture)
    value = yaml.safe_load(evidence.read_text())
    value["tests"] = value["tests"][:-1]
    _write_yaml(evidence, value)
    must_fail(run([
        KPY, V2, "validate-evidence", evidence, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 incomplete physical census", "census differs")


@test("a recorded physical failure remains FAIL",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_physical_failure_bites():
    fixture = _fresh_fixture()
    evidence = _physical_evidence(fixture, {"antenna_insertion": "FAIL"})
    result = must_fail(run([
        KPY, V2, "validate-evidence", evidence, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 physical failure")
    report = json.loads(result.out)
    eq(report["status"], "FAIL")
    eq(report["failed"], ["antenna_insertion"])


@test("required scope aggregation cannot hide an incomplete accessory")
def t_v2_conservative_aggregate():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate.json"
    payload.write_text(json.dumps({
        "required_scopes": ["shell", "board_retention", "antenna_accessory"],
        "scope_statuses": {
            "shell": "CAD_READY", "board_retention": "CAD_READY",
            "antenna_accessory": "INCOMPLETE",
        },
        "ceilings": {
            "shell": "THERMALLY_VERIFIED",
            "board_retention": "THERMALLY_VERIFIED",
            "antenna_accessory": "THERMALLY_VERIFIED",
        },
    }) + "\n")
    result = must_pass(run([KPY, V2, "aggregate", payload]),
                       "v2 conservative aggregate")
    eq(json.loads(result.out)["status"], "INCOMPLETE")


@test("authority ceiling prevents an inflated aggregate status")
def t_v2_aggregate_authority_ceiling():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate.json"
    payload.write_text(json.dumps({
        "required_scopes": ["shell", "antenna_accessory"],
        "scope_statuses": {
            "shell": "PRINT_VERIFIED", "antenna_accessory": "PRINT_VERIFIED",
        },
        "ceilings": {
            "shell": "THERMALLY_VERIFIED", "antenna_accessory": "CAD_READY",
        },
    }) + "\n")
    result = must_pass(run([KPY, V2, "aggregate", payload]),
                       "v2 authority-capped aggregate")
    eq(json.loads(result.out)["status"], "CAD_READY")


@test("config-authoritative aggregation derives service-envelope ceilings")
def t_v2_authoritative_aggregate():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate-config.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "CAD_READY", "board_retention": "CAD_READY",
        "antenna_accessory": "CAD_READY", "thermal": "CAD_READY",
    }}) + "\n")
    result = run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ])
    eq(result.rc, 2, "service-envelope aggregate exit")
    report = json.loads(result.out)
    eq(report["status"], "INCOMPLETE")
    eq(report["scope_readiness_ceilings"]["antenna_accessory"],
       "INCOMPLETE")
    eq(set(report["required_scopes"]),
       {"shell", "board_retention", "antenna_accessory", "thermal"})


@test("authoritative aggregation rejects caller-forged ceilings",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_authoritative_aggregate_forged_ceiling_bites():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate-config.json"
    payload.write_text(json.dumps({
        "scope_statuses": {
            "shell": "CAD_READY", "board_retention": "CAD_READY",
            "antenna_accessory": "CAD_READY", "thermal": "CAD_READY",
        },
        "ceilings": {"antenna_accessory": "THERMALLY_VERIFIED"},
    }) + "\n")
    must_fail(run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 forged authoritative ceiling", "unknown=['ceilings']")


@test("authoritative aggregation cannot omit a required accessory scope",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_authoritative_aggregate_omitted_scope_bites():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate-config.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "CAD_READY", "board_retention": "CAD_READY",
        "thermal": "CAD_READY",
    }}) + "\n")
    result = must_fail(run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 omitted required accessory scope")
    eq(json.loads(result.out)["status"], "INCOMPLETE")


@test("aggregation rejects invalid supplied status even when another scope is missing",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_invalid_present_status_with_missing_scope_bites():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate-invalid-present.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "BOGUS", "board_retention": "CAD_READY",
        "thermal": "CAD_READY",
    }}) + "\n")
    must_fail(run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 invalid present status with omitted scope", "invalid status 'BOGUS'")


@test("required scopes pull every transitive dependency into aggregation",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_optional_dependency_cannot_disappear():
    fixture = _fresh_fixture()
    config = _config(fixture)
    for row in config["verification_scopes"]:
        if row["id"] == "thermal":
            row["required"] = False
            row["depends_on"] = []
        if row["id"] == "shell":
            row["depends_on"] = ["thermal"]
    _write_yaml(fixture["config"], config)
    payload = fixture["root"] / "aggregate-config.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "CAD_READY", "board_retention": "CAD_READY",
        "antenna_accessory": "CAD_READY",
    }}) + "\n")
    result = must_fail(run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 missing transitive dependency")
    eq(json.loads(result.out)["status"], "INCOMPLETE")


@test("schema-v2 JSON inputs reject duplicate keys",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_duplicate_json_key_bites():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate-duplicate.json"
    payload.write_text(
        '{"scope_statuses":{},"scope_statuses":{}}\n', encoding="utf-8")
    must_fail(run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 duplicate JSON key", "duplicate JSON key")


@test("schema-v2 reports cannot replace a bound input",
      kind="known_bad", gate="enclosure_v2.py")
def t_v2_output_alias_bites():
    fixture = _fresh_fixture()
    before = fixture["config"].read_bytes()
    must_fail(run([
        KPY, V2, "validate-config", fixture["config"],
        "--root", fixture["root"], "--output", fixture["config"],
    ]), "v2 report aliases config", "destination aliases input file")
    eq(fixture["config"].read_bytes(), before,
       "v2 config preserved after output-alias refusal")


if __name__ == "__main__":
    sys.exit(main())
