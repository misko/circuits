status: in-progress
current_release: 07_releases/v0.2.1-2026-08-14
commission_basis: clean-room reconstruction with eight user-authoritative decisions

# Commission brief — pluto-rx2-8way-v5

## Original prompt

UNVERIFIED (reconstructed). The original end-user prompt is intentionally not
available to this clean-room checkpoint, so no prompt hash is asserted.

<!-- prompt-verbatim-begin -->
Fresh ADALM-Pluto RX2-related eight-way RF board.
<!-- prompt-verbatim-end -->

The text between the markers remains a provisional seed, not a claim of
verbatim user wording. The later user statements D1–D8 below are verbatim and
authoritative.

## End goal — definition of done

Design a JLCPCB-manufactured receive-only RF
selector that connects one Pluto Plus RX port to at most one of eight external
SMA antenna ports at a time over 100 MHz through approximately 5.9 GHz. D7
locks N=8 and an independent USB-C 5 V input. D18 adds an alternative two-pin
bench 5 V input on the same protected path. D8 accepts the presented
direction: PE42482A-X, STM32C011F4P6, the framed dwell protocol and the
protected TPS7A2433 3.3 V architecture are selected for schematic entry.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Exactly one Pluto Plus RX port can be connected to no more than one selected antenna among eight ports. | D1 / D7 | met in the sealed hardware design |
| G2 | Every selected path operates from 100 MHz through 5.9 GHz at user-approved insertion-loss, flatness and return-loss limits, measured at approved SMA reference planes. | D2 / D3 | partial — design targets and test plan sealed; first-article VNA evidence owed |
| G3 | Unselected paths meet user-approved common-to-off and antenna-to-antenna isolation limits across the full band. | D1 / D2 | partial — topology and test limits sealed; first-article VNA evidence owed |
| G4 | The selector and Pluto RX input survive the user-approved RF input envelope and meet approved compression/intermodulation limits. | D1 | unmet |
| G5 | An onboard preprogrammed controller autonomously cycles populated antenna states using approved predetermined unique dwell durations; downstream analysis can unambiguously infer state from timing, and reset/power/fault behavior meets approved limits. | D1 / D6 | partial — controller and keyed SWD hardware sealed; firmware and behavioral qualification excluded by D16/D17 |
| G6 | The board operates from either USB-C or a two-pin bench 5 V input without taking operating power from or back-powering the Pluto Plus; the non-isolated inputs are used one at a time. | D1 / D7 / D18 | partial — power-only architecture reviewed; first-article power and misuse tests owed |
| G7 | Common and antenna RF interfaces use SMA, with gender, edge/vertical orientation, cable/stacking arrangement and mechanical envelope approved before floorplanning. | D3 | met — D12/D14 lock exact connector and approved edge arrangement |
| G8 | PCB fabrication and the approved assembly scope pass JLCPCB DFM using a selected controlled-impedance stackup and verified order-time component availability. | D4 / D8 | partial — stackup/tier selected; order echo owed |
| G9 | A first article passes a user-approved VNA/RF test plan covering all populated paths and required states with defined calibration planes, instruments and retained results. | D1–D4 | unmet |

## Log

### A1 — 2026-08-12 — provisional clean-room commission reconstruction

Assumed: The only safe initial product intent was a fresh ADALM-Pluto
RX2-related eight-way RF board; no prior Pluto design result is a design input.

Authority: clean-room checkpoint directive.

Escalate if: the user intends reuse of an existing design.

### A2 — 2026-08-12 — fail closed before approval

Assumed: Hardware generation remains blocked while product-defining limits and
architecture approval are missing.

Authority: clean-room checkpoint directive and open requirements.

Escalate if: the user explicitly approves the proposed ADR and supplies or
delegates the remaining limits.

### Q1 — 2026-08-12 — eight-way meaning and signal flow

Asked: Does "eight-way" mean 1-of-8 selection, eight simultaneous outputs from
one input, eight inputs combined to one output, bidirectional operation, or
another topology? Which ADALM-Pluto RX2 port or internal/external interface is
in scope?

Answer: UNANSWERED at the initial checkpoint; D1 later partially resolves it.

Impact: receive-only one-of-N behavior is locked; D7 later selects N=8. The
exact Pluto Plus RX connector remains open.

### Q2 — 2026-08-12 — RF performance envelope

