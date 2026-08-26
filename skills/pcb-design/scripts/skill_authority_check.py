#!/usr/bin/env python3
"""Audit progressive-disclosure budgets, authority, reachability, and traces.

VACUITY: policy reachability is lexical. The audit passes when every frozen ID
appears in its single owning reference, even if surrounding prose reverses the
policy's meaning. Executable gate tests and board canaries remain independent
semantic authorities. Fixtured by
``t1_skill_progressive_disclosure.py::t_authority_lexical_vacuity``.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

from skill_reference_router import (  # noqa: E402
    CATALOG_PATH,
    CapabilityProfile,
    RouterValidationError,
    _domain_index,
    load_catalog,
    resolve_profile,
)


POLICY_PATTERN = (
    r"(?<![A-Z0-9-])(?:"
    r"(?:A|D|E|F|G|GG|M|P|PF|PR|Q|R|RF|S|TSX)-"
    r"[A-Z0-9]+(?:-[A-Z0-9]+)*"
    r"|MODEL-(?:REG|SELF)|NO-BODY|PAD-(?:GEOM|MISMATCH)"
    r"|POLARITY-(?:CHECK|FIT)|ROT-DB-SUGGEST)"
    r"(?![A-Z0-9-])"
)
POLICY_RE = re.compile(POLICY_PATTERN)
POLICY_ID_RE = re.compile(r"^(?:" + POLICY_PATTERN + r")$")
OWNER_PREFIX = {
    "pcb-design": "skills/pcb-design/",
    "pcb-enclosure": "skills/pcb-enclosure/",
    "kicad-pcb": "skills/kicad-pcb/",
    "jlcpcb-fab": "skills/jlcpcb-fab/",
}
BASELINE_SKILLS = (
    "skills/pcb-design/SKILL.md",
    "skills/kicad-pcb/SKILL.md",
    "skills/jlcpcb-fab/SKILL.md",
)
CURRENT_SKILLS = BASELINE_SKILLS + ("skills/pcb-enclosure/SKILL.md",)
ALLOWED_CORE_SCRIPTS = frozenset({
    "commission_project.py", "pcb_publication_gate.py",
    "skill_authority_check.py", "skill_reference_router.py",
    "t1_pcb_documentation.py", "t1_skill_progressive_disclosure.py",
})
STALE_AUTHORITY_PHRASES = (
    "A-ROT gate itself is HELD",
    "A-ROT is HELD",
    "canon A-ROT is HELD",
)


def _words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _route_from_core(reference: str) -> str:
    path = Path(reference)
    skill_root = Path("skills/pcb-design")
    if path.is_relative_to(skill_root):
        return path.relative_to(skill_root).as_posix()
    if path.is_relative_to(Path("skills")):
        return (Path("..") / path.relative_to(Path("skills"))).as_posix()
    return reference


def _frontmatter_fields(text: str, where: str) -> tuple[set[str], str | None]:
    if not text.startswith("---\n"):
        return set(), f"{where}: missing YAML frontmatter"
    parts = text.split("---", 2)
    if len(parts) != 3:
        return set(), f"{where}: unterminated YAML frontmatter"
    fields = set()
    for line in parts[1].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            return fields, f"{where}: malformed frontmatter line {line!r}"
        fields.add(line.split(":", 1)[0].strip())
    return fields, None


def _git_baseline_policy_ids(root: Path, commit: str) -> tuple[set[str], str | None]:
    result: set[str] = set()
    for path in BASELINE_SKILLS:
        proc = subprocess.run(
            ["git", "show", f"{commit}:{path}"], cwd=root,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode:
            return set(), (f"baseline git show failed for {path}: "
                           f"{proc.stderr.strip()}")
        result.update(POLICY_RE.findall(proc.stdout))
    return result, None


def _fixture_profiles() -> dict[str, CapabilityProfile]:
    return {
        "simple": CapabilityProfile(
            signal_integrity="ordinary", assembly="none",
            firmware="forbidden", foreign_mating=False, target="design"),
        "usb_hub_v4": CapabilityProfile(
            signal_integrity="ordinary", assembly="jlcpcb",
            firmware="forbidden", foreign_mating=False, target="release"),
        "pi_usb": CapabilityProfile(
            signal_integrity="high_speed_digital", assembly="jlcpcb",
            firmware="forbidden", foreign_mating=False, target="release"),
        "pluto_v5": CapabilityProfile(
            signal_integrity="rf", assembly="jlcpcb",
            firmware="forbidden", foreign_mating=False, target="release"),
    }


EXPECTED_STAGES = {
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


def audit(
    root: Path = ROOT,
    *,
    catalog_path: Path | None = None,
    check_git_baseline: bool = True,
) -> tuple[list[str], dict[str, Any]]:
    root = root.resolve()
    path = catalog_path or (root / CATALOG_PATH.relative_to(ROOT))
    findings: list[str] = []
    metrics: dict[str, Any] = {}
    try:
        catalog = load_catalog(path)
        domains = _domain_index(catalog)
    except RouterValidationError as exc:
        return [str(exc)], metrics

    if catalog["schema"] != 1:
        findings.append("catalog.schema: only schema 1 is supported")

    budget = catalog["core_budget"]
    if not isinstance(budget, Mapping):
        findings.append("core_budget: expected mapping")
        return findings, metrics
    core_path = root / str(budget.get("path", ""))
    try:
        core_text = core_path.read_text(encoding="utf-8")
    except OSError as exc:
        findings.append(f"core skill unreadable: {exc}")
        return findings, metrics
    lines = len(core_text.splitlines())
    words = _words(core_text)
    metrics.update(core_lines=lines, core_words=words)
    for key in ("min_lines", "max_lines", "max_words"):
        if not isinstance(budget.get(key), int) or isinstance(budget.get(key), bool):
            findings.append(f"core_budget.{key}: expected integer")
    if not findings:
        if not budget["min_lines"] <= lines <= budget["max_lines"]:
            findings.append(
                f"core line budget: {lines} not in "
                f"[{budget['min_lines']}, {budget['max_lines']}]")
        if words > budget["max_words"]:
            findings.append(
                f"core word budget: {words} > {budget['max_words']}")

    for skill_path in CURRENT_SKILLS:
        live = root / skill_path
        try:
            skill_text = live.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(f"{skill_path}: unreadable ({exc})")
            continue
        fields, error = _frontmatter_fields(skill_text, skill_path)
        if error:
            findings.append(error)
        elif fields != {"name", "description"}:
            findings.append(
                f"{skill_path}: frontmatter fields must be name+description, "
                f"got {sorted(fields)}")

    all_policy_ids: dict[str, str] = {}
    all_references: set[str] = set()
    for domain_id, domain in domains.items():
        owner = domain["owner"]
        if owner not in OWNER_PREFIX:
            findings.append(f"{domain_id}: unknown owner {owner!r}")
            continue
        refs = domain["references"]
        policy_ids = domain["policy_ids"]
        if (not isinstance(refs, list) or refs != sorted(set(refs)) or not refs):
            findings.append(f"{domain_id}: references must be sorted unique")
            continue
        if (not isinstance(policy_ids, list) or
                policy_ids != sorted(set(policy_ids))):
            findings.append(f"{domain_id}: policy_ids must be sorted unique")
            continue
        reference_text = ""
        for reference in refs:
            all_references.add(reference)
            if not reference.startswith(OWNER_PREFIX[owner]):
                findings.append(
                    f"{domain_id}: {reference} is outside owner {owner}")
            ref_path = root / reference
            if not ref_path.is_file():
                findings.append(f"{domain_id}: missing reference {reference}")
                continue
            text = ref_path.read_text(encoding="utf-8")
            reference_text += "\n" + text
            if len(text.splitlines()) > 100 and "## Contents" not in text:
                findings.append(
                    f"{domain_id}: long reference lacks Contents: {reference}")
            route = _route_from_core(reference)
            if route not in core_text:
                findings.append(
                    f"{domain_id}: core router does not directly name {route}")
        for policy_id in policy_ids:
            if not isinstance(policy_id, str) or not POLICY_ID_RE.fullmatch(policy_id):
                findings.append(f"{domain_id}: invalid policy id {policy_id!r}")
                continue
            prior = all_policy_ids.get(policy_id)
            if prior is not None:
                findings.append(
                    f"policy {policy_id} has duplicate authority: "
                    f"{prior}, {domain_id}")
            else:
                all_policy_ids[policy_id] = domain_id
            if policy_id not in reference_text:
                findings.append(
                    f"{domain_id}: policy {policy_id} is not reachable in its "
                    "owning reference")

    metrics.update(domains=len(domains), references=len(all_references),
                   mapped_policies=len(all_policy_ids))

    baseline = catalog["baseline"]
    if not isinstance(baseline, Mapping):
        findings.append("baseline: expected mapping")
    elif check_git_baseline:
        commit = baseline.get("source_commit")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            findings.append("baseline.source_commit: expected 40-hex commit")
        else:
            legacy_ids, error = _git_baseline_policy_ids(root, commit)
            if error:
                findings.append(error)
            else:
                missing = sorted(legacy_ids - set(all_policy_ids))
                if missing:
                    findings.append(
                        "legacy policy IDs have no authority: " + ", ".join(missing))
                metrics["legacy_policies"] = len(legacy_ids)

    core_scripts = set(re.findall(r"\b[A-Za-z0-9_]+\.py\b", core_text))
    unexpected_scripts = sorted(core_scripts - ALLOWED_CORE_SCRIPTS)
    if unexpected_scripts:
        findings.append(
            "core duplicates detailed script mechanics: " +
            ", ".join(unexpected_scripts))

    skill_tree_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for skill in ("pcb-design", "pcb-enclosure", "jlcpcb-fab")
        for path in (root / "skills" / skill).rglob("*.md")
    )
    for phrase in STALE_AUTHORITY_PHRASES:
        if phrase in skill_tree_text:
            findings.append(f"stale authority contradiction remains: {phrase}")

    try:
        for name, profile in _fixture_profiles().items():
            result = resolve_profile(profile, catalog=catalog)
            ids = tuple(entry["spec"]["id"] for entry in result["stages"])
            if ids != EXPECTED_STAGES[name]:
                findings.append(
                    f"fixture {name}: stage trace differs\n"
                    f"  expected={EXPECTED_STAGES[name]}\n  actual={ids}")
            if result["firmware_handoff_required"]:
                findings.append(f"fixture {name}: firmware handoff unexpectedly set")
            if any("firmware" in stage_id.lower() for stage_id in ids):
                findings.append(f"fixture {name}: firmware stage selected")
            refs = set(result["references"])
            if name == "pi_usb":
                if not any(reference.endswith("signal-integrity.md")
                           for reference in refs):
                    findings.append(
                        "fixture pi_usb: high-speed digital reference absent")
                if any("/rf" in reference for reference in refs):
                    findings.append("fixture pi_usb: RF references loaded")
            elif name == "pluto_v5":
                if not any("/rf" in reference for reference in refs):
                    findings.append("fixture pluto_v5: RF references absent")
                if any(reference.endswith("signal-integrity.md")
                       for reference in refs):
                    findings.append(
                        "fixture pluto_v5: generic SI duplicates RF authority")
            elif (any("/rf" in reference for reference in refs) or
                  any(reference.endswith("signal-integrity.md")
                      for reference in refs)):
                findings.append(
                    f"fixture {name}: SI/RF references loaded unnecessarily")
    except RouterValidationError as exc:
        findings.append(f"fixture resolution failed: {exc}")

    runner = (root / "tests/run_tests.sh").read_text(
        encoding="utf-8", errors="replace")
    for suite in ("t1_pipeline_canary_usb.py", "t1_pipeline_canary_pluto_v4.py"):
        if suite not in runner:
            findings.append(f"compatibility canary not wired: {suite}")

    return findings, metrics


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--skip-git-baseline", action="store_true",
                        help="tests only: do not compare the frozen git source")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    findings, metrics = audit(
        args.root, catalog_path=args.catalog,
        check_git_baseline=not args.skip_git_baseline)
    if findings:
        for finding in findings:
            print(f"SKILL-AUTH FAIL: {finding}")
        print(f"SKILL-AUTH VERDICT FAIL: {len(findings)} finding(s)")
        return 1
    print(
        "SKILL-AUTH PASS: "
        f"core={metrics['core_lines']} lines/{metrics['core_words']} words, "
        f"domains={metrics['domains']}, references={metrics['references']}, "
        f"policies={metrics['mapped_policies']}/{metrics.get('legacy_policies', '?')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
