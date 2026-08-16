# ADR-0001 — single-cable USB 2.0 compound hub

status: accepted
date: 2026-08-15
tags: [topology, usb, spec-tension]

## Context

Four external USB-A functions and one onboard USB management function cannot
share a four-port hub. A second device also cannot be wired in parallel with a
hub's upstream D+/D- pair. USB 3 would add eight SuperSpeed pair segments and
four additional high-speed disconnect paths to a debugging feature that only
requires deterministic attach/detach behavior.

## Decision

Use a USB2517I seven-port USB 2.0 High-Speed hub. Connect its physical port 1
to the onboard management bridge, ports 2–5 to the external receptacles, and
disable ports 6–7 with documented hardware straps. Mark port 1 non-removable
so the hub truthfully enumerates as a compound device. Use one USB-B upstream
connector for both hub traffic and management traffic.

## Consequences

- The user needs only one host cable.
- All four requested external ports remain available.
- USB 2.0 High-Speed, not USB 3, is the performance claim.
- Hardware straps eliminate a configuration EEPROM or startup loader.

