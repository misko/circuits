#!/usr/bin/env python3
"""Admit placement only when legality and declared route feasibility agree.

This is a read-only placement-stage compositor.  It combines the exact outline,
body and corridor-capacity checks with critical-pair inventory, route ownership,
layer eligibility, and explicit high-speed component topology declarations.
It does not generate accepted copper and therefore cannot become a hidden
routing stage.

Optional ``route.routability.topology`` rows have this schema::

  - ref: U_ESD1
    kind: shunt                   # shunt|series_flow_through|series_directional
    signal_pads: ["1", "2"]
    return_pads: ["3"]           # required for shunt
    pairs: [P1_PORT]
    why: "direct-on-trace USB clamp"

When ``route.routability.require_topology`` is true, every footprint whose
part dossier declares ``layout.route_topology.kind`` must have a matching row.
The board row remains the instance authority; the dossier is the part-class
authority.

Two optional source contracts close common placement-time omissions without
turning this gate into a router:

``connector_lanes`` maps ordered physical pads to exact nets, so a correct
connector orientation cannot hide a crossed or reversed lane assignment.
``series_power_paths`` lists explicit copper and component transitions from
input to load, so a fuse/switch/protection device cannot be present but bypassed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import pcbnew
import yaml

import critical_route_check
import board_authority
import placement_cell_checks
import placement_gates
import route_ownership_preflight
from tier_preflight import board_scoped

PCB_PIPELINE = Path(__file__).resolve().parents[2] / "pcb-design" / "scripts"
if str(PCB_PIPELINE) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(PCB_PIPELINE))
from pipeline_identity import TypedIdentityInput, subject_identity  # noqa: E402
from pipeline_stage_evidence import publish_stage_evidence  # noqa: E402


KINDS = {"shunt", "series_flow_through", "series_directional"}


def _record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _functional_cell_shadow(config_path: Path, board: Any) -> dict[str, Any]:
    """Grade the schema-1 functional-cell contract without owning admission.

    The first deployment is deliberately shadow-only: several predicates use
    authored local-clearance evidence until the pcbnew measurement adapter is
    proven on fleet canaries.  A result is still exact-config/board bound by
    the parent receipt and cannot silently disappear once configured.
    """
    contract = yaml.safe_load(
        config_path.read_text(encoding="utf-8-sig")) or {}
    if not isinstance(contract, dict):
        raise ValueError("placement_cells.yaml must contain a mapping")
    snapshot = placement_cell_checks.snapshot_from_pcbnew(board)
    measured = contract.get("snapshot") or {}
    if not isinstance(measured, dict):
        raise ValueError("placement_cells.snapshot must be a mapping")
    forbidden = sorted(set(measured) - {"obstacles", "fabrication", "stackup"})
    if forbidden:
        raise ValueError(
            "placement_cells.snapshot has unsupported keys: " +
            ", ".join(forbidden))
    snapshot.update(measured)
    report = placement_cell_checks.evaluate_placement_cells(contract, snapshot)
    return {
        "status": report["status"],
        "detail": (f"{report['coverage']['graded']}/"
                   f"{report['coverage']['total']} functional-cell facts graded"),
        "report": report,
        "authority": "SHADOW",
        "promotion_note": (
            "authored local-clearance predicates remain shadow-only until "
            "pcbnew-measured canary equivalence is demonstrated"),
    }


def _observed_source_facts(board: Any,
                           circuit_json: Path | None = None) -> dict[str, Any]:
    """Extract live authority facts independently from the exact board/source.

    Refdes and net identity come from the loaded PCB.  Exact MPN population is
    read from the generated circuit artifact when present; it is never copied
    from the stack, route-plan, or migration contracts being checked.
    """
    refs: set[str] = set()
    nets: set[str] = set()
    for footprint in board.GetFootprints():
        ref = str(footprint.GetReference() or "").strip()
        if ref:
            refs.add(ref)
        for pad in footprint.Pads():
            net = str(pad.GetNetname() or "").strip()
            if net:
                nets.add(net)

    mpns: set[str] = set()
    if circuit_json is not None and circuit_json.is_file():
        payload = json.loads(circuit_json.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list):
            raise ValueError("circuit.json must contain a list")
        for row in payload:
            if not isinstance(row, dict) or row.get("type") != "source_component":
                continue
            mpn = str(row.get("manufacturer_part_number") or "").strip()
            if mpn:
                mpns.add(mpn)
    return {
        "schema": "observed-source-facts-v1",
        "refs": sorted(refs),
        "nets": sorted(nets),
        "mpns": sorted(mpns),
        "occurrences": [],
    }


def _source_authority_shadow(stack_path: Path, route_plan_path: Path,
                             migration_path: Path | None, board: Any,
                             circuit_json: Path | None) -> dict[str, Any]:
    """Compile source-to-prep authority without changing admission yet."""
    stack = yaml.safe_load(stack_path.read_text(encoding="utf-8-sig")) or {}
    route_plan = yaml.safe_load(
        route_plan_path.read_text(encoding="utf-8-sig")) or {}
    migration = None
    if migration_path is not None:
        migration = yaml.safe_load(
            migration_path.read_text(encoding="utf-8-sig")) or {}
    observed = _observed_source_facts(board, circuit_json)
    report = board_authority.compile_source_prep_authority(
        stack=stack, observed=observed, route_plan=route_plan,
        migration=migration)
    valid, failures = board_authority.verify_authority(
        report, stack=stack, observed=observed, route_plan=route_plan,
        migration=migration)
    status = report["verdict"] if valid else "INCOMPLETE"
    return {
        "status": status,
        "detail": (f"{report['coverage']['owned_live_nets']}/"
                   f"{report['coverage']['live_nets']} live nets owned; "
                   f"{len(report['findings'])} finding(s)"),
        "report": report,
        "verification_failures": failures,
        "authority": "SHADOW",
        "promotion_note": (
            "dual-run until fleet canaries prove exact board/source extraction "
            "and no legacy gate is weakened"),
    }


def _topology(route_cfg: dict[str, Any], board: Any,
              project: Path) -> dict[str, Any]:
    route = route_cfg.get("route") or {}
    cfg = route.get("routability") or {}
    if not isinstance(cfg, dict):
        raise ValueError("route.routability must be a mapping")
    rows = cfg.get("topology") or []
    if not isinstance(rows, list):
        raise ValueError("route.routability.topology must be a list")
    if not rows and cfg.get("require_topology"):
        return {
            "status": "FAIL",
            "detail": "topology declarations are required but none exist",
            "rows": [],
            "findings": [
                "route.routability.require_topology is true but topology is empty"
            ],
        }
    if not rows:
        return {"status": "N-A", "detail": "no topology rows declared",
                "rows": [], "findings": []}
    footprints = {str(fp.GetReference()): fp for fp in board.GetFootprints()}
    dossiers = {}
    for path in sorted((project / "02_parts").glob("*/part.yaml")):
        value = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        if isinstance(value, dict) and value.get("mpn"):
            dossiers[str(value["mpn"])] = (path, value)
    pairs = {str(row.get("name")) for row in
             route.get("preflight_critical_pairs") or [] if isinstance(row, dict)}
    pair_nets = {
        str(row.get("name")): {str(row.get("p")), str(row.get("n"))}
        for row in route.get("preflight_critical_pairs") or []
        if isinstance(row, dict) and row.get("name") and row.get("p")
        and row.get("n")
    }
    seen, findings, graded = set(), [], []
    for index, raw in enumerate(rows):
        where = f"route.routability.topology[{index}]"
        if not isinstance(raw, dict):
            findings.append(f"{where}: expected a mapping")
            continue
        ref = str(raw.get("ref") or "").strip()
        part_mpn = str(raw.get("part_mpn") or "").strip()
        kind = str(raw.get("kind") or "").strip()
        why = str(raw.get("why") or "").strip()
        signal = [str(value) for value in raw.get("signal_pads") or []]
        returns = [str(value) for value in raw.get("return_pads") or []]
        common = [str(value) for value in raw.get("common_signal_pads") or []]
        selected = [str(value) for value in raw.get("selected_signal_pads") or []]
        unused = [str(value) for value in raw.get("unused_signal_pads") or []]
        inputs = [str(value) for value in raw.get("input_signal_pads") or []]
        outputs = [str(value) for value in raw.get("output_signal_pads") or []]
        row_pairs = [str(value) for value in raw.get("pairs") or []]
        if not ref or ref in seen:
            findings.append(f"{where}.ref must be non-empty and unique")
        seen.add(ref)
        fp = footprints.get(ref)
        if fp is None:
            findings.append(f"{where}: footprint {ref!r} is absent")
            continue
        dossier = dossiers.get(part_mpn)
        if dossier is None:
            findings.append(f"{where}.part_mpn {part_mpn!r} has no exact dossier")
        else:
            layout = dossier[1].get("layout") or {}
            dossier_topology = (layout.get("route_topology") or {}) \
                if isinstance(layout, dict) else {}
            declared = dossier_topology.get("kind")
            if declared != kind:
                findings.append(
                    f"{where}: instance kind {kind!r} disagrees with "
                    f"{part_mpn} dossier kind {declared!r}")
        if kind not in KINDS:
            findings.append(f"{where}.kind must be one of {sorted(KINDS)}")
        if not why:
            findings.append(f"{where}.why is required")
        if len(signal) < 2 or len(signal) != len(set(signal)):
            findings.append(f"{where}.signal_pads needs at least two unique pads")
        if kind == "shunt" and not returns:
            findings.append(f"{where}: shunt requires return_pads")
        if kind != "shunt" and returns:
            findings.append(f"{where}: series component may not declare return_pads")
        if kind == "series_directional":
            if (not common or not selected or len(common) != len(selected)
                    or set(signal) != set(common + selected)):
                findings.append(
                    f"{where}: series_directional requires equal common/selected "
                    "banks whose union is signal_pads")
            if set(unused) & set(signal):
                findings.append(f"{where}: unused_signal_pads overlaps signal_pads")
        elif common or selected or unused:
            findings.append(
                f"{where}: directional bank fields require series_directional")
        if kind == "series_flow_through":
            if (not inputs or not outputs or len(inputs) != len(outputs)
                    or set(signal) != set(inputs + outputs)):
                findings.append(
                    f"{where}: series_flow_through requires equal input/output "
                    "banks whose union is signal_pads")
        elif inputs or outputs:
            findings.append(
                f"{where}: input/output bank fields require series_flow_through")
        if not row_pairs or any(name not in pairs for name in row_pairs):
            findings.append(f"{where}.pairs must name declared critical pairs")
        pad_numbers = {str(pad.GetNumber()) for pad in fp.Pads()}
        unknown = sorted(set(signal + returns + common + selected + unused
                             + inputs + outputs) - pad_numbers)
        if unknown:
            findings.append(f"{where}: unknown pad(s) {unknown} on {ref}")
        signal_nets = [str(pad.GetNetname()) for pad in fp.Pads()
                       if str(pad.GetNumber()) in signal]
        if kind == "shunt" and len(set(signal_nets)) != len(signal_nets):
            findings.append(f"{where}: shunt signal pads do not land on distinct nets")
        expected_nets = set().union(*(pair_nets.get(name, set())
                                      for name in row_pairs))
        if expected_nets and set(signal_nets) != expected_nets:
            findings.append(
                f"{where}: signal-pad nets {sorted(set(signal_nets))} disagree "
                f"with declared pair nets {sorted(expected_nets)}")
        if dossier is not None:
            dossier_fields = {
                "shunt": ("signal_pads", "return_pads"),
                "series_directional": ("common_signal_pads",
                                       "selected_signal_pads",
                                       "unused_signal_pads"),
                "series_flow_through": ("input_signal_pads",
                                        "output_signal_pads"),
            }.get(kind, ())
            for field in dossier_fields:
                instance_value = [str(value) for value in raw.get(field) or []]
                dossier_value = [str(value) for value in
                                 dossier_topology.get(field) or []]
                if set(instance_value) != set(dossier_value):
                    findings.append(
                        f"{where}.{field} disagrees with {part_mpn} dossier: "
                        f"{sorted(instance_value)} != {sorted(dossier_value)}")
        graded.append({"ref": ref, "part_mpn": part_mpn, "kind": kind,
                       "part_yaml": str(dossier[0].resolve()) if dossier else None,
                       "signal_pads": signal,
                       "return_pads": returns,
                       "common_signal_pads": common,
                       "selected_signal_pads": selected,
                       "unused_signal_pads": unused,
                       "input_signal_pads": inputs,
                       "output_signal_pads": outputs, "pairs": row_pairs,
                       "signal_nets": signal_nets, "why": why})
    return {"status": "FAIL" if findings else "PASS",
            "detail": f"{len(graded)}/{len(rows)} topology row(s) graded",
            "rows": graded, "findings": findings}


def _layers(route_cfg: dict[str, Any], board: Any) -> dict[str, Any]:
    route = route_cfg.get("route") or {}
    cfg = route.get("routability") or {}
    roles = cfg.get("layer_roles") or {}
    eligibility = cfg.get("class_layers") or {}
    if not roles and not eligibility:
        return {"status": "N-A", "detail": "no executable layer roles declared",
                "findings": []}
    if not isinstance(roles, dict) or not isinstance(eligibility, dict):
        raise ValueError("routability layer_roles/class_layers must be mappings")
    enabled = {board.GetLayerName(layer) for layer in board.GetEnabledLayers().Seq()
               if pcbnew.IsCopperLayer(layer)}
    allowed_roles = {"signal", "reference_plane", "mixed_signal_pour",
                     "power_plane"}
    findings = []
    for layer, role in roles.items():
        if layer not in enabled:
            findings.append(f"layer_roles names disabled/unknown layer {layer}")
        if role not in allowed_roles:
            findings.append(f"layer_roles.{layer} has unknown role {role!r}")
    for class_name, layers in eligibility.items():
        if not isinstance(layers, list) or not layers:
            findings.append(f"class_layers.{class_name} must be a non-empty list")
            continue
        unknown = sorted(set(map(str, layers)) - enabled)
        if unknown:
            findings.append(f"class_layers.{class_name} names {unknown}")
        forbidden = [layer for layer in layers
                     if roles.get(str(layer)) in {"reference_plane", "power_plane"}]
        if forbidden:
            findings.append(f"class_layers.{class_name} uses plane-only {forbidden}")
    return {"status": "FAIL" if findings else "PASS",
            "detail": f"{len(roles)} layer role(s), {len(eligibility)} class map(s)",
            "roles": roles, "class_layers": eligibility,
            "findings": findings}


def _pads_by_ref(board: Any) -> dict[str, dict[str, Any]]:
    return {
        str(fp.GetReference()): {str(pad.GetNumber()): pad for pad in fp.Pads()}
        for fp in board.GetFootprints()
    }


def _connector_lanes(route_cfg: dict[str, Any], board: Any) -> dict[str, Any]:
    cfg = ((route_cfg.get("route") or {}).get("routability") or {})
    rows = cfg.get("connector_lanes") or []
    required = bool(cfg.get("require_connector_lanes"))
    if not isinstance(rows, list):
        raise ValueError("route.routability.connector_lanes must be a list")
    if not rows:
        return {
            "status": "FAIL" if required else "N-A",
            "detail": ("connector lane declarations are required but absent"
                       if required else "no connector lane rows declared"),
            "rows": [],
            "findings": (["require_connector_lanes is true but rows are empty"]
                         if required else []),
        }
    footprints = _pads_by_ref(board)
    findings, graded, seen = [], [], set()
    for index, raw in enumerate(rows):
        where = f"route.routability.connector_lanes[{index}]"
        if not isinstance(raw, dict):
            findings.append(f"{where}: expected a mapping")
            continue
        ref = str(raw.get("ref") or "").strip()
        why = str(raw.get("why") or "").strip()
        lanes = raw.get("lanes") or []
        if not ref or ref in seen:
            findings.append(f"{where}.ref must be non-empty and unique")
        seen.add(ref)
        if not why:
            findings.append(f"{where}.why is required")
        if not isinstance(lanes, list) or not lanes:
            findings.append(f"{where}.lanes must be a non-empty ordered list")
            continue
        pads = footprints.get(ref)
        if pads is None:
            findings.append(f"{where}: footprint {ref!r} is absent")
            continue
        observed, lane_seen = [], set()
        for lane_index, lane in enumerate(lanes):
            lane_where = f"{where}.lanes[{lane_index}]"
            if not isinstance(lane, dict) or set(lane) != {"pad", "net"}:
                findings.append(f"{lane_where}: requires exactly pad and net")
                continue
            pad_number, expected = str(lane["pad"]), str(lane["net"])
            if not pad_number or pad_number in lane_seen or not expected:
                findings.append(f"{lane_where}: pad must be unique and net non-empty")
                continue
            lane_seen.add(pad_number)
            pad = pads.get(pad_number)
            actual = None if pad is None else str(pad.GetNetname())
            observed.append({"pad": pad_number, "expected_net": expected,
                             "actual_net": actual})
            if pad is None:
                findings.append(f"{lane_where}: {ref}.{pad_number} is absent")
            elif actual != expected:
                findings.append(
                    f"{lane_where}: {ref}.{pad_number} is {actual!r}, "
                    f"expected {expected!r}")
        graded.append({"ref": ref, "lanes": observed, "why": why})
    return {"status": "FAIL" if findings else "PASS",
            "detail": f"{len(graded)}/{len(rows)} connector row(s) graded",
            "rows": graded, "findings": findings}


def _series_power_paths(route_cfg: dict[str, Any], board: Any) -> dict[str, Any]:
    cfg = ((route_cfg.get("route") or {}).get("routability") or {})
    rows = cfg.get("series_power_paths") or []
    required = bool(cfg.get("require_series_power_paths"))
    if not isinstance(rows, list):
        raise ValueError("route.routability.series_power_paths must be a list")
    if not rows:
        return {
            "status": "FAIL" if required else "N-A",
            "detail": ("series power paths are required but absent" if required
                       else "no series power paths declared"),
            "rows": [],
            "findings": (["require_series_power_paths is true but rows are empty"]
                         if required else []),
        }
    footprints = _pads_by_ref(board)
    findings, graded, seen_ids = [], [], set()

    def resolve(endpoint: str, where: str) -> tuple[str, str, str] | None:
        if "." not in endpoint:
            findings.append(f"{where}: endpoint must be REF.PAD")
            return None
        ref, pad_number = endpoint.split(".", 1)
        pad = footprints.get(ref, {}).get(pad_number)
        if pad is None:
            findings.append(f"{where}: endpoint {endpoint!r} is absent")
            return None
        return ref, pad_number, str(pad.GetNetname())

    for index, raw in enumerate(rows):
        where = f"route.routability.series_power_paths[{index}]"
        if not isinstance(raw, dict):
            findings.append(f"{where}: expected a mapping")
            continue
        path_id = str(raw.get("id") or "").strip()
        why = str(raw.get("why") or "").strip()
        transitions = raw.get("transitions") or []
        if not path_id or path_id in seen_ids:
            findings.append(f"{where}.id must be non-empty and unique")
        seen_ids.add(path_id)
        if not why:
            findings.append(f"{where}.why is required")
        if not isinstance(transitions, list) or not transitions:
            findings.append(f"{where}.transitions must be a non-empty list")
            continue
        observed = []
        for transition_index, transition in enumerate(transitions):
            tw = f"{where}.transitions[{transition_index}]"
            if (not isinstance(transition, dict) or
                    set(transition) != {"kind", "from", "to"}):
                findings.append(f"{tw}: requires exactly kind, from, and to")
                continue
            kind = str(transition["kind"])
            left = resolve(str(transition["from"]), f"{tw}.from")
            right = resolve(str(transition["to"]), f"{tw}.to")
            if kind not in {"copper", "component"}:
                findings.append(f"{tw}.kind must be copper or component")
            if left is None or right is None:
                continue
            if kind == "copper" and (not left[2] or left[2] != right[2]):
                findings.append(
                    f"{tw}: copper endpoints have different nets "
                    f"{left[2]!r}/{right[2]!r}")
            if kind == "component" and (left[0] != right[0] or
                                         left[1] == right[1] or
                                         left[2] == right[2]):
                findings.append(
                    f"{tw}: component transition must cross two pads/nets "
                    "of one footprint")
            observed.append({"kind": kind, "from": transition["from"],
                             "to": transition["to"],
                             "from_net": left[2], "to_net": right[2]})
        graded.append({"id": path_id, "transitions": observed, "why": why})
    return {"status": "FAIL" if findings else "PASS",
            "detail": f"{len(graded)}/{len(rows)} power path(s) graded",
            "rows": graded, "findings": findings}


def grade(project: Path, board_path: Path, *, board_name: str | None = None,
          placement_config: Path | None = None,
          functional_cells_config: Path | None = None,
          stack_authority: Path | None = None,
          route_plan_authority: Path | None = None,
          topology_migration: Path | None = None) -> dict[str, Any]:
    project, board_path = project.resolve(), board_path.resolve()
    route_path, route_note = board_scoped(project, "route.yaml", board_name)
    nets_path, nets_note = board_scoped(project, "rules/nets.yaml", board_name)
    if route_path is None or not route_path.is_file():
        raise ValueError(f"route contract unresolved: {route_note}")
    if nets_path is None or not nets_path.is_file():
        raise ValueError(f"net rules unresolved: {nets_note}")
    route_cfg = yaml.safe_load(route_path.read_text(encoding="utf-8-sig")) or {}
    placement_cfg = {}
    if placement_config is not None and placement_config.is_file():
        placement_cfg = json.loads(
            placement_config.read_text(encoding="utf-8-sig"))
    checks: dict[str, dict[str, Any]] = {}
    try:
        physical = placement_gates.inspect(board_path, placement_cfg)
        checks["physical_placement"] = {
            "status": physical["verdict"],
            "detail": f"{len(physical['failures'])} failure(s), "
                      f"{len(physical['warnings'])} warning(s)",
            "report": physical,
        }
    except Exception as exc:
        checks["physical_placement"] = {"status": "INCOMPLETE",
                                         "detail": str(exc)}
    try:
        notes = critical_route_check.check(
            project, board_path, False, route_path=route_path,
            nets_path=nets_path)
        count = sum(not note.startswith("no critical routes:") for note in notes)
        checks["critical_route_contract"] = {
            "status": "PASS", "detail": f"{count} critical pair(s) contracted",
            "notes": notes}
    except Exception as exc:
        checks["critical_route_contract"] = {"status": "FAIL", "detail": str(exc)}
    try:
        board_nets, pad_counts = route_ownership_preflight._load_board_facts(
            board_path)
        nets_cfg = yaml.safe_load(nets_path.read_text(encoding="utf-8-sig")) or {}
        ownership = route_ownership_preflight.audit_config(
            route_cfg, pad_counts=pad_counts, board_nets=board_nets,
            nets_cfg=nets_cfg)
        checks["route_ownership"] = {
            "status": ownership["verdict"],
            "detail": f"{len(ownership['findings'])} finding(s)",
            "report": ownership}
    except Exception as exc:
        checks["route_ownership"] = {"status": "INCOMPLETE", "detail": str(exc)}
    board = pcbnew.LoadBoard(str(board_path))
    shadow_checks: dict[str, dict[str, Any]] = {}
    try:
        checks["endpoint_topology"] = _topology(route_cfg, board, project)
    except Exception as exc:
        checks["endpoint_topology"] = {"status": "INCOMPLETE", "detail": str(exc)}
    try:
        checks["layer_eligibility"] = _layers(route_cfg, board)
    except Exception as exc:
        checks["layer_eligibility"] = {"status": "INCOMPLETE", "detail": str(exc)}
    try:
        checks["connector_lane_order"] = _connector_lanes(route_cfg, board)
    except Exception as exc:
        checks["connector_lane_order"] = {"status": "INCOMPLETE", "detail": str(exc)}
    try:
        checks["series_power_paths"] = _series_power_paths(route_cfg, board)
    except Exception as exc:
        checks["series_power_paths"] = {"status": "INCOMPLETE", "detail": str(exc)}
    cells_path: Path | None
    if functional_cells_config is not None:
        cells_path = functional_cells_config.resolve()
        if not cells_path.is_file():
            shadow_checks["functional_cells"] = {
                "status": "INCOMPLETE",
                "detail": f"functional-cell contract does not exist: {cells_path}",
                "authority": "SHADOW"}
            cells_path = None
    else:
        cells_path, _ = board_scoped(
            project, "rules/placement_cells.yaml", board_name)
    if cells_path is not None and cells_path.is_file():
        try:
            shadow_checks["functional_cells"] = _functional_cell_shadow(
                cells_path.resolve(), board)
        except Exception as exc:
            shadow_checks["functional_cells"] = {
                "status": "INCOMPLETE", "detail": str(exc),
                "authority": "SHADOW"}

    authority_errors: list[str] = []

    def authority_path(explicit: Path | None, relative: str) -> Path | None:
        if explicit is not None:
            resolved = explicit.resolve()
            if not resolved.is_file():
                authority_errors.append(
                    f"source-authority input does not exist: {resolved}")
                return None
            return resolved
        candidate, _ = board_scoped(project, relative, board_name)
        return candidate.resolve() if candidate is not None and candidate.is_file() \
            else None

    stack_path = authority_path(stack_authority, "rules/stackup.yaml")
    plan_path = authority_path(route_plan_authority, "rules/route_plan.yaml")
    migration_path = authority_path(
        topology_migration, "rules/topology_migration.yaml")
    authority_configured = bool(authority_errors) or any(
        (stack_path, plan_path, migration_path))
    circuit_path = project / "03_tscircuit/build/circuit.json"
    if authority_configured:
        if authority_errors:
            shadow_checks["source_prep_authority"] = {
                "status": "INCOMPLETE", "detail": "; ".join(authority_errors),
                "authority": "SHADOW"}
        elif stack_path is None or plan_path is None:
            missing = [name for name, value in (
                ("stackup.yaml", stack_path), ("route_plan.yaml", plan_path))
                       if value is None]
            shadow_checks["source_prep_authority"] = {
                "status": "INCOMPLETE",
                "detail": "configured source authority is missing " +
                          ", ".join(missing),
                "authority": "SHADOW",
            }
        else:
            try:
                shadow_checks["source_prep_authority"] = (
                    _source_authority_shadow(
                        stack_path, plan_path, migration_path, board,
                        circuit_path if circuit_path.is_file() else None))
            except Exception as exc:
                shadow_checks["source_prep_authority"] = {
                    "status": "INCOMPLETE", "detail": str(exc),
                    "authority": "SHADOW"}
    statuses = {row["status"] for row in checks.values()}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
               "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    inputs = {"board": _record(board_path), "route": _record(route_path),
              "nets": _record(nets_path)}
    if placement_config is not None and placement_config.is_file():
        inputs["placement_config"] = _record(placement_config.resolve())
    if cells_path is not None and cells_path.is_file():
        inputs["placement_cells"] = _record(cells_path.resolve())
    for name, path in (("stack_authority", stack_path),
                       ("route_plan_authority", plan_path),
                       ("topology_migration", migration_path)):
        if path is not None:
            inputs[name] = _record(path)
    if authority_configured and circuit_path.is_file():
        inputs["circuit"] = _record(circuit_path.resolve())
    for row in checks.get("endpoint_topology", {}).get("rows", []):
        if row.get("part_yaml"):
            key = "part_" + row["part_mpn"].lower().replace("/", "_")
            inputs.setdefault(key, _record(Path(row["part_yaml"])))
    return {
        "schema": 1, "kind": "placement-routability-receipt-v1",
        "verdict": verdict, "subject": inputs["board"], "inputs": inputs,
        "checks": checks,
        "shadow_checks": shadow_checks,
        "coverage": {"passing": sum(row["status"] in {"PASS", "N-A"}
                                     for row in checks.values()),
                     "total": len(checks)},
        "shadow_coverage": {
            "passing": sum(row["status"] in {"PASS", "N-A"}
                           for row in shadow_checks.values()),
            "total": len(shadow_checks),
        },
    }


def verify(receipt_path: Path) -> tuple[bool, list[str]]:
    failures = []
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"]
    if (receipt.get("schema") != 1 or
            receipt.get("kind") != "placement-routability-receipt-v1"):
        failures.append("unsupported receipt schema/kind")
    for name, record in sorted((receipt.get("inputs") or {}).items()):
        path = Path(str(record.get("path") or ""))
        if not path.is_file() or _record(path) != record:
            failures.append(f"input moved or changed: {name}")
    if receipt.get("verdict") == "ACCEPTED":
        bad = [name for name, row in (receipt.get("checks") or {}).items()
               if row.get("status") not in {"PASS", "N-A"}]
        if bad:
            failures.append(f"accepted receipt contains bad checks: {bad}")
    return not failures, failures


def _publish_feasibility(receipt: dict[str, Any], receipt_path: Path,
                         bundle_path: Path, stage_path: Path) -> None:
    if receipt.get("verdict") != "ACCEPTED":
        raise ValueError("P-FEASIBILITY cannot publish non-accepted evidence")
    semantic = {
        "checks": {
            name: {"status": row.get("status"), "detail": row.get("detail")}
            for name, row in sorted(receipt["checks"].items())
        },
        "topology": (receipt["checks"].get("endpoint_topology") or {})
                    .get("rows", []),
        "layers": receipt["checks"].get("layer_eligibility", {}),
    }
    shadow_inputs = {
        "placement_cells", "stack_authority", "route_plan_authority",
        "topology_migration", "circuit",
    }
    authoritative_inputs = {
        name: record for name, record in receipt["inputs"].items()
        if name not in shadow_inputs
    }
    authoritative_receipt = {
        "schema": receipt["schema"], "kind": receipt["kind"],
        "verdict": receipt["verdict"], "subject": receipt["subject"],
        "inputs": authoritative_inputs, "checks": receipt["checks"],
        "coverage": receipt["coverage"],
    }
    authoritative_bytes = (json.dumps(
        authoritative_receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
    identity = subject_identity("placement-feasibility", 1, [TypedIdentityInput(
        "placement", "mapping", semantic, authoritative_bytes)])
    inputs = {name: Path(record["path"])
              for name, record in authoritative_inputs.items()}
    coverage = receipt["coverage"]
    # Publish only the authoritative projection. Shadow diagnostics remain in
    # the caller's receipt but cannot churn the accepted P-FEASIBILITY subject
    # or invalidate downstream evidence.
    with tempfile.TemporaryDirectory(prefix="p-feas-authority-") as temporary:
        measurement = Path(temporary) / "placement_feasibility.json"
        measurement.write_bytes(authoritative_bytes)
        publish_stage_evidence(
            stage_id="P-FEASIBILITY",
            output_symbol="placement_feasibility_report",
            producer="placement_routability_preflight.py",
            producer_version="schema-1-shadow",
            subject=identity,
            inputs=inputs,
            measurement_path=measurement,
            measurement_name="placement_feasibility.json",
            accepted_dir=bundle_path,
            stage_result_path=stage_path,
            status="PASS",
            graded=coverage["passing"],
            total=coverage["total"],
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    grade_parser = sub.add_parser("grade")
    grade_parser.add_argument("project", type=Path)
    grade_parser.add_argument("--board", type=Path, required=True)
    grade_parser.add_argument("--board-name")
    grade_parser.add_argument("--placement-config", type=Path)
    grade_parser.add_argument("--functional-cells", type=Path)
    grade_parser.add_argument("--stack-authority", type=Path)
    grade_parser.add_argument("--route-plan-authority", type=Path)
    grade_parser.add_argument("--topology-migration", type=Path)
    grade_parser.add_argument("--json", type=Path, required=True)
    grade_parser.add_argument("--stage-bundle", type=Path)
    grade_parser.add_argument("--stage-result", type=Path)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        valid, failures = verify(args.receipt)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"PLACEMENT-ROUTABILITY RECEIPT {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1
    try:
        receipt = grade(args.project, args.board, board_name=args.board_name,
                        placement_config=args.placement_config,
                        functional_cells_config=args.functional_cells,
                        stack_authority=args.stack_authority,
                        route_plan_authority=args.route_plan_authority,
                        topology_migration=args.topology_migration)
    except Exception as exc:
        print(f"PLACEMENT-ROUTABILITY INCOMPLETE: {exc}")
        return 2
    _atomic_json(args.json, receipt)
    if bool(args.stage_bundle) != bool(args.stage_result):
        print("PLACEMENT-ROUTABILITY INCOMPLETE: --stage-bundle and "
              "--stage-result must be supplied together")
        return 2
    if args.stage_bundle:
        try:
            _publish_feasibility(receipt, args.json.resolve(),
                                 args.stage_bundle.resolve(),
                                 args.stage_result.resolve())
        except Exception as exc:
            print(f"PLACEMENT-ROUTABILITY INCOMPLETE: shadow stage evidence: {exc}")
            return 2
    coverage = receipt["coverage"]
    print(f"PLACEMENT-ROUTABILITY {receipt['verdict']}: "
          f"{coverage['passing']}/{coverage['total']} checks passing or N-A; "
          f"receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[receipt["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
