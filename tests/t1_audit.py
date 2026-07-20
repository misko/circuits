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
                     edit_board, main, must_fail, must_pass, project_copy,
                     run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
AUDIT_T = SCRIPTS / "audit_template.py"
POLICY = SCRIPTS / "policy_audit.py"
PARITY = SCRIPTS / "board_netlist_parity.py"
LC = ROOT / "projects" / "cook-loadcell"
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


if __name__ == "__main__":
    sys.exit(main())
