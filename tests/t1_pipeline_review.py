#!/usr/bin/env python3
"""T1: bounded review commissions and witness admissibility."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/pcb-design/scripts"))
from pipeline_review import (  # noqa: E402
    ReviewCommission, ReviewInadmissibleError, ReviewValidationError,
    ReviewWitness, assess_witness, require_admissible,
)


SUBJECT = {"semantic_sha256": "a" * 64, "raw_sha256": "b" * 64}
ARTIFACTS = [
    {"path": "04_kicad/board.kicad_pcb", "sha256": "c" * 64},
    {"path": "06_build/review/render.png", "sha256": "d" * 64},
]


def commission_mapping():
    return {"schema": 1, "commission_id": "R-LAYOUT-1",
            "project": "example-board", "source_commit": "e" * 40,
            "subject": SUBJECT, "lens": "layout_thermal",
            "checklist": ["body_registration", "thermal_path"],
            "exclusions": ["catalog_stock"], "artifacts": ARTIFACTS,
            "output_path": "08_reviews/layout_witness.json",
            "issued_at": "2026-08-12T10:00:00Z",
            "deadline_at": "2026-08-12T10:10:00Z"}


def witness_mapping(**changes):
    value = {"schema": 1, "commission_id": "R-LAYOUT-1",
             "project": "example-board", "source_commit": "e" * 40,
             "subject": SUBJECT, "lens": "layout_thermal",
             "artifacts": ARTIFACTS,
             "checklist": [
                 {"item": "body_registration", "status": "PASS"},
                 {"item": "thermal_path", "status": "PASS"}],
             "graded": 2, "total": 2,
             "output": {"path": "08_reviews/layout_witness.json",
                        "sha256": "f" * 64},
             "completed_at": "2026-08-12T10:08:00Z",
             "design_verdict": "SOUND",
             "order_verdict": "FIRST-ARTICLE-ONLY"}
    value.update(changes)
    return value


def observations():
    return {item["path"]: item["sha256"] for item in ARTIFACTS}


def assess(witness=None, **kwargs):
    return assess_witness(
        ReviewCommission.from_mapping(commission_mapping()),
        witness or ReviewWitness.from_mapping(witness_mapping()),
        observed_output_path="08_reviews/layout_witness.json",
        observed_output_sha256="f" * 64,
        observed_artifact_hashes=observations(),
        now="2026-08-12T10:09:00Z", **kwargs)


def rejects(fn, phrase):
    try:
        fn()
    except ReviewValidationError as exc:
        check(phrase in str(exc), f"diagnosis missing {phrase!r}: {exc}")
    else:
        raise AssertionError("malformed review contract was accepted")


@test("commission and SOUND witness round-trip exact schema-1 data")
def t_roundtrip():
    commission = ReviewCommission.from_mapping(commission_mapping())
    witness = ReviewWitness.from_mapping(witness_mapping())
    eq(commission.to_mapping(), commission_mapping(), "commission mapping")
    eq(ReviewCommission.from_json(commission.to_json()), commission,
       "commission JSON")
    eq(witness.to_mapping(), witness_mapping(), "witness mapping")
    eq(ReviewWitness.from_json(witness.to_json()), witness, "witness JSON")


@test("complete on-time exact-subject witness is admissible")
def t_admissible():
    result = assess()
    check(result.admissible, f"clean witness rejected: {result.reasons}")
    eq(result.design_verdict, "SOUND", "design verdict")
    witness = ReviewWitness.from_mapping(witness_mapping())
    eq(require_admissible(
        ReviewCommission.from_mapping(commission_mapping()), witness,
        observed_output_path="08_reviews/layout_witness.json",
        observed_output_sha256="f" * 64,
        observed_artifact_hashes=observations()), witness, "required witness")


@test("DEFECTIVE complete witness is admissible evidence but never orderable")
def t_defective_evidence():
    rows = [{"item": "body_registration", "status": "FAIL"},
            {"item": "thermal_path", "status": "PASS"}]
    witness = ReviewWitness.from_mapping(witness_mapping(
        checklist=rows, design_verdict="DEFECTIVE",
        order_verdict="DO-NOT-ORDER"))
    result = assess(witness)
    check(result.admissible, f"valid blocking witness rejected: {result.reasons}")
    eq(result.design_verdict, "DEFECTIVE", "blocking design verdict")


@test("late or incomplete witness is never admissible", kind="known_bad")
def t_late_incomplete():
    late = ReviewWitness.from_mapping(witness_mapping(
        completed_at="2026-08-12T10:11:00Z"))
    check("LATE" in assess(late).reasons, "late witness was admitted")
    rows = [{"item": "body_registration", "status": "PASS"},
            {"item": "thermal_path", "status": "INCOMPLETE"}]
    partial = ReviewWitness.from_mapping(witness_mapping(
        checklist=rows, graded=1, design_verdict="INCOMPLETE",
        order_verdict="DO-NOT-ORDER"))
    result = assess(partial)
    check(not result.admissible and "INCOMPLETE" in result.reasons,
          "partial witness was admitted")


@test("identity, lens, project and checklist drift are refused", kind="known_bad")
def t_binding_mismatch():
    changed = witness_mapping(
        project="other-board", lens="different_lens",
        subject={"semantic_sha256": "1" * 64, "raw_sha256": "2" * 64})
    rows = list(changed["checklist"])
    rows[1] = {"item": "uncommissioned_check", "status": "PASS"}
    changed["checklist"] = sorted(rows, key=lambda row: row["item"])
    witness = ReviewWitness.from_mapping(changed)
    reasons = assess(witness).reasons
    for reason in ("PROJECT_MISMATCH", "SUBJECT_MISMATCH", "LENS_MISMATCH",
                   "CHECKLIST_MISMATCH"):
        check(reason in reasons, f"{reason} was not refused")


@test("durable output and artifact hashes are independently observed",
      kind="known_bad")
def t_durable_observation():
    commission = ReviewCommission.from_mapping(commission_mapping())
    witness = ReviewWitness.from_mapping(witness_mapping())
    absent = assess_witness(commission, witness)
    check("OUTPUT_NOT_OBSERVED" in absent.reasons and
          "ARTIFACTS_NOT_OBSERVED" in absent.reasons,
          "self-asserted hashes became durable evidence")
    changed = observations()
    changed[ARTIFACTS[0]["path"]] = "0" * 64
    result = assess_witness(
        commission, witness,
        observed_output_path="08_reviews/layout_witness.json",
        observed_output_sha256="0" * 64,
        observed_artifact_hashes=changed)
    check("OUTPUT_HASH_MISMATCH" in result.reasons and
          "OBSERVED_ARTIFACT_MISMATCH" in result.reasons,
          "mutated durable bytes were admitted")


@test("review schemas reject unsafe paths, unknowns and abbreviated commits",
      kind="known_bad")
def t_schema_strictness():
    unknown = commission_mapping()
    unknown["prompt"] = "unbounded scope"
    rejects(lambda: ReviewCommission.from_mapping(unknown), "unknown=['prompt']")
    unsafe = commission_mapping()
    unsafe["output_path"] = "../outside.json"
    rejects(lambda: ReviewCommission.from_mapping(unsafe), "non-traversing")
    abbreviated = commission_mapping()
    abbreviated["source_commit"] = "e" * 12
    rejects(lambda: ReviewCommission.from_mapping(abbreviated),
            "source_commit")
    empty = commission_mapping()
    empty["checklist"] = []
    rejects(lambda: ReviewCommission.from_mapping(empty), "non-zero")


@test("SOUND and affirmative-order verdicts cannot hide failed coverage",
      kind="known_bad")
def t_verdict_invariants():
    failed = witness_mapping()
    failed["checklist"] = [
        {"item": "body_registration", "status": "FAIL"},
        {"item": "thermal_path", "status": "PASS"}]
    rejects(lambda: ReviewWitness.from_mapping(failed), "SOUND requires")
    failed["design_verdict"] = "DEFECTIVE"
    rejects(lambda: ReviewWitness.from_mapping(failed), "only a SOUND")
    partial = witness_mapping(graded=1)
    rejects(lambda: ReviewWitness.from_mapping(partial), "graded/total")


@test("require_admissible raises with all refusal reasons", kind="known_bad")
def t_require_admissible():
    commission = ReviewCommission.from_mapping(commission_mapping())
    witness = ReviewWitness.from_mapping(witness_mapping(
        completed_at="2026-08-12T10:11:00Z"))
    try:
        require_admissible(commission, witness)
    except ReviewInadmissibleError as exc:
        check("LATE" in str(exc) and "OUTPUT_NOT_OBSERVED" in str(exc),
              "inadmissibility reasons were lost")
    else:
        raise AssertionError("inadmissible review was required successfully")


if __name__ == "__main__":
    raise SystemExit(main())
