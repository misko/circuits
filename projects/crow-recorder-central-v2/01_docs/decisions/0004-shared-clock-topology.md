---
id: 0004
date: 2026-07-23
status: accepted
---
# 0004 — Shared sample-clock topology (one clock for all channels)

## Context
Requirement: ONE physical sample clock for every channel (USB Audio Class 2
async; the recorder is the timing authority). Two PCM1865 ADCs must share
MCLK/BCLK/LRCK so all 8 channels sample coherently. The PCM1865 has a
CLOCK TRAP (ledger, audio-adc-8ch-tdm): SCKI (pin 15) is the 3.3V master-clock
input; XI (pin 10) is a crystal pin with abs-max **2.1V** — feeding the 3.3V
MCLK into XI over-stresses it.

## Options
- **Each ADC on its own crystal** — REJECTED: independent clocks = per-ADC
  drift = incoherent channels; violates the one-clock requirement.
- **MCLK into XI** — REJECTED (destroys the part): XI abs-max 2.1V < 3.3V MCLK.
- **XU316 MCLK -> NC7NZ34 buffer (1->2 fanout) -> each ADC SCKI, XI to GND,
  BCLK/LRCK shared with source-series 33R** — CHOSEN.

## Decision
- FA-238 24MHz crystal on the XU316; the xcore.ai PLL derives MCLK.
- XU316 MCLK_OUT -> NC7NZ34 clock buffer (all 3 inputs tied to MCLK, Y1/Y2 to
  the two ADCs) -> **33R source-series** on each buffered leg -> PCM1865 SCKI
  (pin 15) of U2 and U3.
- BCLK and LRCK driven by the XU316, **one 33R source-series each** at the
  driver, shared to both ADCs' BCK/LRCK.
- **Both PCM1865 XI (pin 10) TIED TO GND.**
- I2C address strap: U2 AD -> GND (0x4A), U3 AD -> 3V3 (0x4B); MD0 -> GND
  selects I2C control on both.

## Consequences
- NC7NZ34 (U4) + FA-238 (Y1) + 3x 33R (clock) + 2x 33R (buffered legs) on BOM.
- Clock legs kept SHORT and series-terminated (CLOCK netclass, 0.25mm).

## Invariants emitted (03_src/rules/electrical_invariants.yaml)
- `pin_on_net U2.10 GND` and `pin_on_net U3.10 GND` — XI tied to GND (the
  abs-max-2.1V safety invariant; THE defect this ADR exists to prevent).
- `pin_on_net U2.15 MCLK_A1`, `pin_on_net U3.15 MCLK_A2` — SCKI on the
  buffered master clock, not XI.
