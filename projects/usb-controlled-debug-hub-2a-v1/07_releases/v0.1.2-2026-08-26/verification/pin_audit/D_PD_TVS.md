# pin dossier: D_PD_TVS  (TVS2200DRVR)

- footprint: Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm_ThermalVias
- board position: (35.0, 127.0) rot 90
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/TVS2200DRVR/SLVSED5C.pdf
- part.yaml verification note: CITED: TI SLVSED5C features, Figure 6-1 bottom view and Table 6-1 pin functions, electrical table 7.6 clamp rows, and section 9.4 layout read 2026-08-20.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-0.89,-0.65) | W | 0.38x0.4 | GND | GND |
| 2 | (-0.89,+0.00) | W | 0.38x0.4 | GND | GND |
| 3 | (-0.89,+0.65) | W | 0.38x0.4 | GND | GND |
| 4 | (+0.89,+0.65) | E | 0.38x0.4 | IN | VBUS_PD |
| 5 | (+0.89,+0.00) | E | 0.38x0.4 | IN | VBUS_PD |
| 6 | (+0.89,-0.65) | E | 0.38x0.4 | IN | VBUS_PD |
| 7 | (+0.00,-0.55) | N | 0.5x0.5 THT | EXPOSED_PAD | GND |
| 7 | (+0.00,+0.00) | center | 0.5x1.6 | EXPOSED_PAD | GND |
| 7 | (+0.00,+0.00) | center | 1.0x1.6 | EXPOSED_PAD | GND |
| 7 | (+0.00,+0.55) | S | 0.5x0.5 THT | EXPOSED_PAD | GND |

(2 unnumbered paste/mechanical pads not shown)
