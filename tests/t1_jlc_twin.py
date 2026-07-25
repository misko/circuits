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


if __name__ == "__main__":
    sys.exit(main())
