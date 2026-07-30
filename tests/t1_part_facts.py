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
import json
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
    contains(r.out, "1/1 assertion(s) REACHED A COMPARISON",
             "says how much it actually graded, over the total declared")


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


# ================= `equals:` as a LITERAL (2026-07-28, the fleet-wide hole) ===
RF_SWITCH = """\
mpn: PE42482A-X
type: rf_switch
asserts:
  - assert: value
    equals: PE42482A-X
    why: "the BOM Comment must NAME the switch; a pin-compatible SPDT in the
      same land is a different part and only the Comment can say which"
sourcing: {lcsc: C7654321}
"""


@test("P-FACT FAILS a WRONG MPN in the BOM Comment — an `equals:` the SI "
      "decoder cannot read is a LITERAL, not a broken assertion",
      kind="known_bad")
def t_value_literal_mpn_mismatch():
    """THE FLEET-WIDE HOLE (2026-07-28). `equals:` was pushed through
    `parse_si()` and nothing else. An MPN operand — `RP2040`, `PE42482A-X`,
    `TYPE-C-31-M-12A`, `MCP1755S-3302E/DB` — decoded to None, emitted a
    NON-BLOCKING `P-FACT-CONFIG` note and GRADED NOTHING, while the run went on
    to print `P-FACT OK`.

    MEASURED before the fix: 11 of 13 asserts on pluto-rx2-8way (including
    BOTH assertions that shipped as the exemplars) and 5 on pluto-cal-switch
    checked nothing at all. After it: 0 P-FACT-CONFIG anywhere in the fleet,
    and ZERO new failures — every one became a properly graded assert. That is
    exactly the class the 02_parts contract cites as the REASON `asserts:`
    exists, reproduced inside the mechanism built to end it: a fact written
    down and never read is indistinguishable from a fact nobody knew.

    RED-VERIFIED 2026-07-28 (git-swap, tests/README step 3): with git HEAD's
    part_facts_check.py swapped back in this fails with `P-FACT on a wrong MPN
    SHOULD HAVE FAILED but exited 0 — the gate is not gating`, and the report
    reads `P-FACT-CONFIG: PE42482A-X: value assert has no decodable
    equals: ('PE42482A-X')` followed by `P-FACT OK`. Restored, it FAILS as it
    must.
    """
    d = release({"PE42482A-X": RF_SWITCH},
                [("PE42480A-X", "U_SW1", "QFN-20", "PE42482A-X", "C7654321")])
    r = must_fail(pfact(d), "P-FACT on a wrong MPN", "P-FACT")
    contains(r.out, "U_SW1", "names the ref")
    contains(r.out, "PE42480A-X", "names the ACTUAL BOM Comment")
    contains(r.out, "PE42482A-X", "names the DECLARED literal")
    check("P-FACT-CONFIG" not in r.out,
          f"a literal operand is still being called a config error:\n{r.out}")


@test("P-FACT accepts the matching literal, and the compare is EXACT — the "
      "SS12D07VG6 space-vs-hyphen drift is a MISMATCH", kind="known_bad")
def t_value_literal_is_exact():
    """The adjacent property, re-measured every run rather than asserted in a
    docstring: the SAME fixture with the Comment CORRECTED must PASS, or the
    known-bad above proves only that the gate says no to everything.

    And the compare is deliberately not case-folded or punctuation-normalised.
    `SS12D07VG6 087` vs `SS12D07VG6-087` is a drift this fleet has ALREADY
    shipped — usb-hub-3s-v3 SW1, where the retired side-file and the dossier
    disagreed by exactly one character and a blank-only check passed it
    (ADR-0006 / F-ECHO). A compare loose enough to accept that would re-open
    the hole it is here to close, so both near-misses must still FAIL.
    """
    ok = release({"PE42482A-X": RF_SWITCH},
                 [("PE42482A-X", "U_SW1", "QFN-20", "PE42482A-X", "C7654321")])
    r = must_pass(pfact(ok), "P-FACT on the matching literal")
    check("P-FACT-CONFIG" not in r.out, f"config noise on a good part:\n{r.out}")
    # leading/trailing whitespace is the ONE thing normalised away.
    # THE LCSC HERE USED TO READ `C7` (2026-07-29): the part declares C7654321,
    # so the code matched no BOM row, the assertion reached NOTHING, and this
    # fixture passed only because the pre-fix gate exited 0 over a zero
    # denominator. The test was green and vacuous — the defect under test,
    # inside the test for it. Found by the M-COVER fix making it RED.
    sp = release({"PE42482A-X": RF_SWITCH},
                 [("  PE42482A-X  ", "U_SW1", "QFN-20", "PE42482A-X",
                   "C7654321")])
    must_pass(pfact(sp), "P-FACT on a whitespace-padded Comment")
    for near in ("pe42482a-x", "PE42482AX", "PE42482A X"):
        bad = release({"PE42482A-X": RF_SWITCH},
                      [(near, "U_SW1", "QFN-20", "PE42482A-X", "C7654321")])
        must_fail(pfact(bad), f"P-FACT on the near-miss {near!r}", "U_SW1")


