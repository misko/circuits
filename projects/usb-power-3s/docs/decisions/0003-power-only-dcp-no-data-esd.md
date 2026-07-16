---
id: 0003
date: 2026-07-16
status: accepted
---
# 0003 — Power-only ports: DCP strap D+/D−, omit data ESD arrays

## Context
No host upstream — these ports source power only. Legacy BC1.2 devices
limit themselves to 500 mA unless the port identifies as a charger.

## Options
- **Float D+/D−** — REJECTED: BC1.2 devices stay at 500 mA; port looks broken.
- **DCP: short D+ to D− (≤200 Ω)** — one trace per port; devices detect a
  Dedicated Charging Port and draw their max.
- **CDP/SDP emulation** — needs a data connection or an emulator IC; no host
  exists. REJECTED.

## Decision
Short D+/D− with copper on each USB-A port and on both D-pairs of the
USB-C (A6–A7, B6–B7).

## Consequences
No USBLC6 ESD arrays: no data nets leave the board; the shorted stubs are
millimeters long behind the shell, and VBUS is clamped by the rail TVS
(SMBJ5.0A). If a future revision passes data, ESD arrays and this ADR must
both be revisited.
