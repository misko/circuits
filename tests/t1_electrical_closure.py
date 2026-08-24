#!/usr/bin/env python3
"""T1: E-CLOSURE composition is non-vacuous and fail closed."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/kicad-pcb/scripts"))
sys.path.insert(0, str(ROOT / "skills/pcb-design/scripts"))
import electrical_closure  # noqa: E402
from pipeline_applicability import (  # noqa: E402
    APPLIES, FACT_DOMAINS, FACT_KIND, INCOMPLETE, NOT_APPLICABLE,
    REQUIREMENTS_KIND, canonical_sha256, compile_applicability,
    verify_applicability,
)


def project_tree():
    project = tmpdir("e_closure_")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "03_src/rules/electrical_invariants.yaml").write_text(
        "schema: 1\ninvariants: []\n")
    (project / "02_parts/U1").mkdir(parents=True)
    (project / "02_parts/U1/part.yaml").write_text("mpn: U1\n")
    (project / "03_tscircuit/build").mkdir(parents=True)
    (project / "03_tscircuit/build/circuit.json").write_text("[]\n")
    (project / "06_build/netlists").mkdir(parents=True)
    (project / "06_build/netlists/board.net").write_text("(export)\n")
    return project


def applicability(*, applies=True):
    profile = {
        "schema": 1, "signal_integrity": "ordinary", "assembly": "none",
        "firmware": "forbidden", "foreign_mating": False, "target": "design",
    }
    facts = {}
    for domain in FACT_DOMAINS:
        facts[domain] = {
            "schema": 1, "kind": FACT_KIND, "domain": domain,
            "validation": {"status": "PASS", "authority": f"{domain}_check.py",
                           "subject_sha256": "a" * 64},
            "facts": {"cross_device_operating_states": (
                applies and domain == "power")},
        }
    rule = {
        "schema": 1, "id": "operating_state_compatibility",
        "sources": ["architecture", "integration", "power"],
        "when": {"any": [
            {"source": domain, "fact": "cross_device_operating_states",
             "equals": True}
            for domain in ("architecture", "integration", "power")
        ]},
        "not_applicable_reason": "NO_CROSS_DEVICE_OPERATING_STATES",
    }
    requirements = {
        "schema": 1, "kind": REQUIREMENTS_KIND, "rules": [rule],
    }
    exact = {"profile": profile, "facts": facts,
             "requirements": requirements}
    return compile_applicability(**exact), exact


@test("E-CLOSURE composes exactly nine specialist predicates")
def t_clean_composition():
    project = project_tree()
    report = electrical_closure.grade(
        project, runner=lambda _command, _cwd: {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"})
    eq(report["verdict"], "ACCEPTED", "closure verdict")
    eq(report["coverage"], {"passing": 9, "total": 9}, "closure denominator")


@test("one missing electrical predicate rejects the whole closure",
      kind="known_bad")
def t_one_failure_rejects():
    project = project_tree()
    calls = {"count": 0}
    def runner(_command, _cwd):
        calls["count"] += 1
        return {"status": "FAIL" if calls["count"] == 4 else "PASS",
                "returncode": 1 if calls["count"] == 4 else 0,
                "elapsed_s": 0.01, "output": "fixture"}
    report = electrical_closure.grade(project, runner=runner)
    eq(report["verdict"], "REJECTED", "closure verdict")
    eq(report["coverage"], {"passing": 8, "total": 9}, "closure denominator")
    check(report["checks"]["design_and_corner_models"]["status"] == "FAIL",
          "failed corner predicate disappeared")


@test("legacy operating-state opt-in remains authoritative and hash-bound",
      kind="known_bad")
def t_legacy_state_presence_remains_authoritative():
    project = project_tree()
    (project / "03_src/rules/operating_states.yaml").write_text("""
schema: 1
contracts:
  - id: pd_to_input
    phase: negotiated
    producer: {ref: U_PD, quantity: voltage, unit: V, min: 19, max: 21,
               evidence: {source: 02_parts/U_PD/part.yaml, sha256: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
                          locator: decoded selected-part state}}
    consumer: {ref: U_IN, quantity: voltage, unit: V, min: 16, max: 30,
               evidence: {source: 02_parts/U_IN/part.yaml, sha256: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb,
                          locator: exact UVLO and input limits}}
""")
    (project / "03_src/rules/operating_state_manifest.yaml").write_text("""
schema: 1
expected:
  - {id: pd_to_input, phase: negotiated}
