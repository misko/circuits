# BRIEF — crow-array-central

This board is part of the crow-array commission: the authoritative
verbatim brief, parse (P1-P8), Q/A (A1-A3) and decision register live in
../crow-array/01_docs/BRIEF.md (source sha 21e54984...). This file carries
board-local decisions only.

## Decision register (board-local; D1/D2 live in the shared BRIEF)

- D3 (2026-07-18): **4-layer** JLC7628 (brief allowed 4-6) —
  decisions/0001-layer-count-4.md. **SUPERSEDED by ADR-0008 / D18: 6-layer**
  — 4L would not close routing (XU316 escape + distributed power + the 8
  beeper-gate lines saturate 3 signal layers); 6L (4 signal layers over 2
  GND planes) is the routable design, within the brief's 4-6 allowance.
- D4: 5V entry = DC-005 barrel (center+, matches GST25A05-P1J) populated
  + KF128L-3.5-2P terminal DNP alternate; protection = 2A PTC + SMBJ5.0A
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

## Board-local design decisions (D9-D14; recorded during generator build 2026-07-18)

- D9 (2026-07-18): **Q9 reverse-FET orientation** = SOURCE(pad2)=5V load,
  DRAIN(pad3)=5V_P input, GATE(pad1)=GATE9->R90 100k->GND —
  decisions/0007-reverse-fet-orientation.md. This is the electrically-
  correct reading of ADR-0002's "body diode conducts first" (AO3401A P-ch
  body-diode anode=drain) and SUPERSEDES ADR-0002's literal "drain toward
  load". Flagged for the dedicated pin reviewer (polarity-trap class).
- D10: **schematic on A0 sheet** — the XU316 is a single 129-pad symbol
  (~165mm tall); A0 is the smallest KiCad sheet that holds it plus the ~20
  other functional regions. generate_schematic.py registers A0 in the
  schwriter2 paper table.
- D11: **W25Q16 footprint = KiCad SOIC-8_5.3x5.3mm_P1.27mm** (208-mil SS).
  The part.yaml's named 5.23x5.23 footprint does not exist in KiCad; 5.3x5.3
  is the 208-mil match (body 5.23 nom, sec 11.3 drawing). part.yaml updated.
- D12: **PLL_AVDD filter = FB3 600R ferrite (0402) + 1uF C123**, copying
  the XMOS FB3 (§14 p30, our fidelity mandate). No qualified ferrite-bead
  part existed in 02_parts; FB3 carries footprint L_0402_1005Metric and the
  exact 600R@100MHz bead MPN is chosen at bom_seed. Not a resistor (a
  resistor RC was rejected: worse HF rejection on a PLL analog supply).
- D13: **XU316 pin assignment** (from part.yaml Table 4 + XMOS-ref port map):
  MCLK from APLLOUT (pin23 X1D11) -> NC7NZ34 buffer -> both ADC SCKI, tile0
  loopback on pin7 (X0D11); LRCK=X1D01(20), BCLK=X1D10(22), TDM DATA1/2 =
  X1D24(107)/X1D25(108); I2C SCL/SDA = X0D35(93)/X0D36(94); 8 beeper GPIOs
  on 3.3V IOR/IOT pins X0D24-29 + X1D26-27; LV_L/T/R_N tied to 3V3 (3.3V IO);
  MIPI unused (VDD pins->GND, data->NC); pin55 & USB_ID(58) NC.
- D14: **USB self-powered posture** — CC1/CC2 get 5.1k Rd device pulldowns;
  VBUS presence sensed via a 220k/330k divider to VBUS_DET (X0D14); RJ45 SH
  and USB-C SH tied to GND (single-point chassis-to-GND, no separate shield
  net in Rev-A).

## Routing decisions (D15-D16; 2026-07-18)

- D15 (2026-07-18): **power distributes as floored tracks across F/In2/B**,
  NOT as In2 rail islands. The rails are spatially intermixed — 3V3 (47
  pads) and 0V9 (35 pads) are both dense at the XU316, and 3V3 also feeds
  BOTH ADCs — so a clean single-island-per-rail partition of In2 is not
  geometrically achievable. In1.Cu stays the SOLID GND reference plane
  (untouched); the PWR5 0.5mm / RAIL 0.4mm .kicad_dru width floors give
  ampacity (5V trunk 1.2A on 0.5mm outer ~1.5A). Supersedes nets.yaml's
  "In2 islands" intent (the intent text is kept for provenance). GND is
  not routed: In1 plane + F/In2/B pours + stitch vias.
- D18 (2026-07-18): **board grown 176x104 -> 176x122mm** (+18mm height).
  The original 104mm height put the XU316 north-edge power+data escapes at
  4-layer capacity: the ADC↔XU316 gap was ~10mm and 2 XU316 3V3 IO pins
  (or DATA1) could not route — via sites boxed on ALL layers. The taller
  board shifts the whole digital+power cluster +16mm south (gap ~23mm) and
  widens the XU316 decoupling annulus (ring 16x14 -> 19x17mm), relieving
  the escape. Still under the XMOS reference board's 130mm. D17 width
  floors + D15 power-as-tracks unchanged.
