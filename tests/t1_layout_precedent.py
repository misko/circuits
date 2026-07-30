#!/usr/bin/env python3
"""T1: P-PREC — the LAYOUT PRECEDENT SEARCH record, graded BY TIER
(canon P-PREC; `policy_audit.py`).

MOTIVATING CASE, and it is the repo's BEST dossier rather than its worst.
`projects/pluto-rx2-8way/02_parts/RP2040/part.yaml` ran the search SKILL.md
demands and ran it carefully: it consulted the manufacturer's own routed
reference — "Hardware design with RP2040", Figure 6, PDF p9 — and pulled out the
flash-against-the-QSPI-corner placement, the decoupling rows, and a crystal
series resistor that exists ONLY in that guide's section 2.3 and not in the
datasheet. It read that figure VISUALLY AT 200 dpi, off a raster.

Verified 2026-07-30 at raspberrypi.com/documentation/microcontrollers/rp2040.html:
Raspberry Pi publishes a "Minimal Viable Board" reference design IN KICAD —
schematic and PCB layout — plus the full Pico / Pico W designs in Cadence
Allegro, all under "Raspberry Pi grants permission to use, copy, modify, and
distribute the following designs for any purpose, with or without fee". A free,
permissively licensed, EDITABLE tier-2 artifact for the exact part.

THE DOSSIER ALREADY SAID SO, in prose: "OWED: minimal-design-example and
VGA-demo KiCad design files ... Not fetched; Figure 6 is a raster." The
judgement was made and made honestly. What did not exist was any way for a
MACHINE to tell that record apart from one that had reached the design files —
a bare-string `layout_refs:` list is the same shape either way. That, not the
author's care, is what P-PREC fixes.

WHAT IS GRADED IS HONESTY ABOUT THE CEILING, NOT POSSESSION OF IT — see the
canon row. Both halves are fixtured here on purpose: `t_kb_*` are the known-bad
cases, and `t_tier1_with_a_NAMED_gap_passes` / `t_strongest_tier_reached_passes`
are the other half, because a ladder that cannot be satisfied is a ladder that
gets switched off.

RED-VERIFICATION (tests/README.md §Adding a regression). P-PREC is a NEW check,
so the pre-fix code is its ABSENCE. Every known-bad fixture below was re-run
with `git show 5566d356:skills/kicad-pcb/scripts/policy_audit.py` swapped in
(5566d356 = the commit before P-PREC landed), and the MEASURED pre-fix output is
recorded in each docstring. Restored and re-run green afterwards.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     run, test, tmpdir)

POLICY = SCRIPTS / "policy_audit.py"

# An in-scope part by P-LAYOUT's rule (npins > 2), carrying a valid `layout:`
# block so that P-LAYOUT itself is green and only P-PREC is under test.
PART = """mpn: RP2040
manufacturer: Raspberry Pi
type: mcu
package: QFN-56
footprint: lib:QFN-56_7x7mm_P0.4mm
pins: {{1: IOVDD, 2: GPIO0, 3: GPIO1, 4: GPIO2}}
verified: "pinout table p.10"
layout:
  source: "RP2040 datasheet sec 2.9 Power Supplies + Hardware Design Fig 6"
  keep_short:
    - {{net: DVDD, max_span_mm: 10, why: "per-pin decoupling, datasheet 2.9"}}
{refs}
"""

# The honest RP2040 shape: tier 1 REACHED off a raster, tier 2 NAMED and not
# reached, with the reason. This is the record the live dossier already writes
# in prose, transcribed into the mapping form.
RP2040_HONEST = """layout_refs:
  - tier: 1
    artifact: "Hardware design with RP2040 build 2b6018e-clean, Figure 6
      'Section of layout showing RP2040 routing and decoupling', PDF p9 —
      the manufacturer's own routed board, read visually at 200 dpi"
    reached: true
  - tier: 2
    artifact: "Raspberry Pi 'Minimal Viable Board' KiCad reference design
      (schematic + PCB), raspberrypi.com/documentation/microcontrollers/
      rp2040.html; Pico / Pico W in Cadence Allegro alongside it"
    reached: false
    why: "19.9 MB guide fetch not attempted at the parts stage and the Allegro
      designs are not openable here. Figure 6's raster was used instead.
      Recorded as NOT DONE, not as absent."
