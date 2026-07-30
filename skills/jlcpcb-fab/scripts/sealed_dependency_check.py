#!/usr/bin/env python3
"""M-DEPEND — a SEALED release may not depend on a mutable fact it does not carry.

usage:
  sealed_dependency_check.py PROJECT_DIR [--board STEM]
  sealed_dependency_check.py --fleet [--root REPO]
  sealed_dependency_check.py --release RELEASE_DIR
  [--ledger PATH] [--parts DIR] [--json OUT] [-v]

Exit 0 = every LCSC code in every sealed `fab/bom.csv` this project ships is
still resolvable at the grade the sealed bytes CLAIM. Exit 1 = at least one
sealed row's claim now rests on nothing the live tree can supply.

============================================================== THE INCIDENT ==

`02_parts/<MPN>/part.yaml` is the MPN AUTHORITY for EVERY release, and it lives
OUTSIDE the archive. cooksense's v1.7 work removed `02_parts/ULN2803ADWR/`
because the board legitimately no longer contains a ULN2803 (ADR-0023: the coil
driver became a TBD62083AFWG). The SEALED `cooksense-v1.6-2026-07-27` —
immutable, not one byte changed — flipped F-MPN **PASS -> FAIL** on row 56
(`C9683`). The dossier was restored and it flipped **back**. Twice, in opposite
directions, inside one session, and **the self-healing direction is the worse
half: `t1_fleet_regrade` went green on its own and no artifact anywhere recorded
that it had ever been red.** Measured with the external authorities neutralised,
**9 of 33 sealed releases failed — every release that passed F-MPN at all, four
of them LIVE and orderable.**

THE TRIGGER IS NOT ONLY A DELETION. `02_parts/MCP23017-E-SS` was **EDITED**: a
legitimate re-source moved `sourcing.lcsc` from `C506653` to `C558584` when the
old code went to stock 0, and that ONE FIELD orphaned a code SIX sealed releases
ship. The fix (57044c0) was to hand-write the old code back as a mapping-form
`alternates:` entry with the comment *"The old code MUST stay resolvable here
forever."* That sentence is a human promise with no gate behind it. This file is
the gate.

F-LEGIBLE (9f516e4) fixed the VERDICT side: a sealed release is now graded
against a map sealed INSIDE it (`verification/stock_check.csv`), so verdicts no
longer flip. M-DEPEND is the complement and it is the **M-ENTRY** half (ADR-0007:
check a fact where it ENTERS the pipeline, not where it SHOWS). F-LEGIBLE
notices at the release, hours or days later, and only for the 8 of 33 releases
that happen to carry a map. This notices at the DELETION — the one moment the
tree is still live and the author is still holding the change.

=================================== WHY IT GRADES STATE AND NOT A GIT DIFF ==

Comparing `02_parts/` against git HEAD is the obvious mechanism and it was
REJECTED on measurement, not taste:

  1. IT CANNOT SEE A DELETION THAT IS ALREADY COMMITTED, which is exactly how
     the incident happened — the removal landed in a commit before anything
     noticed. A gate blind to the committed case is a gate blind to the
     incident it was built for.
  2. IT CANNOT REACH AN ORPHAN NOBODY EVER TOUCHED. `usb-hub-3s-v3` v1.1 ships
     `C2866319` (row 30, U13) and v1.2 ships `C140903` (row 28, D5); **both
     resolve from NOTHING today**, and `07_releases/` is immutable so the
     archives can never be fixed. No diff rule reaches those.
  3. A DIFF NEEDS A REFERENCE and HEAD is not one: three sibling agents hold
     uncommitted work in `projects/` at any moment, so "differs from HEAD" is
     ambient noise, not signal.

So the graded object is the STATE: *every code in every sealed BOM resolves,
today, at the grade the sealed bytes claim.* State grading turns out to SUBSUME
the diff — a deletion and an edit both land as the same state — which is why
there is no git code in this file at all.

============================================================== THE LADDER ==

Per coded row of a sealed `fab/bom.csv`, resolved through the SAME loaders
F-MPN uses (`bom_legibility_check.MpnAuthority`, imported rather than
re-implemented — canon M-WIDTH, so the two gates cannot disagree about what the
authority says):

  GRADED       a HAND-VERIFIED authority resolves the code and names an MPN:
               `02_parts/<MPN>/part.yaml` (`sourcing.lcsc` or a mapping-form
               `alternates:` entry) or the vetted `lcsc_passives_ledger.yaml`.
               The two-path EQUALITY check F-MPN exists for is performable.
  CORROBORATED no hand-verified authority resolves it; the release's OWN sealed
               `verification/stock_check.csv` does. EXISTENCE only — JLC's
               `componentModelEn` is a catalog DESCRIPTION and is NOT the part
               number on 7 of 156 fleet rows (`436500224` for Molex
               `43650-0224`), which is precisely why F-LEGIBLE refuses to grade
               equality on it.
  ORPHAN       nothing resolves it.

And the verdict depends on WHAT THE SEALED BYTES CLAIM, because a gate may not
demand evidence for a claim the artifact never made:

  ORPHAN                          -> FAIL. The row cites a code no authority can
                                    name a part for. Existence is a claim every
                                    coded row makes.
  CORROBORATED + MPN cell FILLED  -> FAIL. The row ASSERTS a part number and no
                                    hand-verified authority can confirm it any
                                    more. This is F-MPN's NOT-RE-DERIVABLE class
                                    arriving at the moment it is still fixable.
  CORROBORATED + MPN cell BLANK   -> WAIVED, and this is the whole waiver.
  GRADED                          -> OK.

THE WAIVER IS NARROW AND STRUCTURAL, and it is the one the F-LEGIBLE row
promises: the release carries its OWN `verification/stock_check.csv` covering
that code, so existence is re-derivable from sealed bytes alone, AND the sealed
row never made an equality claim (blank MPN cell) so nothing was lost. It is
EVIDENCE, not rationale (canon M4): the map row is printed with the finding.
There is no waiver FILE, deliberately — a waiver a human writes into a project
gets copied to the next board and becomes an inherited defect (the
refdes-on-silk rule, across three boards). This one cannot be copied, because
it is a property of the archive itself.

**A BLANK MPN CELL IS NOT EXCUSED, IT IS ELSEWHERE.** F-MPN fails it
unconditionally and before any authority is consulted; M-DEPEND does not grade
it a second time (canon M-WIDTH: one home per fact). Same for a hand-verified
authority that DISAGREES with a filled cell — the fleet's 5 live instances
(`usb-hub-3s-v3` v1.5-v1.9, `SS12D07VG6 087` vs the dossier's
`SS12D07VG6-087`) are F-MPN findings. M-DEPEND REPORTS them, named and counted,
because they are the measured proof that a sealed verdict is pinned to a mutable
field — but it does not re-fail them.

`02_parts/` IS DELIBERATELY NOT MADE APPEND-ONLY. That would make the LIVE tree
a function of the ARCHIVE and force the v1.7 board that legitimately has no
ULN2803 to keep the dossier forever. This gate makes the author choose
CONSCIOUSLY between three cheap options, and every one of them is legitimate:

  (a) keep the dossier;
  (b) move the code->MPN fact to `lcsc_passives_ledger.yaml`, the live
      hand-verified home for a code no board vendors any more; or
  (c) accept the demotion where the release's own map already covers it and the
      sealed row made no equality claim — which needs no action at all.

============================================== FLEET CENSUS, 2026-07-29 ==

33 sealed releases carrying a `fab/bom.csv`; 1175 coded rows.

  8/33   carry a release-internal `verification/stock_check.csv` map
  25/33  do NOT, and being immutable never can
  25/33  depend on `02_parts/` as the SOLE resolver for at least one code
         (0 of the 8 map-carrying releases do; the split is exactly clean)
  2/33   are ALREADY BROKEN and unfixable in the archive: usb-hub-3s-v3 v1.1
         row 30 (`C2866319`, U13) and v1.2 row 28 (`C140903`, D5) resolve from
         nothing. Reported, not fixable here — the remedy is a catalog-verified
         `lcsc_passives_ledger.yaml` entry, which needs a live catalog read.
  5/33   carry a finding that exists ONLY because the tree currently says
         something (usb-hub-3s-v3 v1.5-v1.9, SW1/`C2939728`).
  0/33   sit at CORROBORATED with a FILLED MPN cell — so the second FAIL class
         costs the fleet nothing today and bites the moment a dossier leaves.

M1/M-PROV: the checker reads the SEALED BOM BYTES and the SEALED map bytes; the
authority it grades them against is the live `02_parts/` tree plus the ledger.
Nothing here is produced by `export_jlc_package.py`, so checker and checked do
not share a method.
"""
import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import bom_legibility_check as B                              # noqa: E402
import release_index as _relidx                               # noqa: E402

