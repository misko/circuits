# brief: pi-usb-port-switch

status: achieved
prompt_sha256: 2a83e1ad13bd5a004709e4315fe4a609d37e2d6371a84c065b3f6b7aa74f1c59
current_release: v0.1.0-2026-08-15

## Original prompt

<!-- prompt-verbatim-begin -->
/pcb-design a board that can be used with raspberry pi GPIO that can toggle on and off diffferent USB A ports . This will be used to debug and develop USB applications, where connecting/disconnecting is required. We want to allow the rpi to disconnect data only while leaving power connected, or disconect both power and data. We should be able to control up to 4 USB ports with this . This board will pass through connections into the pi and allow us to fully control power  or data lines
<!-- prompt-verbatim-end -->

- date: 2026-08-14
- channel: user request

## End goal — definition of done

Deliver an assembled, orderable four-channel USB inline switch for Raspberry
Pi development. GPIO control independently selects full connection, power-only
connection, or full disconnect on every downstream USB-A port without
disconnecting ground. The final design is source-reproducible and passes the
repository's schematic, controlled-impedance routing, DRC/parity, sourcing,
JLCPCB assembly, digital-twin, render, and release gates.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Control up to four downstream USB-A ports independently from Raspberry Pi GPIO | P | met — `verification/electrical_invariants.json` 282/282 and J2 GPIO map in the sealed schematic |
| G2 | Each channel can disconnect both USB conductors while leaving VBUS powered | P | met — per-channel hardware `DATA_OK` interlock and 282/282 netlist invariants |
| G3 | Each channel can disconnect VBUS and both USB data conductors together | P | met — safe-state truth table and pull-down/interlock invariants |
| G4 | Connections pass one-to-one between Raspberry Pi host ports and downstream device ports | P, Q2 | met — 56/56 critical pair routes and connector/pin review SOUND |
| G5 | GPIO/reset/unpowered behavior is deterministic and electrically safe | P, Q4 | met — physical pull-downs plus hardware power/data interlock; topology review SOUND |
| G6 | JLCPCB-assembled release passes all applicable electrical, SI, mechanical, sourcing, and assembly gates | P, A2 | met — v0.1.0 staged archive: DRC 0/0/0, ERC 0 errors, A-POP PASS, stock 25/25, twin 185/185, model 190/190; order remains held for uploader/first article |
| G7 | No firmware is generated unless explicitly requested | D1, D2 | met — `05_firmware/` contains its binding contract only |

## Log

### D1 — prior standing user directive

> please do not generate firmware by default for a project only if specifically requested

Impact: `05_firmware/` retains only its binding contract. No MCU firmware,
Raspberry Pi daemon, or host utility is part of this commission.

### D2 — prior standing user directive

> please stop generating firmware

Impact: Reinforces D1. Hardware-safe states must not depend on code.

### Q1 — 2026-08-14 — USB generation

Asked: Should every channel carry USB 2.0 only, or must it preserve USB 3.x
SuperSpeed as well? USB 2.0 is recommended for a smaller, simpler, more easily
verified development fixture; USB 3.x requires switching the SuperSpeed pairs
in addition to D+/D-.

Answer: See D3: try USB 3, with USB 2 accepted as the fallback.

Impact: Selects connector/pin count, switching ICs, stackup, routing contract,
and signal-integrity verification.

### Q2 — 2026-08-14 — Pi and upstream physical connection

Asked: May the board be cable-connected and Pi-model-independent, using four
rugged USB-B upstream receptacles plus four USB-A downstream receptacles and a
GPIO control cable/header, or must it directly mount and align with a specific
Raspberry Pi model? The cable-connected form is recommended.

Answer: See D3 and A3: support standard full-size Raspberry Pi 4 and 5 with a
cable-connected, model-independent interface.

Impact: Selects eight USB connectors versus a Pi-specific rigid interface and
determines whether a Raspberry Pi mating fact-lock is required.

