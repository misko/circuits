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
import math
import os
import re
import shutil
import stat
import sys
from pathlib import Path

import pcbnew

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, SCRIPTS, check, contains, eq, main,  # noqa: E402
                     not_contains,
                     must_fail, must_pass, run, test, tmpdir)

sys.path.insert(0, str(FAB_SCRIPTS))
from jlc_rotation_resolve import (load_lcsc_rotations,  # noqa: E402
                                  resolve_rotation)
from jlc_twin import (best_fit, centered, pads_of,  # noqa: E402
                      portable_twin_model_path,
                      rebase_cached_model_paths,
                      select_render_model_path)

TWIN = FAB_SCRIPTS / "jlc_twin.py"
E2K_COMPAT = FAB_SCRIPTS / "easyeda2kicad_compat.py"
GEN = SCRIPTS / "generate_board_generic.py"
LC = ROOT / "archived_projects" / "cook-loadcell"
CODE = "C22775"          # a real code on cook-loadcell's BOM (R7, 100R 0603)


@test("cached model paths survive an atomic staging-directory promotion")
def t_cached_model_path_rebase_and_portability():
    """A copied cache must not retain the vanished producer's absolute path."""
    d = tmpdir("jlc_cache_promote_")
    code_dir = d / "twin" / "easyeda" / CODE
    pretty = code_dir / "jlc.pretty"
    models = code_dir / "jlc.3dshapes"
    pretty.mkdir(parents=True)
    models.mkdir(parents=True)
    fp_path = pretty / "fixture.kicad_mod"
    fp_path.write_text("fixture")
    current = models / "fixture.wrl"
    current.write_text("#VRML V2.0 utf8\n")

    fp = pcbnew.FOOTPRINT(None)
    old = pcbnew.FP_3DMODEL()
    old.m_Filename = str(d / "vanished_next.XYZ" / "twin" / "easyeda" /
                         CODE / "jlc.3dshapes" / "fixture.wrl")
    old.m_Offset.x = 1.25
    old.m_Rotation.z = 270
    fp.Models().push_back(old)

    rebase_cached_model_paths(fp, fp_path)
    rebound = list(fp.Models())[0]
    eq(Path(rebound.m_Filename), current.resolve(), "rebased cache model")
    eq(rebound.m_Offset.x, 1.25, "model offset preserved")
    eq(rebound.m_Rotation.z, 270, "model rotation preserved")
    eq(portable_twin_model_path(rebound.m_Filename, d / "twin"),
       "${KIPRJMOD}/easyeda/C22775/jlc.3dshapes/fixture.wrl",
       "portable twin path")


@test("an evidenced sibling STEP is selected explicitly and cannot silently "
      "fall back")
def t_render_model_representation_selection():
    d = tmpdir("jlc_model_representation_")
    wrl = d / "part.wrl"
    step = d / "part.step"
    wrl.write_text("#VRML V2.0 utf8\n")
    step.write_text("ISO-10303-21;\n")
    eq(select_render_model_path(wrl), wrl.resolve(),
       "default representation remains unchanged")
    eq(select_render_model_path(wrl, "step"), step.resolve(),
       "explicit sibling STEP selected")
    missing = d / "missing.wrl"
    try:
        select_render_model_path(missing, "step")
    except ValueError as exc:
        contains(str(exc), "does not exist", "missing sibling fails closed")
    else:
        check(False, "missing requested sibling silently fell back")


@test("bottom-side land comparison removes KiCad's placement mirror")
def t_bottom_side_fit_uses_unflipped_library_frame():
    """A correct asymmetric B.Cu package must compare non-mirrored to the
    identical supplier land.  The placement mirror is physical board state,
    not a mirrored pin-numbering defect in either source library."""
    b = pcbnew.NewBoard("")
    fp = pcbnew.FOOTPRINT(b)
    fp.SetPosition(pcbnew.VECTOR2I(int(30e6), int(25e6)))
    pts = {"1": (-2.0, -1.0), "2": (2.0, -1.0), "3": (2.0, 1.6)}
    for number, (x, y) in pts.items():
        p = pcbnew.PAD(fp)
        p.SetNumber(number)
        p.SetShape(pcbnew.PAD_SHAPE_RECT)
        p.SetSize(pcbnew.VECTOR2I(int(0.8e6), int(0.8e6)))
        p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        p.SetLayerSet(p.SMDMask())
        p.SetPosition(pcbnew.VECTOR2I(int((30 + x) * 1e6),
                                     int((25 + y) * 1e6)))
        fp.Add(p)
    b.Add(fp)
    fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(90)
    ours = centered(pads_of(fp, footprint_local=True))
    supplier = centered({k: [v] for k, v in pts.items()})
    fit = best_fit(ours, supplier)[0]
    check(fit[0] < 0.001, f"expected sub-micron fit, got {fit}")
    check(fit[1] is False, f"correct B.Cu land was called MIRRORED: {fit}")
    eq(fit[2], 0, "correct B.Cu library-frame rotation")


@test("easyeda2kicad compatibility shim overrides only the HTTP User-Agent")
def t_easyeda_compat_user_agent():
    """The shim must remain independent of the installed network package.
    A tiny fake upstream module proves delegation and the configurable UA
    override without making a live HTTP request."""
    d = tmpdir("e2k_compat_")
    pkg = d / "easyeda2kicad"
    api = pkg / "easyeda"
    api.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (api / "__init__.py").write_text("")
    (api / "easyeda_api.py").write_text(
        "class EasyedaApi:\n"
        "    def __init__(self, use_cache=False):\n"
        "        self.headers = {'User-Agent': 'stale-upstream'}\n")
    (pkg / "__main__.py").write_text(
        "from .easyeda.easyeda_api import EasyedaApi\n"
        "def main():\n"
        "    print(EasyedaApi().headers['User-Agent'])\n"
        "    return 0\n")
    sentinel = "fixture-browser/999"
    r = must_pass(run([KPY, E2K_COMPAT], cwd=d,
                      env={"PYTHONPATH": str(d),
                           "JLC_TWIN_USER_AGENT": sentinel}),
                  "easyeda2kicad compatibility shim")
    contains(r.out, sentinel, "compatibility User-Agent")
    not_contains(r.out, "stale-upstream", "compatibility User-Agent")


@test("jlc_twin wraps the real easyeda2kicad entry point but not test stubs")
def t_easyeda_compat_command_selection():
    d = tmpdir("e2k_command_")
    real = d / "easyeda2kicad"
    real.write_text(f"#!{KPY}\n")
    real.chmod(real.stat().st_mode | stat.S_IEXEC)
    stub = d / "easyeda2kicad_stub"
    stub.write_text(f"#!{KPY}\n")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    code = (
        "import json,sys\n"
        f"sys.path.insert(0,{str(FAB_SCRIPTS)!r})\n"
        "from jlc_twin import easyeda2kicad_command\n"
        "print('@@'+json.dumps(easyeda2kicad_command(sys.argv[1])))\n")
    wrapped = must_pass(run([KPY, "-c", code, real]), "real fetcher command")
    contains(wrapped.out, str(E2K_COMPAT), "real fetcher wrapper")
    direct = must_pass(run([KPY, "-c", code, stub]), "stub fetcher command")
    contains(direct.out, f'"{stub}"', "stub direct command")
    not_contains(direct.out, str(E2K_COMPAT), "stub direct command")


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


@test("JLC twin canonicalizes EasyEDA pad labels 01..09 to KiCad 1..9",
      kind="known_bad")
def t_leading_zero_pad_labels_are_same_identity():
    """Samtec J7's JLC CAD uses 01..09 while the board uses 1..9. Before the
    fix only pad 10 intersected, so the twin accepted a vacuous one-point fit
    at offset 0 against the independently measured 270-degree rotation row."""
    code = ("import sys\n"
            f"sys.path.insert(0, {str(FAB_SCRIPTS)!r})\n"
            "from jlc_twin import canonical_pad_number\n"
            "print(','.join(canonical_pad_number(x) "
            "for x in ('01','08','10','A1')))\n")
    r = must_pass(run([KPY, "-c", code]), "pad-number canonicalization")
    contains(r.out, "1,8,10,A1", "formatting zeros are not pin identity")


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


@test("an evidence-bound FETCH-FAILED adjudication is persisted in the CSV "
      "and is not reported as a transient retry")
