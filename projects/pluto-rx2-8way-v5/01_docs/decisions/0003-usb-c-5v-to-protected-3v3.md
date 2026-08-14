---
id: 0003
date: 2026-08-12
status: accepted
---
# 0003 — Alternative USB-C or bench 5 V input and quiet 3.3 V rail

## Context

D7 originally approved an independent USB-C 5 V input. D18 later requires a
separate pair of easy bench-power pins. The RF selector must not take
its operating power from, or back-power, the Pluto Plus. The candidate onboard
controller and RF switch are low-current 3.3 V-compatible loads, but the exact
parts, total worst-case current, input tolerance/transient envelope, rail
tolerance/noise, fault behavior and regulator thermal budget remain open.

The intended port is power-only. There is no approved USB data function and no
need for USB Power Delivery voltage negotiation. A sink that stays within the
approved default-current budget can identify itself passively by placing an Rd
termination on each Type-C configuration-channel pin. TI's current Type-C
guide gives 5.1 kOhm for each Rd in the simplest 5 V sink-only implementation.
This proposal does not assume access to 1.5 A or 3 A source modes: the actual
board load and source-current entitlement must be proved first.

## Proposed architecture

```text
USB-C receptacle ----+
                     +-- VBUS_RAW -- passive resettable fuse
J12 +5V/GND header --+                  |
                                       +-- protected-node TVS to GND
                                       +-- fixed 3.3 V LDO
                                           -> RF switch and MCU
USB-C CC1 -- independent Rd to GND [with connector-side ESD]
USB-C CC2 -- independent Rd to GND [with connector-side ESD]
USB-C D+/D-/SBU -- explicit no-connects
```

The connector shell/ground treatment and exact passive protection order remain
layout and part-selection decisions. Any TVS must coordinate its clamp voltage
and waveform with every exposed part's recommended and absolute maximum—not
merely appear in the BOM. The load is expected to remain far below default USB
current, and the input capacitance is expected to be small. Therefore a PD
controller, active eFuse, dedicated inrush controller and active reverse-
blocking stage are rejected unless the completed load/fault calculation proves
one necessary. Pluto backfeed is prevented structurally: there is no Pluto
power connection and the programming interface senses target VDD but does not
inject operating power. J1-to-J12 backfeed is prevented operationally by the
one-input-only contract, not by reverse-blocking hardware.

## Trade study

| Function/option | Fresh primary evidence | Fresh JLC observation | Disposition |
|---|---|---|---|
| Passive 5 V sink, two Rd | TI's Type-C guide states that the simplest 5 V sink-only port uses a 5.1 kOhm Rd on each CC pin | Standard resistors are broadly assembleable; exact value/package/tolerance not selected | Recommended protocol class; no PD controller |
| GCT USB4105-GF-A-120 receptacle | GCT rates the 16-pin USB 2.0 Type-C receptacle at 5 A collectively on VBUS, 48 V DC and 20,000 cycles | JLC C5184243 listed the exact GCT part with SMT assembly and displayed stock on 2026-08-12 | Connector feasibility reference only; mechanics/stock/order eligibility must be rechecked |
| TI TPD2E2U06DRLR dual ESD array | TI specifies 5.5 V working voltage, 1.5 pF typical capacitance and IEC 61000-4-2 ±25 kV contact protection | JLC C1972959 listed the exact TI part for Economic/Standard SMT assembly | Leading CC-line ESD reference, not selected; placement/ground/clamp coordination owed |
| TI TPS7A2433DBVR LDO | TI specifies an active 2.4–18 V, fixed-3.3 V, 200 mA LDO with 1.25% accuracy over temperature, 250 mV maximum dropout at 200 mA, overcurrent/thermal protection and 1 uF minimum output capacitance | JLC C2866134 listed the exact SOT-23-5 part for Economic/Standard SMT assembly and displayed more than 20k units during the fresh check | Leading robust-regulator reference, not selected; its worst-case load, dissipation, noise/filtering and capacitor proof remain owed |
| TI LP5907MFX-3.3/NOPB LDO | TI specifies 250 mA, 6.5 uVrms typical noise, 60 dB PSRR at 100 kHz, 12 uA typical quiescent current and 2.2–5.5 V input | JLC C80670 listed the exact TI SOT-23-5 part for SMT assembly | Low-noise alternate; its 5.5 V input ceiling leaves much less transient margin than TPS7A24 and demands tighter clamp proof |
| Microchip MIC5504-3.3YM5-TR LDO | Microchip specifies 300 mA, 2.5–5.5 V input, 160 mV typical dropout at 300 mA, current limit, thermal shutdown and output discharge | JLC C88419 listed the exact Microchip SOT-23-5 part for assembly | Higher-current alternate, but materially higher stated noise than LP5907; not selected |
| TPS2553/TPS25961/TPS25940 active protection | These families can add current limit, controlled slew, overvoltage cutoff and/or reverse blocking, depending on exact part | JLC lists examples, but eligibility does not establish need | Rejected for the baseline as avoidable complexity; reconsider only if the closed load/fault/inrush/backfeed analysis requires it |
| Switching buck to 3.3 V | Higher conversion efficiency is possible | No exact candidate researched because the load is not known | Not recommended at present: extra switching/RF-noise and magnetics burden are unjustified until LDO thermal/current analysis fails |

