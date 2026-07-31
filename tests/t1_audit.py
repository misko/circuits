#!/usr/bin/env python3
"""T1: the board checkers — audit_template, audit_board, policy_audit,
board_netlist_parity.

These are the gates that decide whether a board ships, so each one gets a
KNOWN-BAD fixture built by breaking a known-good board in exactly ONE way.
Two of these gates could not fail before this suite existed:

  * audit_template I6 was bounding-BOX and warn-only, so a genuine
    courtyard overlap printed "AUDIT: PASS". I6c now fails on real
    courtyard polygon intersection.
  * jlc_twin's fetch classifier (see t1_jlc_twin.py) defaulted to NO-CAD.
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FIXTURES, KPY, ROOT, SCRIPTS, check, contains,  # noqa: E402
                     edit_board, eq, main, must_fail, must_pass,
                     not_contains, project_copy, run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
AUDIT_T = SCRIPTS / "audit_template.py"
POLICY = SCRIPTS / "policy_audit.py"
PARITY = SCRIPTS / "board_netlist_parity.py"
LC = ROOT / "archived_projects" / "cook-loadcell"
SEALED_LC = LC / "04_kicad" / "cook_loadcell.kicad_pcb"

AUDIT_CFG = {
    "frame": [20.0, 20.0, 55.0, 45.0],
    "edge_margin": 0.3,
    "screw_head_r": 3.2,
    "fab_floor": 0.10,
    "float_ok_numbers": ["MP", "S1"],
}


def fresh_board(d=None):
    """A known-GOOD board straight from the generic generator."""
    d = d or tmpdir("aud_")
    out = d / "cook_loadcell.kicad_pcb"
    must_pass(run([KPY, GEN, LC / "03_src" / "floorplan.yaml", "-o", out], cwd=LC),
              "generate board fixture")
    return d, out


def with_audit_cfg(d, **over):
    cfg = dict(AUDIT_CFG)
    cfg.update(over)
    p = d / "audit.json"
    p.write_text(json.dumps(cfg))
    return p


# ------------------------------------------------------------ clean cases
@test("audit_template PASSes a clean generated board")
def t_audit_clean():
    d, b = fresh_board()
    cfg = with_audit_cfg(d)
    r = must_pass(run([KPY, AUDIT_T, b, "--config", cfg]), "audit_template clean")
    contains(r.out, "AUDIT: PASS", "audit output")


@test("audit_board (cook-loadcell) PASSes a clean generated board")
def t_audit_board_clean():
    d, b = fresh_board()
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    r = must_pass(run([KPY, "03_src/audit_board.py"], cwd=proj), "audit_board clean")
    contains(r.out, "AUDIT PASS", "audit_board output")


@test("board_netlist_parity PASSes identical boards")
def t_parity_clean():
    d, b = fresh_board()
    r = must_pass(run([KPY, PARITY, b, SEALED_LC]), "parity clean")
    contains(r.out, "BOARD PARITY 0 -> PASS", "parity output")
    # G-INPUT/G-COVER (2026-07-27): the verdict must name BOTH boards and carry
    # its denominator, so a reader can tell a sealed board from a 06_build
    # reconstruction (canon M-SHIP) and can see how much was compared.
    contains(r.out, "input: built", "names the built board it graded")
    contains(r.out, "input: sealed", "names the sealed board it graded")
    contains(r.out, "nodes identical", "carries an N/M node denominator")


@test("board_netlist_parity FAILS two EMPTY boards rather than calling them "
      "identical", kind="known_bad")
def t_parity_zero_denominator():
    """G-COVER. Two boards with no netted pads agree perfectly, and the gate
    printed `BOARD PARITY 0 -> PASS (0 nodes identical, net-for-net)` and
    exited 0 — a parity proof over nothing, which is the `jlc_twin` exit-0
    shape. A zero denominator is a FAIL (canon M-COVER).
    RED-VERIFIED against pre-fix code (git show 5054b07:...board_netlist_parity
    .py): it exits 0 on this fixture."""
    d = tmpdir("parzero_")
    empty = d / "empty.kicad_pcb"
    empty.write_text('(kicad_pcb (version 20240108) (generator "test")\n'
                     '  (general (thickness 1.6))\n'
                     '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal))\n)\n')
    r = must_fail(run([KPY, PARITY, empty, empty]),
                  "board_netlist_parity on two empty boards", "0/0 nodes")
    contains(r.out, "M-COVER", "cites the canon it is enforcing")


# --------------------------------------------------------- known-bad cases
@test("audit_template FAILS on a courtyard overlap", kind="known_bad")
def t_courtyard_overlap():
    """Park C3 exactly on top of U1. Their courtyards now intersect, which
    means the two parts physically cannot both be assembled. Before I6c,
    this printed AUDIT: PASS — I6 was bbox-based AND warn-only."""
    d, b = fresh_board()
    edit_board(b, "u=b.FindFootprintByReference('U1')\n"
                  "c=b.FindFootprintByReference('C3')\n"
                  "c.SetPosition(u.GetPosition())")
    cfg = with_audit_cfg(d)
    r = run([KPY, AUDIT_T, b, "--config", cfg])
    must_fail(r, "audit_template on a courtyard overlap", "I6c courtyard-overlap")
    contains(r.out, "AUDIT: FAIL", "audit verdict")


@test("audit_template FAILS when refdes are on F.Fab only", kind="known_bad")
def t_fab_only_refdes():
    """A board whose references print nowhere on the physical board. It
    still routes, still passes DRC, and is undebuggable on the bench."""
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "for f in b.GetFootprints():\n"
                  "    f.Reference().SetLayer(pcbnew.F_Fab)")
    cfg = with_audit_cfg(d)
    r = run([KPY, AUDIT_T, b, "--config", cfg])
    must_fail(r, "audit_template on F.Fab-only refdes", "I8 refdes-not-on-silk")


@test("audit_template FAILS when a pad sits outside the board outline",
      kind="known_bad")
def t_pad_offboard():
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "f=b.FindFootprintByReference('R7')\n"
                  "f.SetPosition(pcbnew.VECTOR2I_MM(19.0, 42.0))")
    cfg = with_audit_cfg(d)
    r = run([KPY, AUDIT_T, b, "--config", cfg])
    must_fail(r, "audit_template on an off-board pad")
    check("I1" in r.out or "I2" in r.out,
          f"expected an I1/I2 frame failure, got:\n{r.out[-1500:]}")


@test("audit_board FAILS when a GND pour is deleted", kind="known_bad")
def t_audit_board_missing_pour():
    """cook-loadcell's IZ gate: both GND pours must exist. Delete one."""
    d, b = fresh_board()
    edit_board(b, "zs=[z for z in b.Zones() if z.GetNetname()=='GND']\n"
                  "b.Remove(zs[0])")
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    r = run([KPY, "03_src/audit_board.py"], cwd=proj)
    must_fail(r, "audit_board with one GND pour", "IZ")


@test("audit_board FAILS when a decoupler drifts away from its IC",
      kind="known_bad")
def t_audit_board_decoupler():
    """The IP proximity gate — C3 must stay within 8mm of U1. Push it to
    the far corner: still connected, still DRC-clean, electrically worse."""
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "b.FindFootprintByReference('C3')"
                  ".SetPosition(pcbnew.VECTOR2I_MM(70.0, 60.0))")
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    r = run([KPY, "03_src/audit_board.py"], cwd=proj)
    must_fail(r, "audit_board with a stranded decoupler", "IP")


