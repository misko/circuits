#!/usr/bin/env python3
"""Project canary for Pluto RX2 8-way v5 schema-v2 enclosure replay."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from harness import check, eq, main, must_fail, must_pass, run, test, tmpdir


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "pluto-rx2-8way-v5"
MECHANICAL = PROJECT / "03_src" / "mechanical"
V2 = ROOT / "skills" / "pcb-enclosure" / "scripts" / "enclosure_v2.py"
CONNECTOR_COMPILER = (ROOT / "skills" / "pcb-design" / "scripts" /
                      "connector_assembly_contract.py")
KPY = "/usr/bin/python3"
CONFIG = MECHANICAL / "enclosure-v2.yaml"
INTENT = MECHANICAL / "mechanical-intent-v2.yaml"
FABRICATED_RELEASE = PROJECT / "07_releases" / "v0.2.1-2026-08-14"
FABRICATED_BOARD = FABRICATED_RELEASE / "source" / \
    "pluto_rx2_8way_v5.kicad_pcb"
CONNECTOR_CONTRACT = PROJECT / "03_src" / "rules" / \
    "connector_assemblies.yaml"
CAD_DESIGN = MECHANICAL / "enclosure-cad-design-v2.yaml"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sexpr_blocks(text: str, form: str) -> list[str]:
    """Return complete KiCad s-expression blocks for one top-level form."""
    marker = f"({form}"
    blocks: list[str] = []
    cursor = 0
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            return blocks
        depth = 0
        quoted = False
        escaped = False
        for end in range(start, len(text)):
            char = text[end]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    blocks.append(text[start:end + 1])
                    cursor = end + 1
                    break
        else:
            raise AssertionError(f"unterminated ({form} ...) block")


def _fabricated_footprint_origins() -> dict[str, tuple[float, float]]:
    text = FABRICATED_BOARD.read_text(encoding="utf-8")
    result: dict[str, tuple[float, float]] = {}
    for block in _sexpr_blocks(text, "footprint"):
        reference = re.search(r'\(property\s+"Reference"\s+"(J[0-9]+)"',
                              block)
        origin = re.search(
            r'^\s*\(at\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)(?:\s|\))',
            block, re.MULTILINE)
        if reference and origin:
            result[reference.group(1)] = (
                float(origin.group(1)), float(origin.group(2)))
    return result


def _validate_config(path: Path = CONFIG):
    return run([KPY, V2, "validate-config", path, "--root", PROJECT])


@test("Pluto connector axes follow the exact fabricated board convention")
def t_pluto_fabricated_board_connector_axes():
    manifest = FABRICATED_RELEASE / "MANIFEST.txt"
    manifest_row = re.search(
        r"^\s*source/pluto_rx2_8way_v5\.kicad_pcb\s+([0-9a-f]{64})$",
        manifest.read_text(encoding="utf-8"), re.MULTILINE)
    check(manifest_row is not None, "fabricated board manifest row")
    eq(_sha(FABRICATED_BOARD), manifest_row.group(1),
       "exact fabricated board binding")

    board_text = FABRICATED_BOARD.read_text(encoding="utf-8")
    edge_points: list[tuple[float, float]] = []
    for block in _sexpr_blocks(board_text, "gr_line"):
        if '(layer "Edge.Cuts")' not in block:
            continue
        for match in re.finditer(
                r"\((?:start|end)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\)",
                block):
            edge_points.append((float(match.group(1)), float(match.group(2))))
    check(edge_points, "fabricated board Edge.Cuts points")
    north_y = min(point[1] for point in edge_points)
    south_y = max(point[1] for point in edge_points)

    contract = yaml.safe_load(CONNECTOR_CONTRACT.read_text(encoding="utf-8"))
    axes = {
        instance["ref"]: instance["mating_axis_board"]
        for assembly in contract["assemblies"]
        for instance in assembly["instances"]
    }
    sma = next(row for row in contract["assemblies"]
               if row["id"] == "amphenol-901-143-6rfx-v5-bank")
    offset = sma["interface"]["mating_plane_offset_mm"]
    origins = _fabricated_footprint_origins()
    north_refs = ("J2", "J3", "J4", "J9", "J10")
    for ref in north_refs:
        eq(axes[ref], [0.0, -1.0, 0.0], f"{ref} north/min-Y axis")
        eq(origins[ref][1] + axes[ref][1] * offset, north_y,
           f"{ref} mating plane reaches exact north Edge.Cuts")
    eq(axes["J1"], [0.0, 1.0, 0.0], "J1 south/max-Y axis")
    check(origins["J1"][1] > (north_y + south_y) / 2,
          "J1 lies on fabricated board's south half")

    interfaces = {
        row["ref"]: row["side"]
        for row in yaml.safe_load(CAD_DESIGN.read_text(encoding="utf-8"))
        ["interfaces"]
    }
    for ref in north_refs:
        eq(interfaces[ref], "north", f"{ref} enclosure side")
    eq(interfaces["J1"], "south", "J1 enclosure side")


@test("Pluto v5 mechanical intent makes lid-off retention and prewired loading explicit")
def t_pluto_v2_intent():
    report = json.loads(must_pass(run([
        KPY, V2, "validate-intent", INTENT,
    ]), "Pluto v2 intent").out)
    eq(report["status"], "VALID")


@test("Pluto v5 v2 config reopens only committed immutable authorities")
def t_pluto_v2_clean_clone_replay():
    report = json.loads(must_pass(
        _validate_config(), "Pluto v2 config").out)
    eq(report["status"], "VALID")
    eq(report["scope_readiness_ceilings"], {
        # This published config predates the shared connector-service receipt.
        # Structural replay remains valid, but edge openings cannot retain a
        # readiness claim merely because the new additive authority is absent.
        "shell": "INCOMPLETE",
        "board_retention": "INCOMPLETE",
        "antenna_accessory": "INCOMPLETE",
        "thermal": "INCOMPLETE",
    })
    eq(report["service_envelope_coverage"]["legacy_omitted"], True)
    eq(report["service_envelope_coverage"]["legacy_readiness_capped"], True)
    interface = Path(report["bindings"]["interface"]["path"])
    check("06_build" not in interface.parts,
          "v2 interface authority must not depend on ignored build output")
    check(interface.is_relative_to(PROJECT / "07_enclosure_releases"),
          "v2 interface must reopen from the sealed enclosure stream")

    original = yaml.safe_load((MECHANICAL / "enclosure.yaml").read_text())
    adapter = yaml.safe_load(
        (MECHANICAL / "enclosure-cad-design-v2.yaml").read_text())
    original["subject"]["interface"] = adapter["subject"]["interface"]
    eq(adapter, original,
       "v2 CAD adapter should differ only by its replay-stable interface binding")


@test("Pluto v5 shared connector overlay covers every J1-J12 enclosure interface")
def t_pluto_v2_shared_connector_overlay():
    receipt_relative = Path(
        "06_build/verification/t1_pluto_connector_assembly_contract.json")
    receipt_path = PROJECT / receipt_relative
    result = run([
        KPY, CONNECTOR_COMPILER, "--project", PROJECT,
        "--output", receipt_relative,
    ])
    eq(result.rc, 2, "honest incomplete connector-contract exit")
    try:
        value = yaml.safe_load(CONFIG.read_text())
        value["interface_assemblies"] = {
            "receipt": {
                "path": receipt_relative.as_posix(),
                "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                "size": receipt_path.stat().st_size,
            },
            "non_enclosure_refs": [],
            "mappings": [
                {
                    "id": "sma-bank",
                    "assembly_id": "amphenol-901-143-6rfx-v5-bank",
                    "interface_ids": [
                        "rx-sma", "ant1-sma", "ant2-sma", "ant3-sma",
                        "ant4-sma", "ant5-sma", "ant6-sma", "ant7-sma",
                        "ant8-sma",
                    ],
                    "scope": "shell",
                    "mated_in_states": ["installed"],
                    "mated_during_operations": [],
                },
                {
                    "id": "usb-c",
                    "assembly_id": "gct-usb4105-power-service",
                    "interface_ids": ["usb-c-power"],
                    "scope": "shell",
                    "mated_in_states": ["installed"],
                    "mated_during_operations": [],
                },
                {
                    "id": "swd",
                    "assembly_id": "samtec-swd-service",
                    "interface_ids": ["swd-service"],
                    "scope": "shell",
                    "mated_in_states": ["installed"],
                    "mated_during_operations": [],
                },
                {
                    "id": "bench-power",
                    "assembly_id": "cjt-bench-power-service",
                    "interface_ids": ["bench-power-service"],
                    "scope": "shell",
                    "mated_in_states": ["installed"],
                    "mated_during_operations": [],
                },
            ],
            "group_state_bindings": [
                {"group_id": group, "enclosure_state_ids": ["installed"]}
                for group in (
                    "all-sma-service", "usb-c-service", "swd-service",
                    "bench-power-service",
                )
            ],
        }
        value["physical_tests"].append({
            "id": "connector_cable_service",
            "type": "cable_strain_clearance",
            "scope": "shell",
            "required_for": "PRINT_VERIFIED",
            "subject_parts": ["base", "lid", "pcb"],
        })
        overlay = tmpdir("pluto_enclosure_v2_connector_overlay_") / \
            "enclosure-v2.yaml"
        overlay.write_text(yaml.safe_dump(value, sort_keys=False),
                           encoding="utf-8")
        report = json.loads(must_pass(
            _validate_config(overlay), "Pluto connector overlay").out)
        eq(report["service_envelope_coverage"]["shared_mappings"], 4)
        eq(report["service_envelope_coverage"]["shared_non_enclosure_refs"],
           0)
        eq(report["service_envelope_coverage"]["required_edge_openings"], 12)
        eq(report["service_envelope_coverage"]["shared_receipt_status"],
           "INCOMPLETE")
        eq(report["scope_readiness_ceilings"]["shell"], "INCOMPLETE")
    finally:
        receipt_path.unlink(missing_ok=True)


@test("Pluto v5 aggregate remains incomplete despite optimistic CAD inputs")
def t_pluto_v2_honest_aggregate():
    payload = tmpdir("pluto_enclosure_v2_") / "scope-statuses.json"
    payload.write_text(json.dumps({"scope_statuses": {
        "shell": "CAD_READY",
        "board_retention": "CAD_READY",
        "antenna_accessory": "CAD_READY",
        "thermal": "CAD_READY",
    }}) + "\n", encoding="utf-8")
    result = run([
        KPY, V2, "aggregate-config", payload, "--config", CONFIG,
        "--root", PROJECT,
    ])
    eq(result.rc, 2, "honest incomplete aggregate exit status")
    report = json.loads(result.out)
    eq(report["status"], "INCOMPLETE")
    eq(set(report["required_scopes"]),
       {"shell", "board_retention", "antenna_accessory", "thermal"})
    eq(report["scope_readiness_ceilings"]["antenna_accessory"],
       "INCOMPLETE")


@test("Pluto v0.4 legacy enclosure evidence reopens with an exact payload census")
def t_pluto_v04_legacy_evidence_census():
    release = PROJECT / "07_enclosure_releases" / "v0.4.0-2026-08-25"
    manifest = json.loads((release / "MANIFEST.json").read_text())
    rows = {row["path"]: row for row in manifest["payloads"]}
    files = {
        path.relative_to(release).as_posix()
        for path in release.rglob("*")
        if path.is_file() and path.name != "MANIFEST.json"
    }
    eq(manifest["payload_count"], 34)
    eq(set(rows), files, "legacy v0.4 payload census")
    for relative, row in rows.items():
        path = release / relative
        eq(path.stat().st_size, row["size"], f"{relative} size")
        eq(hashlib.sha256(path.read_bytes()).hexdigest(), row["sha256"],
           f"{relative} hash")
    eq(manifest["status"], "INCOMPLETE")
    eq(manifest["shell_status"], "CAD_READY")
    eq(manifest["antenna_accessory_status"], "INCOMPLETE")
    check(not manifest["publication"]["order_ready"],
          "legacy incomplete evidence must not authorize ordering")


@test("Pluto v5 board and case screws cannot share an axis",
      kind="known_bad", gate="enclosure_v2.py")
def t_pluto_v2_shared_fastener_axis_bites():
    value = yaml.safe_load(CONFIG.read_text())
    value["fastener_groups"][1]["axes"][0]["origin_mm"] = \
        value["fastener_groups"][0]["axes"][0]["origin_mm"]
    broken = tmpdir("pluto_enclosure_v2_bad_axis_") / "enclosure-v2.yaml"
    broken.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    must_fail(_validate_config(broken), "Pluto shared fastener axis",
              "axes overlap")


@test("Pluto v5 prewired antenna cannot be graded with cable-only clearance",
      kind="known_bad", gate="enclosure_v2.py")
def t_pluto_v2_cable_only_opening_bites():
    value = yaml.safe_load(CONFIG.read_text())
    value["clearance_cases"][0]["envelope_basis"] = "cable_only"
    broken = tmpdir("pluto_enclosure_v2_cable_only_") / "enclosure-v2.yaml"
    broken.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    must_fail(_validate_config(broken), "Pluto cable-only antenna opening",
              "requires full_part")


if __name__ == "__main__":
    sys.exit(main())
