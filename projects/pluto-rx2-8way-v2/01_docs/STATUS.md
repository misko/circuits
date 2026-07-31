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
step:    "STOPPED AT THE SEAL. BOTH red-team lenses returned design_verdict: DEFECTIVE. THREE P0s open, one of them electrical: the RX1 pickoff is built as a 10.107 mm BRANCH, not the lumped node DETAIL_DESIGN sec 2 declares — 90 deg at 4.06 GHz, 490 ohm arm -> 5.1 ohm shunt across the antenna node, RX1 through-loss -13.995 dB and antenna return loss 1.91 dB at 4.00 GHz. Release v1.0-2026-07-30 is STAGING and did NOT seal."
measure: "LENSES: topology DEFECTIVE/DO-NOT-ORDER 2 P0 6 P1 14 P2; layout DEFECTIVE/DO-NOT-ORDER 1 P0 8 P1 8 P2; pin review SOUND/ORDER 98/98 pads 0 FAIL. GATES GREEN: DRC 0/0/0 both lists empty - standalone archive DRC 0/0/0 outside the repo (was 657 until fp-lib-table stopped escaping and .kicad_pro/.kicad_dru were shipped) - R-LEN PASS 0.5314mm=7.01deg - E-NETREF 87/87 - S-COUNT 4/4 over 28 refdes - stock 11/11 at >=5x - F-LEGIBLE 13 checks - A-RENDER twin_overlay OK - twin 25 OK bodies 27/27. policy_audit FAIL=3 PASS=29 WAIVED=3. FENCE 0.95mm: worst structural along-arm 1.3435 vs 1.35; 12/21 arm-sides carry a named occupancy aperture, worst 5.1071 at J_ANT8 (lens independently: 15/22, same worst)."
state:   blocked
next:    "D-BACK TO PLACEMENT. (1) P0-1: move R_T1/R_T2 hard against J_ANT8 so the tap is a lumped node (lens: <=1mm needed for >=16.5dB worst-case RL) — this discards the promoted chain 03_src/route/r4.kicad_pcb and needs a fresh KRT campaign; take R_PD1..4 to the U_SW pads in the same pass (P1-7, U_SW.12->R_PD4.1 7.96mm of 4.0), and add the module underside rect to stitch.stitch_grid.avoid (P1-2, 22 GND vias, my 0.95 fence quadrupled it). (2) P0-2: amend ADR-0002 + ARCHITECTURE sec 10 to the built user_supplied posture. (3) COORDINATOR, outside this partition: three rows for skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv — C2286,0,two-channel (NOT the 180 twin_report suggests; that ships the LED dark), C504007,0,two-channel, C5121458,0,single-channel + order-preview human gate. Evidence in 01_docs/journal/05_verify.md."
op_pid:
updated: 2026-07-30T21:45:00
