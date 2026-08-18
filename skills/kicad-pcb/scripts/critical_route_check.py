#!/usr/bin/env python3
"""R-PAIRMAP / R-CRITESC: critical-net route contract and artifact gate.

Before routing, validate that every declared differential pair exists, is
assigned to a differential wave, has P/N polarity, matching membership, and a
legal layer policy.  After the critical-first route candidate exists,
--require-connected proves the actual copper joins every pad while respecting
the declared no-via/layer constraints.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pcbnew
import yaml


class RouteContractError(ValueError):
    pass


def die(msg):
    raise RouteContractError(msg)


def load(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        die(f"route config {path} must be a mapping")
    return data


def pair_in_groups(raw, p, n):
    if not isinstance(raw, list):
        return False
    groups = raw if raw and isinstance(raw[0], list) else [raw]
    return any(g == [p, n] or g == [n, p] for g in groups)


def length_contract_pairs(project, nets_path=None):
    """Derive the critical-pair denominator from the independent rules file.

    A self-declared preflight list cannot prove its own completeness. Every
    one-P/one-N length_match group is an independently authored assertion that
    a physical pair exists and therefore must have an R-PAIRMAP row.
    End-to-end groups with multiple segments contribute each suffix-matched
    segment once.
    """
    path = Path(nets_path) if nets_path is not None else \
        project / "03_src/rules/nets.yaml"
    if not path.is_file():
        return set()
    doc = load(path)
    groups = doc.get("length_match") or {}
    if not isinstance(groups, dict):
        die("rules/nets.yaml length_match must be a mapping")
    found = set()
    for name, group in groups.items():
        if not isinstance(group, dict):
            continue
        members = group.get("members") or {}
        ps = members.get("P") or [] if isinstance(members, dict) else []
        ns = members.get("N") or [] if isinstance(members, dict) else []
        if not isinstance(ps, list) or not isinstance(ns, list):
            continue
        nset = {str(x) for x in ns}
        for p in map(str, ps):
            if p.endswith("_P") and p[:-2] + "_N" in nset:
                found.add((p, p[:-2] + "_N"))
            elif p.endswith("+") and p[:-1] + "-" in nset:
                found.add((p, p[:-1] + "-"))
    return found


def connected(board, netname):
    pads = [p for f in board.GetFootprints() for p in f.Pads()
            if p.GetNetname() == netname]
    if len(pads) < 2:
        return False, f"{len(pads)} pad(s)"
    conn = board.GetConnectivity()
    conn.Build(board)
    got = list(conn.GetConnectedItems(pads[0]))
    missing = [f"{p.GetParentFootprint().GetReference()}.{p.GetNumber()}"
               for p in pads[1:] if p not in got]
    return not missing, ("all pads connected" if not missing
                         else f"unconnected pads {missing}")


def check(project, board_path, require_connected=False, *, route_path=None,
          nets_path=None):
    route_path = (Path(route_path) if route_path is not None else
                  project / "03_src" / "route.yaml")
    if not route_path.exists():
        die(f"missing {route_path}")
    cfg = load(route_path)
    route = cfg.get("route") or {}
    pairs = route.get("preflight_critical_pairs")
    if not isinstance(pairs, list):
        die("route.preflight_critical_pairs must be a list")
    if not pairs:
        reason = str(route.get("no_critical_routes") or "").strip()
        if not reason:
            die("route.preflight_critical_pairs is empty; declare a specific "
                "route.no_critical_routes reason")
        return [f"no critical routes: {reason}"]
    waves = route.get("waves") or []
    wave_by_name = {str(w.get("name")): w for w in waves if isinstance(w, dict)}
    groups = ((cfg.get("prep") or {}).get("waves") or {}).get("groups") or {}
    board = pcbnew.LoadBoard(str(board_path))
    board_nets = {str(n) for n in board.GetNetsByName().keys()}
    notes = []
    realized_findings = []
    declared_pairs = set()
    for i, item in enumerate(pairs):
        where = f"route.preflight_critical_pairs[{i}]"
        if not isinstance(item, dict):
            die(f"{where} must be a mapping")
        name = str(item.get("name") or "").strip() or die(f"{where}.name is required")
        p = str(item.get("p") or "").strip() or die(f"{where}.p is required")
        n = str(item.get("n") or "").strip() or die(f"{where}.n is required")
        declared_pairs.add((p, n))
        source = str(item.get("source") or "wave").strip()
        wave_name = str(item.get("wave") or "").strip()
        if not (p.endswith(("_P", "+")) and n.endswith(("_N", "-"))):
            die(f"R-PAIRMAP {name}: polarity must be p=*P/+ and n=*N/-, got {p}/{n}")
        absent = [x for x in (p, n) if x not in board_nets]
        if absent:
            die(f"R-PAIRMAP {name}: board is missing nets {absent}")
        if source == "wave":
            if not wave_name:
                die(f"{where}.wave is required for source: wave")
            wave = wave_by_name.get(wave_name)
            if wave is None:
                die(f"R-PAIRMAP {name}: unknown wave {wave_name!r}")
            if wave.get("engine") != "diff":
                die(f"R-PAIRMAP {name}: wave {wave_name!r} is not engine: diff")
            group_name = wave.get("group", wave_name)
            members = groups.get(group_name) or []
            if p not in members or n not in members:
                die(f"R-PAIRMAP {name}: {p}/{n} are not both in prep group {group_name!r}")
            if not pair_in_groups(wave.get("length_match_group"), p, n):
                die(f"R-PAIRMAP {name}: {p}/{n} absent from {wave_name}.length_match_group")
            wave_layers = wave.get("layers") or (route.get("common") or {}).get("layers") or []
        elif source == "seed_stubs":
            group_name = str(item.get("group") or "").strip()
            if not group_name:
                die(f"{where}.group is required for source: seed_stubs")
            members = groups.get(group_name) or []
            if p not in members or n not in members:
                die(f"R-PAIRMAP {name}: {p}/{n} are not both in prep group {group_name!r}")
            stubs = ((cfg.get("prep") or {}).get("seed_stubs") or {}).get("stubs") or []
            stub_nets = {str(s.get("net")) for s in stubs if isinstance(s, dict)}
            if p not in stub_nets or n not in stub_nets:
                die(f"R-PAIRMAP {name}: {p}/{n} do not both have deterministic seed stubs")
            wave_name = f"seed_stubs:{group_name}"
            wave_layers = sorted({
                str(seg.get("layer"))
                for s in stubs if isinstance(s, dict) and str(s.get("net")) in (p, n)
                for seg in (s.get("segments") or []) if isinstance(seg, dict)
            })
        else:
            die(f"{where}.source must be wave or seed_stubs")
        allowed = item.get("allowed_layers")
        if not isinstance(allowed, list) or not allowed:
            die(f"R-PAIRMAP {name}: allowed_layers must be non-empty")
        bad_layers = sorted(set(wave_layers) - set(allowed))
        if bad_layers:
            die(f"R-PAIRMAP {name}: wave permits forbidden layers {bad_layers}")
        no_vias = item.get("no_vias")
        if no_vias not in (True, False):
            die(f"R-PAIRMAP {name}: no_vias must be true/false")
        if no_vias and len(set(wave_layers)) != 1:
            die(f"R-PAIRMAP {name}: no_vias requires a single-layer wave")

        if require_connected:
            allowed_ids = {board.GetLayerID(x) for x in allowed}
            for net in (p, n):
                ok, detail = connected(board, net)
                if not ok:
                    realized_findings.append(f"R-CRITESC {name}/{net}: {detail}")
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                if not tracks:
                    realized_findings.append(
                        f"R-CRITESC {name}/{net}: no routed copper")
                    continue
                vias = [t for t in tracks if isinstance(t, pcbnew.PCB_VIA)]
                if no_vias and vias:
                    realized_findings.append(
                        f"R-CRITESC {name}/{net}: {len(vias)} via(s), expected zero")
                layers = {t.GetLayer() for t in tracks
                          if not isinstance(t, pcbnew.PCB_VIA)}
                if layers - allowed_ids:
                    bad = [board.GetLayerName(x) for x in sorted(layers - allowed_ids)]
                    realized_findings.append(
                        f"R-CRITESC {name}/{net}: copper on forbidden layers {bad}")
        notes.append(f"{name} {p}/{n} -> {wave_name} on {wave_layers}, no_vias={no_vias}")
    missing = sorted(length_contract_pairs(project, nets_path) - declared_pairs)
    if missing:
        die("R-PAIRMAP critical-pair inventory omits length_match pair(s): "
            + ", ".join(f"{p}/{n}" for p, n in missing))
    if realized_findings:
        die("\n  ".join(realized_findings))
    return notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path)
    ap.add_argument("--board", type=Path, required=True)
    ap.add_argument("--require-connected", action="store_true")
    args = ap.parse_args(argv)
    try:
        notes = check(args.project.resolve(), args.board.resolve(),
                      args.require_connected)
    except (RouteContractError, OSError, yaml.YAMLError) as exc:
        print(f"R-PAIRMAP/R-CRITESC FAIL: {exc}")
        return 1
    for note in notes:
        print("  PASS", note)
    # An explicit no-critical-routes disposition is evidence and therefore a
    # printable note, but it is not a phantom differential-pair denominator.
    pair_count = sum(not note.startswith("no critical routes:")
                     for note in notes)
    print(f"R-PAIRMAP/R-CRITESC PASS: {pair_count} critical pair(s) "
          f"{'connected' if args.require_connected else 'contracted'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
