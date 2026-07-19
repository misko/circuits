# ADR-0005 — Power architecture & USB co-power

Context: §7.1 external 5 V ≥2 A; Pico may also be USB-powered; relay coils
must never load the Pi's USB port; §7.2 wants a low-noise 3.3 V independent
of the Pico's module regulator + optional filtered analog rail.

Decision: single protected rail 5VP; RELAY_5V branches through the gated
high-side switch DIRECTLY off 5VP (upstream of the VSYS OR diode) — with
board power absent, USB cannot reach RELAY_5V through any path (D1 SS34
blocks reverse into 5VP; Q1 default-off besides). Pico rides VSYS via SS34;
its internal VBUS→VSYS Schottky ORs USB per the RPi hardware design guide;
no backfeed into the Pi (module's own diode) and no coil current over USB
(§7.1) by construction. VBUS socket pin → TP only (D12).

3.3 V: AMS1117-3.3 (C6186, basic, 1 A): sensors+logic ≤0.3 A → 0.51 W,
thermals in DETAIL_DESIGN #9. The Pico's onboard 3V3 powers nothing on the
board (§7.2). 3V3A = 3V3 through 600 Ω@100 MHz ferrite + 10 µF+100 nF for
MAX31856 + thermistor references (§7.2 "separate filtered analog rail").
Rejected: dedicated low-noise LDO (e.g. LP5907 ≤250 mA) — MAX31856 has 50/60
Hz digital filtering and PSRR enough that a ferrite-filtered rail meets the
±0.7 °C class; budget favors AMS1117 (basic part, no reel fee).

Power budget (§7.6): Pico 150 + sensors 300 + coils 160 = 610 mA typ-max
vs 2000 mA supply → 227% margin (≥50% required).
