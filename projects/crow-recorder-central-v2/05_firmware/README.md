# 05_firmware/ — crow-recorder-central-v2

**This is not the board's firmware.** The XU316 application (USB Audio Class 2
async, TDM from two PCM1865, I2C, boot from QSPI flash) has not been written.
What lives here is the one piece of firmware behaviour that a HARDWARE defect
made binding, captured before anyone writes the rest and gets it wrong.

## What is here

| File | What |
|---|---|
| `cal_burst.c` | the calibration-burst DRIVE LEVEL: named constants, the full CAL-1 derivation, the trim ladder, and `cal_burst_on_ticks()` — pure logic, no MCU header |
| `Makefile` | host test harness. `MCU` is a variable, per this folder's contract |
| `contracts.md` | the folder contract |

## Build / test

```
make test          # compiles cal_burst.c with -DCAL_BURST_SELFTEST and runs it
make test MCU=...  # the MCU is a variable, never a constant
```

`make test` needs only a host C compiler and libm — no XMOS toolchain, no
silicon. It re-derives every constant in `cal_burst.c` from the physics and
fails if any of them drifts. Measured 2026-07-28: **PASS, 0 failures**; and
RED-verified — rebuilt with `CAL_BURST_DUTY_DEN` set back to the pre-fix `2`,
it reports **5 failures**, including `MARGIN vs the pod input ceiling` going
negative, and exits 1. A gate that cannot fail is worthless.

There is no flash step here yet. When the application is written: XU316 boots
from `U5` W25Q16JVSSIQ over QSPI; the programming/debug connector and its
pinout are in `01_docs/ARCHITECTURE.md` and `01_docs/DETAIL_DESIGN.md` (xSYS /
`J_DBG`) — referenced, not restated.

## THE BINDING CONSTRAINT — a two-board rule

**Central's beep drive is bounded ABOVE by the input ceiling of the preamp on
the sibling board, `crow-mic-pod-v2`. Raising it breaks the pod.**

| | dB SPL at the pod capsule MK1 |
|---|---|
| burst at 1/2 duty (the pre-fix level) | **106.8173** |
| pod OPA1678 worst-case linear input ceiling | **101.3144** |
| shortfall that must be given back HERE | **5.5028** |
| shipped level, duty 1/6 (−6.0206 dB) | **100.7967** — clears by 0.5178 dB |

Derivation, evidence and the model are in the header comment of
`cal_burst.c`; the defect is CAL-1 in
`projects/crow-mic-pod-v2/08_reviews/DISPOSITIONS.md`.

Why it can only be fixed here: measured from the SEALED v1.7 netlist,
`PLUS5V_BEEP` is the 5 V rail through a ferrite bead with **no series
resistor and no regulator**, `BEEP_RETURN` is **one AO3400A for all eight
ports**, and `BEEP_GATE` has exactly **two nodes** — `U1.122` and `R_bg1.1`.
There is no analog level control anywhere on this board. The GPIO waveform is
the only lever, so the level is a FIRMWARE constant by construction.

**Still open, and the user's call:** CAL-1's 5.50 dB is computed from LS1's
datasheet *minimum* output. A unit at the datasheet's own *typical* curve
(~104 dB @ 10 cm at 3.9 kHz) lands at 110.8173 dB and, even after −6.02 dB,
remains 3.48 dB over the ceiling. −6 dB is the authorized fix for the recorded
defect; it is not proven sufficient for a loud unit. **Trim against a
measurement at bring-up** using the ladder in `cal_burst.c`.

## Hardware-default behaviour (unprogrammed board)

**SILENT, and that is the fail-safe direction.** `BEEP_GATE` is driven only by
`U1.122`; with the XU316 unprogrammed or held in reset that pin is an input,
and `R_bg2` (100 kΩ, gate to GND) holds the AO3400A gate low. Q2 stays off,
`BEEP_RETURN` floats, and no transducer current flows on any of the eight
ports. Nothing else on the board is hardware-default-on in a way that matters
to this loop.

The dangerous default is the opposite one and it is a SOFTWARE risk, not a
hardware one: a naive first cut that toggles `BEEP_GATE` at 50 % duty —
the datasheet's characterisation condition, and the obvious thing to write —
puts 106.82 dB on the capsule and clips the preamp the burst exists to
calibrate. Use `cal_burst_on_ticks()`.
