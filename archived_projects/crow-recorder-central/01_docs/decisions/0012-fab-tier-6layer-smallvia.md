# ADR-0012 — D-TIER: fab_tier = jlc_6layer_smallvia (cost ceiling raised)

Status: accepted 2026-07-21 (this project's own decision; formalizes the
adopted archive's ADR-0008 + ADR-0009 as the D-TIER gate requires)

## Context

The commission's cost-minimal tier ladder was walked and measured by the
adopted archive design (ADR-0011 provenance, re-verified here):

- **4-layer (any via option)** — does NOT close routing. ADR-0008 measured
  the 4L deficit across placement/net-order/board-growth attempts: the
  XU316 TQFP-128 escape annulus cannot carry signals AND the distributed
  3V3/0V9 power taps, and the 8 beeper-gate lines saturate the analog
  corridor. Final 4L deficit 2-5 nets, reproduced over reconcile passes
  3..9. Topology limit, not router tuning.
- **6-layer STANDARD (0.45/0.30 vias)** — layer budget closes routing, but
  the 0.4mm-pitch via-in-pad escape fails DRC: 0.45mm barrels OVERLAP at
  0.4mm pitch (6 shorting_items on TDO/TDI) + 24 hole_clearance (ADR-0009).
  0.45 does not fit; this is geometry, not iteration.
- **6-layer + JLC SMALL-VIA option (0.30/0.15, via-in-pad)** — closes:
  0.30mm via-in-pad keeps 0.10mm copper gap at 0.4mm pitch. Board
  reproduces DRC severity-all+refill+parity = 0 violations / 2 unconnected
  (both ADR-0010-waived GND slivers) / 0 parity from committed sources
  (06_build/rebuild_attempt1.log, 2026-07-21).

The BRIEF itself says "4-layer min, 6 preferred — archive proved 4L does
not close; expect 6L + small-via tier" (tension T4, user-flagged).

## Decision

`03_src/rules/nets.yaml` declares **`fab_tier: jlc_6layer_smallvia`**
(rank 4 in `skills/kicad-pcb/references/fab_tiers.yaml`, added with this
board's provenance: 6 layers, 0.30/0.15 vias, via-in-pad, 0.09
track/space, 0.2 hole-to-hole). The previously declared name
`jlc_6layer_standard` existed in no tier table (P-TIER would fail it) and
was falsified by ADR-0009 anyway.

The ORDER_README must carry the tier's exact order_readme line:

> 6 layers + "advanced" SMALL-VIA option REQUIRED: min via 0.30/0.15 mm
> (XU316 TQFP-128 0.4mm via-in-pad escape, ADR-0009)

## Consequence

- Cost: 6L large-area board (176x122mm) + per-order small-via fee — the
  dominant drivers of the archive's $150-220/board estimate vs the $79-90
  target, already flagged to the user (BRIEF T4).
- Per-package escape tiers (part.yaml `escape.tier_required`) stay HONEST
  to escape_check's math: the XU316/PCM1865/TPD4EUSB30 compute
  `jlc_4layer_advanced` as the cheapest via-in-pad-capable tier — the 6L
  escalation is a BOARD-level routing-congestion decision (ADR-0008),
  above any single package's escape. P-TIER passes because rank(declared
  4) >= rank(required 2).
- A future cost spin's levers: every-other-pad F.Cu escape to drop the
  small-via fee, smaller outline, 4L partial depop (ADR-0009/archive
  ORDER_README) — not attempted for v1.0, correctness first.
