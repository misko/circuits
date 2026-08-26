#!/usr/bin/env python3
"""t1_sealed_dependency.py — canon M-DEPEND.

A SEALED release may not depend on a mutable fact it does not carry.

THE INCIDENT. `02_parts/<MPN>/part.yaml` is the MPN authority for EVERY release
and it lives OUTSIDE the archive. cooksense's v1.7 work removed
`02_parts/ULN2803ADWR/` — legitimately, ADR-0023 replaced the coil driver — and
the SEALED `cooksense-v1.6-2026-07-27`, immutable and byte-unchanged, flipped
F-MPN PASS -> FAIL on row 56 (`C9683`); restoring the dossier flipped it back.
Twice in opposite directions in one session, and the self-healing direction is
the worse half: `t1_fleet_regrade` went green on its own with nothing recording
that it had been red. Measured with the external authorities neutralised, 9 of
33 sealed releases failed — every release that passed F-MPN at all, four LIVE.

THE TRIGGER IS NOT ONLY A DELETION. `02_parts/MCP23017-E-SS` was EDITED
(`sourcing.lcsc` C506653 -> C558584 when the old code hit stock 0), orphaning a
code SIX sealed releases ship. Commit 57044c0 fixed it by hand and wrote *"The
old code MUST stay resolvable here forever"* into the dossier — a human promise
with no gate. Both halves have a known-bad below and they are the REAL edits,
not synthetics.

WHY EVERY FIXTURE IS A SCRATCH COPY. `07_releases/` is immutable and three
sibling agents hold live work in `projects/`, so each known-bad copies
`02_parts/` + `07_releases/` into a tmpdir and breaks the COPY. Nothing here
writes to a project tree.

RED-VERIFICATION, and for a NEW gate the pre-fix state is "the gate does not
exist" — so what must be measured is that NOTHING ELSE IN THE REPO FAILS on the
fixture. That measurement is recorded in each known-bad docstring with the real
pre-fix output: F-LEGIBLE, the gate closest to this fact, exits **0** on the
sealed v1.6 with the dossier deleted, demoting row 56 to
`NOT-REDERIVABLE-FROM-SHIPPED-BYTES` and saying in as many words that this "does
not say OK and does not say FAIL". That demotion on immutable bytes, caused by a
live-tree edit, is precisely what M-DEPEND fails.
"""
import csv
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, check, contains,  # noqa: E402
                     eq, main, must_fail, must_pass, not_contains, run, test,
                     tmpdir)

sys.path.insert(0, str(FAB_SCRIPTS))
from sealed_dependency_check import (CORROBORATED, GRADED,  # noqa: E402
                                     ORPHAN, classify, grade_release,
                                     sole_dependency, verdicts)
import bom_legibility_check as B                                # noqa: E402

TOOL = FAB_SCRIPTS / "sealed_dependency_check.py"
LEGIBILITY = FAB_SCRIPTS / "bom_legibility_check.py"

COOKSENSE = ROOT / "archived_projects" / "smc0985-cooksense"
USB = ROOT / "projects" / "usb-hub-3s-v3"

#: the incident's dossier and the code six sealed cooksense releases ship
INCIDENT_DOSSIER = "ULN2803ADWR"
INCIDENT_CODE = "C9683"
#: the release the incident was MEASURED on, and its row number
V16 = "cooksense-v1.6-2026-07-27"
V16_ROW = 56


def scratch(project=COOKSENSE):
    """A writable copy of just the two directories M-DEPEND reads: the sealed
    archive and the live MPN authority. Copying the whole project would drag in
    a 195-footprint board for no reason, and copying the archive is what makes
    breaking it legal at all."""
    d = tmpdir("mdep_") / "proj"
    d.mkdir(parents=True)
    for name in ("02_parts", "07_releases"):
        shutil.copytree(project / name, d / name)
    for p in d.rglob("*"):
        p.chmod(p.stat().st_mode | 0o200)
    return d


