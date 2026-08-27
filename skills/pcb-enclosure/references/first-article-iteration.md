# First-article enclosure iteration

Treat a first print as measured evidence about a particular enclosure,
printer, material, slicer, hardware lot, and installed assembly. Preserve the
failed observation, identify which authority or design assumption it tests,
and regenerate from source. Never repair an STL directly.

## Audit the load path

Name every intended PCB support and every intended case-closure support. With
the lid removed and board screws secured, verify that the PCB seats
simultaneously on all intended bosses or rails. Check that no connector body,
solder tail, component, perimeter wall, panel, or closure post bears load.

An empty intersection mesh proves only non-penetration within represented CAD.
It cannot prove contact pressure, coplanarity, print warp, or which feature
actually carries the board. Add the typed `board_support_clearance` physical
test whenever an alternate bearing path is plausible. If a perimeter feature
causes an edge component to become a standoff, remove or relocate that feature
or change to isolated pillars; do not raise the PCB by resting it on the part.

## Keep retention roles independent

PCB screws retain PCB plus base and remain secured with the lid removed. Case
screws retain base plus lid and never clamp or release the PCB. Recheck screw
engagement, tip clearance, insert access, and axis separation after every boss
or post move. A case that appears rigid while closed can still leave the board
loose during service.

## Verify the real assembly path

Model the state transition, not only the final pose. For a prewired item, sweep
the complete body, connector, already-attached cable exit, and any rigid elbow
through the actual opening. Size an arch or slot for the maximum body radius,
not merely the cable. Prefer a declared straight insertion leg over an
unmodeled S-shaped, threaded, flexed, or compound path. Declare both insertion
and removal when the documentation promises service removal or replacement.

An inspiration holder, photograph, or unrelated STL may teach loading
direction, local compliance, or retention topology. It is not dimensional
authority for the installed part. Bind exact vendor geometry or traceable
measurements separately; otherwise use a conservative candidate with explicit
excluded claims and a readiness ceiling.

## Qualify fit locally

Start insert pilots from the exact insert datasheet, then print a bracketed
coupon with the production printer, material, slicer, orientation, and local
wall thickness. Record the selected pilot and process; a value qualified on a
different print is not evidence for this one.

When controlled compliance is necessary, isolate it in a short key, tongue,
or flexure with a lead-in and a hard motion stop. Print a gap or fit coupon
covering the production clearance. Avoid making the whole enclosure wall the
spring, because global flex changes connector alignment and closure fit.

Use the repository-wide
[fit and tolerance registry](../../../docs/enclosure-fit-registry.md) as a
record of priors, not as a default table. After a traceable coupon or assembly
test, preserve the project-local raw evidence first, then add an evidence-graded
registry observation with total and per-side allowance, process, result, and
limits. Never promote a CAD-only candidate or inspiration-holder measurement
to a production tolerance.

## Harden reproducibility before promotion

- Reject unknown CAD selectors; export collision geometry only through the
  fixed installed-case selector.
- Make project-specific verifiers reject missing subjects, partial obstacle
  censuses, stale hashes, unknown selector output, and vacuous denominators.
- Aggregate every required scope. A ready shell cannot hide an incomplete
  accessory, motion, support, or thermal scope.
- Keep source, committed authorities, exact generation commands, printable
  part census, stable build paths, and physical-test plan discoverable before
  considering publication.
- For an immutable enclosure candidate, copy every required tool/import or
  bind it explicitly, replay from the release root, and reopen the staged
  result. A governing `FAIL` remains mutable source work; do not launder it
  into an immutable release.

## Close the loop

For each observation, record: observed condition, affected scope, exact
subject/config identity, diagnosed cause, source change, regenerated artifact,
automated result, physical retest, and remaining unknowns. Promote only the
scope supported by that chain. Photographs and renders are useful witnesses,
but neither substitutes for dimensional authority, motion evidence, or a
dated physical test.
