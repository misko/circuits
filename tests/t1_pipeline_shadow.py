#!/usr/bin/env python3
"""T1: single-execution legacy observations and exact shadow comparison."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))
from pipeline_contract import StageResult, StageSpec  # noqa: E402
from pipeline_identity import SubjectIdentity  # noqa: E402
from pipeline_registry import StageRegistry  # noqa: E402
from pipeline_shadow import (LegacyCompletion, LegacyVerdict,  # noqa: E402
                             ShadowObserver, ShadowRunContext,
                             ShadowValidationError, compare_observed_run)
from pipeline_timing import StageSpan  # noqa: E402


SUBJECT = SubjectIdentity("a" * 64, "b" * 64)
RUN_ID = "20260812T170000Z-shadow01"


def spec(stage_id, *, requires=(), produces=(), work_class="local"):
    return StageSpec(
        id=stage_id, owner="pcb-design", lifecycle="schematic", cost="cheap",
        work_class=work_class, timeout_s=30,
        requires=tuple(sorted(requires)), produces=tuple(sorted(produces)),
        blocks=(), invalidated_by=())


SPECS = (
    spec("P-ONE", produces=("fact_one",)),
    spec("P-TWO", requires=("fact_one",), produces=("fact_two",)),
    spec("P-THREE", requires=("fact_two",)),
)
REGISTRY = StageRegistry(SPECS)
CONTEXT = ShadowRunContext(run_id=RUN_ID, subject=SUBJECT)


def clocks(times, monotonic):
    time_values = iter(times)
    mono_values = iter(monotonic)
    return lambda: next(time_values), lambda: next(mono_values)


def completion(label, *, rc=0, elapsed=1, outputs=(), timed_out=False,
               cancelled=False, child_rc=None):
    return LegacyCompletion(
        legacy_label=label, argv=("legacy-tool", "--stage", label),
        child_returncode=rc if child_rc is None else child_rc,
        authority_returncode=rc, timed_out=timed_out, cancelled=cancelled,
        subprocess_elapsed_s=elapsed, accepted_outputs=tuple(sorted(outputs)))


def verdict(status="PASS", *, resume=None):
    return LegacyVerdict(
        applicability="APPLIES", applicability_reason=None, status=status,
        graded=1 if status == "PASS" else 0, total=1,
        findings=() if status == "PASS" else ({"legacy_status": status},),
        resume_argv=resume)


def observe(stage_spec, start, finish, *, dependencies=(), status="PASS",
            outputs=(), rc=0, resume=None, context=CONTEXT,
            subject_after=None):
    utc, mono = clocks(
        (f"2026-08-12T17:00:{start:02d}Z",
         f"2026-08-12T17:00:{finish:02d}Z"),
        (float(start), float(finish)))
    observer = ShadowObserver(lambda event: None, utc_clock=utc,
                              monotonic_clock=mono)
    token = observer.begin(context, stage_spec, dependencies=dependencies)
    return observer.finish(
        token, subject_after=(context.subject if subject_after is None
                              else subject_after),
        completion=completion(
            stage_spec.id, rc=rc, elapsed=finish - start, outputs=outputs),
        verdict=verdict(status, resume=resume))


def rejects(fn, expected, what):
    try:
        fn()
    except (ShadowValidationError, ValueError) as exc:
        check(expected in str(exc),
              f"{what}: {exc!s} does not contain {expected!r}")
    else:
        raise AssertionError(f"{what}: malformed shadow evidence SHOULD HAVE FAILED")


@test("observer emits an incomplete start before projecting one legacy execution")
def t_observe_clean():
    events = []
    utc, mono = clocks(
        ("2026-08-12T17:00:00Z", "2026-08-12T17:00:03Z"), (10, 13))
    observer = ShadowObserver(events.append, utc_clock=utc,
                              monotonic_clock=mono)
    token = observer.begin(CONTEXT, SPECS[0])
    eq(len(events), 1, "start event count before legacy completion")
    eq(events[0]["event"], "STARTED", "start event kind")
    eq(events[0]["status"], "INCOMPLETE", "crash-safe start status")

    legacy = completion("legacy_one", elapsed=2.5, outputs=("fact_one",))
    observed = observer.finish(
        token, subject_after=SUBJECT, completion=legacy, verdict=verdict())
    check(isinstance(observed.result, StageResult), "strict StageResult projection")
    check(isinstance(observed.span, StageSpan), "strict StageSpan projection")
    eq(observed.result.outputs, ("fact_one",), "accepted output projection")
    eq(observed.span.elapsed_s, 3.0, "outer monotonic duration")
    eq(observed.span.subprocess_elapsed_s, 2.5, "inner subprocess duration")
    eq(observed.legacy.authority_returncode, 0, "legacy authority retained")
    eq(events[1]["event"], "FINISHED", "finish event kind")


@test("explicit non-applicability executes nothing and remains reasoned")
def t_not_applicable():
    events = []
    observer = ShadowObserver(
        events.append, utc_clock=lambda: "2026-08-12T17:00:00Z")
    observed = observer.not_applicable(
        CONTEXT, SPECS[0], reason="project declares no matching subsystem")
    eq(observed.result.status, "NOT_APPLICABLE", "N/A result status")
    eq(observed.result.total, 0, "N/A denominator")
    eq(observed.span.elapsed_s, 0.0, "N/A elapsed time")
    eq(events[0]["event"], "FINISHED", "N/A event kind")


@test("observer refuses drift, overclaim and impossible PASS projections",
      kind="known_bad")
def t_projection_failures():
    def attempt(completed, legacy_verdict=verdict(), *, after=SUBJECT,
                mono=(0, 2)):
        utc, monotonic = clocks(
            ("2026-08-12T17:00:00Z", "2026-08-12T17:00:02Z"), mono)
        observer = ShadowObserver(lambda event: None, utc_clock=utc,
                                  monotonic_clock=monotonic)
        token = observer.begin(CONTEXT, SPECS[0])
        return observer.finish(
            token, subject_after=after, completion=completed,
            verdict=legacy_verdict)

    rejects(lambda: attempt(completion("one"),
                            after=SubjectIdentity("c" * 64, "b" * 64)),
            "subject drifted", "semantic subject drift")
    rejects(lambda: attempt(completion("one", outputs=("invented",))),
            "overclaims", "undeclared output")
    rejects(lambda: attempt(completion(
        "one", rc=124, timed_out=True, elapsed=1)),
        "timed-out or cancelled", "timed-out PASS")
    rejects(lambda: attempt(completion(
        "one", rc=125, cancelled=True, elapsed=1)),
        "timed-out or cancelled", "cancelled PASS")
    rejects(lambda: attempt(completion("one", rc=6)),
            "nonzero legacy authority", "budget-failed PASS")
    rejects(lambda: attempt(completion("one", elapsed=3)),
            "cannot exceed", "subprocess longer than envelope")


@test("shadow sink failure cannot rewrite the immutable legacy authority result",
      kind="known_bad")
def t_sink_failure_authority():
    calls = 0

    def sink(event):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("evidence disk unavailable")

    utc, mono = clocks(
        ("2026-08-12T17:00:00Z", "2026-08-12T17:00:01Z"), (0, 1))
    observer = ShadowObserver(sink, utc_clock=utc, monotonic_clock=mono)
    token = observer.begin(CONTEXT, SPECS[0])
    legacy = completion("one", rc=7)
    rejects(lambda: observer.finish(
        token, subject_after=SUBJECT, completion=legacy,
        verdict=verdict("FAIL")), "shadow sink rejected", "finish sink")
    eq(legacy.authority_returncode, 7, "legacy authority remains untouched")


@test("completed, failed and explicitly paused traces compare by exact scope")
def t_compare_clean_modes():
    one = observe(SPECS[0], 0, 1, outputs=("fact_one",))
    two = observe(SPECS[1], 1, 2, dependencies=("P-ONE",),
                  outputs=("fact_two",))
    three = observe(SPECS[2], 2, 3, dependencies=("P-TWO",))
    complete = compare_observed_run(
        REGISTRY, CONTEXT, [one, two, three], termination="COMPLETED")
    check(complete.agrees, f"complete trace mismatch: {complete.mismatches}")
    eq(complete.not_reached, (), "complete not-reached stages")

    failed_two = observe(
        SPECS[1], 1, 2, dependencies=("P-ONE",), status="FAIL", rc=7)
    failed = compare_observed_run(
        REGISTRY, CONTEXT, [one, failed_two], termination="FAILED")
    check(failed.agrees, f"failed prefix mismatch: {failed.mismatches}")
    eq(failed.not_reached, ("P-THREE",), "failed not-reached tail")

    paused_two = observe(
        SPECS[1], 1, 2, dependencies=("P-ONE",), status="INCOMPLETE",
        rc=125, resume=("rebuild_all.sh", "--resume"))
    paused = compare_observed_run(
        REGISTRY, CONTEXT, [one, paused_two], termination="PAUSED")
    check(paused.agrees, f"paused prefix mismatch: {paused.mismatches}")
    eq(paused.not_reached, ("P-THREE",), "paused not-reached tail")


@test("resume scope treats checkpoint facts as external, not missing spans")
def t_compare_resume_scope():
    resume_context = ShadowRunContext(
        run_id="20260812T180000Z-resume01", subject=SUBJECT,
        target_stage_ids=("P-THREE",), available_facts=("fact_two",),
        segment="resume_after_review")
    resumed = observe(SPECS[2], 0, 1, context=resume_context)
    comparison = compare_observed_run(
        REGISTRY, resume_context, [resumed], termination="COMPLETED")
    check(comparison.agrees,
          f"resume scope mismatch: {comparison.mismatches}")
    eq(resumed.span.dependencies, (), "checkpoint fact is not an executed span")
    eq(comparison.expected, ("P-THREE",), "resume target closure")


@test("comparison refuses reordered, partial-complete and semantically false traces",
      kind="known_bad")
def t_compare_failures():
    one = observe(SPECS[0], 0, 1, outputs=("fact_one",))
    two = observe(SPECS[1], 1, 2, dependencies=("P-ONE",),
                  outputs=("fact_two",))
    three = observe(SPECS[2], 2, 3, dependencies=("P-TWO",))

    reordered = compare_observed_run(
        REGISTRY, CONTEXT, [two, one, three], termination="COMPLETED")
    check(not reordered.agrees, "reordered trace was accepted")
    eq(reordered.first_divergence, 0, "reordered first divergence")

    partial = compare_observed_run(
        REGISTRY, CONTEXT, [one, two], termination="COMPLETED")
    check(not partial.agrees, "partial trace claimed COMPLETED")
    eq(partial.not_reached, ("P-THREE",), "partial not-reached reporting")

    false_failure = compare_observed_run(
        REGISTRY, CONTEXT, [one], termination="FAILED")
    check(not false_failure.agrees, "PASS-ending failed trace was accepted")

    wrong_dep = observe(SPECS[1], 1, 2, outputs=("fact_two",))
    dependency = compare_observed_run(
        REGISTRY, CONTEXT, [one, wrong_dep], termination="ABORTED")
    check(not dependency.agrees, "wrong dependency set was accepted")
    check(any("dependencies" in item for item in dependency.mismatches),
          "dependency mismatch was not named")

    missing_output = observe(SPECS[0], 0, 1)
    outputs = compare_observed_run(
        REGISTRY, CONTEXT, [missing_output], termination="COMPLETED")
    check(not outputs.agrees, "PASS missing its declared output was accepted")
    check(any("outputs" in item for item in outputs.mismatches),
          "output mismatch was not named")

    other_run_context = ShadowRunContext(
        run_id="20260812T170000Z-other", subject=SUBJECT)
    other_run = observe(
        SPECS[0], 0, 1, outputs=("fact_one",), context=other_run_context)
    mixed_run = compare_observed_run(
        REGISTRY, CONTEXT, [other_run], termination="COMPLETED")
    check(any("run_id differs" in item for item in mixed_run.mismatches),
          "mixed run id was not diagnosed")

    other_subject_context = ShadowRunContext(
        run_id=RUN_ID, subject=SubjectIdentity("c" * 64, "d" * 64))
    other_subject = observe(
        SPECS[0], 0, 1, outputs=("fact_one",),
        context=other_subject_context)
    mixed_subject = compare_observed_run(
        REGISTRY, CONTEXT, [other_subject], termination="COMPLETED")
    check(any("subject differs" in item for item in mixed_subject.mismatches),
          "mixed subject was not diagnosed")


if __name__ == "__main__":
    raise SystemExit(main())
