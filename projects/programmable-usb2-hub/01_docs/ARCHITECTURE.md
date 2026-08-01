# Architecture — programmable USB 2.0 hub

## Functional partition

The board is a self-powered seven-port USB 2.0 high-speed hub with five ports
used: external ports 1–4 and an internal management-controller port 5. Hub
ports 6 and 7 are disabled during pre-enumeration configuration.

```text
USB-B upstream
  D+/D- -> ESD -> USB2517I hub
  VBUS  -> sense only; never powers or receives power from the board

USB2517I downstream 1..4
  D+/D- -> FSUSB42 physical gate -> ESD -> USB-A connector
  PRT_PWR ---------------------+                per port
                               AND -> TPS259470A EN -> switched 5 V
  MCU power command -----------+
  TPS259470A FLT -> hub OCS_N + management MCU

USB2517I downstream 5 -> STM32G0B1 management USB device (always connected)
STM32 -> power/data commands, FLT, IMON, switched-VBUS ADC, hub SMBus/reset
host utility -> MCU telemetry + OS hub-port attachment/enumeration
```

The meaning of every reported state is fixed by ADR-0003 and the management
protocol in `05_firmware/README.md`. In particular, the MCU never claims that
a child enumerated; the host utility owns that fact.

## Power tree

```text
12–24 V locking terminal
  -> 10 A replaceable fuse
  -> LM74810-Q1 protected ideal-diode / back-to-back 60 V MOSFET stage
  -> VIN_PROTECTED
       +-> SMBJ26A TVS clamp (protected side)
       +-> LM5116 buck A -> 5V_A, 5.15 V / 7 A -> ports 1,2
       +-> LM5116 buck B -> 5V_B, 5.15 V / 7 A -> ports 3,4
       +-> AP63203 fixed buck -> 3V3_LOGIC, up to 2 A
```

Each external port uses a TPS259470A eFuse. It provides hardware current
limiting, true reverse-current blocking, fault output, and an analog current
monitor. MCU ADCs also measure the post-eFuse VBUS node through independent
dividers. A power-good inference therefore requires measured VBUS, not merely
an enable bit.

The USB-A 3 A interpretation and connector constraint are recorded in
ADR-0001. The split high-current rails are recorded in ADR-0002. The
machine-readable voltage/current/loss bounds live in
`03_src/rules/power_tree.yaml`.

## Startup and fault behavior

1. The input protection stage validates polarity and overvoltage before
   energizing `VIN_PROTECTED`.
2. `3V3_LOGIC` starts independently of both high-current bucks. Hardware
   pulldowns hold all four eFuse enables low; hardware pullups hold the four
   active-low data-switch OE_N controls high, physically disconnecting D+/D-.
3. The MCU boots, configures the USB2517I over SMBus while holding hub reset,
   then releases the hub. Its own port 5 is not externally gated.
4. The USB host enumerates the hub, then the management interface. External
   ports remain off until commanded.
5. An eFuse short/overcurrent is limited in hardware, asserts FLT to both hub
   and MCU, and the MCU latches that port disabled. Firmware is not credited
   for the safe peak current.

Removing the external input is the only whole-board de-energization method.
That commission assumption is in BRIEF A2.

## USB 2.0 signal topology

External upstream/downstream high-speed pairs route on L1 over the unbroken L2
ground plane. The short internal MCU-management pair may use one symmetric via
pair to cross without a polarity swap; all connector-facing pairs remain on
L1. Connector ESD devices are inline at
the board edge; the FSUSB42 switch lies between the hub and the connector-side
ESD. The unused FSUSB42 throw is physically unconnected.

Preliminary USB class is 0.25 mm trace / 0.15 mm pair gap on the 1.6 mm
JLC04161H-7628 four-layer stack (0.20 mm outer prepreg). This is an
**ESTIMATED** 90 ohm differential geometry, not release evidence. The exact
width/gap must be replayed through JLCPCB's order-time impedance calculator and
the ordered stackup recorded before sealing. JLCPCB's current guidance requires
the selected stackup, copper weights, pair gap, and reference layer as calculator
inputs; it does not make a generic width portable across stackups.

Routing constraints:

- Pair length mismatch <= 0.50 mm within each switched segment and <= 1.0 mm
  end-to-end.
- No stubs at ESD or switch pins; no test pads on D+/D-; any internal-port
  layer transition uses a symmetric via pair.
- Continuous L2 ground below every pair; no 5 V or 3.3 V split may interrupt it.
- At least 3W spacing from switch nodes, inductors, bootstrap and gate-drive
  traces where geometry permits; never route through a buck hot-loop footprint.
- Upstream and port-5 internal pairs receive the same class as external pairs.

## Stackup and ground

Declared fabrication: JLCPCB 1.6 mm, four layers, advanced tier, controlled
impedance, 1 oz outer copper. Layer use:

| layer | use |
|---|---|
| L1 | all USB pairs, components, short local signals, high-current top pours |
| L2 | uninterrupted ground reference plane |
| L3 | 5V_A / 5V_B / VIN_PROTECTED power regions with ground fill between them |
| L4 | slow control, high-current reinforcement pours, ground fill |

High-current nets are pour-fed on L1 plus L3/L4 reinforcement with multiple
vias at every layer transition. USB-A shell tabs bond directly to ground with
nearby chassis/ESD return vias; there is no thin shell-return trace. Analog
IMON and VBUS-sense traces route as quiet Kelvin-like signals from the eFuse
pins/output node to the MCU and are guarded from switch nodes.

## Physical floorplan

Target outline is approximately 130 mm x 90 mm with four M3 holes. Four USB-A
mouths are spaced along the north edge. The upstream USB-B connector is on the
west edge and the 12–24 V terminal/fuse is on the south-west edge.

- Hub, 24 MHz reference, upstream ESD, and data-switch fanout occupy the
  north-central low-noise region.
- Each FSUSB42 and its connector-side ESD array sit in the direct path to its
  USB-A receptacle.
- Port eFuses sit behind their receptacles with short, wide VBUS pours and
  local output capacitance.
- Buck A occupies the south-east power island and buck B the south-central
  island; their switch nodes face away from the USB routing bank.
- Input protection and the logic buck occupy the south-west island.
- The MCU and SWD header sit west of the hub, outside both buck hot loops.

Connector mouths, fuse access, status labels, and programming access remain
usable with the board mounted on 6 mm standoffs.

## Programming and service connector

`J_SWD` is a keyed 2x5, 1.27 mm ARM Cortex debug header at the west edge:

| pin | signal | pin | signal |
|---:|---|---:|---|
| 1 | 3V3 target reference | 2 | SWDIO |
| 3 | GND | 4 | SWCLK |
| 5 | GND | 6 | SWO / spare trace |
| 7 | NC, keyed | 8 | NC |
| 9 | GND detect | 10 | NRST |

The header supplies no programmer power to the board; pin 1 is reference only.
BOOT0 is pulled low and exposed as a nearby labeled test pad for recovery.

## Indicators

One logic-ready LED and four RGB-equivalent two-color status groups are
optional assembly features, not sources of truth. Per-port green indicates
measured VBUS present and amber indicates a latched fault. The host utility and
hardware telemetry remain authoritative; LEDs may be omitted if routing or BOM
cost conflicts with signal integrity.
