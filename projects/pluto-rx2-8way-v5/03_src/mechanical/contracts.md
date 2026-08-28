# contract: 03_src/mechanical/

**Purpose** — hand-authored, board-coupled mechanical source for accessories
that must track the exact PCB outline, mounting holes, and connector geometry.

**Mutability** — hand-edited source of truth.

## Allowed

| Pattern | What |
|---|---|
| `enclosure.yaml` | Declarative enclosure identity, subject, process, CAD backend, geometry, fastener, access-interface, thermal and physical-validation contract |
| `enclosure-cad-design-v2.yaml` | Immutable-subject schema-v1 CAD adapter bound by the schema-v2 composition contract |
| `enclosure-v2.yaml` | Schema-v2 installed-part, independent-fastener, motion, scope, and physical-evidence composition contract |
| `mechanical-intent-v2.yaml` | Commissioned assembly/service intent, including prewired insertion and lid-off PCB retention |
| `*.scad` | Parametric OpenSCAD source |
| `verify_antenna_clearance.py` | Project-specific, fail-closed accessory insertion and exact-collision verifier |
| `reference/**` | Bound user reference geometry, raw visual evidence, measurements, and conservative candidate contracts |
| `README.md` | Dimensions, assumptions, export commands, print and assembly instructions |
| `contracts.md` | This file |

Generated interface/STL/PNG/report files belong in `06_build/mechanical/`; that folder is
disposable and gitignored. Do not copy generated meshes into this source
folder.

## Validate

From the project root, run the three OpenSCAD export commands in `README.md`.
Each must exit zero and produce a non-empty STL under `06_build/mechanical/`.
Render `part="assembly"` and visually confirm that every J1-J10 edge is
continuously open, the J11/J12 roof notch reaches the south edge, the roof adds
no nominal mating-plane setback, and all independent fastener axes align with
the reference board. This visual check is not complete mate/tool/cable-service
evidence; the shared connector receipt governs that boundary.

## Repair

- PCB outline, mounting, or connector placement changed: update the named board
  parameters in the SCAD source from `04_kicad/pluto_rx2_8way_v5.kicad_pcb`,
  regenerate all meshes, and repeat the fit checks in `README.md`.
- Printer or insert fit differs: change only the exposed clearance/insert
  parameters after printing the coupon; do not silently move PCB datums.
