# brief: usb-controlled-debug-hub-v1

status: in-progress
prompt_sha256: 7959371bea4d4016e563f30e86b0acc5a552a4b47a189b7d18968a086dcc92a0
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
once you are done with the changes for improvements , please make a new board, similar to the usb pi switch, but instead of 4 x USB host connectors, lets have the board act as a USB hub and usb device. The usb hub controls the 4 x USB A ports on the board, and the usb device lets you toggle on and off power and or data to each USB A.
<!-- prompt-verbatim-end -->

- date: 2026-08-15
- channel: user request

## End goal — definition of done

Deliver an assembled, source-reproducible USB 2.0 debug hub. One upstream USB
connection exposes four independently controlled USB-A ports and an internal
management USB device. The management device can request full-off, power-only,
or full connection per external port. The release must pass the repository's
schematic, high-speed routing, JLCPCB assembly, digital-twin, independent
review, and release gates without generating custom firmware.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | One upstream connector enumerates a USB 2.0 hub | P | unmet |
| G2 | Four downstream USB-A receptacles are available concurrently | P | unmet |
| G3 | The same upstream cable also exposes an onboard USB management device | P, A1 | unmet |
| G4 | Each USB-A independently supports full-off, power-only, and fully connected states | P | unmet |
| G5 | Reset, unconfigured control, or loss of control power leaves every external port fully disconnected; the command-state interlock rejects data-on whenever the commanded power enable is off | A3 | unmet |
| G6 | The hub is self-powered from a separate regulated 5 V input and never back-powers the upstream host | A2 | unmet |
| G7 | Each external port delivers the USB 2.0 self-powered-hub load of 500 mA at 4.75–5.25 V at the mated test plug, all four simultaneously | A2 | unmet |
| G8 | No firmware or host utility is generated unless the user explicitly requests it | D1, D2 | unmet |
| G9 | A complete JLCPCB PCBA release passes applicable electrical, SI, sourcing, assembly, render, and independent-review gates | A4 | unmet |

## Spec tensions

| id | requirement | standard / part cap | how honoured | ADR | user-flagged |
|---|---|---|---|---|---|
| T1 | Four external ports plus an onboard management device on one upstream cable | A four-port hub has only four downstream functions; attaching a fifth USB function in parallel to the upstream pair is invalid | Use a seven-port hub: one internal management port, four external ports, two hardware-disabled ports | [0001](decisions/0001-single-cable-usb2-compound-hub.md) | yes |
| T2 | Disconnect data while retaining VBUS | Standard hub port-power control alone does not physically isolate D+/D- | Add one USB 2.0 high-speed analog disconnect per external port | [0003](decisions/0003-firmwareless-control-and-safe-states.md) | yes |
| T3 | Independent software control without firmware generation | A programmable MCU would require a firmware and bring-up workstream | Use a factory USB HID-to-I2C bridge and I/O expander; generate no firmware | [0003](decisions/0003-firmwareless-control-and-safe-states.md) | yes |
| T4 | Similar to the earlier USB 3-capable Pi switch | USB 3 would require a SuperSpeed hub plus eight additional differential lanes and switches; the earlier user answer accepted USB 2 fallback | Build a USB 2.0 High-Speed hub and qualify 480 Mbit/s operation; make no USB 3 claim | [0001](decisions/0001-single-cable-usb2-compound-hub.md) | yes |
| T5 | Four powered USB-A ports on a USB 2.0 hub | A standard USB 2.0 downstream port supplies 500 mA; 900 mA is a USB 3 port claim and 1.5 A requires BC1.2 behavior | Guarantee 500 mA per port and make no charging-port advertisement | [0002](decisions/0002-self-powered-5v-envelope.md) | yes |

## Commission fact-lock

| Fact | Value | Locked by |
|---|---|---|
| Output rails: Vout min-max @ Imax | Four switched USB-A VBUS rails, each 4.75–5.25 V at 0.50 A continuous | A2 |
| External outputs | Four USB-A receptacles; four simultaneous loads | P, A2 |
| Duty | 0.50 A per port continuous; USB-compliant inrush and short-circuit behavior; no charging-current claim | A2 |
| Measurement plane | Qualified mated USB-A test plug; includes input fuse/reverse protection, power switch, PCB copper/vias/joints, and mated VBUS/GND contacts; excludes external supply lead, downstream cable, and device | A2 |
| Input envelope | Regulated SELV 5.20–5.25 V at `P5V_RAW` under load, at least 3 A continuous and qualified for 5 A / 6 ms transient service | A2, A6 |
| Protection posture | Input fuse and aggregate reverse-current-blocking latch-off eFuse; per-port current limiting, thermal shutdown, and hub overcurrent feedback; low-capacitance connector ESD; sustained input overvoltage above 5.25 V remains outside the admitted source envelope | A2, A6 |
| Off-control / storage | Remove the external 5 V feed; upstream VBUS is sense-only and cannot power or backfeed the board | A2 |
| Hard-cell functions | USB2517I hub, MCP2221A control bridge, MCP23017 expander, FSUSB42 data switches, and TPS2557 power switches are JLC/LCSC-listed; volatile stock remains an order-time recheck | sourcing spike 2026-08-15 |
| Integration posture | Complexity weighted: use the bare USB2517 only because no module exposes five raw downstream paths; use fixed-function bridge/expander parts to eliminate firmware | A5, [0004](decisions/0004-module-and-fabrication-tier.md) |

