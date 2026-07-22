#!/usr/bin/env python3
"""T2: grind_driver.py — the BOUNDED mechanical DRC grind loop.

The one property that matters most here is NEGATIVE: the driver must be
UNABLE to loop forever. A synthetic board whose findings never improve
must terminate with the D-BACK escalation within 3 cycles; a novel class
must terminate immediately; table-escalate classes must stop the loop with
a report, not be "fixed". An unbounded auto-fixer is worse than none.

Hermetic via the documented test seams (the stub_krt pattern):
--check-cmd replaces measurement with a scripted stub that emits the Nth
gate.json of a sequence; --rebuild-cmd replaces the auto-fix chain with a
logger. Exit codes are the contract: 0 clean, 2 table-escalate, 3 novel,
4 D-BACK/cap.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     must_pass, run, test, tmpdir)

GRIND = SCRIPTS / "grind_driver.py"


def gate(unconnected=0, parity=0, **classes):
    """A gate.json-shaped findings dict."""
    g = {"violations": [], "unconnected_items": [], "schematic_parity": []}
    for cls, n in classes.items():
        for i in range(n):
            g["violations"].append(
                {"type": cls, "description": f"{cls} sample {i}",
                 "items": [{"description": f"item {i} [NETA]"},
                           {"description": f"item {i} [NETB]"}]})
    for i in range(unconnected):
        g["unconnected_items"].append(
            {"items": [{"description": f"Pad 1 [N{i}] of U{i}"},
                       {"description": f"Pad 2 [N{i}] of U{i}"}]})
    for i in range(parity):
        g["schematic_parity"].append({"description": f"parity {i}"})
    return g


def grind_scratch(seq):
    """A scratch tree + a check stub that emits seq[n] on the nth call and
    a rebuild stub that logs each invocation."""
    d = tmpdir("t2g_")
    (d / "seq.json").write_text(json.dumps(seq))
    stub = d / "check_stub.py"
    stub.write_text(
        "import json, sys, pathlib\n"
        "d = pathlib.Path(__file__).parent\n"
        "c = d / 'counter'\n"
        "n = int(c.read_text()) if c.is_file() else 0\n"
        "seq = json.loads((d / 'seq.json').read_text())\n"
        "c.write_text(str(n + 1))\n"
        "pathlib.Path(sys.argv[1]).write_text("
        "json.dumps(seq[min(n, len(seq) - 1)]))\n")
    rebuild = d / "rebuild_stub.py"
    rebuild.write_text(
        "import pathlib\n"
        "p = pathlib.Path(__file__).parent / 'rebuild_log'\n"
        "p.write_text(p.read_text() + 'x' if p.is_file() else 'x')\n")
    return d


def grind(d, extra=()):
    return run([KPY, GRIND, d,
                "--check-cmd", f"{sys.executable} {d / 'check_stub.py'} {{out}}",
                "--rebuild-cmd", f"{sys.executable} {d / 'rebuild_stub.py'}",
                *extra])


def cycles_run(d):
    c = d / "counter"
    return int(c.read_text()) if c.is_file() else 0


def rebuilds_run(d):
    p = d / "rebuild_log"
    return len(p.read_text()) if p.is_file() else 0


@test("grind auto-fixes a batch class, reaches 0/0/0 and journals each cycle")
def t_grind_auto_clean():
    """The mechanical loop working as intended: text_height (an auto class —
    the v4 112-finding incident) triggers ONE rebuild rerun, the re-measure
    is clean, exit 0. Each cycle appends an M9 journal entry with MEASURED
    counts, and no escalation report is written."""
    d = grind_scratch([gate(text_height=3, lib_footprint_issues=2), gate()])
    r = must_pass(grind(d), "grind on a self-healing batch class")
    contains(r.out, "0/0/0", "the clean verdict")
    eq(cycles_run(d), 2, "measurement cycles")
    eq(rebuilds_run(d), 1, "exactly one auto-fix rebuild")
    j = (d / "01_docs" / "journal" / "routing.md").read_text()
    contains(j, "iterate 1 (grind)", "M9 journal cycle 1")
    contains(j, "iterate 2 (grind)", "M9 journal cycle 2")
    contains(j, "text_height=3", "measured counts in the journal")
    contains(j, "total 0 findings", "the clean measurement is journaled too")
    check(not (d / "06_build" / "grind_escalation.md").exists(),
          "a clean run must not write an escalation report")


@test("grind classifies same-net zone<->zone splits as the AUTO class "
      "unconnected_zone_islands and rebuilds to clean")
def t_grind_zone_islands_auto():
    """The v4 usb-hub-3s tail (2026-07-21): 4 of the last 7 gate findings
    were unconnected_items whose BOTH sides read 'Zone [X]' of the same net
    (LX1/LX2/VIN_S/VBUSA3) — a pour filled as disconnected islands, which
    the stitch `heal_islands` pass now fixes mechanically. classify_gate
    must split this class out of the escalate-only `unconnected` so the
    grind table's auto entry (fix: rerun stitch with heal_islands, via the
    rebuild chain) fires instead of summoning the designer. A MIXED item
    (pad<->zone, same net) must stay `unconnected`. RED-verified against
    the pre-split classifier (git stash swap, 2026-07-21): everything lands
    in `unconnected` there, the run exits 2 (table-escalate), and this test
    fails on the exit code."""
    def zone_split(net):
        d2 = f"Zone [{net}] on F.Cu, priority 2"
        return {"type": "unconnected_items", "severity": "error",
                "items": [{"description": d2}, {"description": d2}]}
    g0 = gate()
    for net in ("LX1", "LX2", "VIN_S", "VBUSA3"):
        g0["unconnected_items"].append(zone_split(net))
    d = grind_scratch([g0, gate()])
    r = must_pass(grind(d), "grind on an all-zone-island tail")
    contains(r.out, "unconnected_zone_islands=4", "the split-out class")
    eq(rebuilds_run(d), 1, "exactly one auto-fix rebuild")
    contains(r.out, "0/0/0", "the clean verdict")
    # mixed pad<->zone same net is NOT the heal class — must still escalate
    g1 = gate()
    g1["unconnected_items"].append(
        {"type": "unconnected_items", "severity": "error",
         "items": [{"description": "Pad 18 [LX1] of U1 on F.Cu"},
                   {"description": "Zone [LX1] on F.Cu, priority 2"}]})
    d = grind_scratch([g1])
    r = grind(d)
    eq(r.rc, 2, "pad<->zone must remain the escalate-only `unconnected`")


@test("grind CANNOT loop forever: a never-improving board escalates D-BACK "
      "within 3 cycles", kind="known_bad")
def t_kb_grind_dback():
    """THE hard requirement. The stub reports the same 3 text_height
    findings every cycle — an auto class, so a naive driver would rebuild
    forever. After 3 consecutive measurements without total-count
    improvement the driver must stop with the distinct D-BACK exit code
    and the escalation report, having run at most 3 cycles / 2 fix
    attempts. RED-verified 2026-07-21 against a stall-disabled driver
    (sed the trigger to 999): it ground to the 12-cycle cap and this test
    failed on 'ran 12'."""
    d = grind_scratch([gate(text_height=3)])
    r = grind(d)
    eq(r.rc, 4, "the distinct D-BACK exit code")
    check(cycles_run(d) <= 3,
          f"D-BACK must bite within 3 cycles, ran {cycles_run(d)}")
    check(rebuilds_run(d) <= 2,
          f"too many fix attempts before stopping: {rebuilds_run(d)}")
    esc = (d / "06_build" / "grind_escalation.md").read_text()
    contains(esc, "D-BACK", "the report names the stop condition")
    contains(esc, "text_height", "the stuck class is in the report")
    contains(esc, "3 -> 3 -> 3", "the per-cycle totals are in the report")


@test("a NOVEL class with no table entry escalates immediately",
      kind="known_bad")
def t_kb_grind_novel():
    """An auto-fixer guessing at an unknown finding class is the unbounded
    failure mode. One cycle, no fix attempt, distinct exit code, report
    names the class."""
    d = grind_scratch([gate(text_height=1, quantum_flux=2)])
    r = grind(d)
    eq(r.rc, 3, "the distinct novel-class exit code")
    eq(cycles_run(d), 1, "must stop after the first measurement")
    eq(rebuilds_run(d), 0, "must not attempt any fix")
    esc = (d / "06_build" / "grind_escalation.md").read_text()
    contains(esc, "quantum_flux", "the novel class is named")
    contains(esc, "no grind_fixes.yaml entry", "why there is no auto-fix")


@test("table-escalate classes (real work) stop the loop with a compact "
      "report", kind="known_bad")
def t_kb_grind_escalate():
    """clearance + unconnected are the REAL-work classes (141 + 41 of the
    v4 648). The driver must not touch them: one cycle, no fix, exit 2,
    and the report carries class, count, samples and the table's `why`."""
    d = grind_scratch([gate(clearance=4, unconnected=2)])
    r = grind(d)
    eq(r.rc, 2, "the table-escalate exit code")
    eq(rebuilds_run(d), 0, "escalate classes must never be auto-fixed")
    esc = (d / "06_build" / "grind_escalation.md").read_text()
    contains(esc, "## clearance — 4", "class + count")
    contains(esc, "## unconnected — 2", "class + count")
    contains(esc, "sample", "sample items in the report")
    contains(esc, "placement", "the table's why (D-BACK ladder) rides along")
    j = (d / "01_docs" / "journal" / "routing.md").read_text()
    contains(j, "clearance=4", "measured counts journaled before escalating")


