---
id: 0002
date: 2026-07-16
status: accepted
---
# 0002 — USB-C: fixed 5 V, Rp = 10 kΩ (3 A advertisement), hardware sized for 6 A

## Context

The brief asks for a USB-C port "6A max". The Type-C spec allows a source to
advertise current only via Rp on CC (56 kΩ = default, 22 kΩ = 1.5 A,
10 kΩ = 3.0 A); anything above 3 A requires USB-PD negotiation AND an
e-marked cable, and even PD tops out at 5 A — 5 V/6 A is not a spec-legal
contract at all.

## Options

- **PD source controller (e.g. IP2723/WT6633B class)** — could advertise
  5 V/5 A with e-marker check. REJECTED: still cannot reach 6 A legally;
  adds a programmable IC, firmware/OTP configuration, and D+/D- protocol
  parts for zero gain toward the brief's 5 V-only intent.
- **Rp = 10 kΩ to 5 V on CC1 and CC2** — dumb, robust, spec-maximal 3 A
  advertisement; any sink may legally draw 3 A, and non-compliant
  high-draw devices (the realistic 6 A use case) are limited only by the
  converter's ~7-8 A cycle-by-cycle limit.
- **Rp as current source per full spec + VBUS cold until attach** —
  compliance nicety. REJECTED: needs a load switch + attach detection;
  always-on VBUS is standard practice for charger boards.

## Decision

Fixed always-on 5 V VBUS, Rp = 10 kΩ 1% from each of CC1/CC2 to 5V_C
(advertises 3.0 A), with converter, connector, and copper all rated for
6 A continuous.

## Consequences

Compliant sinks draw at most 3 A; the extra headroom to 6 A serves
resistor-trigger loads and parallel/legacy devices. The 16-pin connector
must use all four VBUS and four GND contacts, and its VBUS rating must be
verified >= 6 A (part.yaml fact). CC lines get ESD protection. No firmware,
no OTP, no digital parts on the board.
