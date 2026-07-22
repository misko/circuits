# ADR-0004 — MCU + BLE + logging memory

Status: accepted 2026-07-18

## Context

P4 BLE telemetry, P5 onboard statistics memory. Commission recommends
ESP32-C3-MINI or nRF52 by stock; SPI NOR W25Q64+ for logging.

## Decisions

1. **ESP32-C3-WROOM-02-N4** (C2934560, 7163 stock, $3.26). The MINI-1
   is JLC stock-dead (all variants 0). nRF52832/40 modules carry 2–3×
   the price, and the C3 gives BLE 5.0 + native USB-Serial-JTAG
   (no UART bridge chip — flashing/debug over the USB-C) + 4 MB
   internal flash for app/OTA. The WROOM-02 footprint ships in the
   KiCad standard library (RF_Module) — one less vendored footprint to
   verify. Antenna keepout per module datasheet §3.1 honored as an
   all-layer copper keepout at the west board edge.

2. **Dedicated 8 MB SPI NOR W25Q64JVSSIQ** (C179171, 57 k stock) for
   the stats log, NOT a partition of the module's internal flash:
   P5 asks for onboard memory as a feature; a dedicated die means app
   OTA can never eat the log, wear-leveling budget is independent
   (100 k cycles × 8 MB ring ≈ years at 16 B/port/10 s), and bring-up
   can test it in isolation. SOIC-8 on the module's FSPI pins
   (IO6/IO7/IO2/IO10 — the C3's native fast-SPI set).

3. **Strap hygiene** (the C3's known trap set): IO2 (=MISO) 10 k
   pull-up (flash DO is Hi-Z until CS); IO8 10 k pull-up; IO9 boot
   button to GND; FLASH_CS 10 k pull-up so the log flash stays
   deselected through boot/strap sampling; EN 10 k + 1 µF RC + reset
   button. LEDs kept OFF strap pins (IO0/3V3 only).

4. **USB-C for flash/debug + bench power** via AMS1117-3.3 → schottky
   OR into the rail (≈3.0 V USB-only — inside every part's operating
   range, math in DETAIL_DESIGN §6). Board is fully flashable with no
   bus connected; USB can never back-power the bus.
