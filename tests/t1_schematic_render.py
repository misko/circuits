#!/usr/bin/env python3
"""Executable checks for the exact-Circuit-JSON human schematic renderer."""

import json
import hashlib
import pathlib
import sys
import tempfile

from harness import check, contains, main, run, test


ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDERER = ROOT / "skills/kicad-pcb/scripts/render_schematic_pdf.mjs"
ALIGNER = RENDERER


def component(number, sheet_id=None):
    source_id = f"source_component_{number}"
    schematic_id = f"schematic_component_{number}"
    source = {
        "type": "source_component",
        "source_component_id": source_id,
        "ftype": "simple_chip",
        "name": f"U{number + 1}",
    }
    schematic = {
        "type": "schematic_component",
        "schematic_component_id": schematic_id,
        "center": {"x": number * 3, "y": 0},
        "rotation": 0,
        "size": {"width": 2, "height": 1},
        "source_component_id": source_id,
    }
    if sheet_id is not None:
        schematic["schematic_sheet_id"] = sheet_id
    text = {
        "type": "schematic_text",
        "schematic_text_id": f"schematic_text_{number}",
        "schematic_component_id": schematic_id,
        "text": f"U{number + 1}",
        "anchor": "center",
        "rotation": 0,
        "position": {"x": number * 3, "y": 0},
        "font_size": 0.18,
    }
    if sheet_id is not None:
        text["schematic_sheet_id"] = sheet_id
    return [source, schematic, text]


def render(circuit, aliases=None):
    tmp = tempfile.TemporaryDirectory()
    directory = pathlib.Path(tmp.name)
    source = directory / "circuit.json"
    output = directory / "schematic.pdf"
    source.write_text(json.dumps(circuit))
    source_before = hashlib.sha256(source.read_bytes()).hexdigest()
    command = ["node", str(RENDERER), str(source), str(output),
               "--title", "FIXTURE"]
    if aliases is not None:
        alias_path = directory / "net_aliases.txt"
        alias_path.write_text(aliases)
        command += ["--net-aliases", str(alias_path)]
    result = run(command)
    source_after = hashlib.sha256(source.read_bytes()).hexdigest()
    return tmp, output, result, source_before, source_after


@test("scaled two-port alignment lands symbol terminals on original trace endpoints")
def t_scaled_symbol_alignment():
    script = f"""
      import {{ alignScaledTwoPortSymbols }} from {json.dumps(ALIGNER.as_uri())}
      const original = [
        {{
          type: "schematic_component",
          schematic_component_id: "schematic_component_0",
          symbol_name: "fixture",
          center: {{ x: 10, y: 20 }},
        }},
        {{
          type: "schematic_port",
          schematic_port_id: "schematic_port_0",
          schematic_component_id: "schematic_component_0",
          center: {{ x: 10, y: 19.7 }},
        }},
        {{
          type: "schematic_port",
          schematic_port_id: "schematic_port_1",
          schematic_component_id: "schematic_component_0",
          center: {{ x: 10, y: 20.3 }},
        }},
      ]
      const before = JSON.stringify(original)
      const symbols = {{
        fixture: {{
          center: {{ x: 0, y: 0 }},
          ports: [{{ x: 0, y: -0.5 }}, {{ x: 0, y: 0.5 }}],
        }},
      }}
      const result = alignScaledTwoPortSymbols(original, symbols)
      const component = result.circuit[0]
      const ports = result.circuit.slice(1)
      const scale = 0.6
      const anchor = symbols.fixture.ports[1]
      const translation = {{
        x: ports[1].center.x - anchor.x,
        y: ports[1].center.y - anchor.y,
      }}
      const projected = symbols.fixture.ports.map((port) => ({{
        x: scale * port.x + translation.x,
        y: scale * port.y + translation.y,
      }}))
      console.log(JSON.stringify({{
        count: result.correctionCount,
        residual: result.maximumResidual,
        inputUnchanged: before === JSON.stringify(original),
        component,
        projected,
      }}))
    """
    result = run(["node", "--input-type=module", "--eval", script])
    check(result.rc == 0, result.out)
    payload = json.loads(result.out)
    check(payload["count"] == 1, "expected one scaled-symbol correction")
    check(payload["inputUnchanged"], "alignment mutated authoritative input")
    check(payload["residual"] < 1e-9, "alignment residual was not negligible")
    check(abs(payload["projected"][0]["y"] - 19.7) < 1e-9,
          "lower symbol terminal missed original endpoint")
    check(abs(payload["projected"][1]["y"] - 20.3) < 1e-9,
          "upper symbol terminal missed original endpoint")


