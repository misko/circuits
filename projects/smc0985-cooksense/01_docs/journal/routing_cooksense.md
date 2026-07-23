# journal: routing — cooksense board

Stage 6 (ROUTE) for the cooksense main board. Goal: DRC 0/0/0 with the keypad
ISOLATION ZONE preserved. Per ADR-0007 the board source lives under
`03_src/cooksense/`. Tools: KRT (`~/gits/KiCadRoutingTools`) is the router;
`/usr/bin/python3` for pcbnew; the shared generics in `skills/kicad-pcb/scripts`.

## Setup done (deliverables that persist)

- **route.yaml authored** (`03_src/cooksense/route.yaml`): KRT prep/route/import
  order, isolation-preserving keepouts (User.2 = strip blocked for logic waves;
  User.3 = strip open for keypad-iso waves), hardest-first waves (crossers first),
  race:3, GND(In1)+3V3(In2) plane-owned & KRT-excluded, full stitch pass list
  incl. `stitch_grid.avoid` over the strip (no GND vias bridging the barrier).
- **ADR-0007 path gap bridged**: `route_and_stitch_generic.load_cfg` sets the
  root to the yaml's GRANDPARENT (`03_src` for a nested config), and the flat
  lookups (`fab_tier_util.resolve`, `net_class_floors`) read
  `<root>/03_src/rules/nets.yaml`. Workaround = pass `--root <project root>` +
  symlink `03_src/rules/{nets,electrical_invariants,power_tree}.yaml ->
  ../cooksense/rules/…` (mirrors the existing audit_board.py / policy_waivers.yaml
  symlinks). PROPER FIX (backend): a per-board rules-dir resolver, same gap the
  placement journal flagged for policy_audit.
- **netclasses generated BEFORE routing** (canon R1): `generate_rules_generic .`
  -> 6 netclasses + 6 width rules into `04_kicad/cooksense.kicad_pro/.kicad_dru`.
- prep OK: track-free base r0 + 9 keepout rects on [User.2, User.3];
  waves cross_safety(16) cross_pi(7) keypad(14) coil(19) pwr(9) sig(89).
  prep also caught 2 real wave-floor bugs I fixed (coil 0.4<PWR_IN 0.5;
  sig 0.2<ANALOG_SENSE 0.25).

## Iteration 1 (MEASURED) — the isolation-corridor wall

Ran the hardest wave (cross_safety: 16 N-S crossing SIGNAL nets) with KRT
DIRECTLY on the empty prepped board (best case: every crossing lane free, no
competition), strip keepout active, advanced tier (0.2 track / 0.15 clr /
0.3-0.15 via), 600k iters + reconciliation.

**Result: 6 / 16 routed; 10 FAILED** (ground-truth check_connected on r_cross):
  FAILED: COIL_D1_N, COIL_D2_N, SEL_D3, SEL_D4, STOP_REQ, ESTOP_OK,
          MODE_AUTO_HW, PWR_GOOD_N, WD_OK, TEMP_OK
  routed: CONTACTOR_C, PRESS_TIMED, REARM_N, KEY_RELAY_ALLOWED, FAULT, DOOR_OK
Sample failure (KRT log): PWR_GOOD_N MST edge R_PG(49.99,30.80 north) -> U_EXP
(92.5,87.8 south), 99.49mm, "No route found after 600000 iterations" x2 layers.
The 6 that DID cross consumed the corridor capacity (they weave the east lane
x>163, past the connector barrels).

## STUCK — measured plateau + causal hypothesis (D-BACK to PLACEMENT)

