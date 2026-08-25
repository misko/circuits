# Pluto RX2 eight-way v5 enclosure v0.1.1

Status: **CAD_READY**

Based on PCB release: **v0.2.1-2026-08-14**

This immutable enclosure release replaces only the insert-fit calibration
coupon from v0.1.0. The coupon now tests four modeled pilot diameters:
`4.15`, `4.25`, `4.35`, and `4.45 mm`, left to right when the recessed labels
face the operator.

The production base pocket deliberately remains `3.95 mm`. Print this coupon
first, identify the smallest diameter that accepts the specified cold-press
insert without cracking or visibly whitening the boss, and only then revise
the production pocket in a later enclosure release.

## Printable files

- `meshes/insert_coupon.stl` — revised 4.15–4.45 mm calibration ladder
- `meshes/base.stl`
- `meshes/lid.stl`

The assembled enclosure measures approximately `96.8 x 71.8 x 27.1 mm`.
The insert coupon is `54 x 20 x 6 mm`. A labeled coupon preview is available
at `renders/insert-coupon.png`.

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

## Before changing the production base

1. Print the revised coupon using the intended material, printer, nozzle,
   layer height, orientation, and slicer profile.
2. Test the same insert family intended for the enclosure.
3. Record the smallest reliable pocket, flange seating, boss condition, and
   whether the insert spins or pulls out.
4. Update both the authored SCAD production pocket and `enclosure.yaml` to the
   selected diameter, then mint another immutable enclosure release.

This release remains `CAD_READY`; it is not `PRINT_VERIFIED` or
`THERMALLY_VERIFIED`, and it does not change the PCB release's order state.
