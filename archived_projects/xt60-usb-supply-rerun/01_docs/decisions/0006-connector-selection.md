---
id: 0006
date: 2026-07-16
status: accepted
---
# 0006 — Connectors: XT60PW-M, XY-AF90-WJDG USB-A, HRO TYPE-C-31-M-12A

## Context

Battery packs terminate in a female XT60 pigtail, so the BOARD carries the
horizontal PCB male. USB-A THT right-angle receptacles at JLC are all
shallow-stock; the USB-C port must carry 6 A. All four connectors may be
hand-soldered (BRIEF A4).

## Options

- **XT60PW-M (Amass, C98732, 9,370 stock)** — the standard horizontal
  board male; KiCad ships AMASS_XT60PW-M footprint. XT60PW-F is 0 stock
  and the wrong gender anyway. CHOSEN. Polarity fact: in the KiCad
  footprint, pad 1 is the "-" blade (skill-verified failure); recorded in
  part.yaml and gated by the polarity audit.
- **USB-A: XY-AF90-WJDG (C53133490, 801)** — most-stocked THT right-angle
  4P option; HDGC ZD-115 (875) / ZD-113 (815) are footprint-compatible
  backups. All are <1000 stock: flagged, order-time substitution likely;
  hand-solder anyway. Listings state 1.5 A contact rating — standard for
  USB-A shells; 2.5 A/port is accepted practice on these contacts
  (dual-blade VBUS), noted as a derating caveat.
- **USB-C: HRO TYPE-C-31-M-12A (C5337088, 1,420)** — explicitly rated
  6 A/20 V, 16P hybrid SMD+TH. The plain -12 (C165948, 108,946) is the 5 A
  footprint-compatible fallback. CHOSEN (-12A). KiCad ships
  USB_C_Receptacle_HRO_TYPE-C-31-M-12 footprint.

## Decision

XT60PW-M battery input; 3x XY-AF90-WJDG USB-A; HRO TYPE-C-31-M-12A USB-C.

## Consequences

All four connectors are hand-solder items (JLC economic SMT does not place
them) — they go on the explicit hand-solder list in the release MANIFEST
and stay uncoded-or-noted in the BOM per the fab skill. USB-A 2.5 A rides a
1.5 A-rated contact pair (both VBUS blades) — accepted with derating note.
The USB-C footprint must use all 4 VBUS + 4 GND contacts for 6 A.
