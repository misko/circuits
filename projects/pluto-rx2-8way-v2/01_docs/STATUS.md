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
stage:   routing
step:    "PLANNED HANDOFF at ~93% context. The RF P0 is CLOSED and MEASURED: the RX1 pickoff is now IN LINE with the through path (routed stub 0.0000 mm, R_T1.1 perpendicular 0.0100 mm vs a DERIVED lambda_g/16 = 1.8129 mm at 5.5 GHz). The mechanical P0 is CLOSED: every jack pair clears the 9.1654 mm coupling-nut envelope. P-ADJ SW_V4 closed. TWO defects remain open and both are named: 2 stranded GND pads, and the docs/PDF P0s not yet started."
measure: "DRC --severity-all --refill-zones --schematic-parity = 0 violations / 2 unconnected / 0 parity. CLASSIFIED: the 2 unconnected are TWO F.Cu GND pour islands each carrying a GND pad and NO via - R_PD2.2 (island 0.67x1.34 @41.20,52.61) and C_SW2.2 (1.29x1.32 @41.51,56.50). DRC calls them Zone<->Zone and names no pad. FOUR remedies measured and failed (island min_bbox 0.8->0.25, astar window 3->6, pad_rescue served_within 1.6->0.4, zone clearance 0.25->0.20); a fifth (row pitch 1.30->1.60) BROKE SW_V2's escape and was reverted. RF: RX1_MAIN 11.0000 mm copper over an 11.0000 mm through path. Jacks: worst pair J_RX2<->J_ANT8 9.9334 (unchanged), J_ANT8<->J_RX1 8.000 -> 11.0000. SW_V4 3.3992 of 4.0; 3V3 2.8268 of 3.0. Placement gates PASS, tier_preflight 0 FAIL, 12 asserts PASS, P-COLLIDE 0/0."
state:   blocked
next:    "1. CLOSE THE 2 STRANDED GND PADS (R_PD2.2, C_SW2.2) - untested hypotheses in journal/04_placement.md tail: a manual stitch_grid site at each pad, pad_rescue.rings below 0.15, or read WHY via-in-pad refuses those two sites when it served R_PD1.2 and C_SW1.2 1.30 mm either side. 2. P0-2 docs: amend ADR-0002 + ARCHITECTURE sec 10 to the built user_supplied posture. 3. P0-4: regenerate 03_tscircuit/build/schematic.pdf via gen_tscircuit.sh and verify it against the shipped netlist. 4. re-run policy_audit (P-ADJ should now be PASS; M-REL/A-POP close at seal). 5. re-gate ALL FOUR lenses fresh-context. 6. MANIFEST -> 2-commit seal -> beacon. NOT YET RUN THIS SESSION: rebuild_all.sh end-to-end (so M-FRESH is UNVERIFIED since the last full run), fence_pitch.py (produced no output when invoked bare - check its argv), the standalone-archive DRC."
op_pid:
updated: 2026-07-30T23:45:00
