# contract: archived_projects/

**Purpose** — completed/retired boards moved out of the active `projects/`
tree (2026-07-21 reorganization: `usb-hub-3s` era begins). Same governance
as `projects/`: each board carries its OWN root contract; sealed `04_kicad/`
and `07_releases/` remain IMMUTABLE. Boards here also serve as FROZEN
regression fixtures — the e2e suites rebuild cook-loadcell and
crow-array-pod against their sealed boards.

**Mutability** — read-only by default. A board that returns to active
development moves back to `projects/` in its own commit.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `*/` | one archived board — governed by its own root contract |

## Audit

- `scripts/contracts_audit.py --projects` grades boards here honestly
  (adopted-forward), same as active projects.
