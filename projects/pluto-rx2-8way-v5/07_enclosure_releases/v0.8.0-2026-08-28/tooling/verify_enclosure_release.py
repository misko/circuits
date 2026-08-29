#!/usr/bin/env python3
"""Reopen and verify an immutable pcb-enclosure release directory.

The release is self-contained for integrity checking: every ordinary file
except MANIFEST.json is in the manifest census, PCB authorities are copied
into the release, and replay inputs resolve to release-local files. Hashes are
not origin authentication. ``--project-root`` additionally
checks that the live parent PCB release and optional enclosure predecessor
still have the exact bytes bound at publication time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
import unicodedata
from datetime import date as Date
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

# Verification must be read-only with respect to the release even when this
# script itself is executed from release-local ``tooling/``.  Set the runtime
# flag before importing any sibling replay module; caller environment and
# ``python -B`` are useful defense in depth, but are not part of the contract.
sys.dont_write_bytecode = True

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("pcb-enclosure release verification needs PyYAML") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import enclosure_v2 as composition  # noqa: E402


KIND = "pcb-enclosure-release-v2"
MANIFEST_NAME = "MANIFEST.json"
STATUS_ORDER = {
    "INCOMPLETE": 0,
    "CAD_READY": 1,
    "PRINT_VERIFIED": 2,
    "THERMALLY_VERIFIED": 3,
}
SEMVER_RE = re.compile(
    r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
ARTIFACT_RE = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
SCOPE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
ROLE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_PAYLOAD_ROOTS = {
    "README.md", "authorities", "cad", "meshes", "package", "renders",
    "source", "tooling", "verification",
}
CONNECTOR_COMPILER_ROLE = composition.CONNECTOR_COMPILER_ROLE
CONNECTOR_COMPILER_RELEASE_PATH = composition.CONNECTOR_COMPILER_RELEASE_PATH
CONNECTOR_COMPILER_SOURCE_PATH = composition.CONNECTOR_COMPILER_SOURCE_PATH
CONNECTOR_REPLAY_ROOT = composition.CONNECTOR_RELEASE_PROJECT_ROOT
FDM_AUDIT_COMPILER_ROLE = composition.FDM_AUDIT_COMPILER_ROLE
FDM_AUDIT_COMPILER_RELEASE_PATH = composition.FDM_AUDIT_COMPILER_RELEASE_PATH
FDM_AUDIT_COMPILER_SOURCE_PATH = composition.FDM_AUDIT_COMPILER_SOURCE_PATH
COLLISION_BUILDER_ROLE = composition.COLLISION_BUILDER_ROLE
COLLISION_BUILDER_RELEASE_PATH = composition.COLLISION_BUILDER_RELEASE_PATH
COLLISION_BUILDER_SOURCE_PATH = composition.COLLISION_BUILDER_SOURCE_PATH
STEP_INSPECTOR_ROLE = composition.STEP_INSPECTOR_ROLE
STEP_INSPECTOR_RELEASE_PATH = composition.STEP_INSPECTOR_RELEASE_PATH
STEP_INSPECTOR_SOURCE_PATH = composition.STEP_INSPECTOR_SOURCE_PATH
ENCLOSURE_GENERATOR_ROLE = "enclosure_generator"
ENCLOSURE_GENERATOR_RELEASE_PATH = "tooling/generate_enclosure.py"
ENCLOSURE_GENERATOR_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/generate_enclosure.py")
PROCESS_RUNNER_ROLE = "process_runner"
PROCESS_RUNNER_RELEASE_PATH = "tooling/process_runner.py"
PROCESS_RUNNER_SOURCE_PATH = composition.PROCESS_RUNNER_SOURCE_PATH
PIPELINE_RUNTIME_ROLE = "pipeline_runtime"
PIPELINE_RUNTIME_RELEASE_PATH = "tooling/pipeline_runtime.py"
PIPELINE_RUNTIME_SOURCE_PATH = composition.PIPELINE_RUNTIME_SOURCE_PATH
V2_VALIDATOR_ROLE = composition.V2_VALIDATOR_ROLE
V2_VALIDATOR_RELEASE_PATH = composition.V2_VALIDATOR_RELEASE_PATH
V2_VALIDATOR_SOURCE_PATH = composition.V2_VALIDATOR_SOURCE_PATH
GENERIC_VERIFIER_ROLE = "verify"
GENERIC_VERIFIER_RELEASE_PATH = "tooling/verify_enclosure.py"
GENERIC_VERIFIER_SOURCE_PATH = (
    "skills/pcb-enclosure/scripts/verify_enclosure.py")
OBSTRUCTION_COMPOSITOR_ROLE = "obstruction_compositor"
OBSTRUCTION_COMPOSITOR_RELEASE_PATH = (
    "tooling/compose_obstruction_step.py")


class ReleaseError(ValueError):
    """The release is incomplete, contradictory, or not immutable."""


class _StrictYamlLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_yaml_mapping(loader: _StrictYamlLoader, node: yaml.MappingNode,
                            deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise ReleaseError("replay-config mapping keys must be scalar") from exc
        if duplicate:
            raise ReleaseError(
                f"duplicate replay-config key {key!r} at line "
                f"{key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictYamlLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_yaml_mapping)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def stable_file_digest(path: Path, where: str) -> tuple[os.stat_result, str]:
    """Hash one ordinary descriptor and prove its path stayed identical."""
    try:
        before = path.lstat()
    except OSError as exc:
        raise ReleaseError(f"{where}: cannot stat {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
        raise ReleaseError(f"{where}: expected ordinary file")
    if before.st_nlink != 1:
        raise ReleaseError(f"{where}: hard-linked files are not accepted")
    expected = (before.st_dev, before.st_ino, before.st_size,
                before.st_mtime_ns)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    digest = hashlib.sha256()
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1 or \
                (opened.st_dev, opened.st_ino, opened.st_size,
                 opened.st_mtime_ns) != expected:
            raise ReleaseError(f"{where}: file changed while opening")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        finished = os.fstat(descriptor)
        if (finished.st_dev, finished.st_ino, finished.st_size,
                finished.st_mtime_ns) != expected:
            raise ReleaseError(f"{where}: file changed while reading")
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as exc:
        raise ReleaseError(f"{where}: path changed after reading: {exc}") from exc
    if not stat.S_ISREG(after.st_mode) or stat.S_ISLNK(after.st_mode) or \
            after.st_nlink != 1 or \
            (after.st_dev, after.st_ino, after.st_size,
             after.st_mtime_ns) != expected:
        raise ReleaseError(f"{where}: path changed while reading")
    return before, digest.hexdigest()


def sha256_file(path: Path) -> str:
    return stable_file_digest(path, f"file {path}")[1]


def stable_file_bytes(path: Path, where: str) -> bytes:
    """Read parseable authority bytes while retaining stable path identity."""
    info, expected_digest = stable_file_digest(path, where)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size,
                opened.st_mtime_ns) != \
                (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
            raise ReleaseError(f"{where}: file changed before parsing")
        payload = bytearray()
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload.extend(chunk)
    finally:
        os.close(descriptor)
    final_info, final_digest = stable_file_digest(path, where)
    if len(payload) != info.st_size or \
            hashlib.sha256(payload).hexdigest() != expected_digest or \
            (final_info.st_dev, final_info.st_ino, final_info.st_size,
             final_info.st_mtime_ns, final_digest) != \
            (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
             expected_digest):
        raise ReleaseError(f"{where}: file changed while parsing")
    return bytes(payload)


def load_json_strict(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            stable_file_bytes(path, f"JSON file {path}").decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"{path}: expected JSON object")
    return value


def _exact(value: Any, fields: Iterable[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReleaseError(f"{where}: expected object")
    expected = set(fields)
    actual = set(value)
    if actual != expected:
        raise ReleaseError(
            f"{where}: fields differ; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}")
    return value


def _string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ReleaseError(f"{where}: expected non-empty string")
    return value


def _boolean(value: Any, where: str) -> bool:
    if not isinstance(value, bool):
        raise ReleaseError(f"{where}: expected boolean")
    return value


def _integer(value: Any, where: str, *, nonnegative: bool = True) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReleaseError(f"{where}: expected integer")
    if nonnegative and value < 0:
        raise ReleaseError(f"{where}: expected nonnegative integer")
    return value


def _status(value: Any, where: str) -> str:
    result = _string(value, where)
    if result not in STATUS_ORDER:
        raise ReleaseError(f"{where}: unknown status {result!r}")
    return result


def safe_rel(value: Any, where: str) -> str:
    """Return one normalized, traversal-free POSIX relative path."""
    text = _string(value, where)
    if "\\" in text or unicodedata.normalize("NFC", text) != text:
        raise ReleaseError(f"{where}: path must be NFC POSIX form")
    path = PurePosixPath(text)
    if path.is_absolute() or str(path) != text or any(
            part in {"", ".", ".."} for part in path.parts):
        raise ReleaseError(
            f"{where}: path must be normalized, relative, and traversal-free")
    return text


def canonical_path_key(path: str) -> str:
    return unicodedata.normalize("NFC", path).casefold()


def _binding(value: Any, where: str, *, with_source: bool = False) -> dict[str, Any]:
    fields = {"path", "sha256", "size"}
    if with_source:
        fields = {"source_path", "release_path", "sha256", "size"}
    item = _exact(value, fields, where)
    if with_source:
        source_path = safe_rel(item["source_path"], f"{where}.source_path")
        release_path = safe_rel(item["release_path"], f"{where}.release_path")
        result = {"source_path": source_path, "release_path": release_path}
    else:
        result = {"path": safe_rel(item["path"], f"{where}.path")}
    digest = _string(item["sha256"], f"{where}.sha256")
    if not HEX64_RE.fullmatch(digest):
        raise ReleaseError(f"{where}.sha256: expected lowercase 64-hex")
    result.update({"sha256": digest,
                   "size": _integer(item["size"], f"{where}.size")})
    return result


def _plain_directory(path: Path, where: str) -> Path:
    absolute = Path(os.path.abspath(path))
    cursor = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except OSError as exc:
            raise ReleaseError(
                f"{where}: cannot inspect directory path {cursor}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ReleaseError(f"{where}: symlink directory paths are not accepted")
    if not absolute.is_dir():
        raise ReleaseError(f"{where}: expected ordinary directory: {absolute}")
    return absolute


def resolve_plain_relative(root: Path, relative: str, where: str) -> Path:
    """Resolve a path while preserving evidence of every symlink component."""
    cursor = root
    if cursor.is_symlink() or not cursor.is_dir():
        raise ReleaseError(f"{where}: root is not an ordinary directory")
    for index, part in enumerate(PurePosixPath(relative).parts):
        cursor = cursor / part
        try:
            mode = cursor.lstat().st_mode
        except OSError as exc:
            raise ReleaseError(f"{where}: missing path {cursor}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise ReleaseError(f"{where}: symlink paths are not accepted")
        if index < len(PurePosixPath(relative).parts) - 1 and not stat.S_ISDIR(mode):
            raise ReleaseError(f"{where}: non-directory path component {cursor}")
    return cursor


def scan_regular_tree(root: Path) -> tuple[dict[str, os.stat_result], set[str]]:
    """Census a tree, rejecting links, special files, aliases, and empty dirs."""
    _plain_directory(root, "release")
    files: dict[str, os.stat_result] = {}
    directories: set[str] = set()
    inodes: dict[tuple[int, int], str] = {}
    canonical: dict[str, str] = {}
    for current_text, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(current_text)
        dirnames.sort()
        filenames.sort()
        for dirname in dirnames:
            path = current / dirname
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ReleaseError(f"release contains linked/special directory: {relative}")
            key = canonical_path_key(relative)
            if key in canonical:
                raise ReleaseError(
                    f"release path collision: {canonical[key]!r} and {relative!r}")
            canonical[key] = relative
            directories.add(relative)
        for filename in filenames:
            path = current / filename
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                raise ReleaseError(f"release contains linked/special file: {relative}")
            if info.st_nlink != 1:
                raise ReleaseError(f"release contains hard-linked file: {relative}")
            inode = (info.st_dev, info.st_ino)
            if inode in inodes:
                raise ReleaseError(
                    f"release files share an inode: {inodes[inode]!r} and {relative!r}")
            inodes[inode] = relative
            key = canonical_path_key(relative)
            if key in canonical:
                raise ReleaseError(
                    f"release path collision: {canonical[key]!r} and {relative!r}")
            canonical[key] = relative
            files[relative] = info
    needed_dirs = {
        parent.as_posix()
        for relative in files
        for parent in PurePosixPath(relative).parents
        if parent != PurePosixPath(".")
    }
    extras = directories - needed_dirs
    if extras:
        raise ReleaseError(f"release contains empty/extra directories: {sorted(extras)}")
    return files, directories


def regular_tree_content_snapshot(
        root: Path, files: Mapping[str, os.stat_result],
        where: str) -> dict[str, dict[str, Any]]:
    """Bind an already-scanned tree to exact path, size, and content bytes."""
    result: dict[str, dict[str, Any]] = {}
    for relative in sorted(files):
        scanned = files[relative]
        current, digest = stable_file_digest(root / relative,
                                             f"{where} {relative}")
        if (current.st_dev, current.st_ino, current.st_size,
                current.st_mtime_ns) != \
                (scanned.st_dev, scanned.st_ino, scanned.st_size,
                 scanned.st_mtime_ns):
            raise ReleaseError(
                f"{where}: tree changed after census at {relative}")
        result[relative] = {"sha256": digest, "size": current.st_size}
    return result


def _declared_subject_hashes(manifest_path: Path) -> dict[str, str]:
    """Extract path/hash pairs from JSON or conventional MANIFEST.txt."""
    pairs: dict[str, str] = {}

    def add(path_value: Any, hash_value: Any) -> None:
        if not isinstance(path_value, str) or not isinstance(hash_value, str):
            return
        try:
            normalized = safe_rel(path_value, "PCB manifest subject path")
        except ReleaseError:
            return
        if not HEX64_RE.fullmatch(hash_value):
            return
        previous = pairs.get(normalized)
        if previous is not None and previous != hash_value:
            raise ReleaseError(
                f"PCB manifest contradicts itself for {normalized!r}")
        pairs[normalized] = hash_value

    try:
        if manifest_path.suffix.lower() == ".json":
            root: Any = load_json_strict(manifest_path)

            def walk(value: Any) -> None:
                if isinstance(value, Mapping):
                    path_value = value.get("path", value.get("name"))
                    add(path_value, value.get("sha256"))
                    for child in value.values():
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)

            walk(root)
        else:
            for line in stable_file_bytes(
                    manifest_path, "PCB release manifest").decode(
                        "utf-8").splitlines():
                path_first = re.match(
                    r"^\s*(\S+)\s+([0-9a-f]{64})\s*$", line)
                hash_first = re.match(
                    r"^\s*([0-9a-f]{64})\s+[ *]?(.+?)\s*$", line)
                if path_first:
                    add(path_first.group(1), path_first.group(2))
                elif hash_first:
                    add(hash_first.group(2), hash_first.group(1))
    except (OSError, UnicodeError) as exc:
        raise ReleaseError(f"cannot inspect PCB manifest {manifest_path}: {exc}") from exc
    return pairs


def validate_parent_manifest(manifest_path: Path, pcb_source: str,
                             pcb_digest: str, step_source: str,
                             step_digest: str) -> None:
    declared = _declared_subject_hashes(manifest_path)
    for label, path, digest in (
            ("PCB", pcb_source, pcb_digest), ("STEP", step_source, step_digest)):
        if declared.get(path) != digest:
            raise ReleaseError(
                f"parent PCB manifest does not bind selected {label} {path!r} "
                f"to {digest}")


def _match_file(root: Path, record: Mapping[str, Any], where: str,
                *, path_field: str = "path") -> Path:
    relative = record[path_field]
    path = resolve_plain_relative(root, relative, where)
    info, digest = stable_file_digest(path, where)
    if info.st_size != record["size"] or digest != record["sha256"]:
        raise ReleaseError(f"{where}: bound size/hash differs from actual file")
    return path


def _same_record(left: Mapping[str, Any], right: Mapping[str, Any],
                 left_path: str, right_path: str) -> bool:
    return (left[left_path] == right[right_path]
            and left["sha256"] == right["sha256"]
            and left["size"] == right["size"])


def validate_replay_config(
        release_dir: Path, config_record: Mapping[str, Any],
        authority: Mapping[str, Mapping[str, Any]],
        payload_by_path: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Require every file binding in the replay config to resolve locally."""
    config_path = _match_file(
        release_dir, config_record, "release-local replay config")
    try:
        config = yaml.load(stable_file_bytes(
            config_path, "release-local replay config").decode("utf-8"),
                           Loader=_StrictYamlLoader)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ReleaseError(f"cannot parse replay config {config_path}: {exc}") from exc
    if not isinstance(config, Mapping):
        raise ReleaseError("replay config must contain a YAML/JSON object")
    bindings: dict[str, dict[str, Any]] = {}
    active_containers: set[int] = set()

    def walk(value: Any, where: str) -> None:
        if isinstance(value, Mapping):
            identity = id(value)
            if identity in active_containers:
                raise ReleaseError("replay config contains a cyclic YAML alias")
            active_containers.add(identity)
            try:
                if {"path", "sha256", "size"}.issubset(value):
                    record = _binding(
                        {key: value[key] for key in ("path", "sha256", "size")},
                        f"replay config {where}")
                    payload = payload_by_path.get(record["path"])
                    if payload is None or not _same_record(
                            record, payload, "path", "path"):
                        raise ReleaseError(
                            f"replay config {where}: file binding does not resolve "
                            "to an exact release payload")
                    bindings[where] = record
                for key, child in value.items():
                    walk(child, f"{where}.{key}")
            finally:
                active_containers.remove(identity)
        elif isinstance(value, list):
            identity = id(value)
            if identity in active_containers:
                raise ReleaseError("replay config contains a cyclic YAML alias")
            active_containers.add(identity)
            try:
                for index, child in enumerate(value):
                    walk(child, f"{where}[{index}]")
            finally:
                active_containers.remove(identity)

    walk(config, "$")
    required = {
        name: {
            "path": record["release_path"], "sha256": record["sha256"],
            "size": record["size"],
        }
        for name, record in authority.items()
    }
    resolved_values = list(bindings.values())
    missing = [name for name, expected in required.items()
               if expected not in resolved_values]
    if missing:
        raise ReleaseError(
            "replay config does not bind release-local parent authorities: "
            f"{missing}")
    return {"binding_count": len(bindings),
            "authority_bindings": sorted(required)}


