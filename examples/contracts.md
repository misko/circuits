# contract: examples/

**Purpose** — frozen evidence snapshots that skills and canon may cite
instead of pointing into `projects/` (contracts_audit C-ISO enforces that
skills never reference a live project path). A clean-room worktree carries
this folder, so every citation a skill makes resolves in-tree.

**Mutability** — APPEND-ONLY. A snapshot is evidence of a past run; if the
thing it proves is re-proven, add a NEW snapshot directory and re-point the
citation. Never edit an existing snapshot.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `*/PROVENANCE.md` | REQUIRED per snapshot: source path, commit sha, extraction date, what it is evidence OF, and whether it is runnable |
| `*/**` | the snapshot payload (scripts, notes, configs — whatever the evidence is) |

## Audit

- Every snapshot directory contains `PROVENANCE.md` naming a commit sha that
  exists in this repo (`git cat-file -e <sha>`).
- Citations in `skills/` and `docs/` point here or at commit shas — run
  `scripts/contracts_audit.py` (C-ISO) to verify no `projects/` paths.

## Structure

One directory per piece of evidence, named for what it proves
(`tsx-backend-proof/`, `tsx-placement-proof/`, ...), payload kept minimal —
the load-bearing artifacts only, never whole build trees.
