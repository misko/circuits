#!/usr/bin/env python3
"""T1: the ELECTRICAL-INVARIANTS gate (E1, netlist-only) — electrical_invariants.py.

Motivating incident (2026-07-21, usb-hub-3s v1.0, external + red-team review):
the D1 reverse-polarity defect passed ERC, DRC, netlist parity, jlc_twin AND
pin review. Every artifact was consistently WRONG TOGETHER — symbol, footprint,
netlist, board all agreed D1's cathode sat on VBAT_F; only DESIGN INTENT (D1 is
the reverse-polarity block, its cathode feeds VIN) disagreed, and intent was
not executable. This gate makes intent executable: ADRs emit netlist assertions.

RED-VERIFIED (new-gate variant, per tests/README "Adding a regression"):
electrical_invariants.py did not exist before this change — the suite cannot be
run against pre-fix code because the gate could not exist. Instead each
known-bad fixture is a PASSING fixture broken in exactly ONE way, and the test
asserts the checker fails for the RIGHT reason (naming the assertion + the
actual net found). THE INCIDENT itself is pinned as a known-bad fixture reading
the real sealed v1.0 netlist (D1.1 -> VBAT_F).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

EINV = SCRIPTS / "electrical_invariants.py"

# The real sealed v1.0 netlist — read-only evidence, never written.
V10_NET = (ROOT / "projects" / "usb-hub-3s" / "07_releases" /
           "v1.0-2026-07-21" / "source" / "usb_hub_3s.net")


# --------------------------------------------------------------- fixtures
def netlist(nets):
    """nets: {netname: [(ref, pin, pinfunction), ...]} -> a KiCad .net string."""
    blocks = []
    for i, (name, nodes) in enumerate(nets.items(), 1):
        ns = "".join(
            f'(node (ref "{r}") (pin "{p}") (pinfunction "{f}") '
            f'(pintype "passive"))' for r, p, f in nodes)
        blocks.append(f'(net (code "{i}") (name "{name}") {ns})')
    return '(export (version "E") (nets ' + "".join(blocks) + '))'


# A good little board: BATT -> F1(fuse) -> VBAT_F -> Q1(rev-pol FET D->S) -> VIN,
# with a decoupler C1 on VIN and the D1 clamp cathode on VIN.
CLEAN_NETS = {
    "VBAT":   [("F1", "1", "IN"), ("D1", "2", "A")],
    "VBAT_F": [("F1", "2", "OUT"), ("Q1", "1", "D")],
    "VIN":    [("Q1", "2", "S"), ("D1", "1", "K"),
               ("C1", "1", "p1"), ("U1", "1", "VIN")],
    "GATE":   [("Q1", "3", "G")],
    "GND":    [("C1", "2", "p2"), ("U1", "2", "GND")],
}

CLEAN_INV = """\
invariants:
  - assert: pin_on_net
    pin: "D1.1"
    net: VIN
    adr: 0001
    why: "D1 is the reverse-polarity clamp; its cathode must feed VIN"
  - assert: series_chain
    chain: [VBAT, F1, VBAT_F, Q1, VIN]
    through: {Q1: [D, S]}
    adr: 0001
    why: "battery -> fuse -> protected node -> rev-pol FET drain-source -> VIN"
  - assert: net_has_part
    net: VIN
    part_type: capacitor
    min: 1
    adr: 0007
    why: "VIN rail must carry at least one decoupling capacitor"
