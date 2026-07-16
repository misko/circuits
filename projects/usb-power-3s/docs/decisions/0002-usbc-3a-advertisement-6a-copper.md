---
id: 0002
date: 2026-07-16
status: accepted
---
# 0002 — USB-C: advertise 3 A via Rp, build copper for 6 A, no PD

## Context
Requirement: USB-C output, 6 A max. USB-C without PD may advertise at most
3.0 A (Rp = 10 kΩ to 5 V); 5 A+ legally requires a PD controller and
e-marked cables.

## Options
- **PD controller (5 A contract)** — spec-correct. REJECTED: adds an
  unverified IC + firmware-ish config to an otherwise MCU-free board, still
  caps at 5 A, and the known target loads (Pi-5-class, dumb 5 V devices)
  don't require a PD contract to draw.
- **Rp = 10 k (3 A advertisement) + 6 A-rated path** — spec-compliant
  advertisement; loads that follow USB-C draw ≤3 A and are safe; known
  high-draw loads that exceed advertisement get honest copper and a
  ~6.3 A wc-min buck OCP behind them.
- **Advertise nothing (pure dumb 5 V)** — REJECTED: C-to-C cables/devices
  read CC; without Rp many sinks refuse to draw at all.

## Decision
Rp 10 kΩ on CC1 and CC2, path and regulator sized for 6 A, buck-A OCP as
the port protection.

## Consequences
Compliant devices self-limit to 3 A — the "6 A" is only reachable by loads
that ignore advertisement (documented, intended). No PD, no 9/12/20 V.
If a future revision needs a real 5 A contract, that is a PD-controller
respin, not a tweak.
