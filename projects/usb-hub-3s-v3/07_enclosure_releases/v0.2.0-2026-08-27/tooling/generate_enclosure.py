#!/usr/bin/env python3
"""Generate standalone OpenSCAD and printable STL parts from enclosure.yaml."""
from __future__ import annotations

import argparse
import math
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    BUILT_IN_PRINTABLE_PARTS, EnclosureError, atomic_output,
    load_bound_config, read_stable_bytes, reject_symlink_path, run_bounded, scad,
    semantic_sha256, sha256_file, validate_output_path, write_json,
)


ENGINE = SKILL_DIR / "assets/enclosure-engine.scad"
INSTALLED_CASE_SELECTOR = "installed_case"
INSTALLED_CASE_FILENAME = "assembled-case.stl"
UNKNOWN_SELECTOR_PROBE = "__pcb_enclosure_unknown__"
CANONICAL_STL_KIND = "ascii-stl-facet-order-v1"


def _version_tuple(value: str) -> tuple[int, ...]:
    match = re.search(r"\d+(?:\.\d+)+", value)
    if not match:
        raise EnclosureError(f"cannot parse OpenSCAD version from {value!r}")
    return tuple(int(part) for part in match.group(0).split("."))


def _openscad_identity(executable: str, minimum: str) -> dict[str, str]:
    result = run_bounded([executable, "--version"], timeout_s=30)
    version = (result.stdout + result.stderr).strip()
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


def _canonicalize_ascii_stl(path: Path) -> None:
    """Write a stable facet/vertex ordering without changing mesh topology."""
    try:
        source = read_stable_bytes(
            path, f"generated ASCII STL {path}").decode("ascii")
    except UnicodeDecodeError as exc:
        raise EnclosureError(
            f"custom authored STL is not OpenSCAD ASCII: {path}") from exc
    pending: list[tuple[float, float, float]] = []
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    for line in source.splitlines():
        fields = line.split()
        if fields[:1] != ["vertex"]:
            continue
        if len(fields) != 4:
            raise EnclosureError(f"malformed ASCII STL vertex in {path}")
        try:
            point = tuple(float(value) for value in fields[1:])
        except ValueError as exc:
            raise EnclosureError(f"malformed ASCII STL coordinate in {path}") from exc
        if any(not math.isfinite(value) for value in point):
            raise EnclosureError(f"non-finite ASCII STL coordinate in {path}")
        pending.append(point)
        if len(pending) == 3:
            # Normalize cyclic start while preserving the winding that carries
            # the solid's orientation.  Then normalize global facet order.
            a, b, c = pending
            triangles.append(min(((a, b, c), (b, c, a), (c, a, b))))
            pending = []
    if pending or not triangles:
        raise EnclosureError(f"could not parse complete ASCII STL facets in {path}")
    triangles.sort()

    def number(value: float) -> str:
        if abs(value) < 5e-12:
            value = 0.0
        return format(value, ".10g")

    lines = ["solid pcb_enclosure"]
    for a, b, c in triangles:
        ab = tuple(b[index] - a[index] for index in range(3))
        ac = tuple(c[index] - a[index] for index in range(3))
        cross = (
            ab[1] * ac[2] - ab[2] * ac[1],
            ab[2] * ac[0] - ab[0] * ac[2],
            ab[0] * ac[1] - ab[1] * ac[0],
        )
        magnitude = math.sqrt(sum(value * value for value in cross))
        normal = ((0.0, 0.0, 0.0) if magnitude <= 1e-18 else
                  tuple(value / magnitude for value in cross))
        lines.append("  facet normal " + " ".join(number(value)
                                                    for value in normal))
        lines.append("    outer loop")
        for point in (a, b, c):
            lines.append("      vertex " + " ".join(number(value)
                                                       for value in point))
        lines.extend(("    endloop", "  endfacet"))
    lines.append("endsolid pcb_enclosure")
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def _run_selector(executable: str, source: Path, build_dir: Path,
                  selector: str, filename: str,
                  *, canonicalize: bool = False,
                  protected_inputs: Sequence[Path] = ()) -> dict[str, Any]:
    output = build_dir / filename
    command = [executable, "-o", str(output.resolve(strict=False)), "-D",
               f'part="{selector}"', "-D", "show_reference_board=false",
               str(source.resolve())]
    with atomic_output(
            output, where=f"OpenSCAD {selector} output", root=build_dir,
            inputs=[source, *protected_inputs],
            temporary_suffix=".stl") as (temporary, stream):
        stream.flush()
        staged_command = [*command]
        staged_command[2] = str(temporary)
        result = run_bounded(staged_command, timeout_s=300)
        diagnostic = result.stdout + result.stderr
        if result.returncode or "ERROR:" in diagnostic or \
                "WARNING:" in diagnostic or not temporary.is_file() or \
                temporary.stat().st_size == 0:
            raise EnclosureError(
                f"OpenSCAD could not generate {selector} "
                f"(rc={result.returncode}):\n" + diagnostic[-4000:])
        if canonicalize:
            _canonicalize_ascii_stl(temporary)
    record = {
        "selector": selector,
        "path": output.name,
        "sha256": sha256_file(output),
        "size": output.stat().st_size,
        "command": command,
        "execution": {"kind": "atomic-same-directory-output-v1"},
    }
    if canonicalize:
        record["canonicalization"] = CANONICAL_STL_KIND
    return record


