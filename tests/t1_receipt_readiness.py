#!/usr/bin/env python3
"""Receipt-derived readiness stays strict and non-authoritative in shadow."""
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import SCRIPTS, check, contains, eq, main, must_pass, run, test, tmpdir  # noqa: E402

STATE = SCRIPTS / "project_state.py"
SEMANTIC = "a" * 64
RAW = "b" * 64
OTHER = "c" * 64


def record(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_ledger(project, *, design_state="pass", target="DESIGN_CLEAN"):
    evidence = project / "evidence.txt"
    evidence.write_text("legacy review\n")
    gate = {
        "id": "legacy-design",
        "required_for": "DESIGN_CLEAN",
        "state": design_state,
        "owner": "design",
        "closes_when": "design evidence passes",
    }
    if design_state == "pass":
        gate["evidence"] = ["evidence.txt"]
    ledger = {
        "schema": 1,
        "target": target,
        "gates": [gate],
        "findings": [],
    }
    path = project / "01_docs" / "findings.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(ledger, sort_keys=False))


def write_bundle(project, *, run_id="run-design", subject=None):
    subject = subject or {"semantic_sha256": SEMANTIC, "raw_sha256": RAW}
    directory = project / "06_build" / "bundles" / "design"
    directory.mkdir(parents=True)
    output = directory / "report.json"
    write_json(output, {"graded": 2, "total": 2})
    manifest = {
        "schema": 1,
        "run_id": run_id,
        "producer": "test-design-gate",
        "producer_version": "test-v1",
        "subject": subject,
        "started_at": "2026-08-15T00:00:01Z",
        "finished_at": "2026-08-15T00:00:02Z",
        "status": "PASS",
        "inputs": {"source.txt": {"sha256": "d" * 64, "size": 10}},
        "outputs": {"report.json": record(output)},
    }
    write_json(directory / "bundle.json", manifest)
    return directory


def receipt(stage_id, applicability, *, subject=None):
    applies = applicability == "APPLIES"
    return {
        "schema": 1,
        "stage_id": stage_id,
        "run_id": "run-design" if stage_id == "P-DESIGN" else "run-optional",
        "subject": subject or {
            "semantic_sha256": SEMANTIC,
            "raw_sha256": RAW,
        },
        "applicability": applicability,
        "applicability_reason": None if applies else "profile has no optional stage",
        "status": "PASS" if applies else "NOT_APPLICABLE",
        "started_at": "2026-08-15T00:00:00Z",
        "finished_at": "2026-08-15T00:00:03Z",
        "elapsed_s": 3.0,
        "graded": 2 if applies else 0,
        "total": 2 if applies else 0,
        "outputs": ["design_bundle"] if applies else [],
        "findings": [],
        "resume": None,
    }


def readiness_tree(*, include_optional=False, legacy_state="pass",
                   legacy_target="DESIGN_CLEAN"):
    project = tmpdir("receipt_ready_")
    (project / "06_build").mkdir()
    write_ledger(project, design_state=legacy_state, target=legacy_target)
    write_bundle(project)
    receipts = project / "06_build" / "receipts"
    write_json(receipts / "P-DESIGN.json", receipt("P-DESIGN", "APPLIES"))
    stages = [{
        "stage_id": "P-DESIGN",
        "required_for": "DESIGN_CLEAN",
        "applicability": "APPLIES",
        "minimum_total": 2,
        "bundles": {
            "design_bundle": "06_build/bundles/design/bundle.json",
        },
    }]
    if include_optional:
        write_json(receipts / "P-OPTIONAL.json",
                   receipt("P-OPTIONAL", "NOT_APPLICABLE"))
        stages.append({
            "stage_id": "P-OPTIONAL",
            "required_for": "DESIGN_CLEAN",
            "applicability": "NOT_APPLICABLE",
            "minimum_total": 0,
            "bundles": {},
        })
    registry = {
        "schema": 1,
        "profile": "usb",
        "target": "DESIGN_CLEAN",
        "subject": {"semantic_sha256": SEMANTIC, "raw_sha256": RAW},
        "receipts_dir": "06_build/receipts",
        "stages": stages,
    }
    registry_path = project / "03_src" / "rules" / "receipt_readiness.yaml"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False))
    return project, registry_path


def run_shadow(project):
    return must_pass(run([
        sys.executable,
        STATE,
        project,
        "--receipt-registry",
        "03_src/rules/receipt_readiness.yaml",
    ]), "project state with receipt shadow")


def run_authoritative(project, authority="receipts", must_succeed=True):
    result = run([
        sys.executable,
        STATE,
        project,
        "--receipt-registry",
        "03_src/rules/receipt_readiness.yaml",
        "--readiness-authority",
        authority,
    ])
    return must_pass(result, "authoritative receipt readiness") \
        if must_succeed else result


def shadow(project):
    return json.loads((project / "06_build" / "project_state.json").read_text())["receipt_shadow"]


@test("clean receipts and accepted bundles agree with legacy readiness")
def t_clean():
    project, _ = readiness_tree()
    result = run_shadow(project)
    contains(result.out, "receipt-shadow=PASS", "clean shadow verdict")
    value = shadow(project)
    eq(value["derived_maturity"], "DESIGN_CLEAN", "receipt maturity")
    eq(value["comparison"]["matches"], True, "legacy agreement")
    eq(value["coverage"], {"satisfied": 1, "total": 1, "not_applicable": 0},
       "strict coverage")


@test("missing and unknown receipts fail closed without changing legacy exit",
      kind="known_bad")
