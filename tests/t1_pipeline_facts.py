#!/usr/bin/env python3
"""T1: early-warning and late-authority lifecycle fact contracts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))

from pipeline_facts import (  # noqa: E402
    FactEvaluation,
    FactObservation,
    FactPair,
    FactValidationError,
    InvalidatorState,
    evaluate_early,
    evaluate_late,
)
from pipeline_identity import SubjectIdentity  # noqa: E402


def identity(semantic="1", raw="a"):
    return SubjectIdentity(semantic * 64, raw * 64)


def pair_mapping(*, maximum_age=True, invalidators=True):
    value = {
        "schema": 1,
        "fact": "supplier_allocation",
        "owner": "jlcpcb-fab",
        "early": {"stage": "sourcing", "blocks": "schematic"},
        "late": {
            "stage": "fabrication",
            "blocks": "first_article",
            "authority": "supplier_uploader",
        },
        "invalidated_by": ["catalog_record"] if invalidators else [],
    }
    if maximum_age:
        value["maximum_age_s"] = 600
    return value


def pair(**kwargs):
    return FactPair.from_mapping(pair_mapping(**kwargs))


def invalidator(*, semantic="2", raw="b", name="catalog_record"):
    return InvalidatorState(name=name, subject=identity(semantic, raw))


def early_observation(**changes):
    value = {
        "schema": 1,
        "fact": "supplier_allocation",
        "phase": "EARLY",
        "stage": "sourcing",
        "subject": identity().to_mapping(),
        "authority": None,
        "status": "PASS",
        "started_at": "2026-08-12T10:00:00Z",
        "observed_at": "2026-08-12T10:01:00Z",
        "graded": 3,
        "total": 3,
        "invalidators": [invalidator().to_mapping()],
    }
    value.update(changes)
    return FactObservation.from_mapping(value)


def late_observation(**changes):
    value = {
        "schema": 1,
        "fact": "supplier_allocation",
        "phase": "LATE",
        "stage": "fabrication",
        "subject": identity().to_mapping(),
        "authority": "supplier_uploader",
        "status": "PASS",
        "started_at": "2026-08-12T11:00:00Z",
        "observed_at": "2026-08-12T11:01:00Z",
        "graded": 4,
        "total": 4,
        "invalidators": [],
    }
    value.update(changes)
    return FactObservation.from_mapping(value)


def rejects(fn, expected, what):
    try:
        fn()
    except FactValidationError as exc:
        check(expected in str(exc),
              f"{what}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{what}: malformed fact contract SHOULD HAVE FAILED")


@test("schema-1 fact pair and observations round-trip exact mappings")
def t_roundtrip():
    declaration = pair()
    eq(declaration.to_mapping(), pair_mapping(), "FactPair mapping")
    eq(FactPair.from_json(declaration.to_json()), declaration,
       "FactPair canonical JSON")

    early = early_observation()
    eq(FactObservation.from_json(early.to_json()), early,
       "FactObservation canonical JSON")
    eq(early.invalidators[0].name, "catalog_record", "typed invalidator")


@test("fresh early PASS permits its consumer but never authorizes a final claim")
def t_early_prevention_only():
    result = evaluate_early(
        pair(), early_observation(), current_subject=identity(),
        now="2026-08-12T10:05:00Z", current_invalidators=[invalidator()])
    eq(result.disposition, "PROCEED", "early disposition")
    eq(result.role, "PREVENTION", "early role")
    check(not result.authorizes_final, "early PASS became final authority")
    eq(FactEvaluation.from_json(result.to_json()), result,
       "FactEvaluation canonical JSON")


@test("raw-only subject and invalidator changes preserve semantic early reuse")
def t_raw_only_identity_changes():
    result = evaluate_early(
        pair(), early_observation(),
        current_subject=identity(semantic="1", raw="c"),
        now="2026-08-12T10:05:00Z",
        current_invalidators=[invalidator(semantic="2", raw="d")])
    eq(result.reason, "EARLY_PASS", "raw-only identity boundary")
    eq(result.disposition, "PROCEED", "raw-only identity disposition")
    check(not result.authorizes_final, "raw-only reuse authorized final claim")


@test("realized immutable early fact has no age expiry")
def t_realized_no_age():
    declaration = FactPair.from_mapping({
        "schema": 1,
        "fact": "generated_evidence",
        "owner": "pcb-design",
        "early": {"stage": "routing", "blocks": "layout_seal"},
        "late": {
            "stage": "release_staging",
            "blocks": "release_seal",
            "authority": "bundle_validator",
        },
        "invalidated_by": [],
    })
    observed = FactObservation(
        fact="generated_evidence", phase="EARLY", stage="routing",
        subject=identity(), authority=None, status="PASS",
        started_at="2020-01-01T00:00:00Z",
        observed_at="2020-01-01T00:00:01Z", graded=1, total=1,
        invalidators=())
    result = evaluate_early(
        declaration, observed, current_subject=identity(),
        now="2026-08-12T10:05:00Z")
    eq(result.reason, "EARLY_PASS", "non-expiring realized fact")


@test("passing declared late authority alone authorizes the final claim")
def t_late_authority():
    result = evaluate_late(
        pair(), late_observation(), current_subject=identity())
    eq(result.disposition, "PROCEED", "late disposition")
    eq(result.role, "AUTHORITY", "late role")
    check(result.authorizes_final, "passing late authority did not authorize")
    check(result.causal_fact is None, "passing authority invented a cause")


@test("stale mutable early observation BLOCKS its consumer", kind="known_bad")
def t_stale_early():
    result = evaluate_early(
        pair(), early_observation(), current_subject=identity(),
        now="2026-08-12T10:20:00Z", current_invalidators=[invalidator()])
    eq(result.disposition, "BLOCK", "stale disposition")
    eq(result.reason, "STALE_OBSERVATION", "stale reason")
    check(not result.authorizes_final, "stale observation authorized")


@test("missing or semantic-identity-mismatched early evidence BLOCKS",
      kind="known_bad")
def t_missing_and_subject_mismatch():
    missing = evaluate_early(
        pair(), None, current_subject=identity(),
        now="2026-08-12T10:05:00Z", current_invalidators=[invalidator()])
    eq(missing.reason, "MISSING_OBSERVATION", "missing early reason")
    mismatch = evaluate_early(
        pair(), early_observation(), current_subject=identity("3", "a"),
        now="2026-08-12T10:05:00Z", current_invalidators=[invalidator()])
    eq(mismatch.reason, "SUBJECT_MISMATCH", "subject mismatch reason")
    eq(mismatch.disposition, "BLOCK", "subject mismatch disposition")


@test("changed semantic invalidator BLOCKS reuse of an early PASS",
      kind="known_bad")
def t_changed_invalidator():
    changed = evaluate_early(
        pair(), early_observation(), current_subject=identity(),
        now="2026-08-12T10:05:00Z",
        current_invalidators=[invalidator(semantic="3")])
    eq(changed.reason, "INVALIDATED", "changed invalidator reason")
    eq(changed.disposition, "BLOCK", "changed invalidator disposition")


@test("unknown or missing current invalidator evidence fails closed",
      kind="known_bad")
def t_invalidator_census():
    unknown = evaluate_early(
        pair(), early_observation(), current_subject=identity(),
        now="2026-08-12T10:05:00Z", current_invalidators=[
            invalidator(),
            invalidator(semantic="4", name="undeclared_change"),
        ])
    eq(unknown.reason, "UNKNOWN_INVALIDATOR", "unknown invalidator reason")
    eq(unknown.disposition, "BLOCK", "unknown invalidator disposition")

    missing = evaluate_early(
        pair(), early_observation(), current_subject=identity(),
        now="2026-08-12T10:05:00Z", current_invalidators=[])
    eq(missing.reason, "MISSING_CURRENT_INVALIDATOR",
       "missing invalidator reason")


@test("observation cannot omit its declared invalidator baseline",
      kind="known_bad")
def t_observation_invalidator_census():
    observed = early_observation(invalidators=[])
    result = evaluate_early(
        pair(), observed, current_subject=identity(),
        now="2026-08-12T10:05:00Z", current_invalidators=[invalidator()])
    eq(result.reason, "OBSERVATION_INVALIDATOR_SET_MISMATCH",
       "observation invalidator census")
    eq(result.disposition, "BLOCK", "baseline omission disposition")


@test("non-passing late observation BLOCKS and attributes its early owner",
      kind="known_bad")
def t_late_failure_attribution():
    failed = late_observation(status="FAIL", graded=4, total=4)
    result = evaluate_late(pair(), failed, current_subject=identity())
    eq(result.disposition, "BLOCK", "late failure disposition")
    check(not result.authorizes_final, "late failure authorized")
    eq(result.causal_fact, "supplier_allocation", "causal fact")
    eq(result.causal_owner, "jlcpcb-fab", "causal owner")
    eq(result.causal_stage, "sourcing", "causal early stage")


@test("early PASS cannot weaken or replace the final authoritative recheck",
      kind="known_bad")
def t_no_weakening_final_recheck():
    early = evaluate_early(
        pair(), early_observation(), current_subject=identity(),
        now="2026-08-12T10:05:00Z", current_invalidators=[invalidator()])
    eq(early.disposition, "PROCEED", "early consumer")
    check(not early.authorizes_final, "early result authorized final claim")

    late = evaluate_late(pair(), None, current_subject=identity())
    eq(late.reason, "MISSING_OBSERVATION", "missing late authority reason")
    eq(late.disposition, "BLOCK", "missing late authority disposition")
    check(not late.authorizes_final, "missing final recheck authorized")


@test("wrong late authority or subject identity cannot authorize",
      kind="known_bad")
def t_late_identity_and_authority():
    wrong_authority = evaluate_late(
        pair(), late_observation(authority="cached_catalog"),
        current_subject=identity())
    eq(wrong_authority.reason, "AUTHORITY_MISMATCH", "authority reason")
    wrong_subject = evaluate_late(
        pair(), late_observation(), current_subject=identity("3", "a"))
    eq(wrong_subject.reason, "SUBJECT_MISMATCH", "late subject reason")
    check(not wrong_authority.authorizes_final, "wrong authority authorized")
    check(not wrong_subject.authorizes_final, "wrong subject authorized")


@test("fact schemas REFUSE unknowns, bad age, order, status, and vacuous PASS",
      kind="known_bad")
def t_strict_contract():
    unknown = pair_mapping()
    unknown["command"] = ["hidden", "execution"]
    rejects(lambda: FactPair.from_mapping(unknown), "unknown=['command']",
            "unknown pair field")

    bad_age = pair_mapping()
    bad_age["maximum_age_s"] = 0
    rejects(lambda: FactPair.from_mapping(bad_age), "positive finite",
            "non-positive maximum age")

    unordered = pair_mapping()
    unordered["invalidated_by"] = ["tool_version", "catalog_record"]
    rejects(lambda: FactPair.from_mapping(unordered), "sorted and unique",
            "unordered invalidator declaration")

    bad_status = early_observation().to_mapping()
    bad_status["status"] = "UNKNOWN"
    rejects(lambda: FactObservation.from_mapping(bad_status), "expected one of",
            "unknown observation status")

    vacuous = early_observation().to_mapping()
    vacuous.update(graded=0, total=0)
    rejects(lambda: FactObservation.from_mapping(vacuous),
            "graded == total > 0", "vacuous observation PASS")


@test("late PASS REFUSES partial or zero-denominator coverage",
      kind="known_bad")
def t_late_pass_denominator():
    partial = late_observation().to_mapping()
    partial["graded"] = 3
    rejects(lambda: FactObservation.from_mapping(partial),
            "graded == total > 0", "partial late PASS")
    zero = late_observation().to_mapping()
    zero.update(graded=0, total=0)
    rejects(lambda: FactObservation.from_mapping(zero),
            "graded == total > 0", "zero-denominator late PASS")


if __name__ == "__main__":
    raise SystemExit(main())
