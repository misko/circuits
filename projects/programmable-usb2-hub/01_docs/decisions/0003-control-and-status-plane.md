# ADR-0003 — USB control and status plane

status: accepted
date: 2026-07-31
tags: [topology, usb, firmware, host-control]

## Context

The same upstream host must control four independent power switches and four
physical D+/D- disconnects, while seeing commanded state and real device
attachment/enumeration. A hub controller alone does not provide the requested
vendor control surface, while an MCU alone cannot truthfully infer operating
system enumeration.

## Decision

Use a hub controller with at least five downstream ports. Ports 1–4 feed the
external USB-A connectors through independent high-speed DPDT switches. Port 5
feeds a native-USB management MCU mounted on the same PCB. Ports 6–7, if
present, are disabled in hub configuration.

The MCU exposes a versioned vendor USB protocol for per-port power enable,
data-switch output-enable, voltage-present ADC telemetry, overcurrent/fault,
reset cause, and command-state readback. The host utility associates the
management interface with its parent hub and combines MCU telemetry with
standard hub-class/operating-system port connection and enumeration state.

Hub-controller port-power outputs are ANDed with MCU power commands, so normal
USB hub power sequencing remains authoritative and the MCU can independently
cycle a port. Each power-switch fault feeds both the hub overcurrent input and
the MCU.

## Status semantics

- `power_commanded`: MCU's requested gate state.
- `power_enabled`: readback of the final AND-gate output.
- `vbus_present`: post-switch ADC voltage above the documented threshold.
- `overcurrent`: debounced hardware FAULT input.
- `data_commanded`: MCU's requested D+/D- switch output-enable.
- `connected`: standard hub port connection status observed by the host.
- `enumerated`: host found a child device at that stable hub port path.

No firmware field is allowed to label a command bit as measured attachment.

## Consequences

- Control remains reachable while all external ports are powered and data-
  disconnected.
- Actual enumeration remains a host-side fact, avoiding false hardware claims.
- Host software is part of the deliverable and must tolerate OS permissions
  needed for hub-class status queries.

## Machine-checkable obligations

- Netlist invariants bind external hub ports 1–4 through data switches and the
  MCU to internal port 5.
- Firmware protocol tests distinguish commanded, electrical, connected, and
  enumerated state fields.
