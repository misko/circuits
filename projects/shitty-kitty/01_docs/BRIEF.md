# BRIEF — shitty-kitty

Commissioned: 2026-07-17, via /pcb-design. Brief arrived as an image (page 1
of a multi-page PNG, "Shitty Kitty"); text transcribed verbatim below.
User's inline instruction: "shity kitty, please see multi page png, please
ask clarifying questions"

<!-- prompt-verbatim-begin -->
Shitty Kitty

Description:
A replacement toilet lid+seat that is compatible with cats. The lid is
modified with a hole (115mm wide) that suspends underneath a small (63mm
tall 125mm wide) replaceable plastic cup that is half full with litter. The
cup of litter is suspended on a rail with a stepper motor that is able to
move the cup between two positions Open and Closed.

Open position:
In the open position the cup is aligned with the hole and the cats are able
to play with the litter while sitting on top of the lid.

Closed position:
In the closed position the cup of litter rescinds towards the back of the
lid so that the open part of the cup is totally blocked by the solid part
of the toilet lid.

Image: Toilet Lid + Seat
<!-- prompt-verbatim-end -->

<!-- additional-pages-verbatim-begin (transcribed 2026-07-17) -->
[Pages 2-4 of the PNG brief, transcribed:]

Page: prototype photos — lid underside with 24 hand-cut copper-foil
capacitive pads in two concentric rings (12 inner, 12 outer), wired with
taped harnesses to a breadboard; cup + rail + motor bracket around a
115mm hole; lid shown vertical with cup open and closed.

Detecting a cat:
Cat detection happens by using a software to analyze the cats paws on the
two consecutive rings of capacitive touch sensors. Increasing the
resolution of the touch sensors (while allowing for multi touch / paw)
will help precision of cat detection.
[Sketch dims: lid 530mm x 378mm; sensor ring radial extent ~120mm; center
hole 115mm.]

Electronics:
  Motion:
    Nema 17 Bipolar Stepper Motor 1A
    DRV8825 like motor driver with 1/32 microstepping
    Motor endstop switch (to reset position on physical contact)
  Sensors:
    Accelerometer (parallel to toilet lid) (similar to ADXL345)
    Capacitive sensor with 24 leads (similar to 4 x MPR121 ICs)
      12 sensors in inner circle
      12 sensors in outer circle
  Power distribution:
    Input power 12v
      Output 12v for motor driver
      Output 5v,3.3v for RaspberryPI / Arduino

Lid/cup behavior:
- The cup is only in an open position when the lid is horizontal (cats
  jump on the lid and play with the clean litter).
- Closed when: (1) lid elevated >=20 degrees from horizontal (detected by
  accelerometer) — prevents litter spill; (2) a cat poop/pee event has
  been detected — cup rescinds to let the litter fall into the water.

Goals:
1. Design PCB with power distribution, accelerometer, 4 x mpr121, and
   capacitive sensors
   a. Eagle files for prototyping initial 5 PCBs
   b. Estimate of cost to build / assemble current PCB on scale of 10,000
      units
   c. Estimate of cost to build / assemble optimized PCB on scale of
      10,000 units +
2. Design mechanics and prepare for initial 20 production run
   a. Estimate of cost to build / assemble mechanics on scale of 10,000
      units +
3. Design mechanics and PCB for mass production and prepare updated cost
   estimate
   a. Updated cost estimates for PCB and mechanics on scale of 10,000
      units +

Video: https://www.youtube.com/watch?v=x2Yv9KRT77E
<!-- additional-pages-verbatim-end -->

## Parsed requirements (from page 1)

- P1: Product = replacement toilet lid+seat; lid has a 115mm hole with a
  replaceable litter cup (63mm tall x 125mm wide) suspended beneath.
- P2: Cup rides a rail driven by a STEPPER MOTOR between two positions:
  Open (cup aligned with hole) and Closed (cup retracted to the back,
  blocked by the solid lid).
- P3 (implicit): the PCB scope = the electronics that drive and control
  this mechanism. Everything electrical is currently UNSPECIFIED: motor
  class, driver, MCU/control, trigger/UI, position sensing, power input,
  environment sealing.

## Parsed requirements (full document)

- P4: Motion = NEMA 17 bipolar 1A, DRV8825-like driver with 1/32
  microstepping, endstop switch for position reset on contact.
- P5: Sensors = accelerometer parallel to lid (ADXL345-similar) for the
  >=20-degree lid-angle rule; 24-lead capacitive sensing (4x MPR121),
  12 inner + 12 outer ring pads (pads are foil on the lid, OFF-board).