def validate_connector_replay_closure(
        release_dir: Path, config: Mapping[str, Any],
        replay_tools: Sequence[Mapping[str, Any]],
        payload_by_path: Mapping[str, Mapping[str, Any]],
        ) -> dict[str, Any] | None:
    """Reopen the exact receipt-owned connector replay closure.

    Receipt paths remain byte-for-byte project-relative source identities.  A
    release mirrors those inputs beneath one fixed virtual project root; no
    config or manifest field gets to choose another root.  The compiler path is
    similarly virtualized only through one exact manifest tool role/path while
    its hash and size must equal the receipt's canonical source binding.
    """
    if "interface_assemblies" not in config:
        return None
    interface_assemblies = config["interface_assemblies"]
    if not isinstance(interface_assemblies, Mapping):
        raise ReleaseError("config.interface_assemblies: expected object")
    receipt_raw = interface_assemblies.get("receipt")
    receipt_binding = _binding(
        receipt_raw, "config.interface_assemblies.receipt")
    if not receipt_binding["path"].startswith("verification/"):
        raise ReleaseError(
            "shared connector receipt must be release-local below verification/")
    receipt_payload = payload_by_path.get(receipt_binding["path"])
    if receipt_payload is None or not _same_record(
            receipt_binding, receipt_payload, "path", "path"):
        raise ReleaseError(
            "shared connector receipt binding does not match the payload census")
    receipt_path = _match_file(
        release_dir, receipt_binding, "release-local connector receipt")
    receipt = load_json_strict(receipt_path)
    inputs = _exact(receipt.get("inputs"), {
        "contract", "compiler", "evidence_files",
    }, "connector receipt.inputs")
    contract = _binding(inputs["contract"],
                        "connector receipt.inputs.contract")
    compiler_source = _binding(inputs["compiler"],
                               "connector receipt.inputs.compiler")
    if compiler_source["path"] != CONNECTOR_COMPILER_SOURCE_PATH:
        raise ReleaseError(
            "connector receipt compiler path differs from the canonical "
            f"source identity {CONNECTOR_COMPILER_SOURCE_PATH!r}")

    tools_by_role = {row["role"]: row for row in replay_tools}
    compiler_tool = tools_by_role.get(CONNECTOR_COMPILER_ROLE)
    if compiler_tool is None:
        raise ReleaseError(
            "shared connector replay requires manifest tool role "
            f"{CONNECTOR_COMPILER_ROLE!r}")
    if compiler_tool["path"] != CONNECTOR_COMPILER_RELEASE_PATH:
        raise ReleaseError(
            f"manifest tool role {CONNECTOR_COMPILER_ROLE!r} must bind exact "
            f"path {CONNECTOR_COMPILER_RELEASE_PATH!r}")
    if (compiler_tool["sha256"], compiler_tool["size"]) != \
            (compiler_source["sha256"], compiler_source["size"]):
        raise ReleaseError(
            "manifest-bound connector compiler differs from the exact "
            "compiler identity recorded by the receipt")

    evidence_raw = inputs["evidence_files"]
    if not isinstance(evidence_raw, list):
        raise ReleaseError("connector receipt.inputs.evidence_files: expected list")
    evidence: list[dict[str, Any]] = []
    for index, raw in enumerate(evidence_raw):
        where = f"connector receipt.inputs.evidence_files[{index}]"
        row = _exact(raw, {"id", "kind", "path", "sha256", "size"}, where)
        _string(row["id"], f"{where}.id")
        _string(row["kind"], f"{where}.kind")
        evidence.append(_binding({
            key: row[key] for key in ("path", "sha256", "size")
        }, where))

    original_bindings = [("contract", contract), *[
        (f"evidence file {index}", row)
        for index, row in enumerate(evidence)
    ]]
    original_paths: dict[str, str] = {}
    canonical_original_paths: dict[str, str] = {}
    expected_closure_files: set[str] = set()
    for label, record in original_bindings:
        original = record["path"]
        canonical = canonical_path_key(original)
        if original in original_paths or canonical in canonical_original_paths:
            previous = original_paths.get(
                original, canonical_original_paths.get(canonical, "unknown"))
            raise ReleaseError(
                f"connector replay inputs alias one source path: {previous!r} "
                f"and {label!r}")
        original_paths[original] = label
        canonical_original_paths[canonical] = label
        release_path = f"{CONNECTOR_REPLAY_ROOT}/{original}"
        payload = payload_by_path.get(release_path)
        expected = {
            "path": release_path, "sha256": record["sha256"],
            "size": record["size"],
        }
        if payload is None or not _same_record(
                expected, payload, "path", "path"):
            raise ReleaseError(
                f"release-local connector {label} does not match the exact "
                "receipt binding")
        _match_file(release_dir, expected,
                    f"release-local connector {label}")
        expected_closure_files.add(original)

    connector_root = resolve_plain_relative(
        release_dir, CONNECTOR_REPLAY_ROOT,
        "release-local connector virtual project root")
    closure_files, _ = scan_regular_tree(connector_root)
    if set(closure_files) != expected_closure_files:
        raise ReleaseError(
            "connector replay closure census differs from receipt inputs; "
            f"missing={sorted(expected_closure_files - set(closure_files))}, "
            f"extras={sorted(set(closure_files) - expected_closure_files)}")

    return {
        "receipt": receipt_binding["path"],
        "compiler_role": CONNECTOR_COMPILER_ROLE,
        "compiler": compiler_tool["path"],
        "virtual_project_root": CONNECTOR_REPLAY_ROOT,
        "contract": contract["path"],
        "evidence_files": [row["path"] for row in evidence],
        "compiler_binding": {
            "path": compiler_tool["path"],
            "sha256": compiler_tool["sha256"],
            "size": compiler_tool["size"],
        },
    }


