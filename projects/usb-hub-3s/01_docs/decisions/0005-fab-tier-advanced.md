---
id: 0005
date: 2026-07-21
status: accepted
---
# 0005 — D-TIER: fab_tier = jlc_4layer_advanced

## Context
D-TIER declares the fab tier as a cost ceiling at commission. The default is
the cheapest plausible tier (A3: no cost ceiling given by the user).
The spec-critical PD source (ADR 0004, IP6559-C) is a QFN-48 0.5 mm-pitch EP
package; `escape_check --style qfn --pitch 0.5` reports:

    jlc_2layer_default   INFEASIBLE
    jlc_4layer_standard  INFEASIBLE
    jlc_4layer_advanced  ok

## Options
- **Stay at jlc_4layer_standard and pick another PD part** — REJECTED: the
  in-stock part universe for compliant 5 A has NO sub-0.5 mm-pitch-free
  option (ADR 0004 table); every candidate is 0.4–0.5 mm QFN.
- **jlc_4layer_advanced (CHOSEN)** — 0.25/0.15 mm vias, 0.09 mm track/space,
  via-in-pad (POFV), hole-to-hole 0.25. Proven orderable by this pipeline
  (usb-power-3s v1.0–v1.3 shipped with exactly this option for a 0.5 mm VQFN).

## Decision
`03_src/rules/nets.yaml` declares `fab_tier: jlc_4layer_advanced`.
ORDER_README must carry the tier line:
"ADVANCED option REQUIRED: min via 0.25/0.15 mm (QFN-48 0.5 mm PD SoC fanout)".

## Consequences
- Higher board cost (advanced via option) — accepted under A3, flagged in the
  final report.
- Side benefit: LM5116 HTSSOP-20 0.65 mm escape-budget wall (ADR-0008 class,
  hole-to-hole 0.5 at standard) dissolves — at 0.25 hole-to-hole, escape vias
  fit between adjacent pins.
