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
from harness import (KPY, ROOT, Failed, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

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


@test("gca does not mistake typed pipeline verdict data for an executable gate")
def t_typed_pipeline_library_is_not_gate():
    library = '''\
STATUSES = frozenset({"PASS", "FAIL", "INCOMPLETE"})

def parse_status(value):
    if value not in STATUSES:
        raise ValueError(value)
    return value
'''
    d = _root({name: library for name in (
        "board_authority.py",
        "copper_graph.py",
        "pipeline_catalog.py",
        "pipeline_contract.py",
        "pipeline_applicability.py",
        "pipeline_execution.py",
        "pipeline_shadow.py",
        "pipeline_xtrace.py",
        "placement_cell_checks.py",
        "process_runner.py",
        "route_acceptance_core.py",
    )})
    r = must_pass(run([KPY, TOOL, "--root", d]),
                  "typed pipeline library inventory")
    contains(r.out, "0/0 verdict-printing scripts audited",
             "library exclusion denominator")


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
#: The tier every fixture below is a ONE-FIELD break of: the corrected
#: jlc_2layer_default. 0.45mm text carries 0.1125mm of stroke (KiCad's clamp,
#: and what the generator emits there); JLC's published 0.15 needs 0.9375mm.
GOOD = dict(min_silk_text_height=0.45, min_silk_stroke=0.1125,
            published_silk_stroke=0.15, published_stroke_min_height=0.9375)


def _tiers(d, **broken):
    """A fab_tiers.yaml with the corrected tier plus one broken in exactly ONE
    field (tests/README: a known-bad is a good input broken one way)."""
    def block(name, fields):
        return f"  {name}:\n" + "".join(
            f"    {k}: {v}\n" for k, v in fields.items())
    bad = dict(GOOD)
    bad.update({k: v for k, v in broken.items() if v is not None})
    for k, v in broken.items():
        if v is None:
            bad.pop(k, None)
    (d / "fab_tiers.yaml").write_text(
        "tiers:\n" + block("ok_tier", GOOD) + block("bad_tier", bad))
    return d


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
    synthetic so the test does not go green merely because the repo was fixed.
    Re-measured 2026-07-29 after the widening: the pre-fix checker files **1**
    failure on this fixture because it modelled one stroke path; there are two,
    and both are graded now."""
    import gate_contract_audit as gca                       # noqa: E402
    d = _tiers(tmpdir("selfcon_"), min_silk_stroke=0.15)
    fails, n = gca.check_self_consistency(d)
    eq(n, 2, "both tiers graded (the denominator, canon M-COVER)")
    check(fails and all("bad_tier" in f for f in fails),
          f"only the unsatisfiable tier fails:\n{fails}")
    unreach = [f for f in fails if "UNREACHABLE" in f]
    eq(len(unreach), 2, f"both stroke emitters are graded, not one:\n{fails}")
    check("0.1125" in unreach[0],
          f"states the stroke actually reachable:\n{unreach[0]}")
    check("0.60" in unreach[0],
          f"states the height that WOULD satisfy the declared stroke:\n{unreach[0]}")


@test("G-SELFCON FAILS a published stroke floor the generator will never emit "
      "— the direction the first version was blind to", kind="known_bad")
def t_selfcon_understated_stroke():
    """THE SECOND LESSON OF THE SAME DAY. As first written (ad487df) G-SELFCON
    modelled ONLY KiCad's upper clamp (`KICAD_STROKE_OVER_HEIGHT = 0.25`), so it
    could prove a published stroke unreachable but could not see a published
    stroke that is a FICTION: the generator's LOWER floor is
    max(min_silk_stroke, 0.13, 0.16 x height) for board silk text and
    max(min_silk_stroke, 0.09, 0.20 x height) for the refdes path, so a tier
    declaring 0.1125 at a 0.60mm height floor publishes a number no board can
    be built at — everything it emits is 0.13 / 0.12.

    That blindness is what let the wrong corollary be written beside it. A gate
    that catches only the direction its author got right is worthless
    (canon M-WIDTH).

    RED-VERIFIED against the pre-fix checker (`git show ad487df:...
    gate_contract_audit.py` exec'd in-process, 2026-07-29): it returns
    **0 fails** on this fixture — it cannot represent the defect. After: 2
    (one per stroke emitter), naming both the emitted value and the tier."""
    import gate_contract_audit as gca                       # noqa: E402
    d = _tiers(tmpdir("selfcon_"), min_silk_text_height=0.60)
    fails, n = gca.check_self_consistency(d)
    eq(n, 2, "both tiers graded")
    fict = [f for f in fails if "FICTION" in f]
    eq(len(fict), 2, f"both emitters graded in the LOWER direction:\n{fails}")
    check(all("bad_tier" in f for f in fict), f"names the tier:\n{fict}")
    check(any("0.1300" in f for f in fict) and any("0.1200" in f for f in fict),
          f"states what the generator ACTUALLY emits, per emitter:\n{fict}")


@test("G-SELFCON FAILS the wrong threshold height for the fab's published "
      "stroke — MY error, reproduced", kind="known_bad")
def t_selfcon_wrong_threshold_height():
    """THE ERROR THIS TEST EXISTS FOR. The fab_tiers.yaml header declared, for
    one day: 'TO REACH THE PUBLISHED 0.15 STROKE, TEXT MUST BE >= 0.60mm'. It
    is 0.9375mm. At 0.60 the generator emits max(0.1125, 0.13, 0.096) = 0.13;
    0.70 and 0.80 also emit 0.13; only 0.16 x h >= 0.15 gets there. Both pluto
    boards found it by MEASURING the generator after following the sentence —
    rx2's port captions print 0.152 at 0.95mm, cal-switch went to 1.0/1.2mm.

    The corollary is therefore DATA now (`published_stroke_min_height`), graded
    against the generator's own `silk_stroke`, because a prose corollary is
    exactly what failed. The fixture is the sentence as written.

    RED-VERIFIED against the pre-fix checker (exec'd in-process, 2026-07-29):
    **0 fails** — it had no notion of the threshold at all, which is why the
    wrong number survived being written down in the same commit."""
    import gate_contract_audit as gca                       # noqa: E402
    d = _tiers(tmpdir("selfcon_"), published_stroke_min_height=0.60)
    fails, n = gca.check_self_consistency(d)
    eq(n, 2, "both tiers graded")
    eq(len(fails), 1, f"exactly the wrong threshold fails:\n{fails}")
    check("bad_tier" in fails[0], f"names the tier:\n{fails[0]}")
    check("0.1300" in fails[0],
          f"states what 0.60mm text actually emits:\n{fails[0]}")
    check("0.9375" in fails[0],
          f"states the TRUE first height reaching 0.15:\n{fails[0]}")


@test("G-SELFCON FAILS an overstated threshold height too (a floor that "
      "outlaws legible text)", kind="known_bad")
def t_selfcon_overstated_threshold():
    """Both directions or neither: a threshold ABOVE the first height that
    reaches the published stroke would forbid legible silk for no reason, and a
    gate that only ever pushes numbers up is a ratchet, not a model. 1.2mm text
    already reaches 0.15 at 0.9375."""
    import gate_contract_audit as gca                       # noqa: E402
    d = _tiers(tmpdir("selfcon_"), published_stroke_min_height=1.2)
    fails, n = gca.check_self_consistency(d)
    eq(n, 2, "both tiers graded")
    eq(len(fails), 1, f"exactly the overstated tier fails:\n{fails}")
    check("0.9375" in fails[0], f"names the true threshold:\n{fails[0]}")


@test("G-SELFCON FAILS a tier that declares a stroke floor but no coupling",
      kind="known_bad")
def t_selfcon_missing_coupling():
    """A tier with no `published_silk_stroke` / `published_stroke_min_height`
    has quietly gone back to prose: the floor is declared and the rule that
    binds it is not, which is the state the file was in when the 0.60 sentence
    was believed for a day."""
    import gate_contract_audit as gca                       # noqa: E402
    d = _tiers(tmpdir("selfcon_"), published_silk_stroke=None,
               published_stroke_min_height=None)
    fails, n = gca.check_self_consistency(d)
    eq(n, 2, "both tiers graded")
    eq(len(fails), 1, f"exactly the uncoupled tier fails:\n{fails}")
    check("bad_tier" in fails[0] and "published_stroke_min_height" in fails[0],
          f"names the tier and the missing field:\n{fails[0]}")


@test("G-SELFCON carries NO COPY of the formula it grades, and FAILS if it "
      "cannot lift it from the generator", kind="known_bad")
def t_selfcon_formula_is_not_copied():
    """CANON M1, IN THE OTHER DIRECTION. A checker that keeps its own copy of
    the constants it grades does not disagree with the generator — it agrees
    with a STALE COPY, and then a formula change silently un-grades itself.
    (`KICAD_STROKE_OVER_HEIGHT = 0.25` was such a copy: correct, and blind to
    the 0.13 / 0.16 floor that produced the wrong corollary.)

    So two assertions. (1) no float in gate_contract_audit.py's AST is one of
    the generator's stroke constants — the numbers exist in exactly one place;
    (2) if the generator stops declaring them, G-SELFCON FAILS loudly instead
    of falling back on a copy.

    RED-VERIFIED against the pre-fix checker (2026-07-29): assertion (1) fails
    on it because `KICAD_STROKE_OVER_HEIGHT = 0.25` is a literal in
    gate_contract_audit.py — a copy that happened to be right, and blind
    besides; assertion (2) fails with AttributeError because no extraction
    existed. Assertion (2) also caught a real hole while being written: a
    renamed constant raised NameError out of the exec instead of failing the
    gate, so `load_stroke_model` now converts any exec failure into a
    SelfConError."""
    import ast as _ast
    import gate_contract_audit as gca                       # noqa: E402

    src = Path(gca.__file__).read_text()
    lits = {c.value for c in _ast.walk(_ast.parse(src))
            if isinstance(c, _ast.Constant) and isinstance(c.value, float)}
    fn, ns = gca.load_stroke_model()
    copied = lits & {ns["SILK_STROKE_MIN"], ns["SILK_STROKE_OVER_SIZE"],
                     ns["REFDES_STROKE_MIN"], ns["REFDES_STROKE_OVER_SIZE"],
                     ns["KICAD_STROKE_OVER_HEIGHT"]}
    check(not copied,
          f"gate_contract_audit.py hard-codes the generator's stroke "
          f"constants {sorted(copied)} — it would agree with a stale copy")
    eq(fn(0.6, 0.1125), 0.13, "the lifted formula is the generator's own")

    # (2) the generator loses a constant -> a LOUD failure, not a fallback
    d = tmpdir("selfcon_gen_")
    gen = (d / "generate_board_generic.py")
    gen.write_text(Path(gca.GEN_PATH).read_text().replace(
        "SILK_STROKE_OVER_SIZE = 0.16", "SILK_STROKE_OVER_SIZE_RENAMED = 0.16"))
    try:
        gca.GEN_PATH = gen
        fails, n = gca.check_self_consistency(
            _tiers(tmpdir("selfcon_")))
        eq(n, 0, f"nothing may be graded without the formula:\n{fails}")
        eq(len(fails), 1, f"the missing constant must FAIL:\n{fails}")
        check("SILK_STROKE_OVER_SIZE" in fails[0],
              f"names the constant it could not lift:\n{fails[0]}")
    finally:
        gca.GEN_PATH = Path(gca.__file__).resolve().parent / \
            "generate_board_generic.py"


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



# ------------------------------------------------- G-VACUOUS (2026-07-29)
# G-RED asks "can this gate fail at all?" and 31/31 answer yes. G-VACUOUS asks
# the sharper question: can it fail ON THE CASE IT EXISTS FOR? Six gates were
# measured GREEN on 2026-07-28/29 while the fact each grades was false. See the
# G-VACUOUS block in gate_contract_audit.py for all six with their numbers.
#
# The contract: a gate's module DOCSTRING carries a `VACUITY:` block and tests/
# carries `@test(..., kind="vacuity", gate="<basename>.py")` that constructs that
# input and asserts the gate PASSES. Bidirectional — prose alone fails, a
# fixture alone fails, and a "vacuity" fixture asserting must_fail is a FALSE
# declaration and fails.

#: a gate that satisfies G-INPUT/G-COVER/G-RED, so the only thing under test
#: below is the vacuity binding.
COMPLIANT_TESTS = {"t1_loud.py": 'TOOL = SCRIPTS / "loud.py"\nmust_fail(1)\n'}


def _vac_root(docstring, test_body=None, tests=None):
    """A miniature repo with ONE compliant gate whose docstring is `docstring`,
    plus optional extra test files."""
    body = (f'"""{docstring}"""\n' if docstring else "") + COVERED
    t = dict(COMPLIANT_TESTS)
    if test_body is not None:
        t["t2_vac.py"] = test_body
    t.update(tests or {})
    return _root({"loud.py": body}, t)


def _vac(docstring, test_body=None, tests=None, floor=None):
    """(gca, root, fails, stats) for a miniature repo — the whole G-VACUOUS
    check run in-process against one synthetic gate."""
    import gate_contract_audit as gca                       # noqa: E402
    root = _vac_root(docstring, test_body, tests)
    rows = gca.audit(root)["gates"]
    check(len(rows) == 1, f"the miniature repo must hold exactly one gate, "
                          f"got {[r['script'] for r in rows]}")
    keep = gca.VACUITY_FLOOR
    if floor is not None:
        gca.VACUITY_FLOOR = floor
    try:
        fails, stats = gca.check_vacuity(root, rows)
    finally:
        gca.VACUITY_FLOOR = keep
    return gca, root, fails, stats


@test("G-VACUOUS FAILS a gate that DECLARES a vacuity condition and ships no "
      "fixture for it", kind="known_bad")
def t_vacuity_prose_without_a_fixture_fails():
    """THE POINT OF THE WHOLE CHECK. A declared blind spot with no fixture is
    strictly WORSE than an undeclared one: it reads as diligence and grades
    nothing. That is the `keep_short` defect one level up — 39 of 181 budgets
    named the DATASHEET's reference-design pin function (`VCC`, `VDD`, `VREF`,
    `D+`) instead of a net any board has, so none of cooksense's logic
    decoupling was budget-graded while 181 budgets sat in source looking like
    coverage. If G-VACUOUS accepted prose it would become exactly the paperwork
    it was built to prevent.

    RED-VERIFIED against the real tree, which is the strongest available form:
    with the five `VACUITY:` blocks written and no fixtures yet, the auditor
    reported (2026-07-29, measured, quoted verbatim):

        G-VACUOUS: 0/31 gate(s) declare a vacuity condition WITH a fixture
        that exercises it (floor 5); 26 OWED
        FAIL G-VACUOUS .../part_facts_check.py: its docstring declares a
        VACUITY: condition and NO tests/ fixture exercises it
        ... x5, plus the floor ...
        G-CONTRACT FAIL: 6 obligation(s) unmet

    i.e. the five prose-only declarations each failed and the floor failed with
    them. The synthetic fixture below is what pins it, so the test does not go
    green merely because those five have since been fixtured."""
    _, _, fails, stats = _vac(
        "a gate\n\nVACUITY: passes when the input list is empty.\n", floor=0)
    check(any("NO tests/ fixture exercises it" in f for f in fails),
          f"a prose-only declaration must FAIL:\n{fails}")
    eq(stats["bound"], [], "nothing is bound")


@test("G-VACUOUS FAILS a vacuity fixture whose gate declares nothing",
      kind="known_bad")
def t_vacuity_fixture_without_prose_fails():
    """The other direction of the binding. A fixture that pins a blind spot
    while the gate's own docstring says nothing puts the finding somewhere no
    reader of the gate will look — and then a docstring rewrite cannot
    contradict a fixture nobody reads. Both homes or neither."""
    _, _, fails, stats = _vac(
        "a gate with no declaration",
        '@test("x", kind="vacuity", gate="loud.py")\n'
        'def t_x():\n    must_pass(0, "x")\n', floor=0)
    check(any("no VACUITY: block" in f for f in fails),
          f"an orphan fixture must FAIL:\n{fails}")


@test("G-VACUOUS FAILS a `vacuity` fixture whose FIRST assertion is must_fail "
      "— it has DISPROVED the blind spot it claims", kind="known_bad")
def t_vacuity_fixture_asserting_must_fail_is_a_false_declaration():
    """A FALSE DECLARATION, caught statically. A vacuity fixture asserts the
    gate PASSES on input whose graded fact is false. One asserting `must_fail`
    on that input proves the gate BITES there, so the docstring's claim is
    false — and a falsely-declared blind spot is worse than an undeclared one
    for the same reason prose is: it reads as an honest limitation and is not
    one. The right move when a blind spot closes is to convert the fixture to
    `kind="known_bad"`, which is what the message says.

    WHY IT IS THE **FIRST** ASSERTION AND NOT ANY. This check shipped, for about
    ten minutes, as "any `must_fail` in the body is a false declaration" — and
    it immediately flagged two of the four real fixtures seeded the same day
    (measured: `t_vacuity_all_deferred_or_all_config_prints_OK_over_a_zero_
    denominator` and `t_vacuity_E_OFF_is_N_A_on_a_battery_board_that_declares_
    nothing`). Both were correct. Each asserts the blind spot AND THEN a
    CONTRAST — the same input changed in exactly one way, which the gate DOES
    catch — and the contrast is what distinguishes a blind spot from a fact the
    gate simply cannot represent. Rejecting the best fixtures in the set is the
    adjacent-property error this repo keeps paying for (canon M-WIDTH), so the
    rule now grades the SUBJECT assertion: first pass/fail call must be a
    must_pass. `t_vacuity_a_must_fail_CONTRAST_after_the_subject_is_allowed`
    holds the other side."""
    _, _, fails, _s = _vac(
        "a gate\n\nVACUITY: passes on an empty list.\n",
        '@test("x", kind="vacuity", gate="loud.py")\n'
        'def t_x():\n    must_fail(1, "x")\n', floor=0)
    check(any("declaration is FALSE" in f for f in fails),
          f"a must_fail vacuity fixture must FAIL:\n{fails}")


@test("G-VACUOUS ALLOWS a must_fail CONTRAST after the must_pass on the "
      "vacuity input — the best fixtures all have one")
def t_vacuity_a_must_fail_CONTRAST_after_the_subject_is_allowed():
    """The other side of the ordering rule, and the reason it is an ordering
    rule at all. A fixture that asserts the gate passes on the blind-spot input
    and THEN that it fails on the one-field-changed contrast is the strongest
    form available: it proves the gate can grade the fact, and that this
    particular input escapes it. All four gates seeded on 2026-07-29 are written
    this way, and the first version of the check rejected two of them."""
    _, _, fails, stats = _vac(
        "a gate\n\nVACUITY: passes on an empty list.\n",
        '@test("x", kind="vacuity", gate="loud.py")\n'
        'def t_x():\n'
        '    must_pass(0, "the empty list — THE BLIND SPOT")\n'
        '    must_fail(1, "the CONTRAST: one row present, and it is graded")\n',
        floor=1)
    eq(fails, [], f"a subject-then-contrast fixture must be accepted:\n{fails}")
    eq(stats["bound"], ["loud.py"], "and counted as bound")


@test("G-VACUOUS FAILS a `vacuity` fixture that asserts NOTHING",
      kind="known_bad")
def t_vacuity_fixture_with_no_assertion_fails():
    """Prose in a .py file is still prose. A fixture with no
    must_pass/check/eq in its body has moved the paperwork, not replaced it."""
    _, _, fails, _s = _vac(
        "a gate\n\nVACUITY: passes on an empty list.\n",
        '@test("x", kind="vacuity", gate="loud.py")\n'
        'def t_x():\n    pass\n', floor=0)
    check(any("asserts NOTHING" in f for f in fails),
          f"an inert vacuity fixture must FAIL:\n{fails}")


@test("G-VACUOUS FAILS a vacuity fixture naming a gate that is not in the "
      "inventory — a rename must not silently un-declare", kind="known_bad")
def t_vacuity_fixture_naming_an_unknown_gate_fails():
    """The binding is by NAME, so the binding can rot. If `loud.py` is renamed
    and its fixture keeps the old name, the gate silently loses its declaration
    and the fixture silently grades nothing — the `has_red_fixture` prose hole
    in a new costume."""
    _, _, fails, _s = _vac(
        "a gate\n\nVACUITY: passes on an empty list.\n",
        '@test("x", kind="vacuity", gate="loud.py")\n'
        'def t_x():\n    must_pass(0, "x")\n'
        '@test("y", kind="vacuity", gate="renamed_away.py")\n'
        'def t_y():\n    must_pass(0, "y")\n', floor=0)
    check(any("not in the verdict-printing inventory" in f for f in fails),
          f"a fixture naming an unknown gate must FAIL:\n{fails}")


@test("G-VACUOUS PASSES a gate declared in BOTH homes, with a fixture that "
      "asserts the gate passes")
def t_vacuity_declared_and_fixtured_passes():
    """THE OTHER HALF OF DISCRIMINATION. A check that only ever fails ranks
    nothing. A correctly-declared, correctly-fixtured gate must produce ZERO
    G-VACUOUS findings, or the whole family is just failing everything."""
    _, _, fails, stats = _vac(
        "a gate\n\nVACUITY: it passes when the input list is empty, because\n"
        "an empty list has no row that can disagree.\n",
        '@test("x", kind="vacuity", gate="loud.py")\n'
        'def t_x():\n    must_pass(0, "the empty list")\n', floor=1)
    eq(fails, [], "a fully compliant declaration must produce no findings")
    eq(stats["bound"], ["loud.py"], "and it is counted as bound")
    eq(stats["owed"], [], "with nothing owed")


@test("G-VACUOUS PASSES a repo where NO gate declares anything — its OWN "
      "declared blind spot", kind="vacuity", gate="gate_contract_audit.py")
def t_vacuity_G_VACUOUS_passes_a_repo_where_no_gate_declares_anything():
    """G-VACUOUS'S OWN VACUITY CONDITION (the executable half of the `VACUITY:`
    block in gate_contract_audit.py's docstring).

    G-VACUOUS grades "every gate's blind spot is known". It PASSES on a repo
    where NOTHING is declared, because absence is OWED rather than a violation.
    That is deliberate — a day-one mandate over 31 gates lands as 31 red rows
    and is disabled within the week — and it means the exit code is compatible
    with the graded fact being false for the whole fleet.

    THE CIRCLE, AND HOW IT IS BROKEN. Asking a coverage gate to police its own
    adoption only regresses: whatever it accepts, it accepts. So the vacuity is
    not eliminated, it is made BOUNDED (the blind spot is exactly `owed`),
    ENUMERATED (every owed gate is printed by name on every run — which is what
    separates this from all six instances, each of which passed with nothing
    said) and MONOTONE (`VACUITY_FLOOR` is a committed integer and a drop below
    it is a hard FAIL, pinned from outside by
    `t_vacuity_floor_is_pinned_to_the_measured_count`).

    Both halves are asserted here:
      1. SYNTHETIC — a repo of compliant gates declaring nothing, floor 0:
         zero findings, everything owed. Absence is free.
      2. REAL TREE — the auditor exits 0 today while N gates are owed, and
         names every one of them. That is the live measurement of the blind
         spot, and it is why the owed list is printed rather than counted."""
    _, _, fails, stats = _vac("a gate with no vacuity declaration", floor=0)
    eq(fails, [], "NOTHING is declared and G-VACUOUS has no finding — this is "
                  "the blind spot, stated as an assertion")
    eq(stats["owed"], ["loud.py"], "the whole inventory is owed")

    # (2) the real tree: passes, with the remainder named rather than counted.
    r = must_pass(run([KPY, TOOL, "--root", ROOT]),
                  "G-VACUOUS exits 0 on the real tree while gates are still "
                  "OWED — THE BLIND SPOT. If this now FAILS because adoption "
                  "reached the whole fleet, convert this fixture to a "
                  "known_bad with the floor raised to the inventory size")
    m = re.search(r"G-VACUOUS: (\d+)/(\d+) gate\(s\) declare a vacuity "
                  r"condition WITH a fixture that exercises it "
                  r"\(floor (\d+)\); (\d+) OWED", r.out)
    check(m is not None, f"the G-VACUOUS coverage line changed shape:\n{r.out}")
    bound, total, floor, owed = (int(g) for g in m.groups())
    check(owed > 0, "if nothing is owed the blind spot has closed — see above")
    eq(bound + owed, total, "every gate is either bound or owed; a gate in "
                            "neither bucket would be a silent third state")
    named = len(re.findall(r"^  OWED G-VACUOUS ", r.out, re.M))
    eq(named, owed, "EVERY owed gate is named. A remainder reported as a bare "
                    "count is how a partial rollout becomes permanent")


@test("G-VACUOUS's floor is PINNED to what the tree achieves — it cannot be "
      "lowered to buy a green run, nor lag adoption silently")
def t_vacuity_floor_is_pinned_to_the_measured_count():
    """THE OUTSIDE OF THE CIRCLE. `VACUITY_FLOOR` is the one thing that makes
    G-VACUOUS's own vacuity monotone, so it cannot be graded by G-VACUOUS —
    that is the circularity. It is graded HERE instead, by measuring the tree
    and comparing:

      * floor <= achieved, or the gate fails for a reason nobody can fix by
        writing a declaration (a floor above the tree is a broken build, not a
        ratchet);
      * floor == achieved, so the floor cannot silently lag adoption either. A
        floor of 5 on a tree with 20 bound would let 15 declarations be deleted
        for free.

    Together: the floor may only be edited UP, in the same commit that raises
    the achieved count. That is a human editing a committed integer in a file a
    reviewer reads, checked by a measurement — none of it reachable from inside
    the audit."""
    import gate_contract_audit as gca                       # noqa: E402
    rows = gca.audit(ROOT)["gates"]
    _, stats = gca.check_vacuity(ROOT, rows)
    n = len(stats["bound"])
    eq(gca.VACUITY_FLOOR, n,
       f"VACUITY_FLOOR is {gca.VACUITY_FLOOR} and {n} gate(s) actually carry a "
       f"fixtured vacuity condition. Raise the floor in the SAME commit that "
       f"adds a declaration; never lower it to make a run green")
    check(n >= 5, f"only {n} gate(s) have a fixtured vacuity condition — the "
                  f"five seeded on 2026-07-29 (part_facts_check, twin_overlay, "
                  f"power_topology, waiver_provenance, gate_contract_audit) are "
                  f"the floor of the rollout, not a target")


@test("G-VACUOUS does NOT accept a `VACUITY:` outside the module docstring — "
      "the R-LEN defect, not reproduced", kind="known_bad")
def t_vacuity_prose_outside_the_module_docstring_is_not_a_declaration():
    """THE DEFECT THIS WHOLE FAMILY EXISTS FOR, APPLIED TO ITSELF.

    `R-LEN` is `bool(re.search(r"length|spread", audit_src, re.I))` over the raw
    text of a board's `audit_board.py`. MEASURED 2026-07-29: 3 of 6 boards get
    PASS, and smc0985-cooksense gets it on ZERO code matches — its only two hits
    are `slot-lengthened` and `lengthens`, both in COMMENTS about high-voltage
    creepage, neither about timing. Meanwhile pluto-cal-switch, which carries an
    ADR titled "length match is a published artifact", grades N-A "no
    timing-critical nets declared".

    A gate-on-gates that accepted a `VACUITY:` anywhere in a file would commit
    that exact error in the act of policing it. So `vacuity_declaration` reads
    `ast.get_docstring` and nothing else. Three placements are tested, and all
    three must be REJECTED — a comment, a nested function's docstring, and a
    string literal in code. Each is followed by a real fixture, so the ONLY
    reason the auditor can fail here is that it declined to see the prose."""
    fixture = ('@test("x", kind="vacuity", gate="loud.py")\n'
               'def t_x():\n    must_pass(0, "x")\n')
    for where, body in (
            ("a comment",
             "# VACUITY: passes on an empty list.\n" + COVERED),
            ("a nested docstring",
             COVERED + '\n\ndef helper():\n'
             '    """VACUITY: passes on an empty list."""\n    return 1\n'),
            ("a code string",
             COVERED + '\nBANNER = "VACUITY: passes on an empty list."\n')):
        d = _root({"loud.py": body},
                  {"t1_loud.py": 'TOOL = SCRIPTS / "loud.py"\nmust_fail(1)\n',
                   "t2_vac.py": fixture})
        import gate_contract_audit as gca                   # noqa: E402
        rows = gca.audit(d)["gates"]
        keep, gca.VACUITY_FLOOR = gca.VACUITY_FLOOR, 0
        try:
            fails, stats = gca.check_vacuity(d, rows)
        finally:
            gca.VACUITY_FLOOR = keep
        eq(stats["declared"], [],
           f"a VACUITY: in {where} must NOT count as a declaration — that is "
           f"R-LEN's defect, which credits the word 'lengthens' in a comment "
           f"about creepage")
        check(any("no VACUITY: block" in f for f in fails),
              f"with {where} the gate is UNDECLARED and its fixture is an "
              f"orphan, which must fail:\n{fails}")


# --------------------------------------------- G-VACUOUS, the DRU predicate class
# The worst instance on the 2026-07-29 list is not a Python gate: cooksense's
# `keypad_isolation_6mm` .kicad_dru rule ends `&& B.NetName != ''`, so unnetted
# copper is exempt BY CONSTRUCTION and DRC ITSELF reported zero. A rule-file
# predicate that cannot fire on the geometry it names is the same defect.

#: what a board HAS. check_dru_vacuity is inventory-driven and geometry-free, so
#: the same function grades a synthetic fixture and a real board.
INV = {"netclasses": {"KEYPAD_ISO", "DEFAULT"}, "nets": {"KP_U1", "GND"},
       "areas": {"pad_rescue_stubs"}, "unnetted": 8}


def _dru(cond, constraint="clearance", name="iso_6mm"):
    return (f'(version 1)\n(rule "{name}"\n'
            f'  # a comment\n'
            f'  (condition "{cond}")\n'
            f'  (constraint {constraint} (min 6.0mm)))\n')


@test("G-VACUOUS-DRU FAILS a clearance rule that exempts UNNETTED copper — "
      "the instance that made DRC itself report zero", kind="known_bad")
def t_dru_netname_nonempty_exemption_fails():
    """THE INCIDENT, MEASURED. `projects/smc0985-cooksense/04_kicad/
    cooksense.kicad_dru:31`:

        (rule "keypad_isolation_6mm"
          (condition "A.NetClass == 'KEYPAD_ISO' && B.NetClass != 'KEYPAD_ISO'
                      && B.NetName != ''")
          (constraint clearance (min 6.0mm)))

    Re-measured 2026-07-29 with pcbnew: 14 nets are in KEYPAD_ISO (412 copper
    items); the board carries 8 unnetted copper pads, among them
    `J_KEY_MATRIX.MP` — the keypad connector's own SM10B-GHS-TB shell tabs, which
    is the tab the rule was written for. Minimum distance from any KEYPAD_ISO
    copper to any unnetted copper: **1.0672 mm against a 6.000 mm constraint, a
    5.6x violation, on 106 pairs**, every one silenced by the third conjunct.
    The project's own `apply_drc_policy.py:31-39` independently records "without
    it the keypad rule reports 71 violations", corroborating the direction.

    So "0 DRC violations / 0 unconnected / 0 parity" — this repo's headline
    gate — was never evidence about the one connector tab the rule existed for.
    A barrier rule's whole purpose is copper that may be unnetted: a shell tab,
    a mounting pad, a fill island."""
    import gate_contract_audit as gca                       # noqa: E402
    fails, n = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.NetClass == 'KEYPAD_ISO' && B.NetClass != 'KEYPAD_ISO' "
        "&& B.NetName != ''")), INV)
    eq(n, 1, "one predicate graded (the denominator, canon M-COVER)")
    eq(len(fails), 1, f"the exemption must be the one finding:\n{fails}")
    contains(fails[0], "EXEMPT BY", "names the defect")
    contains(fails[0], "8 unnetted copper item(s)",
             "quotes the inventory, so the finding is about THIS board")
    # THE REAL NUMBER WAS RECONCILED, NOT ACCEPTED. A first forensic pass
    # reported 8 unnetted pads on cooksense; `dru_inventory` measures 2, because
    # 6 of the 8 are NPTH (H1-H4 and J_TC's two) and sit on NO copper layer, so
    # they cannot violate a copper clearance rule. The honest count is 2 — and
    # BOTH are `J_KEY_MATRIX.MP`, the shell tabs the rule exists for, which makes
    # the finding sharper. `INV` here carries a synthetic 8 only to prove the
    # message quotes whatever inventory it is given; the board's own number is
    # asserted in t_dru_flags_the_real_cooksense_rule_file.


@test("G-VACUOUS-DRU FAILS a rule naming a netclass no net belongs to — it can "
      "never fire", kind="known_bad")
def t_dru_dead_netclass_fails():
    """The class-general form, and the reason this is not a one-pattern check.
    A rule whose required conjunct names a netclass, net or rule area the board
    does not have fires NEVER, and DRC reports zero for it by construction —
    identical in effect to the exemption above and invisible in the same way.
    This is the shape a netclass rename produces: the rule survives, its subject
    does not."""
    import gate_contract_audit as gca                       # noqa: E402
    fails, n = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.NetClass == 'KEYPAD_ISOLATION' && B.NetClass != 'KEYPAD_ISO'")), INV)
    eq(n, 1, "one predicate graded")
    eq(len(fails), 1, f"the dead netclass must be the one finding:\n{fails}")
    contains(fails[0], "can NEVER be true", "names the defect")
    contains(fails[0], "KEYPAD_ISOLATION", "names the value that does not exist")


@test("G-VACUOUS-DRU FAILS a rule whose insideArea names no rule area",
      kind="known_bad")
def t_dru_dead_area_fails():
    """Same class, third member (canon M-WIDTH: name the category and enumerate
    it). `insideArea` is how every scoped-floor rule in this repo is written, so
    a renamed keepout silently disarms one."""
    import gate_contract_audit as gca                       # noqa: E402
    fails, n = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.insideArea('efuse_padentry') && (A.NetName == 'GND')")), INV)
    eq(n, 1, "one predicate graded")
    check(any("efuse_padentry" in f and "can NEVER be true" in f
              for f in fails), f"the dead area must fail:\n{fails}")


@test("G-VACUOUS-DRU PASSES a live rule, and does not flag a NetName != '' "
      "outside a clearance constraint")
def t_dru_live_rule_passes():
    """DISCRIMINATION, both edges. A check that flags every rule ranks nothing,
    and the two edges are where a proxy goes wrong:

      1. a rule whose netclasses all exist and which does not exempt unnetted
         copper must PASS;
      2. `NetName != ''` is only a defect on a CLEARANCE-family constraint,
         where unnetted copper is the subject. On a `track_width` it is a
         legitimate scope — the generator's own line 303 writes net-name
         conditions for exactly that, and flagging it would false-fail the
         shared backend."""
    import gate_contract_audit as gca                       # noqa: E402
    fails, n = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.NetClass == 'KEYPAD_ISO' && B.NetClass != 'KEYPAD_ISO'")), INV)
    eq(n, 1, "one predicate graded")
    eq(fails, [], f"a live barrier rule must PASS:\n{fails}")

    fails2, _ = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.NetName != '' && A.NetClass == 'KEYPAD_ISO'",
        constraint="track_width")), INV)
    eq(fails2, [], f"a net-scoped track_width rule is not a barrier and must "
                   f"PASS:\n{fails2}")


@test("G-VACUOUS-DRU does not flag a DISJUNCTION with one live branch")
def t_dru_disjunction_with_a_live_branch_passes():
    """The adjacent-property trap. `(A.NetName == 'X' || A.NetName == 'Y')` with
    only X on the board still fires, so flagging it would be a false positive of
    the exact kind that gets a gate switched off. A rule is dead only when EVERY
    alternative carries a dead conjunct — which is asserted from both sides
    here."""
    import gate_contract_audit as gca                       # noqa: E402
    fails, _ = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.NetName == 'GND' || A.NetName == 'NO_SUCH_NET'")), INV)
    eq(fails, [], f"one live branch is enough to fire:\n{fails}")

    dead, _ = gca.check_dru_vacuity(gca.parse_dru(_dru(
        "A.NetName == 'NO_SUCH_NET' || A.NetName == 'ALSO_ABSENT'")), INV)
    check(any("can NEVER be true" in f for f in dead),
          f"ALL branches dead must still FAIL, or the disjunction handling has "
          f"become an escape hatch:\n{dead}")


@test("G-VACUOUS-DRU flags the REAL cooksense rule file, read from the tree",
      kind="known_bad")
def t_dru_flags_the_real_cooksense_rule_file():
    """THE ACCEPTANCE TEST. A synthetic fixture proves the checker discriminates;
    it does not prove the checker sees the incident. This reads the actual
    sealed-adjacent `04_kicad/cooksense.kicad_dru` — READ-ONLY, no project file
    is written — and requires BOTH barrier rules to be flagged by name.

    Skipped-with-a-loud-note if the board is absent rather than passing quietly,
    because "the file moved" and "the defect is fixed" must not look the same
    (canon M-COVER: input it cannot read is never a silent skip).

    RED-VERIFIED, and the measurement is the whole argument for this arm. At the
    pre-fix commit (2026-07-29, this suite's own HEAD before the change):

        $ /usr/bin/python3 skills/kicad-pcb/scripts/gate_contract_audit.py --root .
          coverage: 31/31 verdict-printing scripts audited ...
        G-CONTRACT OK: 31 verdict-printing script(s) meet G-INPUT/G-COVER/G-RED
        PRE-FIX EXIT=0

    Thirty-one gates satisfying three obligations each, all green, while two
    barrier rules on a live board exempted the exact copper they existed to hold
    off. After, with `--dru` pointed at the board:

        G-VACUOUS-DRU: 11 predicate(s) graded in cooksense.kicad_dru against
        cooksense.kicad_pcb
        FAIL G-VACUOUS-DRU cooksense.kicad_dru:29 rule "keypad_isolation_6mm" ...
        FAIL G-VACUOUS-DRU cooksense.kicad_dru:33 rule "opto_isolation_2mm" ...

    2 of 11 predicates flagged — so the other 9, including every `insideArea`
    scoped-floor rule on that board, are graded and PASS. A checker that flagged
    all 11 would be useless."""
    import gate_contract_audit as gca                       # noqa: E402
    # READ THE SEALED RELEASE, NOT `04_kicad/`. This fixture went red the moment
    # it was merged into main, and not because the checker was wrong: cooksense's
    # LIVE board was mid-rebuild, so its `.kicad_dru` did not yet carry the
    # barrier rules at all (`apply_drc_policy.py` re-applies them AFTER
    # `generate_rules`) and `KEYPAD_ISO` was absent from its `.kicad_pro`, where
    # netclasses actually live — 0 occurrences live against 15 in the seal,
    # exactly the clobber canon R1 warns about. A gate whose verdict depends on
    # whether a sibling happens to be rebuilding is not a gate.
    #
    # This is the THIRD time today a test broke by reading mutable project
    # state (`t1_fleet_regrade` did, and the copper-length gate pre-empted it by
    # choosing the seal for the same reason). Sealed bytes are the right oracle
    # for an acceptance fixture — canon M-SHIP — and they are also flake-free.
    dru = (ROOT / "projects/smc0985-cooksense/07_releases"
           / "cooksense-v1.6-2026-07-27/source/cooksense.kicad_dru")
    if not dru.exists():
        raise Failed(f"{dru} is gone — this acceptance test cannot go quiet; "
                     f"repoint it at the board that carries the barrier rules "
                     f"or retire it deliberately")
    rules = gca.parse_dru(dru.read_text(encoding="utf-8-sig"))
    check(len(rules) >= 4, f"only {len(rules)} rules parsed out of the real "
                           f"file — the s-expression scan has regressed")
    inv = gca.dru_inventory(dru.with_suffix(".kicad_pcb"))
    eq(inv["unnetted"], 2,
       "the board carries exactly 2 unnetted COPPER items, and both are "
       "J_KEY_MATRIX.MP — the keypad connector's SM10B-GHS-TB shell tabs, which "
       "is the tab keypad_isolation_6mm was written for. (A first forensic pass "
       "reported 8; the other 6 are NPTH holes on no copper layer and cannot "
       "violate a copper clearance rule. Reconciled 2026-07-29 — the corrected "
       "number is the sharper one.)")
    check("KEYPAD_ISO" in inv["netclasses"],
          f"the netclass the rule names IS live on the board, so the rule is "
          f"flagged for the EXEMPTION and not for a dead conjunct — the two arms "
          f"must not be confusable: {sorted(inv['netclasses'])[:8]}")
    fails, n = gca.check_dru_vacuity(rules, inv, source=dru.name)
    eq(n, len(rules), f"every rule with a condition is graded: {n}/{len(rules)}")
    exempt = [f for f in fails if "EXEMPT BY" in f]
    eq(len(exempt), 2, f"both barrier rules must be flagged — measured "
                       f"2026-07-29 as keypad_isolation_6mm and "
                       f"opto_isolation_2mm:\n{fails}")
    check(any("keypad_isolation_6mm" in f for f in exempt),
          f"the 6 mm keypad barrier is named:\n{exempt}")
    check(any("opto_isolation_2mm" in f for f in exempt),
          f"the 2 mm opto barrier carries the same conjunct:\n{exempt}")


# ------------------------------- G-VACUOUS-DRU, the PRESERVED-rule species
# A rule can clear every name-existence check and still be dead, because a
# PRESERVED rule is not regenerated: `generate_rules_generic.foreign_dru_rules`
# carried any rule it did not own forward on every run and nothing ever retired
# one, so `pad_rescue_stubs` outlived the stubs it exempted. Name-existence
# (check 1, and `rules_audit`'s A-FIRE) cannot see this — the rule area is still
# on the board, it is merely EMPTY. Only geometry answers it.

MEMBER_INV = {"netclasses": {"PWR"}, "nets": {"GND", "5V"},
              "areas": {"pad_rescue_stubs"}, "unnetted": 0}
STUB_RULE = ("(version 1)\n(rule pad_rescue_stubs\n"
             "  (condition \"A.insideArea('pad_rescue_stubs') "
             "&& (A.NetName == 'GND')\")\n"
             "  (constraint track_width (min 0.300mm)))\n")


@test("G-VACUOUS-DRU reads a BARE rule name — the spelling every "
      "pad_rescue_stubs on every board uses", kind="known_bad")
def t_dru_grades_bare_rule_names():
    """THE GATE WAS BLIND TO ITS OWN SUBJECT, and this is the measurement.
    `.kicad_dru` allows both `(rule "X"` and `(rule X`; generate_rules writes
    the quoted form, stitch's `_append_stub_dru` writes the bare one. `parse_dru`
    required the quotes, so on 2026-07-31 it graded **77 of the fleet's 83
    rules** — and all 6 it skipped were `pad_rescue_stubs`, i.e. every instance
    of the ONE rule family that is preserved rather than regenerated, and the
    family this gate's own docstring is about. Six ungraded rules read as six
    clean ones.

    Every other rule-name matcher in the tree already handled the bare form
    (`rules_audit.dru_rules`, `escape_check._RULE_HEAD_RE`,
    `generate_rules_generic.extract_rules`) — swept 2026-07-31, 6 matchers,
    this was the only blind one.

    RED against the old `re.finditer(r'\\(rule\\s+"([^"]*)"')`: it returns zero
    rules here, so `n` is 0 and nothing is graded."""
    import gate_contract_audit as gca                       # noqa: E402
    rules = gca.parse_dru(STUB_RULE)
    eq(len(rules), 1, f"the bare-named rule must be parsed: {rules}")
    eq(rules[0]["name"], "pad_rescue_stubs", "bare name recovered verbatim")
    eq(rules[0]["constraints"], ["track_width"], "its constraint is read too")
    # and it is GRADED, not merely parsed
    _fails, n = gca.check_dru_vacuity(rules, MEMBER_INV)
    eq(n, 1, "a bare-named rule must count in the denominator")


@test("G-VACUOUS-DRU FAILS a rule whose rule area is LIVE but EMPTY — the "
      "species name-existence cannot see", kind="known_bad")
def t_dru_live_area_with_zero_members_fails():
    """Every name in the condition resolves — `pad_rescue_stubs` IS in the
    inventory's areas, `GND` IS a net — so check (1) passes it and so does
    `rules_audit`'s A-FIRE. Zero board items match it regardless, which is what
    `dru_area_members` measures from geometry. This is the state a preserved
    rule decays into once the pass that owned it stops emitting stubs there.

    RED before check (3) existed: with `members` unread the rule draws no
    finding at all."""
    import gate_contract_audit as gca                       # noqa: E402
    rules = gca.parse_dru(STUB_RULE)
    fails, n = gca.check_dru_vacuity(rules, MEMBER_INV,
                                     members={"pad_rescue_stubs": 0})
    eq(n, 1, "one predicate graded (the denominator, canon M-COVER)")
    eq(len(fails), 1, f"the empty area must be the one finding:\n{fails}")
    contains(fails[0], "ZERO board items match it", "names the defect")
    contains(fails[0], "no subject left", "names why it is not a dead-name case")


@test("G-VACUOUS-DRU PASSES the same rule when its area still has members, and "
      "is SILENT when membership is not derivable")
def t_dru_live_area_with_members_passes():
    """THE CONTRAST, and the constraint on the fix. 4 of the fleet's 6
    `pad_rescue_stubs` rules had live subjects on 2026-07-31 (377, 44, 41 and 5
    members); a check that flagged them would push a rebuild into deleting four
    live exemptions. `None` — not derivable — must be as silent as a positive
    count, because retirement requires a positively derived zero."""
    import gate_contract_audit as gca                       # noqa: E402
    rules = gca.parse_dru(STUB_RULE)
    for members, what in (({"pad_rescue_stubs": 25}, "a populated area"),
                          ({"pad_rescue_stubs": None}, "an underivable one"),
                          ({}, "no geometry read at all")):
        fails, n = gca.check_dru_vacuity(rules, MEMBER_INV, members=members)
        eq(n, 1, f"{what}: still graded")
        eq(len(fails), 0, f"{what} must draw no finding:\n{fails}")


@test("the emptiness verdict is derived TWICE by different methods, and they "
      "agree (canon M1)", slow=True)
def t_dru_members_two_methods_agree():
    """CHECKER AND CHECKED SHARE NO METHOD. `generate_rules_generic` decides
    retirement with `dru_subject`, which parses the `.kicad_pcb` as TEXT and
    runs its own point-in-polygon; `gate_contract_audit.dru_area_members` asks
    pcbnew's object model and SHAPE_POLY_SET. If the gate reused the emitter's
    derivation it would prove nothing about it.

    Built here on a synthetic board rather than a fleet one on purpose: a board
    mid-route moves under the test, and this asserts a property of the two
    METHODS, not of any board. (The same agreement was measured across the real
    fleet on 2026-07-31 — 20 member-counted rules, identical counts under both
    derivations, including 377/44/41/5/0/0 for `pad_rescue_stubs`.)"""
    import json
    import shutil
    sys.path.insert(0, str(ROOT / "tests"))
    from t1_rules_bom import LC, RULE_AREA, _first_seg      # noqa: E402
    d = tmpdir("m1cross_")
    pcb = d / "b.kicad_pcb"
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_pcb", pcb)
    x0, y0, x1, y1 = _first_seg(pcb.read_text(encoding="utf-8-sig"), "5V")
    txt = pcb.read_text(encoding="utf-8-sig").rstrip()
    pcb.write_text(txt[:-1]
                   + RULE_AREA.format(name="live_area", tag=1,
                                      x0=min(x0, x1) - 0.5, y0=min(y0, y1) - 0.5,
                                      x1=max(x0, x1) + 0.5, y1=max(y0, y1) + 0.5)
                   + RULE_AREA.format(name="empty_area", tag=2,
                                      x0=5.0, y0=5.0, x1=8.0, y1=8.0)
                   + ")\n")
    dru = d / "b.kicad_dru"
    dru.write_text("(version 1)\n" + "".join(
        f"(rule {n}\n  (condition \"A.insideArea('{a}') "
        f"&& (A.NetName == '5V')\")\n"
        f"  (constraint track_width (min 0.300mm)))\n"
        for n, a in (("live", "live_area"), ("empty", "empty_area"),
                     ("gone", "no_such_area"))))

    code = ("import json,sys;sys.path.insert(0,%r);"
            "import gate_contract_audit as g;"
            "print('@@'+json.dumps(g.dru_area_members(sys.argv[1],"
            "g.parse_dru(open(sys.argv[2]).read()))))"
            % str(ROOT / "skills/kicad-pcb/scripts"))
    r = must_pass(run([KPY, "-c", code, str(pcb), str(dru)]), "pcbnew method")
    by_pcbnew = json.loads(r.out.split("@@", 1)[1].strip())

    sys.path.insert(0, str(ROOT / "skills/kicad-pcb/scripts"))
    import dru_subject                                       # noqa: E402
    from generate_rules_generic import extract_rules         # noqa: E402
    inv = dru_subject.index_board(pcb)
    by_text = {n: dru_subject.members(b, inv)
               for n, b in extract_rules(dru.read_text())}

    eq(by_text, by_pcbnew, "the two derivations must agree rule for rule")
    check(by_text["live"] > 0, f"the populated area must have members: {by_text}")
    eq(by_text["empty"], 0, "an area over bare laminate has none")
    eq(by_text["gone"], 0, "an area that is not on the board has none")


if __name__ == "__main__":
    sys.exit(main())
