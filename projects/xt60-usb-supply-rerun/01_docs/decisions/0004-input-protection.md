---
id: 0004
date: 2026-07-16
status: accepted
---
# 0004 — Input protection: fuse -> P-FET reverse polarity -> TVS

## Context

A 3S LiPo can deliver hundreds of amps into a fault, and XT60s get plugged
in a hurry. The board needs: catastrophic-fault interruption, survival of a
reversed pack, and clamping of lead-inductance spikes at hot-plug. A
reversed battery connector has already shipped on a previous board in this
ecosystem (skill failure museum) — reverse protection is not optional.

## Options

- **Series schottky diode** — simplest reverse block. REJECTED: at 8 A
  input current a 0.45 V drop burns ~3.6 W continuously and eats headroom
  at the 9 V pack-empty end.
- **High-side P-FET, gate to GND** — body diode conducts on first contact,
  channel (a few mΩ) takes over; reversed pack leaves the channel off with
  Vgs = 0. Costs one FET + one gate resistor; Vgs(max) must exceed 12.6 V
  (no zener needed below +/-20 V rating).
- **Ideal-diode controller + N-FET** — lowest loss, most parts. REJECTED:
  overkill at 12 V/8 A where a 10 mΩ P-FET dissipates < 1 W.
- **No fuse (rely on buck current limits)** — REJECTED: a shorted FET or
  cap upstream of the bucks would see the full pack; the fuse is the only
  protection there.

## Decision

Battery + -> 15 A fuse -> P-FET (drain to fuse, source to protected rail,
gate to GND through 100 kΩ) -> TVS (SMBJ15A-class, 15 V standoff) + bulk
capacitance -> buck inputs.

## Consequences

One TO-252/TO-263 P-FET with Id >= 25 A and Rds(on) <= ~15 mΩ at
Vgs = -10 V must be stocked (part.yaml); its I^2R at 8 A is < 1 W (pour
copper is the heatsink). Fuse choice must tolerate 12.6 V DC and ~8.5 A
continuous with margin (15 A rating). TVS standoff 15 V > 12.6 V max pack;
clamp < FET/buck Vin(max). Polarity audit on the XT60 (pad 1 = "-" blade
in the KiCad AMASS footprint) is a release gate line.
