#!/usr/bin/env python3
"""M-STATE — derive PCB maturity from one findings ledger.

Usage: project_state.py PROJECT [--ledger PATH] [--expect LEVEL] [--no-write]
                        [--receipt-registry PATH]
                        [--readiness-authority shadow|receipts|agreement]

G-INPUT: the verdict names the exact findings ledger under grade.
G-COVER: it reports ``N/M controls satisfied`` for the derived level.
G-RED: tests/t1_pipeline_reliability.py plants an open order-blocking finding
and proves the checker lowers maturity and rejects ``--expect``.

Maturity is never a prose adjective inferred from an old STATUS paragraph.
It is the highest contiguous level whose required gates pass and which has no
open finding that blocks that level.  Later validation work remains visible
without incorrectly making an orderable first article look production-tested.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import yaml


LEVELS = [
    "DRAFT", "DESIGN_CLEAN", "FIRST_ARTICLE_ORDERABLE",
    "FIRST_ARTICLE_TESTED", "PRODUCTION_RELEASED",
]


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def rank(level: str) -> int:
    if level not in LEVELS:
        raise ValueError(f"unknown maturity {level!r}; choose one of {LEVELS}")
    return LEVELS.index(level)


def derive(project: Path, ledger_path: Path) -> dict:
    data = yaml.safe_load(ledger_path.read_text(encoding="utf-8-sig")) or {}
    if data.get("schema") != 1:
        raise ValueError(f"{ledger_path}: schema must be 1")
    gates = data.get("gates") or []
    findings = data.get("findings") or []
    if not isinstance(gates, list) or not isinstance(findings, list):
        raise ValueError("gates and findings must be lists")
    ids: set[str] = set()
    for kind, rows in (("gate", gates), ("finding", findings)):
        for row in rows:
            ident = str(row.get("id", ""))
            if not ident or ident in ids:
                raise ValueError(f"missing/duplicate control id {ident!r}")
            ids.add(ident)
            if not str(row.get("owner", "")).strip():
                raise ValueError(f"{ident}: owner is required")
            if not str(row.get("closes_when", "")).strip():
                raise ValueError(f"{ident}: closes_when is required")
            field = "required_for" if kind == "gate" else "blocks_at_or_above"
            rank(str(row.get(field)))
            if kind == "gate" and row.get("state") not in ("pass", "pending"):
                raise ValueError(f"{ident}: gate state must be pass or pending")
            if kind == "finding" and row.get("state") not in ("open", "closed", "waived"):
                raise ValueError(f"{ident}: finding state must be open, closed or waived")
            if row.get("state") in ("pass", "closed", "waived"):
                evidence = row.get("evidence") or []
                if not isinstance(evidence, list) or not evidence:
                    raise ValueError(f"{ident}: resolved control needs evidence paths")
                for value in evidence:
                    path = project / str(value)
                    if not path.exists():
                        raise ValueError(f"{ident}: evidence does not exist: {value}")

    achieved = "DRAFT"
    evaluated: list[dict] = []
    for level in LEVELS[1:]:
        level_rank = rank(level)
        required = [g for g in gates if rank(str(g["required_for"])) <= level_rank]
        # A named level with no gate of its own would otherwise be achieved by
        # omission.  Every rung needs at least one affirmative control.
        own = [g for g in gates if g["required_for"] == level]
        blockers = [f for f in findings
                    if f["state"] == "open" and
                    rank(str(f["blocks_at_or_above"])) <= level_rank]
        failed = [g for g in required if g["state"] != "pass"]
        ok = bool(own) and not failed and not blockers
        evaluated.append({
            "level": level, "satisfied": ok,
            "required_gates": [g["id"] for g in required],
            "pending_gates": [g["id"] for g in failed],
            "open_blockers": [f["id"] for f in blockers],
        })
        if not ok:
            break
        achieved = level
    arank = rank(achieved)
    relevant_gates = [g for g in gates if rank(str(g["required_for"])) <= arank]
    relevant_findings = [f for f in findings
                         if rank(str(f["blocks_at_or_above"])) <= arank]
    satisfied = sum(g["state"] == "pass" for g in relevant_gates) + \
        sum(f["state"] != "open" for f in relevant_findings)
    total = len(relevant_gates) + len(relevant_findings)
    return {
        "schema": 1, "project": project.name,
        "ledger": ledger_path.relative_to(project).as_posix(),
        "declared_target": data.get("target"), "derived_maturity": achieved,
        "coverage": {"satisfied": satisfied, "total": total},
        "evaluated": evaluated, "gates": gates, "findings": findings,
    }


def attach_receipt_readiness(project: Path, legacy: dict,
                             registry_path: Path,
                             authority: str = "shadow") -> dict:
    """Compose receipt readiness and select an explicit authority policy."""

    try:
        pcb_design_scripts = (
            Path(__file__).resolve().parents[2] / "pcb-design" / "scripts"
        )
        if str(pcb_design_scripts) not in sys.path:
            sys.path.insert(0, str(pcb_design_scripts))
        from pipeline_readiness import evaluate as evaluate_receipts

        receipt_mode = "shadow" if authority == "shadow" else "receipts"
        shadow = evaluate_receipts(
            project, registry_path, authority=receipt_mode)
    except (ImportError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        shadow = {
            "schema": 1,
            "mode": "shadow" if authority == "shadow" else "receipts",
            "authority": ("legacy-findings-ledger" if authority == "shadow"
                          else "receipt-registry"),
            "registry": str(registry_path),
            "status": "FAIL",
            "derived_maturity": "DRAFT",
            "coverage": {"satisfied": 0, "total": 0, "not_applicable": 0},
            "evaluated": [],
            "stages": [],
            "findings": [str(exc)],
        }
    legacy_maturity = legacy["derived_maturity"]
    receipt_maturity = shadow["derived_maturity"]
    maturity_matches = legacy_maturity == receipt_maturity
    shadow["comparison"] = {
        "legacy_derived_maturity": legacy_maturity,
        "receipt_derived_maturity": receipt_maturity,
        "maturity_matches": maturity_matches,
        "matches": shadow["status"] == "PASS" and maturity_matches,
    }
    if authority == "shadow":
        legacy["receipt_shadow"] = shadow
        legacy["receipt_readiness"] = shadow
        legacy["readiness_authority"] = "legacy-findings-ledger"
        return legacy

    legacy_projection = {
        key: legacy[key] for key in (
            "declared_target", "derived_maturity", "coverage", "evaluated",
            "gates", "findings")
    }
    result = dict(legacy)
    result["legacy_projection"] = legacy_projection
    result["receipt_readiness"] = shadow
    result["readiness_authority"] = (
        "receipt-registry" if authority == "receipts"
        else "receipt-registry+legacy-agreement")
    result["declared_target"] = shadow.get("target")
    result["derived_maturity"] = shadow["derived_maturity"]
    result["coverage"] = {
        "satisfied": shadow["coverage"]["satisfied"],
        "total": shadow["coverage"]["total"],
    }
    result["evaluated"] = shadow["evaluated"]
    result["authority_satisfied"] = (
        shadow["status"] == "PASS" and
        (authority != "agreement" or shadow["comparison"]["matches"]))
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project")
    ap.add_argument("--ledger", default="01_docs/findings.yaml")
    ap.add_argument(
        "--receipt-registry",
        help="project-relative receipt registry evaluated under the selected authority",
    )
    ap.add_argument(
        "--readiness-authority",
        choices=("shadow", "receipts", "agreement"), default="shadow",
        help="legacy-compatible shadow, authoritative receipts, or require "
             "receipt/legacy agreement (requires --receipt-registry)",
    )
    ap.add_argument("--expect", choices=LEVELS)
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args(argv)
    project = Path(args.project).resolve()
    ledger = Path(args.ledger)
    ledger = ledger if ledger.is_absolute() else project / ledger
    try:
        result = derive(project, ledger)
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(f"M-STATE FAIL: 0/1 controls satisfied; ledger={ledger}; {exc}")
        return 2
    if args.readiness_authority != "shadow" and not args.receipt_registry:
        print("M-STATE FAIL: --readiness-authority receipts/agreement requires "
              "--receipt-registry")
        return 2
    if args.receipt_registry:
        registry = Path(args.receipt_registry)
        registry = registry if registry.is_absolute() else project / registry
        result = attach_receipt_readiness(
            project, result, registry, args.readiness_authority)
    cov = result["coverage"]
    maturity = result["derived_maturity"]
    if not args.no_write:
        atomic_json(project / "06_build/project_state.json", result)
    expected_ok = args.expect is None or maturity == args.expect
    target_ok = result.get("declared_target") in (None, maturity)
    authority_ok = result.get("authority_satisfied", True)
    shadow_text = ""
    if "receipt_readiness" in result:
        shadow = result["receipt_readiness"]
        comparison = shadow["comparison"]
        shadow_text = (
            f"; receipt-{args.readiness_authority}={shadow['status']}, "
            f"receipt-derived={shadow['derived_maturity']}, "
            f"legacy-agrees={comparison['matches']}"
        )
        if shadow["status"] != "PASS" and shadow.get("findings"):
            shadow_text += f", receipt-finding={shadow['findings'][0]}"
    if not expected_ok or not target_ok or not authority_ok:
        wanted = args.expect or result.get("declared_target")
        first = next((r for r in result["evaluated"] if not r["satisfied"]), {})
        print(f"M-STATE FAIL: {cov['satisfied']}/{max(1, cov['total'])} controls "
              f"satisfied; ledger={ledger}; derived={maturity}, wanted={wanted}; "
              f"pending={first.get('pending_gates', [])}, "
              f"blockers={first.get('open_blockers', [])}{shadow_text}")
        return 1
    print(f"M-STATE PASS: {cov['satisfied']}/{max(1, cov['total'])} controls "
          f"satisfied; authority={result.get('readiness_authority', 'legacy-findings-ledger')}; "
          f"ledger={ledger}; derived={maturity}{shadow_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
