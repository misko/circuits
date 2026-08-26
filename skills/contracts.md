# contract: skills/

**Purpose** — the product: five installable skills whose development/source
authority lives HERE. Codex's `$skill-installer` publishes runtime copies under
`$CODEX_HOME/skills`; reinstall after an update rather than maintaining a
second hand-edited copy. The directory name is the direct invocation name, so
`shopping-list/` is `$shopping-list`; `/skills` opens the selector. Each skill
is self-contained: everything a clean-room agent needs to design a board lives
under its folder. Skills NEVER reference a concrete `projects/<board>` path —
worked evidence they cite lives in `examples/` (machine-checked:
contracts_audit C-ISO). Naming a board as incident provenance in a post-mortem
sentence is fine; pointing at its files is not.

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
| `pcb-enclosure/` | PCB-coupled enclosure design, printability, fit and physical-verification skill (own contract) |
| `shopping-list/` | per-distributor buying skill for the parts the fab will not source, governed by canon M-QUOTE (own contract) |

## Audit

- `scripts/contracts_audit.py` — structure + C-ISO isolation.
- `tests/run_tests.sh` — every checker under these skills has clean +
  known-bad coverage (see tests/README.md).
- **No credential lives under `skills/`.** Keys are read at runtime from
  `$VAR` or `<repo root>/.secrets/*.env` (gitignored, mode 600) and are never
  printed, logged, embedded in a URL, cached or recorded in a fixture —
  `shopping-list/contracts.md` states the rule and `t1_shopping_list.py`
  enforces it with a planted sentinel key.
