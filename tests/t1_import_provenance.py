#!/usr/bin/env python3
"""T1: M-IMPORT / D-MATE — the provenance of facts that come from OUTSIDE.

Every other gate in this repo compares our artifacts to our artifacts. A fact
about someone else's hardware enters the pipeline through a human's eyes and no
gate reads it. One nearly reached copper (2026-07-27, ADR-0005):

  pluto-cal-switch mates to an ADALM-PlutoPlus SMA panel whose vendor publishes
  NO PCB source. The three-connector span was extracted from an undimensioned
  vector assembly plot at 35.60 mm; THREE independent extractions agreed to
  0.003 mm, and a floorplan was ready to be built on it. A caliper on two
  physical units then read 35.04 mm (genuine) and 34.72 mm (a 2025 clone),
  against a rigid-SMA mating window of +-0.05 mm. 10-18x the window.

THE HEADLINE KNOWN-BAD IS THAT RECORD, VERBATIM, AS IT STOOD BEFORE THE
CALIPER — `t_pre_caliper_estimate_spent_on_a_dimension` and its twin
`t_pre_caliper_graded_as_measured`. The defect supplied its own fixture; both
numbers below are the real ones.

RED-VERIFIED, and here is the measurement (new-gate variant, per
tests/README "Adding a regression"): `import_provenance_check.py` did not exist
before this change, so there is no pre-fix code to run the whole suite against.
The two headline fixtures were instead verified against a DELIBERATELY NEUTERED
checker, and here are the runs:

  * M-BAR's `if grade == "ESTIMATED" and use == "dimensional"` block disabled
    -> 18 passed, 2 FAILED — `t_pre_caliper_estimate_spent_on_a_dimension` and
    `t_unreadable_bar`, both with "SHOULD HAVE FAILED but exited 0". Nothing
    else moved.
  * M-PROXY's `if grade in ("MEASURED", "CITED") and words` block disabled
    -> 19 passed, 1 FAILED — `t_pre_caliper_graded_as_measured`, same message.

Restored byte-identical, 22 passed / 16 known-bad. Every other known-bad here
is the clean synthetic tree broken in exactly ONE way, and each asserts the
checker failed for the RIGHT reason by naming its check ID.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

import yaml                                                      # noqa: E402

IMPORTC = SCRIPTS / "import_provenance_check.py"

# The device record, in miniature — the same shape as
# external_hardware/plutoplus_hardware:
# a human document that states, per number, how it was obtained.
RECORD = """# Widget hardware — measured

Taken with calipers on the physical unit.

| span | value |
|---|---|
| **total span** | **35.04** |

Extracted from the vendor's undimensioned assembly plot: span **35.60** mm.

Footprint outline 8.13 mm square.

## NOT established

