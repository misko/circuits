# Fresh-context pin review: U1 = ESP32-S3-WROOM-1-N8R2

Reviewer: independent fresh-context agent, 2026-07-17.
Expected map derived directly from datasheet v1.8, Figure 3-1 "Pin Layout (Top View)" p.10
and Table 3-1 "Pin Definitions" pp.11-12 (rendered and read; NOT taken from part.yaml).

## Winding / orientation check

Datasheet Fig 3-1 (top view): antenna keepout at TOP; pin 1 at top-LEFT corner;
pins 1-14 run DOWN the left side; pins 15-26 run LEFT-to-RIGHT along the bottom
(connector-end) edge; pins 27-40 run UP the right side (IO0 at bottom-right, GND
pin 40 at top-right); pad 41 = center thermal/GND pad. Winding = CCW (top view),
14 + 12 + 14 pins per side.

Dossier (footprint-local, +y down = reads as top view): pad 1 at (-8.75,-5.26)
top-left; pads 1-14 descend the left column (y increasing); pads 15-26 at y=+12.50
bottom row with x increasing left-to-right; pads 27-40 ascend the right column;
pad 41 near center. Computed winding CCW. **Identical orientation to the figure
(not even rotated); NO mirror.** Antenna end (pads 1/40 corner) is the end away
from the pin-dense bottom edge, as in the figure. PASS.

Pin count: 40 perimeter pads + EP = 41, all present, EP on GND as required. PASS.

## Per-pad verdicts

| pad | datasheet function (Fig 3-1 / Tab 3-1) | board net | verdict | note |
|---|---|---|---|---|
| 1 | GND | GND | PASS | |
| 2 | 3V3 (power in) | 3V3 | PASS | LDO output rail |
| 3 | EN (chip enable, must not float) | EN | PASS | 10k pullup + 1uF + reset tactile = canonical EN circuit |
| 4 | IO4 (GPIO4/ADC1_CH3) | COMP1 | PASS | comparator output into GPIO input, sensible |
| 5 | IO5 (GPIO5/ADC1_CH4) | COMP2 | PASS | |
| 6 | IO6 (GPIO6/ADC1_CH5) | COMP3 | PASS | |
| 7 | IO7 (GPIO7) | LDRV1 | PASS | GPIO out -> 100R -> FET gate, sensible |
| 8 | IO15 (GPIO15/XTAL_32K_P) | LDRV2 | PASS | 32k crystal unused; plain GPIO use fine |
| 9 | IO16 (GPIO16/XTAL_32K_N) | LDRV3 | PASS | |
| 10 | IO17 (GPIO17) | BTN1_G | PASS | button input |
| 11 | IO18 (GPIO18) | BTN2_G | PASS | |
| 12 | IO8 (GPIO8) | unconnected | PASS | |
| 13 | IO19 = **USB_D-** | USB_DM | PASS | polarity correct per Table 3-1 |
| 14 | IO20 = **USB_D+** | USB_DP | PASS | polarity correct per Table 3-1 |
| 15 | IO3 (strapping: JTAG source) | unconnected | PASS | floating is the documented default-eFuse case; nothing improper attached |
| 16 | IO46 (strapping: boot msg/ROM log, internal WPD) | unconnected | PASS | floating -> internal pulldown, safe for SPI boot |
| 17 | IO9 | unconnected | PASS | |
| 18 | IO10 | unconnected | PASS | |
| 19 | IO11 | unconnected | PASS | |
| 20 | IO12 | unconnected | PASS | |
| 21 | IO13 | unconnected | PASS | |
| 22 | IO14 | unconnected | PASS | |
| 23 | IO21 (GPIO21) | BTN3_G | PASS | |
| 24 | IO47 | unconnected | PASS | |
| 25 | IO48 | unconnected | PASS | |
| 26 | IO45 (strapping: VDD_SPI voltage, internal WPD) | unconnected | PASS | floating -> pulldown -> 3.3V flash, correct for WROOM-1 |
| 27 | IO0 (strapping: boot mode, internal WPU) | BOOT | PASS | boot tactile to GND = canonical; no improper load |
| 28 | IO35 | unconnected | PASS | note: unavailable on Octal-PSRAM (R8) variants; N8R2 is quad-PSRAM so fine, and unconnected anyway |
| 29 | IO36 | unconnected | PASS | same note as pad 28 |
| 30 | IO37 | unconnected | PASS | same note as pad 28 |
| 31 | IO38 | unconnected | PASS | |
| 32 | IO39 (MTCK) | unconnected | PASS | |
| 33 | IO40 (MTDO) | unconnected | PASS | |
| 34 | IO41 (MTDI) | unconnected | PASS | |
| 35 | IO42 (MTMS) | unconnected | PASS | |
| 36 | RXD0 (U0RXD) | unconnected | WARN | no UART0 programming/debug header; acceptable because USB-Serial-JTAG on IO19/20 provides flashing + console, but there is no fallback if USB path fails |
| 37 | TXD0 (U0TXD) | unconnected | WARN | same as pad 36 |
| 38 | IO2 (GPIO2/ADC1_CH1) | SCL | PASS | matches stated IO2=SCL; 4.7k pullups present |
| 39 | IO1 (GPIO1/ADC1_CH0) | SDA | PASS | matches stated IO1=SDA |
| 40 | GND | GND | PASS | |
| 41 | EP (thermal/GND) | GND | PASS | |

