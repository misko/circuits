#!/usr/bin/env python3
"""Built-in enclosure-engine geometry contracts.

These tests compile the real OpenSCAD engine and interrogate the resulting
closed mesh.  They prevent a configuration-only fastener check from masking
shared screw axes in the actual split-shell CAD.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

from harness import check, main, test, tmpdir


ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "skills" / "pcb-enclosure" / "assets" / "enclosure-engine.scad"
RENDER = ROOT / "skills" / "pcb-enclosure" / "scripts" / "render_enclosure.py"


def _fixture_source(strategy: str) -> str:
    values = {
        "part": "installed_case",
        "explode": 0,
        "show_reference_board": False,
        "topology": "split_shell",
        "fastener_strategy": strategy,
        "board_size": [60, 40],
        "board_thickness": 1.6,
        "board_mount_holes": [[-15, -10], [15, -10], [-15, 10], [15, 10]],
        "case_holes": [[-25, -15], [25, -15], [-25, 15], [25, 15]],
        "xy_clearance": 1,
        "wall": 2,
        "floor": 2,
        "roof": 2,
        "corner_radius": 4,
        "board_bottom_z": 8,
        "inside_top_z": 20,
        "seam_z": 14,
        "panel_thickness": 2,
        "panel_capture": 1,
        "panel_clearance": 0.2,
        "corner_post_d": 8,
        "lid_column_board_gap": 0.2,
        "lip_h": 1.2,
        "lip_t": 0.8,
        "lip_clearance": 0.25,
        "boss_d": 8,
        "case_post_d": 10,
        "lid_column_d": 7,
        "insert_hole_d": 4,
        "insert_flange_recess_d": 6,
        "insert_flange_recess_depth": 0.8,
        "insert_length": 4,
        "insert_bottom_clearance": 0.2,
        "screw_clearance_d": 3.5,
        "screw_head_d": 6.3,
        "screw_head_recess_depth": 1,
        "ports": [],
        "vents": [],
    }

    def scad(value):
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            return '"' + value + '"'
        if isinstance(value, list):
            return "[" + ",".join(scad(item) for item in value) + "]"
        return str(value)

    prelude = "\n".join(f"{key} = {scad(value)};"
                         for key, value in values.items())
    return prelude + "\n\n" + ENGINE.read_text(encoding="utf-8")


def _triangles(path: Path):
    pending = []
    triangles = []
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if fields[:1] != ["vertex"]:
            continue
        pending.append(tuple(float(value) for value in fields[1:]))
        if len(pending) == 3:
            triangles.append(tuple(pending))
            pending = []
    check(bool(triangles) and not pending, "OpenSCAD emitted malformed ASCII STL")
    return triangles


def _point_inside(triangles, point) -> bool:
    # Non-axis-aligned ray avoids the engine's axis-aligned face diagonals.
    direction = (0.827, 0.341, 0.447)

    def sub(a, b):
        return tuple(a[index] - b[index] for index in range(3))

    def dot(a, b):
        return sum(a[index] * b[index] for index in range(3))

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1],
                a[2] * b[0] - a[0] * b[2],
                a[0] * b[1] - a[1] * b[0])

    hits = []
    for a, b, c in triangles:
        edge1 = sub(b, a)
        edge2 = sub(c, a)
        h = cross(direction, edge2)
        determinant = dot(edge1, h)
        if abs(determinant) < 1e-10:
            continue
        inverse = 1.0 / determinant
        s = sub(point, a)
        u = inverse * dot(s, h)
        if u < -1e-9 or u > 1 + 1e-9:
            continue
        q = cross(s, edge1)
        v = inverse * dot(direction, q)
        if v < -1e-9 or u + v > 1 + 1e-9:
            continue
        distance = inverse * dot(edge2, q)
        if distance > 1e-8 and math.isfinite(distance):
            hits.append(distance)
    # Adjacent triangles on one face yield the same geometric crossing.
    crossings = []
    for distance in sorted(hits):
        if not crossings or abs(distance - crossings[-1]) > 1e-7:
            crossings.append(distance)
    return len(crossings) % 2 == 1


def _compile(strategy: str):
    openscad = shutil.which("openscad")
    check(openscad is not None, "OpenSCAD is required for enclosure engine tests")
    directory = tmpdir(f"pcb_enclosure_engine_{strategy}_")
    source = directory / "fixture.scad"
    output = directory / "installed-case.stl"
    source.write_text(_fixture_source(strategy), encoding="utf-8")
    result = subprocess.run(
        [openscad, "-o", output, source], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False, timeout=120)
    check(result.returncode == 0 and output.is_file() and output.stat().st_size,
          "OpenSCAD engine compilation failed: " + result.stdout[-2000:])
    return _triangles(output)


@test("split-shell separate_perimeter has independent PCB and case screw axes")
def t_split_shell_separate_fasteners_are_geometry():
    mesh = _compile("separate_perimeter")
    # Both independent base posts exist away from their insert cavities.
    check(_point_inside(mesh, (-12.0, -10.0, 5.0)),
          "PCB boss is absent from separate-fastener base")
    check(_point_inside(mesh, (28.0, 15.0, 10.0)),
          "case closure post is absent from separate-fastener base")
    # PCB screws stop at the PCB boss: the roof stays closed on that axis.
    check(_point_inside(mesh, (-15.0, -10.0, 21.0)),
          "separate-fastener lid incorrectly reuses a PCB screw axis")
    # The independent case screw passes through the lid roof.
    check(not _point_inside(mesh, (25.0, 15.0, 21.0)),
          "separate-fastener lid lacks its perimeter clearance bore")


@test("split-shell shared_board retains the legacy shared closure stack")
def t_split_shell_shared_fasteners_remain_compatible():
    mesh = _compile("shared_board")
    check(not _point_inside(mesh, (28.0, 15.0, 10.0)),
          "shared-board base unexpectedly gained a case post")
    check(not _point_inside(mesh, (-15.0, -10.0, 21.0)),
          "shared-board lid lost its PCB-axis clearance bore")
    check(_point_inside(mesh, (25.0, 15.0, 21.0)),
          "shared-board lid unexpectedly gained a perimeter bore")


@test("built-in engine rejects an unknown fastener strategy",
      kind="known_bad", gate="enclosure-engine.scad")
def t_unknown_fastener_strategy_bites():
    openscad = shutil.which("openscad")
    check(openscad is not None, "OpenSCAD is required for enclosure engine tests")
    directory = tmpdir("pcb_enclosure_engine_bad_strategy_")
    source = directory / "fixture.scad"
    output = directory / "should-not-exist.stl"
    source.write_text(_fixture_source("not_a_strategy"), encoding="utf-8")
    result = subprocess.run(
        [openscad, "-o", output, source], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False, timeout=120)
    check("Unknown fastener strategy" in result.stdout,
          "engine did not report the invalid fastener strategy")
    check(not output.is_file() or output.stat().st_size == 0,
          "invalid fastener strategy emitted printable geometry")


@test("headless renderer exits only after its virtual display is reaped")
def t_headless_render_runtime_cleanup():
    check(shutil.which("xvfb-run") is not None,
          "xvfb-run is required for enclosure render tests")
    directory = tmpdir("pcb_enclosure_render_")
    source = directory / "fixture.scad"
    output = directory / "assembly.png"
    source.write_text(_fixture_source("separate_perimeter"), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, RENDER, source, "--output", output,
         "--size", "400,300"], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=False, timeout=120)
    check(result.returncode == 0 and output.read_bytes().startswith(b"\x89PNG"),
          "bounded headless render failed: " + result.stdout[-2000:])


if __name__ == "__main__":
    sys.exit(main())
