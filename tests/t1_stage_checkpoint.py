#!/usr/bin/env python3
"""T1: exact-file identity across a human review pause."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

GATE = SCRIPTS / "stage_checkpoint.py"


def fixture():
    project = tmpdir("stage-checkpoint-")
    (project / "04_kicad").mkdir()
    (project / "06_build/netlists").mkdir(parents=True)
    (project / "04_kicad/demo.kicad_sch").write_text("schematic\n")
    (project / "06_build/netlists/demo.net").write_text("netlist\n")
    return project


@test("CHECKPOINT preserves an unchanged reviewed-stage file set")
def t_green():
    project = fixture()
    command = [KPY, GATE, "record", project, "schematic",
               "--input", "04_kicad/demo.kicad_sch",
               "--input", "06_build/netlists/demo.net"]
    must_pass(run(command), "record checkpoint")
    must_pass(run([KPY, GATE, "verify", project, "schematic"]),
              "verify checkpoint")


@test("CHECKPOINT refuses a changed file", kind="known_bad")
def t_changed():
    project = fixture()
    must_pass(run([KPY, GATE, "record", project, "schematic",
                   "--input", "04_kicad/demo.kicad_sch"]), "record checkpoint")
    (project / "04_kicad/demo.kicad_sch").write_text("changed\n")
    must_fail(run([KPY, GATE, "verify", project, "schematic"]),
              "changed checkpoint", "recorded input changed")


@test("CHECKPOINT refuses a missing record or recorded file", kind="known_bad")
def t_missing():
    project = fixture()
    must_fail(run([KPY, GATE, "verify", project, "schematic"]),
              "missing checkpoint", "missing")
    must_pass(run([KPY, GATE, "record", project, "schematic",
                   "--input", "04_kicad/demo.kicad_sch"]), "record checkpoint")
    (project / "04_kicad/demo.kicad_sch").unlink()
    must_fail(run([KPY, GATE, "verify", project, "schematic"]),
              "missing recorded file", "recorded input is missing")


@test("CHECKPOINT refuses project-root escape and empty file maps", kind="known_bad")
def t_scope_and_vacuity():
    project = fixture()
    outside = project.parent / f"{project.name}-outside.txt"
    outside.write_text("outside\n")
    must_fail(run([KPY, GATE, "record", project, "schematic",
                   "--input", outside]), "outside input", "escapes project root")
    record = project / "06_build/checkpoints/schematic.json"
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps({"schema": 1, "name": "schematic",
                                  "project": project.name, "files": {}}))
    must_fail(run([KPY, GATE, "verify", project, "schematic"]),
              "empty checkpoint", "invalid or empty")


if __name__ == "__main__":
    sys.exit(main())
