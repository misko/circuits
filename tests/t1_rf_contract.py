#!/usr/bin/env python3
"""T1: RF applicability, requirements, exact artifact and review coverage."""
import hashlib
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

GATE = SCRIPTS / "rf_contract_check.py"
HEAD = run(["git", "rev-parse", "HEAD"], cwd=ROOT).out.strip()


def project(enabled=True):
    d = tmpdir("rfcontract_") / "demo"
    rules = d / "03_src" / "rules"
    reviews = d / "08_reviews"
    artifacts = d / "04_kicad"
    fab = d / "07_releases" / "v1" / "fab"
    for path in (rules, reviews, artifacts, fab):
        path.mkdir(parents=True, exist_ok=True)
    (artifacts / "demo.kicad_sch").write_text("schematic\n")
    (artifacts / "demo.kicad_pcb").write_text("board\n")
    (fab / "demo.zip").write_bytes(b"gerbers\n")
    rf = {"enabled": enabled,
          "rationale": "RF applicability was evaluated from the signal path."}
    if enabled:
        rf.update({
            "risk_tier": "phase-coherent",
            "risk_basis": "Six GHz phase matching makes electrical length binding.",
            "ports": [{"id": "RF1", "nets": ["RF1"],
                       "band_hz": [1e6, 6e9], "z0_ohm": 50,
                       "launch": "SMA launch model", "termination": "50 ohm",
                       "reference_layer": "In1.Cu"}],
            "cross_sections": [{"id": "CPWG", "stackup_source": "fab rev A",
                                "solver": "field_solver evidence.txt",
                                "copper_layer": "F.Cu",
                                "reference_layer": "In1.Cu",
                                "dielectric_height_mm": 0.21, "dk": 4.4,
                                "target_z0_ohm": 50, "width_mm": 0.36,
                                "gap_mm": 0.2}],
            "performance_claims": [{"id": "RF-CLAIM-PHASE",
                                    "claim": "relative phase is bounded",
                                    "acceptance": "spread <= 1 mm",
                                    "evidence": "length audit"}],
            "first_article": {"measurements": ["VNA S11/S21"],
                              "acceptance": ["S11 < -10 dB"]},
            "reviews": {
                "schematic": {"path": "08_reviews/rf_schematic.md",
                              "artifact": "04_kicad/demo.kicad_sch",
                              "requirements": ["RF-SCH-TOPOLOGY"]},
                "pcb": {"path": "08_reviews/rf_pcb.md",
                        "artifact": "04_kicad/demo.kicad_pcb",
                        "requirements": ["RF-PCB-RETURN", "RF-PCB-LAUNCH"]},
                "fab": {"path": "08_reviews/rf_fab.md",
                        "artifact": "07_releases/v1/fab/demo.zip",
                        "requirements": ["RF-FAB-STACKUP"]},
            },
        })
    (rules / "rf.yaml").write_text(yaml.safe_dump({"schema": 1, "rf": rf},
                                                   sort_keys=False))
    return d


def write_review(project_dir, phase, requirements, *, artifact=None,
                 bound_hash=None, verdict="PASS"):
    kinds = {"schematic": "RF_SCHEMATIC", "pcb": "RF_PCB", "fab": "RF_FAB"}
    names = {"schematic": "rf_schematic.md", "pcb": "rf_pcb.md",
             "fab": "rf_fab.md"}
    if artifact is None:
        artifact = ({"schematic": project_dir / "04_kicad/demo.kicad_sch",
                     "pcb": project_dir / "04_kicad/demo.kicad_pcb",
                     "fab": project_dir / "07_releases/v1/fab/demo.zip"})[phase]
    digest = bound_hash or hashlib.sha256(artifact.read_bytes()).hexdigest()
    verdict_line = ("fab_package_verdict: READY" if phase == "fab"
                    else "design_verdict: SOUND")
    text = (f"review_kind: {kinds[phase]}\n"
            "subject: demo exact artifact\n"
            "reviewer: independent-rf-reviewer\n"
            "independence: independent-from-design-author\n"
            f"source_commit: {HEAD}\n"
            f"artifact_sha256: {digest}\n"
            f"{verdict_line}\n\n")
    text += "".join(f"requirement: {req} {verdict}\n" for req in requirements)
    (project_dir / "08_reviews" / names[phase]).write_text(text)


