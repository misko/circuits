#!/usr/bin/env python3
"""T1: Wave-0 declarative pipeline contracts and sealed canary baselines."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, check, contains, main, test  # noqa: E402


CONTRACT = ROOT / "skills/pcb-design/references/pipeline-stage-contract.md"
ADR = ROOT / "docs/decisions/0008-declarative-pipeline-stage-contract.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_field(path: Path, key: str) -> str:
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"{path}: missing {key}")


def exact_commit(value: str) -> bool:
    """Return true only for a complete, lowercase Git object identity."""
    return re.fullmatch(r"[0-9a-f]{40}", value) is not None


@test("Wave-0 contract freezes all public schema and verdict vocabularies")
def t_contract_surface():
    text = CONTRACT.read_text(encoding="utf-8")
    for token in (
            "## StageSpec schema 1", "## StageResult schema 1",
            "## Subject identity", "## Artifact bundle schema 1",
            "## Review contract schema 1", "## Lifecycle facts",
            "APPLIES", "NOT_APPLICABLE", "FIRST-ARTICLE-ONLY"):
        contains(text, token, "frozen pipeline contract")
    contains(ADR.read_text(encoding="utf-8"),
             "The first migration runs in shadow mode",
             "accepted migration decision")


@test("USB Hub v4 sealed canary pins live/release board identity and payload counts")
def t_usb_hub_canary():
    project = ROOT / "archived_projects/usb-hub-3s-v4"
    release = project / "07_releases/v0.6.1-2026-08-12"
    live = project / "04_kicad/usb_hub_3s_v4.kicad_pcb"
    sealed = release / "source/usb_hub_3s_v4.kicad_pcb"
    check(sha256(live) == sha256(sealed) ==
          "9888b1267744b8f659ce3f57dd0cbdd037e208440781bd1c80da88b2b1966dfb",
          "USB Hub live/sealed board identity moved")
    check(sum(1 for _ in (release / "fab/bom.csv").open(encoding="utf-8-sig")) == 41,
          "USB Hub BOM is no longer 40 rows plus header")
    check(sum(1 for _ in (release / "fab/cpl.csv").open(encoding="utf-8-sig")) == 71,
          "USB Hub CPL is no longer 70 rows plus header")
    manifest = (release / "MANIFEST.txt").read_text(encoding="utf-8")
    contains(manifest, "DESIGN:       PASS", "USB Hub design baseline")
    contains(manifest, "order:        DO-NOT-ORDER", "USB Hub order baseline")


@test("Pluto RX2 v4 sealed canary pins live/release board identity and payload counts")
def t_pluto_canary():
    project = ROOT / "archived_projects/pluto-rx2-8way-v4"
    release = project / "07_releases/v1.1-2026-08-01"
    live = project / "04_kicad/pluto_rx2_8way_v4.kicad_pcb"
    sealed = release / "source/pluto_rx2_8way_v4.kicad_pcb"
    check(sha256(live) == sha256(sealed) ==
          "72875d5ea92a52baa9962be3a69f4e69c1fb1ec3b9faf5ba4412934c18296bf7",
          "Pluto live/sealed board identity moved")
    check(sum(1 for _ in (release / "fab/bom.csv").open(encoding="utf-8-sig")) == 12,
          "Pluto BOM is no longer 11 rows plus header")
    check(sum(1 for _ in (release / "fab/cpl.csv").open(encoding="utf-8-sig")) == 28,
          "Pluto CPL is no longer 27 rows plus header")
    manifest = (release / "MANIFEST.txt").read_text(encoding="utf-8")
    contains(manifest, "DESIGN:       PASS", "Pluto design baseline")
    contains(manifest, "order_verdict: ORDER", "Pluto order baseline")


@test("canary manifests carry exact source commits")
def t_canary_source_commits():
    manifests = (
        ROOT / "archived_projects/usb-hub-3s-v4/07_releases/v0.6.1-2026-08-12/MANIFEST.txt",
        ROOT / "archived_projects/pluto-rx2-8way-v4/07_releases/v1.1-2026-08-01/MANIFEST.txt",
    )
    for manifest in manifests:
        value = manifest_field(manifest, "git_sha").split()[0]
        check(exact_commit(value),
              f"{manifest}: source commit is not exact")


@test("exact source-commit predicate REFUSES an abbreviation", kind="known_bad")
def t_canary_source_commit_abbreviation():
    manifest = (ROOT /
        "archived_projects/usb-hub-3s-v4/07_releases/"
        "v0.6.1-2026-08-12/MANIFEST.txt")
    exact = manifest_field(manifest, "git_sha").split()[0]
    check(not exact_commit(exact[:12]),
          "abbreviated source commit was incorrectly accepted")


if __name__ == "__main__":
    raise SystemExit(main())
