# pin dossier: U_AGG  (TPS259474LRPWR)

- footprint: usb_controlled_debug_hub:TI_RPW0010A_VQFN-HR-10_2x2mm_P0.45mm
- board position: (85.0, 109.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/02_parts/TPS259474LRPWR/SLVSFC9C.pdf
- part.yaml verification note: CITED: exact TPS259474L latch-off/circuit-breaker row in TI SLVSFC9C Device Comparison Table, PDF p.4; RPW 10-pin QFN top view Figure 5-1 and complete Pin Functions Table 5-1, PDF pp.5-6; independently re-read 2026-08-17. Exact JLC/LCSC C2864845 identifies TPS259474LRPWR and the compatible VQFN-HR CAD.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-0.91,-0.90) | W | 0.01x0.01 | EN_UVLO | AGG_UV |
| 2 | (-0.91,-0.23) | W | 0.25x0.6 | OVLO | AGG_OV |
| 3 | (-0.91,+0.23) | W | 0.25x0.6 | PG | unconnected-(U_AGG-PG-Pad3) |
| 4 | (-0.91,+0.90) | W | 0.01x0.01 | PGTH | GND |
| 5 | (-0.23,+0.00) | center | 0.3x2.4 | IN | P5V_REG |
| 6 | (+0.26,+0.00) | center | 0.3x2.4 | OUT | P5V_PROTECTED |
| 7 | (+0.91,+0.90) | E | 0.01x0.01 | DVDT | AGG_DVDT |
| 8 | (+0.91,+0.23) | E | 0.25x0.6 | GND | GND |
| 9 | (+0.91,-0.23) | E | 0.25x0.6 | ILM | AGG_ILIM |
| 10 | (+0.91,-0.90) | E | 0.01x0.01 | ITIMER | AGG_TIMER |
