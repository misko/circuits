#!/usr/bin/env python3
"""RF-CONTRACT: validate RF intent and exact-artifact review coverage.

RF work is conditional, but the condition is explicit.  A new project carries
``03_src/rules/rf.yaml`` with ``rf.enabled`` true or false.  When true, the
file names every RF port, cross-section, performance claim, first-article
measurement, and the exact artifacts/review files used by the three dedicated
RF review phases (schematic, PCB, fabrication output).

Review coverage is derived from requirement IDs, not trusted from a typed
count.  Every required ID must appear exactly once as
``requirement: <ID> PASS`` in the corresponding review, and the review must
bind the SHA256 of its declared artifact.  Zero requirements is a schema
failure, never a successful 0/0 review.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import yaml

PHASES = ("schematic", "pcb", "fab")
RISK_TIERS = {
    "ordinary-high-speed", "controlled-impedance", "phase-coherent",
    "microwave",
}
REVIEW_KIND = {
    "schematic": "RF_SCHEMATIC",
    "pcb": "RF_PCB",
    "fab": "RF_FAB",
}


class ContractError(RuntimeError):
    pass


def _mapping(value, label):
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a mapping")
    return value


def _nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def _substantive(value, label):
    text = _nonempty(value, label)
    if re.fullmatch(r"(?i)(tbd|todo|unknown|n/?a|none|pending)", text):
        raise ContractError(f"{label} must be substantive, not {text!r}")
    return text


def _list(value, label, minimum=1):
    if not isinstance(value, list) or len(value) < minimum:
        raise ContractError(f"{label} must be a list with >= {minimum} item(s)")
    return value


def _inside(project: Path, value, label) -> Path:
    path = (project / _nonempty(value, label)).resolve()
    try:
        path.relative_to(project)
    except ValueError as exc:
        raise ContractError(f"{label} must stay inside the project: {path}") from exc
    return path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _field(text: str, name: str) -> str:
    match = re.search(rf"(?im)^\s*{re.escape(name)}:\s*(.*?)\s*$", text)
    return match.group(1).strip() if match else ""


def _requirements(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2).upper()) for m in re.finditer(
        r"(?im)^\s*requirement:\s*([A-Za-z0-9_.-]+)\s+"
        r"(PASS|FAIL)\s*$", text)]


def load_contract(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        raise ContractError(f"cannot read {path}: {exc}") from exc
    root = _mapping(data, "rf.yaml root")
    if root.get("schema") != 1:
        raise ContractError("rf.yaml schema must be integer 1")
    rf = _mapping(root.get("rf"), "rf")
    if not isinstance(rf.get("enabled"), bool):
        raise ContractError("rf.enabled must be true or false")
    _nonempty(rf.get("rationale"), "rf.rationale")
    return root


def validate_enabled(project: Path, contract: dict,
                     required_phases=()) -> dict[str, dict]:
    rf = contract["rf"]
    tier = _nonempty(rf.get("risk_tier"), "rf.risk_tier")
    if tier not in RISK_TIERS:
        raise ContractError(
            f"rf.risk_tier {tier!r} is not one of {sorted(RISK_TIERS)}")
    _nonempty(rf.get("risk_basis"), "rf.risk_basis")

    ports = _list(rf.get("ports"), "rf.ports")
    port_ids = set()
    for index, raw in enumerate(ports):
        port = _mapping(raw, f"rf.ports[{index}]")
        ident = _nonempty(port.get("id"), f"rf.ports[{index}].id")
        if ident in port_ids:
            raise ContractError(f"duplicate RF port id {ident!r}")
        port_ids.add(ident)
        nets = _list(port.get("nets"), f"rf.ports[{index}].nets")
        for j, net in enumerate(nets):
            _nonempty(net, f"rf.ports[{index}].nets[{j}]")
        band = port.get("band_hz")
        if not isinstance(band, list) or len(band) != 2 \
                or not all(isinstance(v, (int, float)) for v in band) \
                or not 0 <= band[0] < band[1]:
            raise ContractError(
                f"rf.ports[{index}].band_hz must be [low, high], 0 <= low < high")
        if not isinstance(port.get("z0_ohm"), (int, float)) \
                or not 20 <= float(port["z0_ohm"]) <= 150:
            raise ContractError(f"rf.ports[{index}].z0_ohm must be 20..150")
        for key in ("launch", "termination", "reference_layer"):
            _nonempty(port.get(key), f"rf.ports[{index}].{key}")

    sections = _list(rf.get("cross_sections"), "rf.cross_sections")
    section_ids = set()
    pending_sections = []
    for index, raw in enumerate(sections):
        section = _mapping(raw, f"rf.cross_sections[{index}]")
        ident = _nonempty(section.get("id"), f"rf.cross_sections[{index}].id")
        if ident in section_ids:
            raise ContractError(f"duplicate RF cross-section id {ident!r}")
        section_ids.add(ident)
        for key in ("stackup_source", "solver", "copper_layer",
                    "reference_layer"):
            _nonempty(section.get(key), f"rf.cross_sections[{index}].{key}")
        for key in ("dielectric_height_mm", "dk", "target_z0_ohm"):
            if not isinstance(section.get(key), (int, float)) \
                    or float(section[key]) <= 0:
                raise ContractError(
                    f"rf.cross_sections[{index}].{key} must be > 0")
        status = section.get("status", "locked")
        if status not in ("locked", "pending_solver"):
            raise ContractError(
                f"rf.cross_sections[{index}].status must be locked or "
                "pending_solver")
        if status == "pending_solver":
            _substantive(section.get("deferred_until"),
                         f"rf.cross_sections[{index}].deferred_until")
            _substantive(section.get("reason"),
                         f"rf.cross_sections[{index}].reason")
            for key in ("width_mm", "gap_mm"):
                if section.get(key) is not None:
                    raise ContractError(
                        f"rf.cross_sections[{index}].{key} must be null while "
                        "status is pending_solver; do not publish an "
                        "unapproved geometry")
            pending_sections.append(ident)
        else:
            for key in ("width_mm", "gap_mm"):
                if not isinstance(section.get(key), (int, float)) \
                        or float(section[key]) <= 0:
                    raise ContractError(
                        f"rf.cross_sections[{index}].{key} must be > 0 when "
                        "status is locked")

    claims = _list(rf.get("performance_claims"), "rf.performance_claims")
    claim_ids = set()
    for index, raw in enumerate(claims):
        claim = _mapping(raw, f"rf.performance_claims[{index}]")
        ident = _nonempty(claim.get("id"),
                          f"rf.performance_claims[{index}].id")
        if ident in claim_ids:
            raise ContractError(f"duplicate RF performance claim id {ident!r}")
        claim_ids.add(ident)
        for key in ("claim", "acceptance", "evidence"):
            _substantive(claim.get(key),
                         f"rf.performance_claims[{index}].{key}")

    first = _mapping(rf.get("first_article"), "rf.first_article")
    for key in ("measurements", "acceptance"):
        values = _list(first.get(key), f"rf.first_article.{key}")
        for index, value in enumerate(values):
            _substantive(value, f"rf.first_article.{key}[{index}]")

    reviews = _mapping(rf.get("reviews"), "rf.reviews")
    normalized = {}
    all_requirement_ids = set()
    for phase in PHASES:
        spec = _mapping(reviews.get(phase), f"rf.reviews.{phase}")
        review_path = _inside(project, spec.get("path"),
                              f"rf.reviews.{phase}.path")
        artifact = _inside(project, spec.get("artifact"),
                           f"rf.reviews.{phase}.artifact")
        reqs = _list(spec.get("requirements"),
                     f"rf.reviews.{phase}.requirements")
        cleaned = []
        for index, requirement in enumerate(reqs):
            ident = _nonempty(
                requirement, f"rf.reviews.{phase}.requirements[{index}]")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", ident):
                raise ContractError(f"invalid RF requirement id {ident!r}")
            if ident in cleaned:
                raise ContractError(
                    f"duplicate {phase} review requirement {ident!r}")
            if ident in all_requirement_ids:
                raise ContractError(
                    f"RF requirement id {ident!r} is reused across phases")
            cleaned.append(ident)
            all_requirement_ids.add(ident)
        normalized[phase] = {
            "path": review_path, "artifact": artifact,
            "requirements": cleaned,
        }
    if pending_sections and any(
            phase in ("pcb", "fab") for phase in required_phases):
        raise ContractError(
            "RF cross-section solver remains pending for "
            f"{pending_sections}; PCB/fab review cannot proceed until every "
            "width/gap is locked")
    return normalized


def _commit_error(project: Path, commit: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        return "source_commit must be a full SHA"
    context = project
    probe = subprocess.run(
        ["git", "-C", str(context), "rev-parse", "--show-toplevel"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if probe.returncode:
        context = Path(__file__).resolve().parents[3]
    cp = subprocess.run(
        ["git", "-C", str(context), "cat-file", "-e", f"{commit}^{{commit}}"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if cp.returncode:
        return f"source_commit {commit} does not identify a commit"
    cp = subprocess.run(
        ["git", "-C", str(context), "merge-base", "--is-ancestor",
         commit, "HEAD"], text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    if cp.returncode:
        return f"source_commit {commit} is not an ancestor of HEAD"
    return ""


def review_errors(project: Path, phase: str, spec: dict) -> list[str]:
    review, artifact = spec["path"], spec["artifact"]
    errors = []
    if not artifact.is_file():
        return [f"RF-{phase.upper()}-ARTIFACT: missing {artifact}"]
    if not review.is_file():
        return [f"RF-{phase.upper()}-REVIEW: missing {review}"]
    text = review.read_text(encoding="utf-8-sig", errors="replace")
    expected_kind = REVIEW_KIND[phase]
    if _field(text, "review_kind").upper() != expected_kind:
        errors.append(f"RF-{phase.upper()}-KIND: review_kind must be {expected_kind}")
    if _field(text, "independence").lower() != "independent-from-design-author":
        errors.append(
            f"RF-{phase.upper()}-INDEPENDENCE: independence must be "
            "independent-from-design-author")
    if not _field(text, "subject") or not _field(text, "reviewer"):
        errors.append(f"RF-{phase.upper()}-HEADER: subject and reviewer are required")
    commit = _field(text, "source_commit")
    commit_error = _commit_error(project, commit)
    if commit_error:
        errors.append(f"RF-{phase.upper()}-COMMIT: {commit_error}")
    actual_hash = _sha256(artifact)
    bound_hash = _field(text, "artifact_sha256").lower()
    if bound_hash != actual_hash:
        errors.append(
            f"RF-{phase.upper()}-BINDING: artifact_sha256 is "
            f"{bound_hash or 'UNSTATED'}, expected {actual_hash}")
    verdict_key = "fab_package_verdict" if phase == "fab" else "design_verdict"
    verdict_want = "READY" if phase == "fab" else "SOUND"
    if _field(text, verdict_key).upper() != verdict_want:
        errors.append(
            f"RF-{phase.upper()}-VERDICT: {verdict_key} must be {verdict_want}")

    rows = _requirements(text)
    seen = [ident for ident, _ in rows]
    expected = spec["requirements"]
    duplicates = sorted({ident for ident in seen if seen.count(ident) > 1})
    missing = sorted(set(expected) - set(seen))
    extra = sorted(set(seen) - set(expected))
    failed = sorted(ident for ident, verdict in rows if verdict != "PASS")
    if duplicates or missing or extra or failed or len(rows) != len(expected):
        errors.append(
            f"RF-{phase.upper()}-COVERAGE: graded {len(rows)}/{len(expected)}; "
            f"missing={missing}, extra={extra}, duplicate={duplicates}, fail={failed}")
    return errors


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("project", type=Path)
    p.add_argument("--contract", type=Path,
                   help="explicit board-scoped rf.yaml")
    p.add_argument("--require-review", action="append", choices=PHASES,
                   default=[])
    p.add_argument("--require-applicability", action="store_true",
                   help="fail when the project has no explicit rf.yaml")
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    project = args.project.resolve()
    contract_path = (args.contract.resolve() if args.contract else
                     project / "03_src" / "rules" / "rf.yaml")
    if not contract_path.is_file():
        if args.require_applicability:
            print(f"RF-CONTRACT FAIL: no explicit applicability contract at "
                  f"{contract_path}")
            return 1
        print(f"RF-CONTRACT UNMIGRATED: no {contract_path}; legacy project, "
              "not an RF-review pass")
        return 0
    try:
        contract = load_contract(contract_path)
        rf = contract["rf"]
        if not rf["enabled"]:
            print("RF-CONTRACT PASS: applicability 1/1; RF disabled with rationale; "
                  "dedicated RF reviews are N-A")
            return 0
        phases = list(dict.fromkeys(args.require_review))
        reviews = validate_enabled(project, contract, phases)
        errors = []
        for phase in phases:
            phase_errors = review_errors(project, phase, reviews[phase])
            if phase_errors:
                errors.extend(phase_errors)
            else:
                count = len(reviews[phase]["requirements"])
                print(f"RF-REVIEW {phase}: PASS {count}/{count} requirements; "
                      f"exact artifact {reviews[phase]['artifact']}")
    except ContractError as exc:
        print(f"RF-CONTRACT FAIL: {exc}")
        return 2
    print("RF-CONTRACT coverage: 1 applicability decision; "
          f"{len(rf['ports'])} port(s), {len(rf['cross_sections'])} "
          f"cross-section(s), {len(rf['performance_claims'])} claim(s); "
          f"{len(phases)}/3 review phase(s) requested")
    if errors:
        for error in errors:
            print(f"  {error}")
        print(f"RF-CONTRACT FAIL: {len(errors)} finding(s)")
        return 1
    print("RF-CONTRACT PASS: RF intent is complete" +
          (" and requested reviews are exact-artifact-bound" if phases else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
