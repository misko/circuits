# learnings — verify + seal (crow-recorder-central v1.0)

## New stage-7 gates on an adopted archive design
- **E-TOPO on an LDO+buck tree:** power_topology.py classifies only
  buck/boost/buck_boost; LDO `type:` strings return None and would LoadError.
  Correct modeling = declare ONLY the switching converters as rails (the two
  AP61102 bucks) and document the LDO post-regulators in comments as linear
  step-down (inherently outside the buck/boost derivation) — same pattern as
  usb-hub-3s-v2's downstream PD controller. Omit input_trunk_class when the
  trunk carries loads beyond the declared rails (here PWR5 feeds pods+beepers),
  else the over-built advisory false-fires. candidate-canon: no (already the
  script's intent; worth a one-line note in the power_tree template).
- **E-INV/E-ADR:** the three protection/topology ADRs (0002 input protection,
  0005 beeper topology, 0007 reverse-FET) are what E-ADR forces coverage of —
  author invariants for those FIRST, then the task's intent (clocks, RJ45,
  USB-C CC). adr: fields may be non-numeric (pod-0004, usb-c-rd) for cross-board
  / spec-driven intent without tripping E-ADR's numeric coverage. candidate-canon: no.

## Red-team caught what internal gates cannot
- Both zero-context red-teams returned ORDER; the substantive findings were all
  P1 and INVISIBLE to DRC/ERC/parity/twin: F1 (no OVP below the 6.5V downstream
  abs-max — a design-intent gap, not a wiring error), L1 (USB pair layer-hops
  across F.Cu/B.Cu/In2 with 7 vias, violating the nets.yaml F.Cu-only intent —
  a routing-quality rule no gate enforces), L2/L3 (hot-loop + long-analog
  geometry). Lesson: the "routing intent" prose in nets.yaml (USB F.Cu-only) is
  NOT machine-enforced; a candidate check (per-net allowed-layer + max-via
  assertion) would have caught L1. candidate-canon: YES — id R-NETLAYER
  (assert a signal-class net stays on its declared routing layers / via budget).

## Transient JLC API during seal
- jlc_twin FETCH-FAILED and jlc_stock 0 are BOTH partly transient: C90 (100uF)
  and J9 (barrel) fetch-failed across 3 retries incl. ATTEMPTS=8 — adjudicate
  FETCH-FAILED with the board-verified land + order-preview flag (not "no CAD").
  A jellybean 10k (C25744) genuinely read 0 in isolation — real stockouts move
  hour-to-hour, so the seal ships an in-stock drop-in note (C25804), not a
  board change. candidate-canon: no (jlcpcb-fab already documents both).

## Release packaging (V-REL-FPLIB) verified, not assumed
- Standalone DRC on the bare .kicad_pcb = 959 violations (lib_footprint_issues +
  parity-no-schematic). The fix that MEASURES clean (0/2-waived/0): ship source/
  with the .kicad_sch + .kicad_pro + fp-lib-table + a CO-LOCATED cac.pretty and
  the fp-lib-table cac uri rewritten to ${KIPRJMOD}/cac.pretty. TEST it in
  scratch before sealing. candidate-canon: YES — a release-time
  "standalone re-measure" check belongs in the seal script.
