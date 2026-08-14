# Pluto RX2 eight-way v5 — first-article test plan

Status: required external work; no physical article has passed this plan.

## 1. Record and equipment

Assign each board a serial number and record PCB/PCBA order numbers, ambient,
operator, instrument models, calibration dates and photographs. Required
equipment is a current-limited 5 V source or instrumented USB-C supply, DMM,
oscilloscope/logic analyzer, ESD-safe microscope and calibrated VNA covering
at least 100 MHz–6 GHz. Use known-good 50-ohm cables, adapters and loads.

## 2. Order and incoming inspection

Before payment, preserve the JLC layer, drill, impedance, BOM, CPL, polarity
and 3D previews. Confirm selective fill/cap applies only to the nine 0.25 mm
drills, J2–J10 are accepted as exact C429844 through-hole connector placements,
and J12 is accepted as exact C225477 through-hole assembly. On receipt, inspect
outline, layer registration, mask, ENIG,
annular rings, U1 via-in-pad caps, USB-C shell joints, SMA posts and every
pin-1/polarity marker. Reject unexpected DFM edits or substituted lands.

## 3. Unpowered electrical checks

With all cables removed, measure resistance from VBUS_RAW, VBUS_PROTECTED and
3V3 to GND. Record values after capacitors settle; investigate any hard short.
Verify continuity across F1, no continuity from USB D+/D-/SBU to the circuit,
and no conductive path from any RF centre pin to chassis except through the
intended switch state/termination behavior. Inspect that J11.1 is 3V3/VTref,
J11.2 SWDIO, J11.4 SWCLK, J11.10 NRST and J11.3/5/9 GND.

## 4. Current-limited first power

Power through J1 first. Start at 4.75 V with a conservative current limit,
then test 5.0 V and 5.5 V. Repeat from J12 using the marked +5 V/GND polarity.
J1 and J12 are non-isolated alternatives: never connect or energize both at
once. Record input current, 3V3, regulator temperature and startup waveforms.
Acceptance: stable 3.3 V operation within component limits, no unexpected
heating/oscillation, and no voltage sourced from J11 or any RF connector. A
Raspberry Pi or ST-LINK must share ground and sense J11.1 only; it must not
drive power into J11.1.

## 5. Hardware control-state access

This archive supplies no firmware. Use only a separately approved and recorded
debug/test method to command U2 GPIO or otherwise establish each legal U1
state. Preserve the exact method and state-code evidence with the article.
Verify reset/tri-state hardware bias produces ALL_OFF `V4..V1 = 1000` while
3V3 is valid. Do not claim dwell timing or autonomous operation unless a
separate firmware qualification is explicitly commissioned and completed.

## 6. VNA setup

Calibrate at the board's SMA mating planes over 100 MHz–5.9 GHz (or wider with
the retained range clearly identified). Terminate every unused antenna port in
50 ohms. Keep cable routing fixed and below its bend-radius limit. Store the
calibration record and raw Touchstone files; do not normalize one path to
another or subtract an unrecorded fixture.

## 7. Selected-path tests

For ANT1 through ANT8 independently, select exactly that state and measure
S21, S11 and S22 between the common port and selected antenna. Retain dense
sweeps plus spot values at 100 MHz, 325 MHz, 1 GHz, 2.4 GHz, 3.8 GHz, 5.8 GHz
and 5.9 GHz. Acceptance for every path:

- insertion loss <= 2.0 dB through 1 GHz and <= 3.5 dB at 5.9 GHz;
- input and output return loss >= 10 dB across 100 MHz–5.9 GHz;
- all-path insertion-loss spread <= 1.5 dB at every retained comparison point.

## 8. Isolation and off-state tests

For each selected state, measure common-to-each-off-port isolation with all
other unused ports terminated. Measure ALL_OFF common-to-antenna isolation for
all eight throws and antenna-to-antenna spot checks for adjacent physical
ports and worst observed pairs. Acceptance: isolation >= 30 dB through 4 GHz
and >= 25 dB at 5.9 GHz. Retain every required sweep; no unmeasured state may
be inferred from another.

## 9. Closeout

Tabulate each criterion as PASS or FAIL and link it to raw files, photographs
and instrument records. Results outside the AD9363 official band are
article-specific and must never be described as ADI-guaranteed. Any failure,
intermittent SMA joint, unexplained current, unstable rail, process deviation
or missing state blocks production and reopens engineering review.
