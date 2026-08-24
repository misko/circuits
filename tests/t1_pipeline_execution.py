#!/usr/bin/env python3
"""T1: strict task/session envelopes around unchanged PCB stages."""
from __future__ import annotations

import sys
import hashlib
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "skills/pcb-design/scripts"
sys.path.insert(0, str(PIPELINE))

from pipeline_execution import (  # noqa: E402
    AgentSpan, ExecutionValidationError, TaskAttempt, TaskEnvelope,
    aggregate_token_usage, context_handoff_decision, envelope_sha256,
    replacement_admissible, verify_input_packet,
)
from pipeline_identity import TypedIdentityInput, subject_identity  # noqa: E402


def ident():
    return subject_identity("execution", 1, [TypedIdentityInput(
        "packet", "mapping", {"stage": "routing", "board": "abc"},
        b"stage: routing\nboard: abc\n")])


def packet():
    return [{"name": "handoff", "path": "06_build/agent_handoff.yaml",
             "sha256": "1" * 64, "size": 512}]


def envelope_mapping(**changes):
    value = {
        "schema": 1,
        "task_id": "route-wave-1",
        "stage_id": "KICAD-ROUTING",
        "run_id": "20260824T120000Z-a1",
        "subject": ident().to_mapping(),
        "executor": "agent",
        "execution_class": "local",
        "recommended_agent_role": "mechanical",
        "agent_role": "mechanical",
        "role_escalation_reason": None,
        "context_mode": "FRESH",
        "input_handoff_id": "handoff-a1",
        "input_packet": packet(),
        "deadline_at": "2026-08-24T12:10:00Z",
        "max_nonimproving_attempts": 2,
        "replacement_limit": 1,
        "writer_scope": {"mode": "EXCLUSIVE",
                         "paths": ["03_src/route/final.kicad_pcb"]},
        "output_path": "06_build/orchestration/attempts/route-wave-1.json",
    }
    value.update(changes)
    return value


def rejects(fn, expected):
    try:
        fn()
    except ExecutionValidationError as exc:
        check(expected in str(exc), f"{exc!s} does not contain {expected!r}")
    else:
        raise AssertionError("malformed execution contract SHOULD HAVE FAILED")


def span_mapping(**changes):
    value = {
        "schema": 1, "task_id": "route-wave-1",
        "stage_id": "KICAD-ROUTING", "run_id": "run-1",
        "subject": ident().to_mapping(), "agent_role": "mechanical",
        "context_mode": "FRESH", "started_at": "2026-08-24T12:00:00Z",
        "finished_at": "2026-08-24T12:00:10Z", "elapsed_s": 10.0,
        "status": "PASS", "replacement_index": 0,
        "token_usage": {"authority": "app_task_history",
                        "metric": "raw_rollout", "input": 100,
                        "cached_input": 80, "output": 20, "total": 120},
    }
    value.update(changes)
    return value


@test("TaskEnvelope round-trips a fresh content-addressed agent packet")
def t_envelope_roundtrip():
    source = envelope_mapping()
    envelope = TaskEnvelope.from_mapping(source)
    eq(envelope.to_mapping(), source, "TaskEnvelope mapping")
    eq(TaskEnvelope.from_json(envelope.to_json()), envelope,
       "TaskEnvelope canonical JSON")


@test("subprocess envelope uses execution class without an agent role")
def t_subprocess_envelope():
    envelope = TaskEnvelope.from_mapping(envelope_mapping(
        executor="subprocess", recommended_agent_role=None, agent_role=None,
        context_mode="NOT_APPLICABLE", input_handoff_id=None,
        role_escalation_reason=None, input_packet=[],
        writer_scope={"mode": "READ_ONLY", "paths": []}))
    eq(envelope.execution_class, "local", "execution-class attribution")


@test("fresh agent work requires an exact non-empty handoff packet",
      kind="known_bad")
def t_fresh_requires_packet():
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(input_packet=[])),
            "non-empty input packet")
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(
        input_handoff_id=None)), "requires input_handoff_id")


@test("review work cannot inherit a prior context", kind="known_bad")
def t_review_fresh():
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(
        executor="reviewer", context_mode="CONTINUATION",
        input_handoff_id=None)), "reviewer executor must use FRESH")
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(
        executor="reviewer", writer_scope={"mode": "EXCLUSIVE",
        "paths": ["08_reviews/review.md"]})),
        "reviewer executor must use READ_ONLY")


@test("agent role escalation is explicit and reasoned", kind="known_bad")
def t_role_escalation():
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(
        agent_role="judgment")), "role escalation requires")
    allowed = TaskEnvelope.from_mapping(envelope_mapping(
        agent_role="judgment",
        role_escalation_reason="causal D-BACK diagnosis is the output"))
    eq(allowed.agent_role, "judgment", "reasoned escalation")


@test("writer scope is traversal-free, sorted and exclusive",
      kind="known_bad")
def t_writer_scope():
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(
        writer_scope={"mode": "EXCLUSIVE", "paths": []})),
        "requires at least one owned path")
    rejects(lambda: TaskEnvelope.from_mapping(envelope_mapping(
        writer_scope={"mode": "EXCLUSIVE", "paths": ["../outside"]})),
        "traversal-free")


@test("semantic boundaries and D-BACK require a fresh successor")
def t_context_boundaries():
    eq(context_handoff_decision(
        context_used_pct=None, boundary="placement_feasibility_adopted")
       ["decision"], "HANDOFF_REQUIRED", "placement boundary")
    eq(context_handoff_decision(context_used_pct=10, d_back=True)["decision"],
       "HANDOFF_REQUIRED", "D-BACK")


