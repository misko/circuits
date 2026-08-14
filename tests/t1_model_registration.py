#!/usr/bin/env python3
"""T1: independent native-model registration and project orchestration.

The regression fixture starts from the exact Pluto v5 board and exact native
Amphenol model, then changes only J2's internal model offset by 5 mm.  This is
the failure the gate exists to catch: model pixels can remain self-consistent
with their own mesh while missing F.Fab, F.CrtYd, and drilled attachment
datums.
"""
import hashlib
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (FAB_SCRIPTS, KPY, ROOT, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

ENGINE = FAB_SCRIPTS / "native_model_registration.py"
GATE = FAB_SCRIPTS / "model_registration_gate.py"
SOURCE_PROJECT = ROOT / "projects/pluto-rx2-8way-v5"
SOURCE_BOARD = SOURCE_PROJECT / "04_kicad/pluto_rx2_8way_v5.kicad_pcb"
SOURCE_MODEL = (SOURCE_PROJECT /
                "03_src/lib/3dmodels/Amphenol_901_143_6RFX-JLC-C429844.step")


def broken_project():
    project = tmpdir("model_registration_") / "pluto"
    board_dir = project / "04_kicad"
    model_dir = project / "03_src/lib/3dmodels"
    rules_dir = project / "03_src/rules"
    for directory in (board_dir, model_dir, rules_dir):
        directory.mkdir(parents=True, exist_ok=True)
    board = board_dir / SOURCE_BOARD.name
    model = model_dir / SOURCE_MODEL.name
    shutil.copy2(SOURCE_BOARD, board)
    shutil.copy2(SOURCE_MODEL, model)

    # Keep the exact J2 footprint and model; remove unrelated bodies so the
    # raster subtraction has one unambiguous subject. Change only the model's
    # footprint-local offset, preserving the model bytes and their SHA-256.
    mutate = (
        "import pcbnew,sys\n"
        "p=sys.argv[1]; b=pcbnew.LoadBoard(p)\n"
        "for fp in b.GetFootprints():\n"
        "  if fp.GetReference() != 'J2': fp.Models().clear()\n"
        "  else:\n"
        "    models=fp.Models(); model=models[0]\n"
        "    model.m_Offset.x=5.0; models[0]=model\n"
        "b.Save(p)\n"
    )
    must_pass(run([KPY, "-c", mutate, board]), "inject 5 mm model offset")
    model_sha = hashlib.sha256(model.read_bytes()).hexdigest()
    config = {
        "schema": 1,
        "groups": [{
            "id": "shifted_sma",
            "refs": ["J2"],
            "model_sha256": model_sha,
            "fit_tolerance_mm": 1.0,
            "courtyard_containment_tolerance_mm": 0.25,
            "search_margin_mm": 8.0,
            "render_width": 1200,
            "render_height": 800,
        }],
    }
    (rules_dir / "model_registration.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return project, board, model_sha


@test("native registration rejects a provenance-correct model shifted 5 mm",
      kind="known_bad")
def t_native_engine_and_project_gate_reject_shifted_model():
    project, board, model_sha = broken_project()
    direct = must_fail(run([
        KPY, ENGINE, board, project / "direct", "--refs", "J2",
        "--model-sha256", model_sha, "--fit-tol-mm", "1.0",
        "--courtyard-tol-mm", "0.25", "--search-margin-mm", "8.0",
        "--width", "1200", "--height", "800",
    ]), "native_model_registration.py shifted-model fixture",
        expect="P-MODEL-REG FAIL")
    contains(direct.out, "body exceeds F.CrtYd",
             "direct gate identifies physical courtyard excursion")

    aggregate = must_fail(run([
        KPY, GATE, project, "--board", f"04_kicad/{board.name}",
        "--out", "06_build/pre_route/model_registration.md",
    ]), "model_registration_gate.py shifted-model fixture",
        expect="P-MODEL-REG FAIL")
    contains(aggregate.out, "1/1 group(s) graded",
             "project gate reports its complete group denominator")


if __name__ == "__main__":
    sys.exit(main())
