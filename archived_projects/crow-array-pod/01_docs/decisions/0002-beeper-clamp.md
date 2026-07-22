# ADR-0002 — beeper clamp: dual footprint, SS14 flyback populated, TVS empty

Status: accepted 2026-07-18 (implements commission A3/P7 "configurable
clamp type (flyback vs TVS)")

## Context

The CMT-8504 magnetic transducer (coil, 15R, ~mH) is switched at 4 kHz by
a low-side AO3400A at the CENTRAL end of a 35 ft pair. Opening the switch
with coil current flowing needs a clamp at the pod or the kick rings the
pair (and couples into the adjacent audio pairs).

## Decision

Two DO-214AC/SMA positions in parallel across BZ_P/BEEP_RET, identical
orientation (pad1 = cathode = supply side):

- **D2 SS14 schottky — POPULATED.** Classic flyback: clamps at 5V+0.4V,
  slow decay, minimal EMI. 1 A / 40 V rating dwarfs the 150 mA / 5 V duty.
- **D3 SMAJ6.0A TVS — EMPTY.** The doc's alternative: a TVS lets the coil
  de-energize at ~7-10 V instead of 0.4 V (faster current decay, crisper
  burst envelope for the matched filter) at the cost of a harder edge.
  6.0 V standoff chosen because the pair sits at a full 5 V whenever the
  central switch is ON; a 5.0 V part would operate at its standoff limit.

Populate-state matrix is silk-labeled (FLYBACK / TVS) and repeated in
ORDER_README. Swap = move one SMA part; no track changes. R12 (0R) in the
+5V_BEEP leg is the doc's "series pads" — a swap point for a series
resistor if range tests want lower drive.

## Rejected

- RC snubber only: needs tuning per cable length; diode clamp is
  length-insensitive.
- Clamp at central only: leaves the 35 ft pair itself as the flyback loop
  antenna. The pod-side clamp keeps the loop 10 mm, not 10 m.
