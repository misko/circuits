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
              "05_firmware", "06_build", "07_releases", "08_reviews"]
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


@test("skill<->contract sync: every emitted check-ID is in canon; no contract "
      "cites a check-ID that exists nowhere in the skill", kind="known_bad")
def t_skill_contract_sync():
    """A gate added to policy_audit but not to design-policies.md, or a
    contract citing a retired ID, is silent skill<->governance drift — the
    class that let the escape-block schema drift (2026-07-21) and that made
    P-LAYOUT/P-ADJ land WITH its 02_parts contract (2026-07-22). This is the
    machine backstop the CLAUDE.md 'a skill change is not done until its
    contract catches up' rule points to.
    RED-VERIFIED inline: a synthetic emitted ID absent from canon is caught."""
    import re
    skills = ROOT / "skills"
    canon = (skills / "kicad-pcb/references/design-policies.md").read_text()
    audit = (skills / "kicad-pcb/scripts/policy_audit.py").read_text()
    skill = (skills / "pcb-design/SKILL.md").read_text()

    def emitted(txt):
        return set(re.findall(
            r'(?:grade\(|rows\.append\(\()"([A-Z][A-Z0-9-]+)"', txt))

    def in_(hay, i):
        return re.search(rf'(?<![\w-]){re.escape(i)}(?![\w-])', hay) is not None

    # 1. every check-ID the audit EMITS must be documented in the canon
    missing = sorted(i for i in emitted(audit) if not in_(canon, i))
    check(not missing, "check-IDs emitted by policy_audit but undocumented in "
                       f"design-policies.md (add the canon row): {missing}")

    # 2. no contract template may cite a check-ID that exists NOWHERE in the
    #    skill (canon + audit + SKILL.md) — a stale/orphaned governance claim.
    #    A contract may still PROPOSE a future gate: a citation on a line marked
    #    candidate/proposed/future/TODO/planned is exempt (forward-reference,
    #    not drift).
    corpus = canon + "\n" + audit + "\n" + skill
    FWD = re.compile(r'candidate|proposed|future|todo|planned', re.I)
    cited = {}   # id -> True if EVERY citation is a forward-reference
    # The prefix class is the drift backstop's whole reach. It read `[SPRMED]-`
    # until 2026-07-25, which would have SILENTLY EXEMPTED the entire new A-
    # (assembly) family from exactly the check that exists to catch a gate
    # landing without its canon row — the same silent-skip class as the M-REL
    # glob bug and the `^v` release-name regex. Widen it whenever a new family
    # is minted; cases 4 and 5 below are the standing proof that it bites.
    # WIDENED AGAIN 2026-07-27 to `F` and `G`. The instruction directly above
    # was NOT followed when the F- family (F-POUR/F-IDENT, ADR-0004) and the
    # G- family (G-INPUT/G-COVER/G-RED, the gate-on-gates) were minted, so for
    # their whole existence a contract could have cited `F-ANYTHING` and this
    # backstop would have reported success — the very class the comment warns
    # about, reproduced under its own warning. Found while landing F-LEGIBLE
    # (ADR-0006).
    # WIDENED AGAIN 2026-07-27 to `Q` when the Q- (sourcing/quote) family was
    # minted with canon M-QUOTE and skills/shopping-list. This time the
    # instruction two comments up WAS followed, in the same change that minted
    # the family — which is the whole point of writing it down.
    ID_RE = re.compile(r'(?<![\w-])([ASPRMEDFGQ]-[A-Z][A-Z0-9-]+)(?![\w-])')
    for c in (skills / "pcb-design/templates/contracts").rglob("contracts.md"):
        txt = c.read_text()
        for m in ID_RE.finditer(txt):
            # window BEFORE the citation catches a wrapped "candidate ... M-REV"
            fwd = bool(FWD.search(txt[max(0, m.start() - 90):m.start()]))
            iid = m.group(1)
            cited[iid] = fwd and cited.get(iid, True)
    orphan = sorted(i for i, all_fwd in cited.items()
                    if not in_(corpus, i) and not all_fwd)
    check(not orphan, "contract templates cite check-IDs that exist nowhere in "
                      f"the skill (stale governance reference): {orphan}")

    # 3. RED: the logic must catch a gate that skipped the canon
    fake = emitted('    grade("Z-NOPE", ok, "", "")')
    check("Z-NOPE" in fake and not in_(canon, "Z-NOPE"),
          "sync logic failed to detect a synthetic un-canonized gate")

    # 4. RED: the ID regex must REACH the A- family. A fabricated `A-NOPE`
    #    citation in a contract must be caught as an orphan — with the
    #    pre-2026-07-25 `[SPRMED]-` class it is not even seen, so every A-
    #    gate could have landed with no canon row and no contract row and this
    #    backstop would have reported success. VERIFIED RED against the
    #    un-widened class: `re.compile(r'(?<![\w-])([SPRMED]-...)')` finds
    #    ZERO matches in the same text, so `orphan` comes back empty and the
    #    assertion below fails.
    fabricated = "| `x` | governed by A-NOPE and by A-POP |\n"
    seen = {m.group(1) for m in ID_RE.finditer(fabricated)}
    check("A-NOPE" in seen and "A-POP" in seen,
          f"the check-ID regex does not reach the A- (assembly) family — a "
          f"whole gate family would be exempt from this backstop; matched only "
          f"{sorted(seen)}")
    check(not in_(corpus, "A-NOPE"),
          "A-NOPE unexpectedly exists in the skill — pick another fake ID")
    check(in_(corpus, "A-POP"),
          "A-POP is cited by a contract but exists nowhere in the skill — the "
          "assembly family landed without its canon row")

    # 5. RED: the same reach test for the F- (fab-artifact) family, which
    #    landed with ADR-0004 while the class was still `[ASPRMED]-` and was
    #    therefore invisible to this backstop for its whole existence.
    #    VERIFIED RED against that class: `F-NOPE`/`F-LEGIBLE` match ZERO
    #    times, so the assertion below fails.
    fab = "| `x` | governed by F-NOPE and by F-LEGIBLE |\n"
    seen_f = {m.group(1) for m in ID_RE.finditer(fab)}
    check("F-NOPE" in seen_f and "F-LEGIBLE" in seen_f,
          f"the check-ID regex does not reach the F- (fab-artifact) family — "
          f"F-POUR/F-IDENT/F-LEGIBLE would all be exempt; matched only "
          f"{sorted(seen_f)}")
    check(not in_(corpus, "F-NOPE"),
          "F-NOPE unexpectedly exists in the skill — pick another fake ID")
    check(in_(corpus, "F-LEGIBLE"),
          "F-LEGIBLE is cited but exists nowhere in the skill — ADR-0006 "
          "landed without its canon row")

    # 6. RED: the same reach test for the Q- (sourcing/quote) family, minted
    #    2026-07-27 with canon M-QUOTE. VERIFIED RED against the un-widened
    #    `[ASPRMEDFG]-` class: `Q-NOPE`/`Q-STOCK` match ZERO times there, so
    #    `seen_q` comes back empty and the assertion below fails.
    srcq = "| `x` | governed by Q-NOPE and by Q-STOCK |\n"
    seen_q = {m.group(1) for m in ID_RE.finditer(srcq)}
    check("Q-NOPE" in seen_q and "Q-STOCK" in seen_q,
          f"the check-ID regex does not reach the Q- (sourcing) family — "
          f"Q-COVER/Q-WIDE/Q-IDENT/Q-STOCK/Q-SNIPPET/Q-GRADE would all be "
          f"exempt; matched only {sorted(seen_q)}")
    check(not in_(corpus, "Q-NOPE"),
          "Q-NOPE unexpectedly exists in the skill — pick another fake ID")
    check(in_(corpus, "Q-STOCK"),
          "Q-STOCK is cited but exists nowhere in the skill — the sourcing "
          "family landed without its canon row")


if __name__ == "__main__":
    main()