@test("P-FACT REFUSES `tolerance_pct:` on a literal operand — a tolerance on "
      "a part number grades nothing", kind="known_bad")
def t_value_literal_rejects_tolerance():
    """A percentage band around a string is meaningless, and silently ignoring
    it would let an author believe a fuzzy match was happening. It is a schema
    error, named as one."""
    y = RF_SWITCH.replace("    equals: PE42482A-X\n",
                          "    equals: PE42482A-X\n    tolerance_pct: 5\n")
    d = release({"PE42482A-X": y},
                [("PE42482A-X", "U_SW1", "QFN-20", "PE42482A-X", "C7654321")])
    r = pfact(d, "--strict")
    must_fail(r, "P-FACT on tolerance_pct over a literal", "P-FACT-CONFIG")
    contains(r.out, "tolerance", "names the offending key")
    # ...and the numeric operand still takes its tolerance, untouched
    must_pass(pfact(release({"TPS3823-33DBVR": WD_OK},
                            [("1.02k", "R_WDPETPD", "R_0402",
                              "TPS3823-33DBVR", "C7719")]), "--strict"),
              "a numeric equals still honours tolerance_pct")


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


@test("P-FACT REFUSES to print OK over a ZERO denominator — 16 declared, 16 "
      "unreached, `P-FACT OK`, exit 0", kind="known_bad")
def t_zero_denominator_is_a_fail():
    """MEASURED ON pluto-rx2-8way, 2026-07-29, stage 5, verbatim:

        P-FACT: 14/15 part.yaml declare an `asserts:` block;
                16 assertion(s) graded against projects/pluto-rx2-8way
          P-FACT-UNREACHED: ... (x16, every single assertion)
        P-FACT OK                                            <- exit 0

    `graded` was incremented on ENTRY to the assertion loop, before anything
    was compared, so the number that was supposed to BE the coverage proof
    counted the misses. That is `jlc_twin` exiting 0 on 11 unverified parts
    with a different label (tests/README, CLAUDE.md), and canon M-COVER names
    the rule it breaks: A ZERO DENOMINATOR IS A FAIL.

    The fixture is the smallest form of it: one part whose LCSC matches nothing
    the BOM carries, so its single assertion cannot reach a comparison. NOT
    run with --strict — `--strict` decides whether a PARTIAL denominator
    blocks, and there is nothing partial about zero.

    RED-VERIFIED 2026-07-29 (git-swap, tests/README step 3): with git HEAD's
    part_facts_check.py swapped back in, this fixture prints
    `P-FACT: 1/1 part.yaml declare an `asserts:` block; 1 assertion(s) graded`
    then the UNREACHED line then `P-FACT OK`, and exits 0 — this test fails
    there with `P-FACT over a zero denominator SHOULD HAVE FAILED but exited
    0`. Restored, it exits 1 on `P-FACT GRADED NOTHING`.
    """
    y = WD_OK.replace("C7719", "C_NOT_ON_THIS_BOARD")
    d = release({"TPS3823-33DBVR": y},
                [("10k", "R1", "R_0603", "OTHER", "C1")])
    r = must_fail(pfact(d), "P-FACT over a zero denominator",
                  "P-FACT GRADED NOTHING")
    contains(r.out, "0/1 assertion(s) REACHED A COMPARISON",
             "the header states the denominator it earned")
    contains(r.out, "M-COVER", "cites the canon it would otherwise break")
    not_contains(r.out, "P-FACT OK", "must not also claim OK")
    # THE ADJACENT PROPERTY: one assertion that DOES reach still passes, so
    # this is a denominator check and not a blanket refusal.
    ok = release({"TPS3823-33DBVR": WD_OK},
                 [("1k", "R_WDPETPD", "R_0402", "TPS3823-33DBVR", "C7719")])
    r2 = must_pass(pfact(ok), "P-FACT with a real denominator")
    contains(r2.out, "1/1 assertion(s) REACHED", "and it says so")


