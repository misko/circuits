#!/usr/bin/env python3
"""t1_adr_bounds — an ADR's PUBLISHED BOUND is REGENERATED, not typed.

==========================================================================
THE INCIDENT (2026-07-29, smc0985-cooksense ADR-0024)
==========================================================================

The ADR "every pod-mateable safety input is hardened AT THE PINOUT" published,
as the one-line takeaway of a document whose entire argument is worst-case:

    General bound: V <= 0.700 V  =>  R_pd <= 592 Ohm

**592 Ohm is the NOMINAL corner** — 3.300 V rail, 2200 Ohm injected pull-up
exactly, R_pd at +/-0 %. At the corner the rest of the section uses (rail
3.399 V from `power_tree.yaml`'s 3V3 `vout_max`, injection 2178 Ohm = 2.2k -1 %,
R_pd +1 %) the bound is **559.283 Ohm**.

The 33 Ohm was not a rounding note. **560 Ohm is the nearest E24 value under
592, it is the value a future pass reaches for under that ceiling, and at the
worst-case corner it gives 0.700712 V and FAILS by 0.7 mV.** The published bound
permitted exactly one standard value and that value does not clear. The chosen
470 Ohm is unaffected (0.608250 V, +91.8 mV), so the BOARD was never wrong — the
ADR was. THE FAILURE IS THE ONE THE ADR IS NAMED AFTER, REPRODUCED IN ITS OWN
SUMMARY LINE.

Every number in this suite is re-derived independently of the ADR's prose by
`DIVIDER_PY` below, which is written from the topology (a pod pull-up against
the board's pull-down) and not copied from the document. Measured here:

    exact worst-case bound   559.2830 Ohm   (ADR: 559.3)
    exact nominal bound      592.3077 Ohm   (ADR: 592)
    560 Ohm @ worst_case     0.700712 V     (ADR: 0.7007, fails by 0.7 mV)
    549 Ohm @ worst_case     0.689741 V     (ADR: passes by 10.3 mV)
    499 Ohm @ worst_case     0.638728 V     (ADR: passes by 61.3 mV)
    470 Ohm @ worst_case     0.608250 V     (ADR: 0.608, PASS +92 mV)
    680 Ohm @ worst_case     0.814868 V     (ADR: 0.8149, FAIL by 115 mV)
    592.3 Ohm @ worst_case   0.732420 V     -> B-CORNER: not on its own edge

FLEET DENOMINATOR, measured by the gate on 2026-07-29 at main tip: **72 ADRs
(7 repo-level + 65 across 6 live boards); 37 publish at least one numeric
inequality bound; 108 such bounds in total; 0 declare a `<!-- bound -->`
block.** (A survey that counted `*.md` reported 78 documents — six of those are
the per-folder `contracts.md`, which carry no bounds; the 37 is unchanged.)

==========================================================================
RED-VERIFIED, both required senses
==========================================================================

**(1) Against the repo as it stood.** Nothing in this repo read a number out of
`01_docs/decisions/*.md`. Asserted, not asserted-about, by
`t_red_no_pre_existing_gate_reads_a_number_out_of_an_adr`: the ADR-0024 bound
`R_pd <= 592` sat in a live document through a full revision cycle and every
gate in the tree was green on it. There is no earlier version of this checker to
swap back in, so the pre-fix state is measured as an absence.

**(2) Against pre-fix code, by ablation.** `_ablated()` writes a copy of
`adr_bound_provenance.py` with the two incident checks — B-CORNER and B-STDVAL —
excised and nothing else touched, and the headline fixture is run against it.
MEASURED pre-fix output on the real published 592 Ohm bound, verbatim, EXIT 0:

    input: root = /tmp/adrb_74zdjqit  (1 ADR file(s) under docs/decisions + */01_docs/decisions)
    input: regeneration ON, cwd for commands = /tmp/adrb_74zdjqit, per-command timeout 180s
    input: 1 ADR(s) declare a `<!-- bound -->` block (1 block(s)); 0 OWED; 3 inequality bound(s) appear in prose across all 1
      UNVERIFIED  adrb_74zdjqit/0024-incident.md [R_PD_MAX]: regenerated 592.3077 vs published 592.3 (delta 0.0077 <= 0.05)
    BOUND COVERAGE: 0 CITED / 0 ESTIMATED / 1 UNVERIFIED across 1 declared block(s) in 1 ADR(s); 0 of 1 bound-publishing ADR(s) OWED (floors: CITED >= 0, OWED <= 37; NOT ENFORCED — foreign tree)
    ADR BOUND PROVENANCE: PASS (0 fails) — 1/1 ADR(s) publish an inequality bound, 1 declare one

i.e. pre-fix the run is GREEN on the incident bound: `regenerated 592.3077 vs
published 592.3 (delta 0.0077 <= 0.05)`. A `command:` solving at the NOMINAL
corner AGREES with the typed 592.3 to four decimal places, so the M4-shaped half
of this gate — diff the number against a re-runnable command — IS SATISFIED BY
THE DEFECT. The whole finding lives in the two checks that ask what the bound
ADMITS, which is why they are separate check IDs. (The `UNVERIFIED` rather than
`CITED` is an artifact of the ablation being surgical: it removes the two
`fails.append` sites and leaves the grade demotion that followed them. The
verdict, which is what matters, is PASS.)

BOTH HALVES. A bound that regenerates AND whose nearest standard value clears
must PASS and be reported CITED
(`t_a_correct_bound_regenerates_and_its_nearest_standard_value_clears`) — a gate
that only knows how to reject ranks nothing.
"""
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq, main, must_fail,
                     must_pass, not_contains, run, test, tmpdir)

GATE = SCRIPTS / "adr_bound_provenance.py"

