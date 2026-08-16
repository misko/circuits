#!/usr/bin/env python3
"""Strict, shadow-only readiness composition from stage receipts and bundles.

The legacy findings ledger remains maturity authority.  This module computes a
second answer for comparison: every expected stage must have an exact schema-1
``StageResult`` whose subject matches the registry and whose output symbols
reopen through accepted schema-1 artifact bundles.  Missing, unexpected,
stale, malformed, or tampered evidence is never treated as ready.
"""
from __future__ import annotations

import hashlib
import json
import re
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import yaml

from pipeline_contract import (
    APPLICABILITIES,
    ContractValidationError,
    STAGE_ID_RE,
    StageResult,
)
from pipeline_identity import (
    IdentityValidationError,
    SHA256_RE,
    SubjectIdentity,
)


LEVELS = (
    "DRAFT",
    "DESIGN_CLEAN",
    "FIRST_ARTICLE_ORDERABLE",
    "FIRST_ARTICLE_TESTED",
    "PRODUCTION_RELEASED",
)
PROFILE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
MANIFEST_FIELDS = {
    "schema", "run_id", "producer", "producer_version", "subject",
    "started_at", "finished_at", "status", "inputs", "outputs",
}
RECORD_FIELDS = {"sha256", "size"}


class ReadinessValidationError(ValueError):
    """A registry, receipt, or accepted bundle is not admissible evidence."""


