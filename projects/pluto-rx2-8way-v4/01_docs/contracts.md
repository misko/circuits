# contract: 01_docs/

**Purpose** — everything a human must know that cannot be regenerated from
anything else. This is the most valuable folder in the project and the only
one that is unrecoverable if lost.

**Mutability** — hand-edited, except `decisions/` (append-only).

## Allowed

| File | What | Rule |
|---|---|---|
| `BRIEF.md` | the commission record: original prompt (verbatim), end goal + acceptance criteria, clarification/directive/assumption log, decision register | see structure below; user quotes immutable, log append-only |
| `ARCHITECTURE.md` | the high-level concepts: power tree, net domains, stackup, ground strategy, critical geometries | prose + diagrams; the "why". Machine-readable net facts belong in `03_src/rules/nets.yaml`, not here — link to it |
| `DETAIL_DESIGN.md` | the math: ripple, compensation, ampacity, thermal, tolerance | every number that a component value depends on, with its equation |
| `CHANGELOG.md` | one entry per revision | see structure below |
| `CHECKLIST.md` | the gate a revision must pass before release | |
| `findings.yaml` | single machine-readable findings/gates ledger; `project_state.py` derives maturity from it | hand-edited; every row names owner, closure condition and maturity boundary |
| `decisions/` | one file per decision | see `decisions/contracts.md` |
| `renders/**` | TRACKED render pair per revision: `bare_<side>.png` (Cu+Mask+Silk fab view — the no-components truth) + the modeled twin renders. ALWAYS produced (SKILL stage 7); a bodiless modeled render means missing 3D model, never unpopulated — CPL is population ground truth (usb-hub-3s incident 2026-07-21) | committed |
| `STATUS*.md` | the live STATUS beacon — the coordinator's between-gates progress signal, OVERWRITTEN at every transition | `STATUS.md` (single-board) or `STATUS-<board>.md` (multi-board, mirroring `journal/<stage>_<board>.md`); schema + audit below; read by `skills/kicad-pcb/scripts/pcb_status.py` |
| `journal/` | per-stage diary: append an entry at every stage start/iteration/finish | see `journal/contracts.md`; enforced by policy_audit M-JRNL |
| `learnings/` | per-stage harvest source, written at stage completion | see `learnings/contracts.md`; enforced by policy_audit M-LEARN at release |
| `<target>-mechanical.md` | **the board's ANALYSIS of a device it must mate with**: the tolerance stack, the mating strategy, what the geometry means for THIS board. One file per mating target. NOT a design doc and NOT a decision — it is where external evidence is reasoned about, and it belongs beside `BRIEF.md` because, like the brief, it is something the board must be true to | **the NUMBERS live in `spf/<device>/`, not here** (canon M-IMPORT, ADR-0005): the device record is the single home, `facts.yaml` its machine index, and `03_src/rules/mates.yaml` the board's reference. This file may quote them WITH their grade while it reasons; it may not be the only place one exists. Every number it does state must say how it was obtained — a bare dimension with no method is a defect |
| `sourcing/` | what to BUY for the self-supplied parts, and the evidence behind each number — dated, append-only, produced by `/shopping-list` | see `sourcing/contracts.md`; governed by canon M-QUOTE |
| `contracts.md` | this file | |

## Forbidden

- Part datasheets or PDFs → `02_parts/<MPN>/`.
- Stock, price, availability → volatile; `06_build/cache/`, never committed as
  truth. **The one carve-out is `sourcing/`**, and it is a carve-out for
  PROVENANCE, not for the numbers: a dated shopping list, every figure stamped
  with its M-IMPORT grade and the URL/date it was read from, is an OBSERVATION —
  the same shape as a journal entry. It is committed as *what a distributor said
  on a day*, never as *what is true*, it is never re-consumed by a build, and
  the raw responses stay in `06_build/cache/`. Anything without that stamping
  is still forbidden here.
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

### 6. `## Spec tensions` — requirements vs standards + sourceable parts (D-SPEC)

Every numeric requirement tested at COMMISSION against (a) the governing
standard and (b) the sourceable-part envelope; every power port/output pins
its voltage ENVELOPE (min/max), not just current. The table reads
`none found` ONLY after the D-SPEC check actually ran:

