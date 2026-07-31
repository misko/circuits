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
step:    "PHASE 3 BLOCKED AT THE SEAL, two independent walls. (1) A-ROT: three LCSC codes need a measured rotation row and the authority table lives under skills/, outside this board partition — the three rows are MEASURED and reported as a patch. (2) policy_audit P-ADJ FAIL: two real placement findings, U_SW.12->R_PD4.1 7.96mm of 4.0 and the RX1 pickoff branch. Two red-team lenses running."
measure: "STAGING BATTERY, all UNPIPED: DRC 0/0/0 both lists EMPTY - bom_source_check PASS - F-LEGIBLE OK 13 checks - stock PASS 11/11 at >=5x - P-FACT 6/8 graded 2 UNREACHED named - jlc_twin 25 OK, bodies 27/27, 1 critical (LED_ST POLARITY-FIT, resolved by hand to offset 0) - A-RENDER twin_overlay OK, 11 measurable bodies within 1.00mm - A-POP 1 finding left (MANIFEST) - policy_audit FAIL=3 PASS=29 WAIVED=3. FENCE: 0.95mm lattice, worst structural along-arm 1.3435 vs bound 1.35, 12 of 21 arm-sides carry a NAMED occupancy aperture."
state:   blocked
next:    "COORDINATOR ACTION: land three rows in skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv (C2286,0,two-channel; C504007,0,two-channel; C5121458,0,single-channel + order-preview human gate) — evidence in 01_docs/journal/05_verify.md. Then re-export WITHOUT --allow-unsourced-rotations (CPL will be byte-identical, all three offsets are 0), disposition the two P-ADJ findings, write MANIFEST + ORDER_README, 2-commit seal, refresh this beacon."
op_pid:
updated: 2026-07-30T21:00:00