CHECK_ID = "M-DEPEND"

#: the grade ladder, worst first. Ordered so a numeric comparison is legible.
ORPHAN, CORROBORATED, GRADED = 0, 1, 2
LEVEL_NAME = {ORPHAN: "ORPHAN", CORROBORATED: "CORROBORATED", GRADED: "GRADED"}


class Dep:
    """One coded row of one sealed BOM, and what the live tree can still say
    about it. `claim` is what the SEALED BYTES assert — the thing a gate is
    allowed to demand evidence for."""

    __slots__ = ("release", "row", "refs", "code", "claim", "level",
                 "resolver", "resolved", "map_mpn")

    def __init__(self, release, row, refs, code, claim, level, resolver,
                 resolved, map_mpn):
        self.release, self.row, self.refs, self.code = release, row, refs, code
        self.claim, self.level = claim, level
        self.resolver, self.resolved, self.map_mpn = resolver, resolved, map_mpn

    @property
    def where(self):
        return (f"{self.release} row {self.row} "
                f"({','.join(self.refs) or '?'}) {self.code}")


def classify(auth, code, claim):
    """(level, resolver_source, resolved_mpn, map_mpn) for one code.

    The hand-verified pair is consulted FIRST and the release-carried map LAST,
    in exactly the order `MpnAuthority.resolve()` uses — the order F-LEGIBLE
    measured, where putting the map first would have manufactured 7 false
    DISAGREE failures across four sealed releases, two of them LIVE. Reusing
    that object rather than re-deriving the order is the point: a second
    ordering in a second file is the M-WIDTH failure this repo keeps paying for.
    """
    m = auth.release.get(code)
    map_mpn = m.mpn if m else ""
    for table in (auth.parts, auth.ledger):
        r = table.get(code)
        if r and r.mpn:
            return GRADED, r.source, r.mpn, map_mpn
    if map_mpn:
        return CORROBORATED, B.RELEASE_SRC, map_mpn, map_mpn
    return ORPHAN, "", "", map_mpn


