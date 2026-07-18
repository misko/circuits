# ADR-0002 — 5V input: barrel jack + protection chain (mandatory protection ADR)

Status: accepted 2026-07-18 (brief §5A names the Mean Well GST25A05-P1J
as the supply candidate; connector + protection delegated, D4)

## Context

Single 5V input powers everything: both bucks, both LDOs, six pod feeds
(+5V_AUDIO, ~6mA each), and the beeper feeds (150mA, one pod at a time).
Worst-case draw ~1.2A; GST25A05-P1J supplies 5V/5A on a 5.5x2.1mm
center-positive barrel plug. The cable ports leave the enclosure — ESD
enters here too (per-port protection is the port channel's job; this ADR
is the power entry).

## Decision

- **J9 = DC-005 5.5x2.1mm barrel jack (center positive), populated.**
  Matches the named supply's P1J plug directly; keyed against reversal in
  normal use.
- **J11 = KF128L-3.5-2P screw terminal, DNP footprint** in parallel:
  field/bench alternative supply entry (silk-labeled 5V/GND). This is the
  path that CAN be miswired, hence:
- **Protection chain (entry -> rail):**
  1. **F1 SMD1812P200TF16 PTC, 2A hold** — limits fault current from the
     5A-capable supply into any board fault; 2A >= 1.7x worst-case draw
     so no nuisance trips (math in DETAIL_DESIGN.md).
  2. **D9 SMBJ5.0A TVS to GND (reused fleet part C113974)** — clamps cable ESD/inductive transients;
     5V working = exactly the rail, acceptable because the GST25A05 is
     regulated +-2% (leakage at 5.0V standoff is uA-class).
  3. **Q9 AO3401A P-FET reverse-polarity guard** (drain toward load, gate
     to GND via 100k; body diode conducts first, FET then shorts it):
     ~10mV drop at 1.2A vs 400mV for a schottky — preserves pod +5V_AUDIO
     headroom on 35ft drops. -12V reverse leaves the FET off; abs-max
     Vgs +-12V not exceeded at 5V input (no divider needed).
- No UVLO: 5V wall supply, no battery to over-discharge (contrast the
  canon's LiPo incident — N/A here, stated deliberately).

## Rejected

- Series schottky only: 0.4V drop eats pod bias headroom.
- Bare entry (barrel is keyed): the DNP terminal alternative and outdoor
  cable plant make "keyed" insufficient; three boards in the fleet audit
  shipped with zero entry protection — not repeating that.
