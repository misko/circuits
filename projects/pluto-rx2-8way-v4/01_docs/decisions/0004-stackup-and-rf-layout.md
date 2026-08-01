# ADR-0004 — four-layer advanced controlled-impedance stack

Status: accepted, 2026-07-31.

Target `jlc_4layer_advanced` on the selected JLC four-layer controlled-
impedance stack. PE42482A-X is a 0.5 mm-pitch QFN whose ground/RF land field and
via requirements exceed the standard-tier geometry. L2 remains continuous
ground, L3 carries control routing, and B.Cu is ground-dominant.

All RF stays on F.Cu without vias. The 50-ohm width is derived from the ordered
stack rather than inherited blindly. The module removes the RP2040 escape
problem but does not relax the RF switch or SMA launch constraints.
