# USB Hub 3S v4 — detail design

Status: commission only. No component values or copper dimensions are yet
approved.

## Locked boundary

The commission facts are in `BRIEF.md`; the machine-readable output and source
envelopes are in `../03_src/rules/requirements.yaml` and
`../03_src/rules/power_tree.yaml`. Those files currently identify inherited
requirements and candidate topology only. They are not a completed design.

## Calculations owed before schematic generation

Stage 1 and Stage 2 must provide equations, cited inputs, worst-case corners,
results, selected values, and margins for:

- total and per-rail input current over 9.0–12.6 V, including efficiency;
- switching frequency and controller timing components;
- inductor ripple, saturation and RMS current;
- output/input capacitance and ripple-current rating;
- feedback divider tolerance at minimum and maximum corners;
- USB-A and USB-C delivery-path resistance and load voltage;
- current-limit threshold, shunt/inductor tolerances, and peak path rating;
- controller compensation and loop-stability evidence;
- UVLO, reverse-current, transient-clamp and MOSFET stress coordination;
- shutdown current and estimated storage drain;
- PCB copper/via temperature rise and connector-contact derating.

Silence is intentional at commission: the project must not inherit v3's
component math until every input has been re-cited or re-measured for v4.
