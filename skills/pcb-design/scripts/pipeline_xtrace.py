#!/usr/bin/env python3
"""Parse dedicated Bash xtrace records without interpreting shell text.

Only records emitted with the exact ``+PIPELINE_TRACE:SOURCE:LINE: COMMAND``
prefix are considered.  ``COMMAND`` is retained as opaque evidence: this module
does not split, expand, evaluate, or execute it.  Source lines acquire stage
meaning exclusively through caller-supplied maps tied to an exact driver digest.
"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence


SCHEMA = 1
STAGE_ID_RE = re.compile(r"^[A-Z][A-Z0-9-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TRACE_PREFIX = "+PIPELINE_TRACE:"
TRACE_RE = re.compile(
    r"^\+PIPELINE_TRACE:(?P<source>.+):(?P<line>[1-9][0-9]*): "
    r"(?P<command>.+)$")


class XTraceValidationError(ValueError):
    """A trace or its source-line declaration is incomplete or inconsistent."""


def _fail(message: str) -> None:
    raise XTraceValidationError(message)


def _stage_id(value: object, where: str) -> str:
    if not isinstance(value, str) or STAGE_ID_RE.fullmatch(value) is None:
        _fail(f"{where}: expected {STAGE_ID_RE.pattern}, got {value!r}")
    return value


def _digest(value: object, where: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _fail(f"{where}: expected 64 lowercase hexadecimal characters")
    return value


def _root(value: str | Path, where: str) -> PurePosixPath:
    text = str(value)
    if "\0" in text:
        _fail(f"{where}: NUL bytes are not valid paths")
    path = PurePosixPath(posixpath.normpath(text))
    if not path.is_absolute():
        _fail(f"{where}: expected an absolute path")
    return path


def _declared_driver(value: object, where: str) -> str:
    """Validate canonical ``project/...`` or ``repo/...`` mapping keys."""
    if not isinstance(value, str) or not value or "\0" in value or "\\" in value:
        _fail(f"{where}: expected a normalized driver-relative path")
    if value.startswith("/") or posixpath.normpath(value) != value:
        _fail(f"{where}: driver path must already be normalized")
    parts = PurePosixPath(value).parts
    if len(parts) < 2 or parts[0] not in {"project", "repo"}:
        _fail(f"{where}: driver path must begin project/ or repo/")
    if any(part in {"", ".", ".."} for part in parts):
        _fail(f"{where}: driver path cannot contain empty, dot, or parent parts")
    return value


@dataclass(frozen=True, order=True)
class DriverLine:
    """One normalized source location used as an exact mapping key."""

    driver: str
    line: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "driver", _declared_driver(
            self.driver, "DriverLine.driver"))
        if not isinstance(self.line, int) or isinstance(self.line, bool) or self.line <= 0:
            _fail("DriverLine.line: expected a positive integer")


@dataclass(frozen=True)
class XTraceRecord:
    """One dedicated trace line, with its command retained byte-for-text."""

    source: str
    location: DriverLine
    command: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "source": self.source,
            "driver": self.location.driver,
            "line": self.location.line,
            "command": self.command,
        }


@dataclass(frozen=True)
class UnmappedExecutable:
    """A traced command whose source location has no declared disposition."""

    location: DriverLine
    command: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "driver": self.location.driver,
            "line": self.location.line,
            "command": self.command,
        }


@dataclass(frozen=True)
class XTraceObservation:
    """Exact observed stage sequence plus every unmapped executable record."""

    driver_sha256: str
    observed_stage_ids: tuple[str, ...]
    unmapped_executable: tuple[UnmappedExecutable, ...]
    dedicated_record_count: int
    ignored_record_count: int
    collapsed_duplicate_count: int

    @property
    def fully_mapped(self) -> bool:
        return not self.unmapped_executable

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "driver_sha256": self.driver_sha256,
            "fully_mapped": self.fully_mapped,
            "observed_stage_ids": list(self.observed_stage_ids),
            "unmapped_executable": [
                item.to_mapping() for item in self.unmapped_executable],
            "dedicated_record_count": self.dedicated_record_count,
            "ignored_record_count": self.ignored_record_count,
            "collapsed_duplicate_count": self.collapsed_duplicate_count,
        }


def _line_key(value: object, where: str) -> DriverLine:
    if isinstance(value, DriverLine):
        return value
    if (isinstance(value, tuple) and len(value) == 2 and
            isinstance(value[0], str)):
        return DriverLine(value[0], value[1])
    _fail(f"{where}: expected DriverLine or (driver, line) tuple")


def _stage_map(
        value: Mapping[object, object], where: str) -> dict[DriverLine, str]:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    result: dict[DriverLine, str] = {}
    for raw_key, raw_stage in value.items():
        key = _line_key(raw_key, where)
        stage = _stage_id(raw_stage, f"{where}[{key!r}]")
        if key in result:
            _fail(f"{where}: duplicate normalized source location {key!r}")
        result[key] = stage
    return result


def _ignored_lines(value: Sequence[object]) -> frozenset[DriverLine]:
    if (not isinstance(value, (list, tuple, set, frozenset)) or
            isinstance(value, (str, bytes, bytearray))):
        _fail("ignored_lines: expected a collection of source locations")
    material = [_line_key(item, "ignored_lines") for item in value]
    if len(material) != len(set(material)):
        _fail("ignored_lines: duplicate normalized source location")
    return frozenset(material)


def _relative_to(path: PurePosixPath, root: PurePosixPath) -> PurePosixPath | None:
    try:
        return path.relative_to(root)
    except ValueError:
        return None


def _normalize_source(
        source: str, *, project_root: PurePosixPath,
        repo_root: PurePosixPath) -> DriverLine | None:
    # The line number is attached by the parser after normalization.  Returning
    # a placeholder keeps all path policy in this one function.
    if not source or "\0" in source or "\\" in source:
        _fail("trace source: expected a non-empty POSIX path without NUL bytes")
    path = PurePosixPath(posixpath.normpath(source))
    if not path.is_absolute():
        _fail(f"trace source: expected an absolute path, got {source!r}")
    relative = _relative_to(path, project_root)
    if relative is not None and relative.parts:
        return DriverLine("project/" + relative.as_posix(), 1)
    relative = _relative_to(path, repo_root)
    if relative is not None and relative.parts:
        return DriverLine("repo/" + relative.as_posix(), 1)
    _fail(f"trace source lies outside supplied project/repo roots: {source}")


def parse_xtrace(
        trace_text: str, line_to_stage: Mapping[object, object], *,
        project_root: str | Path, repo_root: str | Path,
        expected_driver_sha256: str, trace_driver_sha256: str,
        trace_complete: bool,
        ignored_lines: Sequence[object] = (),
        failure_handlers: Mapping[object, object] | None = None,
) -> XTraceObservation:
    """Parse one captured trace without evaluating its command payload.

    ``line_to_stage`` and ``failure_handlers`` use :class:`DriverLine` keys or
    ``(driver, line)`` tuples.  Driver names are canonical ``project/...`` or
    ``repo/...`` relative paths, which removes only the supplied absolute roots.

    ``trace_complete`` is the capture layer's explicit close witness.  It is
    required because a file truncated exactly at a newline cannot be diagnosed
    from text alone.  A missing final newline is independently rejected.
    """
    if not isinstance(trace_text, str):
        _fail("trace_text: expected text")
    if not isinstance(trace_complete, bool):
        _fail("trace_complete: expected a boolean close witness")
    if not trace_complete:
        _fail("trace is truncated: capture close witness is absent")
    if not trace_text:
        _fail("trace is empty")
    if not trace_text.endswith("\n"):
        _fail("trace is truncated: final newline is absent")

    expected_digest = _digest(expected_driver_sha256, "expected_driver_sha256")
    observed_digest = _digest(trace_driver_sha256, "trace_driver_sha256")
    if expected_digest != observed_digest:
        _fail("trace source/driver digest differs from the declared driver")

    project = _root(project_root, "project_root")
    repo = _root(repo_root, "repo_root")
    stage_map = _stage_map(line_to_stage, "line_to_stage")
    handler_map = _stage_map(failure_handlers or {}, "failure_handlers")
    ignored = _ignored_lines(ignored_lines)
    overlaps = ((set(stage_map) & set(handler_map)) |
                (set(stage_map) & set(ignored)) |
                (set(handler_map) & set(ignored)))
    if overlaps:
        _fail("source locations have multiple dispositions: " +
              ", ".join(repr(item) for item in sorted(overlaps)))

    observed: list[str] = []
    unmapped: list[UnmappedExecutable] = []
    dedicated = ignored_count = collapsed = 0
    for physical_line, text in enumerate(trace_text.splitlines(), start=1):
        if not text.startswith(TRACE_PREFIX):
            continue
        match = TRACE_RE.fullmatch(text)
        if match is None:
            _fail(f"malformed dedicated trace record at captured line {physical_line}")
        source = match.group("source")
        command = match.group("command")
        normalized = _normalize_source(
            source, project_root=project, repo_root=repo)
        assert normalized is not None
        location = DriverLine(normalized.driver, int(match.group("line")))
        record = XTraceRecord(source, location, command)
        dedicated += 1

        if location in ignored:
            ignored_count += 1
            continue
        if location in handler_map:
            stage_id = handler_map[location]
            # A handler belongs to the initiating stage only after that stage
            # has actually appeared immediately before it. Accepting it first,
            # or reaching back across another stage, would invent execution.
            if not observed or observed[-1] != stage_id:
                _fail(f"failure handler {location!r} does not follow its "
                      f"initiating stage {stage_id}")
        elif location in stage_map:
            stage_id = stage_map[location]
        else:
            unmapped.append(UnmappedExecutable(record.location, record.command))
            continue

        if observed and observed[-1] == stage_id:
            collapsed += 1
        else:
            observed.append(stage_id)

    if dedicated == 0:
        _fail("trace is empty: no dedicated PIPELINE_TRACE records")
    return XTraceObservation(
        driver_sha256=observed_digest,
        observed_stage_ids=tuple(observed),
        unmapped_executable=tuple(unmapped),
        dedicated_record_count=dedicated,
        ignored_record_count=ignored_count,
        collapsed_duplicate_count=collapsed,
    )


__all__ = [
    "DriverLine", "SCHEMA", "TRACE_PREFIX", "UnmappedExecutable",
    "XTraceObservation", "XTraceRecord", "XTraceValidationError",
    "parse_xtrace",
]
