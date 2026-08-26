# pin dossier: J_POWER  (TYPE-C-31-M-12)

- footprint: usb_controlled_debug_hub:TYPE-C-31-M-12_Datasheet
- board position: (23.6, 105.0) rot -90
- computed winding of pins 1..N: **n/a (too few perimeter pins)**
- datasheet: /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/02_parts/TYPE-C-31-M-12/TYPE-C-31-M-12.pdf
- part.yaml verification note: CITED: exact drawing p.1 pin table, front/top views, and recommended PCB layout independently read 2026-08-18.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| A1 | (-3.20,-3.67) | W | 0.6x1.14 | GND | GND |
| A4 | (-2.40,-3.67) | W | 0.6x1.14 | VBUS | VBUS_PD_RAW |
| A5 | (-1.25,-3.67) | N | 0.3x1.14 | CC1 | PD_CC1 |
| A6 | (-0.25,-3.67) | N | 0.3x1.14 | DP1 | unconnected-(J_POWER-DP_A6-PadA6) |
| A7 | (+0.25,-3.67) | N | 0.3x1.14 | DN1 | unconnected-(J_POWER-DM_A7-PadA7) |
| A8 | (+1.25,-3.67) | N | 0.3x1.14 | SBU1 | unconnected-(J_POWER-SBU1-PadA8) |
| A9 | (+2.40,-3.67) | E | 0.6x1.14 | VBUS | VBUS_PD_RAW |
| B1 | (+3.20,-3.67) | E | 0.6x1.14 | GND | GND |
| B4 | (+2.40,-3.67) | E | 0.6x1.14 | VBUS | VBUS_PD_RAW |
| B5 | (+1.75,-3.67) | N | 0.3x1.14 | CC2 | PD_CC2 |
| B6 | (+0.75,-3.67) | N | 0.3x1.14 | DP2 | unconnected-(J_POWER-DP_B6-PadB6) |
| B7 | (-0.75,-3.67) | N | 0.3x1.14 | DN2 | unconnected-(J_POWER-DM_B7-PadB7) |
| B8 | (-1.75,-3.67) | N | 0.3x1.14 | SBU2 | unconnected-(J_POWER-SBU2-PadB8) |
| B9 | (-2.40,-3.67) | W | 0.6x1.14 | VBUS | VBUS_PD_RAW |
| SH | (-4.33,-3.10) | W | 0.9x2.0 THT | SHIELD | GND |
| SH | (-4.33,+1.08) | W | 0.9x1.7 THT | SHIELD | GND |
| SH | (+4.33,-3.10) | E | 0.9x2.0 THT | SHIELD | GND |
| SH | (+4.33,+1.08) | E | 0.9x1.7 THT | SHIELD | GND |
| A12 | (+3.20,-3.67) | E | 0.6x1.14 | GND | GND |
| B12 | (-3.20,-3.67) | W | 0.6x1.14 | GND | GND |

Declared pin aliases (review these against the manufacturer drawing):
- `A1`: schematic `1`, footprint `A1`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A12`: schematic `8`, footprint `A12`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A4`: schematic `2`, footprint `A4`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A5`: schematic `3`, footprint `A5`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A6`: schematic `4`, footprint `A6`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A7`: schematic `5`, footprint `A7`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A8`: schematic `6`, footprint `A8`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `A9`: schematic `7`, footprint `A9`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B1`: schematic `9`, footprint `B1`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B12`: schematic `16`, footprint `B12`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B4`: schematic `10`, footprint `B4`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B5`: schematic `11`, footprint `B5`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B6`: schematic `12`, footprint `B6`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B7`: schematic `13`, footprint `B7`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B8`: schematic `14`, footprint `B8`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `B9`: schematic `15`, footprint `B9`, fused: `false`; why: tscircuit assigns sequential logical pins while the manufacturer land remains alphanumeric; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1
- `SH`: schematic `17`, footprint `SH`, fused: `false`; why: tscircuit assigns sequential logical pins while the four fused shell lands retain the manufacturer SH identity; evidence: 03_tscircuit/parity_padmap.txt and exact HRO drawing p.1

(2 unnumbered paste/mechanical pads not shown)
