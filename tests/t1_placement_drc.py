#!/usr/bin/env python3
"""T1: exact pre-review placement DRC classification."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, contains, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

GATE = SCRIPTS / "placement_drc_check.py"


def report(violations=None, unconnected=None, parity=None):
    d = tmpdir("pdrc_")
    p = d / "pre_route.json"
    p.write_text(json.dumps({
        "violations": violations or [],
        "unconnected_items": unconnected or [],
        "schematic_parity": parity or [],
    }))
    return p


@test("P-DRC accepts declared preliminary islands and observes unrouted items")
def t_clean_unrouted():
    p = report([{"type": "isolated_copper", "description": "preliminary"}],
               [{"description": "ratsnest"}] * 3)
    r = must_pass(run([KPY, GATE, p]), "unrouted placement")
    contains(r.out, "3 unrouted connection(s) observed", "coverage")


@test("P-DRC rejects a different-net short before review", kind="known_bad")
def t_short():
    p = report([{"type": "shorting_items",
                 "description": "Items shorting nets GND and 5VA_RAW"}])
    must_fail(run([KPY, GATE, p]), "placement short", "shorting_items")


@test("P-DRC rejects footprint-library and clearance defects", kind="known_bad")
def t_other_defects():
    p = report([{"type": "lib_footprint_issues", "description": "missing"},
                {"type": "clearance", "description": "0 mm"}])
    r = must_fail(run([KPY, GATE, p]), "placement defects",
                  "lib_footprint_issues")
    contains(r.out, "clearance", "second finding")


@test("P-DRC rejects schematic parity with no ordinary violation", kind="known_bad")
def t_parity():
    p = report(parity=[{"description": "missing footprint"}])
    must_fail(run([KPY, GATE, p]), "placement parity", "schematic-parity")


@test("P-DRC exposes no generic defect-suppression option", kind="known_bad")
def t_no_generic_allowlist():
    p = report([{"type": "shorting_items", "description": "real short"}])
    r = run([KPY, GATE, p, "--allow", "shorting_items"])
    if r.rc != 2:
        raise AssertionError(f"expected invocation exit 2, got {r.rc}: {r.out}")


@test("P-DRC refuses a structurally incomplete report", kind="known_bad")
def t_ungraded():
    d = tmpdir("pdrc_bad_")
    p = d / "bad.json"
    p.write_text('{"violations": []}')
    r = run([KPY, GATE, p])
    if r.rc != 3:
        raise AssertionError(f"expected graded-nothing exit 3, got {r.rc}: {r.out}")


if __name__ == "__main__":
    sys.exit(main())
