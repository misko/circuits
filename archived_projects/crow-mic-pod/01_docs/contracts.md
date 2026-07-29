# contract: 01_docs/

**Purpose** — everything a human must know that cannot be regenerated from
anything else. This is the most valuable folder in the project and the only
one that is unrecoverable if lost.

**Mutability** — hand-edited, except `decisions/` (append-only).

## Allowed

| File | What | Rule |
|---|---|---|
| `BRIEF.md` | the commission record: original prompt (verbatim), end goal + acceptance criteria, clarification/directive/assumption log, decision register | see structure below; user quotes immutable, log append-only |
| `brief_source_condensed.md` | the CONDENSED commission source, used only when the full prompt was not transmitted verbatim — BRIEF.md's repair path quotes it and pins its whole-file sha256 | immutable source; referenced by BRIEF.md |
| `*.pdf` | doc-level mechanical/enclosure reference datasheet with no `02_parts/<MPN>` home (e.g. the enclosure drawing cited by the board-outline ADR) | reference only; cite by filename in the ADR |
| `ARCHITECTURE.md` | the high-level concepts: power tree, net domains, stackup, ground strategy, critical geometries | prose + diagrams; the "why". Machine-readable net facts belong in `03_src/rules/nets.yaml`, not here — link to it |
| `DETAIL_DESIGN.md` | the math: ripple, compensation, ampacity, thermal, tolerance | every number that a component value depends on, with its equation |
| `CHANGELOG.md` | one entry per revision | see structure below |
| `CHECKLIST.md` | the gate a revision must pass before release | |
| `decisions/` | one file per decision | see `decisions/contracts.md` |
| `renders/**` | TRACKED render pair per revision: `bare_<side>.png` (Cu+Mask+Silk fab view — the no-components truth) + the modeled twin renders. ALWAYS produced (SKILL stage 7); a bodiless modeled render means missing 3D model, never unpopulated — CPL is population ground truth (usb-hub-3s incident 2026-07-21) | committed |
| `journal/` | per-stage diary: append an entry at every stage start/iteration/finish | see `journal/contracts.md`; enforced by policy_audit M-JRNL |
| `learnings/` | per-stage harvest source, written at stage completion | see `learnings/contracts.md`; enforced by policy_audit M-LEARN at release |
| `contracts.md` | this file | |

## Forbidden

- Part datasheets or PDFs → `02_parts/<MPN>/`.
- Stock, price, availability → volatile; `06_build/cache/`, never committed as truth.
- Generated renders → `06_build/renders/`, EXCEPT the tracked
  `renders/**` pair above (bare + modeled board views — the one
  sanctioned committed-render set). Other committed images only if
  hand-drawn (block diagrams) with source in `03_src/`.
- Decisions inline in `ARCHITECTURE.md` — link to `decisions/NNNN-*.md` instead.
  Architecture says WHAT IS; decisions say WHY IT IS.

## Structure: `BRIEF.md` — the commission record

The file that answers, at any moment: *what did the user actually ask for,
what have they said since, what did we assume on their behalf, and are we
done?* It is the only file whose primary content is **user-sourced, verbatim,
and immutable**; everything the agent writes around those quotes is
bookkeeping and stays mutable.

The organizing rule — every requirement and every commission-level decision
must TRACE to exactly one of:

| Tag | Source | Mutability |
|---|---|---|
| `P` | the original prompt | verbatim, hashed, never edited |
| `D#` | a later user directive | verbatim, append-only |
| `Q#` | a clarification we asked + the user's answer | verbatim answer, append-only |
| `A#` | an assumption we declared instead of asking | append-only; supersedable by a later D#/Q# |

Required sections, in order:

### 1. Header block

```
status: draft | agreed | in-progress | delivered | superseded
prompt_sha256: <sha256 of the bytes between the prompt markers>
current_release: no | 07_releases/<dir>
```

### 2. `## Original prompt` — verbatim, immutable

The user's commissioning message, quoted exactly (typos included), between
`<!-- prompt-verbatim-begin/end -->` markers, with date and channel.

### 3. `## End goal — definition of done`

One paragraph, then the acceptance table:

```
| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | 3x USB-A outputs at 2.5 A max each | P | met — 07_releases/v1.0-... |
```

`Status` is `unmet`, `met — <evidence link>`, or `dropped — D#/Q#` (only a
user utterance can drop a criterion; an agent cannot).

### 4. `## Log` — directives, clarifications, assumptions (append-only)

Chronological entries, ids monotonic per type, prior entries never edited:

```
### D2 — 2026-07-16 — user directive
> verbatim quote
Impact: <what changed; link to files/ADRs/criteria>

### Q1 — <date> — clarification asked
Asked: <our question>
Answer: > verbatim user answer   (or: UNANSWERED — proceeding on A#n)
Impact: ...

### A1 — <date> — assumption (not asked)
Assumed: <the choice>  Authority: <e.g. P delegates design decisions>
Escalate if: <condition that should turn this into a real question>
```

