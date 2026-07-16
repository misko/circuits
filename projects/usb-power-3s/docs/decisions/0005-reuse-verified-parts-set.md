---
id: 0005
date: 2026-07-16
status: accepted
---
# 0005 — Bias every selection toward the SPF-verified parts set

## Context
An earlier board burned days on part-selection failures: string-matched
wrong-voltage caps, a motor driver proposed as an ideal-diode controller, a
thermistor coded as a resistor, unobtainable MPNs. It ended with ~30 MPNs
whose pin maps, polarity, JLC codes and stock behavior are verified.

## Options
- **Green-field selection per function** — REJECTED: re-pays the burn-in
  cost for zero design benefit at these operating points.
- **Verified-set-first** — new parts only where no verified part fits
  (this board needs exactly two new values: 432 Ω, 24k3, 52k3 — resistors).

## Decision
Verified-set-first. Deviations require their own ADR.

## Consequences
BOM inherits known LCSC codes, rotation-DB entries and `part.yaml` facts;
sourcing risk concentrates on already-watched thin-stock lines (LM5145,
MWSA inductor — check stock at order). Design headroom follows SPF's
operating envelope; rail B's +25% is the one place we exceed it (ADR-0001).
