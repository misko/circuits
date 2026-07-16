---
id: 0000
date: 2026-07-14
status: accepted
---
# 0000 — Example: keep this ADR as the format reference

## Context
New contributors and agents need a worked example of the ADR format that
`docs/decisions/contracts.md` specifies. A schema in prose is easy to
misread; a real file is not.

## Options
- **A README section showing the format** — REJECTED: drifts from the
  contract, and is not itself validated by the folder's own rules.
- **This ADR (id 0000)** — is itself a valid ADR, so the folder's validator
  checks the example. Costs one id, permanently.
- **No example** — REJECTED: every author re-derives the format and they
  diverge.

## Decision
Keep `0000-example-adr.md` as a permanent, self-demonstrating format
reference. Real decisions start at 0001.

## Consequences
- id 0000 is never available for a real decision.
- If the ADR format changes, this file must change with it — it is the
  fixture the contract's validator runs against.
- Deleting it is allowed once a project has several real ADRs to imitate.
