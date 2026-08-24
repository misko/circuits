#!/usr/bin/env python3
"""T1: common domain-measurement to pipeline-evidence boundary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills" / "pcb-design" / "scripts"))

from pipeline_identity import SubjectIdentity  # noqa: E402
from pipeline_stage_evidence import (  # noqa: E402
    publish_stage_evidence, write_shadow_stage_result,
)


def fixture():
    root = tmpdir("stage_evidence_")
    source = root / "source.yaml"
    source.write_text("parts: [U1]\n", encoding="utf-8")
    measurement = root / "measurement.json"
    measurement.write_text('{"coverage":{"graded":3,"total":3}}\n')
    return root, source, measurement


@test("unsafe two-target promotion is disabled before filesystem mutation",
      kind="known_bad")
def t_publish_is_disabled():
    root, source, measurement = fixture()
    before = {source: source.read_bytes(), measurement: measurement.read_bytes()}
    try:
        publish_stage_evidence(
            stage_id="S-PART-FREEZE", output_symbol="part_freeze_report",
            producer="fixture", producer_version="v1",
            subject=SubjectIdentity("1" * 64, "2" * 64),
            inputs={"source.yaml": source}, measurement_path=measurement,
            measurement_name="part_freeze.json",
            # This historically could replace the whole fixture root.
            accepted_dir=root, stage_result_path=root / "stage.json",
            status="PASS", graded=3, total=3)
    except RuntimeError as exc:
        check("disabled" in str(exc), "refusal did not name disabled promotion")
    else:
        raise AssertionError("unsafe two-target promotion was accepted")
    for path, content in before.items():
        eq(path.read_bytes(), content, f"{path.name} changed")
    check(not (root / "stage.json").exists(), "stage result was partially written")


@test("boundary hold replaces unsafe PASS but no accepted bundle")
def t_shadow_result():
    root, _source, _measurement = fixture()
    stage_path = root / "stage.json"
    stage_path.write_text('{"status":"PASS","outputs":["unsafe"]}\n')
    result = write_shadow_stage_result(
        stage_id="E-CLOSURE",
        subject=SubjectIdentity("1" * 64, "2" * 64),
        stage_result_path=stage_path, total=9,
        finding_code="PROMOTION-DISABLED",
        finding_detail="pending independent regrade")
    eq(result.status, "INCOMPLETE", "boundary hold status")
    payload = json.loads(stage_path.read_text())
    eq(payload["status"], "INCOMPLETE", "unsafe PASS survived rollback")
    eq(payload["outputs"], [], "boundary hold output symbols")
    check(not (root / "accepted").exists(), "hold created accepted bundle")


@test("failed or vacuous evidence cannot become an accepted bundle",
      kind="known_bad")
def t_reject_nonpassing():
    root, source, measurement = fixture()
    for status, graded, total in (("FAIL", 2, 3), ("PASS", 0, 0)):
        try:
            publish_stage_evidence(
                stage_id="E-CLOSURE", output_symbol="electrical_closure_report",
                producer="fixture", producer_version="v1",
                subject=SubjectIdentity("1" * 64, "2" * 64),
                inputs={"source.yaml": source}, measurement_path=measurement,
                measurement_name="closure.json",
                accepted_dir=root / f"accepted-{status}-{total}",
                stage_result_path=root / f"stage-{status}-{total}.json",
                status=status, graded=graded, total=total,
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("inadmissible evidence was published")
    check(not list(root.glob("accepted-*")), "failed bundle directory exists")


if __name__ == "__main__":
    raise SystemExit(main())
