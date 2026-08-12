#!/usr/bin/env python3
"""P-ROUTEBASE: prove a promoted KRT chain derives from this exact base.

    /usr/bin/python3 promoted_route_check.py BOARD.kicad_pcb ROUTE.yaml

The imported route contributes tracks and router vias; placement and zones
come from the regenerated base, while deterministic ``prep`` copper must be
present in the promoted chain.  A promoted chain that inherited an older
placement, source-via process, or seed-stub recipe cannot be replayed safely.
This cheap pre-review check compares the regenerated base, freshly prepared
``r0``, and promoted chain before any human review or route/import spend.

An absent promoted artifact is N-A for a first route.  Once ``route.final``
exists and ``route.import_source`` selects ``promoted``, any disagreement is a
hard failure; the importer retains its independent geometry refusal.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pcbnew
import yaml


POS_TOL_NM = 1000
DIM_TOL_NM = 1000
ROT_TOL_DEG = 0.001


def _root(route_path: Path):
    return route_path.resolve().parent.parent


def _resolve(root: Path, value):
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _pos(item):
    p = item.GetPosition()
    return p.x, p.y


def _xy(point):
    return point.x, point.y


def _near(a, b):
    return abs(a[0] - b[0]) <= POS_TOL_NM and abs(a[1] - b[1]) <= POS_TOL_NM


def _fmt_pos(pos):
    return f"({pcbnew.ToMM(pos[0]):.6f},{pcbnew.ToMM(pos[1]):.6f})"


def _via_rows(board):
    rows = []
    for item in board.GetTracks():
        if item.GetClass() != "PCB_VIA":
            continue
        rows.append({
            "pos": _pos(item), "net": item.GetNetname(),
            "diameter": item.GetWidth(pcbnew.F_Cu), "drill": item.GetDrill(),
            "cap": int(item.GetCappingMode()),
            "fill": int(item.GetFillingMode()),
        })
    return rows


def _track_rows(board):
    rows = []
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA":
            continue
        a, b = _xy(item.GetStart()), _xy(item.GetEnd())
        if b < a:
            a, b = b, a
        rows.append({
            "a": a, "b": b, "net": item.GetNetname(),
            "layer": item.GetLayer(), "width": item.GetWidth(),
        })
    return rows


def _pad_rows(fp):
    rows = []
    for pad in fp.Pads():
        pos = _pos(pad)
        size = pad.GetSize()
        rows.append((
            pad.GetNumber(), pad.GetNetname(), pos[0], pos[1], size.x, size.y,
            pad.GetDrillSize().x, pad.GetDrillSize().y,
            int(pad.GetShape()), pad.GetLayerSet().FmtHex(),
        ))
    return sorted(rows)


def compare(base_path: Path, chain_path: Path):
    base = pcbnew.LoadBoard(str(base_path))
    chain = pcbnew.LoadBoard(str(chain_path))
    failures = []

    base_fp = {fp.GetReference(): fp for fp in base.GetFootprints()}
    chain_fp = {fp.GetReference(): fp for fp in chain.GetFootprints()}
    missing = sorted(set(base_fp) - set(chain_fp))
    extra = sorted(set(chain_fp) - set(base_fp))
    if missing or extra:
        failures.append(
            f"P-ROUTEBASE footprint set differs: missing={missing[:5]} "
            f"extra={extra[:5]}")
    graded_fp = 0
    for ref in sorted(set(base_fp) & set(chain_fp)):
        a, b = base_fp[ref], chain_fp[ref]
        graded_fp += 1
        if not _near(_pos(a), _pos(b)) or abs(
                a.GetOrientationDegrees() - b.GetOrientationDegrees()) > ROT_TOL_DEG \
                or a.GetLayer() != b.GetLayer():
            failures.append(
                f"P-ROUTEBASE {ref} placement differs: base "
                f"{_fmt_pos(_pos(a))}/{a.GetOrientationDegrees():.3f}deg/"
                f"{a.GetLayerName()} vs promoted "
                f"{_fmt_pos(_pos(b))}/{b.GetOrientationDegrees():.3f}deg/"
                f"{b.GetLayerName()}")
            continue
        if _pad_rows(a) != _pad_rows(b):
            failures.append(
                f"P-ROUTEBASE {ref} pad geometry/net identity differs")

    base_tracks, chain_tracks = _track_rows(base), _track_rows(chain)
    graded_tracks = 0
    for source in base_tracks:
        candidates = [row for row in chain_tracks
                      if row["net"] == source["net"]
                      and row["layer"] == source["layer"]
                      and _near(row["a"], source["a"])
                      and _near(row["b"], source["b"])]
        if not candidates:
            failures.append(
                f"P-ROUTEBASE prepared segment missing from promoted chain: "
                f"{source['net']} {_fmt_pos(source['a'])}->"
                f"{_fmt_pos(source['b'])}")
            continue
        graded_tracks += 1
        if abs(candidates[0]["width"] - source["width"]) > DIM_TOL_NM:
            failures.append(
                f"P-ROUTEBASE prepared segment width differs: "
                f"{source['net']} {_fmt_pos(source['a'])}->"
                f"{_fmt_pos(source['b'])} base "
                f"{pcbnew.ToMM(source['width']):.3f}mm vs promoted "
                f"{pcbnew.ToMM(candidates[0]['width']):.3f}mm")

    base_vias, chain_vias = _via_rows(base), _via_rows(chain)
    graded_vias = 0
    for source in base_vias:
        candidates = [row for row in chain_vias
                      if row["net"] == source["net"]
                      and _near(row["pos"], source["pos"])]
        if not candidates:
            failures.append(
                f"P-ROUTEBASE source via missing from promoted chain: "
                f"{source['net']} {_fmt_pos(source['pos'])}")
            continue
        graded_vias += 1
        match = candidates[0]
        if abs(match["diameter"] - source["diameter"]) > DIM_TOL_NM \
                or abs(match["drill"] - source["drill"]) > DIM_TOL_NM:
            failures.append(
                f"P-ROUTEBASE source via geometry differs: {source['net']} "
                f"{_fmt_pos(source['pos'])} base "
                f"{pcbnew.ToMM(source['diameter']):.3f}/"
                f"{pcbnew.ToMM(source['drill']):.3f}mm vs promoted "
                f"{pcbnew.ToMM(match['diameter']):.3f}/"
                f"{pcbnew.ToMM(match['drill']):.3f}mm")
        if (match["cap"], match["fill"]) != (source["cap"], source["fill"]):
            failures.append(
                f"P-ROUTEBASE source via process differs: {source['net']} "
                f"{_fmt_pos(source['pos'])} base cap/fill="
                f"{source['cap']}/{source['fill']} vs promoted "
                f"{match['cap']}/{match['fill']}")
    return failures, graded_fp, graded_vias, graded_tracks


def _prepared_path(root: Path, cfg: dict):
    project = cfg.get("project") or {}
    prep = cfg.get("prep") or {}
    build = _resolve(root, project.get("build_dir", "06_build/route"))
    return build / str(prep.get("out", "r0.kicad_pcb"))


def _prep_copper_declared(cfg: dict):
    prep = cfg.get("prep") or {}
    return bool((((prep.get("seed_stubs") or {}).get("stubs")) or [])
                or prep.get("pad_rescue"))


def check(base_path: Path, route_path: Path):
    route_path = route_path.resolve()
    cfg = yaml.safe_load(route_path.read_text(encoding="utf-8-sig")) or {}
    routing = cfg.get("route") or {}
    if not isinstance(routing, dict):
        return ["P-ROUTEBASE route: must be a mapping"], None, 0, 0, 0
    if routing.get("import_source", "auto") != "promoted":
        return [], "P-ROUTEBASE N-A: route.import_source is not promoted", 0, 0, 0
    final = routing.get("final")
    if not final:
        return [], "P-ROUTEBASE N-A: no route.final configured (first route)", 0, 0, 0
    chain = _resolve(_root(route_path), final)
    if not chain.is_file():
        return [], (f"P-ROUTEBASE N-A: promoted artifact {chain} does not yet "
                    "exist (first route)"), 0, 0, 0
    root = _root(route_path)
    prepared = _prepared_path(root, cfg)
    subject = base_path.resolve()
    failures = []
    if _prep_copper_declared(cfg):
        if not prepared.is_file():
            return [f"P-ROUTEBASE prepared base missing: {prepared}; run "
                    "route prep before placement review"], None, 0, 0, 0
        newest_input = max(base_path.stat().st_mtime_ns,
                           route_path.stat().st_mtime_ns)
        if prepared.stat().st_mtime_ns < newest_input:
            return [f"P-ROUTEBASE prepared base is stale: {prepared}"], \
                None, 0, 0, 0
        base_errors, _fp, _vias, _tracks = compare(base_path.resolve(), prepared)
        failures.extend(f"prepared/base: {item}" for item in base_errors)
        subject = prepared
    route_errors, footprints, vias, tracks = compare(subject, chain)
    failures.extend(route_errors)
    return failures, None, footprints, vias, tracks


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("route_config")
    args = ap.parse_args(argv)
    failures, note, footprints, vias, tracks = check(
        Path(args.board), Path(args.route_config))
    if note:
        print(note)
        return 0
    print(f"P-ROUTEBASE coverage: {footprints} footprints / {vias} "
          f"base/prepared vias / {tracks} prepared segments compared")
    for failure in failures:
        print(f"  FAIL {failure}")
    if failures:
        print(f"P-ROUTEBASE FAIL: {len(failures)} finding(s)")
        return 1
    print("P-ROUTEBASE PASS: promoted route is compatible with the exact base")
    return 0


if __name__ == "__main__":
    sys.exit(main())
