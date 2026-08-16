#!/usr/bin/env python3
"""T1: canonical board rendering receives P-MODEL's exact environment."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, SCRIPTS, contains, main, must_fail, must_pass, run,  # noqa: E402
                     test, tmpdir)

RENDER = SCRIPTS / "render_board.py"


@test("P-RENDER-ENV passes a referenced KiCad model directory to kicad-cli")
def t_render_command_uses_model_coverage_environment():
    directory = tmpdir("render_env_")
    board = directory / "board.kicad_pcb"
    output = directory / "top.png"
    code = """
import pcbnew,sys
b=pcbnew.CreateEmptyBoard()
f=pcbnew.FOOTPRINT(b); f.SetReference('U1'); f.SetValue('SOIC14'); b.Add(f)
p=pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_RECT)
p.SetSize(pcbnew.VECTOR2I_MM(1,1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
p.SetLayerSet(pcbnew.PAD.SMDMask()); f.Add(p)
m=pcbnew.FP_3DMODEL()
m.m_Filename='${KICAD10_3DMODEL_DIR}/Package_SO.3dshapes/SOIC-14_3.9x8.7mm_P1.27mm.step'
f.Add3DModel(m)
pcbnew.SaveBoard(sys.argv[1],b)
"""
    must_pass(run([KPY, "-c", code, board]), "render environment fixture")
    result = must_pass(run([KPY, RENDER, board, output, "--dry-run"]),
                       "render command dry run")
    contains(result.out, '"coverage": [', "coverage denominator")
    contains(result.out, '"KICAD10_3DMODEL_DIR"', "required renderer define")
    payload = json.loads(result.out[result.out.index("{"):])
    command = payload["command"]
    define = "KICAD10_3DMODEL_DIR=" + payload["defines"]["KICAD10_3DMODEL_DIR"]
    assert "-D" in command and define in command, command


@test("P-RENDER-ENV refuses an unresolved saved-board model before rendering",
      kind="known_bad")
def t_render_command_refuses_unresolved_model():
    directory = tmpdir("render_missing_")
    board = directory / "board.kicad_pcb"
    output = directory / "top.png"
    code = """
import pcbnew,sys
b=pcbnew.CreateEmptyBoard()
f=pcbnew.FOOTPRINT(b); f.SetReference('U1'); f.SetValue('MISSING'); b.Add(f)
p=pcbnew.PAD(f); p.SetNumber('1'); p.SetShape(pcbnew.PAD_SHAPE_RECT)
p.SetSize(pcbnew.VECTOR2I_MM(1,1)); p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
p.SetLayerSet(pcbnew.PAD.SMDMask()); f.Add(p)
m=pcbnew.FP_3DMODEL(); m.m_Filename='${UNBOUND_MODEL_DIR}/no.step'
f.Add3DModel(m); pcbnew.SaveBoard(sys.argv[1],b)
"""
    must_pass(run([KPY, "-c", code, board]), "missing render model fixture")
    must_fail(run([KPY, RENDER, board, output, "--dry-run"]),
              "unresolved renderer model", "unresolved refs: ['U1']")


if __name__ == "__main__":
    sys.exit(main())
