#!/usr/bin/env python3
"""G-*: the gate that governs the gates.

`contracts_audit.py` governs FOLDERS. Nothing governed the CHECKERS — so five of
them shipped unable to fail on the property they name, and a fleet audit found
two boards not orderable with every gate green:

  * A-AMP graded 10 of 57 declared net-class currents fleet-wide; usb-hub-3s-v3's
    PWR_IN 7 A, PWR_RAIL 6 A and SWITCH_NODE 7 A are all silenced by a qualifier,
    and the one class it does grade FAILS.
  * `row_kind` dropped RS1/RS2 (the shunts setting both buck current limits) and
    CE1 (the only electrolytic, which shipped reversed) while printing PASS.
  * `labeled_resistance("10mOhm")` returns 1.0e7 — milli decoded as mega.

The acceptance test for the auditor itself WAS adversarial against the real
tree (`t_flags_the_scripts_independently_known_broken`): it required the
auditor to flag the scripts independently measured as silent, because a
gate-on-gates that comes back clean on a codebase measured to be riddled is
decoration. That backlog is now CLOSED — 12 unmet obligations across 25
verdict-printing scripts on 2026-07-27, 0 after — so per that test's own
written instruction the floor was DELETED rather than lowered, and
`t_scans_the_whole_real_tree` guards the remaining risk (an auditor that
reports clean because it scanned nothing). The DISCRIMINATION proof lives
where it always really did: the synthetic known-bad fixtures below.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent /
                       'skills' / 'kicad-pcb' / 'scripts'))   # G-SELFCON
from harness import (KPY, ROOT, check, contains, eq, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

TOOL = ROOT / "skills/kicad-pcb/scripts/gate_contract_audit.py"

SILENT = '''\
import argparse
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("board"); a = ap.parse_args()
    print("PASS all good")
'''

COVERED = '''\
import argparse
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("board"); a = ap.parse_args()
    n, m = 3, 3
    print(f"  coverage: {n}/{m} rows graded")
    print("PASS all good")
'''

NO_INPUT = '''\
def main():
    n, m = 1, 1
    print(f"  coverage: {n}/{m} rows graded")
    print("FAIL nope")
'''


def _root(scripts, tests=None):
    """A miniature repo: skills/x/scripts/*.py plus tests/t*.py."""
    d = tmpdir("gca_")
    sd = d / "skills" / "x" / "scripts"
    sd.mkdir(parents=True)
    td = d / "tests"
    td.mkdir()
    for name, body in scripts.items():
        (sd / name).write_text(body)
    for name, body in (tests or {}).items():
        (td / name).write_text(body)
    return d


@test("gca_silent_gate_is_flagged", kind="known_bad")
def t_silent_gate_is_flagged():
    """THE SHAPE. A verdict with no denominator can report success over input it
    never understood — the shape shared by every instance in the docstring."""
    d = _root({"quiet.py": SILENT},
              {"t1_quiet.py": 'TOOL = SCRIPTS / "quiet.py"\nmust_fail(1)\n'})
    must_fail(run([KPY, TOOL, "--root", d]), "silent gate", expect="G-COVER")


@test("gca_covered_gate_passes")
def t_covered_gate_passes():
    """Discrimination: a gate that names its input, reports coverage and has a
    RED fixture must PASS, or the auditor is just failing everything."""
    d = _root({"loud.py": COVERED},
              {"t1_loud.py": 'TOOL = SCRIPTS / "loud.py"\nmust_fail(1)\n'})
    must_pass(run([KPY, TOOL, "--root", d]), "fully compliant gate")


@test("gca_unnamed_input_is_flagged", kind="known_bad")
def t_unnamed_input_is_flagged():
    """G-INPUT / canon M6: policy_audit graded a `06_build` shadow tree and
    reported 79 warnings where the sealed archive has 102."""
    d = _root({"noin.py": NO_INPUT},
              {"t1_noin.py": 'TOOL = SCRIPTS / "noin.py"\nmust_fail(1)\n'})
    must_fail(run([KPY, TOOL, "--root", d]), "gate not naming its input",
              expect="G-INPUT")


@test("gca_missing_red_fixture_is_flagged", kind="known_bad")
def t_missing_red_fixture_is_flagged():
    """G-RED: a gate never observed to fail is a claim, not a control."""
    d = _root({"loud.py": COVERED}, {})
    must_fail(run([KPY, TOOL, "--root", d]), "gate with no RED fixture",
              expect="G-RED")


@test("gca_a_test_without_must_fail_is_not_a_red_fixture", kind="known_bad")
def t_test_without_must_fail_is_not_red():
    """Mentioning the script in tests/ is not enough — the fixture must assert
    the checker REJECTED something."""
    d = _root({"loud.py": COVERED},
              {"t1_loud.py": 'TOOL = SCRIPTS / "loud.py"\nmust_pass(0)\n'})
    must_fail(run([KPY, TOOL, "--root", d]), "test that never asserts failure",
              expect="G-RED")


@test("gca_a_prose_mention_is_not_a_red_fixture", kind="known_bad")
def t_prose_mention_is_not_a_red_fixture():
    """A HOLE THIS CHECK SHIPPED WITH, found by running it on itself.

    `has_red_fixture` first searched for the script's stem ANYWHERE in a test
    file. The sentence "found by fleet_regrade.py" inside an UNRELATED suite's
    docstring therefore satisfied G-RED for fleet_regrade — a gate-on-gates
    crediting a fixture that does not exist, which is precisely the defect
    class it polices.

    Now the name must appear QUOTED, the form both binding idioms use
    (`ROOT / "skills/.../x.py"` and `SCRIPTS / "x.py"`). A docstring writes it
    bare. The first fix over-corrected to requiring a literal `scripts/x.py`
    path, which false-failed 16 gates that DO have real suites; that measurement
    is what forced the middle ground.
    """
    d = _root({"loud.py": COVERED},
              {"t1_other.py": '"""this suite mentions loud.py in prose only"""\n'
                              "must_fail(1)\n"})
    must_fail(run([KPY, TOOL, "--root", d]), "prose-only mention of the script",
              expect="G-RED")


@test("gca_a_quoted_invocation_IS_a_red_fixture")
def t_quoted_invocation_is_a_red_fixture():
    """The other side: both real binding idioms must be accepted, or the check
    rejects suites that genuinely exercise their gate."""
    for name, body in (("path", 'TOOL = ROOT / "skills/x/scripts/loud.py"\nmust_fail(1)\n'),
                       ("harness", 'TOOL = SCRIPTS / "loud.py"\nmust_fail(1)\n')):
        d = _root({"loud.py": COVERED}, {f"t1_{name}.py": body})
        must_pass(run([KPY, TOOL, "--root", d]), f"{name}-style binding")


@test("gca_unparseable_script_is_a_fail_not_a_skip", kind="known_bad")
def t_unparseable_script_is_a_fail():
    """NEVER SILENTLY SKIP. A file the auditor cannot parse is a FAIL — the
    `row_kind` failure mode is precisely 'did not understand, reported PASS'."""
    d = _root({"broken.py": "def main(:\n  print('PASS')\n"},
              {"t1_x.py": "must_fail(1)\n"})
    must_fail(run([KPY, TOOL, "--root", d]), "unparseable script",
              expect="G-PARSE")


@test("gca_emits_its_own_coverage")
def t_emits_its_own_coverage():
    """The auditor obeys the contract it enforces."""
    d = _root({"loud.py": COVERED},
              {"t1_loud.py": 'TOOL = SCRIPTS / "loud.py"\nmust_fail(1)\n'})
    r = must_pass(run([KPY, TOOL, "--root", d]), "compliant fixture")
    contains(r.out, "coverage:", "the auditor reports its own denominator")


@test("gca_scans_the_whole_real_tree_and_the_backlog_is_closed")
def t_scans_the_whole_real_tree():
    """THE FORMER ADVERSARIAL ACCEPTANCE TEST, RETIRED AS ITS DOCSTRING
    INSTRUCTED (2026-07-27).

    It used to assert `rc != 0` and `>= 5 FAIL lines` against the real tree,
    with this note attached:

        IF THE FLOOR BELOW EVER BECOMES THE THING THAT FAILS, DELETE THIS TEST.
        Do not lower the number to make it pass — a tree that genuinely
        satisfies G-INPUT/G-COVER/G-RED everywhere has earned the deletion,
        and a lowered floor is just a gate quietly relaxing until it cannot
        fail.

    The floor became the thing that failed. Measured: the backlog went from
    **12 obligations unmet across 25 verdict-printing scripts** to **0/25** by
    fixing the nine scripts that were silent (jlc_stock_check,
    board_netlist_parity, classified_drc, count_parity, escape_check,
    kicad_sch_parity, net_label_survival, tsx_preflight, waiver_provenance) —
    not by relaxing anything in gate_contract_audit.py, whose regexes are
    unchanged in this campaign. So the instruction is followed: the floor is
    deleted rather than lowered.

    WHAT REPLACES IT. The risk the old test guarded was VACUITY on the real
    tree — an auditor that reports clean because it looked at nothing. Two
    assertions still cover that, and neither can be satisfied by going quiet:

      1. the SCAN denominator must stay large. A `SKIP_BASENAMES` entry added
         to silence a failing script, or a glob that stopped matching, drops
         this number and is caught here.
      2. the auditor must still DISCRIMINATE. That is proved by the synthetic
         known-bad fixtures above, which are the real control — this test only
         asserts the real tree is clean for the reason claimed, with its own
         coverage line printed.
    """
    r = must_pass(run([KPY, TOOL, "--root", ROOT]),
                  "the G-* backlog is closed on the real tree")
    contains(r.out, "coverage:", "the auditor reports its own denominator")
    m = re.search(r"coverage: (\d+)/(\d+) verdict-printing scripts audited "
                  r"\((\d+) scripts scanned", r.out)
    check(m is not None, f"the coverage line changed shape: {r.out[:300]!r}")
    audited, scanned = int(m.group(1)), int(m.group(3))
    # measured 2026-07-27: 25 verdict-printing of 45 scanned. The floors are
    # well below those so a genuine addition does not trip them, but a
    # SKIP_BASENAMES entry or a broken glob that silences a whole family does.
    check(scanned >= 40, f"only {scanned} scripts scanned under skills/*/scripts/ "
                         f"— the auditor has gone quiet by not looking")
    check(audited >= 20, f"only {audited} scripts recognised as printing a "
                         f"verdict — a gate-on-gates auditing this few is "
                         f"decoration, not a control")


