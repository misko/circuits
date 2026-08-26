# contract: 01_docs/journal/

**Purpose** — the per-stage diary (canon M9). The knowledge-evaporation
failure: a run's hardest analysis lived only in an agent's chat report and
died with the session. Journals capture it AS IT HAPPENS, per stage.

**Mutability** — APPEND-ONLY. An entry is a record of what happened, not a
document to polish. Never rewrite history; a wrong entry gets a correcting
entry.

## Allowed

| Pattern | What |
|---|---|
| `<stage>.md` | one journal per pipeline stage (`02_parts.md`, `03_schematic.md`, `placement.md`, `routing.md`, `verify.md`, ...) |
| `contracts.md` | this file |

## Entry structure (every stage start / iteration / finish / stuck)

    ## <YYYY-MM-DD HH:MM> — <start|iterate N|finish|stuck|iterate N (post-back)|handoff>
    - did: <the action, one line>
    - result: <MEASURED outcome — gate output, counts; never hope>
    - next: <what this implies>

A `stuck` entry is MANDATORY before backtracking (SKILL.md D-BACK): it
records the stagnation trigger (3 no-improvement iterations, or an
inexpressible finding class), the measured plateau, and the causal
hypothesis being carried upstream. The learnings block for the issue is
written at that moment, not at stage end.

## Audit

- `policy_audit` M-JRNL: once the design produces artifacts (a board or a
  promoted route), at least one journal with `## ` entries must exist.
- Entries reference measured numbers; an entry whose `result:` is a claim
  without a command output behind it is a defect in review.
