#!/usr/bin/env python3
"""Record, render, and verify one canonical PCB pipeline pause state.

The machine manifest is authority. `01_docs/STATUS.md` and root `RESUME.md`
are generated views carrying the same semantic state id; plausible but stale
prose therefore fails verification instead of competing for operator trust.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(content)
    os.replace(temporary, path)


def _project_file(project: Path, raw: str) -> tuple[Path, str]:
    path = Path(raw)
    path = (path if path.is_absolute() else project / path).resolve()
    try:
        relative = path.relative_to(project).as_posix()
    except ValueError as exc:
        raise ValueError(f"path escapes project: {raw}") from exc
    if not path.is_file():
        raise ValueError(f"referenced file is missing: {relative}")
    return path, relative


def _record(path: Path, relative: str) -> dict[str, Any]:
    return {"path": relative, "sha256": _sha(path), "size": path.stat().st_size}


def _state_id(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _render(payload: dict[str, Any]) -> tuple[str, str]:
    marker = f"<!-- pause-state:{payload['state_id']} -->"
    receipts = "\n".join(
        f"- `{row['path']}` — `{row['sha256'][:12]}`"
        for row in payload["receipts"]) or "- None"
    status = f"""# Project status

{marker}

- Phase: `{payload['phase']}`
- State: **PAUSED**
- Checkpoint: `{payload['checkpoint']['path']}` (`{payload['checkpoint']['sha256'][:12]}`)
- Blocker: {payload['blocker']}
- Next command: `{payload['next_command']}`

## Bound receipts

{receipts}

This file is generated from `01_docs/pause_state.json`; edit the manifest with
`pause_state.py record`, not this view.
"""
    resume = f"""# Resume

{marker}

Canonical state: `01_docs/pause_state.json`

1. Verify: `python3 skills/pcb-design/scripts/pause_state.py verify .`
2. Confirm blocker: {payload['blocker']}
3. Resume with: `{payload['next_command']}`

The authenticated checkpoint is `{payload['checkpoint']['path']}` at
`{payload['checkpoint']['sha256']}`.
"""
    return status, resume


def record(project: Path, phase: str, checkpoint: str, blocker: str,
           next_command: str, receipts: list[str]) -> dict[str, Any]:
    project = project.resolve()
    if not project.is_dir() or not phase.strip() or not blocker.strip() \
            or not next_command.strip():
        raise ValueError("project, phase, blocker and next-command are required")
    checkpoint_path, checkpoint_rel = _project_file(project, checkpoint)
    receipt_rows = []
    for raw in receipts:
        path, relative = _project_file(project, raw)
        receipt_rows.append(_record(path, relative))
    body = {
        "schema": 1, "project": project.name, "phase": phase.strip(),
        "checkpoint": _record(checkpoint_path, checkpoint_rel),
        "receipts": sorted(receipt_rows, key=lambda row: row["path"]),
        "blocker": blocker.strip(), "next_command": next_command.strip(),
    }
    body["state_id"] = _state_id(body)
    manifest = project / "01_docs" / "pause_state.json"
    _atomic_text(manifest, json.dumps(body, indent=2, sort_keys=True) + "\n")
    status, resume = _render(body)
    _atomic_text(project / "01_docs" / "STATUS.md", status)
    _atomic_text(project / "RESUME.md", resume)
    return body


def verify(project: Path) -> tuple[bool, list[str]]:
    project = project.resolve()
    failures = []
    manifest = project / "01_docs" / "pause_state.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"cannot read canonical pause manifest: {exc}"]
    body = dict(payload)
    state_id = body.pop("state_id", None)
    if body.get("schema") != 1 or body.get("project") != project.name \
            or state_id != _state_id(body):
        failures.append("manifest schema/project/state id is invalid")
    for row in [body.get("checkpoint") or {}, *(body.get("receipts") or [])]:
        relative = str(row.get("path") or "")
        path = (project / relative).resolve()
        try:
            path.relative_to(project)
        except ValueError:
            failures.append(f"referenced path escapes project: {relative}")
            continue
        if not path.is_file():
            failures.append(f"referenced file is missing: {relative}")
        elif _sha(path) != row.get("sha256") or path.stat().st_size != row.get("size"):
            failures.append(f"referenced file changed: {relative}")
    marker = f"<!-- pause-state:{state_id} -->"
    for relative in ("01_docs/STATUS.md", "RESUME.md"):
        path = project / relative
        if not path.is_file() or marker not in path.read_text(encoding="utf-8-sig"):
            failures.append(f"generated view is missing or stale: {relative}")
    return not failures, failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command_name", required=True)
    add = sub.add_parser("record")
    add.add_argument("project", type=Path)
    add.add_argument("--phase", required=True)
    add.add_argument("--checkpoint", required=True)
    add.add_argument("--receipt", action="append", default=[])
    add.add_argument("--blocker", required=True)
    add.add_argument("--next-command", required=True)
    check = sub.add_parser("verify")
    check.add_argument("project", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command_name == "record":
            result = record(args.project, args.phase, args.checkpoint,
                            args.blocker, args.next_command, args.receipt)
            print(f"PAUSE-STATE PASS (record): {result['state_id']}")
            return 0
        valid, failures = verify(args.project)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"PAUSE-STATE {'PASS' if valid else 'FAIL'}")
        print("coverage: canonical manifest, checkpoint, receipts, STATUS and RESUME graded")
        return 0 if valid else 1
    except Exception as exc:
        print(f"PAUSE-STATE INCOMPLETE: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
