# Pluto RX2 eight-way v5 enclosure v0.5.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v0.2.1-2026-08-14**

Design-lineage baseline: **v0.4.0-2026-08-25** (legacy release schema)

The schema-v2 manifest leaves `predecessor` null because the current publisher
can bind only a schema-v2 predecessor. The legacy v0.4 bytes remain untouched.

This candidate addresses two physical failures observed in the predecessor
print: the PCB reached SMA bodies before it seated on its supports, and the
right-angle RX2 antenna had visible lateral movement in the top adapter.
`source/reference/physical-fit-observation-2026-08-26.md` records the four
photo hashes and relational observations. It makes no pixel-derived dimension
claims.

## Pillar-only base

The lower perimeter wall and alignment lip are gone. `meshes/base.stl` now
contains only:

- a 2.40 mm printable foundation connecting the features;
- four short PCB support/insert pillars at H1–H4; and
- four tall, external case-closure posts at `(±49.0, ±36.5)` mm.

The PCB uses four M3 × 6 screws in its own supports. Four different M3 × 6
screws close the lid to the external posts. No case screw shares a PCB axis or
load stack, and no SMA/USB-C body is an intended support.

Machine evidence records zero base sidewall height, four PCB supports, four
case posts, 1.15685 mm minimum post-to-PCB-corner clearance, exact
base-versus-complete-STEP volume of 0 mm³, and exact empty BREP drop-in
checkpoints at 0, 5, 15, and 45 mm above the installed datum.

## Snug, bottom-loaded antenna adapter

The already-wired L antenna still slides into the adapter from its fully open
58 × 31 mm underside. The rigid upright aperture, rail path, and south
full-body arch remain 10.8 mm; the cable is never threaded through a bore.

A localized four-millimetre section of the roof-hung rail pair now provides a
compliant key near the elbow/tongue:

- target gap: **9.75 mm**;
- open-bottom mouth: **11.75 mm**;
- entry lead/blend: **1.00 mm**;
- inset from the rigid rails: **0.525 mm per side**;
- nominal overlap against the conservative D10 witness: **0.125 mm radial**.

The 9.75/11.75/1.00 geometry is authorized only as a compliant void measured
from the exact user holder STL (SHA-256
`a1e74e1611c6b9027d5c63d88bc9293ca1ad833619e40cb52d8556bd1cd1030f`).
It does not measure the production antenna. The 4 mm axial placement is a CAD
candidate. `meshes/rx2_antenna_fit_gauge.stl` therefore exposes actual channel
gaps **9.50, 9.75, 10.00, and 10.25 mm** for printer/material selection.

## Automated evidence

- schema-v2 intent and composition: VALID;
- sealed STEP occurrence coverage: 30/30 modeled footprint references;
- generic shell checks: 6/7 PASS, zero FAIL, physical evidence INCOMPLETE;
- printable mesh census: 6/6 PASS (five parts plus installed case);
- exact installed-case/STEP collision: EMPTY, 0 mm³;
- exact base/complete-STEP collision: EMPTY, 0 mm³;
- rigid 45 mm full-prewired-assembly insertion selector: EMPTY;
- antenna/mount, antenna/board, antenna/fastener, antenna/cable, and cable/lid selectors: EMPTY;
- localized compliant-key overlap selector: SOLID as required, 2.667401 mm³;
- antenna and cable versus exact STEP components: 0 mm³ each;
- collision-receipt atomic-filename regression suite: 15/15 PASS.

`verification/verification.json` is subordinate CAD evidence and reports
`CAD_READY`. It does not promote this release: the governing accessory receipt
and all schema-v2 release scopes remain `INCOMPLETE` under the current
publisher policy.

## Release-root replay

The release-local `source/enclosure-v2.yaml` and
`source/enclosure-cad-design-v2.yaml` bind only files inside this release.
`MANIFEST.json.replay.tools` binds the complete Python tool/import closure used
for schema validation, generation, STEP inspection, exact collision, generic
verification, and the Pluto antenna/base verifier. In particular,
`tooling/verify_antenna_clearance.py`, `enclosure_common.py`,
`process_runner.py`, and `pipeline_runtime.py` live together so replay cannot
depend on the repository's `skills/` tree.

Release qualification included a replay from a copied release tree outside
the repository with a sanitized `PYTHONPATH` and working directory. That run
validated both schema-v2 contracts, regenerated all five canonical meshes,
re-inspected the release-local STEP, rebuilt exact collision evidence, reran
the generic CAD verifier, and reran the complete antenna/base verifier. Fresh
printable and cable-reference mesh bytes matched this candidate. The antenna
reference matched in topology, bounds, and volume within contract tolerance;
its facet ordering differed. All governing collision metrics matched. External
PCB-authority verification was then repeated against the live parent release.

## Required physical retest

1. Print the new base. Confirm the unpowered PCB seats simultaneously on all
   four supports, cannot rock, and shows clearance around every SMA/USB-C body.
2. Retain the PCB with only its four screws; remove lid/case screws and confirm
   the board cannot move.
3. Mate every connector and verify the four separate case screws close the lid
   without touching or loading the PCB.
4. Print the channel coupon. Starting loose, select a snug station without
   forcing or marring the actual antenna.
5. Print the adapter and test bottom insertion/removal of the complete prewired
   antenna, elbow/tongue retention, rattle, cable strain clearance, and screw-down
   seating.
6. Record the normal thermal soak before claiming thermal qualification.

Until these tests are recorded, this release is **not PRINT_VERIFIED, not
THERMALLY_VERIFIED, not order-ready, and not a production-fit assertion**.