"""


def project(net_map=None, inv_text=None, net_text=None):
    """Build a scratch project tree so auto-location (06_build/netlists) and
    03_src/rules/electrical_invariants.yaml path resolution are exercised."""
    d = tmpdir("einv_")
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "06_build" / "netlists").mkdir(parents=True)
    if inv_text is not None:
        (d / "03_src" / "rules" / "electrical_invariants.yaml").write_text(inv_text)
    text = net_text if net_text is not None else netlist(net_map or CLEAN_NETS)
    (d / "06_build" / "netlists" / "board.net").write_text(text)
    return d


def einv(d, *extra):
    return run([KPY, EINV, d, *extra])


# ------------------------------------------------------------ clean cases
@test("E-INV passes a netlist satisfying pin_on_net + series_chain + net_has_part")
def t_clean():
    d = project(CLEAN_NETS, CLEAN_INV)
    r = must_pass(einv(d), "E-INV on a clean board")
    contains(r.out, "3 invariants hold", "clean E-INV report")


@test("E-INV is N-A (exit 0) when there is no electrical_invariants.yaml")
def t_na_no_file():
    d = project(CLEAN_NETS, None)
    r = must_pass(einv(d), "E-INV with no invariants file")
    contains(r.out, "N-A", "N-A report")


@test("E-ADR passes when a protection ADR is cited by an invariant")
def t_adr_clean():
    d = project(CLEAN_NETS, CLEAN_INV)
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / "0001-battery-input-protection.md").write_text(
        "---\nid: 0001\nstatus: accepted\n---\n"
        "# 0001 — Battery/input protection: fuse + reverse-polarity FET\n")
    r = must_pass(einv(d, "--adr-coverage"), "E-ADR with the loop closed")
    contains(r.out, "OK", "E-ADR ok report")


# ------------------------------------------------------------ known-bad
@test("E-INV FAILS on THE INCIDENT: D1.1 on VBAT_F, invariant requires VIN",
      kind="known_bad")
def t_incident():
    """usb-hub-3s v1.0 shipped D1.1 (rev-pol clamp cathode) on VBAT_F instead
    of VIN — the defect every other gate missed. Read from the SEALED v1.0
    netlist so this is the incident itself, not a re-creation of it."""
    if not V10_NET.exists():
        raise AssertionError(f"sealed v1.0 netlist missing: {V10_NET}")
    d = project(inv_text=(
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"D1.1\"\n"
        "    net: VIN\n"
        "    adr: 0001\n"
        "    why: \"D1 reverse-polarity clamp cathode must feed VIN, not VBAT_F\"\n"),
        net_text=V10_NET.read_text())
    r = must_fail(einv(d), "E-INV on the D1 incident", "pin_on_net")
    contains(r.out, "D1.1", "incident names the pin")
    contains(r.out, "VBAT_F", "incident names the ACTUAL (wrong) net")
    contains(r.out, "VIN", "incident names the REQUIRED net")


@test("E-INV FAILS a broken series_chain (a missing link)", kind="known_bad")
def t_series_broken():
    """The clean board, broken in one way: Q1's drain is stranded on ORPHAN
    instead of the protected node VBAT_F, so the fuse->FET link is missing."""
    nets = dict(CLEAN_NETS)
    nets["VBAT_F"] = [("F1", "2", "OUT")]           # Q1.D removed from here
    nets["ORPHAN"] = [("Q1", "1", "D")]             # ...stranded here
    d = project(nets, CLEAN_INV)
    r = must_fail(einv(d), "E-INV on a broken chain", "series_chain")
    contains(r.out, "ORPHAN", "chain failure names the wrong net Q1.D reaches")


@test("E-INV FAILS net_has_part when the net has zero parts of that type",
      kind="known_bad")
def t_net_has_part_zero():
    """Assert VBAT carries a decoupling capacitor — it carries only F1 and D1,
    so the count is zero and the assertion must bite."""
    inv = (
        "invariants:\n"
        "  - assert: net_has_part\n"
        "    net: VBAT\n"
        "    part_type: capacitor\n"
        "    min: 1\n"
        "    adr: 0007\n"
        "    why: \"claim VBAT needs a cap it does not have — must fail\"\n")
    d = project(CLEAN_NETS, inv)
    r = must_fail(einv(d), "E-INV net_has_part zero", "net_has_part")
    contains(r.out, "0 capacitor", "reports the actual (zero) count")


@test("E-INV refuses to load an invariant that lacks 'adr:'", kind="known_bad")
def t_missing_adr():
    """Every invariant must cite the ADR that emitted it — a file with an
    invariant lacking adr: is a schema error and must fail to load (exit 2)."""
    inv = (
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"D1.1\"\n"
        "    net: VIN\n"
        "    why: \"no adr field on this invariant\"\n")
    d = project(CLEAN_NETS, inv)
    r = must_fail(einv(d), "E-INV load without adr", "adr")
    contains(r.out, "LOAD ERROR", "reports a load error, not an assertion result")


@test("E-ADR FAILS when a protection ADR emits no invariant (loop open)",
      kind="known_bad")
def t_adr_uncited():
    """The loop-closing discipline: a protection/topology ADR with no invariant
    citing its number is flaggable — the D1 class of defect (an ADR whose
    intent never became a machine check)."""
    inv = (
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"D1.1\"\n"
        "    net: VIN\n"
        "    adr: 0009\n"          # cites a DIFFERENT adr, not 0001
        "    why: \"cites 0009, leaving protection ADR 0001 uncovered\"\n")
    d = project(CLEAN_NETS, inv)
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / "0001-battery-input-protection.md").write_text(
        "---\nid: 0001\nstatus: accepted\n---\n"
        "# 0001 — Battery/input protection: fuse + reverse-polarity FET\n")
    r = must_fail(einv(d, "--adr-coverage"), "E-ADR loop open", "ADR 0001")
    contains(r.out, "loop is not closed", "explains the missing link")


@test("E-ADR sees an uncited protection ADR headed '# ADR-NNNN' (the vacuous-"
      "pass regex bug)", kind="known_bad")
def t_adr_uncited_adr_prefix():
    """The crow re-audits (2026-07-22) found E-ADR passing VACUOUSLY fleet-wide:
    every board heads its ADRs '# ADR-0001 — ...', but _adr_title required
    '# 0001 — ...', so protection_adrs() returned [] and the loop-closer graded
    NOTHING. Same open loop as t_adr_uncited, but with the ADR- heading — this
    MUST still FAIL. RED-VERIFIED: against the pre-fix regex (^#\\s*(\\d{4})...)
    the heading is unrecognized, protection_adrs()==[], and --adr-coverage
    exits 0 (a false PASS) — so must_fail sees exit 0 and this test goes RED."""
    inv = (
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"D1.1\"\n"
        "    net: VIN\n"
        "    adr: 0009\n"
        "    why: \"cites 0009, leaving protection ADR 0001 uncovered\"\n")
    d = project(CLEAN_NETS, inv)
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / "0001-battery-input-protection.md").write_text(
        "---\nid: 0001\nstatus: accepted\n---\n"
        "# ADR-0001 — Battery/input protection: fuse + reverse-polarity FET\n")
    r = must_fail(einv(d, "--adr-coverage"), "E-ADR loop open (ADR- heading)",
                  "ADR 0001")
    contains(r.out, "loop is not closed", "explains the missing link")


# ============================================ part_value (E-INV, 2026-07-25)
# THE INCIDENT (smc0985-cooksense, ab94de3 then 929b089). A safety P0 was found
# — WD_PET, the TPS3823 watchdog heartbeat, had no pull-down, so with the Pi
# unplugged the supervisor self-pulsed, WD_OK never fell and the external
# COOKING CONTACTOR stayed energised indefinitely. The fix landed the pull-down
# AT 100k. TI SLVS165O S6.5 gives I_IL at WDI = 190 uA MAX and the pin SOURCES
# it, so the hold resistor is bounded by I_IL x R < V_IL:
#     R_max = (0.3 x 3.3 V) / 190 uA = 0.99 V / 190 uA ~= 5.2k
#     100k -> the node sits at ~VDD; THE WATCHDOG IS SILENTLY DISABLED
# and ALL THREE E-INV assertions that landed with the fix — one net_has_part
# plus two pin_on_net — PASS on the 100k netlist, because a resistor DOES exist
# on WD_PET with its pads on the right nets. The commit body: "An invariant
# that pins a component's EXISTENCE does not pin its VALUE."
#
# The fixture is the REAL cooksense netlist, broken in exactly one way: the
# value string of R_WDPETPD alone is put back to 100k. Everything else — every
# net, every node, every other component — is the shipped board.
COOK_NET = (ROOT / "projects" / "smc0985-cooksense" / "06_build" /
            "netlists" / "cooksense.net")

# the three assertions that shipped WITH the defective fix, verbatim in shape
WD_TOPOLOGY_INV = """\
invariants:
  - assert: net_has_part
    net: WD_PET
    part_type: resistor
    min: 1
    adr: 0011
    why: "WD_PET must carry a pull resistor or the supervisor self-pulses"
  - assert: pin_on_net
    pin: "R_WDPETPD.1"
    net: WD_PET
    adr: 0011
    why: "the pull sits on the WDI node, not a neighbouring watchdog net"
  - assert: pin_on_net
    pin: "R_WDPETPD.2"
    net: GND
    adr: 0011
    why: "direction DOWN: a defined LOW produces no edge, so the WD expires"
"""

WD_VALUE_INV = """\
invariants:
  - assert: part_value
    part: R_WDPETPD
    max: 5.2k
    adr: 0011
    why: "I_IL(max) 190uA x R < V_IL 0.99V => R <= 5.2k (TI SLVS165O 6.5/7.3.4)"
"""


def cook_netlist(value=None):
    """The real cooksense netlist, optionally with R_WDPETPD's VALUE (and
    nothing else) rewritten — a good input broken in exactly one way."""
    if not COOK_NET.exists():
        raise AssertionError(f"missing real netlist fixture: {COOK_NET}")
    text = COOK_NET.read_text()
    if value is None:
        return text
    i = text.index('(ref "R_WDPETPD")')
    j = text.index("(value ", i)
    k = text.index(")", j)
    return text[:j] + f'(value "{value}"' + text[k:]


@test("E-INV part_value passes the cooksense watchdog pull-down as SHIPPED (1k)")
def t_part_value_clean():
    """The board that is actually correct: R_WDPETPD = 1k, TI's own recommended
    value, 0.19V at I_IL(max) — 81% margin under the 0.99V V_IL bound."""
    d = project(inv_text=WD_VALUE_INV, net_text=cook_netlist())
    r = must_pass(einv(d), "part_value on the shipped 1k")
    contains(r.out, "1 invariants hold", "clean part_value report")


@test("E-INV part_value FAILS THE INCIDENT: the watchdog pull-down at 100k",
      kind="known_bad")
def t_part_value_incident():
    """cooksense's WD_PET fix landed a 100k pull-down where the datasheet
    demands <= 5.2k, and the board looked fixed. RED-VERIFIED (new-kind
    variant): before this change `part_value` was not in the checker's `kinds`
    set, so this exact invariants file raised LOAD ERROR "unknown or missing
    assert kind 'part_value'" — the assertion could not be written at all,
    which is precisely why the 100k board certified clean."""
    d = project(inv_text=WD_VALUE_INV, net_text=cook_netlist("100kΩ"))
    r = must_fail(einv(d), "part_value on the 100k watchdog resistor",
                  "part_value")
    contains(r.out, "R_WDPETPD", "names the part")
    contains(r.out, "100k", "names the ACTUAL value found")
    contains(r.out, "5.2k", "names the REQUIRED bound")


@test("the THREE topology invariants that shipped with the fix PASS on the "
      "100k board — existence is not value", kind="known_bad")
def t_topology_invariants_cannot_see_value():
    """THE POINT OF THE WHOLE KIND, asserted rather than asserted-about. The
    net_has_part + two pin_on_net assertions added with the WD_PET fix all hold
    on the DEFECTIVE netlist: the resistor exists, on WD_PET, to GND. They
    would have certified the broken board — and did. This test FAILS if
    anyone ever "fixes" a topology kind to peek at values, because then the
    demonstration that a separate kind is needed would be false."""
    d = project(inv_text=WD_TOPOLOGY_INV, net_text=cook_netlist("100kΩ"))
    r = must_pass(einv(d), "the topology invariants on the 100k board")
    contains(r.out, "3 invariants hold",
             "all three topology assertions still pass the defective board")
    # ...and the SAME netlist fails the value assertion. Same input, two
    # verdicts: that difference IS the gap part_value closes.
    d2 = project(inv_text=WD_VALUE_INV, net_text=cook_netlist("100kΩ"))
    must_fail(einv(d2), "part_value on the same netlist", "part_value")


@test("part_value decodes SI notation, and m/M are NOT the same multiplier")
def t_part_value_si():
    """`m` is MILLI and `M` is MEGA. A case-folding parser turns a 4.7M
    feedback resistor into 4.7 milliohms and reports a comfortable pass — the
    quiet way a value gate becomes decoration. Also pins the infix form (4k7)
    and unit suffixes (1kOhm / 1kΩ), because a real fleet netlist carries all
    of them for values a human calls the same thing."""
    sys.path.insert(0, str(SCRIPTS))
    from electrical_invariants import parse_si            # noqa: E402
    for text, want in [("100k", 1e5), ("1kOhm", 1e3), ("1kΩ", 1e3),
                       ("4k7", 4700.0), ("0R1", 0.1), ("5.2k", 5200.0),
                       ("1K", 1e3), ("10uF 25V", 1e-5), ("100nF", 1e-7)]:
        got = parse_si(text)
        check(got is not None and abs(got - want) <= abs(want) * 1e-9,
              f"parse_si({text!r}) = {got}, want {want}")
    check(parse_si("1M") == 1e6 and parse_si("1m") == 1e-3,
          f"m/M collapsed: 1M={parse_si('1M')} 1m={parse_si('1m')} — a "
          f"case-folding parser reads a 4.7M resistor as 4.7 milliohms")
    check(parse_si("DNP") is None and parse_si("") is None,
          "an undecodable value must be None (reported as a FAILURE, never "
          "silently passed)")


@test("part_value FAILS a value the netlist carries but the gate cannot decode",
      kind="known_bad")
def t_part_value_undecodable():
    """A value the gate cannot read is a value it cannot vouch for. Silently
    skipping it is the NO-CAD class: an unrecognised input treated as an
    affirmative disposition."""
    d = project(inv_text=WD_VALUE_INV, net_text=cook_netlist("DNP"))
    r = must_fail(einv(d), "part_value on an undecodable value", "part_value")
    contains(r.out, "cannot be decoded", "says why it failed")


@test("part_value refuses to load an assertion that declares NO bound",
      kind="known_bad")
def t_part_value_no_bound():
    """An invariant naming a part and asserting nothing about it is exactly
    the gap this kind closes — it must be a schema error, not a vacuous pass."""
    inv = ("invariants:\n"
           "  - assert: part_value\n"
           "    part: R_WDPETPD\n"
           "    adr: 0011\n"
           "    why: \"names the part but bounds nothing\"\n")
    d = project(inv_text=inv, net_text=cook_netlist())
    r = must_fail(einv(d), "part_value with no bound", "no bound")
    contains(r.out, "LOAD ERROR", "a schema error, not an assertion result")


@test("part_value FAILS a min bound and an equals-with-tolerance", kind="known_bad")
def t_part_value_min_and_equals():
    """The other two bound forms, each broken in one way. `equals` without a
    tolerance is exact; `tolerance_pct` widens it symmetrically."""
    mn = ("invariants:\n"
          "  - assert: part_value\n"
          "    part: R_WDPETPD\n"
          "    min: 470\n"
          "    adr: 0011\n"
          "    why: \"below 470R the WDI pull burns needless quiescent current\"\n")
    d = project(inv_text=mn, net_text=cook_netlist("100R"))
    r = must_fail(einv(d), "part_value min bound", ">= 470")
    eqv = ("invariants:\n"
           "  - assert: part_value\n"
           "    part: R_WDPETPD\n"
           "    equals: 1k\n"
           "    tolerance_pct: 5\n"
           "    adr: 0011\n"
           "    why: \"TI names 1k explicitly in SLVS165O 7.3.4\"\n")
    d2 = project(inv_text=eqv, net_text=cook_netlist("1.2kΩ"))
    must_fail(einv(d2), "part_value equals +/-5%", "part_value")
    # ...and 1.04k IS inside the +/-5% band, so the tolerance is real, not
    # decorative (a band that rejects everything is the same as no band)
    d3 = project(inv_text=eqv, net_text=cook_netlist("1.04kΩ"))
    must_pass(einv(d3), "part_value equals +/-5% on an in-band value")


if __name__ == "__main__":
    sys.exit(main())
