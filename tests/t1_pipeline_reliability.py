#!/usr/bin/env python3
"""Regression tests for bounded execution, provenance, maturity and facts."""
import json
import os
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, SCRIPTS, check, contains, edit_board, eq, main,
                     must_fail, must_pass, run, test, tmpdir)  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
from process_runner import EXIT_TIMEOUT, run_bounded  # noqa: E402

PROV = SCRIPTS / "artifact_provenance.py"
STATE = SCRIPTS / "project_state.py"
FACTS = SCRIPTS / "critical_part_facts.py"


@test("bounded runner streams quiet-stage heartbeats and kills the process "
      "group at its hard deadline")
def t_bounded_runner_timeout():
    d = tmpdir("bounded_")
    child_pid = d / "child.pid"
    code = (
        "import pathlib,subprocess,sys,time\n"
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])\n"
        "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
        "print('child',p.pid,flush=True)\n"
        "time.sleep(60)\n")
    result = run_bounded(
        [sys.executable, "-c", code, str(child_pid)], timeout_s=0.35,
        heartbeat_s=0.1, label="fixture", state_path=d / "state.json",
        echo=False)
    eq(result.returncode, EXIT_TIMEOUT, "timeout exit")
    check(result.elapsed_s < 3, f"deadline did not bound execution: {result.elapsed_s}")
    state = json.loads((d / "state.json").read_text())
    eq(state["status"], "timed_out", "published terminal state")
    pid = int(child_pid.read_text())
    for _ in range(20):
        stat = Path(f"/proc/{pid}/stat")
        if not stat.exists() or stat.read_text().split()[2] == "Z":
            break
        time.sleep(0.05)
    else:
        raise AssertionError(f"grandchild {pid} survived process-group timeout")


def provenance_tree():
    d = tmpdir("prov_")
    (d / "03_src").mkdir()
    (d / "06_build").mkdir()
    (d / "03_src" / "input.txt").write_text("source-v1\n")
    (d / "06_build" / "output.txt").write_text("old\n")
    must_pass(run([sys.executable, PROV, "begin", d, "--stage", "layout",
                   "--input", "03_src/input.txt", "--output",
                   "06_build/output.txt"]), "provenance begin")
    (d / "06_build" / "output.txt").write_text("new\n")
    must_pass(run([sys.executable, PROV, "finish", d, "--stage", "layout"]),
              "provenance finish")
    return d


@test("major-artifact provenance audits an unchanged completed stage")
def t_provenance_clean():
    d = provenance_tree()
    r = must_pass(run([sys.executable, PROV, "audit", d,
                       "--require-stage", "layout"]), "provenance audit")
    contains(r.out, "M-PROV PASS", "clean provenance verdict")


@test("major-artifact provenance rejects a post-stage artifact mutation",
      kind="known_bad")
def t_provenance_mutation():
    d = provenance_tree()
    (d / "06_build" / "output.txt").write_text("mutated after gate\n")
    r = must_fail(run([sys.executable, PROV, "audit", d,
                       "--require-stage", "layout"]),
                  "provenance after mutation", "M-PROV FAIL")
    contains(r.out, "output changed", "mutation diagnosis")


@test("major-artifact provenance rejects an input changed during its stage",
      kind="known_bad")
def t_provenance_input_mutation():
    d = tmpdir("prov_input_")
    (d / "03_src").mkdir()
    (d / "06_build").mkdir()
    source = d / "03_src" / "input.txt"
    output = d / "06_build" / "output.txt"
    source.write_text("source-v1\n")
    must_pass(run([sys.executable, PROV, "begin", d, "--stage", "layout",
                   "--input", "03_src/input.txt", "--output",
                   "06_build/output.txt"]), "provenance begin")
    source.write_text("source-v2\n")
    output.write_text("built from moving input\n")
    r = must_fail(run([sys.executable, PROV, "finish", d, "--stage", "layout"]),
                  "provenance with moving input", "M-PROV FAIL")
    contains(r.out, "input moved during stage", "input mutation diagnosis")


