#!/usr/bin/env python3
"""Fail closed when tracked project enclosure files cross canonical paths."""
from __future__ import annotations

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from enclosure_common import (  # noqa: E402
    EnclosureError, load_yaml, run_bounded,
)


PROJECT_ROOTS = {"projects", "archived_projects"}
SOURCE_PARTS = ("03_src", "mechanical")
RELEASE_DIR = "07_enclosure_releases"
REVIEW_DIR = "08_reviews"
AUTHORING_NAMES = {
    "enclosure.yaml", "enclosure-v2.yaml", "mechanical-intent-v2.yaml",
}
REVIEW_GENERATED_DIRS = {
    "cad", "meshes", "package", "renders", "replay", "tooling", "verification",
}
REVIEW_GENERATED_NAMES = {
    "generation.json", "verification.json", "collision.json",
    "step-inspection.json", "scoped-verdict.json", "v2-validation.json",
}


def tracked_files(root: Path) -> list[PurePosixPath]:
    result = run_bounded(
        ["git", "ls-files", "-z", "--", "projects", "archived_projects"],
        cwd=root, timeout_s=60, max_output_bytes_per_stream=20_000_000,
        check=True)
    if "[pcb-enclosure: stdout truncated" in result.stdout:
        raise EnclosureError("tracked-file census exceeded its bounded output cap")
    return sorted(
        PurePosixPath(item)
        for item in result.stdout.split("\0") if item
    )


def project_key(path: PurePosixPath) -> tuple[str, str] | None:
    parts = path.parts
    if len(parts) < 3 or parts[0] not in PROJECT_ROOTS:
        return None
    return parts[0], parts[1]


def under(path: PurePosixPath, prefix: tuple[str, ...]) -> bool:
    return path.parts[:len(prefix)] == prefix


def source_prefix(key: tuple[str, str]) -> tuple[str, ...]:
    return (*key, *SOURCE_PARTS)


def release_prefix(key: tuple[str, str]) -> tuple[str, ...]:
    return (*key, RELEASE_DIR)


def review_prefix(key: tuple[str, str]) -> tuple[str, ...]:
    return (*key, REVIEW_DIR)


def _walk_bindings(value: Any) -> list[tuple[str, str, int]]:
    bindings: list[tuple[str, str, int]] = []
    if isinstance(value, dict):
        if set(("path", "sha256", "size")).issubset(value) and \
                isinstance(value["path"], str) and \
                isinstance(value["sha256"], str) and \
                isinstance(value["size"], int):
            bindings.append((value["path"], value["sha256"], value["size"]))
        for child in value.values():
            bindings.extend(_walk_bindings(child))
    elif isinstance(value, list):
        for child in value:
            bindings.extend(_walk_bindings(child))
    return bindings


def source_bindings(root: Path, key: tuple[str, str],
                    files: list[PurePosixPath]) -> set[tuple[str, str, int]]:
    prefix = source_prefix(key)
    bindings: set[tuple[str, str, int]] = set()
    authority = PurePosixPath(*prefix, "enclosure-v2.yaml")
    if authority in files:
        try:
            bindings.update(_walk_bindings(load_yaml(root / authority)))
        except (EnclosureError, OSError) as exc:
            raise EnclosureError(f"cannot read binding source {authority}: {exc}")
    return bindings


def audit(root: Path) -> tuple[list[str], dict[str, int]]:
    files = tracked_files(root)
    findings: list[str] = []
    metrics: defaultdict[str, int] = defaultdict(int)
    by_project: defaultdict[tuple[str, str], list[PurePosixPath]] = defaultdict(list)
    for relative in files:
        key = project_key(relative)
        if key:
            by_project[key].append(relative)

    for key, project_files in sorted(by_project.items()):
        src = source_prefix(key)
        rel = release_prefix(key)
        review = review_prefix(key)
        project_name = "/".join(key)
        source_files = [path for path in project_files if under(path, src)]
        designed = any(
            path.name == "enclosure.yaml" or path.suffix.lower() == ".scad"
            for path in source_files
        )
        if designed:
            metrics["designed_projects"] += 1
            required = {
                PurePosixPath(*src, "contracts.md"),
                PurePosixPath(*src, "README.md"),
                PurePosixPath(*src, "enclosure.yaml"),
            }
            missing = sorted(required - set(project_files))
            for path in missing:
                findings.append(f"{project_name}: designed enclosure missing {path}")

        bindings = source_bindings(root, key, project_files)
        for path in project_files:
            suffix = path.suffix.lower()
            lower = path.as_posix().lower()
            in_source = under(path, src)
            in_release = under(path, rel)
            in_review = under(path, review)
            review_payload_parts = set(path.parts[len(review):])

            if path.name in AUTHORING_NAMES and not (in_source or in_release):
                findings.append(
                    f"{path}: enclosure authoring config must be under "
                    "03_src/mechanical or an immutable enclosure release")

            if suffix == ".scad" and not (in_source or in_release):
                findings.append(
                    f"{path}: authored/generated enclosure SCAD is outside "
                    "03_src/mechanical or 07_enclosure_releases")

            if in_review and (suffix in {".stl", ".scad"} or
                              path.name in REVIEW_GENERATED_NAMES or
                              review_payload_parts & REVIEW_GENERATED_DIRS or
                              (suffix == ".zip" and any(
                                  token in lower for token in
                                  ("enclos", "case", "mechanical", "cad")))):
                findings.append(
                    f"{path}: 08_reviews is physical evidence, not CAD/mesh/package storage")

            if suffix != ".stl":
                continue
            metrics["tracked_stls"] += 1
            reference_prefix = (*src, "reference")
            if under(path, reference_prefix):
                metrics["source_reference_stls"] += 1
                absolute = root / path
                data = absolute.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                project_relative = PurePosixPath(*path.parts[2:]).as_posix()
                if (project_relative, digest, len(data)) not in bindings:
                    findings.append(
                        f"{path}: source reference STL lacks one exact path/size/SHA-256 binding")
                continue
            if in_release:
                parts = path.parts
                release_index = parts.index(RELEASE_DIR)
                if len(parts) <= release_index + 2:
                    findings.append(f"{path}: STL is not below a versioned enclosure release")
                    continue
                payload_root = parts[release_index + 2]
                if payload_root not in {"meshes", "source", "verification"}:
                    findings.append(
                        f"{path}: release STL must be printable meshes, bound source, or verification evidence")
                elif payload_root == "meshes":
                    metrics["printable_release_stls"] += 1
                else:
                    metrics["release_evidence_stls"] += 1
                continue
            findings.append(
                f"{path}: tracked STL must be a hash-bound 03_src/mechanical/reference input "
                "or an immutable 07_enclosure_releases payload; generated 06_build meshes stay ignored")

    return findings, dict(metrics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        findings, metrics = audit(root)
    except (EnclosureError, OSError, ValueError) as exc:
        print(f"ENCLOSURE LAYOUT FAIL: {exc}", file=sys.stderr)
        return 1
    if findings:
        for finding in findings:
            print(f"FAIL {finding}")
        print(f"ENCLOSURE LAYOUT FAIL: {len(findings)} finding(s)")
        return 1
    print(
        "ENCLOSURE LAYOUT PASS: "
        f"designed_projects={metrics.get('designed_projects', 0)} "
        f"tracked_stls={metrics.get('tracked_stls', 0)} "
        f"source_references={metrics.get('source_reference_stls', 0)} "
        f"printable_release={metrics.get('printable_release_stls', 0)} "
        f"release_evidence={metrics.get('release_evidence_stls', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