def grade_release(release_dir, parts_dir, ledger=None):
    """[Dep] for one sealed release, or [] when it ships no BOM.

    The BOM is read with `bom_legibility_check.read_bom`, so the ROW NUMBERS
    M-DEPEND prints are the SAME row numbers F-MPN prints. A gate that numbers
    rows its own way sends the author to the wrong line, which is the whole
    difference between "a dossier was deleted" and "this deletion breaks
    cooksense-v1.6-2026-07-27 row 56 (C9683)".
    """
    release_dir = Path(release_dir)
    bom = None
    for name in ("bom.csv", "bom_jlc.csv"):
        if (release_dir / "fab" / name).is_file():
            bom = release_dir / "fab" / name
            break
    if bom is None:
        return []
    auth = B.MpnAuthority(parts_dir, ledger, release_dir)
    rows, _fields = B.read_bom(bom)
    out = []
    for x in rows:
        if not B.LCSC_RE.fullmatch(x.lcsc or ""):
            continue
        level, resolver, resolved, map_mpn = classify(auth, x.lcsc, x.mpn)
        out.append(Dep(release_dir.name, x.n, x.refs, x.lcsc, x.mpn,
                       level, resolver, resolved, map_mpn))
    return out


def verdicts(deps):
    """(fails, waived, disagree, ok) — the four classes, each a list of
    (Dep, message). Nothing is dropped: every Dep lands in exactly one list,
    so the printed denominator is the real one (canon M-COVER)."""
    fails, waived, disagree, ok = [], [], [], []
    for d in deps:
        if d.level == ORPHAN:
            fails.append((d, (
                f"{CHECK_ID} ORPHAN {d.where}: the code this sealed row cites "
                f"resolves from NO authority — not `02_parts/<MPN>/part.yaml` "
                f"(`sourcing.lcsc` or a mapping-form `alternates:` entry), not "
                f"`lcsc_passives_ledger.yaml`, and this release carries no "
                f"`{B.RELEASE_SRC}` entry for it either. The release is "
                f"IMMUTABLE, so the remedy is in the LIVE tree: restore the "
                f"dossier, or add a catalog-verified ledger entry")))
        elif d.level == CORROBORATED and d.claim:
            fails.append((d, (
                f"{CHECK_ID} UNPINNED {d.where}: the sealed row ASSERTS MPN "
                f"'{d.claim}' and NO hand-verified authority resolves that code "
                f"any more. Only the release's own {B.RELEASE_SRC} still names "
                f"it ('{d.map_mpn}'), and that column is JLC's catalog "
                f"DESCRIPTION — an EXISTENCE record, wrong as an MPN on 7 of "
                f"156 fleet rows — so the two-path agreement F-MPN exists for "
                f"can no longer be performed on immutable bytes. Keep the "
                f"dossier, or move the code->MPN fact to "
                f"`lcsc_passives_ledger.yaml`")))
        elif d.level == CORROBORATED:
            waived.append((d, (
                f"{CHECK_ID} WAIVED {d.where}: no hand-verified authority "
                f"resolves this code, but the release carries its own "
                f"{B.RELEASE_SRC} naming it '{d.map_mpn}' (evidence, recorded "
                f"at the seal from JLC's own catalog) and the sealed MPN cell "
                f"is BLANK, so the row never made an equality claim to lose. "
                f"Existence is re-derivable from the shipped bytes. (The blank "
                f"cell itself is an unconditional F-MPN FAIL — one home per "
                f"fact, canon M-WIDTH)")))
        elif d.claim and d.resolved and d.claim != d.resolved:
            disagree.append((d, (
                f"{CHECK_ID} PINNED-AND-DISAGREEING {d.where}: sealed cell says "
                f"'{d.claim}', the live {d.resolver} says '{d.resolved}'. This "
                f"finding EXISTS ONLY BECAUSE THE TREE CURRENTLY SAYS SO and "
                f"vanishes if it moves — the measured proof that a sealed "
                f"verdict is pinned to a mutable field. It is F-MPN's DISAGREE "
                f"and is NOT re-failed here (canon M-WIDTH)")))
        else:
            ok.append((d, ""))
    return fails, waived, disagree, ok


