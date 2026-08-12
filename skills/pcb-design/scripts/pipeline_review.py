#!/usr/bin/env python3
"""Strict bounded review commissions and durable witness admissibility.

This core module parses typed data; it does not launch reviewers or translate
legacy Markdown.  The runtime owns process deadlines.  An adapter which reads
a witness file must supply the durable output path/hash and observed input
artifact hashes to :func:`assess_witness`.  ``completed_at`` is a claim inside
the witness, not proof of filesystem creation time; the adapter must also
refuse files created after the launcher deadline.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Mapping, Optional, Sequence

from pipeline_identity import SubjectIdentity


SCHEMA = 1
ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PROJECT_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CHECK_STATUSES = frozenset({"PASS", "FAIL", "INCOMPLETE"})
DESIGN_VERDICTS = frozenset({"SOUND", "DEFECTIVE", "INCOMPLETE"})
ORDER_VERDICTS = frozenset({
    "ORDER", "FIRST-ARTICLE-ONLY", "DO-NOT-ORDER", "BLOCKED-SOURCING",
})


class ReviewValidationError(ValueError):
    """A commission or witness violates schema-1 review invariants."""


class ReviewInadmissibleError(RuntimeError):
    """A well-formed witness is not admissible for its commission."""


def _fail(message: str) -> None:
    raise ReviewValidationError(message)


def _exact(value: Mapping[str, Any], fields: set[str], where: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    actual = set(value)
    if actual != fields:
        _fail(f"{where}: fields differ (missing={sorted(fields - actual)}, "
              f"unknown={sorted(actual - fields)})")


def _enum(value: Any, allowed: frozenset[str], where: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{where}: expected one of {sorted(allowed)}, got {value!r}")
    return value


def _match(value: Any, pattern: re.Pattern[str], where: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        _fail(f"{where}: expected {pattern.pattern}, got {value!r}")
    return value


def _timestamp(value: Any, where: str) -> tuple[str, datetime]:
    if (not isinstance(value, str) or "T" not in value or
            not value.endswith("Z")):
        _fail(f"{where}: expected a canonical UTC RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        _fail(f"{where}: invalid UTC RFC3339 timestamp {value!r}")
    if parsed.utcoffset() != timezone.utc.utcoffset(None):
        _fail(f"{where}: timestamp must be UTC")
    return value, parsed


def _safe_path(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        _fail(f"{where}: expected a non-empty relative POSIX path")
    path = PurePosixPath(value)
    if (path.is_absolute() or any(part in ("", ".", "..") for part in path.parts)
            or path.as_posix() != value):
        _fail(f"{where}: path must be normalized, relative, and non-traversing")
    return value


def _symbols(value: Any, where: str, *, nonempty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        _fail(f"{where}: expected a sorted list of symbolic names")
    result = tuple(_match(item, SYMBOL_RE, f"{where} item") for item in value)
    if nonempty and not result:
        _fail(f"{where}: denominator must be non-zero")
    if list(result) != sorted(set(result)):
        _fail(f"{where}: names must be sorted and unique")
    return result


def _subject(value: SubjectIdentity | Mapping[str, Any]) -> SubjectIdentity:
    if isinstance(value, SubjectIdentity):
        return value
    if isinstance(value, Mapping):
        try:
            return SubjectIdentity.from_mapping(value)
        except ValueError as exc:
            _fail(f"subject: {exc}")
    _fail("subject: expected SubjectIdentity or its exact mapping")


def _json_object(text: str, where: str) -> Mapping[str, Any]:
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        _fail(f"{where} JSON: {exc}")
    if not isinstance(value, Mapping):
        _fail(f"{where} JSON: expected an object")
    return value


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class ArtifactHash:
    path: str
    sha256: str

    def __post_init__(self) -> None:
        _safe_path(self.path, "artifact.path")
        _match(self.sha256, SHA256_RE, "artifact.sha256")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ArtifactHash":
        _exact(value, {"path", "sha256"}, "ArtifactHash")
        return cls(path=value["path"], sha256=value["sha256"])

    def to_mapping(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


def _artifacts(value: Any) -> tuple[ArtifactHash, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        _fail("artifacts: expected a non-empty sorted list")
    result = tuple(item if isinstance(item, ArtifactHash)
                   else ArtifactHash.from_mapping(item) for item in value)
    paths = [item.path for item in result]
    if paths != sorted(set(paths)):
        _fail("artifacts: paths must be sorted and unique")
    return result


@dataclass(frozen=True)
class ChecklistResult:
    item: str
    status: str

    def __post_init__(self) -> None:
        _match(self.item, SYMBOL_RE, "checklist item")
        _enum(self.status, CHECK_STATUSES, "checklist status")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ChecklistResult":
        _exact(value, {"item", "status"}, "ChecklistResult")
        return cls(item=value["item"], status=value["status"])

    def to_mapping(self) -> dict[str, str]:
        return {"item": self.item, "status": self.status}


def _results(value: Any) -> tuple[ChecklistResult, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        _fail("checklist: expected a non-empty sorted result list")
    result = tuple(item if isinstance(item, ChecklistResult)
                   else ChecklistResult.from_mapping(item) for item in value)
    names = [item.item for item in result]
    if names != sorted(set(names)):
        _fail("checklist: result names must be sorted and unique")
    return result


@dataclass(frozen=True)
class ReviewOutput:
    path: str
    sha256: str

    def __post_init__(self) -> None:
        _safe_path(self.path, "output.path")
        _match(self.sha256, SHA256_RE, "output.sha256")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewOutput":
        _exact(value, {"path", "sha256"}, "ReviewOutput")
        return cls(path=value["path"], sha256=value["sha256"])

    def to_mapping(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}


@dataclass(frozen=True)
class ReviewCommission:
    commission_id: str
    project: str
    source_commit: str
    subject: SubjectIdentity | Mapping[str, Any]
    lens: str
    checklist: Sequence[str]
    exclusions: Sequence[str]
    artifacts: Sequence[ArtifactHash | Mapping[str, Any]]
    output_path: str
    issued_at: str
    deadline_at: str
    schema: int = SCHEMA
    _issued: datetime = field(init=False, repr=False, compare=False)
    _deadline: datetime = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _match(self.commission_id, ID_RE, "commission_id")
        _match(self.project, PROJECT_RE, "project")
        _match(self.source_commit, COMMIT_RE, "source_commit")
        object.__setattr__(self, "subject", _subject(self.subject))
        _match(self.lens, SYMBOL_RE, "lens")
        object.__setattr__(self, "checklist",
                           _symbols(self.checklist, "checklist", nonempty=True))
        object.__setattr__(self, "exclusions",
                           _symbols(self.exclusions, "exclusions"))
        if set(self.checklist) & set(self.exclusions):
            _fail("exclusions: a checklist item cannot also be excluded")
        object.__setattr__(self, "artifacts", _artifacts(self.artifacts))
        _safe_path(self.output_path, "output_path")
        issued_text, issued = _timestamp(self.issued_at, "issued_at")
        deadline_text, deadline = _timestamp(self.deadline_at, "deadline_at")
        if deadline <= issued:
            _fail("deadline_at: must follow issued_at")
        object.__setattr__(self, "issued_at", issued_text)
        object.__setattr__(self, "deadline_at", deadline_text)
        object.__setattr__(self, "_issued", issued)
        object.__setattr__(self, "_deadline", deadline)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewCommission":
        fields = {"schema", "commission_id", "project", "source_commit",
                  "subject", "lens", "checklist", "exclusions", "artifacts",
                  "output_path", "issued_at", "deadline_at"}
        _exact(value, fields, "ReviewCommission")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "ReviewCommission":
        return cls.from_mapping(_json_object(text, "ReviewCommission"))

    def to_mapping(self) -> dict[str, Any]:
        return {"schema": self.schema, "commission_id": self.commission_id,
                "project": self.project, "source_commit": self.source_commit,
                "subject": self.subject.to_mapping(), "lens": self.lens,
                "checklist": list(self.checklist),
                "exclusions": list(self.exclusions),
                "artifacts": [item.to_mapping() for item in self.artifacts],
                "output_path": self.output_path, "issued_at": self.issued_at,
                "deadline_at": self.deadline_at}

    def to_json(self) -> str:
        return _json(self.to_mapping())


@dataclass(frozen=True)
class ReviewWitness:
    commission_id: str
    project: str
    source_commit: str
    subject: SubjectIdentity | Mapping[str, Any]
    lens: str
    artifacts: Sequence[ArtifactHash | Mapping[str, Any]]
    checklist: Sequence[ChecklistResult | Mapping[str, Any]]
    graded: int
    total: int
    output: ReviewOutput | Mapping[str, Any]
    completed_at: str
    design_verdict: str
    order_verdict: str
    schema: int = SCHEMA
    _completed: datetime = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.schema != SCHEMA or isinstance(self.schema, bool):
            _fail(f"schema: only schema {SCHEMA} is supported")
        _match(self.commission_id, ID_RE, "commission_id")
        _match(self.project, PROJECT_RE, "project")
        _match(self.source_commit, COMMIT_RE, "source_commit")
        object.__setattr__(self, "subject", _subject(self.subject))
        _match(self.lens, SYMBOL_RE, "lens")
        object.__setattr__(self, "artifacts", _artifacts(self.artifacts))
        results = _results(self.checklist)
        object.__setattr__(self, "checklist", results)
        for name in ("graded", "total"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                _fail(f"{name}: expected a non-negative integer")
        expected_graded = sum(item.status != "INCOMPLETE" for item in results)
        if self.total != len(results) or self.graded != expected_graded:
            _fail("coverage: graded/total must exactly match checklist results")
        if isinstance(self.output, Mapping):
            object.__setattr__(self, "output", ReviewOutput.from_mapping(self.output))
        elif not isinstance(self.output, ReviewOutput):
            _fail("output: expected ReviewOutput or its exact mapping")
        completed_text, completed = _timestamp(self.completed_at, "completed_at")
        object.__setattr__(self, "completed_at", completed_text)
        object.__setattr__(self, "_completed", completed)
        _enum(self.design_verdict, DESIGN_VERDICTS, "design_verdict")
        _enum(self.order_verdict, ORDER_VERDICTS, "order_verdict")
        statuses = {item.status for item in results}
        if self.design_verdict == "SOUND" and statuses != {"PASS"}:
            _fail("SOUND requires every non-zero checklist item to PASS")
        if self.design_verdict == "DEFECTIVE" and (
                "FAIL" not in statuses or "INCOMPLETE" in statuses):
            _fail("DEFECTIVE requires a complete checklist with at least one FAIL")
        if self.design_verdict == "INCOMPLETE" and "INCOMPLETE" not in statuses:
            _fail("INCOMPLETE verdict requires an incomplete checklist item")
        if self.design_verdict != "SOUND" and self.order_verdict in {
                "ORDER", "FIRST-ARTICLE-ONLY"}:
            _fail("only a SOUND design may carry an affirmative order verdict")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewWitness":
        fields = {"schema", "commission_id", "project", "source_commit",
                  "subject", "lens", "artifacts", "checklist", "graded",
                  "total", "output", "completed_at", "design_verdict",
                  "order_verdict"}
        _exact(value, fields, "ReviewWitness")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "ReviewWitness":
        return cls.from_mapping(_json_object(text, "ReviewWitness"))

    def to_mapping(self) -> dict[str, Any]:
        return {"schema": self.schema, "commission_id": self.commission_id,
                "project": self.project, "source_commit": self.source_commit,
                "subject": self.subject.to_mapping(), "lens": self.lens,
                "artifacts": [item.to_mapping() for item in self.artifacts],
                "checklist": [item.to_mapping() for item in self.checklist],
                "graded": self.graded, "total": self.total,
                "output": self.output.to_mapping(),
                "completed_at": self.completed_at,
                "design_verdict": self.design_verdict,
                "order_verdict": self.order_verdict}

    def to_json(self) -> str:
        return _json(self.to_mapping())


@dataclass(frozen=True)
class ReviewAdmissibility:
    admissible: bool
    reasons: tuple[str, ...]
    design_verdict: str
    order_verdict: str

    def to_mapping(self) -> dict[str, Any]:
        return {"admissible": self.admissible, "reasons": list(self.reasons),
                "design_verdict": self.design_verdict,
                "order_verdict": self.order_verdict}


def assess_witness(
        commission: ReviewCommission, witness: ReviewWitness, *,
        observed_output_path: Optional[str] = None,
        observed_output_sha256: Optional[str] = None,
        observed_artifact_hashes: Optional[Mapping[str, str]] = None,
        now: Optional[str] = None) -> ReviewAdmissibility:
    """Return all reasons a well-formed witness is not durable evidence."""
    if not isinstance(commission, ReviewCommission):
        _fail("commission: expected ReviewCommission")
    if not isinstance(witness, ReviewWitness):
        _fail("witness: expected ReviewWitness")
    reasons: list[str] = []
    comparisons = (
        (witness.commission_id, commission.commission_id, "COMMISSION_MISMATCH"),
        (witness.project, commission.project, "PROJECT_MISMATCH"),
        (witness.source_commit, commission.source_commit, "COMMIT_MISMATCH"),
        (witness.subject, commission.subject, "SUBJECT_MISMATCH"),
        (witness.lens, commission.lens, "LENS_MISMATCH"),
        (witness.artifacts, commission.artifacts, "ARTIFACT_BINDING_MISMATCH"),
        (tuple(item.item for item in witness.checklist), commission.checklist,
         "CHECKLIST_MISMATCH"),
        (witness.output.path, commission.output_path, "OUTPUT_PATH_MISMATCH"),
    )
    for got, expected, reason in comparisons:
        if got != expected:
            reasons.append(reason)
    if witness._completed < commission._issued:
        reasons.append("COMPLETED_BEFORE_ISSUE")
    if witness._completed > commission._deadline:
        reasons.append("LATE")
    if witness.design_verdict == "INCOMPLETE" or witness.graded != witness.total:
        reasons.append("INCOMPLETE")
    if now is not None:
        _, current = _timestamp(now, "now")
        if witness._completed > current:
            reasons.append("FUTURE_COMPLETION")

    if observed_output_path is None or observed_output_sha256 is None:
        reasons.append("OUTPUT_NOT_OBSERVED")
    else:
        try:
            durable_path = _safe_path(observed_output_path, "observed_output_path")
            durable_hash = _match(observed_output_sha256, SHA256_RE,
                                  "observed_output_sha256")
        except ReviewValidationError:
            reasons.append("OUTPUT_OBSERVATION_INVALID")
        else:
            if durable_path != commission.output_path:
                reasons.append("DURABLE_OUTPUT_PATH_MISMATCH")
            if durable_hash != witness.output.sha256:
                reasons.append("OUTPUT_HASH_MISMATCH")

    if observed_artifact_hashes is None:
        reasons.append("ARTIFACTS_NOT_OBSERVED")
    elif not isinstance(observed_artifact_hashes, Mapping):
        reasons.append("ARTIFACT_OBSERVATION_INVALID")
    else:
        expected = {item.path: item.sha256 for item in commission.artifacts}
        observed = dict(observed_artifact_hashes)
        if set(observed) != set(expected) or any(
                not isinstance(path, str) or not isinstance(digest, str) or
                SHA256_RE.fullmatch(digest) is None
                for path, digest in observed.items()):
            reasons.append("ARTIFACT_OBSERVATION_INVALID")
        elif observed != expected:
            reasons.append("OBSERVED_ARTIFACT_MISMATCH")

    unique = tuple(dict.fromkeys(reasons))
    return ReviewAdmissibility(
        admissible=not unique, reasons=unique,
        design_verdict=witness.design_verdict,
        order_verdict=witness.order_verdict)


def require_admissible(*args: Any, **kwargs: Any) -> ReviewWitness:
    """Return the witness or raise with every admissibility failure reason."""
    witness = args[1] if len(args) > 1 else kwargs.get("witness")
    result = assess_witness(*args, **kwargs)
    if not result.admissible:
        raise ReviewInadmissibleError(
            "review witness is inadmissible: " + ", ".join(result.reasons))
    return witness


__all__ = [
    "ArtifactHash", "ChecklistResult", "DESIGN_VERDICTS", "ORDER_VERDICTS",
    "ReviewAdmissibility", "ReviewCommission", "ReviewInadmissibleError",
    "ReviewOutput", "ReviewValidationError", "ReviewWitness",
    "assess_witness", "require_admissible",
]
