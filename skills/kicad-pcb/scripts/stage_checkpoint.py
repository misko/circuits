#!/usr/bin/env python3
"""Record and verify exact files at a deliberate pipeline pause.

This is not a design gate.  It preserves the identity of artifacts already
graded by earlier gates so a human-review pause can resume without rebuilding
and silently changing the reviewed subject.

Usage:
    stage_checkpoint.py record PROJECT NAME --input PATH [--input PATH ...]
    stage_checkpoint.py verify PROJECT NAME
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_path(project, name):
    return project / "06_build" / "checkpoints" / f"{name}.json"


def resolve_input(project, raw):
    path = Path(raw)
    if not path.is_absolute():
        path = project / path
    path = path.resolve()
    try:
        relative = path.relative_to(project)
    except ValueError as exc:
        raise ValueError(f"input escapes project root: {raw}") from exc
    if not path.is_file():
        raise ValueError(f"input is missing or not a regular file: {relative}")
    return path, relative.as_posix()


def cmd_record(args):
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"CHECKPOINT FAIL: project does not exist: {project}")
        return 1
    if not args.input:
        print("CHECKPOINT FAIL: zero inputs would preserve no artifact identity")
        return 1

    entries = {}
    failures = []
    for raw in args.input:
        try:
            path, relative = resolve_input(project, raw)
        except ValueError as exc:
            failures.append(str(exc))
            continue
        if relative in entries:
            failures.append(f"duplicate input: {relative}")
            continue
        entries[relative] = {
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"CHECKPOINT FAIL (record): {len(failures)} finding(s)")
        return 1

    output = record_path(project, args.name)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": 1,
        "name": args.name,
        "project": project.name,
        "files": dict(sorted(entries.items())),
    }
    temporary = output.with_suffix(f"{output.suffix}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, output)
    print(f"CHECKPOINT PASS (record): {len(entries)}/{len(entries)} file(s) pinned "
          f"in {output.relative_to(project)}")
    return 0


def cmd_verify(args):
    project = Path(args.project).resolve()
    checkpoint = record_path(project, args.name)
    if not checkpoint.is_file():
        print(f"CHECKPOINT FAIL (verify): missing {checkpoint}; run the full "
              "pipeline to create the review subject before resuming")
        return 1
    try:
        payload = json.loads(checkpoint.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"CHECKPOINT FAIL (verify): cannot parse {checkpoint}: {exc}")
        return 1

    failures = []
    files = payload.get("files")
    if payload.get("schema") != 1 or payload.get("name") != args.name or \
            payload.get("project") != project.name or not isinstance(files, dict) or \
            not files:
        failures.append("record schema/name/project/files are invalid or empty")
        files = files if isinstance(files, dict) else {}

    for relative, expected in sorted(files.items()):
        path = (project / relative).resolve()
        try:
            path.relative_to(project)
        except ValueError:
            failures.append(f"recorded path escapes project root: {relative}")
            continue
        if not path.is_file():
            failures.append(f"recorded input is missing: {relative}")
            continue
        actual_hash = sha256_file(path)
        actual_size = path.stat().st_size
        if actual_hash != expected.get("sha256") or actual_size != expected.get("size"):
            failures.append(
                f"recorded input changed: {relative} "
                f"({str(expected.get('sha256', ''))[:12]} -> {actual_hash[:12]})")

    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"CHECKPOINT FAIL (verify): {len(failures)} finding(s) over "
              f"{len(files)} recorded file(s); rerun the full schematic stage")
        return 1
    print(f"CHECKPOINT PASS (verify): {len(files)}/{len(files)} reviewed-stage "
          "file(s) are byte-identical")
    return 0


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record")
    record.add_argument("project")
    record.add_argument("name")
    record.add_argument("--input", action="append", required=True)
    record.set_defaults(function=cmd_record)
    verify = commands.add_parser("verify")
    verify.add_argument("project")
    verify.add_argument("name")
    verify.set_defaults(function=cmd_verify)
    return root


def main():
    args = parser().parse_args()
    return args.function(args)


if __name__ == "__main__":
    sys.exit(main())