Asked: What are the minimum/maximum RF frequencies, system impedance,
insertion-loss or gain target, ripple, return loss, isolation, phase/amplitude
matching, noise figure, maximum input/output power, compression,
intermodulation, switching speed, duty cycle, and environmental limits? At
which connector or fixture reference planes are they measured?

Answer: UNANSWERED at the initial checkpoint; D2 later locks only the band.

Impact: 100 MHz to approximately 5.9 GHz is locked; all other RF limits and
measurement conditions remain open.

### Q3 — 2026-08-12 — interfaces, safety, power, and mechanics

Asked: Which RF connectors and control interface are required; what logic
levels, truth table, default state, power-up/reset timing, and unpowered
behavior define boot safety; what power source and voltage/current limits
apply; and what outline, height, mounting, keep-out, cable, and enclosure
constraints apply?

Answer: UNANSWERED at the initial checkpoint; D3 later locks SMA only.

Impact: SMA is locked; gender/orientation, control, power, boot safety and
mechanics remain open.

### Q4 — 2026-08-12 — manufacturing, assembly, test, and calibration

Asked: Which fabrication tier and controlled-impedance stackup are available;
is assembly turnkey, contract, or hand assembly; what package/process limits
apply; and what fixtures, instruments, calibration method, channel sampling,
data retention, and pass/fail report are required?

Answer: UNANSWERED at the initial checkpoint; D4 later locks the fab vendor.

Impact: JLCPCB is locked; service tier, stackup, assembly scope, sourcing and
test remain open.

### D1 — 2026-08-12 — user topology clarification

> means one RX port of the pluto plus connected to at most 8 (or 4) different antennas.

Impact: lock receive-only one-of-N selection with at most one antenna active at
a time; compare N=4 and N=8. Do not infer the exact RX connector.

### D2 — 2026-08-12 — user RF-band clarification

> 100Mhz ~ 5.9Ghz

Impact: lock the desired external selector band to 100 MHz through
approximately 5.9 GHz, subject to the device-rating tension below.

### D3 — 2026-08-12 — user RF-connector clarification

> SMA

Impact: lock the RF connector family. Gender, launch orientation and cables
remain open.

### D4 — 2026-08-12 — user fabrication clarification

> JLCPCB

Impact: lock the PCB fabricator. Assembly use, service tier, materials,
stackup and order-time part eligibility remain open.

### D5 — 2026-08-12 — user acceptance of AD9363 extended operation

> its a AD9363 that is running as a AD9361 , we have reliably used it in the 5.8Ghz mode before, and we will continue doing so accepting the risks

Impact: lock the physical transceiver silicon as AD9363 and the software
profile as AD9361. Prior 5.8 GHz operation is USER-REPORTED/INHERITED, not a
measurement made or independently verified by this design. The user accepts
operation outside ADI's official AD9363 325 MHz–3.8 GHz range for this project;
this does not authorize any claim of ADI-guaranteed complete-system coverage.

### D6 — 2026-08-12 — user autonomous dwell-coded control directive

> it should be controlled by an onboard IC that can be preprogrammed. The downstream analysis will determine switching state by having a predetermined and unique dwell time on each antenna

Impact: lock an onboard preprogrammable controller operating autonomously.
Every populated antenna state has a predetermined unique dwell duration and
downstream analysis infers antenna identity from timing. Do not assume or
require a live Pluto GPIO/control link. Exact durations, accuracy, ordering,
guards/framing, observation rules, startup/fault behavior, programming/update
interface, power, manual override and status output remain OPEN.

### D7 — 2026-08-12 — eight ports and independent USB-C power approved

> yes please

Context: this answers the immediately preceding question, “should I proceed
with eight antenna ports and an independent USB-C 5 V power input?”

Impact: lock N=8 and an independent USB-C nominal-5 V operating-power input.
Do not infer approval of an exact RF switch, MCU, dwell protocol parameters,
USB-C connector, protection device, regulator, current entitlement, input
tolerance/transient envelope, or power schematic.

### D8 — 2026-08-13 — continue with presented exact architecture

> Looks great! please keep going

Context: this follows the presented leading exact parts and architecture:
PE42482A-X, STM32C011F4P6, framed dwell timing, and a simple TPS7A2433-based
protected 3.3 V rail. It authorizes closure of the exact-parts and interface-
proof stage while preserving the requested pause after each stage.

