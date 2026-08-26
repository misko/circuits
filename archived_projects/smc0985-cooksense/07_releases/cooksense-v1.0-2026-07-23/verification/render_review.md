# Render review — smc0985-cooksense MAIN board

Fresh zero-context reviewer, clean-room from artifacts only.
Commit: 9f5c385. Date: 2026-07-23.
Artifacts judged: `04_kicad/cooksense.kicad_sch` (converter schematic, 2026-07-23 15:39,
fresh vs circuit.json 15:38), `04_kicad/cooksense.kicad_pcb` (15:42),
`03_tscircuit/build/schematic.pdf` (15:38). Renders: kicad-cli sch export svg
(rasterized 12 px/mm, all 77 occlusion sites cropped and inspected on 11 contact
sheets) + kicad-cli pcb render top/bottom overview + 6 zoom regions.

## Item 1 — S-OCCL backstop (77 converter-schematic occlusions)

**Verdict: COSMETIC-OK — zero dangerous (wrong-wire-attachment) instances in all 77.**

Method: re-derived the full 77-pair list with coordinates from the same bbox model
policy_audit uses, clustered into 65 crop windows, and inspected every window
visually at 12 px/mm.

Classification of the 77:
- ~28 pairs are bbox edge-kisses (overlap height 0.04 mm — e.g. `3V3 x Reference
  C_3V3`): invisible-to-marginal in the render. Pure noise.
- ~25 pairs are partial overlaps (label plate clips a refdes or a neighbouring
  plate by <1 mm): both texts remain legible (e.g. `5V_PROTECTED x C_COMP`,
  `SCL_RHA + 3V3_SW_RHA` side-by-side). Cosmetic.
- ~24 pairs are FULL superpositions — two global-label plates printed across the
  same 2-pin passive body, text mashed into garble. Worst instances:
  `3V3_ANALOG x TH_MOUNT_A` (R_REF1), `ADC_CH5 x TH_PORT_B` (R_SER5, reads
  "TADCORTLB"), `LC_CLK x LC_CLK_PI` (R_LCCLK, "LC_CCKCPK"),
  `TC_NEG x TC_NEG_IN` (R_TCN), `CONTACTOR_LOOP x CONTACTOR_E` (J_CONTACTOR),
  `OPTO_LED_A x CONTACTOR_REQ` (R_OPTOLED), `3V3_SW_A x SCL_A` (R_SCLA),
  `SDA_B x KEY_CLOCK` / `SCL_B x KEY_DATA` / `HOST_AUTH x TC_CS_N` (keypad-IC
  pin rows), `TEMP_OK x TH_CAM_A` (R_HYS1 node).

Why the full superpositions are still graded cosmetic, not dangerous:
1. Every label plate remains ANCHORED to its own pin/wire — in all 77 crops no
   plate's anchor lands on, or visually attaches to, a different net's wire.
   The dangerous class (label reading as owned by the wrong wire) does not occur.
2. Each plate keeps its own box outline, so a mash is self-evidently a collision
   — no mash forms a plausible-but-wrong net name a reader would trust.
3. Every mashed net was confirmed to have at least one fully legible instance
   elsewhere on the sheet (spot-verified: TH_MOUNT_B at R_REF4, ADC_CH3 at
   R_SER3, TC_POS_IN at R_TCP, ESTOP_RAW/MODE_RAW at R_*PD pulldowns,
   KEY_RELAY_ALLOWED at TP_ALLOW, SHIELD_DRAIN at R_SHIELD).

Readability cost is real: on ~24 nodes the local net names are not recoverable
without tracing. Recommended (non-blocking) converter improvement: offset the
two labels of a 2-pin passive to opposite sides of the body instead of printing
both across it.

## Item 2 — Board render sanity (252x92, 4-layer)

**(a) ANALOG SENSE label — PASS.** `ANALOG SENSE (3V3_ANALOG)` at (46.0, 64.0)
F.Silk, U_ADC at (42, 70): the text sits ~6 mm north of the U_ADC pad rows,
fully clear of all pads, complete and legible in the top render.

**(b) Functional/standalone silk vs SMD pads — PASS.** Machine check (pcbnew
exact `GetEffectiveShape().Collide`, every visible silk text — board texts,
footprint texts, refdes — vs every same-side SMD pad): **0 collisions**. Visual
sweep of both render halves concurs. (Relay body outlines over THT pads and
edge clips: waived cosmetic classes, ignored per brief.)

**(c) Polarity / pin-1 marks — PASS.** Sampled every polarized-part class in
zoom renders: CE1 electrolytic has silk `+`; D_ESTOP, D_DOOR, D_LCCLK, D_LCDAT,
D_REVCLAMP, D_ESD_IN show the cathode-side bracket; D_TVS boxed; U_OPTO has the
pin-1 notch; U_ADC, U_LATCHA/B, U_WD, U_ULNA/B, U_SCHM show pin-1 triangles;
Q_* FETs have triangle markers; all 12 reed relays (K_U1–K_U6, K_D1–K_D4,
K_PRESS, K_STOP) have square pin-1 pad + adjacent silk dot on the coil side.
No bottom-side footprints exist (bare bottom is correct).

**(d) Keypad 6 mm isolation barrier — PASS.** Rule area `iso_barrier`
(x 12–264, y 31.1–37.0, all 4 Cu layers, keepout tracks+vias+fill) plus
`keypad_iso` pour keepout. Machine scan: 0 tracks/vias overlapping the band,
0 pads inside it, 0 zone-fill vertices inside it, on any copper layer.
**Measured minimum copper-to-copper gap across the barrier: 6.12 mm**
(K_D1 pad 3 north edge 30.94 → K_D1 pad 1 south edge 37.06) — meets the
">=6mm creepage" silk claim. Renders show the clean dark band; only relay
BODIES span it (that is the isolation element); keypad matrix traces stay
north, coil drive stays south. Functional silk "KEYPAD ISOLATION ZONE
>=6mm creepage" and "D_ISO ONLY (contacts NORTH)" present.

**(e) Refdes legibility — PASS.** At 9.6 px/mm full-board render every refdes
on both halves is readable; zoom renders confirm clean de-collided placement
(no refdes-on-refdes or refdes-on-pad found). Functional silk present at
human-touch points: `5V SELV IN`, `PI 40-PIN RIBBON (SIDECAR)`, `J_PWR`,
`J_LOADCELL`, `J_KEY_MATRIX`, TP labels, board name `cooksense SMC0985KS`.

## Overall

**RENDER REVIEW: PASS.**
- Item 1: COSMETIC-OK (77/77 inspected; no wrong-attachment instances; ~24
  full-superposition mashes are readability-degrading — non-blocking converter
  improvement suggested).
- Item 2: PASS on all of a–e, with machine backstops for (b) and (d).
