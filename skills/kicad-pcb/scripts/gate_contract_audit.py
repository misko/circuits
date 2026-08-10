#!/usr/bin/env python3
"""gate_contract_audit.py — canon G-*: a gate on the gates.

    gate_contract_audit.py [--root DIR] [--json OUT] [--enforce LIST]

WHY THIS EXISTS. `contracts_audit.py` governs FOLDERS. Nothing governed the
CHECKERS, so five of them shipped unable to fail on the property they name, and
a five-release fleet audit (2026-07-26/27) found two boards not orderable with
every gate green. Measured on this repo at the time of writing:

  * A-AMP graded **10 of 57** declared net-class currents fleet-wide. Any
    qualifier ("7 A worst case", "6 A / 5 A", "~1.5A pulsed") made `parse_amps`
    return None, and rules_audit.py then filed it under OKS with the text
    "n/a (no current: declared)". ZERO net classes actually declare no current,
    so that message was wrong 100% of the times it fired. usb-hub-3s-v3 ships
    PWR_IN 7 A, PWR_RAIL 6 A and SWITCH_NODE 7 A — all silenced; the one class
    it did grade, VBUS, FAILED.

    **REPAIRED 2026-07-27 (`rules_audit.py:120-140`), AND THIS PARAGRAPH WENT ON
    ASSERTING THE DEFECT FOR SIX DAYS.** Probe, and the reason every negative
    claim below now carries one (canon G-STALE-NEG):

        /usr/bin/python3 -c "import sys; sys.path.insert(0, \
          'skills/kicad-pcb/scripts'); from rules_audit import parse_amps; \
          print([parse_amps(s) for s in ('7 A worst case', '6 A / 5 A', \
          '~1.5A pulsed')])"
        # 2026-08-02 -> [(7.0, 'number'), (6.0, 'number'), (1.5, 'number')]

    MEASURED COST OF LEAVING IT: an agent planning the R-POUR repair read this
    paragraph, concluded the prose `current:` field "is not machine-readable",
    and built a contract obligation on that premise. One command refutes it. A
    stale negative claim in a gate's own docstring is not documentation debt —
    it is an instrument reporting a defect that no longer exists, and it
    propagates into whatever reads it.
  * `bom_source_check.row_kind()` classifies by the whole leading-alpha run, so
    `RS1/RS2` (the 10 mOhm shunts setting BOTH buck current limits) and `CE1`
    (the only electrolytic, which shipped REVERSED in v1.0/v1.1) exit leg C
    while the tool prints PASS.
  * `labeled_resistance("10mOhm")` returns 1.0e7 — the multiplier is uppercased
    before lookup, so milli decodes as mega.

None of those is a bad line of code. They are one SHAPE: a checker permitted to
report success over input it did not understand.

THE THREE OBLIGATIONS. A script that prints a verdict must:

  G-INPUT   name the artifact it graded, so a reader can tell whether it read
            the SHIPPED bytes or a reconstruction (canon M6). policy_audit ran
            against a `06_build` shadow tree and reported 79 warnings where the
            sealed archive has 102; bom_source_check graded a filename that does
            not exist in the release.
  G-COVER   emit `N graded / M total`. A verdict with no denominator hides its
            own blind spot, and every instance above is invisible without one.
  G-RED     have a fixture in tests/ that makes it FAIL. A gate that has never
            been observed to fail is a claim, not a control.

THIS SCRIPT IS ITSELF A GATE AND MUST OBEY ITS OWN CONTRACT. It reports its
coverage, it names its input, and t1_gate_contract.py holds its known-bads. Its
acceptance test is adversarial: on first run against this repo it MUST flag a
large number of scripts. A gate-on-gates that comes back clean on a codebase
independently measured as riddled is decoration, and should be deleted rather
than trusted.

VACUITY: (canon G-VACUOUS, applied to G-VACUOUS. Fixtured by
`t1_gate_contract.py` `t_vacuity_G_VACUOUS_passes_a_repo_where_no_gate_declares
_anything`.)

G-VACUOUS grades "every gate's blind spot is known". It PASSES on a repo where
**no gate declares anything**, because it treats an absent declaration as OWED
rather than as a violation. That is not a slip — a day-one mandate over 31 gates
lands as 31 red rows and is disabled within the week, which is the failure mode
this whole family exists to avoid. But it means the exit code is compatible with
the graded fact being false for the entire fleet.

HOW THE CIRCLE IS BROKEN. A coverage gate on partial adoption cannot be made
non-vacuous on the empty case; asking it to police itself only regresses. What it
CAN be made is BOUNDED, ENUMERATED and MONOTONE, and all three are outside its own
judgement:

  * BOUNDED — the blind spot is exactly the set in `owed`, and nothing else. Any
    gate that DOES declare is fully graded, in both directions.
  * ENUMERATED — every owed gate is printed BY NAME on every run. The vacuity is
    therefore never silent, which is what separates it from all six instances in
    the G-VACUOUS block below: each of those passed with nothing said.
  * MONOTONE — `VACUITY_FLOOR` is a committed integer, and a drop below it is a
    hard FAIL. `t_vacuity_floor_is_pinned_to_the_measured_count` additionally
    pins the floor to what the tree actually achieves, so the floor cannot be
    lowered to buy a green run and cannot silently lag adoption either.

The floor is data a human must edit, in a file a reviewer reads, checked by a test
that measures the tree. That is the break: G-VACUOUS does not certify its own
adoption — the committed number and the test do, and neither is reachable from
inside the audit.
"""
import argparse
import ast
import json
import re
import sys

try:
    import yaml
except ImportError:            # G-SELFCON degrades to N-A, never a false OK
    yaml = None
from pathlib import Path

#: a script "prints a verdict" if it emits PASS/FAIL/OK as a result word.
VERDICT_RE = re.compile(r"""print\(\s*f?["'][^"']*\b(PASS|FAIL)\b""", re.X)
VERDICT_RE2 = re.compile(r"""["']\s*(PASS|FAIL)\b""")

#: a coverage denominator: "N/M", "graded N of M", "coverage ...".
COVERAGE_RE = re.compile(
    r"coverage|"
    r"\{[^{}]*\}\s*/\s*\{[^{}]*\}|"          # f"{n}/{m}"
    r"\bof\s+\{?len\(|"                       # "of {len(rows)}"
    r"\bgraded\b[^\n]*\bof\b|"
    r"\d+\s*/\s*\{",
    re.I)

