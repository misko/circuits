---
id: 0006
date: 2026-08-14
status: accepted
---
# 0006 — 5.15 V input drop budget

## Context

The user selected a separate 5 V source. The board must deliver at least
4.75 V at a downstream USB-A mated test plug while all four ports continuously
draw 0.9 A. A protected path includes a replaceable input fuse and holder, a
reverse-polarity MOSFET, shared and branch copper, a TPS2557 current-limited
switch, solder joints, and the output connector. Starting at 5.0 V leaves only
250 mV for all of those elements and their temperature/production variation;
that is not a defensible guaranteed budget.

## Options

- **Keep a 5.0 V minimum and waive the 4.75 V plug guarantee** — accepts
  brownout risk exactly where the fixture is meant to produce repeatable tests.
- **Replace the fuse/reverse-polarity architecture with a more complex ideal
  path** — may recover margin, but increases cost, parts risk, and validation
  effort without eliminating connector and copper drop.
- **Require 5.15-5.25 V at the board terminal** — uses a nominal 5.2 V
  regulated supply and preserves at least 150 mV of additional path budget without exceeding the
  USB 5.25 V ceiling.

## Decision

Require a regulated 5.15-5.25 V source rated at least 5 A, measured at the board
input terminal under simultaneous load. Retain the fuse, reverse-polarity FET,
and TPS2557 per-port limiter. The external supply lead remains outside the
downstream measurement boundary.

## Consequences

The input terminal and documentation must be marked `5.2V REGULATED`; a generic
5.0 V-minimum adapter is not qualified. Pre-layout resistance allocations must
be closed using extracted copper geometry, exact connector limits, and a hot
four-wire first-article measurement. If 5.0 V minimum becomes mandatory, the
power path or the downstream voltage guarantee must be reopened rather than
silently consuming negative margin.
