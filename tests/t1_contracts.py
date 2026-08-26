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
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, eq, main,  # noqa: E402
                     must_fail,
                     must_pass, run, test, tmpdir)

AUDIT = ROOT / "scripts" / "contracts_audit.py"
COMMISSION = ROOT / "skills" / "pcb-design" / "scripts" / "commission_project.py"

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
@test("contracts_audit: the real repo (non-projects scope) is clean, and its "
      "verdict CARRIES ITS DENOMINATOR")
def t_repo_clean():
    """The second half is canon M-COVER and it landed 2026-07-28.
    `contracts_audit: 243 files, 0 violations` was being read as COVERAGE. It
    is not: the default universe excludes `projects/**` and
    `archived_projects/**`, which was 6715 of 6958 tracked files — the
    invocation CLAUDE.md names grades 3.5% of the tree. A verdict with no
    denominator invites exactly that reading, and every other gate here prints
    N/M.

    RED-VERIFIED 2026-07-28 (git-swap): pre-fix the line is
    `contracts_audit: 243 files, 0 violations` and `tracked` appears nowhere,
    so the `NOT GRADED` assertion fails.
    """
    r = must_pass(run([KPY, AUDIT]), "contracts_audit on the repo")
    # PROPERTY, not the literal count (canon: assert PROPERTIES, never bytes).
    # The original form pinned "/6958 tracked" and went RED the same day, when
    # concurrent board work grew the tree to 6979 — a test that fails whenever
    # anyone adds a file measures the repo's size, not the gate's behaviour.
    # What the test NAMES is that the verdict CARRIES ITS DENOMINATOR, so that
    # is what it now checks: graded <= tracked, and tracked genuinely wider.
    m = re.search(r"(\d+)/(\d+) tracked", r.out)
    check(m is not None,
          "the verdict states the full universe as <graded>/<tracked> tracked\n"
          f"--- got ---\n{r.out}")
    graded, tracked = int(m.group(1)), int(m.group(2))
    check(graded <= tracked,
          f"graded {graded} cannot exceed tracked {tracked}")
    check(tracked > graded,
          "the non-projects scope must report a WIDER tracked universe than it "
          f"graded, else the denominator says nothing (got {graded}/{tracked})")
    contains(r.out, "NOT GRADED", "the verdict says what it did not grade")
    contains(r.out, "--projects", "the verdict names the wider invocation")
    # ...and the wider scope does NOT print an exclusion it did not make
    w = run([KPY, AUDIT, "--projects"])
    check("NOT GRADED" not in w.out,
          f"--projects claims an exclusion it did not make:\n{w.out[-500:]}")
    # ...and ITS EXIT CODE IS READ. See t_projects_exit_code_is_read below for
    # why this one line is the whole point; it lived here unasserted for three
    # days while the run beneath it exited 1.
    eq(w.rc, 0, "the --projects RAW exit code")


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
    # The commissioner is the one executable scaffold manifest. This test
    # exercises its largest conditional shape rather than copying a second
    # hand-maintained file list into the suite.
    base = tmpdir("seed_")
    projects = base / "projects"
    projects.mkdir()
    brief = base / "brief.txt"
    brief.write_text("Commission a governed RF board with an enclosure.\n")
    must_pass(run([
        KPY, COMMISSION, "seeded-board",
        "--projects-root", projects,
        "--brief-file", brief,
        "--signal-integrity", "rf",
        "--assembly", "jlcpcb",
        "--target", "release",
        "--foreign-mating",
        "--enclosure",
    ]), "template commissioner")
    d = projects / "seeded-board"
    r = must_pass(run([KPY, AUDIT, "--walk", "--root", d]),
                  "contracts_audit on template-seeded project")
    contains(r.out, "0 violations", "seeded project audits clean")


# ================== the MARKDOWN PIPE in a pattern cell (2026-07-28) =========
PIPE_ROOT = """# contract: fixture root
## Allowed
| Pattern | What |
|---|---|
| `*.c\\|*.h\\|*.rs\\|*.py` | the firmware |
| `README.md` | doc |
"""


def pipe_tree(names):
    d = tmpdir("ctp_")
    (d / "contracts.md").write_text(PIPE_ROOT)
    for n in names:
        (d / n).parent.mkdir(parents=True, exist_ok=True)
        (d / n).write_text("x")
    return d


@test("contracts_audit reads a pattern cell whose pipes are ESCAPED — "
      "`*.c\\|*.h\\|*.rs\\|*.py` permits all four, not just the first",
      kind="known_bad")