@test("board_netlist_parity FAILS when a net is renamed", kind="known_bad")
def t_parity_renamed_net():
    """The gate exists to prove the built board is ELECTRICALLY identical.
    Rename one named net and it must notice."""
    d, b = fresh_board()
    edit_board(b, "n=b.FindNet('S_PLUS')\nn.SetNetname('S_PLUSX')")
    r = run([KPY, PARITY, b, SEALED_LC])
    must_fail(r, "parity with a renamed net", "NET MISMATCH")


@test("board_netlist_parity FAILS when a part is missing", kind="known_bad")
def t_parity_missing_part():
    d, b = fresh_board()
    edit_board(b, "b.Remove(b.FindFootprintByReference('C6'))")
    r = run([KPY, PARITY, b, SEALED_LC])
    must_fail(r, "parity with a deleted part", "ONLY in sealed")


# ------------------------------------------- I-HW mounting-hardware isolation
# cooksense's per-board gate: the metal fastener stack (M2.5 pan head + DIN125
# washer + nut) in each mounting hole is a floating 3.0mm-radius conductive
# disc; its creepage approaches to keypad copper (a) and SELV copper (s) —
# pads + FILLED pours, path measured AROUND outline cutouts — must satisfy
# a+s >= 6.0mm per hole (bonded collapse: the free approach alone).
# TEETH PROVEN 2026-07-25: with the pre-I-HW audit_board.py (git HEAD of that
# day) swapped back in, all three tests below FAIL (--ihw is unknown to the old
# script, which then audits the live board and exits 0); restored, all pass.
CS = ROOT / "projects" / "smc0985-cooksense"
CS_AUDIT = CS / "03_src" / "cooksense" / "audit_board.py"
# The historical defect board: cooksense v1.3 generator output at 3f781da,
# BEFORE the H4 isolation notch landed (95db1d2). Same placement, no notch —
# extracted READ-ONLY from git history so this fixture cannot drift.
PRENOTCH_COMMIT = "3f781da"
PRENOTCH_PATH = "projects/smc0985-cooksense/04_kicad/cooksense.kicad_pcb"


def prenotch_board():
    import subprocess
    d = tmpdir("ihw_hist_")
    out = d / "cooksense_prenotch.kicad_pcb"
    cp = subprocess.run(["git", "show", f"{PRENOTCH_COMMIT}:{PRENOTCH_PATH}"],
                        cwd=ROOT, capture_output=True)
    check(cp.returncode == 0 and len(cp.stdout) > 100000,
          f"git show of the pre-notch board failed: {cp.stderr[:200]}")
    out.write_bytes(cp.stdout)
    return d, out


@test("I-HW (cooksense) PASSes the live board, reporting per-hole margins")
def t_ihw_clean():
    """The live board carries the H4 notch (95db1d2): H4's straight-line
    keypad approach is only 4.031mm, but the surface path around the
    edge-reaching cutout measures 6.598mm — the PASS depends on the checker
    walking AROUND outline voids, so this also pins the geodesic. Measured at
    time of writing: H1 a=2.305 s=13.631; H2 a=3.129 s=13.000; H3 a=40.933
    s=-1.450 (GND-bonded); H4 a=6.598 s=-1.450 (GND-bonded)."""
    r = must_pass(run([KPY, CS_AUDIT, "--ihw"]), "I-HW on the live board")
    contains(r.out, "I-HW PASS", "I-HW verdict")
    for h in ("H1", "H2", "H3", "H4"):
        contains(r.out, f"I-HW {h} a=", f"per-hole margin line for {h}")
    # H4 must pass VIA the notch: its measured approach sits between the
    # straight-line 4.031 (blind checker) and 8.5 — assert the property,
    # not the byte-exact figure
    import re
    m = re.search(r"I-HW H4 a=([\d.]+)mm", r.out)
    check(m and 6.0 <= float(m.group(1)) <= 8.5,
          f"H4 keypad approach should be the ~6.6mm around-the-notch path: "
          f"{m.group(0) if m else r.out[-800:]}")


@test("I-HW measures TRACK copper around outline voids, not straight through "
      "them")
def t_ihw_track_geodesic():
    """RED-VERIFIED against a real false-FAIL on the first fully ROUTED v1.3
    board (task#21, 2026-07-26).

    I-HW handed PAD copper to the visibility-graph geodesic and TRACK copper to
    a straight-line distance, commented "straight fallback, conservative". It is
    not conservative, it is the exact metric this check was built to reject: the
    commit that landed I-HW records that a straight line measures the pre-notch
    and notched boards IDENTICALLY at H4 and therefore "cannot see the notch at
    all, and would have failed the very board the notch fixes". The board was
    track-free when the pad path was written, so nothing exercised the track
    path until the route landed. Then:

        I-HW H4 a=4.617mm (track RSTOP_MID) -> 4.617 < 6.000 FAIL

    MEASURED on that board, same track (F.Cu (198.600,44.400) ->
    (197.400,45.600), the K_STOP.3 escape), same 3.0mm disc:
        straight-line disc-edge gap      4.617 mm
        SURFACE PATH around the notch    7.165 mm
    The straight line crosses the H4 isolation notch (y[48.80,49.80],
    x[191.50,200.10]) at x194.51 and x195.20 — it runs through a through-cut, so
    it was never a creepage path. With the geodesic applied to tracks the
    binding item at H4 goes back to being the PAD at 6.598mm, which is the
    figure ADR-0012 records — an independent confirmation, on routed copper, of
    a number that was measured on a track-free board.

    RED VERIFICATION: with the pre-fix `ihw_measure` (track polygon = None ->
    straight fallback) this test FAILS on the live board, reporting
    `I-HW FAIL` / `H4 a=4.617mm (track RSTOP_MID)`. Restored, it passes.
    t_ihw_prenotch still FAILS at 4.031mm, so the fix did not make the gate
    unfailable — it made it measure the right thing."""
    r = must_pass(run([KPY, CS_AUDIT, "--ihw"]), "I-HW on the live routed board")
    contains(r.out, "I-HW PASS", "I-HW verdict")
    import re
    m = re.search(r"I-HW H4 a=([\d.]+)mm \(([^)]+)\)", r.out)
    check(m, f"H4 line with its binding item: {r.out[-800:]}")
    a, who = float(m.group(1)), m.group(2)
    # the DEFECT signature, named so it cannot come back quietly
    check(abs(a - 4.617) > 0.05,
          f"H4 reported {a}mm — that is the straight-line-through-the-notch "
          f"reading the track branch used to emit; the geodesic must be used "
          f"for tracks too")
    check(a >= 6.0, f"H4 keypad approach must clear 6.000mm: {m.group(0)}")
    # and the binding item is the PAD again, at the ADR-0012 figure
    check("pad K_STOP.3" in who and 6.4 <= a <= 6.8,
          f"expected the K_STOP.3 pad at ~6.598mm to bind H4, got {m.group(0)}")


@test("I-HW FAILS the pre-notch board (3f781da) at H4", kind="known_bad")
def t_ihw_prenotch():
    """RED-VERIFIED against the real defect: the board at 3f781da is the SAME
    placement as the sealed v1.3 state but WITHOUT the H4 isolation notch.
    H4's hardware disc sits in the GND pour (s=-1.400, SELV-bonded), so its
    keypad approach alone must make 6.0mm — measured 4.031mm to K_STOP.3
    (RSTOP_MID), FAIL. The other three holes pass (H1 15.936, H2 16.129,
    H3 40.933) — the checker reacts to exactly the defect the notch fixed,
    not to some unrelated malformation."""
    d, b = prenotch_board()
    r = run([KPY, CS_AUDIT, "--ihw", b])
    must_fail(r, "I-HW on the pre-notch board", "I-HW H4")
    contains(r.out, "I-HW FAIL", "I-HW verdict")
    import re
    m = re.search(r"I-HW H4 a=([\d.]+)mm.*FAIL", r.out)
    check(m and float(m.group(1)) < 6.0,
          f"H4 should fail on a sub-6mm keypad approach: {r.out[-800:]}")


