# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

<!-- reader parses from here down -->
stage:   sealed
step:    "v1.2 SEALED: 07_releases/crow-recorder-central-v2-v1.2-2026-07-24 (seal 64764a7 on source S d66fd1e). Supersedes v1.1 (EXT2-F1: 8x 100nF on 0V9 vs ds minimum 12 — now 13x, placed at the under-served pins). SUPERSEDED.md on v1.1."
measure: "staged DRC 0/0/0; ERC 0/1211; parity 0 (116); count_parity 199x4; port nets 115/115+8/8; policy 0 FAIL (M-REL PASS post-stamp); twin 165/369 exit 0; M-BOM PASS; freshness+M-CONS PASS post-stamp; RT topology ORDER + RT layout ORDER + pin PASS + render PASS + fresh lens ORDER; worst pin-to-cap 3.22mm, 50/54 at 2.01/2.02; USB 23.621/23.511 skew 0.110 0 vias; EP 16x0.30/0.15; LV floats intact"
state:   done
next:    "Order per v1.2 ORDER_README (same JLC options as v1.1 + §4a rail-sequencing corners gate + 0V9 ripple/droop first-article). v-next: 1V8-supervisor interlock on U8 EN (EXT2-F2), in-line D_USB ESD (EXT2-F3), ADR-0007 OVP/F_BEEP."
op_pid:
updated: 2026-07-24T14:20:00
