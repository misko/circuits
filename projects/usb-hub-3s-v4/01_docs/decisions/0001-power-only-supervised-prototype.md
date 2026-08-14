---
id: 0001
date: 2026-08-10
status: accepted
---
# 0001 — Power-only supervised prototype boundary

## Context

The short project name “USB hub” is ambiguous between a USB protocol hub and a
multi-port power source. The user explicitly stated that v4 carries no USB
data, does not need active overvoltage cutoff, and targets JLCPCB. A sustained
converter fail-high event therefore cannot be presented as a fault the board
guarantees to isolate.

## Options

- **USB data hub plus power distribution** — rejected because it contradicts
  the explicit no-data directive and would add a hub controller, clocking,
  differential routing, ESD, and protocol-compliance scope.
- **Power-only distribution with active fail-high cutoff** — technically
  stronger fault containment, but rejected as a requirement by the user's
  explicit direction.
- **Power-only distribution with ordinary overload/reverse/transient
  protection and an explicit supervised-prototype boundary** — selected. It
  matches the requested interface while keeping claims aligned with what the
  eventual circuit can prove.

## Decision

Design v4 as a JLCPCB-manufactured, USB-power-only distribution board with no
USB data paths and no required active sustained-overvoltage cutoff; classify it
as a supervised prototype until a later ADR changes the protection boundary.

## Consequences

USB connectors do not make this a USB data hub, and no USB data or PD PHY may
be added without a new requirement and ADR. The schematic and release material
must not claim deterministic protection of the load against converter
fail-high. Stage 1 must still select and coordinate input, overload,
reverse-feed, ESD/transient, and per-port current protection appropriate to the
actual parts. Any unattended, inaccessible, high-value, or safety-critical use
requires reopening the active-cutoff decision. JLCPCB capabilities and live
catalog data must be verified before parts and fabrication gates close.
