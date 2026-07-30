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
V10_NET = (ROOT / "archived_projects" / "usb-hub-3s" / "07_releases" /
           "v1.0-2026-07-21" / "source" / "usb_hub_3s.net")   # ARCHIVED 2026-07-28


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
    adr: "0001"
    why: "D1 is the reverse-polarity clamp; its cathode must feed VIN"
  - assert: series_chain
    chain: [VBAT, F1, VBAT_F, Q1, VIN]
    through: {Q1: [D, S]}
    adr: "0001"
    why: "battery -> fuse -> protected node -> rev-pol FET drain-source -> VIN"
  - assert: net_has_part
    net: VIN
    part_type: capacitor
    min: 1
    adr: "0007"
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
        "    adr: \"0001\"\n"
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
        "    adr: \"0007\"\n"
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
        "    adr: \"0009\"\n"          # cites a DIFFERENT adr, not 0001
        "    why: \"cites 0009, leaving protection ADR 0001 uncovered\"\n")
    d = project(CLEAN_NETS, inv)
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / "0001-battery-input-protection.md").write_text(
        "---\nid: 0001\nstatus: accepted\n---\n"
        "# 0001 — Battery/input protection: fuse + reverse-polarity FET\n")
    r = must_fail(einv(d, "--adr-coverage"), "E-ADR loop open", "ADR 0001")
    contains(r.out, "loop is not closed", "explains the missing link")


# ============================== E-ADR vs a WITHDRAWN decision (O8b, 2026-07-28)
def superseded_project(status, adr="0006", by="0015"):
    """A project whose ONLY protection ADR carries `status:` — and no
    invariant citing it. The loop is open by construction; the question the
    fixture asks is whether E-ADR should still be demanding that it close."""
    inv = ("invariants:\n"
           "  - assert: pin_on_net\n"
           "    pin: \"D1.1\"\n"
           "    net: VIN\n"
           "    adr: \"0009\"\n"
           "    why: \"cites 0009 only\"\n")
    d = project(CLEAN_NETS, inv)
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / f"{adr}-mating-strategy.md").write_text(
        f"---\nid: {adr}\ndate: 2026-07-27\nstatus: {status}\n"
        f"tags: [mechanical, topology]\n---\n"
        f"# {adr} — SMA->SMP adapters on the Pluto; edge-launch SMP\n")
    (dec / f"{by}-sma-cables.md").write_text(
        f"---\nid: {by}\ndate: 2026-07-27\nstatus: accepted\n"
        f"tags: [mechanical]\n---\n"
        f"# {by} — SMA CABLES to the Pluto; five true SMA jacks\n")
    return d


@test("E-ADR does not demand an invariant from a SUPERSEDED protection ADR")
def t_adr_superseded_is_skipped():
    """THE DECLARED GAP O8b (2026-07-28). protection_adrs() excluded only
    `0000-example` and never read `status:`, so a topology ADR whose decision
    had been REVERSED was still required to emit a machine-checkable
    invariant. pluto-cal-switch ADR-0006 (SMA->SMP adapters on the Pluto) was
    reversed outright by ADR-0015 (SMA cables, five true SMA jacks): there is
    no topology left to assert, and E-ADR reported FAIL 11/12 for a hole that
    cannot be filled.

    It was declared as a gap rather than gamed by retagging the ADR — the
    right call, and the reason the fix belongs in the GATE: deleting a live
    ADR's `topology` tag to silence a checker would have left the next reader
    a lie in the decision record.

    MEASURED on the real tree: pluto-cal-switch goes from 12 protection ADRs
    (11 cited, FAIL) to 10 (10 cited, PASS). The two dropped are 0006
    (superseded-by-0015) and 0004 (superseded-by-0016).

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    electrical_invariants.py swapped back in this fails with `E-ADR on a
    superseded ADR should have exited 0, got 1` and the report naming
    `ADR 0006 ... the intent loop is not closed`. Restored, it passes.
    """
    d = superseded_project("superseded-by-0015")
    r = must_pass(einv(d, "--adr-coverage"), "E-ADR on a superseded ADR")
    check("ADR 0006" not in r.out,
          f"a withdrawn decision is still being demanded:\n{r.out}")