JLC availability observations are volatile and must be repeated in the actual
order. A JLC listing is manufacturing evidence, not a substitute for the
manufacturer data sheet or a completed protection/thermal calculation.

## Decision

D8 continued after this class and leading parts were presented. Select a
power-only **USB4105-GF-A-120** sink with two independent 5.1k 1% Rd parts,
**TPD2E2U06DRLR** on CC, **0603L010YR** in series with VBUS,
**SMBJ6.0A** as the protected-node shunt clamp, and
**TPS7A2433DBVR** for 3.3V. D18 adds **A2541WV-2P** / JLC C225477 as J12:
pin 1 is bench +5V on `VBUS_RAW`, pin 2 is GND. Normal input at either J1 or
J12 is 4.75V-5.5V and total design load is limited to 20mA. Both inputs share
F1, the protected-node TVS and U3. There is no PD, USB data, active eFuse,
active overvoltage cutoff or reverse-isolation stage.

Use a 16V C1 on the clamped input; the initially considered 10V part was
rejected when the executable surge proof showed it could not cover the
10.3V clamp plus margin. The accepted ADR authorizes schematic work after the
stage pause, not PCB/fabrication.

## Consequences and blockers

This avoids a live Pluto power/control dependency and avoids adding an
unneeded PD controller, eFuse or switching converter. It also makes the
board's 5 V input explicit and gives the digital/RF loads a quiet candidate
rail.

The total-current, voltage, clamp, capacitor and thermal source checks now
pass. USB D+/D-/SBU remain explicit no-connects. Sustained overvoltage remains
outside the interface contract by user requirement; clamp overshoot, shell
implementation and assembled behavior remain first-article/layout checks.
J1 and J12 are deliberately non-isolated and therefore must never be
energized together. The schematic, silk and operating instructions all state
one input at a time; reverse-current blocking remains outside this revision.

Primary sources:
[USB-IF Type-C specification page](https://www.usb.org/usb-type-cr-cable-and-connector-specification),
[TI Type-C guide](https://www.ti.com/lit/pdf/slyy228),
[GCT USB4105](https://gct.co/connector/usb4105),
[TI TPD2E2U06](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf),
[TI TPS7A24](https://www.ti.com/product/TPS7A24),
[TI LP5907](https://www.ti.com/lit/ds/symlink/lp5907.pdf), and
[Microchip MIC5504](https://www.microchip.com/en-us/product/MIC5504).

JLC evidence:
[USB4105-GF-A-120 C5184243](https://jlcpcb.com/partdetail/5849584-USB4105_GF_A120/C5184243),
[TPD2E2U06DRLR C1972959](https://jlcpcb.com/partdetail/TexasInstruments-TPD2E2U06DRLR/C1972959),
[TPS7A2433DBVR C2866134](https://jlcpcb.com/partdetail/TPS7A2433DBVR/C2866134),
[LP5907MFX-3.3/NOPB C80670](https://jlcpcb.com/partdetail/TexasInstruments-LP5907MFX_3_3NOPB/C80670), and
[MIC5504-3.3YM5-TR C88419](https://jlcpcb.com/partdetail/MicrochipTech-MIC5504_3_3YM5TR/C88419).
