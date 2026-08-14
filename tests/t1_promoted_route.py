#!/usr/bin/env python3
"""P-ROUTEBASE: a promoted chain must derive from the exact source base."""
import shutil
import sys
from pathlib import Path

import pcbnew
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, contains, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

TOOL = SCRIPTS / "promoted_route_check.py"


def fixture(with_chain=True):
    d = tmpdir("routebase_")
    (d / "03_src/route").mkdir(parents=True)
    (d / "04_kicad").mkdir()
    board_path = d / "04_kicad/demo.kicad_pcb"
    board = pcbnew.BOARD()
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference("U1")
    fp.SetPosition(pcbnew.VECTOR2I_MM(20, 20))
    pad = pcbnew.PAD(fp)
    pad.SetNumber("1")
    pad.SetPosition(pcbnew.VECTOR2I_MM(20, 20))
    pad.SetSize(pcbnew.VECTOR2I_MM(1, 1))
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetLayerSet(pad.SMDMask())
    fp.Add(pad)
    board.Add(fp)
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I_MM(22, 20))
    via.SetWidth(pcbnew.FromMM(0.5))
    via.SetDrill(pcbnew.FromMM(0.2))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)
    via.SetFillingMode(pcbnew.FILLING_MODE_FILLED)
    board.Add(via)
    board.Save(str(board_path))
    chain = d / "03_src/route/r1.kicad_pcb"
    if with_chain:
        shutil.copy(board_path, chain)
    route = d / "03_src/route.yaml"
    route.write_text(yaml.safe_dump({
        "route": {"import_source": "promoted",
                  "final": "03_src/route/r1.kicad_pcb"}}, sort_keys=False))
    return d, board_path, chain, route


def edit(path, code):
    script = f"""
import pcbnew
b=pcbnew.LoadBoard({str(path)!r})
{code}
b.Save({str(path)!r})
"""
    must_pass(run([KPY, "-c", script]), "fixture edit")


def prepared_fixture(*, copy_segment_to_chain=True):
    d, board, chain, route = fixture()
    doc = yaml.safe_load(route.read_text())
    doc["project"] = {"build_dir": "06_build/route"}
    doc["prep"] = {"out": "r0.kicad_pcb",
                   "seed_stubs": {"stubs": [{"net": "PWR"}]}}
    route.write_text(yaml.safe_dump(doc, sort_keys=False))
    prepared = d / "06_build/route/r0.kicad_pcb"
    prepared.parent.mkdir(parents=True)
    shutil.copy(board, prepared)
    segment = "t=pcbnew.PCB_TRACK(b);t.SetStart(pcbnew.VECTOR2I_MM(20,22));t.SetEnd(pcbnew.VECTOR2I_MM(21,22));t.SetWidth(pcbnew.FromMM(0.3));t.SetLayer(pcbnew.F_Cu);b.Add(t)"
    edit(prepared, segment)
    if copy_segment_to_chain:
        edit(chain, segment)
    return d, board, prepared, chain, route


@test("P-ROUTEBASE accepts matching placement and source vias")
def t_matching():
    _d, board, _chain, route = fixture()
    result = must_pass(run([KPY, TOOL, board, route]), "compatible route")
    contains(result.out, "1 footprints / 1 base/prepared vias / 0 prepared segments", "coverage")


@test("P-ROUTEBASE accepts freshly prepared deterministic copper")
def t_prepared_matching():
    _d, board, _prepared, _chain, route = prepared_fixture()
    result = must_pass(run([KPY, TOOL, board, route]), "prepared route")
    contains(result.out, "1 prepared segments", "prepared copper coverage")


@test("P-ROUTEBASE refuses a prepared segment absent from the chain",
      kind="known_bad")
def t_prepared_segment_missing():
    _d, board, _prepared, _chain, route = prepared_fixture(
        copy_segment_to_chain=False)
    must_fail(run([KPY, TOOL, board, route]),
              "stale seed copper", "prepared segment missing")


@test("P-ROUTEBASE permits an absent first-route artifact")
def t_first_route():
    _d, board, _chain, route = fixture(with_chain=False)
    result = must_pass(run([KPY, TOOL, board, route]), "first route")
    contains(result.out, "N-A", "absence is explicit, not a vacuous PASS")


@test("P-ROUTEBASE refuses source-via geometry drift", kind="known_bad")
def t_via_geometry():
    _d, board, chain, route = fixture()
    edit(chain, "v=list(b.GetTracks())[0];v.SetWidth(pcbnew.FromMM(0.6));v.SetDrill(pcbnew.FromMM(0.3))")
    result = must_fail(run([KPY, TOOL, board, route]),
                       "via geometry drift", "source via geometry differs")
    contains(result.out, "0.500/0.200mm vs promoted 0.600/0.300mm", "dimensions")


@test("P-ROUTEBASE refuses source-via process drift", kind="known_bad")
def t_via_process():
    _d, board, chain, route = fixture()
    edit(chain, "v=list(b.GetTracks())[0];v.SetCappingMode(pcbnew.CAPPING_MODE_NOT_CAPPED);v.SetFillingMode(pcbnew.FILLING_MODE_NOT_FILLED)")
    must_fail(run([KPY, TOOL, board, route]),
              "via process drift", "source via process differs")


@test("P-ROUTEBASE refuses a source via removed from the chain", kind="known_bad")
def t_via_removed():
    _d, board, chain, route = fixture()
    edit(chain, "[b.Remove(v) for v in list(b.GetTracks())]")
    must_fail(run([KPY, TOOL, board, route]),
              "removed source via", "source via missing from promoted chain")


@test("P-ROUTEBASE refuses a new source via absent from the chain", kind="known_bad")
def t_via_added_to_source():
    _d, board, chain, route = fixture()
    edit(board, "v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I_MM(24,20));v.SetWidth(pcbnew.FromMM(0.6));v.SetDrill(pcbnew.FromMM(0.3));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)")
    must_fail(run([KPY, TOOL, board, route]),
              "new source via", "source via missing from promoted chain")


@test("P-ROUTEBASE refuses moved footprints", kind="known_bad")
def t_moved_footprint():
    _d, board, chain, route = fixture()
    edit(chain, "b.FindFootprintByReference('U1').SetPosition(pcbnew.VECTOR2I_MM(21,20))")
    must_fail(run([KPY, TOOL, board, route]),
              "stale placement", "U1 placement differs")


if __name__ == "__main__":
    sys.exit(main())
