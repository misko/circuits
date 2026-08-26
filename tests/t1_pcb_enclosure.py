#!/usr/bin/env python3
"""PCB-enclosure gates: exact subjects, interfaces, solids, and packages.

Every bad fixture starts from the same clean, fully hash-bound synthetic case
and changes one property.  No live project or sealed-release byte participates.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import yaml

from harness import (check, contains, eq, main, must_fail, must_pass, run,
                     test, tmpdir)


ROOT = Path(__file__).resolve().parent.parent
ENCLOSURE_SCRIPTS = ROOT / "skills" / "pcb-enclosure" / "scripts"
sys.path.insert(0, str(ENCLOSURE_SCRIPTS))
from enclosure_common import load_bound_config, stl_metrics  # noqa: E402

VERIFY = ENCLOSURE_SCRIPTS / "verify_enclosure.py"
INSPECT = ENCLOSURE_SCRIPTS / "inspect_step.py"
PACKAGE = ENCLOSURE_SCRIPTS / "package_enclosure.py"
GENERATE = ENCLOSURE_SCRIPTS / "generate_enclosure.py"
KPY = "/usr/bin/python3"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _semantic_sha(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _binding(root: Path, path: Path) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha(path),
        "size": path.stat().st_size,
    }


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _assembly_contract(config: dict, interface: dict) -> dict:
    by_ref = {row["ref"]: row["position_mm"]
              for row in interface["board"]["mounting_holes"]}
    board_axes = [by_ref[ref] for ref in config["fasteners"]["board_holes"]]
    case_axes = config["fasteners"]["case_holes_mm"]
    separate = config["fasteners"]["strategy"] == "separate_perimeter"
    return {
        "kind": "pcb-enclosure-assembly-contract-v1",
        "fastener_strategy": config["fasteners"]["strategy"],
        "board_fastener_axes_mm": board_axes,
        "case_fastener_axes_mm": case_axes,
        "shell_closure_axes_mm": case_axes if separate else board_axes,
        "pcb_retained_with_lid_removed": separate,
        "shared_board_shell_axes": not separate,
    }


def _cube_triangles(offset=(0.0, 0.0, 0.0)):
    ox, oy, oz = offset

    def v(x, y, z):
        return (x + ox, y + oy, z + oz)

    p000, p100, p010, p110 = v(0, 0, 0), v(1, 0, 0), v(0, 1, 0), v(1, 1, 0)
    p001, p101, p011, p111 = v(0, 0, 1), v(1, 0, 1), v(0, 1, 1), v(1, 1, 1)
    return [
        (p000, p010, p110), (p000, p110, p100),  # bottom
        (p001, p101, p111), (p001, p111, p011),  # top
        (p000, p100, p101), (p000, p101, p001),  # south
        (p010, p011, p111), (p010, p111, p110),  # north
        (p000, p001, p011), (p000, p011, p010),  # west
        (p100, p110, p111), (p100, p111, p101),  # east
    ]


def _write_stl(path: Path, triangles) -> None:
    lines = ["solid fixture"]
    for triangle in triangles:
        lines.extend(("  facet normal 0 0 0", "    outer loop"))
        lines.extend(f"      vertex {x:g} {y:g} {z:g}" for x, y, z in triangle)
        lines.extend(("    endloop", "  endfacet"))
    lines.extend(("endsolid fixture", ""))
    path.write_text("\n".join(lines))


def _step_text(refs) -> str:
    occurrences = "\n".join(
        f"#{index}=NEXT_ASSEMBLY_USAGE_OCCURRENCE('id{index}','{ref}',"
        "'','',#1,#2,$);"
        for index, ref in enumerate(refs, 10)
    )
    return (
        "ISO-10303-21;\nHEADER;ENDSEC;\nDATA;\n"
        f"{occurrences}\nENDSEC;\nEND-ISO-10303-21;\n"
    )


def _fake_cadquery(directory: Path, *, duplicate_substrate: bool = False) -> Path:
    """A deterministic exact-backend seam; it does not parse the STEP."""
    directory.mkdir(parents=True, exist_ok=True)
    duplicate = (
        "                          Shape(Box(-30,-20,0,30,20,1.6)),\n"
        if duplicate_substrate else ""
    )
    (directory / "cadquery.py").write_text(
        "class Box:\n"
        "    def __init__(self, xmin, ymin, zmin, xmax, ymax, zmax):\n"
        "        self.xmin=xmin; self.ymin=ymin; self.zmin=zmin\n"
        "        self.xmax=xmax; self.ymax=ymax; self.zmax=zmax\n"
        "        self.xlen=xmax-xmin; self.ylen=ymax-ymin; self.zlen=zmax-zmin\n"
        "class Shape:\n"
        "    def __init__(self, box): self.box=box\n"
        "    def BoundingBox(self): return self.box\n"
        "class Selection:\n"
        "    def __init__(self, values): self.values=values\n"
        "    def vals(self): return self.values\n"
        "class Imported:\n"
        "    def val(self): return Shape(Box(-30,-20,0,30,20,6))\n"
        "    def solids(self):\n"
        "        return Selection([Shape(Box(-29.7,-19.7,-0.035,29.7,19.7,0)),\n"
        "                          Shape(Box(-29.7,-19.7,1.6,29.7,19.7,1.635)),\n"
        "                          Shape(Box(-30,-20,0,30,20,1.6)),\n"
        + duplicate +
        "                          Shape(Box(-2,-2,1.6,2,2,6))])\n"
        "class Importers:\n"
        "    def importStep(self, path): return Imported()\n"
        "importers=Importers()\n"
    )
    return directory


def _fresh_fixture(step_refs=("J1", "SW1")) -> dict[str, Path]:
    work = tmpdir("pcb_enclosure_")
    root = work / "root"
    subject = root / "subject"
    generated = root / "generated"
    build = root / "build"
    subject.mkdir(parents=True)
    generated.mkdir()
    build.mkdir()

    pcb = subject / "synthetic.kicad_pcb"
    step = subject / "synthetic.step"
    release_manifest = subject / "MANIFEST.txt"
    interface_path = generated / "board-interface.json"
    config_path = root / "enclosure.yaml"
    pcb.write_text("(kicad_pcb (version 20240108) (generator pcb-enclosure-test))\n")
    step.write_text(_step_text(step_refs), encoding="latin-1")
    release_manifest.write_text(
        "MANIFEST — synthetic-v1\nDESIGN: PASS\n", encoding="utf-8")

    def footprint(ref, position, model_declared):
        x, y = position
        return {
            "ref": ref, "value": ref, "footprint": "Synthetic_" + ref,
            "position_mm": [x, y], "rotation_deg": 0.0, "side": "front",
            "bbox_mm": [x - 2, y - 2, x + 2, y + 2],
            "model_declared": model_declared,
        }

    footprints = [
        footprint("H1", (-25.0, -15.0), False),
        footprint("H2", (25.0, -15.0), False),
        footprint("H3", (-25.0, 15.0), False),
        footprint("H4", (25.0, 15.0), False),
        footprint("J1", (0.0, -18.0), True),
        footprint("SW1", (0.0, 0.0), True),
    ]
    mounting_holes = [
        {"ref": row[0], "pad": "", "position_mm": list(row[1]),
         "drill_mm": [3.2, 3.2], "attribute": "NPTH"}
        for row in (("H1", (-25.0, -15.0)), ("H2", (25.0, -15.0)),
                    ("H3", (-25.0, 15.0)), ("H4", (25.0, 15.0)))
    ]
    interface = {
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
            "drills": mounting_holes,
            "mounting_holes": mounting_holes,
            "footprints": footprints,
            "access_candidates": [
                {"ref": "J1", "position_mm": [0.0, -18.0], "value": "J1",
                 "footprint": "Synthetic_J1", "selection": "required"},
                {"ref": "SW1", "position_mm": [0.0, 0.0], "value": "SW1",
                 "footprint": "Synthetic_SW1", "selection": "required"},
            ],
        },
        "coverage": {"footprints": len(footprints), "drills": 4,
                     "mounting_holes": 4, "access_candidates": 2},
    }
    _write_json(interface_path, interface)

    config = {
        "schema": 1,
        "kind": "pcb-enclosure-config-v1",
        "name": "synthetic-split-shell",
        "mode": "derived",
        "subject": {
            "release": "synthetic-v1",
            "release_manifest": _binding(root, release_manifest),
            "pcb": _binding(root, pcb),
            "step": _binding(root, step),
            "interface": _binding(root, interface_path),
        },
        "process": {
            "method": "fdm", "material": "PETG", "nozzle_mm": 0.4,
            "layer_mm": 0.2, "support_policy": "forbid_when_practical",
            "minimum_wall_mm": 1.2,
        },
        "cad": {"engine": "openscad", "minimum_version": "2021.01",
                "printable_parts": ["base", "lid", "insert_coupon"]},
        "geometry": {
            "topology": "split_shell", "xy_clearance_mm": 1.0,
            "wall_mm": 2.0, "floor_mm": 2.0, "roof_mm": 2.0,
            "corner_radius_mm": 4.0, "board_bottom_z_mm": 8.0,
            "inside_top_z_mm": 20.0, "seam_z_mm": 15.0,
            "panel_thickness_mm": 2.0, "panel_capture_mm": 1.0,
            "panel_clearance_mm": 0.2, "corner_post_mm": 8.0,
            "lid_column_board_gap_mm": 0.15,
        },
        "fasteners": {
            "strategy": "shared_board", "thread": "M3-0.5",
            "board_holes": ["H1", "H2", "H3", "H4"],
            "case_holes_mm": [], "boss_d_mm": 8.0,
            "case_post_d_mm": 8.0, "minimum_radial_wall_mm": 0.8,
            "insert": {
                "family": "synthetic-flanged-M3", "installation": "cold_press",
                "hole_d_mm": 4.0, "body_d_mm": 4.2, "flange_d_mm": 5.5,
                "flange_recess_d_mm": 6.0, "flange_recess_depth_mm": 0.8,
                "length_mm": 4.0, "bottom_clearance_mm": 0.2,
            },
            "screw": {
                "clearance_d_mm": 3.4, "head_d_mm": 6.0,
                "head_recess_depth_mm": 1.0, "board_length_mm": 6.0,
                "lid_length_mm": 17.0, "minimum_engagement_mm": 3.0,
                "minimum_tip_clearance_mm": 0.0,
            },
        },
        "interfaces": [
            {
                "id": "usb", "ref": "J1", "role": "data-and-power",
                "side": "south", "disposition": "opening",
                "center_mm": [0.0, -20.0, 10.0], "shape": "rect",
                "opening_mm": [12.0, 8.0],
                "plug_envelope_mm": [10.0, 6.0, 15.0], "clearance_mm": 1.0,
            },
            {
                "id": "switch", "ref": "SW1", "role": "configuration",
                "side": "top", "disposition": "internal",
                "center_mm": [0.0, 0.0, 0.0], "shape": "none",
                "opening_mm": [0.0, 0.0],
                "plug_envelope_mm": [0.0, 0.0, 0.0], "clearance_mm": 0.0,
            },
        ],
        "thermal": {"risk": "low", "physical_soak_required": False,
                    "load_case": "synthetic room-temperature load", "vents": []},
        "physical_validation": {
            "insert_coupon_required": True, "board_drop_in_required": True,
            "all_interfaces_mated_required": True, "thermal_soak_required": False,
        },
    }
    _write_yaml(config_path, config)

    _write_stl(build / "base.stl", _cube_triangles())
    _write_stl(build / "lid.stl", _cube_triangles())
    _write_stl(build / "insert_coupon.stl", _cube_triangles())
    # A zero-thickness result is the portable representation of an empty
    # intersection for this synthetic exact-solid seam.
    _write_stl(build / "collision.stl", [((0, 0, 0), (0, 0, 0), (0, 0, 0))])
    _write_stl(build / "components.stl", _cube_triangles((4, 4, 4)))
    _write_stl(build / "assembled-case.stl", _cube_triangles())
    (build / "enclosure.scad").write_text("// synthetic enclosure\n")
    parsed_config = yaml.safe_load(config_path.read_text())
    installed_case_record = {
        "selector": "installed_case", "path": "assembled-case.stl",
        "sha256": _sha(build / "assembled-case.stl"),
        "size": (build / "assembled-case.stl").stat().st_size,
        "command": [
            "synthetic-openscad", "-o", str((build / "assembled-case.stl").resolve()),
            "-D", 'part="installed_case"', "-D", "show_reference_board=false",
            str((build / "enclosure.scad").resolve()),
        ],
    }
    _write_json(build / "generation.json", {
        "schema": 1,
        "kind": "pcb-enclosure-generation-v1",
        "engine": {"executable": "synthetic-openscad", "version": "synthetic",
                   "minimum_version": "2021.01"},
        "config": {"path": str(config_path),
                   "semantic_sha256": _semantic_sha(parsed_config),
                   "raw_sha256": _sha(config_path)},
        "interface": {"semantic_sha256": _semantic_sha(interface),
                      "raw_sha256": _sha(interface_path)},
        "source": {"path": "enclosure.scad", "sha256": _sha(build / "enclosure.scad"),
                   "size": (build / "enclosure.scad").stat().st_size},
        "authority": {"kind": "built_in_v1"},
        "assembly_contract": _assembly_contract(parsed_config, interface),
        "parts": [
            {"part": part, "path": f"{part}.stl",
             "sha256": _sha(build / f"{part}.stl"),
             "size": (build / f"{part}.stl").stat().st_size,
             "command": ["synthetic-openscad", part]}
            for part in ("base", "lid", "insert_coupon")
        ],
        "installed_case": installed_case_record,
    })
    _write_json(build / "step-inspection.json", {
        "schema": 1,
        "kind": "pcb-enclosure-step-inspection-v1",
        "status": "COMPLETE",
        "step": {"path": step.name, "sha256": _sha(step),
                 "size": step.stat().st_size},
        "interface": {"path": interface_path.name,
                      "sha256": _sha(interface_path),
                      "size": interface_path.stat().st_size},
        "occurrence_coverage": {
            "status": "COMPLETE", "expected_modeled_refs": 2,
            "observed_designators": 2, "covered_modeled_refs": 2,
            "missing_modeled_refs": [], "unmodeled_access_refs": [],
        },
        "geometry": {
            "status": "COMPLETE", "backend": "synthetic-exact",
            "solid_count": 2, "component_solid_count": 1,
            "pcb_related_solid_indices": [0],
            "case_registration_translate_mm_at_board_z0": [0.0, 0.0, 0.0],
            "component_mesh": _binding(build, build / "components.stl"),
        },
    })
    collision_metrics = stl_metrics(build / "collision.stl")
    _write_json(build / "collision.json", {
        "schema": 1, "kind": "pcb-enclosure-collision-v1", "status": "COMPLETE",
        "backend": {"name": "synthetic-exact"},
        "inputs": {
            "step_inspection": _binding(build, build / "step-inspection.json"),
            "step": _binding(root, step),
            "component_mesh": _binding(build, build / "components.stl"),
            "generation": _binding(build, build / "generation.json"),
            "assembled_case_mesh": installed_case_record,
        },
        "transform": {
            "case_registration_translate_mm_at_board_z0": [0.0, 0.0, 0.0],
            "board_bottom_z_mm": config["geometry"]["board_bottom_z_mm"],
            "applied_component_translate_mm": [
                0.0, 0.0, config["geometry"]["board_bottom_z_mm"]],
        },
        "selection": {"step_solid_count": 2, "pcb_related_solid_count": 1,
                      "component_solid_count": 1},
        "result": {
            "classification": "EMPTY", "exact_brep_volume_mm3": 0.0,
            "representation": "zero-area-marker-for-empty-brep",
            "collision_mesh": _binding(build, build / "collision.stl"),
            "mesh_metrics": collision_metrics,
        },
    })
    return {
        "work": work, "root": root, "pcb": pcb, "step": step,
        "release_manifest": release_manifest,
        "interface": interface_path, "config": config_path, "build": build,
        "report": build / "verification.json",
        "collision": build / "collision.stl",
        "collision_report": build / "collision.json",
    }


def _verify_args(fixture: dict[str, Path]):
    return [
        KPY, VERIFY, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--step-inspection",
        fixture["build"] / "step-inspection.json", "--collision-mesh",
        fixture["collision"], "--collision-report", fixture["collision_report"],
        "--report", fixture["report"], "--target", "cad",
    ]


def _refresh_collision_receipt(fixture: dict[str, Path], volume: float) -> None:
    receipt = json.loads(fixture["collision_report"].read_text())
    generation = json.loads((fixture["build"] / "generation.json").read_text())
    receipt["inputs"]["generation"] = _binding(
        fixture["build"], fixture["build"] / "generation.json")
    receipt["inputs"]["assembled_case_mesh"] = generation["installed_case"]
    metrics = stl_metrics(fixture["collision"])
    receipt["result"].update({
        "classification": "INTERSECTION" if volume else "EMPTY",
        "exact_brep_volume_mm3": volume,
        "representation": ("tessellation-of-exact-brep-common" if volume else
                           "zero-area-marker-for-empty-brep"),
        "collision_mesh": _binding(fixture["build"], fixture["collision"]),
        "mesh_metrics": metrics,
    })
    _write_json(fixture["collision_report"], receipt)


def _refresh_generation_config(fixture: dict[str, Path]) -> None:
    generation_path = fixture["build"] / "generation.json"
    generation = json.loads(generation_path.read_text())
    config = yaml.safe_load(fixture["config"].read_text())
    generation["config"]["raw_sha256"] = _sha(fixture["config"])
    generation["config"]["semantic_sha256"] = _semantic_sha(config)
    interface = json.loads(fixture["interface"].read_text())
    generation["assembly_contract"] = _assembly_contract(config, interface)
    _write_json(generation_path, generation)
    collision = json.loads(fixture["collision_report"].read_text())
    _refresh_collision_receipt(
        fixture, float(collision["result"]["exact_brep_volume_mm3"]))


def _enable_authored_scad(fixture: dict[str, Path]) -> Path:
    authored_dir = fixture["root"] / "authored"
    authored_dir.mkdir()
    authored = authored_dir / "reviewed-case.scad"
    authored.write_text(
        'part = "assembly";\n'
        'module printable() { cube([1, 1, 1]); }\n'
        'if (part == "base") printable();\n'
        'else if (part == "lid") printable();\n'
        'else if (part == "insert_coupon") printable();\n'
        'else { printable(); }\n',
        encoding="utf-8",
    )
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["source"] = {
        "kind": "authored_scad",
        **_binding(fixture["root"], authored),
    }
    _write_yaml(fixture["config"], config)
    return authored


def _replace_authored_scad(fixture: dict[str, Path], authored: Path,
                           source: str) -> None:
    authored.write_text(source, encoding="utf-8")
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["source"] = {
        "kind": "authored_scad",
        **_binding(fixture["root"], authored),
    }
    _write_yaml(fixture["config"], config)


def _assert_only_failed(fixture: dict[str, Path], check_name: str) -> None:
    report = json.loads(fixture["report"].read_text())
    eq(report["status"], "FAIL", "overall verification status")
    failed = [row["name"] for row in report["checks"] if row["status"] == "FAIL"]
    eq(failed, [check_name], "isolated failing check")


@test("enclosure verifier reaches CAD_READY on a complete synthetic subject")
def t_verify_clean_subject():
    fixture = _fresh_fixture()
    result = must_pass(run(_verify_args(fixture)), "verify_enclosure clean fixture")
    contains(result.out, "ENCLOSURE VERDICT CAD_READY", "clean verifier output")
    report = json.loads(fixture["report"].read_text())
    eq(report["summary"], {"failed": 0, "incomplete": 1, "passed": 6,
                           "total": 7}, "verification denominators")
    eq(report["checks"][-1]["name"], "physical_evidence")


@test("the built-in generator refuses to approximate an irregular outline",
      kind="known_bad")
def t_generator_irregular_outline_bites():
    fixture = _fresh_fixture()
    interface = json.loads(fixture["interface"].read_text())
    interface["board"]["outline"]["contours_mm"][0][2][0] = 29.0
    _write_json(fixture["interface"], interface)
    config = yaml.safe_load(fixture["config"].read_text())
    config["subject"]["interface"] = _binding(fixture["root"],
                                                fixture["interface"])
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure irregular outline", "axis-aligned rectangle only")


@test("built-in generation emits the fixed installed-case selector")
def t_generator_installed_case_clean():
    fixture = _fresh_fixture()
    must_pass(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure installed case")
    generation = json.loads((fixture["build"] / "generation.json").read_text())
    installed = generation["installed_case"]
    eq(installed["selector"], "installed_case", "fixed selector")
    eq(installed["path"], "assembled-case.stl", "fixed artifact name")
    eq(installed["command"][3:7],
       ["-D", 'part="installed_case"', "-D", "show_reference_board=false"],
       "fixed selector command")
    check((fixture["build"] / "assembled-case.stl").is_file(),
          "installed-case artifact was not generated")


@test("coupon-qualified FDM pilot may exceed nominal cold-press body")
def t_coupon_qualified_pilot_clean():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    insert = config["fasteners"]["insert"]
    insert["hole_d_mm"] = 4.25
    insert["pilot_basis"] = "coupon_qualified"
    _write_yaml(fixture["config"], config)
    loaded, _ = load_bound_config(fixture["config"], fixture["root"])
    eq(loaded["fasteners"]["insert"]["hole_d_mm"], 4.25,
       "qualified modeled pilot")
    eq(loaded["fasteners"]["insert"]["body_d_mm"], 4.2,
       "nominal hardware body remains truthful")


@test("oversize nominal cold-press pilot needs explicit coupon basis",
      kind="known_bad", gate="generate_enclosure.py")
def t_unqualified_oversize_pilot_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["fasteners"]["insert"]["hole_d_mm"] = 4.25
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure unqualified pilot",
        "cold-press pilot lacks nominal interference")


@test("authored-SCAD generation and package preserve the exact bound source")
def t_authored_scad_clean_round_trip():
    fixture = _fresh_fixture()
    authored = _enable_authored_scad(fixture)
    must_pass(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure authored SCAD")
    eq((fixture["build"] / "enclosure.scad").read_bytes(),
       authored.read_bytes(), "build copy must preserve authored source bytes")
    generation = json.loads((fixture["build"] / "generation.json").read_text())
    expected_binding = _binding(fixture["root"], authored)
    eq(generation["authority"], {
        "kind": "authored_scad", "binding": expected_binding,
    }, "generation CAD authority")
    eq(generation["installed_case"]["selector"], "installed_case",
       "fixed installed-case selector")
    eq(generation["installed_case"]["path"], "assembled-case.stl",
       "installed-case artifact name")
    _refresh_collision_receipt(fixture, 0.0)

    must_pass(run(_verify_args(fixture)), "verification before authored package")
    output = fixture["build"] / "authored.zip"
    must_pass(run([
        KPY, PACKAGE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--output", output,
    ]), "package_enclosure authored SCAD")
    with zipfile.ZipFile(output) as archive:
        eq(archive.read("cad/enclosure.scad"), authored.read_bytes(),
           "package must carry exact authored source bytes")
        manifest = json.loads(archive.read("MANIFEST.json"))
    eq(manifest["cad_authority"], generation["authority"],
       "package CAD authority")


@test("authored SCAD may declare receipt-bound custom printable selectors")
def t_authored_scad_custom_printable_clean():
    fixture = _fresh_fixture()
    authored = _enable_authored_scad(fixture)
    _replace_authored_scad(
        fixture, authored,
        'part = "assembly";\n'
        'module printable() { cube([1, 1, 1]); }\n'
        'if (part == "base") printable();\n'
        'else if (part == "lid") printable();\n'
        'else if (part == "insert_coupon") printable();\n'
        'else if (part == "fixture_accessory") printable();\n'
        'else if (part == "fixture_fit_coupon") printable();\n'
        'else if (part == "installed_case") printable();\n'
        'else if (part == "assembly") printable();\n')
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].extend([
        "fixture_accessory", "fixture_fit_coupon",
    ])
    _write_yaml(fixture["config"], config)
    must_pass(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure custom authored selectors")
    generation = json.loads((fixture["build"] / "generation.json").read_text())
    eq([row["part"] for row in generation["parts"]],
       config["cad"]["printable_parts"], "custom selector receipt census")
    eq(generation["selector_contract"]["custom"],
       ["fixture_accessory", "fixture_fit_coupon"],
       "custom selector contract census")
    eq(generation["selector_contract"]["mesh_canonicalization"],
       "ascii-stl-facet-order-v1", "custom mesh canonicalization contract")
    first_meshes = {
        row["part"]: row["sha256"] for row in generation["parts"]
    }
    first_installed = generation["installed_case"]["sha256"]
    must_pass(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "repeat custom authored generation")
    repeated = json.loads((fixture["build"] / "generation.json").read_text())
    eq({row["part"]: row["sha256"] for row in repeated["parts"]},
       first_meshes, "custom mesh hashes must replay deterministically")
    eq(repeated["installed_case"]["sha256"], first_installed,
       "installed-case hash must replay deterministically")
    check((fixture["build"] / "fixture_accessory.stl").is_file(),
          "custom accessory mesh absent")
    check((fixture["build"] / "fixture_fit_coupon.stl").is_file(),
          "custom fit-coupon mesh absent")
    _refresh_collision_receipt(fixture, 0.0)
    must_pass(run(_verify_args(fixture)),
              "verification with custom authored selectors")
    output = fixture["build"] / "custom-authored.zip"
    must_pass(run([
        KPY, PACKAGE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--output", output,
    ]), "package_enclosure custom authored selectors")
    with zipfile.ZipFile(output) as archive:
        check("meshes/fixture_accessory.stl" in archive.namelist(),
              "custom accessory absent from package")
        check("meshes/fixture_fit_coupon.stl" in archive.namelist(),
              "custom fit coupon absent from package")


@test("built-in CAD cannot claim an unimplemented custom selector",
      kind="known_bad", gate="generate_enclosure.py")
def t_built_in_custom_printable_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].append("fixture_accessory")
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure built-in custom selector",
        "custom printable selectors require authored_scad")


@test("authored custom selectors reject catch-all unknown output",
      kind="known_bad", gate="generate_enclosure.py")
def t_authored_open_custom_selector_bites():
    fixture = _fresh_fixture()
    _enable_authored_scad(fixture)
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].append("fixture_accessory")
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure open authored selectors",
        "unknown selector generated geometry")


@test("authored custom selector must be implemented by the bound source",
      kind="known_bad", gate="generate_enclosure.py")
def t_authored_unimplemented_custom_selector_bites():
    fixture = _fresh_fixture()
    authored = _enable_authored_scad(fixture)
    _replace_authored_scad(
        fixture, authored,
        'part = "assembly";\n'
        'module printable() { cube([1, 1, 1]); }\n'
        'if (part == "base") printable();\n'
        'else if (part == "lid") printable();\n'
        'else if (part == "insert_coupon") printable();\n'
        'else if (part == "installed_case") printable();\n'
        'else if (part == "assembly") printable();\n')
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].append("fixture_accessory")
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure unimplemented authored selector",
        "could not generate fixture_accessory")


@test("authored custom selectors remain unique",
      kind="known_bad", gate="generate_enclosure.py")
def t_authored_duplicate_custom_selector_bites():
    fixture = _fresh_fixture()
    _enable_authored_scad(fixture)
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].extend([
        "fixture_accessory", "fixture_accessory",
    ])
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure duplicate authored selector",
        "expected non-empty unique list")


@test("authored custom selectors are traversal-safe identifiers",
      kind="known_bad", gate="generate_enclosure.py")
def t_authored_unsafe_custom_printable_bites():
    fixture = _fresh_fixture()
    _enable_authored_scad(fixture)
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].append("../fixture")
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure unsafe authored selector",
        "expected lowercase selector")


@test("installed_case remains a reserved non-printable selector",
      kind="known_bad", gate="generate_enclosure.py")
def t_authored_installed_case_printable_bites():
    fixture = _fresh_fixture()
    _enable_authored_scad(fixture)
    config = yaml.safe_load(fixture["config"].read_text())
    config["cad"]["printable_parts"].append("installed_case")
    _write_yaml(fixture["config"], config)
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure installed_case printable",
        "reserved for verification")


@test("authored-SCAD generation refuses a changed source binding",
      kind="known_bad", gate="generate_enclosure.py")
def t_authored_scad_stale_binding_bites():
    fixture = _fresh_fixture()
    authored = _enable_authored_scad(fixture)
    authored.write_text(authored.read_text().replace(
        "cube([1, 1, 1])", "cube([2, 1, 1])"), encoding="utf-8")
    must_fail(run([
        KPY, GENERATE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"],
    ]), "generate_enclosure stale authored SCAD",
        "config.cad.source: bound size/hash differs from actual file")


@test("enclosure verifier refuses a changed PCB subject hash",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_subject_hash_bites():
    fixture = _fresh_fixture()
    original = fixture["pcb"].read_text()
    fixture["pcb"].write_text(original.replace("pcb-enclosure-test",
                                                 "pcb-enclosure-best"))
    eq(fixture["pcb"].stat().st_size,
       yaml.safe_load(fixture["config"].read_text())["subject"]["pcb"]["size"],
       "hash-only mutation preserves subject size")
    result = must_fail(run(_verify_args(fixture)), "verify_enclosure stale PCB",
                       "bound size/hash differs from actual file")
    contains(result.out, "ENCLOSURE VERIFICATION FAIL", "subject-hash failure")


@test("enclosure verifier refuses a changed PCB release manifest",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_release_manifest_hash_bites():
    fixture = _fresh_fixture()
    manifest = fixture["release_manifest"]
    manifest.write_text(
        manifest.read_text().replace("DESIGN: PASS", "DESIGN: FAIL"),
        encoding="utf-8")
    must_fail(run(_verify_args(fixture)),
              "verify_enclosure stale release manifest",
              "config.subject.release_manifest: bound size/hash differs")


@test("enclosure verifier refuses an access candidate with no disposition",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_missing_interface_disposition_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["interfaces"] = [row for row in config["interfaces"]
                            if row["ref"] != "SW1"]
    _write_yaml(fixture["config"], config)
    _refresh_generation_config(fixture)
    result = must_fail(run(_verify_args(fixture)), "verify_enclosure disposition",
                       "access candidate SW1 has no disposition")
    _assert_only_failed(fixture, "interface_coverage")


@test("enclosure verifier refuses an undersize insert boss",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_undersize_boss_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["fasteners"]["boss_d_mm"] = 7.0
    _write_yaml(fixture["config"], config)
    _refresh_generation_config(fixture)
    must_fail(run(_verify_args(fixture)), "verify_enclosure boss wall",
              "boss radial wall 0.500 < 0.800 mm")
    _assert_only_failed(fixture, "fastener_geometry")


@test("separate board and case fasteners cannot reuse or overlap screw axes",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_overlapping_independent_fasteners_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["fasteners"]["strategy"] = "separate_perimeter"
    config["fasteners"]["case_holes_mm"] = [
        [-25.0, -15.0], [25.0, -15.0], [-25.0, 15.0], [25.0, 15.0],
    ]
    config["fasteners"]["screw"]["board_length_mm"] = 5.0
    config["fasteners"]["screw"]["lid_length_mm"] = 5.0
    _write_yaml(fixture["config"], config)
    _refresh_generation_config(fixture)
    must_fail(run(_verify_args(fixture)),
              "verify_enclosure overlapping independent axes",
              "posts require >= 8.000 mm")
    _assert_only_failed(fixture, "fastener_geometry")


@test("enclosure verifier refuses a non-manifold printable STL",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_nonmanifold_mesh_bites():
    fixture = _fresh_fixture()
    _write_stl(fixture["build"] / "base.stl", _cube_triangles()[:-1])
    must_fail(run(_verify_args(fixture)), "verify_enclosure non-manifold mesh",
              "non-two-use edge(s)")
    _assert_only_failed(fixture, "printable_meshes")


@test("enclosure verifier refuses disconnected printable geometry",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_disconnected_mesh_bites():
    fixture = _fresh_fixture()
    triangles = _cube_triangles() + _cube_triangles((3.0, 0.0, 0.0))
    _write_stl(fixture["build"] / "base.stl", triangles)
    must_fail(run(_verify_args(fixture)), "verify_enclosure disconnected mesh",
              "expected 1 component, got 2")
    _assert_only_failed(fixture, "printable_meshes")


@test("enclosure verifier refuses nonzero exact-solid intersection volume",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_collision_volume_bites():
    fixture = _fresh_fixture()
    _write_stl(fixture["collision"], _cube_triangles())
    _refresh_collision_receipt(fixture, 1.0)
    must_fail(run(_verify_args(fixture)), "verify_enclosure collision",
              "case intersects exact STEP components by 1 mm^3")
    _assert_only_failed(fixture, "exact_solid_clearance")


@test("oppositely oriented collision solids cannot cancel their volume",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_collision_component_volume_cannot_cancel():
    fixture = _fresh_fixture()
    first = _cube_triangles()
    second = [tuple(reversed(triangle))
              for triangle in _cube_triangles((3.0, 0.0, 0.0))]
    _write_stl(fixture["collision"], first + second)
    _refresh_collision_receipt(fixture, 2.0)
    must_fail(run(_verify_args(fixture)), "verify_enclosure collision cancellation",
              "case intersects exact STEP components by 2 mm^3")
    _assert_only_failed(fixture, "exact_solid_clearance")


@test("enclosure verifier refuses a collision mesh changed after its receipt",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_stale_collision_receipt_bites():
    fixture = _fresh_fixture()
    _write_stl(fixture["collision"], _cube_triangles())
    must_fail(run(_verify_args(fixture)), "verify_enclosure stale collision receipt",
              "collision mesh: file differs from its receipt")
    _assert_only_failed(fixture, "exact_solid_clearance")


@test("enclosure verifier refuses an arbitrary case mesh outside generation",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_unproven_installed_case_bites():
    fixture = _fresh_fixture()
    _write_stl(fixture["build"] / "assembled-case.stl",
               _cube_triangles((100.0, 100.0, 100.0)))
    collision = json.loads(fixture["collision_report"].read_text())
    supplied = dict(collision["inputs"]["assembled_case_mesh"])
    supplied.update(_binding(fixture["build"],
                             fixture["build"] / "assembled-case.stl"))
    collision["inputs"]["assembled_case_mesh"] = supplied
    _write_json(fixture["collision_report"], collision)
    must_fail(run(_verify_args(fixture)), "verify_enclosure unproven case",
              "generated installed-case mesh: file differs from its receipt")
    _assert_only_failed(fixture, "exact_solid_clearance")


@test("supplied physical FAIL evidence cannot hide behind CAD_READY",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_supplied_physical_failure_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    evidence = fixture["build"] / "physical-evidence.yaml"
    _write_yaml(evidence, {
        "schema": 1,
        "kind": "pcb-enclosure-physical-evidence-v1",
        "config_semantic_sha256": _semantic_sha(config),
        "tests": {
            "insert_coupon": {"status": "FAIL", "evidence": "boss split"},
            "board_drop_in": {"status": "PASS", "evidence": "dated photo"},
            "all_interfaces_mated": {"status": "PASS", "evidence": "dated photo"},
            "thermal_soak": {"status": "NOT_RUN", "evidence": "not required"},
        },
    })
    args = _verify_args(fixture)
    args[args.index("--report"):args.index("--report")] = [
        "--physical-evidence", evidence,
    ]
    must_fail(run(args), "verify_enclosure physical failure",
              "physical test insert_coupon records FAIL")
    _assert_only_failed(fixture, "physical_evidence")


@test("STEP inspector covers every modeled footprint with an exact backend")
def t_step_inspector_clean_coverage():
    fixture = _fresh_fixture()
    fake_modules = _fake_cadquery(fixture["work"] / "fake_modules")
    output = fixture["build"] / "inspector-clean.json"
    result = must_pass(run([
        KPY, INSPECT, fixture["step"], "--interface", fixture["interface"],
        "--output", output,
    ], env={"PYTHONPATH": str(fake_modules)}), "inspect_step clean fixture")
    contains(result.out, "2/2 modeled footprint refs covered")
    report = json.loads(output.read_text())
    eq(report["status"], "COMPLETE")
    eq(report["geometry"]["solid_count"], 4)
    eq(report["geometry"]["component_solid_count"], 1)
    eq(report["geometry"]["pcb_related_solid_indices"], [0, 1, 2])


@test("STEP inspector refuses two board-thickness substrate solids",
      kind="known_bad", gate="inspect_step.py")
def t_step_inspector_duplicate_substrate_bites():
    fixture = _fresh_fixture()
    fake_modules = _fake_cadquery(
        fixture["work"] / "fake_modules", duplicate_substrate=True)
    output = fixture["build"] / "inspector-ambiguous.json"
    must_fail(run([
        KPY, INSPECT, fixture["step"], "--interface", fixture["interface"],
        "--output", output,
    ], env={"PYTHONPATH": str(fake_modules)}),
        "inspect_step duplicate substrate")
    report = json.loads(output.read_text())
    eq(report["occurrence_coverage"]["status"], "COMPLETE")
    eq(report["geometry"]["status"], "FAIL")
    contains(report["geometry"]["reason"], "substrate_candidates=[2, 3]",
             "ambiguous substrate reason")


@test("STEP inspector refuses one missing modeled footprint occurrence",
      kind="known_bad", gate="inspect_step.py")
def t_step_inspector_missing_occurrence_bites():
    fixture = _fresh_fixture(step_refs=("SW1",))
    fake_modules = _fake_cadquery(fixture["work"] / "fake_modules")
    output = fixture["build"] / "inspector-bad.json"
    result = must_fail(run([
        KPY, INSPECT, fixture["step"], "--interface", fixture["interface"],
        "--output", output,
    ], env={"PYTHONPATH": str(fake_modules)}), "inspect_step missing model", "J1")
    contains(result.out, "1/2 modeled footprint refs covered")
    report = json.loads(output.read_text())
    eq(report["occurrence_coverage"]["missing_modeled_refs"], ["J1"])
    eq(report["geometry"]["status"], "COMPLETE",
       "adjacent exact-geometry property")


@test("STEP inspector refuses a zero modeled-footprint denominator",
      kind="known_bad", gate="inspect_step.py")
def t_step_inspector_zero_denominator_bites():
    fixture = _fresh_fixture(step_refs=())
    interface = json.loads(fixture["interface"].read_text())
    for footprint in interface["board"]["footprints"]:
        footprint["model_declared"] = False
    interface["board"]["access_candidates"] = []
    interface["coverage"]["access_candidates"] = 0
    _write_json(fixture["interface"], interface)
    fake_modules = _fake_cadquery(fixture["work"] / "fake_modules")
    output = fixture["build"] / "inspector-zero.json"
    result = must_fail(run([
        KPY, INSPECT, fixture["step"], "--interface", fixture["interface"],
        "--output", output,
    ], env={"PYTHONPATH": str(fake_modules)}),
        "inspect_step zero denominator", "modeled footprint denominator is zero")
    report = json.loads(output.read_text())
    eq(report["occurrence_coverage"]["expected_modeled_refs"], 0)
    eq(report["occurrence_coverage"]["zero_modeled_denominator"], True)


@test("enclosure package is deterministic and carries its manifest")
def t_package_clean_is_deterministic():
    fixture = _fresh_fixture()
    must_pass(run(_verify_args(fixture)), "verification before package")
    first = fixture["build"] / "first.zip"
    second = fixture["build"] / "second.zip"
    for output in (first, second):
        must_pass(run([
            KPY, PACKAGE, fixture["config"], "--root", fixture["root"],
            "--build-dir", fixture["build"], "--output", output,
        ]), "package_enclosure clean fixture")
    eq(_sha(first), _sha(second), "deterministic package digest")
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        check(names[0] == "MANIFEST.json", "manifest must be first")
        check("meshes/base.stl" in names, "printable mesh absent from package")
        check("verification/collision.json" in names,
              "exact-collision receipt absent from package")
        check("verification/assembled-case.stl" in names,
              "assembled-case collision subject absent from package")
        check("subject/pcb-release-MANIFEST.txt" in names,
              "sealed PCB release identity absent from package")
        check("replay/enclosure.yaml" in names,
              "replayable path-rebased config absent from package")
        manifest = json.loads(archive.read("MANIFEST.json"))
        unpacked = fixture["work"] / "unpacked"
        archive.extractall(unpacked)
    eq(manifest["status"], "CAD_READY")
    eq(len(manifest["files"]), len(names) - 1, "manifest file denominator")
    eq(manifest["based_on"]["release"], "synthetic-v1",
       "PCB release dependency label")
    eq(manifest["based_on"]["manifest"]["sha256"],
       _sha(fixture["release_manifest"]), "PCB release manifest identity")
    replay_config, replay_loaded = load_bound_config(
        unpacked / manifest["replay"]["config"], unpacked)
    eq(_semantic_sha(replay_config), manifest["replay"]["semantic_sha256"],
       "replay config semantic identity")
    eq(replay_loaded["bindings"]["pcb"]["actual_sha256"], _sha(fixture["pcb"]),
       "replay PCB binding")
    eq(replay_loaded["bindings"]["release_manifest"]["actual_sha256"],
       _sha(fixture["release_manifest"]), "replay release binding")


@test("enclosure package refuses an incomplete verification by default",
      kind="known_bad", gate="package_enclosure.py")
def t_package_incomplete_verification_bites():
    fixture = _fresh_fixture()
    must_pass(run(_verify_args(fixture)), "verification before bad package")
    report = json.loads(fixture["report"].read_text())
    report["status"] = "INCOMPLETE"
    _write_json(fixture["report"], report)
    output = fixture["build"] / "should-not-exist.zip"
    must_fail(run([
        KPY, PACKAGE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--output", output,
    ]), "package_enclosure incomplete verification",
              "verification status INCOMPLETE")
    check(not output.exists(), "failed package run published an archive")


@test("enclosure package refuses a mesh changed after verification",
      kind="known_bad", gate="package_enclosure.py")
def t_package_stale_mesh_bites():
    fixture = _fresh_fixture()
    must_pass(run(_verify_args(fixture)), "verification before stale package")
    base = fixture["build"] / "base.stl"
    base.write_text(base.read_text() + "\n")
    output = fixture["build"] / "stale.zip"
    must_fail(run([
        KPY, PACKAGE, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--output", output,
    ]), "package_enclosure stale mesh", "generated mesh base: file changed")
    check(not output.exists(), "stale package run published an archive")


@test("enclosure verifier report cannot overwrite a bound input",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_report_alias_bites():
    fixture = _fresh_fixture()
    before = fixture["config"].read_bytes()
    args = list(_verify_args(fixture))
    args[args.index("--report") + 1] = fixture["config"]
    must_fail(run(args), "verification report aliases config",
              "verification report must be the canonical build artifact")
    eq(fixture["config"].read_bytes(), before,
       "verification alias refusal preserved config")


@test("enclosure verifier rejects linked build meshes",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_linked_meshes_bite():
    for kind in ("symlink", "hardlink"):
        fixture = _fresh_fixture()
        base = fixture["build"] / "base.stl"
        outside = fixture["work"] / f"outside-{kind}.stl"
        outside.write_bytes(base.read_bytes())
        base.unlink()
        if kind == "symlink":
            os.symlink(outside, base)
            expected = "symlink path component"
        else:
            os.link(outside, base)
            expected = "hard-linked files are not accepted"
        must_fail(run(_verify_args(fixture)), f"verification {kind} mesh",
                  expected)


@test("schema-v1 physical readiness cannot use a zero acceptance denominator",
      kind="known_bad", gate="enclosure_common.py")
def t_zero_physical_acceptance_denominator_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["physical_validation"].update({
        "insert_coupon_required": False,
        "board_drop_in_required": False,
        "all_interfaces_mated_required": False,
        "thermal_soak_required": False,
    })
    config["thermal"]["physical_soak_required"] = False
    _write_yaml(fixture["config"], config)
    must_fail(
        run(_verify_args(fixture)), "zero physical acceptance denominator",
        "a zero physical acceptance denominator cannot authorize")


if __name__ == "__main__":
    sys.exit(main())
