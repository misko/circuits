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