## Cross-check against part.yaml (done AFTER independent derivation)

The dossier's part.yaml function column agrees with my datasheet-derived map on all
41 pads. No discrepancies.

## Summary of findings

- Winding, pin-1 corner, per-side counts, and antenna-end orientation all match the
  datasheet top view exactly; no mirror.
- USB polarity correct: pad 13 (IO19) = D- = USB_DM, pad 14 (IO20) = D+ = USB_DP.
- All four strapping pins (IO0/IO3/IO45/IO46) clean: only IO0 has anything attached
  (boot button to GND, correct).
- EN and 3V3 correct; all three GND pads incl. EP on GND.
- Two WARNs only (RXD0/TXD0 unconnected = no UART fallback for flashing); not
  order-blocking.

VERDICT: PASS
# Fresh-context pin review: U3 = LM339DT (ST quad comparator, SO-14)

Reviewer: independent agent, datasheet-first (no design-session context).
Datasheet: 02_parts/LM339DT/DocID2159Rev4.pdf, Figure 1 "Pin connections (top view)", p.3/19.
Dossier: 06_build/pin_audit/U3.md. Nets independently re-read from
04_kicad/esp32_laser_timing.kicad_pcb via pcbnew (match the dossier exactly).

## Winding / pin-1 check

Datasheet Figure 1 (SO-14, top view): pin 1 at top-left, numbers wind CCW —
1..7 down the left side, 8..14 up the right side, 7 pins per side. Dossier pad
coordinates (+y down): pin 1 at (-2.48,-3.81) top-left, 1-7 descending the left
edge, 8-14 ascending the right edge. Computed winding CCW (top view). Rotation
0, no mirror. **PASS** — matches the datasheet frame exactly.

Note: right-side input ordering read directly from the figure: 8 = Inverting
input 3, 9 = Non-inverting input 3, 10 = Inverting input 4, 11 = Non-inverting
input 4 (i.e. minus-below-plus on the right side, same as the left). The
part.yaml functions agree; no mirror-of-memory error present.

## Per-pin table (function derived from datasheet Figure 1)

| pin | datasheet function | board net | verdict | note |
|---|---|---|---|---|
| 1 | Output 2 (open-collector) | COMP2 | PASS | channel-2 output net (10k pullup to 3V3, MCU + TP) |
| 2 | Output 1 (open-collector) | COMP1 | PASS | channel-1 output net |
| 3 | VCC+ | 5V | PASS | 5V supply per common-mode requirement; C6 100n decoupler on this net (see below) |
| 4 | Inverting input 1 | VTH1 | PASS | 0.7V threshold divider on -IN, correct |
| 5 | Non-inverting input 1 | PD1 | PASS | photodiode node with +feedback on +IN, correct (hysteresis is positive) |
| 6 | Inverting input 2 | VTH2 | PASS | |
| 7 | Non-inverting input 2 | PD2 | PASS | |
| 8 | Inverting input 3 | VTH3 | PASS | |
| 9 | Non-inverting input 3 | PD3 | PASS | |
| 10 | Inverting input 4 | VTH3 | PASS | spare: -IN tied to defined 0.7V level |
| 11 | Non-inverting input 4 | GND | PASS | spare: +IN grounded; +IN < -IN so open-collector output sits low — safe defined state |
| 12 | VCC- (GND) | GND | PASS | |
| 13 | Output 4 (open-collector) | unconnected-(U3-OUT4-Pad13) | PASS | spare output intentionally floating — matches design intent; harmless for an open-collector output |
| 14 | Output 3 (open-collector) | COMP3 | PASS | |

