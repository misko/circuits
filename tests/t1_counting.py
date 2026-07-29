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


# ============================== G-COVER zero denominators (2026-07-27) ======
# Every one of these was a GREEN EXIT before this change. They are the same
# defect the two gates above exist to catch, one level up: the gate ran, looked
# at nothing, and said so in a way indistinguishable from success.


@test("count_parity FAILS when the base source carries ZERO refdes",
      kind="known_bad")
def t_count_zero_denominator():
    """A manifest with an empty `components:` list makes every comparison
    vacuously equal — `ok board == manifest (0 components)` for each source,
    exit 0. And a manifest that lists NOTHING is exactly what a silent drop of
    EVERY component looks like from here.
    RED-VERIFIED against pre-fix code (git show 5054b07:...count_parity.py):
    it exits 0 printing three `ok` lines."""
    d = project(refs_manifest=[], refs_cj=[], refs_sch=[], refs_board=[])
    r = must_fail(run([KPY, COUNT, d]), "count_parity over an empty tree",
                  "0 refdes")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")


@test("count_parity NAMES the file behind each source, and does not silently "
      "truncate its finding")
def t_count_names_inputs_and_full_count():
    """G-INPUT: `board`/`netlist` named a KIND, never a PATH, so a glob that
    picked the wrong one of several files was invisible — and `missing[:8]`
    reported 8 of 12 refs as if 8 were the answer (a campaign report quoted
    that 8). Twelve refs are dropped here; the output must carry BOTH the
    truncated sample and the true total."""
    twelve = [f"RX{i}" for i in range(1, 13)]     # RX*, so none collide with REFS
    d = project(refs_manifest=REFS + twelve)
    r = must_fail(run([KPY, COUNT, d]), "count_parity with 12 dropped",
                  "S-COUNT")
    contains(r.out, "12 TOTAL", "states the FULL count beside the sample")
    contains(r.out, "manifest.yaml", "names the path of the base source")
    contains(r.out, "04_kicad", "names the path of the board it read")


@test("tsx_preflight FAILS a project with no part.yaml at all", kind="known_bad")
def t_pre_zero_parts():
    """A wrong directory, or a stage not yet run, produced
    `TSX-PRE: all multi-pin pad names tsx-safe or mapped` and exit 0 over ZERO
    parts. RED-VERIFIED: pre-fix this exits 0."""
    d = project()          # no part() calls: 02_parts does not exist
    r = must_fail(run([KPY, PRE, d]), "tsx_preflight over zero parts",
                  "0/0 parts graded")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")


@test("tsx_preflight NAMES the padmap it graded against, present or ABSENT")
def t_pre_names_padmap():
    """The verdict depends entirely on parity_padmap.txt, and an ABSENT padmap
    is the case where every alphanumeric pad is uncovered — so its absence has
    to be stated, not inferred from a FAIL list."""
    d = project()
    part(d, "PLAIN", ["1", "2", "3"])
    r = must_pass(run([KPY, PRE, d]), "tsx_preflight with no padmap needed")
    contains(r.out, "parity_padmap.txt", "names the padmap path")
    contains(r.out, "ABSENT", "says the padmap is missing rather than implying it")
    contains(r.out, "1/1", "carries an N/M denominator")


def two_board_project():
    """A project that builds TWO boards, like smc0985-cooksense. The manifest
    describes board A; board B is a DIFFERENT, disjoint set of refdes."""
    d = project()                                    # manifest/cj/sch/board = REFS
    ts = d / "03_tscircuit"
    other = ["X9", "Y9"]
    (ts / "kicad" / "other.kicad_sch").write_text(sch_text(other))
    (d / "04_kicad" / "other.kicad_pcb").write_text("".join(
        f'(footprint (property "Reference" "{r}"))\n' for r in other))
    return d


@test("count_parity REFUSES to guess a board when the project builds two",
      kind="known_bad")
def t_multiboard_ambiguity_is_refused():
    """THE INCIDENT (2026-07-28, smc0985-cooksense v1.7): every artifact was
    chosen with `paths[0]` off an UNSORTED glob, and `--board` was accepted on
    the command line and silently IGNORED — the script never parsed past
    argv[1]. So S-COUNT graded `interposer.kicad_pcb`, `interposer.kicad_sch`
    and `interposer.net` against COOKSENSE's manifest and reported
    `S-COUNT FAIL: 0/4`. Three of those four "disagreements" were the tool
    reading a different board.

    Both halves were bad: a WRONG red here would have sent someone hunting 234
    phantom refdes, and an unsorted `[0]` is not deterministic between runs, so
    a GREEN could not have been trusted either.

    RED-VERIFIED 2026-07-28 by git-swapping the pre-fix count_parity.py back in.
    Stated precisely, because the obvious guess is wrong: pre-fix it does NOT
    exit 0 here. It grades one board against the other's manifest, so it exits 1
    with a phantom symmetric difference — a red for entirely the wrong reason.
    This test therefore fails pre-fix on the `--board` assertion, not on
    must_fail: `tells the caller how to disambiguate does not contain '--board'`.
    That distinction is the whole point — the old failure mode was a CONFIDENT
    WRONG RED, which is worse than a green, and `must_fail` alone cannot tell
    the two apart.
    """
    d = two_board_project()
    r = must_fail(run([KPY, COUNT, d]), "count_parity on a 2-board project")
    contains(r.out, "--board", "tells the caller how to disambiguate")
    for stem in ("board", "other"):
        contains(r.out, stem, f"names candidate {stem!r} rather than picking one")


@test("count_parity --board selects that board, and the OTHER board's refdes "
      "never enter the comparison")
def t_board_selects():
    """The positive half: with --board named, every source resolves to the SAME
    board and the disjoint second board is invisible. Without this the guard
    above could be satisfied by a tool that simply always refuses."""
    d = two_board_project()
    r = must_pass(run([KPY, COUNT, d, "--board", "board"]),
                  "count_parity --board board")
    contains(r.out, "4/4", "all four sources agree once the board is named")
    check("X9" not in r.out and "Y9" not in r.out,
          f"the other board's refdes leaked into the comparison:\n{r.out}")


@test("count_parity FAILS a --board that matches nothing, naming what exists",
      kind="known_bad")
def t_board_typo_is_refused():
    """A typo must not silently fall back to `[0]` — that would reintroduce the
    defect through the door marked 'convenience'.

    RED-VERIFIED 2026-07-28 (git-swap): pre-fix the flag is ignored entirely, so
    the run is indistinguishable from the no-flag case — it exits 1 from the
    wrong-board mismatch while never quoting the name it failed to match. The
    test goes red on `contains('nosuchboard')`, which is the assertion that
    separates 'refused the typo' from 'happened to fail anyway'."""
    d = two_board_project()
    r = must_fail(run([KPY, COUNT, d, "--board", "nosuchboard"]),
                  "count_parity with a bogus --board")
    contains(r.out, "nosuchboard", "quotes the name it could not match")
    contains(r.out, "board", "lists the stems that DO exist")


if __name__ == "__main__":
    sys.exit(main())
