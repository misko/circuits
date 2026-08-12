#!/usr/bin/env python3
"""Typed early-warning and late-authority lifecycle fact contracts.

An early observation may prevent avoidable downstream work.  It is never
evidence for a final claim.  Only a passing late observation, made by the
declared authority against the current semantic subject, can authorize that
claim.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from pipeline_contract import LIFECYCLES, OWNERS
from pipeline_identity import SubjectIdentity


SCHEMA = 1
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PHASES = frozenset({"EARLY", "LATE"})
OBSERVATION_STATUSES = frozenset({
    "PASS", "FAIL", "TIMED_OUT", "INCOMPLETE", "ERROR",
})
ROLES = frozenset({"PREVENTION", "AUTHORITY"})
DISPOSITIONS = frozenset({"PROCEED", "BLOCK"})
REASONS = frozenset({
    "EARLY_PASS",
    "LATE_PASS",
    "MISSING_OBSERVATION",
    "FACT_MISMATCH",
    "PHASE_MISMATCH",
    "STAGE_MISMATCH",
    "AUTHORITY_MISMATCH",
    "SUBJECT_MISMATCH",
    "OBSERVATION_NOT_PASS",
    "FUTURE_OBSERVATION",
    "STALE_OBSERVATION",
    "OBSERVATION_INVALIDATOR_SET_MISMATCH",
    "UNKNOWN_INVALIDATOR",
    "MISSING_CURRENT_INVALIDATOR",
    "INVALIDATED",
})

_LIFECYCLE_ORDER = (
    "commission", "architecture", "sourcing", "schematic", "placement",
    "routing", "layout_seal", "fabrication", "release_staging",
    "release_seal", "publication", "first_article", "production",
)
_LIFECYCLE_INDEX = {name: index for index, name in enumerate(_LIFECYCLE_ORDER)}
if set(_LIFECYCLE_ORDER) != set(LIFECYCLES):
    raise RuntimeError(
        "pipeline_facts lifecycle order is out of sync with pipeline_contract")


class FactValidationError(ValueError):
    """A lifecycle fact declaration, observation, or input is malformed."""


def _fail(message: str) -> None:
    raise FactValidationError(message)


def _exact_fields(value: Mapping[str, Any], expected: set[str], where: str,
                  optional: set[str] | None = None) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    optional = optional or set()
    actual = set(value)
    missing = expected - actual - optional
    unknown = actual - expected
    if missing or unknown:
        _fail(f"{where}: fields differ (missing={sorted(missing)}, "
              f"unknown={sorted(unknown)})")


def _symbol(value: Any, where: str) -> str:
    if not isinstance(value, str) or SYMBOL_RE.fullmatch(value) is None:
        _fail(f"{where}: expected {SYMBOL_RE.pattern}, got {value!r}")
    return value


def _enum(value: Any, allowed: frozenset[str], where: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{where}: expected one of {sorted(allowed)}, got {value!r}")
    return value


def _lifecycle(value: Any, where: str) -> str:
    return _enum(value, LIFECYCLES, where)


def _timestamp(value: Any, where: str) -> tuple[str, datetime]:
    if not isinstance(value, str) or not value:
        _fail(f"{where}: expected a non-empty RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail(f"{where}: invalid RFC3339 timestamp {value!r}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"{where}: timestamp must include a UTC offset")
    return value, parsed


def _subject(value: SubjectIdentity | Mapping[str, Any], where: str) -> SubjectIdentity:
    if isinstance(value, SubjectIdentity):
        return value
    if isinstance(value, Mapping):
        try:
            return SubjectIdentity.from_mapping(value)
        except ValueError as exc:
            _fail(f"{where}: {exc}")
    _fail(f"{where}: expected SubjectIdentity or its exact mapping")


def _from_json(text: str, where: str) -> Mapping[str, Any]:
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        _fail(f"{where} JSON: {exc}")
    if not isinstance(value, Mapping):
        _fail(f"{where} JSON: expected an object")
    return value


def _to_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class EarlyBoundary:
    stage: str
    blocks: str

    def __post_init__(self) -> None:
        _lifecycle(self.stage, "early.stage")
        _lifecycle(self.blocks, "early.blocks")
        if _LIFECYCLE_INDEX[self.stage] > _LIFECYCLE_INDEX[self.blocks]:
            _fail("early: observation stage cannot follow its block boundary")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EarlyBoundary":
        _exact_fields(value, {"stage", "blocks"}, "early")
        return cls(stage=value["stage"], blocks=value["blocks"])

    def to_mapping(self) -> dict[str, str]:
        return {"stage": self.stage, "blocks": self.blocks}


@dataclass(frozen=True)
class LateBoundary:
    stage: str
    blocks: str
    authority: str

    def __post_init__(self) -> None:
        _lifecycle(self.stage, "late.stage")
        _lifecycle(self.blocks, "late.blocks")
        _symbol(self.authority, "late.authority")
        if _LIFECYCLE_INDEX[self.stage] > _LIFECYCLE_INDEX[self.blocks]:
            _fail("late: observation stage cannot follow its block boundary")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LateBoundary":
        _exact_fields(value, {"stage", "blocks", "authority"}, "late")
        return cls(stage=value["stage"], blocks=value["blocks"],
                   authority=value["authority"])

    def to_mapping(self) -> dict[str, str]:
        return {
            "stage": self.stage,
            "blocks": self.blocks,
            "authority": self.authority,
        }


@dataclass(frozen=True)
class FactPair:
    fact: str
    owner: str
    early: EarlyBoundary | Mapping[str, Any]
    late: LateBoundary | Mapping[str, Any]
    invalidated_by: Sequence[str] = field(default_factory=tuple)
    maximum_age_s: Optional[float] = None
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _symbol(self.fact, "fact")
        _enum(self.owner, OWNERS, "owner")
        if isinstance(self.early, Mapping):
            object.__setattr__(self, "early", EarlyBoundary.from_mapping(self.early))
        elif not isinstance(self.early, EarlyBoundary):
            _fail("early: expected EarlyBoundary or its exact mapping")
        if isinstance(self.late, Mapping):
            object.__setattr__(self, "late", LateBoundary.from_mapping(self.late))
        elif not isinstance(self.late, LateBoundary):
            _fail("late: expected LateBoundary or its exact mapping")

        invalidators = tuple(self.invalidated_by)
        for index, name in enumerate(invalidators):
            _symbol(name, f"invalidated_by[{index}]")
        if list(invalidators) != sorted(set(invalidators)):
            _fail("invalidated_by: names must be sorted and unique")
        object.__setattr__(self, "invalidated_by", invalidators)

        if self.maximum_age_s is not None and (
                not isinstance(self.maximum_age_s, (int, float)) or
                isinstance(self.maximum_age_s, bool) or
                not math.isfinite(self.maximum_age_s) or
                self.maximum_age_s <= 0):
            _fail("maximum_age_s: expected a positive finite number or null")

        early_stage = _LIFECYCLE_INDEX[self.early.stage]
        early_block = _LIFECYCLE_INDEX[self.early.blocks]
        late_stage = _LIFECYCLE_INDEX[self.late.stage]
        late_block = _LIFECYCLE_INDEX[self.late.blocks]
        if not (early_stage < late_stage and early_block <= late_stage <= late_block):
            _fail("fact pair: lifecycle boundaries must progress from the early "
                  "observation and consumer to the late authoritative recheck")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FactPair":
        fields = {
            "schema", "fact", "owner", "early", "late", "maximum_age_s",
            "invalidated_by",
        }
        _exact_fields(value, fields, "FactPair", optional={"maximum_age_s"})
        return cls(
            schema=value["schema"], fact=value["fact"], owner=value["owner"],
            early=value["early"], late=value["late"],
            maximum_age_s=value.get("maximum_age_s"),
            invalidated_by=value["invalidated_by"],
        )

    @classmethod
    def from_json(cls, text: str) -> "FactPair":
        return cls.from_mapping(_from_json(text, "FactPair"))

    def to_mapping(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "schema": self.schema,
            "fact": self.fact,
            "owner": self.owner,
            "early": self.early.to_mapping(),
            "late": self.late.to_mapping(),
            "invalidated_by": list(self.invalidated_by),
        }
        if self.maximum_age_s is not None:
            value["maximum_age_s"] = self.maximum_age_s
        return value

    def to_json(self) -> str:
        return _to_json(self.to_mapping())


@dataclass(frozen=True)
class InvalidatorState:
    name: str
    subject: SubjectIdentity | Mapping[str, Any]

    def __post_init__(self) -> None:
        _symbol(self.name, "invalidator.name")
        object.__setattr__(self, "subject", _subject(
            self.subject, f"invalidator[{self.name}].subject"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "InvalidatorState":
        _exact_fields(value, {"name", "subject"}, "InvalidatorState")
        return cls(name=value["name"], subject=value["subject"])

    def to_mapping(self) -> dict[str, Any]:
        return {"name": self.name, "subject": self.subject.to_mapping()}


def _invalidators(value: Sequence[InvalidatorState | Mapping[str, Any]],
                  where: str) -> tuple[InvalidatorState, ...]:
    if (not isinstance(value, (list, tuple)) or
            isinstance(value, (str, bytes, bytearray))):
        _fail(f"{where}: expected a sorted list")
    result = tuple(
        item if isinstance(item, InvalidatorState)
        else InvalidatorState.from_mapping(item)
        for item in value
    )
    names = [item.name for item in result]
    if names != sorted(set(names)):
        _fail(f"{where}: names must be sorted and unique")
    return result


@dataclass(frozen=True)
class FactObservation:
    fact: str
    phase: str
    stage: str
    subject: SubjectIdentity | Mapping[str, Any]
    authority: Optional[str]
    status: str
    started_at: str
    observed_at: str
    graded: int
    total: int
    invalidators: Sequence[InvalidatorState | Mapping[str, Any]] = field(
        default_factory=tuple)
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _symbol(self.fact, "fact")
        _enum(self.phase, PHASES, "phase")
        _lifecycle(self.stage, "stage")
        object.__setattr__(self, "subject", _subject(self.subject, "subject"))
        if self.phase == "EARLY":
            if self.authority is not None:
                _fail("authority: EARLY observations require null")
        else:
            _symbol(self.authority, "authority")
        _enum(self.status, OBSERVATION_STATUSES, "status")

        started_text, started = _timestamp(self.started_at, "started_at")
        observed_text, observed = _timestamp(self.observed_at, "observed_at")
        object.__setattr__(self, "started_at", started_text)
        object.__setattr__(self, "observed_at", observed_text)
        if observed < started:
            _fail("observed_at: cannot precede started_at")

        for name in ("graded", "total"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                _fail(f"{name}: expected a non-negative integer")
        if self.graded > self.total:
            _fail("graded: cannot exceed total")
        if self.status == "PASS" and not (
                self.total > 0 and self.graded == self.total):
            _fail("PASS requires graded == total > 0")

        normalized = _invalidators(self.invalidators, "invalidators")
        if self.phase == "LATE" and normalized:
            _fail("invalidators: LATE observations are current authority and "
                  "must not claim reuse of early invalidator evidence")
        object.__setattr__(self, "invalidators", normalized)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FactObservation":
        fields = {
            "schema", "fact", "phase", "stage", "subject", "authority",
            "status", "started_at", "observed_at", "graded", "total",
            "invalidators",
        }
        _exact_fields(value, fields, "FactObservation")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "FactObservation":
        return cls.from_mapping(_from_json(text, "FactObservation"))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "fact": self.fact,
            "phase": self.phase,
            "stage": self.stage,
            "subject": self.subject.to_mapping(),
            "authority": self.authority,
            "status": self.status,
            "started_at": self.started_at,
            "observed_at": self.observed_at,
            "graded": self.graded,
            "total": self.total,
            "invalidators": [item.to_mapping() for item in self.invalidators],
        }

    def to_json(self) -> str:
        return _to_json(self.to_mapping())


@dataclass(frozen=True)
class FactEvaluation:
    fact: str
    owner: str
    phase: str
    role: str
    blocks: str
    disposition: str
    reason: str
    authorizes_final: bool
    causal_fact: Optional[str] = None
    causal_owner: Optional[str] = None
    causal_stage: Optional[str] = None
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _symbol(self.fact, "fact")
        _enum(self.owner, OWNERS, "owner")
        _enum(self.phase, PHASES, "phase")
        _enum(self.role, ROLES, "role")
        _lifecycle(self.blocks, "blocks")
        _enum(self.disposition, DISPOSITIONS, "disposition")
        _enum(self.reason, REASONS, "reason")
        if not isinstance(self.authorizes_final, bool):
            _fail("authorizes_final: expected boolean")
        if self.phase == "EARLY" and (
                self.role != "PREVENTION" or self.authorizes_final):
            _fail("EARLY evaluation is prevention only and cannot authorize")
        if self.phase == "LATE" and self.role != "AUTHORITY":
            _fail("LATE evaluation must carry the AUTHORITY role")
        if self.authorizes_final and not (
                self.phase == "LATE" and self.disposition == "PROCEED" and
                self.reason == "LATE_PASS"):
            _fail("final authorization requires a passing late evaluation")

        causal = (self.causal_fact, self.causal_owner, self.causal_stage)
        if self.phase == "LATE" and self.disposition == "BLOCK":
            if any(value is None for value in causal):
                _fail("blocked LATE evaluation requires early causal attribution")
            _symbol(self.causal_fact, "causal_fact")
            _enum(self.causal_owner, OWNERS, "causal_owner")
            _lifecycle(self.causal_stage, "causal_stage")
        elif any(value is not None for value in causal):
            _fail("causal attribution is only valid on blocked LATE evaluation")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "fact": self.fact,
            "owner": self.owner,
            "phase": self.phase,
            "role": self.role,
            "blocks": self.blocks,
            "disposition": self.disposition,
            "reason": self.reason,
            "authorizes_final": self.authorizes_final,
            "causal_fact": self.causal_fact,
            "causal_owner": self.causal_owner,
            "causal_stage": self.causal_stage,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FactEvaluation":
        fields = {
            "schema", "fact", "owner", "phase", "role", "blocks",
            "disposition", "reason", "authorizes_final", "causal_fact",
            "causal_owner", "causal_stage",
        }
        _exact_fields(value, fields, "FactEvaluation")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "FactEvaluation":
        return cls.from_mapping(_from_json(text, "FactEvaluation"))

    def to_json(self) -> str:
        return _to_json(self.to_mapping())


def _evaluation(pair: FactPair, phase: str, disposition: str,
                reason: str) -> FactEvaluation:
    late_block = phase == "LATE" and disposition == "BLOCK"
    return FactEvaluation(
        fact=pair.fact,
        owner=pair.owner,
        phase=phase,
        role="PREVENTION" if phase == "EARLY" else "AUTHORITY",
        blocks=pair.early.blocks if phase == "EARLY" else pair.late.blocks,
        disposition=disposition,
        reason=reason,
        authorizes_final=(phase == "LATE" and disposition == "PROCEED" and
                          reason == "LATE_PASS"),
        causal_fact=pair.fact if late_block else None,
        causal_owner=pair.owner if late_block else None,
        causal_stage=pair.early.stage if late_block else None,
    )


def _coerce_pair(value: FactPair | Mapping[str, Any]) -> FactPair:
    return value if isinstance(value, FactPair) else FactPair.from_mapping(value)


def _coerce_observation(
        value: FactObservation | Mapping[str, Any] | None,
) -> FactObservation | None:
    if value is None or isinstance(value, FactObservation):
        return value
    return FactObservation.from_mapping(value)


def evaluate_early(
        pair: FactPair | Mapping[str, Any],
        observation: FactObservation | Mapping[str, Any] | None,
        *,
        current_subject: SubjectIdentity | Mapping[str, Any],
        now: str,
        current_invalidators: Sequence[
            InvalidatorState | Mapping[str, Any]
        ] = (),
) -> FactEvaluation:
    """Decide whether an early consumer may proceed, never a final claim."""
    declaration = _coerce_pair(pair)
    current = _subject(current_subject, "current_subject")
    _, current_time = _timestamp(now, "now")
    current_states = _invalidators(current_invalidators, "current_invalidators")
    declared_names = set(declaration.invalidated_by)
    current_names = {item.name for item in current_states}
    if current_names - declared_names:
        return _evaluation(declaration, "EARLY", "BLOCK", "UNKNOWN_INVALIDATOR")
    if declared_names - current_names:
        return _evaluation(
            declaration, "EARLY", "BLOCK", "MISSING_CURRENT_INVALIDATOR")

    observed = _coerce_observation(observation)
    if observed is None:
        return _evaluation(declaration, "EARLY", "BLOCK", "MISSING_OBSERVATION")
    if observed.fact != declaration.fact:
        return _evaluation(declaration, "EARLY", "BLOCK", "FACT_MISMATCH")
    if observed.phase != "EARLY":
        return _evaluation(declaration, "EARLY", "BLOCK", "PHASE_MISMATCH")
    if observed.stage != declaration.early.stage:
        return _evaluation(declaration, "EARLY", "BLOCK", "STAGE_MISMATCH")
    if observed.subject.semantic_sha256 != current.semantic_sha256:
        return _evaluation(declaration, "EARLY", "BLOCK", "SUBJECT_MISMATCH")

    observed_names = {item.name for item in observed.invalidators}
    if observed_names != declared_names:
        return _evaluation(
            declaration, "EARLY", "BLOCK",
            "OBSERVATION_INVALIDATOR_SET_MISMATCH")
    observed_by_name = {item.name: item for item in observed.invalidators}
    for item in current_states:
        prior = observed_by_name[item.name]
        if prior.subject.semantic_sha256 != item.subject.semantic_sha256:
            return _evaluation(declaration, "EARLY", "BLOCK", "INVALIDATED")

    _, observed_time = _timestamp(observed.observed_at, "observed_at")
    age_s = (current_time - observed_time).total_seconds()
    if age_s < 0:
        return _evaluation(
            declaration, "EARLY", "BLOCK", "FUTURE_OBSERVATION")
    if (declaration.maximum_age_s is not None and
            age_s > declaration.maximum_age_s):
        return _evaluation(declaration, "EARLY", "BLOCK", "STALE_OBSERVATION")
    if observed.status != "PASS":
        return _evaluation(
            declaration, "EARLY", "BLOCK", "OBSERVATION_NOT_PASS")
    return _evaluation(declaration, "EARLY", "PROCEED", "EARLY_PASS")


def evaluate_late(
        pair: FactPair | Mapping[str, Any],
        observation: FactObservation | Mapping[str, Any] | None,
        *,
        current_subject: SubjectIdentity | Mapping[str, Any],
) -> FactEvaluation:
    """Authorize a final claim only from the declared current late authority.

    There is intentionally no early-observation argument: an early PASS cannot
    be substituted, promoted, or otherwise used to satisfy this decision.
    """
    declaration = _coerce_pair(pair)
    current = _subject(current_subject, "current_subject")
    observed = _coerce_observation(observation)
    if observed is None:
        return _evaluation(declaration, "LATE", "BLOCK", "MISSING_OBSERVATION")
    if observed.fact != declaration.fact:
        return _evaluation(declaration, "LATE", "BLOCK", "FACT_MISMATCH")
    if observed.phase != "LATE":
        return _evaluation(declaration, "LATE", "BLOCK", "PHASE_MISMATCH")
    if observed.stage != declaration.late.stage:
        return _evaluation(declaration, "LATE", "BLOCK", "STAGE_MISMATCH")
    if observed.authority != declaration.late.authority:
        return _evaluation(declaration, "LATE", "BLOCK", "AUTHORITY_MISMATCH")
    if observed.subject.semantic_sha256 != current.semantic_sha256:
        return _evaluation(declaration, "LATE", "BLOCK", "SUBJECT_MISMATCH")
    if observed.status != "PASS":
        return _evaluation(
            declaration, "LATE", "BLOCK", "OBSERVATION_NOT_PASS")
    return _evaluation(declaration, "LATE", "PROCEED", "LATE_PASS")


__all__ = [
    "DISPOSITIONS", "FactEvaluation", "FactObservation", "FactPair",
    "FactValidationError", "InvalidatorState", "OBSERVATION_STATUSES",
    "PHASES", "REASONS", "ROLES", "SCHEMA", "evaluate_early",
    "evaluate_late",
]