@test("E-ADR STILL FAILS a protection ADR that is not superseded — the skip "
      "reads the STATUS, not the presence of the word", kind="known_bad")
def t_adr_non_superseded_still_fails():
    """The other half of the property, and the one that matters: a status read
    too loosely turns the whole gate off. Same fixture, same open loop, the
    ONE difference being `status: accepted`.

    The three shapes here are the ones that could go wrong, each broken in
    exactly one way from the passing case:
      * `accepted` — the ordinary live ADR. MUST still FAIL.
      * `accepted   # proposed | accepted | rejected | superseded-by-0012` —
        THE TEMPLATE'S OWN PLACEHOLDER, on 10 live ADRs across the fleet. The
        word `superseded` is present, in a COMMENT. Reading it as the status
        would silently un-grade a tenth of the fleet's ADRs. This is the S-VER
        defect verbatim (a `verified:` inside a comment shadowing the real
        key), which is why it is asserted here rather than trusted.
      * `proposed` — not yet decided is not withdrawn.
    """
    for status in ("accepted",
                   "accepted   # proposed | accepted | rejected | "
                   "superseded-by-0012",
                   "proposed"):
        d = superseded_project(status)
        r = must_fail(einv(d, "--adr-coverage"),
                      f"E-ADR on status={status!r}", "ADR 0006")
        contains(r.out, "loop is not closed", f"status={status!r} report")


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
        "    adr: \"0009\"\n"
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
    adr: "0011"
    why: "WD_PET must carry a pull resistor or the supervisor self-pulses"
  - assert: pin_on_net
    pin: "R_WDPETPD.1"
    net: WD_PET
    adr: "0011"
    why: "the pull sits on the WDI node, not a neighbouring watchdog net"
  - assert: pin_on_net
    pin: "R_WDPETPD.2"
    net: GND
    adr: "0011"
    why: "direction DOWN: a defined LOW produces no edge, so the WD expires"
"""

WD_VALUE_INV = """\
invariants:
  - assert: part_value
    part: R_WDPETPD
    max: 5.2k
    adr: "0011"
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
           "    adr: \"0011\"\n"
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
          "    adr: \"0011\"\n"
          "    why: \"below 470R the WDI pull burns needless quiescent current\"\n")
    d = project(inv_text=mn, net_text=cook_netlist("100R"))
    r = must_fail(einv(d), "part_value min bound", ">= 470")
    eqv = ("invariants:\n"
           "  - assert: part_value\n"
           "    part: R_WDPETPD\n"
           "    equals: 1k\n"
           "    tolerance_pct: 5\n"
           "    adr: \"0011\"\n"
           "    why: \"TI names 1k explicitly in SLVS165O 7.3.4\"\n")
    d2 = project(inv_text=eqv, net_text=cook_netlist("1.2kΩ"))
    must_fail(einv(d2), "part_value equals +/-5%", "part_value")
    # ...and 1.04k IS inside the +/-5% band, so the tolerance is real, not
    # decorative (a band that rejects everything is the same as no band)
    d3 = project(inv_text=eqv, net_text=cook_netlist("1.04kΩ"))
    must_pass(einv(d3), "part_value equals +/-5% on an in-band value")


# ================================================ `adr:` YAML OCTAL (2026-07-27)
# THE DEFECT, reported by the pluto-cal-switch agent. A zero-padded ADR
# reference written BARE is a YAML 1.1 OCTAL literal:
#     adr: 0011 -> the int 9  -> _norm_adr -> "0009"
#     adr: 0012 -> the int 10 -> _norm_adr -> "0010"
#     adr: 0010 -> the int 8  -> _norm_adr -> "0008"
#     adr: 0008 -> the STRING "0008" (8 is not an octal digit; it survives)
# So it is not a SKIP — the invariant silently satisfies the WRONG ADR, and
# E-ADR then credits an ADR that emitted nothing while reporting the intended
# one as uncited. Measured on this tree before the fix: the pcb-design TEMPLATE
# (`skills/pcb-design/templates/03_src/rules/electrical_invariants.yaml`, the
# source of truth every new board is seeded from) and the pluto-cal-switch copy
# taken from it both wrote `adr: 0011` and both RESOLVED IT TO 0009. The live
# pluto-cal-switch file cites 0011 AND 0012 — the two the reporter named.
#
# The fix REJECTS the bare form rather than coercing it, because coercion is
# impossible after the fact: safe_load has already turned 0011 into 9, and
# `adr: 9` and `adr: 0011` are then the same object.


