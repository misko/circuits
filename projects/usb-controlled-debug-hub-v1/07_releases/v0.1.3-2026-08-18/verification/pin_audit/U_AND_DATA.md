# pin dossier: U_AND_DATA  (74LVC08APW,118)

- footprint: Package_SO:TSSOP-14_4.4x5mm_P0.65mm
- board position: (120.0, 86.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v1/02_parts/74LVC08APW-118/74LVC08A.pdf
- part.yaml verification note: CITED: Nexperia 74LVC08A Rev 8 pin configuration and ordering information, PDF pp2-3 and p13; checked 2026-07-31.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-2.86,-1.95) | W | 1.48x0.4 | 1A | PWR_EN1 |
| 2 | (-2.86,-1.30) | W | 1.48x0.4 | 1B | DATA_CMD1 |
| 3 | (-2.86,-0.65) | W | 1.48x0.4 | 1Y | DATA_OK1 |
| 4 | (-2.86,+0.00) | W | 1.48x0.4 | 2A | PWR_EN2 |
| 5 | (-2.86,+0.65) | W | 1.48x0.4 | 2B | DATA_CMD2 |
| 6 | (-2.86,+1.30) | W | 1.48x0.4 | 2Y | DATA_OK2 |
| 7 | (-2.86,+1.95) | W | 1.48x0.4 | GND | GND |
| 8 | (+2.86,+1.95) | E | 1.48x0.4 | 3Y | DATA_OK3 |
| 9 | (+2.86,+1.30) | E | 1.48x0.4 | 3A | PWR_EN3 |
| 10 | (+2.86,+0.65) | E | 1.48x0.4 | 3B | DATA_CMD3 |
| 11 | (+2.86,+0.00) | E | 1.48x0.4 | 4Y | DATA_OK4 |
| 12 | (+2.86,-0.65) | E | 1.48x0.4 | 4A | PWR_EN4 |
| 13 | (+2.86,-1.30) | E | 1.48x0.4 | 4B | DATA_CMD4 |
| 14 | (+2.86,-1.95) | E | 1.48x0.4 | VCC | 3V3_MAIN |
