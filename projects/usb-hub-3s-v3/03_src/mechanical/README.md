# USB Hub 3S v3 v1.12 roof-only enclosure candidate

This is the mutable enclosure authority for the fabricated PCB release
`v1.12-2026-07-28`. The candidate is intentionally **INCOMPLETE**. It removes
the wall-lid feature implicated by the received XT60 fit observation without
inventing dimensions for the unknown mate, rear termination, heat-shrink,
cable, bend, grip, tool, or service operation.

The immutable PCB release and the existing enclosure releases remain inputs.
They are not edited or resealed by this candidate.

## Topology and load paths

The three printable parts remain:

- a floor-down foundation with four H1-H4 PCB bosses and four separate case
  posts;
- a roof-down lid with no vertical skirts or side walls; and
- the D4.05-D4.45 insert-fit coupon centred on the D4.25 transferred prior.

The PCB is retained by four M3 screws before the roof is installed. Four
different top-down M3 screws close the roof at the corner posts. Removing the
roof and every case screw does not loosen the PCB.

The roof bottom remains at Z=27.0 mm, preserving the predecessor's interior
height. Thickness grows upward from 2.4 to 3.2 mm. Its main plate stops at the
exact 130 x 92 mm PCB outline, rather than retaining the predecessor shell's
10.4 mm per-side roof overhang. Four tapered closure ears reach the posts at
(+/-70, +/-51) mm. Each ear grows from a D16 inboard root pad into a D10.8
screw member; the generated mesh measures a 57.60 mm^2 root section with an
18.00 mm net throat, a 23.56 mm^2 drilled/recessed member section with 8.33 mm
net material, and a 2.44 root/member section ratio. The D10.8 member leaves a
2.25 mm radial bearing land around the D6.3 head and a 7.3 mm through-ligament
around the D3.5 bore. The narrowest conservative legacy connector-opening
corridor is 4.1 mm.

That 4.1 mm assertion is only a check against the old two-dimensional opening
candidates. It is not a complete connector-service clearance. The design makes
the narrower claim that there is no vertical skirt barrier along the declared
J1-J5 mating axes. The roof edge, local lugs, posts, screw heads, and base floor
remain obstacles until complete received connector/cable/tool solids and their
operations are swept. The preserved 150.8 x 112.8 mm base floor projects
**10.4 mm outboard of every exact PCB edge**. An XT60 under-grip finger path,
rear termination, or cable that bends downward can still encounter that shelf;
the roof-only change does not prove the whole service cell unobstructed.

The 3.2/2.4 thickness ratio gives a 2.37x simple thickness-cubed plate-bending
candidate before vents and local geometry. This is not print evidence. Flatness,
handling flex, fastened sag, and component clearance require a first article.

## FDM and structural audit boundary

`fdm-structural-contract.yaml` closes the three-part printable census and
declares 17 critical attachments: H1-H4 PCB bosses, C1-C4 base posts, four lid
ears, and five insert-coupon bosses. The shared auditor slices the exact
generated meshes at 34 distinct root/member planes and grades 85 area, throat,
and reinforcement assertions. Nine closed load cases reach those attachments:
PCB clamp/service, west/east and south connector mate/unmate, cable pull/bend,
hand/tool reaction, closure preload, detached-lid handling, fastened/binding
closure-joint lateral service, and coupon pressing.
Connector loads are reacted through the PCB and all four H1-H4 bosses; the open
roof is never credited as a connector or cable support. The current structural
local attachment-section screen passes.

That is not a strength or print qualification. Mesh self-intersection and
whole-part local thickness are not yet automated; no printer build volume,
pinned slicer/profile, toolpath, bridge/support result, material strength, or
global roof torsion/stiffness result or physical torque/load cycle is bound.
The manufacturing receipt and every
affected scope therefore remain `INCOMPLETE` even with a structural screen
PASS. The required first article must include the declared closure-joint
torque/twist/service-cycle test.

## Connector-assembly authority

`../rules/connector_assemblies.yaml` is now the one project connector/service
fact lock. It covers 7 profiles, 12 interface refs, and 5 simultaneous groups:

- J1 XT60 input;
- J2-J4 USB-A outputs;
- J5 USB-C output;
- F1 fuse service;
- SW1 switch service; and
- D8-D12 indicator viewing apertures.

The compiled receipt is valid but `INCOMPLETE`: all 77 required evidence
claims remain explicitly unknown. The dated XT60 photograph rejects the old
skirt assumption but contributes no millimetre value. Schema v2 maps every one
of the 12 `opening` or `service_opening` interfaces to that exact receipt and
accounts for every receipt ref; nothing is hidden through a non-enclosure
disposition.

