# pin dossier: D_PD_TVS  (TVS1800DRVR)

- footprint: usb_controlled_debug_hub:TI_DRV0006A_WSON-6_2x2mm_P0.65mm
- board position: (35.0, 114.0) rot 90
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v2/02_parts/TVS1800DRVR/SLVSEV7B.pdf
- part.yaml verification note: TI SLVSEV7B electrical characteristics, pin functions, Figure 9-1/9-2 layout and DRV0006A package; read 2026-08-19. JLC/LCSC C2649846 identifies exact TVS1800DRVR.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.03,-0.65) | W | 0.61x0.36 | GND | GND |
| 2 | (-1.03,+0.00) | W | 0.61x0.36 | GND | GND |
| 3 | (-1.03,+0.65) | W | 0.61x0.36 | GND | GND |
| 4 | (+1.03,+0.65) | E | 0.61x0.36 | IN | VBUS_PD |
| 5 | (+1.03,+0.00) | E | 0.61x0.36 | IN | VBUS_PD |
| 6 | (+1.03,-0.65) | E | 0.61x0.36 | IN | VBUS_PD |
| 7 | (+0.00,+0.00) | center | 1.0x1.6 | GND_EP | GND |
