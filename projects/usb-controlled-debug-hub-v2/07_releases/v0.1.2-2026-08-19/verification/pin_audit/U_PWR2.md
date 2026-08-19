# pin dossier: U_PWR2  (TPS259470ARPWR)

- footprint: usb_controlled_debug_hub:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm
- board position: (76.0, 54.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/02_parts/TPS259470ARPWR/SLVSFC9C.pdf
- part.yaml verification note: CITED: exact TPS259470A auto-retry/active-current-limit row, RPW pin table, 45mOhm catalog maximum, true RCB description and equations 5/10/11 in TI SLVSFC9C; read 2026-08-18. JLC/LCSC C3662799 identifies exact TPS259470ARPWR.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-0.91,-0.90) | W | 0.01x0.01 | EN_UVLO | PWR_EN2 |
| 2 | (-0.91,-0.23) | W | 0.25x0.6 | OVLO | GND |
| 3 | (-0.91,+0.23) | W | 0.25x0.6 | AUXOFF | unconnected-(U_PWR2-AUXOFF-Pad3) |
| 4 | (-0.91,+0.90) | W | 0.01x0.01 | FLT | HUB_OCS3_N |
| 5 | (-0.23,+0.00) | center | 0.3x2.4 | IN | P5V_PROTECTED |
| 6 | (+0.26,+0.00) | center | 0.3x2.4 | OUT | VBUS2_SW |
| 7 | (+0.91,+0.90) | E | 0.01x0.01 | DVDT | unconnected-(U_PWR2-DVDT-Pad7) |
| 8 | (+0.91,+0.23) | E | 0.25x0.6 | GND | GND |
| 9 | (+0.91,-0.23) | E | 0.25x0.6 | ILM | ILIM2 |
| 10 | (+0.91,-0.90) | E | 0.01x0.01 | ITIMER | unconnected-(U_PWR2-ITIMER-Pad10) |