The current composition does not instantiate or sweep complete mate,
termination, cable, bend, grip, tool, and reaction solids. Connector access
therefore stays `INCOMPLETE` even though the roof has no skirts.

## Exact PCB and obstruction evidence

The v1 CAD design binds these immutable PCB authorities:

- manifest SHA-256 `2d6192ebbd5755920d3b2099574455339ab02ba4a4cd3b56905a86ac2ba33ef4`;
- PCB SHA-256 `2eb04b6b7e526d6fe30c2b3bab399558dc5c34c4c4e254dac6a4d9ffd71125bf`;
- STEP SHA-256 `e4c9a9957692a251eff85e058522e2e402ca2b7dea7eb3a532fd4350e7ce6e11`;
  and
- deterministic interface SHA-256
  `36e6d236be966f188d18906afcd2b0b3acf0a27dd536a96fb65e923365b7448b`.

The sealed STEP omits modeled F2, J1-J5, Q1-Q6, and U3-U5; SW1 has no model.
The generic parent inspection therefore truthfully fails at 106/121 modeled
refs plus unmodeled SW1. The bound project compositor adds the reviewed
supplemental bodies without changing the PCB release. The composite covers
121/121 modeled refs plus SW1, 244 component solids, and its exact installed
case intersection is empty at 0 mm^3.

That result proves non-penetration only for the represented final installed
pose. It does not prove connector mating, cable motion, roof installation over
received leads, board support contact, print fit, ingress/touch protection, or
thermal performance.

## Source and disposable build

Authored source:

- `usb_hub_3s_v3_case.scad` - roof-only CAD, closed selectors, and analytic
  roof/lug/vent assertions;
- `enclosure.yaml` - exact schema-v1 generation binding;
- `mechanical-intent-v2.yaml` - service states, four linear motions, unknowns,
  and excluded claims;
- `enclosure-v2.yaml` - exact receipt mappings, scopes, independent fasteners,
  clearance cases, and physical-test census; and
- `fdm-structural-contract.yaml` - exact printable/process/load/attachment and
  mesh-section threshold census; and
- `reference/` plus the two obstruction scripts - exact board interface and
  supplemental obstruction authority.

Regenerate into:

```text
projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12-reinforced-roof-v4/
```

Important outputs are `base.stl`, `lid.stl`, `insert_coupon.stl`,
`assembled-case.stl`, four review renders, generation/validation receipts,
the composite STEP/mesh, and the exact collision report. These build outputs
are disposable and ignored. The hash-bound printable STLs, renders, source,
connector replay closure, and evidence are tracked in immutable candidate
`07_enclosure_releases/v0.4.0-2026-08-28/`; its overall status and every scope
remain `INCOMPLETE`.

## Exact regeneration

Run from the repository root. Compile the canonical shared connector receipt
before schema-v2 validation; exit 2 is the expected honest `INCOMPLETE` result.

```sh
project_path=projects/usb-hub-3s-v3
build_path="$project_path/06_build/mechanical/usb-hub-v1.12-reinforced-roof-v4"
mkdir -p "$build_path"

/usr/bin/python3 skills/pcb-design/scripts/connector_assembly_contract.py \
  --project "$project_path"
test "$?" -eq 2

/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-intent "$project_path/03_src/mechanical/mechanical-intent-v2.yaml" \
  --output "$build_path/mechanical-intent-validation-v2.json"

/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  "$project_path/03_src/mechanical/enclosure.yaml" --root "$project_path" \
  --build-dir "$build_path"

/usr/bin/python3 skills/pcb-enclosure/scripts/fdm_structural_audit.py \
  "$project_path/03_src/mechanical/fdm-structural-contract.yaml" \
  --config "$project_path/03_src/mechanical/enclosure.yaml" \
  --root "$project_path" --generation "$build_path/generation.json" \
  --mesh base="$build_path/base.stl" \
  --mesh lid="$build_path/lid.stl" \
  --mesh insert_coupon="$build_path/insert_coupon.stl" \
  --output "$build_path/fdm-audit.json"
test "$?" -eq 2

```

Reproduce the exact interface authority:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/extract_board_interface.py \
  "$project_path/07_releases/v1.12-2026-07-28/source/usb_hub_3s_v2.kicad_pcb" \
  -o "$build_path/board-interface.json" \
  --access-ref J1 --access-ref J2 --access-ref J3 --access-ref J4 \
  --access-ref J5 --access-ref F1 --access-ref F2 --access-ref SW1 \
  --access-ref D8 --access-ref D9 --access-ref D10 --access-ref D11 \
  --access-ref D12

cmp "$build_path/board-interface.json" \
  "$project_path/03_src/mechanical/reference/board-interface-v1.12.json"