# ======================================================= the ladder, in unit ==
@test("the ladder ranks hand-verified above release-carried above nothing")
def t_ladder():
    """GRADED > CORROBORATED > ORPHAN, and the ORDER is the measured one:
    F-LEGIBLE proved that consulting the release map FIRST manufactures 7 false
    DISAGREE failures across four sealed releases (two LIVE) because JLC's
    `componentModelEn` is `436500224` where Molex's part number is `43650-0224`.
    M-DEPEND imports `MpnAuthority` rather than re-deriving that order — a
    second ordering in a second file is the M-WIDTH failure this repo pays for.
    """
    rel = COOKSENSE / "07_releases" / V16
    auth = B.MpnAuthority(COOKSENSE / "02_parts", None, rel)
    lvl, src, mpn, map_mpn = classify(auth, INCIDENT_CODE, "ULN2803ADWR")
    eq(lvl, GRADED, "C9683 with its dossier present")
    contains(src, "02_parts/ULN2803ADWR", "the resolver named")
    eq(mpn, "ULN2803ADWR", "resolved MPN")
    # the map also carries it; that is what makes the WAIVED class reachable
    eq(map_mpn, "ULN2803ADWR", "the release-internal map entry")
    # a code nothing knows
    lvl, src, mpn, map_mpn = classify(auth, "C999999999", "WHATEVER")
    eq(lvl, ORPHAN, "an unknown code")
    eq((src, mpn, map_mpn), ("", "", ""), "an ORPHAN names no resolver")


@test("the fragility census names the dossiers a sealed release leans on")
def t_fragility_census():
    """The argument FOR the gate, and it is a measurement, not a defect. A row
    listed here is GRADED only because a `02_parts/` dossier is still in the
    tree AND the release carries no map to fall back on — i.e. one `git rm`
    from an M-DEPEND finding. Measured 2026-07-29 over the fleet: 539 rows
    across 25 of 33 sealed releases; the 8 map-carrying releases contribute
    ZERO, so the split is exactly clean."""
    deps = grade_release(COOKSENSE / "07_releases" / "cooksense-v1.0-2026-07-23",
                         COOKSENSE / "02_parts")
    check(deps, "cooksense v1.0 graded no rows")
    sole = sole_dependency(deps)
    check(len(sole) >= 20,
          f"cooksense v1.0 leans on only {len(sole)} dossier(s) — it carries no "
          f"release-internal map, so most of its coded rows must be sole-"
          f"dependent; the census has gone quiet")
    check(all(d.resolver.startswith("02_parts/") for d in sole),
          "a sole-dependency row named a resolver that is not a dossier")
    # and a release WITH a map contributes nothing to the census
    withmap = grade_release(COOKSENSE / "07_releases" / V16,
                            COOKSENSE / "02_parts")
    eq(sole_dependency(withmap), [], "a map-carrying release's fragility set")


# ================================================================== clean ===
@test("M-DEPEND PASSES the real smc0985-cooksense project as it stands")
def t_cooksense_passes():
    """The in-flight seal's tree. Both dossiers the incident touched were
    restored, so every one of cooksense's 376 coded rows across 9 sealed
    releases must be GRADED by a hand-verified authority. This is the gate
    saying the tree is currently CORRECT — the other half of discrimination,
    without which a gate that fires on every deletion gets waived into
    uselessness inside a week."""
    r = must_pass(run([KPY, TOOL, str(COOKSENSE)]),
                  "M-DEPEND on smc0985-cooksense")
    contains(r.out, "M-DEPEND: PASS", "the verdict")
    contains(r.out, "376 coded row(s) across 9 sealed release(s)",
             "the row and release denominators")
    not_contains(r.out, "ORPHAN", "a clean project's output")
    not_contains(r.out, "UNPINNED", "a clean project's output")


@test("a deletion that NO sealed BOM depends on PASSES")
def t_safe_deletion_passes():
    """THE DISCRIMINATION THAT KEEPS THE GATE USABLE. `02_parts/` is deliberately
    NOT made append-only (the cost the M-SHIP agent rejected): that would make
    the LIVE tree a function of the ARCHIVE and force the v1.7 board which
    legitimately has no ULN2803 to keep the dossier forever. So a dossier whose
    `sourcing.lcsc` appears in no sealed BOM may be deleted freely.

    `SN74HC138DR` is a live-tree candidate whose primary and alternate LCSC
    codes are absent from every sealed cooksense BOM. The fixture proves that
    absence from the copied bytes before deleting it, so a future release that
    adopts the part makes the fixture red instead of silently turning this into
    another dependency incident."""
    d = scratch()
    safe = d / "02_parts" / "SN74HC138DR"
    y = yaml.safe_load((safe / "part.yaml").read_text(encoding="utf-8-sig"))
    sourcing = y.get("sourcing") or {}
    codes = {str(sourcing.get("lcsc") or "")}
    for alt in sourcing.get("alternates") or []:
        codes.add(str(alt.get("lcsc") if isinstance(alt, dict) else alt))
    codes.discard("")
    sealed_codes = set()
    for bom in d.glob("07_releases/*/fab/bom.csv"):
        with bom.open(encoding="utf-8-sig", newline="") as stream:
            sealed_codes.update((row.get("LCSC") or "").strip()
                                for row in csv.DictReader(stream))
    check(codes and codes.isdisjoint(sealed_codes),
          "SN74HC138DR is no longer a safe-deletion fixture: its codes are "
          f"{sorted(codes & sealed_codes)} in a sealed BOM")
    shutil.rmtree(safe)
    r = must_pass(run([KPY, TOOL, str(d)]),
                  "deleting a dossier no sealed BOM cites")
    contains(r.out, "M-DEPEND: PASS", "the verdict")


