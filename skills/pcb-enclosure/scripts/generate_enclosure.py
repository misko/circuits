#!/usr/bin/env python3
"""Generate standalone OpenSCAD and printable STL parts from enclosure.yaml."""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, load_bound_config, scad, semantic_sha256, sha256_file,
    write_json,
)


ENGINE = SKILL_DIR / "assets/enclosure-engine.scad"


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)+", value)
    if not match:
        raise EnclosureError(f"cannot parse OpenSCAD version from {value!r}")
    return tuple(int(part) for part in match.group(0).split("."))


def _openscad_identity(executable: str, minimum: str) -> dict[str, str]:
    result = subprocess.run([executable, "--version"], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            check=False)
    version = result.stdout.strip()
    if result.returncode or not version:
        raise EnclosureError("OpenSCAD version probe failed")
    actual_tuple = _version_tuple(version)
    minimum_tuple = _version_tuple(minimum)
    width = max(len(actual_tuple), len(minimum_tuple))
    if actual_tuple + (0,) * (width - len(actual_tuple)) < \
            minimum_tuple + (0,) * (width - len(minimum_tuple)):
        raise EnclosureError(
            f"OpenSCAD {version!r} is older than required {minimum!r}")
    return {"executable": executable, "version": version,
            "minimum_version": minimum}


def _mount_points(interface: dict[str, Any], refs: Sequence[str]) -> list[list[float]]:
    by_ref: dict[str, list[list[float]]] = {}
    for row in interface["board"]["mounting_holes"]:
        by_ref.setdefault(row["ref"], []).append(row["position_mm"])
    points = []
    for ref in refs:
        matches = by_ref.get(ref, [])
        if len(matches) != 1:
            raise EnclosureError(
                f"board mounting ref {ref}: expected exactly one drilled pad, got {len(matches)}")
        points.append(matches[0])
    return points


def _require_rectangular_outline(interface: dict[str, Any]) -> None:
    """Bound the v1 engine to the geometry it actually represents."""
    outline = interface["board"]["outline"]
    contours = outline["contours_mm"]
    width, height = outline["size_mm"]
    expected = {
        (-width / 2, -height / 2), (-width / 2, height / 2),
        (width / 2, -height / 2), (width / 2, height / 2),
    }
    if len(contours) != 1 or len(contours[0]) != 4:
        raise EnclosureError(
            "built-in OpenSCAD engine supports one rectangular outline only")
    observed = {(round(point[0], 6), round(point[1], 6))
                for point in contours[0]}
    normalized_expected = {(round(x, 6), round(y, 6)) for x, y in expected}
    if observed != normalized_expected:
        raise EnclosureError(
            "built-in OpenSCAD engine supports an axis-aligned rectangle only")


def _prelude(config: dict[str, Any], interface: dict[str, Any]) -> str:
    geometry = config["geometry"]
    fasteners = config["fasteners"]
    insert = fasteners["insert"]
    screw = fasteners["screw"]
    board = interface["board"]
    mount_points = _mount_points(interface, fasteners["board_holes"])
    ports = [[
        row["id"], row["ref"], row["side"], row["disposition"],
        *row["center_mm"], row["shape"], *row["opening_mm"],
    ] for row in config["interfaces"]]
    vents = [[
        *row["center_mm"], row["count"], row["length_mm"], row["width_mm"],
        row["pitch_mm"], row["axis"],
    ] for row in config["thermal"]["vents"]]
    values = {
        "part": "assembly",
        "explode": 8,
        "show_reference_board": True,
        "topology": geometry["topology"],
        "board_size": board["outline"]["size_mm"],
        "board_thickness": board["thickness_mm"],
        "board_mount_holes": mount_points,
        "case_holes": fasteners["case_holes_mm"],
        "xy_clearance": geometry["xy_clearance_mm"],
        "wall": geometry["wall_mm"],
        "floor": geometry["floor_mm"],
        "roof": geometry["roof_mm"],
        "corner_radius": geometry["corner_radius_mm"],
        "board_bottom_z": geometry["board_bottom_z_mm"],
        "inside_top_z": geometry["inside_top_z_mm"],
        "seam_z": geometry["seam_z_mm"],
        "panel_thickness": geometry["panel_thickness_mm"],
        "panel_capture": geometry["panel_capture_mm"],
        "panel_clearance": geometry["panel_clearance_mm"],
        "corner_post_d": geometry["corner_post_mm"],
        "lid_column_board_gap": geometry["lid_column_board_gap_mm"],
        "lip_h": 1.20,
        "lip_t": 0.80,
        "lip_clearance": 0.25,
        "boss_d": fasteners["boss_d_mm"],
        "case_post_d": fasteners["case_post_d_mm"],
        "lid_column_d": max(screw["head_d_mm"] + 0.8,
                            screw["clearance_d_mm"] + 2.0),
        "insert_hole_d": insert["hole_d_mm"],
        "insert_flange_recess_d": insert["flange_recess_d_mm"],
        "insert_flange_recess_depth": insert["flange_recess_depth_mm"],
        "insert_length": insert["length_mm"],
        "insert_bottom_clearance": insert["bottom_clearance_mm"],
        "screw_clearance_d": screw["clearance_d_mm"],
        "screw_head_d": screw["head_d_mm"],
        "screw_head_recess_depth": screw["head_recess_depth_mm"],
        "ports": ports,
        "vents": vents,
    }
    header = [
        "// GENERATED by pcb-enclosure; edit enclosure.yaml, not this file.",
        f"// config semantic sha256: {semantic_sha256(config)}",
        f"// interface semantic sha256: {semantic_sha256(interface)}",
    ]
    header.extend(f"{key} = {scad(value)};" for key, value in values.items())
    return "\n".join(header) + "\n\n"


