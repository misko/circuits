# Pluto RX2 8-way v4

An evidence-first, JLC-assemblable 70 MHz–6 GHz antenna selector for the
PlutoPlus RX2 input. Eight antenna states are sequenced by a Waveshare
RP2040-Zero module; the eighth is a low-loss resistive tap of the RX1 antenna.
The module provides USB-C, flash, clock, linear regulation and host control.

The authoritative intent is in `01_docs/BRIEF.md`. Circuit source lives in
`03_tscircuit/`; deterministic floorplan, rules, and routing inputs live in
`03_src/`. Generated KiCad and manufacturing evidence must not outrank those
sources.

Status: layout sealed from fresh source; final KiCad DRC is 0 violations,
0 unconnected items, and 0 schematic-parity issues. Fabrication release and
RF characterization remain intentionally open.
