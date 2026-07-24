# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   v1.1-respin
step:    "DO-NOT-ORDER on v1.0 (external review 2026-07-24, orchestrator-verified vs sealed bytes; archived 08_reviews/2026-07-24_v1.0_external-llm_full.md). v1.1 respin in progress: F1 U1 EP thermal vias filled+capped, F2 USB 90ohm diff-pair rules+reroute, F4 clean re-seal with consistent evidence. ADR-0007 waiver carried unchanged."
measure: "v1.0 gates historical; v1.1 gates pending rebuild"
state:   in-work
next:    "F1 footprint remodel -> F2 stackup+netclass -> full rebuild --reroute -> gates -> stage v1.1 -> battery + fresh lens -> 2-commit seal + SUPERSEDED.md on v1.0"
op_pid:
updated: 2026-07-24T00:00:00
