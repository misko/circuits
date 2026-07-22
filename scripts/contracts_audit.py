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
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or set(cells[0]) <= {"-", " ", ":"}:
            continue
        first = cells[0].strip("`").strip()
        if first.lower() in ("pattern", "path", "file", "ref", ""):
            continue
        for tok in first.split():
            pats.append(tok.strip("`"))
    return pats


def pat_to_regex(pat):
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
    if not args.projects:
        files = [f for f in files
                 if (not f.startswith("projects/")
                     or f == "projects/contracts.md")
                 and (not f.startswith("archived_projects/")
                      or f == "archived_projects/contracts.md")]

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
    print(f"contracts_audit: {len(files)} files, {len(viol)} violations")
    sys.exit(1 if viol else 0)


if __name__ == "__main__":
    main()