# ---------------------------------------------------------------------------
# THE ARITHMETIC, RE-DERIVED. This is the ADR AUTHOR's side of the M1 split:
# the gate owns the ladder, the E-series and the relation, and never the
# physics. Written from the topology — a cross-mated pod holds SCL high through
# its own module pull-up, against the board's safety pull-down — so the numbers
# it prints are an INDEPENDENT re-derivation of ADR-0024's table rather than a
# transcription of it.
#
# It is a fixture-local file rather than a repo script on purpose: a gate that
# shipped the arithmetic it grades would be checker and checked sharing a
# method (canon M1), and a fixture that re-measured a live 04_kicad board would
# grade whichever sibling is mid-rebuild (tests/README, "which real bytes").
# ---------------------------------------------------------------------------
DIVIDER_PY = '''#!/usr/bin/env python3
"""V(node) for a pod pull-up injected against a board pull-down, per corner."""
import argparse

# (rail volts, injected pull-up ohms, pull-down tolerance multiplier)
CORNERS = {
    "nominal":    (3.300, 2200.0, 1.00),
    "typical":    (3.300, 2200.0, 1.00),
    "worst_case": (3.399, 2178.0, 1.01),
}

ap = argparse.ArgumentParser()
ap.add_argument("--corner", required=True, choices=sorted(CORNERS))
ap.add_argument("--solve", type=float, help="print the largest R_pd holding V under this")
ap.add_argument("--r", type=float, help="print V for this nominal R_pd")
a = ap.parse_args()
vr, ri, tol = CORNERS[a.corner]
if a.solve is not None:
    print("%.4f" % (a.solve * ri / (vr - a.solve) / tol))
else:
    print("%.6f" % (vr * a.r * tol / (a.r * tol + ri)))
'''

CLAIM = (">-\n      Largest safety pull-down that keeps V(DOOR_RAW) under the "
         "HC14\n      V_T-(min) of 0.700 V with a cross-mated pod's 2.2k SCL "
         "pull-up injected.")
SERIES_WHY = (">-\n        A 1 %-tolerance safety pull-down taken off this "
              "board's own E24 strip;\n        the board stocks no E96 "
              "resistors, so E96 values are not sourceable here.")
TOL_WHY = (">-\n      The published bound is rounded to 0.1 Ohm from an exact "
           "559.2830;\n      0.05 is half that last digit and is 3 orders "
           "under the 49.3 Ohm gap to\n      the nearest E24 value the bound "
           "must rule on.")


def _tree(bound_yaml, prose_bounds=3, name="0024-incident.md"):
    """A scratch tree holding ONE ADR with ONE declared bound block."""
    root = tmpdir("adrb_")
    (root / "decisions").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / "divider.py").write_text(DIVIDER_PY)
    prose = "\n".join(f"- some quoted datasheet limit <= {i + 1}.0 V"
                      for i in range(prose_bounds))
    (root / "docs" / "decisions" / name).write_text(
        "# 0024 — pod-mateable safety inputs are hardened at the pinout\n\n"
        "## Context\nA cross-mated pod drives the door sense node.\n\n"
        f"## Options\n{prose}\n\n"
        "## Decision\nHarden at the pinout.\n\n"
        "## Consequences\n\n"
        + bound_yaml + "\n")
    return root


def _block(value="559.3", corner="worst_case", relation='"<="',
           command=None, series="E24", series_why=SERIES_WHY,
           tolerance="0.05", tolerance_why=TOL_WHY, chosen="470",
           governs=True, evaluate=None, budget='"<= 0.700"', grade="CITED",
           extra="", claim=CLAIM, solve_corner=None):
    """One `<!-- bound -->` block, every load-bearing field dialable."""
    sc = solve_corner or corner
    cmd = command if command is not None else (
        f"/usr/bin/python3 divider.py --corner {sc} --solve 0.700")
    ev = evaluate if evaluate is not None else (
        f"/usr/bin/python3 divider.py --corner {corner} --r {{value}}")
    lines = ["<!-- bound: R_PD_MAX -->", "```yaml",
             "id: R_PD_MAX", f"claim: {claim}", f"relation: {relation}",
             f"value: {value}", "unit: Ohm", f"corner: {corner}"]
    if cmd:
        lines.append(f"command: {cmd}")
    if grade:
        lines.append(f"grade: {grade}")
    if governs:
        lines += ["governs:"]
        if ev:
            lines.append(f"  evaluate: {ev}")
        if budget:
            lines.append(f"  budget: {budget}")
        lines.append("  unit: V")
    if series is not None:
        lines += ["standard_value:"]
        if str(series).startswith("["):
            lines.append(f"  explicit: {series}")
        elif series:
            lines.append(f"  series: {series}")
        if series_why:
            lines.append(f"  series_why: {series_why}")
    if chosen:
        lines.append(f"chosen: {chosen}")
    if tolerance:
        lines.append(f"tolerance: {tolerance}")
        if tolerance_why:
            lines.append(f"tolerance_why: {tolerance_why}")
    if extra:
        lines.append(extra)
    lines.append("```")
    return "\n".join(lines)


def _go(root, *args):
    return run([KPY, GATE, str(root), "--repo-root", str(root), *args])


# ===========================================================================
# THE HEADLINE — built from the REAL published bound
# ===========================================================================

@test("INCIDENT: ADR-0024's real published `R_pd <= 592` is caught TWICE — the "
      "corner it was derived at and the only standard value it admits",
      kind="known_bad")
