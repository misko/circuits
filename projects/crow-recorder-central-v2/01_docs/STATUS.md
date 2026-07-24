# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   respin-v1.2
step:    "v1.2 fix LANDED at source: 13x 100nF on 0V9 (ds XM-014532-PC-2.0.0 §14 p.29 'at least 12'); C_c9..C_c13 anchored at under-served pins; C_b0v9 slot swap; TDI->In3 reroute; routing gate GREEN from committed source."
measure: "DRC 0/0/0 (severity-all+refill+parity); port nets 115/115+8/8; netlist diff vs v1.1 = exactly 5 caps; USB pair 23.621/23.511 skew 0.110 0 vias; EP 16 vias; LV straps unconnected; worst pin-to-cap 3.22mm (50/54: 2.01/2.02)"
state:   in-work
next:    "rebuild_all parity -> semantic battery -> twin -> M-BOM -> ORDER_README F2 criteria -> stage v1.2 -> release gates + M-CONS -> INITIAL battery + fresh lens -> 2-commit seal + SUPERSEDED.md on v1.1"
op_pid:
updated: 2026-07-24T13:10:00
