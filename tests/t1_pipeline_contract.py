#!/usr/bin/env python3
"""T1: strict pipeline stage contracts and subject identity projections."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "skills/pcb-design/scripts"
sys.path.insert(0, str(PIPELINE))

from pipeline_contract import (ContractValidationError, StageResult,  # noqa: E402
                               StageSpec)
from pipeline_identity import (IdentityValidationError, SubjectIdentity,  # noqa: E402
                               TypedIdentityInput, subject_identity)


def rejects(fn, expected, what):
    try:
        fn()
    except (ContractValidationError, IdentityValidationError) as exc:
        check(expected in str(exc), f"{what}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{what}: malformed input SHOULD HAVE FAILED")


def spec_mapping():
    return {
        "schema": 1,
        "id": "P-ROUTEBASE",
        "owner": "kicad-pcb",
        "lifecycle": "placement",
        "cost": "cheap",
        "work_class": "local",
        "timeout_s": 30,
        "requires": ["deterministic_route_prep", "exact_placement"],
        "produces": ["route_compatibility_report"],
        "blocks": ["placement_review"],
        "invalidated_by": ["placement_semantic", "route_process"],
    }


def identity():
    return subject_identity("layout", 1, [
        TypedIdentityInput("board", "mapping", {
            "nets": {"GND": ["J1.1", "U1.2"], "VCC": ["J1.2", "U1.1"]},
            "parts": ["J1", "U1"],
        }, b"(board\n  (part U1)\n)\n"),
        TypedIdentityInput("process", "set", [
            {"family": "ordinary", "drill_mm": 0.3},
            {"family": "filled", "drill_mm": 0.2},
        ], b"process:\n  filled: 0.20\n  ordinary: 0.30\n"),
    ])


def result_mapping(**changes):
    value = {
        "schema": 1,
        "stage_id": "P-ROUTEBASE",
        "run_id": "20260812T170000Z-8d31a2f0",
        "subject": identity().to_mapping(),
        "applicability": "APPLIES",
        "applicability_reason": None,
        "status": "PASS",
        "started_at": "2026-08-12T17:00:00Z",
        "finished_at": "2026-08-12T17:00:01Z",
        "elapsed_s": 1.0,
        "graded": 95,
        "total": 95,
        "outputs": ["route_compatibility_report"],
        "findings": [],
        "resume": None,
    }
    value.update(changes)
    return value


@test("schema-1 StageSpec round-trips its exact typed public mapping")
def t_spec_roundtrip():
    source = spec_mapping()
    spec = StageSpec.from_mapping(source)
    eq(spec.to_mapping(), source, "StageSpec mapping")
    eq(StageSpec.from_json(spec.to_json()), spec, "StageSpec canonical JSON")
    eq(spec.requires, ("deterministic_route_prep", "exact_placement"),
       "immutable requires")


@test("operator-only declarative StageSpec may omit its timeout")
def t_operator_spec():
    source = spec_mapping()
    source.update(cost="operator", work_class="operator_wait")
    del source["timeout_s"]
    spec = StageSpec.from_mapping(source)
    check(spec.timeout_s is None, "operator timeout should remain absent")
    check("timeout_s" not in spec.to_mapping(), "absent timeout was invented")


@test("StageSpec rejects unknown fields and unsorted or path-like symbols",
      kind="known_bad")
def t_spec_strict_failures():
    unknown = spec_mapping()
    unknown["command"] = "rm -rf ."
    rejects(lambda: StageSpec.from_mapping(unknown), "unknown=['command']",
            "unknown execution field")
    unordered = spec_mapping()
    unordered["requires"] = ["exact_placement", "deterministic_route_prep"]
    rejects(lambda: StageSpec.from_mapping(unordered), "sorted and unique",
            "unordered identity symbols")
    path = spec_mapping()
    path["produces"] = ["06_build/report.json"]
    rejects(lambda: StageSpec.from_mapping(path), "not a symbolic name",
            "artifact path in semantic contract")


@test("StageSpec enforces closed vocabularies and executable deadlines",
      kind="known_bad")
def t_spec_vocab_failures():
    for field, bad in (("owner", "usb-team"), ("lifecycle", "done"),
                       ("cost", "fast"), ("work_class", "sleep")):
        source = spec_mapping()
        source[field] = bad
        rejects(lambda source=source: StageSpec.from_mapping(source),
                "expected one of", f"unknown {field}")
    no_timeout = spec_mapping()
    del no_timeout["timeout_s"]
    rejects(lambda: StageSpec.from_mapping(no_timeout), "only operator",
            "executable stage without timeout")


@test("schema-1 StageResult round-trips a passing non-vacuous result")
def t_result_roundtrip():
    source = result_mapping()
    result = StageResult.from_mapping(source)
    eq(result.to_mapping(), source, "StageResult mapping")
    eq(StageResult.from_json(result.to_json()), result,
       "StageResult canonical JSON")
    check(isinstance(result.subject, SubjectIdentity), "subject was not typed")


@test("NOT_APPLICABLE is explicit, reasoned, and has a zero denominator")
def t_not_applicable():
    source = result_mapping(
        applicability="NOT_APPLICABLE",
        applicability_reason="board declares no RF paths",
        status="NOT_APPLICABLE", graded=0, total=0, outputs=[])
    result = StageResult.from_mapping(source)
    eq(result.applicability_reason, "board declares no RF paths",
       "applicability reason")


@test("PASS cannot be vacuous, partial, inapplicable, or reason-bearing",
      kind="known_bad")
def t_pass_invariants():
    rejects(lambda: StageResult.from_mapping(result_mapping(graded=0, total=0)),
            "graded == total > 0", "zero denominator PASS")
    rejects(lambda: StageResult.from_mapping(result_mapping(graded=94)),
            "graded == total > 0", "partial PASS")
    rejects(lambda: StageResult.from_mapping(result_mapping(
        applicability="NOT_APPLICABLE", applicability_reason="not used")),
        "requires NOT_APPLICABLE status", "inapplicable PASS")
    rejects(lambda: StageResult.from_mapping(result_mapping(
        applicability_reason="free-form maybe")), "requires null or empty",
        "APPLIES with applicability excuse")


@test("NOT_APPLICABLE cannot hide applicability uncertainty or graded work",
      kind="known_bad")
def t_na_invariants():
    rejects(lambda: StageResult.from_mapping(result_mapping(
        applicability="NOT_APPLICABLE", applicability_reason=" ",
        status="NOT_APPLICABLE", graded=0, total=0)), "requires a reason",
        "blank applicability reason")
    rejects(lambda: StageResult.from_mapping(result_mapping(
        applicability="NOT_APPLICABLE", applicability_reason="no RF",
        status="NOT_APPLICABLE", graded=1, total=1)), "graded == total == 0",
        "graded NOT_APPLICABLE")
    rejects(lambda: StageResult.from_mapping(result_mapping(
        applicability="UNKNOWN", status="INCOMPLETE")), "expected one of",
        "unknown applicability")


@test("StageResult rejects unknown fields, malformed subjects, and bad time",
      kind="known_bad")
def t_result_schema_failures():
    unknown = result_mapping()
    unknown["command"] = ["hidden", "execution"]
    rejects(lambda: StageResult.from_mapping(unknown), "unknown=['command']",
            "unknown result field")
    malformed_subject = result_mapping()
    malformed_subject["subject"]["semantic_sha256"] = "A" * 64
    rejects(lambda: StageResult.from_mapping(malformed_subject),
            "64 lowercase hexadecimal", "noncanonical subject hash")
    rejects(lambda: StageResult.from_mapping(result_mapping(
        finished_at="2026-08-12T16:59:59Z")), "cannot precede",
        "reversed result timestamps")
    rejects(lambda: StageResult.from_mapping(result_mapping(
        started_at="2026-08-12T17:00:00")), "must include a UTC offset",
        "timezone-free result timestamp")


@test("timed-out and incomplete outcomes remain non-PASS durable states")
def t_non_admissible_states():
    for status in ("TIMED_OUT", "INCOMPLETE"):
        source = result_mapping(status=status, graded=0, total=95, outputs=[])
        result = StageResult.from_mapping(source)
        check(result.status != "PASS", f"{status} became PASS")


@test("identity canonicalizes mapping keys, input order, and declared sets")
def t_identity_canonical_order():
    left = subject_identity("electrical", 1, [
        TypedIdentityInput("parts", "set", ["U2", "U1"], b"U1,U2"),
        TypedIdentityInput("nets", "mapping", {
            "VCC": ["U1.1", "U2.1"], "GND": ["U1.2", "U2.2"]}, b"raw"),
    ])
    right = subject_identity("electrical", 1, [
        TypedIdentityInput("nets", "mapping", {
            "GND": ["U1.2", "U2.2"], "VCC": ["U1.1", "U2.1"]}, b"raw"),
        TypedIdentityInput("parts", "set", ["U1", "U2"], b"U1,U2"),
    ])
    eq(left, right, "canonical identity")


@test("formatting-only source mutation changes raw but not semantic identity")
def t_identity_formatting_stability():
    compact = subject_identity("schematic", 1, [TypedIdentityInput(
        "netlist", "mapping", {"GND": ["C1.2", "U1.2"]},
        b'{"GND":["C1.2","U1.2"]}')])
    pretty = subject_identity("schematic", 1, [TypedIdentityInput(
        "netlist", "mapping", {"GND": ["C1.2", "U1.2"]},
        b'{\n  "GND": ["C1.2", "U1.2"]\n}\n')])
    eq(compact.semantic_sha256, pretty.semantic_sha256, "semantic identity")
    check(compact.raw_sha256 != pretty.raw_sha256,
          "formatting-only mutation did not move raw identity")


@test("design mutation changes semantic and raw identity")
def t_identity_design_mutation():
    original = subject_identity("schematic", 1, [TypedIdentityInput(
        "netlist", "mapping", {"VCC": ["U1.1", "J1.1"]}, b"VCC U1.1 J1.1")])
    changed = subject_identity("schematic", 1, [TypedIdentityInput(
        "netlist", "mapping", {"VCC": ["U1.1", "J1.2"]}, b"VCC U1.1 J1.2")])
    check(original.semantic_sha256 != changed.semantic_sha256,
          "design mutation did not move semantic identity")
    check(original.raw_sha256 != changed.raw_sha256,
          "design mutation did not move raw identity")


@test("raw-only tool metadata mutation does not contaminate semantic identity")
def t_identity_raw_metadata_mutation():
    original = subject_identity("placement", 1, [TypedIdentityInput(
        "placement", "sequence", [["U1", 10.0, 20.0, 0]], b"U1 10 20 0",
        {"tool": "kicad", "version": "10.0", "log_level": "quiet"})])
    changed = subject_identity("placement", 1, [TypedIdentityInput(
        "placement", "sequence", [["U1", 10.0, 20.0, 0]], b"U1 10 20 0",
        {"tool": "kicad", "version": "10.0", "log_level": "debug"})])
    eq(original.semantic_sha256, changed.semantic_sha256, "semantic identity")
    check(original.raw_sha256 != changed.raw_sha256,
          "raw-only metadata mutation did not move raw identity")


@test("identity refuses implicit ordering, duplicate names, and empty subjects",
      kind="known_bad")
def t_identity_strict_failures():
    rejects(lambda: TypedIdentityInput("parts", "set", {"U1", "U2"}, b"raw"),
            "requires a list or tuple", "unordered Python set")
    duplicate = TypedIdentityInput("parts", "scalar", "U1", b"U1")
    rejects(lambda: subject_identity("schematic", 1, [duplicate, duplicate]),
            "names must be unique", "duplicate input name")
    rejects(lambda: subject_identity("schematic", 1, []),
            "denominator must be non-zero", "empty subject identity")


@test("identity version and semantic sequence order are discriminators")
def t_identity_version_and_sequence():
    source = TypedIdentityInput("path", "sequence", ["J1", "F1", "U1"],
                                b"J1 F1 U1")
    reordered = TypedIdentityInput("path", "sequence", ["F1", "J1", "U1"],
                                   b"F1 J1 U1")
    version_1 = subject_identity("power-path", 1, [source])
    version_2 = subject_identity("power-path", 2, [source])
    order_2 = subject_identity("power-path", 1, [reordered])
    check(version_1.semantic_sha256 != version_2.semantic_sha256,
          "projection version did not move semantic identity")
    check(version_1.semantic_sha256 != order_2.semantic_sha256,
          "meaningful sequence order was erased")


@test("contract JSON serialization is deterministic despite mapping insertion order")
def t_contract_json_canonical():
    mapping = result_mapping(findings=[{"z": 2, "a": 1}])
    result = StageResult.from_mapping(mapping)
    encoded = result.to_json()
    eq(encoded, json.dumps(result.to_mapping(), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=False),
       "canonical StageResult JSON")


if __name__ == "__main__":
    raise SystemExit(main())
