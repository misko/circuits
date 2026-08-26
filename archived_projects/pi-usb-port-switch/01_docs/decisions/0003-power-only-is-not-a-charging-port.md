---
id: 0003
date: 2026-08-14
status: accepted
---
# 0003 — Power-only is not a charging port

## Context

One required state keeps VBUS applied while disconnecting every USB data pair.
The fixture can deliver a protected 0.9 A electrical load, but a USB device's
permitted or chosen current draw can depend on enumeration or a separate
charging-port advertisement.

## Options

- **Add charging-port detection/advertisement** — may make some devices draw
  more current, but changes the meaning of the test fixture and adds another
  switched data-line function.
- **Supply VBUS without a charging claim** — preserves the requested power-only
  state and leaves device behavior observable rather than synthesizing a
  charger protocol.

## Decision

Power-only mode supplies protected 5 V but makes no USB dedicated-charging-port
or guaranteed device-current advertisement.

## Consequences

Some devices may draw less than 0.9 A or behave differently while data is off.
The first-article plan must test the intended devices, and adding BC1.2 or other
charging behavior later requires a new requirement and a superseding ADR.

