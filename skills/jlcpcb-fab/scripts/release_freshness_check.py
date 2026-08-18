#!/usr/bin/env python3
"""RELEASE-ARTIFACT FRESHNESS gate.

A release seal must ship the CURRENT board's own outputs, a manifest whose
claimed result matches the audit it bundles, and a FINAL (not draft) order
README. This gate FAILS a seal on three ways that combination has silently
broken in the past — each one a DO-NOT-ORDER defect no other gate caught.

Motivating incident (usb-hub-3s-v3 v1.2, 2026-07-23 — a redesigned board):

  (a) STALE ARTIFACT. pdf/assembly_back.pdf, pdf/assembly_front.pdf and
      pdf/pcb_layers.pdf were BYTE-IDENTICAL (sha256-confirmed) to the PRIOR
      release v1.1's same-named files — the redesigned board shipped the OLD
      board's fab drawings. A changed board's generated fab/PDF outputs MUST
      differ from an earlier release of the same board.

  (b) AUDIT / MANIFEST DISAGREEMENT. The shipped verification/policy_audit.md
      said "M-BOM FAIL" / "Summary: FAIL=1", while the MANIFEST claimed
      "policy_audit: 0 FAIL" and "M-BOM ... PASS". The bundle contradicted its
      own claimed result — the manifest under-reported the audit it ships.

  (c) DRAFT README. The shipped ORDER_README.md was a working draft
      ("> DRAFT for the v1.2 seal", "fold its verdict in before seal") — a
      pre-seal staging document, not the final order document.

Second motivating incident (crow-recorder-central-v2 v1.0, 2026-07-23 —
found 2026-07-24, AFTER sealing):

  (d) MANIFEST SELF-INCONSISTENCY. The manifest's human-readable gate
      summary disagreed with the machine evidence it SHIPS, three ways at
      once, and no gate caught any of them:
        - MANIFEST said "ERC 0 errors (1409 baselined warnings)" while the
          bundled verification/policy_audit.md said "S-ERC PASS 0 errors
          (1215 warnings)" (the bundled erc.json measures 1409 — the audit
          row was the stale one);
        - MANIFEST said "bom_source_check PASS (48 lines...)" while
          fab/bom.csv actually carries 49 data rows;
        - verification/bom_source_check.txt named
          "07_releases/v1.0-2026-07-23/fab/bom.csv" — a directory that is
          NOT this release's sealed name
          (crow-recorder-central-v2-v1.0-2026-07-23): the evidence was
          produced against a staging path and never re-pointed.
      Check (b) compares only the policy_audit RESULT, and the stale check
      compares only bytes across releases — prose counts and embedded paths
      had no gate. Check (d) closes that: any COUNT the MANIFEST states
      that is also present in shipped evidence must MATCH (ERC errors /
      warnings across MANIFEST, policy_audit.md's S-ERC row, and erc.json;
      bom_source_check's claimed line count vs fab/bom.csv's actual data
      rows), and any 07_releases/<dir>/ path embedded in verification
      evidence must name THIS release's directory (or an EXISTING sibling
      release — diffing against a real predecessor is legitimate). A count
      the MANIFEST does not state is not checked: absence != mismatch.

Fifth check — A-STOCK, always on (2026-07-25, the PCBA-default posture):

  (e) STOCK EVIDENCE THAT DOES NOT PASS. Five sealed releases in this fleet
      ship `verification/stock_check.*` whose LAST LINE says FAIL —
      crow-recorder-central-v2 v1.0-v1.3 record their own CPU (C6938291, the
      XU316 SoC) at LOW_STOCK(0) — because nothing ever parsed the verdict.
      Check (e) grades the shipped evidence for every coded BOM line that has
      a CPL row: stock >= qty x `build_quantity`, or a matching
      `03_src/rules/assembly.yaml` `sourcing_plan:` entry with
      `measured_stock` + `measured_on`. A MISSING OR UNPARSEABLE VERDICT IS A
      FAIL, NOT A SKIP: cooksense v1.1 ships a raw `--out` CSV report as
      stock_check.txt with ZERO verdict lines, so a parser that shrugged at an
      unfamiliar shape could be silenced by choosing a shape. The check is
      OFFLINE — it grades EVIDENCE; live re-query stays in the opt-in --net
      tier, because a gate that needs the network is a gate that gets skipped.

A SEAL MAKES TWO CLAIMS AND THIS GATE USED TO HAVE ONE FIELD FOR BOTH
(2026-07-30, checks (f) A-BUY and (g) M-REV):

    | claim                        | who can answer it            |
    |------------------------------|------------------------------|
    | *this design is correct*     | the design gates, at SEAL time |
    | *this design is orderable*   | JLCPCB allocation, at ORDER time |

  Every other check here grades an artifact WE CONTROL, so a red means *there
  exists an edit to this design that turns it green* and blocking the seal is
  right. Historically **A-STOCK graded the WORLD** through catalog
  `stockCount`; that mode remains only for sealed-release compatibility. One
  reading moved from 0 on 2026-07-29 to 5 on 2026-07-30 on the same unchanged
  board, and NO EDIT
  TO THE DESIGN CHANGES IT. Measured cost of merging the two claims into one
  verdict: smc0985-cooksense v1.7 reached DRC 0/0/0, `policy_audit` FAIL=0,
  ERC 0, E-INV 167/167, both red-team lenses graded — and NINE successive
  agents declined to seal it, every one of them on one BOM line whose
  `minPurchaseNum` (21) exceeds its entire `stockCount` (5). Nine refusals,
  zero design defects. The last red-team lens wrote, verbatim: *"I would accept
  the seal ... but sealing is not the question this verdict field asks."*

  So the gate now grades and prints TWO verdicts, and `--claim` grades either
  one alone:

      DESIGN:   PASS | FAIL (n finding(s))
      SOURCING: CLEAR | PLANNED-<n> | BLOCKED-<n> [ + FAIL (n finding(s)) ]

  THIS IS NOT AN ESCAPE HATCH, AND IT IS A NET TIGHTENING. Before it, a
  `sourcing_plan:` entry SILENTLY CLEARED its line whatever its own measured
  number said — `if code in plan: continue` — so a release could seal
  unbuyable with nothing anywhere saying so. Now:

  (f) A-BUY — THE SOURCING CLAIM IS CLASSIFIED, AND A NON-ORDERABLE RELEASE
      MUST SAY SO WHERE THE BUYER LOOKS.

      **THE ID IS `A-BUY` AND NOT `A-ORDER`, AND THAT IS NOT A STYLE CHOICE.**
      This check was drafted as `A-ORDER`, which has meant something ELSE since
      2026-07-17 (`ae93b4b`): `rules_audit.py`'s A-ORDER asserts that
      `generate_rules.py` is the LAST step to touch the project before the DRC
      gate, because a pcbnew save clobbers netclasses. It is load-bearing and
      cited by name in `tests/README.md`, `t4_regressions.py`,
      `t1_rules_bom.py` and `t1_assembly_gates.py`. Two unrelated checks under
      one ID is the M-WIDTH failure inverted — one NAME, two policies — and it
      is worse than a missing ID: a canon row would have had to describe both,
      a waiver written for either would read as covering the other, and a
      fleet-wide `grep A-ORDER` would answer neither question. `A-BUY` reads
      alongside `A-STOCK` (can we buy it / is it in stock) and collides with
      nothing: MEASURED 2026-07-30, zero occurrences anywhere in the repo
      before this change.

      A `sourcing_plan:` entry whose own
      `measured_stock` does not cover `qty x build_quantity` MUST declare
      `order_status: PLANNED|BLOCKED` — PLANNED means the plan makes the
      catalog irrelevant for that line (consignment, self-supply), BLOCKED
      means it cannot be bought as sealed. An unclassified shortfall is a FAIL
      (it used to be a silent pass). A release measured BLOCKED-<n> may seal,
      and ONLY if BOTH `MANIFEST.txt` and the FIRST SCREEN of `ORDER_README.md`
      carry the gate line

          SOURCING: BLOCKED-<n> (C265111; measured 2026-07-30)

      whose status, count, LCSC set and date all MATCH the measurement, in both
      directions — a release may neither hide a blocked line nor invent one.
      The date must be the newest `measured_on` of the blocking entries and may
      not predate the release by more than 7 days: a stock reading is
      perishable, and an undated one is not evidence.

  (g) M-REV — THE REVIEW VERDICTS, WHICH NOTHING HAS EVER PARSED. The
      07_releases contract has required "both lenses' verdicts = ORDER" since
      it was written and no gate read the field. MEASURED 2026-07-30, quoted
      against its population denominator (canon M-COVER): of 33 sealed
      release dirs, 21 ship both contract-named lens files, and 9 OF THOSE 21
      carry an ungradeable verdict on at least one lens — 5 with no verdict
      KEY at all, 8 with a value outside every stated vocabulary, overlap 4.
      Only 12 of 21 are parseable. The commonest shape is `verdict: DO NOT
      ORDER` written as prose after the colon (first token `DO`); cooksense
      v1.5's shipped `redteam_layout.md` does not use the key at all — line 5
      reads `VERDICT AT RUN TIME: **DO NOT ORDER.**` — a sealed release
      carrying a DO-NOT-ORDER review nobody read. The review
      header is therefore graded as a CLOSED VOCABULARY, never scraped from
      prose (that is the R-LEN word-credit defect):

          design_verdict: SOUND | DEFECTIVE          -> the DESIGN claim
          order_verdict:  ORDER | DO-NOT-ORDER | BLOCKED-SOURCING

      A legacy single `verdict:` maps CONSERVATIVELY — `DO-NOT-ORDER`/`FAIL`
      become DEFECTIVE, so no existing review is retroactively converted into
      an acceptance; the split gives the NEXT reviewer the vocabulary, it does
      not rewrite the last one's judgement. A missing or out-of-vocabulary
      verdict is a FAIL, never a skip (the A-STOCK clause, applied to reviews).
      `order_verdict` is cross-checked against (f)'s MEASUREMENT: a lens may
      not say ORDER on a release measured BLOCKED, nor BLOCKED-SOURCING on one
      measured CLEAR.

  ORDER-TIME RE-GRADE. New pipelines use `--claim sourcing
  --sourcing-authority jlc-pcba --pcba-evidence RECEIPT.json`. Only a fresh,
  exact-BOM, quantity-expanded `ALLOCATED` receipt may clear the order claim.
  `--stock-evidence` and the default `catalog-legacy` authority remain solely
  so historical sealed releases retain their original interpretation.

Usage:
    release_freshness_check.py <release_dir> [--releases-root DIR]
                               [--assembly 03_src/rules/assembly.yaml]
                               [--allow-identical RELPATH ]...
    release_freshness_check.py <release_dir> [--claim design|sourcing|both]
                               [--stock-evidence FRESH.json]
    release_freshness_check.py <release_dir> --claim sourcing
                               --sourcing-authority jlc-pcba
                               --pcba-evidence RECEIPT.json
    release_freshness_check.py <release_dir> --docs-only-supersede PRIOR_DIR
    release_freshness_check.py <release_dir> --legible-bom-supersede PRIOR_DIR
    release_freshness_check.py <release_dir> --sourcing-supersede PRIOR_DIR
    release_freshness_check.py <release_dir> --value-change-supersede PRIOR_DIR
                               --designators R4,R5

VALUE-CHANGE SUPERSEDE MODE (--value-change-supersede <prior> --designators):
a PART VALUE moved on parts that are already placed (22k -> 33k on an existing
0603), so the ASSEMBLY DATA moves and the COPPER does not. Measured on
crow-mic-pod-v2 v1.3, 2026-07-28: `export_jlc_package.py` reads
`val = fp.GetValue()` FROM THE BOARD and feeds that one string to BOTH the BOM
`Comment` column and the CPL `Val` column, so a pure value change moves the
`.kicad_pcb`, the `.kicad_sch`, the `.net`, the BOM rows for those refs and
exactly their CPL `Val` cells — while all 11 gerbers and drills stay
BYTE-IDENTICAL. Every earlier mode refuses it, correctly and for its own
reason: docs-only needs fab/ identical, bom-only permits only row REMOVAL of
UNPLACED refs, legible-bom reads a changed LCSC as a substitution, sourcing
demands an md5-identical board and a byte-identical CPL, and cpl-only names a
`Val` change as its own explicit exclusion. Without this mode the only way to
seal a copper-identical value fix is to hand-edit a CSV, which canon M3
forbids. See `check_value_change_delta`.

SOURCING SUPERSEDE MODE (--sourcing-supersede <prior-release-dir>):
the board is untouched and JLC will not SUPPLY one line of the prior BOM, so a
part is SUBSTITUTED — `MPN` + `LCSC` move on the affected rows and nothing else
does. Promoted under canon M8 (two-strike): usb-hub-3s-v3 v1.11 sealed this
exact shape gated by SEVEN individually-measured file waivers because no mode
permitted a changed LCSC, and crow-recorder-central-v2 v1.7 needs the identical
thing. A waiver a human writes is weaker evidence than an assertion the gate
makes; this mode makes the assertion. See `check_sourcing_delta`.

LEGIBLE-BOM SUPERSEDE MODE (--legible-bom-supersede <prior-release-dir>):
canon F-LEGIBLE (ADR-0006) — the board is untouched and `fab/bom.csv` is
rewritten so JLC's web processing can PARSE it (MPN filled from the part's own
dossier, a Comment no longer an LCSC code or a `simple_*` placeholder, a UTF-8
byte-order-mark). Docs-only mode refuses (fab/ changed) and bom-only mode
refuses too (it FAILs on an EDITED row, correctly, for the A-POP defect IT
guards). This mode exempts exactly `fab/bom.csv` and then asserts something
STRONGER than identity about it: every row's designator group, Footprint and
LCSC UNCHANGED, no row added or removed, no MPN blanked, only Comment/MPN
moving — and the new BOM must PASS `bom_legibility_check` while the prior one
FAILs it. See `check_legible_bom_delta`.

DOCS-ONLY SUPERSEDE MODE (--docs-only-supersede <prior-release-dir>):
a documentation-only supersede release (usb-hub-3s-v3 v1.4, 2026-07-23)
INTENTIONALLY ships its fab outputs byte-identical to its predecessor — the
board did not change, only the documentation did. The default stale check
would flag exactly that identity as a defect. In this mode the declared
identity is ASSERTED instead of flagged:

  - fab/, source/, 3d/ MUST be byte-identical to the prior release (any
    differing, missing, or added file is a FAIL — a "docs-only" release
    that changes fab is lying about being docs-only);
  - pdf/ identical to the prior release is ALLOWED (not flagged);
  - the order README and MANIFEST MUST DIFFER from the prior release's (a
    supersede that changes no document supersedes nothing);
  - checks (b) audit==manifest and (c) no draft markers still run.

`<release_dir>` is one sealed release directory,
`07_releases/<version>-<date>/`. Earlier releases of the SAME board are its
siblings under `07_releases/` with a strictly-lower version; they are read
READ-ONLY for the stale comparison. Exit 0 = fresh, non-zero = a defect that
must block the seal.

Documented exception mechanism (for a legitimately-unchanged file across a
doc-only re-release — the edge case): list the relative path, WITH a reason,
one per line in `<release_dir>/verification/freshness_exceptions.txt`
(`pdf/schematic.pdf   reason: doc-only re-release, board unchanged`), or pass
`--allow-identical pdf/schematic.pdf`. An exception without a reason in the
file is itself rejected — a waiver needs evidence, not a bare path.
"""
import argparse
import hashlib
import re
import sys
from pathlib import Path

# Generated fab/drawing artifacts whose bytes MUST change for a changed board.
# Compared subtrees; within them every file is a generated output.
_ARTIFACT_DIRS = ("pdf", "fab")

# README draft / placeholder markers. Word-bounded, case-insensitive.
_DRAFT_MARKERS = ("DRAFT", "TODO", "TBD", "FIXME", "WIP",
                  "PLACEHOLDER", "XXX", "FILL ME", "FILL-ME")


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# RELEASE NAMING AND ORDERING LIVE IN ONE PLACE: release_index.py, in this
# same directory. This module used to own them, and policy_audit.py imported
# `_version_key` from here; both names are re-exported so those callers keep
# working, but there is exactly ONE implementation of "which board is this
# release for" and "which of them is newer" in the repo (canon M-WIDTH — the
# rule is written at the width of the class, so no consumer of release
# ordering can quietly re-derive it differently).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_index import (_NAME_RE, _version_key,            # noqa: E402,F401
                           earlier_releases as _earlier_releases,
                           parse_release_name, slug)          # noqa: F401


