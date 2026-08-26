# contract: 08_reviews/

**Purpose** — the project's review record: every design review this board
receives — red-team release reviews, fresh-context pin/render verdicts,
EXTERNAL reviews (human or LLM) — archived VERBATIM with provenance, plus
the disposition ledger tracing every finding to its outcome. The most
consequential document a board ever receives is often a review; before this
folder existed, the review that forced usb-hub-3s v1.1 lived only in a chat
window (2026-07-21) — the knowledge-evaporation failure mode, review
edition.

**Mutability** — review files are APPEND-ONLY EVIDENCE (verbatim, never
paraphrased or edited — same discipline as BRIEF prompts; a wrong review is
dispositioned as refuted, not rewritten). `DISPOSITIONS.md` is the mutable
index.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `DISPOSITIONS.md` | the living findings ledger — REQUIRED once any review exists |
| `<date>_<subject>_<source>_<lens>.md` | one review, verbatim (e.g. `2026-07-21_v1.0_redteam_topology.md`, `2026-07-21_v1.0_external-llm_full.md`) |

## Review file structure

Header block, REQUIRED:

    subject: <project> <release-version-or-git-sha reviewed>
    date: YYYY-MM-DD
    reviewer: <redteam-agent (model, lens) | external (who/what) | pin-review | render-review>
    context-given: <zero-context | release-archive-only | full-tree | unknown (external)>
    design_verdict: <SOUND | DEFECTIVE>
    order_verdict:  <ORDER | DO-NOT-ORDER | BLOCKED-SOURCING>

Then the review body VERBATIM. For external reviews received through a
person, note the transmission path; never edit the content.

### TWO verdict keys, because a seal makes TWO claims (canon M-REV)

A review used to carry ONE `verdict:` field, and it was asked to answer two
different questions at once:

| claim | the question | who can answer it | the key |
|---|---|---|---|
| *this design is correct* | may it SEAL? | the design gates + the lens, at SEAL time | `design_verdict` |
| *this design is orderable* | may it be BOUGHT today? | the CATALOG, at ORDER time | `order_verdict` |

`BLOCKED-SOURCING` exists precisely so a lens can say **"this board is right
and you cannot buy it today"** without either half contaminating the other.
The vocabularies are CLOSED and the value is read as DATA — the first token
after the colon. Prose is not a verdict: `VERDICT AT RUN TIME: **DO NOT
ORDER.**` states none, and is reported as stating none (crediting prose is
the R-LEN word-credit defect). A missing or out-of-vocabulary verdict is a
FAIL, never a skip.

**Which key each consumer reads:**

- the **seal gate** reads `design_verdict` — `DEFECTIVE` blocks the seal
  exactly as `DO-NOT-ORDER` always did. The split adds a dimension; it adds
  no way past a design-side red.
- the **ORDER_README** reads `order_verdict` — it is the buyer's document,
  and `DO-NOT-ORDER` / `BLOCKED-SOURCING` belong on its first screen beside
  the `SOURCING:` gate line (07_releases contract, canon A-BUY).

**LEGACY RETROFIT (non-breaking, and deliberately CONSERVATIVE).** Reviews
written before this split carry a single `verdict:`, and they map to BOTH
keys rather than being invalidated — 07_releases is immutable, so retro-
editing sealed archives to a new vocabulary is a retro-fill by another name:

| legacy `verdict:` | `design_verdict` | `order_verdict` |
|---|---|---|
| `ORDER` | SOUND | ORDER |
| `PASS` / `PASS-WITH-NOTES` | SOUND | *unstated* — a readability/pin verdict never asserted orderability |
| `DO-NOT-ORDER` / `FAIL` | DEFECTIVE | DO-NOT-ORDER |

A refusal stays a refusal: **no existing review is retroactively converted
into an acceptance.** The split gives the NEXT reviewer the vocabulary; it
does not re-adjudicate the last one. New reviews write both keys.

