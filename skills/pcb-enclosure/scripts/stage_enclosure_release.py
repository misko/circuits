#!/usr/bin/env python3
"""Atomically publish a prepared workspace to 07_enclosure_releases.

This command only reads the selected PCB release.  It copies its manifest,
PCB, and STEP into the new enclosure release, writes a complete payload
census, reopens the staged tree with verify_enclosure_release.py, and uses a
Linux no-replace rename for the single publication step.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from datetime import date as Date
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

# Publication may be invoked from a prepared replay-tool closure.  Keep its
# imports read-only before taking the workspace snapshot so bytecode caches can
# neither mutate the source tree nor slip into the immutable payload census.
sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import enclosure_v2 as composition  # noqa: E402
import verify_enclosure_release as release_verify  # noqa: E402


WORKSPACE_ROOTS = {
    "README.md", "cad", "meshes", "package", "renders", "source",
    "tooling", "verification",
}


def _ordinary_file(path: Path, where: str) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as exc:
        raise release_verify.ReleaseError(f"{where}: cannot stat {path}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise release_verify.ReleaseError(f"{where}: expected ordinary file: {path}")
    if info.st_nlink != 1:
        raise release_verify.ReleaseError(f"{where}: hard-linked files are not accepted")
    return info


def _copy_regular(source: Path, destination: Path, where: str) -> dict[str, Any]:
    """Copy one no-link source to a new file, detecting a racing mutation."""
    before = _ordinary_file(source, where)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    source_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    input_fd = os.open(source, source_flags)
    output_fd: int | None = None
    try:
        opened = os.fstat(input_fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or \
                (opened.st_dev, opened.st_ino, opened.st_size) != \
                (before.st_dev, before.st_ino, before.st_size):
            raise release_verify.ReleaseError(f"{where}: source changed while opening")
        output_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                            0o644)
        digest = hashlib.sha256()
        size = 0
        while True:
            chunk = os.read(input_fd, 1024 * 1024)
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
        os.close(input_fd)
        if output_fd is not None:
            os.close(output_fd)
    after = _ordinary_file(source, where)
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != \
            (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
        raise release_verify.ReleaseError(f"{where}: source changed during copy")
    result = {"sha256": digest.hexdigest(), "size": size}
    if result["size"] != before.st_size or \
            release_verify.sha256_file(destination) != result["sha256"]:
        raise release_verify.ReleaseError(f"{where}: copied bytes did not verify")
    return result


def _write_json_exclusive(path: Path, value: Mapping[str, Any]) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _rename_noreplace_at(directory_fd: int, source_name: str,
                         destination_name: str) -> None:
    """Atomically rename below one locked directory without replacing."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise release_verify.ReleaseError(
            "atomic no-clobber publication needs Linux renameat2")
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                          ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    rename_noreplace = 1
    result = renameat2(directory_fd, os.fsencode(source_name), directory_fd,
                       os.fsencode(destination_name), rename_noreplace)
    if result != 0:
        error = ctypes.get_errno()
        if error in {errno.EEXIST, errno.ENOTEMPTY}:
            raise release_verify.ReleaseError(
                f"release destination already exists: {destination_name}")
        if error in {errno.ENOSYS, errno.EINVAL}:
            raise release_verify.ReleaseError(
                "filesystem cannot provide atomic no-clobber publication")
        raise OSError(error, os.strerror(error), destination_name)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_tree_directories(root: Path) -> None:
    directories = [Path(current) for current, _, _ in os.walk(root)]
    for directory in sorted(directories, key=lambda item: len(item.parts),
                            reverse=True):
        _fsync_directory(directory)


def _parse_scope(values: list[str]) -> dict[str, str]:
    scopes: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise release_verify.ReleaseError(
                f"scope {raw!r}: expected name=STATUS")
        name, value = raw.split("=", 1)
        if not release_verify.SCOPE_RE.fullmatch(name) or name in scopes:
            raise release_verify.ReleaseError(
                f"scope {name!r}: expected unique lowercase identifier")
        if value not in release_verify.STATUS_ORDER:
            raise release_verify.ReleaseError(f"scope {name!r}: unknown status {value!r}")
        scopes[name] = value
    if not scopes:
        raise release_verify.ReleaseError("at least one --scope is required")
    return dict(sorted(scopes.items()))