```
| id | requirement | standard/part cap | how honoured | ADR | user-flagged |
|---|---|---|---|---|---|
| T1 | USB-C 5A | Type-C 3A CC / PD 5V/5A | 5V/5A protection-ceiling reading | decisions/0005-... | yes |
```

Each tension links a spec-tension `decisions/NNNN-*.md` and is flagged to the
user in the report — never silently built out-of-spec, never silently
downgraded. Machine-readable rail envelopes go to `03_src/rules/power_tree.yaml`
(the E-TOPO input), not here.

### 7. `## Mating fact-lock` — foreign geometry graded BEFORE the floorplan (D-MATE)

Present when the board mates to hardware this repo did not design. Every
dimension the floorplan consumes from outside appears here with its **M-IMPORT
grade** (MEASURED / CITED / ESTIMATED+bar / OWED), where it is spent, and the
mating budget it is spent against. The facts live ONCE in `spf/<device>/`;
this table is the user-facing lock and `03_src/rules/mates.yaml` is the machine
copy — the same relationship the Commission fact-lock has with
`power_tree.yaml`, and the reason neither table may restate a number that has a
home elsewhere.

`none — this board does not mate to hardware this repo did not design` closes
the section; SILENCE DOES NOT. ADR-0005, 2026-07-27: an SMA span extracted from
an undimensioned vector assembly plot read 35.60 mm with three independent
extractions agreeing to 0.003 mm, and a caliper on two physical units then read
35.04 and 34.72 mm — 10-18x the ±0.05 mm mating window, and both a floorplan
and a $101 adapter order were ready to be built on the plot. Precision about a
proxy is not accuracy about the object.

### 8. `## Commission fact-lock` — load-derived facts locked BEFORE architecture

A table (template in `templates/01_docs/BRIEF.md`) pinning, per output rail:
Vout min-max @ Imax, the input envelope + source type, the protection posture,
the off-control/storage answer, and each spec-critical function's sourcing
class. Every row cites its lock (`Q#/A#` user-confirmed, or `D#/A#` explicit
conservative assumption) — a blank or silently-inferred row fails Validate.
Added 2026-07-23: the two facts left unlocked on usb-hub-3s (output voltage
range, protection posture) caused two generation restarts (~27/53 commits).
The table mirrors `power_tree.yaml`; the yaml feeds the machine gates, the
table is the user-facing commitment.

## Validate — BRIEF.md

- `sha256sum` of the bytes between the prompt markers, **with the FINAL
  NEWLINE STRIPPED**, equals `prompt_sha256`. That newline is `sed`'s line
  terminator, not part of the prompt, and the commission computes the digest
  without it — so the command must drop it or it can never reproduce the value
  it is checking. Runnable, and verified against the recorded hash of
  `pluto-rx2-8way` (the most recent commission):
  `sed -n '/prompt-verbatim-begin/,/prompt-verbatim-end/p' 01_docs/BRIEF.md | sed '1d;$d' | head -c -1 | sha256sum`
  Without `head -c -1` EVERY board's check disagrees with its own recorded
  hash, which trains the reader to ignore the one check that proves the
  commission was not rewritten (2026-07-28)
- git history: section 2 and existing log entries byte-identical since the
  commit that introduced them (only appends and Status/Impact edits allowed)
- every `Source`/`Authority` tag (P, D#, Q#, A#) resolves to an existing
  prompt/log entry; log ids are monotonic with no gaps or renumbering
- the Commission fact-lock table exists with no blank `Locked by` cell —
  every row resolves to a Q#/A#/D# entry (or names the ledger/sourcing-spike
  evidence for the hard-cell row)
- every acceptance criterion `Status` is one of the three forms; every
  `dropped` cites a D#/Q# (never an A#)
- decision register ↔ `decisions/`: every ADR file appears in exactly one
  register row; every register row's depth link exists
- `Spec tensions` table present; each row links an existing
  `decisions/NNNN-*.md` and is flagged in the report; `none found` allowed
  only after the D-SPEC check ran
