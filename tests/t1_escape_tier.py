#!/usr/bin/env python3
"""T1: escape feasibility + fab tier gates — escape_check.py and the
policy_audit P-ESC / P-TIER checks (canon P7).

Motivating incident (2026-07-20, commit 6ae4a4c): the clean-room 3S run
selected a 0.5mm-pitch QFN-10 (SY8368) with the fab tier defaulted to
standard; the unmade ADVANCED decision surfaced two stages later as
drill_out_of_range at DRC, and the escape analysis lived only in a chat
report. These gates move that failure to the PARTS stage.

RED-VERIFIED: the known-bad cases below were run against the pre-gate
policy_audit.py (git show 656bab3:...policy_audit.py swapped in): every
P-ESC/P-TIER case failed with "report has no row for P-ESC/P-TIER" —
the gate did not exist, so nothing could block the incident. Restored and
re-run green 2026-07-21.

v2 (Phase F, 2026-07-21): the CONDITIONAL escape-budget model. The
calibration table below is paid-for ground truth in both directions —
xt60-usb-supply-rerun SHIPPED the SY8368 x3 at STANDARD tier with
outward-only escapes (a4ff7ed) while the v2 clean-room STALLED the same
part, and usb-pwr-hub-3s ADR-0008 measured the dense-leaded LM5116 wall.
The v2 known-bad cases were RED-VERIFIED against the pre-v2 escape_check
(git show 656bab3 swap): the conditional-clean cases FAIL there (the model
could only say 'advanced always') and the conditions-mismatch cases fail
with the wrong reason — details per test.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     must_fail, not_contains,
                     must_pass, run, test, tmpdir)

ESC = SCRIPTS / "escape_check.py"
POLICY = SCRIPTS / "policy_audit.py"

QFN_PART = """mpn: SY8368QNC
manufacturer: Silergy
type: buck_converter
package: QFN3x3-10
footprint: power3s:SY8368QNC_QFN-10_3x3mm_P0.5mm
pins: {{1: EN, 2: PG, 3: ILMT, 4: FB, 5: VC, 6: BS, 7: IN, 8: IN, 9: GND, 10: LX}}
verified: "pinout table p.2"
{escape}
"""

TSSOP_PART = """mpn: FAKE-TSSOP16
manufacturer: Example
type: codec
package: TSSOP-16
footprint: lib:TSSOP-16_4.4x5mm_P0.65mm
pins: {{1: A, 2: B, 3: C, 4: D, 5: E, 6: F, 7: G, 8: H, 9: I, 10: J, 11: K, 12: L, 13: M, 14: N, 15: O, 16: P}}
verified: "pinout figure 1"
{escape}
"""


def scratch_project(parts, fab_tier="jlc_2layer_default"):
    """A minimal project tree: 02_parts entries + a nets.yaml fab_tier."""
    d = tmpdir("esc_")
    for name, text in parts.items():
        pd = d / "02_parts" / name
        pd.mkdir(parents=True)
        (pd / "part.yaml").write_text(text)
    r = d / "03_src" / "rules"
    r.mkdir(parents=True)
    (r / "nets.yaml").write_text(f"fab_tier: {fab_tier}\nclasses: {{}}\n")
    return d


def audit_rows(d):
    """Run policy_audit (no board, --skip-drc) and return {id: (grade, detail)}."""
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    rows = {}
    for m in re.finditer(r"^\| (\S+) \| (\S+) \| (.*) \|$", md, re.M):
        rows[m.group(1)] = (m.group(2), m.group(3))
    return rows


def placement_audit_rows(d):
    """Run the post-placement/pre-route subset and return its rows + result."""
    result = run([KPY, POLICY, d, "--skip-drc", "--phase", "placement"])
    md = (d / "06_build" / "placement_policy_audit.md").read_text()
    rows = {}
    for m in re.finditer(r"^\| (\S+) \| (\S+) \| (.*) \|$", md, re.M):
        rows[m.group(1)] = (m.group(2), m.group(3))
    return result, rows


LM5116_PART = """mpn: LM5116MHX
manufacturer: Texas Instruments
type: buck_controller
package: HTSSOP-20-EP
footprint: lib:HTSSOP-20-1EP_4.4x6.5mm_P0.65mm
pins: {{1: VIN, 2: UVLO, 3: RT, 4: EN, 5: SS, 6: RAMP, 7: AGND, 8: FB, 9: COMP, 10: VOUT, 11: DEMB, 12: CSG, 13: CS, 14: LG, 15: PGND, 16: VCC, 17: VCCX, 18: BST, 19: HG, 20: SW, 21: EP}}
verified: "pinout figure p.3"
{escape}
"""


# ------------------------------------------------------------ clean cases
@test("escape_check calibration matches every shipped ground truth")
def t_calibration():
    # each of these tiers was PAID for: SY8368/LM5145 shipped or stalled at
    # exactly these verdicts. If the math drifts from history, the math is wrong.
    for style, pitch, want in (("qfn", 0.5, "jlc_4layer_advanced"),
                               ("qfn", 0.45, "jlc_4layer_advanced"),
                               ("qfn", 0.65, "jlc_4layer_standard"),
                               ("leaded", 0.65, "jlc_2layer_default"),
                               ("leaded", 0.5, "jlc_2layer_default")):
        r = must_pass(run([KPY, ESC, "--style", style, "--pitch", str(pitch)]),
                      f"escape_check {style}@{pitch}")
        contains(r.out, f"tier_required: {want}", f"{style}@{pitch}")


@test("through-hole headers are an outward-escape style, not a checker crash")
def t_through_hole_style():
    r = must_pass(run([KPY, ESC, "--style", "through_hole", "--pitch", "1.27"]),
                  "through-hole header escape")
    contains(r.out, "tier_required: jlc_2layer_default", "header tier")


@test("an unknown dossier escape style is a classified failure, not a traceback",
      kind="known_bad")
def t_kb_unknown_style_classified():
    part = TSSOP_PART.format(
        escape="escape: {style: teleport, pitch: 0.65, "
               "tier_required: jlc_2layer_default, checked: escape_check}")
    d = scratch_project({"FAKE-TSSOP16": part})
    p = d / "02_parts/FAKE-TSSOP16/part.yaml"
    r = must_fail(run([KPY, ESC, p]), "unknown escape style",
                  "unknown escape style 'teleport'")
    not_contains(r.out, "Traceback", "classified style failure")


@test("P-ESC + P-TIER PASS a part whose block agrees and fits the tier")
def t_clean_pass():
    esc = ("escape: {style: leaded, pitch: 0.65, "
           "tier_required: jlc_2layer_default, checked: escape_check}")
    d = scratch_project({"FAKE-TSSOP16": TSSOP_PART.format(escape=esc)})
    rows = audit_rows(d)
    check(rows.get("P-ESC", ("",))[0] == "PASS", f"P-ESC not PASS: {rows.get('P-ESC')}")
    check(rows.get("P-TIER", ("",))[0] == "PASS", f"P-TIER not PASS: {rows.get('P-TIER')}")


@test("v2 CALIBRATION TABLE: conditional verdicts reproduce every paid-for "
      "outcome (SY8368 both ways, LM5145, LM5116, IP6559, plain leaded)")
def t_calibration_v2():
    """Each row was PAID for (see module docstring). The model must
    reproduce ALL of them or the model is wrong. RED-VERIFIED against the
    pre-v2 escape_check (git show 656bab3 swap, 2026-07-21): rows 1 and 3
    fail there — no --escapes-worst-side flag, no CONDITIONAL verdict."""
    # 1. SY8368 shipped config: qfn 0.45, ~6 escapes one side, 10 pins ->
    #    standard CONDITIONAL on outward-only-local (xt60-usb-supply-rerun
    #    shipped x3); unconditional tier stays advanced.
    r = must_pass(run([KPY, ESC, "--style", "qfn", "--pitch", "0.45",
                       "--escapes-worst-side", "6", "--pins", "10"]),
                  "SY8368 shipped config")
    contains(r.out, "jlc_4layer_standard      CONDITIONAL on outward-only-local",
             "SY8368: standard is conditional")
    contains(r.out, "tier_required: jlc_4layer_advanced",
             "SY8368: unconditional stays advanced")
    # 2. the same part with NO declared escape budget = the v2 clean-room
    #    stall configuration -> UNCONDITIONAL advanced, standard INFEASIBLE
    r = must_pass(run([KPY, ESC, "--style", "qfn", "--pitch", "0.45"]),
                  "SY8368 stranded config")
    contains(r.out, "jlc_4layer_standard      INFEASIBLE",
             "SY8368 stranded: no conditional rescue without the budget")
    contains(r.out, "tier_required: jlc_4layer_advanced", "stranded verdict")
    # 3. LM5145: qfn 0.5, 20 pins on 4 sides -> advanced UNCONDITIONAL
    #    (3 shipped boards) — the outward-only rescue must NOT apply even
    #    with a small per-side count declared.
    r = must_pass(run([KPY, ESC, "--style", "qfn", "--pitch", "0.5",
                       "--escapes-worst-side", "5", "--pins", "20"]),
                  "LM5145 config")
    contains(r.out, "jlc_4layer_standard      INFEASIBLE",
             "LM5145: no conditional standard for a 4-sided VQFN-20")
    contains(r.out, "tier_required: jlc_4layer_advanced", "LM5145 verdict")
    # 4. LM5116: leaded 0.65, 8 escapes worst side -> standard CONDITIONAL
    #    on escape-corridor (ADR-0008: 0.65 - 0.3 drill = 0.35 < 0.5
    #    hole-to-hole); advanced (0.65 - 0.15 = 0.5 >= 0.25) unconditional.
    r = must_pass(run([KPY, ESC, "--style", "leaded", "--pitch", "0.65",
                       "--escapes-worst-side", "8"]), "LM5116 config")
    contains(r.out, "jlc_4layer_standard      CONDITIONAL on escape-corridor",
             "LM5116: standard needs the reserved corridor")
    contains(r.out, "tier_required: jlc_4layer_advanced",
             "LM5116: unconditional tier is advanced")
    # 5. IP6559-C: qfn-48 0.5 7x7 EP -> advanced OK (v4 routed + released)
    r = must_pass(run([KPY, ESC, "--style", "qfn", "--pitch", "0.5",
                       "--pins", "48"]), "IP6559 config")
    contains(r.out, "jlc_4layer_advanced      ok", "IP6559: advanced feasible")
    contains(r.out, "tier_required: jlc_4layer_advanced", "IP6559 verdict")
    # 6. plain leaded 0.65 with < 6 escapes/side -> cheapest tier,
    #    unconditional (many shipped boards)
    r = must_pass(run([KPY, ESC, "--style", "leaded", "--pitch", "0.65",
                       "--escapes-worst-side", "5"]), "plain leaded config")
    contains(r.out, "jlc_2layer_default       ok", "plain leaded: cheapest ok")
    contains(r.out, "tier_required: jlc_2layer_default", "plain leaded verdict")


@test("P-ESC + P-TIER PASS the SY8368 SHIPPED configuration: conditional "
      "standard tier with the conditions RECORDED")
def t_conditional_earned_pass():
    """The xt60-usb-supply-rerun ground truth (a4ff7ed): the part carries
    escapes_worst_side + the outward-only-local condition, the board
    declares standard tier — this must PASS, or the checker is
    over-conservative vs a board that shipped three times. RED-VERIFIED:
    pre-v2 escape_check fails this part ('math says jlc_4layer_advanced'),
    which is exactly the over-conservatism a4ff7ed queued for Phase F."""
    esc = ("escape: {style: qfn, pitch: 0.5, escapes_worst_side: 6, "
           "tier_required: jlc_4layer_standard, "
           "conditions: [outward-only-local], checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    check(rows.get("P-ESC", ("",))[0] == "PASS",
          f"P-ESC not PASS: {rows.get('P-ESC')}")
    check(rows.get("P-TIER", ("",))[0] == "PASS",
          f"P-TIER not PASS: {rows.get('P-TIER')}")


@test("P-ESC PASSES the dense-leaded LM5116 at standard tier when the "
      "escape-corridor condition is recorded")
def t_corridor_earned_pass():
    """ADR-0008 (usb-pwr-hub-3s, 2026-07-21): 8 escapes on one 0.65mm side
    — standard tier is feasible only with a reserved escape corridor at
    placement (floorplan `escape_corridors:`). Recording the condition is
    what P-ESC accepts."""
    esc = ("escape: {style: leaded, pitch: 0.65, escapes_worst_side: 8, "
           "tier_required: jlc_4layer_standard, "
           "conditions: [escape-corridor], checked: escape_check}")
    d = scratch_project({"LM5116MHX": LM5116_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    check(rows.get("P-ESC", ("",))[0] == "PASS",
          f"P-ESC not PASS: {rows.get('P-ESC')}")


# -------------------------------------------------------- known-bad cases
@test("P-ESC FAILS a conditional tier whose conditions are NOT recorded "
      "in the part.yaml", kind="known_bad")
def t_kb_conditional_unearned():
    """The heart of the v2 contract: a conditional verdict must be EARNED.
    A part claiming the SY8368's conditional standard tier without
    recording the conditions is the copied-waiver disease — the next board
    inherits the tier but not the discipline (the exact mechanism of the
    v2 clean-room stall: same part, stranded passives). RED-VERIFIED: the
    'conditions:' assertion below fails against pre-v2 escape_check
    (which rejects for the unrelated reason 'math says advanced')."""
    esc = ("escape: {style: qfn, pitch: 0.5, escapes_worst_side: 6, "
           "tier_required: jlc_4layer_standard, checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "CONDITIONAL", "P-ESC names the conditional verdict")
    contains(det, "conditions:", "P-ESC says what must be recorded")


@test("P-ESC FAILS recorded conditions that do not match the math",
      kind="known_bad")
def t_kb_conditions_mismatch():
    """A QFN outward-only part carrying the LEADED corridor condition is a
    copied block — the conditions must be the ones this geometry needs."""
    esc = ("escape: {style: qfn, pitch: 0.5, escapes_worst_side: 6, "
           "tier_required: jlc_4layer_standard, "
           "conditions: [escape-corridor], checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "do not match", "P-ESC names the mismatch")


@test("P-ESC FAILS stale conditions on an unconditionally-feasible tier",
      kind="known_bad")
def t_kb_conditions_stale():
    """Conditions riding on a tier that needs none are a copied block."""
    esc = ("escape: {style: leaded, pitch: 0.65, escapes_worst_side: 5, "
           "tier_required: jlc_2layer_default, "
           "conditions: [escape-corridor], checked: escape_check}")
    d = scratch_project({"FAKE-TSSOP16": TSSOP_PART.format(escape=esc)})
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "UNCONDITIONAL", "P-ESC names the stale conditions")


@test("P-ESC FAILS an unknown condition token (no invented vocabulary)",
      kind="known_bad")
def t_kb_condition_unknown():
    esc = ("escape: {style: qfn, pitch: 0.5, escapes_worst_side: 6, "
           "tier_required: jlc_4layer_standard, "
           "conditions: [trust-me], checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "unknown escape condition", "P-ESC names the token")


@test("P-LAYOUT FAILS an IC part.yaml with no layout: block", kind="known_bad")
def t_kb_layout_missing():
    """The usb-hub-3s-v2 TPS25740A miss (2026-07-22): pinout + escape verified,
    but the datasheet LAYOUT section never read, so no layout: block and the
    floorplan fought the part. P-LAYOUT must FAIL an in-scope IC that has none.
    RED-VERIFIED: before P-LAYOUT existed, the report had no P-LAYOUT row at
    all — the gate could not fail because it did not exist."""
    esc = ("escape: {style: qfn, pitch: 0.5, "
           "tier_required: jlc_4layer_advanced, checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_advanced")
    rows = audit_rows(d)
    g, det = rows.get("P-LAYOUT", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-LAYOUT (got {g})")
    contains(det, "SY8368QNC", "P-LAYOUT names the part missing the block")


@test("P-LAYOUT PASSes an IC that carries a layout: block with source + budget")
def t_layout_present():
    esc = ("escape: {style: qfn, pitch: 0.5, "
           "tier_required: jlc_4layer_advanced, checked: escape_check}")
    part = (QFN_PART.format(escape=esc)
            + '\nlayout:\n'
              '  source: "datasheet Sec.11 Layout + EVM reference design"\n'
              '  keep_short:\n'
              '    - {net: LX, max_span_mm: 5, why: "switch-node hot loop"}\n')
    d = scratch_project({"SY8368QNC": part}, fab_tier="jlc_4layer_advanced")
    rows = audit_rows(d)
    g, _ = rows.get("P-LAYOUT", ("MISSING", ""))
    check(g == "PASS", f"P-LAYOUT not PASS with a valid layout block (got {g})")


LEDGER_PATH = SCRIPTS.parent / "references" / "proven-parts.yaml"
_XREF = re.compile(r"(?:see|use)\s+`([a-z][a-z0-9-]*)`")


def ledger_findings(ledger):
    """Every problem in a proven-parts ledger, as a LIST — so the same
    function can be pointed at a deliberately corrupted copy and required to
    produce findings. A validator that only ever runs on the good file proves
    nothing about whether it can bite (tests/README, the whole point).

    Returns (findings, candidates_examined) so the caller can assert a
    denominator too: a validator that examined nothing is not a pass.
    """
    sys.path.insert(0, str(SCRIPTS))
    import escape_check as ec
    tiers = ec.load_tiers()
    statuses = {"shipped", "designed-in", "incident", "unresolved"}
    fns = set(ledger.get("functions") or {})
    out, n = [], 0
    for fn, body in (ledger.get("functions") or {}).items():
        for c in body.get("candidates") or []:
            text = " ".join(str(v) for v in c.values())
            # a cross-reference must RESOLVE: pointing the next board at a
            # function that does not exist sends it nowhere, and that is the
            # exact failure this ledger exists to prevent.
            for ref in _XREF.findall(text):
                if ref not in fns:
                    out.append(f"{fn}/{c.get('mpn')}: dangling cross-reference "
                               f"`{ref}` — no such function entry")
            if "projects/" in text:
                out.append(f"{fn}/{c.get('mpn')}: names a projects/ path "
                           f"(C-ISO) — provenance names BOARDS, never paths")
            if set(c) == {"mpn", "note"}:      # cross-reference stub
                continue
            if c.get("status") not in statuses:
                out.append(f"{fn}/{c.get('mpn')}: bad status "
                           f"{c.get('status')!r}")
            if not c.get("provenance"):
                out.append(f"{fn}/{c.get('mpn')}: no provenance")
            esc = c.get("escape")
            if esc:
                if esc.get("style") not in (ec.OUTWARD_STYLES | ec.RING_STYLES
                                            | {"bga"}):
                    out.append(f"{fn}/{c['mpn']}: bad style "
                               f"{esc.get('style')!r}")
                if esc.get("tier_required") not in tiers:
                    out.append(f"{fn}/{c['mpn']}: bad tier "
                               f"{esc.get('tier_required')!r}")
                bad = set(esc.get("conditions") or []) - ec.KNOWN_CONDITIONS
                if bad:
                    out.append(f"{fn}/{c['mpn']}: unknown conditions {bad}")
            n += 1
    return out, n


@test("proven-parts ledger parses, every escape block is schema-valid, and "
      "every cross-reference RESOLVES")
def t_proven_parts_schema():
    """The v4 harvest added 9 function entries and the pluto-rx2-8way harvest
    (2026-07-28) added 3 more — the ledger must parse, every candidate's
    escape block must use the checker's own vocabulary (style/tier/condition
    names), and every `` see `x` `` / `` use `x` `` must name a function that
    exists, or the next D-ESC consult starts from a corrupt ledger or is sent
    to a row that is not there.

    The cross-reference rule is what makes a DISQUALIFICATION usable: the
    2026-07-28 harvest disqualified `analog-ldo-quiet-3v3` behind a >6.5 V
    clamp and pointed at `wide-vin-ldo-3v3`. A pointer to a row that does not
    exist is worse than no pointer, because it reads as an answer.
    """
    import yaml as _y
    findings, n = ledger_findings(_y.safe_load(LEDGER_PATH.read_text()))
    check(not findings, f"proven-parts ledger: {len(findings)} finding(s) over "
                        f"{n} candidates: {findings[:6]}")
    check(n >= 17, f"ledger looks truncated: only {n} candidates")


@test("the proven-parts validator BITES: each way of corrupting a ledger "
      "entry produces its own finding", kind="known_bad")
def t_proven_parts_validator_has_teeth():
    """Until 2026-07-28 the ledger's only check was a run of `check()` calls
    inside a test that had only ever seen a GOOD file. A validator whose
    failure path has never executed is the `jlc_twin` exit-0 shape: it
    reports success and nothing has proved it could report anything else.

    Each case below is the SHIPPED ledger broken in exactly ONE way, so the
    finding is attributable to that break and not to a malformed document.
    """
    import copy
    import yaml as _y
    good = _y.safe_load(LEDGER_PATH.read_text())
    base, n = ledger_findings(good)
    check(not base, f"the fixture base is not clean: {base[:3]}")
    fn = "wide-vin-ldo-3v3"
    check(fn in good["functions"], f"{fn} missing — the harvest did not land")

    def broken(mutate):
        g = copy.deepcopy(good)
        mutate(g["functions"][fn]["candidates"][0])
        f, _ = ledger_findings(g)
        return f

    cases = [
        ("bad status", lambda c: c.__setitem__("status", "probably-fine"),
         "bad status"),
        ("no provenance", lambda c: c.pop("provenance"), "no provenance"),
        ("bad tier", lambda c: c["escape"].__setitem__("tier_required",
                                                       "jlc_9layer_magic"),
         "bad tier"),
        ("bad style", lambda c: c["escape"].__setitem__("style", "wishful"),
         "bad style"),
        ("dangling xref", lambda c: c.__setitem__(
            "provenance", "see `ldo-that-does-not-exist`"),
         "dangling cross-reference"),
        ("projects/ path", lambda c: c.__setitem__(
            "provenance", "projects/pluto-rx2-8way/02_parts/MCP1755S-3302E-DB"),
         "projects/ path"),
    ]
    for name, mutate, expect in cases:
        f = broken(mutate)
        check(f, f"{name}: the validator found NOTHING — it cannot bite")
        check(any(expect in x for x in f),
              f"{name}: no finding mentions {expect!r}; got {f}")


@test("P-TIER FAILS the incident: 0.5mm QFN vs a standard-tier board",
      kind="known_bad")
def t_tier_bites():
    # the exact clean-room 3S configuration, now blocked at the parts stage
    esc = ("escape: {style: qfn, pitch: 0.5, "
           "tier_required: jlc_4layer_advanced, checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    g, det = rows.get("P-TIER", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-TIER (got {g})")
    contains(det, "jlc_4layer_advanced", "P-TIER detail")
    contains(det, "ADR", "P-TIER remediation must name the D-TIER ADR")


@test("P-ESC FAILS a tampered/copied block that contradicts the math",
      kind="known_bad")
def t_esc_tampered():
    # block claims the QFN escapes at standard — the copied-waiver disease
    esc = ("escape: {style: qfn, pitch: 0.5, "
           "tier_required: jlc_4layer_standard, checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_standard")
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "math", "P-ESC detail names the recomputation mismatch")


@test("P-ESC FAILS a declared style that contradicts the footprint text",
      kind="known_bad")
def t_esc_style_lie():
    # 'leaded' declared for a footprint whose own name says QFN P0.5mm
    esc = ("escape: {style: leaded, pitch: 0.65, "
           "tier_required: jlc_2layer_default, checked: escape_check}")
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape=esc)})
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "contradicts", "P-ESC detail")


@test("P-ESC FAILS a multi-pin part with no escape block at all",
      kind="known_bad")
def t_esc_missing():
    d = scratch_project({"SY8368QNC": QFN_PART.format(escape="")})
    rows = audit_rows(d)
    g, det = rows.get("P-ESC", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-ESC (got {g})")
    contains(det, "NO escape block", "P-ESC detail")


@test("P-TIER FAILS an unknown fab_tier name (typo cannot pass as a tier)",
      kind="known_bad")
def t_tier_typo():
    esc = ("escape: {style: leaded, pitch: 0.65, "
           "tier_required: jlc_2layer_default, checked: escape_check}")
    d = scratch_project({"FAKE-TSSOP16": TSSOP_PART.format(escape=esc)},
                        fab_tier="jlc_4layer_advnaced")
    rows = audit_rows(d)
    g, det = rows.get("P-TIER", ("MISSING", ""))
    check(g == "FAIL", f"report has no FAIL row for P-TIER (got {g})")
    contains(det, "not a tier", "P-TIER detail")


@test("escape_check refuses a package no tier can escape (0.5mm BGA)",
      kind="known_bad")
def t_infeasible_everywhere():
    r = must_fail(run([KPY, ESC, "--style", "bga", "--pitch", "0.5"]),
                  "escape_check on an unescapable package", "NONE")


# ============================== G-COVER zero denominator (2026-07-27) =======
@test("escape_check FAILS when it is handed NO part.yaml at all",
      kind="known_bad")
def t_esc_zero_parts():
    """`escape_check.py` with no arguments printed NOTHING and exited 0. A
    shell glob that matched nothing — a renamed 02_parts directory, the wrong
    cwd, a stage that has not run — lands exactly here and reads as a clean
    escape audit over every part on the board.
    RED-VERIFIED against pre-fix code (git show 5054b07:...escape_check.py):
    it exits 0 with empty output, so must_fail goes RED."""
    r = must_fail(run([KPY, ESC]), "escape_check with no parts",
                  "0/0 parts graded")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")


@test("escape_check FAILS a part.yaml path that does not exist",
      kind="known_bad")
def t_esc_missing_path():
    """A path that cannot be read is UNGRADED, and must not fall out of the
    denominator: pre-fix, `check_part` would raise, but a caller passing a
    mixed list wants the MISSING one named, not a traceback."""
    r = must_fail(run([KPY, ESC, "/nonexistent/part.yaml"]),
                  "escape_check on a missing path", "no such part.yaml")
    contains(r.out, "0/1", "counts the unreadable part in the denominator")


@test("escape_check reports its denominator and names the tier table")
def t_esc_reports_coverage():
    """G-COVER/G-INPUT: the verdict depends entirely on the tier table, and
    printed neither it nor how many parts were graded."""
    d = tmpdir("escov_")
    p = d / "part.yaml"
    p.write_text("mpn: TWOPIN\npins:\n  1: A\n  2: B\n")
    r = must_pass(run([KPY, ESC, p]), "escape_check on a 2-pin part")
    contains(r.out, "1/1 part.yaml graded", "carries an N/M denominator")
    contains(r.out, "input: tiers", "names the tier table it graded against")


# ============================ S-VER READS THE KEY (2026-07-28) ==============
# policy_audit's S-VER grepped the RAW TEXT for the first literal `verified:`
# and read 300 characters from there. `part.yaml` is a YAML document that
# TALKS ABOUT ITSELF — `gotchas:` entries say "see verified:", a `sha256:`
# value says "no PDF is vendored; see verified:", comments say "# Footprint
# match verified: ..." — so any earlier mention SHADOWS the real key, and the
# 300-char window then bleeds PAST the value into unrelated keys.
#
# MEASURED over all 557 fleet part.yaml: 15 files where the grep and the
# parsed key disagree (4 shadowed by a `#` comment, 11 by an earlier quoted
# string). And the window half is the same class as the E-TOPO
# `fuse rated 3401 A` incident: on smc0985-cooksense/MF-MSMF200L-2 the real
# citation is `2/3-pad commodity; polarity/pad-1 asserted in board generator
# + audit I9` — no figure, no page — and S-VER PASSED it because the window
# ran three keys further into `sourcing:` and matched `p 4` out of the PPTC's
# trip current, `Itrip 4A`.
SHADOWED_PART = '''\
mpn: SHADOWED-8
manufacturer: Example
type: logic
package: SOIC-8
footprint: lib:SOIC-8_3.9x4.9mm_P1.27mm
# Footprint match verified: figure 3 of the KiCad library drawing
pins: {1: A, 2: B, 3: C, 4: D, 5: E, 6: F, 7: G, 8: H}
verified: "pin map taken from a colleague's schematic, not from the datasheet"
'''

WINDOW_PART = '''\
mpn: WINDOW-8
manufacturer: Example
type: fuse
package: SOIC-8
footprint: lib:SOIC-8_3.9x4.9mm_P1.27mm
pins: {1: A, 2: B, 3: C, 4: D, 5: E, 6: F, 7: G, 8: H}
verified: "2/3-pad commodity; polarity asserted in the board generator"
sourcing:
  lcsc: C89650
  note: "6286 stock. F1: Ihold 2A, Itrip 4A, 16V (ADR-0001)."
'''

GOOD_PART = '''\
mpn: GOOD-8
manufacturer: Example
type: logic
package: SOIC-8
footprint: lib:SOIC-8_3.9x4.9mm_P1.27mm
pins: {1: A, 2: B, 3: C, 4: D, 5: E, 6: F, 7: G, 8: H}
verified: "pin map read from figure 2, datasheet page 3 of 14"
'''


@test("S-VER FAILS a weak citation that an earlier `verified:` in a COMMENT "
      "was hiding", kind="known_bad")
def t_sver_comment_shadow():
    """The part's real citation admits it came from a colleague's schematic —
    no figure, no page. A `# Footprint match verified: figure 3 ...` comment
    sits above it, and the grep found that first and graded S-VER PASS.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    policy_audit.py swapped back in this fails with `S-VER on a
    comment-shadowed citation: got 'PASS', want 'FAIL'`. Restored, FAIL.
    """
    d = scratch_project({"SHADOWED-8": SHADOWED_PART})
    rows = audit_rows(d)
    check(rows["S-VER"][0] == "FAIL",
          f"S-VER on a comment-shadowed citation: got {rows['S-VER'][0]!r}, "
          f"want 'FAIL' — detail was {rows['S-VER'][1]!r}")
    contains(rows["S-VER"][1], "SHADOWED-8", "names the part")
    # the ADJACENT property, re-measured every run: the same tree with the ONE
    # thing fixed — a real citation — must PASS, or the gate proves nothing.
    ok = scratch_project({"GOOD-8": GOOD_PART})
    check(audit_rows(ok)["S-VER"][0] == "PASS", "a real citation still passes")


@test("S-VER FAILS a weak citation the 300-char WINDOW rescued from a later "
      "key — `Itrip 4A` is not `page 4`", kind="known_bad")
def t_sver_window_bleed():
    """The real smc0985-cooksense/MF-MSMF200L-2 shape, reproduced. The
    `verified:` value carries no figure and no page; the old window read on
    into `sourcing.note` and matched `p 4` inside the PPTC's trip current
    `Itrip 4A`. Same class as E-TOPO's `fuse rated 3401 A`, where an
    unanchored pattern read a rating out of a part number.

    RED-VERIFIED 2026-07-28 (git-swap): pre-fix `S-VER on a window-bleed
    citation: got 'PASS', want 'FAIL'`. It is also the measured fleet delta —
    this fix turns up 2 previously-hidden weak citations (the same part on
    smc0985-cooksense and archived cook-hub) and clears 0 false alarms.
    """
    d = scratch_project({"WINDOW-8": WINDOW_PART})
    rows = audit_rows(d)
    check(rows["S-VER"][0] == "FAIL",
          f"S-VER on a window-bleed citation: got {rows['S-VER'][0]!r}, "
          f"want 'FAIL' — detail was {rows['S-VER'][1]!r}")
    contains(rows["S-VER"][1], "WINDOW-8", "names the part")


# ============= P-ADJ-UNREACHED: a budget nothing evaluates (2026-07-28) =====
# `pts = netpads.get(net) or []; if len(pts) < 2: continue` — a declared
# keep_short budget whose net does not name a 2+-pad net on this board was
# graded by NOTHING, and the `continue` said so to no one. P-ADJ then reported
# PASS over a budget it never looked up. The usual cause is a net name that
# does not exist here (renamed, or copied out of the datasheet's reference
# design), which is exactly when a silent pass misleads most.
#
# MEASURED fleet-wide 2026-07-28: 61 of 119 declared keep_short budgets — 51%
# — resolved to nothing. 32 of 46 on crow-recorder-central-v2, 25 of 37 on
# smc0985-cooksense, and all 4 on crow-mic-pod-v2, whose `net:` fields are
# PROSE ("V+ decoupler (pin 8)") rather than net names at all.
#
# IT IS ITS OWN ROW, deliberately. Both boards carrying budgets already hold a
# P-ADJ waiver, and each names THREE measured span violations as its evidence.
# Reporting "never graded" under the same ID would let those waivers absorb 57
# findings of a different class in silence — canon M4's inherited-defect
# pattern, which is the failure this gate exists to stop.
FX_PART = """mpn: FXPART
manufacturer: Example
type: buck_converter
package: SOT-23-6
footprint: t:SOT-23-6
pins: {1: SW, 2: GND, 3: VIN, 4: FB, 5: EN, 6: BST}
verified: "pin map read from figure 1, page 2"
escape: {style: leaded, pitch: 0.95, tier_required: jlc_2layer_default, checked: escape_check}
layout:
  keep_short:
