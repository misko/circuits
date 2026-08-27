# USB Hub 3S v3 enclosure v0.2.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v1.12-2026-07-28**

Enclosure predecessor: **v0.1.0-2026-08-27**

This immutable candidate updates the E-Z LOK 260-M3 insert fit while keeping
the enclosure topology, PCB basis, connector clearances, independent PCB/case
fasteners, and thermal plan unchanged.

The production insert pilot changes from the untested D3.95 mm datasheet start
to a **D4.25 mm coupon prior**. The new `meshes/insert_coupon.stl` brackets it
with D4.05, 4.15, 4.25, 4.35, and 4.45 mm stations. The prior comes from the
closest same-family PETG/0.4 mm nozzle/0.2 mm layer observation in the
repository-wide fit registry. It is not a physical result for this enclosure.

## Printable files

- `meshes/base.stl` — floor-down foundation with eight D4.25 insert pockets,
  four dedicated PCB supports, and four independent case-closure posts;
- `meshes/lid.stl` — roof-down one-piece lid with four skirts and five
  bottom-open connector notches; and
- `meshes/insert_coupon.stl` — D4.05–D4.45 insert-fit ladder.

The PCB is retained by four M3 × 6 screws on H1–H4. Four different M3 × 6
screws close the lid at the perimeter. Removing the lid screws cannot release
the PCB.

## Automated evidence

- schema-v1 accepts the explicit `pilot_basis: coupon_prior` only while the
  insert coupon remains a required physical test;
- schema-v2 intent/composition validation passes;
- generation completes for 3/3 declared printable parts plus the fixed
  installed-case selector;
- the exact parent-plus-supplement composition covers all 121 modeled PCB refs
  plus SW1, with 244 component solids; and
- the installed enclosure versus that exact composition is `EMPTY`, exactly
  **0 mm³**.

The D4.25 pocket change is internal to the eight bosses/posts and does not
change connector access or lid motion. Renders remain relational review
evidence, not physical fit evidence. `renders/insert-coupon.png` shows the new
ladder and labels.

## Why status remains INCOMPLETE

No v0.2.0 coupon, insert installation, board drop-in, support-clearance,
connector-mating, lid-off retention, closure-independence, service-cycle, or
thermal-soak result has been recorded. The transferred D4.25 prior therefore
cannot be called coupon-qualified for this enclosure.

Before using the full base:

1. Print the D4.05–D4.45 coupon in the production PETG profile and boss
   orientation.
2. Install the exact insert lot into every station and record seating,
   insertion method/force, boss damage, spin-out, and pull-out tendency.
3. Select the smallest reliable station and update the authored source if it
   is not D4.25.
4. Print the base, complete the project physical plan, and add the result to
   the global fit registry with printer, material, profile, and test evidence.

Until those steps are complete, this release is **not CAD_READY,
PRINT_VERIFIED, THERMALLY_VERIFIED, order-ready, or a production-fit claim**.

## Release-root replay

The release-local configs bind only release payloads and copied PCB
authorities. The manifest includes the complete Python import closure for
schema validation, generation, obstruction composition, exact collision, and
release reopening. A clean replay must regenerate all three printable meshes,
recompose the complete obstruction subject, reproduce the 0 mm³ collision,
and reopen the full payload census.

The enclosure release is independent of the PCB release. Nothing under
`07_releases/v1.12-2026-07-28/` or the predecessor enclosure release was
edited.