def t_escaped_pipe_alternation():
    """THE DEFECT (2026-07-28). `parse_allowed` split table rows with a naive
    `line.split("|")`, so the 05_firmware contract's one Allowed row —
    `` `*.c|*.h|*.rs|*.py` `` — was torn into four cells and only `*.c` ever
    became a pattern. EVERY `.h`, `.rs` and `.py` in the repo failed C-ALLOW
    while its own contract said, in plain sight, that it was permitted. Six
    live failures in `archived_projects/` prove it, and it is why a constant
    shipped in a `.c` rather than the `.h` it belonged in: the author read the
    audit and concluded the FILE was wrong, not the parser.

    A parser that silently keeps the first fragment of a pattern list is worse
    than one that rejects the row outright — it disagrees with the document it
    is enforcing and gives no hint why.

    THE KNOWN-BAD IS THE ASYMMETRY, and it is what makes this a fixture rather
    than a restatement: in ONE tree, `main.c` must PASS and `pinmap.h` must
    also pass, while `notes.md` — matched by no pattern at all — must still
    FAIL. Pre-fix the first two disagree with each other over one row.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    contracts_audit.py swapped back in, the all-permitted tree FAILS with
    `C-ALLOW  pinmap.h: not permitted by contracts.md` (and `main.rs`,
    `tool.py`), i.e. `contracts_audit on an all-permitted tree should have
    exited 0, got 1`. Restored, it passes and `notes.md` still fails.
    """
    ok = pipe_tree(["main.c", "pinmap.h", "main.rs", "tool.py", "README.md"])
    r = must_pass(run([KPY, AUDIT, "--walk", "--root", ok]),
                  "contracts_audit on an all-permitted tree")
    contains(r.out, "0 violations", "every listed extension is permitted")
    # ...and the row did not become a wildcard: an extension it never named
    # is still refused, in the SAME tree shape.
    bad = pipe_tree(["main.c", "notes.md"])
    b = must_fail(run([KPY, AUDIT, "--walk", "--root", bad]),
                  "contracts_audit on an unlisted extension", "C-ALLOW")
    contains(b.out, "notes.md", "names the file the row never permitted")


@test("contracts_audit does not split a pattern cell on a pipe inside a "
      "BACKTICK code span either", kind="known_bad")
def t_codespan_pipe_not_split():
    """The defensive half. Every project contract already in the tree — and
    every archived copy, which is never retro-edited — carries the UNESCAPED
    form `` `*.c|*.h|*.rs|*.py` ``, so a fix that only understood `\\|` would
    leave the whole existing fleet broken. A pipe inside a code span is
    content, not a delimiter.

    RED-VERIFIED 2026-07-28 by the same git-swap: pre-fix this tree reports
    `C-ALLOW  pinmap.h` and exits 1.
    """
    d = tmpdir("ctc_")
    (d / "contracts.md").write_text(
        "# contract: fixture root\n## Allowed\n| Pattern | What |\n|---|---|\n"
        "| `*.c|*.h|*.rs|*.py` | the firmware, pipes unescaped |\n")
    for n in ("main.c", "pinmap.h", "main.rs", "tool.py"):
        (d / n).write_text("x")
    r = must_pass(run([KPY, AUDIT, "--walk", "--root", d]),
                  "contracts_audit on an unescaped-pipe contract")
    contains(r.out, "0 violations", "the code span is one pattern cell")
    (d / "notes.md").write_text("x")
    must_fail(run([KPY, AUDIT, "--walk", "--root", d]),
              "contracts_audit on an unlisted extension", "notes.md")


@test("the 05_firmware TEMPLATE permits a header and a src/ tree — the "
      "contract and the auditor now agree", kind="known_bad")