""")
    def runner(command, _cwd):
        is_state = "operating_state_check.py" in " ".join(command)
        return {
            "status": "FAIL" if is_state else "PASS",
            "returncode": 1 if is_state else 0, "elapsed_s": 0.01,
            "output": "fixture state mismatch" if is_state else "fixture pass"}

    report = electrical_closure.grade(project, runner=runner)
    eq(report["verdict"], "REJECTED", "legacy E-STATE was weakened")
    eq(report["coverage"], {"passing": 9, "total": 10},
       "legacy opt-in denominator")
    eq(report["checks"]["operating_state_compatibility"]["status"],
       "FAIL", "legacy E-STATE result disappeared")
    check("03_src/rules/operating_states.yaml" in report["subject"],
          "legacy operating-state source left the receipt identity")
    check("03_src/rules/operating_state_manifest.yaml" in report["subject"],
          "legacy operating-state manifest left the receipt identity")


@test("fact-applicable E-STATE records a pending isolated shadow task")
def t_state_shadow_composition():
    project = project_tree()
    (project / "03_src/rules/operating_states.yaml").write_text("schema: 1\n")
    (project / "03_src/rules/operating_state_manifest.yaml").write_text("schema: 1\n")
    receipt, exact = applicability(applies=True)
    calls = 0

    def runner(_command, _cwd):
        nonlocal calls
        calls += 1
        return {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"}

    report = electrical_closure.grade(
        project, runner=runner,
        operating_state_applicability=receipt,
        applicability_inputs=exact, applicability_mode="shadow")
    eq(report["verdict"], "ACCEPTED", "legacy closure verdict")
    eq(report["coverage"], {"passing": 10, "total": 10},
       "authoritative denominator")
    check("shadow_checks" not in report,
          "shadow request entered the authoritative receipt")
    shadow = electrical_closure._pending_state_shadow_request(
        report["subject"], applicability_path=Path("applicability.json"),
        applicability_inputs_path=Path("inputs.json"))
    eq(shadow["checks"]["operating_state_compatibility"]["status"],
       "INCOMPLETE", "E-STATE pending request")
    eq(calls, 10, "shadow migration changed the legacy E-STATE runtime")
    check("no shadow input was opened" in
          shadow["checks"]["operating_state_compatibility"]["output"],
          "pending request overclaimed shadow execution")


@test("applicable E-STATE with missing config is shadow INCOMPLETE, not N-A",
      kind="known_bad")
def t_applicable_missing_state_config():
    project = project_tree()
    receipt, exact = applicability(applies=True)
    report = electrical_closure.grade(
        project, runner=lambda _command, _cwd: {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"},
        operating_state_applicability=receipt,
        applicability_inputs=exact, applicability_mode="shadow")
    eq(report["verdict"], "ACCEPTED", "shadow changed legacy verdict")
    eq(report["coverage"], {"passing": 9, "total": 9},
       "shadow changed legacy identity denominator")
    shadow = electrical_closure._state_shadow_request(
        project, report["subject"], receipt, exact)
    state = shadow["checks"]["operating_state_compatibility"]
    eq(state["status"], "INCOMPLETE", "missing applicable config")
    check("configuration is missing" in state["output"],
          "missing applicable configuration was not named")


@test("validated facts can prove E-STATE NOT_APPLICABLE despite stray config")
def t_typed_state_not_applicable():
    project = project_tree()
    (project / "03_src/rules/operating_states.yaml").write_text("invented: true\n")
    receipt, exact = applicability(applies=False)
    report = electrical_closure.grade(
        project, runner=lambda _command, _cwd: {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"},
        operating_state_applicability=receipt,
        applicability_inputs=exact, applicability_mode="shadow")
    shadow = electrical_closure._state_shadow_request(
        project, report["subject"], receipt, exact)
    state = shadow["checks"]["operating_state_compatibility"]
    eq(state["status"], "N-A")
    eq(state["applicability"]["reason"],
       "NO_CROSS_DEVICE_OPERATING_STATES")


@test("shadow applicability cannot authorize a typed E-STATE N/A promotion",
      kind="known_bad")
def t_typed_state_not_applicable_authoritative():
    project = project_tree()
    receipt, exact = applicability(applies=False)
    report = electrical_closure.grade(
        project, runner=lambda _command, _cwd: {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"},
        operating_state_applicability=receipt,
        applicability_inputs=exact, applicability_mode="authoritative")
    eq(report["verdict"], "INCOMPLETE")
    eq(report["coverage"], {"passing": 9, "total": 10})
    state = report["checks"]["operating_state_applicability_authority"]
    eq(state["status"], "INCOMPLETE")
    check("compiled applicability is SHADOW" in state["output"],
          "unverified source truth was promoted from structural hashes")
    check("shadow_checks" not in report,
          "promoted N/A was incorrectly retained as shadow evidence")


@test("applicability receipts are exact-input hash bound", kind="known_bad")
def t_applicability_hash_binding():
    receipt, exact = applicability(applies=True)
    check(verify_applicability(receipt, exact)[0],
          "fresh applicability receipt did not recompile")
    altered = json.loads(json.dumps(receipt))
    altered["decisions"]["operating_state_compatibility"]["status"] = \
        "NOT_APPLICABLE"
    altered["decisions"]["operating_state_compatibility"]["reason"] = \
        "NO_CROSS_DEVICE_OPERATING_STATES"
    rehashed = json.loads(json.dumps(altered))
    del rehashed["binding"]["receipt_sha256"]
    altered["binding"]["receipt_sha256"] = canonical_sha256(rehashed)
    valid, failures = verify_applicability(altered, exact)
    check(not valid, "attacker-rehashed applicability status was accepted")
    check(any("recompilation" in row for row in failures),
          "exact-input mismatch did not name recompilation")


@test("applicability distinguishes APPLIES, NOT_APPLICABLE, and unvalidated "
      "INCOMPLETE", kind="known_bad")
def t_applicability_three_way_status():
    applies, _ = applicability(applies=True)
    not_applicable, _ = applicability(applies=False)
    eq(applies["authority"], "SHADOW",
       "structural applicability compilation claimed owner authority")
    eq(applies["decisions"]["operating_state_compatibility"]["status"],
       APPLIES)
    eq(not_applicable["decisions"]["operating_state_compatibility"]["status"],
       NOT_APPLICABLE)

    _receipt, exact = applicability(applies=True)
    exact["facts"]["power"]["validation"]["status"] = "FAIL"
    incomplete = compile_applicability(**exact)
    decision = incomplete["decisions"]["operating_state_compatibility"]
    eq(decision["status"], INCOMPLETE)
    eq(decision["reason"], "APPLICABILITY_INPUT_INCOMPLETE")
    check(any("not validated PASS" in finding
              for finding in decision["findings"]),
          "failed source validation was silently treated as N/A")


@test("E-CLOSURE shadow publication failure preserves legacy exit")
def t_shadow_publish_failure_is_nonblocking():
    project = project_tree()
    output = project / "closure.json"
    receipt = {
        "verdict": "ACCEPTED", "coverage": {"passing": 9, "total": 9}}
    with mock.patch("electrical_closure.grade", return_value=receipt), \
         mock.patch("electrical_closure._publish",
                    side_effect=OSError("shadow disk unavailable")):
        rc = electrical_closure.main([
            str(project), "--json", str(output),
            "--stage-bundle", str(project / "bundle"),
            "--stage-result", str(project / "stage.json"),
        ])
    eq(rc, 0, "shadow publisher changed accepted closure exit")
    check(output.is_file(), "legacy closure receipt was not retained")


@test("E-CLOSURE shadow inputs are not opened by the legacy hot path")
def t_shadow_inputs_are_pending_only():
    project = project_tree()
    output = project / "closure.json"
    receipt = {
        "verdict": "ACCEPTED", "subject": {}, "checks": {},
        "coverage": {"passing": 9, "total": 9}}
    with mock.patch("electrical_closure.grade", return_value=receipt), \
         mock.patch.object(Path, "read_text",
                           side_effect=AssertionError("shadow input opened")):
        rc = electrical_closure.main([
            str(project), "--json", str(output),
            "--applicability-mode", "shadow",
            "--operating-state-applicability", str(project / "missing-a.json"),
            "--applicability-inputs", str(project / "missing-b.json"),
        ])
    eq(rc, 0, "pending shadow input changed legacy exit")
    shadow = json.loads((project / "closure.shadow.json").read_text())
    eq(shadow["checks"]["operating_state_compatibility"]["status"],
       "INCOMPLETE")


@test("E-CLOSURE rejects output aliases before grading", kind="known_bad")
def t_output_alias_is_rejected_before_write():
    project = project_tree()
    output = project / "closure.json"
    output.write_text("sentinel")
    with mock.patch("electrical_closure.grade") as grade:
        rc = electrical_closure.main([
            str(project), "--json", str(output),
            "--stage-bundle", str(project / "bundle"),
            "--stage-result", str(output),
        ])
    eq(rc, 2, "aliased output was accepted")
    grade.assert_not_called()
    eq(output.read_text(), "sentinel", "aliased output was overwritten")


@test("E-CLOSURE stage request preserves an existing accepted bundle")
def t_stage_request_never_promotes_bundle():
    project = project_tree()
    bundle = project / "bundle"
    bundle.mkdir()
    (bundle / "sentinel.txt").write_text("accepted")
    output = project / "closure.json"
    stage = project / "stage.json"
    receipt = electrical_closure.grade(
        project, runner=lambda _command, _cwd: {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"})
    with mock.patch("electrical_closure.grade", return_value=receipt):
        rc = electrical_closure.main([
            str(project), "--json", str(output),
            "--stage-bundle", str(bundle), "--stage-result", str(stage)])
    eq(rc, 0)
    eq((bundle / "sentinel.txt").read_text(), "accepted")
    eq(json.loads(stage.read_text())["status"], "INCOMPLETE")


if __name__ == "__main__":
    raise SystemExit(main())