### A3 / D9 — 2026-08-13 — provisional SMA mechanical assumption

Assumed: all nine RF connectors are female/jack right-angle through-hole
Amphenol 901-143-6RFX parts, so ordinary male SMA cables mate to the board.

Authority: agent engineering assumption, explicitly surfaced for review at
this stage pause.

Escalate if: the desired cables require male board connectors, vertical/end-
launch geometry, direct mating, or a constrained enclosure/edge arrangement.

### D10 — 2026-08-13 — programmable 20-ms-class dwell directive

> can we programatically change the dwell times? can we have shorter 20ms dwells?

Impact: make the timing profile a generated firmware/decoder input rather than
duplicated constants. Lock the initial `fast20-v1` profile to unique
20/23/26/30/34/39/44/50 ms active dwells, 5 ms ALL_OFF guards, an 80 ms
marker body, +/-5% disjoint decoder windows, a 386 ms cycle and an 850 ms
recommended capture. Equal 20 ms dwells are not authorized because they would
remove duration-coded antenna identity. Profile changes require regeneration,
validation, firmware build and reflash; this board has no live data interface.

### D11 — 2026-08-13 — direct Raspberry Pi SWD programming

> is there a way to directly program without a programmer?

Context: the immediately preceding answer proposed using the Raspberry Pi as
the SWD adapter through GPIO, with an ST-LINK-compatible recovery fallback.
The user continued with “Wonderful! lets keep going”.

Impact: retain five bare test pads for target-sense 3V3, GND, SWDIO, SWCLK and
NRST. The board remains powered by its own USB-C input. A Raspberry Pi may
directly drive the 3.3 V SWD signals using OpenOCD; no programming IC or
populated connector is added. A conventional ST-LINK may use the same pads.

Superseded interface detail: D13 retains the direct-Pi/ST-LINK SWD method and
self-powered target, but replaces these five loose pads with keyed connector
J11. D11 remains the authority for the programming method, not the final
physical connector.

### D12 — 2026-08-13 — exact SMA connector confirmed

> This looks great! 901-143-6RFX works!

Impact: promote the provisional D9 connector choice to user-confirmed product
authority. J2–J10 are all Amphenol RF `901-143-6RFX` female/jack, right-angle,
through-hole SMA connectors. No rigid direct-mating relationship to the Pluto
or enclosure-driven edge order has been specified; placement remains free to
minimize RF path length and coupling while keeping every mating interface
accessible.

### D13 — 2026-08-13 — proper keyed programming connector

> Lets not have pads but a proper connector please.

Impact: replace TP1–TP5 with J11, exact Samtec
`FTSH-105-01-L-DV-K-P-TR` / JLC `C2932107`, using the standard 10-pin Cortex
Debug/MIPI10 SWD mapping. Pin 1 is target-powered 3V3/VTref, pins 2/4 are
SWDIO/SWCLK, pins 3/5/9 are ground, pin 10 is NRST, and pins 6/7/8 remain
explicit no-connects. A Pi connects through a keyed 10-pin cable and GPIO
breakout; its 40-pin header is not directly pin-compatible. The board remains
self-powered from USB-C and must not be powered through J11.

The accompanying image question triggered a recheck of every SMA against
Amphenol drawing `SMA6252A2-3GT50G-50` Rev C. The five-hole patterns and edge
anchors are correct. The complete holes visible beside connector bodies in the
first render came from a misregistered converted WRL model; the native exact-
code STEP aligns the bodies over the same unchanged copper and shows only the
expected annular-ring crescents.

### D14 — 2026-08-13 — compact five-top, two-per-side mechanics

> is there a reason the board is so big? can we put 5 SMA on the top, and two
> on each side?
>
> how small can we comfortabley go?
>
> Great lets do it!

Impact: replace the conservative 100 x 100 mm four-edge RF ring with a
90 x 65 mm open-bottom U perimeter. The top edge carries ANT2, ANT1, PLUTO RX,
ANT8 and ANT7 at 15-mm centres; the left edge carries ANT3/ANT4 and the right
edge ANT6/ANT5 at 18-mm centres. This is the PE42482 cyclic order cut between
ANT4 and ANT5, so it retains crossing-free single-layer RF fan-out while
freeing the bottom edge for keyed SWD and power-only USB-C. Four M3 holes and
three fiducials remain. The 90 x 65 mm outline is the comfortable target, not
the absolute geometric minimum; cable/tool access and route realization still
receive exact-board review before layout approval.

