status: in-progress
prompt_sha256: 73597f7ce6d0079d891d1d2e44b7e0fa33ac542160dcb276905042d880bd61fd
current_release: no

# Commission record — programmable USB 2.0 hub

## Original prompt

Date: 2026-07-31
Channel: user request

<!-- prompt-verbatim-begin -->
Please use the pcb design skill in this repo to make programmable USB 2 hub, capable of delivering 3A per USB socket, and full controlable by usb host (power cycle, power status, data connect, data disconnect, data status).
<!-- prompt-verbatim-end -->

## End goal — definition of done

Deliver an assembled, orderable four-port USB 2.0 hub whose downstream power
and physical data paths are independently controlled and observed by its USB
host, with a verified KiCad design, tested management firmware/host utility,
and a complete JLCPCB PCBA release.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Four downstream USB-A sockets | P, Q1 | unmet |
| G2 | Each downstream socket can continuously deliver 5 V at 2 A at the mated test plug, subject to an explicit current limit and thermal design | Q2 | in verification |
| G3 | USB 2.0 high-speed hub connectivity to the upstream host | P | unmet |
| G4 | Host can power-cycle each port independently | P | unmet |
| G5 | Host receives per-port commanded power state, power-present state, and fault/overcurrent status | P | unmet |
| G6 | Host can physically connect and disconnect each port's D+/D- pair independently | P, Q1 | unmet |
| G7 | Host receives both commanded data-switch state and actual hub attach/enumeration state | P, Q1 | unmet |
| G8 | Input accepts 12–24 V DC from a source rated at least 75 W | Q1 | unmet |
| G9 | Complete assembled JLCPCB release passes ERC, DRC 0/0/0, parity, assembly, sourcing, twin, pin, render, and policy gates | P | unmet |

## Log

### Q1 — 2026-07-31 — clarification asked

Asked: How many downstream ports and which connector; what input power
envelope; whether data disconnect must physically isolate D+/D-; and whether
data status must cover both commanded switch state and real attach/enumeration.

Answer:

> 1) 4 x USBA, 2) sounds good, 3) yes, 4) lets do both then

Impact: Locks four USB-A downstream ports, 12–24 V / at least 75 W external
DC input, one physical USB 2.0 data switch per port, and combined hardware plus
host-enumeration status.

### A1 — 2026-07-31 — assumption (protection posture)

Assumed: The 3 A requirement means 3 A continuous usable output per port, not
merely a 3 A trip ceiling. Each port therefore receives an independently
enabled current-limited high-side switch, reverse-current blocking or proven
backfeed prevention, local bulk capacitance, switched-VBUS sensing, and an
overcurrent/fault indication. Input protection includes a replaceable or
resettable fuse, reverse-polarity protection, surge/TVS clamp, UVLO, and OVLO.
Authority: P delegates circuit implementation while Q1 locks the current.
Escalate if: no USB-A receptacle with a cited continuous-current rating of at
least 3 A can be assembled or consigned.

### A2 — 2026-07-31 — assumption (whole-board off control)

Assumed: This is externally powered equipment, not a battery product. Removing
or switching the external 12–24 V feed is the master de-energization method;
while input remains present, the management controller and hub remain powered
so the host can turn all four downstream power and data paths off.
Authority: Q1 selects an external DC source.
Escalate if: a latching whole-board electronic off state is required.

### A3 — 2026-07-31 — assumption (upstream connector)

Assumed: Use a USB-B receptacle for the upstream USB 2.0 connection. The board
is self-powered, senses upstream VBUS, and never sources power into it.
Authority: P requires USB-host control but does not select the upstream shell;
USB-B is the simplest unambiguous self-powered-hub interface.
Escalate if: the enclosure or host cable requires USB-C upstream.

### A4 — 2026-07-31 — assumption (control plane)

Assumed: Use a hub with at least five downstream ports; four serve the external
USB-A connectors and one internal port serves a native-USB management MCU.
The MCU exposes a versioned vendor control interface and the supplied host
utility combines MCU telemetry with the operating system's hub port
connection/enumeration state.
Authority: P requires control by the same USB host and Q1 requires both status
views.
Escalate if: no sourceable hub/controller combination can provide the internal
management path without compromising USB 2.0 compliance.

### A5 — 2026-07-31 — measured load context (Pluto+ SDR)

The Pluto+ project specifies a **5 V, 2 A** DC input. This is treated as the
required source rating, not as evidence that every operating mode continuously
draws 2 A. Four Pluto+ loads therefore establish a 40 W credible application
budget, while the original 3 A-per-socket requirement remains the hardware
design envelope for cable-drop, startup, and other loads.
Source: https://github.com/plutoplus/plutoplus, read 2026-07-31.

