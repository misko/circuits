# ble-bus-bar firmware notes (v1.0 board)

Firmware is out of scope for the v1.0 hardware release; this file is the
hardware contract a firmware bring-up needs. Source of truth:
01_docs/DETAIL_DESIGN.md #7 + the schematic.

## Pin map (ESP32-C3)

| GPIO | Net | Function |
|---|---|---|
| IO4 | SDA | I2C to 6x INA238 @ 0x40..0x45 (100 kHz recommended on this bus) |
| IO5 | SCL | I2C clock |
| IO6 | SPI_CLK | W25Q64 log flash |
| IO7 | SPI_MOSI | W25Q64 DI |
| IO2 | SPI_MISO | W25Q64 DO (boot strap — has 10k pull-up) |
| IO10 | FLASH_CS | W25Q64 /CS (10k pull-up keeps it deselected at boot) |
| IO3 | ALERT | shared INA238 ALERT, open-drain, active low |
| IO1 | LED_ST | status LED, active high |
| IO9 | BOOT | boot button (hold low + reset for download mode) |
| IO18/IO19 | USB D-/D+ | native USB-Serial-JTAG (flash via the USB-C) |
| IO20/IO21 | RXD/TXD | debug UART on J10 (DNP header) |

## INA238 configuration

- ADCRANGE = 1 (±40.96 mV); shunt 0.5 mΩ → 2.5 mA/LSB
  (SHUNT_CAL per datasheet eq. with R = 0.0005 Ω).
- Addresses (A1,A0): U1 0x40 (GND,GND), U2 0x41 (GND,VS), U3 0x42
  (GND,SDA), U4 0x43 (GND,SCL), U5 0x44 (VS,GND), U6 0x45 (VS,VS).
- Blown-fuse detection: VBUS (tied to IN− node) collapses while current
  reads 0 → port marked "fuse open".

## Logging / brown-out

- W25Q64: 8 MB ring of 16 B/port/10 s stat records, wear-leveled.
- Flush the ring header when any INA VBUS reads < 10 V (bus dying);
  hardware UVLO turns the buck off at ≈8.25 V (ADR-0001 #5).
- BLE: advertise per-port live stats; GATT read of history pages.
