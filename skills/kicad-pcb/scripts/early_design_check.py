#!/usr/bin/env python3
"""Fail-closed commission/parts/schematic design-contract gates.

The PCB pipeline already checked arithmetic once an author supplied numbers,
but it did not prove that the numbers described the user's measurement plane,
that a switching controller could drive the selected MOSFETs, or that a TVS
clamp was compatible with every exposed part.  This checker owns those three
pre-placement decisions:

  D-SPEC / E-PATH  requirements.yaml <-> power_tree.yaml
  E-SWDRV          power_stages.yaml gate-drive/current/thermal compatibility
  E-SURGE          protection_paths.yaml normal and transient ratings

Missing adopted inputs are errors.  Legacy projects need not invoke this
checker until their next material revision; new templates invoke it before
board generation.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment failure is explicit
    yaml = None


class ContractError(ValueError):
    pass


def load_yaml(path: Path, label: str):
    if not path.exists():
        raise ContractError(f"{label}: missing required adopted input {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ContractError(f"{label}: cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"{label}: {path} must contain a YAML mapping")
    if data.get("schema") != 1:
        raise ContractError(f"{label}: {path} requires schema: 1")
    return data


def number(value, where, *, positive=False, nonnegative=False):
    if isinstance(value, bool):
        raise ContractError(f"{where} must be numeric, not boolean")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{where} must be numeric, got {value!r}") from exc
    if not math.isfinite(out):
        raise ContractError(f"{where} must be finite")
    if positive and out <= 0:
        raise ContractError(f"{where} must be > 0")
    if nonnegative and out < 0:
        raise ContractError(f"{where} must be >= 0")
    return out


def text_value(value, where):
    out = str(value or "").strip()
    if not out:
        raise ContractError(f"{where} must be a non-empty string")
    return out


def list_value(value, where):
    if not isinstance(value, list) or not value:
        raise ContractError(f"{where} must be a non-empty list")
    return value


def part_aliases(project: Path):
    aliases = set()
    for path in (project / "02_parts").glob("*/part.yaml"):
        aliases.add(path.parent.name)
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
        except Exception as exc:
            raise ContractError(f"cannot read part dossier {path}: {exc}") from exc
        if isinstance(doc, dict) and doc.get("mpn"):
            aliases.add(str(doc["mpn"]))
    return aliases


def require_part(value, where, aliases):
    part = text_value(value, where)
    if part not in aliases:
        raise ContractError(f"{where} {part!r} does not resolve to 02_parts")
    return part


def ir_values(raw, rail_name):
    if not isinstance(raw, dict) or not raw:
        raise ContractError(
            f"E-PATH rail {rail_name!r} needs non-empty "
            "ir_budget_components_mohm")
    values = {}
    for key, entry in raw.items():
        where = f"rail {rail_name!r} ir_budget_components_mohm.{key}"
        if not isinstance(entry, dict):
            raise ContractError(
                f"E-PATH {where} must be {{value, basis, evidence}}; a bare "
                "number cannot prove worst-case provenance")
        value = number(entry.get("value"), f"{where}.value", nonnegative=True)
        basis = text_value(entry.get("basis"), f"{where}.basis")
        if basis not in {"maximum", "qualified_max", "budgeted_max"}:
            raise ContractError(
                f"E-PATH {where}.basis {basis!r} is not a worst-case basis")
        text_value(entry.get("evidence"), f"{where}.evidence")
        values[str(key)] = value
    return values


PATH_PROFILES = {
    "board_connector": {
        "protection_switch", "pcb_copper_vias_joints", "connector_contacts"
    },
    "mated_test_plug": {
        "protection_switch", "pcb_copper_vias_joints", "mated_power_contacts"
    },
    "load": {
        "protection_switch", "pcb_copper_vias_joints",
        "mated_power_contacts", "cable"
    },
}
PATH_EXCLUSIONS = {
    "board_connector": {"mated_power_contacts", "cable", "appliance"},
    "mated_test_plug": {"cable", "appliance"},
    "load": set(),
}


def check_requirements(project: Path):
    rules = project / "03_src" / "rules"
    req = load_yaml(rules / "requirements.yaml", "D-SPEC")
    power = load_yaml(rules / "power_tree.yaml", "E-PATH")
    claims = req.get("power_claims")
    if not isinstance(claims, list):
        raise ContractError("D-SPEC power_claims must be a list (use [] explicitly)")
    if not claims:
        text_value(req.get("no_external_power_outputs"),
                   "D-SPEC no_external_power_outputs")

    rails = power.get("rails")
    if not isinstance(rails, list):
        raise ContractError("E-PATH power_tree.yaml rails must be a list")
    rail_by_name = {}
    for rail in rails:
        if not isinstance(rail, dict):
            raise ContractError("E-PATH each power_tree rail must be a mapping")
        name = text_value(rail.get("name"), "E-PATH rail.name")
        if name in rail_by_name:
            raise ContractError(f"E-PATH duplicate rail name {name!r}")
        rail_by_name[name] = rail

    seen_claims, claimed_rails, notes = set(), set(), []
    for i, claim in enumerate(claims):
        where = f"D-SPEC power_claims[{i}]"
        if not isinstance(claim, dict):
            raise ContractError(f"{where} must be a mapping")
        cid = text_value(claim.get("id"), f"{where}.id")
        if cid in seen_claims:
            raise ContractError(f"D-SPEC duplicate claim id {cid!r}")
        seen_claims.add(cid)
        names = [text_value(x, f"{where}.rails[]")
                 for x in list_value(claim.get("rails"), f"{where}.rails")]
        count = int(number(claim.get("count"), f"{where}.count", positive=True))
        simult = int(number(claim.get("simultaneous_count"),
                            f"{where}.simultaneous_count", positive=True))
        if count != len(names):
            raise ContractError(
                f"D-SPEC claim {cid!r} count {count} != {len(names)} named rails")
        if simult > count:
            raise ContractError(
                f"D-SPEC claim {cid!r} simultaneous_count {simult} > count {count}")
        current = number(claim.get("current_A"), f"{where}.current_A", positive=True)
        vmin = number(claim.get("voltage_min_V"), f"{where}.voltage_min_V",
                      positive=True)
        vmax = number(claim.get("voltage_max_V"), f"{where}.voltage_max_V",
                      positive=True)
        if vmin >= vmax:
            raise ContractError(f"D-SPEC claim {cid!r} voltage_min_V >= voltage_max_V")
        duty = text_value(claim.get("duty"), f"{where}.duty")
        if duty not in {"continuous", "intermittent"}:
            raise ContractError(f"D-SPEC claim {cid!r} duty must be continuous/intermittent")
        plane = text_value(claim.get("measurement_plane"),
                           f"{where}.measurement_plane")
        if plane not in PATH_PROFILES:
            raise ContractError(
                f"D-SPEC claim {cid!r} measurement_plane {plane!r} is unknown; "
                f"choose one of {sorted(PATH_PROFILES)}")
        text_value(claim.get("boundary_evidence"), f"{where}.boundary_evidence")
        included_raw = claim.get("included_elements")
        excluded_raw = claim.get("excluded_elements")
        if not isinstance(included_raw, list) or not included_raw:
            raise ContractError(f"{where}.included_elements must be a non-empty list")
        if not isinstance(excluded_raw, list):
            raise ContractError(f"{where}.excluded_elements must be a list (use [] explicitly)")
        included = {text_value(x, f"{where}.included_elements[]")
                    for x in included_raw}
        excluded = {text_value(x, f"{where}.excluded_elements[]")
                    for x in excluded_raw}
        overlap = included & excluded
        if overlap:
            raise ContractError(f"D-SPEC claim {cid!r} includes and excludes {sorted(overlap)}")
        missing_boundary = PATH_PROFILES[plane] - included
        if missing_boundary:
            raise ContractError(
                f"D-SPEC claim {cid!r} included_elements omits {sorted(missing_boundary)}")
        missing_exclusions = PATH_EXCLUSIONS[plane] - excluded
        if missing_exclusions:
            raise ContractError(
                f"D-SPEC claim {cid!r} excluded_elements omits {sorted(missing_exclusions)}")

        for name in names:
            if name not in rail_by_name:
                raise ContractError(f"D-SPEC claim {cid!r} names absent rail {name!r}")
            if name in claimed_rails:
                raise ContractError(f"D-SPEC rail {name!r} belongs to multiple claims")
            claimed_rails.add(name)
            rail = rail_by_name[name]
            if rail.get("external_output") is not True:
                raise ContractError(
                    f"E-PATH claimed rail {name!r} must declare external_output: true")
            if rail.get("claim_id") != cid:
                raise ContractError(
                    f"E-PATH rail {name!r} claim_id {rail.get('claim_id')!r} != {cid!r}")
            ri = number(rail.get("iout_max_A"), f"rail {name}.iout_max_A",
                        positive=True)
            ruv = number(rail.get("load_uv_threshold"),
                         f"rail {name}.load_uv_threshold", positive=True)
            rvmax = number(rail.get("vout_max"), f"rail {name}.vout_max",
                           positive=True)
            if ri + 1e-12 < current:
                raise ContractError(
                    f"E-PATH rail {name!r} supplies {ri:g} A below claim {current:g} A")
            if abs(ruv - vmin) > 1e-6:
                raise ContractError(
                    f"E-PATH rail {name!r} load_uv_threshold {ruv:g} V does not "
                    f"equal claim-plane minimum {vmin:g} V")
            if rvmax > vmax + 1e-6:
                raise ContractError(
                    f"E-PATH rail {name!r} vout_max {rvmax:g} V exceeds claim "
                    f"maximum {vmax:g} V")
            total = number(rail.get("ir_budget_mohm"),
                           f"rail {name}.ir_budget_mohm", nonnegative=True)
            values = ir_values(rail.get("ir_budget_components_mohm"), name)
            missing = PATH_PROFILES[plane] - set(values)
            if missing:
                raise ContractError(
                    f"E-PATH rail {name!r} at {plane} omits required elements: "
                    f"{sorted(missing)}")
            undeclared = set(values) - included
            if undeclared:
                raise ContractError(
                    f"E-PATH rail {name!r} has IR elements outside the declared "
                    f"included boundary: {sorted(undeclared)}")
            if abs(sum(values.values()) - total) > max(1e-6, total * 1e-6):
                raise ContractError(
                    f"E-PATH rail {name!r} path sums to {sum(values.values()):g} "
                    f"mOhm, not ir_budget_mohm {total:g}")
        notes.append(
            f"D-SPEC/E-PATH {cid}: {count} x {current:g} A, {simult} simultaneous, "
            f"{vmin:g}-{vmax:g} V at {plane}")

    for name, rail in rail_by_name.items():
        external = rail.get("external_output")
        if external not in (True, False):
            raise ContractError(
                f"E-PATH rail {name!r} must declare external_output: true/false")
        if external and name not in claimed_rails:
            raise ContractError(
                f"E-PATH external rail {name!r} has no D-SPEC power claim")
        if not external and rail.get("claim_id"):
            raise ContractError(
                f"E-PATH internal rail {name!r} must not declare claim_id")
    return notes


def check_switching(project: Path):
    path = project / "03_src" / "rules" / "power_stages.yaml"
    data = load_yaml(path, "E-SWDRV")
    stages = data.get("stages")
    if not isinstance(stages, list):
        raise ContractError("E-SWDRV stages must be a list")
    if not stages:
        text_value(data.get("no_external_gate_drive_stages"),
                   "E-SWDRV no_external_gate_drive_stages")
    aliases = part_aliases(project)
    notes = []
    for i, stage in enumerate(stages):
        where = f"E-SWDRV stages[{i}]"
        if not isinstance(stage, dict):
            raise ContractError(f"{where} must be a mapping")
        name = text_value(stage.get("name"), f"{where}.name")
        controller = text_value(stage.get("controller_ref"), f"{where}.controller_ref")
        require_part(stage.get("controller_part"), f"{where}.controller_part", aliases)
        fsw = number(stage.get("switching_frequency_hz"),
                     f"{where}.switching_frequency_hz", positive=True)
        vgate = number(stage.get("gate_drive_voltage_V"),
                       f"{where}.gate_drive_voltage_V", positive=True)
        limit = number(stage.get("controller_current_limit_min_mA"),
                       f"{where}.controller_current_limit_min_mA", positive=True)
        bias = number(stage.get("controller_bias_current_max_mA"),
                      f"{where}.controller_bias_current_max_mA", nonnegative=True)
        margin = number(stage.get("current_margin_pct", 20),
                        f"{where}.current_margin_pct", nonnegative=True) / 100.0
        if margin >= 1:
            raise ContractError(f"{where}.current_margin_pct must be < 100")
        switches = list_value(stage.get("switches"), f"{where}.switches")
        qsum = 0.0
        for j, switch in enumerate(switches):
            sw = f"{where}.switches[{j}]"
            if not isinstance(switch, dict):
                raise ContractError(f"{sw} must be a mapping")
            text_value(switch.get("refs"), f"{sw}.refs")
            require_part(switch.get("part"), f"{sw}.part", aliases)
            qsum += number(switch.get("qg_nC"), f"{sw}.qg_nC", positive=True)
            basis = text_value(switch.get("qg_basis"), f"{sw}.qg_basis")
            if basis not in {"maximum", "qualified_max"}:
                raise ContractError(
                    f"E-SWDRV {name!r} uses {basis!r} gate charge for {sw}; "
                    "typical values cannot prove a worst-case drive budget")
            qv = number(switch.get("qg_test_voltage_V"),
                        f"{sw}.qg_test_voltage_V", positive=True)
            if qv + 1e-9 < vgate:
                raise ContractError(
                    f"E-SWDRV {name!r} gate charge was bounded at {qv:g} V, "
                    f"below the {vgate:g} V drive")
            text_value(switch.get("evidence"), f"{sw}.evidence")
        igate = qsum * fsw / 1_000_000.0
        need = igate + bias
        allowed = limit * (1.0 - margin)
        if need > allowed + 1e-9:
            raise ContractError(
                f"E-SWDRV {name!r}/{controller}: gate {igate:.3f} mA + bias "
                f"{bias:g} mA = {need:.3f} mA exceeds {limit:g} mA minimum "
                f"limit with {margin*100:g}% margin ({allowed:.3f} mA allowed)")
        source = text_value(stage.get("bias_source"), f"{where}.bias_source")
        if source == "internal_linear":
            vin = number(stage.get("vin_max_V"), f"{where}.vin_max_V", positive=True)
            theta = number(stage.get("controller_theta_ja_C_per_W"),
                           f"{where}.controller_theta_ja_C_per_W", positive=True)
            ambient = number(stage.get("ambient_max_C"),
                             f"{where}.ambient_max_C")
            tj = number(stage.get("junction_max_C"), f"{where}.junction_max_C")
            tmargin = number(stage.get("temperature_margin_C", 20),
                             f"{where}.temperature_margin_C", nonnegative=True)
            pdiss = vin * need / 1000.0
            predicted = ambient + pdiss * theta + tmargin
            if predicted > tj + 1e-9:
                raise ContractError(
                    f"E-SWDRV {name!r}: conservative controller bound {pdiss:.3f} W "
                    f"predicts {predicted:.1f} C including margin > {tj:g} C")
        elif source != "external_regulated":
            raise ContractError(
                f"{where}.bias_source must be internal_linear/external_regulated")
        notes.append(
            f"E-SWDRV {name}: Qg={qsum:g} nC, fsw={fsw:g} Hz, "
            f"gate+bias={need:.3f}/{allowed:.3f} mA allowed")
    return notes


def check_surge(project: Path):
    path = project / "03_src" / "rules" / "protection_paths.yaml"
    data = load_yaml(path, "E-SURGE")
    paths = data.get("paths")
    if not isinstance(paths, list):
        raise ContractError("E-SURGE paths must be a list")
    if not paths:
        text_value(data.get("no_surge_exposed_paths"),
                   "E-SURGE no_surge_exposed_paths")
    aliases = part_aliases(project)
    notes = []
    for i, item in enumerate(paths):
        where = f"E-SURGE paths[{i}]"
        if not isinstance(item, dict):
            raise ContractError(f"{where} must be a mapping")
        name = text_value(item.get("name"), f"{where}.name")
        normal = number(item.get("source_operating_max_V"),
                        f"{where}.source_operating_max_V", positive=True)
        if item.get("source_tolerance_included") is not True:
            raise ContractError(
                f"E-SURGE {name!r} source_operating_max_V must include source "
                "accuracy, regulation, ripple, and wiring rise")
        text_value(item.get("source_boundary_evidence"),
                   f"{where}.source_boundary_evidence")
        tvs = item.get("tvs")
        if not isinstance(tvs, dict):
            raise ContractError(f"{where}.tvs must be a mapping")
        require_part(tvs.get("part"), f"{where}.tvs.part", aliases)
        stand = number(tvs.get("standoff_V"), f"{where}.tvs.standoff_V",
                       positive=True)
        clamp = number(tvs.get("clamp_max_V"), f"{where}.tvs.clamp_max_V",
                       positive=True)
        duration = number(tvs.get("waveform_duration_ms"),
                          f"{where}.tvs.waveform_duration_ms", positive=True)
        text_value(tvs.get("waveform"), f"{where}.tvs.waveform")
        text_value(tvs.get("evidence"), f"{where}.tvs.evidence")
        margin = number(item.get("voltage_margin_pct"),
                        f"{where}.voltage_margin_pct", nonnegative=True) / 100.0
        if normal > stand + 1e-9:
            raise ContractError(
                f"E-SURGE {name!r}: normal max {normal:g} V exceeds TVS "
                f"standoff {stand:g} V")
        exposed = list_value(item.get("exposed"), f"{where}.exposed")
        for j, part in enumerate(exposed):
            ep = f"{where}.exposed[{j}]"
            if not isinstance(part, dict):
                raise ContractError(f"{ep} must be a mapping")
            ref = text_value(part.get("ref"), f"{ep}.ref")
            require_part(part.get("part"), f"{ep}.part", aliases)
            recommended = number(part.get("recommended_max_V"),
                                 f"{ep}.recommended_max_V", positive=True)
            absolute = number(part.get("absolute_max_V"),
                              f"{ep}.absolute_max_V", positive=True)
            if normal > recommended + 1e-9:
                raise ContractError(
                    f"E-SURGE {name!r}/{ref}: normal {normal:g} V exceeds "
                    f"recommended maximum {recommended:g} V")
            if clamp * (1 + margin) > absolute + 1e-9:
                raise ContractError(
                    f"E-SURGE {name!r}/{ref}: clamp {clamp:g} V x "
                    f"{1+margin:.3f} margin exceeds absolute maximum {absolute:g} V")
            if clamp > recommended:
                qual = part.get("transient_qualification")
                if not isinstance(qual, dict):
                    raise ContractError(
                        f"E-SURGE {name!r}/{ref}: clamp exceeds recommended "
                        "maximum but transient_qualification is absent")
                grade = text_value(qual.get("grade"), f"{ep}.transient_qualification.grade")
                if grade not in {"measured", "cited"}:
                    raise ContractError(
                        f"E-SURGE {name!r}/{ref}: transient qualification grade "
                        f"{grade!r} is not measured/cited")
                qv = number(qual.get("max_V"), f"{ep}.transient_qualification.max_V",
                            positive=True)
                qd = number(qual.get("max_duration_ms"),
                            f"{ep}.transient_qualification.max_duration_ms",
                            positive=True)
                rated_d = number(part.get("absolute_max_duration_ms"),
                                 f"{ep}.absolute_max_duration_ms", positive=True)
                text_value(qual.get("evidence"), f"{ep}.transient_qualification.evidence")
                if qv + 1e-9 < clamp or qd + 1e-9 < duration:
                    raise ContractError(
                        f"E-SURGE {name!r}/{ref}: qualification {qv:g} V/{qd:g} ms "
                        f"does not cover clamp {clamp:g} V/{duration:g} ms")
                if qd > rated_d + 1e-9:
                    raise ContractError(
                        f"E-SURGE {name!r}/{ref}: qualified duration {qd:g} ms "
                        f"exceeds absolute-rating duration {rated_d:g} ms")
        notes.append(
            f"E-SURGE {name}: normal={normal:g} V, TVS={stand:g}/{clamp:g} V, "
            f"{len(exposed)} exposed part(s)")
    return notes


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path)
    ap.add_argument("--requirements", action="store_true")
    ap.add_argument("--switching", action="store_true")
    ap.add_argument("--surge", action="store_true")
    args = ap.parse_args(argv)
    if yaml is None:
        print("EARLY-DESIGN FAIL: PyYAML is unavailable")
        return 2
    selected = args.requirements or args.switching or args.surge
    checks = []
    if args.requirements or not selected:
        checks.append(("D-SPEC/E-PATH", check_requirements))
    if args.switching or not selected:
        checks.append(("E-SWDRV", check_switching))
    if args.surge or not selected:
        checks.append(("E-SURGE", check_surge))
    notes, fails = [], []
    for label, fn in checks:
        try:
            notes.extend(fn(args.project.resolve()))
        except ContractError as exc:
            fails.append(f"{label}: {exc}")
    for note in notes:
        print("  PASS", note)
    for fail in fails:
        print("  FAIL", fail)
    print(f"EARLY-DESIGN {'FAIL' if fails else 'PASS'}: "
          f"{len(checks)-len(fails)}/{len(checks)} gate families green")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