def _artifacts(release_dir: Path):
    """(relpath-posix, Path) for every generated fab/drawing file."""
    for sub in _ARTIFACT_DIRS:
        d = release_dir / sub
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file():
                yield p.relative_to(release_dir).as_posix(), p


def _load_exceptions(release_dir: Path):
    """{relpath: reason} from verification/freshness_exceptions.txt. A line
    with a path but no reason is rejected (returned in `bad`)."""
    allow, bad = {}, []
    f = release_dir / "verification" / "freshness_exceptions.txt"
    if not f.is_file():
        return allow, bad
    for raw in f.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # "relpath   reason words..." — split on first run of whitespace
        parts = line.split(None, 1)
        rel = parts[0]
        reason = parts[1].strip() if len(parts) > 1 else ""
        if not reason:
            bad.append(rel)
        else:
            allow[rel] = reason
    return allow, bad


# --------------------------------------------------------------- check (a)
def check_stale(release_dir, releases_root, allow):
    """Any generated artifact sha256-identical to the same-named file in an
    EARLIER release of the same board (unless waived)."""
    findings = []
    earlier = _earlier_releases(release_dir, releases_root)
    for rel, path in _artifacts(release_dir):
        h = _sha256(path)
        for older in earlier:
            other = older / rel
            if other.is_file() and _sha256(other) == h:
                if rel in allow:
                    findings.append(
                        f"  note: {rel} identical to {older.name}/{rel} "
                        f"— WAIVED ({allow[rel]})")
                    continue
                findings.append(
                    f"  STALE: {rel} is sha256-IDENTICAL to "
                    f"{older.name}/{rel} — a changed board must not ship an "
                    f"earlier release's generated output")
    fails = [f for f in findings if f.lstrip().startswith("STALE:")]
    return fails, [f for f in findings if not f.lstrip().startswith("STALE:")]


# ------------------------------------------ docs-only supersede identity
# Subtrees a docs-only supersede must ship UNCHANGED. pdf/ is deliberately
# absent: identical drawings are allowed (the board did not change), but they
# are not required — a regenerated-but-equal-content PDF may differ in bytes
# (timestamps), and neither direction makes the release less docs-only.
_DOCS_ONLY_IDENTICAL_DIRS = ("fab", "source", "3d")


def _tree_files(d: Path):
    """{relpath-posix: Path} for every file under d ({} if d is absent)."""
    if not d.is_dir():
        return {}
    return {p.relative_to(d).as_posix(): p
            for p in sorted(d.rglob("*")) if p.is_file()}


def check_bom_delta(release_dir, prior_dir):
    """BOM-ONLY mode's EXTRA assertion: the one permitted fab/ change is the
    REMOVAL of whole BOM rows for designators that were never on the CPL.

    This is strictly STRONGER than "the file differs", which is all a plain
    diff could say. It pins the exact shape of the fix that canon A-POP
    prescribes — an unplaced part must LEAVE the assembly BOM — and it fails
    on the two things that would make a "BOM-only" claim a lie: a row that
    was ADDED or EDITED (a value/code change is a different board), and the
    removal of a row for a designator JLC is still told to place.

    Motivating case (crow-mic-pod-v2 v1.1, 2026-07-25): v1.0's bom.csv
    carried MK1 with its MPN *and* LCSC columns both empty and J1 at stock 0,
    neither on the CPL. Removing them changes fab/ — so docs-only mode
    correctly refuses — while changing no copper whatsoever."""
    fails, notes = [], []
    cur_p, old_p = release_dir / "fab" / "bom.csv", prior_dir / "fab" / "bom.csv"
    if not (cur_p.is_file() and old_p.is_file()):
        fails.append("  BOM-ONLY: fab/bom.csv missing on one side — cannot "
                     "establish the delta")
        return fails, notes

    def rows(p):
        import csv as _csv
        out = {}
        for r in _csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()):
            refs = tuple(sorted(d.strip() for d in
                                (r.get("Designator") or "").split(",") if d.strip()))
            if refs:
                out[refs] = tuple((k, (v or "").strip()) for k, v in sorted(r.items()))
        return out

    cur, old = rows(cur_p), rows(old_p)
    cpl = release_dir / "fab" / "cpl.csv"
    placed = set()
    if cpl.is_file():
        import csv as _csv
        placed = {(r.get("Designator") or "").strip()
                  for r in _csv.DictReader(cpl.read_text(encoding="utf-8-sig").splitlines())
                  if (r.get("Designator") or "").strip()}
    added = sorted(set(cur) - set(old))
    removed = sorted(set(old) - set(cur))
    changed = sorted(k for k in set(cur) & set(old) if cur[k] != old[k])
    for k in added:
        fails.append(f"  BOM-ONLY DEVIATION: row {list(k)} was ADDED — a "
                     f"BOM-only supersede may only REMOVE rows for parts that "
                     f"are not placed; adding one is a sourcing change")
    for k in changed:
        fails.append(f"  BOM-ONLY DEVIATION: row {list(k)} was EDITED — a "
                     f"changed value/footprint/LCSC is a different board, not "
                     f"a paperwork fix")
    for k in removed:
        still = sorted(set(k) & placed)
        if still:
            fails.append(
                f"  BOM-ONLY DEVIATION: row {list(k)} was removed but "
                f"{still} are STILL ON THE CPL — JLC is told to place a part "
                f"with no BOM line at all")
    if not fails:
        notes.append(
            f"  note: fab/bom.csv delta is {len(removed)} whole row(s) REMOVED "
            f"({', '.join(','.join(k) for k in removed) or 'none'}), 0 added, "
            f"0 edited; none of the removed designators is on the CPL — "
            f"ASSERTED by bom-only mode")
    return fails, notes


def check_legible_bom_delta(release_dir, prior_dir):
    """LEGIBLE-BOM mode's EXTRA assertion: the one permitted fab/ change is
    `fab/bom.csv` gaining LEGIBILITY — and NOTHING else about it moving.

    WHY THIS MODE EXISTS, AND WHY THE THREE THAT PRECEDE IT DO NOT COVER IT.
    Canon F-LEGIBLE (ADR-0006) says a fab artifact is graded as its RECIPIENT
    parses it. Fixing a BOM to satisfy it EDITS every row — an MPN appears in a
    column that was blank, a Comment stops being an LCSC code or a `simple_*`
    placeholder — while the board, the gerbers, the drills, the CPL, the STEP
    and the PDFs are byte-identical. `--docs-only-supersede` correctly refuses
    (fab/ changed). `--bom-only-supersede` correctly refuses too, and for a
    reason worth keeping: it FAILs on any EDITED row, because for the defect IT
    guards (canon A-POP, an unplaced part must leave the BOM) an edited row
    would mean a different board.

    WHAT THIS ASSERTS THAT "the file differs" CANNOT. The row IDENTITY is
    frozen: same set of designator-groups, and for each group the SAME
    Footprint and the SAME LCSC code. Only `Comment` and `MPN` may move. So a
    legibility pass cannot smuggle in a substituted part number (the C82317 ->
    C131025 class this repo has already been bitten by), a re-grouped
    designator, a dropped part, or a footprint change — and it cannot smuggle
    OUT a row either. The MPN may only move from BLANK to a value, or between
    two spellings of the same part; it may not be blanked.

    AND THE POINT OF THE RELEASE IS ASSERTED, NOT ASSUMED: the new BOM must
    PASS `bom_legibility_check`, and the prior one must FAIL it. A "legible
    BOM" supersede whose BOM is still illegible supersedes nothing, and one
    whose predecessor was ALREADY legible had no defect to fix.
    """
    import csv as _csv
    fails, notes = [], []
    cur_p = release_dir / "fab" / "bom.csv"
    old_p = prior_dir / "fab" / "bom.csv"
    if not (cur_p.is_file() and old_p.is_file()):
        fails.append("  LEGIBLE-BOM: fab/bom.csv missing on one side — cannot "
                     "establish the delta")
        return fails, notes

    def rows(p):
        out = {}
        for r in _csv.DictReader(
                p.read_text(encoding="utf-8-sig").splitlines()):
            refs = tuple(sorted(d.strip() for d in
                                (r.get("Designator") or "").split(",")
                                if d.strip()))
            if refs:
                out[refs] = {k: (v or "").strip() for k, v in r.items()}
        return out

    cur, old = rows(cur_p), rows(old_p)
    for k in sorted(set(cur) - set(old)):
        fails.append(
            f"  LEGIBLE-BOM DEVIATION: row {list(k)} was ADDED — a legibility "
            f"pass may rewrite the Comment and MPN of an existing row and "
            f"nothing else; adding one is a population or sourcing change")
    for k in sorted(set(old) - set(cur)):
        fails.append(
            f"  LEGIBLE-BOM DEVIATION: row {list(k)} was REMOVED — that is an "
            f"A-POP fix, not a legibility fix; use --bom-only-supersede so the "
            f"removal is graded against the CPL")
    reworded, mpn_filled, untouched = 0, 0, 0
    for k in sorted(set(cur) & set(old)):
        c, o = cur[k], old[k]
        for col in ("Footprint", "LCSC"):
            if c.get(col) != o.get(col):
                fails.append(
                    f"  LEGIBLE-BOM DEVIATION: {','.join(k)} {col} changed "
                    f"{o.get(col)!r} -> {c.get(col)!r} — a legibility pass "
                    f"rewrites how the row READS, never WHICH PART it is. A "
                    f"changed LCSC is a substitution (the C82317 -> C131025 "
                    f"class); a changed Footprint is a different board")
        if o.get("MPN") and not c.get("MPN"):
            fails.append(
                f"  LEGIBLE-BOM DEVIATION: {','.join(k)} MPN was BLANKED "
                f"({o.get('MPN')!r} -> ''), which is the defect this mode "
                f"exists to fix, running backwards")
        if c.get("MPN") != o.get("MPN"):
            mpn_filled += 1
        if c.get("Comment") != o.get("Comment"):
            reworded += 1
        if c == o:
            untouched += 1
    if not reworded and not mpn_filled:
        fails.append(
            "  LEGIBLE-BOM: fab/bom.csv carries the same Comment and MPN on "
            "every row as the prior release's — a legibility supersede that "
            "makes nothing more legible supersedes nothing; use "
            "--docs-only-supersede")

    # the verdict this mode exists for, taken from the F-LEGIBLE gate itself
    # rather than re-implemented here (ONE grader, canon M1: this file does not
    # get to have its own opinion about what "legible" means)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from bom_legibility_check import check as _legibility
        from bom_legibility_check import discover as _discover
    except ImportError as e:                                  # pragma: no cover
        fails.append(f"  LEGIBLE-BOM: cannot import bom_legibility_check ({e})"
                     f" — this mode's whole verdict comes from it")
        return fails, notes
    for label, d in (("this release", release_dir), ("the prior release",
                                                     prior_dir)):
        bom, parts, _what = _discover(d)
        r = _legibility(bom, parts) if bom else {"fails": ["no BOM"]}
        n = len(r["fails"])
        if label == "this release" and n:
            fails.append(
                f"  LEGIBLE-BOM: this release's fab/bom.csv still FAILS "
                f"F-LEGIBLE with {n} finding(s) — run "
                f"`bom_legibility_check.py {d.name}`. A legibility supersede "
                f"must SHIP a legible BOM")
        if label == "the prior release" and not n:
            fails.append(
                f"  LEGIBLE-BOM: {prior_dir.name}'s fab/bom.csv ALREADY passes "
                f"F-LEGIBLE — there was no legibility defect to supersede")
        notes.append(f"  note: F-LEGIBLE on {label} ({d.name}): "
                     f"{n} finding(s)")
    if not fails:
        notes.append(
            f"  note: fab/bom.csv delta is {reworded} Comment rewrite(s) and "
            f"{mpn_filled} MPN change(s) over {len(cur)} row(s); "
            f"{untouched} row(s) byte-identical; 0 added, 0 removed, 0 "
            f"Footprint/LCSC changes — ASSERTED by legible-bom mode")
    return fails, notes


# ------------------------------------------------ sourcing supersede (M8)
# Lines a PLOT writes about ITSELF: the moment of plotting, never the board.
# Stripping exactly these — and nothing else — is what lets a RE-PLOT prove the
# board still generates the shipped payload, which a copy-check cannot. The list
# is the one measured in usb-hub-3s-v3 v1.11's verification/replot_identity.txt,
# including the Excellon header line that a first pass missed (it read 11/15
# until the drill date was covered; the strip list is part of the method).
_PLOT_TS_RE = re.compile(
    rb"^(?:%TF\.CreationDate,[^\n]*"
    rb"|G04 Created by[^\n]*"
    rb"|;\s*DRILL file[^\n]*"
    rb"|;\s*#@!\s*TF\.CreationDate,[^\n]*)$", re.M)

#: fab/ members compared TIMESTAMP-STRIPPED rather than byte-for-byte.
_REPLOTTABLE = (".zip", ".drl", ".gbr", ".gbrjob")


def _strip_plot_timestamps(data: bytes) -> bytes:
    return _PLOT_TS_RE.sub(b"", data)


def _payload_identical(cur: Path, old: Path):
    """(bool, detail) — are these two fab payload files the same PLOT, ignoring
    only the timestamps the plotter stamps into its own output? A zip is opened
    and compared MEMBER BY MEMBER: two archives of identical members can differ
    in bytes (member order, mtimes, compression), and that difference says
    nothing about the copper."""
    import zipfile
    if cur.read_bytes() == old.read_bytes():
        # the carried-forward case: nothing to explain, and no need to parse a
        # payload this gate is not the validator of (F-PAYLOAD opens the zip).
        return True, "byte-identical"
    if cur.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(cur) as zc, zipfile.ZipFile(old) as zo:
                nc = sorted(i.filename for i in zc.infolist() if not
                            i.is_dir())
                no = sorted(i.filename for i in zo.infolist() if not
                            i.is_dir())
                if nc != no:
                    return False, (f"zip member list differs: "
                                   f"+{sorted(set(nc) - set(no))} "
                                   f"-{sorted(set(no) - set(nc))}")
                diff = [n for n in nc
                        if _strip_plot_timestamps(zc.read(n))
                        != _strip_plot_timestamps(zo.read(n))]
                if diff:
                    return False, (f"{len(diff)} of {len(nc)} zip member(s) "
                                   f"differ after the timestamp strip: "
                                   f"{', '.join(diff[:6])}")
                return True, f"{len(nc)}/{len(nc)} zip members"
        except zipfile.BadZipFile as e:
            return False, f"unreadable zip ({e})"
    same = (_strip_plot_timestamps(cur.read_bytes())
            == _strip_plot_timestamps(old.read_bytes()))
    return same, "timestamp-stripped" if same else "differs beyond timestamps"


