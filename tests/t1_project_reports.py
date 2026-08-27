#!/usr/bin/env python3
"""T1: governed Markdown project reports stay readable, linked, and honest."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)


AUDIT = ROOT / "skills/pcb-design/scripts/project_report_audit.py"
REAL_REPORT = (
    ROOT / "projects/pluto-rx2-8way-v5/01_docs/reports/"
    "2026-08-27-rf-isolation-and-v6-mitigation.md"
)
TEMPLATE_CONTRACT = (
    ROOT / "skills/pcb-design/templates/contracts/01_docs/reports/contracts.md"
)


def report_text(*, report_id: str = "2026-08-27-test-study", evidence: str = "INCOMPLETE") -> str:
    claims = "**PROPOSED:** candidate change. **OWED:** test it."
    if evidence == "MEASURED":
        claims = "All material conclusions are **MEASURED:** retained evidence."
    return f"""---
schema: 1
kind: pcb-human-report
report_id: {report_id}
title: Test study
subtitle: A hermetic report fixture
project: test-board
date: 2026-08-27
status: REVIEWED
evidence_status: {evidence}
---

## Executive conclusion

**INFERRED:** concise conclusion. {claims}

## Question and scope

The exact question.

## Evidence boundary

**DATASHEET:** [local evidence](../../evidence.txt).

## Findings

**CITED:** a primary source. **MEASURED:** a checked artifact.

## Recommendations

Prioritized recommendation.

## Validation plan

Falsify the conclusion.

## Source register

[External primary source](https://example.com/source).
"""


def fixture() -> tuple[Path, Path]:
    root = tmpdir("pcb-report-")
    must_pass(run(["git", "init", "-q"], cwd=root), "init report fixture")
    project = root / "projects/test-board"
    reports = project / "01_docs/reports"
    reports.mkdir(parents=True)
    (project / "evidence.txt").write_text("evidence\n")
    report = reports / "2026-08-27-test-study.md"
    report.write_text(report_text())
    must_pass(
        run(["git", "add", "projects/test-board/evidence.txt",
             "projects/test-board/01_docs/reports/2026-08-27-test-study.md"], cwd=root),
        "stage report fixture",
    )
    return root, report


@test("real Pluto report and template report contract validate")
def t_real_report():
    result = must_pass(
        run([KPY, AUDIT, REAL_REPORT, "--allow-untracked"]),
        "real Pluto report authoring audit",
    )
    contains(result.out, "REPORT-AUDIT PASS", "report pass marker")
    contains(result.out, "images=1", "local board render denominator")
    check(TEMPLATE_CONTRACT.is_file(), "report contract is absent from commissioner templates")
    project_contract = ROOT / "projects/pluto-rx2-8way-v5/01_docs/reports/contracts.md"
    eq(project_contract.read_bytes(), TEMPLATE_CONTRACT.read_bytes(),
       "Pluto report contract differs from forward template")


@test("clean tracked Markdown report passes with local and HTTPS links")
def t_clean_report():
    _, report = fixture()
    result = must_pass(run([KPY, AUDIT, report]), "clean report")
    contains(result.out, "local_links=1", "local link denominator")
    contains(result.out, "remote_links=1", "remote link denominator")


@test("wrong report identity and missing section fail", kind="known_bad")
def t_identity_and_section_fail():
    root, report = fixture()
    report.write_text(report_text(report_id="2026-08-27-other-study"))
    must_fail(run([KPY, AUDIT, report, "--allow-untracked"]),
              "wrong report id", expect="report_id must equal")
    report.write_text(report_text().replace("## Validation plan", "## Future work"))
    must_fail(run([KPY, AUDIT, report, "--allow-untracked"]),
              "missing report section", expect="missing required section: Validation plan")
    check(root.is_dir(), "fixture unexpectedly removed")


@test("remote image and untracked local evidence fail", kind="known_bad")
def t_link_authority_fail():
    root, report = fixture()
    text = report_text().replace(
        "[External primary source](https://example.com/source)",
        "![mutable image](https://example.com/image.png)",
    )
    report.write_text(text)
    must_fail(run([KPY, AUDIT, report, "--allow-untracked"]),
              "remote report image", expect="remote images are forbidden")

    report.write_text(report_text())
    (root / "projects/test-board/evidence.txt").write_text("changed but tracked\n")
    extra = root / "projects/test-board/untracked.txt"
    extra.write_text("not governed\n")
    report.write_text(report.read_text().replace("../../evidence.txt", "../../untracked.txt"))
    must_fail(run([KPY, AUDIT, report]),
              "untracked local evidence", expect="local link target is not tracked")


@test("MEASURED report cannot carry proposed or owed work", kind="known_bad")
def t_measured_overclaim_fails():
    _, report = fixture()
    report.write_text(report_text(evidence="MEASURED").replace(
        "Prioritized recommendation.",
        "**PROPOSED:** untested redesign.",
    ))
    must_fail(run([KPY, AUDIT, report, "--allow-untracked"]),
              "measured report overclaim", expect="still contains PROPOSED or OWED")


if __name__ == "__main__":
    sys.exit(main())