- **RF axis height above the PCB top surface.**
"""

GOOD_FACTS = {
    "device": "Widget",
    "record": "README.md",
    "facts": [
        {"id": "span", "what": "port span", "value": "35.04", "units": "mm",
         "grade": "MEASURED",
         "method": "caliper on the physical unit, outside-to-outside minus OD",
         "quote": "| **total span** | **35.04** |"},
        {"id": "outline", "what": "connector outline", "value": "8.13",
         "units": "mm", "grade": "ESTIMATED",
         "method": "extracted from the assembly plot at 600 dpi",
         "error_bar": "±1.5 % (±0.12 mm)",
         "quote": "Footprint outline 8.13 mm square."},
        {"id": "rf_axis", "what": "RF axis height above the PCB",
         "grade": "OWED",
         "how_to_obtain": "five minutes with a depth gauge on a real unit",
         "quote": "- **RF axis height above the PCB top surface.**"},
    ],
}

GOOD_MATES = {
    "device": "widget_hardware",
    "why": "this board plugs onto a Widget",
    "consumes": [
        {"fact": "span", "use": "dimensional",
         "where": "floorplan connector anchor X coordinates"},
        {"fact": "outline", "use": "dimensional",
         "where": "keep-out envelope around the mating face"},
        {"fact": "rf_axis", "use": "owed",
         "where": "board Z position — BLOCKING for the mechanical stack"},
    ],
}


# --------------------------------------------------------------- fixtures
def tree(facts=None, mates=None, record=None, brief=None, board="cal-switch"):
    """A scratch repo: external_hardware/widget_hardware/ + projects/<board>/.

    Known-bad fixtures are built by passing a MUTATED copy of GOOD_* — one
    change each, so a failure proves the checker reacts to that defect and
    not to some unrelated malformation (tests/README).
    """
    d = tmpdir("imp_")
    registry = d / "external_hardware" / "widget_hardware"
    registry.mkdir(parents=True)
    (registry / "README.md").write_text(RECORD if record is None else record)
    if facts is not False:
        (registry / "facts.yaml").write_text(
            yaml.safe_dump(GOOD_FACTS if facts is None else facts,
                           allow_unicode=True))
    rules = d / "projects" / board / "03_src" / "rules"
    rules.mkdir(parents=True)
    if mates is not False:
        text = (mates if isinstance(mates, str)
                else yaml.safe_dump(GOOD_MATES if mates is None else mates,
                                    allow_unicode=True))
        (rules / "mates.yaml").write_text(text)
    if brief is not None:
        docs = d / "projects" / board / "01_docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "BRIEF.md").write_text(brief)
    return d / "projects" / board


def deep(obj):
    return yaml.safe_load(yaml.safe_dump(obj))


def fact(facts, fid):
    return next(f for f in facts["facts"] if f["id"] == fid)


def gate(pdir, *extra):
    return run([KPY, IMPORTC, str(pdir), *extra])


# ------------------------------------------------------------------ clean
@test("import_provenance passes the real Pluto board against external facts")
def t_real_board():
    """Not a fixture: the shipped `03_src/rules/mates.yaml` graded against the
    shipped `external_hardware/plutoplus_hardware/`. This is the artifact the
    gate exists for, and it must also print a denominator (M-COVER/G-COVER)."""
    r = must_pass(gate(ROOT / "archived_projects" / "pluto-cal-switch"),
                  "import_provenance on pluto-cal-switch")
    contains(r.out, "IMPORT PROVENANCE: PASS", "verdict")
    contains(r.out, "coverage:", "coverage denominator")
    contains(r.out, "referenced facts graded", "coverage wording")
    # the two units DISAGREE by 0.32 mm, so BOTH spans must be consumed —
    # a mates.yaml naming only one of them is designing to a board that may
    # not be the one in the user's hand (D6 / ADR-0014).
    for fid in ("sma_span_genuine", "sma_span_clone"):
        contains(r.out, fid, f"{fid} graded")
    contains(r.out, "M-OWED plutoplus_hardware/rf_axis_height_above_pcb",
             "the unestablished RF-axis height is declared, not invented")


@test("import_provenance passes a clean synthetic tree (MEASURED + ESTIMATED+bar + OWED)")
def t_clean():
    r = must_pass(gate(tree()), "clean tree")
    contains(r.out, "IMPORT PROVENANCE: PASS", "verdict")
    contains(r.out, "3/3", "3 of 3 facts graded")


@test("the explicit external-hardware-root override grades the named registry")
def t_explicit_registry_root():
    pdir = tree()
    repo = pdir.parents[1]
    custom = repo / "vendor-facts"
    (repo / "external_hardware").rename(custom)
    r = must_pass(
        gate(pdir, "--external-hardware-root", str(custom)),
        "explicit external hardware root",
    )
    contains(r.out, str(custom), "reports exact authority root")


@test("a board that mates to nothing says NOTHING TO GRADE out loud")
def t_nothing_to_grade():
    """A gate that reports PASS over an empty denominator is the shape this
    whole family exists to prevent. Most boards legitimately mate to nothing
    foreign, so this is not a FAIL — but it may not read as a pass either."""
    p = tree(mates=False)
    r = must_pass(gate(p), "board with no mates.yaml")
    contains(r.out, "NOTHING TO GRADE", "the empty-denominator announcement")
    check("IMPORT PROVENANCE: PASS" not in r.out,
          "a run that graded nothing must not print PASS")


# -------------------------------------------------------------- known-bad
@test("M-BAR FAILS the PRE-CALIPER PlutoPlus span: ESTIMATED, no bar, spent on a dimension",
      kind="known_bad")
def t_pre_caliper_estimate_spent_on_a_dimension():
    """THE incident, as the record stood on the morning of 2026-07-27.

    35.60 mm off an undimensioned plot, three extractions agreeing to
    0.003 mm, +-1.5 % of scale uncertainty that lived in prose in another
    document and was never attached to the number — about to be spent against
    a +-0.05 mm SMA thread-start window. RED-VERIFIED: with M-BAR's
    ESTIMATED-and-dimensional block disabled this test fails ("SHOULD HAVE
    FAILED but exited 0")."""
    facts = deep(GOOD_FACTS)
    f = fact(facts, "outline")
    f.update(id="span_from_plot", value="35.60", what="port span from the plot",
             method="extracted from the vendor's undimensioned assembly plot",
             quote="Extracted from the vendor's undimensioned assembly plot: "
                   "span **35.60** mm.")
    del f["error_bar"]                       # the ONE break: the bar is gone
    mates = deep(GOOD_MATES)
    mates["consumes"][1] = {"fact": "span_from_plot", "use": "dimensional",
                            "where": "the three connector anchor X coords"}
    r = must_fail(gate(tree(facts=facts, mates=mates)),
                  "M-BAR on the pre-caliper span", "M-BAR")
    contains(r.out, "span_from_plot", "names the offending fact")
    contains(r.out, "no error bar", "says what is missing")


@test("M-PROXY FAILS the same number graded MEASURED — precision about a proxy",
      kind="known_bad")
def t_pre_caliper_graded_as_measured():
    """The other half of the same morning: the plot number was so reproducible
    (0.003 mm across three extractions) that it read as measured. It was not.
    Three extractions measure the PLOT precisely; the object was 0.56 mm away.
    RED-VERIFIED: with M-PROXY's block disabled this test fails."""
    facts = deep(GOOD_FACTS)
    f = fact(facts, "outline")
    f.update(id="span_from_plot", value="35.60",
             grade="MEASURED",              # the ONE break: the grade lies
             method="extracted from the vendor's undimensioned assembly plot, "
                    "three independent extractions agreeing to 0.003 mm",
             quote="Extracted from the vendor's undimensioned assembly plot: "
                   "span **35.60** mm.")
    mates = deep(GOOD_MATES)
    mates["consumes"][1] = {"fact": "span_from_plot", "use": "dimensional",
                            "where": "the three connector anchor X coords"}
    r = must_fail(gate(tree(facts=facts, mates=mates)),
                  "M-PROXY on a plot number graded MEASURED", "M-PROXY")
    contains(r.out, "extracted from", "names the proxy word it found")


@test("M-BAR FAILS an error bar that does not PARSE", kind="known_bad")
def t_unreadable_bar():
    """"about a percent" satisfies a presence check and measures nothing.
    Input a gate cannot understand is a FAIL, never a skip (M-COVER)."""
    facts = deep(GOOD_FACTS)
    fact(facts, "outline")["error_bar"] = "small, probably"
    r = must_fail(gate(tree(facts=facts)), "M-BAR on an unparseable bar",
                  "M-BAR")
    contains(r.out, "does not parse", "says the bar is unreadable")


@test("M-GRADE FAILS a referenced fact with no grade", kind="known_bad")
def t_no_grade():
    facts = deep(GOOD_FACTS)
    del fact(facts, "span")["grade"]
    must_fail(gate(tree(facts=facts)), "M-GRADE on an ungraded fact", "M-GRADE")


@test("M-GRADE FAILS a grade outside the closed vocabulary", kind="known_bad")
def t_bogus_grade():
    facts = deep(GOOD_FACTS)
    fact(facts, "span")["grade"] = "PRETTY_SURE"
    must_fail(gate(tree(facts=facts)), "M-GRADE on an invented grade", "M-GRADE")


@test("M-EXIST FAILS a fact the device record does not hold", kind="known_bad")
def t_unknown_fact():
    mates = deep(GOOD_MATES)
    mates["consumes"][0]["fact"] = "span_of_something_else"
    r = must_fail(gate(tree(mates=mates)), "M-EXIST on an unknown id", "M-EXIST")
    contains(r.out, "span_of_something_else", "names the missing id")


@test("M-EXIST FAILS when facts.yaml has DRIFTED from the record it indexes",
      kind="known_bad")
def t_index_drift():
    """The single-home rule has a failure mode: the index and the record are
    two files, so they can disagree. The `quote:` must appear in the record
    VERBATIM with the value inside it — cooksense v1.1 shipped 13 CPL rows
    contradicting its own MANIFEST for exactly this reason."""
    facts = deep(GOOD_FACTS)
    f = fact(facts, "span")
    f["value"] = "35.60"                     # the index moved; the record did not
    f["quote"] = "| **total span** | **35.60** |"
    r = must_fail(gate(tree(facts=facts)), "M-EXIST on index drift", "M-EXIST")
    contains(r.out, "VERBATIM", "explains what drifted")


@test("M-EXIST FAILS a device folder that does not exist", kind="known_bad")
def t_no_device():
    mates = deep(GOOD_MATES)
    mates["device"] = "widget_hardware_v2"
    must_fail(gate(tree(mates=mates)), "M-EXIST on a missing device folder",
              "M-EXIST")


@test("M-EXIST rejects the retired spf path as authority", kind="known_bad")
def t_retired_spf_root():
    """The default must not silently fall back to the ambiguous old name."""
    pdir = tree()
    repo = pdir.parents[1]
    registry = repo / "external_hardware"
    retired = repo / "spf"
    registry.rename(retired)
    r = must_fail(gate(pdir), "M-EXIST with only retired spf tree", "M-EXIST")
    contains(r.out, "external_hardware/widget_hardware",
             "names forward authority")


@test("M-EXIST FAILS a mates.yaml that does not parse", kind="known_bad")
def t_unparseable_mates():
    must_fail(gate(tree(mates="device: widget_hardware\nconsumes: [{{{")),
              "M-EXIST on unparseable yaml", "M-EXIST")


@test("M-OWED FAILS a fact NOBODY HAS being spent on a dimension", kind="known_bad")
def t_owed_spent():
    """The PlutoPlus RF-axis height, consumed as if someone had measured it.
    It sets the daughter board's entire Z relationship and its geometric
    bound is only '>=3.2 mm, family typical 4.5-6 mm'."""
    mates = deep(GOOD_MATES)
    mates["consumes"][2]["use"] = "dimensional"
    r = must_fail(gate(tree(mates=mates)), "M-OWED on an owed dimension",
                  "M-OWED")
    contains(r.out, "nobody has this number", "says why it cannot be spent")


@test("M-OWED FAILS an OWED fact with no route to obtaining it", kind="known_bad")
def t_owed_without_route():
    facts = deep(GOOD_FACTS)
    del fact(facts, "rf_axis")["how_to_obtain"]
    must_fail(gate(tree(facts=facts)), "M-OWED with no how_to_obtain", "M-OWED")


@test("M-RESTATE FAILS a board that restates the VALUE instead of referencing it",
      kind="known_bad")
def t_restate():
    """Boards reference; they never restate. The moment the number lives in
    two files it can drift in one of them, and the gate that reads the other
    goes on passing."""
    mates = deep(GOOD_MATES)
    mates["consumes"][0]["value"] = "35.04"
    r = must_fail(gate(tree(mates=mates)), "M-RESTATE on a restated value",
                  "M-RESTATE")
    contains(r.out, "['value']", "names the restated key")


@test("D-MATE FAILS a consumed fact that never says WHERE it is spent",
      kind="known_bad")
def t_no_where():
    mates = deep(GOOD_MATES)
    del mates["consumes"][0]["where"]
    must_fail(gate(tree(mates=mates)), "D-MATE on a siteless consumption",
              "D-MATE")


@test("D-MATE FAILS a BRIEF declaring a Mating fact-lock with no mates.yaml",
      kind="known_bad")
def t_brief_without_yaml():
    """The user-facing lock without its machine copy: the table says MEASURED
    and nothing on earth checks that it is."""
    brief = ("# BRIEF\n\n## Mating fact-lock\n\n| Fact | Grade |\n|---|---|\n"
             "| port span | MEASURED |\n\n## Log\n")
    r = must_fail(gate(tree(mates=False, brief=brief)),
                  "D-MATE on a BRIEF with no mates.yaml", "D-MATE")
    contains(r.out, "no machine copy", "explains the gap")


@test("a BRIEF that says it does not mate is NOT a D-MATE failure")
def t_brief_declines():
    """The escape hatch must work, or the gate becomes noise on every board
    that mates to nothing — and a gate people learn to ignore is worse than
    no gate."""
    brief = ("# BRIEF\n\n## Mating fact-lock\n\nnone — this board does not "
             "mate to hardware this repo did not design.\n\n## Log\n")
    r = must_pass(gate(tree(mates=False, brief=brief)),
                  "BRIEF declining to mate")
    contains(r.out, "NOTHING TO GRADE", "still says it graded nothing")


@test("M-COVER FAILS a mates.yaml that consumes NOTHING", kind="known_bad")
def t_empty_consumes():
    """A zero denominator is a FAIL. A mates.yaml with an empty `consumes:`
    reads as governance and grades nothing."""
    mates = deep(GOOD_MATES)
    mates["consumes"] = []
    must_fail(gate(tree(mates=mates)), "M-COVER on an empty consumes list",
              "M-COVER")


@test("the gate obeys its own contract (G-INPUT / G-COVER / G-RED)")
def t_gate_contract():
    """canon G-*, ADR-0004: the checkers are themselves governed. Run the
    gate-on-gates scoped to this script rather than trusting that it looks
    right."""
    r = run([KPY, SCRIPTS / "gate_contract_audit.py", "--root", str(ROOT)])
    for bad in ("G-COVER skills/kicad-pcb/scripts/import_provenance_check.py",
                "G-INPUT skills/kicad-pcb/scripts/import_provenance_check.py",
                "G-RED skills/kicad-pcb/scripts/import_provenance_check.py"):
        check(bad not in r.out, f"gate_contract_audit reports {bad}\n{r.out}")


if __name__ == "__main__":
    sys.exit(main())
