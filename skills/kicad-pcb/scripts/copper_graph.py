#!/usr/bin/env python3
"""Canonical, UUID-free copper and connectivity transaction primitives.

The public functions in this module consume and return JSON-compatible
mappings.  Synthetic item dictionaries are the reference input; a pcbnew board
or board path is accepted through a lazy adapter when pcbnew is available.

Coordinates in canonical output are integer nanometres.  Synthetic inputs may
use ``*_mm``, ``*_um`` or ``*_nm`` keys, or an unqualified key plus
``unit: mm|um|nm`` (``mm`` is the default).  UUIDs, timestamps, insertion
order, and source serialization never participate in a semantic signature.

Primary APIs:

* ``canonical_copper_inventory`` and ``diff_copper``
* ``connectivity_signature`` and ``requested_net_regressions``
* ``endpoint_layer_closure``
* ``filled_zone_components`` and ``power_graph_delta``
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any


SCHEMA = 1
_VOLATILE_KEYS = {
    "id", "uuid", "tstamp", "timestamp", "kiid", "m_uuid", "order",
    "index", "serialization", "source_text", "source_offset",
}
_KIND_ALIASES = {
    "segment": "track", "trace": "track", "pcb_track": "track",
    "pcb_via": "via", "footprint_pad": "pad", "endpoint": "pad",
    "filled_zone": "zone", "pour": "zone",
}


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def _digest(value: Any) -> str:
    return hashlib.sha256(_json_key(value).encode("utf-8")).hexdigest()


def _unit_scale(unit: str) -> int:
    normalized = str(unit or "mm").strip().lower()
    scales = {"nm": 1, "nanometre": 1, "nanometer": 1,
              "um": 1_000, "µm": 1_000,
              "mm": 1_000_000}
    if normalized not in scales:
        raise ValueError(f"unsupported coordinate unit {unit!r}")
    return scales[normalized]


def _number_nm(value: Any, unit: str) -> int:
    if value is None:
        return 0
    return int(round(float(value) * _unit_scale(unit)))


def _dimension_nm(item: Mapping[str, Any], name: str,
                  default: Any = 0) -> int:
    for suffix, unit in (("_nm", "nm"), ("_um", "um"), ("_mm", "mm")):
        key = name + suffix
        if key in item and item[key] is not None:
            return _number_nm(item[key], unit)
    return _number_nm(item.get(name, default), str(item.get("unit") or "mm"))


def _point_nm(value: Any, unit: str = "mm") -> tuple[int, int]:
    if isinstance(value, Mapping):
        if "x_nm" in value or "y_nm" in value:
            return (int(round(float(value.get("x_nm", 0)))),
                    int(round(float(value.get("y_nm", 0)))))
        if "x_um" in value or "y_um" in value:
            return (_number_nm(value.get("x_um", 0), "um"),
                    _number_nm(value.get("y_um", 0), "um"))
        if "x_mm" in value or "y_mm" in value:
            return (_number_nm(value.get("x_mm", 0), "mm"),
                    _number_nm(value.get("y_mm", 0), "mm"))
        local_unit = str(value.get("unit") or unit)
        return (_number_nm(value.get("x", 0), local_unit),
                _number_nm(value.get("y", 0), local_unit))
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) \
            and len(value) >= 2:
        return (_number_nm(value[0], unit), _number_nm(value[1], unit))
    raise ValueError(f"expected an XY point, got {value!r}")


def _named_point(item: Mapping[str, Any], name: str) -> tuple[int, int] | None:
    for suffix, unit in (("_nm", "nm"), ("_um", "um"), ("_mm", "mm")):
        key = name + suffix
        if key in item and item[key] is not None:
            return _point_nm(item[key], unit)
    if name in item and item[name] is not None:
        return _point_nm(item[name], str(item.get("unit") or "mm"))
    return None


def _layers(item: Mapping[str, Any]) -> list[str]:
    raw = item.get("layers")
    if raw is None:
        raw = item.get("pad_layers") or item.get("allowed_layers")
    if raw is None:
        raw = item.get("layer_span")
    if raw is None:
        raw = item.get("layer")
    if raw is None and (item.get("start_layer") or item.get("end_layer")):
        raw = [item.get("start_layer"), item.get("end_layer")]
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    return sorted({str(layer).strip() for layer in raw
                   if layer is not None and str(layer).strip()})


def _terminal(item: Mapping[str, Any]) -> str:
    direct = item.get("terminal") or item.get("endpoint")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    ref = (item.get("ref") or item.get("reference") or
           item.get("footprint"))
    pad = item.get("pad") if "pad" in item else item.get("number")
    if ref is not None and pad is not None:
        return f"{str(ref).strip()}.{str(pad).strip()}"
    return ""


def _canonical_ring(points: Any, unit: str = "mm") -> list[list[int]]:
    if not isinstance(points, Sequence) or isinstance(points, (str, bytes)):
        raise ValueError("polygon ring must be a point sequence")
    ring = [_point_nm(point, unit) for point in points]
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    if not ring:
        return []

    def rotations(row: list[tuple[int, int]]) -> Iterable[tuple[tuple[int, int], ...]]:
        for index in range(len(row)):
            yield tuple(row[index:] + row[:index])

    canonical = min((*rotations(ring), *rotations(list(reversed(ring)))))
    return [[x, y] for x, y in canonical]


def _looks_like_point(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(key in value for key in ("x", "x_mm", "x_um", "x_nm"))
    return (isinstance(value, Sequence) and not isinstance(value, (str, bytes))
            and len(value) >= 2 and not isinstance(value[0], (list, tuple, dict)))


def _canonical_polygons(raw: Any, unit: str = "mm") -> list[list[list[int]]]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        raw = (raw.get("polygons") or raw.get("polygon") or raw.get("outline")
               or raw.get("points") or [])
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("filled polygons must be a sequence")
    if not raw:
        return []
    rings = [raw] if _looks_like_point(raw[0]) else list(raw)
    result = [_canonical_ring(ring, unit) for ring in rings if ring]
    return sorted((ring for ring in result if ring), key=_json_key)


def _component(item: Mapping[str, Any], default_layers: list[str],
               default_unit: str) -> dict[str, Any]:
    layers = _layers(item) or list(default_layers)
    raw_polygons = (item.get("polygons_nm") if "polygons_nm" in item else
                    item.get("polygon_nm") if "polygon_nm" in item else
                    item.get("polygons") if "polygons" in item else
                    item.get("filled_polygons") if "filled_polygons" in item else
                    item.get("polygon") if "polygon" in item else
                    item.get("outline") if "outline" in item else [])
    terminals = (item.get("terminals") or item.get("pads") or
                 item.get("endpoints") or [])
    if isinstance(terminals, str):
        terminals = [terminals]
    return {
        "layers": layers,
        "polygons_nm": _canonical_polygons(
            raw_polygons,
            "nm" if "polygons_nm" in item or "polygon_nm" in item
            else str(item.get("unit") or default_unit)),
        "terminals": sorted({str(value).strip() for value in terminals
                             if str(value).strip()}),
    }


def _zone_components(item: Mapping[str, Any], layers: list[str]) -> list[dict[str, Any]]:
    unit = str(item.get("unit") or "mm")
    raw = item.get("components")
    components: list[dict[str, Any]] = []
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for value in raw:
            if isinstance(value, Mapping):
                components.append(_component(value, layers, unit))
            else:
                components.append(_component({"polygons": value}, layers, unit))
    else:
        filled = item.get("filled_polygons")
        if isinstance(filled, Mapping):
            for layer, polygons in sorted(filled.items(), key=lambda pair: str(pair[0])):
                for polygon in polygons or []:
                    components.append(_component(
                        {"layer": str(layer), "polygon": polygon,
                         "unit": unit}, layers, unit))
        elif filled is not None:
            polygons = _canonical_polygons(filled, unit)
            for polygon in polygons:
                components.append({"layers": layers,
                                   "polygons_nm": [polygon],
                                   "terminals": []})
        else:
            one = _component(item, layers, unit)
            if one["polygons_nm"] or one["terminals"]:
                components.append(one)
    return sorted(components, key=_json_key)


def _canonical_item(raw: Mapping[str, Any]) -> dict[str, Any]:
    kind = str(raw.get("kind") or raw.get("type") or "track").strip().lower()
    kind = _KIND_ALIASES.get(kind, kind)
    net = str(raw.get("net") or raw.get("net_name") or
              raw.get("netname") or "").strip()
    layers = _layers(raw)
    item: dict[str, Any] = {"kind": kind, "net": net, "layers": layers}

    if kind in {"track", "arc"}:
        start = _named_point(raw, "start")
        end = _named_point(raw, "end")
        if start is None or end is None:
            points = raw.get("points") or []
            if len(points) >= 2:
                start = _point_nm(points[0], str(raw.get("unit") or "mm"))
                end = _point_nm(points[-1], str(raw.get("unit") or "mm"))
        if start is None or end is None:
            raise ValueError(f"{kind} requires start and end")
        if kind == "track" and end < start:
            start, end = end, start
        item["start_nm"] = list(start)
        item["end_nm"] = list(end)
        if kind == "arc":
            mid = _named_point(raw, "mid") or _named_point(raw, "center")
            if mid is not None:
                item["mid_nm"] = list(mid)
        item["width_nm"] = _dimension_nm(raw, "width")
    elif kind == "via":
        at = (_named_point(raw, "at") or _named_point(raw, "position") or
              _named_point(raw, "center"))
        if at is None:
            raise ValueError("via requires at/position")
        item["at_nm"] = list(at)
        item["diameter_nm"] = _dimension_nm(
            raw, "diameter", raw.get("width", 0))
        item["drill_nm"] = _dimension_nm(raw, "drill")
    elif kind == "pad":
        at = (_named_point(raw, "at") or _named_point(raw, "position") or
              _named_point(raw, "center"))
        if at is not None:
            item["at_nm"] = list(at)
        item["terminal"] = _terminal(raw)
        drill = _dimension_nm(raw, "drill")
        item["drill_nm"] = drill
        item["through_hole"] = bool(raw.get("through_hole") or drill > 0)
        size = raw.get("size_nm") if "size_nm" in raw else raw.get("size")
        if size is not None:
            item["size_nm"] = list(_point_nm(
                size, "nm" if "size_nm" in raw else str(raw.get("unit") or "mm")))
        connected_layers = (raw.get("connected_layers") or
                            raw.get("attached_layers") or
                            raw.get("copper_layers") or [])
        if isinstance(connected_layers, str):
            connected_layers = [connected_layers]
        item["connected_layers"] = sorted({str(layer) for layer in connected_layers})
    elif kind == "zone":
        item["components"] = _zone_components(raw, layers)
    else:
        # Unknown copper kinds remain comparable, but only declared semantic
        # fields survive. This keeps a future pcbnew primitive fail-visible
        # without allowing UUID/source-text churn into the signature.
        semantic = {}
        for key, value in sorted(raw.items(), key=lambda pair: str(pair[0])):
            normalized_key = str(key).lower()
            if normalized_key in _VOLATILE_KEYS or normalized_key in {
                    "kind", "type", "net", "net_name", "netname",
                    "layer", "layers", "owner"}:
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                semantic[str(key)] = value
        item["semantic"] = semantic
    return item


def _track_line_key(item: Mapping[str, Any]) -> tuple[Any, ...] | None:
    """Return an exact integer line/style identity for a straight track.

    Router and KiCad save passes are free to split one straight segment into
    several collinear primitives.  That serialization choice is not a copper
    mutation, so inventories compare the covered interval on a line rather
    than the number of segment objects.  Width, net and layer remain semantic.
    """
    if item.get("kind") != "track":
        return None
    start = item.get("start_nm") or []
    end = item.get("end_nm") or []
    if len(start) != 2 or len(end) != 2:
        return None
    dx = int(end[0]) - int(start[0])
    dy = int(end[1]) - int(start[1])
    divisor = math.gcd(abs(dx), abs(dy))
    if divisor == 0:
        return None
    ux, uy = dx // divisor, dy // divisor
    if ux < 0 or (ux == 0 and uy < 0):
        ux, uy = -ux, -uy
    # Cross(direction, point) identifies the infinite integer line.
    offset = ux * int(start[1]) - uy * int(start[0])
    return (str(item.get("net") or ""),
            tuple(str(layer) for layer in item.get("layers") or []),
            int(item.get("width_nm") or 0), ux, uy, offset)


def _track_interval(item: Mapping[str, Any], key: tuple[Any, ...]) \
        -> tuple[int, int, tuple[int, int], tuple[int, int]]:
    ux, uy = int(key[3]), int(key[4])
    left = (int(item["start_nm"][0]), int(item["start_nm"][1]))
    right = (int(item["end_nm"][0]), int(item["end_nm"][1]))
    left_t = ux * left[0] + uy * left[1]
    right_t = ux * right[0] + uy * right[1]
    if right_t < left_t:
        left_t, right_t, left, right = right_t, left_t, right, left
    return left_t, right_t, left, right


def _normalize_collinear_tracks(items: Iterable[dict[str, Any]]) \
        -> list[dict[str, Any]]:
    """Merge touching/overlapping collinear track intervals exactly.

    Gaps are never bridged.  Consequently a one-to-two split is equivalent,
    while deleting either half shortens the canonical interval and remains a
    visible failure.
    """
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    passthrough: list[dict[str, Any]] = []
    for item in items:
        key = _track_line_key(item)
        if key is None:
            passthrough.append(item)
        else:
            groups[key].append(item)

    normalized = list(passthrough)
    for key, tracks in groups.items():
        intervals = sorted((_track_interval(item, key) for item in tracks),
                           key=lambda row: (row[0], row[1], row[2], row[3]))
        current_start_t, current_end_t, current_start, current_end = intervals[0]
        merged: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for start_t, end_t, start, end in intervals[1:]:
            if start_t <= current_end_t:
                if end_t > current_end_t:
                    current_end_t, current_end = end_t, end
                continue
            merged.append((current_start, current_end))
            current_start_t, current_end_t = start_t, end_t
            current_start, current_end = start, end
        merged.append((current_start, current_end))
        for start, end in merged:
            if end < start:
                start, end = end, start
            normalized.append({
                "kind": "track", "net": key[0], "layers": list(key[1]),
                "start_nm": list(start), "end_nm": list(end),
                "width_nm": key[2],
            })
    return sorted(normalized, key=_json_key)


def _extract_synthetic_items(source: Any) -> list[Mapping[str, Any]]:
    if isinstance(source, Mapping):
        if source.get("kind") == "semantic-copper-inventory-v1" \
                and isinstance(source.get("items"), list):
            return list(source["items"])
        for key in ("items", "copper"):
            raw = source.get(key)
            if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
                return [value for value in raw if isinstance(value, Mapping)]
        result: list[Mapping[str, Any]] = []
        for key, kind in (("tracks", "track"), ("arcs", "arc"),
                          ("vias", "via"), ("pads", "pad"),
                          ("endpoints", "pad"), ("zones", "zone")):
            raw = source.get(key) or []
            if isinstance(raw, Mapping):
                raw = list(raw.values())
            if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
                continue
            for value in raw:
                if isinstance(value, Mapping):
                    result.append({"kind": kind, **value})
        if result:
            return result
        if "kind" in source or "type" in source:
            return [source]
        return []
    if isinstance(source, Sequence) and not isinstance(source, (str, bytes)):
        return [value for value in source if isinstance(value, Mapping)]
    raise TypeError("synthetic copper source must be a mapping or item sequence")


def _pcbnew_items(source: Any) -> list[dict[str, Any]]:
    """Read a saved/live pcbnew board without importing pcbnew at module load."""
    if isinstance(source, (str, Path)):
        board_path = Path(source)
        if not board_path.is_file():
            raise ValueError(f"board path is missing: {board_path}")
        # pcbnew's parser emits GUI assertions (and some releases can block on
        # them) before raising for arbitrary text.  Refuse an obviously
        # non-board fixture before importing the SWIG runtime.
        with board_path.open("rb") as stream:
            header = stream.read(64 * 1024)
        if b"(kicad_pcb" not in header:
            raise ValueError(f"not a KiCad PCB file: {board_path}")
    try:
        import pcbnew  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on host KiCad
        raise RuntimeError("pcbnew is required to inspect a board path/object") from exc

    board = pcbnew.LoadBoard(str(source)) if isinstance(source, (str, Path)) else source
    result: list[dict[str, Any]] = []

    def point(value: Any) -> list[int]:
        return [int(value.x), int(value.y)]

    def layer_name(layer: Any) -> str:
        return str(board.GetLayerName(int(layer)))

    for track in board.GetTracks():
        net = str(track.GetNetname())
        if isinstance(track, pcbnew.PCB_VIA):
            try:
                layer_ids = list(track.GetLayerSet().Seq())
                layers = [layer_name(layer) for layer in layer_ids]
            except Exception:
                layer_ids = [track.TopLayer(), track.BottomLayer()]
                layers = [layer_name(layer) for layer in layer_ids]
            # KiCad 10 warns on the old no-argument PCB_VIA.GetWidth() and
            # may route it through a GUI property accessor.  Diameter is a
            # layer-aware property; query one realized span layer explicitly.
            diameter_layer = layer_ids[0] if layer_ids else track.TopLayer()
            try:
                diameter = track.GetWidth(diameter_layer)
            except TypeError:  # KiCad 7 exposes only the no-argument overload.
                diameter = track.GetWidth()
            result.append({"kind": "via", "net": net, "layers": layers,
                           "at_nm": point(track.GetPosition()),
                           "diameter_nm": int(diameter),
                           "drill_nm": int(track.GetDrillValue())})
        elif hasattr(pcbnew, "PCB_ARC") and isinstance(track, pcbnew.PCB_ARC):
            try:
                middle = track.GetMid()
            except AttributeError:  # pragma: no cover - KiCad API generation
                middle = track.GetCenter()
            result.append({"kind": "arc", "net": net,
                           "layer": layer_name(track.GetLayer()),
                           "start_nm": point(track.GetStart()),
                           "mid_nm": point(middle),
                           "end_nm": point(track.GetEnd()),
                           "width_nm": int(track.GetWidth()), "unit": "nm"})
        else:
            result.append({"kind": "track", "net": net,
                           "layer": layer_name(track.GetLayer()),
                           "start_nm": point(track.GetStart()),
                           "end_nm": point(track.GetEnd()),
                           "width_nm": int(track.GetWidth())})
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            layers = [layer_name(layer) for layer in pad.GetLayerSet().Seq()
                      if str(board.GetLayerName(int(layer))).endswith(".Cu")]
            size = pad.GetSize()
            drill = pad.GetDrillSize()
            result.append({
                "kind": "pad", "net": str(pad.GetNetname()), "layers": layers,
                "at_nm": point(pad.GetPosition()),
                "terminal": f"{footprint.GetReference()}.{pad.GetNumber()}",
                "size_nm": [int(size.x), int(size.y)],
                "drill_nm": max(int(drill.x), int(drill.y)),
                "through_hole": max(int(drill.x), int(drill.y)) > 0,
            })
    for zone in board.Zones():
        layers = [layer_name(layer) for layer in zone.GetLayerSet().Seq()]
        components = []
        for layer in zone.GetLayerSet().Seq():
            try:
                polyset = zone.GetFilledPolysList(int(layer))
                outlines = []
                for index in range(polyset.OutlineCount()):
                    chain = polyset.COutline(index)
                    outlines.append([[int(chain.CPoint(point_index).x),
                                      int(chain.CPoint(point_index).y)]
                                     for point_index in range(chain.PointCount())])
                for outline in outlines:
                    components.append({"layer": layer_name(layer),
                                       "polygon_nm": outline, "unit": "nm"})
            except Exception:
                # KiCad's filled-poly SWIG surface differs by major version.
                # An empty component list is explicit incomplete evidence to
                # filled_zone_components(), never a serialized-zone fallback.
                continue
        result.append({"kind": "zone", "net": str(zone.GetNetname()),
                       "layers": layers, "components": components,
                       "unit": "nm"})
    return result


def _copper_inventory(source: Any, *, normalize_tracks: bool) -> dict[str, Any]:
    if isinstance(source, (str, Path)) or (not isinstance(source, (Mapping, Sequence))
                                          and hasattr(source, "GetTracks")):
        raw_items = _pcbnew_items(source)
    else:
        raw_items = _extract_synthetic_items(source)
    canonical_items = [_canonical_item(value) for value in raw_items]
    items = (_normalize_collinear_tracks(canonical_items) if normalize_tracks
             else sorted(canonical_items, key=_json_key))
    by_net: dict[str, dict[str, Any]] = {}
    kinds = Counter()
    for item in items:
        kinds[item["kind"]] += 1
        row = by_net.setdefault(item["net"], {"count": 0, "kinds": {}})
        row["count"] += 1
        row["kinds"][item["kind"]] = row["kinds"].get(item["kind"], 0) + 1
    payload = {"schema": SCHEMA, "kind": "semantic-copper-inventory-v1",
               "items": items}
    return {
        **payload,
        "signature": _digest(payload),
        "counts": {"total": len(items),
                   "by_kind": dict(sorted(kinds.items()))},
        "nets": dict(sorted(by_net.items())),
    }


def canonical_copper_inventory(source: Any) -> dict[str, Any]:
    """Return a sorted semantic copper inventory with a content signature.

    ``source`` may be a synthetic mapping/sequence, an already canonical
    inventory, a pcbnew board object, or a ``.kicad_pcb`` path.  Straight
    collinear segments are normalized by covered interval so serialization
    splits do not appear as mutations.  Topology checks retain a private raw
    primitive inventory because a split point can also be a branch endpoint.
    """
    return _copper_inventory(source, normalize_tracks=True)


def _touched_nets(touched: Any) -> tuple[set[str] | None, str | None]:
    if touched is None:
        return None, None
    actor = None
    raw = touched
    if isinstance(touched, Mapping):
        actor = str(touched.get("actor") or touched.get("owner") or
                    touched.get("wave") or "").strip() or None
        raw = touched.get("nets", touched.get("net_names", []))
    if isinstance(raw, Mapping):
        nets = {str(net).strip() for net in raw if str(net).strip()}
    elif isinstance(raw, str):
        nets = {raw.strip()} if raw.strip() else set()
    elif isinstance(raw, Iterable):
        nets = {str(net).strip() for net in raw if str(net).strip()}
    else:
        raise ValueError("touched nets must be a mapping, string, or sequence")
    return nets, actor


def _ownership_map(ownership: Any) -> dict[str, set[str]] | None:
    if ownership is None:
        return None
    raw = ownership
    if isinstance(raw, Mapping) and "nets" in raw:
        raw = raw["nets"]
    result: dict[str, set[str]] = defaultdict(set)
    if isinstance(raw, Mapping):
        for net, value in raw.items():
            if isinstance(value, Mapping):
                value = value.get("owners", value.get("owner", []))
            values = [value] if isinstance(value, str) else value or []
            for owner in values:
                if str(owner).strip():
                    result[str(net).strip()].add(str(owner).strip())
    elif isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for row in raw:
            if not isinstance(row, Mapping):
                continue
            nets = row.get("nets", row.get("net", []))
            owners = row.get("owners", row.get("owner", []))
            nets = [nets] if isinstance(nets, str) else nets or []
            owners = [owners] if isinstance(owners, str) else owners or []
            for net in nets:
                result[str(net).strip()].update(
                    str(owner).strip() for owner in owners if str(owner).strip())
    else:
        raise ValueError("ownership must be a net mapping or ownership rows")
    return dict(result)


def diff_copper(before: Any, after: Any, *, touched: Any = None,
                ownership: Any = None, actor: str | None = None) -> dict[str, Any]:
    """Return a multiset semantic delta and optional mutation-scope findings.

    A changed net outside ``touched`` is ``UNDECLARED_MUTATION``.  When an
    ownership authority is supplied, a changed net without an owner (or not
    owned by ``actor``) is ``UNOWNED_MUTATION``.  With no scope/authority those
    dimensions are reported N-A rather than guessed.
    """
    left = canonical_copper_inventory(before)
    right = canonical_copper_inventory(after)
    left_map = {_json_key(item): item for item in left["items"]}
    right_map = {_json_key(item): item for item in right["items"]}
    left_count = Counter(_json_key(item) for item in left["items"])
    right_count = Counter(_json_key(item) for item in right["items"])
    added = [right_map[key] for key in sorted(right_count)
             for _ in range(max(0, right_count[key] - left_count[key]))]
    removed = [left_map[key] for key in sorted(left_count)
               for _ in range(max(0, left_count[key] - right_count[key]))]
    changed_nets = sorted({item["net"] for item in added + removed})

    declared_nets, touched_actor = _touched_nets(touched)
    actor = str(actor or touched_actor or "").strip() or None
    owners = _ownership_map(ownership)
    findings: list[dict[str, Any]] = []
    for net in changed_nets:
        if declared_nets is not None and net not in declared_nets:
            findings.append({"type": "UNDECLARED_MUTATION", "net": net,
                             "detail": "changed net is outside touched semantics"})
        if owners is not None:
            allowed = owners.get(net, set())
            if not allowed or (actor is not None and actor not in allowed):
                findings.append({
                    "type": "UNOWNED_MUTATION", "net": net,
                    "actor": actor, "declared_owners": sorted(allowed),
                    "detail": ("net has no declared owner" if not allowed else
                               "transaction actor does not own changed net"),
                })
    per_net = {}
    for net in changed_nets:
        per_net[net] = {
            "added": sum(item["net"] == net for item in added),
            "removed": sum(item["net"] == net for item in removed),
        }
    undeclared = sum(row["type"] == "UNDECLARED_MUTATION" for row in findings)
    unowned = sum(row["type"] == "UNOWNED_MUTATION" for row in findings)
    return {
        "schema": SCHEMA, "kind": "semantic-copper-delta-v1",
        "status": "FAIL" if findings else "PASS",
        "before_signature": left["signature"],
        "after_signature": right["signature"],
        "changed": bool(added or removed), "changed_nets": changed_nets,
        "added": added, "removed": removed, "per_net": per_net,
        "counts": {"added": len(added), "removed": len(removed),
                   "changed_nets": len(changed_nets),
                   "undeclared_mutations": undeclared,
                   "unowned_mutations": unowned},
        "scope_graded": declared_nets is not None,
        "ownership_graded": owners is not None,
        "findings": findings,
    }


def source_owned_copper_equivalence(
        source: Any, candidate: Any,
        *, kinds: Iterable[str] = ("track", "arc", "via")) -> dict[str, Any]:
    """Prove that every source-owned copper primitive survives in candidate.

    Candidate additions are deliberately allowed: that is the router's job.
    Source tracks use the same normalized collinear interval representation as
    :func:`diff_copper`, so a serialization split is equivalent but any
    shortened interval is reported missing.  This helper is pure policy and
    remains separate from promotion authority during shadow rollout.
    """
    selected = {str(kind).strip().lower() for kind in kinds
                if str(kind).strip()}
    before = canonical_copper_inventory(source)
    after = canonical_copper_inventory(candidate)
    source_items = [item for item in before["items"]
                    if item.get("kind") in selected]
    candidate_items = [item for item in after["items"]
                       if item.get("kind") in selected]

    candidate_exact = Counter(
        _json_key(item) for item in candidate_items if item.get("kind") != "track")
    candidate_tracks: dict[tuple[Any, ...], list[tuple[int, int]]] = defaultdict(list)
    for item in candidate_items:
        key = _track_line_key(item)
        if key is not None:
            low, high, _start, _end = _track_interval(item, key)
            candidate_tracks[key].append((low, high))

    missing: list[dict[str, Any]] = []
    retained = 0
    for item in source_items:
        key = _track_line_key(item)
        if key is not None:
            low, high, _start, _end = _track_interval(item, key)
            present = any(candidate_low <= low and candidate_high >= high
                          for candidate_low, candidate_high
                          in candidate_tracks.get(key, []))
        else:
            encoded = _json_key(item)
            present = candidate_exact[encoded] > 0
            if present:
                candidate_exact[encoded] -= 1
        if present:
            retained += 1
        else:
            missing.append(item)
    status = "N-A" if not source_items else "FAIL" if missing else "PASS"
    payload = {
        "schema": SCHEMA, "kind": "source-owned-copper-equivalence-v1",
        "status": status, "source_signature": before["signature"],
        "candidate_signature": after["signature"],
        "selected_kinds": sorted(selected), "missing": missing,
        "counts": {"source": len(source_items), "retained": retained,
                   "missing": len(missing)},
        "findings": [{"type": "SOURCE_COPPER_MISSING", "item": item}
                     for item in missing],
    }
    return {**payload, "signature": _digest(payload)}


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[Any, Any] = {}

    def add(self, value: Any) -> None:
        self.parent.setdefault(value, value)

    def find(self, value: Any) -> Any:
        self.add(value)
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: Any, right: Any) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[max(a, b, key=repr)] = min(a, b, key=repr)


def _point_in_ring(point: tuple[int, int], ring: Sequence[Sequence[int]]) -> bool:
    if len(ring) < 3:
        return False
    x, y = point
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = int(previous[0]), int(previous[1])
        x2, y2 = int(current[0]), int(current[1])
        cross = (y1 > y) != (y2 > y)
        if cross and x <= (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
        previous = current
    return inside


def _direct_connectivity(source: Any) -> Mapping[str, Any] | None:
    if not isinstance(source, Mapping):
        return None
    raw = source.get("connectivity") or source.get("net_components")
    if isinstance(raw, Mapping):
        return raw
    nets = source.get("nets")
    if isinstance(nets, Mapping) and any(
            isinstance(value, Mapping) and "components" in value
            for value in nets.values()):
        return nets
    collection_keys = {"items", "copper", "tracks", "arcs", "vias", "pads",
                       "endpoints", "zones", "schema", "kind", "counts"}
    if source and not collection_keys.intersection(source) and all(
            isinstance(value, (Mapping, Sequence)) and
            not isinstance(value, (str, bytes)) for value in source.values()):
        return source
    return None


def _member_name(value: Any) -> str:
    if isinstance(value, Mapping):
        return str(value.get("terminal") or value.get("endpoint") or
                   value.get("name") or _json_key(value)).strip()
    return str(value).strip()


def _normalize_direct_components(value: Any) -> list[list[str]]:
    if isinstance(value, Mapping):
        value = value.get("components", [])
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("connectivity components must be a sequence")
    result = []
    for component in value:
        if isinstance(component, Mapping):
            component = (component.get("terminals") or component.get("members")
                         or component.get("pads") or component.get("endpoints")
                         or component.get("nodes") or [])
        if isinstance(component, str):
            component = [component]
        if not isinstance(component, Sequence):
            raise ValueError("connectivity component must contain members")
        members = sorted({_member_name(member) for member in component
                          if _member_name(member)})
        if members:
            result.append(members)
    return sorted(result, key=_json_key)


def _graph_components(inventory: Mapping[str, Any]) -> dict[str, list[list[str]]]:
    items_by_net: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in inventory.get("items", []):
        if item.get("net"):
            items_by_net[str(item["net"])].append(item)
    result: dict[str, list[list[str]]] = {}
    for net, items in items_by_net.items():
        uf = _UnionFind()
        terminals: dict[str, list[Any]] = defaultdict(list)
        geometric_nodes: set[tuple[int, int, str]] = set()
        zone_nodes: list[tuple[Any, list[str], list[list[list[int]]]]] = []
        for index, item in enumerate(items):
            kind = item["kind"]
            layers = item.get("layers") or []
            if kind in {"track", "arc"}:
                for layer in layers:
                    start = (int(item["start_nm"][0]), int(item["start_nm"][1]), layer)
                    end = (int(item["end_nm"][0]), int(item["end_nm"][1]), layer)
                    geometric_nodes.update((start, end))
                    uf.union(start, end)
            elif kind == "via":
                nodes = [(int(item["at_nm"][0]), int(item["at_nm"][1]), layer)
                         for layer in layers]
                geometric_nodes.update(nodes)
                for node in nodes[1:]:
                    uf.union(nodes[0], node)
            elif kind == "pad" and item.get("at_nm"):
                nodes = [(int(item["at_nm"][0]), int(item["at_nm"][1]), layer)
                         for layer in layers]
                geometric_nodes.update(nodes)
                if item.get("through_hole"):
                    for node in nodes[1:]:
                        uf.union(nodes[0], node)
                terminal = str(item.get("terminal") or "")
                if terminal:
                    terminals[terminal].extend(nodes)
            elif kind == "zone":
                for component_index, component in enumerate(item.get("components") or []):
                    virtual = ("zone", index, component_index)
                    uf.add(virtual)
                    zone_nodes.append((virtual, component.get("layers") or layers,
                                       component.get("polygons_nm") or []))
                    for terminal in component.get("terminals") or []:
                        terminals[str(terminal)].append(virtual)
        for virtual, layers, polygons in zone_nodes:
            for x, y, layer in geometric_nodes:
                if layer in layers and any(_point_in_ring((x, y), ring)
                                           for ring in polygons):
                    uf.union(virtual, (x, y, layer))
        # A terminal may have multiple legal copper-layer nodes (PTH). Tie
        # those only when the pad itself is plated, already done above.
        groups: dict[Any, set[str]] = defaultdict(set)
        for terminal, nodes in terminals.items():
            for node in nodes:
                groups[uf.find(node)].add(terminal)
        partitions = sorted((sorted(values) for values in groups.values() if values),
                            key=_json_key)
        result[net] = partitions
    return result


def connectivity_signature(source: Any, requested_nets: Iterable[str] | None = None) -> dict[str, Any]:
    """Return terminal connectivity partitions, not geometry/UUID identity."""
    direct = _direct_connectivity(source)
    evidence_complete = True
    if direct is not None:
        components = {str(net): _normalize_direct_components(value)
                      for net, value in direct.items()}
    else:
        inventory = _copper_inventory(source, normalize_tracks=False)
        components = _graph_components(inventory)
    requested = sorted({str(net) for net in (requested_nets or [])})
    rows = {}
    for net, partitions in sorted(components.items()):
        terminal_count = len({member for group in partitions for member in group})
        rows[net] = {
            "components": partitions, "component_count": len(partitions),
            "terminal_count": terminal_count,
            "open_count": max(0, len(partitions) - 1),
        }
    missing_requested = sorted(net for net in requested if net not in rows)
    if missing_requested:
        evidence_complete = False
    payload = {"schema": SCHEMA, "kind": "connectivity-signature-v1",
               "nets": rows}
    return {
        **payload, "signature": _digest(payload), "requested_nets": requested,
        "requested_open_count": sum(rows.get(net, {}).get("open_count", 0)
                                    for net in requested),
        "total_open_count": sum(row["open_count"] for row in rows.values()),
        "missing_requested_nets": missing_requested,
        "evidence_complete": evidence_complete,
    }


def _as_connectivity(value: Any, requested: Iterable[str]) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("kind") == "connectivity-signature-v1":
        return dict(value)
    return connectivity_signature(value, requested)


def requested_net_regressions(before: Any, after: Any,
                              requested_nets: Iterable[str]) -> dict[str, Any]:
    """Reject only requested-net connectivity regressions.

    Existing unrelated opens, and an invariant pre-existing requested open,
    are not regressions.  Lost endpoints and formerly-connected endpoint pairs
    are detected even when a raw component count happens to remain constant.
    """
    requested = sorted({str(net) for net in requested_nets})
    left = _as_connectivity(before, requested)
    right = _as_connectivity(after, requested)
    findings = []
    incomplete = []
    for net in requested:
        old = (left.get("nets") or {}).get(net)
        new = (right.get("nets") or {}).get(net)
        if old is None:
            incomplete.append(net)
            continue
        if new is None:
            findings.append({"type": "REQUESTED_NET_MISSING", "net": net})
            continue
        old_components = [set(group) for group in old.get("components") or []]
        new_components = [set(group) for group in new.get("components") or []]
        old_terminals = set().union(*old_components) if old_components else set()
        new_terminals = set().union(*new_components) if new_components else set()
        lost = sorted(old_terminals - new_terminals)
        if lost:
            findings.append({"type": "REQUESTED_ENDPOINT_LOST", "net": net,
                             "endpoints": lost})
        separated = set()
        for component in old_components:
            members = sorted(component & new_terminals)
            for index, first in enumerate(members):
                for second in members[index + 1:]:
                    if not any({first, second} <= group for group in new_components):
                        separated.add((first, second))
        if separated:
            findings.append({"type": "REQUESTED_CONNECTIVITY_REGRESSION",
                             "net": net,
                             "separated_pairs": [list(pair) for pair in sorted(separated)]})
        old_open = int(old.get("open_count", max(0, len(old_components) - 1)))
        new_open = int(new.get("open_count", max(0, len(new_components) - 1)))
        if new_open > old_open:
            findings.append({"type": "REQUESTED_OPENS_INCREASED", "net": net,
                             "before": old_open, "after": new_open})
    status = "INCOMPLETE" if incomplete else "FAIL" if findings else "PASS"
    return {
        "schema": SCHEMA, "kind": "requested-net-regression-v1",
        "status": status, "requested_nets": requested,
        "before_signature": left.get("signature"),
        "after_signature": right.get("signature"),
        "counts": {"requested_nets": len(requested),
                   "regressions": len(findings),
                   "incomplete": len(incomplete),
                   "requested_opens_before": sum(
                       int((left.get("nets") or {}).get(net, {}).get("open_count", 0))
                       for net in requested),
                   "requested_opens_after": sum(
                       int((right.get("nets") or {}).get(net, {}).get("open_count", 0))
                       for net in requested)},
        "incomplete_nets": incomplete, "findings": findings,
    }


def endpoint_layer_closure(source: Any, *, nets: Iterable[str] | None = None,
                           endpoints: Sequence[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Prove each requested pad endpoint is reached on a legal copper layer."""
    inventory = _copper_inventory(source, normalize_tracks=False)
    items = list(inventory["items"])
    if endpoints is not None:
        items.extend(_canonical_item({"kind": "pad", **row}) for row in endpoints)
    requested = (sorted({str(net) for net in nets}) if nets is not None else
                 sorted({str(item["net"]) for item in items
                         if item["kind"] == "pad" and item.get("net")}))
    rows = []
    failures = []
    incomplete = []
    for net in requested:
        pads = [item for item in items if item["kind"] == "pad" and item["net"] == net]
        if not pads:
            incomplete.append(net)
            continue
        conductors = [item for item in items
                      if item["net"] == net and item["kind"] != "pad"]
        for pad in pads:
            expected = set(pad.get("layers") or [])
            observed = set(pad.get("connected_layers") or [])
            at = pad.get("at_nm")
            if at is not None:
                point = (int(at[0]), int(at[1]))
                for item in conductors:
                    if item["kind"] in {"track", "arc"}:
                        if point in {(int(item["start_nm"][0]), int(item["start_nm"][1])),
                                     (int(item["end_nm"][0]), int(item["end_nm"][1]))}:
                            observed.update(item.get("layers") or [])
                    elif item["kind"] == "via" and point == tuple(item["at_nm"]):
                        observed.update(item.get("layers") or [])
                    elif item["kind"] == "zone":
                        for component in item.get("components") or []:
                            if any(_point_in_ring(point, ring)
                                   for ring in component.get("polygons_nm") or []):
                                observed.update(component.get("layers") or [])
            legal = sorted(expected & observed)
            row = {"net": net, "endpoint": pad.get("terminal") or "<unnamed>",
                   "expected_layers": sorted(expected),
                   "observed_layers": sorted(observed), "legal_layers": legal,
                   "through_hole": bool(pad.get("through_hole"))}
            rows.append(row)
            if not expected:
                failures.append({"type": "ENDPOINT_LAYER_UNKNOWN", **row})
            elif not legal:
                failures.append({"type": "ENDPOINT_WRONG_LAYER", **row})
    status = "INCOMPLETE" if incomplete else "FAIL" if failures else "PASS"
    return {
        "schema": SCHEMA, "kind": "endpoint-layer-closure-v1",
        "status": status, "requested_nets": requested, "endpoints": rows,
        "counts": {"requested_nets": len(requested), "endpoints": len(rows),
                   "failures": len(failures), "incomplete": len(incomplete)},
        "incomplete_nets": incomplete, "findings": failures,
    }


