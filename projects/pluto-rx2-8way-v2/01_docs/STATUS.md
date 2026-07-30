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
stage:   schematic
step:    "03_tscircuit scaffolding written (package/manifest/net_aliases/padmap); tsx blocked on the RP2040-Zero pad map, which is being read off the vendor drawing rather than guessed"
measure: "D-SPEC CLOSED: module SURVIVES the RF test (RP2040-Zero = RT9013-33 LDO, no inductor on the vendor schematic; the RT6150/PFM objection is confirmed and applies to the Pico ONLY). Assembly posture = CONSIGN (live JLC read: every footprint-bearing Pico-class code is stock 0; bare RP2040 C2040 at 63,091). 3 ADRs, 4 rules files, 28 components declared vs v1's 64."
state:   working
next:    "module part.yaml -> tsx -> tsx_preflight -> tsci build -> ERC + parity + the cheap semantic battery = the SCHEMATIC GATE (declared handoff boundary)"
op_pid:
updated: 2026-07-30T10:05:00
