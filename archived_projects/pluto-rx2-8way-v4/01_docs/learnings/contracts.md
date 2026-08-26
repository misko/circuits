# contract: 01_docs/learnings/

**Purpose** — per-stage HARVEST SOURCES (canon M9): when a stage completes,
what bit, why, and how to avoid it next time. These feed the skill's canon
(design-policies.md rows, T4 regressions, config defaults) via a harvest
pass — they are raw evidence, NOT the canon itself; repo policy keeps
distilled conclusions in the canon and the ADRs.

**Mutability** — written at stage completion; append if the stage reopens.

## Allowed

| Pattern | What |
|---|---|
| `<stage>.md` | one file per completed stage, same names as `journal/` |
| `contracts.md` | this file |

## Entry structure (one block per issue)

    ## <short issue title>
    - what happened: <measured symptom>
    - root cause: <the actual mechanism, not the proximate fix>
    - avoid next time: <concrete: config default / checker / selection rule>
    - candidate-canon: <yes + suggested check ID | no + why local-only>

## Audit

- `policy_audit` M-LEARN: a release may not be cut while a completed
  stage has no learnings file ("nothing learned" is a valid entry — write
  it explicitly after actually reflecting).
- Harvest: each `candidate-canon: yes` item is either promoted (canon row /
  test / default) or explicitly rejected in the harvest commit message.
