# ADR-0004 — four-layer advanced controlled-impedance stack

Status: accepted, 2026-07-31.

Target `jlc_4layer_advanced` on JLC's `JLC04121H-7628` four-layer controlled-
impedance stack, nominal 1.2 mm and ENIG, with the advanced 0.25/0.15 mm
finished-via/drill option. PE42482A-X is a 0.5 mm-pitch QFN whose ground/RF land
field and via requirements exceed the standard-tier geometry. L2 remains
continuous ground, L3 carries control routing, and B.Cu is ground-dominant.

The 1.2 mm stack is binding, not cosmetic. JLC's published plated-through-hole
limit is 10:1 board thickness to mechanical drill: 1.2/0.15 is 8.0:1, whereas
the rejected 1.6 mm construction was 10.667:1 on all 3,446 vias. The selected
1.2 mm 7628 construction preserves the same 0.2104 mm top prepreg, so the
surface RF cross-section and 0.36 mm CPWG geometry do not move.

All RF stays on F.Cu without signal vias. `03_src/cpwg_field_solver.py` solves a
periodic 3-D quasi-static unit cell containing the actual masked CPWG and both
via-fence rows at the conservative measured offset and pitch. Its finest mesh
gives epsilon_eff 3.173354, 5.942081 ps/mm and 52.087735 ohm; the complete
mesh-convergence interval is 49.19..54.99 ohm, inside the authored 50 ohm
+/-10% contract. The machine-readable output is
`06_build/verify/cpwg_field.json`, and R-LEN fails if the declared constants
drift from it.

The order must invoke controlled impedance and retain coupon/TDR evidence. JLC
may not silently alter the sealed Gerbers: if its solver requires geometry
outside the authored interval, it must return revised production plots for
review and a new seal. The module removes the RP2040 escape problem but does
not relax the RF switch or SMA launch constraints. JLC must separately accept
the ten plug-in SMA jacks in writing.
