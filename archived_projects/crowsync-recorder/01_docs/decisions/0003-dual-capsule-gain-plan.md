---
id: 0003
date: 2026-07-16
status: accepted
---
# 0003 — One gain resistor covers both PUI capsule options (A1)

## Context

A1: design for BOTH the -24 dB (AOM-5024L-HD class, 63 mV/Pa) and -44 dB
(6.3 mV/Pa) PUI electret capsules; ship -24 dB values; document the
alternate. Codec full scale is 0.785 Vrms (DETAIL_DESIGN §1).

## Options

- **Swap Rg (gain = 1 + Rf/Rg with fixed Rf)** — REJECTED: Rg sets the
  Cg high-pass corner (fc = 1/2πRgCg); swapping Rg 13k -> 1k would move the
  corner 12 Hz -> 159 Hz, gutting the low band for the -44 dB build unless
  Cg swaps too (two-part change).
- **Swap Rf only, Rg = 1k fixed** (chosen) — Rf 3k01 -> 39k changes gain
  4.0x -> 40x; the Cg corner stays at 15.9 Hz for both builds. Exactly one
  BOM line differs.

## Decision

Non-inverting gain 1 + Rf/1k; **ship R11 = Rf = 3k01** (gain 4.0, full scale
at 104 dB SPL with the -24 dB capsule); **-44 dB variant: R11 = 39k**
(gain 40, same 104 dB SPL full scale). R12 = 1k and C20 = 10u never change.

## Consequences

- Field re-targeting is a single 0603 resistor swap; both values are JLC
  basic parts.
- Bias network (2k2 from the filtered 3V3A) already suits both capsules
  (2.2 V at 0.5 mA — inside the 1–10 V window of each).
- Stability/noise checked at the HIGHER gain (40x) in DETAIL_DESIGN §6, so
  the alternate build needs no re-analysis.
