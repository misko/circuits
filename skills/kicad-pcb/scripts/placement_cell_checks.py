#!/usr/bin/env python3
"""Deterministic functional-cell placement checks (library, schema 1).

This module closes placement facts that body clearance and scalar proximity do
not: exact selected-MPN pad roles, signed functional orientation, ordered local
paths, simultaneous routing reservations, constrained-pad escape decisions,
critical-ground egress, a fabrication-stack-aware copper-resistance lower
bound, and pilot/replica equivalence.

The public API is deliberately data-only::

    report = evaluate_placement_cells(contract, snapshot)

``contract`` contains ``selected_parts`` plus zero or more ``cells`` and
``replicas``.  ``snapshot`` contains placed ``parts`` (pads with millimetre
coordinates), optional obstacles, a stackup, and fabrication facts.  See the
focused tests beside this module for compact examples.  Every check returns
one of ``PASS``, ``FAIL``, ``INCOMPLETE`` or ``N-A`` and an explicit
``graded``/``total`` denominator.  Missing declarations are N-A only when the
selected parts and measured pad facts do not make the predicate applicable;
there are no ``require_*`` opt-outs.

This is not a router and does not reproduce electrical DC-bias calculations.
It grades only authored straight/local geometry and the PCB mOhm allocation
already supplied by the owning power contract.  ``snapshot_from_pcbnew`` is a
lazy compatibility adapter; importing this module never requires pcbnew.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping, Sequence


PASS = "PASS"
FAIL = "FAIL"
INCOMPLETE = "INCOMPLETE"
NA = "N-A"
N_A = NA
STATUSES = frozenset({PASS, FAIL, INCOMPLETE, NA})
SCHEMA = 1
EPS = 1e-9


class ContractError(ValueError):
    """An unresolved or malformed declaration, retained as INCOMPLETE."""


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _finite(value: Any, where: str, *, positive: bool = False,
            nonnegative: bool = False) -> float:
    if isinstance(value, bool):
        raise ContractError(f"{where}: expected a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{where}: expected a finite number") from exc
    if not math.isfinite(number):
        raise ContractError(f"{where}: expected a finite number")
    if positive and number <= 0:
        raise ContractError(f"{where}: expected a positive number")
    if nonnegative and number < 0:
        raise ContractError(f"{where}: expected a non-negative number")
    return number


def _point(value: Any, where: str) -> tuple[float, float]:
    if _is_mapping(value):
        if "at" in value:
            return _point(value["at"], f"{where}.at")
        if "center" in value:
            return _point(value["center"], f"{where}.center")
        if "position" in value:
            return _point(value["position"], f"{where}.position")
        if "x_mm" in value and "y_mm" in value:
            return (_finite(value["x_mm"], f"{where}.x_mm"),
                    _finite(value["y_mm"], f"{where}.y_mm"))
        if "x" in value and "y" in value:
            return (_finite(value["x"], f"{where}.x"),
                    _finite(value["y"], f"{where}.y"))
    if (isinstance(value, Sequence) and not isinstance(value, (str, bytes))
            and len(value) == 2):
        return (_finite(value[0], f"{where}[0]"),
                _finite(value[1], f"{where}[1]"))
    raise ContractError(f"{where}: expected [x_mm, y_mm]")


def _points(value: Any, where: str, *, minimum: int = 2) -> list[tuple[float, float]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ContractError(f"{where}: expected a point list")
    result = [_point(item, f"{where}[{index}]")
              for index, item in enumerate(value)]
    if len(result) < minimum:
        raise ContractError(f"{where}: needs at least {minimum} point(s)")
    return result


def _text(value: Any, where: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ContractError(f"{where}: expected non-empty text")
    return text


def _list(value: Any, where: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError(f"{where}: expected a list")
    return value


def _rows(value: Mapping[str, Any], names: Sequence[str], where: str) -> list[Any]:
    present = [name for name in names if name in value]
    if not present:
        return []
    first = value[present[0]]
    for name in present[1:]:
        if value[name] != first:
            raise ContractError(
                f"{where}: aliases {present!r} disagree; keep one authority")
    return _list(first, f"{where}.{present[0]}")


def _status_from(items: Sequence[Mapping[str, Any]]) -> str:
    statuses = {str(item.get("status")) for item in items}
    if INCOMPLETE in statuses:
        return INCOMPLETE
    if FAIL in statuses:
        return FAIL
    if PASS in statuses:
        return PASS
    return NA


def _result(name: str, items: Sequence[Mapping[str, Any]],
            *, reason: str | None = None) -> dict[str, Any]:
    copied = [dict(item) for item in items]
    for item in copied:
        status = item.get("status")
        if status not in STATUSES:
            raise AssertionError(f"internal invalid status {status!r}")
    status = _status_from(copied)
    total = sum(item.get("status") != NA for item in copied)
    passed = sum(item.get("status") == PASS for item in copied)
    failed = sum(item.get("status") == FAIL for item in copied)
    incomplete = sum(item.get("status") == INCOMPLETE for item in copied)
    not_applicable = sum(item.get("status") == NA for item in copied)
    graded = passed + failed
    findings = [str(message)
                for item in copied
                for message in item.get("findings", [])]
    if status == NA:
        detail = reason or f"no applicable {name} declarations or selected-pad facts"
    else:
        detail = (f"{graded}/{total} {name} item(s) graded; "
                  f"{failed} failed, {incomplete} incomplete")
    return {
        "status": status,
        "applicability": "NOT_APPLICABLE" if status == NA else "APPLIES",
        "applicability_reason": detail if status == NA else None,
        "detail": detail,
        "graded": graded,
        "total": total,
        "coverage": {
            "passed": passed,
            "failed": failed,
            "incomplete": incomplete,
            "not_applicable": not_applicable,
            "graded": graded,
            "total": total,
        },
        "items": copied,
        "findings": findings,
    }


def _item(subject: str, status: str, *findings: str, **evidence: Any) -> dict[str, Any]:
    return {"subject": subject, "status": status,
            "findings": [finding for finding in findings if finding], **evidence}


def _malformed(subject: str, exc: Exception) -> dict[str, Any]:
    return _item(subject, INCOMPLETE, str(exc))


def _parts(snapshot: Mapping[str, Any]) -> Mapping[str, Any]:
    value = snapshot.get("parts", snapshot.get("footprints", {}))
    if not _is_mapping(value):
        raise ContractError("snapshot.parts: expected a mapping by reference")
    return value


def _pads(part: Mapping[str, Any], where: str) -> Mapping[str, Any]:
    value = part.get("pads", {})
    if not _is_mapping(value):
        raise ContractError(f"{where}.pads: expected a mapping by pad number")
    return {str(number): pad for number, pad in value.items()}


def _selections(contract: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    value = contract.get("selected_parts", {})
    if value is None:
        return []
    rows: list[tuple[str, Mapping[str, Any]]] = []
    if _is_mapping(value):
        for ref, raw in value.items():
            if isinstance(raw, str):
                raw = {"mpn": raw, "pad_roles": {}}
            if not _is_mapping(raw):
                raise ContractError(f"selected_parts.{ref}: expected a mapping")
            rows.append((str(ref), raw))
        return rows
    if isinstance(value, list):
        for index, raw in enumerate(value):
            if not _is_mapping(raw):
                raise ContractError(f"selected_parts[{index}]: expected a mapping")
            ref = _text(raw.get("ref"), f"selected_parts[{index}].ref")
            rows.append((ref, raw))
        return rows
    raise ContractError("selected_parts: expected a mapping or list")


def _selection_map(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for ref, row in _selections(contract):
        if ref in result:
            raise ContractError(f"selected_parts: duplicate ref {ref}")
        result[ref] = row
    return result


def _role_specs(selection: Mapping[str, Any], where: str) -> dict[str, dict[str, Any]]:
    raw = selection.get("pad_roles", selection.get("functional_pad_roles", {}))
    if not _is_mapping(raw):
        raise ContractError(f"{where}.pad_roles: expected a mapping")
    result: dict[str, dict[str, Any]] = {}
    for role, value in raw.items():
        name = _text(role, f"{where}.pad_roles role")
        if isinstance(value, (str, int)):
            spec: dict[str, Any] = {"pads": [str(value)]}
        elif isinstance(value, list):
            spec = {"pads": [str(item) for item in value]}
        elif _is_mapping(value):
            spec = dict(value)
            pads = spec.get("pads", spec.get("pad"))
            if isinstance(pads, (str, int)):
                pads = [str(pads)]
            elif isinstance(pads, list):
                pads = [str(item) for item in pads]
            else:
                raise ContractError(f"{where}.pad_roles.{name}.pads: expected pad(s)")
            spec["pads"] = pads
        else:
            raise ContractError(f"{where}.pad_roles.{name}: expected pad(s) or mapping")
        if not spec["pads"] or any(not str(pad).strip() for pad in spec["pads"]):
            raise ContractError(f"{where}.pad_roles.{name}: pads cannot be empty")
        result[name] = spec
    return result


def _pad_point(snapshot: Mapping[str, Any], ref: str, pad: str) -> tuple[float, float]:
    parts = _parts(snapshot)
    part = parts.get(ref)
    if not _is_mapping(part):
        raise ContractError(f"snapshot.parts: footprint {ref!r} is absent")
    pad_value = _pads(part, f"snapshot.parts.{ref}").get(str(pad))
    if not _is_mapping(pad_value):
        raise ContractError(f"snapshot.parts: pad {ref}.{pad} is absent")
    return _point(pad_value, f"snapshot.parts.{ref}.pads.{pad}")


def _centroid(points: Sequence[tuple[float, float]]) -> tuple[float, float]:
    if not points:
        raise ContractError("cannot take centroid of no points")
    return (sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points))


def _anchor(value: Any, contract: Mapping[str, Any], snapshot: Mapping[str, Any],
            where: str) -> tuple[tuple[float, float], str]:
    if _is_mapping(value):
        if any(key in value for key in ("at", "center", "position", "x_mm", "x")):
            return _point(value, where), str(value.get("id") or where)
        ref = _text(value.get("ref"), f"{where}.ref")
        if "pad" in value:
            pad = _text(value.get("pad"), f"{where}.pad")
            return _pad_point(snapshot, ref, pad), f"{ref}.{pad}"
        role = _text(value.get("role"), f"{where}.role")
        selections = _selection_map(contract)
        if ref not in selections:
            raise ContractError(f"{where}: {ref} has no exact selected-part declaration")
        roles = _role_specs(selections[ref], f"selected_parts.{ref}")
        if role not in roles:
            raise ContractError(f"{where}: role {ref}.{role} is undeclared")
        pads = roles[role]["pads"]
        return _centroid([_pad_point(snapshot, ref, pad) for pad in pads]), f"{ref}.{role}"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return _point(value, where), where
    token = _text(value, where)
    separator = ":" if ":" in token else "."
    if separator not in token:
        raise ContractError(f"{where}: endpoint must be REF.PAD, REF:ROLE, or a point")
    ref, name = token.split(separator, 1)
    parts = _parts(snapshot)
    part = parts.get(ref)
    if _is_mapping(part) and name in _pads(part, f"snapshot.parts.{ref}"):
        return _pad_point(snapshot, ref, name), f"{ref}.{name}"
    selections = _selection_map(contract)
    if ref not in selections:
        raise ContractError(f"{where}: {ref} has no exact selected-part declaration")
    roles = _role_specs(selections[ref], f"selected_parts.{ref}")
    if name not in roles:
        raise ContractError(f"{where}: endpoint {token!r} resolves to neither pad nor role")
    pads = roles[name]["pads"]
    return _centroid([_pad_point(snapshot, ref, pad) for pad in pads]), f"{ref}.{name}"


def _cells(contract: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    value = contract.get("cells", contract.get("functional_cells", []))
    rows = _list(value, "cells")
    result: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows):
        if not _is_mapping(row):
            raise ContractError(f"cells[{index}]: expected a mapping")
        result.append(row)
    return result


def _cell_id(cell: Mapping[str, Any], index: int) -> str:
    return _text(cell.get("id", cell.get("name")), f"cells[{index}].id")


def validate_declaration(contract: Any, snapshot: Any | None = None) -> dict[str, Any]:
    """Validate the closed input envelope without raising to callers."""
    items: list[dict[str, Any]] = []
    try:
        if not _is_mapping(contract):
            raise ContractError("contract: expected a mapping")
        schema = contract.get("schema", SCHEMA)
        if schema != SCHEMA or isinstance(schema, bool):
            raise ContractError(f"contract.schema: only schema {SCHEMA} is supported")
        selections = _selection_map(contract)
        for ref, row in selections.items():
            _text(row.get("mpn"), f"selected_parts.{ref}.mpn")
            _role_specs(row, f"selected_parts.{ref}")
        seen: set[str] = set()
        for index, cell in enumerate(_cells(contract)):
            name = _cell_id(cell, index)
            if name in seen:
                raise ContractError(f"cells: duplicate id {name!r}")
            seen.add(name)
        replicas = contract.get("replicas", contract.get("replications", []))
        _list(replicas, "replicas")
        if snapshot is not None:
            if not _is_mapping(snapshot):
                raise ContractError("snapshot: expected a mapping")
            _parts(snapshot)
        items.append(_item("contract", PASS, schema=SCHEMA,
                           selected_parts=len(selections), cells=len(seen)))
    except (ContractError, TypeError, ValueError) as exc:
        items.append(_malformed("contract", exc))
    return _result("declaration validation", items)


def check_selected_part_pad_roles(contract: Mapping[str, Any],
                                  snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Grade exact selected MPN identity and every declared functional role."""
    items: list[dict[str, Any]] = []
    try:
        selections = _selections(contract)
        parts = _parts(snapshot)
    except (ContractError, TypeError, ValueError) as exc:
        return _result("selected-part role", [_malformed("selected_parts", exc)])
    for ref, selection in selections:
        where = f"selected_parts.{ref}"
        try:
            expected_mpn = _text(selection.get("mpn"), f"{where}.mpn")
            roles = _role_specs(selection, where)
            observed = parts.get(ref)
            if not _is_mapping(observed):
                items.append(_item(f"{ref}:mpn", FAIL,
                                   f"{where}: selected footprint is absent"))
                for role, spec in roles.items():
                    items.append(_item(
                        f"{ref}:{role}", FAIL,
                        f"{where}.pad_roles.{role}: footprint is absent",
                        pads=list(spec["pads"]), nets=[]))
                continue
            actual_mpn = str(observed.get("mpn") or "").strip()
            if not actual_mpn:
                items.append(_item(
                    f"{ref}:mpn", INCOMPLETE,
                    f"{ref}: observed exact MPN is absent; expected authority "
                    "cannot serve as its own measurement",
                    expected_mpn=expected_mpn, observed_mpn=actual_mpn))
            elif actual_mpn != expected_mpn:
                items.append(_item(
                    f"{ref}:mpn", FAIL,
                    f"{ref}: observed exact MPN {actual_mpn!r}, expected {expected_mpn!r}",
                    expected_mpn=expected_mpn, observed_mpn=actual_mpn))
            else:
                items.append(_item(f"{ref}:mpn", PASS,
                                   expected_mpn=expected_mpn,
                                   observed_mpn=actual_mpn))
            pads = _pads(observed, f"snapshot.parts.{ref}")
            for role, spec in roles.items():
                missing = sorted(set(spec["pads"]) - set(pads))
                findings: list[str] = []
                if missing:
                    findings.append(f"{where}.pad_roles.{role}: absent pads {missing}")
                expected_net = spec.get("net")
                actual_nets = [str(pads[pad].get("net", pads[pad].get("net_name", "")))
                               for pad in spec["pads"] if _is_mapping(pads.get(pad))]
                if expected_net is not None and any(net != str(expected_net)
                                                   for net in actual_nets):
                    findings.append(
                        f"{where}.pad_roles.{role}: nets {actual_nets!r}, "
                        f"expected {expected_net!r}")
                items.append(_item(f"{ref}:{role}", FAIL if findings else PASS,
                                   *findings, pads=list(spec["pads"]),
                                   nets=actual_nets))
        except (ContractError, TypeError, ValueError) as exc:
            items.append(_malformed(where, exc))
    return _result("selected-part role", items)


