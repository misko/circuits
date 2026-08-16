# usb-controlled-debug-hub-v1 — architecture

Status: commissioned architecture; exact parts and support circuits are being
locked before schematic generation.

## Functional partition

The board is a self-powered USB 2.0 High-Speed compound hub. Hub port 1 is a
permanently attached management function. Hub ports 2–5 feed the four external
USB-A connectors. Hub ports 6–7 are disabled by hardware straps.

```text
USB-B upstream -> low-capacitance ESD -> USB2517I seven-port hub

hub port 1 -> managed VBUS switch -> VBUS_CTRL -> MCP2221A USB/HID-to-I2C
                                           +----> MCP23017 I/O expander

hub ports 2..5 -> FSUSB42 data disconnect -> connector ESD -> USB-A x4
hub PRTPWR2..5 --+-> hardware AND -> TPS2557 EN -> switched 5 V x4
control PWR_CMD --+                         |-> OCS/FAULT to hub

control DATA_CMD --+-> hardware AND -> transistor -> FSUSB42 OE
final power enable -+
```

The management path uses factory-defined MCP2221A USB HID/I2C behavior. It
does not need project firmware. MCP23017 supplies the eight command bits;
the USB2517I receives each active-low overcurrent fault directly. External pull resistors—not software—define
the state while either control IC is resetting or unpowered.

## Per-port state machine

| `PWR_CMD` | `DATA_CMD` | Result |
|---:|---:|---|
| 0 | 0 | VBUS off; D+/D- high impedance |
| 1 | 0 | VBUS on; D+/D- high impedance (power-only) |
| 1 | 1 | VBUS on; D+/D- connected |
| 0 | 1 | resolved by hardware to VBUS off and D+/D- high impedance |

The standard hub `PRTPWR` output remains in the VBUS enable equation, so the
host's hub-class sequencing and overcurrent policy cannot be bypassed by the
management device. The data equation uses the final power-enable signal, not
only the requested command.

## Hub configuration

USB2517I uses its internal default configuration with hardware straps:

- self-powered, High-Speed and individual port power/overcurrent control;
- internal port 1 declared non-removable, making the hub a compound device;
- external ports use physical hub ports 2–5;
- physical ports 6–7 disabled by the documented D+/D- straps;
- no EEPROM image, SMBus loader, or MCU startup dependency.

This preserves a truthful five-function hub without programming a descriptor
image. The management bridge is powered from internal port 1's switched VBUS
from that port's 5 V VBUS, so its factory bus-powered descriptor matches its
electrical source. MCP23017 shares the same 5 V domain. The 3.3 V 74LVC logic
accepts those 5 V command inputs without a level shifter and drives only
3.3 V-domain loads.

## Power tree

```text
regulated external 5 V, 5.10–5.25 V at P5V_RAW / >=3 A
  -> replaceable input fuse
  -> reverse-polarity MOSFET
  -> protected 5 V trunk
       -> main 3.3 V regulator -> hub, data switches, interlock logic
       -> internal-port current switch -> MCP2221A + MCP23017 at 5 V
       -> external TPS2557 current switch x4 -> USB-A VBUS x4
```

Each external port is a standard USB 2.0 self-powered downstream port: 500 mA
continuous at 4.75–5.25 V at a qualified mated test plug, with all four loaded.
The 165 kΩ, 1% current-limit setting computes to approximately 535–794 mA
across the TPS2557 datasheet equations and resistor tolerance: it clears
500 mA at the worst-low corner while remaining below the connector/protection ceiling. No BC1.2 or dedicated
charging-port current is advertised.

The protected-trunk floor is 4.89 V at the approximately 2.6 A aggregate
worst-case input load. That bound reserves the 4 A fuse's full published
121 mV typical rated-current drop, 65 mV for the conservatively hot reverse
MOSFET, and 24 mV for input copper/joints. Each external branch then owns a
separate 160 mOhm switch/copper/mated-contact budget. These two serial budgets
are intentionally not double-counted.

Upstream USB VBUS reaches only the hub's high-impedance VBUS-detect network.
It does not join the protected 5 V trunk and cannot back-power the board.

## Net domains and stackup

The machine-readable classes live in `../03_src/rules/nets.yaml`. The principal
signal-integrity class is every USB D+/D- segment from connector to hub or
internal management device. Pairs route on F.Cu over an uninterrupted In1.Cu
ground plane. In2.Cu distributes 5 V and 3.3 V; B.Cu carries slow control and
secondary ground/power copper.

The provisional tier is JLC four-layer advanced. The USB2517I's 64-pin,
0.50 mm-pitch QFN has fifteen escapes on its worst side; that package escape,
not the USB impedance itself, is the reason the standard tier is not credited.
The exact order stackup and JLC 90-ohm differential solve remain order-time
evidence rather than an unsupported source-stage claim.

## Ground, ESD, and shield strategy

All functional grounds use one solid reference system; no split plane crosses
USB routing. Low-capacitance ESD arrays sit at the upstream and each external
connector, in-line with the pair and with a short plane return. Connector
shells connect directly to the board-ground system with short copper and are
never a software-controlled conductor. Ground is not disconnected per port.

## Critical geometries

- Ten active USB pair segments: upstream, internal management, and two
  halves for each of four external ports.
- Each FSUSB42 sits in-line with no copper stub on its unused throw.
- Hub supply decouplers, 12 kΩ RBIAS, 24 MHz crystal and load capacitors remain
  against their named pins before escape routing.
- Connector ESD arrays precede longer board traces.
- The external-port bank and data switches stay in a low-noise region; input
  protection and VBUS switching stay outside pair escape corridors.
- Every USB pair keeps an uninterrupted adjacent reference and uses no vias
  unless placement proves a via transition necessary.

## Interfaces

- `J_UP`: robust USB 2.0 Type-B upstream receptacle; any Pi/PC USB host uses a
  standard A-to-B cable.
- `J_PORT1..4`: USB 2.0 Type-A downstream receptacles.
- `J_PWR`: keyed or clearly polarized two-position 5 V/GND terminal input.
- Four mounting holes; the board does not align to a Raspberry Pi body.

## Firmware boundary

Firmware is forbidden for this commission. The MCP2221A contains
manufacturer-supplied fixed USB bridge behavior; MCP23017 is a register-based
I/O expander. No source, binary, bootloader, descriptor image, or host utility
will be generated. Hardware pull-downs hold `PWR_CMD[1:4]` and
`DATA_CMD[1:4]` inactive until an external host explicitly writes them.
