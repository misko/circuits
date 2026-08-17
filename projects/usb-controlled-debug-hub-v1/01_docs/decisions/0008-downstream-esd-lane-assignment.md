# ADR-0008 — bind downstream ESD IO1 to D+ and IO2 to D-

status: accepted for release staging
date: 2026-08-17
tags: [usb, signal-integrity, protection, routing]

## Context

ADR-0006 selected the symmetric PESD2USB3UX-TR channels and correctly required
each shunt protector to remain directly on its physical USB pair, but its
downstream prose assigned IO1 to D- and IO2 to D+. The realized U_ESD1 through
U_ESD4 placement and no-crossover routing use the opposite electrically
equivalent channel order: connector D+ reaches IO1 and connector D- reaches
IO2. The existing downstream electrical invariants already describe that
realized pin-to-net mapping, so their ADR authority must name the decision that
actually made it.

This is a narrow downstream correction. It does not supersede ADR-0006's part
selection, capacitance budget, aggregate-fault decisions, upstream U_ESD_UP
assignment, or the common-ground obligation on pin 3.

## Options

- **Retain ADR-0006's downstream IO1=D- prose** — rejected because it
  contradicts both the executable downstream invariants and realized
  connector-facing route geometry.
- **Cross D+ and D- between the receptacle and protector to reproduce that
  prose** — rejected because the channels are electrically symmetric and the
  crossover would add avoidable USB discontinuity solely to preserve a stale
  label assignment.
- **Bind downstream D+ to IO1 and D- to IO2** — selected because it matches the
  actual no-crossover U_ESD1..4 launches without changing protection function
  or logical USB polarity.

## Decision

For U_ESD1 through U_ESD4, assign physical pin 1 (IO1) to the corresponding
`P*_PORT_P` net and physical pin 2 (IO2) to `P*_PORT_N`. Keep physical pin 3 on
GND under ADR-0006. This ADR supersedes only ADR-0006's downstream symmetric
IO1/IO2 assignment; all other ADR-0006 decisions and obligations remain in
force.

## Consequences

- The eight downstream IO1/IO2 `pin_on_net` invariants cite ADR-0008.
- U_ESD1..4 retain their realized placement and no-crossover copper; no board,
  schematic, footprint, CPL, or firmware change follows from this authority
  correction.
- U_ESD_UP remains IO1=D- and IO2=D+ under ADR-0006.
- Any future downstream lane reassignment must re-run electrical invariants,
  schematic parity, and USB route review.
