---
id: 0001
date: 2026-08-14
status: accepted
---
# 0001 — Pi port speed envelope

## Context

The user asked to try USB 3 while accepting USB 2 and named full-size
Raspberry Pi 4 and Pi 5 as the hosts. Both hosts expose two USB 3 ports and two
USB 2 ports, so the host cannot run four 5 Gb/s links simultaneously.

## Options

- **Two USB 3 channels plus two USB 2 channels** — lower area and part count,
  but creates two channel designs and fixes capability to connector position.
- **Four identical USB 3-capable channels** — more parts, but every channel is
  interchangeable and automatically falls back when connected to a USB 2 host
  port.

## Decision

Implement four identical USB 3 Gen 1-capable channels and state explicitly
that at most two can operate at 5 Gb/s simultaneously on the named Pi hosts.

## Consequences

Every channel carries D+/D- plus SuperSpeed TX/RX and needs the same ESD,
switching and controlled-impedance treatment. A BOM/area optimization cannot
turn two channels into USB 2-only paths without superseding this decision.

