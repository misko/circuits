# Programmable USB 2.0 hub firmware

This directory defines the management MCU interface and the reference host
utility. The control plane is deliberately separate from USB hub-class state:
the MCU reports electrical facts and command state; the host reports child
connection/enumeration at the parent hub's stable port path.

Power-up is fail-safe: all four external VBUS eFuse enables remain low and all
four USB2 data-switch OE_N controls remain high until firmware has configured
GPIOs and a host explicitly enables them. The internal management port is not
gated.

The wire contract is below. `src/` contains hardware-independent protocol/state
logic and the top-level `test_*.py` files are host-runnable tests. The STM32
target will use the same packed records; USB VID/PID values remain
prototype-only until the owner assigns production identifiers.

Build/test: `PYTHONPATH=src python3 -m unittest -v test_phub_protocol.py
test_phub_state.py test_phubctl.py`.

The reference host utility is `host/phubctl.py`. For example,
`python3 host/phubctl.py --simulate data-connect 1` exercises the complete
record/state path without hardware. Real access requires PyUSB and explicit
owner-assigned `--vid` / `--pid`; the tool deliberately has no shipping
default identity.

`target/phub_core.c` is the allocation-free embedded safety core intended for
the STM32G0B1 target. It contains no host or STM32 HAL dependency; compile its
host test with `cc -std=c11 -Wall -Wextra -Werror target/phub_core.c
target/test_phub_core.c -o /tmp/phub_core_test && /tmp/phub_core_test`. The
remaining target integration is USB descriptors/endpoints, ADC calibration,
GPIO binding, watchdog startup, and USB2517 SMBus initialization.
The target/flash commands and SWD connector reference will be added when the
selected MCU dossier fixes the exact target name and pins. An unprogrammed MCU
leaves all external power and data paths disabled by hardware pulldowns.

## PHUB management protocol v1

Transport: one interrupt-IN and one interrupt-OUT endpoint on a vendor-specific
USB interface carried by the internal management MCU on hub port 5. Reports are
64 bytes. Multibyte integers are little-endian. Bytes 60–63 carry CRC-32/ISO-HDLC
over bytes 0–59.

Production firmware must use owner-assigned USB VID/PID values. Development
builds may use the TinyUSB example pair `CAFE:4011` only on a private bench;
those identifiers are not a product identity and must not ship.

### Common header

| byte | field | meaning |
|---:|---|---|
| 0 | magic0 | `0x50` (`P`) |
| 1 | magic1 | `0x48` (`H`) |
| 2 | major | `1` |
| 3 | minor | `0` |
| 4 | opcode | command or response opcode |
| 5 | sequence | echoed by the response |
| 6 | port | 1–4, or 0 for global commands |
| 7 | result/flags | request flags or response result |

### Commands

| opcode | name | request payload | response |
|---:|---|---|---|
| `0x01` | `GET_INFO` | none | firmware/build/capability record |
| `0x10` | `GET_PORT` | port | full `PORT_STATUS` |
| `0x11` | `SET_POWER` | byte 8 = 0/1 | full status after settling |
| `0x12` | `POWER_CYCLE` | bytes 8–11 = off time ms, clamped 50–60000 | acknowledgement; completion appears in status/event |
| `0x13` | `SET_DATA` | byte 8 = 0/1 | full status after settling |
| `0x14` | `CLEAR_FAULT` | none | clears the firmware latch only after hardware FLT is inactive |
| `0x20` | `GET_ALL` | none | global header followed by four compact port records |
| `0x30` | `SET_SAFE_DEFAULTS` | byte 8 power mask, byte 9 data mask | volatile until authenticated persistence is specified |

Undefined commands and invalid ports return `BAD_OPCODE` or `BAD_PORT` and
must not change any output.

### PORT_STATUS response

| byte | field | source |
|---:|---|---|
| 8 | `power_commanded` | retained MCU command bit |
| 9 | `power_enabled` | readback of final enable GPIO/logic output |
| 10 | `vbus_present` | post-eFuse ADC above threshold with hysteresis |
| 11 | `overcurrent` | debounced eFuse FLT input |
| 12 | `fault_latched` | MCU safety latch |
| 13 | `data_commanded` | retained MCU command bit |
| 14 | `data_enabled` | readback of data-switch OE control output |
| 15 | reserved | zero |
| 16–17 | `vbus_mV` | calibrated post-eFuse voltage |
| 18–19 | `current_mA` | calibrated eFuse IMON estimate |
| 20–23 | `fault_count` | saturating counter since MCU reset |
| 24–27 | `last_transition_ms` | MCU uptime at last state change |

`connected` and `enumerated` are intentionally absent: they are host facts.
The reference utility adds them by locating children at parent-hub port paths
1–4. It must print `unknown`, never `false`, when the operating system cannot
provide hub topology or permissions are insufficient.

### Safety state machine

1. Reset leaves each power enable low and each active-low data-switch OE_N high
   through hardware resistors. Firmware preserves those levels until clocks and
   watchdog are live, then drives the same safe state before accepting commands.
2. A power-enable command is rejected while FLT is asserted or the firmware
   latch is set.
3. FLT immediately records the event and disables the affected eFuse. Hardware
   current limiting remains the first-line short-circuit protection; firmware
   is not credited for safe peak current.
4. Data and power controls are independent. Power cycling does not silently
   change the requested data state.
5. Watchdog reset returns all external channels to off and records the reset
   cause for the next `GET_INFO`.
