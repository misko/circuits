# pin dossier: U_CTRL  (MCP2221A-I/ST)

- footprint: Package_SO:TSSOP-14_4.4x5mm_P0.65mm
- board position: (74.0, 76.0) rot 0
- computed winding of pins 1..N: **CCW (top view)**
- datasheet: projects/usb-controlled-debug-hub-2a-v1/02_parts/MCP2221A-I-ST/DS20005565D.pdf
- part.yaml verification note: CITED: 14-pin PDIP/SOIC/TSSOP top-view map and Table 1-1, DS20005565D pp2-4; factory bus-power and 100 mA fields from Registers 1-9/1-10, pp10-11; checked 2026-08-15.

Coordinates are FOOTPRINT-LOCAL mm, rotation undone; +y is DOWN
(so this table reads like the top view of the part on the board).

| pad | local (x,y) | side | size | function (part.yaml) | NET on board |
|---|---|---|---|---|---|
| 1 | (-2.86,-1.95) | W | 1.48x0.4 | VDD | VBUS_CTRL |
| 2 | (-2.86,-1.30) | W | 1.48x0.4 | GP0 | unconnected-(U_CTRL-GP0-Pad2) |
| 3 | (-2.86,-0.65) | W | 1.48x0.4 | GP1 | unconnected-(U_CTRL-GP1-Pad3) |
| 4 | (-2.86,+0.00) | W | 1.48x0.4 | RST | CTRL_RESET_N |
| 5 | (-2.86,+0.65) | W | 1.48x0.4 | URx | unconnected-(U_CTRL-URX-Pad5) |
| 6 | (-2.86,+1.30) | W | 1.48x0.4 | UTx | unconnected-(U_CTRL-UTX-Pad6) |
| 7 | (-2.86,+1.95) | W | 1.48x0.4 | GP2 | unconnected-(U_CTRL-GP2-Pad7) |
| 8 | (+2.86,+1.95) | E | 1.48x0.4 | GP3 | unconnected-(U_CTRL-GP3-Pad8) |
| 9 | (+2.86,+1.30) | E | 1.48x0.4 | SDA | I2C_SDA |
| 10 | (+2.86,+0.65) | E | 1.48x0.4 | SCL | I2C_SCL |
| 11 | (+2.86,+0.00) | E | 1.48x0.4 | VUSB | CTRL_VUSB_3V3 |
| 12 | (+2.86,-0.65) | E | 1.48x0.4 | D- | MGMT_N |
| 13 | (+2.86,-1.30) | E | 1.48x0.4 | D+ | MGMT_P |
| 14 | (+2.86,-1.95) | E | 1.48x0.4 | VSS | GND |
