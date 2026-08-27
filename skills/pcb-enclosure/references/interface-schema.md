# Interface and schema-v1 CAD configuration

This reference defines the exact schema-v1 CAD adapter consumed by
`generate_enclosure.py`, `verify_enclosure.py`, and `package_enclosure.py`.
Use version 1 exactly for that file. New commissioned work also needs the
additive schema-v2 composition in `configuration-schema-v2.md`; v2 binds this
v1 file as `subject.cad_design` and rejects different subject identities. It
does not replace or silently translate the stable geometry contract.

The v1 strict loader rejects duplicate YAML keys, unknown fields, omitted
fields, unsafe paths, hash/size mismatches, and stale interface bindings.

## Contents

- [Subject binding](#subject-binding)
- [Extracted interface frame](#extracted-interface-frame)
- [Process and CAD](#process-and-cad)
- [Geometry](#geometry)
- [Fasteners](#fasteners)
- [Interfaces and thermal intent](#interfaces-and-thermal-intent)

## Subject binding

Set `schema: 1`, `kind: pcb-enclosure-config-v1`, a unique `name`, and `mode: co_design|derived`.

Under `subject`, provide:

- `release`: immutable release or design-snapshot identifier.
- `pcb`, `step`, `interface`: mappings with `path`, lowercase 64-hex `sha256`, and positive integer `size`.
- Paths relative to the explicit `--root`; no absolute paths, symlinks, traversal, backslashes, `.` segments, or `..` segments.

The interface JSON must declare `kind: pcb-enclosure-interface-v1`. Its PCB hash must equal the configured PCB hash.

## Extracted interface frame

The extractor emits millimetres in a centered case frame:

- origin: `outline_bbox_center`
- z zero: `pcb_back_surface`
- positive z: `front`
- `board_to_case`: explicit 4-by-4 transform

It records exact outline contours and bounding box, board thickness, drills, mounting holes, all footprints, model-declared flags, access candidates, and nonzero coverage denominators.

Extraction preserves arbitrary contours, but the built-in v1 OpenSCAD generator consumes only a single axis-aligned rectangle and rejects every other contour. The bounding box is not permission to approximate an irregular PCB.

Run extraction with repeatable `--access-ref REF`. Conservative default prefixes help discovery but do not replace an authored list of required-access refs.

## Process and CAD

`process` requires `method: fdm`, material, nozzle and layer dimensions, support policy, and minimum wall. Support policy is `forbid`, `forbid_when_practical`, or `allow_declared`.

`cad` requires `engine: openscad`, a minimum version string, and unique printable parts. The built-in engine accepts only:

- `base`, `lid`, `insert_coupon`
- `panel_north`, `panel_south`, `panel_east`, `panel_west`

An `authored_scad` entrypoint may additionally declare project-specific
printable selectors matching `[a-z][a-z0-9_]{0,63}`. The generator invokes
each selector exactly as `part="<name>"`, verifies the resulting single mesh,
records it in `generation.json`, and packages it under `meshes/<name>.stl`.
`installed_case` is reserved for the verifier's non-printable collision
subject and may never appear in `printable_parts`. Custom selectors are not
accepted by the built-in engine because it cannot author their geometry.
When custom selectors are present, the authored entrypoint must use explicit
part branches: an unknown selector must emit no mesh or reject evaluation.
Generation probes that closed contract and records the declared/custom census
and probe result in `generation.json`; packaging refuses missing or changed
selector-contract evidence. This prevents a catch-all assembly fallback from
silently exporting the wrong geometry under a mistyped accessory filename.
For these custom-part configurations, generation also canonicalizes OpenSCAD's
otherwise nondeterministic ASCII-STL facet ordering and records that transform
on every printable mesh and the installed-case mesh. Independent replay must
therefore reproduce byte-identical mesh hashes, not merely matching volumes.

Omit `cad.source` to use the built-in declarative engine. To use one reviewed hand-authored entrypoint, add this exact mapping:

```yaml
source:
  kind: authored_scad
  path: 03_src/mechanical/reviewed-case.scad
  sha256: <lowercase 64-hex digest>
  size: <positive byte count>
```

The path follows the same root-relative, traversal-free, non-symlink rules as subject bindings and must name a `.scad` file outside the build directory. The generator copies its bytes unchanged to `BUILD/enclosure.scad`; OpenSCAD `-D part=...` selects each declared printable part. The authored entrypoint is CAD authority, so it must implement every declared part itself and the fixed `part="installed_case"` selector. That selector must emit only the complete enclosure in installed coordinates: no PCB/component witnesses, exploded transforms, or print-oriented lid. The generator always exports it as `BUILD/assembled-case.stl` and binds its exact command and identity in `generation.json`. Configuration geometry remains review and verification intent; the built-in engine does not wrap, modify, or supplement authored source. Every custom printable selector must be implemented by that same bound entrypoint; an empty, disconnected, degenerate, or non-manifold result fails the normal printable-mesh verification.

For an enclosure derived from an immutable PCB release, add an exact
`subject.release_manifest` file binding alongside `pcb`, `step`, and
`interface`. The human release label remains descriptive; the manifest
path/size/SHA-256 is the dependency identity that prevents a same-named or
mutated PCB archive from being substituted. Legacy/co-design configurations
may omit it, but then they make no sealed-PCB-release identity claim.

## Geometry

Provide every field:

- `topology`: `split_shell` or `base_lid_panels`
- `xy_clearance_mm`, `wall_mm`, `floor_mm`, `roof_mm`, `corner_radius_mm`
- `board_bottom_z_mm`, `inside_top_z_mm`, `seam_z_mm`
- `panel_thickness_mm`, `panel_capture_mm`, `panel_clearance_mm`
- `corner_post_mm`, `lid_column_board_gap_mm`

All dimensions except panel clearance and lid-column gap are positive. The two clearances are nonnegative. The inside top must exceed board-bottom z. A split-shell seam must lie strictly between them.

## Fasteners

`fasteners.strategy` is `shared_board` or `separate_perimeter`. Declare thread, unique board-hole refs, case-hole points, boss and post diameters, and minimum radial wall.

- `shared_board` routes case closure through the PCB mounting axes. It is kept
  for replay of legacy v1 designs, but it does not satisfy schema v2's
  lid-off PCB-retention requirement.
- `separate_perimeter` gives the PCB its own board-hole bosses/inserts and
  gives base/lid closure distinct perimeter posts/inserts. Use it for new v2
  work. The built-in split-shell engine emits both groups; the generated
  `assembly_contract` records their roles and axes, and the v1 verifier checks
  that their radial envelopes are disjoint.

Schema v2 separately requires explicit `board_retention`, `case_closure`, and
optional accessory fastener groups with retained-part censuses and 3-D axes.
The current v2 validator checks those declarations against one another, but it
does not derive them from the v1 CAD geometry. Before assigning a
`board_retention` scope result, compare the generated v1 assembly contract and
geometry with the v2 groups. An authored SCAD adapter must implement the same
independence itself.

The insert mapping requires family, `cold_press|heat_set`,
hole/body/flange/recess dimensions, length, and bottom clearance. It may also
declare `pilot_basis: datasheet|coupon_prior|coupon_qualified`; omission means
`datasheet`. A datasheet-based cold-press pilot must remain smaller than the
nominal insert body. `coupon_prior` may use a larger modeled pilot only as the
centre of a new required coupon when a comparable registry observation exists.
`coupon_qualified` may use a larger modeled pilot selected for this design and
process. Both coupon bases require the insert coupon to remain declared and
required. Neither declaration is itself physical evidence or promotes
verification status. The screw mapping requires clearance/head/recess
dimensions, board and lid lengths, minimum engagement, and minimum tip
clearance.

Shared-board designs require no case holes. Separate-perimeter designs require at least four case holes.

## Interfaces and thermal intent

Create one unique row per access candidate with: `id`, `ref`, `role`, `side`, `disposition`, `center_mm`, `shape`, `opening_mm`, `plug_envelope_mm`, and `clearance_mm`.

Thermal intent requires `risk: low|moderate|high`, a soak requirement, named load case, and zero or more vent groups. Each vent group declares center, positive count/length/width/pitch, and `axis: x|y`.

`physical_validation` contains four booleans: insert coupon, board drop-in, all interfaces mated, and thermal soak. Its thermal value must match `thermal.physical_soak_required`.

These booleans govern the closed schema-v1 physical-evidence census. The v2
composition adds scoped, extensible physical tests, including lid-off board
retention, closure independence, and prewired-accessory operations; see
`configuration-schema-v2.md`.
