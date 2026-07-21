#!/usr/bin/env python3
"""T1: the counting gates — count_parity.py (S-COUNT) + tsx_preflight.py.

Motivating incident (2026-07-21, clean-room usb-pwr-hub-3s session 1):
`tsci build` silently dropped all 4 USB connectors — 48/52 components with
ERC still 0 — because tscircuit rejects alphanumeric pad ids (USB-C A1..B12,
shield SH) without failing the build. Every generated artifact AGREED with
every other one; only the author's declared intent disagreed. Hence:
manifest.yaml (intent) is the parity base, and tsx_preflight blocks the
cause before the first build.

RED-VERIFIED (new-gate variant): neither checker exists at 6a5bd82 — the
suite cannot run against pre-fix code; the gate could not exist. Each
known-bad fixture breaks a passing tree in exactly one way.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, check, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

COUNT = SCRIPTS / "count_parity.py"
PRE = SCRIPTS / "tsx_preflight.py"

REFS = ["C1", "R1", "U1", "J1"]


def sch_text(refs):
    blocks = "".join(
        f'(symbol (lib_id "x:{r}")\n  (property "Reference" "{r}" (at 0 0 0))\n'
        f'  (pin "1")\n)\n' for r in refs)
    return f"(kicad_sch {blocks})"


def project(refs_manifest=REFS, refs_cj=REFS, refs_sch=REFS, refs_board=REFS):
    d = tmpdir("cnt_")
    ts = d / "03_tscircuit"
    (ts / "build").mkdir(parents=True)
    (ts / "kicad").mkdir()
    (d / "04_kicad").mkdir()
    (ts / "manifest.yaml").write_text(
        "components: [" + ", ".join(refs_manifest) + "]\n")
    (ts / "build" / "circuit.json").write_text(json.dumps(
        [{"type": "source_component", "name": r} for r in refs_cj]))
    (ts / "kicad" / "board.kicad_sch").write_text(sch_text(refs_sch))
    (d / "04_kicad" / "board.kicad_pcb").write_text("".join(
        f'(footprint (property "Reference" "{r}"))\n' for r in refs_board))
    return d


def part(d, mpn, pins):
    pd = d / "02_parts" / mpn
    pd.mkdir(parents=True)
    pinlines = "".join(f"  {k}: P{k}\n" for k in pins)
    (pd / "part.yaml").write_text(f"mpn: {mpn}\npins:\n{pinlines}")


# ------------------------------------------------------------ clean cases
@test("count_parity passes when every representation agrees")
def t_count_clean():
    must_pass(run([KPY, COUNT, project()]), "count_parity on agreeing tree")


@test("tsx_preflight passes numeric pads, and mapped alphanumeric pads")
def t_pre_clean():
    d = project()
    part(d, "PLAIN", ["1", "2", "3"])
    part(d, "USBC", ["A1", "B12", "SH"])
    (d / "03_tscircuit" / "parity_padmap.txt").write_text(
        "13 A1\n14 B12\n15 SH\n")
    must_pass(run([KPY, PRE, d]), "tsx_preflight with covering padmap")


# -------------------------------------------------------- known-bad cases
@test("count_parity FAILS the incident: silent drop agreed on by every "
      "generated artifact, caught only by declared intent", kind="known_bad")
def t_silent_drop():
    # J1 dropped from circuit.json AND sch AND board — exactly what tsci's
    # silent rejection produces. Only manifest still declares it.
    short = ["C1", "R1", "U1"]
    d = project(refs_cj=short, refs_sch=short, refs_board=short)
    r = must_fail(run([KPY, COUNT, d]), "count_parity on silent drop", "S-COUNT")
    contains(r.out, "J1", "the dropped part is NAMED")


@test("count_parity FAILS a board missing one placed part", kind="known_bad")
def t_board_missing():
    d = project(refs_board=["C1", "R1", "U1"])
    must_fail(run([KPY, COUNT, d]), "count_parity on short board", "S-COUNT")


@test("tsx_preflight FAILS unmapped alphanumeric pads (the drop's cause)",
      kind="known_bad")
def t_pre_unmapped():
    d = project()
    part(d, "USBC", ["A1", "A6", "SH"])
    r = must_fail(run([KPY, PRE, d]), "tsx_preflight without padmap", "TSX-PRE")
    contains(r.out, "USBC", "the offending part is NAMED")
    contains(r.out, "silently", "remedy text explains the silent-drop stake")


if __name__ == "__main__":
    main()
