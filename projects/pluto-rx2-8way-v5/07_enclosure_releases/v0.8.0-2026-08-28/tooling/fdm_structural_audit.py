#!/usr/bin/env python3
"""Deterministic FDM/structural screen for declared enclosure printables.

This tool deliberately stops at CAD evidence.  It proves exact mesh identity,
closed authored censuses, and mesh-visible critical sections.  It does not
silently convert manifold topology into slicer, strength, fit, or physical
qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import stat
import struct
import sys
import types
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit("pcb-enclosure FDM audit needs PyYAML") from exc

CONTRACT_KIND = "pcb-enclosure-fdm-structural-contract-v1"
RECEIPT_KIND = "pcb-enclosure-fdm-structural-audit-v1"
CONFIG_KIND = "pcb-enclosure-config-v1"
GENERATION_KIND = "pcb-enclosure-generation-v1"
COMPILER_ROLE = "fdm_structural_audit"
COMPILER_SOURCE_PATH = "skills/pcb-enclosure/scripts/fdm_structural_audit.py"
COMPILER_RELEASE_PATH = "tooling/fdm_structural_audit.py"
HELPER_ROLE = "enclosure_common"
HELPER_SOURCE_PATH = "skills/pcb-enclosure/scripts/enclosure_common.py"
HELPER_RELEASE_PATH = "tooling/enclosure_common.py"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[_.-][a-z0-9]+)*$")
PART_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
EPS = 1e-8
PARALLEL_FRAME_TOLERANCE = 1e-6
MINIMUM_NONPARALLEL_ANGLE_DEG = 30.0


class AuditError(ValueError):
    """The contract, binding, mesh, or replay evidence is invalid."""


class _StrictLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _StrictLoader, node: yaml.MappingNode,
                       deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise AuditError("mapping keys must be scalar") from exc
        if duplicate:
            raise AuditError(
                f"duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AuditError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _ordinary(path: Path, where: str) -> Path:
    path = _absolute(path)
    for candidate in reversed((path, *path.parents)):
        if candidate.is_symlink():
            raise AuditError(f"{where}: symlink path is not accepted: {candidate}")
    try:
        info = path.lstat()
    except OSError as exc:
        raise AuditError(f"{where}: cannot inspect {path}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise AuditError(f"{where}: expected an ordinary file")
    if info.st_nlink != 1:
        raise AuditError(f"{where}: hard-linked files are not accepted")
    return path


def stable_bytes(path: Path, where: str) -> bytes:
    path = _ordinary(path, where)
    before = path.lstat()
    identity = (before.st_dev, before.st_ino, before.st_size,
                before.st_mtime_ns)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    payload = bytearray()
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_size,
                opened.st_mtime_ns) != identity:
            raise AuditError(f"{where}: file changed while opening")
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            payload.extend(chunk)
        finished = os.fstat(descriptor)
        if (finished.st_dev, finished.st_ino, finished.st_size,
                finished.st_mtime_ns) != identity:
            raise AuditError(f"{where}: file changed while reading")
    finally:
        os.close(descriptor)
    after = _ordinary(path, where).lstat()
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != identity \
            or len(payload) != before.st_size:
        raise AuditError(f"{where}: path changed while reading")
    return bytes(payload)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _binding_from_bytes(path: str, payload: bytes) -> dict[str, Any]:
    return {"path": path, "sha256": _sha(payload), "size": len(payload)}


def _compiler_binding(module_path: Path | None = None) -> dict[str, Any]:
    payload = stable_bytes(module_path or Path(__file__), "FDM audit compiler")
    return _binding_from_bytes(COMPILER_SOURCE_PATH, payload)


def _helper_binding(module_path: Path | None = None) -> dict[str, Any]:
    path = module_path or Path(__file__).resolve().with_name("enclosure_common.py")
    payload = stable_bytes(path, "schema-v1 validation helper")
    return _binding_from_bytes(HELPER_SOURCE_PATH, payload)


def _load_helper(path: Path, expected: Mapping[str, Any]):
    expected = _exact(expected, {"path", "sha256", "size"},
                      "schema-v1 helper binding")
    if expected["path"] != HELPER_SOURCE_PATH:
        raise AuditError("schema-v1 helper has noncanonical source path")
    payload = stable_bytes(path, "schema-v1 validation helper")
    if (_sha(payload), len(payload)) != (expected["sha256"], expected["size"]):
        raise AuditError("schema-v1 validation helper differs from bound bytes")
    module = types.ModuleType("pcb_enclosure_bound_enclosure_common")
    module.__file__ = str(path)
    module.__package__ = None
    try:
        code = compile(payload, str(path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception as exc:  # pragma: no cover - trusted runtime boundary
        raise AuditError(f"cannot execute schema-v1 validation helper: {exc}") from exc
    if not hasattr(module, "validate_config") or not hasattr(module, "EnclosureError"):
        raise AuditError("schema-v1 validation helper lacks required API")
    return module


def load_yaml(path: Path) -> dict[str, Any]:
    payload = stable_bytes(path, "YAML input")
    try:
        value = yaml.load(payload.decode("utf-8"), Loader=_StrictLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise AuditError(f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{path}: expected a YAML object")
    return value


def load_json(path: Path) -> dict[str, Any]:
    payload = stable_bytes(path, "JSON input")
    try:
        value = json.loads(payload, object_pairs_hook=_json_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{path}: expected a JSON object")
    return value


def write_json(path: Path, value: Mapping[str, Any], *,
               inputs: Iterable[Path] = (),
               regrade: Any = None) -> None:
    path = _absolute(path)
    input_stats: list[tuple[Path, os.stat_result]] = []
    for raw in inputs:
        source = _ordinary(raw, "audit protected input")
        input_stats.append((source, source.lstat()))
        if path == source:
            raise AuditError(f"audit output aliases input {source}")
    for candidate in reversed((path.parent, *path.parent.parents)):
        if candidate.exists() and candidate.is_symlink():
            raise AuditError(f"audit output has symlink parent {candidate}")
    path.parent.mkdir(parents=True, exist_ok=True)
    parent_before = path.parent.lstat()
    directory_fd = os.open(
        path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) |
        getattr(os, "O_NOFOLLOW", 0))
    opened_parent = os.fstat(directory_fd)
    parent_identity = (opened_parent.st_dev, opened_parent.st_ino)
    if parent_identity != (parent_before.st_dev, parent_before.st_ino):
        os.close(directory_fd)
        raise AuditError("audit output parent changed while opening")
    temporary_name = f".{path.name}.{secrets.token_hex(12)}.tmp"
    descriptor = -1
    published_identity: tuple[int, int] | None = None

    def read_named() -> tuple[os.stat_result, bytes]:
        info = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise AuditError("published audit output is not an ordinary file")
        fd = os.open(path.name, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                     dir_fd=directory_fd)
        content = bytearray()
        try:
            opened = os.fstat(fd)
            if (opened.st_dev, opened.st_ino, opened.st_size,
                    opened.st_mtime_ns) != \
                    (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
                raise AuditError("published audit output changed while opening")
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                content.extend(chunk)
            final = os.fstat(fd)
            if (final.st_dev, final.st_ino, final.st_size, final.st_mtime_ns) != \
                    (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns):
                raise AuditError("published audit output changed while reading")
        finally:
            os.close(fd)
        return info, bytes(content)

    def remove_ours() -> None:
        if published_identity is None:
            return
        try:
            current = os.stat(path.name, dir_fd=directory_fd,
                              follow_symlinks=False)
        except FileNotFoundError:
            return
        if (current.st_dev, current.st_ino) == published_identity:
            os.unlink(path.name, dir_fd=directory_fd)
            os.fsync(directory_fd)
    try:
        try:
            existing = os.stat(path.name, dir_fd=directory_fd,
                               follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if not stat.S_ISREG(existing.st_mode) or stat.S_ISLNK(existing.st_mode):
                raise AuditError("audit output destination is not an ordinary file")
            for source, source_info in input_stats:
                if (existing.st_dev, existing.st_ino) == \
                        (source_info.st_dev, source_info.st_ino):
                    raise AuditError(f"audit output aliases input {source}")
        descriptor = os.open(
            temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
            getattr(os, "O_NOFOLLOW", 0), 0o600, dir_fd=directory_fd)
        payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o644, dir_fd=directory_fd,
                 follow_symlinks=False)
        staged = os.stat(temporary_name, dir_fd=directory_fd,
                         follow_symlinks=False)
        if regrade is not None and regrade() != value:
            raise AuditError(
                "audit inputs changed before output publication; fresh regrade differs")
        parent_after = path.parent.lstat()
        if (parent_after.st_dev, parent_after.st_ino) != parent_identity:
            raise AuditError("audit output parent path changed before publication")
        for source, source_info in input_stats:
            final_info = _ordinary(source, "audit protected input").lstat()
            if (final_info.st_dev, final_info.st_ino, final_info.st_size,
                    final_info.st_mtime_ns) != \
                    (source_info.st_dev, source_info.st_ino, source_info.st_size,
                     source_info.st_mtime_ns):
                raise AuditError(f"audit protected input changed: {source}")
        os.rename(temporary_name, path.name, src_dir_fd=directory_fd,
                  dst_dir_fd=directory_fd)
        os.fsync(directory_fd)
        published_identity = (staged.st_dev, staged.st_ino)
        published, named_payload = read_named()
        if (published.st_dev, published.st_ino) != published_identity or \
                named_payload != payload:
            remove_ours()
            raise AuditError("published audit output bytes/inode differ from staged output")
        if regrade is not None:
            try:
                fresh = regrade()
            except BaseException:
                remove_ours()
                raise
            if fresh != value:
                remove_ours()
                raise AuditError(
                    "audit inputs changed after publication; removed only the "
                    "just-published stale receipt")
        final, final_payload = read_named()
        if (final.st_dev, final.st_ino) != published_identity or \
                final_payload != payload:
            remove_ours()
            raise AuditError("published audit output changed during final verification")
    except BaseException:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if published_identity is None:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
        raise
    finally:
        try:
            os.close(directory_fd)
        except OSError:
            pass


def _safe_bound_path(root: Path, relative: Any, where: str) -> Path:
    text = _string(relative, where)
    candidate = Path(text)
    if candidate.is_absolute() or "\\" in text or not candidate.parts or \
            any(part in {"", ".", ".."} for part in candidate.parts):
        raise AuditError(f"{where}: expected normalized relative path")
    root = _absolute(root)
    path = _absolute(root / candidate)
    if path == root or not path.is_relative_to(root):
        raise AuditError(f"{where}: path escapes root")
    return _ordinary(path, where)


def validate_config_bindings(config: Mapping[str, Any], root: Path
                            ) -> list[Path]:
    """Reopen every exact v1 subject/CAD binding under one explicit root."""
    root = _absolute(root)
    if not root.is_dir() or root.is_symlink():
        raise AuditError("audit root must be an ordinary directory")
    bound: list[Path] = []
    subject = _mapping(config.get("subject"), "config.subject")
    for field in ("release_manifest", "pcb", "step", "interface"):
        if field not in subject:
            continue
        row = _exact(subject[field], {"path", "sha256", "size"},
                     f"config.subject.{field}")
        path = _safe_bound_path(root, row["path"],
                                f"config.subject.{field}.path")
        payload = stable_bytes(path, f"config.subject.{field}")
        if not HEX64_RE.fullmatch(_string(row["sha256"],
                                          f"config.subject.{field}.sha256")) or \
                isinstance(row["size"], bool) or not isinstance(row["size"], int) or \
                row["size"] <= 0 or _sha(payload) != row["sha256"] or \
                len(payload) != row["size"]:
            raise AuditError(f"config.subject.{field}: stale binding")
        bound.append(path)
    cad = _mapping(config.get("cad"), "config.cad")
    if "source" in cad:
        source = _exact(cad["source"], {"kind", "path", "sha256", "size"},
                        "config.cad.source")
        path = _safe_bound_path(root, source["path"], "config.cad.source.path")
        payload = stable_bytes(path, "config.cad.source")
        if source["kind"] != "authored_scad" or \
                not HEX64_RE.fullmatch(_string(source["sha256"],
                                              "config.cad.source.sha256")) or \
                isinstance(source["size"], bool) or \
                not isinstance(source["size"], int) or source["size"] <= 0 or \
                _sha(payload) != source["sha256"] or len(payload) != source["size"]:
            raise AuditError("config.cad.source: stale binding")
        bound.append(path)
    if len(bound) < 3:
        raise AuditError("CAD subject binding denominator is too small")
    return bound


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuditError(f"{where}: expected object")
    return value


def _exact(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    row = _mapping(value, where)
    if set(row) != fields:
        raise AuditError(
            f"{where}: fields differ; missing={sorted(fields - set(row))}, "
            f"unknown={sorted(set(row) - fields)}")
    return row


def _string(value: Any, where: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise AuditError(f"{where}: expected {'nonempty ' if nonempty else ''}string")
    return value


def _identifier(value: Any, where: str) -> str:
    value = _string(value, where)
    if not ID_RE.fullmatch(value):
        raise AuditError(f"{where}: expected normalized identifier")
    return value


def _number(value: Any, where: str, *, positive: bool = False,
            nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or \
            not math.isfinite(value):
        raise AuditError(f"{where}: expected finite number")
    number = float(value)
    if positive and number <= 0:
        raise AuditError(f"{where}: expected > 0")
    if nonnegative and number < 0:
        raise AuditError(f"{where}: expected >= 0")
    return number


def _vec(value: Any, count: int, where: str) -> list[float]:
    if not isinstance(value, list) or len(value) != count:
        raise AuditError(f"{where}: expected {count}-vector")
    return [_number(item, f"{where}[{index}]")
            for index, item in enumerate(value)]


def _unique_ids(value: Any, where: str, *, allow_empty: bool = False,
                part_names: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise AuditError(f"{where}: expected {'possibly empty ' if allow_empty else ''}list")
    result = []
    pattern = PART_RE if part_names else ID_RE
    for index, raw in enumerate(value):
        item = _string(raw, f"{where}[{index}]")
        if not pattern.fullmatch(item):
            raise AuditError(f"{where}[{index}]: invalid identifier")
        result.append(item)
    if len(result) != len(set(result)):
        raise AuditError(f"{where}: duplicate identifier")
    return result


def _probe_plane_independence(
        root_plane: Mapping[str, Any], member_plane: Mapping[str, Any],
        profile: Mapping[str, Any], where: str) -> dict[str, Any]:
    """Require two probes to represent resolvably different section planes.

    Parallel planes are comparable only as one registered plane family: their
    in-plane axes align, their origins have no tangential offset, and their
    signed normal separation reaches one process-resolution step.  Otherwise
    the planes must differ by at least 30 degrees; a tiny tilt is not a second
    load-path witness.
    """
    root_normal = root_plane["normal"]
    member_normal = member_plane["normal"]
    normal_dot = max(-1.0, min(1.0, sum(
        root_normal[index] * member_normal[index] for index in range(3))))
    unoriented_dot = abs(normal_dot)
    minimum_linear_delta = max(
        float(profile["layer_mm"]), float(profile["nozzle_mm"]) / 2.0)
    delta = [
        member_plane["origin_mm"][index] - root_plane["origin_mm"][index]
        for index in range(3)]
    signed_normal_separation = sum(
        delta[index] * root_normal[index] for index in range(3))
    tangential = [
        delta[index] - signed_normal_separation * root_normal[index]
        for index in range(3)]
    tangential_offset = math.sqrt(sum(value * value for value in tangential))

    if unoriented_dot >= 1.0 - PARALLEL_FRAME_TOLERANCE:
        root_u = root_plane["u_axis"]
        member_u = member_plane["u_axis"]
        u_dot = abs(sum(root_u[index] * member_u[index]
                        for index in range(3)))
        if u_dot < 1.0 - PARALLEL_FRAME_TOLERANCE:
            raise AuditError(
                f"{where}: parallel root/member probes do not share a "
                "registered in-plane axis")
        if tangential_offset > PARALLEL_FRAME_TOLERANCE:
            raise AuditError(
                f"{where}: parallel root/member plane origins have "
                f"{tangential_offset:.6g} mm tangential offset; registered "
                "probe families require no tangential displacement")
        if abs(signed_normal_separation) + EPS < minimum_linear_delta:
            raise AuditError(
                f"{where}: parallel root/member signed normal separation is "
                f"only {abs(signed_normal_separation):.6g} mm; independent "
                "probes require at least one process-resolution step "
                f"({minimum_linear_delta:.6g} mm)")
        return {
            "relation": "registered_parallel",
            "unoriented_normal_angle_deg": 0.0,
            "signed_normal_separation_mm": signed_normal_separation,
            "tangential_offset_mm": tangential_offset,
            "minimum_linear_delta_mm": minimum_linear_delta,
        }

    angle = math.degrees(math.acos(unoriented_dot))
    if angle + 1e-9 < MINIMUM_NONPARALLEL_ANGLE_DEG:
        raise AuditError(
            f"{where}: root/member plane angle is only {angle:.6g} degrees; "
            "nonparallel probes require at least "
            f"{MINIMUM_NONPARALLEL_ANGLE_DEG:g} degrees")
    return {
        "relation": "materially_nonparallel",
        "unoriented_normal_angle_deg": angle,
        "signed_normal_separation_mm": None,
        "tangential_offset_mm": None,
        "minimum_linear_delta_mm": minimum_linear_delta,
    }


def _process_resolved_material_change(
        root_area: float, member_area: float, root_span: float,
        member_span: float, profile: Mapping[str, Any]) -> dict[str, Any]:
    """Grade section change against one deposited-road/process increment."""
    area_delta = abs(root_area - member_area)
    span_delta = abs(root_span - member_span)
    minimum_area_delta = (float(profile["nozzle_mm"]) *
                          float(profile["layer_mm"]))
    minimum_span_delta = max(
        float(profile["layer_mm"]), float(profile["nozzle_mm"]) / 2.0)
    return {
        "independent": (
            area_delta + EPS >= minimum_area_delta or
            span_delta + EPS >= minimum_span_delta),
        "area_delta_mm2": area_delta,
        "minimum_area_delta_mm2": minimum_area_delta,
        "span_delta_mm": span_delta,
        "minimum_span_delta_mm": minimum_span_delta,
    }


def semantic_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return _sha(payload)


def design_fingerprint(config: Mapping[str, Any]) -> str:
    """Return a release-relocation-stable identity for represented CAD intent."""
    if config.get("schema") != 1 or config.get("kind") != CONFIG_KIND:
        raise AuditError("CAD design is not pcb-enclosure schema v1")
    subject = _mapping(config.get("subject"), "config.subject")
    subject_identity: dict[str, Any] = {"release": subject.get("release")}
    for field in ("release_manifest", "pcb", "step", "interface"):
        if field in subject:
            binding = _mapping(subject[field], f"config.subject.{field}")
            subject_identity[field] = {
                "sha256": binding.get("sha256"), "size": binding.get("size")}
    cad = dict(_mapping(config.get("cad"), "config.cad"))
    if "source" in cad:
        source = _mapping(cad["source"], "config.cad.source")
        cad["source"] = {key: source.get(key)
                         for key in ("kind", "sha256", "size")}
    represented = {
        "name": config.get("name"), "mode": config.get("mode"),
        "subject": subject_identity, "process": config.get("process"),
        "cad": cad, "geometry": config.get("geometry"),
        "fasteners": config.get("fasteners"),
        "interfaces": config.get("interfaces"), "thermal": config.get("thermal"),
        "physical_validation": config.get("physical_validation"),
    }
    return semantic_sha256(represented)


def _row_map(value: Any, where: str, *, allow_empty: bool = False,
             part_names: bool = False) -> dict[str, Mapping[str, Any]]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise AuditError(f"{where}: denominator is zero or not a list")
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(value):
        row = _mapping(raw, f"{where}[{index}]")
        ident = _string(row.get("id"), f"{where}[{index}].id")
        pattern = PART_RE if part_names else ID_RE
        if not pattern.fullmatch(ident):
            raise AuditError(f"{where}[{index}].id: invalid identifier")
        if ident in result:
            raise AuditError(f"{where}: duplicate id {ident}")
        result[ident] = row
    return result


def validate_contract(value: Mapping[str, Any], config: Mapping[str, Any]
                      ) -> dict[str, Any]:
    top = _exact(value, {
        "schema", "kind", "name", "design_fingerprint",
        "process_profiles", "parts", "load_cases", "attachments",
        "support_exceptions", "flexure_exceptions",
    }, "contract")
    if top["schema"] != 1 or isinstance(top["schema"], bool):
        raise AuditError("contract.schema: expected 1")
    if top["kind"] != CONTRACT_KIND:
        raise AuditError(f"contract.kind: expected {CONTRACT_KIND!r}")
    name = _identifier(top["name"], "contract.name")
    if name != config.get("name"):
        raise AuditError("contract.name differs from CAD design")
    fingerprint = _string(top["design_fingerprint"],
                          "contract.design_fingerprint")
    if not HEX64_RE.fullmatch(fingerprint) or fingerprint != design_fingerprint(config):
        raise AuditError("contract.design_fingerprint is stale for CAD design")

    profiles_raw = _row_map(top["process_profiles"],
                            "contract.process_profiles")
    profiles: dict[str, Any] = {}
    expected_process = config.get("process")
    for ident, raw in profiles_raw.items():
        row = _exact(raw, {
            "id", "method", "material", "nozzle_mm", "layer_mm",
            "minimum_wall_mm", "support_policy", "slicer",
        }, f"contract.process_profiles.{ident}")
        if row["slicer"] is not None:
            raise AuditError(
                f"contract.process_profiles.{ident}.slicer: v1 accepts only null; "
                "no canonical slicer adapter is implemented")
        represented = {key: row[key] for key in (
            "method", "material", "nozzle_mm", "layer_mm",
            "minimum_wall_mm", "support_policy")}
        if represented != expected_process:
            raise AuditError(
                f"contract.process_profiles.{ident}: differs from CAD process")
        profiles[ident] = dict(row)

    config_parts = config.get("cad", {}).get("printable_parts")
    if not isinstance(config_parts, list) or not config_parts:
        raise AuditError("CAD printable-part denominator is zero")
    parts_raw = _row_map(top["parts"], "contract.parts", part_names=True)
    if set(parts_raw) != set(config_parts):
        raise AuditError(
            "contract.parts census differs from CAD printable parts; "
            f"missing={sorted(set(config_parts) - set(parts_raw))}, "
            f"unknown={sorted(set(parts_raw) - set(config_parts))}")
    parts: dict[str, Any] = {}
    for ident, raw in parts_raw.items():
        row = _exact(raw, {
            "id", "process_profile", "mesh_to_build", "structural_disposition",
            "structural_reason", "attachment_ids", "support_exception_ids",
        }, f"contract.parts.{ident}")
        profile = _identifier(row["process_profile"],
                              f"contract.parts.{ident}.process_profile")
        if profile not in profiles:
            raise AuditError(f"contract.parts.{ident}: unknown process profile")
        matrix = row["mesh_to_build"]
        if not isinstance(matrix, list) or len(matrix) != 4:
            raise AuditError(f"contract.parts.{ident}.mesh_to_build: expected 4x4")
        matrix = [_vec(axis, 4,
                       f"contract.parts.{ident}.mesh_to_build[{index}]")
                  for index, axis in enumerate(matrix)]
        if any(abs(matrix[3][index] - expected) > EPS
               for index, expected in enumerate((0.0, 0.0, 0.0, 1.0))):
            raise AuditError(
                f"contract.parts.{ident}.mesh_to_build: non-affine last row")
        rotation = [row[:3] for row in matrix[:3]]
        for axis in range(3):
            norm = math.sqrt(sum(rotation[axis][index] ** 2
                                 for index in range(3)))
            if abs(norm - 1.0) > 1e-6:
                raise AuditError(
                    f"contract.parts.{ident}.mesh_to_build: rotation row "
                    f"{axis} is not unit length")
        for left in range(3):
            for right in range(left + 1, 3):
                dot = sum(rotation[left][index] * rotation[right][index]
                          for index in range(3))
                if abs(dot) > 1e-6:
                    raise AuditError(
                        f"contract.parts.{ident}.mesh_to_build: upper 3x3 "
                        "contains scale/shear")
        determinant = (
            rotation[0][0] * (rotation[1][1] * rotation[2][2] -
                              rotation[1][2] * rotation[2][1]) -
            rotation[0][1] * (rotation[1][0] * rotation[2][2] -
                              rotation[1][2] * rotation[2][0]) +
            rotation[0][2] * (rotation[1][0] * rotation[2][1] -
                              rotation[1][1] * rotation[2][0]))
        if abs(determinant - 1.0) > 1e-6:
            raise AuditError(
                f"contract.parts.{ident}.mesh_to_build: expected proper rigid "
                "transform with determinant +1")
        disposition = row["structural_disposition"]
        if disposition not in {"audited", "no_critical_attachment"}:
            raise AuditError(
                f"contract.parts.{ident}.structural_disposition: invalid value")
        reason = row["structural_reason"]
        attachments = _unique_ids(
            row["attachment_ids"], f"contract.parts.{ident}.attachment_ids",
            allow_empty=disposition == "no_critical_attachment")
        if disposition == "audited" and not attachments:
            raise AuditError(f"contract.parts.{ident}: audited denominator is zero")
        if disposition == "no_critical_attachment":
            _string(reason, f"contract.parts.{ident}.structural_reason")
            if attachments:
                raise AuditError(
                    f"contract.parts.{ident}: no-critical part names attachments")
        elif reason is not None:
            raise AuditError(
                f"contract.parts.{ident}.structural_reason: audited parts use null")
        supports = _unique_ids(
            row["support_exception_ids"],
            f"contract.parts.{ident}.support_exception_ids", allow_empty=True)
        parts[ident] = {**dict(row), "mesh_to_build": matrix,
                        "attachment_ids": attachments,
                        "support_exception_ids": supports}

    loads_raw = _row_map(top["load_cases"], "contract.load_cases")
    loads: dict[str, Any] = {}
    for ident, raw in loads_raw.items():
        row = _exact(raw, {"id", "description", "direction_local",
                           "application", "reaction"},
                     f"contract.load_cases.{ident}")
        _string(row["description"], f"contract.load_cases.{ident}.description")
        direction = _vec(row["direction_local"], 3,
                         f"contract.load_cases.{ident}.direction_local")
        if math.sqrt(sum(axis * axis for axis in direction)) <= EPS:
            raise AuditError(f"contract.load_cases.{ident}: zero direction")
        _string(row["application"], f"contract.load_cases.{ident}.application")
        _string(row["reaction"], f"contract.load_cases.{ident}.reaction")
        loads[ident] = dict(row)

    supports_raw = _row_map(top["support_exceptions"],
                            "contract.support_exceptions", allow_empty=True)
    supports: dict[str, Any] = {}
    for ident, raw in supports_raw.items():
        row = _exact(raw, {"id", "part", "region", "reason"},
                     f"contract.support_exceptions.{ident}")
        part = _string(row["part"], f"contract.support_exceptions.{ident}.part")
        if part not in parts:
            raise AuditError(f"contract.support_exceptions.{ident}: unknown part")
        _string(row["region"], f"contract.support_exceptions.{ident}.region")
        _string(row["reason"], f"contract.support_exceptions.{ident}.reason")
        supports[ident] = dict(row)
    declared_supports = {
        ident for part in parts.values() for ident in part["support_exception_ids"]}
    if declared_supports != set(supports):
        raise AuditError(
            "support-exception census differs from part declarations; "
            f"missing={sorted(set(supports) - declared_supports)}, "
            f"unknown={sorted(declared_supports - set(supports))}")
    for ident, row in supports.items():
        if ident not in parts[row["part"]]["support_exception_ids"]:
            raise AuditError(f"support exception {ident}: wrong owning part")

    flex_raw = _row_map(top["flexure_exceptions"],
                        "contract.flexure_exceptions", allow_empty=True)
    flexures: dict[str, Any] = {}
    for ident, raw in flex_raw.items():
        row = _exact(raw, {"id", "type", "attachment_id", "rationale",
                           "hard_stop", "physical_test_id"},
                     f"contract.flexure_exceptions.{ident}")
        if row["type"] != "intentional_flexure":
            raise AuditError(f"flexure exception {ident}: closed type is intentional_flexure")
        _identifier(row["attachment_id"],
                    f"contract.flexure_exceptions.{ident}.attachment_id")
        _string(row["rationale"], f"contract.flexure_exceptions.{ident}.rationale")
        _string(row["hard_stop"], f"contract.flexure_exceptions.{ident}.hard_stop")
        _identifier(row["physical_test_id"],
                    f"contract.flexure_exceptions.{ident}.physical_test_id")
        flexures[ident] = dict(row)

    attachments_raw = _row_map(top["attachments"], "contract.attachments")
    attachments: dict[str, Any] = {}
    for ident, raw in attachments_raw.items():
        row = _exact(raw, {
            "id", "part", "scope", "host", "member", "function",
            "load_cases", "root_sections", "reinforcement", "overlap",
            "exception_id",
        }, f"contract.attachments.{ident}")
        part = _string(row["part"], f"contract.attachments.{ident}.part")
        if part not in parts:
            raise AuditError(f"contract.attachments.{ident}: unknown part")
        scope = _identifier(row["scope"], f"contract.attachments.{ident}.scope")
        for field in ("host", "member", "function"):
            _string(row[field], f"contract.attachments.{ident}.{field}")
        load_ids = _unique_ids(row["load_cases"],
                               f"contract.attachments.{ident}.load_cases")
        unknown_loads = set(load_ids) - set(loads)
        if unknown_loads:
            raise AuditError(
                f"contract.attachments.{ident}: unknown load cases {sorted(unknown_loads)}")
        section_raw = _row_map(row["root_sections"],
                               f"contract.attachments.{ident}.root_sections")
        if len(section_raw) < 2:
            raise AuditError(
                f"contract.attachments.{ident}.root_sections: at least two "
                "distinct section probes are required")
        sections: dict[str, Any] = {}
        for section_id, section_value in section_raw.items():
            section = _exact(section_value, {
                "id", "plane", "roi_uv_mm", "minimum_area_mm2", "throat",
            }, f"contract.attachments.{ident}.root_sections.{section_id}")
            plane = _exact(section["plane"], {"origin_mm", "normal", "u_axis"},
                           f"contract.attachments.{ident}.{section_id}.plane")
            origin = _vec(plane["origin_mm"], 3,
                          f"contract.attachments.{ident}.{section_id}.origin_mm")
            normal = _vec(plane["normal"], 3,
                          f"contract.attachments.{ident}.{section_id}.normal")
            u_axis = _vec(plane["u_axis"], 3,
                          f"contract.attachments.{ident}.{section_id}.u_axis")
            nn = math.sqrt(sum(axis * axis for axis in normal))
            un = math.sqrt(sum(axis * axis for axis in u_axis))
            dot = sum(normal[index] * u_axis[index] for index in range(3))
            if abs(nn - 1.0) > 1e-6 or abs(un - 1.0) > 1e-6 or abs(dot) > 1e-6:
                raise AuditError(
                    f"contract.attachments.{ident}.{section_id}.plane: "
                    "normal/u_axis must be orthonormal unit vectors")
            roi = _vec(section["roi_uv_mm"], 4,
                       f"contract.attachments.{ident}.{section_id}.roi_uv_mm")
            if roi[0] >= roi[2] or roi[1] >= roi[3]:
                raise AuditError(
                    f"contract.attachments.{ident}.{section_id}.roi_uv_mm: empty ROI")
            minimum_area = _number(
                section["minimum_area_mm2"],
                f"contract.attachments.{ident}.{section_id}.minimum_area_mm2",
                positive=True)
            throat = _exact(section["throat"], {
                "axis", "coordinate_mm", "interval_mm",
                "minimum_material_span_mm",
            }, f"contract.attachments.{ident}.{section_id}.throat")
            if throat["axis"] not in {"u", "v"}:
                raise AuditError(
                    f"contract.attachments.{ident}.{section_id}.throat.axis: expected u|v")
            coordinate = _number(
                throat["coordinate_mm"],
                f"contract.attachments.{ident}.{section_id}.throat.coordinate_mm")
            interval = _vec(
                throat["interval_mm"], 2,
                f"contract.attachments.{ident}.{section_id}.throat.interval_mm")
            if interval[0] >= interval[1]:
                raise AuditError(
                    f"contract.attachments.{ident}.{section_id}.throat.interval_mm: empty")
            minimum_span = _number(
                throat["minimum_material_span_mm"],
                f"contract.attachments.{ident}.{section_id}.throat.minimum_material_span_mm",
                positive=True)
            sections[section_id] = {
                "id": section_id,
                "plane": {"origin_mm": origin, "normal": normal, "u_axis": u_axis},
                "roi_uv_mm": roi, "minimum_area_mm2": minimum_area,
                "throat": {"axis": throat["axis"], "coordinate_mm": coordinate,
                           "interval_mm": interval,
                           "minimum_material_span_mm": minimum_span},
            }
        reinforcement = _exact(row["reinforcement"], {
            "kind", "root_section", "member_section", "minimum_area_ratio",
        }, f"contract.attachments.{ident}.reinforcement")
        if reinforcement["kind"] not in {
                "none", "fillet", "gusset", "rib", "blended_tab",
                "continuous_section"}:
            raise AuditError(f"contract.attachments.{ident}.reinforcement.kind: invalid")
        root_section = _identifier(
            reinforcement["root_section"],
            f"contract.attachments.{ident}.reinforcement.root_section")
        member_section = _identifier(
            reinforcement["member_section"],
            f"contract.attachments.{ident}.reinforcement.member_section")
        if root_section not in sections or member_section not in sections:
            raise AuditError(f"contract.attachments.{ident}.reinforcement: unknown section")
        if root_section == member_section:
            raise AuditError(
                f"contract.attachments.{ident}.reinforcement: root_section and "
                "member_section must differ")
        root_semantics = {key: value for key, value in sections[root_section].items()
                          if key != "id"}
        member_semantics = {
            key: value for key, value in sections[member_section].items()
            if key != "id"}
        if semantic_sha256(root_semantics) == semantic_sha256(member_semantics):
            raise AuditError(
                f"contract.attachments.{ident}.reinforcement: root/member "
                "section probes are semantically identical")
        profile = profiles[parts[part]["process_profile"]]
        plane_independence = _probe_plane_independence(
            sections[root_section]["plane"],
            sections[member_section]["plane"], profile,
            f"contract.attachments.{ident}.reinforcement")
        ratio = _number(
            reinforcement["minimum_area_ratio"],
            f"contract.attachments.{ident}.reinforcement.minimum_area_ratio",
            positive=True)
        overlap = _exact(row["overlap"], {"disposition", "section_id", "reason"},
                         f"contract.attachments.{ident}.overlap")
        if overlap["disposition"] not in {
                "section_proved", "not_separately_observable"}:
            raise AuditError(f"contract.attachments.{ident}.overlap.disposition: invalid")
        if overlap["disposition"] == "section_proved":
            section_id = _identifier(
                overlap["section_id"],
                f"contract.attachments.{ident}.overlap.section_id")
            if section_id not in sections or overlap["reason"] is not None:
                raise AuditError(f"contract.attachments.{ident}.overlap: bad section proof")
        else:
            if overlap["section_id"] is not None:
                raise AuditError(f"contract.attachments.{ident}.overlap: section must be null")
            _string(overlap["reason"],
                    f"contract.attachments.{ident}.overlap.reason")
        exception_id = row["exception_id"]
        if exception_id is not None:
            exception_id = _identifier(
                exception_id, f"contract.attachments.{ident}.exception_id")
            if exception_id not in flexures:
                raise AuditError(f"contract.attachments.{ident}: unknown flexure exception")
        attachments[ident] = {
            **dict(row), "scope": scope, "load_cases": load_ids,
            "root_sections": sections, "reinforcement": dict(reinforcement),
            "probe_plane_independence": plane_independence,
            "overlap": dict(overlap), "exception_id": exception_id,
        }

    declared_attachments = {
        ident for part in parts.values() for ident in part["attachment_ids"]}
    if declared_attachments != set(attachments):
        raise AuditError(
            "attachment census differs from part declarations; "
            f"missing={sorted(set(attachments) - declared_attachments)}, "
            f"unknown={sorted(declared_attachments - set(attachments))}")
    for ident, row in attachments.items():
        if ident not in parts[row["part"]]["attachment_ids"]:
            raise AuditError(f"attachment {ident}: wrong owning part")
    referenced_loads = {
        load_id for row in attachments.values()
        for load_id in row["load_cases"]
    }
    if referenced_loads != set(loads):
        raise AuditError(
            "load-case census differs from attachment references; "
            f"missing={sorted(set(loads) - referenced_loads)}, "
            f"unknown={sorted(referenced_loads - set(loads))}")
    referenced_flexures = {
        row["exception_id"] for row in attachments.values()
        if row["exception_id"] is not None}
    if referenced_flexures != set(flexures):
        raise AuditError(
            "flexure-exception census differs from attachment references; "
            f"missing={sorted(set(flexures) - referenced_flexures)}, "
            f"unknown={sorted(referenced_flexures - set(flexures))}")
    for ident, row in flexures.items():
        attachment_id = row["attachment_id"]
        if attachment_id not in attachments or \
                attachments[attachment_id]["exception_id"] != ident:
            raise AuditError(f"flexure exception {ident}: attachment cross-link differs")

    return {
        "name": name, "fingerprint": fingerprint, "profiles": profiles,
        "parts": parts, "load_cases": loads, "attachments": attachments,
        "support_exceptions": supports, "flexure_exceptions": flexures,
    }


def _stl_triangles(payload: bytes, where: str
                  ) -> list[tuple[tuple[float, float, float], ...]]:
    triangles: list[tuple[tuple[float, float, float], ...]] = []
    if len(payload) >= 84:
        count = struct.unpack_from("<I", payload, 80)[0]
        if 84 + count * 50 == len(payload):
            for index in range(count):
                values = struct.unpack_from("<12f", payload, 84 + index * 50)
                triangles.append((tuple(values[3:6]), tuple(values[6:9]),
                                  tuple(values[9:12])))
    if not triangles:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AuditError(f"{where}: malformed STL") from exc
        vertices = [tuple(map(float, match.groups())) for match in re.finditer(
            r"\bvertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)",
            text)]
        if not vertices or len(vertices) % 3:
            raise AuditError(f"{where}: malformed ASCII STL vertex count")
        triangles = [tuple(vertices[index:index + 3])
                     for index in range(0, len(vertices), 3)]
    if not triangles or any(not math.isfinite(axis) for tri in triangles
                            for vertex in tri for axis in vertex):
        raise AuditError(f"{where}: zero or non-finite triangles")
    return triangles


def _mesh_metrics(triangles: Sequence[Sequence[Sequence[float]]],
                  payload: bytes) -> dict[str, Any]:
    def key(vertex: Sequence[float]) -> tuple[int, int, int]:
        return tuple(round(axis / 1e-6) for axis in vertex)  # type: ignore[return-value]
    edge_counts: Counter[Any] = Counter()
    directed: Counter[Any] = Counter()
    edge_triangles: defaultdict[Any, list[int]] = defaultdict(list)
    degenerate = 0
    volume6 = 0.0
    xs: list[float] = []; ys: list[float] = []; zs: list[float] = []
    for index, triangle in enumerate(triangles):
        a, b, c = triangle
        xs.extend((a[0], b[0], c[0])); ys.extend((a[1], b[1], c[1]))
        zs.extend((a[2], b[2], c[2]))
        ab = tuple(b[i] - a[i] for i in range(3))
        ac = tuple(c[i] - a[i] for i in range(3))
        cross = (ab[1] * ac[2] - ab[2] * ac[1],
                 ab[2] * ac[0] - ab[0] * ac[2],
                 ab[0] * ac[1] - ab[1] * ac[0])
        if math.sqrt(sum(axis * axis for axis in cross)) <= 1e-12:
            degenerate += 1
        volume6 += (a[0] * (b[1] * c[2] - b[2] * c[1]) -
                    a[1] * (b[0] * c[2] - b[2] * c[0]) +
                    a[2] * (b[0] * c[1] - b[1] * c[0]))
        keys = [key(vertex) for vertex in triangle]
        for left, right in ((keys[0], keys[1]), (keys[1], keys[2]),
                            (keys[2], keys[0])):
            edge = tuple(sorted((left, right)))
            edge_counts[edge] += 1
            directed[(left, right)] += 1
            edge_triangles[edge].append(index)
    neighbors: defaultdict[int, set[int]] = defaultdict(set)
    for owners in edge_triangles.values():
        for left in owners:
            neighbors[left].update(right for right in owners if right != left)
    unseen = set(range(len(triangles)))
    components = 0
    while unseen:
        components += 1
        queue = deque([unseen.pop()])
        while queue:
            current = queue.popleft()
            for other in neighbors[current]:
                if other in unseen:
                    unseen.remove(other); queue.append(other)
    mismatches = sum(
        1 for edge, count in edge_counts.items()
        if count == 2 and not (directed[(edge[0], edge[1])] == 1 and
                               directed[(edge[1], edge[0])] == 1))
    return {
        "sha256": _sha(payload), "size": len(payload),
        "triangles": len(triangles), "components": components,
        "edge_manifold": all(count == 2 for count in edge_counts.values()),
        "nonmanifold_edges": sum(1 for count in edge_counts.values() if count != 2),
        "orientation_consistent": mismatches == 0,
        "orientation_mismatches": mismatches,
        "degenerate_facets": degenerate,
        "absolute_volume_mm3": abs(volume6 / 6.0),
        "bbox_mm": {"min": [min(xs), min(ys), min(zs)],
                    "max": [max(xs), max(ys), max(zs)]},
    }


def _sub(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return tuple(a[i] - b[i] for i in range(3))  # type: ignore[return-value]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(a[i] * b[i] for i in range(3))


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _section_loops(triangles: Sequence[Sequence[Sequence[float]]],
                   plane: Mapping[str, Sequence[float]]) -> list[list[tuple[float, float]]]:
    origin = plane["origin_mm"]; normal = plane["normal"]; u_axis = plane["u_axis"]
    v_axis = _cross(normal, u_axis)
    segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for triangle in triangles:
        distances = [_dot(_sub(vertex, origin), normal) for vertex in triangle]
        if max(distances) < -EPS or min(distances) > EPS:
            continue
        if sum(abs(value) <= EPS for value in distances) >= 2:
            raise AuditError(
                "section plane is coplanar with a mesh edge; move the probe off mesh vertices")
        intersections: list[tuple[float, float, float]] = []
        for left, right in ((0, 1), (1, 2), (2, 0)):
            dl, dr = distances[left], distances[right]
            if abs(dl) <= EPS:
                intersections.append(tuple(triangle[left]))
            elif dl * dr < -EPS * EPS:
                ratio = dl / (dl - dr)
                intersections.append(tuple(
                    triangle[left][axis] + ratio *
                    (triangle[right][axis] - triangle[left][axis])
                    for axis in range(3)))
        unique: list[tuple[float, float, float]] = []
        for point in intersections:
            if not any(math.dist(point, other) <= 1e-7 for other in unique):
                unique.append(point)
        if len(unique) == 2:
            projected = []
            for point in unique:
                relative = _sub(point, origin)
                projected.append((_dot(relative, u_axis), _dot(relative, v_axis)))
            if math.dist(projected[0], projected[1]) > 1e-8:
                segments.append((projected[0], projected[1]))
        elif len(unique) not in {0}:
            raise AuditError("section plane produced an ambiguous triangle intersection")
    if not segments:
        raise AuditError("section plane has zero mesh intersection")

    def key(point: Sequence[float]) -> tuple[int, int]:
        return (round(point[0] / 1e-6), round(point[1] / 1e-6))
    points: dict[tuple[int, int], tuple[float, float]] = {}
    adjacency: defaultdict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    edges: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for left, right in segments:
        lk, rk = key(left), key(right)
        if lk == rk:
            continue
        edge = tuple(sorted((lk, rk)))
        if edge in edges:
            continue
        edges.add(edge); points[lk] = left; points[rk] = right
        adjacency[lk].append(rk); adjacency[rk].append(lk)
    bad = [vertex for vertex, neighbors in adjacency.items() if len(neighbors) != 2]
    if bad:
        raise AuditError(
            f"section contours are not closed two-use loops ({len(bad)} bad vertices)")
    remaining = set(edges)
    loops: list[list[tuple[float, float]]] = []
    while remaining:
        first_edge = next(iter(remaining)); start, current = first_edge
        loop_keys = [start]
        previous = start
        remaining.remove(first_edge)
        while current != start:
            loop_keys.append(current)
            options = [candidate for candidate in adjacency[current]
                       if candidate != previous]
            if len(options) != 1:
                raise AuditError("section contour branch is ambiguous")
            following = options[0]
            edge = tuple(sorted((current, following)))
            if edge not in remaining and following != start:
                raise AuditError("section contour closes inconsistently")
            remaining.discard(edge)
            previous, current = current, following
            if len(loop_keys) > len(edges) + 1:
                raise AuditError("section contour did not close")
        if len(loop_keys) < 3:
            raise AuditError("section contour has fewer than three vertices")
        loops.append([points[item] for item in loop_keys])
    return loops


def _polygon_area(polygon: Sequence[Sequence[float]]) -> float:
    return 0.5 * sum(
        polygon[index][0] * polygon[(index + 1) % len(polygon)][1] -
        polygon[(index + 1) % len(polygon)][0] * polygon[index][1]
        for index in range(len(polygon)))


def _clip_polygon(polygon: list[tuple[float, float]], roi: Sequence[float]
                 ) -> list[tuple[float, float]]:
    result = polygon
    boundaries = [
        (0, roi[0], True), (0, roi[2], False),
        (1, roi[1], True), (1, roi[3], False),
    ]
    for axis, bound, keep_greater in boundaries:
        source = result; result = []
        if not source:
            break
        for index, end in enumerate(source):
            start = source[index - 1]
            start_inside = start[axis] >= bound - EPS if keep_greater else \
                start[axis] <= bound + EPS
            end_inside = end[axis] >= bound - EPS if keep_greater else \
                end[axis] <= bound + EPS
            if start_inside != end_inside:
                delta = end[axis] - start[axis]
                if abs(delta) <= EPS:
                    intersection = end
                else:
                    ratio = (bound - start[axis]) / delta
                    intersection = (start[0] + ratio * (end[0] - start[0]),
                                    start[1] + ratio * (end[1] - start[1]))
                result.append(intersection)
            if end_inside:
                result.append(end)
    return result


def _point_in_polygon(point: Sequence[float], polygon: Sequence[Sequence[float]]) -> bool:
    inside = False
    x, y = point
    for index, end in enumerate(polygon):
        start = polygon[index - 1]
        if ((start[1] > y) != (end[1] > y)):
            crossing = (end[0] - start[0]) * (y - start[1]) / \
                (end[1] - start[1]) + start[0]
            if x < crossing:
                inside = not inside
    return inside


def _section_area(loops: Sequence[list[tuple[float, float]]],
                  roi: Sequence[float]) -> float:
    total = 0.0
    for index, loop in enumerate(loops):
        sample = loop[0]
        depth = sum(1 for other_index, other in enumerate(loops)
                    if other_index != index and _point_in_polygon(sample, other))
        clipped = _clip_polygon(loop, roi)
        if len(clipped) >= 3:
            total += (-1.0 if depth % 2 else 1.0) * abs(_polygon_area(clipped))
    return max(0.0, total)


def _line_intersections(loop: Sequence[Sequence[float]], *, axis: str,
                        coordinate: float) -> list[float]:
    # axis is the varying coordinate; the other coordinate is fixed.
    varying = 0 if axis == "u" else 1
    fixed = 1 - varying
    crossings: list[float] = []
    for index, end in enumerate(loop):
        start = loop[index - 1]
        left, right = start[fixed], end[fixed]
        if (left <= coordinate < right) or (right <= coordinate < left):
            ratio = (coordinate - left) / (right - left)
            crossings.append(start[varying] + ratio *
                             (end[varying] - start[varying]))
    return crossings


def _material_span(loops: Sequence[list[tuple[float, float]]], *, axis: str,
                   coordinate: float, interval: Sequence[float]) -> float:
    crossings = sorted(value for loop in loops
                       for value in _line_intersections(
                           loop, axis=axis, coordinate=coordinate))
    if len(crossings) % 2:
        raise AuditError("throat line has an odd section-contour intersection count")
    spans = []
    for index in range(0, len(crossings), 2):
        low = max(interval[0], crossings[index])
        high = min(interval[1], crossings[index + 1])
        if high > low:
            spans.append((low, high))
    if not spans:
        return 0.0
    merged: list[list[float]] = []
    for low, high in spans:
        if not merged or low > merged[-1][1] + EPS:
            merged.append([low, high])
        else:
            merged[-1][1] = max(merged[-1][1], high)
    return sum(high - low for low, high in merged)


def _transform_point(matrix: Sequence[Sequence[float]], point: Sequence[float]
                    ) -> tuple[float, float, float]:
    homogeneous = [*point, 1.0]
    return tuple(sum(matrix[row][column] * homogeneous[column]
                     for column in range(4)) for row in range(3))  # type: ignore[return-value]


def _transform_triangles(matrix: Sequence[Sequence[float]], triangles):
    return [tuple(_transform_point(matrix, point) for point in triangle)
            for triangle in triangles]


def _status_domain(status: str, passed: int, denominator: int,
                   findings: Sequence[str], **extra: Any) -> dict[str, Any]:
    if denominator <= 0:
        raise AuditError("domain denominator is zero")
    return {"status": status, "passed": passed, "denominator": denominator,
            "findings": list(findings), **extra}


def audit(contract_value: Mapping[str, Any], config: Mapping[str, Any],
          generation: Mapping[str, Any], mesh_payloads: Mapping[str, bytes],
          *, contract_payload: bytes, config_payload: bytes,
          config_relative_path: str, generation_payload: bytes,
          compiler_path: Path | None = None,
          helper_path: Path | None = None) -> dict[str, Any]:
    contract = validate_contract(contract_value, config)
    expected_parts = list(config["cad"]["printable_parts"])
    if set(mesh_payloads) != set(expected_parts):
        raise AuditError(
            "mesh input census differs from declared printable parts; "
            f"missing={sorted(set(expected_parts) - set(mesh_payloads))}, "
            f"unknown={sorted(set(mesh_payloads) - set(expected_parts))}")
    if generation.get("schema") != 1 or generation.get("kind") != GENERATION_KIND:
        raise AuditError("generation receipt has wrong schema/kind")
    generation_config = _mapping(generation.get("config"), "generation.config")
    if set(generation_config) != {
            "path", "semantic_sha256", "raw_sha256"} or \
            generation_config.get("path") != config_relative_path or \
            generation_config.get("semantic_sha256") != semantic_sha256(config) or \
            generation_config.get("raw_sha256") != _sha(config_payload):
        raise AuditError(
            "generation config identity differs from the exact audited CAD design")
    rows = generation.get("parts")
    if not isinstance(rows, list) or not rows:
        raise AuditError("generation printable-part denominator is zero")
    generation_parts: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(rows):
        row = _mapping(raw, f"generation.parts[{index}]")
        ident = _string(row.get("part"), f"generation.parts[{index}].part")
        if ident in generation_parts:
            raise AuditError("generation has duplicate printable part")
        generation_parts[ident] = row
    if set(generation_parts) != set(expected_parts):
        raise AuditError("generation printable-part census differs from CAD design")
    configured_source = config.get("cad", {}).get("source")
    authority = generation.get("authority")
    if configured_source is not None:
        if not isinstance(authority, Mapping) or \
                authority.get("kind") != "authored_scad" or \
                not isinstance(authority.get("binding"), Mapping) or \
                (authority["binding"].get("path"),
                 authority["binding"].get("sha256"),
                 authority["binding"].get("size")) != \
                (configured_source["path"], configured_source["sha256"],
                 configured_source["size"]):
            raise AuditError("generation CAD authority is stale for authored source")
        source = _mapping(generation.get("source"), "generation.source")
        if (source.get("sha256"), source.get("size")) != \
                (configured_source["sha256"], configured_source["size"]):
            raise AuditError("generation source identity differs from authored source")

    mesh_metrics: dict[str, Any] = {}
    mesh_triangles: dict[str, Any] = {}
    mesh_findings: list[str] = []
    mesh_passed = 0
    for part in expected_parts:
        payload = mesh_payloads[part]
        row = generation_parts[part]
        if row.get("path") != f"{part}.stl" or \
                row.get("sha256") != _sha(payload) or row.get("size") != len(payload):
            raise AuditError(f"mesh {part}: differs from generation receipt")
        triangles = _stl_triangles(payload, f"mesh {part}")
        metrics = _mesh_metrics(triangles, payload)
        mesh_metrics[part] = metrics
        mesh_triangles[part] = _transform_triangles(
            contract["parts"][part]["mesh_to_build"], triangles)
        local = []
        if not metrics["edge_manifold"]:
            local.append(f"{part}: nonmanifold edges")
        if not metrics["orientation_consistent"]:
            local.append(f"{part}: inconsistent facet orientation")
        if metrics["components"] != 1:
            local.append(f"{part}: expected one connected component")
        if metrics["absolute_volume_mm3"] <= 1e-6:
            local.append(f"{part}: zero volume")
        if metrics["degenerate_facets"] / metrics["triangles"] > 0.002:
            local.append(f"{part}: degenerate facet rate exceeds 0.2 percent")
        if local:
            mesh_findings.extend(local)
        else:
            mesh_passed += 1
    mesh_topology_status = "FAIL" if mesh_findings else "PASS"
    # These are named gaps, not implied successes.  They keep the aggregate
    # mesh domain incomplete even when topology is clean.
    mesh_unexecuted = [
        "self-intersection analysis is not implemented",
        "local wall/thickness analysis is not implemented",
    ]
    mesh_domain = _status_domain(
        "FAIL" if mesh_findings else "INCOMPLETE", mesh_passed,
        len(expected_parts), mesh_findings + mesh_unexecuted,
        topology_status=mesh_topology_status,
        self_intersection_status="INCOMPLETE",
        local_thickness_status="INCOMPLETE", parts=mesh_metrics)

    orientation_findings: list[str] = []
    build_bboxes: dict[str, Any] = {}
    orientation_passed = len(contract["profiles"])
    build_plate_tolerance = 1e-5
    for part in expected_parts:
        vertices = [point for triangle in mesh_triangles[part]
                    for point in triangle]
        axes = [[point[index] for point in vertices] for index in range(3)]
        minimum = [min(axis) for axis in axes]
        maximum = [max(axis) for axis in axes]
        build_bboxes[part] = {"min": minimum, "max": maximum}
        if any(not math.isfinite(value) for value in [*minimum, *maximum]):
            orientation_findings.append(f"{part}: non-finite build-space bbox")
            continue
        if minimum[2] < -build_plate_tolerance:
            orientation_findings.append(
                f"{part}: build-space mesh extends below Z=0 by "
                f"{-minimum[2]:.6g} mm")
            continue
        if abs(minimum[2]) > build_plate_tolerance:
            orientation_findings.append(
                f"{part}: build-space mesh floats {minimum[2]:.6g} mm above Z=0")
            continue
        orientation_passed += 1
    load_alignment: list[dict[str, Any]] = []
    for attachment_id, attachment in contract["attachments"].items():
        rotation = [row[:3] for row in
                    contract["parts"][attachment["part"]]["mesh_to_build"][:3]]
        for load_id in attachment["load_cases"]:
            local = contract["load_cases"][load_id]["direction_local"]
            transformed = [sum(rotation[row][column] * local[column]
                               for column in range(3)) for row in range(3)]
            magnitude = math.sqrt(sum(value * value for value in transformed))
            load_alignment.append({
                "attachment": attachment_id, "load_case": load_id,
                "absolute_cosine_to_layer_normal": round(
                    abs(transformed[2]) / magnitude, 9),
                "interpretation": (
                    "informational only; no project threshold is declared"),
            })
    orientation_denominator = len(expected_parts) + len(contract["profiles"])
    orientation_domain = _status_domain(
        "FAIL" if orientation_findings else "INCOMPLETE", orientation_passed,
        orientation_denominator,
        orientation_findings + [
            "printer build-volume check is unavailable without a pinned printer"],
        declaration_status="PASS",
        build_plate_contact_status=(
            "FAIL" if orientation_findings else "PASS"),
        build_volume_status="INCOMPLETE",
        build_plate_tolerance_mm=build_plate_tolerance,
        build_space_bboxes=build_bboxes,
        layer_normal_load_alignment=load_alignment,
        part_transforms={part: contract["parts"][part]["mesh_to_build"]
                         for part in expected_parts},
        process_profiles=list(contract["profiles"]))

    structural_findings: list[str] = []
    structural_rows: dict[str, Any] = {}
    probe_denominator = 0
    probe_passed = 0
    for attachment_id, attachment in contract["attachments"].items():
        part = attachment["part"]
        sections: dict[str, Any] = {}
        for section_id, section in attachment["root_sections"].items():
            probe_denominator += 2
            # Keep the authored threshold available even when contour
            # extraction itself fails. A bad/off-mesh probe is a deterministic
            # structural FAIL with its original AuditError, never a compiler
            # crash from an uninitialised local.
            throat = section["throat"]
            try:
                loops = _section_loops(mesh_triangles[part], section["plane"])
                area = _section_area(loops, section["roi_uv_mm"])
                span = _material_span(
                    loops, axis=throat["axis"],
                    coordinate=throat["coordinate_mm"],
                    interval=throat["interval_mm"])
            except AuditError as exc:
                area = 0.0; span = 0.0
                structural_findings.append(
                    f"{attachment_id}/{section_id}: {exc}")
            area_ok = area + 1e-6 >= section["minimum_area_mm2"]
            span_ok = span + 1e-6 >= throat["minimum_material_span_mm"]
            probe_passed += int(area_ok) + int(span_ok)
            if not area_ok:
                structural_findings.append(
                    f"{attachment_id}/{section_id}: area {area:.6g} mm^2 < "
                    f"{section['minimum_area_mm2']:.6g} mm^2")
            if not span_ok:
                structural_findings.append(
                    f"{attachment_id}/{section_id}: net section material span "
                    f"{span:.6g} mm < "
                    f"{throat['minimum_material_span_mm']:.6g} mm")
            sections[section_id] = {
                "area_mm2": round(area, 9),
                "minimum_area_mm2": section["minimum_area_mm2"],
                "net_section_material_span_mm": round(span, 9),
                "minimum_material_span_mm": throat["minimum_material_span_mm"],
                "status": "PASS" if area_ok and span_ok else "FAIL",
            }
        reinforcement = attachment["reinforcement"]
        probe_denominator += 1
        root_area = sections[reinforcement["root_section"]]["area_mm2"]
        member_area = sections[reinforcement["member_section"]]["area_mm2"]
        root_span = sections[reinforcement["root_section"]][
            "net_section_material_span_mm"]
        member_span = sections[reinforcement["member_section"]][
            "net_section_material_span_mm"]
        ratio = root_area / member_area if member_area > EPS else 0.0
        profile = contract["profiles"][
            contract["parts"][part]["process_profile"]]
        material_change = _process_resolved_material_change(
            root_area, member_area, root_span, member_span, profile)
        independently_measured = material_change["independent"]
        ratio_ok = reinforcement["kind"] != "none" and \
            ratio + 1e-6 >= reinforcement["minimum_area_ratio"]
        reinforcement_ok = independently_measured and ratio_ok
        if attachment["exception_id"] is not None:
            # A typed flexure is honest but cannot establish strength from this
            # rigid-section screen.  Physical qualification remains separate.
            reinforcement_ok = True
        probe_passed += int(reinforcement_ok)
        if not independently_measured:
            structural_findings.append(
                f"{attachment_id}: root/member probes measure a sub-process "
                f"material change (area delta "
                f"{material_change['area_delta_mm2']:.6g} mm^2 < "
                f"{material_change['minimum_area_delta_mm2']:.6g} mm^2 and "
                f"span delta {material_change['span_delta_mm']:.6g} mm < "
                f"{material_change['minimum_span_delta_mm']:.6g} mm); "
                "the attachment-to-host transition is not independently witnessed")
        if not ratio_ok and attachment["exception_id"] is None:
            structural_findings.append(
                f"{attachment_id}: reinforcement {reinforcement['kind']} has "
                f"root/member area ratio {ratio:.6g} < "
                f"{reinforcement['minimum_area_ratio']:.6g}")
        structural_rows[attachment_id] = {
            "part": part, "scope": attachment["scope"],
            "load_cases": attachment["load_cases"], "sections": sections,
            "reinforcement": {
                "kind": reinforcement["kind"],
                "root_member_area_ratio": round(ratio, 9),
                "minimum_area_ratio": reinforcement["minimum_area_ratio"],
                "independent_section_measurement": independently_measured,
                "plane_independence": attachment[
                    "probe_plane_independence"],
                "material_change": {
                    key: (round(value, 9) if isinstance(value, float) else value)
                    for key, value in material_change.items()
                },
                "status": "PASS" if reinforcement_ok else "FAIL",
            },
            "overlap": attachment["overlap"],
            "exception_id": attachment["exception_id"],
        }
    if probe_denominator <= 0:
        raise AuditError("structural probe denominator is zero")
    structural_domain = _status_domain(
        "FAIL" if structural_findings else "PASS", probe_passed,
        probe_denominator, structural_findings,
        attachment_count=len(contract["attachments"]),
        load_case_count=len(contract["load_cases"]),
        attachments=structural_rows,
        qualification_boundary=(
            "critical-section geometry screen only; loads are not quantified "
            "and material/print strength is not qualified"))

    profile_count = len(contract["profiles"])
    process_findings = [
        "no canonical slicer/profile/toolpath adapter is bound",
        "overhang and support-material analysis is not implemented",
        "unsupported-island and bridge analysis is not implemented",
        "global plate torsion, stiffness, and distributed load analysis is not implemented",
    ]
    process_domain = _status_domain(
        "INCOMPLETE", 0, profile_count, process_findings,
        slicer_status="INCOMPLETE", overhang_status="INCOMPLETE",
        support_status="INCOMPLETE", toolpath_status="INCOMPLETE",
        declared_support_exceptions=list(contract["support_exceptions"]))

    governing = [mesh_domain, orientation_domain, structural_domain,
                 process_domain]
    if any(row["status"] == "FAIL" for row in governing):
        overall = "FAIL"
    elif any(row["status"] == "INCOMPLETE" for row in governing):
        overall = "INCOMPLETE"
    else:
        overall = "CAD_READY"
    compiler = _compiler_binding(compiler_path)
    helper = _helper_binding(helper_path)
    mesh_inputs = [{"part": part, "sha256": _sha(mesh_payloads[part]),
                    "size": len(mesh_payloads[part])}
                   for part in expected_parts]
    findings = sorted({finding for domain in governing
                       for finding in domain["findings"]})
    return {
        "schema": 1, "kind": RECEIPT_KIND, "name": contract["name"],
        "status": overall, "maximum_claim": "CAD_READY",
        "physical_evidence_consumed": False,
        "inputs": {
            "compiler": compiler,
            "enclosure_common": helper,
            "contract": {"sha256": _sha(contract_payload),
                         "size": len(contract_payload)},
            "cad_design": {"design_fingerprint": contract["fingerprint"]},
            "generation": {"sha256": _sha(generation_payload),
                           "size": len(generation_payload)},
            "meshes": mesh_inputs,
        },
        "denominators": {
            "printable_parts": len(expected_parts),
            "process_profiles": profile_count,
            "load_cases": len(contract["load_cases"]),
            "critical_attachments": len(contract["attachments"]),
            "structural_probe_assertions": probe_denominator,
        },
        "domains": {
            "mesh_integrity": mesh_domain,
            "orientation_and_process_contract": orientation_domain,
            "structural_load_path_screen": structural_domain,
            "slicer_toolpath_evidence": process_domain,
            "physical_evidence_boundary": {
                "status": "INCOMPLETE", "governs_cad_readiness": False,
                "consumed": False,
                "finding": (
                    "physical print, fit, fastener, load, and thermal evidence "
                    "is outside this CAD audit"),
            },
        },
        "findings": findings,
    }


def audit_paths_with_contract(
        contract_path: Path, config_path: Path,
        generation_path: Path, mesh_paths: Mapping[str, Path], *,
        root: Path, compiler_path: Path | None = None,
        helper_path: Path | None = None,
        ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Audit one stable input census and return its normalized contract too.

    Schema-v2 consumes attachment scopes and flexure test cross-links. Returning
    the contract parsed from the same captured bytes prevents it from reopening
    a transiently different contract after receipt computation.
    """
    contract_payload = stable_bytes(contract_path, "FDM audit contract")
    config_payload = stable_bytes(config_path, "schema-v1 CAD design")
    try:
        config_relative_path = config_path.resolve(strict=True).relative_to(
            root.resolve(strict=True)).as_posix()
    except ValueError as exc:
        raise AuditError(
            "schema-v1 CAD design must be inside the declared subject root") from exc
    try:
        config_value = yaml.load(config_payload.decode("utf-8"),
                                 Loader=_StrictLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise AuditError(f"invalid schema-v1 CAD design YAML: {exc}") from exc
    if not isinstance(config_value, dict):
        raise AuditError("schema-v1 CAD design must be an object")
    helper_path = helper_path or Path(__file__).resolve().with_name(
        "enclosure_common.py")
    expected_helper = _helper_binding(helper_path)
    helper = _load_helper(helper_path, expected_helper)
    try:
        # Validate the exact object parsed from the one stable config read;
        # never hash one version and schema-parse a reopened path.
        config_value = helper.validate_config(config_value)
    except helper.EnclosureError as exc:
        raise AuditError(f"invalid schema-v1 CAD design: {exc}") from exc
    validate_config_bindings(config_value, root)
    generation_payload = stable_bytes(generation_path, "generation receipt")
    try:
        contract_value = yaml.load(contract_payload.decode("utf-8"),
                                   Loader=_StrictLoader)
        generation_value = json.loads(
            generation_payload, object_pairs_hook=_json_pairs)
    except (UnicodeDecodeError, yaml.YAMLError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot parse audit input: {exc}") from exc
    if not isinstance(contract_value, Mapping) or \
            not isinstance(generation_value, Mapping):
        raise AuditError("contract/generation must be objects")
    normalized_contract = validate_contract(contract_value, config_value)
    payloads = {part: stable_bytes(path, f"printable mesh {part}")
                for part, path in mesh_paths.items()}
    receipt = audit(contract_value, config_value, generation_value, payloads,
                    contract_payload=contract_payload,
                    config_payload=config_payload,
                    config_relative_path=config_relative_path,
                    generation_payload=generation_payload,
                    compiler_path=compiler_path, helper_path=helper_path)
    final_inputs = {
        "contract": (contract_path, contract_payload),
        "config": (config_path, config_payload),
        "generation": (generation_path, generation_payload),
        **{f"mesh {part}": (mesh_paths[part], payload)
           for part, payload in payloads.items()},
    }
    for where, (path, expected) in final_inputs.items():
        if stable_bytes(path, f"final {where}") != expected:
            raise AuditError(f"{where} changed during audit")
    validate_config_bindings(config_value, root)
    return receipt, normalized_contract


def audit_paths(contract_path: Path, config_path: Path,
                generation_path: Path, mesh_paths: Mapping[str, Path], *,
                root: Path,
                compiler_path: Path | None = None,
                helper_path: Path | None = None) -> dict[str, Any]:
    """Backward-compatible receipt-only adapter for direct callers."""
    receipt, _ = audit_paths_with_contract(
        contract_path, config_path, generation_path, mesh_paths, root=root,
        compiler_path=compiler_path, helper_path=helper_path)
    return receipt


def load_exact_module(binding: Mapping[str, Any], *, release_root: Path | None = None,
                      release_binding: Mapping[str, Any] | None = None):
    """Select exact live or release-local compiler bytes for v2 replay."""
    expected = _exact(binding, {"path", "sha256", "size"}, "audit compiler binding")
    if expected["path"] != COMPILER_SOURCE_PATH:
        raise AuditError("audit receipt compiler has noncanonical source path")
    if release_root is None:
        module_path = Path(__file__)
        if _compiler_binding(module_path) != dict(expected):
            raise AuditError("installed FDM audit compiler differs from receipt")
        return sys.modules[__name__]
    if release_binding is None:
        raise AuditError("release FDM audit compiler binding is absent")
    release_record = _exact(release_binding, {"path", "sha256", "size"},
                            "release audit compiler binding")
    if release_record["path"] != COMPILER_RELEASE_PATH or \
            (release_record["sha256"], release_record["size"]) != \
            (expected["sha256"], expected["size"]):
        raise AuditError("release FDM audit compiler differs from receipt")
    module_path = _ordinary(release_root / release_record["path"],
                            "release FDM audit compiler")
    if _compiler_binding(module_path) != dict(expected):
        raise AuditError("release FDM audit compiler bytes differ from receipt")
    payload = stable_bytes(module_path, "release FDM audit compiler")
    if (_sha(payload), len(payload)) != (expected["sha256"], expected["size"]):
        raise AuditError("release FDM audit compiler changed before execution")
    module = types.ModuleType("pcb_enclosure_release_fdm_structural_audit")
    module.__file__ = str(module_path)
    module.__package__ = None
    try:
        code = compile(payload, str(module_path), "exec", dont_inherit=True)
        exec(code, module.__dict__)
    except Exception as exc:  # pragma: no cover - trusted runtime boundary
        raise AuditError(f"cannot execute release FDM audit compiler: {exc}") from exc
    module._compiler_binding = lambda module_path=None: dict(expected)
    return module


def _parse_mesh(values: Sequence[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for raw in values:
        if "=" not in raw:
            raise AuditError(f"mesh {raw!r}: expected PART=PATH")
        part, path = raw.split("=", 1)
        if not PART_RE.fullmatch(part) or part in result or not path:
            raise AuditError(f"mesh {raw!r}: invalid or duplicate part")
        result[part] = Path(path)
    if not result:
        raise AuditError("mesh input denominator is zero")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--generation", type=Path, required=True)
    parser.add_argument("--mesh", action="append", default=[], metavar="PART=PATH")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        meshes = _parse_mesh(args.mesh)
        receipt = audit_paths(
            args.contract, args.config, args.generation, meshes, root=args.root)
        config = load_yaml(args.config)
        helper_path = Path(__file__).resolve().with_name("enclosure_common.py")
        inputs = [Path(__file__), helper_path, args.contract, args.config, args.generation,
                  *meshes.values(), *validate_config_bindings(config, args.root)]
        write_json(
            args.output, receipt, inputs=inputs,
            regrade=lambda: audit_paths(
                args.contract, args.config, args.generation, meshes,
                root=args.root, helper_path=helper_path))
    except (AuditError, OSError) as exc:
        print(f"FDM STRUCTURAL AUDIT ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"FDM STRUCTURAL AUDIT {receipt['status']}: {args.output}")
    return {"FAIL": 1, "INCOMPLETE": 2, "CAD_READY": 0}[receipt["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
