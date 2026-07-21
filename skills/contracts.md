# contract: skills/

**Purpose** — the product: three symlink-published skills (`~/.claude/skills/*`
point HERE — one home, no drift). Each skill is self-contained: everything a
clean-room agent needs to design a board lives under its folder. Skills NEVER
reference a concrete `projects/<board>` path — worked evidence they cite lives
in `examples/` (machine-checked: contracts_audit C-ISO). Naming a board as
incident provenance in a post-mortem sentence is fine; pointing at its files
is not.

**Mutability** — hand-edited; every gate change must be reflected in
`skills/kicad-pcb/references/design-policies.md` (read it first — repo
CLAUDE.md) and covered by a known-bad test in `tests/`.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `pcb-design/` | pipeline orchestration skill (own contract) |
| `kicad-pcb/` | KiCad engineering skill: scripts + references (own contract) |
| `jlcpcb-fab/` | JLCPCB order/verification skill (own contract) |

## Audit

- `scripts/contracts_audit.py` — structure + C-ISO isolation.
- `tests/run_tests.sh` — every checker under these skills has clean +
  known-bad coverage (see tests/README.md).
