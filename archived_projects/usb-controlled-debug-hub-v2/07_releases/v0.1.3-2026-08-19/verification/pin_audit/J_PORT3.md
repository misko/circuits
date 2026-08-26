# pin dossier: J_PORT3  (KH-AF90DIP-112)

- footprint: usb_controlled_debug_hub:KH-AF90DIP-112_Horizontal
- board position: (111.0, 33.7) rot 180
- computed winding of pins 1..N: **CW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v2/02_parts/KH-AF90DIP-112/KH-AF90DIP-112.pdf
- part.yaml verification note: REPLACEMENT for 1001-011-01101 after the fresh-context pin review proved that part is a USB-A MALE PLUG rated 1.5A (its drawing title 'USB 4P AM SMT', current spec p.1). KH-AF90DIP-112 vendor drawing p.1 proves the female-receptacle geometry: O1.0 signal holes at 2.500/2.000/2.500 pitch and O3.0 shell holes 13.240 apart offset 2.600 forward. The exact JLC/EasyEDA C503996 library independently binds that geometry to pad 1=VCC/VBUS, 2=D-, 3=D+, 4=GND; the project footprint is the same row translated +3.49 mm with the same mouth direction and shell field. Contact rating is not stated by the vendor; disposition remains in ADR 0006.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (+0.00,+0.00) | W | 1.7x1.7 THT | VBUS | VBUS3_SW |
| 2 | (+2.50,+0.00) | N | 1.7x1.7 THT | DM | P3_PORT_N |
| 3 | (+4.50,+0.00) | N | 1.7x1.7 THT | DP | P3_PORT_P |
| 4 | (+7.00,+0.00) | E | 1.7x1.7 THT | GND | GND |
| 5 | (-3.12,+2.60) | W | 4.0x4.0 THT | SHIELD | GND |
| 5 | (+10.12,+2.60) | E | 4.0x4.0 THT | SHIELD | GND |
