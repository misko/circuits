# journal: 03 schematic — cooksense (A+B-merged main board)

## 2026-07-22 — start (schematic stage, cooksense board)
- did: entered the schematic stage for the `cooksense` board (ADR-0007 per-board
  layout). Read the whole design intent: BRIEF (Rev 1.0 + D1-D6), ARCHITECTURE,
  ADRs 0001-0007, all 36 `02_parts/*/part.yaml` verified pin maps, the tscircuit
  authoring idiom (examples/tsx-backend-proof + converter + 03_tscircuit contract),
  and the 6 design flags from 02_parts.md.
- plan: author `03_tscircuit/src/cooksense.tsx` (full net architecture per
  ARCHITECTURE.md, 7 functional blocks) + `03_src/cooksense/rules/{power_tree,
  nets,electrical_invariants}.yaml`; iterate to ERC 0 + refdes parity; resolve the
  6 flags in-schematic; apply the coordinator's decoder fix ('138/'139 -> '238).
- result: pending authoring.
- next: de-risk multi-pin footprint tokens, then author.

## 2026-07-22 — decoder fix + SN74HC238 part added
- did: confirmed the coordinator's flagged decoder bug is REAL — the brief's
  SN74HC138/'139 are ACTIVE-LOW one-hot; the ULN2803 coil driver is ACTIVE-HIGH
  input, so an active-low one-hot would energise 7-of-8 coils and leave the
  SELECTED one OFF (would short 5 keypad U-lines instead of connecting the one
  selected). FIX = two SN74HC238 (pin-compatible ACTIVE-HIGH 3-to-8): one for the
  6 U-selects (Y0-5), one for the 4 D-selects (Y0-3, A/B only, C tied GND).
