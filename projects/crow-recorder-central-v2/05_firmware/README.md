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
RED-verified against the **current** acceptance criterion — rebuilt with
`CAL_BURST_DUTY_DEN` set to the pre-fix `2` **and** to the superseded `6`, it
reports **6 failures each and exits 1** both times, with
`TYPICAL-unit margin, NOMINAL` going negative (−9.50 dB and −3.48 dB). Both
old values are also checked INLINE as always-run known-bad fixtures, so the
gate proves it can fail on every single run, not only when someone recompiles.

There is no flash step here yet. When the application is written: XU316 boots
from `U5` W25Q16JVSSIQ over QSPI; the programming/debug connector and its
pinout are in `01_docs/ARCHITECTURE.md` and `01_docs/DETAIL_DESIGN.md` (xSYS /
`J_DBG`) — referenced, not restated.

## THE BINDING CONSTRAINT — a two-board rule

**Central's beep drive is bounded ABOVE by the input ceiling of the preamp on
the sibling board, `crow-mic-pod-v2`. Raising it breaks the pod.**

The acceptance criterion **changed on 2026-07-28** (user decision): it is no
longer "clears a minimum-spec LS1" but **"clears a unit on the datasheet's
TYPICAL curve"** — the right end of the tolerance for a clipping problem,
since the unit that clips is a loud one.

| | dB SPL at the pod capsule MK1 |
|---|---|
| burst at 1/2 duty, minimum-spec LS1 (pre-fix) | **106.8173** |
| burst at 1/2 duty, **TYPICAL-curve** LS1 | **110.8173** |
| pod OPA1678 worst-case linear input ceiling | **101.3144** |
| **shortfall that must be given back HERE** | **9.5028** |
| shipped level, duty **1/12** (−11.7401 dB nominal) | **99.0772** — clears by **+2.2372 dB** |
| same duty, minimum-spec LS1 | **95.0772** — clears by +6.2372 dB |

Derivation, evidence and the model are in the header comment of
`cal_burst.c`; the defect is CAL-1 in
`projects/crow-mic-pod-v2/08_reviews/DISPOSITIONS.md`.

**`sin(πD)` is NOT a conservative bound at this duty.** It was at 1/6; it is
not at 1/12, and the old conclusion is not carried forward. Two measured
mechanisms push the delivered attenuation the wrong way — an L-R regime change
at the 3 mH corner (+0.835 dB) and, dominantly, a **gate-RC duty bias** that
stretches the conduction window by +1.1…+6.5 µs (turn-off must fall from
3.26 V *down* to Vgs(th) while turn-on only climbs *up* to it). Combined worst
case: **−8.71 dB, not −11.74 dB — slack +3.03 dB.** Under that model the
typical unit **misses by 0.79 dB**. See "Still open" below.

Why it can only be fixed here: measured from the SEALED v1.7 netlist,
`PLUS5V_BEEP` is the 5 V rail through a ferrite bead with **no series
resistor and no regulator**, `BEEP_RETURN` is **one AO3400A for all eight
ports**, and `BEEP_GATE` has exactly **two nodes** — `U1.122` and `R_bg1.1`.
There is no analog level control anywhere on this board. The GPIO waveform is
the only lever, so the level is a FIRMWARE constant by construction.

**Still open, and the user's call.** Duty 1/12 meets the criterion
**nominally** (+2.24 dB) and **misses it under the worst-case model**
(−0.79 dB). The open-loop uncertainty on this hardware is **~3 dB — larger
than the 2.24 dB criterion itself**, so the level *cannot* be set open-loop to
the accuracy the criterion demands. Two ways forward, both cheap:

- **Trim against a measurement** at bring-up (the intended path). Raise
  `CAL_BURST_DUTY_DEN` until the measured capsule level is ≤ 101.3 dB SPL.
  Scoping `BEEP_RETURN` at `TP11` reads the gate-RC stretch directly and
  collapses most of the 3 dB on its own.
- **Or take the worst case open-loop:** `DEN = 14` is the first value that
  clears the typical unit under the worst-case model (+0.11 dB); `16` gives
  +0.93 dB, `20` gives +2.41 dB. One-line change, ladder in `cal_burst.c`.

The trim floor moved `16 → 24` for exactly this reason — the old floor would
have forbidden 1/14…1/20, the values that fix the worst case.

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
