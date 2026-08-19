# Routing topology reflection — 2026-08-17

## Outcome

The remaining control topology is physically feasible.  The proof candidate is
`06_build/route/placement_probes/nearhub-x78y60-complete.kicad_pcb`.
Its immutable-workspace receipt reports:

- all eight required control/sense nets connected;
- zero hard physical DRC findings;
- zero new via-in-pad findings;
- the expected route-base rejection because the experimentally proven
  placement has not yet been promoted into source-owned floorplan inputs.

The divider placement probe found one zero-hard near-hub position in the
bounded 49-point scan: `R_VBUS_TOP=(78,60)` and
`R_VBUS_BOT=(78,62)`.

## What went well

- Candidate grading separated real physical failures from expected source-base
  mismatches throughout the experiment.
- Placement was scanned before promotion, so failed positions did not churn the
  canonical floorplan.
- The successful three-layer route used only 1,369 search iterations and one
  via for `HUB_VBUS_SENSE`; `USB_UP_VBUS` then used 4,747 iterations and one
  via.  Both held 0.30 mm clearance.
- The existing reviewed `HUB_OCS1_N` route remained intact.

## Where time was spent

- The initial assumption that final controls should remain on F.Cu/B.Cu led to
  long five-via detours and localized conflicts with P4, OCS, management, and
  reset copper.
- A handcrafted outer-layer crossover increased the hard-error count because
  it was authored before systematically querying all occupied corridors.
- Once In2.Cu was admitted for this low-speed signal while In1.Cu stayed a
  continuous reference plane, the route solved in 0.06 seconds.

## Generalizable learning

Before escalating outer-layer rip-up on an already crowded four-layer board,
classify the unfinished net and inspect layer intent.  For a low-speed control
or DC sense net, a short signal segment on the non-primary internal plane can
be preferable to a long outer-layer weave, provided:

1. at least one adjacent ground plane remains continuous;
2. the route does not enter an RF/USB differential-pair contract;
3. fill/return-path and plane-continuity gates are rerun after promotion; and
4. the fabrication stack supports the ordinary through-via geometry.

Placement feasibility should also be a bounded, machine-graded scan before a
floorplan change is promoted.  A legal component location is not sufficient;
the location must be proven with both of its required routes and any
temporarily displaced nets restored.

## Next stage

Promote the `(78,60)/(78,62)` placement and the proven route policy into
source-owned inputs, regenerate the prepared base, rebase the reviewed route
chain, and require an accepted (not merely physically passing) candidate
receipt before stitching.