### Q3 — 2026-08-14 — VBUS source and current

Asked: Should each downstream port use only the VBUS arriving from its matching
Raspberry Pi USB port, or use a separate external 5 V supply? What continuous
current should the board support per port? Pi-VBUS pass-through is recommended
for a true inline fixture; an external supply needs a separate power and
backfeed architecture.

Answer: See D3 and A5/A6: use a separate regulated 5.15-5.25 V source rated at
least 5 A; design for 0.9 A continuous per port.

Impact: Selects the per-port power switch, current limit, reverse-current
blocking, connector rating, copper class, protection, and measurement plane.

### Q4 — 2026-08-14 — hardware default and interlock

Asked: May reset, an unpowered Pi, and floating GPIOs force every channel to
fully disconnected, with hardware preventing data-on while VBUS is off? This
fail-safe default is recommended. The allowed states would be full-off,
power-only, and fully connected.

Answer: See D3: yes, require fail-safe full-off defaults and a hardware
power/data interlock.

Impact: Selects enable polarity, physical pulls, and whether a hardware logic
interlock is required.

### A1 — 2026-08-14 — ground and shield scope

Assumed: Port control never switches protective/common ground. USB cable shield
handling will follow the selected connector topology and applicable USB/EMC
guidance rather than being treated as a fourth user-controlled conductor.
Authority: P requests power and data control only.
Escalate if: galvanic isolation or ground disconnect is required.

### A2 — 2026-08-14 — manufacturing target

Assumed: The `/pcb-design` pipeline's standard deliverable applies: a complete
JLCPCB-assembled PCBA, initially at the least-cost capable fabrication tier.
Authority: the invoked skill's PCBA contract.
Escalate if: bare-PCB delivery, another assembler, or a fixed size/cost ceiling
is required.

### D3 — 2026-08-14 — user response to Q1-Q4

> 1) lets try for 3, but 2 works
> 2) just the full original / standard rpi4 and rpi5
> 3) separate 5v
> 4) yes

Impact: Target USB 3 Gen 1 where practical with USB 2.0 as the accepted
fallback; support full-size Raspberry Pi 4 Model B and Raspberry Pi 5; power
downstream VBUS from a separate regulated 5 V input; and require fail-safe
full disconnect plus a hardware data/power interlock.

### A3 — 2026-08-14 — cable-connected Pi interface

Assumed: Use standard cables rather than rigidly aligning to the Pi body: four
short USB 3 A-to-B upstream cables and a Raspberry Pi 40-pin GPIO ribbon/header.
This supports both named models without consuming their body or USB-stack
dimensions. Each channel uses the same USB 3-capable PCB path; the two black
Pi ports naturally operate through the USB 2 conductors only.
Authority: D3 names supported models but does not override the recommended
cable-connected topology in Q2.
Escalate if: the PCB must mount directly on the Pi or align to its USB sockets.

### A4 — 2026-08-14 — four identical data paths

Assumed: Build four identical USB 3 Gen 1-capable channels rather than two USB
3 and two USB 2 PCB variants. Raspberry Pi 4 and 5 each expose two USB 3 and two
USB 2 ports; an identical USB 3 A-to-B cable/path falls back to USB 2 when its
upstream A plug is inserted into a USB 2 host receptacle.
Authority: D3 requests trying USB 3 while accepting USB 2.
Escalate if: reducing cost/area by making two channels USB 2-only is preferred.

### Q5 — 2026-08-14 — downstream current

Asked: What continuous current should the separate 5 V source deliver per
port? Recommended default: 0.9 A per port, all four simultaneously, matching
the USB 3.2 self-powered downstream-port test load; specify a regulated 5 V,
at least 5 A external supply to retain distribution and transient margin.

Answer: UNANSWERED.

Impact: Locks the input connector/rating, per-port current limit, copper and
thermal design, bulk capacitance, and VBUS measurement plane.

### A5 — 2026-08-14 — provisional USB current envelope

