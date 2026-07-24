# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

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
