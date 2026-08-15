#!/usr/bin/env python3
"""RF-CONTRACT: validate RF intent and exact-artifact review coverage.

RF work is conditional, but the condition is explicit.  A new project carries
``03_src/rules/rf.yaml`` with ``rf.enabled`` true or false.  When true, the
file names every RF port, cross-section, performance claim, first-article
measurement, and the exact artifacts/review files used by the three dedicated
RF review phases (schematic, PCB, fabrication output).

Review coverage is derived from requirement IDs, not trusted from a typed
count.  Every required ID must appear exactly once as
``requirement: <ID> PASS`` in the corresponding review, and the review must
bind the SHA256 of its declared artifact.  Zero requirements is a schema
failure, never a successful 0/0 review.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import yaml

PHASES = ("schematic", "pcb", "fab")
RISK_TIERS = {
    "ordinary-high-speed", "controlled-impedance", "phase-coherent",
    "microwave",
}
REVIEW_KIND = {
    "schematic": "RF_SCHEMATIC",
    "pcb": "RF_PCB",
    "fab": "RF_FAB",
}


class ContractError(RuntimeError):
    pass


def _mapping(value, label):
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a mapping")
    return value


def _nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def _substantive(value, label):
    text = _nonempty(value, label)
    if re.fullmatch(r"(?i)(tbd|todo|unknown|n/?a|none|pending)", text):
        raise ContractError(f"{label} must be substantive, not {text!r}")
    return text


def _list(value, label, minimum=1):
    if not isinstance(value, list) or len(value) < minimum:
        raise ContractError(f"{label} must be a list with >= {minimum} item(s)")
    return value


def _inside(project: Path, value, label) -> Path:
    path = (project / _nonempty(value, label)).resolve()
    try:
        path.relative_to(project)
    except ValueError as exc:
        raise ContractError(f"{label} must stay inside the project: {path}") from exc
    return path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(name)}:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else ""


def _requirements(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).upper()) for m in re.finditer(
        r"(?im)^\s*requirement:\s*([A-Za-z0-9_.-]+)\s+"
        r"(PASS|FAIL)\s*$", text)]


def _evidence_bindings(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).lower()) for m in re.finditer(
        r"(?im)^\s*evidence_sha256:\s*([A-Za-z0-9_.-]+)\s+"
        r"([0-9a-f]{64})\s*$", text)]


def _bundle_error(path: Path, role: str, artifact: Path,
                  contract_path: Path | None = None) -> str:
    """Validate an RF evidence manifest and its exact primary subject."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        return f"cannot parse evidence bundle {path}: {exc}"
    if (not isinstance(data, dict) or data.get("schema") != 1
            or data.get("status") != "PASS"):
        return f"evidence bundle {path} is not a schema-1 PASS manifest"
    outputs = data.get("outputs") or {}
    if not isinstance(outputs, dict) or "report.json" not in outputs:
        return f"evidence bundle {path} does not declare report.json"
    for name, facts in outputs.items():
        candidate = Path(str(name))
        if (candidate.is_absolute() or not candidate.parts
                or any(part in ("", ".", "..") for part in candidate.parts)):
            return f"evidence bundle {path} has unsafe output name {name!r}"
        output_path = path.parent / candidate
        if not output_path.is_file() or output_path.is_symlink():
            return f"evidence bundle output is missing or unsafe: {output_path}"
        if not isinstance(facts, dict):
            return f"evidence bundle output metadata is invalid for {name}"
        try:
            recorded_size = int(facts.get("size"))
        except (TypeError, ValueError):
            return f"evidence bundle output size is invalid for {name}"
        if (recorded_size != output_path.stat().st_size
                or facts.get("sha256") != _sha256(output_path)):
            return f"evidence bundle output hash/size is stale for {name}"
    expected_producer = {"rf_source_bundle": "rf_check.py source",
                         "rf_realized_bundle": "rf_check.py realized"}.get(role)
    if expected_producer and data.get("producer") != expected_producer:
        return (f"evidence producer is {data.get('producer') or 'UNSTATED'}, "
                f"expected {expected_producer}")
    try:
        report = yaml.safe_load(
            (path.parent / "report.json").read_text(encoding="utf-8-sig")) or {}
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        return f"cannot parse evidence report.json: {exc}"
    expected_mode = {"rf_source_bundle": "source",
                     "rf_realized_bundle": "realized"}.get(role)
    if (not isinstance(report, dict) or report.get("schema") != 1
            or report.get("verdict") != "PASS"
            or (expected_mode and report.get("mode") != expected_mode)):
        return (f"evidence report.json is not a schema-1 PASS "
                f"{expected_mode or 'RF'} report")
    if contract_path is not None:
        expected_contract = _sha256(contract_path)
        actual_contract = ((data.get("inputs") or {}).get("rf.yaml") or {}).get(
            "sha256")
        if actual_contract != expected_contract:
            return (f"evidence RF-contract hash is "
                    f"{actual_contract or 'UNSTATED'}, expected current "
                    f"contract {expected_contract}")
    if role == "rf_realized_bundle":
        expected = _sha256(artifact)
        actual = ((data.get("inputs") or {}).get("board.kicad_pcb") or {}).get(
            "sha256")
        if actual != expected:
            return (f"realized evidence board hash is {actual or 'UNSTATED'}, "
                    f"expected exact artifact {expected}")
        if report.get("board_sha256") != expected:
            return (f"realized report board hash is "
                    f"{report.get('board_sha256') or 'UNSTATED'}, expected "
                    f"exact artifact {expected}")
    return ""


