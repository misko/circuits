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
stage:   routing
step:    "Driver RE-SEEDED from the template (diff is now exactly BOARD=/TSX=) and RUN end-to-end: M-FRESH PASS 9/9 including F-RENDER, so P0-4 (stale schematic.pdf) is CLOSED mechanically. The driver then DIES at stitch pass heal_islands — the 2 stranded GND pads are a HARD DRIVER ERROR, not just 2 DRC unconnected. Both root causes now MEASURED and they are DIFFERENT defects."
measure: "R_PD2.2 @(41.500,53.110): via_site_ok = TRUE at its own pad centre (144 legal 0.25/0.15 sites inside its island). The refusal is try_via's NET-BLIND stitch.via.spacing=0.85 guard against a SW_V1 escape via 0.7440 mm away — no clearance rule, and no stitch parameter the prior agent swept touches it. C_SW2.2 @(42.375,57.000): 0 legal via sites out of 608 interior points of its 1.411x1.437 island, at clearance 0.20/0.14/0.13 alike. Cause MEASURED: three In2.Cu control verticals SW_V4 x=41.850, SW_V1 x=42.350, SW_V2 x=42.800 run under the pad at 0.50/0.45 pitch; a 0.25/0.15 via needs 0.425 mm from a 0.2 track centreline, so no site exists between them, and F.Cu is walled by the 0.400 3V3 trunk (S+W) and SW_V3 (E). Landlocked — an upstream fix, not a stitch knob."
state:   working
next:    "C_SW2 rotated 0 -> 180 in floorplan.yaml (GND pad moves to x 40.825, 1.025 mm clear of the nearest In2 vertical; centre unmoved so the corridor and the SW_V4 budget are untouched); a User.3 barrel-window keepout reserves the site; stitch.seed_stubs declares a via-in-pad at BOTH pads (reduce-proved by _pin_touched, collision-refused, idempotent). Then prep -> route --race -> promote -> driver. After that: fence_pitch.py BOARD [band] [bound] off the NEW board vs 1.35; P0-2 docs (ADR-0002 + ARCHITECTURE sec 10 say consigned/on-CPL, assembly.yaml says user_supplied — physics wins); R-THERM U_SW.25(0) must be closed or evidenced-waived; DROP the now-inert P-POL/P-KEEP waivers; four fresh-context lenses; MANIFEST -> 2-commit seal -> beacon."
op_pid:
updated: 2026-07-30T21:05:00
