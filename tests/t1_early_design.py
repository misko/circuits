#!/usr/bin/env python3
"""T1: fail-closed commission/parts/schematic design contracts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import (ROOT, check, contains, main, must_fail, must_pass, run,  # noqa: E402
                     test, tmpdir)

ED = ROOT / "skills" / "kicad-pcb" / "scripts" / "early_design_check.py"


REQ = """schema: 1
power_claims:
  - id: ports
    rails: [P1, P2]
    count: 2
    simultaneous_count: 2
    current_A: 3.0
    voltage_min_V: 4.75
    voltage_max_V: 5.25
    duty: continuous
    measurement_plane: mated_test_plug
    boundary_evidence: qualified test plug at the receptacle interface
    included_elements: [protection_switch, pcb_copper_vias_joints, mated_power_contacts]
    excluded_elements: [cable, appliance]
"""

POWER = """schema: 1
rails:
  - &port
    name: P1
    vin_min: 12
    vin_max: 24
    vout_min: 5.17
    vout_max: 5.23
    iout_max_A: 3
    converter: BUCK
    external_output: true
    claim_id: ports
    load_uv_threshold: 4.75
    ir_budget_mohm: 100
    ir_budget_components_mohm:
      protection_switch: {value: 10, basis: maximum, evidence: DS max}
      pcb_copper_vias_joints: {value: 10, basis: budgeted_max, evidence: extraction}
      mated_power_contacts: {value: 80, basis: qualified_max, evidence: connector qualification}
  - <<: *port
    name: P2
  - name: LOGIC
    vin_min: 12
    vin_max: 24
    vout_min: 3.27
    vout_max: 3.33
    iout_max_A: 0.1
    converter: LDO
    external_output: false
"""

STAGES = """schema: 2
stages:
  - name: buck-a
    controller_ref: U1
    controller_part: CTRL
    switching_frequency_hz: 250000
    gate_drive_voltage_V: 7.4
    controller_current_limit_min_mA: 40
    controller_bias_current_max_mA: 5
    current_margin_pct: 20
    bias_source: internal_linear
    vin_max_V: 24
    controller_theta_ja_C_per_W: 40
    ambient_max_C: 60
    junction_max_C: 150
    temperature_margin_C: 20
    current_limit:
      output_current_max_A: 3
      vin_max_V: 24
      vout_V: 5.2
      inductor_each_uH_nominal: 10
      inductor_tolerance_pct: 20
      parallel_inductor_count: 1
      sense_resistor_each_mohm_nominal: 5
      sense_resistor_tolerance_pct: 1
      parallel_sense_resistor_count: 1
      threshold_nominal_mV: 50
      threshold_min_ratio: 0.9
      threshold_max_ratio: 1.1
      required_peak_margin_pct: 10
      sense_ripple_min_mV: 10
      peak_current_path_rating_A_min: 20
      peak_current_path_margin_pct: 10
      evidence: fixture bounded threshold, shunt, inductor and path ratings
    switches:
      - {refs: QH, part: NFET60, qg_nC: 20, qg_basis: maximum,
         qg_test_voltage_V: 10, evidence: datasheet table row}
      - {refs: QL, part: NFET60, qg_nC: 15, qg_basis: maximum,
         qg_test_voltage_V: 10, evidence: datasheet table row}
"""

SURGE = """schema: 1
paths:
  - name: input
    source_operating_max_V: 24
    source_tolerance_included: true
    source_boundary_evidence: commissioned absolute input limit
    voltage_margin_pct: 2
    tvs: {part: TVS24, standoff_V: 24, clamp_max_V: 38,
          waveform_duration_ms: 1, waveform: 10/1000 us,
          evidence: exact datasheet row}
    exposed:
      - ref: U4
        part: LOAD
        recommended_max_V: 32
        absolute_max_V: 40
        absolute_max_duration_ms: 400
        transient_qualification: {grade: cited, max_V: 39,
          max_duration_ms: 1, evidence: source transient specification}
      - ref: Q1
        part: FET
        recommended_max_V: 60
        absolute_max_V: 60
