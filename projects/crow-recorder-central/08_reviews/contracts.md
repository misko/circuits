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
    verdict: <ORDER | DO-NOT-ORDER | PASS | PASS-WITH-NOTES | FAIL>

Then the review body VERBATIM. For external reviews received through a
person, note the transmission path; never edit the content.

## DISPOSITIONS.md structure

One row per finding, across ALL reviews (the review-side decision
register):

    | id | review file | finding (one line) | severity | verification | disposition |

- `verification`: findings are CLAIMS — each is independently verified
  against the artifacts (netlist/board/part.yaml) before disposition:
  `confirmed (evidence)` / `refuted (evidence)` / `unverifiable-here`.
- `disposition`: `fixed — <release/commit link>` / `deferred — <ADR or
  ORDER_README link>` / `waived — <evidence>` / `duplicate of <id>`.

## Gates

- **A release may not seal while any CONFIRMED P0 finding lacks a `fixed`
  disposition** (red-team stage, SKILL.md stage 7).
- The release's red-team reviews are written HERE first (the living
  tracked home) and COPIED into the release `verification/` as the sealed
  snapshot.
- Audit: every `DISPOSITIONS.md` row links an existing review file; every
  review file has the header block; every P0/P1 row has a non-empty
  disposition. (Candidate machine check: M-REV in policy_audit.)
