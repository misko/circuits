# ADR-0003 — absorptive SP8T and split-arm reference tap

Status: accepted, 2026-07-31.

Use PE42482A-X for the eight-state 70 MHz–6 GHz receive selector. Its parallel
control avoids serial latency and its absorptive ports bound inactive behavior.
State 8 receives a resistive branch of two 220-ohm 0402 resistors from the RX1
antenna main line.

A broadband directional coupler cannot provide the required 85.7:1 span, while
a 3 dB splitter permanently costs too much RX1 sensitivity. The pickoff keeps
the confirmed compromise. High-band reference SIR is limited by aggregate
switch leakage and must be measured and included in the correction table.

The system boundary is passive receive-only, 50 ohm, no bias tee, and 0 VDC at
every SMA in powered, unpowered, and fault states. The board is limited to
+18 dBm CW at any SMA. Hot switching/hopping is supported only from
100 MHz to 6 GHz, where the switch rating is applicable; 70 MHz to below
100 MHz is static/cold-switch operation with RF removed during selection and
settling. With no system RF ESD clamps, it is ESD-controlled bench equipment.