@test("context thresholds warn at 60 percent and stop at 70 percent")
def t_context_thresholds():
    eq(context_handoff_decision(context_used_pct=59)["decision"], "CONTINUE")
    eq(context_handoff_decision(context_used_pct=60)["decision"], "WARN")
    eq(context_handoff_decision(context_used_pct=70)["decision"],
       "HANDOFF_REQUIRED")


@test("token telemetry preserves cached input and one accounting authority")
def t_token_aggregation():
    first = AgentSpan.from_mapping(span_mapping())
    second = AgentSpan.from_mapping(span_mapping(
        task_id="route-wave-2", token_usage={"authority": "app_task_history",
        "metric": "raw_rollout", "input": 50, "cached_input": 30,
        "output": 10, "total": 60}))
    summary = aggregate_token_usage([first, second])
    eq(summary["status"], "MEASURED")
    eq(summary["input"], 150)
    eq(summary["cached_input"], 110)
    eq(summary["output"], 30)
    eq(summary["total"], 180)


@test("missing or incomparable token telemetry is UNKNOWN, never zero",
      kind="known_bad")
def t_unknown_token_telemetry():
    measured = AgentSpan.from_mapping(span_mapping())
    missing = AgentSpan.from_mapping(span_mapping(
        task_id="route-wave-2", token_usage=None))
    unknown = aggregate_token_usage([measured, missing])
    eq(unknown["status"], "UNKNOWN")
    check("total" not in unknown, "unknown telemetry was rendered as zero")
    normalized = AgentSpan.from_mapping(span_mapping(
        task_id="route-wave-3", token_usage={"authority": "app_task_history",
        "metric": "normalized_goal", "input": 1, "cached_input": 0,
        "output": 1, "total": 2}))
    eq(aggregate_token_usage([measured, normalized])["status"], "UNKNOWN",
       "raw and normalized metrics were added")


@test("timeout and handoff attempts retain explicit unresolved work",
      kind="known_bad")
def t_attempt_unresolved():
    base = {"schema": 1, "task_id": "review-1",
            "envelope_sha256": "2" * 64, "attempt_index": 0,
            "replacement_index": 0, "subject": ident().to_mapping(),
            "started_at": "2026-08-24T12:00:00Z",
            "finished_at": "2026-08-24T12:01:00Z", "elapsed_s": 60,
            "status": "TIMED_OUT", "unresolved": [], "output": None}
    rejects(lambda: TaskAttempt.from_mapping(base),
            "requires explicit unresolved work")
    base["unresolved"] = [{"check": "pin review", "status": "INCOMPLETE"}]
    attempt = TaskAttempt.from_mapping(base)
    eq(attempt.status, "TIMED_OUT")


@test("replacement ceiling permits exactly the declared replacements")
def t_replacement_limit():
    envelope = TaskEnvelope.from_mapping(envelope_mapping(replacement_limit=1))
    digest = envelope_sha256(envelope)
    attempt = TaskAttempt(
        task_id=envelope.task_id, envelope_sha256=digest,
        attempt_index=0, replacement_index=0, subject=ident(),
        started_at="2026-08-24T12:00:00Z",
        finished_at="2026-08-24T12:01:00Z", elapsed_s=60,
        status="TIMED_OUT", unresolved=[{"check": "layout"}], output=None)
    check(replacement_admissible(envelope, [attempt]),
          "first replacement should be admissible")
    replacement = TaskAttempt(
        task_id=envelope.task_id, envelope_sha256=digest,
        attempt_index=1, replacement_index=1, subject=ident(),
        started_at="2026-08-24T12:01:00Z",
        finished_at="2026-08-24T12:02:00Z", elapsed_s=60,
        status="FAIL", unresolved=[{"check": "layout"}], output=None)
    check(not replacement_admissible(envelope, [attempt, replacement]),
          "second replacement exceeded ceiling")


@test("packet declarations are reopened and hash verified", kind="known_bad")
def t_packet_reopen():
    root = Path(tempfile.mkdtemp(prefix="task-packet-"))
    path = root / "06_build/agent_handoff.yaml"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"handoff: exact\n")
    item = [{"name": "handoff", "path": "06_build/agent_handoff.yaml",
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
             "size": path.stat().st_size}]
    envelope = TaskEnvelope.from_mapping(envelope_mapping(input_packet=item))
    check(verify_input_packet(envelope, root)[0], "exact packet should reopen")
    path.write_bytes(b"handoff: changed\n")
    valid, failures = verify_input_packet(envelope, root)
    check(not valid and any("changed" in row for row in failures),
          "mutated packet was accepted")


@test("replacement accounting is scoped to exact envelope and subject",
      kind="known_bad")
def t_replacement_scope():
    envelope = TaskEnvelope.from_mapping(envelope_mapping(replacement_limit=0))
    foreign = TaskAttempt(
        task_id=envelope.task_id, envelope_sha256="3" * 64,
        attempt_index=0, replacement_index=99, subject=ident(),
        started_at="2026-08-24T12:00:00Z",
        finished_at="2026-08-24T12:01:00Z", elapsed_s=60,
        status="FAIL", unresolved=[{"check": "other envelope"}], output=None)
    check(replacement_admissible(envelope, [foreign]),
          "another envelope consumed this task's replacement ceiling")


@test("elapsed duration must agree with timestamps", kind="known_bad")
def t_elapsed_consistency():
    rejects(lambda: AgentSpan.from_mapping(span_mapping(elapsed_s=1.0)),
            "disagrees with timestamps")


if __name__ == "__main__":
    sys.exit(main())
