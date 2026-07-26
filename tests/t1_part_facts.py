#!/usr/bin/env python3
"""T1: P-FACT — the board + release graded against every part's OWN facts.

`02_parts/<MPN>/part.yaml` is the most expensive artifact this pipeline makes:
187 hand-verified, datasheet-cited fact files. It is almost entirely UNREAD BY
MACHINES — only `pins:`, `escape:`, `layout:`, `type:` and `sourcing:` reach a
gate, and everything else a human learned by reading 60 pages lands in
`gotchas:`, free prose nothing can check.

EVERY FIXTURE BELOW IS A FACT THAT WAS CORRECTLY WRITTEN DOWN AND BECAME A
DEFECT ANYWAY:

  "PAD 1 IS NEGATIVE - polarity is a PART FACT"  the XT60 shipped REVERSED
  "keep off the JLC-assembly BOM"                the part reached the BOM
  "no copper under the opto"                     the LTV-817S 5kV barrier:
                                                 cooksense shipped 0.175 mm
  "MSL 3, 168h floor life"                       the consigned XU316 shipped
                                                 with ZERO MSL text in the
                                                 order paperwork

A fact that is written down and never read is indistinguishable from a fact
nobody knew.

RED-VERIFIED (new-gate variant, per tests/README "Adding a regression"):
`part_facts_check.py` did not exist before this change, so there is no pre-fix
code to run the suite against — the gate could not exist. Each known-bad
fixture is therefore a PASSING fixture broken in exactly ONE way, and each
asserts the checker fails for the RIGHT reason (naming the part, the declared
fact, and the artifact that contradicts it). Two extra teeth beyond that
minimum: `t_facts_reach_the_refs` proves an assertion that reaches no ref is
reported rather than passing, and `t_deferred_is_named` proves the ONE kind
this checker cannot yet grade says so out loud instead of going quiet.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, check, contains, main,  # noqa: E402
                     must_fail, must_pass, not_contains, run, test, tmpdir)

PFACT = FAB_SCRIPTS / "part_facts_check.py"


# --------------------------------------------------------------- fixtures
def release(parts, bom, cpl=None, netlist=None, order=None):
    """A scratch release tree: 02_parts/<MPN>/part.yaml + fab/ + paperwork.

    parts: {mpn: yaml_text}
    bom  : [(comment, "R1,R2", footprint, mpn, lcsc)]
    cpl  : [designator]
    """
    d = tmpdir("pfact_")
    (d / "02_parts").mkdir(parents=True)
    for mpn, text in parts.items():
        (d / "02_parts" / mpn).mkdir()
        (d / "02_parts" / mpn / "part.yaml").write_text(text)
    (d / "fab").mkdir()
    lines = ["Comment,Designator,Footprint,MPN,LCSC"]
    for c, des, fp, mpn, lcsc in bom:
        lines.append(f'{c},"{des}",{fp},{mpn},{lcsc}')
    (d / "fab" / "bom.csv").write_text("\n".join(lines) + "\n")
    cl = ["Designator,Val,Package,Mid X,Mid Y,Layer,Rotation"]
    for r in (cpl if cpl is not None else [b[1] for b in bom]):
        for one in str(r).split(","):
            cl.append(f"{one},x,y,0,0,top,0")
    (d / "fab" / "cpl.csv").write_text("\n".join(cl) + "\n")
    if netlist is not None:
        (d / "06_build" / "netlists").mkdir(parents=True)
        (d / "06_build" / "netlists" / "b.net").write_text(netlist)
    (d / "ORDER_README.md").write_text(order if order is not None else
                                       "# Order\nNothing special.\n")
    return d


def netlist_of(pad1_nets):
    """{ref: net} -> a minimal exported netlist with each ref's pad 1."""
    blocks = []
    for i, (net, refs) in enumerate(pad1_nets.items(), 1):
        nodes = "".join(f'(node (ref "{r}") (pin "1"))' for r in refs)
        blocks.append(f'(net (code "{i}") (name "{net}") {nodes})')
    return '(export (version "E") (nets ' + "".join(blocks) + '))'


def pfact(d, *extra):
    return run([KPY, PFACT, d, *extra])


XT60_OK = """\
mpn: XT60PW-M
type: connector
asserts:
  - assert: pad1_net_polarity
    pad: 1
    polarity: negative
    why: "PAD 1 IS NEGATIVE - polarity is a PART FACT (AMASS drawing fig 2);
      a reversed XT60 already shipped once and no ERC can see it"
sourcing: {lcsc: C98732}
"""

WD_OK = """\
mpn: TPS3823-33DBVR
type: supervisor
asserts:
  - assert: value
    equals: 1k
    tolerance_pct: 5
    why: "I_IL(max) 190uA x R < V_IL 0.99V => R <= 5.2k; TI SLVS165O 7.3.4"
sourcing: {lcsc: C7719}
"""


