---
id: 0001
date: 2026-07-27
status: accepted
tags: [topology, protection, safety]
---
# 0001 — Control polarity ON = loopback, and the power-on state MUST be ANTENNA

## Context

The verbatim commission says `GPIO = off` → antennas to Pluto, `GPIO = on` →
TX loopback. A follow-up answer during the commission CONTRADICTED that; the
user was asked and confirmed the verbatim reading (BRIEF A3, tension T2).

That settles the mapping. It does not settle the question that actually
matters, which nobody asked and which is a safety property rather than a
feature: **what is the RF path doing when nothing is driving the control
line?** That state exists on every board, at least four times per session —
during the supply ramp, during MCU reset, with USB unplugged, and on a board
straight from JLCPCB whose flash has never been programmed.

Landing in LOOPBACK there would connect the Pluto's TX chain to both of its
own RX inputs while the user believes they are receiving off-air. It is also
undetectable: the receiver still sees signal.

There is a second, independent reason this must be a hardware property. The
board's control net fans out to two `BGS12WN6` CTRL pins whose input current
is 2 nA typ / 10 nA max (Table 2, PDF p5). At that leakage an undriven CTRL
pin has NO defined state at all — it floats to wherever charge left it.

## Options

- **Rely on firmware to set the line low at boot.** REJECTED. It does not
  cover the pre-firmware window at all: supply ramp, reset, and a blank board
  from the assembler. A board that arrives unprogrammed would sit in an
  undefined RF state indefinitely.
- **A hardware pull-down only, MCU state unconstrained.** REJECTED as
  insufficient on its own — an MCU whose pins reset as DRIVEN OUTPUTS beats
  any pull-down. This is not hypothetical: `MCP2221A`'s factory flash defaults
  leave every GP pin a push-pull output with `GPIOOUTVAL = 1` in an alternate
  function that idles high (DS20005565E Registers 1-12…1-15 pp.12-15, Table
  1-5 p.19). A board built around it and delivered unprovisioned would DRIVE
  the RF path into loopback.
- **An MCU whose GPIO reset state is a documented pull-down, PLUS an external
  pull-down at each switch.** CHOSEN. Two independent mechanisms, one inside
  the MCU and one that works with the MCU absent or unpowered.
- **Invert the polarity so that "no drive" means loopback.** REJECTED — it
  inverts the safety property for no gain, and contradicts the fact-locked A3.

## Decision

**The control net is LOW = ANTENNA, HIGH = LOOPBACK, and the LOW state is
guaranteed by hardware in two independent ways:**

1. the MCU's GPIO reset state is a documented internal **pull-down** with no
   pull-up (for RP2040: `PADS_BANK0` resets `PDE=1 / PUE=0` — Table 341,
   §2.19.6.3, p.301; `GPIO_OE` resets to `0x00000000` so nothing is driven —
   Table 24, p.46; per-pin reset state stated as the single word `Pull-Down` —
   Table 615, §5.5.2.2, pp.612-613; RPD = 50–80 kΩ, Table 625, p.615);
2. a **10 kΩ external pull-down at each switch's CTRL pin**, which holds the
   state when IOVDD = 0 V and the MCU pin is genuinely floating.

The wiring makes this free of logic: `RF1 = RX_ANTn`, `RF2 = loopback arm`,
against a truth table of `CTRL=0 → RFIN–RF1`. **No inverter, no complementary
control line, no decode** — the safe state and the briefed polarity are the
same state.

`MCP2221A` is DISQUALIFIED by this ADR, not merely out-ranked.

## Consequences

- **Commits the MCU choice to a part whose GPIO reset state is DOCUMENTED as
  a pull-down or a high-impedance input.** Any future MCU substitution must
  re-verify that page. Named do-not-substitute: a "pin-compatible upgrade" to
  a pre-A4 RP2350 would destroy the argument — RP2350-E9 is precisely the
  erratum where the pad pull-down cannot hold a floating input below ~2.2 V.
- **Commits the switch choice to a part with the `CTRL=0 → RF1` truth table.**
  A switch with the opposite table, or with two complementary control lines
  (e.g. SKY13351-378LF), costs an inverter and re-opens this decision.
- Emits machine-checkable netlist invariants (`03_src/rules/electrical_
  invariants.yaml`, canon E-INV): the pull-down resistors exist, are on the
  right nets, and are BOUNDED IN VALUE — a pull-down that exists at the wrong
  value passes a topology assertion and disables the property it was fitted
  for (the `part_value` incident class).
- Firmware must not assume a known RF path until 3.3 V is valid plus the
  switch's power-up settle time. The datasheet specifies no behaviour at
  VDD = 0.
- A board with blank flash is SAFE (antenna mode) but not USABLE over USB.
  That is the correct failure direction and it makes `05_firmware/` a release
  deliverable, not an afterthought.
