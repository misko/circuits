# pin dossier: U_PD_IN  (TPS16630PWPR)

- footprint: Package_SO:Texas_PWP0020A
- board position: (52.0, 117.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/TPS16630PWPR/SLVSET9G.pdf
- part.yaml verification note: CITED: TI SLVSET9G device table, Figures 5-1/5-2, Table 5-1, limits, programming equations 11-13 and layout section read 2026-08-20.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-2.97,-2.92) | W | 1.78x0.42 | IN | VBUS_PD |
| 2 | (-2.97,-2.27) | W | 1.78x0.42 | IN | VBUS_PD |
| 3 | (-2.97,-1.62) | W | 1.78x0.42 | NC | unconnected-(U_PD_IN-NC1-Pad3) |
| 4 | (-2.97,-0.97) | W | 1.78x0.42 | NC | unconnected-(U_PD_IN-NC2-Pad4) |
| 5 | (-2.97,-0.33) | W | 1.78x0.42 | NC | unconnected-(U_PD_IN-NC3-Pad5) |
| 6 | (-2.97,+0.33) | W | 1.78x0.42 | P_IN | VBUS_PD |
| 7 | (-2.97,+0.97) | W | 1.78x0.42 | UVLO | PD_IN_UV |
| 8 | (-2.97,+1.62) | W | 1.78x0.42 | OVP | PD_IN_OV |
| 9 | (-2.97,+2.27) | W | 1.78x0.42 | GND | GND |
| 10 | (-2.97,+2.92) | W | 1.78x0.42 | dVdT | PD_IN_DVDT |
| 11 | (+2.97,+2.92) | E | 1.78x0.42 | ILIM | PD_IN_ILIM |
| 12 | (+2.97,+2.27) | E | 1.78x0.42 | MODE | GND |
| 13 | (+2.97,+1.62) | E | 1.78x0.42 | SHDN | VBUS_PD |
| 14 | (+2.97,+0.97) | E | 1.78x0.42 | IMON | unconnected-(U_PD_IN-IMON-Pad14) |
| 15 | (+2.97,+0.33) | E | 1.78x0.42 | FLT | unconnected-(U_PD_IN-FLT-Pad15) |
| 16 | (+2.97,-0.33) | E | 1.78x0.42 | PGOOD | unconnected-(U_PD_IN-PGOOD-Pad16) |
| 17 | (+2.97,-0.97) | E | 1.78x0.42 | NC | unconnected-(U_PD_IN-NC4-Pad17) |
| 18 | (+2.97,-1.62) | E | 1.78x0.42 | OUT | VBUS_PD_PROTECTED |
| 19 | (+2.97,-2.27) | E | 1.78x0.42 | OUT | VBUS_PD_PROTECTED |
| 20 | (+2.97,-2.92) | E | 1.78x0.42 | NC | unconnected-(U_PD_IN-NC5-Pad20) |
| 21 | (+0.00,+0.00) | center | 3.0x4.2 | PowerPAD | GND |

(4 unnumbered paste/mechanical pads not shown)
