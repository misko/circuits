# ADR-0004 — Cameras + humidity on Pi 5 native I2C

status: accepted
date: 2026-07-22

## Decision (user D2/F2, supersedes brief §3.10 bus plan)
Both MLX90640 (0x33) + both SHT45 move to Pi 5 RP1 I2C buses — up to
4 on the header via dtoverlays, one per CABLE RUN: point-to-point
buses, no branching, 0x33 conflict solved natively (brief C5 fallback
mux unnecessary). Safety unaffected: TEMP_OK comes from the thermistor
COMPARATORS, not the cameras — nothing safety-critical moves to Linux.

## The pullup / phantom-power rule (N1 — binding on the schematic)
Pi GPIO0-3 carry fixed always-on 1.8k pullups: a switched-off sensor
on such a bus gets back-fed through its clamp diodes, defeating
power-cycle recovery. Therefore: (a) use dtoverlay pin options on
GPIOs WITHOUT fixed pullups (e.g. i2c2@4/5, i2c3@6/7, i2c0@8/9,
i2c1@10/11 — clear of UART14/15); (b) bus pullups live ON CookSense,
powered from EACH SENSOR'S SWITCHED RAIL, so pullups die with the
rail. The exact pin-mux table is a Gate-4 artifact with the pin map.
Sensor rails stay CookSense-switched (via ADR-0003 expander bits);
"power-cycle sensor N" is just an expander write — no protocol needed.
