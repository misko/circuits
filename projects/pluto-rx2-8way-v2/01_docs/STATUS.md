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
step:    "ROUTING GATE GREEN AND REGENERABLE. The full driver 03_src/rebuild_all.sh runs tsx -> DRC and exits 0."
measure: "DRC --severity-all --refill-zones --schematic-parity = 0 violations / 0 unconnected / 0 parity, ON THE DRIVER-PRODUCED BOARD. R-LEN PASS realized spread 0.5314 mm = 7.01 deg at 6 GHz vs the 1.0 ceiling; octilinear FLOOR spread 0.0007 mm (v1: 1.4966 mm = 19.74 deg, ABOVE its ceiling). P-LAND PASS 0 failing, routed cross-check 45/45 none wider than the model allows. P-OUT/P-CAP PASS. E-NETREF PASS 95/95 0 ghost. M-FRESH PASS (build_provenance audit). ERC 0 errors / 220 warnings (was 248; the 28 footprint_link_issues left when fp-lib-table resolved). tsci churned the schematic bytes but the netlist is NODE-FOR-NODE IDENTICAL, 40 nets / 130 nodes."
state:   done
next:    "Stage 6/7: fab export, jlc_twin, pin + render reviews, policy_audit, seal. OWED and MEASURED: the ground-via fence ships at 2.0 mm = lambda_g/13.7 against this board's own <= 1.35 mm bound (stitch_grid steps with range(int(...)) so a fractional pitch is silently truncated). OWED upward: a contract row for floorplan `silk.polarity_marks` (G-ORPHAN), and two template findings (the ERC line gates on warnings; the driver calls 03_src/audit_board.py unconditionally)."
op_pid:
updated: 2026-07-30T18:55:00