@test("multi-sheet renderer fits exact Circuit JSON into one PDF page per sheet")
def t_multi_sheet():
    circuit = [
        {
            "type": "schematic_sheet",
            "schematic_sheet_id": "schematic_sheet_0",
            "name": "input",
            "display_name": "INPUT",
            "sheet_index": 1,
        },
        {
            "type": "schematic_sheet",
            "schematic_sheet_id": "schematic_sheet_1",
            "name": "output",
            "display_name": "OUTPUT",
            "sheet_index": 2,
        },
        *component(0, "schematic_sheet_0"),
        *component(1, "schematic_sheet_1"),
    ]
    tmp, output, result, source_before, source_after = render(circuit)
    try:
        check(result.rc == 0, result.out)
        check(output.stat().st_size > 1000, "renderer did not create a real PDF")
        contains(result.out, "page 1/2: INPUT", "first-page progress")
        contains(result.out, "page 2/2: OUTPUT", "second-page progress")
        contains(result.out, "landscape", "page-fit disclosure")
        check(source_before == source_after, "renderer modified its exact input")
        info = run(["pdfinfo", str(output)])
        check(info.rc == 0, info.out)
        contains(info.out, "Pages:           2", "multi-page PDF page count")
    finally:
        tmp.cleanup()


@test("single-sheet legacy Circuit JSON remains renderable")
def t_legacy_single_sheet():
    tmp, output, result, _, _ = render(component(0))
    try:
        check(result.rc == 0, result.out)
        info = run(["pdfinfo", str(output)])
        contains(info.out, "Pages:           1", "legacy page count")
    finally:
        tmp.cleanup()


@test("human PDF uses canonical net names without modifying Circuit JSON")
def t_canonical_net_names():
    circuit = component(0)
    circuit += [
        {
            "type": "source_net",
            "source_net_id": "source_net_0",
            "name": "N5V_INTERNAL",
        },
        {
            "type": "schematic_net_label",
            "schematic_net_label_id": "schematic_net_label_0",
            "text": "N5V_INTERNAL",
            "source_net_id": "source_net_0",
            "anchor_position": {"x": 1, "y": 0},
            "center": {"x": 1.5, "y": 0},
            "anchor_side": "left",
        },
    ]
    tmp, output, result, source_before, source_after = render(
        circuit, "N5V_INTERNAL 5V_CANONICAL\n"
    )
    try:
        check(result.rc == 0, result.out)
        contains(result.out, "1 explicit net alias(es)", "alias disclosure")
        check(source_before == source_after, "alias render modified Circuit JSON")
        text = run(["pdftotext", str(output), "-"])
        check(text.rc == 0, text.out)
        contains(text.out, "5V_CANONICAL", "canonical label in PDF")
        check("N5V_INTERNAL" not in text.out,
              "authoring-only net name leaked into PDF")
    finally:
        tmp.cleanup()


@test("leading-N digit convention is canonicalized without an explicit alias")
def t_implicit_digit_alias():
    circuit = component(0)
    circuit.append({
        "type": "schematic_net_label",
        "schematic_net_label_id": "schematic_net_label_0",
        "text": "N12V_AUX",
        "anchor_position": {"x": 1, "y": 0},
        "center": {"x": 1.5, "y": 0},
        "anchor_side": "left",
    })
    tmp, output, result, _, _ = render(circuit)
    try:
        check(result.rc == 0, result.out)
        text = run(["pdftotext", str(output), "-"])
        contains(text.out, "12V_AUX", "implicit canonical label")
        check("N12V_AUX" not in text.out,
              "leading-N authoring syntax leaked into PDF")
    finally:
        tmp.cleanup()


@test(
    "multi-sheet renderer rejects an unowned component instead of silently omitting it",
    kind="known_bad",
)
def t_unowned_component():
    circuit = [
        {
            "type": "schematic_sheet",
            "schematic_sheet_id": "schematic_sheet_0",
            "name": "input",
            "display_name": "INPUT",
            "sheet_index": 1,
        },
        *component(0),
    ]
    tmp, output, result, _, _ = render(circuit)
    try:
        check(result.rc != 0, "unowned component was silently accepted")
        contains(result.out, "no valid sheet owner", "ownership failure")
        check(not output.exists(), "failed render left a PDF behind")
    finally:
        tmp.cleanup()


@test("tall sheets select portrait fit without changing schematic coordinates")
def t_portrait_fit():
    circuit = component(0) + component(1)
    for element in circuit:
        if element.get("schematic_component_id") == "schematic_component_1":
            point = element.get("center") or element.get("position")
            if point:
                point["x"] = 0
                point["y"] = 10
    tmp, output, result, source_before, source_after = render(circuit)
    try:
        check(result.rc == 0, result.out)
        contains(result.out, "portrait", "portrait page-fit disclosure")
        check(source_before == source_after, "renderer modified portrait input")
        info = run(["pdfinfo", str(output)])
        contains(info.out, "607.5 x 900 pts", "portrait A-series aspect")
    finally:
        tmp.cleanup()


@test("zero-component input is a hard failure, never an empty pass", kind="known_bad")
def t_zero_components():
    tmp, output, result, _, _ = render([])
    try:
        check(result.rc != 0, "zero-component input passed")
        contains(result.out, "zero schematic components", "zero-component failure")
        check(not output.exists(), "failed render left a PDF behind")
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    sys.exit(main())
