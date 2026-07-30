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
stage:   placement
step:    "PAD-MAP M1 CROSS-CHECK COMPLETE + assembly posture corrected. Footprint library authored and vendored. floorplan.yaml is the next act and is NOT started."
measure: "TWO DEFECTS, BOTH IN THE SOURCE, BOTH FIXED. (1) NUMBERING: the schematic gate closed on an INVENTED numbering; Waveshare publishes one (sch header P1 'Header 23' + wiki FAQ 'Pin23'/'Pin 21') and it is the EXACT REVERSE, ours_n = 24 - vendor_n on all 23. Vendor numbering adopted; netlist VERIFIED DIRECTLY pad1=SEL_V1 pad4=SEL_V4 pad5=LED_STAT pad21=3V3_MOD pad22=GND. (2) MECHANICAL: 23 components on the CARRIER-FACING face, crystal 1.000mm proud (STEP-measured, twice, independently) -> no reflowable joint -> assembly.yaml consigned -> not_assembled/hand-solder, reason MECHANICAL. Plus 3 by inspection: 2 FPIDs pointed into v1's lib (vendored), rebuild_all.sh still had TEMPLATE knobs power3s (never run), tsci writes dist/ not build/ (a STALE circuit.json passed EVERY gate). GATES ALL UNPIPED: TSX-PRE 6/6, S-NETMERGE 23/23, E-INV 20/20, E-ADR 1/1, E-TOPO 1/1, E-MARGIN PASS, E-OFF N-A, S-COUNT 28/28 over 3 pairs, E-NETREF 78/78 0 ghost, M-BOM legC PASS, P-FACT 1/8 graded 7 UNREACHED listed, ERC 0 errors/248 warnings (131 off_grid + 89 lib_symbol + 28 footprint_link, all cosmetic; moved from 183 by documented tsci non-determinism)."
state:   working
next:    "floorplan.yaml. FIRST ACT is still the OCTILINEAR FLOOR + P-LAND, and BOTH ARE STILL UNMEASURED because both need artifacts that do not exist: P-LAND is escape_check.py --board (needs a .kicad_pcb); the octilinear floor is a property of the STAR GEOMETRY, not of the parts. The transferable LEVER from v1: put star angles on MULTIPLES OF 45 deg and the octilinear excess is zero by construction (v1 had 6 of 9 radials off-45, each paying 1.0731x). New floorplan constraints from the module: USB-C edge AT/BEYOND the carrier board edge; BOOT+RESET must stay accessible (only route into the bootloader, no SWD anywhere); GND is ONE castellation (pad 22) for all 20 GPIO returns; two keepouts drawn into the footprint (HEIGHT Dwgs.User, COPPER User.Comments) that NOTHING GRADES."
op_pid:
updated: 2026-07-30T15:20:00