def _validate_fdm_generation_evidence_closure(
        release_dir: Path, generation_record: Mapping[str, Any],
        collision_record: Mapping[str, Any],
        payload_by_path: Mapping[str, Mapping[str, Any]],
        ) -> dict[str, Any]:
    """Require printable and selected collision evidence to share generation."""
    generation_path = _match_file(
        release_dir, generation_record, "manufacturing generation receipt")
    generation = load_json_strict(generation_path)
    if generation.get("schema") != 1 or \
            generation.get("kind") != "pcb-enclosure-generation-v1":
        raise ReleaseError(
            "manufacturing generation receipt has wrong schema/kind")
    installed_case = generation.get("installed_case")
    if not isinstance(installed_case, Mapping):
        raise ReleaseError(
            "manufacturing generation lacks installed_case evidence")
    local_generation = {
        "path": PurePosixPath(generation_record["path"]).name,
        "sha256": generation_record["sha256"],
        "size": generation_record["size"],
    }

    verification_path = "verification/verification.json"
    verification_record = payload_by_path.get(verification_path)
    if verification_record is None:
        raise ReleaseError(
            "current-policy FDM release lacks verification/verification.json")
    verification = load_json_strict(_match_file(
        release_dir, verification_record, "generic verification receipt"))
    if verification.get("kind") != "pcb-enclosure-verification-v1":
        raise ReleaseError("generic verification receipt has wrong kind")
    checks = verification.get("checks")
    if not isinstance(checks, list) or any(
            not isinstance(row, Mapping) for row in checks):
        raise ReleaseError("generic verification receipt lacks its check census")
    by_name = {row.get("name"): row for row in checks}
    if len(by_name) != len(checks):
        raise ReleaseError("generic verification receipt has duplicate check names")
    printable = by_name.get("printable_meshes")
    if not isinstance(printable, Mapping):
        raise ReleaseError(
            "generic verification receipt lacks printable_meshes check")
    printable_evidence = printable.get("evidence")
    if not isinstance(printable_evidence, Mapping):
        raise ReleaseError("generic verification printable_meshes lacks evidence")
    printable_generation = _binding(
        printable_evidence.get("generation_file"),
        "generic verification printable_meshes.generation_file")
    if printable_generation != local_generation:
        raise ReleaseError(
            "generic verification printable_meshes binds a different "
            "generation receipt than manufacturing_audit")

    # Generic parent-STEP clearance may honestly FAIL when a governing
    # supplemental obstruction STEP is audited separately.  If the generic
    # check carries generation evidence, cross-check only that identity; its
    # presence or PASS status is not manufacturing collision authority.
    generic_clearance = by_name.get("exact_solid_clearance")
    if generic_clearance is not None:
        if not isinstance(generic_clearance, Mapping):
            raise ReleaseError(
                "generic verification exact_solid_clearance check is malformed")
        generic_evidence = generic_clearance.get("evidence")
        if not isinstance(generic_evidence, Mapping):
            raise ReleaseError(
                "generic verification exact_solid_clearance lacks evidence")
        generic_generation = generic_evidence.get("generation_file")
        if generic_generation is not None and _binding(
                generic_generation,
                "generic verification exact_solid_clearance.generation_file") != \
                local_generation:
            raise ReleaseError(
                "generic verification exact_solid_clearance binds a different "
                "generation receipt than manufacturing_audit")

    collision_relative = collision_record["path"]
    if not collision_relative.startswith("verification/"):
        raise ReleaseError(
            "manufacturing collision must be release-local below verification/")
    collision_payload = payload_by_path.get(collision_relative)
    if collision_payload is None or not _same_record(
            collision_record, collision_payload, "path", "path"):
        raise ReleaseError(
            "manufacturing collision differs from payload census")
    collision = load_json_strict(_match_file(
        release_dir, collision_record, "selected manufacturing collision"))
    _exact(collision, {
        "schema", "kind", "status", "builder", "enclosure_common",
        "step_inspector", "process_runner", "pipeline_runtime", "backend",
        "inputs", "transform", "selection", "result",
    }, "selected manufacturing collision")
    if collision.get("schema") != 1 or collision.get("kind") != \
            "pcb-enclosure-collision-v1":
        raise ReleaseError(
            "selected manufacturing collision has wrong schema/kind")
    if collision.get("status") != "COMPLETE":
        raise ReleaseError(
            "selected manufacturing collision must be COMPLETE")
    collision_inputs = collision.get("inputs")
    if not isinstance(collision_inputs, Mapping):
        raise ReleaseError(
            "selected manufacturing collision lacks input identities")
    collision_generation = _binding(
        collision_inputs.get("generation"),
        "selected manufacturing collision generation")
    if collision_generation != local_generation:
        raise ReleaseError(
            "selected manufacturing collision binds a different generation "
            "receipt than manufacturing_audit")
    if collision_inputs.get("assembled_case_mesh") != installed_case:
        raise ReleaseError(
            "selected manufacturing collision assembled case differs from "
            "the manufacturing generation")
    collision_result = collision.get("result")
    if not isinstance(collision_result, Mapping):
        raise ReleaseError(
            "selected manufacturing collision lacks result evidence")
    volume = collision_result.get("exact_brep_volume_mm3")
    if collision_result.get("classification") != "EMPTY" or \
            isinstance(volume, bool) or not isinstance(volume, (int, float)) or \
            not math.isfinite(volume) or volume != 0:
        raise ReleaseError(
            "selected manufacturing collision must prove EMPTY exact BRep "
            "intersection with zero volume")
    return {
        "generation": generation_record["path"],
        "verification": verification_path,
        "collision": collision_relative,
    }


def _required_replay_tool(
        tools_by_role: Mapping[str, Mapping[str, Any]], role: str,
        expected_path: str, where: str) -> dict[str, Any]:
    raw = tools_by_role.get(role)
    if raw is None:
        raise ReleaseError(f"{where}: missing manifest replay role {role}")
    item = _exact(raw, {"role", "path", "sha256", "size"}, where)
    if item["role"] != role or item["path"] != expected_path:
        raise ReleaseError(
            f"{where}: role/path must be {role}={expected_path}")
    return {key: item[key] for key in ("path", "sha256", "size")}


def _require_source_tool_identity(
        source: Any, source_path: str, release_tool: Mapping[str, Any],
        where: str) -> dict[str, Any]:
    record = _binding(source, f"{where} source binding")
    if record["path"] != source_path or \
            (record["sha256"], record["size"]) != \
            (release_tool["sha256"], release_tool["size"]):
        raise ReleaseError(
            f"{where}: release tool identity differs from canonical source "
            "binding")
    return record