- `Mating fact-lock` present: either every foreign dimension with its
  M-IMPORT grade + a matching `03_src/rules/mates.yaml`, or the explicit
  "does not mate" line. A declared lock with no yaml is a D-MATE FAIL
  (`import_provenance_check.py`) — a user-facing grade nothing checks
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
- `## Power tree` — every rail: source → conversion → load, with current AND
  its voltage ENVELOPE (vin/vout min-max) — an unpinned output voltage range
  lets converter topology be interpreted instead of derived. Name the nets
  exactly as they appear in `03_src/rules/nets.yaml`. Machine-readable rail
  envelopes (vin/vout min-max, iout, converter) belong in
  `03_src/rules/power_tree.yaml` (the E-TOPO / E-MARGIN / E-OFF input — also
  per-rail `load_uv_threshold`/`ir_budget_mohm` for a rail feeding a known
  load, and top-level `source_type`/`off_control`/`quiescent_ua` for a battery
  source), not here — link to it.
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

## Structure: `STATUS*.md` — the live beacon (coordinator progress signal)

The between-gates progress signal (SKILL.md "Journal discipline"). Agents
otherwise signal only at coarse GATE boundaries (schematic/routing/seal), so a
coordinator could not tell "one tap from done" from "stalled" without reading a
multi-MB transcript (usb-hub-3s-v3 v1.2 incident, 2026-07-23). The beacon is the
LIVE HEAD of the journal: it is OVERWRITTEN at every transition, while
`journal/` stays append-only history. `STATUS.md` for a single-board project;
`STATUS-<board>.md` per board for a multi-board project (mirroring the per-board
`journal/<stage>_<board>.md` suffix).

Everything the reader consumes is `key: value`, one field per line (`#` lines
and blanks ignored). Seven fields, all required:

```
stage:   routing            # commission|parts|schematic|placement|routing|verify|seal
step:    "widen R12.1 escape; rebuildE running"   # the thing happening NOW
measure: "route 0/0/0; 1 fragile tap (R12.1)"     # last MEASURED numbers
state:   working            # working | blocked | done
next:    "if R12.1 clears -> DRC gate"
op_pid:  3588               # pid of the running long op, or empty when idle
updated: 2026-07-23T11:59:24
```

