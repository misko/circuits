# Connector orientation and mating-access review

Use this procedure for every edge-mounted connector and whenever its footprint,
native model, placement, board outline, or intended mating edge changes. It
closes `P-ORIENT`; it does not replace pin-map, native-model registration,
courtyard/body clearance, enclosure, or cable-service checks.

## Contents

1. One fact, one owner
2. Gate position and execution
3. Human evidence
4. Debug one reference

## One fact, one owner

Do not infer a connector mouth from a bounding-box centre, symmetric mounting
holes, reference text, pixels, or a model that merely fits its footprint.
Those channels can all be consistently backwards.

The sources are deliberately split by what they uniquely know:

- `03_src/floorplan.yaml` `asserts.edge_faces[]` owns the intended board edge
  (`x0`, `x1`, `y0`, or `y1`). Do not repeat the edge in another contract.
- The existing `03_src/rules/model_registration.yaml` group owns the exact
  model identity and an optional `orientation:` block. The block records the
  footprint-local mouth axis, model-local mouth/up axes, mounting side,
  mating-plane depth, allowed signed edge offset, and one keyed pad.
- A manufacturer drawing or exact manufacturer STEP owns those local axes and
  the mating-plane depth. Name that authority in the block.

Every realised `J*` reference is in the denominator. It must be orientation-
declared or listed in `orientation_exemptions` with a non-empty reason. Every
declared ref must have exactly one `edge_faces` row, and every `edge_faces` row
must be orientation-declared. Silence, an empty list, and 0/0 are not a pass.

Example extension to an existing model-registration group:

```yaml
orientation:
  authority: "Manufacturer drawing rev C and exact SHA-bound STEP"
  mount_side: front
  footprint_access_axis_local: [0, 1, 0]
  model_access_axis_local: [0, 1, 0]
  model_up_axis_local: [0, 0, 1]
  mating_plane_offset_mm: 8.20
  edge_offset_range_mm: [-0.20, 0.30]
  key_pad: "1"
  model_z_offset_range_mm: [-0.05, 0.05]
```

KiCad board coordinates use +X east/right and +Y south/down. Local axes are
unit vectors before footprint rotation and side mirroring. A positive signed
edge offset means the mating plane projects beyond `Edge.Cuts`; a negative
value means it remains inboard. The allowed range comes from the connector
drawing plus the board/enclosure decision, not from the current placement.

## Gate position and execution

Run `connector_orientation_gate.py` after `P-MODEL-REG` and deterministic route
preparation, before placement review or route import. Use the script's `--help`
for exact syntax.

The machine half checks, for every declared instance:

1. exact native-model SHA and exactly one model;
2. declared front/back mounting side and non-mirrored model scale;
3. model mouth versus footprint mouth, and model up versus board up;
4. transformed footprint mouth versus the single `edge_faces` authority;
5. the access ray leaves the closed board through that edge;
6. manufacturer mating-plane depth versus the measured `Edge.Cuts` distance;
7. one and only one keyed pad.

`P-ORIENT` consumes, but does not duplicate, the preceding `P-MODEL-REG`
mount-side result. Before directional views can be reviewed, the exact model
must already pass signed-Z side-profile evidence for its declared front/back
side. A connector whose mouth axis is correct but whose body is underneath the
PCB is a model-registration failure and cannot reach human orientation review.

A human cannot override a machine failure. Correct the owning source and
regenerate. The command prints render progress as `n/total`; a missing terminal
verdict or external timeout is a failure, never a review pause.

## Human evidence

The gate writes an exact-board review bundle under
`06_build/pre_route/orientation/`. Each image burns in the edge, camera name,
and semantic-subject prefix so filenames cannot silently swap camera meaning.
The magenta box is selected from exact footprint geometry in the top view; it
is never inferred from an image difference. Side crops are projected from the
real connector coordinates through a calibrated board span and deliberately
draw no body box. Physical body bboxes remain exclusively `P-MODEL-REG`'s job.

Each unique orientation tuple requires:

- `top`: authored access arrow in board coordinates;
- `outside`: camera on the cable/mating side, where the mouth must be visible;
- `inside`: opposite camera, where the rear shell must be visible.

Orthogonal profiles are included for a single-instance tuple. Their omission
for repeated edge rows is a recorded occlusion note, not a false geometry
failure. Repeated connectors
with the same exact model, transforms, side, rotation, edge, and orientation
contract share one visual representative; every physical reference remains in
the machine denominator and the approval subject.

Ask the user to confirm the visible mouth, mounting side, keying, and cable
approach. Do not write approval merely because the machine half passed or the
user previously said a different stage looked good. After explicit approval,
write `08_reviews/connector_orientation.yaml` through the gate's approval
option. The approval binds the semantic subject, complete reference
denominator, tool identity, and every review-image hash.

Placement, model transform, model SHA, local-axis contract, intended edge,
board outline, keyed pad, checker identity, or evidence changes make approval
stale. Routing-only byte churn does not change the semantic subject.

## Debug one reference

Use the first failing channel; do not repeatedly rerender the whole design:

1. **Model/footprint axis failure:** inspect the manufacturer drawing and exact
   STEP frame, then correct the authored local vector or model transform.
2. **Board-axis/edge failure:** correct the source placement rotation or the
   intended `edge_faces` declaration. Do not rotate only the render.
3. **Mating-plane failure:** reconcile the footprint origin and manufacturer
   mating-plane dimension, then change placement or the evidenced range.
4. **Top box looks wrong:** inspect the footprint geometry/board projection;
   never replace it with a colour threshold or unconstrained pixel bbox.
5. **Outside/inside crop is wrong:** inspect the board-strip calibration and
   fixed camera mapping. Do not substitute a populated-minus-hidden bbox;
   removing an overhanging model can change KiCad's auto-fit camera.
6. **Body is on the wrong side of the PCB:** return to `P-MODEL-REG`; inspect
   the exact STEP frame, model rotation and Z offset, then rerun the signed-Z
   coupon and its deliberately inverted known-bad. Do not repair this by
   changing camera labels or footprint placement.

Preserve the failed receipt and focused images as diagnostics. A corrected run
must produce a new subject and new explicit human decision.
