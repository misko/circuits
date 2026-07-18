# COST_ESTIMATE — shitty-kitty controller PCB (Goal 1b / 1c)

Board: 130.2 x 75.2 mm, 4-layer. 72 SMT placements/board (27 unique assembled
lines: 13 JLC-Basic, 14 Extended) + 6 hand-solder THT connectors.
Component prices below are LIVE JLC quotes captured 2026-07-18
(06_build/cache/stock_priced.json). Fab/assembly figures are JLC-scale
estimates at the stated volume; treat as ±20% planning numbers, not quotes.

## Anchor: current bill of materials (per board)

| Group | Qty | Unit (live) | Ext. |
|---|---:|---:|---:|
| ESP32-S3-WROOM-1-N8R2 (C2913204) | 1 | $5.383 | $5.383 |
| MPR121QR2 x4 (C91322) | 4 | $2.667 | $10.669 |
| TMC2209-LA-T (C2150710) | 1 | $2.637 | $2.637 |
| LIS2DH12TR (C110926) | 1 | $0.926 | $0.926 |
| AP63205 buck, AMS1117 LDO, AOD4185 FET, USBLC6, SMBJ16A TVS, polyfuse, 10uH, USB-C | 8 | — | $1.386 |
| 100u polymer x2, 75k x4, 0.15R x2, + all Basic passives (0402/0805 R/C, LEDs, tact) | ~55 | — | ~$3.15 |
| **Assembled components subtotal** | 72 | | **$24.54** |

The **4x MPR121 = $10.67 (43% of component cost)** and the **ESP32 = $5.38**
are the two cost drivers. Everything else is < $1.50 combined for passives.

---

## Goal 1b — CURRENT PCB, 10,000 units

At 10k, Extended-part feeder setup fees (14 x ~$3) amortize to ~$0.004/board
and volume price breaks apply (~25-35% off the quotes above for the ICs).

| Line item | $/board @ 10k | Basis |
|---|---:|---|
| Components (volume-adjusted) | ~$16.60 | ESP32 ~$3.80, 4x MPR121 ~$7.20, TMC2209 ~$1.90, LIS2DH12 ~$0.70, rest ~$3.00 |
| PCB fab (4L, 98 cm², panelized) | ~$1.20 | JLC 4-layer @ 10k, ~6-up panel |
| SMT assembly (72 joints, 1-side) | ~$0.55 | per-joint + amortized setup/feeders |
| THT connectors (6 parts) | ~$0.60 | barrel, 2x1x13, XH-4, screw term, 1x6 |
| THT hand-solder labor | ~$0.40 | 6 through-hole parts, hand/selective |
| **Current total** | **~$19.35/board** | |

10k build ≈ **$193,500** (± ~20%). Non-recurring: ~$400 stencil/setup,
feeder loads, first-article — negligible per-unit at this volume.

---

## Goal 1c — OPTIMIZED PCB, 10,000+ units

Design + sourcing changes, largest-lever first:

1. **2x MPR121 instead of 4** (biggest single win). 24 electrodes (12 inner +
   12 outer) need only 2x 12-channel MPR121 — the current design runs 4 chips
   at 6 channels each (half capacity; the brief said "4x MPR121" but 2 fully
   cover 24 electrodes). Removing 2 chips saves ~$3.60/board @ 10k and frees
   board area, 2 IRQ GPIOs, and 8 decoupling/REXT parts. (Trade-off: fewer
   chips = each handles a full ring; if per-ring channel isolation or spare
   channels are wanted, keep 3. Recorded as D11.)
2. **Direct/volume MPR121 sourcing** (NXP tape-and-reel or broker) at 10k+
   drops the remaining 2x from ~$1.80 to ~$1.20 each: ~$1.20/board more.
3. **ESP32-S3-MINI-1 or bare ESP32-S3 + module-free** where the antenna
   keep-out allows — MINI-1 ~$3.20 @ 10k saves ~$0.60. (Keep WROOM if the
   larger PCB antenna margin matters.)
4. **THT -> SMD / wave-friendly connectors** (SMD barrel, SMD XH, or a single
   combined edge connector) removes the hand-solder step: ~$0.40 labor +
   handling saved, and enables full 1-pass reflow.
5. **Basic-ify remaining Extended passives** (0.15R sense, 75k REXT, 100u
   polymer -> Basic equivalents) removes feeder fees and ~$0.10/board.
6. **Panel/fab**: dedicated 6-8-up panel + volume 4L run -> ~$0.90/board.

| Line item | $/board @ 10k (optimized) |
|---|---:|
| Components (2x MPR121, MINI-1, sourced) | ~$12.40 |
| PCB fab (4L, panelized) | ~$0.90 |
| SMT assembly (fewer parts, 1-pass, no THT) | ~$0.45 |
| Connectors (SMD) | ~$0.45 |
| **Optimized total** | **~$14.20/board** |

10k optimized build ≈ **$142,000** — ~27% below the current design, driven
almost entirely by halving the MPR121 count and eliminating the hand-solder
THT step. Beyond 10k the ESP32 + MPR121 volume breaks continue; at 50-100k a
custom cap-sense ASIC or a single higher-channel controller is the next lever.

## Notes / caveats
- Prices are JLC library quotes 2026-07-18; a turnkey CM (or NXP/Espressif
  direct at 10k+) will differ. Re-quote at order time.
- The 4x->2x MPR121 change is the dominant optimization and is electrically
  sound for 24 electrodes; it is a DESIGN change (new schematic/layout), not a
  drop-in — out of scope for the v1.0 release but flagged for the next spin.
