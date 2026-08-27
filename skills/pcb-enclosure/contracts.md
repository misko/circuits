# contract: skills/pcb-enclosure/

**Purpose** — the reusable mechanical authority for commissioning,
generating, verifying, packaging, and independently releasing board-coupled
printable enclosures. It composes exact PCB/interface subjects, authored
mechanical intent, deterministic CAD/meshes, scoped evidence, and immutable
enclosure releases without mutating the parent PCB release.

**Mutability** — hand-edited skill source. Sanitized worked evidence lives in
repository-root `examples/`; the skill must never depend on a concrete live
board project.

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | commissioning-first workflow, authority boundary, status vocabulary, and resource router |
| `contracts.md` | this file |
| `agents/**` | Codex UI metadata |
| `scripts/enclosure_common.py` | strict v1 schemas, safe paths/atomic outputs, mesh helpers, and adapter to the repository shared bounded-process authority |
| `scripts/extract_board_interface.py` | exact KiCad interface extraction |
| `scripts/generate_enclosure.py` | deterministic v1 CAD generation and assembly-contract receipt |
| `scripts/inspect_step.py` | exact STEP inspection and component audit export |
| `scripts/build_collision.py` | receipted final installed-position collision evidence |
| `scripts/render_enclosure.py` | visual-review render only |
| `scripts/verify_enclosure.py` | schema-v1 geometry/readiness verification |
| `scripts/package_enclosure.py` | freshly regraded portable v1 candidate package |
| `scripts/enclosure_v2.py` | mechanical-intent/config/evidence validation and conservative scoped aggregation |
| `scripts/stage_enclosure_release.py` | atomic no-replace publication below `07_enclosure_releases/` |
| `scripts/verify_enclosure_release.py` | immutable enclosure-release census, authority, status, and replay-path verification |
| `scripts/enclosure_layout_audit.py` | fleet audit for canonical authored, generated, review, and immutable-release paths |
| `references/**` | commission, schemas, topology, access, motion, fastener, FDM, evidence, and independent-release guidance |
| `assets/enclosure-engine.scad` | reusable OpenSCAD engine with closed part selectors and independent-fastener geometry |
| `assets/*.template.yaml` | mechanical-intent and physical-evidence authoring templates |
| `assets/enclosure-release.contracts.md` | project enclosure-release-stream contract template |

The only low-level process-launch authority used by this skill is the shared
repository implementation in `skills/kicad-pcb/scripts/process_runner.py` and
`pipeline_runtime.py`. Enclosure scripts may adapt its result but must not add
an independent `subprocess.run` or `Popen` path.

## Audit

- `/usr/bin/python3 scripts/verify_enclosure.py --help` names the v1 automated
  geometry boundary; renders never become fit or motion evidence.
- `tests/t1_pcb_enclosure.py` covers schema-v1 verification and packaging,
  including known-bad fixtures for each closed check.
- `tests/t1_pcb_enclosure_engine.py` exercises independent and legacy shared
  fastener solids with OpenSCAD point-in-solid checks.
- `tests/t1_pcb_enclosure_safety.py` exercises bounded execution, path/output
  safety, atomic publication, duplicate-key rejection, and package regrading.
- `tests/t1_pcb_enclosure_v2.py` covers commissioning, exact v1/v2 composition,
  service states, independent fasteners, whole-body motion contracts, evidence,
  authority ceilings, and scoped aggregation.
- `tests/t1_enclosure_release.py` covers independent immutable publication,
  release-root authority/replay resolution, conservative status, and hostile
  workspace/release fixtures.
- `tests/t1_enclosure_layout.py` proves project enclosure sources, reference
  STLs, generated artifacts, physical reviews, and releases cannot cross their
  canonical filesystem boundaries.
- `scripts/contracts_audit.py` enforces coverage and project-isolation rules.
- `skill-creator/scripts/quick_validate.py` validates skill metadata and
  structure.
