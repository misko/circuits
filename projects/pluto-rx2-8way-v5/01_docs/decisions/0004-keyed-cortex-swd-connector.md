# ADR-0004: keyed Cortex SWD programming connector

Status: accepted

Date: 2026-08-13

## Context

D11 selected direct Raspberry Pi GPIO SWD, with ST-LINK compatibility and a
self-powered target. The first schematic exposed those signals as five loose
test pads. D13 explicitly rejects pads and requires a proper connector. The
change must retain the same electrical programming method without inventing a
private cable pinout or allowing the programmer to power the board.

Arm's 10-pin Cortex Debug interface uses a 2x5, 1.27 mm connector. ST's MIPI10
mapping assigns pin 1 to target VTref, pin 2 to SWDIO, pins 3 and 5 to ground,
pin 4 to SWCLK, pin 9 to GNDDetect and pin 10 to NRST. The STM32C011 design does
not expose SWO or JTAG TDI, so pins 6, 7 and 8 have no signal source.

## Decision

Fit J11 as exact Samtec `FTSH-105-01-L-DV-K-P-TR`, JLC `C2932107`: keyed,
vertical SMT, 2x5 at 1.27 mm pitch, with pick-and-place pad and tape-and-reel
packaging. Use the standard target mapping:

| J11 pin | Net | Role |
|---:|---|---|
| 1 | 3V3 | target-powered VTref/sense; never a programmer supply |
| 2 | SWDIO | bidirectional debug data |
| 3, 5 | GND | signal return |
| 4 | SWCLK | debug clock |
| 6 | NC | SWO unavailable/not used |
| 7 | NC | key/reserved position |
| 8 | NC | JTAG TDI unavailable/not used |
| 9 | GND | GNDDetect compatibility |
| 10 | NRST | target reset |

Follow Samtec's manufacturer-recommended SMT land pattern. The exact-code JLC
CAD is retained as an assembly/model comparator but cannot override Samtec's
land dimensions. A Raspberry Pi connects through a keyed Cortex cable and a
small GPIO breakout harness; the Cortex connector is not pin-compatible with
the Pi's 40-pin header. The target remains powered only by USB-C.

## Consequences

The programming interface is polarized, serviceable and compatible with
standard debug probes. J11 becomes an assembled BOM/CPL component rather than
five non-assembled copper features. The schematic, manifest, part set,
placement and all hash-bound reviews must be regenerated before routing.

Direct Pi wiring remains host-dependent and must be tested during firmware
bring-up. Connecting Pi 5 V or Pi 3V3 to J11 pin 1 is prohibited because it can
back-power or contend with the board's protected 3.3 V rail.

Primary sources:
[Arm CoreSight connector guidance](https://developer.arm.com/documentation/kan339/latest),
[ST MIPI10 signal table](https://www.st.com/resource/en/user_manual/um3292-discovery-kit-with-stm32u083mc-mcu-stmicroelectronics.pdf),
[Samtec exact product](https://www.samtec.com/products/ftsh-105-01-l-dv-k-p-tr),
[Samtec series print](https://suddendocs.samtec.com/prints/ftsh-1xx-xx-xxx-dv-xxx-xxx-x-xx-mkt.pdf), and
[Samtec recommended footprint](https://suddendocs.samtec.com/prints/ftsh-1xx-xx-xxx-dv-xxx-footprint.pdf).

Manufacturing evidence:
[JLC C2932107](https://jlcpcb.com/partdetail/Samtec-FTSH_105_01_L_DV_K_PTR/C2932107).