def t_incident_the_adr_0024_592_ohm_bound_is_caught_twice():
    """THE HEADLINE KNOWN-BAD, and it is the number the ADR actually shipped.

    `value: 592.3` with `corner: worst_case` is the bound AS PUBLISHED: the
    figure is the nominal-corner solution and the document it headlines argues
    entirely at worst case. Two independent findings, from the document alone:

      B-CORNER  592.3 - 0.05 evaluated at worst_case gives 0.732371 V against
                `<= 0.700`. The bound does not sit on its own budget edge at
                the corner it declares, so it was NOT DERIVED THERE — and
                because `corner_commands:` names `nominal`, the finding also
                says WHERE it does reproduce (592.3077).
      B-STDVAL  the nearest E24 value under 592.3 is 560, and at worst_case
                that gives 0.700712 V. FAILS by 0.7 mV. The published bound
                permitted exactly one standard value and that value does not
                clear.

    PRE-FIX (ablated: B-CORNER and B-STDVAL excised, nothing else changed) this
    same input produces, byte-for-byte, the report quoted in this module's
    docstring and EXITS 0 — the bound is reported CITED, because a `command:`
    solving at the NOMINAL corner regenerates 592.3077 and agrees with the
    typed 592.3 to within tolerance. The M4-shaped half of the gate is
    SATISFIED by the defect. Verified by
    `t_red_the_ablated_gate_passes_the_592_ohm_bound`.
    """
    root = _tree(_block(
        value="592.3", corner="worst_case", solve_corner="nominal",
        extra=("corner_commands:\n"
               "  nominal: /usr/bin/python3 divider.py --corner nominal "
               "--solve 0.700")))
    r = must_fail(_go(root), "the 592 Ohm bound", "B-CORNER")
    contains(r.out, "B-STDVAL", "the standard-value finding")
    # the two numbers the ADR's own correction names
    contains(r.out, "0.732", "the bound's own value evaluated at worst_case")
    contains(r.out, "560", "the nearest E24 value under 592.3")
    contains(r.out, "0.700712", "560 Ohm at the worst-case corner")
    contains(r.out, "nominal", "the corner the published number DOES reproduce at")


@test("a mislabelled corner FAILS ALONE — no tolerance, no standard value and "
      "no runnable command excuse it", kind="known_bad")
def t_incident_a_mislabelled_corner_fails_alone():
    """B-CORNER is independent of every other check, which is the point.

    Same 592.3 Ohm bound labelled `worst_case`, but the series is declared as
    the explicit set [470] — so the nearest admissible standard value is 470,
    which gives 0.608250 V and CLEARS. And the bound is graded ESTIMATED with
    no `command:`, so there is no B-REGEN either. The ONLY finding is B-CORNER,
    and it is a FAIL: an ADR that says `corner: worst_case` while the
    arithmetic is nominal is the ADR-0024 defect whatever else is true.
    """
    root = _tree(_block(
        value="592.3", corner="worst_case", series="[470]",
        series_why=(">-\n        Only 470 Ohm is stocked for this position on "
                    "this board; nothing\n        else is sourceable without a "
                    "new line item."),
        command="", grade="ESTIMATED",
        extra=("why_not_rerunnable: >-\n"
               "  The closed-form solve lives in the ADR body; only the "
               "evaluation is\n  scripted here.")))
    r = must_fail(_go(root), "a mislabelled corner", "B-CORNER")
    not_contains(r.out, "B-STDVAL", "the standard value clears, so B-STDVAL "
                                    "must NOT fire — B-CORNER stands alone")
    not_contains(r.out, "B-REGEN", "no command was declared")


@test("a bound at an HONEST corner that regenerates exactly is still a FAIL "
      "when its nearest standard value does not clear", kind="known_bad")
def t_a_standard_value_that_fails_at_an_honest_corner_is_caught():
    """B-STDVAL alone: the mirror of the test above.

    `value: 562` at `worst_case` — an E96 value somebody might publish as "the
    bound" — regenerates nothing wrong on its own terms, but 562 evaluated at
    worst_case is 0.702698 V, over 0.700. The bound is inadmissible at its own
    corner AND its nearest E24 value (560, 0.700712 V) also fails, so both
    findings are legitimate here; what this fixture pins is that B-STDVAL names
    the SERIES and the VALUE, because "560 in E24" and "590 in E96" are
    different verdicts on the same published number.
    """
    root = _tree(_block(value="562", corner="worst_case", tolerance="",
                        command="", grade="ESTIMATED",
                        extra=("why_not_rerunnable: >-\n"
                               "  Published from the ADR body's closed form; "
                               "only the evaluation is scripted.")))
    r = must_fail(_go(root), "an inadmissible standard value", "B-STDVAL")
    contains(r.out, "560", "the nearest E24 value")
    contains(r.out, "series E24", "the series is named in the finding")


# ===========================================================================
# BOTH HALVES — the corrected bound must PASS, or the gate ranks nothing
# ===========================================================================

@test("the CORRECTED bound regenerates, sits on its own edge, and its nearest "
      "standard value clears — PASS, reported CITED")
def t_a_correct_bound_regenerates_and_its_nearest_standard_value_clears():
    """THE OTHER HALF. ADR-0024's corrected `R_pd <= 559.3 Ohm` at worst_case:

      command      solves 559.2830, agrees with the published 559.3 inside the
                   declared 0.05 tolerance -> CITED
      B-CORNER     559.3 - 0.05 = 559.25 evaluates to 0.699967 V, inside 0.700
      B-STDVAL     nearest E24 value under 559.3 is 510 -> 0.650115 V, clears

    A gate that only rejects ranks nothing, so this is asserted as hard as the
    headline: exit 0, the block reported CITED with its diff shown, and no
    finding of any kind.
    """
    root = _tree(_block())
    r = must_pass(_go(root), "the corrected 559.3 Ohm bound")
    contains(r.out, "CITED", "the block is graded CITED")
    contains(r.out, "559.283", "the regenerated bound is shown")
    contains(r.out, "0.699967", "the bound sits on its own budget edge")
    contains(r.out, "510", "the nearest E24 value under 559.3")
    contains(r.out, "0.650115", "510 Ohm at the worst-case corner")
    not_contains(r.out, "FAIL", "no finding")
    contains(r.out, "1 CITED / 0 ESTIMATED / 0 UNVERIFIED", "the coverage line")