def adr_octal_project(inv_adr, adr_file="0009-input-protection.md",
                      adr_head="# ADR-0009 — input protection: reverse polarity"):
    """A project with ONE protection ADR and one invariant citing `inv_adr`."""
    d = project(CLEAN_NETS, inv_text=(
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"D1.1\"\n"
        "    net: VIN\n"
        f"    adr: {inv_adr}\n"
        "    why: \"the reverse-polarity clamp cathode must feed VIN\"\n"))
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    (dec / adr_file).write_text(f"{adr_head}\n\ntags: protection\n")
    return d


@test("E-ADR REFUSES `adr: 0011`, which YAML resolves to ADR 0009 — the "
      "silent-wrong-answer, not a skip", kind="known_bad")
def t_adr_octal_misresolves():
    """RED-VERIFIED against pre-fix code (git show 5054b07:...
    electrical_invariants.py, 2026-07-27): the fixture declares ONE protection ADR — 0009 — and an
    invariant citing `adr: 0011`, an ADR that does not exist in the fixture at
    all. Pre-fix output, verbatim:

        E-ADR OK: every protection/topology ADR is cited by an invariant
        exit=0

    i.e. the gate went GREEN on a citation of a nonexistent document, because
    `0011` had already become 9 and been re-padded to "0009". must_fail sees
    exit 0 and this test goes RED. Post-fix it exits 2 naming the line and the
    misresolution."""
    d = adr_octal_project("0011")
    r = must_fail(einv(d, "--adr-coverage"), "E-ADR on a YAML-octal adr",
                  "0011")
    contains(r.out, "0009", "names the ADR it would have silently satisfied")
    contains(r.out, "octal", "names the mechanism, not just the symptom")
    check("E-ADR OK" not in r.out,
          "pre-fix behaviour returned: the gate still reports OK on a citation "
          "of an ADR that does not exist")


@test("E-INV REFUSES a bare zero-padded `adr:` on the MAIN grading path too, "
      "not only under --adr-coverage", kind="known_bad")
def t_adr_octal_main_path():
    """The load-time check guards every consumer of the file, so the E-INV run
    that grades the netlist rejects it as well. Without this the two entry
    points would disagree about whether the same file is loadable."""
    d = adr_octal_project("0011")
    r = must_fail(einv(d), "E-INV on a YAML-octal adr", "LOAD ERROR")
    contains(r.out, "0011", "names the offending literal")
    contains(r.out, "adr", "names the field")


@test("the rejection is written at the width of the CLASS: `adr: 0008` is "
      "refused too, though it happens to survive", kind="known_bad")
def t_adr_octal_class_width():
    """Canon M-WIDTH. `0008` is not a valid octal literal, so PyYAML declines
    to convert it and it arrives as the string "0008" — correct, today, purely
    because of which digits it contains. A rule scoped to the spellings that
    currently break leaves the class open and it re-enters at the next ADR
    number (this is the `netclasses` -> `everything a pcbnew save drops`
    shape). The message must SAY that is why, so the reader does not read the
    rejection as a false positive.
    RED-VERIFIED: pre-fix, `adr: 0008` loads and E-ADR exits 0."""
    d = adr_octal_project("0008", "0008-thermal.md",
                          "# ADR-0008 — input protection thermal path")
    r = must_fail(einv(d, "--adr-coverage"), "E-ADR on adr: 0008", "0008")
    contains(r.out, "not an octal digit", "explains WHY this one survives")


@test("a QUOTED adr and an UNPADDED adr both still load — the fix rejects the "
      "hazard, not the field")
def t_adr_quoted_and_unpadded_ok():
    """A rule that rejected every ADR reference would also be 'safe' and would
    be useless. Both legal spellings must keep working, and `adr: 11` must
    normalise to the same "0011" that `adr: "0011"` does."""
    d = adr_octal_project('"0009"')
    must_pass(einv(d, "--adr-coverage"), "E-ADR on a quoted adr")
    d2 = adr_octal_project("9")
    must_pass(einv(d2, "--adr-coverage"), "E-ADR on an unpadded adr")


