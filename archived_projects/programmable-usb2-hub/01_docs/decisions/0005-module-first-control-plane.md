# ADR-0005 — Module-first control-plane exceptions

status: accepted for declarative implementation
date: 2026-08-01
tags: [module-first, management, usb-hub, integration]

## Context

The architecture backtrack re-opened module selection before schematic work.
The management controller must expose native USB D+/D-, eight simultaneous ADC
inputs, fifteen concurrent digital GPIO, SMBus/I2C, SWD and reset. The hub must
expose at least five downstream pairs, four raw pairs passing through external
data switches, per-port PRT_PWR/OCS signals, SMBus and reset.

## Decision

Retain exact bare `STM32G0B1CBT6` for the management plane. Raspberry Pi Pico 2
exposes only three ADC channels. Seeed XIAO RP2040 exposes four analog inputs
and eleven digital pins. Neither module meets the locked 8-ADC / 15-digital
binding without external expansion that would increase support circuitry and
firmware complexity.

Retain exact bare `USB2517I-JZX` for the hub. EVB-USB2517 is a standalone
evaluation board whose downstream connectors and onboard port-power handling
do not expose the required four inline-switched raw pairs and board-owned
power policy. EVB-USB2514BC exposes only four downstream ports, below the
required five. The bare USB2517I provides seven raw pairs, seven PRT_PWR
outputs, seven OCS inputs, SMBus and reset.

Retain exact bare `LTC3889IUKG#PBF` for the two 6 A 5 V rails. The stocked
TPSM64406RCHR module was considered first, but its 788--812 mV feedback
reference cannot satisfy the locked 4.75--5.25 V mated-connector boundary after
the complete 3 A delivery path and 20% loss margin are included. The LTC3889's
tighter output accuracy and independent dual channels meet that binding.

## Consequences

Each exception is represented in `03_src/rules/integration.yaml` with its
external-support inventory and cited module comparison. This ADR authorizes no
placement or routing by itself; exact pin maps, support networks, safe startup,
escape, early design review, and schematic topology review remain mandatory.
