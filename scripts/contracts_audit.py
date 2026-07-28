#!/usr/bin/env python3
"""Repo structure auditor — every folder is GOVERNED by a contracts.md.

The rule (canon M7): every authored file lives under a contracts.md that
explicitly permits it. Governance is by NEAREST ANCESTOR: a file's governing
contract is the closest contracts.md at or above its directory. A folder
without its own contracts.md is legal only while every file inside it is
matched by a deep pattern (`x/**`) in an ancestor's Allowed table — otherwise
the first unmatched file fails the audit, which is what forces the folder to
either get a contract or get cleaned. Sealed/immutable folders are covered by
their parent's patterns, since adding files to them is forbidden.

Checks:
  C-COV    a file has NO governing contracts.md at all
  C-ALLOW  a file is not matched by any pattern in its governing contract's
           `## Allowed` table(s)
  C-ISO    a file under skills/ references a CONCRETE projects/<board> path
           (the placeholder `projects/<name>` is fine). Skills must reference
           `examples/`, never a live project — a clean-room agent's worktree
           carries no projects, and a skill that points at one is coupled to
           state it cannot see.

Pattern language (first column of the Allowed tables):
  literal names, `*` (one path segment), `**` (any depth), `<placeholder>`
  (= `*`), and `dir/` — which permits the SUBFOLDER plus its `contracts.md`
  only: everything else inside must be matched by that subfolder's own
  contract (or a deep `dir/**` pattern instead, which permits the subtree
  without requiring a nested contract). Cells may hold several
  space-separated patterns. `contracts.md` is implicitly allowed everywhere.

usage:
  contracts_audit.py [--root DIR] [--projects] [--walk]
Default root is the repo this script lives in; default universe is
git-tracked files with projects/** excluded (--projects includes them,
graded honestly per the adopted-forward policy). --walk uses a filesystem
walk instead of git (for fixture trees).

COVERAGE — READ THE DENOMINATOR (measured 2026-07-28)
-----------------------------------------------------
The default invocation grades **243 of 6958 tracked files = 3.5% of the
tree**, and its verdict used to be the bare `243 files, 0 violations`, which
reads as coverage and is not. The verdict now states what it did not grade.

`--projects` reports **6958 files / 2666 violations**, ALL of them C-ALLOW
(C-COV and C-ISO are both 0). Triaged, so the number is a map and not a
scare:

  by cause     2444 (92%)  a file in a SUBFOLDER governed by an ANCESTOR
                           contract — no nested contracts.md and no deep
                           `dir/**` pattern. These are STALE CONTRACTS, not
                           stray files: the archived boards predate the
                           nested-contract convention, so e.g. every
                           `03_src/lib/*.kicad_sym` and
                           `01_docs/decisions/*.md` under them is unmatched.
                222 ( 8%)  the file's OWN directory holds the contract and
                           the name genuinely is not permitted.
  by kind      1616 (61%)  regenerable: `06_build/**` + `.easyeda_cache/**`
                 644 (24%) sealed `07_releases/**` payload (pdf/, cpl.csv,
                           verification/*.png) — immutable, so the CONTRACT
                           is what must move, never the release
  by location  2501 (94%)  archived_projects/**
                 165 ( 6%) live projects/**
  the pipe bug     6       05_firmware (4 headers + 2 stray .md); the 4
                           headers are the class this commit fixed, and they
                           clear when those archived contracts are re-synced
                           from the template — templates are the source of
                           truth and project copies are seeded, never
                           retro-edited.

PROPOSED COVERAGE FIX (not done here — it is a scoped job of its own):
  1. Sync the stage-contract TEMPLATES into the live `projects/**` boards on
     their next revision; that is where the 165 live violations sit and it is
     already the standing policy.
  2. Give `06_build/**` and `.easyeda_cache/**` deep patterns in the stage
     contracts they belong to. 61% of the number is regenerable cache that no
     contract should be enumerating file-by-file.
  3. Then, and only then, make `--projects` the DEFAULT and keep the
     exclusion as an opt-out. Flipping the default first would make the gate
     red for everyone and it would be turned off.
Do NOT bulk-fix 2666 rows to make a number go green; each contract edit is a
statement about what that folder is for.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".tscircuit", "cache"}
ISO_RE = re.compile(rb"projects/(?!<name>)(?=[A-Za-z0-9])[A-Za-z0-9_.-]+")


def universe(root, walk):
    if not walk:
        r = subprocess.run(["git", "ls-files"], cwd=root,
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return sorted(r.stdout.split())
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_dir() or any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p.relative_to(root).as_posix())
    return out


def split_row(line):
    """Markdown table cells, splitting ONLY on pipes that are real delimiters.

    A `|` is a delimiter unless it is BACKSLASH-ESCAPED (`\\|`, the GFM way to
    put a pipe in a cell) or sits INSIDE a backtick code span.

    WHY (2026-07-28). The naive `line.split("|")` tore
    `` `*.c|*.h|*.rs|*.py` `` — the 05_firmware contract's one Allowed row —
    into four cells, so only `*.c` was ever read as a pattern and EVERY
    FIRMWARE HEADER IN THE REPO failed C-ALLOW. Six live failures in
    `archived_projects/` prove it, and it is why a constant shipped as a `.c`
    rather than the `.h` it belonged in. A parser that silently keeps the
    first fragment of a pattern list is worse than one that rejects the row:
    the contract SAYS `.h` is permitted and the audit disagrees, so the author
    concludes the file is wrong rather than the parser.
    """
    cells, cur, tick, i = [], [], False, 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur.append("|")            # an escaped pipe is CONTENT
            i += 2
            continue
        if c == "`":
            tick = not tick
        if c == "|" and not tick:
            cells.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    cells.append("".join(cur))
    # `line.strip("|")` used to drop the leading/trailing delimiters; do the
    # same by discarding the empty edge cells they produce.
    if cells and not cells[0].strip():
        cells = cells[1:]
    if cells and not cells[-1].strip():
        cells = cells[:-1]
    return [c.strip() for c in cells]


def parse_allowed(contract_path):
    """All patterns from every `## Allowed*` section's table rows."""
    pats = []
    in_allowed = False
    for line in contract_path.read_text(errors="replace").splitlines():
        if line.startswith("## "):
            in_allowed = line.lower().startswith("## allowed")
            continue
        if not in_allowed or not line.startswith("|"):
            continue
        cells = split_row(line)
        if not cells or set(cells[0]) <= {"-", " ", ":"}:
            continue
        first = cells[0].strip("`").strip()
        if first.lower() in ("pattern", "path", "file", "ref", ""):
            continue
        for tok in first.split():
            pats.append(tok.strip("`"))
    return pats


