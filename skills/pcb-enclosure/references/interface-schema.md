# Interface and configuration schema

Use schema version 1 exactly. The strict loader rejects duplicate YAML keys, unknown fields, omitted fields, unsafe paths, hash/size mismatches, and stale interface bindings.

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

`cad` requires `engine: openscad`, a minimum version string, and unique printable parts selected from:

- `base`, `lid`, `insert_coupon`
- `panel_north`, `panel_south`, `panel_east`, `panel_west`

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

The insert mapping requires family, `cold_press|heat_set`, hole/body/flange/recess dimensions, length, and bottom clearance. The screw mapping requires clearance/head/recess dimensions, board and lid lengths, minimum engagement, and minimum tip clearance.

Shared-board designs require no case holes. Separate-perimeter designs require at least four case holes.

## Interfaces and thermal intent

Create one unique row per access candidate with: `id`, `ref`, `role`, `side`, `disposition`, `center_mm`, `shape`, `opening_mm`, `plug_envelope_mm`, and `clearance_mm`.

Thermal intent requires `risk: low|moderate|high`, a soak requirement, named load case, and zero or more vent groups. Each vent group declares center, positive count/length/width/pitch, and `axis: x|y`.

`physical_validation` contains four booleans: insert coupon, board drop-in, all interfaces mated, and thermal soak. Its thermal value must match `thermal.physical_soak_required`.
