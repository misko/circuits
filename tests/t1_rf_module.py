#!/usr/bin/env python3
"""T1: conditional RF context, source geometry and bounded solver module."""
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

CONTEXT = SCRIPTS / "rf_context.py"
CHECK = SCRIPTS / "rf_check.py"
SOLVER = SCRIPTS / "rf_solver.py"


def source_project(*, blocking=False):
    root = tmpdir("rfmodule_")
    (root / "03_src/rules").mkdir(parents=True)
    (root / "06_build/rf").mkdir(parents=True)
    process = ({"profile": "rf-module-v1", "context_policy": "clean_room",
                "geometry_policy": "blocking"} if blocking else None)
    rf = {
        "enabled": True, "rationale": "controlled RF fixture",
        "risk_tier": "microwave", "risk_basis": "six gigahertz route",
        "ports": [{"id": "RF", "nets": ["RF1"], "band_hz": [1e6, 6e9],
                   "z0_ohm": 50, "launch": "SMA", "termination": "50 ohm",
                   "reference_layer": "In1.Cu"}],
        "cross_sections": [{"id": "CPWG", "status": "locked",
                            "stackup_source": "JLC named stackup",
                            "solver": "retained local result",
                            "copper_layer": "F.Cu", "reference_layer": "In1.Cu",
                            "dielectric_height_mm": 0.2, "dk": 4.4,
                            "target_z0_ohm": 50, "width_mm": 0.3,
                            "gap_mm": 0.2}],
        "layout_constraints": {
            "route": {"nets": ["RF1"], "layer": "F.Cu",
                      "reference_layer": "In1.Cu", "width_mm": 0.3,
                      "gap_to_top_ground_mm": 0.2,
                      "maximum_vias_per_net": 0,
                      "maximum_stubs_per_net": 0,
                      "length_matching": "not required for one path",
                      "geometry": "short branch-free line",
                      "bend_policy": {
                          "minimum_radius_width_multiple": 3.0,
                          "source_claim_ids": ["ADI-RF-BEND-RADIUS-3W"],
                          "exceptions": []}},
            "ground_fence": {"maximum_along_route_pitch_mm": 1.4,
                             "nominal_lateral_center_offset_mm": 0.7,
                             "maximum_lateral_center_offset_mm": 1.1}},
    }
    if process:
        rf["process"] = process
    (root / "03_src/rules/rf.yaml").write_text(
        yaml.safe_dump({"schema": 1, "rf": rf}, sort_keys=False))
    route = {
        "project": {"name": "fixture", "board": "04_kicad/fixture.kicad_pcb",
                    "build_dir": "06_build/route"},
        "prep": {"seed_stubs": {"stubs": [{
            "net": "RF1", "segments": [{"layer": "F.Cu", "width": 0.3,
                                           "pts": [[0, 0], [5, 0], [7, 2]]}]
        }]}},
        "stitch": {"route_fence": {"band": 1.1}},
    }
    (root / "03_src/route.yaml").write_text(yaml.safe_dump(route, sort_keys=False))
    return root


@test("non-RF source and realized gates are immediate N-A without route or board")
def t_non_rf_shallow_na():
    root = tmpdir("rfmodule_na_")
    (root / "03_src/rules").mkdir(parents=True)
    (root / "03_src/rules/rf.yaml").write_text(
        yaml.safe_dump({"schema": 1, "rf": {"enabled": False,
                                              "rationale": "no RF nets"}},
                       sort_keys=False))
    source = must_pass(run([KPY, CHECK, "source", root]),
                       "non-RF source applicability")
    realized = must_pass(run([KPY, CHECK, "realized", root]),
                         "non-RF realized applicability")
    contains(source.out, "1/1 applicability", "source N-A denominator")
    contains(realized.out, "1/1 applicability", "realized N-A denominator")


@test("RF context clean-room selection excludes precedent and creates no wait")
def t_context_clean_room():
    root = source_project()
    archive = root / "cards.yaml"
    base = {"title": "Source", "publisher": "Vendor", "locator": "DOC",
            "topics": ["controlled_impedance", "bend_geometry", "via_fence"],
            "selectors": ["bend_geometry"], "claim": "claim", "use": "use",
            "limits": "limits"}
    archive.write_text(yaml.safe_dump({"schema": 1, "sources": [
        {"id": "NORM", "provenance": "normative", **base},
        {"id": "OLD-BOARD", "provenance": "precedent", **base},
    ]}, sort_keys=False))
    out = root / "06_build/rf/context"
    r = must_pass(run([KPY, CONTEXT, root, "--archive", archive, "--out", out]),
                  "clean-room RF context")
    contains(r.out, "1/1 context bundle", "context coverage")
    value = json.loads((out / "context.json").read_text())
    eq(value["selected_source_ids"], ["NORM"], "clean-room sources")
    check(value["runtime_network"] is False, "context enabled network")
    check(value["review_wait_created"] is False, "context created a wait")


@test("legacy sharp RF source geometry is visible but advisory")
def t_source_advisory():
    root = source_project()
    out = root / "06_build/rf/source"
    must_pass(run([KPY, CHECK, "source", root, "--out", out]),
              "advisory RF source geometry")
    report = json.loads((out / "report.json").read_text())
    eq(report["coverage"], {"graded": 1, "total": 1}, "RF net coverage")
    eq(len(report["bend_findings"]), 1, "sharp turn inventory")
    eq(report["verdict"], "PASS", "advisory verdict")