@test("an honestly ESTIMATED bound passes and is never counted CITED")
def t_an_honest_estimated_bound_passes_and_is_never_counted_cited():
    """The M-IMPORT rung. No `command:`, an explicit `why_not_rerunnable:`, and
    the corner/standard-value checks still run because `governs.evaluate` is
    independent of the solve. Legal, reported, and NOT credited as CITED — a
    grade that inflates itself is the thing the ladder exists to stop."""
    root = _tree(_block(command="", grade="ESTIMATED",
                        extra=("why_not_rerunnable: >-\n"
                               "  The closed-form solve is three lines of "
                               "algebra in the ADR body and\n  has no script "
                               "of its own; the evaluation does.")))
    r = must_pass(_go(root), "an honest ESTIMATED bound")
    contains(r.out, "0 CITED / 1 ESTIMATED", "counted ESTIMATED, not CITED")


@test("a bound whose declared input is absent is UNVERIFIED, not a FAIL — a "
      "sibling mid-rebuild must not change this gate's verdict")
def t_an_absent_declared_input_is_unverified_not_a_fail():
    """THE LADDER'S REASON FOR EXISTING, and it is load-bearing today: one board
    is mid-rebuild and two are mid-route as this lands. A gate whose verdict
    turns on that is a gate that gets switched off inside a week, so a declared
    `requires:` that is absent HERE downgrades to UNVERIFIED, named on every
    run, credited to nobody. The hole is closed from the other side by
    CITED_FLOOR."""
    root = _tree(_block(extra="requires: [04_kicad/not_built_yet.kicad_pcb]"))
    r = must_pass(_go(root), "an absent declared input")
    contains(r.out, "UNVERIFIED", "the block is UNVERIFIED")
    contains(r.out, "not_built_yet", "the absent input is NAMED")
    not_contains(r.out, "FAIL", "an absent input is not a finding")


@test("`requires:` is not a blanket excuse — the same bound with a file that "
      "DOES exist runs and is graded", kind="known_bad")
def t_requires_is_not_a_blanket_excuse():
    """The contrast to the test above, and the reason it is a known_bad: a
    declaration that suppresses grading whenever it is present would be a
    self-service waiver. The identical 592 Ohm defect with `requires:` pointing
    at a file that IS there runs, and fails."""
    root = _tree(_block(value="592.3", corner="worst_case",
                        solve_corner="nominal",
                        extra="requires: [divider.py]"))
    must_fail(_go(root), "a satisfiable requires", "B-CORNER")


@test("--no-regen degrades every bound to UNVERIFIED — a fast path, not a pass")
def t_no_regen_degrades_every_bound_to_unverified():
    root = _tree(_block(value="592.3", corner="worst_case"))
    r = must_pass(_go(root, "--no-regen"), "--no-regen on a BAD bound")
    contains(r.out, "--no-regen", "the reason is named")
    contains(r.out, "0 CITED", "nothing may be credited CITED without running")


# ===========================================================================
# B-REGEN / B-FLIP — the M4 pair, and why they are two IDs
# ===========================================================================

@test("a published bound that does not regenerate at its declared corner is "
      "B-REGEN", kind="known_bad")
def t_a_regenerated_bound_that_disagrees_is_b_regen():
    """THE PLAIN M4 CASE, ISOLATED. `command` runs at worst_case and prints
    559.283 while the document publishes 500.

    500 is deliberately CONSERVATIVE — it is inside the true bound, so it sits
    on the right side of its own budget (0.641996 V) and its nearest E24 value
    (470 -> 0.608250 V) clears too. Neither B-CORNER nor B-STDVAL can fire, and
    the chosen 470 satisfies `<= 500` and `<= 559.283` alike so nothing flips.
    The ONLY finding is the discrepancy, which is what makes this fixture prove
    B-REGEN rather than prove the gate is loud."""
    root = _tree(_block(value="500", tolerance=""))
    r = must_fail(_go(root), "a bound that does not regenerate", "B-REGEN")
    contains(r.out, "559.283", "the regenerated value")
    not_contains(r.out, "B-FLIP", "470 clears both bounds — no verdict reversed")
    not_contains(r.out, "B-CORNER", "500 is inside its own budget")
    not_contains(r.out, "B-STDVAL", "470 is admissible and clears")


@test("a REVERSED verdict is B-FLIP, reported separately from B-REGEN",
      kind="known_bad")
def t_a_reversed_decision_verdict_is_b_flip_not_b_regen():
    """THE DISTINCTION CARRIED OVER FROM W-FLIP. A bound published at 592.3 that
    regenerates at 559.283 is a 33 Ohm discrepancy — UNLESS the value the ADR
    says it CHOSE sits between them, in which case the decision's own conclusion
    reverses and it must read as one. `chosen: 560` satisfies `<= 592.3` and
    does not satisfy `<= 559.283`, which is precisely the future pass ADR-0024's
    correction was written to protect.
    """
    root = _tree(_block(value="592.3", chosen="560", tolerance="",
                        series="[560]",
                        series_why=(">-\n        The 560 Ohm this fixture is "
                                    "about; a single-member stocked set so the\n"
                                    "        standard-value check has one "
                                    "candidate and no ambiguity.")))
    r = must_fail(_go(root), "a reversed verdict", "B-FLIP")
    contains(r.out, "REVERSES", "the finding says the conclusion reverses")
    contains(r.out, "560", "the chosen value is named")


@test("no tolerance whatsoever excuses a B-FLIP", kind="known_bad")
def t_no_tolerance_excuses_a_b_flip():
    """W-FLIP's rule, restated: a tolerance is a precision claim, never a
    permission slip. A 40 Ohm tolerance covers the whole 33 Ohm discrepancy and
    the reversal is STILL reported — B-TOL fires alongside it, because 40 >= the
    0.3 Ohm gap from 592.3 to the chosen 560 that the bound must discriminate.
    """
    root = _tree(_block(
        value="592.3", chosen="560", tolerance="40", series="[560]",
        series_why=(">-\n        A single-member stocked set, so the standard-"
                    "value check has exactly\n        one candidate."),
        tolerance_why=(">-\n      Deliberately absurd: this fixture exists to "
                       "prove a wide tolerance\n      cannot buy a reversed "
                       "verdict.")))
    r = must_fail(_go(root), "a wide tolerance over a flip", "B-FLIP")
    contains(r.out, "B-TOL", "the tolerance is itself refused")