- result: SN74HC238 verified JLC-stocked (JLCPCB parts search 2026-07-22: 2671u
  @ ~$0.165 + a 452u listing; onsemi MC74HC238ADR2G alternate). MEASURED escape:
  `escape_check --style leaded --pitch 1.27 --pins 16 --escapes-worst-side 8` ->
  tier_required jlc_2layer_default (unconditional, same as the '138 it replaces).
  Created `02_parts/SN74HC238DR/part.yaml` (pinout from the TI D2804 FIGURE p.2-299,
  function table p.2-301 confirms active-HIGH; datasheet PDF committed, sha256'd).
  Updated ADR-0002 (Amendment section) + ARCHITECTURE.md.
- OPEN: the exact genuine-TI LCSC C-code could not be extracted (LCSC/EasyEDA/JLC
  parts APIs unreachable in-sandbox); part.yaml carries `lcsc: ""` + the stock
  evidence + the onsemi alternate, flagged for order-time fill. Stock IS confirmed.
- next: author the board.

## 2026-07-22 — token de-risk (avoid the silent-drop trap)
- did: probed every uncertain tscircuit footprint token BEFORE authoring 189
  parts (canon TSX-PRE: tscircuit drops a part SILENTLY if the token yields 0 pads).
- result (MEASURED pad counts): WORKING = pinrow2/5/8/10/40, soic8/14/16/18w,
  ssop8/28, tssop14, dfn8, dip4, sop8, 1812. FAILING (0 pads -> would drop) =
  sc70_5, sot353, sop4, wson8, idc2x16. Mappings chosen: SC-70-5 (1G00) -> `sot23_5`;
  WSON-8 (eFuse) -> `dfn8` (EP handled at board); SMDIP-4 opto -> `dip4`. The DIP05
  reed relay has NON-contiguous real pads (1,7,8,14): a `<footprint>` child created
  3 phantom ports (converter emitted 1,2,3,4), so authored on `dip4` (clean pads
  1-4) with the 2->7/3->8/4->14 remap recorded in parity_padmap.txt for the board
  stage (schematic gate = ERC + refdes parity, which do NOT bind pad names).
- next: author + gate.

## 2026-07-22 — full board authored, ERC + parity CLEAN (all 7 blocks)
- did: authored `cooksense.tsx` — 189 electrical components (+4 mounting holes),
  all 7 ARCHITECTURE blocks. Every pin bound to an explicit `net.<NAME>` (parity by
  construction); leading-digit rails N-prefixed; specialty parts carry
  supplierPartNumbers so the converter resolves the FPID from 02_parts. Emitted the
  three rules YAMLs + manifest.yaml + parity_padmap.txt. One fix mid-gate: J_PI
  (Pi 2x20) had an empty FPID (pinrow40 not in the commodity map) -> added
  supplierPartNumbers C35165 -> 189/189 FPID.
- result — MEASURED gate outputs:
  - `tsx_preflight.py`  -> TSX-PRE: all multi-pin pad names tsx-safe or mapped
  - `tsci build`        -> 1 passed, 189 source_components, 0 dropped, 0 auto-named nets
  - converter           -> 189 components (189 with FPID), 675 pins, MODE=layout WIRED
  - `kicad-cli sch erc --severity-all` -> **0 ERRORS**, 1154 warnings (all baselined
    classes only: endpoint_off_grid 653, footprint_link_issues 189, lib_symbol_issues
    310, isolated_pin_label 2)
  - `count_parity.py`   -> ok circuit.json == kicad_sch == netlist == manifest (**189**)
  - `electrical_invariants.py` -> **E-INV OK: 13/13 invariants hold**
  - `--adr-coverage`    -> **E-ADR OK** (protection/topology ADRs 0001, 0002, 0006 all cited)
  - `power_topology.py` -> **E-TOPO N-A** (no switching converter — the intended all-linear verdict)
  - ISOLATION cross-check (parser): 14 keypad-domain nets (KP_U1-6, KP_D1-4,
    U_SEL_BUS, D_SEL_BUS, RKEY_MID, RSTOP_MID), **0 GND-node leaks** -> galvanically
    isolated by construction; GND is a separate 120-node net.
  - Safety-chain node check: 5V_KEY_RELAY feeds all 12 coils + both ULN COM only via
    Q_COIL.3; KEY_RELAY_ALLOWED = U_AND3.4; TEMP_OK = LM393 wired-AND (U_COMP.1+.7 +
    pullup); WD_OK gates U_AND1.3 + the 595 OE NAND; PRESS_TIMED = one-shot Q -> ULN.
- next: journal the 6-flag resolution (below); report. NOT committing (main loop serializes).

## 2026-07-22 — the 6 design-flag resolutions (in the schematic)
1. **Watchdog timing.** TPS3823-33 (U_WD) wired as the COARSE ~1.6s brown-out/heartbeat
   supervisor: RESET_N(1)=WD_OK feeds the AND-chain, /MR(3) debounced+tied high, WDI(4)=
   WD_PET (Pi GPIO17 heartbeat). The FAST <=500ms PRESS timeout is the SN74LVC1G123
   one-shot (U_ONESHOT): B(2)=PRESS_REQ edge, Q(5)=PRESS_TIMED (~390ms, R_OS 390k * C_OS
   1uF) -> the K_PRESS ULN input. The fast path is on the 1G123, NOT the '3823. ✓
2. **eFuse OVLO.** TPS259573 (U_EFUSE, the x3 programmable-OVLO die C2653844) wired with
   the OVLO divider R_OVT(100k)/R_OVB(15k) on EN_OVLO_N(2) = true over-voltage CUTOFF
   (~5.5-6V). FLT_N(6) open-drain -> PWR_GOOD_N (pullup R_PG, read by expander). Fault
   mode noted: TSD is AUTO-RETRY (hiccup), not latch-off (part.yaml gotcha) — accepted
   for a SELV input. E-INV asserts the OVLO divider exists (net_has_part EF_OVLO >=2 R). ✓
3. **MCP23017 pin 12 = SCL.** U_EXP pin12 wired to I2C_SCL (NOT SCK). Pins 11 & 14 left
   as NC (not wired) — the converter emits no_connect flags, ERC-clean. ✓
4. **Decoder unused half / one-hot.** Decoders are the ACTIVE-HIGH '238 (fix above).
   U_DECU: /G2A(4)=/G2B(5)=GND (enabled), G1(6)=DECU_G1 (595 enable), Y6/Y7 = NC.
   U_DECD: only A/B used for 4 outputs -> C(3)=GND, /G2A=/G2B=GND, Y4-Y7 = NC. (The '139's
   "unused-half /G->VCC, A/B->GND" rule is moot after the '138/'139 -> '238 swap; the
   unused '238 outputs are simply left NC, and every unused select input is tied GND.) ✓
5. **AND-chain gates the coil rail.** All 7 conditions AND'd through 3x SN74LVC1G11:
   U_AND1=MODE_AUTO_HW·WD_OK·ESTOP_OK, U_AND2=TEMP_OK·MCU_RELAY_ENABLE·HOST_AUTH,
   U_AND3=AND1·AND2·FAULT_LATCH_CLEAR -> KEY_RELAY_ALLOWED. Drives the coil rail via the
   Manual/Auto DPDT pole A (COIL_EN, physical MANUAL cut) -> Q_COILDRV(2N7002) ->
   HS_GATE_COIL -> Q_COIL(AO3401A high-side) -> 5V_KEY_RELAY. ANY false = coil rail dead.
   Secondary interlocks: SN74LVC1G00 NAND(MCU_RELAY_ENABLE,WD_OK) = 595 /OE; SN74HC14
   Schmitt cleans ESTOP/MODE/DOOR; a 2nd 1G00-pair SR latch (set by WD_OK·ESTOP_OK fail,
   cleared by REARM_N) = FAULT_LATCH_CLEAR. E-INV series_chain proves the rail is
   reachable ONLY through Q_COIL. ✓
6. **Keypad isolation domain.** The reed CONTACT side (tsx pads 3/4 = real 8/14) carries
   KP_U1-6/KP_D1-4 + U_SEL_BUS/D_SEL_BUS/RKEY_MID/RSTOP_MID -> J_KEY_MATRIX (SM10B-GHS,
   isolated); the COIL side (pads 1/2) is on the SELV rail. MEASURED: 0 GND-node leaks
   across the 14 keypad nets. GND_ISO (the isolated connector MP tabs) lands at the board
   stage (parity_padmap). ✓

## 2026-07-22 — OPEN QUESTIONS / board-stage carry-forward
- DIP05 relay pad remap (dip4 1,2,3,4 -> real 1,7,8,14) + eFuse EP(9)=GND +
  JST/Micro-Fit MP tabs -> GND/GND_ISO: all documented in parity_padmap.txt; bind at
  the board stage (generate_board / footprint load). NOT a schematic-gate issue.
- SN74HC238DR genuine-TI LCSC C-code to be filled at order (stock confirmed, code
  unfetchable in-sandbox). onsemi MC74HC238ADR2G is the confirmed drop-in alternate.
- Shared-library parts NOT placed on cooksense (documented, not stale): AQY212GS
  (PhotoMOS selector ALTERNATE, ADR-0006 — reed is the default), X9555WV-2x16 IDC
  (cook-hub-era 32-pin patch / B2 per-key fallback — the matrix-selector cooksense
  uses SM10B-GHS for the 10-line isolated J_KEY_MATRIX), and the now-unused
  SN74HC138DR/SN74HC139DR (superseded by the '238 fix).
- Pi 40-pin GPIO<->function pin-mux (incl. the 4 sensor-I2C dtoverlay assignments,
  ADR-0004) is assigned sensibly in the schematic but the exact dtoverlay feasibility
  is the Gate-4 pin-map artifact, not schematic-gate scope.

## 2026-07-24 13:45 — start (v1.2 electrical correction)
- did: v1.2 commissioned (BRIEF D10) from the external v1.1 review, user scope = priorities 1-7. Verified the Pi5/RP1 I2C function table MYSELF (RP1 DS RP-008370 fsel table + raspberrypi/linux i2c2/i2c3-pi5 overlay dts + rp1.dtsi): GPIO2/3=I2C1, GPIO4/5=I2C2 SDA/SCL, GPIO14/15=I2C3 SDA/SCL; GPIO16/18/19/24/26 have NO I2C alt. Reviewer's proposed map CONFIRMED valid. Authored ADR-0010 (pin map — RESTORES the brief §3 verbatim two-shared-bus plan; the sealed 4-bus wiring was an undocumented deviation), ADR-0011 (safety chain ×6 fixes), DETAIL_DESIGN.md (threshold + one-shot math), pin_map.md (maintained artifact + dtoverlay snippet), 02_parts/CD74HC221M96 (non-retriggerable one-shot, LCSC C133954, stock 2542, DS sha 30c3cd71). tsx edited: TEMP_OK into latch set; contactor HW gate (U_CAND1/2); K_STOP on new 5V_STOP rail + dedicated driver; STOP preemption (STOP_REQ direct GPIO26, STOP_REQ_N gates on decoder enables + one-shot clear); U_SR2 deleted; KEY_LATCH freeze gate; 68k/10k threshold (74.9C, solder-select field) + TP_TCTH; RH pods joined cam buses, 4 RH pullups deleted; 9 deterministic pulls. manifest 191→215. E-INV: +45 assertions citing 0010/0011.
- result: docs + source authored; gates not yet run.
- next: gen_tscircuit + ERC + parity + E-INV + count_parity.

## 2026-07-24 13:45 — v-NEXT deviations journaled (coordinator directive, NOT in v1.2 scope)
- did: recorded two brief-vs-implementation deviations surfaced while rewiring the buses.
- result: (1) BRIEF §3 verbatim: "Per bus: selectable 2.2k/4.7k pullups (default OFF with Adafruit onboard 4.7k); 22-33R damping; low-C ESD" — the board has FIXED 2.2k pullups, no series damping, no ESD array on the sensor buses (reviewer items 9/10, user scoped OUT of v1.2; DNP-selectable pullups are NOT zero-cost in this pipeline — BOM/CPL/twin all key on populated parts — so not smuggled in). (2) BRIEF §3 "Watchdog 300-500ms" vs fitted TPS3823-33 ~1.6s (reviewer note): needs an explicit user decision — accept 1.6s formally or change part.
- next: both need a D# disposition at the next commissioning touch; carried in ORDER_README as known deviations.
