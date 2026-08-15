#!/usr/bin/env python3
"""RF-SOURCE/RF-REALIZED: bounded RF geometry gates and evidence bundles.

Usage:
  rf_check.py source PROJECT [--contract PATH] [--route PATH] [--context PATH]
  rf_check.py realized PROJECT [--contract PATH] [--route PATH] [--board PATH]

The source mode grades authored route primitives before expensive generation.
The realized mode independently reopens the saved board, inventories the exact
RF-net denominator, and runs the saved-board fence checker with a heartbeat and
hard timeout. Geometry is advisory for legacy contracts and becomes blocking
only through ``rf.process.geometry_policy: blocking``; tests exercise the same
sharp subject under both policies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PCB_DESIGN_SCRIPTS = HERE.parents[1] / "pcb-design" / "scripts"
sys.path.insert(0, str(PCB_DESIGN_SCRIPTS))
sys.path.insert(0, str(HERE))
from pipeline_artifacts import ArtifactBundleTransaction
from process_runner import run_bounded
from rf_bundle import file_sha256, fresh_bundle

VERSION = "1"


class RFCheckError(RuntimeError):
    pass


def _load_yaml(path: Path, label: str) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise RFCheckError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RFCheckError(f"{label} root must be a mapping")
    return data


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"))
            + "\n").encode()


def _contract_state(contract: dict) -> tuple[dict, str, bool, str]:
    if contract.get("schema") != 1 or not isinstance(contract.get("rf"), dict):
        raise RFCheckError("rf.yaml must carry schema: 1 and an rf mapping")
    rf = contract["rf"]
    if not isinstance(rf.get("enabled"), bool):
        raise RFCheckError("rf.enabled must be true or false")
    process = rf.get("process") or {}
    if not isinstance(process, dict):
        raise RFCheckError("rf.process must be a mapping")
    adopted = bool(process)
    if adopted and process.get("profile") != "rf-module-v1":
        raise RFCheckError("rf.process.profile must be rf-module-v1")
    policy = str(process.get("geometry_policy", "advisory"))
    if policy not in {"advisory", "blocking"}:
        raise RFCheckError("rf.process.geometry_policy must be advisory or blocking")
    geometry_stage = str(process.get("geometry_stage", "source"))
    if geometry_stage not in {"source", "placement"}:
        raise RFCheckError("rf.process.geometry_stage must be source or placement")
    return rf, policy, adopted, geometry_stage


def _resolve(project: Path, supplied: Path | None, default: str) -> Path:
    path = supplied if supplied is not None else Path(default)
    return path.resolve() if path.is_absolute() else (project / path).resolve()


def _route_board(project: Path, route: dict, supplied: Path | None) -> Path:
    if supplied is not None:
        return _resolve(project, supplied, "")
    try:
        value = route["project"]["board"]
    except (KeyError, TypeError):
        raise RFCheckError("route.yaml project.board is required")
    return _resolve(project, None, str(value))


def _route_fence_config(route: dict) -> dict:
    value = (route.get("stitch") or {}).get("route_fence") or {}
    if not isinstance(value, dict):
        raise RFCheckError("route.yaml stitch.route_fence must be a mapping")
    return value


def _validate_context_bundle(path: Path, contract_path: Path) -> None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
        context_path = path.parent / "context.json"
        context = json.loads(context_path.read_text(encoding="utf-8-sig"))
    except (OSError, TypeError, ValueError) as exc:
        raise RFCheckError(f"cannot parse RF context bundle {path}: {exc}") from exc
    if (manifest.get("schema") != 1 or manifest.get("status") != "PASS"
            or context.get("schema") != 1 or context.get("status") != "ACTIVE"):
        raise RFCheckError("RF context bundle is not a schema-1 ACTIVE/PASS result")
    contract_hash = ((manifest.get("inputs") or {}).get("rf.yaml") or {}).get(
        "sha256")
    if contract_hash != file_sha256(contract_path):
        raise RFCheckError("RF context bundle does not bind the current rf.yaml")
    output = ((manifest.get("outputs") or {}).get("context.json") or {})
    if (not context_path.is_file()
            or output.get("sha256") != file_sha256(context_path)
            or output.get("size") != context_path.stat().st_size):
        raise RFCheckError("RF context bundle does not bind its context.json")


def _bend_contract(rf: dict) -> tuple[float, list[dict]]:
    route = ((rf.get("layout_constraints") or {}).get("route") or {})
    bend = route.get("bend_policy") or {}
    if not isinstance(bend, dict):
        raise RFCheckError("rf.layout_constraints.route.bend_policy must be a mapping")
    multiple = bend.get("minimum_radius_width_multiple", 3.0)
    try:
        multiple = float(multiple)
    except (TypeError, ValueError) as exc:
        raise RFCheckError("bend minimum radius multiple must be numeric") from exc
    if multiple <= 0:
        raise RFCheckError("bend minimum radius multiple must be positive")
    source_claim_ids = bend.get("source_claim_ids")
    if bend and (not isinstance(source_claim_ids, list) or not source_claim_ids
                 or any(not isinstance(value, str) or not value.strip()
                        for value in source_claim_ids)):
        raise RFCheckError("bend source_claim_ids must be non-empty strings")
    exceptions = bend.get("exceptions") or []
    if not isinstance(exceptions, list):
        raise RFCheckError("bend exceptions must be a list")
    return multiple, exceptions


def _exception_for(exceptions: list[dict], net: str, point: tuple[float, float]):
    for row in exceptions:
        if not isinstance(row, dict) or str(row.get("net")) != net:
            continue
        at = row.get("at_mm")
        try:
            tolerance = float(row.get("tolerance_mm"))
            distance = math.hypot(point[0] - float(at[0]),
                                  point[1] - float(at[1]))
        except (TypeError, ValueError, IndexError):
            continue
        if distance <= tolerance + 1e-9:
            return str(row.get("id", "unnamed"))
    return None


def _circle(start, mid, end):
    ax, ay = start; bx, by = mid; cx, cy = end
    determinant = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(determinant) <= 1e-12:
        raise RFCheckError(f"arc {start}->{mid}->{end} is collinear")
    aa, bb, cc = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
    ux = (aa * (by - cy) + bb * (cy - ay) + cc * (ay - by)) / determinant
    uy = (aa * (cx - bx) + bb * (ax - cx) + cc * (bx - ax)) / determinant
    return (ux, uy), math.hypot(ax - ux, ay - uy)


def _arc_tangents(start, mid, end, center):
    """Unit travel tangents at the authored start/end of a three-point arc."""
    angles = [math.atan2(point[1] - center[1], point[0] - center[0])
              for point in (start, mid, end)]
    a0, am, a1 = angles
    ccw = (a1 - a0) % (2.0 * math.pi)
    sweep = ccw if (am - a0) % (2.0 * math.pi) <= ccw + 1e-9 \
        else -((a0 - a1) % (2.0 * math.pi))
    direction = 1.0 if sweep >= 0 else -1.0
    tangent = lambda angle: (-math.sin(angle) * direction,
                             math.cos(angle) * direction)
    return tangent(a0), tangent(a0 + sweep)


def _primitive_tangent(primitive: dict, at_end: bool) -> tuple[float, float]:
    """Unit tangent in chain-travel direction at one realized endpoint."""
    if primitive["kind"] == "line":
        start, end = primitive["start"], primitive["end"]
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        if length <= 1e-12:
            raise RFCheckError("route contains a zero-length line primitive")
        return dx / length, dy / length
    angle = (primitive["start_angle"]
             + (primitive["sweep"] if at_end else 0.0))
    direction = 1.0 if primitive["sweep"] >= 0 else -1.0
    return -math.sin(angle) * direction, math.cos(angle) * direction


def _vector_turn(first, second) -> float:
    """Direction change in degrees between two unit-ish travel vectors."""
    la, lb = math.hypot(*first), math.hypot(*second)
    if la <= 1e-12 or lb <= 1e-12:
        raise RFCheckError("route contains a zero-length tangent")
    dot = max(-1.0, min(1.0, (first[0] * second[0]
                              + first[1] * second[1]) / (la * lb)))
    return math.degrees(math.acos(dot))


def _point(value, label):
    if (not isinstance(value, list) or len(value) != 2
            or not all(isinstance(v, (int, float)) for v in value)):
        raise RFCheckError(f"{label} must be a numeric [x, y] point")
    return float(value[0]), float(value[1])


def _source_inventory(rf: dict, route: dict, policy: str, *,
                      geometry_stage: str = "source",
                      require_geometry: bool = False) -> dict:
    layout = rf.get("layout_constraints") or {}
    authority = layout.get("route") or {}
    fence_authority = layout.get("ground_fence") or {}
    nets = [str(v) for v in authority.get("nets") or []]
    if not nets:
        if geometry_stage == "placement" and not require_geometry:
            return {"schema": 1, "mode": "source", "status": "DEFERRED",
                    "geometry_policy": policy, "geometry_stage": geometry_stage,
                    "nets": [], "coverage": {"graded": 0, "total": 0},
                    "routes": [], "bend_findings": [], "errors": [],
                    "advisories": ["RF route coordinates are explicitly "
                                   "deferred to the placement checkpoint"],
                    "verdict": "PASS"}
        pending = [str(row.get("id")) for row in rf.get("cross_sections") or []
                   if isinstance(row, dict)
                   and row.get("status", "locked") == "pending_solver"]
        if pending:
            return {"schema": 1, "mode": "source", "status": "DEFERRED",
                    "geometry_policy": policy, "nets": [],
                    "coverage": {"graded": 0, "total": 0}, "routes": [],
                    "bend_findings": [], "errors": [],
                    "advisories": ["RF route geometry is correctly deferred "
                                   "until pending solver sections are locked: "
                                   + ", ".join(pending)],
                    "verdict": "PASS"}
        raise RFCheckError("RF route-net denominator is empty")
    seed = ((route.get("prep") or {}).get("seed_stubs") or {})
    stubs = seed.get("stubs") or []
    if not isinstance(stubs, list):
        raise RFCheckError("route prep.seed_stubs.stubs must be a list")
    by_net = {net: [] for net in nets}
    for row in stubs:
        if isinstance(row, dict) and str(row.get("net")) in by_net:
            by_net[str(row["net"])].append(row)
    multiple, exceptions = _bend_contract(rf)
    findings, errors, rows = [], [], []
    required_layer = str(authority.get("layer"))
    required_width = float(authority.get("width_mm", 0.0))
    maximum_vias = int(authority.get("maximum_vias_per_net", 0))
    maximum_stubs = int(authority.get("maximum_stubs_per_net", 0))
    for net in nets:
        declarations = by_net[net]
        if len(declarations) != 1:
            errors.append(f"{net}: expected exactly one planned route bank, got "
                          f"{len(declarations)}")
            continue
        row = declarations[0]
        lines, arcs = row.get("segments") or [], row.get("arcs") or []
        if not lines and not arcs:
            errors.append(f"{net}: route bank has no line/arc primitives")
            continue
        primitive_count = via_count = bend_count = arc_count = 0
        edges, edge_tangents, edge_kinds = [], [], []
        for j, segment in enumerate(lines):
            if not isinstance(segment, dict):
                errors.append(f"{net}: segments[{j}] is not a mapping")
                continue
            layer, width = str(segment.get("layer")), float(segment.get("width", 0))
            if layer != required_layer or abs(width - required_width) > 1e-9:
                errors.append(f"{net}: line layer/width {layer}/{width} disagrees "
                              f"with {required_layer}/{required_width}")
            pts = [_point(value, f"{net}.segments[{j}].pts")
                   for value in segment.get("pts") or []]
            if len(pts) < 2:
                errors.append(f"{net}: segments[{j}] needs at least two points")
                continue
            primitive_count += len(pts) - 1
            for start, end in zip(pts, pts[1:]):
                edges.append((start, end))
                dx, dy = end[0] - start[0], end[1] - start[1]
                length = math.hypot(dx, dy)
                tangent = ((dx / length, dy / length) if length > 1e-12
                           else (0.0, 0.0))
                edge_tangents.append((tangent, tangent))
                edge_kinds.append("line")
        for j, arc in enumerate(arcs):
            if not isinstance(arc, dict):
                errors.append(f"{net}: arcs[{j}] is not a mapping")
                continue
            layer, width = str(arc.get("layer")), float(arc.get("width", 0))
            if layer != required_layer or abs(width - required_width) > 1e-9:
                errors.append(f"{net}: arc layer/width {layer}/{width} disagrees "
                              f"with {required_layer}/{required_width}")
            start = _point(arc.get("start"), f"{net}.arcs[{j}].start")
            mid = _point(arc.get("mid"), f"{net}.arcs[{j}].mid")
            end = _point(arc.get("end"), f"{net}.arcs[{j}].end")
            center, radius = _circle(start, mid, end)
            edges.append((start, end))
            edge_tangents.append(_arc_tangents(start, mid, end, center))
            edge_kinds.append("arc")
            primitive_count += 1; arc_count += 1; bend_count += 1
            ratio = radius / width if width > 0 else 0.0
            exception = _exception_for(exceptions, net, mid)
            finding = {"net": net, "kind": "arc", "at_mm": list(mid),
                       "radius_mm": radius, "radius_width_multiple": ratio,
                       "exception": exception}
            findings.append(finding)
            if policy == "blocking" and ratio + 1e-9 < multiple \
                    and exception is None:
                errors.append(f"{net}: arc radius/width {ratio:.3f} < {multiple}")
        via_count = len(row.get("vias") or [])
        if via_count > maximum_vias:
            errors.append(f"{net}: {via_count} planned vias > {maximum_vias}")
        adjacency = {}
        for edge_index, (start, end) in enumerate(edges):
            for point, other in ((start, end), (end, start)):
                key = tuple(round(value, 6) for value in point)
                other_key = tuple(round(value, 6) for value in other)
                adjacency.setdefault(key, []).append((edge_index, other_key))
        # Inventory every primitive junction from the topology graph, not
        # from YAML list grouping. Splitting one polyline into several
        # two-point `segments` must not hide a sharp corner, and an arc only
        # removes the corner when its endpoint tangent is actually continuous.
        for point, neighbours in adjacency.items():
            if len(neighbours) != 2:
                continue
            outward = []
            kinds = []
            for edge_index, _other in neighbours:
                start, end = edges[edge_index]
                start_key = tuple(round(value, 6) for value in start)
                start_tangent, end_tangent = edge_tangents[edge_index]
                tangent = (start_tangent if point == start_key
                           else (-end_tangent[0], -end_tangent[1]))
                outward.append(tangent)
                kinds.append(edge_kinds[edge_index])
            if any(math.hypot(*tangent) <= 1e-12 for tangent in outward):
                errors.append(f"{net}: route contains a zero-length line primitive")
                continue
            turn = 180.0 - _vector_turn(outward[0], outward[1])
            if turn <= 0.5:
                continue
            bend_count += 1
            exception = _exception_for(exceptions, net, point)
            findings.append({
                "net": net,
                "kind": ("line_corner" if kinds == ["line", "line"]
                         else "primitive_junction"),
                "primitive_kinds": kinds,
                "at_mm": list(point),
                "turn_degrees": turn, "exception": exception,
                "minimum_radius_width_multiple": multiple,
            })
            if policy == "blocking" and exception is None:
                errors.append(f"{net}: unrounded {turn:.2f}-degree corner at "
                              f"{point}")
        branch_count = sum(max(0, len(neighbours) - 2)
                           for neighbours in adjacency.values())
        if edges:
            reached_edges, pending, seen_points = set(), [next(iter(adjacency))], set()
            while pending:
                point = pending.pop()
                if point in seen_points:
                    continue
                seen_points.add(point)
                for edge_index, other in adjacency[point]:
                    reached_edges.add(edge_index)
                    pending.append(other)
            if len(reached_edges) != len(edges):
                errors.append(f"{net}: planned line/arc primitives are disconnected "
                              f"({len(reached_edges)}/{len(edges)} reached)")
            ends = [point for point, neighbours in adjacency.items()
                    if len(neighbours) == 1]
            if maximum_stubs == 0 and (branch_count or len(ends) != 2):
                errors.append(f"{net}: planned route is not one simple chain "
                              f"({branch_count} branch stub(s), {len(ends)} endpoints)")
        extra_stubs = branch_count + max(0, len(declarations) - 1)
        if extra_stubs > maximum_stubs:
            errors.append(f"{net}: {extra_stubs} extra banks > {maximum_stubs}")
        rows.append({"net": net, "banks": len(declarations),
                     "primitives": primitive_count, "arcs": arc_count,
                     "bends": bend_count, "vias": via_count,
                     "stubs": extra_stubs})

    route_fence = _route_fence_config(route)
    contract_band = fence_authority.get("maximum_lateral_center_offset_mm")
    route_band = route_fence.get("band")
    authority_gap = contract_band is None
    if contract_band is not None and route_band is not None \
            and abs(float(contract_band) - float(route_band)) > 1e-9:
        errors.append("stitch.route_fence.band disagrees with contract "
                      "maximum_lateral_center_offset_mm")
    if route_band is None and contract_band is None:
        errors.append("no route-following fence lateral grading band is declared")
    coverage = sum(1 for row in rows if row["net"] in nets)
    return {"schema": 1, "mode": "source", "geometry_policy": policy,
            "nets": nets, "coverage": {"graded": coverage, "total": len(nets)},
            "routes": rows, "bend_findings": findings,
            "fence_band_mm": (float(contract_band) if contract_band is not None
                              else float(route_band) if route_band is not None
                              else None),
            "fence_band_authority": ("rf.yaml" if contract_band is not None
                                     else "route.yaml-legacy"),
            "advisories": (["RF fence lateral band has legacy route-only "
                            "authority; promote it into rf.yaml before adopting "
                            "rf-module-v1"] if authority_gap else []),
            "errors": errors, "verdict": "FAIL" if errors else "PASS"}


def _realized_inventory(rf: dict, board_path: Path, policy: str) -> dict:
    try:
        import pcbnew
        import fence_pitch
    except ImportError as exc:
        raise RFCheckError(f"realized mode needs KiCad pcbnew: {exc}") from exc
    board = pcbnew.LoadBoard(str(board_path))
    authority = ((rf.get("layout_constraints") or {}).get("route") or {})
    nets = [str(v) for v in authority.get("nets") or []]
    layer_name = str(authority.get("layer"))
    layer = board.GetLayerID(layer_name)
    width = float(authority.get("width_mm", 0))
    maximum_vias = int(authority.get("maximum_vias_per_net", 0))
    maximum_stubs = int(authority.get("maximum_stubs_per_net", 0))
    multiple, exceptions = _bend_contract(rf)
    rows, findings, errors = [], [], []
    for net in nets:
        items = [item for item in board.GetTracks()
                 if item.GetNetname() == net]
        copper = [item for item in items if item.GetClass() in
                  ("PCB_TRACK", "PCB_ARC") and item.GetLayer() == layer]
        wrong_layer = [item for item in items if item.GetClass() in
                       ("PCB_TRACK", "PCB_ARC") and item.GetLayer() != layer]
        vias = [item for item in items if item.GetClass() == "PCB_VIA"]
        if wrong_layer:
            errors.append(f"{net}: {len(wrong_layer)} RF primitives on wrong layer")
        wrong_width = [item for item in copper
                       if abs(item.GetWidth() / 1e6 - width) > 1e-6]
        if wrong_width:
            errors.append(f"{net}: {len(wrong_width)} RF primitives have wrong width")
        if len(vias) > maximum_vias:
            errors.append(f"{net}: {len(vias)} realized vias > {maximum_vias}")
        chain, chain_error = fence_pitch.route_chain(board, net, layer)
        branch_count = 0
        if chain_error:
            errors.append(f"{net}: {chain_error}")
            rows.append({"net": net, "primitives": len(copper),
                         "vias": len(vias), "chain_error": chain_error})
            continue
        # A valid simple chain has no stubs. route_chain fails before this on
        # any branch/disconnection, keeping the exact denominator visible.
        if branch_count > maximum_stubs:
            errors.append(f"{net}: {branch_count} realized stubs > {maximum_stubs}")
        bend_count = arc_count = 0
        for primitive in chain:
            if primitive["kind"] == "arc":
                arc_count += 1; bend_count += 1
                ratio = primitive["radius"] / width
                exception = _exception_for(exceptions, net, primitive["mid"])
                findings.append({"net": net, "kind": "arc",
                                 "at_mm": list(primitive["mid"]),
                                 "radius_mm": primitive["radius"],
                                 "radius_width_multiple": ratio,
                                 "exception": exception})
                if policy == "blocking" and ratio + 1e-9 < multiple \
                        and exception is None:
                    errors.append(f"{net}: realized arc radius/width "
                                  f"{ratio:.3f} < {multiple}")
        for incoming, outgoing in zip(chain, chain[1:]):
            turn = _vector_turn(_primitive_tangent(incoming, True),
                                _primitive_tangent(outgoing, False))
            if turn <= 0.5:
                continue
            bend_count += 1
            point = incoming["end"]
            exception = _exception_for(exceptions, net, point)
            findings.append({"net": net,
                             "kind": ("line_corner" if incoming["kind"] ==
                                      outgoing["kind"] == "line"
                                      else "primitive_junction"),
                             "primitive_kinds": [incoming["kind"],
                                                 outgoing["kind"]],
                             "at_mm": list(point), "turn_degrees": turn,
                             "exception": exception,
                             "minimum_radius_width_multiple": multiple})
            if policy == "blocking" and exception is None:
                errors.append(f"{net}: realized unrounded {turn:.2f}-degree "
                              f"corner at {point}")
        rows.append({"net": net, "primitives": len(copper),
                     "arcs": arc_count, "bends": bend_count,
                     "vias": len(vias),
                     "length_mm": fence_pitch.total_length(chain)})
    return {"schema": 1, "mode": "realized", "board": str(board_path),
            "board_sha256": _sha(board_path.read_bytes()),
            "geometry_policy": policy, "nets": nets,
            "coverage": {"graded": len(rows), "total": len(nets)},
            "routes": rows, "bend_findings": findings, "errors": errors,
            "verdict": "FAIL" if errors else "PASS"}


def _report_text(report: dict, subject: Path) -> str:
    coverage = report["coverage"]
    lines = [f"input: {subject}", f"mode: {report['mode']}",
             f"geometry_policy: {report.get('geometry_policy', 'advisory')}",
             f"coverage: {coverage['graded']}/{coverage['total']} RF nets graded",
             f"bend_findings: {len(report.get('bend_findings') or [])}"]
    for advisory in report.get("advisories") or []:
        lines.append(f"ADVISORY: {advisory}")
    for error in report.get("errors") or []:
        lines.append(f"FAIL: {error}")
    lines.append(f"VERDICT: {report['verdict']}")
    return "\n".join(lines) + "\n"


def _publish_source(project: Path, contract_path: Path, route_path: Path,
                    context_path: Path | None, out: Path, *,
                    require_geometry: bool = False) -> tuple[dict, Path]:
    contract = _load_yaml(contract_path, "RF contract")
    rf, policy, adopted, geometry_stage = _contract_state(contract)
    if not rf["enabled"]:
        route = {}
        report = {"schema": 1, "mode": "source", "status": "N-A",
                  "geometry_policy": policy, "coverage": {"graded": 1, "total": 1},
                  "bend_findings": [], "errors": [], "verdict": "PASS"}
        inputs = {"rf.yaml": contract_path}
    else:
        route = _load_yaml(route_path, "route contract")
        report = _source_inventory(
            rf, route, policy, geometry_stage=geometry_stage,
            require_geometry=require_geometry)
        if report["verdict"] != "PASS":
            raise RFCheckError("; ".join(report["errors"]))
        inputs = {"rf.yaml": contract_path, "route.yaml": route_path}
        if context_path and context_path.is_file():
            _validate_context_bundle(context_path, contract_path)
            inputs["rf_context_bundle.json"] = context_path
        elif adopted:
            raise RFCheckError("rf-module-v1 source gate requires the RF context bundle")
    subject = _canonical({"rf": rf, "route": route if rf["enabled"] else None,
                          "report": report})
    raw = b"\0".join(path.read_bytes() for path in inputs.values())
    out.parent.mkdir(parents=True, exist_ok=True)
    subject_hashes = {"semantic_sha256": _sha(subject),
                      "raw_sha256": _sha(raw)}
    outputs = {"report.json": None, "report.txt": None}
    producer = ("rf_check.py source --require-geometry" if require_geometry
                else "rf_check.py source")
    if fresh_bundle(out, subject_hashes, inputs, set(outputs),
                    producer=producer, producer_version=VERSION):
        return report, out
    txn = ArtifactBundleTransaction(
        out, producer=producer, producer_version=VERSION,
        subject=subject_hashes, inputs=inputs, outputs=outputs)

    def produce(staging: Path):
        (staging / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
        (staging / "report.txt").write_text(_report_text(report, route_path))
        return 0 if report["verdict"] == "PASS" else 1

    return report, txn.publish(produce).path


def _publish_realized(project: Path, contract_path: Path, route_path: Path,
                      board_path: Path | None,
                      out: Path) -> tuple[dict, Path, Path]:
    contract = _load_yaml(contract_path, "RF contract")
    rf, policy, _adopted, _geometry_stage = _contract_state(contract)
    if not rf["enabled"]:
        # Applicability is source authority.  A non-RF project must not need a
        # route contract, board file, or pcbnew merely to prove that this gate
        # is N-A; keeping that path shallow is part of the anti-stall design.
        route = {}
        report = {"schema": 1, "mode": "realized", "status": "N-A",
                  "geometry_policy": policy, "coverage": {"graded": 1, "total": 1},
                  "bend_findings": [], "errors": [], "verdict": "PASS"}
        inputs = {"rf.yaml": contract_path}
        run_fence = False
        subject_path = contract_path
    else:
        route = _load_yaml(route_path, "route contract")
        board_path = board_path or _route_board(project, route, None)
        if not board_path.is_file():
            raise RFCheckError(f"saved board is missing: {board_path}")
        report = _realized_inventory(rf, board_path, policy)
        if report["verdict"] != "PASS":
            raise RFCheckError("; ".join(report["errors"]))
        inputs = {"rf.yaml": contract_path, "route.yaml": route_path,
                  "board.kicad_pcb": board_path}
        run_fence = True
        subject_path = board_path
    subject = _canonical({"rf": rf, "report": report})
    raw = b"\0".join(path.read_bytes() for path in inputs.values())
    outputs = {"report.json": None, "report.txt": None}
    if run_fence:
        outputs.update({"fence.json": None, "fence.txt": None,
                        "fence_process.json": None})
    out.parent.mkdir(parents=True, exist_ok=True)
    subject_hashes = {"semantic_sha256": _sha(subject),
                      "raw_sha256": _sha(raw)}
    producer = "rf_check.py realized"
    if fresh_bundle(out, subject_hashes, inputs, set(outputs),
                    producer=producer, producer_version=VERSION):
        return report, out, subject_path
    txn = ArtifactBundleTransaction(
        out, producer=producer, producer_version=VERSION,
        subject=subject_hashes,
        inputs=inputs, outputs=outputs)

    def produce(staging: Path):
        fence_rc = 0
        if run_fence:
            fence = (rf.get("layout_constraints") or {}).get("ground_fence") or {}
            route_fence = _route_fence_config(route)
            band = fence.get("maximum_lateral_center_offset_mm",
                             route_fence.get("band"))
            if band is None:
                report["errors"].append("no authoritative fence lateral band")
                report["verdict"] = "FAIL"
            else:
                command = ["/usr/bin/python3", str(HERE / "fence_pitch.py"),
                           str(board_path), str(float(band)), "--contract",
                           str(contract_path), "--json", str(staging / "fence.json")]
                result = run_bounded(
                    command, cwd=project, timeout_s=30, heartbeat_s=5,
                    label="rf-fence", state_path=staging / "fence_process.json")
                (staging / "fence.txt").write_text(result.output)
                fence_rc = result.returncode
                if fence_rc:
                    report["errors"].append(
                        f"saved-board fence gate exited {fence_rc}")
                    report["verdict"] = "FAIL"
        (staging / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n")
        (staging / "report.txt").write_text(_report_text(report, subject_path))
        return 0 if report["verdict"] == "PASS" and fence_rc == 0 else 1

    return report, txn.publish(produce).path, subject_path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=("source", "realized"))
    ap.add_argument("project", type=Path)
    ap.add_argument("--contract", type=Path)
    ap.add_argument("--route", type=Path)
    ap.add_argument("--context", type=Path,
                    help="context bundle manifest; required by rf-module-v1 source")
    ap.add_argument("--board", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--require-geometry", action="store_true",
                    help="fail if placement-deferred route geometry is absent")
    args = ap.parse_args(argv)
    project = args.project.resolve()
    contract_path = _resolve(project, args.contract, "03_src/rules/rf.yaml")
    route_path = _resolve(project, args.route, "03_src/route.yaml")
    context_path = (_resolve(project, args.context, "") if args.context else
                    project / "06_build/rf/context/bundle.json")
    out = (_resolve(project, args.out, "") if args.out else
           project / f"06_build/rf/{args.mode}")
    try:
        if args.mode == "source":
            report, published = _publish_source(
                project, contract_path, route_path, context_path, out,
                require_geometry=args.require_geometry)
            subject = route_path
        else:
            board = _resolve(project, args.board, "") if args.board else None
            report, published, subject = _publish_realized(
                project, contract_path, route_path, board, out)
    except Exception as exc:
        # Artifact errors are intentionally flattened into a stable gate
        # diagnostic; the accepted prior bundle is never replaced by failure.
        print(f"RF-{args.mode.upper()} input: {contract_path}")
        print(f"RF-{args.mode.upper()} coverage: 0/1 evidence bundle")
        print(f"RF-{args.mode.upper()} FAIL: {exc}")
        return 1
    coverage = report["coverage"]
    print(f"RF-{args.mode.upper()} input: {subject}")
    denominator = ("RF nets graded" if report.get("status") != "N-A"
                   else "applicability")
    print(f"RF-{args.mode.upper()} coverage: {coverage['graded']}/"
          f"{coverage['total']} {denominator}")
    print(f"RF-{args.mode.upper()} PASS: {report.get('status', 'ACTIVE')} -> "
          f"{published}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
