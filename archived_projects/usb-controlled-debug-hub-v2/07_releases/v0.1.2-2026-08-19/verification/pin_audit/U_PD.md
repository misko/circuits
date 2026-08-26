# pin dossier: U_PD  (CH224K)

- footprint: usb_controlled_debug_hub:WCH_CH224K_ESSOP10_EP
- board position: (41.0, 105.0) rot 90
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/02_parts/CH224K/CH224DS1_v2.1.pdf
- part.yaml verification note: CITED: exact CH224K top-view pin figure p.2, pin table pp.3-4, K reference schematic p.9, and K-specific voltage table p.9; independently read 2026-08-18.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-2.00,+3.00) | S | 0.6x1.5 | VDD | PD_VDD |
| 2 | (-1.00,+3.00) | S | 0.6x1.5 | CFG2 | PD_VDD |
| 3 | (+0.00,+3.00) | S | 0.6x1.5 | CFG3 | PD_VDD |
| 4 | (+1.00,+3.00) | S | 0.6x1.5 | DP | PD_PROTO |
| 5 | (+2.00,+3.00) | S | 0.6x1.5 | DM | PD_PROTO |
| 6 | (+2.00,-3.00) | N | 0.6x1.5 | CC2 | PD_CC2 |
| 7 | (+1.00,-3.00) | N | 0.6x1.5 | CC1 | PD_CC1 |
| 8 | (+0.00,-3.00) | N | 0.6x1.5 | VBUS | PD_VBUS_SENSE |
| 9 | (-1.00,-3.00) | N | 0.6x1.5 | CFG1 | GND |
| 10 | (-2.00,-3.00) | N | 0.6x1.5 | PG | unconnected-(U_PD-PG-Pad10) |
| 11 | (+0.00,+0.00) | center | 3.3x2.1 | GND | GND |

Declared pin aliases (review these against the manufacturer drawing):
- `0`: schematic `11`, footprint `11`, fused: `false`; why: WCH names the ESSOP exposed thermal land pin 0, while the tscircuit/KiCad package represents that physical land as the eleventh pad; evidence: CH224 manual v2.1 p.2 note 1 and table 4-2; exact WCH_CH224K_ESSOP10_EP footprint