@test("I-HW pairing branch FAILS the live board when the enclosure bonds "
      "the holes", kind="known_bad")
def t_ihw_pairing_bonded_enclosure():
    """ENCLOSURE_BONDS_HOLES=False (non-conductive enclosure, user decision
    2026-07-25) is the ONLY thing standing between this board and a FAIL: a
    conductive chassis plate joins all fasteners into one conductor, so the
    worst approaches across DIFFERENT holes pair up — min_a (H1, 2.305mm) with
    min_s (H3/H4 GND-bonded, <0) collapses to 2.305mm < 6.0mm. Flip the
    constant in-process and the measured rows of the LIVE board must fail.
    RED-VERIFIED 2026-07-25: measured pairing figure 2.305mm (min_a=2.305,
    min_s=-1.450)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cs_audit", CS_AUDIT)
    ab = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ab)
    import pcbnew
    rows = ab.ihw_measure(pcbnew.LoadBoard(str(CS / "04_kicad" / "cooksense.kicad_pcb")))
    f0, _ = ab.ihw_verdicts(rows)
    check(not f0, f"per-hole branch should pass the live board first: {f0}")
    ab.ENCLOSURE_BONDS_HOLES = True
    fails, _ = ab.ihw_verdicts(rows)
    check(any("PAIRING" in x and "FAIL" in x for x in fails),
          f"bonded-enclosure pairing rule did not FAIL the live board: {fails}")


# ------------------------------------------------------------ policy_audit
@test("policy_audit reports zero FAIL on a good project", slow=True)
def t_policy_clean():
    d, b = fresh_board()
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_sch", proj / "04_kicad")
    for extra in ("01_docs", "07_releases"):
        if (LC / extra).is_dir():
            shutil.copytree(LC / extra, proj / extra, dirs_exist_ok=True)
    for f in ("rebuild_all.sh",):
        if (LC / "03_src" / f).is_file():
            shutil.copy(LC / "03_src" / f, proj / "03_src")
    r = run([KPY, POLICY, proj, "--skip-drc"])
    # policy_audit grades a scratch tree harshly (no git history, no
    # releases), so M-REPRO/M-REL always fail here. Assert on the ONE rule
    # this test is about, read from the report where per-rule grades live.
    md = proj / "06_build" / "policy_audit.md"
    check(md.exists(), f"policy_audit wrote no report\n{r.out[-1500:]}")
    body = md.read_text()
    contains(body, "P-SILK-REF", "policy report")
    row = [l for l in body.splitlines() if "P-SILK-REF" in l]
    check(row and not any("FAIL" in l for l in row),
          f"P-SILK-REF should pass on a silk-labelled board: {row}")
    check("refdes not on silk" not in body,
          "P-SILK-REF flagged a board whose refdes are all on silk")


@test("policy_audit P-SILK-REF FAILS on an F.Fab-only board", kind="known_bad",
      slow=True)
def t_policy_silk_ref():
    d, b = fresh_board()
    edit_board(b, "import pcbnew\n"
                  "for f in b.GetFootprints():\n"
                  "    f.Reference().SetLayer(pcbnew.F_Fab)")
    proj = project_copy("cook-loadcell", d / "proj", board=b)
    shutil.copy(LC / "04_kicad" / "cook_loadcell.kicad_sch", proj / "04_kicad")
    (proj / "06_build" / "refdes_waiver.json").write_text("[]")
    r = run([KPY, POLICY, proj, "--skip-drc"])
    check("P-SILK-REF" in r.out, "P-SILK-REF not evaluated at all")
    md = (proj / "06_build" / "policy_audit.md")
    body = md.read_text() if md.exists() else r.out
    check("refdes not on silk" in body,
          f"P-SILK-REF did not flag the F.Fab-only board:\n{body[-2500:]}")
    check(r.rc != 0, "policy_audit exited 0 on a board with no printed refdes")



# ------------------------------------------------- M9 journal discipline
@test("M-JRNL + M-LEARN pass a journaled, harvested project")
def t_journal_clean():
    d = tmpdir("jrn_")
    (d / "01_docs" / "journal").mkdir(parents=True)
    (d / "01_docs" / "learnings").mkdir()
    (d / "03_src" / "route").mkdir(parents=True)
    (d / "07_releases" / "v1.0-x").mkdir(parents=True)
    (d / "01_docs" / "journal" / "routing.md").write_text(
        "## 2026-07-21 14:00 - iterate 3\n- did: x\n- result: DRC 8->6\n")
    (d / "01_docs" / "learnings" / "routing.md").write_text(
        "## via cluster\n- root cause: x\n- candidate-canon: yes\n")
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    check("| M-JRNL | PASS" in md, f"M-JRNL not PASS:\n{md}")
    check("| M-LEARN | PASS" in md, f"M-LEARN not PASS:\n{md}")


@test("M-JRNL FAILS a project generating artifacts with an empty journal",
      kind="known_bad")
def t_journal_missing():
    # the knowledge-evaporation incident: analysis lived only in the chat
    d = tmpdir("jrn_")
    (d / "01_docs").mkdir()
    (d / "03_src" / "route").mkdir(parents=True)
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    check("| M-JRNL | FAIL" in md, f"M-JRNL did not FAIL:\n{md}")


# ------------------------------------------------- M-REL release discovery
def _per_board_release(d, git_ok=True):
    """A scratch git project whose ONLY release dir uses the ADR-0007
    per-board name form '<board>-v1.0-<date>' (cooksense-v1.0-2026-07-23)."""
    import subprocess
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    (d / "seed.txt").write_text("x\n")
    env_git = ["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(env_git + ["add", "-A"], check=True)
    subprocess.run(env_git + ["commit", "-qm", "seed"], check=True)
    sha = subprocess.run(env_git[:3] + ["rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    rel = d / "07_releases" / "scratchboard-v1.0-2026-07-23"
    (rel / "verification").mkdir(parents=True)
    (rel / "verification" / "drc.json").write_text("{}")
    (rel / "MANIFEST.txt").write_text(
        f"git_sha: {sha if git_ok else 'HEAD@release'}\ngit_dirty: false\n")
    (d / "01_docs").mkdir(exist_ok=True)
    (d / "01_docs" / "CHANGELOG.md").write_text(
        "- scratchboard-v1.0-2026-07-23: first\n")
    return rel


@test("M-REL discovers + grades an ADR-0007 per-board-named release dir")
def t_mrel_per_board_name():
    """Release-dir discovery used a bare 'v*' glob that silently skipped the
    ADR-0007 per-board form '<board>-v1.0-<date>' — M-REL graded N-A
    ('no releases yet') on the cooksense-v1.0-2026-07-23 and
    crow-recorder-central-v2-v1.0-2026-07-23 seals (both real, 2026-07-23).
    RED-VERIFIED: with the pre-fix policy_audit.py swapped back in, this test
    FAILS ('| M-REL | N-A | no releases yet'); restored, it passes."""
    d = tmpdir("mrel_")
    _per_board_release(d, git_ok=True)
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    row = [l for l in md.splitlines() if "M-REL" in l]
    check(row and "no releases yet" not in row[0],
          f"M-REL did not DISCOVER the per-board-named release dir: {row}")
    check("| M-REL | PASS" in md and "scratchboard-v1.0-2026-07-23" in row[0],
          f"M-REL should PASS a well-formed per-board release: {row}")


@test("M-REL still FAILS a per-board-named release with a bad MANIFEST",
      kind="known_bad")
def t_mrel_per_board_bad_manifest():
    """Discovery widened, teeth intact: the same per-board dir with the
    'git_sha: HEAD@release' incident manifest must FAIL, not N-A."""
    d = tmpdir("mrel_")
    _per_board_release(d, git_ok=False)
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    row = [l for l in md.splitlines() if "M-REL" in l]
    check(row and "| M-REL | FAIL" in md,
          f"M-REL did not FAIL the bad manifest in a per-board dir: {row}")
    check("git_sha not an exact commit" in row[0],
          f"M-REL failure did not name the bad git_sha: {row}")


def _two_release_project(d, names, table_layout="path-first"):
    """A scratch git project with TWO release dirs whose names are given, the
    LAST-BY-VERSION one being the live release. Both carry a real sha256 table
    over their own files, written in the requested LAYOUT."""
    import hashlib
    import subprocess
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    (d / "seed.txt").write_text("x\n")
    env_git = ["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(env_git + ["add", "-A"], check=True)
    subprocess.run(env_git + ["commit", "-qm", "seed"], check=True)
    sha = subprocess.run(env_git[:3] + ["rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    (d / "01_docs").mkdir(exist_ok=True)
    (d / "01_docs" / "CHANGELOG.md").write_text(
        "".join(f"- {n}: entry\n" for n in names))
    for i, n in enumerate(names):
        rel = d / "07_releases" / n
        (rel / "verification").mkdir(parents=True)
        (rel / "verification" / "drc.json").write_text('{"v": %d}' % i)
        if i < len(names) - 1:
            (rel / "SUPERSEDED.md").write_text(f"superseded by {names[-1]}\n")
        files = sorted(p.relative_to(rel).as_posix() for p in rel.rglob("*")
                       if p.is_file() and p.name != "MANIFEST.txt")
        rows = []
        for f in files:
            h = hashlib.sha256((rel / f).read_bytes()).hexdigest()
            rows.append(f"{h}  {f}" if table_layout == "hash-first"
                        else f"  {f}  {h}")
        (rel / "MANIFEST.txt").write_text(
            f"git_sha: {sha}\ngit_dirty: false\nsha256:\n"
            + "\n".join(rows) + "\n")
    return d


@test("M-REL sorts releases NUMERICALLY: v1.10 is newer than v1.9")
def t_mrel_double_digit_minor():
    """MEASURED 2026-07-27, on the first release in this fleet to reach a
    double-digit minor. `sorted()` over the DIRECTORY NAME puts `v1.10-…`
    BEFORE `v1.9-…`, because '1' < '9' as a character. M-REL then graded the
    WRONG release's MANIFEST and demanded a `SUPERSEDED.md` on the NEWEST
    directory — usb-hub-3s-v3 v1.10 could not seal, and the message accused the
    live release of being superseded. `_version_key` is now imported from the
    jlcpcb-fab freshness gate, which already sorted numerically, so the two
    cannot disagree about which release is latest.

    RED-VERIFIED 2026-07-27: with the pre-fix `sorted(...)` restored, this test
    reports `v1.10-2026-07-27 lacks SUPERSEDED.md`."""
    d = tmpdir("mrel10_")
    _two_release_project(d, ["v1.9-2026-07-27", "v1.10-2026-07-27"])
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    row = [l for l in md.splitlines() if "M-REL" in l]
    check(row, "no M-REL row at all")
    not_contains(row[0], "v1.10-2026-07-27 lacks SUPERSEDED.md",
                 "M-REL treated the NEWEST release as superseded — the "
                 "release list is being sorted as text, so v1.10 < v1.9")
    contains(row[0], "v1.10-2026-07-27",
             "M-REL graded the wrong release: the latest is v1.10")


@test("M-REL reads a sha256sum-ORDER table too, and an unreadable table is a "
      "FAIL rather than a silent zero", kind="known_bad")
def t_mrel_hash_first_table():
    """A GATE THAT VERIFIED NOTHING AND SAID HASHES VERIFY. The fleet ships two
    MANIFEST table layouts — `'  '<path>  <hash>` on three boards and sha256sum
    order `<hash>  <path>` on usb-hub-3s-v3 — and the matcher required the
    first. MEASURED 2026-07-27 over the four live releases: 66 / 80 / 57
    entries matched, and **0 of usb-hub-3s-v3's 76**. M-REL reported
    "provenance + hashes verify" on that board across all ten of its releases
    while checking not one file.

    Both halves are asserted: the hash-first layout must be READ (a corrupted
    file under it must FAIL), and a table that yields ZERO entries against a
    non-empty directory must FAIL in its own right — a denominator that
    silently goes to zero is the M-COVER shape this repo keeps paying for.

    RED-VERIFIED 2026-07-27: with the pre-fix single-layout regex restored, the
    corrupted hash-first release PASSES M-REL."""
    d = tmpdir("mrelhf_")
    _two_release_project(d, ["v1.0-2026-07-27", "v1.1-2026-07-27"],
                         table_layout="hash-first")
    latest = d / "07_releases" / "v1.1-2026-07-27"
    (latest / "verification" / "drc.json").write_text('{"TAMPERED": true}')
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    row = [l for l in md.splitlines() if "M-REL" in l]
    check(row and "| M-REL | FAIL" in md,
          f"M-REL did not FAIL a TAMPERED file in a sha256sum-order table — "
          f"it is not reading that layout at all: {row}")
    contains(row[0], "sha256 mismatch", "and must say which check bit")

    e = tmpdir("mrelempty_")
    _two_release_project(e, ["v1.0-2026-07-27", "v1.1-2026-07-27"])
    bad = e / "07_releases" / "v1.1-2026-07-27" / "MANIFEST.txt"
    bad.write_text(bad.read_text().split("sha256:")[0] + "sha256:\n")
    run([KPY, POLICY, e, "--skip-drc"])
    md2 = (e / "06_build" / "policy_audit.md").read_text()
    row2 = [l for l in md2.splitlines() if "M-REL" in l]
    check(row2 and "| M-REL | FAIL" in md2,
          f"an EMPTY sha256 table passed M-REL: {row2}")
    contains(row2[0], "ZERO readable entries",
             "the empty-table failure must name itself")


# ------------------------------- M-REL release scope: WHICH BOARD (2026-07-27)
#: a minimal but genuinely pcbnew-loadable board, so a scratch multi-board
#: project reaches the release checks instead of dying in LoadBoard.
_MINI_PCB = """(kicad_pcb (version 20221018) (generator test)
  (general (thickness 1.6))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (44 "Edge.Cuts" user)
  )
  (setup)
)
"""


def _multi_board_project(d, boards, names, superseded=()):
    """A scratch git project that BUILDS several boards and holds several
    release series — the smc0985-cooksense shape. Each release carries a real
    sha256 table over its own files; `superseded` names the dirs that get a
    SUPERSEDED.md, so the fixture can state exactly which ones should be
    demanded."""
    import hashlib
    import subprocess
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    (d / "seed.txt").write_text("x\n")
    env_git = ["git", "-C", str(d), "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(env_git + ["add", "-A"], check=True)
    subprocess.run(env_git + ["commit", "-qm", "seed"], check=True)
    sha = subprocess.run(env_git[:3] + ["rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    (d / "04_kicad").mkdir(exist_ok=True)
    for b in boards:
        (d / "04_kicad" / f"{b}.kicad_pcb").write_text(_MINI_PCB)
    (d / "01_docs").mkdir(exist_ok=True)
    (d / "01_docs" / "CHANGELOG.md").write_text(
        "".join(f"- {n}: entry\n" for n in names))
    for i, n in enumerate(names):
        rel = d / "07_releases" / n
        (rel / "verification").mkdir(parents=True)
        (rel / "verification" / "drc.json").write_text('{"v": %d}' % i)
        if n in superseded:
            (rel / "SUPERSEDED.md").write_text("superseded\n")
        files = sorted(p.relative_to(rel).as_posix() for p in rel.rglob("*")
                       if p.is_file() and p.name != "MANIFEST.txt")
        rows = [f"  {f}  {hashlib.sha256((rel / f).read_bytes()).hexdigest()}"
                for f in files]
        (rel / "MANIFEST.txt").write_text(
            f"git_sha: {sha}\ngit_dirty: false\nsha256:\n"
            + "\n".join(rows) + "\n")
    return d


#: the cooksense shape: two boards, one 07_releases/, and the board that sorts
#: SECOND owns the release that sorts LAST.
_COOK_SHAPE_BOARDS = ["cooksense", "interposer"]
_COOK_SHAPE_RELS = ["cooksense-v1.0-2026-07-23", "cooksense-v1.1-2026-07-24",
                    "cooksense-v1.4-2026-07-26", "interposer-v1.0-2026-07-24"]


@test("M-REL scopes the release series to the BOARD under audit, not to the "
      "last directory in 07_releases", kind="known_bad")
def t_mrel_scopes_to_the_board_under_audit():
    """MEASURED 2026-07-27 on smc0985-cooksense, which builds TWO boards and
    holds both series in one 07_releases/::

        cooksense-v1.0 … cooksense-v1.4   interposer-v1.0

    `rels[-1]` returned the INTERPOSER — the board prefix is the leading
    component of the sort key, so `interposer-…` lands last — while
    `boards[0]` gave policy_audit `cooksense.kicad_pcb` to grade. M-REL,
    M-BOM, A-POP and A-BODY all reported on the wrong archive, and
    `rels[:-1]` demanded SUPERSEDED.md on cooksense-v1.4, the LIVE cooksense
    release, which blocked a v1.5 seal. "The last directory" is a property
    ADJACENT to "this board's latest release".

    This fixture reproduces that shape and asserts BOTH halves: the release
    named in the M-REL row is cooksense's, and the live cooksense release is
    not accused of being superseded.

    RED-VERIFIED 2026-07-27 by restoring the pre-fix selector in
    policy_audit.py (`rels = sorted(07_releases/*, key=(_version_key, name))`
    with `latest = rels[-1]` and the SUPERSEDED loop over `rels[:-1]`) and
    re-running `--only=M-REL`: **4 passed, 2 failed** (this test and
    t_mrel_unattributable_release_set_fails; the four pre-existing M-REL tests
    still pass, so the neuter is scoped to the property under test). The
    measured failure line on this fixture is

        | M-REL | FAIL | cooksense-v1.4-2026-07-26 lacks SUPERSEDED.md |

    — the blocked seal, reproduced. Restored byte-identical afterwards
    (md5 bb8d0ef5879407945119efbbfdf614e4); the suite returns to green.
    """
    d = tmpdir("mrelboard_")
    _multi_board_project(d, _COOK_SHAPE_BOARDS, _COOK_SHAPE_RELS,
                         superseded=["cooksense-v1.0-2026-07-23",
                                     "cooksense-v1.1-2026-07-24"])
    run([KPY, POLICY, d, "--skip-drc", "--board", "cooksense"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    contains(md, "Board graded: cooksense",
             "the report must NAME the board it graded")
    row = [l for l in md.splitlines() if "| M-REL |" in l]
    check(row, f"no M-REL row at all:\n{md}")
    contains(row[0], "cooksense-v1.4-2026-07-26",
             "M-REL graded the wrong release: cooksense's latest is v1.4")
    not_contains(row[0], "interposer",
                 "M-REL reached into the SIBLING BOARD's release series")
    not_contains(row[0], "cooksense-v1.4-2026-07-26 lacks SUPERSEDED.md",
                 "M-REL accused the LIVE cooksense release of being "
                 "superseded — this is what blocked the v1.5 seal")
    check("| M-REL | PASS" in md, f"M-REL should PASS this project:\n{row}")
    # A-POP/A-BODY/M-BOM take their target from the same resolution
    contains(md, "cooksense-v1.4-2026-07-26",
             "the release-scoped rows must name cooksense's archive")

    # the mirror: --board interposer grades the OTHER series, not 'the last dir'
    run([KPY, POLICY, d, "--skip-drc", "--board", "interposer"])
    md2 = (d / "06_build" / "policy_audit.md").read_text()
    row2 = [l for l in md2.splitlines() if "| M-REL |" in l]
    contains(row2[0], "interposer-v1.0-2026-07-24", "interposer's own release")
    not_contains(row2[0], "cooksense-v1.4", "and not the sibling's")


@test("M-REL FAILS an UNATTRIBUTABLE release set instead of picking one",
      kind="known_bad")
def t_mrel_unattributable_release_set_fails():
    """canon M-COVER: input a gate cannot parse is a FAIL, never a skip, and
    never a silent pick. Two shapes, both refused by name:

      * a release dir naming a board the project does not build;
      * a BARE `v1.0-<date>` in a project that builds two boards — it names no
        board and more than one is possible.

    RED-VERIFIED 2026-07-27 with the pre-fix `rels[-1]` selector restored
    (same swap as the test above; `--only=M-REL` -> 4 passed, 2 failed).
    MEASURED pre-fix rows:

      ghost: `| M-REL | FAIL | boarda-v1.0-2026-01-01 lacks SUPERSEDED.md |`
             — it graded `ghost-v1.0-…` (the last directory, for a board this
             project does not build) and on that basis accused the project's
             only real release of being superseded. A wrong answer stated
             confidently, which is worse than a skip.
      bare:  `| M-REL | PASS | v1.0-2026-01-01: provenance + hashes verify |`
             — a green verdict over a release it could not attribute at all.

    Both dependent gates were equally blind pre-fix: M-BOM `N-A`, A-BODY
    `N-A`, A-POP failing for an unrelated reason.
    """
    d = tmpdir("mrelghost_")
    _multi_board_project(d, ["boarda"],
                         ["boarda-v1.0-2026-01-01", "ghost-v1.0-2026-01-02"])
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    row = [l for l in md.splitlines() if "| M-REL |" in l]
    check(row and "| M-REL | FAIL" in md,
          f"M-REL did not FAIL an unattributable release set: {row}")
    contains(row[0], "ghost", "the failure must NAME the stray directory")
    # every gate that takes its target from the same resolution must say so —
    # not fall through to 06_build as though nothing were wrong
    for cid in ("M-BOM", "A-POP", "A-BODY"):
        r = [l for l in md.splitlines() if f"| {cid} |" in l]
        check(r and f"| {cid} | FAIL" in md,
              f"{cid} kept grading something while the release set was "
              f"unresolvable: {r}")
        contains(r[0], "ghost",
                 f"{cid} failed without naming WHY the release set is "
                 f"unresolvable")

    e = tmpdir("mrelbare_")
    _multi_board_project(e, ["boarda", "boardb"], ["v1.0-2026-01-01"])
    run([KPY, POLICY, e, "--skip-drc"])
    md2 = (e / "06_build" / "policy_audit.md").read_text()
    row2 = [l for l in md2.splitlines() if "| M-REL |" in l]
    check(row2 and "| M-REL | FAIL" in md2,
          f"a bare release name in a 2-board project passed M-REL: {row2}")
    contains(row2[0], "NO board", "the failure must say what is missing")


@test("M-LEARN FAILS a release with no stage learnings", kind="known_bad")
def t_learnings_missing():
    d = tmpdir("jrn_")
    (d / "01_docs" / "journal").mkdir(parents=True)
    (d / "01_docs" / "journal" / "routing.md").write_text("## e\n- did: x\n")
    (d / "03_src" / "route").mkdir(parents=True)
    (d / "07_releases" / "v1.0-x").mkdir(parents=True)
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    check("| M-LEARN | FAIL" in md, f"M-LEARN did not FAIL:\n{md}")


# --------------------------------- policy_audit REPORT INTEGRITY (M-CONS)
# crow-mic-pod-v2 v1.0 sealed a policy_audit.md whose own Summary could not be
# derived from its own table: a 51-byte splice at offset 387 replaced the
# P-TIER row's middle with the run's stdout summary line and orphaned its tail
# on the next line. Measured grades in the table PASS=22; the file's Summary
# and the release MANIFEST both said PASS=23. The MANIFEST hash VERIFIED — the
# file was generated corrupt and then faithfully hashed, so every integrity
# check downstream of generation certified the corruption.
#
# Mechanism (measured 2026-07-25): the report path was also the process's
# redirected stdout. `import pcbnew` writes to that fd at C level, advancing
# the SHARED offset to 387; write_text() wrote the report from offset 0
# through its own fd; at interpreter exit Python's buffered stdout flushed its
# summary line at 387, into the finished file.
def _policy_fns():
    """The pure report helpers, without importing pcbnew."""
    src = POLICY.read_text()
    ns = {"re": __import__("re")}
    exec(src[src.index("def cell("):src.index("def main()")], ns)
    return ns


CORRUPT = (ROOT / "projects/crow-mic-pod-v2/07_releases"
           / "crow-mic-pod-v2-v1.0-2026-07-23/verification/policy_audit.md")


@test("policy_audit's report check re-derives grades FROM THE WRITTEN TABLE, "
      "and goes RED on the sealed crow-mic-pod-v2 v1.0 corruption",
      kind="known_bad")
def t_kb_policy_report_corrupt():
    """The known-bad fixture is a real sealed artifact, read-only. This is the
    strongest form available: the bytes that shipped GREEN must now go RED.

    It also pins the numbers, so a future 'fix' that merely silences the
    check has to change them: 37 rows recoverable, PASS=22 from the table
    against the PASS=23 the run believed it had graded."""
    fns = _policy_fns()
    check(CORRUPT.is_file(), f"sealed fixture missing: {CORRUPT}")
    text = CORRUPT.read_text()
    rows, stated = fns["parse_report"](text)
    got = {}
    for _cid, g in rows:
        got[g] = got.get(g, 0) + 1
    check(len(rows) == 37, f"expected 37 recoverable rows, got {len(rows)}")
    check(got.get("PASS") == 22, f"expected PASS=22 in the table, got {got}")
    check(stated.get("PASS") == 23,
          f"expected the file's own Summary to claim PASS=23, got {stated}")
    # what the run that wrote it believed it had graded
    claimed = {"HUMAN": 7, "N-A": 7, "PASS": 23, "WAIVED": 1}
    bad = fns["report_inconsistencies"](text, 38, claimed)
    check(bad, "report_inconsistencies MISSED the sealed corruption — the "
               "gate cannot fail and is worthless")
    check(any("37" in b and "38" in b for b in bad),
          f"the finding should name the row shortfall: {bad}")
    check(any("22" in b for b in bad),
          f"the finding should name the grades counted from the table: {bad}")


@test("policy_audit's report check PASSES a well-formed report")
def t_policy_report_clean():
    fns = _policy_fns()
    rows = [("S-ERC", "PASS"), ("R-DRC", "PASS"), ("M1", "HUMAN"),
            ("S-OCCL", "WAIVED"), ("R-LEN", "N-A")]
    counts = {}
    for _c, g in rows:
        counts[g] = counts.get(g, 0) + 1
    body = ["| ID | Grade | Detail |", "|---|---|---|"]
    body += [f"| {c} | {g} | detail |" for c, g in rows]
    body += ["", "Summary: " + ", ".join(f"{k}={v}"
                                         for k, v in sorted(counts.items()))]
    eq(fns["report_inconsistencies"]("\n".join(body) + "\n", len(rows), counts),
       [], "a well-formed report must produce no findings")


@test("policy_audit's report check FAILS when the Summary disagrees with the "
      "table it sits under", kind="known_bad")
def t_kb_policy_summary_drift():
    """The independent half: even an UNCORRUPTED table whose headline was
    computed from something other than the rows must be caught. The old
    writer derived the Summary from the same in-memory counter that produced
    the rows, so it could only ever agree with itself."""
    fns = _policy_fns()
    text = ("| ID | Grade | Detail |\n|---|---|---|\n"
            "| S-ERC | PASS | ok |\n| R-DRC | PASS | ok |\n"
            "\nSummary: PASS=3\n")
    bad = fns["report_inconsistencies"](text, 2, {"PASS": 2})
    check(bad, "a Summary claiming PASS=3 over a 2-row PASS table must FAIL")
    check(any("Summary" in b for b in bad), f"finding should name it: {bad}")


@test("a detail string containing a newline or a pipe cannot reshape the "
      "table it is reported in", kind="known_bad")
def t_kb_policy_cell_escaping():
    """The corruption arrived by a different route, but the same file format
    has a second way to lose a row: an unescaped '|' invents a column and a
    newline splits the row. `cell()` neutralises both, and the read-back
    proves it — a checker whose own output format can be broken by the text
    it reports is not a checker."""
    fns = _policy_fns()
    nasty = "widths differ | 0.25mm vs\n0.2498mm"
    rows = [("A-FIRE", "FAIL", nasty), ("R-DRC", "PASS", "0/0/0")]
    counts = {"FAIL": 1, "PASS": 1}
    lines = ["| ID | Grade | Detail |", "|---|---|---|"]
    lines += [f"| {c} | {g} | {fns['cell'](d)} |" for c, g, d in rows]
    lines += ["", "Summary: FAIL=1, PASS=1"]
    eq(fns["report_inconsistencies"]("\n".join(lines) + "\n", 2, counts), [],
       "escaped cells must round-trip")
    # RED-VERIFY: without cell(), the same details lose a row
    raw = ["| ID | Grade | Detail |", "|---|---|---|"]
    raw += [f"| {c} | {g} | {d} |" for c, g, d in rows]
    raw += ["", "Summary: FAIL=1, PASS=1"]
    check(fns["report_inconsistencies"]("\n".join(raw) + "\n", 2, counts),
          "unescaped, the newline must break the table and be CAUGHT — if "
          "this passes, cell() is not what is doing the work")



# ---------------------------------------------------------------- M-BOM pair
def _bom_pair_project(d, cand_dirname="fab_v22", cand_code="C111", sealed_code="C999"):
    """A project carrying BOTH a sealed release BOM and a candidate build BOM,
    which disagree. Source matches the CANDIDATE — the normal shape the moment
    work starts on the next revision."""
    rel = _per_board_release(d)
    (rel / "fab").mkdir(parents=True, exist_ok=True)
    (rel / "fab" / "bom.csv").write_text(
        "Comment,Designator,Footprint,MPN,LCSC\n"
        f"74LVC1G00,U1,SOIC-8,SN74LVC1G00,{sealed_code}\n")
    cand = d / "06_build" / cand_dirname
    cand.mkdir(parents=True, exist_ok=True)
    (cand / "bom_jlc.csv").write_text(
        "Comment,Designator,Footprint,MPN,LCSC\n"
        f"74LVC1G00,U1,SOIC-8,SN74LVC1G00,{cand_code}\n")
    cj = d / "03_tscircuit" / "build"
    cj.mkdir(parents=True, exist_ok=True)
    (cj / "circuit.json").write_text(json.dumps(
        [{"type": "source_component", "name": "U1",
          "supplier_part_numbers": {"jlcpcb": [cand_code]}}]))
    return d


def _mbom_row(d):
    """The row from the WRITTEN REPORT. policy_audit prints a summary to stdout
    and writes the graded table to 06_build/policy_audit.md; reading stdout
    returns an empty row and a fixture that asserts on "" passes vacuously."""
    run([KPY, POLICY, str(d)])
    md = Path(d) / "06_build" / "policy_audit.md"
    check(md.exists(), f"policy_audit wrote no report at {md}")
    for line in md.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("| M-BOM "):
            return line
    check(False, f"no M-BOM row in {md} — a fixture asserting on an empty "
                 f"row would pass vacuously, which is the defect class this "
                 f"very test exists for")
    return ""


@test("M-BOM grades the CANDIDATE build BOM against CURRENT source, not the "
      "previous SEALED release — the pair must be contemporaneous",
      kind="known_bad")
def t_mbom_grades_the_contemporaneous_pair():
    """MEASURED ON cooksense 2026-07-29, after the prediction had been made and
    not demonstrated FOUR times. M-BOM preferred `latest_sealed/fab/bom.csv` and
    graded it against the LIVE `03_tscircuit/build/circuit.json`. Those are two
    different revisions the moment the next one starts, so the gate asked a
    question with no correct answer: it reported **11 BOM-vs-source defects**
    that were only v1.6's sealed BOM differing from v1.7's source, while
    `bom_source_check` run DIRECTLY on the v1.7 artifact returned `PASS (every
    BOM LCSC == source)` with 28/28 R/C rows value-graded.

    So M-BOM could not clear PRE-SEAL BY CONSTRUCTION — the latest seal is
    always the previous revision — which is exactly why four sessions predicted
    it would "clear at the seal" and none showed it.

    This is the F-LEGIBLE defect in a second gate (canon M-SHIP), and F-LEGIBLE
    had been fixed HOURS EARLIER the same day. The class was not swept, so this
    instance survived: fixing one member of a class and not counting the rest is
    the recurring failure this repo keeps paying for.

    RED-VERIFIED: with the pre-fix candidate list restored (sealed release
    first, `06_build/fab/` only), this fixture reports
    `1 BOM-vs-source defect(s)` naming C999 against a source that says C111."""
    d = _bom_pair_project(tmpdir("mbom_"))
    line = _mbom_row(d)
    check("| PASS |" in line,
          f"M-BOM must grade the candidate, which MATCHES source:\n{line}")
    check("fab_v22" in line,
          f"and must NAME the artifact it graded, so a reader can check it:\n{line}")
    # the sealed release is not silently ignored — the row says WHY it was not
    # the target, so a reader is never left guessing which artifact was graded.
    check("not contemporaneous" in line.lower(),
          f"the row must say WHY the seal was not graded, not just drop it:\n{line}")
    check("CANDIDATE" in line,
          f"and must label which of the two artifacts it graded:\n{line}")


@test("M-BOM picks the NEWEST versioned export by NUMBER, not by glob order",
      kind="known_bad")
def t_mbom_newest_versioned_export_wins():
    """`06_build/fab_v22/` was invisible: the candidate list looked only at
    `06_build/fab/`, so even POST-seal the real artifact was missed.

    Picked by numeric version deliberately. `count_parity` took `paths[0]` off
    an unsorted glob and silently graded the interposer against cooksense's
    manifest — fixed the same day. Lexically `fab_v9` sorts ABOVE `fab_v22`, so
    a sorted() over names would reintroduce that defect in this very file.

    RED-VERIFIED: keying the sort on the directory NAME instead of the parsed
    integer makes this fixture grade `fab_v9` and FAIL on C999."""
    d = _bom_pair_project(tmpdir("mbomv_"), cand_dirname="fab_v22")
    stale = d / "06_build" / "fab_v9"          # lexically ABOVE 'fab_v22'
    stale.mkdir(parents=True, exist_ok=True)
    (stale / "bom_jlc.csv").write_text(
        "Comment,Designator,Footprint,MPN,LCSC\n10k,R1,R_0402,RC0402-10K,C999\n")
    line = _mbom_row(d)
    check("fab_v22" in line and "| PASS |" in line,
          f"fab_v22 must beat fab_v9 on NUMBER, not on string order:\n{line}")


# ================================== P-POL / P-KEEP on an ADR-0002 GENERIC board
# THE DEFECT THESE PIN (2026-07-30). Both checks used to grep `03_src/` for
# PER-BOARD PYTHON — an `audit_board.py` containing the word "polarit", a
# `generate_schematic.py` naming `polarity_audit`. ADR-0002's amendment
# (2026-07-23) abolished that location: a generic-backend board writes ZERO
# generation Python, so `03_src/` holds config and two drivers and there is
# nothing to grep. The result was not one wrong verdict — it was that EVERY
# COMPLIANT BOARD had to carry these two waivers VERBATIM, and a gate whose
# only possible output on a conforming board is a waiver is not grading the
# board, it is grading which generation era the board was built in. It is also
# canon M4's inherited-waiver shape exactly: pluto-rx2-8way-v2 carried both,
# and both closed with "PROPOSED SKILLS PATCH (reported, not applied)".
#
# The RED side is MEASURED ON EVERY RUN, not asserted in a docstring: each
# fixture below runs the PRE-FIX predicate (reconstructed from the pinned
# commit's source, see `_prefix_ppol_pkeep`) over the same tree and requires it
# to disagree. A gate fix whose red side is only claimed is a claim.
PRE_PPOL_COMMIT = "885ce0e8"


def _generic_project(d, pad_net=None, keepouts=None, mounting=True,
                     legacy_python=False, route_keepouts=False):
    """A ZERO-BESPOKE-PYTHON board (ADR-0002) with a minimal loadable board.

    `board is None` short-circuits P-POL/P-KEEP to N-A, so the fixture needs a
    real `.kicad_pcb` — a minimal one is enough, because neither check reads
    copper. That is itself the point: they grade the board's DECLARATIONS."""
    (d / "03_src" / "rules").mkdir(parents=True, exist_ok=True)
    (d / "04_kicad").mkdir(exist_ok=True)
    (d / "06_build").mkdir(exist_ok=True)
    (d / "04_kicad" / "b.kicad_pcb").write_text(
        '(kicad_pcb (version 20240108) (generator "pcbnew")\n'
        '  (general (thickness 1.6))\n  (paper "A4")\n'
        '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (44 "Edge.Cuts" user))\n'
        '  (setup (pad_to_mask_clearance 0))\n  (net 0 "")\n)\n')
    fp = {"project": {"name": "b"}}
    if pad_net is not None:
        fp["asserts"] = {"pad_net": pad_net}
    if keepouts is not None:
        fp["keepouts"] = keepouts
    if mounting:
        fp["board"] = {"mounting_holes": {"refdes_prefix": "H", "at": [[5, 5]]}}
    import yaml as _y
    (d / "03_src" / "floorplan.yaml").write_text(_y.safe_dump(fp))
    if route_keepouts:
        (d / "03_src" / "route.yaml").write_text(
            "prep:\n  keepouts:\n    layers: [User.2]\n"
            "    mounting_holes: {radius: 3.0, refdes_prefix: H}\n")
    if legacy_python:
        (d / "03_src" / "audit_board.py").write_text(
            "# checks pad-1 net polarity and the mate direction keepout\n")
    return d


