#!/usr/bin/env python3
"""PR-REVIEW: require independent schematic/placement evidence before routing.

The final release reviews still grade the routed, staged artifact.  This gate
exists so datasheet authority, topology, placement, and render defects do not
first appear after routing.  Review files are data: each carries a closed
``design_verdict`` and hashes of the exact artifact(s) it reviewed.  KiCad's
legacy netlist exporter rewrites its export clock and schematic-instance UUIDs
on every invocation.  Those fields carry no electrical meaning, so the
topology hash normalizes only that volatile metadata; every component, value,
footprint, property, net, node, and pin byte remains bound by the review.

VACUITY: this checker can prove that named review bytes are current and say
SOUND; it cannot prove the reviewer was genuinely independent or competent.
The review protocol and provenance header remain human controls.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PR-REVIEW: PyYAML is required")


FIELD = re.compile(r"^[>\s*#`-]*([a-z][a-z0-9_-]*)\s*:\s*(.*?)\s*$", re.I)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def netlist_digest(path: Path) -> str:
    """Hash exact electrical netlist bytes without KiCad export churn."""
    text = path.read_text(encoding="utf-8-sig")
    text, dates = re.subn(
        r'(\(date\s+")[^"]*(")',
        r'\1<KICAD_EXPORT_DATE>\2',
        text,
        count=1,
    )
    text, _stamps = re.subn(
        r'(\(tstamps\s+")[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-'
        r'[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(")',
        r'\1<KICAD_INSTANCE_UUID>\2',
        text,
    )
    if dates != 1:
        raise ValueError(
            f"expected exactly one KiCad export date in {path}, found {dates}")
    return hashlib.sha256(text.encode()).hexdigest()


def design_rules_digest(project: Path) -> str | None:
    """Bind reviews to adopted requirement/rule bytes, not just artifacts."""
    requirements = project / "03_src/rules/requirements.yaml"
    if not requirements.is_file():
        return None
    files = sorted((project / "03_src/rules").glob("*.yaml"))
    route = project / "03_src/route.yaml"
    if route.is_file():
        files.append(route)
    return hashlib.sha256(b"".join(
        p.relative_to(project).as_posix().encode() + b"\0" + p.read_bytes() + b"\0"
        for p in files)).hexdigest()


def fields(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = FIELD.match(line)
        if match:
            out[match.group(1).lower()] = match.group(2).strip().strip("`*")
    return out


def config(project: Path) -> dict:
    path = project / "03_src/route.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    return ((doc.get("flow") or {}).get("pre_route_reviews") or {})


def resolve(project: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project / path


def check_review(kind: str, path: Path, expected: dict[str, str], errors: list[str]) -> bool:
    if not path.is_file():
        errors.append(f"{kind}: missing review {path}")
        return False
    doc = fields(path)
    if doc.get("review_stage", "").lower() != "pre-route":
        errors.append(f"{kind}: review_stage must be pre-route in {path}")
    if doc.get("review_kind", "").lower() != kind:
        errors.append(f"{kind}: review_kind must be {kind} in {path}")
    if doc.get("design_verdict", "").upper() != "SOUND":
        errors.append(f"{kind}: design_verdict is not SOUND in {path}")
    for key, wanted in expected.items():
        if doc.get(key, "").lower() != wanted.lower():
            errors.append(f"{kind}: {key} is stale or missing in {path}")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--phase", required=True, choices=("schematic", "placement"))
    ap.add_argument("--board")
    ap.add_argument("--netlist")
    args = ap.parse_args(argv)

    project = Path(args.project).resolve()
    cfg = config(project)
    if not cfg:
        print(f"PR-REVIEW coverage: 0/{1 if args.phase == 'schematic' else 4} "
              "required review artifact(s) graded")
        print("PR-REVIEW UNMIGRATED: flow.pre_route_reviews is absent; this is not a pass")
        return 2

    errors: list[str] = []
    expected_reviews = 1 if args.phase == "schematic" else 4
    graded_reviews = 0
    parts = sorted((project / "02_parts").glob("*/part.yaml"))
    if not parts:
        errors.append("no part.yaml files found")
    parts_hash = hashlib.sha256(b"".join(
        p.relative_to(project).as_posix().encode() + b"\0" + p.read_bytes() + b"\0"
        for p in parts)).hexdigest()
    rules_hash = design_rules_digest(project)

    if args.phase == "schematic":
        netlist = resolve(project, args.netlist or cfg.get("netlist", ""))
        if not netlist.is_file():
            errors.append(f"missing netlist {netlist}")
        else:
            try:
                netlist_hash = netlist_digest(netlist)
            except (OSError, UnicodeError, ValueError) as exc:
                errors.append(f"cannot canonicalize netlist {netlist}: {exc}")
                netlist_hash = ""
            expected = {"netlist_sha256": netlist_hash,
                        "parts_sha256": parts_hash}
            if rules_hash:
                expected["design_rules_sha256"] = rules_hash
            value = cfg.get("topology")
            if not value:
                errors.append("flow.pre_route_reviews.topology is missing")
            else:
                graded_reviews += check_review(
                    "topology", resolve(project, value), expected, errors)
    else:
        board = resolve(project, args.board or cfg.get("board", ""))
        if not board.is_file():
            errors.append(f"missing board {board}")
        else:
            board_hash = digest(board)
            for kind in ("pin", "layout", "render"):
                value = cfg.get(kind)
                if not value:
                    errors.append(f"flow.pre_route_reviews.{kind} is missing")
                    continue
                expected = {"board_sha256": board_hash}
                if rules_hash:
                    expected["design_rules_sha256"] = rules_hash
                if kind == "pin":
                    expected["parts_sha256"] = parts_hash
                graded_reviews += check_review(
                    kind, resolve(project, value), expected, errors)

            value = cfg.get("a_render")
            if not value:
                errors.append("flow.pre_route_reviews.a_render is missing")
            else:
                path = resolve(project, value)
                if not path.is_file():
                    errors.append(f"A-RENDER: missing report {path}")
                else:
                    graded_reviews += 1
                    doc = fields(path)
                    if doc.get("a-render_verdict", "").upper() != "PASS":
                        errors.append(f"A-RENDER: verdict is not PASS in {path}")
                    if doc.get("board_sha256", "").lower() != board_hash:
                        errors.append(f"A-RENDER: board_sha256 is stale or missing in {path}")

    print(f"PR-REVIEW coverage: {graded_reviews}/{expected_reviews} "
          "required review artifact(s) graded")
    if errors:
        for item in errors:
            print(f"FAIL PR-REVIEW: {item}")
        print(f"PR-REVIEW FAIL: {len(errors)} finding(s)")
        return 1
    print(f"PR-REVIEW PASS ({args.phase}): exact pre-route evidence is SOUND and current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
