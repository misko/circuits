#!/usr/bin/env python3
"""Initialize, rehearse, and receipt a PCB release before immutable seal.

The command does not commit, publish, or silently repair a release. ``init``
creates a loud DRAFT manifest skeleton before expensive release work.
``rehearse`` runs the same release and publication predicates against mutable
staging and writes its hash-bound receipt outside the staged archive, avoiding
a self-referential MANIFEST hash. ``seal`` only receipts an already accepted,
still-current rehearsal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def _record(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {"path": str(path.resolve()),
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                            text=True, check=False)
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip())
    return result.stdout.strip()


def _project_for(release: Path) -> Path:
    for parent in release.resolve().parents:
        if (parent / "03_src").is_dir() and (parent / "04_kicad").is_dir():
            return parent
    raise ValueError(f"cannot locate project root above {release}")


def _release_files(release: Path) -> list[Path]:
    return sorted(path for path in release.rglob("*")
                  if path.is_file() and not path.is_symlink()
                  and path.name != "MANIFEST.txt")


def init_manifest(release: Path, project: Path | None = None) -> Path:
    release = release.resolve()
    project = (project or _project_for(release)).resolve()
    manifest = release / "MANIFEST.txt"
    if manifest.exists() or manifest.is_symlink():
        raise ValueError(f"refusing to overwrite existing {manifest}")
    source_boards = sorted((release / "source").glob("*.kicad_pcb"))
    if len(source_boards) != 1:
        raise ValueError(
            f"manifest init requires one staged source board, found {source_boards}")
    assembly_path = project / "03_src/rules/assembly.yaml"
    assembly = (yaml.safe_load(assembly_path.read_text(encoding="utf-8-sig"))
                or {}) if assembly_path.is_file() else {}
    not_assembled = sorted({str(ref)
                            for row in assembly.get("not_assembled") or []
                            if isinstance(row, dict)
                            for ref in row.get("refs") or []})
    head = _git("rev-parse", "HEAD")
    dirty = bool(_git("status", "--porcelain", "--", project.relative_to(REPO).as_posix(),
                      "skills"))
    parsed = re.search(r"v(?P<version>\d+(?:\.\d+)*)-(?P<date>\d{4}-\d{2}-\d{2})",
                       release.name)
    version = f"v{parsed.group('version')}" if parsed else "DRAFT"
    date = parsed.group("date") if parsed else "PENDING"
    lines = [
        f"board:        {source_boards[0].stem}",
        f"version:      {version}",
        f"ordered:      NOT-ORDERED ({date} staging)",
        f"git_sha:      {head}",
        f"git_dirty:    {str(dirty).lower()}",
        "sourcing_authority: jlc-pcba",
        "status:       DRAFT — DO-NOT-ORDER",
        "gates:        PENDING release rehearsal",
        "DESIGN:       FAIL",
        "SOURCING:     BLOCKED-SOURCING (DRAFT; no order-time allocation)",
        f"assembly:     {assembly.get('service', 'PENDING')}",
        "not_assembled: " + (",".join(not_assembled) if not_assembled else "none"),
        "sha256:",
    ]
    for path in _release_files(release):
        record = _record(path)
        lines.append(f"  {path.relative_to(release).as_posix()}  {record['sha256']}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def _run(label: str, command: list[str]) -> dict[str, Any]:
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=REPO, capture_output=True,
                                text=True, timeout=1200, check=False)
    except subprocess.TimeoutExpired as exc:
        return {"status": "INCOMPLETE", "detail": f"{label} timed out",
                "output": ((exc.stdout or "") + (exc.stderr or ""))[-8000:]}
    return {
        "status": "PASS" if result.returncode == 0 else
                  "FAIL" if result.returncode == 1 else "INCOMPLETE",
        "detail": f"exit {result.returncode}",
        "elapsed_s": round(time.monotonic() - started, 6),
        "output": ((result.stdout or "") + (result.stderr or ""))[-12000:],
    }


def _declares_blocked_sourcing(manifest: Path, readme: Path) -> bool:
    manifest_text = manifest.read_text(encoding="utf-8-sig").upper()
    readme_text = readme.read_text(encoding="utf-8-sig").upper()
    return ("BLOCKED-SOURCING" in readme_text and
            ("BLOCKED-SOURCING" in manifest_text or
             "BLOCKED-ORDER" in manifest_text))


def rehearse(release: Path, project: Path | None = None,
             representation_supersede: str | None = None,
             allow_blocked_sourcing: bool = False) -> dict[str, Any]:
    release = release.resolve()
    project = (project or _project_for(release)).resolve()
    manifest = release / "MANIFEST.txt"
    readme = release / "ORDER_README.md"
    if not manifest.is_file() or not readme.is_file():
        raise ValueError("release rehearsal requires MANIFEST.txt and ORDER_README.md")
    if allow_blocked_sourcing and not _declares_blocked_sourcing(manifest, readme):
        raise ValueError(
            "--allow-blocked-sourcing requires BLOCKED-SOURCING on the first "
            "screen of ORDER_README and BLOCKED-SOURCING/BLOCKED-ORDER in "
            "MANIFEST; a quiet order block may not seal")
    freshness_suffix = (["--representation-supersede",
                         representation_supersede]
                        if representation_supersede else [])
    checks = {
        "release_required": _run(
            "release-required",
            ["/usr/bin/python3",
             str(REPO / "skills/kicad-pcb/scripts/release_required_check.py"),
             str(release), "--contract",
             str(project / "07_releases/contracts.md")]),
        "design_freshness": _run(
            "design-freshness",
            ["/usr/bin/python3",
             str(REPO / "skills/jlcpcb-fab/scripts/release_freshness_check.py"),
             str(release), "--claim", "design", *freshness_suffix]),
        "sourcing_freshness": _run(
            "sourcing-freshness",
            ["/usr/bin/python3",
             str(REPO / "skills/jlcpcb-fab/scripts/release_freshness_check.py"),
             str(release), "--claim", "sourcing", *freshness_suffix]),
        "publication_contract": _run(
            "publication-contract",
            ["/usr/bin/python3", str(HERE / "pcb_publication_gate.py"),
             "--root", str(REPO), "--project", str(project),
             "--release", str(release)]),
    }
    for name, row in checks.items():
        row["required_for_seal"] = not (
            allow_blocked_sourcing and name == "sourcing_freshness")
    statuses = {row["status"] for row in checks.values()
                if row["required_for_seal"]}
    verdict = ("INCOMPLETE" if "INCOMPLETE" in statuses else
               "REJECTED" if "FAIL" in statuses else "ACCEPTED")
    inputs = {path.relative_to(release).as_posix(): _record(path)
              for path in _release_files(release)}
    inputs["MANIFEST.txt"] = _record(manifest)
    return {
        "schema": 1, "kind": "release-rehearsal-receipt-v1",
        "verdict": verdict, "project": project.name,
        "freshness_mode": ({"kind": "representation-supersede",
                            "prior": representation_supersede}
                           if representation_supersede else
                           {"kind": "full-release"}),
        "sourcing_admission": ("DECLARED-BLOCKED-INFORMATIONAL"
                               if allow_blocked_sourcing else "REQUIRED"),
        "release": str(release), "inputs": dict(sorted(inputs.items())),
        "checks": checks,
        "coverage": {"passing": sum(row["status"] == "PASS"
                                     for row in checks.values()
                                     if row["required_for_seal"]),
                     "total": sum(row["required_for_seal"]
                                  for row in checks.values()),
                     "informational": sum(not row["required_for_seal"]
                                          for row in checks.values())},
    }


def verify(path: Path) -> tuple[bool, list[str]]:
    failures = []
    try:
        receipt = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, [f"receipt cannot be read: {exc}"]
    if (receipt.get("schema") != 1 or
            receipt.get("kind") != "release-rehearsal-receipt-v1"):
        failures.append("unsupported receipt schema/kind")
    release = Path(str(receipt.get("release") or ""))
    for name, record in sorted((receipt.get("inputs") or {}).items()):
        source = release / name
        if not source.is_file() or _record(source) != record:
            failures.append(f"release input moved or changed: {name}")
    if receipt.get("verdict") == "ACCEPTED":
        bad = [name for name, row in (receipt.get("checks") or {}).items()
               if row.get("status") != "PASS" and
               row.get("required_for_seal", True)]
        if bad:
            failures.append(f"accepted receipt contains bad checks: {bad}")
    return not failures, failures


def _default_output(project: Path, release: Path) -> Path:
    return project / "06_build/release_rehearsal" / f"{release.name}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("release", type=Path)
    init.add_argument("--project", type=Path)
    rehearse_parser = sub.add_parser("rehearse")
    rehearse_parser.add_argument("release", type=Path)
    rehearse_parser.add_argument("--project", type=Path)
    rehearse_parser.add_argument("--output", type=Path)
    rehearse_parser.add_argument(
        "--representation-supersede",
        help="assert a representation-only delta against this prior release")
    rehearse_parser.add_argument(
        "--allow-blocked-sourcing", action="store_true",
        help="seal only the design claim when BLOCKED-SOURCING is declared "
             "loudly; retain sourcing freshness as an informational failure")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("receipt", type=Path)
    seal = sub.add_parser("seal")
    seal.add_argument("receipt", type=Path)
    seal.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "init":
        try:
            path = init_manifest(args.release, args.project)
        except Exception as exc:
            print(f"RELEASE-REHEARSAL INIT FAIL: {exc}")
            return 2
        print(f"RELEASE-REHEARSAL INIT PASS: DRAFT skeleton -> {path}")
        return 0
    if args.command == "verify":
        valid, failures = verify(args.receipt)
        for failure in failures:
            print(f"  FAIL {failure}")
        print(f"RELEASE-REHEARSAL RECEIPT {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1
    if args.command == "seal":
        valid, failures = verify(args.receipt)
        receipt = json.loads(args.receipt.read_text(encoding="utf-8-sig"))
        if not valid or receipt.get("verdict") != "ACCEPTED":
            print("RELEASE-SEAL REFUSED: rehearsal is rejected, incomplete, or stale")
            for failure in failures:
                print(f"  FAIL {failure}")
            return 1
        seal_receipt = {
            "schema": 1, "kind": "release-seal-admission-v1",
            "verdict": "ACCEPTED", "rehearsal": _record(args.receipt.resolve()),
            "release": receipt["release"],
        }
        _atomic_json(args.output, seal_receipt)
        print(f"RELEASE-SEAL ADMISSION PASS: {args.output.resolve()}")
        return 0
    try:
        result = rehearse(args.release, args.project,
                           args.representation_supersede,
                           args.allow_blocked_sourcing)
    except Exception as exc:
        print(f"RELEASE-REHEARSAL INCOMPLETE: {exc}")
        return 2
    project = (args.project or _project_for(args.release)).resolve()
    output = args.output or _default_output(project, args.release.resolve())
    _atomic_json(output, result)
    coverage = result["coverage"]
    print(f"RELEASE-REHEARSAL {result['verdict']}: {coverage['passing']}/"
          f"{coverage['total']} checks pass; receipt={output.resolve()}")
    return {"ACCEPTED": 0, "REJECTED": 1, "INCOMPLETE": 2}[result["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
