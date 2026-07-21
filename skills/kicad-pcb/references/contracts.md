# contract: skills/kicad-pcb/references/

**Purpose** — the canon: policies with check IDs, capability data, and the
hard-won empirics agents must not rediscover. Nothing here is advisory.

## Allowed

| Pattern | What |
|---|---|
| `*.md` | canon documents (design-policies, drc-discipline, routing empirics, tscircuit-folder, ...) |
| `*.yaml` | machine-consumed data models (e.g. `fab_tiers.yaml`) |
| `contracts.md` | this file |

## Audit

- `design-policies.md` rows: every [M] ID must exist in a checker and have a
  known-bad test; every policy carries its motivating incident.
- Data YAMLs: consumed by a script that validates shape on load; numbers
  carry provenance (which board/order proved them — canon M6: the fab's
  published page overrides at order time).
- Evidence citations point at `examples/` snapshots or commit shas, never
  `projects/...` paths (C-ISO).
