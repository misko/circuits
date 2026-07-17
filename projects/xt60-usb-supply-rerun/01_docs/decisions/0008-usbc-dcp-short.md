---
id: 0008
date: 2026-07-16
status: accepted
---
# 0008 — USB-C D+/D- shorted as BC1.2 DCP (both row pairs)

## Context

Fresh-eyes review: with J5's D+/D- floating, a legacy device on an
A-to-C cable sees a Standard Downstream Port and falls back to 500 mA,
defeating the port's purpose. The four data pads (A6/A7 top row, B6/B7
bottom row — the cable uses one pair per plug orientation) were NC.

## Options

- **Leave floating** — spec-pure for a 5V source relying on CC alone.
  REJECTED: silently caps legacy sinks at 500 mA.
- **Short A6+A7+B6+B7 into one DCP node** — BC1.2 Dedicated Charging
  Port signature (D+ shorted to D- < 200 ohm), same scheme as the three
  USB-A ports. Zero parts: the four pads are physically contiguous in
  the row; one 0.25 mm track across their tips joins them.

## Decision

Short all four J5 data pads into net DCPC (BC1.2 DCP), as designed
copper with a router keepout over the corridor.

## Consequences

Legacy A-to-C devices detect a DCP and draw up to 1.5 A+ (BC1.2);
CC-aware sinks still read 3 A from Rp (ADR 0002). The port can never be
a data port (already true — no host on this board). Pin review must
verify A6/A7/B6/B7 all on DCPC.
