# pin dossier: Y_HUB  (X322524MOB4SI)

- footprint: Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm
- board position: (88.5, 55.5) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/X322524MOB4SI/X322524MOB4SI.pdf
- part.yaml verification note: CITED: exact YXC specification table on p.2 fixes 24MHz, 12pF, +/-10ppm tolerance, +/-20ppm stability and 40ohm maximum ESR; the dimension drawing on p.4 fixes the 3.2x2.5mm four-pad geometry. Exact JLC C70590 identity cross-checked 2026-08-20.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.10,+0.85) | W | 1.4x1.2 | XIN | XTAL1 |
| 2 | (+1.10,+0.85) | E | 1.4x1.2 | GND | GND |
| 3 | (+1.10,-0.85) | E | 1.4x1.2 | XOUT | XTAL2 |
| 4 | (-1.10,-0.85) | W | 1.4x1.2 | GND | GND |
