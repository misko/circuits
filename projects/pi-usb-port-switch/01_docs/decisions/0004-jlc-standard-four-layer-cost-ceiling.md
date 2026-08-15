---
id: 0004
date: 2026-08-14
status: superseded-by-0005
---
# 0004 — JLC standard four-layer cost ceiling

## Context

USB 3 Gen 1 pairs need a continuous adjacent reference plane and controlled
impedance. The candidate redriver, USB 2 switch and ESD array use fine-pitch
packages, but their high-speed pins can leave on the outer layer without a
through-via fanout if placement is disciplined.

## Options

- **Two-layer default** — cheapest, but cannot provide the same continuous
  reference-plane and power-distribution architecture with four USB 3 paths.
- **Four-layer standard** — adds the required adjacent plane while retaining
  JLC's standard 0.127 mm track/space and 0.45/0.30 mm via floors.
- **Four-layer advanced** — enables smaller geometry and via-in-pad, but adds
  manufacturing cost before an exact footprint proves it necessary.

## Decision

Declare `jlc_4layer_standard` as the commission cost ceiling.

## Consequences

Every selected footprint must pass `escape_check.py` at this tier. Placement
must reserve outward top-layer escape corridors for the fine-pitch USB parts.
If an exact package needs advanced geometry, work stops for a D-TIER ADR rather
than silently enabling a paid option.
