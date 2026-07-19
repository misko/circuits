# COST_ESTIMATE — ble-bus-bar v1.0 (qty 5, JLCPCB)

Board: 165 × 64 mm, 2-layer, **2 oz outer copper**, small-via option
(0.2 mm holes in the USB weave). 88 SMT placements/board (30 coded BOM
lines) + 6 hand-solder THT fuse holders. Component prices are live JLC
quotes captured 2026-07-18 (stock check run). Fab/assembly figures are
JLC-scale estimates; treat as ±20 % planning numbers, not quotes.

## Components (per board)

| Group | Qty | Unit | Ext. |
|---|---:|---:|---:|
| INA238AIDGSR (C2868250) | 6 | $2.36 | $14.18 |
| WSLP2726 0.5 mΩ shunt (C844297) | 6 | $1.12 | $6.73 |
| ESP32-C3-WROOM-02-N4 (C2934560) | 1 | $3.26 | $3.26 |
| W25Q64JVSSIQ (C179171) | 1 | $1.83 | $1.83 |
| LMR16006XDDCR (C87080) | 1 | $0.62 | $0.62 |
| USB-C, USBLC6, AMS1117, TVS ×2, SS310 ×2, B5819W, 22 µH, 2 A fuse | 10 | — | ~$1.20 |
| All passives, LEDs, buttons (0805/1206/1210) | ~57 | — | ~$1.10 |
| **Assembled subtotal** | 88 | | **~$28.9** |
| Keystone 3557-2 holders (C352820, hand-solder) | 6 | $1.44 | $8.65 |
| **Components total** | | | **~$37.6** |

Cost drivers: the 6× INA238 ($14.2 — the price of 85 V abs-max survival,
ADR-0003) and the 6× Vishay shunt + 6× Keystone holder (the
current-path quality parts). A 12 V-only cost-down variant (INA226 +
SMBJ18A clamp) would save ~$9/board.

## Order (qty 5)

| Line | Est. | Basis |
|---|---:|---|
| PCB fab 2L 2 oz 165×64, small-via option | ~$45 | 2 oz + 0.2 mm hole surcharges dominate |
| SMT assembly (88 joints ×5, ~14 extended feeders) | ~$60 | setup + feeders amortized over 5 |
| Components (5 boards + attrition) | ~$195 | table above ×5 + extended-part padding |
| **Order total (5 boards, ex shipping)** | **~$300** | ≈$60/board |

User-supplied per installed board: ATO blade fuses (≤30 A) ×6, M5
bolt/nut/washers ×1, M4 ×7, ring lugs. ~$10 hardware-store parts.