## Channel consistency (per circuit intent)

- Comparator 1: +IN=PD1, -IN=VTH1, OUT=COMP1 — consistent triplet.
- Comparator 2: +IN=PD2, -IN=VTH2, OUT=COMP2 — consistent.
- Comparator 3: +IN=PD3, -IN=VTH3, OUT=COMP3 — consistent.
- Identity permutation (channel i on comparator i); no +/- swap anywhere, so
  the 33k feedback is positive (hysteresis) on all three channels.
- Spare (comparator 4): inputs tied (GND / VTH3), output floating — exactly as
  specified; no floating inputs.

## Decoupling

C6 = 100n (value field "100n", footprint C_0805): pad 1 = 5V, pad 2 = GND,
placed at (98.5, 81.0), ~8.5 mm from U3 at (104.0, 88.0). PASS.

## VERDICT: PASS
# Fresh-context pin review — group: U2, D1, J1, J2, SW1, SW2, Q1/Q2/Q3

Reviewer: independent agent, no design-session context. Expectations derived
directly from the datasheet PDFs in `02_parts/` (figures rendered and read),
then compared against the dossiers in `06_build/pin_audit/` and the netlist
`06_build/netlists/esp32_laser_timing.net`. Date: 2026-07-17.

---

## U2 — AMS1117-3.3, SOT-223 (SOT-223-3_TabPin2)

Datasheet: `02_parts/AMS1117-3.3/ds1117_2009-08_RoHS.pdf`, p.1.
PIN CONNECTIONS (fixed version): **1 = Ground/Adjust, 2 = VOUT, 3 = VIN**.
SOT-223 Top View figure: pins 1-2-3 left-to-right along the bottom edge, tab
on the top edge; TO-252 figure states "TAB IS OUTPUT" — tab is electrically
VOUT (pin 2). The KiCad footprint merges the tab into pad 2 — correct.

Winding: datasheet top view rotated 90° CW gives pin 1 NW, pin 2 W-mid,
pin 3 SW, tab E — exactly the dossier's pad table. Rotation only, no mirror.

| pad | datasheet function | expected net | board net | verdict |
|---|---|---|---|---|
| 1 | GND (fixed version) | GND | GND | PASS |
| 2 (W lead) | VOUT | 3V3 | 3V3 | PASS |
| 2 (E tab) | VOUT (tab is output) | 3V3 | 3V3 | PASS |
| 3 | VIN | 5V | 5V | PASS |

part.yaml pin '4' has no pad — that is the SO-8 variant's extra pin; not a
board issue for SOT-223.

**U2 VERDICT: PASS**

---

## D1 — USBLC6-2SC6, SOT-23-6

Datasheet: `02_parts/USBLC6-2SC6/UMW-USBLC6-2SC6-Nov2024.pdf`, p.1
"Pinning information": bottom row **1 = I/O1, 2 = GND, 3 = I/O2**; top row
**4 = I/O2, 5 = VBUS, 6 = I/O1**; pin-1 dot bottom-left; winding CCW.
Dossier winding CCW, pads = datasheet view rotated 90° CW (1 NW, 3 SW,
4 SE, 6 NE). Rotation only, no mirror.

| pad | datasheet function | expected net | board net | verdict |
|---|---|---|---|---|
| 1 | I/O1 (line pair 1) | one USB data net | USB_DP | PASS |
| 2 | GND | GND | GND | PASS |
| 3 | I/O2 (line pair 2) | other USB data net | USB_DM | PASS |
| 4 | I/O2 (same pair as 3) | same net as pin 3 | USB_DM | PASS |
| 5 | VBUS | 5V | 5V | PASS |
| 6 | I/O1 (same pair as 1) | same net as pin 1 | USB_DP | PASS |

D+/D- consistency through the array (netlist-verified):
- USB_DP = { D1.1, D1.6, J1.A6, J1.B6, U1.14 (IO20 = USB D+) } — connector
  D+ reaches MCU D+ through the I/O1 pair. No swap.
