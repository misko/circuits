---
id: 0005
date: 2026-07-28
status: accepted
tags: [topology, protection, timing]
---
# 0005 — Parallel 3-bit control, pulled-down defaults, LS hard-grounded, source-terminated

## Context

BRIEF A4 fact-locks a free-running RP2040 PIO sequencer driving **parallel
3-bit** select, and records "**NEVER SPI**" as DERIVED. D1 closes the frame at
8192/4096 clean samples with a **128-sample blanking allowance per hop** —
`128 / 30 Msps = 4.267 µs`, and every microsecond of it is already spoken for.
This ADR fixes the electrical detail that BRIEF A4 left open: what drives
what, what value, what happens before firmware runs, and what the switch's
input pins are protected from.

Three device facts govern (`02_parts/PE42482A-X/part.yaml`):

- **`V1`–`V4` have NO internal pull of any kind** — 5 µA max input current
  and nothing else (Table 2, PDF p3). All four FLOAT before firmware runs.
- **`LS` has a 1 MΩ internal pull-UP** (Table 5 fn 1, PDF p10), and is
  additionally an **RF ground** whose quality moves insertion loss and
  isolation (Table 3 fn 1, PDF p9).
- **Digital absolute maximum is 3.6 V while VDD absolute maximum is 5.5 V**
  (Table 1, PDF p2). On a 3.3 V rail that is **300 mV** of headroom.

## Options

### Control interface

- **SPI / I²C.** REJECTED, and the sharp reason is not latency but
  **DETERMINISM**. A 3-byte SPI transaction at 10 MHz is 2.4 µs of bit time
  before any firmware overhead — 56 % of the 4.267 µs allowance — and its
  START is scheduled by software, so the hop boundary jitters. **P4's whole
  premise is that the X/2 dwell is a measurable timing marker**; a jittering
  hop boundary smears the marker the frame is synchronised on. A free-running
  PIO writing three pins costs **one PIO clock (~8 ns at 125 MHz), with zero
  jitter by construction**.
- **A 3-to-8 decoder + one-hot lines.** REJECTED: PE42482A-X's truth table is
  already a straight 3-bit binary mux (Table 5, PDF p10). A decoder adds a
  part, a propagation delay and a glitch window to re-create what the die
  does internally.
- **Parallel 3-bit direct from PIO.** CHOSEN.

### V4 (the all-ports-terminated line)

- **Hard-tie V4 to GND.** REJECTED — it forfeits a capability for nothing.
- **Drive V4 from a 4th GPIO, with a pull-down.** CHOSEN. `V4 = 1` with
  `V1..V3 = 0` selects the **ALL-PORTS-TERMINATED** state (Table 5 last row,
  PDF p10). That state is a **DARK FRAME**: RFC sees only the switch's own
  leakage and the coupling between the ten SMA barrels on this laminate. It
  is the instrument for the two measurements this design owes and cannot
  otherwise make — the leakage coefficients that ADR-0002's T3 subtraction
  needs, and the port-to-port SMA isolation floor that `02_parts/README.md`
  records as OWED. **One GPIO and one resistor buy the board the ability to
  measure its own noise floor.**

### Pull-down value

| R | offset from 5 µA leakage | margin to `V_IL` = 0.6 V | current when driven high | verdict |
|---|---|---|---|---|
| 1 kΩ | 5 mV | 99 % | 3.3 mA × 4 = 13.2 mA | rejected — 13 mA to solve a 5 µA problem |
| **10 kΩ** | **50 mV** | **92 %** | **0.33 mA × 4 = 1.3 mA** | **CHOSEN** |
| 100 kΩ | 500 mV | **17 %** | 33 µA × 4 | rejected — 100 mV from reading as a logic 1 |

### Series termination

- **Direct connection.** REJECTED by arithmetic. An unterminated CMOS edge
  reflects with Γ ≈ +1 at the switch's 5 µA input and doubles. The CTRL trace
  is **67 Ω** on this stackup at 0.20 mm (DETAIL_DESIGN §4). An RP2040 pad's
  output impedance is a FIRMWARE-SELECTED quantity — **ESTIMATED at 25 ± 10 Ω
  at the 12 mA setting**, rising to a few hundred ohms at 2 mA (M-IMPORT:
  estimated, not read from a document this project holds). At 25 Ω the
  far-end peak is `2 · 3.3 · 67/(67+25)` = **4.81 V — 1.21 V above the 3.6 V
  absolute maximum**, on every hop, 480 times a second.
- **`1 kΩ + 1 nF` RC at each switch pin** (the shape a sibling board uses on
  a control net that is static). **REJECTED by arithmetic:** τ = 1 µs, so
  4.6 µs to 99 % — **more than the entire 4.267 µs blanking allowance**. It
  would convert a 290 ns switch into a 5 µs one.
- **"Set the drive strength to 2 mA and rely on that."** REJECTED as the
  PRIMARY mechanism: drive strength is a register. A firmware change, an SDK
  default or a porting mistake would then violate a device absolute maximum,
  and nothing on the board would object. **Protection that lives in a
  register is not protection.**
- **A series resistor at the SOURCE, no shunt C, sized against the STRONGEST
  drive setting.** CHOSEN. The requirement is `Z_drv + R_S ≥ Z_line`, so
  `R_S ≥ 67 − 25 = 42 Ω` ⇒ **47 Ω** (E24, JLC Basic). Then:

  | Z_drv | source Z | far-end peak | verdict |
  |---|---|---|---|
  | 25 Ω (12 mA, nominal estimate) | 72 Ω | **3.18 V** | below the RAIL |
  | 15 Ω (the pessimistic end of the bar) | 62 Ω | **3.43 V** | still inside the 3.6 V abs max |
  | 250 Ω (2 mA) | 297 Ω | 1.36 V | no overshoot |

  **The absolute-maximum bound therefore holds at every drive setting, in
  copper.** Its own time constant against ~15 pF of trace + pin is **0.7 ns**,
  i.e. 0.016 % of the budget.

