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

- D25 (2026-07-18): **power-neck exemption at unroutable approaches**
  (neck_approaches.py + generate_rules.py 'pwr_neck' scoped DRU rules). The
  18 residual clearance items were corridors where the netclass floor width
  + 0.09mm physically cannot fit: (B) the 0.50mm 5V trace at the AP61102
  SOT-563 0.5mm-pitch GND pad (U10/U11), (A) the 0.40mm 3V3 east-central
  trunk parallel to the RST_N/MCLK_B/I2C escapes (F.Cu + In3.Cu), (C) the
  3V3 tap at the MCLK_A escape near R61. Fix: DRC-guarded local neck to
  0.20mm with a named 'pwr_neck' rule area over exactly the necked copper
  (same scoped-width pattern as 'xu316_taps'; DRU floor 0.15 inside).
  Ampacity margin (1oz outer, IPC-2152 ~0.65A at 10C rise for 0.20mm):
  5V per-buck VIN branch <=0.45A on <1mm necks; 3V3 trunk <=0.40A -> ~3.8C
  rise even on the longest ~16mm neck. Floors remain backstops; trunks
  still ride In2 islands/pours. Cleared all 18 (29->11 violations).
- D26 (2026-07-18): **trim_dangling rewritten subprocess-per-edit with a
  clip-to-anchor fallback**. Repeated pcbnew.LoadBoard in one process hits
  SWIG wrapper corruption -> each removal/clip now runs in a fresh python
  child. 10 of the 11 dangling spurs were LOAD-BEARING KRT through-pin
  routes (the track crosses its TSSOP/TQFP pad mid-segment and overshoots;
  whole-segment removal orphans the pad — guard proved it): fix is CLIPPING
  the dangling end back to the covered pad center (or, VB3P, to a
  tangentially-grazed same-net via center, solidifying a 0.21mm-off-axis
  marginal connection). 1 pure spur removed + 10 clipped -> dangling 0.

- D27 (2026-07-18): **two JLC-stock-0 lines sourcing-substituted** (bom_seed
  tier-1 remap; evidence part.yamls committed): Y1 FA-238 C2650433 -> YXC
  X322524MOB4SI C70590 (same 3225-4P land, SAME CL 12pF — USB clock
  unchanged — tighter +-10/+-20ppm, stock 111k); U12 TCR2LF18 C150173 ->
  TI TLV70018DDCR C79924 (SOT-23-5, identical IN/GND/EN/NC/OUT winding,
  1.8V/200mA, stock 5.2k). Both independently confirmed by the release
  fresh-context pin review (U12/Y1 reviewer: PASS/PASS from TI SLVSA00E +
  YXC YSX321SL primary sources). C90 100u bulk resolved to RYVP6.3V100UF4*5
  C48970904 (exact CP_Elec_4x5.4 land, 6.3V = 79% derating on 5V).
- D28 (2026-07-18): **RJ45 5V/GND contact map — BOARD CORRECT, part.yaml
  doc was wrong** (Q9-class doc error, caught by the fresh-context J1-J6
  pin review). The pod v1.0 (SEALED, git 17ceffe) terminal map J1: 4=5V,
  5=GND, 7=5V, 8=GND — each of the blue/brown pairs carries feed+return
  ("paralleled" in P4 = the two pairs parallel each other). The central
  board matches the pod contact-for-contact on all six jacks. The
  02_parts/RJHSE-5384/part.yaml notes (which claimed 4+5 both 5V, 7+8 both
  GND — a reading that would put split-pair DC on no conductor pair and,
  worse, mismatch the sealed pod) are FIXED. Shield: SH pads tie to GND at
  central (single-point star bond; pod side leaves SHIELD floating with a
  DNP bond R15) — deliberate.

- D29 (2026-07-18): **functional silkscreen labels generated**
  (add_silk_fn.py, chained after trim_dangling; canon P5 / P-SILK-FN).
  The board had every functional word on F.Fab only (unprinted): unmarked
  5V barrel jack, anonymous debug/injection headers, unlabeled PTCs/TPs —
  the exact fleet-audit failure class. The stage stamps each J/F/TP ref's
  VALUE ("DC-005 5V IN", "2A PTC", "TP 5V", "xSYS DBG TDI/TDO", ...) on
  F.Silk, collision-aware (body-only obstacle model; short-label fallback
  "PTC" in the dense port clusters), DRC-guarded, idempotent. 32 labels;
  P-SILK-FN PASS; DRC stays 0. Also: audit_board gains I12
  (mate-direction: RJ45 row north / barrel west / USB-C south within
  4.0mm of their edges — RJHSE bodies legitimately sit 3.5mm back; M3
  screw-head keepout ring 3.2mm at H1-H4) closing policy P-KEEP.

## DRC status (2026-07-18) — GATE GREEN 0/0(waived-2)/0

Start 101 violations + 15 unconnected. After D19-D24: 32 violations + 6
unconnected. After D25 (neck) + D26 (trim/clip): **0 violations, 0 parity,
and exactly the 2 ADR-0010-waived `Zone [GND] <-> Zone [GND]` micro-sliver
unconnected items** (fill-engine artifact; zero electrical impact — every
one of the 234 parts' GND pads is bonded; evidence in ADR-0010). The fixed
board is baked into the promoted route artifact 03_src/route/final.kicad_pcb
(canon M3); rebuild_all.sh re-verifies with the guarded stages as no-ops.
Ordering remains gated on field tests (ORDER_README).
