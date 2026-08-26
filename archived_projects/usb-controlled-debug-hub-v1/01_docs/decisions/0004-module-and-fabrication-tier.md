# ADR-0004 — module choice and fabrication tier

status: accepted
date: 2026-08-15
tags: [module, sourcing, fabrication-tier, layout]

## Context

The hub subsystem exceeds the module-first support threshold. Microchip's
EVB-USB2517 terminates its ports and power policy on an evaluation board; a
four-port hub module cannot expose four external ports plus an internal
management function. The selected hub package is a 64-pin 0.50 mm-pitch QFN
with fifteen escapes on its worst side.

## Decision

Use the bare USB2517I only for the hub subsystem. Study Microchip's official
EVB and hardware checklist, then re-derive the local placement and escape.
Use fixed-function, leaded MCP2221A/MCP23017 control devices instead of a
programmable compute module. Provisionally select JLC four-layer advanced;
the hub escape evidence, not optional pipeline capability, is the reason.

## Alternatives considered

- EVB-USB2517: validated but not an embeddable raw-port module.
- Four-port USB hub modules/controllers: one downstream function short.
- MCU module: adds firmware and USB-device integration without reducing the
  control-plane support set.

## Consequences

- Package escape and JLC uploader cost are checked before routing.
- If a sourceable five-port-or-greater leaded hub appears, it may reopen this
  decision; convenience alone does not justify a package change.

