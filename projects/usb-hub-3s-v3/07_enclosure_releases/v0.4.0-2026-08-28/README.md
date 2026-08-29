# USB Hub 3S v3 enclosure v0.4.0

Overall and every published scope: **INCOMPLETE**

Immutable PCB basis: **v1.12-2026-07-28**

Enclosure predecessor: **v0.3.0-2026-08-27**

This immutable successor reinforces all four roof-to-screw joints while
preserving the predecessor's open connector topology. The main roof remains
exactly 130 x 92 x 3.2 mm, with no continuous skirt or side wall. Each corner
now transitions from a D16 inboard root pad to a D10.8 screw member through a
wide tapered ear; the prior base, PCB-support stack, case posts, insert pocket,
and connector-edge planes remain unchanged.

The generated lid measures 57.60 mm2 at each declared ear root with an
18.00 mm net throat. At the drilled and head-recessed member it measures
23.56 mm2 and 8.33 mm net material. The root/member section ratio is 2.44.
The D10.8 member leaves 2.25 mm radial bearing land around the D6.3 screw head
and a 7.3 mm through-ligament around the D3.5 clearance bore. The conservative
legacy connector-opening corridor remains at least 4.1 mm.

Those are CAD section measurements, not connector-clearance, FDM-strength, or
physical-life claims. Exact mated plugs, rear terminations, cables, bends,
hand grips, tools, and service operations remain unknown. The 150.8 x 112.8 mm
base still leaves a 10.4 mm shelf beyond each PCB edge and may obstruct an
XT60 downward bend or under-grip.

## Printable files

- `meshes/base.stl` — preserved floor-down base with four PCB bosses and four
  independent case-closure posts;
- `meshes/lid.stl` — reinforced roof-only plate with four tapered closure
  ears; and
- `meshes/insert_coupon.stl` — preserved D4.05-D4.45 insert-fit ladder.

The PCB remains secured by four M3 x 6 screws on H1-H4. Four separate M3 x 6
screws fasten the roof. Removing every case screw and the complete roof cannot
release the PCB.

## Automated evidence

- the connector-assembly receipt covers 7 profiles and all 12 enclosure refs,
  but records 0/77 required service facts known and remains `INCOMPLETE`;
- generation completes for all 3 printables and the installed-case selector;
- the structural contract closes 17 attachment joints and its exact mesh
  screen passes 85/85 area, throat, and reinforcement assertions across nine
  referenced load cases, including connector mate/unmate, cable pull/bend,
  hand/tool reaction, closure preload, lid handling, and coupon pressing;
- topology is one closed, consistently oriented, edge-manifold component per
  printable, while self-intersection and whole-part local thickness remain
  explicitly unimplemented; the mesh PASS is a local attachment-section screen,
  not a global roof-torsion or strength result;
- the sealed STEP honestly remains incomplete at 106/121 modeled refs with
  SW1 unmodeled;
- the parent-plus-supplement subject covers 121/121 modeled refs plus SW1 with
  244 component solids; its selected composite STEP is byte-bound and an
  independent pinned CadQuery 2.8.0 replay reproduces the exact input/tool
  identities, solid selection, semantic geometry signature, and component-mesh
  bytes without claiming STEP-serializer byte identity; and
- exact installed-case collision against that composition is `EMPTY`, exactly
  **0 mm3**.

The renders are visual-review evidence only.

## Why status remains INCOMPLETE

No canonical printer/build-volume or pinned slicer/profile/toolpath is bound,
so bridge, overhang, support, dropped-thin-feature, perimeter, and first-layer
behavior are not graded. There is also no physical insert, board seating,
closure-independence, torque/twist/load, roof flatness/warp, repeated service,
all-ports-mated, cable-strain, or thermal evidence. Open sides waive ingress
and touch-protection claims.

Before promotion:

1. Slice all three exact meshes with a pinned printer/material/profile and
   inspect every layer without repair, rescaling, auto-orientation, or hidden
   support changes.
2. Print the insert coupon and qualify the exact insert lot and PETG process.
3. Torque and repeatedly service all four closure joints; record twist,
   deflection, crack, creep, and warped-seat behavior.
4. Mate XT60, three USB-A, and USB-C leads simultaneously; exercise roof
   install/removal and inspect the retained base shelf.
5. Verify PCB seating on H1-H4 and lid-off retention, then run the declared
   roof-covered thermal soak.

This release is not `CAD_READY`, `PRINT_VERIFIED`, `THERMALLY_VERIFIED`,
order-ready, or a production-fit claim.

## Release-root replay

The release-local closure includes exact PCB authorities, connector evidence,
CAD source, obstruction models, generation/collision receipts, the FDM
contract and receipt, and the exact FDM compiler plus schema helper. Replay
must recompile both connector and FDM receipts byte-for-byte and regenerate
every printable byte-for-byte. It must also reproduce the expected sealed-STEP
limitation, rebuild and regrade the supplemental subject by its exact bound
reference/solid census, independently rerun the exact STEP solid classifier
and reproduce its component mesh, generate a collision receipt bound to the
same exact generation and installed-case mesh, reproduce
`COMPLETE`/`EMPTY`/`0 mm3`, and
reopen the complete payload census without creating cache files. KiCad and
CadQuery STEP serialization and augmentation-receipt execution paths are not
claimed byte-stable; their replay is geometry/census graded, not `cmp` graded.

From the staged release root, the project-specific compositor and the exact
collision builder are independently replayed with:

```sh
/usr/bin/python3 -B tooling/compose_obstruction_step.py \
  --replay-receipt verification/composite-step-inspection.json
/usr/bin/python3 -B tooling/build_collision.py \
  --replay-receipt verification/composite-collision.json
```

Nothing in the immutable PCB release or any predecessor enclosure is edited.
