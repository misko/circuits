# Stage 1 exact-MPN two-source qualification — 2026-08-10

> Historical Stage 1 evidence: ADR-0006 later supersedes TPS2557 and adds two
> polymer capacitors plus an exact user-fit fuse. This dated matrix must not be
> treated as current release qualification until those new lines are refreshed.

Policy: every selected complex/polarity-sensitive line must have more than ten
units visible in the JLC/LCSC catalog and more than ten units at one independent
authorized distributor. Counts are dated observations for quantity-five
selection, not order promises. JLC assembly allocation is a different pool and
must still clear the uploader on order day.

## Composed result

| exact MPN | JLC/LCSC code | JLC/LCSC stock | independent pool | independent stock | result |
|---|---|---:|---|---:|---|
| TPSM63610RDFR | C7125816 | 203 | Mouser | 1,365 | pass |
| TPSM63604RDLR | C5219289 | 54 | Mouser | 810 | pass |
| TPS25810RVCR | C473913 | 307 | Mouser | 172 | pass |
| TPS2557DRBR | C130056 | 2,875 | Mouser | 8,618 | pass |
| TPS2513ADBVR | C473910 | 60 | Mouser | 3,014 | pass |
| USBLC6-2SC6 | C7519 | 27,015 | DigiKey | 53,630 | pass |
| TPD2EUSB30DRTR | C97502 | 7,240 | Mouser | 126 | pass |
| DMP3013SFV-7 | C264098 | 630 | Mouser | 42,814 | pass |
| BZT52C12-7-F | C124196 | 18,766 | Mouser | 62,837 | pass |
| SMBJ15A | C83846 | 31,849 | Mouser | 36,695 | pass |
| 35TZV100M6.3X8 | C88744 | 61,172 | Mouser | 22,039 | pass |
| USB4105-GF-A | C3020560 | 11,367 | Mouser | 471,384 | pass |
| USB1130-15-A | C5815149 | 143 | Mouser | 32,139 | pass |
| 1715022 | C3817933 | 926 | Mouser | 915 | pass |
| 3568 | C5249699 | 233 | Mouser | 119,907 | pass |
| EG1218 | C273394 | 429 | Mouser | 10,586 | pass |

Verdict: **PASS 16/16** by the composed two-pool policy.

## Evidence and interpretation

- Canonical composed gate: `06_build/cache/stage1_composed_supplier_report.{md,json}`,
  which joins every candidate-BOM row to a fresh JLC snapshot and an
  independent Mouser/DigiKey observation by exact manufacturer plus full MPN.
  It reports **COMPOSED-POOLS PASS 16/16** at two authorized pools per row.
- JLC/LCSC input: `06_build/cache/stage1_stock_check_composed.{txt,json}`, exact
  component-code lookup, dated UTC, stock floor ten and manufacturer identity.
- Mouser input: API observations retained in the gitignored session cache,
  using exact plus broad search with exact-MPN and manufacturer adjudication.
- DigiKey USBLC6 value: direct product-page observation in
  `01_docs/sourcing/manual_quotes.yaml`, consumed by the same shopping report.
- Per-distributor gaps remain visible and do not falsify the composed verdict:
  Mouser contributes 15 rows and DigiKey the remaining USBLC6 row; Amazon is
  marketplace evidence and never counts as an authorized source pool.

## Backtrack evidence

The preserved initial report has Mouser only 9/15 sourceable and exposes the
late-gate defect. AON6403 was absent, Panasonic EEEFK1V101P was below the stock
floor, and the XKB switch, HRO Type-C and AMASS XT60 were not catalogued. The
generic BZT52C12 hit also belonged to a different manufacturer. The correction
happened before schematic capture, so it cost documentation and dossier time
rather than symbol, footprint, placement and routing rework.
