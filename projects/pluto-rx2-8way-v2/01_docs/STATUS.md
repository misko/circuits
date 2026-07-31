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
step:    "STOPPED AT THE SEAL. THREE of four lenses returned design_verdict: DEFECTIVE. FIVE P0s open. The 8.000 mm between J_ANT8 and J_RX1 is three of them at once: a P-ADJ span failure, a 10.107 mm branch line (-13.995 dB at 4 GHz), and two SMA coupling nuts that physically interfere so the board cannot be cabled. Release v1.0-2026-07-30 is STAGING and did NOT seal."
measure: "LENSES: topology DEFECTIVE/DO-NOT-ORDER 2P0 6P1 14P2; layout DEFECTIVE/DO-NOT-ORDER 1P0 8P1 8P2; render DEFECTIVE/DO-NOT-ORDER 2P0 8P1 10P2 (schematic readability FAIL); pin review SOUND/ORDER 98/98 pads 0 FAIL. MECHANICAL GATES GREEN: DRC 0/0/0 both lists empty - standalone archive DRC 0/0/0 outside the repo (was 657 until fp-lib-table stopped escaping and .kicad_pro/.kicad_dru shipped) - R-LEN PASS 0.5314mm=7.01deg - E-NETREF 87/87 - S-COUNT 4/4 over 28 refdes - stock 11/11 - F-LEGIBLE 13 - A-RENDER OK - twin 25 OK bodies 27/27 - M-FRESH PASS. policy_audit FAIL=3 PASS=29 WAIVED=3. FENCE 0.95mm lattice: worst structural along-arm 1.3435 vs bound 1.35; 12/21 arm-sides carry a named occupancy aperture, worst 5.1071 at J_ANT8 (lens independently 15/22, same worst)."
state:   blocked
next:    "D-BACK TO PLACEMENT, one pass fixes four findings. (1) separate J_ANT8/J_RX1 to >=10mm and move R_T1/R_T2 hard against J_ANT8 so the tap is a lumped node (<=1mm for >=16.5dB worst-case RL) — discards 03_src/route/r4.kicad_pcb, needs a fresh KRT campaign; (2) R_PD1..4 to the U_SW pads (P1-7); (3) module underside rect into stitch.stitch_grid.avoid (P1-2, 22 GND vias, my 0.95 fence quadrupled it); (4) regenerate 03_tscircuit/build/schematic.pdf, which is 4h STALE (P0-4). Then amend ADR-0002 + ARCHITECTURE sec 10 to the built user_supplied posture (P0-2). COORDINATOR, outside this partition: three rows for skills/jlcpcb-fab/scripts/jlc_lcsc_rotations.csv — C2286,0,two-channel (NOT the 180 twin_report suggests: that ships the LED dark), C504007,0,two-channel, C5121458,0,single-channel + order-preview human gate."
op_pid:
updated: 2026-07-30T22:05:00
