# ADR 0003 — accept the +200 public-catalog check for pre-layout

status: accepted
date: 2026-08-20
supersedes: ADR 0002 only for the pre-layout JLC `AVAILABLE`/economics pause

## Context

The exact quantity-five preliminary BOM has 50 machine-assembled LCSC lines.
Fresh public-catalog evidence passes 50/50 with every line satisfying
`stock >= required quantity + 200`. The four exact 3 A USB-A receptacles are
separately declared manual/consigned and are not hidden outside the population
denominator.

The normal pipeline also requests a logged-in JLC PCB-assembly availability
and economics response before placement. On 2026-08-20 the user explicitly
accepted the `+200` public-stock check as sufficient for this pre-layout
decision: “dont worry about it, the +200 check is enough”.

## Decision

Accept the fresh exact-code public-catalog receipt as the pre-layout negative
filter for this board and proceed to footprint/floorplan work without a filled
JLC PCBA response. This is a user-authorized `public-catalog` exception at the
`pre-layout` boundary only.

This decision does **not** claim JLC allocation, authorize a preorder, accept
unknown MOQ cost, or make the board orderable. The board remains
`DO-NOT-ORDER` until the final exact release BOM clears JLC's uploader-side
allocation, economics, BOM echo, rotation/polarity, THT/manual population,
stackup and fabrication previews.

## Evidence and expiry

- request: `06_build/sourcing/prelayout_request.json`
- public evidence: `06_build/sourcing/stock_check.json`
- required absolute surplus: 200 units beyond the aggregated quantity-five
  requirement on every machine-assembled LCSC line
- freshness: the readiness compositor accepts evidence no older than 24 hours
- expiry: any exact-code, per-board quantity, assembly disposition, build
  quantity, or source-circuit change requires a fresh request and stock receipt

## Consequences

- Placement may begin after the existing readiness compositor verifies the
  request, public receipt, and this decision together.
- Procurement exposure is deferred, not silently accepted.
- Final order-time JLC evidence remains mandatory and cannot use this ADR.