%s
%s
"""
KS_REAL = ('    - {net: SW_NODE, max_span_mm: 6, why: "switch-node loop area '
           'sets EMI; datasheet Layout sec 11"}')
KS_GHOST = ('    - {net: NOT_ON_THIS_BOARD, max_span_mm: 3, why: "net name '
            'copied out of the datasheet reference design"}')
KS_LONE = ('    - {net: LONE, max_span_mm: 3, why: "resolves to a single-pad '
           'net on this board"}')
#: a budget on a net that HAS two pads, neither of them on the declaring part —
#: the shape a series element makes (RP2040 `USB_DP` is `USB_DP_MCU` after the
#: 27R; the SMA jack's `SW1_ANT` is between the DC block and the switch).
KS_NOT_MINE = ('    - {net: PARTNERS, max_span_mm: 3, why: "a net this part '
               'does not touch — 2 pads, none of them mine"}')


def _fp(ref, x, y, pads, fpid="t:R_0402"):
    ps = "\n".join(
        f'\t\t(pad "{i}" smd roundrect (at 0 {j * 1.0} 0) (size 0.9 0.9)\n'
        f'\t\t\t(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25)\n'
        f'\t\t\t(net {n} "{nm}"))' for j, (i, n, nm) in enumerate(pads))
    return (f'\t(footprint "{fpid}"\n\t\t(layer "F.Cu")\n\t\t(at {x} {y} 0)\n'
            f'\t\t(property "Reference" "{ref}" (at 0 -2 0) (layer "F.SilkS")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
            f'\t\t(property "Value" "V" (at 0 2 0) (layer "F.Fab")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
            f'\t\t(attr smd)\n{ps}\n\t)')


def padj_project(keep_short, sw_span=2.0, bulk_at=None, adjacency=()):
    """A scratch project WITH a board.

    `U1` IS THE DECLARING PART — its footprint id matches FXPART's `footprint:`
    (`t:SOT-23-6`), which is how P-ADJ resolves the ANCHOR PIN of a keep_short
    budget. It used to be `t:R_0402` like everything else, which no longer
    resolves and would make every budget UNREACHED.

    `SW_NODE` runs U1.1 -> C1.1 at `sw_span` mm; `bulk_at` optionally adds a
    THIRD pad on the same net that far away (the correctly-placed bulk cap
    whose presence used to make the budget score worse); `PARTNERS` has two
    pads and neither is U1's; `LONE` has one; `NOT_ON_THIS_BOARD` none.
    """
    d = scratch_project({"FXPART": FX_PART % ("\n".join(keep_short),
                                             "\n".join(adjacency) and
                                             "  adjacency:\n"
                                             + "\n".join(adjacency))})
    (d / "04_kicad").mkdir(parents=True, exist_ok=True)
    (d / "04_kicad" / "fx.kicad_pcb").write_text(
        '(kicad_pcb\n\t(version 20260206)\n\t(generator "pcbnew")\n'
        '\t(generator_version "10.0")\n\t(general (thickness 1.6))\n'
        '\t(paper "A4")\n\t(layers\n\t\t(0 "F.Cu" signal)\n'
        '\t\t(2 "B.Cu" signal)\n\t\t(11 "F.Paste" user)\n'
        '\t\t(13 "F.SilkS" user "F.Silkscreen")\n\t\t(15 "F.Mask" user)\n'
        '\t\t(25 "Edge.Cuts" user)\n\t\t(31 "F.CrtYd" user "F.Courtyard")\n'
        '\t\t(35 "F.Fab" user)\n\t)\n\t(setup (pad_to_mask_clearance 0))\n'
        '\t(net 0 "")\n\t(net 1 "SW_NODE")\n\t(net 2 "GND")\n\t(net 3 "LONE")\n'
        '\t(net 4 "PARTNERS")\n'
        + _fp("U1", 100, 100, [("1", 1, "SW_NODE"), ("2", 2, "GND")],
              fpid="t:SOT-23-6") + "\n"
        + _fp("C1", 100 + sw_span, 100,
              [("1", 1, "SW_NODE"), ("2", 2, "GND")]) + "\n"
        + (_fp("C_BULK", 100 + bulk_at, 100,
               [("1", 1, "SW_NODE"), ("2", 2, "GND")]) + "\n"
           if bulk_at else "")
        + _fp("D1", 120, 110, [("1", 4, "PARTNERS")]) + "\n"
        + _fp("D2", 122, 110, [("1", 4, "PARTNERS")]) + "\n"
        + _fp("TP1", 150, 100, [("1", 3, "LONE")]) + "\n)\n")
    return d


@test("P-ADJ-UNREACHED FAILS a keep_short budget whose net has fewer than 2 "
      "pads — declared, and graded by NOTHING", kind="known_bad")
def t_padj_unreached_is_reported():
    """The two shapes, in one board: a net that does not exist here at all
    (`NOT_ON_THIS_BOARD`, 0 pads — the reference-design copy) and one that
    resolves to a single pad (`LONE`). Neither can be measured, and neither
    was reported. The finding must NAME the net, since the fix is almost
    always the name itself.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    policy_audit.py swapped back in, `06_build/policy_audit.md` has NO
    `P-ADJ-UNREACHED` row at all and P-ADJ reads
    `PASS | board honours every layout keep_short net-span budget` — over
    three budgets of which it evaluated one. This test fails there with
    `report has no P-ADJ-UNREACHED row`.
    """
    d = padj_project([KS_REAL, KS_GHOST, KS_LONE])
    rows = audit_rows(d)
    check("P-ADJ-UNREACHED" in rows, f"report has no P-ADJ-UNREACHED row: "
                                     f"{sorted(rows)}")
    eq(rows["P-ADJ-UNREACHED"][0], "FAIL", "P-ADJ-UNREACHED grade")
    contains(rows["P-ADJ-UNREACHED"][1], "NOT_ON_THIS_BOARD",
             "names the net that does not exist here")
    contains(rows["P-ADJ-UNREACHED"][1], "LONE", "names the single-pad net")
    contains(rows["P-ADJ-UNREACHED"][1], "2/3", "carries the N/M denominator")
    # the SPAN check is unaffected and still passes on its own terms
    eq(rows["P-ADJ"][0], "PASS", "P-ADJ span grade")
    contains(rows["P-ADJ"][1], "1/3 declared budgets graded",
             "P-ADJ states how many budgets it actually measured")


@test("P-ADJ-UNREACHED PASSES when every budget resolves, and P-ADJ still "
      "FAILS an exceeded span — the two are independent")
def t_padj_unreached_adjacent_property():
    """The adjacent-property red-verify, re-measured on every run: a gate that
    fired on everything would prove nothing. With only the resolvable budget
    declared, P-ADJ-UNREACHED PASSES; widen the same board's SW_NODE span past
    its budget and P-ADJ FAILS while P-ADJ-UNREACHED stays PASS. Splitting the
    row is only worth anything if the two verdicts can disagree."""
    ok = padj_project([KS_REAL])
    rows = audit_rows(ok)
    eq(rows["P-ADJ-UNREACHED"][0], "PASS", "all budgets reached")
    contains(rows["P-ADJ-UNREACHED"][1], "1/1", "denominator on the pass side")
    eq(rows["P-ADJ"][0], "PASS", "span within budget")

    over = padj_project([KS_REAL], sw_span=25.0)   # 25mm against a 6mm budget
    r2 = audit_rows(over)
    eq(r2["P-ADJ"][0], "FAIL", "span over budget")
    contains(r2["P-ADJ"][1], "SW_NODE", "names the over-budget net")
    eq(r2["P-ADJ-UNREACHED"][0], "PASS",
       "a span violation is not an unreached budget")


@test("placement policy phase runs P-ADJ before routing, rejects an exceeded "
      "budget, and cannot clobber the full release report", kind="known_bad")
def t_padj_placement_phase_is_a_real_early_gate():
    d = padj_project([KS_REAL], sw_span=25.0)
    full = d / "06_build" / "policy_audit.md"
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text("full-release-report-sentinel\n")
    result, rows = placement_audit_rows(d)
    must_fail(result, "over-budget placement phase", "FAIL P-ADJ")
    eq(rows["P-ADJ"][0], "FAIL", "early P-ADJ verdict")
    rows.pop("ID", None)  # Markdown table header, matched by the tiny parser.
    eq(set(rows), {"P-LAYOUT", "P-PREC", "P-ADJ", "P-ADJ-PAIR",
                   "P-ADJ-UNREACHED"}, "placement phase row coverage")
    eq(full.read_text(), "full-release-report-sentinel\n",
       "placement phase must not overwrite the release audit")


# ===== P-ADJ measured the WRONG DISTANCE, and ignored half its schema =======
# 2026-07-29. Two board agents found this independently, from opposite ends.
@test("P-ADJ grades the ANCHOR PIN to its nearest partner, not the whole "
      "net's worst pad pair — a correctly-placed bulk cap must not make a "
      "budget WORSE", kind="known_bad")
def t_padj_anchor_not_whole_net():
    """THE PERVERSE CONSEQUENCE THAT NAMES THE DEFECT. The span was
    `max(dist(a,b) for a in pads for b in pads)` over the WHOLE net, so ADDING
    a third pad — a correctly-placed bulk capacitor — made the score worse.
    The same board, one part later, scored lower for being more correct.

    Here U1.1 -> C1.1 is 2mm against a 6mm budget, and `C_BULK` sits 40mm away
    on the same net. Whole-net: 40mm, FAIL. Anchor: 2mm, PASS — and the row
    must NAME THE PAIR IT GRADED, because an unstated anchor is a hidden
    assumption.

    MEASURED ON THE REAL BOARDS. pluto-cal-switch RP2040:3V3 reported 72.96mm
    against 4mm (3V3 is a poured rail crossing a 72mm board); the anchor
    metric on the same 44 budgets is 44/44 PASS, worst 2.60mm
    (U_MCU.26 -> C_IO3.1). pluto-rx2-8way RP2040:DVDD_1V1 reported 13.167mm
    against 10mm; the anchor pair is U_MCU.23 -> C_MCU7.1 at 8.79mm, which is
    inside the budget AND is the tight number the whole-net figure buried.

    AND IT DOES NOT SOFTEN THE INCIDENT P-ADJ WAS BUILT FOR: usb-hub-3s-v2's
    TPS25740A `RSNS <= 5mm` still FAILS on the anchor metric at 7.34mm
    (U1.19 -> Q6.5), where the whole-net number was 10.18mm.

    RED-VERIFIED 2026-07-29 (git-swap, tests/README step 3): with git HEAD's
    policy_audit.py swapped back in, this fixture's P-ADJ row reads
    `FAIL | datasheet layout budgets exceeded: ['SW_NODE span 40.0mm > 6.0mm
    ...']` and the test fails on `P-ADJ on the anchor pair`.
    """
    d = padj_project([KS_REAL], sw_span=2.0, bulk_at=40.0)
    rows = audit_rows(d)
    eq(rows["P-ADJ"][0], "PASS", "P-ADJ on the anchor pair")
    contains(rows["P-ADJ"][1], "U1.1->C1.1", "names the pin pair it graded")
    contains(rows["P-ADJ"][1], "of 6.0mm", "and the budget it graded against")
    # the bulk cap is on the net and is NOT what got graded
    not_contains(rows["P-ADJ"][1], "40.", "the whole-net span is not the metric")

    # ...and the anchor pin itself moving away still FAILS: this is a change of
    # METRIC, not a loosening. 25mm from U1.1 to its nearest partner.
    over = padj_project([KS_REAL], sw_span=25.0, bulk_at=40.0)
    r2 = audit_rows(over)
    eq(r2["P-ADJ"][0], "FAIL", "an anchor pin far from every partner")
    contains(r2["P-ADJ"][1], "U1.1->C1.1", "names the pair that failed")


@test("P-ADJ reports UNREACHED when the DECLARING PART has no pad on the "
      "budgeted net — it must not grade off two other parts' pads",
      kind="known_bad")
def t_padj_anchor_must_be_the_declaring_part():
    """`PARTNERS` has two pads and neither belongs to U1, the part whose
    datasheet sentence this is. The old whole-net metric happily measured
    D1.1 -> D2.1 (2mm, inside the 3mm budget) and reported the budget honoured
    — a PASS assembled entirely out of parts the sentence is not about.

    This is the commonest form in the fleet, and it is always a series
    element: RP2040's `USB_DP` budget names a net that becomes `USB_DP_MCU`
    after the 27R, the SMA jack's `SW1_ANT` lives between the DC block and the
    switch, ABM8's `XOUT` is the crystal side of R_XTAL. MEASURED 2026-07-29:
    5 such budgets on pluto-cal-switch and 3 on pluto-rx2-8way, every one of
    them previously graded — and every one of them graded off somebody else's
    copper.

    RED-VERIFIED 2026-07-29 (git-swap): pre-fix, P-ADJ reads
    `PASS | ... (1/1 budgets reached)` on this fixture and P-ADJ-UNREACHED
    reads PASS, so this test fails on `P-ADJ-UNREACHED on a budget the
    declaring part is not in`.
    """
    d = padj_project([KS_NOT_MINE])
    rows = audit_rows(d)
    eq(rows["P-ADJ-UNREACHED"][0], "FAIL",
       "P-ADJ-UNREACHED on a budget the declaring part is not in")
    contains(rows["P-ADJ-UNREACHED"][1], "PARTNERS", "names the net")
    contains(rows["P-ADJ-UNREACHED"][1], "U1",
             "names the declaring part's refdes, which is the anchor it wanted")
    # and P-ADJ must NOT report a pass over it: zero graded is zero
    eq(rows["P-ADJ"][0], "FAIL", "P-ADJ over a zero denominator")
    contains(rows["P-ADJ"][1], "GRADED NOTHING",
             "a gate with no denominator says so (canon M-COVER)")
    contains(rows["P-ADJ"][1], "M-COVER", "and cites the canon")


@test("P-ADJ-PAIR grades layout.adjacency refdes pairs — a schema field no "
      "gate read at all", kind="known_bad")
def t_padj_pair_is_graded():
    """`layout.adjacency` was in the 02_parts schema, in the part.yaml files,
    and READ BY NOTHING — while looking covered, which is worse than an absent
    field: the author who wrote it believed a gate stood behind it.

    THE LIVE EXAMPLE, with its number: USBLC6-2SC6 requires U_ESD within
    2.0mm of J_USB because ST DocID11265 sec 2.2 turns 6nH per 10mm into a 17V
    clamp firing at 305V. pluto-rx2-8way's floorplan sat at ~8mm and no gate
    objected — that board's agent had to hand-measure it, and got the placement
    to 1.689mm on D+/D-. This gate now reads 1.689mm for the same pair (canon
    M1: two methods, one number), and it FAILS the two MCP1755S budgets the
    same board never had graded: U_LDO~C_LDO 4.88mm and U_LDO~C_LDI 10.78mm,
    both against 3mm.

    An adjacency budget is measured as the COPPER GAP (pad edge to pad edge —
    the track length the nH/mm arithmetic applies to) on the worst net the two
    parts share, POURED nets excluded because a plane joins them without a
    track.

    RED-VERIFIED 2026-07-29 (git-swap): pre-fix there is NO `P-ADJ-PAIR` row in
    the report at all, and this test fails on `report has no P-ADJ-PAIR row`.
    """
    far = ('    - {refdes: [U1, C_BULK], max_mm: 2.0, why: "the ESD array '
           'belongs behind the connector pads; 6nH/10mm is a clamp term"}')
    d = padj_project([KS_REAL], adjacency=[far], bulk_at=40.0)
    rows = audit_rows(d)
    check("P-ADJ-PAIR" in rows, f"report has no P-ADJ-PAIR row: {sorted(rows)}")
    eq(rows["P-ADJ-PAIR"][0], "FAIL", "P-ADJ-PAIR on a 40mm-apart pair")
    contains(rows["P-ADJ-PAIR"][1], "U1~C_BULK", "names the pair")
    contains(rows["P-ADJ-PAIR"][1], "of 2.0mm", "and the budget")
    # SEPARATE ROW: the keep_short verdict is untouched by it
    eq(rows["P-ADJ"][0], "PASS", "keep_short is graded on its own")

    # ...and a pair that IS adjacent passes, on the gap and not the centres
    near = ('    - {refdes: [U1, C1], max_mm: 2.0, why: "same sentence, and '
            'this placement honours it"}')
    ok = audit_rows(padj_project([KS_REAL], adjacency=[near]))
    eq(ok["P-ADJ-PAIR"][0], "PASS", "an adjacent pair")
    contains(ok["P-ADJ-PAIR"][1], "U1~C1", "names the pair it graded")

    # ...and a pair that shares NO net is UNREACHED, not silently measured:
    # without a shared net there is no copper whose length the budget bounds.
    nonet = ('    - {refdes: [D1, TP1], max_mm: 2.0, why: "these two share no '
             'net at all, so this budget bounds no copper"}')
    un = audit_rows(padj_project([KS_REAL], adjacency=[nonet]))
    eq(un["P-ADJ-UNREACHED"][0], "FAIL", "an adjacency budget over no shared net")
    contains(un["P-ADJ-UNREACHED"][1], "share no net", "says why")

    # ...and a refdes that is not on the board at all is UNREACHED by name
    ghost = ('    - {refdes: [U1, U_NOT_HERE], max_mm: 2.0, why: "a refdes '
             'copied out of the reference design"}')
    gh = audit_rows(padj_project([KS_REAL], adjacency=[ghost]))
    eq(gh["P-ADJ-UNREACHED"][0], "FAIL", "an adjacency budget naming a ghost")
    contains(gh["P-ADJ-UNREACHED"][1], "U_NOT_HERE", "names the missing refdes")


@test("P-ADJ-PAIR may scope a physical requirement to named shared nets and "
      "fails closed on unknown names", kind="known_bad")
def t_padj_pair_net_scope():
    scoped = ('    - {refdes: [U1, C1], nets: [SW_NODE], max_mm: 2.0, '
              'why: "the short-loop requirement applies to this signal path, '
              'not every rail the packages happen to share"}')
    ok = audit_rows(padj_project([KS_REAL], adjacency=[scoped]))
    eq(ok["P-ADJ-PAIR"][0], "PASS", "a valid shared-net allowlist")
    contains(ok["P-ADJ-PAIR"][1], "on SW_NODE", "names the scoped net")

    ghost = ('    - {refdes: [U1, C1], nets: [NOT_SHARED], max_mm: 2.0, '
             'why: "a typo must not silently broaden or erase the grade"}')
    bad = audit_rows(padj_project([KS_REAL], adjacency=[ghost]))
    eq(bad["P-ADJ-UNREACHED"][0], "FAIL", "an unknown scoped net")
    contains(bad["P-ADJ-UNREACHED"][1], "NOT_SHARED", "names the bad net")
    contains(bad["P-ADJ-UNREACHED"][1], "not shared", "states the mismatch")


@test("P-ADJ failure reports enumerate every actionable finding instead of "
      "truncating the iteration set", kind="known_bad")
def t_padj_reports_all_failures():
    finding = ('    - {refdes: [U1, C_BULK], max_mm: 2.0, why: '
               '"six independent declarations model a report longer than the '
               'old five-item preview"}')
    rows = audit_rows(padj_project([KS_REAL], adjacency=[finding] * 6,
                                   bulk_at=40.0))
    eq(rows["P-ADJ-PAIR"][0], "FAIL", "six over-budget declarations")
    eq(rows["P-ADJ-PAIR"][1].count("U1~C_BULK"), 6,
       "the durable report retains every finding")


@test("a PROSE adjacency entry is UNREACHED, not a CRASH — the string form is "
      "the fleet's COMMON one", kind="known_bad")
def t_padj_pair_prose_entry_does_not_crash():
    """FOUND BY RUNNING THE NEW GATE ON THE FLEET, 2026-07-29, and it is the
    reason to do that before believing a green fixture. `adjacency:` in the wild
    is mostly FREE PROSE: 22 string entries on usb-hub-3s-v3 ('Cin (C13 HF +
    C9-C12 bulk) hard against the HS-FET drain (VIN) and PGND'), 5 more on
    archived crow-mic-pod. The first version of the pair loop did
    `ad.get("refdes")` on them and died with `AttributeError: 'str' object has
    no attribute 'get'`.

    A CRASH IS THE WORST AVAILABLE VERDICT — worse than a FAIL — because the
    wrapper reads the non-zero exit as "the gate ran and objected" while a human
    reads the traceback as a broken test rather than an ungraded board (the same
    lesson as fa22228's UTF-8 BOM post-mortem). And the prose entries are a real
    finding, not an exception: they declare a placement constraint no gate can
    read, which is the M-COVER class this whole change is about. MEASURED after
    the fix: usb-hub-3s-v3 reports `P-ADJ-PAIR GRADED NOTHING: 0 of 22` with all
    22 named under P-ADJ-UNREACHED, instead of a traceback.

    RED-VERIFIED 2026-07-29 by restoring the unguarded `ad.get("refdes")`:
    policy_audit exits non-zero with the AttributeError above and writes NO
    report at all, so `audit_rows` fails on a missing
    `06_build/policy_audit.md`.
    """
    prose = ('    - "Cin (C13 HF + C9-C12 bulk) hard against the HS-FET drain '
             '(VIN) and PGND -> smallest possible hot loop"')
    rows = audit_rows(padj_project([KS_REAL], adjacency=[prose]))
    eq(rows["P-ADJ-UNREACHED"][0], "FAIL", "a prose adjacency entry")
    contains(rows["P-ADJ-UNREACHED"][1], "PROSE", "names the shape problem")
    contains(rows["P-ADJ-UNREACHED"][1], "notes:", "and where prose belongs")
    eq(rows["P-ADJ-PAIR"][0], "FAIL", "0 of 1 adjacency budgets measurable")
    contains(rows["P-ADJ-PAIR"][1], "GRADED NOTHING", "with no denominator")
    # the keep_short half is unaffected by a malformed neighbour
    eq(rows["P-ADJ"][0], "PASS", "keep_short still graded")


# ===========================================================================
# P-LAND — the widest track that can actually leave a pad (canon M-ENTRY)
# ===========================================================================
# THE FIXTURE CORPUS IS THE TWO REAL BOARDS THAT ASKED THE QUESTION, not a
# model of them. Both halves must work or the gate ranks nothing:
#   * a pad that genuinely cannot emit its class width must FAIL, and
#   * a pad relaxed by a rule area / `scoped_floors` must PASS.
# `pluto-cal-switch` supplies both from ONE board: as it stands it has three
# permissive rule areas + `scoped_floors`, and stripping those three rules
# from the .kicad_dru copy (the good input broken in exactly one way) brings
# back the eleven pads its stage-6 hand measurement found.
#
# RED-VERIFIED against pre-fix code: `git show HEAD~1:...escape_check.py`
# has no `--board` at all, so every P-LAND test below exits 2 with
# `unrecognized arguments: --board`. That is the weak red. The STRONG reds
# were run by ablation on the post-fix gate and are recorded per test:
#   (a) relaxation reader neutered (`resolve_min` ignoring kind == "area"):
#       the clean board test goes RED with the ELEVEN failures back, i.e.
#       the gate reds a board that already fixed the problem;
#   (b) landing grid neutered (`launch_points` returning the centre only):
#       the clean board test goes RED with SIX failures — U_SW1.1/.3/.4 and
#       their channel-2 twins, pads the board routed at 0.35 mm;
#   (c) pour + via-on-pad exemptions neutered: the sealed
#       crow-recorder-central-v2 goes RED with 17 failures, 16 of them on a
#       TQFP-128 power ring that carries no track at all.
CAL_KICAD = ROOT / "projects" / "pluto-cal-switch" / "04_kicad"
CAL_R0 = ROOT / "projects" / "pluto-cal-switch" / "06_build" / "route" / "r0.kicad_pcb"
RX2_KICAD = ROOT / "projects" / "pluto-rx2-8way" / "04_kicad"
CRC_KICAD = (ROOT / "projects" / "crow-recorder-central-v2" / "04_kicad")

# the eleven, verbatim from pluto-cal-switch's own nets.yaml evidence block:
# pad, class floor, landable maximum measured by hand at stage 6
CAL_ELEVEN = [("U_SW1.5", "0.360", "0.250"), ("U_SW2.5", "0.360", "0.250"),
              ("U_MCU.46", "0.330", "0.300"), ("U_MCU.47", "0.330", "0.300"),
              ("U_MCU.10", "0.400", "0.300"), ("U_MCU.22", "0.400", "0.300"),
              ("U_MCU.26", "0.400", "0.300"), ("U_MCU.33", "0.400", "0.300"),
              ("U_MCU.23", "0.400", "0.300"), ("U_MCU.45", "0.400", "0.300"),
              ("U_MCU.50", "0.400", "0.300")]


def board_copy(kicad_dir, drop_rules=(), extra_dru="", keep_rules=None,
               board_source=None):
    """A scratch copy of a real 04_kicad board triple, optionally with its
    .kicad_dru edited. The BOARD bytes are never touched — only the rule file
    the gate reads its floors and relaxations from."""
    import shutil
    d = tmpdir("land_")
    stem = sorted(Path(kicad_dir).glob("*.kicad_pcb"))[0].stem
    shutil.copy(board_source or (Path(kicad_dir) / f"{stem}.kicad_pcb"),
                d / f"{stem}.kicad_pcb")
    for ext in ("kicad_pro", "kicad_dru"):
        shutil.copy(Path(kicad_dir) / f"{stem}.{ext}", d / f"{stem}.{ext}")
    dru = d / f"{stem}.kicad_dru"
    blocks = re.split(r"(?=\(rule )", dru.read_text())
    out = []
    for b in blocks:
        m = re.match(r'\(rule\s+"?([^"\s)]+)"?', b)
        if m and any(m.group(1).startswith(p) for p in drop_rules):
            continue
        if m and keep_rules is not None and m.group(1) not in keep_rules:
            continue
        out.append(b)
    dru.write_text("".join(out) + extra_dru)
    return d / f"{stem}.kicad_pcb"


def land(board, *args):
    return run([KPY, ESC, "--board", str(board), *args])


def denominator(out):
    m = re.search(r"P-LAND denominator \S+: (\d+) graded / (\d+) copper pads "
                  r"\((\d+) no declared width floor, (\d+) fed by a same-net "
                  r"POUR, (\d+) escaped by a VIA ON THE LAND, (\d+) no net, "
                  r"(\d+) UNREACHED\); (\d+) graded against a SCOPED floor, "
                  r"(\d+) against a scoped clearance; (\d+) failing", out)
    check(m is not None, f"no P-LAND denominator line in:\n{out[-2000:]}")
    keys = ("graded", "pads", "no_floor", "pour", "via", "no_net",
            "unreached", "scoped", "scoped_clear", "failing")
    return dict(zip(keys, (int(x) for x in m.groups())))


@test("P-LAND passes the board that ALREADY FIXED the problem")
def t_land_passes_the_relaxed_board():
    """pluto-cal-switch solved its eleven pads with three permissive rule
    areas + `scoped_floors` bounded to lambda_g/61. A gate that reports
    eleven failures on it is switched off inside a week, so this is the
    half that decides whether P-LAND is adoptable at all.

    ABLATION RED (a): with `resolve_min` skipping kind == "area" rules the
    same command exits 1 with the eleven FAIL lines. ABLATION RED (b): with
    `launch_points` returning only the pad centre it exits 1 with six other
    failures (U_SW1.1/.3/.4 + twins), pads this board routed at 0.35 mm and
    whose hand measurement is 0.460 mm."""
    r = must_pass(land(CAL_KICAD / "pluto_cal_switch.kicad_pcb"),
                  "P-LAND on pluto-cal-switch as it stands")
    d = denominator(r.out)
    eq(d["failing"], 0, "failing pads on the board that fixed the problem")
    check(d["scoped"] >= 11, f"pads graded against a SCOPED floor: "
                             f"{d['scoped']} (the three tapers license 21)")
    check(d["graded"] > 100, f"only {d['graded']} pads graded")
    contains(r.out, "input: floors+relaxations = ",
             "G-INPUT names the rule file the verdict depends on")


@test("P-LAND FAILS the ELEVEN pads when the relaxations are stripped",
      kind="known_bad")
def t_land_fails_the_eleven():
    """THE MOTIVATING MEASUREMENT, reproduced by an independent method. The
    board's own stage-6 measurement (48 directions x a 30 um landing grid,
    by hand, recorded in nets.yaml) found ELEVEN pads under their own class
    minimum. Strip the three `scoped_*` rules from a COPY of the .kicad_dru
    — the good input broken in exactly one way — and this gate must name the
    same eleven with the same numbers.

    Pre-fix (HEAD~1) there is no `--board` flag at all: nothing in the
    pipeline asked this question, which is why it was found by hand."""
    b = board_copy(CAL_KICAD, drop_rules=("scoped_",), board_source=CAL_R0)
    r = must_fail(land(b), "P-LAND with the scoped_floors stripped")
    d = denominator(r.out)
    eq(d["failing"], 11, "pads under their own class floor")
    eq(d["scoped"], 0, "scoped floors, after stripping them")
    for pad, floor, landable in CAL_ELEVEN:
        contains(r.out, f"{pad} ", f"the finding names {pad}")
        m = re.search(rf"FAIL P-LAND \S+ {re.escape(pad)} .*?floor="
                      rf"([0-9.]+) .*?landable=([0-9.]+)", r.out)
        check(m is not None, f"{pad} has no FAIL line")
        eq((m.group(1), m.group(2)), (floor, landable),
           f"{pad} floor/landable vs the hand measurement")


@test("P-LAND does not blame WIDTH for a routing failure")
def t_land_fix_order_ranks_grid_first():
    """The correction that cost a day: on pluto-rx2-8way the arms did NOT
    fail for want of width. At `grid_step: 0.1` nothing routed the five
    boxed RF pads at ANY width; at 0.05 + clearance 0.14 the same wave
    routes 11/11 at the full 0.36 mm. So a failing run must rank GRID,
    then CLEARANCE, then WIDTH — and must not offer NECK-DOWN, which was
    MEASURED to deliver 149.832 mm at 0.25 mm and 0.000 mm at 0.36."""
    b = board_copy(CAL_KICAD, drop_rules=("scoped_",))
    r = must_fail(land(b), "a failing P-LAND run")
    for needle in ("ROUTER GRID", "grid_step: 0.05", "SCOPED CLEARANCE",
                   "NOT A REMEDY", "149.832", "0.000 mm at 0.36",
                   "DOES NOT CLAIM WIDTH IS WHY A BOARD FAILED TO ROUTE"):
        contains(r.out, needle, "the fix-line")
    gi = r.out.index("1. ROUTER GRID")
    ci = r.out.index("2. A LAUNCH-LOCAL SCOPED CLEARANCE")
    wi = r.out.index("3. WIDTH")
    check(gi < ci < wi, "the ranked causes are GRID, CLEARANCE, WIDTH")


@test("P-LAND honours a rule-area CLEARANCE relaxation")
def t_land_honours_a_scoped_clearance():
    """WHAT THIS GATE NEEDS FROM THE SCOPED-CLEARANCE WORK. Today
    `scoped_floors:` emits `track_width` only, so the ONE relaxation that
    actually rescues pluto-rx2-8way's RF launches cannot be declared. The
    reader is already here: any `.kicad_dru` rule carrying `constraint
    clearance (min ...)` is resolved by the same last-match precedence.

    MEASURED on the real rx2 board: with the declared 0.200 mm clearance the
    five boxed RF launches take 0.316 mm against a 0.360 mm RF50 floor; add
    a 0.14 mm clearance rule for RF50 and all five clear it outright
    (0.436 mm), taking the board from 8 findings to 3."""
    # BASELINE IS BUILT BY STRIPPING, NOT BY ASSUMING THE BOARD IS UNFIXED.
    # This read the LIVE board and asserted the five RF launches still fail —
    # which was true when written and became false hours later when canon
    # R-SCOPE landed `scoped_clr_rf_*` on that very board. A fixture that
    # asserts a defect the tree has since REPAIRED fails for being right.
    #
    # THIRD INSTANCE of a fixture breaking on mutable project state
    # (t1_fleet_regrade on a dossier deletion, t1_gate_contract on a
    # mid-rebuild board), which is the trigger tests/README.md names for
    # earning a checker. Stripping makes it a ROUND TRIP on real bytes and
    # therefore stronger: remove the relaxation and the five come back, add it
    # and they clear — the gate's response to the rule is what is under test,
    # not the board's current state.
    stripped = board_copy(RX2_KICAD, drop_rules=(
        "scoped_clr_rf_launch", "scoped_clr_rf_jack_ant2",
        "scoped_clr_rf_jack_ant3", "scoped_clr_rf_jack_ant6",
        "scoped_clr_rf_jack_ant7", "scoped_clr_rf_jack_rx1",
        "scoped_clr_rf_jack_rx2"))
    base = must_fail(land(stripped),
                     "P-LAND with the scoped clearances STRIPPED")
    hard = denominator(base.out)
    for pad in ("U_SW.2", "U_SW.4", "U_SW.15", "U_SW.17", "U_SW.22"):
        contains(base.out, f"{pad} net=", f"the RF launch {pad} is named")
    b = board_copy(RX2_KICAD, extra_dru=(
        '(rule "scoped_rf_launch_clearance"\n'
        "  (condition \"A.NetClass == 'RF50'\")\n"
        "  (constraint clearance (min 0.14mm)))\n"))
    r = land(b)
    d = denominator(r.out)
    check(d["scoped_clear"] > 0, "pads graded against a scoped clearance")
    check(d["failing"] < hard["failing"],
          f"a 0.14 mm scoped clearance must clear findings: "
          f"{hard['failing']} -> {d['failing']}")
    for pad in ("U_SW.2", "U_SW.4", "U_SW.15", "U_SW.17", "U_SW.22"):
        not_contains(r.out, f"FAIL P-LAND pluto_rx2_8way {pad} ",
                     f"{pad} under a 0.14 mm scoped clearance")


@test("P-LAND leaves POUR-fed and VIA-escaped pads out of scope, and says so")
def t_land_pour_and_via_are_out_of_scope():
    """The sealed, DRC-clean crow-recorder-central-v2 escapes its XU316
    TQFP-128 power ring with a VIA ON THE LAND — U1.10 carries NO track at
    all, only a 0.3 mm via on a 1.475 x 0.250 mm pad — and pours feed
    another 34 pads. A gate that demands a track floor of those pads reds a
    board that shipped.

    ABLATION RED (c): with both exemptions removed this exits 1 with 17
    failures, 16 of them on that power ring."""
    r = must_pass(land(CRC_KICAD / "crow_recorder_central_v2.kicad_pcb"),
                  "P-LAND on the sealed crow-recorder-central-v2")
    d = denominator(r.out)
    eq(d["failing"], 0, "failures on a sealed DRC-clean board")
    check(d["pour"] >= 30 and d["via"] >= 40,
          f"pour-fed {d['pour']} / via-escaped {d['via']} pads named in the "
          f"denominator")
    eq(d["graded"] + d["no_floor"] + d["pour"] + d["via"] + d["no_net"]
       + d["unreached"], d["pads"], "the denominator accounts for every pad")


@test("P-LAND cross-checks its own model against routed copper")
def t_land_model_is_falsifiable_on_routed_copper():
    """canon M1/G-VACUOUS: a prediction nothing can contradict is not a
    prediction. On a routed board every graded pad already carrying same-net
    copper is compared against the width that ACTUALLY left it. 0 of 540
    over five sealed boards — and the 5 that fire on pluto-rx2-8way are its
    RF star routed at 0.36 mm on a clearance the .kicad_dru never declares,
    which is the same board's 49 DRC findings."""
    r = must_pass(land(CRC_KICAD / "crow_recorder_central_v2.kicad_pcb"),
                  "P-LAND on the sealed crow-recorder-central-v2")
    m = re.search(r"routed cross-check \S+: (\d+) graded pad\(s\) already "
                  r"carry a same-net track, (\d+) of them WIDER", r.out)
    check(m is not None, f"no routed cross-check line:\n{r.out[-1500:]}")
    check(int(m.group(1)) > 100, "the cross-check reached real copper")
    eq(int(m.group(2)), 0, "pads where routed copper refutes the model")