### 5. `## Decision register` — the index of ALL decisions

| id | decision (one line) | decided by | depth |
|---|---|---|---|

`decided by` is `user (P/D#/Q#)` or `agent (A# / P-delegation)`. Engineering
decisions link their `decisions/NNNN-*.md`; commission-level ones link a log
entry. The register is an index — rationale lives in the linked file/entry.

## Validate — BRIEF.md

- `sha256sum` of the bytes between the prompt markers equals `prompt_sha256`
  (runnable: `sed -n '/prompt-verbatim-begin/,/prompt-verbatim-end/p' | sed '1d;$d' | sha256sum`)
- git history: section 2 and existing log entries byte-identical since the
  commit that introduced them (only appends and Status/Impact edits allowed)
- every `Source`/`Authority` tag (P, D#, Q#, A#) resolves to an existing
  prompt/log entry; log ids are monotonic with no gaps or renumbering
- every acceptance criterion `Status` is one of the three forms; every
  `dropped` cites a D#/Q# (never an A#)
- decision register ↔ `decisions/`: every ADR file appears in exactly one
  register row; every register row's depth link exists
- release gate: cutting a `07_releases/` dir while any criterion is `unmet`
  is a contract violation — `CHECKLIST.md` must carry this line

## Repair — BRIEF.md

- Original prompt lost or known only as a paraphrase → mark the section
  `UNVERIFIED (reconstructed)`, drop `prompt_sha256`, and ask the user to
  confirm the wording at the next contact. Never hash a reconstruction.
- A requirement found in ARCHITECTURE/code with no P/D/Q/A trace → someone
  invented it. Add an `A#` entry declaring it retroactively and flag it for
  the user, or remove the feature.
- A log entry edited after the fact (git shows it) → the log is no longer
  evidence; restore the original from history and append a correction entry.

## Structure: `ARCHITECTURE.md`

Required sections:
- `## Power tree` — every rail: source → conversion → load, with current.
  Name the nets exactly as they appear in `03_src/rules/nets.yaml`.
- `## Net domains` — the classes and what makes each one special. Link each
  to its `nets.yaml` entry. Do not restate widths here; they drift.
- `## Stackup` — layer count and what each layer is FOR.
- `## Ground strategy` — planes, splits, stitching, return-path intent.
- `## Critical geometries` — hot loops, Kelvin senses, differential pairs,
  keep-out intent. The things a router will destroy if it does not know.

## Structure: `DETAIL_DESIGN.md`

Every component value that came from a calculation gets: the equation, the
inputs, the result, and the chosen E-series value. Required coverage: switching
frequency, inductor ripple, output capacitance, feedback dividers, current
limits, compensation, UVLO/OV thresholds, and worst-case input current.
A value in the schematic with no line here is UNJUSTIFIED (validate below).

## Structure: `CHECKLIST.md`

The pre-release gate as literal checkboxes. Each line must be CHECKABLE BY A
FRESH AGENT: name the command to run or the file to inspect and the expected
result — "review the layout" is not a checklist line, "`bash 03_src/rebuild_all.sh`
ends `violations: 0`" is.

## Structure: `CHANGELOG.md`

Reverse-chronological. One entry per revision:

```
## v4.10 — 2026-07-14  [tag: v4.10]
- Current-tiered netclasses + enforced ampacity floors (DRC now gates width).
- HO_A rerouted around the SW_A pour; SW_B islands bridged on B.Cu.
Released: no
```

`Released:` is `no`, or the `07_releases/` dir name. It is the only link between
a revision and a fab order.

## Validate

- `BRIEF.md` passes its own Validate block (above)

- every net named in `ARCHITECTURE.md` exists in `03_src/rules/nets.yaml`
- every `CHANGELOG.md` entry has a git tag that exists
- every `Released:` value that is not `no` names an existing `07_releases/` dir
- no `decisions/` content duplicated into `ARCHITECTURE.md`
- `DETAIL_DESIGN.md` numbers match the values in `03_src/` (spot-check on review)

## Repair

- Net named in prose but absent from `nets.yaml` → the prose is stale OR the
  net is undeclared. Check the netlist to decide which, then fix that one.
- Rationale found inside `ARCHITECTURE.md` → extract to a new ADR, replace
  with a link.

## Compliance audit (design-policies.md IDs)

This folder answers: **S5** (design math with margins in DETAIL_DESIGN.md),
**M5-partial** (CHANGELOG entry naming every release directory), plus the
ADR obligations referenced throughout (protection ADR mandatory; split
planes, trunk-instead-of-pour, and any policy waiver each need a written
decision).

- Audit: run `policy_audit.py <project>` — M-REL includes the CHANGELOG
  check; S5 is HUMAN-graded (a fresh reviewer re-derives two values from
  DETAIL_DESIGN.md per the render-review protocol).
- A failing S5 spot-check (underivable value) reopens the design doc, not
  the board.
