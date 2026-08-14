#!/usr/bin/env python3
"""Focused tests for schema-1 cross-stage timing aggregation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "pcb-design" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from pipeline_identity import SubjectIdentity  # noqa: E402
from pipeline_timing import (StageSpan, TimingValidationError,  # noqa: E402
                             summarize_spans)


SUBJECT = SubjectIdentity("a" * 64, "b" * 64)
RUN_ID = "20260812T170000Z-8d31a2f0"


def span(stage_id, started, finished, elapsed, work_class="local", *,
         subprocess=None, dependencies=(), cache="MISS", status="PASS",
         run_id=RUN_ID, subject=SUBJECT, resume=None):
    if subprocess is None:
        subprocess = elapsed
    return StageSpan(
        stage_id=stage_id,
        run_id=run_id,
        subject=subject,
        work_class=work_class,
        started_at=f"2026-08-12T17:00:{started:02d}Z",
        finished_at=f"2026-08-12T17:00:{finished:02d}Z",
        elapsed_s=elapsed,
        subprocess_elapsed_s=subprocess,
        dependencies=dependencies,
        cache_status=cache,
        status=status,
        resume_argv=resume,
    )


def rejects(fn, expected, what):
    try:
        fn()
    except TimingValidationError as exc:
        check(expected in str(exc),
              f"{what}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{what}: malformed timing SHOULD HAVE FAILED")


@test("StageSpan round-trips exact schema-1 data without executing resume argv")
def t_span_roundtrip():
    source = {
        "schema": 1,
        "stage_id": "P-FETCH",
        "run_id": RUN_ID,
        "subject": SUBJECT.to_mapping(),
        "work_class": "network",
        "started_at": "2026-08-12T17:00:00Z",
        "finished_at": "2026-08-12T17:00:10Z",
        "elapsed_s": 9.75,
        "subprocess_elapsed_s": 8.5,
        "dependencies": ["P-PREFLIGHT"],
        "cache_status": "MISS",
        "status": "TIMED_OUT",
        "resume_argv": ["fetch-model", "--part", "C123;still-one-argument"],
    }
    observed = StageSpan.from_mapping(source)
    eq(observed.to_mapping(), source, "StageSpan mapping")
    eq(StageSpan.from_json(observed.to_json()), observed, "StageSpan JSON")
    eq(observed.resume_argv,
       ("fetch-model", "--part", "C123;still-one-argument"),
       "resume command remains argv data")


@test("overlapping local/network/wait spans report the correct critical path")
def t_known_aggregate():
    # Independent local and network work overlap. P-REVIEW starts ten seconds
    # after its dependency, so observed wall span is intentionally larger than
    # the dependency-duration critical path.
    spans = [
        span("P-LOCAL", 0, 4, 4, subprocess=4),
        span("P-NETWORK", 0, 10, 10, "network", subprocess=8),
        span("P-BACKOFF", 4, 10, 6, "backoff", subprocess=0,
             dependencies=("P-LOCAL",)),
        span("P-CONSUME", 10, 13, 3, subprocess=3,
             dependencies=("P-BACKOFF", "P-NETWORK")),
        span("P-REVIEW", 20, 40, 20, "review_wait", subprocess=0,
             dependencies=("P-NETWORK",)),
        span("P-OPERATOR", 40, 45, 5, "operator_wait", subprocess=0,
             dependencies=("P-REVIEW",)),
    ]
    summary = summarize_spans(list(reversed(spans)))
    eq(summary.stage_count, 6, "stage denominator")
    eq(summary.wall_span_s, 45.0, "observed UTC run envelope")
    eq(summary.summed_stage_elapsed_s, 48.0, "summed stage work")
    eq(summary.aggregate_subprocess_elapsed_s, 15.0,
       "aggregate subprocess work")
    eq(summary.critical_path_elapsed_s, 35.0,
       "dependency-duration critical path")
    eq(summary.critical_path_stage_ids,
       ("P-NETWORK", "P-REVIEW", "P-OPERATOR"), "critical path ids")
    eq(summary.work_class_elapsed_s, {
        "local": 7.0,
        "network": 10.0,
        "backoff": 6.0,
        "review_wait": 20.0,
        "operator_wait": 5.0,
    }, "productive/wait work-class split")
    eq(summary.work_class_subprocess_s, {
        "local": 7.0,
        "network": 8.0,
        "backoff": 0.0,
        "review_wait": 0.0,
        "operator_wait": 0.0,
    }, "subprocess work-class split")
    eq(summary.cache_counts, {"HIT": 0, "MISS": 6}, "cache counts")
    eq(summary.status_counts["PASS"], 6, "PASS count")
    eq(summary.to_mapping()["critical_path_stage_ids"],
       ["P-NETWORK", "P-REVIEW", "P-OPERATOR"], "serialized path")


@test("critical-path ties resolve deterministically by complete stage-id path")
def t_deterministic_tie():
    spans = [
        span("P-BETA", 0, 1, 1),
        span("P-ALPHA", 0, 1, 1),
        span("P-JOIN", 1, 2, 1,
             dependencies=("P-ALPHA", "P-BETA")),
    ]
    summary = summarize_spans(spans)
    eq(summary.critical_path_elapsed_s, 2.0, "tie duration")
    eq(summary.critical_path_stage_ids, ("P-ALPHA", "P-JOIN"),
       "lexicographic deterministic tie")


@test("critical path reaches a dependency-graph terminal even at zero cost")
def t_zero_cost_terminal():
    spans = [
        span("P-WORK", 0, 2, 2),
        span("P-ZERO-CLOSE", 2, 2, 0, subprocess=0,
             dependencies=("P-WORK",)),
    ]
    summary = summarize_spans(spans)
    eq(summary.critical_path_elapsed_s, 2.0, "zero-cost terminal duration")
    eq(summary.critical_path_stage_ids, ("P-WORK", "P-ZERO-CLOSE"),
       "source-to-terminal path ids")


@test("zero-time NOT_APPLICABLE span remains explicit and non-resumable")
def t_not_applicable():
    observed = span(
        "P-NO-RF", 0, 0, 0, subprocess=0, status="NOT_APPLICABLE")
    summary = summarize_spans([observed])
    eq(summary.status_counts["NOT_APPLICABLE"], 1,
       "not-applicable result count")
    eq(summary.critical_path_elapsed_s, 0.0, "not-applicable path duration")


@test("StageSpan rejects unknown vocabularies, ids, fields and unsafe argv",
      kind="known_bad")
def t_schema_failures():
    base = span("P-CLEAN", 0, 1, 1).to_mapping()
    for field, bad in (("work_class", "sleep"), ("cache_status", "MAYBE"),
                       ("status", "SUCCESS")):
        changed = dict(base)
        changed[field] = bad
        rejects(lambda changed=changed: StageSpan.from_mapping(changed),
                "expected one of", f"unknown {field}")
    changed = dict(base, stage_id="bad_stage")
    rejects(lambda: StageSpan.from_mapping(changed), "expected ^[A-Z]",
            "malformed stage id")
    changed = dict(base, run_id="run id/with spaces")
    rejects(lambda: StageSpan.from_mapping(changed), "run_id: expected",
            "malformed run id")
    changed = dict(base, hidden_command="shell text")
    rejects(lambda: StageSpan.from_mapping(changed), "unknown=['hidden_command']",
            "unknown execution field")
    changed = dict(base, resume_argv="fetch-model --all")
    rejects(lambda: StageSpan.from_mapping(changed), "argv list",
            "shell-string resume command")
    changed = dict(base, resume_argv=["fetch\0model"])
    rejects(lambda: StageSpan.from_mapping(changed), "NUL bytes",
            "NUL-bearing argv")


@test("StageSpan rejects malformed, negative or internally impossible timing",
      kind="known_bad")
def t_timing_failures():
    base = span("P-CLEAN", 0, 1, 1).to_mapping()
    for field, bad in (("elapsed_s", -1), ("elapsed_s", float("nan")),
                       ("subprocess_elapsed_s", -0.1)):
        changed = dict(base)
        changed[field] = bad
        rejects(lambda changed=changed: StageSpan.from_mapping(changed),
                "non-negative finite", f"malformed {field}")
    changed = dict(base, subprocess_elapsed_s=1.01)
    rejects(lambda: StageSpan.from_mapping(changed), "cannot exceed elapsed_s",
            "subprocess exceeds stage")
    changed = dict(base, started_at="2026-08-12T17:00:00+00:00")
    rejects(lambda: StageSpan.from_mapping(changed), "ending in Z",
            "noncanonical UTC timestamp")
    changed = dict(base, started_at="2026-08-12 17:00:00Z")
    rejects(lambda: StageSpan.from_mapping(changed), "canonical RFC3339",
            "UTC timestamp without canonical T separator")
    changed = dict(base, started_at="2026-08-12T17:00:02Z")
    rejects(lambda: StageSpan.from_mapping(changed), "cannot precede",
            "reversed timestamps")
    changed = span("P-NA", 0, 0, 0, subprocess=0,
                   status="NOT_APPLICABLE").to_mapping()
    changed["elapsed_s"] = 1
    rejects(lambda: StageSpan.from_mapping(changed), "zero elapsed",
            "timed NOT_APPLICABLE")
    changed["elapsed_s"] = 0
    changed["resume_argv"] = ["retry"]
    rejects(lambda: StageSpan.from_mapping(changed), "cannot carry resume",
            "resumable NOT_APPLICABLE")


@test("aggregator rejects duplicate, missing, cyclic and overlapping dependencies",
      kind="known_bad")
def t_graph_failures():
    clean = span("P-CLEAN", 0, 1, 1)
    rejects(lambda: summarize_spans([clean, clean]), "duplicate stage_id",
            "duplicate stage")
    missing = span("P-CONSUME", 2, 3, 1, dependencies=("P-ABSENT",))
    rejects(lambda: summarize_spans([missing]), "missing dependencies",
            "missing dependency")
    # Non-zero observations deliberately make one edge temporally impossible;
    # structural cycle diagnosis must still win over incidental wall ordering.
    cycle_a = span("P-A", 0, 1, 1, dependencies=("P-B",))
    cycle_b = span("P-B", 1, 2, 1, dependencies=("P-A",))
    rejects(lambda: summarize_spans([cycle_a, cycle_b]), "contains a cycle",
            "dependency cycle")
    producer = span("P-PRODUCE", 0, 5, 5)
    early_consumer = span(
        "P-CONSUME", 4, 6, 2, dependencies=("P-PRODUCE",))
    rejects(lambda: summarize_spans([producer, early_consumer]),
            "had not finished", "dependency overlap")
    rejects(lambda: span(
        "P-JOIN", 2, 3, 1, dependencies=("P-ZED", "P-ALPHA")),
        "sorted and unique",
            "unordered dependencies")


@test("aggregator refuses spans from a different run or immutable subject",
      kind="known_bad")
def t_run_subject_failures():
    first = span("P-FIRST", 0, 1, 1)
    other_run = span("P-OTHER", 1, 2, 1, run_id="different-run")
    rejects(lambda: summarize_spans([first, other_run]), "run_id does not match",
            "mixed run")
    other_subject = span(
        "P-OTHER", 1, 2, 1,
        subject=SubjectIdentity("c" * 64, "d" * 64))
    rejects(lambda: summarize_spans([first, other_subject]),
            "subject does not match", "mixed subject")


if __name__ == "__main__":
    raise SystemExit(main())