@test("P-LAND FAILS a board with no declared width floor at all",
      kind="known_bad")
def t_land_zero_denominator_fails():
    """canon M-COVER: a zero denominator is a FAIL, never a pass. Netclass
    floors are generated BEFORE routing (canon R1), so 0 graded pads means
    generate_rules never ran — the exact shape of `escape_check.py` with a
    glob that matched nothing, one artifact up."""
    b = board_copy(CAL_KICAD, keep_rules=())
    r = must_fail(land(b), "P-LAND on a board whose .kicad_dru declares "
                           "no width floor", "0 pads graded")
    contains(r.out, "M-COVER", "names the canon it is enforcing")
    eq(denominator(r.out)["graded"], 0, "graded pads")


@test("P-LAND FAILS a board path that does not exist", kind="known_bad")
def t_land_missing_board_fails():
    """A board that cannot be read is not a board that passed (G-COVER)."""
    must_fail(land(tmpdir("land_") / "nope.kicad_pcb"),
              "P-LAND on a missing board", "no such board")


@test("P-LAND reports an UNREADABLE land as UNREACHED, never as a pass",
      kind="known_bad")
def t_land_unreached_pad_is_named():
    """M-COVER's other half. A pad whose land geometry cannot be resolved is
    named and counted, never silently absent from the denominator. Injected
    at the one seam where it can happen (KiCad failing to give a pad
    polygon), because no real board in this fleet has one — which is exactly
    why the branch needs a fixture."""
    d = tmpdir("land_")
    drv = d / "drv.py"
    drv.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        "import escape_check as ec\n"
        "real = ec.read_board\n"
        "def fake(p):\n"
        "    pads, un, areas, pours, vias, tracks = real(p)\n"
        "    bad = pads.pop()\n"
        "    bad['why_unreached'] = 'pad outline unreadable (injected)'\n"
        "    un.append(bad)\n"
        "    return pads, un, areas, pours, vias, tracks\n"
        "ec.read_board = fake\n"
        "sys.argv = ['escape_check', '--board', sys.argv[1]]\n"
        "ec.main()\n")
    r = run([KPY, drv, CAL_KICAD / "pluto_cal_switch.kicad_pcb"])
    check(r.rc != 0, "an UNREACHED pad must not exit 0\n" + r.out[-1500:])
    contains(r.out, "UNREACHED pluto_cal_switch ", "the pad is named")
    eq(denominator(r.out)["unreached"], 1, "UNREACHED pads in the denominator")


