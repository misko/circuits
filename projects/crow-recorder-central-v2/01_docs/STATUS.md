# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   seal
step:    "v1.4 staged + gated: 07_releases/crow-recorder-central-v2-v1.4-2026-07-25. CPL-correction supersede of v1.3, which is DO-NOT-ORDER for PCBA (7 rows 180deg off: U1/U2/U3/U5/U7/U8/D_USB, all 90->270). Copper UNCHANGED and proven so by re-plot. assembly.yaml + A-POP/A-STOCK land on this board."
measure: "CPL diff vs v1.3 = EXACTLY 7 changed cells (all Rotation, all 90.0->270.0), 0 rows added/removed, Q1/Q2/U9 byte-identical; independent re-derivation (operator proven vs pcbnew, max err 0.000000000mm) puts all 7 at 270 with rms<=0.0725mm vs a runner-up 15x-4811x worse, 0 mismatches; re-plot 15/15 zip members identical with timestamps stripped, 20 payload files sha256-identical; DRC 0/0/0; standalone-archive DRC 0/0/0 with 0 lib_footprint_issues; ERC 0/1211; parity 0 (116 nets); count_parity 199x4; port nets 115/115+8/8; twin exit 0, 175 OK/369, 0 ROT-DB-SUGGEST; missing_models 177/177/0; A-POP PASS (203/177/26 = 10 declared + 16 exempt, consigned 1); A-STOCK PASS at qty 5; M-BOM PASS (49 lines); policy_audit 0 FAIL"
state:   working
next:    "source commit S -> stamp MANIFEST (git_sha=S, git_dirty:false) + re-run M-REL/freshness -> seal commit (release dir + CHANGELOG + SUPERSEDED.md on v1.3). Then: order per v1.4 ORDER_README; the U1 pin-1 JLC-preview gate (270deg) is MANDATORY before any PCBA."
op_pid:
updated: 2026-07-25T15:55:00