def _parse_replay_tools(values: list[str]) -> list[tuple[str, str]]:
    tools: list[tuple[str, str]] = []
    roles: set[str] = set()
    paths: set[str] = set()
    for raw in values:
        if "=" not in raw:
            raise release_verify.ReleaseError(
                f"replay tool {raw!r}: expected role=tooling/path")
        role, raw_path = raw.split("=", 1)
        if not release_verify.ROLE_RE.fullmatch(role) or role in roles:
            raise release_verify.ReleaseError(
                f"replay tool role {role!r}: expected unique lowercase identifier")
        path = release_verify.safe_rel(raw_path, f"replay tool {role}")
        if not path.startswith("tooling/") or path in paths:
            raise release_verify.ReleaseError(
                "replay tools must have unique release-local paths below tooling/")
        roles.add(role)
        paths.add(path)
        tools.append((role, path))
    if not tools:
        raise release_verify.ReleaseError("at least one --replay-tool is required")
    return sorted(tools)


def _validate_metadata(artifact_id: str, version: str, date_text: str,
                       status: str, scopes: Mapping[str, str],
                       candidate: bool, order_ready: bool) -> str:
    if not release_verify.ARTIFACT_RE.fullmatch(artifact_id):
        raise release_verify.ReleaseError(
            "artifact-id must be a lowercase filesystem-safe identifier")
    if not release_verify.SEMVER_RE.fullmatch(version):
        raise release_verify.ReleaseError("version must be SemVer (optional v prefix)")
    try:
        if Date.fromisoformat(date_text).isoformat() != date_text:
            raise ValueError
    except ValueError as exc:
        raise release_verify.ReleaseError("date must be a real YYYY-MM-DD date") from exc
    if status not in release_verify.STATUS_ORDER:
        raise release_verify.ReleaseError(f"unknown status {status!r}")
    aggregate = min(scopes.values(), key=lambda item: release_verify.STATUS_ORDER[item])
    if status != aggregate:
        raise release_verify.ReleaseError(
            f"overall status {status} must equal conservative scope aggregate {aggregate}")
    if status != "INCOMPLETE":
        raise release_verify.ReleaseError(
            "CAD_READY, PRINT_VERIFIED, and THERMALLY_VERIFIED publication is "
            "disabled until the release publisher can reopen a governing "
            "schema-v2 scope receipt and independently regrade its exact evidence")
    if any(value != "INCOMPLETE" for value in scopes.values()):
        raise release_verify.ReleaseError(
            "current candidate publication requires every declared scope to be "
            "INCOMPLETE; component-ready claims need the same future governing "
            "receipt and independent regrade")
    if not candidate or order_ready:
        raise release_verify.ReleaseError(
            "INCOMPLETE may publish only with --immutable-candidate and "
            "without --order-ready")
    return f"{version}-{date_text}"


def _workspace_census(workspace: Path) -> dict[str, os.stat_result]:
    files, _ = release_verify.scan_regular_tree(workspace)
    if "README.md" not in files:
        raise release_verify.ReleaseError("prepared workspace must contain README.md")
    if "MANIFEST.json" in files or any(
            PurePosixPath(path).parts[0] == "authorities" for path in files):
        raise release_verify.ReleaseError(
            "MANIFEST.json and authorities/ are publisher-owned paths")
    for path in files:
        if PurePosixPath(path).parts[0] not in WORKSPACE_ROOTS:
            raise release_verify.ReleaseError(
                f"prepared workspace has out-of-contract file: {path}")
    if not any(path.startswith("meshes/") and path.lower().endswith(".stl")
               for path in files):
        raise release_verify.ReleaseError(
            "prepared workspace must contain at least one meshes/*.stl")
    return files


def _source_record(parent_root: Path, relative: str, where: str) -> tuple[Path, dict[str, Any]]:
    normalized = release_verify.safe_rel(relative, where)
    path = release_verify.resolve_plain_relative(parent_root, normalized, where)
    info, digest = release_verify.stable_file_digest(path, where)
    return path, {
        "source_path": normalized,
        "release_path": f"authorities/pcb-release/{normalized}",
        "sha256": digest,
        "size": info.st_size,
    }


def _tree_snapshot(root: Path, files: Mapping[str, os.stat_result],
                   where: str) -> dict[str, dict[str, Any]]:
    """Bind one complete ordinary-file tree before copying it."""
    snapshot: dict[str, dict[str, Any]] = {}
    for relative in sorted(files):
        info, digest = release_verify.stable_file_digest(
            root / relative, f"{where} {relative}")
        snapshot[relative] = {
            "device": info.st_dev, "inode": info.st_ino,
            "size": info.st_size, "mtime_ns": info.st_mtime_ns,
            "sha256": digest,
        }
    return snapshot


