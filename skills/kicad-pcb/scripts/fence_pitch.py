#!/usr/bin/env python3
"""Measure the realized plated-GND fence along every saved RF centreline.

Independent of the emitter (canon M1): this gate reopens the SAVED
``.kicad_pcb`` through pcbnew, reconstructs each named F.Cu route from its own
track graph, and projects realized GND vias/PTH posts onto both flanks.  It
does not read ``route.yaml`` and never credits an attempted or declared site.

The graded aperture includes all three spans a travelling wave encounters:

* launch/package endpoint to the first plated fence element (lead-in),
* every element-to-element interior span, and
* the last element to the opposite endpoint (run-out).

The former checker graded only interior spans, silently passed a board whose
entire far end had no fence, and hard-coded one historical board's 11 net
names.  This version accepts an exact net denominator or discovers the RF
nets that actually carry saved F.Cu tracks.  Missing, branched, disconnected,
arc-only and zero-length subjects are explicit coverage failures.

Why along-route rather than nearest-neighbour distance: the wall aperture is
what the wave sees while travelling along the line.  On an angled arm a
rectangular lattice's projection can exceed its nominal X/Y pitch, so lattice
configuration cannot certify the realized fence.

Usage:
  fence_pitch.py BOARD [band_mm] [bound_mm]
      [--nets RF_COMMON,RF_ANT1,...] [--layer F.Cu]
      [--ground-net GND] [--json REPORT.json]

The two optional positional numbers are retained for existing callers.
``band_mm`` is the maximum perpendicular distance at which a plated element
may be credited to a flank; ``bound_mm`` is the maximum allowed along-route
aperture, including endpoint spans.
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path

import pcbnew
import yaml


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("board")
    ap.add_argument("band_mm", nargs="?", type=float)
    ap.add_argument("bound_mm", nargs="?", type=float)
    ap.add_argument("--nets",
                    help="comma-separated exact RF-net denominator; default "
                         "discovers saved F.Cu RF/ANT/RX track nets")
    ap.add_argument("--layer")
    ap.add_argument("--ground-net", default="GND")
    ap.add_argument("--contract",
                    help="rf.yaml requirement authority; supplies and pins "
                         "the exact route nets, layer and maximum pitch")
    ap.add_argument("--json", dest="json_out")
    return ap.parse_args(argv)


def xy(point):
    return point.x / 1e6, point.y / 1e6


def discover_nets(board, layer):
    """RF-looking nets with realized straight copper on the graded layer."""
    names = set()
    pattern = re.compile(r"^(?:RF(?:_|$)|ANT(?:ENNA)?\d|RX\d)", re.I)
    for item in board.GetTracks():
        if (item.GetClass() == "PCB_TRACK" and item.GetLayer() == layer
                and pattern.match(item.GetNetname() or "")):
            names.add(item.GetNetname())
    return sorted(names)


def polyline(board, net, layer):
    """Return ``(ordered_points_mm, error)`` for one exact simple chain."""
    tracks, unsupported = [], []
    for item in board.GetTracks():
        if item.GetNetname() != net or item.GetLayer() != layer:
            continue
        if item.GetClass() == "PCB_TRACK":
            tracks.append(item)
        elif item.GetClass() != "PCB_VIA":
            unsupported.append(item.GetClass())
    if unsupported:
        return [], f"unsupported copper {sorted(set(unsupported))}"
    if not tracks:
        return [], "no saved straight-track centreline"

    def key(p):
        return int(p.x), int(p.y)

    points, adjacency = {}, {}
    for index, track in enumerate(tracks):
        a, b = key(track.GetStart()), key(track.GetEnd())
        if a == b:
            return [], "zero-length track"
        points[a], points[b] = track.GetStart(), track.GetEnd()
        adjacency.setdefault(a, []).append((index, b))
        adjacency.setdefault(b, []).append((index, a))
    branches = [p for p, edges in adjacency.items() if len(edges) > 2]
    ends = sorted(p for p, edges in adjacency.items() if len(edges) == 1)
    if branches or len(ends) != 2:
        return [], (f"not one simple chain: {len(branches)} branch node(s), "
                    f"{len(ends)} endpoint(s)")
    ordered, used, current = [ends[0]], set(), ends[0]
    while True:
        nxt = next(((i, other) for i, other in adjacency[current]
                    if i not in used), None)
        if nxt is None:
            break
        index, current = nxt
        used.add(index)
        ordered.append(current)
    if len(used) != len(tracks) or ordered[-1] != ends[1]:
        return [], f"disconnected: reached {len(used)}/{len(tracks)} segments"
    return [xy(points[p]) for p in ordered], None


def total_length(chain):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1])
               for a, b in zip(chain, chain[1:]))


def projections(chain, px, py):
    """Every finite-segment ``(distance, arclength, side)`` projection.

    A plated return beside a bend can serve both adjacent arms.  Crediting
    only its nearest point invents an aperture through the vertex and makes
    the verdict depend on which segment happened to win a floating-point
    tie.  Keep one bounded projection per realized straight segment; the
    grading band and side filters below remain unchanged.
    """
    hits, walked = [], 0.0
    for a, b in zip(chain, chain[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length <= 1e-12:
            continue
        raw = ((px - a[0]) * dx + (py - a[1]) * dy) / (length * length)
        t = max(0.0, min(1.0, raw))
        qx, qy = a[0] + t * dx, a[1] + t * dy
        distance = math.hypot(px - qx, py - qy)
        cross = (dx * (py - a[1]) - dy * (px - a[0])) / length
        hits.append((distance, walked + t * length,
                     1 if cross >= 0.0 else -1))
        walked += length
    return hits


def project(chain, px, py):
    """Nearest projection retained for callers needing one route point."""
    hits = projections(chain, px, py)
    return min(hits, key=lambda hit: hit[0]) if hits else None


def plated_elements(board, ground_net):
    """Every realized plated hole tied to the selected reference net."""
    elements, posts = [], 0
    for item in board.GetTracks():
        if item.GetClass() == "PCB_VIA" and item.GetNetname() == ground_net:
            elements.append(xy(item.GetPosition()))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname() != ground_net or pad.GetDrillSizeX() <= 0:
                continue
            elements.append(xy(pad.GetPosition()))
            posts += 1
    return elements, posts


def endpoint_refs(board, net, chain):
    """Exact footprint-pad owner at each ordered route endpoint."""
    refs = []
    for x, y in (chain[0], chain[-1]):
        point = pcbnew.VECTOR2I_MM(x, y)
        matches = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if (pad.GetNetname() == net
                        and pad.GetBoundingBox().Contains(point)):
                    matches.append(fp.GetReference())
        matches = sorted(set(matches))
        if len(matches) != 1:
            return (), (f"endpoint ({x:.4f},{y:.4f}) belongs to "
                        f"{matches or 'no exact net pad'}")
        refs.append(matches[0])
    return tuple(refs), None


def endpoint_span_map(fence_contract):
    spans, errors = {}, []
    for i, row in enumerate(fence_contract.get("endpoint_structures") or []):
        if not isinstance(row, dict):
            errors.append(f"endpoint_structures[{i}] is not a mapping")
            continue
        try:
            span = float(row["maximum_along_route_span_mm"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"endpoint_structures[{i}] has no numeric span")
            continue
        for ref in row.get("refs") or []:
            ref = str(ref)
            if ref in spans:
                errors.append(f"endpoint_structures repeats ref {ref}")
            spans[ref] = span
    return spans, errors


def grade(argv=None):
    args = parse_args(argv)
    board_path = Path(args.board).resolve()
    board = pcbnew.LoadBoard(str(board_path))
    contract_path = Path(args.contract).resolve() if args.contract else None
    contract_route, contract_fence = {}, {}
    if contract_path:
        try:
            contract = yaml.safe_load(
                contract_path.read_text(encoding="utf-8-sig")) or {}
            layout = contract["rf"]["layout_constraints"]
            contract_route = layout["route"]
            contract_fence = layout["ground_fence"]
        except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
            print(f"input: board =    {board_path}")
            print(f"COVERAGE FAIL: cannot load RF contract {contract_path}: {exc}")
            print("coverage: 0/0 configured arm-sides graded; 0/0 pass")
            print("VERDICT: FAIL")
            return 1

    layer_name = args.layer or contract_route.get("layer") or "F.Cu"
    if args.layer and contract_route.get("layer") \
            and args.layer != str(contract_route["layer"]):
        print(f"input: board =    {board_path}")
        print("COVERAGE FAIL: --layer disagrees with RF-contract route.layer")
        print("coverage: 0/0 configured arm-sides graded; 0/0 pass")
        print("VERDICT: FAIL")
        return 1
    layer = board.GetLayerID(layer_name)
    explicit_nets = ([n.strip() for n in args.nets.split(",") if n.strip()]
                     if args.nets else [])
    contract_nets = [str(n) for n in (contract_route.get("nets") or [])]
    if explicit_nets and contract_nets and explicit_nets != contract_nets:
        print(f"input: board =    {board_path}")
        print("COVERAGE FAIL: --nets disagrees with RF-contract route.nets")
        print("coverage: 0/0 configured arm-sides graded; 0/0 pass")
        print("VERDICT: FAIL")
        return 1
    nets = explicit_nets or contract_nets or discover_nets(board, layer)
    contract_bound = contract_fence.get("maximum_along_route_pitch_mm")
    if args.bound_mm is not None and contract_bound is not None \
            and abs(args.bound_mm - float(contract_bound)) > 1e-9:
        print(f"input: board =    {board_path}")
        print("COVERAGE FAIL: bound_mm disagrees with RF-contract "
              "maximum_along_route_pitch_mm")
        print("coverage: 0/0 configured arm-sides graded; 0/0 pass")
        print("VERDICT: FAIL")
        return 1
    band_mm = args.band_mm if args.band_mm is not None else 2.5
    bound_mm = (args.bound_mm if args.bound_mm is not None else
                float(contract_bound) if contract_bound is not None else 1.1910)
    if band_mm <= 0 or bound_mm <= 0:
        print(f"input: board =    {board_path}")
        print("COVERAGE FAIL: band_mm and bound_mm must both be positive")
        print("coverage: 0/0 configured arm-sides graded; 0/0 pass")
        print("VERDICT: FAIL")
        return 1
    elements, posts = plated_elements(board, args.ground_net)
    span_map, span_errors = endpoint_span_map(contract_fence)

    print(f"input: board =    {board_path}")
    print(f"input: layer =    {layer_name}")
    print(f"input: RF nets =  {','.join(nets) if nets else '(none discovered)'}")
    print(f"input: GND net =  {args.ground_net}")
    if contract_path:
        print(f"input: contract = {contract_path}")
    print(f"GND fence elements: {len(elements)}  "
          f"(of which PTH GND pads/posts: {posts})")
    print(f"band = +/-{band_mm:.4f}mm; maximum aperture, including "
          f"endpoint spans = {bound_mm:.4f}mm\n")
    header = (f"{'net':<18}{'len':>8} {'side':>5}{'n':>5}{'max':>9}"
              f"{'lead':>9}{'runout':>9}{'offsets(mm)':>24}  verdict")
    print(header)

    results, errors = [], list(span_errors)
    worst, worst_where = 0.0, ""
    for net in nets:
        chain, error = polyline(board, net, layer)
        if error:
            errors.append(f"{net}: {error}")
            print(f"{net:<18} UNGRADED — {error}")
            continue
        length = total_length(chain)
        if contract_fence.get("endpoint_structures"):
            refs, endpoint_error = endpoint_refs(board, net, chain)
            if endpoint_error:
                errors.append(f"{net}: {endpoint_error}")
                print(f"{net:<18} UNGRADED — {endpoint_error}")
                continue
            missing = [ref for ref in refs if ref not in span_map]
            if missing:
                error = f"endpoint ref(s) {missing} have no endpoint structure"
                errors.append(f"{net}: {error}")
                print(f"{net:<18} UNGRADED — {error}")
                continue
        else:
            refs = ("route-start", "route-end")
        start = span_map.get(refs[0], 0.0)
        stop = length - span_map.get(refs[1], 0.0)
        if start >= stop - 1e-9:
            error = (f"endpoint structures consume route: {refs[0]}={start}, "
                     f"{refs[1]}={length - stop}, length={length:.4f}")
            errors.append(f"{net}: {error}")
            print(f"{net:<18} UNGRADED — {error}")
            continue
        for side in (-1, 1):
            projected = []
            for x, y in elements:
                for distance, s, hit_side in projections(chain, x, y):
                    if distance <= band_mm + 1e-9 and hit_side == side:
                        projected.append((max(start, min(stop, s)), distance))
            # Multiple plated elements may project onto one arclength.  One
            # aperture boundary is enough; retain the closest offset there.
            by_s = {}
            for s, distance in projected:
                key = round(s, 4)
                by_s[key] = min(distance, by_s.get(key, distance))
            points = sorted(by_s)
            interior = [s for s in points
                        if start + 1e-6 < s < stop - 1e-6]
            boundaries = [start] + interior + [stop]
            gaps = [boundaries[i + 1] - boundaries[i]
                    for i in range(len(boundaries) - 1)]
            aperture = max(gaps) if gaps else length
            graded_length = stop - start
            lead = interior[0] - start if interior else graded_length
            runout = stop - interior[-1] if interior else graded_length
            offsets = [by_s[s] for s in points]
            ok = aperture <= bound_mm + 1e-9
            tag = "R" if side < 0 else "L"
            if aperture > worst:
                index = gaps.index(aperture) if gaps else 0
                worst = aperture
                worst_where = (f"{net} {tag} at "
                               f"s={boundaries[index]:.3f}.."
                               f"{boundaries[index + 1]:.3f}")
            offset_text = ((f"{min(offsets):.2f}-{max(offsets):.2f}"
                            f" ({len(set(round(v, 2) for v in offsets))})")
                           if offsets else "none")
            print(f"{net:<18}{length:8.3f} {tag:>5}{len(points):5d}"
                  f"{aperture:9.4f}{lead:9.4f}{runout:9.4f}"
                  f"{offset_text:>24}  {'OK' if ok else 'OVER'}")
            results.append({"net": net, "side": tag, "length_mm": length,
                            "elements": len(points),
                            "maximum_aperture_mm": aperture,
                            "lead_in_mm": lead, "run_out_mm": runout,
                            "endpoint_refs": list(refs),
                            "start_endpoint_span_mm": start,
                            "end_endpoint_span_mm": length - stop,
                            "minimum_offset_mm": min(offsets) if offsets else None,
                            "maximum_offset_mm": max(offsets) if offsets else None,
                            "verdict": "PASS" if ok else "FAIL"})

    total = 2 * len(nets)
    graded = len(results)
    passed = sum(row["verdict"] == "PASS" for row in results)
    failed = total == 0 or graded != total or passed != total or bool(errors)
    print(f"\nWORST along-route aperture: {worst:.4f}mm  [{worst_where or 'none'}]")
    print(f"coverage: {graded}/{total} configured arm-sides graded; "
          f"{passed}/{total} pass")
    for error in errors:
        print(f"COVERAGE FAIL: {error}")
    print(f"BOUND: <= {bound_mm:.4f}mm on both saved-board flanks, "
          "including launch/package endpoint spans")
    print("VERDICT: " + ("FAIL" if failed else "PASS"))

    if args.json_out:
        payload = {"schema": 1, "board": str(board_path),
                   "layer": layer_name, "ground_net": args.ground_net,
                   "contract": str(contract_path) if contract_path else None,
                   "nets": nets, "band_mm": band_mm,
                   "maximum_aperture_mm": bound_mm,
                   "coverage": {"graded": graded, "total": total,
                                "passed": passed},
                   "worst_aperture_mm": worst,
                   "worst_where": worst_where, "errors": errors,
                   "results": results,
                   "verdict": "FAIL" if failed else "PASS"}
        path = Path(args.json_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"report: {path.resolve()}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(grade())
