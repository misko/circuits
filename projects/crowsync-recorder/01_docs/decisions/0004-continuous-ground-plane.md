---
id: 0004
date: 2026-07-16
status: accepted
---
# 0004 — Continuous GND plane; analog/digital separation by placement

## Context

P5 requires "a continuous ground reference plane". The PCM2900C has five
ground pins across three analog domains (AGNDC/AGNDX/AGNDP) plus DGND/DGNDU,
and mixed-signal folklore suggests split planes. The skill rule: no split
planes without an ADR justifying it — this ADR justifies NOT splitting.

## Options

- **Split AGND/DGND planes joined at the codec** — REJECTED: at 12 MHz USB
  full-speed + 48 kHz audio, a split forces every USB return current to
  detour around the moat; any trace crossing the split radiates. TI's own
  PCM290x EVMs use a single plane with partitioned placement. A split is
  also exactly what P5 forbids.
- **Single continuous In1 plane, placement partitioning** (chosen) —
  analog front-end (U2, bias, dividers, J2/J3, codec analog pin column) in
  the east region; USB entry, crystal and codec digital pins west/central.
  Return currents follow their traces and never mix because the traces
  don't cross regions.

## Decision

In1.Cu is one unbroken GND plane covering the whole outline. No slots, no
moats. F.Cu/B.Cu GND pours stitch to it. All five codec ground pins tie to
the same plane at their pads.

## Consequences

- Layout gate: In1 carries NOTHING but GND (audit checks no In1 tracks).
- Placement discipline is load-bearing: the audit's proximity checks + the
  render review verify the analog region stays clear of DP/DM and Y1.
- The codec's grounds must not be "star-routed" on F.Cu — each pin drops
  straight to the plane.
