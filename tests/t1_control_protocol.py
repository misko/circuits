#!/usr/bin/env python3
"""T1: observable timing must be derived from one atomic state schedule."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import KPY, SCRIPTS, contains, main, must_fail, must_pass, run, test, tmpdir  # noqa: E402

GATE = SCRIPTS / "control_protocol_check.py"
CODEGEN = SCRIPTS / "control_profile_codegen.py"


def clean_data():
    return {
        "schema": 1,
        "protocol": "framed_unique_dwell_v1",
        "clock": {
            "manufacturer_error_full_temperature_pct": [-2.5, 2.0],
            "decoder_window_pct": 5,
        },
        "states": {
            "ALL_OFF": {"gpio_PA3_PA2_PA1_PA0": "1000"},
            "ANT1": {"gpio_PA3_PA2_PA1_PA0": "0000", "dwell_ms": 80,
                     "window_ms": [76, 84]},
            "ANT2": {"gpio_PA3_PA2_PA1_PA0": "0100", "dwell_ms": 120,
                     "window_ms": [114, 126]},
        },
        "frame": {
            "order": ["ANT1", "ANT2"],
            "all_off_guard_ms": 5,
            "guards_per_cycle": 2,
            "marker": {"state": "ALL_OFF", "body_nominal_ms": 500,
                       "contiguous_pre_ANT1_guard_ms": 5,
                       "observable_nominal_ms": 505, "decoder_min_ms": 475},
            "nominal_cycle_ms": 710,
            "recommended_capture_ms": 1500,
            "minimum_capture_for_guaranteed_complete_frame_ms": 1420,
        },
        "decoder": {
            "reject_to_unknown": ["no_observable_signal", "truncated_capture",
                                  "ambiguous_duration", "invalid_order",
                                  "no_valid_marker"],
        },
    }


def project(data=None):
    d = tmpdir("control_protocol_")
    rules = d / "03_src" / "rules"
    rules.mkdir(parents=True)
    (rules / "control_protocol.yaml").write_text(
        yaml.safe_dump(data or clean_data(), sort_keys=False))
    return d


def profile_data():
    data = clean_data()
    data["schema"] = 2
    data["profile"] = {
        "id": "fast-test",
        "revision": 1,
        "source_of_truth": "03_src/rules/control_protocol.yaml",
        "firmware_header": "05_firmware/include/control_profile.h",
        "decoder_json": "05_firmware/host/control_profile.json",
        "change_method": "regenerate_validate_build_flash",
    }
    return data


@test("observable marker, windows, cycle and capture derive cleanly")
def t_clean():
    r = must_pass(run([KPY, GATE, project()]), "clean timing protocol")
    contains(r.out, "observable marker 505ms", "merged marker duration")
    contains(r.out, "2/2 active states", "coverage denominator")


@test("a 500ms body plus same-state 5ms guard cannot be declared 500ms",
      kind="known_bad")
def t_adjacent_same_state_is_merged():
    data = clean_data()
    data["frame"]["marker"]["observable_nominal_ms"] = 500
    r = must_fail(run([KPY, GATE, project(data)]), "unmerged marker", "505ms")
    contains(r.out, "merges", "diagnosis names observable-state merging")


@test("overlapping dwell windows are rejected", kind="known_bad")
def t_overlapping_windows():
    data = clean_data()
    data["states"]["ANT2"]["dwell_ms"] = 85
    data["states"]["ANT2"]["window_ms"] = [80.75, 89.25]
    must_fail(run([KPY, GATE, project(data)]), "overlapping dwell windows",
              "overlap/touch")


@test("handwritten cycle and minimum capture drift are rejected",
      kind="known_bad")
def t_derived_timing_drift():
    data = clean_data()
    data["frame"]["nominal_cycle_ms"] = 700
    data["frame"]["minimum_capture_for_guaranteed_complete_frame_ms"] = 1400
    r = must_fail(run([KPY, GATE, project(data)]), "derived timing drift",
                  "derived 710ms")
    contains(r.out, "2 cycles=1420ms", "capture is derived from the cycle")


@test("no-signal and truncated observations must decode unknown",
      kind="known_bad")
def t_unknown_failure_states_required():
    data = clean_data()
    data["decoder"]["reject_to_unknown"].remove("no_observable_signal")
    must_fail(run([KPY, GATE, project(data)]), "missing unknown outcome",
              "no_observable_signal")


@test("unknown control-protocol keys fail boundedly before generation",
      kind="known_bad")
def t_unknown_key_is_a_schema_error():
    data = clean_data()
    data["protcol"] = "typo"
    result = must_fail(run([KPY, GATE, project(data)]),
                       "unknown protocol key", "unknown key(s): protcol")
    if "Traceback" in result.out:
        raise AssertionError(f"schema failure leaked a traceback:\n{result.out}")


@test("schema-2 profile generates exact MCU and decoder artifacts")
def t_profile_codegen():
    d = project(profile_data())
    must_pass(run([KPY, CODEGEN, d, "--write"]), "write profile artifacts")
    r = must_pass(run([KPY, CODEGEN, d, "--check"]), "check profile artifacts")
    contains(r.out, "2/2 artifacts exact", "both consumers are pinned")
    contains((d / "05_firmware/include/control_profile.h").read_text(),
             "CONTROL_PROFILE_ID \"fast-test\"", "firmware profile identity")


@test("a changed dwell makes generated timing artifacts stale", kind="known_bad")
def t_profile_stale_after_dwell_change():
    d = project(profile_data())
    must_pass(run([KPY, CODEGEN, d, "--write"]), "initial profile generation")
    path = d / "03_src/rules/control_protocol.yaml"
    data = yaml.safe_load(path.read_text())
    data["states"]["ANT1"]["dwell_ms"] = 81
    data["states"]["ANT1"]["window_ms"] = [76.95, 85.05]
    data["frame"]["nominal_cycle_ms"] = 711
    data["frame"]["minimum_capture_for_guaranteed_complete_frame_ms"] = 1422
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    must_fail(run([KPY, CODEGEN, d, "--check"]), "stale profile", "STALE")


@test("profile consumers cannot collide with or overwrite their authority", kind="known_bad")
def t_profile_output_collision():
    data = profile_data()
    d = project(data)
    authority = d / "03_src/rules/control_protocol.yaml"
    header = d / data["profile"]["firmware_header"]
    header.parent.mkdir(parents=True)
    header.hardlink_to(authority)
    before = authority.read_bytes()
    result = must_fail(
        run([KPY, CODEGEN, d, "--write"]),
        "profile output collision", "must not overwrite")
    if authority.read_bytes() != before:
        raise AssertionError(f"failed codegen changed its authority:\n{result.out}")


@test("profile source-of-truth spelling is canonical", kind="known_bad")
def t_profile_source_path():
    data = profile_data()
    data["profile"]["source_of_truth"] = "control_protocol.yaml"
    must_fail(run([KPY, GATE, project(data)]),
              "noncanonical profile authority", "canonical project path")


if __name__ == "__main__":
    sys.exit(main())
