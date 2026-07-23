---
id: 0005
date: 2026-07-23
status: accepted
---
# 0005 — Power sequencing (XMOS reference)

## Context
The XU316 xcore.ai has multiple supply domains: VDD core 0.9V, VDDIO banks
3.3V, VDDIOB18 + USB_VDD18 1.8V. The named XMOS multichannel-audio reference
design sequences core after IO and never leaves the 1.8V IO bank last. The
AP61102 buck can gate a dependent rail via its PG output (ledger, buck-1a5).

## Options
- **All rails enabled together** — REJECTED: violates the XMOS reference; core
  before IO can latch or draw excess.
- **PG-sequenced: 3V3 first, PG enables 0V9 core, 1V8 off 3V3** — CHOSEN.

## Decision
- U7 (AP61102, 5V->3V3) comes up first (EN tied high through the input).
- U8 (AP61102, 5V->0V9 core) EN driven by U7's **PG (power-good)** — core comes
  up only after the 3V3 IO rail is valid.
- U9 (TCR2LF18, 3V3->1V8) is fed from 3V3, so it rises right after 3V3 — the
  1.8V IO bank is never the last rail up.
- U10 (XC6227, 5V->3V3A analog) is independent; AVDD isolation is by its own
  LDO + local bulk/HF decoupling, joined to digital only at GND.
- AP61102 EN doubles as MODE: to get FORCED-PWM (lower ripple, the mixed-signal
  choice) drive EN < VIN-200mV from logic rather than tying EN to VIN (PFM).
  This board ties EN to the sequencing logic; the 3V3 buck uses forced-PWM for
  cleaner rails feeding the analog LDO input.

## Consequences
- U7 PG -> U8 EN net (PG_3V3).
- Firmware/hardware bring-up order documented for first power.
- No electrical invariant emitted here beyond the PG wiring net (topology, not
  protection); ADR-0001 carries the protection invariants.
