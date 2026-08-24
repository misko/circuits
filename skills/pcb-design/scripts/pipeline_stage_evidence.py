#!/usr/bin/env python3
"""Create typed diagnostic StageResults for domain measurements.

Domain gates own engineering measurements.  This module owns only the common
pipeline boundary for typed results.  Direct promotion of an accepted bundle
and a separate StageResult path is deliberately disabled: two independent
filesystem targets cannot be committed atomically. The migration writes one
canonical fail-closed ``INCOMPLETE`` boundary hold and leaves every accepted
bundle untouched. It intentionally invalidates a former unsafe PASS
StageResult at that path; this is an authority rollback, not shadow isolation.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from pipeline_artifacts import PublishedBundle
from pipeline_contract import StageResult
from pipeline_identity import SubjectIdentity


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z")


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


def write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def require_distinct_output_paths(paths: Mapping[str, Path]) -> None:
    """Reject output aliases before any writer can replace another result."""

    if not paths:
        raise ValueError("at least one output path is required")
    named_resolved: dict[str, Path] = {}
    resolved: dict[Path, list[str]] = {}
    for name, path in paths.items():
        if not isinstance(name, str) or not name:
            raise ValueError("output path names must be non-empty strings")
        candidate = Path(path).resolve(strict=False)
        named_resolved[name] = candidate
        resolved.setdefault(candidate, []).append(name)
    collisions = {
        str(path): sorted(names) for path, names in resolved.items()
        if len(names) > 1
    }
    if collisions:
        raise ValueError(f"output paths must be distinct: {collisions}")
    items = list(named_resolved.items())
    for index, (left_name, left_path) in enumerate(items):
        for right_name, right_path in items[index + 1:]:
            if not left_path.exists() or not right_path.exists():
                continue
            try:
                aliases = os.path.samefile(left_path, right_path)
            except OSError as exc:
                raise ValueError(
                    f"output identity could not be verified for {left_name}/"
                    f"{right_name}: {exc}") from exc
            if aliases:
                raise ValueError(
                    f"output paths alias one inode: {left_name}, {right_name}")


def require_safe_output_layout(
    paths: Mapping[str, Path], *, directory_outputs: Sequence[str] = (),
    protected_paths: Mapping[str, Path] | None = None,
) -> None:
    """Reject aliases and directory outputs that can consume other evidence."""

    require_distinct_output_paths(paths)
    resolved = {
        name: Path(path).resolve(strict=False) for name, path in paths.items()
    }
    unknown_directories = set(directory_outputs) - set(resolved)
    if unknown_directories:
        raise ValueError(
            f"unknown directory output names: {sorted(unknown_directories)}")
    protected = {
        name: Path(path).resolve(strict=False)
        for name, path in (protected_paths or {}).items()
    }
    for output_name, output_path in resolved.items():
        for protected_name, protected_path in protected.items():
            if output_path == protected_path:
                raise ValueError(
                    f"{output_name} aliases protected {protected_name}: "
                    f"{output_path}")
            if output_path.exists() and protected_path.exists():
                try:
                    aliases = os.path.samefile(output_path, protected_path)
                except OSError as exc:
                    raise ValueError(
                        f"output/protected identity could not be verified for "
                        f"{output_name}/{protected_name}: {exc}") from exc
                if aliases:
                    raise ValueError(
                        f"{output_name} aliases protected {protected_name} "
                        "through a hardlink")
    for directory_name in directory_outputs:
        directory = resolved[directory_name]
        for name, path in {**resolved, **protected}.items():
            if name == directory_name:
                continue
            if path == directory or path.is_relative_to(directory):
                raise ValueError(
                    f"{directory_name} may not contain {name}: {directory}")


@dataclass(frozen=True)
class PublishedStageEvidence:
    bundle: PublishedBundle
    result: StageResult


def publish_stage_evidence(
    *,
    stage_id: str,
    output_symbol: str,
    producer: str,
    producer_version: str,
    subject: SubjectIdentity,
    inputs: Mapping[str, Path],
    measurement_path: Path,
    measurement_name: str,
    accepted_dir: Path,
    stage_result_path: Path,
    status: str,
    graded: int,
    total: int,
    findings: Sequence[Any] = (),
    run_id: str | None = None,
    started_at: str | None = None,
    started_clock: float | None = None,
) -> PublishedStageEvidence:
    """Refuse unsafe two-target promotion before touching the filesystem.

    The historical implementation replaced ``accepted_dir`` and only then
    wrote ``stage_result_path``.  A failure during the second write could leave
    a newly accepted bundle with no matching StageResult.  Promotion must be
    redesigned around one content-addressed transaction and a pointer-last
    commit before this API can become authoritative.
    """

    del (stage_id, output_symbol, producer, producer_version, subject, inputs,
         measurement_path, measurement_name, accepted_dir, stage_result_path,
         status, graded, total, findings, run_id, started_at, started_clock)
    raise RuntimeError(
        "accepted stage-evidence promotion is disabled until bundle and "
        "StageResult share one atomic pointer-last transaction")


def write_shadow_stage_result(
    *,
    stage_id: str,
    subject: SubjectIdentity,
    stage_result_path: Path,
    total: int,
    finding_code: str,
    finding_detail: str,
) -> StageResult:
    """Write the canonical fail-closed hold without touching accepted bundles."""

    now = utc_now()
    result = StageResult(
        stage_id=stage_id,
        run_id=new_run_id(),
        subject=subject,
        applicability="APPLIES",
        applicability_reason=None,
        status="INCOMPLETE",
        started_at=now,
        finished_at=now,
        elapsed_s=0.0,
        graded=0,
        total=total,
        outputs=[],
        findings=[{"code": finding_code, "detail": finding_detail}],
        resume=None,
    )
    write_json_atomic(stage_result_path, result.to_mapping())
    return result


__all__ = [
    "PublishedStageEvidence",
    "new_run_id",
    "publish_stage_evidence",
    "require_distinct_output_paths",
    "require_safe_output_layout",
    "utc_now",
    "write_json_atomic",
    "write_shadow_stage_result",
]
