#!/usr/bin/env python3
"""Create a deterministic candidate enclosure ZIP with an internal manifest."""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, load_bound_config, load_json, semantic_sha256, sha256_file,
)


ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def _entry(path: Path, arcname: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EnclosureError(f"package input missing or symlinked: {path}")
    return {"path": path, "name": arcname, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def _require_record(path: Path, record: Any, where: str) -> None:
    if not isinstance(record, dict):
        raise EnclosureError(f"{where}: missing file identity")
    if record.get("sha256") != sha256_file(path) or \
            record.get("size") != path.stat().st_size:
        raise EnclosureError(f"{where}: file changed after its evidence was written")


def _build_record_path(build_dir: Path, record: Any, where: str) -> Path:
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise EnclosureError(f"{where}: missing build-relative path")
    name = record["path"]
    if Path(name).name != name or name in {"", ".", ".."}:
        raise EnclosureError(f"{where}: evidence path is not a build filename")
    path = build_dir / name
    _require_record(path, record, where)
    return path


def package(config_path: Path, root: Path, build_dir: Path, output: Path,
            allow_incomplete: bool) -> dict[str, Any]:
    config, loaded = load_bound_config(config_path, root)
    verification_path = build_dir / "verification.json"
    verification = load_json(verification_path)
    if verification.get("kind") != "pcb-enclosure-verification-v1":
        raise EnclosureError("verification.json has wrong kind")
    config_hash = semantic_sha256(config)
    if verification.get("config", {}).get("semantic_sha256") != config_hash or \
            verification.get("config", {}).get("raw_sha256") != sha256_file(config_path):
        raise EnclosureError("verification.json is stale for this config")
    status = verification.get("status")
    if status not in {"CAD_READY", "PRINT_VERIFIED", "THERMALLY_VERIFIED",
                      "INCOMPLETE", "FAIL"}:
        raise EnclosureError("verification.json has unknown status")
    checks = verification.get("checks")
    if not isinstance(checks, list) or any(
            not isinstance(row, dict) for row in checks):
        raise EnclosureError("verification.json lacks its check census")
    if any(row.get("status") == "FAIL" for row in checks) or status == "FAIL":
        raise EnclosureError("failed verification cannot be packaged")
    if status == "INCOMPLETE" and not allow_incomplete:
        raise EnclosureError(
            "verification status INCOMPLETE; use --allow-incomplete for a draft")

    generation_path = build_dir / "generation.json"
    generation = load_json(generation_path)
    if generation.get("kind") != "pcb-enclosure-generation-v1":
        raise EnclosureError("generation.json has wrong kind")
    if generation.get("config", {}).get("semantic_sha256") != config_hash or \
            generation.get("config", {}).get("raw_sha256") != sha256_file(config_path):
        raise EnclosureError("generation.json is stale for this config")
    source_path = build_dir / "enclosure.scad"
    _require_record(source_path, generation.get("source"), "generated CAD source")
    part_records = generation.get("parts")
    if not isinstance(part_records, list):
        raise EnclosureError("generation.json lacks part identities")
    part_by_name = {row.get("part"): row for row in part_records
                    if isinstance(row, dict)}
    if set(part_by_name) != set(config["cad"]["printable_parts"]) or \
            len(part_records) != len(part_by_name):
        raise EnclosureError("generation.json part census differs from config")
    mesh_check = next((row for row in checks
                       if row.get("name") == "printable_meshes"), None)
    mesh_evidence = (mesh_check or {}).get("evidence", {}).get("parts", {})
    if not isinstance(mesh_evidence, dict):
        raise EnclosureError("verification.json lacks printable mesh identities")
    for part in config["cad"]["printable_parts"]:
        mesh_path = build_dir / f"{part}.stl"
        _require_record(mesh_path, part_by_name[part], f"generated mesh {part}")
        _require_record(mesh_path, mesh_evidence.get(part),
                        f"verified mesh {part}")
    clearance_check = next((row for row in checks
                            if row.get("name") == "exact_solid_clearance"), {})
    clearance_evidence = clearance_check.get("evidence", {})
    step_record = clearance_evidence.get("step_inspection_file")
    step_inspection_path = (_build_record_path(
        build_dir, step_record, "STEP inspection") if step_record else None)
    component_mesh_path = None
    step_report = clearance_evidence.get("step_inspection")
    if isinstance(step_report, dict):
        component_record = step_report.get("geometry", {}).get("component_mesh")
        if component_record:
            component_mesh_path = _build_record_path(
                build_dir, component_record, "STEP component mesh")
    collision_record = clearance_evidence.get("collision_mesh")
    collision_path = (_build_record_path(
        build_dir, collision_record, "clearance intersection")
        if collision_record else None)
    physical_path = build_dir / "physical-evidence.yaml"
    if physical_path.is_file():
        physical_check = next((row for row in checks
                               if row.get("name") == "physical_evidence"), {})
        _require_record(physical_path, physical_check.get("evidence"),
                        "physical evidence")
    entries = [
        _entry(config_path, "source/enclosure.yaml"),
        _entry(loaded["bindings"]["interface"]["path"],
               "source/board-interface.json"),
        _entry(loaded["bindings"]["pcb"]["path"],
               "subject/" + loaded["bindings"]["pcb"]["path"].name),
        _entry(loaded["bindings"]["step"]["path"],
               "subject/" + loaded["bindings"]["step"]["path"].name),
        _entry(source_path, "cad/enclosure.scad"),
        _entry(generation_path, "verification/generation.json"),
        _entry(verification_path, "verification/verification.json"),
    ]
    for part in config["cad"]["printable_parts"]:
        entries.append(_entry(build_dir / f"{part}.stl", f"meshes/{part}.stl"))
    for optional, arcname in (
            (build_dir / "assembly.png", "renders/assembly.png"),
            (step_inspection_path, "verification/step-inspection.json"),
            (component_mesh_path, "verification/step-components.stl"),
            (collision_path, "verification/clearance-intersection.stl"),
            (physical_path, "verification/physical-evidence.yaml")):
        if optional is not None and optional.is_file():
            entries.append(_entry(optional, arcname))
    entries.sort(key=lambda row: row["name"])
    manifest = {
        "schema": 1,
        "kind": "pcb-enclosure-package-v1",
        "name": config["name"],
        "mode": config["mode"],
        "status": status,
        "config_semantic_sha256": config_hash,
        "files": [{key: row[key] for key in ("name", "sha256", "size")}
                  for row in entries],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        manifest_info = zipfile.ZipInfo("MANIFEST.json", ZIP_TIME)
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(manifest_info,
                         json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        for row in entries:
            info = zipfile.ZipInfo(row["name"], ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, row["path"].read_bytes())
    return {**manifest, "package": {"path": str(output),
                                    "sha256": sha256_file(output),
                                    "size": output.stat().st_size}}


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-incomplete", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        receipt = package(args.config, args.root, args.build_dir, args.output,
                          args.allow_incomplete)
    except (OSError, EnclosureError, zipfile.BadZipFile) as exc:
        print(f"ENCLOSURE PACKAGE ERROR — input: {args.config}: {exc}", file=sys.stderr)
        return 1
    print(
        f"ENCLOSURE PACKAGED — input: {args.config} — "
        f"{len(receipt['files'])}/{len(receipt['files'])} files, "
        f"verification={receipt['status']}")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
