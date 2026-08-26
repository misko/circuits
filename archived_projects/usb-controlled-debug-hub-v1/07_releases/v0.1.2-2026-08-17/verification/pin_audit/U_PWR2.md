# pin dossier: U_PWR2  (TPS2557DRBR)

- footprint: Package_SON:VSON-8-1EP_3x3mm_P0.65mm_EP1.65x2.4mm_ThermalVias
- board position: (76.0, 54.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v1/02_parts/TPS2557DRBR/SLVS931B.pdf
- part.yaml verification note: TI SLVS931B DRB top-view figure and pin table, printed p.3, confirm pins 1 GND, 2-3 IN, 4 active-high EN, 5 ILIM, 6-7 OUT, 8 FAULT and PowerPAD GND; electrical table and current-limit row re-read 2026-08-14.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.45,-0.97) | W | 0.85x0.35 | GND | GND |
| 2 | (-1.45,-0.33) | W | 0.85x0.35 | IN | P5V_PROTECTED |
| 3 | (-1.45,+0.33) | W | 0.85x0.35 | IN | P5V_PROTECTED |
| 4 | (-1.45,+0.97) | W | 0.85x0.35 | EN | PWR_EN2 |
| 5 | (+1.45,+0.97) | E | 0.85x0.35 | ILIM | ILIM2 |
| 6 | (+1.45,+0.33) | E | 0.85x0.35 | OUT | VBUS2_SW |
| 7 | (+1.45,-0.33) | E | 0.85x0.35 | OUT | VBUS2_SW |
| 8 | (+1.45,-0.97) | E | 0.85x0.35 | FAULT | HUB_OCS3_N |
| 9 | (-0.57,-0.95) | N | 0.5x0.5 THT | EP | GND |
| 9 | (-0.57,+0.00) | W | 0.5x0.5 THT | EP | GND |
| 9 | (-0.57,+0.95) | S | 0.5x0.5 THT | EP | GND |
| 9 | (+0.00,+0.00) | center | 1.65x2.4 | EP | GND |
| 9 | (+0.00,+0.00) | center | 1.65x2.4 | EP | GND |
| 9 | (+0.57,-0.95) | N | 0.5x0.5 THT | EP | GND |
| 9 | (+0.57,+0.00) | E | 0.5x0.5 THT | EP | GND |
| 9 | (+0.57,+0.95) | S | 0.5x0.5 THT | EP | GND |

(2 unnumbered paste/mechanical pads not shown)
