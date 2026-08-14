---
status: superseded-by-0007
---
# ADR-0006 — Restore four simultaneous 3 A ports with a bounded power path

date: 2026-08-01
tags: [topology, power, voltage-margin, sourcing, safe-startup]

## Context

ADR-0001 and ADR-0004 reduced the board to 2 A per port because the former
LM5116/TPS259470 implementation could not prove gate-drive or complete-path
voltage margin. The board objective remains four simultaneous proprietary
5 V / 3 A USB-A power outputs with USB 2.0 data. A replacement may be selected
only after exact-part sourcing clears two independent authorized supplier
pools and the worst-case mated-plug voltage is proven before layout.

## Options considered

- Retain the 2 A TPSM63606/TPS259470 implementation. Rejected because it no
  longer meets the commissioned 3 A output and TPSM63606 failed the current
  two-supplier selection gate.
- Use TPSM64406RCHR for each 6 A rail. Electrically and commercially available,
  but its 788-812 mV full-temperature feedback-reference range cannot keep the
  unloaded output below 5.25 V while preserving the required worst-low
  connector voltage through the complete 3 A path.
- Use LTC3889IUKG#PBF with external 60 V MOSFET stages. Selected because its
  independent channels, programmable command, and less-than +/-0.5% output
  error preserve the connector window. The bare-IC exception is separately
  recorded by ADR-0005.

## Decision

Use one LTC3889 dual controller at 250 kHz. Each rail uses a CSD18533Q5AT
high-side/low-side pair, two symmetric 6.8 uH inductors in parallel, and two
10 mOhm Kelvin shunts in parallel. Program and read back Linear16 command
`0x14DC`, representing 5.21484375 V. The release voltage envelope is bounded
conservatively at 5.183925-5.246075 V.

Use one TPS259830LNRGER per port with 300 Ohm RILIM and an external AON6354
reverse-blocking FET. The eFuse guarantees the external gate off when disabled.
The complete per-port resistance budget is:

| element | bounded maximum |
|---|---:|
| TPS259830 pass path | 4.5 mOhm |
| AON6354 blocking FET | 5.2 mOhm |
| PCB copper, vias, joints | 10.0 mOhm |
| USB1130 VBUS and GND contacts | 80.0 mOhm |
| total | 99.7 mOhm |

At 3 A with 20% residual margin, the drop allowance is
`3 A * 99.7 mOhm * 1.20 = 358.92 mV`. The worst-low mated-plug voltage is
therefore 4.825005 V, above 4.75 V, while the unloaded high corner remains
below 5.25 V.

RILIM = 300 Ohm yields the cited 4.36-5.66 A device limit range. A 2.15 kOhm
IMON burden keeps the management ADC below its input ceiling at the 5.66 A
fault corner. The power capability is proprietary; it does not claim that
USB 2.0 or BC1.2 grants every attached device a generic 3 A entitlement.

Generate a protected-input 6 V auxiliary rail with LMR36510FADDAR and feed
AP63203QWU-7 from that rail, not directly from VIN_PROTECTED. AUX_6V supplies
LTC3889 EXTVCC and bounds the 3.3 V converter input.

Hardware holds both LTC3889 RUN pins low until the management MCU has written
and read back the complete volatile configuration. Q7/Q8 pull RUN low whenever
their MCU hold nets are released; R22/R23 pull those MOSFET gates high. Factory
EEPROM state and firmware intent alone are not credited as a safe default.

## Sourcing decision

The exact selected controller, switching FET, eFuse, auxiliary converter,
auxiliary inductor, RUN pull-down transistor, and temperature-sense transistor
each passed the two-independent-supplier pre-selection evidence in
`01_docs/sourcing/dual-source-2026-08-01-backtrack.md`. Stock must be refreshed
again from the same exact MPNs before payment.

## Consequences

- ADR-0001 and ADR-0004 are superseded; their 2 A limits and old parts must not
  appear in live rules, source, BOM, placement, fabrication, or release files.
- The four-layer advanced JLC tier is required for the LTC3889 and split-pad
  TPS259830 escapes and filled thermal/current vias.
- Placement must follow both converter reference layouts, preserve symmetric
  current paths and Kelvin sense routing, and pass P-ADJ before routing.
- Release still requires authoritative ERC, pin-map, DRC 0/0, source/schematic/
  PCB parity 0, exact-artifact adversarial review, and JLC fabrication review.

## 2026-08-01 current-limit amendment

The initial 48.2 mV cycle-by-cycle current-limit tier was nominal-only and is
rejected before topology sign-off. At 24 V input, 5.21484375 V output, 250 kHz,
and two 6.8 uH -20% inductors in parallel, total ripple is 6.0026 A peak to
peak. A 6 A rail therefore requires 9.0013 A peak before margin. With the
LTC3889 high-range 68/75 minimum-threshold ratio and the +1% corner of two
10 mOhm shunts in parallel, 48.2 mV permits only 8.6537 A peak.

Adopt Linear11 `IOUT_OC_FAULT_LIMIT = 0xD2F2` = 11.78125 A, corresponding to
58.90625 mV at `IOUT_CAL_GAIN = 5 mOhm`. The bounded threshold/shunt range is
10.5759-13.0109 A peak. The low corner clears load plus half-ripple with 15%
required margin; the high corner remains below the 15.2 A single-inductor
Isat(-20%) rating. The exact calculation is now an E-SWDRV schema-2 gate in
`power_stages.yaml`, so a future current-limit or inductor/shunt edit fails at
the schematic stage rather than surviving to placement or first article.
