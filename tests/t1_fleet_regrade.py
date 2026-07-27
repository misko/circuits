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


@test("regrade_finds_the_live_pour_defect", kind="known_bad")
def t_finds_the_live_pour_defect():
    """usb-hub v1.8 is LIVE (no SUPERSEDED.md — no successor exists yet) and
    must show as a live F-PAYLOAD failure, not be lost among its superseded
    siblings."""
    r = must_fail(run([KPY, TOOL, "--project", "usb-hub-3s-v3"]),
                  "regrade over usb-hub-3s-v3")
    contains(r.out, "v1.8-2026-07-26", "v1.8 is listed")
    contains(r.out, "NO POUR", "the live defect is named with its reason")


@test("regrade_confirms_the_clean_boards_are_clean")
def t_confirms_clean_boards():
    """The other half of discrimination. crow-recorder-central-v2 v1.5 and
    cooksense v1.4 were audited as ORDERABLE; today's gates must agree, or the
    regrade is just noise. A sweep that fails everything ranks nothing."""
    for proj, rel in (("crow-recorder-central-v2", "v1.5-2026-07-25"),
                      ("smc0985-cooksense", "cooksense-v1.4-2026-07-26")):
        r = run([KPY, TOOL, "--project", proj])
        line = [l for l in r.out.splitlines() if rel in l and "*" not in l[:60]]
        check(line, f"{proj} {rel} missing from the regrade output")
        check("FAIL" not in line[0],
              f"{proj} {rel} was audited ORDERABLE but the regrade fails it:\n"
              f"{line[0]}")


if __name__ == "__main__":
    sys.exit(main())