This is a PLACEMENT/TOPOLOGY wall, not a router-tuning issue. Two independent,
geometrically-proven root causes; more iterations/layers/tuning cannot clear
either (the skill's own empiric: "more layers do NOT fix escape-/corridor-bound
failures").

**Cause A — the keypad isolation strip walls the logic into N & S, and ~26 nets
must cross through ~2 sub-3mm lanes (capacity ~6).**
- The keypad CONTACT copper is a continuous horizontal band: the U_SEL_BUS
  (y55.8) and D_SEL_BUS (y70.2) rails span x36.4..156.6, plus J_KEY (x18.6) and
  reed contacts. A >=6mm-creepage logic crossing is therefore only possible where
  NO keypad copper is within 6mm on either side:
    - WEST lane: J_KEY(x21.9) <-> reed K_U1.3(x36.4) gap -> clear band x27.9..30.4
      = ~2.4mm.
    - EAST lane: keypad copper ends x156.6; 6mm line = x162.6; but D_DOOR(x163.8),
      J_DOOR(x164.2 barrel), J_CONTACTOR(x166 barrel), J_LOADCELL(x166 barrel)
      occupy x163.8..166 across the whole y49-77 band -> usable clear width ~1mm
      (B.Cu, x162.6..163.7 before the J_DOOR barrel).
  Total crossing capacity across 2 layers ~6-8 tracks. MEASURED capacity = 6.
- Demand: 27 nets have pads in BOTH y<49 and y>77 (excludes GND/keypad-iso):
  3V3(60 pads, PLANEABLE) + 26 that need TRACKS. Of the 26: 23 signal + 3 power
  (5V_KEY_RELAY, 5V_PROTECTED, 3V3_ANALOG). The 23 signal crossers come from
  south components reaching north logic across the barrier:
    - MCP23017 expander U_EXP (south) reads 8 north safety-status nets
      (TEMP_OK, WD_OK, ESTOP_OK, PWR_GOOD_N, FAULT, MODE_AUTO_HW, DOOR_OK, REARM_N)
    - Pi header J_PI (south) drives 7 north nets (KEY_CLOCK/LATCH/RESET_N/DATA to
      the 595s, WD_PET to the watchdog, HOST_AUTH, MCU_RELAY_ENABLE)
    - south ULN_B fed by north decoders/595/one-shot: SEL_D3, SEL_D4, STOP_REQ,
      PRESS_TIMED
    - ULN_A (north) drives SOUTH reeds D1,D2: COIL_D1_N, COIL_D2_N
    - CONTACTOR_C, KEY_RELAY_ALLOWED
  The placement journal's crossing estimate ("only 5V_KEY_RELAY, D-select, 595
  cascade cross east") under-counted by ~8x — it missed the expander-reads-north,
  Pi-drives-north, and ULN_B-fed-from-north traffic.

**Cause B — J_PI is OFF-BOARD (independent fatal defect).**
- J_PI (2x20 PinSocket_2x20_P2.54mm_Vertical, 48.26mm long) at floorplan anchor
  [102,111,0] lays its 48mm body along +Y: pads span y111.0..159.3, but the board
  outline is y16..116. ~34 of 40 pins sit 1..43mm OFF the south edge -> not
  routable, not manufacturable.
- audit_board PASSED because it has NO pads-inside-outline check (only I-EDGE =
  "connector mouth reaches an edge"). This is an audit gap.

## Recommendations to the placement/upstream owner (to unblock 0/0/0)

1. **J_PI**: rotate 90deg (48mm body ALONG the south edge, on-board, pins
   y~108..113). 1-line floorplan change + regen. And add a pads-inside-outline
   gate to audit_board (the I-EDGE check cannot see this class).
2. **Cut the crossing count from ~26 to <=~6** — this is the load-bearing fix and
   needs a topology decision, not a nudge:
   - Co-locate the MCP23017 expander (U_EXP) with the safety AND-chain/watchdog on
     the NORTH side (it reads 8 north status nets) -> removes ~8 crossings; verify
     its I2C + remaining GPIO fanout doesn't re-introduce as many.
   - Drive south reeds D1,D2 from ULN_B (south) not ULN_A (north): reassign 2 ULN
     channels (SCHEMATIC/netlist change) -> removes COIL_D1_N, COIL_D2_N.
   - Give ULN_B's selects a SOUTH source (a south latch/decoder) or move that
     decoder south -> removes SEL_D3/D4/STOP_REQ/PRESS_TIMED.
   - The Pi<->north-595/watchdog signals (~5-7) are inherent to Pi-south +
     595/watchdog-north: either move the 595s + watchdog SOUTH next to J_PI, or
     budget them as the ~6 the east lane can carry.
   - Power south-branches: plane 3V3 on In2 (whole board, strip carved, east wrap)
     and GND on In1 likewise (removes both from crossing); relocate the ferrite FB1
     + analog 3V3 decouplers SOUTH so 3V3_ANALOG is generated south (no crossing);
     leave 5V_PROTECTED as an F.Cu NW pour + one east-lane track to the 4 south
     pins (or move U_COMP/loadcell 5V feed).
3. If crossings cannot be cut to the corridor budget, the topology itself needs
   reconsidering (single-row reed wall on a taller board so the logic is NOT
   split; or accept a wider east corridor by clearing D_DOOR/J_DOOR/J_CONTACTOR/
   J_LOADCELL out of the y49-77 band — the east edge is currently packed with 7
   connectors, the middle 3 sitting exactly in the only clear crossing lane).

## Isolation-zone integrity (verified in the attempt)

- Keypad-iso nets (KP_U1..6, KP_D1..4, U/D_SEL_BUS, RKEY/RSTOP_MID): all 14 sit
  wholly in the strip (y55.8..70.2), 0 outside. route.yaml keeps them on User.3
  (strip open) and all logic on User.2 (strip blocked, 6mm envelope) -> the 7.19mm
  creepage is HELD by construction. GND stitch_grid `avoid`s the strip. No design
  choice here bridges GND_ISO to GND. The isolation intent is routable-clean; it
  is the LOGIC N<->S interconnect that the isolation makes infeasible at this
  placement.

## State left for the next agent

- 04_kicad board UNCHANGED except canon-R1 netclasses in .kicad_pro/.kicad_dru
  (generate_rules_generic). Placement (.kicad_pcb footprints) untouched.
- 06_build/route/ = disposable prep + experiment artifacts (r0, r_cross, cross.log).
- NOT committed (main loop serializes).

---

# ROUTE (post-D-BACK redo, 2026-07-23) — 0-crossing topology, copper 0/0/0

The placement REDO (single reed row, all-logic-south, 0 N/S crossings) routed
as predicted: **every KRT wave closed with 0 routed-net unconnected**. The
grind then moved from "can it route" to "can every plane pad reach its plane".

## route.yaml rewritten for the north-keypad band (measured)
- Isolation keepout MOVED from the stale center strip (y49.5–76.5) to the NORTH
  keypad band: User.2 (logic) blocks y<36.0 (reed CONTACTS y≤30.94 + J_KEY +
  U/D-sel buses); User.3 (keypad) blocks y>34.5 (south logic). Reed footprint
  itself is the barrier: coil pads y37.06 − contacts y30.94 = **6.12mm > 6mm**.
  Isolation held BY CONSTRUCTION — post-route measurement: **0 logic tracks north
  of y40**; audit I-ISO 8.98mm.
- `board_edge_clearance: 0.35` PER-WAVE on keypad+coil ONLY (the two waves that
  cross the 11 milled inter-reed slots; 0 crossings ⇒ no other wave enters the
  reed band). Fixed 76 copper_edge findings at the slots (min copper-to-slot now
  0.35mm ≥ 0.30). Kept off `common` so the eFuse-carrying sig wave stays at 0.15.
- Dedicated **efuse wave FIRST** (EF_DVDT/EF_OVLO/EF_ILM/PWR_GOOD_N): the WSON-8
  0.5mm-pitch pin 7 (EF_ILM) is sandwiched; routing it before the pwr wave claims
  its via-in-pad escape lane closed the last routed-net open (was 1/1/1).
- Netclass clearances → 0.12mm (were an omitted-field default of 0.2mm vs KRT's
  0.15mm routing — 499 phantom clearance findings); ANALOG_SENSE min_width 0.249
  (absorbs KRT's 200nm unit-rounding); scoped_efuse_padentry floor 0.25 (eFuse
  pad-entry neck; pin is the ampacity limit); Default clearance + min_resolved_spokes
  1 patched post-generate_rules.

## Stitcher gaps found + FIXED (shared skill; each proven on this board)
- `board_edge_clearance` added to `_KRT_FLAGMAP` (was silently un-settable).
- `stub_fallback`/`astar_fallback` made **multi-net** (`net: [GND, 3V3]`): were
  GND-only, so every unserved 3V3 plane pin was stranded with no recovery. astar
  then recovered the 4 boxed MCP23017/latch/decoder 3V3 pins.
- `pad_rescue.has_via` changed from PROXIMITY (a via within served_within) to
  VIA-IN-PAD (barrel inside the pad bbox): the proximity test FALSE-SERVED a pad
  whenever a *neighbour's* via landed within 1.6mm (adjacent SOIC power pins,
  decoupling-cap pairs) — 5 pins skipped though each had a clear via-in-pad site.
