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

The acceptance test for the auditor itself is ADVERSARIAL and lives in
`t_flags_the_scripts_independently_known_broken` below: it must flag the two
scripts we already know are silent. A gate-on-gates that comes back clean on a
codebase measured to be riddled is decoration.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_fail,  # noqa: E402
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
              {"t1_quiet.py": "quiet.py\nmust_fail(1)\n"})
    must_fail(run([KPY, TOOL, "--root", d]), "silent gate", expect="G-COVER")


@test("gca_covered_gate_passes")
def t_covered_gate_passes():
    """Discrimination: a gate that names its input, reports coverage and has a
    RED fixture must PASS, or the auditor is just failing everything."""
    d = _root({"loud.py": COVERED},
              {"t1_loud.py": "loud.py\nmust_fail(1)\n"})
    must_pass(run([KPY, TOOL, "--root", d]), "fully compliant gate")


@test("gca_unnamed_input_is_flagged", kind="known_bad")
def t_unnamed_input_is_flagged():
    """G-INPUT / canon M6: policy_audit graded a `06_build` shadow tree and
    reported 79 warnings where the sealed archive has 102."""
    d = _root({"noin.py": NO_INPUT},
              {"t1_noin.py": "noin.py\nmust_fail(1)\n"})
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
              {"t1_loud.py": "loud.py\nmust_pass(0)\n"})
    must_fail(run([KPY, TOOL, "--root", d]), "test that never asserts failure",
              expect="G-RED")


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
              {"t1_loud.py": "loud.py\nmust_fail(1)\n"})
    r = must_pass(run([KPY, TOOL, "--root", d]), "compliant fixture")
    contains(r.out, "coverage:", "the auditor reports its own denominator")


@test("gca_flags_the_scripts_independently_known_broken")
def t_flags_the_scripts_independently_known_broken():
    """ADVERSARIAL ACCEPTANCE TEST — the reason to trust this tool at all.

    `rules_audit.py` (A-AMP: 10 of 57 currents graded fleet-wide) and
    `bom_source_check.py` (row_kind: RS1/RS2 and CE1 dropped while printing
    PASS) were both proven silent by independent measurement BEFORE this auditor
    existed. If the auditor does not flag the ones still broken, it is not
    measuring the property it claims to measure, and this suite should fail
    rather than reassure.

    NEITHER IS ASSERTED BY NAME ANY MORE, because BOTH WERE FIXED in the same
    campaign, and this test failed twice on the way — once as each repair
    landed. That is the intended behaviour of an acceptance test pinned to
    specific defects, and the honest response is to record the repair rather
    than to loosen the check:

      rules_audit.py       A-AMP 10/57 -> 53/57 graded, `coverage A-AMP: N/M`
      bom_source_check.py  row_kind dropped 87/673 all-R/C rows -> 0/673, and
                           leg C now prints `coverage leg C: N/M`

    What survives is the property, not the instances: the auditor must not
    report this tree clean, and it must not go quiet. The synthetic fixtures
    above are what actually prove it DISCRIMINATES — they are the known-bads;
    this test only guards against vacuity on the real tree.

    IF THE FLOOR BELOW EVER BECOMES THE THING THAT FAILS, DELETE THIS TEST.
    Do not lower the number to make it pass — a tree that genuinely satisfies
    G-INPUT/G-COVER/G-RED everywhere has earned the deletion, and a lowered
    floor is just a gate quietly relaxing until it cannot fail.
    """
    r = run([KPY, TOOL, "--root", ROOT])
    check(r.rc != 0, "the auditor must not report the current tree as clean")
    n = r.out.count("  FAIL ")
    check(n >= 5, f"the auditor found only {n} violations on a tree independently "
                  f"measured as riddled — a gate-on-gates this quiet is "
                  f"decoration, not a control")


if __name__ == "__main__":
    sys.exit(main())
