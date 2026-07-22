#!/usr/bin/env python3
"""T1: the repo-structure gate — scripts/contracts_audit.py (canon M7).

Motivating incidents (2026-07-21):
- template/ at repo root drifted from the skill-owned stage contracts
  unnoticed (the skill's 02_parts contract gained the escape-block schema;
  template/'s copy did not) — two homes, silent divergence.
- skills/kicad-pcb cited a live project's proof artifact
  (archived_projects/cook-loadcell/03_tscircuit/backend_proof/...) — a path a
  clean-room worktree cannot resolve and a contamination vector.

RED-VERIFIED (new-gate variant): contracts_audit.py did not exist before
this commit — at 656bab3 there is no scripts/ directory, so every case
below fails with "no such file"; the gate could not exist. The tampered
fixtures were additionally verified to FAIL against the CURRENT auditor
run on an untampered copy (each breaks a passing tree in exactly one way).
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

AUDIT = ROOT / "scripts" / "contracts_audit.py"

GOOD_ROOT = """# contract: fixture root
## Allowed
| Pattern | What |
|---|---|
| `README.md` | doc |
| `sub/` | governed subfolder |
| `blob/**` | wholesale-covered subtree |
"""

GOOD_SUB = """# contract: sub/
## Allowed
| Pattern | What |
|---|---|
| `*.py` | tools |
"""


def fixture_tree():
    d = tmpdir("cta_")
    (d / "contracts.md").write_text(GOOD_ROOT)
    (d / "README.md").write_text("x")
    (d / "sub").mkdir()
    (d / "sub" / "contracts.md").write_text(GOOD_SUB)
    (d / "sub" / "tool.py").write_text("pass")
    (d / "blob" / "deep").mkdir(parents=True)
    (d / "blob" / "deep" / "data.bin").write_text("x")
    return d


# ------------------------------------------------------------ clean cases
@test("contracts_audit: the real repo (non-projects scope) is clean")
def t_repo_clean():
    must_pass(run([KPY, AUDIT]), "contracts_audit on the repo")


@test("contracts_audit passes a well-governed fixture tree")
def t_fixture_clean():
    must_pass(run([KPY, AUDIT, "--walk", "--root", fixture_tree()]),
              "contracts_audit on clean fixture")


# -------------------------------------------------------- known-bad cases
@test("contracts_audit FAILS a stray file its contract never permitted",
      kind="known_bad")
def t_stray_file():
    d = fixture_tree()
    (d / "stray.txt").write_text("nobody said I could be here")
    must_fail(run([KPY, AUDIT, "--walk", "--root", d]),
              "audit on stray file", "C-ALLOW")


@test("contracts_audit FAILS a governed subfolder that lost its contract",
      kind="known_bad")
def t_sub_without_contract():
    # `sub/` (trailing slash) means: the folder must govern itself. Remove
    # its contracts.md and its files become unpermitted.
    d = fixture_tree()
    (d / "sub" / "contracts.md").unlink()
    must_fail(run([KPY, AUDIT, "--walk", "--root", d]),
              "audit on contract-less governed subfolder", "C-ALLOW")


@test("contracts_audit FAILS a tree with no contracts.md at all",
      kind="known_bad")
def t_no_governance():
    d = tmpdir("cta_")
    (d / "orphan.md").write_text("x")
    must_fail(run([KPY, AUDIT, "--walk", "--root", d]),
              "audit on ungoverned tree", "C-COV")


@test("contracts_audit FAILS a skill that references a concrete project path",
      kind="known_bad")
def t_iso():
    d = fixture_tree()
    (d / "contracts.md").write_text(GOOD_ROOT +
                                    "| `skills/**` | fixture skills |\n")
    (d / "skills").mkdir()
    (d / "skills" / "leaky.md").write_text(
        "see projects/some-board/03_src/floorplan.yaml for how it's done")
    r = must_fail(run([KPY, AUDIT, "--walk", "--root", d]),
                  "audit on skills->projects reference", "C-ISO")
    contains(r.out, "some-board", "C-ISO names the leaked path")


@test("contracts_audit does NOT flag the projects/<name> placeholder",
      kind="clean")
def t_iso_placeholder_ok():
    d = fixture_tree()
    (d / "contracts.md").write_text(GOOD_ROOT +
                                    "| `skills/**` | fixture skills |\n")
    (d / "skills").mkdir()
    (d / "skills" / "howto.md").write_text(
        "commission copies templates into projects/<name>/03_src/")
    must_pass(run([KPY, AUDIT, "--walk", "--root", d]),
              "audit on placeholder reference")


@test("a project seeded from the skill templates audits clean (template/"
      "contract coherence pinned)")
def t_template_seed():
    # replicates templates/README.md's commission copy list exactly; a gap
    # between what the templates ship and what the contracts permit fails
    # here (9 such gaps shipped before this test existed — 6a5bd82)
    tpl = ROOT / "skills" / "pcb-design" / "templates"
    d = tmpdir("seed_")
    stages = ["01_docs", "02_parts", "03_src", "03_tscircuit", "04_kicad",
              "05_firmware", "06_build", "07_releases"]
    for s in stages:
        (d / s).mkdir()
        shutil.copy(tpl / "contracts" / s / "contracts.md", d / s)
    shutil.copy(tpl / "contracts" / "ROOT.contracts.md", d / "contracts.md")
    (d / "03_src" / "rules").mkdir()
    (d / "03_src" / "lib").mkdir()
    (d / "01_docs" / "decisions").mkdir()
    (d / "01_docs" / "journal").mkdir()
    (d / "01_docs" / "learnings").mkdir()
    for src, dst in [
            ("03_src/floorplan.yaml", "03_src/floorplan.yaml"),
            ("03_src/route.yaml", "03_src/route.yaml"),
            ("03_src/rules/nets.yaml", "03_src/rules/nets.yaml"),
            ("project.gitignore", ".gitignore"),
            ("01_docs/decisions/0000-example-adr.md",
             "01_docs/decisions/0000-example-adr.md"),
            ("contracts/01_docs/decisions/contracts.md",
             "01_docs/decisions/contracts.md"),
            ("contracts/01_docs/journal/contracts.md",
             "01_docs/journal/contracts.md"),
            ("contracts/01_docs/learnings/contracts.md",
             "01_docs/learnings/contracts.md"),
            ("contracts/03_src/lib/contracts.md", "03_src/lib/contracts.md"),
            ("contracts/03_src/rules/contracts.md",
             "03_src/rules/contracts.md")]:
        shutil.copy(tpl / src, d / dst)
    for md in (tpl / "01_docs").glob("*.md"):
        shutil.copy(md, d / "01_docs")
    r = must_pass(run([KPY, AUDIT, "--walk", "--root", d]),
                  "contracts_audit on template-seeded project")
    contains(r.out, "0 violations", "seeded project audits clean")


if __name__ == "__main__":
    main()
