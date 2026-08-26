# pin dossier: U_DATA1  (FSUSB42MUX)

- footprint: Package_SO:MSOP-10_3x3mm_P0.5mm
- board position: (57.0, 44.5) rot 180
- computed winding of pins 1..N: **CW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v1/02_parts/FSUSB42MUX/FSUSB42-D_Rev3.pdf
- part.yaml verification note: MSOP pin map read from Figure 3 "10-Lead MSOP (Top-Through View)" and cross-checked against the MSOP column of the pin-description table, PDF p.2; exact FSUSB42MUX suffix cross-checked in the ordering table, PDF p.7. 2026-07-31.


Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-2.10,+1.00) | W | 1.5x0.35 | VCC | 3V3_MAIN |
| 2 | (-2.10,+0.50) | W | 1.5x0.35 | SEL | GND |
| 3 | (-2.10,+0.00) | W | 1.5x0.35 | D+ | P1_HUB_N |
| 4 | (-2.10,-0.50) | W | 1.5x0.35 | D- | P1_HUB_P |
| 5 | (-2.10,-1.00) | W | 1.5x0.35 | GND | GND |
| 6 | (+2.10,-1.00) | E | 1.5x0.35 | HSD1- | P1_PORT_P |
| 7 | (+2.10,-0.50) | E | 1.5x0.35 | HSD1+ | P1_PORT_N |
| 8 | (+2.10,+0.00) | E | 1.5x0.35 | HSD2- | unconnected-(U_DATA1-HSD2_MINUS-Pad8) |
| 9 | (+2.10,+0.50) | E | 1.5x0.35 | HSD2+ | unconnected-(U_DATA1-HSD2_PLUS-Pad9) |
| 10 | (+2.10,+1.00) | E | 1.5x0.35 | OE | DATA_OE1_N |
