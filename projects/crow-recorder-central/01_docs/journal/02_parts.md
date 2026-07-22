# journal — 02_parts (successor: P-ESC escape blocks + tension ADRs)

## 2026-07-21 22:05 — start
- did: successor session opened; work order = routing.md handoff list. Read
  escape_check v2 + policy_audit P-ESC/P-TIER + fab_tiers.yaml.
- result: MEASURED — 23/23 part.yamls lack `escape:` blocks (grep -L);
  nets.yaml declares `fab_tier: jlc_6layer_standard` which does NOT exist in
  fab_tiers.yaml (P-TIER would FAIL: "not a tier"); board DRU floors are
  0.30/0.15 vias, 0.09 track/clearance, 0.2 hole-to-hole (ADR-0009) — i.e.
  the real tier is 6L + small-via, not 6L standard (nets.yaml header comment
  is stale vs ADR-0009).
- next: add jlc_6layer_standard + jlc_6layer_smallvia tiers to fab_tiers.yaml
  (with provenance), write D-TIER ADR-0012, point nets.yaml at the small-via
  tier, compute escape blocks for all multi-pin parts, verify with
  escape_check over the merged set.

## 2026-07-21 22:20 — iterate 1 (P-ESC + D-TIER done)
- did: added jlc_6layer_standard (rank 3) + jlc_6layer_smallvia (rank 4) to
  skills/kicad-pcb/references/fab_tiers.yaml with archive provenance; wrote
  D-TIER ADR-0012; nets.yaml fab_tier -> jlc_6layer_smallvia (header
  comment de-staled vs ADR-0009); appended computed escape blocks to all 23
  part.yamls (XU316 block encodes ADR-0009 via-in-pad small-via; PCM1865 /
  TPD4EUSB30 declare the unconditional jlc_4layer_advanced per the math).
- result: MEASURED — escape_check 23/23 ok EXIT=0; policy_audit P-ESC PASS
  ("23 parts: escape blocks agree"), P-TIER PASS ("all parts escape at
  declared fab_tier 'jlc_6layer_smallvia'"); full audit 0 FAIL
  (PASS=16, WAIVED=3, HUMAN=6, N-A=5).
- next: tension ADRs T1-T3 with live JLC stock re-check.

## 2026-07-21 22:35 — finish (tension ADRs T1-T3 resolved, live stock re-measured)
- did: live JLC stock re-check on the 9 tension-relevant codes
  (jlc_stock_check.py, evidence 06_build/cache/tension_stock_2026-07-21.csv);
  wrote ADR-0013 (XU316 consign line, C-grade C6362698 stock=10 noted as
  user-approval-only option), ADR-0014 (Y1 = X322524MOB4SI C70590 stock
  104,480; FA-238 Digi-Key fallback), ADR-0015 (U12 = TLV70018DDCR C79924
  stock 5,258; LP5907/ME6211/RT9013 ranked alternates all stocked;
  exact-MPN Digi-Key fallback); BRIEF tension table + decision register
  updated to RESOLVED.
- result: MEASURED — C6938291=0, C2650433=0, C150173=0 (all three tensions
  confirmed live); substitutes C70590=104480, C79924=5258 healthy; the
  archive's D27 substitutions are already wired in 03_src/bom_seed.py, so
  no board/BOM code change was needed — the ADRs formalize + re-evidence.
- next: work-order item 3 (rev-string residue) + item 4 (silk-attribution
  check port), then stage-7 verification fan-out.
