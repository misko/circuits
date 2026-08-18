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
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pcbnew
import yaml

import critical_route_check
import placement_gates
import route_ownership_preflight
from tier_preflight import board_scoped


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


def grade(project: Path, board_path: Path, *, board_name: str | None = None,
          placement_config: Path | None = None) -> dict[str, Any]:
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
    try:
        checks["endpoint_topology"] = _topology(route_cfg, board, project)
    except Exception as exc:
        checks["endpoint_topology"] = {"status": "INCOMPLETE", "detail": str(exc)}
    try:
        checks["layer_eligibility"] = _layers(route_cfg, board)
    except Exception as exc:
        checks["layer_eligibility"] = {"status": "INCOMPLETE", "detail": str(exc)}
    statuses = {row["status"] for row in checks.values()}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
               "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    inputs = {"board": _record(board_path), "route": _record(route_path),
              "nets": _record(nets_path)}
    if placement_config is not None and placement_config.is_file():
        inputs["placement_config"] = _record(placement_config.resolve())
    for row in checks.get("endpoint_topology", {}).get("rows", []):
        if row.get("part_yaml"):
            key = "part_" + row["part_mpn"].lower().replace("/", "_")
            inputs.setdefault(key, _record(Path(row["part_yaml"])))
    return {
        "schema": 1, "kind": "placement-routability-receipt-v1",
        "verdict": verdict, "subject": inputs["board"], "inputs": inputs,
        "checks": checks,
        "coverage": {"passing": sum(row["status"] in {"PASS", "N-A"}
                                     for row in checks.values()),
                     "total": len(checks)},
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    grade_parser = sub.add_parser("grade")
    grade_parser.add_argument("project", type=Path)
    grade_parser.add_argument("--board", type=Path, required=True)
    grade_parser.add_argument("--board-name")
    grade_parser.add_argument("--placement-config", type=Path)
    grade_parser.add_argument("--json", type=Path, required=True)
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
                        placement_config=args.placement_config)
    except Exception as exc:
        print(f"PLACEMENT-ROUTABILITY INCOMPLETE: {exc}")
        return 2
    _atomic_json(args.json, receipt)
    coverage = receipt["coverage"]
    print(f"PLACEMENT-ROUTABILITY {receipt['verdict']}: "
          f"{coverage['passing']}/{coverage['total']} checks passing or N-A; "
          f"receipt={args.json.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[receipt["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