def load_contract(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc
    root = _mapping(data, "rf.yaml root")
    if root.get("schema") != 1:
        raise ContractError("rf.yaml schema must be integer 1")
    rf = _mapping(root.get("rf"), "rf")
    if not isinstance(rf.get("enabled"), bool):
        raise ContractError("rf.enabled must be true or false")
    _nonempty(rf.get("rationale"), "rf.rationale")
    return root


def validate_enabled(project: Path, contract: dict,
                     required_phases=(), contract_path: Path | None = None
                     ) -> dict[str, dict]:
    rf = contract["rf"]
    process = rf.get("process")
    adopted_rf_module = process is not None
    if adopted_rf_module:
        process = _mapping(process, "rf.process")
        if process.get("profile") != "rf-module-v1":
            raise ContractError("rf.process.profile must be rf-module-v1")
        if process.get("context_policy") not in (
                "clean_room", "allow_precedent"):
            raise ContractError(
                "rf.process.context_policy must be clean_room or allow_precedent")
        if process.get("geometry_policy") not in ("advisory", "blocking"):
            raise ContractError(
                "rf.process.geometry_policy must be advisory or blocking")
        if process.get("geometry_stage", "source") not in ("source", "placement"):
            raise ContractError(
                "rf.process.geometry_stage must be source or placement")
    tier = _nonempty(rf.get("risk_tier"), "rf.risk_tier")
    if tier not in RISK_TIERS:
        raise ContractError(
            f"rf.risk_tier {tier!r} is not one of {sorted(RISK_TIERS)}")
    _nonempty(rf.get("risk_basis"), "rf.risk_basis")

    ports = _list(rf.get("ports"), "rf.ports")
    port_ids = set()
    for index, raw in enumerate(ports):
        port = _mapping(raw, f"rf.ports[{index}]")
        ident = _nonempty(port.get("id"), f"rf.ports[{index}].id")
        if ident in port_ids:
            raise ContractError(f"duplicate RF port id {ident!r}")
        port_ids.add(ident)
        nets = _list(port.get("nets"), f"rf.ports[{index}].nets")
        for j, net in enumerate(nets):
            _nonempty(net, f"rf.ports[{index}].nets[{j}]")
        band = port.get("band_hz")
        if not isinstance(band, list) or len(band) != 2 \
                or not all(isinstance(v, (int, float)) for v in band) \
                or not 0 <= band[0] < band[1]:
            raise ContractError(
                f"rf.ports[{index}].band_hz must be [low, high], 0 <= low < high")
        if not isinstance(port.get("z0_ohm"), (int, float)) \
                or not 20 <= float(port["z0_ohm"]) <= 150:
            raise ContractError(f"rf.ports[{index}].z0_ohm must be 20..150")
        for key in ("launch", "termination", "reference_layer"):
            _nonempty(port.get(key), f"rf.ports[{index}].{key}")

    sections = _list(rf.get("cross_sections"), "rf.cross_sections")
    section_ids = set()
    pending_sections = []
    for index, raw in enumerate(sections):
        section = _mapping(raw, f"rf.cross_sections[{index}]")
        ident = _nonempty(section.get("id"), f"rf.cross_sections[{index}].id")
        if ident in section_ids:
            raise ContractError(f"duplicate RF cross-section id {ident!r}")
        section_ids.add(ident)
        for key in ("stackup_source", "solver", "copper_layer",
                    "reference_layer"):
            _nonempty(section.get(key), f"rf.cross_sections[{index}].{key}")
        for key in ("dielectric_height_mm", "dk", "target_z0_ohm"):
            if not isinstance(section.get(key), (int, float)) \
                    or float(section[key]) <= 0:
                raise ContractError(
                    f"rf.cross_sections[{index}].{key} must be > 0")
        status = section.get("status", "locked")
        if status not in ("locked", "pending_solver"):
            raise ContractError(
                f"rf.cross_sections[{index}].status must be locked or "
                "pending_solver")
        if status == "pending_solver":
            _substantive(section.get("deferred_until"),
                         f"rf.cross_sections[{index}].deferred_until")
            _substantive(section.get("reason"),
                         f"rf.cross_sections[{index}].reason")
            for key in ("width_mm", "gap_mm"):
                if section.get(key) is not None:
                    raise ContractError(
                        f"rf.cross_sections[{index}].{key} must be null while "
                        "status is pending_solver; do not publish an "
                        "unapproved geometry")
            pending_sections.append(ident)
        else:
            for key in ("width_mm", "gap_mm"):
                if not isinstance(section.get(key), (int, float)) \
                        or float(section[key]) <= 0:
                    raise ContractError(
                        f"rf.cross_sections[{index}].{key} must be > 0 when "
                        "status is locked")

    analysis = rf.get("analysis")
    if analysis is not None:
        analysis = _mapping(analysis, "rf.analysis")
        jobs = analysis.get("solver_jobs") or []
        if not isinstance(jobs, list):
            raise ContractError("rf.analysis.solver_jobs must be a list")
        job_ids, covered_sections = set(), []
        for i, raw in enumerate(jobs):
            job = _mapping(raw, f"rf.analysis.solver_jobs[{i}]")
            ident = _nonempty(job.get("id"), f"rf.analysis.solver_jobs[{i}].id")
            if ident in job_ids:
                raise ContractError(f"duplicate RF solver job {ident!r}")
            job_ids.add(ident)
            if job.get("work_class") != "local_compute":
                raise ContractError(
                    f"rf.analysis.solver_jobs[{i}].work_class must be local_compute")
            if job.get("network") is not False:
                raise ContractError(
                    f"rf.analysis.solver_jobs[{i}].network must be false")
            section_refs = _list(
                job.get("cross_section_ids"),
                f"rf.analysis.solver_jobs[{i}].cross_section_ids")
            for j, section_id in enumerate(section_refs):
                section_id = _nonempty(
                    section_id,
                    f"rf.analysis.solver_jobs[{i}].cross_section_ids[{j}]")
                if section_id not in section_ids:
                    raise ContractError(
                        f"RF solver job {ident!r} names unknown cross-section "
                        f"{section_id!r}")
                covered_sections.append(section_id)
            command = _list(job.get("command"),
                            f"rf.analysis.solver_jobs[{i}].command")
            for j, value in enumerate(command):
                _nonempty(value, f"rf.analysis.solver_jobs[{i}].command[{j}]")
            for key in ("inputs", "outputs"):
                values = _list(job.get(key),
                               f"rf.analysis.solver_jobs[{i}].{key}")
                for j, value in enumerate(values):
                    _nonempty(value,
                              f"rf.analysis.solver_jobs[{i}].{key}[{j}]")
            timeout = job.get("timeout_s")
            heartbeat = job.get("heartbeat_s")
            if (not isinstance(timeout, (int, float)) or isinstance(timeout, bool)
                    or not 1 <= float(timeout) <= 300):
                raise ContractError("RF solver timeout_s must be within 1..300")
            if (not isinstance(heartbeat, (int, float))
                    or isinstance(heartbeat, bool)
                    or not 1 <= float(heartbeat) <= min(30, float(timeout))):
                raise ContractError(
                    "RF solver heartbeat_s must be within 1..min(30, timeout_s)")
        duplicate_coverage = sorted({value for value in covered_sections
                                     if covered_sections.count(value) > 1})
        if duplicate_coverage:
            raise ContractError(
                f"RF solver jobs duplicate cross-section coverage {duplicate_coverage}")
        if adopted_rf_module and set(covered_sections) != set(pending_sections):
            raise ContractError(
                "rf-module-v1 solver jobs must cover exactly the pending "
                f"cross-sections; jobs={sorted(covered_sections)}, "
                f"pending={sorted(pending_sections)}")
    elif adopted_rf_module and pending_sections:
        raise ContractError(
            "rf-module-v1 pending cross-sections require rf.analysis.solver_jobs")

    # RF layout is optional before geometry work begins, but once declared it
    # is executable authority: the route-following emitter and the independent
    # saved-board fence gate both consume it.  Validate the complete block and
    # reconcile it with the port/cross-section authorities here so a copied
    # net list, layer, width, gap or fence number cannot drift silently.
    layout_raw = rf.get("layout_constraints")
    if (adopted_rf_module
            and process.get("geometry_stage", "source") == "source"
            and layout_raw is None and not pending_sections):
        raise ContractError(
            "rf-module-v1 source-stage geometry requires layout_constraints; "
            "use process.geometry_stage: placement only when coordinates are "
            "deliberately deferred to the placement checkpoint")
    if layout_raw is not None:
        layout = _mapping(layout_raw, "rf.layout_constraints")
        route = _mapping(layout.get("route"),
                         "rf.layout_constraints.route")
        route_nets = _list(route.get("nets"),
                           "rf.layout_constraints.route.nets")
        route_nets = [_nonempty(net,
                               f"rf.layout_constraints.route.nets[{i}]")
                      for i, net in enumerate(route_nets)]
        if len(set(route_nets)) != len(route_nets):
            raise ContractError("rf.layout_constraints.route.nets contains "
                                "duplicates")
        port_nets = [str(net) for port in ports for net in port["nets"]]
        if set(route_nets) != set(port_nets):
            raise ContractError(
                "rf.layout_constraints.route.nets must equal the exact union "
                f"of rf.ports[].nets; route={route_nets}, ports={port_nets}")
        route_layer = _nonempty(route.get("layer"),
                                "rf.layout_constraints.route.layer")
        reference_layer = _nonempty(
            route.get("reference_layer"),
            "rf.layout_constraints.route.reference_layer")
        numeric = {}
        for key in ("width_mm", "gap_to_top_ground_mm"):
            value = route.get(key)
            if not isinstance(value, (int, float)) or float(value) <= 0:
                raise ContractError(
                    f"rf.layout_constraints.route.{key} must be > 0")
            numeric[key] = float(value)
        for key in ("maximum_vias_per_net", "maximum_stubs_per_net"):
            value = route.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ContractError(
                    f"rf.layout_constraints.route.{key} must be a "
                    "non-negative integer")
        for key in ("length_matching", "geometry"):
            _substantive(route.get(key),
                         f"rf.layout_constraints.route.{key}")
        bend_policy = route.get("bend_policy")
        if bend_policy is not None:
            bend_policy = _mapping(
                bend_policy, "rf.layout_constraints.route.bend_policy")
            multiple = bend_policy.get("minimum_radius_width_multiple")
            if not isinstance(multiple, (int, float)) or float(multiple) <= 0:
                raise ContractError(
                    "rf.layout_constraints.route.bend_policy."
                    "minimum_radius_width_multiple must be > 0")
            sources = _list(
                bend_policy.get("source_claim_ids"),
                "rf.layout_constraints.route.bend_policy.source_claim_ids")
            for i, source in enumerate(sources):
                _nonempty(source, "rf.layout_constraints.route.bend_policy."
                          f"source_claim_ids[{i}]")
            exceptions = bend_policy.get("exceptions") or []
            if not isinstance(exceptions, list):
                raise ContractError(
                    "rf.layout_constraints.route.bend_policy.exceptions "
                    "must be a list")
            exception_ids = set()
            for i, raw in enumerate(exceptions):
                row = _mapping(raw, "rf.layout_constraints.route."
                               f"bend_policy.exceptions[{i}]")
                ident = _nonempty(row.get("id"), "rf.layout_constraints."
                                  f"route.bend_policy.exceptions[{i}].id")
                if ident in exception_ids:
                    raise ContractError(f"duplicate RF bend exception {ident!r}")
                exception_ids.add(ident)
                _nonempty(row.get("net"), "rf.layout_constraints.route."
                          f"bend_policy.exceptions[{i}].net")
                at = row.get("at_mm")
                if (not isinstance(at, list) or len(at) != 2
                        or not all(isinstance(v, (int, float)) for v in at)):
                    raise ContractError("RF bend exception at_mm must be [x, y]")
                tolerance = row.get("tolerance_mm")
                if not isinstance(tolerance, (int, float)) or tolerance <= 0:
                    raise ContractError(
                        "RF bend exception tolerance_mm must be > 0")
                _substantive(row.get("reason"), "RF bend exception reason")
                _substantive(row.get("evidence"), "RF bend exception evidence")
        if adopted_rf_module and bend_policy is None:
            raise ContractError(
                "rf-module-v1 requires rf.layout_constraints.route.bend_policy")
        matching_sections = [s for s in sections
                             if s.get("status", "locked") == "locked"
                             and s.get("copper_layer") == route_layer
                             and s.get("reference_layer") == reference_layer
                             and abs(float(s.get("width_mm", -1)) -
                                     numeric["width_mm"]) <= 1e-9
                             and abs(float(s.get("gap_mm", -1)) -
                                     numeric["gap_to_top_ground_mm"]) <= 1e-9]
        if not matching_sections:
            raise ContractError(
                "rf.layout_constraints.route layer/reference/width/gap does "
                "not match any locked rf.cross_sections[] authority")

        fence = _mapping(layout.get("ground_fence"),
                         "rf.layout_constraints.ground_fence")
        for key in ("status", "source", "wavelength_basis",
                    "pitch_derivation", "lateral_offset_basis", "coverage",
                    "verify"):
            _substantive(fence.get(key),
                         f"rf.layout_constraints.ground_fence.{key}")
        urls = _list(fence.get("source_urls"),
                     "rf.layout_constraints.ground_fence.source_urls")
        for i, url in enumerate(urls):
            value = _nonempty(
                url, f"rf.layout_constraints.ground_fence.source_urls[{i}]")
            if not re.match(r"^https://", value):
                raise ContractError(
                    "rf.layout_constraints.ground_fence.source_urls must use "
                    f"https URLs, got {value!r}")
        maximum_pitch = fence.get("maximum_along_route_pitch_mm")
        lateral_offset = fence.get("nominal_lateral_center_offset_mm")
        maximum_band = fence.get("maximum_lateral_center_offset_mm")
        for key, value in (("maximum_along_route_pitch_mm", maximum_pitch),
                           ("nominal_lateral_center_offset_mm", lateral_offset)):
            if not isinstance(value, (int, float)) or float(value) <= 0:
                raise ContractError(
                    f"rf.layout_constraints.ground_fence.{key} must be > 0")
        if maximum_band is not None:
            if not isinstance(maximum_band, (int, float)) or maximum_band <= 0:
                raise ContractError(
                    "rf.layout_constraints.ground_fence."
                    "maximum_lateral_center_offset_mm must be > 0")
            if float(maximum_band) + 1e-9 < float(lateral_offset):
                raise ContractError(
                    "ground_fence maximum lateral offset cannot be below "
                    "the nominal lateral offset")
        elif adopted_rf_module:
            raise ContractError(
                "rf-module-v1 requires ground_fence."
                "maximum_lateral_center_offset_mm")
        nominal_via = _mapping(
            fence.get("nominal_via_mm"),
            "rf.layout_constraints.ground_fence.nominal_via_mm")
        for key in ("size", "drill"):
            value = nominal_via.get(key)
            if not isinstance(value, (int, float)) or float(value) <= 0:
                raise ContractError(
                    "rf.layout_constraints.ground_fence.nominal_via_mm."
                    f"{key} must be > 0")
        if float(nominal_via["drill"]) >= float(nominal_via["size"]):
            raise ContractError(
                "rf.layout_constraints.ground_fence nominal via drill must "
                "be smaller than its copper size")
        minimum_offset = (numeric["width_mm"] / 2.0
                          + numeric["gap_to_top_ground_mm"]
                          + float(nominal_via["size"]) / 2.0)
        if float(lateral_offset) + 1e-9 < minimum_offset:
            raise ContractError(
                "rf.layout_constraints.ground_fence nominal lateral offset "
                f"{lateral_offset}mm is below the realized copper-separation "
                f"minimum {minimum_offset:.4f}mm")
        endpoint_structures = _list(
            fence.get("endpoint_structures"),
            "rf.layout_constraints.ground_fence.endpoint_structures")
        endpoint_refs = set()
        for i, raw in enumerate(endpoint_structures):
            row = _mapping(
                raw,
                f"rf.layout_constraints.ground_fence.endpoint_structures[{i}]")
            refs = _list(
                row.get("refs"),
                "rf.layout_constraints.ground_fence."
                f"endpoint_structures[{i}].refs")
            for j, ref in enumerate(refs):
                ref = _nonempty(
                    ref, "rf.layout_constraints.ground_fence."
                    f"endpoint_structures[{i}].refs[{j}]")
                if ref in endpoint_refs:
                    raise ContractError(
                        "rf.layout_constraints.ground_fence."
                        f"endpoint_structures repeats ref {ref!r}")
                endpoint_refs.add(ref)
            span = row.get("maximum_along_route_span_mm")
            if not isinstance(span, (int, float)) or float(span) < 0:
                raise ContractError(
                    "rf.layout_constraints.ground_fence."
                    "endpoint_structures[].maximum_along_route_span_mm must "
                    "be >= 0")
            _substantive(
                row.get("basis"),
                "rf.layout_constraints.ground_fence."
                f"endpoint_structures[{i}].basis")

    claims = _list(rf.get("performance_claims"), "rf.performance_claims")
    claim_ids = set()
    for index, raw in enumerate(claims):
        claim = _mapping(raw, f"rf.performance_claims[{index}]")
        ident = _nonempty(claim.get("id"),
                          f"rf.performance_claims[{index}].id")
        if ident in claim_ids:
            raise ContractError(f"duplicate RF performance claim id {ident!r}")
        claim_ids.add(ident)
        for key in ("claim", "acceptance", "evidence"):
            _substantive(claim.get(key),
                         f"rf.performance_claims[{index}].{key}")

    first = _mapping(rf.get("first_article"), "rf.first_article")
    for key in ("measurements", "acceptance"):
        values = _list(first.get(key), f"rf.first_article.{key}")
        for index, value in enumerate(values):
            _substantive(value, f"rf.first_article.{key}[{index}]")

    reviews = _mapping(rf.get("reviews"), "rf.reviews")
    normalized = {}
    all_requirement_ids = set()
    for phase in PHASES:
        spec = _mapping(reviews.get(phase), f"rf.reviews.{phase}")
        review_path = _inside(project, spec.get("path"),
                              f"rf.reviews.{phase}.path")
        artifact = _inside(project, spec.get("artifact"),
                           f"rf.reviews.{phase}.artifact")
        reqs = _list(spec.get("requirements"),
                     f"rf.reviews.{phase}.requirements")
        cleaned = []
        for index, requirement in enumerate(reqs):
            ident = _nonempty(
                requirement, f"rf.reviews.{phase}.requirements[{index}]")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", ident):
                raise ContractError(f"invalid RF requirement id {ident!r}")
            if ident in cleaned:
                raise ContractError(
                    f"duplicate {phase} review requirement {ident!r}")
            if ident in all_requirement_ids:
                raise ContractError(
                    f"RF requirement id {ident!r} is reused across phases")
            cleaned.append(ident)
            all_requirement_ids.add(ident)
        evidence = []
        evidence_roles = set()
        raw_evidence = spec.get("evidence") or []
        if not isinstance(raw_evidence, list):
            raise ContractError(f"rf.reviews.{phase}.evidence must be a list")
        for index, raw in enumerate(raw_evidence):
            row = _mapping(raw, f"rf.reviews.{phase}.evidence[{index}]")
            role = _nonempty(row.get("role"),
                             f"rf.reviews.{phase}.evidence[{index}].role")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", role):
                raise ContractError(f"invalid RF evidence role {role!r}")
            if role in evidence_roles:
                raise ContractError(f"duplicate RF evidence role {role!r}")
            evidence_roles.add(role)
            evidence.append({
                "role": role,
                "path": _inside(project, row.get("path"),
                                f"rf.reviews.{phase}.evidence[{index}].path"),
            })
        required_role = {"schematic": "rf_source_bundle",
                         "pcb": "rf_realized_bundle"}.get(phase)
        if adopted_rf_module and required_role and required_role not in evidence_roles:
            raise ContractError(
                f"rf-module-v1 requires rf.reviews.{phase}.evidence role "
                f"{required_role}")
        normalized[phase] = {
            "path": review_path, "artifact": artifact,
            "requirements": cleaned, "evidence": evidence,
            "contract_path": contract_path,
        }
    if pending_sections and any(
            phase in ("pcb", "fab") for phase in required_phases):
        raise ContractError(
            "RF cross-section solver remains pending for "
            f"{pending_sections}; PCB/fab review cannot proceed until every "
            "width/gap is locked")
    return normalized


def _commit_error(project: Path, commit: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        return "source_commit must be a full SHA"
    context = project
    probe = subprocess.run(
        ["git", "-C", str(context), "rev-parse", "--show-toplevel"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if probe.returncode:
        context = Path(__file__).resolve().parents[3]
    cp = subprocess.run(
        ["git", "-C", str(context), "cat-file", "-e", f"{commit}^{{commit}}"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if cp.returncode:
        return f"source_commit {commit} does not identify a commit"
    cp = subprocess.run(
        ["git", "-C", str(context), "merge-base", "--is-ancestor",
         commit, "HEAD"], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    if cp.returncode:
        return f"source_commit {commit} is not an ancestor of HEAD"
    return ""


def review_errors(project: Path, phase: str, spec: dict) -> list[str]:
    review, artifact = spec["path"], spec["artifact"]
    errors = []
    if not artifact.is_file():
        return [f"RF-{phase.upper()}-ARTIFACT: missing {artifact}"]
    if not review.is_file():
        return [f"RF-{phase.upper()}-REVIEW: missing {review}"]
    text = review.read_text(encoding="utf-8-sig", errors="replace")
    expected_kind = REVIEW_KIND[phase]
    if _field(text, "review_kind").upper() != expected_kind:
        errors.append(f"RF-{phase.upper()}-KIND: review_kind must be {expected_kind}")
    if _field(text, "independence").lower() != "independent-from-design-author":
        errors.append(
            f"RF-{phase.upper()}-INDEPENDENCE: independence must be "
            "independent-from-design-author")
    if not _field(text, "subject") or not _field(text, "reviewer"):
        errors.append(f"RF-{phase.upper()}-HEADER: subject and reviewer are required")
    commit = _field(text, "source_commit")
    commit_error = _commit_error(project, commit)
    if commit_error:
        errors.append(f"RF-{phase.upper()}-COMMIT: {commit_error}")
    actual_hash = _sha256(artifact)
    bound_hash = _field(text, "artifact_sha256").lower()
    if bound_hash != actual_hash:
        errors.append(
            f"RF-{phase.upper()}-BINDING: artifact_sha256 is "
            f"{bound_hash or 'UNSTATED'}, expected {actual_hash}")
    evidence_rows = _evidence_bindings(text)
    evidence_seen = [role for role, _digest in evidence_rows]
    duplicates = sorted({role for role in evidence_seen
                         if evidence_seen.count(role) > 1})
    expected_roles = [row["role"] for row in spec.get("evidence") or []]
    missing_roles = sorted(set(expected_roles) - set(evidence_seen))
    extra_roles = sorted(set(evidence_seen) - set(expected_roles))
    if duplicates or missing_roles or extra_roles \
            or len(evidence_rows) != len(expected_roles):
        errors.append(
            f"RF-{phase.upper()}-EVIDENCE-COVERAGE: bound "
            f"{len(evidence_rows)}/{len(expected_roles)}; missing={missing_roles}, "
            f"extra={extra_roles}, duplicate={duplicates}")
    bound_evidence = dict(evidence_rows)
    for row in spec.get("evidence") or []:
        role, path = row["role"], row["path"]
        if not path.is_file():
            errors.append(f"RF-{phase.upper()}-EVIDENCE: {role} missing {path}")
            continue
        expected_hash = _sha256(path)
        if bound_evidence.get(role) != expected_hash:
            errors.append(
                f"RF-{phase.upper()}-EVIDENCE-BINDING: {role} is "
                f"{bound_evidence.get(role, 'UNSTATED')}, expected {expected_hash}")
        bundle_error = _bundle_error(
            path, role, artifact, spec.get("contract_path"))
        if bundle_error:
            errors.append(f"RF-{phase.upper()}-EVIDENCE: {role}: {bundle_error}")
    verdict_key = "fab_package_verdict" if phase == "fab" else "design_verdict"
    verdict_want = "READY" if phase == "fab" else "SOUND"
    if _field(text, verdict_key).upper() != verdict_want:
        errors.append(
            f"RF-{phase.upper()}-VERDICT: {verdict_key} must be {verdict_want}")

    rows = _requirements(text)
    seen = [ident for ident, _ in rows]
    expected = spec["requirements"]
    duplicates = sorted({ident for ident in seen if seen.count(ident) > 1})
    missing = sorted(set(expected) - set(seen))
    extra = sorted(set(seen) - set(expected))
    failed = sorted(ident for ident, verdict in rows if verdict != "PASS")
    if duplicates or missing or extra or failed or len(rows) != len(expected):
        errors.append(
            f"RF-{phase.upper()}-COVERAGE: graded {len(rows)}/{len(expected)}; "
            f"missing={missing}, extra={extra}, duplicate={duplicates}, fail={failed}")
    return errors


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("project", type=Path)
    p.add_argument("--contract", type=Path,
                   help="explicit board-scoped rf.yaml")
    p.add_argument("--require-review", action="append", choices=PHASES,
                   default=[])
    p.add_argument("--require-applicability", action="store_true",
                   help="fail when the project has no explicit rf.yaml")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    project = args.project.resolve()
    contract_path = (args.contract.resolve() if args.contract else
                     project / "03_src" / "rules" / "rf.yaml")
    if not contract_path.is_file():
        if args.require_applicability:
            print(f"RF-CONTRACT FAIL: no explicit applicability contract at "
                  f"{contract_path}")
            return 1
        print(f"RF-CONTRACT UNMIGRATED: no {contract_path}; legacy project, "
              "not an RF-review pass")
        return 0
    try:
        contract = load_contract(contract_path)
        rf = contract["rf"]
        if not rf["enabled"]:
            print("RF-CONTRACT PASS: applicability 1/1; RF disabled with rationale; "
                  "dedicated RF reviews are N-A")
            return 0
        phases = list(dict.fromkeys(args.require_review))
        reviews = validate_enabled(project, contract, phases, contract_path)
        errors = []
        for phase in phases:
            phase_errors = review_errors(project, phase, reviews[phase])
            if phase_errors:
                errors.extend(phase_errors)
            else:
                count = len(reviews[phase]["requirements"])
                print(f"RF-REVIEW {phase}: PASS {count}/{count} requirements; "
                      f"exact artifact {reviews[phase]['artifact']}")
    except ContractError as exc:
        print(f"RF-CONTRACT FAIL: {exc}")
        return 2
    print("RF-CONTRACT coverage: 1 applicability decision; "
          f"{len(rf['ports'])} port(s), {len(rf['cross_sections'])} "
          f"cross-section(s), {len(rf['performance_claims'])} claim(s); "
          f"{len(phases)}/3 review phase(s) requested")
    if errors:
        for error in errors:
            print(f"  {error}")
        print(f"RF-CONTRACT FAIL: {len(errors)} finding(s)")
        return 1
    print("RF-CONTRACT PASS: RF intent is complete" +
          (" and requested reviews are exact-artifact-bound" if phases else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
