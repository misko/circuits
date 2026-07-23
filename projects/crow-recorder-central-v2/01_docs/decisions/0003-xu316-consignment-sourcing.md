---
id: 0003
date: 2026-07-23
status: accepted
---
# 0003 — XU316-1024-TQ128-I24 sourcing: consignment / global-sourcing

## Context
The SoC is spec-critical and named by the brief. The proven-parts ledger
(usb-audio-soc-xcore, provenance crow-recorder-central v1.0) records: JLC
ASSEMBLY stock is chronically 0 — the XU316 is a CONSIGNMENT / global-sourcing
line, not a JLC-stocked assembly part. This is a D-SPEC sourcing-spike outcome:
scarcity discovered at commission, not at order.

## Options
- **Substitute a JLC-stocked xcore part** — REJECTED: the brief names the
  XU316-1024-TQ128-I24 as the reference-design SoC; a substitute changes the
  USB-Audio firmware, pin map, and power domains.
- **Accept consignment / global-sourcing** — CHOSEN: order the SoC via JLC
  global sourcing (or hand-place from Digi-Key/Mouser stock) and consign it to
  the assembly. Plan it at commission so order day is not surprised.

## Decision
LCSC C6938291 on the BOM; flagged in ORDER_README as a consignment/global-source
line with an order-day stock re-check and a Digi-Key/Mouser hand-solder fallback
(0.4mm TQFP-128 is hand-solderable with hot-air + flux by a skilled operator,
but prefer JLC placement given the fine pitch — consign to their line).

## Consequences
- ORDER_README: XU316 = global-sourcing/consign, verify availability + lead time
  before committing the order; it may gate the order timeline.
- Cost/lead-time risk accepted (matches the brief's "stock must be rechecked").
