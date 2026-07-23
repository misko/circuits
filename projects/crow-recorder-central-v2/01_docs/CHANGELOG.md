# Changelog

One entry per REVISION (a design state, git-tagged). Reverse-chronological.
`Released:` is `no`, or the name of the `07_releases/` directory that shipped it.

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
