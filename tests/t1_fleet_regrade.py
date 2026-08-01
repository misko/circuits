#!/usr/bin/env python3
"""The regrade: run TODAY'S gates against EVERY sealed release.

Some defects were always wrong. Others BECOME wrong, and no amount of shifting
left catches those.

interposer v1.0 sealed 2026-07-24 with `J_KEY_MATRIX` at CPL rotation 90.0,
from name-DB rule `^JST_GH_SM,180`. That rule was REFUTED on 2026-07-25 — the
day after. The release was correct by the knowledge of its day and became a P0
overnight, silently, because the pad array is symmetric about its own centre:
at 180 degrees every pad still lands on a pad and the part solders perfectly
while pin1<->pin10 swap reverses the whole ten-line keypad ribbon.

And its `verification/policy_audit.md` has NO A-POP/A-POS/A-ROT/A-POL/A-BODY/
A-STOCK row AT ALL — sealed during the days that family was landing, never
re-graded. An absent verdict is not a pass; that is the `graded_by:` hole this
tool reports.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_fail,  # noqa: E402
                     must_pass, not_contains, run, test, tmpdir)

TOOL = ROOT / "skills/kicad-pcb/scripts/fleet_regrade.py"


@test("regrade_reports_the_never_graded_hole", kind="known_bad")
def t_reports_the_never_graded_hole():
    """THE INCIDENT. The interposer must be reported as never graded by the
    ASSEMBLY family — the specific hole every one of its P0s lives in."""
    r = must_fail(run([KPY, TOOL, "--project", "smc0985-cooksense"]),
                  "regrade over cooksense")
    contains(r.out, "interposer-v1.0", "the interposer is listed")
    contains(r.out, "ASSEMBLY", "its never-graded families are named")
    contains(r.out, "NEVER GRADED", "the summary names the hole class")


@test("regrade_declares_its_own_coverage")
def t_declares_its_own_coverage():
    """Canon M-COVER applied to the regrade itself: a fleet sweep that
    silently skipped what it could not run would reproduce, at fleet scale,
    exactly the defect it exists to find."""
    r = run([KPY, TOOL, "--project", "crow-mic-pod-v2"])
    contains(r.out, "coverage:", "the regrade reports N/M releases")
    contains(r.out, "sealed release(s) regraded", "with the denominator named")


@test("regrade_separates_superseded_history_from_live_defects")
def t_separates_superseded_from_live():
    """A FAIL on a release carrying SUPERSEDED.md is history. Counting it as a
    live defect would bury the two that actually block an order under 20 that
    do not — a report nobody reads is a gate that cannot fail."""
    r = run([KPY, TOOL, "--project", "usb-hub-3s-v3"])
    contains(r.out, "SUPERSEDED.md", "the distinction is stated")
    contains(r.out, "history, not a live defect", "and its meaning is explicit")


@test("regrade_retires_the_pour_defect_without_erasing_it")
def t_retires_the_pour_defect():
    """UPDATED 2026-07-27, when v1.9 sealed. This test used to assert that
    usb-hub v1.8 shows as a LIVE F-PAYLOAD failure, on the stated premise "no
    successor exists yet". v1.9-2026-07-27 IS that successor: it restores the
    copper pour (F-PAYLOAD OK, 5 checks) and v1.8 gained the SUPERSEDED.md the
    07_releases contract permits exactly once. The old premise is now false BY
    DESIGN, so the assertion had to move rather than be deleted.

    What must still hold, and is what this now checks:
      1. the v1.8 defect is STILL NAMED, with its reason. A retired defect that
         vanishes from the report is a report that cannot be audited later.
      2. it is marked as superseded HISTORY, not counted as a live blocker.
      3. the successor is LIVE and does NOT fail F-PAYLOAD — otherwise the fix
         did not take and the regrade would be agreeing with a broken release.

    The RED fixture for F-POUR is NOT lost: t1_fab_payload.py pins the sealed,
    immutable v1.8 directory itself (`V18`) and asserts the gate reports
    "NO POUR" on it. That is the permanent proof the checker can fail, and it
    lives with the checker rather than here.

    AMENDED LATER THE SAME DAY (ADR-0006), for the reason its sibling
    `t_confirms_clean_boards` was amended, and discovered the same way — by
    going RED rather than by anyone predicting it. This test asserted a blanket
    `"FAIL" not in v19`. `F-LEGIBLE` was minted HOURS AFTER v1.9 sealed and
    fails it on F-ENCODE (the BOM carries 'Omega' with no UTF-8 byte-order-mark,
    so a cp936-defaulting reader renders it as a CJK character). That failure is
    CORRECT and must not be suppressed: 07_releases is immutable, so v1.9 cannot
    be retro-fixed, and the honest record is that the fleet's newest release
    already carries a known adopted-forward gap.

    The blanket assertion was ALSO the weaker test. It could not distinguish
    "the pour fix did not take" — the thing this test exists to catch — from
    "a gate invented afterwards found something else". Per-gate can:
      * F-PAYLOAD must PASS. That is the pour, the whole reason v1.9 exists.
      * F-LEGIBLE is pinned FAIL. When v1.10 fixes the encoding this test goes
        RED and must be updated deliberately — an adopted-forward gap that
        silently heals is one nobody records having closed.

    AND IT DID GO RED, on 2026-07-27, exactly as written. **v1.10 closed the
    gap** — a BOM-legibility supersede, no copper change — so v1.9 is now
    superseded and F-LEGIBLE PASSES on the live release. This update is the
    "deliberately" the sentence above asked for, and it is why the pin was
    worth having: the hand-off is recorded rather than silently absorbed.

    The assertions now run on BOTH rows, which is stronger than either alone:
      * v1.9 must read SUPERSEDED and must still show its F-LEGIBLE FAIL. The
        adopted-forward gap is HISTORY, not erased — a sealed release is never
        retro-fixed, and a report that forgets what was wrong with it cannot be
        audited later. This is the same property the v1.8 NO-POUR row carries.
      * v1.10 must be LIVE, and must PASS F-PAYLOAD **and** F-LEGIBLE. The pour
        has to survive the supersede (the whole risk of touching this board
        again), and the legibility fix has to be real.

    AMENDED AGAIN 2026-07-27, and this time NOT because a gate found something:
    **v1.11** superseded v1.10 for a reason no gate in this repo can see. JLC's
    UPLOADER rejected the v1.10 BOM — "10 shortfall" on C25744, the 10k 0402 at
    R28/R29 — while `jlc_stock_check` had PASSED that exact line at the v1.10
    seal reading `stock: 291`. The part was substituted for C60490 (electrically
    identical, catalog `describe` character-identical) and the copper did not
    move. So this test now pins THREE rows, and the third one carries the point:

      * v1.10 must now read SUPERSEDED — and must STILL PASS all four gates.
        This is the discrimination that matters here. A superseded release whose
        gates still pass is one that was UNORDERABLE, not WRONG, and the regrade
        has to be able to say the difference. If v1.10's row ever starts FAILING
        a gate, something retro-touched a sealed directory.
      * v1.11 must be LIVE and must PASS F-PAYLOAD and F-LEGIBLE. F-PAYLOAD
        because the pour has now survived TWO supersedes on the board that
        shipped 44287.91 mm2 of missing copper; F-LEGIBLE because a substituted
        MPN/LCSC pair that does not resolve is exactly the row JLC leaves at
        "No Part Selected".

    WHAT THIS TEST STILL CANNOT SEE, stated so nobody mistakes green for safe:
    every gate passed on v1.10 and it could not be built. Row-level PASS here is
    a statement about OUR artifacts, not about JLC's willingness to stuff the
    board."""
    r = run([KPY, TOOL, "--project", "usb-hub-3s-v3"])
    contains(r.out, "v1.8-2026-07-26", "the retired defect is still listed")
    contains(r.out, "NO POUR", "and still named with its reason")
    v18 = [l for l in r.out.splitlines() if "v1.8-2026-07-26" in l]
    check(v18 and "*" in v18[0],
          f"v1.8 must be flagged superseded (*) now that v1.9 exists:\n{v18}")

    def verdicts_of(line):
        cols = ("F-PAYLOAD", "F-LEGIBLE", "A-EVID", "A-POP")
        # UNGR ADDED 2026-07-29 and it is not cosmetic: the gate ran, found no
        # defect, and could not cross-check the shipped bytes. A parser that
        # does not know the state SILENTLY DROPS the cell and mis-zips every
        # verdict after it onto the wrong gate — the table would move under the
        # test without the test noticing, which is why the count is asserted.
        cells = [c for c in line.split()[1:]
                 if c in ("PASS", "FAIL", "UNGR", "?")]
        return dict(zip(cols, cells))

    v19 = [l for l in r.out.splitlines()
           if "v1.9-2026-07-27" in l and "FAIL F-" not in l]
    check(v19, "v1.9 must still appear in the regrade")
    check("*" in v19[0][:60],
          f"v1.9 is SUPERSEDED by v1.10 and must read that way:\n{v19[0]}")
    check(verdicts_of(v19[0]).get("F-LEGIBLE") == "FAIL",
          f"v1.9's F-LEGIBLE failure is HISTORY and must not be erased — "
          f"07_releases is immutable and the record of what was wrong is the "
          f"point of keeping the row:\n{v19[0]}")

    v110 = [l for l in r.out.splitlines()
            if "v1.10-2026-07-27" in l and "FAIL F-" not in l]
    check(v110, "v1.10 must appear in the regrade")
    check("*" in v110[0][:60],
          f"v1.10 is SUPERSEDED by v1.11 and must read that way:\n{v110[0]}")
    v110v = verdicts_of(v110[0])
    for gid in ("F-PAYLOAD", "F-LEGIBLE", "A-EVID", "A-POP"):
        check(v110v.get(gid) == "PASS",
              f"v1.10 was superseded because JLC would not SUPPLY C25744, not "
              f"because anything was wrong with it — all four gates must STILL "
              f"pass on it. A gate turning red on a sealed directory means "
              f"something retro-touched it. {gid}:\n{v110[0]}")

    v111 = [l for l in r.out.splitlines()
            if "v1.11-2026-07-27" in l and "FAIL F-" not in l]
    check(v111, "v1.11 must appear in the regrade")
    verdicts = verdicts_of(v111[0])
    check(verdicts.get("F-PAYLOAD") == "PASS",
          f"v1.11 inherits v1.9's restored pour through TWO supersedes and must "
          f"still ship it — this is the board whose v1.6-v1.8 shipped "
          f"44287.91 mm2 of missing copper:\n{v111[0]}")
    check(verdicts.get("F-LEGIBLE") == "PASS",
          f"v1.11 SUBSTITUTES an MPN/LCSC pair; if F-LEGIBLE does not pass, the "
          f"substituted row is one JLC leaves at 'No Part Selected':\n{v111[0]}")

    # AMENDED 2026-07-28: this block used to pin `"*" not in v111[0]` — i.e. it
    # named v1.11 as the LIVE release. v1.12 sealed the same day (J5's land was
    # KiCad's stock geometry, 0.375 mm off HRO's and JLC's) and the test went
    # RED for the one reason a regrade must NOT go red: the fleet advanced
    # exactly as intended. A test that names a version measures WHEN it ran,
    # not what the gate does. The version-specific rows above stay — they are
    # HISTORY, and the point of an immutable 07_releases is that their verdicts
    # never move — but liveness is now asserted as the PROPERTY it always was:
    # whichever release is live carries the restored pour and a legible BOM.
    # TABLE rows only. The regrade also emits per-gate DETAIL lines that begin
    # with the gate id (`A-EVID usb-hub-3s-v3/v1.1-...: ... [superseded: ...]`);
    # those carry the board path but never the `*` liveness marker, so a naive
    # substring filter reads every one of them as a live release. Table rows are
    # the ones whose first token IS the board path.
    rows = [l for l in r.out.splitlines()
            if l.strip().startswith("usb-hub-3s-v3/") and "FAIL F-" not in l]
    live = [l for l in rows if "*" not in l[:60]]
    check(len(live) == 1,
          "exactly one usb-hub-3s-v3 release may be live (no `*`); got "
          f"{len(live)}:\n" + "\n".join(rows))
    lv = verdicts_of(live[0])
    check(lv.get("F-PAYLOAD") == "PASS",
          f"the LIVE release must ship the restored pour:\n{live[0]}")
    check(lv.get("F-LEGIBLE") == "PASS",
          f"the LIVE release must ship a BOM JLC can read:\n{live[0]}")


@test("regrade_measures_whether_a_seal_can_be_re_derived", kind="known_bad")
def t_measures_reproducibility():
    """THE REGRADE'S OWN PREMISE, WHICH WAS FALSE.

    This tool exists to re-grade sealed work against later knowledge. That is
    only meaningful if a sealed release's verdict is a function of the sealed
    bytes — and for F-LEGIBLE it was not. `cooksense-v1.6-2026-07-27` went FAIL,
    then PASS, on UNCHANGED sealed bytes within one session, because the live
    v1.7 work removed and then restored an `02_parts/ULN2803ADWR` dossier. The
    sweep could not have told anyone: it printed whichever answer the tree
    happened to give that hour.

    So reproducibility is now MEASURED, by an independent method (canon M1): each
    gate that declares a perturbation is re-run with its mutable EXTERNAL
    authority neutralised, and a verdict that MOVES is a verdict about our tree
    rather than about the release. MEASURED at landing: 9 of 33 sealed releases
    flipped PASS -> FAIL under it — every release that passed F-LEGIBLE at all,
    four of them LIVE — and 0 of 33 do now.

    THE KNOWN-BAD IS A SCRATCH FLEET, because the real one is (now) clean and a
    fixture that evaporates when the defect it guards is repaired proves nothing
    afterwards — the exact failure c1af621 recorded for this very tool. The
    synthetic release ships MPN `WRONG-PART` for C1523 while its `02_parts`
    dossier declares `0402B102K500NT`: graded with the tree in reach that is a
    DISAGREE FAIL, graded with the tree gone it is UNGRADEABLE, so the verdict
    MOVES and the sweep must say so and exit non-zero.

    RED-VERIFIED 2026-07-29 by running this fixture through the pre-census
    fleet_regrade (`--no-reproducibility`, which is that tool exactly): the
    NOT-REPRODUCIBLE line is absent and the run reports only the FAIL, i.e. the
    old sweep sees a defective release and cannot see that the defect is a
    property of our editable source. Asserted both ways below."""
    d = tmpdir("regr_repro_")
    (d / "skills").symlink_to(ROOT / "skills")
    rel = d / "projects" / "synth" / "07_releases" / "synth-v1.0-2026-01-01"
    (rel / "fab").mkdir(parents=True)
    (rel / "verification").mkdir()
    (rel / "fab" / "bom.csv").write_bytes(
        b"\xef\xbb\xbfComment,Designator,Footprint,MPN,LCSC\n"
        b"1nF,C1,C_0402_1005Metric,WRONG-PART,C1523\n")
    dossier = d / "projects" / "synth" / "02_parts" / "0402B102K500NT"
    dossier.mkdir(parents=True)
    (dossier / "part.yaml").write_text(
        "mpn: 0402B102K500NT\nsourcing:\n  lcsc: C1523\n")

    r = run([KPY, TOOL, "--root", d])
    check(r.rc != 0, f"a fleet with a non-reproducible verdict exited 0:\n{r.out}")
    contains(r.out, "NOT-REPRODUCIBLE",
             "a verdict that MOVES when the mutable authority is neutralised "
             "must be named as such — it is a statement about our tree, not "
             "about the sealed release")
    contains(r.out, "synth/synth-v1.0-2026-01-01", "and the release is named")
    contains(r.out, "reproducibility:",
             "the census declares its own denominator (canon M-COVER)")
    contains(r.out, "NOT MEASURED",
             "the gates with NO declared perturbation must be NAMED — "
             "unmeasured is not certified reproducible")

    # the pre-census tool, which is what `--no-reproducibility` restores
    old = run([KPY, TOOL, "--root", d, "--no-reproducibility"])
    not_contains(old.out, "NOT-REPRODUCIBLE",
                 "the perturbation must actually be what finds this — if the "
                 "un-perturbed sweep reports it too, this fixture is not "
                 "testing the census")
    contains(old.out, "REPRODUCIBILITY NOT MEASURED",
             "opting out must SAY it graded nothing, not imply a clean bill")


@test("regrade_confirms_the_clean_boards_are_clean")
def t_confirms_clean_boards():
    """The other half of discrimination: a sweep that fails everything ranks
    nothing. crow-recorder-central-v2 v1.5 and cooksense v1.4 were audited as
    ORDERABLE, and every gate that EXISTED at their audit — F-PAYLOAD, A-EVID,
    A-POP — must still agree.

    AMENDED 2026-07-27 (ADR-0006). This test used to require NO `FAIL` anywhere
    in their row, and `F-LEGIBLE` broke it — CORRECTLY. v1.5 is the exact board
    whose BOM was uploaded and whose parts "were not being picked up by their
    web processing"; a new gate failing sealed work is the regrade doing its
    job, not noise. Sealed releases are NOT retro-fixed (07_releases
    immutability), so the honest form is per-gate: the OLD gates must still
    pass, the NEW one is pinned as the ADOPTED-FORWARD gap it is. Weakening the
    assertion to "some gate passes" would have hidden it; deleting the test
    would have thrown away the discrimination property it exists for.

    AMENDED AGAIN 2026-07-27, and the amendment IS the answer the previous one
    demanded. The paragraph above ends "if this is now a pass, either the board
    was re-released (update this test) or the gate stopped biting." cooksense
    WAS re-released: `cooksense-v1.5-2026-07-27` fixes exactly the 83 F-LEGIBLE
    findings v1.4 carried, so v1.4 gained a SUPERSEDED.md and left the LIVE set.
    The failure that surfaced this was not the F-LEGIBLE assertion at all — the
    row filter `"*" not in l[:60]` skips superseded table rows, so once v1.4 was
    starred the filter fell through to a trailing DETAIL line and parsed
    nonsense out of it. A fixture pinned to a release NAME decays; this one now
    asks for the board's LIVE release by name-independent means and asserts the
    property per release STATE:

      SUPERSEDED and pre-ADR-0006  old gates PASS, F-LEGIBLE FAIL (history)
      LIVE                         ALL FOUR must PASS

    crow-recorder-central-v2 v1.5 keeps the first shape (it too is superseded,
    by v1.6, for the same reason); cooksense now exercises the second, which is
    the stronger claim and the one a live board must satisfy.

    RED-VERIFIED IN PLACE at the v1.5 seal, per tests/README: pointing the LIVE
    half at `cooksense-v1.4-2026-07-26` — the superseded, F-LEGIBLE-failing
    release it used to assert on — makes this test FAIL with
    "the LIVE cooksense release cooksense-v1.4-2026-07-26 carries a
    SUPERSEDED.md — the release index and the regrade disagree about what is
    live", then restored to green. The new assertion bites."""
    cols = ("F-PAYLOAD", "F-LEGIBLE", "A-EVID", "A-POP")


    def row(proj, rel):
        r = run([KPY, TOOL, "--project", proj])
        # the TABLE row, not a trailing detail line: detail lines start with a
        # gate id and carry a ':' before the release name.
        line = [ln for ln in r.out.splitlines()
                if rel in ln and ln.lstrip().startswith(("*", proj[0], proj))
                and ":" not in ln.split(rel)[0]]
        check(line, f"{proj} {rel} missing from the regrade table")
        cells = [c for c in line[0].split()[1:]
                 if c in ("PASS", "FAIL", "UNGR", "?")]
        check(len(cells) == len(cols),
              f"{proj} {rel}: parsed {len(cells)} verdict cells, expected "
              f"{len(cols)} — the table shape moved:\n{line[0]}")
        return line[0], dict(zip(cols, cells))

    # MERGED 2026-07-27 from two concurrent agents, and BOTH halves were right
    # about different things -- kept rather than picking a winner.
    #
    # From one: the `row()` helper above, which parses the TABLE row instead of
    # a trailing detail line and ASSERTS the parsed cell count. A test that
    # silently mis-parses a moved table is a test that grades nothing.
    #
    # From the other: A-EVID is not a fixed expectation, because it reads the
    # project's OWN 07_releases/contracts.md -- so a CONTRACT RE-SYNC widens the
    # gate by a second door. When crow-recorder-central-v2 synced its copy from
    # the template at v1.7, the contract gained the two ADR-0006 artifacts
    # (`verification/bom_legibility.txt`, `verification/bom_echo_gate.txt`) and
    # v1.5, which predates ADR-0006 entirely, does not carry them. That is the
    # same gap F-LEGIBLE already pins on that release, arriving through a
    # different door, so it is PINNED the same way rather than excused.
    #
    # cooksense has now synced the widened contract too, so v1.4's missing
    # ADR-0006 evidence is pinned as FAIL just like crow v1.5. Recording that
    # move preserves the adopted-forward gap instead of weakening the gate.
    expect_aevid = {"crow-recorder-central-v2": "FAIL",
                    "smc0985-cooksense": "FAIL"}
    for proj, rel in (("crow-recorder-central-v2", "v1.5-2026-07-25"),
                      ("smc0985-cooksense", "cooksense-v1.4-2026-07-26")):
        line, verdicts = row(proj, rel)
        for gid in ("F-PAYLOAD", "A-POP"):
            check(verdicts.get(gid) == "PASS",
                  f"{proj} {rel} was audited ORDERABLE but {gid} — a gate that "
                  f"existed at its audit AND whose contract has not widened "
                  f"since — now fails it:\n{line}")
        check(verdicts.get("A-EVID") == expect_aevid[proj],
              f"{proj} {rel} A-EVID is {verdicts.get('A-EVID')}, expected "
              f"{expect_aevid[proj]}. A FAIL here is legitimate ONLY as the "
              f"contract widening described above — check WHICH artifacts are "
              f"missing before updating this expectation:\n{line}")

        check(verdicts.get("F-LEGIBLE") == "FAIL",
              f"{proj} {rel} unexpectedly PASSES F-LEGIBLE. It was sealed "
              f"before ADR-0006 and ships an unreadable BOM; if this is now a "
              f"pass, either the board was re-released (update this test) or "
              f"the gate stopped biting.\n{line}")

    # NEWEST: every standalone gate that can run must PASS. The newest release
    # can legitimately be superseded by an order-process defect outside these
    # four artifact gates; the table marker must agree with the immutable
    # release bytes instead of this test inventing a second definition of
    # "live".
    sys.path.insert(0, str(ROOT / "skills" / "jlcpcb-fab" / "scripts"))
    import release_index as ri  # noqa: E402
    cook = ROOT / "projects" / "smc0985-cooksense"
    latest = ri.releases_for_board(cook, "cooksense")[-1].name
    line, verdicts = row("smc0985-cooksense", latest)
    is_superseded = (cook / "07_releases" / latest / "SUPERSEDED.md").is_file()
    check(("*" in line[:60]) == is_superseded,
          f"the newest cooksense release {latest} superseded marker disagrees "
          f"with its immutable release bytes:\n{line}")
    for gid in cols:
        check(verdicts.get(gid) == "PASS",
              f"smc0985-cooksense {latest} is the newest release and {gid} "
              f"fails it. Supersession does not excuse a regression in a "
              f"standalone artifact gate:\n{line}")

    # AMENDED 2026-07-29, and this is the amendment that keeps the assertion
    # HONEST rather than merely green. This test was RED on 2026-07-29 because
    # F-LEGIBLE failed the sealed cooksense v1.6 on C506653 and C9683; hours
    # later it was GREEN again with no byte of that release changed, because the
    # concurrent v1.7 work happened to restore the `ULN2803ADWR` dossier it had
    # removed. A "PASS" that a sibling agent's unrelated edit can hand you and
    # take away is not a passing gate — it is a coin toss the test cannot see.
    # So the NEWEST release must also be REPRODUCIBLE: no verdict of its may move
    # when the mutable authority behind it is neutralised. If this line ever goes
    # red, the gate has re-acquired a dependency on editable source and the
    # verdicts above mean nothing.
    r = run([KPY, TOOL, "--project", "smc0985-cooksense"])
    moved = [ln for ln in r.out.splitlines()
             if "NOT-REPRODUCIBLE" in ln and latest in ln]
    check(not moved,
          f"the newest cooksense release {latest} has a verdict that MOVES "
          f"when the gate's mutable external authority is neutralised, so the PASSes "
          f"asserted above are statements about our 02_parts tree and not about "
          f"the sealed release:\n" + "\n".join(moved))
    contains(r.out, "reproducibility:",
             "the sweep must MEASURE reproducibility, not assume it — assuming "
             "it is how a seal's verdict moved twice in one session unnoticed")


if __name__ == "__main__":
    sys.exit(main())