@test("the --max-cycles cap is a hard bound even while totals improve",
      kind="known_bad")
def t_kb_grind_max_cycles():
    """A slowly-improving sequence never trips D-BACK's stall counter; the
    absolute cap must stop it anyway — bounded means bounded."""
    seq = [gate(text_height=n) for n in range(30, 0, -1)]
    d = grind_scratch(seq)
    r = grind(d, extra=["--max-cycles", "4"])
    eq(r.rc, 4, "cap exits with the stagnation code")
    eq(cycles_run(d), 4, "exactly the capped number of cycles")
    contains((d / "06_build" / "grind_escalation.md").read_text(),
             "--max-cycles", "the report names the cap")



def zone_split_gate(text_height, islands):
    """total improves via text_height while zone-island unconnected stays flat."""
    g = gate(text_height=text_height)
    for i in range(islands):
        g["unconnected_items"].append(
            {"items": [{"description": f"Zone [LX{i}] on F.Cu, priority 2"},
                       {"description": f"Zone [LX{i}] on F.Cu, priority 2"}]})
    return g


@test("SUBSET plateau: unconnected flat while total improves escalates "
      "D-BACK (v4 measured: 7u flat across 3 checkpoints)", kind="known_bad")
def t_kb_grind_subset_plateau():
    """INCIDENT(2026-07-21 usb-hub-3s): the total kept dropping (cosmetic
    classes) while the unconnected subset sat flat — a masked reachability
    problem the total-stall trigger cannot see. The driver must escalate on
    4 flat nonzero unconnected cycles even though best-total improves every
    cycle. RED-verified 2026-07-21: against the pre-trigger driver (git
    stash) this sequence runs to the max-cycles cap and the test fails on
    the exit code."""
    seq = [zone_split_gate(th, 2) for th in (10, 9, 8, 7, 6, 5, 4)]
    d = grind_scratch(seq)
    r = grind(d)
    eq(r.rc, 4, "the distinct D-BACK exit code")
    check(cycles_run(d) <= 5, f"subset plateau must bite by cycle 5, ran {cycles_run(d)}")
    esc = (d / "06_build" / "grind_escalation.md").read_text()
    contains(esc, "subset plateau", "the report names the subset condition")


