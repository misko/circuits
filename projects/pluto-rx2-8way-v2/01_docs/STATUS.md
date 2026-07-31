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
step:    "THE VIA-FENCE P0 IS CLOSED IN COPPER AND NO EXCEPTION WAS SPENT — but the board does NOT seal today, because policy_audit S-OCCL cannot reach 0 inside this agent's partition. HANDOFF at a gate boundary: copper is finished and green, what remains is a converter patch that is not this partition's to make, two tscircuit label placements, and the release ceremony. NOTHING IS STAGED and 07_releases/ is empty."
measure: "FENCE (MEASURED, 03_src/fence_pitch.py off the saved board through pcbnew, reads no config): worst interior along-arm aperture 1.1769 mm at RX1_TAP sideE s=18.97..20.15 against the ADR-0004 bound 1.1910 = lambda_pp/20.24; 0 of 22 arm-sides OVER; VERDICT PASS, exit 0. Was 17 of 20 at 3.0500. Sequence, each step measured: 17/20@3.0500 -> 11/22@3.6000 (lattice 0.95->0.80 + spacing guard 0.85->0.75) -> 6/22@3.6000 (re-route, meander pass DELETED) -> 2/22@1.9769 -> 1/22@1.9802 -> 0/22@1.1769 (per-arm fence, 17 declared barrels, 3 measured rounds). DRC --severity-all --refill-zones --schematic-parity --exit-code-violations = 0 violations / 0 unconnected / 0 parity, BOTH halves empty. R-LEN PASS 8/8, realized track spread 0.1657 mm vs max_spread_mm 1.0 (0.5314 with the meander pass). M-BOUND PASS, fleet CITED 8->9, OWED back to its 37 ratchet. contracts_audit 0 violations. M-BEACON PASS. rebuild_all.sh exit 0 end to end in 1m54s, so the shipped schematic.pdf now renders the CURRENT circuit (closes P0-4). policy_audit FAIL=2 (S-OCCL, A-POP), HUMAN=6, N-A=7, PASS=30. CLASSES B AND D CLOSED PHYSICALLY, NOT BY EXCEPTION: every aperture had legal ground in it and the SMA avoid-ring barrels sit OUTSIDE the ring at 1.36-2.46 mm offset. Two P1s closed as side effects: L-03 (six arms 10-12 track segments -> ONE, so the six 0.600 mm 37-ohm meander blobs are gone) and L-04 (closest non-GND via In1 antipad edge to RF copper edge 0.0219 -> 0.2728 mm)."
state:   blocked
next:    "S-OCCL IS A CONVERTER DEFECT AND IS THE ONLY THING BETWEEN THIS BOARD AND A SEAL. MEASURED: R_LED's symbol sits at x=73.025 and its two global labels at 69.215 (ang 0, plate extends RIGHT) and 76.835 (ang 180, plate extends LEFT) — 73.025 +/- 3.81, the part's own pin tips — so BOTH plates point INWARD across the body. Same for R_S2 (body 118.745, labels 114.935/125.095) and R_T2 (body 151.130, labels 147.320/154.940). circuit_json_to_kicad_sch.py INTENDS the opposite (side left -> ang 180 justify right; side right -> ang 0 justify left), so the mapping is correct and the SIDE handed to it is inverted for a horizontally-placed 2-pin part. A 7.62 mm pin span cannot hold two plates of (len(net)+2)*1.05 mm fired inward from both ends — 12.6 mm for LED_STAT_A, 15.75 for RX1_TAP_MID — so NO placement fixes it and it will reproduce on every board with a 2-pin part carrying labels on both pins. FOUR THINGS OWED, none of them copper: (1) the converter patch in skills/ (OUTSIDE this partition, REPORTED not made) — after it, re-run rebuild_all and S-OCCL should fall to 0; (2) two tscircuit schematic placements so the SHIPPED PDF stops saying something false — the N3V3_MOD label from U_MCU pin 21 lands on U_SW's RF2 row (3V3 appearing wired to an RF port) and a GND symbol composites with the N3V3 label at U_SW pin 8 into G|N3V3; the .tsx declares no schX/schY at all today; (3) stage the release and write the MANIFEST, which is what closes A-POP; (4) re-gate all four lenses fresh-context with DISTINCT filenames against the staged archive, then the 2-commit seal, refreshing this beacon as PART of it. THE FOUR r2 LENS VERDICTS ARE VOID by the material change and must not be reused."
op_pid:
updated: 2026-07-31T03:05:00