def _policy_rows(d):
    run([KPY, POLICY, d, "--skip-drc"])
    md = (d / "06_build" / "policy_audit.md").read_text()
    return {cid: line for cid in ("P-POL", "P-KEEP")
            for line in md.splitlines() if line.startswith(f"| {cid} ")}


def _prefix_ppol_pkeep(d):
    """(p_pol, p_keep) as the PRE-FIX checks would have graded this tree.

    Reconstructed from the pinned commit's own source rather than paraphrased:
    the two regexes are EXTRACTED from `git show <commit>:policy_audit.py`, so
    if someone edits this helper to be kind the extraction fails loudly instead
    of quietly agreeing with the new code."""
    import re as _re
    src = run(["git", "-C", str(ROOT), "show",
               f"{PRE_PPOL_COMMIT}:skills/kicad-pcb/scripts/policy_audit.py"]).out
    m_pol = _re.search(r'has_pol = bool\(re\.search\(r"([^"]+)", audit_src', src)
    m_keep = _re.search(r'has_keep = bool\(re\.search\(r"([^"]+)", audit_src', src)
    check(m_pol and m_keep,
          "could not extract the PRE-FIX P-POL/P-KEEP predicates from "
          f"{PRE_PPOL_COMMIT} — the red side of these fixtures is not being "
          "measured, which is worse than not having it")
    ab = d / "03_src" / "audit_board.py"
    audit_src = ab.read_text() if ab.exists() else ""
    gs = d / "03_src" / "generate_schematic.py"
    pol = bool(_re.search(m_pol.group(1), audit_src, _re.I)) or bool(
        _re.search(r"polarity_audit", gs.read_text() if gs.exists() else ""))
    return pol, bool(_re.search(m_keep.group(1), audit_src, _re.I))


