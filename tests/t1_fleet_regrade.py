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
                     must_pass, run, test, tmpdir)

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
        cells = [c for c in line.split()[1:] if c in ("PASS", "FAIL", "?")]
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
    check("*" not in v111[0][:60],
          f"v1.11 is the LIVE release and must not read as superseded:"
          f"\n{v111[0]}")
    verdicts = verdicts_of(v111[0])
    check(verdicts.get("F-PAYLOAD") == "PASS",
          f"v1.11 inherits v1.9's restored pour through TWO supersedes and must "
          f"still ship it — this is the board whose v1.6-v1.8 shipped "
          f"44287.91 mm2 of missing copper:\n{v111[0]}")
    check(verdicts.get("F-LEGIBLE") == "PASS",
          f"v1.11 SUBSTITUTES an MPN/LCSC pair; if F-LEGIBLE does not pass, the "
          f"substituted row is one JLC leaves at 'No Part Selected':\n{v111[0]}")


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
    would have thrown away the discrimination property it exists for."""
    cols = ("F-PAYLOAD", "F-LEGIBLE", "A-EVID", "A-POP")
    for proj, rel in (("crow-recorder-central-v2", "v1.5-2026-07-25"),
                      ("smc0985-cooksense", "cooksense-v1.4-2026-07-26")):
        r = run([KPY, TOOL, "--project", proj])
        line = [l for l in r.out.splitlines() if rel in l and "*" not in l[:60]]
        check(line, f"{proj} {rel} missing from the regrade output")
        cells = line[0].split()[1:]
        verdicts = dict(zip(cols, [c for c in cells if c in ("PASS", "FAIL", "?")]))
        for gid in ("F-PAYLOAD", "A-EVID", "A-POP"):
            check(verdicts.get(gid) == "PASS",
                  f"{proj} {rel} was audited ORDERABLE but {gid} — a gate that "
                  f"existed at its audit — now fails it:\n{line[0]}")
        check(verdicts.get("F-LEGIBLE") == "FAIL",
              f"{proj} {rel} unexpectedly PASSES F-LEGIBLE. Both were sealed "
              f"before ADR-0006 and both ship an unreadable BOM; if this is now "
              f"a pass, either the board was re-released (update this test) or "
              f"the gate stopped biting.\n{line[0]}")


if __name__ == "__main__":
    sys.exit(main())
