# journal: placement — interposer (Board C)

## 2026-07-24 09:08 — start
- did: floorplan.yaml authored (no archetype exists for a passive interposer
  class — trivial 3-connector board, derived directly): two 10FDZ-BT rows
  X-ALIGNED (pin k columns at same x -> straight-through verticals), TP rows
  on-column between them, GH breakout west edge mouth-west (main-board idiom),
  4x M2.5 holes. NO zones/pours/keepouts: single floating domain.
- result: 23 parts anchored, 12 asserts passed (pad_net 9 + pad_order 2 +
  body_offset 1), refdes 23/23 on silk. Two crowded captions fixed by
  relocation; the redundant "1:1 RIBBON" caption dropped (refdes + ORDER_README
  carry it).

## 2026-07-24 09:10 — finish (placement gate GREEN)
- P-OUT: PASS — tightest pad-to-outline margin 2.30mm (J_KEY_MATRIX.MP).
- P-CAP: PASS — worst cut y=22.4: demand 10 vs capacity 136 (ratio 0.07).
- tier_preflight: 0 FAIL / 0 WARN after legalize.clearance 0.8 (PF-LEGALIZE).
- P-LAYOUT/P-ADJ scope: no ICs, no keep_short budgets (passive; the 10FDZ
  part.yaml layout: block is mechanical-only) — nothing to measure.
- next: KRT route.