### Q2 — 2026-08-01 — current and module-policy revision

Answer:

> Module-first policy: LM5116, STM32, and USB2517 need explicit module-vs-chip decisions. dont need to be too strict, if its only a few support components its file. If its an PI chip with 10+ components supporting it, thats a different call.
>
> 3A lets lower to 2A would that help?

Impact: Replaces the 3 A guarantee with 2 A continuous at each mated USB-A
receptacle and adopts a complexity-weighted module policy. Bare ICs with fewer
than ten external support parts need a rationale; integrations at or above ten
need an evidenced module trade study. The connector remains rated for 3 A.

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| C1 | Four USB-A downstream ports | user (Q1) | Q1 |
| C2 | 12–24 V DC, at least 75 W input | user (Q1) | Q1 |
| C3 | Physical D+/D- isolation per external port | user (Q1) | Q1 |
| C4 | Report commanded data state and actual attach/enumeration | user (Q1) | Q1 |
| C5 | Conservative input and per-port protection posture | agent (A1 / P-delegation) | A1 |
| C6 | External-feed removal is whole-board de-energization | agent (A2 / Q1-delegation) | A2 |
| C7 | USB-B upstream connector | agent (A3 / P-delegation) | A3 |
| C8 | Internal management MCU behind a fifth hub port | agent (A4 / P-delegation) | A4 |
| C9 | Guarantee 2 A continuously per port at the mated test plug | user (Q2) | Q2 |
| C10 | Use complexity-weighted module decisions with a default ten-support-part trade-study threshold | user (Q2) | Q2 |
| 0001 | Treat USB-A 2 A as a proprietary high-current capability with explicit connector and protocol limits | agent (Q2 implementation) | [ADR-0001](decisions/0001-usb-a-3a-spec-tension.md) |
| 0002 | Retain two independent 5.16 V / 4 A LM5116 rails, two ports per rail | agent (Q2 implementation) | [ADR-0002](decisions/0002-dual-seven-amp-bucks.md) |
| 0003 | Put the management MCU on internal hub port 5 and combine vendor telemetry with standard host hub status | agent (A4 / P-delegation) | [ADR-0003](decisions/0003-control-and-status-plane.md) |
| 0004 | Retain the reviewed LM5116 cells using maximum-Qg AON6266E switches, a 110 kHz bounded high corner, and a 2 A complete-path margin | agent (Q2 implementation) | [ADR-0004](decisions/0004-power-architecture-backtrack.md) |

## Spec tensions

| id | requirement | standard/part cap | how honoured | ADR | user-flagged |
|---|---|---|---|---|---|
| T1 | 5 V / 2 A from a USB-A downstream port | USB 2.0 unit loads and BC 1.2 do not advertise a generic 2 A entitlement | Proprietary high-current capability, hardware current limiting, no USB-IF-compliance claim for the 2 A power mode, and a receptacle cited for >=3 A continuous | [0001](decisions/0001-usb-a-3a-spec-tension.md) | yes |

## Mating fact-lock

none — this board does not mate to hardware this repo did not design.

## Commission fact-lock

| Fact | Locked value | Locked by |
|---|---|---|
| Downstream rail envelope | Four independent ports, 4.75–5.25 V at mated test plug, 2.0 A continuous per port | Q2 |
| Aggregate downstream load | 40 W maximum delivered load, excluding conversion and hub overhead | Q2 |
| Input envelope and source type | 12–24 V DC, external SELV supply, at least 75 W | Q1 |
| Protection posture | Input fuse/reverse/TVS/UVLO/OVLO; per-port current limit, fault, switched-voltage sense, and backfeed prevention | A1 |
| Off control | Remove/switch external feed for full off; host may independently disable every downstream power/data path while logic remains alive | A2 |
| Upstream interface | Self-powered USB 2.0 over USB-B; VBUS sense only and no upstream backfeed | A3 |
| Host control plane | Internal native-USB MCU behind hub port 5; versioned control protocol plus host-side hub enumeration query | A4 |
| USB-A connector sourcing class | Must retain >=3 A cited continuous contact rating for 2 A use; consignment permitted with an assembly record | Q2, ADR-0001 |
| Hub/control silicon sourcing class | At least five downstream hub ports plus native-USB MCU, both JLC-placeable or explicitly consigned | A4; sourcing spike pending |
| Component availability | Every selected component has the exact MPN, or an approved dossier alternate, active and orderable from at least two independent authorized supplier pools with stock sufficient for five boards | Q-2SOURCE; verify before schematic completion and again on order day |
