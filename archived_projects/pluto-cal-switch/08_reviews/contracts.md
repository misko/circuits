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
- **Per sealed release, BOTH red-team lenses must be present with an ORDER
  verdict** — a `redteam` topology/protection/ratings-lens review AND a
  `redteam` layout/thermal/power-integrity-lens review file (reviewer:
  `redteam-agent` with the named lens), each carrying `verdict: ORDER` in
  its header block. A `DO-NOT-ORDER` verdict blocks the seal until re-gated
  or superseded (SKILL.md stage 7).
- The release's red-team reviews are written HERE first (the living
  tracked home) and COPIED into the release `verification/` as the sealed
  snapshot.
- Audit: every `DISPOSITIONS.md` row links an existing review file; every
  review file has the header block; every P0/P1 row has a non-empty
  disposition; both red-team lenses present with ORDER verdicts. (Candidate
  machine check: M-REV in policy_audit — makes the two-lens coverage
  enforceable, not prose-only, per canon M2.)
