#!/usr/bin/env python3
"""Strict cross-stage timing aggregation for declarative PCB pipelines.

This module consumes already-recorded spans.  It never launches a command and
does not infer engineering dependencies.  UTC timestamps establish temporal
ordering and the observed run envelope; ``elapsed_s`` is a monotonic duration
recorded by the stage launcher.  Dependency critical-path calculations use
those monotonic durations and therefore exclude scheduler gaps between stages.

Deliberate limitations:

* undeclared dependencies and work performed outside a span are unknowable;
* summed stage/subprocess durations are work totals, never wall-clock time;
* overlapping independent spans are valid and no CPU-utilization inference is
  attempted; and
* ``resume_argv`` is durable data only.  This module never executes it.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from heapq import heappop, heappush
from typing import Any, Mapping, Optional, Sequence

from pipeline_identity import SubjectIdentity


SCHEMA = 1
STAGE_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z$")
WORK_CLASSES = (
    "local", "network", "backoff", "review_wait", "operator_wait",
)
CACHE_STATUSES = ("HIT", "MISS")
RESULT_STATUSES = (
    "PASS", "FAIL", "NOT_APPLICABLE", "TIMED_OUT", "INCOMPLETE", "ERROR",
)


class TimingValidationError(ValueError):
    """A timing span or dependency graph is malformed or inconsistent."""


def _fail(message: str) -> None:
    raise TimingValidationError(message)


def _exact_fields(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    actual = set(value)
    missing = expected - actual
    unknown = actual - expected
    if missing or unknown:
        _fail(f"{where}: fields differ (missing={sorted(missing)}, "
              f"unknown={sorted(unknown)})")


def _enum(value: Any, allowed: Sequence[str], where: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{where}: expected one of {list(allowed)}, got {value!r}")
    return value


def _stage_id(value: Any, where: str = "stage_id") -> str:
    if not isinstance(value, str) or STAGE_ID_RE.fullmatch(value) is None:
        _fail(f"{where}: expected {STAGE_ID_RE.pattern}, got {value!r}")
    return value


def _run_id(value: Any) -> str:
    if not isinstance(value, str) or RUN_ID_RE.fullmatch(value) is None:
        _fail(f"run_id: expected {RUN_ID_RE.pattern}, got {value!r}")
    return value


def _duration(value: Any, where: str) -> float:
    if (not isinstance(value, (int, float)) or isinstance(value, bool) or
            not math.isfinite(value) or value < 0):
        _fail(f"{where}: expected a non-negative finite number")
    return float(value)


def _utc_timestamp(value: Any, where: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or UTC_TIMESTAMP_RE.fullmatch(value) is None:
        _fail(f"{where}: expected a canonical RFC3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _fail(f"{where}: invalid RFC3339 UTC timestamp {value!r}")
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(None):
        _fail(f"{where}: timestamp must be UTC")
    return value, parsed


def _dependencies(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        _fail("dependencies: expected a sorted list of stage ids")
    result = tuple(_stage_id(item, "dependency") for item in value)
    if list(result) != sorted(set(result)):
        _fail("dependencies: stage ids must be sorted and unique")
    return result


def _resume_argv(value: Any) -> Optional[tuple[str, ...]]:
    if value is None:
        return None
    if (not isinstance(value, (list, tuple)) or
            isinstance(value, (str, bytes, bytearray)) or not value):
        _fail("resume_argv: expected null or a non-empty argv list")
    result = tuple(value)
    for index, argument in enumerate(result):
        if not isinstance(argument, str):
            _fail(f"resume_argv[{index}]: expected a string")
        if "\0" in argument:
            _fail(f"resume_argv[{index}]: NUL bytes are not valid argv data")
    if not result[0]:
        _fail("resume_argv[0]: executable name must not be empty")
    return result


@dataclass(frozen=True)
class StageSpan:
    """One immutable schema-1 timing observation for an orchestration stage."""

    stage_id: str
    run_id: str
    subject: SubjectIdentity | Mapping[str, Any]
    work_class: str
    started_at: str
    finished_at: str
    elapsed_s: float
    subprocess_elapsed_s: float
    dependencies: Sequence[str] = field(default_factory=tuple)
    cache_status: str = "MISS"
    status: str = "PASS"
    resume_argv: Optional[Sequence[str]] = None
    schema: int = SCHEMA
    _started: datetime = field(init=False, repr=False, compare=False)
    _finished: datetime = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _stage_id(self.stage_id)
        _run_id(self.run_id)
        if isinstance(self.subject, Mapping):
            try:
                subject = SubjectIdentity.from_mapping(self.subject)
            except ValueError as exc:
                _fail(f"subject: {exc}")
            object.__setattr__(self, "subject", subject)
        elif not isinstance(self.subject, SubjectIdentity):
            _fail("subject: expected SubjectIdentity or its exact mapping")
        _enum(self.work_class, WORK_CLASSES, "work_class")
        _enum(self.cache_status, CACHE_STATUSES, "cache_status")
        _enum(self.status, RESULT_STATUSES, "status")

        started_text, started = _utc_timestamp(self.started_at, "started_at")
        finished_text, finished = _utc_timestamp(self.finished_at, "finished_at")
        if finished < started:
            _fail("finished_at: cannot precede started_at")
        object.__setattr__(self, "started_at", started_text)
        object.__setattr__(self, "finished_at", finished_text)
        object.__setattr__(self, "_started", started)
        object.__setattr__(self, "_finished", finished)

        elapsed = _duration(self.elapsed_s, "elapsed_s")
        subprocess_elapsed = _duration(
            self.subprocess_elapsed_s, "subprocess_elapsed_s")
        if subprocess_elapsed > elapsed:
            _fail("subprocess_elapsed_s: cannot exceed elapsed_s")
        object.__setattr__(self, "elapsed_s", elapsed)
        object.__setattr__(self, "subprocess_elapsed_s", subprocess_elapsed)
        object.__setattr__(self, "dependencies", _dependencies(self.dependencies))
        object.__setattr__(self, "resume_argv", _resume_argv(self.resume_argv))

        if self.stage_id in self.dependencies:
            _fail("dependencies: a stage cannot depend on itself")
        if self.status == "NOT_APPLICABLE":
            if elapsed != 0 or subprocess_elapsed != 0:
                _fail("NOT_APPLICABLE spans require zero elapsed durations")
            if self.resume_argv is not None:
                _fail("NOT_APPLICABLE spans cannot carry resume_argv")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StageSpan":
        fields = {
            "schema", "stage_id", "run_id", "subject", "work_class",
            "started_at", "finished_at", "elapsed_s",
            "subprocess_elapsed_s", "dependencies", "cache_status", "status",
            "resume_argv",
        }
        _exact_fields(value, fields, "StageSpan")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "StageSpan":
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError) as exc:
            _fail(f"StageSpan JSON: {exc}")
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "stage_id": self.stage_id,
            "run_id": self.run_id,
            "subject": self.subject.to_mapping(),
            "work_class": self.work_class,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_s": self.elapsed_s,
            "subprocess_elapsed_s": self.subprocess_elapsed_s,
            "dependencies": list(self.dependencies),
            "cache_status": self.cache_status,
            "status": self.status,
            "resume_argv": (None if self.resume_argv is None
                            else list(self.resume_argv)),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_mapping(), sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class TimingSummary:
    """Deterministic aggregate which keeps work totals distinct from wall span."""

    run_id: str
    subject: SubjectIdentity
    stage_count: int
    started_at: str
    finished_at: str
    wall_span_s: float
    summed_stage_elapsed_s: float
    aggregate_subprocess_elapsed_s: float
    critical_path_elapsed_s: float
    critical_path_stage_ids: tuple[str, ...]
    work_class_elapsed_s: Mapping[str, float]
    work_class_subprocess_s: Mapping[str, float]
    cache_counts: Mapping[str, int]
    status_counts: Mapping[str, int]
    schema: int = SCHEMA

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "subject": self.subject.to_mapping(),
            "stage_count": self.stage_count,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "wall_span_s": self.wall_span_s,
            "summed_stage_elapsed_s": self.summed_stage_elapsed_s,
            "aggregate_subprocess_elapsed_s": self.aggregate_subprocess_elapsed_s,
            "critical_path_elapsed_s": self.critical_path_elapsed_s,
            "critical_path_stage_ids": list(self.critical_path_stage_ids),
            "work_class_elapsed_s": dict(self.work_class_elapsed_s),
            "work_class_subprocess_s": dict(self.work_class_subprocess_s),
            "cache_counts": dict(self.cache_counts),
            "status_counts": dict(self.status_counts),
        }


def summarize_spans(spans: Sequence[StageSpan]) -> TimingSummary:
    """Validate and aggregate one run's complete declared timing graph.

    The critical path is the maximum sum of monotonic stage durations along a
    dependency path.  Calendar gaps between a dependency finishing and its
    consumer starting contribute to ``wall_span_s`` but never to that path.
    """
    if (not isinstance(spans, (list, tuple)) or
            isinstance(spans, (str, bytes, bytearray)) or not spans):
        _fail("spans: expected a non-empty list of StageSpan values")
    material = list(spans)
    if any(not isinstance(span, StageSpan) for span in material):
        _fail("spans: every item must be a StageSpan")

    by_id: dict[str, StageSpan] = {}
    for span in material:
        if span.stage_id in by_id:
            _fail(f"duplicate stage_id in timing run: {span.stage_id}")
        by_id[span.stage_id] = span

    run_id = material[0].run_id
    subject = material[0].subject
    for span in material:
        if span.run_id != run_id:
            _fail(f"stage {span.stage_id}: run_id does not match timing run")
        if span.subject != subject:
            _fail(f"stage {span.stage_id}: subject does not match timing run")
        missing = sorted(set(span.dependencies) - set(by_id))
        if missing:
            _fail(f"stage {span.stage_id}: missing dependencies {missing}")

    dependents: dict[str, list[str]] = {stage_id: [] for stage_id in by_id}
    indegree = {stage_id: 0 for stage_id in by_id}
    for span in material:
        for dependency in span.dependencies:
            dependents[dependency].append(span.stage_id)
            indegree[span.stage_id] += 1
    for stage_ids in dependents.values():
        stage_ids.sort()

    ready: list[str] = []
    for stage_id, degree in indegree.items():
        if degree == 0:
            heappush(ready, stage_id)
    topological: list[str] = []
    while ready:
        stage_id = heappop(ready)
        topological.append(stage_id)
        for dependent in dependents[stage_id]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heappush(ready, dependent)
    if len(topological) != len(material):
        cyclic = sorted(stage_id for stage_id, degree in indegree.items() if degree)
        _fail(f"dependency graph contains a cycle involving {cyclic}")

    # Diagnose graph structure before comparing observed calendar ordering. A
    # cycle is a semantic graph defect regardless of which of its edges also
    # happens to violate the wall-clock observations.
    for span in material:
        for dependency in span.dependencies:
            predecessor = by_id[dependency]
            if predecessor._finished > span._started:
                _fail(f"stage {span.stage_id}: dependency {dependency} had not "
                      "finished before the stage started")

    path_duration: dict[str, float] = {}
    path_ids: dict[str, tuple[str, ...]] = {}
    for stage_id in topological:
        span = by_id[stage_id]
        if not span.dependencies:
            path_duration[stage_id] = span.elapsed_s
            path_ids[stage_id] = (stage_id,)
            continue
        candidates = [
            (path_duration[dependency], path_ids[dependency])
            for dependency in span.dependencies
        ]
        best_duration = max(duration for duration, _ in candidates)
        best_prefix = min(path for duration, path in candidates
                          if duration == best_duration)
        path_duration[stage_id] = best_duration + span.elapsed_s
        path_ids[stage_id] = best_prefix + (stage_id,)

    terminal_ids = [stage_id for stage_id in by_id if not dependents[stage_id]]
    critical_duration = max(path_duration[stage_id] for stage_id in terminal_ids)
    critical_path = min(path_ids[stage_id] for stage_id in terminal_ids
                        if path_duration[stage_id] == critical_duration)

    earliest = min(material, key=lambda span: (span._started, span.stage_id))
    latest = max(material, key=lambda span: (span._finished, span.stage_id))
    wall_span = (latest._finished - earliest._started).total_seconds()
    work_elapsed = Counter({name: 0.0 for name in WORK_CLASSES})
    work_subprocess = Counter({name: 0.0 for name in WORK_CLASSES})
    cache_counts = Counter({name: 0 for name in CACHE_STATUSES})
    status_counts = Counter({name: 0 for name in RESULT_STATUSES})
    for span in material:
        work_elapsed[span.work_class] += span.elapsed_s
        work_subprocess[span.work_class] += span.subprocess_elapsed_s
        cache_counts[span.cache_status] += 1
        status_counts[span.status] += 1

    return TimingSummary(
        run_id=run_id,
        subject=subject,
        stage_count=len(material),
        started_at=earliest.started_at,
        finished_at=latest.finished_at,
        wall_span_s=wall_span,
        summed_stage_elapsed_s=sum(span.elapsed_s for span in material),
        aggregate_subprocess_elapsed_s=sum(
            span.subprocess_elapsed_s for span in material),
        critical_path_elapsed_s=critical_duration,
        critical_path_stage_ids=critical_path,
        work_class_elapsed_s={name: work_elapsed[name] for name in WORK_CLASSES},
        work_class_subprocess_s={
            name: work_subprocess[name] for name in WORK_CLASSES},
        cache_counts={name: cache_counts[name] for name in CACHE_STATUSES},
        status_counts={name: status_counts[name] for name in RESULT_STATUSES},
    )


__all__ = [
    "CACHE_STATUSES", "RESULT_STATUSES", "SCHEMA", "StageSpan",
    "TimingSummary", "TimingValidationError", "WORK_CLASSES",
    "summarize_spans",
]
