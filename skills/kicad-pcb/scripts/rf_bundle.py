#!/usr/bin/env python3
"""Freshness helper for deterministic RF evidence bundles.

This is an optimization only: producers still use ``ArtifactBundleTransaction``
for every publication. Reusing an exact subject/input/output match keeps the
manifest hash stable, so a no-op rebuild does not invalidate a human review.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fresh_bundle(directory: Path, subject: Mapping[str, str],
                 inputs: Mapping[str, Path], outputs: set[str], *,
                 producer: str, producer_version: str) -> bool:
    manifest_path = directory / "bundle.json"
    try:
        if directory.is_symlink() or not manifest_path.is_file():
            return False
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        if (manifest.get("schema") != 1 or manifest.get("status") != "PASS"
                or manifest.get("producer") != producer
                or str(manifest.get("producer_version")) != producer_version
                or manifest.get("subject") != dict(subject)):
            return False
        recorded_inputs = manifest.get("inputs") or {}
        if set(recorded_inputs) != set(inputs):
            return False
        for name, path in inputs.items():
            if (not path.is_file() or path.is_symlink()
                    or recorded_inputs[name].get("sha256") != file_sha256(path)
                    or recorded_inputs[name].get("size") != path.stat().st_size):
                return False
        recorded_outputs = manifest.get("outputs") or {}
        if set(recorded_outputs) != outputs:
            return False
        for name in outputs:
            path = directory / name
            if (not path.is_file() or path.is_symlink()
                    or recorded_outputs[name].get("sha256") != file_sha256(path)
                    or recorded_outputs[name].get("size") != path.stat().st_size):
                return False
        return True
    except (OSError, TypeError, ValueError, KeyError):
        return False


__all__ = ["file_sha256", "fresh_bundle"]
