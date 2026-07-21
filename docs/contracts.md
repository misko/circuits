# contract: docs/

**Purpose** — repo-level canon that outlives any one board: architecture
decision records and the proof documents that state exactly what the generic
backend is proven on.

**Mutability** — ADRs are append-only once accepted (supersede, don't edit);
proof docs are updated in place when new evidence lands.

## Allowed

| Pattern | What |
|---|---|
| `*.md` | proof documents (`generic-generator-proof.md`, `generic-router-proof.md`, ...) |
| `decisions/**` | numbered ADRs `NNNN-slug.md` — govern; do not contradict silently (repo CLAUDE.md) |
| `contracts.md` | this file |

## Audit

- ADR numbering is monotonically increasing, no gaps introduced by deletion
  (supersede with a new ADR instead).
- Proof docs claim only MEASURED results and name the boards/commits that
  produced them.
