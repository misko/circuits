#!/usr/bin/env python3
"""Create a deterministic candidate enclosure ZIP with an internal manifest."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Sequence

import yaml

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


def _data_entry(payload: bytes, arcname: str) -> dict[str, Any]:
    return {"data": payload, "name": arcname,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size": len(payload)}


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
    generation_authority = generation.get("authority")
    authored = config["cad"].get("source")
    if authored is not None:
        expected_authority = {
            "kind": "authored_scad",
            "binding": {key: authored[key] for key in ("path", "sha256", "size")},
        }
        if generation_authority != expected_authority:
            raise EnclosureError(
                "generation.json CAD authority differs from authored source binding")
        if sha256_file(source_path) != authored["sha256"] or \
                source_path.stat().st_size != authored["size"]:
            raise EnclosureError(
                "generated CAD source is not the exact bound authored SCAD")
    elif generation_authority is not None:
        if not isinstance(generation_authority, dict) or \
                generation_authority.get("kind") != "built_in_v1":
            raise EnclosureError("generation.json has unexpected CAD authority")
    installed_case_record = generation.get("installed_case")
    if not isinstance(installed_case_record, dict) or \
            installed_case_record.get("selector") != "installed_case" or \
            installed_case_record.get("path") != "assembled-case.stl":
        raise EnclosureError(
            "generation.json lacks the fixed installed_case artifact")
    installed_case_path = _build_record_path(
        build_dir, installed_case_record, "generated installed-case mesh")
    installed_command = installed_case_record.get("command")
    generation_engine = generation.get("engine")
    if not isinstance(generation_engine, dict) or \
            not isinstance(installed_command, list) or len(installed_command) != 8 or \
            installed_command[1] != "-o" or \
            Path(installed_command[2]).resolve() != installed_case_path.resolve() or \
            installed_command[3:7] != ["-D", 'part="installed_case"', "-D",
                                      "show_reference_board=false"] or \
            Path(installed_command[7]).resolve() != source_path.resolve() or \
            generation_engine.get("executable") != installed_command[0]:
        raise EnclosureError("generation.json installed_case command is not canonical")
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
    collision_report_record = clearance_evidence.get("collision_report_file")
    collision_report_path = (_build_record_path(
        build_dir, collision_report_record, "collision receipt")
        if collision_report_record else None)
    collision_generation_record = clearance_evidence.get("generation_file")
    if collision_generation_record:
        _require_record(generation_path, collision_generation_record,
                        "collision generation receipt")
    assembled_case_record = clearance_evidence.get("assembled_case_mesh")
    assembled_case_path = None
    if assembled_case_record:
        if assembled_case_record != {key: installed_case_record[key]
                                     for key in ("path", "sha256", "size")}:
            raise EnclosureError(
                "verified assembled-case mesh differs from generation.json")
        assembled_case_path = installed_case_path
    if clearance_check.get("status") == "PASS":
        if collision_report_path is None or collision_generation_record is None or \
                assembled_case_path is None:
            raise EnclosureError(
                "passed collision check lacks generation/case provenance")
        collision_report = load_json(collision_report_path)
        inputs = collision_report.get("inputs")
        generation_binding = {"path": generation_path.name,
                              "sha256": sha256_file(generation_path),
                              "size": generation_path.stat().st_size}
        if not isinstance(inputs, dict) or \
                inputs.get("generation") != generation_binding or \
                inputs.get("assembled_case_mesh") != installed_case_record:
            raise EnclosureError(
                "collision receipt differs from packaged generation provenance")
    physical_path = build_dir / "physical-evidence.yaml"
    if physical_path.is_file():
        physical_check = next((row for row in checks
                               if row.get("name") == "physical_evidence"), {})
        _require_record(physical_path, physical_check.get("evidence"),
                        "physical evidence")
    config_arc = "source/enclosure.yaml"
    interface_arc = "source/board-interface.json"
    pcb_arc = "subject/" + loaded["bindings"]["pcb"]["path"].name
    step_arc = "subject/" + loaded["bindings"]["step"]["path"].name
    cad_arc = "cad/enclosure.scad"
    release_manifest_path = loaded["bindings"].get("release_manifest", {}).get(
        "path")
    release_manifest_arc = ("subject/pcb-release-MANIFEST.txt"
                            if release_manifest_path is not None else None)

    # The authored config remains provenance, while this path-rebased copy can
    # be reopened with `--root` set to the extracted package directory.  It
    # changes no dimensions or hashes—only root-relative file locations.
    replay_config = copy.deepcopy(config)
    replay_config["subject"]["pcb"]["path"] = pcb_arc
    replay_config["subject"]["step"]["path"] = step_arc
    replay_config["subject"]["interface"]["path"] = interface_arc
    if release_manifest_arc is not None:
        replay_config["subject"]["release_manifest"]["path"] = \
            release_manifest_arc
    if authored is not None:
        replay_config["cad"]["source"]["path"] = cad_arc
    replay_payload = yaml.safe_dump(
        replay_config, sort_keys=False, allow_unicode=True).encode("utf-8")
    replay_arc = "replay/enclosure.yaml"

    entries = [
        _entry(config_path, config_arc),
        _data_entry(replay_payload, replay_arc),
        _entry(loaded["bindings"]["interface"]["path"], interface_arc),
        _entry(loaded["bindings"]["pcb"]["path"], pcb_arc),
        _entry(loaded["bindings"]["step"]["path"], step_arc),
        _entry(source_path, cad_arc),
        _entry(generation_path, "verification/generation.json"),
        _entry(verification_path, "verification/verification.json"),
    ]
    if release_manifest_path is not None:
        entries.append(_entry(release_manifest_path, release_manifest_arc))
    for part in config["cad"]["printable_parts"]:
        entries.append(_entry(build_dir / f"{part}.stl", f"meshes/{part}.stl"))
    for optional, arcname in (
            (build_dir / "assembly.png", "renders/assembly.png"),
            (step_inspection_path, "verification/step-inspection.json"),
            (component_mesh_path, "verification/step-components.stl"),
            (assembled_case_path, "verification/assembled-case.stl"),
            (collision_path, "verification/clearance-intersection.stl"),
            (collision_report_path, "verification/collision.json"),
            (physical_path, "verification/physical-evidence.yaml")):
        if optional is not None and optional.is_file():
            entries.append(_entry(optional, arcname))
    entries.sort(key=lambda row: row["name"])
    if len({row["name"] for row in entries}) != len(entries):
        raise EnclosureError("package payload contains duplicate archive paths")
    manifest = {
        "schema": 1,
        "kind": "pcb-enclosure-package-v1",
        "name": config["name"],
        "mode": config["mode"],
        "status": status,
        "config_semantic_sha256": config_hash,
        "based_on": {
            "release": config["subject"]["release"],
            "pcb": {"path": pcb_arc,
                    "sha256": config["subject"]["pcb"]["sha256"],
                    "size": config["subject"]["pcb"]["size"]},
            "step": {"path": step_arc,
                     "sha256": config["subject"]["step"]["sha256"],
                     "size": config["subject"]["step"]["size"]},
        },
        "replay": {"root": ".", "config": replay_arc,
                   "semantic_sha256": semantic_sha256(replay_config)},
        "files": [{key: row[key] for key in ("name", "sha256", "size")}
                  for row in entries],
    }
    if release_manifest_arc is not None:
        manifest["based_on"]["manifest"] = {
            "path": release_manifest_arc,
            "sha256": config["subject"]["release_manifest"]["sha256"],
            "size": config["subject"]["release_manifest"]["size"],
        }
    if generation_authority is not None:
        manifest["cad_authority"] = generation_authority
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
            payload = (row["path"].read_bytes() if "path" in row else
                       row["data"])
            archive.writestr(info, payload)
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
