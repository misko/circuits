> Adopted 2026-07-21 into crow-recorder-central from archived_projects/crow-array-central (provenance ADR 0011; re-verified by this project's own gates before any release). Original text follows.

# ADR-0001 — 4-layer stackup (JLC7628), not 6

Status: accepted 2026-07-18 (brief §5A: "four PCB layers minimum; six
layers preferred" — layer count delegated to us, D3 in BRIEF.md)

## Context

Needs on this board: (a) continuous ground reference under a short USB-HS
diff pair (brief §5A), (b) a quiet analog region for two PCM1865s fed by
per-port RC networks, (c) escape of a 0.4mm-pitch TQFP-128 plus two
TSSOP-30s, (d) power distribution for five rails at <=1A each, (e) cost —
the whole central-electronics budget is $79-90 (§8A), fab+assembly
$100-250 (§8).

## Options

- **4L JLC7628: F sig / In1 solid GND / In2 power islands / B sig+pour.**
  One unbroken GND plane directly under EVERY F.Cu signal (USB pair,
  clocks, TDM, analog) satisfies (a),(b),(c: escapes are peripheral, see
  ADR-0004). Rails at <=1A need islands, not planes-per-rail. JLC 4L is
  the cheap standard tier (~$30-60/5 at this size).
- **6L (sig/GND/sig/PWR/GND/sig).** Buys a second routing layer and
  GND-sandwiched inner signals. Rejected: nothing here is dense enough to
  need it — the TQFP is peripheral (no BGA-style depth escape), signal
  count is ~60 nets beyond power, and the 136-part SPF power board routed
  clean on 4L with the same toolchain. 6L doubles fab cost and adds no
  gate we could pass that 4L fails.

## Decision

4 layers, JLC7628 stackup. USB 90R diff geometry per JLC's 7628 impedance
table for the ~10mm pair (0.25mm width / 0.20mm gap class, exact values in
DETAIL_DESIGN.md §USB); at this length (<< lambda/10 at 480MHz knee) the
tolerance window is wide. In1.Cu is THE reference plane: policy R-PLANE
named-region checks (analog band, USB corridor) gate on its continuity;
In2 carries the 3V3 / 0V9 / 5V / 3V3A islands (P6: splits only on the
power layer, never the reference layer).

## Revisit trigger

If routing saturates F/B under the RJ45 channel strip or the analog band
cannot keep beeper copper out (audit fails), escalate to 6L rather than
weaken the invariants.
