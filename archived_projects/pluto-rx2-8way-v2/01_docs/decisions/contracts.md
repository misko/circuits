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
| `<NNNN>-<kebab-title>.md` | one ADR. `NNNN` = zero-padded, monotonic, never reused |
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

## Schema: a PUBLISHED BOUND (canon M-BOUND)

**A published bound is REGENERATED, not typed**, and a bound is not a number —
it is a number PLUS THE SET OF PARTS YOU CAN ACTUALLY BUY. Every numeric
inequality this ADR publishes as its OWN derived result (not a quoted datasheet
limit) carries a declaration: a line reading exactly `<!-- bound -->` or
`<!-- bound: ID -->`, immediately followed by a fenced `yaml` block. One block
per bound; anything else in the document is prose and is read by nothing.

````markdown
<!-- bound: R_PD_MAX -->
```yaml
id: R_PD_MAX
claim: >-                    # WHAT is bounded, >= 10 chars
  Largest safety pull-down that keeps V(DOOR_RAW) under V_T-(min) 0.700 V with
  a cross-mated pod's 2.2k SCL pull-up injected.
relation: "<="               # <= < >= > ==
value: 559.3                 # THE PUBLISHED BOUND
unit: Ohm
corner: worst_case           # nominal | worst_case | typical — MANDATORY
command: <cmd>               # regenerates `value` AT THE DECLARED CORNER
governs:                     # what the bound is a bound ON — MANDATORY
  evaluate: <cmd ... {value}>  # `{value}` placeholder, at the DECLARED corner
  budget: "<= 0.700"           # the limit the bound was solved against
  unit: V
standard_value:
  series: E24                # or `explicit: [470, 510]`. NO GLOBAL DEFAULT.
  series_why: >-             # >= 20 chars, and it is a SOURCING argument
    A 1 %-tolerance safety pull-down off this board's own E24 strip; the board
    stocks no E96 resistors.
chosen: 470                  # the value the decision actually uses
tolerance: 0.05              # optional, in units of `value`
tolerance_why: >-            # MANDATORY whenever `tolerance` is present
  The bound is rounded to 0.1 Ohm from an exact 559.2830; 0.05 is half that
  last digit and three orders under the 49.3 Ohm gap to the nearest E24 value.
grade: CITED                 # CITED | ESTIMATED (+ `why_not_rerunnable:`)
requires: [03_src/rules/power_tree.yaml]   # optional; absent -> UNVERIFIED
corner_commands:             # optional; only to DIAGNOSE a mislabelled corner
  nominal: <cmd --corner nominal>
```
````

`command` is re-run from the repo root and its last stdout line must carry
exactly one number, diffed against `value`. `governs.evaluate` is run TWICE
MORE and those two runs are the whole point:

1. **AT THE BOUND ITSELF** (nudged inward by `tolerance`, because a published
   bound is rounded). A bound sits on its own budget edge at the corner it was
   derived at, and nowhere else. If it violates its own `governs.budget` there,
   IT WAS NOT DERIVED AT THE CORNER IT DECLARES.
2. **AT THE NEAREST STANDARD VALUE** admissible under the bound — the largest
   for `<=`/`<`, the smallest for `>=`/`>`. A bound whose only admissible
   standard value FAILS at the declared corner is a FAIL, not a rounding note.

WHY, and it is this ADR folder's own incident. A cooksense ADR published
`R_pd <= 592 Ohm` as the ONE-LINE TAKEAWAY of a document whose entire argument
is worst-case. **592 Ohm is the NOMINAL corner** (3.300 V, 2200 Ohm, ±0 %); the
worst-case bound is **559.283 Ohm**; and **560 Ohm, the nearest E24 value under
592, gives 0.700712 V against the 0.700 V budget and FAILS by 0.7 mV.** The
published bound permitted exactly one standard value and that value does not
clear. The chosen 470 Ohm was unaffected, so the BOARD was fine and no gate
reading copper could ever have found it. **A rule about a quantity must name
its EMITTER and its CORNER.**

### Validate (canon M-BOUND, `adr_bound_provenance.py <repo-root>`)

- `B-CORNER` — the bound, nudged inward by its own `tolerance`, must satisfy its
  own `governs.budget`. Fails ON THAT ALONE, whether or not anything else does.
- `B-STDVAL` — the nearest admissible standard value, re-evaluated at the
  declared corner, must satisfy that budget.
- `B-SERIES` — `series`/`explicit` and `series_why` are both mandatory. **An
  ASSUMED series is a verdict nobody chose**: E24 admits 560 under a 592 Ohm
  ceiling, E96 admits 590, and a stocked-set declaration may admit only 470.
- `B-REGEN` / `B-FLIP` — the command must reproduce `value` within `tolerance`;
  and if `chosen` satisfies the published bound but not the regenerated one,
  **THE DECISION'S OWN CONCLUSION REVERSES** and that is a separate finding no
  tolerance excuses.
- `B-TOL` — no `tolerance_why`, or a tolerance `>=` the distance from `value` to
  the nearest value the bound must rule on (`chosen`, the standard value), is
  refused. A tolerance wide enough to swallow the margin cannot distinguish pass
  from fail; that is how a fix recreates the defect it closes.
- `B-SCHEMA` / `B-GRADE` / `B-CMD` — unknown or misspelled keys, a missing
  `governs:`, an `evaluate` with no `{value}`, a `corner` outside
  {nominal, worst_case, typical}, `grade: CITED` with no command, `ESTIMATED`
  with no `why_not_rerunnable`, or a command that can WRITE.
- **ADOPTION IS RATCHETED, NOT MANDATED.** Coverage is reported and every ADR
  that publishes a bound without declaring it is named as OWED, under a
  committed `OWED_CEILING` (37 of 72 at adoption, 2026-07-29). The ceiling only
  ratchets DOWN and `CITED_FLOOR` only UP: the existing debt is a named list,
  and the NEXT typed bound must either declare a block or raise the ceiling in
  the same commit, naming the run that earned it.
- An unrunnable command is **UNVERIFIED**, never a FAIL — a gate whose verdict
  depends on whether a sibling board is mid-rebuild is a gate that gets switched
  off (canon M-IMPORT's ladder). The hole is closed from the other side by
  `CITED_FLOOR`.

### Repair

- A bound that does not regenerate at its declared corner → **do not edit the
  number in place if the ADR is `accepted`.** Publish the correction as a dated
  amendment inside the same document (the append-only rule protects the ARGUMENT
  and the decision, not a demonstrably false arithmetic result), state BOTH
  numbers and both corners, and say which one governs.
- A bound whose nearest standard value fails → the bound is wrong, not the
  series. Re-solve at the corner the document argues at.
- A quoted datasheet limit needs no block. If it is load-bearing, it is an
  IMPORTED FACT and belongs to canon M-IMPORT / S-VER, graded there.

## What deserves an ADR

- Any part chosen over a viable alternative (and why the other lost).
- Any deviation from the datasheet-recommended design.
- Any deliberate tolerance of a flagged issue ("15mΩ ESR vs 25mΩ design —
  accepted because the ceramic bank dominates above 20kHz").
- For a self-powered board: how it is DE-ENERGIZED (master disconnect /
  load-switch / EN-gating, or an ADR-justified always-on) and its stored
  quiescent draw — the mandatory input-protection ADR must settle this;
  usb-hub-3s-v3 (2026-07-23) self-drained a LiPo pack via always-on EN pins
  because no ADR asked. Emitted to `power_tree.yaml` for the E-OFF gate.
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
