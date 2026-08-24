# contract: skills/pcb-enclosure/

**Purpose** — the reusable mechanical authority for board-coupled, printable
PCB enclosures. It turns an exact PCB/interface snapshot plus authored
mechanical intent into deterministic CAD, meshes, verification receipts, and
candidate packages without mutating the PCB release it derives from.

**Mutability** — hand-edited skill source. Worked board evidence lives in
repository-root `examples/` snapshots; this skill never points at a live board
project.

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | workflow, authority boundary, status vocabulary, and resource router |
| `contracts.md` | this file |
| `agents/**` | Codex UI metadata |
| `scripts/**` | interface extraction, deterministic generation, verification, rendering, STEP inspection, and packaging |
| `references/**` | schemas, topology selection, connector access, inserts, FDM, and evidence/release guidance |
| `assets/**` | reusable OpenSCAD engine and operator-evidence template copied or consumed by the scripts |

## Audit

- `/usr/bin/python3 scripts/verify_enclosure.py --help` names the exact
  automated boundary; attractive renders never become physical-fit evidence.
- Every checker has clean and one-defect known-bad coverage in
  `tests/t1_pcb_enclosure.py`.
- `scripts/contracts_audit.py` enforces coverage and C-ISO isolation.
- `skill-creator/scripts/quick_validate.py` validates the skill package.
