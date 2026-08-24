#!/usr/bin/env python3
"""T1: progressive-disclosure router and single-authority compatibility gate."""
from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

SCRIPTS = ROOT / "skills/pcb-design/scripts"
FIXTURES = ROOT / "tests/fixtures/skill_router"
AUTH = SCRIPTS / "skill_authority_check.py"
ROUTER = SCRIPTS / "skill_reference_router.py"
sys.path.insert(0, str(SCRIPTS))

from skill_authority_check import audit  # noqa: E402
from skill_reference_router import (  # noqa: E402
    CapabilityProfile,
    RouterValidationError,
    load_catalog,
    resolve_profile,
)


EXPECTED = {
    "simple": (
        "PCB-COMMISSION", "PCB-ARCHITECTURE", "PCB-SOURCING",
        "KICAD-SCHEMATIC", "KICAD-PLACEMENT", "KICAD-ROUTING",
        "KICAD-LAYOUT-SEAL",
    ),
    "usb_hub_v4": (
        "PCB-COMMISSION", "PCB-ARCHITECTURE", "PCB-SOURCING",
        "KICAD-SCHEMATIC", "KICAD-PLACEMENT", "KICAD-ROUTING",
        "KICAD-LAYOUT-SEAL", "JLC-FABRICATION", "JLC-ASSEMBLY-VERIFY",
        "PCB-RELEASE-REVIEW", "PCB-RELEASE-SEAL",
    ),
    "pi_usb": (
        "PCB-COMMISSION", "PCB-ARCHITECTURE", "PCB-SOURCING",
        "KICAD-SCHEMATIC", "KICAD-PLACEMENT", "KICAD-ROUTING",
        "KICAD-LAYOUT-SEAL", "JLC-FABRICATION", "JLC-ASSEMBLY-VERIFY",
        "PCB-RELEASE-REVIEW", "PCB-RELEASE-SEAL",
    ),
    "pluto_v5": (
        "PCB-COMMISSION", "PCB-ARCHITECTURE", "PCB-SOURCING",
        "KICAD-RF-CONTEXT", "KICAD-RF-SOURCE", "KICAD-SCHEMATIC",
        "KICAD-PLACEMENT", "KICAD-ROUTING", "KICAD-RF-REALIZED",
        "KICAD-LAYOUT-SEAL", "JLC-FABRICATION", "JLC-ASSEMBLY-VERIFY",
        "JLC-RF-FAB-REVIEW", "PCB-RELEASE-REVIEW", "PCB-RELEASE-SEAL",
    ),
}


def profile(name: str) -> CapabilityProfile:
    return CapabilityProfile.from_mapping(
        json.loads((FIXTURES / f"{name}.json").read_text()))


@test("the real skill authority gate passes with the frozen legacy denominator")
def t_real_authority_gate():
    result = must_pass(run([KPY, AUTH]), "real skill authority gate")
    contains(result.out, "policies=111/109", "legacy policy denominator plus connector gates")
    contains(result.out, "core=", "reported core progressive-disclosure budget")
    contains(result.out, " lines/", "reported core line/word denominator")


@test("the four compatibility profiles resolve the exact normalized stage traces")
def t_profile_traces():
    for name, expected in EXPECTED.items():
        result = resolve_profile(profile(name))
        actual = tuple(row["spec"]["id"] for row in result["stages"])
        eq(actual, expected, f"{name} stage trace")
        check(not result["firmware_handoff_required"],
              f"{name} unexpectedly requested firmware")
        check(all("FIRMWARE" not in stage_id for stage_id in actual),
              f"{name} contains a firmware stage")


@test("ordinary, high-speed digital, and RF select distinct reference modules")
def t_signal_integrity_progressive_disclosure():
    for name in ("simple", "usb_hub_v4"):
        refs = resolve_profile(profile(name))["references"]
        check(not any("/rf" in ref for ref in refs),
              f"{name} loaded RF references: {refs}")
        check(not any(ref.endswith("signal-integrity.md") for ref in refs),
              f"{name} loaded high-speed references: {refs}")

    pi_refs = resolve_profile(profile("pi_usb"))["references"]
    check(any(ref.endswith("signal-integrity.md") for ref in pi_refs),
          f"Pi high-speed adapter absent: {pi_refs}")
    check(not any("/rf" in ref for ref in pi_refs),
          f"RF leaked into Pi high-speed plan: {pi_refs}")

    pluto_refs = resolve_profile(profile("pluto_v5"))["references"]
    check(any("/rf/" in ref for ref in pluto_refs),
          f"Pluto RF module absent: {pluto_refs}")
    check(not any(ref.endswith("signal-integrity.md") for ref in pluto_refs),
          f"generic digital SI duplicated Pluto RF authority: {pluto_refs}")


