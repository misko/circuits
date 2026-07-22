---
id: 0001
date: 2026-07-16
status: accepted
---
# 0001 — Input protection: USB VBUS entry + field-harness lines

## Context

Mandatory protection ADR (pcb-design skill). Three ways in from outside:
USB-C (power + data, human-handled cable), the outdoor microphone harness
(via a sealed M8 on the enclosure — long unshielded wire, outdoor static),
and the GNSS PPS harness. Downstream ratings: PCM2900C absolute max on
D+/D- is VDDI+0.3 V-referenced; TLV9062 inputs limited to rail ±0.5 V;
codec analog inputs −0.3 to +4 V.

## Options

**USB entry:**
- **Fuse/polyfuse + TVS on VBUS** — REJECTED as overkill: we are a bus-POWERED
  sink drawing 70 mA from a host with its own current limiting; a series
  polyfuse adds drop and nothing a 5 V host doesn't already provide.
- **No ESD, rely on codec** — REJECTED: PCM2900C D+/D- are ±LV-TTL pins with
  no rated contact-discharge tolerance; a certified-compliant board needs
  connector-side clamping.
- **USBLC6-2SC6 array** (chosen) — IEC 61000-4-2 level 4 (±15 kV air), 3.5 pF
  line capacitance (fine at 12 Mbps), clamps D+, D-, AND VBUS in one SOT-23-6;
  92k in JLC stock; the exact part class verified on the usb-power-3s board.
- **Inrush**: input bulk capped at 10 uF (USB spec attach limit); codec's own
  2R2/1u pin filter per datasheet fig 38. No further inrush device at 70 mA.

**Harness lines (mic, PPS) — A3 directive: "ESD + bias-line clamp — TVS/ESD
array on mic and PPS lines, series resistance, ferrite on mic bias":**
- **Discrete bidirectional TVS per line** — works, 2 extra placements, and a
  5 V-class bidirectional clamp leaves the TLV9062 input exposed between
  ±5 V clamp and ±(3.3+0.5) V rating; series R must absorb the gap anyway.
- **Second USBLC6-2SC6 referenced to 3V3A** (chosen) — rail-referenced diode
  steering clamps MIC and PPS to GND-0.7…3V3A+0.7 V, exactly bracketing both
  signals (MIC sits at 2.2 V DC, PPS is 3.3 V CMOS); one part, same LCSC reel
  as D1. Its VBUS pin doubles as a clamp on the 3V3A rail. 3.5 pF on the mic
  line is inaudible (fc with 2.2k bias ≈ 20 MHz).
- Plus per A3: **R9/R14 = 100R series** between connector and circuit (limits
  residual clamp current into U2/the divider; with TLV9062 10 mA input-current
  rating, survives > ±1.7 V overdrive past the clamp), and **FB1 ferrite
  (600R @ 100 MHz)** on the mic bias feed so RF picked up by the field wire
  cannot pump the 3V3A rail.

## Decision

D1 USBLC6-2SC6 at the USB-C connector (D+, D-, VBUS); D2 USBLC6-2SC6 at
J2/J3 referenced to 3V3A (MIC, PPS lines + rail clamp); 100R series in both
harness lines; ferrite + RC on the mic bias feed; 10 uF max input bulk.

## Consequences

- Both ESD parts live within 3 mm of their connectors, clamp-to-GND vias
  direct to the plane.
- ±15 kV contact events shunt at the board edge; residual is series-R
  limited below TLV9062/PCM2900C input ratings.
- No protection against a harness miswired to > 5 V supply (not in scope:
  harness is captive inside the user's enclosure, keyed connectors —
  BRIEF A3 scope).