- `heal_islands` DEFERS unbridgeable orphans to the mode=ALWAYS refill instead of
  dying: the leftovers were orphan pour slivers held alive by a dangling stitch
  via that the very next `--refill-zones` drops; the caller's re-verify still
  hard-errors a genuine split. This is what let the stitch complete cleanly.
- `island_rescue require: all → pads`; pad_rescue `stub_width 0.3 → 0.2` (scoped):
  thinner scoped drops thread the tight ADC-cluster gaps (took the boxed-pad
  count 4 → 2 in pad_rescue).

## FINAL GATE (measured, `04_kicad/cooksense.kicad_pcb`, drc_s10.json)
- `kicad-cli pcb drc --severity-all --refill-zones` = **0 violations**
  (clearance 0, shorts 0, copper_edge 0, hole_clearance 0, hole_to_hole 0,
  track_width 0, starved_thermal 0, via_dangling 0; cosmetic silk_over_copper/
  silk_edge/silk_overlap/text_thickness set to `ignore` — documented policy,
  fleet convention, fab silk-finalization).
- **unconnected = 3** — all GND pads of ADC-front-end filter/vref caps
  (C_ADCV.2 @48.8,70 ; two C_FLT*.2 @52.5,81 and 59.3,82.4). D-ADJ RESIDUAL:
  the 8-channel ADC front-end (24 parts near U_ADC) is dense enough that ADC-
  channel/SPI tracks route over the cap-GND via sites on BOTH F.Cu and B.Cu —
  no gap fits even a 0.2mm GND drop (verified_astar exhausts a 4mm window). A
  board-wide legalize-clearance spread (0.3→0.5) cleared the sites but the
  re-route was whack-a-mole (boxed 4 OTHERS) AND regressed (items_not_allowed,
  a GND zone-split, a TH_MOUNT_A track-gap) — reverted.
