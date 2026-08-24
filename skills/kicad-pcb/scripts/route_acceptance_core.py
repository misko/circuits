#!/usr/bin/env python3
"""Compatibility-safe routing transaction acceptance primitives.

This module is deliberately orchestration-neutral.  Its public APIs accept and
return JSON-compatible mappings so route drivers, candidate workspaces, and
synthetic tests share one fail-closed interpretation without importing pcbnew.

``wave`` and ``pilot`` profiles grade non-regression against baseline evidence;
``final`` requires an absolute fresh native DRC result of 0 violations, 0
unconnected items, and 0 schematic-parity findings.  Missing, stale,
unparseable, vacuous, or abnormally terminated evidence is always INCOMPLETE.

Primary APIs:

* ``run_native_drc`` and ``classify_native_drc_result``
* ``derive_required_checks`` and ``admit``
* ``objective_vector`` and ``pareto_relation``
* ``recommend_backtrack``
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import time
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable


SCHEMA = 1
PROFILES = ("wave", "pilot", "final")
DRC_SECTIONS = ("violations", "unconnected_items", "schematic_parity")
_EVIDENCE_MARKERS = ("$schema", "source", "date", "kicad_version")
_STATUS_VALUES = {"PASS", "FAIL", "N-A", "INCOMPLETE"}


class BacktrackStage(str, Enum):
    NONE = "none"
    EVIDENCE = "evidence"
    OWNERSHIP = "ownership"
    ENDPOINT_ESCAPE = "endpoint_escape"
    POWER_FILL = "power_fill"
    ROUTING = "routing"
    PLACEMENT = "placement"
    RULES = "rules"
    TRANSACTION = "transaction"


class BacktrackAction(str, Enum):
    NONE = "NONE"
    REGENERATE_EVIDENCE = "REGENERATE_EVIDENCE"
    RESTORE_OR_DECLARE_OWNERSHIP = "RESTORE_OR_DECLARE_OWNERSHIP"
    REPAIR_ENDPOINT_LAYER = "REPAIR_ENDPOINT_LAYER"
    REPAIR_POWER_GRAPH = "REPAIR_POWER_GRAPH"
    RIP_UP_REQUESTED_NETS = "RIP_UP_REQUESTED_NETS"
    BACKTRACK_PLACEMENT = "BACKTRACK_PLACEMENT"
    RESTORE_RULE_AUTHORITY = "RESTORE_RULE_AUTHORITY"
    REVERT_TRANSACTION = "REVERT_TRANSACTION"


@dataclass(frozen=True)
class BacktrackRecommendation:
    stage: BacktrackStage
    action: BacktrackAction
    reason_codes: tuple[str, ...]
    retry_same_candidate: bool
    detail: str

    def to_mapping(self) -> dict[str, Any]:
        value = asdict(self)
        value["stage"] = self.stage.value
        value["action"] = self.action.value
        value["reason_codes"] = list(self.reason_codes)
        value["kind"] = "route-backtrack-recommendation-v1"
        value["schema"] = SCHEMA
        return value


def _profile(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized not in PROFILES:
        raise ValueError(f"profile must be one of {', '.join(PROFILES)}")
    return normalized


def _json_key(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _fingerprint(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            "sha256": _sha256(path)}


def _incomplete(detail: str, *, reasons: Sequence[str],
                returncode: int | None = None,
                report_path: Path | None = None,
                output: str = "") -> dict[str, Any]:
    return {
        "schema": SCHEMA, "kind": "native-drc-result-v1",
        "status": "INCOMPLETE", "detail": detail,
        "counts": {"violations": None, "unconnected": None,
                   "schematic_parity": None},
        "process_exit": returncode,
        "evidence": {"path": str(report_path) if report_path else None,
                     "fresh": False, "complete": False},
        "reasons": list(reasons), "findings": [
            {"type": reason, "detail": detail} for reason in reasons],
        "output": output[-4000:],
    }


def _load_report(report: Any, report_path: Path | None) -> tuple[Any, bytes | None]:
    if report is not None:
        if isinstance(report, Mapping):
            payload = dict(report)
            raw = json.dumps(
                payload, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False).encode("utf-8")
            return payload, raw
        if isinstance(report, bytes):
            return json.loads(report.decode("utf-8-sig")), report
        if isinstance(report, str):
            stripped = report.strip()
            if stripped.startswith(("{", "[")):
                return json.loads(stripped), report.encode("utf-8")
            candidate = Path(report)
            if report_path is None and candidate.is_file():
                data = candidate.read_bytes()
                return json.loads(data.decode("utf-8-sig")), data
        raise ValueError("report must be a JSON mapping, bytes, JSON text, or path")
    if report_path is None or not report_path.is_file():
        raise FileNotFoundError(str(report_path) if report_path else "no report path")
    data = report_path.read_bytes()
    if not data.strip():
        raise ValueError("native DRC report is empty")
    return json.loads(data.decode("utf-8-sig")), data


def _semantic_finding(value: Any) -> Any:
    """Remove report serialization identity while retaining the violation."""
    if isinstance(value, Mapping):
        result = {}
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            normalized = str(key).lower()
            if normalized in {"uuid", "kiid", "tstamp", "timestamp", "id",
                              "pos", "position", "x", "y", "x_mm", "y_mm"}:
                continue
            result[str(key)] = _semantic_finding(item)
        return result
    if isinstance(value, list):
        return sorted((_semantic_finding(item) for item in value), key=_json_key)
    if isinstance(value, str):
        # Object UUIDs and coordinate formatting may change on a save/reload;
        # violation type/net/description remain semantic.
        value = re.sub(r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", "<uuid>", value,
                       flags=re.IGNORECASE)
        return value.strip()
    return value


def _finding_signatures(payload: Mapping[str, Any]) -> dict[str, list[str]]:
    return {section: sorted({_json_key(_semantic_finding(row))
                             for row in payload.get(section, [])})
            for section in DRC_SECTIONS}


def _counts(payload: Mapping[str, Any]) -> dict[str, int]:
    return {"violations": len(payload["violations"]),
            "unconnected": len(payload["unconnected_items"]),
            "schematic_parity": len(payload["schematic_parity"])}


def _baseline_counts(baseline: Any) -> tuple[dict[str, int] | None,
                                             dict[str, list[str]] | None]:
    if baseline is None:
        return None, None
    if isinstance(baseline, Mapping) and all(section in baseline
                                             for section in DRC_SECTIONS):
        if all(isinstance(baseline[section], list) for section in DRC_SECTIONS):
            return _counts(baseline), _finding_signatures(baseline)
    if isinstance(baseline, Mapping):
        raw = baseline.get("counts", baseline)
        if isinstance(raw, Mapping):
            aliases = {"violations": ("violations", "drc_violations"),
                       "unconnected": ("unconnected", "unconnected_items"),
                       "schematic_parity": ("schematic_parity", "parity")}
            result = {}
            for canonical, names in aliases.items():
                found = next((raw[name] for name in names if name in raw), None)
                if found is None:
                    return None, None
                result[canonical] = int(found)
            signatures = baseline.get("finding_signatures")
            if isinstance(signatures, Mapping):
                return result, {str(key): list(value)
                                for key, value in signatures.items()}
            return result, None
    raise ValueError("baseline must be a native report or complete count mapping")


def classify_native_drc_result(
        result: Any = None, *, returncode: int | None = None,
        report: Any = None, report_path: str | Path | None = None,
        profile: str = "final", baseline: Any = None,
        started_at_ns: int | None = None,
        report_mtime_ns: int | None = None,
        preexisting_fingerprint: Mapping[str, Any] | None = None,
        evidence_fresh: bool | None = None,
        evidence_complete: bool | None = None,
        output: str = "") -> dict[str, Any]:
    """Classify one native KiCad JSON report, failing closed on weak evidence.

    ``result`` may be a CompletedProcess-like object or a mapping carrying
    ``returncode``, ``report``, ``report_path``, timestamps, and output.  The
    explicit keyword arguments override those fields.
    """
    profile = _profile(profile)
    if isinstance(result, Mapping):
        if returncode is None:
            value = result.get("returncode", result.get("process_exit"))
            returncode = int(value) if value is not None else None
        if report is None:
            report = result.get("report")
        if report_path is None:
            report_path = result.get("report_path") or result.get("path")
        if started_at_ns is None:
            value = result.get("started_at_ns")
            started_at_ns = int(value) if value is not None else None
        if report_mtime_ns is None:
            value = result.get("report_mtime_ns", result.get("generated_at_ns"))
            report_mtime_ns = int(value) if value is not None else None
        if preexisting_fingerprint is None:
            value = result.get("preexisting_fingerprint")
            if isinstance(value, Mapping):
                preexisting_fingerprint = value
        if evidence_complete is None and "evidence_complete" in result:
            evidence_complete = bool(result["evidence_complete"])
        if evidence_fresh is None and "evidence_fresh" in result:
            evidence_fresh = bool(result["evidence_fresh"])
        output = output or str(result.get("output") or result.get("stderr") or "")
    elif result is not None:
        if returncode is None and hasattr(result, "returncode"):
            returncode = int(result.returncode)
        if not output:
            output = ((getattr(result, "stdout", "") or "") +
                      (getattr(result, "stderr", "") or ""))
    path = Path(report_path).resolve() if report_path is not None else None

    reasons = []
    if returncode is None or returncode != 0:
        reasons.append("DRC_ABNORMAL_EXIT")
    if evidence_fresh is False:
        reasons.append("DRC_REPORT_STALE")
    if started_at_ns is not None and report_mtime_ns is not None \
            and int(report_mtime_ns) < int(started_at_ns):
        reasons.append("DRC_REPORT_STALE")
    current_fingerprint = _fingerprint(path) if path is not None else None
    if path is not None:
        if current_fingerprint is None:
            reasons.append("DRC_REPORT_MISSING")
        elif current_fingerprint["size"] == 0:
            reasons.append("DRC_REPORT_EMPTY")
        if current_fingerprint is not None and preexisting_fingerprint is not None \
                and dict(current_fingerprint) == dict(preexisting_fingerprint):
            reasons.append("DRC_REPORT_STALE")
        if current_fingerprint is not None and started_at_ns is not None \
                and int(current_fingerprint["mtime_ns"]) < int(started_at_ns):
            reasons.append("DRC_REPORT_STALE")
    elif report is None:
        reasons.append("DRC_REPORT_MISSING")
    if reasons:
        return _incomplete(
            "; ".join(dict.fromkeys(reasons)), reasons=list(dict.fromkeys(reasons)),
            returncode=returncode, report_path=path, output=output)

    try:
        payload, raw_bytes = _load_report(report, path)
    except FileNotFoundError:
        return _incomplete("native DRC report is missing",
                           reasons=["DRC_REPORT_MISSING"],
                           returncode=returncode, report_path=path, output=output)
    except Exception as exc:
        return _incomplete(f"native DRC report is unparseable: {exc}",
                           reasons=["DRC_REPORT_UNPARSEABLE"],
                           returncode=returncode, report_path=path, output=output)
    if not isinstance(payload, Mapping):
        return _incomplete("native DRC JSON root is not an object",
                           reasons=["DRC_REPORT_UNPARSEABLE"],
                           returncode=returncode, report_path=path, output=output)
    missing = [section for section in DRC_SECTIONS if section not in payload]
    malformed = [section for section in DRC_SECTIONS
                 if section in payload and not isinstance(payload[section], list)]
    if missing or malformed:
        detail = (f"native DRC report lacks required arrays: {missing}" if missing else
                  f"native DRC report sections are not arrays: {malformed}")
        return _incomplete(detail, reasons=["DRC_REPORT_VACUOUS"],
                           returncode=returncode, report_path=path, output=output)
    has_marker = any(payload.get(marker) not in (None, "", [])
                     for marker in _EVIDENCE_MARKERS)
    if evidence_complete is False or (evidence_complete is not True and not has_marker):
        return _incomplete(
            "native DRC report has count arrays but no generator/provenance evidence",
            reasons=["DRC_REPORT_VACUOUS"], returncode=returncode,
            report_path=path, output=output)

    counts = _counts(payload)
    signatures = _finding_signatures(payload)
    findings = []
    comparison: dict[str, Any] = {"mode": "absolute" if profile == "final" else
                                 "non_regression"}
    if profile == "final":
        for dimension, count in counts.items():
            if count:
                findings.append({"type": "FINAL_DRC_NONZERO",
                                 "dimension": dimension, "count": count})
    else:
        try:
            old_counts, old_signatures = _baseline_counts(baseline)
        except Exception as exc:
            return _incomplete(f"native DRC baseline is unparseable: {exc}",
                               reasons=["DRC_BASELINE_UNPARSEABLE"],
                               returncode=returncode, report_path=path, output=output)
        if old_counts is None:
            if any(counts.values()):
                return _incomplete(
                    "delta DRC profile has nonzero findings but no complete baseline",
                    reasons=["DRC_BASELINE_MISSING"], returncode=returncode,
                    report_path=path, output=output)
            old_counts = {key: 0 for key in counts}
        if old_signatures is None and (any(old_counts.values()) or
                                       any(counts.values())):
            return _incomplete(
                "delta DRC with nonzero findings requires semantic baseline "
                "signatures, not counts alone",
                reasons=["DRC_BASELINE_SEMANTICS_MISSING"],
                returncode=returncode, report_path=path, output=output)
        increases = {key: counts[key] - old_counts[key] for key in counts
                     if counts[key] > old_counts[key]}
        comparison.update({"baseline_counts": old_counts,
                           "increases": increases})
        for dimension, increase in increases.items():
            findings.append({"type": "DRC_COUNT_REGRESSION",
                             "dimension": dimension, "increase": increase})
        if old_signatures is not None:
            new_findings = {}
            section_to_count = {"violations": "violations",
                                "unconnected_items": "unconnected",
                                "schematic_parity": "schematic_parity"}
            for section in DRC_SECTIONS:
                introduced = sorted(set(signatures[section]) -
                                    set(old_signatures.get(section, [])))
                if introduced:
                    new_findings[section] = introduced
                    findings.append({"type": "DRC_SEMANTIC_REGRESSION",
                                     "dimension": section_to_count[section],
                                     "introduced": len(introduced)})
            comparison["new_finding_signatures"] = new_findings

    status = "FAIL" if findings else "PASS"
    evidence = {"path": str(path) if path else None, "fresh": True,
                "complete": True,
                "size": (current_fingerprint or {}).get("size",
                         len(raw_bytes) if raw_bytes is not None else None),
                "sha256": (current_fingerprint or {}).get(
                    "sha256", hashlib.sha256(raw_bytes).hexdigest()
                    if raw_bytes is not None else None)}
    return {
        "schema": SCHEMA, "kind": "native-drc-result-v1",
        "profile": profile, "status": status,
        "detail": (f"{counts['violations']}/{counts['unconnected']}/"
                   f"{counts['schematic_parity']} " +
                   ("absolute" if profile == "final" else "delta-safe")),
        "counts": counts, "process_exit": returncode, "evidence": evidence,
        "finding_signatures": signatures, "comparison": comparison,
        "reasons": [], "findings": findings, "output": output[-4000:],
    }


Runner = Callable[..., Any]


def run_native_drc(board: str | Path, report_path: str | Path, *,
                   profile: str = "final", baseline: Any = None,
                   kicad_cli: str = "kicad-cli", runner: Runner | None = None,
                   cwd: str | Path | None = None, timeout: int = 600) -> dict[str, Any]:
    """Run native DRC and classify exactly the report produced by that run."""
    profile = _profile(profile)
    board_path = Path(board).resolve()
    output_path = Path(report_path).resolve()
    run_cwd = Path(cwd).resolve() if cwd is not None else board_path.parent
    board_before = _fingerprint(board_path)
    before = _fingerprint(output_path)
    started_at_ns = time.time_ns()
    command = [kicad_cli, "pcb", "drc", "--severity-all", "--refill-zones",
               "--schematic-parity", "--format", "json", "-o",
               str(output_path), str(board_path)]
    try:
        if runner is None:
            completed = subprocess.run(
                command, cwd=run_cwd, capture_output=True, text=True,
                timeout=timeout, check=False)
        else:
            try:
                completed = runner(command, run_cwd)
            except TypeError:
                completed = runner(command, cwd=run_cwd, timeout=timeout)
        if isinstance(completed, Mapping):
            returncode = completed.get("returncode", completed.get("process_exit"))
            stdout = str(completed.get("stdout") or "")
            stderr = str(completed.get("stderr") or completed.get("output") or "")
        else:
            returncode = getattr(completed, "returncode", None)
            stdout = str(getattr(completed, "stdout", "") or "")
            stderr = str(getattr(completed, "stderr", "") or "")
        classified = classify_native_drc_result(
            returncode=int(returncode) if returncode is not None else None,
            report_path=output_path, profile=profile, baseline=baseline,
            started_at_ns=started_at_ns, preexisting_fingerprint=before,
            output=stdout + stderr)
    except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
        classified = _incomplete(
            f"native DRC tool failed: {exc}", reasons=["DRC_TOOL_ERROR"],
            report_path=output_path)
    board_after = _fingerprint(board_path)
    if board_before is None or board_after is None or board_before != board_after:
        classified = _incomplete(
            "board subject changed or disappeared during native DRC",
            reasons=["DRC_SUBJECT_CHANGED"], report_path=output_path)
    classified["command"] = command
    classified["subject"] = {
        "path": str(board_path),
        "size": (board_after or {}).get("size"),
        "sha256": (board_after or {}).get("sha256"),
    }
    classified["started_at_ns"] = started_at_ns
    classified["finished_at_ns"] = time.time_ns()
    return classified


def _semantic_tags(touched: Any) -> set[str]:
    if touched is None:
        return set()
    if isinstance(touched, str):
        return {touched.strip().lower()} if touched.strip() else set()
    if isinstance(touched, Sequence) and not isinstance(touched, (str, bytes)):
        # A bare list is normally the requested net set.
        return {"copper", "nets", "connectivity"} if touched else set()
    if not isinstance(touched, Mapping):
        raise ValueError("touched semantics must be a mapping, list, or tag")
    tags = set()
    semantic = touched.get("semantics") or touched.get("kinds") or []
    if isinstance(semantic, str):
        semantic = [semantic]
    tags.update(str(value).strip().lower() for value in semantic if str(value).strip())
    synonyms = {"net": "nets", "track": "copper", "tracks": "copper",
                "arc": "copper", "via": "copper", "vias": "copper",
                "endpoint": "endpoints", "pad": "endpoints", "pads": "endpoints",
                "zone": "zones", "pour": "zones", "filled_zone": "zones",
                "power_net": "power"}
    tags = {synonyms.get(tag, tag) for tag in tags}
    aliases = {
        "nets": {"nets", "requested_nets", "net_names"},
        "copper": {"copper", "tracks", "arcs", "vias", "segments", "items"},
        "endpoints": {"endpoints", "pads", "endpoint_layers", "smd_endpoints"},
        "zones": {"zones", "filled_zones", "pours", "zone_fill"},
        "power": {"power", "power_nets", "power_graph"},
        "ownership": {"ownership", "owner", "actor", "wave"},
    }
    for tag, keys in aliases.items():
        if any(key in touched and touched[key] not in (None, False, [], {}, "")
               for key in keys):
            tags.add(tag)
    if "nets" in tags:
        tags.update({"copper", "connectivity"})
    if "power" in tags:
        tags.add("zones")
    return tags


def derive_required_checks(profile: str, touched: Any) -> list[str]:
    """Derive check applicability from what the transaction says it touched."""
    profile = _profile(profile)
    tags = _semantic_tags(touched)
    required = {"native_drc"}
    if tags & {"copper", "nets", "endpoints", "zones", "power"}:
        # diff_copper owns both geometry delta and mutation scope/ownership;
        # requiring a second alias check would duplicate one predicate.
        required.add("copper_delta")
    if tags & {"nets", "connectivity", "endpoints", "power"}:
        required.add("connectivity_regression")
    if "endpoints" in tags:
        required.add("endpoint_layer_closure")
    if tags & {"zones", "power"}:
        required.add("power_graph_delta")
    if profile in {"wave", "pilot"} and tags:
        required.add("objective_pareto")
    return sorted(required)


OBJECTIVE_DIMENSIONS = (
    "incomplete_checks", "drc_violations", "schematic_parity",
    "requested_opens", "total_unconnected", "undeclared_mutations",
    "unowned_mutations", "endpoint_layer_failures",
    "power_graph_regressions", "power_zone_splits", "via_count",
    "copper_length_nm", "bend_count",
)


def _status(row: Any) -> str | None:
    if not isinstance(row, Mapping):
        return None
    status = str(row.get("status") or row.get("verdict") or "").upper()
    aliases = {"ACCEPTED": "PASS", "REJECTED": "FAIL",
               "NA": "N-A", "NOT_APPLICABLE": "N-A"}
    status = aliases.get(status, status)
    return status if status in _STATUS_VALUES else None


def _int_value(mapping: Any, *names: str) -> int | None:
    if not isinstance(mapping, Mapping):
        return None
    for name in names:
        if name in mapping and mapping[name] is not None:
            try:
                return int(mapping[name])
            except (TypeError, ValueError):
                return None
    return None


def objective_vector(checks: Mapping[str, Any]) -> dict[str, Any]:
    """Extract the complete known minimization vector from transaction checks."""
    if not isinstance(checks, Mapping):
        raise ValueError("checks must be a mapping")
    dimensions: dict[str, int | float | None] = {
        name: None for name in OBJECTIVE_DIMENSIONS}
    public_rows = {str(name): row for name, row in checks.items()
                   if not str(name).startswith("_") and isinstance(row, Mapping)}
    status_rows = {name: row for name, row in public_rows.items()
                   if name not in {"metrics", "route_metrics", "touched"}}
    dimensions["incomplete_checks"] = (sum(
        _status(row) in {None, "INCOMPLETE"} for row in status_rows.values())
        if status_rows else None)

    for name, row in public_rows.items():
        counts = row.get("counts") if isinstance(row, Mapping) else None
        kind = str(row.get("kind") or name)
        if name == "native_drc" or kind == "native-drc-result-v1":
            dimensions["drc_violations"] = _int_value(
                counts, "violations", "drc_violations")
            dimensions["total_unconnected"] = _int_value(
                counts, "unconnected", "unconnected_items")
            dimensions["schematic_parity"] = _int_value(
                counts, "schematic_parity", "parity")
        if name in {"connectivity", "connectivity_regression"} or \
                kind in {"requested-net-regression-v1", "connectivity-signature-v1"}:
            dimensions["requested_opens"] = _int_value(
                counts, "requested_opens_after", "requested_open_count",
                "requested_opens")
            if dimensions["requested_opens"] is None:
                dimensions["requested_opens"] = _int_value(
                    row, "requested_open_count")
        if name in {"copper_delta", "mutation_scope"} or \
                kind == "semantic-copper-delta-v1":
            dimensions["undeclared_mutations"] = _int_value(
                counts, "undeclared_mutations")
            dimensions["unowned_mutations"] = _int_value(
                counts, "unowned_mutations")
        if name == "endpoint_layer_closure" or kind == "endpoint-layer-closure-v1":
            dimensions["endpoint_layer_failures"] = _int_value(counts, "failures")
        if name == "power_graph_delta" or kind == "power-graph-delta-v1":
            dimensions["power_graph_regressions"] = _int_value(counts, "regressions")
            dimensions["power_zone_splits"] = _int_value(counts, "splits")
        if name in {"metrics", "route_metrics"}:
            dimensions["via_count"] = _int_value(row, "via_count", "vias")
            dimensions["copper_length_nm"] = _int_value(
                row, "copper_length_nm", "length_nm")
            dimensions["bend_count"] = _int_value(row, "bend_count", "bends")
        explicit = row.get("objective")
        if isinstance(explicit, Mapping):
            for dimension, value in explicit.items():
                if dimension not in dimensions:
                    dimensions[str(dimension)] = None
                if value is not None:
                    try:
                        dimensions[str(dimension)] = float(value)
                    except (TypeError, ValueError):
                        dimensions[str(dimension)] = None
    active = sorted(name for name, value in dimensions.items() if value is not None)
    incomplete = any(_status(row) in {None, "INCOMPLETE"}
                     for row in status_rows.values())
    payload = {"schema": SCHEMA, "kind": "route-objective-vector-v1",
               "dimensions": dimensions, "active_dimensions": active,
               "complete": bool(active) and not incomplete}
    return {**payload,
            "signature": hashlib.sha256(_json_key(payload).encode()).hexdigest()}


def _as_vector(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("kind") == "route-objective-vector-v1":
        return dict(value)
    if isinstance(value, Mapping) and isinstance(value.get("dimensions"), Mapping):
        return {"kind": "route-objective-vector-v1", "schema": SCHEMA,
                "dimensions": dict(value["dimensions"]),
                "complete": bool(value.get("complete", True))}
    if isinstance(value, Mapping):
        # A direct numeric mapping is convenient in search/optimizer tests.
        if value and all((isinstance(item, (int, float)) and not isinstance(item, bool))
                         or item is None for item in value.values()):
            return {"kind": "route-objective-vector-v1", "schema": SCHEMA,
                    "dimensions": dict(value), "complete": True}
        return objective_vector(value)
    raise ValueError("objective must be a vector or check mapping")


def pareto_relation(previous: Any, current: Any) -> dict[str, Any]:
    """Compare ``current`` against ``previous`` on all minimization axes."""
    old = _as_vector(previous)
    new = _as_vector(current)
    old_dimensions = old.get("dimensions") or {}
    new_dimensions = new.get("dimensions") or {}
    # Canonical vectors expose every known axis as ``None``.  An axis absent
    # from both transactions is non-applicable, not incomplete evidence.
    names = sorted(name for name in set(old_dimensions) | set(new_dimensions)
                   if old_dimensions.get(name) is not None or
                   new_dimensions.get(name) is not None)
    missing = sorted(name for name in names
                     if old_dimensions.get(name) is None or
                     new_dimensions.get(name) is None)
    invalid = []
    better, worse, equal = [], [], []
    for name in names:
        if name in missing:
            continue
        left, right = old_dimensions[name], new_dimensions[name]
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)) \
                or isinstance(left, bool) or isinstance(right, bool) \
                or not math.isfinite(float(left)) or not math.isfinite(float(right)):
            invalid.append(name)
            continue
        if right < left:
            better.append(name)
        elif right > left:
            worse.append(name)
        else:
            equal.append(name)
    if not old.get("complete", True) or not new.get("complete", True) \
            or missing or invalid or not names:
        relation = "INCOMPLETE"
    elif better and not worse:
        relation = "IMPROVEMENT"
    elif worse and not better:
        relation = "REGRESSION"
    elif better and worse:
        relation = "TRADEOFF"
    else:
        relation = "EQUIVALENT"
    return {
        "schema": SCHEMA, "kind": "pareto-relation-v1",
        "status": ("PASS" if relation == "IMPROVEMENT" else
                   "INCOMPLETE" if relation == "INCOMPLETE" else "FAIL"),
        "relation": relation, "is_improvement": relation == "IMPROVEMENT",
        "is_non_regression": relation in {"IMPROVEMENT", "EQUIVALENT"},
        "better": better, "worse": worse, "equal": equal,
        "missing": missing, "invalid": invalid,
        "findings": ([] if relation == "IMPROVEMENT" else [{
            "type": ("PARETO_EVIDENCE_INCOMPLETE" if relation == "INCOMPLETE"
                     else "PARETO_NON_IMPROVEMENT"),
            "relation": relation,
        }]),
    }


def _finding_types(findings: Any) -> list[str]:
    result = []
    if isinstance(findings, Mapping):
        if findings.get("type"):
            result.append(str(findings["type"]).upper())
        for key in ("findings", "reasons", "checks"):
            if key in findings:
                result.extend(_finding_types(findings[key]))
        for key, value in findings.items():
            if key not in {"findings", "reasons", "checks"} and isinstance(value, Mapping):
                result.extend(_finding_types(value))
    elif isinstance(findings, Sequence) and not isinstance(findings, (str, bytes)):
        for value in findings:
            result.extend(_finding_types(value))
    elif isinstance(findings, str) and findings.strip():
        result.append(findings.strip().upper())
    return sorted(set(result))


def recommend_backtrack(findings: Any) -> dict[str, Any]:
    """Map concrete finding types to a typed owning-stage recommendation."""
    types = _finding_types(findings)
    joined = " ".join(types)
    rules = [
        (("REQUESTED_", "UNCONNECTED", "OPEN"),
         BacktrackStage.ROUTING, BacktrackAction.RIP_UP_REQUESTED_NETS, False,
         "rip up only the owned requested nets and reroute from the last receipt"),
        (("DRC_REPORT_MISSING", "DRC_BASELINE_MISSING",
          "DRC_BASELINE_SEMANTICS_MISSING", "DRC_REPORT_STALE",
          "DRC_REPORT_UNPARSEABLE", "DRC_REPORT_VACUOUS", "DRC_TOOL_ERROR",
          "CHECK_MISSING", "INCOMPLETE"),
         BacktrackStage.EVIDENCE, BacktrackAction.REGENERATE_EVIDENCE, True,
         "regenerate fresh machine evidence before changing the board"),
        (("UNOWNED_MUTATION", "UNDECLARED_MUTATION"),
         BacktrackStage.OWNERSHIP, BacktrackAction.RESTORE_OR_DECLARE_OWNERSHIP,
         False, "restore out-of-scope copper or backtrack to route ownership"),
        (("ENDPOINT_WRONG_LAYER", "ENDPOINT_LAYER_UNKNOWN"),
         BacktrackStage.ENDPOINT_ESCAPE, BacktrackAction.REPAIR_ENDPOINT_LAYER,
         False, "repair the endpoint escape on a pad-supported copper layer"),
        (("POWER_ZONE_SPLIT", "POWER_ZONE_LOST", "POWER_ENDPOINT"),
         BacktrackStage.POWER_FILL, BacktrackAction.REPAIR_POWER_GRAPH, False,
         "backtrack to zone topology/fill and restore the power component"),
        (("RULE_AUTHORITY", "SIDECAR", "CLEARANCE_RULE"),
         BacktrackStage.RULES, BacktrackAction.RESTORE_RULE_AUTHORITY, False,
         "restore the prepared rule authority before another route attempt"),
        (("SHORT", "CLEARANCE", "COURTYARD", "NO_CORRIDOR", "PLACEMENT"),
         BacktrackStage.PLACEMENT, BacktrackAction.BACKTRACK_PLACEMENT, False,
         "routing geometry has no legal corridor; revisit placement"),
        (("FINAL_DRC_NONZERO", "FINAL_ABSOLUTE_DRC_NONZERO"),
         BacktrackStage.ROUTING, BacktrackAction.REVERT_TRANSACTION, False,
         "revert the transaction and repair the absolute final DRC findings"),
        (("PARETO", "REGRESSION", "TRADEOFF", "NON_IMPROVEMENT"),
         BacktrackStage.TRANSACTION, BacktrackAction.REVERT_TRANSACTION, False,
         "revert the non-Pareto transaction before exploring another candidate"),
    ]
    for needles, stage, action, retry, detail in rules:
        if any(needle in joined for needle in needles):
            return BacktrackRecommendation(
                stage, action, tuple(types), retry, detail).to_mapping()
    return BacktrackRecommendation(
        BacktrackStage.NONE, BacktrackAction.NONE, tuple(types), False,
        "no backtrack is recommended").to_mapping()


def admit(profile: str, checks: Mapping[str, Any]) -> dict[str, Any]:
    """Compose required check statuses into ACCEPTED/REJECTED/INCOMPLETE."""
    profile = _profile(profile)
    if not isinstance(checks, Mapping):
        raise ValueError("checks must be a mapping")
    meta = checks.get("_meta") if isinstance(checks.get("_meta"), Mapping) else {}
    explicit_required = meta.get("required_checks") if isinstance(meta, Mapping) else None
    touched = meta.get("touched") if isinstance(meta, Mapping) else None
    if explicit_required is not None:
        required = sorted({str(name) for name in explicit_required})
    elif touched is not None:
        required = derive_required_checks(profile, touched)
    else:
        required = sorted(str(name) for name, row in checks.items()
                          if not str(name).startswith("_") and isinstance(row, Mapping))
        if profile == "final" and "native_drc" not in required:
            required.append("native_drc")
            required.sort()
    if profile == "final" and "native_drc" not in required:
        required.append("native_drc")
        required.sort()
    rows = {str(name): row for name, row in checks.items()
            if not str(name).startswith("_") and isinstance(row, Mapping)}
    missing = sorted(set(required) - set(rows))
    invalid = sorted(name for name in required if name in rows and _status(rows[name]) is None)
    incomplete = sorted(name for name in required if name in rows and
                        _status(rows[name]) in {"INCOMPLETE", "N-A"})
    failed = sorted(name for name in required if name in rows and
                    _status(rows[name]) == "FAIL")

    # Final acceptance cannot trust a forged PASS label: it independently
    # inspects the absolute native 0/0/0 denominator.
    final_absolute_failure = False
    if profile == "final" and "native_drc" in rows:
        native = rows["native_drc"]
        evidence = native.get("evidence") if isinstance(native, Mapping) else None
        subject = native.get("subject") if isinstance(native, Mapping) else None
        evidence_sha = str((evidence or {}).get("sha256") or "")
        subject_sha = str((subject or {}).get("sha256") or "")
        if (native.get("schema") != SCHEMA or
                native.get("kind") != "native-drc-result-v1" or
                native.get("profile") != "final" or
                native.get("process_exit") != 0 or
                not isinstance(evidence, Mapping) or
                evidence.get("fresh") is not True or
                evidence.get("complete") is not True or
                re.fullmatch(r"[0-9a-f]{64}", evidence_sha) is None or
                not isinstance(subject, Mapping) or
                re.fullmatch(r"[0-9a-f]{64}", subject_sha) is None or
                not subject.get("path") or not subject.get("size")):
            incomplete.append("native_drc:exact_evidence")
        counts = native.get("counts") if isinstance(native, Mapping) else None
        absolute = [_int_value(counts, "violations", "drc_violations"),
                    _int_value(counts, "unconnected", "unconnected_items"),
                    _int_value(counts, "schematic_parity", "parity")]
        if any(value is None for value in absolute):
            incomplete.append("native_drc:absolute_counts")
        elif any(value != 0 for value in absolute):
            failed.append("native_drc:absolute_0_0_0")
            final_absolute_failure = True
    missing = sorted(set(missing))
    invalid = sorted(set(invalid))
    incomplete = sorted(set(incomplete))
    failed = sorted(set(failed))
    if missing or invalid or incomplete:
        verdict = "INCOMPLETE"
    elif failed:
        verdict = "REJECTED"
    else:
        verdict = "ACCEPTED"

    statuses = [_status(row) for row in rows.values()]
    vector = objective_vector(rows)
    finding_rows: list[Any] = []
    for name in failed + incomplete + invalid:
        base_name = name.split(":", 1)[0]
        row = rows.get(base_name)
        if isinstance(row, Mapping):
            finding_rows.extend(row.get("findings") or row.get("reasons") or [name])
        else:
            finding_rows.append(name)
    finding_rows.extend({"type": "CHECK_MISSING", "check": name} for name in missing)
    if final_absolute_failure:
        finding_rows.append({"type": "FINAL_ABSOLUTE_DRC_NONZERO"})
    recommendation = recommend_backtrack(finding_rows)
    return {
        "schema": SCHEMA, "kind": "route-transaction-admission-v1",
        "profile": profile, "verdict": verdict,
        "required_checks": required,
        "required_not_pass": sorted(set(missing + invalid + incomplete + failed)),
        "coverage": {
            "required": len(required),
            "required_pass": sum(_status(rows.get(name)) == "PASS" for name in required),
            "pass": sum(status == "PASS" for status in statuses),
            "non_applicable": sum(status == "N-A" for status in statuses),
            "fail": sum(status == "FAIL" for status in statuses),
            "incomplete": sum(status in {None, "INCOMPLETE"} for status in statuses),
            "total": len(rows),
        },
        "missing_checks": missing, "invalid_checks": invalid,
        "incomplete_checks": incomplete, "failed_checks": failed,
        "objective": vector, "backtrack": recommendation,
    }


__all__ = [
    "PROFILES", "BacktrackStage", "BacktrackAction",
    "BacktrackRecommendation", "run_native_drc",
    "classify_native_drc_result", "derive_required_checks",
    "objective_vector", "pareto_relation", "admit", "recommend_backtrack",
]