def sole_dependency(deps):
    """[Dep] graded ONLY because `02_parts/` is still there — the fragility
    census. Not a defect: the argument for the gate. A dossier named here is
    load-bearing for a sealed release, and a `git rm` on it produces an
    ORPHAN or an UNPINNED finding above."""
    return [d for d in deps
            if d.level == GRADED and d.resolver.startswith("02_parts/")
            and not d.map_mpn]


# ================================================================ targets ===
def releases_of(project, board=None):
    """[(release_dir, parts_dir)] for one project.

    Release SELECTION comes from `release_index` (canon M-WIDTH: the ONE home
    for "which release belongs to which board"), but M-DEPEND grades ALL of a
    project's sealed releases, not just the newest. That is the point — the
    victims of a deletion are the OLD releases, and v1.6 does not stop being
    orderable because v1.7 exists. An UNATTRIBUTABLE set is a FAIL upstream in
    policy_audit; here a board filter that resolves nothing falls back to every
    release directory, because grading them all is never wrong for this check.
    """
    project = Path(project)
    rel = project / "07_releases"
    if not rel.is_dir():
        return []
    parts = project / "02_parts"
    parts = parts if parts.is_dir() else None
    dirs = None
    if board:
        try:
            dirs = [Path(p) for p in _relidx.releases_for_board(project, board)]
        except Exception:                                     # noqa: BLE001
            dirs = None
    if not dirs:
        dirs = sorted(p for p in rel.glob("*") if p.is_dir())
    return [(d, parts) for d in dirs]


def fleet_targets(root):
    out = []
    for proj in sorted((Path(root) / "projects").glob("*")):
        if proj.is_dir():
            out.extend(releases_of(proj))
    return out