"""


def project(req=REQ, power=POWER, stages=STAGES, surge=SURGE):
    d = tmpdir("early_design_")
    rules = d / "03_src" / "rules"
    rules.mkdir(parents=True)
    for name in ("CTRL", "NFET60", "TVS24", "LOAD", "FET"):
        pd = d / "02_parts" / name
        pd.mkdir(parents=True)
        (pd / "part.yaml").write_text(f"mpn: {name}\ntype: fixture\n")
    (rules / "requirements.yaml").write_text(req)
    (rules / "power_tree.yaml").write_text(power)
    (rules / "power_stages.yaml").write_text(stages)
    (rules / "protection_paths.yaml").write_text(surge)
    return d


@test("EARLY-DESIGN passes a fully bounded external-power design")
def t_clean():
    r = must_pass(run([sys.executable, ED, project()]), "clean early design")
    contains(r.out, "EARLY-DESIGN PASS", "clean verdict")
    for gate in ("D-SPEC/E-PATH", "E-SWDRV", "E-SURGE"):
        contains(r.out, gate, "clean evidence")


@test("D-SPEC rejects a power claim with no measurement plane", kind="known_bad")
def t_missing_plane():
    p = project(req=REQ.replace("    measurement_plane: mated_test_plug\n", ""))
    must_fail(run([sys.executable, ED, p, "--requirements"]),
              "missing measurement plane", "measurement_plane")


@test("E-PATH rejects a claimed path that omits mated contacts", kind="known_bad")
def t_missing_path_element():
    bad = POWER.replace(
        "      mated_power_contacts: {value: 80, basis: qualified_max, evidence: connector qualification}\n",
        "      regulator_misc: {value: 80, basis: budgeted_max, evidence: typed budget}\n")
    must_fail(run([sys.executable, ED, project(power=bad), "--requirements"]),
              "incomplete output path", "mated_power_contacts")


@test("D-SPEC rejects prose-only boundaries without structured included and "
      "excluded elements", kind="known_bad")
def t_unstructured_boundary():
    bad = REQ.replace(
        "    included_elements: [protection_switch, pcb_copper_vias_joints, mated_power_contacts]\n",
        "")
    must_fail(run([sys.executable, ED, project(req=bad), "--requirements"]),
              "prose-only boundary", "included_elements")


@test("E-PATH rejects bare resistance scalars without worst-case evidence",
      kind="known_bad")
def t_bare_ir_scalar():
    bad = POWER.replace(
        "protection_switch: {value: 10, basis: maximum, evidence: DS max}",
        "protection_switch: 10")
    must_fail(run([sys.executable, ED, project(power=bad), "--requirements"]),
              "bare path scalar", "bare number")


@test("E-PATH rejects an externally exposed rail that has no claim",
      kind="known_bad")
def t_unclaimed_external():
    bad = POWER.replace("    external_output: false\n", "    external_output: true\n")
    must_fail(run([sys.executable, ED, project(power=bad), "--requirements"]),
              "unclaimed external rail", "has no D-SPEC power claim")


@test("E-SWDRV rejects typical-only MOSFET gate charge", kind="known_bad")
def t_typical_qg():
    bad = STAGES.replace("qg_basis: maximum", "qg_basis: typical", 1)
    must_fail(run([sys.executable, ED, project(stages=bad), "--switching"]),
              "typical gate charge", "typical values cannot prove")


@test("E-SWDRV rejects a component identity that does not resolve to the part "
      "dossiers", kind="known_bad")
def t_unknown_switch_part():
    bad = STAGES.replace("part: NFET60", "part: INVENTED_FET", 1)
    must_fail(run([sys.executable, ED, project(stages=bad), "--switching"]),
              "invented switch part", "does not resolve to 02_parts")


@test("E-SWDRV rejects gate plus bias current above the controller limit",
      kind="known_bad")
def t_gate_current():
    bad = STAGES.replace("controller_current_limit_min_mA: 40",
                         "controller_current_limit_min_mA: 15")
    must_fail(run([sys.executable, ED, project(stages=bad), "--switching"]),
              "overloaded gate driver", "exceeds 15")


@test("E-SWDRV schema 2 rejects a missing peak-current-limit proof",
      kind="known_bad")
def t_missing_current_limit():
    start = STAGES.index("    current_limit:\n")
    end = STAGES.index("    switches:\n", start)
    bad = STAGES[:start] + STAGES[end:]
    must_fail(run([sys.executable, ED, project(stages=bad), "--switching"]),
              "missing current-limit proof", "cannot be deferred")


@test("E-SWDRV rejects a current-limit tier below load plus ripple and margin",
      kind="known_bad")
def t_low_peak_current_limit():
    bad = STAGES.replace("threshold_nominal_mV: 50",
                         "threshold_nominal_mV: 20")
    must_fail(run([sys.executable, ED, project(stages=bad), "--switching"]),
              "under-rated peak current limit", "worst-low peak is below")


@test("E-SWDRV rejects a worst-high current limit above the power-path rating",
      kind="known_bad")
def t_high_peak_current_limit():
    bad = STAGES.replace("peak_current_path_rating_A_min: 20",
                         "peak_current_path_rating_A_min: 12")
    must_fail(run([sys.executable, ED, project(stages=bad), "--switching"]),
              "current limit above path rating", "worst-high peak exceeds")


@test("E-SURGE rejects a clamp above an exposed absolute maximum",
      kind="known_bad")
def t_clamp_over_abs():
    bad = SURGE.replace("absolute_max_V: 40", "absolute_max_V: 38")
    must_fail(run([sys.executable, ED, project(surge=bad), "--surge"]),
              "clamp over absolute maximum", "exceeds absolute maximum")


@test("E-SURGE rejects an owed transient qualification", kind="known_bad")
def t_owed_transient():
    bad = SURGE.replace("grade: cited", "grade: owed")
    must_fail(run([sys.executable, ED, project(surge=bad), "--surge"]),
              "owed transient qualification", "not measured/cited")


if __name__ == "__main__":
    sys.exit(main())