def pat_to_regex(pat):
    # `a|b|c` is ALTERNATION — one pattern cell listing several extensions,
    # which is how `*.c|*.h|*.rs|*.py` reads to anyone writing a contract.
    # Without this the fixed splitter would hand the whole string through as a
    # single literal and the row would still permit nothing.
    if "|" in pat:
        subs = [pat_to_regex(p).pattern for p in pat.split("|") if p]
        return re.compile("(?:" + "|".join(s[:-1] if s.endswith("$") else s
                                           for s in subs) + ")$")
    if pat.endswith("/"):
        # a governed subfolder: only its own contracts.md rides on this row
        return re.compile(re.escape(pat) + r"contracts\.md$")
    pat = re.sub(r"<[^>]*>", "*", pat)
    out = []
    i = 0
    while i < len(pat):
        if pat.startswith("**", i):
            out.append(".*")
            i += 2
        elif pat[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(pat[i]))
            i += 1
    return re.compile("".join(out) + "$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--projects", action="store_true",
                    help="include projects/** (graded honestly)")
    ap.add_argument("--walk", action="store_true",
                    help="filesystem walk instead of git ls-files")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    files = universe(root, args.walk)
    total = len(files)
    if not args.projects:
        files = [f for f in files
                 if (not f.startswith("projects/")
                     or f == "projects/contracts.md")
                 and (not f.startswith("archived_projects/")
                      or f == "archived_projects/contracts.md")]
    excluded = total - len(files)

    # contract cache: dir posix path -> list[regex] or None
    cache = {}

    def contract_for(dirpath):
        if dirpath in cache:
            return cache[dirpath]
        c = root / dirpath / "contracts.md" if dirpath else root / "contracts.md"
        val = None
        if c.is_file():
            val = (dirpath, [pat_to_regex(p) for p in parse_allowed(c)])
        cache[dirpath] = val
        return val

    def governing(relfile):
        d = "/".join(relfile.split("/")[:-1])
        while True:
            got = contract_for(d)
            if got:
                return got
            if not d:
                return None
            d = "/".join(d.split("/")[:-1])

    viol = []
    for f in files:
        base = f.split("/")[-1]
        gov = governing(f)
        if gov is None:
            viol.append(("C-COV", f, "no governing contracts.md anywhere"))
            continue
        gdir, regexes = gov
        if base == "contracts.md" and (not gdir or f == gdir + "/contracts.md"):
            continue          # a contract governs itself
        rel = f[len(gdir) + 1:] if gdir else f
        if not any(rx.match(rel) for rx in regexes):
            viol.append(("C-ALLOW", f,
                         f"not permitted by {gdir or '.'}/contracts.md"))

    for f in files:
        if not f.startswith("skills/"):
            continue
        try:
            data = (root / f).read_bytes()
        except OSError:
            continue
        for m in ISO_RE.finditer(data):
            frag = m.group(0).decode(errors="replace")
            viol.append(("C-ISO", f, f"references '{frag}' — skills must "
                         f"cite examples/, never a live project"))
            break

    for cid, f, why in viol:
        print(f"FAIL {cid:8s} {f}: {why}")
    # ---- THE DENOMINATOR (canon M-COVER / G-COVER, 2026-07-28) ------------
    # `contracts_audit: 243 files, 0 violations` was being read as COVERAGE.
    # It is not: the default universe EXCLUDES projects/** and
    # archived_projects/**, which on 2026-07-28 was 6715 of 6958 tracked files
    # — the invocation CLAUDE.md names grades 3.5% of the tree. A verdict that
    # does not carry its own denominator invites exactly that reading, which
    # is why every other gate in this pipeline prints N/M.
    scope = f"{len(files)} files"
    if excluded:
        scope += (f" ({len(files)}/{total} tracked; {excluded} in projects/** "
                  f"and archived_projects/** NOT GRADED — rerun with "
                  f"--projects)")
    print(f"contracts_audit: {scope}, {len(viol)} violations")
    sys.exit(1 if viol else 0)


if __name__ == "__main__":
    main()
