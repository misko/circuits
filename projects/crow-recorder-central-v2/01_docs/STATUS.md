# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   release
step:    "SEALING v1.0-2026-07-23: fresh-lens ORDER (no P0; its 2 P1s FIXED pre-seal: CL1/CL2 12pF, Cout_U10 2.2uF), all gates green on the final staged archive. 2-commit seal in progress (source commit S -> stamp MANIFEST -> seal commit)."
measure: "DRC 0/0/0; check_port_nets 115/115+8/8; twin exit 0 (160 OK/358); policy_audit 0 FAIL exc M-REL (stamping); bom_source PASS; E-INV 7/7; count_parity 194x4"
state:   working
next:    "Stamp MANIFEST with S; seal commit; git check-ignore sweep LAST; final report."
op_pid:
updated: 2026-07-23T19:55:00
