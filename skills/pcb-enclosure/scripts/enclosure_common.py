#!/usr/bin/env python3
"""Shared strict schemas and geometry helpers for pcb-enclosure.

This module is intentionally dependency-light. PyYAML is used only for the
authored configuration; STL parsing and all verification arithmetic use the
standard library so the verifier remains runnable on a stock KiCad host.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("pcb-enclosure needs PyYAML") from exc


CONFIG_KIND = "pcb-enclosure-config-v1"
INTERFACE_KIND = "pcb-enclosure-interface-v1"
PHYSICAL_KIND = "pcb-enclosure-physical-evidence-v1"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
REF_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.+-]*$")


class EnclosureError(ValueError):
    """A represented enclosure input is invalid or contradictory."""


class StrictLoader(yaml.SafeLoader):
    """YAML loader that refuses duplicate mapping keys."""


def _construct_mapping(loader: StrictLoader, node: yaml.MappingNode,
                       deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise EnclosureError(
                f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictLoader)
    except (OSError, yaml.YAMLError) as exc:
        raise EnclosureError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EnclosureError(f"{path}: expected a YAML mapping")
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EnclosureError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EnclosureError(f"{path}: expected a JSON object")
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def semantic_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return sha256_bytes(payload)


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EnclosureError(f"{where}: expected mapping")
    return value


def _exact(value: Any, fields: Iterable[str], where: str) -> Mapping[str, Any]:
    item = _mapping(value, where)
    expected = set(fields)
    actual = set(item)
    if actual != expected:
        raise EnclosureError(
            f"{where}: fields differ; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}")
    return item


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise EnclosureError(f"{where}: expected non-empty string")
    return value


def _number(value: Any, where: str, *, positive: bool = False,
            nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EnclosureError(f"{where}: expected number")
    result = float(value)
    if not math.isfinite(result):
        raise EnclosureError(f"{where}: expected finite number")
    if positive and result <= 0:
        raise EnclosureError(f"{where}: expected > 0")
    if nonnegative and result < 0:
        raise EnclosureError(f"{where}: expected >= 0")
    return result


def _boolean(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise EnclosureError(f"{where}: expected boolean")
    return value


def _enum(value: Any, choices: Iterable[str], where: str) -> str:
    result = _string(value, where)
    allowed = set(choices)
    if result not in allowed:
        raise EnclosureError(f"{where}: expected one of {sorted(allowed)}")
    return result


def _vec(value: Any, count: int, where: str) -> list[float]:
    if not isinstance(value, list) or len(value) != count:
        raise EnclosureError(f"{where}: expected {count}-element list")
    return [_number(item, f"{where}[{index}]")
            for index, item in enumerate(value)]


def safe_relative_path(value: Any, root: Path, where: str) -> Path:
    text = _string(value, where)
    path = Path(text)
    if path.is_absolute() or "\\" in text or any(part in {"", ".", ".."}
                                                  for part in path.parts):
        raise EnclosureError(
            f"{where}: path must be normalized, relative, and traversal-free")
    base = root.resolve()
    unresolved = base / path
    # Resolving first would erase evidence that an otherwise in-root subject
    # was reached through a symlink.  Subject bindings are deliberately made
    # from ordinary files so a later link retarget cannot change what a config
    # means without changing the config itself.
    cursor = base
    for part in path.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise EnclosureError(f"{where}: symlink paths are not accepted")
    resolved = unresolved.resolve(strict=False)
    if not resolved.is_relative_to(base):
        raise EnclosureError(f"{where}: path escapes subject root")
    return resolved


def validate_file_binding(value: Any, root: Path, where: str,
                          *, require_exists: bool = True) -> dict[str, Any]:
    item = _exact(value, {"path", "sha256", "size"}, where)
    path = safe_relative_path(item["path"], root, f"{where}.path")
    expected_hash = _string(item["sha256"], f"{where}.sha256")
    if not HEX64_RE.fullmatch(expected_hash):
        raise EnclosureError(f"{where}.sha256: expected lowercase 64-hex")
    expected_size = item["size"]
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) \
            or expected_size <= 0:
        raise EnclosureError(f"{where}.size: expected positive integer")
    result = {
        "path": path,
        "expected_sha256": expected_hash,
        "expected_size": expected_size,
        "exists": path.is_file(),
    }
    if not path.is_file():
        if require_exists:
            raise EnclosureError(f"{where}: bound file is missing: {path}")
        return result
    result["actual_sha256"] = sha256_file(path)
    result["actual_size"] = path.stat().st_size
    result["matches"] = (
        result["actual_sha256"] == expected_hash and
        result["actual_size"] == expected_size)
    return result


def validate_interface(value: Mapping[str, Any]) -> dict[str, Any]:
    top = _exact(value, {"schema", "kind", "subject", "frame", "board",
                         "coverage"}, "interface")
    if top["schema"] != 1 or isinstance(top["schema"], bool):
        raise EnclosureError("interface.schema: only schema 1 is supported")
    if top["kind"] != INTERFACE_KIND:
        raise EnclosureError(f"interface.kind: expected {INTERFACE_KIND!r}")
    subject = _exact(top["subject"], {"board"}, "interface.subject")
    board_binding = _exact(subject["board"], {"name", "sha256", "size"},
                           "interface.subject.board")
    _string(board_binding["name"], "interface.subject.board.name")
    if not HEX64_RE.fullmatch(_string(
            board_binding["sha256"], "interface.subject.board.sha256")):
        raise EnclosureError("interface.subject.board.sha256: expected 64-hex")
    if isinstance(board_binding["size"], bool) or not isinstance(
            board_binding["size"], int) or board_binding["size"] <= 0:
        raise EnclosureError("interface.subject.board.size: expected positive int")

    frame = _exact(top["frame"], {"units", "origin", "board_to_case",
                                  "z_zero", "z_positive"}, "interface.frame")
    if frame["units"] != "mm" or frame["origin"] != "outline_bbox_center":
        raise EnclosureError("interface.frame: only centered millimetre frame supported")
    matrix = frame["board_to_case"]
    if not isinstance(matrix, list) or len(matrix) != 4:
        raise EnclosureError("interface.frame.board_to_case: expected 4x4 list")
    for index, row in enumerate(matrix):
        _vec(row, 4, f"interface.frame.board_to_case[{index}]")
    _enum(frame["z_zero"], {"pcb_back_surface"}, "interface.frame.z_zero")
    _enum(frame["z_positive"], {"front"}, "interface.frame.z_positive")

    board = _exact(top["board"], {"thickness_mm", "outline", "drills",
                                   "mounting_holes", "footprints",
                                   "access_candidates"}, "interface.board")
    _number(board["thickness_mm"], "interface.board.thickness_mm", positive=True)
    outline = _exact(board["outline"], {"contours_mm", "bbox_mm", "size_mm"},
                     "interface.board.outline")
    _vec(outline["bbox_mm"], 4, "interface.board.outline.bbox_mm")
    size = _vec(outline["size_mm"], 2, "interface.board.outline.size_mm")
    if min(size) <= 0:
        raise EnclosureError("interface.board.outline.size_mm: dimensions must be > 0")
    contours = outline["contours_mm"]
    if not isinstance(contours, list) or not contours:
        raise EnclosureError("interface.board.outline.contours_mm: no outline")
    for ci, contour in enumerate(contours):
        if not isinstance(contour, list) or len(contour) < 3:
            raise EnclosureError(f"interface outline contour {ci}: <3 points")
        for pi, point in enumerate(contour):
            _vec(point, 2, f"interface outline contour {ci} point {pi}")

    for field in ("drills", "mounting_holes", "footprints",
                  "access_candidates"):
        if not isinstance(board[field], list):
            raise EnclosureError(f"interface.board.{field}: expected list")
    refs = set()
    for index, footprint in enumerate(board["footprints"]):
        fp = _exact(footprint, {
            "ref", "value", "footprint", "position_mm", "rotation_deg",
            "side", "bbox_mm", "model_declared",
        }, f"interface.board.footprints[{index}]")
        ref = _string(fp["ref"], f"interface footprint {index}.ref")
        if ref in refs:
            raise EnclosureError(f"interface footprint duplicate ref {ref}")
        refs.add(ref)
        _string(fp["value"], f"interface footprint {ref}.value",
                nonempty=False)
        _string(fp["footprint"], f"interface footprint {ref}.footprint",
                nonempty=False)
        _vec(fp["position_mm"], 2,
             f"interface footprint {ref}.position_mm")
        _number(fp["rotation_deg"], f"interface footprint {ref}.rotation_deg")
        _enum(fp["side"], {"front", "back"},
              f"interface footprint {ref}.side")
        _vec(fp["bbox_mm"], 4, f"interface footprint {ref}.bbox_mm")
        _boolean(fp["model_declared"],
                 f"interface footprint {ref}.model_declared")
    for field in ("drills", "mounting_holes"):
        for index, raw in enumerate(board[field]):
            row = _exact(raw, {"ref", "pad", "position_mm", "drill_mm",
                               "attribute"},
                         f"interface.board.{field}[{index}]")
            ref = _string(row["ref"], f"interface {field}[{index}].ref")
            if ref not in refs:
                raise EnclosureError(f"interface {field} ref {ref}: footprint absent")
            _string(row["pad"], f"interface {field}[{index}].pad",
                    nonempty=False)
            _vec(row["position_mm"], 2,
                 f"interface {field}[{index}].position_mm")
            drill = _vec(row["drill_mm"], 2,
                         f"interface {field}[{index}].drill_mm")
            if max(drill) <= 0:
                raise EnclosureError(
                    f"interface {field}[{index}].drill_mm: zero drill")
            _enum(row["attribute"], {"NPTH", "PTH"},
                  f"interface {field}[{index}].attribute")
    access_refs = []
    for index, candidate in enumerate(board["access_candidates"]):
        row = _exact(candidate, {"ref", "position_mm", "value", "footprint",
                                 "selection"},
                     f"interface.board.access_candidates[{index}]")
        ref = _string(row["ref"], f"access candidate {index}.ref")
        if ref not in refs:
            raise EnclosureError(f"access candidate {ref}: footprint absent")
        if ref in access_refs:
            raise EnclosureError(f"access candidate duplicate ref {ref}")
        access_refs.append(ref)
        _vec(row["position_mm"], 2,
             f"interface access candidate {ref}.position_mm")
        _string(row["value"], f"interface access candidate {ref}.value",
                nonempty=False)
        _string(row["footprint"],
                f"interface access candidate {ref}.footprint", nonempty=False)
        _enum(row["selection"], {"required", "conservative-prefix"},
              f"interface access candidate {ref}.selection")

    coverage = _exact(top["coverage"], {"footprints", "drills",
                                        "mounting_holes", "access_candidates"},
                      "interface.coverage")
    measured = {
        "footprints": len(board["footprints"]),
        "drills": len(board["drills"]),
        "mounting_holes": len(board["mounting_holes"]),
        "access_candidates": len(board["access_candidates"]),
    }
    for key, count in measured.items():
        if coverage[key] != count:
            raise EnclosureError(
                f"interface.coverage.{key}: declared {coverage[key]}, actual {count}")
    if measured["footprints"] == 0 or measured["mounting_holes"] == 0:
        raise EnclosureError("interface: zero footprint or mounting-hole denominator")
    return dict(value)


def validate_config(value: Mapping[str, Any]) -> dict[str, Any]:
    top = _exact(value, {"schema", "kind", "name", "mode", "subject",
                         "process", "cad", "geometry", "fasteners",
                         "interfaces", "thermal", "physical_validation"},
                 "config")
    if top["schema"] != 1 or isinstance(top["schema"], bool):
        raise EnclosureError("config.schema: only schema 1 is supported")
    if top["kind"] != CONFIG_KIND:
        raise EnclosureError(f"config.kind: expected {CONFIG_KIND!r}")
    _string(top["name"], "config.name")
    _enum(top["mode"], {"co_design", "derived"}, "config.mode")

    subject = _mapping(top["subject"], "config.subject")
    required_subject = {"release", "pcb", "step", "interface"}
    optional_subject = {"release_manifest"}
    if not required_subject <= set(subject) or \
            set(subject) - required_subject - optional_subject:
        raise EnclosureError(
            "config.subject: fields differ; "
            f"missing={sorted(required_subject - set(subject))}, "
            f"unknown={sorted(set(subject) - required_subject - optional_subject)}")
    _string(subject["release"], "config.subject.release")
    bound_subjects = ["pcb", "step", "interface"]
    if "release_manifest" in subject:
        bound_subjects.append("release_manifest")
    for field in bound_subjects:
        binding = _exact(subject[field], {"path", "sha256", "size"},
                         f"config.subject.{field}")
        _string(binding["path"], f"config.subject.{field}.path")
        digest = _string(binding["sha256"], f"config.subject.{field}.sha256")
        if not HEX64_RE.fullmatch(digest):
            raise EnclosureError(f"config.subject.{field}.sha256: expected 64-hex")
        if isinstance(binding["size"], bool) or not isinstance(binding["size"], int) \
                or binding["size"] <= 0:
            raise EnclosureError(f"config.subject.{field}.size: expected positive int")

    process = _exact(top["process"], {"method", "material", "nozzle_mm",
                                      "layer_mm", "support_policy",
                                      "minimum_wall_mm"}, "config.process")
    _enum(process["method"], {"fdm"}, "config.process.method")
    _string(process["material"], "config.process.material")
    _number(process["nozzle_mm"], "config.process.nozzle_mm", positive=True)
    _number(process["layer_mm"], "config.process.layer_mm", positive=True)
    _enum(process["support_policy"], {"forbid", "forbid_when_practical",
                                       "allow_declared"},
          "config.process.support_policy")
    _number(process["minimum_wall_mm"], "config.process.minimum_wall_mm",
            positive=True)

    cad = _mapping(top["cad"], "config.cad")
    legacy_cad_fields = {"engine", "minimum_version", "printable_parts"}
    authored_cad_fields = legacy_cad_fields | {"source"}
    if frozenset(cad) not in {frozenset(legacy_cad_fields),
                              frozenset(authored_cad_fields)}:
        expected = authored_cad_fields if "source" in cad else legacy_cad_fields
        raise EnclosureError(
            "config.cad: fields differ; "
            f"missing={sorted(expected - set(cad))}, "
            f"unknown={sorted(set(cad) - expected)}")
    _enum(cad["engine"], {"openscad"}, "config.cad.engine")
    _string(cad["minimum_version"], "config.cad.minimum_version")
    if "source" in cad:
        source = _exact(cad["source"], {"kind", "path", "sha256", "size"},
                        "config.cad.source")
        _enum(source["kind"], {"authored_scad"}, "config.cad.source.kind")
        source_path = _string(source["path"], "config.cad.source.path")
        if Path(source_path).suffix.lower() != ".scad":
            raise EnclosureError("config.cad.source.path: expected a .scad file")
        digest = _string(source["sha256"], "config.cad.source.sha256")
        if not HEX64_RE.fullmatch(digest):
            raise EnclosureError(
                "config.cad.source.sha256: expected lowercase 64-hex")
        if isinstance(source["size"], bool) or not isinstance(source["size"], int) \
                or source["size"] <= 0:
            raise EnclosureError(
                "config.cad.source.size: expected positive integer")
    parts = cad["printable_parts"]
    if not isinstance(parts, list) or not parts or parts != list(dict.fromkeys(parts)):
        raise EnclosureError("config.cad.printable_parts: expected non-empty unique list")
    allowed_parts = {"base", "lid", "insert_coupon", "panel_north",
                     "panel_south", "panel_east", "panel_west"}
    for index, part in enumerate(parts):
        _enum(part, allowed_parts, f"config.cad.printable_parts[{index}]")

    geometry = _exact(top["geometry"], {
        "topology", "xy_clearance_mm", "wall_mm", "floor_mm", "roof_mm",
        "corner_radius_mm", "board_bottom_z_mm", "inside_top_z_mm",
        "seam_z_mm", "panel_thickness_mm", "panel_capture_mm",
        "panel_clearance_mm", "corner_post_mm", "lid_column_board_gap_mm",
    }, "config.geometry")
    topology = _enum(geometry["topology"], {"split_shell", "base_lid_panels"},
                     "config.geometry.topology")
    for field in ("xy_clearance_mm", "wall_mm", "floor_mm", "roof_mm",
                  "corner_radius_mm", "board_bottom_z_mm", "inside_top_z_mm",
                  "panel_thickness_mm", "panel_capture_mm", "corner_post_mm"):
        _number(geometry[field], f"config.geometry.{field}", positive=True)
    _number(geometry["seam_z_mm"], "config.geometry.seam_z_mm", positive=True)
    _number(geometry["panel_clearance_mm"],
            "config.geometry.panel_clearance_mm", nonnegative=True)
    _number(geometry["lid_column_board_gap_mm"],
            "config.geometry.lid_column_board_gap_mm", nonnegative=True)
    if geometry["inside_top_z_mm"] <= geometry["board_bottom_z_mm"]:
        raise EnclosureError("config.geometry: inside top must be above PCB bottom")
    if topology == "split_shell" and not (
            geometry["board_bottom_z_mm"] < geometry["seam_z_mm"] <
            geometry["inside_top_z_mm"]):
        raise EnclosureError("config.geometry.seam_z_mm: outside split-shell interior")
    minimum_wall = process["minimum_wall_mm"]
    wall_fields = ["wall_mm", "floor_mm", "roof_mm"]
    if topology == "base_lid_panels":
        wall_fields.append("panel_thickness_mm")
    too_thin = [field for field in wall_fields
                if geometry[field] + 1e-9 < minimum_wall]
    if too_thin:
        raise EnclosureError(
            "config.geometry: below process.minimum_wall_mm: " +
            ", ".join(too_thin))

    fasteners = _exact(top["fasteners"], {
        "strategy", "thread", "board_holes", "case_holes_mm", "boss_d_mm",
        "case_post_d_mm", "minimum_radial_wall_mm", "insert", "screw",
    }, "config.fasteners")
    strategy = _enum(fasteners["strategy"], {"shared_board", "separate_perimeter"},
                     "config.fasteners.strategy")
    _string(fasteners["thread"], "config.fasteners.thread")
    holes = fasteners["board_holes"]
    if not isinstance(holes, list) or not holes or holes != list(dict.fromkeys(holes)):
        raise EnclosureError("config.fasteners.board_holes: expected unique refs")
    for index, ref in enumerate(holes):
        if not REF_RE.fullmatch(_string(ref, f"config.fasteners.board_holes[{index}]")):
            raise EnclosureError(f"config.fasteners.board_holes[{index}]: bad ref")
    case_holes = fasteners["case_holes_mm"]
    if not isinstance(case_holes, list):
        raise EnclosureError("config.fasteners.case_holes_mm: expected list")
    for index, point in enumerate(case_holes):
        _vec(point, 2, f"config.fasteners.case_holes_mm[{index}]")
    if strategy == "shared_board" and case_holes:
        raise EnclosureError("shared_board fasteners cannot declare case holes")
    if strategy == "separate_perimeter" and len(case_holes) < 4:
        raise EnclosureError("separate_perimeter requires at least four case holes")
    for field in ("boss_d_mm", "case_post_d_mm", "minimum_radial_wall_mm"):
        _number(fasteners[field], f"config.fasteners.{field}", positive=True)

    insert = _exact(fasteners["insert"], {
        "family", "installation", "hole_d_mm", "body_d_mm", "flange_d_mm",
        "flange_recess_d_mm", "flange_recess_depth_mm", "length_mm",
        "bottom_clearance_mm",
    }, "config.fasteners.insert")
    _string(insert["family"], "config.fasteners.insert.family")
    _enum(insert["installation"], {"cold_press", "heat_set"},
          "config.fasteners.insert.installation")
    for field in ("hole_d_mm", "body_d_mm", "flange_d_mm",
                  "flange_recess_d_mm", "flange_recess_depth_mm", "length_mm"):
        _number(insert[field], f"config.fasteners.insert.{field}", positive=True)
    _number(insert["bottom_clearance_mm"],
            "config.fasteners.insert.bottom_clearance_mm", nonnegative=True)
    if insert["flange_recess_d_mm"] + 1e-9 < insert["flange_d_mm"]:
        raise EnclosureError(
            "config.fasteners.insert: flange recess is smaller than flange")
    if insert["flange_recess_depth_mm"] >= insert["length_mm"]:
        raise EnclosureError(
            "config.fasteners.insert: flange recess depth reaches past insert")
    if insert["installation"] == "cold_press" and \
            insert["hole_d_mm"] >= insert["body_d_mm"]:
        raise EnclosureError(
            "config.fasteners.insert: cold-press pilot lacks interference")

    screw = _exact(fasteners["screw"], {
        "clearance_d_mm", "head_d_mm", "head_recess_depth_mm",
        "board_length_mm", "lid_length_mm", "minimum_engagement_mm",
        "minimum_tip_clearance_mm",
    }, "config.fasteners.screw")
    for field in screw:
        _number(screw[field], f"config.fasteners.screw.{field}",
                positive=field != "minimum_tip_clearance_mm",
                nonnegative=field == "minimum_tip_clearance_mm")
    if screw["head_d_mm"] <= screw["clearance_d_mm"]:
        raise EnclosureError(
            "config.fasteners.screw: head diameter must exceed clearance bore")

    required_parts = {"base", "lid"}
    panel_parts = {"panel_north", "panel_south", "panel_east", "panel_west"}
    if not required_parts.issubset(parts):
        raise EnclosureError("config.cad.printable_parts: base and lid are required")
    if topology == "base_lid_panels" and not panel_parts.issubset(parts):
        raise EnclosureError(
            "config.cad.printable_parts: panel topology requires all four panels")
    if topology == "split_shell" and panel_parts.intersection(parts):
        raise EnclosureError(
            "config.cad.printable_parts: split shell cannot declare edge panels")

    interfaces = top["interfaces"]
    if not isinstance(interfaces, list) or not interfaces:
        raise EnclosureError("config.interfaces: expected non-empty list")
    seen_ids: set[str] = set()
    seen_refs: set[str] = set()
    for index, raw in enumerate(interfaces):
        row = _exact(raw, {"id", "ref", "role", "side", "disposition",
                           "center_mm", "shape", "opening_mm",
                           "plug_envelope_mm", "clearance_mm"},
                     f"config.interfaces[{index}]")
        ident = _string(row["id"], f"config.interfaces[{index}].id")
        ref = _string(row["ref"], f"config.interfaces[{index}].ref")
        if ident in seen_ids or ref in seen_refs:
            raise EnclosureError(f"config.interfaces[{index}]: duplicate id/ref")
        seen_ids.add(ident)
        seen_refs.add(ref)
        _string(row["role"], f"config.interfaces[{index}].role")
        side = _enum(row["side"], {"north", "south", "east", "west", "top"},
                     f"config.interfaces[{index}].side")
        disposition = _enum(row["disposition"], {
            "opening", "service_opening", "internal", "not_fitted"},
            f"config.interfaces[{index}].disposition")
        _vec(row["center_mm"], 3, f"config.interfaces[{index}].center_mm")
        shape = _enum(row["shape"], {"round", "rect", "arch", "none"},
                      f"config.interfaces[{index}].shape")
        opening = _vec(row["opening_mm"], 2,
                       f"config.interfaces[{index}].opening_mm")
        plug = _vec(row["plug_envelope_mm"], 3,
                    f"config.interfaces[{index}].plug_envelope_mm")
        clearance = _number(row["clearance_mm"],
                            f"config.interfaces[{index}].clearance_mm",
                            nonnegative=True)
        if disposition in {"opening", "service_opening"}:
            if shape == "none" or min(opening) <= 0:
                raise EnclosureError(f"config interface {ident}: opening lacks shape/size")
            if side == "top" and disposition == "opening":
                raise EnclosureError(f"config interface {ident}: top access is service_opening")
        elif shape != "none" or any(opening) or any(plug) or clearance:
            raise EnclosureError(
                f"config interface {ident}: non-opening disposition must zero geometry")

    thermal = _exact(top["thermal"], {"risk", "physical_soak_required",
                                      "load_case", "vents"}, "config.thermal")
    _enum(thermal["risk"], {"low", "moderate", "high"}, "config.thermal.risk")
    _boolean(thermal["physical_soak_required"],
             "config.thermal.physical_soak_required")
    _string(thermal["load_case"], "config.thermal.load_case")
    vents = thermal["vents"]
    if not isinstance(vents, list):
        raise EnclosureError("config.thermal.vents: expected list")
    for index, raw in enumerate(vents):
        vent = _exact(raw, {"center_mm", "count", "length_mm", "width_mm",
                            "pitch_mm", "axis"}, f"config.thermal.vents[{index}]")
        _vec(vent["center_mm"], 2, f"config.thermal.vents[{index}].center_mm")
        if isinstance(vent["count"], bool) or not isinstance(vent["count"], int) \
                or vent["count"] <= 0:
            raise EnclosureError(f"config.thermal.vents[{index}].count: expected >0 int")
        for field in ("length_mm", "width_mm", "pitch_mm"):
            _number(vent[field], f"config.thermal.vents[{index}].{field}", positive=True)
        _enum(vent["axis"], {"x", "y"}, f"config.thermal.vents[{index}].axis")

    physical = _exact(top["physical_validation"], {
        "insert_coupon_required", "board_drop_in_required",
        "all_interfaces_mated_required", "thermal_soak_required",
    }, "config.physical_validation")
    for field in physical:
        _boolean(physical[field], f"config.physical_validation.{field}")
    if physical["thermal_soak_required"] != thermal["physical_soak_required"]:
        raise EnclosureError("config: thermal soak requirements disagree")
    if physical["insert_coupon_required"] and "insert_coupon" not in parts:
        raise EnclosureError(
            "config.cad.printable_parts: required insert coupon is absent")
    return dict(value)


def load_bound_config(config_path: Path, root: Path) -> tuple[dict[str, Any],
                                                               dict[str, Any]]:
    config = validate_config(load_yaml(config_path))
    bindings = {}
    subject_fields = ["pcb", "step", "interface"]
    if "release_manifest" in config["subject"]:
        subject_fields.append("release_manifest")
    for field in subject_fields:
        bindings[field] = validate_file_binding(
            config["subject"][field], root, f"config.subject.{field}")
        if not bindings[field].get("matches", False):
            raise EnclosureError(
                f"config.subject.{field}: bound size/hash differs from actual file")
    cad_source = config["cad"].get("source")
    if cad_source is not None:
        bindings["cad_source"] = validate_file_binding(
            {key: cad_source[key] for key in ("path", "sha256", "size")},
            root, "config.cad.source")
        if not bindings["cad_source"].get("matches", False):
            raise EnclosureError(
                "config.cad.source: bound size/hash differs from actual file")
    interface_path = bindings["interface"]["path"]
    interface = validate_interface(load_json(interface_path))
    if interface["subject"]["board"]["sha256"] != \
            config["subject"]["pcb"]["sha256"]:
        raise EnclosureError(
            "config/interface PCB hashes disagree; regenerate the interface")
    return config, {"bindings": bindings, "interface": interface}


def stl_metrics(path: Path, *, quantization: float = 1e-6) -> dict[str, Any]:
    """Return strict, dependency-free ASCII/binary STL topology metrics."""
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise EnclosureError(f"cannot read STL {path}: {exc}") from exc
    if len(payload) < 15:
        raise EnclosureError(f"STL {path}: too short")
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    binary = False
    if len(payload) >= 84:
        count = struct.unpack_from("<I", payload, 80)[0]
        if 84 + count * 50 == len(payload):
            binary = True
            for index in range(count):
                values = struct.unpack_from("<12f", payload, 84 + index * 50)
                triangles.append((tuple(values[3:6]), tuple(values[6:9]),
                                  tuple(values[9:12])))
    if not binary:
        text = payload.decode("utf-8", errors="strict")
        vertices = [tuple(map(float, match.groups())) for match in re.finditer(
            r"\bvertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",
            text)]
        if not vertices or len(vertices) % 3:
            raise EnclosureError(f"STL {path}: malformed ASCII vertex count")
        triangles = [tuple(vertices[index:index + 3])
                     for index in range(0, len(vertices), 3)]
    if not triangles:
        raise EnclosureError(f"STL {path}: zero triangles")
    if any(not math.isfinite(axis) for tri in triangles for vertex in tri
           for axis in vertex):
        raise EnclosureError(f"STL {path}: non-finite coordinate")

    def key(vertex: Sequence[float]) -> tuple[int, int, int]:
        return tuple(round(axis / quantization) for axis in vertex)  # type: ignore[return-value]

    edge_counts: Counter[tuple[tuple[int, int, int], tuple[int, int, int]]] = Counter()
    directed_edges: Counter[tuple[tuple[int, int, int],
                                  tuple[int, int, int]]] = Counter()
    edge_tris: defaultdict[Any, list[int]] = defaultdict(list)
    area2_values: list[float] = []
    volume6 = 0.0
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for ti, tri in enumerate(triangles):
        a, b, c = tri
        xs.extend((a[0], b[0], c[0])); ys.extend((a[1], b[1], c[1]))
        zs.extend((a[2], b[2], c[2]))
        ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        cross = (ab[1] * ac[2] - ab[2] * ac[1],
                 ab[2] * ac[0] - ab[0] * ac[2],
                 ab[0] * ac[1] - ab[1] * ac[0])
        area2_values.append(math.sqrt(sum(axis * axis for axis in cross)))
        volume6 += (a[0] * (b[1] * c[2] - b[2] * c[1]) -
                    a[1] * (b[0] * c[2] - b[2] * c[0]) +
                    a[2] * (b[0] * c[1] - b[1] * c[0]))
        keys = [key(vertex) for vertex in tri]
        for left, right in ((keys[0], keys[1]), (keys[1], keys[2]),
                            (keys[2], keys[0])):
            edge = tuple(sorted((left, right)))
            edge_counts[edge] += 1
            directed_edges[(left, right)] += 1
            edge_tris[edge].append(ti)

    neighbors: defaultdict[int, set[int]] = defaultdict(set)
    for owners in edge_tris.values():
        for left in owners:
            neighbors[left].update(right for right in owners if right != left)
    unseen = set(range(len(triangles)))
    components = 0
    component_volumes: list[float] = []
    while unseen:
        components += 1
        start = unseen.pop()
        members = [start]
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for other in neighbors[current]:
                if other in unseen:
                    unseen.remove(other)
                    queue.append(other)
                    members.append(other)
        local_volume6 = 0.0
        for ti in members:
            a, b, c = triangles[ti]
            local_volume6 += (
                a[0] * (b[1] * c[2] - b[2] * c[1]) -
                a[1] * (b[0] * c[2] - b[2] * c[0]) +
                a[2] * (b[0] * c[1] - b[1] * c[0]))
        component_volumes.append(local_volume6 / 6.0)
    boundary = sum(1 for count in edge_counts.values() if count == 1)
    nonmanifold = sum(1 for count in edge_counts.values() if count != 2)
    orientation_mismatches = sum(
        1 for edge, count in edge_counts.items()
        if count == 2 and edge[0] != edge[1] and not (
            directed_edges[(edge[0], edge[1])] == 1 and
            directed_edges[(edge[1], edge[0])] == 1))
    return {
        "path": path.name,
        "sha256": sha256_file(path),
        "size": len(payload),
        "format": "binary" if binary else "ascii",
        "triangles": len(triangles),
        "components": components,
        "edge_manifold": nonmanifold == 0,
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "orientation_consistent": orientation_mismatches == 0,
        "orientation_mismatches": orientation_mismatches,
        "degenerate_facets": sum(1 for value in area2_values if value <= 1e-12),
        "bbox_mm": {
            "min": [min(xs), min(ys), min(zs)],
            "max": [max(xs), max(ys), max(zs)],
            "size": [max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)],
        },
        "signed_volume_mm3": volume6 / 6.0,
        "absolute_volume_mm3": abs(volume6 / 6.0),
        # Summing absolute per-component volumes prevents two disconnected,
        # oppositely oriented collision solids from cancelling to zero.
        "component_absolute_volume_mm3": sum(
            abs(value) for value in component_volumes),
    }


def scad(value: Any) -> str:
    """Serialize the small JSON-like subset used by the OpenSCAD engine."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:.9g}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(scad(item) for item in value) + "]"
    raise EnclosureError(f"cannot serialize {type(value).__name__} to OpenSCAD")
