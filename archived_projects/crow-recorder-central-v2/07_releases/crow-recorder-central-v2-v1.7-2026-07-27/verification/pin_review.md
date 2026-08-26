subject: crow-recorder-central-v2 v1.2-staging (07_releases/crow-recorder-central-v2-v1.2-2026-07-24)
date: 2026-07-24
reviewer: pin-review (fable-medium, zero-context delta review)
context-given: release-archive-only
verdict: PASS

# Pin review — v1.2 staged delta vs sealed v1.1

Scope: delta review of a minimal respin (5 new 0402 100nF core-decoupling caps
on 0V9/GND near U1, C_b0v9 bulk cap moved). Baseline: the full zero-context
pin review of v1.1 (08_reviews/2026-07-24_v1.1-staging_pin-review.md, PASS).
All numbers below are measured from the staged bytes:
`source/crow_recorder_central_v2.net` (sexpr-parsed, ref.pin -> net) and
`source/crow_recorder_central_v2.kicad_pcb` (loaded via /usr/bin/python3 +
pcbnew), against the v1.1 release archive and the XU316 datasheet PDF in
`02_parts/XU316-1024-TQ128-I24/` (XM-014532-PC v2.0.0).

## 1. Netlist diff v1.1 -> v1.2 (computed, pin-level)

Every (ref, pin) -> net binding compared across both `.net` files.
Result: exactly 10 node differences, all additions, nothing removed:

| ref.pin | v1.1 | v1.2 |
|---|---|---|
| C_c9.1  | (absent) | 0V9 |
| C_c9.2  | (absent) | GND |
| C_c10.1 | (absent) | 0V9 |
| C_c10.2 | (absent) | GND |
| C_c11.1 | (absent) | 0V9 |
| C_c11.2 | (absent) | GND |
| C_c12.1 | (absent) | 0V9 |
| C_c12.2 | (absent) | GND |
| C_c13.1 | (absent) | 0V9 |
| C_c13.2 | (absent) | GND |

- Refdes added: C_c9, C_c10, C_c11, C_c12, C_c13. Refdes removed: none.
- Nets added: none. Nets removed: none.
- Net-membership diff: net 0V9 gains exactly {C_c9..C_c13}.1; net GND gains
  exactly {C_c9..C_c13}.2. No other net changed membership.
- C_b0v9 has zero netlist delta (its move is placement-only, confirmed below).

The diff matches the declared respin scope exactly — nothing extra rode along.

## 2. Board pad nets for every refdes in the diff (node-for-node vs netlist)

From the staged `.kicad_pcb` via pcbnew:

| ref | footprint | value | pad1 net | pad2 net | position (mm) | dist to U1 center |
|---|---|---|---|---|---|---|
| C_c9  | C_0402_1005Metric | 100nF | 0V9 | GND | (80.34, 100.40) | 9.79 mm |
| C_c10 | C_0402_1005Metric | 100nF | 0V9 | GND | (79.60, 95.50)  | 12.26 mm |
| C_c11 | C_0402_1005Metric | 100nF | 0V9 | GND | (90.50, 112.15) | 10.16 mm |
| C_c12 | C_0402_1005Metric | 100nF | 0V9 | GND | (100.49, 97.18) | 11.54 mm |
| C_c13 | C_0402_1005Metric | 100nF | 0V9 | GND | (92.40, 112.15) | 10.43 mm |

Board pads match the netlist node-for-node for all 5 refs (10/10 nodes).
None of the 5 refs exists in the v1.1 board (asserted).

C_b0v9 (bulk): pads {1: 0V9, 2: GND} in BOTH boards (unchanged nets);
position moved (91.800, 112.300) -> (91.850, 116.050), rotation 0 -> 0.
Placement-only move, as declared.

## 3. Polarity / correctness of the connection

C_0402_1005Metric 100nF MLCC is unpolarized — pin1/pin2 orientation is
electrically irrelevant; only the net pair matters, and it is 0V9 (core VDD
rail) / GND on all 5.

Datasheet check (§14 Integration, p.29): "VDD pins for the xCORE Tile. The
VDD supply should be well decoupled at high frequencies. Place many (at least
12) 100 nF low inductance multi-layer ceramic capacitors close to the chip
between the supplies and GND." On this board VDD(core) = net 0V9 (v1.1 review
verified 0V9 on all 15 core-VDD pins). 100nF between 0V9 and GND is exactly
the mandated connection.

Count context: 100nF caps on the 0V9/GND net pair, measured from the boards —
v1.1: 9 (C_c1..C_c8 + Couth_U8), v1.2: 14 (adds C_c9..C_c13). The respin
brings the board from below to above the datasheet's "at least 12" floor.

Note (informational, no action): the 5 new caps sit 9.8–12.3 mm from U1
center, i.e. roughly 2–4 mm outside the TQ128 package edge — plausible for a
respin squeezing 0402s into a routed area, and looser than C_c1..C_c8. The
datasheet asks for "close to the chip"; these are the far end of that. Not a
pin-binding defect.

## 4. v1.1 P0 pins re-verified (LV straps)

U1 pads 40 (LV_L_N), 43 (LV_T_N), 52 (LV_R_N) in the staged board:

| pad | net (v1.2 staged) |
|---|---|
| 40 | unconnected-(U1-Pad40) |
| 43 | unconnected-(U1-Pad43) |
| 52 | unconnected-(U1-Pad52) |

All three float, matching the sanctioned fix (float = 3.3V-mode select per ds
§4.8; the ds §14 GROUND-strap requirement applies only when the corresponding
VDDIO domain is 1.8V — here VDDIOL/T/R = 3V3, so float is correct).

## 5. Full U1 pad-net compare v1.1 vs v1.2

All U1 pads compared between the two boards (130 unique pad numbers, 138 pad
objects incl. the split EP paddle — identical counts in both):
**pad-net diffs: NONE.** Every U1 pad carries the same net in v1.2 as in the
sealed v1.1, including the three floating LV straps above.

## Verdict

**PASS.** The staged v1.2 delta is exactly the declared minimal respin: 5 new
100nF 0402 caps on 0V9/GND (netlist and board agree node-for-node), one
placement-only bulk-cap move, zero other netlist or U1 pad-net changes, and
the connection is the one the XU316 datasheet §14 mandates for core-VDD
decoupling (bringing the count to 14, above the "at least 12" floor). The
three v1.1 P0 LV-strap pins remain correctly floating.