def zi_gate(n, same=True):
    """A gate.json with n zones_intersect violations — SAME net (the auto
    zones_intersect_same_net class) or CROSS net (a short, escalate-only)."""
    g = gate()
    for i in range(n):
        bnet = "PWR" if same else "SIG"
        g["violations"].append({
            "type": "zones_intersect", "severity": "error",
            "description": "Copper zones intersect (intersecting zones must "
                           "have distinct priorities)",
            "items": [{"description": "Zone [PWR] on F.Cu, priority 2"},
                      {"description": f"Zone [{bnet}] on F.Cu, priority 2"}]})
    return g


@test("grind classifies SAME-net zones_intersect as the AUTO class "
      "zones_intersect_same_net and rebuilds to clean")
def t_grind_zones_intersect_same_net():
    """usb-hub-3s v1.0 P3-union / v1.1 re-learn (2026-07-22): overlapping
    same-net same-priority pours. classify_gate must split same-net
    zones_intersect (both items name one net) out of the escalate-only
    cross-net `zones_intersect`, so the auto entry (fix: rerun stitch with
    unify_zone_priorities via the rebuild chain) fires instead of summoning
    the designer."""
    d = grind_scratch([zi_gate(3, same=True), gate()])
    r = must_pass(grind(d), "grind on a same-net zones_intersect tail")
    contains(r.out, "zones_intersect_same_net=3", "the split-out auto class")
    eq(rebuilds_run(d), 1, "exactly one auto-fix rebuild")
    contains(r.out, "0/0/0", "the clean verdict")