#: naming the graded artifact — a path argument or an explicit echo.
#: `--root` / `--project` / `--releases-root` were added after this check
#: FALSE-FAILED `fleet_regrade.py`, which prints the full path of every release
#: it grades — more explicitly than most gates here. The regex is a PROXY for
#: "names what it graded", and a proxy that rejects a tool doing the thing
#: properly is the adjacent-property error this repo keeps paying for.
#: Widened on that principle, not to make one tool pass: any of these options
#: selects the artifact set under grade.
INPUT_RE = re.compile(
    r"add_argument\(\s*[\"'](?!--)|"          # a positional path arg
    r"add_argument\(\s*[\"']--(release|releases-root|root|project|board|pcb|"
    r"zip|fab|bom|cpl|dir|archive|manifest|src|source|input)|"
    r"graded against|read from|input:",
    re.I)

SKIP_BASENAMES = {
    # generators and libraries, not checkers — they produce, they do not grade.
    "pcb_toolkit.py", "fab_tier_util.py", "schwriter2.py", "grind_driver.py",
    "audit_template.py", "circuit_json_to_kicad_pcb.py",
    "circuit_json_to_kicad_sch.py", "generate_board_generic.py",
    "generate_rules_generic.py", "route_and_stitch_generic.py",
    "import_krt.py", "export_fab_jlc.py", "export_jlc_package.py",
    "pcb_status.py", "jlc_rotation_measure.py", "jlc_rotation_resolve.py",
}


def prints_verdict(text):
    return bool(VERDICT_RE.search(text) or VERDICT_RE2.search(text))


def has_red_fixture(name, tests_dir):
    """Some tests/*.py must INVOKE this script AND use must_fail.

    A BARE NAME MATCH IS NOT ENOUGH, and this check shipped with that hole: the
    first version searched for the stem anywhere in the file, so the sentence
    "found by fleet_regrade.py" inside an unrelated test's DOCSTRING satisfied
    G-RED for fleet_regrade. A gate could claim a fixture it does not have —
    a gate-on-gates that cannot fail on the property it names, which is the
    exact defect class it exists to police.

    The first fix over-corrected the other way: requiring the literal path
    `scripts/<stem>.py` false-failed 16 gates that DO have real suites but bind
    through the harness idiom `SCRIPTS / "<stem>.py"` — t1_bom_source.py really
    does exercise bom_source_check.py. Matching a QUOTED filename covers both
    binding forms and still excludes prose, because a docstring sentence writes
    the name bare.

    Still a proxy. A test could quote a name it never runs. But a proxy that
    rejects prose and accepts both real idioms is the honest middle; the
    alternative is parsing call graphs to grade a docstring.
    """
    stem = Path(name).stem
    pat = re.compile(rf"""["'][^"']*{re.escape(stem)}\.py["']""")
    for t in sorted(tests_dir.glob("t*.py")):
        body = t.read_text(errors="replace")
        if pat.search(body) and "must_fail" in body:
            return t.name
    return None


def audit(root, enforce=None):
    root = Path(root)
    tests_dir = root / "tests"
    scripts = sorted(root.glob("skills/*/scripts/*.py"))
    rows, unparsed = [], []
    for p in scripts:
        if p.name in SKIP_BASENAMES:
            continue
        try:
            text = p.read_text(encoding="utf-8-sig")
            ast.parse(text)                 # a file we cannot parse is a FAIL
        except Exception as e:
            unparsed.append(f"{p.relative_to(root)}: {e}")
            continue
        if not prints_verdict(text):
            continue
        rows.append({
            "script": str(p.relative_to(root)),
            "cover": bool(COVERAGE_RE.search(text)),
            "input": bool(INPUT_RE.search(text)),
            "red": has_red_fixture(p.name, tests_dir),
        })

    want = set(enforce or ["G-COVER", "G-INPUT", "G-RED"])
    fails = []
    for r in rows:
        if "G-COVER" in want and not r["cover"]:
            fails.append(f"G-COVER {r['script']}: prints a verdict with no "
                         f"`N/M` coverage denominator — it can report success "
                         f"over input it did not understand")
        if "G-INPUT" in want and not r["input"]:
            fails.append(f"G-INPUT {r['script']}: never names the artifact it "
                         f"graded — a reader cannot tell shipped bytes from a "
                         f"reconstruction (canon M6)")
        if "G-RED" in want and not r["red"]:
            fails.append(f"G-RED {r['script']}: no tests/ fixture makes it "
                         f"FAIL — it has never been observed to gate")
    return {"root": str(root), "gates": rows, "fails": fails,
            "unparsed": unparsed,
            "coverage": f"{len(rows)}/{len(rows)} verdict-printing scripts "
                        f"audited ({len(scripts)} scripts scanned, "
                        f"{len(SKIP_BASENAMES)} generator/library names skipped)"}



# --------------------------------------------------------------- G-SELFCON
# ADR-0007. A rule file can contradict ITSELF, and then no board can satisfy it.
# fab_tiers.yaml declared min_silk_text_height 0.45 AND min_silk_stroke 0.15 on
# every tier, while KiCad clamps a text stroke to <= 0.25 x height: 0.45 mm text
# can reach at most 0.1125 mm of stroke, so the two floors cannot both be met.
# smc0985-cooksense then shipped six SAFETY designators below the stroke floor —
# J_ESTOP, J_DOOR, J_MODE among them — and the waiver written the same day
# called 0.13 acceptable. Nothing could have passed; nothing said so.
#
# WIDENED 2026-07-29 (same day, second lesson). The first version modelled ONLY
# that upper clamp, so it could prove a published stroke UNREACHABLE but was
# blind to the other direction — and the corollary written beside it in
# fab_tiers.yaml ("to reach the published 0.15 stroke, text must be >= 0.60mm")
# was WRONG for exactly that reason: the generator's LOWER floor is
# max(min_silk_stroke, 0.13, 0.16 x height), so 0.60 / 0.70 / 0.80 all emit
# 0.13 and the true threshold is 0.9375. Two boards (pluto-rx2-8way,
# pluto-cal-switch) each discovered that by measuring the generator after
# following the sentence. A gate that catches only the direction its author got
# right is worthless (canon M-WIDTH), so the rule is now written at the width of
# its class: a tier's published stroke floor must EQUAL what the generator will
# actually emit at that tier's own height floor, in BOTH directions, and the
# tier's declared threshold height for the fab's published stroke must be the
# FIRST height at which the generator reaches it.
#
# THE FORMULA IS NOT COPIED HERE. `load_stroke_model` lifts `silk_stroke` and
# its constants out of generate_board_generic.py's AST and calls them: a checker
# that carries its own copy of the formula it grades is canon M1 failing in the
# other direction — it agrees with a stale copy.
GEN_PATH = Path(__file__).resolve().parent / "generate_board_generic.py"

