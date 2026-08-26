# usb-controlled-debug-hub-v1 — architecture

Status: schematic and exact-model placement approved; paused before the first
USB differential routing wave. This is not fabrication readiness.

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
commanded PWR_EN ---+
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
management device. The data equation uses the commanded power-enable result,
not only the requested power command. This prevents contradictory command
states, but it does not sense the switched VBUS voltage or TPS2557 power-good
state. A TPS2557 fault is reported directly to the hub's OCS input, whose
standard hub policy handles the fault.

## Hub configuration

USB2517I uses its internal default configuration with hardware straps:

- self-powered, High-Speed and individual port power/overcurrent control;
- internal port 1 declared non-removable, making the hub a compound device;
- external ports use physical hub ports 2–5;
- physical ports 2–5 keep the documented `PRT_SWP` straps low, with logical D+
  assigned to each physical DP pad and logical D- to each physical DM pad;
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
regulated external 5 V, 5.20–5.25 V at P5V_RAW / >=3 A continuous,
qualified for 5 A / 6 ms transients
  -> replaceable input fuse
  -> TPS259474L reverse-current-blocking latch-off aggregate eFuse
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

The normal commissioned input is 2.58 A and the admitted service peak is 3 A
for no more than 1.5 ms. Five simultaneous TPS2557 worst-high limits plus the
charged 3.3 V input demand total 4.45 A. A TPS259474L programmed by an exact
1 kOhm resistor opens at a calculated 2.990–3.680 A and latches off after a
calculated 1.608–5.042 ms. The source and input path therefore require a
separate 5 A / 6 ms transient qualification; they are not claimed to carry
4.45 A continuously.

The protected trunk includes a 180 uF polymer and 22 uF X7R bank. After
initial tolerance, life, bias and temperature loss, the calculated effective
minimum is 128.664 uF, above the USB 2.0 120 uF hub-bypass requirement. The
aggregate eFuse has a dedicated 100 nF input bypass at `P5V_FUSED`; its dV/dt
control bounds startup slew to 0.640 V/ms and the 251.86 uF maximum output
bank's calculated inrush to 0.161 A.

Upstream USB VBUS reaches only the hub's high-impedance VBUS-detect network.
It does not join the protected 5 V trunk and cannot back-power the board.

## Net domains and stackup

The machine-readable classes live in `../03_src/rules/nets.yaml`. The principal
signal-integrity class is every USB D+/D- segment from connector to hub or
internal management device. F.Cu pairs reference the uninterrupted In1.Cu
ground plane; B.Cu pairs reference an uninterrupted In2.Cu ground plane.
Each port-side switch-to-connector segment stays on B.Cu without vias, with a
short shunt branch to its ESD device. The management pair stays on F.Cu without
vias. Each hub-side external segment
and the upstream path may make one matched F.Cu/B.Cu transition with adjacent
ground-return vias; realized layer use, via symmetry and skew are release
gates rather than assumptions.

The provisional tier is JLC four-layer advanced. The USB2517I's 64-pin,
0.50 mm-pitch QFN has fifteen escapes on its worst side; that package escape,
not the USB impedance itself, is the reason the standard tier is not credited.
The provisional public JLC04161H-7628 geometry is 0.2332 mm trace width,
0.15 mm pair gap and 0.30 mm outer-copper clearance. The exact order stackup,
JLC calculator result and impedance-coupon selection remain order-time evidence
rather than an unsupported source-stage claim.

## Ground, ESD, and shield strategy

All functional grounds use one solid reference system; no split plane crosses
USB routing. Low-capacitance PESD2USB3UX shunt arrays sit at the upstream and
each external connector with a short plane return. Connector
shells connect directly to the board-ground system with short copper and are
never a software-controlled conductor. Ground is not disconnected per port.

## Critical geometries

- Five functional USB links are represented as ten pair-net segments. The
  shunt ESD arrays do not divide the upstream or connector-side signal nets;
  the four FSUSB42 switches do divide their hub-side and port-side pairs.
- FSUSB42 contributes 3.7 pF typical channel-on capacitance and the selected
  shunt protector contributes at most 0.7 pF. The resulting 4.4 pF component
  budget is narrow and does not include connector/PCB discontinuities or an
  FSUSB42 maximum; first-article USB 2.0 eye/compliance testing is mandatory.
- Each FSUSB42 sits in-line with no copper stub on its unused throw.
- Hub supply decouplers, 12 kΩ RBIAS, 24 MHz crystal and load capacitors remain
  against their named pins before escape routing.
- Connector ESD shunt branches and their ground returns remain shorter than
  the protected path continuing into the board.
- The external-port bank and data switches stay in a low-noise region; input
  protection and VBUS switching stay outside pair escape corridors.
- Every USB pair keeps an uninterrupted adjacent reference. Bottom connector/
  switch segments and the top management segment use no vias; the
  hub-side external/upstream paths permit only a deliberate matched transition
  with nearby ground-return vias.

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
