# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   verify
step:    "P0 fix RE-VERIFIED from committed source + P1 set closed: check_port_nets 115/115 + 8/8, DRC 0/0/0, E-INV 7/7, count_parity 194x4, policy_audit 0 FAIL (3 evidence-backed waivers), audit_board P-POL/P-KEEP new gate red-tested, ADR-0007 finalized (pod waiver carried), 08_reviews archived."
measure: "gate.json 2026-07-23T18:10 — 0/0/0; policy_audit PASS=21 WAIVED=3 HUMAN=6"
state:   working
next:    "Commit green state -> stage 07_releases/v1.0-2026-07-23 (fab package, twin, renders, PDFs) -> one zero-context fresh lens -> harvest ledger -> 2-commit seal."
op_pid:
updated: 2026-07-23T18:25:00
