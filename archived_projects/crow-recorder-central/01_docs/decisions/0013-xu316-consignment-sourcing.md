# ADR-0013 — T1: XU316 (U1) sourcing = JLC consignment / global-sourcing line

Status: accepted 2026-07-21 (resolves BRIEF spec tension T1)

## Context — live stock, re-measured this session

jlc_stock_check.py against the live JLC parts API, 2026-07-21 (evidence
row copy: 06_build/cache/tension_stock_2026-07-21.csv):

| Code | Part | JLC stock | Price |
|---|---|---|---|
| C6938291 | XU316-1024-TQ128-**I24** (industrial, the spec part) | **0** (expand listing exists) | $25.19 |
| C6362698 | XU316-1024-TQ128-**C24** (commercial 0..70C alternate) | **10** | $21.51 |

Same result as the commission spike (2026-07-21) and the archive's finding
(2026-07-18): the I-grade part is a zero-stock JLC extended listing. There
is no substitute for the function (the XU316 IS the product's compute; the
package is fixed by the commission).

## Decision — the archive's SHIPPED approach, adopted

The BOM line for U1 **stays CODED as C6938291** so JLC's
consignment / global-sourcing flow can populate it. Order-day ladder:

1. **JLC global sourcing / consignment** of C6938291 (the listing exists;
   JLC quotes lead time at order). This is how the sealed archive release
   shipped the line.
2. If consign is refused or slow: **Digi-Key / XMOS direct** purchase +
   consign the reel to JLC, or hand-reflow (TQFP-128 0.4mm + EP:
   hot-air/paste, NOT iron-only).
3. C6362698 (C-grade, stock 10 today) is **NOT a drop-in resolution**: it
   narrows the temperature envelope to 0..70C, a SPEC change only the user
   can approve. Recorded as an order-day option to raise with the user if
   1-2 both stall; stock 10 covers qty 5 but is below the 5x floor anyway.

## Consequence

- ORDER_README carries the consign section (as the archive's did) and the
  first-order stock re-check includes C6938291 + C6362698.
- Cost: ~$25-30/board for the XU316 line plus consign handling — already
  inside the BRIEF T4 cost headline.
- jlc_stock_check on the full BOM will report this line LOW_STOCK(0); that
  finding is ADJUDICATED BY THIS ADR (designated consign line), not a gate
  failure.
