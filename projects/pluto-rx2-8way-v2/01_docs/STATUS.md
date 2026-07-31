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
step:    "THE COPPER MOVED, and that is the whole frame. The fab lens's hole-to-hole finding was QUANTIFIED rather than waived: classified by pair class, the tight class is the RF LAUNCH (VIA<->PTH pad, 54 pairs, min 0.3016) and NOT the 3446-via fence (VIA<->VIA, 2 pairs, min 0.3785). At JLC's published +0.13 mm pad-hole tolerance 8 of the 54 fell UNDER the declared 0.25 floor (worst 0.2366). Fixed in SOURCE and rebuilt: floorplan design_rules.hole_to_hole 0.25 -> 0.315 (derived = tier floor + max-material pad-radius growth) plus 8 seed_stubs displaced 0.035 mm outward. BOTH tight constraints clear. 06_build/staging/ is REMOVED — a material change voids prior verdicts, and its gerbers, MANIFEST and all four 2026-07-31 lens reviews describe copper that no longer exists."
measure: "AFTER, rebuild_all.sh RAW EXIT 0. min hole-to-hole 0.3016 -> 0.3265 nominal, 0.2366 -> 0.2615 at MAX MATERIAL, pairs under the 0.25 floor 8 -> 0. fence_pitch.py RAW EXIT 0, worst 1.1769 mm vs bound 1.1910, 22 arm-sides, 0 OVER, VERDICT PASS - UNCHANGED TO FOUR DECIMALS. fence_apertures.py 0 GAP lines over 3433 PCB_VIA GND + 40 PTH = 3473 elements (exit code is NEVER evidence, its own header says so; the absence of GAP lines is). Band-free nearest-ground max over all arms 2.2142 -> 2.2142 mm. GND vias / fence elements 3433 / 3473 -> 3433 / 3473. DRC --severity-all --refill-zones --schematic-parity 0 / 0 / 0. KNOWN-BAD FIXTURE: the PRE-FIX board against the new 0.315 floor gives 16 hole_to_hole findings over 8 distinct pairs at exactly 0.3016 x2, 0.3028, 0.3118, 0.3121 x2, 0.3144 x2 - the gate can fail. THE TRADEOFF, SWEPT: both-pass window is displacement in [0.0134, 0.0632] mm, 49.8 um wide; the hole metric SATURATES above 0.025 (binding pair becomes an untouched one, via 43.000,27.000 <-> J_ANT8.3 at 0.3265/0.2615); 0.035 is the centre of [0.025, 0.048] where the hole gap is maximal and the fence is bit-for-bit unchanged. Suite: CONTROL worktree /tmp/ctrl_pluto @ 0a3a5ab1 TOTAL 1116 passed, 18 failed, 664 known-bad, RAW EXIT 1; AFTER worktree /home/mouse9911/gits/circuits @ 34b3d66b TOTAL 1130 passed, 13 failed, 675 known-bad, RAW EXIT 1. ZERO failures attributable to this change - proven, not asserted: copying only the sibling'"'"'s untracked projects/programmable-usb2-hub/ into the clean control worktree reproduces both differing files exactly (t1_adr_bounds 3 failed, t1_layout_precedent 2 failed)."
state:   working
next:    "TWO THINGS OWED, neither of them copper, and neither claimed as done. (1) A FRESH LENS ROUND against the REBUILT board, then a re-stage. The four 2026-07-31 reviews (RF SOUND/ORDER, schematic SOUND/ORDER, release-integrity DEFECTIVE, fab/orderability DEFECTIVE) are ARCHIVED REVIEWS OF THE PRE-FIX COPPER from here on and must not be promoted into verification/redteam_{layout,topology}.md as this release'"'"'s verdict - that is the adjacent-property error M-REV'"'"'s own comment warns about. The fab lens'"'"'s DEFECTIVE is the finding THIS session closed; the release-integrity lens'"'"'s DEFECTIVE (a stale archive) is closed by the rebuild and the removal. Both need a fresh reviewer to say so, not this agent. (2) THE VENDOR QUESTION IS NOT SETTLED AND 0.315 DOES NOT SETTLE IT. JLC publishes 0.2 mm via-to-via and 0.45 mm pad-to-pad and NOTHING for the mixed class; their public Q&A #693 is a customer asking exactly this, unanswered. 0.315 makes the board honour ITS OWN declared tier at max material - the mixed-class rule remains a DFM item to put to JLC in writing before the order, beside the ORDER_README'"'"'s other human gates. ALSO OPEN, unchanged: S-OCCL is a converter defect outside this partition; RF-4 (fence_pitch grades max INTERIOR gap only, so lead-in and run-out enter no comparison) is now LOAD-BEARING - it is what made DELETING the 8 vias score better than MOVING them 0.14 mm, and it is why they were moved rather than deleted."
op_pid:
updated: 2026-07-31T12:50:00
