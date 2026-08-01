# ADR-0004 — four-layer advanced controlled-impedance stack

Status: accepted, 2026-07-31.

Target `jlc_4layer_advanced` on JLC's `JLC04161H-7628` four-layer controlled-
impedance stack, nominal 1.6 mm and ENIG, with the advanced 0.25/0.15 mm
finished-via/drill option. PE42482A-X is a 0.5 mm-pitch QFN whose ground/RF land
field and via requirements exceed the standard-tier geometry. L2 remains
continuous ground, L3 carries control routing, and B.Cu is ground-dominant.

All RF stays on F.Cu without vias. The authored 0.36 mm masked CPWG is the
design model derived from that stack, not an order-side guarantee. The order
must invoke JLC's impedance solver, permit controlled width/spacing adjustment,
and retain coupon/TDR evidence. The module removes the RP2040 escape problem
but does not relax the RF switch or SMA launch constraints. JLC must separately
accept the ten plug-in SMA jacks in writing.