# ============================================================== known-bad ===
@test("THE INCIDENT: deleting 02_parts/ULN2803ADWR names cooksense-v1.6 row 56 "
      "(C9683)", kind="known_bad")
def t_the_incident():
    """The real deletion, on a scratch copy of the real archive.

    PRE-FIX MEASUREMENT (2026-07-29, the state before this gate existed).
    F-LEGIBLE — the gate that owns this fact and the closest thing to a
    predecessor — was run against the SAME scratch v1.6 with the dossier
    deleted and exited **0**:

        UNGRADED F-MPN row 56 (U_ULNA,U_ULNB): LCSC C9683 resolves from NO
        hand-verified authority; the release's OWN sealed
        verification/stock_check.csv ... CORROBORATES ... and AGREES with it
        character for character
        F-LEGIBLE NOT FULLY GRADED [NOT-REDERIVABLE-FROM-SHIPPED-BYTES]: 1
        row(s) could not be cross-checked ..., 55 check(s) passed, 0 defects
        found ... it does not say OK and it does not say FAIL
        rc=0

    So on the pre-fix tree the deletion silently DEMOTED a sealed row from a
    two-path equality grade to existence-only corroboration on immutable bytes,
    and nothing anywhere blocked. That demotion is the finding.

    WHY THE MAP DOES NOT WAIVE THIS ROW, decided on measurement and not on the
    obvious reading. v1.6 does carry `verification/stock_check.csv` and it does
    name C9683 as `ULN2803ADWR`, matching the sealed cell character for
    character — so "the release carries its own map" looks like a complete
    substitute for the dossier. It is not: that column is JLC's
    `componentModelEn`, a catalog DESCRIPTION, and F-LEGIBLE measured it WRONG
    AS AN MPN on 7 of 156 fleet rows, which is exactly why it consults it LAST
    and as an EXISTENCE authority only. An existence authority cannot carry an
    equality claim. So the map waives the ORPHAN class and never the equality
    class — see `t_the_map_waives_a_row_that_claims_nothing` for the half it
    DOES waive.
    """
    d = scratch()
    shutil.rmtree(d / "02_parts" / INCIDENT_DOSSIER)
    r = must_fail(run([KPY, TOOL, str(d)]),
                  "deleting the ULN2803ADWR dossier")
    # THE RELEASE AND THE ROW, not just the file: "a dossier was deleted" sends
    # the author hunting; this names the line.
    contains(r.out, f"{V16} row {V16_ROW}", "the release and row named")
    contains(r.out, INCIDENT_CODE, "the LCSC code named")
    contains(r.out, "U_ULNA,U_ULNB", "the refdes named")
    contains(r.out, "UNPINNED", "the finding class")
    # the older map-less releases lose the code ENTIRELY, which is the ORPHAN
    # half of the same deletion
    contains(r.out, "ORPHAN cooksense-v1.0-2026-07-23", "the map-less releases")
    contains(r.out, "ORPHAN cooksense-v1.1-2026-07-24", "the map-less releases")


@test("THE EDIT: an `alternates:` re-source that drops the shipped code names "
      "cooksense-v1.6 row 39 (C506653)", kind="known_bad")
