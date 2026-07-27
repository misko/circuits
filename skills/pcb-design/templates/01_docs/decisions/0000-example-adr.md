---
id: 0000
date: 2026-07-14
status: accepted
---
# 0000 — Example: keep this ADR as the format reference

## Context
New contributors and agents need a worked example of the ADR format that
`01_docs/decisions/contracts.md` specifies. A schema in prose is easy to
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

## Invariants emitted
Intent that only a human reads drifts silently from the netlist — the D1
reverse-polarity defect (usb-hub-3s v1.0) passed every gate because no ADR's
intent was EXECUTABLE. So a **protection / topology / input-protection** ADR
MUST emit at least one machine-checkable assertion into
`03_src/rules/electrical_invariants.yaml`, each citing this ADR's number.
Graded by `electrical_invariants.py` (canon E-INV); the E-ADR check flags a
protection/topology ADR that emits none. Example (this format ADR emits none —
it decides nothing electrical):

```yaml
# in 03_src/rules/electrical_invariants.yaml
invariants:
  - assert: pin_on_net      # a named pin must sit on a named net
    pin: "D1.1"
    net: VIN
    adr: "0001"
    why: "D1 reverse-polarity clamp cathode feeds VIN, not the raw battery rail"
```
Kinds: `pin_on_net`, `series_chain` (topological order; `through: {Q1: [D, S]}`
names a >2-pad part's bridging pins), `net_has_part` (net carries >= N parts of
a type). Geometric kinds (`clamp_le_rating`, `kelvin_within`) are deferred (E2).