@test("RF source corners cannot hide at YAML segment-list boundaries")
def t_source_segment_boundary_corner():
    root = source_project()
    route_path = root / "03_src/route.yaml"
    route = yaml.safe_load(route_path.read_text())
    route["prep"]["seed_stubs"]["stubs"][0]["segments"] = [
        {"layer": "F.Cu", "width": 0.3, "pts": [[0, 0], [5, 0]]},
        {"layer": "F.Cu", "width": 0.3, "pts": [[5, 0], [7, 2]]},
    ]
    route_path.write_text(yaml.safe_dump(route, sort_keys=False))
    out = root / "06_build/rf/source"
    must_pass(run([KPY, CHECK, "source", root, "--out", out]),
              "split source geometry")
    report = json.loads((out / "report.json").read_text())
    eq(len(report["bend_findings"]), 1, "split-list sharp turn inventory")


@test("blocking RF accepts a tangent 3W arc and rejects a kinked arc join")
def t_source_arc_tangency():
    arc = {"layer": "F.Cu", "width": 0.3, "start": [5, 0],
           "mid": [5.707107, 0.292893], "end": [6, 1]}

    smooth = source_project(blocking=True)
    route_path = smooth / "03_src/route.yaml"
    route = yaml.safe_load(route_path.read_text())
    bank = route["prep"]["seed_stubs"]["stubs"][0]
    bank["segments"] = [{"layer": "F.Cu", "width": 0.3,
                          "pts": [[0, 0], [5, 0]]}]
    bank["arcs"] = [arc]
    route_path.write_text(yaml.safe_dump(route, sort_keys=False))
    must_pass(run([KPY, CONTEXT, smooth]), "smooth-arc RF context")
    must_pass(run([KPY, CHECK, "source", smooth]),
              "tangent radius-compliant RF arc")

    kinked = source_project(blocking=True)
    route_path = kinked / "03_src/route.yaml"
    route = yaml.safe_load(route_path.read_text())
    bank = route["prep"]["seed_stubs"]["stubs"][0]
    bank["segments"] = [{"layer": "F.Cu", "width": 0.3,
                          "pts": [[5, -2], [5, 0]]}]
    bank["arcs"] = [arc]
    route_path.write_text(yaml.safe_dump(route, sort_keys=False))
    must_pass(run([KPY, CONTEXT, kinked]), "kinked-arc RF context")
    must_fail(run([KPY, CHECK, "source", kinked]),
              "non-tangent line/arc junction", "unrounded")


@test("adopted blocking RF geometry rejects the same sharp corner",
      kind="known_bad")
def t_source_blocking_rejects_corner():
    root = source_project(blocking=True)
    must_pass(run([KPY, CONTEXT, root]), "blocking project context")
    must_fail(run([KPY, CHECK, "source", root]), "blocking sharp corner",
              "unrounded")


def solver_project(*, timeout=False):
    root = tmpdir("rfsolver_")
    (root / "03_src/rules").mkdir(parents=True)
    (root / "input.txt").write_text("stackup input\n")
    if timeout:
        command = [KPY, "-c", "import time; time.sleep(3)"]
        limit = 1
    else:
        command = [KPY, "-c",
                   "import json,pathlib,sys; pathlib.Path(sys.argv[1]).write_text(json.dumps({'z0':50})+'\\n')",
                   "{output_dir}/result.json"]
        limit = 5
    rf = {
        "enabled": True, "rationale": "pending local solver fixture",
        "cross_sections": [{"id": "CPWG", "status": "pending_solver"}],
        "analysis": {"solver_jobs": [{
            "id": "cpwg", "cross_section_ids": ["CPWG"],
            "work_class": "local_compute", "network": False,
            "command": command, "inputs": ["input.txt"],
            "outputs": ["result.json"], "timeout_s": limit,
            "heartbeat_s": 1}]},
    }
    (root / "03_src/rules/rf.yaml").write_text(
        yaml.safe_dump({"schema": 1, "rf": rf}, sort_keys=False))
    return root


@test("pending RF solver job is bounded, publishes, and exact rerun is cached")
def t_solver_bounded_cache():
    root = solver_project()
    first = must_pass(run([KPY, SOLVER, root]), "local RF solver")
    contains(first.out, "1/1 pending cross-sections", "solver denominator")
    manifest = root / "06_build/rf/solver/cpwg/bundle.json"
    before = hashlib.sha256(manifest.read_bytes()).hexdigest()
    second = must_pass(run([KPY, SOLVER, root]), "cached local RF solver")
    contains(second.out, "cached exact bundle", "solver cache")
    eq(hashlib.sha256(manifest.read_bytes()).hexdigest(), before,
       "cached solver manifest hash")


@test("quiet RF solver is terminated at its hard deadline", kind="known_bad")
def t_solver_timeout():
    root = solver_project(timeout=True)
    r = must_fail(run([KPY, SOLVER, root], timeout=10), "timed-out RF solver",
                  "TIMEOUT")
    contains(r.out, "coverage: 0/1", "timeout coverage")


if __name__ == "__main__":
    sys.exit(main())