### D15 — 2026-08-13 — exact compact placement approved

> yes , Great means its approved. Please continue

Context: the approval answers the intentional D15 pause after presentation of
the exact 90 x 65 mm top, oblique and edge renders and the clarification that
the board still contained zero routed segments.

Impact: approve connector access, operational-silk readability and the nine
crossing-free straight RF planning corridors on exact board SHA-256
`3fffbc690051998618880c63afcc559ddd37370e516f4869f670cf51288f2c42`.
This authorizes deterministic route preparation and routing. It does not
approve routed RF launch/fence geometry, declare the PCB fabrication-ready, or
waive the order-stage JLC assembly review of the 0.10 mm SMA drill delta.

### D16 — 2026-08-13 — firmware is opt-in, never a default deliverable

> please do not generate firmware by default for a project only if specifically requested

Impact: firmware generation is outside the default PCB-design pipeline. The
hardware design may retain a programmable controller and programming
interface, but no firmware source, binary, test result or behavioral claim may
be created or included unless the user separately and explicitly requests it.

### D17 — 2026-08-13 — stop Pluto v5 firmware work

> please stop generating firmware

Impact: stop all firmware work for this project immediately. The Pluto v5
release scope is hardware-only and excludes `05_firmware/` in full. The board
retains U2 and keyed SWD connector J11 as hardware interfaces, but this release
does not claim that U2 is programmed or that autonomous dwell switching has
been qualified. Any future firmware work requires a new explicit user request.

### D18 — 2026-08-14 — separate two-pin bench-power input

> Can you also please provide a separate way to get power to the board, can we
> provide two easy pins that we can connect power directly to when at the bench