def gate(d, *reviews):
    args = [KPY, GATE, d]
    for phase in reviews:
        args += ["--require-review", phase]
    return run(args)


@test("legacy inspection may report unmigrated without claiming RF review")
def t_missing_contract_is_visible_legacy_state():
    d = tmpdir("rfcontract_missing_") / "demo"
    d.mkdir(parents=True)
    r = must_pass(gate(d), "legacy unmigrated inspection")
    contains(r.out, "UNMIGRATED", "legacy state")


@test("seal-time RF applicability is fail-closed", kind="known_bad")
def t_missing_contract_fails_when_required():
    d = tmpdir("rfcontract_required_") / "demo"
    d.mkdir(parents=True)
    must_fail(run([KPY, GATE, d, "--require-applicability"]),
              "missing RF applicability", "no explicit applicability")


@test("a non-RF board records an explicit applicability decision")
def t_disabled_is_explicit_na():
    r = must_pass(gate(project(enabled=False)), "RF disabled contract")
    contains(r.out, "applicability 1/1", "applicability denominator")


@test("a complete enabled RF contract passes schema validation")
def t_enabled_contract_is_complete():
    r = must_pass(gate(project()), "complete RF contract")
    contains(r.out, "1 port(s), 1 cross-section(s), 1 claim(s)",
             "requirements census")


@test("RF review phases bind exact artifacts and grade every requirement")
def t_three_exact_reviews_pass():
    d = project()
    write_review(d, "schematic", ["RF-SCH-TOPOLOGY"])
    write_review(d, "pcb", ["RF-PCB-RETURN", "RF-PCB-LAUNCH"])
    write_review(d, "fab", ["RF-FAB-STACKUP"])
    r = must_pass(gate(d, "schematic", "pcb", "fab"), "three RF reviews")
    contains(r.out, "3/3 review phase(s) requested", "phase denominator")


@test("an enabled RF contract cannot declare zero review requirements",
      kind="known_bad")
def t_zero_requirement_denominator_fails():
    d = project()
    path = d / "03_src/rules/rf.yaml"
    data = yaml.safe_load(path.read_text())
    data["rf"]["reviews"]["pcb"]["requirements"] = []
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    must_fail(gate(d), "zero RF PCB requirements", "list with >= 1")


@test("an RF review with partial requirement coverage fails",
      kind="known_bad")
def t_partial_review_fails():
    d = project()
    write_review(d, "pcb", ["RF-PCB-RETURN"])
    r = must_fail(gate(d, "pcb"), "partial RF PCB review", "RF-PCB-COVERAGE")
    contains(r.out, "graded 1/2", "coverage count")


@test("an RF review of adjacent artifact bytes fails", kind="known_bad")
def t_artifact_binding_fails():
    d = project()
    write_review(d, "pcb", ["RF-PCB-RETURN", "RF-PCB-LAUNCH"],
                 bound_hash="0" * 64)
    must_fail(gate(d, "pcb"), "wrong RF board hash", "RF-PCB-BINDING")


@test("a failed RF requirement cannot hide inside full coverage",
      kind="known_bad")
def t_failed_requirement_fails():
    d = project()
    write_review(d, "schematic", ["RF-SCH-TOPOLOGY"], verdict="FAIL")
    must_fail(gate(d, "schematic"), "failed RF requirement", "fail=['RF-SCH-TOPOLOGY']")


@test("placeholder RF acceptance and evidence are rejected", kind="known_bad")
def t_placeholder_claim_fails():
    d = project()
    path = d / "03_src/rules/rf.yaml"
    data = yaml.safe_load(path.read_text())
    data["rf"]["performance_claims"][0]["evidence"] = "TBD"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    must_fail(gate(d), "placeholder RF evidence", "must be substantive")


if __name__ == "__main__":
    sys.exit(main())
