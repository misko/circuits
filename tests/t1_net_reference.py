#!/usr/bin/env python3
"""T1: the NET-REFERENCE gate (canon E-NETREF) — net_reference_audit.py.

Motivating measurement (smc0985-cooksense v1.7, 2026-07-29): **10 of 123 net
names referenced by that board's rule files and dossiers are not nets on the
board**, and the fleet sweep this gate's landing commit records makes it 64 of
908 across six boards. Three of the ten had already been paid for:

  1. THE SILK PRINTED A GHOST — a keypad caption read `GND_ISO ONLY`, and
     `grep -c GND_ISO` on `cooksense.net` is 0. The only ISO-bearing net name on
     the board is `SPI_MISO`, which matches `GND_ISO` by SUBSTRING only. It
     reached the shipped F.Silkscreen.
  2. A SAFETY-RELEVANT BUDGET WAS UNENFORCEABLE — `TPS259573DSGR`'s eFuse input
     decoupling `keep_short` is addressed to `5V_SELV`, not a net on the board,
     so `5V_IN`/`5V_FUSED`/`5V_RPP` carry zero graded capacitors.
  3. A WHOLE RAIL WAS INVISIBLE TO A GRADER — `supplies: {N3V3: 3.3}`, the tsx
     AUTHOR-PREFIX form of the net the netlist calls `3V3`.

Case 3 was closed NARROWLY in `electrical_invariants.py` (fa22228) by checking
one field. This gate is the general one, at the width of the class (canon
M-WIDTH), over eleven enumerated reference kinds with the denominator printed.

RED-VERIFICATION (new-gate variant, per tests/README "Adding a regression").
`net_reference_audit.py` did not exist before this commit, so there is no
pre-fix code to swap in: MEASURED pre-fix output for every case below is
`/usr/bin/python3: can't open file '.../net_reference_audit.py': [Errno 2] No
such file or directory`, exit 2 — no gate, no verdict. Where a stronger red is
available it is taken instead of relying on that:

  * `t_ghost_only_a_substring` reproduces THE DEFECT MECHANISM inline — a
    naive containment resolver, which is how `GND_ISO` survived review — and
    asserts it reports the ghost RESOLVED while this gate fails it. That is a
    real RED against the wrong algorithm, not against an absent file.
  * `t_author_prefix_near_miss` asserts the DIAGNOSIS, not the exit code:
    with the two `N`-prefix rules deleted from `near_miss()` the fixture still
    FAILS but names no candidate, and a verdict that sends the author hunting
    is the false lead fa22228's post-mortem is about.
  * `t_real_cooksense_silk_ghost` and `t_real_fleet_denominators` read REAL
    project bytes read-only, so the incident itself is pinned, not a model of
    it.

Each known-bad fixture is a PASSING fixture broken in exactly ONE way, and the
other half of the discrimination is asserted too: a rule file whose every
reference resolves must PASS, and a legitimately-unresolvable reference must
land in the honest UNREACHED class rather than a FAIL. A check that only ever
fires one way ranks nothing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, eq,  # noqa: E402
                     main, must_fail, must_pass, not_contains, run, test,
                     tmpdir)

NRA = SCRIPTS / "net_reference_audit.py"

REAL = ROOT / "archived_projects" / "smc0985-cooksense"
#: the PRE-FIX silk, preserved in-tree as a regenerated proof artifact. Its
#: caption still reads `GND_ISO ONLY`; the live 03_src floorplan was corrected
#: on 2026-07-29. Read-only — nothing here writes a project file.
PROOF_FP = REAL / "06_build" / "proof" / "floorplan_p0proof.yaml"
REAL_NET = REAL / "06_build" / "netlists" / "cooksense.net"


# --------------------------------------------------------------- fixtures
def netlist(nets, comps=()):
    """{netname: [(ref, pin)]} -> a minimal KiCad .net string.

    Written one-atom-per-line for the nets, which is how kicad-cli exports and
    the shape the audit's regex must tolerate; the components block is dense,
    so both spacings are exercised by every fixture.
    """
    blocks = []
    for i, (name, nodes) in enumerate(nets.items(), 1):
        ns = "".join(f'\n\t\t\t(node (ref "{r}") (pin "{p}"))' for r, p in nodes)
        blocks.append(f'\n\t\t(net\n\t\t\t(code "{i}")\n\t\t\t'
                      f'(name "{name}"){ns}\n\t\t)')
    cs = "".join(f'(comp (ref "{c}") (value "x"))' for c in comps)
    return f'(export (version "E") (components {cs}) (nets{"".join(blocks)}))'


#: a small board with a deliberate trap: SPI_MISO CONTAINS the string that the
#: known-bad caption names. This is the cooksense situation exactly.
GOOD_NETS = {
    "3V3":      [("U1", "1"), ("C1", "1")],
    "5V_IN":    [("J1", "1"), ("F1", "1")],
    "5V_FUSED": [("F1", "2"), ("Q1", "3")],
    "5V_RPP":   [("Q1", "2"), ("U1", "3")],
    "SPI_MISO": [("U1", "4"), ("U2", "2")],
    "GND":      [("C1", "2"), ("U1", "2")],
}
GOOD_COMPS = ("U1", "U2", "C1", "J1", "F1", "Q1")


def project(nets_yaml=None, inv_yaml=None, power_yaml=None,
            floorplan=None, keep_short=None, net_text=None, netlist_name="b"):
    """A scratch project tree. Only the pieces a case needs are written, so a
    fixture breaks exactly one thing and the rest stays a PASSING tree."""
    d = tmpdir("nra_")
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "02_parts").mkdir(parents=True)
    nl = d / "06_build" / "netlists"
    nl.mkdir(parents=True)
    if net_text is not None:
        (nl / f"{netlist_name}.net").write_text(net_text)
    if nets_yaml is not None:
        (d / "03_src" / "rules" / "nets.yaml").write_text(nets_yaml)
    if inv_yaml is not None:
        (d / "03_src" / "rules" / "electrical_invariants.yaml").write_text(inv_yaml)
    if power_yaml is not None:
        (d / "03_src" / "rules" / "power_tree.yaml").write_text(power_yaml)
    if floorplan is not None:
        (d / "03_src" / "floorplan.yaml").write_text(floorplan)
    if keep_short is not None:
        for mpn, body in keep_short.items():
            p = d / "02_parts" / mpn
            p.mkdir(parents=True)
            (p / "part.yaml").write_text(body)
    return d


GOOD_NETS_YAML = """\
classes:
  PWR_IN:
    intent: the 5V input path
    nets: [5V_IN, 5V_FUSED, 5V_RPP]
    current: 2A
    min_width: 0.5mm
  PWR_3V3:
    intent: logic rail
    nets: [3V3]
    current: 0.35A
    min_width: 0.3mm