def check_sourcing_delta(release_dir, prior_dir):
    """SOURCING mode's EXTRA assertion: the one permitted fab/ change is
    `fab/bom.csv` moving `MPN` + `LCSC` on the SUBSTITUTED rows, and nothing
    else about the payload moving at all.

    WHY THIS MODE EXISTS (canon M8, the two-strike promotion). JLC refusing to
    SUPPLY a line is not a design defect and not a paperwork defect: v1.10 of
    usb-hub-3s-v3 was uploaded and line 8 came back "10 shortfall" (C25744, the
    only basic-library 10k 0402, stockCount 0). The fix substitutes an
    electrically identical part at SOURCE and changes NO copper. None of the
    four earlier modes covers it — docs-only requires fab/ byte-identical,
    cpl-only permits only coordinates, bom-only only ROW REMOVAL, and
    legible-bom explicitly FAILs a changed LCSC because when it was written a
    changed LCSC could only be the C82317 -> C131025 accident. So v1.11 shipped
    gated by SEVEN hand-written file waivers, each carrying its own measurement
    — weaker evidence than the release it superseded, because a waiver is a
    human's claim and this is all machine-checkable. crow-recorder-central-v2
    v1.7 is the second board needing it, which under M8 makes promotion
    MANDATORY rather than optional.

    WHAT IS ASSERTED, none of it waivable:

      * the `.kicad_pcb` is BYTE-IDENTICAL, and the md5 is PRINTED (on a board
        whose v1.6-v1.8 shipped 44287.91 mm2 of MISSING COPPER with every gate
        green, "the copper did not move" is the claim that most needs a number);
      * `fab/cpl.csv` is BYTE-IDENTICAL — a substitution to a different package
        would move the placement datum, so an unchanged CPL is what makes
        "drop-in" mean something;
      * every gerber and drill is identical after stripping ONLY the plot's own
        timestamps — which ACCEPTS a re-plot from this release's own board, the
        stronger evidence, instead of demanding a byte-copy;
      * `fab/bom.csv` keeps its ROW COUNT and its designator groups IN THE SAME
        ORDER, and on every row the ONLY cells permitted to move are `MPN` and
        `LCSC`, together, on the substituted rows. A `Comment` or `Footprint`
        change is a different board. An `MPN` moving where the `LCSC` did not is
        a LEGIBILITY edit and belongs in `--legible-bom-supersede`;
      * no row is left with a BLANK `MPN` or a blank/malformed `LCSC`, and the
        new BOM PASSES `bom_legibility_check` (ONE grader, canon M1 — this file
        does not get its own opinion about what "legible" means);
      * the SOURCE moved too (canon M3): a `fab/bom.csv` that changed without
        its `.tsx` changing is a HAND-EDITED BOM — the defect crow-mic-pod-v2
        paid for on 2026-07-27;
      * and BOTH codes of every substitution — the one leaving and the one
        arriving — are NAMED in the release's own MANIFEST or order README, so
        the diff is auditable by someone who was not here.
    """
    import csv as _csv
    fails, notes = [], []

    # -- (1) the copper did not move, stated as a NUMBER
    cur_b = sorted((release_dir / "source").glob("*.kicad_pcb"))
    old_b = sorted((prior_dir / "source").glob("*.kicad_pcb"))
    if len(cur_b) != 1 or len(old_b) != 1:
        fails.append(
            f"  SOURCING: expected exactly one source/*.kicad_pcb on each side, "
            f"found {len(cur_b)} here and {len(old_b)} in {prior_dir.name} — "
            f"the copper-identity claim cannot be made")
    elif cur_b[0].name != old_b[0].name:
        fails.append(
            f"  SOURCING DEVIATION: the board file is named {cur_b[0].name!r} "
            f"here and {old_b[0].name!r} in {prior_dir.name} — a sourcing "
            f"supersede substitutes a PART, never a board")
    else:
        h_cur = hashlib.md5(cur_b[0].read_bytes()).hexdigest()
        h_old = hashlib.md5(old_b[0].read_bytes()).hexdigest()
        if h_cur != h_old:
            fails.append(
                f"  SOURCING DEVIATION: source/{cur_b[0].name} md5 {h_cur} != "
                f"{prior_dir.name}'s {h_old} — a sourcing supersede changes "
                f"WHICH PART IS BOUGHT, never the copper. If the board really "
                f"moved, cut a full release")
        else:
            notes.append(f"  note: source/{cur_b[0].name} md5 {h_cur} — "
                         f"IDENTICAL to {prior_dir.name}'s (ASSERTED)")

    # -- (2) the placement datum did not move
    cur_cpl, old_cpl = release_dir / "fab" / "cpl.csv", prior_dir / "fab" / "cpl.csv"
    if cur_cpl.is_file() and old_cpl.is_file():
        if _sha256(cur_cpl) != _sha256(old_cpl):
            fails.append(
                "  SOURCING DEVIATION: fab/cpl.csv differs from "
                f"{prior_dir.name}'s — a part substitution changes NO "
                "placement. A moved CPL means the replacement is not a "
                "drop-in (different land pattern), or something else was "
                "changed under cover of the swap")
        else:
            n = max(len(cur_cpl.read_text(encoding="utf-8-sig").splitlines()) - 1, 0)
            notes.append(f"  note: fab/cpl.csv byte-identical to "
                         f"{prior_dir.name}'s ({n} rows) — ASSERTED")

    # -- (3) the plot still describes the same copper (re-plot friendly)
    cur_fab = _tree_files(release_dir / "fab")
    old_fab = _tree_files(prior_dir / "fab")
    checked = 0
    for rel in sorted(set(cur_fab) & set(old_fab)):
        if not rel.lower().endswith(_REPLOTTABLE):
            continue
        ok, detail = _payload_identical(cur_fab[rel], old_fab[rel])
        checked += 1
        if not ok:
            fails.append(
                f"  SOURCING DEVIATION: fab/{rel} is not the same plot as "
                f"{prior_dir.name}/fab/{rel} ({detail}) — the timestamp strip "
                f"deliberately tolerates a RE-PLOT and nothing else, so a "
                f"difference here is COPPER, not paperwork")
    if checked:
        notes.append(f"  note: {checked} gerber/drill payload file(s) identical "
                     f"to {prior_dir.name}'s after stripping only the plot's "
                     f"own timestamps — ASSERTED (a re-plot is accepted; a "
                     f"changed plot is not)")

    # -- (4) the SOURCE moved too (canon M3) — otherwise the BOM was hand-edited
    cur_tsx = sorted((release_dir / "source").glob("*.tsx"))
    old_tsx = {p.name: p for p in (prior_dir / "source").glob("*.tsx")}
    if not cur_tsx:
        fails.append(
            "  SOURCING DEVIATION: this release ships no source/*.tsx, so the "
            "BOM row cannot be shown to have moved because the SOURCE moved "
            "(canon M3). A fab/bom.csv that changes on its own is a "
            "HAND-EDITED BOM")
    else:
        moved = [p.name for p in cur_tsx
                 if p.name in old_tsx and _sha256(p) != _sha256(old_tsx[p.name])]
        if not moved:
            fails.append(
                f"  SOURCING DEVIATION: fab/bom.csv changed but every "
                f"source/*.tsx is byte-identical to {prior_dir.name}'s — that "
                f"is a HAND-EDITED BOM (canon M3: everything must be "
                f"regenerable from source). Change the "
                f"`supplierPartNumbers` in the .tsx and re-export")
        else:
            notes.append(f"  note: source/{', '.join(moved)} CHANGED — the BOM "
                         f"row moved because the source moved (canon M3)")

    # -- (5) the BOM delta itself
    cur_p, old_p = release_dir / "fab" / "bom.csv", prior_dir / "fab" / "bom.csv"
    if not (cur_p.is_file() and old_p.is_file()):
        fails.append("  SOURCING: fab/bom.csv missing on one side — cannot "
                     "establish the delta")
        return fails, notes

    def rows(p):
        out = []
        for r in _csv.DictReader(
                p.read_text(encoding="utf-8-sig").splitlines()):
            refs = tuple(d.strip() for d in
                         (r.get("Designator") or "").split(",") if d.strip())
            if refs:
                out.append((refs, {k: (v or "").strip() for k, v in r.items()}))
        return out

    cur, old = rows(cur_p), rows(old_p)
    if len(cur) != len(old):
        fails.append(
            f"  SOURCING DEVIATION: fab/bom.csv has {len(cur)} data row(s), "
            f"{prior_dir.name}'s has {len(old)} — a substitution changes WHICH "
            f"PART a row buys, never how many rows there are (a removal is "
            f"--bom-only-supersede)")
        return fails, notes
    order_cur = [r for r, _ in cur]
    order_old = [r for r, _ in old]
    if order_cur != order_old:
        bad = next((i for i in range(len(cur)) if order_cur[i] != order_old[i]),
                   0)
        fails.append(
            f"  SOURCING DEVIATION: fab/bom.csv designator groups differ in "
            f"CONTENT OR ORDER — row {bad + 1} is {list(order_cur[bad])} here "
            f"and {list(order_old[bad])} in {prior_dir.name}. A re-grouped BOM "
            f"is a different assembly, and a reordered one cannot be diffed "
            f"cell-by-cell at all")
        return fails, notes

    subs, untouched = [], 0
    for (refs, c), (_r, o) in zip(cur, old):
        ref = ",".join(refs)
        changed = sorted(k for k in set(c) | set(o) if c.get(k) != o.get(k))
        for col in changed:
            if col in ("MPN", "LCSC"):
                continue
            fails.append(
                f"  SOURCING DEVIATION: {ref} {col} changed {o.get(col)!r} -> "
                f"{c.get(col)!r} — a sourcing supersede moves MPN and LCSC and "
                f"NOTHING else. A changed Footprint is a different board; a "
                f"changed Comment is a legibility edit "
                f"(--legible-bom-supersede)")
        if "LCSC" in changed:
            new, was = c.get("LCSC", ""), o.get("LCSC", "")
            if not re.fullmatch(r"C\d+", new or ""):
                fails.append(
                    f"  SOURCING DEVIATION: {ref} LCSC became {new!r} — a "
                    f"substituted row must carry a real LCSC code; a coded row "
                    f"losing its code is an A-POP change, not a sourcing one")
            if not c.get("MPN"):
                fails.append(
                    f"  SOURCING DEVIATION: {ref} was substituted "
                    f"{was} -> {new} but its MPN is BLANK — the substituted "
                    f"row is exactly the row a human must be able to check "
                    f"against the vendor (canon F-MPN)")
            subs.append((ref, was, new, o.get("MPN", ""), c.get("MPN", "")))
        elif "MPN" in changed:
            fails.append(
                f"  SOURCING DEVIATION: {ref} MPN changed {o.get('MPN')!r} -> "
                f"{c.get('MPN')!r} while its LCSC did not — that is a "
                f"LEGIBILITY edit (how the row READS), not a substitution "
                f"(WHICH PART it is). Use --legible-bom-supersede")
        if not changed:
            untouched += 1
    if not subs:
        fails.append(
            "  SOURCING: not one fab/bom.csv row changed its LCSC — a sourcing "
            "supersede that substitutes no part supersedes nothing; use "
            "--docs-only-supersede (or --legible-bom-supersede if the BOM only "
            "became more readable)")

    # -- (6) the verdict this mode leans on comes from the F-LEGIBLE gate
    #        itself, never re-implemented here (ONE grader, canon M1)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from bom_legibility_check import check as _legibility
        from bom_legibility_check import discover as _discover
    except ImportError as e:                                  # pragma: no cover
        fails.append(f"  SOURCING: cannot import bom_legibility_check ({e}) — "
                     f"the substituted row's readability is ungraded, and "
                     f"unevaluable input is a FAIL")
        return fails, notes
    bom, parts, _what = _discover(release_dir)
    r = _legibility(bom, parts) if bom else {"fails": ["no BOM"]}
    n = len(r["fails"])
    notes.append(f"  note: F-LEGIBLE on this release ({release_dir.name}): "
                 f"{n} finding(s)")
    if n:
        fails.append(
            f"  SOURCING: this release's fab/bom.csv FAILS F-LEGIBLE with {n} "
            f"finding(s) — run `bom_legibility_check.py {release_dir.name}`. "
            f"The substituted code must resolve an MPN like every other row; "
            f"a new part that nobody can look up is not sourced")

    # -- (7) the substitution is RECORDED where a later reader will find it
    docs = []
    for p in (release_dir / "MANIFEST.txt", _find_readme(release_dir)):
        if p is not None and p.is_file():
            docs.append(p.read_text(errors="ignore"))
    doctext = "\n".join(docs)
    for ref, was, new, o_mpn, c_mpn in subs:
        missing = [code for code in (was, new) if code and code not in doctext]
        if missing:
            fails.append(
                f"  SOURCING DEVIATION: {ref} was substituted {was} -> {new} "
                f"but {', '.join(missing)} appears in neither MANIFEST.txt nor "
                f"the order README — BOTH codes must be recorded, or the "
                f"reason this release exists is legible only as a CSV diff "
                f"against a release nobody will still have")
    if subs:
        notes.append(
            "  note: " + str(len(subs)) + " substitution(s), each recorded in "
            "MANIFEST/README: " + "; ".join(
                f"{ref} {was}({o_mpn or '-'}) -> {new}({c_mpn or '-'})"
                for ref, was, new, o_mpn, c_mpn in subs))
    if not fails:
        notes.append(
            f"  note: fab/bom.csv delta is {len(subs)} substituted row(s) over "
            f"{len(cur)} row(s); {untouched} row(s) cell-identical; 0 added, 0 "
            f"removed, 0 reordered, 0 Comment/Footprint changes — ASSERTED by "
            f"sourcing mode")
    return fails, notes


# ------------------------------------------------- value-change supersede
#: source/ members a VALUE change legitimately moves. The value lives in the
#: BOARD (`(property "Value" ...)`) and in the SCHEMATIC symbol, and both reach
#: the netlist — measured on crow-mic-pod-v2 v1.3, 2026-07-28. Everything else
#: under source/ must still be byte-identical.
_AUTHORING_EXT = (".kicad_pcb", ".kicad_sch", ".tsx", ".net")


def _csv_rows_in_order(path, key="Designator"):
    """[(ref, {col: cell})] in FILE ORDER, one entry per designator. A row
    whose Designator cell groups several refs (the BOM's `"R4,R5"`) yields one
    entry per ref, all sharing the row's other cells — which is what makes a
    BOM and a CPL comparable at the DESIGNATOR level even when the exporter
    splits or merges rows around them."""
    import csv as _csv
    out = []
    for r in _csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()):
        cells = {k: (v or "").strip() for k, v in r.items() if k is not None}
        for ref in (d.strip() for d in (cells.get(key) or "").split(",")):
            if ref:
                out.append((ref, cells))
    return out