- USB_DM = { D1.3, D1.4, J1.A7, J1.B7, U1.13 (IO19 = USB D-) } — no swap.

**D1 VERDICT: PASS**

---

## J1 — TYPE-C-31-M-12 USB-C 16-pin receptacle

Datasheet: `02_parts/TYPE-C-31-M-12/TYPE-C-31-M-12_revA_2020-12-08.pdf`.
Contact table read from the drawing: A1=GND, A4=VBUS, A5=CC1, A6=DP1,
A7=DN1, A8=SBU1, A9=VBUS, A12=GND; B1=GND, B4=VBUS, B5=CC2, B6=DP2,
B7=DN2, B8=SBU2, B9=VBUS, B12=GND. Shell = GND.

Footprint note: the KiCad HRO footprint merges A1/B12, A4/B9, B4/A9, B1/A12
onto shared pads (dossier shows coincident coordinates) — each merged pair
is same-function (GND with GND, VBUS with VBUS) per the table, so this is
electrically correct.

| pad | datasheet function | expected net | board net | verdict |
|---|---|---|---|---|
| A1, A12, B1, B12 | GND | GND | GND | PASS |
| A4, A9, B4, B9 | VBUS | 5V | 5V | PASS |
| A5 | CC1 | CC1 + 5.1k to GND | CC1 (R1 5.1k → GND, netlist) | PASS |
| B5 | CC2 | CC2 + 5.1k to GND | CC2 (R2 5.1k → GND, netlist) | PASS |
| A6 | DP1 (D+) | USB_DP | USB_DP | PASS |
| B6 | DP2 (D+) | USB_DP | USB_DP | PASS |
| A7 | DN1 (D-) | USB_DM | USB_DM | PASS |
| B7 | DN2 (D-) | USB_DM | USB_DM | PASS |
| A8 | SBU1 | no connect | unconnected | PASS |
| B8 | SBU2 | no connect | unconnected | PASS |
| SH (x4) | SHIELD | GND | GND | PASS |

**J1 VERDICT: PASS**

---

## J2 — OLED header, generic 1x4 2.54 mm female socket

No electrical datasheet (generic socket, `02_parts/2.54-1x4P-Female/`);
expectations come from the design brief's pin order GND / VCC / SCL / SDA.

| pad | expected function | expected net | board net | verdict |
|---|---|---|---|---|
| 1 | GND | GND | GND | PASS |
| 2 | VCC | 3V3 | 3V3 | PASS |
| 3 | SCL | SCL | SCL (→ U1.38, pull-up R51) | PASS |
| 4 | SDA | SDA | SDA (→ U1.39, pull-up R50) | PASS |

WARN (assembly note, not a board error): 4-pin OLED modules exist in both
GND-VCC-SCL-SDA and VCC-GND-SCL-SDA pin orders. The board matches the brief
(GND first). Confirm the actual module purchased is the GND-first variant
before plugging in; the swapped variant would put 3V3 on the module's GND.

**J2 VERDICT: PASS** (with module-variant WARN above)

---

## SW1 / SW2 — TS-1187A-B-A-B tactile switches

Datasheet: `02_parts/TS-1187A-B-A-B/TS-1187A-X-X-X_revA0.pdf`. Circuit
diagram: **A–B internally common (one rail), C–D internally common (other
rail)**, switch contact between the rails. Top view: A/B on one edge,
C/D on the opposite edge — same-edge pads are internally shorted.
KiCad footprint numbers both pads on one edge "1" and both on the other
edge "2", i.e. pad 1 = A/B rail, pad 2 = C/D rail — pressing connects
net(1) to net(2). Requirement: the two nets must NOT sit on the same rail.

SW1:
| pad | rail | board net | verdict |
|---|---|---|---|
| 1 (W & E, north edge) | A/B rail | BOOT (→ U1.27 = IO0) | PASS |
| 2 (W & E, south edge) | C/D rail | GND | PASS |

Nets on opposite rails — press shorts BOOT to GND. Correct.

**SW1 VERDICT: PASS**

SW2:
| pad | rail | board net | verdict |
|---|---|---|---|
| 1 (W & E, north edge) | A/B rail | EN (→ U1.3, R3 10k pull-up, C1) | PASS |
| 2 (W & E, south edge) | C/D rail | GND | PASS |

Nets on opposite rails — press shorts EN to GND. Correct.

