# Render review — crow-recorder-central-v2 v1.5-2026-07-25

**Renders REGENERATED for v1.5** (2026-07-25 21:08–21:09). None are reused from
v1.4: the render path carried a handedness bug fixed in 9066ebd/828db4c, so an
inherited render would be evidence about the old code, not this board.
Reviewed: `twin_{top,bottom,iso_nw,iso_se,edge_west,edge_east}.png` (modeled,
JLC's own part bodies) and `render_{top,bottom}_bare.png` (no components, the
kicad-cli truth view).

## What the renders DO show

- **Board outline and population read correctly.** 8 RJ45 jacks in a row along
  the north edge (J3–J10), the DC barrel jack on the west edge (J1), USB-C at
  south-centre (J2), the XU316 TQFP-128 centred (U1) with its two PCM1865
  TSSOP-30 ADCs symmetrically north-west and north-east (U2/U3), the 1×08 JTAG
  header at south-east (J_DBG). This matches the floorplan and the schematic's
  intent.
- **Bodies mounted 174/174** on the CPL population, `missing_models.txt` empty
  — every placed designator resolves a 3D body. (v1.4's own missing_models
  claimed "0 missing" while 27 footprints had unresolvable model paths; this
  release's coverage is real, and the file states its denominator.)
- **No body-on-body collision or overhang** at the four board edges in
  `twin_edge_west/east` and the two isometrics.
- **Silk legibility:** the "NOT ETHERNET — CUSTOM 5V AUDIO PINOUT" warning
  banner and the per-port pinout legend are present, unclipped and the right
  way up on `render_top_bare.png` — this is the board's single most important
  silk feature (a pod plugged into real Ethernet is the deployment hazard
  section 0 exists for) and it survives.
- **J1, J3–J10, JP_INJ, R_inj1, R_inj2 still render with bodies.** That is
  CORRECT and expected, not a contradiction of the CPL: `jlc_twin --assembly`
  deliberately mounts coded-but-not-assembled parts so their LAND PATTERN is
  still checked. Population truth is `fab/cpl.csv`, not the render.

## What the renders DO NOT show — stated so nobody infers it

**No render in this release validates the CPL coordinate, which is the defect
v1.5 exists to fix.** The twin mounts each body at the BOARD footprint's
position, not at the CPL's `Mid X/Y`. A render of a board whose CPL is 1.3 mm
wrong looks identical to a render of a board whose CPL is right — which is
precisely why v1.4 passed a render review and still shipped a USB-C that
cannot seat.

The CPL coordinate is graded by **A-POS** (`assembly_coverage.py`, worst
residual 0.00050 mm over all 174 rows) and, independently, by the **order-time
JLC placement preview** required in ORDER_README §3a. Both are needed; neither
is a render.

## Verdict

**PASS** — for what a render can decide (population, bodies, mechanical fit,
silk). Explicitly NOT a verdict on placement coordinates.
