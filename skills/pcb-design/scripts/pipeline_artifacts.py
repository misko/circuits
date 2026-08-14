#!/usr/bin/env python3
"""Transactional artifact bundles for declarative PCB pipeline stages.

The transaction deliberately knows nothing about KiCad, JLCPCB, or any
project.  A producer receives a fresh sibling directory, and that directory
only becomes the accepted bundle after every declared output and relationship
has been checked.  The previous accepted directory is never used as producer
input, so an exit-zero producer cannot accidentally reuse stale evidence.
"""
from __future__ import annotations

import csv
import ctypes
import errno
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Callable, Mapping


_HASH_RE = re.compile(r"[0-9a-f]{64}")
_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_RENAME_EXCHANGE = 2
_AT_FDCWD = -100

Parser = Callable[[Path], Any]
Producer = Callable[[Path], Any]
FinalStateSerializer = Callable[[Path, Any], None]
ReopenValidator = Callable[[Path, Mapping[str, Any]], Any]


class ArtifactError(RuntimeError):
    """Base class for fail-closed artifact transaction failures."""


class ArtifactDeclarationError(ArtifactError):
    """The transaction declaration cannot safely describe a bundle."""


class ArtifactProducerError(ArtifactError):
    """The producer reported failure."""


class ArtifactValidationError(ArtifactError):
    """Produced bytes did not satisfy the bundle postconditions."""


class ArtifactPromotionError(ArtifactError):
    """The validated staging directory could not be atomically published."""


@dataclass(frozen=True)
class OutputSpec:
    """A required non-empty output and its durable parser.

    ``parser`` receives a path and must either return a parsed representation
    or raise.  When omitted, JSON, CSV, ZIP and UTF-8 text have strict built-in
    parsers; other suffixes are reopened as bytes.
    """

    parser: Parser | None = None


