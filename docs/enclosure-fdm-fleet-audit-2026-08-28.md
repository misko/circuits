# Enclosure FDM fleet audit — 2026-08-28

## Outcome

The repository now treats a printable mesh, a structurally screened enclosure,
and a physically qualified print as different claims. A connected, manifold
STL is necessary but does not prove that a screw lug is adequately attached,
that a slicer preserves the feature, or that the printed joint survives torque,
warpage, cable load, service cycles or heat.

This audit introduced a fail-closed local attachment-section screen and used it
to create successor enclosure candidates for the two fabricated boards:

- Pluto RX2 eight-way v5 enclosure `v0.8.0-2026-08-28`;
- USB Hub 3S v3 enclosure `v0.4.0-2026-08-28`.

Both successors remain `INCOMPLETE` and `order_ready=false`. They are printable
CAD candidates and evidence archives, not production-fit or strength claims.

## Role-aware fleet census

The pushed baseline contained 12 immutable enclosure releases and 48 declared
printable release payloads. Every one of those 48 meshes passed the existing
topology checks for exact census/hash, nonzero volume, connectivity, manifold
edges, consistent orientation and degeneracy. Six older Pluto schema-v1
releases cannot be reopened by the current schema-v2 verifier and are therefore
classified `LEGACY/INCOMPLETE`; their immutable bytes are not rewritten.

The two successors add eight declared printables, producing a 14-release,
56-printable fleet. The fleet audit deliberately excludes installed assemblies,
component witnesses, collision meshes, supplied reference models and other
verification STLs from the printable denominator. Those files are still
censused by their own manifests and evidence contracts.

## Failure that motivated the change

Pluto enclosure v0.7 removed the perimeter skirt but retained four circular
screw lugs largely outside the roof plate. The resulting lid remained a valid
single-component manifold mesh, yet the narrowest ideal-CAD roof-to-lug throat
was only about 2.47 mm through a 2.4 mm roof. Normal axial screw preload mostly
reacted directly into the case post, but roof twist, warped seating, lateral
handling and removal of a binding lid could peel that small root.

The USB first-article feedback exposed the companion service-envelope problem:
a nominal connector-body opening did not represent the mated termination,
heat-shrink, cable exit, bend, grip and reaction space. That observation
invalidates the old two-dimensional allowance as a complete assembly rule but
does not provide a new numeric tolerance.

## Implemented current-policy gate

New candidates bind a `pcb-enclosure-fdm-structural-contract-v1` and a
deterministic receipt. The contract closes:

- the exact printable-part and build-orientation census;
- process identity and the explicit slicer/toolpath evidence boundary;
- every represented load case and its inverse attachment references;
- every critical post, boss, lug, clip, rail or insert attachment;
- distinct arbitrary-plane root and member sections measured from the exact
  generated STL;
- minimum material area, net throat/span and reinforcement ratio; and
- tightly typed intentional-flexure exceptions linked to physical tests.

The release verifier also requires the FDM receipt, printable mesh evidence and
the explicitly selected exact collision receipt to bind one exact generation
record and installed-case mesh. A parent STEP may remain honestly incomplete;
a separately bound supplemental collision is not allowed to turn that parent
check into a false PASS.

The screen has a maximum claim of `CAD_READY`. With no pinned slicer/toolpath or
physical evidence, its overall result is `INCOMPLETE` even when every represented
local section passes.

## Successor geometry

### Pluto RX2 eight-way v5

The v0.8 roof uses full-height tangent load-transfer webs rather than circular
lugs touching the roof through narrow corner slivers. Exact STEP collision
limited the north pair to D12 roots; the south pair uses D14. The narrowest
measured lid root is approximately 90 mm2 with a 12 mm throat, compared with
about 5.9 mm2 of ideal throat section in v0.7. The post sleeves and screw bores
also receive larger candidate radial clearances. Connector-facing edges remain
open, but the fabricated board's intrinsic zero-overhang SMA faces and dense
15/18 mm pitch remain unsolved.

### USB Hub 3S v3

The v0.4 roof retains continuously open connector sides and replaces each local
closure ear with a D16 tapered inboard root feeding a D10.8 screw member. Its
exact generated mesh records a 57.6 mm2 root section, 18 mm net root throat and
2.44 root/member area ratio. Connector mate/unmate, cable pull/bend and hand/tool
reaction loads are routed through the PCB and all four independent PCB bosses.
The open roof is not credited as a connector or cable support. The retained
10.4 mm base shelf and all real connector/cable envelopes remain physical-test
questions.

## Remaining qualification work

Neither successor is yet FDM-qualified. Before promotion, bind and inspect an
exact printer/material/nozzle/layer/slicer profile and toolpath; add automated
self-intersection and whole-mesh local-thickness checks; disposition global
roof/vent-ligament torsion; then print the exact-process coupons and cases.
Physical evidence must cover insert fit, maximum declared screw torque, joint
deflection, warped-seat behavior, repeated lid service, PCB retention,
simultaneous connector operation, cable loads and thermal soak.

Forward work is tracked in [IMP-192](../improvements.md#imp-192--separate-local-attachment-screening-from-whole-part-fdm-qualification).