def _canonical_json_report(
        release_dir: Path, payload_by_path: Mapping[str, Mapping[str, Any]],
        relative: str, expected: Mapping[str, Any], where: str) -> dict[str, Any]:
    """Require one carried derived report to be canonical and freshly equal."""
    record = payload_by_path.get(relative)
    if record is None:
        raise ReleaseError(f"current-policy release lacks {relative}")
    path = _match_file(release_dir, record, where)
    payload = stable_file_bytes(path, where)
    canonical = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode(
        "utf-8")
    if payload != canonical:
        try:
            parsed = json.loads(
                payload.decode("utf-8"), object_pairs_hook=_reject_duplicate_pairs)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ReleaseError(f"{where}: invalid JSON: {exc}") from exc
        if parsed != expected:
            raise ReleaseError(
                f"{where}: differs from the canonical fresh regrade")
        raise ReleaseError(f"{where}: JSON bytes are not canonical")
    return dict(expected)


def validate_current_policy_derived_reports(
        release_dir: Path, config: Mapping[str, Any],
        loaded: Mapping[str, Any], replay_tools: Sequence[Mapping[str, Any]],
        payload_by_path: Mapping[str, Mapping[str, Any]],
        declared_scopes: Mapping[str, str], *,
        current_policy: bool) -> dict[str, Any] | None:
    """Close every standard derived schema-v2 report carried as evidence."""
    if not current_policy:
        return None
    tools_by_role = {row["role"]: row for row in replay_tools}
    validator = _required_replay_tool(
        tools_by_role, V2_VALIDATOR_ROLE, V2_VALIDATOR_RELEASE_PATH,
        "schema-v2 validation compiler")
    validator_path = _match_file(
        release_dir, validator, "schema-v2 validation compiler")
    local_validator = Path(composition.__file__).resolve(strict=True)
    local_info, local_hash = stable_file_digest(
        local_validator, "active schema-v2 validation compiler")
    if (validator["sha256"], validator["size"]) != \
            (local_hash, local_info.st_size):
        raise ReleaseError(
            "schema-v2 validation compiler differs from the active canonical "
            "validator")

    try:
        expected_v2 = composition.config_validation_report(
            config, loaded, release_dir, validator_path=validator_path)
        composition.validate_config_validation_report(
            expected_v2, config, loaded, release_dir,
            validator_path=validator_path)
    except composition.V2Error as exc:
        raise ReleaseError(f"cannot derive canonical v2 validation: {exc}") from exc
    _canonical_json_report(
        release_dir, payload_by_path, "verification/v2-validation.json",
        expected_v2, "schema-v2 validation report")

    intent_binding = loaded.get("bindings", {}).get("mechanical_intent")
    if not isinstance(intent_binding, Mapping) or not isinstance(
            intent_binding.get("path"), Path):
        raise ReleaseError(
            "validated schema-v2 config lacks mechanical-intent authority")
    try:
        intent_raw = composition.load_yaml(intent_binding["path"])
        expected_intent = composition.mechanical_intent_validation_report(
            intent_raw)
    except (OSError, composition.V2Error) as exc:
        raise ReleaseError(
            f"cannot derive canonical mechanical-intent validation: {exc}") from exc
    _canonical_json_report(
        release_dir, payload_by_path,
        "verification/mechanical-intent-validation-v2.json",
        expected_intent, "mechanical-intent validation report")

    statuses_path = "verification/scope-statuses.json"
    statuses_record = payload_by_path.get(statuses_path)
    if statuses_record is None:
        raise ReleaseError(f"current-policy release lacks {statuses_path}")
    statuses = {"scope_statuses": dict(declared_scopes)}
    _canonical_json_report(
        release_dir, payload_by_path, statuses_path, statuses,
        "schema-v2 scope-status input")
    try:
        expected_verdict = composition.aggregate_config_report(statuses, loaded)
    except composition.V2Error as exc:
        raise ReleaseError(f"cannot derive canonical scoped verdict: {exc}") from exc
    _canonical_json_report(
        release_dir, payload_by_path, "verification/scoped-verdict.json",
        expected_verdict, "schema-v2 scoped verdict")
    if expected_verdict["status"] != min(
            declared_scopes.values(), key=lambda item: STATUS_ORDER[item]):
        raise ReleaseError(
            "schema-v2 scoped verdict differs from manifest aggregate")

    # Reopen all derived inputs and the selected compiler after comparison.
    for relative, label in (
            ("verification/v2-validation.json", "schema-v2 validation report"),
            ("verification/mechanical-intent-validation-v2.json",
             "mechanical-intent validation report"),
            ("verification/scope-statuses.json", "schema-v2 scope-status input"),
            ("verification/scoped-verdict.json", "schema-v2 scoped verdict")):
        _match_file(release_dir, payload_by_path[relative], label)
    _match_file(release_dir, validator, "schema-v2 validation compiler")
    return {
        "validator": validator["path"],
        "config_report": "verification/v2-validation.json",
        "intent_report": "verification/mechanical-intent-validation-v2.json",
        "scoped_verdict": "verification/scoped-verdict.json",
    }


def _release_local_payload_binding(
        release_dir: Path, payload_by_path: Mapping[str, Mapping[str, Any]],
        path: str, sha256: str, size: int, where: str) -> dict[str, Any]:
    record = {"path": safe_rel(path, f"{where}.path"),
              "sha256": sha256, "size": size}
    payload = payload_by_path.get(record["path"])
    if payload is None or not _same_record(record, payload, "path", "path"):
        raise ReleaseError(f"{where}: differs from release payload census")
    _match_file(release_dir, record, where)
    return record


def _validate_generation_replay(
        release_dir: Path, config: Mapping[str, Any],
        audit: Mapping[str, Any], generation_record: Mapping[str, Any],
        tools_by_role: Mapping[str, Mapping[str, Any]],
        payload_by_path: Mapping[str, Mapping[str, Any]],
        ) -> dict[str, Any]:
    """Re-run the exact release generator and compare every generated byte.

    The generator runs from release-local tooling in a private directory.  Its
    sibling imports therefore resolve the exact helper and bounded-runtime
    payloads selected by the manifest; the immutable release is never written.
    """
    generator = _required_replay_tool(
        tools_by_role, ENCLOSURE_GENERATOR_ROLE,
        ENCLOSURE_GENERATOR_RELEASE_PATH, "enclosure generator")
    helper = _required_replay_tool(
        tools_by_role, "enclosure_common", "tooling/enclosure_common.py",
        "enclosure generator helper")
    process_runner = _required_replay_tool(
        tools_by_role, PROCESS_RUNNER_ROLE, PROCESS_RUNNER_RELEASE_PATH,
        "enclosure generator process runner")
    pipeline_runtime = _required_replay_tool(
        tools_by_role, PIPELINE_RUNTIME_ROLE, PIPELINE_RUNTIME_RELEASE_PATH,
        "enclosure generator pipeline runtime")
    for binding, label in (
            (generator, "enclosure generator"),
            (helper, "enclosure generator helper"),
            (process_runner, "enclosure generator process runner"),
            (pipeline_runtime, "enclosure generator pipeline runtime")):
        _match_file(release_dir, binding, label)

    generation_path = _match_file(
        release_dir, generation_record, "sealed manufacturing generation")
    sealed = load_json_strict(generation_path)
    _exact(sealed, {
        "schema", "kind", "name", "mode", "engine", "config",
        "interface", "authority", "assembly_contract", "selector_contract",
        "source", "parts", "installed_case",
    }, "sealed manufacturing generation")
    if sealed["schema"] != 1 or sealed["kind"] != \
            "pcb-enclosure-generation-v1":
        raise ReleaseError("sealed manufacturing generation has wrong schema/kind")
    authority = sealed.get("authority")
    if not isinstance(authority, Mapping) or \
            authority.get("kind") != "authored_scad":
        raise ReleaseError(
            "current-policy manufacturing replay requires authored_scad "
            "generation authority")

    subject = _exact(config.get("subject"), {
        "release", "release_manifest", "pcb", "step", "interface",
        "mechanical_intent", "cad_design",
    }, "release config.subject")
    cad_design = _binding(
        subject["cad_design"], "release config.subject.cad_design")
    if not cad_design["path"].startswith("source/"):
        raise ReleaseError(
            "release CAD design replay config must resolve below source/")
    cad_payload = payload_by_path.get(cad_design["path"])
    if cad_payload is None or not _same_record(
            cad_design, cad_payload, "path", "path"):
        raise ReleaseError(
            "release CAD design replay config differs from payload census")
    cad_path = _match_file(
        release_dir, cad_design, "release CAD design replay config")

    source = _binding(sealed.get("source"), "generation source")
    generation_parent = PurePosixPath(generation_record["path"]).parent
    source_release_path = (generation_parent /
                           PurePosixPath(source["path"])).as_posix()
    _release_local_payload_binding(
        release_dir, payload_by_path, source_release_path,
        source["sha256"], source["size"], "generation source payload")

    rows = sealed.get("parts")
    if not isinstance(rows, list) or not rows:
        raise ReleaseError("generation printable part census is empty")
    parts: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(rows):
        row = _exact(raw, {
            "part", "selector", "path", "sha256", "size", "command",
            "execution", "canonicalization",
        }, f"generation.parts[{index}]")
        part = _string(row["part"], f"generation.parts[{index}].part")
        if part in parts:
            raise ReleaseError("generation printable part census has duplicates")
        parts[part] = row
    installed = _exact(sealed.get("installed_case"), {
        "selector", "path", "sha256", "size", "command", "execution",
        "canonicalization",
    }, "generation.installed_case")

    audit_meshes = audit.get("meshes")
    if not isinstance(audit_meshes, list) or not audit_meshes:
        raise ReleaseError("manufacturing audit mesh denominator is zero")
    audited: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(audit_meshes):
        row = _exact(raw, {"part", "path", "sha256", "size"},
                     f"config.manufacturing_audit.meshes[{index}]")
        part = _string(row["part"],
                       f"config.manufacturing_audit.meshes[{index}].part")
        record = _binding(
            {key: row[key] for key in ("path", "sha256", "size")},
            f"config.manufacturing_audit.meshes[{index}]")
        if part in audited:
            raise ReleaseError("manufacturing audit mesh census has duplicates")
        audited[part] = record
    if set(audited) != set(parts):
        raise ReleaseError(
            "manufacturing audit meshes differ from generation printables")
    for part, row in parts.items():
        record = audited[part]
        if (record["sha256"], record["size"]) != \
                (row["sha256"], row["size"]):
            raise ReleaseError(
                f"manufacturing mesh {part} differs from generation receipt")

    with tempfile.TemporaryDirectory(
            prefix="pcb-enclosure-generation-replay-") as temporary_name:
        temporary = Path(temporary_name)
        command = [
            "/usr/bin/python3", "-B", str(release_dir / generator["path"]),
            str(cad_path), "--root", str(release_dir),
            "--build-dir", str(temporary),
        ]
        try:
            composition._run_collision_process(
                command, cwd=release_dir, timeout_s=1800.0)
        except (OSError, composition.V2Error) as exc:
            raise ReleaseError(
                f"release enclosure generation replay failed: {exc}") from exc
        regenerated_generation = temporary / "generation.json"
        _, regenerated_hash = stable_file_digest(
            regenerated_generation, "regenerated generation receipt")
        regenerated_size = regenerated_generation.stat().st_size
        if (regenerated_hash, regenerated_size) != \
                (generation_record["sha256"], generation_record["size"]):
            raise ReleaseError(
                "manufacturing generation receipt does not reproduce byte-exact")
        if load_json_strict(regenerated_generation) != sealed:
            raise ReleaseError(
                "manufacturing generation semantics differ after replay")
        for part, row in parts.items():
            candidate = temporary / row["path"]
            _, digest = stable_file_digest(
                candidate, f"regenerated printable {part}")
            if (digest, candidate.stat().st_size) != \
                    (row["sha256"], row["size"]):
                raise ReleaseError(
                    f"regenerated printable {part} differs from sealed bytes")
        installed_candidate = temporary / installed["path"]
        _, installed_hash = stable_file_digest(
            installed_candidate, "regenerated installed case")
        if (installed_hash, installed_candidate.stat().st_size) != \
                (installed["sha256"], installed["size"]):
            raise ReleaseError(
                "regenerated installed case differs from sealed bytes")
        source_candidate = temporary / source["path"]
        _, source_hash = stable_file_digest(
            source_candidate, "regenerated enclosure source")
        if (source_hash, source_candidate.stat().st_size) != \
                (source["sha256"], source["size"]):
            raise ReleaseError(
                "regenerated enclosure source differs from sealed bytes")

    # Reopen every release-local tool and output after the private replay.
    for binding, label in (
            (generator, "enclosure generator"),
            (helper, "enclosure generator helper"),
            (process_runner, "enclosure generator process runner"),
            (pipeline_runtime, "enclosure generator pipeline runtime"),
            (generation_record, "sealed manufacturing generation")):
        _match_file(release_dir, binding, label)
    return {
        "generator_binding": generator,
        "source": source_release_path,
        "parts": sorted(parts),
        "installed_case": installed["path"],
    }


