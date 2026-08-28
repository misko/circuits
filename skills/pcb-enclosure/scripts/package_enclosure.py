#!/usr/bin/env python3
"""Create a deterministic candidate enclosure ZIP with an internal manifest."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    BUILT_IN_PRINTABLE_PARTS, EnclosureError, atomic_output,
    load_bound_config, load_json, read_stable_bytes, require_ordinary_file,
    semantic_sha256, sha256_file,
)
from verify_enclosure import verify as regrade_workspace  # noqa: E402


ZIP_TIME = (2026, 1, 1, 0, 0, 0)
VERIFICATION_CHECKS = (
    "subject_binding",
    "interface_coverage",
    "fastener_geometry",
    "printable_meshes",
    "exact_solid_clearance",
    "thermal_plan",
    "physical_evidence",
)
CHECK_STATUSES = {"PASS", "FAIL", "INCOMPLETE", "NOT_APPLICABLE"}
PACKAGE_STATUSES = {
    "CAD_READY", "PRINT_VERIFIED", "THERMALLY_VERIFIED", "INCOMPLETE", "FAIL",
}


def _entry(path: Path, arcname: str) -> dict[str, Any]:
    path = require_ordinary_file(path, f"package input {arcname}")
    return {"path": path, "name": arcname, "sha256": sha256_file(path),
            "size": path.stat().st_size}


def _data_entry(payload: bytes, arcname: str) -> dict[str, Any]:
    return {"data": payload, "name": arcname,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size": len(payload)}


def _snapshot_entries(entries: Sequence[Mapping[str, Any]],
                      directory: Path) -> list[dict[str, Any]]:
    """Copy each path entry once and bind the exact bytes later archived."""
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(entries):
        row = dict(raw)
        if "path" not in row:
            result.append(row)
            continue
        source = require_ordinary_file(
            Path(row["path"]), f"package input {row['name']}")
        before = source.lstat()
        source_fd = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        snapshot = directory / f"{index:04d}.payload"
        output_fd: int | None = None
        digest = hashlib.sha256()
        size = 0
        try:
            opened = os.fstat(source_fd)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or \
                    (opened.st_dev, opened.st_ino, opened.st_size) != \
                    (before.st_dev, before.st_ino, before.st_size):
                raise EnclosureError(
                    f"package input {row['name']}: changed while opening")
            output_fd = os.open(
                snapshot, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            while True:
                chunk = os.read(source_fd, 1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
                view = memoryview(chunk)
                while view:
                    written = os.write(output_fd, view)
                    view = view[written:]
            os.fsync(output_fd)
        finally:
            os.close(source_fd)
            if output_fd is not None:
                os.close(output_fd)
        after = require_ordinary_file(
            source, f"package input {row['name']}").lstat()
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != \
                (before.st_dev, before.st_ino, before.st_size,
                 before.st_mtime_ns):
            raise EnclosureError(
                f"package input {row['name']}: changed during snapshot")
        if digest.hexdigest() != row["sha256"] or size != row["size"]:
            raise EnclosureError(
                f"package input {row['name']}: changed after census")
        row["path"] = snapshot
        result.append(row)
    return result


def _verify_staged_zip(path: Path, manifest: Mapping[str, Any],
                       entries: Sequence[Mapping[str, Any]]) -> None:
    """Reopen the exact staged archive before its atomic publication."""
    try:
        with zipfile.ZipFile(path) as archive:
            expected_names = ["MANIFEST.json", *[row["name"] for row in entries]]
            if archive.namelist() != expected_names or archive.testzip() is not None:
                raise EnclosureError(
                    "staged package ZIP census/integrity differs from manifest")
            parsed = json.loads(archive.read("MANIFEST.json"))
            if parsed != manifest:
                raise EnclosureError("staged package manifest bytes changed")
            for row in entries:
                payload = archive.read(row["name"])
                if len(payload) != row["size"] or \
                        hashlib.sha256(payload).hexdigest() != row["sha256"]:
                    raise EnclosureError(
                        f"staged package payload differs: {row['name']}")
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise EnclosureError(f"cannot reopen staged package ZIP: {exc}") from exc


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


def _exact_mapping(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise EnclosureError(f"{where}: expected object")
    actual = set(value)
    if actual != fields:
        raise EnclosureError(
            f"{where}: fields differ; missing={sorted(fields - actual)}, "
            f"unknown={sorted(actual - fields)}")
    return value


def _validate_verification_receipt(value: Mapping[str, Any]) -> None:
    """Validate the verifier's exact seven-check v1 receipt schema."""
    receipt = _exact_mapping(value, {
        "schema", "kind", "status", "config", "checks", "summary",
    }, "verification.json")
    if receipt["schema"] != 1 or isinstance(receipt["schema"], bool):
        raise EnclosureError("verification.json has wrong schema")
    if receipt["kind"] != "pcb-enclosure-verification-v1":
        raise EnclosureError("verification.json has wrong kind")
    if not isinstance(receipt["status"], str) or \
            receipt["status"] not in PACKAGE_STATUSES:
        raise EnclosureError("verification.json has unknown status")
    config_record = _exact_mapping(
        receipt["config"], {"path", "raw_sha256", "semantic_sha256"},
        "verification.json.config")
    if not all(isinstance(config_record[field], str)
               for field in config_record):
        raise EnclosureError("verification.json.config has invalid values")
    checks = receipt["checks"]
    if not isinstance(checks, list):
        raise EnclosureError("verification.json lacks its check census")
    raw_names = [row.get("name") if isinstance(row, Mapping) else None
                 for row in checks]
    names = [name if isinstance(name, str) else f"<invalid-name-{index}>"
             for index, name in enumerate(raw_names)]
    expected = set(VERIFICATION_CHECKS)
    counts = {name: names.count(name) for name in expected}
    missing = sorted(name for name, count in counts.items() if count == 0)
    duplicate = sorted(name for name, count in counts.items() if count > 1)
    unexpected = sorted(str(name) for name in names if name not in expected)
    if len(checks) != len(VERIFICATION_CHECKS) or missing or duplicate or unexpected \
            or tuple(names) != VERIFICATION_CHECKS:
        raise EnclosureError(
            "verification check census differs from the closed seven-check v1 "
            f"census; missing={missing}, duplicate={duplicate}, "
            f"unexpected={unexpected}")
    for index, raw_row in enumerate(checks):
        row = _exact_mapping(raw_row, {
            "name", "status", "graded", "total", "findings", "evidence",
        }, f"verification.json.checks[{index}]")
        if not isinstance(row["status"], str) or \
                row["status"] not in CHECK_STATUSES:
            raise EnclosureError(
                f"verification check {row['name']} has invalid status")
        graded, total = row["graded"], row["total"]
        if any(isinstance(item, bool) or not isinstance(item, int)
               for item in (graded, total)) or total < 0 or not 0 <= graded <= total:
            raise EnclosureError(
                f"verification check {row['name']} has invalid denominator")
        if not isinstance(row["findings"], list) or any(
                not isinstance(item, str) for item in row["findings"]):
            raise EnclosureError(
                f"verification check {row['name']} has invalid findings")
        if not isinstance(row["evidence"], Mapping):
            raise EnclosureError(
                f"verification check {row['name']} has invalid evidence")
    summary = _exact_mapping(
        receipt["summary"], {"passed", "failed", "incomplete", "total"},
        "verification.json.summary")
    if any(isinstance(value, bool) or not isinstance(value, int)
           for value in summary.values()):
        raise EnclosureError("verification.json summary has invalid counts")
    expected_summary = {
        "passed": sum(row["status"] == "PASS" for row in checks),
        "failed": sum(row["status"] == "FAIL" for row in checks),
        "incomplete": sum(row["status"] == "INCOMPLETE" for row in checks),
        "total": len(checks),
    }
    if dict(summary) != expected_summary:
        raise EnclosureError(
            "verification.json summary disagrees with its seven-check census")