```

The parent STEP inspection is expected to fail closed:

```sh
uv run --offline --with cadquery==2.8.0 python -B \
  skills/pcb-enclosure/scripts/inspect_step.py \
  "$project_path/07_releases/v1.12-2026-07-28/3d/usb_hub_3s_v2.step" \
  --interface "$project_path/03_src/mechanical/reference/board-interface-v1.12.json" \
  --output "$build_path/step-inspection.json" \
  --component-mesh "$build_path/components.stl"
test "$?" -eq 1
```

Then reproduce the reviewed composite and final-pose collision:

```sh
/usr/bin/python3 "$project_path/03_src/mechanical/prepare_obstruction_step.py" \
  --project-root "$project_path" \
  --manifest "$project_path/03_src/mechanical/reference/obstruction-models.json" \
  --output-dir "$build_path"

uv run --offline --with cadquery==2.8.0 python -B \
  "$project_path/03_src/mechanical/compose_obstruction_step.py" \
  --parent-step "$project_path/07_releases/v1.12-2026-07-28/3d/usb_hub_3s_v2.step" \
  --supplement-step "$build_path/supplemental-obstructions.step" \
  --interface "$build_path/board-interface.json" \
  --augmentation-receipt "$build_path/obstruction-augmentation.json" \
  --output-step "$build_path/composite-obstructions.step" \
  --component-mesh "$build_path/composite-components.stl" \
  --report "$build_path/composite-step-inspection.json"

/usr/bin/python3 -B \
  "$project_path/03_src/mechanical/compose_obstruction_step.py" \
  --replay-receipt "$build_path/composite-step-inspection.json"

uv run --offline --with cadquery==2.8.0 python -B \
  skills/pcb-enclosure/scripts/build_collision.py \
  --step "$build_path/composite-obstructions.step" \
  --step-inspection "$build_path/composite-step-inspection.json" \
  --component-mesh "$build_path/composite-components.stl" \
  --interface "$build_path/board-interface.json" \
  --generation "$build_path/generation.json" \
  --assembled-case-mesh "$build_path/assembled-case.stl" \
  --board-bottom-z-mm 9.5 \
  --output "$build_path/composite-clearance-intersection.stl" \
  --report "$build_path/composite-collision.json"

/usr/bin/python3 -B skills/pcb-enclosure/scripts/build_collision.py \
  --replay-receipt "$build_path/composite-collision.json"

/usr/bin/python3 -B skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-config "$project_path/03_src/mechanical/enclosure-v2.yaml" \
  --root "$project_path" --output "$build_path/v2-validation.json"
```

The authored enclosure generation and FDM receipt are deterministic byte
replays. The supplemental obstruction path has a different boundary: KiCad
and CadQuery may serialize an equivalent STEP with different bytes. The
composition receipt therefore byte-binds the selected composite STEP used by
the collision audit, then replays in a private directory with pinned
CadQuery 2.8.0 through the shared bounded runtime. Replay requires exact
validator/helper/input identities, 121/121 modeled references plus SW1, exact
parent/supplement/PCB/component solid selection, a quantized per-solid geometry
signature, and a byte-exact 244-solid component mesh. It deliberately does not
claim that a freshly serialized composite STEP has the same bytes. The collision
receipt separately replays against the exact selected STEP and must report
`COMPLETE`, `EMPTY`, and exactly `0 mm3`. Do not claim byte identity for the
regenerated supplemental STEP or its augmentation receipt.

## Physical qualification plan

1. Print the D4.05-D4.45 coupon in the production PETG profile and qualify the
   exact E-Z LOK insert lot before printing the full base.
2. Retain the PCB on H1-H4. Prove all four intended boss faces seat
   simultaneously and no connector, solder tail, component, floor edge, or
   case post carries the board.
3. Measure and bind each actual J1-J5 receptacle/mate/termination/cable service
   assembly, including grip, straight run, bend, tool, reaction path, and
   simultaneous neighbor state.
4. Mate J1-J5 simultaneously, then execute the complete 40 mm roof install and
   removal path. Inspect the roof edge, all four local lugs/posts/screws, the
   10.4 mm base-floor shelf, under-grip finger paths, downward cable bends, and
   strain reliefs for contact or chafe.
5. Exercise F1 and SW1 and verify all five indicator apertures in the installed
   state.
6. Measure roof flatness, warp, handling flex, and fastened sag relative to the
   populated board.
7. Remove only the four case screws and roof; prove the PCB remains secured.
8. Run the declared roof-covered, open-sided thermal soak after electrical
   load qualification.

Until those checks and the missing exact service geometry are recorded, this
candidate is not `CAD_READY`, `PRINT_VERIFIED`, `THERMALLY_VERIFIED`,
order-ready, or a production-fit claim.
