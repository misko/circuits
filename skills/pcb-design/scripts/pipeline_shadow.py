#!/usr/bin/env python3
"""Non-authoritative observations of an already-executed legacy pipeline.

This module never launches, retries, promotes, or deletes anything.  A legacy
caller keeps authority over command execution and verdicts, then supplies the
result here for strict projection into :class:`StageResult` and
:class:`StageSpan`.  Shadow failures are exceptions for the integration layer
to report; no API here returns or rewrites the legacy authority return code.
"""
from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional, Sequence

from pipeline_contract import StageResult, StageSpec
from pipeline_identity import SubjectIdentity
from pipeline_registry import StageRegistry
from pipeline_timing import StageSpan


SCHEMA = 1
TERMINATIONS = frozenset({"COMPLETED", "FAILED", "ABORTED", "PAUSED"})
STAGE_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SEGMENT_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


class ShadowValidationError(ValueError):
    """A shadow declaration or observation is malformed or inconsistent."""


def _fail(message: str) -> None:
    raise ShadowValidationError(message)


def _subject(value: SubjectIdentity | Mapping[str, Any]) -> SubjectIdentity:
    if isinstance(value, SubjectIdentity):
        return value
    if isinstance(value, Mapping):
        try:
            return SubjectIdentity.from_mapping(value)
        except ValueError as exc:
            _fail(f"subject: {exc}")
    _fail("subject: expected SubjectIdentity or its exact mapping")


def _stage_ids(value: Sequence[str], where: str, *, allow_empty: bool) -> tuple[str, ...]:
    if (not isinstance(value, (list, tuple)) or
            isinstance(value, (str, bytes, bytearray))):
        _fail(f"{where}: expected a sorted stage-id list")
    result = tuple(value)
    if not allow_empty and not result:
        _fail(f"{where}: expected at least one stage id")
    for item in result:
        if not isinstance(item, str) or STAGE_ID_RE.fullmatch(item) is None:
            _fail(f"{where}: invalid stage id {item!r}")
    if list(result) != sorted(set(result)):
        _fail(f"{where}: stage ids must be sorted and unique")
    return result


def _symbols(value: Sequence[str], where: str) -> tuple[str, ...]:
    if (not isinstance(value, (list, tuple)) or
            isinstance(value, (str, bytes, bytearray))):
        _fail(f"{where}: expected a sorted symbolic-name list")
    result = tuple(value)
    for item in result:
        if not isinstance(item, str) or SYMBOL_RE.fullmatch(item) is None:
            _fail(f"{where}: invalid symbolic name {item!r}")
    if list(result) != sorted(set(result)):
        _fail(f"{where}: symbols must be sorted and unique")
    return result


