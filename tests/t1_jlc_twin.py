#!/usr/bin/env python3
"""T1: jlc_twin.py — the JLC "digital twin" gate that mounts JLC's OWN
footprint for every BOM part and compares it to what we placed.

THE REGRESSION (2026-07-20). jlc_twin exited 0 on 11 UNVERIFIED parts.
`fetch()` classified a failure as `transient` only if the fetcher's last
output line matched TRANSIENT_PAT; ANYTHING else — an `HTTP Error 403`, a
proxy page, a python traceback — was declared `nocad`, which is a
DISPOSITION ("the library genuinely has no model") rather than a failure.
NO-CAD never enters `criticals`, so the run exited 0 while claiming the
parts were checked.

A part we could not fetch was never checked. This file pins the fail-closed
behaviour: the ONLY way to get NO-CAD is for the fetcher to say so
affirmatively AND exit 0.

NETWORK IS MOCKED. jlc_twin shells out to `easyeda2kicad`, so a stub binary
on $EASYEDA2KICAD is a complete, deterministic seam — no HTTP anywhere.
The per-LCSC cache dir (`OUTDIR/easyeda/<CODE>/jlc.pretty/*.kicad_mod`) is
the replay store: seed it and `fetch()` returns before ever invoking the
fetcher. Live-network runs live in the opt-in `--net` tier, not here.
"""
import os
import shutil
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, SCRIPTS, check, contains, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

TWIN = FAB_SCRIPTS / "jlc_twin.py"
GEN = SCRIPTS / "generate_board_generic.py"
LC = ROOT / "projects" / "cook-loadcell"
CODE = "C22775"          # a real code on cook-loadcell's BOM (R7, 100R 0603)