# ======================================= E-ADR parse failure (M-COVER, 2026-07-27)
@test("E-ADR NAMES a parse failure instead of reporting every ADR uncited",
      kind="known_bad")
def t_adr_coverage_load_error_names_itself():
    """THE DEFECT: `adr_coverage()` caught LoadError and set `cited = set()`
    with the comment "a broken file cites nothing". True, and the wrong
    verdict — one weak `why:` field produced a report of TEN uncited protection
    ADRs that never once mentioned the parse error, sending the reader after
    ten phantom coverage holes instead of one typo. Canon M-COVER: input a gate
    cannot parse is a FAIL that NAMES ITSELF, never a zero.

    RED-VERIFIED against pre-fix code (5054b07): the fixture has THREE
    protection ADRs and an invariants file whose only defect is a `why:` under
    5 characters. Pre-fix, --adr-coverage exits 1 and prints three "no
    invariant cites adr:" findings with no mention of `why:` or of a load error
    at all — so the `LOAD ERROR` / `why` assertions below both fail. Post-fix
    it exits 2 and names the field.

    AND IT IS NOT SYNTHETIC. Run pre-fix against the real `projects/usb-hub-3s`,
    whose invariants file uses the older pre-checker schema:
        E-ADR FAIL:
          ADR 0001 (Battery/input protection: ...) is a protection/topology ADR
          but no invariant cites adr: 0001 — the intent loop is not closed
    That board's file contains twelve assertions citing ADR 0001. The gate
    reported the opposite of the truth, and named no parse error."""
    d = project(CLEAN_NETS, inv_text=(
        "invariants:\n"
        "  - assert: pin_on_net\n"
        "    pin: \"D1.1\"\n"
        "    net: VIN\n"
        "    adr: \"0001\"\n"
        "    why: \"x\"\n"))            # the ONE defect: too weak to be evidence
    dec = d / "01_docs" / "decisions"
    dec.mkdir(parents=True)
    for n, t in (("0001", "input protection: reverse polarity"),
                 ("0002", "protection: overvoltage clamp"),
                 ("0003", "power topology: the buck selection")):
        (dec / f"{n}-x.md").write_text(f"# ADR-{n} — {t}\n\ntags: protection\n")
    r = must_fail(einv(d, "--adr-coverage"), "E-ADR on an unparseable file",
                  "LOAD ERROR")
    contains(r.out, "why", "names the FIELD that failed to parse")
    check("no invariant cites" not in r.out,
          "pre-fix behaviour returned: a parse failure is still being reported "
          "as N uncited ADRs")
    check(r.rc == 2, f"a parse failure must exit 2 (config error), got {r.rc}")


@test("E-ADR prints an N/M coverage denominator (canon G-COVER)")
def t_adr_coverage_denominator():
    """G-COVER: a verdict with no denominator hides its own blind spot. E-ADR
    printed a bare 'every protection/topology ADR is cited by an invariant'
    with no count at all, so a board with ZERO protection ADRs and a board with
    twelve read identically."""
    d = adr_octal_project('"0009"')
    r = must_pass(einv(d, "--adr-coverage"), "E-ADR coverage line")
    contains(r.out, "1/1", "names how many ADRs were graded, and of how many")
    contains(r.out, "electrical_invariants.yaml",
             "names the artifact it graded (G-INPUT)")



# ==================================== node_level (E-INV, ADR-0007, 2026-07-29)
# THE INCIDENT, and it is mine. cooksense v1.7 added a divider to take U_EXP.1
# off a 5 V node, sized as if EFUSE_FLT_N were a stiff 5 V source. It is
# OPEN-DRAIN behind R_PG = 100k, so the real chain is 100k + 10k over 22k and
# the pin sat at 0.833 V against a 2.640 V threshold: the eFuse fault readback
# was DEAD. E-INV passed 136/136 throughout, because the assertions said the
# divider RESISTORS EXISTED at the right values. Existence was true; the claim
# the divider was written to guarantee was false.
#
# `node_level` asserts the OUTCOME instead: the level the node actually reaches,
# against the threshold of the pin that reads it.

