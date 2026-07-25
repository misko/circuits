# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   sealed
step:    "v1.4 SEALED: 07_releases/crow-recorder-central-v2-v1.4-2026-07-25 (seal d9715e5 on source S 47eca68 + S' ac975e2). CPL-CORRECTION supersede: v1.3 is DO-NOT-ORDER for PCBA — it ships 7 rows 180deg off (U1/U2/U3/U5/U7/U8/D_USB, all 90->270), every fine-pitch part on the board. SUPERSEDED.md on v1.3. Copper UNCHANGED and proven so by re-plot."
measure: "CPL diff vs v1.3 = EXACTLY 7 changed cells (all Rotation, all 90.0->270.0), 0 rows added/removed, Q1/Q2/U9 byte-identical; independent re-derivation (03_src/rot_remeasure.py, operator proven vs pcbnew at 0.000000000mm, pre-fix NEGATED form errs 35.560mm@90 / 0.960mm@270) puts all 7 at 270, rms<=0.0725mm vs a runner-up 15x-4811x worse, 0 mismatches; re-plot 15/15 zip members identical with timestamps stripped; 20 payload files sha256-identical; DRC 0/0/0; standalone-archive DRC 0/0/0 with 0 lib_footprint_issues; ERC 0/1211; parity 0 (116 nets, 598 nodes); count_parity 199x4; port nets 115/115+8/8; twin exit 0, 175 OK/369, 0 ROT-DB-SUGGEST; missing_models 177/177/0; A-POP PASS (203/177/26 = 10 declared + 16 exempt, consigned 1); A-STOCK PASS at qty 5; M-BOM PASS (49 lines); policy_audit 0 FAIL, M-REL PASS; freshness PASS; MANIFEST 64/64 hashes both directions; 2 zero-context lenses (staging DO-NOT-ORDER -> all 17 dispositioned; frozen bytes ORDER, 0 P0)"
state:   done
next:    "Order per v1.4 ORDER_README. TWO BLOCKING pre-PCBA human gates in JLC's placement preview: U1 pin-1 dot at 270deg, and J2 (USB-C) whose rotation NO pad-fit can grade (zero shared pad names, 90-vs-180 separation 1.0x). Re-check stock same-day (C5224055 383, C882626 496; C6938291 is consigned at stock 0 by design). v-next: local fiducials near U1, 1V8-supervisor interlock on U8 EN, in-line D_USB ESD, F_BEEP PTC + P5VA SMBJ5.0A."
op_pid:
updated: 2026-07-25T16:45:00
