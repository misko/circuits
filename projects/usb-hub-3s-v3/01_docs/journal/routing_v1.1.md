# Journal — routing v1.1 (usb-hub-3s-v3 board revision)

Revises the sealed v1.0 (07_releases/v1.0-2026-07-22/ IMMUTABLE). The working
04_kicad/usb_hub_3s_v2.kicad_pcb REGENERATES from source = the v1.1 revision.
All numbers MEASURED, reproducible via `03_src/rebuild_fast.sh` (deterministic
import of the promoted chain 03_src/route/final_chain.kicad_pcb).

## 2026-07-23 — v1.1 place + route GATE GREEN (DRC 0/0/0)

### GATE — MEASURED
- **`kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` =
  0 violations / 0 unconnected / 0 parity.** (06_build/drc/final.json)
- audit_board PASS: 16 polarity, 19 proximity, 4 edge, 119 silk.
- policy_audit: **R-THERM PASS** (EP via arrays added — v1.0 flagged U11.21 with
  1 via), R-RULES PASS, P-LAYOUT/P-ADJ PASS for in-scope parts. Residual FAILs
  are upstream/parts-metadata (see OPEN below), not board defects.
- 119 footprints = 115 parts + 4 mounting holes. Board 130x92 unchanged.

### BOARD DELTA vs v1.0 (the whole revision is the SE + input-trunk + master-off)
The v1.0 single 5VC pour ran buck-C output straight to J5. v1.1 SPLITS that path
with the protected-VBUS eFuse cell and reworks three regions:

**1. PROTECTED-VBUS eFuse cell (new, SE strip x100-128 y88-100, near J5).**
Linear west->east power flow 5VC -> Q6 -> EFINC -> U13 -> VBUSC -> J5:
- **Q6** AON6354 blocking FET [104.5,90.5,rot0]: PowerPAK SO-8, S(1-3)=5VC WEST
  (sits in the buck-C 5VC notch), D-tab(5)=EFINC EAST, G(4)=BGATEC.
- **U13** TPS26631 eFuse [113,92,rot0]: same HTSSOP-20 body as the LM5116s, so
  IN(1-3)=EFINC top-WEST, OUT(18-20)=VBUSC top-EAST, EP(21)=GND. Set pins routed
  to R30(ILIM 3.09k)/R31-R32(OVP div)/R33-R36(SHDN div)/C51(dVdT)/C52(IN byp).
- **Q7** BSS138 fast gate-pulldown [105.5,98.5,rot0] S of the Q6/U13 gap.
- **SW1** SS12D07 master-off slide [66,58,rot0] in the open board center
  (accessible); COM(2)=ENKILL, T1(1)=GND, T2(3)=NC.
- New pours (floorplan): **EFINC** (Q6.D-tab->U13.IN, small F/B pour, N-extended
  to catch C52); **VBUSC** (U13.OUT + C49/C50 + J5 A4/A9/B4/B9 + R28/R29 CC-Rp +
  U12.5; main block + 2 J5 legs flanking the pour-free CC/data column x118.2-122.3);
  **5VC landing patch** for the set-pin divider tops + Q7.S + U13.6 tap.
- Asserts added (all PASS at gen): Q6.1=5VC, Q6.5=EFINC, Q7.3=BGATEC, U13.1=EFINC,
  U13.18=VBUSC, U13.21=GND, SW1.2=ENKILL; J5.A4/A9 flipped 5VC->VBUSC.

**2. Master-off + snubbers.** ENKILL (SW1.COM -> both LM5116 EN + both 100k
pull-ups) routed by KRT (sense wave). RC snubbers R34/C53 (SNUB_A) and R35/C54
(SNUB_C) placed on each buck SW island, SW-pour + SNUB-link taps at 0.6mm
(SWITCH_NODE floor); DNP-populate.

**3. Thermal fixes (review/P2).**
- **>=4x 0.3mm GND EP via arrays under BOTH LM5116s** (measured U2=7, U11=7 GND
  vias) + U13=8. Clears R-THERM (v1.0 waived U11.21 @ 1 via).
- **VBAT_F B.Cu pour** (mirror of the F.Cu input-trunk rects [39,54,47,62] +
  [30,60.5,47,69]) + **7 F<->B stitch vias** (both B.Cu zones filled+bonded).

