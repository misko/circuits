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
from pipeline_stage_evidence import publish_stage_evidence  # noqa: E402


def fixture():
    root = tmpdir("stage_evidence_")
    source = root / "source.yaml"
    source.write_text("parts: [U1]\n", encoding="utf-8")
    measurement = root / "measurement.json"
    measurement.write_text('{"coverage":{"graded":3,"total":3}}\n')
    return root, source, measurement


@test("passing domain evidence publishes one atomic bundle and typed result")
def t_publish():
    root, source, measurement = fixture()
    published = publish_stage_evidence(
        stage_id="S-PART-FREEZE",
        output_symbol="part_freeze_report",
        producer="fixture",
        producer_version="v1",
        subject=SubjectIdentity("1" * 64, "2" * 64),
        inputs={"source.yaml": source},
        measurement_path=measurement,
        measurement_name="part_freeze.json",
        accepted_dir=root / "accepted",
        stage_result_path=root / "stage.json",
        status="PASS",
        graded=3,
        total=3,
    )
    eq(published.result.outputs, ("part_freeze_report",), "output symbol")
    eq(json.loads((root / "stage.json").read_text())["status"], "PASS",
       "durable stage status")
    eq(json.loads((root / "accepted/bundle.json").read_text())["status"],
       "PASS", "bundle status")
    check((root / "accepted/part_freeze.json").is_file(),
          "measurement was not promoted")


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
        except ValueError:
            pass
        else:
            raise AssertionError("inadmissible evidence was published")
    check(not list(root.glob("accepted-*")), "failed bundle directory exists")


if __name__ == "__main__":
    raise SystemExit(main())
