#!/usr/bin/env python3
"""Resolve a PCB capability profile into typed stages and owning references.

This is a pure planning/coverage tool. It does not execute a project driver,
retry a gate, promote an artifact, write a review, seal, or publish.
Graded input: the exact schema-1 capability profile JSON named by ``--profile``;
the emitted plan repeats its normalized contents.

VACUITY: a valid profile resolves and exits zero when no board, project,
artifact, or review exists. Resolution proves that the declared dependency
graph is internally composable; it cannot prove that any selected procedure
was executed, applies to project source, or that a design satisfies it. Catalog
``selects`` rules control disclosure only; engineering applicability belongs to
the project source and the owning executable gate. Fixtured by
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


def _rule_selects(rule: Mapping[str, Any], profile: CapabilityProfile) -> bool:
    if not isinstance(rule, Mapping) or not rule:
        _fail("selection rule: expected a non-empty mapping")
    allowed = {"always", "signal_integrity", "foreign_mating", "targets"}
    unknown = set(rule) - allowed
    if unknown:
        _fail(f"selection rule: unknown keys {sorted(unknown)}")
    if rule.get("always") is True:
        if len(rule) != 1:
            _fail("selection rule: always cannot be combined with conditions")
        return True
    if "always" in rule:
        _fail("selection rule always: expected true")

    checks: list[bool] = []
    if "signal_integrity" in rule:
        values = rule["signal_integrity"]
        if (not isinstance(values, list) or values != sorted(set(values)) or
                any(value not in SIGNAL_INTEGRITY for value in values)):
            _fail("selection rule signal_integrity: expected sorted unique values")
        checks.append(profile.signal_integrity in values)
    if "foreign_mating" in rule:
        values = rule["foreign_mating"]
        if (not isinstance(values, list) or values != sorted(set(values)) or
                any(not isinstance(value, bool) for value in values)):
            _fail("selection rule foreign_mating: expected sorted unique booleans")
        checks.append(profile.foreign_mating in values)
    if "targets" in rule:
        values = rule["targets"]
        if (not isinstance(values, list) or values != sorted(set(values)) or
                any(value not in TARGETS for value in values)):
            _fail("selection rule targets: expected sorted unique targets")
        checks.append(profile.target in values)
    if not checks:
        _fail("selection rule: no supported condition")
    return all(checks)


def _selection_reason(rule: Mapping[str, Any], selected: bool) -> str:
    if rule == {"always": True}:
        return "selected unconditionally"
    state = "matched" if selected else "did not match"
    return f"capability-profile disclosure selector {state}"


def _stage_row(raw: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        _fail(f"{where}: expected a mapping")
    actual = set(raw)
    selector_fields = actual & {"selects", "applies"}
    if selector_fields not in ({"selects"}, {"applies"}):
        _fail(f"{where}: requires exactly one of selects or legacy applies")
    required = {"spec", "domains"} | selector_fields
    allowed = required | {"conditional_domains"}
    if not required <= actual or not actual <= allowed:
        _fail(f"{where}: fields differ (missing={sorted(required - actual)}, "
              f"unknown={sorted(actual - allowed)})")
    normalized = dict(raw)
    if "applies" in normalized:
        # Input compatibility only.  The normalized plan still labels this as
        # disclosure selection and never upgrades it to applicability proof.
        normalized["selects"] = normalized.pop("applies")
    return normalized


def _conditional_domains(
    raw: Any,
    *,
    where: str,
    domains: Mapping[str, Mapping[str, Any]],
) -> tuple[tuple[str, Mapping[str, Any]], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        _fail(f"{where}: expected a list")
    result: list[tuple[str, Mapping[str, Any]]] = []
    for index, value in enumerate(raw):
        item = _exact_mapping(
            value, {"domain", "selects"}, f"{where}[{index}]")
        domain_id = item["domain"]
        if not isinstance(domain_id, str) or domain_id not in domains:
            _fail(f"{where}[{index}].domain: unknown domain {domain_id!r}")
        _rule_selects(item["selects"], CapabilityProfile(
            signal_integrity="ordinary", assembly="none",
            firmware="forbidden", foreign_mating=False, target="design"))
        result.append((domain_id, item["selects"]))
    ids = [item[0] for item in result]
    if ids != sorted(set(ids)):
        _fail(f"{where}: domains must be sorted and unique")
    return tuple(result)


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
    metadata: dict[
        str,
        tuple[
            tuple[str, ...], Mapping[str, Any],
            tuple[tuple[str, Mapping[str, Any]], ...],
        ],
    ] = {}
    for index, raw in enumerate(stage_rows):
        row = _stage_row(raw, f"catalog.stages[{index}]")
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
        metadata[spec.id] = (
            tuple(domain_ids), row["selects"],
            _conditional_domains(
                row.get("conditional_domains"),
                where=f"catalog.stages[{index}].conditional_domains",
                domains=domains,
            ),
        )

    # Dependency closure needs placeholders for products of adapters that this
    # disclosure profile does not select.  These are planning tokens only: in
    # particular they are not N/A engineering evidence and cannot be consumed
    # by an executor or an owning gate.
    dependency_placeholders: dict[str, dict[str, Any]] = {}
    required_outputs = {
        requirement for candidate in specs for requirement in candidate.requires
    }
    for spec in specs:
        _, rule, _ = metadata[spec.id]
        selected = _rule_selects(rule, profile)
        if selected:
            continue
        for output in spec.produces:
            if output not in required_outputs:
                continue
            prior = dependency_placeholders.get(output)
            if prior is not None:
                _fail(f"optional output {output!r} has multiple producers")
            dependency_placeholders[output] = {
                "stage_id": spec.id,
                "selection_reason": _selection_reason(rule, False),
                "authority": "DISCLOSURE_ONLY",
                "engineering_applicability": "UNKNOWN",
            }
    available = set(dependency_placeholders)

    registry = StageRegistry(specs)
    target = TARGET_STAGE[profile.target]
    plan = registry.resolve([target], available=sorted(available))

    entries: list[dict[str, Any]] = []
    all_references: list[str] = []
    for spec in plan:
        domain_ids, rule, optional_domains = metadata[spec.id]
        selected = _rule_selects(rule, profile)
        if not selected:
            _fail(f"{spec.id}: selected by dependency graph but disclosure "
                  "selection is false")
        selected_domain_ids = list(domain_ids)
        conditional_selection: list[dict[str, Any]] = []
        for domain_id, domain_rule in optional_domains:
            domain_selected = _rule_selects(domain_rule, profile)
            conditional_selection.append({
                "domain": domain_id,
                "selected": domain_selected,
                "reason": _selection_reason(domain_rule, domain_selected),
            })
            if domain_selected:
                selected_domain_ids.append(domain_id)
        references: list[str] = []
        for domain_id in selected_domain_ids:
            for reference in domains[domain_id]["references"]:
                if reference not in references:
                    references.append(reference)
                if reference not in all_references:
                    all_references.append(reference)
        entries.append({
            "spec": spec.to_mapping(),
            "domains": selected_domain_ids,
            "references": references,
            "selection_reason": _selection_reason(rule, True),
            "conditional_domain_selection": conditional_selection,
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
        "kind": "skill-disclosure-plan-v1",
        "authority": "DISCLOSURE_ONLY",
        "profile": profile.to_mapping(),
        "target_stage": target,
        "external_clearances": [],
        "dependency_placeholders": dependency_placeholders,
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
            f"lifecycle={spec['lifecycle']} "
            f"selection={entry['selection_reason']}")
        for reference in entry["references"]:
            lines.append(f"       read {reference}")
    lines.append("LOAD_NOW")
    lines.extend(f"  {reference}" for reference in result["load_now"])
    return "\n".join(lines) + "\n"


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True,
                        help="schema-1 capability profile JSON")
    parser.add_argument(
        "--at-stage",
        help="set load_now to the selected stage's references; retain the full plan",
    )
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