scoped_floors:
  - {zone: pad_entry, nets: [5V_RPP], min_width: 0.25, why: pad entry necks}
"""

GOOD_INV_YAML = """\
supplies: {3V3: 3.3}
invariants:
  - assert: pin_on_net
    pin: "U1.3"
    net: 5V_RPP
    adr: "0001"
    why: the protected rail reaches the load
  - assert: series_chain
    chain: [5V_IN, F1, 5V_FUSED]
    adr: "0001"
    why: input fuse in the power path
"""

GOOD_FP = """\
project: {name: b, netlist: 06_build/netlists/b.net}
zones:
  - {net: GND, layers: [F.Cu], rect: [0, 0, 10, 10], priority: 0}
asserts:
  pad_net:
    - {ref: U1, pad: "4", net: SPI_MISO}
silk:
  captions:
    - {text: "SPI_MISO probe here", at: [5, 5], size: 0.8}
"""


def audit(d, *extra):
    return run([KPY, NRA, str(d), *extra])


def clean_tree(**over):
    kw = dict(nets_yaml=GOOD_NETS_YAML, inv_yaml=GOOD_INV_YAML,
              floorplan=GOOD_FP, net_text=netlist(GOOD_NETS, GOOD_COMPS),
              keep_short={"TPS259573DSGR": (
                  "mpn: TPS259573DSGR\nlayout:\n  source: ds Fig.68\n"
                  "  keep_short:\n"
                  "    - {net: 5V_IN, max_span_mm: 3, why: Cin loop}\n")})
    kw.update(over)
    return project(**kw)


# ----------------------------------------------------------- the clean half
@test("E-NETREF passes a tree whose EVERY reference resolves, and prints its "
      "denominator over all 12 reference kinds")
def t_clean_passes():
    """The other half of the discrimination. A gate that only ever fires one
    way ranks nothing, and the denominator is canon M-COVER: without `N/M` and
    the kind table, `0 ghost` is indistinguishable from `0 references read`."""
    r = must_pass(audit(clean_tree()), "clean net-reference tree")
    contains(r.out, "E-NETREF: PASS")
    contains(r.out, "reference site(s) across 12 kinds")
    for k in [f"K{i}" for i in range(1, 13)]:
        contains(r.out, k, f"kind table row {k}")
    # the trap net is RESOLVED, not silently skipped
    contains(r.out, "resolved")
    not_contains(r.out, "GHOST (")


@test("E-NETREF grades every kind it enumerates: --kinds names a CONSUMER for "
      "each of the 12, so no kind is listed without an argument that a miss "
      "costs something")
def t_kinds_have_consumers():
    r = must_pass(run([KPY, NRA, "--kinds"]), "--kinds")
    # 12 since 2026-07-29: K12 (`nets.yaml length_match.<G>.members.<M>[]`,
    # consumer copper_length_audit.py) was added with canon R-LEN.
    eq(r.out.count("consumer:"), 12, "kinds carrying a named consumer")
    eq(len([l for l in r.out.splitlines() if l.startswith("K")]), 12,
       "kind rows")


# --------------------------------------------------- known-bad: the GND_ISO case
@test("E-NETREF FAILS a silk caption naming a net that exists ONLY as a "
      "SUBSTRING of another net (the GND_ISO/SPI_MISO case), and a naive "
      "containment resolver PASSES the same fixture", kind="known_bad")
def t_ghost_only_a_substring():
    """cooksense shipped `KEYPAD ISOLATION COMB >=6mm creepage GND_ISO ONLY` on
    F.Silkscreen. `grep -c GND_ISO` on the netlist is 0; the only ISO-bearing
    net is `SPI_MISO`. Substring matching is how that survived review, so this
    fixture pins BOTH halves: the gate must fail, AND the wrong algorithm must
    be shown to pass.

    MEASURED pre-fix: the script did not exist (exit 2, `No such file or
    directory`) and NO gate in the repo read caption text against the netlist —
    the ghost was found by a human re-deriving the net list by hand.

    RED against the WRONG ALGORITHM (inline, below): resolving by containment
    reports 1/1 resolved on this exact fixture. That is not a hypothetical
    weaker gate; it is the reading that produced the shipped board.
    """
    fp = GOOD_FP.replace('"SPI_MISO probe here"',
                         '"KEYPAD ISOLATION COMB >=6mm creepage GND_ISO ONLY"')
    r = must_fail(audit(clean_tree(floorplan=fp)), "caption ghost net",
                  "'GND_ISO' is NOT a net on this board")
    contains(r.out, "[K11]")
    contains(r.out, "E-NETREF: FAIL")
    # ... and it must NOT have been satisfied by SPI_MISO
    not_contains(r.out, "silk.captions[0].text: resolved")

    # THE DEFECT MECHANISM, reproduced: containment says this board has it.
    nets = set(GOOD_NETS)
    naive = [n for n in nets if "GND_ISO" in n or n in "GND_ISO"]
    check(naive, "the substring resolver was expected to find a false match — "
                 "if it does not, this fixture no longer reproduces the "
                 "mechanism that shipped GND_ISO and must be rewritten")
    check("GND_ISO" not in nets,
          "fixture broken: GND_ISO must NOT be a real net here")


# ------------------------------------------- known-bad: the 5V_SELV budget case
@test("E-NETREF FAILS a keep_short budget addressed to a net the board does "
      "not have (the 5V_SELV case), and names the real rail FAMILY",
      kind="known_bad")
def t_budget_addressed_to_nothing():
    """cooksense's eFuse input-decoupling budget is addressed to `5V_SELV`. The
    real input-side rails are `5V_IN`/`5V_FUSED`/`5V_RPP` and none of them
    carries a graded capacitor — a safety-relevant budget that reads as covered.

    MEASURED pre-fix: exit 2, no such file. `policy_audit.py` P-ADJ-UNREACHED
    does report this class, but only from a BUILT board through pcbnew, only as
    `has 0 pad(s) on this board`, and it cannot distinguish "the net does not
    exist" from "the declaring part is not on it" — the near-miss, which is the
    fix, is not in its output at all.
    """
    ks = {"TPS259573DSGR": (
        "mpn: TPS259573DSGR\nlayout:\n  source: ds Fig.68\n  keep_short:\n"
        "    - {net: 5V_SELV, max_span_mm: 3, why: Cin IN->GND loop}\n")}
    r = must_fail(audit(clean_tree(keep_short=ks)), "keep_short ghost net",
                  "'5V_SELV' is NOT a net on this board")
    contains(r.out, "[K7]")
    contains(r.out, "layout.keep_short[0].net")
    contains(r.out, "5V_FUSED, 5V_IN, 5V_RPP")     # the named 5V_* family
    contains(r.out, "with a named near-miss")


# ------------------------------------- known-bad: the tsx author-prefix (N3V3)
@test("E-NETREF FAILS the tsx AUTHOR-PREFIX form and names the strip as the "
      "fix — the systematic trap, not a typo", kind="known_bad")
def t_author_prefix_near_miss():
    """Authors read net names off the tsx source, where they carry a leading `N`
    the converter strips. cooksense wrote it in TWO places: `supplies: {N3V3:
    3.3}` (closed narrowly in fa22228) and `CD74HC221M96`'s `keep_short` net
    (still live at the time of this commit, and reported by this gate).

    MEASURED pre-fix: exit 2, no such file — and for the keep_short site
    specifically, NOTHING checked it: fa22228's fix reads only `supplies:`.

    THE ASSERTION IS THE DIAGNOSIS, NOT THE EXIT CODE, and the red is measured.
    With the two `N`-prefix rules deleted from `near_miss()` the fixture still
    FAILS and difflib still finds the candidate — MEASURED output: `Did you mean
    '3V3' (similar name)?` — so the exit code and even the candidate prove
    nothing here. What is lost is the WHY: `similar name` invites the author to
    read it as a typo in one dossier, when it is a SYSTEMATIC trap that lands
    wherever anyone transcribes a name off the tsx source, and cooksense carried
    it in two files. The test therefore asserts the phrase `tsx author-prefix
    \\`N\\` — strip it`, and both directions of the rule.
    """
    ks = {"CD74HC221M96": (
        "mpn: CD74HC221M96\nlayout:\n  source: ds Fig.1\n  keep_short:\n"
        "    - {net: N3V3, max_span_mm: 2, why: VCC decoupler}\n")}
    r = must_fail(audit(clean_tree(keep_short=ks)), "author-prefix ghost",
                  "'N3V3' is NOT a net on this board")
    contains(r.out, "tsx author-prefix `N` — strip it")
    contains(r.out, "'3V3'")

    # both directions, so the trap is closed whichever side carries the N
    sys.path.insert(0, str(SCRIPTS))
    import net_reference_audit as m
    eq([w for _c, w in m.near_miss("N3V3", {"3V3"})],
       ["tsx author-prefix `N` — strip it"], "strip direction")
    eq([w for _c, w in m.near_miss("3V3", {"N3V3"})],
       ["tsx author-prefix `N` — the netlist carries it"], "add direction")


# ----------------------------------------- known-bad: the other reference kinds
@test("E-NETREF FAILS a netclass whose net list names a ghost, and a "
      "scoped_floor addressed to one — the class then floors NOTHING",
      kind="known_bad")
def t_netclass_and_scoped_floor_ghosts():
    """A `classes.<C>.nets[]` entry becomes a `.kicad_pro` netclass PATTERN. A
    pattern that matches no net leaves the class empty, so its `min_width` and
    `clearance` are enforced on nothing while `rules_audit` A-CLASS still finds
    the class present in the .kicad_pro — the two agree and both are content.

    MEASURED pre-fix: exit 2, no such file. The 03_src/rules contract has
    listed "every net in nets.yaml exists in the netlist (else the class is a
    no-op)" under **Validate** since the folder was created; it was a sentence
    a human was supposed to check, and nothing ever did.
    """
    bad = GOOD_NETS_YAML.replace("nets: [5V_IN, 5V_FUSED, 5V_RPP]",
                                 "nets: [5V_IN, 5V_SELV, 5V_RPP]")
    r = must_fail(audit(clean_tree(nets_yaml=bad)), "netclass ghost net",
                  "'5V_SELV' is NOT a net on this board")
    contains(r.out, "[K1]")
    contains(r.out, "classes.PWR_IN.nets[1]")

    bad2 = GOOD_NETS_YAML.replace("nets: [5V_RPP], min_width: 0.25",
                                  "nets: [5V_PROTECTED], min_width: 0.25")
    r = must_fail(audit(clean_tree(nets_yaml=bad2)), "scoped_floor ghost net",
                  "[K2]")
    contains(r.out, "scoped_floors[0].nets[0]")


@test("E-NETREF FAILS a netclass GLOB that matches no net, while honouring a "
      "glob that does — patterns are globs, never substrings", kind="known_bad")
def t_glob_pattern():
    """`generate_rules_generic.py` writes `nets:` entries through to
    `netclass_patterns` verbatim, and KiCad treats those as globs. So `5V_*`
    must RESOLVE (three members) and `9V_*` must FAIL — and neither may be
    satisfied by containment.

    MEASURED pre-fix: exit 2, no such file.
    """
    ok = GOOD_NETS_YAML.replace("nets: [5V_IN, 5V_FUSED, 5V_RPP]",
                                'nets: ["5V_*"]')
    r = must_pass(audit(clean_tree(nets_yaml=ok)), "glob that matches")
    contains(r.out, "E-NETREF: PASS")

    bad = GOOD_NETS_YAML.replace("nets: [5V_IN, 5V_FUSED, 5V_RPP]",
                                 'nets: ["9V_*"]')
    r = must_fail(audit(clean_tree(nets_yaml=bad)), "glob that matches nothing",
                  "matches NO net on this board")
    contains(r.out, "enforced on nothing")


@test("E-NETREF FAILS a copper POUR and a pad_net assertion addressed to a "
      "ghost net", kind="known_bad")
def t_floorplan_ghosts():
    """A `zones[].net` naming nothing is a pour that never fills; a
    `asserts.pad_net[]` naming nothing is an assertion about a net that cannot
    be on any pad. Both are floorplan source, and neither was read against the
    netlist by anything before this gate.

    MEASURED pre-fix: exit 2, no such file.
    """
    r = must_fail(audit(clean_tree(floorplan=GOOD_FP.replace(
        "{net: GND,", "{net: GND_ISO,"))), "pour ghost net", "[K8]")
    contains(r.out, "zones[0].net")
    r = must_fail(audit(clean_tree(floorplan=GOOD_FP.replace(
        "net: SPI_MISO}", "net: SPI_MOSI}"))), "pad_net ghost", "[K9]")
    contains(r.out, "asserts.pad_net[0].net")


@test("E-NETREF FAILS an invariant subject net and a series_chain element that "
      "name nothing, and does NOT mistake a chain REFDES for a ghost net",
      kind="known_bad")
def t_invariant_ghosts():
    """`invariants[].chain[]` is deliberately net-OR-refdes (`[5V_IN, F1,
    5V_FUSED]`), so the resolver checks both universes. A gate that only looked
    at nets would report `F1` as a ghost on every series_chain in the fleet —
    117 chain elements — and be waived within a day.

    MEASURED pre-fix: exit 2, no such file. `electrical_invariants.py` does
    fail a `pin_on_net`/`net_has_part` naming an absent net, so K4 overlaps it;
    this gate adds the near-miss, and adds K5's discrimination, which the
    series_chain grader reports only as `unknown element` with no candidate.
    """
    bad = GOOD_INV_YAML.replace("net: 5V_RPP", "net: 5V_PROTECTED")
    r = must_fail(audit(clean_tree(inv_yaml=bad)), "invariant subject ghost",
                  "[K4]")
    contains(r.out, "assert=pin_on_net")

    bad = GOOD_INV_YAML.replace("chain: [5V_IN, F1, 5V_FUSED]",
                                "chain: [5V_IN, F1, 5V_FUSD]")
    r = must_fail(audit(clean_tree(inv_yaml=bad)), "chain element ghost",
                  "[K5]")
    contains(r.out, "'5V_FUSD'")
    contains(r.out, "'5V_FUSED'")            # the near-miss is named
    not_contains(r.out, "'F1' is NOT a net")  # the refdes is not a ghost


# ------------------------------------------- the HONEST UNREACHED half
@test("a power_tree rail LABEL that resolves to no net is UNREACHED, not a "
      "FAIL — nothing was going to look it up")
def t_rail_label_is_unreached():
    """THE DISCRIMINATION THAT KEEPS THIS GATE ALIVE. `power_topology.py` grades
    a rail's NUMBERS and never resolves its `name:` against the netlist, so a
    non-net label costs nothing. Two boards depend on this being true:
    usb-hub-3s-v3 writes `name: USB-A` for a port bank, and cooksense writes
    `name: 3V3_SW_A / 3V3_SW_B / 3V3_SW_RHA / 3V3_SW_RHE` for four load-switch
    rails sharing one envelope. Failing those is how a gate gets waived into
    uselessness, and passing them SILENTLY is what this whole family is about —
    so it is reported, with its reason, and does not fail.

    RED-VERIFIED inline: flipping K6's `hard` flag to True makes this fixture
    fail and turns two shipped boards red for writing documentation correctly.
    """
    pt = ('source_type: usb\nrails:\n'
          '  - {name: USB-A, vin_min: 4.5, vin_max: 5.5, vout_min: 4.75, '
          'vout_max: 5.25, iout_max_A: 1, converter: none, eff: 1}\n')
    r = must_pass(audit(clean_tree(power_yaml=pt)), "advisory rail label")
    contains(r.out, "E-NETREF: PASS")
    contains(r.out, "UNREACHED (1)")
    contains(r.out, "reported, NOT failed")
    contains(r.out, "[K6]")
    # and the slash form is split, so each sibling rail is looked up
    pt2 = pt.replace("name: USB-A", "name: 5V_IN / 5V_FUSED")
    r = must_pass(audit(clean_tree(power_yaml=pt2)), "slash-joined rail label")
    not_contains(r.out, "UNREACHED (")


@test("a board with NO netlist yet is UNREACHED as a whole and says so — "
      "never a zero, never a wall of ghosts")
def t_no_netlist_is_unreached():
    """An early-stage board has references nothing could resolve. Reporting
    every one as a ghost produces a gate that is waived on its first run;
    reporting `PASS` with no denominator is the vacuous pass this repo keeps
    rediscovering (canon M-COVER). So the references are COUNTED, filed as
    unreached, and the reason is named."""
    d = clean_tree()
    for n in (d / "06_build" / "netlists").glob("*.net"):
        n.unlink()
    r = must_pass(audit(d), "project with no exported netlist")
    contains(r.out, "no netlist exported yet")
    contains(r.out, "unreached")
    contains(r.out, "netlist(s): NONE")
    check("GHOST (" not in r.out, "an un-exported board must not be a wall of "
                                  "ghosts")


@test("an EMPTY or non-netlist file is UNGRADED at exit 2, never a green zero",
      kind="known_bad")
def t_empty_netlist_is_ungraded():
    """A crash or a silent zero are the two worst verdicts (fa22228's BOM
    post-mortem). Grading 0 references against 0 nets would report PASS on a
    truncated export, so the audit refuses and names itself.

    MEASURED pre-fix: exit 2, no such file — the same code by coincidence, which
    is why this test asserts the MESSAGE and not only the number.
    """
    d = clean_tree()
    for n in (d / "06_build" / "netlists").glob("*.net"):
        n.write_text("(export (version \"E\"))")
    r = must_fail(audit(d), "empty netlist")
    eq(r.rc, 2, "exit code for an ungradeable oracle")
    contains(r.out, "E-NETREF: UNGRADED")
    contains(r.out, "refusing")


# ------------------------------------------------- the real incident, real bytes
@test("the REAL cooksense pre-fix silk caption is caught: `GND_ISO ONLY` on "
      "the proof floorplan against the real netlist", kind="known_bad")
def t_real_cooksense_silk_ghost():
    """Not a model of the incident — the incident. `06_build/proof/
    floorplan_p0proof.yaml` still carries the shipped caption verbatim, and
    `06_build/netlists/cooksense.net` is the netlist it was printed against.
    Both are read READ-ONLY into a scratch tree; no project file is written.

    MEASURED: 1 ghost of 31 reference sites, near-miss `GND` named.
    """
    if not (PROOF_FP.is_file() and REAL_NET.is_file()):
        check(False, f"missing real evidence: {PROOF_FP} / {REAL_NET}")
    d = tmpdir("nra_real_")
    (d / "03_src").mkdir(parents=True)
    (d / "06_build" / "netlists").mkdir(parents=True)
    (d / "03_src" / "floorplan.yaml").write_bytes(PROOF_FP.read_bytes())
    (d / "06_build" / "netlists" / "cooksense.net").write_bytes(
        REAL_NET.read_bytes())
    r = must_fail(audit(d), "the shipped GND_ISO caption",
                  "'GND_ISO' is NOT a net on this board")
    contains(r.out, "[K11]")
    contains(r.out, "KEYPAD ISOLATION COMB")
    contains(r.out, "'GND'")


@test("the fleet sweep prints a per-board denominator for every project and "
      "keeps its verdicts apart")
def t_real_fleet_denominators():
    """`--root` is the census that argues for the gate. The assertion is a
    PROPERTY — every project gets a named verdict line with an `N/M` — never
    the counts, which change as the boards are fixed (and pinning them is how
    a test ends up measuring the repo's size instead of the gate's behaviour).
    """
    r = run([KPY, NRA, "--root", str(ROOT)])
    check(r.rc in (0, 1), f"fleet sweep should grade, got rc={r.rc}\n{r.out}")
    projs = [p.name for p in sorted((ROOT / "projects").glob("*"))
             if p.is_dir()]
    check(projs, "no projects to sweep")
    verdicts = [l for l in r.out.splitlines() if l.startswith("E-NETREF: ")]
    eq(len(verdicts), len(projs), "one verdict per project")
    for p in projs:
        contains(r.out, f"audit — {p}", "per-board header")
    for v in verdicts:
        contains(v, "references resolved", "verdict carries its denominator")
    check(any("FAIL" in v for v in verdicts) or
          all("PASS" in v for v in verdicts),
          "verdicts must be one of PASS/FAIL")


@test("pluto-cal-switch — the board whose keep_short budgets were re-pointed "
      "to the nets their own parts touch — resolves EVERY reference")
def t_real_clean_board():
    """The clean half on real bytes, and an independent cross-check of the
    oracle: `policy_audit.py` P-ADJ reports `58/58 declared budgets graded` on
    this board through pcbnew, and this gate resolves the same 58 `keep_short`
    nets through a regex read of the netlist. Two methods, one answer (canon
    M1) — if they ever disagree, one of them is reading the wrong thing.
    """
    proj = ROOT / "archived_projects" / "pluto-cal-switch"
    if not (proj / "06_build" / "netlists").is_dir():
        check(False, f"missing {proj}")
    r = must_pass(audit(proj), "pluto-cal-switch net references")
    contains(r.out, "E-NETREF: PASS")
    contains(r.out, "0 ghost")
    import re as _re
    m = _re.search(r"K7\s+(\d+)\s+(\d+)\s+(\d+)", r.out)
    check(m, "no K7 row in the report")
    eq(m.group(1), m.group(2), "K7 keep_short found == resolved")
    eq(m.group(3), "0", "K7 ghosts")


if __name__ == "__main__":
    sys.exit(main())
