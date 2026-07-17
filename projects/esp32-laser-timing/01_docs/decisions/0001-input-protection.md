---
id: 0001
date: 2026-07-17
status: accepted
---
# 0001 — Input protection: USB VBUS entry + three off-board wire classes

## Context

Mandatory protection ADR (pcb-design skill). Four ways in from outside:
USB-C (power + data), and three off-board wire classes on screw terminals
with runs to ~50cm on an open bench jig: laser feeds (5V + switched GND),
photodiode lines (5V bias + anode signal), button lines (3.3V pullup +
GND). Downstream ratings: ESP32-S3 GPIO abs max 3.6V+0.3; LM339 inputs
rated +36V INDEPENDENT of supply (ST datasheet abs-max table — the key
robustness fact); AO3400A VDS 30V avalanche-rated; AMS1117 Vin 15V.

## Options

**USB VBUS/data:**
- **ESD array on D+/D-** — pinned by the brief (P3). USBLC6-2SC6 chosen
  (UMW C2687116, same class verified on crowsync/usb-power-3s): its pin-5
  rail reference tied to 5V also places a working clamp on VBUS itself —
  VBUS ESD/transient protection comes free with the pinned part.
- **Dedicated VBUS TVS + polyfuse** — REJECTED: bus-powered sink < 0.6A
  from a current-limited host; the USBLC6 VBUS clamp already covers ESD;
  a polyfuse adds drop feeding the LDO for no defined fault it would clear.
- **Inrush**: on-board 5V capacitance (~150uF) exceeds the USB 10uF attach
  guideline. ACCEPTED deviation for a bench instrument: hosts/hubs
  current-limit and this class of design (100uF+ on 5V dev boards) is
  ubiquitous; documented rather than "fixed" — a series inrush limiter
  would drop laser-rail voltage. Flagged in ORDER_README first-power notes.

**Laser terminals (5V + FET drain):**
- Short-to-GND of the 5V pin = USB host port current limit (and bulk cap)
  — no board damage mechanism; accepted.
- Drain wire inductive kick at turn-off: 0.5uH x 40mA = 0.4nJ, absorbed
  by the AO3400A's rated 30V avalanche. Snubber/flyback REJECTED as
  unnecessary at 40mA resistive loads.
- Miswire 5V->drain (laser omitted): FET turn-on shorts 5V through the
  wire; host current-limit + FET 5.7A rating survive it; accepted with a
  plain-words silk label per terminal (P10) as the primary miswire defense.

**Photodiode terminals (the exposed analog input):**
- Brief pins the topology: terminal -> 1k load -> LM339 +IN, no caps
  (P6). Protection beyond that considered:
  - **Series R / clamp diodes at +IN** — REJECTED: the LM339 input is
    rated to +36V regardless of VCC and the node's 1k-to-GND load bleeds
    static; adding a clamp network buys nothing the comparator doesn't
    already tolerate, and any C added would violate the microsecond-edge
    requirement. Negative transients see the LM339's substrate diode via
    the 1k; energy at 50cm-wire scale is trivial.
  - Nothing connects the PD line to an MCU pin — the LM339 isolates the
    GPIO domain from the field wiring by construction. This is the
    protection architecture: the 36V-tolerant part faces the wire.
- Miswire (5V onto the signal pin): 5V node -> comparator sees 5V (rated
  36V), 1k load dissipates 25mW. Harmless; accepted.

**Button terminals:**
- 10k pullup + 100nF + 1k series into the GPIO (pinned, P9). The 1k
  series resistor IS the GPIO protection: with the S3's internal clamps,
  a 5V miswire onto a button terminal injects (5−3.6)/1k ≈ 1.4mA —
  within safe clamp current. ESD hits the 100nF + 10k node first.
  Additional TVS REJECTED: bench jig, 3.3V domain, series-R bounded.

## Decision

USBLC6-2SC6 at the USB connector clamping D+, D−, and (via its rail pin)
VBUS; no polyfuse/inrush device (documented deviation); laser channels
protected by FET avalanche rating + silk labeling; photodiode channels
protected by the LM339's 36V input rating with the pinned 1k load;
buttons by the pinned 10k/100nF/1k network. No parts beyond the brief's
prescription were added; each omission is justified above.
