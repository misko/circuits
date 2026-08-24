#!/usr/bin/env python3
"""Strict companion contracts for bounded subprocess and agent execution.

``StageSpec`` remains the engineering-stage authority.  This module describes
one execution attempt around a stage without changing the public lifecycle:

* ``TaskEnvelope`` binds an executor to an exact subject and input packet;
* ``TaskAttempt`` records the terminal outcome of one bounded attempt; and
* ``AgentSpan`` records agent/session time and optional, explicitly-attributed
  token telemetry without contaminating ``StageSpan``.

The module is deliberately orchestration-only.  It launches no process or
agent and contains no PCB engineering predicates.
"""
from __future__ import annotations

import json
import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

from pipeline_identity import SubjectIdentity


SCHEMA = 1
STAGE_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXECUTORS = frozenset({"subprocess", "agent", "reviewer", "operator"})
EXECUTION_CLASSES = frozenset({
    "local", "network", "backoff", "review_wait", "operator_wait",
})
AGENT_ROLES = ("mechanical", "authoring", "judgment")
CONTEXT_MODES = frozenset({"FRESH", "CONTINUATION", "NOT_APPLICABLE"})
WRITER_MODES = frozenset({"READ_ONLY", "EXCLUSIVE"})
ATTEMPT_STATUSES = frozenset({
    "PASS", "FAIL", "TIMED_OUT", "INCOMPLETE", "ERROR",
    "HANDOFF_REQUIRED",
})
TOKEN_METRICS = frozenset({"raw_rollout", "normalized_goal", "host_reported"})
MANDATORY_FRESH_BOUNDARIES = frozenset({
    "schematic_review_adopted", "placement_feasibility_adopted",
    "layout_sealed",
})


class ExecutionValidationError(ValueError):
    """An execution envelope/span is malformed or internally inconsistent."""


def _fail(message: str) -> None:
    raise ExecutionValidationError(message)


