# Exact-parts and interface research — 2026-08-13

## Method

This stage used current primary evidence for every exact electrical claim.
Distributor records were used only to prove order-code identity and dated
availability. Textbooks, application notes, tutorials, and videos were used
as design-method cross-checks; none overrides a current standard, exact-part
data sheet, manufacturer land pattern, or JLC order option.

## Comparison and decisions

| Topic | Primary/industry evidence | Comparison with established guidance | Project decision and remaining proof |
|---|---|---|---|
| One-of-eight topology | [pSemi PE42482 data sheet](https://www.psemi.com/pdf/datasheets/pe42482ds.pdf) specifies a single absorptive SP8T, 10 MHz–8 GHz, terminated ALL_OFF and exact binary truth table. | Pozar, *Microwave Engineering*, treats every junction and discontinuity as part of the microwave network. One direct stage therefore avoids the extra junctions, control states, and accumulated loss of a switch tree. A finished module lowers layout risk but largely replaces the custom PCB. | Select PE42482A-X. Its data-sheet figures establish feasibility, not assembled-board performance; VNA qualification remains mandatory. |
| Reset-safe switching | The PE42482 truth table makes `V4..V1=1000` ALL_OFF; ST documents MCU GPIO/reset behavior. | Ott, *Electromagnetic Compatibility Engineering*, and robust embedded practice favor hardware-defined benign states over firmware-only safety. Break-before-make must be explicit, not assumed from sequential GPIO writes. | External 10-kohm biases force 1000. Firmware preloads the full word before enabling outputs and inserts 5-ms ALL_OFF guards. Schematic pin-map review and first-article edge capture remain. |
| Dwell identification | [ST STM32C011F4 data sheet](https://www.st.com/resource/en/datasheet/stm32c011f4.pdf) bounds HSI48 error and documents timers/BOR/watchdog. | A unique duration alone is not self-synchronizing. Communications practice requires framing, bounded acceptance windows, order checks, and an explicit invalid/unknown result. | Fixed ANT1..8 order, disjoint +/-5% windows, ALL_OFF guards, >=475-ms marker, 4.32-s guaranteed/full-frame capture. Absence or ambiguity decodes to `unknown`. Firmware and downstream decoder tests remain. |
| Programming connector | [Arm's CoreSight connector guidance](https://developer.arm.com/documentation/kan339/latest) specifies the compact 10-pin Cortex Debug connector, [ST's MIPI10 table](https://www.st.com/resource/en/user_manual/um3292-discovery-kit-with-stm32u083mc-mcu-stmicroelectronics.pdf) fixes VTref/SWDIO/GND/SWCLK/GNDDetect/NRST pins, and [Samtec's exact FTSH page](https://www.samtec.com/products/ftsh-105-01-l-dv-k-p-tr) identifies the keyed 2x5 1.27-mm SMT header. | Loose pads are compact but require a custom probe and permit reversal. A standard keyed connector makes service and recovery repeatable. The Pi 40-pin header is not pin-compatible, so direct GPIO programming still needs an adapter harness and must not source target power. | D13 selects exact J11 `FTSH-105-01-L-DV-K-P-TR` / JLC C2932107 with MIPI10 mapping. Manufacturer lands override the discrepant JLC library land; schematic, placement, pin-1 and cable review must be regenerated before routing. |
| USB-C power-only sink | [USB-IF Type-C Release 2.5](https://usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-25) is the current standard; [TI's Type-C design guide](https://www.ti.com/lit/pdf/slyy228) illustrates the simple sink with a separate 5.1-kohm Rd on CC1 and CC2. | Tutorials commonly show one resistor or omit explicit no-connects; that is unsafe as an implementation authority. The reversible receptacle needs both CC terminations. No PD controller is needed for a small default-current 5-V sink. | Two exact 5.1-kohm 1% Rd parts, CC ESD, D+/D-/SBU explicit NC, 4.75–5.5 V/20 mA contract; no data or PD. Schematic/ERC and connector footprint checks remain. |
| Quiet 3.3-V rail | [TI TPS7A24](https://www.ti.com/product/TPS7A24) documents 18-V input capability, fixed 3.3-V option, 1.25% accuracy, 250-mV maximum dropout and 1-uF minimum capacitance. | Linear regulation is proportionate at 20 mA: `(5.5-3.25875)*0.02=44.825 mW`; a buck adds switching energy and support parts without a thermal benefit needed here. Bogatin, *Signal and Power Integrity*, supports short local return loops and evidence-based decoupling rather than bulk capacitance by habit. | TPS7A2433DBVR; 44.825-mW worst-case dissipation, ~7.6-C estimated rise, and 1.798-uF conservative effective capacitance on each required bank. Layout and measured rail behavior remain. |
| VBUS transient coordination | [Littelfuse SMBJ data](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf), exact capacitor ratings, fuse data, and TPS7A24 limits were evaluated as one path. | A TVS name or standoff voltage is not protection proof; its maximum clamp, series element, downstream absolute ratings, and capacitor voltage rating must be compared at the same waveform. | The gate rejected the original 10-V C1 because the TVS maximum clamp is 10.3 V before margin. Use a 16-V C1. The TVS handles admitted transients only; there is deliberately no sustained-OV cutoff. |
| CC-line ESD | [TI TPD2E2U06 data sheet](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf) gives working/clamp values and placement guidance. | Protection-loop inductance makes placement and return geometry part of the clamp, so a valid part in a BOM is insufficient. | One dual-channel device close to J1, short ground return, separate downstream Rd. Exact placement is a PCB-stage review. |
| RF stackup and geometry | [JLCPCB impedance stackups](https://jlcpcb.com/impedance), [calculator](https://jlcpcb.com/pcb-impedance-calculator), and [capabilities](https://jlcpcb.com/capabilities/pcb-ca-) publish `JLC04161H-7628`, copper/dielectric values, calculator inputs, and +/-10% controlled-impedance capability. | Pozar and Johnson & Graham, *High-Speed Digital Design*, both make the return plane and transmission-line geometry inseparable from the signal path. Evaluation-board widths cannot be copied to a different dielectric build. | Lock the JLC stackup, solid adjacent L2 ground, and 50-ohm target; leave width/gap null until the official calculator is run against the final copper/ground choice. VNA measurements close board performance. |
| RF connector | [Amphenol's exact 901-143-6RFX product page](https://www.amphenolrf.com/en-us/part/901-143-6rfx/3961/) defines an active, right-angle THT 50-ohm SMA jack and links drawing `SMA6252A2-3GT50G-50`; PCN-031726 says the 2026 CN-to-VN transfer does not alter form or fit. | At 5.9 GHz the launch and ground-leg transition are RF components; a generic SMA footprint is not interchangeable. The drawing's centre and ground holes have different diameters and must be transcribed by role, not as an undifferentiated list. | D12 confirms the same exact connector on all nine ports. A hash-bound Rev-C capture fixes the 1.50-mm RF-contact hole, four 1.70-mm ground holes on a 5.08-mm square and edge datum. D13's visual question exposed only a converted-WRL registration defect: the native STEP aligns over the unchanged, correct footprint. |
| Manufacturability | Current JLC catalog observations and exact-code second-source checks cover all 14 BOM lines. The advanced escape checker rejects U1 at the default tier but accepts it at the advanced tier; all other packages pass the default tier. | DFM should be performed at exact-code freeze, before schematic/layout effort makes a substitution expensive. Stock is volatile and catalog presence is not an assembly allocation promise. Manufacturer land patterns outrank catalog CAD. | Four-layer advanced board because of PE42482 only. Re-run availability and obtain JLC uploader allocation/rotation/population echo before payment; explicitly preserve J11's Samtec land pattern despite the exact-code JLC CAD delta. |

## Tutorials and videos

Official interactive/tutorial material was preferred where the user action
must match a current service: JLC's live impedance calculator and guide for
trace geometry, and TI's current Type-C guide for the power-only sink. General
KiCad videos can be helpful for user-interface orientation but age quickly and
cannot prove a symbol pin map, custom footprint, rule-file semantics, or JLC
manufacturing option. At the schematic and PCB pauses, any tutorial/video
comparison will be version-matched to the installed KiCad and checked against
KiCad's official documentation and the generated artifact itself.

## Source and stocking result

The D13 candidate BOM contains 14 exact codes. The original 13 passed the dated
JLC catalog-stock check on 2026-08-13; new J11 code C2932107 was separately
observed as SMT-eligible, MSL1 and in stock on the same date. The SMA line
requires nine per board.
Every exact code also has an independent distributor identity check. These are
procurement-risk indicators only. They expire, and the JLC order uploader is
the authority for actual PCBA allocation and placement eligibility.

The reproducible source-stage input is
[`sourcing/exact-parts.csv`](../sourcing/exact-parts.csv). It is a candidate
BOM, not a generated schematic BOM; netlist/BOM parity becomes mandatory at
the schematic checkpoint.

Evidence provenance and the remaining STM32 revision deviation are visible in
[`02_parts/README.md`](../../02_parts/README.md). The Amphenol endpoint refused
the local client, but the exact Rev-C drawing is now retained and qualified
against the current exact product page and no-form/fit-change PCN. The local
STM32 data sheet is still Rev 4 while relevant facts were cross-checked against
Rev 5 online; that deviation may not pass design freeze without fresh evidence.
