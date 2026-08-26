# ADR-0001 — module-first selection: Waveshare RP2040-Zero

Status: accepted, 2026-07-31. Binding input: P9 requires an RP2040 module.

## Decision

Use Waveshare RP2040-Zero. It integrates RP2040, 2 MB QSPI flash, 12 MHz
crystal, USB-C, boot/reset controls and RT9013-33 linear regulation in an
18.00 x 23.50 mm module. GP0–GP3 are consecutive in GPIO number and physical
order, so PIO can update the four PE42482 select inputs in one instruction
without a crossing fanout.

This is a module-first decision: it removes the carrier's hardest escape,
external flash bus, crystal network, USB-C/ESD network, core rail, regulator
and their verification surface. The carrier keeps only five module signals,
power/ground, four terminations, a status LED and RF-switch filtering.

## Rejected alternatives

- Raspberry Pi Pico: rejected because its 51 x 21 mm area is large beside the
  RF star and its RT6150 buck-boost defaults to variable-frequency PFM. Forced
  PWM burns GPIO23 and still leaves a 0.8–1.2 MHz oscillator tolerance.
- Waveshare RP2040-Tiny: electrically good and LDO-regulated, but its USB lives
  on a detachable 0.5 mm-pitch FPC adapter that becomes a lifetime accessory
  and bring-up failure point.
- Seeed XIAO RP2040: accepted as the electrical second source but not a
  footprint-compatible alternate. Its LDO is quiet, but GP0–GP4 are physically
  scrambled (D6, D7, D8, D10, D9) and its underside pads complicate the mount.
- WeAct RP2040 core: rejected because published evidence does not establish its
  regulator topology or complete schematic/BOM.
- Bare RP2040: prohibited by P9; no exception analysis is allowed for v4.

## Consequences

The module's WS2812 and on-module QSPI/clock remain potential emissions and are
included in the first physical spur survey. The module is not a drop-in JLC
line part; assembly posture is separately closed by ADR-0002.

Evidence: Waveshare RP2040-Zero schematic, dimension/pinout images and STEP
facts archived in `02_parts/RP2040-Zero/part.yaml`; Raspberry Pi Pico powerchain
datasheet and RT6150 topology review; live JLC module catalog evidence dated
2026-07-30/31 in the reused dossier.