def t_fetch_failed_adjudication_is_final_evidence():
    """The pre-fix tool applied adjudications only after writing the CSV, then
    printed an unconditional TRANSIENT footer from the raw fetch set. It exited
    zero while its shipped report still said FETCH-FAILED and its prose said
    the run was not verification. Final evidence must describe one state.
    """
    d = tmpdir("twin_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = stub_e2k(d, stderr="HTTP Error 403: Forbidden\n", rc=1)
    adj = d / "adjudications.yaml"
    adj.write_text(
        f"- lcsc: {CODE}\n"
        "  refs: [R7]\n"
        "  status: FETCH-FAILED\n"
        "  why: same-run controls succeeded and exact unpolarized land was verified\n")
    r = twin(d, board, bom, e2k, extra=("--adjudications", str(adj)))
    must_pass(r, "jlc_twin with an explicit library-absence adjudication")
    rpt = d / "twin" / "twin_report.csv"
    contains(rpt.read_text(), "ADJUDICATED-FETCH-FAILED",
             "final machine report")
    contains(r.out, "ADJUDICATED LIBRARY ABSENCES", "final console verdict")
    check("does NOT constitute twin verification" not in r.out,
          "an adjudicated absence must not retain the unresolved footer")


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
    contains(r.out, "state=cached", "cache replay progress state")
    contains(r.out, "completed=1/1", "cache replay coverage heartbeat")


@test("a silent fetch child emits heartbeats, times out, and leaves a resume path")
def t_fetch_timeout_is_visible_and_bounded():
    d = tmpdir("twin_timeout_")
    board, bom = fixture(d, [f"100R shield bond,R7,R_0603_1608Metric,,{CODE}"])
    e2k = d / "easyeda2kicad_stub"
    e2k.write_text(
        "#!/usr/bin/env python3\n"
        "import time\n"
        "time.sleep(5)\n")
    e2k.chmod(e2k.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    out = d / "twin"
    r = run([KPY, TWIN, board, bom, out, "--no-render"], cwd=d, env={
        "EASYEDA2KICAD": str(e2k),
        "JLC_TWIN_FETCH_ATTEMPTS": "1",
        "JLC_TWIN_FETCH_TIMEOUT_S": "0.25",
        "JLC_TWIN_HEARTBEAT_S": "0.05",
        "JLC_TWIN_WALL_TIMEOUT_S": "2",
    })
    must_fail(r, "silent fetch child", "TIMED-OUT")
    contains(r.out, "state=running", "periodic fetch heartbeat")
    contains(r.out, "completed=0/1", "in-progress coverage")
    contains(r.out, "simply RE-RUNNING", "resumable timeout instruction")


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


@test("a part with no per-LCSC row is UNSOURCED — the name DB cannot decide",
      kind="known_bad")
def t_name_db_fallback():
    """AMENDED 2026-07-25 (canon A-ROT). This test used to assert the OPPOSITE:
    that an un-listed part "falls back to the name DB unchanged" (-90 -> 270).
    That fallback WAS the defect. It shipped 22 wrong CPL rotations on
    smc0985-cooksense alone, through four separate mechanisms — a partial
    prefix (`^SOT-23` swallowing SOT-23-6, ten safety-chain gates 90 out), an
    unevidenced rule (`^JST_GH_SM,180`, eight connectors 180 out), a wrong key
    (C79924 vs C7719, one name two answers) and no rule at all (silently 0.0).
    A footprint NAME is not a part, so the name DB is now ADVISORY: a part with
    no MEASURED per-LCSC row resolves `unsourced` and BLOCKS.
    Full coverage of all five mechanisms, with the red-verification, lives in
    tests/t1_rotation_authority.py."""
    cpl, off, src = resolve_rotation("SOT-23-5", 0, "C7719", _SOT235,
                                     {"C79924": 180.0})
    eq(src, "unsourced", "resolution source for an unmeasured part")
    check(cpl != 270.0, "the name-DB's 270 still reaches the CPL")


@test("board orientation is added to the per-LCSC offset (non-zero rot)")
def t_board_rotation_composes():
    """CPL = (board_rot + offset) % 360. A part placed at 90 on the board with
    a +180 per-LCSC offset ships at 270."""
    cpl, off, src = resolve_rotation("SOT-23", 90, "C15127", _SOT235,
                                     {"C15127": 180.0})
    eq(cpl, 270.0, "C15127 at board-rot 90 + offset 180")
    eq(src, "lcsc", "resolution source")


@test("no per-LCSC row and no name-DB match is UNSOURCED, not a silent 0.0",
      kind="known_bad")
def t_no_match_passthrough():
    """AMENDED 2026-07-25 (canon A-ROT). The old assertion — `src == "none"`,
    offset 0.0, non-blocking — is the quietest of the five mechanisms and the
    hardest to notice: C98732 (the XT60, on a VENDORED footprint name that the
    start-anchored `^AMASS_XT60PW-M` rule never matched) and C125121 (the
    cooksense SAFETY-ISOLATION opto) both matched nothing and shipped at 0."""
    cpl, off, src = resolve_rotation("Some_Weird_FP", 45, "C0000", [], {})
    eq(cpl, 45.0, "the bare board rotation is still what would be emitted")
    eq(off, 0.0, "no offset to apply")
    eq(src, "unsourced", "resolution source — silence must BLOCK, not default")


# ------------------------------------------ xform() handedness (2026-07-25)
# THE INCIDENT. `jlc_twin.xform()` — the function that computes `jlc_offset`,
# the number this pipeline calls "the MEASURED rotation" — used the OPPOSITE
# handedness to `local_to_board()`, which is the operator KiCad actually
# applies to a rotated footprint's pads. Every offset the twin ever reported
# was therefore NEGATED. 0 and 180 are sign-invariant, so the error was
# invisible on those; 90 and 270 negate into each other, so it was exactly
# 180 deg wrong there. Six rows of jlc_lcsc_rotations.csv had been populated
# FROM this function and were all 180 deg wrong (canon M1: the authority table
# WAS the checker's output). A correct sealed release, crow-recorder-central-v2
# v1.2, was "fixed" into a wrong one (v1.3) on that evidence.
#
# RED-VERIFIED (2026-07-25, both tests below, by editing the live file,
# running `--only=handedness`, and restoring). With the pre-fix line
#     out[k] = sorted((round(x*c - y*s, 3), round(x*s + y*c, 3)) ...)
# swapped back into xform():
#   t_xform_matches_pcbnew FAILS — "xform() rotates local (1,0) by 90 deg to
#     (0.0, 1.0); KiCad's own convention (y-down, CCW) puts it at (0,-1)"
#   t_fit_offset_handedness FAILS — "fitted offset for ours(+1.90,0) vs
#     JLC(0,+1.90): got 270, want 90"
# Restored, both pass (2 passed, 0 failed).
#
# MEASURED on this suite's own fixture (61 pads on footprints rotated to
# 0/90/180/270), reproducing the incident's signature independently of the
# board it was found on:
#   verified form  max error 4.2e-15 mm  (exact at every angle)
#   pre-fix form   max error 20.000 mm @90, 10.175 mm @270, 3.0e-15 mm @180
# The 180-deg tie is the whole reason this survived: the two forms are
# mathematically identical there.
_ROT_PROBE = r"""
import json, math, sys
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
out = []
for fp in b.GetFootprints():
    rot = fp.GetOrientationDegrees()
    if round(rot) % 360 == 0:
        continue                       # 0 deg proves nothing about handedness
    ox, oy = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
    for p in fp.Pads():
        r = p.GetFPRelativePosition()
        a = p.GetPosition()
        out.append({"rot": rot,
                    "local": [r.x / 1e6, r.y / 1e6],
                    "board": [a.x / 1e6 - ox, a.y / 1e6 - oy]})
print("@@" + json.dumps(out))
"""


@test("xform()'s rotation operator reproduces pcbnew's OWN pad placement "
      "exactly, and the pre-fix handedness provably does not")
def t_xform_matches_pcbnew():
    """Pins the OPERATOR itself against the only authority that cannot be
    wrong about KiCad geometry: KiCad. For every pad on every rotated
    footprint, `pad.GetFPRelativePosition()` pushed through the operator must
    equal `pad.GetPosition() - footprint.GetPosition()`.

    Two layers, deliberately: first establish which of the two candidate
    forms IS KiCad's (measured here at 4.2e-15 mm vs 20.0 mm over 61 pads,
    and the fixture is REQUIRED to be able to tell them apart), then push a
    known point through the LIVE `xform()` and require it to be that form.
    Without the second layer the test would grade an idea rather than the
    shipped code. This is what makes the class un-reintroducible: it does not
    ask whether a fit "looks right", it asks whether the transform IS KiCad's.

    RED-VERIFIED: swapping the pre-fix `(x*c - y*s, x*s + y*c)` back into
    xform() makes this test FAIL at the live probe — "xform() rotates local
    (1,0) by 90 deg to (0.0, 1.0); KiCad's own convention (y-down, CCW) puts
    it at (0,-1)"."""
    import json
    d = tmpdir("twin_")
    board = d / "cook_loadcell.kicad_pcb"
    must_pass(run([KPY, GEN, LC / "03_src" / "floorplan.yaml", "-o", board],
                  cwd=LC), "generate handedness fixture board")
    # rotate a spread of footprints so 90 / 180 / 270 are all sampled; 180 is
    # deliberately included because it is where the two forms AGREE — a
    # fixture that only sampled 180 would have passed the broken code.
    must_pass(run([KPY, "-c",
                   "import pcbnew,sys\n"
                   "b=pcbnew.LoadBoard(sys.argv[1])\n"
                   "for i,fp in enumerate(b.GetFootprints()):\n"
                   "    fp.SetOrientationDegrees([0,90,180,270][i%4])\n"
                   "b.Save(sys.argv[1])\n", str(board)]), "rotate fixture")
    got = json.loads(must_pass(run([KPY, "-c", _ROT_PROBE, str(board)]),
                               "pcbnew rotation probe").out.split("@@", 1)[1])
    check(len(got) >= 40, f"too few rotated pads to be evidence: {len(got)}")
    angles = {round(s["rot"]) % 360 for s in got}
    check({90, 180, 270} <= angles,
          f"fixture must sample 90/180/270, sampled {sorted(angles)}")

    def err(form):
        worst, at = 0.0, None
        for s in got:
            th = math.radians(s["rot"])
            c, sn = math.cos(th), math.sin(th)
            x, y = s["local"]
            gx, gy = form(x, y, c, sn)
            e = math.hypot(gx - s["board"][0], gy - s["board"][1])
            if e > worst:
                worst, at = e, s["rot"]
        return worst, at

    fixed = err(lambda x, y, c, s: (x * c + y * s, -x * s + y * c))
    prefix = err(lambda x, y, c, s: (x * c - y * s, x * s + y * c))
    check(fixed[0] < 1e-6,
          f"the operator in xform() does NOT reproduce pcbnew's pad "
          f"placement: max error {fixed[0]:.6f} mm at {fixed[1]} deg over "
          f"{len(got)} pads")
    check(prefix[0] > 1.0,
          f"the PRE-FIX handedness also reproduces pcbnew (max error "
          f"{prefix[0]:.6f} mm) — this fixture cannot tell the two forms "
          f"apart, so it proves nothing; rotate parts off 0/180")
    # and the live function must BE the verified form, not merely agree in
    # spirit: push a known point through the real xform().
    probe = ("import sys,json\n"
             f"sys.path.insert(0, {str(FAB_SCRIPTS)!r})\n"
             "import jlc_twin\n"
             "print('@@'+json.dumps(jlc_twin.xform({'1':[(1.0,0.0)]},90,False)))\n")
    live = json.loads(must_pass(run([KPY, "-c", probe]),
                                "live xform probe").out.split("@@", 1)[1])
    x, y = live["1"][0]
    check(abs(x - 0.0) < 1e-6 and abs(y - (-1.0)) < 1e-6,
          f"xform() rotates local (1,0) by 90 deg to {(x, y)}; KiCad's own "
          f"convention (y-down, CCW) puts it at (0,-1) — the shipped function "
          f"is not the pcbnew-verified operator")


@test("the fitted jlc_offset has the CORRECT handedness: a 90-deg pad-vector "
      "difference fits at 90, not at the negated 270", kind="known_bad")
def t_fit_offset_handedness():
    """The synthetic land-pattern fixture the incident calls for. Two 3-pad
    footprints whose pad1->pad3 vectors differ by a quarter turn:

        ours (+1.90, 0)  vs  JLC (0, +1.90)  ->  offset  90
        ours (0, +1.90)  vs  JLC (+1.90, 0)  ->  offset 270

    Derived, not guessed: `best_fit` returns the `ang` with
    `ours == xform(jlc, ang)`, and in KiCad's y-down CCW frame rotating
    (0,+1.90) (south) by +90 gives (+1.90,0) (east). BOTH rows flip under the
    pre-fix handedness — that is the RED-verification: swapping
    `(x*c - y*s, x*s + y*c)` back in returns 270 for the first row and 90 for
    the second, i.e. every 90/270 part 180 deg off. (NB the incident brief
    quoted the first row's answer as 270; that is the PRE-FIX value. The
    post-fix answer is 90, and the second row is the framing that yields 270 —
    both are pinned here so the direction cannot be misremembered again.)"""
    import json
    probe = ("import sys,json\n"
             f"sys.path.insert(0, {str(FAB_SCRIPTS)!r})\n"
             "import jlc_twin\n"
             "ew = {'1':[(-0.95,0.0)],'2':[(0.0,0.6)],'3':[(0.95,0.0)]}\n"
             "ns = {'1':[(0.0,-0.95)],'2':[(-0.6,0.0)],'3':[(0.0,0.95)]}\n"
             "print('@@'+json.dumps([jlc_twin.best_fit(ew, ns)[0],\n"
             "                       jlc_twin.best_fit(ns, ew)[0]]))\n")
    (a_err, a_mir, a_ang), (b_err, b_mir, b_ang) = json.loads(
        must_pass(run([KPY, "-c", probe]), "best_fit probe")
        .out.split("@@", 1)[1])
    check(a_err < 1e-6 and not a_mir,
          f"east-vs-south should fit exactly and unmirrored, got "
          f"err={a_err} mir={a_mir}")
    eq(a_ang, 90, "fitted offset for ours(+1.90,0) vs JLC(0,+1.90)")
    check(b_err < 1e-6 and not b_mir,
          f"south-vs-east should fit exactly and unmirrored, got "
          f"err={b_err} mir={b_mir}")
    eq(b_ang, 270, "fitted offset for ours(0,+1.90) vs JLC(+1.90,0)")
    check(a_ang != 270 and b_ang != 90,
          "the fitted offsets are NEGATED — this is the pre-fix xform() "
          "handedness, and every 90/270 part will ship 180 deg off")


# ------------------------------------------------ --assembly (canon A-POP)
@test("--assembly pulls coded not-assembled/consigned refs from the ONE "
      "declared home, so an unplaced part is still land-pattern checked")
def t_assembly_pairs():
    """`--also REF=LCSC` was hand-typed, which made it a SECOND home for the
    population set — cooksense v1.1's MANIFEST and CPL drifted apart on 12
    refs for exactly that reason. The pairs now come from
    03_src/rules/assembly.yaml. R7 is NOT on this fixture's BOM, so a checked
    R7 can only have come from the assembly file."""
    d = tmpdir("twin_")
    board, bom = fixture(d, ["100R shield bond,R7,R_0603_1608Metric,,"])
    asm = d / "assembly.yaml"
    asm.write_text(
        "service: standard\nsides: [top]\nfiducials: none\n"
        "build_quantity: 5\nnot_assembled:\n"
        "  - refs: [R7]\n"
        f"    reason: user_supplied\n    lcsc: {CODE}\n"
        "    evidence: \"fixture entry, dated 2026-07-25\"\n"
        "    disposition: \"n/a\"\n")
    cache = d / "twin" / "easyeda" / CODE / "jlc.pretty"
    cache.mkdir(parents=True)
    (cache / "R_0603.kicad_mod").write_text(MINIMAL_MOD)
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay is broken\n", rc=1)
    r = twin(d, board, bom, e2k, extra=("--assembly", str(asm)))
    contains(r.out, "1 coded not-assembled/consigned ref(s)",
             "the assembly file was read")
    contains(r.out, "R7", "the not-assembled part was actually checked")
    # and --also still works for an ad-hoc probe (back-compat)
    r2 = twin(d, board, bom, e2k, extra=("--also", f"R7={CODE}"))
    contains(r2.out, "R7", "--also still mounts an ad-hoc pair")


@test("the shipped per-LCSC table loads and resolves crow-rv2's 10 rows")
def t_shipped_table_resolves():
    """Guards the real jlc_lcsc_rotations.csv: every crow-recorder-central-v2
    ROT-DB-SUGGEST code must be present with its offset, so a fresh
    export/twin reports ZERO unresolved suggestions.

    VALUES CORRECTED 2026-07-25. The five 90s below were 90 until the
    `jlc_twin.xform()` handedness bug was found: xform and `local_to_board`
    use OPPOSITE handedness, and measured against pcbnew itself over 72 pads
    local_to_board's form is exact (0.000000 mm) while xform's is off by up to
    23.93 mm — wrong at every 90/270 part, sign-invariant and therefore
    invisible at 0/180. Every offset the twin reported was NEGATED, and these
    rows had been populated FROM it (canon M1: the authority table WAS the
    checker's output). Re-fitted against each part's own cached JLC model with
    the proven operator, all five are 270; the 180s are unaffected because 180
    is sign-invariant. This test now pins the CORRECTED values, so reverting
    the table re-fails it."""
    tbl = load_lcsc_rotations()
    want = {"C6938291": 270, "C181312": 270, "C82317": 270, "C5224055": 270,
            "C90627": 270, "C7719": 270,
            "C15127": 180, "C20917": 180, "C79924": 180}
    for code, rot in want.items():
        check(code in tbl, f"{code} missing from jlc_lcsc_rotations.csv")
        eq(tbl[code], float(rot), f"{code} rotation")


# ================================================================ MOUNT
# THE SECOND HALF OF THE HANDEDNESS INCIDENT (2026-07-25). Fixing `xform()`
# left FOUR more hand-inlined copies of the wrong rotation form — the render
# mount's OFFSET, its Z-ROTATION, and the model-frame rotation in BOTH
# `reg_check()` and `model_self_check()`. Because MODEL-REG used the same
# wrong form as the mount it graded the mount with the mount's OWN method
# (canon M1), so a TRUE 14.37 mm mis-mount on a shipped XT60 was waived as a
# false alarm and usb-hub-3s-v3 v1.5 sealed with every 90/270 part rendering
# 180 deg out.
#
# The single-function tests that existed here could not have caught that:
# they graded ONE site. What follows is an INVARIANT test — it mounts a
# deliberately asymmetric model through the WHOLE pipeline at each of
# 0/90/180/270 and asserts the mounted pose is JLC's pose turned by exactly
# the fitted angle. It goes RED if `xform`, `reg_check`, the mount offset or
# the mount z drifts at ANY site, because all four are on the path it walks.
#
# EVERY rotation fixture here includes 90 AND 270 and asserts it can tell the
# two candidate forms apart. A fixture that only sampled 0/180 would have
# passed all five copies of the bug: the two forms are mathematically
# IDENTICAL there, which is exactly why five copies survived review.

BAR = (0.0, -1.0, 8.0, 1.0)      # model-frame bbox: long +x, short +/-y


def bar_wrl(path):
    """An ASYMMETRIC body: 8 mm along +x from the origin, 2 mm across.
    KiCad VRML convention, 1 unit = 2.54 mm. Asymmetry is the whole point —
    a symmetric body's bbox is invariant under the very rotations under test.
    """
    u = 2.54
    pts = [(x / u, y / u, z / u)
           for z in (0.0, 2.0)
           for (x, y) in ((BAR[0], BAR[1]), (BAR[2], BAR[1]),
                          (BAR[2], BAR[3]), (BAR[0], BAR[3]))]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    path.write_text(
        "#VRML V2.0 utf8\nShape {\n"
        " appearance Appearance { material Material "
        "{ diffuseColor 0.9 0.1 0.1 } }\n"
        " geometry IndexedFaceSet {\n  coord Coordinate { point [\n"
        + ",\n".join("   %.6f %.6f %.6f" % p for p in pts)
        + "\n  ] }\n  coordIndex [\n"
        + ",\n".join("   " + ", ".join(str(i) for i in f) + ", -1"
                     for f in faces)
        + "\n  ]\n }\n}\n")


def render_pose(bbox, off, rot_z, scale=(1.0, 1.0)):
    """The plan-view corners a renderer draws for one FP_3DMODEL, in the
    footprint's y-DOWN frame. The test's OWN implementation on purpose — if it
    imported jlc_twin's, a sign flip there would cancel on both sides of the
    invariant and the test would grade nothing. Its own sign is pinned
    separately, against the RENDERER, by t_model_rot_matches_render."""
    th = math.radians(rot_z)
    c, s = math.cos(th), math.sin(th)
    out = []
    for mx in (bbox[0], bbox[2]):
        for my in (bbox[1], bbox[3]):
            rx, ry = mx * c + my * s, -mx * s + my * c
            out.append((rx * scale[0] + off[0], -(ry * scale[1] + off[1])))
    return out


def bbox_of(pts):
    return (min(p[0] for p in pts), min(p[1] for p in pts),
            max(p[0] for p in pts), max(p[1] for p in pts))


def form_a(pts, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(x * c + y * s, -x * s + y * c) for x, y in pts]


def form_b(pts, ang):
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(x * c - y * s, x * s + y * c) for x, y in pts]


# A scalene, non-mirror-symmetric pad triangle: no rotation OR mirror of it
# coincides with another, so the fit angle is unique and a MIRRORED verdict
# is impossible by construction.
JPADS = {"1": (-2.0, -1.0), "2": (2.0, -1.0), "3": (2.0, 1.6)}
JMODEL_ROT_Z = 90.0          # non-zero on purpose: exercises model_rot too
JMODEL_OFF = (1.5, 0.75)     # non-zero on purpose: offset and rotation
#                              compose, and a sign error in either alone is
#                              invisible when the other is zero


def jlc_mod(d, code, model_path, pads=None, rot_z=JMODEL_ROT_Z,
            off=JMODEL_OFF, extra_pads=(), out="twin"):
    """Seed the per-code replay cache with a synthetic 'JLC' footprint."""
    pads = pads or JPADS
    cache = d / out / "easyeda" / code / "jlc.pretty"
    cache.mkdir(parents=True, exist_ok=True)
    rows = [(n, xy) for n, xy in pads.items()] + list(extra_pads)
    padtxt = "\n".join(
        '  (pad "%s" smd rect (at %s %s) (size 0.8 0.8) '
        '(layers "F.Cu" "F.Paste" "F.Mask"))' % (n, xy[0], xy[1])
        for n, xy in rows)
    (cache / "synth.kicad_mod").write_text(
        '(footprint "SYNTH" (version 20240108) (generator "test")\n'
        '  (layer "F.Cu")\n' + padtxt + "\n"
        '  (model "%s"\n' % model_path
        + '    (offset (xyz %s %s 0))\n' % (off[0], off[1])
        + '    (scale (xyz 1 1 1))\n'
        + '    (rotate (xyz 0 0 %s))\n' % rot_z
        + '  )\n)\n')
    return cache / "synth.kicad_mod"


_MKBOARD = (
    "import json, sys\n"
    "import pcbnew\n"
    "out, ang = sys.argv[1], float(sys.argv[2])\n"
    "pads = json.loads(sys.argv[3]); ct = json.loads(sys.argv[4])\n"
    "b = pcbnew.NewBoard(out)\n"
    "for (x1, y1), (x2, y2) in (((0,0),(60,0)), ((60,0),(60,60)),\n"
    "                           ((60,60),(0,60)), ((0,60),(0,0))):\n"
    "    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)\n"
    "    s.SetStart(pcbnew.VECTOR2I(int(x1*1e6), int(y1*1e6)))\n"
    "    s.SetEnd(pcbnew.VECTOR2I(int(x2*1e6), int(y2*1e6)))\n"
    "    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(100000); b.Add(s)\n"
    "def mkpad(owner, n, x, y):\n"
    "    p = pcbnew.PAD(owner); p.SetNumber(n)\n"
    "    p.SetShape(pcbnew.PAD_SHAPE_RECT)\n"
    "    p.SetSize(pcbnew.VECTOR2I(int(0.8e6), int(0.8e6)))\n"
    "    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)\n"
    "    p.SetLayerSet(p.SMDMask())\n"
    "    p.SetPosition(pcbnew.VECTOR2I(int(x*1e6), int(y*1e6)))\n"
    "    owner.Add(p)\n"
    "# STEP 1: let PCBNEW rotate the pad set.  The fixture's rotation must\n"
    "# not come from this repo's own operator, or the test would grade\n"
    "# self-consistency instead of KiCad's actual geometry.\n"
    "scratch = pcbnew.FOOTPRINT(b)\n"
    "scratch.SetPosition(pcbnew.VECTOR2I(0, 0))\n"
    "for n, xy in pads.items():\n"
    "    mkpad(scratch, n, xy[0], xy[1])\n"
    "scratch.SetOrientationDegrees(ang)\n"
    "rot = {}\n"
    "for p in scratch.Pads():\n"
    "    rot.setdefault(p.GetNumber(), []).append(\n"
    "        (p.GetPosition().x/1e6, p.GetPosition().y/1e6))\n"
    "# STEP 2: bake those as the LOCAL pads of a footprint placed at 0 deg.\n"
    "POS = (30.0, 25.0)\n"
    "fp = pcbnew.FOOTPRINT(b)\n"
    "fp.SetReference('U9')\n"
    "fp.SetPosition(pcbnew.VECTOR2I(int(POS[0]*1e6), int(POS[1]*1e6)))\n"
    "for n, pts in rot.items():\n"
    "    for (x, y) in pts:\n"
    "        mkpad(fp, n, POS[0]+x, POS[1]+y)\n"
    "if ct:\n"
    "    r = pcbnew.PCB_SHAPE(fp); r.SetShape(pcbnew.SHAPE_T_RECT)\n"
    "    r.SetStart(pcbnew.VECTOR2I(int((POS[0]+ct[0])*1e6),\n"
    "                               int((POS[1]+ct[1])*1e6)))\n"
    "    r.SetEnd(pcbnew.VECTOR2I(int((POS[0]+ct[2])*1e6),\n"
    "                             int((POS[1]+ct[3])*1e6)))\n"
    "    r.SetLayer(pcbnew.F_CrtYd); r.SetWidth(50000); fp.Add(r)\n"
    "b.Add(fp)\n"
    "b.Save(out)\n"
    "flat = {n: pts[0] for n, pts in rot.items()}\n"
    "print('@@' + json.dumps({'rotated': flat, 'pos': POS}))\n")


def synth_board(d, ang, pads=None, courtyard=None, name="synth.kicad_pcb"):
    import json
    pads = pads or JPADS
    board = d / name
    r = must_pass(run([KPY, "-c", _MKBOARD, str(board), str(ang),
                       json.dumps(pads), json.dumps(courtyard or [])]),
                  "build synthetic board at %s deg" % ang)
    return board, json.loads(r.out.split("@@", 1)[1])


def expected_local(ang, rotated, jm_off=JMODEL_OFF, jm_rot=JMODEL_ROT_Z,
                   pads=None):
    """The mounted body's plan bbox in OUR footprint-local frame, derived from
    the INVARIANT alone: our footprint is JLC's turned by `ang`, so the body
    must be JLC's body turned by `ang` about the pad centroid. Returns
    (formA_expectation, formB_expectation) so a fixture can prove it
    discriminates the two."""
    pads = pads or JPADS
    jc = (sum(p[0] for p in pads.values()) / len(pads),
          sum(p[1] for p in pads.values()) / len(pads))
    oc = (sum(p[0] for p in rotated.values()) / len(rotated),
          sum(p[1] for p in rotated.values()) / len(rotated))
    rel = [(x - jc[0], y - jc[1])
           for x, y in render_pose(BAR, jm_off, jm_rot)]
    return (bbox_of([(x + oc[0], y + oc[1]) for x, y in form_a(rel, ang)]),
            bbox_of([(x + oc[0], y + oc[1]) for x, y in form_b(rel, ang)]))


_READ_MOUNT = (
    "import json, sys\n"
    "import pcbnew\n"
    "b = pcbnew.LoadBoard(sys.argv[1])\n"
    "fp = b.FindFootprintByReference(sys.argv[2])\n"
    "print('@@' + json.dumps([{'f': m.m_Filename, 'rz': m.m_Rotation.z,\n"
    "                          'ox': m.m_Offset.x, 'oy': m.m_Offset.y,\n"
    "                          'sx': m.m_Scale.x, 'sy': m.m_Scale.y}\n"
    "                         for m in fp.Models()]))\n")


def read_mount(board, ref="U9"):
    import json
    return json.loads(
        must_pass(run([KPY, "-c", _READ_MOUNT, str(board), ref]),
                  "read mounted model").out.split("@@", 1)[1])


def set_fixture_ref_model(board, ref, model=None):
    """Rename U9 and optionally install one exact board-owned model."""
    code = (
        "import pcbnew,sys\n"
        "b=pcbnew.LoadBoard(sys.argv[1])\n"
        "fp=b.FindFootprintByReference('U9')\n"
        "fp.SetReference(sys.argv[2])\n"
        "fp.Models().clear()\n"
        "if len(sys.argv) > 3:\n"
        " m=pcbnew.FP_3DMODEL(); m.m_Filename=sys.argv[3]; "
        "fp.Models().push_back(m)\n"
        "b.Save(sys.argv[1])\n")
    args = [KPY, "-c", code, str(board), ref]
    if model is not None:
        args.append(str(model))
    must_pass(run(args), "prepare manual-body fixture")


@test("REGRESSION: a manual connector absent from the CPL is injected from "
      "assembly twin_body and counted by NO-BODY", kind="known_bad")
def t_manual_connector_body_not_dropped_by_cpl_denominator():
    """The released hub claimed 194/194 bodies while J3-J6 were four empty
    connector land patterns: NO-BODY walked only the CPL, and the manual
    connectors were excluded from it by design. This fixture has an EMPTY
    CPL and one post-installed J3, so the pre-fix denominator is exactly 0/0.
    The fixed run must inject the project model and grade 1/1.
    """
    d = tmpdir("manualbody_")
    board, _ = synth_board(d, 0)
    set_fixture_ref_model(board, "J3")
    body = d / "usb1130.wrl"
    bar_wrl(body)
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n")
    cpl = d / "cpl.csv"
    cpl.write_text("Designator,Val,Package,Mid X,Mid Y,Layer,Rotation\n")
    asm = d / "project" / "03_src" / "rules" / "assembly.yaml"
    asm.parent.mkdir(parents=True)
    part_dir = d / "project" / "02_parts" / "USB1130"
    part_dir.mkdir(parents=True)
    (part_dir / "part.yaml").write_text(
        "mpn: USB1130\ntwin_body:\n  source: file\n"
        f"  model: {body}\n  identity: exact manual USB-A body\n")
    asm.write_text(
        "service: standard\nsides: [top]\nfiducials: none\n"
        "build_quantity: 1\nnot_assembled:\n"
        "  - refs: [J3]\n    reason: not_in_catalog\n"
        "    on_bom: false\n"
        "    twin_body:\n      source: part\n"
        "      dossier: USB1130\n"
        "    evidence: dated fixture\n    disposition: install manually\n")
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    r = twin(d, board, bom, e2k,
             extra=("--assembly", str(asm), "--cpl", str(cpl)))
    must_pass(r, "manual connector twin")
    check("NETWORK WAS CALLED" not in r.out, "a local body triggered a fetch")
    contains(r.out, "bodies mounted: 1/1", "manual-inclusive denominator")
    mm = (d / "twin" / "missing_models.txt").read_text()
    contains(mm, "0 CPL placements", "the deliberately empty CPL")
    contains(mm, "1 declared manual-install bodies", "manual body source")
    contains(mm, "CPL bodies mounted: 0/0", "contractual CPL denominator")
    contains(mm, "manual bodies mounted: 1/1", "separate manual denominator")
    mounts = read_mount(d / "twin" / "twin.kicad_pcb", "J3")
    eq(len(mounts), 1, "J3 model count")
    eq(Path(mounts[0]["f"]), body.resolve(), "J3 project model")


@test("REGRESSION: F1 board body overrides a catalog near-match and keeps "
      "its original registration", kind="known_bad")
def t_board_body_suppresses_wrong_catalog_twin():
    """The hub's F1 is a four-hole complete Keystone 3568 holder. Its old
    assembly entry named C5249699, one loose clip, so jlc_twin cleared the
    correctly registered board model and mounted the clip at a rejected
    3.26 mm fallback fit. Keep a deliberately wrong code in this fixture:
    `source: board` must suppress fetching it and preserve the exact path and
    zero transform byte-for-byte.
    """
    d = tmpdir("boardbody_")
    board, _ = synth_board(d, 0)
    holder = d / "complete-holder.wrl"
    bar_wrl(holder)
    symbolic = "${KICAD10_3DMODEL_DIR}/complete-holder.wrl"
    set_fixture_ref_model(board, "F1", symbolic)
    before = read_mount(board, "F1")
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n")
    cpl = d / "cpl.csv"
    cpl.write_text("Designator,Val,Package,Mid X,Mid Y,Layer,Rotation\n")
    asm = d / "project" / "03_src" / "rules" / "assembly.yaml"
    asm.parent.mkdir(parents=True)
    part_dir = d / "project" / "02_parts" / "3568"
    part_dir.mkdir(parents=True)
    (part_dir / "part.yaml").write_text(
        "mpn: 3568\ntwin_body:\n  source: board\n"
        "  identity: complete four-hole holder\n")
    asm.write_text(
        "service: standard\nsides: [top]\nfiducials: none\n"
        "build_quantity: 1\nnot_assembled:\n"
        "  - refs: [F1]\n    reason: process_incompatible\n"
        "    lcsc: C_WRONG_LOOSE_CLIP\n    on_bom: false\n"
        "    twin_body:\n      source: part\n"
        "      dossier: 3568\n"
        "    evidence: dated fixture\n    disposition: install manually\n")
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    old_3d = os.environ.get("KICAD10_3DMODEL_DIR")
    os.environ["KICAD10_3DMODEL_DIR"] = str(d)
    try:
        r = twin(d, board, bom, e2k,
                 extra=("--assembly", str(asm), "--cpl", str(cpl)))
    finally:
        if old_3d is None:
            os.environ.pop("KICAD10_3DMODEL_DIR", None)
        else:
            os.environ["KICAD10_3DMODEL_DIR"] = old_3d
    must_pass(r, "board-owned holder twin")
    check("NETWORK WAS CALLED" not in r.out,
          "the forbidden loose-clip catalog body was fetched")
    after = read_mount(d / "twin" / "twin.kicad_pcb", "F1")
    eq(len(after), 1, "F1 model count")
    eq(Path(after[0]["f"]), holder.resolve(), "resolved F1 model path")
    eq({k: v for k, v in after[0].items() if k != "f"},
       {k: v for k, v in before[0].items() if k != "f"},
       "F1 scale, offset, and rotation")
    report = (d / "twin" / "twin_report.csv").read_text()
    contains(report, "JLC CAD replacement suppressed", "local-body semantics")
    not_contains(report, "C_WRONG_LOOSE_CLIP", "false catalog identity")
    not_contains(report, "MOUNT-FALLBACK", "wrong catalog registration")


@test("INVARIANT: a mounted body's pose is JLC's pose turned by the fitted "
      "angle — at 0/90/180/270, covering xform, the mount offset, the mount "
      "z-rotation and reg_check in one assertion", kind="known_bad")
def t_mount_pose_invariant():
    """ONE test for all four rotation sites. For each fit angle it:

      1. builds a synthetic JLC footprint (scalene pad triangle, asymmetric
         body, NON-ZERO model offset AND model rotation — a sign error in
         either alone is invisible when the other is zero),
      2. builds OUR board footprint by letting PCBNEW rotate that pad set,
      3. draws the courtyard where the invariant says the body must land,
      4. runs the real jlc_twin,
      5. asserts the fitted offset == the angle pcbnew applied,
      6. asserts the MOUNTED model's pose == formA(ang) of JLC's pose, and
      7. asserts MODEL-REG-OK — reg_check, computed by a different route
         (courtyard-vs-bbox), agreeing.

    Step 7 is why this replaces a per-function test: before 2026-07-25
    reg_check shared the mount's wrong form, so steps 6 and 7 were consistent
    with each other AND both wrong. They now come from different operators
    over different inputs.

    RED-VERIFIED 2026-07-25 by restoring each pre-fix line in the live file,
    running `--only=INVARIANT`, and restoring. Verbatim failures:
      - mount OFFSET `(x*c - y*sn, x*sn + y*c)`:
        "mounted body bbox at 90 deg: got (0.483, -0.833, 8.483, 1.167),
         want (-0.75, -2.5, 7.25, -0.5) (max delta 1.667 mm)"
      - mount Z `+ ang` instead of `- ang`:
        "... got (-8.75, -2.5, -0.75, -0.5) ... (max delta 8.000 mm)"
      - reg_check MODEL-FRAME `(mx*cm - my*sm, ...)` (i.e. model_rot):
        "reg_check produced no verdict at 0 deg (statuses ['MODEL-REG',
         'MODEL-SELF', 'OK'])" — the body is graded OFF its courtyard
      - reg_check FIT-TRANSFORM `(x*c - y*sn, ...)`:
        "reg_check produced no verdict at 90 deg (statuses ['MODEL-REG',
         'MODEL-SELF', 'ROT-DB-SUGGEST'])"
    Four sites, four red lights. The offset revert passes at 0/180 and fails
    only at 90/270 — the exact signature that let it ship.
    """
    for ang in (0, 90, 180, 270):
        d = tmpdir("twinmount%s_" % ang)
        wrl = d / "bar.wrl"
        bar_wrl(wrl)
        code = "C900001"
        jlc_mod(d, code, str(wrl))
        # the courtyard is where the INVARIANT says the body goes; it is
        # derived from JLC's pose + formA, never from the mount's output.
        _, meta = synth_board(d, ang, name="probe%s.kicad_pcb" % ang)
        want, wrong = expected_local(ang, meta["rotated"])
        board, meta = synth_board(d, ang, courtyard=list(want),
                                  name="synth%s.kicad_pcb" % ang)
        bom = d / "bom.csv"
        bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                       "synthetic,U9,SYNTH,,%s\n" % code)
        e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay is broken\n",
                       rc=1)
        r = run([KPY, TWIN, board, bom, d / "twin", "--no-render"],
                cwd=d, env={"EASYEDA2KICAD": str(e2k),
                            "JLC_TWIN_FETCH_ATTEMPTS": "1"})
        check("NETWORK WAS CALLED" not in r.out,
              "replay broken: the fetcher was invoked")

        # 5. the fit recovered the angle PCBNEW applied
        contains(r.out, "jlc_offset=%d " % ang,
                 "fitted offset at %s deg" % ang)

        # 6. the mounted pose IS formA(ang) of JLC's pose
        ms = read_mount(d / "twin" / "twin.kicad_pcb")
        check(len(ms) == 1,
              "expected exactly one mounted model, got %d" % len(ms))
        m = ms[0]
        got = bbox_of(render_pose(BAR, (m["ox"], m["oy"]), m["rz"],
                                  (m["sx"], m["sy"])))
        err = max(abs(g - w) for g, w in zip(got, want))
        werr = max(abs(g - w) for g, w in zip(got, wrong))
        check(err < 0.02,
              "mounted body bbox at %s deg: got %s, want %s (max delta "
              "%.3f mm) — the mount offset and/or the mount z-rotation is "
              "not formA(%s) of JLC's pose"
              % (ang, tuple(round(v, 3) for v in got),
                 tuple(round(v, 3) for v in want), err, ang))
        # DISCRIMINATION: the fixture must be able to tell the two forms
        # apart at 90/270 — otherwise the assertion above proves nothing.
        if ang in (90, 270):
            check(werr > 1.0,
                  "at %s deg this fixture cannot distinguish formA from "
                  "formB (they differ by only %.3f mm) — it would have "
                  "passed the shipped bug; make the body more asymmetric"
                  % (ang, werr))

        # 7. reg_check agrees, by a different route, and does not block
        import csv as _csv
        rows = list(_csv.DictReader(
            open(str(d / "twin" / "twin_report.csv"))))
        stat = {row["Status"] for row in rows if row["Ref"] == "U9"}
        check("MODEL-REG-OK" in stat,
              "reg_check produced no verdict at %s deg (statuses %s)"
              % (ang, sorted(stat)))
        check("MODEL-REG" not in stat,
              "reg_check reported the body OFF the courtyard at %s deg, "
              "where the mount agrees with the invariant — reg_check's own "
              "frame math has drifted:\n%s"
              % (ang, [row for row in rows if row["Status"] == "MODEL-REG"]))
        check(r.rc == 0,
              "clean synthetic mount at %s deg should exit 0:\n%s"
              % (ang, r.out[-2000:]))


