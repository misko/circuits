#!/usr/bin/env python3
"""Resolve a PCB capability profile into typed stages and owning references.

This is a pure planning/coverage tool. It does not execute a project driver,
retry a gate, promote an artifact, write a review, seal, or publish.
Graded input: the exact schema-1 capability profile JSON named by ``--profile``;
the emitted plan repeats its normalized contents.

VACUITY: a valid profile resolves and exits zero when no board, project,
artifact, or review exists. Resolution proves that the declared dependency
graph is internally composable; it cannot prove that any selected procedure
was executed or that a design satisfies it. Fixtured by
``t1_skill_progressive_disclosure.py::t_cli``.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
CATALOG_PATH = ROOT / "skills/pcb-design/references/skill-authority-map.json"
sys.path.insert(0, str(SCRIPT_DIR))

from pipeline_contract import StageSpec  # noqa: E402
from pipeline_registry import StageRegistry  # noqa: E402


PROFILE_FIELDS = {
    "schema", "signal_integrity", "assembly", "firmware",
    "foreign_mating", "target",
}
SIGNAL_INTEGRITY = frozenset({"ordinary", "high_speed_digital", "rf"})
ASSEMBLY = frozenset({"jlcpcb", "none", "other"})
FIRMWARE = frozenset({"forbidden", "requested"})
TARGETS = frozenset({
    "design", "release", "publication", "first_article", "production",
})
TARGET_STAGE = {
    "design": "KICAD-LAYOUT-SEAL",
    "release": "PCB-RELEASE-SEAL",
    "publication": "PCB-PUBLICATION",
    "first_article": "PCB-FIRST-ARTICLE",
    "production": "PCB-PRODUCTION",
}


class RouterValidationError(ValueError):
    """The profile or authority catalog is incomplete or contradictory."""


def _fail(message: str) -> None:
    raise RouterValidationError(message)


def _exact_mapping(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    actual = set(value)
    if actual != fields:
        _fail(f"{where}: fields differ (missing={sorted(fields - actual)}, "
              f"unknown={sorted(actual - fields)})")
    return value


def _enum(value: Any, choices: frozenset[str], where: str) -> str:
    if not isinstance(value, str) or value not in choices:
        _fail(f"{where}: expected one of {sorted(choices)}, got {value!r}")
    return value


@dataclass(frozen=True)
class CapabilityProfile:
    signal_integrity: str
    assembly: str
    firmware: str
    foreign_mating: bool
    target: str
    schema: int = 1

    def __post_init__(self) -> None:
        if self.schema != 1 or isinstance(self.schema, bool):
            _fail("profile.schema: only schema 1 is supported")
        _enum(self.signal_integrity, SIGNAL_INTEGRITY,
              "profile.signal_integrity")
        _enum(self.assembly, ASSEMBLY, "profile.assembly")
        _enum(self.firmware, FIRMWARE, "profile.firmware")
        _enum(self.target, TARGETS, "profile.target")
        if not isinstance(self.foreign_mating, bool):
            _fail("profile.foreign_mating: expected boolean")
        if self.target != "design" and self.assembly != "jlcpcb":
            _fail("release/publication/first-article/production targets require "
                  "the registered jlcpcb assembly path; use target=design or "
                  "add a separately reviewed manufacturer adapter")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "CapabilityProfile":
        item = _exact_mapping(value, PROFILE_FIELDS, "profile")
        return cls(**{field: item[field] for field in PROFILE_FIELDS})

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "signal_integrity": self.signal_integrity,
            "assembly": self.assembly,
            "firmware": self.firmware,
            "foreign_mating": self.foreign_mating,
            "target": self.target,
        }


def load_catalog(path: Path = CATALOG_PATH) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"catalog {path}: {exc}")
    return _exact_mapping(
        value, {"schema", "baseline", "core_budget", "domains", "stages"},
        "catalog")


def _rule_applies(rule: Mapping[str, Any], profile: CapabilityProfile) -> bool:
    if not isinstance(rule, Mapping) or not rule:
        _fail("stage.applies: expected a non-empty mapping")
    allowed = {"always", "signal_integrity", "foreign_mating", "targets"}
    unknown = set(rule) - allowed
    if unknown:
        _fail(f"stage.applies: unknown keys {sorted(unknown)}")
    if rule.get("always") is True:
        if len(rule) != 1:
            _fail("stage.applies: always cannot be combined with conditions")
        return True
    if "always" in rule:
        _fail("stage.applies.always: expected true")

    checks: list[bool] = []
    if "signal_integrity" in rule:
        values = rule["signal_integrity"]
        if (not isinstance(values, list) or values != sorted(set(values)) or
                any(value not in SIGNAL_INTEGRITY for value in values)):
            _fail("stage.applies.signal_integrity: expected sorted unique values")
        checks.append(profile.signal_integrity in values)
    if "foreign_mating" in rule:
        values = rule["foreign_mating"]
        if (not isinstance(values, list) or values != sorted(set(values)) or
                any(not isinstance(value, bool) for value in values)):
            _fail("stage.applies.foreign_mating: expected sorted unique booleans")
        checks.append(profile.foreign_mating in values)
    if "targets" in rule:
        values = rule["targets"]
        if (not isinstance(values, list) or values != sorted(set(values)) or
                any(value not in TARGETS for value in values)):
            _fail("stage.applies.targets: expected sorted unique targets")
        checks.append(profile.target in values)
    if not checks:
        _fail("stage.applies: no supported condition")
    return all(checks)


def _domain_index(catalog: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    domains = catalog["domains"]
    if not isinstance(domains, list) or not domains:
        _fail("catalog.domains: expected a non-empty list")
    result: dict[str, Mapping[str, Any]] = {}
    for index, raw in enumerate(domains):
        item = _exact_mapping(
            raw, {"id", "owner", "references", "policy_ids"},
            f"catalog.domains[{index}]")
        domain_id = item["id"]
        if not isinstance(domain_id, str) or not domain_id:
            _fail(f"catalog.domains[{index}].id: expected string")
        if domain_id in result:
            _fail(f"duplicate domain id: {domain_id}")
        result[domain_id] = item
    return result


def resolve_profile(
    profile: CapabilityProfile,
    *,
    catalog: Mapping[str, Any] | None = None,
    at_stage: str | None = None,
) -> dict[str, Any]:
    catalog = catalog or load_catalog()
    domains = _domain_index(catalog)
    stage_rows = catalog["stages"]
    if not isinstance(stage_rows, list) or not stage_rows:
        _fail("catalog.stages: expected a non-empty list")

    specs: list[StageSpec] = []
    metadata: dict[str, tuple[tuple[str, ...], Mapping[str, Any]]] = {}
    for index, raw in enumerate(stage_rows):
        row = _exact_mapping(raw, {"spec", "domains", "applies"},
                             f"catalog.stages[{index}]")
        spec = StageSpec.from_mapping(row["spec"])
        domain_ids = row["domains"]
        if (not isinstance(domain_ids, list) or
                domain_ids != sorted(set(domain_ids)) or not domain_ids):
            _fail(f"catalog.stages[{index}].domains: expected sorted unique list")
        for domain_id in domain_ids:
            if domain_id not in domains:
                _fail(f"{spec.id}: unknown domain {domain_id!r}")
        specs.append(spec)
        if spec.id in metadata:
            _fail(f"duplicate stage id: {spec.id}")
        metadata[spec.id] = (tuple(domain_ids), row["applies"])

    available: set[str] = set()
    if profile.signal_integrity == "ordinary":
        available.update({
            "rf_source_clearance", "rf_realized_clearance",
            "rf_fab_clearance",
        })
    if not profile.foreign_mating:
        available.add("mating_clearance")

    registry = StageRegistry(specs)
    target = TARGET_STAGE[profile.target]
    plan = registry.resolve([target], available=sorted(available))

    entries: list[dict[str, Any]] = []
    all_references: list[str] = []
    for spec in plan:
        domain_ids, rule = metadata[spec.id]
        if not _rule_applies(rule, profile):
            _fail(f"{spec.id}: selected by dependency graph but capability "
                  "applicability is false")
        references: list[str] = []
        for domain_id in domain_ids:
            for reference in domains[domain_id]["references"]:
                if reference not in references:
                    references.append(reference)
                if reference not in all_references:
                    all_references.append(reference)
        entries.append({
            "spec": spec.to_mapping(),
            "domains": list(domain_ids),
            "references": references,
        })

    if at_stage is not None and at_stage not in {item.id for item in plan}:
        _fail(f"--at-stage {at_stage!r} is not in the resolved plan")
    load_now = (all_references if at_stage is None else next(
        entry["references"] for entry in entries
        if entry["spec"]["id"] == at_stage))

    if any("firmware" in entry["spec"]["id"].lower() for entry in entries):
        _fail("firmware stage leaked into PCB plan")

    return {
        "schema": 1,
        "profile": profile.to_mapping(),
        "target_stage": target,
        "external_clearances": sorted(available),
        "firmware_handoff_required": profile.firmware == "requested",
        "stages": entries,
        "references": all_references,
        "load_now": load_now,
    }


def _load_profile(path: Path) -> CapabilityProfile:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"profile {path}: {exc}")
    return CapabilityProfile.from_mapping(value)


def _text_plan(result: Mapping[str, Any]) -> str:
    lines = [
        f"TARGET {result['target_stage']}",
        f"FIRMWARE_HANDOFF {'YES' if result['firmware_handoff_required'] else 'NO'}",
        "STAGES",
    ]
    for index, entry in enumerate(result["stages"], 1):
        spec = entry["spec"]
        lines.append(
            f"  {index:02d} {spec['id']} owner={spec['owner']} "
            f"lifecycle={spec['lifecycle']}")
        for reference in entry["references"]:
            lines.append(f"       read {reference}")
    lines.append("LOAD_NOW")
    lines.extend(f"  {reference}" for reference in result["load_now"])
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True,
                        help="schema-1 capability profile JSON")
    parser.add_argument("--at-stage", help="show current-stage references only")
    parser.add_argument("--json", action="store_true", help="emit canonical JSON")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH,
                        help="authority/stage catalog override (tests only)")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        result = resolve_profile(
            _load_profile(args.profile), catalog=load_catalog(args.catalog),
            at_stage=args.at_stage)
    except RouterValidationError as exc:
        print(f"SKILL-ROUTER FAIL: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True, indent=2))
    else:
        print(_text_plan(result), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
