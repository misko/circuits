#!/usr/bin/env python3
"""Project-level P-MODEL-REG orchestrator for native model registrations."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

import yaml


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project")
    parser.add_argument("--board", required=True)
    parser.add_argument("--out", default="06_build/pre_route/model_registration.md")
    args = parser.parse_args(argv)

    project = Path(args.project).resolve()
    board = (project / args.board).resolve()
    config_path = project / "03_src/rules/model_registration.yaml"
    if not config_path.is_file():
        print("P-MODEL-REG N-A: no 03_src/rules/model_registration.yaml")
        return 0
    config = yaml.safe_load(config_path.read_text(encoding="utf-8-sig")) or {}
    if config.get("schema") != 1:
        raise SystemExit("P-MODEL-REG schema must be 1")
    groups = config.get("groups")
    if not isinstance(groups, list) or not groups:
        raise SystemExit("P-MODEL-REG groups must be a non-empty list")
    if not board.is_file():
        raise SystemExit(f"P-MODEL-REG board does not exist: {board}")

    engine = Path(__file__).with_name("native_model_registration.py")
    build = project / "06_build/pre_route/native_registration"
    build.mkdir(parents=True, exist_ok=True)
    seen_ids = set()
    rows = []
    failed = False
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise SystemExit(f"P-MODEL-REG groups[{index}] must be a mapping")
        group_id = str(group.get("id", "")).strip()
        if not group_id or group_id in seen_ids or "/" in group_id or ".." in group_id:
            raise SystemExit(f"P-MODEL-REG invalid/duplicate group id: {group_id!r}")
        seen_ids.add(group_id)
        refs = group.get("refs")
        if isinstance(refs, list):
            refs = ",".join(str(ref) for ref in refs)
        if not isinstance(refs, str) or not refs.strip():
            raise SystemExit(f"P-MODEL-REG {group_id}: refs must be non-empty")
        model_sha = str(group.get("model_sha256", "")).lower()
        if len(model_sha) != 64 or any(ch not in "0123456789abcdef" for ch in model_sha):
            raise SystemExit(f"P-MODEL-REG {group_id}: invalid model_sha256")
        outdir = build / group_id
        command = [
            sys.executable, str(engine), str(board), str(outdir),
            "--refs", refs, "--model-sha256", model_sha,
            "--fit-tol-mm", str(float(group.get("fit_tolerance_mm", 1.0))),
            "--courtyard-tol-mm",
            str(float(group.get("courtyard_containment_tolerance_mm", 0.25))),
            "--search-margin-mm", str(float(group.get("search_margin_mm", 8.0))),
            "--width", str(int(group.get("render_width", 2400))),
            "--height", str(int(group.get("render_height", 1600))),
        ]
        result = subprocess.run(command, text=True, capture_output=True)
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        report = outdir / "native_model_registration.md"
        if result.returncode or not report.is_file():
            failed = True
        rows.append((group_id, refs, model_sha, report, result.returncode))

    output = (project / args.out).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Project native model physical registration",
        "",
        f"board_sha256: {digest(board)}",
        f"a-render_verdict: {'FAIL' if failed else 'PASS'}",
        "registration_kind: P-MODEL-REG",
        f"config_sha256: {digest(config_path)}",
        "",
        "This aggregate is independent physical-registration evidence. Each "
        "group compares native-model pixels with F.Fab, F.CrtYd, and drilled "
        "attachment datums. Catalog-twin renderer fidelity is a separate gate.",
        "",
        "| group | refs | model SHA-256 | group report | result |",
        "|---|---|---|---|---|",
    ]
    for group_id, refs, model_sha, report, returncode in rows:
        relative = report.relative_to(project).as_posix()
        lines.append(
            f"| {group_id} | {refs} | `{model_sha}` | `{relative}` | "
            f"{'PASS' if returncode == 0 and report.is_file() else 'FAIL'} |"
        )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"P-MODEL-REG {'FAIL' if failed else 'PASS'}: {len(rows)}/{len(rows)} "
        f"group(s) graded -> {output}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
