status: draft
current_release: no
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
locks N=8 and an independent USB-C 5 V input. D8 accepts the presented
direction: PE42482A-X, STM32C011F4P6, the framed dwell protocol and the
protected TPS7A2433 3.3 V architecture are selected for schematic entry.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Exactly one Pluto Plus RX port can be connected to no more than one selected antenna among eight ports. | D1 / D7 | unmet |
| G2 | Every selected path operates from 100 MHz through 5.9 GHz at user-approved insertion-loss, flatness and return-loss limits, measured at approved SMA reference planes. | D2 / D3 | unmet |
| G3 | Unselected paths meet user-approved common-to-off and antenna-to-antenna isolation limits across the full band. | D1 / D2 | unmet |
| G4 | The selector and Pluto RX input survive the user-approved RF input envelope and meet approved compression/intermodulation limits. | D1 | unmet |
| G5 | An onboard preprogrammed controller autonomously cycles populated antenna states using approved predetermined unique dwell durations; downstream analysis can unambiguously infer state from timing, and reset/power/fault behavior meets approved limits. | D1 / D6 | unmet |
| G6 | The board operates from an independent USB-C 5 V input without taking operating power from or back-powering the Pluto Plus; its remaining input envelope and protection limits are approved. | D1 / D7 | unmet |
| G7 | Common and antenna RF interfaces use SMA, with gender, edge/vertical orientation, cable/stacking arrangement and mechanical envelope approved before floorplanning. | D3 | unmet |
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
| 0001 | Select PE42482A-X as one true absorptive solid-state SP8T. | user D8 / agent exact-code proof | [accepted ADR](decisions/0001-one-of-eight-absorptive-sp8t.md) |
| 0002 | Select STM32C011F4P6 and the fixed-order, guarded, framed dwell protocol. | user D8 / agent parameter lock | [accepted ADR](decisions/0002-autonomous-dwell-coded-control.md) |
| 0003 | Select the exact protected power-only USB-C sink and TPS7A2433DBVR 3.3 V rail. | user D8 / agent exact-code proof | [accepted ADR](decisions/0003-usb-c-5v-to-protected-3v3.md) |

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
| Connectors | LOCKED D3 SMA family / PROVISIONAL D9 exact connector — nine female right-angle THT SMA; edge order/cable/enclosure review OPEN |
| Fabricator | LOCKED D4/D8 — JLCPCB advanced four-layer, JLC04161H-7628; RF solver/order echo OPEN |
| Receiver silicon/profile | LOCKED D5 — physical AD9363 using AD9361 software profile; extended-band risk accepted |
| Control architecture | LOCKED D6 — onboard preprogrammable controller, autonomous cycling, unique dwell duration per populated antenna; no live Pluto GPIO link assumed |
| Control parameters | LOCKED D10 — generated `fast20-v1`, 20–50 ms unique dwells, 5 ms guard, ≥76 ms marker detection, ±5% windows, BOR4/IWDG/SWD, passive ALL_OFF |
| Reprogramming | LOCKED D11 — direct Raspberry Pi GPIO SWD on five bare pads; board self-powered by USB-C; ST-LINK-compatible fallback; no live runtime data interface |
| Power | LOCKED D7/D8 — power-only Type-C 4.75–5.5 V, 20 mA; exact passive protection and TPS7A2433DBVR; no active OVP/eFuse/data/PD |
| RF limits | PROVISIONAL — 0 dBm operating limit and first-article loss/isolation/return-loss targets; final evidence requires VNA |
| Timing/state | LOCKED — ALL_OFF guards and reset state; 1.4 µs switch-settling ceiling is far below the 5 ms guard |
| Mechanics | PARTIAL — D9 provisionally selects female right-angle THT SMA; outline, mounting, edge order, enclosure and cabling remain OPEN |
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
| T3 | JLCPCB fabrication over 5.9 GHz | JLCPCB publishes exact controlled-impedance multilayer stackups and calculator inputs. | Select advanced four-layer JLC04161H-7628; solve the exact route/launch at PCB stage and validate every path on the first article. | [0001](decisions/0001-one-of-eight-absorptive-sp8t.md) | yes |

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
| Common-port SMA gender/orientation and cable | AGENT ASSUMPTION D9 | Launch and system loss budget | female/right-angle provisional for schematic; cable and final mechanical approval OPEN |
| Enclosure/mounting/antenna SMA geometry | OWED | Board boundary and placement | OPEN |

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
| Programming | Five bare 3V3/GND/SWDIO/SWCLK/NRST pads; direct Raspberry Pi GPIO SWD with ST-LINK-compatible fallback; target power remains USB-C | D11 |
| Power source | Independent USB-C nominal 5 V input | D7 |
| Power implementation | Exact passive protection and TPS7A2433DBVR; 4.75–5.5 V/20 mA; no active OVP/data/PD/backfeed path | D8 / ADR-0003 accepted |
| Mechanics/cabling | Nine female right-angle SMA provisionally selected; outline, mounting, edge order and cable loss remain OPEN | A3 / D9 |
| Assembly/test | Five JLC first articles proposed; uploader allocation and instrument availability remain OPEN | A3 |

## Exact-parts and interface gate

The architecture, exact BOM and electrical interfaces are closed for
schematic entry. `03_src/floorplan.yaml` remains fail-closed only for the
requested stage pause and because RF solver geometry, board mechanics and
custom-footprint reviews belong to later stages. No schematic, PCB, route,
fab or release artifact exists yet.

Before PCB generation, review D9's all-female/right-angle SMA assumption,
solve the 50-ohm geometry with JLC's current calculator, and lock board
outline, edge order and mounting. Before fabrication, provide/confirm the
at-least-6 GHz VNA and calibration fixtures, pass the JLC uploader echo, and
approve the complete first-article test plan.
