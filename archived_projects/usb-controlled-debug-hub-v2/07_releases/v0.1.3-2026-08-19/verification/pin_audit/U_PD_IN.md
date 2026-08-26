# pin dossier: U_PD_IN  (TPS259470ARPWR)

- footprint: usb_controlled_debug_hub:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm
- board position: (46.0, 98.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v2/02_parts/TPS259470ARPWR/SLVSFC9C.pdf
- part.yaml verification note: CITED: TI SLVSFC9C Table 4-1 exact TPS259470A ordering row, Figure 5-1 RPW pinout, Table 5-1 terminal functions, Figure 8-22 layout, 45mOhm catalog maximum, true RCB description, and equations 5/10/11; read 2026-08-18. JLC/LCSC C3662799 identifies exact TPS259470ARPWR.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-0.91,-0.90) | W | 0.01x0.01 | EN_UVLO | PD_IN_UV |
| 2 | (-0.91,-0.23) | W | 0.25x0.6 | OVLO | PD_IN_OV |
| 3 | (-0.91,+0.23) | W | 0.25x0.6 | AUXOFF | unconnected-(U_PD_IN-AUXOFF-Pad3) |
| 4 | (-0.91,+0.90) | W | 0.01x0.01 | FLT | unconnected-(U_PD_IN-FAULT_N-Pad4) |
| 5 | (-0.23,+0.00) | center | 0.3x2.4 | IN | VBUS_PD |
| 6 | (+0.26,+0.00) | center | 0.3x2.4 | OUT | VBUS_PD_SW |
| 7 | (+0.91,+0.90) | E | 0.01x0.01 | DVDT | PD_IN_DVDT |
| 8 | (+0.91,+0.23) | E | 0.25x0.6 | GND | GND |
| 9 | (+0.91,-0.23) | E | 0.25x0.6 | ILM | PD_IN_ILIM |
| 10 | (+0.91,-0.90) | E | 0.01x0.01 | ITIMER | unconnected-(U_PD_IN-ITIMER-Pad10) |
