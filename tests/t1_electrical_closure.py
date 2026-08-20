#!/usr/bin/env python3
"""T1: E-CLOSURE composition is non-vacuous and fail closed."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import check, eq, main, test, tmpdir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "skills/kicad-pcb/scripts"))
import electrical_closure  # noqa: E402


def project_tree():
    project = tmpdir("e_closure_")
    (project / "03_src/rules").mkdir(parents=True)
    (project / "03_src/rules/electrical_invariants.yaml").write_text(
        "schema: 1\ninvariants: []\n")
    (project / "02_parts/U1").mkdir(parents=True)
    (project / "02_parts/U1/part.yaml").write_text("mpn: U1\n")
    (project / "03_tscircuit/build").mkdir(parents=True)
    (project / "03_tscircuit/build/circuit.json").write_text("[]\n")
    (project / "06_build/netlists").mkdir(parents=True)
    (project / "06_build/netlists/board.net").write_text("(export)\n")
    return project


@test("E-CLOSURE composes exactly nine specialist predicates")
def t_clean_composition():
    project = project_tree()
    report = electrical_closure.grade(
        project, runner=lambda _command, _cwd: {
            "status": "PASS", "returncode": 0, "elapsed_s": 0.01,
            "output": "fixture pass"})
    eq(report["verdict"], "ACCEPTED", "closure verdict")
    eq(report["coverage"], {"passing": 9, "total": 9}, "closure denominator")


@test("one missing electrical predicate rejects the whole closure",
      kind="known_bad")
def t_one_failure_rejects():
    project = project_tree()
    calls = {"count": 0}
    def runner(_command, _cwd):
        calls["count"] += 1
        return {"status": "FAIL" if calls["count"] == 4 else "PASS",
                "returncode": 1 if calls["count"] == 4 else 0,
                "elapsed_s": 0.01, "output": "fixture"}
    report = electrical_closure.grade(project, runner=runner)
    eq(report["verdict"], "REJECTED", "closure verdict")
    eq(report["coverage"], {"passing": 8, "total": 9}, "closure denominator")
    check(report["checks"]["design_and_corner_models"]["status"] == "FAIL",
          "failed corner predicate disappeared")


if __name__ == "__main__":
    raise SystemExit(main())