def t_firmware_template_permits_headers():
    """The end-to-end statement, against the SHIPPED template rather than a
    hand-written fixture: `05_firmware/pinmap.h` and `05_firmware/src/x.c`
    must audit clean, and `05_firmware/notes.md` must not.

    MEASURED: the whole fleet holds 5 firmware source files, and 4 of them are
    the `.h` files under `archived_projects/cook-hub/05_firmware/{include,src}/`
    that this row was failing. Those archived copies keep failing until they
    are re-synced from this template on their next revision — templates are
    the source of truth and project copies are seeded, never retro-edited
    (CLAUDE.md, Structure governance).

    RED-VERIFIED 2026-07-28 (git-swap): pre-fix, `pinmap.h` fails C-ALLOW
    against the template's own contract.
    """
    tpl = (ROOT / "skills" / "pcb-design" / "templates" / "contracts" /
           "05_firmware" / "contracts.md")
    d = tmpdir("ctf_")
    shutil.copy(tpl, d / "contracts.md")
    (d / "pinmap.h").write_text("#define X 1\n")
    (d / "src").mkdir()
    (d / "src" / "relay_fsm.c").write_text("int main(void){return 0;}\n")
    (d / "include").mkdir()
    (d / "include" / "protocol.h").write_text("#define Y 2\n")
    (d / "README.md").write_text("build\n")
    r = must_pass(run([KPY, AUDIT, "--walk", "--root", d]),
                  "contracts_audit on the shipped 05_firmware template")
    contains(r.out, "0 violations", "the template permits what it says")
    (d / "notes.md").write_text("stray\n")
    must_fail(run([KPY, AUDIT, "--walk", "--root", d]),
              "a stray .md under 05_firmware", "notes.md")


@test("the 01_docs contract's OWN prompt-hash command reproduces the digest a "
      "commission records — and refuses an altered prompt", kind="known_bad")
def t_prompt_hash_command_reproduces():
    """THE DEFECT (2026-07-28). The Validate line shipped

        sed -n '/prompt-verbatim-begin/,/prompt-verbatim-end/p' | sed '1d;$d' | sha256sum

    which keeps the block's FINAL NEWLINE — `sed`'s line terminator, not part
    of the prompt. Commissions compute the digest with it stripped, so EVERY
    board's check disagreed with its own recorded hash. A check that never
    reproduces its own recorded value trains the reader to ignore it, and this
    is the one check that proves the commission text was not rewritten after
    the fact.

    MEASURED against the real pluto-rx2-8way BRIEF (the most recent
    commission): recorded `1bf0eca3306a...`; the shipped command produced
    `21708345f8ae...`; with `head -c -1` it produces `1bf0eca3306a...` exactly.

    THIS TEST RUNS THE CONTRACT'S OWN TEXT. The command is extracted from the
    shipped `contracts.md` with a regex and executed — the document is what is
    graded, so re-implementing the pipeline here would prove nothing about the
    thing a human will actually paste (canon M1).

    A SECOND defect the same line carried, found by running it: it named no
    FILE. Pasted as written it reads stdin, so a human running it in a shell
    gets a hang and a subprocess gets the digest of the empty string.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    01_docs contract swapped back in, the test fails with `the contract's own
    command reproduces the recorded digest: got
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'` —
    which is sha256 of NOTHING, the missing-filename half. Against the real
    pluto-rx2-8way BRIEF, where the filename is supplied by hand, the
    trailing-newline half shows on its own: recorded `1bf0eca3306a...`,
    shipped command `21708345f8ae...`, `head -c -1` `1bf0eca3306a...`.
    """
    import hashlib
    import re
    import subprocess
    c = (ROOT / "skills" / "pcb-design" / "templates" / "contracts" /
         "01_docs" / "contracts.md").read_text()
    m = re.search(r"`(sed -n '/prompt-verbatim-begin/.*?sha256sum)`", c, re.S)
    check(m, "the 01_docs contract no longer carries a runnable prompt-hash "
             "command at all")
    cmd = " ".join(m.group(1).split())

    d = tmpdir("phash_")
    body = ("we want a high speed switching 8 pole on RX2, timed off a GPS "
            "PPS edge.\n\nEach antenna gets an SMA connector.")
    (d / "01_docs").mkdir()
    (d / "01_docs" / "BRIEF.md").write_text(
        "# BRIEF\n\n<!-- prompt-verbatim-begin -->\n" + body +
        "\n<!-- prompt-verbatim-end -->\n\nprompt_sha256: \"" +
        hashlib.sha256(body.encode()).hexdigest() + "\"\n")
    want = hashlib.sha256(body.encode()).hexdigest()

    got = subprocess.run(cmd, shell=True, cwd=d, capture_output=True,
                         text=True).stdout.split()[0]
    eq(got, want, "the contract's own command reproduces the recorded digest")

    # THE KNOWN-BAD: the prompt is rewritten by one word. The command must
    # produce a DIFFERENT digest, or the check is decorative.
    (d / "01_docs" / "BRIEF.md").write_text(
        (d / "01_docs" / "BRIEF.md").read_text().replace("8 pole", "4 pole"))
    tampered = subprocess.run(cmd, shell=True, cwd=d, capture_output=True,
                              text=True).stdout.split()[0]
    check(tampered != want,
          "an ALTERED commission prompt still hashes to the recorded digest — "
          "the check cannot detect a rewritten brief")


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
    # Progressive disclosure moved orchestration policy from one monolithic
    # SKILL.md into routed references.  The governance corpus is therefore the
    # whole human-readable pcb-design skill, not only its small entry point.
    skill = "\n".join(
        p.read_text()
        for p in sorted((skills / "pcb-design").rglob("*.md"))
    )

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
    #    skill (canon + audit + routed pcb-design Markdown corpus) — a
    #    stale/orphaned governance claim.
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


