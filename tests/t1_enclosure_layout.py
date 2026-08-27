#!/usr/bin/env python3
"""T1: canonical project enclosure filesystem layout."""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import ROOT, check, contains, main, test, tmpdir  # noqa: E402


AUDIT = ROOT / "skills/pcb-enclosure/scripts/enclosure_layout_audit.py"


def fixture() -> Path:
    root = tmpdir("enclosure-layout-")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    project = root / "projects/demo"
    source = project / "03_src/mechanical"
    source.mkdir(parents=True)
    (source / "contracts.md").write_text("# fixture contract\n")
    (source / "README.md").write_text("# fixture enclosure\n")
    (source / "enclosure.yaml").write_text("schema: 1\n")
    (source / "case.scad").write_text('part = "base";\n')
    (root / "projects/contracts.md").write_text("# fixture root\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    return root


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AUDIT), "--root", str(root)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False)


@test("real fleet uses the canonical enclosure source/build/release layout")
def t_real_fleet():
    result = run(ROOT)
    check(result.returncode == 0, result.stdout)
    contains(result.stdout, "designed_projects=2", "real design census")
    contains(result.stdout, "tracked_stls=57", "real STL census")


@test("minimal authored enclosure source passes without generated payloads")
def t_minimal_source():
    result = run(fixture())
    check(result.returncode == 0, result.stdout)


@test("hash-bound input STL is permitted under source reference")
def t_bound_reference():
    root = fixture()
    source = root / "projects/demo/03_src/mechanical"
    reference = source / "reference/inspiration.stl"
    reference.parent.mkdir()
    reference.write_bytes(b"solid reference\nendsolid reference\n")
    digest = hashlib.sha256(reference.read_bytes()).hexdigest()
    size = reference.stat().st_size
    (source / "enclosure-v2.yaml").write_text(
        "path: 03_src/mechanical/reference/inspiration.stl\n"
        f"sha256: {digest}\nsize: {size}\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    result = run(root)
    check(result.returncode == 0, result.stdout)


@test("unbound source STL is rejected", kind="known_bad")
def t_unbound_reference():
    root = fixture()
    reference = root / "projects/demo/03_src/mechanical/reference/inspiration.stl"
    reference.parent.mkdir()
    reference.write_bytes(b"solid reference\nendsolid reference\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    result = run(root)
    check(result.returncode != 0, "unbound STL unexpectedly passed")
    contains(result.stdout, "lacks one exact path/size/SHA-256 binding",
             "unbound reference diagnostic")


@test("reference identity words outside one exact mapping do not bind an STL",
      kind="known_bad")
def t_scattered_reference_identity():
    root = fixture()
    source = root / "projects/demo/03_src/mechanical"
    reference = source / "reference/inspiration.stl"
    reference.parent.mkdir()
    reference.write_bytes(b"solid reference\nendsolid reference\n")
    digest = hashlib.sha256(reference.read_bytes()).hexdigest()
    (source / "enclosure-v2.yaml").write_text(
        "notes:\n"
        "  - path: 03_src/mechanical/reference/inspiration.stl\n"
        f"  - sha256: {digest}\n"
        f"  - size: {reference.stat().st_size}\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    result = run(root)
    check(result.returncode != 0, "scattered identity unexpectedly passed")
    contains(result.stdout, "lacks one exact path/size/SHA-256 binding",
             "scattered identity diagnostic")


@test("generated STL committed under build is rejected", kind="known_bad")
def t_tracked_build_mesh():
    root = fixture()
    mesh = root / "projects/demo/06_build/mechanical/candidate/base.stl"
    mesh.parent.mkdir(parents=True)
    mesh.write_text("solid base\nendsolid base\n")
    subprocess.run(["git", "-C", str(root), "add", "-f", str(mesh)], check=True)
    result = run(root)
    check(result.returncode != 0, "tracked build mesh unexpectedly passed")
    contains(result.stdout, "generated 06_build meshes stay ignored",
             "tracked build diagnostic")


@test("CAD package under physical reviews is rejected", kind="known_bad")
def t_review_payload():
    root = fixture()
    mesh = root / "projects/demo/08_reviews/enclosure-fit/meshes/base.stl"
    mesh.parent.mkdir(parents=True)
    mesh.write_text("solid base\nendsolid base\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    result = run(root)
    check(result.returncode != 0, "review CAD payload unexpectedly passed")
    contains(result.stdout, "08_reviews is physical evidence",
             "review payload diagnostic")


@test("generated verification receipts under physical reviews are rejected",
      kind="known_bad")
def t_review_receipt():
    root = fixture()
    receipt = root / "projects/demo/08_reviews/enclosure-fit/verification.json"
    receipt.parent.mkdir(parents=True)
    receipt.write_text('{"status":"CAD_READY"}\n')
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    result = run(root)
    check(result.returncode != 0, "review receipt unexpectedly passed")
    contains(result.stdout, "08_reviews is physical evidence",
             "review receipt diagnostic")


@test("authored enclosure config under generated build is rejected", kind="known_bad")
def t_config_in_build():
    root = fixture()
    config = root / "projects/demo/06_build/mechanical/enclosure-v2.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("schema: 2\n")
    subprocess.run(["git", "-C", str(root), "add", "-f", str(config)], check=True)
    result = run(root)
    check(result.returncode != 0, "build-local authored config unexpectedly passed")
    contains(result.stdout, "authoring config must be under 03_src/mechanical",
             "config path diagnostic")


if __name__ == "__main__":
    raise SystemExit(main())
