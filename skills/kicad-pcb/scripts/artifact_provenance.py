#!/usr/bin/env python3
"""M-PROV — bind major PCB artifacts to the inputs and stage that wrote them.

Usage:
  artifact_provenance.py begin PROJECT --stage NAME --input PATH --output PATH
  artifact_provenance.py finish PROJECT --stage NAME
  artifact_provenance.py audit PROJECT [--require-stage NAME]

G-INPUT: every verdict names the project manifest and every input/output path.
G-COVER: every verdict reports ``N/M artifacts verified``.
G-RED: tests/t1_pipeline_reliability.py mutates a recorded output and proves
this checker rejects it.

This is intentionally stage-sized provenance, not a receipt for every tiny
temporary.  A producer calls ``begin`` immediately before a meaningful stage
and ``finish`` immediately after it.  ``finish`` proves inputs did not move,
outputs exist, and each output was created or rewritten during this run.
``audit`` later proves the recorded bytes are still the bytes on disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import uuid
from pathlib import Path


MANIFEST = Path("06_build/artifact_provenance.json")
PENDING = Path("06_build/provenance")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def resolve(project: Path, value: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else project / path
    path = path.resolve()
    if path != project and project not in path.parents:
        raise ValueError(f"path escapes project: {value}")
    return path


def inventory(project: Path, values: list[str], require: bool) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for value in values:
        root = resolve(project, value)
        paths = ([root] if root.is_file() else
                 sorted(p for p in root.rglob("*") if p.is_file())
                 if root.is_dir() else [])
        if require and not paths:
            raise ValueError(f"input has no files: {value}")
        if not paths:
            key = root.relative_to(project).as_posix()
            out[key] = {"exists": False}
        for path in paths:
            key = path.relative_to(project).as_posix()
            stat = path.stat()
            out[key] = {
                "exists": True, "sha256": sha256_file(path),
                "size": stat.st_size, "mtime_ns": stat.st_mtime_ns,
            }
    return out


def pending_path(project: Path, stage: str) -> Path:
    if not stage or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for c in stage):
        raise ValueError("stage may contain only letters, numbers, dot, dash, underscore")
    return project / PENDING / f"{stage}.pending.json"


def cmd_begin(args) -> int:
    project = Path(args.project).resolve()
    inputs = inventory(project, args.input, True)
    outputs = inventory(project, args.output, False)
    record = {
        "schema": 1, "run_id": uuid.uuid4().hex, "stage": args.stage,
        "started_ns": time.time_ns(), "inputs_declared": args.input,
        "outputs_declared": args.output, "inputs": inputs,
        "outputs_before": outputs,
    }
    path = pending_path(project, args.stage)
    atomic_json(path, record)
    print(f"M-PROV BEGIN {args.stage}: {len(inputs)}/{len(inputs)} inputs "
          f"fingerprinted; outputs={args.output}; witness={path}")
    return 0


def cmd_finish(args) -> int:
    project = Path(args.project).resolve()
    path = pending_path(project, args.stage)
    if not path.is_file():
        print(f"M-PROV FAIL: 0/1 artifacts verified; no begin witness {path}")
        return 1
    rec = json.loads(path.read_text(encoding="utf-8-sig"))
    failures: list[str] = []
    now_inputs = inventory(project, rec["inputs_declared"], True)
    old_names = set(rec["inputs"])
    new_names = set(now_inputs)
    for name in sorted(new_names - old_names):
        failures.append(f"input added during stage: {name}")
    for name in sorted(old_names - new_names):
        failures.append(f"input removed during stage: {name}")
    for name, old in rec["inputs"].items():
        if name not in now_inputs or now_inputs[name].get("sha256") != old.get("sha256"):
            failures.append(f"input moved during stage: {name}")
    outputs = inventory(project, rec["outputs_declared"], False)
    for name, item in outputs.items():
        if not item.get("exists"):
            failures.append(f"output missing: {name}")
            continue
        before = rec.get("outputs_before", {}).get(name, {"exists": False})
        rewritten = (not before.get("exists") or
                     item.get("sha256") != before.get("sha256") or
                     item.get("mtime_ns", 0) >= rec["started_ns"])
        if not rewritten:
            failures.append(f"output was not written by this run: {name}")
    reached = sum(1 for item in outputs.values() if item.get("exists"))
    total = max(1, len(outputs))
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"M-PROV FAIL: {reached}/{total} artifacts verified; witness={path}")
        return 1

    rec.update({"phase": "finished", "finished_ns": time.time_ns(),
                "inputs": now_inputs, "outputs": outputs})
    manifest_path = project / MANIFEST
    manifest = {"schema": 1, "project": project.name, "stages": {}}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    manifest.setdefault("stages", {})[args.stage] = rec
    atomic_json(manifest_path, manifest)
    path.unlink()
    print(f"M-PROV PASS: {reached}/{total} artifacts verified for "
          f"{args.stage}; manifest={manifest_path}")
    return 0


def cmd_audit(args) -> int:
    project = Path(args.project).resolve()
    path = project / MANIFEST
    if not path.is_file():
        print(f"M-PROV FAIL: 0/1 artifacts verified; no manifest {path}")
        return 1
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    stages = manifest.get("stages") or {}
    required = args.require_stage or sorted(stages)
    failures: list[str] = []
    reached = total = 0
    for stage in required:
        rec = stages.get(stage)
        if rec is None:
            total += 1
            failures.append(f"required stage absent: {stage}")
            continue
        for group in ("inputs", "outputs"):
            for name, expected in rec.get(group, {}).items():
                total += 1
                file = project / name
                if not file.is_file():
                    failures.append(f"{stage} {group[:-1]} missing: {name}")
                    continue
                reached += 1
                actual = sha256_file(file)
                if actual != expected.get("sha256"):
                    failures.append(f"{stage} {group[:-1]} changed: {name} "
                                    f"({actual[:12]} != {expected.get('sha256', '')[:12]})")
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"M-PROV FAIL: {reached}/{max(1, total)} artifacts verified; "
              f"manifest={path}")
        return 1
    print(f"M-PROV PASS: {reached}/{max(1, total)} artifacts verified; "
          f"manifest={path}")
    return 0


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    begin = sub.add_parser("begin")
    begin.add_argument("project")
    begin.add_argument("--stage", required=True)
    begin.add_argument("--input", action="append", default=[], required=True)
    begin.add_argument("--output", action="append", default=[], required=True)
    begin.set_defaults(fn=cmd_begin)
    finish = sub.add_parser("finish")
    finish.add_argument("project")
    finish.add_argument("--stage", required=True)
    finish.set_defaults(fn=cmd_finish)
    audit = sub.add_parser("audit")
    audit.add_argument("project")
    audit.add_argument("--require-stage", action="append", default=[])
    audit.set_defaults(fn=cmd_audit)
    return ap


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.fn(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"M-PROV FAIL: 0/1 artifacts verified; {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
