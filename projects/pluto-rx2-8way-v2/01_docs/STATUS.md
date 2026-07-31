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
step:    "ROUTING GATE GREEN. DRC 0/0/0 at full severity. Route chain PROMOTED to 03_src/route/r4.kicad_pcb and committed."
measure: "kicad-cli pcb drc --severity-all --refill-zones --schematic-parity = 0 violations / 0 unconnected / 0 parity. R-LEN PASS: realized copper spread 0.5314 mm = 7.01 deg at 6 GHz vs the 1.0 mm DRIFT ceiling; octilinear FLOOR spread 0.0007 mm; 8/8 members measured, 0 vias / 1 component / 2 ends each. P-LAND PASS 45 graded/130 copper pads, 0 failing, 9 against a scoped clearance, routed cross-check 45/45 none wider than the model allows. P-OUT/P-CAP PASS (tightest pad-to-outline 1.28 mm, worst corridor ratio 0.04). E-NETREF PASS 95/95 0 ghost. tier_preflight 0 FAIL/1 WARN. DRC burn-down 21 -> 0 over FIVE causes: 12 stitch-grid vias inside an SMA pin 0.80 mm local clearance (one fact, reported once per layer), 5 module-footprint silk vs its own lands, 2 C_BULK 0.175 mm from the module castellations, 1 KRT 0.1069 mm via-in-pad stub, 1 module Value field on F.SilkS instead of F.Fab."
state:   done
next:    "Stage 6/7 verification: fab export, jlc_twin, pin + render reviews, policy_audit, then seal. OWED and MEASURED: the ground-via fence ships at 2.0 mm = lambda_g/13.7 against this board's own <= 1.35 mm bound, because stitch_grid steps with range(int(...)) and cannot take a fractional pitch."
op_pid:
updated: 2026-07-30T18:35:00
