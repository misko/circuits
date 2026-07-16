---
id: 0004
date: 2026-07-16
status: accepted
---
# 0004 — Front-end: LM74800-Q1 + b2b FETs; ladder doubles as battery UVLO

## Context
A reversed XT60 pigtail is a when-not-if field event, and an unattended 3S
LiPo must not be drained below ~3.0 V/cell. No MCU exists to supervise.

## Options
- **Nothing (keyed connector)** — REJECTED: keying protects against the
  plug, not the pigtail wiring; a reversal puts −12 V on both bucks.
- **Series Schottky** — REJECTED: 0.5 V × 8 A ≈ 4 W of heat, 10% of budget.
- **P-FET clamp** — cheap, but a new unverified part and no UV/OV function.
- **LM74800-Q1 + 2× CSD18543Q3A common-drain** — verified stack (SPF);
  blocks reverse, ~1.1 W at full load, and its EN/OV ladder gives hardware
  battery-UVLO (9.33 V on) and charger-OV (15.25 V) for free — the closest
  thing to a battery protector an MCU-free board gets.

## Decision
LM74800-Q1 + b2b CSD18543Q3A, ladder 887k/52k3/82k5.

## Consequences
+$3 and ~120 mm² vs bare input. UV cutoff hysteresis is the controller's
internal EN hysteresis — coarse; measured at bring-up. Storage drain is the
12 µA ladder: fine for weeks, still disconnect for months.
