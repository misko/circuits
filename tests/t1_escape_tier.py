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
from harness import (KPY, SCRIPTS, check, contains, main, must_fail,  # noqa: E402
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


@test("proven-parts ledger parses and every escape block is schema-valid")
def t_proven_parts_schema():
    """The v4 harvest added 9 function entries — the ledger must parse and
    every candidate's escape block must use the checker's own vocabulary
    (style/tier/condition names), or the next D-ESC consult starts from a
    corrupt ledger."""
    import yaml as _y
    sys.path.insert(0, str(SCRIPTS))
    import escape_check as ec
    ledger = _y.safe_load(
        (SCRIPTS.parent / "references" / "proven-parts.yaml").read_text())
    tiers = ec.load_tiers()
    statuses = {"shipped", "designed-in", "incident", "unresolved"}
    n = 0
    for fn, body in ledger["functions"].items():
        for c in body.get("candidates") or []:
            if set(c) == {"mpn", "note"}:      # cross-reference stub
                continue
            check(c.get("status") in statuses,
                  f"{fn}/{c.get('mpn')}: bad status {c.get('status')!r}")
            check(bool(c.get("provenance")),
                  f"{fn}/{c.get('mpn')}: no provenance")
            esc = c.get("escape")
            if esc:
                check(esc.get("style") in
                      ec.OUTWARD_STYLES | ec.RING_STYLES | {"bga"},
                      f"{fn}/{c['mpn']}: bad style {esc.get('style')!r}")
                check(esc.get("tier_required") in tiers,
                      f"{fn}/{c['mpn']}: bad tier {esc.get('tier_required')!r}")
                bad = set(esc.get("conditions") or []) - ec.KNOWN_CONDITIONS
                check(not bad, f"{fn}/{c['mpn']}: unknown conditions {bad}")
            n += 1
    check(n >= 14, f"ledger looks truncated: only {n} candidates")


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


if __name__ == "__main__":
    main()
