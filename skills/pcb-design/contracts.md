# contract: skills/pcb-design/

**Purpose** — the pipeline-orchestration skill: takes a brief, drives it to an
orderable release. Carries its own project-independent seed set under
`templates/` (contracts + config schemas + doc starters) — commission copies
from HERE, never from a project (the 2026-07-20 clean-room contamination is
why).

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | the orchestration manual, stage by stage, with the D-* gates |
| `contracts.md` | this file |
| `templates/**` | the seed set: `contracts/` (stage contracts, nested to match project layout), `03_src/` + `03_tscircuit/` schema examples, `01_docs/` starters, `project.gitignore`, `rebuild_all.sh`, `README.md` |

## Audit

- `templates/README.md` documents the exact commission copy list; a new
  project seeded from it must pass `contracts_audit.py --walk --root <proj>`
  with zero violations before any design work.
- Template drift is the failure mode this layout kills: there is exactly ONE
  copy of each stage contract (here), so nothing can silently diverge.

## Structure

`templates/contracts/<stage>/[<sub>/]contracts.md` mirrors where each file
lands in a project. Schema YAMLs carry their provenance board in a header
comment; the KEYS are the contract, the values are placeholders.
