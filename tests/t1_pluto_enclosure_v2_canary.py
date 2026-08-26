#!/usr/bin/env python3
"""Project canary for Pluto RX2 8-way v5 schema-v2 enclosure replay."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

from harness import check, eq, main, must_fail, must_pass, run, test, tmpdir


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "pluto-rx2-8way-v5"
MECHANICAL = PROJECT / "03_src" / "mechanical"
V2 = ROOT / "skills" / "pcb-enclosure" / "scripts" / "enclosure_v2.py"
KPY = "/usr/bin/python3"
CONFIG = MECHANICAL / "enclosure-v2.yaml"
INTENT = MECHANICAL / "mechanical-intent-v2.yaml"


def _validate_config(path: Path = CONFIG):
    return run([KPY, V2, "validate-config", path, "--root", PROJECT])


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
        "shell": "CAD_READY",
        "board_retention": "CAD_READY",
        "antenna_accessory": "INCOMPLETE",
        "thermal": "PRINT_VERIFIED",
    })
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