def _validate_generic_verification_replay(
        release_dir: Path, config: Mapping[str, Any], audit: Mapping[str, Any],
        generation_record: Mapping[str, Any],
        tools_by_role: Mapping[str, Mapping[str, Any]],
        payload_by_path: Mapping[str, Mapping[str, Any]],
        *, refresh_report: bool = False,
        ) -> dict[str, Any]:
    """Freshly reproduce the carried schema-v1 verification report.

    The replay uses the exact manifest-selected verifier and sibling helper in
    a fresh process. Generated build inputs are copied to a private directory
    using their receipt-selected basenames; no carried report chooses inputs.
    Immutable release verification is read-only.  The private staging caller
    may instead replace a stale carried report with the exact replay output
    before the manifest census is built.
    """
    verifier = _required_replay_tool(
        tools_by_role, GENERIC_VERIFIER_ROLE, GENERIC_VERIFIER_RELEASE_PATH,
        "generic enclosure verifier")
    verifier_path = _match_file(
        release_dir, verifier, "generic enclosure verifier")
    active_verifier = Path(__file__).resolve().with_name("verify_enclosure.py")
    active_info, active_hash = stable_file_digest(
        active_verifier, "active generic enclosure verifier")
    if (verifier["sha256"], verifier["size"]) != \
            (active_hash, active_info.st_size):
        raise ReleaseError(
            "generic enclosure verifier differs from the active canonical "
            "verifier")
    helper = _required_replay_tool(
        tools_by_role, "enclosure_common", "tooling/enclosure_common.py",
        "generic enclosure verifier helper")
    _match_file(release_dir, helper, "generic enclosure verifier helper")

    report_relative = "verification/verification.json"
    report_record = payload_by_path.get(report_relative)
    if report_record is None:
        raise ReleaseError(
            "current-policy FDM release lacks verification/verification.json")
    sealed_report_path = _match_file(
        release_dir, report_record, "generic verification receipt")
    sealed_report = load_json_strict(sealed_report_path)
    if sealed_report.get("schema") != 1 or sealed_report.get("kind") != \
            "pcb-enclosure-verification-v1":
        raise ReleaseError("generic verification receipt has wrong schema/kind")

    subject = _exact(config.get("subject"), {
        "release", "release_manifest", "pcb", "step", "interface",
        "mechanical_intent", "cad_design",
    }, "release config.subject")
    cad_design = _binding(subject["cad_design"], "release CAD design")
    cad_path = _match_file(release_dir, cad_design, "release CAD design")
    generation_path = _match_file(
        release_dir, generation_record, "generic verification generation")
    generation = load_json_strict(generation_path)
    generation_parent = PurePosixPath(generation_record["path"]).parent

    def binding_fields(raw: Any, where: str) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            raise ReleaseError(f"{where}: expected binding object")
        try:
            candidate = {key: raw[key] for key in ("path", "sha256", "size")}
        except KeyError as exc:
            raise ReleaseError(f"{where}: incomplete binding") from exc
        return _binding(candidate, where)

    def release_record(relative: str, expected: Mapping[str, Any],
                       where: str) -> dict[str, Any]:
        record = binding_fields(expected, where)
        payload = payload_by_path.get(relative)
        if payload is None or not _same_record(
                {"path": relative, "sha256": record["sha256"],
                 "size": record["size"]}, payload, "path", "path"):
            raise ReleaseError(f"{where}: differs from payload census")
        _match_file(release_dir, payload, where)
        return dict(payload)

    source = binding_fields(generation.get("source"), "generation source")
    source_relative = (generation_parent / source["path"]).as_posix()
    source_payload = release_record(
        source_relative, source, "generic verification generation source")
    installed = binding_fields(
        generation.get("installed_case"), "generation installed case")
    installed_relative = (generation_parent / installed["path"]).as_posix()
    installed_payload = release_record(
        installed_relative, installed,
        "generic verification generation installed case")

    generation_rows = generation.get("parts")
    if not isinstance(generation_rows, list) or not generation_rows:
        raise ReleaseError("generic verification generation has no printables")
    generation_parts: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(generation_rows):
        if not isinstance(row, Mapping):
            raise ReleaseError(
                f"generic verification generation.parts[{index}] is malformed")
        part = _string(row.get("part"),
                       f"generic verification generation.parts[{index}].part")
        if part in generation_parts:
            raise ReleaseError("generic verification generation duplicates a part")
        generation_parts[part] = row
    audit_rows = audit.get("meshes")
    if not isinstance(audit_rows, list) or not audit_rows:
        raise ReleaseError("generic verification audit mesh census is empty")
    mesh_payloads: dict[str, tuple[dict[str, Any], str]] = {}
    for index, raw in enumerate(audit_rows):
        row = _exact(raw, {"part", "path", "sha256", "size"},
                     f"generic verification audit.meshes[{index}]")
        part = _string(row["part"],
                       f"generic verification audit.meshes[{index}].part")
        generation_row = generation_parts.get(part)
        if generation_row is None or \
                (row["sha256"], row["size"]) != \
                (generation_row.get("sha256"), generation_row.get("size")):
            raise ReleaseError(
                f"generic verification mesh {part} differs from generation")
        payload = release_record(
            row["path"], row, f"generic verification printable {part}")
        mesh_payloads[part] = (payload, str(generation_row.get("path")))
    if set(mesh_payloads) != set(generation_parts):
        raise ReleaseError(
            "generic verification printable census differs from generation")

    step_relative = "verification/step-inspection.json"
    step_record = payload_by_path.get(step_relative)
    if step_record is None:
        raise ReleaseError(
            "current-policy release lacks verification/step-inspection.json")
    step_path = _match_file(
        release_dir, step_record, "generic verification STEP inspection")
    step = load_json_strict(step_path)
    component = binding_fields(
        step.get("geometry", {}).get("component_mesh"),
        "generic verification STEP component mesh")
    component_relative = (PurePosixPath(step_relative).parent /
                          component["path"]).as_posix()
    component_payload = release_record(
        component_relative, component,
        "generic verification STEP component mesh")

    collision_report_relative = "verification/collision.json"
    collision_mesh_relative = "verification/clearance-intersection.stl"
    collision_record = payload_by_path.get(collision_report_relative)
    collision_mesh_record = payload_by_path.get(collision_mesh_relative)
    if (collision_record is None) != (collision_mesh_record is None):
        raise ReleaseError(
            "generic collision report and mesh must both be present or absent")
    if collision_record is not None:
        _match_file(release_dir, collision_record,
                    "generic verification collision receipt")
        _match_file(release_dir, collision_mesh_record,
                    "generic verification collision mesh")
    physical_relative = "verification/physical-evidence.yaml"
    physical_record = payload_by_path.get(physical_relative)
    physical_path = None
    if physical_record is not None:
        physical_path = _match_file(
            release_dir, physical_record,
            "generic verification physical evidence")

    def copy_payload(record: Mapping[str, Any], destination: Path,
                     where: str) -> None:
        payload = stable_file_bytes(
            release_dir / record["path"], where)
        destination.write_bytes(payload)
        if hashlib.sha256(payload).hexdigest() != record["sha256"] or \
                len(payload) != record["size"]:
            raise ReleaseError(f"{where}: changed while copying for replay")

    with tempfile.TemporaryDirectory(
            prefix="pcb-enclosure-generic-verification-replay-") as name:
        temporary = Path(name)
        copy_payload(generation_record, temporary / "generation.json",
                     "generic verification generation")
        copy_payload(source_payload, temporary / source["path"],
                     "generic verification generation source")
        copy_payload(installed_payload, temporary / installed["path"],
                     "generic verification installed case")
        for part, (payload, basename) in mesh_payloads.items():
            copy_payload(payload, temporary / basename,
                         f"generic verification printable {part}")
        private_step = temporary / PurePosixPath(step_relative).name
        copy_payload(step_record, private_step,
                     "generic verification STEP inspection")
        copy_payload(component_payload, temporary / component["path"],
                     "generic verification STEP component mesh")
        command = [
            "/usr/bin/python3", "-B", str(verifier_path), str(cad_path),
            "--root", str(release_dir), "--build-dir", str(temporary),
            "--step-inspection", str(private_step),
            "--report", str(temporary / "verification.json"),
            "--target", "cad", "--regrade-report",
        ]
        if collision_record is not None and collision_mesh_record is not None:
            private_collision = temporary / "collision.json"
            private_collision_mesh = temporary / "clearance-intersection.stl"
            copy_payload(collision_record, private_collision,
                         "generic verification collision receipt")
            copy_payload(collision_mesh_record, private_collision_mesh,
                         "generic verification collision mesh")
            command.extend((
                "--collision-report", str(private_collision),
                "--collision-mesh", str(private_collision_mesh),
            ))
        if physical_path is not None:
            command.extend(("--physical-evidence", str(physical_path)))
        try:
            composition._run_collision_process(
                command, cwd=release_dir, timeout_s=600.0)
        except (OSError, composition.V2Error) as exc:
            raise ReleaseError(
                f"generic verification replay failed: {exc}") from exc
        regenerated = temporary / "verification.json"
        regenerated_payload = stable_file_bytes(
            regenerated, "regenerated generic verification receipt")
        sealed_payload = stable_file_bytes(
            sealed_report_path, "sealed generic verification receipt")
        regenerated_report = load_json_strict(regenerated)
        refreshed = False
        if regenerated_payload != sealed_payload or \
                regenerated_report != sealed_report:
            if not refresh_report:
                raise ReleaseError(
                    "generic verification receipt does not reproduce byte-exact")
            protected_inputs = [
                verifier_path, cad_path, generation_path, step_path,
                release_dir / source_payload["path"],
                release_dir / installed_payload["path"],
                release_dir / component_payload["path"],
                *(release_dir / payload["path"]
                  for payload, _ in mesh_payloads.values()),
            ]
            if collision_record is not None and \
                    collision_mesh_record is not None:
                protected_inputs.extend((
                    release_dir / collision_record["path"],
                    release_dir / collision_mesh_record["path"],
                ))
            if physical_path is not None:
                protected_inputs.append(physical_path)
            try:
                with composition.atomic_output(
                        sealed_report_path,
                        where="staged generic verification receipt",
                        root=release_dir, inputs=protected_inputs) as (_, stream):
                    stream.write(regenerated_payload)
            except (OSError, composition.V1EnclosureError) as exc:
                raise ReleaseError(
                    f"cannot refresh staged generic verification receipt: "
                    f"{exc}") from exc
            if stable_file_bytes(
                    sealed_report_path,
                    "refreshed generic verification receipt") != \
                    regenerated_payload or \
                    load_json_strict(sealed_report_path) != regenerated_report:
                raise ReleaseError(
                    "refreshed generic verification receipt changed after "
                    "atomic publication")
            refreshed = True

    reopen = [
            (verifier, "generic enclosure verifier"),
            (helper, "generic enclosure verifier helper"),
            (generation_record, "generic verification generation"),
            (step_record, "generic verification STEP inspection")]
    if not refreshed:
        reopen.append((report_record, "generic verification receipt"))
    for binding, label in reopen:
        _match_file(release_dir, binding, label)
    report_info, report_hash = stable_file_digest(
        sealed_report_path, "final generic verification receipt")
    return {
        "verifier": verifier["path"],
        "report": report_relative,
        "report_binding": {
            "path": report_relative,
            "sha256": report_hash,
            "size": report_info.st_size,
        },
        "refreshed": refreshed,
        "step_inspection": step_relative,
        "collision": (
            collision_report_relative if collision_record is not None else None),
    }


