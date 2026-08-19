# usb-controlled-debug-hub-v2 — architecture

Status: architecture, schematic and placement are encoded; both USB-C
orientations are machine-checked and user-approved. The USB and high-current
power prefixes are authenticated; control routing and final-board/release gates
remain open.

## System partition

```text
USB-C DATA
  D+/D- -> low-C ESD -> USB2517I upstream pair
  VBUS  -> high-impedance USB2517I VBUS_DET divider only
  CC1/CC2 -> Rd/Rd (USB data-device role)
  no connection to any board power rail

USB-C POWER
  CC1/CC2 -> CH224K hardware PD sink (request 15 V)
  VBUS -> input fuse + TVS + TPS56637 6 A buck -> P5V_RAW (~5.13 V)
  D+/D-/SBU -> no-connect

P5V_RAW -> existing TPS259474L reverse-blocking latch-off eFuse
          -> P5V_PROTECTED
             -> existing AP63203Q 3.3 V regulator
             -> existing management TPS2557
             -> existing external TPS2557 x4
```

The existing USB topology is retained: hub port 1 is the permanently attached
MCP2221A management device; hub ports 2–5 feed the four external USB-A ports;
ports 6–7 remain hardware-disabled. MCP2221A controls MCP23017 over I2C, and
the existing hardware interlocks enforce each port's full-off, power-only, or
fully-connected state without project firmware.

## Domain-separation invariant

There are two unrelated connector VBUS nets:

- `VBUS_DATA_SENSE` exists only from USB-C DATA VBUS contacts to the
  USB2517I detector divider and local sense protection.
- `VBUS_PD` exists only from USB-C POWER VBUS contacts to CH224K and the
  high-voltage power front end.

No resistor-zero-link, test jumper, protection device, plane, or alternate
population may join these nets. Connector shields and signal grounds share the
board ground system; VBUS does not.

## USB-C DATA behavior

TYPE-C-31-M-12 is used as a USB 2.0 receptacle:

- A6/B6 join `UP_DP`; A7/B7 join `UP_DM` immediately at the connector.
- A5 and B5 each receive an independent 5.1 kOhm Rd to ground.
- A4/A9/B4/B9 join `VBUS_DATA_SENSE`, not the protected power trunk.
- SBU1/SBU2 are explicit no-connects.
- the existing low-capacitance upstream ESD array remains between the
  connector and USB2517I.

The host therefore sees a normal USB-C USB 2.0 device/upstream-facing port.
The board still requires USB-C POWER before it can enumerate.

## USB-C POWER behavior

TYPE-C-31-M-12 is used as a power-only sink receptacle. CH224K connects only
to CC1/CC2 and the protected connector-side VBUS. Its fixed hardware straps
request the 15 V PD profile. D+/D- and SBU pins are not routed.

The admitted source advertises a 15 V fixed PDO at 3 A (45 W minimum).
Default 5 V, a 9 V-only source, or a source without the requested contract is
not a qualified supply. The buck's external UVLO is set above default 5 V so
an unsuccessful contract leaves `P5V_RAW` off.

## New regulator island

TPS56637 converts the contracted 15 V to approximately 5.13 V. It was selected
because it:

- accepts 4.5–28 V and tolerates the 15 V PDO with substantial voltage margin;
- supplies 6 A continuously and has a 6.3 A minimum valley-current limit;
- has a vendor 5 V / 6 A reference circuit and layout;
- leaves the existing 5 V aggregate breaker and all downstream switches intact.

The local cell follows TI's 5 V reference topology: 3.3 uH inductor, at least
20 uF effective local output capacitance, close ceramic input bypass, 100 nF
bootstrap capacitor, Eco-mode strap, Kelvin feedback, and separated AGND/PGND
joined at the prescribed point. Existing purchased 22 uF / 25 V 1210 output
capacitors are reused. MWSA0804S-3R3MT provides 3.3 uH, 11 A minimum saturation
rating, 10 A heat-current rating, and 15 mOhm maximum DCR.

The former 5 V blade-fuse holder and screw-terminal path are not in series with
the new 5 V rail. Retaining their 121 mV fixed-drop allowance would consume too
much of the USB output-voltage tolerance. Catastrophic input protection moves
to the lower-current 15 V side; the existing TPS259474L remains the coordinated
5 V aggregate breaker.

## Reused functional core

The following circuits remain semantically unchanged and must pass exact
connectivity parity against v1:

- USB2517I hub, clock, straps, detector, and decoupling;
- MCP2221A/MCP23017 management path;
- five TPS2557 power switches and their current-limit programming;
- four FSUSB42 data switches and four PESD2USB3UX connector protectors;
- 74LVC08/2N7002 hardware interlocks and safe-state pulls;
- AP63203Q 3.3 V regulator;
- four USB-A receptacles and external-port routing topology.

Sourcing substitutions that preserve exact value/package may remain, but stale
v1 release aliases are not release authority for v2. The v2 preliminary BOM is
re-probed before placement and the exact final BOM is allocated at order time.

## Signal integrity and placement boundaries

This remains USB 2.0 High-Speed. The existing ten-segment USB pair contract,
solid In1/In2 ground references, matched transitions, FSUSB42 discontinuity
budget, and first-article eye/compliance hold remain applicable.

The two USB-C connectors will be visibly separated and labeled `DATA` and
`POWER`. The DATA connector sits in the existing upstream USB corridor. The
POWER connector, CH224K, TVS, buck, inductor, and switch node form a compact
power island kept away from all USB pairs and the 24 MHz crystal. Both
connector orientations require machine geometry evidence plus user-approved
directional 3D views before routing.

## Firmware boundary

Firmware remains forbidden. CH224K is hardware-strapped, USB2517I uses its
hardware configuration, and the management path uses MCP2221A's factory USB
bridge behavior. No firmware, descriptor image, or host utility is created.
