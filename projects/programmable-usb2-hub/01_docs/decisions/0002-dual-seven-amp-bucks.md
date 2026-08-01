# ADR-0002 — Dual 7 A buck rails

status: accepted
date: 2026-07-31
tags: [topology, power, protection, thermal]

## Context

Four ports must each deliver 5 V at 3 A. Including hub and control logic, a
single rail would need roughly 13 A and would require a new high-current power
stage, inductor, compensation proof, and concentrated thermal solution. The
repository already carries a manufacturer-worked, locally reviewed LM5116
5 V / 7 A synchronous-buck cell.

## Decision

Use two electrically independent LM5116 buck cells regulated to nominally
5.15 V. Rail A feeds ports 1 and 2; rail B feeds ports 3 and 4. Each rail has a
6 A declared continuous load and 1 A design margin. The logic rail is derived
separately and is not counted against either port pair's 6 A delivery promise.

The input is common and protected before it branches. A fault on one buck may
remove two ports but must not propagate through the other port rail except by
input protection operation.

## Consequences

- Reuses a cited 5 V / 7 A reference design and known layout constraints.
- Splits heat, switch-node area, output capacitance, and 12 A downstream copper.
- Adds one controller/FET/inductor cell versus a single large converter.
- Requires two reserved LM5116 escape corridors and two independently scoped
  switch nodes during first-board qualification.

## Machine-checkable obligations

- `power_tree.yaml` declares both BUCK converters, 6 A loads, efficiency, and
  delivery resistance.
- `electrical_invariants.yaml` binds each port switch input to the assigned
  rail and prevents cross-rail shorting.
- Floorplan keeps the two hot loops separated and gives each controller a
  clear escape corridor.