def _nl_comps(nets, values):
    """netlist() + the (comp ...) value records node_level needs."""
    body = netlist(nets)
    comps = "".join(f'(comp (ref "{r}") (value "{v}"))' for r, v in values.items())
    return body.replace("(nets ", "(components " + comps + ") (nets ", 1)


def _parts(d, code, el):
    pd = d / "02_parts" / "PART"
    pd.mkdir(parents=True, exist_ok=True)
    (pd / "part.yaml").write_text(
        "mpn: PART\nsourcing:\n  lcsc: %s\n%s" % (code, el))


# EFUSE_FLT_N --R_PG 100k--> V5   and  --R_T 10k--> TAP --R_B 22k--> GND
# U_RX.1 reads TAP.
NL_NETS = {
    "V5":       [("R_PG", "2", "p2")],
    "EFUSE_N":  [("R_PG", "1", "p1"), ("R_T", "1", "p1")],
    "TAP":      [("R_T", "2", "p2"), ("R_B", "1", "p1"), ("U_RX", "1", "GPB0")],
    "GND":      [("R_B", "2", "p2")],
}
NL_EL = """electrical:
  vdd: 3.3
  pins:
    "1": {kind: input, v_ih_min_frac_vdd: 0.8, v_il_max_frac_vdd: 0.2}
"""
NL_INV = """\
supplies: {V5: 5.0}
invariants:
  - assert: node_level
    net: TAP
    receiver: U_RX.1
    driver_state: released
    must_be: logic_high
    adr: "0007"
    why: "the readback must reach a valid logic high or the flag is dead"
"""


def _nl_project(values, el=NL_EL):
    d = project(net_text=_nl_comps(NL_NETS, values), inv_text=NL_INV)
    _parts(d, "CRX", el)
    return d


@test("E-INV node_level FAILS THE INCIDENT: a divider behind a 100k pull-up "
      "reads 0.833 V against a 2.640 V threshold", kind="known_bad")
def t_node_level_incident():
    """RED-VERIFIED: this is the exact network cooksense v1.7 shipped, and the
    three part_value/pin_on_net assertions that shipped beside it all PASS on
    it — which is why the defect survived to a pre-seal review battery."""
    d = _nl_project({"R_PG": "100k", "R_T": "10k", "R_B": "22k", "U_RX": "CRX"})
    r = must_fail(einv(d), "node_level on the shipped divider")
    contains(r.out, "0.833", "reports the level it computed")
    contains(r.out, "2.640", "reports the threshold it graded against")
    contains(r.out, "R_PG=100k", "names the pull-up that makes the chain 132k")