@test("G-VACUOUS P-FACT: a MALFORMED assertion prints `OK — 0/0` and exits 0 — "
      "the zero denominator survived where UNREACHED was closed",
      kind="vacuity", gate="part_facts_check.py")
def t_vacuity_all_deferred_or_all_config_prints_OK_over_a_zero_denominator():
    """THE DECLARED BLIND SPOT (canon G-VACUOUS; the executable half of the
    `VACUITY:` block in part_facts_check.py's docstring).

    This fixture asserts the gate PASSES while the fact it grades — "the board
    and release agree with every part's own declared facts" — is FALSE. It PINS
    the defect; closing it should break this test, which then becomes a
    `known_bad` beside `t_zero_denominator_is_a_fail`.

    WHAT WAS FIXED AND WHAT WAS NOT. The 2026-07-29 fix closed `graded == 0 and
    unreached > 0` — measured then as `16 assertion(s) graded`, all 16
    UNREACHED, `P-FACT OK`, exit 0, and now `P-FACT GRADED NOTHING`, exit 1.
    A find lands in exactly one of three buckets, and only ONE of the three is
    counted by that guard:

      graded     -> compared. Good.
      unreached  -> the artifact was missing. Now a hard fail in aggregate.
      CONFIG     -> the ASSERTION ITSELF is malformed. Still neither.

    So a part whose ONLY assertion is malformed reaches `P-FACT OK — 0/0
    assertions graded`, exit 0. MEASURED: `polarity: minus` (instead of
    `negative`) yields `P-FACT-CONFIG ... got 'minus'` and then OK. A typo in a
    polarity claim therefore reads as a pass — and a REVERSED electrolytic
    (CE1, in this repo's own history, shipped in v1.0 and v1.1) is what that
    class costs. `P-FACT-DEFERRED` is the same shape and is deliberate, argued
    for in the code; the CONFIG path is not.

    Both block under `--strict`, so the blind spot is precisely: DEFAULT flags,
    and every declared assertion malformed. The fixture also asserts the
    CONTRAST — the identical part.yaml with `negative` spelled correctly reaches
    a comparison and FAILS on the netlist — because that is what makes this a
    blind spot and not a limitation."""
    bad = XT60_OK.replace("polarity: negative", "polarity: minus")
    d = release({"XT60PW-M": bad},
                [("XT60PW-M", "J1", "XT60", "XT60PW-M", "C98732")],
                netlist=netlist_of({"VBAT": ["J1"]}))
    r = must_pass(pfact(d),
                  "P-FACT over a release whose only assertion is MALFORMED — "
                  "THE BLIND SPOT. If this now FAILS, the CONFIG bucket has "
                  "been folded into the denominator guard: convert this fixture "
                  "to kind=\"known_bad\"")
    contains(r.out, "P-FACT-CONFIG", "the malformed assertion IS reported")
    contains(r.out, "0/0", "and the denominator IS printed as zero")
    contains(r.out, "P-FACT OK", "yet the verdict is OK")
    not_contains(r.out, "GRADED NOTHING",
                 "the zero-denominator guard does not fire, because it is "
                 "conditioned on unreached > 0 and a CONFIG find is neither "
                 "graded nor unreached")

    # THE CONTRAST. One character back and the same assertion reaches a real
    # comparison — proving the fixture is a good input broken in ONE way, and
    # that the gate genuinely can grade this fact when it parses.
    good = release({"XT60PW-M": XT60_OK},
                   [("XT60PW-M", "J1", "XT60", "XT60PW-M", "C98732")],
                   netlist=netlist_of({"VBAT": ["J1"]}))
    g = must_fail(pfact(good), "the SAME assertion, spelled correctly",
                  "1/1 assertion(s) REACHED A COMPARISON")
    contains(g.out, "P-FACT FAIL", "the correctly-spelled assertion is graded "
                                   "and violated, so the fact IS gradeable")

    # And --strict does block the malformed case, which is where the blind spot
    # ends: the default flags are the whole of it.
    must_fail(pfact(d, "--strict"), "the malformed assertion under --strict",
              "P-FACT-CONFIG")