def _red_bbox(png):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    w, h = im.size
    px = im.load()
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 110 and r - g > 50 and r - b > 50:
                xs.append(x)
                ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


@test("model_rot() reproduces what kicad-cli ACTUALLY renders for an "
      "m_Rotation.z, and the opposite sign provably does not",
      kind="known_bad")
def t_model_rot_matches_render():
    """The model-frame operator cannot be pinned by the invariant above — it
    appears on both sides there and cancels. So it is pinned against the only
    authority that cannot be wrong about what KiCad draws: KiCad's renderer.

    MEASURED (2026-07-25): an asymmetric bar (model frame x 0..8 mm,
    y -1..+1 mm) at board (20,20), rendered `--side top` at 19.25 px/mm.
    rot_z 90 puts the long axis SOUTH and 270 puts it NORTH, each within
    0.014 mm of this form; the pre-fix form predicts the exact opposite at
    both (8.000 mm out), and the two agree at 0/180 — the same
    sign-invariance that hid four other copies of this bug.

    RED-VERIFIED: restoring `(mx*c - my*s, mx*s + my*c)` in
    jlc_twin.model_rot() makes this FAIL at the live probe — "model_rot((1,0),
    90) = [0.0, 1.0]; the renderer puts it at (0,-1)"."""
    d = tmpdir("modelrot_")
    wrl = d / "bar.wrl"
    bar_wrl(wrl)
    seen = {}
    for rz in (0, 90, 180, 270):
        board, _ = synth_board(d, 0, name="mr%s.kicad_pcb" % rz)
        must_pass(run([KPY, "-c",
                       "import pcbnew,sys\n"
                       "b=pcbnew.LoadBoard(sys.argv[1])\n"
                       "fp=b.FindFootprintByReference('U9')\n"
                       "m=pcbnew.FP_3DMODEL()\n"
                       "m.m_Filename=sys.argv[2]\n"
                       "m.m_Scale=pcbnew.VECTOR3D(1,1,1)\n"
                       "m.m_Offset=pcbnew.VECTOR3D(0,0,0)\n"
                       "m.m_Rotation=pcbnew.VECTOR3D(0,0,float(sys.argv[3]))\n"
                       "fp.Models().push_back(m)\n"
                       "b.Save(sys.argv[1])\n",
                       str(board), str(wrl), str(rz)]),
                  "attach model at rot_z=%s" % rz)
        png = d / ("mr%s.png" % rz)
        run(["kicad-cli", "pcb", "render", "--width", "800", "--height", "800",
             "--side", "top", "--zoom", "1.0", "-o", str(png), str(board)])
        check(png.exists(), "kicad-cli produced no render for rot_z=%s" % rz)
        seen[rz] = _red_bbox(png)
        check(seen[rz] is not None,
              "no red body pixels in the rot_z=%s render — the fixture model "
              "did not load, so this test proves nothing" % rz)

    def is_vertical(bb):
        return (bb[3] - bb[1]) > (bb[2] - bb[0])

    for rz in (90, 270):
        check(is_vertical(seen[rz]),
              "rot_z=%s did not turn the bar at all (bbox %s) — the render is "
              "not exercising m_Rotation.z" % (rz, seen[rz]))
    ox = seen[0][0]                        # x of the bar's origin end
    oy = (seen[0][1] + seen[0][3]) / 2.0   # y of the model origin
    check(seen[90][3] > oy + 20 and seen[90][1] > oy - 20,
          "rot_z 90: the rendered long axis does not point SOUTH "
          "(origin y=%.0f, bar y %s..%s) — model_rot's sign disagrees with "
          "the renderer" % (oy, seen[90][1], seen[90][3]))
    check(seen[270][1] < oy - 20 and seen[270][3] < oy + 20,
          "rot_z 270: the rendered long axis does not point NORTH "
          "(origin y=%.0f, bar y %s..%s)"
          % (oy, seen[270][1], seen[270][3]))
    check(seen[180][2] < ox + 20,
          "rot_z 180 did not mirror rot_z 0 about the model origin")
    # and the LIVE function must BE that form, not merely agree in spirit
    import json as _json
    probe = ("import sys,json\n"
             "sys.path.insert(0, %r)\n"
             "import jlc_twin\n"
             "print('@@'+json.dumps([jlc_twin.model_rot(1.0,0.0,90.0),\n"
             "                       jlc_twin.model_rot(1.0,0.0,270.0)]))\n"
             % str(FAB_SCRIPTS))
    a, b = _json.loads(must_pass(run([KPY, "-c", probe]),
                                 "live model_rot probe")
                       .out.split("@@", 1)[1])
    check(abs(a[0]) < 1e-9 and abs(a[1] + 1.0) < 1e-9,
          "model_rot((1,0), 90) = %s; the renderer puts it at (0,-1) in the "
          "model's y-up frame (= SOUTH once flipped to the board frame)" % a)
    check(abs(b[0]) < 1e-9 and abs(b[1] - 1.0) < 1e-9,
          "model_rot((1,0), 270) = %s; want (0,+1)" % b)


