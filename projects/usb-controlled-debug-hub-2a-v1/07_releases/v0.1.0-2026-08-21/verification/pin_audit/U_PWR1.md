# pin dossier: U_PWR1  (TPS259470ARPWR)

- footprint: usb_controlled_debug_hub_2a:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm
- board position: (48.0, 54.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/TPS259470ARPWR/SLVSFC9C.pdf
- part.yaml verification note: CITED: TI SLVSFC9C Table 4-1 exact TPS259470A ordering row, Figure 5-1 RPW pinout, Table 5-1 terminal functions, Figure 8-22 layout, 45mOhm catalog maximum, true RCB description, and equations 5/10/11; read 2026-08-18. JLC/LCSC C3662799 identifies exact TPS259470ARPWR.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-0.91,-0.90) | W | 0.01x0.01 | EN_UVLO | PWR_EN1 |
| 2 | (-0.91,-0.23) | W | 0.25x0.6 | OVLO | GND |
| 3 | (-0.91,+0.23) | W | 0.25x0.6 | AUXOFF | unconnected-(U_PWR1-AUXOFF-Pad3) |
| 4 | (-0.91,+0.90) | W | 0.01x0.01 | FLT | HUB_OCS2_N |
| 5 | (-0.23,+0.00) | center | 0.3x2.4 | IN | P5V_A_PROTECTED |
| 6 | (+0.26,+0.00) | center | 0.3x2.4 | OUT | VBUS1_SW |
| 7 | (+0.91,+0.90) | E | 0.01x0.01 | DVDT | unconnected-(U_PWR1-DVDT-Pad7) |
| 8 | (+0.91,+0.23) | E | 0.25x0.6 | GND | GND |
| 9 | (+0.91,-0.23) | E | 0.25x0.6 | ILM | ILIM1 |
| 10 | (+0.91,-0.90) | E | 0.01x0.01 | ITIMER | unconnected-(U_PWR1-ITIMER-Pad10) |
