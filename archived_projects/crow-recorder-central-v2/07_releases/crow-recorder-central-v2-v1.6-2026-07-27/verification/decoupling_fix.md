# EXT2-F1 fix evidence — XU316 core (0V9) decoupling to vendor minimum (v1.2)

Requirement (verified at source, not reviewer-claimed): XU316-1024-TQ128
datasheet XM-014532-PC-2.0.0 (02_parts/XU316-1024-TQ128-I24/), §14
"Integration" p.29: "The VDD supply should be well decoupled at high
frequencies. Place many (at least 12) 100 nF low inductance multi-layer
ceramic capacitors close to the chip between the supplies and GND."
Checklist §H.2 p.92 repeats multiple-per-supply + >=10uF bulk.

## Netlist diff, sealed v1.1 source vs this archive's source (measured)

- net `0V9`: ADDED [('C_c10', '1'), ('C_c11', '1'), ('C_c12', '1'), ('C_c13', '1'), ('C_c9', '1')] REMOVED []
- net `GND`: ADDED [('C_c10', '2'), ('C_c11', '2'), ('C_c12', '2'), ('C_c13', '2'), ('C_c9', '2')] REMOVED []
- nets changed: 2; net-name set diff: NONE
- 100nF C_c* caps on 0V9 in this archive: 13 (['C_c1', 'C_c10', 'C_c11', 'C_c12', 'C_c13', 'C_c2', 'C_c3', 'C_c4', 'C_c5', 'C_c6', 'C_c7', 'C_c8', 'C_c9']) — v1.1 had 8; datasheet minimum 12.

## Per-core-VDD-pin nearest 100nF (0V9-pad to pin center, measured on the archived board)

| U1 pin | nearest cap | dist (mm) | v1.1 dist (mm) |
|---|---|---|---|
| 5 | C_c6 | 3.22 | 3.22 |
| 11 | C_c9 | 1.63 | 3.50 |
| 14 | C_c9 | 1.63 | 2.99 |
| 18 | C_c9 | 2.67 | 2.88 |
| 39 | C_c1 | 2.68 | 2.68 |
| 45 | C_c1 | 2.28 | 2.28 |
| 50 | C_c11 | 2.01 | 3.51 |
| 54 | C_c13 | 2.02 | 3.90 |
| 68 | C_c4 | 2.47 | 2.47 |
| 85 | C_c7 | 2.94 | 2.94 |
| 95 | C_c12 | 2.55 | 2.94 |
| 104 | C_c3 | 3.05 | 3.05 |
| 105 | C_c3 | 2.78 | 2.78 |
| 106 | C_c3 | 2.55 | 2.54 |
| 113 | C_c3 | 2.57 | 2.57 |

Worst-case pin-to-nearest-cap: 3.22mm (pin 5, unchanged nearest C_c6; the
pin-5 pocket cap C_c10 lands its 0V9 pad directly on the existing 0.5mm 0V9
F.Cu feeder 3.6mm from the pin). Pins 50/54 improved 3.51/3.90 -> 2.01/2.02
via the C_b0v9 bulk slot swap (bulk has no pin-adjacency requirement, ds §14;
it moved 3.75mm south with a 0.4mm B.Cu feed + 2 vias, in-pad at both ends).

GND sides: F.Cu GND pour (C_c11 FULL zone connection, pad_overrides) +
In1/In4 plane stitch vias per the stitch pass; board-wide filled+capped vias.

Survival (measured on this archive): USB pair 23.621/23.511mm skew 0.110mm
all 0.125mm F.Cu 0 vias; U1 EP 16x 0.30/0.15 GND vias (4x4); LV straps U1
pads 40/43/52 unconnected. DRC 0/0/0 standalone (drc.json).

## Per-cap loop geometry (both generations, measured on this archive)

| cap | gen | nearest core-VDD pin | d(0V9 pad -> pin) mm | d(GND pad -> GND via) mm | d(that via -> EP field) mm |
|---|---|---|---|---|---|
| C_c1 | v1.1 | 45 | 2.28 | 0.00 | 8.16 |
| C_c2 | v1.1 | 18 | 2.88 | 0.00 | 7.89 |
| C_c3 | v1.1 | 106 | 2.55 | 0.00 | 8.17 |
| C_c4 | v1.1 | 68 | 2.47 | 0.00 | 9.38 |
| C_c5 | v1.1 | 18 | 4.47 | 0.00 | 8.45 |
| C_c6 | v1.1 | 5 | 3.22 | 0.00 | 8.45 |
| C_c7 | v1.1 | 85 | 2.94 | 0.00 | 9.38 |
| C_c8 | v1.1 | 54 | 3.90 | 0.41 | 9.27 |
| C_c9 | v1.2-new | 14 | 1.63 | 0.00 | 8.49 |
| C_c10 | v1.2-new | 5 | 3.63 | 0.00 | 9.78 |
| C_c11 | v1.2-new | 50 | 2.01 | 0.50 | 9.27 |
| C_c12 | v1.2-new | 95 | 2.55 | 0.00 | 9.84 |
| C_c13 | v1.2-new | 54 | 2.02 | 0.40 | 9.26 |

Reading: the five v1.2 caps sit AT or TIGHTER than the v1.1 population on the
pad-to-served-pin metric (1.63-3.63mm vs 2.28-4.47mm) with ground returns
via-in-pad (0.00mm) or <=0.50mm into the In1/In4 planes. The via->EP-field
column is a plane-spreading distance, uniform across generations (the return
current flows in the solid GND planes, not point-to-point). Distance from U1
CENTER (9.8-12.3mm) is not a loop metric on a 14x14mm package whose pin rows
sit ~7.7mm from center.