# =================================================================== main ===
def run(targets, ledger=None, verbose=False, out=sys.stdout):
    deps = []
    for rel, parts in targets:
        deps.extend(grade_release(rel, parts, ledger))
    fails, waived, disagree, ok = verdicts(deps)
    sole = sole_dependency(deps)
    rels = sorted({d.release for d in deps})

    for _d, msg in fails:
        print(msg, file=out)
    for _d, msg in disagree:
        print(msg, file=out)
    if verbose:
        for _d, msg in waived:
            print(msg, file=out)

    n = len(deps)
    if not n:
        # M-COVER: a gate that PASSES while grading nothing is the failure this
        # repo has paid for repeatedly (A-AMP graded 10 of 57; leg C dropped 87
        # of 673 and printed PASS). Sealed releases were handed to this run and
        # not one coded row came out of them, so something is wrong with the
        # BOMs or the reader — never a clean bill.
        print(f"{CHECK_ID} coverage: 0 coded row(s) from {len(targets)} sealed "
              f"release target(s) — a gate may not pass while grading NOTHING "
              f"(canon M-COVER). Either the BOMs carry no LCSC column or the "
              f"reader lost them", file=out)
        print(f"{CHECK_ID}: FAIL (0 rows graded)", file=out)
        empty = Dep("(all targets)", 0, [], "", "", ORPHAN, "", "", "")
        return [(empty, f"{CHECK_ID}: graded 0 coded rows")], [], [], [], []
    print(f"\n{CHECK_ID} coverage: {n} coded row(s) across {len(rels)} sealed "
          f"release(s) — {len(ok)} GRADED, {len(waived)} WAIVED "
          f"(release-internal map, blank cell), {len(disagree)} "
          f"PINNED-AND-DISAGREEING (F-MPN's), {len(fails)} FAIL", file=out)
    print(f"{CHECK_ID} fragility: {len(sole)} row(s) across "
          f"{len({d.release for d in sole})} release(s) are GRADED only because "
          f"a `02_parts/` dossier is still in the tree, with no "
          f"release-internal map to fall back on", file=out)
    if sole and verbose:
        for d in sorted(sole, key=lambda x: (x.release, x.row)):
            print(f"  SOLE {d.where} <- {d.resolver}", file=out)
    print(f"{CHECK_ID}: {'FAIL' if fails else 'PASS'} "
          f"({len(fails)} finding(s))", file=out)
    return fails, waived, disagree, ok, sole


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("project", nargs="?", default="")
    ap.add_argument("--board", default="", help="04_kicad stem of a "
                    "multi-board project (release scope)")
    ap.add_argument("--release", default="", help="grade ONE sealed release dir")
    ap.add_argument("--parts", default="", help="02_parts override (used with "
                    "--release; default is the release's own project)")
    ap.add_argument("--ledger", default="", help="lcsc_passives_ledger.yaml "
                    "override")
    ap.add_argument("--fleet", action="store_true", help="every project")
    ap.add_argument("--root", default="", help="repo root for --fleet")
    ap.add_argument("--json", default="", help="machine-readable sidecar")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="also print WAIVED rows and the fragility roster")
    a = ap.parse_args(argv)

    if a.fleet:
        root = Path(a.root) if a.root else _HERE.parent.parent.parent
        targets = fleet_targets(root)
    elif a.release:
        rel = Path(a.release).resolve()
        parts = Path(a.parts) if a.parts else rel.parent.parent / "02_parts"
        targets = [(rel, parts if parts.is_dir() else None)]
    elif a.project:
        targets = releases_of(Path(a.project).resolve(), a.board or None)
    else:
        ap.error("give a PROJECT_DIR, --release DIR, or --fleet")

    if not targets:
        print(f"{CHECK_ID}: no sealed release to grade")
        return 0
    fails, waived, disagree, ok, sole = run(
        targets, a.ledger or None, a.verbose)
    if a.json:
        Path(a.json).write_text(json.dumps({
            "check": CHECK_ID,
            "verdict": "FAIL" if fails else "PASS",
            "coverage": {"rows": len(ok) + len(waived) + len(disagree)
                         + len(fails), "graded": len(ok), "waived": len(waived),
                         "disagree": len(disagree), "fail": len(fails)},
            "fails": [{"release": d.release, "row": d.row, "code": d.code,
                       "refs": d.refs, "claim": d.claim,
                       "level": LEVEL_NAME[d.level], "why": m}
                      for d, m in fails],
            "disagree": [{"release": d.release, "row": d.row, "code": d.code,
                          "claim": d.claim, "resolved": d.resolved,
                          "resolver": d.resolver} for d, _m in disagree],
            "sole_dependency": [{"release": d.release, "row": d.row,
                                 "code": d.code, "resolver": d.resolver}
                                for d in sole],
        }, indent=1) + "\n", encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
