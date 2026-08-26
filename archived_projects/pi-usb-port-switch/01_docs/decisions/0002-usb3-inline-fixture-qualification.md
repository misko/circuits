---
id: 0002
date: 2026-08-14
status: accepted
---
# 0002 — USB 3 inline fixture qualification

## Context

The fixture adds an upstream cable, two PCB connectors, ESD protection and a
controlled disconnect element between the host and the ordinary downstream
device cable. That is useful for debugging but consumes more channel loss and
discontinuity budget than a simple passive USB cable.

## Options

- **USB 2 only** — simplest and easiest to verify, but does not attempt the
  requested USB 3 capability.
- **Passive SuperSpeed switch** — low power and small, but only adds loss and
  cannot recover the added cable/connector attenuation.
- **Dual-channel 5 Gb/s redriver with shutdown** — combines the disconnect and
  signal-conditioning functions, at the cost of power, tuning straps and
  first-article setting validation.

## Decision

Use a sourceable dual-channel USB 3 Gen 1 redriver with hardware shutdown for
the SuperSpeed path and treat USB 3 as a first-article qualification target,
not a USB-IF compliance claim.

## Consequences

The schematic must expose deterministic equalization/de-emphasis settings,
the layout must use a named 90-ohm stackup and short, uninterrupted pairs, and
the release test plan must verify enumeration and sustained transfer at 5 Gb/s
with bounded cable lengths. USB 2 remains the accepted fallback.