- D17 (2026-07-18): **CLK/USB/AUDIO width floors = 0.15mm** (the fab
  capability floor). The 0.2/0.25 values were nominal targets; the
  fine-pitch XU316 escapes neck to 0.15mm, so 0.2/0.25 as a hard DRC floor
  false-failed every escape. Nominal widths stay the router's target
  (USB ~90R, series-terminated clocks); the floor is the fab minimum.
- D16 (2026-07-18): **routing waves** (canon R4, hardest escapes first):
  wave 1 = USB-HS diff pair + MCLK clock tree + I2S/TDM clock+data
  (the XU316 escapes); wave 2 = audio pairs + injection + I2C + QSPI;
  wave 3 = beeper gates + GPIO + straps + VBUS sense + debug + remainder;
  wave 4 = power rails (In2-preferred, wide). TQ128 peripheral escape is
  straight-out on F.Cu per ADR-0004 (standard tier, no advanced vias).

## DRC-cleanup + release-prep decisions (D19-D24; 2026-07-18)

- D19 (2026-07-18): **Q9 AO3401A polarity CONFIRMED CORRECT on the board** by
  a dedicated fresh-context datasheet review. The P-channel body diode is
  anode=DRAIN / cathode=SOURCE (conducts D->S); a high-side reverse guard
  therefore needs DRAIN=input, SOURCE=load. Board: pad3=DRAIN=5V_P (input),
  pad2=SOURCE=5V (load) -> CORRECT. ADR-0007 is right; the board is right.
  Two WRONG statements in 02_parts/AO3401A/part.yaml (pin-3 note "body diode
  S->D"; gotcha "SOURCE to the input, DRAIN to the load") were FIXED to agree
  with the datasheet + ADR-0007. No board change.
- D20 (2026-07-18): **DRU set to JLC 6L ACTUAL capability** (generate_rules.py):
  clearance/track 0.09 (was netclass 0.127), hole-to-hole 0.2 EDGE (was 0.5 -
  KiCad measures edge-to-edge; JLC's ~0.5 quote is CENTRE-to-centre = 0.2 edge
  for 0.3 drills; the 0.5-edge floor false-failed 13 diff-pair vias), via
  0.30/0.15 (see D21), hole-to-copper 0.2, edge 0.2. This dropped the inflated
  101-count report of manufacturable-margin items (canon golden-rule-8).
- D21 (2026-07-18): **fine-pitch escape uses JLC 6L small-via option**
  (0.30/0.15) - ADR-0009. 0.45/0.30 standard vias short the 0.4mm-pitch
  via-in-pad pair + encroach neighbours; 0.30 clears both. Cost adder flagged.
- D22 (2026-07-18): **SHT40 (U6) + barrel jack (J9) VENDORED** into cac.pretty
  to end runtime footprint edits: U6 keepout tracks/vias baked ALLOWED (was a
  runtime DoNotAllow flip -> lib_footprint_mismatch); J9 west barrel silk
  clamped inside the x=10 board edge (was 0.8mm overhang -> silk_edge). Both
  re-pointed to cac: in generate_schematic + the promoted route artifact.
- D23 (2026-07-18): **TDO escape dogbone** (route_fixups.py): TDO relocated
  out of pad 37 south into the escape channel (F.Cu dogbone + B.Cu bridge) so
  the 0.30/0.15 TDO/TDI drills clear the 0.2mm hole-to-copper floor.
- D24 (2026-07-18): **GND pad rescue** (gnd_rescue.py): boxed GND SMD pads the
  pour/grid could not thermal-reach (PCM1865 decoupling, USB-C escape) get an
  outer-edge on-pad 0.30/0.15 via (bond to In1/In4 plane) or a short F.Cu stub
  to the nearest GND via. Cut unconnected GND 15 -> 6.

## DRC status (2026-07-18) — NOT yet 0/0/0; residual is route-quality rework

Start 101 violations + 15 unconnected. After the above: **32 violations
(18 clearance sub-0.09 different-net + 14 track_dangling loose copper) + 6
unconnected GND**. All shorts, hole_to_hole, hole_clearance, lib_mismatch,
silk_edge, and the TDO/TDI pair are FIXED. The residual are KRT route-quality
artifacts (0.4mm power-rail-vs-signal tight spacing; loose escape spurs;
6 boxed GND connections) that need targeted RE-ROUTE of the affected nets
(3V3/RST_N/MCLK/5V taps + R34 GND + loose-copper trim), not floor changes or
waivers - they are genuine sub-floor items. The v1.0 release is therefore NOT
sealed at 0/0/0; see 06_build for the current gate report. Ordering is gated
on field tests regardless (ORDER_README), so this rework precedes the order.
