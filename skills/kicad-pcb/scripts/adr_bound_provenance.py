#!/usr/bin/env python3
"""adr_bound_provenance — an ADR's PUBLISHED BOUND is REGENERATED, not typed.

    python3 adr_bound_provenance.py ROOT [--adr NAME] [--no-regen]
                                    [--timeout 180] [--strict-owed]

THE INCIDENT (2026-07-29, smc0985-cooksense ADR-0024, "every pod-mateable
safety input is hardened AT THE PINOUT"). The ADR published

    General bound: V <= 0.700 V  =>  R_pd <= 592 Ohm

as the ONE-LINE TAKEAWAY of a document whose entire argument is worst-case, one
row below a table that correctly quotes the rail ceiling 3.399 V. **592 Ohm is
the NOMINAL corner** — 3.300 V, 2200 Ohm exactly, R_pd at +/-0 %. At the corner
the rest of the section uses (rail 3.399 V, injected pull-up 2178 Ohm = 2.2k
-1 %, R_pd +1 %) the bound is **559.3 Ohm**.

The 33 Ohm was not a rounding note. **560 Ohm is the only E24 value under 592,
it is the value a future pass reaches for under that ceiling, and at the
worst-case corner it produces 0.7007 V and FAILS by 0.7 mV.** The published
bound permitted exactly one standard value and that value does not clear. The
chosen 470 Ohm is unaffected (+91.7 mV), so the board was never wrong — the ADR
was. THE FAILURE IS THE ONE THE ADR IS NAMED AFTER, REPRODUCED IN ITS OWN
SUMMARY LINE: a remedy quoted at a corner the decision does not use.

AND IT IS NOT ONE DOCUMENT — canon M-WIDTH says name the CLASS and enumerate its
known members, so here they are, all found by re-deriving 108 published bounds
across 37 ADRs on 2026-07-29:

  1. cooksense ADR-0024, `R_pd <= 592 Ohm` — above. Corrected in the body since;
     the CLASS is what this gate closes.
  2. **cooksense ADR-0018 line 213, `V <= 1.0 V => R >= 1 564 Ohm`, AND IT IS
     STILL PUBLISHED.** In a section whose heading reads, verbatim, "WORST CASE,
     INJECTED PULL-UP — must stay under `V_GS(th)` MIN = 1.0 V", the table's own
     column header is `3.3 · 680/(680+R)`. 3.3 V is the NOMINAL rail; the board's
     `power_tree.yaml` declares 3V3 `vout_max: 3.399`, and the ADR itself takes
     the rail "at its LOW end, 3.201 V" forty lines earlier for the opposite
     direction *because a low rail is the worst case for clearing a threshold*.
     At 3.399 V the bound is **1 631.3 Ohm** (1 647.6 with R_COILENPD +1 %), so
     the published bound admits E24 **1.60 k** (1.0137 V), E96 **1.58 k**
     (1.0227 V) and E96 **1.62 k** (1.0049 V) — and NOT ONE OF THEM CLEARS. Same
     shape, same board, same week, in the ADR that ADR-0024 EXTENDS. The safety
     claim survives (every tabulated pod pull-up still clears at 3.399 V), so
     this is a wrong published bound rather than a wrong board — which is exactly
     why nothing that reads copper could find it.
  3. usb-hub-3s-v3 ADR-0003, `PASS <= 300 uA` — the board's own
     `power_tree.yaml` retired it in writing ("**PASS <= 1.00 mA**, re-derived
     2026-07-27. The old `<= 300 uA` WOULD HAVE FAILED A GOOD BOARD"), because
     two LM5116 UVLO dividers were missing from the budget. The ADR was never
     amended. A gate that cannot PASS, published as a bound.
  4. crow-recorder-central-v2 ADR-0007, a v-next `F_BEEP` PTC at `~1.1 A hold`
     naming MINISMDC110F. Six pods fire together off one shared driver = 0.900 A,
     and this repo's own derating (ADR-0002's 6 A -> 4.8 A at 50 C, x0.8) puts the
     named part at 0.880 A. **The bound names one purchasable part and that part
     nuisance-trips.** cooksense's 560 Ohm with a different unit.

Same class, same day, different artifact: a hand-derived silk-stroke threshold
entered two canon files and was wrong TWICE — 0.9375 mm is the board-silk figure
and 0.75 mm the refdes figure, because "the generator" was two generators all
along. **A RULE ABOUT A QUANTITY MUST NAME ITS EMITTER AND ITS CORNER.**

So this gate is the ADR analogue of canon M4's `evidence:` schema on
`policy_waivers.yaml` (`waiver_provenance.py`): a load-bearing number stops
being a digit and becomes A COMMAND AND ITS OUTPUT, re-run and diffed. The
vocabulary, the ladder and the monotone ratchet are REUSED VERBATIM from that
gate — deliberately not a second dialect — and the read-only denylist and
number parsers are IMPORTED from it rather than copied.


================================================================================
THE SCHEMA
================================================================================

An ADR declares one block per published inequality: a line reading exactly
`<!-- bound -->` (or `<!-- bound: ID -->`), immediately followed by a fenced
```yaml block. Anything else in the ADR is prose and is read by nothing.

    <!-- bound: R_PD_MAX -->
    ```yaml
    id: R_PD_MAX
    claim: >-
      Largest safety pull-down that keeps V(DOOR_RAW) under V_T-(min) 0.700 V
      with a cross-mated pod's 2.2k SCL pull-up injected.
    relation: "<="
    value: 559.3               # THE PUBLISHED BOUND. The typed number.
    unit: Ohm
    corner: worst_case         # nominal | worst_case | typical
    command: /usr/bin/python3 .../divider.py --solve --corner worst_case
    governs:                   # WHAT the bound is a bound ON
      evaluate: /usr/bin/python3 .../divider.py --corner worst_case --r {value}
      budget: "<= 0.700"
      unit: V
    standard_value:
      series: E24              # DECLARED PER BOUND. There is no global default.
      series_why: >-
        A 1 %-tolerance safety pull-down off this board's own E24 strip; the
        board stocks no E96 resistors.
    chosen: 470                # the value the decision actually uses
    tolerance: 0.1
    tolerance_why: >-
      ...
    grade: CITED
    ```

`command` is re-run from the REPO ROOT and its last stdout line must carry
exactly one number, which is diffed against `value`. `governs.evaluate` carries
a `{value}` placeholder and is run TWICE MORE, and those two runs are the whole
insight of this gate:

  1. **AT THE PUBLISHED BOUND ITSELF.** A bound sits on its own budget edge at
     the corner it was derived at, and nowhere else. Evaluating 559.3 Ohm at
     `worst_case` gives 0.699967 V against `<= 0.700`; evaluating **592.3 Ohm**
     at `worst_case` gives **0.732420 V** and violates it by 32.4 mV. That
     single run reproduces the ADR-0024 incident FROM THE DOCUMENT ALONE, with
     no second opinion and no sibling corner needed: a bound whose own value is
     inadmissible under its own budget WAS NOT DERIVED AT THE CORNER IT
     DECLARES.
     THE BOUND IS NUDGED INWARD BY ITS OWN DECLARED `tolerance` FIRST, and that
     is not a softening — it is the only way a ROUNDED bound can be graded at
     all. The exact worst-case solution is 559.2830 Ohm and the ADR publishes
     559.3, which at 559.3 evaluates to 0.700017 V: strictly over, by 17 uV of
     rounding. So the value tested is `559.3 - tolerance`, and a bound that
     rounds must therefore DECLARE the tolerance it rounded by — which B-TOL
     then keeps honest. 592.3 - 0.05 still gives 0.732371 V and still fires.
  2. **AT THE NEAREST STANDARD VALUE.** A bound is not a number, it is a number
     PLUS THE SET OF PARTS YOU CAN ACTUALLY BUY. The nearest series value
     admissible under the bound — the largest for `<=`/`<`, the smallest for
     `>=`/`>` — is re-evaluated at the declared corner, and a bound whose only
     admissible standard value FAILS THERE is a FAIL, not a rounding note.
     560 Ohm under a 592 Ohm ceiling at worst_case: 0.7007 V. Fails by 0.7 mV.

WHY THE SERIES IS DECLARED PER BOUND AND NEVER ASSUMED. Which E-series applies
is a SOURCING fact, not an arithmetic one, and the answer changes the verdict:
under 592.3 Ohm, E24 admits 560 and E96 admits 590 — both fail here, but a
`decade`/`explicit` set naming only what the board stocks may admit 470 and
pass. A safety pull-down and a decoupling cap are not sourced from the same
series, so a global default would be a single number standing in for two
different supply chains: exactly the "the generator was two generators" defect
above, one level up. `series:` and `series_why:` are both mandatory, and
`explicit: [...]` is the honest spelling of "the board's own preferred set".

CHECKS
  B-SCHEMA   the block is not a mapping, carries an unknown key (a misspelled
             `commmand:` must not degrade silently back into prose), omits a
             required key, declares a `corner:` outside
             {nominal, worst_case, typical}, or `value:` does not carry exactly
             one number. A bound with no `governs:` is prose with a colon in it.
  B-GRADE    `grade:` is not CITED / ESTIMATED; a CITED bound carries no
             `command` (a citation claim with nothing cited); an ESTIMATED bound
             carries no `why_not_rerunnable:`.
  B-CMD      a declared command is not READ-ONLY. This gate EXECUTES what the
             ADR says, and an audit that can write is not an audit. The denylist
             is `waiver_provenance.MUTATING`, imported rather than copied.
  B-REGEN    `command` ran, printed a number, and it DISAGREES with the
             published `value:` by more than `tolerance`.
  B-CORNER   `governs.evaluate` at the PUBLISHED VALUE (nudged inward by the
             declared `tolerance`) violates `governs.budget` — the bound does not
             sit on its own edge at the corner it declares, so it was derived at
             a DIFFERENT corner. This is the ADR-0024
             defect and it FAILS ON THAT ALONE, whether or not any standard
             value clears and whether or not `command` was runnable. When
             `corner_commands:` names sibling corners, the finding also says
             WHICH corner the published number does reproduce at.
  B-STDVAL   the nearest standard value admissible under the bound, re-evaluated
             at the declared corner, VIOLATES the bound's own budget. The bound
             permitted a value that cannot be bought and made to work.
  B-SERIES   a `standard_value:` block with no `series`, an unshort
             `series_why`, an unknown series name, or a `decade`/`explicit` set
             that is empty. An assumed series is a verdict nobody chose.
  B-FLIP     the value the ADR says it CHOSE satisfies the published bound and
             does NOT satisfy the regenerated one (or the reverse). THE
             DECISION'S OWN CONCLUSION REVERSES. Reported separately from
             B-REGEN — 592.3 against 559.3 is not a 33 Ohm discrepancy when the
             chosen part sits between them, it is a reversed verdict — and NO
             TOLERANCE EXCUSES IT. (cooksense chose 470 Ohm, which clears both,
             which is exactly why that board is fine and the ADR was not.)
  B-TOL      `tolerance` present without `tolerance_why`, or a tolerance >= the
             MARGIN the bound must discriminate: the smallest distance from the
             published value to a value the bound has to rule on — `chosen` and
             the nearest standard value. 559.3 Ohm with 510 Ohm as the nearest
             E24 value has 49.3 Ohm to work with, so a 50 Ohm tolerance cannot
             distinguish pass from fail and is not a tolerance. THIS IS THE
             CHECK THAT STOPS THE FIX FROM RECREATING THE DEFECT IT CLOSES: the
             tolerance is itself a load-bearing number.

THE LADDER, verbatim from canon M-IMPORT via `waiver_provenance` — for a number
that cannot be regenerated HERE AND NOW:

  CITED      command ran, printed one number, agrees within tolerance.
  UNVERIFIED a command exists but produced no number here — a declared
             `requires:` absent, a timeout, or a non-zero exit. Named on every
             run, credited to nobody, and deliberately NOT A FAIL: one board is
             mid-rebuild and two are mid-route as this lands, and a gate whose
             verdict turns on whether a sibling agent is regenerating copper is
             a gate that gets switched off inside a week. The hole that opens is
             closed FROM THE OTHER SIDE by `CITED_FLOOR`, so a citation that
             stops reproducing fails.
  ESTIMATED  no command is possible; `why_not_rerunnable:` says why. Legal,
             reported, never counted as CITED.
  OWED       an ADR that publishes a numeric inequality bound and declares no
             `bound:` block at all — 37 of 78 ADRs on the day this landed.
             Named document by document, counted, ceiling-pinned.

THE RATCHET. 37 ADRs carry a bound and 0 declare anything, so a day-one mandate
lands as 37 red documents and gets switched off. Coverage is REPORTED, every
OWED document is printed BY NAME, and only two COUNTING facts can fail — CITED
dropping below `CITED_FLOOR` and OWED rising above `OWED_CEILING`. Everything
else that fails is a number that DISAGREED, a corner that was MISLABELLED, or a
standard value that is INADMISSIBLE. The direction is what makes it monotone:
the existing 37 are a named debt, and the next ADR that publishes a bound must
either declare it or raise the ceiling in the same commit, naming the run.

THE BLIND SPOT THIS LEAVES OPEN, stated exactly (canon G-VACUOUS; declared as
prose rather than as a `VACUITY:` block ON PURPOSE — binding one requires
raising `gate_contract_audit.VACUITY_FLOOR` from 5 to 6, and that file is owned
elsewhere in this session. The one-line patch and its fixture are in the
accompanying report, and this gate is OWED under G-VACUOUS until then. Its
executable half already exists as
`t1_adr_bounds.py:t_blindspot_a_bound_typed_only_in_prose_is_read_by_nothing`,
subject-then-contrast.)

  1. EVERY CHECK HERE GRADES ONLY WHAT A BLOCK DECLARES. A bound typed in ADR
     prose is read by nothing, and on the day this landed that was **37 of 37
     documents, 108 inequality bounds, 0 CITED** — the incident bound itself
     included, in its original form. That is why OWED is enumerated by name on
     every run rather than left as a silent zero.
  2. B-CORNER CATCHES A MISLABELLED CORNER, NOT A BADLY CHOSEN ONE. An ADR that
     declares `corner: nominal` and does its arithmetic at nominal is internally
     consistent and PASSES, even when the document's whole argument is
     worst-case — which is the ADR-0024 incident with the label told honestly.
     The gate can prove a bound was derived somewhere other than where it says;
     it cannot prove that where it says is the right place. THE CONTRAST, and
     what makes this a blind spot rather than a fact the gate cannot represent:
     the same 592.3 Ohm bound labelled `worst_case` is caught by name, twice
     (B-CORNER on its own edge, B-STDVAL on 560 Ohm).
  3. `governs.evaluate` IS THE ADR AUTHOR'S ARITHMETIC, not this gate's. That
     separation is canon M1 on purpose — the gate owns the LADDER, the SERIES
     and the RELATION, and never the physics — and the price is that an
     `evaluate` command wrong in the same direction as the bound agrees with it.
     A second opinion on the physics is `electrical_invariants.yaml`'s job
     (ADR-0007 node_level), not this gate's.

FLEET DENOMINATOR, measured by this script on 2026-07-29 at main tip: **78 ADRs
(7 repo-level + 71 across 6 live boards); 37 carry at least one numeric
inequality bound** (`<=`, `>=`, the unicode `<=`/`>=`, followed by a number),
**108 such bounds in total**, densest smc0985-cooksense ADR-0023 at 10, and
**0 declare a `bound:` block**. A bare `<` or `>` is deliberately NOT counted:
it collides with markdown/HTML and with prose arrows, and over-counting the
denominator would inflate the debt rather than describe it.

Exit 0 when clean, 1 on any finding.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import yaml
except ImportError:
    sys.exit("adr_bound_provenance needs pyyaml")

# REUSED, NOT REDEFINED. The read-only denylist, the "exactly one number" rule,
# the last-stdout-line rule and the relation parser are canon M4's, and a second
# copy of them would be a second dialect drifting from the first.
from waiver_provenance import (MUTATING, last_line_number,  # noqa: E402
                              one_number, relation, satisfies)

# ---------------------------------------------------------------- the ratchet
# MEASURED by this script on the live tree at main tip, 2026-07-29. Each is
# MONOTONE IN THE DIRECTION THAT MATTERS, so the existing debt is a named list
# and the NEXT one is a hard fail:
#   CITED may only RISE, OWED may only FALL.
# Edit one of these only in the same commit that earns it, and say which run
# produced the number.
CITED_FLOOR = 13       # regenerated and agreeing blocks, MEASURED 2026-08-12
                       # after USB Hub v4 made its exact cable-resistance bound
                       # executable instead of increasing OWED. May only rise.
OWED_CEILING = 37      # ADRs that publish a numeric inequality bound and
                       # declare no `bound:` block. Still TIGHT at 37 of 48
                       # bound-publishing ADRs across 105 total ADRs after the
                       # new v4 bound gained its block. Never loosened to 38.

ADR_GLOBS = ("docs/decisions/[0-9]*.md", "*/01_docs/decisions/[0-9]*.md",
             "projects/*/01_docs/decisions/[0-9]*.md")
EXCLUDE_PARTS = ("archived_projects", ".claude", "node_modules", "07_releases",
                 "06_build")

BOUND_KEYS = {"id", "claim", "relation", "value", "unit", "corner", "command",
              "corner_commands", "governs", "standard_value", "chosen",
              "chosen_why", "tolerance", "tolerance_why", "grade", "requires",
              "why_not_rerunnable", "note"}
REQUIRED_KEYS = ("id", "claim", "relation", "value", "corner", "governs")
GOVERNS_KEYS = {"evaluate", "budget", "unit", "note"}
STDVAL_KEYS = {"series", "series_why", "explicit", "note"}
CORNERS = ("nominal", "worst_case", "typical")
GRADES = ("CITED", "ESTIMATED")

# IEC 60063 preferred numbers, one decade each. The gate owns THESE and not the
# physics: which series a bound is sourced from is the author's declaration,
# what the series CONTAINS is a published standard.
E_SERIES = {
    "E3": (10, 22, 47),
    "E6": (10, 15, 22, 33, 47, 68),
    "E12": (10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82),
    "E24": (10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43,
            47, 51, 56, 62, 68, 75, 82, 91),
    "E48": (100, 105, 110, 115, 121, 127, 133, 140, 147, 154, 162, 169, 178,
            187, 196, 205, 215, 226, 237, 249, 261, 274, 287, 301, 316, 332,
            348, 365, 383, 402, 422, 442, 464, 487, 511, 536, 562, 590, 619,
            649, 681, 715, 750, 787, 825, 866, 909, 953),
    "E96": (100, 102, 105, 107, 110, 113, 115, 118, 121, 124, 127, 130, 133,
            137, 140, 143, 147, 150, 154, 158, 162, 165, 169, 174, 178, 182,
            187, 191, 196, 200, 205, 210, 215, 221, 226, 232, 237, 243, 249,
            255, 261, 267, 274, 280, 287, 294, 301, 309, 316, 324, 332, 340,
            348, 357, 365, 374, 383, 392, 402, 412, 422, 432, 442, 453, 464,
            475, 487, 499, 511, 523, 536, 549, 562, 576, 590, 604, 619, 634,
            649, 665, 681, 698, 715, 732, 750, 768, 787, 806, 825, 845, 866,
            887, 909, 931, 953, 976),
}

#: THE DENOMINATOR. A published inequality bound: `<=`, `>=`, or their unicode
#: forms, followed by a number. A bare `<`/`>` is excluded on purpose — see the
#: docstring's denominator note.
BOUND_IN_PROSE = re.compile(r"(<=|>=|≤|≥)\s*\d")

#: `<!-- bound -->` / `<!-- bound: ID -->` then a fenced yaml block. ONE form,
#: because two spellings of a declaration is how a schema drifts.
DECL = re.compile(
    r"^[ \t]*<!--[ \t]*bound(?:[ \t]*:[ \t]*(?P<id>[^\->]+?))?[ \t]*-->[ \t]*\r?\n"
    r"[ \t]*```[ \t]*ya?ml[ \t]*\r?\n"
    r"(?P<body>.*?)"
    r"^[ \t]*```[ \t]*$",
    re.M | re.S)


def series_values(spec, why=None):
    """-> (sorted values, error). `spec` is a series name or an explicit list.

    E-series values are expanded across decades 1e-3 .. 1e9 of the base set, so
    a bound in Ohm, mm, or Farad all resolve without the gate knowing the unit.
    """
    if isinstance(spec, (list, tuple)):
        vals = []
        for v in spec:
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                return None, f"explicit series member {v!r} is not a number"
        if not vals:
            return None, "explicit series is empty"
        return sorted(vals), None
    name = str(spec or "").strip().upper()
    if name not in E_SERIES:
        return None, (f"unknown series {name!r} — known: "
                      f"{sorted(E_SERIES)} or an explicit list")
    base = E_SERIES[name]
    scale = 10.0 ** (-len(str(base[0])) + 1)      # 10 -> 1.0, 100 -> 1.0
    out = []
    for d in range(-3, 10):
        for b in base:
            out.append(round(b * scale * (10.0 ** d), 12))
    return sorted(out), None


def nearest_admissible(values, rel, limit):
    """The standard value a future pass reaches for under this bound.

    `<=`/`<` -> the LARGEST series value that satisfies it (the one nearest the
    ceiling, i.e. the cheapest/most permissive choice somebody will make);
    `>=`/`>` -> the SMALLEST. `==` admits only an exact hit. None when the
    series admits nothing at all, which is itself worth saying out loud.
    """
    ok = [v for v in values if satisfies(v, rel, limit)]
    if not ok:
        return None
    return max(ok) if rel in ("<=", "<") else min(ok)


def inward(value, rel, tol):
    """The published bound nudged INTO its own admissible side by `tol`.

    A published bound is rounded — cooksense ADR-0024's exact worst-case
    solution is 559.2830 Ohm and the document publishes 559.3, which is
    strictly inadmissible by 17 uV. Testing the printed digits would make every
    rounded bound a B-CORNER finding, which is the adjacent-property error this
    repo keeps paying for. Testing `value -/+ tolerance` instead grades the
    bound AT THE PRECISION IT CLAIMS, and it costs nothing: a bound with no
    declared tolerance is graded strictly (tol defaults to 1e-9), so rounding
    forces an author to DECLARE what they rounded by, and B-TOL then refuses a
    tolerance wide enough to swallow the margin.
    """
    if rel in ("<=", "<"):
        return value - tol
    if rel in (">=", ">"):
        return value + tol
    return value


def find_adrs(root, include_archived=False):
    """-> sorted list of ADR paths under `root`.

    G-INPUT: the caller sees exactly which documents were in scope, because a
    fleet-wide coverage number is only meaningful next to its universe.
    """
    root = Path(root)
    hits = set()
    for g in ADR_GLOBS:
        for p in root.glob(g):
            if p.is_file():
                hits.add(p.resolve())
    for p in root.glob("*/*/01_docs/decisions/[0-9]*.md"):
        if p.is_file():
            hits.add(p.resolve())
    keep = []
    for p in sorted(hits):
        parts = set(p.parts)
        if not include_archived and (parts & set(EXCLUDE_PARTS)):
            continue
        keep.append(p)
    return keep


def parse_blocks(text, where):
    """-> (blocks, fails). Each block is the parsed mapping plus its marker id."""
    blocks, fails = [], []
    for m in DECL.finditer(text):
        marker = (m.group("id") or "").strip()
        try:
            data = yaml.safe_load(m.group("body"))
        except yaml.YAMLError as e:
            fails.append(f"B-SCHEMA {where}: a `<!-- bound -->` block is not "
                         f"parseable YAML ({e}) — a declaration that does not "
                         f"load is worse than none, it reads as diligence")
            continue
        if not isinstance(data, dict):
            fails.append(f"B-SCHEMA {where}: a `<!-- bound -->` block is a "
                         f"{type(data).__name__}, not a mapping")
            continue
        data = dict(data)
        data["_marker"] = marker
        blocks.append(data)
    return blocks, fails


def _runner(repo_root, timeout):
    def go(cmd):
        """-> (number, detail). number is None when nothing could be measured."""
        bad = [t for t in MUTATING if t in cmd]
        if bad:
            return None, f"refused: not read-only ({bad!r})"
        try:
            r = subprocess.run(cmd, shell=True, cwd=str(repo_root),
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, f"timeout after {timeout}s"
        except OSError as e:
            return None, f"could not launch: {e}"
        if r.returncode != 0:
            return None, (f"exit {r.returncode}: "
                          f"{(r.stderr or r.stdout).strip()[-160:]}")
        got, line = last_line_number(r.stdout)
        if got is None:
            return None, (f"last stdout line {line[:80]!r} does not carry "
                          f"exactly one number")
        return got, f"printed {got}"
    return go


def grade_bound(b, repo_root, where, regen=True, timeout=180):
    """-> (fails, grade, notes) for one declared bound block.

    The LADDER lives here: a command that cannot produce a number HERE is
    UNVERIFIED and reported, never a fail — see the module docstring for why
    that is not a softening. B-CORNER and B-STDVAL are the two checks that
    reproduce the incident, and B-CORNER does not need `command` to have run.
    """
    fails, notes = [], []
    bid = str(b.get("id") or b.get("_marker") or "?")
    tag = f"{where} [{bid}]"

    unknown = sorted(set(b) - BOUND_KEYS - {"_marker"})
    if unknown:
        fails.append(f"B-SCHEMA {tag}: unknown key(s) {unknown} — a misspelled "
                     f"`command:` must not degrade silently back into prose "
                     f"(known keys: {sorted(BOUND_KEYS)})")
    missing = [k for k in REQUIRED_KEYS if b.get(k) is None]
    if missing:
        fails.append(f"B-SCHEMA {tag}: missing required key(s) {missing} — a "
                     f"bound with no `governs:` is prose with a colon in it")
    if len(str(b.get("claim") or "").strip()) < 10:
        fails.append(f"B-SCHEMA {tag}: `claim:` must say WHAT is bounded")

    corner = str(b.get("corner") or "").strip()
    if corner not in CORNERS:
        fails.append(f"B-SCHEMA {tag}: corner {corner!r} is not one of "
                     f"{list(CORNERS)} — an unnamed corner is the whole "
                     f"defect class this gate exists for")

    value = one_number(b.get("value")) if b.get("value") is not None else None
    if b.get("value") is not None and value is None:
        fails.append(f"B-SCHEMA {tag}: `value:` {str(b['value'])[:40]!r} does "
                     f"not carry exactly one number — a published bound with "
                     f"two numbers in it is prose")
    rel = str(b.get("relation") or "").strip()
    if rel not in ("<=", "<", ">=", ">", "=="):
        fails.append(f"B-SCHEMA {tag}: `relation:` {rel!r} must be one of "
                     f"<= < >= > ==")
        rel = None

    gov = b.get("governs")
    ev_cmd, budget = "", None
    if gov is not None:
        if not isinstance(gov, dict):
            fails.append(f"B-SCHEMA {tag}: `governs:` must be a mapping")
            gov = {}
        else:
            gu = sorted(set(gov) - GOVERNS_KEYS)
            if gu:
                fails.append(f"B-SCHEMA {tag}: unknown `governs:` key(s) {gu}")
        ev_cmd = str(gov.get("evaluate") or "").strip()
        if gov.get("budget") is None:
            fails.append(f"B-SCHEMA {tag}: `governs.budget:` is required — the "
                         f"bound must name the limit it was solved against")
        else:
            budget = relation(gov["budget"])
            if budget is None:
                fails.append(f"B-SCHEMA {tag}: `governs.budget:` "
                             f"{str(gov['budget'])[:40]!r} must read like "
                             f"'<= 0.700'")
        if ev_cmd and "{value}" not in ev_cmd:
            fails.append(f"B-SCHEMA {tag}: `governs.evaluate:` carries no "
                         f"`{{value}}` placeholder, so it cannot be re-run at "
                         f"the standard value — which is the check this schema "
                         f"exists for")
            ev_cmd = ""

    # ---- B-SERIES: the sourcing declaration. Never assumed, per bound.
    sv = b.get("standard_value")
    svals, snote = None, None
    if sv is not None:
        if not isinstance(sv, dict):
            fails.append(f"B-SCHEMA {tag}: `standard_value:` must be a mapping")
            sv = {}
        else:
            su = sorted(set(sv) - STDVAL_KEYS)
            if su:
                fails.append(f"B-SCHEMA {tag}: unknown `standard_value:` "
                             f"key(s) {su}")
        spec = sv.get("explicit") if sv.get("explicit") is not None \
            else sv.get("series")
        if spec is None:
            fails.append(
                f"B-SERIES {tag}: `standard_value:` names no `series:` and no "
                f"`explicit:` set. A safety pull-down and a decoupling cap are "
                f"not sourced from the same series, so an ASSUMED series is a "
                f"verdict nobody chose")
        else:
            svals, err = series_values(spec)
            if err:
                fails.append(f"B-SERIES {tag}: {err}")
        if len(str(sv.get("series_why") or "").strip()) < 20:
            fails.append(
                f"B-SERIES {tag}: `series_why:` must say WHY this series is the "
                f"one this quantity is sourced from — the series choice changes "
                f"the verdict (E24 admits 560 under a 592 Ohm ceiling; a "
                f"stocked-set declaration may admit only 470)")
        if svals is not None:
            snote = f"series {spec if isinstance(spec, str) else 'explicit'}"

    chosen = one_number(b.get("chosen")) if b.get("chosen") is not None else None
    if b.get("chosen") is not None and chosen is None:
        fails.append(f"B-SCHEMA {tag}: `chosen:` does not carry exactly one "
                     f"number")

    std = None
    if svals is not None and rel and value is not None:
        std = nearest_admissible(svals, rel, value)
        if std is None:
            fails.append(
                f"B-STDVAL {tag}: the declared series admits NO value "
                f"satisfying {rel} {value} — the bound permits nothing that can "
                f"be bought, which is a stronger finding than a marginal one")

    # ---- B-TOL: the tolerance is itself a load-bearing number.
    tol = b.get("tolerance")
    if tol is not None:
        try:
            tol = float(tol)
        except (TypeError, ValueError):
            fails.append(f"B-SCHEMA {tag}: `tolerance:` must be a number")
            tol = None
    if tol:
        if len(str(b.get("tolerance_why") or "").strip()) < 20:
            fails.append(
                f"B-TOL {tag}: `tolerance: {tol}` with no `tolerance_why:` — "
                f"the tolerance is the number most likely to become the next "
                f"typed number, so it carries the same burden as the bound")
        rivals = [v for v in (chosen, std) if v is not None and value is not None]
        if rivals:
            margin = min(abs(value - v) for v in rivals)
            if margin and tol >= margin:
                fails.append(
                    f"B-TOL {tag}: tolerance {tol} >= {margin:.4g}, the "
                    f"smallest distance from the published bound {value} to a "
                    f"value it must rule on ({', '.join(str(v) for v in rivals)})"
                    f" — a tolerance that cannot distinguish pass from fail is "
                    f"not a tolerance, it is the next typed number, and this is "
                    f"the check that stops this fix from recreating the defect "
                    f"it closes")
    tol = tol or 1e-9

    # ---- the grade declaration must be internally honest before anything runs
    cmd = str(b.get("command") or "").strip()
    grade = str(b.get("grade") or ("CITED" if cmd else "ESTIMATED")).upper()
    if grade not in GRADES:
        fails.append(f"B-GRADE {tag}: grade {grade!r} is not one of "
                     f"{list(GRADES)}")
        grade = "ESTIMATED"
    if grade == "CITED" and not cmd:
        fails.append(f"B-GRADE {tag}: grade CITED with no `command:` — a "
                     f"citation claim with nothing cited. Use grade: ESTIMATED "
                     f"and say why in `why_not_rerunnable:` (canon M-IMPORT)")
    if grade == "ESTIMATED" and len(
            str(b.get("why_not_rerunnable") or "").strip()) < 20:
        fails.append(f"B-GRADE {tag}: grade ESTIMATED needs "
                     f"`why_not_rerunnable:` — ESTIMATED is a legal grade, an "
                     f"UNEXPLAINED one is not")
    if cmd:
        bad = [t for t in MUTATING if t in cmd]
        if bad:
            fails.append(
                f"B-CMD {tag}: `command:` is not read-only ({bad!r}) — this "
                f"gate RUNS what the ADR says, and an audit that can write is "
                f"not an audit")
            cmd = ""

    if not regen:
        return fails, "UNVERIFIED", ["--no-regen"]

    # ---- the ladder's first rung: declared inputs, so a board being rebuilt
    # right now downgrades to UNVERIFIED instead of failing anyone.
    missing_req = [str(r) for r in (b.get("requires") or [])
                   if str(r) != "pcbnew" and not (repo_root / str(r)).exists()]
    if "pcbnew" in [str(r) for r in (b.get("requires") or [])]:
        try:
            subprocess.run(["/usr/bin/python3", "-c", "import pcbnew"],
                           capture_output=True, timeout=60, check=True)
        except Exception:
            missing_req.append("pcbnew (not importable by /usr/bin/python3)")
    if missing_req:
        return fails, "UNVERIFIED", [f"declared input absent here: "
                                     f"{', '.join(missing_req)}"]

    go = _runner(repo_root, timeout)
    out_grade = grade

    # ---- B-REGEN / B-FLIP: does the published bound regenerate?
    regen_val = None
    if cmd:
        regen_val, detail = go(cmd)
        if regen_val is None:
            out_grade = "UNVERIFIED"
            notes.append(f"bound command: {detail}")
        elif value is None:
            out_grade = "UNVERIFIED"
            notes.append(f"regenerated {regen_val} but the published `value:` "
                         f"is unparseable, so there is nothing to diff")
        else:
            delta = abs(regen_val - value)
            flipped = (chosen is not None and rel
                       and satisfies(chosen, rel, value)
                       != satisfies(chosen, rel, regen_val))
            if flipped:
                fails.append(
                    f"B-FLIP {tag}: THE DECISION'S CONCLUSION REVERSES. The "
                    f"ADR publishes {rel} {value} and regenerates {rel} "
                    f"{regen_val}; the value it says it CHOSE ({chosen}) "
                    f"satisfies one and not the other. This is not a "
                    f"{delta:.4g} discrepancy, it is a reversed verdict, and no "
                    f"tolerance excuses it")
                out_grade = "UNVERIFIED"
            elif delta > tol:
                fails.append(
                    f"B-REGEN {tag}: published bound {value}, regenerated "
                    f"{regen_val} at corner {corner!r}, delta {delta:.4g} > "
                    f"tolerance {tol:.4g}. claim: "
                    f"{str(b.get('claim'))[:80]}")
                out_grade = "UNVERIFIED"
            else:
                notes.append(f"regenerated {regen_val} vs published {value} "
                             f"(delta {delta:.4g} <= {tol:.4g})")

    # ---- B-CORNER: the bound must sit on its OWN budget edge at the corner it
    # declares. This runs whether or not `command` was available, because a
    # mislabelled corner is a fail on its own — the ADR-0024 defect.
    if ev_cmd and budget and value is not None and rel:
        edge = inward(value, rel, tol)
        got, detail = go(ev_cmd.replace("{value}", repr(edge)))
        if got is None:
            notes.append(f"corner check: {detail}")
            out_grade = "UNVERIFIED" if out_grade == "CITED" else out_grade
        elif not satisfies(got, budget[0], budget[1]):
            extra = ""
            cc = b.get("corner_commands") or {}
            if isinstance(cc, dict):
                for other, ocmd in sorted(cc.items()):
                    ov, _ = go(str(ocmd))
                    if ov is not None and abs(ov - value) <= max(tol, 1e-9):
                        extra = (f" The published number DOES reproduce at "
                                 f"corner {other!r} ({ov}), so the corner is "
                                 f"mislabelled rather than the arithmetic "
                                 f"wrong.")
                        break
            fails.append(
                f"B-CORNER {tag}: the published bound {value} does NOT sit on "
                f"its own budget edge at the corner it declares — evaluating "
                f"the bound value itself ({edge:.6g}, nudged inward by the "
                f"declared tolerance {tol:.4g}) gives {got}, which violates "
                f"`governs.budget` {budget[0]} {budget[1]}. A bound whose own "
                f"value is inadmissible under its own budget WAS NOT DERIVED AT "
                f"CORNER {corner!r}.{extra} This is the 2026-07-29 ADR-0024 "
                f"class: a remedy quoted at a corner the decision does not use")
            out_grade = "UNVERIFIED"
        else:
            notes.append(f"corner {corner}: the bound value {value} evaluates "
                         f"to {got} at {edge:.6g}, on its budget edge "
                         f"{budget[0]} {budget[1]}")

        # ---- B-STDVAL: a bound is a number PLUS THE PARTS YOU CAN BUY.
        if std is not None:
            sgot, sdetail = go(ev_cmd.replace("{value}", repr(std)))
            if sgot is None:
                notes.append(f"standard-value check: {sdetail}")
                out_grade = "UNVERIFIED" if out_grade == "CITED" else out_grade
            elif not satisfies(sgot, budget[0], budget[1]):
                fails.append(
                    f"B-STDVAL {tag}: the nearest standard value admissible "
                    f"under this bound is {std} ({snote}), and re-evaluated at "
                    f"corner {corner!r} it gives {sgot}, which VIOLATES the "
                    f"bound's own budget {budget[0]} {budget[1]}. THE PUBLISHED "
                    f"BOUND PERMITS A VALUE THAT DOES NOT CLEAR — a bound is "
                    f"not a number, it is a number plus the set of parts you "
                    f"can actually buy, and this is a FAIL rather than a "
                    f"rounding note (ADR-0024: 560 Ohm under a 592 Ohm ceiling "
                    f"gives 0.7007 V and fails by 0.7 mV)")
                out_grade = "UNVERIFIED"
            else:
                notes.append(f"nearest standard value {std} ({snote}) "
                             f"evaluates to {sgot}, inside "
                             f"{budget[0]} {budget[1]}")
    elif value is not None and budget and not ev_cmd:
        notes.append("no `governs.evaluate:` — the corner and standard-value "
                     "checks did not run")
        out_grade = "UNVERIFIED" if out_grade == "CITED" else out_grade

    return fails, out_grade, notes


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("root", help="repo root (or any tree holding ADRs)")
    ap.add_argument("--adr", default="",
                    help="grade only ADR files whose path contains this")
    ap.add_argument("--no-regen", action="store_true",
                    help="do not RUN declared commands (every CITED bound "
                         "degrades to UNVERIFIED — a fast path, not a pass)")
    ap.add_argument("--timeout", type=int, default=180,
                    help="per-command budget; expiry is UNVERIFIED, not a fail")
    ap.add_argument("--repo-root", default="",
                    help="cwd for declared commands (default: ROOT)")
    ap.add_argument("--include-archived", action="store_true")
    ap.add_argument("--strict-owed", action="store_true",
                    help="make an OWED ADR a FAIL rather than named debt under "
                         "the ceiling")
    ap.add_argument("--cited-floor", type=int, default=CITED_FLOOR)
    ap.add_argument("--owed-ceiling", type=int, default=OWED_CEILING)
    a = ap.parse_args(argv)

    root = Path(a.root)
    if not root.is_dir():
        print(f"FAIL B-SRC: no such directory {root}")
        return 1
    repo_root = Path(a.repo_root).resolve() if a.repo_root else root.resolve()

    adrs = find_adrs(root, a.include_archived)
    if a.adr:
        adrs = [p for p in adrs if a.adr in str(p)]

    fails, tally = [], {"CITED": [], "UNVERIFIED": [], "ESTIMATED": []}
    owed, declaring, n_bounds_prose, n_blocks = [], [], 0, 0

    for p in adrs:
        try:
            text = p.read_text(encoding="utf-8-sig", errors="replace")
        except OSError as e:
            fails.append(f"B-SRC {p}: unreadable ({e})")
            continue
        where = f"{p.parent.parent.parent.name}/{p.name}"
        # Count the bounds still living in PROSE, with the declared blocks
        # removed first — a block spells its own `relation:` and
        # `governs.budget:` with the same operators, and counting those would
        # make the debt figure rise as adoption rises.
        in_prose = len(BOUND_IN_PROSE.findall(DECL.sub("", text)))
        n_bounds_prose += in_prose
        blocks, bf = parse_blocks(text, where)
        fails.extend(bf)
        n_blocks += len(blocks)
        if blocks:
            declaring.append(where)
        elif in_prose:
            owed.append(f"{where} — publishes {in_prose} numeric inequality "
                        f"bound(s) in prose and declares no `<!-- bound -->` "
                        f"block")
        for b in blocks:
            bfails, grade, notes = grade_bound(
                b, repo_root, where, regen=not a.no_regen, timeout=a.timeout)
            fails.extend(bfails)
            label = f"{where} [{b.get('id') or b.get('_marker') or '?'}]"
            tally[grade].append(f"{label}: {'; '.join(notes) or 'no detail'}")

    # G-INPUT: name the tree and the documents actually read. A coverage number
    # is only meaningful next to the universe it was taken over.
    print(f"input: root = {root.resolve()}  ({len(adrs)} ADR file(s) under "
          f"docs/decisions + */01_docs/decisions"
          f"{', including archived' if a.include_archived else ''})")
    print(f"input: regeneration {'OFF (--no-regen)' if a.no_regen else 'ON'}, "
          f"cwd for commands = {repo_root}, per-command timeout {a.timeout}s")
    print(f"input: {len(declaring)} ADR(s) declare a `<!-- bound -->` block "
          f"({n_blocks} block(s)); {len(owed)} OWED; {n_bounds_prose} "
          f"inequality bound(s) appear in prose across all {len(adrs)}")

    for label in tally["CITED"]:
        print("  CITED      ", label)
    for label in tally["ESTIMATED"]:
        print("  ESTIMATED  ", label)
    for label in tally["UNVERIFIED"]:
        print("  UNVERIFIED ", label)
    # OWED is printed BY NAME on every run. That enumeration is the whole
    # difference between this and the state that produced the incident: 108
    # published bounds nobody had counted.
    for o in sorted(set(owed)):
        print(("FAIL  B-OWED " if a.strict_owed else "  OWED       ") + o)
    if a.strict_owed:
        fails.extend(f"B-OWED {o}" for o in sorted(set(owed)))

    for f in sorted(set(fails)):
        print("FAIL ", f)

    # ---- the two counting facts, monotone in the direction that matters
    n_cited = len(tally["CITED"])
    # The floors are facts about THIS tree, so they are enforced only when the
    # tree under audit IS the one this script lives in — a scratch fixture is a
    # different universe and a committed 37 says nothing about it. Pinned to the
    # measured counts separately by t1_adr_bounds.py, which always runs against
    # the real ROOT. (The parent walk is guarded: a copy of this gate can live
    # anywhere, and an IndexError there would be a crash instead of a verdict.)
    here = Path(__file__).resolve().parents
    own_tree = len(here) > 3 and root.resolve() == here[3]
    count_fails = []
    if own_tree and n_cited < a.cited_floor:
        count_fails.append(
            f"B-FLOOR: {n_cited} CITED bound(s), below the committed floor of "
            f"{a.cited_floor} — a bound that used to regenerate no longer does, "
            f"or a declaration was deleted. The floor may only be edited UP")
    if own_tree and len(owed) > a.owed_ceiling:
        count_fails.append(
            f"B-FLOOR: {len(owed)} OWED ADR(s) publishing a bound with no "
            f"`<!-- bound -->` block, above the committed ceiling of "
            f"{a.owed_ceiling} — a NEW ADR published a typed bound. Declare it, "
            f"or raise the ceiling in the same commit and name the run. The "
            f"ceiling may only be edited DOWN")
    for f in count_fails:
        print("FAIL ", f)
    fails.extend(count_fails)

    print(f"BOUND COVERAGE: {n_cited} CITED / {len(tally['ESTIMATED'])} "
          f"ESTIMATED / {len(tally['UNVERIFIED'])} UNVERIFIED across "
          f"{n_blocks} declared block(s) in {len(declaring)} ADR(s); "
          f"{len(owed)} of {len(owed) + len(declaring)} bound-publishing ADR(s) "
          f"OWED (floors: CITED >= {a.cited_floor}, OWED <= {a.owed_ceiling}"
          f"{'' if own_tree else '; NOT ENFORCED — foreign tree'})")

    # G-COVER: how many DOCUMENTS were graded, not how many findings printed. A
    # run over zero ADRs used to be indistinguishable from a clean fleet.
    if not adrs:
        print(f"ADR BOUND PROVENANCE: FAIL 0 ADR(s) graded — nothing under "
              f"{root} matched {list(ADR_GLOBS)}. A zero denominator is a FAIL, "
              f"never a pass (canon M-COVER); if this tree genuinely has no "
              f"ADRs, that is a fact worth stating out loud rather than a green "
              f"verdict")
        return 1
    corpus = (f"{len(owed) + len(declaring)}/{len(adrs)} ADR(s) publish an "
              f"inequality bound, {len(declaring)} declare one")
    if not declaring:
        corpus += (" — NOTE: every check that regenerates a number grades only "
                   "DECLARED blocks, and this tree declares none, so the "
                   "regenerating half of this gate graded nothing")
    print("ADR BOUND PROVENANCE:", "FAIL" if fails else "PASS",
          f"({len(set(fails))} fails) — {corpus}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
