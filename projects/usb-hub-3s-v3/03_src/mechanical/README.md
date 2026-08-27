# USB Hub 3S v3 v1.12 wall-lid enclosure candidate

This directory is the discoverable source for a three-print enclosure candidate
bound exactly to immutable PCB release `v1.12-2026-07-28`:

- a floor-down foundation with only four PCB bosses and four independent case
  posts above its floor;
- one roof-down lid whose four close-in side skirts lower vertically over the
  already-fastened complete PCB; and
- one insert-fit coupon.

This is a mutable derived-enclosure candidate, not an enclosure release. The sealed PCB
STEP is missing F2, J1-J5, Q1-Q6, and U3-U5, and SW1 has no modeled body. Exact
solid clearance therefore remains `FAIL`; physical and thermal tests remain
`NOT_RUN`. Do not claim `CAD_READY`, `PRINT_VERIFIED`, production readiness, or
order readiness, and do not publish under `07_enclosure_releases/` yet.

## Topology and load paths

The PCB is retained with four M3 screws on H1-H4. Four different top-down M3
screws close the lid onto four perimeter posts. Removing every case screw and
the complete lid does not release the PCB.

PCB-to-boss and roof-to-post terminal bearing contacts are intentional and
nonpenetrating, so the four schema-v2 whole-part motion cases declare 0.0 mm at
their endpoints. Positive clearance to non-bearing features remains encoded by
the analytic skirt/notch/post assertions and must be checked physically. A
future contact-aware motion schema is tracked in `improvements.md` as IMP-239;
the candidate does not pretend that a whole-part positive clearance can coexist
with its required bearing contacts.

The lid is one piece: its roof bridges four 2.4 mm skirts. Each skirt stops
0.30 mm before the adjacent 9 mm corner posts, which fill the corner structure
without intersecting the lid's vertical path. J1-J5 use full-width,
bottom-open notches, so the complete lid lowers 40 mm over the populated PCB
without threading a connector through a final-pose hole. The SCAD asserts:

- four skirt transforms map local vertical to global +Z;
- all five notch tangent/Z centers and tops match the declared interface
  coordinates on their wall planes;
- every notch reaches through the skirt bottom;
- minimum material is 4.40 mm below the roof, 2.00 mm between adjacent
  notches, and 0.30 mm between skirt endpoints and case posts; and
- all 140 vent-slot/top-service-opening pairs retain at least a conservative
  1.40 mm 2D ligament against the 1.20 mm process minimum.

The schema-v1 `topology: split_shell` value is the supported two-shell/no-panel
vocabulary. Exact skirt reach, assembly motion, and clearance authority live in
the authored SCAD and schema-v2 intent rather than the generic v1 seam engine.

Connector openings, plug envelopes, vents, and service openings remain
provisional conservative gauges until received-part measurements and the
missing exact obstruction authority exist. The supplemental-authority decision
is explicit: immutable footprints and reviewed bounds can seed this candidate,
but current schema/tooling cannot compose them with the incomplete sealed STEP
as exact collision authority.

## Committed source

- `usb_hub_3s_v3_case.scad` — authored reproducible CAD and analytic geometry
  assertions;
- `enclosure.yaml` — schema-v1 generation/verification binding;
- `mechanical-intent-v2.yaml` — three states and four straight 40 mm motions;
- `enclosure-v2.yaml` — exact subjects, scoped policy, independent fasteners,
  four clearance cases, and physical-test census;
- `reference/board-interface-v1.12.json` — deterministic exact interface
  extraction committed for clean-clone validation; and
- `reference/supplemental-obstruction-decision.yaml` — reviewed authority
  boundary and forward composite-authority limitation.

The immutable PCB release is an input only. Nothing under `07_releases/` is
edited by this candidate.

## Generated printable outputs

Regenerate into this stable ignored build path:

```text
projects/usb-hub-3s-v3/06_build/mechanical/usb-hub-v1.12-wall-lid-v2/
```

Key files are:

| File | Purpose |
|---|---|
| `base.stl` | foundation, H1-H4 bosses, and four independent case posts |
| `lid.stl` | roof-down one-piece four-skirt lid with bottom-open notches |
| `insert_coupon.stl` | 3.95/4.05/4.15/4.25/4.35 mm pilot ladder |
| `assembled-case.stl` | installed enclosure selector for review checks |
| `assembly.png` | exploded CAD review |
| `closed-assembly.png` | closed lid plus reference PCB review |
| `base-board.png` | lid-off board-seating/load-path review |
| `generation.json` | exact source/selector/mesh receipt |
| `v2-validation.json` | exact schema-v2 binding receipt |
| `step-inspection.json` | expected incomplete STEP census |
| `verification.json` | expected governing `FAIL` report |

