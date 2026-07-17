---
id: 0005
date: 2026-07-16
status: accepted
---
# 0005 — Connector selection and one-sided JLC assembly

## Context

P6/P7 + A4: JST GH internal connectors, USB-C receptacle, mostly top-side
SMT, JLC assembles everything including connectors (extended parts OK).
The sealed M8/EN3 field connector lives on the enclosure harness (P6), so
the board only needs harness headers.

## Options

- **USB-C**: GCT USB4105-GF-A 16-pin top-mount (chosen) — power + USB 2.0
  pins only (all this design uses), KiCad std footprint, JLC C3020560 with
  4.5k stock, and the exact part/footprint pair was verified on the
  usb-power-3s board (twin + pin review passed). Alternatives (HRO
  TYPE-C-31-M-12) — REJECTED: equivalent electrically but would re-open
  footprint verification for no benefit.
- **Mic header**: JST GH 3-pin **horizontal** SM03B-GHS-TB (chosen) — GH
  latch survives vibration (outdoor pole mount); horizontal entry keeps the
  harness parallel to the board inside a shallow enclosure. Genuine JST
  C514175 stock is thin (40); XY clone C54582898 (1.6k stock) is the
  documented alternate — decide at order-day stock check.
- **PPS header**: JST GH 2-pin SM02B-GHS-TB (C189893, 39k stock). The
  DIFFERENT pin count from J2 is deliberate physical keying — a mic harness
  cannot land on the PPS header or vice versa.
- **All SMT, all top side** (chosen): every part including connectors is
  top-side SMT -> single JLC SMT pass, no hand-solder list at all.

## Decision

J1 = USB4105-GF-A, J2 = SM03B-GHS-TB, J3 = SM02B-GHS-TB; 100% top-side SMT;
JLC standard/extended assembly places everything.

## Consequences

- The release's not_assembled list is EMPTY by design.
- J2 sourcing (genuine vs XY clone) re-checked on order day; both share the
  KiCad SM03B footprint.
- USB-C pin map reused verbatim from the verified usb-power-3s part.yaml.
