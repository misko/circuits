# ADR-0003 — USB-C: advertise 3 A (dual Rp), size copper + regulator for 6 A

Status: accepted (2026-07-20)

## Context

P3 asks for a USB-C port at 6 A max. USB Type-C advertises source current to the sink
via the CC pull-up (Rp) resistor value: Rp to 5 V through 56 kΩ = default USB, 22 kΩ =
1.5 A, 10 kΩ = 3.0 A. There is **no CC resistor value that advertises 6 A** — anything
above 3 A requires a USB Power Delivery (PD) contract negotiated by a BMC/PD controller.

## Decision

- **Advertise 3.0 A** via **dual 10 kΩ Rp** (R19 on CC1, R20 on CC2 — one per CC line so
  the port works in both plug orientations), the maximum a non-PD fixed-5 V source may
  legally advertise.
- **Size the copper and regulator (Buck A) for the full 6 A.** A compliant sink limits
  itself to the advertised 3 A; a load that ignores advertisement and simply draws
  current on a fixed-5 V source (many single-board computers, dumb loads) can pull up to
  the buck's ~6.3 A OCP without the board browning out or overheating.

No PD controller is added.

## Why not add a PD controller for a true 6 A contract

REJECTED for this board: a PD sink contract above 3 A at 5 V is non-standard (PD fixed
PDOs above 15 W move to higher voltages, not 6 A @ 5 V), and a PD/PPS front-end is a
significant cost, firmware, and complexity addition that the brief's "power/charging
board" scope does not warrant. The honest position is: **advertise what is legal (3 A),
build the headroom the brief asked for (6 A copper/regulator).**

## Consequences

- A strictly-compliant USB-C sink will draw ≤ 3 A. The 6 A capability is available to
  non-advertisement-limited loads. This is documented in the ORDER_README.
- D+/D− pairs (A6/A7, B6/B7) are shorted for legacy BC1.2 DCP so A-to-C cables still get
  a charging signal.
- SBU1/SBU2 and the second CC's role are unused beyond the Rp (no alt-mode, no PD).