def _record_for_release_file(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    info = _ordinary_file(path, f"release payload {relative}")
    return {"path": relative, "sha256": release_verify.sha256_file(path),
            "size": info.st_size}


def stage_release(args: argparse.Namespace) -> tuple[Path, dict[str, Any]]:
    project_root = release_verify._plain_directory(args.project_root, "project root")
    workspace = release_verify._plain_directory(args.workspace, "prepared workspace")
    workspace_files = _workspace_census(workspace)
    workspace_snapshot = _tree_snapshot(
        workspace, workspace_files, "prepared workspace file")
    workspace_abs = Path(os.path.abspath(workspace))
    project_abs = Path(os.path.abspath(project_root))
    pcb_stream = project_abs / "07_releases"
    release_verify._plain_directory(pcb_stream, "PCB release stream")
    enclosure_stream = project_abs / "07_enclosure_releases"
    if workspace_abs == pcb_stream or workspace_abs.is_relative_to(pcb_stream) or \
            workspace_abs == enclosure_stream or workspace_abs.is_relative_to(enclosure_stream):
        raise release_verify.ReleaseError(
            "prepared workspace must be outside immutable release streams")

    scopes = _parse_scope(args.scope)
    tools = _parse_replay_tools(args.replay_tool)
    if not args.status_reason.strip() or "\x00" in args.status_reason:
        raise release_verify.ReleaseError("--status-reason must be non-empty text")
    release_id = _validate_metadata(
        args.artifact_id, args.version, args.date, args.status, scopes,
        args.immutable_candidate, args.order_ready)
    replay_config = release_verify.safe_rel(args.replay_config, "replay config")
    if not replay_config.startswith("source/") or replay_config not in workspace_files:
        raise release_verify.ReleaseError(
            "--replay-config must name an ordinary prepared file below source/")
    for role, path in tools:
        if path not in workspace_files:
            raise release_verify.ReleaseError(
                f"replay tool {role!r} is absent from prepared workspace: {path}")

    if "/" in args.pcb_release or "\\" in args.pcb_release or \
            args.pcb_release in {"", ".", ".."}:
        raise release_verify.ReleaseError("--pcb-release must be one directory name")
    parent_project_path = f"07_releases/{args.pcb_release}"
    parent_root = release_verify.resolve_plain_relative(
        project_abs, parent_project_path, "parent PCB release")
    release_verify._plain_directory(parent_root, "parent PCB release")
    manifest_path, manifest_record = _source_record(
        parent_root, args.pcb_manifest, "parent PCB manifest")
    pcb_path, pcb_record = _source_record(parent_root, args.pcb, "parent PCB")
    step_path, step_record = _source_record(parent_root, args.step, "parent STEP")
    selected = [manifest_path.lstat(), pcb_path.lstat(), step_path.lstat()]
    if len({(row.st_dev, row.st_ino) for row in selected}) != 3:
        raise release_verify.ReleaseError(
            "parent manifest, PCB, and STEP must be distinct non-aliased files")
    release_verify.validate_parent_manifest(
        manifest_path, pcb_record["source_path"], pcb_record["sha256"],
        step_record["source_path"], step_record["sha256"])

    predecessor: dict[str, Any] | None = None
    predecessor_path: Path | None = None
    predecessor_root: Path | None = None
    if args.predecessor:
        if "/" in args.predecessor or "\\" in args.predecessor or \
                args.predecessor in {".", ".."}:
            raise release_verify.ReleaseError("--predecessor must be one release name")
        if args.predecessor == release_id:
            raise release_verify.ReleaseError("release cannot be its own predecessor")
        predecessor_project_path = f"07_enclosure_releases/{args.predecessor}"
        predecessor_root = release_verify.resolve_plain_relative(
            project_abs, predecessor_project_path, "enclosure predecessor")
        release_verify._plain_directory(predecessor_root, "enclosure predecessor")
        predecessor_result = release_verify.verify_release(
            predecessor_root, project_abs)
        if predecessor_result["artifact_id"] != args.artifact_id:
            raise release_verify.ReleaseError(
                "enclosure predecessor belongs to a different artifact stream")
        predecessor_path = release_verify.resolve_plain_relative(
            predecessor_root, release_verify.MANIFEST_NAME,
            "enclosure predecessor manifest")
        predecessor_info = _ordinary_file(
            predecessor_path, "enclosure predecessor manifest")
        predecessor = {
            "release_id": args.predecessor,
            "project_path": predecessor_project_path,
            "manifest": {
                "source_path": release_verify.MANIFEST_NAME,
                "release_path": "authorities/enclosure-predecessor/MANIFEST.json",
                "sha256": release_verify.sha256_file(predecessor_path),
                "size": predecessor_info.st_size,
            },
        }

    if not enclosure_stream.exists():
        raise release_verify.ReleaseError(
            "enclosure release stream is absent; first install the reviewed "
            "07_enclosure_releases/contracts.md contract")
    release_verify._plain_directory(enclosure_stream, "enclosure release stream")
    _ordinary_file(enclosure_stream / "contracts.md",
                   "enclosure release stream contract")
    stream_fd = os.open(
        enclosure_stream,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
        getattr(os, "O_NOFOLLOW", 0))
    stream_identity = os.fstat(stream_fd)
    fcntl.flock(stream_fd, fcntl.LOCK_EX)
    destination = enclosure_stream / release_id
    temporary: Path | None = None
    published = False
    try:
        wanted_key = release_verify.canonical_path_key(release_id)
        aliases = [name for name in os.listdir(stream_fd)
                   if release_verify.canonical_path_key(name) == wanted_key]
        if release_id in aliases:
            raise release_verify.ReleaseError(
                f"release destination already exists: {destination}")
        if aliases:
            raise release_verify.ReleaseError(
                f"release destination has a case/Unicode path collision: {aliases}")
        temporary = Path(tempfile.mkdtemp(
            prefix=f".{release_id}.staging-", dir=enclosure_stream))
        temporary.chmod(0o755)
        for relative in sorted(workspace_files):
            copied = _copy_regular(
                workspace / relative, temporary / relative,
                f"workspace file {relative}")
            expected = workspace_snapshot[relative]
            if copied != {key: expected[key] for key in ("sha256", "size")}:
                raise release_verify.ReleaseError(
                    f"workspace file {relative}: changed after initial census")
        for source, record, label in (
                (manifest_path, manifest_record, "parent PCB manifest"),
                (pcb_path, pcb_record, "parent PCB"),
                (step_path, step_record, "parent STEP")):
            copied = _copy_regular(
                source, temporary / record["release_path"], label)
            if copied != {key: record[key] for key in ("sha256", "size")}:
                raise release_verify.ReleaseError(
                    f"{label}: source identity changed before publication")
        if predecessor is not None and predecessor_path is not None:
            copied = _copy_regular(
                predecessor_path,
                temporary / predecessor["manifest"]["release_path"],
                "enclosure predecessor manifest")
            if copied != {key: predecessor["manifest"][key]
                          for key in ("sha256", "size")}:
                raise release_verify.ReleaseError(
                    "predecessor identity changed before publication")

        files, _ = release_verify.scan_regular_tree(temporary)
        payloads = [_record_for_release_file(temporary, relative)
                    for relative in sorted(files)]
        payload_by_path = {row["path"]: row for row in payloads}
        config_record = payload_by_path[replay_config]
        replay_tools = [
            {"role": role, **payload_by_path[path]} for role, path in tools
        ]
        try:
            replay_value = composition.load_yaml(temporary / replay_config)
            if not isinstance(replay_value, Mapping):
                raise release_verify.ReleaseError(
                    "release-local replay config must contain a YAML/JSON "
                    "object before shared connector replay is inspected")
            connector_replay = release_verify.validate_connector_replay_closure(
                temporary, replay_value, replay_tools, payload_by_path)
            fdm_replay = release_verify.validate_fdm_replay_closure(
                temporary, replay_value, replay_tools, payload_by_path,
                refresh_derived_reports=True)
            composition_loaded = composition.validate_config_v2(
                replay_value, temporary,
                release_connector_compiler=(
                    connector_replay["compiler_binding"]
                    if connector_replay is not None else None),
                release_fdm_compiler=(
                    fdm_replay["compiler_binding"]
                    if fdm_replay is not None else None),
                release_fdm_helper=(
                    fdm_replay["helper_binding"]
                    if fdm_replay is not None else None),
                release_collision_builder=(
                    fdm_replay["collision_builder_binding"]
                    if fdm_replay is not None else None),
                release_step_inspector=(
                    fdm_replay["step_inspector_binding"]
                    if fdm_replay is not None else None),
                release_process_runner=(
                    fdm_replay["process_runner_binding"]
                    if fdm_replay is not None else None),
                release_pipeline_runtime=(
                    fdm_replay["pipeline_runtime_binding"]
                    if fdm_replay is not None else None),
                release_collision_subject_validator=(
                    fdm_replay["collision_subject_validator_binding"]
                    if fdm_replay is not None else None))
        except (composition.V2Error, OSError) as exc:
            raise release_verify.ReleaseError(
                f"release-local schema-v2 config is invalid: {exc}") from exc
        required_scopes = composition.required_scope_closure(
            composition_loaded["scopes"])
        if set(scopes) != set(required_scopes):
            raise release_verify.ReleaseError(
                "declared release scopes differ from the validated schema-v2 "
                f"required scope census; expected={required_scopes}, "
                f"actual={sorted(scopes)}")
        if fdm_replay is not None:
            # Derived reports are products of the exact release-local closure,
            # not opaque workspace evidence. Rebuild them after every replay
            # and before the manifest census so staging paths never leak into
            # the immutable candidate.
            tools_by_role = {row["role"]: row for row in replay_tools}
            validator = release_verify._required_replay_tool(
                tools_by_role, release_verify.V2_VALIDATOR_ROLE,
                release_verify.V2_VALIDATOR_RELEASE_PATH,
                "schema-v2 validation compiler")
            validator_path = temporary / validator["path"]
            v2_report = composition.config_validation_report(
                replay_value, composition_loaded, temporary,
                validator_path=validator_path)
            intent_binding = composition_loaded["bindings"][
                "mechanical_intent"]
            intent_raw = composition.load_yaml(intent_binding["path"])
            intent_report = composition.mechanical_intent_validation_report(
                intent_raw)
            status_input = {"scope_statuses": dict(scopes)}
            scoped_report = composition.aggregate_config_report(
                status_input, composition_loaded)
            derived = {
                "verification/v2-validation.json": v2_report,
                "verification/mechanical-intent-validation-v2.json":
                    intent_report,
                "verification/scope-statuses.json": status_input,
                "verification/scoped-verdict.json": scoped_report,
            }
            for relative, report in derived.items():
                composition._write_or_print(
                    report, temporary / relative,
                    inputs=[temporary / replay_config,
                            intent_binding["path"], validator_path])

            # Every rewritten report changes its payload identity. Rebuild the
            # complete pre-manifest census and all records derived from it.
            files, _ = release_verify.scan_regular_tree(temporary)
            payloads = [_record_for_release_file(temporary, relative)
                        for relative in sorted(files)]
            payload_by_path = {row["path"]: row for row in payloads}
            config_record = payload_by_path[replay_config]
            replay_tools = [
                {"role": role, **payload_by_path[path]}
                for role, path in tools
            ]

        release_verify.validate_current_policy_derived_reports(
            temporary, replay_value, composition_loaded, replay_tools,
            payload_by_path, scopes, current_policy=fdm_replay is not None)

        manifest = {
            "schema": 2,
            "kind": release_verify.KIND,
            "artifact_id": args.artifact_id,
            "version": args.version,
            "date": args.date,
            "release_id": release_id,
            "lifecycle": ("immutable_candidate" if args.immutable_candidate
                          else "immutable_release"),
            "status": args.status,
            "status_reason": args.status_reason,
            "scopes": scopes,
            "publication": {
                "release": True,
                "immutable_candidate": args.immutable_candidate,
                "order_ready": args.order_ready,
            },
            "based_on": {
                "pcb_release": {
                    "release_id": args.pcb_release,
                    "project_path": parent_project_path,
                },
                "manifest": manifest_record,
                "pcb": pcb_record,
                "step": step_record,
            },
            "predecessor": predecessor,
            "replay": {
                "root": ".",
                "config": config_record,
                "tools": replay_tools,
            },
            "payload_count": len(payloads),
            "payloads": payloads,
        }
        _write_json_exclusive(temporary / release_verify.MANIFEST_NAME, manifest)
        sealed_files, _ = release_verify.scan_regular_tree(temporary)
        sealed_tree_snapshot = release_verify.regular_tree_content_snapshot(
            temporary, sealed_files, "sealed staging tree")
        release_verify.verify_release(
            temporary, project_abs, require_directory_name=False)
        # Reopen every mutable source name through the stable no-link seam.
        for record, label in (
                (manifest_record, "parent PCB manifest"),
                (pcb_record, "parent PCB"),
                (step_record, "parent STEP")):
            release_verify._match_file(
                parent_root, record, label, path_field="source_path")
        if predecessor is not None and predecessor_root is not None:
            release_verify._match_file(
                predecessor_root, predecessor["manifest"],
                "enclosure predecessor manifest", path_field="source_path")
        final_workspace_files = _workspace_census(workspace)
        final_workspace_snapshot = _tree_snapshot(
            workspace, final_workspace_files, "prepared workspace file")
        if final_workspace_snapshot != workspace_snapshot:
            raise release_verify.ReleaseError(
                "prepared workspace changed during release transaction")
        _fsync_tree_directories(temporary)
        current_stream = enclosure_stream.lstat()
        if (current_stream.st_dev, current_stream.st_ino) != \
                (stream_identity.st_dev, stream_identity.st_ino) or \
                not stat.S_ISDIR(current_stream.st_mode) or \
                stat.S_ISLNK(current_stream.st_mode):
            raise release_verify.ReleaseError(
                "enclosure release stream path changed during publication")
        aliases = [name for name in os.listdir(stream_fd)
                   if name != temporary.name and
                   release_verify.canonical_path_key(name) == wanted_key]
        if release_id in aliases:
            raise release_verify.ReleaseError(
                f"release destination already exists: {destination}")
        if aliases:
            raise release_verify.ReleaseError(
                f"release destination has a case/Unicode path collision: {aliases}")
        final_staged_files, _ = release_verify.scan_regular_tree(temporary)
        final_staged_snapshot = release_verify.regular_tree_content_snapshot(
            temporary, final_staged_files, "final staging tree")
        if final_staged_snapshot != sealed_tree_snapshot:
            initial_paths = set(sealed_tree_snapshot)
            final_paths = set(final_staged_snapshot)
            changed = sorted(
                path for path in initial_paths & final_paths
                if sealed_tree_snapshot[path] != final_staged_snapshot[path])
            raise release_verify.ReleaseError(
                "staged release tree changed after verification; "
                f"missing={sorted(initial_paths - final_paths)}, "
                f"extras={sorted(final_paths - initial_paths)}, "
                f"changed={changed}")
        _rename_noreplace_at(stream_fd, temporary.name, release_id)
        published = True
        _fsync_directory(enclosure_stream)
    finally:
        if not published and temporary is not None and temporary.exists():
            shutil.rmtree(temporary)
        fcntl.flock(stream_fd, fcntl.LOCK_UN)
        os.close(stream_fd)

    return destination, manifest


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path,
                        help="prepared release payload (without authorities/manifest)")
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--pcb-release", required=True,
                        help="one existing 07_releases directory name")
    parser.add_argument("--pcb-manifest", required=True,
                        help="path relative to the selected PCB release")
    parser.add_argument("--pcb", required=True,
                        help=".kicad_pcb path relative to the PCB release")
    parser.add_argument("--step", required=True,
                        help="STEP path relative to the PCB release")
    parser.add_argument("--status", required=True,
                        choices=tuple(release_verify.STATUS_ORDER))
    parser.add_argument("--status-reason", required=True)
    parser.add_argument("--scope", action="append", default=[],
                        metavar="NAME=STATUS")
    parser.add_argument("--replay-config", required=True,
                        help="prepared release-local source/... config path")
    parser.add_argument("--replay-tool", action="append", default=[],
                        metavar="ROLE=TOOLING/PATH")
    parser.add_argument("--predecessor",
                        help="optional exact 07_enclosure_releases predecessor")
    parser.add_argument("--immutable-candidate", action="store_true",
                        help="required for publishing status INCOMPLETE")
    parser.add_argument("--order-ready", action="store_true",
                        help="reserved for a future governing-regrade publisher; "
                             "currently rejected")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        destination, manifest = stage_release(args)
    except (OSError, release_verify.ReleaseError) as exc:
        print(f"ENCLOSURE RELEASE ERROR — {args.workspace}: {exc}", file=sys.stderr)
        return 1
    print(
        f"ENCLOSURE RELEASE PUBLISHED — {manifest['release_id']} — "
        f"status={manifest['status']}, files={manifest['payload_count']}/"
        f"{manifest['payload_count']}, order_ready="
        f"{str(manifest['publication']['order_ready']).lower()}")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