**WHY THIS COST A BOARD ITS SEAL.** smc0985-cooksense v1.7 reached DRC
0/0/0, `policy_audit` FAIL=0 and both red-team lenses graded, and its
topology re-gate wrote, verbatim: *"I would accept the seal ... **but
sealing is not the question this verdict field asks.** The question is
whether this release can be ordered, and it cannot."* The reviewer would
seal, the gate read `verdict:`, `verdict:` meant *orderable*, and eight
successive sealing passes declined. The lens and the gate did not disagree
about anything physical.

## DISPOSITIONS.md structure

One row per finding, across ALL reviews (the review-side decision
register):

    | id | review file | finding (one line) | severity | verification | disposition |

- `severity`: `P0` / `P1` / `P2` (SKILL.md stage 7) — a P0 blocks the
  release; a P1 lands in ORDER_README + the next-rev work order; a P2 is
  recorded. There is no other severity vocabulary.
- `verification`: findings are CLAIMS — each is independently verified
  against the artifacts (netlist/board/part.yaml) before disposition:
  `confirmed (evidence)` / `refuted (evidence)` / `unverifiable-here`.
- `disposition`: `fixed — <release/commit link>` / `deferred — <ADR /
  ORDER_README / next-rev work-order link>` (a P1 lands here) / `waived —
  <evidence>` / `recorded — <note>` (a P2 lands here) / `duplicate of <id>`.

## Gates

- **A release may not seal while any CONFIRMED P0 finding lacks a `fixed`
  disposition** (red-team stage, SKILL.md stage 7).
- **Per sealed release, BOTH red-team lenses must be present with a
  `design_verdict: SOUND`** — a `redteam` topology/protection/ratings-lens
  review AND a `redteam` layout/thermal/power-integrity-lens review file
  (reviewer: `redteam-agent` with the named lens), each carrying both
  verdict keys in its header block. `design_verdict: DEFECTIVE` blocks the
  seal until re-gated or superseded (SKILL.md stage 7).
- **`order_verdict` does NOT block the seal — it blocks the ORDER**, and it
  is cross-checked against the release's own shipped stock evidence in both
  directions (canon M-REV + A-BUY): a lens may not grade `ORDER` on a
  release measured `SOURCING: BLOCKED`, nor `BLOCKED-SOURCING` on one where
  every coded, placed line clears its build quantity. BLOCKED-SOURCING is a
  MEASUREMENT, not a mood, and an unfounded one costs the buyer a real
  order.
- The release's red-team reviews are written HERE first (the living
  tracked home) and COPIED into the release `verification/` as the sealed
  snapshot **under the two contract-named filenames** `redteam_topology.md`
  and `redteam_layout.md` — those exact names are what M-REV grades, and
  deliberately not a `redteam*.md` glob, because releases archive dated
  reviews of EARLIER versions beside them and grading a v1.0 review's
  verdict against a v1.12 release is the adjacent-property error.
- Audit: every `DISPOSITIONS.md` row links an existing review file; every
  review file has the header block; every P0/P1 row has a non-empty
  disposition; both red-team lenses present with `design_verdict: SOUND`.
  Machine check: **M-REV** (`release_freshness_check.py <release_dir>`
  check (g)) — the field the contract has demanded since it was written and
  that nothing parsed for its whole history. MEASURED 2026-07-30, with its
  denominator: of 33 sealed release dirs, 21 ship both named lens files, and
  **9 of those 21** carry an ungradeable verdict on at least one lens (5 with
  no verdict KEY at all, 8 with a value outside every vocabulary, overlap 4).
  Only 12 of 21 parse. The commonest defect is `verdict: DO NOT ORDER`
  written as prose after the colon — first token `DO`. cooksense v1.5's
  shipped `redteam_layout.md` does not use the key at all: line 5 reads
  `VERDICT AT RUN TIME: **DO NOT ORDER.**`, a sealed release carrying a
  DO-NOT-ORDER review nobody read. A prose rule eventually gets skipped
  (canon M2).