@dataclass(frozen=True)
class PublishedBundle:
    """The accepted result of a successful transaction."""

    path: Path
    manifest: Mapping[str, Any]
    replaced_existing: bool


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z")


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def _safe_manifest_path(value: str, what: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ArtifactDeclarationError(f"{what} must be a non-empty POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ArtifactDeclarationError(
            f"{what} must be relative and may not contain '.' or '..': {value!r}")
    normalized = path.as_posix()
    if normalized == "bundle.json":
        raise ArtifactDeclarationError("bundle.json is reserved for the manifest")
    return normalized


def _regular_file(path: Path, what: str) -> os.stat_result:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise ArtifactValidationError(f"missing {what}: {path}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ArtifactValidationError(f"{what} is not a regular file: {path}")
    return info


def _file_record(path: Path, what: str, *, non_empty: bool) -> dict[str, Any]:
    info = _regular_file(path, what)
    if non_empty and info.st_size == 0:
        raise ArtifactValidationError(f"{what} is empty: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest(), "size": info.st_size}


def _parse_json(path: Path) -> Any:
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return json.load(stream, object_pairs_hook=no_duplicates)


def _parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        if fields is None or not fields or any(not field for field in fields):
            raise ValueError("CSV has no complete header")
        if len(fields) != len(set(fields)):
            raise ValueError("CSV contains duplicate header fields")
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError("CSV row has more columns than its header")
        return rows


def _parse_zip(path: Path) -> tuple[str, ...]:
    with zipfile.ZipFile(path) as archive:
        names = tuple(archive.namelist())
        if not names:
            raise ValueError("ZIP archive has no entries")
        corrupt = archive.testzip()
        if corrupt is not None:
            raise ValueError(f"ZIP archive contains corrupt entry {corrupt!r}")
        return names


def _parse_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _parse_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _default_parser(path: Path) -> Parser:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _parse_json
    if suffix == ".csv":
        return _parse_csv
    if suffix == ".zip":
        return _parse_zip
    if suffix in {".txt", ".md", ".log", ".tsv", ".xml", ".html"}:
        return _parse_text
    return _parse_bytes


def _fsync_file(path: Path) -> None:
    with path.open("rb") as stream:
        os.fsync(stream.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _rename_exchange(source: Path, target: Path) -> None:
    """Atomically exchange two sibling directories or fail closed.

    A backup-then-rename fallback would briefly hide the accepted bundle and
    could not satisfy the frozen contract.  Filesystems without renameat2
    exchange support therefore get an explicit failure instead.
    """

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOSYS, "renameat2 is unavailable")
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(
        _AT_FDCWD,
        os.fsencode(source),
        _AT_FDCWD,
        os.fsencode(target),
        _RENAME_EXCHANGE,
    )
    if result != 0:
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(target))


def _discard_staging(path: Path, parent: Path, prefix: str) -> None:
    """Remove only the exact temporary directory created by this module."""

    try:
        safe = (path.parent == parent and path.name.startswith(prefix)
                and path.is_dir() and not path.is_symlink())
        if safe:
            shutil.rmtree(path)
    except OSError:
        # Cleanup failure must not mask the validation or producer error.  The
        # unique hidden directory remains visibly unaccepted and recoverable.
        pass


def _publish_staging(staging: Path, target: Path) -> bool:
    """Publish ``staging`` atomically; return whether ``target`` was replaced."""

    existed = target.exists()
    if target.is_symlink() or (existed and not target.is_dir()):
        raise ArtifactPromotionError(
            f"accepted bundle must be a directory, not {target}")
    try:
        if existed:
            _rename_exchange(staging, target)
        else:
            os.replace(staging, target)
    except OSError as exc:
        raise ArtifactPromotionError(
            f"atomic promotion failed for {target}: {exc}") from exc

    # Promotion is already complete.  Durability and old-bundle cleanup are
    # best effort from here so a cleanup failure cannot turn a successful
    # atomic exchange into a reported failure with ambiguous ownership.
    try:
        _fsync_directory(target.parent)
    except OSError:
        pass
    if existed:
        _discard_staging(staging, target.parent, f".{target.name}.txn-")
        try:
            _fsync_directory(target.parent)
        except OSError:
            pass
    return existed


class ArtifactBundleTransaction:
    """Generate, validate and atomically publish one artifact bundle.

    Inputs are a mapping from stable manifest paths to existing source files.
    Outputs are a mapping from relative paths inside the accepted bundle to an
    :class:`OutputSpec` (or ``None`` for default parsing).
    """

    def __init__(
        self,
        accepted_dir: Path | str,
        *,
        producer: str,
        producer_version: str,
        subject: Mapping[str, str],
        inputs: Mapping[str, Path | str],
        outputs: Mapping[str, OutputSpec | None],
        run_id: str | None = None,
    ) -> None:
        raw_target = Path(accepted_dir).expanduser()
        if raw_target.name in {"", ".", ".."}:
            raise ArtifactDeclarationError("accepted bundle path is too broad")
        parent = raw_target.parent.resolve(strict=True)
        if not parent.is_dir():
            raise ArtifactDeclarationError(f"bundle parent is not a directory: {parent}")
        self.accepted_dir = parent / raw_target.name
        if self.accepted_dir.is_symlink():
            raise ArtifactDeclarationError("accepted bundle may not be a symlink")

        if not isinstance(producer, str) or not producer.strip():
            raise ArtifactDeclarationError("producer must be non-empty")
        if not isinstance(producer_version, str) or not producer_version.strip():
            raise ArtifactDeclarationError("producer_version must be non-empty")
        self.producer = producer.strip()
        self.producer_version = producer_version.strip()

        expected_subject = {"semantic_sha256", "raw_sha256"}
        if set(subject) != expected_subject:
            raise ArtifactDeclarationError(
                "subject must contain exactly semantic_sha256 and raw_sha256")
        self.subject = {}
        for field in sorted(expected_subject):
            value = subject[field]
            if not isinstance(value, str) or not _HASH_RE.fullmatch(value.lower()):
                raise ArtifactDeclarationError(f"subject {field} is not a SHA-256")
            self.subject[field] = value.lower()

        self.run_id = run_id or _new_run_id()
        if not _RUN_ID_RE.fullmatch(self.run_id):
            raise ArtifactDeclarationError(f"invalid run_id: {self.run_id!r}")

        if not inputs:
            raise ArtifactDeclarationError("at least one declared input is required")
        self.inputs: dict[str, Path] = {}
        for name, path in inputs.items():
            clean = _safe_manifest_path(name, "input name")
            if clean in self.inputs:
                raise ArtifactDeclarationError(
                    f"duplicate normalized input name: {clean!r}")
            self.inputs[clean] = Path(path).expanduser().resolve(strict=True)

        if not outputs:
            raise ArtifactDeclarationError("at least one declared output is required")
        self.outputs: dict[str, OutputSpec] = {}
        for name, spec in outputs.items():
            clean = _safe_manifest_path(name, "output name")
            if clean in self.outputs:
                raise ArtifactDeclarationError(
                    f"duplicate normalized output name: {clean!r}")
            if spec is not None and not isinstance(spec, OutputSpec):
                raise ArtifactDeclarationError(
                    f"output {clean!r} must use OutputSpec or None")
            self.outputs[clean] = spec or OutputSpec()

    def _output_path(self, staging: Path, name: str) -> Path:
        path = staging.joinpath(*PurePosixPath(name).parts)
        # The lexical declaration is already constrained; this catches a
        # parent directory replaced with a symlink by an untrusted producer.
        try:
            parent = path.parent.resolve(strict=False)
            parent.relative_to(staging.resolve())
        except ValueError:
            raise ArtifactValidationError(f"output escapes staging bundle: {name}")
        if parent != path.parent:
            raise ArtifactValidationError(
                f"output parent is not the declared directory: {name}")
        return path

    def _validate_output_set(self, staging: Path, *, manifest_ok: bool = False) -> None:
        expected = set(self.outputs)
        if manifest_ok:
            expected.add("bundle.json")
        actual = set()
        directories = set()
        for path in staging.rglob("*"):
            relative = path.relative_to(staging).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ArtifactValidationError(
                    f"bundle contains symlink instead of declared output: {relative}")
            if stat.S_ISREG(info.st_mode):
                actual.add(relative)
            elif stat.S_ISDIR(info.st_mode):
                directories.add(relative)
            else:
                raise ArtifactValidationError(
                    f"bundle contains unsupported file type: {relative}")
        expected_directories = {
            PurePosixPath(name).parent.as_posix()
            for name in expected
            if PurePosixPath(name).parent.as_posix() != "."
        }
        expected_directories |= {
            parent.as_posix()
            for name in expected
            for parent in PurePosixPath(name).parents
            if parent.as_posix() not in (".", "")
        }
        undeclared = sorted(actual - expected)
        undeclared_directories = sorted(directories - expected_directories)
        missing = sorted(set(self.outputs) - actual)
        if undeclared:
            raise ArtifactValidationError(
                f"undeclared output(s): {', '.join(undeclared)}")
        if undeclared_directories:
            raise ArtifactValidationError(
                "undeclared output directories: "
                + ", ".join(undeclared_directories))
        if missing:
            raise ArtifactValidationError(f"missing output(s): {', '.join(missing)}")

    def _records(self, files: Mapping[str, Path], what: str,
                 *, non_empty: bool) -> dict[str, dict[str, Any]]:
        return {
            name: _file_record(path, f"{what} {name!r}", non_empty=non_empty)
            for name, path in sorted(files.items())
        }

    def _parse_outputs(self, paths: Mapping[str, Path]) -> dict[str, Any]:
        parsed = {}
        for name, path in sorted(paths.items()):
            parser = self.outputs[name].parser or _default_parser(path)
            try:
                parsed[name] = parser(path)
            except Exception as exc:
                raise ArtifactValidationError(
                    f"output {name!r} is unparsable: {exc}") from exc
        return parsed

    def publish(
        self,
        produce: Producer,
        *,
        final_state_serializer: FinalStateSerializer | None = None,
        reopen_validator: ReopenValidator | None = None,
    ) -> PublishedBundle:
        """Run hooks and publish only a complete, self-consistent bundle.

        ``produce`` receives the fresh staging directory.  It may return
        ``None``, integer zero, or an object whose ``returncode`` is zero.
        ``final_state_serializer`` runs after producer adjudication and before
        validation.  ``reopen_validator`` receives a second, durable parse of
        every output and may cross-check fields by raising or returning
        ``False``.
        """

        if not callable(produce):
            raise ArtifactDeclarationError("produce must be callable")
        if final_state_serializer is not None and not callable(final_state_serializer):
            raise ArtifactDeclarationError("final_state_serializer must be callable")
        if reopen_validator is not None and not callable(reopen_validator):
            raise ArtifactDeclarationError("reopen_validator must be callable")

        input_paths = dict(self.inputs)
        initial_inputs = self._records(input_paths, "input", non_empty=False)
        started_at = _utc_now()
        prefix = f".{self.accepted_dir.name}.txn-"
        staging = Path(tempfile.mkdtemp(prefix=prefix, dir=self.accepted_dir.parent))
        try:
            # Fresh staging is the freshness boundary: no declared output may
            # exist before this invocation of the producer.
            for name in self.outputs:
                if self._output_path(staging, name).exists():
                    raise ArtifactValidationError(
                        f"old output existed before producer start: {name}")

            try:
                producer_value = produce(staging)
            except Exception as exc:
                raise ArtifactProducerError(f"producer raised: {exc}") from exc
            if isinstance(producer_value, bool):
                raise ArtifactProducerError(
                    "producer returned a boolean; use integer zero, non-zero "
                    "status, None, or an explicit state object")
            returncode = (producer_value if isinstance(producer_value, int)
                          and not isinstance(producer_value, bool)
                          else getattr(producer_value, "returncode", None))
            if returncode not in (None, 0):
                raise ArtifactProducerError(
                    f"producer returned non-zero status {returncode}")

            if final_state_serializer is not None:
                try:
                    final_state_serializer(staging, producer_value)
                except Exception as exc:
                    raise ArtifactValidationError(
                        f"final-state serialization failed: {exc}") from exc

            self._validate_output_set(staging)
            output_paths = {
                name: self._output_path(staging, name) for name in self.outputs
            }
            first_outputs = self._records(
                output_paths, "output", non_empty=True)
            self._parse_outputs(output_paths)

            for path in output_paths.values():
                _fsync_file(path)
            _fsync_directory(staging)

            # Reopen rather than trusting producer memory or the first parser
            # objects.  This is the representation supplied to cross-checks.
            reopened = self._parse_outputs(output_paths)
            if reopen_validator is not None:
                try:
                    verdict = reopen_validator(
                        staging, MappingProxyType(reopened))
                except ArtifactValidationError:
                    raise
                except Exception as exc:
                    raise ArtifactValidationError(
                        f"reopen validation failed: {exc}") from exc
                if verdict is False:
                    raise ArtifactValidationError(
                        "reopen validation reported disagreement")

            # Hooks are validators, not producers.  No bytes or declarations
            # may move after the first durable parse.
            self._validate_output_set(staging)
            final_outputs = self._records(
                output_paths, "output", non_empty=True)
            if final_outputs != first_outputs:
                raise ArtifactValidationError(
                    "output bytes changed during reopen validation")
            final_inputs = self._records(input_paths, "input", non_empty=False)
            if final_inputs != initial_inputs:
                raise ArtifactValidationError(
                    "declared input changed during artifact transaction")

            finished_at = _utc_now()
            manifest = {
                "schema": 1,
                "run_id": self.run_id,
                "producer": self.producer,
                "producer_version": self.producer_version,
                "subject": dict(self.subject),
                "started_at": started_at,
                "finished_at": finished_at,
                "status": "PASS",
                "inputs": final_inputs,
                "outputs": final_outputs,
            }
            manifest_path = staging / "bundle.json"
            with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(manifest, stream, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            _fsync_directory(staging)

            # Reading is permitted after the manifest is written last.  A
            # partial or mutated manifest still prevents publication.
            durable_manifest = _parse_json(manifest_path)
            if durable_manifest != manifest:
                raise ArtifactValidationError("durable bundle manifest disagrees")
            self._validate_output_set(staging, manifest_ok=True)
            if self._records(output_paths, "output", non_empty=True) != final_outputs:
                raise ArtifactValidationError(
                    "output bytes changed after bundle manifest was written")
            if self._records(input_paths, "input", non_empty=False) != final_inputs:
                raise ArtifactValidationError(
                    "input bytes changed after bundle manifest was written")

            replaced = _publish_staging(staging, self.accepted_dir)
            return PublishedBundle(
                path=self.accepted_dir,
                manifest=MappingProxyType(manifest),
                replaced_existing=replaced,
            )
        except BaseException:
            _discard_staging(staging, self.accepted_dir.parent, prefix)
            raise


__all__ = [
    "ArtifactBundleTransaction",
    "ArtifactDeclarationError",
    "ArtifactError",
    "ArtifactProducerError",
    "ArtifactPromotionError",
    "ArtifactValidationError",
    "OutputSpec",
    "PublishedBundle",
]
