#!/usr/bin/env python3
"""V-PROCESS: selective via fabrication intent reaches the order boundary."""
import sys
from pathlib import Path

import pcbnew
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (KPY, ROOT, check, contains, main, must_fail,  # noqa: E402
                     must_pass, run, test, tmpdir)

TOOL = ROOT / "skills/jlcpcb-fab/scripts/via_process_check.py"
EXPORT = ROOT / "skills/jlcpcb-fab/scripts/export_jlc_package.py"


def fixture(rows=((0.50, 0.20, True), (0.60, 0.30, False))):
    d = tmpdir("vprocess_")
    board_path = d / "04_kicad" / "demo.kicad_pcb"
    board_path.parent.mkdir(parents=True)
    board = pcbnew.BOARD()
    for i, (diameter, drill, protected) in enumerate(rows):
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I_MM(10 + i, 10))
        via.SetWidth(pcbnew.FromMM(diameter))
        via.SetDrill(pcbnew.FromMM(drill))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        if protected:
            via.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)
            via.SetFillingMode(pcbnew.FILLING_MODE_FILLED)
        board.Add(via)
    board.Save(str(board_path))
    assembly = d / "03_src" / "rules" / "assembly.yaml"
    assembly.parent.mkdir(parents=True)
    assembly.write_text(yaml.safe_dump({
        "service": "advanced",
        "via_process": {
            "ipc_4761": "type_vii_filled_and_capped",
            "protected_geometry": {
                "via_diameter_mm": 0.50, "drill_mm": 0.20},
            "fabricator_selector": {
                "kind": "drill_family", "protected_drill_mm": 0.20,
                "ordinary_drill_mm": [0.30]},
            "order_remark": (
                "Fill and cap the complete 0.20 mm drill family; do not fill "
                "or cap the ordinary 0.30 mm drill family."),
            "uploader_confirmation_required": True,
        },
        "not_assembled": [],
    }, sort_keys=False))
    return d, board_path, assembly


@test("V-PROCESS accepts drill-disjoint protected and ordinary families")
def t_disjoint_passes():
    _d, board, _assembly = fixture()
    result = must_pass(run([KPY, TOOL, board]), "clean via process")
    contains(result.out, "1 protected / 1 ordinary", "census is explicit")
    contains(result.out, "V-PROCESS PASS", "gate is green")


@test("V-PROCESS refuses an ordinary via in the protected drill family",
      kind="known_bad")
def t_ordinary_protected_drill_fails():
    _d, board, _assembly = fixture(rows=(
        (0.50, 0.20, True), (0.50, 0.20, False)))
    result = must_fail(run([KPY, TOOL, board]),
                       "ambiguous ordinary 0.20 drill", "V-SELECT")
    contains(result.out, "shares protected 0.200mm drill family",
             "finding names the unmanufacturable ambiguity")


@test("V-PROCESS refuses protected geometry outside its selected family",
      kind="known_bad")
def t_protected_wrong_geometry_fails():
    _d, board, _assembly = fixture(rows=(
        (0.60, 0.30, True), (0.60, 0.30, False)))
    result = must_fail(run([KPY, TOOL, board]),
                       "wrong protected geometry", "V-GEOM")
    contains(result.out, "expected 0.500/0.200mm",
             "finding names authored protected geometry")


@test("JLC exporter emits the exact generated via order note")
def t_exporter_emits_note():
    d, board, assembly = fixture()
    out = d / "06_build" / "fab"
    must_pass(run([KPY, EXPORT, board, out, "--layers", "4"]),
              "minimal JLC export with selective via process")
    note = out / "order_notes.txt"
    check(note.is_file(), "export wrote no order_notes.txt")
    text = note.read_text()
    contains(text, "GENERATED; DO NOT RE-TYPE", "provenance warning")
    contains(text, "complete 0.20 mm drill family", "protected selector")
    contains(text, "ordinary 0.30 mm drill family", "ordinary selector")
    contains(text, str(assembly), "note names its machine-readable source")
    contains(text, "Uploader confirmation required: YES", "human gate")


if __name__ == "__main__":
    sys.exit(main())
