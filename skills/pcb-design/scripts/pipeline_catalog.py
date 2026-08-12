#!/usr/bin/env python3
"""Strict, non-executing catalog of observed legacy pipeline stages.

``StageSpec`` describes reusable semantic work.  This module deliberately keeps
legacy command, working-directory, path, ordering, and verdict-authority
evidence beside that contract rather than adding project-specific execution
fields to it.  A catalog can therefore seed a ``StageRegistry`` and a shadow
observation without becoming an executor or changing legacy authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence

from pipeline_contract import (APPLICABILITIES, STAGE_ID_RE,
                               ContractValidationError, StageSpec)
from pipeline_registry import RegistryValidationError, StageRegistry


SCHEMA = 1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
TOKEN_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
LEGACY_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
AUTHORITY_SEMANTICS = frozenset({"exit", "postcheck", "ignored_until"})


class CatalogValidationError(ValueError):
    """Legacy catalog evidence is malformed, ambiguous, or inconsistent."""


def _fail(message: str) -> None:
    raise CatalogValidationError(message)


def _exact_fields(value: Mapping[str, Any], expected: set[str], where: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    actual = set(value)
    missing = expected - actual
    unknown = actual - expected
    if missing or unknown:
        _fail(f"{where}: fields differ (missing={sorted(missing)}, "
              f"unknown={sorted(unknown)})")


def _schema(value: Any, where: str) -> int:
    if value != SCHEMA or isinstance(value, bool):
        _fail(f"{where}.schema: only schema {SCHEMA} is supported")
    return value


def _token(value: Any, where: str) -> str:
    if not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None:
        _fail(f"{where}: expected {TOKEN_RE.pattern}, got {value!r}")
    return value


def _relative_path(value: Any, where: str, *, root_ok: bool = False) -> str:
    """Return one canonical project-relative POSIX path.

    Backslashes are rejected instead of being interpreted differently on each
    host.  ``PurePosixPath`` collapsing a spelling is also a rejection: catalog
    evidence records the exact path the legacy driver named.
    """
    if not isinstance(value, str) or not value:
        _fail(f"{where}: expected a non-empty relative POSIX path")
    if "\\" in value or "\x00" in value:
        _fail(f"{where}: backslashes and NUL bytes are forbidden")
    if value == ".":
        if root_ok:
            return value
        _fail(f"{where}: project root is not a file path")
    path = PurePosixPath(value)
    if path.is_absolute():
        _fail(f"{where}: absolute paths are forbidden")
    parts = path.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        _fail(f"{where}: path must be normalized, relative, and non-escaping")
    canonical = path.as_posix()
    if canonical != value or value.endswith("/") or value.startswith("//"):
        _fail(f"{where}: path must use its normalized POSIX spelling")
    return canonical


def _sorted_strings(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or isinstance(value, (str, bytes)):
        _fail(f"{where}: expected a sorted list")
    result = tuple(value)
    if any(not isinstance(item, str) or not item for item in result):
        _fail(f"{where}: every item must be a non-empty string")
    if list(result) != sorted(set(result)):
        _fail(f"{where}: values must be sorted and unique")
    return result


def _stage_ids(value: Any, where: str) -> tuple[str, ...]:
    result = _sorted_strings(value, where)
    for item in result:
        if STAGE_ID_RE.fullmatch(item) is None:
            _fail(f"{where}: {item!r} is not a stage id")
    return result


def _output_symbols(value: Any, where: str) -> tuple[str, ...]:
    # StageSpec owns the symbolic-name grammar; parsing a small temporary spec
    # here would couple validation to unrelated fields, so compare against the
    # real spec's already-validated symbols in LegacyStageBinding instead.
    return _sorted_strings(value, where)


def _output_paths(value: Any, where: str) -> tuple[str, ...]:
    result = _sorted_strings(value, where)
    return tuple(_relative_path(item, f"{where}[{index}]")
                 for index, item in enumerate(result))


def _argv(value: Any, where: str) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)) or isinstance(value, (str, bytes)):
        _fail(f"{where}: argv must be a JSON list of data, never a shell string")
    result = tuple(value)
    if not result:
        _fail(f"{where}: argv must contain an executable")
    if any(not isinstance(item, str) or "\x00" in item for item in result):
        _fail(f"{where}: every argv item must be a NUL-free string")
    if not result[0]:
        _fail(f"{where}: argv[0] must name an executable")
    return result


def _loads_exact(text: str, where: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                _fail(f"{where}: duplicate JSON field {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=pairs)
    except (TypeError, json.JSONDecodeError) as exc:
        _fail(f"{where}: invalid JSON ({exc})")


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


@dataclass(frozen=True)
class LegacyStageBinding:
    """One observed legacy stage and its evidence, not an execution request."""

    sequence: int
    legacy_key: str
    spec: StageSpec | Mapping[str, Any]
    dependencies: Sequence[str] = field(default_factory=tuple)
    argv: Sequence[str] | None = None
    shell_builtin: str | None = None
    cwd: str = "."
    applicability: str = "APPLIES"
    applicability_reason: str | None = None
    authority: str = "exit"
    authority_binding: str | None = None
    accepted_output_symbols: Sequence[str] = field(default_factory=tuple)
    accepted_output_paths: Sequence[str] = field(default_factory=tuple)
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        _schema(self.schema, "LegacyStageBinding")
        if (not isinstance(self.sequence, int) or isinstance(self.sequence, bool)
                or self.sequence <= 0):
            _fail("LegacyStageBinding.sequence: expected a positive integer")
        if (not isinstance(self.legacy_key, str) or
                LEGACY_KEY_RE.fullmatch(self.legacy_key) is None):
            _fail("LegacyStageBinding.legacy_key: expected "
                  f"{LEGACY_KEY_RE.pattern}")

        if isinstance(self.spec, Mapping):
            try:
                parsed = StageSpec.from_mapping(self.spec)
            except ContractValidationError as exc:
                _fail(f"LegacyStageBinding.spec: {exc}")
            object.__setattr__(self, "spec", parsed)
        elif not isinstance(self.spec, StageSpec):
            _fail("LegacyStageBinding.spec: expected StageSpec or exact mapping")

        object.__setattr__(self, "dependencies",
                           _stage_ids(self.dependencies, "dependencies"))
        parsed_argv = _argv(self.argv, "argv")
        builtin = self.shell_builtin
        if builtin is not None:
            builtin = _token(builtin, "shell_builtin")
        if (parsed_argv is None) == (builtin is None):
            _fail("command evidence: exactly one of argv or shell_builtin is required")
        object.__setattr__(self, "argv", parsed_argv)
        object.__setattr__(self, "shell_builtin", builtin)
        object.__setattr__(self, "cwd",
                           _relative_path(self.cwd, "cwd", root_ok=True))

        if self.applicability not in APPLICABILITIES:
            _fail("applicability: expected one of "
                  f"{sorted(APPLICABILITIES)}, got {self.applicability!r}")
        reason = self.applicability_reason
        if reason is not None and not isinstance(reason, str):
            _fail("applicability_reason: expected string or null")
        if self.applicability == "NOT_APPLICABLE":
            if not isinstance(reason, str) or not reason.strip():
                _fail("applicability_reason: NOT_APPLICABLE requires a reason")
            object.__setattr__(self, "applicability_reason", reason.strip())
        elif reason is not None:
            _fail("applicability_reason: APPLIES requires null")

        if self.authority not in AUTHORITY_SEMANTICS:
            _fail(f"authority: expected one of {sorted(AUTHORITY_SEMANTICS)}")
        ref = self.authority_binding
        if self.authority == "exit":
            if ref is not None:
                _fail("authority_binding: exit authority requires null")
        elif (not isinstance(ref, str) or
              LEGACY_KEY_RE.fullmatch(ref) is None):
            _fail(f"authority_binding: {self.authority} requires a legacy key")

        symbols = _output_symbols(self.accepted_output_symbols,
                                  "accepted_output_symbols")
        paths = _output_paths(self.accepted_output_paths,
                              "accepted_output_paths")
        object.__setattr__(self, "accepted_output_symbols", symbols)
        object.__setattr__(self, "accepted_output_paths", paths)
        if self.applicability == "APPLIES":
            if symbols != tuple(self.spec.produces):
                _fail(f"{self.spec.id}: accepted output symbols must equal "
                      f"StageSpec.produces {tuple(self.spec.produces)!r}")
        elif symbols or paths:
            _fail("NOT_APPLICABLE bindings cannot accept output symbols or paths")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LegacyStageBinding":
        fields = {
            "schema", "sequence", "legacy_key", "spec", "dependencies",
            "argv", "shell_builtin", "cwd", "applicability",
            "applicability_reason", "authority", "authority_binding",
            "accepted_output_symbols", "accepted_output_paths",
        }
        _exact_fields(value, fields, "LegacyStageBinding")
        return cls(**{name: value[name] for name in fields})

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "sequence": self.sequence,
            "legacy_key": self.legacy_key,
            "spec": self.spec.to_mapping(),
            "dependencies": list(self.dependencies),
            "argv": list(self.argv) if self.argv is not None else None,
            "shell_builtin": self.shell_builtin,
            "cwd": self.cwd,
            "applicability": self.applicability,
            "applicability_reason": self.applicability_reason,
            "authority": self.authority,
            "authority_binding": self.authority_binding,
            "accepted_output_symbols": list(self.accepted_output_symbols),
            "accepted_output_paths": list(self.accepted_output_paths),
        }


@dataclass(frozen=True)
class LegacyPipelineCatalog:
    """Exact schema-1 record of one project driver and its observed stages."""

    project_slug: str
    driver_relative_path: str
    driver_sha256: str
    entrypoint: str
    mode: str
    bindings: Sequence[LegacyStageBinding | Mapping[str, Any]]
    schema: int = SCHEMA

    def __post_init__(self) -> None:
        _schema(self.schema, "LegacyPipelineCatalog")
        if (not isinstance(self.project_slug, str) or
                SLUG_RE.fullmatch(self.project_slug) is None):
            _fail(f"project_slug: expected {SLUG_RE.pattern}")
        object.__setattr__(self, "driver_relative_path", _relative_path(
            self.driver_relative_path, "driver_relative_path"))
        if (not isinstance(self.driver_sha256, str) or
                SHA256_RE.fullmatch(self.driver_sha256) is None):
            _fail("driver_sha256: expected exactly 64 lowercase hexadecimal characters")
        _token(self.entrypoint, "entrypoint")
        _token(self.mode, "mode")
        if (not isinstance(self.bindings, (list, tuple)) or
                isinstance(self.bindings, (str, bytes)) or not self.bindings):
            _fail("bindings: catalog denominator must be a non-empty ordered list")

        parsed: list[LegacyStageBinding] = []
        for index, value in enumerate(self.bindings):
            if isinstance(value, LegacyStageBinding):
                binding = value
            elif isinstance(value, Mapping):
                binding = LegacyStageBinding.from_mapping(value)
            else:
                _fail(f"bindings[{index}]: expected LegacyStageBinding or mapping")
            parsed.append(binding)
        object.__setattr__(self, "bindings", tuple(parsed))

        sequences = [binding.sequence for binding in parsed]
        expected_sequences = list(range(1, len(parsed) + 1))
        if sequences != expected_sequences:
            _fail("bindings: sequence values must be unique, contiguous, and "
                  f"match list order {expected_sequences!r}")
        keys = [binding.legacy_key for binding in parsed]
        if len(keys) != len(set(keys)):
            _fail("bindings: legacy_key values must be unique")
        ids = [binding.spec.id for binding in parsed]
        if len(ids) != len(set(ids)):
            _fail("bindings: StageSpec ids must be unique")

        by_id = {binding.spec.id: binding for binding in parsed}
        by_key = {binding.legacy_key: binding for binding in parsed}
        producer: dict[str, str] = {}
        for binding in parsed:
            for symbol in binding.spec.produces:
                prior = producer.get(symbol)
                if prior is not None:
                    _fail(f"output {symbol!r} has multiple producers: "
                          f"{prior}, {binding.spec.id}")
                producer[symbol] = binding.spec.id

        for binding in parsed:
            for dep in binding.dependencies:
                target = by_id.get(dep)
                if target is None:
                    _fail(f"{binding.legacy_key}: dependency {dep!r} is unknown")
                if target.sequence >= binding.sequence:
                    _fail(f"{binding.legacy_key}: dependency {dep!r} must precede it")
            for symbol in binding.spec.requires:
                internal = producer.get(symbol)
                if internal is None:
                    continue
                target = by_id[internal]
                if target.sequence >= binding.sequence:
                    _fail(f"{binding.legacy_key}: required symbol {symbol!r} is "
                          f"produced by non-prior stage {internal}")
                if internal not in binding.dependencies:
                    _fail(f"{binding.legacy_key}: internal producer {internal} for "
                          f"{symbol!r} is missing from dependencies")

            if binding.authority != "exit":
                target = by_key.get(binding.authority_binding or "")
                if target is None:
                    _fail(f"{binding.legacy_key}: authority_binding "
                          f"{binding.authority_binding!r} is unknown")
                if target.sequence <= binding.sequence:
                    _fail(f"{binding.legacy_key}: {binding.authority} authority "
                          "must refer to a later binding")

        try:
            StageRegistry(binding.spec for binding in parsed)
        except RegistryValidationError as exc:
            _fail(f"bindings cannot form a StageRegistry: {exc}")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LegacyPipelineCatalog":
        fields = {
            "schema", "project_slug", "driver_relative_path", "driver_sha256",
            "entrypoint", "mode", "bindings",
        }
        _exact_fields(value, fields, "LegacyPipelineCatalog")
        return cls(**{name: value[name] for name in fields})

    @classmethod
    def from_json(cls, text: str) -> "LegacyPipelineCatalog":
        return cls.from_mapping(_loads_exact(text, "LegacyPipelineCatalog JSON"))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "project_slug": self.project_slug,
            "driver_relative_path": self.driver_relative_path,
            "driver_sha256": self.driver_sha256,
            "entrypoint": self.entrypoint,
            "mode": self.mode,
            "bindings": [binding.to_mapping() for binding in self.bindings],
        }

    def to_json(self) -> str:
        return _canonical_json(self.to_mapping())

    def stage_registry(self) -> StageRegistry:
        """Build the semantic registry without invoking or joining commands."""
        return StageRegistry(binding.spec for binding in self.bindings)

    def observed_stage_ids(self) -> tuple[str, ...]:
        """Return the exact legacy observation order, including explicit N/A."""
        return tuple(binding.spec.id for binding in self.bindings)

    def driver_matches(self, exact_bytes: bytes) -> bool:
        """Check supplied driver bytes without discovering or executing a path."""
        if not isinstance(exact_bytes, bytes):
            _fail("driver bytes must be exact bytes")
        return hashlib.sha256(exact_bytes).hexdigest() == self.driver_sha256


__all__ = [
    "AUTHORITY_SEMANTICS",
    "CatalogValidationError",
    "LegacyPipelineCatalog",
    "LegacyStageBinding",
    "SCHEMA",
]