# ================== THE RATCHET (2026-07-31) ================================
def _drive(body):
    """Run the REAL auditor in a subprocess with its ceilings mutated.

    The mutation happens in the imported module, so what runs is the shipped
    `main()` against the shipped repo — the known-bad exercises the MEASUREMENT
    and its exit code, not a re-implementation of either (canon M1).
    """
    d = tmpdir("ratch_")
    (d / "drive.py").write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT / 'scripts')!r})\n"
        "import contracts_audit as ca\n"
        "ca.DEBT_CEILING = dict(ca.DEBT_CEILING)\n"
        "ca.STRAY_UNITS = dict(ca.STRAY_UNITS)\n"
        f"{body}\n"
        "sys.argv = ['contracts_audit.py'] + sys.argv[1:]\n"
        "ca.main()\n")
    return d / "drive.py"


@test("--projects RAW EXIT CODE IS READ, and the per-unit debt ceiling is "
      "TIGHT", kind="known_bad")
def t_projects_exit_code_is_read():
    """THE MISSING HALF OF THE 2026-07-28 FIX, and the half-fix is the
    interesting part.

    On 2026-07-28 someone caught `contracts_audit: 243 files, 0 violations`
    being read as COVERAGE and fixed the REPORTING, so the verdict now carries
    its denominator (t_repo_clean, above). They stopped there. **The gap was
    made VISIBLE without being made to COST anything.** This repo has ratchet
    FLOORS and no CEILINGS, so an honestly declared gap is free — and
    `t_repo_clean` went on running the WIDE scope on every suite run while
    asserting exactly one thing about it, that the output does not contain
    `NOT GRADED`. **It never looked at `w.rc`.** MEASURED at c0e21fa7 before
    this change: `contracts_audit.py --projects` = **2674 violations, RAW EXIT
    1**, on every suite run since, silently.

    WHAT THIS ASSERTS: `--projects` exits 0, and it does so because the measured
    per-unit debt EQUALS the recorded ceiling, not because there is nothing
    wrong. Equality, not `<=`: an improvement must lower its row in the same
    commit and cannot be banked as slack, or the ceiling rots back into the free
    gap it replaced.

    RED-VERIFIED 2026-07-31, END-TO-END, all three pawl directions, by running
    the SHIPPED main() with one ceiling row mutated (`_drive`), UNPIPED:
      * row LOWERED  (`ble-bus-bar` 287->286) -> RAW EXIT **1**,
        `DEBT_CEILING: archived_projects/ble-bus-bar measured 287, row says 286
        — it ROSE`. A debt that grows is caught.
      * row DELETED  -> RAW EXIT **1**, `UNRATCHETED unit
        'archived_projects/ble-bus-bar' carries 287 violation(s) and has no
        row`. The map cannot be satisfied by omission.
      * row INVENTED (`projects/no-such-board: 3`) -> RAW EXIT **1**,
        `STALE row 'projects/no-such-board'`. A bound nothing measures is not a
        bound.
    Each restored to 0 after. And the pre-fix statement: at c0e21fa7 the
    unmutated `--projects` exits **1**, so `eq(r.rc, 0)` below is RED against
    the code this replaces.
    """
    r = must_pass(run([KPY, AUDIT, "--projects"]), "contracts_audit --projects")
    contains(r.out, "RATCHET debt", "the wide scope states its ratchet")
    m = re.search(r"RATCHET debt (\d+) tracked violations over (\d+) units "
                  r"vs (\d+) recorded over (\d+)", r.out)
    check(m, f"the ratchet line is not machine-readable:\n{r.out[-400:]}")
    got, gotu, want, wantu = (int(m.group(i)) for i in (1, 2, 3, 4))
    eq(got, want, "measured tracked debt vs the recorded DEBT_CEILING total")
    eq(gotu, wantu, "units measured vs units with a ceiling row")
    check(got > 0, "a zero debt would make this ratchet vacuous — if the debt "
                   "really reached 0, delete the ceiling and make --projects "
                   "strict (canon M-COVER: a zero denominator is never a pass)")

    # THE PAWL, end-to-end on the real measurement.
    for body, expect in [
            ('ca.DEBT_CEILING["archived_projects/ble-bus-bar"] -= 1', "ROSE"),
            ('del ca.DEBT_CEILING["archived_projects/ble-bus-bar"]',
             "UNRATCHETED"),
            ('ca.DEBT_CEILING["projects/no-such-board"] = 3', "STALE row")]:
        b = must_fail(run([KPY, _drive(body), "--projects"]),
                      f"a mutated ceiling ({expect})", expect)
        contains(b.out, "BREACHED", "the verdict names the breach")