@test("stage-local disclosure for Pi routing loads no JLC, RF, or release procedure")
def t_stage_local_disclosure():
    result = resolve_profile(profile("pi_usb"), at_stage="KICAD-ROUTING")
    refs = result["load_now"]
    check(any(ref.endswith("routing-pipeline.md") for ref in refs),
          f"routing procedure absent: {refs}")
    check(any(ref.endswith("source-to-prep-authority.md") for ref in refs),
          f"source authority absent: {refs}")
    check(any(ref.endswith("route-candidate-contract.md") for ref in refs),
          f"candidate transaction authority absent: {refs}")
    check(any(ref.endswith("route-exploration.md") for ref in refs),
          f"route exploration authority absent: {refs}")
    check(any(ref.endswith("signal-integrity.md") for ref in refs),
          f"high-speed digital adapter absent: {refs}")
    check(not any("jlcpcb-fab" in ref for ref in refs),
          f"JLC leaked into routing stage: {refs}")
    check(not any("/rf" in ref for ref in refs),
          f"RF leaked into Pi routing stage: {refs}")
    check(not any(ref.endswith("review-and-publication.md") for ref in refs),
          f"release procedure leaked into routing stage: {refs}")


@test("placement discloses source-to-prep authority without routing mechanics")
def t_placement_local_disclosure():
    refs = resolve_profile(profile("pi_usb"), at_stage="KICAD-PLACEMENT")["load_now"]
    check(any(ref.endswith("source-to-prep-authority.md") for ref in refs),
          f"placement source authority absent: {refs}")
    check(not any(ref.endswith("route-candidate-contract.md") for ref in refs),
          f"candidate mechanics leaked into placement: {refs}")
    check(not any(ref.endswith("route-exploration.md") for ref in refs),
          f"exploration mechanics leaked into placement: {refs}")
    check(any(ref.endswith("signal-integrity.md") for ref in refs),
          f"high-speed placement guidance absent: {refs}")
    check(not any("/rf/" in ref for ref in refs),
          f"RF guidance leaked into digital placement: {refs}")


@test("digital fabrication and first article disclose SI without RF stages")
def t_high_speed_fabrication_disclosure():
    fab = resolve_profile(
        profile("pi_usb"), at_stage="JLC-FABRICATION")["load_now"]
    check(any(ref.endswith("signal-integrity.md") for ref in fab),
          f"digital fabrication guidance absent: {fab}")
    check(not any("/rf/" in ref for ref in fab),
          f"RF guidance leaked into digital fabrication: {fab}")

    item = profile("pi_usb").to_mapping()
    item["target"] = "first_article"
    first = resolve_profile(
        CapabilityProfile.from_mapping(item),
        at_stage="PCB-FIRST-ARTICLE")["load_now"]
    check(any(ref.endswith("signal-integrity.md") for ref in first),
          f"digital first-article guidance absent: {first}")
    check(not any("/rf/" in ref for ref in first),
          f"RF guidance leaked into digital first article: {first}")


@test("router labels disclosure selection without fabricating N-A evidence")
def t_selection_is_not_engineering_applicability():
    result = resolve_profile(profile("pi_usb"))
    eq(result["authority"], "DISCLOSURE_ONLY", "router authority boundary")
    check(all(row["selection_reason"] for row in result["stages"]),
          "stage selection reasons missing")
    placeholders = result["dependency_placeholders"]
    eq(placeholders["rf_source_clearance"]["stage_id"], "KICAD-RF-SOURCE",
       "RF source placeholder producer")
    eq(placeholders["rf_realized_clearance"]["stage_id"], "KICAD-RF-REALIZED",
       "RF realized placeholder producer")
    check(all(row["authority"] == "DISCLOSURE_ONLY" and
              row["engineering_applicability"] == "UNKNOWN"
              for row in placeholders.values()),
          "a planning placeholder claimed engineering applicability")
    eq(result["external_clearances"], [],
       "planning placeholders were mislabeled external evidence")


