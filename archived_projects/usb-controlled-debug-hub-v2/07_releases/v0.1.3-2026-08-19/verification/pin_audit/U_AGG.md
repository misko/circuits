# pin dossier: U_AGG  (TPS259804ONRGER)

- footprint: usb_controlled_debug_hub:TI_RGE0024M_VQFN24_4x4_SplitPad_TypeVII
- board position: (85.0, 109.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v2/02_parts/TPS259804ONRGER/SLVSFR1A.pdf
- part.yaml verification note: CITED: TI SLVSFR1A device-information row for TPS259804O, RGE top view and pin table pp.4-6, absolute/electrical limits and 300-ohm ILIM row pp.8-15, programming equations and RGE0024M drawing/example land pp.21-30 and 51-53; independently re-read 2026-08-19. Exact JLC/LCSC C2878936 identifies TPS259804ONRGER and supplied the source-owned native STEP.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.91,-1.25) | W | 0.57x0.24 | IN | P5V_REG |
| 2 | (-1.91,-0.75) | W | 0.57x0.24 | IN | P5V_REG |
| 3 | (-1.91,-0.25) | W | 0.57x0.24 | IN | P5V_REG |
| 4 | (-1.91,+0.25) | W | 0.57x0.24 | GND | GND |
| 5 | (-1.91,+0.75) | W | 0.57x0.24 | GND | GND |
| 6 | (-1.91,+1.25) | W | 0.57x0.24 | EN_UVLO | P5V_REG |
| 7 | (-1.25,+1.91) | S | 0.24x0.57 | ITIMER | AGG_TIMER |
| 8 | (-0.75,+1.91) | S | 0.24x0.57 | ILIM | AGG_ILIM |
| 9 | (-0.25,+1.91) | S | 0.24x0.57 | IMON | unconnected-(U_AGG-IMON-Pad9) |
| 10 | (+0.25,+1.91) | S | 0.24x0.57 | RETRY_DLY | GND |
| 11 | (+0.75,+1.91) | S | 0.24x0.57 | NRETRY | GND |
| 12 | (+1.25,+1.91) | S | 0.24x0.57 | LDSTRT | GND |
| 13 | (+1.91,+1.25) | E | 0.57x0.24 | PG | unconnected-(U_AGG-PG-Pad13) |
| 14 | (+1.91,+0.75) | E | 0.57x0.24 | GND | GND |
| 15 | (+1.91,+0.25) | E | 0.57x0.24 | DVDT | AGG_DVDT |
| 16 | (+1.91,-0.25) | E | 0.57x0.24 | IN | P5V_REG |
| 17 | (+1.91,-0.75) | E | 0.57x0.24 | OUT | P5V_PROTECTED |
| 18 | (+1.91,-1.25) | E | 0.57x0.24 | OUT | P5V_PROTECTED |
| 19 | (+1.25,-1.91) | N | 0.24x0.57 | OUT | P5V_PROTECTED |
| 20 | (+0.75,-1.91) | N | 0.24x0.57 | OUT | P5V_PROTECTED |
| 21 | (+0.25,-1.91) | N | 0.24x0.57 | OUT | P5V_PROTECTED |
| 22 | (-0.25,-1.91) | N | 0.24x0.57 | OUT | P5V_PROTECTED |
| 23 | (-0.75,-1.91) | N | 0.24x0.57 | OUT | P5V_PROTECTED |
| 24 | (-1.25,-1.91) | N | 0.24x0.57 | OUT | P5V_PROTECTED |
| 25 | (-1.10,-0.94) | W | 0.46x0.46 THT | IN_POWERPAD | P5V_REG |
| 25 | (-1.10,-0.31) | W | 0.46x0.46 THT | IN_POWERPAD | P5V_REG |
| 25 | (+0.00,-0.94) | N | 0.46x0.46 THT | IN_POWERPAD | P5V_REG |
| 25 | (+0.00,-0.62) | N | 2.7x1.45 | IN_POWERPAD | P5V_REG |
| 25 | (+0.00,-0.31) | N | 0.46x0.46 THT | IN_POWERPAD | P5V_REG |
| 25 | (+1.10,-0.94) | E | 0.46x0.46 THT | IN_POWERPAD | P5V_REG |
| 25 | (+1.10,-0.31) | E | 0.46x0.46 THT | IN_POWERPAD | P5V_REG |
| 26 | (-1.10,+0.93) | W | 0.46x0.46 THT | GND_POWERPAD | GND |
| 26 | (+0.00,+0.93) | S | 0.46x0.46 THT | GND_POWERPAD | GND |
| 26 | (+0.00,+0.93) | S | 2.7x0.85 | GND_POWERPAD | GND |
| 26 | (+1.10,+0.93) | E | 0.46x0.46 THT | GND_POWERPAD | GND |

(2 unnumbered paste/mechanical pads not shown)
