# contract: skills/pcb-design/

**Purpose** — the prompt-to-device orchestration skill: takes a plain-language
hardware brief through iterative development to reviewed, reproducible PCB
fabrication and optional enclosure evidence. Order admission, a physical first
article, firmware, and a product-level digital twin remain separately governed
claims. Carries its own project-independent seed set under
`templates/` (contracts + config schemas + doc starters) — commission copies
from HERE, never from a project (the 2026-07-20 clean-room contamination is
why).

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | the small orchestration kernel: lifecycle, invariants, capability-profile decisions, and direct reference router |
| `agents/**` | Codex UI metadata for the installed skill; generated from the current SKILL.md and required to keep `$pcb-design` in the default prompt |
| `contracts.md` | this file |
| `scripts/**` | fail-closed project commissioning, shared connector-assembly contract compiler, publication-boundary orchestration gates, the pure reference router and authority/coverage checker; enclosure and fabrication mechanics remain owned by `pcb-enclosure` and `jlcpcb-fab` |
| `templates/**` | the seed set: `contracts/` (stage contracts, nested to match project layout), `03_src/` + `03_tscircuit/` schema examples, `01_docs/` starters, `ORCHESTRATION_STATE.md` (the coordinator's state-journal skeleton, copied per campaign not per project), `project.gitignore`, `rebuild_all.sh`, `README.md` |
| `references/**` | one-owner orchestration procedures, the typed stage contract, and the machine-readable authority map; KiCad, enclosure and JLC mechanics remain routed to their owning skills |

## Audit

- `scripts/commission_project.py` owns the exact scaffold manifest;
  `templates/README.md` summarizes it. A new project must pass
  `contracts_audit.py --walk --root <proj>` with zero violations before design.
- Template drift is the failure mode this layout kills: there is exactly ONE
  copy of each stage contract (here), so nothing can silently diverge.
- `scripts/skill_authority_check.py` freezes the pre-refactor policy
  denominator, requires every routed reference to be reachable, and rejects
  duplicate authority or a core outside its line/word budget.
- `scripts/pause_state.py` owns the single current pause manifest and generated
  STATUS/RESUME views. Project prose may explain history but may not compete
  with its checkpoint/receipt hashes or semantic state id.
- `scripts/connector_assembly_contract.py` owns the exact shared connector
  schema and deterministic receipt. Canonical rebuilds compile it as a
  pre-placement fact lock; exact typed no-operated evidence yields
  applicability-only `N-A`. The current enclosure adapter revalidates operated
  profiles and remains capped `INCOMPLETE`. A realized-board PCB geometry
  consumer is still owed. New mappings may not copy connector dimensions; current enclosure
  schema-v1 inline candidates remain a declared migration gap and cannot become
  shared service authority.

## Structure

`templates/contracts/<stage>/[<sub>/]contracts.md` mirrors where each file
lands in a project. Schema YAMLs carry their provenance board in a header
comment; the KEYS are the contract, the values are placeholders.
