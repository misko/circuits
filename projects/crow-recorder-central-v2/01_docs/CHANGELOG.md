# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

## v1.3 — 2026-07-24
- CPL/evidence-only supersede closing the THIRD external review of v1.2 (HOLD-
  for-PCBA; archived 08_reviews/2026-07-24_v1.2_external-llm_full.md). Root cause:
  jlc_rotations_db.csv keyed by FOOTPRINT NAME while JLC orients per LCSC PART —
  the sealed v1.2 CPL shipped U1 (consigned XU316) at 270 deg vs its exact pad-fit
  90 deg (180 deg off), plus 9 more ROT-DB-SUGGEST rows. Fixed at the source: new
  per-LCSC rotation table skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv checked
  BEFORE the name-DB (RED-verified, fleet-wide fix). CPL regenerated -> twin 0
  ROT-DB-SUGGEST (was 10). missing_models corrected 172->177; ORDER_README gains
  U1 rotation-closure + JLC-preview pin-1 human gate + 8-beeper aggregate-load
  (~1.2A vs 2A fuse) + MSL-3 consigned-U1 handling. Copper/gerbers/drill/BOM/source
  byte-identical to v1.2 (documented in freshness_exceptions.txt). Fresh-lens ORDER.
Released: crow-recorder-central-v2-v1.3-2026-07-24

## v1.2 — 2026-07-24
- Respin closing the SECOND external review of v1.1 (HOLD; archived verbatim
  08_reviews/2026-07-24_v1.1_external-llm2_full.md, EXT2-F1..F5 dispositioned).
  EXT2-F1 (the driver): 0V9 core rail had 8x 100nF for 15 XU316 core-VDD pins
  vs the vendor minimum — VERIFIED at the datasheet (XM-014532-PC-2.0.0 §14
  "Integration" p.29: "at least 12" 100nF low-inductance MLCCs close to the
  chip; §H.2 p.92). v1.2 ships 13x (C_c1..C_c13): C_c9 -> pins 11/14 (1.63mm),
  C_c10 -> pin-5 pocket (0V9 pad on the existing 0.5mm feeder), C_c11/C_c13 ->
  pins 50/54 (2.01/2.02mm, via the C_b0v9 bulk slot swap — bulk has no
  pin-adjacency requirement per ds §14, moved 3.75mm south with a B.Cu feed),
  C_c12 -> pin 95 (2.55mm). TDI F.Cu run rerouted to In3 to free the south
  band; 32 U1-cluster floaters pinned at their exact v1.1 positions so only
  the intended copper changed; netlist diff vs v1.1 = exactly the 5 caps
  (verification/decoupling_fix.md). EXT2-F2: ORDER_README §4a rail-sequencing
  scope gate strengthened (all startup corners + explicit 1V8-before-0V9 +
  reset-held pass condition; interlock = v-next design item, never a delay
  tweak). EXT2-F3 (D_USB stub) carried P2 + in-line-ESD pre-production v-next.
  EXT2-F4 (RJ45/PoE + DC OVP) = ADR-0007 USER waiver carried UNCHANGED.
  USB pair / U1 EP via grid / LV-strap floats re-measured intact.
Released: crow-recorder-central-v2-v1.2-2026-07-24

## v1.1 — 2026-07-24
- Respin closing the external DO-NOT-ORDER review of v1.0 (orchestrator-verified;
  08_reviews/2026-07-24_v1.0_external-llm_full.md, EXT-F1..F6 dispositioned).
  F1: U1 (XU316) EP thermal grid remodeled from 16 duplicate-numbered thru-hole
  pads (emitted ComponentDrill) to 16 REAL GND vias (ViaDrill T1) seeded by
  03_src/add_u1_thermal_vias.py at rebuild step 3.5; board setup capping/filling
  = yes; filled+capped via-in-pad explicitly ordered (ORDER_README §1a) + X-ray
  first-article gate. F2: USB_DM renamed USB_DN (KiCad pairs only P/N suffixes),
  USB_DIFF netclass with diff_pair {0.125/0.15} solved for JLC06161H-3313 (2D FD
  field solve 89.7-90.5 ohm, verification/usb90_solve.md), pair rerouted with KRT
  route_diff: spread 0.110mm, all F.Cu, 0 vias; diff-pair DRC rule ACTIVE
  (proven able to fail); R-LEN now graded via audit_board skew gate. F4: all
  evidence regenerated against the staged archive itself (standalone-source DRC
  0/0/0; manifest counts == shipped evidence; bom_source/stock name the sealed
  dir). Promoted converter sch guarded in rebuild_all (dogleg surgery survives
  regeneration). PR2-P0-1 (this release's own zero-context pin review): U1
  LV_L_N/LV_T_N/LV_R_N straps (40/43/52) were 3V3-tied on the FIXED-1.8V IOB
  bank (AMR VDDIO+0.5=2.3V, ds v2.0.0 §4.4/§4.8/§15.1) — fixed to the
  datasheet float select; netlist diff vs v1.0 = exactly 7 node moves (4 USB
  rename + these 3). Sourcing: RG1/R_cs/R_rst -> C60490, R_scl/R_sda ->
  C105871 (basics stocked out). ADR-0007 RJ45/beeper USER waiver carried
  UNCHANGED.
Released: crow-recorder-central-v2-v1.1-2026-07-24

## v1.0 — 2026-07-23
- P0 fix pass sealed: two geometric net-merges (P5VA_4->AUDIO4M, MID2P->5V)
  fixed at source; check_port_nets gate added (115/115 labels, 8/8 ports).
  P1 set closed with measured evidence (5V trunk 0.5mm + 1144mm2 pours,
  P-ADJ local measurements, 8x per-port NOT-ETH silk, ADR-0005 amendment,
  ADR-0007 PoE waiver carried from pod-v2). audit_board (P-POL/P-KEEP) added,
  red-tested. Sourcing staged: TLV70018 for TCR2LF18 (stock 0), NX3225SA for
  FA-238 (stock 0), 402k for 400k (not stocked), BLM21SP601SN1D for the
  mislabeled 60R bead (wrong-part catch); XU316 + RJ45 consignment per
  ADR-0003. DRC 0/0/0; policy_audit 0 FAIL; ERC 0 err; count_parity 194 x4.
Released: crow-recorder-central-v2-v1.0-2026-07-23

## v0.1 — 2026-07-23
- Commissioned crow-recorder-central-v2 (mixed-signal-audio-hub class), CLEAN-ROOM
  from the brief + sanctioned skill references. ADR-0001..0006 written; fab_tier
  = jlc_6layer_smallvia (ADR-0002); netclasses + ampacity floors defined BEFORE
  routing (03_src/rules/nets.yaml). Parts research fanned out (18 parts; 8 ledger
  hits). Schematic (tscircuit) authoring in progress.
Released: no
- Placement: mixed-signal-audio-hub floorplan (39 anchors + 155 pattern-placed
  passives), 6-layer In1+In4 GND planes; audit_template I1-I8 PASS (0/0). Project-
  local footprints: TQFP-128_EP (16-via grid), US8, vendored numeric-pad USB-C+RJ45.
  generate_rules merged 5 netclasses into 04_kicad. Routing (KRT) in progress.
