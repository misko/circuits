---
id: 0003
date: 2026-07-17
status: accepted
---
# 0003 — 4-layer board (SIG/GND/PWR/SIG), JLC standard tier

## Context

The board carries 24 capacitive-electrode lines (the product's sensing
floor), a 1.1MHz buck, a chopper stepper driver, an RF module, and ~110
parts with ~100 nets. 2-layer vs 4-layer decides the MPR121 noise floor
and the routing risk.

## Decision: 4 layers

- **Cap-sense noise floor**: MPR121 layout guidance (AN3892 class) wants a
  stable reference and aggressor isolation for electrode traces. On 2
  layers the B.Cu "plane" gets shredded by escape routing exactly under
  the MPR121 cluster; on 4 layers In1 is an unbroken GND plane under every
  electrode stub and the I2C bus, and the buck/motor switching return
  currents stay under their own corner.
- **Routing density**: 24 electrode stubs + 4x QFN-20 0.4mm-pitch escapes
  + module + driver on 2 layers is exactly the escape-saturation regime
  the kicad-pcb skill warns about. 4 layers keeps every escape short.
- **Aggressor separation**: motor phases (1A chopped) and the 1.1MHz SW
  node return over In1 without sharing copper with electrode guard pours.
- **Cost**: qty-5 prototype delta ~$15 total (JLC 2L ~$4 vs 4L ~$20 per
  5 boards at this size) — noise-floor insurance for the core feature.
  At 10k units the 4L premium is ~$0.5-0.8/board; COST_ESTIMATE.md (c)
  carries "re-qualify on 2 layers after EMC/sensitivity validation" as an
  optimization candidate, explicitly gated on measured cap-sense SNR.
- **Tier**: JLC standard 4L (0.45/0.3 vias, 0.127 track/space capability;
  we design at 0.2+ signal / 0.127 floors). The 0.4mm-pitch MPR121 QFN
  escapes go straight out on F.Cu (no between-pad routing at any legal
  geometry — skill golden rule 5); no advanced small-via option needed
  unless fanout proves otherwise (it did not: release DRC is clean at
  standard geometry).

Stackup: F.Cu signal+parts, In1.Cu solid GND plane, In2.Cu power pours
(12V motor region / 5V / 3V3), B.Cu signal + GND pour.