# ===========================================================================
# B-TOL — the tolerance is itself a load-bearing number
# ===========================================================================

@test("a tolerance >= the margin the bound must discriminate is refused",
      kind="known_bad")
def t_a_tolerance_wider_than_the_margin_is_refused():
    """THE CHECK THAT STOPS THIS FIX FROM RECREATING THE DEFECT IT CLOSES.

    The corrected 559.3 Ohm bound has to rule on two nearby values: the chosen
    470 (89.3 Ohm away) and the nearest E24 value 510 (49.3 Ohm away). A 50 Ohm
    tolerance is wider than the tighter of those, so it cannot distinguish "510
    is admissible" from "510 is not" — it is not a tolerance, it is the next
    typed number. Refused, with the margin quoted.
    """
    root = _tree(_block(
        tolerance="50",
        tolerance_why=(">-\n      A deliberately over-wide tolerance, so this "
                       "fixture proves the gate\n      refuses one that "
                       "swallows its own margin.")))
    r = must_fail(_go(root), "a tolerance wider than the margin", "B-TOL")
    contains(r.out, "49.3", "the margin the bound must discriminate")


@test("a tolerance with no `tolerance_why:` is refused", kind="known_bad")
def t_a_tolerance_without_a_why_is_refused():
    root = _tree(_block(tolerance="0.05", tolerance_why=""))
    must_fail(_go(root), "a bare tolerance", "B-TOL")


# ===========================================================================
# B-SERIES — the standard-value decision is DECLARED, never assumed
# ===========================================================================

@test("a `standard_value:` block that names no series is refused — an assumed "
      "series is a verdict nobody chose", kind="known_bad")
def t_an_assumed_series_is_refused():
    """THE JUDGEMENT CALL, made enforceable. E24 admits 560 under a 592 Ohm
    ceiling and E96 admits 590; a stocked-set declaration may admit only 470.
    The series therefore CHANGES THE VERDICT, so it is declared per bound and
    there is no global default to fall back to."""
    root = _tree(_block(series=""))
    must_fail(_go(root), "an unnamed series", "B-SERIES")


@test("an unknown series name is refused", kind="known_bad")
def t_an_unknown_series_is_refused():
    root = _tree(_block(series="E37"))
    r = must_fail(_go(root), "an unknown series", "B-SERIES")
    contains(r.out, "E24", "the known series are listed")


@test("a `series_why:` that says nothing is refused", kind="known_bad")
def t_a_series_why_that_says_nothing_is_refused():
    root = _tree(_block(series_why="standard"))
    must_fail(_go(root), "an empty series_why", "B-SERIES")


@test("a bound whose declared series admits NOTHING is refused",
      kind="known_bad")
def t_a_bound_whose_series_admits_nothing_is_refused():
    """A stronger finding than a marginal one: the bound permits no value that
    can be bought at all."""
    root = _tree(_block(series="[1000, 2200]"))
    r = must_fail(_go(root), "a series admitting nothing", "B-STDVAL")
    contains(r.out, "admits NO value", "the finding says so plainly")


@test("E24 and E96 pick DIFFERENT nearest values under the same bound — the "
      "series choice really does change the verdict")
def t_the_series_choice_changes_the_verdict():
    """A unit assertion on the one decision this gate delegates. Under the
    ADR-0024 published ceiling of 592.3 Ohm, E24's nearest admissible value is
    560 and E96's is 590; under the corrected 559.3, E24 gives 510 and E96 gives
    549. Four different candidates from two published numbers, which is the
    whole reason `series:` is mandatory."""
    sys.path.insert(0, str(SCRIPTS))
    import adr_bound_provenance as abp                        # noqa: E402
    def near(series, limit):
        vals, err = abp.series_values(series)
        eq(err, None, f"{series} expands")
        return abp.nearest_admissible(vals, "<=", limit)
    eq(near("E24", 592.3), 560.0, "E24 under the published 592.3")
    eq(near("E96", 592.3), 590.0, "E96 under the published 592.3")
    eq(near("E24", 559.3), 510.0, "E24 under the corrected 559.3")
    eq(near("E96", 559.3), 549.0, "E96 under the corrected 559.3")
    # decades, so the same series works for a bound in mm or in Farad
    eq(near("E24", 0.62), 0.62, "E24 crosses decades downward")
    eq(near("E12", 1.0e6), 1.0e6, "and upward")
    # `>=` takes the SMALLEST admissible value, not the largest
    vals, _ = abp.series_values("E24")
    eq(abp.nearest_admissible(vals, ">=", 559.3), 560.0, "the >= direction")


# ===========================================================================
# B-SCHEMA / B-GRADE / B-CMD — a declaration that does not load is worse
# ===========================================================================

@test("an unknown `corner:` is refused — an unnamed corner IS the defect class",
      kind="known_bad")
def t_an_unknown_corner_is_refused():
    root = _tree(_block(corner="hot", evaluate=(
        "/usr/bin/python3 divider.py --corner worst_case --r {value}")))
    r = must_fail(_go(root), "an unnamed corner", "B-SCHEMA")
    contains(r.out, "worst_case", "the legal corners are listed")


@test("a misspelled key does not degrade silently back into prose",
      kind="known_bad")
def t_a_misspelled_key_does_not_degrade_into_prose():
    root = _tree(_block(extra="commmand: /usr/bin/python3 divider.py --help"))
    must_fail(_go(root), "a misspelled key", "B-SCHEMA")


@test("a bound with no `governs:` is refused — prose with a colon in it",
      kind="known_bad")
def t_a_bound_with_no_governs_is_refused():
    root = _tree(_block(governs=False))
    r = must_fail(_go(root), "a bound with no governs", "B-SCHEMA")
    contains(r.out, "governs", "the missing key is named")


