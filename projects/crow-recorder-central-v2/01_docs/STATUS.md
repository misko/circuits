# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   sealed
step:    "v1.5 SEALED (708a0c7, immutable) and RE-CONFIRMED 2026-07-26 against the fleet's moved gates. The cooksense passive-value defect class (picker decade-misparse, e.g. 62k read as 6k2) had never been checked on this board: measured on the sealed v1.5 BOM = 0 VALUE-MISMATCH across 26 value-bearing passive rows / 79 coded R/C refdes. v1.5 REMAINS THE FLEET'S ORDERABLE RELEASE."
measure: "value check (known-bad proof first: authored 62k vs MPN 0402WGF6201TCE decodes 6200 = VALUE-MISMATCH exit 1): 24 rows reconciled via vetted ledger, 0 MISMATCH, 2 UNVERIFIABLE (C377773 2.2uF x17 refs, C25130 680R x1) — both catalog-verified live vs JLC parts API 2026-07-26, both MATCH, recorded as 02_parts entries (commit 8092f4f); policy_audit re-run 0 FAIL (29 PASS/2 WAIVED/6 HUMAN/3 N-A); freshness re-run PASS in --cpl-only-supersede v1.4 mode (fab/source/3d byte-identical asserted; cpl delta = 1 coord move J2 + 3 rows removed J1,R_inj1,R_inj2); live stock reproduces sealed evidence exactly (C6938291 x1, C9900035627 x8 at stock 0, both sourcing_plan-covered); contracts_audit 187 files 0 violations. CHECKER GAP reported upstream: bom_source_check row_kind() is blind to descriptive refdes prefixes (Cc*/Rs*/Rf/Rd/RG1/CL*/Cd*/Cinh*/Cout*) — 12 of 26 passive rows (57 refdes) silently skipped by the gate in BOTH bom and --circuit-only modes; covered this session by a forced-kind sweep over every row."
state:   done
next:    "Order per v1.5 ORDER_README (human gates + consign plan unchanged). Upstream owed: row_kind fix + known-bad fixture in bom_source_check.py, ledger rows for C377773/C25130 (skills/ paths — outside this board agent's staging scope)."
op_pid:
updated: 2026-07-26T09:25:00
