# Pre-route topology review — USB Controlled Debug Hub v2

review_stage: pre-route
review_kind: topology
design_verdict: SOUND
netlist_sha256: 415ed5f78099519b05c7bce13fd1e95a9532578aefef0adefd7c5e5c01f3a4ce
parts_sha256: 5b7c3bc4fac920871378776dae0bae8dc84dbc28d80715fd51fabfef45c6ee48
design_rules_sha256: 753a8d737d660ca4efb41bc3403da5e5da911881e5239b5568cf5172a50870d9
reviewed_at: 2026-08-18T21:02:00-07:00

## Scope and result

The exact generated netlist, part dossiers, ADR-0014, protection paths, power
tree, and 121 electrical invariants were reviewed before PCB regeneration. No
topology or ratings defect was found.

- USB-C POWER is a sink-only 15 V contract. The CH224K configuration, fused
  and TVS-protected input, and TPS259470A input eFuse keep the converter's
  20 uF input bank disconnected at the default 5 V attach state.
- The input eFuse divider gives a full-corner 9.646–10.329 V UVLO rising
  threshold and 17.381–18.653 V OVLO threshold. Its output alone supplies the
  TPS56637 input bank.
- The TPS56637 feedback network computes to 5.074–5.247 V at the regulator.
  Aggregate eFuse and common-copper worst-case drop retain a 4.903 V protected
  floor at the 2.58 A normal simultaneous-load point.
- Each external port uses one TPS259470A true reverse-current-blocking eFuse.
  The 5.90 kOhm ILIM network bounds each port to approximately 0.503–0.628 A;
  the modeled switch/copper/contact drop is 88 mV at 0.5 A, below the 150 mV
  delivery headroom.
- The internal management function retains the TPS2557 with a 187 kOhm,
  1% programmer, the largest value inside TI's recommended range. The three
  datasheet equations bound its fault limit to 0.468–0.706 A; its commissioned
  load remains at or below 0.10 A. It is load-only and cannot source an
  external port.
- The upstream USB-C connector carries USB 2.0 data/VBUS sense only; its CC
  pins are both 5.1 kOhm Rd. Downstream data switches and power switches remain
  hardware-interlocked by the hub policy outputs and host commands.
- Aggregate simultaneous worst-case branch limiting is 3.698 A, intentionally
  inside the timed aggregate latch's trip envelope. The commissioned 2.58 A
  normal load remains 0.410 A below the aggregate eFuse's 2.990 A worst-low
  threshold. USB source capacitance remains 128.664 uF effective against the
  120 uF contract.

Machine corroboration on this subject: ERC errors 0; E-INV 121/121; E-ADR 5/5;
early-design 5/5; power topology 7/7; voltage-margin 6/6.

The remaining JLC PCB-assembly availability/MOQ response is a manufacturing
evidence hold, not an electrical-topology defect. It must remain explicit in
the release and may not be inferred from catalog stock.

The review was rebound after the placement-stage rule refinement that moved
the four ILIM resistors, separated the downstream PD bulk bank, and split the
input-gate/buck-enable sense launch areas. These changes do not alter the
reviewed netlist or part denominator.

The renewed rules digest additionally binds the 0.30 mm footprint-relative
TPS259470A input/output launch areas and the local 100 nF PD-input bypass
branch. These are bounded package transitions; global current-path widths are
unchanged outside their named areas.
