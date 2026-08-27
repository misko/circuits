# contract: 03_src/mechanical/

**Purpose** — commissioned, board-coupled enclosure source for the current
USB-controlled debug hub 2A. This directory preserves mechanical requirements
and exact parent selection while the shared `pcb-enclosure` skill owns
interface extraction, CAD generation, verification, and publication.

**Mutability** — hand-edited source of truth. Generated interfaces, STEP
assemblies, meshes, renders, receipts, and packages belong under
`06_build/mechanical/`. Dated physical observations belong under
`08_reviews/`. Immutable printable payloads belong only under a future
`07_enclosure_releases/<version>-<date>/`.

## Allowed

| Pattern | What |
|---|---|
| `mechanical-intent-v2.yaml` | Commissioned states, motions, independent fastener roles, unknowns, and physical obligations |
| `enclosure.yaml` | Future exact schema-v1 CAD design; absent until PCB, STEP, and interface authorities are complete |
| `enclosure-v2.yaml` | Future schema-v2 composition binding the exact v1 design and parent authorities |
| `*.scad` | Future reviewed authored CAD entrypoint |
| `reference/**` | Future exact path/size/SHA-256-bound mechanical input authority |
| `verify_*.py` | Future tested project-specific verifier where generic checks cannot express the assembly |
| `README.md` | Parent selection, rejected prototype boundary, requirements, and resume procedure |
| `contracts.md` | This file |

## Validate

- `enclosure_v2.py validate-intent` must accept the exact committed intent.
- Do not add `enclosure.yaml` until an exact current assembly STEP and exact
  interface are reproducible from the selected sealed PCB release.
- New CAD must use independent PCB-retention and case-closure screws. Removing
  every case screw and the lid must leave the PCB fastened to the base.
- Generated files must pass `enclosure_layout_audit.py`; none belongs under
  this source directory or `08_reviews/`.

## Repair

- A newer selected PCB release invalidates every future STEP/interface/CAD
  binding and requires regeneration.
- If independent case posts obstruct the board, connectors, or insertion path,
  change topology or outer envelope; do not fall back to shared PCB/case screws.
- If a physical print rests on a connector or solder tail, preserve the dated
  witness, remove the unintended support, regenerate from source, and repeat
  the board-support/load-path test.