def maturity_tree(open_blocker=False):
    d = tmpdir("state_")
    (d / "01_docs").mkdir()
    (d / "06_build").mkdir()
    (d / "evidence.txt").write_text("reviewed\n")
    blocker = ("  - id: unsafe\n    state: open\n"
               "    blocks_at_or_above: FIRST_ARTICLE_ORDERABLE\n"
               "    owner: electrical\n    finding: planted defect\n"
               "    closes_when: remove the planted defect\n") if open_blocker else ""
    (d / "01_docs" / "findings.yaml").write_text(
        "schema: 1\ntarget: FIRST_ARTICLE_ORDERABLE\ngates:\n"
        "  - id: design\n    required_for: DESIGN_CLEAN\n    state: pass\n"
        "    owner: design\n    closes_when: review passes\n"
        "    evidence: [evidence.txt]\n"
        "  - id: order\n    required_for: FIRST_ARTICLE_ORDERABLE\n"
        "    state: pass\n    owner: fab\n    closes_when: fab gate passes\n"
        "    evidence: [evidence.txt]\n"
        "  - id: test\n    required_for: FIRST_ARTICLE_TESTED\n"
        "    state: pending\n    owner: lab\n    closes_when: bench passes\n"
        "  - id: production\n    required_for: PRODUCTION_RELEASED\n"
        "    state: pending\n    owner: ops\n    closes_when: pilot passes\n"
        "findings:\n" + blocker)
    return d


@test("findings ledger derives orderable without claiming hardware tested")
def t_project_state_clean():
    d = maturity_tree()
    r = must_pass(run([sys.executable, STATE, d, "--expect",
                       "FIRST_ARTICLE_ORDERABLE"]), "maturity derivation")
    contains(r.out, "derived=FIRST_ARTICLE_ORDERABLE", "derived state")


@test("an open order blocker lowers maturity and fails the expected state",
      kind="known_bad")
def t_project_state_blocker():
    d = maturity_tree(open_blocker=True)
    r = must_fail(run([sys.executable, STATE, d, "--expect",
                       "FIRST_ARTICLE_ORDERABLE", "--no-write"]),
                  "maturity with blocker", "M-STATE FAIL")
    contains(r.out, "unsafe", "blocker id")


def usb_board_copy():
    src = ROOT / "projects/usb-hub-3s-v3"
    d = tmpdir("critfact_")
    (d / "03_src" / "rules").mkdir(parents=True)
    (d / "04_kicad").mkdir()
    shutil.copytree(src / "02_parts" / "TYPE-C-31-M-12A",
                    d / "02_parts" / "TYPE-C-31-M-12A")
    shutil.copy(src / "03_src" / "rules" / "critical_parts.yaml",
                d / "03_src" / "rules" / "critical_parts.yaml")
    board = d / "04_kicad" / "usb_hub_3s_v2.kicad_pcb"
    shutil.copy(src / "04_kicad" / board.name, board)
    return d, board


@test("critical accepted facts pass the reviewed USB-C footprint")
def t_critical_facts_clean():
    d, _ = usb_board_copy()
    r = must_pass(run([KPY, FACTS, d]), "critical USB-C facts")
    contains(r.out, "23/23 facts compared", "facts denominator")


@test("critical accepted facts reject a mutated USB-C signal land",
      kind="known_bad")
def t_critical_facts_mutation():
    d, board = usb_board_copy()
    edit_board(board,
               "f=b.FindFootprintByReference('J5')\n"
               "p=next(p for p in f.Pads() if p.GetNumber()=='A5')\n"
               "p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.50),"
               "pcbnew.FromMM(1.14)))")
    r = must_fail(run([KPY, FACTS, d]), "mutated USB-C fact",
                  "P-CRITFACT FAIL")
    contains(r.out, "pad_A5_size", "exact mutated fact")


if __name__ == "__main__":
    raise SystemExit(main())