`state` vocabulary: `working` (progressing — coordinator POLLS, never
interrupts), `blocked` (a decision or D-BACK wall the agent PUSHED up — the
coordinator acts), `done` (this stage's gate is green). `stage` vocabulary is
the seven pipeline stages above. The reader
(`skills/kicad-pcb/scripts/pcb_status.py`) DERIVES a STALLED verdict from
`state: working` + `updated` older than its threshold + no live `op_pid`; a live
`op_pid` overrides staleness (a long route legitimately runs while the beacon
sits). The template seed is `skills/pcb-design/templates/01_docs/STATUS.md`.

**PERMITTED STRUCTURE — exactly one occurrence of each of the seven fields.**
The file is a FRAME, not a log: it is rewritten whole, so a second `stage:` (or
`step:`, `measure:`, `state:`, `next:`, `op_pid:`, `updated:`) means someone
APPENDED where the contract says OVERWRITE. The reader takes the LAST value of
each field, so an appended file does not look broken — it renders a frame
nobody wrote, mixing two moments in time. Extra `key:` lines outside the seven
are IGNORED by the reader and must not be used to carry content: narrative that
needs a home goes to `journal/<stage>.md`, which is append-only and is where
history belongs (one beacon had grown 20 such keys precisely because its stage
had no journal file).

**A SEALED BEACON NAMES THE LIVE RELEASE.** Which release is live is a property
of `07_releases/` — the newest of THIS board's own series with no
`SUPERSEDED.md` — so a beacon stating it is a SECOND HOME for a fact that
already has an authoritative one, and second homes drift. It is kept anyway
(the human reading `step:` needs the version in the sentence) and MACHINE-
CHECKED against the tree; it is never the only place the fact lives. Refreshing
it is step 4 of the seal procedure in the `07_releases/` contract: **a seal is
not complete until the beacon names the release it just created.**

## Validate — STATUS*.md

**Audit: `/usr/bin/python3 skills/kicad-pcb/scripts/status_beacon_check.py
<project>`** (or `--root <repo>` for the whole fleet) — canon **M-BEACON**,
exit 0 required. It grades every `01_docs/STATUS*.md` and prints an `N/M`
denominator per property; a beacon it cannot parse is a FAIL, never a skip.
The four findings, and what each means:

| finding | means | repair |
|---|---|---|
| `M-BEACON-DUP` | a field appears twice — the file was APPENDED to. The reader's last-wins rule has been reporting a frame nobody wrote | rewrite the frame WHOLE; move the retired frame's content to `journal/<stage>.md` if it has no other home |
| `M-BEACON-FIELD` | a required field is missing. Not cosmetic: a missing `updated:` makes `M-BEACON-AGE` unevaluable, and unevaluable input is a FAIL (canon M-COVER) | add the field; if `updated:` is unknown, the beacon is not a beacon |
| `M-BEACON-REL` | the beacon claims a COMPLETED seal but names a release that is not the live one (usually the predecessor, because the seal did not refresh it) | overwrite `step:` to name the live release; then ask why the seal ritual's step 4 was skipped |
| `M-BEACON-AGE` | `updated:` predates the board's newest seal — stale by construction, whatever the text says | refresh the whole frame, not just the timestamp |

Also true, and checked by eye rather than by that gate:

- exactly the seven fields present, one `key:` per line; `stage`/`state` values
  are in the vocabularies above (a value outside them renders as `?` in
  `pcb_status.py`)
- `updated` parses as ISO-8601 (`YYYY-MM-DDTHH:MM:SS`); `op_pid` is empty or an
  integer
- runnable: `pcb_status.py --root <repo>` lists the board with a non-`?` stage
  and a derived state column (a beacon it cannot parse shows `?`/STALLED, never
  a false green)
- the beacon is OVERWRITTEN, not appended (git history shows a single evolving
  frame, not accumulating entries — the append-only record is `journal/`)
- a beacon whose `measure:` is a claim with no gate output behind it is a defect
  in review, same rule as a journal entry

**A FAILING M-BEACON IS NOT A COSMETIC DEFECT.** The beacon is the
coordinator's only between-gates eye, and a stale one does not go blank: it
keeps reporting a superseded release as live, in a frame that reads
`sealed / done`. Measured 2026-07-27, before the gate existed: every beacon in
the fleet named the wrong release.

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
**S9** (spec tensions surfaced at commission — [H] BRIEF `Spec tensions`
table filled + a spec-tension ADR per tension), **M5-partial** (CHANGELOG
entry naming every release directory), **M9 / M-BEACON** (`journal/` +
`learnings/` per stage, and the live head `STATUS*.md` agreeing with the tree —
`status_beacon_check.py`), plus the ADR obligations referenced
throughout (protection ADR mandatory; split planes, trunk-instead-of-pour,
and any policy waiver each need a written decision). A protection/topology
ADR is not complete until it emits >= 1 assertion into
`03_src/rules/electrical_invariants.yaml` (canon E-INV); **E-ADR** flags a
protection ADR that emits none. **A SUPERSEDED ADR IS EXEMPT** — E-ADR skips
any ADR whose front-matter `status:` starts with `superseded`, so a reversed
decision is not asked to assert a topology that no longer exists. SUPERSEDE
BY STATUS, never by retagging: deleting a live ADR's `protection`/`topology`
tag to quiet the checker leaves the decision record lying to the next reader. For a self-powered board the protection ADR
must also settle OFF-CONTROL (de-energization) + stored quiescent draw,
emitted to `03_src/rules/power_tree.yaml` where **E-OFF** gates it; a regulated
rail feeding a known load pins its `load_uv_threshold` + `ir_budget_mohm` there
for **E-MARGIN**.

- Audit: run `policy_audit.py <project>` — M-REL includes the CHANGELOG
  check; S5 is HUMAN-graded (a fresh reviewer re-derives two values from
  DETAIL_DESIGN.md per the render-review protocol).
- A failing S5 spot-check (underivable value) reopens the design doc, not
  the board.
