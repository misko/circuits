# esp32-laser-timing

Bench instrument that timestamps laser-beam interruptions from moving
shutter blades: 3 laser channels (low-side switched), 3 photodiode
channels (LM339 on the 5V rail -> clean 3.3V edges), 3 off-board
buttons, SSD1306 OLED header. ESP32-S3-WROOM-1-N8R2, native USB-C,
92x62mm 2-layer, JLC-assembled SMD top side + 10 hand-solder THT joints.

- Status: **v1.0 released** — see `07_releases/v1.0-2026-07-17/`
- Commissioned brief + decision register: `01_docs/BRIEF.md`
- Rebuild: `bash 03_src/rebuild_all.sh` (ends ERC 0 / AUDIT PASS /
  DRC `violations: 0` `unconnected: 0` `parity: 0`)
- Re-route from scratch: `03_src/route_prep.py` + `03_src/route_waves.sh`

## Final MCU pin map (P11 deliverable; also silkscreened on the board)

| Function | GPIO | Module pad | Direction | Notes |
|---|---|---|---|---|
| COMP1 (photodiode ch1) | IO4 | 4 | in | LM339 OUT1, 10k pullup to 3V3 |
| COMP2 (photodiode ch2) | IO5 | 5 | in | LM339 OUT2 |
| COMP3 (photodiode ch3) | IO6 | 6 | in | LM339 OUT3 |
| LASER1 gate | IO7 | 7 | out | 100R series, 100k pulldown — off at boot |
| LASER2 gate | IO15 | 8 | out | " |
| LASER3 gate | IO16 | 9 | out | " |
| BTN1 | IO17 | 10 | in | 10k pullup, active-low, 1k series |
| BTN2 | IO18 | 11 | in | " |
| BTN3 | IO21 | 23 | in | " |
| I2C SDA (OLED) | IO1 | 39 | i/o | 4.7k pullup |
| I2C SCL (OLED) | IO2 | 38 | out | 4.7k pullup |
| USB D− / D+ | IO19/IO20 | 13/14 | i/o | native USB via USB-C |
| BOOT | IO0 | 27 | — | on-board tactile only |
| RESET | EN | 3 | — | tactile + 10k/1uF RC |

Timestamping: on the ESP32-S3 both MCPWM capture and RMT receive route
through the GPIO matrix, so IO4/5/6 are full-capability capture inputs
(ADR-0004). Comparator polarity: beam ON (lit, node >0.7V) -> output
released -> pulled HIGH; beam interrupted -> LOW. Falling edge = active
comparator sink = fast edge.

## Terminals

| Ref | Silk | Pin 1 | Pin 2 |
|---|---|---|---|
| J4/J5/J6 | LASER 1/2/3 | 5V | switched GND (FET drain) |
| J7/J8/J9 | PHOTODIODE 1/2/3 | 5V (BPW34 cathode) | anode -> 1k load node |
| J10/J11/J12 | BUTTON 1/2/3 | IN (10k pullup) | GND |
| J2 | OLED | GND / 3V3 / SCL / SDA — **check your module's pin order!** |

## Firmware notes

Unprogrammed board: lasers OFF (100k gate pulldowns), comparators run,
LED on — safe. `05_firmware/` is empty (bench firmware is out of scope
for the v1.0 hardware release).
