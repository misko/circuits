# pin dossier: U_PD_BUCK  (TPS56637RPAR)

- footprint: usb_controlled_debug_hub:TI_RPA0010A_VQFN-HR-10_3x3mm
- board position: (50.0, 108.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v2/02_parts/TPS56637RPAR/SLVSEG1A.pdf
- part.yaml verification note: CITED: TI SLVSEG1A RPA top-view and pin table p.3, operating/electrical limits pp.4-5, 5V/6A reference Figure 17 p.18, component table p.19, and layout Figure 34 pp.24-25.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-1.36,-0.75) | W | 0.6x0.25 | EN | PD_BUCK_EN |
| 2 | (-1.36,-0.25) | W | 0.6x0.25 | FB | PD_FB |
| 3 | (-1.36,+0.25) | W | 0.6x0.25 | AGND | GND |
| 4 | (-1.36,+0.75) | W | 0.6x0.25 | PG | unconnected-(U_PD_BUCK-PG-Pad4) |
| 5 | (-0.89,+1.40) | S | 0.25x0.6 | NC | unconnected-(U_PD_BUCK-NC-Pad5) |
| 6 | (+0.41,+0.85) | S | 0.25x1.7 | SW | PD_SW |
| 7 | (+0.91,+1.40) | S | 0.25x0.6 | BOOT | PD_BOOT |
| 8 | (+0.99,-0.65) | E | 0.4x2.1 | VIN | VBUS_PD_SW |
| 8 | (+1.36,-0.75) | E | 0.8x0.25 | VIN | VBUS_PD_SW |
| 8 | (+1.36,-0.25) | E | 0.8x0.25 | VIN | VBUS_PD_SW |
| 8 | (+1.36,+0.25) | E | 0.8x0.25 | VIN | VBUS_PD_SW |
| 9 | (-0.17,-0.65) | N | 0.4x2.1 | PGND | GND |
| 10 | (-0.89,-1.40) | N | 0.25x0.6 | MODE | GND |
