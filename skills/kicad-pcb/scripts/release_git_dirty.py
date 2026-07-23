#!/usr/bin/env python3
"""release_git_dirty.py — the release seal's `git_dirty` flag, scoped to a
release's ACTUAL regeneration inputs.

A board's fab set regenerates from exactly two things: its own project subtree
(``projects/<board>/{02_parts,03_src,03_tscircuit}`` and the rest of the
board's stage folders) and the shared skill backend (``skills/``). Nothing
else feeds the gerbers. So the seal's clean-tree guarantee is scoped to those
inputs and nothing more:

    the release is CLEAN  iff  ``git status --porcelain -- projects/<board>/ skills/``
    is empty.

A dirty SIBLING project (a concurrently-building board) has ZERO bearing on
THIS release's reproducibility and MUST NOT block the seal. The whole-repo
``git status --porcelain`` this replaces DID block on it, forcing
pause-coordination between independent boards (2026-07-23). A dirty ``skills/``
backend, or a dirty / untracked file inside this board's own subtree, DOES
block: those are the inputs the gerbers are reproducible from.

Why the board's own ``07_releases/`` / ``06_build/`` / ``01_docs/`` sit inside
the in-scope subtree and are still checked: the seal commits the board's own
artifacts first, so at ``git_sha`` the whole subtree is committed-clean; a
leftover uncommitted input there is a real reproducibility hole and SHOULD
block. Only OTHER boards are out of scope.

Usage:
    release_git_dirty.py <board-name | project-path> [--repo-root DIR]

      <board-name>    resolves to ``projects/<board-name>``
      project-path    an existing directory (a ``projects/<board>`` path,
                      relative to the repo root or absolute)
      --repo-root DIR repo top (default: ``git rev-parse --show-toplevel``
                      from the project path, or the cwd)

Output (stdout): the exact MANIFEST ``git_dirty`` line, scope noted, e.g.
    git_dirty:    false                   # scope: projects/<board>/ + skills/
When dirty the offending ``git status --porcelain`` lines are echoed to stderr.
Exit: 0 clean, 1 dirty, 2 usage/resolution error. The seal calls this and
gates on the exit code rather than eyeballing ``git status``.

Provenance: rescoped from a repo-wide clean-check that blocked a board's seal
on unrelated sibling-project dirt (skill fix, 2026-07-23).
"""
import subprocess
import sys
from pathlib import Path

SKILLS_DIR = "skills"


def _sh(args, cwd=None):
    return subprocess.run([str(a) for a in args],
                          cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True)


def _die(msg, code=2):
    sys.stderr.write(msg.rstrip("\n") + "\n")
    raise SystemExit(code)


def repo_root(start, override=None):
    if override:
        return Path(override).resolve()
    r = _sh(["git", "rev-parse", "--show-toplevel"], cwd=start)
    if r.returncode != 0:
        _die(f"not inside a git repo (start={start}): {r.stderr.strip()}")
    return Path(r.stdout.strip()).resolve()


def resolve_project(arg, root):
    """(project_dir_abs, rel_to_root) for a bare board name or a path."""
    p = Path(arg)
    if p.is_absolute():
        candidates = [p]
    else:
        # a path relative to the repo root, or a bare board name under projects/
        candidates = [root / arg, root / "projects" / arg]
    for c in candidates:
        if c.is_dir():
            c = c.resolve()
            try:
                rel = c.relative_to(root)
            except ValueError:
                _die(f"project {c} is not inside repo root {root}")
            return c, rel
    _die(f"no such project: {arg!r} (looked for "
         f"{[str(c) for c in candidates]})")


def git_dirty(board, repo_root_override=None):
    """(dirty: bool, porcelain: str, scope_label: str) for a board's inputs.

    Scope is the board's own subtree + ``skills/`` — a dirty sibling project
    is deliberately invisible here.
    """
    start = Path(board)
    start_dir = start if start.is_dir() else Path.cwd()
    root = repo_root(start_dir, repo_root_override)
    _proj_abs, rel = resolve_project(board, root)
    rel = str(rel).rstrip("/") + "/"
    r = _sh(["git", "status", "--porcelain", "--", rel, SKILLS_DIR + "/"],
            cwd=root)
    if r.returncode != 0:
        _die(f"git status failed: {r.stderr.strip()}")
    porcelain = r.stdout.rstrip("\n")
    scope = f"{rel} + {SKILLS_DIR}/"
    return bool(porcelain.strip()), porcelain, scope


def manifest_line(dirty, scope):
    val = "true" if dirty else "false"
    label = f"git_dirty:    {val}"
    return f"{label:<38}# scope: {scope} (never seal with these inputs dirty)"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root_override = None
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-h", "--help"):
            sys.stdout.write((__doc__ or "") + "\n")
            return 0
        if a == "--repo-root":
            i += 1
            if i >= len(argv):
                _die("--repo-root needs a directory argument")
            root_override = argv[i]
        elif a.startswith("--repo-root="):
            root_override = a.split("=", 1)[1]
        elif a.startswith("-"):
            _die(f"unknown flag: {a}")
        else:
            pos.append(a)
        i += 1
    if len(pos) != 1:
        _die("usage: release_git_dirty.py <board|project-path> "
             "[--repo-root DIR]")
    dirty, porcelain, scope = git_dirty(pos[0], root_override)
    print(manifest_line(dirty, scope))
    if dirty:
        sys.stderr.write(
            f"DIRTY — uncommitted release inputs (scope: {scope}):\n"
            f"{porcelain}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
