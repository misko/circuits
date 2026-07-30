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
stage:   schematic
step:    "SCHEMATIC GATE GREEN — planned handoff at the declared boundary. Next agent starts at stage 5 (floorplan)."
measure: "ERC 0 errors/183 warnings (baselined) | TSX-PRE 6/6 | S-COUNT 28/28 over 3 source pairs | S-NETMERGE 23/23 | E-INV 20/20 | E-ADR 1/1 | E-TOPO 1/1 rails (PD 202mW of 400, 50%) | E-MARGIN PASS | E-OFF N-A stated | M-BOM legC PASS | E-NETREF 78/78 0 ghost | M-BOUND 1 CITED | M-BEACON 1/1 | contracts_audit 0. ALL EXIT 0, ALL RUN UNPIPED."
state:   done
next:    "OWED before stage 5: (1) the RP2040_Zero_LCC23_18x23.5 footprint in 03_src/lib -- the FPID is referenced and the file does not exist; (2) 03_src/floorplan.yaml + route.yaml, deliberately NOT written (v2's star surroundings differ from v1's); (3) commit the two Waveshare PDFs into 02_parts/RP2040-Zero. FIRST ACT of stage 5 is the OCTILINEAR FLOOR from v2's own pads -- do NOT inherit v1's 1.4966 mm."
op_pid:
updated: 2026-07-30T12:10:00
