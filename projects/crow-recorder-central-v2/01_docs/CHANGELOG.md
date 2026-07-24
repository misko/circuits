# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

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
