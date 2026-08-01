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
  contracts_audit.py [--root DIR] [--projects | --present] [--walk]
Default root is the repo this script lives in. THREE scopes, and the suite
reads the RAW EXIT CODE of all three (tests/t1_contracts.py). Never pipe
them — `| tail` reports tail's status.

  (default)    git-tracked, projects/** and archived_projects/** excluded.
               STRICT: any violation exits 1.
  --projects   all git-tracked files. Ratcheted by DEBT_CEILING, per unit.
  --present    tracked UNION untracked-not-ignored — the filesystem walk
               minus everything `git check-ignore` excludes. Adds
               STRAY_UNITS. Implies --projects.
  --walk       filesystem walk instead of git, for fixture trees. Never
               ratcheted (the ceilings are about THIS repo).

COVERAGE — READ THE DENOMINATOR, THEN READ THE EXIT CODE
--------------------------------------------------------
MEASURED 2026-07-31 in /home/mouse9911/gits/circuits:

  scope        files   violations   raw exit
  (default)      280            0          0     280/7414 = 3.8% of the tree
  --projects    7414         2646          0     = DEBT_CEILING exactly
  --present     7523         2650          0     +109 untracked, 1 unit

THE TWO-STAGE HISTORY OF THIS BLOCK IS THE LESSON.

  2026-07-28: the verdict was a bare `243 files, 0 violations`, which READS
  AS COVERAGE and is not — the default scope excluded 96% of the tree. Fixed
  by making the verdict carry its denominator.

  2026-07-31: that fix was HALF of one. It made the gap VISIBLE without
  making it COST anything, and this repo has ratchet FLOORS and no CEILINGS,
  so an honestly declared gap is free. `--projects` kept exiting **1** on
  every suite run for the next three days — 2674 violations — while the test
  running it asserted only that its output did not say "NOT GRADED". Nothing
  read `w.rc`. Fixed by the ceilings below.

THE 2646, CLASSIFIED (canon: violations are CLASSIFIED, never counted). All
C-ALLOW; C-COV and C-ISO are both 0. Graded against the SHIPPED TEMPLATES
rather than each board's own frozen copy:

  2145 (81%)  THE TEMPLATE ALREADY PERMITS THEM. Stale project copies, not
              stray files — the archived boards predate the nested-contract
              convention. Cleared by the standing policy (project copies are
              re-synced from the template on their next revision, never
              retro-edited), so the CONTRACT is what moves, never the board.
   501 (19%)  the template refuses them too:
     256      `.easyeda_cache/**` at BOARD ROOT. The 06_build contract says
              this cache belongs in 06_build (usb-hub-3s, 2026-07-21) — the
              file is misplaced and the contract is right.
      90      sealed releases in the LEGACY FLAT layout (`bom.csv` and the
              gerber zip at release root, no `fab/`). 07_releases is
              IMMUTABLE, so this residue is permanent and honest.
      57      `03_tscircuit/` proof subtrees (backend_proof/, placement_proof/)
      45      `03_src/*.sh` beyond the three named drivers
      17      `03_src/lib/*.kicad_sym` at lib root
      12      loose `01_docs/*.md` (COST_ESTIMATE.md and friends)
      10      `08_reviews/` names short of `<date>_<subject>_<source>_<lens>`
       9      board-root strays: PROGRESS.md, RESUME.md, a loose *.rpt
       5      other single-board oddities

FIXED IN THE SAME CHANGE rather than ceilinged, because these were the
CONTRACT being wrong and a ceiling would have frozen them in:
  * the comma-list parser bug (see parse_allowed) — 124 corrupted patterns
    across 38 contracts, now 0.
  * 06_build gained `verification/**`, `pin_audit/**`, `audit_<date>/**`.
  * 03_tscircuit gained `.gitignore`; 05_firmware gained `target/**` `host/**`.

Do NOT bulk-fix rows to make a number go green; each contract edit is a
statement about what that folder is for.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".tscircuit", "cache"}
ISO_RE = re.compile(rb"projects/(?!<name>)(?=[A-Za-z0-9])[A-Za-z0-9_.-]+")

# ===================== THE CEILINGS (see check_ratchet) =====================
# MEASURED 2026-07-31 in the MAIN worktree /home/mouse9911/gits/circuits at
# c0e21fa7 (+ this change), by `contracts_audit.py --projects`, RAW exit code.
# Recording the tree matters: this repo's suite `failed` count is NOT stable
# across worktrees at one sha (9, 12, 16, 17 and 18 have all been read at the
# same sha — docs/denominator-census.md). `--projects` IS stable, and that is
# VERIFIED rather than assumed: its universe is `git ls-files`, whose output at
# this sha is BYTE-IDENTICAL to `git ls-tree -r --name-only HEAD` (both 7414
# paths, both sha256 55a36824ffa58446…), i.e. the universe is a function of the
# COMMIT, not of the checkout. The one caveat, stated rather than hidden:
# `git ls-files` reads the INDEX, so a tree with files STAGED but not committed
# has a wider universe than its sha implies. That can only ADD files, so it can
# only push a unit ABOVE its row — the ratchet fails loud, never silently green.
#
# WHY THE ROWS ARE PER UNIT AND NOT ONE NUMBER: see unit_of(). A fleet
# aggregate breaks when a new board is commissioned, which is a CORRECT action.
#
# WHY THIS IS NOT THE `/6958 tracked` MISTAKE (t1_contracts.py:77-79, a test
# that pinned the tracked-file count and went red the same day when concurrent
# board work grew the tree): that number measured THE REPO'S SIZE. These
# measure GOVERNANCE DEBT. Adding a correctly-governed file — the normal case,
# and what every one of the 280 default-scope files is — moves no row at all.
# A row moves only when a file lands that its folder's contract does not
# permit, which is the behaviour being gated.
DEBT_CEILING = {
    "archived_projects/ble-bus-bar": 287,
    "archived_projects/cook-hub": 336,
    "archived_projects/cook-loadcell": 180,
    "archived_projects/crow-array": 1,
    "archived_projects/crow-array-central": 354,
    "archived_projects/crow-array-pod": 237,
    "archived_projects/crowsync-recorder": 132,
    "archived_projects/esp32-laser-timing": 235,
    "archived_projects/lipo3s-tsc": 35,
    "archived_projects/lipo3s-usb-hub": 44,
    "archived_projects/shitty-kitty": 330,
    "archived_projects/smc0985-cook": 1,
    "archived_projects/usb-hub-3s": 65,
    "archived_projects/usb-hub-3s-v2": 1,
    "archived_projects/usb-power-3s": 159,
    "archived_projects/xt60-usb-supply-rerun": 142,
    "projects/crow-mic-pod-v2": 1,
    "projects/crow-recorder-central-v2": 9,
    "projects/pluto-rx2-8way-v2": 2,
    "projects/smc0985-cooksense": 79,
    "projects/usb-hub-3s-v3": 16,
}

# ---- the UNTRACKED-NOT-IGNORED half (`--present` only) ---------------------
# WHICH UNITS MAY CARRY UNTRACKED-NOT-IGNORED FILES AT ALL, and why. Value is
# the EVIDENCE for the exemption, not a rationale (CLAUDE.md, Evidence).
#
# THIS RATCHET IS ON PRESENCE, NOT ON VIOLATIONS, AND THAT IS THE WHOLE POINT.
# MEASURED 2026-07-31: point `contracts_audit --walk` at a COPY of a governed
# tree and it reports `0 violations`, RAW EXIT 0 — a copy brings its
# `contracts.md` files with it, so every file in it is permitted by its own
# ancestor. The 3.1 GB stray `git worktree` sitting at this repo's root an hour
# before this was written was exactly that: a full, self-governing, perfectly
# CLEAN copy. A violation-counting stray gate would have graded it green. What
# is wrong with a stray worktree is that it EXISTS, so existence is what is
# graded.
#
# IT IS A SET OF UNITS AND NOT A FILE COUNT, deliberately. A count over an
# in-flight board flaps on every file its author writes — the ratchet then
# fails on correct work, which is how a ratchet gets deleted (the
# `PREC_OWED_CEILING` lesson). The unit set is a PROPERTY — *which* corners of
# the tree may hold uncommitted work — and it is unmoved by how much work
# happens inside a corner already declared.
#
# MEASURED 2026-08-01 after the programmable-usb2-hub source handoff landed:
# zero untracked-not-ignored units remain. The temporary exemption was removed
# in the same process-hardening change; a stale exemption is itself a failure.
# THE SCOPING CONTROL still passes: `~*.kicad_pro.lck` files are gitignored and
# never enter this population.
STRAY_UNITS = {}


def _git(root, *args):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    return sorted(r.stdout.split()) if r.returncode == 0 else []


def untracked_present(root):
    """Files PRESENT in the working tree that git neither tracks NOR ignores.

    THE POPULATION AND WHY IT IS THIS ONE (measured 2026-07-31). A raw
    filesystem walk of this repo is **227883 files** — agent worktrees under
    `.claude/`, `node_modules`, `.easyeda_cache`, build trees — and auditing it
    is useless. The right population is the walk MINUS everything
    `git check-ignore` excludes, because **a file that is neither tracked nor
    ignored is either a violation or something that should not be in the
    repo**. That is 227883 - 220360 = **7523**, of which 7414 are tracked.

    VERIFIED BY TWO INDEPENDENT METHODS (canon M1 — the checker and the checked
    must not share a method): an external `find` walk piped through
    `git check-ignore --stdin`, and git's own
    `ls-files --cached --others --exclude-standard`. Both give 7523 and their
    SYMMETRIC DIFFERENCE IS 0.

    THE SCOPING CONTROL: the eleven `~*.kicad_pro.lck` files strewn across the
    fleet on 2026-07-31 — four of them inside SEALED releases — are now
    gitignored, so a correctly scoped population must report **zero** of them.
    It does. A population still listing them would be walking, not scoping.
    """
    return _git(root, "ls-files", "--others", "--exclude-standard")


def universe(root, walk, present=False):
    if present:
        # tracked ∪ untracked-not-ignored — see untracked_present()
        return sorted(set(_git(root, "ls-files")) | set(untracked_present(root)))
    if not walk:
        got = _git(root, "ls-files")
        if got:
            return got
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


CODE_SPAN = re.compile(r"`([^`]+)`")


def parse_allowed(contract_path):
    """All patterns from every `## Allowed*` section's table rows.

    A pattern cell is read as its BACKTICK CODE SPANS, not as whitespace-
    separated words. Only when the cell has no code span at all is it split on
    whitespace as a bare literal.

    WHY (2026-07-31) — this is the PIPE BUG'S TWIN, found by finally reading
    `--projects`' exit code. The cell

        `build/pcb.svg`, `build/assembly.svg`, `build/board.gltf`

    (03_tscircuit, the `--study` artifacts) was split on whitespace and each
    token `.strip("`")`-ed. `strip` removes a character only while it is at the
    END, and the end of `` `build/pcb.svg`, `` is a COMMA — so the trailing
    backtick survived and the pattern became the literal ``build/pcb.svg`,``,
    which matches no file that can exist. The LAST item in every such list has
    no trailing comma and therefore parsed fine, which is why the defect looked
    like "one odd file" instead of a parser fault: `build/board.gltf` was
    permitted and `build/assembly.svg`, named on the same line of the same
    contract, was not.

    MEASURED before the fix: **124 corrupted patterns across 38 of the repo's
    329 `contracts.md`** — every board's `03_tscircuit` (4 each) and every
    board's `03_src` (2 each). Same failure mode as the pipe bug, same
    consequence: the auditor silently disagrees with the document it enforces,
    so the reader concludes the FILE is wrong rather than the parser.
    """
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
        first = cells[0].strip()
        if first.strip("`").strip().lower() in ("pattern", "path", "file",
                                                "ref", ""):
            continue
        # code spans are the patterns; punctuation BETWEEN them is prose
        for span in (CODE_SPAN.findall(first) or [first]):
            for tok in span.split():
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


def unit_of(f):
    """The RATCHET UNIT a file belongs to — a board, or a top-level folder.

    Per-unit is the whole design, and it is inherited from `PREC_OWED_CEILING`
    (policy_audit.py, 2026-07-30), which learned it the expensive way: a
    FLEET-WIDE integer ceiling **breaks on a correct action**. Commissioning a
    board with un-governed files raises the fleet count, no work on the
    existing boards can prevent it, and the only way to pay is to re-baseline —
    which records nothing and re-breaks on the next board. A board's own debt
    is a thing that board's author controls, it falls only through their work,
    and a NEW board cannot breach ANOTHER board's row.
    """
    p = f.split("/")
    if p[0] in ("projects", "archived_projects") and len(p) > 1:
        return "/".join(p[:2])
    return p[0] if len(p) > 1 else "(root)"


def check_ratchet(label, ceiling, measured, where):
    """EQUALITY per unit, plus both vacuity guards. Returns list[str] failures.

    Equality and not `<=`, so an improvement must be RECORDED in the same
    commit and cannot be banked as slack — that is the pawl. Coverage guard: a
    per-unit map is trivially satisfiable by DELETING rows, so every unit the
    sweep sees must carry one. Staleness guard: a row for a unit the sweep no
    longer sees is a bound nothing measures.
    """
    bad = []
    for u in sorted(set(measured) - set(ceiling)):
        bad.append(f"{label}: UNRATCHETED unit {u!r} carries {measured[u]} "
                   f"violation(s) and has no row. Add `\"{u}\": "
                   f"{measured[u]},` to {where} in the SAME change — an absent "
                   f"row is an unratcheted unit, and a map that may omit units "
                   f"is not a bound.")
    for u in sorted(set(ceiling) - set(measured)):
        bad.append(f"{label}: STALE row {u!r} = {ceiling[u]} — the sweep sees "
                   f"no violations there. Delete it from {where}; a bound "
                   f"nothing measures is not a bound.")
    for u in sorted(set(ceiling) & set(measured)):
        if measured[u] != ceiling[u]:
            verb = ("ROSE — this is the regression the ratchet exists to stop"
                    if measured[u] > ceiling[u] else
                    "FELL — lower the row in the SAME change; slack may not be "
                    "banked, or the ceiling rots back into a free gap")
            bad.append(f"{label}: {u} measured {measured[u]}, row says "
                       f"{ceiling[u]} — it {verb}.")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--projects", action="store_true",
                    help="include projects/** (graded honestly)")
    ap.add_argument("--walk", action="store_true",
                    help="filesystem walk instead of git ls-files")
    ap.add_argument("--present", action="store_true",
                    help="tracked UNION untracked-not-ignored (implies "
                         "--projects): the filesystem walk minus everything "
                         "git check-ignore excludes")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    if args.present:
        args.projects = True

    files = universe(root, args.walk, args.present)
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

    # ---- THE RATCHET (2026-07-31) ---------------------------------------
    # THE HALF-FIX THIS FINISHES. On 2026-07-28 the verdict was made to carry
    # its denominator, because `243 files, 0 violations` was being read as
    # COVERAGE. That made the gap VISIBLE without making it COST anything: this
    # repo has ratchet FLOORS and no CEILINGS, so an honestly declared gap is
    # free, and `--projects` sat at ~2670 violations from that day to this.
    # `tests/t1_contracts.py` ran the wide scope on every suite run and
    # asserted exactly one thing — that the output does not say "NOT GRADED".
    # IT NEVER READ `w.rc`. The gate computed the right answer and threw it
    # away.
    fails = []
    debt = {}
    default_root = Path(__file__).resolve().parent.parent
    if args.projects and not args.walk and root == default_root:
        tracked = set(_git(root, "ls-files"))
        for _cid, f, _why in viol:
            if f in tracked:                 # untracked files are STRAY's job
                debt[unit_of(f)] = debt.get(unit_of(f), 0) + 1
        fails += check_ratchet("DEBT_CEILING", DEBT_CEILING, debt,
                               "scripts/contracts_audit.py")
        if args.present:
            seen = {unit_of(f) for f in untracked_present(root)}
            for u in sorted(seen - set(STRAY_UNITS)):
                fails.append(
                    f"STRAY_UNITS: {u!r} holds UNTRACKED-NOT-IGNORED files. "
                    f"Commit them, gitignore them, or delete them. If it is "
                    f"genuinely in-flight, add `\"{u}\": \"<evidence>\",` to "
                    f"STRAY_UNITS in scripts/contracts_audit.py.")
            for u in sorted(set(STRAY_UNITS) - seen):
                fails.append(
                    f"STRAY_UNITS: STALE row {u!r} — it holds no untracked "
                    f"files any more. Delete the row; an exemption that "
                    f"exempts nothing is how the next stray gets in free.")
        for line in fails:
            print(f"FAIL RATCHET  {line}")
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

    if args.projects and not args.walk and root == default_root:
        print(f"contracts_audit: RATCHET debt {sum(debt.values())} tracked "
              f"violations over {len(debt)} units vs "
              f"{sum(DEBT_CEILING.values())} recorded over "
              f"{len(DEBT_CEILING)} — {'BREACHED' if fails else 'held'}")
        if args.present:
            n = len(untracked_present(root))
            print(f"contracts_audit: RATCHET stray {n} untracked-not-ignored "
                  f"files in {len({unit_of(f) for f in untracked_present(root)})}"
                  f" unit(s); {len(STRAY_UNITS)} declared "
                  f"(population {len(files)} = tracked ∪ untracked-not-ignored)")
        sys.exit(1 if fails else 0)
    sys.exit(1 if viol else 0)


if __name__ == "__main__":
    main()