def stub_e2k(d, stderr="", stdout="", rc=1, emit_mod_for=None):
    """A fake easyeda2kicad. `emit_mod_for` makes it succeed by writing a
    minimal .kicad_mod into the per-code cache dir, exactly where the real
    tool would put it."""
    p = d / "easyeda2kicad_stub"
    body = ["#!/usr/bin/env python3", "import sys, os, pathlib"]
    if emit_mod_for:
        body += [
            "out = None",
            "a = sys.argv",
            "out = a[a.index('--output')+1] if '--output' in a else None",
            "d = pathlib.Path(out).parent / 'jlc.pretty'",
            "d.mkdir(parents=True, exist_ok=True)",
            f"(d / 'stub.kicad_mod').write_text({emit_mod_for!r})",
        ]
    if stdout:
        body.append(f"sys.stdout.write({stdout!r})")
    if stderr:
        body.append(f"sys.stderr.write({stderr!r})")
    body.append(f"sys.exit({rc})")
    p.write_text("\n".join(body) + "\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return p


MINIMAL_MOD = (
    '(footprint "R_0603" (version 20240108) (generator "test")\n'
    '  (layer "F.Cu")\n'
    '  (pad "1" smd roundrect (at -0.7875 0) (size 0.875 0.95) '
    '(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))\n'
    '  (pad "2" smd roundrect (at 0.7875 0) (size 0.875 0.95) '
    '(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25))\n'
    ')\n')


def fixture(d, bom_rows):
    """A board + a BOM CSV limited to the rows the test cares about."""
    board = d / "cook_loadcell.kicad_pcb"
    must_pass(run([KPY, GEN, LC / "03_src" / "floorplan.yaml", "-o", board], cwd=LC),
              "generate twin fixture board")
    bom = d / "bom_jlc.csv"
    lines = ["Comment,Designator,Footprint,MPN,LCSC"] + bom_rows
    bom.write_text("\n".join(lines) + "\n")
    return board, bom


def twin(d, board, bom, e2k, extra=()):
    out = d / "twin"
    return run([KPY, TWIN, board, bom, out, "--no-render", *extra],
               cwd=d, env={"EASYEDA2KICAD": str(e2k),
                           "JLC_TWIN_FETCH_ATTEMPTS": "1"})


# ------------------------------------------------------------- known-bad
@test("REGRESSION: an unrecognised fetch failure is FETCH-FAILED and BLOCKS",
      kind="known_bad")
def t_fetch_failed_blocks():
    """An HTTP 403 matches neither TRANSIENT_PAT nor any 'no CAD' wording.
    Before the fix this became NO-CAD and the run exited 0."""
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = stub_e2k(d, stderr="HTTP Error 403: Forbidden\n", rc=1)
    r = twin(d, board, bom, e2k)
    must_fail(r, "jlc_twin on an HTTP 403 fetch failure", "FETCH-FAILED")
    contains(r.out, "CRITICAL", "twin verdict")
    rpt = (d / "twin" / "twin_report.csv")
    check(rpt.exists(), "no twin_report.csv written")
    contains(rpt.read_text(), "FETCH-FAILED", "twin_report.csv")


@test("REGRESSION: a fetcher crash (traceback) BLOCKS, it is not NO-CAD",
      kind="known_bad")
def t_fetch_crash_blocks():
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = stub_e2k(d, stderr="Traceback (most recent call last):\n"
                             "KeyError: 'result'\n", rc=1)
    r = twin(d, board, bom, e2k)
    must_fail(r, "jlc_twin on a fetcher crash", "FETCH-FAILED")


@test("a genuine timeout is still classified FETCH-FAILED and BLOCKS",
      kind="known_bad")
def t_timeout_blocks():
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = stub_e2k(d, stderr="Connection timed out after 30s\n", rc=1)
    r = twin(d, board, bom, e2k)
    must_fail(r, "jlc_twin on a timeout", "FETCH-FAILED")


@test("a nonzero-exit fetcher is never NO-CAD even if it says 'not found'",
      kind="known_bad")
def t_nocad_requires_clean_exit():
    """NO-CAD is a disposition, so it needs BOTH the affirmative wording and
    a clean exit. A crash that happens to print 'not found' must block."""
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = stub_e2k(d, stderr="config file not found\n", rc=2)
    r = twin(d, board, bom, e2k)
    must_fail(r, "jlc_twin on a nonzero exit that mentions 'not found'",
              "FETCH-FAILED")


# ---------------------------------------------------------- disposition
@test("an affirmative, clean-exit 'no CAD data' is NO-CAD and does not block")
def t_nocad_disposition():
    """The fail-closed change must not make every part block — a part the
    library genuinely lacks is still a reportable disposition, not a defect."""
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = stub_e2k(d, stdout="No CAD data available for this component\n", rc=0)
    r = twin(d, board, bom, e2k)
    check(r.rc == 0,
          f"an affirmative NO-CAD should not block the run:\n{r.out[-2000:]}")
    contains(r.out, "NO-CAD", "twin output")


# ------------------------------------------------------------ record/replay
@test("the per-code cache dir replays without touching the fetcher")
def t_cache_replay():
    """Seed OUTDIR/easyeda/<CODE>/jlc.pretty and point $EASYEDA2KICAD at a
    stub that would BLOCK if called. A clean run proves replay works and
    that the fast tier never needs the network."""
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    cache = d / "twin" / "easyeda" / CODE / "jlc.pretty"
    cache.mkdir(parents=True)
    (cache / "R_0603.kicad_mod").write_text(MINIMAL_MOD)
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay is broken\n", rc=1)
    r = twin(d, board, bom, e2k)
    check("NETWORK WAS CALLED" not in r.out,
          f"cache miss: the fetcher was invoked despite a seeded cache\n"
          f"{r.out[-1500:]}")
    contains(r.out, "R7", "twin output should mention the checked ref")


@test("a BOM with no LCSC codes reports 0 checked rather than a silent pass")
def t_empty_bom():
    """`0 OK / 0 checked` exiting 0 is correct but must be VISIBLE — an
    empty BOM silently 'passing' is how unverified parts ship."""
    d = tmpdir("twin_")
    board, bom = fixture(d, ["100R shield bond,R7,R_0603_1608Metric,,"])
    e2k = stub_e2k(d, stderr="should not be called\n", rc=1)
    r = twin(d, board, bom, e2k)
    check("0 checked" in r.out or "0 OK" in r.out,
          f"an empty BOM did not announce that it checked nothing:\n"
          f"{r.out[-1500:]}")


if __name__ == "__main__":
    sys.exit(main())
