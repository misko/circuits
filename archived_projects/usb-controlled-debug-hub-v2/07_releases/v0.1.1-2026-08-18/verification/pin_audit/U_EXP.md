# pin dossier: U_EXP  (MCP23017T-E/SS)

- footprint: Package_SO:SSOP-28_5.3x10.2mm_P0.65mm
- board position: (123.0, 76.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: /home/mouse9911/gits/circuits/projects/usb-controlled-debug-hub-v2/02_parts/MCP23017T-E-SS/DS20001952D.pdf
- part.yaml verification note: CITED: DS20001952D Package Types figure p2 and pin description table pp14-15; SSOP map cross-checked pin-by-pin and tape/reel T-E/SS identity checked in ordering information, 2026-08-15.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-3.50,-4.22) | N | 1.9x0.4 | GPB0 | unconnected-(U_EXP-GPB0-Pad1) |
| 2 | (-3.50,-3.58) | N | 1.9x0.4 | GPB1 | unconnected-(U_EXP-GPB1-Pad2) |
| 3 | (-3.50,-2.92) | W | 1.9x0.4 | GPB2 | unconnected-(U_EXP-GPB2-Pad3) |
| 4 | (-3.50,-2.27) | W | 1.9x0.4 | GPB3 | unconnected-(U_EXP-GPB3-Pad4) |
| 5 | (-3.50,-1.62) | W | 1.9x0.4 | GPB4 | unconnected-(U_EXP-GPB4-Pad5) |
| 6 | (-3.50,-0.97) | W | 1.9x0.4 | GPB5 | unconnected-(U_EXP-GPB5-Pad6) |
| 7 | (-3.50,-0.33) | W | 1.9x0.4 | GPB6 | unconnected-(U_EXP-GPB6-Pad7) |
| 8 | (-3.50,+0.33) | W | 1.9x0.4 | GPB7 | unconnected-(U_EXP-GPB7-Pad8) |
| 9 | (-3.50,+0.97) | W | 1.9x0.4 | VDD | VBUS_CTRL |
| 10 | (-3.50,+1.62) | W | 1.9x0.4 | VSS | GND |
| 11 | (-3.50,+2.27) | W | 1.9x0.4 | NC | unconnected-(U_EXP-NC1-Pad11) |
| 12 | (-3.50,+2.92) | W | 1.9x0.4 | SCL | I2C_SCL |
| 13 | (-3.50,+3.58) | S | 1.9x0.4 | SDA | I2C_SDA |
| 14 | (-3.50,+4.22) | S | 1.9x0.4 | NC | unconnected-(U_EXP-NC2-Pad14) |
| 15 | (+3.50,+4.22) | S | 1.9x0.4 | A0 | GND |
| 16 | (+3.50,+3.58) | S | 1.9x0.4 | A1 | GND |
| 17 | (+3.50,+2.92) | E | 1.9x0.4 | A2 | GND |
| 18 | (+3.50,+2.27) | E | 1.9x0.4 | RESET_N | EXP_RESET_N |
| 19 | (+3.50,+1.62) | E | 1.9x0.4 | INTB | unconnected-(U_EXP-INTB-Pad19) |
| 20 | (+3.50,+0.97) | E | 1.9x0.4 | INTA | unconnected-(U_EXP-INTA-Pad20) |
| 21 | (+3.50,+0.33) | E | 1.9x0.4 | GPA0 | PWR_CMD1 |
| 22 | (+3.50,-0.33) | E | 1.9x0.4 | GPA1 | PWR_CMD2 |
| 23 | (+3.50,-0.97) | E | 1.9x0.4 | GPA2 | PWR_CMD3 |
| 24 | (+3.50,-1.62) | E | 1.9x0.4 | GPA3 | PWR_CMD4 |
| 25 | (+3.50,-2.27) | E | 1.9x0.4 | GPA4 | DATA_CMD1 |
| 26 | (+3.50,-2.92) | E | 1.9x0.4 | GPA5 | DATA_CMD2 |
| 27 | (+3.50,-3.58) | N | 1.9x0.4 | GPA6 | DATA_CMD3 |
| 28 | (+3.50,-4.22) | N | 1.9x0.4 | GPA7 | DATA_CMD4 |
