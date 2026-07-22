# ADR-0004 — Per-port current limiting (TPS2557) + power-only, no data ESD

Status: accepted (2026-07-20)

## Context

The three USB-A ports must each be limited to 2.5 A (P2), independently, so that a
short or over-draw on one port does not collapse the shared 5V_A rail or the other two
ports. No data passes through the board (it is a power/charging hub).

## Decision

- **One TPS2557 current-limit power switch per USB-A port** (U4/U5/U6), fixed-mode,
  ILIM set by RILIM = 24.3 kΩ → IOS ≈ 2.51 A. The TPS2557 adds, per port: adjustable
  current limit, thermal shutdown, reverse-current blocking, and controlled slew
  in-rush. A soft-shorted device on one port trips only that port.
- **Open-drain FAULT (pad 8) left floating** — there is no MCU to read it, and the
  protection is autonomous (auto-retry). A pull-up + LED per port was considered and
  rejected as board-area/cost not justified for a headless power hub (the rail power
  LEDs already indicate the board is live).
- **BC1.2 DCP strapping**: each port shorts D+ to D− through direct copper so attached
  devices detect a Dedicated Charging Port and draw to their own maximum.
- **No USB data ESD arrays.** Because no data leaves the board (D+/D− go only to the
  local DCP short) and VBUS is clamped by the rail TVS (D2/D3), a dedicated USB ESD
  array on the data lines protects nothing that is exposed to a data link. This is a
  deliberate, documented omission (contrast: a data-carrying port MUST have ESD).

## Consequences

- Three-way port isolation with autonomous fault recovery, no firmware.
- The USB-A bank's aggregate (3 × 2.51 A ≈ 7.5 A) sets Buck B's rating and ILIM.
- If a future variant carries USB data, ESD arrays on the data pairs become mandatory —
  noted so the omission is not silently inherited.
