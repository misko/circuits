---
id: 0001
date: 2026-07-31
status: accepted
tags: [spec-tension, protection, topology]
---
# 0001 — USB-A 3 A is a proprietary high-current capability

## Context

The commission requires four USB-A downstream sockets capable of delivering
3 A each. USB 2.0 and USB Battery Charging do not provide a standards-based
USB-A mechanism equivalent to USB Type-C's 3 A current advertisement. The
connector contacts, power switch, copper, and source must nevertheless safely
carry the requested current.

## Options

- Limit the ports to standard USB 2.0 current. Rejected because it does not
  meet the explicit 3 A requirement.
- Change the downstream connectors to USB-C. Rejected because Q1 explicitly
  selects four USB-A sockets.
- Provide 3 A as a documented proprietary power capability while retaining
  standards-compliant USB 2.0 data signaling. Selected, conditional on a cited
  >=3 A continuous connector rating and explicit current limiting.

## Decision

Each external port will provide USB 2.0 data and an independently protected
5 V / 3 A power path, but project and silkscreen documentation will not claim
USB-IF compliance for the 3 A USB-A charging mode. A receptacle without a cited
continuous rating of at least 3 A is not acceptable merely because the load
switch trips at 3 A.

## Consequences

The parts stage must prove the connector contact rating and sourcing route.
Every port needs a separately enabled current limiter, fault feedback, local
capacitance, and backfeed analysis. Host software must distinguish electrical
capability from what a connected legacy device is entitled or able to draw.
The protection topology is emitted into `03_src/rules/electrical_invariants.yaml`
once refdes and nets exist.
