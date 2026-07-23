# ADR-0003 (repo) — the STATUS beacon: an overwritten per-board progress signal, polled

Status: **accepted** 2026-07-23
Scope: cross-project / pipeline. Governs how a coordinator observes a board's
progress BETWEEN gate boundaries. Binds the pcb-design skill (Journal
discipline) and adds a reader to the kicad-pcb skill's scripts.

## Problem — coarse gate-only signalling leaves the coordinator blind

Agents driving `/pcb-design` signal at the coarse GATE boundaries the pipeline
already defines: the schematic gate, the routing gate (DRC 0/0/0), the seal.
Those are minutes-to-hours apart. BETWEEN them the coordinator had no cheap
read of where a board actually was: "one tap from done" and "stalled on a wall"
were indistinguishable without opening a multi-megabyte transcript and inferring
state from the last tool calls. We hit this concretely on usb-hub-3s-v3 v1.2
(2026-07-23) — a routing grind that was one escape-widen from the DRC gate was,
from outside, indistinguishable from a run that had quietly wedged.

The journal (`01_docs/journal/<stage>.md`, canon M9) already captures the hard
analysis, but it is APPEND-ONLY HISTORY optimised for the post-mortem reader,
not a glanceable "where is it now" — you still have to read to its tail and
judge whether the tail is fresh.

## Decision — a live, overwritten beacon + a reader; poll progress, push walls

1. **Each board carries a tiny `01_docs/STATUS.md` beacon** — the LIVE HEAD of
   the journal — that the agent **OVERWRITES** (never appends) at every stage
   enter/finish, every iterate, and immediately BEFORE and AFTER every long
   blocking op. Seven `key: value` fields: `stage`, `step`, `measure` (last
   MEASURED numbers), `state` (`working`|`blocked`|`done`), `next`, `op_pid`
   (the running long-op pid, or empty), `updated`. The append-only journal is
   unchanged — the beacon is its current frame, not a replacement. Multi-board
   projects carry one per board (`STATUS-<board>.md`), mirroring the existing
   per-board `journal/<stage>_<board>.md` suffix.

2. **The coordinator reads with `pcb_status.py`**, not by peeking at
   transcripts. It scans `projects/*/01_docs/STATUS*.md` and prints one line per
   board, DERIVING the traffic light: `working` + fresh + a live `op_pid` =
   progressing; `working` + stale `updated` + no live `op_pid` = STALLED;
   `blocked` = an escalated wall; `done` = terminal. A live `op_pid` overrides
   staleness, because a long route legitimately runs for many minutes while the
   beacon sits — which is why the beacon records `op_pid` before a long op and
   clears it after.

3. **The signalling split is load-bearing.** Routine progress flows to the
   BEACON and the coordinator **POLLS** it (never interrupting a live op). A
   genuine DECISION or a D-BACK wall is not beacon traffic — the agent STOPS,
   sets `state: blocked`, and **PUSHES** an escalation up. Progress is pulled;
   only walls are pushed.

## Alternatives rejected

- **Greppable `PROGRESS:` lines in the append-only journal.** Keeps one file,
  but the coordinator must then read to the tail AND decide whether the tail is
  current — the exact judgement we are trying to remove — and an append-only log
  grows without bound while only its last line is ever "the state". A single
  overwritten frame is O(1) to read and unambiguously current; history stays in
  the journal where it belongs.

- **Per-step push via SendMessage (agent notifies the coordinator each step).**
  A push can't fire from INSIDE a blocking op — the poll-to-completion route/
  grind loop is precisely where the coordinator most needs a signal, and that
  loop holds the thread until it returns, so no per-step message escapes it. The
  beacon is written before the loop (with `op_pid`) and the loop tees its last
  line into `measure`, so a POLL sees current state mid-grind without the agent
  having to emit anything. Push is reserved for the rare wall, where stopping is
  the point.

## What this is NOT (yet)

There is **no enforcing `policy_audit` gate** for the beacon. An optional STATUS
gate (freshness at commit, schema at release) is a deliberate follow-up, left
out here so the mechanism can prove itself coordinator-facing first. Today the
beacon is validated by its reader (`pcb_status.py`) and the 01_docs contract's
Validate block, and pinned by `tests/t1_status.py` (the reader's STALLED-vs-
fresh-vs-done classification, RED-verified against a broken age test).

## Reversibility

Additive. The beacon is a new optional file; boards without one simply do not
appear in `pcb_status.py` output (it announces "no beacons found"), and the
append-only journal — the canonical record — is untouched. Removing the
mechanism is deleting one script, one template, one contract block, and the
Journal-discipline paragraph; nothing downstream depends on it.
