#!/usr/bin/env python3
"""release_required_check.py — canon A-EVID: is every REQUIRED release artifact
actually THERE?

    release_required_check.py <release-dir> [--contract PATH] [--json OUT]

WHY THIS EXISTS. `contracts_audit.py` iterates FILES THAT EXIST and asks "is
this permitted?" — C-ALLOW, C-COV, C-ISO all loop over the tree. Nothing ever
walked the contract's REQUIRED list and asked "is it here?". So the ALLOWED
direction was enforced and the REQUIRED direction was enforced by nobody, and
three releases were caught by that in a single day (2026-07-26):

  * usb-hub-3s-v3 v1.6 sealed with 13 files in verification/ where its own
    contract names ~34 REQUIRED. policy_audit was FAIL=0 and contracts_audit
    reported 187 files / 0 violations. M-REL only asks whether verification/
    is non-empty. The MANIFEST asserted DRC 0/0/0 and twin 119/119 with no
    machine evidence in the release for either — and, worse, the missing
    `standalone_archive_drc.json` WAS the gate that would have caught v1.6's
    real defect: its fp-lib-table pointed outside the archive, so 12
    footprints failed to load for anyone who extracted source/.
  * smc0985-cooksense reached a seal attempt with ZERO sha256 hashes in its
    MANIFEST, which the contract requires.
  * crow-mic-pod-v2 v1.1 staged with 9 REQUIRED items absent or MIS-NAMED
    (`bare_top.png` for `render_top_bare.png`, and five more). A mis-named
    required artifact is worse than an absent one: it looks present to a
    human and is invisible to every name-based check.

A diff against the PREVIOUS RELEASE is not a substitute and was tried first.
It makes a board's first release vacuous, and it inherits the predecessor's
omissions — crow-mic-pod's `comm -23` against v1.0 came back EMPTY while nine
contract-required items were missing. THE CONTRACT IS THE AUTHORITY.

NEVER SILENTLY SKIP. Every line of the contract tree is classified, and any
line this parser cannot read is reported as UNPARSED and counts as a failure.
A checker that quietly ignores what it does not understand is the defect it
exists to prevent: `bom_source_check` classified refdes by leading-alpha
prefix and silently dropped 12 of 26 passive rows while printing PASS.
"""
import argparse
import json
import re
import sys
from pathlib import Path

#: a tree line: leading glyphs, the item, then its description column.
TREE_RE = re.compile(r"^(?P<indent>[\s│]*)(?:├──|└──)\s*(?P<item>\S+)\s*(?P<desc>.*)$")

#: a DIRECTORY node carrying contract METAVARIABLE syntax — `<version>-<date>`,
#: `[<board>-]<version>-<date>`. Deliberately a SEPARATE name from
#: PLACEHOLDER_RE below, which rewrites an artifact NAME into a glob: the two
#: questions are different ("is this a real path component?" vs "what filename
#: does this describe?"), and one regex answering both is how a widened
#: contract form would silently change matching behaviour.
METAVAR_DIR_RE = re.compile(r"[<>\[\]]")

#: REQUIRED, but only under a condition the CONTRACT states. These are reported
#: as CONDITIONAL and never as a hard failure — the tool cannot know whether a
#: board is tscircuit-authored or whether a 3D model exists upstream, and
#: guessing would be the same overreach the ALLOWED-only audit made in reverse.
CONDITIONAL_RE = re.compile(
    r"REQUIRED\s+WHERE\s+AVAILABLE|REQUIRED\s+on\s+a\b|REQUIRED\s+if\b|"
    r"REQUIRED\s+when\b|REQUIRED\s+unless\b", re.I)
REQUIRED_RE = re.compile(r"\bREQUIRED\b")

#: an ASCII tree connector — "|--", "+--", "\\--". A contract line shaped like
#: a tree entry but not drawn with box characters is MALFORMED, not prose, and
#: must be reported. Skipping it silently is how my own first implementation
#: reproduced the defect it exists to catch: `|-- verification/` was swallowed
#: as a description line, so verification/ never entered the stack and its
#: children silently inherited the PREVIOUS sibling (3d/, conditional) — a
#: whole required directory vanished from the check while it printed OK.
ASCII_TREE_RE = re.compile(r"^[\s│|+\\]*[|+\\][-]{2,}\s*\S")

#: placeholders the contract writes generically.
PLACEHOLDER_RE = re.compile(r"<[^>]+>")


def tree_block(text):
    """The fenced ``` block that holds the directory tree, or None."""
    blocks = re.findall(r"```[^\n]*\n(.*?)```", text, re.S)
    for b in blocks:
        if "├──" in b or "└──" in b:
            return b
    return None


def item_to_patterns(item):
    """Contract item -> filename glob patterns.

    Handles `stock_check.{txt,csv}` (brace alternation, ALL required) and
    `<board>.kicad_pcb` (placeholder -> wildcard).
    """
    m = re.match(r"^(?P<pre>[^{]*)\{(?P<alts>[^}]*)\}(?P<post>.*)$", item)
    parts = ([f"{m.group('pre')}{a.strip()}{m.group('post')}"
              for a in m.group("alts").split(",")] if m else [item])
    return [PLACEHOLDER_RE.sub("*", p) for p in parts]


