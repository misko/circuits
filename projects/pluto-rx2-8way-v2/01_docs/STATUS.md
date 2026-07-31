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
step:    "Placement gate GREEN. floorplan.yaml authored, board generated, BOTH owed floors MEASURED off the real .kicad_pcb. route.yaml is next."
measure: "OCTILINEAR FLOOR SPREAD 0.0007 mm = 0.01 deg at 6 GHz (copper_length_audit.py, pads alone, off 04_kicad/pluto_rx2_8way_v2.kicad_pcb) against v1's MEASURED 1.4966 mm / 19.74 deg — 2100x, bought at placement before a router ran. Construction: all 8 graded arms leave their OWN U_SW pad on an EXACT 45-deg multiple (135/180/225/270/315/0/45/90 on pads 24/2/4/6/13/15/17/22), the only assignment monotone in the QFN's CCW RF pin order; axis 14.00 mm, diagonal 9.90/axis, because 99/70 is the sqrt(2) convergent so BOTH stay on the 0.05 mm router grid and 9.90*sqrt2 = 14.000714. P-LAND PASS 50 graded/130 copper pads, 0 failing, 10 against ONE scoped clearance (rf_launch 0.14 mm) earned by this board's own escape_check --board run: SIX U_SW pads could not emit their class width at 0.200 (5x RF50 short 0.060, U_SW.8 PWR short 0.100) — arithmetic on a 0.30x0.60 land at 0.50 pitch, not congestion. FIVE of v1's six relaxations NOT re-adopted: v2's arms arrive on the SMA post-square symmetry axes and clear every post centre by 2.540 mm. Gates UNPIPED: generate_board 28/28 anchored asserts 12/12; P-COLLIDE 0 shorts 0 overlaps; P-OUT PASS tightest 1.49 mm; P-CAP PASS ratio 0.04. DEFECT FOUND AND FIXED: the module footprint drew its COPPER keepout on `User.Comments` (a GUI display name) instead of `Cmts.User` — pcbnew LoadBoard returned None and kicad-cli said only Failed to load board; found by bisecting the board file."
state:   working
next:    "Author 03_src/route.yaml (RF wave FIRST, F.Cu only, In1.Cu EXCLUDED from routing layers, grid_step 0.05, clearance 0.14, length_match_group over the 8 members, meander), then prep/route/stitch, then generate_rules LAST, then the DRC gate 0/0/0 CLASSIFIED both halves."
op_pid:
updated: 2026-07-30T17:40:00