def _fail(message: str) -> None:
    raise ReadinessValidationError(message)


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader which refuses duplicate mapping keys."""


def _unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode,
                    deep: bool = False) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError:
            _fail("receipt registry: mapping key is not a scalar")
        if duplicate:
            _fail(f"receipt registry: duplicate YAML key {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _unique_mapping,
)


def _exact_fields(value: Any, expected: set[str], where: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    actual = set(value)
    if actual != expected:
        _fail(
            f"{where}: fields differ (missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)})"
        )


def _safe_relative(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        _fail(f"{where}: expected a non-empty POSIX project-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        _fail(f"{where}: path must not be absolute or contain '.'/'..': {value!r}")
    return path.as_posix()


def _load_json(path: Path, where: str) -> Any:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                _fail(f"{where}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            return json.load(stream, object_pairs_hook=no_duplicates)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"{where}: cannot read JSON: {exc}")


def _timestamp(value: Any, where: str) -> datetime:
    if not isinstance(value, str) or not value:
        _fail(f"{where}: expected a non-empty RFC3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail(f"{where}: invalid RFC3339 timestamp {value!r}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"{where}: timestamp must include a UTC offset")
    return parsed


def _file_record(path: Path, where: str, *, non_empty: bool) -> dict[str, Any]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        _fail(f"{where}: missing file {path}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        _fail(f"{where}: expected a regular non-symlink file: {path}")
    if non_empty and info.st_size == 0:
        _fail(f"{where}: file is empty: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "size": info.st_size}


def _reject_symlink_chain(project: Path, path: Path, where: str) -> None:
    """Require every existing project-relative path component to be real."""

    try:
        relative = path.relative_to(project)
    except ValueError:
        _fail(f"{where}: path escapes project: {path}")
    current = project
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            _fail(f"{where}: symlink path component is inadmissible: {current}")


def _load_stable_json(path: Path, where: str) -> tuple[Any, dict[str, Any]]:
    before = _file_record(path, where, non_empty=True)
    value = _load_json(path, where)
    after = _file_record(path, where, non_empty=True)
    if after != before:
        _fail(f"{where}: bytes moved while evidence was being read")
    return value, before


def _validate_record(value: Any, where: str) -> dict[str, Any]:
    _exact_fields(value, RECORD_FIELDS, where)
    digest = value["sha256"]
    size = value["size"]
    if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
        _fail(f"{where}.sha256: expected 64 lowercase hexadecimal characters")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        _fail(f"{where}.size: expected a non-negative integer")
    return {"sha256": digest, "size": size}


def _validate_records(value: Any, where: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    result: dict[str, dict[str, Any]] = {}
    for name, record in value.items():
        clean = _safe_relative(name, f"{where} key")
        if clean in result:
            _fail(f"{where}: duplicate normalized path {clean!r}")
        result[clean] = _validate_record(record, f"{where}.{clean}")
    return dict(sorted(result.items()))


@dataclass(frozen=True)
class ExpectedStage:
    stage_id: str
    required_for: str
    applicability: str
    bundles: Mapping[str, str]

    @classmethod
    def from_mapping(cls, value: Any, where: str) -> "ExpectedStage":
        _exact_fields(
            value,
            {"stage_id", "required_for", "applicability", "bundles"},
            where,
        )
        stage_id = value["stage_id"]
        if not isinstance(stage_id, str) or STAGE_ID_RE.fullmatch(stage_id) is None:
            _fail(f"{where}.stage_id: invalid stage id {stage_id!r}")
        required_for = value["required_for"]
        if required_for not in LEVELS[1:]:
            _fail(f"{where}.required_for: expected one of {list(LEVELS[1:])}")
        applicability = value["applicability"]
        if applicability not in APPLICABILITIES:
            _fail(f"{where}.applicability: expected one of {sorted(APPLICABILITIES)}")
        raw_bundles = value["bundles"]
        if not isinstance(raw_bundles, Mapping):
            _fail(f"{where}.bundles: expected a mapping")
        bundles: dict[str, str] = {}
        for symbol, path in raw_bundles.items():
            if not isinstance(symbol, str) or SYMBOL_RE.fullmatch(symbol) is None:
                _fail(f"{where}.bundles: invalid output symbol {symbol!r}")
            clean = _safe_relative(path, f"{where}.bundles.{symbol}")
            if PurePosixPath(clean).name != "bundle.json":
                _fail(f"{where}.bundles.{symbol}: expected a bundle.json path")
            bundles[symbol] = clean
        if list(bundles) != sorted(bundles):
            _fail(f"{where}.bundles: symbols must be sorted")
        if applicability == "APPLIES" and not bundles:
            _fail(f"{where}.bundles: APPLIES stage needs an accepted bundle")
        if applicability == "NOT_APPLICABLE" and bundles:
            _fail(f"{where}.bundles: NOT_APPLICABLE stage cannot name bundles")
        return cls(stage_id, required_for, applicability, dict(bundles))


@dataclass(frozen=True)
class ReadinessRegistry:
    profile: str
    target: str
    subject: SubjectIdentity
    receipts_dir: str
    stages: tuple[ExpectedStage, ...]
    schema: int = 1

    @classmethod
    def from_mapping(cls, value: Any) -> "ReadinessRegistry":
        _exact_fields(
            value,
            {"schema", "profile", "target", "subject", "receipts_dir", "stages"},
            "receipt registry",
        )
        if value["schema"] != 1 or isinstance(value["schema"], bool):
            _fail("receipt registry.schema: only schema 1 is supported")
        profile = value["profile"]
        if not isinstance(profile, str) or PROFILE_RE.fullmatch(profile) is None:
            _fail("receipt registry.profile: expected lowercase profile identifier")
        target = value["target"]
        if target not in LEVELS[1:]:
            _fail(f"receipt registry.target: expected one of {list(LEVELS[1:])}")
        try:
            subject = SubjectIdentity.from_mapping(value["subject"])
        except IdentityValidationError as exc:
            _fail(f"receipt registry.subject: {exc}")
        receipts_dir = _safe_relative(value["receipts_dir"], "receipt registry.receipts_dir")
        rows = value["stages"]
        if not isinstance(rows, list) or not rows:
            _fail("receipt registry.stages: expected a non-empty list")
        stages = tuple(
            ExpectedStage.from_mapping(row, f"receipt registry.stages[{index}]")
            for index, row in enumerate(rows)
        )
        ids = [stage.stage_id for stage in stages]
        if ids != sorted(set(ids)):
            _fail("receipt registry.stages: stage ids must be sorted and unique")
        if any(LEVELS.index(stage.required_for) > LEVELS.index(target)
               for stage in stages):
            _fail("receipt registry.stages: a stage is later than registry target")
        for level in LEVELS[1:LEVELS.index(target) + 1]:
            if not any(stage.required_for == level for stage in stages):
                _fail(f"receipt registry.stages: target ladder has no {level} stage")
        return cls(profile, target, subject, receipts_dir, stages)

    @classmethod
    def load(cls, path: Path) -> "ReadinessRegistry":
        try:
            value = yaml.load(
                path.read_text(encoding="utf-8-sig"),
                Loader=_UniqueKeyLoader,
            )
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            _fail(f"receipt registry: cannot read {path}: {exc}")
        return cls.from_mapping(value)


def _validate_bundle(
    project: Path,
    manifest_rel: str,
    receipt: StageResult,
    expected_subject: SubjectIdentity,
) -> dict[str, Any]:
    manifest_path = project.joinpath(*PurePosixPath(manifest_rel).parts)
    _reject_symlink_chain(project, manifest_path, f"bundle {manifest_rel}")
    manifest, manifest_record = _load_stable_json(
        manifest_path, f"bundle {manifest_rel}"
    )
    _exact_fields(manifest, MANIFEST_FIELDS, f"bundle {manifest_rel}")
    if manifest["schema"] != 1 or isinstance(manifest["schema"], bool):
        _fail(f"bundle {manifest_rel}: only schema 1 is supported")
    if manifest["status"] != "PASS":
        _fail(f"bundle {manifest_rel}: status must be PASS")
    if manifest["run_id"] != receipt.run_id:
        _fail(f"bundle {manifest_rel}: run_id does not match stage receipt")
    if not RUN_ID_RE.fullmatch(str(manifest["run_id"])):
        _fail(f"bundle {manifest_rel}: invalid run_id")
    for name in ("producer", "producer_version"):
        if not isinstance(manifest[name], str) or not manifest[name].strip():
            _fail(f"bundle {manifest_rel}: {name} must be non-empty")
    try:
        bundle_subject = SubjectIdentity.from_mapping(manifest["subject"])
    except IdentityValidationError as exc:
        _fail(f"bundle {manifest_rel}.subject: {exc}")
    if bundle_subject != expected_subject:
        _fail(f"bundle {manifest_rel}: subject is stale for current registry")

    receipt_started = _timestamp(receipt.started_at, "receipt.started_at")
    receipt_finished = _timestamp(receipt.finished_at, "receipt.finished_at")
    bundle_started = _timestamp(manifest["started_at"], f"bundle {manifest_rel}.started_at")
    bundle_finished = _timestamp(manifest["finished_at"], f"bundle {manifest_rel}.finished_at")
    if not receipt_started <= bundle_started <= bundle_finished <= receipt_finished:
        _fail(f"bundle {manifest_rel}: timing is outside its stage receipt")

    inputs = _validate_records(manifest["inputs"], f"bundle {manifest_rel}.inputs")
    if not inputs:
        _fail(f"bundle {manifest_rel}: accepted bundle has no inputs")
    outputs = _validate_records(manifest["outputs"], f"bundle {manifest_rel}.outputs")
    if not outputs:
        _fail(f"bundle {manifest_rel}: accepted bundle has no outputs")
    bundle_dir = manifest_path.parent
    actual_files: set[str] = set()
    for path in bundle_dir.rglob("*"):
        relative = path.relative_to(bundle_dir).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            _fail(f"bundle {manifest_rel}: symlink is not admissible: {relative}")
        if stat.S_ISREG(info.st_mode):
            actual_files.add(relative)
        elif not stat.S_ISDIR(info.st_mode):
            _fail(f"bundle {manifest_rel}: unsupported file type: {relative}")
    expected_files = set(outputs) | {"bundle.json"}
    if actual_files != expected_files:
        _fail(
            f"bundle {manifest_rel}: file set differs "
            f"(missing={sorted(expected_files - actual_files)}, "
            f"unknown={sorted(actual_files - expected_files)})"
        )
    for name, record in outputs.items():
        actual = _file_record(bundle_dir.joinpath(*PurePosixPath(name).parts),
                              f"bundle {manifest_rel} output {name}", non_empty=True)
        if actual != record:
            _fail(f"bundle {manifest_rel}: output hash/size changed: {name}")
    if _file_record(manifest_path, f"bundle {manifest_rel}", non_empty=True) != manifest_record:
        _fail(f"bundle {manifest_rel}: manifest moved during readiness audit")
    # Include the exact manifest bytes in the shadow audit output so downstream
    # comparisons cannot mistake a later manifest rewrite for the same check.
    return {
        "path": manifest_rel,
        "manifest_sha256": manifest_record["sha256"],
        "outputs": sorted(outputs),
    }


def evaluate(project: Path, registry_path: Path) -> dict[str, Any]:
    """Return a deterministic shadow verdict; evidence defects become FAIL."""

    project = project.resolve()
    registry_path = registry_path if registry_path.is_absolute() else project / registry_path
    try:
        registry_relative = registry_path.relative_to(project).as_posix()
    except ValueError:
        _fail(f"receipt registry must be inside project: {registry_path}")
    if any(part in ("", ".", "..")
           for part in PurePosixPath(registry_relative).parts):
        _fail(f"receipt registry path is not canonical: {registry_relative!r}")
    _reject_symlink_chain(project, registry_path, "receipt registry")
    resolved_registry = registry_path.resolve()
    try:
        resolved_registry.relative_to(project)
    except ValueError:
        _fail(f"receipt registry resolves outside project: {registry_path}")
    registry_path = resolved_registry
    registry_record = _file_record(registry_path, "receipt registry", non_empty=True)
    registry = ReadinessRegistry.load(registry_path)
    if _file_record(registry_path, "receipt registry", non_empty=True) != registry_record:
        _fail("receipt registry: bytes moved while registry was being read")
    receipt_dir = project.joinpath(*PurePosixPath(registry.receipts_dir).parts)
    expected_names = {f"{stage.stage_id}.json" for stage in registry.stages}
    findings: list[str] = []
    actual_names: set[str] = set()
    _reject_symlink_chain(project, receipt_dir, "receipt directory")
    if not receipt_dir.exists():
        findings.append(f"missing receipt directory: {registry.receipts_dir}")
    elif receipt_dir.is_symlink() or not receipt_dir.is_dir():
        findings.append(f"receipt directory is not a real directory: {registry.receipts_dir}")
    else:
        for path in receipt_dir.iterdir():
            if path.is_symlink() or not path.is_file():
                findings.append(f"unknown receipt entry: {path.name}")
            else:
                actual_names.add(path.name)
        for name in sorted(actual_names - expected_names):
            findings.append(f"unknown receipt: {registry.receipts_dir}/{name}")
    for name in sorted(expected_names - actual_names):
        findings.append(f"missing receipt: {registry.receipts_dir}/{name}")

    stage_rows: list[dict[str, Any]] = []
    satisfied = 0
    not_applicable = 0
    for expected in registry.stages:
        stage_findings: list[str] = []
        bundles: list[dict[str, Any]] = []
        receipt_sha256: str | None = None
        receipt_rel = f"{registry.receipts_dir}/{expected.stage_id}.json"
        receipt_path = project.joinpath(*PurePosixPath(receipt_rel).parts)
        receipt: StageResult | None = None
        if receipt_path.name in actual_names:
            try:
                raw, receipt_record = _load_stable_json(
                    receipt_path, f"receipt {expected.stage_id}"
                )
                receipt_sha256 = receipt_record["sha256"]
                receipt = StageResult.from_mapping(raw)
                if receipt.stage_id != expected.stage_id:
                    _fail(
                        f"receipt {expected.stage_id}: declares unknown/mismatched "
                        f"stage {receipt.stage_id}"
                    )
                if receipt.subject != registry.subject:
                    _fail(f"receipt {expected.stage_id}: subject is stale for current registry")
                if receipt.applicability != expected.applicability:
                    _fail(
                        f"receipt {expected.stage_id}: applicability "
                        f"{receipt.applicability} disagrees with profile expectation "
                        f"{expected.applicability}"
                    )
                if expected.applicability == "APPLIES" and receipt.status != "PASS":
                    _fail(f"receipt {expected.stage_id}: applicable stage did not PASS")
                if (expected.applicability == "NOT_APPLICABLE" and
                        receipt.status != "NOT_APPLICABLE"):
                    _fail(f"receipt {expected.stage_id}: expected NOT_APPLICABLE")
                if tuple(receipt.outputs) != tuple(expected.bundles):
                    _fail(
                        f"receipt {expected.stage_id}: output symbols disagree "
                        f"(receipt={list(receipt.outputs)}, "
                        f"expected={sorted(expected.bundles)})"
                    )
                for symbol, path in expected.bundles.items():
                    audit = _validate_bundle(project, path, receipt, registry.subject)
                    bundles.append({"symbol": symbol, **audit})
                if _file_record(
                    receipt_path, f"receipt {expected.stage_id}", non_empty=True
                ) != receipt_record:
                    _fail(f"receipt {expected.stage_id}: bytes moved during readiness audit")
            except (ReadinessValidationError, ContractValidationError,
                    IdentityValidationError, OSError, TypeError, ValueError) as exc:
                stage_findings.append(str(exc))
        else:
            stage_findings.append(f"missing receipt: {receipt_rel}")
        admissible = not stage_findings and receipt is not None
        if admissible:
            satisfied += 1
            not_applicable += expected.applicability == "NOT_APPLICABLE"
        findings.extend(stage_findings)
        stage_rows.append({
            "stage_id": expected.stage_id,
            "required_for": expected.required_for,
            "expected_applicability": expected.applicability,
            "receipt": receipt_rel,
            "receipt_sha256": receipt_sha256,
            "admissible": admissible,
            "bundles": bundles,
            "findings": stage_findings,
        })

    achieved = "DRAFT"
    evaluated: list[dict[str, Any]] = []
    for level in LEVELS[1:LEVELS.index(registry.target) + 1]:
        required = [row for row in stage_rows
                    if LEVELS.index(row["required_for"]) <= LEVELS.index(level)]
        own = [row for row in stage_rows if row["required_for"] == level]
        failed = [row["stage_id"] for row in required if not row["admissible"]]
        ok = bool(own) and not failed
        evaluated.append({"level": level, "satisfied": ok, "failed_stages": failed})
        if not ok:
            break
        achieved = level
    ready = achieved == registry.target and not findings
    if _file_record(registry_path, "receipt registry", non_empty=True) != registry_record:
        _fail("receipt registry: bytes moved during readiness audit")
    return {
        "schema": 1,
        "mode": "shadow",
        "authority": "legacy-findings-ledger",
        "profile": registry.profile,
        "target": registry.target,
        "registry": registry_relative,
        "registry_sha256": registry_record["sha256"],
        "subject": registry.subject.to_mapping(),
        "status": "PASS" if ready else "FAIL",
        "derived_maturity": achieved,
        "coverage": {
            "satisfied": satisfied,
            "total": len(registry.stages),
            "not_applicable": not_applicable,
        },
        "evaluated": evaluated,
        "stages": stage_rows,
        "findings": sorted(set(findings)),
    }


__all__ = [
    "ExpectedStage",
    "LEVELS",
    "ReadinessRegistry",
    "ReadinessValidationError",
    "evaluate",
]
