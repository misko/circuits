#!/usr/bin/env python3
"""T1: the release seal's `git_dirty` flag is scoped to a release's ACTUAL
regeneration inputs — the board's own subtree + `skills/` — NOT the whole repo
(`skills/kicad-pcb/scripts/release_git_dirty.py`).

Motivating incident (2026-07-23): the seal's clean-tree check ran a repo-wide
`git status --porcelain`, so a dirty SIBLING project (a concurrently-building
board) blocked an unrelated board's seal — forcing pause-coordination between
independent projects whose reproducibility does not overlap. Rescoped: clean
iff the board's own subtree + `skills/` are clean; a dirty sibling is invisible.

RED-VERIFIED inline (`t_sibling_dirty_does_not_block`): the SAME fixture the
scoped helper calls clean is shown DIRTY under the old whole-repo logic
(`git status --porcelain` with no pathspec is non-empty and names the sibling)
— so the sibling case genuinely changed behavior and the pre-change repo-wide
check WOULD have blocked this seal. The helper is NEW (no prior version to swap
in), so this old-blocks / new-passes comparison on one fixture is the
red-verify the tests/README workflow calls for.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, KPY, check, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

HELPER = ROOT / "skills" / "kicad-pcb" / "scripts" / "release_git_dirty.py"


def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True)


def fixture_repo():
    """A scratch git repo, everything committed clean:

      projects/board-a/{03_src,02_parts}   -- 'the release' being sealed
      projects/board-b/03_src              -- an unrelated SIBLING board
      skills/kicad-pcb/scripts/backend.py  -- the shared backend

    Known-bad cases break exactly one of these; the sibling stays untouched
    except where a test deliberately dirties it to prove it is ignored.
    """
    d = tmpdir("rgd_")
    _git(d, "init", "-q")
    _git(d, "config", "user.email", "t@t")
    _git(d, "config", "user.name", "t")
    for rel, body in [
        ("projects/board-a/03_src/floorplan.yaml", "a: 1\n"),
        ("projects/board-a/02_parts/part.yaml", "p: a\n"),
        ("projects/board-b/03_src/floorplan.yaml", "b: 1\n"),
        ("skills/kicad-pcb/scripts/backend.py", "print('backend')\n"),
    ]:
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body)
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "seed")
    return d


def helper(repo, board):
    return run([KPY, HELPER, board, "--repo-root", str(repo)], cwd=repo)


# ------------------------------------------------------------ clean cases
@test("release_git_dirty: a clean board subtree + clean skills = git_dirty false")
def t_clean():
    d = fixture_repo()
    r = must_pass(helper(d, "board-a"), "clean board")
    contains(r.out, "git_dirty:    false", "manifest line reads false")
    contains(r.out, "projects/board-a/", "scope names the board's subtree")
    contains(r.out, "skills/", "scope names the shared backend")


@test("release_git_dirty accepts a project PATH as well as a bare board name "
      "(same verdict either way)")
def t_resolve_forms():
    d = fixture_repo()
    r_name = must_pass(helper(d, "board-a"), "by board name")
    r_path = must_pass(helper(d, "projects/board-a"), "by project path")
    check(r_name.out.strip() == r_path.out.strip(),
          f"name vs path disagree:\n{r_name.out!r}\n{r_path.out!r}")


@test("release_git_dirty: a DIRTY SIBLING project does NOT block the seal — "
      "the whole point — RED-verified vs the old repo-wide logic")
def t_sibling_dirty_does_not_block():
    d = fixture_repo()
    # dirty a completely unrelated sibling board (modify a tracked input)
    (d / "projects/board-b/03_src/floorplan.yaml").write_text("b: 999\n")
    # NEW scoped helper: board-a's inputs are untouched -> clean, exit 0
    r = must_pass(helper(d, "board-a"),
                  "sibling-dirty must not block board-a's seal")
    contains(r.out, "git_dirty:    false", "board-a still clean")
    # RED-VERIFY: the OLD whole-repo logic (git status --porcelain, no
    # pathspec) WOULD have blocked — it sees the sibling dirt. Same fixture,
    # opposite verdict, which is exactly the behavior change under test.
    whole = _git(d, "status", "--porcelain")
    check(whole.stdout.strip() != "",
          "red-verify: old repo-wide logic should see the sibling dirt")
    check("board-b" in whole.stdout,
          f"red-verify: the dirt the old logic blocks on is board-b's, "
          f"got:\n{whole.stdout!r}")


@test("release_git_dirty: an UNTRACKED file in a sibling project is ignored too")
def t_sibling_untracked_ignored():
    d = fixture_repo()
    (d / "projects/board-b/03_src/scratch.yaml").write_text("x: 1\n")
    r = must_pass(helper(d, "board-a"),
                  "untracked sibling file must not block board-a")
    contains(r.out, "git_dirty:    false", "board-a still clean")


# -------------------------------------------------------- known-bad cases
@test("release_git_dirty FAILS when the shared skills/ backend is dirty",
      kind="known_bad")
def t_skills_dirty():
    # A dirty backend means the gerbers are NOT reproducible from committed
    # code — it must block EVERY board's seal, not just this one.
    d = fixture_repo()
    (d / "skills/kicad-pcb/scripts/backend.py").write_text("print('CHANGED')\n")
    r = must_fail(helper(d, "board-a"), "dirty skills backend blocks",
                  "git_dirty:    true")
    contains(r.out, "backend.py", "names the offending skills file (stderr)")


@test("release_git_dirty FAILS when a file in the board's OWN subtree is dirty",
      kind="known_bad")
def t_own_subtree_dirty():
    d = fixture_repo()
    (d / "projects/board-a/03_src/floorplan.yaml").write_text("a: 2\n")
    r = must_fail(helper(d, "board-a"), "dirty own subtree blocks",
                  "git_dirty:    true")
    contains(r.out, "board-a", "names the offending own file (stderr)")


@test("release_git_dirty FAILS on an UNTRACKED file in the board's own subtree "
      "(a reproducibility hole, not only modifications)", kind="known_bad")
def t_own_untracked():
    d = fixture_repo()
    (d / "projects/board-a/03_src/new_input.yaml").write_text("x: 1\n")
    must_fail(helper(d, "board-a"), "untracked own input blocks",
              "git_dirty:    true")


@test("release_git_dirty: the seal's OWN untracked output does not make its "
      "inputs dirty")
def t_seal_output_excused():
    """RED-VERIFIED against the pre-fix helper: without the exclusion this
    returns true, because the 2-commit seal stamps the MANIFEST *before* the
    commit that adds the release directory, so the release being sealed is
    untracked AT STAMP TIME BY CONSTRUCTION.

    That made `false` unreachable for every seal. It did not stop seals — it
    forced a judgement call, and on usb-hub-3s-v3 v1.6 (2026-07-26) that call
    was resolved by hand-writing `git_dirty: false` into the MANIFEST while
    this tool said `true`. M-REL greps the manifest's own text, so it passed,
    and the release shipped a mechanical claim its own tool contradicted. A
    gate that cannot be satisfied honestly teaches people to satisfy it
    dishonestly."""
    d = fixture_repo()
    rel = d / "projects/board-a/07_releases/v1.0-2026-01-01"
    rel.mkdir(parents=True)
    (rel / "MANIFEST.txt").write_text("m\n")
    # 01_docs must ALREADY be tracked, or git collapses the whole directory to
    # a single "?? .../01_docs/" entry and the CHANGELOG never appears by name.
    # That collapse is real and the exclusion deliberately does NOT cover it: an
    # entirely-untracked 01_docs/ means the board's documented inputs are
    # uncommitted, which is a genuine dirty input, not seal output.
    docs = d / "projects/board-a/01_docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "ARCHITECTURE.md").write_text("arch\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "docs")
    (docs / "CHANGELOG.md").write_text("c\n")
    r = must_pass(helper(d, "board-a"), "untracked seal output is excused")
    contains(r.out, "git_dirty:    false", "inputs are clean, so false")
    contains(r.out, "excused", "the scope line SAYS what it excused")


@test("release_git_dirty: a MODIFIED file in a SEALED release still blocks",
      kind="known_bad")
def t_modified_sealed_release_still_blocks():
    """The exclusion is UNTRACKED-ONLY, and this is the reason. An untracked
    release directory is the seal's own output; a MODIFIED file inside an
    already-sealed release is an edit to an immutable artifact — the exact
    thing CLAUDE.md forbids ('Sealed 04_kicad/ and 07_releases/ are IMMUTABLE
    ... a fix means a NEW release plus SUPERSEDED.md on the old one, never an
    edit'). If the exclusion were status-blind it would hide precisely the
    violation the flag exists to catch, and it would hide it during the one
    operation — sealing — where someone is most likely to commit it."""
    d = fixture_repo()
    rel = d / "projects/board-a/07_releases/v1.0-2026-01-01"
    rel.mkdir(parents=True)
    (rel / "MANIFEST.txt").write_text("sealed\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "seal v1.0")
    (rel / "MANIFEST.txt").write_text("TAMPERED\n")     # edit a sealed file
    r = must_fail(helper(d, "board-a"), "modified sealed release blocks",
                  "git_dirty:    true")
    contains(r.out, "MANIFEST.txt", "names the sealed file that was edited")


if __name__ == "__main__":
    main()