### LS

- **A trace to a distant GND, or a 0 Ω link.** REJECTED: Table 3 fn 1 makes
  LS an RF ground, and a stub is not one.
- **A via to the ground plane AT the pad.** CHOSEN.

## Decision

```
RP2040 PIO ──[R_S1 47Ω]── SW_V1 ── U_SW.9   (V1, MSB)   ── R_PD1 10k ── GND
           ──[R_S2 47Ω]── SW_V2 ── U_SW.10  (V2)        ── R_PD2 10k ── GND
           ──[R_S3 47Ω]── SW_V3 ── U_SW.11  (V3, LSB)   ── R_PD3 10k ── GND
           ──[R_S4 47Ω]── SW_V4 ── U_SW.12  (V4, dark)  ── R_PD4 10k ── GND
                                   U_SW.1   (LS) ── via at the pad ── GND plane
```

DC check on the divider: `V_OH` at the switch is `3.3 · 10k/(10k+47)` =
**3.28 V** against `V_IH` 1.17 V min; `V_OL` from 5 µA of leakage through
10.047 kΩ is **50 mV** against `V_IL` 0.6 V max.

Series resistors at the **MCU** end; pull-downs at the **switch** end (the
part's own `layout:` block budgets `SW_V4` at ≤4 mm because a floating V4 is
the failure that mutes the receiver silently).

**Selection map, from Table 5 (PDF p10): with `LS = 0` and `V4 = 0`, `RF_n`
is selected where `n − 1 = 4·V1 + 2·V2 + 1·V3`.** V1 is the MSB, V3 the LSB.
Getting V1 and V3 backwards silently reverses the sweep order, and an AoA
solver absorbs a reversed sweep as a rotated array — **nothing on the board
can detect it**, which is why the pin-to-net assignment is emitted as
invariants rather than trusted.

**POWER-ON DEFAULT = `RF1`.** All four lines are pulled low, so before
firmware runs the board selects antenna 1 — a real antenna, not the mute
state and not an undefined one. **The design deliberately does not rely on
the RP2040's own pad-reset state**: that is a datasheet fact this project has
not verified and a silicon revision could change, whereas four resistors make
the power-on antenna a property of the BOARD.

**Firmware obligations, recorded here as DESIGN INPUTS** (the same standing as
the BRIEF's MGC / RX-FIR / frozen-DC-tracking inputs — the arithmetic below is
false without them):

1. **RP2040 pad drive strength = 2 mA and slew rate = slow** on all four
   select lines. This is GOOD PRACTICE (lower EMI into a board that is 270°
   of RF fan) and is deliberately **NOT load-bearing**: the 47 Ω series
   value already holds the absolute-maximum bound at the strongest setting,
   so a firmware regression degrades emissions rather than exceeding a
   device rating.
2. The sequencer writes all three (or four) bits in ONE PIO instruction. A
   read-modify-write across two instructions creates a transient code and
   therefore a transient antenna.

### The blanking budget, itemised

| term | FIR bypassed | 128-tap FIR |
|---|---|---|
| PIO write → pin (parallel) | 8 ns | 8 ns |
| PE42482A-X settle to 0.05 dB, **max** (Table 3, PDF p9) | 1400 ns | 1400 ns |
| AD9363 analog baseband settle | ~75 ns | ~75 ns |
| AD9363 RX digital chain group delay | ~700 ns | ~4900 ns |
| **total** | **2183 ns** | **6383 ns** |
| **against the 128-sample allowance** | **4267 ns — 1.95× margin** | **4267 ns — FAILS by 1.5×** |

**That row is why "RX FIR bypassed or short" is a design input and not a
preference**, and it is the number that must be re-checked if the dwell
structure ever changes.

## Consequences

- **Six invariant families cite this ADR**: `LS` on GND, each `SW_Vn` on its
  switch pin, a pull-down resistor present on each `SW_Vn`, the
  `SEL_Vn → R_Sn → SW_Vn` series chains, and `part_value` on the 10 kΩ and
  47 Ω sets. The V1-MSB/V3-LSB mapping is unobservable electrically; making
  it executable is the whole point of E-INV.
- **`LS` is on the GND net, so it is not a distinct net**, and P-ADJ skips a
  `keep_short` budget whose net has fewer than two pads. **The
  `SW_LS ≤ 2 mm` budget in `02_parts/PE42482A-X/part.yaml` is therefore
  graded by NOTHING**, silently. It is discharged geometrically instead —
  the ground via centre within **0.5 mm** of the LS pad centre — and that is
  a `CHECKLIST.md` line measured at placement. (The gate gap itself is
  reported upstream: a `keep_short` net that reaches fewer than 2 pads should
  be reported UNREACHED, the way P-FACT reports an unreached assertion, not
  skipped.)
- **The dark state is now a documented capability**, so the firmware and the
  host tooling owe it a mode. Without one, the leakage-subtraction path that
  ADR-0002 leans on has no calibration source.
- **`R_S*` and `R_PD*` are eight 0402s in the digital corner**, all on the
  pins-7..12 side where ADR-0007 puts the escape corridor. They do not enter
  the RF fan.
- **If the MCU is ever swapped**, items 1–3 above must be re-derived against
  the new pad model; the 47 Ω is not a universal constant, it is the value
  that makes *this* pad's source impedance ≥ *this* trace's impedance.