def _probe_closed_authored_selectors(executable: str, source: Path,
                                     build_dir: Path,
                                     declared: Sequence[str],
                                     protected_inputs: Sequence[Path] = (),
                                     ) -> dict[str, Any] | None:
    """Reject catch-all authored entrypoints when custom parts are declared."""
    custom = [part for part in declared
              if part not in BUILT_IN_PRINTABLE_PARTS]
    if not custom:
        return None
    output = build_dir / ".selector-contract-probe.stl"
    command = [executable, "-o", str(output.resolve()), "-D",
               f'part="{UNKNOWN_SELECTOR_PROBE}"', "-D",
               "show_reference_board=false", str(source.resolve())]
    with atomic_output(
            output, where="OpenSCAD unknown-selector probe", root=build_dir,
            inputs=[source, *protected_inputs],
            temporary_suffix=".stl") as (temporary, stream):
        stream.flush()
        staged_command = [*command]
        staged_command[2] = str(temporary)
        result = run_bounded(staged_command, timeout_s=120)
        diagnostic = result.stdout + result.stderr
        generated = temporary.is_file() and temporary.stat().st_size > 0
        if "WARNING:" in diagnostic:
            raise EnclosureError(
                "OpenSCAD unknown-selector probe emitted a warning:\n" +
                diagnostic[-4000:])
    output.unlink(missing_ok=True)
    if generated:
        raise EnclosureError(
            "authored custom selector contract is open: an unknown selector "
            "generated geometry; use explicit part branches")
    return {
        "kind": "closed-authored-selectors-v1",
        "declared": list(declared),
        "custom": custom,
        "probe_selector": UNKNOWN_SELECTOR_PROBE,
        "probe_result": ("REJECTED" if result.returncode or
                         "ERROR:" in diagnostic else "EMPTY"),
        "mesh_canonicalization": CANONICAL_STL_KIND,
    }


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
        "fastener_strategy": fasteners["strategy"],
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


def _assembly_contract(config: dict[str, Any],
                       interface: dict[str, Any]) -> dict[str, Any]:
    """Project the authored fastener intent into generated-CAD semantics."""
    fasteners = config["fasteners"]
    board_axes = _mount_points(interface, fasteners["board_holes"])
    case_axes = fasteners["case_holes_mm"]
    separate = fasteners["strategy"] == "separate_perimeter"
    return {
        "kind": "pcb-enclosure-assembly-contract-v1",
        "fastener_strategy": fasteners["strategy"],
        "board_fastener_axes_mm": board_axes,
        "case_fastener_axes_mm": case_axes,
        "shell_closure_axes_mm": case_axes if separate else board_axes,
        "pcb_retained_with_lid_removed": separate,
        "shared_board_shell_axes": not separate,
    }