@test("E-INV node_level PASSES the recommended fix: pull-up on 3V3, no divider")
def t_node_level_fixed():
    """The other half of discrimination. A check that only ever fails ranks
    nothing: moving the pull-up to a 3.3 V rail and deleting the divider puts
    the pin at the rail, and node_level must say so."""
    nets = {"V3": [("R_PG", "2", "p2")],
            "TAP": [("R_PG", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_B", "2", "p2"), ("R_B", "1", "p1")]}
    inv = NL_INV.replace("supplies: {V5: 5.0}", "supplies: {V3: 3.3}")
    d = project(net_text=_nl_comps(nets, {"R_PG": "100k", "R_B": "1k",
                                          "U_RX": "CRX"}), inv_text=inv)
    _parts(d, "CRX", NL_EL)
    must_pass(einv(d), "node_level on the recommended fix")


@test("E-INV node_level REFUSES to reach a rail through a CAPACITOR",
      kind="known_bad")
def t_node_level_no_cap_path():
    """MY OWN BUG, caught on the first real run against cooksense and fixtured
    so it cannot come back. The walker traversed `CE1=220u` — a 220 uF bulk
    capacitor — because parse_si decodes "220u" and CE1 is a 2-pin part, and it
    printed a CONFIDENT WRONG PATH (2.500 V via R_FLTDIVB + CE1). A DC series
    path may only run through resistance.

    Here the ONLY route to a rail is through C_UP. Pre-fix the walker crossed
    the cap and computed a level, which is the failure this fixture pins: not a
    wrong number, but ANY number.

    EXPECTATION UPDATED 2026-07-29, and the property it guards is UNCHANGED.
    This fixture used to assert `UNREACHED`. The restrictive-default branch now
    resolves the node the honest DC way — with every driver released, a node
    whose only resistive path is a pull-down to GND sits AT GND — so the verdict
    is now a graded 0.000 V that FAILS the logic_high assert. That is strictly
    more informative than UNREACHED and it was always the correct DC answer.
    What this fixture exists to prove is untouched and is asserted below: the
    capacitor is still not crossed, `C_UP` never appears in a path, and no
    2.500 V divider is invented. Only the verdict changed, not the refusal."""
    nets = {"V5":  [("C_UP", "2", "p2")],
            "TAP": [("C_UP", "1", "p1"), ("R_B", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_B", "2", "p2")]}
    d = project(net_text=_nl_comps(nets, {"C_UP": "220u", "R_B": "22k",
                                          "U_RX": "CRX"}), inv_text=NL_INV)
    _parts(d, "CRX", NL_EL)
    r = must_fail(einv(d), "node_level with only a capacitive path to a rail")
    check("C_UP" not in r.out,
          f"the capacitor must not appear in a DC path:\n{r.out}")
    check("2.500" not in r.out,
          f"the pre-fix divider-through-the-capacitor must not be computed:\n{r.out}")
    contains(r.out, "no resistive path to any declared rail",
             "says WHY it did not reach a rail")


@test("E-INV node_level reports UNREACHED when the receiver declares no "
      "thresholds — it does not assume one", kind="known_bad")
def t_node_level_unreached():
    """canon M-COVER. A missing datasheet fact must be NAMED, not defaulted:
    a check that invents a threshold is worse than one that admits it cannot
    grade."""
    d = _nl_project({"R_PG": "100k", "R_T": "10k", "R_B": "22k", "U_RX": "CRX"},
                    el="")                      # dossier with no electrical:
    r = must_fail(einv(d), "node_level with no receiver thresholds")
    contains(r.out, "UNREACHED", "says it could not grade")
    contains(r.out, "electrical", "names the block that would fix it")


@test("E-INV rejects a `supplies:` rail net that is NOT in the netlist, and "
      "names the near-miss", kind="known_bad")
def t_supplies_net_absent():
    """THE COOKSENSE INCIDENT VERBATIM, 2026-07-29. The invariants file declared
    `supplies: {N3V3: 3.3}` — the tsx AUTHOR-PREFIX form — and no net called
    `N3V3` exists in the netlist. _grade_node_level filters supplies to nets it
    can see, so the 3V3 rail was INVISIBLE to every node_level grade on the
    board and nothing said so.

    RED-VERIFIED against the pre-fix checker: it failed, but for the WRONG
    REASON — "no supply rail voltages declared — add `supplies:`" — when
    `supplies:` was in fact declared and merely misspelt. A verdict that sends
    the author to add a block they already wrote is a false lead, so this
    fixture pins the DIAGNOSIS, not just the exit code."""
    nets = {"3V3": [("R_PG", "2", "p2")],
            "TAP": [("R_PG", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_B", "2", "p2"), ("R_B", "1", "p1")]}
    inv = NL_INV.replace("supplies: {V5: 5.0}", "supplies: {N3V3: 3.3}")
    d = project(net_text=_nl_comps(nets, {"R_PG": "100k", "R_B": "1k",
                                          "U_RX": "CRX"}), inv_text=inv)
    _parts(d, "CRX", NL_EL)
    r = must_fail(einv(d), "a supplies: rail that is not a net")
    contains(r.out, "N3V3", "names the rail it could not find")
    contains(r.out, "'3V3'", "suggests the net the author meant")


@test("E-INV catches a misnamed rail even when ANOTHER rail resolves — the "
      "silent half of the trap", kind="known_bad")
def t_supplies_net_absent_while_another_resolves():
    """The sharper case, and the reason this is graded whenever `supplies:` is
    present at all rather than only when a grade comes up short. With ONE valid
    rail the pre-fix checker PASSES: it finds V5, computes a level, reports
    green, and the misnamed second rail is simply never mentioned. Nothing in
    the output distinguishes this board from one whose supplies are all correct.

    RED-VERIFIED: pre-fix this fixture exits 0."""
    nets = {"V5":  [("R_PG", "2", "p2")],
            "3V3": [("R_B2", "2", "p2")],
            "TAP": [("R_PG", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_B", "2", "p2"), ("R_B", "1", "p1"),
                    ("R_B2", "1", "p1")]}
    inv = NL_INV.replace("supplies: {V5: 5.0}",
                         "supplies: {V5: 5.0, N3V3: 3.3}")
    d = project(net_text=_nl_comps(nets, {"R_PG": "100k", "R_B": "1k",
                                          "R_B2": "1k", "U_RX": "CRX"}),
                inv_text=inv)
    _parts(d, "CRX", NL_EL)
    r = must_fail(einv(d), "a misnamed rail beside a resolving one")
    contains(r.out, "N3V3", "names the misnamed rail even though V5 resolved")


@test("E-INV node_level resolves a SELF-SUPPLIED receiver, whose netlist value "
      "is an MPN and not an LCSC code", kind="known_bad")
def t_node_level_mpn_join():
    """cooksense 2026-07-29, and the cost was that the gate could not express
    the very margin the board was being re-spun to fix. `_load_part_electrical`
    joined dossiers to the netlist by LCSC code only. That holds for parts this
    pipeline SOURCES — but a SELF-SUPPLIED part has no LCSC to carry, so its
    netlist value is its MPN, and the join silently missed it. The 13 reed
    relays carry `DIP05-1A72-13L`, so every coil-driver `node_level` came back
    UNREACHED even though the margin had been computed by hand and shown to PASS
    at +0.494 V on the new driver where the superseded one FAILED.

    UNREACHED was at least honest — it did not invent a verdict (that is
    M-COVER working). But an honest refusal on a fact the tree DOES carry is
    still a gate that cannot grade its board.

    RED-VERIFIED: with the MPN and directory-name keys removed from the join,
    this fixture reports `UNREACHED ... (code 'DIP05-1A72-13L') declares no
    input thresholds` and exits 1."""
    nets = {"V3": [("R_PG", "2", "p2")],
            "TAP": [("R_PG", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_B", "2", "p2"), ("R_B", "1", "p1")]}
    inv = NL_INV.replace("supplies: {V5: 5.0}", "supplies: {V3: 3.3}")
    d = project(net_text=_nl_comps(nets, {"R_PG": "100k", "R_B": "1k",
                                          "U_RX": "DIP05-1A72-13L"}),
                inv_text=inv)
    pd = d / "02_parts" / "DIP05-1A72-13L"
    pd.mkdir(parents=True, exist_ok=True)
    # a SELF-SUPPLIED dossier: `mpn:` and deliberately NO `sourcing.lcsc`
    (pd / "part.yaml").write_text("mpn: DIP05-1A72-13L\n" + NL_EL)
    must_pass(einv(d), "node_level on a self-supplied receiver")


@test("E-INV the widened join does NOT let a directory name shadow another "
      "dossier's real LCSC code", kind="known_bad")
def t_node_level_join_precedence():
    """The risk the widening introduces, fixtured so the cure cannot become the
    next defect. Once MPNs and DIRECTORY NAMES are join keys, a directory could
    collide with a genuine LCSC code and answer a lookup that belongs to another
    part — swapping in the wrong part's thresholds, which is a CONFIDENT WRONG
    verdict rather than an UNREACHED one.

    Here a decoy dossier declares `mpn: CRX` — the LCSC code of the real
    receiver — and a threshold that flips the grade: `v_ih_min: 5.0`, which the
    3.300 V node cannot reach. (A FRACTION does not discriminate here and my
    first attempt at this fixture used one: 0.99 x 3.3 = 3.267 V, and the node
    sits AT the rail on 3.300, so it passed with either dossier answering. A
    fixture that cannot tell the two apart proves nothing.) It lives in
    `ZDECOY/` so that it
    sorts AFTER the real `PART/` dossier: that ordering is the whole point,
    because a single-pass loader with plain assignment is last-write-wins and
    would hand the lookup to the decoy. Precedence is explicit in the loader —
    sourcing codes are applied AFTER name-derived keys — so the real dossier
    wins whatever the glob order.

    RED-VERIFIED: collapsing the two passes into one with plain assignment makes
    the decoy answer the lookup and this fixture fails on the 0.99 threshold."""
    nets = {"V3": [("R_PG", "2", "p2")],
            "TAP": [("R_PG", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_B", "2", "p2"), ("R_B", "1", "p1")]}
    inv = NL_INV.replace("supplies: {V5: 5.0}", "supplies: {V3: 3.3}")
    d = project(net_text=_nl_comps(nets, {"R_PG": "100k", "R_B": "1k",
                                          "U_RX": "CRX"}), inv_text=inv)
    _parts(d, "CRX", NL_EL)                      # the real, SOURCED dossier
    decoy = d / "02_parts" / "ZDECOY"            # sorts AFTER PART/
    decoy.mkdir(parents=True, exist_ok=True)
    (decoy / "part.yaml").write_text(            # its MPN collides with the code
        "mpn: CRX\nelectrical:\n  vdd: 3.3\n  pins:\n"
        '    "1": {kind: input, v_ih_min: 5.0}\n')
    must_pass(einv(d), "node_level with a decoy dossier named after the code")


@test("E-INV node_level grades a RESTRICTIVE DEFAULT — pull-down only, no rail "
      "path — instead of reporting UNREACHED", kind="known_bad")
def t_node_level_restrictive_default():
    """The mirror of the pull-up case, missing from the start. `_grade_node_level`
    special-cased "no path to GND -> pulled to the rail" and had no branch for
    "no path to a rail -> pulled to GND", so every RESTRICTIVE DEFAULT in the
    fleet graded UNREACHED.

    That is not a cosmetic gap. cooksense ADR-0019 adds ELEVEN restrictive
    defaults, and ADR-0025's unfitted safety inputs are the same shape — the
    pull-down alone holds the node, hand-measured at 1.15 mV against V_T-(min)
    0.500 V, and it is the fact the whole scope reduction turns on. A board
    agent reported it as a gate limitation it would not work around, which is
    the right call and is why this exists.

    RED-VERIFIED: with the branch removed the fixture reports `UNREACHED
    node_level (ADR 0007): no series-RESISTIVE path from 'TAP' to any declared
    rail` and exits 1."""
    nets = {"V5":  [("C_V5", "2", "p2")],       # rail EXISTS, reachable only via a cap
            "TAP": [("R_PD", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_PD", "2", "p2"), ("C_V5", "1", "p1")]}
    inv = NL_INV.replace("must_be: logic_high", "must_be: logic_low")
    d = project(net_text=_nl_comps(nets, {"R_PD": "10k", "C_V5": "100n",
                                          "U_RX": "CRX"}), inv_text=inv)
    _parts(d, "CRX", NL_EL)
    must_pass(einv(d), "node_level on a pull-down-only node asserted logic_low")


@test("E-INV the restrictive-default branch still FAILS a node asserted "
      "logic_high — it grades, it does not excuse", kind="known_bad")
def t_node_level_restrictive_default_discriminates():
    """The other half. A branch that resolves a level must be able to REFUSE
    one: the same pull-down-only node asserted `logic_high` reads 0.000 V
    against a 2.640 V threshold and must fail by name. Without this the new
    branch would be a way to make any pull-down node pass."""
    nets = {"V5":  [("C_V5", "2", "p2")],
            "TAP": [("R_PD", "1", "p1"), ("U_RX", "1", "GPB0")],
            "GND": [("R_PD", "2", "p2"), ("C_V5", "1", "p1")]}
    d = project(net_text=_nl_comps(nets, {"R_PD": "10k", "C_V5": "100n",
                                          "U_RX": "CRX"}), inv_text=NL_INV)
    _parts(d, "CRX", NL_EL)
    r = must_fail(einv(d), "a pull-down-only node asserted logic_high")
    contains(r.out, "0.000", "reports the level it computed")
    contains(r.out, "2.640", "reports the threshold it graded against")
    contains(r.out, "restrictive default", "names what is holding the node")


if __name__ == "__main__":
    sys.exit(main())
