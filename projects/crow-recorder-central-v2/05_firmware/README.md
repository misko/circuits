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
RED-verified against the **current** acceptance criterion — rebuilt at each of
the three superseded duties, it **exits 1 every time**, failing on the fatal
`TYPICAL-unit margin, WORST CASE` assertion: `DEN=2` → −10.2236 dB, `DEN=6` →
−5.3586 dB, `DEN=12` → −0.7897 dB. All three are *also* checked INLINE as
always-run known-bad fixtures, so the gate proves it can fail on every single
run, not only when someone recompiles.

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
| shipped level, duty **1/20** (−16.1134 dB nominal) | **94.7039** — clears by +6.6105 dB |
| same, **under the WORST-CASE model** (−11.9165 dB) | **98.9008** — clears by **+2.4136 dB** |
| minimum-spec LS1, worst case | 94.9008 — clears by +6.4136 dB |

Derivation, evidence and the model are in the header comment of
`cal_burst.c`; the defect is CAL-1 in
`projects/crow-mic-pod-v2/08_reviews/DISPOSITIONS.md`.

**`sin(πD)` is NOT a conservative bound here**, and it is re-verified from
scratch at every retune rather than extrapolated — the L-R term is *not
monotonic in duty* (conservative at 1/6, non-conservative at 1/12,
conservative again at 1/20), and extrapolating it is exactly the mistake the
1/6 → 1/12 carry-forward made.

At 1/20 the dominant term is the **gate-RC duty bias**: turn-off must fall from
the 3.069 V gate peak *down* to `Vgs(th)` while turn-on only climbs *up* to it,
so the conduction window is stretched by **+6.19 µs = 49 % of the 12.50 µs
commanded pulse**. Combined worst case **−11.9165 dB, not −16.1134 dB — slack
+4.197 dB**. The criterion is nevertheless met **under the worst-case model**
(+2.4136 dB), which is why the self-test's fatal assertion is the worst-case
form and why duties 1/2, 1/6 **and 1/12** all fail it.

**Why 1/20 and not 1/14** (the least value that clears): the risk is
asymmetric. Clipping destroys the timing reference outright; a low level only
costs SNR, and the local path still sits ~77 dB above the mic's self-noise.
With the open-loop uncertainty (+4.20 dB) still larger than the criterion,
1/14's +0.11 dB is a rounding error against a model that has already moved
3 dB once.

Why it can only be fixed here: measured from the SEALED v1.7 netlist,
`PLUS5V_BEEP` is the 5 V rail through a ferrite bead with **no series
resistor and no regulator**, `BEEP_RETURN` is **one AO3400A for all eight
ports**, and `BEEP_GATE` has exactly **two nodes** — `U1.122` and `R_bg1.1`.
There is no analog level control anywhere on this board. The GPIO waveform is
the only lever, so the level is a FIRMWARE constant by construction.

## Bring-up: the TP11 measurement is NORMATIVE

The margin is met under the worst-case model, so nothing is *open* about the
level. What is open is the **model**: nearly half the conduction window at this
duty is gate-RC artefact and **it has never been measured on hardware.**

**Do the TP11 stretch measurement once per board build.** Full procedure —
scope CH1 on `U1.122` (commanded pulse) against CH2 on `TP11`/`BEEP_RETURN`
(actual conduction window), subtract, record — is written up as a normative
bring-up step in **`01_docs/CHECKLIST.md`**, and repeated in the header of
`cal_burst.c`.

**What it licenses:** once the stretch is known for real parts, the
`Vgs(th)` 0.65–1.45 V sweep collapses to a single number, the **+4.20 dB
open-loop uncertainty collapses with it, and the duty may be tightened back
toward 1/14–1/16 WITH EVIDENCE** — recovering ~2–4 dB of burst level and
far-pod SNR. Until then **1/20 stands**; the extra margin is the price of not
knowing. **Do not tighten the duty on the strength of the model alone.**

The trim floor is `36`, re-derived at 1/20 and bound by the one hard physical
limit: the gate must still reach the AO3400A's 2.5 V Rdson spec point inside
the commanded pulse, which fails at den ≈ 37.5. (An earlier revision set it at
24 on a "the worst case saturates" argument that measurement **retracted** —
over 1/20 → 1/40 nominal gains 5.99 dB and worst case gains 5.24 dB, tracking
within ~0.75 dB per doubling.)

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