## Mating fact-lock

none — this board does not mate to hardware this repository did not design.
It uses standard cables, a screw-terminal power lead, and free-standing mounting
holes; no Raspberry Pi body or connector alignment is consumed.

## Log

### D1 — prior standing user directive

> please do not generate firmware by default for a project only if specifically requested

Impact: `05_firmware/` contains only its binding contract. A programmable or
configurable IC does not expand firmware scope.

### D2 — prior standing user directive

> please stop generating firmware

Impact: Reinforces D1. The control plane uses factory USB bridge behavior and
hardware-safe defaults rather than generated firmware.

### A1 — 2026-08-15 — single upstream cable

Assumed: “act as a USB hub and USB device” means the management device appears
through the same upstream USB connection, not a second control cable.
Authority: P asks for one board acting as both functions.
Escalate if: two upstream cables are preferred.

### A2 — 2026-08-15 — conservative USB 2.0 power boundary

Assumed: inherit the earlier fixture's separate regulated 5 V supply, but use
the standards-correct USB 2.0 self-powered load of 500 mA per port. Require
5.20–5.25 V / 3 A at `P5V_RAW` under load and 4.75–5.25 V at each mated USB-A plug.
Authority: P asks for a hub similar to the prior separate-supply fixture and
delegates the exact electrical envelope.
Escalate if: any target device requires BC1.2 charging or more than 500 mA.

### A3 — 2026-08-15 — safe state and hardware interlock

Assumed: control reset, a missing host command, or an unpowered control device
forces every external port fully off. Hardware rejects a data-on command when
the commanded power-enable equation is false. This is not a `VBUS_SW` voltage,
power-good, or fault-sense interlock; TPS2557 overcurrent feedback remains on
the normal USB hub OCS path.
Authority: this is the conservative interpretation of independent disconnect.
Escalate if: ports must power or connect automatically at boot.

### A4 — 2026-08-15 — manufacturing target

Assumed: `/pcb-design` defaults apply: populated JLCPCB PCBA and complete
release archive, starting at the least-cost capable tier.
Authority: PCB skill outcome contract and prior project practice.
Escalate if: bare boards or another assembler are wanted.

### A5 — 2026-08-15 — firmwareless management implementation

Assumed: use MCP2221A's factory USB HID/I2C interface to control an MCP23017
expander. The host may use existing protocol support; no custom host utility or
firmware is part of this commission.
Authority: P requires a USB management device while D1/D2 forbid default
firmware generation.
Escalate if: a custom protocol, signed firmware, or autonomous behavior is
required.

### A6 — 2026-08-16 — aggregate fault and source transient boundary

Assumed: the separately regulated input source can be selected and qualified
for 5 A / 6 ms transient service while remaining a 3 A continuous source. A
TPS259474L aggregate breaker latches the board off before the simultaneous
4.45 A downstream worst-high envelope becomes a continuous input obligation.
Authority: independent pre-route review found the earlier 3 A-only contract
did not bound simultaneous current-limit faults.
Escalate if: the intended source cannot tolerate that short transient; select
a lower threshold/current-limit architecture before fabrication.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| C1 | One USB 2.0 upstream connection serves the hub and internal management function | agent (A1 / P-delegation) | [0001](decisions/0001-single-cable-usb2-compound-hub.md) |
| C2 | Use one internal hub port, four external ports, and disable two unused ports | agent (A1 / P-delegation) | [0001](decisions/0001-single-cable-usb2-compound-hub.md) |
| C3 | Self-power from regulated 5.20–5.25 V / 3 A at `P5V_RAW` and guarantee four 500 mA USB 2.0 outputs | agent (A2 / P-delegation) | [0002](decisions/0002-self-powered-5v-envelope.md) |
| C4 | Use physical per-port data switches plus independently current-limited VBUS switches | user (P) | [0003](decisions/0003-firmwareless-control-and-safe-states.md) |
| C5 | Use MCP2221A plus MCP23017 and generate no firmware | user (D1, D2), agent (A5) | [0003](decisions/0003-firmwareless-control-and-safe-states.md) |
| C6 | Safe default is full-off and the data-on command is hardware-interlocked with the commanded power-enable result | agent (A3 / P-delegation) | [0003](decisions/0003-firmwareless-control-and-safe-states.md) |
| C7 | Bare USB2517 is justified; JLC four-layer advanced is the provisional minimum tier | agent (A4, A5 / P-delegation) | [0004](decisions/0004-module-and-fabrication-tier.md) |
| C8 | Use dual adjacent GND planes and explicit outer-layer USB transition policy; treat public JLC geometry as provisional until order-time confirmation | agent (placement evidence / P-delegation) | [0005](decisions/0005-usb-stackup-and-layer-transitions.md) |
| C9 | Close the USB hub bulk, aggregate-fault and connector-capacitance envelopes before routing; use a latch-off aggregate eFuse and 0.7 pF shunt ESD devices | agent (independent pre-route review / P-delegation) | [0006](decisions/0006-pre-route-electrical-corrections.md) |
