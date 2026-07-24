# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   respin-v1.2
step:    "v1.2 staged + FULL battery green: redteam topology ORDER, redteam layout ORDER, pin PASS, render PASS, fresh lens ORDER on final bytes. Sealing (2-commit dance)."
measure: "staged DRC 0/0/0; ERC 0/1211; parity 0 (116 nets); twin 165/369 exit 0; M-BOM PASS; policy 0 FAIL; 13x 100nF on 0V9, per-pin worst 3.22mm, new caps 1.63-3.63mm to served pins, GND in-pad or <=0.5mm; USB pair + EP 16 vias + LV floats re-verified on the archive"
state:   in-work
next:    "source commit S -> stamp MANIFEST (git_sha S) -> freshness + M-REL/M-CONS re-run -> seal commit (release dir + CHANGELOG + SUPERSEDED.md on v1.1)"
op_pid:
updated: 2026-07-24T14:05:00
