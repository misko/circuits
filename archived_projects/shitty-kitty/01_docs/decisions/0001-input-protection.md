---
id: 0001
date: 2026-07-17
status: accepted
---
# 0001 — 12V input entry + protection chain (MANDATORY ADR)

## Context

P6: 12V external supply feeds the motor driver directly and a 5V/3.3V
conversion chain. Environment is a bathroom (humidity, occasional splash,
consumer user who can plug the wrong brick or swap tip polarity). Downstream
absolute-max ratings that bound the clamp: TMC2209 VS abs max 29V;
AP63205 VIN max 32V; 100uF electrolytics 25V.

## Decision — chain, in order

`J1 (DC-005C-20A barrel jack, 2.0mm center-positive) -> F1 polyfuse
SMD1812P200TF16 (2A hold / 4A trip, 16V) -> Q1 AOD4185 P-FET high-side
reverse-polarity switch (gate to GND via R 100k) -> D3 SMBJ16A TVS
(unidirectional, to GND) -> net VIN_12V`

1. **Connector: barrel jack** (DC-005C-20A, C84007, 3A/24V rated, $0.21,
   3.5k stock, hand-solder THT). Consumer 12V wall bricks terminate in
   2.1/5.5 barrels; a screw terminal invites bare-wire hookups in a wet
   room. Rejected: KF128L screw terminal (kept for the endstop only, where
   the user wires a microswitch anyway). Center-positive marked on silk.
2. **Fuse: resettable polyfuse 2A hold/4A trip** (C20812, 16V, 1812).
   Worst-case steady draw ~1.5A at 12V (DETAIL_DESIGN §input current);
   a blown one-shot fuse on a consumer appliance is a support call, a
   polyfuse recovers. 16V rating >= supply; interrupt backed by the 3A
   barrel and the wall brick's own limit.
3. **Reverse polarity: P-FET high-side** (AOD4185, C400894, -40V/-40A,
   15mOhm, DPAK). At up to 2A a series Schottky burns ~1W and drops 0.5V
   into the motor rail; the FET burns ~60mW. Vgs(max) ±20V > 12V so the
   gate needs only the 100k pulldown, no zener. Body diode conducts first,
   channel takes over. Reversed input: channel and body diode both block.
4. **TVS: SMBJ16A unidirectional** (C10211). Standoff 16V > 12V + 5%
   brick tolerance (no conduction in normal operation); clamp 26V max at
   23A < TMC2209's 29V abs max and < AP63205's 32V — the whole downstream
   survives the clamped surge. Rejected SMBJ18A: 29.2V clamp exceeds the
   TMC2209 abs max. TVS sits AFTER the FET so a reversed input never
   forward-biases it at full fault current; input differential surges are
   still absorbed through the FET body diode path.
5. **No UVLO stage**: wall-powered (no battery to over-discharge);
   AP63205 has its own UVLO at 3.8V, TMC2209 at ~4.5V. Brown-out just
   stops the show safely (driver ENN is pulled disabled at boot).

## Humidity / conformal coat

Bathroom deployment: recommend conformal coating the assembled board
EXCEPT the two electrode header connectors, USB-C, and jacks (masked).
Noted in ORDER_README; coating is a post-assembly user step, not a JLC
option on this order. Electrode foils on the lid are off-board and taped
under the lid per the prototype photos.
