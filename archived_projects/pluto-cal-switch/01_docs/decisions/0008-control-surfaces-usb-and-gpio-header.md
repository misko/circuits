---
id: 0008
date: 2026-07-27
status: accepted
tags: [topology, protection]
---
# 0008 — USB and GPIO header BOTH; the header is an ANALOG input

## Context

The verbatim commission asks for "a GPIO interface to switch" with LEVEL
semantics (`GPIO = off` / `GPIO = on`). A follow-up (A4) asked for the state to
be settable over USB. BRIEF D3 resolved that by giving both to one MCU rather
than trading one for the other.

That leaves two questions the brief does not answer, and one hard electrical
fact nobody checked.

**The fact, and it is fatal to the obvious build: PlutoPlus IO is 1.8 V, and
RP2040's `VIH` is a FLAT 2.0 V minimum** — not 0.65·IOVDD (DS Table 625,
§5.5.3.4, p.615). A Zynq HR bank at VCCO = 1.8 V has a worst-case VOH of
VCCO − 0.45 = **1.35 V**. The original ADALM-Pluto is worse: its AD9363 GPO
pins run from VDD_GPO = 1.3 V.

**A 1.8 V header wired to an RP2040 digital input reads permanently LOW.** The
board would silently stay in antenna mode forever — and because that failure is
*fail-safe*, it passes every bench test that asks "can it spuriously enter
loopback" and surfaces only as "the GPIO control doesn't work", plausibly after
seal. A series resistor into a pull-down, as the sourcing spike proposed, makes
it marginally worse (1.35 V → 1.32 V).

There is a **reverse hazard** too, unmentioned anywhere before now: RP2040 VOH
is 2.62–3.3 V, and a Zynq HR bank at VCCO = 1.8 V has an absolute-maximum IO of
≈VCCO + 0.55 = **2.35 V**. The reset state protects at power-on but not at
runtime — one firmware bug or one netlist error destroys the user's Pluto.

## Options

### Level compatibility

- **Direct GPIO connection.** REJECTED — does not work at all (above).
- **Fixed-direction level translator** (SN74LVC1T45, NLSV1T244), A-side 1.8 V /
  B-side 3.3 V. Correct, and gives hard unidirectional protection. REJECTED on
  cost of a **1.8 V rail** the board otherwise does not need — a second LDO or
  a dependency on the header carrying one.
- **BSS138 + 2 × 10 kΩ bidirectional shifter.** Cheapest. REJECTED:
  bidirectional means no protection for the Pluto, and its Vgs(th) of 0.8–1.5 V
  against a 1.35 V worst-case input is marginal.
- **Run IOVDD at 1.8 V.** REJECTED: collides with the crystal guidance and
  drops VOH to 1.24 V min, which must then clear the RF switch's V_Ctrl,H.
- **Read the header on an ADC-capable pin and threshold in firmware.** CHOSEN.

### Which surface wins

- **Header only** — violates A4.
- **USB only** — violates P2.
- **OR, plus a USB watchdog.** CHOSEN.

## Decision

### 1. The header lands on an ADC pin through a ÷2.5 divider

`HDR_CTRL_IN` → **3.3 kΩ series → GPIO28 (ADC2)**, with **2.2 kΩ to GND** and
an ESD clamp at the connector. Firmware thresholds at **0.36 V**.

> **CORRECTED 2026-07-30 — the two resistor values were TRANSPOSED in the
> as-authored netlist, and this table was the evidence.** Stage 4 shipped
> `R_HDR_S` = 2.2 kΩ and `R_HDR_G` = 3.3 kΩ, i.e. ratio **0.600**, while this
> ADR's prose said "2.2 kΩ series … 3.3 kΩ to GND" and the table below listed
> the voltages for **0.400**. The table was never an estimate — it is exactly
> what the two values produce when swapped, which is what identified the fault
> as a transposition rather than a rounding disagreement. **The netlist was
> corrected to match the table** (series 3.3 kΩ / shunt 2.2 kΩ), not the other
> way round, for three reasons: (a) the ratio the whole ADR argues for is
> ÷2.5; (b) the swap **tightens** the fault-current bound below (0.303 mA
> instead of 0.45 mA); (c) at 0.600 the ADC ceiling collapses — see the
> headroom column. **BOM-neutral**: `C25879` (2.2 k) and `C137992` (3.3 k) are
> each used exactly once and only here, so the swap changes no line item.
> Now machine-checked three ways — `series_chain` pins which leg is which,
> `part_value equals` pins each leg's value, `net_has_part` pins existence —
> because the single pre-existing assert (`R_HDR_S min: 1k`) was satisfied by
> the wrong value.

| header logic | voltage at the pin | vs 0.36 V threshold | headroom to 3.3 V FS |
|---|---|---|---|
| 0 V / unconnected | 0.00 V | LOW | — |
| 1.8 V (PlutoPlus) | 0.72 V | HIGH, 2× margin | 2.58 V |
| 3.3 V | 1.32 V | HIGH | 1.98 V |
| 5.0 V (silk-stated ceiling) | 2.00 V | HIGH, inside the 0–3.3 V ADC range | **1.30 V** |
| 5.5 V (USB-legal worst case) | 2.20 V | HIGH | 1.10 V |

