# journal: placement — cooksense board

Stage 4 (BOARD placement) for the cooksense main board. Per ADR-0007 the
board-specific source lives under `03_src/cooksense/`. Author
`floorplan.yaml` -> `generate_board_generic.py` -> `04_kicad/cooksense.kicad_pcb`,
gate with `audit_board.py` + policy_audit P-ADJ/P-LAYOUT. /usr/bin/python3 for pcbnew.

## Archetype + the organizing constraint

Started from the BAND-SEPARATION archetype (references/floorplan-archetypes.md
"mixed-signal-audio-hub" / crow-recorder). ADAPTED for the dominant cooksense
constraint: the **12-relay KEYPAD ISOLATION WALL** (ADR-0001/0002, brief §4/§7).

**Geometry wall analysed first (the task's flagged risk).** Each DIP05 reed is
19.9mm courtyard on its long axis; to present ALL contacts to one isolated edge
they pack along that 19.9mm axis, so 12 reeds in a single row = 238mm — infeasible.
2 rows with contacts facing the SAME way is electrically broken (the inner row's
coils land against the outer row's contacts <6mm, and inner coil traces must cross
the keypad copper). The only clean 2-row topology is **contacts facing INWARD**:
a CENTER keypad strip, N relay row (rot270, coil NORTH / contact SOUTH) + S relay
row (rot90, contact NORTH / coil SOUTH), coils facing OUT to the two logic bands.
Consequence: the N-S logic that must join both bands (5V_KEY_RELAY, D-select,
595 cascade) crosses ONLY through the EAST corridor (x>=159), never the strip.
Reed rotations verified empirically (pcbnew): rot270=coilN/contactS, rot90=coilS/contactN.

## HAT vs sidecar — SIDECAR (justified)

Board is 154x100mm (189 parts: 12 reeds + 2 ULN + 2x595 + 2x'238 + MCP23017 +
8-ch analog front-end + safety AND-chain + Pi 40-pin). A Raspberry Pi HAT envelope
is 65x56.5 with a 58x49 hole pattern; a 154x100 board stacked as a HAT overhangs
the Pi 5 and blocks USB-C/HDMI/fan/Ethernet (brief mechanical do-not-block list).
=> **40-pin-ribbon SIDECAR** (brief: "sidecar if keepouts cannot be met"). J_PI
(2x20) sits at the SOUTH edge, mouth south, ribbon to the Pi. Board's own 4x M2.5
corner mounts (not the Pi HAT holes). Recorded in 2.54-2x20PPC104/part.yaml layout:.

## Regions (154x100, 4-layer jlc_4layer_advanced)

- NW POWER: J_PWR(W edge) -> F1 -> Q_REV -> TPS259573 eFuse(OVLO) -> 5V_PROTECTED
  -> AMS1117 3V3 -> ferrite -> 3V3_ANALOG. eFuse fine pins -> local passives + S escape corridor.
- N DRIVER: 2x595 -> 2x'238 -> ULN_A -> NORTH relay-row coils.
- NE SAFETY: HC14 + 3x AND + fault-latch + watchdog + one-shot + Q_COIL (gates 5V_KEY_RELAY),
  beside the E-edge discrete inputs (Mode/E-stop/Door).
- CENTER: KEYPAD ISOLATION STRIP (reed contacts + U/D-sel buses + RKEY/RSTOP + TPs);
  J_KEY_MATRIX = WEST peninsula (mouth W). Milled slots in the inter-reed gaps.
- S DRIVER: ULN_B -> SOUTH relay-row coils; MCP23017 (dense side -> S escape corridor).
- S ANALOG: MCP3208 + LM393 + MAX31856 + thermistor front-ends + J_THERM_A/B + J_TC
  on the ferrite-split 3V3_ANALOG rail, hugging the south edge, off the coil rows.
- S EDGE: Pi 40-pin (sidecar, mouth S) + switched sensor rails + RH connectors (E edge).

## ISOLATION realization (brief §4/§7, ADR-0001/0002)

- >=6mm creepage: measured MIN keypad-copper <-> SELV-logic gap = **7.19mm**
  (K_U6.U_SEL_BUS <-> D_DOOR.DOOR_RAW), cross-footprint (the reed's own 7.62mm
  coil/contact gap is the rated 1.5kVDC barrier, excluded). audit_board I-ISO gates it.
- Milled slots: 10 Edge.Cuts rectangles in the inter-reed gaps (x 54.5/75.5/96.5/117.5/138.5,
  N-row y46-58 + S-row y68-80) reinforcing the coil/contact boundary between adjacent reeds.
- NO planes in the zone: GND planes/pours SPLIT into N (y<=49) + S (y>=77) halves, neither
  entering the strip; a `keypad_iso` rule-area (deny pours, all 4 layers) over [16,50]-[160,76].
  audit_board I-ISO: 0 logic/GND pads inside the strip.
- NO shared GND: schematic proved 0 GND-leaks; GND touches ZERO keypad refs (netlist parse).
  GND_ISO is the J_KEY MP tabs only (netted at board-parity stage, parity_padmap.txt).

## ESCAPE CORRIDORS (D-ADJ / P-ESC)

- MCP23017 SSOP-28 (0.65mm, ~11 escapes/side): dense side faces SOUTH open copper,
  escape_corridor {U_EXP, S, 5mm} (via-in-pad at advanced tier).
- TPS259573 WSON-8 (0.5mm): escape_corridor {U_EFUSE, S, 4mm} + `efuse_escape` keepout;
  outward-only-local honoured (C_DVDT 3.6, R_OVT 5.7, R_OVB 7.3, R_ILM 8.1, R_PG 5.8mm).

## Infrastructure authored at this stage (03_src/lib + fixes)

- `cooksense.pretty/Relay_StandexDIP_1A_pinout12.kicad_mod` — cook-hub geometry,
  pads RENUMBERED 1,7,8,14 -> 1,2,3,4 to match the tscircuit `dip4` netlist
  (else check_pads_present hard-fails on K_*.2/.3/.4). DIP05 part.yaml repointed.
- `cooksense.pretty/Omega_PCC-SMP-K_TypeK_PCpin.kicad_mod` — TC jack (no KiCad stock;
  "TO BE CREATED"). 2-pad, pad1=TCP pad2=TCN. PCC-SMP-K part.yaml repointed.
- Vendored `TerminalBlock_KF350_2P` (cook-hub) — KF350 part.yaml pointed at a
  NONEXISTENT + wrong-pitch `TerminalBlock:...bornier-2_P5.08mm`; fixed to the 3.5mm part.
- AMS1117-3.3: footprint SOT-223-3_TabPin2 (3 pads) vs tscircuit sot223 (4 pads) ->
  U_LDO.4 (tab) had no board pad. Fixed CORRECTLY: wired the tsx tab pin4 -> VOUT (N3V3)
  [a floating regulator tab is a thermal defect], part.yaml -> 4-pad SOT-223, rebuilt
  circuit.json (tsci) + netlist. U_LDO.4 now = 3V3.
- 3 P-LAYOUT layout: blocks added (2.54-2x20PPC104, B5B-XH-A, X9555WV-2x16) — connectors,
  layout-agnostic, `notes:` (no keep_short).

## Iterations (measured)

1. First floorplan (90x70 attempt scaled up): generate OK after fixing YAML colon +
   `project.root: ../..` (nested 03_src/<board>/) + KF350 footprint + AMS1117 tab.
   189 placed. FAILED isolation: J_KEY + safety both crowded the strip's west
   (min keypad<->logic 2.63mm; 2 GND pads in zone).
2. Refined to 154x100: J_KEY -> W edge peninsula, safety -> NE, coil-gate -> east
   corridor. Reed rotations corrected (N=270,S=90). min gap 2.63 (C_KR/Q_COIL/U_OPTO
   still in east corridor near K_U6); GND-in-zone 2; TH_CAM_B 14.8mm.
3. Coil-gate cluster -> N band, U_OPTO -> S, analog U_COMP centred between J_THERM_A/B:
   min gap 6.05mm (DOOR cluster binding); GND-in-zone 0; TH_CAM_A 8.2, TH_CAM_B 7.9.
4. DOOR/E-stop/Mode connectors -> NE (off strip); analog tightened: min gap **7.19mm**,
   TH_CAM_A **6.0**, TH_CAM_B **7.5** (both <=8), GND-in-zone 0.
5. AND/latch decouplers switched region->near (C_AND1 was 17.5mm -> 3.0mm hard against U_AND1).
6. J_KEY -> x20 (I-EDGE W within 4mm); removed a mis-placed west-end slot that would have
   cut J_KEY<->reed keypad copper.
7. Anchor overlap sweep: coil-gate FETs lifted off relay K_U4; E-edge connectors respaced;
   U_OPTO clear of switched-rail FETs. **courtyard overlaps >0.35mm: 0.**

## FINAL GATE OUTPUT (measured)

- generate_board_generic.py: 189 footprints, 63 anchored, 33 orientation asserts passed, saved.
- audit_board.py: **AUDIT PASS** — 18 polarity, 26 proximity, 13 edge, I-ISO gap 7.19mm(>=6),
  0 strip intruders, 193 silk.
- policy_audit: **P-ADJ WAIVED** (board-wide rails 3V3 151.2mm/60pads, 5V_PROTECTED
  150.6mm/14pads; local decoupling intent honoured pad-to-pad: COUT 3.12mm, CIN 3.0mm,
  '238 bypass 4.89mm), **P-LAYOUT PASS, P-ESC PASS, P-TIER PASS, P-POL PASS, P-KEEP PASS**.
  Summary FAIL=4 / PASS=10 / WAIVED=1.
- Board: 154x100mm 4-layer; 44 Edge.Cuts segments (outline + 10 isolation slots); 0 overlaps.

## Out-of-placement-scope FAILs (other stages)

- S-VER: parts-stage datasheet figure citations (2N7002/AO3401A/... weak). Parts owner.
- R-THERM: U_LDO.4 (AMS1117 tab=VOUT) has 0 thermal vias — a ROUTE/stitch task (add
  thermal vias like the eFuse EP). Introduced by correctly wiring the tab; expected pre-route.
- E-ADR: electrical-invariants ADR coverage — schematic stage; ALSO blocked by the
  multi-board path gap (invariants live in 03_src/cooksense/rules/, policy_audit reads flat).
- M-REPRO: 03_src/cooksense/rebuild_all.sh not authored yet — pipeline stage.

## OPEN QUESTIONS / follow-ups

- **policy_audit multi-board path gap**: policy_audit.py hardcodes flat `03_src/rules/`
  + `03_src/audit_board.py`, but ADR-0007 nests them under `03_src/cooksense/`. Bridged
  with two symlinks (03_src/rules/policy_waivers.yaml, 03_src/audit_board.py -> subdir) so
  P-ADJ/P-POL/P-KEEP grade. PROPER FIX: make policy_audit resolve per-board rules dirs
  (also unblocks E-ADR/R-RULES/P-TIER reading the subdir). Backend gap — report, don't paper over.
- ULN_A->west-reed coil traces are long (~66mm to K_U1) — inherent to the 105mm reed wall;
  slow 120mA rail, acceptable, but a routing consideration (KRT fanout).
- PCC-SMP-K + KF350 footprints are cook-hub-geometry / placeholder mechanicals; Gate-1
  measurement refines the TC-jack body against the PCC-OST-SMP spec.
- Analog spine sits ~12mm S of the south reed coils (not a central firewall, since the
  2-row strip forces coils on both sides). Mitigations: ferrite-split 3V3_ANALOG rail,
  one-at-a-time reed firing, firmware sampling between key presses. Watch at review.

---

# REDO (D-BACK from routing, 2026-07-23)

Routing D-BACK (`routing_cooksense.md`) proved the 2-row center-strip floorplan
UNROUTABLE: two independent fatal defects. This redo fixes both **placement-only,
NO schematic change**.

## Defect 1 — J_PI off-board (was invisible to the audit)

J_PI (2x20, 48mm body) at old anchor [102,111,0] laid its body along +Y with
pads y111..159, but the board ended at y116 -> 34/40 pins 1..43mm OFF the south
edge. `audit_board` PASSED it because I-EDGE only measures the connector MOUTH
gap. **Added I-OUT** (pads-inside-outline, minus 0.15mm edge clr) to
`audit_board.py`; **proved it RED** on a known-bad fixture (shoved J_MODE 11mm off
the east edge -> `AUDIT FAIL, 7 pads OFF the board, exit 1`), then restored.
J_PI now rot90 (body ALONG the south edge) @ [98,95,90]: **40/40 pads on-board**,
body x98..146, south-edge gap 2.7mm.

## Defect 2 — ~26 logic N/S crossings vs ~6 corridor  =>  CONSOLIDATE (0 crossings)

Root cause: the CENTER keypad strip walled the logic into N & S; ~26 logic nets
crossed 2 sub-3mm creepage lanes. FIX per spec: **eliminate the split** — put ALL
SELV logic on ONE side. Reed geometry forces the choice: each DIP05 reed is 19.9mm
on its long (barrier-perpendicular) axis, so a single coils-one-side row of 12 is
~239mm wide; a 2-row band ALWAYS re-splits one domain (verified: contacts-inward
=> coils split N/S; both-coils-south => the mid-band interleaves keypad/logic).
The only zero-crossing topology is a **single reed row**, so the board is GROWN
(spec: "GROW rather than re-split").

New topology (**252 x 92 mm**, was 154 x 100):
- **NORTH (y<34)** = keypad domain ONLY: J_KEY_MATRIX (W peninsula) + reed
  CONTACTS + U/D-sel buses + RKEY/RSTOP. Isolated, GND_ISO only, no plane.
- **REED BAND (y29..39)** = 12 reeds in ONE row @ **rot90** (empirically
  coilS/contactN; verified K_D1 pad3 y30.2 contact / pad1 y37.8 coil), pitch 20mm,
  x28..248. Order U1..U6,D1,D2 | D3,D4,PRESS,STOP so ULN_A (reeds 1-8) & ULN_B
  (reeds 9-12) sit contiguous just south of the coils. 11 milled inter-reed slots.
- **SOUTH (y>40)** = ALL logic: power (SW) -> drive chain 2x595->2x'238+1G123->
  ULN_A/ULN_B -> coils (center) ; MCP23017 + TPS3823 + J_PI (center-S) ; HC14 +
  AND-chain + fault-latch + Q_COIL (E, by the discrete inputs) ; analog spine
  MCP3208/LM393/MAX31856 + switched rails A/B (SW) ; RH rails (SE).

Both ULN_A and ULN_B are now SOUTH; every reed coil faces south; NO ULN channel
reassignment -> **schematic UNCHANGED** (ULN_A still drives U1-6,D1,D2; ULN_B
D3,D4,PRESS,STOP; netlist byte-identical).

## Iterations (measured)

1. New floorplan (single row, all-logic-south, 252x92). Generate FAILED: added
   body_offset asserts on J_TC/J_LOADCELL/J_PI — SYMMETRIC parts (body centroid ==
   pad centroid), offset +0.00 => always fail. Removed those 3 (kept the
   asymmetric side-entry ones J_THERM_A/B, J_RH_A/E->y+, J_MODE/ESTOP/DOOR).
   Re-gen: 189 placed, 33 asserts pass, 119 legalized.
2. Audit: I-OUT caught **J_PWR.MP 3.0mm off the west edge** (Micro-Fit MP pad);
   I-PROX **C_LDOOUT 11mm from U_LDO** (crowded corner). Fixed: J_PWR ->[22,48],
   LDO locals -> `near U_LDO`.
3. P-CRT = **12 courtyard findings**. Causes: (a) J_PI courtyard extends +50mm
   EAST of its anchor -> overlapped J_LOADCELL; re-anchored J_PI 122->98. (b) the
   B5B-XH THT J_LOADCELL had its D_LC*/R_LC* locals on its pads (8x pth_inside_
   courtyard + shorts); moved J_LOADCELL ->182, reseeded locals clear north.
   (c) anchored power parts too close (J_PWR/U_LDO, D_REVCLAMP/F1); respaced from
   measured courtyards. => **P-CRT 12 -> 0**.
4. 2x items_not_allowed: R_EXPRST & D_TVS sat in the U_EXP / U_EFUSE S escape
   corridors. Moved R_EXPRST W of U_EXP, D_TVS S of the eFuse escape. => **0**.
5. P-SILK-FN: F1 lost its functional caption (I'd moved "5V SELV IN" >8mm).
   Repositioned caption to [39,42] (4.5mm from F1). => PASS.

## FINAL GATE (measured, on 04_kicad/cooksense.kicad_pcb)

- **audit_board.py: AUDIT PASS** — 18 polarity, 26 proximity, 13 edge, **I-OUT
  all pads inside (tightest 0.35mm)**, **I-ISO 8.98mm (>=6)**, 0 strip intruders,
  193 silk. (I-OUT proven RED on a known-bad fixture.)
- **N/S isolation crossings: LOGIC = 0, KEYPAD = 0** (corridor cap ~6). 0 logic
  pads north of the boundary, 0 keypad pads south, 0 GND pads in the keypad zone,
  0 copper pours enter y<39 (isolation held by construction).
- **policy_audit: P-LAYOUT PASS, P-ADJ WAIVED** (same board-wide-rail budget
  waiver as v1: 3V3/5V_PROTECTED/TH_CAM spans geometrically unreachable),
  **P-CRT PASS (0 courtyard), P-ESC/P-TIER/P-POL/P-KEEP/P-SILK-* PASS**.
- kicad-cli DRC --severity-error = **0**; --severity-all = 104 (ALL silk
  warnings: silk_over_copper 50 / silk_edge_clr 48 / overlap 4 / thick 2 —
  cosmetic, resolved at fab silk-finalization) + 372 unconnected (unrouted).
- J_PI **40/40 pads on-board**. Board 252 x 92 mm, 4-layer, 48 Edge.Cuts items
  (outline + 11 isolation slots), 4 M2.5 holes.
- PRESERVED: >=6mm creepage (8.98), 11 milled slots, keypad_iso deny-pours (no
  plane in band), no GND_ISO<->GND bridge, MCP23017 (esc_U_EXP_S) + TPS259573
  (esc_U_EFUSE_S) escape corridors, AMS1117 tab U_LDO.4=3V3 + eFuse EP U_EFUSE.8=GND.

## Out-of-placement-scope FAILs (unchanged, other stages)

S-VER (parts datasheet citations), R-DRC (unrouted: 372 unconnected + silk
warnings), R-THERM (U_LDO.4 tab thermal vias — route/stitch), E-OFF (ADR-0006
de-energization — schematic), M-REPRO (rebuild_all.sh — pipeline). None are
placement defects.

## Note for the shared-checker harvest

I-OUT (pads-inside-outer-outline, minus edge clr, with a known-bad fixture) is the
guard that would have caught this D-BACK. It checks the OUTER outline only; pad-in-
milled-slot clearance is left to DRC copper_edge_clearance. Harvest-ready.

## 2026-07-23 21:40 — start (v1.1 repack) + stuck (pre-build wall)
- did: v1.1 shrink commission (D7): relay row pitch 20 -> 15.24mm, single-row
  topology kept, outline 252x92 -> ~195x92. Before touching floorplan.yaml,
  MEASURED the relay footprint (03_src/lib/cooksense.pretty/
  Relay_StandexDIP_1A_pinout12.kicad_mod) against the proposed pitch.
- result: INFEASIBLE, mechanically, pre-build. At rot90 (the orientation the
  single-row barrier REQUIRES: contacts N y-3.81 / coils S y+3.81), the body
  long axis lies ALONG the row: body 19.3mm, courtyard 19.90mm (fp_line CrtYd
  +-9.95), pads x+-7.62. 15.24mm pitch => adjacent courtyards overlap 4.66mm,
  bodies 4.06mm — parts collide. v1.0's 20mm pitch already leaves 0.10mm
  courtyard gap (0.70mm body gap holding the 0.6mm milled iso slot): ZERO
  pitch shrink available in this orientation at ANY legal pitch (~20mm min).
  The part.yaml "15.24mm super-column pitch" is COUPLING evidence from the
  old vertical-column layout (rot0, 6.5mm across the pitch axis) — it was
  never a rot90 fit claim. rot0 relays at 15.24mm would fit but put both
  contact pads on one vertical column (y+-7.62 per relay), destroying the
  straight keypad barrier (I-ISO >=6.0mm) the scope mandates keeping.
- next: STOP per the commission guardrail (not a routing wall — no rebuild
  changes a courtyard). User decision required: (a) accept ~no shrink at
  single-row (only edge-margin trims, ~252 -> ~246 x 92 best case), (b)
  bench-measure the coupling (U+D+PRESS triple energize, physical v1.0
  boards) to license the two-row repack, or (c) vertical-relay topology
  redesign (new barrier concept). D7 records the escalation; no floorplan,
  netlist, or 04_kicad change made; v1.0 release untouched and orderable.