#: (label, ratio-constant, hard-floor-constant) — the generator has TWO stroke
#: pairs, and one hand-derived corollary could not have covered both.
EMITTERS = (("board silk text", "SILK_STROKE_OVER_SIZE", "SILK_STROKE_MIN"),
            ("refdes de-collision", "REFDES_STROKE_OVER_SIZE",
             "REFDES_STROKE_MIN"))


class SelfConError(RuntimeError):
    """The stroke model could not be lifted from the generator. Never a skip:
    a G-SELFCON that cannot find the formula must FAIL, not pass quietly."""


def load_stroke_model(path=GEN_PATH):
    """(silk_stroke, constants) taken FROM the generator's own source.

    The module cannot simply be imported — it imports pcbnew, which only the
    KiCad interpreter has — so its AST is filtered to the module-level numeric
    constants plus the `silk_stroke` FunctionDef and exec'd. What runs here is
    therefore the exact arithmetic the boards are built with."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8-sig"))
    keep, fn = [], None
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name) \
                and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, (int, float)) \
                and not isinstance(node.value.value, bool):
            keep.append(node)
        elif isinstance(node, ast.FunctionDef) and node.name == "silk_stroke":
            keep.append(node)
            fn = node
    ns = {}
    try:
        exec(compile(ast.Module(body=keep, type_ignores=[]), str(path), "exec"),
             ns)
    except Exception as e:            # a renamed/moved constant lands here
        raise SelfConError(
            f"{path.name}'s silk_stroke() no longer stands alone at module "
            f"level ({type(e).__name__}: {e}) — G-SELFCON grades the "
            f"generator's OWN formula and will not fall back to a copy of it "
            f"(canon M1). Keep the formula and its constants module-level, or "
            f"update load_stroke_model deliberately")
    need = ["KICAD_STROKE_OVER_HEIGHT"] + \
        [c for _, r, h in EMITTERS for c in (r, h)]
    missing = [k for k in need if not isinstance(ns.get(k), float)]
    if fn is None or missing:
        raise SelfConError(
            f"{path.name} no longer declares "
            f"{'silk_stroke() ' if fn is None else ''}{missing} at module "
            f"level — G-SELFCON grades the generator's OWN formula and will "
            f"not fall back to a copy of it (canon M1)")
    return ns["silk_stroke"], ns


def _emitted(fn, ns, h, floor):
    """{emitter: stroke the generator emits} for text of height `h`."""
    return {name: fn(float(h), float(floor), ns[ratio], ns[hard])
            for name, ratio, hard in EMITTERS}


def _first_height_reaching(fn, ns, floor, target, hi=50.0):
    """The LOWEST text height at which EVERY emitter reaches `target`, by
    bisection on the generator's own (monotone non-decreasing) formula. None
    when no height does."""
    def worst(h):
        return min(_emitted(fn, ns, h, floor).values())
    if worst(hi) < target - 1e-12:
        return None
    lo = 1e-3
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if worst(mid) >= target - 1e-12:
            hi = mid
        else:
            lo = mid
    return hi


def check_self_consistency(refs_dir):
    """Cross-FIELD checks on the rule files themselves. Returns (fails, n),
    n being the number of tiers graded (canon M-COVER)."""
    fails, n = [], 0
    ft = Path(refs_dir) / "fab_tiers.yaml"
    if not ft.exists() or yaml is None:
        return fails, n
    try:
        fn, ns = load_stroke_model(GEN_PATH)   # module global: patchable in tests
    except (SelfConError, SyntaxError, OSError, ValueError) as e:
        return [f"G-SELFCON {e}"], 0
    clamp = ns["KICAD_STROKE_OVER_HEIGHT"]
    doc = yaml.safe_load(ft.read_text(encoding="utf-8-sig")) or {}
    for tier, d in sorted((doc.get("tiers") or {}).items()):
        if not isinstance(d, dict):
            continue
        h, s = d.get("min_silk_text_height"), d.get("min_silk_stroke")
        if h is None or s is None:
            continue
        n += 1
        h, s = float(h), float(s)
        emitted = _emitted(fn, ns, h, s)

        # (1) BOTH DIRECTIONS. The published floor must be exactly what the
        #     generator emits at the tier's own height floor.
        for name, got in sorted(emitted.items()):
            if got < s - 1e-9:
                fails.append(
                    f"G-SELFCON fab_tiers.yaml[{tier}]: min_silk_stroke "
                    f"{s} mm is UNREACHABLE at min_silk_text_height {h} mm — "
                    f"KiCad clamps stroke to <= {clamp} x height, so the most "
                    f"the {name} path can plot is {got:.4f} mm. No board can "
                    f"satisfy both floors; raise the height to "
                    f">= {s / clamp:.2f} mm or lower the stroke to "
                    f"<= {got:.4f} mm")
            elif got > s + 1e-9:
                fails.append(
                    f"G-SELFCON fab_tiers.yaml[{tier}]: min_silk_stroke {s} mm "
                    f"is a FICTION — at min_silk_text_height {h} mm the "
                    f"generator's {name} path emits {got:.4f} mm and cannot go "
                    f"thinner, so the published floor understates the file's "
                    f"own behaviour and a board 'meeting' it proves nothing. "
                    f"Publish {got:.4f} mm, or raise min_silk_text_height")

        # (2) THE COROLLARY, AS DATA. A tier that publishes the fab's stroke
        #     must also declare the FIRST height its own generator reaches it
        #     at — the claim that was prose, and wrong, for one day.
        pub, ph = d.get("published_silk_stroke"), d.get("published_stroke_min_height")
        if pub is None or ph is None:
            fails.append(
                f"G-SELFCON fab_tiers.yaml[{tier}]: declares min_silk_stroke "
                f"but not the coupling it is bound by — "
                f"published_silk_stroke / published_stroke_min_height are "
                f"missing, so the file's legibility corollary is prose again "
                f"and cannot be checked (it was prose, and wrong, on "
                f"2026-07-29: '0.60mm reaches 0.15' — it is 0.9375mm)")
            continue
        pub, ph = float(pub), float(ph)
        if pub < s - 1e-9:
            fails.append(
                f"G-SELFCON fab_tiers.yaml[{tier}]: published_silk_stroke "
                f"{pub} mm is BELOW the enforced min_silk_stroke {s} mm — the "
                f"fab's published floor cannot be laxer than the one enforced")
        true_h = _first_height_reaching(fn, ns, s, pub)
        at_declared = min(_emitted(fn, ns, ph, s).values())
        if at_declared < pub - 1e-9:
            fails.append(
                f"G-SELFCON fab_tiers.yaml[{tier}]: "
                f"published_stroke_min_height {ph} mm does NOT reach "
                f"published_silk_stroke {pub} mm — at {ph} mm the generator "
                f"emits only {at_declared:.4f} mm "
                f"({', '.join(f'{k} {v:.4f}' for k, v in sorted(_emitted(fn, ns, ph, s).items()))}). "
                f"The first height that reaches {pub} mm is "
                f"{'no height below 50 mm' if true_h is None else f'{true_h:.4f} mm'}")
        elif true_h is not None and ph > true_h + 1e-6:
            fails.append(
                f"G-SELFCON fab_tiers.yaml[{tier}]: "
                f"published_stroke_min_height {ph} mm is not the FIRST height "
                f"reaching published_silk_stroke {pub} mm — the generator "
                f"already emits {min(_emitted(fn, ns, true_h, s).values()):.4f} mm "
                f"at {true_h:.4f} mm, so the declared threshold outlaws legible "
                f"text for no reason")
    return fails, n


# --------------------------------------------------------------- G-VACUOUS
# THE QUESTION G-RED DOES NOT ASK. G-RED asks "can this gate fail at all?" and
# 31/31 gates answer yes. That is the weak form. The strong form is: CAN IT FAIL
# ON THE CASE IT EXISTS FOR? Six gates measured GREEN on 2026-07-28/29 while the
# fact each grades was FALSE, every one of them internally honest:
#
#   * R-LEN (policy_audit.py:1078) is `re.search(r"length|spread", audit_src)`.
#     smc0985-cooksense gets PASS on ZERO code matches — its only two hits are
#     the words "slot-lengthened" and "lengthens" in COMMENTS about high-voltage
#     creepage. Measured: 3 of 6 boards PASS, 1 of the 3 on comments alone; and
#     pluto-cal-switch, which carries an ADR titled "length match is a published
#     artifact", grades N-A "no timing-critical nets declared".
#   * cooksense's `keypad_isolation_6mm` .kicad_dru rule conditions on
#     `B.NetName != ''`, so UNNETTED copper is exempt BY CONSTRUCTION. Measured:
#     the nearest unnetted copper to a KEYPAD_ISO net is 1.0672 mm from a
#     6.000 mm constraint — a 5.6x violation, on 106 pairs, and the nearest item
#     is J_KEY_MATRIX.MP, the connector shell tab the rule was written for.
#     "0 DRC violations" was never evidence about it.
#   * twin_overlay A-RENDER grades only the parts whose body survives a 2 px
#     erosion at jlc_twin's hard-coded 1600x1000 render. On the 188.1 mm
#     cooksense board that is 8.34 px/mm and 53 of 210 parts are graded.
#   * waiver_provenance W-COPY/W-FOREIGN compare waiver PROSE to other prose and
#     never re-derive a number. A waiver reading "C_SW1 pad 1 -> U_SW pin 8 =
#     2.62 mm, inside the 3 mm" measures 3.085 mm centre-to-centre — OVER the
#     threshold it claimed to be inside — and passed for a full revision cycle.
#   * power_topology E-OFF returns N-A when it finds no source_type, no battery
#     net and no battery-ish ADR, so a real battery board that declares nothing
#     exits 0.
#   * part_facts_check P-FACT now FAILS a zero denominator, but two paths still
#     print `P-FACT OK - 0/0` and exit 0.
#
# So a gate must declare the input class on which it PASSES while the graded
# fact is FALSE. THE DECLARATION IS A FIXTURE, NOT PROSE. A declared blind spot
# with no fixture is strictly worse than an undeclared one: it reads as diligence
# and grades nothing, which is the `keep_short` failure (39 of 181 budgets
# addressed to net names no board has) one level up. So the binding is
# bidirectional and both halves are machine-graded:
#
#   the gate's module DOCSTRING carries a `VACUITY:` block   <->   tests/ carries
#   @test(..., kind="vacuity", gate="<basename>.py") that CONSTRUCTS that input
#   and asserts the gate PASSES on it.
#
# A fixture asserting `must_fail` is a FALSE declaration and fails statically:
# it proves the gate BITES where the docstring claims it is blind. Prose with no
# fixture fails. A fixture with no prose fails (a reader of the gate must see
# it). A fixture naming a gate not in the inventory fails (a rename silently
# un-declares otherwise).
#
# WHY THE DOCSTRING AND NOT A REGISTRY. A registry is a second home and drifts;
# the R-LEN defect above is precisely a check satisfied by text. So the
# declaration is read from `ast.get_docstring` ONLY — a `VACUITY:` in a comment,
# in a nested function's docstring, or in a code string does NOT satisfy it, and
# `t_vacuity_prose_outside_the_module_docstring_is_not_a_declaration` pins that.
# The docstring alone is still prose; what makes it a check is that it is
# INERT WITHOUT the fixture, and the fixture is inert without it.
VACUITY_RE = re.compile(r"^[ \t]*VACUITY:", re.M)

#: THE RATCHET. 31 gates are in the inventory and a day-one fleet mandate would
#: land as 31 red rows and be disabled by the end of the week (the honest
#: precedent: G-RED's own adversarial acceptance floor had to be DELETED once
#: the backlog closed, not lowered). So coverage is REPORTED for all 31 and
#: OWED gates are named, while only three things FAIL: a false declaration, a
#: declaration without a fixture, and a drop below this floor. Raise it as gates
#: adopt; `t_vacuity_floor_is_pinned_to_the_measured_count` refuses a lowering.
#: 6 since 2026-07-29: `schema_reader_audit.py` (canon G-ORPHAN) landed with a
#: declared and fixtured blind spot — it PASSES a family whose every key is
#: declared `OWED`. Raised in the SAME commit that added the declaration, which
#: is the ratchet working rather than a number chasing the tree.
#: 8 since 2026-07-30: `build_provenance.py` (canon M-FRESH) declared F-RENDER's
#: blind spot when the finding landed — the HUMAN schematic has no second copy
#: to hash against, so its build-time freshness is a TIME ORDERING and a `touch`
#: defeats it, where F-PATH's cross-file sha256 cannot be defeated at all. The
#: interesting part is that ONE GATE now carries both: the same file has an
#: undefeatable assertion and a forgeable one, and only saying so out loud keeps
#: a reader from generalising the strong one to the weak one.
#: 10 since 2026-07-31: `trace_audit.py` (canon GG-SHADOW/GG-RESOLVE) declares
#: the blind spot that STOPPED its own layer — it exits 0 over a battery that
#: saw only a gate's own PRE-EXISTING exhaust, because neither the write-set (a
#: METHOD test) nor the pre-run snapshot (an EXISTENCE test) is an IDENTITY
#: test. The declaration landed WITH its fixture, which reproduces the vacuous
#: pass on every run instead of asserting it in prose. Raised in the same commit
#: that earns it, never ahead of one.
VACUITY_FLOOR = 13


def vacuity_declaration(text):
    """The `VACUITY:` block from the MODULE docstring, or None.

    Deliberately not a whole-file search. `R-LEN` is
    `re.search(r"length|spread", audit_src)` over raw source text, and
    smc0985-cooksense earns a PASS from the word "lengthens" in a comment about
    creepage. A gate-on-gates that accepted a `VACUITY:` anywhere in a file
    would reproduce that defect in the act of policing it."""
    try:
        doc = ast.get_docstring(ast.parse(text))
    except SyntaxError:
        return None
    if not doc or not VACUITY_RE.search(doc):
        return None
    return doc[VACUITY_RE.search(doc).start():].strip()


def vacuity_fixtures(tests_dir):
    """{gate basename: [fixture]} from `@test(..., kind="vacuity", gate=...)`.

    An EXACT binding, read from the decorator's AST — not a name-in-the-file
    proxy like `has_red_fixture`. G-RED had to settle for a proxy because it
    retrofits 31 pre-existing suites; G-VACUOUS is new, so it can demand that a
    fixture NAME its subject and there is no reason to accept less.

    Each fixture records whether its body asserts PASS or FAIL, because that is
    what makes the declaration checkable: a vacuity fixture asserts the gate
    passes on input whose graded fact is false. One asserting `must_fail` has
    disproved the very blind spot it claims."""
    out = {}
    for t in sorted(Path(tests_dir).glob("t*.py")):
        try:
            tree = ast.parse(t.read_text(errors="replace"))
        except SyntaxError:
            continue
        src = t.read_text(errors="replace").splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                kw = {k.arg: k.value for k in dec.keywords if k.arg}
                kind = kw.get("kind")
                if not (isinstance(kind, ast.Constant)
                        and kind.value == "vacuity"):
                    continue
                gate = kw.get("gate")
                gate = gate.value if isinstance(gate, ast.Constant) else None
                body = "\n".join(src[node.lineno - 1:(node.end_lineno or
                                                      node.lineno)])
                # ORDER MATTERS, and this cost a revision. The first version
                # failed any vacuity fixture containing `must_fail` at all —
                # and that flagged the four best fixtures in the repo, because
                # each asserts the blind spot AND THEN a CONTRAST: the same
                # input changed in one way, which the gate DOES catch. The
                # contrast is what proves the fixture is a good input broken one
                # way (tests/README) rather than an input the gate simply cannot
                # read. So the rule is about the SUBJECT assertion: the FIRST
                # pass/fail assertion must be a `must_pass`, on the vacuity
                # input itself. A fixture whose first — or only — assertion is
                # `must_fail` has disproved the blind spot it claims.
                order = [m.group(1) for m in
                         re.finditer(r"\b(must_pass|must_fail)\(", body)]
                out.setdefault(gate, []).append({
                    "test": t.name, "func": node.name,
                    "asserts_fail": bool(order) and order[0] == "must_fail",
                    "asserts_pass": ("must_pass(" in body
                                     or "check(" in body or "eq(" in body),
                })
    return out


def check_vacuity(root, rows):
    """(fails, stats) for G-VACUOUS over the gate inventory `rows`."""
    root = Path(root)
    fixtures = vacuity_fixtures(root / "tests")
    inventory = {Path(r["script"]).name for r in rows}
    fails, declared, bound, owed = [], [], [], []

    for r in rows:
        name = Path(r["script"]).name
        try:
            decl = vacuity_declaration((root / r["script"]).read_text(
                encoding="utf-8-sig"))
        except OSError:
            decl = None
        fx = fixtures.get(name, [])
        r["vacuity"] = bool(decl)
        r["vacuity_fixture"] = [f["func"] for f in fx]
        if decl:
            declared.append(name)
        if decl and fx:
            bound.append(name)
        elif decl and not fx:
            fails.append(
                f"G-VACUOUS {r['script']}: its docstring declares a VACUITY: "
                f"condition and NO tests/ fixture exercises it "
                f"(@test(..., kind=\"vacuity\", gate=\"{name}\")). A declared "
                f"blind spot with no fixture is WORSE than an undeclared one — "
                f"it reads as diligence and grades nothing, which is the "
                f"keep_short defect (39 of 181 budgets addressed to net names "
                f"no board has) one level up")
        elif fx and not decl:
            fails.append(
                f"G-VACUOUS {r['script']}: tests/{fx[0]['test']} carries a "
                f"vacuity fixture ({fx[0]['func']}) but the module docstring "
                f"has no VACUITY: block — the blind spot is invisible where "
                f"anyone reading the gate would look, and a docstring rewrite "
                f"cannot then contradict a fixture nobody reads")
        else:
            owed.append(name)
        for f in fx:
            if f["asserts_fail"]:
                fails.append(
                    f"G-VACUOUS {r['script']}: {f['test']}:{f['func']} is "
                    f"declared kind=\"vacuity\" and its FIRST assertion is "
                    f"must_fail — it PROVES the gate bites on the input the "
                    f"docstring calls a blind spot, so the declaration is "
                    f"FALSE. A blind spot that has been closed is a known_bad "
                    f"fixture, not a vacuity one. (A must_fail CONTRAST after "
                    f"the must_pass on the vacuity input is not only allowed "
                    f"but wanted — it is what proves the fact is gradeable at "
                    f"all.)")
            elif not f["asserts_pass"]:
                fails.append(
                    f"G-VACUOUS {r['script']}: {f['test']}:{f['func']} is "
                    f"declared kind=\"vacuity\" and asserts NOTHING — no "
                    f"must_pass/check/eq in its body. That is prose in a .py "
                    f"file, which is the form this check exists to reject")

    for gate, fx in sorted(fixtures.items()):
        if gate is None:
            fails.append(
                f"G-VACUOUS tests/{fx[0]['test']}:{fx[0]['func']}: a vacuity "
                f"fixture with no gate=\"<basename>.py\" — an unbound fixture "
                f"cannot be counted for any gate and cannot go stale visibly")
        elif gate not in inventory:
            fails.append(
                f"G-VACUOUS tests/{fx[0]['test']}:{fx[0]['func']}: names "
                f"gate=\"{gate}\", which is not in the verdict-printing "
                f"inventory — a renamed or retired gate silently un-declares "
                f"its blind spot otherwise")

    # THE FLOOR IS A FACT ABOUT THIS TREE, so it is enforced only when the tree
    # under audit IS the one this script lives in. A `--root` pointing at a
    # miniature fixture (or another checkout) is a DIFFERENT inventory, and a
    # committed count of 5 says nothing about it — enforcing it there made three
    # of the pre-existing G-COVER/G-INPUT/G-RED synthetic tests fail on a
    # property they are not about. Not an escape hatch: the floor is separately
    # pinned to the measured count by t1_gate_contract's
    # `t_vacuity_floor_is_pinned_to_the_measured_count`, which always runs
    # against the real ROOT.
    own_tree = root.resolve() == Path(__file__).resolve().parents[3]
    if own_tree and len(bound) < VACUITY_FLOOR:
        fails.append(
            f"G-VACUOUS: {len(bound)} gate(s) carry a fixtured vacuity "
            f"condition, below the committed floor of {VACUITY_FLOOR}. The "
            f"floor only ratchets UP; a gate whose blind spot was documented "
            f"and is now not has lost a control, not gained a clean run")

    return fails, {"declared": sorted(declared), "bound": sorted(bound),
                   "owed": sorted(owed), "total": len(rows),
                   "floor": VACUITY_FLOOR}


# ------------------------------------------------- G-VACUOUS, the DRU class
# THE WORST INSTANCE ON THE LIST IS NOT A PYTHON GATE. `keypad_isolation_6mm`
# lives in a `.kicad_dru` file, and its condition ends `&& B.NetName != ''`.
# Every rule-file predicate is a gate, and a predicate that excludes its own
# subject is the same defect — worse, because it makes DRC ITSELF report zero.
#
# Two checkable species, and the parser is deliberately small: it grades the
# CONDITION as a boolean over an INVENTORY of what the board actually contains,
# so it needs no geometry. `condition` is a disjunction of conjunctions in every
# form this repo generates; a rule can only fire if SOME alternative has all its
# required atoms satisfiable.
DRU_ATOM_RE = re.compile(
    r"(?P<side>[AB])\.(?P<prop>NetClass|NetName)\s*(?P<op>==|!=)\s*"
    r"'(?P<val>[^']*)'|"
    r"(?P<side2>[AB])\.insideArea\(\s*'(?P<area>[^']*)'\s*\)")

#: constraints whose whole purpose is to police copper that may be UNNETTED —
#: a shell tab, a mounting pad, a fill island. An exemption for empty net names
#: in one of these excludes the subject.
DRU_CLEARANCE_KINDS = ("clearance", "physical_clearance", "hole_clearance",
                       "edge_clearance", "physical_hole_clearance",
                       "silk_clearance", "courtyard_clearance")

#: constraint kinds whose subjects are exactly the objects `board.GetTracks()`
#: returns — tracks, arcs, vias. `dru_area_members` counts members only for a
#: rule whose every constraint is in here; a clearance-family rule also polices
#: pads, courtyards and fill, so counting tracks alone would under-count and an
#: under-count is what a false "0 members, retire it" is made of.
DRU_TRACKLIKE = {"track_width", "via_diameter", "via_drill", "via_count",
                 "annular_width", "length", "skew", "diff_pair_gap",
                 "diff_pair_uncoupled", "track_angle", "track_segment_length"}


def parse_dru(text):
    """[{name, condition, constraints, line}] by paren matching (the format is
    s-expressions; a line regex would miss a wrapped condition).

    THE NAME MAY BE BARE. `generate_rules_generic` writes `(rule "PWR_width"`
    but stitch's `_append_stub_dru` writes `(rule pad_rescue_stubs` — both are
    legal .kicad_dru. This matcher required the quotes until 2026-07-31, so it
    read 77 of the fleet's 83 rules and the 6 it skipped were EVERY
    `pad_rescue_stubs` on every board — i.e. the one rule family this gate's
    own docstring is about, and the only family that is preserved across runs
    rather than regenerated. A gate blind to its own subject reports zero and
    calls it clean. RED-verified by `t_dru_grades_bare_rule_names`."""
    rules = []
    for m in re.finditer(r"\(rule\s+(?:\"([^\"]*)\"|([^\"\s()]+))", text):
        depth, i = 0, m.start()
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = text[m.start():i + 1]
        cond = re.search(r"\(condition\s+\"((?:[^\"\\]|\\.)*)\"", body)
        rules.append({
            "name": m.group(1) if m.group(1) is not None else m.group(2),
            "condition": (cond.group(1).replace('\\"', '"') if cond else None),
            "constraints": re.findall(r"\(constraint\s+(\w+)", body),
            "line": text[:m.start()].count("\n") + 1,
        })
    return rules


def dru_area_members(pcb_path, rules):
    """{rule name: member count or None} — how many board items each rule's
    condition can actually match, by pcbnew GEOMETRY.

    A NAMED AREA IS NOT A POPULATED ONE, and that is the third species of DRU
    vacuity. Check (1) below asks whether the board HAS a rule area of that
    name; a rule can pass it and still be dead, because the area survives on
    the board with nothing inside it. Only geometry answers that.

    INDEPENDENT ON PURPOSE (canon M1). `generate_rules_generic` retires a
    preserved rule using `dru_subject`, which parses the `.kicad_pcb` as TEXT
    and does its own point-in-polygon. This function must NOT import it: it
    asks the same question of pcbnew's object model and SHAPE_POLY_SET
    collision, so agreement between the two is evidence rather than a
    tautology. Fleet cross-check 2026-07-31: the two methods agreed on the
    zero/non-zero verdict for all 6 `pad_rescue_stubs` rules.

    None means NOT DERIVABLE (a NetClass atom, a constraint whose subjects are
    pads/courtyards, an unmodelled operator) and is never graded as empty."""
    import pcbnew                                           # noqa: PLC0415
    b = pcbnew.LoadBoard(str(pcb_path))
    zones = {}
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName():
            zones.setdefault(z.GetZoneName(), []).append(z)
    items = [t for t in b.GetTracks()]

    out = {}
    for r in rules:
        cond, kinds = r["condition"], set(r["constraints"])
        if cond is None or not kinds or not kinds <= DRU_TRACKLIKE:
            out[r["name"]] = None
            continue
        alts, ok_shape = [], True
        for alt in cond.split("||"):
            atoms, rest = [], alt
            for m in DRU_ATOM_RE.finditer(alt):
                atoms.append(m)
                rest = rest.replace(m.group(0), "", 1)
            # a B-side atom makes membership a question about a PAIR, and every
            # TRACKLIKE constraint is single-item — decline rather than guess
            if (re.sub(r"[\s()&]", "", rest)
                    or any(m.group("prop") == "NetClass" for m in atoms)
                    or any((m.group("side") or m.group("side2")) == "B"
                           for m in atoms)):
                ok_shape = False
                break
            alts.append(atoms)
        if not ok_shape or not alts:
            out[r["name"]] = None
            continue

        n = 0
        for it in items:
            shape, layer, net = it.GetEffectiveShape(), it.GetLayer(), it.GetNetname()
            for atoms in alts:
                hit = True
                for m in atoms:
                    if m.group("area") is not None:
                        zs = [z for z in zones.get(m.group("area"), [])
                              if z.IsOnLayer(layer)]
                        if not any(z.Outline().Collide(shape, 0) for z in zs):
                            hit = False
                            break
                    elif (net == m.group("val")) != (m.group("op") == "=="):
                        hit = False
                        break
                if hit:
                    n += 1
                    break
        out[r["name"]] = n
    return out


def check_dru_vacuity(rules, inv, source="<dru>", members=None):
    """(fails, graded) — a rule-file predicate must be able to fire on the
    geometry it names.

    `inv` is what the board HAS: {"netclasses": set, "nets": set,
    "areas": set, "unnetted": int}. Pure and inventory-driven on purpose, so
    the same function grades a synthetic fixture and a real board and nothing
    has to be believed about either."""
    fails, graded = [], 0
    for r in rules:
        cond = r["condition"]
        if cond is None:
            continue
        graded += 1
        clear = [c for c in r["constraints"] if c in DRU_CLEARANCE_KINDS]

        # (1) CAN IT FIRE AT ALL? A positive atom naming a netclass/net/area the
        #     board does not have is a required conjunct that is never true.
        alts, dead = [a.strip() for a in cond.split("||")], []
        for alt in alts:
            for m in DRU_ATOM_RE.finditer(alt):
                if m.group("area") is not None:
                    if m.group("area") not in inv.get("areas", set()):
                        dead.append(f"insideArea('{m.group('area')}') — no such "
                                    f"rule area on the board")
                    continue
                if m.group("op") != "==" or not m.group("val"):
                    continue
                pool = ("netclasses" if m.group("prop") == "NetClass"
                        else "nets")
                if m.group("val") not in inv.get(pool, set()):
                    dead.append(f"{m.group('side')}.{m.group('prop')} == "
                                f"'{m.group('val')}' — no such "
                                f"{'netclass' if pool == 'netclasses' else 'net'}")
        if dead and len(dead) >= len(alts):
            fails.append(
                f"G-VACUOUS-DRU {source}:{r['line']} rule \"{r['name']}\": its "
                f"condition can NEVER be true — {'; '.join(sorted(set(dead)))}. "
                f"The rule is decoration and DRC reports zero for it by "
                f"construction")

        # (2) DOES IT EXEMPT ITS OWN SUBJECT? `NetName != ''` on a clearance
        #     rule exempts unnetted copper, which is exactly what an isolation
        #     barrier exists to hold off.
        for m in re.finditer(r"([AB])\.NetName\s*!=\s*''", cond):
            if not clear:
                continue
            fails.append(
                f"G-VACUOUS-DRU {source}:{r['line']} rule \"{r['name']}\": its "
                f"{m.group(1)}-side condition requires "
                f"{m.group(1)}.NetName != '', so UNNETTED copper is EXEMPT BY "
                f"CONSTRUCTION from a {'/'.join(clear)} constraint — and the "
                f"board carries {inv.get('unnetted', '?')} unnetted copper "
                f"item(s). A shell tab, mounting pad or fill island is the case "
                f"an isolation barrier exists for, so '0 DRC violations' is not "
                f"evidence about it. Measured on smc0985-cooksense: nearest "
                f"unnetted copper to a KEYPAD_ISO net 1.0672 mm against a "
                f"6.000 mm constraint, 106 pairs under the floor, the nearest "
                f"being the keypad connector's own shell tab")

        # (3) IS ITS SUBJECT STILL THERE? A rule can clear (1) — every name it
        #     mentions exists — and still match NOTHING, because the named area
        #     survives on the board with nothing inside it. That is how a
        #     PRESERVED rule dies: `generate_rules_generic.foreign_dru_rules`
        #     carried any rule it did not own forward on every run, so a
        #     `pad_rescue_stubs` sub-floor outlived the stubs it exempted.
        #     Graded from GEOMETRY (dru_area_members), which (1) cannot see.
        n = (members or {}).get(r["name"])
        if n == 0 and not (dead and len(dead) >= len(alts)):    # (1) said it first
            fails.append(
                f"G-VACUOUS-DRU {source}:{r['line']} rule \"{r['name']}\": every "
                f"name in its condition exists on the board, but ZERO board "
                f"items match it — the rule has no subject left. A preserved "
                f"rule is not retired by anything upstream, so it survives as "
                f"a predicate that can never fire and DRC reports zero for it "
                f"by construction. Re-run the pass that owns it, or let "
                f"generate_rules_generic retire it")
    return fails, graded


def dru_inventory(pcb_path):
    """What the board HAS, read from the .kicad_pcb by pcbnew.

    Imported lazily: G-VACUOUS's python arm must run under a plain interpreter,
    and only this function needs the KiCad one."""
    import pcbnew                                       # noqa: PLC0415
    b = pcbnew.LoadBoard(str(pcb_path))
    nets = {n.GetNetname() for n in b.GetNetsByNetcode().values()
            if n.GetNetname()}
    ncls = {b.FindNet(n).GetNetClassName() for n in nets if b.FindNet(n)}
    areas = {z.GetZoneName() for z in b.Zones() if z.GetZoneName()}
    # ON COPPER, and this number was reconciled rather than accepted. A first
    # forensic pass reported 8 unnetted pads on cooksense; 6 of those are NPTH
    # mounting holes (H1-H4) and J_TC's two NPTH pads, which are on NO copper
    # layer and therefore cannot violate a copper clearance rule at all. The
    # honest count is 2 — and both are `J_KEY_MATRIX.MP`, the keypad connector's
    # SM10B-GHS-TB shell tabs, i.e. EXACTLY the tab `keypad_isolation_6mm` was
    # written for. Filtering to copper made the finding sharper, not weaker.
    unnetted = 0
    for f in b.GetFootprints():
        for p in f.Pads():
            if (not p.GetNetname()
                    and p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH
                    and p.IsOnCopperLayer()):
                unnetted += 1
    for t in b.GetTracks():
        if not t.GetNetname():
            unnetted += 1
    return {"nets": nets, "netclasses": ncls, "areas": areas,
            "unnetted": unnetted}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    ap.add_argument("--json", default=None)
    ap.add_argument("--enforce", default=None,
                    help="comma list, e.g. G-COVER,G-INPUT (default: all)")
    ap.add_argument("--dru", default=None,
                    help="a .kicad_dru to grade for predicate vacuity; its "
                         "sibling .kicad_pcb supplies the inventory")
    a = ap.parse_args(argv)

    enforce = a.enforce.split(",") if a.enforce else None
    r = audit(a.root, enforce)
    if a.json:
        Path(a.json).write_text(json.dumps(r, indent=2) + "\n")

    print(f"  coverage: {r['coverage']}")
    for u in r["unparsed"]:
        print(f"  FAIL G-PARSE {u}")
    for f in r["fails"]:
        print(f"  FAIL {f}")

    sc_fails, sc_n = check_self_consistency(
        Path(__file__).resolve().parent.parent / "references")
    print(f"  G-SELFCON: {sc_n} tier(s) graded x {len(EMITTERS)} stroke "
          f"emitter(s) + the published-stroke threshold, against "
          f"{GEN_PATH.name}'s own silk_stroke()")
    for f in sc_fails:
        print(f"  FAIL {f}")

    vc_fails, vs = check_vacuity(a.root, r["gates"])
    r["vacuity"] = vs
    print(f"  G-VACUOUS: {len(vs['bound'])}/{vs['total']} gate(s) declare a "
          f"vacuity condition WITH a fixture that exercises it "
          f"(floor {vs['floor']}); {len(vs['owed'])} OWED")
    # THE OWED GATES ARE NAMED. An adoption ratchet whose remainder is a bare
    # count is how a partial rollout becomes permanent — nobody can see whose
    # blind spot is still unknown.
    for name in vs["owed"]:
        print(f"  OWED G-VACUOUS {name}: no declared vacuity condition")
    for f in vc_fails:
        print(f"  FAIL {f}")

    dru_fails, dru_n = [], 0
    if a.dru:
        dru = Path(a.dru)
        pcb = dru.with_suffix(".kicad_pcb")
        inv = dru_inventory(pcb) if pcb.exists() else {}
        dru_rules = parse_dru(dru.read_text(encoding="utf-8-sig"))
        mem = dru_area_members(pcb, dru_rules) if pcb.exists() else {}
        dru_fails, dru_n = check_dru_vacuity(dru_rules, inv, source=dru.name,
                                             members=mem)
        against = pcb.name if pcb.exists() else \
            "NO board (inventory empty — netclass/area existence UNGRADED)"
        counted = sum(1 for v in mem.values() if v is not None)
        print(f"  G-VACUOUS-DRU: {dru_n}/{len(dru_rules)} predicate(s) graded "
              f"in {dru.name} against {against}; {counted}/{len(dru_rules)} "
              f"member-counted (rest not derivable from geometry alone)")
        for dr in dru_rules:                 # NB not `r` — that is the audit result
            if mem.get(dr["name"]) is not None:
                print(f"    members {dr['name']}: {mem[dr['name']]}")
        for f in dru_fails:
            print(f"  FAIL {f}")

    bad = len(r["fails"]) + len(r["unparsed"]) + len(sc_fails) + \
        len(vc_fails) + len(dru_fails)
    if bad:
        print(f"G-CONTRACT FAIL: {bad} obligation(s) unmet across "
              f"{len(r['gates'])} verdict-printing script(s)")
        return 1
    print(f"G-CONTRACT OK: {len(r['gates'])} verdict-printing script(s) "
          f"meet G-INPUT/G-COVER/G-RED; {sc_n} rule-file pair(s) "
          f"self-consistent; {len(vs['bound'])} fixtured vacuity condition(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
