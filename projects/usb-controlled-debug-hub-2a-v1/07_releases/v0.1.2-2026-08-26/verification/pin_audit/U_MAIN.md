# pin dossier: U_MAIN  (AP63203QWU-7)

- footprint: Package_TO_SOT_SMD:TSOT-23-6
- board position: (66.0, 123.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/AP63203QWU-7/AP63200Q-AP63205Q.pdf
- part.yaml verification note: exact automotive AP63200Q/AP63201Q/AP63203Q/AP63205Q datasheet DS43698 top-view pin assignment and pin table, pp.1 and 6; AP63203QWU-7 orderable row p.28, 2026-08-01

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.14,-0.95) | W | 1.32x0.6 | FB | 3V3_MAIN |
| 2 | (-1.14,+0.00) | W | 1.32x0.6 | EN | VBUS_PD_PROTECTED |
| 3 | (-1.14,+0.95) | W | 1.32x0.6 | VIN | VBUS_PD_PROTECTED |
| 4 | (+1.14,+0.95) | E | 1.32x0.6 | GND | GND |
| 5 | (+1.14,+0.00) | E | 1.32x0.6 | SW | SW_3V3 |
| 6 | (+1.14,-0.95) | E | 1.32x0.6 | BST | BST_3V3 |
