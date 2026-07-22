---
id: 0011
date: 2026-07-22
status: accepted
---
# 0011 — fab_tier = jlc_4layer_advanced (forced by the 5 A PD PHY, NOT over-engineering)

## Context (D-TIER, decided at D-ESC per SKILL)
Commission (D3) TARGETED jlc_4layer_standard: v1 needed advanced ONLY for the
IP6559 buck-boost QFN-48, and v2 removes the buck-boost. But the D-SPEC sourcing
spike's 5 A-capable PD source PHY, **TPS25740A**, is a 4-sided **VQFN-24 0.5 mm**
part, and escape_check grades it:

    escape_check.py --style qfn --pitch 0.5  ->  jlc_4layer_advanced
    (INFEASIBLE at 2-layer and 4-layer-standard; the outward-only-local rescue
     applies to DUAL-ROW small QFNs only, not a 4-sided 24-pin part — inner
     pins on a loaded side cannot escape without via-in-pad.)

Every OTHER multi-pin part on the board escapes at STANDARD or better:
- LM5116 HTSSOP-20 0.65 mm leaded → jlc_2layer_default (ledger)
- TPS2557 VSON-8 0.65 mm → jlc_4layer_standard (ledger)
- TPS2513A SOT-23-6, USBLC6 SOT-23-6, AON6354/AON6403 DFN 1.27 mm → 2-layer
- XT60, fuse, USB-A, USB-C receptacle → connectors, 2-layer

So exactly ONE part drives the tier, and it is driven by the **5 A PD
requirement**, not by an over-capable topology.

## Options
- **Accept jlc_4layer_advanced (CHOSEN).** ADVANCED (0.25/0.15 mm vias,
  via-in-pad) is proven orderable (usb-power-3s v1.0-1.3; usb-hub-3s v1). The
  cost delta buys a legitimate 5 A PD source in a single small QFN — a far
  smaller advanced-tier footprint than v1's whole buck-boost cell (QFN-48 + 4
  FETs + inductor). ORDER_README carries the advanced-tier line.
- **Drop to 5 V/3 A, no PD chip (plain Rp), STANDARD tier (REJECTED here,
  offered to user — BRIEF T4).** Type-C current advertisement gives 5 V/3 A
  (15 W) with zero PD silicon → the board's only advanced-forcing part
  disappears and it fabs at STANDARD. But the spec is 5 A (25 W); per the SKILL
  autonomous rule I take the SIMPLEST reading that satisfies the STATED
  requirement — and the stated requirement is 5 A. This tension is flagged
  LOUDLY: if the user accepts 3 A, v2 becomes a STANDARD-tier board.
- **Find a wider-pitch / leaded 5 A PD source (REJECTED).** The sourcing spike
  found none in stock; all real DFP PD source PHYs are fine-pitch QFN.

## Decision
`fab_tier: jlc_4layer_advanced` (03_src/rules/nets.yaml). Forced solely by the
TPS25740A VQFN-24 0.5 mm, which is forced by the 5 A PD-source spec. This is
NOT the v1 over-engineering pattern (a converter more capable than its rail);
it is the intrinsic cost of a 5 A USB-C PD contract.

## Consequences
- Advanced via/annular floors in generate_rules (.kicad_dru + .kicad_pro).
- Only the TPS25740A cell needs the advanced escape (via-in-pad); the rest of
  the board is standard geometry — placement can localize the fine work.
- If the user relaxes to 3 A: delete TPS25740A + path FET, add 2 CC pull-ups,
  set fab_tier back to jlc_4layer_standard. A bounded, documented downgrade.
