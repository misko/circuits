# contract: projects/

**Purpose** — one folder per commissioned board. Each board is standalone
and transferable, governed by its OWN root `contracts.md` (seeded at
commission from `skills/pcb-design/templates/contracts/ROOT.contracts.md`)
and per-stage contracts.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `*/` | one board project — MUST carry its own root `contracts.md`; its stage folders carry theirs. Sealed `04_kicad/` + `07_releases/` are IMMUTABLE (repo CLAUDE.md) and covered by the board's root contract |

## Audit

- `scripts/contracts_audit.py --projects` grades every board honestly
  (adopted-forward: boards commissioned before this contract are graded, the
  gaps tracked in their remediation lists — history is not rewritten).
- Per-board content gates: each board's own contracts + `policy_audit.py`.