@test("P-FACT resolves refdes BEFORE stage 7 — the netlist-graded polarity "
      "assert stops being UNREACHED at the placement gate", kind="known_bad")
def t_entry_refmap_reaches_polarity():
    """ADR-0007 M-ENTRY: grade a fact where it ENTERS the pipeline, not where
    it SHOWS. P-FACT resolved every refdes through the FAB BOM, which stage 7
    writes — so at stage 5 `pad1_net_polarity` was reported UNREACHED even
    though the netlist it grades against had been on disk since stage 4. The
    XT60 class is a PLACEMENT-time defect; discovering it at the order gate is
    discovering it too late.

    The fixture has NO fab/ at all and carries the refdes<->LCSC relation only
    in 03_tscircuit/build/circuit.json, exactly as both pluto boards do at
    stage 5. The polarity assert must reach its comparison and FAIL on the
    reversed net.

    RED-VERIFIED 2026-07-29 by deleting the `load_entry_refmap` fallback (the
    pre-fix behaviour): the run reports
    `P-FACT-UNREACHED: XT60PW-M: pad1_net_polarity reached NO board ref` and
    exits 0, so this test fails with `SHOULD HAVE FAILED but exited 0`.
    MEASURED on the real board: pluto-rx2-8way went from 16 graded / 16
    unreached / OK to 2 of 16 REACHED — the KT-0603R LED and the SMBJ6.0A TVS
    polarity asserts, both graded off `03_tscircuit/build/circuit.json`.
    """
    d = tmpdir("pfact_entry_")
    (d / "02_parts" / "XT60PW-M").mkdir(parents=True)
    (d / "02_parts" / "XT60PW-M" / "part.yaml").write_text(XT60_OK)
    (d / "06_build" / "netlists").mkdir(parents=True)
    (d / "06_build" / "netlists" / "b.net").write_text(
        netlist_of({"VBAT": ["J1"]}))
    (d / "03_tscircuit" / "build").mkdir(parents=True)
    (d / "03_tscircuit" / "build" / "circuit.json").write_text(json.dumps([
        {"type": "source_component", "name": "J1",
         "supplier_part_numbers": {"jlcpcb": ["C98732"]}}]))
    r = must_fail(pfact(d), "P-FACT on a pre-stage-7 project", "P-FACT")
    contains(r.out, "circuit.json",
             "names the artifact the refdes map came from")
    contains(r.out, "J1", "names the ref it reached")
    contains(r.out, "XT60 CLASS", "and grades the fact, not the stage")


@test("P-FACT does not fail a pre-order project for paperwork stage 7 writes")
def t_msl_before_the_release_is_unreached():
    """The mirror image of the zero-denominator bug, in the same file: `msl`
    with no ORDER_README was a HARD P-FACT violation, so any project declaring
    an MSL part failed at every stage before its release existed. A document
    that has not been written yet is not a violated fact — it is an ungraded
    one, and the two verdicts send an author to different places. A target that
    HAS a fab BOM and no paperwork is still the real defect
    (t_msl_absent_from_paperwork above), which is what tells them apart."""
    y = ("mpn: XU316-1024-TQ128-I24\ntype: soc\n"
         "asserts:\n"
         "  - assert: msl\n    level: 3\n    floor_life_h: 168\n"
         "    why: \"consigned part; J-STD-033D bake if the bag is open "
         ">168h below 30C/60% RH\"\n"
         "sourcing: {lcsc: C6938291}\n")
    d = tmpdir("pfact_msl_")
    (d / "02_parts" / "XU316-1024-TQ128-I24").mkdir(parents=True)
    (d / "02_parts" / "XU316-1024-TQ128-I24" / "part.yaml").write_text(y)
    r = pfact(d)
    contains(r.out, "P-FACT-UNREACHED", "an ungraded fact, not a violated one")
    contains(r.out, "stage 7", "says where it WILL be graded")
    not_contains(r.out, "P-FACT: XU316", "not reported as a violated fact")
    # and with nothing gradeable at all it still refuses to say OK
    must_fail(r, "P-FACT with a zero denominator", "GRADED NOTHING")


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