def t_the_edit():
    """THE TRIGGER IS NOT ONLY A DELETION, and this is the fleet's own instance.

    `02_parts/MCP23017-E-SS` was re-sourced 2026-07-29 — `sourcing.lcsc` moved
    C506653 -> C558584 because C506653 read stock 0 on two independent live
    reads. Six sealed releases ship C506653. Commit 57044c0 repaired it by
    rewriting the dossier's `alternates:` from the BARE form
    (`[C506653, C47023]`, which `load_part_mpns` resolves to no MPN) to the
    mapping form, and left this comment in the file:

        # The old code MUST stay resolvable here forever.

    That is a human promise with no machine behind it. This fixture reverts
    exactly that one field to the bare form — the state the tree was actually in
    — and requires M-DEPEND to name what it costs.

    PRE-FIX MEASUREMENT (2026-07-29, measured on this exact fixture): F-LEGIBLE
    against the scratch v1.6 with the bare form restored exits **0**:

        UNGRADED F-MPN row 39 (U_EXP): LCSC C506653 resolves from NO
        hand-verified authority; the release's OWN sealed
        verification/stock_check.csv ... CORROBORATES ... The row ships
        'MCP23017-E/SS'. Existence is re-derivable from the shipped bytes; the
        two-path equality check is NOT
        F-LEGIBLE NOT FULLY GRADED [NOT-REDERIVABLE-FROM-SHIPPED-BYTES]: 1
        row(s) could not be cross-checked ..., 55 check(s) passed, 0 defects
        found
        rc=0

    Nothing gated it, which is why the hand-written promise was necessary.

    NOTE the finding is NOT a DISAGREE: `MpnAuthority` still knows the code as a
    BARE alternate, so `resolve()` correctly returns None rather than inventing
    the parent's MPN (C47023 is `MCP23017-E/SO`, a SOIC-28W part, not the
    SSOP-28 the dossier is about). M-DEPEND therefore sees the same thing the
    author would: the code names a dossier that declares no part number for it.
    """
    d = scratch()
    y = d / "02_parts" / "MCP23017-E-SS" / "part.yaml"
    text = y.read_text(encoding="utf-8-sig")
    old = ("  alternates:\n"
           "    - {lcsc: C506653, mpn: MCP23017-E/SS}")
    check(old in text,
          "the mapping-form alternates block is gone from MCP23017-E-SS — this "
          "fixture reverts a specific repair and can no longer find it")
    head, _, tail = text.partition(old)
    # drop the two mapping lines, restore the bare list commit 57044c0 replaced
    tail = tail.split("\n", 2)[2]
    y.write_text(head + "  alternates: [C506653, C47023]\n" + tail,
                 encoding="utf-8")

    r = must_fail(run([KPY, TOOL, str(d)]),
                  "reverting the MCP23017-E-SS alternates to the bare form")
    contains(r.out, f"{V16} row 39", "the release and row named")
    contains(r.out, "C506653", "the orphaned code named")
    contains(r.out, "U_EXP", "the refdes named")
    contains(r.out, "ORPHAN cooksense-v1.0-2026-07-23", "the map-less releases")


@test("the REAL fleet: usb-hub-3s-v3 v1.1/v1.2 ship codes that resolve from "
      "NOTHING", kind="known_bad")
def t_fleet_already_broken():
    """THE CASE A DIFF RULE CAN NEVER REACH, and the reason this gate grades
    STATE rather than a git diff against HEAD.

    Nobody deleted anything recently: `usb-hub-3s-v3` v1.1 row 30 (U13,
    `C2866319`) and v1.2 row 28 (D5, `C140903`) resolve from no dossier, no
    ledger entry, and no release-internal map — TODAY, on the unmodified tree.
    `07_releases/` is immutable so the archives can never be fixed; the remedy
    is a catalog-verified `lcsc_passives_ledger.yaml` entry in the LIVE tree,
    which needs a live catalog read and is filed rather than faked here.

    This fixture is UNSYNTHETIC and it is the denominator's teeth: 2 of 33
    sealed releases are already broken this way. A HEAD-diff gate reports clean
    on all of it.

    PRE-FIX MEASUREMENT: nothing in the repo names these two rows as a defect.
    `policy_audit projects/usb-hub-3s-v3 --skip-drc` on 2026-07-29 reported
    `FAIL=3` — P-ADJ-PAIR, P-ADJ-UNREACHED, P-SILK-OWN — and no MPN-resolution
    finding at all; F-LEGIBLE grades the LIVE release (v1.12), not v1.1/v1.2.
    """
    r = must_fail(run([KPY, TOOL, str(USB)]), "M-DEPEND on usb-hub-3s-v3")
    contains(r.out, "ORPHAN v1.1-2026-07-23 row 30 (U13) C2866319",
             "the v1.1 orphan, named to the row")
    contains(r.out, "ORPHAN v1.2-2026-07-23 row 28 (D5) C140903",
             "the v1.2 orphan, named to the row")
    contains(r.out, "restore the dossier, or add a catalog-verified ledger "
                    "entry", "the remedy, which is in the LIVE tree")


@test("a gate handed sealed releases and grading ZERO rows FAILS",
      kind="known_bad")
