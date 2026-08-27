# USB Hub 3S v3 enclosure v0.1.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v1.12-2026-07-28**

This is the first immutable, downloadable enclosure candidate for the
fabricated three-output USB hub. Printable files are in `meshes/`:

- `base.stl` — floor-down foundation with four dedicated PCB supports and four
  separate case-closure posts;
- `lid.stl` — roof-down one-piece lid with four skirts and five bottom-open
  connector notches; and
- `insert_coupon.stl` — E-Z LOK 260-M3 pilot ladder.

The PCB is retained by four M3 × 6 screws on H1-H4. Four different M3 × 6
screws close the lid at the perimeter. Removing the lid screws cannot release
the PCB.

## Complete obstruction evidence

The sealed PCB STEP remains byte-for-byte unchanged and contains 106 of 121
modeled references. It omits F2, J1-J5, Q1-Q6, and U3-U5; SW1 declared no body.
This release therefore does not pretend the parent STEP was complete.

Instead, `source/reference/obstruction-models.json` binds exact JLC/EasyEDA
catalog bodies, registration footprints, transforms, and LCSC-valued PCB refs
for those 16 parts. `tooling/prepare_obstruction_step.py` produces only their
supplemental solids. `tooling/compose_obstruction_step.py` combines those
solids with the immutable parent STEP and proves the union covers all 121
modeled refs plus SW1.

The resulting exact composition contains 244 component solids. The normal
CadQuery/OCP BRep collision gate reports `EMPTY`, exactly **0 mm³**, against the
installed enclosure. This is candidate CAD evidence, not received-part fit
evidence.

## Why status remains INCOMPLETE

No physical coupon, board drop-in, support-clearance, connector-mating,
lid-off retention, closure-independence, service-cycle, or thermal-soak result
has been recorded for this print. Catalog CAD does not establish received-part
tolerances, plug overmolds, cable bends, fuse access, switch feel, printer
shrinkage, insert fit, or operating temperature.

Do not call this release CAD_READY, PRINT_VERIFIED, THERMALLY_VERIFIED,
order-ready, or production-fit. Print the coupon first, then complete the
physical plan in `source/mechanical-intent-v2.yaml` and the project mechanical
README before promoting any claim.

## Visual review

- `renders/assembly.png` — exploded base/PCB/lid view;
- `renders/base-board.png` — lid-off support/load-path view; and
- `renders/closed-assembly.png` — closed-case review.

The renders are relational evidence only. The exact collision receipts live in
`verification/composite-step-inspection.json` and
`verification/composite-collision.json`.

## Release-root replay

The release-local configs bind only files within this release. The manifest
binds the full Python import closure for schema validation, generation,
supplement production, exact composition, STEP inspection, collision, and
release reopening. A clean replay must:

1. validate `source/enclosure-v2.yaml` from the release root;
2. regenerate all three printable meshes from `cad/usb_hub_3s_v3_case.scad`;
3. rebuild `verification/supplemental-obstructions.step` from the copied PCB
   authority and catalog models;
4. recompose 121/121 modeled refs plus SW1;
5. reproduce the exact 0 mm³ installed-case collision; and
6. reopen the complete release census with the release verifier.

The enclosure release is independent of the PCB release. Nothing under
`07_releases/v1.12-2026-07-28/` was edited.
