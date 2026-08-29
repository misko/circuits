# FDM and structural audit contract

Use the deterministic audit for every new enclosure candidate. It is a CAD
manufacturability screen, not a strength calculation or print qualification.
Copy `assets/fdm-structural-contract.template.yaml`, replace every example,
and keep the contract beside mutable mechanical source.

## Close every census

The contract repeats the exact schema-v1 printable selector census. Each part
binds one process profile and one proper rigid `mesh_to_build` transform. Its
upper 3-by-3 matrix must be orthonormal with determinant +1; scale, shear, and
reflection are forbidden because they can inflate measured sections. The
transformed mesh must remain at or above build Z=0 and touch the plate.

Set each part to:

- `audited` with a nonempty exact attachment-ID census; or
- `no_critical_attachment` with an empty census and a nonempty reason.

The union of per-part attachment IDs must exactly equal the global attachment
census. Load cases, process profiles, structural probes, support exceptions,
and intentional-flexure exceptions also have nonzero or exact denominators.

## Audit the complete load chain

Name loads from enclosure use, not only from the fastening diagram. Include
connector insertion/removal and tool reaction, cable pull and bending moment,
closure-screw tightening or preload, uneven lid handling/twist, accessory
operation, and any declared impact or service cycle. Trace each load from its
application through named members to a support; do not let a connector body,
solder tail, PCB edge, or enclosure opening become an accidental reaction.
The v1 mesh implementation verifies only the named local attachment sections;
it does not solve whole-plate bending, torsion, distributed stress, or material
strength. Keep those global paths explicit in prose and physical tests, and do
not describe a local section PASS as a complete enclosure load-path PASS.

For every screw/insert chain, review the screw-head bearing land, residual
material beneath the head recess, clearance sleeve or post wall, threaded
engagement, screw-tip clearance, post/boss body, and its root into the parent
plate. Passing insert radial-wall arithmetic cannot substitute for the
post-to-roof or post-to-floor root measurement.

Treat walls, skirts, lips, and perimeter rails as possible structural members.
Removing or opening one triggers a new torsion and load-path audit of every
affected closure, root, connector reaction, and board support, even if all
remaining meshes are manifold and collision-free.

## Probe mesh-visible critical sections

Each critical attachment names its printable part, required schema-v2 scope,
host, member, function, and one or more load cases. Supply at least two
distinct section probes: a host/root section and a member section.

A section plane has a 3-D origin, unit normal, orthogonal unit `u_axis`, and a
bounded UV region. The auditor intersects that plane with the exact generated
STL, stitches closed contours, applies even/odd hole semantics, clips them to
the region, and computes net material area. Its named throat line computes
total/net material span within a bounded interval. It is not a generic local
minimum-thickness result.

Root and member probes must use different IDs and resolve different geometry.
For parallel or antiparallel planes, they must belong to one registered plane
family: their in-plane axes align, their origins have no tangential offset,
and their signed separation along the common normal is at least
`max(layer_mm, nozzle_mm / 2)`. A translation within the same geometric plane
therefore cannot impersonate a second section. Nonparallel plane normals must
differ by at least 30 degrees; this admits the intentional perpendicular
host/root and member sections used by many bosses while rejecting a tiny tilt
through one tapered member.

Plane independence alone is not material independence. The exact-mesh results
must also change by at least one deposited-road cross-section,
`nozzle_mm * layer_mm`, in net area, or by one linear process increment,
`max(layer_mm, nozzle_mm / 2)`, in throat span. Smaller area *and* span changes
are a sub-process taper and fail because the attachment-to-host transition
remains unmeasured. A reinforcement row names the required root/member area
ratio and one reviewed form: `fillet`, `gusset`, `rib`, `blended_tab`, or
`continuous_section`.
`none` fails unless the attachment carries a typed intentional-flexure
exception. Thresholds remain authored engineering requirements; a passing
section is not a force, fatigue, or material-strength result.

Final union meshes do not preserve a bonded construction interface. Use
`overlap.disposition: section_proved` when the critical section is the relevant
load-transfer witness. Otherwise use `not_separately_observable` with an honest
reason; never invent an overlap footprint from the union STL.

## Bind exceptions and evidence boundaries

The only exception type is `intentional_flexure`. It requires a rationale,
hard motion stop, exact attachment cross-link, and a named schema-v2 physical
test required for `PRINT_VERIFIED` in the same scope. The v2 validator rejects
missing, optional-scope, or wrong-readiness tests.

Process profiles exactly repeat schema-v1 material, nozzle, layer, minimum
wall, and support policy. The first adapter accepts only `slicer: null` because
no canonical slicer/profile/toolpath replay exists yet. Consequently it
reports slicer, overhang, support, bridge, unsupported-island, printer build
volume, self-intersection, and local-thickness checks as `INCOMPLETE`, never
implicit `PASS`.

The receipt separates mesh topology, orientation/process contract,
mesh-visible structural load-path screen, slicer/toolpath evidence, and the
physical-evidence boundary. Its maximum claim is `CAD_READY` and
`physical_evidence_consumed` is false. Missing physical proof alone does not
lower a future complete CAD audit, but `PRINT_VERIFIED` remains governed by
schema-v2 physical evidence.

## Run and publish

```bash
/usr/bin/python3 skills/pcb-enclosure/scripts/fdm_structural_audit.py \
  "$PROJECT/03_src/mechanical/fdm-structural-contract.yaml" \
  --config "$PROJECT/03_src/mechanical/enclosure-cad-design-v2.yaml" \
  --root "$PROJECT" \
  --generation "$BUILD/generation.json" \
  --mesh base="$BUILD/base.stl" \
  --mesh lid="$BUILD/lid.stl" \
  --mesh insert_coupon="$BUILD/insert_coupon.stl" \
  --output "$BUILD/fdm-audit.json"
```

Pass one `--mesh PART=PATH` for every declared printable. Exit 1 is `FAIL`, 2
is `INCOMPLETE`, and 0 is `CAD_READY`. The tool validates the strict v1 config
from the same stable bytes, reopens every exact subject/source binding, writes
through a held parent directory descriptor, verifies published bytes/inode,
and performs a fresh post-publication regrade.

Schema v2 binds the contract, receipt, generation, governing exact collision,
typed collision subject, and exact per-part meshes under optional
`manufacturing_audit`. Omission is legacy-compatible but caps
required scopes at `INCOMPLETE`. An immutable successor also carries exact
replay roles `fdm_structural_audit=tooling/fdm_structural_audit.py` and
`enclosure_common=tooling/enclosure_common.py`, plus exact collision builder,
STEP inspector, generator, process runner, and pipeline runtime roles; stage
and reopen regrade them all.
Never edit predecessor releases to adopt this policy.