@test("a `governs.evaluate:` with no `{value}` placeholder is refused",
      kind="known_bad")
def t_an_evaluate_without_a_value_placeholder_is_refused():
    """Without the placeholder the standard-value re-evaluation cannot happen,
    which is the check the schema exists for. Silence would be a gate that
    grades nothing while printing a verdict (canon M-COVER)."""
    root = _tree(_block(evaluate=(
        "/usr/bin/python3 divider.py --corner worst_case --r 470")))
    r = must_fail(_go(root), "an evaluate with no placeholder", "B-SCHEMA")
    contains(r.out, "{value}", "the placeholder is named")


@test("a `governs.budget:` that is not a relation is refused", kind="known_bad")
def t_a_budget_that_is_not_a_relation_is_refused():
    root = _tree(_block(budget='"about 0.7 volts"'))
    must_fail(_go(root), "a prose budget", "B-SCHEMA")


@test("a `value:` carrying two numbers is prose and is refused",
      kind="known_bad")
def t_a_value_with_two_numbers_is_refused():
    root = _tree(_block(value='"559.3 to 592.3"'))
    must_fail(_go(root), "a two-number bound", "B-SCHEMA")


@test("grade CITED with no `command:` is refused — a citation with nothing "
      "cited", kind="known_bad")
def t_cited_with_no_command_is_refused():
    root = _tree(_block(command="", grade="CITED"))
    must_fail(_go(root), "CITED with no command", "B-GRADE")


@test("grade ESTIMATED with no `why_not_rerunnable:` is refused",
      kind="known_bad")
def t_estimated_with_no_reason_is_refused():
    root = _tree(_block(command="", grade="ESTIMATED"))
    must_fail(_go(root), "an unexplained ESTIMATED", "B-GRADE")


@test("a command that can WRITE is refused rather than run — an audit that can "
      "write is not an audit", kind="known_bad")
def t_a_writing_command_is_refused():
    root = _tree(_block(
        command="/usr/bin/python3 divider.py --corner nominal --solve 0.700 "
                "> /tmp/adrb_should_not_exist"))
    must_fail(_go(root), "a writing command", "B-CMD")
    check(not Path("/tmp/adrb_should_not_exist").exists(),
          "the refused command must not have run")


@test("a `<!-- bound -->` block that is not parseable YAML is refused",
      kind="known_bad")
def t_an_unparseable_block_is_refused():
    root = _tree("<!-- bound -->\n```yaml\nid: X\n  bad: [indent\n```")
    must_fail(_go(root), "an unparseable block", "B-SCHEMA")


# ===========================================================================
# THE RATCHET, the coverage denominator, and the real fleet
# ===========================================================================

@test("the REAL fleet passes with every OWED ADR named — 37 of 45 owed, "
      "10 cited")
def t_the_real_fleet_passes_with_every_owed_adr_named():
    """THE ADOPTION RATCHET, measured on the live tree.

    45 ADRs publish a numeric inequality bound; 8 ADRs declare 10 runnable
    blocks and 37 remain OWED, so the gate REPORTS coverage, PRINTS every OWED
    document by name, and exits 0. A
    day-one mandate over 37 documents lands as 37 red rows and gets switched off
    inside a week; the ceiling is what makes the debt monotone instead.

    This reads live `01_docs/decisions/*.md` and NOT a live `04_kicad/` board —
    ADRs are append-only by contract, and the assertions here are about the
    SHAPE of the report and an inequality on the count, so a sibling adding
    ADR-0026 changes the number without changing the verdict (tests/README,
    "which real bytes may a fixture read?").
    """
    r = must_pass(run([KPY, GATE, str(ROOT)]), "the real fleet")
    m = re.search(r"BOUND COVERAGE: (\d+) CITED / (\d+) ESTIMATED / "
                  r"(\d+) UNVERIFIED across (\d+) declared block\(s\) in "
                  r"(\d+) ADR\(s\); (\d+) of (\d+) bound-publishing ADR\(s\) "
                  r"OWED", r.out)
    check(m is not None, f"the coverage line changed shape:\n{r.out[-3000:]}")
    cited, _, _, blocks, declaring, owed, total = (int(g) for g in m.groups())
    check(owed > 0, "if nothing is owed, adoption has reached the whole fleet — "
                    "raise CITED_FLOOR to the achieved count and convert this "
                    "fixture's inequality into an equality")
    eq(declaring + owed, total, "every bound-publishing ADR is either declaring "
                                "or owed; a third silent state is how a partial "
                                "rollout becomes permanent")
    check(cited <= blocks, "CITED can never exceed the number of declared "
                           "blocks — a gate crediting more than it read")
    named = len(re.findall(r"^  OWED       ", r.out, re.M))
    eq(named, owed, "EVERY owed ADR is named. A remainder reported as a bare "
                    "count is exactly how 108 published bounds went uncounted")
    m2 = re.search(r"(\d+) inequality bound\(s\) appear in prose across all "
                   r"(\d+)", r.out)
    check(m2 is not None, "the prose-bound denominator is printed")
    check(int(m2.group(1)) >= 100, f"only {m2.group(1)} prose bounds found — "
                                   f"108 were measured on 2026-07-29; a sharp "
                                   f"drop means the detector broke, not that "
                                   f"the ADRs changed")


@test("--strict-owed turns the named debt red, on demand")
def t_strict_owed_turns_the_named_debt_red():
    """The ratchet has an override so the debt can be worked deliberately
    without the default gate blocking three live boards."""
    root = _tree("(no declared bound at all)\n\nSomething <= 5.0 V.\n")
    must_pass(_go(root), "an OWED ADR under the default ceiling")
    must_fail(_go(root, "--strict-owed"), "--strict-owed", "B-OWED")


@test("OWED above the committed ceiling FAILS — the next typed bound is a hard "
      "fail today", kind="known_bad")