@test("--present grades PRESENCE for untracked files, because a stray "
      "worktree is a governed tree and audits CLEAN", kind="known_bad")
def t_present_scope_is_presence_not_violations():
    """THE POPULATION (canon: the walk MINUS everything `git check-ignore`
    excludes). A raw `--walk` of this repo is **227883 files** — agent
    worktrees, node_modules, build trees — and grading it is meaningless. A
    file that is neither tracked nor ignored is either a violation or something
    that should not be in the repo, and THAT is the population: MEASURED
    2026-07-31, 227883 - 220360 = **7523** = 7414 tracked + 109 untracked.
    VERIFIED BY TWO INDEPENDENT METHODS whose SYMMETRIC DIFFERENCE IS 0: an
    external `find` walk piped through `git check-ignore --stdin`, and git's own
    `ls-files --cached --others --exclude-standard` (canon M1).

    WHY THE UNTRACKED HALF IS RATCHETED ON PRESENCE AND NOT ON VIOLATIONS —
    this is the part that is not obvious and it is MEASURED below: **a copy of
    a governed tree carries its `contracts.md` files with it, so every file in
    it is permitted by its own ancestor and the audit reports `0 violations`,
    RAW EXIT 0.** The 3.1 GB stray `git worktree` found at this repo's root on
    2026-07-31 was exactly that — a self-governing, perfectly clean copy. A
    violation-counting stray gate grades it GREEN. What is wrong with a stray
    worktree is that it EXISTS.

    AND IT IS A SET OF UNITS, NOT A FILE COUNT: a count over an in-flight board
    flaps on every file its author writes, and a ratchet that fails on correct
    work is a ratchet that gets deleted (the `PREC_OWED_CEILING` lesson,
    policy_audit.py 2026-07-30). *Which* corners may hold uncommitted work is a
    PROPERTY, unmoved by how much work happens inside a declared corner.

    THE SCOPING CONTROL, and it is a real control because it must go SILENT:
    the eleven `~*.kicad_pro.lck` files strewn across the fleet on 2026-07-31 —
    four of them inside SEALED releases — were gitignored that morning. A
    correctly scoped population reports ZERO of them; a population still
    listing them would be walking, not scoping. Asserted below by creating one.

    RED-VERIFIED end-to-end (`_drive`), UNPIPED:
      * a governed, allowed untracked file is planted under the hub and an
        empty `STRAY_UNITS` -> RAW EXIT **1**, `holds
        UNTRACKED-NOT-IGNORED files.` An undeclared corner is caught.
      * a row INVENTED for a corner holding none -> RAW EXIT **1**,
        `STALE row` — an exemption that exempts nothing is how the next stray
        gets in free.
    """
    r = must_pass(run([KPY, AUDIT, "--present"]), "contracts_audit --present")
    m = re.search(r"RATCHET stray (\d+) untracked-not-ignored files in "
                  r"(\d+) unit\(s\); (\d+) declared \(population (\d+)", r.out)
    check(m, f"--present does not state its stray ratchet:\n{r.out[-400:]}")
    strays, units, declared, pop = (int(m.group(i)) for i in (1, 2, 3, 4))
    eq(units, declared, "stray-holding units vs declared STRAY_UNITS rows")
    tracked = len(run(["git", "ls-files"], cwd=ROOT).out.split())
    check(pop >= tracked,
          f"the --present population {pop} is narrower than the tracked "
          f"universe {tracked} — it must be a SUPERSET")
    eq(pop, tracked + strays,
       "population = tracked + untracked-not-ignored, exactly")

    # PRESENCE, not violations: a copy of a governed tree audits CLEAN.
    d = fixture_tree()
    clean = must_pass(run([KPY, AUDIT, "--walk", "--root", d]),
                      "a governed tree")
    contains(clean.out, "0 violations", "the tree is clean")
    stray = tmpdir("strayclone_")
    shutil.copytree(d, stray / "a-whole-stray-copy")
    (stray / "contracts.md").write_text(
        "# contract: fixture root\n## Allowed\n| Pattern | What |\n|---|---|\n"
        "| `a-whole-stray-copy/**` | the stray |\n")
    c2 = must_pass(run([KPY, AUDIT, "--walk", "--root", stray]),
                   "a tree containing a whole stray copy of another")
    contains(c2.out, "0 violations",
             "THE POINT: a stray copy is invisible to a violation count, which "
             "is why the stray ratchet grades PRESENCE")

    # THE CONTROL: a gitignored artefact must not enter the population.
    lck = ROOT / "~contracts_audit_scoping_control.kicad_pro.lck"
    try:
        lck.write_text("advisory lock\n")
        ign = run(["git", "check-ignore", lck.name], cwd=ROOT)
        eq(ign.rc, 0, "the .lck control file is gitignored (it must be, or the "
                      "control proves nothing)")
        after = must_pass(run([KPY, AUDIT, "--present"]),
                          "--present with a .lck present on disk")
        check(".kicad_pro.lck" not in after.out,
              "a GITIGNORED .lck entered the --present population — the scope "
              "is walking, not scoping")
        m2 = re.search(r"population (\d+)", after.out)
        eq(int(m2.group(1)), pop, "the population is unchanged by a gitignored "
                                  "file appearing on disk")
    finally:
        lck.unlink(missing_ok=True)

    probe = (ROOT / "projects" / "programmable-usb2-hub" / "01_docs" /
             "renders" / "stray-ratchet-control.png")
    probe.parent.mkdir(parents=True, exist_ok=True)
    try:
        probe.write_bytes(b"stray-presence-control\n")
        must_fail(run([KPY, _drive("ca.STRAY_UNITS = {}"), "--present"]),
                  "an undeclared untracked unit",
                  "holds UNTRACKED-NOT-IGNORED files")
        must_pass(run([KPY, _drive(
            'ca.STRAY_UNITS["projects/programmable-usb2-hub"] = "test control"'),
            "--present"]), "the same planted unit with an evidence row")
    finally:
        probe.unlink(missing_ok=True)
        try:
            probe.parent.rmdir()
        except OSError:
            pass

    must_fail(run([KPY, _drive(
        'ca.STRAY_UNITS["skills"] = "invented"'), "--present"]),
        "an invented STRAY_UNITS row", "STALE row")