def check_value_change_delta(release_dir, prior_dir, declared):
    """VALUE-CHANGE mode's EXTRA assertion: a part's VALUE moved on parts that
    are already placed, so the ASSEMBLY DATA moves and the COPPER does not.

    WHY THIS MODE EXISTS, AND WHY NO EARLIER MODE COVERS IT. Measured on
    crow-mic-pod-v2 v1.3, 2026-07-28 (`08_reviews/`, the CAL-1 re-derivation):
    `export_jlc_package.py` reads `val = fp.GetValue()` **from the board** and
    feeds that ONE string to BOTH the BOM `Comment` column and the CPL `Val`
    column. So changing a divider from 22k to 33k on two already-placed 0603
    resistors moves the `.kicad_pcb`, the `.kicad_sch`, the `.net`, 2 CPL `Val`
    cells and the BOM rows for those refs — while **all 11 gerbers and drills
    are byte-identical** (verified 11/11, the method validated by re-plotting
    the sealed v1.3 zip from its own archived board). `--docs-only-supersede`
    refuses (fab/ changed). `--bom-only-supersede` refuses (it permits only row
    REMOVAL, and these refs ARE on the CPL). `--legible-bom-supersede` refuses
    (a changed LCSC is a substitution to it). `--sourcing-supersede` refuses
    (it demands an md5-identical board and a byte-identical CPL — a value
    change moves both). `--cpl-only-supersede` names a `Val` change as its own
    explicit exclusion. Without this mode the only way to seal a
    copper-identical value fix is to hand-edit a CSV, which canon M3 forbids.

    WHAT IS ASSERTED, none of it waivable:

      * **the COPPER did not move**, stated the strong way: every gerber and
        drill is identical after stripping ONLY the plot's own timestamps
        (`_PLOT_TS_RE`, incl. the Excellon `; DRILL file ... date` header that
        a first pass on usb-hub-3s-v3 v1.11 missed — it read 11/15 until the
        drill date was covered). That ACCEPTS a re-plot from this release's own
        board, which is stronger evidence than a byte-copy. A release with no
        gerber/drill to compare cannot make the claim at all and FAILs;
      * **the SOURCE moved** (canon M3, in the direction this mode needs it).
        A value is carried BY the board and BY the schematic, so an unchanged
        `source/*.kicad_pcb` or `*.kicad_sch` means the CSVs were HAND-EDITED.
        Both md5s are PRINTED. Editing the board alone is not a way out: the
        measurement recorded `kicad-cli pcb drc --schematic-parity` returning
        2 `footprint_symbol_mismatch` violations for exactly that shortcut;
      * **the CPL delta is `Val` cells and NOTHING else** — identical row
        count, identical designator sequence, and for every ref every
        coordinate, rotation, layer and package cell unchanged. A moved
        coordinate is `--cpl-only-supersede`'s defect (A-POS) and a moved
        rotation is A-ROT's; neither may ride along here;
      * **every moved cell belongs to a DECLARED designator.** The caller
        names the refs (`--designators R4,R5`) and a change touching any other
        ref FAILs. The list must also not be WIDER than the delta: a declared
        ref that moved nothing is padding, and a strip list too wide is as
        wrong as one too narrow;
      * **the BOM ref set is FROZEN** — rows may split or merge around the new
        values (the exporter groups by `(code, val, footprint)`), but no
        designator may be added or dropped. That is A-POP's business and
        `--bom-only-supersede`'s mode;
      * **a declared ref's `Footprint` may not move** (a different land
        pattern is a different board), and its `LCSC` MUST move. A different
        value is a different part: a row whose `Comment` claims 33 kΩ against
        the 22 kΩ part's code is the R12/R30 wrong-part class verbatim, and it
        is exactly what a board-only edit produces;
      * **the two artifacts AGREE** — each declared ref's new CPL `Val` appears
        as a token in its own BOM `Comment` (the exporter writes one merged
        `a / b` Comment when two values share a code+footprint, so containment
        is the honest form of "same string"). They come from one `GetValue()`
        call; a disagreement means one of the two CSVs was written by hand;
      * the new BOM **PASSES `bom_legibility_check`** (taken from the F-LEGIBLE
        gate itself, never re-implemented — ONE grader, canon M1);
      * and **both the OLD and the NEW value of every declared designator are
        NAMED in MANIFEST.txt or the order README**, so the reason this
        release exists is legible to someone who was not here.
    """
    fails, notes = [], []
    declared = sorted({d for d in declared if d})
    if not declared:
        fails.append(
            "  VALUE-CHANGE: no --designators given — this mode confines the "
            "delta to a DECLARED refdes list, so an empty list confines "
            "nothing and would accept any BOM/CPL edit at all")
        return fails, notes
    notes.append(f"  note: declared value-change designator(s): "
                 f"{', '.join(declared)}")

    # -- (1) the COPPER did not move (re-plot friendly, byte-copy accepted)
    cur_fab = _tree_files(release_dir / "fab")
    old_fab = _tree_files(prior_dir / "fab")
    checked = 0
    for rel in sorted(set(cur_fab) & set(old_fab)):
        if not rel.lower().endswith(_REPLOTTABLE):
            continue
        ok, detail = _payload_identical(cur_fab[rel], old_fab[rel])
        checked += 1
        if not ok:
            fails.append(
                f"  VALUE-CHANGE DEVIATION: fab/{rel} is not the same plot as "
                f"{prior_dir.name}/fab/{rel} ({detail}) — a VALUE change moves "
                f"no copper, no silk and no drill. The timestamp strip "
                f"deliberately tolerates a RE-PLOT and nothing else, so a "
                f"difference here is COPPER, and this is a full respin")
    if checked:
        notes.append(
            f"  note: {checked} gerber/drill payload file(s) identical to "
            f"{prior_dir.name}'s after stripping only the plot's own "
            f"timestamps — ASSERTED (a re-plot is accepted; changed copper is "
            f"not)")
    else:
        fails.append(
            f"  VALUE-CHANGE: no gerber/drill payload file is present in BOTH "
            f"this release and {prior_dir.name} ({'/'.join(_REPLOTTABLE)}) — "
            f"the copper-identity claim this mode rests on cannot be made, and "
            f"an unevaluable claim is a FAIL, not a skip")

    # -- (2) the SOURCE moved (canon M3, in the direction this mode needs)
    for ext, required in ((".kicad_pcb", True), (".kicad_sch", True),
                          (".tsx", None), (".net", False)):
        cur_s = sorted(p for p in (release_dir / "source").glob("*" + ext))
        old_s = {p.name: p for p in (prior_dir / "source").glob("*" + ext)}
        if not cur_s or not old_s:
            if required:
                fails.append(
                    f"  VALUE-CHANGE: source/*{ext} is missing on one side "
                    f"(here {len(cur_s)}, {prior_dir.name} {len(old_s)}) — a "
                    f"value is carried BY that file, so without it on both "
                    f"sides the change cannot be shown to come from SOURCE")
            continue
        moved = [p.name for p in cur_s if p.name in old_s
                 and hashlib.md5(p.read_bytes()).hexdigest()
                 != hashlib.md5(old_s[p.name].read_bytes()).hexdigest()]
        if ext in (".kicad_pcb", ".kicad_sch"):
            for p in cur_s:
                if p.name in old_s:
                    notes.append(
                        f"  note: source/{p.name} md5 "
                        f"{hashlib.md5(p.read_bytes()).hexdigest()} vs "
                        f"{prior_dir.name}'s "
                        f"{hashlib.md5(old_s[p.name].read_bytes()).hexdigest()}")
        if required is False:
            continue
        if not moved:
            fails.append(
                f"  VALUE-CHANGE DEVIATION: every source/*{ext} is IDENTICAL "
                f"to {prior_dir.name}'s, but fab/ carries a new value — that "
                f"is a HAND-EDITED CSV (canon M3: everything must be "
                f"regenerable from source). The value lives in that file; "
                f"change it there and re-export"
                + (" (editing the board alone leaves the schematic disagreeing "
                   "— `kicad-cli pcb drc --schematic-parity` reports "
                   "footprint_symbol_mismatch, measured 2026-07-28)"
                   if ext == ".kicad_sch" else ""))
        else:
            notes.append(f"  note: source/{', '.join(moved)} CHANGED — the "
                         f"value moved because the SOURCE moved (canon M3)")

    # -- (3) the CPL delta is `Val` cells and nothing else
    cur_p = release_dir / "fab" / "cpl.csv"
    old_p = prior_dir / "fab" / "cpl.csv"
    if not (cur_p.is_file() and old_p.is_file()):
        fails.append("  VALUE-CHANGE: fab/cpl.csv missing on one side — cannot "
                     "establish the delta")
        return fails, notes
    cur_cpl = _csv_rows_in_order(cur_p)
    old_cpl = _csv_rows_in_order(old_p)
    cpl_moved, cpl_new_val = [], {}
    if [r for r, _ in cur_cpl] != [r for r, _ in old_cpl]:
        cur_set, old_set = {r for r, _ in cur_cpl}, {r for r, _ in old_cpl}
        fails.append(
            f"  VALUE-CHANGE DEVIATION: fab/cpl.csv designator sequence "
            f"differs from {prior_dir.name}'s ({len(cur_cpl)} vs "
            f"{len(old_cpl)} row(s); +{sorted(cur_set - old_set)} "
            f"-{sorted(old_set - cur_set)}) — a value change places exactly "
            f"the same parts in exactly the same order. A row added or removed "
            f"is a POPULATION change")
    else:
        for (ref, c), (_r, o) in zip(cur_cpl, old_cpl):
            for col in sorted(set(c) | set(o)):
                if col in ("Designator", "Val") or c.get(col) == o.get(col):
                    continue
                fails.append(
                    f"  VALUE-CHANGE DEVIATION: {ref} CPL {col} changed "
                    f"{o.get(col)!r} -> {c.get(col)!r} — a value change moves "
                    f"the `Val` cell and NOTHING else. A moved coordinate is "
                    f"--cpl-only-supersede's defect (canon A-POS) and a moved "
                    f"Rotation needs its own A-ROT evidence; neither rides "
                    f"along inside a value fix")
            if c.get("Val") != o.get("Val"):
                cpl_moved.append(f"{ref} {o.get('Val')!r} -> {c.get('Val')!r}")
                cpl_new_val[ref] = c.get("Val", "")
                if ref not in declared:
                    fails.append(
                        f"  VALUE-CHANGE DEVIATION: {ref} CPL Val changed "
                        f"{o.get('Val')!r} -> {c.get('Val')!r} but {ref} is "
                        f"NOT on the declared --designators list "
                        f"({', '.join(declared)}) — every moved cell must be "
                        f"one the caller declared, or the release is changing "
                        f"parts nobody reviewed")

    # -- (4) the BOM delta is confined to the declared designators
    cur_b = release_dir / "fab" / "bom.csv"
    old_b = prior_dir / "fab" / "bom.csv"
    if not (cur_b.is_file() and old_b.is_file()):
        fails.append("  VALUE-CHANGE: fab/bom.csv missing on one side — cannot "
                     "establish the delta")
        return fails, notes
    cur_bom = dict(_csv_rows_in_order(cur_b))
    old_bom = dict(_csv_rows_in_order(old_b))
    for ref in sorted(set(cur_bom) - set(old_bom)):
        fails.append(
            f"  VALUE-CHANGE DEVIATION: {ref} was ADDED to fab/bom.csv — a "
            f"value change re-labels parts that are already there; adding one "
            f"is a population or sourcing change")
    for ref in sorted(set(old_bom) - set(cur_bom)):
        fails.append(
            f"  VALUE-CHANGE DEVIATION: {ref} was REMOVED from fab/bom.csv — "
            f"that is an A-POP fix; use --bom-only-supersede so the removal is "
            f"graded against the CPL")
    bom_moved, undeclared_hits = [], []
    for ref in sorted(set(cur_bom) & set(old_bom)):
        c, o = cur_bom[ref], old_bom[ref]
        changed = sorted(col for col in set(c) | set(o)
                         if col != "Designator" and c.get(col) != o.get(col))
        if not changed:
            continue
        bom_moved.append(ref)
        if ref not in declared:
            undeclared_hits.append((ref, changed))
            fails.append(
                f"  VALUE-CHANGE DEVIATION: {ref}'s BOM row changed "
                f"{changed} but {ref} is NOT on the declared --designators "
                f"list ({', '.join(declared)}) — a value-change supersede is "
                f"confined to the refs the caller named, precisely so a "
                f"second, unreviewed edit cannot ride along inside it")
            continue
        for col in changed:
            if col in ("Comment", "MPN", "LCSC"):
                continue
            fails.append(
                f"  VALUE-CHANGE DEVIATION: {ref} BOM {col} changed "
                f"{o.get(col)!r} -> {c.get(col)!r} — even on a declared "
                f"designator only Comment, MPN and LCSC may move. A changed "
                f"Footprint is a different land pattern, i.e. a different "
                f"board")
        if c.get("Comment") != o.get("Comment") and c.get("LCSC") == o.get("LCSC"):
            fails.append(
                f"  VALUE-CHANGE DEVIATION: {ref} Comment moved "
                f"{o.get('Comment')!r} -> {c.get('Comment')!r} while its LCSC "
                f"stayed {c.get('LCSC')!r} — a different VALUE is a different "
                f"PART. A row whose Comment claims the new value against the "
                f"OLD part's code is the R12/R30 wrong-part class verbatim, "
                f"and it is exactly what editing the board without the source "
                f"produces. (If only the wording changed, that is "
                f"--legible-bom-supersede.)")

    # -- (5) the declared list is not WIDER than the delta
    for ref in declared:
        if ref not in cur_bom and ref not in cpl_new_val:
            fails.append(
                f"  VALUE-CHANGE: {ref} is declared on --designators but "
                f"appears in neither fab/bom.csv nor the CPL delta — the list "
                f"must name the refs that actually moved")
        elif ref not in bom_moved and ref not in cpl_new_val:
            fails.append(
                f"  VALUE-CHANGE: {ref} is declared on --designators but "
                f"NOTHING about it changed — a declared list wider than the "
                f"real delta launders unrelated edits exactly as a list too "
                f"narrow hides them")
    if not cpl_moved:
        fails.append(
            "  VALUE-CHANGE: not one fab/cpl.csv `Val` cell moved — a "
            "value-change supersede that changes no value supersedes nothing. "
            "If only the BOM's wording moved, that is "
            "--legible-bom-supersede; if only its LCSC moved, "
            "--sourcing-supersede")

    # -- (6) the two artifacts AGREE (they come from ONE GetValue() call)
    for ref, val in sorted(cpl_new_val.items()):
        row = cur_bom.get(ref)
        if row is None:
            continue
        comment = row.get("Comment", "")
        tokens = [t.strip() for t in comment.split("/")] or [comment]
        if val and val not in tokens and val != comment:
            fails.append(
                f"  VALUE-CHANGE DEVIATION: {ref} CPL Val is {val!r} but its "
                f"BOM Comment is {comment!r} — the exporter feeds ONE "
                f"`fp.GetValue()` string to both columns, so a disagreement "
                f"means one of the two CSVs was written BY HAND (canon M3)")

    # -- (7) the verdict this mode leans on comes from the F-LEGIBLE gate
    #        itself, never re-implemented here (ONE grader, canon M1)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from bom_legibility_check import check as _legibility
        from bom_legibility_check import discover as _discover
    except ImportError as e:                                  # pragma: no cover
        fails.append(f"  VALUE-CHANGE: cannot import bom_legibility_check "
                     f"({e}) — the re-valued row's readability is ungraded, "
                     f"and unevaluable input is a FAIL")
        return fails, notes
    bom, parts, _what = _discover(release_dir)
    r = _legibility(bom, parts) if bom else {"fails": ["no BOM"]}
    n = len(r["fails"])
    notes.append(f"  note: F-LEGIBLE on this release ({release_dir.name}): "
                 f"{n} finding(s)")
    if n:
        fails.append(
            f"  VALUE-CHANGE: this release's fab/bom.csv FAILS F-LEGIBLE with "
            f"{n} finding(s) — run `bom_legibility_check.py "
            f"{release_dir.name}`. The re-valued row must still resolve an MPN "
            f"that AGREES with its dossier; a new value nobody can look up is "
            f"not sourced")

    # -- (8) the change is RECORDED where a later reader will find it
    docs = []
    for p in (release_dir / "MANIFEST.txt", _find_readme(release_dir)):
        if p is not None and p.is_file():
            docs.append(p.read_text(errors="ignore"))
    doctext = "\n".join(docs)
    for ref in declared:
        # the CPL is the authority on a placed part's value; an UNPLACED
        # declared ref still has one, in its BOM Comment.
        was = (dict(old_cpl).get(ref, {}).get("Val", "")
               or old_bom.get(ref, {}).get("Comment", ""))
        new = (cpl_new_val.get(ref, "")
               or cur_bom.get(ref, {}).get("Comment", ""))
        missing = [v for v in (was, new) if v and v not in doctext]
        if missing:
            fails.append(
                f"  VALUE-CHANGE DEVIATION: {ref} moved {was!r} -> {new!r} but "
                f"{missing} appears in neither MANIFEST.txt nor the order "
                f"README — BOTH values must be recorded, or the reason this "
                f"release exists is legible only as a CSV diff against a "
                f"release nobody will still have")
    if not fails:
        notes.append(
            f"  note: fab/cpl.csv delta is {len(cpl_moved)} `Val` cell(s) "
            f"[{'; '.join(cpl_moved)}] over {len(cur_cpl)} row(s), 0 "
            f"coordinate/rotation/layer/package changes, 0 rows added or "
            f"removed; fab/bom.csv moved {len(bom_moved)} designator(s) "
            f"[{', '.join(bom_moved)}], all declared, 0 refs added or removed, "
            f"0 Footprint changes — ASSERTED by value-change mode")
    return fails, notes


