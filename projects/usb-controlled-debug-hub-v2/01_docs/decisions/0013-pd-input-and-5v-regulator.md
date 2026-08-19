# ADR-0013: hardware 15 V PD sink and 6 A 5 V regulator

- Status: accepted and encoded for schematic implementation; preliminary JLC
  catalog evidence is positive, exact order allocation remains a release gate
- Date: 2026-08-18
- Decision owner: engineering derivation under the user's two-USB-C approval
- Partially supersedes: ADR-0002 only for the external source/input path

## Context

The retained board consumes at most 2.58 A normally at about 5 V, but its
existing aggregate breaker contract admits a short 5 A / 6 ms fault transient.
A 9 V / 3 A source has only 27 W before conversion losses and is therefore too
tight for that inherited transient. The power controller must not require
project firmware.

## Decision

- Use CH224K (JLC/LCSC C970725) in its documented hardware-I/O configuration
  for a 15 V request. No I2C or MCU control is used.
- Require the external source to advertise a 15 V fixed PDO at 3 A (45 W).
- Use TPS56637RPAR (C841386), a 4.5–28 V, 6 A synchronous buck, with the
  manufacturer's 5 V / 6 A reference topology.
- Use MWSA0804S-3R3MT (C17700166), 3.3 uH, 15 mOhm maximum DCR, 11 A minimum
  saturation rating, and 10 A heat-current rating.
- Set the nominal output near 5.13 V with a 75.0 kOhm + 499 Ohm series upper
  leg and 10.0 kOhm lower leg, all 0.1%. With TI's 0.591--0.609 V reference
  limits and resistor corners, the source-owned window is 5.044--5.216 V.
  Charging 45 mOhm maximum eFuse resistance plus 18 mOhm common copper at the
  2.58 A continuous board load, then applying the declared 5% delivery-margin
  multiplier, leaves 4.873 V at P5V_PROTECTED (contracted downward to 4.87 V).
  Applying the independent 20% margin to the 160 mOhm per-port budget at
  500 mA leaves 4.777 V at the mated test plug, above the 4.75 V requirement.
- Set external UVLO above default USB-C 5 V. A source that cannot provide the
  requested contract leaves the board off.
- Use a 3 A / 32 V Littelfuse 0466003.NRHF fuse, Littelfuse SMF16A TVS and two
  10 uF / 50 V X7R input capacitors. Feed the retained
  TPS259474L directly from the regulated output rather than through the former
  high-drop blade-fuse holder.

## Evidence at selection

- WCH CH224 manual v2.1: CH224K pin map and 15 V I/O strap table; official WCH
  content retrieved through JLC C970725, SHA-256
  `df4f8a9f305df715b1c3617e89505faaa2223a0e4053b44373c5deb565b63c0d`.
- TI TPS56637 datasheet SLVSEG1A: 4.5–28 V, 6 A, 6.3 A minimum valley limit,
  5 V / 6 A reference circuit and four-layer layout guidance; SHA-256
  `18edaff6769b0d5c3d0cdef66df1232538cd357bbaac214df138969f9b0d6745`.
- Sunlord MWSA-S catalog revised 2025-05-29: exact 0804 3R3 row and current/DCR
  ratings; JLC C17700166.

## Consequences

- A fixed 5 V USB-C source will not operate v2. A 30 W 15 V / 2 A source is
  also not qualified for the inherited worst-case transient. These are visible supply
  qualification, not an intermittent failure.
- The power island adds one controller, one buck, one larger inductor, one
  connector, and associated protection/passives while retaining every costly
  v1 functional IC.
- Switching-node placement and thermal copper become new pre-route gates.
- Final order authorization still requires exact JLC allocation, MOQ cash,
  uploader echo, and first-article full-load/thermal testing.
