#!/usr/bin/env python3
"""t1_waiver_evidence — the `evidence:` schema on a waiver: a load-bearing
number carries a COMMAND and its OUTPUT, and the gate REGENERATES AND DIFFS it.

==========================================================================
THE INCIDENT (2026-07-29, pluto-rx2-8way, waiver `P-ADJ-UNREACHED` at c07aaf2)
==========================================================================

    MEASURED by hand instead: C_SW1 pad 1 to U_SW pin 8 = 2.62 mm, inside the
    3 mm the datasheet sentence means.

Re-measured with pcbnew against the board that revision governed: **3.085 mm**
pad-centre to pad-centre — the measure `policy_audit.py:412` itself defines for
P-ADJ. That is 0.085 mm OVER the 3 mm the waiver asserted it was inside, so THE
WAIVER'S CONCLUSION REVERSES. `2.62` reproduces under no definition (edge-to-edge
is 2.375 mm rect / 2.438 mm roundrect), so it is a free-hand estimate rather than
a typo or a mis-defined metric. A second entry typed "2.53 mm" where the pair
measures 3.057 mm; that one stayed inside its 4 mm budget, so it was wrong
without being load-bearing. Both survived a full revision cycle, past
`policy_audit.py:165` (a LENGTH test on `why`) and past `waiver_provenance`'s
W-COPY/W-FOREIGN (prose-against-prose similarity).

FLEET DENOMINATOR, measured by this gate on 2026-07-29 at main tip:
**22 waiver entries across 5 boards, 22 OWED, 0 CITED** — and separately
**2 of 11 machine-waived refdes** in `04_kicad/refdes_waiver.json` carry a
project-side evidenced entry.

RED-VERIFIED against pre-fix code. The pre-fix gate is
`git show 55be87b:skills/kicad-pcb/scripts/waiver_provenance.py` (equivalently
HEAD before this commit), which has no `evidence:` handling of any kind. Run
against every known-bad fixture below its measured output is byte-identical to
its output on the clean fixture and it EXITS 0:

    input: root = <root>  (2 project dir(s), reading 03_src/rules/policy_waivers.yaml)
    input: 2 project(s) carry waivers, 2 waiver(s) total; grading 2: board-alpha, board-bravo
      ok   W-COPY/board-alpha: 1 waivers, all independently reasoned
      ok   W-COPY/board-bravo: 1 waivers, all independently reasoned
    WAIVER PROVENANCE: PASS (0 fails, 2 ok) — 2/2 waiver(s) graded across 2/2 project(s) carrying waivers

i.e. pre-fix, an `evidence:` block is unread YAML: the typed 2.62, the true
3.085 and a physically impossible -410 all produce that same text. Each test
below names its own pre-fix result in its docstring.

BOTH HALVES. A waiver carrying a CORRECT `command:`/`output:` must PASS and be
reported CITED (`t_a_correct_citation_passes_and_is_reported_cited`,
`t_the_real_board_end_to_end_pcbnew_citation_regenerates`) — a gate that only
knows how to reject ranks nothing.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq, main, must_fail,
                     must_pass, not_contains, run, test, tmpdir)

PY = KPY
WAIVER_PROV = SCRIPTS / "waiver_provenance.py"
FLEET = ROOT / "projects"

# A second, independently-reasoned waiver so W-COPY has something to compare
# and the run is never a single-project no-op (canon M-COVER).
OTHER = """- id: R-THERM
  refs: [Q1]
  why: >-
    Q1's DPAK tab dissipates about 1.0W at the 8.2A pack-empty corner. With
    roughly 70C/W single-sided spreading on this 2oz pour that is hot but
    inside the device rating, and the tab already carries four in-pad vias
    down to the plane. Measured on the fabricated v1.1 board with a probe.
"""

# A THIRD, unrelated rationale. Reusing OTHER for both projects in a fixture
# trips W-COPY at 100% (correctly — that is the 2026-07-20 incident), which
# would then mask whichever new finding the fixture is actually about.
DISTINCT = """- id: R-POUR
  refs: [VBUS1]
  why: >-
    MEASURED (pcbnew) on THIS board: VBUS1 is a continuous 0.8 mm F.Cu run at
    1oz over 9 mm from the TPS2557 to the USB-A THT pad. IPC-2221 external
    gives 2.03 A at a 10 C rise and the ILIM-bounded worst case is 2.51 A, so
    the rise is about 16 C. Recorded as a next-spin defect, not shipped.
"""

# THE REAL ENTRY, verbatim in substance, promoted to the schema. The prose is
# the incident's own prose; only the evidence block is new.
INCIDENT_WHY = """    PE42482A-X `SW_VDD <= 3 mm` — pin 8 sits on the GLOBAL 3V3 net (no series
    element makes a second node), so the budget as written would grade the
    whole rail. MEASURED by hand instead, against the datasheet's 3 mm.
