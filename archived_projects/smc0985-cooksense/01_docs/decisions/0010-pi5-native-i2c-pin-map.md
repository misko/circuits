# ADR-0010 — Pi 5 native-I2C pin map repaired + published (v1.2)

status: accepted
date: 2026-07-24
tags: topology

## Problem (external review F1, CONFIRMED against sealed v1.1 source)

ADR-0004 moved the sensors to "Pi-native I2C", but the sealed v1.0/v1.1
J_PI assignment never landed on native pairs: camera A sat on physical
7/8 (GPIO4+GPIO14 — two different buses' SDA lines), camera B on 10/12
(GPIO15+GPIO18), ambient SHT45 on 18/35 (GPIO24+GPIO19), exhaust SHT45
on 36/37 (GPIO16+GPIO26). GPIO16/18/19/24/26 carry NO I2C alternate
function at all. Only the MCP23017 on physical 3/5 (GPIO2/3 = I2C1) was
correct. 4 of 5 buses were unusable as native I2C.

## Verified function table (do not take on faith — re-verified 2026-07-24)

Sources: RP1 peripherals datasheet RP-008370 GPIO function-select table
(bank 0), cross-checked against raspberrypi/linux rpi-6.6.y
`i2c2-pi5-overlay.dts` / `i2c3-pi5-overlay.dts` / `rp1.dtsi`:

| GPIO | phys pin | I2C alt (RP1 a3) | overlay |
|---|---|---|---|
| 2 / 3   | 3 / 5   | I2C1_SDA / I2C1_SCL | i2c1 (default arm I2C) |
| 4 / 5   | 7 / 29  | I2C2_SDA / I2C2_SCL | i2c2-pi5 (default pins_4_5) |
| 14 / 15 | 8 / 10  | I2C3_SDA / I2C3_SCL | i2c3-pi5, pins_14_15 |
| 6 / 7   | 31 / 26 | I2C3 (alt option)   | not used: GPIO6=KEY_CLOCK, GPIO7=SPI CE1 |
| 16,18,19,24,26 | 36,12,35,18,37 | NONE | — |

GPIO14/15 default to UART0 (debug console): the console is disabled per
brief §3 — recorded in the overlay snippet (pin_map.md).

## Decision — RESTORES the commissioned bus plan, not a new architecture

The BRIEF's verbatim §3 already specifies EXACTLY this topology: "I2C:
two native buses (both cameras are 0x33): bus A = camera A + ambient
SHT45 (0x44); bus B = camera B + exhaust SHT45." The sealed v1.0/v1.1
FOUR-separate-bus wiring was a silent DEVIATION from the brief — and the
deviation is what made the pin map impossible (four buses do not fit the
header's native pairs; two do). v1.2 restores commissioned intent:
three native buses (2 sensor + 1 control), cameras and SHT45s sharing
by address (0x33 vs 0x44):

| bus | GPIO (SDA/SCL) | phys | devices | net |
|---|---|---|---|---|
| I2C1 | 2 / 3   | 3 / 5  | MCP23017 (0x20) | I2C_SDA / I2C_SCL |
| I2C2 | 4 / 5   | 7 / 29 | MLX90640 A (0x33) + ambient SHT45 (0x44) | SDA_A / SCL_A |
| I2C3 | 14 / 15 | 8 / 10 | MLX90640 B (0x33) + exhaust SHT45 (0x44) | SDA_B / SCL_B |

Consequences:
- Nets SDA_RHA/SCL_RHA/SDA_RHE/SCL_RHE are MERGED into SDA_A/SCL_A and
  SDA_B/SCL_B (J_RH_AMBIENT joins bus A, J_RH_EXHAUST joins bus B).
- The four RH-bus 2.2k pullup pairs are DELETED: one 2.2k pair per bus
  remains, powered from the CAMERA's switched rail (N3V3_SW_A/_SW_B),
  honouring ADR-0004 N1 (pullups die with the rail). The SHT45 pods keep
  their module 10k pullups.
- PHANTOM-POWER note (accepted, documented): two switched rails now feed
  one bus's devices. With one rail off and the other on, the off device
  can be back-powered ~uA-mA through its bus pins. Bus-stuck recovery
  procedure = power-cycle BOTH rails of the affected bus together
  (RAIL_EN_A+RAIL_EN_RHA, or RAIL_EN_B+RAIL_EN_RHE). Recorded in
  DETAIL_DESIGN + ORDER_README.
- KEY_DATA re-homed GPIO5/phys29 → GPIO16/phys36 (GPIO16 has no I2C or
  boot-strap function).
- STOP_REQ becomes a DIRECT Pi GPIO26/phys37 (motivated by ADR-0011's
  KEY_LATCH freeze: a registered STOP bit behind a frozen latch could
  not preempt a press). Freed after moves: phys 12 (GPIO18), 18
  (GPIO24), 35 (GPIO19) = NC spares.
- The complete GPIO map is a MAINTAINED artifact: 01_docs/pin_map.md
  (D3/T4 gate artifact), shipped in every release with the
  device-tree-overlay snippet.

## Executable invariants (E-ADR)

Emitted in 03_src/rules/electrical_invariants.yaml citing adr 0010:
every I2C net pinned to its exact header pin (J_PI.3/.5/.7/.29/.8/.10),
KEY_DATA pinned to J_PI.36, STOP_REQ to J_PI.37, and the RH connectors
pinned to the shared bus nets — a silent regression of this map fails
the schematic gate.
