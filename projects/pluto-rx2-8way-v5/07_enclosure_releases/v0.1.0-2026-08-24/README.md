# Pluto RX2 eight-way v5 enclosure v0.1.0

Status: **CAD_READY**

Based on PCB release: **v0.2.1-2026-08-14**

This is the first independent enclosure release for the sealed Pluto RX2
eight-way v5 PCB geometry. It uses the reviewed hand-authored OpenSCAD design,
not the generic rectangular enclosure approximation.

## Printable files

- `meshes/base.stl`
- `meshes/lid.stl`
- `meshes/insert_coupon.stl`

The assembled enclosure measures approximately `96.8 x 71.8 x 27.1 mm`.
The insert coupon is `54 x 20 x 6 mm`.

## Verification

- exact subject bindings: 5/5 PASS;
- connector/interface coverage: 62/62 PASS;
- fastener geometry: 9/9 PASS;
- printable meshes: 3/3 PASS;
- exact STEP-component/case intersection: EMPTY, 0 mm^3;
- thermal-plan consistency: 2/2 PASS;
- physical evidence: INCOMPLETE, 0/3.

The self-contained replay package is in `package/`. It contains the exact PCB,
STEP, interface, authored SCAD, printable meshes, collision evidence, and a
path-rebased `replay/enclosure.yaml` configuration.

## Before calling this print-verified

1. Print and qualify the insert coupon with the intended material, printer,
   nozzle, and layer height.
2. Print the base and lid.
3. Install the actual assembled PCB without force and confirm lid closure.
4. Mate all intended SMA, USB-C, SWD, and bench-power interfaces together.
5. Record the physical evidence and mint a new immutable enclosure release.

This enclosure release does not change the PCB release's existing order state
and is not yet `PRINT_VERIFIED` or `THERMALLY_VERIFIED`.