def _argv(value: Sequence[str], where: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if (not isinstance(value, (list, tuple)) or
            isinstance(value, (str, bytes, bytearray))):
        _fail(f"{where}: expected an argv list")
    result = tuple(value)
    if not allow_empty and not result:
        _fail(f"{where}: argv must not be empty")
    for index, item in enumerate(result):
        if not isinstance(item, str):
            _fail(f"{where}[{index}]: expected a string")
        if "\0" in item:
            _fail(f"{where}[{index}]: NUL bytes are not valid argv data")
    if result and not result[0]:
        _fail(f"{where}[0]: executable name must not be empty")
    return result


def _duration(value: Any, where: str) -> float:
    if (not isinstance(value, (int, float)) or isinstance(value, bool) or
            not math.isfinite(value) or value < 0):
        _fail(f"{where}: expected a non-negative finite number")
    return float(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z")


def _canonical_utc(value: Any, where: str) -> str:
    if not isinstance(value, str):
        _fail(f"{where}: expected a canonical RFC3339 UTC timestamp")
    # Let StageSpan be the single strict timestamp parser without manufacturing
    # a partially-valid span.  This local check mirrors its public vocabulary.
    if re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:"
            r"[0-9]{2}(?:\.[0-9]+)?Z", value) is None:
        _fail(f"{where}: expected a canonical RFC3339 UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _fail(f"{where}: invalid RFC3339 UTC timestamp {value!r}")
    return value


@dataclass(frozen=True)
class ShadowRunContext:
    """Immutable identity and declared scope of one legacy invocation."""

    run_id: str
    subject: SubjectIdentity | Mapping[str, Any]
    target_stage_ids: Sequence[str] = field(default_factory=tuple)
    available_facts: Sequence[str] = field(default_factory=tuple)
    segment: str = "full"
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        if not isinstance(self.run_id, str) or RUN_ID_RE.fullmatch(self.run_id) is None:
            _fail(f"run_id: expected {RUN_ID_RE.pattern}, got {self.run_id!r}")
        object.__setattr__(self, "subject", _subject(self.subject))
        object.__setattr__(self, "target_stage_ids", _stage_ids(
            self.target_stage_ids, "target_stage_ids", allow_empty=True))
        object.__setattr__(self, "available_facts", _symbols(
            self.available_facts, "available_facts"))
        if not isinstance(self.segment, str) or SEGMENT_RE.fullmatch(self.segment) is None:
            _fail(f"segment: expected {SEGMENT_RE.pattern}, got {self.segment!r}")


@dataclass(frozen=True)
class LegacyCompletion:
    """Execution facts returned by the existing, still-authoritative runner."""

    legacy_label: str
    argv: Sequence[str]
    child_returncode: Optional[int]
    authority_returncode: int
    timed_out: bool
    cancelled: bool
    subprocess_elapsed_s: float
    accepted_outputs: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if (not isinstance(self.legacy_label, str) or
                not self.legacy_label.strip() or "\0" in self.legacy_label):
            _fail("legacy_label: expected non-empty text without NUL bytes")
        object.__setattr__(self, "argv", _argv(self.argv, "argv"))
        for name in ("child_returncode", "authority_returncode"):
            value = getattr(self, name)
            if value is None and name == "child_returncode":
                continue
            if not isinstance(value, int) or isinstance(value, bool):
                _fail(f"{name}: expected an integer" +
                      (" or null" if name == "child_returncode" else ""))
        if not isinstance(self.timed_out, bool) or not isinstance(self.cancelled, bool):
            _fail("timed_out and cancelled must be booleans")
        if self.timed_out and self.cancelled:
            _fail("completion cannot be both timed out and cancelled")
        object.__setattr__(self, "subprocess_elapsed_s", _duration(
            self.subprocess_elapsed_s, "subprocess_elapsed_s"))
        object.__setattr__(self, "accepted_outputs", _symbols(
            self.accepted_outputs, "accepted_outputs"))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "legacy_label": self.legacy_label,
            "argv": list(self.argv),
            "child_returncode": self.child_returncode,
            "authority_returncode": self.authority_returncode,
            "timed_out": self.timed_out,
            "cancelled": self.cancelled,
            "subprocess_elapsed_s": self.subprocess_elapsed_s,
            "accepted_outputs": list(self.accepted_outputs),
        }


@dataclass(frozen=True)
class LegacyVerdict:
    """The verdict already made by the legacy gate owner, never by this module."""

    applicability: str
    applicability_reason: Optional[str]
    status: str
    graded: int
    total: int
    findings: Sequence[Any] = field(default_factory=tuple)
    resume_argv: Optional[Sequence[str]] = None

    def __post_init__(self) -> None:
        if self.resume_argv is not None:
            object.__setattr__(self, "resume_argv", _argv(
                self.resume_argv, "resume_argv"))
        if not isinstance(self.findings, (list, tuple)):
            _fail("findings: expected a list")
        object.__setattr__(self, "findings", tuple(self.findings))


@dataclass(frozen=True)
class ObservationToken:
    """Start witness held across exactly one externally-owned execution."""

    context: ShadowRunContext
    spec: StageSpec
    dependencies: Sequence[str]
    started_at: str
    started_monotonic: float

    def __post_init__(self) -> None:
        if not isinstance(self.context, ShadowRunContext):
            _fail("context: expected ShadowRunContext")
        if not isinstance(self.spec, StageSpec):
            _fail("spec: expected StageSpec")
        object.__setattr__(self, "dependencies", _stage_ids(
            self.dependencies, "dependencies", allow_empty=True))
        if self.spec.id in self.dependencies:
            _fail("dependencies: a stage cannot depend on itself")
        object.__setattr__(self, "started_at", _canonical_utc(
            self.started_at, "started_at"))
        if (not isinstance(self.started_monotonic, (int, float)) or
                isinstance(self.started_monotonic, bool) or
                not math.isfinite(self.started_monotonic)):
            _fail("started_monotonic: expected a finite number")
        object.__setattr__(self, "started_monotonic", float(self.started_monotonic))


@dataclass(frozen=True)
class ShadowObservation:
    """One strict result/span pair plus the legacy facts from the same execution."""

    result: StageResult
    span: StageSpan
    legacy: LegacyCompletion

    def __post_init__(self) -> None:
        if not isinstance(self.result, StageResult):
            _fail("result: expected StageResult")
        if not isinstance(self.span, StageSpan):
            _fail("span: expected StageSpan")
        if not isinstance(self.legacy, LegacyCompletion):
            _fail("legacy: expected LegacyCompletion")
        pairs = (
            ("stage_id", self.result.stage_id, self.span.stage_id),
            ("run_id", self.result.run_id, self.span.run_id),
            ("subject", self.result.subject, self.span.subject),
            ("status", self.result.status, self.span.status),
            ("started_at", self.result.started_at, self.span.started_at),
            ("finished_at", self.result.finished_at, self.span.finished_at),
            ("elapsed_s", self.result.elapsed_s, self.span.elapsed_s),
        )
        for name, left, right in pairs:
            if left != right:
                _fail(f"observation {name} differs between result and span")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "result": self.result.to_mapping(),
            "span": self.span.to_mapping(),
            "legacy": self.legacy.to_mapping(),
        }


