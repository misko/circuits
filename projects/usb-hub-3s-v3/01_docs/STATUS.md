# STATUS beacon — usb-hub-3s-v3 (live head of the journal)

<!-- reader parses from here down -->
stage:   v1.5-SEALED
step:    "SEALED: 07_releases/v1.5-2026-07-25 — CPL-CORRECTION supersede of v1.4 (which is DO-NOT-ORDER: C1/C2, polarized 100uF/35V polymer across the 3S pack, shipped 180deg REVERSED). ORDER FROM v1.5. Live journal: 01_docs/journal/v1.5_cpl_fix.md; driving review: 08_reviews/2026-07-25_v1.4_pcba-audit_assembly.md (PCBA-1..15)."
measure: "CPL diff vs v1.4 = EXACTLY 4 cells (C1 270->90, C2 270->90, Q7 270->180, J1 90->0), 0 added/removed rows. Payload sha256-IDENTICAL to v1.4 on 20 files (gerber zip + 2 drl + 17 pdf/source/3d). DRC 0/0/0; ERC 0 errors (204 lib_symbol_issues warnings, ADR-0002); parity 110 comp/67 nets/347 nodes, 0 diff. twin exit 0, 231 checks, 0 ROT-DB-SUGGEST. stock PASS 43/43 at qty 5, split 12 Basic/31 Extended, tightest ceiling C473910=37 boards. BOM MPN 43/43 (was 0/43), cross-checked 26/26 vs 02_parts. A-POP PASS; bom_source_check PASS; policy_audit 0 FAIL; contracts_audit PASS."
state:   done
next:    "order-day: re-run jlc_stock_check (C473910 + C5337088 are the movers; plus the correctness codes R12=C2984354 / D5=C113976 / R30=C25803). Then the ORDER-PREVIEW HUMAN GATE P1-P7 — C1/C2 polarity and J1 XT60 polarity are MANDATORY eyeball items. Mark F1/SW1 DNP (2 unmatched designators expected). Order JLC THT assembly (J1-J4, 22 holes) + tell them J5 is an SMD/THT hybrid. Panel: single boards, rails ONLY on the edge opposite the USB-C connector. Then Q0-Q7 bench gate before any Pi; Q1 must RECORD measured VBUSC/VBUSA (waiver W-U12 evidence). Deferred: F1 onto the CPL (PCBA-6, needs a board change); assembly.yaml schema gaps (PCBA-9, a skill change)."
op_pid:
updated: 2026-07-25T12:00:00-07:00