Assumed: Design for 0.9 A continuous per downstream port with all four ports
loaded simultaneously. Require a regulated 5.15-5.25 V source rated at least
5 A at the board input. Deliver 4.75-5.25 V
at the downstream USB-A mated test plug at 0.9 A, including input protection,
the per-port switch, PCB interconnect and the mated output contacts. The
external supply lead is outside that boundary.
Authority: D3 delegates the detailed external-supply envelope; 0.9 A is the
USB 3.2 self-powered downstream-port test load and is the conservative standard
target for the requested USB 3-capable fixture.
Escalate if: a downstream device needs more than 0.9 A continuous, or the
available supply cannot hold 5.15 V at the board input under a 4.1 A board load.

### A6 — 2026-08-14 — 5.15 V board-terminal minimum

Assumed: Interpret the requested separate 5 V source as a regulated nominal
5.2 V supply, with 5.15 V minimum and 5.25 V maximum at the board terminal under
load. A 5.0 V board-terminal minimum cannot guarantee 4.75 V at the downstream
mated plug after the input fuse and holder, reverse-polarity MOSFET, shared
trunk, TPS2557, branch copper and connector contacts. This is an admitted input
requirement, not hidden voltage-drop margin.
Authority: D3 selects a separate 5 V source and delegates the exact electrical
envelope; the selected protected four-port architecture requires the margin.
Escalate if: only a 5.0 V-minimum source is available; the input-protection
architecture or the 4.75 V output guarantee must then be reopened.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| C1 | Up to four independently controlled downstream USB-A ports | user (P) | P |
| C2 | Required states include power-only and full disconnect | user (P) | P |
| C3 | Ground is not user-switched | agent (A1 / P-delegation) | A1 |
| C4 | Deliver an assembled JLCPCB PCBA at the least-cost capable tier | agent (A2 / skill contract) | A2 |
| C5 | Do not generate firmware or host software | user (D1, D2) | D1, D2 |
| C6 | Target USB 3 Gen 1 with USB 2 fallback accepted | user (D3) | D3 |
| C7 | Support full-size Raspberry Pi 4 Model B and Raspberry Pi 5 | user (D3) | D3 |
| C8 | Use a separate regulated 5 V downstream supply | user (D3) | D3 |
| C9 | Default fully off and interlock data enable with power enable | user (D3) | D3 |
| C10 | Use cable-connected, model-independent USB and GPIO interfaces | agent (A3 / D3-delegation) | A3 |
| C11 | Implement four identical USB 3-capable channels | agent (A4 / D3-delegation) | A4 |
| C12 | Design for 0.9 A per port, all four simultaneous, from a regulated 5 V / 5 A source | agent (A5 / D3-delegation) | A5 |
| C13 | Pi 4/5 port-speed ceiling and identical-channel response | agent | [0001](decisions/0001-pi-port-speed-envelope.md) |
| C14 | USB 3 is a first-article qualification target, not a compliance claim | agent | [0002](decisions/0002-usb3-inline-fixture-qualification.md) |
| C15 | Power-only mode makes no USB charging-current advertisement | agent | [0003](decisions/0003-power-only-is-not-a-charging-port.md) |
| C16 | Use JLC standard four-layer fabrication as the cost ceiling | agent | [0004](decisions/0004-jlc-standard-four-layer-cost-ceiling.md) |
| C17 | Escalate to JLC four-layer advanced to retain the requested USB 3 attempt | agent | [0005](decisions/0005-advanced-tier-for-usb3-escape.md) |
| C18 | Require 5.15-5.25 V at the board input to preserve the downstream VBUS guarantee | agent | [0006](decisions/0006-5v-input-drop-budget.md) |

## Spec tensions

