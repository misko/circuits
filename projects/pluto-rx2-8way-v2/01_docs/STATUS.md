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
step:    "PHASE 2 DONE. rebuild_all.sh re-seeded from the template — diff is exactly the two BOARD=/TSX= knobs. Full driver ran tsx -> DRC end to end, exit 0, and the deterministic rebuild_reuse path reproduces the SAME GEOMETRY from the pinned schematic. Next: Phase 3 battery + two-key red-team + seal."
measure: "FULL DRIVER exit 0 in 1m55.8s, DRC 0/0/0. M-FRESH PASS stamp+verify (6/6), fleet audit says ok pluto-rx2-8way-v2 (only adopted board of 5 knobbed). TSX-PRE 6/6, S-NETMERGE 23/23, E-INV 20/20, E-ADR 1/1, E-TOPO 1/1, E-MARGIN 1/1, S-COUNT 4/4 over 28 refdes, M-BOM leg C PASS, ERC 0 errors, P-OUT/P-CAP 0 fails 0 warns, R-PREFLIGHT 0 FAIL 1 WARN. TWO DRIVERS, ONE BOARD: 218 segments / 2265 vias / 32 footprints SET-EQUAL between rebuild_all and rebuild_reuse outputs, 0 only-in-either; md5 differs on UUIDs and write order only. FENCE (final board): worst structural along-arm 1.3435 vs bound 1.35; 12 of 21 arm-sides carry a NAMED occupancy aperture, worst 5.1071 at J_ANT8 avoid ring."
state:   working
next:    "Phase 3: fab export, jlc_stock, jlc_twin, twin_overlay, pin + render reviews, TWO-KEY red-team (design_verdict + order_verdict, EVERY lens re-gated), policy_audit, release_freshness (A-BUY + M-REV), standalone-archive DRC, MANIFEST, 2-commit seal, beacon refresh."
op_pid:
updated: 2026-07-30T20:30:00
