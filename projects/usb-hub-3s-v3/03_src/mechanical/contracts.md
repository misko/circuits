# contract: 03_src/mechanical/

**Purpose** — hand-authored, board-coupled mechanical source. This folder
binds an enclosure to the exact PCB/release subject while the shared
`pcb-enclosure` skill owns extraction, CAD generation, verification and
candidate packaging.

**Mutability** — hand-edited source of truth. Generated meshes, renders,
reports and packages belong under `06_build/mechanical/`. A deterministic
interface extracted from an immutable parent release may be retained beneath
`reference/` only when its exact replay command and byte comparison are in the
README and both configs bind it.

## Allowed

| Pattern | What |
|---|---|
| `enclosure.yaml` | Declarative enclosure identity, subject, process, CAD backend, geometry, fastener, access-interface, thermal and physical-validation contract |
| `enclosure-v2.yaml` | Commissioned authority, scope, installed-part, fastener-role, assembly-motion and physical-test composition |
| `mechanical-intent-v2.yaml` | Installed/service states, insertion/removal operations, unknowns and excluded claims |
| `*.scad` | Optional board-coupled parametric OpenSCAD source or an explicitly retained co-design prototype |
| `prepare_obstruction_step.py` | Strict producer for the supplemental JLC-catalog obstruction STEP; never edits the sealed PCB release |
| `compose_obstruction_step.py` | Exact CadQuery/OCP compositor for the sealed STEP plus the bound supplemental obstruction STEP |
| `reference/board-interface*.json` | Reviewed deterministic extraction of an exact immutable parent PCB; never hand-edited |
| `reference/*decision*.yaml` | Reviewed authority decision that preserves blockers and excluded claims; not installed geometry |
| `reference/obstruction-models.json` | Exact model, footprint, transform, reference-census, and parent-release bindings for supplemental obstruction geometry |
| `reference/usb-hub-wall-lid-unbound-qualitative-xt60-fit-observation-2026-08-27.md` | Qualitative physical-fit observation with explicitly unbound printed-article identity; negative mechanical evidence only, never dimensional authority |
| `reference/obstruction_models/*/*.step` | Hash-bound JLC/EasyEDA catalog bodies; obstruction authority only, not received-part fit proof |
| `reference/obstruction_models/*/*.kicad_mod` | Hash-bound JLC/EasyEDA registration footprints for those bodies; not a replacement PCB land-pattern authority |
| `README.md` | Board-specific dimensions, assumptions, export, print and assembly instructions |
| `contracts.md` | This file |

## Validate

- Run the owning skill's verifier against `enclosure.yaml`; every applicable
  check must carry a nonzero denominator and exact subject hashes.
- Run `enclosure_v2.py validate-intent` and `validate-config` against the
  committed paths; both must work from a clean clone before generation.
- Re-extract a retained board interface into `06_build/mechanical/` and require
  byte identity with the committed `reference/` copy.
- Regenerate under `06_build/mechanical/`; `rm -rf 06_build/` must never remove
  the only copy of a design decision or physical-test observation.
- Rebuild and compose the supplemental obstruction STEP. The union must cover
  every modeled PCB reference plus every declared unmodeled access body before
  its exact collision result may govern a candidate.
- A render can establish CAD review only. Promote to `PRINT_VERIFIED` or
  `THERMALLY_VERIFIED` solely from a dated physical witness in `08_reviews/`.

## Repair

- PCB outline, holes, connector placement or STEP bytes changed: update the
  subject identity, regenerate all mechanical artifacts, and repeat affected
  fit/thermal checks.
- Printer or insert fit differs: change the declared process/fastener
  clearance after a measured coupon; never silently move PCB datums.
