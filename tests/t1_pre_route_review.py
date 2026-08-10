#!/usr/bin/env python3
"""T1: fail-closed, exact-artifact pre-route review boundary."""
import hashlib
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, contains, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

GATE = SCRIPTS / "pre_route_review_check.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def netlist_sha(path):
    """Expected netlist digest, derived INDEPENDENTLY of the gate (canon M1).

    The gate normalizes KiCad's volatile export metadata before hashing. This
    fixture re-derives the same expectation with its own substitution rather
    than importing `netlist_digest`, so a change to the gate's normalization
    shows up as a test failure instead of being silently agreed with.
    """
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace('(date "2026-01-01T00:00:00")',
                        '(date "<KICAD_EXPORT_DATE>")')
    return hashlib.sha256(text.encode()).hexdigest()


def fixture():
    d = tmpdir("prreview_")
    for rel in ("02_parts/X", "03_src/rules", "04_kicad", "06_build/pre_route"):
        (d / rel).mkdir(parents=True, exist_ok=True)
    (d / "02_parts/X/part.yaml").write_text("mpn: X\npins: {1: A, 2: B}\n")
    board = d / "04_kicad/demo.kicad_pcb"
    netlist = d / "04_kicad/demo.net"
    board.write_text("(kicad_pcb pre-route-placement)\n")
    # The netlist carries a KiCad export date because `netlist_digest`
    # normalizes exactly one and refuses a file with none — a fixture without
    # it exercises the error path, not the canonicalization the gate ships.
    netlist.write_text(
        '(export (design (date "2026-01-01T00:00:00"))'
        " (nets (net (code 1) (name GND))))\n")
    parts_hash = hashlib.sha256(
        b"02_parts/X/part.yaml\0" + (d / "02_parts/X/part.yaml").read_bytes() + b"\0"
    ).hexdigest()
    paths = {k: f"06_build/pre_route/{k}.md"
             for k in ("topology", "pin", "layout", "render")}
    cfg = {"project": {"board": "04_kicad/demo.kicad_pcb"},
           "flow": {"pre_route_reviews": {
               **paths, "board": "04_kicad/demo.kicad_pcb",
               "netlist": "04_kicad/demo.net",
               "a_render": "06_build/pre_route/a_render.md"}}}
    (d / "03_src/route.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False))
    (d / "03_src/rules/requirements.yaml").write_text(
        "schema: 1\npower_claims: []\n"
        "no_external_power_outputs: Fixture has none.\n")
    rule_files = sorted((d / "03_src/rules").glob("*.yaml")) + [d / "03_src/route.yaml"]
    rules_hash = hashlib.sha256(b"".join(
        p.relative_to(d).as_posix().encode() + b"\0" + p.read_bytes() + b"\0"
        for p in rule_files)).hexdigest()
    for kind, rel in paths.items():
        binding = (f"netlist_sha256: {netlist_sha(netlist)}\nparts_sha256: {parts_hash}\n"
                   if kind == "topology" else f"board_sha256: {sha(board)}\n")
        binding += f"design_rules_sha256: {rules_hash}\n"
        if kind == "pin":
            binding += f"parts_sha256: {parts_hash}\n"
        (d / rel).write_text(
            f"review_stage: pre-route\nreview_kind: {kind}\n"
            "design_verdict: SOUND\n" + binding)
    (d / "06_build/pre_route/a_render.md").write_text(
        f"a-render_verdict: PASS\nboard_sha256: {sha(board)}\n")
    return d, board


@test("PR-REVIEW passes current SOUND schematic and placement evidence")
def t_green():
    d, _ = fixture()
    must_pass(run([KPY, GATE, d, "--phase", "schematic"]), "schematic witness")
    must_pass(run([KPY, GATE, d, "--phase", "placement"]), "placement witness")


@test("PR-REVIEW blocks routing when a review is missing", kind="known_bad")
def t_missing():
    d, _ = fixture()
    (d / "06_build/pre_route/pin.md").unlink()
    must_fail(run([KPY, GATE, d, "--phase", "placement"]),
              "missing review", "missing review")


@test("PR-REVIEW blocks a DEFECTIVE verdict", kind="known_bad")
def t_defective():
    d, _ = fixture()
    p = d / "06_build/pre_route/topology.md"
    p.write_text(p.read_text().replace("SOUND", "DEFECTIVE"))
    must_fail(run([KPY, GATE, d, "--phase", "schematic"]),
              "defective topology", "not SOUND")


@test("PR-REVIEW invalidates placement evidence after the board changes",
      kind="known_bad")
def t_stale_board():
    d, board = fixture()
    board.write_text(board.read_text() + "(footprint moved)\n")
    result = must_fail(run([KPY, GATE, d, "--phase", "placement"]),
                       "stale placement", "board_sha256 is stale")
    contains(result.out, "A-RENDER: board_sha256 is stale", "render gate also stale")


@test("PR-REVIEW invalidates topology evidence after the netlist changes",
      kind="known_bad")
def t_stale_netlist():
    d, _ = fixture()
    p = d / "04_kicad/demo.net"
    p.write_text(p.read_text() + "(net (code 2) (name VIN))\n")
    must_fail(run([KPY, GATE, d, "--phase", "schematic"]),
              "stale topology", "netlist_sha256 is stale")


@test("PR-REVIEW invalidates schematic and placement evidence after an adopted "
      "design rule changes", kind="known_bad")
def t_stale_design_rules():
    d, _ = fixture()
    p = d / "03_src/rules/requirements.yaml"
    p.write_text(p.read_text().replace("Fixture has none", "Fixture changed"))
    must_fail(run([KPY, GATE, d, "--phase", "schematic"]),
              "stale topology rule binding", "design_rules_sha256 is stale")
    must_fail(run([KPY, GATE, d, "--phase", "placement"]),
              "stale placement rule binding", "design_rules_sha256 is stale")


@test("PR-REVIEW refuses an absent adoption block instead of silently passing",
      kind="known_bad")
def t_unmigrated():
    d, _ = fixture()
    path = d / "03_src/route.yaml"
    doc = yaml.safe_load(path.read_text())
    del doc["flow"]["pre_route_reviews"]
    path.write_text(yaml.safe_dump(doc))
    must_fail(run([KPY, GATE, d, "--phase", "schematic"]),
              "unmigrated", "not a pass")


@test("G-VACUOUS PR-REVIEW: a colluding or incompetent reviewer can write SOUND",
      kind="vacuity", gate="pre_route_review_check.py")
def t_vacuity_review_independence_is_not_machine_derivable():
    d, _ = fixture()
    result = must_pass(run([KPY, GATE, d, "--phase", "schematic"]),
                       "syntactically valid but not independently authored review")
    contains(result.out, "PR-REVIEW PASS", "declared blind spot reproduced")


if __name__ == "__main__":
    sys.exit(main())
