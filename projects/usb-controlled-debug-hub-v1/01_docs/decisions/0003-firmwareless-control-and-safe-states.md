# ADR-0003 — firmwareless control and safe states

status: accepted
date: 2026-08-15
tags: [topology, usb, control, protection]

## Context

The host must independently control power and physical USB data connectivity,
but standing user directives forbid generating firmware by default. A hub's
standard port-power command does not physically open D+/D-.

## Decision

Use MCP2221A as a factory USB HID-to-I2C bridge on internal hub port 1 and an
MCP23017 as the 16-bit command register bank. Allocate eight expander outputs
to `PWR_CMD[1:4]` and `DATA_CMD[1:4]`. Keep each active-low power-switch fault
on the direct hardware path to its USB2517I overcurrent input rather than
crossing it into the switched management domain. Add an FSUSB42 high-speed
switch to each external pair.

Power MCP2221A and MCP23017 directly from internal port 1 VBUS. Their I2C bus
therefore remains in one 5 V domain. The selected 74LVC logic is powered at
3.3 V but has 5.5 V-tolerant inputs, so it accepts the command levels without
another regulator or level shifter.

Each VBUS enable is `hub_PRTPWR AND PWR_CMD`. Each data connect is
`final_power_enable AND DATA_CMD`; the result pulls the active-high-disconnect
FSUSB42 `OE` low. Physical pull-downs on commands and pull-ups on `OE` enforce
full disconnect during reset, power loss, unconfigured I/O, or bridge removal.

## Consequences

- No project firmware, descriptor image, or bootloader is required.
- Existing MCP2221A HID/I2C protocol support can manipulate the expander.
- Removing the management LDO and fault-domain crossing reduces both the BOM
  and unpowered-input/back-power failure modes.
- Host software, if later requested, is a separate explicit workstream.
- Command state is not mislabeled as device enumeration; the host OS remains
  authoritative for attach/enumeration status.
