#!/usr/bin/env python3
"""Compile typed pipeline-check applicability from validated source facts.

Applicability is a source decision, not a side effect of finding (or failing to
find) a checker configuration file.  This module therefore accepts only:

* the closed schema-1 PCB capability profile;
* closed, authority-labelled fact envelopes for architecture, integration,
  power, and assembly; and
* closed rules made from exact equality selectors.

It deliberately has no project-file discovery and never searches prose.  A
referenced fact source that is absent, unvalidated, malformed, or missing a
selected fact produces ``INCOMPLETE``.  Only complete facts can produce the
distinct ``APPLIES`` or ``NOT_APPLICABLE`` decisions.

The compiled receipt is deterministic and SHA-256 bound to the normalized
profile, facts, and requirements, but remains explicitly ``SHADOW``.  Exact-
input recompilation proves structural consistency only: the fact envelopes do
not reopen their owner receipts, and the requirements are not yet selected
from a pinned registry.  Consumers must not promote this receipt until both
authorities exist and are independently verified.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA = 1
FACT_KIND = "validated-applicability-facts-v1"
REQUIREMENTS_KIND = "pipeline-applicability-requirements-v1"
DECISION_KIND = "pipeline-applicability-decision-v1"
RECEIPT_KIND = "pipeline-applicability-receipt-v1"
SHADOW_AUTHORITY = "SHADOW"

APPLIES = "APPLIES"
NOT_APPLICABLE = "NOT_APPLICABLE"
INCOMPLETE = "INCOMPLETE"
DECISIONS = frozenset({APPLIES, NOT_APPLICABLE, INCOMPLETE})

FACT_DOMAINS = ("architecture", "integration", "power", "assembly")
SOURCES = frozenset(("profile", *FACT_DOMAINS))
PROFILE_FIELDS = {
    "schema", "signal_integrity", "assembly", "firmware",
    "foreign_mating", "target",
}
PROFILE_ENUMS = {
    "signal_integrity": frozenset({"ordinary", "high_speed_digital", "rf"}),
    "assembly": frozenset({"jlcpcb", "none", "other"}),
    "firmware": frozenset({"forbidden", "requested"}),
    "target": frozenset({
        "design", "release", "publication", "first_article", "production",
    }),
}

SYMBOL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
RULE_ID_RE = re.compile(r"^(?:[a-z][a-z0-9_]*|[A-Z][A-Z0-9-]*)$")
REASON_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class ApplicabilitySchemaError(ValueError):
    """An applicability input is not a closed supported schema."""


class ApplicabilityVerificationError(ValueError):
    """A serialized applicability receipt failed reopening/verification."""


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ApplicabilitySchemaError(f"{where}: expected a mapping")
    return value


def _exact(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    item = _mapping(value, where)
    non_strings = [key for key in item if not isinstance(key, str)]
    if non_strings:
        raise ApplicabilitySchemaError(
            f"{where}: keys must be strings, got {non_strings!r}")
    actual = set(item)
    if actual != fields:
        raise ApplicabilitySchemaError(
            f"{where}: fields differ (missing={sorted(fields - actual)}, "
            f"unknown={sorted(actual - fields)})")
    return item


def _symbol(value: Any, where: str) -> str:
    if not isinstance(value, str) or SYMBOL_RE.fullmatch(value) is None:
        raise ApplicabilitySchemaError(
            f"{where}: expected {SYMBOL_RE.pattern}, got {value!r}")
    return value


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ApplicabilitySchemaError(
            f"value is not canonical JSON data: {exc}") from exc


def canonical_sha256(value: Any) -> str:
    """Return a canonical-JSON SHA-256 for an applicability value."""
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _typed_value(value: Any, where: str) -> Any:
    """Normalize a deliberately small, non-prose applicability value type."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if not math.isfinite(number):
            raise ApplicabilitySchemaError(f"{where}: number must be finite")
        return value
    if isinstance(value, str):
        return _symbol(value, where)
    if isinstance(value, list):
        result = [_symbol(item, f"{where}[{index}]")
                  for index, item in enumerate(value)]
        if result != sorted(set(result)):
            raise ApplicabilitySchemaError(
                f"{where}: symbol lists must be sorted and unique")
        return result
    raise ApplicabilitySchemaError(
        f"{where}: expected bool, null, finite number, symbol, or symbol list")


