#!/usr/bin/env python3
"""Content-addressed, terminal-state store for routing experiments.

An experiment is recorded once as ACCEPTED, REJECTED, or INCOMPLETE. Retained
files are copied into the store by hash; manifests and the accepted pointer use
relative paths, so the store survives relocation and needs no `/tmp` state.
Pruning is report-only: deletion remains an explicit operator action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any


OUTCOMES = {"ACCEPTED", "REJECTED", "INCOMPLETE"}
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic(path: Path, value: dict[str, Any], *, exclusive=False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise ValueError(f"refusing to replace existing terminal state: {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    if exclusive:
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ValueError(f"terminal state appeared concurrently: {path}") from exc
        finally:
            temporary.unlink(missing_ok=True)
    else:
        os.replace(temporary, path)


def _object(store: Path, source: Path) -> dict[str, Any]:
    source = source.resolve()
    if not source.is_file():
        raise ValueError(f"retained artifact is missing: {source}")
    digest = _sha(source)
    suffix = "".join(source.suffixes)[-48:]
    relative = Path("objects") / digest[:2] / f"{digest}{suffix}"
    target = store / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and _sha(target) != digest:
        raise ValueError(f"content-address collision at {target}")
    if not target.exists():
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        shutil.copy2(source, temporary)
        if _sha(temporary) != digest:
            temporary.unlink(missing_ok=True)
            raise ValueError(f"copy changed bytes for {source}")
        os.replace(temporary, target)
    return {"name": source.name, "path": relative.as_posix(),
            "sha256": digest, "size": source.stat().st_size}


def record(store: Path, experiment_id: str, outcome: str, parent: str,
           retained: list[Path], receipt: Path | None = None,
           command: str = "") -> dict[str, Any]:
    store = store.resolve()
    if not ID_RE.fullmatch(experiment_id):
        raise ValueError("experiment id must be 1-128 safe filename characters")
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(OUTCOMES)}")
    manifest_path = store / "experiments" / f"{experiment_id}.json"
    lock_fd = None
    lock = store / ".accepted.lock"
    try:
        if outcome == "ACCEPTED":
            store.mkdir(parents=True, exist_ok=True)
            try:
                lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ValueError("another accepted promotion is in progress") from exc
            pointer = store / "accepted.json"
            if pointer.exists():
                current = json.loads(pointer.read_text(encoding="utf-8-sig"))
                if current.get("id") != experiment_id:
                    raise ValueError(
                        f"accepted candidate already exists: {current.get('id')}; "
                        "explicit promotion/replacement is required")
        if manifest_path.exists():
            raise ValueError(f"experiment already has terminal state: {experiment_id}")
        files = [_object(store, path) for path in retained]
        receipt_record = _object(store, receipt) if receipt else None
        manifest = {
            "schema": 1, "id": experiment_id, "outcome": outcome,
            "parent": parent, "command": command,
            "receipt": receipt_record, "retained": files,
        }
        _atomic(manifest_path, manifest, exclusive=True)
        if outcome == "ACCEPTED" and not pointer.exists():
            _atomic(pointer, {"schema": 1, "id": experiment_id,
                              "manifest": f"experiments/{experiment_id}.json"},
                    exclusive=True)
        return manifest
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            lock.unlink(missing_ok=True)


def verify(store: Path, experiment_id: str) -> tuple[bool, list[str]]:
    store = store.resolve()
    failures = []
    path = store / "experiments" / f"{experiment_id}.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"cannot read manifest: {exc}"]
    if manifest.get("schema") != 1 or manifest.get("id") != experiment_id \
            or manifest.get("outcome") not in OUTCOMES:
        failures.append("manifest identity/outcome is invalid")
    records = list(manifest.get("retained") or [])
    if manifest.get("receipt"):
        records.append(manifest["receipt"])
    for record_row in records:
        relative = Path(str(record_row.get("path") or ""))
        if relative.is_absolute() or ".." in relative.parts:
            failures.append(f"object path escapes store: {relative}")
            continue
        object_path = store / relative
        if not object_path.is_file():
            failures.append(f"object missing: {relative}")
        elif _sha(object_path) != record_row.get("sha256"):
            failures.append(f"object changed: {relative}")
    return not failures, failures


def prune_report(store: Path) -> dict[str, Any]:
    store = store.resolve()
    referenced = set()
    for manifest_path in (store / "experiments").glob("*.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        rows = list(manifest.get("retained") or [])
        if manifest.get("receipt"):
            rows.append(manifest["receipt"])
        referenced.update(str(row.get("path")) for row in rows)
    existing = {path.relative_to(store).as_posix()
                for path in (store / "objects").glob("**/*") if path.is_file()}
    return {"schema": 1, "mode": "DRY-RUN", "referenced": len(referenced),
            "unreferenced": sorted(existing - referenced)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command_name", required=True)
    add = sub.add_parser("record")
    add.add_argument("store", type=Path)
    add.add_argument("--id", required=True)
    add.add_argument("--outcome", choices=sorted(OUTCOMES), required=True)
    add.add_argument("--parent", required=True)
    add.add_argument("--receipt", type=Path)
    add.add_argument("--retain", action="append", type=Path, default=[])
    add.add_argument("--command", default="")
    check = sub.add_parser("verify")
    check.add_argument("store", type=Path)
    check.add_argument("id")
    prune = sub.add_parser("prune-dry-run")
    prune.add_argument("store", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command_name == "record":
            result = record(args.store, args.id, args.outcome, args.parent,
                            args.retain, args.receipt, args.command)
            print(f"ROUTE-EXPERIMENT {result['outcome']}: {result['id']}")
            return 0
        if args.command_name == "verify":
            valid, failures = verify(args.store, args.id)
            for failure in failures:
                print(f"  FAIL {failure}")
            print(f"ROUTE-EXPERIMENT VERIFY {'PASS' if valid else 'FAIL'}")
            print("coverage: terminal manifest and every retained object hash graded")
            return 0 if valid else 1
        result = prune_report(args.store)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ROUTE-EXPERIMENT INCOMPLETE: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
