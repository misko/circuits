#!/usr/bin/env python3
"""Compile source-only board facts into one pre-route authority mapping.

This module is deliberately independent of :mod:`pcbnew`.  Callers extract
live refs/nets/MPNs and, when useful, KiCad layer IDs at their own boundary;
the core below validates and composes only ordinary Python data.

The canonical stack input is ``stackup-v1``.  Its ``copper`` list is physical
top-to-bottom order and is the *only* ordering authority.  KiCad numeric layer
IDs are identities, never sortable stack positions.  The other inputs are
closed, versioned source-fact schemas so a topology or stack migration cannot
silently inherit a field this compiler does not understand.

``compile_source_prep_authority`` returns a deterministic,
hash-bound ``source-prep-authority-v1`` mapping.  ``write_authority`` and
``reopen_authority`` provide relocatable serialization and same-input/tamper
verification.  ``adapt_legacy_stack`` exists only to prepare an authored
migration: its result is explicitly non-authoritative and is not accepted by
the compiler.
"""
from __future__ import annotations

import copy
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping, Sequence


STACK_SCHEMA = "stackup-v1"
OBSERVED_SCHEMA = "observed-source-facts-v1"
MIGRATION_SCHEMA = "topology-migration-v1"
ROUTE_SCHEMA = "route-plan-v1"
AUTHORITY_SCHEMA = "source-prep-authority-v1"
LEGACY_ADAPTER_SCHEMA = "legacy-stack-adapter-v1"
LEGACY_AUTHORITY_DIAGNOSTIC_SCHEMA = \
    "legacy-source-prep-authority-diagnostic-v1"
STACK_ROLE_OWNER = "board_authority.py:stackup-v1"
LEGACY_AUTHORITY = "NON_AUTHORITATIVE"

SEMANTIC_ROLES = frozenset({
    "signal", "reference_plane", "power", "mixed",
})
ROUTABLE_ROLES = frozenset({"signal", "mixed"})
VIA_KINDS = frozenset({"through", "blind", "buried", "microvia"})
FACT_KINDS = ("refs", "nets", "mpns")


class AuthoritySchemaError(ValueError):
    """An authored mapping is not a closed supported schema."""


class AuthorityVerificationError(ValueError):
    """A reopened receipt or its expected inputs failed hash verification."""


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuthoritySchemaError(f"{where} must be a mapping")
    return value


def _closed(value: Mapping[str, Any], allowed: set[str], where: str) -> None:
    non_strings = [key for key in value if not isinstance(key, str)]
    if non_strings:
        raise AuthoritySchemaError(
            f"{where} keys must be strings, got {non_strings!r}")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise AuthoritySchemaError(f"{where} has unknown key(s): {unknown}")


def _nonempty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthoritySchemaError(f"{where} must be a non-empty string")
    return value.strip()


def _positive_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AuthoritySchemaError(f"{where} must be a positive number")
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise AuthoritySchemaError(f"{where} must be a positive finite number")
    return result


