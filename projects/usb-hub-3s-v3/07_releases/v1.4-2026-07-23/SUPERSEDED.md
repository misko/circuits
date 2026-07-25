# SUPERSEDED — v1.4-2026-07-23

**Superseded by `07_releases/v1.5-2026-07-25/`. DO NOT ORDER THIS RELEASE.**

## Reason: C1 and C2 are placed 180° REVERSED

`fab/cpl.csv` of this release places **C1 and C2 at rotation 270.0**:

    C1,C2982822,CP_Elec_6.3x7.7,26.5,-60.0,top,270.0
    C2,C2982822,CP_Elec_6.3x7.7,26.5,-72.0,top,270.0

**The measured correct value is 90.0.** C1 and C2 are
**C2982822 = KNM2100UF35V149EC0055, 100 µF / 35 V POLARIZED polymer aluminium
electrolytics**, wired `pin 1 = VIN (+)` / `pin 2 = GND` — directly across the
XT60 3S-LiPo input (9.0-12.6 V) behind a 10 A blade fuse. Assembled at 270.0
they are **reverse-biased on a near-zero-impedance source**: they heat, gas and
**vent**, at first power-up, upstream of every bench gate this release's
ORDER_README specifies.

**Measured 2026-07-25**, independently of `jlc_twin`'s reported offset (which
was negated by a handedness bug — see repo commit `e0d735c`), using the operator
verified against `pcbnew` itself:

    our CP_Elec_6.3x7.7 : pad1 (VIN, '+') local x = -2.700 mm
    JLC C2982822 model  : pad1              local x = -2.670 mm
    -> already aligned, offset 0; fit rms 0.030 mm @0 vs 5.370 mm @180
    -> board orientation 90.0 + 0 = CPL 90.0        (this release ships 270.0)

Polarity cross-checked against JLC's own library silk rather than assumed: two
crossed filled polygons centred at (−2.706, 1.518) draw a **“+” over JLC's
pad 1**, and a lone bar at (+2.706, 1.518) draws a **“−” over pad 2**. Our pad 1
is on VIN. The two agree, so the pad fit is sound and 90.0 is correct.

## Also corrected in v1.5 (same mechanism, lower severity)

| ref | this release | correct | note |
|---|---|---|---|
| **J1** (AMASS XT60PW-M) | 90.0 | **0.0** | the name-DB pattern is start-anchored and never matched the vendored `XT60PW-M_EdgeTrim`, so no rule fired and the offset defaulted to 0 |
| **Q7** (BSS138, Q6 gate inverter) | 270.0 | **180.0** | `^SOT-23` = −90 is wrong for C78284; would have left Q6 un-gated |

## What is NOT wrong with this release

The **copper is correct and is carried into v1.5 unchanged**: v1.5's gerbers,
both drill files, `source/`, `3d/` and `pdf/` are **sha256-identical** to this
release's (20 files). The BOM is identical row-for-row apart from a newly
populated MPN column. The electrical design — v1.3's R12/D5/R30 fixes, the
tolerance-inclusive margin analysis, the discrete VBUS protection posture — all
stand. **The defect is in the assembly instruction, not the board.**

## Evidence

- Driving review: `08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md`
  (verdict DO-NOT-ORDER; 15 findings, PCBA-1 is this one).
- Dispositions: `08_reviews/DISPOSITIONS.md`, rows PCBA-1..15.
- Acceptance-gate + copper-identity proof:
  `07_releases/v1.5-2026-07-25/verification/cpl_acceptance_gate.md`.
- Source fixes: repo commits `e0d735c` (the handedness root cause),
  `9078ad9` (the C2982822 rotation row), `95a8180` (C98732), `1b69760`
  (`jlc_twin.xform()` itself).

**This directory is otherwise IMMUTABLE and has not been edited.** This file is
the single addition the 07_releases contract permits.