def t_vacuous_run_fails():
    """M-COVER. A checker that passes while grading nothing is the failure this
    repo has paid for over and over: A-AMP graded 10 of 57 declared currents,
    leg C dropped 87 of 673 R/C rows and printed PASS. So a run handed real
    release directories that extracts no coded row FAILS rather than reporting
    a clean bill.

    PRE-FIX: written with the guard removed, this fixture exits 0 with
    `M-DEPEND coverage: 0 coded row(s) ... M-DEPEND: PASS` — verified by
    deleting the `if not n:` block, observing the pass, and restoring it."""
    d = scratch()
    for bom in (d / "07_releases").glob("*/fab/bom.csv"):
        bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n",
                       encoding="utf-8")
    r = must_fail(run([KPY, TOOL, str(d)]), "a run that grades no rows")
    contains(r.out, "may not pass while grading NOTHING", "the M-COVER refusal")


# ================================================== the waiver, and only it ==
@test("the map waives a row that never CLAIMED an MPN, and only that row")
def t_the_map_waives_a_row_that_claims_nothing():
    """THE WHOLE WAIVER, and it is structural — there is no waiver FILE, because
    a waiver a human writes into a project gets copied to the next board and
    becomes an inherited defect (the refdes-on-silk rule, across three boards).

    Same deletion as `t_the_incident`. cooksense v1.3/v1.4 also ship C9683, also
    carry a release-internal map — and their sealed MPN CELL IS BLANK. A blank
    cell makes no equality claim, so nothing was lost when the dossier left:
    existence is re-derivable from the shipped bytes, and the map row is printed
    as the evidence (canon M4). v1.5/v1.6 ship `ULN2803ADWR` in that cell and
    are NOT waived.

    The blank cell is itself an unconditional F-MPN FAIL, graded before any
    authority is consulted. M-DEPEND does not re-grade it — one home per fact
    (canon M-WIDTH) — and says so in the waiver line.
    """
    d = scratch()
    shutil.rmtree(d / "02_parts" / INCIDENT_DOSSIER)
    r = run([KPY, TOOL, str(d), "-v"])
    check(r.rc != 0, "the deletion should still FAIL on v1.5/v1.6")
    contains(r.out, "WAIVED cooksense-v1.3-2026-07-26", "the blank-cell waiver")
    contains(r.out, "WAIVED cooksense-v1.4-2026-07-26", "the blank-cell waiver")
    contains(r.out, "never made an equality claim to lose", "the evidence")
    # and the waived releases are NOT in the FAIL set
    fails = [l for l in r.out.splitlines()
             if l.startswith(("M-DEPEND ORPHAN", "M-DEPEND UNPINNED"))]
    check(not any("v1.3-2026-07-26" in l or "v1.4-2026-07-26" in l
                  for l in fails),
          f"a map-covered blank-cell row was FAILED, not waived:\n"
          + "\n".join(fails))
    eq(len(fails), 4, "the fail set (v1.0/v1.1 ORPHAN + v1.5/v1.6 UNPINNED)")


@test("a DISAGREE is reported and NOT re-failed — F-MPN owns equality")
def t_disagree_is_reported_not_refailed():
    """The 5 releases that carry a finding existing ONLY because the tree
    currently says something: `usb-hub-3s-v3` v1.5-v1.9 ship SW1 as
    `SS12D07VG6 087` where `02_parts/SS12D07VG6-087` says `SS12D07VG6-087`.
    Move the dossier and the finding vanishes — which is the measured proof
    that a sealed verdict is pinned to a mutable field, and the reason
    M-DEPEND exists.

    It is F-MPN's DISAGREE, so M-DEPEND REPORTS it (named, counted, with the
    denominator) and does NOT fail it a second time. Two gates failing one fact
    means two places to fix and two places to drift (canon M-WIDTH). The proof
    that the report is not decoration: the 5 rows are present in the output and
    absent from the FAIL set."""
    r = run([KPY, TOOL, str(USB)])
    contains(r.out, "PINNED-AND-DISAGREEING v1.5-2026-07-25 row 31 (SW1) "
                    "C2939728", "the drifted row, named to the line")
    contains(r.out, "5 PINNED-AND-DISAGREEING", "counted with the denominator")
    fails = [l for l in r.out.splitlines()
             if l.startswith(("M-DEPEND ORPHAN", "M-DEPEND UNPINNED"))]
    eq(len(fails), 2, "usb-hub's FAIL set is the two orphans and nothing else")


if __name__ == "__main__":
    sys.exit(main())