def t_missing_and_unknown():
    project, _ = readiness_tree()
    (project / "06_build" / "receipts" / "P-DESIGN.json").unlink()
    write_json(project / "06_build" / "receipts" / "P-UNKNOWN.json", {})
    result = run_shadow(project)
    contains(result.out, "M-STATE PASS", "legacy remains authority")
    contains(result.out, "receipt-shadow=FAIL", "shadow fails closed")
    findings = "\n".join(shadow(project)["findings"])
    check("missing receipt" in findings and "unknown receipt" in findings,
          "missing/unknown diagnoses were not retained")


@test("stale subject identity is inadmissible", kind="known_bad")
def t_stale_subject():
    project, _ = readiness_tree()
    path = project / "06_build" / "receipts" / "P-DESIGN.json"
    value = json.loads(path.read_text())
    value["subject"]["semantic_sha256"] = OTHER
    write_json(path, value)
    run_shadow(project)
    value = shadow(project)
    eq(value["status"], "FAIL", "stale receipt verdict")
    check(any("stale" in item for item in value["findings"]),
          "stale identity diagnosis")


@test("post-acceptance output tamper breaks hash/size freshness",
      kind="known_bad")
def t_tampered_bundle():
    project, _ = readiness_tree()
    output = project / "06_build" / "bundles" / "design" / "report.json"
    output.write_text('{"graded": 0, "total": 2}\n')
    run_shadow(project)
    value = shadow(project)
    eq(value["status"], "FAIL", "tampered bundle verdict")
    check(any("hash/size changed" in item for item in value["findings"]),
          "tamper diagnosis")


@test("profile-declared NOT_APPLICABLE receipt is explicit and counted")
def t_not_applicable():
    project, _ = readiness_tree(include_optional=True)
    run_shadow(project)
    value = shadow(project)
    eq(value["status"], "PASS", "N/A shadow verdict")
    eq(value["coverage"], {"satisfied": 2, "total": 2, "not_applicable": 1},
       "N/A denominator")


@test("low nonzero denominator cannot advance receipt readiness",
      kind="known_bad")
def t_low_nonzero_denominator():
    project, registry_path = readiness_tree()
    registry = yaml.safe_load(registry_path.read_text())
    registry["stages"][0]["minimum_total"] = 3
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False))
    result = run_shadow(project)
    contains(result.out, "M-STATE PASS", "legacy remains authority")
    contains(result.out, "receipt-shadow=FAIL", "minimum coverage verdict")
    value = shadow(project)
    check(any("total 2 is below minimum_total 3" in item
              for item in value["findings"]), "minimum coverage diagnosis")


@test("one accepted bundle cannot satisfy two stage/output bindings",
      kind="known_bad")
def t_duplicate_bundle_reuse():
    project, registry_path = readiness_tree()
    registry = yaml.safe_load(registry_path.read_text())
    registry["stages"].append({
        "stage_id": "P-SECOND",
        "required_for": "DESIGN_CLEAN",
        "applicability": "APPLIES",
        "minimum_total": 1,
        "bundles": {
            "second_bundle": "06_build/bundles/design/bundle.json",
        },
    })
    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False))
    result = run_shadow(project)
    contains(result.out, "M-STATE PASS", "legacy remains authority")
    contains(result.out, "receipt-shadow=FAIL", "duplicate bundle verdict")
    value = shadow(project)
    check(any("is reused by P-DESIGN.design_bundle and P-SECOND.second_bundle"
              in item for item in value["findings"]),
          "duplicate bundle ownership diagnosis")


@test("legacy/receipt disagreement is exposed but legacy result stays authority")
def t_legacy_disagreement():
    project, _ = readiness_tree(legacy_state="pending", legacy_target="DRAFT")
    result = run_shadow(project)
    contains(result.out, "derived=DRAFT", "legacy derived result")
    contains(result.out, "legacy-agrees=False", "disagreement summary")
    value = shadow(project)
    eq(value["status"], "PASS", "independent receipt verdict")
    eq(value["comparison"], {
        "legacy_derived_maturity": "DRAFT",
        "receipt_derived_maturity": "DESIGN_CLEAN",
        "maturity_matches": False,
        "matches": False,
    }, "exact disagreement")


@test("receipt authority promotes the closed registry into project maturity")
def t_receipts_authoritative():
    project, _ = readiness_tree()
    result = run_authoritative(project)
    contains(result.out, "authority=receipt-registry", "authority summary")
    value = json.loads(
        (project / "06_build" / "project_state.json").read_text())
    eq(value["derived_maturity"], "DESIGN_CLEAN", "authoritative maturity")
    eq(value["authority_satisfied"], True, "authority satisfaction")
    check("legacy_projection" in value, "legacy comparison was discarded")


@test("agreement authority refuses a receipt/legacy maturity disagreement",
      kind="known_bad")
def t_agreement_refuses_disagreement():
    project, _ = readiness_tree(legacy_state="pending", legacy_target="DRAFT")
    result = run_authoritative(project, "agreement", must_succeed=False)
    check(result.rc != 0, "agreement mode accepted contradictory authorities")
    contains(result.out, "legacy-agrees=False", "agreement diagnosis")


@test("receipt authority fails closed when an expected receipt is missing",
      kind="known_bad")
def t_receipts_authority_missing():
    project, _ = readiness_tree()
    (project / "06_build/receipts/P-DESIGN.json").unlink()
    result = run_authoritative(project, must_succeed=False)
    check(result.rc != 0, "receipt authority ignored a missing receipt")
    contains(result.out, "receipt-receipts=FAIL", "missing receipt diagnosis")


if __name__ == "__main__":
    raise SystemExit(main())