def _orientation(a: Sequence[int], b: Sequence[int], c: Sequence[int]) -> int:
    value = (int(b[1]) - int(a[1])) * (int(c[0]) - int(b[0])) - \
            (int(b[0]) - int(a[0])) * (int(c[1]) - int(b[1]))
    return 0 if value == 0 else 1 if value > 0 else 2


def _on_segment(a: Sequence[int], b: Sequence[int], c: Sequence[int]) -> bool:
    return (min(int(a[0]), int(c[0])) <= int(b[0]) <= max(int(a[0]), int(c[0]))
            and min(int(a[1]), int(c[1])) <= int(b[1]) <= max(int(a[1]), int(c[1])))


def _segments_touch(a: Sequence[int], b: Sequence[int],
                    c: Sequence[int], d: Sequence[int]) -> bool:
    o1, o2 = _orientation(a, b, c), _orientation(a, b, d)
    o3, o4 = _orientation(c, d, a), _orientation(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return ((o1 == 0 and _on_segment(a, c, b)) or
            (o2 == 0 and _on_segment(a, d, b)) or
            (o3 == 0 and _on_segment(c, a, d)) or
            (o4 == 0 and _on_segment(c, b, d)))


def _rings_touch(left: Sequence[Sequence[int]],
                 right: Sequence[Sequence[int]]) -> bool:
    if not left or not right:
        return False
    if _point_in_ring((int(left[0][0]), int(left[0][1])), right) or \
            _point_in_ring((int(right[0][0]), int(right[0][1])), left):
        return True
    for index, a in enumerate(left):
        b = left[(index + 1) % len(left)]
        for other_index, c in enumerate(right):
            d = right[(other_index + 1) % len(right)]
            if _segments_touch(a, b, c, d):
                return True
    return False


def _components_touch(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if not set(left.get("layers") or []) & set(right.get("layers") or []):
        return False
    if set(left.get("terminals") or []) & set(right.get("terminals") or []):
        return True
    return any(_rings_touch(a, b)
               for a in left.get("polygons_nm") or []
               for b in right.get("polygons_nm") or [])


def filled_zone_components(source: Any, nets: Iterable[str] | None = None) -> dict[str, Any]:
    """Return merged filled-zone components in semantic geometry form."""
    inventory = _copper_inventory(source, normalize_tracks=False)
    requested = set(str(net) for net in nets) if nets is not None else None
    raw_by_net: dict[str, list[dict[str, Any]]] = defaultdict(list)
    zones_seen: set[str] = set()
    for item in inventory["items"]:
        if item["kind"] != "zone" or not item.get("net"):
            continue
        net = str(item["net"])
        if requested is not None and net not in requested:
            continue
        zones_seen.add(net)
        raw_by_net[net].extend(item.get("components") or [])
    rows = {}
    incomplete = []
    target_nets = sorted(requested if requested is not None else zones_seen)
    for net in target_nets:
        components = raw_by_net.get(net, [])
        if net not in zones_seen:
            incomplete.append(net)
            rows[net] = {"components": [], "component_count": 0}
            continue
        if not components:
            incomplete.append(net)
            rows[net] = {"components": [], "component_count": 0}
            continue
        uf = _UnionFind()
        for index in range(len(components)):
            uf.add(index)
        for index, left in enumerate(components):
            for other_index in range(index + 1, len(components)):
                if _components_touch(left, components[other_index]):
                    uf.union(index, other_index)
        grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for index, component in enumerate(components):
            grouped[uf.find(index)].append(component)
        merged = []
        for group in grouped.values():
            merged.append({
                "layers": sorted({layer for component in group
                                  for layer in component.get("layers") or []}),
                "polygons_nm": sorted(
                    [ring for component in group
                     for ring in component.get("polygons_nm") or []], key=_json_key),
                "terminals": sorted({terminal for component in group
                                     for terminal in component.get("terminals") or []}),
            })
        merged.sort(key=_json_key)
        rows[net] = {"components": merged, "component_count": len(merged)}
    payload = {"schema": SCHEMA, "kind": "filled-zone-components-v1",
               "nets": rows}
    return {**payload, "signature": _digest(payload),
            "evidence_complete": not incomplete,
            "incomplete_nets": incomplete,
            "counts": {"nets": len(rows),
                       "components": sum(row["component_count"]
                                         for row in rows.values())}}


def _as_zone_components(value: Any, nets: Iterable[str] | None) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("kind") == "filled-zone-components-v1":
        return dict(value)
    return filled_zone_components(value, nets)


def power_graph_delta(before: Any, after: Any, *,
                      power_nets: Iterable[str] | None = None) -> dict[str, Any]:
    """Detect filled-zone splits/lost power connectivity without UUIDs."""
    requested = sorted({str(net) for net in power_nets}) if power_nets is not None else None
    left = _as_zone_components(before, requested)
    right = _as_zone_components(after, requested)
    nets = (requested if requested is not None else
            sorted(set((left.get("nets") or {})) | set((right.get("nets") or {}))))
    findings = []
    incomplete = []
    for net in nets:
        old = (left.get("nets") or {}).get(net)
        new = (right.get("nets") or {}).get(net)
        if old is None or new is None or net in left.get("incomplete_nets", []) \
                or net in right.get("incomplete_nets", []):
            incomplete.append(net)
            continue
        old_components = old.get("components") or []
        new_components = new.get("components") or []
        if old_components and not new_components:
            findings.append({"type": "POWER_ZONE_LOST", "net": net,
                             "before": len(old_components), "after": 0})
        if len(new_components) > len(old_components):
            findings.append({"type": "POWER_ZONE_SPLIT", "net": net,
                             "before": len(old_components),
                             "after": len(new_components)})
        old_terminal_groups = [set(row.get("terminals") or [])
                               for row in old_components]
        new_terminal_groups = [set(row.get("terminals") or [])
                               for row in new_components]
        old_terminals = set().union(*old_terminal_groups) if old_terminal_groups else set()
        new_terminals = set().union(*new_terminal_groups) if new_terminal_groups else set()
        lost = sorted(old_terminals - new_terminals)
        if lost:
            findings.append({"type": "POWER_ENDPOINT_LOST", "net": net,
                             "endpoints": lost})
        separated = set()
        for group in old_terminal_groups:
            members = sorted(group & new_terminals)
            for index, first in enumerate(members):
                for second in members[index + 1:]:
                    if not any({first, second} <= candidate
                               for candidate in new_terminal_groups):
                        separated.add((first, second))
        if separated:
            findings.append({"type": "POWER_ENDPOINT_REGRESSION", "net": net,
                             "separated_pairs": [list(pair)
                                                 for pair in sorted(separated)]})
    status = "INCOMPLETE" if incomplete else "FAIL" if findings else "PASS"
    return {
        "schema": SCHEMA, "kind": "power-graph-delta-v1", "status": status,
        "power_nets": nets, "before_signature": left.get("signature"),
        "after_signature": right.get("signature"),
        "counts": {"power_nets": len(nets), "regressions": len(findings),
                   "splits": sum(row["type"] == "POWER_ZONE_SPLIT"
                                 for row in findings),
                   "incomplete": len(incomplete)},
        "incomplete_nets": incomplete, "findings": findings,
    }


__all__ = [
    "canonical_copper_inventory", "diff_copper", "connectivity_signature",
    "requested_net_regressions", "endpoint_layer_closure",
    "filled_zone_components", "power_graph_delta",
    "source_owned_copper_equivalence",
]
