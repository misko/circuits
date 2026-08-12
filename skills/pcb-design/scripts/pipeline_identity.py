#!/usr/bin/env python3
"""Versioned semantic and raw identities for declarative pipeline subjects.

Semantic identity is computed only from explicitly typed, parsed values.  Raw
identity is computed independently from exact bytes and optional reproduction
metadata.  This separation is deliberate: reformatting a source file may move
the raw identity without invalidating a review of unchanged design meaning.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = 1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PROJECTION_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
SEMANTIC_TYPES = frozenset({"scalar", "mapping", "sequence", "set"})


class IdentityValidationError(ValueError):
    """An identity projection is ambiguous, untyped, or malformed."""


def _fail(message: str) -> None:
    raise IdentityValidationError(message)


def _json_value(value: Any, where: str = "value") -> Any:
    """Return a detached JSON value, rejecting ambiguous Python objects."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            _fail(f"{where}: non-finite numbers are not canonical JSON")
        return value
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                _fail(f"{where}: mapping keys must be strings")
            result[key] = _json_value(item, f"{where}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [_json_value(item, f"{where}[{index}]")
                for index, item in enumerate(value)]
    _fail(f"{where}: unsupported value type {type(value).__name__}")


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sorted_set(items: Sequence[Any], where: str) -> list[Any]:
    normalized = [_json_value(item, f"{where}[{index}]")
                  for index, item in enumerate(items)]
    encoded = [(_canonical_bytes(item), item) for item in normalized]
    encoded.sort(key=lambda pair: pair[0])
    for index in range(1, len(encoded)):
        if encoded[index - 1][0] == encoded[index][0]:
            _fail(f"{where}: set projection contains a duplicate value")
    return [item for _, item in encoded]


@dataclass(frozen=True)
class SubjectIdentity:
    """The two independent SHA-256 identities carried by a stage result."""

    semantic_sha256: str
    raw_sha256: str

    def __post_init__(self) -> None:
        for name in ("semantic_sha256", "raw_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
                _fail(f"{name}: expected 64 lowercase hexadecimal characters")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SubjectIdentity":
        if not isinstance(value, Mapping):
            _fail("subject: expected a mapping")
        expected = {"semantic_sha256", "raw_sha256"}
        actual = set(value)
        if actual != expected:
            missing = sorted(expected - actual)
            unknown = sorted(actual - expected)
            _fail(f"subject: fields differ (missing={missing}, unknown={unknown})")
        return cls(
            semantic_sha256=value["semantic_sha256"],
            raw_sha256=value["raw_sha256"],
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "semantic_sha256": self.semantic_sha256,
            "raw_sha256": self.raw_sha256,
        }


@dataclass(frozen=True)
class TypedIdentityInput:
    """One named, typed input to both identity projections.

    ``semantic_type`` is explicit so callers must decide whether collection
    order is meaningful. ``sequence`` preserves order; ``set`` sorts and
    rejects duplicates. Mappings always have canonical key ordering.
    ``raw_bytes`` must be the exact source/tool bytes, not decoded text.
    """

    name: str
    semantic_type: str
    semantic_value: Any
    raw_bytes: bytes
    raw_metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or SYMBOL_RE.fullmatch(self.name) is None:
            _fail(f"input name {self.name!r}: expected {SYMBOL_RE.pattern}")
        if self.semantic_type not in SEMANTIC_TYPES:
            _fail(f"{self.name}: semantic_type must be one of "
                  f"{sorted(SEMANTIC_TYPES)}")
        if not isinstance(self.raw_bytes, bytes):
            _fail(f"{self.name}: raw_bytes must be exact bytes")
        metadata = _json_value(self.raw_metadata, f"{self.name}.raw_metadata")
        if not isinstance(metadata, dict):
            _fail(f"{self.name}.raw_metadata: expected a mapping")
        object.__setattr__(self, "raw_metadata", metadata)

        value = self.semantic_value
        if self.semantic_type == "mapping":
            if not isinstance(value, Mapping):
                _fail(f"{self.name}: mapping projection requires a mapping")
            normalized = _json_value(value, f"{self.name}.semantic_value")
        elif self.semantic_type in {"sequence", "set"}:
            if (not isinstance(value, (list, tuple)) or
                    isinstance(value, (str, bytes, bytearray))):
                _fail(f"{self.name}: {self.semantic_type} projection requires "
                      "a list or tuple")
            normalized = (_sorted_set(value, f"{self.name}.semantic_value")
                          if self.semantic_type == "set" else
                          _json_value(value, f"{self.name}.semantic_value"))
        else:
            normalized = _json_value(value, f"{self.name}.semantic_value")
            if isinstance(normalized, (dict, list)):
                _fail(f"{self.name}: scalar projection cannot contain a collection")
        object.__setattr__(self, "semantic_value", normalized)

    def semantic_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.semantic_type,
            "value": self.semantic_value,
        }

    def raw_record(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.semantic_type,
            "sha256": hashlib.sha256(self.raw_bytes).hexdigest(),
            "size": len(self.raw_bytes),
            "metadata": self.raw_metadata,
        }


def subject_identity(
        projection: str,
        version: int,
        inputs: Iterable[TypedIdentityInput],
        *,
        schema: int = SCHEMA,
) -> SubjectIdentity:
    """Hash a named, versioned subject projection.

    Input order is deliberately irrelevant: stable symbolic names provide the
    join key and are sorted before hashing. Collection order is controlled by
    each input's explicit semantic type.
    """
    if schema != SCHEMA or isinstance(schema, bool):
        _fail(f"schema: only schema {SCHEMA} is supported")
    if not isinstance(projection, str) or PROJECTION_RE.fullmatch(projection) is None:
        _fail(f"projection {projection!r}: expected {PROJECTION_RE.pattern}")
    if not isinstance(version, int) or isinstance(version, bool) or version <= 0:
        _fail("version: expected a positive integer")
    material = list(inputs)
    if not material:
        _fail("inputs: identity denominator must be non-zero")
    if any(not isinstance(item, TypedIdentityInput) for item in material):
        _fail("inputs: every item must be a TypedIdentityInput")
    material.sort(key=lambda item: item.name)
    names = [item.name for item in material]
    if len(names) != len(set(names)):
        _fail("inputs: names must be unique")

    prefix = {"schema": schema, "projection": projection, "version": version}
    semantic = {**prefix, "inputs": [item.semantic_record() for item in material]}
    raw = {**prefix, "inputs": [item.raw_record() for item in material]}
    return SubjectIdentity(
        semantic_sha256=hashlib.sha256(_canonical_bytes(semantic)).hexdigest(),
        raw_sha256=hashlib.sha256(_canonical_bytes(raw)).hexdigest(),
    )


__all__ = [
    "IdentityValidationError",
    "SCHEMA",
    "SEMANTIC_TYPES",
    "SubjectIdentity",
    "TypedIdentityInput",
    "subject_identity",
]
