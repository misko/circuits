#!/usr/bin/env python3
"""E2E (slow tier): regenerate REAL boards with the generic generator and
prove they are electrically identical to the sealed ones.

This is the validation gate from the generic-generator work, kept as a
permanent regression: any change to generate_board_generic.py that alters
connectivity on a shipped board fails here. Sealed 04_kicad boards are read
ONLY — every artifact goes to a scratch dir.

Asserts PROPERTIES (node-for-node parity, audit verdict), never file bytes:
the silk de-collision search is order-dependent and KRT routing is
stochastic, so a golden-file comparison would be permanently broken.
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, main, must_pass,  # noqa: E402
                     project_copy, run, test, tmpdir)

GEN = SCRIPTS / "generate_board_generic.py"
PARITY = SCRIPTS / "board_netlist_parity.py"

BOARDS = [
    ("cook-loadcell", "cook_loadcell", 33),
    ("crow-array-pod", "crow_array_pod", 40),
]


def _regen_and_check(project, stem, nparts):
    proj_dir = ROOT / "projects" / project
    d = tmpdir(f"e2e_{stem}_")
    out = d / f"{stem}.kicad_pcb"
    r = must_pass(run([KPY, GEN, proj_dir / "03_src" / "floorplan.yaml", "-o", out],
                      cwd=proj_dir), f"{project}: generate")
    contains(r.out, "saved", "generator stdout")

    sealed = proj_dir / "04_kicad" / f"{stem}.kicad_pcb"
    rp = must_pass(run([KPY, PARITY, out, sealed]), f"{project}: parity")
    contains(rp.out, "BOARD PARITY 0 -> PASS", f"{project} parity verdict")

    # audit_board.py is path-hardcoded to 04_kicad/, so give it a scratch
    # project tree with the candidate board in place of the sealed one.
    scratch = project_copy(project, d / "proj", board=out)
    wv = d / "refdes_waiver.json"
    src_wv = out.parent / "refdes_waiver.json"
    if src_wv.exists():
        shutil.copy(src_wv, scratch / "06_build" / "refdes_waiver.json")
    ra = must_pass(run([KPY, "03_src/audit_board.py"], cwd=scratch),
                   f"{project}: audit_board")
    check("AUDIT PASS" in ra.out or "AUDIT: PASS" in ra.out,
          f"{project}: audit_board did not report PASS\n{ra.out[-2000:]}")
    return r, rp, ra


@test("E2E cook-loadcell: generic generator -> parity 0 + audit PASS", slow=True)
def t_cook_loadcell():
    r, rp, ra = _regen_and_check(*BOARDS[0])
    contains(rp.out, "77 nodes identical", "cook-loadcell parity node count")


@test("E2E crow-array-pod: generic generator -> parity 0 + audit PASS", slow=True)
def t_crow_array_pod():
    r, rp, ra = _regen_and_check(*BOARDS[1])
    contains(rp.out, "90 nodes identical", "crow-array-pod parity node count")


@test("E2E: regenerating twice gives the same CONNECTIVITY (not the same bytes)",
      slow=True)
def t_determinism():
    """Placement search and silk de-collision may reorder; connectivity may
    not. This is why the suite asserts properties, not file hashes."""
    from harness import board_nodes
    proj_dir = ROOT / "projects" / "cook-loadcell"
    d = tmpdir("e2e_det_")
    outs = []
    for i in (1, 2):
        o = d / f"b{i}.kicad_pcb"
        must_pass(run([KPY, GEN, proj_dir / "03_src" / "floorplan.yaml", "-o", o],
                      cwd=proj_dir), f"regen {i}")
        outs.append(o)
    a, b = board_nodes(outs[0]), board_nodes(outs[1])
    check(a == b, "two runs produced different connectivity")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] + ["--slow"]))
