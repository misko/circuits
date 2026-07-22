---
id: 0003
date: 2026-07-17
status: accepted
---
# 0003 — Sourcing: Basic/Extended tally + 0805 passive family

## Context

P2: everything in JLC stock, Basic strongly preferred, MINIMIZE UNIQUE
EXTENDED COUNT (setup fee per Extended reel), highest-stock/lowest-cost
among crosses, all SMD one side, THT connectors hand-solder. This ADR is
the explicit tally the commission requires.

## Passive family choice (D2)

Live JLC check 2026-07-17: the 0603 UNI-ROYAL 1% Basic series has stock
GAPS at exactly our values (0603WAF1001T5E 1k and 0603WAF1002T5E 10k
both stock=0; Basic-library 0603 alternatives for those values: none).
The 0805 UNI-ROYAL 0805W8F series is Basic with 0.6M–12.7M stock at
every needed value, and Basic 0805 caps exist for 100nF/1uF/22uF.
**All passives 0805** — one family, deep Basic stock, easier bench
rework on a hand-serviced instrument. (0603 would work for 100nF only;
not worth splitting the family.)

## The tally (assembled SMD lines)

**Extended, unique count = 5 (irreducible):**

| Part | LCSC | Why no Basic |
|---|---|---|
| ESP32-S3-WROOM-1-N8R2 | C2913204 | no Basic MCU modules exist |
| TYPE-C-31-M-12 USB-C | C165948 | no Basic USB-C exists |
| LM339DT | C71036 | no Basic LM339 (ADR-0002) |
| USBLC6-2SC6 (UMW) | C2687116 | no Basic USB ESD array |
| 100uF/16V SMD electrolytic | C2887276 | no Basic ≥100uF; P4 pins ≥100uF bulk |

**Basic (12 unique):** AO3400A C20917, AMS1117-3.3 C6186, TS-1187A-B-A-B
C318884, KT-0805G C2297, R 0805: 100R C17408, 1k C17513, 2.7k C17530,
4.7k C17673, 5.1k C27834, 10k C17414, 33k C17633, 100k C149504; C 0805:
100nF C49678, 1uF C28323, 22uF C45783. (15 unique lines; 12 R/C values
share two component classes.)

**Hand-solder THT (uncoded in BOM, listed in MANIFEST not_assembled):**
KF128L-3.5-2P screw terminals x9 (C474930 known, for the twin), 2.54mm
1x4 female socket x1.

Rejected cost paths: cheaper clone AO3400 (Hottech C181090, $0.03) and
UMW AMS1117 are EXTENDED — the Basic originals (C20917/C6186) win under
the minimize-unique-Extended rule even at higher unit cost.

## Decision

5 unique Extended reels, 15 Basic lines, 2 hand-solder THT items; all
SMD on the top side; passives standardized on 0805 Basic.
