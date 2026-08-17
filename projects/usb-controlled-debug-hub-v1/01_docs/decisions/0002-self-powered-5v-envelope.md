# ADR-0002 — self-powered 5 V envelope

status: accepted
date: 2026-08-15
tags: [topology, input-protection, power, spec-tension]

## Context

The earlier Pi fixture used a separate supply. A USB 2.0 self-powered hub must
deliver at least 4.75 V at 500 mA at its downstream port, while a USB 3-style
900 mA claim or BC1.2 charging claim is outside this board's data topology.

## Decision

Accept regulated SELV 5.20–5.25 V at `P5V_RAW` under load through a clearly polarity-marked board terminal, rated at
least 3 A continuous and qualified for 5 A / 6 ms transients. Protect the input
with a user-replaceable fuse and a reverse-current-blocking, latch-off aggregate
eFuse. Use one active-high current-limited switch per enabled hub
port. Guarantee four external ports at 4.75–5.25 V / 500 mA continuously at
the mated test plug; make no charging-port claim. Upstream VBUS is sense-only.

Sustained input overvoltage above 5.25 V remains outside the admitted source
envelope. The aggregate eFuse provides a secondary hardware cutoff, but the
board is still commissioned for a regulated 5.20–5.25 V source rather than
crediting that cutoff as source regulation.

Use exact Littelfuse 0297004.WXNV (4 A MINI) in a Keystone 3568 holder. The
normal input estimate is 2.58 A, and Littelfuse's published
typical ambient derating allows 2.9 A at 60 C and 2.7 A at 80 C. Reserve a
mechanically derive and reserve a 4.89 V protected-trunk floor after the common fuse, aggregate eFuse, holder, and input
copper. The simultaneous downstream worst-high envelope is separately bounded
by ADR-0006 rather than being treated as continuous service.

## Machine-checkable obligations

- `requirements.yaml` binds four simultaneous 500 mA output claims.
- `power_tree.yaml` binds input/output envelopes and the measurement boundary.
- Electrical invariants prove no upstream-VBUS path reaches the protected
  external supply and every VBUS switch is gated by its hub power output.
