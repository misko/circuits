# Fasteners and threaded inserts

Treat insert geometry as part-number-, material-, and printer-specific. Datasheet nominal dimensions seed a coupon; the coupon establishes the production hole.

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

## Print and qualify a coupon

Include `insert_coupon` in printable parts when insert validation is required. Print it with the same:

- material brand and condition;
- nozzle, layer height, extrusion width, and wall settings;
- orientation and local wall thickness;
- printer and slicer profile used for the enclosure.

Test at least the authored pilot diameter; bracket it with nearby diameters when machine/process variation is unknown. Record installation force or method, flange seating, boss splitting, spin-out, pull-out tendency, and screw fit.

Use the smallest hole that installs reliably without cracking or severe distortion. Update `enclosure.yaml`, regenerate all parts, and bind new physical evidence to the new semantic config hash.

## Assembly checks

- Deburr without enlarging the pocket unpredictably.
- Install inserts square to the screw axis.
- Confirm no insert or screw tip protrudes into PCB copper, components, or cables.
- Use washers or head recesses only when represented in the stack-up.
- Define a tightening method appropriate to printed plastic; avoid treating metal fastener torque tables as plastic-boss limits.
- Perform repeated assembly only if service cycling is part of the use case.