# ------------------------------------------------------------ clean cases
@test("P-FACT passes a release whose artifacts agree with every declared fact")
def t_clean():
    d = release(
        {"XT60PW-M": XT60_OK},
        [("XT60", "J1", "XT60PW-M_EdgeTrim", "XT60PW-M", "C98732")],
        netlist=netlist_of({"GND": ["J1"]}))
    r = must_pass(pfact(d), "P-FACT on an agreeing release")
    contains(r.out, "P-FACT OK", "clean verdict")
    contains(r.out, "1 assertion(s) graded", "says how much it actually graded")


@test("P-FACT says out loud when NOTHING is declared, rather than passing "
      "quietly")
def t_nothing_declared():
    """The state the whole fleet is in today: 0 of 187 part.yaml declare an
    `asserts:` block. Exiting 0 is correct — there is nothing to grade — but a
    silent 0 is how "we check part facts" becomes true-sounding and false."""
    d = release({"PLAIN": "mpn: PLAIN\ntype: resistor\n"},
                [("10k", "R1", "R_0603", "PLAIN", "C1")])
    r = must_pass(pfact(d), "P-FACT with nothing declared")
    contains(r.out, "0/1 part.yaml declare", "the coverage denominator")
    contains(r.out, "nothing was proved", "says so in words")


# ------------------------------------------------------------- known-bad
@test("P-FACT FAILS the XT60 class: part.yaml says pad 1 is NEGATIVE and the "
      "netlist puts it on VBAT", kind="known_bad")
def t_pad1_polarity():
    """THE INCIDENT (usb-power-3s, spf fa0b9c1; the same fact is written in
    usb-hub-3s-v2/02_parts/XT60PW-M/part.yaml as "PAD 1 IS NEGATIVE - polarity
    is a PART FACT"). The battery connector shipped with '+' on the '-' blade.
    The netlist is SELF-CONSISTENT either way — symbol, footprint and board all
    agree — so no electrical check can see it. Only the PART's own recorded
    fact disagrees, and nothing read it."""
    d = release(
        {"XT60PW-M": XT60_OK},
        [("XT60", "J1", "XT60PW-M_EdgeTrim", "XT60PW-M", "C98732")],
        netlist=netlist_of({"VBAT": ["J1"]}))
    r = must_fail(pfact(d), "P-FACT on a reversed XT60", "P-FACT")
    contains(r.out, "J1", "names the ref")
    contains(r.out, "VBAT", "names the ACTUAL net")
    contains(r.out, "negative", "names the DECLARED polarity")
    contains(r.out, "XT60 CLASS", "explains why no electrical check sees it")


@test("P-FACT FAILS a part declared not_on_assembly_bom that reached the BOM",
      kind="known_bad")
def t_not_on_assembly_bom():
    """crow-mic-pod-v2's AOM-5024L: catalogued but stock 0 on all three
    siblings AND through_hole on an SMT-only order, so its part.yaml says keep
    it off the JLC-assembly BOM. The fact was written down; the BOM carried the
    code anyway."""
    y = ("mpn: AOM-5024L-HD-R\ntype: microphone\n"
         "asserts:\n"
         "  - assert: not_on_assembly_bom\n"
         "    why: \"THT on an SMT-only order and stock 0 on all three "
         "siblings (live query 2026-07-25) — hand-wire from Digi-Key\"\n"
         "sourcing: {lcsc: C3273706}\n")
    d = release({"AOM-5024L-HD-R": y},
                [("MIC", "MK1", "AOM5024", "AOM-5024L-HD-R", "C3273706")])
    r = must_fail(pfact(d), "P-FACT on a part that must stay off the BOM",
                  "P-FACT")
    contains(r.out, "MK1", "names the ref")
    contains(r.out, "not_on_assembly_bom", "names the declared fact")


@test("P-FACT FAILS an MSL part whose order paperwork never states the level",
      kind="known_bad")
def t_msl_absent_from_paperwork():
    """crow-recorder-central-v2's consigned XU316: its part.yaml records "MSL
    3, 168h floor life below 30C / 60% RH; bake per J-STD-033D", and the order
    paperwork shipped with ZERO MSL text. A moisture obligation the assembler
    cannot infer is one that will not be met — and a popcorned 0.4mm-pitch
    128-lead TQFP is not recoverable."""
    y = ("mpn: XU316-1024-TQ128-I24\ntype: soc\n"
         "asserts:\n"
         "  - assert: msl\n    level: 3\n    floor_life_h: 168\n"
         "    why: \"consigned part; J-STD-033D bake if the bag is open "
         ">168h below 30C/60% RH\"\n"
         "sourcing: {lcsc: C6938291}\n")
    d = release({"XU316-1024-TQ128-I24": y},
                [("XU316", "U1", "TQFP-128", "XU316-1024-TQ128-I24",
                  "C6938291")],
                order="# Order\nBuild 5. Standard 4-layer.\n")
    r = must_fail(pfact(d), "P-FACT on missing MSL paperwork", "P-FACT")
    contains(r.out, "MSL 3", "names the declared level")
    contains(r.out, "cannot infer", "says why paperwork is the artifact")
    # ...and stating it discharges the finding, so the gate is satisfiable
    d2 = release({"XU316-1024-TQ128-I24": y},
                 [("XU316", "U1", "TQFP-128", "XU316-1024-TQ128-I24",
                   "C6938291")],
                 order="# Order\nConsigned U1 is MSL 3 (168h floor life); "
                       "bake per J-STD-033D if the bag has been open longer.\n")
    must_pass(pfact(d2), "P-FACT once the paperwork states MSL 3")