For contrast, the transposed 0.600 ratio that was actually built: 1.080 /
1.980 / **3.000** / 3.300 V. The 0.36 V detect threshold clears with *better*
margin at 0.600 — which is why no functional test would have found it — but
the 5.0 V case leaves **0.30 V** of headroom against a 3.3 V full scale
(≈0.23 V against a −2 % `ADC_AVDD` of 3.234 V), and the 5.5 V case reaches
**3.300 V, at or above AVDD**, forward-biasing the input ESD diode. The
failure mode of this divider is the CEILING, not the threshold.

Four properties, all of which the alternatives buy only partially:

- **Reads 1.8 V, 3.3 V AND 5.0 V logic** with no translator, no second rail
  and no assumption about what the user connects.
- **INPUT-ONLY BY CONSTRUCTION.** An ADC-configured pin has its digital output
  disabled, so no firmware bug can drive 3.3 V into a 2.35 V-max Zynq pin. The
  3.3 kΩ series bounds any such fault to **0.303 mA** regardless, inside any
  IO clamp. (Was stated as 0.45 mA for a 2.2 kΩ series — see the 2026-07-30
  transposition note above; the corrected value is the *tighter* bound.)
- **An unconnected header reads 0 V = antenna mode** — the 2.2 kΩ shunt is the
  pull-down.
- Loads a 1.8 V driver with only 1.8 V / 5.5 kΩ = **0.33 mA**.

A 12-bit LSB is 0.81 mV, so the threshold is not resolution-limited. Polling at
~1 kHz is ample for a manual mode switch.

### 2. `RF_CTRL = HEADER_level OR USB_bit`, with a 10 s USB watchdog

The verbatim brief states the header's semantics as a LEVEL, so a header held
HIGH must produce loopback whatever USB says or P2 is violated; and a header
held LOW must not block USB control or A4 is violated. **OR is the only
resolution that satisfies both.**

The real objection to an OR is that the header can only ever FORCE loopback,
never recover the board to the safe state if a host commands loopback and then
hangs. **The watchdog answers it**: if the USB bit is set and the host stops
talking for **>10 s**, firmware clears it. The header therefore regains full
authority within 10 s of any host failure, and the safe state is always
reachable without unplugging.

### 3. The header is 1×4: `GND / CTRL_IN / STATE_OUT / GND`

`STATE_OUT` is an emulated open-drain (firmware drives the pin low or leaves it
a hi-Z input) through a 1 kΩ series, so it cannot exceed whatever rail the user
pulls it up to and cannot damage a 1.8 V device. It reports the RESOLVED RF
state, which is the same philosophy as brief D4: publish the number rather than
let the user infer it.

**`STATE_OUT` is an ADDITION, not a requirement** — the brief asks only for an
input. It costs one pin and one resistor. Recorded so it is not mistaken for
something the user asked for.

## Consequences

- **THE USER HAS NOT BEEN ASKED WHICH SURFACE WINS. Recorded as D7 and flagged
  in the report.** If they want the header to be authoritative in BOTH
  directions (i.e. header LOW forces antenna even against a USB command), that
  is a firmware one-liner and no hardware change.
- **Adds a BRIEF fact-lock row: GPIO header logic level.** The divider makes
  the board level-agnostic across 1.8–5.0 V, so the row is satisfied by design
  rather than by an assumption about the user's wiring — but the ceiling is
  5.0 V and must be stated on the silk.
- **`RF_CTRL` must be on an ADC-capable pin (GPIO26–29)** and NOT on GPIO15
  (RP2040-E5), GPIO0/1 (debug UART) or QSPI_SS (BOOTSEL). Constrains the
  pin-out before schematic.
- **The header is the board's SECOND, UNKEYED power/signal entry** and the
  realistic miswire path. It carries series resistance and an ESD clamp
  (ADR-0009), and **3V3 is deliberately NOT exported on it** — a back-feed
  must not be able to fight the LDO.
- **Firmware obligations, all now specified**: ADC threshold at 0.36 V; the OR;
  the 10 s watchdog; report the resolved state over CDC; and do not assume a
  known RF path until 3.3 V is valid plus the switch's power-up settle.
- **The control net becomes a two-branch stub through the RF section**, since
  the two switches are mirrored about the splitter. Handled by 1 kΩ series +
  1 nF shunt at each CTRL pin, low drive strength, an inner layer under ground,
  and a routing rule that it never runs parallel to a loopback arm
  (ARCHITECTURE §10.6). A fast-edge digital net coupling into the calibration
  path would corrupt the very measurement this board exists to make.
- **The board cannot be commanded from the header with USB unplugged**, because
  the board is USB-powered. If the user wants header-only operation the header
  must also carry 5 V in — **flagged to the user as an open question, not
  designed in.**
