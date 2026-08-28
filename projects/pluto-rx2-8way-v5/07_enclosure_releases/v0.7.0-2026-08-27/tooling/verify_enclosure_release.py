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
import os
import re
import stat
import sys
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


def verify_release(release_dir: Path, project_root: Path | None = None,
                   *, require_directory_name: bool = True) -> dict[str, Any]:
    release_dir = _plain_directory(release_dir, "release")
    actual_files, _ = scan_regular_tree(release_dir)
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
        composition_loaded = composition.validate_config_v2(
            replay_value, release_dir,
            release_connector_compiler=(
                connector_replay["compiler_binding"]
                if connector_replay is not None else None))
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