### ROUTING approach (canon R1: netclasses BEFORE route, generate_rules LAST)
- Pours own the power (excluded from KRT): +VBUSC, +EFINC, +SNUB_A/C added to
  the exclude list. KRT (race:6, promoted c0/r4) routes only signals: added
  BGATEC/DRVC to the gate wave; ENKILL + OVPC/DVDTC/ILIMC/SHDNC to the sense
  wave (dropped the merged-away EN_A/EN_C).
- **FB-at-connector Kelvin sense (the one hard net):** buck-C FB top R12.1 now
  sits on VBUSC but ~61mm from the SE VBUSC pour. Routed as a LAYER-escape A*
  tap (verified_astar, 2-layer, window 6) into the VBUSC west leg — the
  joinpath/via_hop taps cannot span that. Quiet run, no current.
- Deterministic taps for the pour-fed pins: U13.6 (IN_SYS sense)->5VC patch;
  the snubber SW/SNUB links; all v1.0 USB-C / USB-A / SW / 5VA-5VC taps carried.

### ITERATIONS / gotchas (D-BACK bounded, each fixed at source)
1. **SW1 footprint did not exist** (`Button_Switch_THT:SW_Slide_1P2T_CK-12D07`,
   part.yaml SPIKE). VENDORED a land pattern into a project-local
   `03_src/lib/Button_Switch_THT.pretty` (3 signal PTH @2.5mm + 2 NPTH posts).
   Reordered floorplan `libraries` (project dir FIRST) so the generated
   fp-lib-table maps the lib to the project dir -> lib_footprint_issues cleared.
   Redrew the silk (top/bottom + pin-1 dot only) to clear its own mounting posts.
2. **U2.10 (buck-A VOUT sense) tap unroutable** on this KRT roll: the pin-9
   COMP_A escape boxed the 38mm cross-buck run; even an escape-A* failed
   (via-in-pad gate). RETARGETED to R3.1 (buck-A FB-top, also 5VA, ~6mm local);
   R3.1's own tap reaches the pour. Robust across rolls.
3. **R3.1's 46mm 5VA B.Cu tap clipped a COMP_A via** (0.1337 vs 0.15). Promoted
   it to an escape A* (respects clearance) -> clean.
4. **Post-stitch via bugs** (my `03_src/post_stitch_fixes.py`, added to the
   rebuild chain after stitch): first cut dropped GND "island" vias ON connector
   GND PTH pads (already bonded) -> 6 co-located + 2 hole_to_hole, and could not
   place VBAT_F vias (removed-island chicken-and-egg + GetLayerName mislabels
   B.Cu zones as F.Cu). Fixed: skip islands already bonded by a same-net via OR
   PTH pad; enforce true hole-to-hole vs every drill; UNFILL before placing
   VBAT_F vias (via_site_ok then sees pads/tracks only, the pour voids on refill);
   read the real LayerSet. escape-A* vias came out 0.2 drill (toolkit default) ->
   drill-floor pass bumps to 0.3; KRT 0.1998 track -> nm round-up to 0.2.
- DRC trajectory: 10/1/0 -> 10/1/0 (2nd cut, different tail) -> **0/0/0**.

### OPEN QUESTIONS / residual policy (reported, not board defects)
- **BSS138 (Q7)** part.yaml: S-VER weak figure cite + P-ESC style ('passive' vs
  leaded SOT-23) + missing P-LAYOUT block. Flagged by the schematic agent as the
  one part-set deviation; parts-stage metadata, routes/DRC clean.
- **SS12D07 (SW1)** part.yaml missing a P-LAYOUT block (mechanical part; land
  figure-verify per LCSC C2939728 still open, as the part.yaml notes).
- **R-POUR flags SNUB_A/SNUB_C** (SWITCH_NODE class, no pour): a heuristic
  mismatch for DNP R-C snubber midpoints (0.6mm taps meet the floor) — waiver
  candidate, like the v1.0 pour-carried FET-drain R-THERM waivers.
- **E-OFF VBAT**: pre-existing XT60 battery-source characteristic (unchanged
  from v1.0), not a v1.1 regression.
- Loop stability with the eFuse in the FB loop + OVP no-false-trip: bench items
  carried from 03_schematic_v1.1.md (analysis says stable; unchanged here).
