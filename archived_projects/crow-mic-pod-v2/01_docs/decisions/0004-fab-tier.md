---
id: 0004
date: 2026-07-23
status: accepted
---
# 0004 — Fab tier = jlc_2layer_default (cost ceiling)

## Context
D-TIER: the fab tier is a COST CEILING declared at commission
(nets.yaml `fab_tier:`). Default to the cheapest plausible tier; P-TIER
blocks any part whose escape needs a costlier one.

## Options
- **jlc_2layer_default** (0.6/0.3 vias, 0.15 track floor, no advanced
  option) — ACCEPTED.
- 4-layer / small-via / advanced — REJECTED: nothing on this board needs
  it. The densest package is the OPA1678 SOIC-8 (1.27 mm pitch, trivially
  escapable at standard tier) and the TPD2E2U06 SOT-553 (0.5 mm pitch,
  5-lead, leaded outward escape). All 7 specialty parts' ledger escape
  blocks declare `tier_required: jlc_2layer_default`.

## Decision
`03_src/rules/nets.yaml fab_tier: jlc_2layer_default`. 2-layer, GND pours +
stitch. No advanced-PCB order option; no small-via callout.

## Consequences
- ORDER_README states: standard 2-layer, no advanced option, 0.6/0.3 min
  via. Cheapest JLC tier.
- If routing ever demands a sub-0.15 track or a <0.45 via, that is a
  BACKTRACK to placement (D-ADJ) — not a silent tier bump.