def check_cpl_delta(release_dir, prior_dir):
    """The ONE permitted fab/ change in CPL-only mode: `fab/cpl.csv` changing
    only PLACEMENT COORDINATES, or losing whole rows for designators that are
    no longer populated.

    WHY THIS MODE EXISTS. A wrong CPL coordinate is the one defect that is
    100% assembly data and 0% copper: crow-recorder-central-v2 v1.4 shipped
    its only USB-C 1.3025mm off its own pads (canon A-POS) because the
    exporter emitted KiCad's footprint ANCHOR instead of JLC's pad-array
    placement datum. Fixing it changes fab/cpl.csv and NOTHING else — the
    gerbers, drills, BOM, STEP, PDFs and the board itself are byte-identical
    — so docs-only mode correctly refuses, and bom-only mode does not cover
    it either.

    WHAT THIS ASSERTS THAT IDENTITY CANNOT. A rotation is not a coordinate.
    The v1.3 -> v1.4 supersede WAS a CPL-only change and it moved seven
    rotations; had it also smuggled a coordinate, or vice versa, no gate
    would have separated the two. So this mode permits Mid X/Y to move and
    FAILs on any Rotation, Layer, Val or Package change, and on any ADDED
    row. A removed row must be a part that is genuinely off the assembly:
    its designator must not reappear anywhere in the CPL.
    """
    import csv as _csv
    fails, notes = [], []
    cur_p, old_p = release_dir / "fab" / "cpl.csv", prior_dir / "fab" / "cpl.csv"
    if not (cur_p.is_file() and old_p.is_file()):
        fails.append("  CPL-ONLY: fab/cpl.csv missing on one side — cannot "
                     "establish the delta")
        return fails, notes

    def rows(p):
        out = {}
        for r in _csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()):
            ref = (r.get("Designator") or "").strip()
            if ref:
                out[ref] = {k: (v or "").strip() for k, v in r.items()}
        return out

    cur, old = rows(cur_p), rows(old_p)
    added = sorted(set(cur) - set(old))
    removed = sorted(set(old) - set(cur))
    moved, other = [], 0
    for ref in sorted(set(cur) & set(old)):
        c, o = cur[ref], old[ref]
        for col in ("Rotation", "Layer", "Val", "Package"):
            if c.get(col) != o.get(col):
                fails.append(
                    f"  CPL-ONLY DEVIATION: {ref} {col} changed "
                    f"{o.get(col)!r} -> {c.get(col)!r} — a CPL-only supersede "
                    f"may move a part's COORDINATE, never its orientation, "
                    f"side or identity. A rotation change is a different "
                    f"claim needing its own A-ROT evidence")
        dx = c.get("Mid X") != o.get("Mid X")
        dy = c.get("Mid Y") != o.get("Mid Y")
        if dx or dy:
            moved.append(f"{ref} ({o.get('Mid X')},{o.get('Mid Y')}) -> "
                         f"({c.get('Mid X')},{c.get('Mid Y')})")
        else:
            other += 1
    for ref in added:
        fails.append(
            f"  CPL-ONLY DEVIATION: {ref} was ADDED to the CPL — placing a "
            f"part that was not placed before is a population change, not a "
            f"coordinate fix (declare it and cut the right kind of release)")
    if not moved and not removed:
        fails.append(
            "  CPL-ONLY: fab/cpl.csv is byte-equivalent to the prior "
            "release's — a CPL-only supersede that moves nothing and drops "
            "nothing supersedes nothing; use --docs-only-supersede")
    if not fails:
        notes.append(
            f"  note: fab/cpl.csv delta is {len(moved)} coordinate move(s) "
            f"[{'; '.join(moved) or 'none'}] and {len(removed)} row(s) "
            f"REMOVED [{', '.join(removed) or 'none'}]; {other} row(s) "
            f"unchanged; 0 added, 0 rotation/layer/identity changes — "
            f"ASSERTED by cpl-only mode")
    return fails, notes


def check_docs_only(release_dir, prior_dir, bom_only=False,
                    cpl_only=False, legible_bom=False, sourcing=False,
                    value_change=False):
    """Assert the docs-only-supersede contract against the DECLARED prior
    release: fab/source/3d byte-identical (any deviation = FAIL), order
    README + MANIFEST byte-DIFFERENT (identical docs supersede nothing).

    `bom_only=True` relaxes EXACTLY ONE file — fab/bom.csv — and only because
    check_bom_delta() then asserts something stronger about it than identity.
    `legible_bom=True` relaxes the same one file for check_legible_bom_delta().
    `sourcing=True` relaxes fab/bom.csv, every source/*.tsx (canon M3 REQUIRES
    the source to move WITH the BOM) and a re-plotted gerber/drill's own
    timestamp lines — each asserted, more strongly than identity, by
    check_sourcing_delta().
    `value_change=True` relaxes fab/bom.csv, fab/cpl.csv, the re-plotted
    gerber/drill timestamp lines, and the AUTHORING members of source/
    (`.kicad_pcb` `.kicad_sch` `.tsx` `.net` — a value is carried BY those
    files, so canon M3 REQUIRES them to move); check_value_change_delta()
    then asserts far more than identity about every one of them, including
    that the plot is unchanged and that the source really did move.
    Nothing else in fab/, and nothing at all in source/ or 3d/, may move.

    THE FILE SET IS GRADED IN EVERY MODE, and that is not incidental: a file
    ADDED to a sealed release is what this check caught on 2026-07-27 when
    `kicad-cli pcb drc` wrote a `.kicad_prl` into an immutable release —
    invisible to `git status` (gitignored) and invisible to any hash of the
    files you expected NOT to change."""
    fails, notes = [], []
    exempt = set()
    if bom_only or legible_bom:
        exempt = {("fab", "bom.csv")}
    elif cpl_only:
        exempt = {("fab", "cpl.csv")}
    for sub in _DOCS_ONLY_IDENTICAL_DIRS:
        cur = _tree_files(release_dir / sub)
        old = _tree_files(prior_dir / sub)
        if sourcing:
            exempt = {("fab", "bom.csv")}
            exempt |= {("source", rel) for rel in _tree_files(
                release_dir / "source") if rel.endswith(".tsx")}
            exempt |= {("fab", rel) for rel in cur
                       if sub == "fab" and rel.lower().endswith(_REPLOTTABLE)}
        if value_change:
            exempt = {("fab", "bom.csv"), ("fab", "cpl.csv")}
            exempt |= {("source", rel) for rel in _tree_files(
                release_dir / "source")
                if rel.lower().endswith(_AUTHORING_EXT)}
            exempt |= {("fab", rel) for rel in cur
                       if sub == "fab" and rel.lower().endswith(_REPLOTTABLE)}
        for rel in sorted(set(cur) - set(old)):
            fails.append(
                f"  DOCS-ONLY DEVIATION: {sub}/{rel} exists here but not in "
                f"{prior_dir.name} — a docs-only supersede must not ADD "
                f"{sub}/ content; cut a full release instead")
        for rel in sorted(set(old) - set(cur)):
            fails.append(
                f"  DOCS-ONLY DEVIATION: {sub}/{rel} shipped in "
                f"{prior_dir.name} is MISSING here — a docs-only supersede "
                f"must carry the prior release's {sub}/ unchanged")
        same = 0
        for rel in sorted(set(cur) & set(old)):
            if (sub, rel) in exempt:
                continue                      # asserted by check_bom_delta()
            if _sha256(cur[rel]) != _sha256(old[rel]):
                fails.append(
                    f"  DOCS-ONLY DEVIATION: {sub}/{rel} DIFFERS from "
                    f"{prior_dir.name}/{sub}/{rel} — a 'docs-only' release "
                    f"that changes {sub}/ is lying; cut a full release "
                    f"instead")
            else:
                same += 1
        if same:
            _label = ("bom-only" if bom_only else "cpl-only" if cpl_only
                      else "legible-bom" if legible_bom
                      else "sourcing" if sourcing
                      else "value-change" if value_change else "docs-only")
            notes.append(f"  note: {sub}/ byte-identical to {prior_dir.name} "
                         f"({same} file(s)) — ASSERTED by {_label} mode")
    # the documents themselves MUST change — that is the release's whole point
    doc_pairs = [("order README", _find_readme(release_dir),
                  _find_readme(prior_dir)),
                 ("MANIFEST.txt", release_dir / "MANIFEST.txt",
                  prior_dir / "MANIFEST.txt")]
    for label, cp, op in doc_pairs:
        if cp is None or not cp.is_file():
            fails.append(f"  MISSING: {label} in {release_dir.name}")
            continue
        if op is not None and op.is_file() and _sha256(cp) == _sha256(op):
            fails.append(
                f"  DOCS-ONLY UNCHANGED: {label} is byte-identical to "
                f"{prior_dir.name}'s — a docs-only supersede exists to CHANGE "
                f"the documentation; an unchanged {label} supersedes nothing")
    return fails, notes


# --------------------------------------------------------------- check (b)
def _audit_fail_count(audit_text):
    """FAIL count the shipped policy_audit.md actually reports. Prefer its
    'Summary: FAIL=N' line; else count '| ... | FAIL |' table rows."""
    m = re.search(r"Summary:.*?FAIL\s*=\s*(\d+)", audit_text)
    if m:
        return int(m.group(1)), "Summary line"
    rows = re.findall(r"^\s*\|[^|]*\|\s*FAIL\s*\|", audit_text, re.M)
    return len(rows), "table rows"


def _audit_fail_checkids(audit_text):
    """Check-IDs the audit marks FAIL, e.g. {'M-BOM'} from '| M-BOM | FAIL |'."""
    return set(re.findall(r"^\s*\|\s*([A-Za-z0-9\-]+)\s*\|\s*FAIL\s*\|",
                          audit_text, re.M))


def _manifest_claimed_fail(manifest_text):
    """FAIL count the MANIFEST claims for policy_audit. 'policy_audit: 0 FAIL'
    -> 0; 'policy_audit FAIL=1 PASS=24' -> 1; a bare 'PASS' with no explicit
    FAIL count -> 0; unknown -> None.

    THE `FAIL=N` FORM WAS UNREADABLE HERE UNTIL 2026-07-27, AND IT IS THE FORM
    policy_audit.py ITSELF PRINTS. `(\\d+)\\s*FAIL` matches "0 FAIL" but not
    "FAIL=1"; the fallback then saw the word PASS inside "PASS=24" and returned
    **0**. Every MANIFEST in this fleet writes the summary line the audit
    prints — `policy_audit  FAIL=0  PASS=30  WAIVED=2 …` — so every one of them
    was read as "claims 0 FAIL" by ACCIDENT, and the check only ever agreed
    because the true count happened to be 0 as well.

    It bit for the first time on cooksense v1.5, whose MANIFEST honestly says
    `FAIL=1` beside a shipped policy_audit.md that says FAIL=1: the parser read
    the claim as 0, `audit_fail > claimed` fired, and the gate accused an
    HONEST manifest of under-reporting. The dangerous direction is the same
    bug's mirror — a manifest claiming `FAIL=1` beside an audit reporting
    FAIL=5 would also read as claimed=0, so the check could never distinguish a
    manifest that under-reports by 4 from one that under-reports by 5. Ordered
    explicit-first so `FAIL=N` wins and `N FAIL` remains supported.
    """
    for m in re.finditer(r"policy_audit\b[^\n]*", manifest_text):
        seg = m.group(0)
        n = (re.search(r"\bFAIL\s*[=:]\s*(\d+)", seg)
             or re.search(r"(\d+)\s*FAIL\b", seg))
        if n:
            return int(n.group(1))
        if re.search(r"\bPASS\b|\b0\s*board-FAIL\b", seg):
            return 0
    return None


def check_audit_manifest(release_dir):
    """The manifest's claimed policy_audit result must not under-report the
    audit it ships (audit FAIL while manifest claims 0-FAIL / PASS)."""
    audit = release_dir / "verification" / "policy_audit.md"
    manifest = release_dir / "MANIFEST.txt"
    fails = []
    if not audit.is_file():
        return [f"  MISSING: verification/policy_audit.md (cannot verify the "
                f"manifest's claimed audit result)"]
    if not manifest.is_file():
        return [f"  MISSING: MANIFEST.txt"]
    at = audit.read_text(encoding="utf-8-sig")
    mt = manifest.read_text(encoding="utf-8-sig")
    audit_fail, how = _audit_fail_count(at)
    claimed = _manifest_claimed_fail(mt)
    if claimed is None:
        return fails  # manifest makes no machine-readable policy_audit claim
    if audit_fail > claimed:
        ids = _audit_fail_checkids(at)
        idtxt = (" [" + ", ".join(sorted(ids)) + "]") if ids else ""
        fails.append(
            f"  AUDIT/MANIFEST DISAGREEMENT: shipped policy_audit.md reports "
            f"FAIL={audit_fail}{idtxt} (from its {how}) but MANIFEST claims "
            f"policy_audit FAIL={claimed} — the bundle contradicts its own "
            f"claimed result")
    return fails


# --------------------------------------------------------------- check (c)
def _find_readme(release_dir):
    for name in ("ORDER_README.md", "README.md"):
        p = release_dir / name
        if p.is_file():
            return p
    return None


def check_draft_readme(release_dir):
    """The shipped order README must be FINAL — no draft/placeholder markers."""
    readme = _find_readme(release_dir)
    if readme is None:
        return [f"  MISSING: ORDER_README.md / README.md"]
    fails = []
    pat = re.compile(
        r"\b(" + "|".join(re.escape(m) for m in _DRAFT_MARKERS) + r")\b",
        re.I)
    for i, line in enumerate(readme.read_text(encoding="utf-8-sig").splitlines(), 1):
        for m in pat.finditer(line):
            fails.append(
                f"  DRAFT README: {readme.name}:{i} contains draft/placeholder "
                f"marker {m.group(0)!r}: {line.strip()[:100]!r}")
            break  # one finding per line is enough
    return fails


# --------------------------------------------------------------- check (d)
def _erc_claim(text, near=r"\bERC\b"):
    """(errors, warnings) stated in `text` near an ERC mention (`near` is a
    regex); either may be None if not stated. Parses tolerantly: '0 errors
    (1409 baselined warnings)', '0 errors (1215 warnings)', '0 errors / 12
    warnings' — the warning count is the LAST number before 'warning', with
    at most one qualifier word ('baselined') between."""
    m = re.search(near + r"[^\n]{0,120}", text)
    if not m:
        return None, None
    seg = m.group(0)
    e = re.search(r"(\d+)\s+error", seg)
    w = re.search(r"(\d+)(?:\s+[A-Za-z-]+)?\s+warning", seg)
    return (int(e.group(1)) if e else None,
            int(w.group(1)) if w else None)


