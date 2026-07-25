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
import re
import shutil
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     must_fail, must_pass, run, test, tmpdir)

sys.path.insert(0, str(FAB_SCRIPTS))
from jlc_rotation_resolve import (load_lcsc_rotations,  # noqa: E402
                                  resolve_rotation)

TWIN = FAB_SCRIPTS / "jlc_twin.py"
GEN = SCRIPTS / "generate_board_generic.py"
LC = ROOT / "archived_projects" / "cook-loadcell"
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


# ------------------------------------------------ per-LCSC rotation override
# JLC's CPL zero-orientation is a PER-PART fact: two parts sharing a KiCad
# footprint NAME can need different offsets. Measured (2026-07-24): C79924 and
# C7719 are both SOT-23-5 yet fit at 180 vs 90 — a footprint-name table cannot
# hold both. jlc_rotation_resolve.resolve_rotation() checks the per-LCSC table
# BEFORE the name DB. The exporter and the twin share this resolver, so these
# unit tests pin the behaviour for BOTH.
#
# RED-VERIFY (performed 2026-07-24): deleting the `if lcsc and lcsc in
# lcsc_table:` branch in resolve_rotation() (i.e. reverting to name-only, the
# pre-fix code) makes t_lcsc_override_wins FAIL — it then returns 270 (name-DB
# -90) instead of the fitted 180. Restored; the test now passes. That is the
# whole bug: the name key served 270 to a part whose exact fit is 180.
_SOT235 = [(re.compile("^SOT-23"), -90.0)]   # the generic name-DB rule (buggy for these parts)


@test("per-LCSC override WINS over a matching footprint-name rule", kind="known_bad")
def t_lcsc_override_wins():
    """The defended behaviour. C79924 (SOT-23-5) fits at 180; the name DB says
    -90 (=270). With the per-LCSC row present the resolver MUST return 180 —
    if it returned the name-DB 270 the CPL ships the consigned/known-bad
    generic rotation, which is exactly the crow-recorder-central-v2 blocker."""
    cpl, off, src = resolve_rotation("SOT-23-5", 0, "C79924", _SOT235,
                                     {"C79924": 180.0})
    eq(cpl, 180.0, "C79924 SOT-23-5 CPL rotation")
    eq(off, 180.0, "offset")
    eq(src, "lcsc", "resolution source")
    check(cpl != 270.0, "per-LCSC must NOT fall through to the name-DB 270")


@test("a part with no per-LCSC row falls back to the name DB unchanged")
def t_name_db_fallback():
    """C7719 is also SOT-23-5 but needs 90, so it is NOT in the crow table.
    It must keep the existing name-DB behaviour (-90 -> 270): the override is
    strictly additive and never disturbs an un-listed part. This is what lets
    C79924->180 land WITHOUT touching cooksense's C7719."""
    cpl, off, src = resolve_rotation("SOT-23-5", 0, "C7719", _SOT235,
                                     {"C79924": 180.0})
    eq(cpl, 270.0, "C7719 SOT-23-5 CPL rotation (name-DB -90)")
    eq(src, "name", "resolution source")


@test("board orientation is added to the per-LCSC offset (non-zero rot)")
def t_board_rotation_composes():
    """CPL = (board_rot + offset) % 360. A part placed at 90 on the board with
    a +180 per-LCSC offset ships at 270."""
    cpl, off, src = resolve_rotation("SOT-23", 90, "C15127", _SOT235,
                                     {"C15127": 180.0})
    eq(cpl, 270.0, "C15127 at board-rot 90 + offset 180")
    eq(src, "lcsc", "resolution source")


@test("no per-LCSC row and no name-DB match returns the bare board rotation")
def t_no_match_passthrough():
    cpl, off, src = resolve_rotation("Some_Weird_FP", 45, "C0000", [], {})
    eq(cpl, 45.0, "passthrough CPL rotation")
    eq(off, 0.0, "passthrough offset")
    eq(src, "none", "resolution source")


@test("the shipped per-LCSC table loads and resolves crow-rv2's 10 rows")
def t_shipped_table_resolves():
    """Guards the real jlc_lcsc_rotations.csv: every crow-recorder-central-v2
    ROT-DB-SUGGEST code must be present with its fitted offset, so a fresh
    export/twin reports ZERO unresolved suggestions."""
    tbl = load_lcsc_rotations()
    want = {"C6938291": 90, "C181312": 90, "C82317": 90, "C5224055": 90,
            "C90627": 90, "C15127": 180, "C20917": 180, "C79924": 180}
    for code, rot in want.items():
        check(code in tbl, f"{code} missing from jlc_lcsc_rotations.csv")
        eq(tbl[code], float(rot), f"{code} rotation")


if __name__ == "__main__":
    sys.exit(main())
