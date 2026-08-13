---
id: 0002
date: 2026-08-12
status: accepted
---
# 0002 — Autonomous dwell-coded antenna control

## Context

D6 requires an onboard preprogrammable IC to autonomously select antennas.
Each populated antenna state must have a predetermined unique dwell duration,
and downstream analysis infers the state from timing. There is no assumed live
Pluto GPIO link. D7 selects eight antenna ports; the SP8T implementation in
ADR-0001 is accepted.

Unique durations alone are not a self-synchronizing code: a recording that
starts mid-dwell, misses an edge, spans too short a window, or sees clock drift
can mislabel a state. Reset or partial power can also leave switch-control pins
floating before firmware runs. The controller and protocol must address these
failure modes without inventing timing values prematurely.

## Options

- **STM32C011F4P6 bare MCU — leading feasibility reference.** ST specifies
  16 KB flash, 18 I/O, hardware timers, independent and window watchdogs,
  programmable BOR, SWD, and 2.0–3.6 V operation. At a prospective 3.3 V rail
  its outputs are compatible with PE42482's cited 1.17 V minimum logic-high.
  HSI48 drift is characterized as -1/+1% from 0–85 °C and -2.5/+2% over the
  wider -40–125 °C range; an external crystal is supported if approved dwell
  separation cannot tolerate internal-RC error. JLC explicitly lists TSSOP-20
  SMT assembly for C5452432. LCSC displayed 1,443 units on 2026-08-12.
- **ATtiny1616-SFR bare MCU.** Microchip specifies 16 KB flash, EEPROM,
  18 I/O, timers/RTC, watchdog, BOD and single-pin UPDI programming. Reset
  direction registers make GPIO inputs until firmware configures them, so
  external all-off enforcement is still mandatory. JLC explicitly lists the
  SOIC-20 part C145558 for Economic and Standard SMT assembly. LCSC displayed
  274 units in the fresh capture. It is a viable alternate; its exact
  full-envelope oscillator budget still must be derived before timing values.
- **CH32V003F4P6 bare MCU.** WCH specifies 16 KB flash, 18 I/O, two 16-bit
  timer blocks plus a 32-bit time base, two watchdogs, programmable voltage
  monitor and single-wire debug. It operates at 3.3 V or 5 V; 3.3 V is the
  candidate logic-compatible posture. JLC explicitly lists TSSOP-20 SMT
  assembly for C5187096. LCSC displayed 16,415 units on 2026-08-12. It is a
  cost/source alternate, but no controller is selected on stock and its timing
  error/reset-pin behavior still needs a dossier-level proof.
- **ESP32-C3-MINI-1 module.** It provides flash, crystal, timers/watchdogs and
  plentiful GPIO, and JLC lists module assembly. It also adds a 2.4 GHz radio,
  antenna keep-out, much higher peak current and a larger package beside a
  sensitive 100 MHz–5.9 GHz RF selector. Those functions are not required by
  D6. The N4 variant is NRND in current Espressif documentation. REJECTED as
  higher total integration and RF-coupling risk; it does not justify module
  use for this simple deterministic controller.
- **Unique dwell durations only, arbitrary order.** Minimal firmware, but a
  downstream observer cannot reliably recover identity after truncated or
  missed transitions. REJECTED.
- **Fixed cyclic order plus unique dwells.** Sequence context detects many
  missed transitions, but start-mid-cycle ambiguity remains.
- **Fixed cyclic order, explicit all-off guard between antenna states, and a
  distinctive frame/superframe marker.** Adds transition safety and a recovery
  point. Duration codes remain redundant identity information rather than the
  only framing mechanism. This is the recommended protocol shape.

All stock counts are dated volatile observations. A JLC part page supports
assembly eligibility at the time observed, not guaranteed order-time stock;
both must be rechecked before selection/order.

## Decision

D8 continued after the leading controller/protocol recommendation was
presented. Select **STM32C011F4P6 / JLC C5452432** at 3.3V and the repeating
fixed-order framed protocol recorded in `03_src/rules/control_protocol.yaml`:
ANT1..ANT8 use 80/105/135/170/210/255/305/360ms active dwells, a 5ms ALL_OFF
guard separates active states, and a 500ms ALL_OFF marker body marks a frame.
The contiguous pre-ANT1 guard makes its nominal observable interval 505ms.
Acceptance windows are +/-5%; a decoder returns `unknown` for
incomplete, ambiguous, unordered or unframed observations.

Use HSI48, hardware timers, BOR level 4, IWDG and SWD test pads. External
pulls own ALL_OFF until firmware atomically preloads `PA3..PA0=1000` and only
then enables the GPIO outputs. The accepted ADR authorizes schematic work
after the stage pause, not firmware release or PCB generation.

## Consequences

The circuit must make the switch all-off without firmware. The selected truth
table allows external 10-kohm pulls to force `V4..V1=1000` while the MCU is
reset, unpowered, brownout-reset, programming or tri-stated, so no separate
output gate is required. Firmware first preloads the same safe control word,
then enables drive. BOR level 4 and the independent watchdog return GPIOs to
the passive state on reset.

The selected protocol solves these parameters together. Adjacent +/-5%
duration windows remain disjoint while covering the documented full-temperature
HSI48 error and reserving estimator margin. The 5-ms guard exceeds the switch's
1.4-us settling ceiling by more than three orders of magnitude. Captures shorter
than the 4320-ms guaranteed full-frame window remain explicitly ambiguous.

First-article control verification must observe real switch-control or RF-state
edges with an independent timebase over multiple superframes and approved
supply/temperature corners. It must measure every dwell, all-off guard,
frame marker, cycle order, startup delay, reset/brownout/watchdog recovery and
prove no multi-selected transient. Captured timestamps and decoder results are
retained; commanded timer counts alone are not evidence of actual dwell time.

Primary sources:
[STM32C011F4](https://www.st.com/en/product/stm32c011f4.html),
[STM32C011 data sheet](https://www.st.com/resource/en/datasheet/stm32c011f4.pdf),
[ATtiny1616](https://www.microchip.com/en-us/product/ATtiny1616),
[ATtiny1616 data sheet](https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/ATtiny1614-16-17-DataSheet-DS40002204A.pdf),
[CH32V003](https://www.wch-ic.com/products/CH32V003.html),
[Espressif module data sheet](https://documentation.espressif.com/esp32-c3-mini-1_datasheet_en.pdf),
[JLC STM32C011](https://jlcpcb.com/partdetail/STMicroelectronics-STM32C011F4P6/C5452432),
[JLC ATtiny1616](https://jlcpcb.com/partdetail/MicrochipTech-ATTINY1616SFR/C145558), and
[JLC CH32V003](https://jlcpcb.com/partdetail/WCH-CH32V003F4P6/C5187096).
