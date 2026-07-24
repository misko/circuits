#!/usr/bin/env python3
"""T1: tsx_to_board.sh backend selection (ADR-0002 amendment 2026-07-23).

The gap: tsx_to_board.sh hard-required a bespoke 03_src/generate_board.py
(its old line-48 FATAL) although the DEFAULT for every current board is the
SHARED GENERIC BACKEND (floorplan.yaml + route.yaml + rules/, zero
board-specific Python). That made the one-command driver a legacy-only tool —
ADR-0002's amendment tracked the retrofit as open work. Now: generate_board.py
present -> bespoke path, behavior unchanged; absent but floorplan.yaml present
-> fall through to the generic chain (generate_board_generic /
route_and_stitch_generic / generate_rules_generic, reparented into the
isolated build root); neither -> a FATAL naming BOTH options.

These are hermetic PROPERTY tests of the mode selection and early fatals —
they stop before tsci build (no bun, no network, no kicad-cli). The full
generic chain itself is proven by t2_route_stitch.py / e2e_boards.py on the
real boards.

RED-VERIFIED against pre-fix code (git show HEAD:skills/kicad-pcb/scripts/
tsx_to_board.sh swapped in, 2026-07-23): ALL FIVE tests fail against it —
t_generic_falls_through / t_no_backend_names_both because the old driver
FATALs "backend not present" without ever considering floorplan.yaml, the
banner tests because the old driver has no "backend :" line, and
t_bespoke_unchanged because of a LATENT pre-fix bug this change also fixes:
under `set -euo pipefail` the `TSX=$(ls ... | head -1)` pipeline exits the
script SILENTLY (rc 2, no message) when no tsx exists, so the old "FATAL: no
.../src/*.tsx" line was unreachable. The bespoke path's behavior with a tsx
present is unchanged; without one it now actually prints its FATAL (same
exit code 2). Restored the fixed file afterwards.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (SCRIPTS, check, contains, main, must_fail,  # noqa: E402
                     not_contains, run, test, tmpdir)

DRIVER = SCRIPTS / "tsx_to_board.sh"

FLOORPLAN = """\
project:
  name: scratch_board
  netlist: 06_build/netlists/scratch_board.net
  output: 04_kicad/scratch_board.kicad_pcb
"""


def project(bespoke=False, generic=False, tsx=False):
    d = tmpdir("t2b_")
    (d / "03_src").mkdir()
    (d / "03_tscircuit" / "src").mkdir(parents=True)
    if bespoke:
        (d / "03_src" / "generate_board.py").write_text(
            'NETLIST = "scratch_board.net"\n')
    if generic:
        (d / "03_src" / "floorplan.yaml").write_text(FLOORPLAN)
    if tsx:
        (d / "03_tscircuit" / "src" / "scratch.tsx").write_text("// tsx\n")
    return d


@test("no generate_board.py AND no floorplan.yaml = FATAL naming BOTH options",
      kind="known_bad")
def t_no_backend_names_both():
    d = project()
    r = must_fail(run(["bash", DRIVER, d]), "driver with no backend at all",
                  "no backend present")
    contains(r.out, "generate_board.py", "fatal names the bespoke option")
    contains(r.out, "floorplan.yaml", "fatal names the generic option")
    check(r.rc == 2, f"backend fatal must exit 2, got {r.rc}")


@test("floorplan.yaml WITHOUT generate_board.py falls through to the generic "
      "backend (the retrofitted line-48 FATAL)")
def t_generic_falls_through():
    """The deliverable: a generic-backend board (i.e. every current board)
    must get PAST the old FATAL. With no tsx present the driver then stops at
    the tsx check — proving mode selection happened and the bespoke
    requirement is gone."""
    d = project(generic=True)
    r = run(["bash", DRIVER, d])
    check(r.rc != 0, "no tsx: the driver still stops, later")
    not_contains(r.out, "backend not present",
                 "the old bespoke-only FATAL must not fire on a generic board")
    contains(r.out, "src/*.tsx", "it proceeded to the tsx check")


@test("generic mode parses the board name from floorplan.yaml project.output")
def t_generic_board_name():
    d = project(generic=True, tsx=True)
    # tsci is not on PATH in the test env; the banner prints BEFORE step [1],
    # so the board-name property is observable hermetically.
    r = run(["bash", DRIVER, d], env={"PATH": "/usr/bin:/bin"})
    contains(r.out, "board name   : scratch_board", "name from project.output")
    contains(r.out, "backend      : generic", "mode line printed")


@test("bespoke path is UNCHANGED: generate_board.py present, no tsx = the "
      "same tsx FATAL as before the retrofit")
def t_bespoke_unchanged():
    d = project(bespoke=True)
    r = must_fail(run(["bash", DRIVER, d]), "bespoke project without tsx",
                  "src/*.tsx")
    not_contains(r.out, "backend not present", "no spurious backend fatal")


@test("bespoke wins when BOTH backends are present (legacy priority)")
def t_bespoke_priority():
    d = project(bespoke=True, generic=True, tsx=True)
    r = run(["bash", DRIVER, d], env={"PATH": "/usr/bin:/bin"})
    contains(r.out, "backend      : bespoke", "generate_board.py takes priority")
    contains(r.out, "board name   : scratch_board", "name parsed from .net ref")


if __name__ == "__main__":
    sys.exit(main())
