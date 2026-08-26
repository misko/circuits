# cooksense ↔ Raspberry Pi 5 pin map — MAINTAINED GATE ARTIFACT (D3/T4, ADR-0010)

Ships in every release. Any J_PI change MUST update this file + the E-INV
assertions (electrical_invariants.yaml, adr 0010) in the same commit.
Verified against the RP1 peripherals datasheet (RP-008370) function-select
table and raspberrypi/linux rpi-6.6.y overlay sources, 2026-07-24.

## 40-pin header (v1.2)

| phys | GPIO | net | function |
|---|---|---|---|
| 1,2,4,17 | — | NC | Pi power pins — NOT a power source (brief §3) |
| 3 | 2 | I2C_SDA | I2C1 SDA — MCP23017 (0x20) |
| 5 | 3 | I2C_SCL | I2C1 SCL |
| 6,9,14,20,25,30,34,39 | — | GND | shared signal ground |
| 7 | 4 | SDA_A | I2C2 SDA — bus A: MLX90640 A (0x33) + ambient SHT45 (0x44) |
| 8 | 14 | SDA_B | I2C3 SDA — bus B: MLX90640 B (0x33) + exhaust SHT45 (0x44) |
| 10 | 15 | SCL_B | I2C3 SCL |
| 11 | 17 | WD_PET | watchdog pet (TPS3823 WDI) |
| 12 | 18 | — | NC (freed by v1.2 remap) |
| 13 | 27 | INT_ALERT | expander INTA |
| 15 | 22 | HOST_AUTH | host authorization (100k PD) |
| 16 | 23 | MCU_RELAY_ENABLE | relay enable (100k PD) |
| 18 | 24 | — | NC (freed) |
| 19 | 10 | SPI_MOSI | SPI0 MOSI |
| 21 | 9 | SPI_MISO | SPI0 MISO |
| 22 | 25 | TC_DRDY_N | MAX31856 DRDY |
| 23 | 11 | SPI_SCLK | SPI0 SCLK |
| 24 | 8 | ADC_CS_N | SPI0 CE0 — MCP3208 |
| 26 | 7 | TC_CS_N | SPI0 CE1 — MAX31856 |
| 27,28 | 0,1 | NC | HAT ID (reserved) |
| 29 | 5 | SCL_A | I2C2 SCL (was KEY_DATA in ≤v1.1) |
| 31 | 6 | KEY_CLOCK | 595 SRCLK |
| 32 | 12 | KEY_LATCH | 595 RCLK request (hardware-frozen while PRESS_TIMED high) |
| 33 | 13 | KEY_RESET_N | 595 SRCLR̄ (100k PD → cleared at boot) |
| 35 | 19 | — | NC (freed) |
| 36 | 16 | KEY_DATA | 595 SER (re-homed from phys 29) |
| 37 | 26 | STOP_REQ | DIRECT stop request (100k PD) — clears PRESS, disables decoders, drives K_STOP |
| 38 | 20 | LC_DAT_PI | HX711 data |
| 40 | 21 | LC_CLK_PI | HX711 clock |

## /boot/firmware/config.txt snippet (ships in ORDER_README)

```ini
# cooksense v1.2 — verified against RP1 datasheet + i2c*-pi5 overlays
dtparam=i2c_arm=on                 # I2C1 GPIO2/3  (MCP23017 0x20)
dtoverlay=i2c2-pi5                 # I2C2 GPIO4/5  (cam A 0x33 + ambient SHT45 0x44)
dtoverlay=i2c3-pi5,pins_14_15      # I2C3 GPIO14/15 (cam B 0x33 + exhaust SHT45 0x44)
# GPIO14/15 default to UART0: the debug console MUST stay disabled (brief §3)
enable_uart=0
# 100kHz bring-up clocks (raise to 400kHz only after EMI validation, brief §3.10)
dtparam=i2c_arm_baudrate=100000
```

Also disable the serial console in cmdline.txt (no `console=serial0,...`).

## RP1 function-table evidence (extracted 2026-07-24)

RP-008370 bank-0 fsel table, a3 column: GPIO2=I2C1_SDA, GPIO3=I2C1_SCL,
GPIO4=I2C2_SDA, GPIO5=I2C2_SCL, GPIO14=I2C3_SDA, GPIO15=I2C3_SCL;
GPIO16/18/19/24/26 have NO I2C function (the ≤v1.1 defect). Kernel
overlays: i2c2-pi5 default pins_4_5; i2c3-pi5 options pins_6_7 /
pins_14_15 / pins_22_23 (rp1.dtsi pinctrl nodes match).
