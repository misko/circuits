#!/usr/bin/env python3
"""Schema-v2 enclosure contracts: authority, service, motion, and evidence."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

from harness import check, contains, eq, main, must_fail, must_pass, run, test, tmpdir


ROOT = Path(__file__).resolve().parent.parent
V2 = ROOT / "skills" / "pcb-enclosure" / "scripts" / "enclosure_v2.py"
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
                "cable_condition": "not_applicable",
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
            "side": "south", "disposition": "opening",
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
            {"id": "thermal_soak", "type": "thermal_soak", "scope": "thermal",
             "required_for": "THERMALLY_VERIFIED",
             "subject_parts": ["base", "lid", "pcb"]},
        ],
    }
    _write_yaml(config_path, config)
    return {"root": root, "config": config_path, "intent": intent_path,
            "manifest": manifest_path, "antenna": antenna,
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
    eq(report["scope_readiness_ceilings"]["antenna_accessory"],
       "THERMALLY_VERIFIED")


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


@test("config-authoritative aggregation derives applicability and ceilings")
def t_v2_authoritative_aggregate():
    fixture = _fresh_fixture()
    payload = fixture["root"] / "aggregate-config.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "CAD_READY", "board_retention": "CAD_READY",
        "antenna_accessory": "CAD_READY", "thermal": "CAD_READY",
    }}) + "\n")
    result = must_pass(run([
        KPY, V2, "aggregate-config", payload, "--config", fixture["config"],
        "--root", fixture["root"],
    ]), "v2 authoritative aggregate")
    report = json.loads(result.out)
    eq(report["status"], "CAD_READY")
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