def _erc_measured(erc_json_path):
    """(errors, warnings) actually recorded in the shipped erc.json, or None
    per field when it is no evidence for that field — file absent/unreadable,
    or the severity was NOT in the run's `included_severities` (an
    errors-only erc.json measures nothing about warnings: cooksense v1.0
    ships exactly that, and a 0 read off it would be a false mismatch)."""
    if not erc_json_path.is_file():
        return None, None
    try:
        import json
        d = json.loads(erc_json_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None, None
    counts = {"error": 0, "warning": 0}
    for sheet in d.get("sheets", []):
        for v in sheet.get("violations", []):
            sev = v.get("severity")
            if sev in counts:
                counts[sev] += 1
    included = d.get("included_severities")
    if included is not None:
        for sev in list(counts):
            if sev not in included:
                counts[sev] = None
    return counts["error"], counts["warning"]


def _bom_data_rows(bom_csv_path):
    """Actual data-row count of fab/bom.csv (rows minus the header), or None
    if absent. csv-parsed so quoted multi-refdes cells count as ONE row."""
    if not bom_csv_path.is_file():
        return None
    import csv
    with bom_csv_path.open(newline="") as f:
        rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    return max(len(rows) - 1, 0)


def _manifest_bom_lines(manifest_text):
    """Line count the MANIFEST's bom_source_check summary claims
    ('bom_source_check PASS (48 lines, ...)'), or None if not stated."""
    m = re.search(r"bom_source_check[^\n(]*\((\d+)\s+lines", manifest_text)
    return int(m.group(1)) if m else None


def _count_disagreement(label, stated):
    """One FAIL line if the non-None values in `stated` (list of
    (source, value)) disagree; else None. Absence is never a mismatch."""
    have = [(src, v) for src, v in stated if v is not None]
    if len({v for _, v in have}) <= 1:
        return None
    vals = ", ".join(f"{src}={v}" for src, v in have)
    return (f"  MANIFEST/EVIDENCE MISMATCH: {label} disagrees across the "
            f"bundle ({vals}) — the manifest's gate summary must match the "
            f"machine evidence it ships")


# 07_releases/<dir>/... references inside verification evidence. The dir
# component must look version-ish (contain v<digit>) so prose like
# '07_releases/.../source/x' or '07_releases/contracts.md' never matches.
_RELPATH_RE = re.compile(
    r"07_releases/((?=[^/\s`'\")\]]*v\d)[^/\s`'\")\]]+)/")


def check_manifest_consistency(release_dir, releases_root):
    """(d) the MANIFEST's human-readable gate summary must not disagree with
    the machine evidence shipped alongside it, and evidence must not embed a
    release path that is not this release."""
    fails = []
    manifest = release_dir / "MANIFEST.txt"
    mt = manifest.read_text(encoding="utf-8-sig") if manifest.is_file() else ""

    # -- ERC counts: MANIFEST vs policy_audit S-ERC row vs erc.json
    stated_e, stated_w = [], []
    if mt:
        e, w = _erc_claim(mt)
        stated_e.append(("MANIFEST", e))
        stated_w.append(("MANIFEST", w))
    audit = release_dir / "verification" / "policy_audit.md"
    if audit.is_file():
        row = re.search(r"^\s*\|\s*S-ERC\s*\|[^\n]*", audit.read_text(encoding="utf-8-sig"), re.M)
        if row:
            e, w = _erc_claim(row.group(0), near=r"^")
            stated_e.append(("policy_audit.md S-ERC", e))
            stated_w.append(("policy_audit.md S-ERC", w))
    me, mw = _erc_measured(release_dir / "verification" / "erc.json")
    stated_e.append(("erc.json", me))
    stated_w.append(("erc.json", mw))
    for label, stated in (("ERC error count", stated_e),
                          ("ERC warning count", stated_w)):
        f = _count_disagreement(label, stated)
        if f:
            fails.append(f)

    # -- BOM line count: MANIFEST claim vs fab/bom.csv actual data rows
    claimed = _manifest_bom_lines(mt)
    actual = _bom_data_rows(release_dir / "fab" / "bom.csv")
    if claimed is not None and actual is not None and claimed != actual:
        fails.append(
            f"  MANIFEST/EVIDENCE MISMATCH: MANIFEST claims bom_source_check "
            f"checked {claimed} lines but fab/bom.csv carries {actual} data "
            f"row(s) — the manifest's gate summary must match the BOM it "
            f"ships")

    # -- release paths embedded in verification evidence must name THIS
    #    release's directory (or an existing sibling — diffing a real
    #    predecessor is legitimate), never a staging/shortened path.
    ver = release_dir / "verification"
    if ver.is_dir():
        for f in sorted(ver.glob("*")):
            if f.suffix not in (".txt", ".md") or not f.is_file():
                continue
            try:
                text = f.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            seen = set()
            for m in _RELPATH_RE.finditer(text):
                name = m.group(1)
                if name in seen or name == release_dir.name:
                    continue
                seen.add(name)
                if (releases_root / name).is_dir():
                    continue  # a real sibling release — legitimate reference
                fails.append(
                    f"  EVIDENCE PATH MISMATCH: verification/{f.name} names "
                    f"'07_releases/{name}/' but this release's directory is "
                    f"'{release_dir.name}' (and no such sibling release "
                    f"exists) — the evidence was produced against a "
                    f"staging/foreign path, not this sealed archive")
    return fails


# --------------------------------------------------------------- check (e)
# A-STOCK — a release seals only against stock evidence that PASSES.
#
# Five sealed releases in this fleet ship stock evidence whose LAST LINE says
# FAIL, including crow-recorder-central-v2 v1.0-v1.3 whose own CPU
# (C6938291, the XU316 SoC) is recorded LOW_STOCK(0). Nothing ever read the
# verdict, so "stock verified" in the MANIFEST meant only that the tool ran.
# Worse, the fleet ships THREE incompatible evidence formats — stdout text, a
# `--out` CSV report saved as stock_check.txt (cooksense v1.1, ZERO verdict
# lines), and a stdout dump saved as .csv — so a parser that gives up on an
# unfamiliar shape is a parser that can be silenced by choosing a shape.
#
# Therefore: a MISSING or UNPARSEABLE VERDICT IS A FAIL, NOT A SKIP. The one
# legitimate way past a non-OK line is an assembly.yaml `sourcing_plan:` entry
# carrying the MEASURED stock and the date it was measured.
#
# This check is OFFLINE: it grades the EVIDENCE the release ships. Live
# re-query stays in the opt-in `--net` tier — a gate that needs the network
# is a gate that gets skipped.
_STOCK_EVIDENCE = ("stock_check.json", "stock_check.txt", "stock_check.csv")
_STOCK_BAD = ("LOW_STOCK", "NOT_FOUND", "QUERY_FAILED", "NO_MATCH")
_VERDICT_RE = re.compile(r"^\s*(PASS|FAIL)\s*:\s*(\d+)\s+coded", re.M)
_LINE_RE = re.compile(
    r"^\s{2,}(OK|LOW_STOCK\(\d+\)|NOT_FOUND|QUERY_FAILED)\s+(C\d+)\s+x(\d+)"
    r".*?(?:stock=(\S+))?\s*$", re.M)


def _placed_coded_lines(release_dir):
    """{lcsc: qty} for every coded BOM line with at least one ref ON the CPL.
    `qty` counts only the refs actually placed — an unpopulated ref consumes
    no stock. Returns None when the release ships no BOM/CPL to grade."""
    import csv as _csv
    bom = release_dir / "fab" / "bom.csv"
    cpl = release_dir / "fab" / "cpl.csv"
    if not bom.is_file() or not cpl.is_file():
        return None
    with cpl.open(newline="") as f:
        placed = {(r.get("Designator") or "").strip()
                  for r in _csv.DictReader(f)}
    out = {}
    with bom.open(newline="") as f:
        for r in _csv.DictReader(f):
            code = (r.get("LCSC") or "").strip()
            if not code:
                continue
            n = sum(1 for d in (r.get("Designator") or "").split(",")
                    if d.strip() in placed)
            if n:
                out[code] = out.get(code, 0) + n
    return out


def _parse_stock_evidence(path):
    """(verdict, {lcsc: (status, stock_or_None)}) from any of the shipped
    formats. `verdict` is 'PASS' / 'FAIL' / None — None means the file states
    no verdict, which is itself the finding."""
    lines = {}
    if path.suffix == ".json":
        import json as _json
        try:
            d = _json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return None, lines
        for e in d.get("lines", []):
            code = str(e.get("lcsc") or "").strip()
            if code:
                st = str(e.get("status") or "")
                try:
                    stock = int(e.get("stock"))
                except (TypeError, ValueError):
                    stock = None
                lines[code] = (st, stock)
        v = str(d.get("verdict") or "").upper()
        return (v if v in ("PASS", "FAIL") else None), lines
    text = path.read_text(errors="ignore")
    for m in _LINE_RE.finditer(text):
        st, code, _qty, stock = m.groups()
        try:
            stock = int(stock)
        except (TypeError, ValueError):
            stock = None
        lines[code] = (st, stock)
    if not lines:                       # the `--out` CSV report shape
        import csv as _csv
        try:
            rows = list(_csv.DictReader(path.open(newline="")))
        except Exception:
            rows = []
        for r in rows:
            code = (r.get("code") or r.get("LCSC") or "").strip()
            if not code:
                continue
            try:
                stock = int(r.get("stock"))
            except (TypeError, ValueError):
                stock = None
            lines[code] = ((r.get("status") or ""), stock)
    m = _VERDICT_RE.search(text)
    return (m.group(1) if m else None), lines


#: `sourcing_plan[].order_status` — the CLOSED vocabulary a plan must use when
#: its OWN measured number does not cover `qty x build_quantity`. An unknown
#: value is a FAIL, never a coercion to the permissive one.
_ORDER_STATUS_VOCAB = ("PLANNED", "BLOCKED")


def _ungraded_sourcing(reason):
    """The sourcing verdict for a release whose lines could not be measured.
    UNGRADED is never CLEAR: checks (f)/(g) compare against a MEASUREMENT and
    must not compare against an absence (canon M-COVER)."""
    return {"graded": False, "status": "UNGRADED", "why": reason,
            "planned": [], "blocked": [], "measured_on": None,
            "n_lines": 0, "n_graded": 0}


def check_stock(release_dir, assembly, evidence_override=None):
    """(e) grade the SHIPPED stock evidence for every coded, placed BOM line.

    Returns `(fails, notes, sourcing)`. `sourcing` is the MEASURED order-
    readiness of this release — the input checks (f) and (g) grade the
    release's own DECLARATIONS against."""
    fails, notes = [], []
    want = _placed_coded_lines(release_dir)
    if want is None:
        notes.append("  note: A-STOCK: this release ships no fab/bom.csv + "
                     "fab/cpl.csv pair — no coded, placed line to grade")
        return fails, notes, _ungraded_sourcing("no fab/bom.csv + fab/cpl.csv")
    qty_mult = int(assembly.get("build_quantity") or 5)
    if not assembly.get("build_quantity"):
        notes.append("  note: A-STOCK: no assembly.yaml build_quantity — "
                     "grading against the 5-board default")
    plan = {}
    for e in (assembly.get("sourcing_plan") or []):
        code = str(e.get("lcsc") or "").strip()
        if (code and e.get("measured_stock") is not None
                and str(e.get("measured_on") or "").strip()):
            plan[code] = e
        elif code:
            fails.append(
                f"  STOCK-PLAN-INCOMPLETE: sourcing_plan entry for {code} is "
                f"missing measured_stock and/or measured_on — a plan without "
                f"the measured number and its date is a hope, not evidence")
        st = str(e.get("order_status") or "").strip().upper()
        if code and st and st not in _ORDER_STATUS_VOCAB:
            fails.append(
                f"  STOCK-PLAN-BAD-STATUS: sourcing_plan entry for {code} "
                f"declares order_status {st!r}, which is outside the closed "
                f"vocabulary {'|'.join(_ORDER_STATUS_VOCAB)} — an unreadable "
                f"classification is a FAIL, never a fallback to the "
                f"permissive one")

    ver = release_dir / "verification"
    if evidence_override is not None:
        ev = Path(evidence_override)
        if not ev.is_file():
            fails.append(
                f"  STOCK-NO-EVIDENCE: --stock-evidence {ev} does not exist — "
                f"an order-time re-grade against a file that is not there "
                f"grades nothing")
            return fails, notes, _ungraded_sourcing("--stock-evidence absent")
        notes.append(f"  note: A-STOCK: ORDER-TIME re-grade — grading {ev} "
                     f"INSTEAD of the sealed verification/ evidence (the "
                     f"archive is immutable and is not touched)")
    else:
        ev = next((ver / n for n in _STOCK_EVIDENCE if (ver / n).is_file()),
                  None)
    if ev is None:
        fails.append(
            f"  STOCK-NO-EVIDENCE: {len(want)} coded line(s) are on the CPL "
            f"but verification/ ships no stock evidence "
            f"({'/'.join(_STOCK_EVIDENCE)}) — a release with unverified "
            f"sourcing is not orderable")
        return fails, notes, _ungraded_sourcing("no stock evidence shipped")
    verdict, lines = _parse_stock_evidence(ev)
    notes.append(f"  note: A-STOCK: grading verification/{ev.name} "
                 f"({len(lines)} graded line(s), verdict={verdict}) against "
                 f"{len(want)} coded+placed BOM line(s) x {qty_mult} boards")
    if verdict is None:
        fails.append(
            f"  STOCK-NO-VERDICT: verification/{ev.name} states no parseable "
            f"PASS:/FAIL: verdict — the VERDICT LINE IS THE GATE, so evidence "
            f"that omits it is unverified sourcing, never a pass (cooksense "
            f"v1.1 shipped a raw CSV report with zero verdict lines)")
    elif verdict == "FAIL":
        problem = {c for c, (st, _s) in lines.items()
                   if any(b in st for b in _STOCK_BAD)}
        # Only a problem line that is actually PLACED and unplanned accuses
        # this release: an unpopulated hand-solder/consign line legitimately
        # reads LOW_STOCK(0) and is A-POP's business, not A-STOCK's.
        bad = sorted((problem & set(want)) - set(plan))
        if bad:
            fails.append(
                f"  STOCK-VERDICT-FAIL: verification/{ev.name} ends in a FAIL "
                f"verdict; unplanned PLACED problem line(s): "
                f"{', '.join(bad[:12])} — seal only against a PASS, or record "
                f"each line in assembly.yaml `sourcing_plan:` with its "
                f"measured stock + date")
        elif problem:
            notes.append(
                f"  note: A-STOCK: verification/{ev.name} verdict is FAIL but "
                f"every problem line ({', '.join(sorted(problem)[:8])}) is "
                f"unplaced or covered by a sourcing_plan entry")
        else:
            fails.append(
                f"  STOCK-VERDICT-FAIL: verification/{ev.name} ends in a FAIL "
                f"verdict and no line-level status could be parsed from it — "
                f"the release cannot show WHICH line failed")
    planned, blocked, plan_dates, unclassified = [], [], [], []
    for code, qty in sorted(want.items()):
        need = qty * qty_mult
        e = plan.get(code)
        if e is not None:
            try:
                measured = int(e.get("measured_stock"))
            except (TypeError, ValueError):
                measured = None
            st = str(e.get("order_status") or "").strip().upper()
            if measured is not None and measured >= need:
                # The plan's own number COVERS the build: the line is cleared
                # by evidence, and may not simultaneously claim otherwise.
                if st in _ORDER_STATUS_VOCAB:
                    fails.append(
                        f"  ORDER-PLAN-OVERCLAIM: sourcing_plan entry for "
                        f"{code} declares order_status {st} while its own "
                        f"measured_stock {measured} covers {qty} x {qty_mult} "
                        f"= {need} — a release may not invent a blocked line "
                        f"any more than it may hide one")
                continue
            # THE SHORTFALL CASE. Until 2026-07-30 this fell through
            # `if code in plan: continue` and CLEARED SILENTLY, whatever the
            # plan's own number said. It must now classify itself.
            if st not in _ORDER_STATUS_VOCAB:
                fails.append(
                    f"  ORDER-PLAN-UNCLASSIFIED: sourcing_plan entry for "
                    f"{code} measures stock {measured} against {qty} x "
                    f"{qty_mult} = {need} and states no `order_status:` "
                    f"({'|'.join(_ORDER_STATUS_VOCAB)}) — a plan whose OWN "
                    f"number does not cover the build used to clear the line "
                    f"silently, which is how a release could seal unbuyable "
                    f"with nothing anywhere saying so")
                unclassified.append(code)
                continue
            (blocked if st == "BLOCKED" else planned).append(code)
            plan_dates.append(str(e.get("measured_on") or "").strip())
            continue
        if code not in lines:
            fails.append(
                f"  STOCK-UNGRADED: {code} (x{qty} placed) has no line in "
                f"verification/{ev.name} — a placed part with no stock "
                f"evidence was never sourced, only assumed")
            continue
        st, stock = lines[code]
        if stock is not None and stock < need:
            fails.append(
                f"  STOCK-INSUFFICIENT: {code} stock={stock} < {qty} x "
                f"{qty_mult} boards = {need} (status {st}) and no "
                f"assembly.yaml sourcing_plan entry names a measured "
                f"alternative")
        elif stock is None and any(b in st for b in _STOCK_BAD):
            fails.append(
                f"  STOCK-INSUFFICIENT: {code} graded {st} with no readable "
                f"stock number and no sourcing_plan entry")
    if unclassified:
        # M-COVER: a line whose state could not be read leaves the RELEASE's
        # state unread. UNGRADED is not CLEAR, and (f)/(g) grade nothing
        # against it — the finding above is the whole report.
        return fails, notes, _ungraded_sourcing(
            f"{len(unclassified)} unclassified sourcing_plan line(s): "
            f"{', '.join(sorted(unclassified))}")
    status = "BLOCKED" if blocked else "PLANNED" if planned else "CLEAR"
    sourcing = {
        "graded": True, "status": status, "why": "",
        "planned": sorted(planned), "blocked": sorted(blocked),
        "measured_on": max((d for d in plan_dates if d), default=None),
        "n_lines": len(want), "n_graded": len(lines),
    }
    return fails, notes, sourcing


def check_pcba_availability(release_dir, evidence):
    """Grade final JLCPCB order allocation for the exact release BOM.

    LCSC catalog stock is deliberately absent from this decision.  A valid
    REJECTED receipt is a measured BLOCKED sourcing state; missing, stale,
    partial, moved, or hash-mismatched evidence is UNGRADED and fails closed.
    """
    fails, notes = [], []
    if not evidence:
        fails.append(
            "  PCBA-NO-EVIDENCE: sourcing authority is jlc-pcba but no "
            "--pcba-evidence receipt was supplied — catalog stock cannot "
            "authorize a JLCPCB assembly order")
        return fails, notes, _ungraded_sourcing("no JLCPCB PCBA receipt")
    path = Path(evidence).resolve()
    try:
        from jlc_pcba_availability import verify_receipt
        valid, problems, receipt = verify_receipt(
            path, bom=release_dir / "fab/bom.csv", required_phase="order")
    except Exception as exc:
        valid, problems, receipt = False, [str(exc)], {}
    if not valid:
        for problem in problems:
            fails.append(f"  PCBA-EVIDENCE-INVALID: {problem}")
        return fails, notes, _ungraded_sourcing("invalid JLCPCB PCBA receipt")
    rows = receipt.get("rows") or []
    incomplete = [row for row in rows if row.get("status") == "INCOMPLETE"]
    if receipt.get("verdict") == "INCOMPLETE" or incomplete:
        fails.append(
            f"  PCBA-EVIDENCE-INCOMPLETE: {len(incomplete)} line(s) are "
            "unresolved; an incomplete uploader capture is not an order fact")
        return fails, notes, _ungraded_sourcing("incomplete JLCPCB PCBA receipt")
    blocked = sorted({str(row.get("requested_lcsc") or "") for row in rows
                      if row.get("status") == "FAIL"})
    dates = sorted({str(row.get("checked_at") or "")[:10] for row in rows
                    if row.get("checked_at")})
    status = "BLOCKED" if blocked else "CLEAR"
    notes.append(
        f"  note: J-PCBA-FINAL: {path} measures {status} over "
        f"{len(rows)}/{len(rows)} exact line(s); authority="
        f"{receipt.get('authority')}; catalog stock is advisory only")
    return fails, notes, {
        "graded": True, "status": status, "why": "", "planned": [],
        "blocked": blocked, "measured_on": max(dates, default=None),
        "n_lines": len(rows), "n_graded": len(rows),
    }


def _contract_sourcing_authority(release_dir):
    """Select the declared project contract without changing old releases."""
    candidates = [release_dir / "MANIFEST.txt",
                  release_dir.parent / "contracts.md"]
    candidates.extend(parent / "07_releases/contracts.md"
                      for parent in release_dir.parents)
    for path in candidates:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        match = re.search(r"^sourcing_authority:\s*([a-z0-9-]+)\s*$",
                          text, re.M)
        if match:
            return match.group(1)
    return "catalog-legacy"


# --------------------------------------------------------------- check (f)
# A-BUY — a release that is NOT ORDERABLE may seal, and only out loud.
#
# The permission and the obligation are one clause: `SOURCING: BLOCKED-<n>`
# stops vetoing the DESIGN claim, and in exchange the release must carry the
# fact where a BUYER meets it — the MANIFEST's own gate summary and the FIRST
# SCREEN of ORDER_README.md — with the COUNT, every blocked LCSC, and the DATE
# the stock was measured. All three are cross-checked against the measurement,
# in BOTH directions, so the declaration cannot drift from the fact and cannot
# be satisfied by an adjective. (That two-way form is deliberate: R-LEN passed
# a board on the word "lengthens" in a comment about creepage, so a gate that
# credits prose is a gate that credits nothing.)

#: The ORDER_README's first screen. A buyer scrolls; a buyer in a hurry does
#: not. cooksense v1.7's hand-written non-orderable banner lands at line 14.
_README_BANNER_LINES = 40

#: A stock reading is perishable. A `measured_on` this much older than the
#: release date is not evidence ABOUT this release.
_STOCK_MEASUREMENT_MAX_AGE_DAYS = 7

#: The gate line, in MANIFEST.txt and in ORDER_README.md:
#:     SOURCING: BLOCKED-1 (C265111; measured 2026-07-30)
#: Leading markdown decoration is tolerated; the VALUE never is — status,
#: count, codes and date are all compared as data.
_SOURCING_DECL_RE = re.compile(
    r"SOURCING:\s*(CLEAR|PLANNED-\d+|BLOCKED-\d+)\b[^\n(]*(?:\(([^)]*)\))?",
    re.I)
_ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_LCSC_RE = re.compile(r"\bC\d{3,}\b")


def _parse_sourcing_declaration(text):
    """(status, count, {codes}, date) for the FIRST `SOURCING:` gate line in
    `text`, or None when it states none. `count`/`date` may be None — an
    incomplete declaration is reported by the caller, never repaired here."""
    m = _SOURCING_DECL_RE.search(text or "")
    if not m:
        return None
    raw = m.group(1).upper()
    status = raw.split("-")[0]
    count = int(raw.split("-")[1]) if "-" in raw else None
    detail = m.group(2) or ""
    d = _ISO_DATE_RE.search(detail)
    return status, count, set(_LCSC_RE.findall(detail)), (d.group(1) if d
                                                          else None)


def _release_date(release_dir):
    """The YYYY-MM-DD trailing the release directory name, or None."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})$", release_dir.name)
    return m.group(1) if m else None


def _days_between(later, earlier):
    """`later - earlier` in days, or None if either is unparseable."""
    from datetime import date
    try:
        a = date(*(int(x) for x in later.split("-")))
        b = date(*(int(x) for x in earlier.split("-")))
    except (AttributeError, TypeError, ValueError):
        return None
    return (a - b).days


def _grade_declaration(where, decl, status, codes, date):
    """The declaration in `where` must MATCH the measurement, as data."""
    fails = []
    d_status, d_count, d_codes, d_date = decl
    if d_status != status:
        fails.append(
            f"  ORDER-DECL-MISMATCH: {where} declares SOURCING: {d_status} "
            f"but the shipped evidence measures {status} — the release's own "
            f"gate line contradicts the evidence it bundles")
    if d_count is not None and d_count != len(codes):
        fails.append(
            f"  ORDER-DECL-MISMATCH: {where} declares {d_status}-{d_count} "
            f"but {len(codes)} line(s) measure {status} "
            f"({', '.join(sorted(codes))}) — the count is the claim")
    missing = sorted(set(codes) - d_codes)
    extra = sorted(d_codes - set(codes))
    if missing:
        fails.append(
            f"  ORDER-DECL-MISMATCH: {where}'s SOURCING line does not name "
            f"{', '.join(missing)} — a buyer told 'one line is blocked' and "
            f"not told WHICH has been told nothing actionable")
    if extra:
        fails.append(
            f"  ORDER-DECL-MISMATCH: {where}'s SOURCING line names "
            f"{', '.join(extra)}, which the evidence does not measure as "
            f"{status} — a stale declaration is a false statement about the "
            f"catalog, not a harmless surplus")
    if d_date is None:
        fails.append(
            f"  ORDER-DECL-UNDATED: {where}'s SOURCING line carries no "
            f"YYYY-MM-DD — stock changes hourly (this line read 0 on "
            f"2026-07-29 and 5 on 2026-07-30), so an undated reading is not "
            f"evidence about any particular day")
    elif date and d_date != date:
        fails.append(
            f"  ORDER-DECL-UNDATED: {where}'s SOURCING line is dated "
            f"{d_date} but the newest blocking `measured_on` is {date} — the "
            f"declaration must carry the date of the measurement it reports")
    return fails


def check_order_declaration(release_dir, sourcing):
    """(f) A-BUY: the ORDER-READINESS claim is true, complete and LOUD."""
    fails, notes = [], []
    manifest = release_dir / "MANIFEST.txt"
    readme = _find_readme(release_dir)
    mtext = (manifest.read_text(encoding="utf-8-sig", errors="replace")
             if manifest.is_file() else "")
    rtext = (readme.read_text(encoding="utf-8-sig", errors="replace")
             if readme is not None else "")
    mdecl = _parse_sourcing_declaration(mtext)
    if not sourcing["graded"]:
        notes.append(f"  note: A-BUY: sourcing UNGRADED ({sourcing['why']}) "
                     f"— 0 line(s) measured, so no declaration is graded "
                     f"either way")
        return fails, notes
    status = sourcing["status"]
    codes = sourcing["blocked"] if status == "BLOCKED" else sourcing["planned"]
    notes.append(
        f"  note: A-BUY: measured SOURCING: {status}"
        f"{'-%d' % len(codes) if codes else ''}"
        f"{' (' + ', '.join(codes) + ')' if codes else ''} over "
        f"{sourcing['n_lines']} coded+placed line(s)")
    if status != "BLOCKED":
        # No declaration is REQUIRED here — but one that is present must be
        # true. A release may not scare a buyer off a line it can supply.
        if mdecl is not None and mdecl[0] != status:
            fails.append(
                f"  ORDER-DECL-FALSE: MANIFEST.txt declares SOURCING: "
                f"{mdecl[0]} while the shipped evidence measures {status} — "
                f"the declaration and the measurement have one authority "
                f"between them, and it is the measurement")
        return fails, notes

    date = sourcing["measured_on"]
    rel_date = _release_date(release_dir)
    age = _days_between(rel_date, date) if (rel_date and date) else None
    if age is not None and age < 0:
        # THE MEASUREMENT POSTDATES THE SEAL. `sourcing_plan:` lives in
        # `03_src/`, which keeps moving, so every sealed release of a board is
        # re-graded against a later sourcing reading — and 07_releases is
        # IMMUTABLE, so an archive can never be made to declare a fact
        # discovered after it was written. Reporting the status is right (that
        # is what an order-time re-grade is for); FAILING the archive for not
        # having declared it is the retro-fill the release contract forbids.
        notes.append(
            f"  note: A-BUY: the blocking measurement is dated {date}, "
            f"{-age} day(s) AFTER this release ({rel_date}) — the archive is "
            f"immutable and could not have declared it. Status reported, "
            f"declaration NOT required; re-grade at order time with "
            f"--claim sourcing with fresh authority evidence")
        return fails, notes
    if age is not None and age > _STOCK_MEASUREMENT_MAX_AGE_DAYS:
        fails.append(
            f"  ORDER-DECL-STALE: the blocking measurement is dated {date}, "
            f"{age} days before this release ({rel_date}) and past the "
            f"{_STOCK_MEASUREMENT_MAX_AGE_DAYS}-day bound — a release may "
            f"seal NOT-ORDERABLE only on a reading taken about ITSELF")
    if mdecl is None:
        fails.append(
            f"  ORDER-UNDECLARED: {len(codes)} BOM line(s) "
            f"({', '.join(codes)}) are declared BLOCKED in assembly.yaml and "
            f"MANIFEST.txt states no `SOURCING: BLOCKED-{len(codes)} "
            f"(<codes>; measured <date>)` gate line — sealing a "
            f"non-orderable release is permitted; sealing one QUIETLY is not")
    else:
        fails += _grade_declaration("MANIFEST.txt", mdecl, status, codes, date)
    if readme is None:
        fails.append(
            f"  ORDER-README-SILENT: no ORDER_README.md/README.md to carry "
            f"the non-orderable status to the buyer")
        return fails, notes
    head = "\n".join(rtext.splitlines()[:_README_BANNER_LINES])
    rdecl = _parse_sourcing_declaration(head)
    if rdecl is None:
        fails.append(
            f"  ORDER-README-SILENT: {readme.name} states no `SOURCING: "
            f"BLOCKED-{len(codes)}` gate line in its first "
            f"{_README_BANNER_LINES} lines — the buyer's first screen is the "
            f"one place this fact has to be, and a warning 900 lines down is "
            f"a warning for the reader who already knew")
    else:
        fails += _grade_declaration(readme.name, rdecl, status, codes, date)
    silent = [c for c in codes if c not in rtext]
    if silent:
        fails.append(
            f"  ORDER-README-SILENT: {readme.name} never mentions "
            f"{', '.join(silent)} anywhere — the buyer cannot act on a code "
            f"the order document does not carry")
    return fails, notes


# --------------------------------------------------------------- check (g)
# M-REV — the red-team verdicts, graded as a CLOSED VOCABULARY.

#: The two files the 07_releases contract REQUIRES by name. Deliberately not a
#: `redteam*.md` glob: releases archive dated reviews of EARLIER versions
#: beside these, and grading a v1.0 review's verdict against a v1.12 release
#: is the adjacent-property error. Presence is A-EVID's job (it walks the
#: contract's REQUIRED list); this check grades the verdicts of what is here.
_REVIEW_LENS_FILES = ("redteam_topology.md", "redteam_layout.md")
_REVIEW_HEADER_LINES = 40
_DESIGN_VERDICT_VOCAB = ("SOUND", "DEFECTIVE")
_ORDER_VERDICT_VOCAB = ("ORDER", "DO-NOT-ORDER", "BLOCKED-SOURCING")

#: A single legacy `verdict:` maps CONSERVATIVELY. A refusal stays a refusal:
#: the split gives the NEXT reviewer a vocabulary, it does not re-adjudicate
#: the last one. `None` = this shape states no order verdict at all.
_LEGACY_VERDICT_MAP = {
    "ORDER": ("SOUND", "ORDER"),
    "PASS": ("SOUND", None),
    "PASS-WITH-NOTES": ("SOUND", None),
    "DO-NOT-ORDER": ("DEFECTIVE", "DO-NOT-ORDER"),
    "FAIL": ("DEFECTIVE", "DO-NOT-ORDER"),
}
_REVIEW_KEY_RE = re.compile(
    r"^[>\s*#`]*(design_verdict|order_verdict|verdict)\s*:\s*(.+)$", re.I)


def _verdict_token(raw):
    """The first whitespace-delimited token of a verdict value, stripped of
    markdown and trailing punctuation, upper-cased. Deliberately NOT a prose
    parse: `VERDICT AT RUN TIME: **DO NOT ORDER.**` yields no key match at
    all and is reported as stating no verdict, which is the truth about it."""
    tok = raw.strip().lstrip("*`_ ").split()
    if not tok:
        return ""
    return tok[0].strip("*`_.,;:()[]").upper()


def _read_review_header(path):
    """{key: token} from the first `_REVIEW_HEADER_LINES` lines."""
    out = {}
    try:
        lines = path.read_text(encoding="utf-8-sig",
                               errors="replace").splitlines()
    except OSError:
        return out
    for line in lines[:_REVIEW_HEADER_LINES]:
        m = _REVIEW_KEY_RE.match(line)
        if m:
            out.setdefault(m.group(1).lower(), _verdict_token(m.group(2)))
    return out


def check_reviews(release_dir, sourcing):
    """(g) M-REV: grade both claims out of the shipped red-team lens files.

    Returns `(design_fails, sourcing_fails, notes)` — the two claims are
    separated at the point they are read, which is the whole change."""
    dfails, sfails, notes = [], [], []
    ver = release_dir / "verification"
    present = sorted(p.name for p in ver.glob("*.md")
                     if "redteam" in p.name.lower()) if ver.is_dir() else []
    graded = [n for n in _REVIEW_LENS_FILES if (ver / n).is_file()]
    notes.append(
        f"  note: M-REV: {len(graded)} graded / {len(present)} redteam*.md "
        f"present in verification/ (graded = the contract-named "
        f"{', '.join(_REVIEW_LENS_FILES)}; others are archived reviews of "
        f"other versions and are not this release's verdict)")
    missing = [n for n in _REVIEW_LENS_FILES if n not in graded]
    if missing:
        finding = (
            f"  REVIEW-COVERAGE: expected {len(_REVIEW_LENS_FILES)}/"
            f"{len(_REVIEW_LENS_FILES)} contract-named red-team lenses; "
            f"graded {len(graded)}/{len(_REVIEW_LENS_FILES)}; missing "
            f"{', '.join('verification/' + n for n in missing)}. Zero or "
            f"partial review coverage is a FAIL, never a skip")
        dfails.append(finding)
        sfails.append(finding)
    for name in graded:
        hdr = _read_review_header(ver / name)
        design = hdr.get("design_verdict")
        order = hdr.get("order_verdict")
        legacy = hdr.get("verdict")
        if design is None and order is None:
            if legacy is None:
                dfails.append(
                    f"  REVIEW-NO-VERDICT: verification/{name} states no "
                    f"`design_verdict:`/`order_verdict:` (or legacy "
                    f"`verdict:`) in its first {_REVIEW_HEADER_LINES} lines — "
                    f"the contract has required a lens verdict since it was "
                    f"written and nothing ever parsed the field. A missing "
                    f"verdict is a FAIL, never a skip")
                continue
            if legacy not in _LEGACY_VERDICT_MAP:
                dfails.append(
                    f"  REVIEW-VERDICT-UNPARSEABLE: verification/{name} "
                    f"states `verdict: {legacy}`, outside the vocabulary "
                    f"{'|'.join(sorted(_LEGACY_VERDICT_MAP))} — a verdict is "
                    f"graded as DATA and never scraped out of prose, so a "
                    f"lens that says two things in one field says none")
                continue
            design, order = _LEGACY_VERDICT_MAP[legacy]
            notes.append(f"  note: M-REV: verification/{name} carries the "
                         f"legacy single `verdict: {legacy}` -> "
                         f"design_verdict {design}, order_verdict "
                         f"{order or 'UNSTATED'}")
        if design is not None and design not in _DESIGN_VERDICT_VOCAB:
            dfails.append(
                f"  REVIEW-VERDICT-UNPARSEABLE: verification/{name} states "
                f"`design_verdict: {design}`, outside "
                f"{'|'.join(_DESIGN_VERDICT_VOCAB)}")
            design = None
        if order is not None and order not in _ORDER_VERDICT_VOCAB:
            sfails.append(
                f"  REVIEW-VERDICT-UNPARSEABLE: verification/{name} states "
                f"`order_verdict: {order}`, outside "
                f"{'|'.join(_ORDER_VERDICT_VOCAB)}")
            order = None
        if design == "DEFECTIVE":
            dfails.append(
                f"  REVIEW-DESIGN-DEFECTIVE: verification/{name} grades this "
                f"release's DESIGN defective — a design-side red blocks the "
                f"seal exactly as it always has. The split adds a dimension; "
                f"it adds no way past this line")
        if order == "DO-NOT-ORDER":
            sfails.append(
                f"  REVIEW-DO-NOT-ORDER: verification/{name} grades this "
                f"release DO-NOT-ORDER. If the reason is SOURCING and the "
                f"design is sound, the lens has the vocabulary to say so — "
                f"`design_verdict: SOUND` + `order_verdict: BLOCKED-SOURCING` "
                f"— and re-graded that way the seal is permitted")
        if not sourcing["graded"] or order is None:
            continue
        if order == "ORDER" and sourcing["status"] == "BLOCKED":
            sfails.append(
                f"  REVIEW-ORDER-CONTRADICTS-EVIDENCE: verification/{name} "
                f"grades this release ORDER while its own shipped stock "
                f"evidence measures BLOCKED-{len(sourcing['blocked'])} "
                f"({', '.join(sourcing['blocked'])}) — a lens may not certify "
                f"an order the archive it graded cannot place")
        if order == "BLOCKED-SOURCING" and sourcing["status"] == "CLEAR":
            sfails.append(
                f"  REVIEW-ORDER-CONTRADICTS-EVIDENCE: verification/{name} "
                f"grades this release BLOCKED-SOURCING while every coded, "
                f"placed line clears its build quantity — BLOCKED-SOURCING is "
                f"a MEASUREMENT, not a mood, and an unfounded one costs the "
                f"buyer a real order")
    return dfails, sfails, notes


def _load_assembly(release_dir, override):
    """assembly.yaml for this release: --assembly, else the project's
    03_src/rules/assembly.yaml (a release is projects/<b>/07_releases/<r>/)."""
    p = Path(override) if override else (release_dir.parent.parent
                                         / "03_src" / "rules" / "assembly.yaml")
    if not p.is_file():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8-sig")) or {}


# ------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description="release-artifact freshness gate")
    ap.add_argument("release_dir")
    ap.add_argument("--releases-root", default=None,
                    help="the 07_releases/ dir (default: release_dir's parent)")
    ap.add_argument("--allow-identical", action="append", default=[],
                    metavar="RELPATH",
                    help="waive a same-named-identical artifact (edge case: "
                         "doc-only re-release)")
    ap.add_argument("--docs-only-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="docs-only supersede mode: ASSERT fab/source/3d "
                         "byte-identical to PRIOR_RELEASE_DIR (any deviation "
                         "FAILs), allow identical pdf/, and REQUIRE the order "
                         "README + MANIFEST to differ; the stale check is "
                         "replaced by this identity assertion, checks (b)/(c) "
                         "still run")
    ap.add_argument("--cpl-only-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="CPL-only supersede mode: docs-only, PLUS the one "
                         "permitted fab/ change — fab/cpl.csv moving "
                         "PLACEMENT COORDINATES or dropping whole rows for "
                         "designators that are no longer populated (canon "
                         "A-POS: a coordinate emitted at the wrong datum is "
                         "100%% assembly data and 0%% copper). Everything "
                         "else in fab/, and all of source/ and 3d/, must "
                         "still be byte-identical. A ROTATION, Layer, Val or "
                         "Package change, or an ADDED row, FAILs")
    ap.add_argument("--bom-only-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="BOM-only supersede mode: docs-only, PLUS the one "
                         "permitted fab/ change — fab/bom.csv losing whole "
                         "rows for designators that are NOT on the CPL "
                         "(canon A-POP: an unplaced part must leave the "
                         "assembly BOM). Everything else in fab/, and all of "
                         "source/ and 3d/, must still be byte-identical. Rows "
                         "ADDED or EDITED, or a removal for a still-placed "
                         "designator, FAIL")
    ap.add_argument("--legible-bom-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="LEGIBLE-BOM supersede mode (canon F-LEGIBLE, "
                         "ADR-0006): docs-only, PLUS the one permitted fab/ "
                         "change — fab/bom.csv rewriting ONLY its Comment and "
                         "MPN columns so JLC can PARSE it. Every row's "
                         "designator group, Footprint and LCSC must be "
                         "UNCHANGED (a changed LCSC is a substitution; a "
                         "changed Footprint is a different board), no row may "
                         "be added or removed, no MPN may be blanked, this "
                         "release's BOM must PASS bom_legibility_check and "
                         "the prior one must FAIL it")
    ap.add_argument("--sourcing-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="SOURCING supersede mode (canon M8, promoted from the "
                         "seven file waivers usb-hub-3s-v3 v1.11 shipped "
                         "instead): docs-only, PLUS the one permitted fab/ "
                         "change — fab/bom.csv moving MPN+LCSC on the "
                         "SUBSTITUTED rows because JLC will not SUPPLY the "
                         "part. ASSERTS the .kicad_pcb md5 identical, "
                         "fab/cpl.csv byte-identical, every gerber/drill "
                         "identical after stripping ONLY the plot's own "
                         "timestamps (so a re-plot is accepted), the BOM's row "
                         "count and designator order unchanged with no cell "
                         "but MPN/LCSC moving, no blank MPN and no blank LCSC "
                         "on a substituted row, F-LEGIBLE PASSing, the "
                         "source/*.tsx CHANGED (canon M3 — a BOM that moved "
                         "without its source is HAND-EDITED), and BOTH codes "
                         "of every substitution named in MANIFEST/README")
    ap.add_argument("--value-change-supersede", metavar="PRIOR_RELEASE_DIR",
                    default=None,
                    help="VALUE-CHANGE supersede mode: a PART VALUE moved on "
                         "already-placed parts (22k -> 33k), so the ASSEMBLY "
                         "DATA moves and the COPPER does not — the exporter "
                         "feeds one `fp.GetValue()` string to both the BOM "
                         "Comment and the CPL Val. REQUIRES --designators. "
                         "ASSERTS every gerber/drill identical after stripping "
                         "ONLY the plot's own timestamps (so a re-plot is "
                         "accepted), the source/.kicad_pcb AND .kicad_sch "
                         "CHANGED with both md5s printed (canon M3 — an "
                         "unchanged source means a HAND-EDITED CSV), the CPL "
                         "delta confined to `Val` cells with every coordinate/"
                         "rotation/layer/package and the row order unchanged, "
                         "the BOM delta confined to the DECLARED designators "
                         "with no ref added or dropped and no Footprint "
                         "moving, each declared ref's LCSC moving with its "
                         "value (a different value is a different part), the "
                         "CPL Val agreeing with the BOM Comment, F-LEGIBLE "
                         "PASSing, and BOTH the old and new value recorded in "
                         "MANIFEST/README")
    ap.add_argument("--designators", action="append", default=[],
                    metavar="R4,R5",
                    help="the refdes whose VALUE this release changes — the "
                         "list --value-change-supersede confines the BOM/CPL "
                         "delta to. Repeatable and/or comma-separated. A "
                         "change touching a ref NOT on the list FAILs, and so "
                         "does a ref on the list that did not move")
    # RED-VERIFY hooks: neuter one check so a known-bad fixture is shown to
    # pass when — and only when — that check is disabled. Tests only.
    ap.add_argument("--_disable-stale", action="store_true")
    ap.add_argument("--_disable-audit-manifest", action="store_true")
    ap.add_argument("--_disable-readme", action="store_true")
    ap.add_argument("--_disable-manifest-consistency", action="store_true")
    ap.add_argument("--_disable-stock", action="store_true")
    ap.add_argument("--_disable-order", action="store_true")
    ap.add_argument("--_disable-reviews", action="store_true")
    ap.add_argument("--claim", choices=("design", "sourcing", "both"),
                    default="both",
                    help="which of the seal's TWO claims to grade. `design` = "
                         "is the artifact correct (every gate that grades "
                         "something we control); `sourcing` = can it be "
                         "bought (J-PCBA/A-BUY + the lens order "
                         "verdicts). They are graded and exit-coded "
                         "independently because they are answered by "
                         "different authorities at different times — the "
                         "design gates at SEAL time, JLCPCB allocation at ORDER "
                         "time")
    ap.add_argument("--stock-evidence", default=None, metavar="FRESH.json",
                    help="ORDER-TIME re-grade: read the stock evidence from "
                         "HERE instead of the release's sealed "
                         "verification/. A sealed archive is immutable, so "
                         "the only honest way to re-ask the sourcing question "
                         "later is from outside it. Pair with "
                         "--claim sourcing")
    ap.add_argument("--sourcing-authority",
                    choices=("auto", "catalog-legacy", "jlc-pcba"),
                    default="auto",
                    help="order-readiness authority. catalog-legacy preserves "
                         "historical releases; auto reads the project release "
                         "contract; new contracts declare jlc-pcba")
    ap.add_argument("--pcba-evidence", default=None, metavar="RECEIPT.json",
                    help="hash-bound order-phase JLCPCB PCBA allocation "
                         "receipt; required with --sourcing-authority jlc-pcba")
    ap.add_argument("--assembly", default="",
                    help="03_src/rules/assembly.yaml (auto-discovered from "
                         "the release path) — supplies build_quantity and the "
                         "sourcing_plan the A-STOCK check grades against")
    args = ap.parse_args(argv)

    release_dir = Path(args.release_dir).resolve()
    if not release_dir.is_dir():
        print(f"FATAL: not a directory: {release_dir}", file=sys.stderr)
        return 2
    releases_root = (Path(args.releases_root).resolve()
                     if args.releases_root else release_dir.parent)
    if args.sourcing_authority == "auto":
        args.sourcing_authority = _contract_sourcing_authority(release_dir)
    if args.sourcing_authority == "jlc-pcba" and not args.pcba_evidence:
        args.pcba_evidence = str(
            release_dir / "verification/pcba_order_receipt.json")

    allow, bad_exceptions = _load_exceptions(release_dir)
    for rel in args.allow_identical:
        allow[rel] = "waived via --allow-identical"

    prior_dir = None
    bom_only = bool(args.bom_only_supersede)
    cpl_only = bool(args.cpl_only_supersede)
    legible_bom = bool(args.legible_bom_supersede)
    sourcing = bool(args.sourcing_supersede)
    value_change = bool(args.value_change_supersede)
    _modes = [args.docs_only_supersede, args.bom_only_supersede,
              args.cpl_only_supersede, args.legible_bom_supersede,
              args.sourcing_supersede, args.value_change_supersede]
    if sum(1 for m in _modes if m) > 1:
        print("FATAL: pass at most ONE of --docs-only-supersede / "
              "--bom-only-supersede / --cpl-only-supersede / "
              "--legible-bom-supersede / --sourcing-supersede / "
              "--value-change-supersede", file=sys.stderr)
        return 2
    _mode = ("bom-only" if bom_only else "cpl-only" if cpl_only
             else "legible-bom" if legible_bom
             else "sourcing" if sourcing
             else "value-change" if value_change else "docs-only")
    declared = [d.strip() for chunk in args.designators
                for d in chunk.replace(";", ",").split(",") if d.strip()]
    if declared and not value_change:
        print("FATAL: --designators only means anything with "
              "--value-change-supersede — it is the list that mode confines "
              "the BOM/CPL delta to", file=sys.stderr)
        return 2
    if value_change and not declared:
        print("FATAL: --value-change-supersede REQUIRES --designators R4,R5 — "
              "the mode's whole assertion is that the delta is confined to a "
              "DECLARED refdes list, and an empty list confines nothing",
              file=sys.stderr)
        return 2
    if any(_modes):
        prior_dir = Path(args.docs_only_supersede or args.bom_only_supersede
                         or args.cpl_only_supersede
                         or args.legible_bom_supersede
                         or args.sourcing_supersede
                         or args.value_change_supersede).resolve()
        if not prior_dir.is_dir():
            print(f"FATAL: --{_mode}-supersede "
                  f"prior release is not a directory: {prior_dir}",
                  file=sys.stderr)
            return 2

    print(f"== release-freshness: {release_dir.name} =="
          + (f" [{_mode} supersede of "
             f"{prior_dir.name}]" if prior_dir else "")
          + (f" [claim: {args.claim}]" if args.claim != "both" else ""))
    # `fails` is the DESIGN claim; `sfails` the SOURCING claim. Everything
    # above check (e) grades an artifact we control, so it is design-side.
    fails, sfails, notes = [], [], []

    if bad_exceptions:
        fails += [f"  BAD EXCEPTION: freshness_exceptions.txt lists {rel!r} "
                  f"with no reason — a waiver needs evidence"
                  for rel in bad_exceptions]

    if prior_dir is not None:
        # docs-only mode REPLACES the stale check: identity with the declared
        # prior release is asserted, not flagged.
        if not args._disable_stale:
            df, dn = check_docs_only(release_dir, prior_dir,
                                     bom_only=bom_only, cpl_only=cpl_only,
                                     legible_bom=legible_bom,
                                     sourcing=sourcing,
                                     value_change=value_change)
            fails += df
            notes += dn
            if value_change:
                vf, vn = check_value_change_delta(release_dir, prior_dir,
                                                  declared)
                fails += vf
                notes += vn
            if sourcing:
                qf, qn = check_sourcing_delta(release_dir, prior_dir)
                fails += qf
                notes += qn
            if legible_bom:
                lf, ln = check_legible_bom_delta(release_dir, prior_dir)
                fails += lf
                notes += ln
            if cpl_only:
                cf, cn = check_cpl_delta(release_dir, prior_dir)
                fails += cf
                notes += cn
            if bom_only:
                bf, bn = check_bom_delta(release_dir, prior_dir)
                fails += bf
                notes += bn
    elif not args._disable_stale:
        sf, sn = check_stale(release_dir, releases_root, allow)
        fails += sf
        notes += sn
    if not args._disable_audit_manifest:
        fails += check_audit_manifest(release_dir)
    if not args._disable_readme:
        fails += check_draft_readme(release_dir)
    if not args._disable_manifest_consistency:
        fails += check_manifest_consistency(release_dir, releases_root)
    # ---- the SOURCING claim: (e) A-STOCK, (f) A-BUY, and (g)'s order half.
    # `srcstate` is the MEASUREMENT; (f) and (g) grade the release's own
    # DECLARATIONS against it. Neutering (e) leaves it UNGRADED, never CLEAR.
    srcstate = _ungraded_sourcing("check (e) disabled")
    if not args._disable_stock:
        kf, kn, srcstate = check_stock(
            release_dir, _load_assembly(release_dir, args.assembly),
            evidence_override=args.stock_evidence)
        if args.sourcing_authority == "catalog-legacy":
            sfails += kf
        else:
            notes += ["  note: A-CATALOG advisory only: " + finding.strip()
                      for finding in kf]
        notes += kn
    if args.sourcing_authority == "jlc-pcba":
        pf, pn, srcstate = check_pcba_availability(
            release_dir, args.pcba_evidence)
        sfails += pf
        notes += pn
    if not args._disable_order:
        of, on = check_order_declaration(release_dir, srcstate)
        sfails += of
        notes += on
    if not args._disable_reviews:
        rdf, rsf, rn = check_reviews(release_dir, srcstate)
        fails += rdf
        sfails += rsf
        notes += rn

    want_design = args.claim in ("design", "both")
    want_sourcing = args.claim in ("sourcing", "both")
    for n in notes:
        print(n)
    if want_design:
        for f in fails:
            print(f)
    if want_sourcing:
        for f in sfails:
            print(f)

    # TWO CLAIMS, TWO LINES. A release may be DESIGN: PASS and
    # SOURCING: BLOCKED-1 at the same time — that is the whole point, and it
    # is the state nine successive agents had no way to record.
    status = srcstate["status"]
    n_state = len(srcstate["blocked"] or srcstate["planned"])
    label = f"{status}-{n_state}" if n_state else status
    if want_design:
        print(f"DESIGN: {'FAIL (%d finding(s))' % len(fails) if fails else 'PASS'}")
    if want_sourcing:
        print(f"SOURCING: {label}"
              + (f" + FAIL ({len(sfails)} finding(s))" if sfails else ""))
    hard = (fails if want_design else []) + (sfails if want_sourcing else [])
    if hard:
        print(f"FRESHNESS: FAIL ({len(hard)} finding(s))")
        return 1
    print("FRESHNESS: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