def parse(contract_path):
    """(entries, unparsed) — entries are dicts with dir/item/required/conditional."""
    text = Path(contract_path).read_text()
    blk = tree_block(text)
    if blk is None:
        return [], ["no fenced tree block containing '├──' found in the contract"]

    entries, unparsed, stack = [], [], []
    for raw in blk.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if "──" not in line:
            if ASCII_TREE_RE.match(line):
                unparsed.append(line.strip())
            continue                      # else: a description continuation line
        m = TREE_RE.match(line)
        if not m:
            unparsed.append(line.strip())
            continue
        # Indent is 4 chars per level ("│   " or "    "). Do NOT rstrip it:
        # the trailing spaces after a "│" ARE the indent, and stripping them
        # collapsed every level to 0, so every artifact was looked for at the
        # release root instead of inside fab/ pdf/ source/ verification/.
        depth = len(m.group("indent")) // 4
        item, desc = m.group("item"), m.group("desc")
        req = bool(REQUIRED_RE.search(desc))
        cond = bool(CONDITIONAL_RE.search(desc))

        # REQUIRED IS INHERITED BY CONTAINMENT. The contract marks `fab/` and
        # `verification/` REQUIRED and then lists their contents WITHOUT
        # repeating the word — "REQUIRED — the JLCPCB order set" plainly means
        # the set, not just the folder. Reading only literal markers found 3
        # required items in a contract that governs ~30, which would have made
        # this checker agree that a 13-file release was complete: the precise
        # failure it exists to catch.
        parent_req = stack[depth - 1][1] if depth and len(stack) >= depth else False
        parent_cond = stack[depth - 1][2] if depth and len(stack) >= depth else False
        req, cond = req or parent_req, cond or parent_cond

        stack[depth:] = [(item.rstrip("/"), req, cond)]
        if item.endswith("/"):
            continue                      # directories are containers, not artifacts
        # A node describing the RELEASE ROOT is a METAVARIABLE, not a real
        # directory: the root is whatever `release_dir` names. The filter used
        # to be `startswith("<")`, which covered `<version>-<YYYY-MM-DD>/` and
        # NOT the multi-board form the template itself now carries,
        # `[<board>-]<version>-<YYYY-MM-DD>/` — so the literal string
        # "[<board>-]<version>-<YYYY-MM-DD>" was prefixed onto EVERY artifact
        # path and the gate reported "31 missing, 0 present" on a complete
        # release (measured 2026-07-27 on crow-recorder-central-v2 v1.7 the
        # moment its contract was re-synced from the template). A gate that
        # cannot read the CANONICAL contract is broken against every project
        # that syncs to it, so the test is "does this node contain placeholder
        # syntax at all", not "does it start with one particular bracket".
        parent = "/".join(n for (n, _r, _c) in stack[:depth]
                          if not METAVAR_DIR_RE.search(n))
        entries.append({"dir": parent, "item": item,
                        "required": req, "conditional": cond})
    return entries, unparsed


def check(release_dir, contract_path):
    rel = Path(release_dir)
    entries, unparsed = parse(contract_path)
    missing, conditional, present = [], [], []
    for e in entries:
        if not e["required"]:
            continue
        base = rel / e["dir"] if e["dir"] else rel
        hit = any(list(base.glob(p)) for p in item_to_patterns(e["item"])) \
            if base.is_dir() else False
        where = f"{e['dir']}/{e['item']}" if e["dir"] else e["item"]
        if hit:
            present.append(where)
        elif e["conditional"]:
            conditional.append(where)
        else:
            missing.append(where)
    return {"release": str(rel), "contract": str(contract_path),
            "present": present, "missing": missing,
            "conditional_absent": conditional, "unparsed": unparsed}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("release_dir")
    ap.add_argument("--contract", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    rel = Path(a.release_dir)
    contract = Path(a.contract) if a.contract else rel.parent / "contracts.md"
    if not contract.is_file():
        print(f"A-EVID ERROR: no contract at {contract}", file=sys.stderr)
        return 2

    r = check(rel, contract)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2) + "\n")

    for w in r["conditional_absent"]:
        print(f"  CONDITIONAL absent (contract states a condition): {w}")
    for w in r["unparsed"]:
        print(f"  UNPARSED contract line: {w!r}")
    for w in r["missing"]:
        print(f"  MISSING required artifact: {w}")

    bad = len(r["missing"]) + len(r["unparsed"])
    if bad:
        print(f"A-EVID FAIL: {len(r['missing'])} required artifact(s) missing, "
              f"{len(r['unparsed'])} contract line(s) unparsed, "
              f"{len(r['present'])} present")
        return 1
    print(f"A-EVID OK: {len(r['present'])} required artifact(s) present, "
          f"{len(r['conditional_absent'])} conditional absent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
