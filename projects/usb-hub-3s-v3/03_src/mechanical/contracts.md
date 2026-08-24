# contract: 03_src/mechanical/

**Purpose** — hand-authored, board-coupled mechanical source. This folder
binds an enclosure to the exact PCB/release subject while the shared
`pcb-enclosure` skill owns extraction, CAD generation, verification and
candidate packaging.

**Mutability** — hand-edited source of truth. Generated interface snapshots,
meshes, renders, reports and packages belong under `06_build/mechanical/`.

## Allowed

| Pattern | What |
|---|---|
| `enclosure.yaml` | Declarative enclosure identity, subject, process, CAD backend, geometry, fastener, access-interface, thermal and physical-validation contract |
| `*.scad` | Optional board-coupled parametric OpenSCAD source or an explicitly retained co-design prototype |
| `README.md` | Board-specific dimensions, assumptions, export, print and assembly instructions |
| `contracts.md` | This file |

## Validate

- Run the owning skill's verifier against `enclosure.yaml`; every applicable
  check must carry a nonzero denominator and exact subject hashes.
- Regenerate under `06_build/mechanical/`; `rm -rf 06_build/` must never remove
  the only copy of a design decision or physical-test observation.
- A render can establish CAD review only. Promote to `PRINT_VERIFIED` or
  `THERMALLY_VERIFIED` solely from a dated physical witness in `08_reviews/`.

## Repair

- PCB outline, holes, connector placement or STEP bytes changed: update the
  subject identity, regenerate all mechanical artifacts, and repeat affected
  fit/thermal checks.
- Printer or insert fit differs: change the declared process/fastener
  clearance after a measured coupon; never silently move PCB datums.