class ShadowObserver:
    """Project already-completed work while leaving legacy authority untouched."""

    def __init__(
            self, sink: Callable[[Mapping[str, Any]], None], *,
            utc_clock: Callable[[], str] = _utc_now,
            monotonic_clock: Callable[[], float] = time.monotonic) -> None:
        if not callable(sink) or not callable(utc_clock) or not callable(monotonic_clock):
            _fail("sink and clocks must be callable")
        self._sink = sink
        self._utc_clock = utc_clock
        self._monotonic_clock = monotonic_clock

    def _emit(self, value: Mapping[str, Any], event: str) -> None:
        try:
            self._sink(value)
        except Exception as exc:
            raise ShadowValidationError(
                f"shadow sink rejected {event} event: {type(exc).__name__}: {exc}") from exc

    def begin(
            self, context: ShadowRunContext, spec: StageSpec, *,
            dependencies: Sequence[str] = ()) -> ObservationToken:
        started_at = _canonical_utc(self._utc_clock(), "started_at")
        started_monotonic = self._monotonic_clock()
        token = ObservationToken(
            context=context, spec=spec, dependencies=dependencies,
            started_at=started_at, started_monotonic=started_monotonic)
        self._emit({
            "schema": SCHEMA,
            "event": "STARTED",
            "status": "INCOMPLETE",
            "stage_id": spec.id,
            "run_id": context.run_id,
            "subject": context.subject.to_mapping(),
            "work_class": spec.work_class,
            "started_at": started_at,
            "dependencies": list(token.dependencies),
        }, "STARTED")
        return token

    def finish(
            self, token: ObservationToken, *,
            subject_after: SubjectIdentity | Mapping[str, Any],
            completion: LegacyCompletion, verdict: LegacyVerdict,
            cache_status: str = "MISS") -> ShadowObservation:
        if not isinstance(token, ObservationToken):
            _fail("token: expected ObservationToken")
        if not isinstance(completion, LegacyCompletion):
            _fail("completion: expected LegacyCompletion")
        if not isinstance(verdict, LegacyVerdict):
            _fail("verdict: expected LegacyVerdict")
        after = _subject(subject_after)
        if after != token.context.subject:
            _fail("subject drifted while the legacy stage executed")
        declared = set(token.spec.produces)
        overclaim = sorted(set(completion.accepted_outputs) - declared)
        if overclaim:
            _fail("legacy completion overclaims undeclared output(s): " +
                  ", ".join(overclaim))
        if verdict.status != "PASS" and completion.accepted_outputs:
            _fail("non-PASS legacy verdict cannot publish accepted outputs")
        if verdict.status == "PASS" and (completion.timed_out or completion.cancelled):
            _fail("timed-out or cancelled legacy execution cannot become PASS")
        if verdict.status == "PASS" and completion.authority_returncode != 0:
            _fail("nonzero legacy authority return code cannot become PASS")

        finished_at = _canonical_utc(self._utc_clock(), "finished_at")
        finished_monotonic = self._monotonic_clock()
        if (not isinstance(finished_monotonic, (int, float)) or
                isinstance(finished_monotonic, bool) or
                not math.isfinite(finished_monotonic)):
            _fail("finished_monotonic: expected a finite number")
        elapsed_s = float(finished_monotonic) - token.started_monotonic
        if elapsed_s < 0:
            _fail("monotonic clock moved backwards")
        if completion.subprocess_elapsed_s > elapsed_s:
            _fail("subprocess_elapsed_s cannot exceed observed stage elapsed_s")

        resume = (None if verdict.resume_argv is None
                  else list(verdict.resume_argv))
        result = StageResult(
            stage_id=token.spec.id,
            run_id=token.context.run_id,
            subject=token.context.subject,
            applicability=verdict.applicability,
            applicability_reason=verdict.applicability_reason,
            status=verdict.status,
            started_at=token.started_at,
            finished_at=finished_at,
            elapsed_s=elapsed_s,
            graded=verdict.graded,
            total=verdict.total,
            outputs=completion.accepted_outputs,
            findings=verdict.findings,
            resume=resume,
        )
        span = StageSpan(
            stage_id=token.spec.id,
            run_id=token.context.run_id,
            subject=token.context.subject,
            work_class=token.spec.work_class,
            started_at=token.started_at,
            finished_at=finished_at,
            elapsed_s=elapsed_s,
            subprocess_elapsed_s=completion.subprocess_elapsed_s,
            dependencies=token.dependencies,
            cache_status=cache_status,
            status=verdict.status,
            resume_argv=verdict.resume_argv,
        )
        observation = ShadowObservation(result, span, completion)
        self._emit({
            "schema": SCHEMA,
            "event": "FINISHED",
            "observation": observation.to_mapping(),
        }, "FINISHED")
        return observation

    def not_applicable(
            self, context: ShadowRunContext, spec: StageSpec, *, reason: str,
            dependencies: Sequence[str] = ()) -> ShadowObservation:
        """Record an explicit skip without launching or pretending work occurred."""
        at = _canonical_utc(self._utc_clock(), "observed_at")
        deps = _stage_ids(dependencies, "dependencies", allow_empty=True)
        completion = LegacyCompletion(
            legacy_label=spec.id, argv=("<not-applicable>",),
            child_returncode=None, authority_returncode=0,
            timed_out=False, cancelled=False, subprocess_elapsed_s=0,
            accepted_outputs=())
        result = StageResult(
            stage_id=spec.id, run_id=context.run_id, subject=context.subject,
            applicability="NOT_APPLICABLE", applicability_reason=reason,
            status="NOT_APPLICABLE", started_at=at, finished_at=at,
            elapsed_s=0, graded=0, total=0, outputs=(), findings=(), resume=None)
        span = StageSpan(
            stage_id=spec.id, run_id=context.run_id, subject=context.subject,
            work_class=spec.work_class, started_at=at, finished_at=at,
            elapsed_s=0, subprocess_elapsed_s=0, dependencies=deps,
            cache_status="MISS", status="NOT_APPLICABLE", resume_argv=None)
        observation = ShadowObservation(result, span, completion)
        self._emit({
            "schema": SCHEMA, "event": "FINISHED",
            "observation": observation.to_mapping(),
        }, "FINISHED")
        return observation


