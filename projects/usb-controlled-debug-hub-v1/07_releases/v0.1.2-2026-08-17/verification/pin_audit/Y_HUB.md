# pin dossier: Y_HUB  (CX3225SB24000H0FLJCC)

- footprint: Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm
- board position: (88.5, 55.5) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v1/02_parts/CX3225SB24000H0FLJCC/cx3225sb_e.pdf
- part.yaml verification note: CITED: Kyocera CX3225SB family catalog page 1 connection top view, recommended land drawing, and ordering table; exact H0FLJCC ordering row cross-checked at LCSC C1985204, 2026-08-01.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.10,+0.85) | W | 1.4x1.2 | XIN | XTAL1 |
| 2 | (+1.10,+0.85) | E | 1.4x1.2 | GND | GND |
| 3 | (+1.10,-0.85) | E | 1.4x1.2 | XOUT | XTAL2 |
| 4 | (-1.10,-0.85) | W | 1.4x1.2 | GND | GND |
