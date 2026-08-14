#!/usr/bin/env python3
"""RF-CONTEXT: select a bounded local RF knowledge bundle for one project.

Usage: rf_context.py PROJECT [--contract PATH] [--archive PATH] [--out DIR]

The command performs no network access and launches no reviewer. It exits N-A
for an explicit non-RF contract, excludes precedent/incident cards by default,
and publishes deterministic context/report outputs through the shared atomic
artifact transaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

PCB_DESIGN_SCRIPTS = Path(__file__).resolve().parents[2] / "pcb-design" / "scripts"
sys.path.insert(0, str(PCB_DESIGN_SCRIPTS))
from pipeline_artifacts import ArtifactBundleTransaction
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rf_bundle import fresh_bundle

VERSION = "1"
ALLOWED_PROVENANCE = {"normative", "background", "tool_capability",
                      "precedent", "incident"}
CLEAN_ROOM = {"normative", "background", "tool_capability"}


class ContextError(RuntimeError):
    pass


def _load_yaml(path: Path, label: str) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        raise ContextError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContextError(f"{label} root must be a mapping")
    return data


def _canonical(value) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _features(rf: dict) -> list[str]:
    result = {"rf_intent"}
    tier = str(rf.get("risk_tier", ""))
    if tier == "microwave":
        result.add("microwave")
    if tier == "phase-coherent":
        result.add("phase_coherent")
    ports = rf.get("ports") or []
    if len(ports) > 2 or sum(len(p.get("nets") or []) for p in ports
                             if isinstance(p, dict)) > 2:
        result.add("multiport")
    if any(str(p.get("launch", "")).strip() for p in ports
           if isinstance(p, dict)):
        result.add("connector_launch")
    sections = rf.get("cross_sections") or []
    if sections:
        result.add("controlled_impedance")
    if any("coplanar" in str(s.get("solver", "")).lower()
           or s.get("gap_mm") is not None for s in sections
           if isinstance(s, dict)):
        result.add("cpwg")
    if any("jlc" in str(s.get("stackup_source", "")).lower()
           for s in sections if isinstance(s, dict)):
        result.add("jlcpcb")
    layout = rf.get("layout_constraints") or {}
    if isinstance(layout, dict) and layout.get("route"):
        result.add("bend_geometry")
    if isinstance(layout, dict) and layout.get("ground_fence"):
        result.add("via_fence")
    return sorted(result)


def _validate_archive(archive: dict) -> list[dict]:
    if archive.get("schema") != 1:
        raise ContextError("RF source-card archive schema must be integer 1")
    rows = archive.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ContextError("RF source-card archive needs a non-empty sources list")
    required = {"id", "title", "publisher", "locator", "provenance",
                "topics", "selectors", "claim", "use", "limits"}
    seen, normalized = set(), []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ContextError(f"sources[{index}] must be a mapping")
        missing = sorted(required - set(row))
        if missing:
            raise ContextError(f"sources[{index}] missing {missing}")
        ident = str(row["id"]).strip()
        if not ident or ident in seen:
            raise ContextError(f"source-card id is empty or duplicated: {ident!r}")
        seen.add(ident)
        provenance = str(row["provenance"]).strip()
        if provenance not in ALLOWED_PROVENANCE:
            raise ContextError(f"{ident}: invalid provenance {provenance!r}")
        for key in ("title", "publisher", "locator", "claim", "use", "limits"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ContextError(f"{ident}.{key} must be non-empty text")
        for key in ("topics", "selectors"):
            if (not isinstance(row[key], list) or not row[key]
                    or any(not isinstance(v, str) or not v.strip()
                           for v in row[key])):
                raise ContextError(f"{ident}.{key} must be non-empty strings")
        normalized.append({key: row[key] for key in sorted(required)})
    return normalized


def build_context(contract: dict, archive: dict) -> dict:
    if contract.get("schema") != 1 or not isinstance(contract.get("rf"), dict):
        raise ContextError("rf.yaml must carry schema: 1 and an rf mapping")
    rf = contract["rf"]
    if not isinstance(rf.get("enabled"), bool):
        raise ContextError("rf.enabled must be true or false")
    process = rf.get("process") or {}
    if not isinstance(process, dict):
        raise ContextError("rf.process must be a mapping")
    profile = str(process.get("profile", "legacy-compatible"))
    policy = str(process.get("context_policy", "clean_room"))
    if policy not in {"clean_room", "allow_precedent"}:
        raise ContextError("rf.process.context_policy must be clean_room or allow_precedent")
    features = _features(rf) if rf["enabled"] else []
    allowed = CLEAN_ROOM if policy == "clean_room" else ALLOWED_PROVENANCE
    cards = _validate_archive(archive)
    selected = [row for row in cards
                if row["provenance"] in allowed
                and set(row["selectors"]) & set(features)]
    selected.sort(key=lambda row: row["id"])
    adopted_claim_ids = []
    if process.get("profile") == "rf-module-v1":
        bend = (((rf.get("layout_constraints") or {}).get("route") or {})
                .get("bend_policy") or {})
        adopted_claim_ids = [str(value) for value in
                             bend.get("source_claim_ids") or []]
        missing_claims = sorted(set(adopted_claim_ids)
                                - {row["id"] for row in selected})
        if missing_claims:
            raise ContextError(
                f"adopted RF source claim IDs were not selected: {missing_claims}")
    if rf["enabled"]:
        required_topics = {"controlled_impedance"}
        if "via_fence" in features:
            required_topics.add("via_fence")
        if "bend_geometry" in features:
            required_topics.add("bend_geometry")
        coverage = {topic: sorted(row["id"] for row in selected
                                  if topic in row["topics"])
                    for topic in sorted(required_topics)}
        missing = [topic for topic, ids in coverage.items() if not ids]
        if missing:
            raise ContextError(f"source-card coverage missing topics {missing}")
    else:
        coverage = {}
    return {
        "schema": 1,
        "status": "ACTIVE" if rf["enabled"] else "N-A",
        "profile": profile,
        "context_policy": policy,
        "features": features,
        "coverage": coverage,
        "selected_source_ids": [row["id"] for row in selected],
        "adopted_source_claim_ids": sorted(adopted_claim_ids),
        "sources": selected,
        "runtime_network": False,
        "review_wait_created": False,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", type=Path)
    ap.add_argument("--contract", type=Path)
    ap.add_argument("--archive", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    project = args.project.resolve()
    contract_path = (args.contract.resolve() if args.contract else
                     project / "03_src/rules/rf.yaml")
    archive_path = (args.archive.resolve() if args.archive else
                    Path(__file__).resolve().parents[1] /
                    "references/rf/source_cards.yaml")
    out = (args.out.resolve() if args.out else project / "06_build/rf/context")
    try:
        contract = _load_yaml(contract_path, "RF contract")
        archive = _load_yaml(archive_path, "RF source-card archive")
        context = build_context(contract, archive)
        semantic = _canonical(context)
        raw = contract_path.read_bytes() + b"\0" + archive_path.read_bytes()
        out.parent.mkdir(parents=True, exist_ok=True)
        subject_hashes = {"semantic_sha256": _digest(semantic),
                          "raw_sha256": _digest(raw)}
        inputs = {"rf.yaml": contract_path, "source_cards.yaml": archive_path}
        outputs = {"context.json": None, "report.txt": None}
        if fresh_bundle(out, subject_hashes, inputs, set(outputs),
                        producer="rf_context.py", producer_version=VERSION):
            count = len(context["sources"])
            print(f"RF-CONTEXT input: {contract_path}")
            print(f"RF-CONTEXT coverage: 1/1 context bundle; {count} source card(s)")
            print(f"RF-CONTEXT PASS: exact cached bundle -> {out}")
            return 0
        txn = ArtifactBundleTransaction(
            out, producer="rf_context.py", producer_version=VERSION,
            subject=subject_hashes, inputs=inputs, outputs=outputs)

        def produce(staging: Path):
            (staging / "context.json").write_bytes(
                json.dumps(context, indent=2, sort_keys=True).encode() + b"\n")
            covered = sum(bool(v) for v in context["coverage"].values())
            total = len(context["coverage"])
            lines = [
                f"input: {contract_path}",
                f"status: {context['status']}",
                f"policy: {context['context_policy']}",
                f"features: {', '.join(context['features']) or 'none'}",
                f"sources: {len(context['sources'])}",
                f"coverage: {covered}/{total} required topics",
                "network: disabled",
                "review_wait: none",
                "VERDICT: PASS",
            ]
            (staging / "report.txt").write_text("\n".join(lines) + "\n")

        published = txn.publish(produce)
    except (ContextError, OSError, ValueError) as exc:
        print(f"RF-CONTEXT coverage: 0/1 context bundle")
        print(f"RF-CONTEXT FAIL: {exc}")
        return 1
    count = len(context["sources"])
    print(f"RF-CONTEXT input: {contract_path}")
    print(f"RF-CONTEXT coverage: 1/1 context bundle; {count} source card(s)")
    print(f"RF-CONTEXT PASS: {context['status']} -> {published.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
