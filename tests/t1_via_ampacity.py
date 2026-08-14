#!/usr/bin/env python3
"""A-VIA series-transfer capacity contracts."""
import json
import sys
from pathlib import Path

import pcbnew
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, contains, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

TOOL = SCRIPTS / "via_ampacity_check.py"


def fixture(count=4, required=3.0, block=True):
    d = tmpdir("via_amp_")
    board_path = d / "demo.kicad_pcb"
    board = pcbnew.BOARD()
    net = pcbnew.NETINFO_ITEM(board, "PWR")
    board.Add(net)
    for i in range(count):
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I_MM(10 + i, 10))
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetDrill(pcbnew.FromMM(0.3))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(net)
        board.Add(via)
    board.Save(str(board_path))
    route = d / "route.yaml"
    doc = {"project": {"board": "demo.kicad_pcb"}}
    if block:
        doc["via_ampacity"] = {
            "source": "TI SLVA959B Table 3-1 / IPC-2152",
            "method": "finished-hole lookup at stated rise",
            "temperature_rise_c": 10,
            "capacity_by_finished_hole_mm": {"0.20": 0.55, "0.30": 0.84},
            "transfers": [{
                "name": "bank", "net": "PWR", "rect": [9, 9, 15, 11],
                "required_continuous_a": required, "minimum_vias": count,
                "why": "fixture series layer transition",
            }],
        }
    route.write_text(yaml.safe_dump(doc, sort_keys=False))
    return d, board_path, route


@test("A-VIA credits a declared bank from finished-hole capacity")
def t_clean():
    d, board, route = fixture()
    result = must_pass(run([KPY, TOOL, board, route, "--json", d / "out.json"]),
                       "qualified transfer")
    contains(result.out, "3.360 A credited / 3.000 A required", "capacity")
    report = json.loads((d / "out.json").read_text())
    assert report["verdict"] == "PASS"


@test("A-VIA refuses insufficient parallel barrels", kind="known_bad")
def t_insufficient():
    _d, board, route = fixture(count=2, required=3.0)
    must_fail(run([KPY, TOOL, board, route]),
              "under-capacity transfer", "below 3.000 A")


@test("A-VIA is explicit N-A without an adopted transfer contract")
def t_unmigrated():
    _d, board, route = fixture(block=False)
    result = must_pass(run([KPY, TOOL, board, route]), "unmigrated board")
    contains(result.out, "coverage: 0/0", "explicit denominator")
    contains(result.out, "N-A", "explicit disposition")


@test("G-VACUOUS A-VIA: a counted via need not cross real current",
      kind="vacuity", gate="via_ampacity_check.py")
def t_vacuity_unconnected_via():
    _d, board, route = fixture(count=1, required=0.8)
    result = must_pass(run([KPY, TOOL, board, route]),
                       "geometrically counted but unconnected barrel")
    contains(result.out, "A-VIA PASS", "declared blind spot reproduced")


if __name__ == "__main__":
    sys.exit(main())
