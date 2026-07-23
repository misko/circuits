---
id: 0006
date: 2026-07-23
status: accepted
---
# 0006 — 1V8 LDO selection (TCR2LF18 + TLV70018 fallback)

## Context
The XU316 needs a 1.8V rail for VDDIOB18 + USB_VDD18 (~50mA). The brief names
the TCR2LF18 (Toshiba). The ledger (ldo-1v8-200ma) records the pin-compatible
TLV70018DDCR (TI, C79924) as the in-JLC-stock exact alternative.

## Options
- **TCR2LF18 (brief)** — CHOSEN as the primary MPN.
- **TLV70018DDCR** — pin-compatible fallback (SOT-23-5), used if TCR2LF18 stock
  is thin at order day.

## Decision
BOM primary: TCR2LF18. Both are SOT-23-5, fixed 1.8V, ~200mA, fed from 3V3 (not
5V — so it comes up right after 3V3 and is never the last rail, ADR-0005). If
order-day stock check fails TCR2LF18, swap to TLV70018DDCR (C79924) — a
documented drop-in, same footprint.

## Consequences
- 02_parts holds TCR2LF18 as the primary; TLV70018 is the noted alternate.
- ORDER_README lists the fallback with its LCSC code.
- No protection/topology invariant (a rail LDO).
