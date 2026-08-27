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
| `mechanical-intent-v2.yaml` | Commissioned assembly states, prewired insertion/removal operations, independent fastener roles and physical evidence obligations |
| `enclosure-v2.yaml` | Optional schema-v2 composition wrapper binding intent, exact v1 CAD design, installed parts, fastener groups, clearance cases and readiness scopes |
| `*.scad` | Optional board-coupled parametric OpenSCAD source or an explicitly retained co-design prototype |
| `reference/**` | Exact externally supplied or project-authored mechanical inputs only when path/size/SHA-256-bound by schema-v2 authority; generated printable meshes remain under `06_build/` |
| `*.json` | Project-specific machine-readable accessory/measurement authority or verifier input named by schema-v2 bindings; never an unbound result receipt |
| `verify_*.py` | Project-specific verifier only when generic enclosure checks cannot express an installed accessory; must be bound as tooling evidence and tested with known-bad fixtures |
| `README.md` | Board-specific dimensions, assumptions, export, print and assembly instructions |
| `contracts.md` | This file |

### keys: 03_src/mechanical/enclosure.yaml

| key | reader | why |
|---|---|---|
| `schema` | `enclosure_common.py, verify_enclosure.py, package_enclosure.py` | closed schema version, preserved in verification and package evidence |
| `kind` | `enclosure_common.py, verify_enclosure.py` | closed document kind prevents another YAML family being graded as an enclosure |
| `name` | `enclosure_common.py, generate_enclosure.py, package_enclosure.py` | stable artifact/package stem |
| `mode` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | `co_design` may feed constraints upstream; `derived` must adapt to immutable PCB bytes |
| `subject.*` | `enclosure_common.py, verify_enclosure.py, package_enclosure.py` | exact PCB/STEP paths and SHA-256 identities bind every derived artifact |
| `process.*` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | printer, material, nozzle/layer and support policy constrain generated geometry |
| `cad.*` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | backend/source selection and exact generated-part contract |
| `geometry.*` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | split-shell or captured-panel base/tray topology and its panel-capture clearances; service-access openings come from `interfaces[].*` |
| `fasteners.*` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | screw, insert, boss and fit-coupon geometry |
| `interfaces[].*` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | every connector, control, fuse and mounting feature receives an explicit access disposition |
| `thermal.*` | `enclosure_common.py, generate_enclosure.py, verify_enclosure.py` | ventilation zones and the thermal-validation obligation |
| `physical_validation.*` | `enclosure_common.py, verify_enclosure.py, package_enclosure.py` | schema-v1 compatibility evidence; schema-v2 intent/config owns extensible physical obligations and scoped readiness |

## Validate

- Run the owning skill's verifier against `enclosure.yaml`; every applicable
  check must carry a nonzero denominator and exact subject hashes.
- Regenerate under `06_build/mechanical/`; `rm -rf 06_build/` must never remove
  the only copy of a design decision or physical-test observation.
- A render can establish CAD review only. Promote to `PRINT_VERIFIED` or
  `THERMALLY_VERIFIED` solely from a dated physical witness in `08_reviews/`.
- Keep the authored v2 physical witness under a dated `08_reviews/` path;
  validation and aggregation receipts remain disposable under
  `06_build/mechanical/` until immutable enclosure publication.

## Repair

- PCB outline, holes, connector placement or STEP bytes changed: update the
  subject identity, regenerate all mechanical artifacts, and repeat affected
  fit/thermal checks.
- Printer or insert fit differs: change the declared process/fastener
  clearance after a measured coupon; never silently move PCB datums.
