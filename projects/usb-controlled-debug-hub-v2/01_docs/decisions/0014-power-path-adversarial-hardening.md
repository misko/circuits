# ADR-0014 — harden attach inrush and externally exposed VBUS paths

Status: accepted  
Date: 2026-08-18  
Partially supersedes: ADR-0012 reuse disposition for the four external
TPS2557 channels; ADR-0013 direct buck-input capacitance and feedback values.

## Context

The v0.1.0 adversarial review found three coupled power defects:

1. `R_PD_VDD` was a 1 kOhm 0402 rated 62.5 mW. With CH224K's 3.24–3.36 V
   shunt rail and a 15 V contract it dissipates about 135–138 mW nominal and
   173–176 mW at the former 16.5 V analysis bound.
2. Two 10 uF capacitors plus 100 nF were permanently visible at the POWER
   receptacle. A Type-C sink must not expose more than 10 uF at initial attach;
   the TPS56637 simultaneously requires more than 10 uF at VIN.
3. TPS2557 does not block a powered downstream target from driving a disabled
   or unpowered hub VBUS rail. That is an avoidable bench-debug hazard even
   though compliant USB peripherals are not supposed to source VBUS.

## Decision

- Replace only `U_PWR1..4` with `TPS259470ARPWR` / JLC `C3662799`. Retain
  `U_PWR_CTRL` as the purchased TPS2557 because its output is internal and
  cannot be driven by an external cable.
- Program retained `U_PWR_CTRL` with 187 kOhm 1% (`C163486`), the largest
  value inside TI's recommended 20–187 kOhm range. The full-corner datasheet
  equations give a 0.468–0.706 A protection window; its commissioned load
  budget remains 0.10 A. The earlier 210 kOhm candidate is rejected as an
  out-of-range extrapolation, not treated as a valid 0.15 A setting.
- Program each external eFuse with 5.90 kOhm 1% (`C23071`). TI equation 5,
  `ILIM = 3334/RILM`, with ±10% IC accuracy and ±1% resistance gives
  0.503–0.628 A before the small TCR term. Pin 4 `FLT` remains the direct
  active-low USB2517I `OCS_N` signal; no inversion or firmware is introduced.
- Add `U_PD_IN`, another TPS259470A, between `VBUS_PD` and a new
  `VBUS_PD_SW` buck-input rail. The receptacle sees only the 100 nF local input
  bypass; the two required 10 uF buck capacitors are downstream of `U_PD_IN`.
- Use 470 kOhm / 28.7 kOhm / 35.7 kOhm 1% for `U_PD_IN` UVLO/OVLO. Charging
  resistor tolerance and TI's 1.183–1.223 V rising thresholds gives a
  9.646–10.329 V turn-on window and a 17.381–18.652 V turn-off window. Thus
  default 5 V cannot connect the bulk bank, while a valid 15 V contract can.
- Use 3.3 nF C0G on `U_PD_IN.DVDT` and 1 kOhm 0.1% on ILM. The input eFuse is
  an inrush controller and secondary current limiter; the 3 A fuse remains the
  input branch's primary sacrificial protection.
- Change `R_PD_VDD` to a 1 kOhm, 0.5 W, 1210 resistor (`C52444`). At 16.5 V
  and the lowest 3.24 V shunt corner its calculated dissipation is 176 mW,
  below 50% of rating.
- Change `R_PD_FB_B` from 499 Ohm to 1.00 kOhm 0.1%. With the existing 75 kOhm
  and 10 kOhm 0.1% legs and the TPS56637 0.591–0.609 V reference, the full
  output window is 5.07363–5.24667 V. This restores loaded-plug margin for the
  new external switches without exceeding USB's 5.25 V ceiling.
- Short CH224K DP and DM locally because the POWER receptacle is deliberately
  PD-only; its connector D+/D- pads remain unconnected.

## Why this implementation

TPS2553 was considered first because it is inexpensive and stocked, but its
135 mOhm hot maximum consumes nearly all of the qualified 4.75 V plug margin.
TPS25210 provides low-loss true reverse blocking but exposes `PG`, not the
active-low fault behavior required by USB2517I, and would need per-channel
logic. TPS259470A has 45 mOhm maximum resistance, true reverse-current
blocking, active current limiting, the required active-low `FLT`, and reuses
the exact RPW0010A footprint already qualified for `U_AGG`.

The new external active parts cost more and are the only exception to the
high-cost reuse preference. The change is justified by an externally applied
power threat that the retained part cannot meet. All hub, management, data
switch, regulator and internal power-switch ICs remain unchanged.

## Authorities

- TI TPS25947 datasheet SLVSFC9C: device table, true reverse-current blocking,
  pin table, RON, equation 5 and equations 10/11.
- TI TPS2553 datasheet SLVS841F: 135 mOhm hot maximum and delayed
  reverse-voltage response used to reject the low-cost candidate.
- WCH CH224 manual v2.1: CH224K pin table, 15 V strap table and reference
  schematic.
- TI TPS56637 datasheet SLVSEG1A: VIN decoupling and feedback requirements.
- USB Type-C Cable and Connector Specification sink attach model; TI's Type-C
  power-path guidance independently describes the 1–10 uF sink-side bank.

## Consequences and validation

- The four port-switch footprints and local copper must be regenerated and
  re-routed; this is a real PCB revision, not a BOM substitution.
- Verify powered-target tests with hub power absent and with each port disabled,
  recording reverse leakage and upstream-rail rise.
- Capture POWER attach at default 5 V and at successful 15 V negotiation. The
  buck-side bulk bank must remain disconnected at 5 V and rise monotonically
  only after the eFuse UVLO threshold is crossed.
- Re-run full loaded-plug voltage, fault, thermal, USB SI, model-registration,
  rotation and order-allocation gates before release.