@test("P-POL/P-KEEP PASS an ADR-0002 generic board with NO per-board python — "
      "and the PRE-FIX checks FAIL the same tree")
def t_ppol_pkeep_generic_board_needs_no_waiver():
    """The headline. This is pluto-rx2-8way-v2's shape: a compliant board that
    writes no generation Python and declares its polarity and keepout facts
    where the SHARED backend consumes them. Post-fix both PASS on the
    declarations. Pre-fix both FAIL, which is why every generic board was
    carrying two verbatim waivers."""
    d = _generic_project(tmpdir("ppol_"),
                         pad_net=[{"ref": "U1", "pad": "1", "net": "GND"},
                                  {"ref": "D1", "pad": "1", "net": "VBUS"}],
                         keepouts=[{"name": "rf", "region": [1, 1, 2, 2],
                                    "layers": ["User.2"], "deny": ["tracks"]}],
                         route_keepouts=True)
    rows = _policy_rows(d)
    check("| PASS |" in rows["P-POL"], f"P-POL did not PASS:\n{rows['P-POL']}")
    check("| PASS |" in rows["P-KEEP"], f"P-KEEP did not PASS:\n{rows['P-KEEP']}")
    # the evidence must NAME the home and carry a COUNT — "it passed" with no
    # denominator is how a gate stops being readable.
    contains(rows["P-POL"], "asserts.pad_net x2", "P-POL detail")
    contains(rows["P-KEEP"], "keepouts", "P-KEEP detail")
    # THE RED SIDE, MEASURED: the pre-fix predicates on this exact tree.
    pol, keep = _prefix_ppol_pkeep(d)
    check(not pol and not keep,
          "the PRE-FIX P-POL/P-KEEP would have PASSED this generic board — "
          "then these fixtures prove nothing, because the fix would not have "
          "changed the verdict")


