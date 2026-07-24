# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   sealed
step:    "v1.0 SEALED: 07_releases/crow-recorder-central-v2-v1.0-2026-07-23 (seal 496b4bb on source S 8d96583). Fresh-lens ORDER; both its P1s fixed pre-seal. The crow pair (pod-v2 + central-v2) is complete."
measure: "DRC 0/0/0 (+ standalone archive re-measure 0/0/0); check_port_nets 115/115+8/8; twin exit 0; policy_audit 0 FAIL/3 waived; MANIFEST 45/45; freshness PASS"
state:   done
next:    "Order at JLCPCB per ORDER_README (6L ADVANCED small-via REQUIRED; same-day stock recheck; XU316 + RJ45 consign). v-next work order in ADR-0007 + ORDER_README sec 6."
op_pid:
updated: 2026-07-23T20:15:00