"""


def scratch(refs, extra_parts=None):
    """A minimal project tree: one in-scope 02_parts entry + a nets.yaml."""
    d = tmpdir("prec_")
    for name, text in {"RP2040": PART.format(refs=refs),
                       **(extra_parts or {})}.items():
        pd = d / "02_parts" / name
        pd.mkdir(parents=True)
        (pd / "part.yaml").write_text(text)
    r = d / "03_src" / "rules"
    r.mkdir(parents=True)
    (r / "nets.yaml").write_text("fab_tier: jlc_2layer_default\nclasses: {}\n")
    return d


def audit_rows(d):
    """Run policy_audit (no board, --skip-drc) -> {id: (grade, detail)}."""
    run([KPY, str(POLICY), str(d), "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    return {m.group(1): (m.group(2), m.group(3))
            for m in re.finditer(r"^\| (\S+) \| (\S+) \| (.*) \|$", md, re.M)}


def prec(d):
    rows = audit_rows(d)
    return rows.get("P-PREC", ("MISSING", ""))


# =================================================== the known-bad half ======
@test("P-PREC FAILS a record that stops at tier 1 and names NO stronger tier "
      "— the ladder must NAME ITS CEILING", kind="known_bad")
def t_kb_unclosed_ladder():
    """THE INCIDENT SHAPE, minus the honesty. The live RP2040 dossier reached
    tier 1 (a 200 dpi raster) while a free, permissively licensed KiCad
    reference design existed for the exact part — and it SAID SO. Strip that
    admission and the record becomes a tier-1 stop presented as complete, which
    is precisely what no gate could see before.

    RED-VERIFIED against `git show 5566d356:...policy_audit.py`: the report has
    NO `P-PREC` row at all, so this test fails there with
    `report has no P-PREC row (got MISSING)` — the check did not exist, so
    nothing could tell a tier-1 stop from a tier-2 reach."""
    d = scratch("layout_refs:\n"
                "  - tier: 1\n"
                "    artifact: \"Hardware design with RP2040 Fig 6, PDF p9\"\n"
                "    reached: true\n")
    g, det = prec(d)
    check(g == "FAIL", f"report has no P-PREC row (got {g})")
    contains(det, "RP2040", "P-PREC names the part whose ladder is unclosed")
    contains(det, "NAME ITS CEILING", "P-PREC says what is missing")


@test("P-PREC FAILS an unreached tier declared with no why: — a debt states "
      "its reason", kind="known_bad")
def t_kb_unreached_without_reason():
    """`reached: false` with no reason is the waiver-without-evidence shape
    (canon M-WAIV): it looks like a considered decision and carries none. The
    threshold is 20 characters, which "not fetched" does not clear.

    RED-VERIFIED against 5566d356: no `P-PREC` row exists, so this fails with
    `report has no P-PREC row (got MISSING)`."""
    d = scratch("layout_refs:\n"
                "  - tier: 1\n"
                "    artifact: \"datasheet Fig 6\"\n"
                "    reached: true\n"
                "  - tier: 2\n"
                "    artifact: \"Minimal Viable Board KiCad reference design\"\n"
                "    reached: false\n"
                "    why: \"no\"\n")
    g, det = prec(d)
    check(g == "FAIL", f"report has no P-PREC row (got {g})")
    contains(det, "no why", "P-PREC names the missing reason")


@test("P-PREC FAILS a mapping entry that declares no tier — the authority "
      "order IS the grade", kind="known_bad")
def t_kb_no_tier():
    """An entry with an artifact and no tier is the bare-string defect wearing
    a mapping: it names what was read and still cannot be ranked.

    RED-VERIFIED against 5566d356: `report has no P-PREC row (got MISSING)`."""
    d = scratch("layout_refs:\n"
                "  - artifact: \"some reference layout I looked at\"\n"
                "    reached: true\n")
    g, det = prec(d)
    check(g == "FAIL", f"report has no P-PREC row (got {g})")
    contains(det, "no tier", "P-PREC names the missing tier")


@test("P-PREC FAILS a tier declared with no artifact — an unnamed precedent "
      "is not a precedent", kind="known_bad")
def t_kb_no_artifact():
    """`tier: 2, reached: true` with nothing named is an unfalsifiable claim to
    have done the most valuable half of the search.

    RED-VERIFIED against 5566d356: `report has no P-PREC row (got MISSING)`."""
    d = scratch("layout_refs:\n"
                "  - tier: 2\n"
                "    reached: true\n")
    g, det = prec(d)
    check(g == "FAIL", f"report has no P-PREC row (got {g})")
    contains(det, "no artifact", "P-PREC names the missing artifact")


@test("P-PREC FAILS an entry that declares neither reached: true nor false — "
      "consulted and merely known-of are what this gate separates",
      kind="known_bad")
def t_kb_no_reached():
    """RED-VERIFIED against 5566d356: `report has no P-PREC row (got
    MISSING)`."""
    d = scratch("layout_refs:\n"
                "  - tier: 2\n"
                "    artifact: \"Minimal Viable Board KiCad reference design\"\n")
    g, det = prec(d)
    check(g == "FAIL", f"report has no P-PREC row (got {g})")
    contains(det, "no reached", "P-PREC names the missing reached: flag")


# ================================================= the OTHER half ============
# A ladder that cannot be satisfied is a ladder that gets switched off. These
# fixtures are the reason the gate is landable.
@test("P-PREC PASSES a record that reached only TIER 1 but NAMES the tier-2 "
      "artifact it did not reach, with a reason — honesty about the ceiling "
      "is the graded obligation, not possession of it")
def t_tier1_with_a_named_gap_passes():
    """The live pluto-rx2-8way RP2040 judgement, in the mapping form. It stops
    at a 200 dpi raster and says exactly which free, permissively licensed
    KiCad design it did not fetch and why. This MUST pass, or the gate is
    demanding a fact about the web that no static check can establish."""
    d = scratch(RP2040_HONEST)
    g, det = prec(d)
    eq(g, "PASS", "P-PREC on a tier-1 stop with a NAMED tier-2 gap")
    contains(det, "1/1", "the graded denominator prints")


@test("P-PREC PASSES a record that reached the STRONGEST tier — the part that "
      "did the most work is not punished for having nothing left to name")
def t_strongest_tier_reached_passes():
    """Tier 4 is the bottom of the authority order, so a record reaching it has
    swept the whole ladder and owes no `reached: false` entry. The closure rule
    is `max(reached) < 4`, and this fixture is what pins that boundary: get the
    comparison wrong (`<=`) and the best possible record FAILS."""
    d = scratch("layout_refs:\n"
                "  - tier: 1\n"
                "    artifact: \"datasheet Layout figure, sec 11, p.24\"\n"
                "    reached: true\n"
                "  - tier: 2\n"
                "    artifact: \"vendor EVM design files, SLVUAP7A\"\n"
                "    reached: true\n"
                "  - tier: 3\n"
                "    artifact: \"OSHWLab by-LCSC C2040, copper viewed\"\n"
                "    reached: true\n"
                "  - tier: 4\n"
                "    artifact: \"github.com/example/board KiCad project\"\n"
                "    reached: true\n")
    g, det = prec(d)
    eq(g, "PASS", "P-PREC on a record that reached tier 4")
    contains(det, "1/1", "the graded denominator prints")


@test("the BARE-STRING form stays legal and is counted OWED, never failed — "
      "45 of the fleet's 89 in-scope parts are real searches recorded as prose")
def t_bare_string_is_owed_not_failed():
    """A gate that reds every existing part on day one gets switched off
    (G-VACUOUS's and schema_reader_audit's shared lesson). The bare-string list
    is not an absence — it is the form every dossier in the fleet uses today —
    so it is COUNTED and enumerated, and the board still passes."""
    d = scratch('layout_refs:\n'
                '  - "Hardware design with RP2040 Figure 6, PDF p9"\n')
    g, det = prec(d)
    eq(g, "PASS", "P-PREC on a bare-string layout_refs list")
    contains(det, "0/1", "the graded denominator prints 0")
    contains(det, "1 OWED", "the owed count prints")
    contains(det, "RP2040", "the owed part is ENUMERATED, never a bare number")


@test("the denominator prints on the PASS path too — '0 graded' can never "
      "read as 'all clear' (canon M-COVER)")
def t_denominator_prints_on_the_pass_path():
    """The `jlc_twin` exit-0 class, guarded directly: a board where nothing is
    graded must say so in the same words as a board where everything is."""
    d = scratch("")               # no layout_refs at all
    g, det = prec(d)
    eq(g, "PASS", "P-PREC with no layout_refs anywhere")
    contains(det, "0/1", "graded/scoped prints even when graded is zero")
    contains(det, "OWED", "the owed half prints")
    contains(det, "fleet floors", "the ratchet's numbers print with the row")


@test("P-PREC shares P-LAYOUT's in-scope rule exactly — the two gates cannot "
      "disagree about which parts the fleet owes a precedent for")
def t_scope_is_shared_with_p_layout():
    """A second scope rule would drift from the first, and the denominator is
    the whole point of the ratchet. An out-of-scope part (<= 2 pins, inert
    type) must be counted by NEITHER gate."""
    passive = """mpn: CL05B104KO5NNNC
