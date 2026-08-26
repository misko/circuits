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

## Amendment 2026-07-23 (red-team P1#1 — U7 EN/mode contradiction)
The original text claimed "the 3V3 buck uses forced-PWM for cleaner rails
feeding the analog LDO input" while ALSO tying U7 EN "high through the input"
(EN=VIN). Per the AP61102 datasheet (02_parts gotchas), EN > VIN-200mV selects
PFM — the wiring contradicts the forced-PWM claim. The rationale was ALSO
factually wrong: the analog LDO U10's input is 5V (this ADR's own U10 line),
not 3V3 — U7's mode does not touch the analog supply path.

CORRECTED POSITION (no netlist change): U7 (3V3 digital) EN stays tied to VIN
=> PFM at light load, ACCEPTED because (a) 3V3 feeds DIGITAL loads only
(XU316 IO, PCM1865 DVDD/IOVDD, ~0.5-0.6A typical — the buck sits at/near its
PFM/PWM crossover under real load anyway); (b) the analog chain (AVDD=3V3A) is
5V -> U10 LDO, independent of U7's mode; (c) U8 (0V9 core) is genuinely in
forced-PWM (EN = PG_3V3 = 3.3V < VIN-200mV), which the datasheet gotcha
documents as the intended sequencing+mode double-duty. If bench bring-up shows
3V3 PFM ripple coupling into the ADC (not expected via the LDO path), the
v-next fix is a 2-resistor EN divider (5V -> ~2.5V) putting U7 in forced-PWM.
