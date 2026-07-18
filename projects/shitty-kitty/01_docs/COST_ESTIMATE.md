# COST_ESTIMATE — shitty-kitty controller PCB at 10,000 units

**Engineering estimates** (Goal 1b/1c), prepared 2026-07-17. Basis: live
JLC/LCSC qty-1 prices from the stock research cached in
`06_build/cache/adr_stock*.json`, extrapolated to 10k-reel pricing with
typical LCSC price-break curves (qty-1 -> qty-3000+ is usually -10..-20%
for ICs, -50..-70% for passives). Currency USD. These are NOT quotes;
volume pricing for the ESP32 module, TMC2209 and MPR121 should be
negotiated directly (Espressif/ADI/NXP distys) before committing.

## Shared assumptions

- Volume fab+assembly in Shenzhen (JLC or equivalent EMS at this scale).
- Panelization: board is 130 x 75 mm; 2-up panel with rails, ~0.5% fab
  scrap, ~0.3% assembly attrition on passives.
- One-time costs amortized over 10k: tooling/stencils (~$400), assembly
  programming (~$300), test-jig build (~$2500 incl bed-of-nails +
  firmware) -> ~$0.32/unit, listed as "NRE amortized".
- Functional test + firmware flash ~45 s/board on a 2-station jig.
- THT connectors machine/selective-wave soldered at volume (not
  hand-solder as in the 5-board prototype run).
- EXCLUDED: mechanics (Goal 2), enclosure, electrode foils/harness on the
  lid, 12V adapter, packaging, shipping/duties, cert (FCC/CE — WiFi module
  keeps modular cert; plan ~$15-25k NRE separately), margin.

## (b) CURRENT PCB as designed — 10,000 units

| Line | Qty/brd | Est unit @10k | Ext/brd | Notes |
|---|---|---|---|---|
| ESP32-S3-WROOM-1-N8R2 | 1 | $4.60 | $4.60 | $5.39@1; Espressif volume ~-15% |
| MPR121QR2 (cap touch) | 4 | $2.20 | $8.80 | $2.67@1; **supply risk: JLC stock 1200; 10k build needs 40k pcs — must be broker/NXP-direct sourced** |
| TMC2209-LA-T | 1 | $2.20 | $2.20 | $2.64@1 |
| LIS2DH12TR | 1 | $0.75 | $0.75 | $0.93@1 |
| AP63205WU-7 buck | 1 | $0.35 | $0.35 | |
| AMS1117-3.3 | 1 | $0.12 | $0.12 | |
| TYPE-C-31-M-12 + USBLC6 | 1+1 | $0.19 | $0.19 | |
| AOD4185 + SMBJ16A + polyfuse | 3 | — | $0.50 | input protection chain |
| L1 10uH + 2x 100uF/25V | 3 | — | $0.16 | |
| MLCC set (4x22u, 3x4.7u, ~18x100n, 1u, 22n) | ~27 | — | $0.62 | 22uF/25V dominates |
| Resistor set (0805 x ~20, 2x 0.15R 1206) | ~22 | — | $0.08 | |
| LEDs x2, tactiles x2 | 4 | — | $0.07 | |
| THT: barrel, XH-4, screw term, 2x 1x13, 1x6 | 6 | — | $0.45 | |
| **BOM subtotal** | ~95 | | **$18.9** | +/- $2 |
| PCB fab 4-layer 130x75, ENIG-free HASL | 1 | | $1.60 | ~$0.165/dm2-layer at 10k |
| SMT assembly (~90 placements) + selective THT | | | $2.10 | ~$0.02/placement + THT ops |
| Test + flash + QA | | | $0.45 | 45s, 2 stations |
| NRE amortized (stencil, jig, programming) | | | $0.32 | |
| **Total per unit (current design)** | | | **$23.4** | range **$21 – $26** |

10k-run total: ~$234k (range $210k – $260k).

## (c) OPTIMIZED PCB — 10,000+ units

Changes an engineering pass would make before volume (each with its
saving; several interact):

| # | Change | Saving/brd | Risk/cost to qualify |
|---|---|---|---|
| O1 | **2x MPR121 instead of 4** — each chip drives all 12 of its ring's electrodes (12+12 = 24 exactly); the 4-chip split only buys scan rate/per-ring multi-touch, which firmware profiling may show unnecessary | $4.40 | firmware A/B test on prototype; keeps 0x5A/0x5B straps |
| O2 | ESP32-S3-WROOM-1-**N4** (paw analysis fits 4MB/no-PSRAM after profiling) or chip-down ESP32-S3FN8 + PCB antenna | $0.60 (N4) to $2.00 (chip-down) | chip-down forfeits modular RF cert (~$20k + tuning NRE) — only worth it >=25k units |
| O3 | Re-qualify on **2-layer** after cap-sense SNR + EMC validation (ADR-0003 gate) | $0.80 | measured MPR121 noise floor must hold; guard pour redesign |
| O4 | Drop USB-C + ESD array; program/debug via the host-header UART + factory pogo pads | $0.25 | worsens field-debug UX; WiFi OTA mitigates |
| O5 | Consolidate: single status LED, AMS1117 -> SOT-89 clone, 22uF/25V -> 2x10uF/25V 1206 where DC-bias allows, delete C25/C15 dupes after bring-up data | $0.35 | spec-confirmation pass per line |
| O6 | Connector cost-down: 1x13 headers -> single FFC-24 + lid-side flex electrode sheet (also kills 24-wire hand harness in mechanics assembly) | $0.15 board-side (larger saving lives in Goal-2 mechanics labor) | flex sheet tooling ~$3k NRE |
| O7 | TMC2209 -> volume-negotiated (~$1.80) or, if StealthChop proves unnecessary next to cats (unlikely — keep), DRV8825-class clone | $0.40 | keep TMC2209 unless acoustic testing says otherwise |
| O8 | Assembly: full panel-optimized 4-up, all-SMD connector variants where available | $0.30 | |

**Optimized estimate**: BOM ~$13.5, fab $0.9 (2L) - 1.6 (4L), assembly
$1.9, test $0.45, NRE $0.35 ->
**~$17.1/unit, range $15 – $19** (conservative: O1+O2(N4)+O4+O5+O8 only,
staying 4-layer, keeps $18-20).

10k-run total optimized: ~$171k (range $150k – $190k).

## Sensitivities worth flagging

1. **MPR121 supply** is the single biggest cost AND availability lever
   (37% of the current BOM). O1 halves exposure; a qualified second
   source (e.g. CY8CMBR / AT42QT class, or ESP32-S3 native touch for a
   subset) should be bench-raced during prototype firmware work.
2. ESP32 module pricing moves with flash/PSRAM options; profile firmware
   memory early (decides O2).
3. The 4L->2L decision must be data-driven (cap-sense SNR); do not take
   O3 on faith — the sensing IS the product.