Impact: add J12, an assembled vertical 1x2 2.54-mm through-hole header beside
USB-C. Pin 1 is nominal +5V on `VBUS_RAW`; pin 2 is GND. Bench power therefore
passes through the same F1, protected-node TVS and U3 path as USB-C. The input
contract remains 4.75V-5.5V. J1 and J12 are not reverse-isolated: connect and
energize exactly one source at a time. The square pin-1 pad and silk identify
polarity, and the board carries an explicit `USB OR J12 - NOT BOTH` warning.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| COM-001 | Derive this design clean-room without prior Pluto results. | agent (A1) | [A1](#a1--2026-08-12--provisional-clean-room-commission-reconstruction) |
| COM-002 | Receive-only one-of-N behavior, 100 MHz–5.9 GHz, SMA and JLCPCB are locked; all named residual requirements stay open. | user (D1–D4) | [D1](#d1--2026-08-12--user-topology-clarification) |
| COM-003 | Accept physical AD9363 operation under an AD9361 software profile outside the AD9363 official band without representing it as ADI-guaranteed coverage. | user (D5) | [D5](#d5--2026-08-12--user-acceptance-of-ad9363-extended-operation) |
| COM-004 | Select eight antenna ports and an independent USB-C nominal-5 V input; leave their exact implementations open. | user (D7) | [D7](#d7--2026-08-12--eight-ports-and-independent-usb-c-power-approved) |
| COM-005 | Continue through exact-part and interface closure using the presented leading architecture, while preserving stage pauses. | user (D8) | [D8](#d8--2026-08-13--continue-with-presented-exact-architecture) |
| COM-006 | Use a generated, versioned 20-ms-class dwell profile while retaining unique duration-coded antenna identity. | user (D10) / agent derived schedule | [D10](#d10--2026-08-13--programmable-20-ms-class-dwell-directive) |
| COM-007 | Expose bare SWD pads so a Raspberry Pi can directly reflash profiles; retain ST-LINK compatibility only as fallback. | user (D11) | [D11](#d11--2026-08-13--direct-raspberry-pi-swd-programming) |
| COM-008 | Use Amphenol RF 901-143-6RFX female right-angle THT SMA connectors for J2–J10. | user (D12) | [D12](#d12--2026-08-13--exact-sma-connector-confirmed) |
| COM-009 | Replace loose SWD pads with a proper keyed 10-pin Cortex connector while retaining direct-Pi and ST-LINK programming. | user (D13) | [D13](#d13--2026-08-13--proper-keyed-programming-connector) |
| COM-010 | Compact the board to a comfortable 90 x 65 mm outline with five top SMAs and two on each side while preserving cyclic RF order. | user (D14) | [D14](#d14--2026-08-13--compact-five-top-two-per-side-mechanics) |
| COM-011 | Approve the exact D15 compact connector/access/render placement and authorize routing to continue. | user (D15) | [D15](#d15--2026-08-13--exact-compact-placement-approved) |
| COM-012 | Make firmware generation opt-in across PCB projects and stop all firmware work for Pluto v5; seal only a hardware archive. | user (D16/D17) | [D17](#d17--2026-08-13--stop-pluto-v5-firmware-work) |
| COM-013 | Add an easy two-pin 5 V/GND bench input on the common protected power path; USB-C and bench power are non-isolated alternatives used one at a time. | user (D18) | [D18](#d18--2026-08-14--separate-two-pin-bench-power-input) |
| 0001 | Select PE42482A-X as one true absorptive solid-state SP8T. | user D8 / agent exact-code proof | [accepted ADR](decisions/0001-one-of-eight-absorptive-sp8t.md) |
| 0002 | Select STM32C011F4P6 and the fixed-order, guarded, framed dwell protocol. | user D8 / agent parameter lock | [accepted ADR](decisions/0002-autonomous-dwell-coded-control.md) |
| 0003 | Select the protected power-only USB-C/J12 alternative inputs and TPS7A2433DBVR 3.3 V rail. | user D8/D18 / agent exact-code proof | [accepted ADR](decisions/0003-usb-c-5v-to-protected-3v3.md) |
| 0004 | Replace the loose programming pads with exact keyed Cortex SWD header J11 and the standard MIPI10 mapping. | user D13 / standards and exact-part proof | [accepted ADR](decisions/0004-keyed-cortex-swd-connector.md) |

## Architecture comparison

The complete evidence and consequences are in accepted
[ADR-0001](decisions/0001-one-of-eight-absorptive-sp8t.md). Summary:

| Architecture | Functional fit | Main tradeoff | Checkpoint disposition |
|---|---|---|---|
| True SP8T | Direct one-of-eight in one RF stage | One IC and eight launches; performance depends on layout/stackup | Selected: PE42482A-X |
| True SP4T | Direct one-of-four in one RF stage | Cannot expose eight antennas | Preferred only if user chooses N=4 |
| Cascaded switches | Can synthesize one-of-eight from SPDT/SP4T elements | More RF stages, loss, traces, controls and transient-state risk | Not recommended absent a binding sourcing/performance reason |
| Commercial SP8T module | Complete characterized switch with SMA/control | High cost/size; bypasses most custom-JLCPCB value; module loss/speed vary | Useful benchmark or fallback, not the custom-board recommendation |
| Passive splitter | Simultaneous distribution with inherent division loss | Does not implement selectable one-of-N | Rejected as functionally incompatible |

## Requirements lock

| Area | Current state |
|---|---|
| Function/direction | LOCKED D1 — receive-only one-of-N; at most one antenna selected |
| Port count | LOCKED D7 — eight antenna ports |
| RF band | LOCKED D2 — 100 MHz to approximately 5.9 GHz |
| Connectors | LOCKED D12/D15 — nine Amphenol RF 901-143-6RFX female right-angle THT SMA; exact lands/datums and outward access on board SHA `3fffbc690051` are human-approved; routed launches remain OPEN |
| Fabricator | LOCKED D4/D8 — JLCPCB advanced four-layer, JLC04161H-7628; 0.295/0.200-mm CPWG source geometry solved; order echo OPEN |
| Receiver silicon/profile | LOCKED D5 — physical AD9363 using AD9361 software profile; extended-band risk accepted |
| Control architecture | LOCKED D6 — onboard preprogrammable controller, autonomous cycling, unique dwell duration per populated antenna; no live Pluto GPIO link assumed |
| Control parameters | LOCKED D10 — generated `fast20-v1`, 20–50 ms unique dwells, 5 ms guard, ≥76 ms marker detection, ±5% windows, BOR4/IWDG/SWD, passive ALL_OFF |
| Reprogramming | LOCKED D11/D13/D18 — direct Raspberry Pi GPIO SWD through exact keyed J11 and a Pi breakout harness; board powered by exactly one of USB-C or J12; standard-probe fallback; no live runtime data interface |
| Power | LOCKED D7/D8/D18 — power-only Type-C or J12 bench input, 4.75–5.5 V, 20 mA; common passive protection and TPS7A2433DBVR; non-isolated inputs used one at a time; no active OVP/eFuse/data/PD |
| RF limits | PROVISIONAL — 0 dBm operating limit and first-article loss/isolation/return-loss targets; final evidence requires VNA |
| Timing/state | LOCKED — ALL_OFF guards and reset state; 1.4 µs switch-settling ceiling is far below the 5 ms guard |
| Mechanics | LOCKED D14/D15 for the current no-enclosure scope — compact 90x65-mm outline, five-top/two-per-side exact SMAs, four M3 holes, three fiducials and cyclic U-perimeter placement are realized and human-approved on SHA `3fffbc690051`; no rigid Pluto or enclosure mate is specified |
| Assembly | PROVISIONAL — five JLC first articles, top-side SMT plus nine wave-solder SMA; uploader echo required |
| Test | METHOD LOCKED / AVAILABILITY OPEN — ≥6 GHz VNA, SMA-plane calibration, all paths/states and retained Touchstone data |

## Spec tensions

### Official transceiver comparison

| Device | Official ADI frequency rating | Official channel description | Consequence here |
|---|---|---|---|
| AD9363 | 325 MHz–3.8 GHz; channel bandwidth up to 20 MHz | RF 2 × 2 transceiver | D5 confirms this is the physical silicon. D5 accepts operation outside its official band; ADI does not guarantee the requested endpoints. |
| AD9361 | RX 70 MHz–6.0 GHz; channel bandwidth below 200 kHz to 56 MHz | RF 2 × 2 transceiver | D5 confirms this is the software profile, not physical AD9361 silicon; its device rating cannot be transferred to AD9363 silicon. |

The switch-board path target remains 100 MHz–5.9 GHz independently of the
receiver IC. Prior reliable 5.8 GHz use is USER-REPORTED/INHERITED and was not
independently measured by this design. Assembled-path characterization may
support an article-specific result, but this project must never describe
complete-system extended-band coverage as guaranteed by ADI.

The Pluto+ maintainer describes its hardware as AD9363 that can be "hacked"
to an AD9361 or AD9364 software profile. A software/profile change is not proof
of AD9361 silicon and does not promote an AD9363 to the AD9361 data-sheet
limits. If manufacturer-specified 100 MHz–5.9 GHz system coverage is binding,
the fitted device must be confirmed as a genuine AD9361 (or another receiver
officially rated for the band).

| id | requirement | official/maintainer evidence | how honoured now | ADR | user-flagged |
|---|---|---|---|---|---|
| T1 — ACCEPTED D-SPEC TENSION | 100 MHz–5.9 GHz at a Pluto Plus RX port | Physical silicon is AD9363, officially 325 MHz–3.8 GHz; it runs an AD9361 software profile, whose physical device is officially rated 70 MHz–6 GHz. D5 reports reliable prior 5.8 GHz use and accepts the risk of AD9363 out-of-range operation. | Keep the selector requirement independent at 100 MHz–5.9 GHz; characterize the assembled path, label prior use USER-REPORTED/INHERITED, and never claim ADI-guaranteed complete-system extended-band coverage. | [0001](decisions/0001-one-of-eight-absorptive-sp8t.md) | yes — accepted by D5 |
| T2 | Receive-only antenna input versus +2.5 dBm receiver damage ceiling | ADI states AD9363 RF inputs have a +2.5 dBm absolute maximum. | Set 0 dBm operator limit; retain +2.5 dBm only as survival ceiling; no transmitter/high-power protection claim. | [0001](decisions/0001-one-of-eight-absorptive-sp8t.md) | yes |
| T3 | JLCPCB fabrication over 5.9 GHz | JLCPCB publishes exact controlled-impedance multilayer stackups and calculator inputs. | Use advanced four-layer JLC04161H-7628 and the retained 0.295/0.200-mm CPWG source geometry; realize/audit each launch during routing and validate every path on the first article. | [0001](decisions/0001-one-of-eight-absorptive-sp8t.md) | yes |

Sources: [Pluto+ maintainer](https://github.com/plutoplus/plutoplus),
[AD9363 product page](https://www.analog.com/en/products/ad9363.html),
[ADI CN0534](https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/cn0534.html),
[AD9361 product page](https://www.analog.com/en/products/ad9361.html), and
[JLCPCB capabilities](https://jlcpcb.com/capabilities/Capabilities%2C/).

## Mating fact-lock

No direct mechanical stacking or rigid mating to a Pluto Plus is authorized.
The current boundary is an SMA-connected RF cable, but its gender, length,
loss and routing are OPEN. Therefore the floorplan may consume no Pluto Plus
dimensions.

| External fact | Grade | Intended use | Current state |
|---|---|---|---|
| Physical transceiver silicon and software profile | USER-REPORTED/INHERITED — D5 | Electrical rating/risk boundary | LOCKED — AD9363 silicon, AD9361 profile; extended-band risk accepted |
| Exact Pluto Plus hardware revision and RX port | OWED | Common-port identity | OPEN |
| Common-port SMA gender/orientation and cable | USER D12/D15 / cable still OWED | Launch and system loss budget | 901-143-6RFX female/right-angle LOCKED; north-edge mating face and placement approved; cable and routed launch remain OPEN |
| Enclosure/mounting/antenna SMA geometry | no enclosure supplied / layout-derived | Board boundary and placement | 90x65-mm board, four M3 holes and nine accessible edge SMAs realized; enclosure compatibility is not claimed |

## Commission fact-lock

| Fact | Locked value | Locked by |
|---|---|---|
| RF function | Receive-only one-of-N; zero or one antenna connected; never more than one | D1 |
| Port count | N=8 | D7 |
| RF band | 100 MHz to approximately 5.9 GHz | D2 |
| RF connector family | SMA | D3 |
| PCB fabricator | JLCPCB | D4 |
| Receiver silicon/profile and extended-band posture | Physical AD9363 using AD9361 software profile; risk accepted; prior 5.8 GHz reliability USER-REPORTED/INHERITED; no ADI-guaranteed extended-band claim | D5 |
| Control function | Onboard preprogrammable IC autonomously cycles populated antennas; each has a predetermined unique dwell; downstream analysis infers state from timing; no live Pluto control link assumed | D6 |
| Integration posture | One PE42482A-X bare SP8T; module trade rejected on total system complexity | D8 / ADR-0001 accepted |
| RF performance/measurement boundary | Provisional numeric targets at SMA mating planes; VNA evidence required | A3 |
| Control/default/switching | STM32C011F4P6, exact truth table, generated `fast20-v1` framed profile, passive ALL_OFF/BOR4/IWDG | D8 / D10 / ADR-0002 accepted |
| Programming | Exact keyed 10-pin Cortex J11 carries VTref/GND/SWDIO/SWCLK/NRST; direct Raspberry Pi GPIO SWD needs a breakout harness; standard-probe fallback; target power comes from exactly one of J1/J12 | D11/D13/D18 |
| Power source | Independent USB-C nominal 5 V input or J12 two-pin bench 5 V input, one at a time | D7/D18 |
| Power implementation | Exact passive protection and TPS7A2433DBVR; 4.75–5.5 V/20 mA; no active OVP/data/PD/reverse isolation; explicit no-simultaneous-input warning | D8/D18 / ADR-0003 accepted |
| Mechanics/cabling | Nine exact 901-143-6RFX female right-angle SMA connectors locked; D14 90x65-mm outline, mounting and cyclic open-U edge order realized; exact compact placement approved; cable loss and routed geometry remain OPEN | D12–D15 + board SHA `3fffbc690051` |
| Assembly/test | Five JLC first articles proposed; uploader allocation and instrument availability remain OPEN | A3 |

## Exact-parts and interface gate

The architecture and electrical method are closed, and the D14 compact
mechanics have now been regenerated from source as an exact track-free
placement. J11 remains present with the standard target-powered Cortex
mapping; the RF cross-section and exact SMA copper/datum geometry are
unchanged. The 90 x 65 mm board passes placement DRC and route preflight, and
the cyclic U-perimeter has no straight RF-corridor crossings. D15 approves the
exact track-free placement and authorizes routing; routed copper remains
unstarted. No fab-ready claim exists.

Before fabrication, provide/confirm the at-least-6 GHz VNA and calibration
fixtures, pass the JLC uploader echo, and approve the complete first-article
test plan plus the exact SMA drill delta in JLC assembly DFM.
