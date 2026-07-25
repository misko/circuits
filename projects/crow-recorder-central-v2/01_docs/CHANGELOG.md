# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

## v1.4 — 2026-07-25
- **CPL-CORRECTION supersede: v1.3 is DO-NOT-ORDER for PCBA.** v1.3 shipped SEVEN
  CPL rows 180 deg off — U1 (C6938291, the CONSIGNED XU316 TQFP-128, 0.4mm pitch),
  U2+U3 (C181312 PCM1865 TSSOP-30), U5 (C82317 SOIC-8), U7+U8 (C5224055 SOT-563)
  and D_USB (C90627 USON-10), i.e. every fine-pitch part on the board — all at
  90.0 where the measured value is 270.0. v1.0/v1.1/v1.2 shipped these SEVEN
  correctly at 270; v1.3 "fixed" a non-defect. ROOT CAUSE (fixed at source before
  this release): jlc_twin.xform() used the OPPOSITE handedness to the operator
  KiCad applies to a rotated footprint's pads, negating every jlc_offset —
  invisible at 0/180 (sign-invariant), exactly 180 deg wrong at 90/270 (1b69760,
  pinned by two RED-verified tests against pcbnew). jlc_lcsc_rotations.csv had
  been POPULATED FROM that function, so six rows inherited the negation and an
  external reviewer reading the table was misled (canon M1); corrected in e0d735c.
  Q1/Q2/U9 are UNCHANGED because their values are 180, which the negation cannot
  move — that asymmetry is the root cause's fingerprint.
- ACCEPTANCE GATE (stated as a number BEFORE looking): the v1.4-vs-v1.3 CPL diff
  is EXACTLY SEVEN changed CELLS, all Rotation, all 90.0 -> 270.0; 0 rows added or
  removed; Q1/Q2/U9 byte-identical. Measured cell-by-cell. The seven angles were
  then RE-DERIVED by a method sharing no code with the twin/resolver/exporter
  (pcbnew for our pads, a text parse of JLC's own cached footprint for theirs,
  operator proven against pcbnew first): all seven fit at 270 with residual
  <= 0.0725mm against a runner-up 15x-4811x worse, 0 mismatches vs the shipped
  CPL. verification/cpl_acceptance_gate.md + rotation_remeasure.txt.
- NO COPPER CHANGE, proven by RE-PLOT rather than by copying: all 15 gerber/drill
  zip members hash identically once the plot's own timestamp comments are stripped;
  20 payload files are sha256-identical to sealed v1.3 and fab/cpl.csv is the only
  file that differs (verification/replot_identity.txt + payload_identity.txt).
- **PCBA gates land on this board.** 03_src/rules/assembly.yaml is authored (A-POP
  PASS: board 203 / cpl 177 / unpopulated 26 = 10 declared + 16 exempt H,TP), with
  U1 moved from v1.3's `not_assembled` prose into `consigned:` — a consigned part
  is POPULATED — carrying the REQUIRED msl: (MSL 3, 168h floor life, XU316 ds
  v2.0.0 s14.5 p33; also backfilled into the part.yaml limits: block, which was
  missing it). J3-J10 declared not_in_catalog with the dated catalog query;
  JP_INJ/J_DBG re-classified dnp_by_design after proving JLC DOES stock 2.54mm
  headers — "hand-solder" is a wall you prove you hit, not a style. A-STOCK PASS
  at build_quantity 5 with verification/stock_check.json and a sourcing_plan entry
  for C6938291 (JLC stock MEASURED 0; consigned, so JLC stock is irrelevant) —
  v1.0-v1.3 all shipped a stock report ending in FAIL that nothing ever parsed.
- Archive self-containment CHECKED, not assumed: a standalone DRC on a copy of
  source/ alone is 0/0/0 with zero lib_footprint_issues (this board's fp-lib-table
  resolves both vendored libraries via ${KIPRJMOD} and they ship inside source/),
  so it does NOT have the usb-hub-3s-v3 v1.3/v1.4 out-of-archive-pointer defect.
- Project contracts.md copies re-synced from skills/pcb-design/templates/contracts/
  (01_docs, 02_parts, 03_src, 03_src/rules, 07_releases) — this revision is when
  they catch up, per CLAUDE.md.
Released: crow-recorder-central-v2-v1.4-2026-07-25

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