def normalize_profile(profile: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the closed capability profile without invoking the router."""
    source = _exact(profile, PROFILE_FIELDS, "profile")
    if source["schema"] != SCHEMA or isinstance(source["schema"], bool):
        raise ApplicabilitySchemaError(
            f"profile.schema: only schema {SCHEMA} is supported")
    result: dict[str, Any] = {"schema": SCHEMA}
    for field, allowed in PROFILE_ENUMS.items():
        value = source[field]
        if not isinstance(value, str) or value not in allowed:
            raise ApplicabilitySchemaError(
                f"profile.{field}: expected one of {sorted(allowed)}")
        result[field] = value
    if not isinstance(source["foreign_mating"], bool):
        raise ApplicabilitySchemaError(
            "profile.foreign_mating: expected a boolean")
    result["foreign_mating"] = source["foreign_mating"]
    return {field: result[field] for field in (
        "schema", "signal_integrity", "assembly", "firmware",
        "foreign_mating", "target")}


def normalize_fact_envelope(value: Mapping[str, Any], *,
                            expected_domain: str | None = None) -> dict[str, Any]:
    """Validate one authority-labelled applicability fact envelope."""
    source = _exact(value, {"schema", "kind", "domain", "validation", "facts"},
                    f"facts.{expected_domain or '?'}")
    if source["schema"] != SCHEMA or isinstance(source["schema"], bool):
        raise ApplicabilitySchemaError("fact schema: only schema 1 is supported")
    if source["kind"] != FACT_KIND:
        raise ApplicabilitySchemaError(f"fact kind must be {FACT_KIND!r}")
    domain = source["domain"]
    if domain not in FACT_DOMAINS:
        raise ApplicabilitySchemaError(
            f"fact domain must be one of {list(FACT_DOMAINS)}")
    if expected_domain is not None and domain != expected_domain:
        raise ApplicabilitySchemaError(
            f"facts.{expected_domain}.domain disagrees: {domain!r}")
    validation = _exact(
        source["validation"], {"status", "authority", "subject_sha256"},
        f"facts.{domain}.validation")
    status = validation["status"]
    if status not in {"PASS", "FAIL", "INCOMPLETE"}:
        raise ApplicabilitySchemaError(
            f"facts.{domain}.validation.status: expected PASS, FAIL, or INCOMPLETE")
    authority = validation["authority"]
    if not isinstance(authority, str) or not authority.strip():
        raise ApplicabilitySchemaError(
            f"facts.{domain}.validation.authority: expected non-empty text")
    subject_sha256 = validation["subject_sha256"]
    if (not isinstance(subject_sha256, str) or
            SHA_RE.fullmatch(subject_sha256) is None):
        raise ApplicabilitySchemaError(
            f"facts.{domain}.validation.subject_sha256: expected 64-hex SHA-256")
    raw_facts = _mapping(source["facts"], f"facts.{domain}.facts")
    normalized: dict[str, Any] = {}
    for raw_name, raw_value in raw_facts.items():
        name = _symbol(raw_name, f"facts.{domain}.facts key")
        if name in normalized:
            raise ApplicabilitySchemaError(
                f"facts.{domain}.facts: duplicate normalized fact {name!r}")
        normalized[name] = _typed_value(
            raw_value, f"facts.{domain}.facts.{name}")
    return {
        "schema": SCHEMA,
        "kind": FACT_KIND,
        "domain": domain,
        "validation": {
            "status": status,
            "authority": authority.strip(),
            "subject_sha256": subject_sha256,
        },
        "facts": {name: normalized[name] for name in sorted(normalized)},
    }


def normalize_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a domain-to-envelope mapping; domains may be absent."""
    source = _mapping(facts, "facts")
    unknown = sorted(set(source) - set(FACT_DOMAINS))
    if unknown:
        raise ApplicabilitySchemaError(
            f"facts: unknown domain(s) {unknown}; free-form sources are forbidden")
    return {
        domain: normalize_fact_envelope(source[domain], expected_domain=domain)
        for domain in FACT_DOMAINS if domain in source
    }


def normalize_rule(rule: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one exact-selector applicability rule."""
    source = _exact(
        rule, {"schema", "id", "sources", "when", "not_applicable_reason"},
        "applicability rule")
    if source["schema"] != SCHEMA or isinstance(source["schema"], bool):
        raise ApplicabilitySchemaError("rule.schema: only schema 1 is supported")
    rule_id = source["id"]
    if not isinstance(rule_id, str) or RULE_ID_RE.fullmatch(rule_id) is None:
        raise ApplicabilitySchemaError(
            f"rule.id: expected {RULE_ID_RE.pattern}, got {rule_id!r}")
    raw_sources = source["sources"]
    if (not isinstance(raw_sources, list) or not raw_sources or
            raw_sources != sorted(set(raw_sources)) or
            any(item not in SOURCES for item in raw_sources)):
        raise ApplicabilitySchemaError(
            f"rule.sources: expected sorted unique values from {sorted(SOURCES)}")
    reason = source["not_applicable_reason"]
    if not isinstance(reason, str) or REASON_RE.fullmatch(reason) is None:
        raise ApplicabilitySchemaError(
            "rule.not_applicable_reason: expected a typed UPPER_SNAKE_CASE reason")
    when = _mapping(source["when"], "rule.when")
    if set(when) not in ({"all"}, {"any"}):
        raise ApplicabilitySchemaError(
            "rule.when: requires exactly one non-empty all or any selector list")
    operator = next(iter(when))
    raw_selectors = when[operator]
    if not isinstance(raw_selectors, list) or not raw_selectors:
        raise ApplicabilitySchemaError(
            f"rule.when.{operator}: expected a non-empty list")
    selectors: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_selectors):
        where = f"rule.when.{operator}[{index}]"
        row = _exact(raw, {"source", "fact", "equals"}, where)
        selector_source = row["source"]
        if selector_source not in SOURCES:
            raise ApplicabilitySchemaError(
                f"{where}.source: expected one of {sorted(SOURCES)}")
        fact = _symbol(row["fact"], f"{where}.fact")
        if selector_source == "profile" and fact not in PROFILE_FIELDS - {"schema"}:
            raise ApplicabilitySchemaError(
                f"{where}.fact: unknown profile field {fact!r}")
        selectors.append({
            "source": selector_source,
            "fact": fact,
            "equals": _typed_value(row["equals"], f"{where}.equals"),
        })
    selector_sources = sorted({row["source"] for row in selectors})
    if selector_sources != raw_sources:
        raise ApplicabilitySchemaError(
            "rule.sources must exactly equal the sources named by selectors")
    canonical_selectors = sorted(
        selectors,
        key=lambda row: (row["source"], row["fact"],
                         json.dumps(row["equals"], sort_keys=True)))
    if selectors != canonical_selectors or len(selectors) != len({
            _canonical_bytes(row) for row in selectors}):
        raise ApplicabilitySchemaError(
            f"rule.when.{operator}: selectors must be sorted and unique")
    return {
        "schema": SCHEMA,
        "id": rule_id,
        "sources": list(raw_sources),
        "when": {operator: selectors},
        "not_applicable_reason": reason,
    }


def normalize_requirements(requirements: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the closed, ordered set of applicability requirements."""
    source = _exact(requirements, {"schema", "kind", "rules"}, "requirements")
    if source["schema"] != SCHEMA or isinstance(source["schema"], bool):
        raise ApplicabilitySchemaError(
            "requirements.schema: only schema 1 is supported")
    if source["kind"] != REQUIREMENTS_KIND:
        raise ApplicabilitySchemaError(
            f"requirements.kind must be {REQUIREMENTS_KIND!r}")
    if not isinstance(source["rules"], list) or not source["rules"]:
        raise ApplicabilitySchemaError("requirements.rules must be non-empty")
    rules = [normalize_rule(row) for row in source["rules"]]
    ids = [row["id"] for row in rules]
    if ids != sorted(set(ids)):
        raise ApplicabilitySchemaError(
            "requirements.rules must be sorted and unique by id")
    return {"schema": SCHEMA, "kind": REQUIREMENTS_KIND, "rules": rules}


def _incomplete_decision(rule_id: str, findings: Sequence[str],
                         fact_hashes: Mapping[str, str] | None = None
                         ) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "kind": DECISION_KIND,
        "id": rule_id,
        "status": INCOMPLETE,
        "reason": "APPLICABILITY_INPUT_INCOMPLETE",
        "fact_hashes": dict(sorted((fact_hashes or {}).items())),
        "checks": [],
        "findings": list(findings),
    }


def evaluate_applicability(rule: Mapping[str, Any],
                           facts: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate one rule against exact typed facts, returning a mapping.

    ``facts`` may additionally contain the closed capability profile under the
    reserved ``profile`` key.  Direct callers that do not select profile facts
    need only pass domain envelopes.  Schema/input problems are retained as an
    ``INCOMPLETE`` decision rather than escaping as an accidental N/A.
    """
    rule_id = str(rule.get("id") or "invalid") if isinstance(rule, Mapping) \
        else "invalid"
    try:
        normalized_rule = normalize_rule(rule)
    except (ApplicabilitySchemaError, TypeError, ValueError) as exc:
        return _incomplete_decision(rule_id, [str(exc)])

    try:
        raw_facts = _mapping(facts, "facts")
    except ApplicabilitySchemaError as exc:
        return _incomplete_decision(normalized_rule["id"], [str(exc)])
    unknown = sorted(set(raw_facts) - SOURCES)
    if unknown:
        return _incomplete_decision(
            normalized_rule["id"],
            [f"facts: unknown source(s) {unknown}; free-form sources are forbidden"])

    normalized: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    findings: list[str] = []
    for source in normalized_rule["sources"]:
        if source not in raw_facts:
            findings.append(f"required applicability source is absent: {source}")
            continue
        try:
            value = (normalize_profile(raw_facts[source]) if source == "profile"
                     else normalize_fact_envelope(
                         raw_facts[source], expected_domain=source))
            normalized[source] = value
            hashes[source] = canonical_sha256(value)
            if (source != "profile" and
                    value["validation"]["status"] != "PASS"):
                findings.append(
                    f"applicability source {source} is not validated PASS")
        except (ApplicabilitySchemaError, TypeError, ValueError) as exc:
            findings.append(str(exc))
    if findings:
        return _incomplete_decision(normalized_rule["id"], findings, hashes)

    operator, selectors = next(iter(normalized_rule["when"].items()))
    checks: list[dict[str, Any]] = []
    for selector in selectors:
        source = selector["source"]
        values = (normalized[source] if source == "profile"
                  else normalized[source]["facts"])
        fact = selector["fact"]
        if fact not in values:
            findings.append(f"applicability fact is absent: {source}.{fact}")
            continue
        actual = values[fact]
        checks.append({
            "source": source,
            "fact": fact,
            "equals": copy.deepcopy(selector["equals"]),
            "actual": copy.deepcopy(actual),
            "matched": actual == selector["equals"],
        })
    if findings:
        decision = _incomplete_decision(normalized_rule["id"], findings, hashes)
        decision["checks"] = checks
        return decision

    matches = [row["matched"] for row in checks]
    applies = all(matches) if operator == "all" else any(matches)
    return {
        "schema": SCHEMA,
        "kind": DECISION_KIND,
        "id": normalized_rule["id"],
        "status": APPLIES if applies else NOT_APPLICABLE,
        "reason": None if applies else normalized_rule["not_applicable_reason"],
        "fact_hashes": dict(sorted(hashes.items())),
        "checks": checks,
        "findings": [],
    }


def _normalized_inputs(profile: Mapping[str, Any], facts: Mapping[str, Any],
                       requirements: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "pipeline-applicability-inputs-v1",
        "profile": normalize_profile(profile),
        "facts": normalize_facts(facts),
        "requirements": normalize_requirements(requirements),
    }


def _receipt_digest(receipt: Mapping[str, Any]) -> str:
    value = copy.deepcopy(dict(receipt))
    binding = value.get("binding")
    if isinstance(binding, dict):
        binding.pop("receipt_sha256", None)
    return canonical_sha256(value)


def compile_applicability(
        profile: Mapping[str, Any], facts: Mapping[str, Any],
        requirements: Mapping[str, Any]) -> dict[str, Any]:
    """Compile deterministic decisions bound to the three exact inputs."""
    inputs = _normalized_inputs(profile, facts, requirements)
    evaluation_facts = {"profile": inputs["profile"], **inputs["facts"]}
    decisions = {
        rule["id"]: evaluate_applicability(rule, evaluation_facts)
        for rule in inputs["requirements"]["rules"]
    }
    counts = {
        status.lower(): sum(row["status"] == status
                            for row in decisions.values())
        for status in (APPLIES, NOT_APPLICABLE, INCOMPLETE)
    }
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "kind": RECEIPT_KIND,
        "authority": SHADOW_AUTHORITY,
        "status": (INCOMPLETE if counts[INCOMPLETE.lower()] else "COMPLETE"),
        "binding": {
            "algorithm": "sha256",
            "subject_sha256": canonical_sha256(inputs),
        },
        "inputs": {
            "profile": {"sha256": canonical_sha256(inputs["profile"])},
            "facts": {
                domain: {"sha256": canonical_sha256(value)}
                for domain, value in inputs["facts"].items()
            },
            "requirements": {
                "sha256": canonical_sha256(inputs["requirements"]),
            },
        },
        "decisions": decisions,
        "coverage": {
            "applies": counts[APPLIES.lower()],
            "not_applicable": counts[NOT_APPLICABLE.lower()],
            "incomplete": counts[INCOMPLETE.lower()],
            "total": len(decisions),
        },
    }
    receipt["binding"]["receipt_sha256"] = _receipt_digest(receipt)
    return receipt


def verify_applicability(receipt: Mapping[str, Any],
                         exact_inputs: Mapping[str, Any] | None = None
                         ) -> tuple[bool, list[str]]:
    """Verify structure/self-hash and recompile from ``exact_inputs``.

    Exact inputs are a mapping containing exactly ``profile``, ``facts``, and
    ``requirements``.  Omitting them is a structural verification failure.
    Even a successful recompilation does not authenticate owner truth or confer
    promotion authority.
    """
    failures: list[str] = []
    if not isinstance(receipt, Mapping):
        return False, ["applicability receipt must be a mapping"]
    allowed = {"schema", "kind", "authority", "status", "binding", "inputs",
               "decisions", "coverage"}
    actual = set(receipt)
    if actual != allowed:
        failures.append(
            f"receipt fields differ (missing={sorted(allowed - actual)}, "
            f"unknown={sorted(actual - allowed)})")
    if receipt.get("schema") != SCHEMA or receipt.get("kind") != RECEIPT_KIND:
        failures.append("unsupported applicability receipt schema/kind")
    if receipt.get("authority") != SHADOW_AUTHORITY:
        failures.append(
            "applicability receipt authority must remain SHADOW until owner "
            "receipts and a pinned requirements registry are reopened")
    binding = receipt.get("binding")
    if not isinstance(binding, Mapping):
        failures.append("receipt binding must be a mapping")
    else:
        if set(binding) != {"algorithm", "subject_sha256", "receipt_sha256"}:
            failures.append("receipt binding fields are invalid")
        if binding.get("algorithm") != "sha256":
            failures.append("receipt binding algorithm is invalid")
        for name in ("subject_sha256", "receipt_sha256"):
            value = binding.get(name)
            if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
                failures.append(f"receipt binding {name} is invalid")
        try:
            if binding.get("receipt_sha256") != _receipt_digest(receipt):
                failures.append("applicability receipt content hash changed")
        except (ApplicabilitySchemaError, TypeError, ValueError) as exc:
            failures.append(f"applicability receipt is not canonical data: {exc}")

    decisions = receipt.get("decisions")
    if not isinstance(decisions, Mapping) or not decisions:
        failures.append("receipt decisions must be a non-empty mapping")
        decisions = {}
    else:
        for rule_id, decision in decisions.items():
            if not isinstance(decision, Mapping):
                failures.append(f"decision {rule_id!r} must be a mapping")
                continue
            if decision.get("id") != rule_id:
                failures.append(f"decision key/id disagree: {rule_id!r}")
            if decision.get("status") not in DECISIONS:
                failures.append(f"decision {rule_id!r} has invalid status")
            reason = decision.get("reason")
            if decision.get("status") == APPLIES and reason is not None:
                failures.append(f"APPLIES decision {rule_id!r} carries a reason")
            if decision.get("status") != APPLIES and (
                    not isinstance(reason, str) or
                    REASON_RE.fullmatch(reason) is None):
                failures.append(f"non-applying decision {rule_id!r} lacks typed reason")

    if exact_inputs is None:
        failures.append(
            "exact profile/facts/requirements are required for structural "
            "recompilation")
    else:
        try:
            supplied = _exact(
                exact_inputs, {"profile", "facts", "requirements"},
                "exact_inputs")
            expected = compile_applicability(
                supplied["profile"], supplied["facts"], supplied["requirements"])
            if receipt != expected:
                failures.append(
                    "applicability receipt does not match recompilation from exact inputs")
        except (ApplicabilitySchemaError, TypeError, ValueError) as exc:
            failures.append(f"exact applicability inputs are invalid: {exc}")
    return not failures, failures


def write_applicability(path: Path | str, receipt: Mapping[str, Any],
                        exact_inputs: Mapping[str, Any]) -> Path:
    """Serialize a SHADOW receipt after exact-input structural verification."""
    valid, failures = verify_applicability(receipt, exact_inputs)
    if not valid:
        raise ApplicabilityVerificationError("; ".join(failures))
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(
        receipt, indent=2, sort_keys=True, ensure_ascii=False,
        allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, target)
    return target


def reopen_applicability(path: Path | str,
                         exact_inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Read a SHADOW receipt and structurally recompile its exact inputs."""
    target = Path(path)
    try:
        value = json.loads(target.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApplicabilityVerificationError(
            f"applicability receipt cannot be reopened: {exc}") from exc
    valid, failures = verify_applicability(value, exact_inputs)
    if not valid:
        raise ApplicabilityVerificationError("; ".join(failures))
    return value


__all__ = [
    "APPLIES", "DECISION_KIND", "DECISIONS", "FACT_DOMAINS", "FACT_KIND",
    "INCOMPLETE", "NOT_APPLICABLE", "RECEIPT_KIND", "REQUIREMENTS_KIND",
    "SHADOW_AUTHORITY",
    "SCHEMA", "ApplicabilitySchemaError", "ApplicabilityVerificationError",
    "canonical_sha256", "compile_applicability", "evaluate_applicability",
    "normalize_fact_envelope", "normalize_facts", "normalize_profile",
    "normalize_requirements", "normalize_rule", "reopen_applicability",
    "verify_applicability", "write_applicability",
]