def _comparable_receipt(value: Mapping[str, Any]) -> dict[str, Any]:
    """Ignore display-only path spelling while comparing graded facts."""
    result = copy.deepcopy(dict(value))
    result["config"]["path"] = "<config>"
    physical = result["checks"][-1].get("evidence", {})
    if "evidence_path" in physical:
        physical["evidence_path"] = "<physical-evidence>"
    return result


def package(config_path: Path, root: Path, build_dir: Path, output: Path,
            allow_incomplete: bool) -> dict[str, Any]:
    config, loaded = load_bound_config(config_path, root)
    verification_path = build_dir / "verification.json"
    verification = load_json(verification_path)
    _validate_verification_receipt(verification)
    config_hash = semantic_sha256(config)
    if verification.get("config", {}).get("semantic_sha256") != config_hash or \
            verification.get("config", {}).get("raw_sha256") != sha256_file(config_path):
        raise EnclosureError("verification.json is stale for this config")
    status = verification.get("status")
    checks = verification.get("checks")
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
    if authored is not None and (
            installed_case_record.get("canonicalization") !=
            "ascii-stl-facet-order-v1" or any(
                row.get("canonicalization") != "ascii-stl-facet-order-v1"
                for row in part_records)):
        raise EnclosureError(
            "generation.json lacks canonical authored mesh identities")
    custom_parts = [part for part in config["cad"]["printable_parts"]
                    if part not in BUILT_IN_PRINTABLE_PARTS]
    selector_contract = generation.get("selector_contract")
    if custom_parts:
        expected_selector_contract = {
            "kind": "closed-authored-selectors-v1",
            "declared": config["cad"]["printable_parts"],
            "custom": custom_parts,
            "probe_selector": "__pcb_enclosure_unknown__",
            "mesh_canonicalization": "ascii-stl-facet-order-v1",
        }
        if not isinstance(selector_contract, dict) or any(
                selector_contract.get(key) != value
                for key, value in expected_selector_contract.items()) or \
                selector_contract.get("probe_result") not in {"EMPTY", "REJECTED"}:
            raise EnclosureError(
                "generation.json lacks the closed authored-selector contract")
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
    tolerance = clearance_evidence.get(
        "collision_volume_tolerance_mm3", 1e-4)
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) \
            or not math.isfinite(float(tolerance)) or tolerance < 0:
        raise EnclosureError(
            "verification.json has invalid collision-volume tolerance")
    reopened = regrade_workspace(
        config_path, root, build_dir, step_inspection_path, collision_path,
        collision_report_path, float(tolerance),
        physical_path if physical_path.is_file() else None)
    if _comparable_receipt(reopened) != _comparable_receipt(verification):
        raise EnclosureError(
            "verification.json does not match a fresh seven-check workspace regrade")
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
    package_inputs = tuple(row["path"] for row in entries if "path" in row)
    # Archive only private, identity-checked snapshots.  Hashing a live file
    # and reading it again later would let a concurrent mutation produce ZIP
    # bytes that disagree with the manifest census.
    with tempfile.TemporaryDirectory(
            prefix=".enclosure-package-snapshot-", dir=build_dir) as snapshot_dir:
        snapshot_entries = _snapshot_entries(entries, Path(snapshot_dir))
        with atomic_output(output, where="package output", root=build_dir,
                           inputs=package_inputs) as (temporary, stream):
            with zipfile.ZipFile(
                    stream, "w", compression=zipfile.ZIP_DEFLATED,
                    compresslevel=9) as archive:
                manifest_info = zipfile.ZipInfo("MANIFEST.json", ZIP_TIME)
                manifest_info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(
                    manifest_info,
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n")
                for row in snapshot_entries:
                    info = zipfile.ZipInfo(row["name"], ZIP_TIME)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o100644 << 16
                    payload = (read_stable_bytes(
                        row["path"], f"package snapshot {row['name']}")
                               if "path" in row else
                               row["data"])
                    archive.writestr(info, payload)
            stream.flush()
            os.fsync(stream.fileno())
            _verify_staged_zip(temporary, manifest, snapshot_entries)
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
