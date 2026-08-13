#!/usr/bin/env python3
"""Validate timing-coded control protocols from their atomic state schedule.

The downstream observer sees contiguous runs of electrical states, not prose
labels such as "marker body" and "guard".  This source-only gate recomputes
observable marker duration, active-state windows, cycle duration and minimum
capture from ``03_src/rules/control_protocol.yaml``.

Exit 0 = pass or explicit N-A (no protocol file), 1 = violated timing claim,
2 = malformed/ungradeable input.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import yaml


class ProtocolError(ValueError):
    pass


def mapping(value, label):
    if not isinstance(value, dict):
        raise ProtocolError(f"{label} must be a mapping")
    return value


def reject_unknown(value, allowed, label):
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ProtocolError(f"{label} has unknown key(s): {', '.join(unknown)}")


def sequence(value, label, minimum=1):
    if not isinstance(value, list) or len(value) < minimum:
        raise ProtocolError(f"{label} must be a list with >= {minimum} item(s)")
    return value


def number(value, label, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) \
            or not math.isfinite(float(value)):
        raise ProtocolError(f"{label} must be a finite number")
    value = float(value)
    if positive and value <= 0:
        raise ProtocolError(f"{label} must be > 0")
    return value


def close(got, want, *, tolerance=1e-6):
    return math.isclose(float(got), float(want), rel_tol=0, abs_tol=tolerance)


def load(path: Path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ProtocolError(f"cannot read {path}: {exc}") from exc
    root = mapping(data, "control protocol root")
    reject_unknown(root, {
        "schema", "protocol", "clock", "states", "frame",
        "firmware_sequence", "decoder",
    }, "control protocol root")
    if root.get("schema") != 1:
        raise ProtocolError("control protocol schema must be integer 1")
    if not isinstance(root.get("protocol"), str) or not root["protocol"].strip():
        raise ProtocolError("protocol must be a non-empty identifier")
    return root


def grade(data):
    failures = []
    clock = mapping(data.get("clock"), "clock")
    reject_unknown(clock, {
        "source", "manufacturer_error_full_temperature_pct",
        "decoder_window_pct", "rationale",
    }, "clock")
    error = sequence(clock.get("manufacturer_error_full_temperature_pct"),
                     "clock.manufacturer_error_full_temperature_pct", 2)
    if len(error) != 2:
        raise ProtocolError(
            "clock.manufacturer_error_full_temperature_pct must be [low, high]")
    error_low = number(error[0], "clock error low")
    error_high = number(error[1], "clock error high")
    if error_low > error_high:
        raise ProtocolError("clock error bounds must be ordered low..high")
    window_pct = number(clock.get("decoder_window_pct"),
                        "clock.decoder_window_pct", positive=True)
    if window_pct >= 50:
        raise ProtocolError("clock.decoder_window_pct must be < 50")
    if window_pct <= max(abs(error_low), abs(error_high)):
        failures.append(
            f"decoder window {window_pct:g}% does not exceed the full-"
            f"temperature controller error [{error_low:g}, {error_high:g}]%")

    states = mapping(data.get("states"), "states")
    all_off = mapping(states.get("ALL_OFF"), "states.ALL_OFF")
    reject_unknown(all_off, {
        "gpio_PA3_PA2_PA1_PA0", "u1_V4_V3_V2_V1",
    }, "states.ALL_OFF")
    code_key = "gpio_PA3_PA2_PA1_PA0"
    all_off_code = str(all_off.get(code_key) or "")
    if not re.fullmatch(r"[01]+", all_off_code):
        raise ProtocolError(f"states.ALL_OFF.{code_key} must be a binary word")

    frame = mapping(data.get("frame"), "frame")
    reject_unknown(frame, {
        "order", "all_off_guard_ms", "guards_per_cycle", "marker",
        "nominal_cycle_ms", "recommended_capture_ms",
        "minimum_capture_for_guaranteed_complete_frame_ms",
    }, "frame")
    order = sequence(frame.get("order"), "frame.order")
    if len(set(map(str, order))) != len(order):
        raise ProtocolError("frame.order must contain unique state names")
    guard = number(frame.get("all_off_guard_ms"),
                   "frame.all_off_guard_ms", positive=True)
    guards = frame.get("guards_per_cycle")
    if guards != len(order):
        failures.append(
            f"guards_per_cycle={guards!r}, derived {len(order)} from frame.order")

    windows = []
    dwell_total = 0.0
    codes = {all_off_code}
    for index, raw_name in enumerate(order):
        name = str(raw_name)
        if name == "ALL_OFF":
            raise ProtocolError("frame.order contains ALL_OFF as an active state")
        state = mapping(states.get(name), f"states.{name}")
        reject_unknown(state, {
            "gpio_PA3_PA2_PA1_PA0", "u1_V4_V3_V2_V1", "dwell_ms",
            "window_ms",
        }, f"states.{name}")
        code = str(state.get(code_key) or "")
        if not re.fullmatch(r"[01]+", code):
            raise ProtocolError(f"states.{name}.{code_key} must be a binary word")
        if code in codes:
            failures.append(f"states.{name} reuses observable control word {code}")
        codes.add(code)
        dwell = number(state.get("dwell_ms"), f"states.{name}.dwell_ms",
                       positive=True)
        win = sequence(state.get("window_ms"), f"states.{name}.window_ms", 2)
        if len(win) != 2:
            raise ProtocolError(f"states.{name}.window_ms must be [low, high]")
        low = number(win[0], f"states.{name}.window_ms[0]", positive=True)
        high = number(win[1], f"states.{name}.window_ms[1]", positive=True)
        if low >= high:
            raise ProtocolError(f"states.{name}.window_ms must be ordered")
        expected = (dwell * (1 - window_pct / 100),
                    dwell * (1 + window_pct / 100))
        if not close(low, expected[0]) or not close(high, expected[1]):
            failures.append(
                f"{name} window [{low:g}, {high:g}]ms != derived "
                f"{window_pct:g}% window [{expected[0]:g}, {expected[1]:g}]ms")
        windows.append((low, high, name))
        dwell_total += dwell

    by_low = sorted(windows)
    for left, right in zip(by_low, by_low[1:]):
        if left[1] >= right[0]:
            failures.append(
                f"active windows overlap/touch: {left[2]} ends {left[1]:g}ms, "
                f"{right[2]} starts {right[0]:g}ms")

    marker = mapping(frame.get("marker"), "frame.marker")
    reject_unknown(marker, {
        "state", "body_nominal_ms", "contiguous_pre_ANT1_guard_ms",
        "observable_nominal_ms", "decoder_min_ms",
    }, "frame.marker")
    if marker.get("state") != "ALL_OFF":
        raise ProtocolError("frame.marker.state must be ALL_OFF")
    body = number(marker.get("body_nominal_ms"),
                  "frame.marker.body_nominal_ms", positive=True)
    contiguous = number(marker.get("contiguous_pre_ANT1_guard_ms"),
                        "frame.marker.contiguous_pre_ANT1_guard_ms",
                        positive=True)
    if not close(contiguous, guard):
        failures.append(
            f"marker contiguous guard {contiguous:g}ms != frame guard {guard:g}ms")
    observable = body + guard
    declared_observable = number(marker.get("observable_nominal_ms"),
                                 "frame.marker.observable_nominal_ms",
                                 positive=True)
    if not close(declared_observable, observable):
        failures.append(
            f"marker observable_nominal_ms={declared_observable:g}, but "
            f"adjacent ALL_OFF body {body:g}ms + guard {guard:g}ms merges to "
            f"{observable:g}ms")
    decoder_min = number(marker.get("decoder_min_ms"),
                         "frame.marker.decoder_min_ms", positive=True)
    active_high = max(high for _, high, _ in windows)
    if decoder_min <= active_high:
        failures.append(
            f"marker decoder_min {decoder_min:g}ms is not above longest active "
            f"window {active_high:g}ms")
    marker_worst_low = observable * (1 + error_low / 100)
    if decoder_min > marker_worst_low:
        failures.append(
            f"marker decoder_min {decoder_min:g}ms exceeds worst-low observable "
            f"marker {marker_worst_low:g}ms")

    cycle = body + len(order) * guard + dwell_total
    declared_cycle = number(frame.get("nominal_cycle_ms"),
                            "frame.nominal_cycle_ms", positive=True)
    if not close(declared_cycle, cycle):
        failures.append(
            f"nominal_cycle_ms={declared_cycle:g}, derived {cycle:g}ms from "
            "marker body + guards + active dwells")
    guaranteed = 2 * cycle
    declared_min = number(frame.get("minimum_capture_for_guaranteed_complete_frame_ms"),
                          "frame.minimum_capture_for_guaranteed_complete_frame_ms",
                          positive=True)
    if not close(declared_min, guaranteed):
        failures.append(
            f"minimum guaranteed capture={declared_min:g}ms, derived "
            f"2 cycles={guaranteed:g}ms")
    recommended = number(frame.get("recommended_capture_ms"),
                         "frame.recommended_capture_ms", positive=True)
    if recommended < guaranteed:
        failures.append(
            f"recommended capture {recommended:g}ms is below guaranteed "
            f"complete-frame minimum {guaranteed:g}ms")

    decoder = mapping(data.get("decoder"), "decoder")
    reject_unknown(decoder, {
        "sync", "accept", "reject_to_unknown", "fundamental_limit",
    }, "decoder")
    reject = set(map(str, sequence(decoder.get("reject_to_unknown"),
                                   "decoder.reject_to_unknown")))
    required_unknown = {
        "no_observable_signal", "truncated_capture", "ambiguous_duration",
        "invalid_order", "no_valid_marker",
    }
    missing_unknown = sorted(required_unknown - reject)
    if missing_unknown:
        failures.append(
            "decoder.reject_to_unknown omits " + ", ".join(missing_unknown))

    firmware = data.get("firmware_sequence")
    if firmware is not None:
        for index, step in enumerate(sequence(
                firmware, "firmware_sequence")):
            if not isinstance(step, str) or not step.strip():
                raise ProtocolError(
                    f"firmware_sequence[{index}] must be a non-empty string")
    for key in ("source", "rationale"):
        if key in clock and (not isinstance(clock[key], str)
                             or not clock[key].strip()):
            raise ProtocolError(f"clock.{key} must be a non-empty string")
    for key in ("sync", "accept", "fundamental_limit"):
        if key in decoder and (not isinstance(decoder[key], str)
                               or not decoder[key].strip()):
            raise ProtocolError(f"decoder.{key} must be a non-empty string")

    return failures, {
        "active_states": len(order),
        "windows": len(windows),
        "observable_marker_ms": observable,
        "cycle_ms": cycle,
        "minimum_capture_ms": guaranteed,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("project")
    parser.add_argument("--contract", default="")
    args = parser.parse_args(argv)
    project = Path(args.project).resolve()
    path = (Path(args.contract).resolve() if args.contract else
            project / "03_src" / "rules" / "control_protocol.yaml")
    if not path.is_file():
        print(f"CONTROL-PROTOCOL N-A: no {path}")
        return 0
    try:
        data = load(path)
        failures, summary = grade(data)
    except (ProtocolError, TypeError, KeyError, ValueError) as exc:
        print(f"CONTROL-PROTOCOL LOAD ERROR: 0/1 contracts graded; "
              f"input={path}; {exc}")
        return 2
    print(f"input: {path}")
    if failures:
        print(f"CONTROL-PROTOCOL FAIL: {len(failures)} finding(s); "
              f"{summary['active_states']}/{summary['active_states']} active "
              "states parsed")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"CONTROL-PROTOCOL PASS: {summary['active_states']}/"
          f"{summary['active_states']} active states and {summary['windows']}/"
          f"{summary['windows']} windows graded; observable marker "
          f"{summary['observable_marker_ms']:g}ms; cycle "
          f"{summary['cycle_ms']:g}ms; guaranteed capture "
          f"{summary['minimum_capture_ms']:g}ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