@dataclass(frozen=True)
class ShadowRunComparison:
    termination: str
    expected: tuple[str, ...]
    observed: tuple[str, ...]
    first_divergence: Optional[int]
    not_reached: tuple[str, ...]
    mismatches: tuple[str, ...]

    @property
    def agrees(self) -> bool:
        return not self.mismatches

    def to_mapping(self) -> dict[str, Any]:
        return {
            "agrees": self.agrees,
            "termination": self.termination,
            "expected": list(self.expected),
            "observed": list(self.observed),
            "first_divergence": self.first_divergence,
            "not_reached": list(self.not_reached),
            "mismatches": list(self.mismatches),
        }


def compare_observed_run(
        registry: StageRegistry, context: ShadowRunContext,
        observations: Sequence[ShadowObservation], *,
        termination: str) -> ShadowRunComparison:
    """Compare a complete or explicitly partial legacy trace with its plan."""
    if not isinstance(registry, StageRegistry):
        _fail("registry: expected StageRegistry")
    if not isinstance(context, ShadowRunContext):
        _fail("context: expected ShadowRunContext")
    if termination not in TERMINATIONS:
        _fail(f"termination: expected one of {sorted(TERMINATIONS)}")
    if (not isinstance(observations, (list, tuple)) or
            isinstance(observations, (str, bytes, bytearray)) or
            any(not isinstance(item, ShadowObservation) for item in observations)):
        _fail("observations: expected a list of ShadowObservation values")

    targets = None if not context.target_stage_ids else context.target_stage_ids
    plan = registry.resolve(targets, available=context.available_facts)
    expected = tuple(spec.id for spec in plan)
    observed = tuple(item.result.stage_id for item in observations)
    mismatches: list[str] = []

    if len(observed) != len(set(observed)):
        mismatches.append("observed stage ids are not unique")
    limit = min(len(expected), len(observed))
    first_divergence = next(
        (index for index in range(limit)
         if expected[index] != observed[index]), None)
    prefix = first_divergence is None and observed == expected[:len(observed)]
    if not prefix:
        if first_divergence is None:
            first_divergence = limit
        mismatches.append("observed order is not an exact declared-plan prefix")

    if termination == "COMPLETED":
        if observed != expected:
            mismatches.append("COMPLETED trace is not the exact declared plan")
    else:
        if not observations:
            mismatches.append(f"{termination} trace has no terminal observation")
        elif observations[-1].result.status in {"PASS", "NOT_APPLICABLE"}:
            mismatches.append(
                f"{termination} trace must end in an explicit non-PASS status")
        if termination == "PAUSED" and observations:
            last = observations[-1]
            if last.result.status != "INCOMPLETE" or last.span.resume_argv is None:
                mismatches.append(
                    "PAUSED trace must end INCOMPLETE with explicit resume argv")

    if termination == "COMPLETED":
        for item in observations:
            if item.result.status not in {"PASS", "NOT_APPLICABLE"}:
                mismatches.append(
                    f"COMPLETED stage {item.result.stage_id} has "
                    f"non-admissible status {item.result.status}")

    by_id = {spec.id: spec for spec in plan}
    producer = {
        symbol: spec.id for spec in registry.stages for symbol in spec.produces
    }
    selected = set(expected)
    available = set(context.available_facts)
    for item in observations:
        result, span = item.result, item.span
        stage_id = result.stage_id
        if result.run_id != context.run_id or span.run_id != context.run_id:
            mismatches.append(f"stage {stage_id}: run_id differs from context")
        if result.subject != context.subject or span.subject != context.subject:
            mismatches.append(f"stage {stage_id}: subject differs from context")
        spec = by_id.get(stage_id)
        if spec is None:
            mismatches.append(f"stage {stage_id}: not present in resolved plan")
            continue
        required_dependencies = tuple(sorted({
            producer[symbol] for symbol in spec.requires
            if symbol not in available and producer.get(symbol) in selected
        }))
        if span.dependencies != required_dependencies:
            mismatches.append(
                f"stage {stage_id}: dependencies {span.dependencies!r} differ "
                f"from {required_dependencies!r}")
        required_outputs = spec.produces if result.status == "PASS" else ()
        if result.outputs != required_outputs:
            mismatches.append(
                f"stage {stage_id}: outputs {result.outputs!r} differ from "
                f"{required_outputs!r}")

    not_reached = expected[len(observed):] if prefix else ()
    return ShadowRunComparison(
        termination=termination,
        expected=expected,
        observed=observed,
        first_divergence=first_divergence,
        not_reached=not_reached,
        mismatches=tuple(mismatches),
    )


__all__ = [
    "LegacyCompletion", "LegacyVerdict", "ObservationToken", "SCHEMA",
    "ShadowObservation", "ShadowObserver", "ShadowRunComparison",
    "ShadowRunContext", "ShadowValidationError", "TERMINATIONS",
    "compare_observed_run",
]