**SW2 VERDICT: PASS**

---

## Q1 / Q2 / Q3 — AO3400A, SOT-23 low-side switches

Datasheet: `02_parts/AO3400A/AO3400A_Rev3.1_2023-07.pdf`, p.1 package
figure (SOT23 Top View): **G = pin 1 (bottom-left, dot corner), S = pin 2
(bottom-right), D = pin 3 (top, alone)**. N-channel; body diode anode at
source, cathode at drain.

Dossier pad geometry (all three at rot 0): pad 1 NW, pad 2 SW, pad 3 E —
the datasheet top view rotated 90° CW. Rotation only, no mirror.

| ref | pad | datasheet function | expected net | board net | verdict |
|---|---|---|---|---|---|
| Q1 | 1 | Gate | GATE1 (R10 100R from LDRV1/MCU, R11 100k → GND) | GATE1 | PASS |
| Q1 | 2 | Source | GND | GND | PASS |
| Q1 | 3 | Drain | LSW1 (laser switched-ground, J4.2) | LSW1 | PASS |
| Q2 | 1 | Gate | GATE2 (R12 100R, R13 100k → GND) | GATE2 | PASS |
| Q2 | 2 | Source | GND | GND | PASS |
| Q2 | 3 | Drain | LSW2 (J5.2) | LSW2 | PASS |
| Q3 | 1 | Gate | GATE3 (R14 100R, R15 100k → GND) | GATE3 | PASS |
| Q3 | 2 | Source | GND | GND | PASS |
| Q3 | 3 | Drain | LSW3 (J6.2) | LSW3 | PASS |

Source on GND, drain on the switched terminal: body diode (S→D) is
reverse-biased when LSW is pulled high by the load — the FET actually
blocks when off. Pairwise symmetry across Q1/Q2/Q3 is exact (same pin →
same kind of net on every instance).

**Q1 VERDICT: PASS**
**Q2 VERDICT: PASS**
**Q3 VERDICT: PASS**

---

## Summary

| part | verdict |
|---|---|
| U2 (AMS1117-3.3) | PASS |
| D1 (USBLC6-2SC6) | PASS |
| J1 (TYPE-C-31-M-12) | PASS |
| J2 (OLED 1x4) | PASS (WARN: verify module pin-order variant) |
| SW1 (TS-1187A) | PASS |
| SW2 (TS-1187A) | PASS |
| Q1/Q2/Q3 (AO3400A) | PASS |

No FAILs. Nothing in this group blocks the order.

---
## v1.1 carry-forward note (2026-07-17)
This pin review is carried forward UNCHANGED from v1.0. v1.1 differs from
v1.0 only in silkscreen (all reference designators moved to F.SilkS) and a
single connection-width repair-nudge (613 vs 612 track segments, same 203
vias, +/-1mm copper). The NETLIST, pinout, and every pad-to-net assignment
are byte-identical (CPL identical; ERC/parity 0). No pin can have changed,
so the v1.0 zero-FAIL verdicts stand. The twin was re-run for v1.1 (U2 now
mounts via pad_alias) — see twin_report.csv.

---
## v1.2 note
Unchanged from v1.1/v1.0 — v1.2 corrects only the J1 twin-render orientation
(model_rot_z:180). Netlist/pinout/pads byte-identical; zero-FAIL verdicts stand.

---
## v1.3 note
Unchanged — v1.3 only restores J1's correct twin-render orientation (reverts
v1.2's wrong rotation override). Netlist/pads byte-identical; verdicts stand.

---
## v1.4 note
Unchanged — v1.4 is a schematic-PDF regeneration only (occlusion cleanup,
title-block rev). Netlist byte-equivalent (parity 0); verdicts stand.

---
## v1.5 note
Unchanged — schematic-PDF-only (chain wires + pitch nudges); netlist parity
0 before/after. Verdicts stand.

---
## v1.6 note
Unchanged — schematic regenerated by schwriter2 with netlist verified
node-for-node identical (parity 0). Verdicts stand.

---
## v1.7 note
Unchanged — schematic-PDF-only: GND pins now draw power-symbol ground
icons instead of global labels (engine change, schwriter2). Netlist
verified node-for-node identical (parity 0, 61 nets/214 nodes); the GND
net's membership is exactly the same, named by the icons' hidden
power_in pins. Verdicts stand.
