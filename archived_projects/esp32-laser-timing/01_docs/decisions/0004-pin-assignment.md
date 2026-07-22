---
id: 0004
date: 2026-07-17
status: accepted
---
# 0004 — MCU pin assignment

## Context

P7 constraints: comparator outputs on GPIOs usable for hardware edge
timestamping (MCPWM capture or RMT input); never GPIO0/3/45/46 for
external signals; avoid GPIO19/20 (USB). On the ESP32-S3 **both MCPWM
capture and RMT inputs route through the GPIO matrix — any physical
GPIO qualifies** (S3 TRM: GPIO matrix signals; no dedicated capture
pins), so the constraint reduces to "clean, non-strapping, non-USB
GPIOs". N8R2 (quad PSRAM) leaves IO35/36/37 available but we don't
need them.

## Assignment

| Function | GPIO | Module pad | Notes |
|---|---|---|---|
| COMP1/2/3 | IO4 / IO5 / IO6 | 4 / 5 / 6 | adjacent pads → matched short traces to LM339 |
| LASER1/2/3 gate | IO7 / IO15 / IO16 | 7 / 8 / 9 | high-Z at reset; 100k pulldowns hold FETs off (P5) |
| BTN1/2/3 | IO17 / IO18 / IO21 | 10 / 11 / 23 | inputs, external 10k pullups |
| I2C SDA / SCL | IO1 / IO2 | 39 / 38 | OLED header; 4.7k pullups (P8) |
| USB D− / D+ | IO19 / IO20 | 13 / 14 | fixed function |
| BOOT | IO0 | 27 | on-board tactile only — no external signal (P7 ok) |
| EN (RESET) | EN | 3 | tactile + 10k/1uF RC |
| Power LED | — | — | hardwired to 3V3 (no GPIO spent) |

Strapping check: IO0 (tactile only), IO3/IO45/IO46 unconnected, IO46
untouched. IO15/16 double as XTAL32K — unused here, free for GPIO.
Laser gates on IO7/15/16: all default to input/high-Z at reset and have
no pull-up strapping behavior, so the 100k pulldowns guarantee
lasers-off through boot (verified against datasheet Table 4-1).

## Decision

Map as tabled; documented in README (P11) and silkscreened next to the
module. COMP inputs on IO4/5/6 satisfy P7 because capture peripherals
are matrix-routed on the S3.