@test("a pattern cell listing several backticked patterns SEPARATED BY COMMAS "
      "is read as all of them — the pipe bug's twin", kind="known_bad")
def t_comma_separated_pattern_cell():
    """THE DEFECT (found 2026-07-31, by finally reading `--projects`' exit
    code). `parse_allowed` split a pattern cell on WHITESPACE and `.strip("`")`
    each token. `str.strip` removes a character only while it is at the END, and
    the end of `` `build/pcb.svg`, `` is a COMMA — so the trailing backtick
    survived and the pattern became the literal ``build/pcb.svg`,``, which
    matches no file that can exist.

    THE LAST ITEM OF EVERY SUCH LIST HAS NO TRAILING COMMA and therefore parsed
    fine, which is exactly why this looked like one odd file rather than a
    parser fault: in the 03_tscircuit contract's `--study` row,
    `build/board.gltf` was permitted and `build/assembly.svg` — named on the
    SAME LINE of the SAME cell — was not.

    MEASURED before the fix: **124 corrupted patterns across 38 of the repo's
    329 `contracts.md`** — 4 in every board's `03_tscircuit`, 2 in every board's
    `03_src`. After: **0 of 2896**.

    THE KNOWN-BAD IS THE ASYMMETRY WITHIN ONE CELL, which is what makes it a
    fixture rather than a restatement of the fix: in ONE tree the FIRST item of
    the comma list must pass, the LAST item must also pass, and a name the cell
    never mentioned must still FAIL. Pre-fix the first and last disagree about
    the row they share.

    RED-VERIFIED 2026-07-31 (git-swap, tests/README step 3): with HEAD's
    `parse_allowed` swapped back in, the all-permitted tree FAILS —
    `C-ALLOW  build/pcb.svg: not permitted by contracts.md` and the same for
    `build/assembly.svg`, i.e. `contracts_audit on a comma-listed cell should
    have exited 0, got 1` — while `build/board.gltf` passes. Restored, all three
    pass and `build/stray.svg` still fails.
    """
    def tree(names):
        d = tmpdir("ctcomma_")
        (d / "contracts.md").write_text(
            "# contract: fixture root\n## Allowed\n| Pattern | What |\n|---|---|\n"
            "| `build/pcb.svg`, `build/assembly.svg`, `build/board.gltf` | "
            "the study renders |\n")
        for n in names:
            (d / n).parent.mkdir(parents=True, exist_ok=True)
            (d / n).write_text("x")
        return d

    ok = tree(["build/pcb.svg", "build/assembly.svg", "build/board.gltf"])
    r = must_pass(run([KPY, AUDIT, "--walk", "--root", ok]),
                  "contracts_audit on a comma-listed cell")
    contains(r.out, "0 violations",
             "every item of the comma list is a pattern, not just the last")
    # ...and the row did not become a wildcard, in the SAME tree shape.
    bad = tree(["build/pcb.svg", "build/stray.svg"])
    b = must_fail(run([KPY, AUDIT, "--walk", "--root", bad]),
                  "an item the cell never listed", "C-ALLOW")
    contains(b.out, "stray.svg", "names the file the cell never permitted")

    # ...and no contract in the repo still parses to a corrupted pattern.
    sys.path.insert(0, str(ROOT / "scripts"))
    import contracts_audit as ca
    corrupt = []
    for c in run(["git", "ls-files"], cwd=ROOT).out.split():
        if not c.endswith("contracts.md"):
            continue
        for p in ca.parse_allowed(ROOT / c):
            if "`" in p or p.endswith(","):
                corrupt.append(f"{c}: {p!r}")
    check(not corrupt,
          f"{len(corrupt)} contract pattern(s) still parse to a literal "
          f"containing a backtick or a trailing comma — they can match no file "
          f"that can exist: {corrupt[:6]}")