def check_functional_vectors(contract: Mapping[str, Any],
                             snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Check signed pad-role vectors; opposite orientation is a hard failure."""
    items: list[dict[str, Any]] = []
    try:
        cells = _cells(contract)
    except (ContractError, TypeError, ValueError) as exc:
        return _result("functional vector", [_malformed("cells", exc)])
    for cell_index, cell in enumerate(cells):
        try:
            cell_name = _cell_id(cell, cell_index)
            rows = _rows(cell, ("functional_vectors", "vectors"),
                         f"cells[{cell_index}]")
        except (ContractError, TypeError, ValueError) as exc:
            items.append(_malformed(f"cells[{cell_index}].functional_vectors", exc))
            continue
        for index, raw in enumerate(rows):
            subject = f"{cell_name}:vector[{index}]"
            try:
                if not _is_mapping(raw):
                    raise ContractError(f"{subject}: expected a mapping")
                vector_id = str(raw.get("id") or f"vector-{index}")
                start, start_label = _anchor(raw.get("from"), contract, snapshot,
                                             f"{subject}.from")
                end, end_label = _anchor(raw.get("to"), contract, snapshot,
                                         f"{subject}.to")
                expected = _point(raw.get("expected_direction",
                                          raw.get("expected", raw.get("direction"))),
                                  f"{subject}.expected_direction")
                expected_length = math.hypot(*expected)
                if expected_length <= EPS:
                    raise ContractError(f"{subject}.expected_direction: zero vector")
                unit = (expected[0] / expected_length, expected[1] / expected_length)
                actual = (end[0] - start[0], end[1] - start[1])
                actual_length = math.hypot(*actual)
                if actual_length <= EPS:
                    items.append(_item(subject, FAIL,
                                       f"{vector_id}: {start_label} and {end_label} coincide"))
                    continue
                projection = actual[0] * unit[0] + actual[1] * unit[1]
                lateral = abs(actual[0] * unit[1] - actual[1] * unit[0])
                min_projection = _finite(raw.get("min_projection_mm", 0.0),
                                         f"{subject}.min_projection_mm",
                                         nonnegative=True)
                # A signed vector must point forward even when its caller uses
                # the natural zero projection floor.
                forward_floor = max(min_projection, EPS)
                findings = []
                if projection < forward_floor:
                    findings.append(
                        f"{vector_id}: signed projection {projection:.6f} mm is "
                        f"below {forward_floor:.6f} mm; functional orientation is reversed")
                if "max_lateral_mm" in raw:
                    max_lateral = _finite(raw["max_lateral_mm"],
                                          f"{subject}.max_lateral_mm",
                                          nonnegative=True)
                    if lateral > max_lateral + EPS:
                        findings.append(
                            f"{vector_id}: lateral offset {lateral:.6f} mm exceeds "
                            f"{max_lateral:.6f} mm")
                if "max_angle_deg" in raw:
                    max_angle = _finite(raw["max_angle_deg"],
                                        f"{subject}.max_angle_deg",
                                        nonnegative=True)
                    if max_angle > 180:
                        raise ContractError(f"{subject}.max_angle_deg: cannot exceed 180")
                    cosine = projection / actual_length
                    angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
                    if angle > max_angle + EPS:
                        findings.append(
                            f"{vector_id}: angle {angle:.3f} deg exceeds {max_angle:.3f} deg")
                items.append(_item(subject, FAIL if findings else PASS, *findings,
                                   id=vector_id, from_anchor=start_label,
                                   to_anchor=end_label,
                                   actual_vector_mm=list(actual),
                                   projection_mm=projection,
                                   lateral_mm=lateral))
            except (ContractError, TypeError, ValueError) as exc:
                items.append(_malformed(subject, exc))
    return _result("functional vector", items)


def _orient(a: tuple[float, float], b: tuple[float, float],
            c: tuple[float, float]) -> float:
    return ((b[0] - a[0]) * (c[1] - a[1])
            - (b[1] - a[1]) * (c[0] - a[0]))


def _on_segment(a: tuple[float, float], b: tuple[float, float],
                p: tuple[float, float]) -> bool:
    return (min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS
            and min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS
            and abs(_orient(a, b, p)) <= EPS)


def _segments_intersect(a: tuple[float, float], b: tuple[float, float],
                        c: tuple[float, float], d: tuple[float, float]) -> bool:
    o1, o2, o3, o4 = (_orient(a, b, c), _orient(a, b, d),
                      _orient(c, d, a), _orient(c, d, b))
    proper = (((o1 > EPS and o2 < -EPS) or (o1 < -EPS and o2 > EPS))
              and ((o3 > EPS and o4 < -EPS) or (o3 < -EPS and o4 > EPS)))
    return proper or ((abs(o1) <= EPS and _on_segment(a, b, c))
                      or (abs(o2) <= EPS and _on_segment(a, b, d))
                      or (abs(o3) <= EPS and _on_segment(c, d, a))
                      or (abs(o4) <= EPS and _on_segment(c, d, b)))


def _same_point(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return math.hypot(a[0] - b[0], a[1] - b[1]) <= EPS


def check_local_paths(contract: Mapping[str, Any],
                      snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Grade ordered local two-terminal paths and reject geometric crossings."""
    items: list[dict[str, Any]] = []
    parsed: list[dict[str, Any]] = []
    try:
        cells = _cells(contract)
    except (ContractError, TypeError, ValueError) as exc:
        return _result("local path", [_malformed("cells", exc)])
    for cell_index, cell in enumerate(cells):
        try:
            cell_name = _cell_id(cell, cell_index)
            rows = _rows(cell, ("local_paths", "two_terminal_paths"),
                         f"cells[{cell_index}]")
        except (ContractError, TypeError, ValueError) as exc:
            items.append(_malformed(f"cells[{cell_index}].local_paths", exc))
            continue
        for index, raw in enumerate(rows):
            subject = f"{cell_name}:path[{index}]"
            try:
                if not _is_mapping(raw):
                    raise ContractError(f"{subject}: expected a mapping")
                path_id = str(raw.get("id") or f"path-{index}")
                ordered = raw.get("ordered", raw.get("anchors", raw.get("pads")))
                if not isinstance(ordered, list) or len(ordered) < 2:
                    raise ContractError(f"{subject}.ordered: needs at least two anchors")
                resolved = [_anchor(value, contract, snapshot,
                                    f"{subject}.ordered[{anchor_index}]")
                            for anchor_index, value in enumerate(ordered)]
                points = [value[0] for value in resolved]
                labels = [value[1] for value in resolved]
                findings: list[str] = []
                for edge_index, (left, right) in enumerate(zip(points, points[1:])):
                    if _same_point(left, right):
                        findings.append(f"{path_id}: zero-length transition at index {edge_index}")
                # Any reference named more than once inside an ordered path is
                # a local component transition: its two pad anchors must be
                # adjacent.  This catches a two-terminal part whose physical
                # pad order was interleaved by placement.
                refs: dict[str, list[int]] = {}
                for anchor_index, label in enumerate(labels):
                    if "." in label:
                        refs.setdefault(label.split(".", 1)[0], []).append(anchor_index)
                explicit_refs = [str(value) for value in raw.get("two_terminal_refs", [])]
                inferred_refs = set()
                for ref, positions in refs.items():
                    part = _parts(snapshot).get(ref)
                    if (_is_mapping(part)
                            and len(_pads(part, f"snapshot.parts.{ref}")) == 2
                            and len(positions) == 2):
                        inferred_refs.add(ref)
                for ref in sorted(set(explicit_refs) | inferred_refs):
                    positions = refs.get(ref, [])
                    if len(positions) != 2 or positions[1] != positions[0] + 1:
                        findings.append(
                            f"{path_id}: two-terminal {ref} pads must occur "
                            "exactly once and adjacent")
                    else:
                        pad_names = {labels[position].split(".", 1)[1]
                                     for position in positions}
                        try:
                            part = _parts(snapshot).get(ref)
                            known = set(_pads(part, f"snapshot.parts.{ref}")) \
                                if _is_mapping(part) else set()
                        except ContractError:
                            known = set()
                        if len(known) == 2 and pad_names != known:
                            findings.append(
                                f"{path_id}: {ref} transition uses {sorted(pad_names)}, "
                                f"expected its two pads {sorted(known)}")
                parsed.append({"subject": subject, "id": path_id,
                               "cell": cell_name, "points": points,
                               "labels": labels, "findings": findings})
            except (ContractError, TypeError, ValueError) as exc:
                items.append(_malformed(subject, exc))

    # Compare the complete set at once.  Crossings are not order-dependent and
    # cannot be made green by reserving/routing one path before another.
    for left_index, left in enumerate(parsed):
        for right_index in range(left_index, len(parsed)):
            right = parsed[right_index]
            if left["cell"] != right["cell"]:
                continue
            for li, (a, b) in enumerate(zip(left["points"], left["points"][1:])):
                rstart = li + 2 if left_index == right_index else 0
                for ri, (c, d) in enumerate(zip(right["points"], right["points"][1:])):
                    if left_index == right_index and ri < rstart:
                        continue
                    if not _segments_intersect(a, b, c, d):
                        continue
                    shared_labels = {
                        left["labels"][li], left["labels"][li + 1]
                    } & {
                        right["labels"][ri], right["labels"][ri + 1]
                    }
                    shared_points = ({_point_key(a), _point_key(b)}
                                     & {_point_key(c), _point_key(d)})
                    if shared_labels and shared_points:
                        # A shared authored anchor is a legal branch/end.  An
                        # overlap beyond that point remains a crossing.
                        collinear = abs(_orient(a, b, c)) <= EPS and abs(_orient(a, b, d)) <= EPS
                        if not collinear:
                            continue
                        if sum(_same_point(p, q) for p in (a, b) for q in (c, d)) == 1:
                            continue
                    message = (f"local paths {left['id']} edge {li} and "
                               f"{right['id']} edge {ri} cross/overlap")
                    left["findings"].append(message)
                    if right is not left:
                        right["findings"].append(message)
    for row in parsed:
        items.append(_item(row["subject"], FAIL if row["findings"] else PASS,
                           *row["findings"], id=row["id"],
                           ordered=row["labels"],
                           points_mm=[list(point) for point in row["points"]]))
    return _result("local path", items)


def _point_key(point: tuple[float, float]) -> tuple[int, int]:
    return (round(point[0] / EPS), round(point[1] / EPS))


def _layers(value: Mapping[str, Any], where: str) -> frozenset[str]:
    raw = value.get("layers", value.get("layer"))
    if isinstance(raw, str):
        layers = [raw]
    elif isinstance(raw, list):
        layers = [str(item) for item in raw]
    else:
        raise ContractError(f"{where}.layers: expected layer name(s)")
    if not layers or any(not item.strip() for item in layers):
        raise ContractError(f"{where}.layers: cannot be empty")
    return frozenset(layers)


def _bbox(value: Mapping[str, Any], where: str) -> tuple[float, float, float, float]:
    if "bbox" in value:
        raw = value["bbox"]
        if (_is_mapping(raw) and all(key in raw for key in ("x0", "y0", "x1", "y1"))):
            box = tuple(_finite(raw[key], f"{where}.bbox.{key}")
                        for key in ("x0", "y0", "x1", "y1"))
        elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and len(raw) == 4:
            box = tuple(_finite(raw[index], f"{where}.bbox[{index}]")
                        for index in range(4))
        else:
            raise ContractError(f"{where}.bbox: expected [x0,y0,x1,y1]")
    elif "polygon" in value:
        points = _points(value["polygon"], f"{where}.polygon", minimum=3)
        box = (min(point[0] for point in points), min(point[1] for point in points),
               max(point[0] for point in points), max(point[1] for point in points))
    elif "path" in value:
        points = _points(value["path"], f"{where}.path")
        width = _finite(value.get("width_mm", 0.0), f"{where}.width_mm",
                        nonnegative=True)
        half = width / 2.0
        box = (min(point[0] for point in points) - half,
               min(point[1] for point in points) - half,
               max(point[0] for point in points) + half,
               max(point[1] for point in points) + half)
    elif "at" in value and ("diameter_mm" in value or "radius_mm" in value):
        center = _point(value["at"], f"{where}.at")
        radius = (_finite(value["radius_mm"], f"{where}.radius_mm", positive=True)
                  if "radius_mm" in value else
                  _finite(value["diameter_mm"], f"{where}.diameter_mm", positive=True) / 2)
        box = (center[0] - radius, center[1] - radius,
               center[0] + radius, center[1] + radius)
    else:
        raise ContractError(f"{where}: expected bbox, polygon, or path geometry")
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        raise ContractError(f"{where}: geometry has a degenerate bounding box")
    return (x0, y0, x1, y1)


def _boxes_overlap(left: tuple[float, float, float, float],
                   right: tuple[float, float, float, float],
                   clearance: float = 0.0) -> bool:
    return not (left[2] + clearance <= right[0]
                or right[2] + clearance <= left[0]
                or left[3] + clearance <= right[1]
                or right[3] + clearance <= left[1])


def _reservations(
        contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parsed: list[dict[str, Any]] = []
    bad: list[dict[str, Any]] = []
    try:
        cells = _cells(contract)
    except (ContractError, TypeError, ValueError) as exc:
        return [], [_malformed("cells", exc)]
    for cell_index, cell in enumerate(cells):
        try:
            cell_name = _cell_id(cell, cell_index)
            rows = _rows(cell, ("reservations", "route_reservations"),
                         f"cells[{cell_index}]")
        except (ContractError, TypeError, ValueError) as exc:
            bad.append(_malformed(f"cells[{cell_index}].reservations", exc))
            continue
        for index, raw in enumerate(rows):
            subject = f"{cell_name}:reservation[{index}]"
            try:
                if not _is_mapping(raw):
                    raise ContractError(f"{subject}: expected a mapping")
                reservation_id = _text(raw.get("id"), f"{subject}.id")
                commodity = _text(raw.get("commodity", raw.get("owner")),
                                  f"{subject}.commodity")
                parsed.append({"subject": subject, "cell": cell_name,
                               "id": reservation_id, "commodity": commodity,
                               "layers": _layers(raw, subject),
                               "bbox": _bbox(raw, subject), "raw": raw,
                               "findings": []})
            except (ContractError, TypeError, ValueError) as exc:
                bad.append(_malformed(subject, exc))
    return parsed, bad


def _obstacles(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_rows = snapshot.get("obstacles", [])
    rows = _list(raw_rows, "snapshot.obstacles")
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not _is_mapping(raw):
            raise ContractError(f"snapshot.obstacles[{index}]: expected a mapping")
        where = f"snapshot.obstacles[{index}]"
        oid = str(raw.get("id") or f"obstacle-{index}")
        layers = _layers(raw, where)
        result.append({"id": oid, "layers": layers, "bbox": _bbox(raw, where),
                       "kind": str(raw.get("kind") or "obstacle"), "raw": raw})
    return result


def check_reservations(contract: Mapping[str, Any],
                       snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate all commodity reservations simultaneously on their layers."""
    parsed, bad = _reservations(contract)
    items = list(bad)
    try:
        obstacles = _obstacles(snapshot)
    except (ContractError, TypeError, ValueError) as exc:
        if parsed:
            items.append(_malformed("snapshot.obstacles", exc))
        obstacles = []
    seen_ids: dict[tuple[str, str], dict[str, Any]] = {}
    for row in parsed:
        key = (row["cell"], row["id"])
        if key in seen_ids:
            row["findings"].append(
                f"{row['cell']}: duplicate reservation id {row['id']!r}")
            seen_ids[key]["findings"].append(
                f"{row['cell']}: duplicate reservation id {row['id']!r}")
        seen_ids[key] = row
    for left_index, left in enumerate(parsed):
        for right in parsed[left_index + 1:]:
            if left["cell"] != right["cell"]:
                continue
            if not (left["layers"] & right["layers"]):
                continue
            if left["commodity"] == right["commodity"]:
                continue
            if _boxes_overlap(left["bbox"], right["bbox"]):
                message = (f"{left['cell']}: simultaneous reservations {left['id']} "
                           f"({left['commodity']}) and {right['id']} "
                           f"({right['commodity']}) overlap on "
                           f"{sorted(left['layers'] & right['layers'])}")
                left["findings"].append(message)
                right["findings"].append(message)
    for row in parsed:
        allowed = {str(value) for value in row["raw"].get("allowed_obstacles", [])}
        for obstacle in obstacles:
            if obstacle["id"] in allowed or not (row["layers"] & obstacle["layers"]):
                continue
            if _boxes_overlap(row["bbox"], obstacle["bbox"]):
                row["findings"].append(
                    f"{row['cell']}: reservation {row['id']} collides with "
                    f"obstacle {obstacle['id']}")
        items.append(_item(row["subject"], FAIL if row["findings"] else PASS,
                           *row["findings"], id=row["id"],
                           commodity=row["commodity"], layers=sorted(row["layers"]),
                           bbox_mm=list(row["bbox"])))
    return _result("simultaneous reservation", items)


def _pad_record(snapshot: Mapping[str, Any], token: str) -> Mapping[str, Any]:
    if "." not in token:
        raise ContractError(f"pad {token!r}: expected REF.PAD")
    ref, pad = token.split(".", 1)
    part = _parts(snapshot).get(ref)
    if not _is_mapping(part):
        raise ContractError(f"pad {token}: footprint is absent")
    record = _pads(part, f"snapshot.parts.{ref}").get(pad)
    if not _is_mapping(record):
        raise ContractError(f"pad {token}: pad is absent")
    return record


def _role_pad_tokens(contract: Mapping[str, Any], predicate: Any) -> set[str]:
    result: set[str] = set()
    for ref, selection in _selections(contract):
        for role, spec in _role_specs(selection, f"selected_parts.{ref}").items():
            if predicate(role, spec):
                result.update(f"{ref}.{pad}" for pad in spec["pads"])
    return result


def _constrained_pad_rows(contract: Mapping[str, Any],
                          snapshot: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]],
                                                               list[dict[str, Any]]]:
    candidates: dict[str, dict[str, Any]] = {}
    bad: list[dict[str, Any]] = []
    try:
        role_tokens = _role_pad_tokens(
            contract,
            lambda _role, spec: bool(spec.get("constrained"))
            or str(spec.get("escape") or "").lower() == "constrained")
        for token in role_tokens:
            candidates.setdefault(token, {"pad": token, "sources": []})["sources"].append(
                "selected functional pad role")
        for ref, part in _parts(snapshot).items():
            if not _is_mapping(part):
                continue
            for pad_number, pad in _pads(part, f"snapshot.parts.{ref}").items():
                if not _is_mapping(pad):
                    continue
                constrained = bool(pad.get("constrained"))
                aperture = pad.get("escape_aperture_mm")
                envelope = pad.get("route_envelope_mm",
                                   pad.get("required_envelope_mm"))
                if aperture is not None and envelope is not None:
                    constrained = (_finite(aperture, f"{ref}.{pad_number}.escape_aperture_mm",
                                           nonnegative=True)
                                   < _finite(envelope, f"{ref}.{pad_number}.route_envelope_mm",
                                             positive=True) - EPS)
                if constrained:
                    token = f"{ref}.{pad_number}"
                    candidates.setdefault(token, {"pad": token, "sources": []})[
                        "sources"].append("measured escape aperture")
        for cell_index, cell in enumerate(_cells(contract)):
            cell_name = _cell_id(cell, cell_index)
            raw_candidates = cell.get("constrained_pads", [])
            if not isinstance(raw_candidates, list):
                raise ContractError(f"cells[{cell_index}].constrained_pads: expected a list")
            decisions: dict[str, Mapping[str, Any]] = {}
            raw_decisions = cell.get("escape_decisions", [])
            if not isinstance(raw_decisions, list):
                raise ContractError(f"cells[{cell_index}].escape_decisions: expected a list")
            for decision_index, decision in enumerate(raw_decisions):
                if not _is_mapping(decision):
                    bad.append(_malformed(
                        f"{cell_name}:escape_decisions[{decision_index}]",
                        ContractError("escape decision must be a mapping")))
                    continue
                token = str(decision.get("pad") or "").strip()
                if not token or token in decisions:
                    bad.append(_malformed(
                        f"{cell_name}:escape_decisions[{decision_index}]",
                        ContractError("pad must be non-empty and unique within the cell")))
                    continue
                decisions[token] = decision
            for candidate_index, raw in enumerate(raw_candidates):
                if isinstance(raw, str):
                    token, embedded = raw, None
                elif _is_mapping(raw):
                    token = str(raw.get("pad") or "").strip()
                    embedded = raw.get("decision")
                else:
                    bad.append(_malformed(
                        f"{cell_name}:constrained_pads[{candidate_index}]",
                        ContractError("constrained pad must be REF.PAD or a mapping")))
                    continue
                if not token:
                    bad.append(_malformed(
                        f"{cell_name}:constrained_pads[{candidate_index}]",
                        ContractError("constrained pad requires pad: REF.PAD")))
                    continue
                row = candidates.setdefault(token, {"pad": token, "sources": []})
                row["cell"] = cell_name
                row["sources"].append("cell constrained-pad declaration")
                if embedded is not None:
                    row["decision"] = embedded
            for token, decision in decisions.items():
                row = candidates.setdefault(token, {"pad": token, "sources": []})
                row["cell"] = cell_name
                row["decision"] = decision
                row["sources"].append("escape decision declaration")
    except (ContractError, TypeError, ValueError) as exc:
        bad.append(_malformed("constrained-pad census", exc))
    return candidates, bad


def _point_in_box(point: tuple[float, float],
                  box: tuple[float, float, float, float]) -> bool:
    return (box[0] - EPS <= point[0] <= box[2] + EPS
            and box[1] - EPS <= point[1] <= box[3] + EPS)


def _segment_hits_box(start: tuple[float, float], end: tuple[float, float],
                      box: tuple[float, float, float, float]) -> bool:
    if _point_in_box(start, box) or _point_in_box(end, box):
        return True
    corners = _box_corners(box)
    return any(_segments_intersect(start, end, left, right)
               for left, right in zip(corners, corners[1:] + corners[:1]))


def _path_hits_box(points: Sequence[tuple[float, float]], width: float,
                   box: tuple[float, float, float, float]) -> bool:
    half = width / 2
    expanded = (box[0] - half, box[1] - half,
                box[2] + half, box[3] + half)
    return any(_segment_hits_box(start, end, expanded)
               for start, end in zip(points, points[1:]))


def _decision_collisions(
        decision: Mapping[str, Any], points: Sequence[tuple[float, float]],
        snapshot: Mapping[str, Any], where: str,
        extra_obstacles: Sequence[Mapping[str, Any]] = (),
) -> list[str]:
    width = _finite(decision.get("trace_width_mm", decision.get("width_mm", 0.001)),
                    f"{where}.trace_width_mm", positive=True)
    layers = _layers(decision, where)
    own = {str(value) for value in decision.get("reservation_ids", [])}
    if decision.get("reservation"):
        own.add(str(decision["reservation"]))
    findings: list[str] = []
    try:
        obstacles = _obstacles(snapshot)
    except ContractError as exc:
        raise ContractError(f"{where}: cannot grade collisions: {exc}") from exc
    for obstacle in [*obstacles, *extra_obstacles]:
        if obstacle["id"] in own or not (layers & obstacle["layers"]):
            continue
        if _path_hits_box(points, width, obstacle["bbox"]):
            findings.append(f"{where}: escape collides with obstacle {obstacle['id']}")
    return findings


def _grade_escape_decision(
        token: str, decision: Any, snapshot: Mapping[str, Any], where: str,
        reservations: Sequence[Mapping[str, Any]] = (),
) -> tuple[str, list[str], dict[str, Any]]:
    if decision is None:
        return FAIL, [f"{token}: constrained pad has no explicit escape decision"], {}
    if not _is_mapping(decision):
        raise ContractError(f"{where}.decision: expected a mapping")
    kind = str(decision.get("kind") or decision.get("type") or "").strip().lower()
    if not kind:
        raise ContractError(f"{where}.decision.kind: expected non-empty text")
    if kind in {"backtrack", "placement_backtrack", "placement-change"}:
        return FAIL, [f"{token}: decision requires placement backtrack"], {"kind": kind}
    pad_record = _pad_record(snapshot, token)
    pad_at = _point(pad_record, f"snapshot pad {token}")
    findings: list[str] = []
    evidence: dict[str, Any] = {"kind": kind}
    if kind in {"planar", "verified_planar", "planar_escape"}:
        points = _points(decision.get("path"), f"{where}.decision.path")
        if not _same_point(points[0], pad_at):
            findings.append(f"{token}: planar escape path does not start at pad")
        if decision.get("verified") is not True:
            findings.append(f"{token}: planar escape is not explicitly verified")
        required = _finite(decision.get("required_clearance_mm", 0.0),
                           f"{where}.required_clearance_mm", nonnegative=True)
        measured = _finite(decision.get("clearance_mm"), f"{where}.clearance_mm",
                           nonnegative=True)
        if measured + EPS < required:
            findings.append(
                f"{token}: planar clearance {measured:.6f} mm is below "
                f"{required:.6f} mm")
        findings.extend(_decision_collisions(
            decision, points, snapshot, where, reservations))
        evidence.update(path_mm=[list(point) for point in points],
                        clearance_mm=measured)
    elif kind in {"dogbone", "exact_dogbone"}:
        raw_path = decision.get("path")
        points = _points(raw_path, f"{where}.decision.path")
        via_at = _point(decision.get("via_at", points[-1]), f"{where}.decision.via_at")
        if not _same_point(points[0], pad_at):
            findings.append(f"{token}: dogbone path does not start at pad")
        if not _same_point(points[-1], via_at):
            findings.append(f"{token}: dogbone path does not terminate at its via")
        diameter = _finite(decision.get("via_diameter_mm"),
                           f"{where}.decision.via_diameter_mm", positive=True)
        drill = _finite(decision.get("via_drill_mm"),
                        f"{where}.decision.via_drill_mm", positive=True)
        if drill >= diameter:
            findings.append(f"{token}: via drill must be smaller than its diameter")
        required = _finite(decision.get("required_clearance_mm", 0.0),
                           f"{where}.required_clearance_mm", nonnegative=True)
        measured = _finite(decision.get("clearance_mm"), f"{where}.clearance_mm",
                           nonnegative=True)
        if measured + EPS < required:
            findings.append(
                f"{token}: dogbone clearance {measured:.6f} mm is below "
                f"{required:.6f} mm")
        size = pad_record.get("size_mm")
        if size is not None:
            sx, sy = _point(size, f"snapshot pad {token}.size_mm")
            inside = (abs(via_at[0] - pad_at[0]) <= sx / 2 + EPS
                      and abs(via_at[1] - pad_at[1]) <= sy / 2 + EPS)
            if inside:
                findings.append(f"{token}: dogbone via centre remains inside the pad")
        elif decision.get("via_outside_pad") is not True:
            raise ContractError(
                f"{where}: pad size is absent; via_outside_pad: true evidence is required")
        findings.extend(_decision_collisions(
            decision, points, snapshot, where, reservations))
        evidence.update(path_mm=[list(point) for point in points],
                        via_at_mm=list(via_at), via_diameter_mm=diameter,
                        via_drill_mm=drill, clearance_mm=measured)
    elif kind in {"via_in_pad", "selective_via_in_pad"}:
        fabrication = snapshot.get("fabrication", {})
        if not _is_mapping(fabrication):
            raise ContractError("snapshot.fabrication: expected a mapping")
        capability = bool(fabrication.get("selective_via_in_pad",
                                          fabrication.get("via_in_pad")))
        process = decision.get("process", decision)
        if not _is_mapping(process):
            raise ContractError(f"{where}.decision.process: expected a mapping")
        approved = process.get("approved") is True
        filled = process.get("filled") is True or process.get("filled_capped") is True
        capped = process.get("capped") is True or process.get("filled_capped") is True
        cad_rule = process.get("cad_rule") is True or process.get("cad_validated") is True
        if not capability:
            findings.append(f"{token}: selected fabrication does not allow selective via-in-pad")
        if not approved or not filled or not capped or not cad_rule:
            findings.append(
                f"{token}: via-in-pad needs approved, filled, capped, "
                "CAD-validated process evidence")
        evidence.update(process={"approved": approved, "filled": filled,
                                 "capped": capped, "cad_rule": cad_rule},
                        fabrication_capability=capability)
    else:
        raise ContractError(
            f"{where}.decision.kind {kind!r}: expected planar, dogbone, "
            "selective_via_in_pad, or placement_backtrack")
    return (FAIL if findings else PASS), findings, evidence


def check_constrained_pad_escapes(contract: Mapping[str, Any],
                                  snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Census constrained pads and require one manufacturable local decision."""
    candidates, items = _constrained_pad_rows(contract, snapshot)
    reservations, reservation_bad = _reservations(contract)
    if candidates:
        items.extend(reservation_bad)
    for token in sorted(candidates):
        row = candidates[token]
        subject = f"{row.get('cell', 'selected')}:{token}"
        try:
            status, findings, evidence = _grade_escape_decision(
                token, row.get("decision"), snapshot, subject, reservations)
            items.append(_item(subject, status, *findings, pad=token,
                               sources=sorted(set(row["sources"])), **evidence))
        except (ContractError, TypeError, ValueError) as exc:
            items.append(_malformed(subject, exc))
    return _result("constrained-pad escape", items)


def _ground_candidates(contract: Mapping[str, Any],
                       snapshot: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]],
                                                            list[dict[str, Any]]]:
    candidates: dict[str, dict[str, Any]] = {}
    bad: list[dict[str, Any]] = []
    try:
        tokens = _role_pad_tokens(
            contract,
            lambda role, spec: bool(spec.get("critical_ground"))
            or role.lower() in {"ground", "gnd", "return", "critical_ground",
                                "bypass_ground", "ground_return"}
            or "ground" in role.lower())
        for token in tokens:
            candidates.setdefault(token, {"pad": token, "sources": []})[
                "sources"].append("selected critical-ground role")
        for ref, part in _parts(snapshot).items():
            if not _is_mapping(part):
                continue
            for pad_number, pad in _pads(part, f"snapshot.parts.{ref}").items():
                if _is_mapping(pad) and pad.get("critical_ground") is True:
                    token = f"{ref}.{pad_number}"
                    candidates.setdefault(token, {"pad": token, "sources": []})[
                        "sources"].append("measured critical-ground pad")
        for cell_index, cell in enumerate(_cells(contract)):
            cell_name = _cell_id(cell, cell_index)
            rows = cell.get("critical_ground_pads", [])
            if not isinstance(rows, list):
                raise ContractError(f"cells[{cell_index}].critical_ground_pads: expected list")
            egress_rows = cell.get("ground_egress", cell.get("ground_egresses", []))
            if not isinstance(egress_rows, list):
                raise ContractError(f"cells[{cell_index}].ground_egress: expected list")
            egress_by_pad: dict[str, Mapping[str, Any]] = {}
            for egress_index, egress in enumerate(egress_rows):
                if not _is_mapping(egress):
                    bad.append(_malformed(
                        f"{cell_name}:ground_egress[{egress_index}]",
                        ContractError("ground egress must be a mapping")))
                    continue
                token = str(egress.get("pad") or "").strip()
                if not token or token in egress_by_pad:
                    bad.append(_malformed(
                        f"{cell_name}:ground_egress[{egress_index}]",
                        ContractError("pad must be non-empty and unique")))
                    continue
                egress_by_pad[token] = egress
            for row_index, raw in enumerate(rows):
                if isinstance(raw, str):
                    token, embedded = raw, None
                elif _is_mapping(raw):
                    token = str(raw.get("pad") or "").strip()
                    embedded = raw.get("egress")
                else:
                    bad.append(_malformed(
                        f"{cell_name}:critical_ground_pads[{row_index}]",
                        ContractError("critical ground must be REF.PAD or mapping")))
                    continue
                if not token:
                    bad.append(_malformed(
                        f"{cell_name}:critical_ground_pads[{row_index}]",
                        ContractError("critical ground requires pad: REF.PAD")))
                    continue
                target = candidates.setdefault(token, {"pad": token, "sources": []})
                target["cell"] = cell_name
                target["sources"].append("cell critical-ground declaration")
                if embedded is not None:
                    target["egress"] = embedded
            for token, egress in egress_by_pad.items():
                target = candidates.setdefault(token, {"pad": token, "sources": []})
                target["cell"] = cell_name
                target["sources"].append("ground-egress declaration")
                target["egress"] = egress
    except (ContractError, TypeError, ValueError) as exc:
        bad.append(_malformed("critical-ground census", exc))
    return candidates, bad


def _grade_ground_egress(
        token: str, egress: Any, snapshot: Mapping[str, Any], where: str,
        reservation_ids: set[str],
        reservations: Sequence[Mapping[str, Any]] = (),
) -> tuple[str, list[str], dict[str, Any]]:
    if egress is None:
        return FAIL, [f"{token}: critical ground pad has no local egress"], {}
    if not _is_mapping(egress):
        raise ContractError(f"{where}.egress: expected a mapping")
    kind = str(egress.get("kind") or "").strip().lower()
    if kind in {"backtrack", "placement_backtrack"}:
        return FAIL, [f"{token}: ground egress requires placement backtrack"], {"kind": kind}
    pad_at = _point(_pad_record(snapshot, token), f"snapshot pad {token}")
    findings: list[str] = []
    evidence: dict[str, Any] = {"kind": kind}
    if kind in {"plane_via", "via_to_plane"}:
        via_at = _point(egress.get("via_at"), f"{where}.via_at")
        points = [pad_at, via_at]
        target = str(egress.get("plane") or egress.get("to_layer") or "").strip()
        if not target:
            raise ContractError(f"{where}: plane_via requires plane/to_layer")
        clearance = _finite(egress.get("clearance_mm"), f"{where}.clearance_mm",
                            nonnegative=True)
        required = _finite(egress.get("required_clearance_mm", 0.0),
                           f"{where}.required_clearance_mm", nonnegative=True)
        if clearance + EPS < required:
            findings.append(
                f"{token}: ground-via clearance {clearance:.6f} mm is below "
                f"{required:.6f} mm")
        findings.extend(_decision_collisions(
            egress, points, snapshot, where, reservations))
        evidence.update(via_at_mm=list(via_at), plane=target,
                        clearance_mm=clearance)
    elif kind in {"planar_bridge", "same_net_bridge"}:
        points = _points(egress.get("path"), f"{where}.path")
        if not _same_point(points[0], pad_at):
            findings.append(f"{token}: ground bridge does not start at pad")
        reservation = str(egress.get("reservation") or "").strip()
        if not ((reservation and reservation in reservation_ids)
                or egress.get("reserved") is True):
            findings.append(f"{token}: planar ground bridge is not reserved for later waves")
        findings.extend(_decision_collisions(
            egress, points, snapshot, where, reservations))
        evidence.update(path_mm=[list(point) for point in points],
                        reservation=reservation or None)
    elif kind in {"same_net_zone", "continuous_zone"}:
        if egress.get("connected") is not True or not str(egress.get("zone") or "").strip():
            findings.append(f"{token}: same-net zone egress needs connected: true and a zone id")
        evidence.update(zone=egress.get("zone"), connected=egress.get("connected") is True)
    elif not kind:
        raise ContractError(f"{where}.kind: expected plane_via, planar_bridge, or same_net_zone")
    else:
        raise ContractError(f"{where}.kind {kind!r}: unknown ground-egress decision")
    return (FAIL if findings else PASS), findings, evidence


def check_critical_ground_egress(contract: Mapping[str, Any],
                                 snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Require local egress for every selected/declaratively critical ground pad."""
    candidates, items = _ground_candidates(contract, snapshot)
    reservations, reservation_bad = _reservations(contract)
    if candidates:
        items.extend(reservation_bad)
    reservation_ids = {row["id"] for row in reservations}
    for token in sorted(candidates):
        row = candidates[token]
        subject = f"{row.get('cell', 'selected')}:{token}:ground"
        try:
            status, findings, evidence = _grade_ground_egress(
                token, row.get("egress"), snapshot, subject, reservation_ids,
                reservations)
            items.append(_item(subject, status, *findings, pad=token,
                               sources=sorted(set(row["sources"])), **evidence))
        except (ContractError, TypeError, ValueError) as exc:
            items.append(_malformed(subject, exc))
    return _result("critical-ground egress", items)


def _stack_layers(contract: Mapping[str, Any],
                  snapshot: Mapping[str, Any]) -> tuple[dict[str, float], Mapping[str, Any]]:
    stack = contract.get("stackup", snapshot.get("stackup"))
    if not _is_mapping(stack):
        raise ContractError("stackup: hot paths require a declared fabrication stack")
    raw_layers = stack.get("layers")
    layers: dict[str, float] = {}
    if _is_mapping(raw_layers):
        iterable = raw_layers.items()
        for name, raw in iterable:
            thickness = raw.get("copper_thickness_um") if _is_mapping(raw) else raw
            layers[str(name)] = _finite(thickness,
                                        f"stackup.layers.{name}.copper_thickness_um",
                                        positive=True)
    elif isinstance(raw_layers, list):
        for index, raw in enumerate(raw_layers):
            if not _is_mapping(raw):
                raise ContractError(f"stackup.layers[{index}]: expected a mapping")
            name = _text(raw.get("name"), f"stackup.layers[{index}].name")
            if name in layers:
                raise ContractError(f"stackup.layers: duplicate layer {name}")
            layers[name] = _finite(raw.get("copper_thickness_um"),
                                   f"stackup.layers[{index}].copper_thickness_um",
                                   positive=True)
    else:
        raise ContractError("stackup.layers: expected mapping or list")
    if not layers:
        raise ContractError("stackup.layers: copper-layer denominator is empty")
    return layers, stack


def _hot_path_rows(contract: Mapping[str, Any]) -> tuple[list[tuple[str, Mapping[str, Any]]],
                                                        list[dict[str, Any]]]:
    rows: list[tuple[str, Mapping[str, Any]]] = []
    bad: list[dict[str, Any]] = []
    try:
        for cell_index, cell in enumerate(_cells(contract)):
            cell_name = _cell_id(cell, cell_index)
            raw_rows = _rows(cell, ("hot_paths", "hot_path_lower_bounds"),
                             f"cells[{cell_index}]")
            for index, raw in enumerate(raw_rows):
                subject = f"{cell_name}:hot_path[{index}]"
                if not _is_mapping(raw):
                    bad.append(_malformed(subject,
                                          ContractError("hot path must be a mapping")))
                else:
                    rows.append((subject, raw))
    except (ContractError, TypeError, ValueError) as exc:
        bad.append(_malformed("hot paths", exc))
    return rows, bad


def _segment_layer(segment: Mapping[str, Any], layers: Mapping[str, float],
                   where: str) -> tuple[str, float]:
    if "layer" in segment:
        name = _text(segment.get("layer"), f"{where}.layer")
        if name not in layers:
            raise ContractError(f"{where}.layer {name!r}: absent from stackup")
        return name, layers[name]
    allowed = segment.get("allowed_layers")
    if not isinstance(allowed, list) or not allowed:
        raise ContractError(f"{where}: needs layer or non-empty allowed_layers")
    unknown = sorted(set(map(str, allowed)) - set(layers))
    if unknown:
        raise ContractError(f"{where}.allowed_layers: absent from stackup {unknown}")
    # A lower bound deliberately chooses the thickest permitted copper.  If
    # even this optimistic segment misses the budget, placement is impossible.
    name = max(map(str, allowed), key=lambda layer: layers[layer])
    return name, layers[name]


def _hot_segment_length(segment: Mapping[str, Any], contract: Mapping[str, Any],
                        snapshot: Mapping[str, Any], where: str) -> float:
    if "length_mm" in segment:
        return _finite(segment["length_mm"], f"{where}.length_mm", positive=True)
    start, _ = _anchor(segment.get("from"), contract, snapshot, f"{where}.from")
    end, _ = _anchor(segment.get("to"), contract, snapshot, f"{where}.to")
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length <= EPS:
        raise ContractError(f"{where}: endpoints coincide")
    return length


def check_hot_path_lower_bounds(contract: Mapping[str, Any],
                                snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Compare optimistic stack-aware PCB resistance with the named allocation."""
    rows, items = _hot_path_rows(contract)
    for subject, raw in rows:
        try:
            path_id = str(raw.get("id") or subject.rsplit("[", 1)[-1].rstrip("]"))
            allocation_value = raw.get("pcb_mohm_allocation",
                                       raw.get("pcb_allocation_mohm"))
            # A generic allocation is admissible only when its owner labels it
            # PCB-specific.  This prevents the historical error of comparing
            # copper alone with a complete rail/headroom number.
            if (allocation_value is None
                    and str(raw.get("allocation_scope") or "").lower() == "pcb"):
                allocation_value = raw.get("allocation_mohm")
            allocation = _finite(allocation_value,
                                 f"{subject}.pcb_mohm_allocation", positive=True)
            layers, stack = _stack_layers(contract, snapshot)
            temperature = _finite(raw.get("temperature_c", stack.get("temperature_c")),
                                  f"{subject}.temperature_c")
            reference_temperature = _finite(
                stack.get("reference_temperature_c", 20.0),
                "stackup.reference_temperature_c")
            tempco = _finite(stack.get("copper_tempco_per_c", 0.00393),
                             "stackup.copper_tempco_per_c", nonnegative=True)
            rho_ref = _finite(stack.get("copper_resistivity_ohm_m", 1.724e-8),
                              "stackup.copper_resistivity_ohm_m", positive=True)
            factor = 1.0 + tempco * (temperature - reference_temperature)
            if factor <= 0:
                raise ContractError(f"{subject}: non-positive temperature resistance factor")
            rho = rho_ref * factor
            segments = raw.get("segments")
            if segments is None:
                segment = {key: raw[key] for key in
                           ("from", "to", "layer", "allowed_layers", "length_mm",
                            "max_width_mm", "width_mm", "corridor_width_mm")
                           if key in raw}
                segments = [segment]
            if not isinstance(segments, list) or not segments:
                raise ContractError(f"{subject}.segments: expected a non-empty list")
            total_mohm = 0.0
            evidence_segments = []
            for index, segment in enumerate(segments):
                where = f"{subject}.segments[{index}]"
                if not _is_mapping(segment):
                    raise ContractError(f"{where}: expected a mapping")
                layer, thickness_um = _segment_layer(segment, layers, where)
                width_value = segment.get("max_width_mm",
                                          segment.get("corridor_width_mm",
                                                      segment.get("width_mm")))
                width_mm = _finite(width_value, f"{where}.max_width_mm", positive=True)
                length_mm = _hot_segment_length(segment, contract, snapshot, where)
                area_m2 = width_mm * 1e-3 * thickness_um * 1e-6
                resistance_mohm = rho * (length_mm * 1e-3) / area_m2 * 1e3
                total_mohm += resistance_mohm
                evidence_segments.append({
                    "layer": layer, "length_mm": length_mm,
                    "max_width_mm": width_mm,
                    "copper_thickness_um": thickness_um,
                    "lower_bound_mohm": resistance_mohm,
                })
            unavoidable_vias = raw.get("unavoidable_vias", 0)
            if isinstance(unavoidable_vias, bool):
                raise ContractError(f"{subject}.unavoidable_vias: expected integer")
            try:
                via_count = int(unavoidable_vias)
            except (TypeError, ValueError) as exc:
                raise ContractError(f"{subject}.unavoidable_vias: expected integer") from exc
            if via_count < 0 or via_count != unavoidable_vias:
                raise ContractError(f"{subject}.unavoidable_vias: expected non-negative integer")
            via_each = 0.0
            if via_count:
                via_each = _finite(raw.get("via_lower_bound_mohm_each"),
                                   f"{subject}.via_lower_bound_mohm_each",
                                   nonnegative=True)
                total_mohm += via_count * via_each
            joint = _finite(raw.get("joint_allowance_mohm", 0.0),
                            f"{subject}.joint_allowance_mohm", nonnegative=True)
            total_mohm += joint
            margin = allocation - total_mohm
            findings = []
            if margin <= EPS:
                findings.append(
                    f"{path_id}: optimistic hot-path lower bound {total_mohm:.6f} mOhm "
                    f"consumes/exceeds declared PCB allocation {allocation:.6f} mOhm")
            items.append(_item(subject, FAIL if findings else PASS, *findings,
                               id=path_id, temperature_c=temperature,
                               pcb_mohm_allocation=allocation,
                               lower_bound_mohm=total_mohm,
                               margin_mohm=margin, segments=evidence_segments,
                               unavoidable_vias=via_count,
                               via_lower_bound_mohm_each=via_each,
                               joint_allowance_mohm=joint))
        except (ContractError, TypeError, ValueError, KeyError) as exc:
            items.append(_malformed(subject, exc))
    return _result("hot-path lower bound", items)


def _transform(point: tuple[float, float], transform: Mapping[str, Any],
               where: str) -> tuple[float, float]:
    origin = _point(transform.get("origin", [0.0, 0.0]), f"{where}.origin")
    translate = transform.get("translate")
    if translate is None:
        translate = [transform.get("dx_mm", 0.0), transform.get("dy_mm", 0.0)]
    dx, dy = _point(translate, f"{where}.translate")
    angle = _finite(transform.get("rotation_deg", transform.get("rotate_deg", 0.0)),
                    f"{where}.rotation_deg")
    x, y = point[0] - origin[0], point[1] - origin[1]
    if transform.get("mirror_x") is True:
        x = -x
    if transform.get("mirror_y") is True or transform.get("mirror") is True:
        y = -y
    radians = math.radians(angle)
    rotated = (x * math.cos(radians) - y * math.sin(radians),
               x * math.sin(radians) + y * math.cos(radians))
    return (rotated[0] + origin[0] + dx, rotated[1] + origin[1] + dy)


def _cell_map(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for index, cell in enumerate(_cells(contract)):
        name = _cell_id(cell, index)
        if name in result:
            raise ContractError(f"cells: duplicate id {name}")
        result[name] = cell
    return result


def _replica_obstacles(cell: Mapping[str, Any], cell_name: str,
                       obstacles: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    explicit = cell.get("obstacle_ids")
    if explicit is not None:
        if not isinstance(explicit, list):
            raise ContractError(f"cell {cell_name}.obstacle_ids: expected list")
        wanted = {str(value) for value in explicit}
        return [obstacle for obstacle in obstacles if obstacle["id"] in wanted]
    result = []
    for obstacle in obstacles:
        raw = obstacle["raw"]
        owner = raw.get("cell", raw.get("owner_cell"))
        owners = raw.get("cells", [])
        if owner == cell_name or (isinstance(owners, list) and cell_name in owners):
            result.append(obstacle)
    return result


def _box_corners(box: tuple[float, float, float, float]) -> list[tuple[float, float]]:
    return [(box[0], box[1]), (box[2], box[1]),
            (box[2], box[3]), (box[0], box[3])]


def _normalized_obstacle_signature(obstacle: Mapping[str, Any],
                                   transform: Mapping[str, Any] | None,
                                   where: str, tolerance: float) -> tuple[Any, ...]:
    corners = _box_corners(obstacle["bbox"])
    if transform is not None:
        corners = [_transform(point, transform, where) for point in corners]
    quant = lambda value: round(value / tolerance) if tolerance > 0 else value
    geometry = tuple(sorted((quant(point[0]), quant(point[1])) for point in corners))
    return (str(obstacle["kind"]), tuple(sorted(obstacle["layers"])), geometry)


def _semantic_structure(cell: Mapping[str, Any]) -> Any:
    # Authors may pin an explicit semantic structure when refdes/net names vary
    # too much for automatic comparison.  Geometry, MPN and pads are still
    # re-measured independently below.
    return cell.get("structure", cell.get("structure_signature"))


def _member_refs(cell: Mapping[str, Any], where: str) -> set[str]:
    value = cell.get("members", [])
    if not isinstance(value, list):
        raise ContractError(f"{where}.members: expected a list")
    refs = {str(item.get("ref")) if _is_mapping(item) else str(item)
            for item in value}
    if "" in refs:
        raise ContractError(f"{where}.members: references cannot be empty")
    return refs


def _replica_role_signature(selection: Mapping[str, Any], where: str) -> dict[str, Any]:
    result = {}
    for role, spec in _role_specs(selection, where).items():
        result[role] = {
            "pads": tuple(spec["pads"]),
            "critical_ground": bool(spec.get("critical_ground")),
            "constrained": (bool(spec.get("constrained"))
                            or str(spec.get("escape") or "").lower() == "constrained"),
        }
    return result


def check_pilot_replica_equivalence(contract: Mapping[str, Any],
                                    snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Prove replica pad geometry/MPNs and local obstacle structure match pilot."""
    items: list[dict[str, Any]] = []
    try:
        cells = _cell_map(contract)
        selections = _selection_map(contract)
        rows = _list(contract.get("replicas", contract.get("replications", [])),
                     "replicas")
        parts = _parts(snapshot)
        obstacles = _obstacles(snapshot)
    except (ContractError, TypeError, ValueError) as exc:
        return _result("pilot/replica equivalence", [_malformed("replicas", exc)])
    for index, raw in enumerate(rows):
        subject = f"replicas[{index}]"
        try:
            if not _is_mapping(raw):
                raise ContractError(f"{subject}: expected a mapping")
            replica_id = str(raw.get("id") or f"replica-{index}")
            pilot_name = _text(raw.get("pilot"), f"{subject}.pilot")
            replica_name = _text(raw.get("replica", raw.get("cell")),
                                 f"{subject}.replica")
            if pilot_name not in cells or replica_name not in cells:
                raise ContractError(
                    f"{subject}: pilot/replica must name declared cells "
                    f"({pilot_name!r}, {replica_name!r})")
            ref_map = raw.get("ref_map", raw.get("member_map"))
            if not _is_mapping(ref_map) or not ref_map:
                raise ContractError(f"{subject}.ref_map: expected a non-empty mapping")
            transform = raw.get("transform", {})
            if not _is_mapping(transform):
                raise ContractError(f"{subject}.transform: expected a mapping")
            tolerance = _finite(raw.get("tolerance_mm", 0.01),
                                f"{subject}.tolerance_mm", positive=True)
            findings: list[str] = []
            compared_pads = 0
            pilot_members = _member_refs(cells[pilot_name], f"cell {pilot_name}")
            replica_members = _member_refs(cells[replica_name], f"cell {replica_name}")
            if pilot_members and set(map(str, ref_map)) != pilot_members:
                findings.append(
                    f"{replica_id}: ref_map does not cover pilot members "
                    f"{sorted(pilot_members)}")
            if replica_members and {str(value) for value in ref_map.values()} != replica_members:
                findings.append(
                    f"{replica_id}: ref_map does not cover replica members "
                    f"{sorted(replica_members)}")
            for pilot_ref, replica_ref_value in ref_map.items():
                pilot_ref, replica_ref = str(pilot_ref), str(replica_ref_value)
                pilot_part, replica_part = parts.get(pilot_ref), parts.get(replica_ref)
                if not _is_mapping(pilot_part) or not _is_mapping(replica_part):
                    findings.append(
                        f"{replica_id}: mapped parts {pilot_ref}->{replica_ref} must both exist")
                    continue
                pilot_mpn = str(pilot_part.get("mpn") or "")
                replica_mpn = str(replica_part.get("mpn") or "")
                if pilot_mpn != replica_mpn:
                    findings.append(
                        f"{replica_id}: exact-MPN mismatch {pilot_ref}={pilot_mpn!r}, "
                        f"{replica_ref}={replica_mpn!r}")
                pilot_selection = selections.get(pilot_ref)
                replica_selection = selections.get(replica_ref)
                if ((pilot_selection is None) != (replica_selection is None)
                        or (pilot_selection is not None
                            and _replica_role_signature(
                                pilot_selection, f"selected_parts.{pilot_ref}")
                            != _replica_role_signature(
                                replica_selection, f"selected_parts.{replica_ref}"))):
                    findings.append(
                        f"{replica_id}: functional pad-role mismatch "
                        f"{pilot_ref}->{replica_ref}")
                pilot_pads = _pads(pilot_part, f"snapshot.parts.{pilot_ref}")
                replica_pads = _pads(replica_part, f"snapshot.parts.{replica_ref}")
                if set(pilot_pads) != set(replica_pads):
                    findings.append(
                        f"{replica_id}: pad-set mismatch {pilot_ref}={sorted(pilot_pads)}, "
                        f"{replica_ref}={sorted(replica_pads)}")
                for pad in sorted(set(pilot_pads) & set(replica_pads)):
                    expected = _transform(_point(pilot_pads[pad],
                                                 f"snapshot.parts.{pilot_ref}.pads.{pad}"),
                                          transform, f"{subject}.transform")
                    actual = _point(replica_pads[pad],
                                    f"snapshot.parts.{replica_ref}.pads.{pad}")
                    error = math.hypot(expected[0] - actual[0], expected[1] - actual[1])
                    compared_pads += 1
                    if error > tolerance + EPS:
                        findings.append(
                            f"{replica_id}: geometry mismatch {pilot_ref}.{pad}->"
                            f"{replica_ref}.{pad}, transform error {error:.6f} mm > "
                            f"{tolerance:.6f} mm")
            pilot_structure = _semantic_structure(cells[pilot_name])
            replica_structure = _semantic_structure(cells[replica_name])
            if ((pilot_structure is None) != (replica_structure is None)
                    or (pilot_structure is not None and pilot_structure != replica_structure)):
                findings.append(
                    f"{replica_id}: pilot/replica semantic structure mismatch")
            pilot_obstacles = _replica_obstacles(cells[pilot_name], pilot_name, obstacles)
            replica_obstacles = _replica_obstacles(cells[replica_name], replica_name, obstacles)
            pilot_signatures = sorted(_normalized_obstacle_signature(
                obstacle, transform, f"{subject}.transform", tolerance)
                for obstacle in pilot_obstacles)
            replica_signatures = sorted(_normalized_obstacle_signature(
                obstacle, None, f"{subject}.replica", tolerance)
                for obstacle in replica_obstacles)
            if pilot_signatures != replica_signatures:
                findings.append(
                    f"{replica_id}: pilot/replica obstacle mismatch "
                    f"({len(pilot_signatures)} != {len(replica_signatures)} or geometry differs)")
            items.append(_item(subject, FAIL if findings else PASS, *findings,
                               id=replica_id, pilot=pilot_name,
                               replica=replica_name, compared_pads=compared_pads,
                               pilot_obstacles=len(pilot_signatures),
                               replica_obstacles=len(replica_signatures),
                               tolerance_mm=tolerance))
        except (ContractError, TypeError, ValueError, KeyError) as exc:
            items.append(_malformed(subject, exc))
    return _result("pilot/replica equivalence", items)


CHECKERS = {
    "selected_part_pad_roles": check_selected_part_pad_roles,
    "functional_vectors": check_functional_vectors,
    "local_paths": check_local_paths,
    "simultaneous_reservations": check_reservations,
    "constrained_pad_escapes": check_constrained_pad_escapes,
    "critical_ground_egress": check_critical_ground_egress,
    "hot_path_lower_bounds": check_hot_path_lower_bounds,
    "pilot_replica_equivalence": check_pilot_replica_equivalence,
}


def evaluate_placement_cells(contract: Any, snapshot: Any) -> dict[str, Any]:
    """Return the closed aggregate placement-cell report.

    Validation and every domain predicate are retained even when another
    predicate fails.  ``INCOMPLETE`` takes precedence because an unresolved
    declaration cannot support placement acceptance; then ``FAIL``, ``PASS``,
    and finally ``N-A`` for a genuinely simple/unscoped board.
    """
    validation = validate_declaration(contract, snapshot)
    if not _is_mapping(contract) or not _is_mapping(snapshot):
        checks = {name: _result(name.replace("_", " "), []) for name in CHECKERS}
    else:
        checks = {name: checker(contract, snapshot)
                  for name, checker in CHECKERS.items()}
    statuses = {row["status"] for row in checks.values()}
    if validation["status"] == INCOMPLETE or INCOMPLETE in statuses:
        status = INCOMPLETE
    elif FAIL in statuses:
        status = FAIL
    elif PASS in statuses:
        status = PASS
    else:
        status = NA
    coverage = {
        key: sum(row["coverage"][key] for row in checks.values())
        for key in ("passed", "failed", "incomplete", "not_applicable",
                    "graded", "total")
    }
    findings = list(validation["findings"])
    findings.extend(message for row in checks.values() for message in row["findings"])
    return {
        "schema": SCHEMA,
        "kind": "functional-cell-placement-checks-v1",
        "status": status,
        "verdict": status,
        "applicability": "NOT_APPLICABLE" if status == NA else "APPLIES",
        "applicability_reason": (
            "no selected functional parts or placement-cell declarations"
            if status == NA else None),
        "validation": validation,
        "checks": checks,
        "graded": coverage["graded"],
        "total": coverage["total"],
        "coverage": coverage,
        "findings": findings,
    }


# Compatibility-safe spellings for compositors that conventionally call
# library checkers ``grade`` or ``inspect``.
grade = evaluate_placement_cells
inspect = evaluate_placement_cells
check_placement_cells = evaluate_placement_cells
check_functional_cells = evaluate_placement_cells
evaluate = evaluate_placement_cells


def snapshot_from_pcbnew(board_or_path: Any,
                         observed_parts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the minimal pure snapshot from a pcbnew board, importing lazily.

    MPN identity is read from independent footprint properties when present or
    from an independently generated observed-parts/BOM receipt supplied by the
    caller.  It is never copied from the expected placement contract.
    Obstacles, fabrication approval, and stack thickness remain explicit
    inputs; this adapter does not invent them from incidental board state.
    """
    board = board_or_path
    if isinstance(board_or_path, (str, Path)):
        try:
            import pcbnew  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on KiCad runtime
            raise RuntimeError("snapshot_from_pcbnew(path) requires pcbnew") from exc
        board = pcbnew.LoadBoard(str(board_or_path))
    observed_parts = observed_parts or {}
    result: dict[str, Any] = {"parts": {}, "obstacles": []}
    for footprint in board.GetFootprints():
        ref = str(footprint.GetReference())
        observed = (observed_parts.get(ref, {})
                    if _is_mapping(observed_parts) else {})
        mpn = observed.get("mpn") if _is_mapping(observed) else observed
        try:
            properties = footprint.GetProperties()
        except AttributeError:  # pragma: no cover - KiCad API generation
            properties = {}
        if not mpn and isinstance(properties, Mapping):
            for key in ("MPN", "mpn", "Manufacturer Part Number",
                        "Manufacturer_Part_Number"):
                if properties.get(key):
                    mpn = properties[key]
                    break
        part = {"mpn": str(mpn or ""), "pads": {}}
        for pad in footprint.Pads():
            position = pad.GetPosition()
            size = pad.GetSize()
            try:
                layers = [board.GetLayerName(layer) for layer in pad.GetLayerSet().Seq()]
            except AttributeError:  # pragma: no cover - KiCad API generation
                layers = []
            part["pads"][str(pad.GetNumber())] = {
                "at": [position.x / 1e6, position.y / 1e6],
                "size_mm": [size.x / 1e6, size.y / 1e6],
                "net": str(pad.GetNetname()),
                "layers": layers,
            }
        result["parts"][ref] = part
    return result


__all__ = [
    "CHECKERS", "ContractError", "FAIL", "INCOMPLETE", "NA", "N_A", "PASS",
    "SCHEMA", "STATUSES", "check_constrained_pad_escapes",
    "check_critical_ground_egress", "check_functional_vectors",
    "check_hot_path_lower_bounds", "check_local_paths",
    "check_functional_cells", "check_pilot_replica_equivalence",
    "check_placement_cells",
    "check_reservations", "check_selected_part_pad_roles", "evaluate_placement_cells",
    "evaluate", "grade", "inspect", "snapshot_from_pcbnew",
    "validate_declaration",
]