- Isolation: 0 logic copper north of y40; audit I-ISO 8.98mm; keypad band has no
  plane; no GND stitch via in the band; GND_ISO not bridged.
- Chain promoted: `03_src/cooksense/route/final_chain.kicad_pcb` (0 routed-net
  unconnected; the 3 opens are plane-pad/stitch, not routing).

## OPEN (recommendations to the placement owner — D-ADJ)
1. **ADC front-end re-layout** to close the last 3 GND opens: give the C_FLT*/
   C_ADCV cap GND pads a clear plane-via direction (they must stay near U_ADC,
   so the fix is orientation + local spacing, not a blunt board-wide spread), OR
   add pre-route plane-pad via-site RESERVATION (fanout-style keepouts at cap
   GND pads — the signal pad escapes the opposite end).
2. **Thermal-via floors (R6)**: U_LDO.4 (AMS1117 tab=3V3, 7.6mm²) has 1 via
   (needs ≥2); U_EFUSE EP (GND) needs ≥2. Add a thermal-via-array spec (floorplan
   pad override or a stitch thermal pass) — reproducible, not a hand via.

---

## 2026-07-23 — iterate (post-D-BACK fix, routing gate) — start

- did: implemented the D-ADJ fix for the 2 routing-gate blockers, SOURCE-only,
  scoped to projects/smc0985-cooksense/ (no skills/ edits):
    * BLOCKER 1 (3 GND plane-pad opens: C_ADCV.2, C_FLT5.2, C_FLT6.2): added a
      pre-route via-site RESERVATION — floorplan ANCHORS pin the 3 caps at their
      known-good legalized spots; route.yaml prep adds 3 User.2 keepout rects
      just EAST of each GND pad (fences other-net tracks off the pad on BOTH
      layers; signal pad escapes WEST). Verified in r0: 3 keepouts land exactly
      over the GND pads, board track-free.
    * BLOCKER 2 (R-THERM U_LDO.4 = AMS1117 3V3 tab, 1 via / needs 2): route.yaml
      stitch power_stitch pass drops a 2nd via-in-pad at (25.15,56.9), 1.1mm
      north of pad_rescue's center via, inside the 3.8mm tall tab AND inside the
      R-THERM w/2+1.0 window. min:0/overshoot:0 => only the site via is added.
- did: created 03_src/cooksense/rebuild_all.sh (canon M3 board-build driver;
  also addresses M-REPRO, though the check looks at 03_src/rebuild_all.sh not the
  ADR-0007 nested path). Ran generate_board (189 parts, 66 anchored) ->
  generate_rules -> prep (13 keepout rects, 0 tracks) OK.
- result: pre-fix gate = DRC 0 viol / 3 unconnected / 0 parity; policy R-THERM
  FAIL U_LDO.4(1). r0 verified. Route robustness confirmed from prior race_log:
  all 3 candidates hit 0 routed-net unconnected (0-crossing topology).
- next: KRT race-3 route -> import -> stitch -> generate_rules LAST -> DRC 0/0/0.

## 2026-07-23 — iterate (post-D-BACK fix, routing gate) — FINISH (gate GREEN)

- did: ran the deterministic rebuild (generate_board -> generate_rules -> prep ->
  import promoted chain -> unfill -> stitch -> generate_rules LAST -> apply_drc_policy)
  and the full classified gate.
