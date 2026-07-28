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
from harness import (KPY, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     must_fail,
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
"""
KS_REAL = ('    - {net: SW_NODE, max_span_mm: 6, why: "switch-node loop area '
           'sets EMI; datasheet Layout sec 11"}')
KS_GHOST = ('    - {net: NOT_ON_THIS_BOARD, max_span_mm: 3, why: "net name '
            'copied out of the datasheet reference design"}')
KS_LONE = ('    - {net: LONE, max_span_mm: 3, why: "resolves to a single-pad '
           'net on this board"}')


def _fp(ref, x, y, pads):
    ps = "\n".join(
        f'\t\t(pad "{i}" smd roundrect (at 0 {j * 1.0} 0) (size 0.9 0.9)\n'
        f'\t\t\t(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.25)\n'
        f'\t\t\t(net {n} "{nm}"))' for j, (i, n, nm) in enumerate(pads))
    return (f'\t(footprint "t:R_0402"\n\t\t(layer "F.Cu")\n\t\t(at {x} {y} 0)\n'
            f'\t\t(property "Reference" "{ref}" (at 0 -2 0) (layer "F.SilkS")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
            f'\t\t(property "Value" "V" (at 0 2 0) (layer "F.Fab")\n'
            f'\t\t\t(effects (font (size 1 1) (thickness 0.15))))\n'
            f'\t\t(attr smd)\n{ps}\n\t)')


def padj_project(keep_short, sw_span=2.0):
    """A scratch project WITH a board: `SW_NODE` spans `sw_span` mm over two
    real pads, `LONE` has exactly one pad, and `NOT_ON_THIS_BOARD` has none."""
    d = scratch_project({"FXPART": FX_PART % "\n".join(keep_short)})
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
        + _fp("U1", 100, 100, [("1", 1, "SW_NODE"), ("2", 2, "GND")]) + "\n"
        + _fp("C1", 100 + sw_span, 100,
              [("1", 1, "SW_NODE"), ("2", 2, "GND")]) + "\n"
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
    contains(rows["P-ADJ"][1], "1/3 budgets reached",
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


if __name__ == "__main__":
    sys.exit(main())