# ============ A DECLARED FIELD WITH NO CONSUMER IS A DEFECT ==================
# Per-FILE ceiling, MEASURED 2026-07-31 in /home/mouse9911/gits/circuits:
# 47 declared fields across the 4 `skills/**/references/*.yaml`, 9 with no
# Python reader. Per file and not one number, for unit_of()'s reason: a fleet
# aggregate breaks when a new reference file is added, which is a correct
# action. TIGHT, so wiring a field up must lower its row in the same change.
ORPHAN_CEILING = {
    # `order_readme` carries the EXACT required ORDER_README sentence per fab
    # tier and NOTHING READS IT. That is how pluto-rx2-8way-v2's ORDER_README
    # came to name no fab option while 3446 of its 3496 plated holes sit under
    # the no-fee tier's 0.30 mm floor. OWED: a consumer in the ORDER_README
    # producer. Not wired here — that producer is another agent's file.
    "skills/kicad-pcb/references/fab_tiers.yaml": 1,
    # 6 of 13: `detect` `fix` `reduce` `refuse` `idempotent` `no_new_violations`
    # — grind_fixes.yaml IS loaded (grind_driver.py) but these fields are read
    # by a human, not by the driver. OWED: either the driver executes them or
    # the file says in its own header that it is a playbook, not config.
    "skills/kicad-pcb/references/grind_fixes.yaml": 6,
    # `gotchas` and `maker`: declared per proven part, never read by
    # bom_source_check.py, the file's only loader.
    "skills/kicad-pcb/references/proven-parts.yaml": 2,
}


def _orphan_fields():
    """(file -> sorted orphan field names). A DECLARED FIELD is a key whose
    value is a LEAF — scalar, or a list. A key whose value is a MAPPING is a
    CONTAINER (an entry id or a section) and is addressed dynamically, never by
    literal, so it is deliberately out of scope: `jlc_2layer_default` is a tier
    NAME, and requiring a string literal for it would be a check that cannot
    pass."""
    import yaml
    py = "\n".join(p.read_text(errors="replace")
                   for p in (ROOT / "skills").rglob("*.py"))

    def fields(node, out):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and not isinstance(v, dict):
                    out.add(k)
                if isinstance(v, (dict, list)):
                    fields(v, out)
        elif isinstance(node, list):
            for v in node:
                fields(v, out)

    res, total = {}, 0
    for f in sorted((ROOT / "skills").glob("*/references/*.yaml")):
        ks = set()
        fields(yaml.safe_load(f.read_text()), ks)
        ks = {k for k in ks if re.fullmatch(r"[a-z_][a-z0-9_]{2,}", k)}
        total += len(ks)
        orph = sorted(k for k in ks
                      if not re.search(rf'["\']{re.escape(k)}["\']', py))
        if orph:
            res[f.relative_to(ROOT).as_posix()] = orph
    return res, total