def _exact_fields(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing or unknown:
        _fail(f"{where}: fields differ (missing={sorted(missing)}, "
              f"unknown={sorted(unknown)})")


def _enum(value: Any, allowed: Sequence[str] | frozenset[str], where: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{where}: expected one of {sorted(allowed)}, got {value!r}")
    return value


def _token(value: Any, where: str) -> str:
    if not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None:
        _fail(f"{where}: expected {TOKEN_RE.pattern}, got {value!r}")
    return value


def _stage_id(value: Any) -> str:
    if not isinstance(value, str) or STAGE_ID_RE.fullmatch(value) is None:
        _fail(f"stage_id: expected {STAGE_ID_RE.pattern}, got {value!r}")
    return value


def _timestamp(value: Any, where: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value.endswith("Z"):
        _fail(f"{where}: expected canonical RFC3339 UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _fail(f"{where}: invalid RFC3339 timestamp {value!r}")
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        _fail(f"{where}: timestamp must be UTC")
    return value, parsed


def _duration(value: Any, where: str) -> float:
    if (not isinstance(value, (int, float)) or isinstance(value, bool) or
            not math.isfinite(value) or value < 0):
        _fail(f"{where}: expected a non-negative finite number")
    return float(value)


def _elapsed_matches(started: datetime, finished: datetime,
                     elapsed_s: float, where: str) -> None:
    measured = (finished - started).total_seconds()
    tolerance = max(0.001, measured * 0.01)
    if abs(elapsed_s - measured) > tolerance:
        _fail(f"{where}: elapsed_s {elapsed_s:g} disagrees with timestamps "
              f"({measured:g}s, tolerance {tolerance:g}s)")


def _nonnegative_int(value: Any, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _fail(f"{where}: expected a non-negative integer")
    return value


def _json_value(value: Any, where: str) -> Any:
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False)
        return json.loads(encoded)
    except (TypeError, ValueError) as exc:
        _fail(f"{where}: expected a finite JSON value ({exc})")


def _subject(value: SubjectIdentity | Mapping[str, Any]) -> SubjectIdentity:
    if isinstance(value, SubjectIdentity):
        return value
    if isinstance(value, Mapping):
        try:
            return SubjectIdentity.from_mapping(value)
        except ValueError as exc:
            _fail(f"subject: {exc}")
    _fail("subject: expected SubjectIdentity or its exact mapping")


def _relative_path(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        _fail(f"{where}: expected a non-empty relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or str(path) in {".", ""}:
        _fail(f"{where}: path must be project-relative and traversal-free")
    return path.as_posix()


@dataclass(frozen=True)
class PacketItem:
    name: str
    path: str
    sha256: str
    size: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or SYMBOL_RE.fullmatch(self.name) is None:
            _fail(f"packet.name: expected {SYMBOL_RE.pattern}")
        object.__setattr__(self, "path", _relative_path(self.path, "packet.path"))
        if not isinstance(self.sha256, str) or SHA256_RE.fullmatch(self.sha256) is None:
            _fail("packet.sha256: expected 64 lowercase hex characters")
        _nonnegative_int(self.size, "packet.size")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PacketItem":
        fields = {"name", "path", "sha256", "size"}
        _exact_fields(value, fields, "PacketItem")
        return cls(**{name: value[name] for name in fields})

    def to_mapping(self) -> dict[str, Any]:
        return {"name": self.name, "path": self.path,
                "sha256": self.sha256, "size": self.size}


@dataclass(frozen=True)
class WriterScope:
    mode: str
    paths: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _enum(self.mode, WRITER_MODES, "writer_scope.mode")
        if not isinstance(self.paths, (list, tuple)):
            _fail("writer_scope.paths: expected a sorted list")
        paths = tuple(_relative_path(item, "writer_scope.paths[]")
                      for item in self.paths)
        if list(paths) != sorted(set(paths)):
            _fail("writer_scope.paths: paths must be sorted and unique")
        if self.mode == "EXCLUSIVE" and not paths:
            _fail("writer_scope: EXCLUSIVE requires at least one owned path")
        if self.mode == "READ_ONLY" and paths:
            _fail("writer_scope: READ_ONLY cannot claim writable paths")
        object.__setattr__(self, "paths", paths)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "WriterScope":
        _exact_fields(value, {"mode", "paths"}, "WriterScope")
        return cls(mode=value["mode"], paths=value["paths"])

    def to_mapping(self) -> dict[str, Any]:
        return {"mode": self.mode, "paths": list(self.paths)}


@dataclass(frozen=True)
class TaskEnvelope:
    task_id: str
    stage_id: str
    run_id: str
    subject: SubjectIdentity | Mapping[str, Any]
    executor: str
    execution_class: str
    recommended_agent_role: Optional[str]
    agent_role: Optional[str]
    role_escalation_reason: Optional[str]
    context_mode: str
    input_handoff_id: Optional[str]
    input_packet: Sequence[PacketItem | Mapping[str, Any]]
    deadline_at: str
    max_nonimproving_attempts: int
    replacement_limit: int
    writer_scope: WriterScope | Mapping[str, Any]
    output_path: str
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _token(self.task_id, "task_id")
        _stage_id(self.stage_id)
        _token(self.run_id, "run_id")
        object.__setattr__(self, "subject", _subject(self.subject))
        _enum(self.executor, EXECUTORS, "executor")
        _enum(self.execution_class, EXECUTION_CLASSES, "execution_class")
        _enum(self.context_mode, CONTEXT_MODES, "context_mode")
        _timestamp(self.deadline_at, "deadline_at")
        if (not isinstance(self.max_nonimproving_attempts, int) or
                isinstance(self.max_nonimproving_attempts, bool) or
                self.max_nonimproving_attempts < 1):
            _fail("max_nonimproving_attempts: expected a positive integer")
        _nonnegative_int(self.replacement_limit, "replacement_limit")

        packet = tuple(PacketItem.from_mapping(row) if isinstance(row, Mapping)
                       else row for row in self.input_packet)
        if any(not isinstance(row, PacketItem) for row in packet):
            _fail("input_packet: expected PacketItem mappings")
        names = [row.name for row in packet]
        if names != sorted(set(names)):
            _fail("input_packet: item names must be sorted and unique")
        object.__setattr__(self, "input_packet", packet)

        scope = (WriterScope.from_mapping(self.writer_scope)
                 if isinstance(self.writer_scope, Mapping) else self.writer_scope)
        if not isinstance(scope, WriterScope):
            _fail("writer_scope: expected WriterScope or its exact mapping")
        object.__setattr__(self, "writer_scope", scope)
        object.__setattr__(self, "output_path",
                           _relative_path(self.output_path, "output_path"))

        is_agent = self.executor in {"agent", "reviewer"}
        if is_agent:
            _enum(self.recommended_agent_role, AGENT_ROLES,
                  "recommended_agent_role")
            _enum(self.agent_role, AGENT_ROLES, "agent_role")
            if self.context_mode == "NOT_APPLICABLE":
                _fail("agent/reviewer executor requires a context mode")
            if self.executor == "reviewer" and self.context_mode != "FRESH":
                _fail("reviewer executor must use FRESH context")
            if self.executor == "reviewer" and scope.mode != "READ_ONLY":
                _fail("reviewer executor must use READ_ONLY writer scope")
            if self.context_mode == "FRESH":
                if not isinstance(self.input_handoff_id, str) or not self.input_handoff_id:
                    _fail("FRESH context requires input_handoff_id")
                _token(self.input_handoff_id, "input_handoff_id")
                if not packet:
                    _fail("FRESH context requires a non-empty input packet")
            elif self.input_handoff_id is not None:
                _fail("CONTINUATION context cannot claim a fresh handoff id")
            baseline = AGENT_ROLES.index(self.recommended_agent_role)
            actual = AGENT_ROLES.index(self.agent_role)
            escalated = actual > baseline
            reason = self.role_escalation_reason
            if escalated and (not isinstance(reason, str) or not reason.strip()):
                _fail("role escalation requires a non-empty reason")
            if not escalated and reason not in (None, ""):
                _fail("role_escalation_reason is allowed only for escalation")
        else:
            if any(value is not None for value in (
                    self.recommended_agent_role, self.agent_role,
                    self.role_escalation_reason, self.input_handoff_id)):
                _fail("non-agent executor cannot carry agent/handoff fields")
            if self.context_mode != "NOT_APPLICABLE":
                _fail("non-agent executor requires NOT_APPLICABLE context")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskEnvelope":
        fields = {
            "schema", "task_id", "stage_id", "run_id", "subject",
            "executor", "execution_class", "recommended_agent_role",
            "agent_role", "role_escalation_reason", "context_mode",
            "input_handoff_id", "input_packet", "deadline_at",
            "max_nonimproving_attempts", "replacement_limit", "writer_scope",
            "output_path",
        }
        _exact_fields(value, fields, "TaskEnvelope")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "TaskEnvelope":
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError) as exc:
            _fail(f"TaskEnvelope JSON: {exc}")
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema, "task_id": self.task_id,
            "stage_id": self.stage_id, "run_id": self.run_id,
            "subject": self.subject.to_mapping(), "executor": self.executor,
            "execution_class": self.execution_class,
            "recommended_agent_role": self.recommended_agent_role,
            "agent_role": self.agent_role,
            "role_escalation_reason": self.role_escalation_reason,
            "context_mode": self.context_mode,
            "input_handoff_id": self.input_handoff_id,
            "input_packet": [row.to_mapping() for row in self.input_packet],
            "deadline_at": self.deadline_at,
            "max_nonimproving_attempts": self.max_nonimproving_attempts,
            "replacement_limit": self.replacement_limit,
            "writer_scope": self.writer_scope.to_mapping(),
            "output_path": self.output_path,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class TokenUsage:
    authority: str
    metric: str
    input: int
    cached_input: int
    output: int
    total: int

    def __post_init__(self) -> None:
        if not isinstance(self.authority, str) or not self.authority.strip():
            _fail("token_usage.authority: expected a non-empty authority")
        _enum(self.metric, TOKEN_METRICS, "token_usage.metric")
        for name in ("input", "cached_input", "output", "total"):
            _nonnegative_int(getattr(self, name), f"token_usage.{name}")
        if self.cached_input > self.input:
            _fail("token_usage.cached_input cannot exceed input")
        if self.total != self.input + self.output:
            _fail("token_usage.total must equal input + output")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TokenUsage":
        fields = {"authority", "metric", "input", "cached_input", "output", "total"}
        _exact_fields(value, fields, "TokenUsage")
        return cls(**{name: value[name] for name in fields})

    def to_mapping(self) -> dict[str, Any]:
        return {"authority": self.authority, "metric": self.metric,
                "input": self.input, "cached_input": self.cached_input,
                "output": self.output, "total": self.total}


@dataclass(frozen=True)
class AgentSpan:
    task_id: str
    stage_id: str
    run_id: str
    subject: SubjectIdentity | Mapping[str, Any]
    agent_role: str
    context_mode: str
    started_at: str
    finished_at: str
    elapsed_s: float
    status: str
    replacement_index: int
    token_usage: Optional[TokenUsage | Mapping[str, Any]] = None
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _token(self.task_id, "task_id")
        _stage_id(self.stage_id)
        _token(self.run_id, "run_id")
        object.__setattr__(self, "subject", _subject(self.subject))
        _enum(self.agent_role, AGENT_ROLES, "agent_role")
        if self.context_mode not in {"FRESH", "CONTINUATION"}:
            _fail("AgentSpan.context_mode must be FRESH or CONTINUATION")
        _enum(self.status, ATTEMPT_STATUSES, "status")
        started_text, started = _timestamp(self.started_at, "started_at")
        finished_text, finished = _timestamp(self.finished_at, "finished_at")
        if finished < started:
            _fail("finished_at cannot precede started_at")
        object.__setattr__(self, "started_at", started_text)
        object.__setattr__(self, "finished_at", finished_text)
        object.__setattr__(self, "elapsed_s", _duration(self.elapsed_s, "elapsed_s"))
        _elapsed_matches(started, finished, self.elapsed_s, "AgentSpan")
        _nonnegative_int(self.replacement_index, "replacement_index")
        usage = self.token_usage
        if isinstance(usage, Mapping):
            usage = TokenUsage.from_mapping(usage)
        if usage is not None and not isinstance(usage, TokenUsage):
            _fail("token_usage: expected null, TokenUsage, or its exact mapping")
        object.__setattr__(self, "token_usage", usage)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AgentSpan":
        fields = {"schema", "task_id", "stage_id", "run_id", "subject",
                  "agent_role", "context_mode", "started_at", "finished_at",
                  "elapsed_s", "status", "replacement_index", "token_usage"}
        _exact_fields(value, fields, "AgentSpan")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "AgentSpan":
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError) as exc:
            _fail(f"AgentSpan JSON: {exc}")
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        return {"schema": self.schema, "task_id": self.task_id,
                "stage_id": self.stage_id, "run_id": self.run_id,
                "subject": self.subject.to_mapping(),
                "agent_role": self.agent_role, "context_mode": self.context_mode,
                "started_at": self.started_at, "finished_at": self.finished_at,
                "elapsed_s": self.elapsed_s, "status": self.status,
                "replacement_index": self.replacement_index,
                "token_usage": (None if self.token_usage is None
                                else self.token_usage.to_mapping())}

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class TaskAttempt:
    task_id: str
    envelope_sha256: str
    attempt_index: int
    replacement_index: int
    subject: SubjectIdentity | Mapping[str, Any]
    started_at: str
    finished_at: str
    elapsed_s: float
    status: str
    unresolved: Sequence[Any] = field(default_factory=tuple)
    output: Any = None
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _token(self.task_id, "task_id")
        if not isinstance(self.envelope_sha256, str) or SHA256_RE.fullmatch(
                self.envelope_sha256) is None:
            _fail("envelope_sha256: expected 64 lowercase hex characters")
        _nonnegative_int(self.attempt_index, "attempt_index")
        _nonnegative_int(self.replacement_index, "replacement_index")
        object.__setattr__(self, "subject", _subject(self.subject))
        started_text, started = _timestamp(self.started_at, "started_at")
        finished_text, finished = _timestamp(self.finished_at, "finished_at")
        if finished < started:
            _fail("finished_at cannot precede started_at")
        object.__setattr__(self, "started_at", started_text)
        object.__setattr__(self, "finished_at", finished_text)
        object.__setattr__(self, "elapsed_s", _duration(self.elapsed_s, "elapsed_s"))
        _elapsed_matches(started, finished, self.elapsed_s, "TaskAttempt")
        _enum(self.status, ATTEMPT_STATUSES, "status")
        if not isinstance(self.unresolved, (list, tuple)):
            _fail("unresolved: expected a list")
        unresolved = tuple(_json_value(row, f"unresolved[{index}]")
                           for index, row in enumerate(self.unresolved))
        if self.status in {"TIMED_OUT", "INCOMPLETE", "HANDOFF_REQUIRED"} \
                and not unresolved:
            _fail(f"{self.status} requires explicit unresolved work")
        if self.status == "PASS" and unresolved:
            _fail("PASS cannot carry unresolved work")
        object.__setattr__(self, "unresolved", unresolved)
        object.__setattr__(self, "output", _json_value(self.output, "output"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TaskAttempt":
        fields = {"schema", "task_id", "envelope_sha256", "attempt_index",
                  "replacement_index", "subject", "started_at", "finished_at",
                  "elapsed_s", "status", "unresolved", "output"}
        _exact_fields(value, fields, "TaskAttempt")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "TaskAttempt":
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError) as exc:
            _fail(f"TaskAttempt JSON: {exc}")
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        return {"schema": self.schema, "task_id": self.task_id,
                "envelope_sha256": self.envelope_sha256,
                "attempt_index": self.attempt_index,
                "replacement_index": self.replacement_index,
                "subject": self.subject.to_mapping(),
                "started_at": self.started_at, "finished_at": self.finished_at,
                "elapsed_s": self.elapsed_s, "status": self.status,
                "unresolved": list(self.unresolved), "output": self.output}

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True,
                          separators=(",", ":"), ensure_ascii=False)


def context_handoff_decision(*, context_used_pct: Optional[float],
                             boundary: Optional[str] = None,
                             d_back: bool = False) -> dict[str, Any]:
    """Return a deterministic advisory/hard handoff decision.

    Semantic boundaries and D-BACK are enforceable even when the host exposes
    no comparable live context counter.  Percentage thresholds apply only to
    a finite 0..100 observation supplied by the host.
    """
    if boundary is not None and boundary not in MANDATORY_FRESH_BOUNDARIES:
        _fail(f"boundary: unknown semantic boundary {boundary!r}")
    if context_used_pct is not None:
        if (not isinstance(context_used_pct, (int, float)) or
                isinstance(context_used_pct, bool) or
                not math.isfinite(context_used_pct) or
                not 0 <= context_used_pct <= 100):
            _fail("context_used_pct: expected null or finite 0..100")
        context_used_pct = float(context_used_pct)
    if d_back:
        return {"decision": "HANDOFF_REQUIRED", "reason": "D-BACK requires a fresh successor"}
    if boundary is not None:
        return {"decision": "HANDOFF_REQUIRED",
                "reason": f"semantic boundary {boundary} requires a fresh successor"}
    if context_used_pct is not None and context_used_pct >= 70:
        return {"decision": "HANDOFF_REQUIRED",
                "reason": f"context use {context_used_pct:g}% reached hard threshold 70%"}
    if context_used_pct is not None and context_used_pct >= 60:
        return {"decision": "WARN",
                "reason": f"context use {context_used_pct:g}% reached planning threshold 60%"}
    return {"decision": "CONTINUE",
            "reason": ("live context telemetry unavailable"
                       if context_used_pct is None else "below handoff threshold")}


def aggregate_token_usage(spans: Sequence[AgentSpan]) -> dict[str, Any]:
    """Aggregate comparable token telemetry or explicitly return UNKNOWN."""
    if not spans:
        return {"status": "UNKNOWN", "reason": "no agent spans"}
    usages = [span.token_usage for span in spans]
    if any(usage is None for usage in usages):
        return {"status": "UNKNOWN", "reason": "one or more spans lack token telemetry"}
    authorities = {usage.authority for usage in usages if usage is not None}
    metrics = {usage.metric for usage in usages if usage is not None}
    if len(authorities) != 1 or len(metrics) != 1:
        return {"status": "UNKNOWN",
                "reason": "token authorities or metrics are not comparable"}
    return {
        "status": "MEASURED", "authority": next(iter(authorities)),
        "metric": next(iter(metrics)),
        "input": sum(usage.input for usage in usages if usage is not None),
        "cached_input": sum(usage.cached_input for usage in usages if usage is not None),
        "output": sum(usage.output for usage in usages if usage is not None),
        "total": sum(usage.total for usage in usages if usage is not None),
    }


def replacement_admissible(envelope: TaskEnvelope,
                           prior_attempts: Sequence[TaskAttempt]) -> bool:
    """Return whether one more replacement stays within the envelope ceiling."""
    digest = envelope_sha256(envelope)
    subject = envelope.subject.to_mapping()
    matching = [attempt for attempt in prior_attempts
                if (attempt.task_id == envelope.task_id and
                    attempt.envelope_sha256 == digest and
                    attempt.subject.to_mapping() == subject)]
    used = max((attempt.replacement_index for attempt in matching), default=-1)
    return used < envelope.replacement_limit


def envelope_sha256(envelope: TaskEnvelope) -> str:
    """Return the canonical digest attempts must use as their authority."""
    return hashlib.sha256(envelope.to_json().encode("utf-8")).hexdigest()


def verify_input_packet(envelope: TaskEnvelope,
                        project_root: str | Path) -> tuple[bool, list[str]]:
    """Reopen every declared packet item under one explicit project root."""
    root = Path(project_root).resolve()
    failures = []
    for item in envelope.input_packet:
        path = (root / item.path).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            failures.append(f"packet path escapes project root: {item.name}")
            continue
        if not path.is_file():
            failures.append(f"packet item missing: {item.name}")
            continue
        data = path.read_bytes()
        if len(data) != item.size:
            failures.append(f"packet size changed: {item.name}")
        if hashlib.sha256(data).hexdigest() != item.sha256:
            failures.append(f"packet hash changed: {item.name}")
    return not failures, failures


__all__ = [
    "AGENT_ROLES", "AgentSpan", "ATTEMPT_STATUSES", "CONTEXT_MODES",
    "EXECUTION_CLASSES", "EXECUTORS", "ExecutionValidationError",
    "MANDATORY_FRESH_BOUNDARIES", "PacketItem", "SCHEMA", "TaskAttempt",
    "TaskEnvelope", "TokenUsage", "WriterScope", "aggregate_token_usage",
    "context_handoff_decision", "envelope_sha256", "replacement_admissible",
    "verify_input_packet",
]
