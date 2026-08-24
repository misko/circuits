#!/usr/bin/env python3
"""PCB-enclosure gates: exact subjects, interfaces, solids, and packages.

Every bad fixture starts from the same clean, fully hash-bound synthetic case
and changes one property.  No live project or sealed-release byte participates.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import yaml

from harness import (check, contains, eq, main, must_fail, must_pass, run,
                     test, tmpdir)


ROOT = Path(__file__).resolve().parent.parent
ENCLOSURE_SCRIPTS = ROOT / "skills" / "pcb-enclosure" / "scripts"
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


def _fake_cadquery(directory: Path) -> Path:
    """A deterministic exact-backend seam; it does not parse the STEP."""
    directory.mkdir(parents=True, exist_ok=True)
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
        "        return Selection([Shape(Box(-30,-20,0,30,20,1.6)),\n"
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
    interface_path = generated / "board-interface.json"
    config_path = root / "enclosure.yaml"
    pcb.write_text("(kicad_pcb (version 20240108) (generator pcb-enclosure-test))\n")
    step.write_text(_step_text(step_refs), encoding="latin-1")

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
    _write_stl(build / "collision.stl", [((0, 0, 0), (1, 0, 0), (0, 1, 0))])
    (build / "enclosure.scad").write_text("// synthetic enclosure\n")
    parsed_config = yaml.safe_load(config_path.read_text())
    _write_json(build / "generation.json", {
        "schema": 1,
        "kind": "pcb-enclosure-generation-v1",
        "config": {"path": str(config_path),
                   "semantic_sha256": _semantic_sha(parsed_config),
                   "raw_sha256": _sha(config_path)},
        "interface": {"semantic_sha256": _semantic_sha(interface),
                      "raw_sha256": _sha(interface_path)},
        "source": {"path": "enclosure.scad", "sha256": _sha(build / "enclosure.scad"),
                   "size": (build / "enclosure.scad").stat().st_size},
        "parts": [
            {"part": part, "path": f"{part}.stl",
             "sha256": _sha(build / f"{part}.stl"),
             "size": (build / f"{part}.stl").stat().st_size,
             "command": ["synthetic-openscad", part]}
            for part in ("base", "lid", "insert_coupon")
        ],
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
        "geometry": {"status": "COMPLETE", "backend": "synthetic-exact"},
    })
    return {
        "work": work, "root": root, "pcb": pcb, "step": step,
        "interface": interface_path, "config": config_path, "build": build,
        "report": build / "verification.json",
        "collision": build / "collision.stl",
    }


def _verify_args(fixture: dict[str, Path]):
    return [
        KPY, VERIFY, fixture["config"], "--root", fixture["root"],
        "--build-dir", fixture["build"], "--step-inspection",
        fixture["build"] / "step-inspection.json", "--collision-mesh",
        fixture["collision"], "--report", fixture["report"], "--target", "cad",
    ]


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


@test("enclosure verifier refuses an access candidate with no disposition",
      kind="known_bad", gate="verify_enclosure.py")
def t_verify_missing_interface_disposition_bites():
    fixture = _fresh_fixture()
    config = yaml.safe_load(fixture["config"].read_text())
    config["interfaces"] = [row for row in config["interfaces"]
                            if row["ref"] != "SW1"]
    _write_yaml(fixture["config"], config)
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
    must_fail(run(_verify_args(fixture)), "verify_enclosure boss wall",
              "boss radial wall 0.500 < 0.800 mm")
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
    must_fail(run(_verify_args(fixture)), "verify_enclosure collision cancellation",
              "case intersects exact STEP components by 2 mm^3")
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
    eq(report["geometry"]["solid_count"], 2)


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
        manifest = json.loads(archive.read("MANIFEST.json"))
    eq(manifest["status"], "CAD_READY")
    eq(len(manifest["files"]), len(names) - 1, "manifest file denominator")


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


if __name__ == "__main__":
    sys.exit(main())
