#!/usr/bin/env python3
"""Strict schema-1 typed contracts for declarative PCB pipeline stages."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from pipeline_identity import SubjectIdentity


SCHEMA = 1
STAGE_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")

OWNERS = frozenset({"pcb-design", "kicad-pcb", "jlcpcb-fab"})
LIFECYCLES = frozenset({
    "commission", "architecture", "sourcing", "schematic", "placement",
    "routing", "layout_seal", "fabrication", "release_staging",
    "release_seal", "publication", "first_article", "production",
})
COSTS = frozenset({"cheap", "bounded", "external", "review", "operator"})
WORK_CLASSES = frozenset({
    "local", "network", "backoff", "review_wait", "operator_wait",
})
APPLICABILITIES = frozenset({"APPLIES", "NOT_APPLICABLE"})
STATUSES = frozenset({
    "PASS", "FAIL", "NOT_APPLICABLE", "TIMED_OUT", "INCOMPLETE", "ERROR",
})


class ContractValidationError(ValueError):
    """A stage contract is malformed or violates a fail-closed invariant."""


def _fail(message: str) -> None:
    raise ContractValidationError(message)


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


def _enum(value: Any, allowed: frozenset[str], where: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{where}: expected one of {sorted(allowed)}, got {value!r}")
    return value


def _stage_id(value: Any, where: str = "stage_id") -> str:
    if not isinstance(value, str) or STAGE_ID_RE.fullmatch(value) is None:
        _fail(f"{where}: expected {STAGE_ID_RE.pattern}, got {value!r}")
    return value


def _symbols(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        _fail(f"{where}: expected a sorted list of symbolic names")
    result = tuple(value)
    for item in result:
        if not isinstance(item, str) or SYMBOL_RE.fullmatch(item) is None:
            _fail(f"{where}: {item!r} is not a symbolic name")
    if list(result) != sorted(set(result)):
        _fail(f"{where}: symbolic names must be sorted and unique")
    return result


def _json_value(value: Any, where: str) -> Any:
    """Detach JSON-compatible evidence while rejecting lossy encodings."""
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False)
        return json.loads(encoded)
    except (TypeError, ValueError) as exc:
        _fail(f"{where}: expected a finite JSON value ({exc})")


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


@dataclass(frozen=True)
class StageSpec:
    id: str
    owner: str
    lifecycle: str
    cost: str
    work_class: str
    timeout_s: Optional[float]
    requires: Sequence[str] = field(default_factory=tuple)
    produces: Sequence[str] = field(default_factory=tuple)
    blocks: Sequence[str] = field(default_factory=tuple)
    invalidated_by: Sequence[str] = field(default_factory=tuple)
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _stage_id(self.id, "id")
        _enum(self.owner, OWNERS, "owner")
        _enum(self.lifecycle, LIFECYCLES, "lifecycle")
        _enum(self.cost, COSTS, "cost")
        _enum(self.work_class, WORK_CLASSES, "work_class")
        if self.timeout_s is None:
            if not (self.cost == "operator" and self.work_class == "operator_wait"):
                _fail("timeout_s: only operator/operator_wait declarative stages "
                      "may omit it")
        elif (not isinstance(self.timeout_s, (int, float)) or
              isinstance(self.timeout_s, bool) or
              not math.isfinite(self.timeout_s) or self.timeout_s <= 0):
            _fail("timeout_s: expected a positive finite number")
        for name in ("requires", "produces", "blocks", "invalidated_by"):
            object.__setattr__(self, name, _symbols(getattr(self, name), name))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StageSpec":
        fields = {
            "schema", "id", "owner", "lifecycle", "cost", "work_class",
            "timeout_s", "requires", "produces", "blocks", "invalidated_by",
        }
        _exact_fields(value, fields, "StageSpec", optional={"timeout_s"})
        return cls(
            schema=value["schema"],
            id=value["id"],
            owner=value["owner"],
            lifecycle=value["lifecycle"],
            cost=value["cost"],
            work_class=value["work_class"],
            timeout_s=value.get("timeout_s"),
            requires=value["requires"],
            produces=value["produces"],
            blocks=value["blocks"],
            invalidated_by=value["invalidated_by"],
        )

    @classmethod
    def from_json(cls, text: str) -> "StageSpec":
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError) as exc:
            _fail(f"StageSpec JSON: {exc}")
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        value = {
            "schema": self.schema,
            "id": self.id,
            "owner": self.owner,
            "lifecycle": self.lifecycle,
            "cost": self.cost,
            "work_class": self.work_class,
        }
        if self.timeout_s is not None:
            value["timeout_s"] = self.timeout_s
        value.update({
            "requires": list(self.requires),
            "produces": list(self.produces),
            "blocks": list(self.blocks),
            "invalidated_by": list(self.invalidated_by),
        })
        return value

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class StageResult:
    stage_id: str
    run_id: str
    subject: SubjectIdentity | Mapping[str, Any]
    applicability: str
    applicability_reason: Optional[str]
    status: str
    started_at: str
    finished_at: str
    elapsed_s: float
    graded: int
    total: int
    outputs: Sequence[str] = field(default_factory=tuple)
    findings: Sequence[Any] = field(default_factory=tuple)
    resume: Any = None
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _stage_id(self.stage_id)
        if (not isinstance(self.run_id, str) or not self.run_id.strip() or
                any(char.isspace() for char in self.run_id)):
            _fail("run_id: expected a non-empty whitespace-free identifier")
        if isinstance(self.subject, Mapping):
            object.__setattr__(self, "subject",
                               SubjectIdentity.from_mapping(self.subject))
        elif not isinstance(self.subject, SubjectIdentity):
            _fail("subject: expected SubjectIdentity or its exact mapping")
        _enum(self.applicability, APPLICABILITIES, "applicability")
        _enum(self.status, STATUSES, "status")

        reason = self.applicability_reason
        if reason is not None and not isinstance(reason, str):
            _fail("applicability_reason: expected string or null")
        if self.applicability == "NOT_APPLICABLE":
            if not isinstance(reason, str) or not reason.strip():
                _fail("applicability_reason: NOT_APPLICABLE requires a reason")
            if self.status != "NOT_APPLICABLE":
                _fail("status: NOT_APPLICABLE applicability requires "
                      "NOT_APPLICABLE status")
        else:
            if reason is not None and reason.strip():
                _fail("applicability_reason: APPLIES requires null or empty")
            if self.status == "NOT_APPLICABLE":
                _fail("status: NOT_APPLICABLE requires NOT_APPLICABLE "
                      "applicability")

        started_text, started = _timestamp(self.started_at, "started_at")
        finished_text, finished = _timestamp(self.finished_at, "finished_at")
        object.__setattr__(self, "started_at", started_text)
        object.__setattr__(self, "finished_at", finished_text)
        if finished < started:
            _fail("finished_at: cannot precede started_at")
        if (not isinstance(self.elapsed_s, (int, float)) or
                isinstance(self.elapsed_s, bool) or
                not math.isfinite(self.elapsed_s) or self.elapsed_s < 0):
            _fail("elapsed_s: expected a non-negative finite number")
        for name in ("graded", "total"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                _fail(f"{name}: expected a non-negative integer")
        if self.graded > self.total:
            _fail("graded: cannot exceed total")
        if self.status == "PASS" and not (
                self.applicability == "APPLIES" and self.total > 0 and
                self.graded == self.total):
            _fail("PASS requires APPLIES and graded == total > 0")
        if self.status == "NOT_APPLICABLE" and (self.graded or self.total):
            _fail("NOT_APPLICABLE requires graded == total == 0")

        object.__setattr__(self, "outputs", _symbols(self.outputs, "outputs"))
        if not isinstance(self.findings, (list, tuple)):
            _fail("findings: expected a list")
        object.__setattr__(self, "findings", tuple(
            _json_value(item, f"findings[{index}]")
            for index, item in enumerate(self.findings)))
        object.__setattr__(self, "resume", _json_value(self.resume, "resume"))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StageResult":
        fields = {
            "schema", "stage_id", "run_id", "subject", "applicability",
            "applicability_reason", "status", "started_at", "finished_at",
            "elapsed_s", "graded", "total", "outputs", "findings", "resume",
        }
        _exact_fields(value, fields, "StageResult")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "StageResult":
        try:
            value = json.loads(text)
        except (TypeError, json.JSONDecodeError) as exc:
            _fail(f"StageResult JSON: {exc}")
        return cls.from_mapping(value)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "stage_id": self.stage_id,
            "run_id": self.run_id,
            "subject": self.subject.to_mapping(),
            "applicability": self.applicability,
            "applicability_reason": self.applicability_reason,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_s": self.elapsed_s,
            "graded": self.graded,
            "total": self.total,
            "outputs": list(self.outputs),
            "findings": [_json_value(item, "finding") for item in self.findings],
            "resume": _json_value(self.resume, "resume"),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)


__all__ = [
    "APPLICABILITIES", "COSTS", "ContractValidationError", "LIFECYCLES",
    "OWNERS", "SCHEMA", "STATUSES", "StageResult", "StageSpec",
    "WORK_CLASSES",
]