@test("P-POL FAILS a board that declares pad-1 polarity NOWHERE", kind="known_bad")
def t_kb_ppol_no_declaration_anywhere():
    """The other direction, and the one that makes the fix safe: widening a
    gate to accept a second home must not make it unfailable. No per-board
    script, no `asserts.pad_net` — the XT60 class (spf 2026-07-14, '+' net on
    the '-' blade) has nothing checking it, and P-POL says so."""
    d = _generic_project(tmpdir("ppol_"), pad_net=None, keepouts=None,
                         mounting=False)
    rows = _policy_rows(d)
    check("| FAIL |" in rows["P-POL"], f"P-POL did not FAIL:\n{rows['P-POL']}")
    contains(rows["P-POL"], "asserts.pad_net", "P-POL detail names the fix")
    check("| FAIL |" in rows["P-KEEP"], f"P-KEEP did not FAIL:\n{rows['P-KEEP']}")


@test("P-POL/P-KEEP refuse an EMPTY declaration block (canon M-COVER)",
      kind="known_bad")
def t_kb_ppol_empty_block_is_not_a_check():
    """A declaration with nothing in it is not a check, and accepting one is
    the cheapest way to make this fix vacuous: every board would add
    `asserts: {pad_net: []}` and both rows would go green forever. Same tree as
    the clean case with exactly one thing changed — the lists emptied."""
    d = _generic_project(tmpdir("ppol_"), pad_net=[], keepouts=[],
                         mounting=False)
    rows = _policy_rows(d)
    check("| FAIL |" in rows["P-POL"], f"empty pad_net passed:\n{rows['P-POL']}")
    check("| FAIL |" in rows["P-KEEP"], f"empty keepouts passed:\n{rows['P-KEEP']}")


