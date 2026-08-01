subject: pluto-rx2-8way-v4 48688aa3
date: 2026-07-31
reviewer: render-review
context-given: curated-pre-seal-zero-context
design_verdict: SOUND
order_verdict: ORDER

summary:
No P0 or P1 defect was found. The modeled and bare renders agree on population, placement, connector orientation, mechanical form, IC polarity, and LED polarity. The remaining findings are P2 documentation/render-evidence improvements and do not block ordering. Order-time acceptance of the ten through-hole SMA connectors by the assembly uploader remains mandatory.

findings:

- P0: None.

- P1: None.

- P2 — S6 schematic readability is EFFORTFUL.
  exact_evidence: The one-page schematic has useful local drawn circuits, but power and primary RF tracing still requires label hops. In particular, U_MCU pin 21 reaches the separately drawn FB_3V3 input through the N3V3_MOD label, while N3V3 leaves the ferrite through another label. Likewise, U_SW RF pins and the antenna/output connectors are joined principally through ANT1–ANT8, RX1_TAP, and RX2_OUT labels rather than continuous drawn signal paths.
  recommended_disposition: Accepted for this order; in the next schematic revision, draw the complete U_MCU 3V3 -> FB_3V3 -> N3V3 -> U_SW power chain together and add continuous or clearly grouped RF signal-chain presentation.

- P2 — S7 schematic decoupling adjacency is not met.
  exact_evidence: C_SW1 100 nF and C_SW2 1 uF are drawn together in the upper-left N3V3 block, remote from U_SW in the center of the sheet; the reader must infer the served IC through the N3V3 label. The board render does place these parts directly below U_SW, so this is schematic-teaching debt rather than evidence of a population error.
  recommended_disposition: Accepted for this order; redraw C_SW1/C_SW2 beside U_SW VDD in the next schematic revision.

- P2 — LED polarity silk is cramped.
  exact_evidence: In render_top_bare.png and twin_top.png, the LED cathode “K” marker visually reads as an appended character in “ANT8 = RX1 TAP -20.26 dB K”. The modeled LED’s green cathode bar is nevertheless on the same right-hand end identified by the K, so the modeled orientation is internally consistent.
  recommended_disposition: Accepted for this order; move the K marker immediately beside the LED outline and away from the informational sentence before the next release.

- P2 — Twin provenance text names a different CPL path.
  exact_evidence: missing_models.txt reports 27/27 bodies and no missing models, but names `06_build/fab_candidate/cpl.csv` as its source while the reviewed fabrication CPL is `06_build/fab/cpl.csv`. Visual inspection found the same 27-designator population and matching placement, but the text does not bind the twin explicitly to the reviewed CPL path.
  recommended_disposition: Before sealing the immutable release, regenerate the twin from the final CPL or record matching hashes/content identity in the provenance output.

population_truth:
The BOM contains 11 lines resolving to 27 designators. The CPL contains 27 rows, all top-side: 10 SMA connectors, U_SW, LED_ST, three capacitors, FB_3V3, and 11 resistors. twin_top.png visibly contains that population, while U_MCU and H1–H4 remain unpopulated as intended. twin_bottom.png and render_bottom_bare.png show no bottom-side component population. missing_models.txt reports bodies mounted 27/27 and no missing models. The modeled and bare top images align at U_SW, the switch decoupling/pulldown cluster, the RX1 tap resistors, all ten SMA sites, the module pads, LED/status network, and ferrite/bulk-capacitor pair.

connector_and_mechanical_orientation:
All ten modeled SMA bodies are upright on the top face with their center contacts registered to the signal barrels and their four ground legs registered to the surrounding plated holes. The alternating 0°/45° placements match the corresponding square/diamond footprint orientations. The edge renders show the plug-in legs extending below the PCB, with no unintended bottom-side bodies. H1–H4 remain clear. The U_MCU footprint is oriented with its USB end at the lower board edge and remains bare for hand soldering. The module itself is not modeled, so its real underside clearance still requires the documented hand-fit check.

polarity_and_orientation:
U_SW’s modeled pin-1 dot is at the upper-left and coincides with the board’s pin-1 marker; CPL rotation is 0°. LED_ST’s modeled green cathode mark is on the same right-hand end indicated by the silk K; CPL rotation is 0°. No modeled/bare polarity contradiction was found.

usability_and_legibility:
The large functional labels ANT1–ANT8, RX1, RX2, the receive-only warning, passive-antenna voltage warning, tap level, hand-solder instruction, and USB-C note are legible in the top renders. Some reference designators are necessarily covered by installed SMA bodies, but the functional connector labels remain visible. The LED K-marker collision noted above is the only material silk-readability issue found.

S5_math_spot_checks:

1. Timing frame:
   ordinary state = 128 + 8192 = 8320 samples.
   reference state = 128 + 4096 = 4224 samples.
   frame = 7 × 8320 + 4224 = 62,464 samples.
   62,464 / 30,000,000 = 2.082133 ms, and 30,000,000 / 62,464 = 480.276 sweeps/s.
   Eight frames = 8 × 62,464 = 499,712 samples.
   result: PASS; the documented values re-derive exactly.

2. RX1 resistive tap:
   With 50-ohm source and main load, the tap branch is 220 + 220 + 50 = 490 ohms. The effective load at RX1_MAIN is 50 || 490 = 45.370 ohms. Relative main voltage is `[45.370 / (50 + 45.370)] / 0.5 = 0.95145`, giving 20 log10(0.95145) = -0.432 dB. The tap voltage relative to the unloaded 50-ohm main reference is `[45.370 / (50 + 45.370)] × (50 / 490) / 0.5 = 0.09708`, giving 20 log10(0.09708) = -20.26 dB.
   result: PASS; this independently reproduces the documented approximately -0.43 dB main loss and -20.3 dB tap level.

final_disposition:
Proceed with the order from the reviewed design/render evidence. In the actual uploader, verify U_SW and LED preview orientation and obtain explicit assembly-process acceptance for all ten KH-SMA-KE-Z through-hole jacks. Resolve the P2 twin-provenance item before sealing the immutable release.
