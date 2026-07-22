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
from harness import (KPY, ROOT, SCRIPTS, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

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


if __name__ == "__main__":
    sys.exit(main())
