---
id: 0001
date: 2026-07-16
status: accepted
---
# 0001 — Two independent 5 V bucks: one for the USB-A trio, one for USB-C

## Context

Total 5 V load is 3x2.5 A + 6 A = 13.5 A worst case from a 9.0-12.6 V
source. One converter, four converters, or two converters all satisfy the
brief; the choice drives part count, layout area, thermal spread, and
whether a fault on one port group drags down the other.

## Options

- **Single 13.5 A rail** — one converter, minimum parts. REJECTED: 13.5 A
  from a monolithic buck is out of reach (needs controller + external FETs,
  the most layout-critical and highest-risk option), a single point of
  failure for every port, and one huge hot loop.
- **Per-port bucks (4x)** — inherent per-port limiting. REJECTED: 4
  converters + 4 inductors for no functional gain (the ports are
  capability-rated, not precision-limited — BRIEF A1); doubles hot loops
  to route and the BOM.
- **Two rails: 5V_A (8 A, three USB-A) + 5V_C (6 A, USB-C)** — two
  identical medium-current converters, each within monolithic/simple-buck
  reach; a USB-C overload cannot brown out the USB-A trio and vice versa;
  two copies of one proven circuit.

## Decision

Two independent 5 V buck rails: 5V_A rated 8 A feeding the three USB-A
ports, 5V_C rated 6 A feeding the USB-C port.

## Consequences

Two inductors, two hot loops, two feedback networks to place and route; the
converter circuit is designed once and instantiated twice (rail A sized for
8 A governs). Board area ~ two TO-263/QFN power stages. If the user later
requires true per-port 2.5 A limiting, per-port switches must be added
downstream of 5V_A (BRIEF A1 escalation).
