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
    semantic_sha256, sha256_file, stl_metrics, write_json,
)


def check(name: str, status: str, graded: int, total: int,
          findings: Sequence[str] = (), **evidence: Any) -> dict[str, Any]:
    if status not in {"PASS", "FAIL", "INCOMPLETE", "NOT_APPLICABLE"}:
        raise EnclosureError(f"internal status error for {name}: {status}")
    if total < 0 or graded < 0 or graded > total:
        raise EnclosureError(f"internal denominator error for {name}")
    return {"name": name, "status": status, "graded": graded, "total": total,
            "findings": list(findings), "evidence": evidence}


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
    for row in interface["board"]["mounting_holes"]:
        mount_counts[row["ref"]] = mount_counts.get(row["ref"], 0) + 1
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
        fixed_checks += 6
    total = fixed_checks + len(f["board_holes"])
    return check("fastener_geometry", "FAIL" if findings else "PASS",
                 max(0, total - len(findings)), total, findings, **evidence)


def _mesh_check(config: Mapping[str, Any], build_dir: Path) -> dict[str, Any]:
    parts = config["cad"]["printable_parts"]
    findings = []
    metrics = {}
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
    return check("printable_meshes", "FAIL" if findings else "PASS",
                 len(parts) - len({item.split(":", 1)[0] for item in findings}),
                 len(parts), findings, parts=metrics,
                 support_policy=config["process"]["support_policy"])


def _clearance_check(config: Mapping[str, Any], step_report_path: Path | None,
                     collision_mesh: Path | None,
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
    try:
        mesh = stl_metrics(collision_mesh)
    except EnclosureError as exc:
        return check("exact_solid_clearance", "FAIL", 1, 2,
                     [f"collision mesh unreadable: {exc}"],
                     step_inspection=report, step_inspection_file=report_file)
    volume = mesh["component_absolute_volume_mm3"]
    if volume > collision_tolerance:
        findings.append(
            f"case intersects exact STEP components by {volume:.6g} mm^3 "
            f"> {collision_tolerance:.6g} mm^3")
    return check("exact_solid_clearance", "FAIL" if findings else "PASS",
                 2 if not findings else 1, 2, findings,
                 step_inspection=report, step_inspection_file=report_file,
                 collision_mesh=mesh,
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
           collision_tolerance: float, physical_evidence: Path | None) -> dict[str, Any]:
    config, loaded = load_bound_config(config_path, root)
    config_hash = semantic_sha256(config)
    checks = [
        _subject_check(loaded),
        _interface_check(config, loaded["interface"]),
        _fastener_check(config, loaded["interface"]),
        _mesh_check(config, build_dir),
        _clearance_check(config, step_report, collision_mesh, collision_tolerance),
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
        report = verify(args.config, args.root, args.build_dir,
                        args.step_inspection, args.collision_mesh,
                        args.collision_tolerance_mm3, args.physical_evidence)
        write_json(args.report, report)
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
