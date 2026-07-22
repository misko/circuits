---
id: 0005
date: 2026-07-16
status: accepted
---
# 0005 — 4-layer JLC standard tier, GND plane on In1

## Context

Two 5 V bucks moving 6-8 A each at a few hundred kHz need a solid return
plane under their hot loops; 13.5 A of 5 V distribution plus an 8.5 A
input trunk need copper cross-section. Board must pass JLC standard-tier
DRC floors with margin.

## Options

- **2-layer** — cheaper (~$2 less on a small board). REJECTED: every pour
  on the bottom is sliced by routing, GND return integrity under the
  switch nodes depends on routing luck, and the previous-generation
  tooling/gates are proven on 4-layer.
- **4-layer, 1 oz outer / 0.5 oz inner (JLC standard 4L)** — In1 as an
  unbroken GND plane, In2 as a secondary power/GND plane, outer layers for
  power pours and routing. ~0.5 mm² per 3 A on outer pours is easily met.

## Decision

4-layer JLCPCB standard tier (JLC04161H-7628): F.Cu = power pours +
routing, In1.Cu = solid GND, In2.Cu = GND + 5 V pour patches as needed,
B.Cu = routing + pour patches. Standard vias 0.6/0.3; floors per
jlc_4layer standard tier (0.10 clearance / 0.09 track / 0.45-0.20 via).

## Consequences

Costs a 4L order (~$8 for 5 boards at 100x60 mm class). No small-via
(advanced) option needed — keeps the order on the cheap tier; if routing
later demands 0.45/0.2 vias that is still within standard 4L capability.
Ampacity: trunk currents ride F.Cu pours per rules/nets.yaml; In1 must
never be split by routing (gate: no tracks on In1).