@test("router accepts the frozen applies spelling only as a disclosure alias")
def t_legacy_applies_catalog_adapter():
    catalog = copy.deepcopy(load_catalog())
    for row in catalog["stages"]:
        row["applies"] = row.pop("selects")
    current = resolve_profile(profile("pi_usb"))
    adapted = resolve_profile(profile("pi_usb"), catalog=catalog)
    eq(adapted["stages"], current["stages"], "legacy catalog stage adapter")
    eq(adapted["authority"], "DISCLOSURE_ONLY",
       "legacy selector spelling gained execution authority")


@test("runtime documentation does not overclaim hermetic containment")
def t_runtime_truth_boundary():
    text = (ROOT / "skills/pcb-design/references/execution-runtime.md").read_text()
    contains(text, "bounded, not hermetic", "bounded-versus-hermetic truth")
    contains(text, "actually enforces it", "network enforcement truth")
    contains(text, "cannot update a live board", "runtime authority boundary")


@test("an explicit firmware request creates only a handoff, never a PCB stage")
def t_firmware_is_separate():
    item = profile("simple").to_mapping()
    item["firmware"] = "requested"
    result = resolve_profile(CapabilityProfile.from_mapping(item))
    check(result["firmware_handoff_required"], "firmware handoff was not exposed")
    check(all("FIRMWARE" not in row["spec"]["id"] for row in result["stages"]),
          "firmware request inserted a PCB pipeline stage")


@test("a release without a registered assembly adapter fails closed",
      kind="known_bad")
def t_unowned_manufacturer_rejected():
    item = profile("usb_hub_v4").to_mapping()
    item["assembly"] = "other"
    try:
        CapabilityProfile.from_mapping(item)
    except RouterValidationError as exc:
        contains(str(exc), "registered jlcpcb assembly path",
                 "closed manufacturer-adapter error")
    else:
        raise AssertionError("unowned manufacturer path was accepted")


@test("the authority gate catches duplicate policy ownership",
      kind="known_bad")
def t_duplicate_authority_rejected():
    catalog = copy.deepcopy(load_catalog())
    twin = next(domain for domain in catalog["domains"]
                if domain["id"] == "jlc_twin")
    twin["policy_ids"] = sorted(twin["policy_ids"] + ["A-ROT"])
    directory = tmpdir("skill_auth_")
    altered = directory / "authority.json"
    altered.write_text(json.dumps(catalog, sort_keys=True, indent=2))
    findings, _ = audit(ROOT, catalog_path=altered, check_git_baseline=False)
    text = "\n".join(findings)
    contains(text, "duplicate authority", "duplicate policy gate")
    contains(text, "A-ROT", "duplicate policy identity")


@test("the authority gate is lexical and cannot detect inverted policy prose",
      kind="vacuity", gate="skill_authority_check.py")
def t_authority_lexical_vacuity():
    directory = tmpdir("skill_auth_vacuity_")
    for skill in ("pcb-design", "pcb-enclosure", "kicad-pcb", "jlcpcb-fab"):
        shutil.copytree(ROOT / "skills" / skill,
                        directory / "skills" / skill)
    (directory / "tests").mkdir()
    shutil.copy2(ROOT / "tests/run_tests.sh",
                 directory / "tests/run_tests.sh")

    commission = (directory / "skills/pcb-design/references/"
                  "commission-and-scope.md")
    text = commission.read_text()
    before = "Only a user statement may relax a"
    after = "Any source may relax a"
    check(before in text, "vacuity fixture mutation target exists")
    commission.write_text(text.replace(before, after, 1))

    result = must_pass(run([
        KPY, AUTH, "--root", directory, "--skip-git-baseline",
    ]), "lexical authority check over semantically inverted procedure")
    contains(result.out, "SKILL-AUTH PASS", "lexical vacuity verdict")


@test("the CLI emits a typed plan with no board or project present",
      kind="vacuity", gate="skill_reference_router.py")
def t_cli():
    result = must_pass(run([
        KPY, ROUTER, "--profile", FIXTURES / "pluto_v5.json",
        "--at-stage", "KICAD-RF-REALIZED", "--json",
    ]), "router CLI")
    value = json.loads(result.out)
    eq(value["target_stage"], "PCB-RELEASE-SEAL", "CLI target")
    check(any(ref.endswith("rf/rf-context.md") for ref in value["load_now"]),
          f"RF stage-local reference missing: {value['load_now']}")


if __name__ == "__main__":
    sys.exit(main())
