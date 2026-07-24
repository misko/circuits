subject: crow-recorder-central-v2 v1.2-staging (07_releases/crow-recorder-central-v2-v1.2-2026-07-24)
date: 2026-07-24
reviewer: redteam-agent (fable-medium, layout/thermal/power-integrity lens)
context-given: release-archive-only
verdict: ORDER

All numbers below measured directly with /usr/bin/python3 + pcbnew on the
staged archive's `source/crow_recorder_central_v2.kicad_pcb`, with the sealed
v1.1 release source opened read-only as baseline. Nothing outside this file
was written.

## 1. Claimed per-pin cap distances (decoupling_fix.md) — CONFIRMED

Nearest C_c* 0V9-pad to U1 pin center, my measurement vs the claim:

| U1 pin | nearest cap (measured) | measured (mm) | claimed (mm) |
|---|---|---|---|
| 5  | C_c6  | 3.22 | 3.22 |
| 11 | C_c9  | 1.63 | 1.63 |
| 14 | C_c9  | 1.63 | 1.63 |
| 18 | C_c9  | 2.67 | 2.67 |
| 50 | C_c11 | 2.01 | 2.01 |
| 54 | C_c13 | 2.02 | 2.02 |
| 95 | C_c12 | 2.54 | 2.55 |

Only delta is pin 95, 0.01mm (rounding). Nearest-cap identities all match.
100nF C_c* population on 0V9: 13 (C_c1..C_c13), v1.1 had 8; datasheet
minimum 12 — met.

## 2. New-cap 0V9 connectivity — CONFIRMED

- `verification/drc.json`: 0 violations / 0 unconnected / 0 parity — confirmed
  by parsing the JSON (0 0 0).
- Independent check: board connectivity unrouted-ratsnest count on the staged
  board = 0. All five new caps' 0V9 pads (pad 1 in each case, net `0V9`)
  are on the connected net.
- Pad-95 tap traced end-to-end: C_c12 0V9 pad (100.01,97.18) -> (99.00,96.20)
  -> (97.90,96.20), and the endpoint lies inside U1 pad 95's copper (pad
  bbox x 96.925..98.400, y 96.075..96.325; Contains() = True). Pad 95 also
  retains its pre-existing 0.5mm In2.Cu feed (endpoint 0.04mm from pad
  center), so the 0.30mm tap is supplemental, not the sole path.

## 3. New-cap GND paths — CONFIRMED

Nearest GND via to each new cap's GND pad center:

| cap | position (mm) | layer | nearest GND via (mm) |
|---|---|---|---|
| C_c9  | (80.34,100.40) | F | 0.00 (in-pad) |
| C_c10 | (79.60, 95.50) | F | 0.00 (in-pad) |
| C_c11 | (90.50,112.15) | F | 0.50 |
| C_c12 | (100.49, 97.18)| F | 0.00 (in-pad) |
| C_c13 | (92.40,112.15) | F | 0.40 |

Three of five have via-in-pad to the plane; the other two have a stitch via
within 0.5mm. Combined with 0 unconnected and 0 DRC, ground return for every
new cap is copper-verified and short.

## 4. Survival checks vs sealed v1.1 — ALL PASS

- USB pair (both boards measured identically):
  - USB_DP: 23.621mm, USB_DN: 23.511mm, skew 0.110mm
  - width set {0.125mm} only, layer set {F.Cu} only, 0 vias on either net
  - v1.1 values byte-for-byte identical numbers — untouched.
- U1 EP thermal vias: exactly 16 GND vias in the EP window, all 0.30/0.15,
  offsets from (90,102) = x {-1.65,-0.55,0.55,1.65} x y {-1.65,-0.55,0.55,1.65}
  (clean 4x4) — matches spec.
- LV straps: U1 pads 40/43/52 nets are `unconnected-(U1-Pad40/43/52)` —
  still open, the v1.1 P0 fix survives.

## 5. Moved C_b0v9 + B.Cu feed — NO CONCERN

- C_b0v9 moved (91.80,112.30) -> (91.85,116.05), 3.75mm south (frees the slot
  C_c11/C_c13 now occupy at y=112.15). Bulk has no pin-adjacency requirement
  (ds §14) — acceptable.
- B.Cu feed measured: three 0.40mm segments (0.49 + 3.70 + 0.25mm = 4.44mm),
  landing in-pad at both ends per the segment endpoints. 0V9 via count
  23 -> 25 (+2), all 0.30/0.15 — matches the claimed 2 new vias.
- P2 (observation, no action): the bulk cap now hangs off ~4.4mm of 0.40mm
  B.Cu plus two 0.15mm-drill vias. For a bulk reservoir this added ~ nH-scale
  inductance is normal and the 13 local 100nF caps own the HF band; DC
  current through this stub is negligible. Not order-blocking.

## 6. No collateral copper changes — CONFIRMED

Per-net track+via element count diff, v1.2 minus v1.1, across ALL nets:

- `0V9`: 124 -> 139 (+15: 5 cap fanouts, 5 taps, bulk refeed, +2 vias)
- `GND`: 371 -> 377 (+6: new cap GND fanouts/stitch vias)
- `TDI`: 13 -> 12 (reroute; length 70.15 -> 70.32mm, still 1 via,
  layer split F.Cu 7/In3 5 -> F.Cu 3/In3 8 — the claimed F.Cu->In3 move)
- Every other net: zero element-count change. No unexplained copper deltas.

0V9 track-width census: v1.1 {0.35:1, 0.5:100}; v1.2 {0.3:8, 0.35:1, 0.4:6,
0.5:99}. The eight 0.30mm segments are exactly the four cap taps (pads
14/50/54/95, lengths 1.10-1.64mm, each paralleling an existing 0.5mm feed);
the 0.40mm segments are the C_b0v9 B.Cu feed + the wider tap onto the
existing F.Cu feeder. P2 (observation): 0.30mm on a core rail is below the
board's 0.5mm 0V9 norm, but these are decoupling stitch taps in parallel
with intact primary feeds, not primary current paths — ampacity is not at
risk. Not order-blocking.

## Verdict

ORDER. All six check groups pass with measured evidence; the two P2 items
are observations requiring no change.