| id | requirement | standard/part cap | how honoured | ADR | user-flagged |
|---|---|---|---|---|---|
| T1 | Four USB 3-capable controlled paths | Pi 4 and Pi 5 expose only two USB 3 host ports; the other two are USB 2 | Build four identical USB 3-capable paths; on the named hosts, at most two operate at 5 Gb/s and the others fall back to USB 2 | [0001](decisions/0001-pi-port-speed-envelope.md) | yes |
| T2 | USB 3 operation through an inline disconnect fixture | The added upstream cable, two connectors, protection and active switch/redriver are outside a simple passive-cable topology and consume channel margin | Treat 5 Gb/s as a first-article qualification target; bind short upstream cables, controlled impedance, redriver settings and link/throughput evidence; make no USB-IF compliance claim | [0002](decisions/0002-usb3-inline-fixture-qualification.md) | yes |
| T3 | Keep VBUS on while all data is disconnected | With no data or BC advertisement, a device is not promised charging current merely because the fixture can electrically supply 0.9 A | Supply a protected 5 V rail but make no dedicated-charging-port claim; device draw/behavior in power-only mode is part of first-article functional testing | [0003](decisions/0003-power-only-is-not-a-charging-port.md) | yes |
| T4 | Attempt USB 3 at the least-cost capable JLC tier | Exact 0.5 mm-pitch redriver and ESD packages require advanced escape geometry under P-ESC; standard four-layer is the USB 2-only fallback | Select four-layer advanced for the USB 3 attempt; if cost must remain standard-tier, supersede this design with a USB 2-only architecture | [0005](decisions/0005-advanced-tier-for-usb3-escape.md) | yes |
| T5 | Use a separate 5 V source and guarantee at least 4.75 V at a loaded downstream plug | A 5.0 V board-terminal minimum leaves no defensible allowance for fuse, reverse-polarity FET, current limiter, copper and connector drop | Require a regulated 5.15-5.25 V source at the board terminal; reopen protection or output guarantee if only 5.0 V minimum is available | [0006](decisions/0006-5v-input-drop-budget.md) | yes |

## Mating fact-lock

none — under A3 this board does not mechanically mate or align to Raspberry Pi
hardware. It uses standard USB cables and a GPIO ribbon/header. If A3 is
overridden by a direct-fit requirement, this section reopens before floorplan.

## Commission fact-lock

| Fact | Value | Locked by |
|---|---|---|
| USB data envelope | Four identical USB 3 Gen 1-capable paths carrying USB 2 D+/D- plus SuperSpeed TX/RX; USB 2 fallback accepted | D3, A4 |
| Output rail(s): Vout min-max @ Imax | 4.75-5.25 V at 0.9 A per port | D3, A5 |
| External outputs: connector count + simultaneous count | Four USB-A outputs; all four may be controlled simultaneously | P |
| Duty: continuous and peak current/time | 0.9 A continuous on all four ports simultaneously; transient qualification follows USB VBUS droop testing | P, A5 |
| Measurement plane + included/excluded path elements | Downstream USB-A mated test plug including input protection, power switch, PCB copper/vias/joints, and mated output contacts; external supply lead excluded | A3, A5 |
| Input envelope: Vin min-max, source type | External regulated 5.15-5.25 V source, at least 5 A at the board terminal | D3, A5, A6 |
| Protection posture | Switch all three USB data pairs; per-port current limiting and reverse-voltage protection; external 5 V must never feed upstream Pi VBUS | P, D3 |
| Off-control / storage | Reset/floating GPIOs force full disconnect; data path can connect only while that port's power command is enabled | D3 |
| Hard-cell parts: USB 3/2 data switches, power switch, USB 3 A/B connectors | exact TUSB522PIRGER, TS3USB221ERSER, TPS2557DRBR, Wurth 692121030100/692221030100 and associated protection/control identities passed the dated 27/27 Q-2SOURCE and P-ESC gate; USB 2 remains the fallback if first-article 5 Gb/s qualification fails | D3, parts-stage evidence |
| Integration posture | No onboard programmable controller; direct Pi GPIO control; no firmware | P, D1, D2 |
