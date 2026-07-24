# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   routing
step:    "ROUTING GATE GREEN + committed (coordinator 3bee9ec). M-REPRO done: promoted committed board driver 03_src/rebuild_reuse.sh (fleet rebuild_fast pattern; regenerates from committed 03_src + imports promoted chain rv2_final.kicad_pcb, no stochastic KRT), which REPRODUCES 0/0/0 from committed source. Fixed 1 --schematic-parity field mismatch (removed US8 footprint Description property)."
measure: "rebuild_reuse.sh -> ROUTING GATE 0 violations / 0 unconnected / 0 parity, from committed source (kicad-cli --severity-all --refill-zones --schematic-parity). Full 79/8 -> 0/0 achieved earlier this session."
state:   done
next:    "M-REPRO reproducer delivered. FLAG for coordinator (pre-seal, NOT routing, frozen skills): full rebuild_all.sh does not cleanly reproduce — tsci regenerates a divergent .kicad_sch (UUID churn) + kicad_sch_parity.py crashes; schematic-stage concern. New/changed for commit: 03_src/rebuild_reuse.sh, 03_src/rebuild_all.sh, US8 footprint Description-property removal. All projects/-scoped, NO skills/ edits. git left to coordinator."
op_pid:
updated: 2026-07-23T16:00:00
