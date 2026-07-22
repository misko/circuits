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


if __name__ == "__main__":
    sys.exit(main())
