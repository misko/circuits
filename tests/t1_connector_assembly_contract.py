#!/usr/bin/env python3
"""T1: one fail-closed connector assembly/service authority for PCB and case."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

PCB_SCRIPTS = ROOT / "skills/pcb-design/scripts"
sys.path.insert(0, str(PCB_SCRIPTS))
import connector_assembly_contract as contract_module  # noqa: E402
from connector_assembly_contract import (  # noqa: E402
    DEFAULT_CONTRACT, DEFAULT_OUTPUT, ContractError, load_and_compile,
    validate_receipt,
)

COMPILER = PCB_SCRIPTS / "connector_assembly_contract.py"
TEMPLATE = ROOT / "skills/pcb-design/templates/03_src/rules/connector_assemblies.yaml"
PLUTO_V5 = ROOT / "projects/pluto-rx2-8way-v5"


def evidence(grade: str = "exact", source_ids: list[str] | None = None) -> dict:
    return {
        "grade": grade,
        "source_ids": (["fixture-drawing"] if source_ids is None else source_ids),
        "rationale": "Fixture-only selected hardware evidence; not a reusable dimension.",
    }


def good_contract() -> dict:
    ev = evidence()
    return {
        "schema": 1,
        "contract_id": "test-connector-bank",
        "evidence_sources": [
            {
                "id": "fixture-drawing",
                "kind": "manufacturer-drawing",
                "path": "02_parts/fixture/evidence.txt",
            },
            {
                "id": "fixture-placement",
                "kind": "placement-contract",
                "path": "02_parts/fixture/placement.yaml",
            },
        ],
        "assemblies": [{
            "id": "fixture-threaded-profile",
            "instances": [
                {"ref": "J1", "mating_axis_board": [0.0, -1.0, 0.0],
                 "simultaneous_group_ids": ["fixture-bank"]},
                {"ref": "J2", "mating_axis_board": [0.0, -1.0, 0.0],
                 "simultaneous_group_ids": ["fixture-bank"]},
            ],
            "receptacle": {
                "manufacturer": "Fixture Maker", "mpn": "FIX-JACK",
                "mounting_method": "through-hole", "model_source_id": None,
                "body_envelope_mm": {"x": 9.0, "y": 7.0, "z": 8.0},
                "evidence": copy.deepcopy(ev),
            },
            "mate": {
                "manufacturer": "Fixture Maker", "mpn": "FIX-PLUG",
                "part_kind": "cable-plug", "model_source_id": None,
                "body_envelope_mm": {"x": 12.0, "y": 8.0, "z": 8.0},
                "evidence": copy.deepcopy(ev),
            },
            "interface": {
                "mating_plane_offset_mm": 10.0,
                "minimum_exposure_mm": 1.0,
                "exposure_setback_allowance_mm": 0.4,
                "minimum_service_clearance_mm": 0.5,
                "orientation_source_id": "fixture-placement",
                "evidence": evidence(
                    source_ids=["fixture-drawing", "fixture-placement"]),
            },
            "grip": {
                "kind": "coupling-nut", "across_flats_mm": 7.0,
                "outer_diameter_mm": 8.0, "axial_length_mm": 4.0,
                "evidence": copy.deepcopy(ev),
            },
            "fastening": {
                "method": "threaded", "thread_designation": "fixture-thread",
                "final_tightening": "torque-wrench",
                "evidence": copy.deepcopy(ev),
            },
            "tool": {
                "kind": "open-end-torque-wrench", "identifier": "FIX-WRENCH",
                "model_source_id": None,
                "head_envelope_mm": {"x": 5.0, "y": 12.0, "z": 4.0},
                "approach": "along_mating_axis",
                "effective_sweep_radius_mm": 9.0,
                "counter_tool_required": True,
                "evidence": copy.deepcopy(ev),
            },
            "torque": {
                "required": True, "minimum_nm": 0.3, "maximum_nm": 0.5,
                "evidence": copy.deepcopy(ev),
            },
            "reaction": {
                "method": "counter-wrench",
                "load_path": "mating body to held receptacle body",
                "evidence": copy.deepcopy(ev),
            },
            "cable": {
                "kind": "coaxial", "manufacturer": "Fixture Maker",
                "mpn": "FIX-CABLE", "outer_diameter_mm": 3.0,
                "straight_run_mm": 10.0, "minimum_bend_radius_mm": 12.0,
                "exit": "along_mating_axis", "evidence": copy.deepcopy(ev),
            },
            "operations": [{
                "id": "mate-and-tighten", "sequence": 1, "kind": "tighten",
                "required": True, "with_neighbors_populated": True,
                "start_state": "plug-hand-started", "end_state": "plug-torqued",
                "evidence": copy.deepcopy(ev),
            }],
            "tolerances": [{
                "id": "mating-plane-drawing-stack",
                "applies_to": "interface.mating_plane_offset_mm",
                "effect": "exposure_setback",
                "minus_mm": 0.2, "plus_mm": 0.2,
                "evidence": copy.deepcopy(ev),
            }],
        }],
        "simultaneous_groups": [{
            "id": "fixture-bank", "members": ["J1", "J2"],
            "required_state": "all_connected",
            "serviceable_member_refs": ["J1", "J2"],
        }],
    }


def no_operated_contract() -> dict:
    return {
        "schema": 1,
        "contract_id": "test-no-operated-connectors",
        "evidence_sources": [{
            "id": "connector-census",
            "kind": "connector-applicability-record",
            "path": "02_parts/fixture/applicability.yaml",
        }],
        "applicability": {
            "operated": False,
            "evidence": {
                "grade": "exact",
                "source_ids": ["connector-census"],
                "rationale": (
                    "Project connector census records no connector that is "
                    "mated, fastened, cabled, or serviced."),
            },
        },
        "assemblies": [],
        "simultaneous_groups": [],
    }


def fixture(value: dict | None = None) -> Path:
    project = tmpdir("connector-contract-")
    rules = project / "03_src/rules"
    parts = project / "02_parts/fixture"
    rules.mkdir(parents=True)
    parts.mkdir(parents=True)
    (parts / "evidence.txt").write_text("fixture drawing revision A\n")
    (parts / "placement.yaml").write_text(
        "J1: [0.0, -1.0, 0.0]\nJ2: [0.0, -1.0, 0.0]\n")
    (parts / "model.step").write_text("ISO-10303-21; fixture model\n")
    (parts / "applicability.yaml").write_text(
        "operated_connector_refs: []\nreviewed_scope: fixture-board\n")
    (rules / "connector_assemblies.yaml").write_text(
        yaml.safe_dump(good_contract() if value is None else value,
                       sort_keys=False, allow_unicode=True))
    return project


def invoke(project: Path, *extra: str):
    return run([KPY, COMPILER, "--project", project, *extra], cwd=ROOT)


@test("exact complete connector bank compiles deterministically and reopens")
def t_clean_compile_and_reopen():
    project = fixture()
    first = load_and_compile(project, DEFAULT_CONTRACT)
    second = load_and_compile(project, DEFAULT_CONTRACT)
    eq(first, second, "deterministic in-memory receipt")
    eq(first["kind"], "connector-assembly-contract-receipt", "receipt kind")
    eq(first["status"], "PASS", "complete receipt status")
    eq(first["summary"], {
        "assembly_count": 1,
        "instance_count": 2,
        "simultaneous_group_count": 1,
        "operation_count": 1,
        "tolerance_count": 1,
        "evidence_total": 11,
        "evidence_exact": 11,
        "evidence_conservative": 0,
        "evidence_unknown": 0,
        "evidence_ceiling": "EXACT",
        "evidence_file_count": 2,
    }, "receipt denominators")
    check(validate_receipt(first, project) == (True, []),
          "fresh receipt did not recompile identically")
    result = must_pass(invoke(project), "clean connector compiler CLI")
    contains(result.out, "CONNECTOR-CONTRACT PASS", "clean status line")
    contains(result.out, "coverage=11/11", "clean evidence denominator")
    disk = json.loads((project / "06_build/verification/connector_assembly_contract.json").read_text())
    eq(disk, first, "CLI and API receipt")


@test("conservative fact lock remains contract PASS but caps the evidence ceiling")
def t_conservative_ceiling():
    value = good_contract()
    value["assemblies"][0]["tool"]["evidence"] = evidence("conservative")
    receipt = load_and_compile(fixture(value))
    eq(receipt["status"], "PASS", "evidenced conservative contract status")
    eq(receipt["summary"]["evidence_conservative"], 1, "conservative denominator")
    eq(receipt["summary"]["evidence_ceiling"], "CONSERVATIVE", "conservative ceiling")


@test("explicit operated applicability retains the nonzero PASS contract")
def t_explicit_operated_true():
    value = good_contract()
    value["evidence_sources"].append({
        "id": "connector-census",
        "kind": "connector-applicability-record",
        "path": "02_parts/fixture/applicability.yaml",
    })
    value["applicability"] = {
        "operated": True,
        "evidence": {
            "grade": "exact",
            "source_ids": ["connector-census"],
            "rationale": "The reviewed fixture design operates J1 and J2.",
        },
    }
    project = fixture(value)
    receipt = load_and_compile(project)
    eq(receipt["status"], "PASS", "explicit operated contract status")
    eq(receipt["summary"]["assembly_count"], 1,
       "explicit operated assembly denominator")
    eq(receipt["summary"]["instance_count"], 2,
       "explicit operated instance denominator")
    eq(receipt["summary"]["evidence_total"], 12,
       "explicit applicability evidence denominator")
    check(validate_receipt(receipt, project) == (True, []),
          "explicit operated receipt did not revalidate")


@test("held skill template represents unknowns and exits 2 without dimensions")
def t_template_is_incomplete():
    project = tmpdir("connector-template-")
    rules = project / "03_src/rules"
    rules.mkdir(parents=True)
    (rules / "connector_assemblies.yaml").write_bytes(TEMPLATE.read_bytes())
    result = invoke(project)
    eq(result.rc, 2, "held template exit")
    contains(result.out, "CONNECTOR-CONTRACT INCOMPLETE", "template verdict")
    receipt = json.loads((project / "06_build/verification/connector_assembly_contract.json").read_text())
    eq(receipt["summary"]["evidence_unknown"], 11, "template unknown denominator")
    eq(receipt["status"], "INCOMPLETE", "template receipt status")
    interface = receipt["assemblies"][0]["interface"]
    check(all(interface[key] is None for key in (
        "mating_plane_offset_mm", "minimum_exposure_mm",
        "exposure_setback_allowance_mm", "minimum_service_clearance_mm")),
        "template invented an interface dimension")


@test("exact no-operated-connectors authority compiles, publishes, and reopens")
def t_no_operated_connectors_na():
    project = fixture(no_operated_contract())
    first = load_and_compile(project)
    second = load_and_compile(project)
    eq(first, second, "deterministic N-A receipt")
    eq(first["status"], "N-A", "no-operated receipt status")
    eq(first["assemblies"], [], "N-A assembly denominator")
    eq(first["simultaneous_groups"], [], "N-A group denominator")
    eq(first["summary"], {
        "assembly_count": 0,
        "instance_count": 0,
        "simultaneous_group_count": 0,
        "operation_count": 0,
        "tolerance_count": 0,
        "evidence_total": 1,
        "evidence_exact": 1,
        "evidence_conservative": 0,
        "evidence_unknown": 0,
        "evidence_ceiling": "EXACT",
        "evidence_file_count": 1,
    }, "N-A receipt denominators")
    check(validate_receipt(first, project) == (True, []),
          "fresh N-A receipt did not validate")
    result = must_pass(invoke(project), "no-operated connector compiler CLI")
    contains(result.out, "CONNECTOR-CONTRACT N-A", "N-A status line")
    contains(result.out, "assemblies=0 instances=0 coverage=1/1",
             "N-A evidence denominator")
    disk = json.loads(
        (project / "06_build/verification/connector_assembly_contract.json").read_text())
    eq(disk, first, "CLI and API N-A receipt")

    forged = copy.deepcopy(first)
    forged["status"] = "PASS"
    valid, findings = validate_receipt(forged, project)
    check(not valid and any("status" in finding for finding in findings),
          f"consumer accepted forged N-A status: {findings}")


@test("zero-connector N-A cannot self-assert or use untyped evidence",
      kind="known_bad")
def t_no_operated_connectors_evidence_required():
    silent = no_operated_contract()
    del silent["applicability"]
    silent["evidence_sources"] = []
    result = must_fail(
        invoke(fixture(silent)), "silent zero connector denominator",
        expect="expected non-empty list")
    eq(result.rc, 1, "silent zero denominator exit")

    unknown = no_operated_contract()
    unknown["applicability"]["evidence"] = {
        "grade": "unknown", "source_ids": [],
        "rationale": "No connector census has been performed.",
    }
    result = must_fail(
        invoke(fixture(unknown)), "unknown N-A applicability",
        expect="operated=false requires exact evidence")
    eq(result.rc, 1, "unknown N-A exit")

    no_source = no_operated_contract()
    no_source["applicability"]["evidence"]["source_ids"] = []
    result = must_fail(
        invoke(fixture(no_source)), "source-free N-A applicability",
        expect="exact evidence requires source_ids")
    eq(result.rc, 1, "source-free N-A exit")

    wrong_kind = no_operated_contract()
    wrong_kind["evidence_sources"][0]["kind"] = "manufacturer-drawing"
    result = must_fail(
        invoke(fixture(wrong_kind)), "untyped N-A applicability source",
        expect="not an allowed connector applicability artifact")
    eq(result.rc, 1, "untyped N-A source exit")

    no_rationale = no_operated_contract()
    no_rationale["applicability"]["evidence"]["rationale"] = ""
    result = must_fail(
        invoke(fixture(no_rationale)), "rationale-free N-A applicability",
        expect="expected non-empty string")
    eq(result.rc, 1, "rationale-free N-A exit")

    extra_field = no_operated_contract()
    extra_field["applicability"]["geometry_pass"] = True
    result = must_fail(
        invoke(fixture(extra_field)), "N-A applicability schema extension",
        expect="exact schema violation")
    eq(result.rc, 1, "N-A schema extension exit")


@test("N-A requires empty populations and current evidence bytes",
      kind="known_bad")
def t_no_operated_connectors_population_and_freshness():
    populated = no_operated_contract()
    normal = good_contract()
    populated["evidence_sources"].extend(normal["evidence_sources"])
    populated["assemblies"] = normal["assemblies"]
    populated["simultaneous_groups"] = normal["simultaneous_groups"]
    result = must_fail(
        invoke(fixture(populated)), "populated N-A contract",
        expect="requires empty assemblies and simultaneous_groups")
    eq(result.rc, 1, "populated N-A exit")

    missing = no_operated_contract()
    missing["evidence_sources"][0]["path"] = \
        "02_parts/fixture/missing-applicability.yaml"
    result = must_fail(
        invoke(fixture(missing)), "missing N-A evidence",
        expect="path does not exist")
    eq(result.rc, 1, "missing N-A evidence exit")

    project = fixture(no_operated_contract())
    receipt = load_and_compile(project)
    (project / "02_parts/fixture/applicability.yaml").write_text(
        "operated_connector_refs: [J1]\nreviewed_scope: changed\n")
    valid, findings = validate_receipt(receipt, project)
    check(not valid and any("stale" in finding for finding in findings),
          f"stale N-A evidence validated: {findings}")


@test("represented unknown evidence returns INCOMPLETE rather than schema FAIL",
      kind="known_bad")
def t_unknown_exit_two():
    value = good_contract()
    value["assemblies"][0]["cable"]["evidence"] = {
        "grade": "unknown", "source_ids": [],
        "rationale": "The selected cable is still owed.",
    }
    project = fixture(value)
    result = must_fail(invoke(project), "unknown cable")
    eq(result.rc, 2, "represented unknown exit")
    contains(result.out, "unknown=1", "unknown denominator")
    receipt = json.loads((project / "06_build/verification/connector_assembly_contract.json").read_text())
    eq(receipt["status"], "INCOMPLETE", "unknown receipt status")


@test("fabricated Pluto v5 canary covers all connectors and keeps SMA service incomplete",
      kind="known_bad")
def t_pluto_v5_canary():
    receipt = load_and_compile(PLUTO_V5)
    eq(receipt["status"], "INCOMPLETE", "Pluto connector readiness")
    eq(receipt["summary"]["assembly_count"], 4, "Pluto assembly profiles")
    eq(receipt["summary"]["instance_count"], 12, "Pluto connector refs")
    eq(receipt["summary"]["evidence_total"], 50, "Pluto evidence denominator")
    eq(receipt["summary"]["evidence_unknown"], 48, "Pluto unknown denominator")
    group = next(row for row in receipt["simultaneous_groups"]
                 if row["id"] == "all-sma-service")
    eq(group["id"], "all-sma-service", "Pluto simultaneous group")
    eq(len(group["members"]), 9, "Pluto populated group members")
    eq(group["serviceable_member_refs"], group["members"],
       "every Pluto SMA must remain serviceable")
    profile = next(row for row in receipt["assemblies"]
                   if row["id"] == "amphenol-901-143-6rfx-v5-bank")
    for section in ("mate", "grip", "tool", "torque", "reaction", "cable"):
        eq(profile[section]["evidence"]["grade"], "unknown",
           f"Pluto {section} evidence")

    canary_output = Path(
        "06_build/verification/t1_connector_assembly_contract.json")
    result = must_fail(invoke(
        PLUTO_V5, "--output", canary_output.as_posix(),
    ), "Pluto incomplete real-project canary")
    (PLUTO_V5 / canary_output).unlink(missing_ok=True)
    eq(result.rc, 2, "Pluto compiler exit")
    contains(result.out, "assemblies=4 instances=12", "Pluto CLI census")
    contains(result.out, "coverage=2/50", "Pluto evidence denominator")
    contains(result.out, "unknown=48", "Pluto CLI unknowns")


@test("unknown schema fields and duplicate YAML keys fail at exit 1",
      kind="known_bad")
def t_strict_schema_rejects():
    value = good_contract()
    value["assemblies"][0]["tool"]["finger_clearance_mm"] = 99
    project = fixture(value)
    result = must_fail(invoke(project), "unknown schema field", expect="exact schema violation")
    eq(result.rc, 1, "schema failure exit")

    contract = project / DEFAULT_CONTRACT
    text = yaml.safe_dump(good_contract(), sort_keys=False)
    contract.write_text("schema: 1\n" + text)
    result = must_fail(invoke(project), "duplicate YAML key", expect="duplicate YAML key")
    eq(result.rc, 1, "duplicate key exit")


@test("missing, symlinked, and unreferenced evidence cannot become authority",
      kind="known_bad")
def t_evidence_files_fail_closed():
    missing = good_contract()
    missing["evidence_sources"][0]["path"] = "02_parts/fixture/absent.txt"
    result = must_fail(invoke(fixture(missing)), "missing evidence", expect="path does not exist")
    eq(result.rc, 1, "missing evidence exit")

    project = fixture()
    source = project / "02_parts/fixture/evidence.txt"
    actual = project / "02_parts/fixture/actual.txt"
    source.rename(actual)
    source.symlink_to(actual.name)
    result = must_fail(invoke(project), "symlink evidence", expect="symlink path component")
    eq(result.rc, 1, "symlink evidence exit")

    project = fixture()
    source = project / "02_parts/fixture/evidence.txt"
    actual = project / "02_parts/fixture/actual.txt"
    source.rename(actual)
    os.link(actual, source)
    result = must_fail(invoke(project), "hard-linked evidence",
                       expect="hard-linked files are not accepted")
    eq(result.rc, 1, "hard-linked evidence exit")

    unused = good_contract()
    unused["evidence_sources"].append({
        "id": "unused-file", "kind": "physical-test",
        "path": "02_parts/fixture/evidence.txt",
    })
    result = must_fail(invoke(fixture(unused)), "unused evidence", expect="unreferenced sources")
    eq(result.rc, 1, "unused evidence exit")


@test("receipt output cannot replace contract or evidence inputs",
      kind="known_bad")
def t_output_alias_rejected():
    project = fixture()
    contract = project / DEFAULT_CONTRACT
    before = contract.read_bytes()
    result = must_fail(invoke(
        project, "--output", DEFAULT_CONTRACT.as_posix()),
        "contract output alias", expect="destination aliases")
    eq(result.rc, 1, "output alias exit")
    eq(contract.read_bytes(), before, "contract survives output alias refusal")


@test("simultaneous group and instance claims must agree bidirectionally",
      kind="known_bad")
def t_group_mismatch_rejected():
    value = good_contract()
    value["simultaneous_groups"][0]["members"] = ["J1"]
    value["simultaneous_groups"][0]["serviceable_member_refs"] = ["J1"]
    result = must_fail(invoke(fixture(value)), "shrunk simultaneous group",
                       expect="member list and instance claims differ")
    eq(result.rc, 1, "group mismatch exit")


@test("evidence-byte drift invalidates an otherwise identical receipt",
      kind="known_bad")
def t_receipt_staleness():
    project = fixture()
    receipt = load_and_compile(project)
    semantic_before = receipt["semantic_sha256"]
    (project / "02_parts/fixture/evidence.txt").write_text("fixture drawing revision B\n")
    current = load_and_compile(project)
    eq(current["semantic_sha256"], semantic_before,
       "logical contract changed when only evidence bytes changed")
    check(current["subject_sha256"] != receipt["subject_sha256"],
          "evidence mutation retained subject identity")
    valid, findings = validate_receipt(receipt, project)
    check(not valid, "stale receipt validated")
    check(any("stale" in finding for finding in findings),
          f"stale input diagnosis absent: {findings}")


@test("known torque cannot omit range or reaction path", kind="known_bad")
def t_torque_and_reaction_are_required():
    value = good_contract()
    value["assemblies"][0]["torque"]["maximum_nm"] = None
    result = must_fail(invoke(fixture(value)), "missing torque maximum",
                       expect="unknown fields")
    eq(result.rc, 1, "missing torque exit")

    value = good_contract()
    value["assemblies"][0]["reaction"]["method"] = "none"
    result = must_fail(invoke(fixture(value)), "missing reaction method",
                       expect="requires a known reaction method")
    eq(result.rc, 1, "missing reaction exit")


@test("tolerance effects are mandatory, closed, and cover exposure setback",
      kind="known_bad")
def t_tolerance_effect_contract():
    missing = good_contract()
    del missing["assemblies"][0]["tolerances"][0]["effect"]
    result = must_fail(invoke(fixture(missing)), "missing tolerance effect",
                       expect="exact schema violation")
    eq(result.rc, 1, "missing tolerance effect exit")

    invalid = good_contract()
    invalid["assemblies"][0]["tolerances"][0]["effect"] = "toolish_margin"
    result = must_fail(invoke(fixture(invalid)), "unknown tolerance effect",
                       expect="expected one of")
    eq(result.rc, 1, "unknown tolerance effect exit")

    no_exposure = good_contract()
    no_exposure["assemblies"][0]["tolerances"][0]["effect"] = "other"
    result = must_fail(invoke(fixture(no_exposure)), "missing exposure stack",
                       expect="at least one exposure_setback row")
    eq(result.rc, 1, "missing exposure stack exit")

    understated = good_contract()
    understated["assemblies"][0]["interface"]["exposure_setback_allowance_mm"] = 0.1
    result = must_fail(invoke(fixture(understated)), "understated setback stack",
                       expect="below the explicit tolerance stack")
    eq(result.rc, 1, "understated setback exit")


@test("unknown tolerance bounds retain their effect and return INCOMPLETE",
      kind="known_bad")
def t_unknown_tolerance_effect_is_not_zero():
    value = good_contract()
    row = value["assemblies"][0]["tolerances"][0]
    row.update({
        "effect": "exposure_setback",
        "minus_mm": None,
        "plus_mm": None,
        "evidence": {
            "grade": "unknown", "source_ids": [],
            "rationale": "PCB edge and installed seating stack are owed.",
        },
    })
    project = fixture(value)
    result = must_fail(invoke(project), "unknown exposure tolerance")
    eq(result.rc, 2, "unknown tolerance exit")
    receipt = json.loads(
        (project / "06_build/verification/connector_assembly_contract.json").read_text())
    compiled = receipt["assemblies"][0]["tolerances"][0]
    eq(compiled["effect"], "exposure_setback", "preserved tolerance effect")
    check(compiled["minus_mm"] is None and compiled["plus_mm"] is None,
          "unknown tolerance was coerced to zero")


@test("model and realized-orientation authority use closed artifact kinds",
      kind="known_bad")
def t_typed_model_and_orientation_sources():
    drawing_as_model = good_contract()
    receptacle = drawing_as_model["assemblies"][0]["receptacle"]
    receptacle["body_envelope_mm"] = None
    receptacle["model_source_id"] = "fixture-drawing"
    result = must_fail(
        invoke(fixture(drawing_as_model)), "drawing laundered as 3D model",
        expect="not an allowed 3D/model artifact")
    eq(result.rc, 1, "drawing-as-model exit")

    actual_model = good_contract()
    actual_model["evidence_sources"].append({
        "id": "fixture-model", "kind": "manufacturer-3d-model",
        "path": "02_parts/fixture/model.step",
    })
    receptacle = actual_model["assemblies"][0]["receptacle"]
    receptacle["body_envelope_mm"] = None
    receptacle["model_source_id"] = "fixture-model"
    receptacle["evidence"]["source_ids"].append("fixture-model")
    receipt = load_and_compile(fixture(actual_model))
    eq(receipt["status"], "PASS", "typed model artifact admission")

    drawing_as_orientation = good_contract()
    drawing_as_orientation["evidence_sources"][1]["kind"] = "manufacturer-drawing"
    result = must_fail(
        invoke(fixture(drawing_as_orientation)),
        "drawing laundered as realized orientation",
        expect="not an allowed realized orientation/placement artifact")
    eq(result.rc, 1, "drawing-as-orientation exit")

    missing_orientation = good_contract()
    missing_orientation["evidence_sources"] = [
        missing_orientation["evidence_sources"][0]]
    interface = missing_orientation["assemblies"][0]["interface"]
    interface["orientation_source_id"] = None
    interface["evidence"] = evidence()
    result = must_fail(
        invoke(fixture(missing_orientation)), "known interface without axis authority",
        expect="known interface requires orientation_source_id")
    eq(result.rc, 1, "missing orientation authority exit")

    unknown_orientation = copy.deepcopy(missing_orientation)
    unknown_orientation["assemblies"][0]["interface"]["evidence"] = evidence("unknown")
    receipt = load_and_compile(fixture(unknown_orientation))
    eq(receipt["status"], "INCOMPLETE", "candidate axis with unknown authority")
    eq(receipt["assemblies"][0]["instances"][0]["mating_axis_board"],
       [0.0, -1.0, 0.0], "candidate axis retained without promotion")


@test("threaded and torque-required fastening bind tool and reaction",
      kind="known_bad")
def t_fastening_cross_section_constraints():
    no_tool = good_contract()
    no_tool["assemblies"][0]["tool"]["kind"] = "none"
    result = must_fail(
        invoke(fixture(no_tool)), "threaded fastening without tool",
        expect="requires a known non-none tool")
    eq(result.rc, 1, "no-tool fastening exit")

    no_reaction = good_contract()
    no_reaction["assemblies"][0]["reaction"]["method"] = "unknown"
    result = must_fail(
        invoke(fixture(no_reaction)), "torque without reaction",
        expect="requires a known reaction method")
    eq(result.rc, 1, "no-reaction fastening exit")

    represented_unknown = good_contract()
    represented_unknown["assemblies"][0]["reaction"] = {
        "method": None, "load_path": None,
        "evidence": {
            "grade": "unknown", "source_ids": [],
            "rationale": "Selected reaction fixture remains owed.",
        },
    }
    project = fixture(represented_unknown)
    result = must_fail(invoke(project), "represented unknown reaction")
    eq(result.rc, 2, "unknown reaction remains incomplete")


@test("operation graph is linear, non-vacuous, and proves populated service",
      kind="known_bad")
def t_executable_operation_graph():
    no_required = good_contract()
    no_required["assemblies"][0]["operations"][0]["required"] = False
    result = must_fail(
        invoke(fixture(no_required)), "vacuous known operation graph",
        expect="has no required operation")
    eq(result.rc, 1, "vacuous operations exit")

    neighbors_absent = good_contract()
    operation = neighbors_absent["assemblies"][0]["operations"][0]
    operation["with_neighbors_populated"] = False
    result = must_fail(
        invoke(fixture(neighbors_absent)), "unpopulated-only service operation",
        expect="no required operation with with_neighbors_populated=true")
    eq(result.rc, 1, "simultaneous-state coverage exit")

    sequence_gap = good_contract()
    second = copy.deepcopy(sequence_gap["assemblies"][0]["operations"][0])
    second.update({
        "id": "remove", "sequence": 3,
        "start_state": "plug-torqued", "end_state": "plug-removed",
    })
    sequence_gap["assemblies"][0]["operations"].append(second)
    result = must_fail(
        invoke(fixture(sequence_gap)), "operation sequence gap",
        expect="sequence must be contiguous from 1")
    eq(result.rc, 1, "sequence gap exit")

    broken_state = good_contract()
    second = copy.deepcopy(broken_state["assemblies"][0]["operations"][0])
    second.update({
        "id": "remove", "sequence": 2,
        "start_state": "different-state", "end_state": "plug-removed",
    })
    broken_state["assemblies"][0]["operations"].append(second)
    result = must_fail(
        invoke(fixture(broken_state)), "operation state discontinuity",
        expect="state discontinuity")
    eq(result.rc, 1, "state discontinuity exit")


@test("governing receipt validation refuses receipt-selected alternate authority",
      kind="known_bad")
def t_validate_receipt_requires_expected_contract():
    project = fixture()
    alternate = project / "03_src/rules/alternate_connector_assemblies.yaml"
    alternate.write_text((project / DEFAULT_CONTRACT).read_text())
    receipt = load_and_compile(
        project, "03_src/rules/alternate_connector_assemblies.yaml")
    valid, findings = validate_receipt(receipt, project)
    check(not valid, "alternate self-selected contract became governing authority")
    check(any("does not match expected" in finding for finding in findings),
          f"alternate authority diagnosis absent: {findings}")
    check(validate_receipt(
        receipt, project,
        expected_contract_path="03_src/rules/alternate_connector_assemblies.yaml",
    ) == (True, []), "explicit non-governing alternate did not regrade")


@test("receipt publication holds its directory and protects compiler input",
      kind="known_bad")
def t_dirfd_publication_and_compiler_alias():
    project = fixture()
    receipt = load_and_compile(project)
    compiler_before = COMPILER.read_bytes()
    try:
        contract_module._write_receipt(
            ROOT, COMPILER.relative_to(ROOT), receipt)
    except ContractError as exc:
        contains(str(exc), "compiler input", "compiler output alias diagnosis")
    else:
        raise AssertionError("compiler output alias was accepted")
    eq(COMPILER.read_bytes(), compiler_before, "compiler survives output alias refusal")

    output_parent = project / DEFAULT_OUTPUT.parent
    attacker = project / "attacker-output"
    displaced = project / "06_build/verification-held"
    attacker.mkdir()
    original_replace = contract_module.os.replace
    observed: dict[str, object] = {}

    def swap_parent_then_replace(source, destination, *, src_dir_fd=None,
                                 dst_dir_fd=None):
        observed.update({
            "source": source, "destination": destination,
            "src_dir_fd": src_dir_fd, "dst_dir_fd": dst_dir_fd,
        })
        output_parent.rename(displaced)
        output_parent.symlink_to(attacker, target_is_directory=True)
        return original_replace(
            source, destination, src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd)

    contract_module.os.replace = swap_parent_then_replace
    try:
        contract_module._write_receipt(project, DEFAULT_OUTPUT, receipt)
    finally:
        contract_module.os.replace = original_replace
    check(observed.get("src_dir_fd") is not None and
          observed.get("src_dir_fd") == observed.get("dst_dir_fd"),
          f"publication was not same-dirfd relative: {observed}")
    check("/" not in str(observed.get("source")) and
          "/" not in str(observed.get("destination")),
          f"publication used pathnames: {observed}")
    check(not (attacker / DEFAULT_OUTPUT.name).exists(),
          "parent swap redirected receipt into attacker directory")
    check((displaced / DEFAULT_OUTPUT.name).is_file(),
          "held original directory did not receive receipt")


@test("mid-publication semantic and evidence drift refuse success and remove output",
      kind="known_bad")
def t_mid_publication_input_drift():
    def invoke_with_mutation(project: Path, mutate) -> tuple[int, str, str]:
        original_replace = contract_module.os.replace

        def replace_then_mutate(source, destination, *, src_dir_fd=None,
                                dst_dir_fd=None):
            result = original_replace(
                source, destination, src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd)
            mutate(project)
            return result

        contract_module.os.replace = replace_then_mutate
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = contract_module.main(["--project", str(project)])
        finally:
            contract_module.os.replace = original_replace
        return rc, stdout.getvalue(), stderr.getvalue()

    semantic_project = fixture()

    def make_pass_incomplete(project: Path) -> None:
        path = project / DEFAULT_CONTRACT
        value = yaml.safe_load(path.read_text())
        value["assemblies"][0]["cable"]["evidence"] = evidence("unknown", [])
        path.write_text(yaml.safe_dump(
            value, sort_keys=False, allow_unicode=True))

    rc, stdout, stderr = invoke_with_mutation(
        semantic_project, make_pass_incomplete)
    eq(rc, 1, "PASS-to-INCOMPLETE publication drift exit")
    contains(stderr, "inputs changed during receipt publication",
             "PASS-to-INCOMPLETE publication diagnosis")
    check("CONNECTOR-CONTRACT PASS" not in stdout,
          "semantic drift reported CLI success")
    check(not (semantic_project / DEFAULT_OUTPUT).exists(),
          "semantic drift left the stale published receipt")

    evidence_project = fixture()

    def drift_evidence(project: Path) -> None:
        (project / "02_parts/fixture/evidence.txt").write_text(
            "fixture drawing revision B\n")

    rc, stdout, stderr = invoke_with_mutation(evidence_project, drift_evidence)
    eq(rc, 1, "evidence-byte publication drift exit")
    contains(stderr, "inputs changed during receipt publication",
             "evidence-byte publication diagnosis")
    check("CONNECTOR-CONTRACT PASS" not in stdout,
          "evidence drift reported CLI success")
    check(not (evidence_project / DEFAULT_OUTPUT).exists(),
          "evidence drift left the stale published receipt")


if __name__ == "__main__":
    sys.exit(main())
