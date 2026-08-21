# pin dossier: U_AGG_B  (TPS259827ONRGET)

- footprint: usb_controlled_debug_hub_2a:TI_TPS25982_RGE0024_SplitPad_ThermalVias
- board position: (159.0, 113.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/TPS259827ONRGET/SLVSEI3D.pdf
- part.yaml verification note: device table, pin table, electrical limits, circuit-breaker response, ITIMER equation and RGE mechanical drawing independently read from TI SLVSEI3D 2026-08-11

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.25,+2.00) | S | 0.25x0.8 | IN | P5V_BANK_B |
| 2 | (-0.75,+2.00) | S | 0.25x0.8 | IN | P5V_BANK_B |
| 3 | (-0.25,+2.00) | S | 0.25x0.8 | IN | P5V_BANK_B |
| 4 | (+0.25,+2.00) | S | 0.25x0.8 | GND | GND |
| 5 | (+0.75,+2.00) | S | 0.25x0.8 | GND | GND |
| 6 | (+1.25,+2.00) | S | 0.25x0.8 | EN_UVLO | P5V_BANK_B |
| 7 | (+2.00,+1.25) | E | 0.8x0.25 | ITIMER | AGG_B_TIMER |
| 8 | (+2.00,+0.75) | E | 0.8x0.25 | ILIM | AGG_B_ILIM |
| 9 | (+2.00,+0.25) | E | 0.8x0.25 | IMON | unconnected-(U_AGG_B-IMON-Pad9) |
| 10 | (+2.00,-0.25) | E | 0.8x0.25 | RETRY_DLY | GND |
| 11 | (+2.00,-0.75) | E | 0.8x0.25 | NRETRY | GND |
| 12 | (+2.00,-1.25) | E | 0.8x0.25 | LDSTRT | GND |
| 13 | (+1.25,-2.00) | N | 0.25x0.8 | PG | unconnected-(U_AGG_B-PG-Pad13) |
| 14 | (+0.75,-2.00) | N | 0.25x0.8 | GND | GND |
| 15 | (+0.25,-2.00) | N | 0.25x0.8 | dVdt | AGG_B_DVDT |
| 16 | (-0.25,-2.00) | N | 0.25x0.8 | IN | P5V_BANK_B |
| 17 | (-0.75,-2.00) | N | 0.25x0.8 | OUT | P5V_B_PROTECTED |
| 18 | (-1.25,-2.00) | N | 0.25x0.8 | OUT | P5V_B_PROTECTED |
| 19 | (-2.00,-1.25) | W | 0.8x0.25 | OUT | P5V_B_PROTECTED |
| 20 | (-2.00,-0.75) | W | 0.8x0.25 | OUT | P5V_B_PROTECTED |
| 21 | (-2.00,-0.25) | W | 0.8x0.25 | OUT | P5V_B_PROTECTED |
| 22 | (-2.00,+0.25) | W | 0.8x0.25 | OUT | P5V_B_PROTECTED |
| 23 | (-2.00,+0.75) | W | 0.8x0.25 | OUT | P5V_B_PROTECTED |
| 24 | (-2.00,+1.25) | W | 0.8x0.25 | OUT | P5V_B_PROTECTED |
| 25 | (-0.62,+0.01) | W | 1.45x2.7 | IN_PowerPAD | P5V_BANK_B |
| 26 | (+0.92,+0.01) | E | 0.85x2.7 | GND_PowerPAD | GND |

(4 unnumbered paste/mechanical pads not shown)