@test("grind keeps a CROSS-net zones_intersect as the escalate-only class "
      "(a short is never a priority bump)", kind="known_bad")
def t_kb_grind_zones_intersect_cross():
    """A different-net zone overlap is a SHORT: it must stay the escalate-only
    `zones_intersect`, never the auto same-net class. RED-verified by the
    reverse of the same-net split: were the cross-net pair classed auto, the
    driver would rebuild a short away — here it must exit 2 (table-escalate)."""
    d = grind_scratch([zi_gate(2, same=False)])
    r = grind(d)
    eq(r.rc, 2, "cross-net zones_intersect must escalate, not auto-fix")
    eq(rebuilds_run(d), 0, "a short must never be auto-fixed")
    contains(r.out, "zones_intersect=2", "stays the escalate-only class")


@test("the escalation report SELF-HARVESTS: a class escalated whose "
      "provenance spans >= 2 boards is flagged a promotion candidate")
def t_grind_two_strike_harvest():
    """The self-harvest hook (canon M8): when the driver escalates a class
    whose grind_fixes provenance already names >= 2 boards, it prints
    'class X escalated on boards A,B — two-strike, promotion candidate' to
    stdout and the report, so the loop flags what to mechanize NEXT.
    `unconnected` carries boards: [usb-hub-3s-v4, spf, usb-hub-3s-v1.1]."""
    d = grind_scratch([gate(unconnected=3)])
    r = grind(d)
    eq(r.rc, 2, "unconnected escalates")
    contains(r.out, "two-strike", "the hook must print to stdout")
    esc = (d / "06_build" / "grind_escalation.md").read_text()
    contains(esc, "two-strike promotion candidates", "the report section")
    contains(esc, "class unconnected escalated on boards", "the flagged class")
    contains(esc, "usb-hub-3s-v1.1", "the boards are named from provenance")


@test("self-harvest does NOT flag an already-mechanized (auto) class even if "
      "it escalates because a rebuild stalled", kind="known_bad")
def t_kb_two_strike_excludes_auto():
    """A class that is ALREADY auto (zones_intersect_same_net, 2 boards) must
    not be re-flagged as a promotion candidate — it is already mechanized.
    Forced to escalate via a never-improving same-net zones_intersect (the
    rebuild stub does not touch the synthetic findings), it hits D-BACK; the
    report must NOT carry a two-strike line for it. (Were the auto exclusion
    dropped, the hook would spam an already-done promotion.)"""
    d = grind_scratch([zi_gate(3, same=True)])   # never improves -> D-BACK
    r = grind(d)
    eq(r.rc, 4, "a stalled auto class D-BACKs")
    esc = (d / "06_build" / "grind_escalation.md").read_text()
    check("two-strike promotion candidate" not in esc
          or "zones_intersect_same_net" not in esc.split(
              "two-strike promotion candidates")[-1],
          "an auto class must not be a promotion candidate")


if __name__ == "__main__":
    sys.exit(main())
