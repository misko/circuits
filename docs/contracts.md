# contract: docs/

**Purpose** — the indexed repository documentation set: accepted architecture
decisions, measured proof documents, and explicitly classified history.

**Mutability** — ADRs are append-only once accepted (supersede, don't edit);
proof docs are updated in place when new evidence lands. Historical plans are
frozen context: give them a non-authoritative banner rather than reviving them
as procedure.

## Allowed

| Pattern | What |
|---|---|
| `README.md` | documentation authority and navigation index |
| `*.md` | measured proof, implementation notes, or explicitly bannered history as classified by `README.md` |
| `decisions/**` | numbered ADRs `NNNN-slug.md` — govern; do not contradict silently (repo CLAUDE.md) |
| `contracts.md` | this file |

## Audit

- ADR numbering is monotonically increasing, no gaps introduced by deletion
  (supersede with a new ADR instead).
- Proof docs claim only MEASURED results and name the boards/commits that
  produced them.
- Historical plans carry a prominent non-authoritative banner and are linked
  only from `README.md` or retained evidence.
