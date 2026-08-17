#!/usr/bin/env python3
"""Fail-closed commission/parts/schematic design-contract gates.

The PCB pipeline already checked arithmetic once an author supplied numbers,
but it did not prove that the numbers described the user's measurement plane,
that a switching controller could drive the selected MOSFETs, or that a TVS
clamp was compatible with every exposed part.  This checker owns those three
pre-placement decisions:

  D-SPEC / E-PATH  requirements.yaml <-> power_tree.yaml
  E-SWDRV          power_stages.yaml gate-drive/current/thermal compatibility,
                   including schema-2 peak-current-limit/ripple proof
  E-SURGE          protection_paths.yaml normal and transient ratings
  E-CAP            power_tree.yaml effective-capacitance evidence, including
                   tolerance, DC bias, temperature and lifecycle derating
  E-FAULT          power_tree.yaml aggregate current/fault envelope, including
                   downstream current-limit sum, breaker thresholds, upstream
                   ratings, fault timer and startup-timer compatibility

Missing adopted inputs are errors.  Legacy projects need not invoke this
checker until their next material revision; new templates invoke it before
board generation.
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment failure is explicit
    yaml = None


class ContractError(ValueError):
    pass


def load_yaml(path: Path, label: str, *, schemas=(1,)):
    if not path.exists():
        raise ContractError(f"{label}: missing required adopted input {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ContractError(f"{label}: cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"{label}: {path} must contain a YAML mapping")
    if data.get("schema") not in schemas:
        expected = "/".join(str(v) for v in schemas)
        raise ContractError(f"{label}: {path} requires schema: {expected}")
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
    "board_connector": ({
        "protection_switch", "pcb_copper_vias_joints", "connector_contacts"
    },),
    "mated_test_plug": ({
        "protection_switch", "pcb_copper_vias_joints", "mated_power_contacts"
    },),
    # A load-plane claim may decompose each boundary only when the measurement
    # endpoints make that decomposition honest.  For a Type-C-to-Type-C cable,
    # USB-IF LLCR excludes plug/receptacle paddle cards and there are two mated
    # pairs, so one end-to-end qualified interconnect term is often the only
    # non-overlapping representation available before first article.
    "load": (
        {"protection_switch", "pcb_copper_vias_joints",
         "mated_power_contacts", "cable"},
        {"protection_switch", "pcb_copper_vias_joints",
         "complete_type_c_interconnect"},
    ),
}
PATH_EXCLUSIONS = {
    "board_connector": {"mated_power_contacts", "cable", "appliance"},
    "mated_test_plug": {"cable", "appliance"},
    "load": set(),
}


def path_profile(plane, available, where):
    matches = [profile for profile in PATH_PROFILES[plane]
               if profile <= available]
    if matches:
        if ("complete_type_c_interconnect" in available and
                ({"mated_power_contacts", "cable"} & available)):
            raise ContractError(
                f"{where} mixes complete_type_c_interconnect with decomposed "
                "mated_power_contacts/cable terms; choose one non-overlapping "
                "measurement boundary")
        return matches[0]
    missing = min((profile - available for profile in PATH_PROFILES[plane]),
                  key=lambda items: (len(items), sorted(items)))
    raise ContractError(f"{where} omits {sorted(missing)}")


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
        path_profile(plane, included,
                     f"D-SPEC claim {cid!r} included_elements")
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
            path_profile(plane, set(values),
                         f"E-PATH rail {name!r} at {plane}")
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


CAP_DERATING_FIELDS = (
    "tolerance_minus_pct",
    "dc_bias_derating_pct",
    "temperature_derating_pct",
    "lifecycle_derating_pct",
)


def check_capacitance(project: Path):
    """Grade datasheet minimums against conservative effective capacitance.

    Nominal capacitance is not a stability proof for MLCCs: initial negative
    tolerance, applied-voltage bias, temperature and lifecycle/aging can all
    reduce the value.  Each contributor must therefore expose every derating
    term explicitly, even when a term is zero.  The terms are multiplied,
    which preserves their independent worst-case meaning and avoids a hidden
    nameplate-value assumption.
    """
    path = project / "03_src" / "rules" / "power_tree.yaml"
    data = load_yaml(path, "E-CAP")
    banks = data.get("effective_capacitance_banks")
    no_requirements = data.get("no_effective_capacitance_requirements")
    if banks is not None and no_requirements is not None:
        raise ContractError(
            "E-CAP effective_capacitance_banks and "
            "no_effective_capacitance_requirements are mutually exclusive")
    if banks is None and no_requirements is not None:
        reason = text_value(no_requirements,
                            "no_effective_capacitance_requirements")
        return [f"E-CAP not applicable: {reason}"]
    if not isinstance(banks, list) or not banks:
        raise ContractError(
            "E-CAP effective_capacitance_banks must be a non-empty list; "
            "use an explicit no_effective_capacitance_requirements reason "
            "only for a design with no converter/protection minimum")
    aliases = part_aliases(project)
    notes = []
    seen_names = set()
    for i, bank in enumerate(banks):
        where = f"E-CAP effective_capacitance_banks[{i}]"
        if not isinstance(bank, dict):
            raise ContractError(f"{where} must be a mapping")
        name = text_value(bank.get("name"), f"{where}.name")
        if name in seen_names:
            raise ContractError(f"E-CAP duplicate bank name {name!r}")
        seen_names.add(name)
        required = number(bank.get("requirement_uF"),
                          f"{where}.requirement_uF", positive=True)
        text_value(bank.get("requirement_evidence"),
                   f"{where}.requirement_evidence")
        accepted = {
            text_value(value, f"{where}.accepted_dielectrics[]").lower()
            for value in list_value(bank.get("accepted_dielectrics"),
                                    f"{where}.accepted_dielectrics")
        }
        contributors = list_value(bank.get("contributors"),
                                  f"{where}.contributors")
        total, used_refs = 0.0, set()
        for j, row in enumerate(contributors):
            cw = f"{where}.contributors[{j}]"
            if not isinstance(row, dict):
                raise ContractError(f"{cw} must be a mapping")
            require_part(row.get("part"), f"{cw}.part", aliases)
            refs = [text_value(ref, f"{cw}.refs[]")
                    for ref in list_value(row.get("refs"), f"{cw}.refs")]
            duplicate = used_refs & set(refs)
            if duplicate or len(set(refs)) != len(refs):
                raise ContractError(
                    f"E-CAP bank {name!r} counts duplicate refs "
                    f"{sorted(duplicate or {r for r in refs if refs.count(r) > 1})}")
            used_refs.update(refs)
            nominal = number(row.get("nominal_each_uF"),
                             f"{cw}.nominal_each_uF", positive=True)
            dielectric = text_value(row.get("dielectric"),
                                    f"{cw}.dielectric").lower()
            if dielectric not in accepted:
                raise ContractError(
                    f"E-CAP bank {name!r}: {dielectric!r} contributor is not "
                    f"one of accepted dielectrics {sorted(accepted)}")
            text_value(row.get("basis"), f"{cw}.basis")
            text_value(row.get("evidence"), f"{cw}.evidence")
            factor = 1.0
            for field in CAP_DERATING_FIELDS:
                if field not in row:
                    raise ContractError(
                        f"{cw} is missing {field!r}; every effective-value "
                        "derating must be explicit, including zero")
                pct = number(row[field], f"{cw}.{field}", nonnegative=True)
                if pct >= 100:
                    raise ContractError(f"{cw}.{field} must be below 100%")
                factor *= 1.0 - pct / 100.0
            total += len(refs) * nominal * factor
        if total + 1e-9 < required:
            raise ContractError(
                f"E-CAP bank {name!r}: {total:.3f} uF worst-case effective "
                f"is below {required:g} uF required")
        notes.append(
            f"E-CAP {name}: {total:.3f}/{required:g} uF effective "
            f"from {len(used_refs)} component(s)")
    return notes


CAP_VALUE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(pF|nF|uF|µF|mF|F)\s*$", re.IGNORECASE)
CAP_TO_NF = {
    "pf": 1e-3,
    "nf": 1.0,
    "uf": 1e3,
    "µf": 1e3,
    "mf": 1e6,
    "f": 1e9,
}


def parse_capacitance_nf(value, where):
    match = CAP_VALUE_RE.match(str(value or ""))
    if not match:
        raise ContractError(
            f"{where} must be an engineering capacitance such as 47nF")
    return float(match.group(1)) * CAP_TO_NF[match.group(2).lower()]


RESISTANCE_VALUE_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*([mRrkKMG]?)\s*(?:[oO][hH][mM][sS]?|Ω)?\s*$")
RESISTANCE_SCALE = {
    "": 1.0,
    "R": 1.0,
    "r": 1.0,
    "m": 1e-3,
    "k": 1e3,
    "K": 1e3,
    "M": 1e6,
    "G": 1e9,
}


def parse_resistance_ohm(value, where):
    """Decode the exact asserted programmer value without duplicating it."""
    if isinstance(value, bool):
        raise ContractError(f"{where} must be a resistance, not boolean")
    if isinstance(value, (int, float)):
        return number(value, where, positive=True)
    match = RESISTANCE_VALUE_RE.match(str(value or ""))
    if not match:
        raise ContractError(
            f"{where} must be a resistance such as 210, 210R or 0.21k")
    return number(float(match.group(1)) * RESISTANCE_SCALE[match.group(2)],
                  where, positive=True)


def asserted_part_values(project: Path):
    """Return source-owned part values used to prevent duplicated proof data.

    E-FAULT owns corner relationships, while electrical_invariants.yaml owns
    the exact fitted values.  Requiring agreement means a capacitor or
    programmer-resistor edit cannot silently leave the safety proof stale.
    """
    path = project / "03_src" / "rules" / "electrical_invariants.yaml"
    if not path.exists():
        raise ContractError(
            f"E-FAULT missing required adopted input {path}; fault-envelope "
            "component values must be tied to exact schematic invariants")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8-sig")) or {}
    except Exception as exc:
        raise ContractError(f"E-FAULT cannot parse {path}: {exc}") from exc
    rows = data.get("invariants")
    if not isinstance(rows, list):
        raise ContractError("E-FAULT electrical_invariants.yaml needs invariants: []")
    values = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("assert") != "part_value":
            continue
        ref = str(row.get("part") or "").strip()
        if ref:
            values[ref] = row
    return values


FAULT_CAP_DERATING_FIELDS = (
    "tolerance_pct",
    "temperature_minus_pct",
    "temperature_plus_pct",
    "dc_bias_minus_pct",
    "aging_minus_pct",
)


def fault_cap_corners(raw, where, invariant_values):
    if not isinstance(raw, dict):
        raise ContractError(f"{where} must be a mapping")
    ref = text_value(raw.get("capacitor_ref"), f"{where}.capacitor_ref")
    nominal = number(raw.get("capacitance_nominal_nF"),
                     f"{where}.capacitance_nominal_nF", positive=True)
    factors = {}
    for field in FAULT_CAP_DERATING_FIELDS:
        if field not in raw:
            raise ContractError(
                f"{where} is missing {field!r}; every timer-capacitance "
                "corner term must be explicit, including zero")
        factors[field] = number(raw[field], f"{where}.{field}",
                                nonnegative=True)
        if factors[field] >= 100:
            raise ContractError(f"{where}.{field} must be below 100%")
    evidence = text_value(raw.get("evidence"), f"{where}.evidence")

    invariant = invariant_values.get(ref)
    if invariant is None:
        raise ContractError(
            f"{where}.capacitor_ref {ref!r} has no part_value assertion in "
            "electrical_invariants.yaml")
    fitted_nf = parse_capacitance_nf(invariant.get("equals"),
                                     f"part_value assertion for {ref}")
    fitted_tol = number(invariant.get("tolerance_pct"),
                        f"part_value assertion for {ref}.tolerance_pct",
                        nonnegative=True)
    if not math.isclose(fitted_nf, nominal, rel_tol=1e-9, abs_tol=1e-12):
        raise ContractError(
            f"{where}: {ref} proof says {nominal:g} nF but the exact "
            f"schematic invariant says {fitted_nf:g} nF")
    if not math.isclose(fitted_tol, factors["tolerance_pct"],
                        rel_tol=1e-9, abs_tol=1e-12):
        raise ContractError(
            f"{where}: {ref} proof uses {factors['tolerance_pct']:g}% "
            f"tolerance but the exact schematic invariant uses "
            f"{fitted_tol:g}%")

    low = nominal
    for field in ("tolerance_pct", "temperature_minus_pct",
                  "dc_bias_minus_pct", "aging_minus_pct"):
        low *= 1.0 - factors[field] / 100.0
    high = nominal * (1.0 + factors["tolerance_pct"] / 100.0)
    high *= 1.0 + factors["temperature_plus_pct"] / 100.0
    return ref, low, high, evidence


def require_asserted_part(ref, where, invariant_values):
    ref = text_value(ref, where)
    if ref not in invariant_values:
        raise ContractError(
            f"{where} {ref!r} has no part_value assertion in "
            "electrical_invariants.yaml")
    return ref


def check_fault_envelopes(project: Path):
    """Grade aggregate overload handling across normal, peak and fault time.

    This intentionally treats the current-limit population, aggregate breaker,
    upstream source and timer/startup relation as one envelope.  Checking any
    member alone is insufficient when several independently limited outputs can
    demand more than the upstream converter can continuously survive.
    """
    path = project / "03_src" / "rules" / "power_tree.yaml"
    data = load_yaml(path, "E-FAULT")
    envelopes = data.get("fault_envelopes")
    no_requirements = data.get("no_fault_envelope_requirements")
    if envelopes is not None and no_requirements is not None:
        raise ContractError(
            "E-FAULT fault_envelopes and no_fault_envelope_requirements are "
            "mutually exclusive")
    if envelopes is None and no_requirements is not None:
        reason = text_value(no_requirements,
                            "no_fault_envelope_requirements")
        return [f"E-FAULT not applicable: {reason}"]
    if not isinstance(envelopes, list) or not envelopes:
        raise ContractError(
            "E-FAULT fault_envelopes must be a non-empty list; use an explicit "
            "no_fault_envelope_requirements reason only when no independently "
            "limited outputs share an upstream path")
    invariant_values = asserted_part_values(project)
    aliases = part_aliases(project)
    notes, seen_names = [], set()
    for i, env in enumerate(envelopes):
        where = f"E-FAULT fault_envelopes[{i}]"
        if not isinstance(env, dict):
            raise ContractError(f"{where} must be a mapping")
        name = text_value(env.get("name"), f"{where}.name")
        if name in seen_names:
            raise ContractError(f"E-FAULT duplicate envelope name {name!r}")
        seen_names.add(name)
        normal = number(env.get("normal_continuous_A"),
                        f"{where}.normal_continuous_A", positive=True)
        peak = number(env.get("service_peak_A"), f"{where}.service_peak_A",
                      positive=True)
        peak_ms = number(env.get("service_peak_max_ms"),
                         f"{where}.service_peak_max_ms", positive=True)
        if peak + 1e-12 < normal:
            raise ContractError(
                f"E-FAULT {name!r}: service peak {peak:g} A is below normal "
                f"continuous load {normal:g} A")

        downstream = list_value(env.get("downstream_limits"),
                                f"{where}.downstream_limits")
        downstream_sum = 0.0
        for j, row in enumerate(downstream):
            dw = f"{where}.downstream_limits[{j}]"
            if not isinstance(row, dict):
                raise ContractError(f"{dw} must be a mapping")
            text_value(row.get("name"), f"{dw}.name")
            count = number(row.get("count"), f"{dw}.count", positive=True)
            simultaneous = number(row.get("simultaneous_count"),
                                  f"{dw}.simultaneous_count", positive=True)
            if not count.is_integer() or not simultaneous.is_integer():
                raise ContractError(f"{dw} counts must be integers")
            if simultaneous > count:
                raise ContractError(
                    f"{dw}.simultaneous_count {simultaneous:g} exceeds count "
                    f"{count:g}")
            each_high = number(row.get("worst_high_each_A"),
                               f"{dw}.worst_high_each_A", positive=True)
            programmer_refs = row.get("programmer_refs")
            evidence_refs = row.get("evidence_refs")
            if programmer_refs is not None and evidence_refs is not None:
                raise ContractError(
                    f"{dw} must use programmer_refs or evidence_refs, not both")
            if programmer_refs is not None:
                refs = list_value(programmer_refs, f"{dw}.programmer_refs")
                if len(refs) != int(count):
                    raise ContractError(
                        f"{dw}.programmer_refs has {len(refs)} refs, expected "
                        f"count {int(count)}")
                for ref in refs:
                    require_asserted_part(ref, f"{dw}.programmer_refs[]",
                                          invariant_values)
            else:
                refs = list_value(evidence_refs, f"{dw}.evidence_refs")
                if len(refs) != int(count):
                    raise ContractError(
                        f"{dw}.evidence_refs has {len(refs)} refs, expected "
                        f"count {int(count)}")
                for ref in refs:
                    require_part(ref, f"{dw}.evidence_refs[]", aliases)
            text_value(row.get("evidence"), f"{dw}.evidence")
            downstream_sum += simultaneous * each_high

        upstream = env.get("upstream")
        if not isinstance(upstream, dict):
            raise ContractError(f"{where}.upstream must be a mapping")
        continuous_rating = number(upstream.get("continuous_rating_A"),
                                   f"{where}.upstream.continuous_rating_A",
                                   positive=True)
        peak_rating = number(upstream.get("peak_rating_A"),
                             f"{where}.upstream.peak_rating_A", positive=True)
        if peak_rating + 1e-12 < continuous_rating:
            raise ContractError(
                f"E-FAULT {name!r}: upstream peak rating {peak_rating:g} A is "
                f"below continuous rating {continuous_rating:g} A")
        text_value(upstream.get("evidence"), f"{where}.upstream.evidence")
        if normal > continuous_rating + 1e-12:
            raise ContractError(
                f"E-FAULT {name!r}: normal load {normal:g} A exceeds upstream "
                f"continuous rating {continuous_rating:g} A")
        if peak > peak_rating + 1e-12:
            raise ContractError(
                f"E-FAULT {name!r}: service peak {peak:g} A exceeds upstream "
                f"peak rating {peak_rating:g} A")
        if downstream_sum > peak_rating + 1e-12:
            raise ContractError(
                f"E-FAULT {name!r}: downstream worst-high aggregate "
                f"{downstream_sum:.3f} A exceeds upstream peak rating "
                f"{peak_rating:g} A")

        breaker = env.get("aggregate_breaker")
        if not isinstance(breaker, dict):
            raise ContractError(f"{where}.aggregate_breaker must be a mapping")
        programmer_ref = require_asserted_part(
            breaker.get("programmer_ref"),
            f"{where}.aggregate_breaker.programmer_ref", invariant_values)
        programmer = invariant_values[programmer_ref]
        programmer_ohm = parse_resistance_ohm(
            programmer.get("equals"),
            f"electrical_invariants part_value {programmer_ref}.equals")
        programmer_tol_pct = number(
            programmer.get("tolerance_pct"),
            f"electrical_invariants part_value {programmer_ref}.tolerance_pct",
            nonnegative=True)

        model_where = f"{where}.aggregate_breaker.threshold_model"
        model = breaker.get("threshold_model")
        if not isinstance(model, dict):
            raise ContractError(f"{model_where} must be a mapping")
        equation = text_value(model.get("equation"), f"{model_where}.equation")
        if equation != "inverse_resistance_with_offset":
            raise ContractError(
                f"{model_where}.equation must be "
                "inverse_resistance_with_offset")
        coefficient_low = number(
            model.get("coefficient_worst_low_A_ohm"),
            f"{model_where}.coefficient_worst_low_A_ohm", positive=True)
        coefficient_high = number(
            model.get("coefficient_worst_high_A_ohm"),
            f"{model_where}.coefficient_worst_high_A_ohm", positive=True)
        if coefficient_high + 1e-12 < coefficient_low:
            raise ContractError(
                f"E-FAULT {name!r}: breaker threshold coefficients are reversed")
        current_offset = number(
            model.get("current_offset_A"), f"{model_where}.current_offset_A",
            nonnegative=True)
        programmer_tcr = number(
            model.get("programmer_tcr_ppm_per_C"),
            f"{model_where}.programmer_tcr_ppm_per_C", nonnegative=True)
        temperature_excursion = number(
            model.get("programmer_temperature_excursion_C"),
            f"{model_where}.programmer_temperature_excursion_C",
            nonnegative=True)
        programmer_error = (programmer_tol_pct / 100.0 +
                            programmer_tcr * temperature_excursion / 1_000_000.0)
        if programmer_error >= 1:
            raise ContractError(
                f"{model_where}: charged programmer error must be below 100%")
        low = (current_offset + coefficient_low /
               (programmer_ohm * (1 + programmer_error)))
        high = (current_offset + coefficient_high /
                (programmer_ohm * (1 - programmer_error)))
        expected_low = number(
            breaker.get("expected_threshold_worst_low_A"),
            f"{where}.aggregate_breaker.expected_threshold_worst_low_A",
            positive=True)
        expected_high = number(
            breaker.get("expected_threshold_worst_high_A"),
            f"{where}.aggregate_breaker.expected_threshold_worst_high_A",
            positive=True)
        calculation_tolerance = number(
            breaker.get("threshold_calculation_tolerance_A"),
            f"{where}.aggregate_breaker.threshold_calculation_tolerance_A",
            positive=True)
        if abs(expected_low - low) > calculation_tolerance + 1e-12:
            raise ContractError(
                f"E-FAULT {name!r}: expected breaker worst-low threshold "
                f"{expected_low:g} A does not match derived {low:.6f} A")
        if abs(expected_high - high) > calculation_tolerance + 1e-12:
            raise ContractError(
                f"E-FAULT {name!r}: expected breaker worst-high threshold "
                f"{expected_high:g} A does not match derived {high:.6f} A")
        if high + 1e-12 < low:
            raise ContractError(
                f"E-FAULT {name!r}: breaker threshold corners are reversed")
        response = text_value(breaker.get("response"),
                              f"{where}.aggregate_breaker.response")
        if response not in {"latch_off", "auto_retry", "foldback"}:
            raise ContractError(
                f"{where}.aggregate_breaker.response must be "
                "latch_off/auto_retry/foldback")
        text_value(breaker.get("threshold_evidence"),
                   f"{where}.aggregate_breaker.threshold_evidence")
        text_value(breaker.get("reset_evidence"),
                   f"{where}.aggregate_breaker.reset_evidence")
        normal_margin_min = number(
            breaker.get("minimum_normal_margin_A"),
            f"{where}.aggregate_breaker.minimum_normal_margin_A",
            positive=True)
        fault_margin_min = number(
            breaker.get("minimum_fault_coordination_margin_A"),
            f"{where}.aggregate_breaker.minimum_fault_coordination_margin_A",
            positive=True)
        if low - normal + 1e-12 < normal_margin_min:
            raise ContractError(
                f"E-FAULT {name!r}: breaker worst-low threshold {low:.6f} A "
                f"leaves only {low - normal:.6f} A above normal load; "
                f"{normal_margin_min:g} A required")
        if high > peak_rating + 1e-12:
            raise ContractError(
                f"E-FAULT {name!r}: breaker worst-high threshold {high:g} A "
                f"exceeds upstream peak rating {peak_rating:g} A")
        breaker_must_interrupt = downstream_sum > continuous_rating + 1e-12
        if (breaker_must_interrupt and
                downstream_sum - high + 1e-12 < fault_margin_min):
            raise ContractError(
                f"E-FAULT {name!r}: downstream worst-high aggregate "
                f"{downstream_sum:.3f} A leaves only "
                f"{downstream_sum - high:.6f} A above the breaker "
                f"worst-high threshold; {fault_margin_min:g} A required")

        timer = breaker.get("timer")
        timer_ref, timer_c_min, timer_c_max, _ = fault_cap_corners(
            timer, f"{where}.aggregate_breaker.timer", invariant_values)
        delta_min = number(timer.get("comparator_delta_min_V"),
                           f"{where}.aggregate_breaker.timer.comparator_delta_min_V",
                           positive=True)
        delta_max = number(timer.get("comparator_delta_max_V"),
                           f"{where}.aggregate_breaker.timer.comparator_delta_max_V",
                           positive=True)
        current_min = number(timer.get("discharge_current_min_uA"),
                             f"{where}.aggregate_breaker.timer.discharge_current_min_uA",
                             positive=True)
        current_max = number(timer.get("discharge_current_max_uA"),
                             f"{where}.aggregate_breaker.timer.discharge_current_max_uA",
                             positive=True)
        if delta_max + 1e-12 < delta_min or current_max + 1e-12 < current_min:
            raise ContractError(
                f"E-FAULT {name!r}: timer voltage/current corners are reversed")
        timer_min_ms = timer_c_min * delta_min / current_max
        timer_max_ms = timer_c_max * delta_max / current_min
        if timer_min_ms + 1e-12 < peak_ms:
            raise ContractError(
                f"E-FAULT {name!r}: {timer_ref} worst-low fault timer "
                f"{timer_min_ms:.3f} ms is below service peak duration "
                f"{peak_ms:g} ms")
        if breaker_must_interrupt and high > continuous_rating + 1e-12:
            overload_max_ms = number(
                upstream.get("overload_qualification_max_ms"),
                f"{where}.upstream.overload_qualification_max_ms",
                positive=True)
            text_value(
                upstream.get("overload_qualification_evidence"),
                f"{where}.upstream.overload_qualification_evidence")
            if timer_max_ms > overload_max_ms + 1e-12:
                raise ContractError(
                    f"E-FAULT {name!r}: breaker worst-high threshold "
                    f"{high:.6f} A exceeds the {continuous_rating:g} A "
                    f"continuous rating for up to {timer_max_ms:.3f} ms, "
                    f"above the {overload_max_ms:g} ms qualified overload "
                    "window")

        startup = timer.get("startup")
        startup_where = f"{where}.aggregate_breaker.timer.startup"
        startup_ref, startup_c_min, _, _ = fault_cap_corners(
            startup, startup_where, invariant_values)
        startup_model = str(startup.get("model") or
                            "timer_to_gate_high_ratio").strip()
        if startup_model == "slew_limited_output_bank":
            coefficient = number(
                startup.get("slew_coefficient_pF_V_per_ms"),
                f"{startup_where}.slew_coefficient_pF_V_per_ms",
                positive=True)
            output_cap = number(startup.get("output_capacitance_max_uF"),
                                f"{startup_where}.output_capacitance_max_uF",
                                positive=True)
            slew_max_v_per_ms = coefficient / (startup_c_min * 1000.0)
            inrush_max_a = output_cap * slew_max_v_per_ms / 1000.0
            expected_inrush = number(
                startup.get("expected_inrush_max_A"),
                f"{startup_where}.expected_inrush_max_A", positive=True)
            inrush_tolerance = number(
                startup.get("calculation_tolerance_A"),
                f"{startup_where}.calculation_tolerance_A", positive=True)
            if abs(expected_inrush - inrush_max_a) > inrush_tolerance + 1e-12:
                raise ContractError(
                    f"E-FAULT {name!r}: expected startup inrush "
                    f"{expected_inrush:g} A does not match derived "
                    f"{inrush_max_a:.6f} A")
            if inrush_max_a > low + 1e-12:
                raise ContractError(
                    f"E-FAULT {name!r}: startup inrush {inrush_max_a:.6f} A "
                    f"exceeds breaker worst-low threshold {low:.6f} A")
            startup_note = (f"startup={startup_ref} gives "
                            f"{slew_max_v_per_ms:.3f} V/ms, "
                            f"{inrush_max_a:.3f} A")
        elif startup_model == "timer_to_gate_high_ratio":
            vin_min = number(startup.get("vin_min_V"),
                             f"{startup_where}.vin_min_V", positive=True)
            gate = number(startup.get("gate_overdrive_V"),
                          f"{startup_where}.gate_overdrive_V", positive=True)
            dvdt_current_max = number(startup.get("dvdt_current_max_uA"),
                                      f"{startup_where}.dvdt_current_max_uA",
                                      positive=True)
            divisor = number(startup.get("itimer_divisor"),
                             f"{startup_where}.itimer_divisor", positive=True)
            tghi_min_ms = startup_c_min * (vin_min + gate) / dvdt_current_max
            allowed_timer_nf = tghi_min_ms * 1_000_000.0 / divisor
            if timer_c_max > allowed_timer_nf + 1e-12:
                raise ContractError(
                    f"E-FAULT {name!r}: {timer_ref} worst-high "
                    f"{timer_c_max:.3f} nF exceeds {allowed_timer_nf:.3f} nF "
                    f"allowed by {startup_ref} worst-low startup ramp "
                    f"({tghi_min_ms:.3f} ms)")
            startup_note = f"startup allows {allowed_timer_nf:.3f} nF"
        else:
            raise ContractError(
                f"{startup_where}.model {startup_model!r} is unknown")

        notes.append(
            f"E-FAULT {name}: normal/peak/fault={normal:g}/{peak:g}/"
            f"{downstream_sum:.3f} A, breaker={low:g}..{high:g} A, "
            f"timer={timer_min_ms:.3f}..{timer_max_ms:.3f} ms, "
            f"{startup_note}")
    return notes


def check_switching(project: Path):
    path = project / "03_src" / "rules" / "power_stages.yaml"
    data = load_yaml(path, "E-SWDRV", schemas=(1, 2))
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
        current_note = ""
        if data.get("schema") == 2:
            cl = stage.get("current_limit")
            if not isinstance(cl, dict):
                raise ContractError(
                    f"{where}.current_limit must be a mapping in schema 2; "
                    "peak current-limit/ripple proof cannot be deferred")
            cl_where = f"{where}.current_limit"
            iout = number(cl.get("output_current_max_A"),
                          f"{cl_where}.output_current_max_A", positive=True)
            vin = number(cl.get("vin_max_V"), f"{cl_where}.vin_max_V",
                         positive=True)
            vout = number(cl.get("vout_V"), f"{cl_where}.vout_V", positive=True)
            if vin <= vout:
                raise ContractError(
                    f"{cl_where}: buck ripple proof requires vin_max_V > vout_V")
            l_each = number(cl.get("inductor_each_uH_nominal"),
                            f"{cl_where}.inductor_each_uH_nominal", positive=True)
            l_tol = number(cl.get("inductor_tolerance_pct"),
                           f"{cl_where}.inductor_tolerance_pct",
                           nonnegative=True) / 100.0
            if l_tol >= 1:
                raise ContractError(
                    f"{cl_where}.inductor_tolerance_pct must be < 100")
            n_l = number(cl.get("parallel_inductor_count"),
                         f"{cl_where}.parallel_inductor_count", positive=True)
            if not n_l.is_integer():
                raise ContractError(
                    f"{cl_where}.parallel_inductor_count must be an integer")
            r_each = number(cl.get("sense_resistor_each_mohm_nominal"),
                            f"{cl_where}.sense_resistor_each_mohm_nominal",
                            positive=True)
            r_tol = number(cl.get("sense_resistor_tolerance_pct"),
                           f"{cl_where}.sense_resistor_tolerance_pct",
                           nonnegative=True) / 100.0
            if r_tol >= 1:
                raise ContractError(
                    f"{cl_where}.sense_resistor_tolerance_pct must be < 100")
            n_r = number(cl.get("parallel_sense_resistor_count"),
                         f"{cl_where}.parallel_sense_resistor_count", positive=True)
            if not n_r.is_integer():
                raise ContractError(
                    f"{cl_where}.parallel_sense_resistor_count must be an integer")
            threshold = number(cl.get("threshold_nominal_mV"),
                               f"{cl_where}.threshold_nominal_mV", positive=True)
            threshold_min_ratio = number(cl.get("threshold_min_ratio"),
                                         f"{cl_where}.threshold_min_ratio",
                                         positive=True)
            threshold_max_ratio = number(cl.get("threshold_max_ratio"),
                                         f"{cl_where}.threshold_max_ratio",
                                         positive=True)
            if threshold_min_ratio > 1 or threshold_max_ratio < 1:
                raise ContractError(
                    f"{cl_where}: threshold ratios must bracket nominal 1.0")
            peak_margin = number(cl.get("required_peak_margin_pct"),
                                 f"{cl_where}.required_peak_margin_pct",
                                 nonnegative=True) / 100.0
            if peak_margin >= 1:
                raise ContractError(
                    f"{cl_where}.required_peak_margin_pct must be < 100")
            sense_ripple_min = number(cl.get("sense_ripple_min_mV"),
                                      f"{cl_where}.sense_ripple_min_mV",
                                      positive=True)
            path_rating = number(cl.get("peak_current_path_rating_A_min"),
                                 f"{cl_where}.peak_current_path_rating_A_min",
                                 positive=True)
            path_margin = number(cl.get("peak_current_path_margin_pct"),
                                 f"{cl_where}.peak_current_path_margin_pct",
                                 nonnegative=True) / 100.0
            if path_margin >= 1:
                raise ContractError(
                    f"{cl_where}.peak_current_path_margin_pct must be < 100")
            text_value(cl.get("evidence"), f"{cl_where}.evidence")

            l_equiv_min_h = l_each * (1.0 - l_tol) * 1e-6 / n_l
            ripple = vout * (1.0 - vout / vin) / (fsw * l_equiv_min_h)
            required_peak = (iout + ripple / 2.0) * (1.0 + peak_margin)
            r_equiv_max = r_each * (1.0 + r_tol) / n_r
            available_peak_min = threshold * threshold_min_ratio / r_equiv_max
            if available_peak_min + 1e-9 < required_peak:
                raise ContractError(
                    f"E-SWDRV {name!r} current limit: {available_peak_min:.3f} A "
                    f"worst-low peak is below {required_peak:.3f} A required "
                    f"({iout:.3f} A load + {ripple:.3f}/2 A ripple, then "
                    f"{peak_margin*100:g}% margin)")

            r_equiv_nom = r_each / n_r
            sense_ripple = ripple * r_equiv_nom
            if sense_ripple + 1e-9 < sense_ripple_min:
                raise ContractError(
                    f"E-SWDRV {name!r} current sense ripple {sense_ripple:.3f} mV "
                    f"is below the required {sense_ripple_min:g} mV")

            r_equiv_min = r_each * (1.0 - r_tol) / n_r
            available_peak_max = threshold * threshold_max_ratio / r_equiv_min
            allowed_path_peak = path_rating * (1.0 - path_margin)
            if available_peak_max > allowed_path_peak + 1e-9:
                raise ContractError(
                    f"E-SWDRV {name!r} current limit: {available_peak_max:.3f} A "
                    f"worst-high peak exceeds the {allowed_path_peak:.3f} A "
                    f"current-path allowance including {path_margin*100:g}% margin")
            current_note = (
                f", current-limit={available_peak_min:.3f}.."
                f"{available_peak_max:.3f} A peak, ripple={ripple:.3f} A_pp/"
                f"{sense_ripple:.3f} mV")
        notes.append(
            f"E-SWDRV {name}: Qg={qsum:g} nC, fsw={fsw:g} Hz, "
            f"gate+bias={need:.3f}/{allowed:.3f} mA allowed{current_note}")
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
        for j, bias in enumerate(item.get("gate_biases") or []):
            gp = f"{where}.gate_biases[{j}]"
            if not isinstance(bias, dict):
                raise ContractError(f"{gp} must be a mapping")
            ref = text_value(bias.get("ref"), f"{gp}.ref")
            polarity = text_value(bias.get("polarity"), f"{gp}.polarity")
            if polarity != "p_channel_source_upper_gate_lower_ground":
                raise ContractError(
                    f"{gp}.polarity must be p_channel_source_upper_gate_lower_ground")

            def resistor(row, label):
                if not isinstance(row, dict):
                    raise ContractError(f"{label} must be a mapping")
                text_value(row.get("ref"), f"{label}.ref")
                ohm = number(row.get("ohm"), f"{label}.ohm", positive=True)
                tol = number(row.get("tolerance_pct"),
                             f"{label}.tolerance_pct", nonnegative=True) / 100.0
                if tol >= 1:
                    raise ContractError(f"{label}.tolerance_pct must be <100")
                return ohm * (1 - tol), ohm * (1 + tol)

            upper = list_value(bias.get("upper_resistors"),
                               f"{gp}.upper_resistors")
            upper_corners = [resistor(row, f"{gp}.upper_resistors[{k}]")
                             for k, row in enumerate(upper)]
            ru_min = sum(row[0] for row in upper_corners)
            ru_max = sum(row[1] for row in upper_corners)
            rd_min, rd_max = resistor(bias.get("lower_resistor"),
                                      f"{gp}.lower_resistor")
            leakage = number(bias.get("gate_leakage_abs_uA"),
                             f"{gp}.gate_leakage_abs_uA", nonnegative=True) * 1e-6
            drive_source = number(bias.get("drive_source_min_V"),
                                  f"{gp}.drive_source_min_V", positive=True)
            required_drive = number(bias.get("required_vgs_magnitude_min_V"),
                                    f"{gp}.required_vgs_magnitude_min_V",
                                    positive=True)
            transient_source = number(bias.get("transient_source_max_V"),
                                      f"{gp}.transient_source_max_V", positive=True)
            absolute_vgs = number(bias.get("absolute_vgs_max_V"),
                                  f"{gp}.absolute_vgs_max_V", positive=True)
            text_value(bias.get("evidence"), f"{gp}.evidence")
            coordinated = clamp * (1 + margin)
            if transient_source + 1e-9 < coordinated:
                raise ContractError(
                    f"E-SURGE {name!r}/{ref}: gate transient source "
                    f"{transient_source:g} V does not cover coordinated rail "
                    f"corner {coordinated:g} V")

            def vgs_magnitude(source, ru, rd, injection):
                gate = (source / ru + injection) / (1 / ru + 1 / rd)
                return source - gate

            drive_low = vgs_magnitude(
                drive_source, ru_min, rd_max, leakage)
            stress_high = vgs_magnitude(
                transient_source, ru_max, rd_min, -leakage)
            if drive_low + 1e-9 < required_drive:
                raise ContractError(
                    f"E-SURGE {name!r}/{ref}: worst-low |VGS| "
                    f"{drive_low:.3f} V is below required {required_drive:g} V")
            if stress_high > absolute_vgs + 1e-9:
                raise ContractError(
                    f"E-SURGE {name!r}/{ref}: worst-high |VGS| "
                    f"{stress_high:.3f} V exceeds absolute maximum "
                    f"{absolute_vgs:g} V")
            notes.append(
                f"E-SURGE {name}/{ref} gate: |VGS|="
                f"{drive_low:.3f}..{stress_high:.3f} V bounded")
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
    ap.add_argument("--capacitance", action="store_true")
    ap.add_argument("--fault-envelope", action="store_true")
    args = ap.parse_args(argv)
    if yaml is None:
        print("EARLY-DESIGN FAIL: PyYAML is unavailable")
        return 2
    selected = (args.requirements or args.switching or args.surge or
                args.capacitance or args.fault_envelope)
    # E-CAP and E-FAULT are adopted-contract gates. Existing fleet projects
    # that predate either schema keep their previous default battery; an
    # explicit family invocation is fail-closed, and adding its key adopts the
    # family on every subsequent default run.
    cap_adopted = fault_adopted = False
    power_path = args.project.resolve() / "03_src/rules/power_tree.yaml"
    if power_path.is_file():
        try:
            power_doc = yaml.safe_load(
                power_path.read_text(encoding="utf-8-sig")) or {}
            cap_adopted = any(k in power_doc for k in (
                "effective_capacitance_banks",
                "no_effective_capacitance_requirements",
            ))
            fault_adopted = any(k in power_doc for k in (
                "fault_envelopes",
                "no_fault_envelope_requirements",
            ))
        except Exception:
            # The owning D-SPEC/E-PATH loader will report malformed YAML; an
            # explicit E-CAP request still reaches check_capacitance.
            pass
    checks = []
    if args.requirements or not selected:
        checks.append(("D-SPEC/E-PATH", check_requirements))
    if args.switching or not selected:
        checks.append(("E-SWDRV", check_switching))
    if args.surge or not selected:
        checks.append(("E-SURGE", check_surge))
    if args.capacitance or (not selected and cap_adopted):
        checks.append(("E-CAP", check_capacitance))
    if args.fault_envelope or (not selected and fault_adopted):
        checks.append(("E-FAULT", check_fault_envelopes))
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