"""


def _project(root, name, entries):
    p = root / name
    (p / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
    (p / "03_src" / "rules" / "policy_waivers.yaml").write_text(entries)
    return p


def _incident(output, budget='"<= 3.0"', measured="3.085", extra=""):
    """The C_SW1 entry with `output:` and the regenerated value both dialable.

    `command` is a `printf` rather than a live pcbnew call ON PURPOSE: the
    number this fixture must reproduce is the one measured on the board AS IT
    WAS AT c07aaf2, and a fixture that re-measures today's copper would grade a
    board a sibling agent is rebuilding. The pcbnew path is proved separately,
    end to end, by `t_the_real_board_end_to_end_pcbnew_citation_regenerates`.
    """
    return (f"- id: P-ADJ-UNREACHED\n"
            f"  refs: [PE42482A-X]\n"
            f"  why: >-\n{INCIDENT_WHY}"
            f"  evidence:\n"
            f"    - claim: C_SW1.1 -> U_SW.8, pad centre to pad centre "
            f"(the measure policy_audit.py:412 defines for P-ADJ)\n"
            f"      command: printf '%s\\n' {measured}\n"
            f"      output: \"{output}\"\n"
            + (f"      budget: {budget}\n" if budget else "")
            + extra)


def _pair(entries, other=OTHER):
    d = tmpdir("t1wev_")
    root = d / "projects"
    _project(root, "board-alpha", entries)
    _project(root, "board-bravo", other)
    return root


# ==========================================================================
# THE HEADLINE: the real entry, and the conclusion that reverses
# ==========================================================================

@test("INCIDENT(2026-07-29): the C_SW1 waiver promoted to the `evidence:` "
      "schema is CAUGHT, and the reversal is named", kind="known_bad")
def t_incident_the_c_sw1_waiver_promoted_to_the_evidence_schema_is_caught():
    """The headline case, built from the real entry.

    Typed 2.62 against a declared budget of `<= 3.0`; the command regenerates
    3.085, which does NOT satisfy `<= 3.0`. That is not a 0.465 discrepancy, it
    is a REVERSED VERDICT, and it must be reported as one — W-FLIP, distinct
    from W-REGEN, and never excused by a tolerance.

    PRE-FIX (HEAD's waiver_provenance.py, no `evidence:` handling): exit 0,
    output byte-identical to the clean fixture —
    `WAIVER PROVENANCE: PASS (0 fails, 2 ok) — 2/2 waiver(s) graded`.
    """
    r = run([PY, WAIVER_PROV, _pair(_incident("2.62 mm"))])
    must_fail(r, "waiver_provenance on the C_SW1 entry as written", "W-FLIP")
    contains(r.out, "CONCLUSION REVERSES", "the reversal must be named as such")
    contains(r.out, "2.62", "the typed number must be quoted")
    contains(r.out, "3.085", "the regenerated number must be quoted")
    contains(r.out, "C_SW1", "the claim must be quoted so the pair is findable")
    # NOT a plain disagreement: the gate must distinguish the two.
    not_contains(r.out, "W-REGEN", "a reversal is reported as W-FLIP, not as a "
                                   "mere numeric delta")


@test("a tolerance cannot excuse a reversed conclusion", kind="known_bad")
def t_tolerance_cannot_excuse_a_reversal():
    """The obvious escape hatch, closed. 2.62 -> 3.085 is a 0.465 delta; declare
    a 1.0 tolerance with a straight-faced justification and W-REGEN goes quiet.
    W-FLIP must fire anyway, because the budget relation flipped and no amount
    of declared drift makes an over-budget pair under-budget.

    PRE-FIX: exit 0 (no `evidence:` handling at all).
    """
    entry = _incident("2.62 mm", extra=(
        "      tolerance: 1.0\n"
        "      tolerance_why: >-\n"
        "        Placement is stochastic and pads drift, so a millimetre of\n"
        "        slack is reasonable here.\n"))
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "a reversal under a 1.0 mm tolerance", "W-FLIP")


@test("a correct citation PASSES and is reported CITED")
def t_a_correct_citation_passes_and_is_reported_cited():
    """THE OTHER HALF. A gate that only rejects ranks nothing: the same entry
    with the number it actually measures, and a budget it actually satisfies,
    must pass and must be VISIBLE as CITED in the report — otherwise nobody can
    tell a graded waiver from an ungraded one, which is the state that produced
    the incident.

    PRE-FIX: also exit 0 — indistinguishable from the fixture above, which is
    the point.
    """
    r = must_pass(run([PY, WAIVER_PROV, _pair(_incident("2.873",
                                                        measured="2.873"))]),
                  "waiver_provenance on a citation that regenerates")
    contains(r.out, "CITED", "the item must be reported CITED by name")
    contains(r.out, "regenerated 2.873 vs typed 2.873",
             "the report must show the diff it performed, not just a verdict")
    contains(r.out, "1 CITED", "the coverage line must count it")
    contains(r.out, "EVIDENCE COVERAGE", "coverage carries a denominator")


# ==========================================================================
# W-REGEN and the tolerance that must not become the next typed number
# ==========================================================================

@test("a regenerated number that DISAGREES beyond tolerance FAILS",
      kind="known_bad")
def t_regen_disagreement_fails():
    """The 2.53-vs-3.057 class: wrong without being load-bearing (it stayed
    inside its 4 mm budget). A gate that only caught reversals would let this
    one through, and a number nobody can reproduce is not evidence even when
    its conclusion happens to survive.

    PRE-FIX: exit 0.
    """
    entry = _incident("2.53", budget='"<= 4.0"', measured="3.057")
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "a typed 2.53 against a measured 3.057", "W-REGEN")
    contains(r.out, "delta 0.527", "the delta must be reported")
    not_contains(r.out, "W-FLIP", "3.057 still satisfies <= 4.0 — this is a "
                                  "disagreement, not a reversal, and "
                                  "conflating them would hide which is which")


@test("a disagreement INSIDE a justified tolerance passes")
def t_disagreement_inside_tolerance_passes():
    """Non-determinism is real: KRT routing is stochastic and silk placement is
    order-dependent, so a regenerated number may legitimately move. The
    tolerance is per-entry and declared, and this is the case it exists for."""
    entry = _incident("2.870", measured="2.873", extra=(
        "      tolerance: 0.01\n"
        "      tolerance_why: >-\n"
        "        Pad centres move only when the legalizer moves a part; the\n"
        "        0.01 mm allows for the nanometre-quantised import rounding\n"
        "        that KRT introduces, and nothing else.\n"))
    r = must_pass(run([PY, WAIVER_PROV, _pair(entry)]),
                  "a 0.003 delta inside a declared 0.01 tolerance")
    contains(r.out, "CITED", "it is still a citation")


@test("a tolerance WIDER than the margin the entry claims FAILS",
      kind="known_bad")
def t_tolerance_wider_than_margin_fails():
    """THE FIX MUST NOT RECREATE THE DEFECT. `tolerance` is itself a
    load-bearing number, and the way it goes wrong is being set wide enough
    that the check cannot discriminate: 2.873 against `<= 3.0` has a 0.127 mm
    margin, so a 0.2 mm tolerance means a regenerated 3.05 would be accepted as
    'agreeing' with a number whose whole job is to be under 3.0.

    PRE-FIX: exit 0.
    """
    entry = _incident("2.873", measured="2.873", extra=(
        "      tolerance: 0.2\n"
        "      tolerance_why: >-\n"
        "        Placement moves parts around, so a couple of tenths is fine.\n"))
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "a tolerance wider than the claimed margin", "W-TOL")
    contains(r.out, "cannot distinguish pass from fail",
             "the report must say WHY the tolerance is refused")


@test("a tolerance with no justification FAILS", kind="known_bad")
def t_tolerance_without_why_fails():
    """A bare `tolerance: 0.01` is the next typed number. It carries the same
    burden as the measurement it grades.

    PRE-FIX: exit 0.
    """
    entry = _incident("2.870", measured="2.873",
                      extra="      tolerance: 0.01\n")
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "a tolerance with no tolerance_why", "W-TOL")


# ==========================================================================
# W-ARITH — free, no board, no command
# ==========================================================================

@test("a typed number that contradicts its OWN declared budget FAILS with no "
      "command at all", kind="known_bad")
def t_arith_typed_number_contradicts_its_own_budget():
    """The cheapest arm and the one that needs nothing: the author wrote 3.085
    and `<= 3.0` next to each other. No board, no pcbnew, no command — pure
    arithmetic on two numbers in the same YAML mapping. This is the shape the
    incident would have taken had the hand measurement been honest and the
    conclusion still asserted.

    PRE-FIX: exit 0.
    """
    entry = (f"- id: P-ADJ-UNREACHED\n"
             f"  refs: [PE42482A-X]\n"
             f"  why: >-\n{INCIDENT_WHY}"
             f"  evidence:\n"
             f"    - claim: C_SW1.1 -> U_SW.8 pad centre to pad centre\n"
             f"      output: \"3.085\"\n"
             f"      budget: \"<= 3.0\"\n"
             f"      grade: ESTIMATED\n"
             f"      why_not_rerunnable: >-\n"
             f"        Measured with calipers on the fabricated coupon; there\n"
             f"        is no board file for that revision any more.\n")
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "a typed number that fails its own budget", "W-ARITH")
    contains(r.out, "contradicts itself",
             "the finding is self-contradiction, and should read that way")


# ==========================================================================
# W-GRADE / W-SCHEMA — the declaration must be honest before anything runs
# ==========================================================================

@test("grade CITED with no command FAILS — a citation claim with nothing "
      "cited", kind="known_bad")
def t_grade_cited_without_command_fails():
    """The obvious way to buy the badge without paying for it.
    PRE-FIX: exit 0."""
    entry = (f"- id: P-ADJ\n  refs: [PE42482A-X]\n  why: >-\n{INCIDENT_WHY}"
             f"  evidence:\n"
             f"    - claim: C_SW1.1 -> U_SW.8 pad centre to pad centre\n"
             f"      output: \"2.873\"\n"
             f"      grade: CITED\n")
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "grade CITED with no command", "W-GRADE")
    contains(r.out, "M-IMPORT", "the ladder's canon must be cited in the fix "
                                "advice — ESTIMATED is the legal alternative")


@test("grade ESTIMATED PASSES when it says why, and is NEVER counted CITED")
def t_grade_estimated_passes_and_is_not_cited():
    """THE LADDER'S MIDDLE RUNG (canon M-IMPORT: ESTIMATED, not CITED). A number
    that genuinely cannot be regenerated must not silently pass AND must not
    block the fleet. It is legal, it is reported with its own grade, and it
    never inflates the CITED count."""
    entry = (f"- id: P-ADJ\n  refs: [PE42482A-X]\n  why: >-\n{INCIDENT_WHY}"
             f"  evidence:\n"
             f"    - claim: C_SW1.1 -> U_SW.8 measured on the fabricated board\n"
             f"      output: \"2.873\"\n"
             f"      budget: \"<= 3.0\"\n"
             f"      grade: ESTIMATED\n"
             f"      why_not_rerunnable: >-\n"
             f"        Calipers on the assembled v1.0 coupon; the placement\n"
             f"        that produced it was superseded, so no board file in\n"
             f"        the tree reproduces this pair.\n")
    r = must_pass(run([PY, WAIVER_PROV, _pair(entry)]),
                  "an honestly-declared ESTIMATED measurement")
    contains(r.out, "ESTIMATED", "the grade must be reported by name")
    contains(r.out, "0 CITED", "an ESTIMATED item must not be counted CITED")


@test("grade ESTIMATED with no reason FAILS", kind="known_bad")
def t_grade_estimated_without_reason_fails():
    """ESTIMATED is a legal grade; an UNEXPLAINED one is a blank cheque.
    PRE-FIX: exit 0."""
    entry = (f"- id: P-ADJ\n  refs: [PE42482A-X]\n  why: >-\n{INCIDENT_WHY}"
             f"  evidence:\n"
             f"    - claim: C_SW1.1 -> U_SW.8 pad centre to pad centre\n"
             f"      output: \"2.873\"\n"
             f"      grade: ESTIMATED\n")
    must_fail(run([PY, WAIVER_PROV, _pair(entry)]),
              "grade ESTIMATED with no why_not_rerunnable", "W-GRADE")


@test("a MISSPELLED `command:` key FAILS instead of degrading into prose",
      kind="known_bad")
def t_misspelled_command_key_fails():
    """The failure mode that would quietly undo the whole schema: `commmand:`
    parses as YAML, carries a perfectly good shell line, and is read by nobody.
    An unknown key inside `evidence:` is a hard finding, so the schema cannot
    rot back into the prose it replaced.

    PRE-FIX: exit 0.
    """
    entry = _incident("2.62 mm").replace("      command:", "      commmand:")
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "an evidence item with a misspelled command key", "W-SCHEMA")
    contains(r.out, "commmand", "the offending key must be named")


@test("an `output:` carrying TWO numbers FAILS — that is prose again",
      kind="known_bad")
def t_output_with_two_numbers_fails():
    """`output: "2.62 mm of the 3 mm budget"` is the sentence the schema exists
    to replace. One field, one number, or there is nothing to diff.

    PRE-FIX: exit 0.
    """
    entry = _incident("2.62 mm of the 3 mm budget", budget="")
    r = run([PY, WAIVER_PROV, _pair(entry)])
    must_fail(r, "an output with two numbers in it", "W-SCHEMA")
    contains(r.out, "exactly one number", "the rule must be stated")


@test("an evidence command that is not READ-ONLY is refused, not run",
      kind="known_bad")
def t_mutating_command_refused():
    """This gate EXECUTES what the YAML says. An audit that can write is not an
    audit — and the file it would write to is under `projects/`, which is
    exactly what a checker must never touch. The refusal is also verified by
    its effect: the file the command names must not exist afterwards.

    PRE-FIX: exit 0 — and pre-fix the command was never run either, because
    `evidence:` was unread YAML. The check is what makes running it safe.
    """
    d = tmpdir("t1wev_mut_")
    victim = d / "must_not_exist.txt"
    root = d / "projects"
    _project(root, "board-alpha", _incident(
        "2.873", measured="2.873").replace(
            f"      command: printf '%s\\n' 2.873",
            f"      command: printf '%s' 2.873 > {victim}"))
    _project(root, "board-bravo", OTHER)
    r = run([PY, WAIVER_PROV, root])
    must_fail(r, "a mutating evidence command", "W-CMD")
    contains(r.out, "read-only", "the refusal must state the property")
    check(not victim.exists(),
          f"the gate RAN a mutating evidence command: {victim} exists")


# ==========================================================================
# THE LADDER: un-rerunnable must neither pass silently nor block the fleet
# ==========================================================================

@test("a command whose DECLARED input is absent is UNVERIFIED, named, and "
      "does not fail the fleet")
def t_absent_declared_input_is_unverified_not_a_fail():
    """THE LADDER RUNG THAT DECIDES WHETHER THIS GATE IS USABLE. Some evidence
    needs pcbnew, some needs a board a sibling agent is rebuilding right now. A
    verdict that depends on whether that rebuild happens to be mid-write is a
    verdict nobody can act on, so a declared-but-absent input downgrades the
    item to UNVERIFIED: printed by name, credited to nobody, and NOT a fail.

    The contrast (next test) is what stops that from being a blanket excuse."""
    entry = _incident("2.873", measured="2.873", extra=(
        "      requires: [projects/board-alpha/04_kicad/nope.kicad_pcb]\n"))
    r = must_pass(run([PY, WAIVER_PROV, _pair(entry)]),
                  "an evidence item whose declared input is absent")
    contains(r.out, "UNVERIFIED", "the item must be named as UNVERIFIED")
    contains(r.out, "declared input absent here", "with the reason")
    contains(r.out, "0 CITED", "and must NOT be credited as a citation")


@test("`requires:` is not a blanket excuse — a present input still gets "
      "diffed", kind="known_bad")
def t_requires_present_still_diffed():
    """The adjacent property. Same entry, same `requires:`, pointing at a file
    that DOES exist: the command runs and the wrong number fails. If this
    passed, `requires:` would be a way to switch the check off.

    PRE-FIX: exit 0.
    """
    d = tmpdir("t1wev_req_")
    root = d / "projects"
    marker = root / "board-alpha" / "03_src" / "rules" / "policy_waivers.yaml"
    entry = _incident("2.62 mm", measured="3.085", extra=(
        f"      requires: [projects/board-alpha/03_src/rules/"
        f"policy_waivers.yaml]\n"))
    _project(root, "board-alpha", entry)
    _project(root, "board-bravo", OTHER)
    check(marker.exists(), "fixture setup: the required file must exist")
    must_fail(run([PY, WAIVER_PROV, root]),
              "a satisfiable `requires:` with a reversed conclusion", "W-FLIP")


@test("a command that RUNS AND FAILS is UNVERIFIED, not a fleet fail")
def t_broken_command_is_unverified():
    """A citation that no longer executes is a maintenance defect, not a false
    claim about copper, and the environment (a missing interpreter, a moved
    script) must not be able to red the fleet. It is named with its exit code
    and stderr tail, and the monotone protection is the CITED FLOOR: if a
    working citation stops working, the CITED count drops below the committed
    floor and THAT fails."""
    entry = _incident("2.873", measured="2.873").replace(
        "      command: printf '%s\\n' 2.873",
        "      command: /usr/bin/python3 -c \"import sys; sys.exit(3)\"")
    r = must_pass(run([PY, WAIVER_PROV, _pair(entry)]),
                  "an evidence command that exits nonzero")
    contains(r.out, "UNVERIFIED", "named")
    contains(r.out, "exit 3", "with the exit code")


@test("the CITED FLOOR fails a citation that stopped reproducing",
      kind="known_bad")
def t_cited_floor_catches_a_lost_citation():
    """The ratchet's monotone half, and the reason a broken command can be
    UNVERIFIED without opening a hole: with a floor of 1 committed, an entry
    whose command no longer produces a number takes CITED to 0 and fails.

    PRE-FIX: exit 0 (no floors, no coverage, no evidence).
    """
    entry = _incident("2.873", measured="2.873").replace(
        "      command: printf '%s\\n' 2.873",
        "      command: /usr/bin/python3 -c \"print('no number here at all')\"")
    root = _pair(entry)
    r = run([PY, WAIVER_PROV, root, "--cited-floor", "1"])
    must_fail(r, "a lost citation against a floor of 1", "W-FLOOR")
    contains(r.out, "may only be edited UP", "the floor's direction is stated")
    # ADJACENT PROPERTY, re-measured every run: the SAME tree with the command
    # restored passes the same floor. Otherwise this test would pass merely
    # because a floor of 1 is unreachable in a fixture.
    r2 = must_pass(run([PY, WAIVER_PROV, _pair(_incident("2.873",
                                                         measured="2.873")),
                        "--cited-floor", "1"]),
                   "the same floor with the citation intact")
    contains(r2.out, "1 CITED", "the floor is met by a real citation")


@test("--no-regen degrades every citation to UNVERIFIED rather than passing it")
def t_no_regen_is_not_a_pass():
    """The fast path must not be a green path. With regeneration off the run
    still exits 0 (it has graded nothing to the contrary) but reports 0 CITED
    and says regeneration was OFF, so a run whose numbers were never re-derived
    cannot be mistaken for one that was."""
    r = must_pass(run([PY, WAIVER_PROV, _pair(_incident("2.62 mm")),
                       "--no-regen"]),
                  "waiver_provenance --no-regen")
    contains(r.out, "regeneration OFF", "the run must declare it")
    contains(r.out, "0 CITED", "nothing may be credited as regenerated")
    contains(r.out, "UNVERIFIED", "and the item is named")


# ==========================================================================
# W-REFS — a line span is a load-bearing typed number
# ==========================================================================

@test("a `refs:` line span that reaches past the end of the file FAILS",
      kind="known_bad")
def t_refs_line_span_out_of_range_fails():
    """crow-mic-pod-v2's R-RULES cites `04_kicad/....kicad_dru:8-10` for the two
    rules that cannot fire. That range is a typed number: regenerate the .dru,
    or drop a rule, and the citation silently points at nothing while still
    reading as precise evidence.

    PRE-FIX: exit 0 — nothing has ever opened a `refs:` target.
    """
    d = tmpdir("t1wev_refs_")
    root = d / "projects"
    p = _project(root, "board-alpha",
                 "- id: R-RULES\n"
                 "  refs: [\"04_kicad/board.kicad_dru:8-10\"]\n"
                 "  why: >-\n"
                 "    Two of the four rules in the shipped .kicad_dru cannot\n"
                 "    fire; accepted for this docs-only supersede because the\n"
                 "    copper is asserted byte-identical to the sealed release.\n")
    (p / "04_kicad").mkdir(parents=True, exist_ok=True)
    dru = p / "04_kicad" / "board.kicad_dru"
    dru.write_text("\n".join(f"line {i}" for i in range(1, 14)))
    _project(root, "board-bravo", OTHER)
    # BOTH HALVES, on the same fixture: 8-10 is inside a 13-line file.
    r_ok = must_pass(run([PY, WAIVER_PROV, root]),
                     "a refs line span that resolves")
    not_contains(r_ok.out, "W-REFS", "an in-range span is not a finding")
    # ... and the one-property break: the file loses its tail.
    dru.write_text("\n".join(f"line {i}" for i in range(1, 8)))
    r = run([PY, WAIVER_PROV, root])
    must_fail(r, "a refs span past the end of the file", "W-REFS")
    contains(r.out, "7 line(s)", "the measured line count must be reported")


@test("a `refs:` path that resolves NOWHERE fails, but a bare basename that "
      "resolves somewhere does not", kind="known_bad")
def t_refs_missing_path_fails_but_basename_is_not_a_path():
    """The adjacent-property trap this check walked into on first run:
    pluto-rx2-8way's S-OCCL cites `pluto_rx2_8way.kicad_sch` with no directory,
    and that file exists twice in the project. Failing it would punish an
    unqualified citation as if it were a broken one. So a bare basename is
    searched for; only a slash-bearing path, or a name that resolves nowhere, is
    a finding.

    PRE-FIX: exit 0.
    """
    d = tmpdir("t1wev_refs2_")
    root = d / "projects"
    p = _project(root, "board-alpha",
                 "- id: S-OCCL\n"
                 "  refs: [board.kicad_sch]\n"
                 "  why: >-\n"
                 "    16 text occlusions in the CONVERTER schematic, which per\n"
                 "    ADR-0002 is the machine artifact and need not be pretty.\n")
    _project(root, "board-bravo", OTHER)
    (p / "03_tscircuit" / "kicad").mkdir(parents=True, exist_ok=True)
    (p / "03_tscircuit" / "kicad" / "board.kicad_sch").write_text("(sch)")
    r_ok = must_pass(run([PY, WAIVER_PROV, root]),
                     "an unqualified basename that resolves under the project")
    not_contains(r_ok.out, "W-REFS", "an unqualified but resolvable ref is ok")
    (p / "03_tscircuit" / "kicad" / "board.kicad_sch").unlink()
    must_fail(run([PY, WAIVER_PROV, root]),
              "a refs target that resolves nowhere", "W-REFS")


# ==========================================================================
# W-MACHINE — refdes_waiver.json, the file the generator writes for itself
# ==========================================================================

@test("M1: a refdes the GENERATOR waived for itself with no project-side "
      "evidence is named, and --strict-machine fails it", kind="known_bad")
def t_machine_waiver_unbacked_is_named_and_strict_fails():
    """`generate_board_generic.py` writes `04_kicad/refdes_waiver.json` when its
    silk placer finds no slot, and `policy_audit.py:793` then READS it and skips
    every refdes in it while grading P-SILK-REF. Checker and checked share a
    method — canon M1 from the inside — and the 04_kicad contract calls that
    file evidence-backed. pluto-rx2-8way's own P-SILK-REF waiver says so in
    writing and asks for exactly this check.

    PRE-FIX: exit 0, and the file is not read by any provenance check at all.
    """
    d = tmpdir("t1wev_mach_")
    root = d / "projects"
    p = _project(root, "board-alpha", OTHER)
    _project(root, "board-bravo",
             "- id: R-POUR\n  refs: [VBUS1]\n  why: >-\n"
             "    MEASURED on THIS board: VBUS1 is a continuous 0.8 mm F.Cu\n"
             "    run at 1oz over 9 mm; IPC-2221 external gives 2.03 A at a\n"
             "    10 C rise and the ILIM-bounded worst case is 2.51 A.\n")
    (p / "04_kicad").mkdir(parents=True, exist_ok=True)
    (p / "04_kicad" / "refdes_waiver.json").write_text(json.dumps(["C_MCU7"]))
    r = must_pass(run([PY, WAIVER_PROV, root]),
                  "an unbacked machine waiver under the default ceiling")
    contains(r.out, "UNBACKED", "it must be named on every run")
    contains(r.out, "C_MCU7", "by refdes")
    contains(r.out, "0/1 refdes", "with a denominator")
    r2 = run([PY, WAIVER_PROV, root, "--strict-machine"])
    must_fail(r2, "an unbacked machine waiver under --strict-machine",
              "W-MACHINE")


@test("a machine-waived refdes that the project DOES evidence is reported "
      "BACKED")
def t_machine_waiver_backed_passes():
    """THE OTHER HALF, and it is the shape pluto-rx2-8way already ships: its
    refdes_waiver.json holds C_MCU7 and R_CC1 and its P-SILK-REF waiver names
    both in `refs:` with the measured regression that explains them. The check
    must rank that above the unevidenced case or it is just a counter."""
    d = tmpdir("t1wev_mach2_")
    root = d / "projects"
    p = _project(root, "board-alpha",
                 "- id: P-SILK-REF\n  refs: [C_MCU7, R_CC1]\n  why: >-\n"
                 "    62 of 64 refdes print on silk; C_MCU7 and R_CC1 are on\n"
                 "    F.Fab only. Both are JLC-assembled 0402s on a CPL row in\n"
                 "    the 2.2 mm-pitch sub-MCU band, so no hand-fitting\n"
                 "    operator reads either label.\n")
    _project(root, "board-bravo", OTHER)
    (p / "04_kicad").mkdir(parents=True, exist_ok=True)
    (p / "04_kicad" / "refdes_waiver.json").write_text(
        json.dumps(["C_MCU7", "R_CC1"]))
    r = must_pass(run([PY, WAIVER_PROV, root, "--strict-machine"]),
                  "backed machine waivers under --strict-machine")
    contains(r.out, "2/2 refdes", "both must be counted BACKED")
    not_contains(r.out, "UNBACKED   W-MACHINE", "neither is a finding")


@test("the machine ceiling fails a NEW unevidenced generator waiver",
      kind="known_bad")
def t_machine_ceiling_catches_a_new_unbacked_waiver():
    """The ratchet, in the direction that matters. The existing fleet debt is a
    named list under the ceiling; the moment the generator waives one MORE
    refdes for itself, the count rises above the committed ceiling and fails.
    Adoption cannot go backwards even though day one is not a wall.

    PRE-FIX: exit 0.
    """
    d = tmpdir("t1wev_mach3_")
    root = d / "projects"
    p = _project(root, "board-alpha", OTHER)
    _project(root, "board-bravo", DISTINCT)
    (p / "04_kicad").mkdir(parents=True, exist_ok=True)
    (p / "04_kicad" / "refdes_waiver.json").write_text(
        json.dumps(["R_A", "R_B", "R_C"]))
    must_pass(run([PY, WAIVER_PROV, root, "--machine-ceiling", "3"]),
              "three unbacked waivers against a ceiling of 3")
    r = run([PY, WAIVER_PROV, root, "--machine-ceiling", "2"])
    must_fail(r, "three unbacked waivers against a ceiling of 2", "W-FLOOR")
    contains(r.out, "may only be edited DOWN", "the direction is stated")


@test("a malformed refdes_waiver.json FAILS rather than being read as an "
      "empty waiver list", kind="known_bad")
def t_malformed_machine_waiver_file_fails():
    """The zero-denominator shape (canon M-COVER) specific to this file: a
    `{}` or a truncated write reads as 'nothing waived', which is
    indistinguishable from a board where every refdes printed. policy_audit
    would crash or skip; this names it.

    PRE-FIX: exit 0.
    """
    d = tmpdir("t1wev_mach4_")
    root = d / "projects"
    p = _project(root, "board-alpha", OTHER)
    _project(root, "board-bravo", DISTINCT)
    (p / "04_kicad").mkdir(parents=True, exist_ok=True)
    (p / "04_kicad" / "refdes_waiver.json").write_text('{"C_MCU7": "no slot"}')
    must_fail(run([PY, WAIVER_PROV, root]),
              "a refdes_waiver.json that is not a JSON list", "W-MACHINE")


# ==========================================================================
# OWED — the coverage denominator, and why absence is named rather than red
# ==========================================================================

@test("an entry with a typed measurement and no `evidence:` block is OWED, "
      "named, and does not fail under the ceiling")
def t_owed_is_named_not_red():
    """THE ADOPTION PATTERN (the one G-VACUOUS used: 5/32 declared, 27 named as
    OWED, floor pinned). 22 of 22 fleet entries are OWED on the day this landed.
    A gate that reds all 22 gets disabled inside a week, and a gate that says
    nothing is how the incident survived — so every OWED entry is printed BY
    NAME with the reason, counted against a committed ceiling, and the run
    exits 0."""
    r = must_pass(run([PY, WAIVER_PROV, _pair(
        "- id: P-ADJ\n  refs: [PE42482A-X]\n  why: >-\n" + INCIDENT_WHY)]),
        "an OWED entry under the ceiling")
    contains(r.out, "OWED", "OWED must be printed")
    contains(r.out, "P-ADJ", "with the entry named")
    contains(r.out, "leans on a typed measurement",
             "and the reason it is owed")
    contains(r.out, "EVIDENCE COVERAGE", "with a coverage denominator")


@test("the OWED ceiling fails a NEW waiver written with a typed number",
      kind="known_bad")
def t_owed_ceiling_catches_a_new_typed_waiver():
    """The other monotone half. Existing debt is named; the NEXT hand-typed
    measurement is a hard fail today.

    PRE-FIX: exit 0.
    """
    root = _pair("- id: P-ADJ\n  refs: [PE42482A-X]\n  why: >-\n"
                 + INCIDENT_WHY)
    must_pass(run([PY, WAIVER_PROV, root, "--owed-ceiling", "2"]),
              "two OWED entries against a ceiling of 2")
    r = run([PY, WAIVER_PROV, root, "--owed-ceiling", "1"])
    must_fail(r, "two OWED entries against a ceiling of 1", "W-FLOOR")
    contains(r.out, "may only be edited DOWN", "the direction is stated")


# ==========================================================================
# END TO END, on real copper and the real fleet
# ==========================================================================

@test("the real board, end to end: a pcbnew citation regenerates and is CITED")
def t_the_real_board_end_to_end_pcbnew_citation_regenerates():
    """The `printf` fixtures prove the diff machinery. This proves the thing
    that has to work in practice: a real pcbnew one-liner, against a real board
    in this tree, run by the gate from the repo root, producing a number the
    gate then diffs.

    It is SELF-MEASURING rather than pinned to a constant. C_SW1 -> U_SW.8 is
    2.873 mm on pluto-rx2-8way today (it was 2.62-claimed / 3.085-actual at
    c07aaf2, which is the incident), and that board is still in flight — pinning
    2.873 here would make this test a tripwire on a sibling agent's placement
    work rather than a test of the gate. So the test measures the pair itself,
    writes THAT into `output:`, and asserts the gate agrees; then perturbs the
    declared number by 0.5 mm and asserts it disagrees. Both halves, same
    board, one property changed.

    ORACLE 3 under tests/README.md "Which real bytes may a fixture read?" — a
    LIVE `04_kicad/` board, legal here because the assertion tolerates the board
    being regenerated: no number is pinned, only the agreement between what the
    gate regenerates and what the fixture wrote down a moment earlier. If the
    board is absent (it is generated, not committed) the test grades the LADDER
    instead of skipping, so this can never become a silent no-op."""
    board = (FLEET / "pluto-rx2-8way" / "04_kicad" / "pluto_rx2_8way.kicad_pcb")
    if not board.is_file():
        # The board is generated, not committed. Absence is the LADDER's own
        # case, so assert that instead of skipping silently.
        r = must_pass(run([PY, WAIVER_PROV, _pair(_incident(
            "2.873", measured="2.873",
            extra=f"      requires: [{board.relative_to(ROOT)}]\n"))]),
            "the ladder when the real board is absent")
        contains(r.out, "declared input absent here",
                 "an absent board must downgrade, not fail")
        return

    measure = (
        "/usr/bin/python3 -c \"import pcbnew, math; "
        "b = pcbnew.LoadBoard('projects/pluto-rx2-8way/04_kicad/"
        "pluto_rx2_8way.kicad_pcb'); "
        "d = {(f.GetReference(), p.GetNumber()): p.GetPosition() "
        "for f in b.GetFootprints() for p in f.Pads()}; "
        "a = d[('C_SW1', '1')]; c = d[('U_SW', '8')]; "
        "print(round(math.hypot(pcbnew.ToMM(a.x - c.x), "
        "pcbnew.ToMM(a.y - c.y)), 3))\"")
    got = subprocess.run(measure, shell=True, cwd=str(ROOT),
                         capture_output=True, text=True, timeout=300)
    check(got.returncode == 0,
          f"the fixture's own pcbnew measurement failed: {got.stderr[-300:]}")
    val = [l for l in got.stdout.splitlines() if l.strip()][-1].strip()
    entry = (f"- id: P-ADJ-UNREACHED\n"
             f"  refs: [PE42482A-X]\n"
             f"  why: >-\n{INCIDENT_WHY}"
             f"  evidence:\n"
             f"    - claim: C_SW1.1 -> U_SW.8, pad centre to pad centre, the "
             f"measure policy_audit.py:412 defines for P-ADJ\n"
             # A LITERAL block scalar, because the command contains ": " and a
             # plain YAML scalar would be parsed as a nested mapping. Worth
             # stating in the contract: any real pcbnew one-liner needs `|-`.
             f"      command: |-\n        {measure}\n"
             f"      output: \"{val}\"\n"
             f"      requires: [pcbnew, projects/pluto-rx2-8way/04_kicad/"
             f"pluto_rx2_8way.kicad_pcb]\n")
    r = must_pass(run([PY, WAIVER_PROV, _pair(entry), "--repo-root", ROOT]),
                  f"a live pcbnew citation of {val} mm")
    contains(r.out, "CITED", "the live measurement must be reported CITED")
    contains(r.out, f"regenerated {val}", "with the regenerated number")

    # ONE PROPERTY CHANGED: the declared number moves 0.5 mm and nothing else.
    wrong = f"{float(val) - 0.5:.3f}"
    r2 = run([PY, WAIVER_PROV,
              _pair(entry.replace(f"output: \"{val}\"",
                                  f"output: \"{wrong}\"")),
              "--repo-root", ROOT])
    must_fail(r2, f"a live pcbnew citation typed {wrong} against {val}",
              "W-REGEN")


@test("the REAL fleet is graded with a denominator, and the machine-waiver "
      "exposure is measured on every run")
def t_real_fleet_is_measured():
    """The denominators are the deliverable, so they are re-measured rather than
    quoted. Measured 2026-07-29 at main tip: 22 waiver entries across 5 boards,
    22 OWED / 0 CITED, and 2 of 11 refdes in `04_kicad/refdes_waiver.json`
    carrying a project-side evidenced entry (pluto-rx2-8way's C_MCU7 + R_CC1).

    The EXIT CODE is deliberately not asserted: the fleet carries one
    pre-existing W-FOREIGN finding (crow-recorder-central-v2's S-OCCL names
    crow-mic-pod-v2 with no `derived_from`), which is HEAD's finding, not this
    schema's — measured identical before and after."""
    r = run([PY, WAIVER_PROV, FLEET, "--no-regen"])
    contains(r.out, "waiver(s) graded", "the fleet run carries a denominator")
    contains(r.out, "EVIDENCE COVERAGE", "and a coverage line")
    contains(r.out, "MACHINE WAIVERS", "and the M1 exposure line")
    check("22 of 22" in r.out or "OWED" in r.out,
          "the OWED set must be enumerated for the real fleet")
    # The generator's own waiver file is now IN SCOPE fleet-wide, which is the
    # single structural change here. Assert the total is nonzero so a rename of
    # refdes_waiver.json cannot quietly empty the check (canon M-COVER).
    mach = [l for l in r.out.splitlines() if l.startswith("MACHINE WAIVERS")]
    check(len(mach) == 1, f"expected one MACHINE WAIVERS line, got {mach}")
    check("/0 refdes" not in mach[0],
          f"the machine-waiver denominator collapsed to zero: {mach[0]} — "
          f"either every 04_kicad/refdes_waiver.json vanished or the path "
          f"moved, and a zero denominator is a FAIL, never a pass")


if __name__ == "__main__":
    sys.exit(main())
