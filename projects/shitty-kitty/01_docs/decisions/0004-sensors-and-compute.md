---
id: 0004
date: 2026-07-17
status: accepted
---
# 0004 — Sensor ICs, compute, and the 5V/host budget

## Accelerometer: LIS2DH12TR (C110926) — "similar to ADXL345" (P5)

Live JLC 2026-07-17: LIS2DH12TR $0.93/9.3k stock vs LIS3DHTR $1.64/4.4k
vs ADXL345BCCZ-RL7 $4.64/1.2k (all Extended). All three: 3-axis, I2C,
±2..16g, interrupt engines — the >=20-degree tilt rule (P5) needs only
±2g static orientation at a few Hz. LIS2DH12 is the cheapest, deepest
stock, and its INT1 wakes the ESP32 on orientation change. Mounted
parallel to the lid = board plane itself (P5); axis convention noted in
ORDER_README. Rejected ADXL345: 5x price for no needed capability.

## Capacitive: 4x MPR121QR2 (C91322), addresses 0x5A-0x5D

The only real MPR121 on JLC (QFN-20 3x3, 0.4mm pitch, $2.67, 1200 stock
— covers 5-board build 60x over; the 10k-unit story is in
COST_ESTIMATE.md). All four ADDR strap options used: ADDR->GND(0x5A),
->3V3(0x5B), ->SDA(0x5C), ->SCL(0x5D). 24 electrodes = 6 per chip
(ELE0-ELE5), inner ring on U3/U4, outer on U5/U6 — spare inputs stay
unconnected (allowed per datasheet; disabled in firmware) and buy scan
speed + per-ring multi-touch. Per-chip IRQ -> own GPIO (open-drain,
10k pullup shared per datasheet: one 10k per IRQ line).

## Compute: ESP32-S3-WROOM-1-N8R2 (C2913204) + host header (A2)

Same module as esp32-laser-timing (pin map + antenna keepout facts
already verified): native USB programming via USB-C, WiFi for the app,
2MB PSRAM headroom for paw-analysis firmware. Optional host header J8
(2.54mm 1x6: 5V 5V GND GND ESP_TX ESP_RX) powers and talks to a
RaspberryPi/Arduino per P6 — UART chosen over I2C (Pi is I2C master
only; UART console doubles as the debug port; D-register D8).

## 5V budget (the "Pi budget" assumption)

AP63205WU-7 fixed-5V 2A buck (C2071056, $0.44, 32k stock): allocation
0.5A on-board (ESP32 WiFi peaks via AMS1117-3.3 + LEDs + logic) and
**1.5A budget for the host header** — enough for Pi Zero 2 W / Arduino /
ESP-only operation, NOT a Pi 4 under load (needs 3A). Flagged in
ORDER_README and silk ("HOST 5V 1.5A MAX"). Rejected: 3A buck
(TPS54331) — more externals, and the polyfuse/entry chain is sized 2A
hold; a Pi 4 host deserves its own supply.
3V3: AMS1117-3.3 (C6186, Basic) from 5V — 1A, drop 1.7V, dissipation
worst ~0.7W at ESP32 WiFi peak (SOT-223 on pour, same as laser board).
