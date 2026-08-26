---
id: 0002
date: 2026-08-10
status: accepted
---
# 0002 — Dual integrated buck modules

## Context

The output ranges are always below the 9V minimum input, so both converters are
plain bucks. All ports require 9A continuous and 10.5A coincident peak at 5V.
One 8A/10A module cannot cover the board, while reusing v3's two LM5116 cells
would recreate controller, MOSFET, inductor, shunt, gate-drive, compensation and
Kelvin-layout obligations that caused large pipeline and review cost.

## Options

- One TPSM63610 for all outputs — rejected because load exceeds both its rated
  and peak current.
- Two discrete LM5116 cells — electrically possible, but rejected on total
  design/integration complexity and the history of difficult review/routing.
- TPSM63610 for the three USB-A ports plus TPSM63604 for the Pi — selected.

## Decision

Use TPSM63610RDFR for the 6A continuous/7.5A peak USB-A bank and an independent
TPSM63604RDLR for the 3A Pi rail. Both are synchronous buck power modules with
integrated controller, MOSFETs, inductor and protection.

## Consequences

Stage 2 follows the exact TI application requirements rather than calculating
an external gate-drive/current-sense/compensation cell. Unit cost is higher,
and the thermal land pattern requires an advanced via-in-pad process (ADR-0004).
The split also improves load-step isolation and preserves rated-current margin.
