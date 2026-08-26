# pin dossier: U_CTRL  (MCP2221A-I/SL)

- footprint: Package_SO:SOIC-14_3.9x8.7mm_P1.27mm
- board position: (74.0, 76.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-v2/02_parts/MCP2221A-I-SL/DS20005565D.pdf
- part.yaml verification note: CITED: 14-pin PDIP/SOIC/TSSOP top-view map and Table 1-1, DS20005565D pp2-4; factory bus-power and 100 mA fields from Registers 1-9/1-10, pp10-11; checked 2026-08-15.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-2.48,-3.81) | N | 1.95x0.6 | VDD | VBUS_CTRL |
| 2 | (-2.48,-2.54) | N | 1.95x0.6 | GP0 | unconnected-(U_CTRL-GP0-Pad2) |
| 3 | (-2.48,-1.27) | W | 1.95x0.6 | GP1 | unconnected-(U_CTRL-GP1-Pad3) |
| 4 | (-2.48,+0.00) | W | 1.95x0.6 | RST | CTRL_RESET_N |
| 5 | (-2.48,+1.27) | W | 1.95x0.6 | URx | unconnected-(U_CTRL-URX-Pad5) |
| 6 | (-2.48,+2.54) | S | 1.95x0.6 | UTx | unconnected-(U_CTRL-UTX-Pad6) |
| 7 | (-2.48,+3.81) | S | 1.95x0.6 | GP2 | unconnected-(U_CTRL-GP2-Pad7) |
| 8 | (+2.48,+3.81) | S | 1.95x0.6 | GP3 | unconnected-(U_CTRL-GP3-Pad8) |
| 9 | (+2.48,+2.54) | S | 1.95x0.6 | SDA | I2C_SDA |
| 10 | (+2.48,+1.27) | E | 1.95x0.6 | SCL | I2C_SCL |
| 11 | (+2.48,+0.00) | E | 1.95x0.6 | VUSB | CTRL_VUSB_3V3 |
| 12 | (+2.48,-1.27) | E | 1.95x0.6 | D- | MGMT_N |
| 13 | (+2.48,-2.54) | N | 1.95x0.6 | D+ | MGMT_P |
| 14 | (+2.48,-3.81) | N | 1.95x0.6 | VSS | GND |
