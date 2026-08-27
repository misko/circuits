#!/usr/bin/env python3
"""Strict commissioning and evidence contracts for pcb-enclosure schema v2.

Schema v1 remains owned by ``enclosure_common.py``.  This module is an
additive v2 seam: it validates a hash-bound mechanical-intent document, exact
release subjects, installed-part authority, independent fastener roles,
assembly motion, clearance cases, and an extensible physical-test census.

It deliberately does not generate geometry.  A CAD adapter may consume a
validated v2 configuration, but it must not silently weaken these contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("pcb-enclosure v2 needs PyYAML") from exc

try:
    from enclosure_common import (  # type: ignore
        atomic_output,
        EnclosureError as V1EnclosureError,
        load_json as load_json_strict,
        load_bound_config as load_bound_config_v1,
        read_stable_bytes,
        sha256_file as sha256_file_v1,
        stable_file_digest as stable_file_digest_v1,
    )
except ImportError:  # pragma: no cover - package-style import seam
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from enclosure_common import (  # type: ignore
        atomic_output,
        EnclosureError as V1EnclosureError,
        load_json as load_json_strict,
        load_bound_config as load_bound_config_v1,
        read_stable_bytes,
        sha256_file as sha256_file_v1,
        stable_file_digest as stable_file_digest_v1,
    )


CONFIG_KIND = "pcb-enclosure-config-v2"
INTENT_KIND = "pcb-enclosure-mechanical-intent-v2"
PHYSICAL_KIND = "pcb-enclosure-physical-evidence-v2"
VALIDATION_KIND = "pcb-enclosure-v2-validation"

READINESS = ("INCOMPLETE", "CAD_READY", "PRINT_VERIFIED",
             "THERMALLY_VERIFIED")
RESULT_STATUSES = {"FAIL", *READINESS}
READINESS_RANK = {status: index for index, status in enumerate(READINESS)}
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*$")
CUSTOM_TEST_RE = re.compile(
    r"^custom\.[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")

AUTHORITY_GRADES = {
    "vendor_authoritative",
    "measured_unit",
    "derived_measurement",
    "conservative_candidate",
    "inspiration_only",
}
AUTHORITY_REQUIRED_EXCLUSIONS = {
    "vendor_authoritative": {"physical_fit"},
    "measured_unit": {"physical_fit"},
    "derived_measurement": {"physical_fit"},
    "conservative_candidate": {"exact_geometry", "physical_fit"},
    "inspiration_only": {
        "exact_geometry", "clearance", "physical_fit",
        "manufacturing_dimensions",
    },
}
BUILTIN_PHYSICAL_TYPES = {
    "insert_coupon",
    "board_drop_in",
    "board_support_clearance",
    "all_interfaces_mated",
    "thermal_soak",
    "lid_off_pcb_retention",
    "case_closure_independence",
    "accessory_insertion_removal",
    "accessory_retention_rattle",
    "cable_strain_clearance",
}


class V2Error(ValueError):
    """A v2 document is malformed, ambiguous, or contradictory."""


class StrictLoader(yaml.SafeLoader):
    """YAML loader which rejects duplicate mapping keys."""


def _construct_mapping(loader: StrictLoader, node: yaml.MappingNode,
                       deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise V2Error(
                f"duplicate YAML key {key!r} at line "
                f"{key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(read_stable_bytes(
            path, f"schema-v2 YAML input {path}").decode("utf-8"),
            Loader=StrictLoader)
    except (OSError, yaml.YAMLError, UnicodeError) as exc:
        raise V2Error(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise V2Error(f"{path}: expected a YAML mapping")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = load_json_strict(path)
    except V1EnclosureError as exc:
        raise V2Error(f"cannot read {path}: {exc}") from exc
    return value


def sha256_file(path: Path) -> str:
    return sha256_file_v1(path)


def semantic_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise V2Error(f"{where}: expected mapping")
    return value


def _exact(value: Any, fields: Iterable[str], where: str) -> Mapping[str, Any]:
    item = _mapping(value, where)
    expected = set(fields)
    actual = set(item)
    if actual != expected:
        raise V2Error(
            f"{where}: fields differ; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}")
    return item


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise V2Error(f"{where}: expected {'non-empty ' if nonempty else ''}string")
    return value


def _identifier(value: Any, where: str) -> str:
    result = _string(value, where)
    if not ID_RE.fullmatch(result):
        raise V2Error(f"{where}: expected normalized lower-case identifier")
    return result


def _enum(value: Any, choices: Iterable[str], where: str) -> str:
    result = _string(value, where)
    allowed = set(choices)
    if result not in allowed:
        raise V2Error(f"{where}: expected one of {sorted(allowed)}")
    return result


def _boolean(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise V2Error(f"{where}: expected boolean")
    return value


def _number(value: Any, where: str, *, positive: bool = False,
            nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise V2Error(f"{where}: expected number")
    result = float(value)
    if not math.isfinite(result):
        raise V2Error(f"{where}: expected finite number")
    if positive and result <= 0:
        raise V2Error(f"{where}: expected > 0")
    if nonnegative and result < 0:
        raise V2Error(f"{where}: expected >= 0")
    return result


def _vec(value: Any, count: int, where: str, *, nonzero: bool = False) -> list[float]:
    if not isinstance(value, list) or len(value) != count:
        raise V2Error(f"{where}: expected {count}-element list")
    result = [_number(axis, f"{where}[{index}]")
              for index, axis in enumerate(value)]
    if nonzero and math.sqrt(sum(axis * axis for axis in result)) <= 1e-12:
        raise V2Error(f"{where}: vector must be nonzero")
    return result


def _unique_ids(rows: Any, where: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(rows, list) or (not rows and not allow_empty):
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise V2Error(f"{where}: expected {qualifier} list")
    result: list[str] = []
    for index, value in enumerate(rows):
        ident = _identifier(value, f"{where}[{index}]")
        if ident in result:
            raise V2Error(f"{where}: duplicate identifier {ident}")
        result.append(ident)
    return result


def _row_ids(rows: Any, where: str, *, allow_empty: bool = False) -> set[str]:
    if not isinstance(rows, list) or (not rows and not allow_empty):
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise V2Error(f"{where}: expected {qualifier} list")
    result: set[str] = set()
    for index, row in enumerate(rows):
        item = _mapping(row, f"{where}[{index}]")
        ident = _identifier(item.get("id"), f"{where}[{index}].id")
        if ident in result:
            raise V2Error(f"{where}: duplicate id {ident}")
        result.add(ident)
    return result


def _safe_relative_path(value: Any, root: Path, where: str) -> Path:
    text = _string(value, where)
    path = Path(text)
    if path.is_absolute() or "\\" in text or any(
            part in {"", ".", ".."} for part in path.parts):
        raise V2Error(
            f"{where}: path must be normalized, relative, and traversal-free")
    base = root.resolve()
    cursor = base
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise V2Error(f"{where}: symlink paths are not accepted")
    resolved = (base / path).resolve(strict=False)
    if not resolved.is_relative_to(base):
        raise V2Error(f"{where}: path escapes root")
    return resolved


def validate_file_binding(value: Any, root: Path, where: str) -> dict[str, Any]:
    item = _exact(value, {"path", "sha256", "size"}, where)
    path = _safe_relative_path(item["path"], root, f"{where}.path")
    digest = _string(item["sha256"], f"{where}.sha256")
    if not HEX64_RE.fullmatch(digest):
        raise V2Error(f"{where}.sha256: expected lowercase 64-hex")
    size = item["size"]
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise V2Error(f"{where}.size: expected positive integer")
    try:
        _, info, actual_hash = stable_file_digest_v1(path, where)
    except V1EnclosureError as exc:
        raise V2Error(str(exc)) from exc
    actual_size = info.st_size
    if actual_size != size or actual_hash != digest:
        raise V2Error(f"{where}: bound size/hash differs from actual file")
    return {"path": path, "sha256": digest, "size": size}


def _validate_cabled_parts(rows: Any) -> list[dict[str, Any]]:
    ids = _row_ids(rows, "intent.requirements.cabled_parts", allow_empty=True)
    result = []
    for index, raw in enumerate(rows):
        where = f"intent.requirements.cabled_parts[{index}]"
        row = _exact(raw, {
            "id", "part", "cable_pre_attached", "threading_permitted",
            "bending_permitted", "disconnecting_permitted",
        }, where)
        _identifier(row["id"], f"{where}.id")
        _identifier(row["part"], f"{where}.part")
        for field in ("cable_pre_attached", "threading_permitted",
                      "bending_permitted", "disconnecting_permitted"):
            _boolean(row[field], f"{where}.{field}")
        if row["cable_pre_attached"] and row["threading_permitted"]:
            raise V2Error(
                f"{where}: a pre-attached cable may not be authorized for threading; "
                "model a full-part insertion path")
        result.append(dict(row))
    if len(ids) != len(result):  # defensive; _row_ids already rejects duplicates
        raise V2Error("intent.requirements.cabled_parts: duplicate rows")
    parts = [row["part"] for row in result]
    if len(parts) != len(set(parts)):
        raise V2Error("intent.requirements.cabled_parts: duplicate part")
    return result


def validate_mechanical_intent(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the standalone v2 mechanical commissioning authority."""
    top = _exact(value, {
        "schema", "kind", "name", "desired_release", "requirements",
        "states", "operations", "unknowns", "excluded_claims",
    }, "intent")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise V2Error("intent.schema: expected 2")
    if top["kind"] != INTENT_KIND:
        raise V2Error(f"intent.kind: expected {INTENT_KIND!r}")
    _identifier(top["name"], "intent.name")

    desired = _exact(top["desired_release"], {"lifecycle", "readiness"},
                     "intent.desired_release")
    _enum(desired["lifecycle"], {"draft", "immutable"},
          "intent.desired_release.lifecycle")
    _enum(desired["readiness"], set(READINESS) - {"INCOMPLETE"},
          "intent.desired_release.readiness")

    requirements = _exact(top["requirements"], {
        "pcb_retained_with_lid_removed", "cabled_parts",
    }, "intent.requirements")
    _boolean(requirements["pcb_retained_with_lid_removed"],
             "intent.requirements.pcb_retained_with_lid_removed")
    if not requirements["pcb_retained_with_lid_removed"]:
        raise V2Error(
            "intent.requirements.pcb_retained_with_lid_removed: schema v2 "
            "requires independent lid-off PCB retention")
    cabled_parts = _validate_cabled_parts(requirements["cabled_parts"])

    state_ids = _row_ids(top["states"], "intent.states")
    purposes: list[str] = []
    state_map: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(top["states"]):
        where = f"intent.states[{index}]"
        row = _exact(raw, {
            "id", "purpose", "present_parts", "secured_fastener_groups",
            "enclosure_closed", "pcb_retained",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        purpose = _enum(row["purpose"], {
            "initial", "insertion", "lid_removed", "installed", "service",
            "removal",
        }, f"{where}.purpose")
        purposes.append(purpose)
        _unique_ids(row["present_parts"], f"{where}.present_parts",
                    allow_empty=True)
        _unique_ids(row["secured_fastener_groups"],
                    f"{where}.secured_fastener_groups", allow_empty=True)
        _boolean(row["enclosure_closed"], f"{where}.enclosure_closed")
        _boolean(row["pcb_retained"], f"{where}.pcb_retained")
        if purpose == "lid_removed" and row["enclosure_closed"]:
            raise V2Error(f"{where}: lid_removed state cannot be closed")
        if purpose == "installed" and not row["enclosure_closed"]:
            raise V2Error(f"{where}: installed state must be closed")
        state_map[ident] = row
    for required_purpose in ("lid_removed", "installed"):
        if purposes.count(required_purpose) != 1:
            raise V2Error(
                f"intent.states: expected exactly one {required_purpose} state")

    operation_ids = _row_ids(top["operations"], "intent.operations")
    operation_map: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(top["operations"]):
        where = f"intent.operations[{index}]"
        row = _exact(raw, {
            "id", "kind", "from_state", "to_state", "moving_parts",
            "direction", "travel_mm", "cable_condition",
            "threading_permitted", "bending_permitted",
            "disconnecting_permitted", "clearance_case",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        kind = _enum(row["kind"], {"linear_insert", "linear_remove"},
                     f"{where}.kind")
        source = _identifier(row["from_state"], f"{where}.from_state")
        target = _identifier(row["to_state"], f"{where}.to_state")
        if source not in state_ids or target not in state_ids:
            raise V2Error(f"{where}: from/to state is not declared")
        if source == target:
            raise V2Error(f"{where}: from_state and to_state must differ")
        moving = _unique_ids(row["moving_parts"], f"{where}.moving_parts")
        _vec(row["direction"], 3, f"{where}.direction", nonzero=True)
        _number(row["travel_mm"], f"{where}.travel_mm", positive=True)
        _enum(row["cable_condition"],
              {"pre_attached", "detached", "not_applicable"},
              f"{where}.cable_condition")
        for field in ("threading_permitted", "bending_permitted",
                      "disconnecting_permitted"):
            _boolean(row[field], f"{where}.{field}")
        _identifier(row["clearance_case"], f"{where}.clearance_case")

        before = set(state_map[source]["present_parts"])
        after = set(state_map[target]["present_parts"])
        changed = after - before if kind == "linear_insert" else before - after
        opposite = before - after if kind == "linear_insert" else after - before
        if opposite:
            raise V2Error(
                f"{where}: {kind} also changes parts in the opposite direction: "
                f"{sorted(opposite)}")
        if changed != set(moving):
            raise V2Error(
                f"{where}: moving_parts {sorted(moving)} do not equal state delta "
                f"{sorted(changed)}")
        operation_map[ident] = row

    for cabled in cabled_parts:
        moving_ops = [row for row in operation_map.values()
                      if cabled["part"] in row["moving_parts"]]
        if not moving_ops:
            raise V2Error(
                f"intent cabled part {cabled['part']}: no linear operation declared")
        if cabled["cable_pre_attached"] and not any(
                row["kind"] == "linear_insert" for row in moving_ops):
            raise V2Error(
                f"intent cabled part {cabled['part']}: no insertion operation")
        expected_condition = ("pre_attached" if cabled["cable_pre_attached"]
                              else "detached")
        for row in moving_ops:
            if row["cable_condition"] != expected_condition:
                raise V2Error(
                    f"intent operation {row['id']}: cable condition contradicts "
                    f"cabled part {cabled['part']}")
            for field in ("threading_permitted", "bending_permitted",
                          "disconnecting_permitted"):
                if row[field] != cabled[field]:
                    raise V2Error(
                        f"intent operation {row['id']}: {field} contradicts "
                        f"cabled part {cabled['part']}")

    unknown_ids = _row_ids(top["unknowns"], "intent.unknowns", allow_empty=True)
    for index, raw in enumerate(top["unknowns"]):
        where = f"intent.unknowns[{index}]"
        row = _exact(raw, {"id", "scope", "question", "blocks_readiness"}, where)
        _identifier(row["id"], f"{where}.id")
        _identifier(row["scope"], f"{where}.scope")
        _string(row["question"], f"{where}.question")
        _enum(row["blocks_readiness"],
              {"CAD_READY", "PRINT_VERIFIED", "THERMALLY_VERIFIED"},
              f"{where}.blocks_readiness")
    if len(unknown_ids) != len(top["unknowns"]):
        raise V2Error("intent.unknowns: duplicate ids")
    excluded = _unique_ids(top["excluded_claims"], "intent.excluded_claims",
                           allow_empty=True)
    if len(excluded) != len(set(excluded)):
        raise V2Error("intent.excluded_claims: duplicate claim")
    return dict(value)


def _validate_external_subjects(rows: Any, root: Path) -> tuple[dict[str, Any],
                                                               dict[str, Any]]:
    ids = _row_ids(rows, "config.external_subjects", allow_empty=True)
    result: dict[str, Any] = {}
    bindings: dict[str, Any] = {}
    for index, raw in enumerate(rows):
        where = f"config.external_subjects[{index}]"
        row = _exact(raw, {"id", "role", "source", "authority"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        _identifier(row["role"], f"{where}.role")
        bindings[ident] = validate_file_binding(
            row["source"], root, f"{where}.source")
        authority = _exact(row["authority"],
                           {"grade", "basis", "excluded_claims"},
                           f"{where}.authority")
        grade = _enum(authority["grade"], AUTHORITY_GRADES,
                      f"{where}.authority.grade")
        _string(authority["basis"], f"{where}.authority.basis")
        excluded = set(_unique_ids(
            authority["excluded_claims"],
            f"{where}.authority.excluded_claims", allow_empty=True))
        missing = AUTHORITY_REQUIRED_EXCLUSIONS[grade] - excluded
        if missing:
            raise V2Error(
                f"{where}.authority.excluded_claims: grade {grade} must "
                f"exclude {sorted(missing)}")
        result[ident] = dict(row)
    if len(ids) != len(result):
        raise V2Error("config.external_subjects: duplicate ids")
    return result, bindings


def _validate_scopes(rows: Any) -> dict[str, Mapping[str, Any]]:
    ids = _row_ids(rows, "config.verification_scopes")
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(rows):
        where = f"config.verification_scopes[{index}]"
        row = _exact(raw, {"id", "description", "required", "depends_on"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        _string(row["description"], f"{where}.description")
        _boolean(row["required"], f"{where}.required")
        deps = _unique_ids(row["depends_on"], f"{where}.depends_on",
                           allow_empty=True)
        if ident in deps:
            raise V2Error(f"{where}.depends_on: scope cannot depend on itself")
        result[ident] = row
    for ident, row in result.items():
        missing = set(row["depends_on"]) - ids
        if missing:
            raise V2Error(
                f"config verification scope {ident}: unknown dependencies "
                f"{sorted(missing)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ident: str) -> None:
        if ident in visiting:
            raise V2Error("config.verification_scopes: dependency cycle")
        if ident in visited:
            return
        visiting.add(ident)
        for dep in result[ident]["depends_on"]:
            visit(dep)
        visiting.remove(ident)
        visited.add(ident)

    for ident in result:
        visit(ident)
    return result


def _validate_installed_parts(rows: Any, scopes: Mapping[str, Any],
                              external: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.installed_parts")
    result: dict[str, Mapping[str, Any]] = {}
    role_count: dict[str, int] = {}
    for index, raw in enumerate(rows):
        where = f"config.installed_parts[{index}]"
        row = _exact(raw, {"id", "role", "source", "scopes"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        role = _enum(row["role"],
                     {"pcb", "base", "lid", "panel", "accessory", "hardware"},
                     f"{where}.role")
        role_count[role] = role_count.get(role, 0) + 1
        source = _exact(row["source"], {"kind", "id"}, f"{where}.source")
        source_kind = _enum(source["kind"],
                            {"subject", "generated", "external_subject"},
                            f"{where}.source.kind")
        source_id = _identifier(source["id"], f"{where}.source.id")
        if source_kind == "subject" and not (role == "pcb" and source_id == "pcb"):
            raise V2Error(
                f"{where}.source: only the pcb installed part may use subject:pcb")
        if source_kind == "external_subject" and source_id not in external:
            raise V2Error(f"{where}.source: unknown external subject {source_id}")
        part_scopes = _unique_ids(row["scopes"], f"{where}.scopes")
        missing = set(part_scopes) - set(scopes)
        if missing:
            raise V2Error(f"{where}.scopes: unknown scopes {sorted(missing)}")
        result[ident] = row
    for singular in ("pcb", "base", "lid"):
        if role_count.get(singular, 0) != 1:
            raise V2Error(
                f"config.installed_parts: expected exactly one {singular} part")
    return result


def _normalize(vec: Sequence[float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(axis * axis for axis in vec))
    return tuple(axis / length for axis in vec)  # type: ignore[return-value]


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(vec: Sequence[float]) -> float:
    return math.sqrt(sum(axis * axis for axis in vec))


def _parallel_axis_distance(first: Mapping[str, Any],
                            second: Mapping[str, Any]) -> float | None:
    a = _normalize(first["direction"])
    b = _normalize(second["direction"])
    if _norm(_cross(a, b)) > 1e-6:
        return None
    delta = [second["origin_mm"][index] - first["origin_mm"][index]
             for index in range(3)]
    return _norm(_cross(delta, a))


def _validate_fasteners(rows: Any, policy: Mapping[str, Any],
                        parts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.fastener_groups")
    result: dict[str, Mapping[str, Any]] = {}
    roles: dict[str, list[str]] = {role: [] for role in
                                   ("board_retention", "case_closure", "accessory")}
    axes_by_group: dict[str, list[Mapping[str, Any]]] = {}
    part_ids = set(parts)
    pcb = next(ident for ident, row in parts.items() if row["role"] == "pcb")
    base = next(ident for ident, row in parts.items() if row["role"] == "base")
    lid = next(ident for ident, row in parts.items() if row["role"] == "lid")
    accessory_parts = {ident for ident, row in parts.items()
                       if row["role"] == "accessory"}

    for index, raw in enumerate(rows):
        where = f"config.fastener_groups[{index}]"
        row = _exact(raw, {
            "id", "role", "axes", "retained_parts", "hardware",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        role = _enum(row["role"], roles, f"{where}.role")
        roles[role].append(ident)
        axis_ids = _row_ids(row["axes"], f"{where}.axes")
        axes = []
        for ai, raw_axis in enumerate(row["axes"]):
            axis_where = f"{where}.axes[{ai}]"
            axis = _exact(raw_axis, {"id", "origin_mm", "direction"}, axis_where)
            _identifier(axis["id"], f"{axis_where}.id")
            _vec(axis["origin_mm"], 3, f"{axis_where}.origin_mm")
            _vec(axis["direction"], 3, f"{axis_where}.direction", nonzero=True)
            axes.append(axis)
        if len(axis_ids) != len(axes):
            raise V2Error(f"{where}.axes: duplicate ids")
        retained = set(_unique_ids(row["retained_parts"], f"{where}.retained_parts"))
        missing = retained - part_ids
        if missing:
            raise V2Error(f"{where}.retained_parts: unknown parts {sorted(missing)}")
        hardware = _exact(row["hardware"], {
            "thread", "screw_length_mm", "minimum_engagement_mm",
            "minimum_tip_clearance_mm",
        }, f"{where}.hardware")
        _string(hardware["thread"], f"{where}.hardware.thread")
        _number(hardware["screw_length_mm"],
                f"{where}.hardware.screw_length_mm", positive=True)
        _number(hardware["minimum_engagement_mm"],
                f"{where}.hardware.minimum_engagement_mm", positive=True)
        _number(hardware["minimum_tip_clearance_mm"],
                f"{where}.hardware.minimum_tip_clearance_mm", nonnegative=True)
        if role == "board_retention":
            if not {pcb, base}.issubset(retained) or lid in retained:
                raise V2Error(
                    f"{where}: board_retention must retain pcb+base and must not "
                    "retain the lid")
        elif role == "case_closure":
            if not {base, lid}.issubset(retained) or pcb in retained:
                raise V2Error(
                    f"{where}: case_closure must retain base+lid and must not "
                    "retain the PCB")
        elif not (retained & accessory_parts) or not (base in retained or lid in retained):
            raise V2Error(
                f"{where}: accessory group must retain an accessory and base or lid")
        result[ident] = row
        axes_by_group[ident] = axes

    if not roles["board_retention"] or not roles["case_closure"]:
        raise V2Error(
            "config.fastener_groups: board_retention and case_closure are required")
    tolerance = policy["axis_disjoint_tolerance_mm"]
    for board_group in roles["board_retention"]:
        for case_group in roles["case_closure"]:
            for board_axis in axes_by_group[board_group]:
                for case_axis in axes_by_group[case_group]:
                    distance = _parallel_axis_distance(board_axis, case_axis)
                    if distance is not None and distance <= tolerance + 1e-12:
                        raise V2Error(
                            "config.fastener_groups: board_retention and "
                            f"case_closure axes overlap within {tolerance:g} mm "
                            f"({board_group}:{board_axis['id']} vs "
                            f"{case_group}:{case_axis['id']})")
    return result


def _validate_clearance_cases(rows: Any, scopes: Mapping[str, Any],
                              parts: Mapping[str, Any],
                              operations: Mapping[str, Any],
                              cabled: Mapping[str, Any],
                              states: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.clearance_cases")
    result: dict[str, Mapping[str, Any]] = {}
    operation_cases: dict[str, str] = {}
    for index, raw in enumerate(rows):
        where = f"config.clearance_cases[{index}]"
        row = _exact(raw, {
            "id", "scope", "operation", "opening_id", "moving_parts",
            "obstacles", "envelope_basis", "method", "minimum_clearance_mm",
        }, where)
        ident = _identifier(row["id"], f"{where}.id")
        scope = _identifier(row["scope"], f"{where}.scope")
        if scope not in scopes:
            raise V2Error(f"{where}.scope: unknown scope {scope}")
        operation = _identifier(row["operation"], f"{where}.operation")
        if operation not in operations:
            raise V2Error(f"{where}.operation: unknown operation {operation}")
        if operation in operation_cases:
            raise V2Error(
                f"config.clearance_cases: operation {operation} has multiple cases")
        operation_cases[operation] = ident
        _identifier(row["opening_id"], f"{where}.opening_id")
        moving = set(_unique_ids(row["moving_parts"], f"{where}.moving_parts"))
        obstacles = set(_unique_ids(row["obstacles"], f"{where}.obstacles"))
        unknown = (moving | obstacles) - set(parts)
        if unknown:
            raise V2Error(f"{where}: unknown parts {sorted(unknown)}")
        if moving & obstacles:
            raise V2Error(f"{where}: moving parts cannot also be obstacles")
        if moving != set(operations[operation]["moving_parts"]):
            raise V2Error(
                f"{where}.moving_parts: differs from operation {operation}")
        source_state = states[operations[operation]["from_state"]]
        expected_obstacles = set(source_state["present_parts"]) - moving
        if obstacles != expected_obstacles:
            raise V2Error(
                f"{where}.obstacles: must exactly equal every non-moving part "
                f"present in source state; expected={sorted(expected_obstacles)}, "
                f"actual={sorted(obstacles)}")
        basis = _enum(row["envelope_basis"],
                      {"full_part", "conservative_body", "cable_only"},
                      f"{where}.envelope_basis")
        _enum(row["method"], {"linear_sweep_exact", "linear_sweep_envelope"},
              f"{where}.method")
        _number(row["minimum_clearance_mm"],
                f"{where}.minimum_clearance_mm", nonnegative=True)
        for part in moving:
            constraint = cabled.get(part)
            if constraint and not constraint["threading_permitted"] and \
                    basis != "full_part":
                raise V2Error(
                    f"{where}.envelope_basis: no-threading cabled part {part} "
                    "requires full_part, never cable_only or a partial body")
        result[ident] = row
    expected_by_operation = {
        ident: row["clearance_case"] for ident, row in operations.items()}
    if set(operation_cases) != set(expected_by_operation):
        raise V2Error(
            "config.clearance_cases: every linear operation needs exactly one case")
    for operation, case_id in expected_by_operation.items():
        if operation_cases[operation] != case_id:
            raise V2Error(
                f"config clearance operation {operation}: intent names {case_id}, "
                f"config supplies {operation_cases[operation]}")
    return result


def _physical_type(value: Any, where: str) -> str:
    result = _string(value, where)
    if result not in BUILTIN_PHYSICAL_TYPES and not CUSTOM_TEST_RE.fullmatch(result):
        raise V2Error(
            f"{where}: expected a built-in type or namespaced custom.<owner>.<test>")
    return result


def _validate_physical_specs(rows: Any, scopes: Mapping[str, Any],
                             parts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    _row_ids(rows, "config.physical_tests")
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(rows):
        where = f"config.physical_tests[{index}]"
        row = _exact(raw, {"id", "type", "scope", "required_for", "subject_parts"},
                     where)
        ident = _identifier(row["id"], f"{where}.id")
        _physical_type(row["type"], f"{where}.type")
        scope = _identifier(row["scope"], f"{where}.scope")
        if scope not in scopes:
            raise V2Error(f"{where}.scope: unknown scope {scope}")
        _enum(row["required_for"], {"PRINT_VERIFIED", "THERMALLY_VERIFIED"},
              f"{where}.required_for")
        subject_parts = set(_unique_ids(row["subject_parts"],
                                        f"{where}.subject_parts"))
        missing = subject_parts - set(parts)
        if missing:
            raise V2Error(f"{where}.subject_parts: unknown parts {sorted(missing)}")
        result[ident] = row
    return result


def _enforce_physical_obligations(specs: Mapping[str, Mapping[str, Any]],
                                  policy: Mapping[str, Any],
                                  parts: Mapping[str, Any],
                                  cabled: Mapping[str, Any]) -> None:
    """Ensure service and prewired claims acquire physical acceptance tests."""
    by_type: dict[str, list[Mapping[str, Any]]] = {}
    for row in specs.values():
        by_type.setdefault(row["type"], []).append(row)

    def require(test_type: str, subject_parts: set[str]) -> None:
        candidates = [row for row in by_type.get(test_type, [])
                      if row["required_for"] == "PRINT_VERIFIED" and
                      subject_parts.issubset(set(row["subject_parts"]))]
        if not candidates:
            raise V2Error(
                "config.physical_tests: represented service/assembly intent "
                f"requires PRINT_VERIFIED test {test_type} covering "
                f"{sorted(subject_parts)}")

    pcb = next(ident for ident, row in parts.items() if row["role"] == "pcb")
    base = next(ident for ident, row in parts.items() if row["role"] == "base")
    lid = next(ident for ident, row in parts.items() if row["role"] == "lid")
    if policy["pcb_retained_with_lid_removed"]:
        require("lid_off_pcb_retention", {base, pcb})
        require("case_closure_independence", {base, lid, pcb})
    for part, constraint in cabled.items():
        if constraint["cable_pre_attached"] and not constraint["threading_permitted"]:
            require("accessory_insertion_removal", {part})
            require("accessory_retention_rattle", {part})
            require("cable_strain_clearance", {part})


def _collect_hex64(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for item in value.values():
            found.update(_collect_hex64(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_collect_hex64(item))
    elif isinstance(value, str) and HEX64_RE.fullmatch(value):
        found.add(value)
    return found


def _manifest_subjects(path: Path) -> dict[str, str]:
    """Read exact path/hash pairs from structured or legacy manifests.

    PCB releases predate schema v2 and may use an audited ``MANIFEST.txt``
    rather than YAML/JSON. A hash occurring under another path is not authority
    for the selected PCB or STEP.
    """
    try:
        text = read_stable_bytes(
            path, f"release manifest {path}").decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise V2Error(f"cannot read release manifest {path}: {exc}") from exc
    found: dict[str, str] = {}

    def add(raw_path: Any, raw_hash: Any) -> None:
        if not isinstance(raw_path, str) or not isinstance(raw_hash, str) or \
                not HEX64_RE.fullmatch(raw_hash):
            return
        candidate = Path(raw_path)
        if candidate.is_absolute() or "\\" in raw_path or any(
                part in {"", ".", ".."} for part in candidate.parts):
            return
        normalized = candidate.as_posix()
        previous = found.get(normalized)
        if previous is not None and previous != raw_hash:
            raise V2Error(
                f"release manifest contradicts itself for {normalized!r}")
        found[normalized] = raw_hash

    for line in text.splitlines():
        # Historical release streams use both a path-first census and the
        # standard ``sha256sum`` hash-first form.  Accept only the two exact,
        # whitespace-delimited shapes; in either case authority remains bound
        # to the selected relative path as well as the digest.
        path_first = re.match(r"^\s*(\S+)\s+([0-9a-f]{64})\s*$", line)
        if path_first:
            add(path_first.group(1), path_first.group(2))
            continue
        hash_first = re.match(r"^\s*([0-9a-f]{64})\s{2}(\S+)\s*$", line)
        if hash_first:
            add(hash_first.group(2), hash_first.group(1))
    try:
        structured = yaml.load(text, Loader=StrictLoader)
    except yaml.YAMLError:
        structured = None

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            add(value.get("path", value.get("name")), value.get("sha256"))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(structured)
    if not found:
        raise V2Error("release manifest contains no path-bound SHA-256 census")
    return found


def _v1_fastener_bridge(cad_design: Mapping[str, Any],
                        cad_loaded: Mapping[str, Any],
                        fasteners: Mapping[str, Mapping[str, Any]]) -> None:
    """Prove that schema-v2 independent screw roles exist in bound v1 CAD."""
    v1 = cad_design["fasteners"]
    if v1["strategy"] != "separate_perimeter":
        raise V2Error(
            "config.subject.cad_design: schema-v2 independent PCB retention "
            "requires v1 fasteners.strategy=separate_perimeter")
    by_role: dict[str, list[Mapping[str, Any]]] = {
        "board_retention": [], "case_closure": [], "accessory": []}
    for row in fasteners.values():
        by_role[row["role"]].append(row)
    if len(by_role["board_retention"]) != 1 or \
            len(by_role["case_closure"]) != 1:
        raise V2Error(
            "config.fastener_groups: bound v1 CAD requires exactly one "
            "board_retention and one case_closure group")

    interface = cad_loaded["interface"]
    positions: dict[str, list[list[float]]] = {}
    for row in interface["board"]["mounting_holes"]:
        positions.setdefault(row["ref"], []).append(row["position_mm"])
    expected_board: list[tuple[float, float]] = []
    for ref in v1["board_holes"]:
        matches = positions.get(ref, [])
        if len(matches) != 1:
            raise V2Error(
                f"config.subject.cad_design: board fastener ref {ref} is not unique")
        expected_board.append((float(matches[0][0]), float(matches[0][1])))
    expected_case = [(float(row[0]), float(row[1]))
                     for row in v1["case_holes_mm"]]

    def actual_xy(group: Mapping[str, Any], where: str) -> list[tuple[float, float]]:
        result = []
        for axis in group["axes"]:
            direction = _normalize(axis["direction"])
            if abs(direction[0]) > 1e-9 or abs(direction[1]) > 1e-9 or \
                    direction[2] < 1 - 1e-9:
                raise V2Error(f"{where}: v1 adapter screw axes must point +Z")
            result.append((float(axis["origin_mm"][0]),
                           float(axis["origin_mm"][1])))
        return result

    def same_points(actual: Sequence[tuple[float, float]],
                    expected: Sequence[tuple[float, float]]) -> bool:
        if len(actual) != len(expected):
            return False
        remaining = list(expected)
        for point in actual:
            matches = [index for index, candidate in enumerate(remaining)
                       if math.dist(point, candidate) <= 1e-6]
            if len(matches) != 1:
                return False
            remaining.pop(matches[0])
        return not remaining

    board_group = by_role["board_retention"][0]
    case_group = by_role["case_closure"][0]
    if not same_points(actual_xy(board_group, "board_retention group"),
                       expected_board):
        raise V2Error(
            "config.fastener_groups: board_retention axes differ from bound v1 CAD")
    if not same_points(actual_xy(case_group, "case_closure group"), expected_case):
        raise V2Error(
            "config.fastener_groups: case_closure axes differ from bound v1 CAD")
    expected_hardware = {
        "board_retention": {
            "thread": v1["thread"],
            "screw_length_mm": float(v1["screw"]["board_length_mm"]),
            "minimum_engagement_mm": float(
                v1["screw"]["minimum_engagement_mm"]),
            "minimum_tip_clearance_mm": float(
                v1["screw"]["minimum_tip_clearance_mm"]),
        },
        "case_closure": {
            "thread": v1["thread"],
            "screw_length_mm": float(v1["screw"]["lid_length_mm"]),
            "minimum_engagement_mm": float(
                v1["screw"]["minimum_engagement_mm"]),
            "minimum_tip_clearance_mm": float(
                v1["screw"]["minimum_tip_clearance_mm"]),
        },
    }
    for role, group in (("board_retention", board_group),
                        ("case_closure", case_group)):
        if group["hardware"] != expected_hardware[role]:
            raise V2Error(
                f"config.fastener_groups: {role} hardware differs from bound v1 CAD")


def _state_and_motion_cross_checks(intent: Mapping[str, Any],
                                   parts: Mapping[str, Any],
                                   fasteners: Mapping[str, Any],
                                   policy: Mapping[str, Any]) -> None:
    part_ids = set(parts)
    group_ids = set(fasteners)
    installed_part_ids = set(parts)
    pcb = next(ident for ident, row in parts.items() if row["role"] == "pcb")
    lid = next(ident for ident, row in parts.items() if row["role"] == "lid")
    board_groups = {ident for ident, row in fasteners.items()
                    if row["role"] == "board_retention"}
    closure_groups = {ident for ident, row in fasteners.items()
                      if row["role"] == "case_closure"}
    for state in intent["states"]:
        unknown_parts = set(state["present_parts"]) - part_ids
        unknown_groups = set(state["secured_fastener_groups"]) - group_ids
        if unknown_parts:
            raise V2Error(
                f"intent state {state['id']}: unknown parts {sorted(unknown_parts)}")
        if unknown_groups:
            raise V2Error(
                f"intent state {state['id']}: unknown fastener groups "
                f"{sorted(unknown_groups)}")
        if state["pcb_retained"] and pcb not in state["present_parts"]:
            raise V2Error(
                f"intent state {state['id']}: PCB cannot be retained when absent")
        if state["pcb_retained"] and not board_groups.issubset(
                state["secured_fastener_groups"]):
            raise V2Error(
                f"intent state {state['id']}: pcb_retained requires every "
                "board_retention group secured")
        if state["purpose"] == "installed":
            if set(state["present_parts"]) != installed_part_ids:
                raise V2Error(
                    "intent installed state must contain every installed part")
            if not closure_groups.issubset(state["secured_fastener_groups"]):
                raise V2Error(
                    "intent installed state lacks secured case_closure group(s)")
            if set(state["secured_fastener_groups"]) != group_ids:
                raise V2Error(
                    "intent installed state must secure every installed "
                    "fastener group")
        if state["purpose"] == "lid_removed":
            if lid in state["present_parts"]:
                raise V2Error("intent lid_removed state still contains the lid")
            if closure_groups & set(state["secured_fastener_groups"]):
                raise V2Error(
                    "intent lid_removed state still secures case_closure hardware")
            required = policy["pcb_retained_with_lid_removed"]
            if required and (not state["pcb_retained"] or
                             not board_groups.issubset(
                                 state["secured_fastener_groups"])):
                raise V2Error(
                    "intent lid_removed state does not retain the PCB with its "
                    "independent board_retention fasteners")

    for operation in intent["operations"]:
        missing = set(operation["moving_parts"]) - part_ids
        if missing:
            raise V2Error(
                f"intent operation {operation['id']}: unknown parts {sorted(missing)}")


def validate_config_v2(value: Mapping[str, Any], root: Path) -> dict[str, Any]:
    """Validate and cross-bind one complete schema-v2 configuration."""
    top = _exact(value, {
        "schema", "kind", "name", "mode", "subject", "external_subjects",
        "verification_scopes", "installed_parts", "fastener_policy",
        "fastener_groups", "clearance_cases", "physical_tests",
    }, "config")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise V2Error("config.schema: expected 2")
    if top["kind"] != CONFIG_KIND:
        raise V2Error(f"config.kind: expected {CONFIG_KIND!r}")
    name = _identifier(top["name"], "config.name")
    mode = _enum(top["mode"], {"co_design", "derived"}, "config.mode")

    subject = _exact(top["subject"], {
        "release", "release_manifest", "pcb", "step", "interface",
        "mechanical_intent", "cad_design",
    }, "config.subject")
    _string(subject["release"], "config.subject.release")
    bindings: dict[str, Any] = {}
    for field in ("pcb", "step", "interface", "mechanical_intent", "cad_design"):
        bindings[field] = validate_file_binding(
            subject[field], root, f"config.subject.{field}")
    if mode == "derived":
        if subject["release_manifest"] is None:
            raise V2Error(
                "config.subject.release_manifest: required for derived mode")
        bindings["release_manifest"] = validate_file_binding(
            subject["release_manifest"], root,
            "config.subject.release_manifest")
        try:
            manifest_subjects = _manifest_subjects(
                bindings["release_manifest"]["path"])
        except V2Error as exc:
            raise V2Error(
                f"config.subject.release_manifest: invalid manifest: {exc}") from exc
        manifest_root = bindings["release_manifest"]["path"].parent
        absent: list[str] = []
        for field in ("pcb", "step"):
            try:
                relative = bindings[field]["path"].relative_to(
                    manifest_root).as_posix()
            except ValueError:
                absent.append(field)
                continue
            if manifest_subjects.get(relative) != bindings[field]["sha256"]:
                absent.append(field)
        if absent:
            raise V2Error(
                "config.subject.release_manifest: does not bind configured "
                f"subject paths and hashes for {absent}")
    elif subject["release_manifest"] is not None:
        raise V2Error(
            "config.subject.release_manifest: co_design mode must use null")

    intent = validate_mechanical_intent(load_yaml(bindings["mechanical_intent"]["path"]))
    if intent["name"] != name:
        raise V2Error(
            "config.subject.mechanical_intent: intent.name differs from config.name")

    try:
        cad_design, cad_loaded = load_bound_config_v1(
            bindings["cad_design"]["path"], root)
    except V1EnclosureError as exc:
        raise V2Error(f"config.subject.cad_design: invalid bound v1 design: {exc}") \
            from exc
    if cad_design["name"] != name:
        raise V2Error(
            "config.subject.cad_design: v1 config.name differs from v2 config.name")
    if cad_design["mode"] != mode:
        raise V2Error(
            "config.subject.cad_design: v1/v2 modes differ")
    if cad_design["subject"]["release"] != subject["release"]:
        raise V2Error(
            "config.subject.cad_design: v1/v2 release identifiers differ")
    for field in ("release_manifest", "pcb", "step", "interface"):
        if cad_design["subject"].get(field) != subject[field]:
            raise V2Error(
                f"config.subject.cad_design: v1/v2 {field} bindings differ")

    external, external_bindings = _validate_external_subjects(
        top["external_subjects"], root)
    bindings["external_subjects"] = external_bindings
    scopes = _validate_scopes(top["verification_scopes"])
    parts = _validate_installed_parts(top["installed_parts"], scopes, external)
    policy = _exact(top["fastener_policy"], {
        "axis_disjoint_tolerance_mm", "pcb_retained_with_lid_removed",
    }, "config.fastener_policy")
    _number(policy["axis_disjoint_tolerance_mm"],
            "config.fastener_policy.axis_disjoint_tolerance_mm", positive=True)
    _boolean(policy["pcb_retained_with_lid_removed"],
             "config.fastener_policy.pcb_retained_with_lid_removed")
    if not policy["pcb_retained_with_lid_removed"]:
        raise V2Error(
            "config.fastener_policy.pcb_retained_with_lid_removed: schema v2 "
            "requires true")
    if policy["pcb_retained_with_lid_removed"] != \
            intent["requirements"]["pcb_retained_with_lid_removed"]:
        raise V2Error(
            "config/intent disagree on pcb_retained_with_lid_removed")
    fasteners = _validate_fasteners(top["fastener_groups"], policy, parts)
    _v1_fastener_bridge(cad_design, cad_loaded, fasteners)

    operation_map = {row["id"]: row for row in intent["operations"]}
    state_map = {row["id"]: row for row in intent["states"]}
    cabled = {row["part"]: row
              for row in intent["requirements"]["cabled_parts"]}
    clearances = _validate_clearance_cases(
        top["clearance_cases"], scopes, parts, operation_map, cabled, state_map)
    physical = _validate_physical_specs(top["physical_tests"], scopes, parts)
    _enforce_physical_obligations(physical, policy, parts, cabled)
    _state_and_motion_cross_checks(intent, parts, fasteners, policy)

    for unknown in intent["unknowns"]:
        if unknown["scope"] not in scopes:
            raise V2Error(
                f"intent unknown {unknown['id']}: scope {unknown['scope']} absent")
    for cabled_part in cabled:
        if cabled_part not in parts:
            raise V2Error(
                f"intent cabled part {cabled_part}: absent from installed parts")

    ceilings = scope_readiness_ceilings(
        scopes, parts, external, intent["unknowns"])
    return {
        "config": dict(value),
        "intent": intent,
        "cad_design": cad_design,
        "cad_design_loaded": cad_loaded,
        "bindings": bindings,
        "scopes": scopes,
        "parts": parts,
        "fastener_groups": fasteners,
        "clearance_cases": clearances,
        "physical_tests": physical,
        "scope_readiness_ceilings": ceilings,
    }


def scope_readiness_ceilings(scopes: Mapping[str, Any],
                             parts: Mapping[str, Any],
                             external: Mapping[str, Any],
                             unknowns: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    """Return conservative per-scope ceilings imposed by authority/unknowns."""
    ceilings = {ident: "THERMALLY_VERIFIED" for ident in scopes}

    def lower(scope: str, status: str) -> None:
        current = ceilings[scope]
        if status == "INCOMPLETE" or (
                current != "INCOMPLETE" and
                READINESS_RANK[status] < READINESS_RANK[current]):
            ceilings[scope] = status

    for part in parts.values():
        source = part["source"]
        if source["kind"] != "external_subject":
            continue
        grade = external[source["id"]]["authority"]["grade"]
        ceiling = {
            "vendor_authoritative": "THERMALLY_VERIFIED",
            "measured_unit": "THERMALLY_VERIFIED",
            "derived_measurement": "CAD_READY",
            "conservative_candidate": "CAD_READY",
            "inspiration_only": "INCOMPLETE",
        }[grade]
        for scope in part["scopes"]:
            lower(scope, ceiling)
    for unknown in unknowns:
        blocker = unknown["blocks_readiness"]
        ceiling = {
            "CAD_READY": "INCOMPLETE",
            "PRINT_VERIFIED": "CAD_READY",
            "THERMALLY_VERIFIED": "PRINT_VERIFIED",
        }[blocker]
        lower(unknown["scope"], ceiling)
    return ceilings


def aggregate_status(scope_statuses: Mapping[str, str],
                     required_scopes: Iterable[str],
                     *, ceilings: Mapping[str, str] | None = None) -> str:
    """Conservatively aggregate required scopes; FAIL and unknowns dominate."""
    required = list(required_scopes)
    if len(required) != len(set(required)):
        raise V2Error("required_scopes: duplicate scope")
    if not required:
        raise V2Error("required_scopes: denominator is zero")
    unknown_rows = set(scope_statuses) - set(required)
    if unknown_rows:
        raise V2Error(f"scope_statuses: undeclared scopes {sorted(unknown_rows)}")
    for scope, status in scope_statuses.items():
        if status not in RESULT_STATUSES:
            raise V2Error(f"scope {scope}: invalid status {status!r}")
    if ceilings is not None:
        unknown_ceilings = set(ceilings) - set(required)
        if unknown_ceilings:
            raise V2Error(
                f"ceilings: undeclared scopes {sorted(unknown_ceilings)}")
        for scope, ceiling in ceilings.items():
            if ceiling not in READINESS:
                raise V2Error(f"scope {scope}: invalid ceiling {ceiling!r}")
    missing = set(required) - set(scope_statuses)
    if missing:
        return "INCOMPLETE"
    statuses = []
    for scope in required:
        status = scope_statuses[scope]
        if status == "FAIL":
            return "FAIL"
        ceiling = ceilings.get(scope) if ceilings is not None else None
        if ceiling is not None:
            if ceiling == "INCOMPLETE":
                status = "INCOMPLETE"
            elif status != "INCOMPLETE" and \
                    READINESS_RANK[status] > READINESS_RANK[ceiling]:
                status = ceiling
        statuses.append(status)
    if "INCOMPLETE" in statuses:
        return "INCOMPLETE"
    return min(statuses, key=lambda status: READINESS_RANK[status])


def required_scope_closure(scopes: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Return required scopes plus every transitive dependency."""
    required = {ident for ident, row in scopes.items() if row["required"]}
    pending = list(required)
    while pending:
        ident = pending.pop()
        for dependency in scopes[ident]["depends_on"]:
            if dependency not in required:
                required.add(dependency)
                pending.append(dependency)
    return [ident for ident in scopes if ident in required]


def validate_physical_evidence_v2(value: Mapping[str, Any],
                                  loaded: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an exact, extensible v2 physical-test census."""
    top = _exact(value, {"schema", "kind", "config_semantic_sha256", "tests"},
                 "physical_evidence")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise V2Error("physical_evidence.schema: expected 2")
    if top["kind"] != PHYSICAL_KIND:
        raise V2Error(f"physical_evidence.kind: expected {PHYSICAL_KIND!r}")
    digest = _string(top["config_semantic_sha256"],
                     "physical_evidence.config_semantic_sha256")
    if not HEX64_RE.fullmatch(digest):
        raise V2Error(
            "physical_evidence.config_semantic_sha256: expected lowercase 64-hex")
    expected_hash = semantic_sha256(loaded["config"])
    if digest != expected_hash:
        raise V2Error("physical evidence is stale for this v2 config")
    evidence_ids = _row_ids(top["tests"], "physical_evidence.tests")
    specs = loaded["physical_tests"]
    if evidence_ids != set(specs):
        raise V2Error(
            "physical_evidence.tests: census differs; "
            f"missing={sorted(set(specs) - evidence_ids)}, "
            f"unknown={sorted(evidence_ids - set(specs))}")
    normalized: dict[str, Any] = {}
    failed: list[str] = []
    pending: list[str] = []
    for index, raw in enumerate(top["tests"]):
        where = f"physical_evidence.tests[{index}]"
        row = _exact(raw, {"id", "type", "scope", "status", "evidence"}, where)
        ident = _identifier(row["id"], f"{where}.id")
        _physical_type(row["type"], f"{where}.type")
        _identifier(row["scope"], f"{where}.scope")
        status = _enum(row["status"], {"PASS", "FAIL", "NOT_RUN"},
                       f"{where}.status")
        evidence = _string(row["evidence"], f"{where}.evidence")
        spec = specs[ident]
        if row["type"] != spec["type"] or row["scope"] != spec["scope"]:
            raise V2Error(
                f"{where}: type/scope differs from config physical-test spec")
        if status == "FAIL":
            failed.append(ident)
        elif status == "NOT_RUN":
            pending.append(ident)
        normalized[ident] = {"status": status, "evidence": evidence,
                             "required_for": spec["required_for"]}
    if failed:
        status = "FAIL"
    else:
        print_rows = [ident for ident, spec in specs.items()
                      if spec["required_for"] == "PRINT_VERIFIED"]
        thermal_rows = [ident for ident, spec in specs.items()
                        if spec["required_for"] == "THERMALLY_VERIFIED"]
        print_ok = all(normalized[ident]["status"] == "PASS"
                       for ident in print_rows)
        thermal_ok = all(normalized[ident]["status"] == "PASS"
                         for ident in thermal_rows)
        if print_ok and thermal_ok and thermal_rows:
            status = "THERMALLY_VERIFIED"
        elif print_ok:
            status = "PRINT_VERIFIED"
        else:
            status = "INCOMPLETE"
    return {"status": status, "failed": failed, "pending": pending,
            "tests": normalized}


def _binding_for_report(binding: Any) -> Any:
    if isinstance(binding, Mapping):
        return {key: _binding_for_report(value) for key, value in binding.items()}
    if isinstance(binding, Path):
        return str(binding)
    return binding


def _write_or_print(value: Mapping[str, Any], output: Path | None,
                    *, inputs: Iterable[Path] = ()) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(payload)
    else:
        try:
            with atomic_output(output, where="schema-v2 report",
                               inputs=inputs) as (_, stream):
                stream.write(payload.encode("utf-8"))
        except V1EnclosureError as exc:
            raise V2Error(str(exc)) from exc


def _bound_input_paths(loaded: Mapping[str, Any]) -> list[Path]:
    """Collect every reopened file so reports cannot overwrite an authority."""
    result: list[Path] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)
        elif isinstance(value, Path):
            result.append(value)

    walk(loaded.get("bindings", {}))
    return result


def _cli_validate_config(args: argparse.Namespace) -> int:
    raw = load_yaml(args.config)
    loaded = validate_config_v2(raw, args.root)
    report = {
        "schema": 2,
        "kind": VALIDATION_KIND,
        "status": "VALID",
        "config_semantic_sha256": semantic_sha256(raw),
        "bindings": _binding_for_report(loaded["bindings"]),
        "scope_readiness_ceilings": loaded["scope_readiness_ceilings"],
    }
    _write_or_print(
        report, args.output,
        inputs=[args.config, *_bound_input_paths(loaded)])
    return 0


def _cli_validate_intent(args: argparse.Namespace) -> int:
    raw = load_yaml(args.intent)
    validate_mechanical_intent(raw)
    _write_or_print({
        "schema": 2, "kind": VALIDATION_KIND, "status": "VALID",
        "intent_semantic_sha256": semantic_sha256(raw),
    }, args.output, inputs=[args.intent])
    return 0


def _cli_validate_evidence(args: argparse.Namespace) -> int:
    raw_config = load_yaml(args.config)
    loaded = validate_config_v2(raw_config, args.root)
    summary = validate_physical_evidence_v2(load_yaml(args.evidence), loaded)
    _write_or_print(
        {"schema": 2, "kind": VALIDATION_KIND, **summary}, args.output,
        inputs=[args.evidence, args.config, *_bound_input_paths(loaded)])
    return 1 if summary["status"] == "FAIL" else 0


def _cli_aggregate(args: argparse.Namespace) -> int:
    raw = load_json(args.input)
    top = _exact(raw, {"required_scopes", "scope_statuses", "ceilings"},
                 "aggregate_input")
    required = _unique_ids(top["required_scopes"],
                           "aggregate_input.required_scopes")
    statuses = _mapping(top["scope_statuses"], "aggregate_input.scope_statuses")
    ceilings = _mapping(top["ceilings"], "aggregate_input.ceilings")
    status = aggregate_status(statuses, required, ceilings=ceilings)
    _write_or_print({"schema": 2, "kind": VALIDATION_KIND, "status": status},
                    args.output, inputs=[args.input])
    return 1 if status == "FAIL" else 0


def _cli_aggregate_config(args: argparse.Namespace) -> int:
    raw = load_json(args.input)
    top = _exact(raw, {"scope_statuses"}, "aggregate_config_input")
    loaded = validate_config_v2(load_yaml(args.config), args.root)
    required = required_scope_closure(loaded["scopes"])
    statuses = _mapping(top["scope_statuses"],
                        "aggregate_config_input.scope_statuses")
    status = aggregate_status(
        statuses, required, ceilings=loaded["scope_readiness_ceilings"])
    _write_or_print({
        "schema": 2,
        "kind": VALIDATION_KIND,
        "status": status,
        "required_scopes": required,
        "scope_readiness_ceilings": loaded["scope_readiness_ceilings"],
    }, args.output,
        inputs=[args.input, args.config, *_bound_input_paths(loaded)])
    if status == "FAIL":
        return 1
    if status == "INCOMPLETE":
        return 2
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate pcb-enclosure mechanical schema v2 contracts")
    sub = parser.add_subparsers(dest="command", required=True)

    intent = sub.add_parser("validate-intent", help="validate mechanical intent")
    intent.add_argument("intent", type=Path)
    intent.add_argument("--output", type=Path)
    intent.set_defaults(func=_cli_validate_intent)

    config = sub.add_parser("validate-config", help="validate and bind v2 config")
    config.add_argument("config", type=Path)
    config.add_argument("--root", type=Path, required=True)
    config.add_argument("--output", type=Path)
    config.set_defaults(func=_cli_validate_config)

    evidence = sub.add_parser("validate-evidence", help="validate v2 physical evidence")
    evidence.add_argument("evidence", type=Path)
    evidence.add_argument("--config", type=Path, required=True)
    evidence.add_argument("--root", type=Path, required=True)
    evidence.add_argument("--output", type=Path)
    evidence.set_defaults(func=_cli_validate_evidence)

    aggregate = sub.add_parser(
        "aggregate",
        help="diagnostic aggregate with caller-supplied applicability/ceilings")
    aggregate.add_argument("input", type=Path)
    aggregate.add_argument("--output", type=Path)
    aggregate.set_defaults(func=_cli_aggregate)

    aggregate_config = sub.add_parser(
        "aggregate-config",
        help="authoritatively aggregate scopes/ceilings from a validated config")
    aggregate_config.add_argument("input", type=Path)
    aggregate_config.add_argument("--config", type=Path, required=True)
    aggregate_config.add_argument("--root", type=Path, required=True)
    aggregate_config.add_argument("--output", type=Path)
    aggregate_config.set_defaults(func=_cli_aggregate_config)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except V2Error as exc:
        print(f"PCB ENCLOSURE V2 FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
