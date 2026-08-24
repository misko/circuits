#!/usr/bin/env python3
"""E-STATE: prove cross-device operating-state interval compatibility.

Device-specific decoding (strap truth tables, negotiated PDOs, UVLO limits,
fault modes) belongs in selected-part facts or project electrical rules.  This
checker owns only the generic composition: for every declared phase, the full
producer interval must fit inside the consumer's accepted interval, with the
same physical quantity and unit.

Project contracts (``03_src/rules/operating_states.yaml``) are checked against
an independently authored coverage manifest
(``03_src/rules/operating_state_manifest.yaml``)::

    # operating_state_manifest.yaml
    schema: 1
    expected:
      - {id: pd_to_input_efuse, phase: negotiated}

    schema: 1
    contracts:
      - id: pd_to_input_efuse
        phase: negotiated
        producer: {ref: U_PD, quantity: voltage, unit: V,
                   min: 19.0, max: 21.0,
                   evidence: {source: 02_parts/CH224K/part.yaml,
                              sha256: <64-hex>, locator: configured_state}}
        consumer: {ref: U_PD_IN, quantity: voltage, unit: V,
                   min: 16.1, max: 30.0,
                   evidence: {source: 02_parts/TPS16630/part.yaml,
                              sha256: <64-hex>, locator: input_window}}

The tool deliberately contains no device truth table and no electrical
formula.  It is suitable for source/default/negotiated/startup/steady/off and
fault phases.  Missing evidence or malformed/empty coverage is INCOMPLETE,
never a pass.  File grading reopens every cited endpoint source below the
exact project root and requires its SHA-256 to match.  This is citation
integrity only: the numeric endpoints and prose locators are still authored,
not outputs from typed fact extractors.  Receipts therefore remain ``SHADOW``
with ``UNVERIFIED`` evidence authority and cannot be promoted yet.

VACUITY: existing cited bytes need not contain the authored numeric ranges or
locator.  Invented compatible endpoints can therefore produce an ``ACCEPTED``
shadow receipt; the authority labels and E-CLOSURE promotion hold prevent it
from becoming an electrical pass.  Fixtured by
``t1_operating_state.py::t_vacuity_unextracted_numeric_endpoints``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SCHEMA = 1
KIND = "operating-state-receipt-v1"
SHADOW_AUTHORITY = "SHADOW"
UNVERIFIED_EVIDENCE = "UNVERIFIED"
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
PHASES = frozenset({
    "source", "default", "negotiated", "startup", "steady", "off", "fault",
})
QUANTITIES = frozenset({"voltage", "current", "logic", "frequency"})
UNITS = frozenset({"V", "A", "logic", "Hz"})
QUANTITY_UNITS = {
    "voltage": "V", "current": "A", "logic": "logic", "frequency": "Hz",
}


class StateContractError(ValueError):
    """The state contract is malformed or cannot be graded."""


def _fail(message: str) -> None:
    raise StateContractError(message)


def _exact(value: Mapping[str, Any], fields: set[str], where: str) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{where}: expected a mapping")
    missing, unknown = fields - set(value), set(value) - fields
    if missing or unknown:
        _fail(f"{where}: fields differ (missing={sorted(missing)}, "
              f"unknown={sorted(unknown)})")


def _number(value: Any, where: str) -> float:
    if (not isinstance(value, (int, float)) or isinstance(value, bool) or
            not math.isfinite(value)):
        _fail(f"{where}: expected a finite number")
    return float(value)


def _endpoint(value: Mapping[str, Any], where: str) -> dict[str, Any]:
    fields = {"ref", "quantity", "unit", "min", "max", "evidence"}
    _exact(value, fields, where)
    ref = value["ref"]
    if not isinstance(ref, str) or not ref.strip():
        _fail(f"{where}.ref: expected a non-empty identity")
    quantity, unit = value["quantity"], value["unit"]
    if quantity not in QUANTITIES:
        _fail(f"{where}.quantity: expected one of {sorted(QUANTITIES)}")
    if unit not in UNITS or QUANTITY_UNITS[quantity] != unit:
        _fail(f"{where}.unit: {quantity!r} requires {QUANTITY_UNITS[quantity]!r}")
    low, high = _number(value["min"], f"{where}.min"), _number(
        value["max"], f"{where}.max")
    if high < low:
        _fail(f"{where}: max cannot be below min")
    evidence = value["evidence"]
    _exact(evidence, {"source", "sha256", "locator"}, f"{where}.evidence")
    if (not isinstance(evidence["source"], str) or
            not evidence["source"].strip() or
            not isinstance(evidence["locator"], str) or
            not evidence["locator"].strip() or
            not isinstance(evidence["sha256"], str) or
            SHA_RE.fullmatch(evidence["sha256"]) is None):
        _fail(f"{where}.evidence: expected source, locator and 64-hex sha256")
    return {"ref": ref.strip(), "quantity": quantity, "unit": unit,
            "min": low, "max": high, "evidence": {
                "source": evidence["source"].strip(),
                "sha256": evidence["sha256"],
                "locator": evidence["locator"].strip(),
            }}


def normalize_manifest(document: Mapping[str, Any]) -> list[dict[str, str]]:
    _exact(document, {"schema", "expected"}, "operating_state_manifest")
    if document["schema"] != SCHEMA or isinstance(document["schema"], bool):
        _fail(f"manifest schema: only schema {SCHEMA} is supported")
    raw = document["expected"]
    if not isinstance(raw, list) or not raw:
        _fail("manifest.expected: expected a non-empty list")
    rows = []
    for index, value in enumerate(raw):
        where = f"manifest.expected[{index}]"
        _exact(value, {"id", "phase"}, where)
        if not isinstance(value["id"], str) or ID_RE.fullmatch(value["id"]) is None:
            _fail(f"{where}.id: expected {ID_RE.pattern}")
        if value["phase"] not in PHASES:
            _fail(f"{where}.phase: expected one of {sorted(PHASES)}")
        rows.append({"id": value["id"], "phase": value["phase"]})
    keys = [(row["id"], row["phase"]) for row in rows]
    if keys != sorted(set(keys)):
        _fail("manifest.expected: rows must be sorted and unique")
    return rows


def normalize_contracts(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    _exact(document, {"schema", "contracts"}, "operating_states")
    if document["schema"] != SCHEMA or isinstance(document["schema"], bool):
        _fail(f"schema: only schema {SCHEMA} is supported")
    raw = document["contracts"]
    if not isinstance(raw, list) or not raw:
        _fail("contracts: expected a non-empty list")
    rows = []
    for index, value in enumerate(raw):
        where = f"contracts[{index}]"
        _exact(value, {"id", "phase", "producer", "consumer"}, where)
        cid = value["id"]
        if not isinstance(cid, str) or ID_RE.fullmatch(cid) is None:
            _fail(f"{where}.id: expected {ID_RE.pattern}")
        phase = value["phase"]
        if phase not in PHASES:
            _fail(f"{where}.phase: expected one of {sorted(PHASES)}")
        producer = _endpoint(value["producer"], f"{where}.producer")
        consumer = _endpoint(value["consumer"], f"{where}.consumer")
        if (producer["quantity"], producer["unit"]) != (
                consumer["quantity"], consumer["unit"]):
            _fail(f"{where}: producer and consumer quantity/unit disagree")
        rows.append({"id": cid, "phase": phase,
                     "producer": producer, "consumer": consumer})
    ids = [row["id"] for row in rows]
    if ids != sorted(set(ids)):
        _fail("contracts: ids must be sorted and unique")
    return rows


def grade_document(document: Mapping[str, Any],
                   manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    try:
        if manifest is None:
            _fail("operating-state coverage manifest is required")
        expected = normalize_manifest(manifest)
        contracts = normalize_contracts(document)
        expected_keys = {(row["id"], row["phase"]) for row in expected}
        actual_keys = {(row["id"], row["phase"]) for row in contracts}
        if actual_keys != expected_keys:
            _fail("contract coverage differs from manifest "
                  f"(missing={sorted(expected_keys - actual_keys)}, "
                  f"extra={sorted(actual_keys - expected_keys)})")
    except StateContractError as exc:
        return {"schema": SCHEMA, "kind": KIND,
                "authority": SHADOW_AUTHORITY, "verdict": "INCOMPLETE",
                "checks": [], "findings": [{"id": "E-STATE-CONFIG",
                                               "detail": str(exc)}],
                "coverage": {"passing": 0, "total": 0}}
    checks, findings = [], []
    for row in contracts:
        source, sink = row["producer"], row["consumer"]
        contained = source["min"] >= sink["min"] and source["max"] <= sink["max"]
        detail = (f"{source['ref']} {source['min']:g}..{source['max']:g} "
                  f"{source['unit']} {'is' if contained else 'is not'} within "
                  f"{sink['ref']} {sink['min']:g}..{sink['max']:g} {sink['unit']}")
        check = {"id": row["id"], "phase": row["phase"],
                 "status": "PASS" if contained else "FAIL", "detail": detail,
                 "producer": source, "consumer": sink}
        checks.append(check)
        if not contained:
            findings.append({"id": "E-STATE-RANGE", "contract": row["id"],
                             "phase": row["phase"], "detail": detail,
                             "backtrack": "schematic_or_selected_part"})
    passing = sum(row["status"] == "PASS" for row in checks)
    return {"schema": SCHEMA, "kind": KIND,
            "authority": SHADOW_AUTHORITY,
            "verdict": "ACCEPTED" if passing == len(checks) else "REJECTED",
            "checks": checks, "findings": findings,
            "coverage": {"passing": passing, "total": len(checks)}}


def _record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data)}


def _default_evidence_root(path: Path) -> Path:
    parent = path.parent
    if parent.name == "rules" and parent.parent.name == "03_src":
        return parent.parent.parent
    return parent


def _reopen_endpoint_evidence(
        contracts: list[dict[str, Any]], evidence_root: Path,
        ) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], list[str]]:
    """Reopen every endpoint citation beneath ``evidence_root``.

    Sources are relocatable project-relative paths.  Absolute paths, parent
    traversal, symlink escape, missing files, and digest disagreements remain
    explicit evidence failures rather than silently delegating trust back to
    the authored contract.
    """
    root = evidence_root.resolve(strict=True)
    records: dict[str, dict[str, Any]] = {}
    citations: list[dict[str, str]] = []
    failures: list[str] = []
    for contract in contracts:
        for role in ("producer", "consumer"):
            evidence = contract[role]["evidence"]
            source = evidence["source"]
            relative = Path(source)
            subject = f"{contract['id']}:{contract['phase']}:{role}"
            if relative.is_absolute():
                failures.append(
                    f"{subject}: evidence source must be project-relative: {source}")
                continue
            if ".." in relative.parts:
                failures.append(
                    f"{subject}: evidence source cannot contain parent "
                    f"traversal: {source}")
                continue
            try:
                target = (root / relative).resolve(strict=True)
                target.relative_to(root)
                record = _record(target)
            except (OSError, ValueError) as exc:
                failures.append(
                    f"{subject}: evidence source cannot be reopened: {source}: {exc}")
                continue
            if record["sha256"] != evidence["sha256"]:
                failures.append(
                    f"{subject}: evidence SHA-256 disagrees for {source}")
                continue
            existing = records.get(source)
            if existing is not None and existing != record:
                failures.append(
                    f"{subject}: one evidence source resolved to conflicting records")
                continue
            records[source] = record
            citations.append({
                "contract": contract["id"], "phase": contract["phase"],
                "endpoint": role, "source": source,
                "sha256": evidence["sha256"], "locator": evidence["locator"],
            })
    citations.sort(key=lambda row: (
        row["contract"], row["phase"], row["endpoint"], row["source"],
        row["locator"]))
    return ({name: records[name] for name in sorted(records)},
            citations, failures)


def grade_file(path: Path, manifest_path: Path | None = None,
               evidence_root: Path | None = None) -> dict[str, Any]:
    path = path.resolve()
    manifest_path = (manifest_path or
                     path.with_name("operating_state_manifest.yaml")).resolve()
    evidence_root = (evidence_root or _default_evidence_root(path)).resolve()
    try:
        if yaml is None:
            _fail("PyYAML is required")
        document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        manifest = yaml.safe_load(
            manifest_path.read_text(encoding="utf-8-sig"))
        if not isinstance(document, Mapping):
            _fail("root document must be a mapping")
        if not isinstance(manifest, Mapping):
            _fail("coverage manifest root must be a mapping")
    except (OSError, UnicodeError, yaml.YAMLError if yaml is not None else Exception,
            StateContractError) as exc:
        return {"schema": SCHEMA, "kind": KIND,
                "authority": SHADOW_AUTHORITY, "verdict": "INCOMPLETE",
                "subject": None, "checks": [],
                "findings": [{"id": "E-STATE-CONFIG", "detail": str(exc)}],
                "coverage": {"passing": 0, "total": 0},
                "evidence": {"authority": UNVERIFIED_EVIDENCE,
                             "reopened": False, "citations": [],
                             "coverage": {"passing": 0, "total": 0}}}
    result = grade_document(document, manifest)
    evidence_records: dict[str, dict[str, Any]] = {}
    citations: list[dict[str, str]] = []
    evidence_failures: list[str] = []
    contracts: list[dict[str, Any]] = []
    try:
        contracts = normalize_contracts(document)
        evidence_records, citations, evidence_failures = (
            _reopen_endpoint_evidence(contracts, evidence_root))
    except (StateContractError, OSError) as exc:
        evidence_failures.append(str(exc))
    expected_citations = 2 * len(contracts)
    if evidence_failures or len(citations) != expected_citations:
        if len(citations) != expected_citations and not evidence_failures:
            evidence_failures.append(
                "endpoint evidence citation denominator is incomplete")
        result["verdict"] = "INCOMPLETE"
        result["findings"].extend({"id": "E-STATE-EVIDENCE", "detail": detail}
                                  for detail in evidence_failures)
    result["subject"] = {
        "contracts": _record(path), "manifest": _record(manifest_path),
        "evidence": evidence_records,
    }
    result["evidence"] = {
        "authority": UNVERIFIED_EVIDENCE,
        "reopened": not evidence_failures and expected_citations > 0,
        "root": str(evidence_root),
        "citations": citations,
        "coverage": {"passing": len(citations), "total": expected_citations},
    }
    return result


def verify_receipt(receipt: Mapping[str, Any]) -> tuple[bool, list[str]]:
    failures = []
    if not isinstance(receipt, Mapping):
        return False, ["operating-state receipt must be a mapping"]
    if receipt.get("schema") != SCHEMA or receipt.get("kind") != KIND:
        failures.append("unsupported receipt schema/kind")
    if receipt.get("authority") != SHADOW_AUTHORITY:
        failures.append(
            "operating-state receipt authority must remain SHADOW until typed "
            "endpoint extractor receipts exist")
    subjects = receipt.get("subject")
    if (not isinstance(subjects, Mapping) or
            set(subjects) != {"contracts", "manifest", "evidence"}):
        failures.append("missing subject record")
    else:
        for name in ("contracts", "manifest"):
            subject = subjects[name]
            if not isinstance(subject, Mapping):
                failures.append(f"subject record is malformed: {name}")
                continue
            path = Path(str(subject.get("path") or ""))
            try:
                if _record(path) != subject:
                    failures.append(f"subject moved or changed: {name}")
            except OSError:
                failures.append("subject moved or changed")
        evidence_subjects = subjects.get("evidence")
        if not isinstance(evidence_subjects, Mapping):
            failures.append("evidence subject records must be a mapping")
        else:
            for source, subject in evidence_subjects.items():
                if not isinstance(subject, Mapping):
                    failures.append(f"evidence subject is malformed: {source}")
                    continue
                path = Path(str(subject.get("path") or ""))
                try:
                    if _record(path) != subject:
                        failures.append(f"subject moved or changed: evidence:{source}")
                except OSError:
                    failures.append(f"subject moved or changed: evidence:{source}")
    coverage = receipt.get("coverage")
    if not isinstance(coverage, Mapping):
        failures.append("receipt coverage must be a mapping")
        coverage = {}
    total, passing = coverage.get("total"), coverage.get("passing")
    checks = receipt.get("checks")
    if receipt.get("verdict") == "ACCEPTED" and not (
            isinstance(total, int) and total > 0 and passing == total and
            isinstance(checks, list) and checks and
            all(isinstance(row, Mapping) and row.get("status") == "PASS"
                for row in checks)):
        failures.append("accepted receipt lacks complete nonzero passing coverage")
    evidence = receipt.get("evidence")
    if not isinstance(evidence, Mapping):
        failures.append("missing endpoint evidence reopening result")
    else:
        if evidence.get("authority") != UNVERIFIED_EVIDENCE:
            failures.append(
                "endpoint evidence authority must remain UNVERIFIED until "
                "typed endpoint extractor receipts exist")
        evidence_coverage = evidence.get("coverage")
        if not isinstance(evidence_coverage, Mapping):
            failures.append("endpoint evidence coverage must be a mapping")
            evidence_coverage = {}
        evidence_total = evidence_coverage.get("total")
        evidence_passing = evidence_coverage.get("passing")
        citations = evidence.get("citations")
        if receipt.get("verdict") == "ACCEPTED" and not (
                evidence.get("reopened") is True and
                isinstance(evidence_total, int) and evidence_total > 0 and
                evidence_passing == evidence_total and
                isinstance(citations, list) and len(citations) == evidence_total):
            failures.append(
                "accepted receipt lacks complete reopened endpoint evidence")
        if isinstance(citations, list) and isinstance(subjects, Mapping):
            evidence_subjects = subjects.get("evidence") or {}
            if not isinstance(evidence_subjects, Mapping):
                evidence_subjects = {}
            for index, citation in enumerate(citations):
                if (not isinstance(citation, Mapping) or set(citation) != {
                        "contract", "phase", "endpoint", "source", "sha256",
                        "locator"}):
                    failures.append(f"evidence citation {index} is malformed")
                    continue
                source = citation.get("source")
                if not isinstance(source, str):
                    failures.append(
                        f"evidence citation {index}.source must be text")
                    continue
                record = evidence_subjects.get(source)
                if (not isinstance(record, Mapping) or
                        record.get("sha256") != citation["sha256"]):
                    failures.append(
                        f"evidence citation {index} disagrees with reopened subject")
    if (isinstance(subjects, Mapping) and
            isinstance(subjects.get("contracts"), Mapping) and
            isinstance(subjects.get("manifest"), Mapping) and
            isinstance(evidence, Mapping) and
            isinstance(evidence.get("root"), str)):
        try:
            expected = grade_file(
                Path(subjects["contracts"]["path"]),
                Path(subjects["manifest"]["path"]),
                evidence_root=Path(evidence["root"]))
            if receipt != expected:
                failures.append(
                    "receipt does not match regrading from reopened exact inputs")
        except (KeyError, OSError, TypeError, ValueError) as exc:
            failures.append(f"receipt exact-input regrade failed: {exc}")
    return not failures, failures


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("project", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args(argv)
    config = args.config or args.project / "03_src/rules/operating_states.yaml"
    result = grade_file(config, args.manifest,
                        evidence_root=args.evidence_root or args.project)
    _atomic_json(args.json, result)
    coverage = result["coverage"]
    print(f"E-STATE {result['verdict']}: {coverage['passing']}/"
          f"{coverage['total']} operating-state contracts pass; "
          f"receipt={args.json.resolve()}")
    for finding in result["findings"]:
        print(f"  {finding['id']}: {finding['detail']}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[result["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
