# Pre-route pin review — USB-Controlled Debug Hub v2

review_stage: pre-route
review_kind: pin
reviewer: Codex exact-artifact pin and package review
reviewed_at: 2026-08-19
design_verdict: SOUND
order_verdict: BLOCKED-SOURCING
board_sha256: 876030c53811ed00841c3b809cd92d58673a80d05b2e7fa38182ec8fd97b3b26
parts_sha256: d089da4ca84240ff3077e02bdc909dcb3e9d23a41b4967a3f785297b722e626a
design_rules_sha256: be908d898837e6c1d23774e5f97d0f29b5829a160e13bc45da40d42c103a2e82

## Findings

- P0: none.
- P1: JLC's order preview must confirm D_PD_TVS pin 1 and its GND/IN
  bank orientation. Its exact numbered-land fit selects rotation offset zero,
  but the symmetric 3+3 package has no independent function-tied visual mark.
- P2: none.

## Review

- The exact-board pin audit generated 27 active dossiers, including both
  USB-C connectors, all four USB-A connectors, TVS1800DRVR and
  TPS259804ONRGER. Electrical-invariant grading passes 137/137.
- D_PD_TVS implements the TI DRV0006A identity: pins 1--3 and exposed pad 7
  are GND; pins 4--6 are the fused VBUS input bank. The exact JLC C2649846
  numbered-pad fit is 0.0000 mm at offset 0 versus 1.5171 mm next best.
- U_AGG implements TPS259804ONRGER: primary IN pins 1--3 and split IN
  PowerPAD 25 receive P5V_REG, pin 16 is locally joined to the same input,
  output pins 17--24 feed P5V_PROTECTED, and TIMER/ILIM/DVDT reach their
  dedicated support components. The exact C2878936 fit selects offset 0 by
  both numbered pads and independent size-class geometry.
- J_DATA and J_POWER retain their approved exact HRO connector footprints,
  pad identities, outward-facing access direction and source-owned STEP
  bodies. No connector pin or net changed during the aggregate-cell update.

The physical pin, package and net assignments are SOUND for routing. This is
not order authorization; uploader-side rotation/polarity and allocation gates
remain open.
