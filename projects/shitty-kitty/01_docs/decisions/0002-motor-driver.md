---
id: 0002
date: 2026-07-17
status: accepted
---
# 0002 — Stepper driver: TMC2209 over DRV8825 (P4 "DRV8825 like ... or better")

## Context

P4: NEMA17 bipolar 1A, "DRV8825 like motor driver with 1/32 microstepping".
A3 (user): on-board driver IC, JLC-assemblable, cost-optimizable at 10k.
The mechanism lives centimeters from a cat's paws and a toilet user —
audible noise and safe failure modes matter.

## Live JLC data (2026-07-17, 06_build/cache/adr_stock_2026-07-17.json)

| Part | Code | Price@1 | Stock | Lib |
|---|---|---|---|---|
| TMC2209-LA-T (QFN-28-EP 5x5) | C2150710 | $2.64 | 10,544 | Extended |
| DRV8825PWPR (HTSSOP-28-EP) | C81582 | $2.17 | 7,450 | Extended |
| TMC2208-LA-T | C115944 | $2.55 | 7,158 | Extended |

## Decision: TMC2209-LA-T (C2150710)

- **Quiet**: StealthChop2 voltage chopper — near-silent stepping vs the
  DRV8825's audible mixed-decay whine. Cats are noise-averse; the cup
  moves while a cat may be ON the lid.
- **Meets and beats the microstepping spec**: native 8/16/32/64 microsteps
  via MSTEP pins, up to 1/256 with interpolation (MicroPlyer) — P4's 1/32
  satisfied with smoother motion.
- **Fewer externals**: internal RDSon current sensing — no 2x 0.15-0.33R
  power sense resistors (DRV8825 needs them + a 3.3nF/VREF divider).
  Run current is set over UART (IRUN) or VREF; we wire UART.
- **StallGuard4 (DIAG output)**: sensorless load/stall detection to a GPIO
  — a bonus safety layer (paw-jam detection) ON TOP of the endstop, and a
  potential endstop replacement at 10k-unit cost optimization.
- **UART config** = firmware-tunable current/mode without BOM changes.
- Electricals: 4.75-29V VS (12V fine), 2A RMS capability >= 1A motor.
- Cost: $0.47 more than DRV8825PWPR at qty 1; at 10k the gap narrows
  (~$1.9 vs ~$1.6) and removing two power sense resistors + one heatsink
  consideration recovers part of it. Chosen anyway on noise + safety.

Rejected: DRV8825PWPR (noise, sense resistors, 8.2V min VS is tight for
an 11V sagging brick); TMC2208 (no StallGuard/DIAG, 1.4A rating margin
thinner, same price class).

## Safety invariant (hardware, cat-safety class)

TMC2209 ENN (enable, active LOW) gets a 10k pull-UP to 3V3: the motor is
DISABLED at boot/reset/unprogrammed until firmware drives ENN low. Same
class as the laser-off-at-boot rule in esp32-laser-timing. DIAG -> GPIO,
INDEX -> GPIO (optional position telemetry).