- P6: Power = 12V input; 12V to motor driver; 5V and 3.3V outputs for
  external host (RaspberryPi/Arduino class).
- P7: Deliverable scope (per A4) = Goal 1 only: prototype PCB package for
  5 boards + cost estimates at 10k units for current and optimized PCB.
- P8: Cat-detection software itself is out of scope (runs on
  compute; firmware out of scope per pipeline convention).

## Q / A

- Q1: Eagle files vs our KiCad pipeline?
  A1 (user, 2026-07-17): **KiCad 10 is fine** — full project + universal
  gerbers/BOM/CPL.
- Q2: Compute architecture?
  A2 (user, 2026-07-17): **On-board ESP32, Pi optional** — board is
  self-contained (ESP32 does sensing + motion), with the paw-analysis
  software moving to firmware later; optional Pi/host power header stays.
- Q3: Motor driver form?
  A3 (user, 2026-07-17): **On-board driver IC** (DRV8825-class or better
  cross; 1/32 microstepping), JLC-assemblable, cost-optimizable at 10k.
- Q4: Scope?
  A4 (user, 2026-07-17): **Goal 1 only** — PCB release + 10k-unit cost
  estimate docs (1b/1c); mechanics (Goals 2-3) out of this run.

## End goal — definition of done

Goal-1 (A4) deliverables: an orderable, verified JLCPCB release of the
controller PCB plus the two 10k-unit cost estimates.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | PCB with power distribution (12V in, 12V motor, 5V+3V3 out), accelerometer, 4x MPR121, 24 electrode lines, stepper driver, endstop input | P4-P6 | unmet |
| G2 | Fab package for 5 prototype boards (gerbers+BOM+CPL, KiCad 10 per A1) | P7/Goal 1a | unmet |
| G3 | COST_ESTIMATE.md (b): current PCB at 10k units | Goal 1b | unmet |
| G4 | COST_ESTIMATE.md (c): optimized PCB at 10k+ units | Goal 1c | unmet |
| G5 | Motor disabled at boot (hardware pull), endstop on interrupt GPIO | P4 + commission | unmet |

## Decision register

| id | decision (one line) | decided by | depth |
|---|---|---|---|
| D1 | Input entry: barrel jack + polyfuse 2A + P-FET reverse polarity + SMBJ16A TVS | agent (P-delegation) | decisions/0001-input-protection.md |
| D2 | Stepper driver = TMC2209-LA-T (quiet StealthChop, UART, StallGuard) over DRV8825 | agent (P4 "or better") | decisions/0002-motor-driver.md |
| D3 | 4-layer board, JLC standard tier (In1 GND plane for cap-sense floor) | agent (P-delegation) | decisions/0003-layer-count.md |
| D4 | Accelerometer = LIS2DH12TR; 4x MPR121QR2 at 0x5A-0x5D, 6 electrodes/chip | agent (P5 "similar to") | decisions/0004-sensors-and-compute.md |
| D5 | 5V = AP63205 2A buck; host budget 1.5A; 3V3 = AMS1117; USB-C is data-only | agent (P6 delegation) | decisions/0004-sensors-and-compute.md |
| D6 | Sourcing: 12 unique Extended + 10 Basic lines; THT connectors hand-solder | agent (pipeline rule) | decisions/0005-sourcing-and-connectors.md |
| D7 | Connectors: XH-4 motor, 2P screw endstop, 2x 1x13 headers for electrodes, 1x6 host | agent (P-delegation) | decisions/0005-sourcing-and-connectors.md |
| D8 | Host link = UART (TXD0/RXD0) not I2C on the 1x6 header | agent (A2 delegation) | decisions/0004-sensors-and-compute.md |
| D9 | ENN pull-up 10k to 3V3: motor hardware-disabled at boot (cat safety) | agent (commission mandate) | decisions/0002-motor-driver.md |
| D10 | TMC2209 external sense 0.15R (1.35A max) rather than RDSon-only mode | agent (P-delegation) | DETAIL_DESIGN.md §TMC2209 |

## Log

- 2026-07-17: commissioned from page 1 of the PNG brief; awaiting
  remaining pages and answers to Q1-Q4.

- 2026-07-17: Stage-1 docs cut — ARCHITECTURE, DETAIL_DESIGN, ADRs
  0001-0005, decisions D1-D10 (live JLC stock data in 06_build/cache/).
