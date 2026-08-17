#!/usr/bin/env python3
"""Refuse routing whose physical owner or corridor order is contradictory.

This preflight is intentionally progressive.  Ordinary point-to-point boards
need no ownership block.  A many-pad net declared as a pour/wide-track intent,
or a board that declares shared corridors, must make the physical owner
explicit before an autorouter is allowed to search.

    /usr/bin/python3 route_ownership_preflight.py 03_src/route.yaml
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any

import yaml


TOPOLOGIES = {"pour", "wide_trunk", "star", "point_to_point", "local"}
OWNERS = {"zone", "prep.seed_stubs", "stitch.seed_stubs",
          "taps.connections", "route.wave"}


def _list(value: Any, where: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item
                                               for item in value):
        raise ValueError(f"{where} must be a list of non-empty strings")
    return value


def _wave_members(cfg: dict[str, Any], board_nets: set[str]) -> tuple[list[dict[str, Any]], dict[str, str]]:
    route = cfg.get("route") or {}
    waves = route.get("waves") or []
    if not isinstance(waves, list):
        raise ValueError("route.waves must be a list")
    prep_waves = ((cfg.get("prep") or {}).get("waves") or {})
    groups = prep_waves.get("groups") or {}
    excluded = prep_waves.get("exclude") or ["GND", "unconnected-*"]
    if not isinstance(groups, dict):
        raise ValueError("prep.waves.groups must be a mapping")
    claimed: set[str] = set()
    rows: list[dict[str, Any]] = []
    owner: dict[str, str] = {}
    for index, raw in enumerate(waves):
        if not isinstance(raw, dict):
            raise ValueError(f"route.waves[{index}] must be a mapping")
        row = dict(raw)
        name = str(row.get("name") or f"w{index + 1}")
        members = row.get("nets")
        if members is None:
            group_name = str(row.get("group") or name)
            members = groups.get(group_name)
        if members == "rest":
            members = sorted(net for net in board_nets - claimed
                             if not any(fnmatch.fnmatch(net, pattern)
                                        for pattern in excluded))
        elif members is None:
            members = []
        members = _list(members, f"wave {name} members")
        row["_name"] = name
        row["_members"] = members
        rows.append(row)
        for net in members:
            claimed.add(net)
            owner.setdefault(net, name)
    return rows, owner


def _class_intents(nets_cfg: dict[str, Any]) -> dict[str, str]:
    intents: dict[str, str] = {}
    classes = nets_cfg.get("classes") or {}
    if not isinstance(classes, dict):
        raise ValueError("rules/nets.yaml classes must be a mapping")
    for class_name, raw in classes.items():
        if not isinstance(raw, dict):
            continue
        routing = str(raw.get("routing") or "").lower()
        for pattern in raw.get("nets") or []:
            intents[str(pattern)] = routing or str(class_name).lower()
    return intents


def _intent_for(net: str, intents: dict[str, str]) -> str:
    matches = [value for pattern, value in intents.items()
               if fnmatch.fnmatch(net, pattern)]
    return " ".join(matches)


def audit_config(cfg: dict[str, Any], *, pad_counts: dict[str, int],
                 board_nets: set[str], nets_cfg: dict[str, Any]) -> dict[str, Any]:
    route = cfg.get("route") or {}
    ownership = route.get("ownership") or {}
    if not isinstance(ownership, dict):
        raise ValueError("route.ownership must be a mapping")
    allowed_keys = {"multipad_threshold", "nets", "corridors"}
    unknown = set(ownership) - allowed_keys
    if unknown:
        raise ValueError(f"route.ownership has unknown key(s): {sorted(unknown)}")
    threshold = int(ownership.get("multipad_threshold", 8))
    if threshold < 3:
        raise ValueError("route.ownership.multipad_threshold must be >= 3")
    net_specs = ownership.get("nets") or {}
    corridors = ownership.get("corridors") or {}
    if not isinstance(net_specs, dict) or not isinstance(corridors, dict):
        raise ValueError("route.ownership nets/corridors must be mappings")

    waves, net_wave = _wave_members(cfg, board_nets)
    wave_index = {row["_name"]: index for index, row in enumerate(waves)}
    findings: list[dict[str, str]] = []
    notes: list[str] = []
    intents = _class_intents(nets_cfg)

    for net, count in sorted(pad_counts.items()):
        intent = _intent_for(net, intents)
        complex_power = count >= threshold and ("pour" in intent or "wide" in intent)
        if not complex_power:
            continue
        spec = net_specs.get(net)
        if not isinstance(spec, dict):
            findings.append({
                "code": "O-PWR",
                "subject": net,
                "message": (f"{net} has {count} pads and routing intent {intent!r}; "
                            "declare route.ownership.nets topology + owner before KRT"),
            })
            continue
        topology = str(spec.get("topology") or "")
        owner = str(spec.get("owner") or "")
        why = str(spec.get("why") or "").strip()
        if topology not in TOPOLOGIES or owner not in OWNERS or not why:
            findings.append({
                "code": "O-SCHEMA", "subject": net,
                "message": (f"ownership needs topology in {sorted(TOPOLOGIES)}, "
                            f"owner in {sorted(OWNERS)}, and non-empty why"),
            })
            continue
        wave = net_wave.get(net)
        if owner != "route.wave" and wave:
            findings.append({
                "code": "O-DOUBLE", "subject": net,
                "message": (f"owner is {owner} but wave {wave} also asks the "
                            "generic router to own the complete net"),
            })
        if owner == "route.wave" and not bool(spec.get("allow_generic_router")):
            findings.append({
                "code": "O-MST", "subject": net,
                "message": ("many-pad pour/wide intent cannot be inferred by a "
                            "generic MST; choose zone/trunk/taps or explicitly set "
                            "allow_generic_router with reviewed evidence"),
            })
        notes.append(f"{net}: {topology} owned by {owner}")

    constrained: set[str] = set()
    critical = route.get("preflight_critical_pairs") or []
    for pair in critical:
        if not isinstance(pair, dict):
            continue
        wave = pair.get("wave")
        if wave and (pair.get("no_vias") is True or
                     len(pair.get("allowed_layers") or []) == 1):
            constrained.add(str(wave))
    for row in waves:
        layers = row.get("layers") or ((route.get("common") or {}).get("layers")) or []
        if isinstance(layers, list) and len(layers) == 1:
            constrained.add(row["_name"])

    for corridor, raw in sorted(corridors.items()):
        if not isinstance(raw, dict):
            findings.append({"code": "O-CORRIDOR", "subject": str(corridor),
                             "message": "corridor declaration must be a mapping"})
            continue
        unknown_corridor = set(raw) - {"claim_order", "why", "allow_flexible_first"}
        if unknown_corridor:
            findings.append({"code": "O-CORRIDOR", "subject": str(corridor),
                             "message": f"unknown key(s): {sorted(unknown_corridor)}"})
            continue
        try:
            order = _list(raw.get("claim_order"),
                          f"route.ownership.corridors.{corridor}.claim_order")
        except ValueError as exc:
            findings.append({"code": "O-CORRIDOR", "subject": str(corridor),
                             "message": str(exc)})
            continue
        if not str(raw.get("why") or "").strip():
            findings.append({"code": "O-CORRIDOR", "subject": str(corridor),
                             "message": "corridor requires non-empty why"})
        missing = [name for name in order if name not in wave_index]
        if missing:
            findings.append({"code": "O-CORRIDOR", "subject": str(corridor),
                             "message": f"unknown wave(s): {missing}"})
            continue
        actual = sorted(order, key=wave_index.get)
        if actual != order:
            findings.append({
                "code": "O-ORDER", "subject": str(corridor),
                "message": f"declared claim_order {order} but route.waves is {actual}",
            })
        first_constrained = next((i for i, name in enumerate(order)
                                  if name in constrained), None)
        if first_constrained is not None and first_constrained > 0 and not raw.get(
                "allow_flexible_first", False):
            findings.append({
                "code": "O-FLEX", "subject": str(corridor),
                "message": (f"constrained wave {order[first_constrained]} follows "
                            f"flexible claimant(s) {order[:first_constrained]}"),
            })

    applicable = bool(findings or notes or corridors or constrained)
    return {
        "schema": 1,
        "verdict": "FAIL" if findings else ("PASS" if applicable else "N-A"),
        "findings": findings,
        "notes": notes,
        "coverage": {
            "board_nets": len(board_nets), "declared_net_owners": len(net_specs),
            "declared_corridors": len(corridors),
            "constrained_waves": sorted(constrained),
        },
    }


def _load_board_facts(board_path: Path) -> tuple[set[str], dict[str, int]]:
    import pcbnew  # only the KiCad-interpreter command path needs pcbnew
    board = pcbnew.LoadBoard(str(board_path))
    nets: set[str] = set()
    counts: dict[str, int] = {}
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            net = str(pad.GetNetname())
            if not net:
                continue
            nets.add(net)
            counts[net] = counts.get(net, 0) + 1
    return nets, counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("route_config", type=Path)
    parser.add_argument("--board", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)
    try:
        route_path = args.route_config.resolve()
        cfg = yaml.safe_load(route_path.read_text(encoding="utf-8-sig")) or {}
        stage = next((path for path in route_path.parents if path.name == "03_src"), None)
        if stage is None:
            raise ValueError("route config must live below 03_src")
        project = stage.parent
        board_value = args.board or Path((cfg.get("project") or {}).get("board", ""))
        board_path = (board_value if board_value.is_absolute()
                      else project / board_value).resolve()
        if not board_path.is_file():
            raise ValueError(f"board not found: {board_path}")
        # ADR-0007 boards keep route.yaml and rules below 03_src/<board>/;
        # single-board projects keep both directly below 03_src/. Prefer the
        # route-local authority and fall back only for the flat form.
        local_nets = route_path.parent / "rules" / "nets.yaml"
        nets_path = local_nets if local_nets.is_file() else stage / "rules" / "nets.yaml"
        nets_cfg = (yaml.safe_load(nets_path.read_text(encoding="utf-8-sig")) or {}
                    if nets_path.is_file() else {})
        board_nets, pad_counts = _load_board_facts(board_path)
        result = audit_config(cfg, pad_counts=pad_counts, board_nets=board_nets,
                              nets_cfg=nets_cfg)
        result["inputs"] = {"route": str(route_path), "board": str(board_path),
                            "nets": str(nets_path)}
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    except Exception as exc:
        print(f"ROUTE-OWNERSHIP INCOMPLETE: {exc}")
        return 2

    for finding in result["findings"]:
        print(f"  {finding['code']} {finding['subject']}: {finding['message']}")
    print(f"ROUTE-OWNERSHIP {result['verdict']}: "
          f"{len(result['findings'])} finding(s), "
          f"{len(result['notes'])} explicit net owner(s)")
    coverage = result["coverage"]
    print(f"coverage: {coverage['board_nets']} board net(s), "
          f"{coverage['declared_net_owners']} owner(s), "
          f"{coverage['declared_corridors']} corridor(s)")
    return 1 if result["verdict"] == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