# ----------------------------------------------- G-SELFCON (ADR-0007, 2026-07-29)
@test("G-SELFCON FAILS a tier whose silk stroke floor is unreachable at its own "
      "text-height floor", kind="known_bad")
def t_selfcon_unreachable_stroke():
    """THE INCIDENT. fab_tiers.yaml declared min_silk_text_height 0.45 AND
    min_silk_stroke 0.15 on all five tiers, while KiCad clamps a text stroke to
    <= 0.25 x height — 0.45 mm text can carry at most 0.1125 mm. The two floors
    were UNSATISFIABLE TOGETHER and had been since they were written; no board
    could ever have met both, and nothing said so. smc0985-cooksense then
    shipped six SAFETY designators below the stroke floor and the waiver written
    the same day called 0.13 acceptable.

    RED-VERIFIED: run against the real repo BEFORE the fab_tiers fix, this
    reports 5 failures (one per tier); after, 0. The fixture below is
    synthetic so the test does not go green merely because the repo was fixed."""
    import gate_contract_audit as gca                       # noqa: E402
    d = tmpdir("selfcon_")
    (d / "fab_tiers.yaml").write_text(
        "tiers:\n"
        "  bad_tier:\n"
        "    min_silk_text_height: 0.45\n"
        "    min_silk_stroke: 0.15\n"
        "  ok_tier:\n"
        "    min_silk_text_height: 0.60\n"
        "    min_silk_stroke: 0.15\n")
    fails, n = gca.check_self_consistency(d)
    eq(n, 2, "both tiers graded (the denominator, canon M-COVER)")
    eq(len(fails), 1, f"exactly the unsatisfiable tier fails:\n{fails}")
    check("bad_tier" in fails[0], f"names the offending tier:\n{fails[0]}")
    check("0.1125" in fails[0],
          f"states the stroke actually reachable:\n{fails[0]}")
    check("0.60" in fails[0],
          f"states the height that WOULD satisfy the declared stroke:\n{fails[0]}")


@test("G-SELFCON passes the repo's own fab_tiers.yaml, with a denominator")
def t_selfcon_repo_clean():
    """The other half of discrimination: a check that only ever fails ranks
    nothing. The repo's five tiers must now be self-consistent AND the verdict
    must say how many pairs it graded."""
    import gate_contract_audit as gca                       # noqa: E402
    fails, n = gca.check_self_consistency(
        ROOT / "skills" / "kicad-pcb" / "references")
    check(n >= 5, f"graded every tier, got {n}")
    eq(len(fails), 0, f"repo fab_tiers is self-consistent:\n{fails}")



if __name__ == "__main__":
    sys.exit(main())
