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


# -------------------------------------------------------- known-bad cases
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
