# Fasteners and threaded inserts

Treat insert geometry as part-number-, material-, and printer-specific. Datasheet nominal dimensions seed a coupon; the coupon establishes the production hole.

## Contents

- [Capture the hardware](#capture-the-hardware)
- [Model the insert pocket](#model-the-insert-pocket)
- [Select the strategy](#select-the-strategy)
- [Schema-v2 role groups](#schema-v2-role-groups)
- [Print and qualify a coupon](#print-and-qualify-a-coupon)
- [Assembly checks](#assembly-checks)

## Capture the hardware

Record the exact thread, insert family, installation method, body diameter, flange diameter, length, and manufacturer-recommended hole. Also measure screw head and clearance diameters, head height/recess, available lengths, and required engagement.

Do not substitute a similarly named M3 insert without revisiting every pocket and screw-stack dimension.

## Model the insert pocket

Provide:

- pilot-hole diameter;
- flange-recess diameter and depth;
- insert length;
- closed-end bottom clearance;
- boss diameter and required minimum radial wall.

The verifier computes radial wall from the largest pilot/recess diameter. It also checks that the board insert pocket remains above the interior floor plane. These are validation dimensions; inspect local wall intersections and print direction visually too.

For flanged cold-press inserts, install from the designed access face and seat the flange in its recess. Avoid a blind pocket that traps displaced plastic. For heat-set inserts, preserve tool access and protect nearby walls from the iron tip.

## Select the strategy

`shared_board` uses PCB mounting locations for shell closure. Verify the complete lid-to-insert distance, minimum engagement, tip clearance, board compression, and column-to-board gap.

`separate_perimeter` independently mounts the board and closes the case. Verify board-screw engagement and case-screw engagement separately. Ensure perimeter posts do not shadow connectors, mounting hardware, or the board insertion path.

Never infer that a longer screw is safer: it can bottom in the insert before clamping. Never infer that a short screw is harmless: insufficient engagement can pull threads or inserts out.

## Schema-v2 role groups

For new schema-v2 work, replace the single strategy flag with explicit
fastener groups. `board_retention` retains the PCB to the base and must not
retain the lid. `case_closure` retains the lid to the base and must not retain
the PCB. Optional `accessory` groups retain an installed accessory to a base or
lid structural part.

Give every group its actual 3-D screw axes, retained members, thread, screw
length, minimum engagement, and minimum tip clearance. Board-retention and
case-closure axes must be disjoint. A visually separate boss is not sufficient
if its screw line still passes through the PCB mounting hole.

Treat every boss/post-to-floor, boss/post-to-roof, and local screw-seat
transition that carries closure or retention load as a critical attachment in
the FDM/structural contract. Measure independent root and member sections and
declare the overlap plus a real fillet or gusset witness. A large roof or floor
plane sampled twice is not independent root evidence, and a shallow circular
lug merely touching a skin must fail the screen even when the combined STL is
manifold.

The complete screw load chain is: head bearing land, residual thickness below
any head recess, clearance sleeve/post wall, threaded engagement, tip
clearance, post or boss body, and the root into its parent plate. Audit every
link under tightening/preload and external reaction loads. Connector mating,
hand-tool torque, cable pull/bend, or lid twist can govern a closure root even
when the screw stack itself is dimensionally valid. Removing a skirt, sidewall,
lip, or rail requires a fresh torsion/load-path audit; those features may have
been carrying load even when they were not named as fasteners.

Schema v2 requires `pcb_retained_with_lid_removed: true`. Mechanical intent
must include a lid-removed state with all board-retention groups still secured
and all case-closure groups released. Require the typed physical tests
`lid_off_pcb_retention` and `case_closure_independence` before claiming
`PRINT_VERIFIED`.

Declare the PCB's intended bearing surfaces separately from its fasteners.
Perimeter walls, panel rails, and closure posts must not become accidental
standoffs through an edge connector, component body, lead, or solder tail.
CAD collision can catch penetration but cannot prove simultaneous seating or
load sharing. Add a `board_support_clearance` physical test whenever an
alternate bearing path is plausible.

## Print and qualify a coupon

Include `insert_coupon` in printable parts when insert validation is required. Print it with the same:

- material brand and condition;
- nozzle, layer height, extrusion width, and wall settings;
- orientation and local wall thickness;
- printer and slicer profile used for the enclosure.

Test at least the authored pilot diameter; bracket it with nearby diameters when machine/process variation is unknown. Record installation force or method, flange seating, boss splitting, spin-out, pull-out tendency, and screw fit.

Use the smallest hole that installs reliably without cracking or severe distortion. Update `enclosure.yaml`, regenerate all parts, and bind new physical evidence to the new semantic config hash.

If printer undersizing makes the selected modeled pilot equal to or larger than
the insert's nominal body diameter, declare
`pilot_basis: coupon_qualified`. Do not falsify the hardware body dimension or
relabel a cold-press insert as heat-set merely to satisfy nominal interference
arithmetic. Coupon qualification records why the CAD value is credible; it
does not replace the physical-evidence receipt required for status promotion.

When a comparable observation from the repository-wide fit registry is used
only to centre a new design's coupon, declare `pilot_basis: coupon_prior`
instead. Preserve the source observation, keep `insert_coupon_required: true`,
and do not call the transferred value qualified until this design's production
geometry and process have been tested.

## Assembly checks

- Deburr without enlarging the pocket unpredictably.
- Install inserts square to the screw axis.
- Confirm no insert or screw tip protrudes into PCB copper, components, or cables.
- Use washers or head recesses only when represented in the stack-up.
- Define a tightening method appropriate to printed plastic; avoid treating metal fastener torque tables as plastic-boss limits.
- Perform repeated assembly only if service cycling is part of the use case.
