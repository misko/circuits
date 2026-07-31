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
step:    "THE VIA-FENCE P0 IS CLOSED IN COPPER AND NO EXCEPTION WAS SPENT. fence_pitch.py VERDICT: PASS, exit 0 — worst interior along-arm aperture 1.1769 mm against the ADR-0004 bound of 1.1910 mm, 0 of 22 arm-sides over (was 17 of 20 at 3.0500). Closed by FOUR changes, each measured: stitch lattice 0.95 -> 0.80 with the spacing guard corrected 0.85 -> 0.75; the meander length-match pass DELETED and the board re-routed; and a 17-barrel per-arm fence declared as seed_stubs geometry, derived by continuum search and iterated to a fixed point in three measured rounds. Classes B and D closed PHYSICALLY — every aperture had legal ground in it, including the SMA avoid rings, whose barrels sit OUTSIDE the ring. Next: schematic PDF, staging, four lenses, seal."
measure: "FENCE (MEASURED, 03_src/fence_pitch.py off the saved 04_kicad board through pcbnew, reads no config): worst interior along-arm aperture 1.1769 mm at RX1_TAP sideE s=18.97..20.15, bound 1.1910, 0 of 22 arm-sides OVER, VERDICT PASS exit 0. Sequence 17/20@3.0500 -> 11/22@3.6000 (pitch 0.80) -> 6/22@3.6000 (re-route) -> 2/22@1.9769 -> 1/22@1.9802 -> 0/22@1.1769. DRC --severity-all --refill-zones --schematic-parity --exit-code-violations = 0 violations / 0 unconnected / 0 parity, exit 0, BOTH halves empty. R-LEN PASS 8/8 groups, realized track spread 0.1657 mm against max_spread_mm 1.0 (was 0.5314 with the meander pass; octilinear floor spread 0.0007). L-04 CLOSED as a side effect of the re-route: closest non-GND via In1 antipad edge to RF copper edge 0.0219 -> 0.2728 mm (SW_V4 vs ANT5), above the lens's own proposed 0.15 mm gate. L-03 CLOSED: six arms went from 10-12 track segments to ONE, so the six 0.600 mm-wide 37-ohm meander blobs are gone. seed_stubs 24 served / 28 placed / 0 REFUSED. BLIND EXCEPTION CRITERION formed by a zero-context agent given geometry but NOT the failure list (01_docs/decisions/0005-*.note.md): isolated aperture <= lambda_pp/12 = 1.985 mm under five conditions. NOT SPENT — the board meets the tighter lambda_pp/20 and claims no exception."
state:   working
next:    "rebuild_all.sh so the shipped pdf/schematic.pdf is regenerated from the current circuit (P0-4: the released PDF drew an earlier revision and composites N3V3_MOD2, i.e. the human document says the 3V3 rail is wired to an RF port); de-collide the tsx labels to close S-OCCL; then policy_audit to FAIL=0 (S-OCCL + A-POP, both truthful today), stage the release, run all four lenses fresh-context with distinct filenames, MANIFEST, 2-commit seal, refresh this beacon as PART of the seal."
op_pid:
updated: 2026-07-31T02:20:00
