> Adopted 2026-07-21 into crow-recorder-central from archived_projects/crow-array-central (provenance ADR 0011; re-verified by this project's own gates before any release). Original text follows.

# ADR-0006 — "shared reset/config" implemented as shared-rail POR + I2C

Status: accepted 2026-07-18

## Context

The brief (§5) says "Distribute MCLK, BCLK, LRCK, **reset** and
configuration timing to both PCM1865 devices". The PCM1865 has **no
reset pin** (part.yaml gotcha, SLAS831D Pin Functions p.11): it is
power-on-reset only; soft reset = I2C write 0xFE -> page-0 reg 0x00.

## Decision

The brief's intent (both ADCs leave reset and get configured with
identical timing so inter-chip latency is fixed) is implemented as:

- Both PCM1865 AVDD pins on the SAME XC6227 3V3A output, both DVDD/IOVDD
  on the SAME 3V3 rail — shared POR by construction.
- Both on one I2C bus (U2 MS/AD strapped LOW = 0x4A, U3 strapped HIGH =
  0x4B); firmware issues the soft-reset + config sequence back-to-back,
  then the XU316 starts BCLK/LRCK for both simultaneously — the ADCs
  align on the shared frame clock (their DOUT timing is slaved to
  BCLK/LRCK, which is the actual skew authority).
- SCKI (3.3V MCLK input) used on both, fed from the same NC7NZ34 buffer;
  **XI tied to GND, XO no-connect** (XI is a 1.8V-max input — the 3.3V
  MCLK would violate its 2.1V abs max; SLAS831D).
- Residual fixed inter-chip offset (if any) is exactly what the
  same-signal injection header (J10) measures — the brief's own
  verification hook (§5A / §9 "Two ADC devices" risk row).

## Consequence

No reset net exists on the board; the schematic carries the I2C bus +
address straps instead. MICBIAS pins unused (pods bias locally) — NC
flagged; GPIO1-3 and GPIO0/MISO get 100k pulldowns (no floating CMOS
inputs; register-default functions untouched).
