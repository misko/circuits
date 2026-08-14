# contract: skills/kicad-pcb/references/

**Purpose** — the canon: policies with check IDs, capability data, and the
hard-won empirics agents must not rediscover. Nothing here is advisory.

## Allowed

| Pattern | What |
|---|---|
| `*.md` | canon documents (design-policies, drc-discipline, routing empirics, tscircuit-folder, ...) |
| `*.yaml` | machine-consumed data models (e.g. `fab_tiers.yaml`) |
| `rf/` | modular RF source cards and the bounded RF design procedure |
| `contracts.md` | this file |

## Audit

- `design-policies.md` rows: every [M] ID must exist in a checker and have a
  known-bad test; every policy carries its motivating incident.
- An `[H]`-only row must state the ABSENCE of its gate, and where the gate is
  a planned ADR phase, name the ADR and the phase. A Verified cell that reads
  like enforcement while nothing runs is the gate-that-grades-nothing shape
  M-COVER exists to forbid, applied to this file. (M-IMPORT is the worked
  example: `[H]` + "no gate yet, ADR-0005 phases 2-3".)
- A row that declares itself the NARROW INSTANCE of a wider row must say so in
  BOTH rows, and the wider row must enumerate its known members (M-WIDTH).
  Currently: S3/S-VER <-> M-IMPORT, and M-QUOTE <-> M-IMPORT (distributor
  facts — stock/price/lifecycle — graded by `shopping_list.py`'s Q-* family).
- Data YAMLs: consumed by a script that validates shape on load; numbers
  carry provenance (which board/order proved them — canon M6: the fab's
  published page overrides at order time).
- Evidence citations point at `examples/` snapshots or commit shas, never
  `projects/...` paths (C-ISO).