def generate(config_path: Path, root: Path, build_dir: Path,
             parts: Sequence[str], openscad: str) -> dict[str, Any]:
    config, loaded = load_bound_config(config_path, root)
    interface = loaded["interface"]
    _require_rectangular_outline(interface)
    if not ENGINE.is_file():
        raise EnclosureError(f"OpenSCAD engine missing: {ENGINE}")
    build_dir.mkdir(parents=True, exist_ok=True)
    source = build_dir / "enclosure.scad"
    source.write_text(_prelude(config, interface) +
                      ENGINE.read_text(encoding="utf-8"), encoding="utf-8")
    executable = shutil.which(openscad)
    if executable is None:
        raise EnclosureError(f"OpenSCAD executable not found: {openscad}")
    engine_identity = _openscad_identity(executable,
                                        config["cad"]["minimum_version"])
    records = []
    for part in parts:
        if part not in config["cad"]["printable_parts"]:
            raise EnclosureError(f"requested part {part!r} is not declared printable")
        output = build_dir / f"{part}.stl"
        command = [executable, "-o", str(output), "-D", f'part="{part}"',
                   "-D", "show_reference_board=false", str(source)]
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, check=False)
        if result.returncode or not output.is_file() or output.stat().st_size == 0:
            raise EnclosureError(
                f"OpenSCAD could not generate {part} (rc={result.returncode}):\n"
                + result.stdout[-4000:])
        records.append({
            "part": part,
            "path": output.name,
            "sha256": sha256_file(output),
            "size": output.stat().st_size,
            "command": command,
        })
    receipt = {
        "schema": 1,
        "kind": "pcb-enclosure-generation-v1",
        "name": config["name"],
        "mode": config["mode"],
        "engine": engine_identity,
        "config": {"path": str(config_path), "semantic_sha256": semantic_sha256(config),
                   "raw_sha256": sha256_file(config_path)},
        "interface": {"semantic_sha256": semantic_sha256(interface),
                      "raw_sha256": sha256_file(loaded["bindings"]["interface"]["path"])},
        "source": {"path": source.name, "sha256": sha256_file(source),
                   "size": source.stat().st_size},
        "parts": records,
    }
    write_json(build_dir / "generation.json", receipt)
    return receipt


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--root", type=Path, required=True,
                        help="explicit subject root for traversal-free bindings")
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--parts", help="comma-separated subset; default config list")
    parser.add_argument("--openscad", default="openscad")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        config, _ = load_bound_config(args.config, args.root)
        parts = (args.parts.split(",") if args.parts else
                 config["cad"]["printable_parts"])
        receipt = generate(args.config, args.root, args.build_dir, parts,
                           args.openscad)
    except (OSError, EnclosureError) as exc:
        print(f"ENCLOSURE GENERATION ERROR — input: {args.config}: {exc}",
              file=sys.stderr)
        return 1
    print(
        f"ENCLOSURE GENERATED — input: {args.config} — "
        f"{len(receipt['parts'])}/{len(parts)} declared part(s)")
    print(f"wrote {args.build_dir / 'generation.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
