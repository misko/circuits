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
        "shell": "INCOMPLETE",
        "board_retention": "CAD_READY",
        "antenna_accessory": "INCOMPLETE",
        "thermal": "PRINT_VERIFIED",
    })
    eq(report["service_envelope_coverage"], {
        "legacy_omitted": False,
        "legacy_readiness_capped": False,
        "declared": 0,
        "shared_mappings": 4,
        "shared_non_enclosure_refs": 0,
        "shared_receipt_status": "INCOMPLETE",
        "required_edge_openings": 12,
        "candidate_dimension_census_complete": 0,
    })
    interface = Path(report["bindings"]["interface"]["path"])
    check("06_build" not in interface.parts,
          "v2 interface authority must not depend on ignored build output")
    check(interface.is_relative_to(PROJECT / "07_enclosure_releases"),
          "v2 interface must reopen from the sealed enclosure stream")
    receipt = Path(report["bindings"]["connector_assembly_receipt"]["path"])
    check("06_build" not in receipt.parts,
          "connector authority must not depend on ignored build output")
    check(receipt.is_relative_to(PROJECT / "07_enclosure_releases"),
          "connector receipt must reopen from the sealed enclosure stream")

    original = yaml.safe_load((MECHANICAL / "enclosure.yaml").read_text())
    adapter = yaml.safe_load(
        (MECHANICAL / "enclosure-cad-design-v2.yaml").read_text())
    original["subject"]["interface"] = adapter["subject"]["interface"]
    eq(adapter, original,
       "v2 CAD adapter should differ only by its replay-stable interface binding")


@test("Pluto v5 canonical connector receipt covers every J1-J12 interface")
def t_pluto_v2_shared_connector_receipt():
    value = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    shared = value["interface_assemblies"]
    binding = shared["receipt"]
    receipt_path = PROJECT / binding["path"]
    check(receipt_path.is_relative_to(PROJECT / "07_enclosure_releases"),
          "canonical connector receipt is immutable release evidence")
    eq(binding["sha256"], _sha(receipt_path), "receipt binding hash")
    eq(binding["size"], receipt_path.stat().st_size,
       "receipt binding size")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    eq(receipt["status"], "INCOMPLETE",
       "unknown service facts remain fail-closed")
    eq(receipt["summary"], {
        "assembly_count": 4,
        "instance_count": 12,
        "operation_count": 8,
        "simultaneous_group_count": 4,
        "tolerance_count": 6,
        "evidence_total": 50,
        "evidence_exact": 2,
        "evidence_conservative": 0,
        "evidence_unknown": 48,
        "evidence_ceiling": "UNKNOWN",
        "evidence_file_count": 7,
    })
    eq(receipt["inputs"]["compiler"], {
        "path": CONNECTOR_COMPILER.relative_to(ROOT).as_posix(),
        "sha256": _sha(CONNECTOR_COMPILER),
        "size": CONNECTOR_COMPILER.stat().st_size,
    }, "canonical compiler binding")
    eq(receipt["inputs"]["contract"], {
        "path": CONNECTOR_CONTRACT.relative_to(PROJECT).as_posix(),
        "sha256": _sha(CONNECTOR_CONTRACT),
        "size": CONNECTOR_CONTRACT.stat().st_size,
    }, "canonical project contract binding")
    for row in receipt["inputs"]["evidence_files"]:
        evidence = PROJECT / row["path"]
        eq(row["sha256"], _sha(evidence), f"{row['id']} evidence hash")
        eq(row["size"], evidence.stat().st_size,
           f"{row['id']} evidence size")

    receipt_refs = {
        instance["ref"]
        for assembly in receipt["assemblies"]
        for instance in assembly["instances"]
    }
    eq(receipt_refs, {f"J{index}" for index in range(1, 13)},
       "receipt connector census")
    receipt_groups = {row["id"] for row in receipt["simultaneous_groups"]}
    eq(receipt_groups, {
        "all-sma-service", "usb-c-service", "swd-service",
        "bench-power-service",
    })
    eq({row["group_id"] for row in shared["group_state_bindings"]},
       receipt_groups, "every service group has an enclosure state")
    eq(shared["non_enclosure_refs"], [],
       "all receipt connectors require enclosure coverage")

    cad = yaml.safe_load(CAD_DESIGN.read_text(encoding="utf-8"))
    required = {
        row["id"]: row["ref"] for row in cad["interfaces"]
        if row["disposition"] in {"opening", "service_opening"}
    }
    mapped_ids = {
        interface_id
        for mapping in shared["mappings"]
        for interface_id in mapping["interface_ids"]
    }
    eq(mapped_ids, set(required), "all connector openings are mapped")
    eq(set(required.values()), receipt_refs,
       "mapped CAD openings cover the receipt connector census")
    eq({row["scope"] for row in shared["mappings"]}, {"shell"},
       "all connector service limits the shell scope")
    check(any(row["id"] == "connector_cable_service"
              for row in value["physical_tests"]),
          "connector cable-service physical test remains required")


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


@test("Pluto v5 cannot omit one canonical connector opening",
      kind="known_bad", gate="enclosure_v2.py")
def t_pluto_v2_connector_opening_omission_bites():
    value = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    value["interface_assemblies"]["mappings"][0]["interface_ids"].remove(
        "ant8-sma")
    broken = tmpdir("pluto_enclosure_v2_missing_connector_") / \
        "enclosure-v2.yaml"
    broken.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    must_fail(_validate_config(broken), "Pluto omitted connector opening",
              "coverage must equal every connector/service opening")


@test("Pluto v5 cannot substitute the canonical connector receipt binding",
      kind="known_bad", gate="enclosure_v2.py")
def t_pluto_v2_connector_receipt_binding_bites():
    value = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    value["interface_assemblies"]["receipt"]["sha256"] = "0" * 64
    broken = tmpdir("pluto_enclosure_v2_bad_connector_receipt_") / \
        "enclosure-v2.yaml"
    broken.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    must_fail(_validate_config(broken), "Pluto substituted connector receipt",
              "bound size/hash differs from actual file")


if __name__ == "__main__":
    sys.exit(main())
