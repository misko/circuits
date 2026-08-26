# pin dossier: J_UP  (292304-1)

- footprint: usb_controlled_debug_hub:USB_B_TE_292304-1_Horizontal
- board position: (32.2, 57.0) rot -90
- computed winding of pins 1..N: **CW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v1/02_parts/292304-1/TE-292304-drawing-revD4.pdf
- part.yaml verification note: TE drawing ENG_CD_292304_D4 sheet 1, PC BOARD MOUNTING DIMENSIONS and front mating view; standard USB Type-B contact numbering cross-checked against the numbered mating view; TE product features checked 2026-07-31.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (+1.25,-2.00) | N | 1.7x1.7 THT | VBUS | USB_UP_VBUS |
| 2 | (-1.25,-2.00) | N | 1.7x1.7 THT | D- | UP_HUB_N |
| 3 | (-1.25,+0.00) | W | 1.7x1.7 THT | D+ | UP_HUB_P |
| 4 | (+1.25,+0.00) | E | 1.7x1.7 THT | GND | GND |
| 5 | (-6.02,+2.71) | W | 3.5x3.5 THT | SHIELD | GND |
| 5 | (+6.02,+2.71) | E | 3.5x3.5 THT | SHIELD | GND |
