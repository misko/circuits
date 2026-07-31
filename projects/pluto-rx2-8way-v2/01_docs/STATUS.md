# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame. Rewrite it at every stage enter/finish, every iterate, and IMMEDIATELY
BEFORE and AFTER every long blocking op (see SKILL.md "Journal discipline").

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

Multi-board projects: one beacon PER board, named `STATUS-<board>.md`
(mirroring the per-board `journal/<stage>_<board>.md` suffix). A single-board
project uses this bare `STATUS.md`.

## Schema

| field | meaning | vocabulary |
|---|---|---|
| `stage` | which pipeline stage the board is in | `commission` \| `parts` \| `schematic` \| `placement` \| `routing` \| `verify` \| `seal` |
| `step` | the specific thing happening RIGHT NOW, one line | free text |
| `measure` | the last MEASURED numbers (gate output, counts) — never hope | free text; the rebuild loop tees its last line here |
| `state` | the coordinator's traffic light | `working` (progressing) \| `blocked` (STOPPED, escalated to coordinator) \| `done` (this stage's gate is green) |
| `next` | what happens on the next transition | free text |
| `op_pid` | pid of the running long op, or empty when idle | integer or empty |
| `updated` | when this frame was written, ISO-8601 local | `YYYY-MM-DDTHH:MM:SS` |

`state: working` + a fresh `updated` + a live `op_pid` = progressing (coordinator
POLLS, does not interrupt). `state: working` + a STALE `updated` + no live
`op_pid` = STALLED (the reader flags it). `state: blocked` = a decision or
D-BACK wall the agent has PUSHED up — the coordinator acts. `state: done` =
terminal for this stage.

<!-- reader parses from here down -->
stage:   verify
step:    "PHASE 1 DONE: the via fence is closed as far as the lever reaches. Declared stitch_grid pitch 0.95 = floor_0.05(1.35/sqrt(2)) — a square lattice at p is NOT a fence at p, it projects at p*sqrt(2) on a 45-degree arm. Next: Phase 2, re-seed rebuild_all.sh from the template and prove the full driver end-to-end."
measure: "FENCE MEASURED OFF THE BOARD (06_build/verify/fence_pitch.txt): 2208 grid vias + 40 SMA PTH ground posts; worst STRUCTURAL along-arm projection 1.3435 mm vs the 1.35 bound (was 1.9092 at a declared 1.35, 2.8284 derived at the shipped 2.0). 12 of 21 arm-sides still over, EVERY ONE a named site occupancy (SMA avoid rings worst 5.1071 at J_ANT8; the SSE control corridor 3.6200 at ANT4; the star hub 1.8803) - classified in 06_build/verify/fence_apertures.txt. DRC re-established: 0 violations / 0 unconnected / 0 parity, BOTH LISTS EMPTY (Counter() on each), --severity-all --refill-zones --schematic-parity, 2026-07-30T18:35:24."
state:   working
next:    "Phase 2 re-seed the driver; Phase 3 battery + two-key red-team + seal. The residual fence apertures go into the red-team brief VERBATIM so an independent lens grades them, not the designer."
op_pid:
updated: 2026-07-30T20:05:00