# ================================================================ NO-BODY
@test("a CPL designator whose 3D model path does not resolve is NO-BODY and "
      "BLOCKS — and a PAD-MISMATCH waiver cannot discharge it",
      kind="known_bad")
def t_no_body_blocks():
    """usb-hub-3s-v3 v1.5 shipped 7 of 108 placements with no rendered body
    while its own `missing_models.txt` said the gap was zero, because ONE
    PAD-MISMATCH adjudication drained the criticals list and nothing anywhere
    asked "did a body actually render?". Three things are pinned here: the
    question is now ASKED, the answer is GENERATED rather than hand-authored,
    and it has its OWN adjudication key."""
    d = tmpdir("nobody_")
    code = "C900002"
    for sub in ("twin", "twin2", "twin3"):
        jlc_mod(d, code, "${KICAD_NO_SUCH_VAR_AT_ALL}/nope.step", out=sub)
    board, _ = synth_board(d, 0)
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   "synthetic,U9,SYNTH,,%s\n" % code)
    cpl = d / "cpl.csv"
    cpl.write_text("Designator,Val,Package,Mid X,Mid Y,Layer,Rotation\n"
                   "U9,synthetic,SYNTH,30.0,-25.0,top,0.0\n")
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    r = run([KPY, TWIN, board, bom, d / "twin", "--no-render",
             "--cpl", str(cpl)],
            cwd=d, env={"EASYEDA2KICAD": str(e2k),
                        "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    must_fail(r, "jlc_twin on an unresolvable model path", "NO-BODY")
    contains(r.out, "bodies mounted: 0/1", "the headline coverage counter")
    mm = d / "twin" / "missing_models.txt"
    check(mm.exists(), "missing_models.txt was not generated")
    contains(mm.read_text(), "U9", "generated missing_models.txt")
    contains(mm.read_text(), "GENERATED", "missing_models.txt provenance")

    # the waiver-cannot-discharge half: a PAD-MISMATCH adjudication for the
    # SAME part must leave NO-BODY blocking.
    adj = d / "adj.yaml"
    adj.write_text("- {lcsc: %s, refs: [U9], status: PAD-MISMATCH,\n"
                   "   why: \"a waiver about the land pattern\"}\n" % code)
    r2 = run([KPY, TWIN, board, bom, d / "twin2", "--no-render",
              "--cpl", str(cpl), "--adjudications", str(adj)],
             cwd=d, env={"EASYEDA2KICAD": str(e2k),
                         "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    must_fail(r2, "a PAD-MISMATCH waiver must NOT discharge NO-BODY",
              "NO-BODY")

    # ...and its OWN key does discharge it (the escape hatch still exists)
    adj2 = d / "adj2.yaml"
    adj2.write_text("- {lcsc: %s, refs: [U9], status: NO-BODY,\n"
                    "   why: \"measured: bench-verified, model absent "
                    "upstream\"}\n" % code)
    r3 = run([KPY, TWIN, board, bom, d / "twin3", "--no-render",
              "--cpl", str(cpl), "--adjudications", str(adj2)],
             cwd=d, env={"EASYEDA2KICAD": str(e2k),
                         "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    check(r3.rc == 0,
          "an explicit NO-BODY adjudication should clear it:\n%s"
          % r3.out[-1500:])


@test("MODEL-REG is BLOCKING: a body mounted off its own courtyard fails the "
      "run instead of printing a comment", kind="known_bad")
def t_model_reg_blocks():
    """MODEL-REG was emitted at one site and never appended to `criticals`,
    so it could not fail a run: usb-hub-3s-v3 v1.5 sealed with a TRUE 14.37 mm
    finding on J1 sitting beside a green verdict. Here the courtyard is
    deliberately drawn 6 mm off where the body really lands — the ONE thing
    broken about an otherwise clean fixture."""
    d = tmpdir("modelreg_")
    wrl = d / "bar.wrl"
    bar_wrl(wrl)
    code = "C900003"
    jlc_mod(d, code, str(wrl))
    _, meta = synth_board(d, 0, name="probe.kicad_pcb")
    want, _ = expected_local(0, meta["rotated"])
    off = [want[0] + 6.0, want[1], want[2] + 6.0, want[3]]   # 6 mm east
    board, _ = synth_board(d, 0, courtyard=off, name="bad.kicad_pcb")
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   "synthetic,U9,SYNTH,,%s\n" % code)
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    r = run([KPY, TWIN, board, bom, d / "twin", "--no-render"],
            cwd=d, env={"EASYEDA2KICAD": str(e2k),
                        "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    must_fail(r, "jlc_twin on a body mounted off its courtyard", "MODEL-REG")


@test("a pad number with different MULTIPLICITY on the two footprints still "
      "fits (by centroid) instead of discarding the whole part",
      kind="known_bad")
def t_pad_multiplicity_fits():
    """KiCad's PowerPAK_SO-8_Single names FIVE entities '5' (merged paddle +
    four drain fingers) where JLC's DFN-8 names one corner lead '5'. `fit_err`
    used to `return None` on that, so best_fit came back empty, the part fell
    out through PAD-MISMATCH, and its mount, rotation audit and MODEL-REG ALL
    silently skipped — six power MOSFETs shipped unverified that way on
    usb-hub-3s-v3 v1.5. The multiplicity is a NAMING convention; it must not
    cost the audit. Fixture at 90 deg on purpose: the angle the handedness
    bug lands on."""
    d = tmpdir("padmult_")
    wrl = d / "bar.wrl"
    bar_wrl(wrl)
    code = "C900004"
    # JLC names pad '3' TWICE, straddling our single pad-3 position, so the
    # two centroids coincide and only the multiplicity differs.
    # Position matters: jlc_twin anchors the fit on the UNWEIGHTED point
    # centroid, so an extra point biases the anchor by (P - mean)/n. Placing
    # pad 3's pair around (0.6, -0.4) keeps that bias at 0.14 mm — small
    # enough that the fit must succeed on its merits, not on slack.
    OURS = {"1": (-2.0, -1.0), "2": (2.0, -1.0), "3": (0.6, -0.4)}
    jlc_mod(d, code, str(wrl),
            pads={"1": (-2.0, -1.0), "2": (2.0, -1.0), "3": (0.2, -0.4)},
            extra_pads=[("3", (1.0, -0.4))])
    board, _ = synth_board(d, 90, pads=OURS)
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   "synthetic,U9,SYNTH,,%s\n" % code)
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    r = run([KPY, TWIN, board, bom, d / "twin", "--no-render"],
            cwd=d, env={"EASYEDA2KICAD": str(e2k),
                        "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    contains(r.out, "PAD-MULTIPLICITY", "the multiplicity is REPORTED")
    contains(r.out, "jlc_offset=90",
             "the rotation audit ran despite the multiplicity (pre-fix this "
             "was PAD-MISMATCH best=none and the audit silently skipped)")
    not_contains(r.out, "best=none",
                 "fit_err still discards the part on a multiplicity mismatch")

# ============================================================ POLARITY-FIT
# A 2-pad collinear polarized part is the ONE case where a perfect pad fit is
# not evidence: the two pads are symmetric, so a library that numbers the
# CATHODE "2" where we number it "1" fits exactly at 180 and ships the part
# REVERSED. This class produced P0s on three boards.
#
# MEASURED (2026-07-25) on the real parts this fixture is modelled from —
# C2296 (KT-0805Y amber) and C2297 (KT-0805G green):
#   pad-number fit through the verified operator: offset 180, residual
#     0.1125 mm, next non-mirrored candidate 1.9875 mm (17.7x margin) —
#     confidently and PRECISELY wrong.
#   numbering-free: JLC's F.SilkS diode glyph points its apex WEST and its
#     silk body is chamfered WEST (two channels agreeing) => JLC pad 1 =
#     ANODE. KiCad's Device:LED symbol is pin1=K/pin2=A and
#     LED_0805_2012Metric chamfers F.Fab at pin 1 => our pad 1 = CATHODE.
#   Both libraries draw the cathode at the WEST end, so the PHYSICAL parts
#   already align and the correct CPL offset is 0, not the fitted 180.

_POL_BOARD = (
    "import json, sys\n"
    "import pcbnew\n"
    "out = sys.argv[1]; mark_pad = sys.argv[2]\n"
    "rotation = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0\n"
    "b = pcbnew.NewBoard(out)\n"
    "for (x1,y1),(x2,y2) in (((0,0),(40,0)),((40,0),(40,40)),\n"
    "                        ((40,40),(0,40)),((0,40),(0,0))):\n"
    "    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)\n"
    "    s.SetStart(pcbnew.VECTOR2I(int(x1*1e6), int(y1*1e6)))\n"
    "    s.SetEnd(pcbnew.VECTOR2I(int(x2*1e6), int(y2*1e6)))\n"
    "    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(100000); b.Add(s)\n"
    "POS = (20.0, 20.0)\n"
    "fp = pcbnew.FOOTPRINT(b)\n"
    "fp.SetReference('D8')\n"
    "fp.SetFPID(pcbnew.LIB_ID('synth', 'LED_SYNTH_2012Metric'))\n"
    "fp.SetPosition(pcbnew.VECTOR2I(int(POS[0]*1e6), int(POS[1]*1e6)))\n"
    "for n, x in (('1', -0.9375), ('2', 0.9375)):\n"
    "    p = pcbnew.PAD(fp); p.SetNumber(n)\n"
    "    p.SetShape(pcbnew.PAD_SHAPE_RECT)\n"
    "    p.SetSize(pcbnew.VECTOR2I(int(0.975e6), int(1.4e6)))\n"
    "    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)\n"
    "    p.SetLayerSet(p.SMDMask())\n"
    "    p.SetPosition(pcbnew.VECTOR2I(int((POS[0]+x)*1e6), int(POS[1]*1e6)))\n"
    "    fp.Add(p)\n"
    "# the polarity MARKING: an F.Fab outline that overhangs one end\n"
    "ov = -1.7 if mark_pad == '1' else 1.7\n"
    "sh = pcbnew.PCB_SHAPE(fp); sh.SetShape(pcbnew.SHAPE_T_SEGMENT)\n"
    "sh.SetStart(pcbnew.VECTOR2I(int((POS[0]+ov)*1e6), int((POS[1]-0.9)*1e6)))\n"
    "sh.SetEnd(pcbnew.VECTOR2I(int((POS[0]+ov)*1e6), int((POS[1]+0.9)*1e6)))\n"
    "sh.SetLayer(pcbnew.F_Fab); sh.SetWidth(120000); fp.Add(sh)\n"
    "b.Add(fp); fp.SetOrientationDegrees(rotation); b.Save(out)\n"
    "print('@@ok')\n")


def pol_board(d, mark_pad, name="pol.kicad_pcb", rotation=0):
    """OUR footprint: pad 1 WEST, pad 2 EAST, marking overhanging `mark_pad`."""
    board = d / name
    must_pass(run([KPY, "-c", _POL_BOARD, str(board), mark_pad,
                   str(rotation)]),
              "build polarized fixture (mark at pad %s)" % mark_pad)
    return board


def pol_jlc(d, code, mark_pad, out="twin"):
    """JLC's footprint: pad 1 EAST, pad 2 WEST (the numbering this fixture is
    about), with its silk marking overhanging whichever pad is named."""
    cache = d / out / "easyeda" / code / "jlc.pretty"
    cache.mkdir(parents=True, exist_ok=True)
    ov = -2.2 if mark_pad == "2" else 2.2      # pad 2 is WEST on JLC's side
    wrl = d / "bar.wrl"
    if not wrl.exists():
        bar_wrl(wrl)
    (cache / "synth.kicad_mod").write_text(
        '(footprint "LED0805-SYNTH" (version 20240108) (generator "test")\n'
        '  (layer "F.Cu")\n'
        '  (pad "1" smd rect (at 1.05 0) (size 1.0 1.4) '
        '(layers "F.Cu" "F.Paste" "F.Mask"))\n'
        '  (pad "2" smd rect (at -1.05 0) (size 1.0 1.4) '
        '(layers "F.Cu" "F.Paste" "F.Mask"))\n'
        '  (fp_line (start %s -0.9) (end %s 0.9) (layer F.SilkS) '
        '(width 0.12))\n'
        # A refdes TEXT deliberately placed at the OPPOSITE end from the
        # marking, and FURTHER out. Text is placed for legibility, never to
        # mark polarity — if marker_side ever counts it again, it will read
        # this fixture's polarity backwards and both POLARITY-FIT tests go
        # RED. Without this the "shapes only" rule was unpinned.
        '  (fp_text user "REF**" (at %s 0) (layer F.SilkS) '
        '(effects (font (size 1 1) (thickness 0.15))))\n'
        '  (model "%s"\n    (offset (xyz 0 0 0))\n'
        '    (scale (xyz 1 1 1))\n    (rotate (xyz 0 0 0))\n  )\n)\n'
        % (ov, ov, -ov * 1.6, wrl))
    return cache / "synth.kicad_mod"


def pol_run(d, board, code, outdir="twin", adj=None):
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   "synthetic LED,D8,LED_SYNTH_2012Metric,,%s\n" % code)
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    args = [KPY, TWIN, board, bom, d / outdir, "--no-render"]
    if adj:
        args += ["--adjudications", str(adj)]
    return run(args, cwd=d, env={"EASYEDA2KICAD": str(e2k),
                                 "JLC_TWIN_FETCH_ATTEMPTS": "1"})


@test("a 2-pad polarized part whose libraries NUMBER the terminals oppositely "
      "is POLARITY-FIT and BLOCKS, even though the pad fit is perfect",
      kind="known_bad")
def t_polarity_fit_blocks():
    """The fixture is the C2296/C2297 situation exactly: our marking sits at
    pad 1, JLC's at pad 2, and the pad-number fit is EXACT at 180. Before this
    check the run went green, a ROT-DB-SUGGEST row of 180 would have been
    written into the per-LCSC table on the strength of that fit, and every LED
    would have shipped reversed — dark, and indistinguishable from a bad
    joint on the bench.

    RED-VERIFIED 2026-07-25: deleting the `criticals.append(ref)` under the
    POLARITY-FIT branch makes this FAIL (the finding still prints but the run
    exits 0); deleting the whole branch makes it FAIL on the missing string.
    """
    d = tmpdir("polfit_")
    code = "C900010"
    pol_jlc(d, code, mark_pad="2")          # JLC marks its pad 2 (west)
    board = pol_board(d, mark_pad="1")      # we mark our pad 1 (west)
    r = pol_run(d, board, code)
    must_fail(r, "jlc_twin on opposite terminal numbering", "POLARITY-FIT")
    contains(r.out, "jlc_offset=180",
             "the pad fit still reports its (physically wrong) 180")
    contains(r.out, "offset 0 is what places the part correctly",
             "the finding must name the PHYSICALLY correct offset")

    # a PAD-GEOM waiver must NOT discharge it — own key, like NO-BODY
    adj = d / "adj.yaml"
    adj.write_text("- {lcsc: %s, refs: [D8], status: PAD-GEOM,\n"
                   "   why: \"a waiver about the land pattern\"}\n" % code)
    r2 = pol_run(d, board, code, outdir="twin2", adj=adj)
    pol_jlc(d, code, mark_pad="2", out="twin2")
    r2 = pol_run(d, board, code, outdir="twin2", adj=adj)
    must_fail(r2, "a PAD-GEOM waiver must not discharge POLARITY-FIT",
              "POLARITY-FIT")


@test("when both libraries mark the SAME pad, POLARITY-FIT confirms the fit "
      "instead of crying wolf")
def t_polarity_fit_agrees():
    """The check must not fire on every polarized part — a gate that always
    fires is a gate that gets waived by habit. Here JLC marks its pad 1 (east,
    which the 180 fit maps onto our pad 1), so the marking channel and the pad
    channel agree and the run is clean."""
    d = tmpdir("polok_")
    code = "C900011"
    pol_jlc(d, code, mark_pad="1")          # JLC marks its pad 1 (east)
    board = pol_board(d, mark_pad="1")
    r = pol_run(d, board, code)
    contains(r.out, "POLARITY-FIT-OK", "the agreeing verdict")
    check("POLARITY-FIT " not in r.out.replace("POLARITY-FIT-OK", "PFOK"),
          "POLARITY-FIT cried wolf on an agreeing part:\n%s" % r.out[-1500:])
    check(r.rc == 0, "an agreeing polarized part should exit 0:\n%s"
                     % r.out[-1500:])


@test("POLARITY-FIT compares graphics and pads in one local frame on a "
      "180-degree board instance")
def t_polarity_fit_agrees_rotated_180():
    """The board rotation is placement, not terminal identity. The historical
    implementation zeroed the pad cloud, restored the board rotation, and only
    then measured the graphics; that mixed coordinate frames and made the same
    footprint pass at 0 degrees but fail at 180 degrees (programmable USB hub
    D2/D3, C2128)."""
    d = tmpdir("polok180_")
    code = "C900013"
    pol_jlc(d, code, mark_pad="1")
    board = pol_board(d, mark_pad="1", rotation=180)
    r = pol_run(d, board, code)
    contains(r.out, "POLARITY-FIT-OK", "the rotated agreeing verdict")
    check("POLARITY-FIT " not in r.out.replace("POLARITY-FIT-OK", "PFOK"),
          "POLARITY-FIT mixed local/global frames at 180 degrees:\n%s"
          % r.out[-1500:])
    check(r.rc == 0, "a rotated agreeing polarized part should exit 0:\n%s"
                     % r.out[-1500:])


@test("a polarized part with NO usable marking is reported BLIND, never "
      "silently passed")
def t_polarity_fit_blind():
    """Silence is the failure mode this whole file exists to kill. If the
    numbering-free channel cannot run, the run must SAY so — the human
    order-preview gate is then the only thing standing between the part and a
    180deg reversal, and nobody can know that from a green log."""
    d = tmpdir("polblind_")
    code = "C900012"
    cache = d / "twin" / "easyeda" / code / "jlc.pretty"
    cache.mkdir(parents=True, exist_ok=True)
    wrl = d / "bar.wrl"
    bar_wrl(wrl)
    (cache / "synth.kicad_mod").write_text(
        '(footprint "LED0805-BARE" (version 20240108) (generator "test")\n'
        '  (layer "F.Cu")\n'
        '  (pad "1" smd rect (at 1.05 0) (size 1.0 1.4) '
        '(layers "F.Cu" "F.Paste" "F.Mask"))\n'
        '  (pad "2" smd rect (at -1.05 0) (size 1.0 1.4) '
        '(layers "F.Cu" "F.Paste" "F.Mask"))\n'
        '  (model "%s"\n    (offset (xyz 0 0 0))\n'
        '    (scale (xyz 1 1 1))\n    (rotate (xyz 0 0 0))\n  )\n)\n' % wrl)
    board = pol_board(d, mark_pad="1")
    r = pol_run(d, board, code)
    contains(r.out, "POLARITY-FIT-BLIND", "the blind verdict")
    contains(r.out, "ONLY the human order-preview gate",
             "the blind verdict must name what is carrying the risk")

# ------------------------------------------------- pad_alias permutation
def _twin_fn(name):
    """Import ONE pure helper out of jlc_twin without importing pcbnew."""
    src = (FAB_SCRIPTS / "jlc_twin.py").read_text()
    s = src.index("def apply_pad_alias(")
    e = src.index("def centroid(")
    ns = {}
    exec(src[s:e], ns)
    return ns[name]


def _old_apply_pad_alias(jraw, alias):
    """The PRE-FIX implementation, verbatim — kept so the tests below can be
    shown to go RED against it (tests/README: verify the fix against the
    pre-fix code and say so)."""
    jraw = {k: list(v) for k, v in jraw.items()}
    for src, dst in alias.items():
        if src in jraw and src != dst:
            jraw.setdefault(dst, []).extend(jraw.pop(src))
            jraw[dst] = sorted(jraw[dst])
    return jraw


# LS1 (C22359707) on crow-mic-pod-v2, measured 2026-07-25: read in ONE
# convention, our pads 1/2 COINCIDE with JLC's and 3/4 (both NC dummies) are
# transposed. The true correspondence is therefore a 2-way 3<->4 swap.
LS1_JLC = {"1": [(-3.6, -3.6)], "2": [(-3.6, 3.6)],
           "3": [(3.6, 3.6)], "4": [(3.6, -3.6)]}


@test("pad_alias applies a 2-WAY SWAP as one simultaneous permutation",
      kind="known_bad")
def t_pad_alias_two_way_swap():
    """THE BUG. The old loop mutated `jraw` while iterating the alias, so each
    rename saw the previous one's result. For {3:4, 4:3}: step one moved pad
    3 onto key 4 (now holding both), step two moved key 4 — BOTH entries —
    onto key 3. Pad 4 vanished and pad 3 doubled, so a 2-way swap could not
    be written down at all.

    That is why crow-mic-pod-v2 v1.0's LS1 waiver asserts a 1<->2 swap: the
    only correspondence the file format could express. It fits the geometry
    at NO rotation (rms 7.1007mm at all four angles) while the true 3<->4
    swap fits at 0.1414mm."""
    apply_pad_alias = _twin_fn("apply_pad_alias")
    swap = {"3": "4", "4": "3"}

    got = apply_pad_alias(LS1_JLC, swap)
    eq(sorted(got), ["1", "2", "3", "4"], "a 2-way swap must keep all 4 pads")
    eq(got["3"], [(3.6, -3.6)], "JLC pad 4's coords must land on key 3")
    eq(got["4"], [(3.6, 3.6)], "JLC pad 3's coords must land on key 4")
    check(all(len(v) == 1 for v in got.values()),
          f"no pad may be doubled: { {k: len(v) for k, v in got.items()} }")

    # RED-VERIFY against the pre-fix code
    bad = _old_apply_pad_alias(LS1_JLC, swap)
    check(sorted(bad) != ["1", "2", "3", "4"] or
          any(len(v) != 1 for v in bad.values()),
          "the pre-fix implementation must FAIL this test — if it passes, "
          "the test is not pinning the bug")
    eq(sorted(bad), ["1", "2", "3"],
       "pre-fix behaviour, pinned: pad 4 is lost and pad 3 doubled")


@test("pad_alias leaves an identity alias and a real tab-merge unchanged")
def t_pad_alias_identity_and_merge():
    """Regression guard on the case pad_alias was BUILT for: the SOT-223 tab
    (KiCad merges tab+lead as '2', JLC names the tab '4') must still merge,
    and an identity alias must still be a no-op — the old `src != dst` guard
    existed only to stop the in-place loop doubling a pad, and the
    snapshot-based permutation makes it unnecessary rather than missing."""
    apply_pad_alias = _twin_fn("apply_pad_alias")
    sot = {"1": [(0.0, 0.0)], "2": [(1.0, 0.0)], "3": [(2.0, 0.0)],
           "4": [(1.0, 2.0)]}
    merged = apply_pad_alias(sot, {"4": "2"})
    eq(sorted(merged), ["1", "2", "3"], "the tab must merge into pad 2")
    eq(len(merged["2"]), 2, "pad 2 must carry both the lead and the tab")
    eq(apply_pad_alias(sot, {"2": "2"}), sot, "an identity alias is a no-op")
    eq(apply_pad_alias(sot, {}), sot, "an empty alias is a no-op")


@test("a PAD-MISMATCH mounts the body at JLC's OWN transform, never at the "
      "fit it just rejected", kind="known_bad")
def t_mount_fallback_on_failed_fit():
    """THE INCIDENT (2026-07-26). On PAD-MISMATCH this tool recorded "no
    correspondence" and then mounted the body at that SAME rejected fit's
    angle — corrupting the render a human is explicitly told to inspect
    ("VERIFY leads sit on pads visually"). crow-recorder-central-v2 v1.4 and
    v1.5 both sealed with J2, the board's only USB-C, reporting
    `PAD-MISMATCH best=(4.594738839150707, False, 90)` and rendering 90
    DEGREES ROTATED: 7.555 x 8.940 mm where the part is 8.940 x 7.555.

    THE FIXTURE. Our pads are JLC's pad triangle turned 90 deg with pad 3
    displaced 3.0 mm east, so the best non-mirrored fit is 90 deg at a
    MEASURED 2.00 mm residual (the common-pad centroid absorbs a third of the
    displacement) — four times FIT_TOL, and therefore no correspondence.
    Note the DISCRIMINATION requirement (canon M-DISC): the best failed fit
    must be a NON-ZERO angle, or the fallback and the bug produce the same
    mount and this test proves nothing. Here they differ by 90 deg of model
    rot_z (JLC's own 90 vs the bug's 90-90=0) and by 4.9 mm of body bbox.

    RED-VERIFIED 2026-07-26 by restoring the pre-fix `twin[ref] = (jfp,
    nm[0][2], oc, _jca, lcsc)` branch in the live file and re-running. The
    first assertion to go red is the MOUNT-FALLBACK row, which does not exist
    at all — the pre-fix run emits only PAD-MISMATCH / PAD-GEOM / MODEL-SELF
    and says nothing about which transform it mounted at. Measured on the
    same fixture with that branch in place: mounted `rot_z 0.0`, offset
    (0.25, 1.50), body bbox (0.25, -2.50, 8.25, -0.50) against the fallback's
    (0.70, -1.283, 2.70, 6.717) — 7.216 mm apart, i.e. the body lies along
    the WRONG AXIS. Restoring the fix turns it green again.
    """
    d = tmpdir("twinfallback_")
    wrl = d / "bar.wrl"
    bar_wrl(wrl)
    code = "C900002"
    jlc_mod(d, code, str(wrl))
    # rot_ydown(x, y, 90) == (y, -x); pad "3" then pushed 3.0 mm east.
    ours = {"1": (-1.0, 2.0), "2": (-1.0, -2.0), "3": (4.6, -2.0)}
    board, meta = synth_board(d, 0, pads=ours)
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   "synthetic,U9,SYNTH,,%s\n" % code)
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED - replay is broken\n", rc=1)
    r = run([KPY, TWIN, board, bom, d / "twin", "--no-render"],
            cwd=d, env={"EASYEDA2KICAD": str(e2k),
                        "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    check("NETWORK WAS CALLED" not in r.out, "replay broken")
    must_fail(r, "twin on an unfittable part", "PAD-MISMATCH")
    contains(r.out, "MOUNT-FALLBACK", "the fallback must be SAID, not silent")
    contains(r.out, "mounted at JLC's OWN footprint transform",
             "the fallback must name the transform it used")
    # the fitted angle that FAILED must be reported, so a reader can see the
    # mount is not it
    contains(r.out, "best 2.00mm at 90deg", "the rejected fit, quoted")

    ms = read_mount(d / "twin" / "twin.kicad_pcb")
    eq(len(ms), 1, "one mounted model")
    eq(ms[0]["rz"], JMODEL_ROT_Z, "mounted model rot_z")
    # and the body must land where JLC's own pose puts it once their pad
    # centroid is mapped onto ours — computed here from the invariant, not
    # from the tool.
    want, _ = expected_local(0, meta["rotated"])
    got = bbox_of(render_pose(BAR, (ms[0]["ox"], ms[0]["oy"]), ms[0]["rz"],
                              (ms[0]["sx"], ms[0]["sy"])))
    err = max(abs(g - w) for g, w in zip(got, want))
    check(err < 0.02,
          "fallback-mounted body bbox: got %s, want %s (max delta %.3f mm)"
          % (tuple(round(v, 3) for v in got),
             tuple(round(v, 3) for v in want), err))
    # DISCRIMINATION: the rejected fit's mount must be VISIBLY different, or
    # the assertion above would pass the bug.
    wrong, _ = expected_local(90, meta["rotated"])
    werr = max(abs(w - g) for w, g in zip(wrong, want))
    check(werr > 1.0,
          "this fixture cannot tell the fallback mount from the rejected "
          "fit's mount (they differ by only %.3f mm)" % werr)


@test("an explicit unique-pad mount anchor defeats duplicate ground-number "
      "centroid drift", kind="known_bad")
def t_mount_anchor_duplicate_ground_numbers():
    """The Pluto RX2 8-way SMA incident, reduced to its exact geometry.
    Our manufacturer footprint has signal pad 1 at the origin and separately
    numbered ground posts 2/3/4/5.  JLC has the same five hole centres but
    calls every ground post pad 2.  The common-number centroid therefore
    compares our signal+one corner with JLC's signal+four symmetric corners;
    it lies (-1.27,-1.27) mm from the real origin and shifts the model by
    sqrt(1.27^2+1.27^2) = 1.796 mm.

    The unique signal hole is an independent datum present exactly once on
    both sides.  An adjudicated 1->1 anchor must preserve the raw failed-fit
    evidence while placing JLC's zero-offset model exactly at our footprint
    origin.  Before the fix this schema was ignored and the mounted offset was
    (-1.27,+1.27) mm in KiCad model coordinates.
    """
    d = tmpdir("mountanchor_sma_")
    wrl = d / "bar.wrl"
    bar_wrl(wrl)
    code = "C429844"
    ours = {"1": (0.0, 0.0), "2": (-2.54, -2.54),
            "3": (2.54, -2.54), "4": (-2.54, 2.54),
            "5": (2.54, 2.54)}
    jlc_mod(d, code, str(wrl),
            pads={"1": (0.0, 0.0), "2": (-2.54, -2.54)},
            extra_pads=[("2", (2.54, -2.54)),
                        ("2", (-2.54, 2.54)),
                        ("2", (2.54, 2.54))],
            rot_z=0.0, off=(0.0, 0.0))
    board, _ = synth_board(d, 0, pads=ours)
    bom = d / "bom.csv"
    bom.write_text("Comment,Designator,Footprint,MPN,LCSC\n"
                   f"SMA,U9,SYNTH,,{code}\n")
    adj = d / "adj.yaml"
    adj.write_text(
        f"- {{lcsc: {code}, refs: [U9], status: PAD-MISMATCH, "
        "why: exact hole centres independently verified}\n"
        f"- {{lcsc: {code}, refs: [U9], status: PAD-GEOM, "
        "why: exact hole centres independently verified}\n"
        f"- lcsc: {code}\n"
        "  refs: [U9]\n"
        "  status: MODEL-REG\n"
        "  mount_anchor: {our_pad: '1', jlc_pad: '1', angle: 0}\n"
        "  why: unique signal-hole origin independently verified\n")
    e2k = stub_e2k(d, stderr="NETWORK WAS CALLED\n", rc=1)
    r = run([KPY, TWIN, board, bom, d / "twin", "--no-render",
             "--adjudications", adj], cwd=d,
            env={"EASYEDA2KICAD": str(e2k),
                 "JLC_TWIN_FETCH_ATTEMPTS": "1"})
    must_pass(r, "anchored twin on duplicate SMA ground numbers")
    contains(r.out, "best 1.80mm", "the raw mismatch remains visible")
    contains(r.out, "MOUNT-ANCHOR", "the evidence-backed anchor is named")
    contains(r.out, "our 1 -> JLC 1 at 0deg", "the exact datum is reported")

    old_shift = math.hypot(1.27, 1.27)
    check(abs(old_shift - 1.796051) < 1e-5,
          "fixture does not reproduce the 1.796 mm centroid drift")
    ms = read_mount(d / "twin" / "twin.kicad_pcb")
    eq(len(ms), 1, "one SMA model mounted")
    check(abs(ms[0]["ox"]) < 1e-6 and abs(ms[0]["oy"]) < 1e-6,
          "unique pad-1 datum should produce model offset (0,0), got "
          "(%+.6f,%+.6f)" % (ms[0]["ox"], ms[0]["oy"]))


if __name__ == "__main__":
    sys.exit(main())
