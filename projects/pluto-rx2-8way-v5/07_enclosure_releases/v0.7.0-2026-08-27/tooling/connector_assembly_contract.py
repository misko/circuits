#!/usr/bin/env python3
"""Validate and compile the project connector-assembly service contract.

Exit 0 means either a non-vacuous operated-connector contract with no
represented unknown evidence, or an exact evidence-backed N-A decision.
Exit 2 means the schema is valid but one or more facts remain explicitly
unknown.  Exit 1 means the schema, path, identity, or cross-reference is
invalid.  No default connector dimensions or service allowances are supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[3]
RECEIPT_KIND = "connector-assembly-contract-receipt"
RECEIPT_SCHEMA = 1
DEFAULT_CONTRACT = Path("03_src/rules/connector_assemblies.yaml")
DEFAULT_OUTPUT = Path("06_build/verification/connector_assembly_contract.json")

_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_REF = re.compile(r"^[A-Z][A-Z0-9_-]*[0-9][A-Z0-9_-]*$")
_GRADES = frozenset({"exact", "conservative", "unknown"})
_OPERATION_KINDS = frozenset({
    "mate", "unmate", "hand_start", "tighten", "loosen", "latch",
    "unlatch", "insert", "remove", "service", "cable_bend",
    "enclosure_install", "enclosure_remove", "other",
})
_GROUP_STATES = frozenset({
    "all_connected", "all_mated", "installation", "operation", "service",
})
_AXIAL_DIRECTIONS = frozenset({
    "along_mating_axis", "opposite_mating_axis", "none",
})
_TOLERANCE_EFFECTS = frozenset({
    "exposure_setback", "service_radial_growth", "service_axial_growth",
    "other",
})
_MODEL_SOURCE_KINDS = frozenset({
    "manufacturer-3d-model", "measured-3d-model", "native-3d-model",
    "qualified-tool-3d-model",
})
_ORIENTATION_SOURCE_KINDS = frozenset({
    "connector-orientation-receipt", "placement-contract",
    "realized-orientation-measurement",
})
_APPLICABILITY_SOURCE_KINDS = frozenset({"connector-applicability-record"})
_NO_METHOD_VALUES = frozenset({
    "n/a", "na", "none", "not required", "not-required", "not_required",
    "unknown",
})


class ContractError(ValueError):
    """The authored contract cannot safely become executable authority."""


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _StrictLoader, node: yaml.Node,
                       deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ContractError("YAML mapping keys must be scalar") from exc
        if duplicate:
            raise ContractError(f"duplicate YAML key {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _exact_mapping(value: Any, keys: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{where}: expected mapping")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys, key=str)
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"unknown {extra}")
        raise ContractError(f"{where}: exact schema violation ({'; '.join(details)})")
    if not all(isinstance(key, str) for key in actual):
        raise ContractError(f"{where}: keys must be strings")
    return value


def _list(value: Any, where: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{where}: expected list")
    if nonempty and not value:
        raise ContractError(f"{where}: expected non-empty list")
    return value


def _string(value: Any, where: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        suffix = " or null" if nullable else ""
        raise ContractError(f"{where}: expected non-empty string{suffix}")
    if value != value.strip():
        raise ContractError(f"{where}: leading/trailing whitespace is forbidden")
    return value


def _identifier(value: Any, where: str) -> str:
    result = _string(value, where)
    assert result is not None
    if not _ID.fullmatch(result):
        raise ContractError(f"{where}: expected lowercase stable identifier")
    return result


def _ref(value: Any, where: str) -> str:
    result = _string(value, where)
    assert result is not None
    if not _REF.fullmatch(result):
        raise ContractError(f"{where}: expected populated connector reference (for example J1)")
    return result


def _boolean(value: Any, where: str, *, nullable: bool = False) -> bool | None:
    if value is None and nullable:
        return None
    if not isinstance(value, bool):
        suffix = " or null" if nullable else ""
        raise ContractError(f"{where}: expected boolean{suffix}")
    return value


def _integer(value: Any, where: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ContractError(f"{where}: expected integer")
    if minimum is not None and value < minimum:
        raise ContractError(f"{where}: expected >= {minimum}")
    return value


def _number(value: Any, where: str, *, nullable: bool = False,
            minimum: float | None = None, positive: bool = False) -> float | None:
    if value is None and nullable:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        suffix = " or null" if nullable else ""
        raise ContractError(f"{where}: expected finite number{suffix}")
    result = float(value)
    if not math.isfinite(result):
        raise ContractError(f"{where}: expected finite number")
    if positive and result <= 0:
        raise ContractError(f"{where}: expected > 0")
    if minimum is not None and result < minimum:
        raise ContractError(f"{where}: expected >= {minimum}")
    return result


def _unique_sorted_strings(value: Any, where: str, *, ids: bool = False,
                           nonempty: bool = False) -> list[str]:
    items = _list(value, where, nonempty=nonempty)
    result: list[str] = []
    for index, item in enumerate(items):
        result.append(_identifier(item, f"{where}[{index}]") if ids
                      else _string(item, f"{where}[{index}]") or "")
    if len(result) != len(set(result)):
        raise ContractError(f"{where}: duplicate values are forbidden")
    return sorted(result)


def _unit_vector(value: Any, where: str) -> list[float]:
    values = _list(value, where)
    if len(values) != 3:
        raise ContractError(f"{where}: expected [x, y, z]")
    result = [_number(item, f"{where}[{index}]") for index, item in enumerate(values)]
    assert all(item is not None for item in result)
    vector = [float(item) for item in result]
    norm = math.sqrt(sum(item * item for item in vector))
    if abs(norm - 1.0) > 1e-6:
        raise ContractError(f"{where}: expected a unit vector, norm={norm:.9g}")
    return vector


def _envelope(value: Any, where: str, *, nullable: bool = True) -> dict[str, float] | None:
    if value is None and nullable:
        return None
    item = _exact_mapping(value, {"x", "y", "z"}, where)
    # Connector-local axes: x is axial along the mating axis, y is lateral,
    # and z is PCB-normal/vertical.  No board-global box is inferred here.
    return {
        axis: float(_number(item[axis], f"{where}.{axis}", positive=True))
        for axis in ("x", "y", "z")
    }


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _reject_symlink_components(path: Path, where: str, *, allow_missing_tail: bool = False) -> None:
    absolute = _absolute_lexical(path)
    parts = absolute.parts
    current = Path(parts[0])
    for part in parts[1:]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            if allow_missing_tail:
                return
            raise ContractError(f"{where}: path does not exist: {current}")
        except OSError as exc:
            raise ContractError(f"{where}: cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise ContractError(f"{where}: symlink path component is forbidden: {current}")


def _project_directory(path: Path) -> Path:
    result = _absolute_lexical(path)
    _reject_symlink_components(result, "project")
    try:
        mode = result.lstat().st_mode
    except OSError as exc:  # pragma: no cover - component walk already reports it
        raise ContractError(f"project: cannot inspect {result}: {exc}") from exc
    if not stat.S_ISDIR(mode):
        raise ContractError(f"project: expected ordinary directory: {result}")
    return result


def _project_path(project: Path, path: Path, where: str) -> tuple[Path, str]:
    candidate = _absolute_lexical(path if path.is_absolute() else project / path)
    try:
        relative = candidate.relative_to(project).as_posix()
    except ValueError as exc:
        raise ContractError(f"{where}: path must remain inside project") from exc
    if relative == "." or relative.startswith("../"):
        raise ContractError(f"{where}: expected project-relative file path")
    return candidate, relative


def _ordinary_file(project: Path, path: Path, where: str) -> tuple[dict[str, Any], bytes]:
    candidate, relative = _project_path(project, path, where)
    _reject_symlink_components(candidate, where)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(candidate, flags)
    except OSError as exc:
        raise ContractError(f"{where}: cannot open ordinary file {relative}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ContractError(f"{where}: expected ordinary file: {relative}")
        if before.st_nlink != 1:
            raise ContractError(f"{where}: hard-linked files are not accepted: {relative}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        identity = lambda row: (
            row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns,
            row.st_ctime_ns, row.st_nlink)
        if identity(before) != identity(after):
            raise ContractError(f"{where}: file changed while being read: {relative}")
        data = b"".join(chunks)
        if len(data) != before.st_size:
            raise ContractError(f"{where}: short read for {relative}")
    finally:
        os.close(descriptor)
    try:
        named = candidate.lstat()
    except OSError as exc:
        raise ContractError(f"{where}: cannot re-inspect {relative}: {exc}") from exc
    if stat.S_ISLNK(named.st_mode) or (
            named.st_dev, named.st_ino, named.st_size, named.st_mtime_ns,
            named.st_ctime_ns, named.st_nlink) != identity(after):
        raise ContractError(f"{where}: path changed while being read: {relative}")
    return {"path": relative, "sha256": _digest(data), "size": len(data)}, data


def _compiler_binding() -> dict[str, Any]:
    binding, _ = _ordinary_file(REPO_ROOT, SCRIPT_PATH, "compiler")
    return binding


class _Compiler:
    def __init__(self, project: Path, contract_path: Path) -> None:
        self.project = project
        self.contract_binding, raw = _ordinary_file(
            project, contract_path, "contract")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ContractError(f"contract: expected UTF-8: {exc}") from exc
        try:
            self.document = yaml.load(text, Loader=_StrictLoader)
        except ContractError:
            raise
        except yaml.YAMLError as exc:
            raise ContractError(f"contract: invalid YAML: {exc}") from exc
        self.sources: dict[str, dict[str, Any]] = {}
        self.source_declarations: list[dict[str, str]] = []
        self.used_sources: set[str] = set()
        self.unknowns: list[dict[str, str]] = []
        self.evidence_counts = {grade: 0 for grade in sorted(_GRADES)}

    def source_id(self, value: Any, where: str, *, nullable: bool = False) -> str | None:
        if value is None and nullable:
            return None
        source_id = _identifier(value, where)
        if source_id not in self.sources:
            raise ContractError(f"{where}: unknown evidence source {source_id!r}")
        self.used_sources.add(source_id)
        return source_id

    def typed_source_id(self, value: Any, where: str, *,
                        allowed_kinds: frozenset[str], role: str,
                        nullable: bool = False) -> str | None:
        """Resolve a source and require an explicit artifact role by kind."""
        source_id = self.source_id(value, where, nullable=nullable)
        if source_id is None:
            return None
        kind = self.sources[source_id]["kind"]
        if kind not in allowed_kinds:
            raise ContractError(
                f"{where}: evidence source {source_id!r} kind {kind!r} is not "
                f"an allowed {role}; expected one of {sorted(allowed_kinds)}")
        return source_id

    def evidence(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {"grade", "source_ids", "rationale"}, where)
        grade = _string(item["grade"], f"{where}.grade")
        assert grade is not None
        if grade not in _GRADES:
            raise ContractError(f"{where}.grade: expected exact|conservative|unknown")
        source_ids = _unique_sorted_strings(
            item["source_ids"], f"{where}.source_ids", ids=True)
        rationale = _string(item["rationale"], f"{where}.rationale")
        assert rationale is not None
        for source_id in source_ids:
            self.source_id(source_id, f"{where}.source_ids")
        if grade in {"exact", "conservative"} and not source_ids:
            raise ContractError(f"{where}: {grade} evidence requires source_ids")
        if grade == "unknown":
            self.unknowns.append({"path": where, "rationale": rationale})
        self.evidence_counts[grade] += 1
        return {"grade": grade, "source_ids": source_ids, "rationale": rationale}

    @staticmethod
    def _require_known_fields(section: Mapping[str, Any], evidence: Mapping[str, Any],
                              names: Sequence[str], where: str) -> None:
        if evidence["grade"] == "unknown":
            return
        missing = [name for name in names if section[name] is None]
        if missing:
            raise ContractError(
                f"{where}: {evidence['grade']} evidence has unknown fields {missing}")

    def _sources(self, value: Any) -> None:
        rows = _list(value, "evidence_sources")
        for index, raw in enumerate(rows):
            where = f"evidence_sources[{index}]"
            item = _exact_mapping(raw, {"id", "kind", "path"}, where)
            source_id = _identifier(item["id"], f"{where}.id")
            if source_id in self.sources:
                raise ContractError(f"{where}.id: duplicate source {source_id!r}")
            kind = _identifier(item["kind"], f"{where}.kind")
            path_text = _string(item["path"], f"{where}.path")
            assert path_text is not None
            binding, _ = _ordinary_file(self.project, Path(path_text), where)
            binding = {"id": source_id, "kind": kind, **binding}
            self.sources[source_id] = binding
            self.source_declarations.append({
                "id": source_id, "kind": kind, "path": binding["path"],
            })
        self.source_declarations.sort(key=lambda row: row["id"])

    def _applicability(self, value: Any) -> dict[str, Any]:
        where = "applicability"
        item = _exact_mapping(value, {"operated", "evidence"}, where)
        evidence = self.evidence(item["evidence"], f"{where}.evidence")
        operated = _boolean(item["operated"], f"{where}.operated")
        assert operated is not None
        if not operated and evidence["grade"] != "exact":
            raise ContractError(
                "applicability: operated=false requires exact evidence")
        for source_id in evidence["source_ids"]:
            kind = self.sources[source_id]["kind"]
            if kind not in _APPLICABILITY_SOURCE_KINDS:
                raise ContractError(
                    f"applicability.evidence.source_ids: evidence source "
                    f"{source_id!r} kind {kind!r} is not an allowed connector "
                    "applicability artifact; expected "
                    f"{sorted(_APPLICABILITY_SOURCE_KINDS)}")
        return {"operated": operated, "evidence": evidence}

    def _receptacle(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "manufacturer", "mpn", "mounting_method", "model_source_id",
            "body_envelope_mm", "evidence",
        }, where)
        result = {
            "manufacturer": _string(item["manufacturer"], f"{where}.manufacturer", nullable=True),
            "mpn": _string(item["mpn"], f"{where}.mpn", nullable=True),
            "mounting_method": _string(item["mounting_method"], f"{where}.mounting_method", nullable=True),
            "model_source_id": self.typed_source_id(
                item["model_source_id"], f"{where}.model_source_id",
                allowed_kinds=_MODEL_SOURCE_KINDS, role="3D/model artifact",
                nullable=True),
            "body_envelope_mm": _envelope(item["body_envelope_mm"], f"{where}.body_envelope_mm"),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"],
                                   ("manufacturer", "mpn", "mounting_method"), where)
        if result["evidence"]["grade"] != "unknown" and not (
                result["model_source_id"] or result["body_envelope_mm"]):
            raise ContractError(f"{where}: known receptacle needs exact model or body envelope")
        if result["model_source_id"] and result["model_source_id"] not in result["evidence"]["source_ids"]:
            raise ContractError(f"{where}: model_source_id must appear in evidence.source_ids")
        return result

    def _mate(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "manufacturer", "mpn", "part_kind", "model_source_id",
            "body_envelope_mm", "evidence",
        }, where)
        result = {
            "manufacturer": _string(item["manufacturer"], f"{where}.manufacturer", nullable=True),
            "mpn": _string(item["mpn"], f"{where}.mpn", nullable=True),
            "part_kind": _string(item["part_kind"], f"{where}.part_kind", nullable=True),
            "model_source_id": self.typed_source_id(
                item["model_source_id"], f"{where}.model_source_id",
                allowed_kinds=_MODEL_SOURCE_KINDS, role="3D/model artifact",
                nullable=True),
            "body_envelope_mm": _envelope(item["body_envelope_mm"], f"{where}.body_envelope_mm"),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"],
                                   ("manufacturer", "mpn", "part_kind"), where)
        if result["evidence"]["grade"] != "unknown" and not (
                result["model_source_id"] or result["body_envelope_mm"]):
            raise ContractError(f"{where}: known mate needs exact model or body envelope")
        if result["model_source_id"] and result["model_source_id"] not in result["evidence"]["source_ids"]:
            raise ContractError(f"{where}: model_source_id must appear in evidence.source_ids")
        return result

    def _interface(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "mating_plane_offset_mm", "minimum_exposure_mm",
            "exposure_setback_allowance_mm", "minimum_service_clearance_mm",
            "orientation_source_id", "evidence",
        }, where)
        result = {
            "mating_plane_offset_mm": _number(item["mating_plane_offset_mm"], f"{where}.mating_plane_offset_mm", nullable=True),
            "minimum_exposure_mm": _number(
                item["minimum_exposure_mm"],
                f"{where}.minimum_exposure_mm", nullable=True, minimum=0),
            "exposure_setback_allowance_mm": _number(item["exposure_setback_allowance_mm"], f"{where}.exposure_setback_allowance_mm", nullable=True, minimum=0),
            "minimum_service_clearance_mm": _number(item["minimum_service_clearance_mm"], f"{where}.minimum_service_clearance_mm", nullable=True, minimum=0),
            "orientation_source_id": self.typed_source_id(
                item["orientation_source_id"], f"{where}.orientation_source_id",
                allowed_kinds=_ORIENTATION_SOURCE_KINDS,
                role="realized orientation/placement artifact", nullable=True),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(
            result, result["evidence"],
            ("mating_plane_offset_mm", "minimum_exposure_mm",
             "exposure_setback_allowance_mm", "minimum_service_clearance_mm"),
            where,
        )
        if (result["evidence"]["grade"] != "unknown" and
                result["orientation_source_id"] is None):
            raise ContractError(
                f"{where}: known interface requires orientation_source_id")
        if result["orientation_source_id"] and result["orientation_source_id"] not in result["evidence"]["source_ids"]:
            raise ContractError(f"{where}: orientation_source_id must appear in evidence.source_ids")
        return result

    def _grip(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "kind", "across_flats_mm", "outer_diameter_mm", "axial_length_mm",
            "evidence",
        }, where)
        result = {
            "kind": _string(item["kind"], f"{where}.kind", nullable=True),
            "across_flats_mm": _number(item["across_flats_mm"], f"{where}.across_flats_mm", nullable=True, positive=True),
            "outer_diameter_mm": _number(item["outer_diameter_mm"], f"{where}.outer_diameter_mm", nullable=True, positive=True),
            "axial_length_mm": _number(item["axial_length_mm"], f"{where}.axial_length_mm", nullable=True, positive=True),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"], ("kind",), where)
        if result["evidence"]["grade"] != "unknown" and result["kind"] != "none":
            if result["axial_length_mm"] is None or (
                    result["across_flats_mm"] is None and result["outer_diameter_mm"] is None):
                raise ContractError(f"{where}: known grip needs axial length and flats or diameter")
        return result

    def _fastening(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "method", "thread_designation", "final_tightening", "evidence",
        }, where)
        result = {
            "method": _string(item["method"], f"{where}.method", nullable=True),
            "thread_designation": _string(item["thread_designation"], f"{where}.thread_designation", nullable=True),
            "final_tightening": _string(item["final_tightening"], f"{where}.final_tightening", nullable=True),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"],
                                   ("method", "final_tightening"), where)
        if (result["evidence"]["grade"] != "unknown" and
                "thread" in result["method"].lower() and
                result["thread_designation"] is None):
            raise ContractError(
                f"{where}: threaded fastening requires thread_designation")
        return result

    def _tool(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "kind", "identifier", "model_source_id", "head_envelope_mm",
            "approach", "effective_sweep_radius_mm", "counter_tool_required",
            "evidence",
        }, where)
        approach = _string(item["approach"], f"{where}.approach", nullable=True)
        if approach is not None and approach not in _AXIAL_DIRECTIONS:
            raise ContractError(f"{where}.approach: expected along_mating_axis|opposite_mating_axis|none")
        result = {
            "kind": _string(item["kind"], f"{where}.kind", nullable=True),
            "identifier": _string(item["identifier"], f"{where}.identifier", nullable=True),
            "model_source_id": self.typed_source_id(
                item["model_source_id"], f"{where}.model_source_id",
                allowed_kinds=_MODEL_SOURCE_KINDS, role="3D/model artifact",
                nullable=True),
            "head_envelope_mm": _envelope(item["head_envelope_mm"], f"{where}.head_envelope_mm"),
            "approach": approach,
            "effective_sweep_radius_mm": _number(item["effective_sweep_radius_mm"], f"{where}.effective_sweep_radius_mm", nullable=True, minimum=0),
            "counter_tool_required": _boolean(
                item["counter_tool_required"],
                f"{where}.counter_tool_required", nullable=True),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(
            result, result["evidence"],
            ("kind", "approach", "counter_tool_required"), where)
        if result["evidence"]["grade"] != "unknown" and result["kind"] != "none":
            self._require_known_fields(result, result["evidence"],
                                       ("identifier", "effective_sweep_radius_mm"), where)
            if not (result["model_source_id"] or result["head_envelope_mm"]):
                raise ContractError(f"{where}: known tool needs exact model or head envelope")
        if result["model_source_id"] and result["model_source_id"] not in result["evidence"]["source_ids"]:
            raise ContractError(f"{where}: model_source_id must appear in evidence.source_ids")
        return result

    def _torque(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "required", "minimum_nm", "maximum_nm", "evidence",
        }, where)
        result = {
            "required": _boolean(item["required"], f"{where}.required", nullable=True),
            "minimum_nm": _number(item["minimum_nm"], f"{where}.minimum_nm", nullable=True, minimum=0),
            "maximum_nm": _number(item["maximum_nm"], f"{where}.maximum_nm", nullable=True, minimum=0),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"], ("required",), where)
        if result["evidence"]["grade"] != "unknown":
            if result["required"]:
                self._require_known_fields(result, result["evidence"],
                                           ("minimum_nm", "maximum_nm"), where)
                if result["minimum_nm"] > result["maximum_nm"]:
                    raise ContractError(f"{where}: minimum_nm exceeds maximum_nm")
            elif result["minimum_nm"] is not None or result["maximum_nm"] is not None:
                raise ContractError(f"{where}: non-required torque must not declare a range")
        return result

    def _reaction(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {"method", "load_path", "evidence"}, where)
        result = {
            "method": _string(item["method"], f"{where}.method", nullable=True),
            "load_path": _string(item["load_path"], f"{where}.load_path", nullable=True),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"],
                                   ("method", "load_path"), where)
        return result

    def _cable(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "kind", "manufacturer", "mpn", "outer_diameter_mm",
            "straight_run_mm", "minimum_bend_radius_mm", "exit", "evidence",
        }, where)
        exit_direction = _string(item["exit"], f"{where}.exit", nullable=True)
        if exit_direction is not None and exit_direction not in _AXIAL_DIRECTIONS:
            raise ContractError(f"{where}.exit: expected along_mating_axis|opposite_mating_axis|none")
        result = {
            "kind": _string(item["kind"], f"{where}.kind", nullable=True),
            "manufacturer": _string(item["manufacturer"], f"{where}.manufacturer", nullable=True),
            "mpn": _string(item["mpn"], f"{where}.mpn", nullable=True),
            "outer_diameter_mm": _number(item["outer_diameter_mm"], f"{where}.outer_diameter_mm", nullable=True, positive=True),
            "straight_run_mm": _number(item["straight_run_mm"], f"{where}.straight_run_mm", nullable=True, minimum=0),
            "minimum_bend_radius_mm": _number(item["minimum_bend_radius_mm"], f"{where}.minimum_bend_radius_mm", nullable=True, minimum=0),
            "exit": exit_direction,
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"], ("kind", "exit"), where)
        if result["evidence"]["grade"] != "unknown" and result["kind"] != "none":
            self._require_known_fields(
                result, result["evidence"],
                ("manufacturer", "mpn", "outer_diameter_mm", "straight_run_mm",
                 "minimum_bend_radius_mm"), where,
            )
        return result

    def _operation(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "id", "sequence", "kind", "required", "with_neighbors_populated",
            "start_state", "end_state", "evidence",
        }, where)
        kind = _string(item["kind"], f"{where}.kind")
        assert kind is not None
        if kind not in _OPERATION_KINDS:
            raise ContractError(f"{where}.kind: unsupported operation {kind!r}")
        evidence = self.evidence(item["evidence"], f"{where}.evidence")
        result = {
            "id": _identifier(item["id"], f"{where}.id"),
            "sequence": _integer(item["sequence"], f"{where}.sequence", minimum=1),
            "kind": kind,
            "required": _boolean(item["required"], f"{where}.required", nullable=True),
            "with_neighbors_populated": _boolean(
                item["with_neighbors_populated"],
                f"{where}.with_neighbors_populated", nullable=True),
            "start_state": _string(item["start_state"], f"{where}.start_state"),
            "end_state": _string(item["end_state"], f"{where}.end_state"),
            "evidence": evidence,
        }
        self._require_known_fields(
            result, evidence, ("required", "with_neighbors_populated"), where)
        return result

    def _tolerance(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "id", "applies_to", "effect", "minus_mm", "plus_mm", "evidence",
        }, where)
        effect = _string(item["effect"], f"{where}.effect")
        assert effect is not None
        if effect not in _TOLERANCE_EFFECTS:
            raise ContractError(
                f"{where}.effect: expected one of {sorted(_TOLERANCE_EFFECTS)}")
        result = {
            "id": _identifier(item["id"], f"{where}.id"),
            "applies_to": _string(item["applies_to"], f"{where}.applies_to"),
            "effect": effect,
            "minus_mm": _number(item["minus_mm"], f"{where}.minus_mm", nullable=True, minimum=0),
            "plus_mm": _number(item["plus_mm"], f"{where}.plus_mm", nullable=True, minimum=0),
            "evidence": self.evidence(item["evidence"], f"{where}.evidence"),
        }
        self._require_known_fields(result, result["evidence"],
                                   ("minus_mm", "plus_mm"), where)
        return result

    def _assembly(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "id", "instances", "receptacle", "mate", "interface", "grip",
            "fastening", "tool", "torque", "reaction", "cable", "operations",
            "tolerances",
        }, where)
        instances: list[dict[str, Any]] = []
        for index, raw in enumerate(_list(item["instances"], f"{where}.instances", nonempty=True)):
            path = f"{where}.instances[{index}]"
            instance = _exact_mapping(
                raw, {"ref", "mating_axis_board", "simultaneous_group_ids"}, path)
            instances.append({
                "ref": _ref(instance["ref"], f"{path}.ref"),
                "mating_axis_board": _unit_vector(
                    instance["mating_axis_board"], f"{path}.mating_axis_board"),
                "simultaneous_group_ids": _unique_sorted_strings(
                    instance["simultaneous_group_ids"],
                    f"{path}.simultaneous_group_ids", ids=True, nonempty=True),
            })
        refs = [row["ref"] for row in instances]
        if len(refs) != len(set(refs)):
            raise ContractError(f"{where}.instances: duplicate refs")

        operations = [
            self._operation(raw, f"{where}.operations[{index}]")
            for index, raw in enumerate(_list(
                item["operations"], f"{where}.operations", nonempty=True))
        ]
        if len({row["id"] for row in operations}) != len(operations):
            raise ContractError(f"{where}.operations: duplicate ids")
        sequences = [row["sequence"] for row in operations]
        if len(set(sequences)) != len(sequences):
            raise ContractError(f"{where}.operations: duplicate sequence values")
        operations.sort(key=lambda row: (row["sequence"], row["id"]))
        expected_sequences = list(range(1, len(operations) + 1))
        if [row["sequence"] for row in operations] != expected_sequences:
            raise ContractError(
                f"{where}.operations: sequence must be contiguous from 1; "
                f"expected {expected_sequences}")
        for prior, following in zip(operations, operations[1:]):
            if prior["end_state"] != following["start_state"]:
                raise ContractError(
                    f"{where}.operations: state discontinuity between "
                    f"{prior['id']!r} and {following['id']!r}")
        if (not any(row["required"] is True for row in operations) and
                all(row["evidence"]["grade"] != "unknown" for row in operations)):
            raise ContractError(
                f"{where}.operations: known operation graph has no required operation")

        tolerances = [
            self._tolerance(raw, f"{where}.tolerances[{index}]")
            for index, raw in enumerate(_list(
                item["tolerances"], f"{where}.tolerances", nonempty=True))
        ]
        if len({row["id"] for row in tolerances}) != len(tolerances):
            raise ContractError(f"{where}.tolerances: duplicate ids")
        tolerances.sort(key=lambda row: row["id"])
        exposure_rows = [
            row for row in tolerances if row["effect"] == "exposure_setback"
        ]
        if not exposure_rows:
            raise ContractError(
                f"{where}.tolerances: at least one exposure_setback row is required")

        result = {
            "id": _identifier(item["id"], f"{where}.id"),
            "instances": sorted(instances, key=lambda row: row["ref"]),
            "receptacle": self._receptacle(item["receptacle"], f"{where}.receptacle"),
            "mate": self._mate(item["mate"], f"{where}.mate"),
            "interface": self._interface(item["interface"], f"{where}.interface"),
            "grip": self._grip(item["grip"], f"{where}.grip"),
            "fastening": self._fastening(item["fastening"], f"{where}.fastening"),
            "tool": self._tool(item["tool"], f"{where}.tool"),
            "torque": self._torque(item["torque"], f"{where}.torque"),
            "reaction": self._reaction(item["reaction"], f"{where}.reaction"),
            "cable": self._cable(item["cable"], f"{where}.cable"),
            "operations": operations,
            "tolerances": tolerances,
        }
        threaded = (
            result["fastening"]["evidence"]["grade"] != "unknown" and
            "thread" in result["fastening"]["method"].lower()
        )
        torque_required = (
            result["torque"]["evidence"]["grade"] != "unknown" and
            result["torque"]["required"] is True
        )
        if threaded or torque_required:
            if result["tool"]["evidence"]["grade"] != "unknown":
                tool_kind = result["tool"]["kind"].strip().lower()
                if tool_kind in _NO_METHOD_VALUES:
                    raise ContractError(
                        f"{where}: threaded or torque-required fastening "
                        "requires a known non-none tool")
            if result["reaction"]["evidence"]["grade"] != "unknown":
                reaction_method = result["reaction"]["method"].strip().lower()
                if reaction_method in _NO_METHOD_VALUES:
                    raise ContractError(
                        f"{where}: threaded or torque-required fastening "
                        "requires a known reaction method")
        interface_allowance = result["interface"]["exposure_setback_allowance_mm"]
        known_exposure_rows = [
            row for row in exposure_rows
            if row["evidence"]["grade"] != "unknown"
        ]
        if (interface_allowance is not None and
                len(known_exposure_rows) == len(exposure_rows)):
            required_allowance = sum(
                max(row["minus_mm"], row["plus_mm"])
                for row in known_exposure_rows
            )
            if interface_allowance + 1e-12 < required_allowance:
                raise ContractError(
                    f"{where}.interface.exposure_setback_allowance_mm: "
                    f"{interface_allowance:.9g} is below the explicit tolerance "
                    f"stack {required_allowance:.9g}")
        return result

    def _group(self, value: Any, where: str) -> dict[str, Any]:
        item = _exact_mapping(value, {
            "id", "members", "required_state", "serviceable_member_refs",
        }, where)
        state = _string(item["required_state"], f"{where}.required_state")
        assert state is not None
        if state not in _GROUP_STATES:
            raise ContractError(
                f"{where}.required_state: expected one of {sorted(_GROUP_STATES)}")
        members = [_ref(raw, f"{where}.members[{index}]")
                   for index, raw in enumerate(_list(
                       item["members"], f"{where}.members", nonempty=True))]
        serviceable = [_ref(raw, f"{where}.serviceable_member_refs[{index}]")
                       for index, raw in enumerate(_list(
                           item["serviceable_member_refs"],
                           f"{where}.serviceable_member_refs", nonempty=True))]
        if len(members) != len(set(members)):
            raise ContractError(f"{where}.members: duplicate refs")
        if len(serviceable) != len(set(serviceable)):
            raise ContractError(f"{where}.serviceable_member_refs: duplicate refs")
        if not set(serviceable).issubset(members):
            raise ContractError(f"{where}: serviceable refs must be group members")
        return {
            "id": _identifier(item["id"], f"{where}.id"),
            "members": sorted(members),
            "required_state": state,
            "serviceable_member_refs": sorted(serviceable),
        }

    def compile(self) -> dict[str, Any]:
        root_keys = {
            "schema", "contract_id", "evidence_sources", "assemblies",
            "simultaneous_groups",
        }
        if isinstance(self.document, Mapping) and "applicability" in self.document:
            root_keys.add("applicability")
        root = _exact_mapping(self.document, root_keys, "contract")
        if root["schema"] != 1 or isinstance(root["schema"], bool):
            raise ContractError("contract.schema: only schema 1 is supported")
        contract_id = _identifier(root["contract_id"], "contract.contract_id")
        self._sources(root["evidence_sources"])
        applicability = (
            self._applicability(root["applicability"])
            if "applicability" in root
            else {"operated": True, "evidence": None}
        )
        operated = applicability["operated"]

        assembly_rows = _list(
            root["assemblies"], "assemblies", nonempty=operated)
        group_rows = _list(
            root["simultaneous_groups"], "simultaneous_groups",
            nonempty=operated)
        if not operated and (assembly_rows or group_rows):
            raise ContractError(
                "applicability: operated=false requires empty assemblies and "
                "simultaneous_groups")

        assemblies = [
            self._assembly(raw, f"assemblies[{index}]")
            for index, raw in enumerate(assembly_rows)
        ]
        if len({row["id"] for row in assemblies}) != len(assemblies):
            raise ContractError("assemblies: duplicate ids")
        assemblies.sort(key=lambda row: row["id"])
        all_refs = [instance["ref"] for assembly in assemblies
                    for instance in assembly["instances"]]
        if len(all_refs) != len(set(all_refs)):
            raise ContractError("assemblies: a connector ref belongs to multiple profiles")

        groups = [
            self._group(raw, f"simultaneous_groups[{index}]")
            for index, raw in enumerate(group_rows)
        ]
        if len({row["id"] for row in groups}) != len(groups):
            raise ContractError("simultaneous_groups: duplicate ids")
        groups.sort(key=lambda row: row["id"])
        group_map = {row["id"]: row for row in groups}
        ref_set = set(all_refs)
        for group in groups:
            unknown_members = sorted(set(group["members"]) - ref_set)
            if unknown_members:
                raise ContractError(
                    f"simultaneous_groups.{group['id']}: unknown members {unknown_members}")
        claims: dict[str, set[str]] = {ref: set() for ref in all_refs}
        for assembly in assemblies:
            for instance in assembly["instances"]:
                for group_id in instance["simultaneous_group_ids"]:
                    if group_id not in group_map:
                        raise ContractError(
                            f"assemblies.{assembly['id']}.{instance['ref']}: "
                            f"unknown simultaneous group {group_id!r}")
                    claims[instance["ref"]].add(group_id)
        for group in groups:
            declared = {ref for ref, ids in claims.items() if group["id"] in ids}
            if declared != set(group["members"]):
                raise ContractError(
                    f"simultaneous_groups.{group['id']}: member list and instance "
                    f"claims differ ({sorted(set(group['members']) ^ declared)})")

        ref_profiles = {
            instance["ref"]: assembly
            for assembly in assemblies for instance in assembly["instances"]
        }
        for group in groups:
            if group["required_state"] not in {"all_connected", "all_mated"}:
                continue
            for ref in group["serviceable_member_refs"]:
                profile = ref_profiles[ref]
                covered = any(
                    operation["required"] is True and
                    operation["with_neighbors_populated"] is True
                    for operation in profile["operations"]
                )
                uncertain = any(
                    operation["evidence"]["grade"] == "unknown"
                    for operation in profile["operations"]
                )
                if not covered and not uncertain:
                    raise ContractError(
                        f"simultaneous_groups.{group['id']}: serviceable member "
                        f"{ref} in profile {profile['id']!r} has no required "
                        "operation with with_neighbors_populated=true")

        unused = sorted(set(self.sources) - self.used_sources)
        if unused:
            raise ContractError(f"evidence_sources: unreferenced sources {unused}")

        normalized = {
            "schema": 1,
            "contract_id": contract_id,
            "applicability": applicability,
            "evidence_sources": self.source_declarations,
            "assemblies": assemblies,
            "simultaneous_groups": groups,
        }
        semantic_sha256 = _digest(_canonical_bytes(normalized))
        evidence_files = [self.sources[source_id] for source_id in sorted(self.sources)]
        inputs = {
            "contract": self.contract_binding,
            "compiler": _compiler_binding(),
            "evidence_files": evidence_files,
        }
        subject_sha256 = _digest(_canonical_bytes({
            "semantic_sha256": semantic_sha256,
            "inputs": inputs,
        }))
        evidence_total = sum(self.evidence_counts.values())
        unknown_count = self.evidence_counts["unknown"]
        conservative_count = self.evidence_counts["conservative"]
        ceiling = ("UNKNOWN" if unknown_count else
                   "CONSERVATIVE" if conservative_count else "EXACT")
        status = ("N-A" if not operated else
                  "INCOMPLETE" if unknown_count else "PASS")
        summary = {
            "assembly_count": len(assemblies),
            "instance_count": len(all_refs),
            "simultaneous_group_count": len(groups),
            "operation_count": sum(len(row["operations"]) for row in assemblies),
            "tolerance_count": sum(len(row["tolerances"]) for row in assemblies),
            "evidence_total": evidence_total,
            "evidence_exact": self.evidence_counts["exact"],
            "evidence_conservative": conservative_count,
            "evidence_unknown": unknown_count,
            "evidence_ceiling": ceiling,
            "evidence_file_count": len(evidence_files),
        }
        return {
            "kind": RECEIPT_KIND,
            "schema": RECEIPT_SCHEMA,
            "status": status,
            "inputs": inputs,
            "semantic_sha256": semantic_sha256,
            "subject_sha256": subject_sha256,
            "assemblies": assemblies,
            "simultaneous_groups": groups,
            "unknowns": sorted(self.unknowns, key=lambda row: (row["path"], row["rationale"])),
            "summary": summary,
        }


def load_and_compile(project: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    """Compile a strict schema-1 contract into a deterministic receipt mapping.

    Contract and evidence paths in the receipt are relative to ``project``.
    The compiler input is repository-relative identity and is not reopened as a
    project artifact.  Raises :class:`ContractError` for schema/path failures.
    """
    root = _project_directory(Path(project))
    return _Compiler(root, Path(contract_path)).compile()


def validate_receipt(
        receipt: Mapping[str, Any], project: str | Path,
        expected_contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[bool, list[str]]:
    """Reopen all current inputs and require deterministic receipt equality.

    This is the shared governing-consumer API.  Its two-argument form accepts
    only the canonical ``DEFAULT_CONTRACT`` authority.  A caller compiling a
    deliberately non-governing alternate may pass that exact expected path,
    but must not use the result as project authority.  A valid receipt may
    still have status ``INCOMPLETE``; callers independently enforce the
    readiness required for their scope. ``N-A`` is valid only for the exact
    evidence-backed zero-operated-connector branch. Compiler identity is
    load-bearing.
    """
    if not isinstance(receipt, Mapping):
        return False, ["receipt: expected mapping"]
    expected_keys = {
        "kind", "schema", "status", "inputs", "semantic_sha256",
        "subject_sha256", "assemblies", "simultaneous_groups", "unknowns",
        "summary",
    }
    if set(receipt) != expected_keys:
        return False, [
            "receipt: exact schema violation "
            f"missing={sorted(expected_keys - set(receipt))} "
            f"unknown={sorted(set(receipt) - expected_keys, key=str)}"
        ]
    if receipt.get("kind") != RECEIPT_KIND or receipt.get("schema") != RECEIPT_SCHEMA:
        return False, ["receipt: kind/schema mismatch"]
    inputs = receipt.get("inputs")
    if not isinstance(inputs, Mapping) or set(inputs) != {
            "contract", "compiler", "evidence_files"}:
        return False, ["receipt.inputs: exact schema violation"]
    contract = inputs.get("contract")
    if not isinstance(contract, Mapping) or set(contract) != {"path", "sha256", "size"}:
        return False, ["receipt.inputs.contract: exact schema violation"]
    contract_path = contract.get("path")
    if not isinstance(contract_path, str) or not contract_path:
        return False, ["receipt.inputs.contract.path: expected project-relative string"]
    try:
        root = _project_directory(Path(project))
        _, expected_relative = _project_path(
            root, Path(expected_contract_path), "expected contract")
        if contract_path != expected_relative:
            return False, [
                "receipt.inputs.contract.path: receipt-selected authority "
                f"{contract_path!r} does not match expected {expected_relative!r}"
            ]
        current = load_and_compile(root, Path(expected_relative))
    except ContractError as exc:
        return False, [f"receipt source reopen failed: {exc}"]
    if _canonical_bytes(dict(receipt)) == _canonical_bytes(current):
        return True, []

    findings: list[str] = []
    for key in (
        "status", "semantic_sha256", "subject_sha256", "assemblies",
        "simultaneous_groups", "unknowns", "summary",
    ):
        if receipt.get(key) != current.get(key):
            findings.append(f"receipt.{key}: differs from freshly compiled value")
    if receipt.get("inputs") != current.get("inputs"):
        findings.append("receipt.inputs: contract, evidence, or compiler identity is stale")
    if not findings:  # defensive: canonical disagreement should remain visible
        findings.append("receipt: deterministic payload differs")
    return False, findings


def regrade_receipt(
        receipt_path: str | Path, project: str | Path,
        expected_contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[bool, list[str]]:
    """Load a project-relative ordinary JSON receipt and call validate_receipt."""
    try:
        root = _project_directory(Path(project))
        _, raw = _ordinary_file(root, Path(receipt_path), "receipt")
        text = raw.decode("utf-8")

        def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            value: dict[str, Any] = {}
            for key, item in pairs:
                if key in value:
                    raise ContractError(f"receipt: duplicate JSON key {key!r}")
                value[key] = item
            return value

        receipt = json.loads(text, object_pairs_hook=reject_duplicates)
    except (ContractError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, [f"receipt: cannot load: {exc}"]
    return validate_receipt(
        receipt, root, expected_contract_path=expected_contract_path)


def _write_receipt(
        project: Path, output: Path, receipt: Mapping[str, Any],
        expected_contract_path: str | Path = DEFAULT_CONTRACT,
) -> Path:
    candidate, _ = _project_path(project, output, "output")
    protected = {
        _absolute_lexical(project / Path(receipt["inputs"]["contract"]["path"])),
        _absolute_lexical(REPO_ROOT / Path(receipt["inputs"]["compiler"]["path"])),
        *(
            _absolute_lexical(project / Path(row["path"]))
            for row in receipt["inputs"]["evidence_files"]
        ),
    }
    if candidate in protected:
        raise ContractError(
            "output: destination aliases a contract, evidence, or compiler input")
    _reject_symlink_components(candidate.parent, "output parent", allow_missing_tail=True)
    try:
        candidate.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ContractError(f"output parent: cannot create: {exc}") from exc
    _reject_symlink_components(candidate.parent, "output parent")

    try:
        named_parent = candidate.parent.lstat()
    except OSError as exc:
        raise ContractError(f"output parent: cannot inspect: {exc}") from exc
    if not stat.S_ISDIR(named_parent.st_mode) or stat.S_ISLNK(named_parent.st_mode):
        raise ContractError("output parent: expected ordinary directory")
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise ContractError(
            "output: platform lacks required O_DIRECTORY/O_NOFOLLOW safety")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
    try:
        directory_fd = os.open(candidate.parent, directory_flags)
    except OSError as exc:
        raise ContractError(f"output parent: cannot hold directory: {exc}") from exc

    def directory_identity(value: os.stat_result) -> tuple[int, int, int]:
        return value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode)

    temporary_name: str | None = None
    descriptor = -1
    published_descriptor = -1
    payload = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    payload_bytes = payload.encode("utf-8")
    published_identity: tuple[int, int] | None = None

    def remove_published_receipt() -> None:
        """Remove only the inode this invocation atomically published."""
        if published_identity is None:
            return
        try:
            target = os.stat(
                candidate.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise ContractError(
                f"output: cannot inspect stale published receipt: {exc}") from exc
        if (target.st_dev, target.st_ino) != published_identity:
            # The published inode is no longer named by the destination.  Do
            # not remove a concurrently supplied replacement.
            return
        if not stat.S_ISREG(target.st_mode) or stat.S_ISLNK(target.st_mode):
            raise ContractError(
                "output: stale published receipt no longer has ordinary-file identity")
        try:
            os.unlink(candidate.name, dir_fd=directory_fd)
            os.fsync(directory_fd)
        except OSError as exc:
            raise ContractError(
                f"output: cannot remove stale published receipt: {exc}") from exc

    def reopen_published_receipt() -> bytes:
        """Read the named output through the held directory without following links."""
        read_flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            read_flags |= os.O_CLOEXEC
        try:
            receipt_fd = os.open(candidate.name, read_flags, dir_fd=directory_fd)
        except OSError as exc:
            raise ContractError(
                f"output: cannot reopen published receipt: {exc}") from exc
        try:
            before = os.fstat(receipt_fd)
            if (not stat.S_ISREG(before.st_mode) or
                    before.st_nlink != 1 or
                    (before.st_dev, before.st_ino) != published_identity):
                raise ContractError(
                    "output: published receipt identity changed during verification")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(receipt_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(receipt_fd)
            identity = lambda row: (
                row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns,
                row.st_ctime_ns, row.st_nlink)
            if identity(before) != identity(after):
                raise ContractError(
                    "output: published receipt changed while being verified")
            data = b"".join(chunks)
            if len(data) != before.st_size:
                raise ContractError("output: short read while verifying receipt")
        finally:
            os.close(receipt_fd)
        try:
            named = os.stat(
                candidate.name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as exc:
            raise ContractError(
                f"output: cannot re-inspect published receipt: {exc}") from exc
        if (stat.S_ISLNK(named.st_mode) or identity(named) != identity(after)):
            raise ContractError(
                "output: published receipt path changed while being verified")
        return data

    try:
        held_parent = os.fstat(directory_fd)
        if (not stat.S_ISDIR(held_parent.st_mode) or
                directory_identity(named_parent) != directory_identity(held_parent)):
            raise ContractError("output parent: identity changed before hold")
        try:
            rechecked_parent = candidate.parent.lstat()
        except OSError as exc:
            raise ContractError(
                f"output parent: cannot recheck held identity: {exc}") from exc
        if (stat.S_ISLNK(rechecked_parent.st_mode) or
                directory_identity(rechecked_parent) != directory_identity(held_parent)):
            raise ContractError("output parent: named identity differs from held directory")

        try:
            target = os.stat(
                candidate.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            target = None
        except OSError as exc:
            raise ContractError(f"output: cannot inspect existing target: {exc}") from exc
        if target is not None and (
                not stat.S_ISREG(target.st_mode) or stat.S_ISLNK(target.st_mode) or
                target.st_nlink != 1):
            raise ContractError("output: existing target is not an ordinary file")

        create_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            create_flags |= os.O_CLOEXEC
        for _ in range(128):
            temporary_name = f".{candidate.name}.{secrets.token_hex(12)}.tmp"
            try:
                descriptor = os.open(
                    temporary_name, create_flags, 0o600, dir_fd=directory_fd)
                break
            except FileExistsError:
                continue
            except OSError as exc:
                raise ContractError(f"output: cannot create temporary file: {exc}") from exc
        else:  # pragma: no cover - cryptographic collision or hostile saturation
            raise ContractError("output: cannot allocate a unique temporary file")

        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        try:
            publish_parent = candidate.parent.lstat()
        except OSError as exc:
            raise ContractError(
                f"output parent: cannot recheck before publication: {exc}") from exc
        if (stat.S_ISLNK(publish_parent.st_mode) or
                directory_identity(publish_parent) != directory_identity(held_parent)):
            raise ContractError("output parent: identity changed before publication")
        staged_flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            staged_flags |= os.O_CLOEXEC
        try:
            published_descriptor = os.open(
                temporary_name, staged_flags, dir_fd=directory_fd)
        except OSError as exc:
            raise ContractError(f"output: cannot hold staged receipt: {exc}") from exc
        staged = os.fstat(published_descriptor)
        if (not stat.S_ISREG(staged.st_mode) or stat.S_ISLNK(staged.st_mode) or
                staged.st_nlink != 1):
            raise ContractError("output: staged receipt is not an ordinary file")
        published_identity = (staged.st_dev, staged.st_ino)
        os.replace(
            temporary_name, candidate.name,
            src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        temporary_name = None
        os.fsync(directory_fd)

        valid, findings = validate_receipt(
            receipt, project,
            expected_contract_path=expected_contract_path)
        if not valid:
            remove_published_receipt()
            raise ContractError(
                "inputs changed during receipt publication: " +
                "; ".join(findings))
        try:
            published_bytes = reopen_published_receipt()
        except ContractError:
            remove_published_receipt()
            raise
        if published_bytes != payload_bytes:
            remove_published_receipt()
            raise ContractError(
                "output: published receipt bytes differ from freshly regraded payload")
    except OSError as exc:
        raise ContractError(f"output: publication failed: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if published_descriptor >= 0:
            os.close(published_descriptor)
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        os.close(directory_fd)
    return candidate


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True,
                        help="project root owning 03_src/rules and evidence files")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT,
                        help=f"project-relative contract (default: {DEFAULT_CONTRACT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"project-relative receipt output (default: {DEFAULT_OUTPUT})")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        project = _project_directory(args.project)
        receipt = load_and_compile(project, args.contract)
        valid, findings = validate_receipt(
            receipt, project, expected_contract_path=args.contract)
        if not valid:
            raise ContractError(
                "inputs changed before receipt publication: " +
                "; ".join(findings))
        output = _write_receipt(
            project, args.output, receipt,
            expected_contract_path=args.contract)
    except ContractError as exc:
        print(f"CONNECTOR-CONTRACT FAIL: {exc}", file=sys.stderr)
        return 1
    summary = receipt["summary"]
    print(
        f"CONNECTOR-CONTRACT {receipt['status']} "
        f"assemblies={summary['assembly_count']} "
        f"instances={summary['instance_count']} "
        f"coverage="
        f"{summary['evidence_total'] - summary['evidence_unknown']}/"
        f"{summary['evidence_total']} "
        f"unknown={summary['evidence_unknown']} "
        f"ceiling={summary['evidence_ceiling']} output={output}"
    )
    return 0 if receipt["status"] in {"PASS", "N-A"} else 2


if __name__ == "__main__":
    sys.exit(main())
