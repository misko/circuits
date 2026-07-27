# brief: <board>

status: draft
prompt_sha256: <fill after pasting the prompt — see 01_docs/contracts.md>
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
> PASTE THE USER'S COMMISSIONING MESSAGE HERE, EXACTLY, TYPOS INCLUDED.
<!-- prompt-verbatim-end -->

- date: YYYY-MM-DD
- channel: <where it was said>

## End goal — definition of done

One paragraph: what exists when this project is finished, and for whom.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | ... | P | unmet |

## Spec tensions (D-SPEC — fill at commission, before architecture)

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | ... | ... | 01_docs/decisions/NNNN-*.md | yes/no |

(none is a valid answer — write "none found" after actually checking.)

## Commission fact-lock (D-SPEC — confirmed BEFORE architecture)

The load-derived facts that pick topology and protection. Every row is
user-confirmed (Q#/A#) or an explicit conservative assumption (D#/A#) —
never inferred silently. Two unlocked rows (output V range, protection
posture) cost one family two generation restarts (usb-hub-3s, 2026-07-23).
Mirrors `03_src/rules/power_tree.yaml` (the E-TOPO/E-MARGIN/E-OFF input) —
this table is the USER-FACING lock; the yaml is the machine copy.

| Fact | Value | Locked by |
|---|---|---|
| Output rail(s): Vout min-max @ Imax | ... | Q#/A#/D# |
| Input envelope: Vin min-max, source type | ... | Q#/A#/D# |
| Protection posture (defended failures + escalation boundary) | ... | Q#/A#/D# |
| Off-control / storage (how it de-energizes; quiescent budget) | ... | Q#/A#/D# |
| Hard-cell parts (spec-critical functions): sourcing class a/b/c | ... | ledger / sourcing spike |

## Mating fact-lock (D-MATE — fill at commission when this board mates to hardware this repo did not design)

Every dimension the floorplan will consume from foreign hardware, with its
**M-IMPORT grade**. The facts live ONCE, in `spf/<device>/`; this table names
them for a reader and `03_src/rules/mates.yaml` is the machine copy — exactly
the relationship the Commission fact-lock has with `power_tree.yaml`.

Grades: **MEASURED** (someone touched the object, or read a machine-readable
source) · **CITED** (a vendor document, with figure/page/section) ·
**ESTIMATED** (derived, photogrammetric, inferred — and it MUST carry an error
bar before it may be spent on a dimension) · **OWED** (nobody has this number;
say how to get it, and do not design against it).

| Fact (`spf/<device>` id) | Grade | Error bar | Where it is spent | Mating budget it is spent against |
|---|---|---|---|---|
| ... | MEASURED | — | floorplan anchor X coords | ±0.25 mm SMP float |

`none — this board does not mate to hardware this repo did not design` is a
valid answer, and the only one that closes this section. Silence is not a
declaration: a proxy measured beautifully is still a proxy (an SMA span read
off an undimensioned plot, three extractions agreeing to 0.003 mm, was 0.56 mm
from the physical object — ADR-0005).

## Log

(append-only — see 01_docs/contracts.md for entry formats: D# directive,
Q# clarification, A# assumption)

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