type: capacitor
package: 0402
footprint: lib:C_0402
pins: {1: A, 2: B}
verified: "datasheet p.2"
"""
    d = scratch(RP2040_HONEST, extra_parts={"CL05B104KO5NNNC": passive})
    rows = audit_rows(d)
    eq(rows["P-PREC"][0], "PASS", "P-PREC grade")
    contains(rows["P-PREC"][1], "1/1",
             "the 2-pin passive is OUT of P-PREC's denominator")
    contains(rows["P-LAYOUT"][1], "1 in-scope",
             "and out of P-LAYOUT's, which is the same rule")


# ==================================================== the ratchet ============
@test("the precedent ratchet is PINNED to the fleet — it may not be lowered "
      "to buy a green run, nor silently lag adoption")
def t_the_precedent_ratchet_is_pinned_to_the_fleet():
    """`adr_bound_provenance`'s CITED_FLOOR/OWED_CEILING precedent, and
    G-VACUOUS's VACUITY_FLOOR trick of measuring from OUTSIDE the gate.

    THIS SWEEP USES ITS OWN READER (canon M1): it walks
    `projects/*/02_parts/*/part.yaml` and applies the in-scope rule directly
    rather than invoking `policy_audit`, so the numbers the floors claim are
    not produced by the code the floors are meant to constrain. It is also
    strictly READ-ONLY — running `policy_audit` over the live projects would
    write `06_build/policy_audit.md` into six boards.

    MEASURED 2026-07-30 at main tip: 89 in-scope parts across 6 boards, 0 with
    a tier-graded record, 89 OWED (45 of them carrying a bare-string list — a
    real search recorded as prose — and 44 carrying nothing at all)."""
    import yaml
    src = POLICY.read_text(encoding="utf-8")
    floor = int(re.search(r"^PREC_GRADED_FLOOR = (\d+)", src, re.M).group(1))
    ceil = int(re.search(r"^PREC_OWED_CEILING = (\d+)", src, re.M).group(1))
    scope = re.search(r"LAYOUT_SCOPE = re\.compile\(r'([^']*)'\s*\n\s*r'([^']*)'",
                      src)
    check(scope, "could not read LAYOUT_SCOPE back out of policy_audit.py")
    rx = re.compile(scope.group(1) + scope.group(2), re.I)

    scoped = graded = owed = 0
    for py in sorted((ROOT / "projects").glob("*/02_parts/*/part.yaml")):
        y = yaml.safe_load(py.read_text(encoding="utf-8-sig")) or {}
        if not (len(y.get("pins") or {}) > 2 or rx.search(str(y.get("type", "")))):
            continue
        scoped += 1
        if any(isinstance(e, dict) for e in (y.get("layout_refs") or [])):
            graded += 1
        else:
            owed += 1
    check(scoped > 0, "the fleet sweep found no in-scope parts — a zero "
                      "denominator is never a pass (canon M-COVER)")
    eq(graded, floor, f"tier-graded parts measured ({scoped} in scope) vs "
                      f"PREC_GRADED_FLOOR — it may only RISE, and it may not "
                      f"lag adoption either")
    eq(owed, ceil, "OWED parts measured vs PREC_OWED_CEILING — it may only FALL")


if __name__ == "__main__":
    main()
