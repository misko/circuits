# ADR-0002 — self-powered 5 V envelope

status: accepted
date: 2026-08-15
tags: [topology, input-protection, power, spec-tension]

## Context

The earlier Pi fixture used a separate supply. A USB 2.0 self-powered hub must
deliver at least 4.75 V at 500 mA at its downstream port, while a USB 3-style
900 mA claim or BC1.2 charging claim is outside this board's data topology.

## Decision

Accept regulated SELV 5.10–5.25 V at `P5V_RAW` under load through a clearly polarity-marked board terminal, rated at
least 3 A. Protect the input with a user-replaceable fuse and low-loss reverse-
polarity MOSFET. Use one active-high current-limited switch per enabled hub
port. Guarantee four external ports at 4.75–5.25 V / 500 mA continuously at
the mated test plug; make no charging-port claim. Upstream VBUS is sense-only.

Sustained input overvoltage above 5.25 V is an excluded source fault. The board
does not silently add active overvoltage cutoff.

Use exact Littelfuse 0297004.WXNV (4 A MINI) in a Keystone 3568 holder. The
aggregate input estimate is approximately 2.6 A, and Littelfuse's published
typical ambient derating allows 2.9 A at 60 C and 2.7 A at 80 C. Reserve a
4.89 V protected-trunk floor after the common fuse, MOSFET, and input copper;
apply the per-port 160 mOhm delivery budget only after that floor.

## Machine-checkable obligations

- `requirements.yaml` binds four simultaneous 500 mA output claims.
- `power_tree.yaml` binds input/output envelopes and the measurement boundary.
- Electrical invariants prove no upstream-VBUS path reaches the protected
  external supply and every VBUS switch is gated by its hub power output.
