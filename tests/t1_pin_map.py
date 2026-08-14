#!/usr/bin/env python3
"""T1: P-PINMAP early physical/schematic/footprint reconciliation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, contains, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

GATE = SCRIPTS / "pin_map_check.py"


def fixture(*, board_pins=("1", "2", "3", "4", "5", "6", "7", "8"),
            schematic_pins=("1", "2", "3", "4", "5", "6", "7", "8"),
            yaml_pins=("1", "2", "3", "4", "5", "6", "7", "8"),
            aliases=None):
    d = tmpdir("pinmap_")
    (d / "02_parts/FET").mkdir(parents=True)
    (d / "03_tscircuit/build").mkdir(parents=True)
    (d / "04_kicad").mkdir()
    pin_lines = "\n".join(
        f"  {p}: {'DRAIN' if int(p) >= 5 else 'SOURCE'}" for p in yaml_pins)
    alias_text = ""
    if aliases:
        alias_text = "pin_aliases:\n" + "\n".join(
            f"  {logical}:\n"
            f"    schematic: \"{spec.get('schematic', logical)}\"\n"
            f"    footprint: \"{spec.get('footprint', logical)}\"\n"
            f"    fused: {str(spec.get('fused', False)).lower()}\n"
            f"    why: \"{spec.get('why', '')}\"\n"
            f"    evidence: \"{spec.get('evidence', '')}\""
            for logical, spec in aliases.items()) + "\n"
    (d / "02_parts/FET/part.yaml").write_text(
        "mpn: FET\nsourcing: {lcsc: C1}\npins:\n" + pin_lines + "\n" + alias_text)

    cid = "source_component_0"
    data = [{"type": "source_component", "source_component_id": cid,
             "name": "Q1", "supplier_part_numbers": {"jlcpcb": ["C1"]}}]
    for i, pin in enumerate(schematic_pins):
        data.append({"type": "source_port", "source_port_id": f"p{i}",
                     "source_component_id": cid, "pin_number": int(pin),
                     "name": f"P{pin}", "port_hints": [f"pin{pin}", pin]})
    (d / "03_tscircuit/build/circuit.json").write_text(json.dumps(data))

    board = d / "04_kicad/demo.kicad_pcb"
    code = """
import pcbnew,sys
b=pcbnew.CreateEmptyBoard()
f=pcbnew.FOOTPRINT(b)
f.SetReference('Q1')
f.SetValue('C1')
b.Add(f)
for i,n in enumerate(sys.argv[2].split(',')):
 p=pcbnew.PAD(f)
 p.SetNumber(n)
 p.SetShape(pcbnew.PAD_SHAPE_RECT)
 p.SetSize(pcbnew.VECTOR2I_MM(1,1))
 p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
 p.SetLayerSet(pcbnew.PAD.SMDMask())
 f.Add(p)
 p.SetPosition(pcbnew.VECTOR2I_MM(i*1.2,0))
pcbnew.SaveBoard(sys.argv[1],b)
"""
    must_pass(run([KPY, "-c", code, board, ",".join(board_pins)]),
              "fixture board")
    return d, board


def gate(d, board):
    return run([KPY, GATE, d, "--board", board])


@test("P-PINMAP passes a complete one-to-one physical pin map")
def t_clean_identity():
    d, board = fixture()
    result = must_pass(gate(d, board), "identity map")
    contains(result.out, "8 declared physical pin identities graded", "coverage")


@test("P-PINMAP catches pins missing from both producer artifacts",
      kind="known_bad")
def t_missing_physical_pins():
    d, board = fixture(board_pins=("1", "2", "3", "4", "5"),
                       schematic_pins=("1", "2", "3", "4", "5"))
    result = must_fail(gate(d, board), "missing pins", "logical pin 6")
    contains(result.out, "footprint pad 6 is absent", "board-side failure")


@test("P-PINMAP accepts an evidenced manufacturer-fused drain land")
def t_evidenced_fused_alias():
    aliases = {p: {"footprint": "5", "schematic": p, "fused": True,
                   "why": "recommended land fuses drains 5-8",
                   "evidence": "datasheet rev A pp.11-13"}
               for p in ("6", "7", "8")}
    d, board = fixture(board_pins=("1", "2", "3", "4", "5"), aliases=aliases)
    must_pass(gate(d, board), "evidenced fused land")


@test("P-PINMAP refuses an unexplained alias", kind="known_bad")
def t_alias_needs_evidence():
    aliases = {"6": {"footprint": "5", "schematic": "6", "fused": True}}
    d, board = fixture(board_pins=("1", "2", "3", "4", "5"), aliases=aliases)
    must_fail(gate(d, board), "unevidenced alias",
              "requires both why and evidence")


@test("P-PINMAP refuses a collapse of unlike functions", kind="known_bad")
def t_fused_functions_must_agree():
    aliases = {"4": {"footprint": "5", "schematic": "4", "fused": True,
                      "why": "bad planted collapse", "evidence": "fixture"}}
    d, board = fixture(board_pins=("1", "2", "3", "5", "6", "7", "8"),
                       aliases=aliases)
    must_fail(gate(d, board), "unlike fused functions", "different functions")


@test("P-PINMAP refuses a zero-denominator run", kind="known_bad")
def t_zero_coverage():
    d, board = fixture(yaml_pins=("1", "2", "3"),
                       board_pins=("1", "2", "3"),
                       schematic_pins=("1", "2", "3"))
    must_fail(gate(d, board), "zero coverage", "zero multi-pin refs graded")


@test("G-VACUOUS P-PINMAP: a dossier that omits real datasheet pins agrees "
      "with equally truncated schematic and footprint artifacts",
      kind="vacuity", gate="pin_map_check.py")
def t_vacuity_all_three_repo_artifacts_share_the_same_truncated_pin_set():
    """P-PINMAP proves three repository representations agree; it cannot
    independently derive the package pin set from a PDF. A FET whose physical
    package has pins 1..8 can therefore pass when part.yaml, circuit.json and
    the board all repeat the same incorrect 1..5 subset. Fresh-context pin
    review is the independent authority that must close this declared mouth."""
    d, board = fixture(yaml_pins=("1", "2", "3", "4", "5"),
                       board_pins=("1", "2", "3", "4", "5"),
                       schematic_pins=("1", "2", "3", "4", "5"))
    result = must_pass(gate(d, board),
                       "three mutually consistent but datasheet-truncated maps")
    contains(result.out, "5 declared physical pin identities graded",
             "the denominator makes the blind spot observable")


if __name__ == "__main__":
    sys.exit(main())