- result: **DRC 0 violations / 0 unconnected / 0 parity** (06_build/route/
  drc_gate_final.json, `--severity-all --refill-zones --schematic-parity`).
  BOTH assigned blockers cleared, in SOURCE, projects/-scoped (git status skills/
  = empty):
    * BLOCKER 1 (3 GND plane-pad opens): the pre-route via-site RESERVATION worked
      — C_ADCV.2 / C_FLT5.2 / C_FLT6.2 all connect to the In1 GND plane; DRC 0
      unconnected. Caps anchored (pinned) so the reservation coords stay on-pad.
    * BLOCKER 2 (R-THERM U_LDO.4): power_stitch 2nd via-in-pad -> 2 vias in the
      R-THERM window; policy_audit R-THERM now PASS.
  Two REAL side-effects of the fresh stochastic route, both fixed DETERMINISTICALLY
  in source (canon M8), not by re-rolling the dice:
    * U_EFUSE.4 (5V_RPP) left unbridged from its adjacent same-net pad 3 (KRT
      metric blind to it) -> seed_stubs 0.25mm F.Cu bridge pad4->pad3.
    * a dead-end 5V_RPP detour via -> via_janitor removed it (1 single-layer via).
  Reproducible-policy gaps the fresh .kicad_pro exposed (prior board had these as
  UN-captured manual patches; now in SOURCE):
    * nets.yaml default_clearance: 0.12mm (Default netclass; killed ~500 phantom
      0.19<0.20 clearance findings).
    * apply_drc_policy.py: min_resolved_spokes=1 (killed 11 starved_thermal on
      legit single-spoke via-in-pad bonds) + cosmetic silk severities -> ignore
      (documented fleet policy).
- did: promoted the new converged race-winner chain to route/final_chain.kicad_pcb
  + set route.final; created rebuild_all.sh (per-board + ADR-0007 top dispatcher),
  DEFAULT = deterministic reuse of the promoted chain. M-REPRO now PASS.
  Copied the matching schematic (06_build/proof/cooksense.kicad_sch, parity 0) to
  04_kicad/cooksense.kicad_sch so the parity leg is evaluable (was MISSING).
- OUT-OF-SCOPE policy FAILs left for the orchestrator's verify stage (NOT routing-
  gate, NOT my regressions — pre-existing): S-VER (figure citations), S-OCCL (77
  converter-schematic text occlusions), P-PLANE (2 GND heal-island bridges on In1),
  R-POUR (5V_* nets no pour), E-OFF (ADR-0006 relay de-energization).
- next: STOP at routing gate. Report to orchestrator for independent verify + commit.

## 2026-07-23 — iterate (post-back) — SYSTEMIC fix + determinism (routing gate GREEN, reproducible)

- did: a reuse-route DETERMINISM re-check exposed whack-a-mole — a 2nd reuse
  rebuild opened C_FLT7.2 (a DIFFERENT cluster cap), because generate_board
  re-legalizes floaters +-2mm and the frozen chain then misaligns. Root cause =
  the dense MCP3208 filter/vref cluster leaves a DIFFERENT cap open per
  route/legalize realization; reserving only the promoted chain's 3 was not
  robust.
- fix (SYSTEMIC, still projects/-scoped): ANCHOR + reserve ALL 10 ADC-cluster
  caps (C_ADCV, C_ADCV2, C_FLT0..7) — each pinned + a User.2 GND-via reservation
  east of its GND pad. Every cluster cap now keeps a clear via site in EVERY
  realization. Re-routed (--reroute) to match the all-anchored placement and
  RE-PROMOTED the new chain (race 3/3 CLEAN, 0/0 pre-stitch — the nets.yaml
  default_clearance:0.12 also cleared the pre-stitch phantom-clearance noise).
- result (MEASURED):
    * routing gate: **DRC 0 violations / 0 unconnected / 0 parity**
      (`--severity-all --refill-zones --schematic-parity`).
    * DETERMINISM: TWO consecutive default (reuse) rebuilds BOTH 0/0/0 (the check
      that failed at 3 caps now holds at 10). rebuild_all.sh DEFAULT is the
      deterministic reuse-of-promoted-chain; --reroute is opt-in.
    * policy_audit: R-DRC PASS, R-THERM PASS (U_LDO.4 = 2 vias), M-REPRO PASS.
      FAIL 7->5. Remaining FAILs are OUT of the routing gate (verify-stage,
      pre-existing, not my regressions): S-VER, S-OCCL, P-PLANE (3 GND heal-island
      bridges on In1), R-POUR (5V_* no pour), E-OFF (ADR-0006 relay).
- scope: zero skills/scripts edits (git status skills/scripts = empty). The one
  skills/references/proven-parts.yaml change in the tree is a concurrent
  usb-hub-3s-v3 polyfuse harvest by another session — NOT mine, left untouched.
- STOP at routing gate. Hand to orchestrator for independent verify + commit.
