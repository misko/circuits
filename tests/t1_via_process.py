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


@test("V-PROCESS refuses an unprotected ordinary via inside an SMT land",
      kind="known_bad")
def t_ordinary_via_in_pad_fails():
    """Same-net via-in-pad is DRC-clean but can starve the solder joint."""
    _d, board_path, _assembly = fixture()
    board = pcbnew.LoadBoard(str(board_path))
    ordinary = [item for item in board.GetTracks()
                if item.GetClass() == "PCB_VIA"
                and item.GetFillingMode() != pcbnew.FILLING_MODE_FILLED][0]
    footprint = pcbnew.FOOTPRINT(board)
    footprint.SetReference("J11")
    pad = pcbnew.PAD(footprint)
    pad.SetNumber("3")
    pad.SetShape(pcbnew.PAD_SHAPE_RECT)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetSize(pcbnew.VECTOR2I_MM(0.74, 2.79))
    pad.SetLayerSet(pcbnew.PAD.SMDMask())
    pad.SetPosition(ordinary.GetPosition())
    footprint.Add(pad)
    board.Add(footprint)
    board.Save(str(board_path))
    result = must_fail(run([KPY, TOOL, board_path]),
                       "unprotected via inside J11.3", "V-VIP")
    contains(result.out, "SMT land(s) J11.3",
             "finding does not name the affected assembly land")


@test("V-PROCESS refuses native fill/cap intent with no assembly contract",
      kind="known_bad")
def t_protected_without_contract_fails():
    d, board, assembly = fixture(rows=((0.50, 0.20, True),))
    assembly.write_text(yaml.safe_dump({"service": "advanced"}))
    result = must_fail(run([KPY, TOOL, board]),
                       "protected via without order selector", "V-SCHEMA")
    contains(result.out, "declares no via_process",
             "native item flags were silently treated as an order process")


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
    contains(text, "Exact board census: 1 protected, 1 ordinary, 0 partial",
             "exact board counts are generated, not copied from prose")


@test("V-ORDER rejects a hard-coded census copied from an older board",
      kind="known_bad")
def t_stale_hardcoded_census_fails():
    _d, board, assembly = fixture()
    data = yaml.safe_load(assembly.read_text())
    data["via_process"]["order_remark"] += (
        " The exact routed-board census is 578 protected and 0 ordinary.")
    assembly.write_text(yaml.safe_dump(data, sort_keys=False))
    result = must_fail(run([KPY, TOOL, board]), "stale via census", "V-ORDER")
    contains(result.out, "exact board is 1 / 1", "finding prints live counts")


if __name__ == "__main__":
    sys.exit(main())