def validate_fdm_replay_closure(
        release_dir: Path, config: Mapping[str, Any],
        replay_tools: Sequence[Mapping[str, Any]],
        payload_by_path: Mapping[str, Mapping[str, Any]],
        *, refresh_derived_reports: bool = False,
        ) -> dict[str, Any] | None:
    """Bind current-policy FDM regrade to one exact release-local compiler."""
    if "manufacturing_audit" not in config:
        return None
    audit = _exact(config["manufacturing_audit"], {
        "contract", "receipt", "generation", "collision",
        "collision_subject", "meshes",
    },
                   "config.manufacturing_audit")
    expected_roots = {
        "contract": "source/", "receipt": "verification/",
        "generation": "verification/", "collision": "verification/",
    }
    generation_record = _binding(
        audit["generation"], "config.manufacturing_audit.generation")
    collision_record = _binding(
        audit["collision"], "config.manufacturing_audit.collision")
    for field, prefix in expected_roots.items():
        record = ({"generation": generation_record,
                   "collision": collision_record}.get(field) or
                  _binding(audit[field],
                           f"config.manufacturing_audit.{field}"))
        if not record["path"].startswith(prefix):
            raise ReleaseError(
                f"manufacturing audit {field} must be release-local below {prefix}")
        payload = payload_by_path.get(record["path"])
        if payload is None or not _same_record(record, payload, "path", "path"):
            raise ReleaseError(
                f"manufacturing audit {field} differs from payload census")
        _match_file(release_dir, record, f"manufacturing audit {field}")
    meshes = audit["meshes"]
    if not isinstance(meshes, list) or not meshes:
        raise ReleaseError("manufacturing audit mesh denominator is zero")
    for index, raw in enumerate(meshes):
        where = f"config.manufacturing_audit.meshes[{index}]"
        row = _exact(raw, {"part", "path", "sha256", "size"}, where)
        record = _binding({key: row[key] for key in ("path", "sha256", "size")},
                          where)
        if not record["path"].startswith("meshes/"):
            raise ReleaseError(f"{where}: printable must resolve below meshes/")
        payload = payload_by_path.get(record["path"])
        if payload is None or not _same_record(record, payload, "path", "path"):
            raise ReleaseError(f"{where}: differs from payload census")
        _match_file(release_dir, record, f"manufacturing audit mesh {index}")
    receipt_record = _binding(
        audit["receipt"], "config.manufacturing_audit.receipt")
    receipt = load_json_strict(release_dir / receipt_record["path"])
    inputs = _exact(receipt.get("inputs"), {
        "compiler", "enclosure_common", "contract", "cad_design",
        "generation", "meshes",
    }, "manufacturing audit receipt.inputs")
    compiler_source = _binding(
        inputs["compiler"], "manufacturing audit receipt.inputs.compiler")
    if compiler_source["path"] != FDM_AUDIT_COMPILER_SOURCE_PATH:
        raise ReleaseError(
            "manufacturing audit receipt compiler has noncanonical source path")
    tools_by_role = {row["role"]: row for row in replay_tools}
    collision = load_json_strict(release_dir / collision_record["path"])
    _exact(collision, {
        "schema", "kind", "status", "builder", "enclosure_common",
        "step_inspector", "process_runner", "pipeline_runtime", "backend",
        "inputs", "transform", "selection", "result",
    }, "manufacturing collision receipt")
    collision_builder_source = _binding(
        collision.get("builder"), "manufacturing collision builder")
    if collision_builder_source["path"] != COLLISION_BUILDER_SOURCE_PATH:
        raise ReleaseError(
            "manufacturing collision builder has noncanonical source path")
    collision_builder = _required_replay_tool(
        tools_by_role, COLLISION_BUILDER_ROLE,
        COLLISION_BUILDER_RELEASE_PATH, "manufacturing collision builder")
    if \
            (collision_builder["sha256"], collision_builder["size"]) != \
            (collision_builder_source["sha256"],
             collision_builder_source["size"]):
        raise ReleaseError(
            "manifest collision builder path/identity differs from receipt")
    compiler = tools_by_role.get(FDM_AUDIT_COMPILER_ROLE)
    if compiler is None:
        raise ReleaseError(
            "manufacturing audit requires manifest replay tool role "
            f"{FDM_AUDIT_COMPILER_ROLE}")
    if compiler["path"] != FDM_AUDIT_COMPILER_RELEASE_PATH or \
            (compiler["sha256"], compiler["size"]) != \
            (compiler_source["sha256"], compiler_source["size"]):
        raise ReleaseError(
            "manifest FDM audit compiler path/identity differs from receipt")
    helper_source = _binding(
        inputs["enclosure_common"],
        "manufacturing audit receipt.inputs.enclosure_common")
    if helper_source["path"] != \
            "skills/pcb-enclosure/scripts/enclosure_common.py":
        raise ReleaseError(
            "manufacturing audit enclosure_common has noncanonical source path")
    helper = _required_replay_tool(
        tools_by_role, "enclosure_common", "tooling/enclosure_common.py",
        "manufacturing audit enclosure_common")
    if (helper["sha256"], helper["size"]) != \
            (helper_source["sha256"], helper_source["size"]):
        raise ReleaseError(
            "manifest enclosure_common helper path/identity differs from "
            "manufacturing audit receipt")
    collision_helper_source = _require_source_tool_identity(
        collision.get("enclosure_common"),
        "skills/pcb-enclosure/scripts/enclosure_common.py", helper,
        "manufacturing collision enclosure_common")
    if (collision_helper_source["sha256"], collision_helper_source["size"]) != \
            (helper_source["sha256"], helper_source["size"]):
        raise ReleaseError(
            "collision and FDM receipts disagree on enclosure_common")

    inspector = _required_replay_tool(
        tools_by_role, STEP_INSPECTOR_ROLE, STEP_INSPECTOR_RELEASE_PATH,
        "manufacturing collision STEP inspector")
    _require_source_tool_identity(
        collision.get("step_inspector"), STEP_INSPECTOR_SOURCE_PATH,
        inspector, "manufacturing collision STEP inspector")
    process_runner = _required_replay_tool(
        tools_by_role, PROCESS_RUNNER_ROLE, PROCESS_RUNNER_RELEASE_PATH,
        "manufacturing collision process runner")
    _require_source_tool_identity(
        collision.get("process_runner"), PROCESS_RUNNER_SOURCE_PATH,
        process_runner, "manufacturing collision process runner")
    pipeline_runtime = _required_replay_tool(
        tools_by_role, PIPELINE_RUNTIME_ROLE, PIPELINE_RUNTIME_RELEASE_PATH,
        "manufacturing collision pipeline runtime")
    _require_source_tool_identity(
        collision.get("pipeline_runtime"), PIPELINE_RUNTIME_SOURCE_PATH,
        pipeline_runtime, "manufacturing collision pipeline runtime")

    collision_inputs = _exact(collision.get("inputs"), {
        "step_inspection", "step", "component_mesh", "interface",
        "generation", "assembled_case_mesh",
    }, "manufacturing collision receipt.inputs")
    config_subject = _exact(config.get("subject"), {
        "release", "release_manifest", "pcb", "step", "interface",
        "mechanical_intent", "cad_design",
    }, "release config.subject")
    collision_step = _binding(
        collision_inputs["step"], "manufacturing collision STEP")
    collision_interface = _binding(
        collision_inputs["interface"], "manufacturing collision interface")
    subject_step = _binding(config_subject["step"], "release config subject STEP")
    subject_interface = _binding(
        config_subject["interface"], "release config subject interface")
    subject_raw = audit["collision_subject"]
    if not isinstance(subject_raw, Mapping):
        raise ReleaseError("manufacturing collision_subject must be an object")
    subject_mode = subject_raw.get("mode")
    collision_subject_validator = None
    if subject_mode == "subject_step":
        _exact(subject_raw, {"mode"},
               "config.manufacturing_audit.collision_subject")
        if (collision_step["sha256"], collision_step["size"]) != \
                (subject_step["sha256"], subject_step["size"]):
            raise ReleaseError(
                "subject_step collision differs from release CAD subject STEP")
    elif subject_mode == "external_composition":
        external = _exact(subject_raw, {
            "mode", "receipt", "parent_step", "interface",
            "supplement_step", "augmentation_receipt", "validator",
        }, "config.manufacturing_audit.collision_subject")
        external_bindings: dict[str, dict[str, Any]] = {}
        for field in ("receipt", "parent_step", "interface",
                      "supplement_step", "augmentation_receipt", "validator"):
            record = _binding(
                external[field],
                f"config.manufacturing_audit.collision_subject.{field}")
            payload = payload_by_path.get(record["path"])
            if payload is None or not _same_record(
                    record, payload, "path", "path"):
                raise ReleaseError(
                    f"external collision {field} differs from payload census")
            _match_file(release_dir, record, f"external collision {field}")
            external_bindings[field] = record
        if not external_bindings["receipt"]["path"].startswith(
                "verification/") or not \
                external_bindings["augmentation_receipt"]["path"].startswith(
                    "verification/"):
            raise ReleaseError(
                "external composition receipts must resolve below verification/")
        for field, subject_record in (
                ("parent_step", subject_step),
                ("interface", subject_interface)):
            external_record = external_bindings[field]
            if (external_record["sha256"], external_record["size"]) != \
                    (subject_record["sha256"], subject_record["size"]):
                raise ReleaseError(
                    f"external collision {field} differs from release CAD subject")
        if (external_bindings["interface"]["sha256"],
                external_bindings["interface"]["size"]) != \
                (collision_interface["sha256"], collision_interface["size"]):
            raise ReleaseError(
                "external collision interface differs from collision receipt")
        collision_subject_validator = _required_replay_tool(
            tools_by_role, OBSTRUCTION_COMPOSITOR_ROLE,
            OBSTRUCTION_COMPOSITOR_RELEASE_PATH,
            "external collision composition validator")
        validator_record = external_bindings["validator"]
        if validator_record["path"] != \
                collision_subject_validator["path"] or \
                (validator_record["sha256"], validator_record["size"]) != \
                (collision_subject_validator["sha256"],
                 collision_subject_validator["size"]):
            raise ReleaseError(
                "external collision validator differs from manifest "
                "obstruction_compositor")
    else:
        raise ReleaseError(
            "manufacturing collision_subject.mode must be "
            "subject_step|external_composition")

    generation_replay = _validate_generation_replay(
        release_dir, config, audit, generation_record, tools_by_role,
        payload_by_path)
    generation_evidence = _validate_fdm_generation_evidence_closure(
        release_dir, generation_record, collision_record, payload_by_path)
    generic_verification = _validate_generic_verification_replay(
        release_dir, config, audit, generation_record, tools_by_role,
        payload_by_path, refresh_report=refresh_derived_reports)
    return {
        "compiler_role": FDM_AUDIT_COMPILER_ROLE,
        "compiler": compiler["path"],
        "compiler_binding": {key: compiler[key]
                             for key in ("path", "sha256", "size")},
        "helper_binding": {key: helper[key]
                           for key in ("path", "sha256", "size")},
        "collision_builder_binding": {
            key: collision_builder[key] for key in ("path", "sha256", "size")},
        "step_inspector_binding": inspector,
        "process_runner_binding": process_runner,
        "pipeline_runtime_binding": pipeline_runtime,
        "collision_subject_validator_binding": collision_subject_validator,
        "generator_binding": generation_replay["generator_binding"],
        "receipt": receipt_record["path"],
        "generation_replay": generation_replay,
        "generation_evidence": generation_evidence,
        "generic_verification": generic_verification,
    }