@test("P-LAND passes a pad whose class declares NO width floor",
      kind="vacuity", gate="escape_check.py")
def t_vacuity_P_LAND_passes_a_pad_whose_class_declares_no_width_floor():
    """THE DECLARED BLIND SPOT (canon G-VACUOUS), and it is the whole scope
    decision stated as a fixture: P-LAND grades a pad against a DECLARED
    floor, so a class that declares none cannot fail. Delete three lines
    from pluto-cal-switch's nets.yaml and all ELEVEN findings become
    silence, while the geometry — 0.250 mm of landable width on a pad whose
    net wants 0.350 — is unchanged.

    It is BOUNDED and ENUMERATED rather than hidden: `N no declared width
    floor` prints inside the denominator on every run (1440 of 2689 copper
    pads fleet-wide). It is NOT closed by grading against a netclass DEFAULT
    width — that invents a requirement the board never made and would red
    every board on day one, which is how a gate gets switched off.

    The must_fail CONTRAST below is what proves the fact is gradeable at
    all: restore the floors, same board, same pads, eleven findings."""
    # keep ONE floor (QSPI, whose 13 pads are all comfortable) so the run is
    # not the zero-denominator FAIL — the blind spot is a PARTIAL
    # denominator that reads as a clean board.
    b = board_copy(CAL_KICAD, keep_rules={"QSPI_width"}, board_source=CAL_R0)
    r = must_pass(land(b),
                  "P-LAND on a board that declares no width floor for the "
                  "classes whose pads cannot take one")
    d = denominator(r.out)
    eq(d["failing"], 0, "findings once nothing declares a floor")
    eq(d["graded"], 13, "pads still graded (the one surviving class)")
    check(d["no_floor"] > 250, f"only {d['no_floor']} pads out of scope")
    # CONTRAST: the same geometry, with the class floors back = eleven.
    hard = must_fail(land(board_copy(CAL_KICAD, drop_rules=("scoped_",),
                                     board_source=CAL_R0)),
                     "the same pads with their class floors declared")
    eq(denominator(hard.out)["failing"], 11, "the findings the vacuity hides")


if __name__ == "__main__":
    sys.exit(main())
