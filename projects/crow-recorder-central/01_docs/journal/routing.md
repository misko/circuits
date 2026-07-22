# journal — routing (adopted-design reproduce check)

## 2026-07-21 21:44 — finish (reproduce gate GREEN at the routing boundary)
- did: adopted archived crow-array-central v1.0 design under ADR-0011 (02_parts, 03_src incl. promoted FULL-BOARD route artifact 03_src/route/final.kicad_pcb, 01_docs design docs + ADRs 0001-0010 with provenance headers, identity renamed crow_array_central->crow_recorder_central); ran the full rebuild chain (06_build/rebuild_attempt1.log)
- result: MEASURED — ERC clean (chain gate), audit PASS (0 fails, 3 warns incl. C260 refdes-to-Fab waiver), DRC severity-all+refill+parity = 0 violations / 2 unconnected (both the ADR-0010-waived GND zone slivers, matching the sealed archive) / 0 parity, EXIT=0. The central archive does NOT have the pod's stale-route defect — the full-board promotion style reproduces.
- next (successor, in order):
  1. P-ESC: escape blocks for all archive-era part.yamls (escape_check; XU316 TQFP-128 0.4mm must encode ADR-0009 small-via via-in-pad) + D-TIER ADR raising fab_tier to 6L+small-via (T4) with the exact order_readme line.
  2. Resolve commission tensions (BRIEF T1-T3, all JLC stock=0 on 2026-07-21): XU316 consign/global-sourcing ADR (archive shipped it as designated consign line), FA-238 Digi-Key fallback line, TCR2LF18 alternates search (or Digi-Key hand-solder).
  3. Check silk/schematic rev strings for rename residue (pod carried "v1.1" onto a v1.0 board — grep board text for version + check title blocks; pin rev via env like pod's POD_REV).
  4. Consider porting the pod's refdes-attribution check (nearest-neighbor bbox, red-verified) into this board's generator.
  5. Verification fan-out per SKILL stage 7 (bom_seed, stock, twin w/ archive adjudications in 03_src/rules, pin_audit -> fresh agents per group, render review, bare render pair + missing_models.txt, policy_audit), ledger+archetype harvest (found mixed-signal-audio-hub archetype at release), then release per the NEW contract: source/ MUST ship .kicad_pro/.kicad_dru/fp-lib-table (pod learning, candidate-canon).
- interop: RJ45 contact map authority = ../crow-mic-pod/01_docs/decisions/0004 (contact-for-contact; pod v1.0 sealed 2026-07-21).