def verify_release(release_dir: Path, project_root: Path | None = None,
                   *, require_directory_name: bool = True) -> dict[str, Any]:
    release_dir = _plain_directory(release_dir, "release")
    actual_files, _ = scan_regular_tree(release_dir)
    initial_tree_snapshot = regular_tree_content_snapshot(
        release_dir, actual_files, "initial release tree")
    if MANIFEST_NAME not in actual_files:
        raise ReleaseError(f"release lacks {MANIFEST_NAME}")
    manifest_path = release_dir / MANIFEST_NAME
    manifest = load_json_strict(manifest_path)
    top = _exact(manifest, {
        "schema", "kind", "artifact_id", "version", "date", "release_id",
        "lifecycle", "status", "status_reason", "scopes", "publication",
        "based_on", "predecessor", "replay", "payload_count", "payloads",
    }, "manifest")
    if top["schema"] != 2 or isinstance(top["schema"], bool):
        raise ReleaseError("manifest.schema: expected 2")
    if top["kind"] != KIND:
        raise ReleaseError(f"manifest.kind: expected {KIND!r}")
    artifact_id = _string(top["artifact_id"], "manifest.artifact_id")
    if not ARTIFACT_RE.fullmatch(artifact_id):
        raise ReleaseError("manifest.artifact_id: expected filesystem-safe identifier")
    version = _string(top["version"], "manifest.version")
    if not SEMVER_RE.fullmatch(version):
        raise ReleaseError("manifest.version: expected SemVer (optional v prefix)")
    date_text = _string(top["date"], "manifest.date")
    try:
        if Date.fromisoformat(date_text).isoformat() != date_text:
            raise ValueError
    except ValueError as exc:
        raise ReleaseError("manifest.date: expected real YYYY-MM-DD date") from exc
    release_id = _string(top["release_id"], "manifest.release_id")
    expected_release_id = f"{version}-{date_text}"
    if release_id != expected_release_id:
        raise ReleaseError(
            f"manifest.release_id: expected {expected_release_id!r}")
    if require_directory_name and release_dir.name != release_id:
        raise ReleaseError(
            f"release directory name {release_dir.name!r} differs from release_id")

    overall = _status(top["status"], "manifest.status")
    _string(top["status_reason"], "manifest.status_reason")
    scopes_raw = top["scopes"]
    if not isinstance(scopes_raw, Mapping) or not scopes_raw:
        raise ReleaseError("manifest.scopes: expected non-empty object")
    scopes: dict[str, str] = {}
    for name, value in scopes_raw.items():
        if not isinstance(name, str) or not SCOPE_RE.fullmatch(name):
            raise ReleaseError(f"manifest.scopes: invalid scope {name!r}")
        scopes[name] = _status(value, f"manifest.scopes.{name}")
    aggregate = min(scopes.values(), key=lambda item: STATUS_ORDER[item])
    if overall != aggregate:
        raise ReleaseError(
            f"manifest.status {overall} does not equal conservative scope "
            f"aggregate {aggregate}")
    if overall != "INCOMPLETE" or any(
            value != "INCOMPLETE" for value in scopes.values()):
        raise ReleaseError(
            "current pcb-enclosure-release-v2 policy accepts only INCOMPLETE "
            "overall and per-scope candidate status")

    lifecycle = _string(top["lifecycle"], "manifest.lifecycle")
    publication = _exact(top["publication"], {
        "release", "immutable_candidate", "order_ready",
    }, "manifest.publication")
    release_flag = _boolean(publication["release"], "manifest.publication.release")
    candidate = _boolean(publication["immutable_candidate"],
                         "manifest.publication.immutable_candidate")
    order_ready = _boolean(publication["order_ready"],
                           "manifest.publication.order_ready")
    if not release_flag:
        raise ReleaseError("manifest.publication.release must be true")
    if overall == "INCOMPLETE":
        if lifecycle != "immutable_candidate" or not candidate or order_ready:
            raise ReleaseError(
                "INCOMPLETE is publishable only as immutable_candidate with "
                "order_ready=false")
    else:
        if lifecycle != "immutable_release" or candidate:
            raise ReleaseError(
                "completed readiness requires immutable_release lifecycle")
    if order_ready and STATUS_ORDER[overall] < STATUS_ORDER["PRINT_VERIFIED"]:
        raise ReleaseError("order_ready requires PRINT_VERIFIED or better")

    based = _exact(top["based_on"], {
        "pcb_release", "manifest", "pcb", "step",
    }, "manifest.based_on")
    pcb_release = _exact(based["pcb_release"], {
        "release_id", "project_path",
    }, "manifest.based_on.pcb_release")
    parent_release_id = _string(
        pcb_release["release_id"], "manifest.based_on.pcb_release.release_id")
    if "/" in parent_release_id or "\\" in parent_release_id \
            or parent_release_id in {".", ".."}:
        raise ReleaseError("parent PCB release_id must be one path segment")
    parent_project_path = safe_rel(
        pcb_release["project_path"], "manifest.based_on.pcb_release.project_path")
    if parent_project_path != f"07_releases/{parent_release_id}":
        raise ReleaseError("parent PCB project_path is not canonical")
    authority: dict[str, dict[str, Any]] = {}
    for name in ("manifest", "pcb", "step"):
        record = _binding(based[name], f"manifest.based_on.{name}", with_source=True)
        expected = f"authorities/pcb-release/{record['source_path']}"
        if record["release_path"] != expected:
            raise ReleaseError(
                f"manifest.based_on.{name}.release_path: expected {expected!r}")
        authority[name] = record
    if len({row["source_path"] for row in authority.values()}) != 3:
        raise ReleaseError("parent manifest, PCB, and STEP paths must be distinct")

    predecessor_raw = top["predecessor"]
    predecessor: dict[str, Any] | None = None
    if predecessor_raw is not None:
        pred = _exact(predecessor_raw, {
            "release_id", "project_path", "manifest",
        }, "manifest.predecessor")
        pred_id = _string(pred["release_id"], "manifest.predecessor.release_id")
        if "/" in pred_id or "\\" in pred_id or pred_id in {".", ".."}:
            raise ReleaseError("predecessor release_id must be one path segment")
        if pred_id == release_id:
            raise ReleaseError("release cannot name itself as predecessor")
        pred_project_path = safe_rel(
            pred["project_path"], "manifest.predecessor.project_path")
        if pred_project_path != f"07_enclosure_releases/{pred_id}":
            raise ReleaseError("predecessor project_path is not canonical")
        pred_binding = _binding(
            pred["manifest"], "manifest.predecessor.manifest", with_source=True)
        if pred_binding["source_path"] != MANIFEST_NAME or \
                pred_binding["release_path"] != \
                "authorities/enclosure-predecessor/MANIFEST.json":
            raise ReleaseError("predecessor manifest paths are not canonical")
        predecessor = {
            "release_id": pred_id, "project_path": pred_project_path,
            "manifest": pred_binding,
        }

    replay_raw = _exact(top["replay"], {"root", "config", "tools"},
                        "manifest.replay")
    if replay_raw["root"] != ".":
        raise ReleaseError("manifest.replay.root: expected release root '.'")
    replay_config = _binding(replay_raw["config"], "manifest.replay.config")
    if not replay_config["path"].startswith("source/"):
        raise ReleaseError("replay config must resolve below source/")
    tools_raw = replay_raw["tools"]
    if not isinstance(tools_raw, list) or not tools_raw:
        raise ReleaseError("manifest.replay.tools: expected non-empty list")
    replay_tools: list[dict[str, Any]] = []
    tool_roles: set[str] = set()
    tool_paths: set[str] = set()
    for index, value in enumerate(tools_raw):
        item = _exact(value, {"role", "path", "sha256", "size"},
                      f"manifest.replay.tools[{index}]")
        role = _string(item["role"], f"manifest.replay.tools[{index}].role")
        if not ROLE_RE.fullmatch(role) or role in tool_roles:
            raise ReleaseError("replay tool roles must be unique safe identifiers")
        record = _binding({key: item[key] for key in ("path", "sha256", "size")},
                          f"manifest.replay.tools[{index}]")
        if not record["path"].startswith("tooling/") or record["path"] in tool_paths:
            raise ReleaseError("replay tool paths must be unique below tooling/")
        tool_roles.add(role)
        tool_paths.add(record["path"])
        replay_tools.append({"role": role, **record})

    payload_count = _integer(top["payload_count"], "manifest.payload_count")
    payloads_raw = top["payloads"]
    if not isinstance(payloads_raw, list):
        raise ReleaseError("manifest.payloads: expected list")
    payloads: list[dict[str, Any]] = []
    payload_by_path: dict[str, dict[str, Any]] = {}
    canonical_payloads: dict[str, str] = {}
    for index, value in enumerate(payloads_raw):
        record = _binding(value, f"manifest.payloads[{index}]")
        path = record["path"]
        first = PurePosixPath(path).parts[0]
        if first not in ALLOWED_PAYLOAD_ROOTS or path == MANIFEST_NAME:
            raise ReleaseError(f"manifest payload path is outside release contract: {path}")
        canonical = canonical_path_key(path)
        if path in payload_by_path or canonical in canonical_payloads:
            raise ReleaseError(f"duplicate/colliding payload path: {path!r}")
        payload_by_path[path] = record
        canonical_payloads[canonical] = path
        payloads.append(record)
    if payload_count != len(payloads) or payloads != sorted(
            payloads, key=lambda row: row["path"]):
        raise ReleaseError("payload_count/order does not match sorted payload census")
    if "README.md" not in payload_by_path:
        raise ReleaseError("release payload lacks README.md")
    if not any(path.startswith("meshes/") and path.lower().endswith(".stl")
               for path in payload_by_path):
        raise ReleaseError("release payload lacks at least one meshes/*.stl")

    expected_files = {MANIFEST_NAME, *payload_by_path}
    if set(actual_files) != expected_files:
        raise ReleaseError(
            "release file census differs from manifest; "
            f"missing={sorted(expected_files - set(actual_files))}, "
            f"extras={sorted(set(actual_files) - expected_files)}")
    for path, record in payload_by_path.items():
        _match_file(release_dir, record, f"payload {path}")

    for name, record in authority.items():
        payload = payload_by_path.get(record["release_path"])
        if payload is None or not _same_record(
                record, payload, "release_path", "path"):
            raise ReleaseError(f"based_on {name} does not match payload census")
    local_parent_manifest = _match_file(
        release_dir, authority["manifest"], "release-local PCB manifest",
        path_field="release_path")
    validate_parent_manifest(
        local_parent_manifest,
        authority["pcb"]["source_path"], authority["pcb"]["sha256"],
        authority["step"]["source_path"], authority["step"]["sha256"])

    if predecessor is not None:
        pred_record = predecessor["manifest"]
        payload = payload_by_path.get(pred_record["release_path"])
        if payload is None or not _same_record(
                pred_record, payload, "release_path", "path"):
            raise ReleaseError("predecessor manifest does not match payload census")
    for label, record in [("config", replay_config), *[
            (f"tool {row['role']}", row) for row in replay_tools]]:
        payload = payload_by_path.get(record["path"])
        if payload is None or not _same_record(record, payload, "path", "path"):
            raise ReleaseError(f"replay {label} does not match payload census")
    replay_resolution = validate_replay_config(
        release_dir, replay_config, authority, payload_by_path)
    try:
        replay_value = composition.load_yaml(release_dir / replay_config["path"])
        if not isinstance(replay_value, Mapping):
            raise ReleaseError(
                "release-local replay config must contain a YAML/JSON object "
                "before shared connector membership is inspected")
        connector_replay = validate_connector_replay_closure(
            release_dir, replay_value, replay_tools, payload_by_path)
        fdm_replay = validate_fdm_replay_closure(
            release_dir, replay_value, replay_tools, payload_by_path)
        composition_loaded = composition.validate_config_v2(
            replay_value, release_dir,
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
    except ReleaseError:
        raise
    except (composition.V2Error, OSError) as exc:
        raise ReleaseError(
            f"release-local schema-v2 config is invalid: {exc}") from exc
    required_scopes = composition.required_scope_closure(
        composition_loaded["scopes"])
    if set(scopes) != set(required_scopes):
        raise ReleaseError(
            "manifest scopes differ from validated schema-v2 required scope "
            f"census; expected={required_scopes}, actual={sorted(scopes)}")
    derived_reports = validate_current_policy_derived_reports(
        release_dir, replay_value, composition_loaded, replay_tools,
        payload_by_path, scopes, current_policy=fdm_replay is not None)

    if predecessor is not None:
        local_predecessor = load_json_strict(
            release_dir / predecessor["manifest"]["release_path"])
        if local_predecessor.get("schema") != 2 or \
                local_predecessor.get("kind") != KIND or \
                local_predecessor.get("release_id") != predecessor["release_id"] or \
                local_predecessor.get("artifact_id") != artifact_id:
            raise ReleaseError(
                "release-local predecessor manifest has the wrong identity or "
                "artifact stream")

    if project_root is not None:
        project_root = _plain_directory(project_root, "project root")
        parent_root = resolve_plain_relative(
            project_root, parent_project_path, "external parent PCB release")
        if not parent_root.is_dir():
            raise ReleaseError("external parent PCB release is not a directory")
        for name, record in authority.items():
            source = {
                "path": record["source_path"], "sha256": record["sha256"],
                "size": record["size"],
            }
            _match_file(parent_root, source, f"external parent {name}")
        if predecessor is not None:
            predecessor_root = resolve_plain_relative(
                project_root, predecessor["project_path"],
                "external enclosure predecessor")
            pred = predecessor["manifest"]
            _match_file(predecessor_root, {
                "path": pred["source_path"], "sha256": pred["sha256"],
                "size": pred["size"],
            }, "external predecessor manifest")

    # Re-census every path and byte after all executable replays and external
    # authority checks. A late mutation or extra may not enter the success
    # result merely because its earlier manifest-bound read already passed.
    final_files, _ = scan_regular_tree(release_dir)
    final_tree_snapshot = regular_tree_content_snapshot(
        release_dir, final_files, "final release tree")
    if final_tree_snapshot != initial_tree_snapshot:
        initial_paths = set(initial_tree_snapshot)
        final_paths = set(final_tree_snapshot)
        changed = sorted(
            path for path in initial_paths & final_paths
            if initial_tree_snapshot[path] != final_tree_snapshot[path])
        raise ReleaseError(
            "release tree changed during verification; "
            f"missing={sorted(initial_paths - final_paths)}, "
            f"extras={sorted(final_paths - initial_paths)}, "
            f"changed={changed}")

    return {
        "kind": KIND,
        "release_id": release_id,
        "artifact_id": artifact_id,
        "status": overall,
        "scopes": scopes,
        "order_ready": order_ready,
        "payload_count": len(payloads),
        "replay": {
            "root": ".",
            "config": replay_config["path"],
            "tools": {row["role"]: row["path"] for row in replay_tools},
            "resolution": replay_resolution,
            "connector_assembly": (
                None if connector_replay is None else {
                    key: value for key, value in connector_replay.items()
                    if key != "compiler_binding"
                }),
            "manufacturing_audit": (
                None if fdm_replay is None else {
                    key: value for key, value in fdm_replay.items()
                    if key not in {
                        "compiler_binding", "helper_binding",
                        "collision_builder_binding", "step_inspector_binding",
                        "process_runner_binding", "pipeline_runtime_binding",
                        "collision_subject_validator_binding",
                        "generator_binding",
                    }
                }),
            "derived_reports": derived_reports,
        },
        "external_parent_checked": project_root is not None,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path,
                        help="07_enclosure_releases/<version-date> directory")
    parser.add_argument(
        "--project-root", type=Path,
        help="also check live 07_releases parent and enclosure predecessor")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = verify_release(args.release, args.project_root)
    except (OSError, ReleaseError) as exc:
        print(f"ENCLOSURE RELEASE INVALID — {args.release}: {exc}", file=sys.stderr)
        return 1
    print(
        f"ENCLOSURE RELEASE VERIFIED — {result['release_id']} — "
        f"status={result['status']}, files={result['payload_count']}/{result['payload_count']}, "
        f"order_ready={str(result['order_ready']).lower()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
