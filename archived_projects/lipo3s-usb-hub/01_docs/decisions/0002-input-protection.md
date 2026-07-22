# ADR-0002 — Battery / input protection (MANDATORY)

Status: accepted (2026-07-20)

## Context

The input is a 3S LiPo pack on an XT60. LiPo packs can source tens of amps, hold
significant energy, and are routinely mis-connected. A power board on this source that
lacks reverse-polarity, over-discharge, and over-voltage protection is a fire/venting
hazard and can back-feed a fault into the USB rails (12.9 V abs-max input vs 5 V USB
rails whose downstream devices are rated ~5.5 V). This ADR is mandatory: no stage in
the pipeline is allowed to omit the protection question.

## Decision

A layered, hardware-only protection front-end (no firmware, safe from first power-up):

1. **Catastrophic overcurrent — F1, 15 A ATO blade fuse.** Above the ~8.2 A board
   aggregate (worst-case, low-line) with headroom, below pack-fault currents. Blade
   holder = field-replaceable. Chosen over a PTC (too slow / high R-drop at 8 A) and
   over a fixed SMD fuse (not replaceable).

2. **Reverse polarity + ideal-diode — U1 LM74800-Q1 driving two back-to-back
   CSD18543Q3A (common drain at FE_MID).** A reversed pack cannot energize the board
   (both body diodes oppose). Chosen over a series Schottky (1.1 W→~6 W dissipation at
   8 A, unacceptable) and over a single P-FET reverse block (no ideal-diode / UVLO
   integration). The two-FET common-drain also gives reverse-current blocking once
   enabled.

3. **Hardware UVLO (over-discharge protect) + OV — LM74800 EN/OV resistor ladder**
   (R1 887 k / R2 52.3 k / R3 82.5 k, thresholds at 1.231 V):
   - EN-rising (turn-on): **9.33 V** ≈ 3.11 V/cell — will not power a depleted pack.
   - OV-trip (turn-off): **15.25 V** — disconnects on a charger/BMS fault before the
     12.9 V abs-max propagates.
   This is the fix for the clean-room failure mode where a LiPo board shipped with zero
   UVLO because no stage forced the question. Over-discharge protection is present and
   derived, not assumed.

4. **Input transient clamp — D1 SMBJ16A TVS** across VBATT_F (16 V standoff > 12.9 V
   abs-max, ~26 V clamp) absorbs hot-plug / load-dump spikes below the FET and cap
   ratings (25–30 V).

5. **Downstream rail clamps — D2/D3 SMBJ5.0A TVS** on 5V_A and 5V_C protect USB
   devices (rated ~5.5 V) against a buck feedback fault or hot-plug transient on the
   output side.

6. **Per-output current limiting** (see ADR-0004): each USB-A port has its own TPS2557
   (2.51 A + thermal + reverse-current); the USB-C path is bounded by buck-A's
   valley-current OCP (~6.3 A wc-min).

## Consequences

- The abs-max chain is respected end to end: 12.9 V input < 16 V TVS standoff < 25 V
  part ratings; 5 V rails < 5.0 V TVS standoff bracketed.
- The first-power ritual (multimeter XT60 blade polarity + continuity to fuse/FE before
  applying the pack) is in the ORDER_README — polarity bugs are electrically
  self-consistent and invisible to DRC/ERC/parity.
- Two SON-8 FETs dissipate ~1.1 W at worst case; thermal pads sit on the VBATT_F /
  FE_MID pours (adequate, no heatsink).

## Rejected alternatives

- Series Schottky reverse block — dissipation prohibitive at 8 A.
- P-FET-only reverse block (no controller) — loses integrated UVLO/OV and ideal-diode.
- No UVLO ("the pack BMS handles it") — REJECTED: not every 3S pack has a low-voltage
  cutoff, and relying on an external BMS for a designed-in safety function is the exact
  omission this ADR exists to prevent.
