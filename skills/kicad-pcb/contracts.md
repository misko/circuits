# contract: skills/kicad-pcb/

**Purpose** — the KiCad engineering skill: the shared generic backend
(generate/route/stitch/rules), every checker the gates run, and the reference
canon (design policies, fab tiers, empirics).

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | the skill manual + dated learnings (post-mortems) |
| `contracts.md` | this file |
| `scripts/` | executable tooling (own contract) |
| `references/` | canon documents + data models (own contract) |

## Audit

- Every checker in `scripts/` must have a known-bad fixture in `tests/`
  (tests/README.md: a gate that cannot fail is worthless).
- Gate semantics changes require a matching row edit in
  `references/design-policies.md` — the canon and the code move together.
