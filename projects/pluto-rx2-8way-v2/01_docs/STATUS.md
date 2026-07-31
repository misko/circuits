# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame. Rewrite it at every stage enter/finish, every iterate, and IMMEDIATELY
BEFORE and AFTER every long blocking op (see SKILL.md "Journal discipline").

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

Multi-board projects: one beacon PER board, named `STATUS-<board>.md`
(mirroring the per-board `journal/<stage>.md` suffix). A single-board
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
step:    "SEAL REFUSED — 2 of 4 fresh-context lenses returned design_verdict DEFECTIVE. Board itself is now GREEN on every mechanical gate (driver end-to-end, DRC 0/0/0, policy_audit 0 FAIL, twin exit 0, A-ROT/F-LEGIBLE/M-BOM/A-STOCK/A-RENDER all OK); what blocks is an RF DISCLOSURE defect and a documentation/staging defect, not copper. NO release directory exists: the staged archive was moved to 06_build/staging so nothing is lost and nothing unsealed is named like a release."
measure: "LENSES (r2, fresh-context, concurrent, four DISTINCT filenames in 08_reviews/): topology DEFECTIVE/DO-NOT-ORDER (P0x2, P1x3) - layout DEFECTIVE/DO-NOT-ORDER (P0x1, P1x4) - pin SOUND/ORDER (98 pins checked, 0 FAIL) - render SOUND/DO-NOT-ORDER (P0x0, P1x5, schematic readability S6 FAIL). BOARD: DRC --severity-all --refill-zones --schematic-parity = 0 violations / 0 unconnected / 0 parity, CLASSIFIED both halves (both lists empty in 06_build/drc/gate.json). policy_audit: FAIL=0 HUMAN=6 N-A=9 PASS=29 WAIVED=1. M-FRESH PASS 9/9 incl F-RENDER. FENCE re-measured off the NEW board: worst interior along-arm aperture 3.0500 mm at ANT4 sideW s=7.12..10.17 against the 1.35 mm bound (2.26x), 11 of 20 arm-sides over, VERDICT FAIL - each aperture named by occupier in 06_build/verify/fence_apertures.txt. Stranded GND pads: CLOSED, 0 remain."
state:   blocked
next:    "THE BLOCKING P0 IS THE FENCE, AND IT MUST BE SETTLED IN THE RIGHT ORDER. (1) FIRST resolve the layout lens's P1 CBCPW finding - the arms measure as grounded coplanar waveguide (GND pour at median 0.205 mm both sides over 67.5-94.3% of each arm) while ADR-0003's whole constant set is a BARE-MICROSTRIP derivation, and nets.yaml states in writing that a coplanar ground does not run alongside. If it holds, eps_eff moves 3.3286 -> 3.1552 and the fence bound moves with it, so grading the fence first grades it against the wrong number. (2) THEN close the fence: a placement change that frees the occupied lattice sites, a per-arm fence pass the shared stitcher does not have, or an ADR-0003 amendment that re-derives a bound the board can hold and MEASURES what the residual apertures cost in isolation. (3) Withdraw or re-argue the S-OCCL waiver - the render lens FALSIFIED its premise: all four occlusions are in pdf/schematic.pdf, plus two the checker never listed. (4) Fix the schematic PDF (N3V3_MOD/ANT2 overlap on U_SW pin 2 makes the picture say the 3V3 rail is wired to an RF port) and the pcb_layers/assembly PDF export options. (5) Re-stage from 06_build/staging, and this time write MANIFEST + ORDER_README BEFORE the lenses run and run policy_audit LAST, after the fab set - the shipped audit predated the fab artifacts and read vacuous N-A. (6) Re-gate all four lenses fresh-context; the r2 verdicts void on any material change. Full dispositions: 08_reviews/DISPOSITIONS.md."
op_pid:
updated: 2026-07-30T22:52:00
