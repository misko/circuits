# journal: 03 schematic — interposer (Board C)

## 2026-07-24 09:00 — start
- did: authored 03_tscircuit/src/interposer.tsx (23 components: 2x 10FDZ-BT +
  SM10B-GHS-TB + 20 pad TPs; 10 floating nets KP_U1..U6/KP_D1..D4, NO GND/power
  by design) + manifest_interposer.yaml. tsx_preflight: all pad names tsx-safe.
- result: tsci build OK; converter -> kicad/interposer.kicad_sch, 23/23 with
  FPID (both ZIFs resolve cooksense:JST_10FDZ-BT_1x10_P2.54mm_Vertical_ZIF,
  breakout resolves Connector_JST GH via C2683602). J_KEY_MATRIX MP tabs
  FLOAT (netlist: MP in no net) — isolation preserved per the SM10B part.yaml.

## 2026-07-24 09:03 — finish (schematic gate GREEN, all measured)
- ERC --severity-all: 0 errors / 102 warnings — warning classes identical to
  the sealed cooksense baseline (endpoint_off_grid 56, footprint_link_issues
  23, lib_symbol_issues 23 = converter cosmetics).
- netlist: 06_build/netlists/interposer.net — 10 nets x 5 nodes = 50 nodes.
- S-NETMERGE net_label_survival: PASS (10/10 labels survive).
- E-INV: 50/50 invariants hold (pass-through + breakout + both-side TPs, per
  line, incl. D4 as plain pass-through per T3).
- E-ADR: interposer file cites ADR-0009; project-wide coverage PROVEN with a
  merged cooksense+interposer invariants view: "every protection/topology ADR
  is cited" (per-board files are the ADR-0007 split; single-file E-ADR run
  against the shared decisions dir flags the OTHER board's ADRs — expected).
- E-TOPO/E-MARGIN/E-OFF: N-A by design (rails: [], source_type external scan
  signals; passive board — fact-lock rows in BRIEF.md).
- S-COUNT count_parity: 23==23==23 (circuit.json/kicad_sch/netlist vs
  manifest) — run in a single-board shadow tree (multi-board scoping; the
  script reads one manifest.yaml/tree).
- converter-vs-tscircuit netlist parity: 0 node diffs (scripted set compare).
- bom_source_check --circuit-only: PASS.
- next: floorplan + placement gates (P-OUT/P-CAP), tier_preflight, route.