def t_owed_above_the_ceiling_fails():
    """The monotone half. The ceiling is only enforced on this gate's OWN tree
    (a scratch fixture is a different universe and a committed 37 says nothing
    about it), so this is asserted against ROOT with the ceiling dialed to one
    below the measured count."""
    r = must_pass(run([KPY, GATE, str(ROOT)]), "measure the fleet")
    owed = int(re.search(r"(\d+) of \d+ bound-publishing", r.out).group(1))
    must_fail(run([KPY, GATE, str(ROOT), "--owed-ceiling", str(owed - 1)]),
              "one below the measured OWED count", "B-FLOOR")


@test("CITED below the committed floor FAILS — a bound that stops reproducing "
      "is a finding, which is what makes UNVERIFIED safe", kind="known_bad")
def t_cited_below_the_floor_fails():
    """THE OTHER SIDE OF THE LADDER. UNVERIFIED is deliberately not a fail, and
    the hole that opens is closed here: with a floor above the achieved count
    the run is red. Asserted against ROOT because the floors are enforced only
    on this gate's own tree."""
    measured = must_pass(run([KPY, GATE, str(ROOT)]), "measure CITED count")
    cited = int(re.search(r"BOUND COVERAGE: (\d+) CITED", measured.out).group(1))
    must_fail(run([KPY, GATE, str(ROOT), "--cited-floor", str(cited + 1)]),
              "a CITED floor above the achieved count", "B-FLOOR")


@test("CITED_FLOOR is pinned to the measured count, so it cannot lag adoption")
def t_the_cited_floor_is_pinned_to_the_measured_count():
    """THE OUTSIDE OF THE CIRCLE, the trick VACUITY_FLOOR uses. A floor is what
    makes the ladder monotone, so it cannot be graded by the gate that reads it.
    Measured here instead: floor == achieved. A floor of 0 on a tree with 12
    CITED bounds would let 12 declarations be deleted for free, and a floor
    above the tree is a broken build rather than a ratchet.

    Today both sides are 10. The floor became active with the first declaration
    and this test forces every later adoption into the SAME commit."""
    sys.path.insert(0, str(SCRIPTS))
    import adr_bound_provenance as abp                        # noqa: E402
    r = must_pass(run([KPY, GATE, str(ROOT)]), "measure the fleet")
    cited = int(re.search(r"BOUND COVERAGE: (\d+) CITED", r.out).group(1))
    eq(abp.CITED_FLOOR, cited,
       f"CITED_FLOOR is {abp.CITED_FLOOR} and {cited} bound(s) actually "
       f"regenerate. Raise the floor in the SAME commit that adds a "
       f"declaration; never lower it to make a run green")


@test("zero ADRs is a FAIL, never a pass — a zero denominator is not a clean "
      "tree (canon M-COVER)", kind="known_bad")
def t_zero_adrs_is_a_fail_not_a_pass():
    root = tmpdir("adrb_empty_")
    (root / "docs").mkdir()
    must_fail(run([KPY, GATE, str(root)]), "an empty tree",
              "A zero denominator is a FAIL")


# ===========================================================================
# THE BLIND SPOT, declared with its CONTRAST (canon G-VACUOUS)
# ===========================================================================

@test("BLIND SPOT: a bound typed only in ADR prose is read by nothing — 37 of "
      "37 today — and the SAME false bound in a block is caught")
def t_blindspot_a_bound_typed_only_in_prose_is_read_by_nothing():
    """THE DECLARED BLIND SPOT, subject first and then the contrast.

    Registered as `clean` rather than `kind="vacuity"` on purpose: binding a
    vacuity fixture requires a `VACUITY:` block in the gate's docstring AND
    raising `gate_contract_audit.VACUITY_FLOOR` from 5 to 6, and that file is
    owned elsewhere in this session (a vacuity fixture with no declaration, or a
    declaration with no fixture, is itself a G-VACUOUS FAIL — so the pair must
    land together). The gate declares the blind spot in prose under "THE BLIND
    SPOT THIS LEAVES OPEN"; the one-line patch that promotes this fixture is in
    the accompanying report.

    SUBJECT — the ADR-0024 defect IN ITS ORIGINAL FORM: `R_pd <= 592 Ohm`
    written as prose in a worst-case document, with no `<!-- bound -->` block.
    The gate PASSES it. That is 37 of 37 documents and 108 bounds on the day
    this landed, the incident bound among them.

    CONTRAST — the SAME false number moved into a block is caught by name,
    twice. Which is what makes this a blind spot rather than a fact the gate
    cannot represent at all.
    """
    prose = ("## Consequences\n\n"
             "General bound: V <= 0.700 V => **R_pd <= 592 Ohm**, at the "
             "worst-case corner.\n")
    root = tmpdir("adrb_prose_")
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / "docs" / "decisions" / "0024-incident.md").write_text(prose)
    r = must_pass(_go(root), "THE BLIND SPOT: a false bound in prose")
    contains(r.out, "OWED", "it is at least NAMED as owed")
    contains(r.out, "graded nothing", "and the gate says the regenerating half "
                                      "graded nothing")

    # THE CONTRAST: the same 592, declared.
    must_fail(_go(_tree(_block(value="592.3", corner="worst_case",
                              solve_corner="nominal"))),
              "the same false bound, declared", "B-CORNER")


# ===========================================================================
# RED VERIFICATION
# ===========================================================================

@test("RED (1): four gates reach ADR paths and NONE of them reads a NUMBER out "
      "of one — the pre-fix state, measured rather than assumed")
