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
| USB-C power-only sink | [USB-IF Type-C Release 2.5](https://usb.org/document-library/usb-type-cr-cable-and-connector-specification-release-25) is the current standard; [TI's Type-C design guide](https://www.ti.com/lit/pdf/slyy228) illustrates the simple sink with a separate 5.1-kohm Rd on CC1 and CC2. | Tutorials commonly show one resistor or omit explicit no-connects; that is unsafe as an implementation authority. The reversible receptacle needs both CC terminations. No PD controller is needed for a small default-current 5-V sink. | Two exact 5.1-kohm 1% Rd parts, CC ESD, D+/D-/SBU explicit NC, 4.75–5.5 V/20 mA contract; no data or PD. Schematic/ERC and connector footprint checks remain. |
| Quiet 3.3-V rail | [TI TPS7A24](https://www.ti.com/product/TPS7A24) documents 18-V input capability, fixed 3.3-V option, 1.25% accuracy, 250-mV maximum dropout and 1-uF minimum capacitance. | Linear regulation is proportionate at 20 mA: `(5.5-3.25875)*0.02=44.825 mW`; a buck adds switching energy and support parts without a thermal benefit needed here. Bogatin, *Signal and Power Integrity*, supports short local return loops and evidence-based decoupling rather than bulk capacitance by habit. | TPS7A2433DBVR; 44.825-mW worst-case dissipation, ~7.6-C estimated rise, and 1.798-uF conservative effective capacitance on each required bank. Layout and measured rail behavior remain. |
| VBUS transient coordination | [Littelfuse SMBJ data](https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf), exact capacitor ratings, fuse data, and TPS7A24 limits were evaluated as one path. | A TVS name or standoff voltage is not protection proof; its maximum clamp, series element, downstream absolute ratings, and capacitor voltage rating must be compared at the same waveform. | The gate rejected the original 10-V C1 because the TVS maximum clamp is 10.3 V before margin. Use a 16-V C1. The TVS handles admitted transients only; there is deliberately no sustained-OV cutoff. |
| CC-line ESD | [TI TPD2E2U06 data sheet](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf) gives working/clamp values and placement guidance. | Protection-loop inductance makes placement and return geometry part of the clamp, so a valid part in a BOM is insufficient. | One dual-channel device close to J1, short ground return, separate downstream Rd. Exact placement is a PCB-stage review. |
| RF stackup and geometry | [JLCPCB impedance stackups](https://jlcpcb.com/impedance), [calculator](https://jlcpcb.com/pcb-impedance-calculator), and [capabilities](https://jlcpcb.com/capabilities/pcb-ca-) publish `JLC04161H-7628`, copper/dielectric values, calculator inputs, and +/-10% controlled-impedance capability. | Pozar and Johnson & Graham, *High-Speed Digital Design*, both make the return plane and transmission-line geometry inseparable from the signal path. Evaluation-board widths cannot be copied to a different dielectric build. | Lock the JLC stackup, solid adjacent L2 ground, and 50-ohm target; leave width/gap null until the official calculator is run against the final copper/ground choice. VNA measurements close board performance. |
| RF connector | [Amphenol 901-143-6RFX product/drawing](https://www.amphenolrf.com/en-us/products/sma-connectors/901-143-6rfx/) defines a right-angle THT SMA jack and mounting geometry. | At 5.9 GHz the launch and ground-leg transition are RF components; a generic SMA footprint is not interchangeable. | Same exact connector on all nine ports is provisional D9. The current official drawing must be locally captured and the custom footprint independently reviewed before placement. |
| Manufacturability | Current JLC catalog observations and exact-code second-source checks cover all 13 BOM lines. The advanced escape checker rejects U1 at the default tier but accepts it at the advanced tier; all other packages pass the default tier. | DFM should be performed at exact-code freeze, before schematic/layout effort makes a substitution expensive. Stock is volatile and catalog presence is not an assembly allocation promise. | Four-layer advanced board because of PE42482 only. Re-run availability and obtain JLC uploader allocation/rotation/population echo before payment. |

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

The candidate BOM contains 13 exact codes and every one passed the dated JLC
catalog-stock check on 2026-08-13. The captured pool contained at least 951 of
every code at the tested quantities; the SMA line requires nine per board.
Every exact code also has an independent distributor identity check. These are
procurement-risk indicators only. They expire, and the JLC order uploader is
the authority for actual PCBA allocation and placement eligibility.

The reproducible source-stage input is
[`sourcing/exact-parts.csv`](../sourcing/exact-parts.csv). It is a candidate
BOM, not a generated schematic BOM; netlist/BOM parity becomes mandatory at
the schematic checkpoint.

Two evidence deviations remain intentionally visible in
[`02_parts/README.md`](../../02_parts/README.md): the current Amphenol drawing
endpoint refused unattended download, and the local STM32 data sheet is Rev 4
while relevant facts were cross-checked against Rev 5 online. Neither deviation
may pass its affected footprint/release gate without fresh evidence.
