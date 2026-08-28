# USB Hub 3S v3 enclosure v0.3.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v1.12-2026-07-28**

Enclosure predecessor: **v0.2.0-2026-08-27**

This immutable candidate replaces the predecessor's four-skirt lid with a
3.2 mm roof plate. The main roof is exactly 130 x 92 mm, matching the PCB
outline, so it adds no board-edge overhang. Four localized diagonal lugs reach
the independent case-closure posts outside the connector corridors. There is
no vertical skirt barrier along the declared J1-J5 mating axes.

That bounded geometry claim is not a connector-clearance claim. The exact
mated-plug, overmold, rear termination, heat-shrink, cable, bend, hand-grip,
tool, and install/removal envelopes remain unknown. The preserved base is
150.8 x 112.8 mm, leaving a 10.4 mm floor shelf outboard of every PCB edge;
that shelf may still obstruct the XT60's downward bend, under-grip, cable, or
removal sweep.

## Printable files

- `meshes/base.stl` — preserved floor-down base with four PCB bosses and four
  independent case-closure posts;
- `meshes/lid.stl` — roof-only plate with localized corner closure lugs; and
- `meshes/insert_coupon.stl` — preserved D4.05-D4.45 insert-fit ladder.

The PCB remains secured by four M3 x 6 screws on H1-H4. Four separate M3 x 6
screws fasten the roof to the perimeter posts. Removing every case screw and
the complete roof cannot release the PCB.

## Automated evidence

- the connector-assembly receipt covers 7 assembly profiles and all 12
  enclosure-relevant refs, but records 0/77 required service facts known and
  therefore remains `INCOMPLETE`;
- generation completes for all 3 declared printable parts and the installed
  case selector;
- every printable is a closed, consistently oriented, edge-manifold mesh;
- the sealed PCB STEP honestly remains incomplete at 106/121 modeled refs,
  with SW1 unmodeled;
- the reviewed parent-plus-supplement composition covers 121/121 modeled refs
  plus SW1 with 244 component solids; and
- exact installed-case collision against that composition is `EMPTY`, exactly
  **0 mm3**.

The renders show roof topology and independent retention. They do not prove
real connector, plug, cable, grip, tool, or simultaneous-mating clearance.

## Why status remains INCOMPLETE

Open sides remove the predecessor's printed skirt constraint, but unknown
service envelopes and the retained base-floor shelf prevent a connector-fit
claim. No physical insert, board seating, closure-independence, roof
flatness/flex/warp, repeated service-cycle, all-ports-mated, cable-strain, or
thermal-soak evidence exists. Open sides also waive ingress- and touch-
protection claims and change airflow relative to the predecessor.

Before promotion:

1. Measure and bind every real connector body, mated plug/overmold, rear
   termination, cable OD, straight run, exit vector, bend radius, tool/grip
   envelope, install sweep, process allowance, and assembly allowance.
2. Mate the XT60, three USB-A plugs, and USB-C plug simultaneously; test roof
   installation/removal and explicitly inspect the 10.4 mm base shelf at the
   XT60 downward bend and under-grip.
3. Verify PCB seating on all four H1-H4 faces and retention with the roof and
   all case screws removed.
4. Qualify the insert coupon and test roof flatness, handling flex, fastened
   sag/warp, and repeated service cycles with the exact print process.
5. Run the declared roof-covered, open-sided thermal soak after electrical
   load qualification.

This release is not `CAD_READY`, `PRINT_VERIFIED`, `THERMALLY_VERIFIED`,
order-ready, or a production-fit claim.

## Release-root replay

The release-local configuration binds only files inside this tree: copied PCB
authority, connector contract and evidence closure, CAD source, obstruction
models, verification evidence, and replay-tool import closure. Replay must
recompile the connector receipt byte-for-byte, regenerate all printable
meshes, reproduce the expected sealed-STEP limitation, recompose the exact
supplemental subject, reproduce the 0 mm3 collision, and reopen the full
payload census.

Nothing in the immutable PCB release or v0.2 enclosure predecessor is edited.
