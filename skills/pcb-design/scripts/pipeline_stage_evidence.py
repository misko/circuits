#!/usr/bin/env python3
"""Publish one domain measurement as an atomic bundle and StageResult.

Domain gates own engineering measurements.  This module owns only the common
pipeline boundary: exact input identity, atomic publication, and the outer
typed result.  Existing gates can adopt it behind optional CLI arguments while
their legacy receipts remain authoritative during shadow migration.
"""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from pipeline_artifacts import ArtifactBundleTransaction, PublishedBundle
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
    """Publish passing evidence and its exact-subject typed result.

    Failed/incomplete domain evidence must remain diagnostic output owned by
    the caller; it is intentionally never promoted as an accepted bundle.
    """

    if status != "PASS":
        raise ValueError("accepted stage evidence requires status PASS")
    if graded != total or total <= 0:
        raise ValueError("accepted stage evidence requires graded == total > 0")
    measurement_path = measurement_path.resolve(strict=True)
    run_id = run_id or new_run_id()
    started_at = started_at or utc_now()
    started_clock = time.monotonic() if started_clock is None else started_clock
    transaction = ArtifactBundleTransaction(
        accepted_dir,
        producer=producer,
        producer_version=producer_version,
        subject=subject.to_mapping(),
        inputs=inputs,
        outputs={measurement_name: None},
        run_id=run_id,
        retain_failed=True,
    )

    def produce(staging: Path) -> None:
        target = staging / measurement_name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(measurement_path, target)

    published = transaction.publish(produce)
    result = StageResult(
        stage_id=stage_id,
        run_id=run_id,
        subject=subject,
        applicability="APPLIES",
        applicability_reason=None,
        status="PASS",
        started_at=started_at,
        finished_at=utc_now(),
        elapsed_s=max(0.0, time.monotonic() - started_clock),
        graded=graded,
        total=total,
        outputs=[output_symbol],
        findings=list(findings),
        resume=None,
    )
    write_json_atomic(stage_result_path, result.to_mapping())
    return PublishedStageEvidence(bundle=published, result=result)


__all__ = [
    "PublishedStageEvidence",
    "new_run_id",
    "publish_stage_evidence",
    "utc_now",
    "write_json_atomic",
]