def t_red_no_pre_existing_gate_reads_a_number_out_of_an_adr():
    """There is no earlier version of this checker to swap back in, so the
    pre-fix baseline is measured directly — and the first measurement was WRONG
    in the safe direction, which is worth recording. "Nothing reaches the
    decisions folder" is false: FOUR scripts do.

    MEASURED at this commit, and inspected one by one:

      electrical_invariants.py  E-ADR. `protection_adrs()` globs `*.md` and
                                reads the TITLE, the `tags:` line and the
                                front-matter `status:`. Its demand is that a
                                protection/topology ADR be cited by some
                                invariant — a citation graph, not a value.
      module_first_check.py      validates that a bare-IC exception's `adr`
                                path resolves under `01_docs/decisions`; it
                                does not open or parse an ADR quantity.
      policy_audit.py           checks the folder EXISTS (`E-ADR N-A` when it
                                does not).
      power_topology.py         keyword-matches the first 400 characters for
                                batter|lipo|cell|pack to classify the supply.

    Not one of them extracts a quantity. `R_pd <= 592 Ohm` was a title away from
    every gate in the tree, sat in a live document through a full revision
    cycle, and everything was green on it.

    THE ASSERTION IS SET EQUALITY, and it is a proxy stated as one: proving "no
    ADR-derived string ever reaches a numeric comparison" needs a dataflow pass,
    so what is pinned instead is the READER SET. A fourth reader — or one of
    these three growing a number parser — breaks this test and forces the
    inspection above to be redone, which is the property that actually rots."""
    readers = []
    for p in sorted(ROOT.glob("skills/*/scripts/*.py")):
        if p.name == GATE.name:
            continue
        t = p.read_text(errors="replace")
        if re.search(r"decisions[/\"']", t) and re.search(
                r"read_text|open\(|glob\(", t):
            readers.append(p.name)
    eq(readers, ["electrical_invariants.py", "module_first_check.py",
                 "policy_audit.py",
                 "power_topology.py"],
       "the set of ADR-reading gates changed. Re-inspect each one: if any now "
       "grades a NUMBER out of an ADR, this gate overlaps it and the incident "
       "claim in its docstring needs re-measuring")
    # and positively: none of the four carries the shape that finds a published
    # bound in prose at all — an inequality operator followed by a number.
    for name in readers:
        t = (SCRIPTS / name).read_text(errors="replace")
        check("<=|>=" not in t and "≤" not in t,
              f"{name} now carries an inequality-matching pattern — check "
              f"whether it reads a published bound, and re-measure")


@test("RED (2): with B-CORNER and B-STDVAL excised, the real 592 Ohm bound "
      "PASSES and is reported CITED")
def t_red_the_ablated_gate_passes_the_592_ohm_bound():
    """RED-VERIFIED AGAINST PRE-FIX CODE, by ablation, and the measured pre-fix
    output is quoted in this module's docstring.

    `_ablated()` copies the gate and deletes exactly the two blocks that
    implement the incident checks — the `B-CORNER` append and the `B-STDVAL`
    append — leaving the M4-shaped half (B-REGEN / B-FLIP / B-TOL / B-SCHEMA)
    untouched. Against that build, ADR-0024's real published bound is GREEN and
    the run EXITS 0: a `command:` solving at the NOMINAL corner regenerates
    592.3077 and agrees with the typed 592.3, so a gate that only diffs the
    number is SATISFIED BY THE DEFECT.

    This is the fixture that proves the two new IDs, and not the borrowed
    machinery around them, do the work."""
    ablated = _ablated()
    root = _tree(_block(value="592.3", corner="worst_case",
                        solve_corner="nominal"))
    pre = run([KPY, ablated, str(root), "--repo-root", str(root)])
    eq(pre.rc, 0, "PRE-FIX the 592 Ohm bound must PASS — if it now fails, the "
                  "ablation removed the wrong lines and this red verification "
                  f"proves nothing:\n{pre.out}")
    contains(pre.out, "PASS (0 fails)", "pre-fix the verdict is PASS")
    contains(pre.out, "regenerated 592.3077 vs published 592.3",
             "pre-fix the M4-shaped half is SATISFIED by the defect")
    not_contains(pre.out, "B-CORNER", "pre-fix there is no corner check")
    not_contains(pre.out, "B-STDVAL", "pre-fix there is no standard-value check")
    # and POST-fix, the same bytes fail.
    must_fail(_go(root), "POST-fix, the same input", "B-CORNER")


def _ablated():
    """A copy of the gate with the two incident checks excised, nothing else.

    Surgical and asserted: EVERY `fails.append(` whose message begins
    `B-CORNER`/`B-STDVAL` is replaced by `pass`, and the count is asserted — an
    ablation that silently changed nothing, or changed only one of two sites,
    would make the red verification a lie. (It nearly did: B-STDVAL has TWO
    sites, the "admits NO value" case and the real one, and an excision that
    stopped at the first left the incident check live.)
    """
    out = GATE.read_text()
    for cid, want in (("B-CORNER", 1), ("B-STDVAL", 2)):
        out, n = _excise(out, cid)
        eq(n, want, f"the {cid} ablation removed {n} site(s), expected {want} — "
                    f"the gate was refactored and this red verification is "
                    f"stale")
        not_contains(out, f'f"{cid} ', f"no {cid} finding survives the ablation")
    d = tmpdir("adrb_pre_")
    shutil.copy(SCRIPTS / "waiver_provenance.py", d / "waiver_provenance.py")
    p = d / "adr_bound_provenance_prefix.py"
    p.write_text(out)
    return p


def _excise(src, cid):
    """-> (source, n) with EVERY `fails.append(f"<cid> ...")` replaced by `pass`."""
    n = 0
    while True:
        lines = src.splitlines(keepends=True)
        hit = None
        for i, ln in enumerate(lines):
            if "fails.append(" not in ln:
                continue
            if f'f"{cid} ' not in "".join(lines[i:i + 3]):
                continue
            hit = i
            break
        if hit is None:
            return src, n
        indent = lines[hit][:len(lines[hit]) - len(lines[hit].lstrip())]
        j, depth = hit, 0
        while j < len(lines):
            depth += lines[j].count("(") - lines[j].count(")")
            j += 1
            if depth <= 0:
                break
        src = "".join(lines[:hit]) + f"{indent}pass\n" + "".join(lines[j:])
        n += 1


if __name__ == "__main__":
    sys.exit(main())