@test("a DECLARED FIELD WITH NO CONSUMER is a defect — every field in a "
      "skills reference yaml is read by something, or its row says how many "
      "are not", kind="known_bad")
def t_declared_field_has_a_consumer():
    """THE INCIDENT. `skills/kicad-pcb/references/fab_tiers.yaml:130` carries
    the exact sentence a release's ORDER_README must contain, as an
    `order_readme:` field, and **no script reads it** — `grep -rn order_readme
    skills/` returns 3 yaml values and 1 line of SKILL.md prose. That is how
    `pluto-rx2-8way-v2`'s ORDER_README came to name no fab option at all while
    **3446 of its 3496 plated holes** sit under the no-fee tier's 0.30 mm
    floor. A field nobody reads is not a weak control, it is the APPEARANCE of
    one: the value is right there in the canon, so a reader checking whether
    the requirement is captured finds that it is.

    SCOPED BY MEASUREMENT FIRST, because a check that cannot pass is not a
    gate. MEASURED 2026-07-31: **47 declared fields across the 4
    `skills/**/references/*.yaml`; 9 have no Python reader.** All four files
    ARE loaded by real scripts, so every one of the 9 is a genuine
    declared-never-read field rather than a prose document miscounted as
    config.

    DELIBERATELY OUT OF SCOPE, named rather than omitted:
      * CONTAINER keys (a key whose value is a mapping) — `jlc_2layer_default`
        and the other 3 tier ids are looked up dynamically; demanding a string
        literal for them is a check that cannot pass. 56 keys total, 47 fields.
      * `skills/kicad-pcb/gradelib/sitecustomize.py`, which writes 8 fields per
        trace of which 4 have no consumer (task #60). It is not a reference
        yaml and it is another agent's file; the same rule applies to it and it
        is not graded here.
      * every `03_src/**` project schema (`part.yaml`, `floorplan.yaml`, …).
        Far more fields, and their consumers live in the generic backend; that
        is a second, larger sweep, not this one.

    RED-VERIFIED 2026-07-31, all three directions, each `16 passed, 1 failed`
    with RAW EXIT 1, and `17 passed, 0 failed` restored after each:
      * LOOSEN `proven-parts.yaml` 2 -> 3 -> FAILED, `got 2, want 3`. Slack
        cannot be banked, so wiring a field up must lower its row.
      * DELETE the `fab_tiers.yaml: 1` row -> FAILED,
        `UNRATCHETED skills/kicad-pcb/references/fab_tiers.yaml: 1 orphan
        field(s) ['order_readme'] and no row`. The map cannot be satisfied by
        omission.
      * INVENT a row for `lcsc_passives_ledger.yaml`, whose 3 fields all have
        consumers -> FAILED, `STALE ORPHAN_CEILING row`. A bound nothing
        measures is not a bound.
    """
    orph, total = _orphan_fields()
    check(total > 0, "no declared fields found at all — the sweep is broken, "
                     "and a zero denominator is never a pass (canon M-COVER)")
    measured = {f: len(v) for f, v in orph.items()}
    for f in sorted(set(measured) - set(ORPHAN_CEILING)):
        check(False,
              f"UNRATCHETED {f}: {measured[f]} orphan field(s) {orph[f]} and "
              f"no row. Either give them a consumer, or add "
              f"`\"{f}\": {measured[f]},` to ORPHAN_CEILING with the evidence "
              f"— a declared field with no consumer is a defect (SKILL.md)")
    for f in sorted(set(ORPHAN_CEILING) - set(measured)):
        check(False, f"STALE ORPHAN_CEILING row {f} — every field there now "
                     f"has a consumer. Delete the row.")
    for f in sorted(measured):
        eq(measured[f], ORPHAN_CEILING[f],
           f"{f}: orphan fields {orph[f]} vs its ORPHAN_CEILING row — it may "
           f"only FALL, and the row is TIGHT so wiring one up must be recorded "
           f"in the same change rather than banked as slack")


if __name__ == "__main__":
    sys.exit(main())
