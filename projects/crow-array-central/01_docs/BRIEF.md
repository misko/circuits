# BRIEF — crow-array-central

This board is part of the crow-array commission: the authoritative
verbatim brief, parse (P1-P8), Q/A (A1-A3) and decision register live in
../crow-array/01_docs/BRIEF.md (source sha 21e54984...). This file carries
board-local decisions only.

## Decision register (board-local; D1/D2 live in the shared BRIEF)

- D3 (2026-07-18): **4-layer** JLC7628 (brief allowed 4-6) —
  decisions/0001-layer-count-4.md. Solid In1 GND under everything; In2
  power islands; 6L rejected as cost without a passing-gate benefit.
- D4: 5V entry = DC-005 barrel (center+, matches GST25A05-P1J) populated
  + KF128L-3.5-2P terminal DNP alternate; protection = 2A PTC + SMAJ5.0A
  + AO3401A reverse P-FET — decisions/0002-input-protection.md.
- D5: TQ128 escape verified feasible at JLC 4L STANDARD tier before
  commitment (peripheral pins escape straight out; no between-pad
  routing needed) — decisions/0004-tq128-escape-feasibility.md.
- D6: beeper gate slowing 1k + 4.7nF (tau ~5us) + 100k pulldown; clamp
  stays at the pod; BEEP_RETn single-point at the FET drain —
  decisions/0005-beeper-gate-edges.md.
- D7: port->channel map: J1-J4 -> ADC1 VIN1-4, J5-J8 -> ADC2 VIN1-4;
  J7/J8 jacks DNP (channels 7/8 reserved); injection header couples into
  ADC1 ch4? NO — injection must hit BOTH chips: couples into ch4 (ADC1)
  and ch8 (ADC2) via series resistors. (Amended: ch4 shares port 4 —
  injection taps carry series 1k so a populated port and the header
  never fight; ch8's port is DNP in Rev-A.) See ARCHITECTURE.md.
- D8: XMOS-reference fidelity ADR-0003 (power sequencing / clocking /
  USB copied from the platform hardware manual, figure-cited) — pending
  the manual extraction, appended on completion.