def _string_list(value: Any, where: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise AuthoritySchemaError(f"{where} must be a list")
    result = [_nonempty_string(item, f"{where}[{index}]")
              for index, item in enumerate(value)]
    if nonempty and not result:
        raise AuthoritySchemaError(f"{where} must not be empty")
    if len(result) != len(set(result)):
        raise AuthoritySchemaError(f"{where} contains duplicate values")
    return result


def _named_items(value: Any, where: str) -> list[tuple[str, Any]]:
    """Validate free-form mapping keys and reject trim-normalization collisions."""
    source = _mapping(value, where)
    normalized: dict[str, Any] = {}
    origins: dict[str, Any] = {}
    for raw_name, item in source.items():
        name = _nonempty_string(raw_name, f"{where} key")
        if name in normalized:
            raise AuthoritySchemaError(
                f"{where} keys {origins[name]!r} and {raw_name!r} normalize "
                f"to duplicate {name!r}")
        normalized[name] = item
        origins[name] = raw_name
    return [(name, normalized[name]) for name in sorted(normalized)]


def _canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise AuthoritySchemaError(f"value is not canonical JSON data: {exc}") from exc
    return text.encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return the SHA-256 of the repository's canonical JSON representation."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _finding(code: str, subject: str, message: str) -> dict[str, str]:
    return {"code": code, "subject": subject, "message": message}


def _sort_findings(rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (str(row["code"]), str(row["subject"]), str(row["message"]))
        unique[key] = {"code": key[0], "subject": key[1], "message": key[2]}
    return [unique[key] for key in sorted(unique)]


# ------------------------------------------------------------------ stack --

def normalize_stack_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize a closed ``stackup-v1`` mapping.

    The order of ``copper`` is preserved exactly because it is physical
    authority.  Maps and set-like lists are normalized for deterministic
    hashing.  Semantic contradictions (for example routing on a plane layer)
    are reported by :func:`resolve_routing_classes`; malformed/unknown fields
    fail here.
    """
    source = _mapping(contract, "stack")
    if source.get("schema") != STACK_SCHEMA:
        raise AuthoritySchemaError(
            f"stack.schema must be {STACK_SCHEMA!r}; legacy adapters are not authority")
    _closed(source, {"schema", "copper", "routing_classes", "via_families"},
            "stack")

    raw_copper = source.get("copper")
    if not isinstance(raw_copper, list) or len(raw_copper) < 2:
        raise AuthoritySchemaError("stack.copper must contain at least two ordered rows")
    copper: list[dict[str, Any]] = []
    names: list[str] = []
    for index, raw in enumerate(raw_copper):
        row = _mapping(raw, f"stack.copper[{index}]")
        _closed(row, {"name", "thickness_um", "role", "plane_net"},
                f"stack.copper[{index}]")
        name = _nonempty_string(row.get("name"), f"stack.copper[{index}].name")
        role = _nonempty_string(row.get("role"), f"stack.copper[{index}].role")
        if role not in SEMANTIC_ROLES:
            raise AuthoritySchemaError(
                f"stack.copper[{index}].role must be one of {sorted(SEMANTIC_ROLES)}")
        item: dict[str, Any] = {
            "name": name,
            "thickness_um": _positive_number(
                row.get("thickness_um"), f"stack.copper[{index}].thickness_um"),
            "role": role,
        }
        if "plane_net" in row:
            item["plane_net"] = _nonempty_string(
                row["plane_net"], f"stack.copper[{index}].plane_net")
        copper.append(item)
        names.append(name)
    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        raise AuthoritySchemaError(
            f"stack.copper assigns multiple physical positions/roles to {duplicates}")
    if names[0] != "F.Cu" or names[-1] != "B.Cu":
        raise AuthoritySchemaError(
            "stack.copper physical order must begin F.Cu and end B.Cu")

    raw_classes = source.get("routing_classes", {})
    classes: dict[str, Any] = {}
    for name, raw_value in _named_items(raw_classes, "stack.routing_classes"):
        raw = _mapping(raw_value, f"stack.routing_classes.{name}")
        _closed(raw, {"allowed_layers", "references", "reference_required"},
                f"stack.routing_classes.{name}")
        allowed = _string_list(raw.get("allowed_layers"),
                               f"stack.routing_classes.{name}.allowed_layers",
                               nonempty=True)
        references: dict[str, str] = {}
        for source_layer, reference_value in _named_items(
                raw.get("references", {}),
                f"stack.routing_classes.{name}.references"):
            references[source_layer] = _nonempty_string(
                reference_value,
                f"stack.routing_classes.{name}.references.{source_layer}")
        reference_required = raw.get("reference_required", False)
        if not isinstance(reference_required, bool):
            raise AuthoritySchemaError(
                f"stack.routing_classes.{name}.reference_required must be boolean")
        classes[name] = {"allowed_layers": sorted(allowed, key=names.index)
                         if set(allowed) <= set(names) else sorted(allowed),
                         "references": references,
                         "reference_required": reference_required}

    raw_families = source.get("via_families", {})
    families: dict[str, Any] = {}
    for name, raw_value in _named_items(raw_families, "stack.via_families"):
        raw = _mapping(raw_value, f"stack.via_families.{name}")
        _closed(raw, {"from_layer", "to_layer", "kind"},
                f"stack.via_families.{name}")
        item = {
            "from_layer": _nonempty_string(
                raw.get("from_layer"), f"stack.via_families.{name}.from_layer"),
            "to_layer": _nonempty_string(
                raw.get("to_layer"), f"stack.via_families.{name}.to_layer"),
        }
        if "kind" in raw:
            kind = _nonempty_string(raw["kind"],
                                    f"stack.via_families.{name}.kind")
            if kind not in VIA_KINDS:
                raise AuthoritySchemaError(
                    f"stack.via_families.{name}.kind must be one of {sorted(VIA_KINDS)}")
            item["kind"] = kind
        families[name] = item

    return {"schema": STACK_SCHEMA, "copper": copper,
            "routing_classes": classes, "via_families": families}


def physical_copper_order(
        contract: Mapping[str, Any],
        numeric_layer_ids: Mapping[str, int] | None = None) -> tuple[str, ...]:
    """Return physical top-to-bottom copper names.

    ``numeric_layer_ids`` is accepted solely to validate an extracted KiCad
    identity map.  It can never affect ordering; notably IDs
    ``F=0, B=2, In1=4, In2=6`` still produce ``F, In1, In2, B``.
    """
    stack = normalize_stack_contract(contract)
    order = tuple(row["name"] for row in stack["copper"])
    if numeric_layer_ids is not None:
        ids = dict(_named_items(numeric_layer_ids, "numeric_layer_ids"))
        missing = sorted(set(order) - set(ids))
        extra = sorted(set(ids) - set(order))
        if missing or extra:
            raise AuthoritySchemaError(
                f"numeric_layer_ids must cover the exact copper stack; "
                f"missing={missing}, extra={extra}")
        values = []
        for name in order:
            value = ids[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise AuthoritySchemaError(f"numeric_layer_ids.{name} must be an integer")
            values.append(value)
        if len(values) != len(set(values)):
            raise AuthoritySchemaError("numeric_layer_ids contains duplicate identities")
    return order


def physical_via_span(contract: Mapping[str, Any], from_layer: str,
                      to_layer: str) -> tuple[str, ...]:
    """Return the inclusive via span in physical top-to-bottom order."""
    order = physical_copper_order(contract)
    try:
        first, second = order.index(from_layer), order.index(to_layer)
    except ValueError as exc:
        raise AuthoritySchemaError(
            f"via endpoints must name copper layers in {list(order)}") from exc
    if first == second:
        raise AuthoritySchemaError("a via must span two distinct copper layers")
    low, high = sorted((first, second))
    return order[low:high + 1]


def _adjacent_reference(stack: Mapping[str, Any], layer: str) -> str | None:
    copper = stack["copper"]
    names = [row["name"] for row in copper]
    index = names.index(layer)
    candidates = [copper[pos] for pos in (index - 1, index + 1)
                  if 0 <= pos < len(copper)
                  and copper[pos]["role"] == "reference_plane"
                  and copper[pos].get("plane_net")]
    return candidates[0]["name"] if len(candidates) == 1 else None


def resolve_routing_classes(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve allowed layers and declared/unambiguous adjacent references."""
    stack = normalize_stack_contract(contract)
    copper = {row["name"]: row for row in stack["copper"]}
    names = [row["name"] for row in stack["copper"]]
    findings: list[dict[str, str]] = []

    for row in stack["copper"]:
        role, plane_net = row["role"], row.get("plane_net")
        if role in {"reference_plane", "power"} and not plane_net:
            findings.append(_finding(
                "S-PLANE-NET-MISSING", row["name"],
                f"semantic role {role} requires an explicit plane_net"))
        if role in ROUTABLE_ROLES and plane_net:
            findings.append(_finding(
                "S-PLANE-NET-CONFLICT", row["name"],
                f"routable role {role} conflicts with plane_net {plane_net!r}"))

    resolved: dict[str, Any] = {}
    for class_name, spec in stack["routing_classes"].items():
        legal: list[str] = []
        references: dict[str, Any] = {}
        for layer in spec["allowed_layers"]:
            if layer not in copper:
                findings.append(_finding(
                    "S-LAYER-UNKNOWN", f"{class_name}:{layer}",
                    "routing class names a layer absent from the physical stack"))
                continue
            if copper[layer]["role"] not in ROUTABLE_ROLES:
                findings.append(_finding(
                    "S-ROLE-CONFLICT", f"{class_name}:{layer}",
                    f"routing is not permitted on semantic role {copper[layer]['role']}"))
                continue
            legal.append(layer)

        for signal_layer, reference_layer in spec["references"].items():
            subject = f"{class_name}:{signal_layer}->{reference_layer}"
            if signal_layer not in spec["allowed_layers"]:
                findings.append(_finding(
                    "S-REFERENCE-SOURCE", subject,
                    "reference source is not an allowed layer for the class"))
                continue
            if signal_layer not in copper or reference_layer not in copper:
                findings.append(_finding(
                    "S-REFERENCE-UNKNOWN", subject,
                    "reference relationship names a layer absent from the stack"))
                continue
            reference = copper[reference_layer]
            if reference["role"] != "reference_plane":
                findings.append(_finding(
                    "S-REFERENCE-ROLE", subject,
                    f"target role is {reference['role']}, not reference_plane"))
                continue
            if not reference.get("plane_net"):
                findings.append(_finding(
                    "S-REFERENCE-NET", subject,
                    "reference plane has no explicit plane_net"))
                continue
            if abs(names.index(signal_layer) - names.index(reference_layer)) != 1:
                findings.append(_finding(
                    "S-REFERENCE-NONADJACENT", subject,
                    "ordinary reference mapping must cross one physical dielectric"))
                continue
            references[signal_layer] = {
                "layer": reference_layer, "net": reference["plane_net"],
                "source": "declared",
            }

        unresolved: list[str] = []
        for layer in legal:
            if layer in references:
                continue
            if layer in spec["references"]:
                unresolved.append(layer)
                continue
            adjacent = _adjacent_reference(stack, layer)
            if adjacent is None:
                unresolved.append(layer)
                continue
            references[layer] = {
                "layer": adjacent, "net": copper[adjacent]["plane_net"],
                "source": "adjacent-role",
            }
        if spec["reference_required"]:
            findings.extend(_finding(
                "S-REFERENCE-REQUIRED", f"{class_name}:{layer}",
                "routing class explicitly requires an adjacent reference, "
                "but none resolved") for layer in unresolved)
        resolved[class_name] = {
            "allowed_layers": sorted(legal, key=names.index),
            "references": {key: references[key]
                           for key in sorted(references, key=names.index)},
            "unresolved_references": sorted(unresolved, key=names.index),
            "reference_required": spec["reference_required"],
        }

    return {
        "classes": resolved,
        "findings": _sort_findings(findings),
        "coverage": {"routing_classes": len(resolved),
                     "allowed_layer_uses": sum(
                         len(row["allowed_layers"]) for row in resolved.values()),
                     "reference_mappings": sum(
                         len(row["references"]) for row in resolved.values())},
    }


def _resolve_via_families(stack: Mapping[str, Any]) -> dict[str, Any]:
    order = [row["name"] for row in stack["copper"]]
    findings: list[dict[str, str]] = []
    resolved: dict[str, Any] = {}
    for name, spec in stack["via_families"].items():
        start, end = spec["from_layer"], spec["to_layer"]
        if start not in order or end not in order or start == end:
            findings.append(_finding(
                "S-VIA-ENDPOINT", name,
                f"via endpoints {start!r}/{end!r} do not name two stack layers"))
            continue
        low, high = sorted((order.index(start), order.index(end)))
        span = order[low:high + 1]
        kind = spec.get("kind")
        touches = {low, high}.intersection({0, len(order) - 1})
        valid_kind = True
        if kind == "through" and (low != 0 or high != len(order) - 1):
            valid_kind = False
        elif kind == "blind" and len(touches) != 1:
            valid_kind = False
        elif kind == "buried" and touches:
            valid_kind = False
        elif kind == "microvia" and high - low != 1:
            valid_kind = False
        if not valid_kind:
            findings.append(_finding(
                "S-VIA-KIND", name,
                f"declared kind {kind!r} conflicts with physical span {span}"))
        resolved[name] = {
            **spec, "layers": span, "copper_layer_count": len(span),
            "physical_edge_count": len(span) - 1,
        }
    return {"families": resolved, "findings": _sort_findings(findings)}


# --------------------------------------------------------------- topology --

def normalize_observed_facts(observed: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(observed, "observed")
    _closed(source, {"schema", "refs", "nets", "mpns", "occurrences"},
            "observed")
    if source.get("schema") != OBSERVED_SCHEMA:
        raise AuthoritySchemaError(f"observed.schema must be {OBSERVED_SCHEMA!r}")
    result: dict[str, Any] = {"schema": OBSERVED_SCHEMA}
    for kind in FACT_KINDS:
        result[kind] = sorted(_string_list(source.get(kind, []),
                                                  f"observed.{kind}"))
    occurrences_raw = source.get("occurrences", [])
    if not isinstance(occurrences_raw, list):
        raise AuthoritySchemaError("observed.occurrences must be a list")
    occurrences: list[dict[str, str]] = []
    singular = {"ref": "refs", "net": "nets", "mpn": "mpns"}
    for index, raw in enumerate(occurrences_raw):
        row = _mapping(raw, f"observed.occurrences[{index}]")
        _closed(row, {"kind", "value", "source", "scope"},
                f"observed.occurrences[{index}]")
        kind = _nonempty_string(row.get("kind"),
                                f"observed.occurrences[{index}].kind")
        if kind not in singular:
            raise AuthoritySchemaError(
                f"observed.occurrences[{index}].kind must be ref/net/mpn")
        scope = _nonempty_string(row.get("scope"),
                                 f"observed.occurrences[{index}].scope")
        if scope not in {"live", "historical"}:
            raise AuthoritySchemaError(
                f"observed.occurrences[{index}].scope must be live or historical")
        item = {"kind": kind,
                "value": _nonempty_string(
                    row.get("value"), f"observed.occurrences[{index}].value"),
                "source": _nonempty_string(
                    row.get("source"), f"observed.occurrences[{index}].source"),
                "scope": scope}
        occurrences.append(item)
        if scope == "live" and item["value"] not in result[singular[kind]]:
            result[singular[kind]].append(item["value"])
            result[singular[kind]].sort()
    result["occurrences"] = sorted(
        occurrences, key=lambda row: (row["scope"], row["kind"],
                                      row["value"], row["source"]))
    return result


def normalize_topology_migration(
        declaration: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if declaration is None:
        return None
    source = _mapping(declaration, "migration")
    _closed(source, {"schema", "id", "why", "remove", "add"}, "migration")
    if source.get("schema") != MIGRATION_SCHEMA:
        raise AuthoritySchemaError(f"migration.schema must be {MIGRATION_SCHEMA!r}")
    result: dict[str, Any] = {
        "schema": MIGRATION_SCHEMA,
        "id": _nonempty_string(source.get("id"), "migration.id"),
        "why": _nonempty_string(source.get("why"), "migration.why"),
    }
    total = 0
    for direction in ("remove", "add"):
        raw = _mapping(source.get(direction, {}), f"migration.{direction}")
        _closed(raw, set(FACT_KINDS), f"migration.{direction}")
        result[direction] = {}
        for kind in FACT_KINDS:
            values = sorted(_string_list(raw.get(kind, []),
                                         f"migration.{direction}.{kind}"))
            result[direction][kind] = values
            total += len(values)
    if total == 0:
        raise AuthoritySchemaError("migration must declare at least one delta item")
    for kind in FACT_KINDS:
        overlap = sorted(set(result["remove"][kind]) & set(result["add"][kind]))
        if overlap:
            raise AuthoritySchemaError(
                f"migration cannot add and remove the same {kind}: {overlap}")
    return result


def reconcile_topology_migration(
        declaration: Mapping[str, Any] | None,
        observed: Mapping[str, Any]) -> dict[str, Any]:
    """Reconcile only declared add/remove deltas against live observations.

    Unmentioned live population is intentionally permitted: this is a delta
    contract, not a second full BOM/netlist.  Occurrences explicitly scoped
    ``historical`` never become live refs/nets/MPNs and are reported only in
    coverage.
    """
    facts = normalize_observed_facts(observed)
    migration = normalize_topology_migration(declaration)
    historical = [row for row in facts["occurrences"]
                  if row["scope"] == "historical"]
    if migration is None:
        return {"status": "N-A", "id": None, "findings": [],
                "historical_occurrences_excluded": historical,
                "coverage": {"delta_items": 0,
                             "historical_occurrences_excluded": len(historical)}}

    findings: list[dict[str, str]] = []
    checked = 0
    for kind in FACT_KINDS:
        live = set(facts[kind])
        singular = kind[:-1] if kind != "mpns" else "mpn"
        for value in migration["remove"][kind]:
            checked += 1
            if value in live:
                findings.append(_finding(
                    "M-REMNANT", f"{singular}:{value}",
                    "declared removed topology fact remains live"))
        for value in migration["add"][kind]:
            checked += 1
            if value not in live:
                findings.append(_finding(
                    "M-ADDED-MISSING", f"{singular}:{value}",
                    "declared added topology fact is absent from live observations"))
    findings = _sort_findings(findings)
    return {
        "status": "FAIL" if findings else "PASS",
        "id": migration["id"], "findings": findings,
        "historical_occurrences_excluded": historical,
        "coverage": {"delta_items": checked,
                     "historical_occurrences_excluded": len(historical)},
    }


# ------------------------------------------------------------------ waves --

def normalize_route_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(plan, "route_plan")
    _closed(source, {"schema", "groups", "waves", "exclusions",
                     "deterministic_owners"}, "route_plan")
    if source.get("schema") != ROUTE_SCHEMA:
        raise AuthoritySchemaError(f"route_plan.schema must be {ROUTE_SCHEMA!r}")

    groups: dict[str, Any] = {}
    for name, raw in _named_items(source.get("groups", {}), "route_plan.groups"):
        if raw == "rest":
            groups[name] = "rest"
        else:
            groups[name] = sorted(_string_list(raw, f"route_plan.groups.{name}",
                                               nonempty=True))

    waves_raw = source.get("waves")
    if not isinstance(waves_raw, list):
        raise AuthoritySchemaError("route_plan.waves must be a list")
    waves: list[dict[str, Any]] = []
    wave_names: list[str] = []
    for index, raw in enumerate(waves_raw):
        row = _mapping(raw, f"route_plan.waves[{index}]")
        _closed(row, {"name", "group", "nets", "routing_class"},
                f"route_plan.waves[{index}]")
        name = _nonempty_string(row.get("name"), f"route_plan.waves[{index}].name")
        has_group, has_nets = "group" in row, "nets" in row
        if has_group == has_nets:
            raise AuthoritySchemaError(
                f"route_plan.waves[{index}] must declare exactly one of group or nets")
        item: dict[str, Any] = {
            "name": name,
            "routing_class": _nonempty_string(
                row.get("routing_class"),
                f"route_plan.waves[{index}].routing_class"),
        }
        if has_group:
            item["group"] = _nonempty_string(
                row["group"], f"route_plan.waves[{index}].group")
        elif row["nets"] == "rest":
            item["nets"] = "rest"
        else:
            item["nets"] = sorted(_string_list(
                row["nets"], f"route_plan.waves[{index}].nets", nonempty=True))
        waves.append(item)
        wave_names.append(name)
    if len(wave_names) != len(set(wave_names)):
        raise AuthoritySchemaError("route_plan.waves contains duplicate names")

    exclusions_raw = source.get("exclusions", [])
    if not isinstance(exclusions_raw, list):
        raise AuthoritySchemaError("route_plan.exclusions must be a list")
    exclusions: list[dict[str, str]] = []
    for index, raw in enumerate(exclusions_raw):
        row = _mapping(raw, f"route_plan.exclusions[{index}]")
        _closed(row, {"pattern", "owner", "why"},
                f"route_plan.exclusions[{index}]")
        exclusions.append({key: _nonempty_string(
            row.get(key), f"route_plan.exclusions[{index}].{key}")
                           for key in ("pattern", "owner", "why")})
    exclusions.sort(key=lambda row: (row["pattern"], row["owner"], row["why"]))

    owners_raw = source.get("deterministic_owners", [])
    if not isinstance(owners_raw, list):
        raise AuthoritySchemaError("route_plan.deterministic_owners must be a list")
    owners: list[dict[str, str]] = []
    for index, raw in enumerate(owners_raw):
        row = _mapping(raw, f"route_plan.deterministic_owners[{index}]")
        _closed(row, {"net", "owner", "why"},
                f"route_plan.deterministic_owners[{index}]")
        owners.append({key: _nonempty_string(
            row.get(key), f"route_plan.deterministic_owners[{index}].{key}")
                       for key in ("net", "owner", "why")})
    owners.sort(key=lambda row: (row["net"], row["owner"], row["why"]))

    return {"schema": ROUTE_SCHEMA, "groups": groups, "waves": waves,
            "exclusions": exclusions, "deterministic_owners": owners}


def resolve_route_waves(plan: Mapping[str, Any], *, live_nets: Sequence[str],
                        routing_classes: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve every live net to one wave, deterministic owner, or exclusion."""
    route = normalize_route_plan(plan)
    live = set(_string_list(list(live_nets), "live_nets"))
    findings: list[dict[str, str]] = []
    claims: dict[str, list[dict[str, str]]] = {net: [] for net in live}
    removed_sources: dict[str, set[str]] = {}

    def removed(net: str, source: str) -> None:
        removed_sources.setdefault(net, set()).add(source)

    def claim(net: str, kind: str, owner: str) -> None:
        if net in live:
            claims[net].append({"kind": kind, "owner": owner})
        else:
            removed(net, f"{kind}:{owner}")

    # Stale members are invalid even when their group is not scheduled: a
    # removed topology must not survive in dormant authored route authority.
    for group_name, members in route["groups"].items():
        if members == "rest":
            continue
        for net in members:
            if net not in live:
                removed(net, f"group:{group_name}")

    for row in route["deterministic_owners"]:
        claim(row["net"], "deterministic", row["owner"])

    for row in route["exclusions"]:
        matched = sorted(net for net in live
                         if fnmatch.fnmatchcase(net, row["pattern"]))
        for net in matched:
            claim(net, "exclusion", row["owner"])
        if not matched and not any(char in row["pattern"] for char in "*?["):
            removed(row["pattern"], f"exclusion:{row['owner']}")

    explicit: list[tuple[dict[str, Any], list[str] | None]] = []
    for wave in route["waves"]:
        members: list[str] | None
        if "group" in wave:
            group = wave["group"]
            if group not in route["groups"]:
                findings.append(_finding(
                    "W-GROUP-UNKNOWN", wave["name"],
                    f"wave names absent group {group!r}"))
                members = []
            elif route["groups"][group] == "rest":
                members = None
            else:
                members = route["groups"][group]
        elif wave["nets"] == "rest":
            members = None
        else:
            members = wave["nets"]
        explicit.append((wave, members))
        if members is not None:
            for net in members:
                claim(net, "wave", wave["name"])

    # Every rest wave sees the same complement.  Multiple rest waves therefore
    # become visibly multiply-owned rather than depending on authored order.
    remainder = sorted(net for net, owners in claims.items() if not owners)
    resolved_waves: list[dict[str, Any]] = []
    for wave, members in explicit:
        resolved_members = remainder if members is None else sorted(
            net for net in members if net in live)
        if members is None:
            for net in resolved_members:
                claim(net, "wave", wave["name"])
        if not resolved_members:
            findings.append(_finding(
                "W-EMPTY", wave["name"], "wave resolves to zero live nets"))
        class_name = wave["routing_class"]
        resolved_class = routing_classes.get(class_name)
        if resolved_class is None:
            findings.append(_finding(
                "W-CLASS-UNKNOWN", wave["name"],
                f"routing class {class_name!r} is absent from stack authority"))
            allowed_layers: list[str] = []
            references: dict[str, Any] = {}
        else:
            allowed_layers = list(resolved_class.get("allowed_layers", []))
            references = copy.deepcopy(resolved_class.get("references", {}))
            if not allowed_layers:
                findings.append(_finding(
                    "W-CLASS-EMPTY", wave["name"],
                    f"routing class {class_name!r} has no legal physical layers"))
        resolved_waves.append({
            "name": wave["name"], "routing_class": class_name,
            "nets": resolved_members, "allowed_layers": allowed_layers,
            "references": references,
        })

    for net, sources in sorted(removed_sources.items()):
        findings.append(_finding(
            "W-REMOVED", net,
            f"route authority names a non-live net via {sorted(sources)}"))
    owners: dict[str, dict[str, str]] = {}
    for net in sorted(live):
        rows = claims[net]
        if not rows:
            findings.append(_finding(
                "W-UNCOVERED", net,
                "live net has no wave, deterministic owner, or explicit exclusion"))
            continue
        identities = [(row["kind"], row["owner"]) for row in rows]
        if len(rows) > 1:
            findings.append(_finding(
                "W-MULTIPLE", net,
                f"live net has multiple owners {sorted(identities)}"))
            continue
        owners[net] = rows[0]

    findings = _sort_findings(findings)
    return {
        "status": "FAIL" if findings else "PASS",
        "waves": resolved_waves,
        "owners": owners,
        "findings": findings,
        "coverage": {"live_nets": len(live), "owned_nets": len(owners),
                     "waves": len(resolved_waves),
                     "groups": len(route["groups"]),
                     "exclusions": len(route["exclusions"]),
                     "deterministic_owners": len(route["deterministic_owners"])},
    }


# --------------------------------------------------------------- defaults --

def derive_reference_and_stitch_defaults(
        contract: Mapping[str, Any],
        resolved_classes: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Derive only facts entailed by semantic roles and explicit net names.

    No signal-net lists, stitch grid bounds, via geometry, or plane net names
    are guessed.  Ambiguous reference relationships stay absent.  Emitted-only
    cleanup is an ownership safety rule, not inferred board geometry.
    """
    stack = normalize_stack_contract(contract)
    classes = (resolved_classes if resolved_classes is not None
               else resolve_routing_classes(stack)["classes"])
    names = [row["name"] for row in stack["copper"]]
    checks: dict[tuple[str, str, str], set[str]] = {}
    for class_name, spec in classes.items():
        for signal_layer, reference in spec.get("references", {}).items():
            key = (signal_layer, reference["layer"], reference["net"])
            checks.setdefault(key, set()).add(class_name)
    reference_defaults = [
        {"signal_layer": signal, "reference_layer": reference,
         "reference_net": net, "routing_classes": sorted(class_names)}
        for (signal, reference, net), class_names in sorted(
            checks.items(), key=lambda item: (names.index(item[0][0]),
                                              names.index(item[0][1]), item[0][2]))
    ]

    planes = [row for row in stack["copper"]
              if row["role"] == "reference_plane" and row.get("plane_net")]
    stitch: dict[str, Any] = {
        "cleanup_scope": "emitted",
        "reference_layers": [row["name"] for row in planes],
        "reference_nets": sorted({row["plane_net"] for row in planes}),
    }
    if planes:
        via_candidates = []
        for name, family in stack["via_families"].items():
            try:
                span = physical_via_span(
                    stack, family["from_layer"], family["to_layer"])
            except AuthoritySchemaError:
                continue
            if all(row["name"] in span for row in planes):
                via_candidates.append(name)
        if len(via_candidates) == 1:
            stitch["via_family"] = via_candidates[0]
        else:
            stitch["requires_explicit_via_family"] = True
    return {"reference_plane_checks": reference_defaults, "stitch": stitch}


# ------------------------------------------------------------- authority --

def _normalized_input_bundle(*, stack: Mapping[str, Any],
                             observed: Mapping[str, Any],
                             route_plan: Mapping[str, Any],
                             migration: Mapping[str, Any] | None) -> dict[str, Any]:
    return {
        "schema": "source-prep-inputs-v1",
        "stack": normalize_stack_contract(stack),
        "observed": normalize_observed_facts(observed),
        "route_plan": normalize_route_plan(route_plan),
        "migration": normalize_topology_migration(migration),
    }


def _input_records(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return {name: {"sha256": canonical_sha256(bundle[name]),
                   "present": bundle[name] is not None}
            for name in ("stack", "observed", "route_plan", "migration")}


def _authority_digest(authority: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(authority))
    binding = payload.get("binding")
    if isinstance(binding, dict):
        binding.pop("authority_sha256", None)
    return canonical_sha256(payload)


def compile_source_prep_authority(
        *, stack: Mapping[str, Any], observed: Mapping[str, Any],
        route_plan: Mapping[str, Any],
        migration: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compile one deterministic source-to-prep authority receipt."""
    bundle = _normalized_input_bundle(stack=stack, observed=observed,
                                      route_plan=route_plan,
                                      migration=migration)
    stack_value = bundle["stack"]
    observed_value = bundle["observed"]
    class_result = resolve_routing_classes(stack_value)
    via_result = _resolve_via_families(stack_value)
    migration_result = reconcile_topology_migration(bundle["migration"],
                                                     observed_value)
    route_result = resolve_route_waves(
        bundle["route_plan"], live_nets=observed_value["nets"],
        routing_classes=class_result["classes"])
    defaults = derive_reference_and_stitch_defaults(
        stack_value, class_result["classes"])

    findings = _sort_findings(
        class_result["findings"] + via_result["findings"]
        + migration_result["findings"] + route_result["findings"])
    checks = {
        "stack": {"status": "FAIL" if class_result["findings"]
                  or via_result["findings"] else "PASS",
                  "finding_count": len(class_result["findings"])
                  + len(via_result["findings"])},
        "migration": {"status": migration_result["status"],
                      "finding_count": len(migration_result["findings"])},
        "route_ownership": {"status": route_result["status"],
                            "finding_count": len(route_result["findings"])},
    }
    coverage = {
        "copper_layers": len(stack_value["copper"]),
        "routing_classes": class_result["coverage"]["routing_classes"],
        "reference_mappings": class_result["coverage"]["reference_mappings"],
        "via_families": len(via_result["families"]),
        "live_refs": len(observed_value["refs"]),
        "live_nets": len(observed_value["nets"]),
        "live_mpns": len(observed_value["mpns"]),
        "migration_delta_items": migration_result["coverage"]["delta_items"],
        "historical_occurrences_excluded": migration_result["coverage"][
            "historical_occurrences_excluded"],
        "route_groups": route_result["coverage"]["groups"],
        "route_waves": route_result["coverage"]["waves"],
        "owned_live_nets": route_result["coverage"]["owned_nets"],
    }
    authority: dict[str, Any] = {
        "schema": AUTHORITY_SCHEMA,
        "verdict": "FAIL" if findings else "PASS",
        "ownership": {
            "physical_stack": STACK_ROLE_OWNER,
            "semantic_layer_roles": STACK_ROLE_OWNER,
            "legacy_adapters": LEGACY_AUTHORITY,
        },
        "binding": {
            "algorithm": "sha256",
            "subject_sha256": canonical_sha256(bundle),
        },
        "inputs": _input_records(bundle),
        "coverage": coverage,
        "findings": findings,
        "checks": checks,
        "stack": {
            "physical_order": [row["name"] for row in stack_value["copper"]],
            "copper": copy.deepcopy(stack_value["copper"]),
            "routing_classes": class_result["classes"],
            "via_families": via_result["families"],
        },
        "live": {kind: copy.deepcopy(observed_value[kind]) for kind in FACT_KINDS},
        "migration": migration_result,
        "routes": route_result,
        "defaults": defaults,
    }
    authority["binding"]["authority_sha256"] = _authority_digest(authority)
    return authority


def _verify_authority(
        authority: Mapping[str, Any], *,
        stack: Mapping[str, Any] | None = None,
        observed: Mapping[str, Any] | None = None,
        route_plan: Mapping[str, Any] | None = None,
        migration: Mapping[str, Any] | None = None) -> tuple[bool, list[str]]:
    """Internal structural verifier with optional exact-input recompilation."""
    failures: list[str] = []
    if not isinstance(authority, Mapping):
        return False, ["authority must be a mapping"]
    allowed = {"schema", "verdict", "ownership", "binding", "inputs", "coverage",
               "findings", "checks", "stack", "live", "migration", "routes",
               "defaults"}
    try:
        _closed(authority, allowed, "authority")
    except AuthoritySchemaError as exc:
        failures.append(str(exc))
    missing = sorted(allowed - set(authority))
    if missing:
        failures.append(f"authority is missing key(s): {missing}")
    if authority.get("schema") != AUTHORITY_SCHEMA:
        failures.append("authority schema is invalid")
    expected_ownership = {
        "physical_stack": STACK_ROLE_OWNER,
        "semantic_layer_roles": STACK_ROLE_OWNER,
        "legacy_adapters": LEGACY_AUTHORITY,
    }
    if authority.get("ownership") != expected_ownership:
        failures.append(
            "authority ownership must retain canonical stack/role owner and "
            "non-authoritative legacy adapters")

    findings = authority.get("findings")
    if not isinstance(findings, list):
        failures.append("authority findings must be a list")
        findings = []
    findings_well_formed = True
    for index, row in enumerate(findings):
        if not isinstance(row, Mapping):
            failures.append(f"authority findings[{index}] must be a mapping")
            findings_well_formed = False
            continue
        try:
            _closed(row, {"code", "subject", "message"},
                    f"authority findings[{index}]")
        except AuthoritySchemaError as exc:
            failures.append(str(exc))
            findings_well_formed = False
        if set(row) != {"code", "subject", "message"}:
            failures.append(
                f"authority findings[{index}] must contain code/subject/message")
            findings_well_formed = False
        for key in ("code", "subject", "message"):
            if not isinstance(row.get(key), str) or not row.get(key, "").strip():
                failures.append(
                    f"authority findings[{index}].{key} must be a non-empty string")
                findings_well_formed = False
    if findings_well_formed and findings != _sort_findings(findings):
        failures.append("authority findings are not unique canonical order")

    verdict = authority.get("verdict")
    expected_verdict = "FAIL" if findings else "PASS"
    if verdict not in {"PASS", "FAIL"} or verdict != expected_verdict:
        failures.append("authority verdict disagrees with findings")

    coverage_keys = {
        "copper_layers", "routing_classes", "reference_mappings",
        "via_families", "live_refs", "live_nets", "live_mpns",
        "migration_delta_items", "historical_occurrences_excluded",
        "route_groups", "route_waves", "owned_live_nets",
    }
    coverage = authority.get("coverage")
    if not isinstance(coverage, Mapping):
        failures.append("authority coverage must be a mapping")
        coverage = {}
    else:
        try:
            _closed(coverage, coverage_keys, "authority coverage")
        except AuthoritySchemaError as exc:
            failures.append(str(exc))
        missing_coverage = sorted(coverage_keys - set(coverage))
        if missing_coverage:
            failures.append(f"authority coverage is missing key(s): {missing_coverage}")
        for key, value in coverage.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                failures.append(f"authority coverage.{key} must be a non-negative integer")
    if not any(isinstance(value, int) and not isinstance(value, bool) and value > 0
               for value in coverage.values()):
        failures.append("authority has no nonzero coverage denominator")

    def digest(value: Any) -> bool:
        return (isinstance(value, str) and len(value) == 64
                and all(char in "0123456789abcdef" for char in value))

    binding = authority.get("binding")
    if not isinstance(binding, Mapping):
        failures.append("authority binding is invalid")
    else:
        try:
            _closed(binding, {"algorithm", "subject_sha256", "authority_sha256"},
                    "authority binding")
        except AuthoritySchemaError as exc:
            failures.append(str(exc))
        if set(binding) != {"algorithm", "subject_sha256", "authority_sha256"}:
            failures.append("authority binding fields are incomplete")
        if binding.get("algorithm") != "sha256":
            failures.append("authority binding algorithm is invalid")
        if not digest(binding.get("subject_sha256")):
            failures.append("authority subject hash is invalid")
        expected_hash = binding.get("authority_sha256")
        if not digest(expected_hash):
            failures.append("authority content hash is invalid")
        try:
            actual_hash = _authority_digest(authority)
        except AuthoritySchemaError as exc:
            failures.append(f"authority cannot be hashed: {exc}")
            actual_hash = None
        if expected_hash != actual_hash:
            failures.append("authority content hash changed")

    inputs = authority.get("inputs")
    input_names = {"stack", "observed", "route_plan", "migration"}
    if not isinstance(inputs, Mapping):
        failures.append("authority inputs must be a mapping")
    else:
        try:
            _closed(inputs, input_names, "authority inputs")
        except AuthoritySchemaError as exc:
            failures.append(str(exc))
        if set(inputs) != input_names:
            failures.append("authority input hash map is incomplete")
        for name, record in inputs.items():
            if not isinstance(record, Mapping):
                failures.append(f"authority inputs.{name} must be a mapping")
                continue
            try:
                _closed(record, {"sha256", "present"},
                        f"authority inputs.{name}")
            except AuthoritySchemaError as exc:
                failures.append(str(exc))
            if set(record) != {"sha256", "present"}:
                failures.append(f"authority inputs.{name} fields are incomplete")
            if not digest(record.get("sha256")):
                failures.append(f"authority inputs.{name}.sha256 is invalid")
            if not isinstance(record.get("present"), bool):
                failures.append(f"authority inputs.{name}.present must be boolean")

    checks = authority.get("checks")
    check_names = {"stack", "migration", "route_ownership"}
    if not isinstance(checks, Mapping):
        failures.append("authority checks must be a mapping")
    else:
        try:
            _closed(checks, check_names, "authority checks")
        except AuthoritySchemaError as exc:
            failures.append(str(exc))
        if set(checks) != check_names:
            failures.append("authority checks are incomplete")
        for name, row in checks.items():
            if not isinstance(row, Mapping):
                failures.append(f"authority checks.{name} must be a mapping")
                continue
            try:
                _closed(row, {"status", "finding_count"},
                        f"authority checks.{name}")
            except AuthoritySchemaError as exc:
                failures.append(str(exc))
            if set(row) != {"status", "finding_count"}:
                failures.append(f"authority checks.{name} fields are incomplete")
            if row.get("status") not in {"PASS", "FAIL", "N-A"}:
                failures.append(f"authority checks.{name}.status is invalid")
            count = row.get("finding_count")
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                failures.append(
                    f"authority checks.{name}.finding_count must be non-negative")

    section_keys = {
        "stack": {"physical_order", "copper", "routing_classes", "via_families"},
        "live": set(FACT_KINDS),
        "migration": {"status", "id", "findings",
                      "historical_occurrences_excluded", "coverage"},
        "routes": {"status", "waves", "owners", "findings", "coverage"},
        "defaults": {"reference_plane_checks", "stitch"},
    }
    for name, expected_keys in section_keys.items():
        section = authority.get(name)
        if not isinstance(section, Mapping):
            failures.append(f"authority {name} must be a mapping")
            continue
        try:
            _closed(section, expected_keys, f"authority {name}")
        except AuthoritySchemaError as exc:
            failures.append(str(exc))
        missing_section = sorted(expected_keys - set(section))
        if missing_section:
            failures.append(f"authority {name} is missing key(s): {missing_section}")

    expected_requested = any(value is not None
                             for value in (stack, observed, route_plan, migration))
    if expected_requested:
        if stack is None or observed is None or route_plan is None:
            failures.append("stack, observed, and route_plan are all required for input verification")
        else:
            try:
                bundle = _normalized_input_bundle(
                    stack=stack, observed=observed, route_plan=route_plan,
                    migration=migration)
                subject = canonical_sha256(bundle)
                if not isinstance(binding, Mapping) or binding.get(
                        "subject_sha256") != subject:
                    failures.append("authority input subject changed")
                if authority.get("inputs") != _input_records(bundle):
                    failures.append("authority input hash map changed")
                expected_authority = compile_source_prep_authority(
                    stack=stack, observed=observed, route_plan=route_plan,
                    migration=migration)
                if authority != expected_authority:
                    failures.append(
                        "authority does not match recompilation from exact inputs")
            except (AuthoritySchemaError, TypeError, ValueError) as exc:
                failures.append(f"expected inputs are invalid: {exc}")
    return not failures, failures


def verify_authority_structure(
        authority: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Check closed schema and self-hash without conferring promotion authority."""
    return _verify_authority(authority)


def inspect_legacy_authority(
        authority: Mapping[str, Any]) -> dict[str, Any]:
    """Inspect a pre-ownership schema-1 receipt without granting authority.

    ``source-prep-authority-v1`` existed briefly without its mandatory
    ownership declaration.  Those bytes remain readable for diagnostics, but
    cannot pass either structural or exact-input authority verification.
    """
    source = _mapping(authority, "legacy authority")
    if source.get("schema") != AUTHORITY_SCHEMA or "ownership" in source:
        raise AuthoritySchemaError(
            "legacy authority diagnostic requires schema-1 bytes with no ownership")
    old_fields = {
        "schema", "verdict", "binding", "inputs", "coverage", "findings",
        "checks", "stack", "live", "migration", "routes", "defaults",
    }
    _closed(source, old_fields, "legacy authority")
    missing = sorted(old_fields - set(source))
    if missing:
        raise AuthoritySchemaError(
            f"legacy authority is missing diagnostic key(s): {missing}")
    binding = source.get("binding")
    expected_hash = (binding.get("authority_sha256")
                     if isinstance(binding, Mapping) else None)
    try:
        self_hash_valid = expected_hash == _authority_digest(source)
    except (AuthoritySchemaError, TypeError, ValueError):
        self_hash_valid = False
    return {
        "schema": LEGACY_AUTHORITY_DIAGNOSTIC_SCHEMA,
        "authoritative": False,
        "authority_class": LEGACY_AUTHORITY,
        "execution_authority": None,
        "source_schema": AUTHORITY_SCHEMA,
        "source_sha256": canonical_sha256(source),
        "self_hash_valid": self_hash_valid,
        "diagnostics": [
            "canonical physical-stack and semantic-role ownership is absent; "
            "recompile from exact stack/observed/route-plan/migration inputs",
        ],
    }


def read_legacy_authority_diagnostic(path: Path | str) -> dict[str, Any]:
    """Read old receipt bytes into a non-authoritative diagnostic wrapper."""
    target = Path(path)
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorityVerificationError(
            f"legacy authority cannot be read diagnostically: {exc}") from exc
    return inspect_legacy_authority(value)


def verify_authority(
        authority: Mapping[str, Any], *, stack: Mapping[str, Any],
        observed: Mapping[str, Any], route_plan: Mapping[str, Any],
        migration: Mapping[str, Any] | None) -> tuple[bool, list[str]]:
    """Verify an authority receipt by recompiling all exact source inputs."""
    return _verify_authority(
        authority, stack=stack, observed=observed, route_plan=route_plan,
        migration=migration)


def write_authority(
        path: Path | str, authority: Mapping[str, Any], *,
        stack: Mapping[str, Any], observed: Mapping[str, Any],
        route_plan: Mapping[str, Any], migration: Mapping[str, Any] | None,
        ) -> Path:
    """Atomically write only after exact-input authority verification."""
    ok, failures = verify_authority(
        authority, stack=stack, observed=observed, route_plan=route_plan,
        migration=migration)
    if not ok:
        raise AuthorityVerificationError("; ".join(failures))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(authority, indent=2, sort_keys=True,
                                    ensure_ascii=False, allow_nan=False) + "\n",
                         encoding="utf-8")
    os.replace(temporary, target)
    return target


def reopen_authority(
        path: Path | str, *, stack: Mapping[str, Any],
        observed: Mapping[str, Any], route_plan: Mapping[str, Any],
        migration: Mapping[str, Any] | None) -> dict[str, Any]:
    """Read and verify an authority receipt against every exact input."""
    target = Path(path)
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorityVerificationError(f"authority cannot be reopened: {exc}") from exc
    ok, failures = verify_authority(
        value, stack=stack, observed=observed, route_plan=route_plan,
        migration=migration)
    if not ok:
        raise AuthorityVerificationError("; ".join(failures))
    return value


# ---------------------------------------------------------- legacy bridge --

_LEGACY_ROLE_ALIASES = {
    "signal": "signal",
    "reference_plane": "reference_plane",
    "power": "power",
    "high_current_power": "power",
    "mixed": "mixed",
    "mixed_signal_pour": "mixed",
    "low_speed_and_3v3": "mixed",
}


def adapt_legacy_stack(
        floorplan: Mapping[str, Any], route: Mapping[str, Any] | None = None,
        nets: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a non-authoritative ``stackup-v1`` authoring candidate.

    Legacy sources intentionally remain loose because their unrelated keys are
    outside this module's contract.  Every assumption/omission is visible, the
    wrapper is marked ``authoritative: false``, and
    :func:`compile_source_prep_authority` never calls this adapter.
    """
    floorplan = _mapping(floorplan, "legacy floorplan")
    route = _mapping(route or {}, "legacy route")
    nets = _mapping(nets or {}, "legacy nets")
    board = _mapping(floorplan.get("board", {}), "legacy floorplan.board")
    try:
        count = int(board.get("layers", 2))
    except (TypeError, ValueError) as exc:
        raise AuthoritySchemaError("legacy board.layers must be an integer") from exc
    if count < 2:
        raise AuthoritySchemaError("legacy board.layers must be at least two")
    names = ["F.Cu"] + [f"In{index}.Cu" for index in range(1, count - 1)] + ["B.Cu"]
    stackup = _mapping(board.get("stackup", {}), "legacy board.stackup")
    thicknesses = stackup.get("copper_thickness_mm")
    notes: list[str] = []
    if not isinstance(thicknesses, list) or len(thicknesses) != count:
        thicknesses = [35.0 / 1000.0] * count
        notes.append("copper thickness absent/incomplete; 35um suggestion requires author review")

    route_root = _mapping(route.get("route", route), "legacy route.route")
    routability = _mapping(route_root.get("routability", {}),
                           "legacy route.routability")
    roles = dict(_named_items(routability.get("layer_roles", {}),
                              "legacy route.routability.layer_roles"))
    plane_nets: dict[str, str] = {}
    conflicted_plane_layers: set[str] = set()
    checks = nets.get("reference_plane_checks", {})
    if isinstance(checks, Mapping):
        for raw in checks.values():
            if not isinstance(raw, Mapping):
                continue
            layer, net = raw.get("reference_layer"), raw.get("reference_net")
            if isinstance(layer, str) and isinstance(net, str) and layer and net:
                if layer in conflicted_plane_layers:
                    continue
                if layer in plane_nets and plane_nets[layer] != net:
                    notes.append(f"conflicting legacy plane nets for {layer}; omitted")
                    plane_nets.pop(layer, None)
                    conflicted_plane_layers.add(layer)
                else:
                    plane_nets[layer] = net

    copper = []
    for index, name in enumerate(names):
        legacy_role = roles.get(name)
        role = _LEGACY_ROLE_ALIASES.get(str(legacy_role))
        if role is None:
            role = "signal" if name in {"F.Cu", "B.Cu"} else "mixed"
            notes.append(f"{name} role {legacy_role!r} was not authoritative; suggested {role}")
        row: dict[str, Any] = {
            "name": name,
            "thickness_um": _positive_number(
                thicknesses[index], f"legacy copper_thickness_mm[{index}]") * 1000.0,
            "role": role,
        }
        if name in plane_nets:
            row["plane_net"] = plane_nets[name]
        copper.append(row)

    routing_classes = {}
    for name, layers in _named_items(
            routability.get("class_layers", {}),
            "legacy route.routability.class_layers"):
        routing_classes[name] = {
            "allowed_layers": _string_list(
                layers, f"legacy route.routability.class_layers.{name}",
                nonempty=True),
            "references": {},
            "reference_required": False,
        }
    candidate = {"schema": STACK_SCHEMA, "copper": copper,
                 "routing_classes": routing_classes, "via_families": {}}
    # Validate only to make the suggested document mechanically useful.  This
    # does not promote it: the wrapper, not the candidate, is the API result.
    candidate = normalize_stack_contract(candidate)
    return {
        "schema": LEGACY_ADAPTER_SCHEMA,
        "authoritative": False,
        "authority_class": LEGACY_AUTHORITY,
        "execution_authority": None,
        "candidate": candidate,
        "notes": sorted(notes),
    }


__all__ = [
    "AUTHORITY_SCHEMA", "LEGACY_ADAPTER_SCHEMA", "LEGACY_AUTHORITY",
    "LEGACY_AUTHORITY_DIAGNOSTIC_SCHEMA",
    "MIGRATION_SCHEMA",
    "OBSERVED_SCHEMA", "ROUTE_SCHEMA", "SEMANTIC_ROLES", "STACK_SCHEMA",
    "STACK_ROLE_OWNER",
    "AuthoritySchemaError", "AuthorityVerificationError",
    "adapt_legacy_stack", "canonical_sha256", "compile_source_prep_authority",
    "derive_reference_and_stitch_defaults", "normalize_observed_facts",
    "normalize_route_plan", "normalize_stack_contract",
    "normalize_topology_migration", "physical_copper_order",
    "inspect_legacy_authority", "physical_via_span",
    "read_legacy_authority_diagnostic", "reconcile_topology_migration",
    "reopen_authority",
    "resolve_route_waves", "resolve_routing_classes", "verify_authority",
    "verify_authority_structure", "write_authority",
]
