# Architecture — approved for schematic entry

Status: accepted at D8. This is the exact-parts and interface checkpoint; it
does not authorize PCB routing, fabrication, or a performance claim.

## System boundary

The board is a receive-only 50-ohm selector between one cable-connected Pluto
Plus RX SMA and eight antenna SMAs. Zero or one antenna may be connected; two
or more selected throws are illegal. It has its own power-only USB-C input and
no power, data, or control connection to the Pluto.

```text
J3..J10 antenna SMA -- PE42482A-X SP8T -- J2 common SMA -- cable -- Pluto RX
                              ^
                              | V1..V4
USB-C 5 V -- protection -- 3V3+-- STM32C011F4P6 autonomous dwell controller

invariant: selected_count in {0, 1}; reset/unpowered-controller state = ALL_OFF
```

All nine RF connectors are provisionally the same female, right-angle,
through-hole `901-143-6RFX`. This is agent assumption D9, not a user-confirmed
mechanical requirement. No rigid Pluto mating or Pluto mechanical geometry is
authorized.

## RF signal path

`PE42482A-X` is one absorptive SP8T stage covering 10 MHz–8 GHz at the device
level. LS is tied low for binary control. Its exact `V4..V1` codes are:

| State | Code | State | Code |
|---|---:|---|---:|
| ANT1 | 0000 | ANT5 | 0001 |
| ANT2 | 0100 | ANT6 | 0101 |
| ANT3 | 0010 | ANT7 | 0011 |
| ANT4 | 0110 | ANT8 | 0111 |
| ALL_OFF | 1000 | illegal/unused | every other code |

The passive default is `V4=1, V3..V1=0` using 10-kohm pulls, so a reset,
unpowered, or tri-stated MCU produces the documented terminated ALL_OFF state.
The MCU mapping is `PA0..PA3 -> V1..V4`. Firmware preloads `PA3..PA0=1000`
before changing those pins to outputs and explicitly returns to ALL_OFF before
every selected state. A 5-ms guard dwarfs the switch's 1.4-us maximum settling
bound.

The desired board path remains 100 MHz–5.9 GHz. The physical receiver is the
user's AD9363 running an AD9361 software profile. The user accepts operation
outside ADI's official AD9363 325 MHz–3.8 GHz range. Nothing in this design may
describe that extended range as ADI-guaranteed. The operator limit is 0 dBm;
+2.5 dBm is retained only as the cited AD9363 RF-input damage ceiling, not an
operating target.

## Autonomous control protocol

`STM32C011F4P6` runs from 3.3 V, using HSI48, a hardware timer, BOR level 4 and
the independent watchdog. Bare pads TP1..TP5 expose target-sense 3V3, GND,
SWDIO, SWCLK and NRST respectively. The board is powered through its own
USB-C input; neither a Raspberry Pi nor an ST-LINK may source board power.

The primary update path uses a Raspberry Pi as the SWD adapter directly:
GPIO11/physical pin 23 drives SWCLK, GPIO8/physical pin 24 is SWDIO, GPIO24/
physical pin 18 may drive NRST, and a Pi ground joins TP2. OpenOCD uses
`raspberrypi-native.cfg` on Pi 1–4 and `raspberrypi5-gpiod.cfg` on Pi 5.
The same pads remain compatible with a conventional ST-LINK recovery probe.
There is no live configuration/data link; changing a profile means generate,
validate, build, flash, verify and reset.

The initial generated `fast20-v1` frame uses ANT1..ANT8 active dwells of
20/23/26/30/34/39/44/50 ms, with 5 ms ALL_OFF guards and an 80 ms ALL_OFF
marker body; its contiguous pre-ANT1 guard makes the nominal observable
ALL_OFF interval 85 ms. A decoder accepts +/-5% dwell windows only in valid
order after an ALL_OFF interval of at least 76 ms. It returns `unknown` for absent RF,
truncated capture, ambiguous duration, missed/extra transitions, invalid order,
or reset recovery. A cycle is 386 ms; 772 ms is the minimum guaranteed full
frame capture and 850 ms is recommended. The executable definition is
[`control_protocol.yaml`](../03_src/rules/control_protocol.yaml).

## Independent power path

```text
USB4105 VBUS -- 0603L010YR -- VBUS_PROTECTED -- TPS7A2433DBVR -- 3V3
                                      |
                                  SMBJ6.0A
                                      |
                                     GND

CC1 -- TPD2E2U06 -- 5.1k Rd -- GND
CC2 -- TPD2E2U06 -- 5.1k Rd -- GND
D+/D-/SBU: explicit no-connects
```

The contract is 4.75–5.5 V and no more than 20 mA. There is no USB data, PD,
active overvoltage cutoff, eFuse, switching converter, reverse-power source,
or Pluto backfeed path. The 3.3-V LDO worst-case dissipation is 44.825 mW and
the estimated temperature rise is 7.6 C. Its input and output capacitor banks each
retain a conservative 1.798 uF effective value against a 1 uF minimum.

The VBUS TVS has a 10.3-V maximum clamp in the admitted pulse model. Therefore
the protected input capacitor is the 16-V `CL10A475KO8NNNC`; the initially
considered 10-V capacitor was rejected before schematic entry. The TVS is
transient protection, not sustained-overvoltage protection.

## PCB and verification boundary

The PE42482 0.5-mm QFN, with three escapes on the worst side, is the sole
reason the board requires the advanced tier. The MCU and every other selected
part pass the default JLC escape tier. The selected PCB basis is four-layer,
1.6-mm `JLC04161H-7628`, with 35-um outer copper, 0.2104-mm 7628 prepreg to a
solid L2 ground plane, and nominal Dk 4.4. Exact 50-ohm width and coplanar gap
remain deliberately null until solved in JLC's current impedance calculator.

Provisional first-article targets at SMA mating planes are:

- insertion loss no more than 2.0 dB through 1 GHz and 3.5 dB at 5.9 GHz;
- path balance no more than 1.5 dB;
- common-to-off isolation at least 30 dB through 4 GHz and 25 dB at 5.9 GHz;
- active-path return loss at least 10 dB.

These are engineering acceptance targets, not data-sheet promises. A VNA
covering at least 100 MHz–6 GHz must measure every selected path and required
off state at the SMA mating planes, retaining Touchstone data. PCB routing is
blocked until the impedance solution, outline, mounting, edge order, and SMA
footprint review are closed.

## Stage handoff

The architecture, exact BOM, pin maps, control truth table, timing protocol,
power budget, protection coordination, stackup family, assembly intent, and
first-article measurement method are sufficient for schematic entry. The
current pause is intentional. No `.tsx`, KiCad schematic, PCB, route, fab, or
release artifact exists.

Primary evidence and comparison notes are indexed in
[`research/exact-parts-and-interfaces.md`](research/exact-parts-and-interfaces.md),
the accepted ADRs, and the exact-code dossiers under `02_parts/`.
