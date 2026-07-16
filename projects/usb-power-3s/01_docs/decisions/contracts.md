# contract: 01_docs/decisions/

**Purpose** — why the board is the way it is. Architecture Decision Records
(ADRs). Every non-obvious choice, every rejected alternative, every "we tried
X and it failed". This is the folder that makes a board maintainable by
someone who was not there — including yourself in a year.

**Mutability** — **append-only**. A decision is a historical fact. Never edit
an accepted ADR to change its meaning; write a new one and mark the old
`superseded-by`.

## Allowed

| Pattern | What |
|---|---|
| `NNNN-kebab-title.md` | one ADR. `NNNN` = zero-padded, monotonic, never reused |
| `contracts.md` | this file |

Nothing else. No datasheets, no CSVs, no scratch files.

## Structure: `NNNN-*.md`

```markdown
---
id: 0007
date: 2026-07-14
status: accepted          # proposed | accepted | rejected | superseded-by-0012
---
# 0007 — LM5145 over LM25145 for both buck stages

## Context
What forced a choice. The constraint, not the solution.

## Options
Each candidate WITH its tradeoff, including the ones rejected:
- **LM25145** — equation-identical, 42V max. REJECTED: 7 units at JLC.
- **LM5145** — 75V max, 554 in stock. Costs $2.17/ea.

## Decision
What we chose, in one sentence.

## Consequences
What this commits us to, and what breaks if reversed. Include the boring
ones: footprint, part cost, firmware impact, what must be re-verified.
```

All four sections required, non-empty. "Options" must list at least the
alternatives that were seriously considered — **a rejected candidate's
datasheet does not get committed to `02_parts/`, so this file is the ONLY record
that it was evaluated.**

## What deserves an ADR

- Any part chosen over a viable alternative (and why the other lost).
- Any deviation from the datasheet-recommended design.
- Any deliberate tolerance of a flagged issue ("15mΩ ESR vs 25mΩ design —
  accepted because the ceramic bank dominates above 20kHz").
- Any review finding dispositioned as "not a bug" — with the disproof.
- Any structural decision a future agent might "helpfully" undo.

## Forbidden

- Editing an `accepted` ADR's Context/Options/Decision. Only `status` may
  change, and only to `superseded-by-NNNN`.
- Gitignoring this folder. It is the least regenerable content in the repo;
  a repo-wide `**/*.csv`-style ignore that catches it is a defect.

## Validate

- filename matches `^[0-9]{4}-[a-z0-9-]+\.md$`
- frontmatter `id` == filename prefix; ids unique and monotonic
- `status` in {proposed, accepted, rejected, superseded-by-NNNN}
- `superseded-by-NNNN` points at an ADR that exists
- all four sections present and non-empty
- no ADR is gitignored

## Repair

- Missing `id` → derive from filename.
- Two ADRs with the same id → renumber the later one, update referrers.
- Decision text found in `ARCHITECTURE.md`/`README.md` → extract to a new
  ADR, replace the original with a link.
- An accepted ADR that contradicts the current design → do NOT edit it. Write
  the superseding ADR and set `status: superseded-by-NNNN` on the old one.