Generated files are intentionally ignored and reproducible; they are not
hidden under `08_reviews/` and are not immutable release artifacts.

## Exact replay

Run from repository root:

```sh
project_path=projects/usb-hub-3s-v3
build_path="$project_path/06_build/mechanical/usb-hub-v1.12-wall-lid-v2"

/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-intent "$project_path/03_src/mechanical/mechanical-intent-v2.yaml" \
  --output "$build_path/mechanical-intent-validation-v2.json"

/usr/bin/python3 skills/pcb-enclosure/scripts/enclosure_v2.py \
  validate-config "$project_path/03_src/mechanical/enclosure-v2.yaml" \
  --root "$project_path" --output "$build_path/v2-validation.json"

/usr/bin/python3 skills/pcb-enclosure/scripts/generate_enclosure.py \
  "$project_path/03_src/mechanical/enclosure.yaml" --root "$project_path" \
  --build-dir "$build_path"

xvfb-run -a /usr/bin/openscad -o "$build_path/closed-assembly.png" --render \
  --imgsize 1800,1300 --autocenter --viewall --projection p \
  --colorscheme Tomorrow -D 'part="closed_review"' \
  -D 'show_reference_board=true' \
  "$project_path/03_src/mechanical/usb_hub_3s_v3_case.scad"

xvfb-run -a /usr/bin/openscad -o "$build_path/base-board.png" --render \
  --imgsize 1800,1300 --autocenter --viewall --projection p \
  --colorscheme Tomorrow -D 'part="base_review"' \
  -D 'show_reference_board=true' \
  "$project_path/03_src/mechanical/usb_hub_3s_v3_case.scad"

/usr/bin/python3 skills/pcb-enclosure/scripts/render_enclosure.py \
  "$build_path/enclosure.scad" --output "$build_path/assembly.png"
```

Reproduce the committed interface authority rather than trusting it:

```sh
/usr/bin/python3 skills/pcb-enclosure/scripts/extract_board_interface.py \
  "$project_path/07_releases/v1.12-2026-07-28/source/usb_hub_3s_v2.kicad_pcb" \
  -o "$build_path/board-interface.replayed.json" \
  --access-ref J1 --access-ref J2 --access-ref J3 --access-ref J4 \
  --access-ref J5 --access-ref F1 --access-ref F2 --access-ref SW1 \
  --access-ref D8 --access-ref D9 --access-ref D10 --access-ref D11 \
  --access-ref D12

cmp "$build_path/board-interface.replayed.json" \
  "$project_path/03_src/mechanical/reference/board-interface-v1.12.json"
```

The governing audit deliberately exits nonzero:

```sh
uv run --offline --with cadquery python \
  skills/pcb-enclosure/scripts/inspect_step.py \
  "$project_path/07_releases/v1.12-2026-07-28/3d/usb_hub_3s_v2.step" \
  --interface "$project_path/03_src/mechanical/reference/board-interface-v1.12.json" \
  --output "$build_path/step-inspection.json" \
  --component-mesh "$build_path/components.stl"

/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure.py \
  "$project_path/03_src/mechanical/enclosure.yaml" --root "$project_path" \
  --build-dir "$build_path" --target cad \
  --step-inspection "$build_path/step-inspection.json" \
  --report "$build_path/verification.json"
```

Expected result from both commands: exit 1 / `FAIL`. Do not package or stage an
enclosure release around that result.

## Assembly and physical plan

1. Print the coupon in production PETG settings and qualify the exact insert
   lot, pilot, flange seating, spin resistance, and boss condition.
2. Install inserts into the four PCB bosses and four independent case posts.
3. Place the complete PCB vertically onto H1-H4 and retain it with four M3x6
   screws.
4. Prove all four boss lands seat simultaneously and no connector, solder tail,
   component, lid skirt, or case post supports the PCB.
5. Lower the complete lid through its declared 40 mm vertical path. Prove all
   five bottom-open notches clear the full connector bodies without forced
   deflection and the skirts clear all four posts.
6. Close only the four perimeter M3x6 screws, then remove them and lift the lid
   40 mm. Prove the PCB remains secured throughout.
7. Mate the real XT60, three simultaneous USB-A plugs, USB-C plug, fuse, and
   switch/service tooling; record notch witness marks, rattle, wear, and cable
   bend/exit behavior.
8. Run the closed-case thermal soak only after electrical load testing is
   qualified; record converter, switch, fuse/clip, connector, air, and case
   temperatures.