@test("the LEGACY per-board-python path still satisfies P-POL/P-KEEP")
def t_ppol_legacy_path_unchanged():
    """Widening must not be a migration. The pre-ADR-0002 boards
    (smc0985-cooksense keeps a real `03_src/audit_board.py`) must go on
    passing through the ORIGINAL predicate, and the report must SAY which home
    satisfied it so the two eras stay distinguishable in the archive.

    MEASURED on the live fleet 2026-07-30: cooksense's own policy_audit.md row
    reads `pad-1-net polarity machine-checked: 03_src per-board python`."""
    d = _generic_project(tmpdir("ppol_"), pad_net=None, keepouts=None,
                         mounting=False, legacy_python=True)
    rows = _policy_rows(d)
    check("| PASS |" in rows["P-POL"], f"legacy P-POL broke:\n{rows['P-POL']}")
    check("| PASS |" in rows["P-KEEP"], f"legacy P-KEEP broke:\n{rows['P-KEEP']}")
    contains(rows["P-POL"], "per-board python", "P-POL names the legacy home")
    pol, keep = _prefix_ppol_pkeep(d)
    check(pol and keep,
          "the PRE-FIX predicates no longer pass the legacy tree — this "
          "fixture is supposed to prove the old path is UNCHANGED")


if __name__ == "__main__":
    sys.exit(main())