@test("P-FACT FAILS a BOM value that contradicts the part's own datasheet "
      "bound", kind="known_bad")
def t_value_contradicts():
    """The cooksense watchdog pull-down, from the PART's side rather than the
    netlist's (canon E-INV part_value grades the same fact against the
    netlist — two artifacts, one fact, canon M1). TI SLVS165O names 1k; the
    board shipped 100k and the supervisor was silently disabled."""
    d = release({"TPS3823-33DBVR": WD_OK},
                [("100k", "R_WDPETPD", "R_0402", "TPS3823-33DBVR", "C7719")])
    r = must_fail(pfact(d), "P-FACT on a contradicted value", "P-FACT")
    contains(r.out, "R_WDPETPD", "names the ref")
    contains(r.out, "100k", "names the ACTUAL BOM value")
    contains(r.out, "1k", "names the DECLARED value")


@test("P-FACT reports an assertion that reached NO ref — it is not a pass",
      kind="known_bad")
def t_facts_reach_the_refs():
    """A gate that grades zero things and prints OK is the `jlc_twin` exit-0
    class. An `asserts:` block whose LCSC matches nothing on the BOM has
    proved nothing, and must say so."""
    y = WD_OK.replace("C7719", "C_NOT_ON_THIS_BOARD")
    d = release({"TPS3823-33DBVR": y},
                [("10k", "R1", "R_0603", "OTHER", "C1")])
    r = pfact(d, "--strict")
    must_fail(r, "P-FACT strict on an unreached assertion", "UNREACHED")
    contains(r.out, "grades nothing", "says why an unreached assert is not a pass")


@test("P-FACT NAMES the one kind it cannot yet grade instead of going quiet",
      kind="known_bad")
def t_deferred_is_named():
    """`keepout_region` is the LTV-817S 5kV isolation-barrier class — the
    part.yaml says "no copper under the opto" and cooksense shipped 0.175 mm.
    It needs board geometry this offline checker does not read. A deferred kind
    that silently returns clean is worse than no kind at all, so it is reported
    by name and FAILS under --strict."""
    y = ("mpn: LTV-817S\ntype: optocoupler\n"
         "asserts:\n"
         "  - assert: keepout_region\n"
         "    layers: [F.Cu, In1.Cu, In2.Cu, B.Cu]\n    region: under_body\n"
         "    why: \"5kV isolation barrier between the contactor loop and "
         "SELV logic; no copper under the body\"\n"
         "sourcing: {lcsc: C125121}\n")
    d = release({"LTV-817S": y},
                [("OPTO", "U_OPTO", "SMDIP-4", "LTV-817S", "C125121")])
    r = must_pass(pfact(d), "P-FACT with only a deferred kind declared")
    contains(r.out, "P-FACT-DEFERRED", "the deferred kind is named")
    contains(r.out, "keepout_region", "by name")
    must_fail(pfact(d, "--strict"), "P-FACT --strict on a deferred kind",
              "DEFERRED")


@test("P-FACT refuses to load an assert with no 'why:' or an unknown kind",
      kind="known_bad")
def t_schema():
    """A part fact without its reason is exactly the prose gotcha this block
    exists to replace (canon M4)."""
    nowhy = ("mpn: X\ntype: r\nasserts:\n  - assert: not_on_assembly_bom\n"
             "sourcing: {lcsc: C1}\n")
    d = release({"X": nowhy}, [("1", "R1", "f", "X", "C1")])
    r = must_fail(pfact(d), "P-FACT on an assert with no why", "why")
    contains(r.out, "LOAD ERROR", "a schema error, not a graded result")
    bad = ("mpn: X\ntype: r\nasserts:\n  - assert: teleport\n"
           "    why: \"not a real kind\"\nsourcing: {lcsc: C1}\n")
    d2 = release({"X": bad}, [("1", "R1", "f", "X", "C1")])
    r2 = must_fail(pfact(d2), "P-FACT on an unknown kind", "unknown kind")
    contains(r2.out, "teleport", "names the offending kind")


@test("P-FACT's value decode keeps m (milli) and M (mega) apart")
def t_si_case():
    """A case-folding parser reads a 4.7M feedback resistor as 4.7 milliohms
    and reports a comfortable pass — the quiet way a value gate becomes
    decoration."""
    sys.path.insert(0, str(FAB_SCRIPTS))
    from part_facts_check import parse_si                # noqa: E402
    check(parse_si("1M") == 1e6 and parse_si("1m") == 1e-3,
          f"m/M collapsed: 1M={parse_si('1M')} 1m={parse_si('1m')}")
    check(abs(parse_si("4k7") - 4700.0) < 1e-9, "infix form 4k7")
    check(parse_si("DNP") is None, "an undecodable value must be None")


if __name__ == "__main__":
    sys.exit(main())
