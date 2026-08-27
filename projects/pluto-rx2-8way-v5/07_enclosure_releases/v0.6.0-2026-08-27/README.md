# Pluto RX2 eight-way v5 enclosure v0.6.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v0.2.1-2026-08-14**
Enclosure predecessor: **v0.5.0-2026-08-26**

This immutable candidate applies the requested **1.25 mm total** tightening to
the v0.5 antenna adapter. The two compliant key faces move inward 0.625 mm per
side, changing the key gap from 9.75 to **8.50 mm** and its open mouth from
11.75 to **10.50 mm**. The upright antenna-hole diameter changes from 10.80 to
**9.55 mm**, also 0.625 mm inward per radius. The south full-body U-arch and
broad loading channel remain D10.80 so the prewired L assembly still loads from
the adapter's rectangular underside without cable threading.

`meshes/rx2_antenna_fit_gauge.stl` now carries clearly modeled 8.25, 8.50,
8.75, and 9.00 mm gap stations. Print and test the gauge before the adapter.

## Automated evidence

- schema-v2 intent and composition: valid;
- printable mesh census: 5/5, with 6/6 including installed-case evidence;
- sealed STEP occurrence coverage: 30/30 modeled footprint references;
- installed case versus exact PCB STEP: empty, 0 mm³;
- all non-fit rigid antenna, cable, fastener, board, and insertion selectors:
  empty;
- intended D8.50 key overlap against the conservative D10 witness:
  30.278939 mm³ across two key faces;
- intended D9.55 aperture overlap against the conservative D10 lower upright:
  29.649334 mm³ in one collar;
- antenna/cable versus exact STEP components and base versus complete STEP:
  empty, 0 mm³.

The two solid fit selectors are expected candidate interference, not collision
failures or proof of successful elastic insertion. Renders were visually
inspected for the full assembly, cutaway loading orientation, and revised
coupon labels.

## Required physical work

The D8.50 key represents 0.75 mm nominal radial overlap with the conservative
D10 witness; the D9.55 hole represents 0.225 mm radial overlap. These are large
enough that a rigid-body model cannot prove passage. Before use:

1. Print the 8.25/8.50/8.75/9.00 gauge in production material and orientation.
2. Confirm the real antenna inserts without damaging force or surface marring.
3. Test retention, rattle, cable strain, and at least ten insertion/removal
   cycles for cracking or permanent set.
4. Re-run the existing PCB seating, independent-fastener, connector-mating,
   and thermal checks from v0.5.

Until that evidence is recorded, this candidate is **not CAD_READY for the
antenna accessory, not PRINT_VERIFIED, not THERMALLY_VERIFIED, not order-ready,
and not a production-fit assertion**.