def generate(config_path: Path, root: Path, build_dir: Path,
             parts: Sequence[str], openscad: str) -> dict[str, Any]:
    config, loaded = load_bound_config(config_path, root)
    interface = loaded["interface"]
    build_dir = reject_symlink_path(build_dir, "generation build directory")
    subject_root = reject_symlink_path(root, "generation subject root")
    if build_dir == subject_root:
        raise EnclosureError(
            "generation build directory must not be the subject root")
    build_dir.mkdir(parents=True, exist_ok=True)
    build_dir = reject_symlink_path(build_dir, "generation build directory")
    protected_inputs = [
        config_path.resolve(strict=True),
        *(row["path"] for row in loaded["bindings"].values()
          if isinstance(row, dict) and isinstance(row.get("path"), Path)),
    ]
    source = build_dir / "enclosure.scad"
    authored = config["cad"].get("source")
    if authored is None:
        _require_rectangular_outline(interface)
        if not ENGINE.is_file():
            raise EnclosureError(f"OpenSCAD engine missing: {ENGINE}")
        payload = (_prelude(config, interface).encode("utf-8") +
                   read_stable_bytes(ENGINE, "built-in enclosure engine"))
        with atomic_output(
                source, where="generated OpenSCAD source", root=build_dir,
                inputs=[*protected_inputs, ENGINE]) as (_, stream):
            stream.write(payload)
        authority = {
            "kind": "built_in_v1",
            "engine_source": {
                "path": "assets/enclosure-engine.scad",
                "sha256": sha256_file(ENGINE),
                "size": ENGINE.stat().st_size,
            },
        }
    else:
        authored_path = loaded["bindings"]["cad_source"]["path"]
        if authored_path.resolve().is_relative_to(build_dir.resolve()):
            raise EnclosureError(
                "config.cad.source: authored input must be outside the build directory")
        # Preserve the exact reviewed source bytes.  Command-line -D values
        # select parts without modifying or wrapping the authored entrypoint.
        with atomic_output(
                source, where="copied authored OpenSCAD source", root=build_dir,
                inputs=protected_inputs) as (_, stream):
            stream.write(read_stable_bytes(
                authored_path, "authored OpenSCAD source"))
        authority = {
            "kind": "authored_scad",
            "binding": {
                "path": authored["path"],
                "sha256": authored["sha256"],
                "size": authored["size"],
            },
        }
    executable = shutil.which(openscad)
    if executable is None:
        raise EnclosureError(f"OpenSCAD executable not found: {openscad}")
    engine_identity = _openscad_identity(executable,
                                        config["cad"]["minimum_version"])
    selector_contract = (_probe_closed_authored_selectors(
        executable, source, build_dir, config["cad"]["printable_parts"],
        protected_inputs)
        if authored is not None else None)
    canonicalize = selector_contract is not None
    records = []
    for part in parts:
        if part not in config["cad"]["printable_parts"]:
            raise EnclosureError(f"requested part {part!r} is not declared printable")
        record = _run_selector(executable, source, build_dir, part,
                               f"{part}.stl", canonicalize=canonicalize,
                               protected_inputs=protected_inputs)
        records.append({"part": part, **record})
    installed_case = _run_selector(
        executable, source, build_dir, INSTALLED_CASE_SELECTOR,
        INSTALLED_CASE_FILENAME, canonicalize=canonicalize,
        protected_inputs=protected_inputs)
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
        "authority": authority,
        "assembly_contract": _assembly_contract(config, interface),
        "selector_contract": selector_contract,
        "source": {"path": source.name, "sha256": sha256_file(source),
                   "size": source.stat().st_size},
        "parts": records,
        "installed_case": installed_case,
    }
    generation_path = build_dir / "generation.json"
    receipt_inputs = [*protected_inputs, source,
                      *(build_dir / f"{part}.stl" for part in parts),
                      build_dir / INSTALLED_CASE_FILENAME]
    validate_output_path(
        generation_path, where="generation receipt", root=build_dir,
        inputs=receipt_inputs)
    write_json(generation_path, receipt, inputs=receipt_inputs, root=build_dir,
               where="generation receipt")
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
