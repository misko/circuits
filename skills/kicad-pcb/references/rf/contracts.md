# contract: skills/kicad-pcb/references/rf/

**Purpose** — small, locally available RF knowledge cards selected by the
pipeline only when `rf.enabled: true`. The cards summarize authoritative
sources; they are not cached project results and never trigger network access.

## Allowed

| Pattern | What |
|---|---|
| `*.md` | bounded procedures and interpretation guidance |
| `*.yaml` | validated source-card catalogue consumed by `rf_context.py` |
| `contracts.md` | this file |

## Audit

- Every source card has a stable ID, provenance class, URL or bibliographic
  locator, selector topics, a paraphrased claim, a design use, and limits.
- `normative`, `background`, and `tool_capability` cards may enter a clean-room
  context. `precedent` and `incident` cards require an explicit project policy.
- Cards contain no copied project geometry and no runtime web dependency.
- Numeric rules become blocking only when the project contract adopts them and
  a checker independently measures the realized board.
