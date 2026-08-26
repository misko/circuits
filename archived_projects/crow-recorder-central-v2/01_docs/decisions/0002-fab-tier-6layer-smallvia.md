---
id: 0002
date: 2026-07-23
status: accepted
---
# 0002 — D-TIER: fab_tier = jlc_6layer_smallvia

## Context
The brief says "4-layer min, 6 preferred." The dominant escape constraint is
the XU316-1024-**TQ128** (TQFP-128, 14x14mm, **0.40mm pitch**, 4.7mm exposed
GND paddle pin 129). fab_tier is a cost ceiling declared at commission (D-TIER);
choosing it correctly NOW is the cheapest moment.

## Options (from fab_tiers.yaml, cheapest-first)
- **jlc_4layer_standard (rank 1)** — REJECTED: 0.45/0.3 vias cannot via-in-pad
  the 0.4mm-pitch EP or inner rings; the ledger records "0.4mm TQFP-128 does
  NOT close full routing at 4L."
- **jlc_4layer_advanced (rank 2)** — REJECTED: 0.25/0.15 via-in-pad helps, but
  the ledger's XU316 escape needed 6 LAYERS + small-via, not merely advanced 4L
  (ADR-0008/0009 escalation on the precedent board).
- **jlc_6layer_standard (rank 3)** — REJECTED: 6 layers but 0.45/0.3 vias — the
  precedent board's "no small-via needed" claim was falsified; 0.4mm pitch needs
  0.30/0.15 via-in-pad.
- **jlc_6layer_smallvia (rank 4)** — CHOSEN: 0.30/0.15 via-in-pad, 0.09
  track/space, 0.2 hole-to-hole. The proven floor for a 0.4mm TQFP-128 escape
  (fab_tiers provenance). PCM1865 (4L-advanced) is subsumed.

## Decision
`nets.yaml fab_tier: jlc_6layer_smallvia`. Order form: **6 layers + "advanced"
SMALL-VIA option (min via 0.30/0.15mm)** — required for the XU316 0.4mm-pitch
via-in-pad escape. This is the brief's "6 preferred" reading, forced by the SoC
package, and is the cost the design accepts.

## Consequences
- ORDER_README carries the tier's exact order line (small-via advanced option).
- Every part's escape.tier_required must be <= rank 4 (P-TIER gate).
- Stackup: F / In1-GND / In2 / In3 / In4-GND / B (planes on In1+In4).
- Verify every floor against JLC's capability page at order time (canon M6);
  this tier is design-proven on the precedent board but archive-ordered only.
