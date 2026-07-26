# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. OVERWRITTEN (not appended) at every transition; history
lives in `journal/<stage>.md`. Read by `skills/kicad-pcb/scripts/pcb_status.py`.

<!-- reader parses from here down -->
stage:   seal
step:    "v1.1 staging RE-VERIFIED 2026-07-26 (frozen 2026-07-25, digest c9804afe). Seal is BLOCKED on A-ROT: the hardened exporter demands measured per-LCSC rotation rows for 4 codes this board places (C192421 U1, C22359707 LS1, C2480 D2, C559105 D3) and the 57-row authority table has none of them. All four MEASURED this session; rows reported to the orchestrator (table owner). Secondary blocker: skills/ working tree is dirty (peer rotation-tool checkouts) so release_git_dirty cannot report clean for the stamp."
measure: "value check: 10/10 value-bearing BOM rows reconciled via ledger, 0 MISMATCH, 0 UNVERIFIABLE (21 R/C refdes); DRC --severity-all --refill-zones --schematic-parity 0/0/0 on staged source; policy_audit 0 FAIL (26 PASS/2 WAIVED/7 HUMAN/5 N-A); freshness PASS in --bom-only-supersede v1.0 mode (fab delta = 2 rows REMOVED J1,MK1, 0 added/edited; one self-inflicted kicad_prl dropping removed); P-FACT OK (3/7 yaml declare asserts, 4 graded); A-POP PASS (39 fp, 26 CPL, 13 declared); A-POS worst 0.00000mm; A-STOCK live PASS 15/15 (LS1 C22359707 stock=69); jlc_twin exit 0, 26 OK, 2 ADJUDICATED-PAD-GEOM (U1, D3, both pre-characterized), bodies 26/26; contracts_audit 187 files 0 violations"
state:   blocked
stage:   sealed
step:    "v1.1 SEALED: 07_releases/crow-mic-pod-v2-v1.1-2026-07-25 (seal c636241 on source 4f8a57b). BOM-only supersede of v1.0 (MK1 + J1 rows removed — they stalled JLC's BOM/CPL matcher). Copper unchanged, proven by sha256 (18/19 payload identical) + gerber re-plot 11/11. Independent audit 2026-07-26: no DO-NOT-ORDER; findings IA-1..IA-5 all fixed pre-seal and dispositioned."
measure: "seal-day gates all re-run + persisted: DRC 0/0/0; ERC 0/176; parity 78/78 nodes PASS; A-ROT 26/26 sourced (61-row table, this board's 4 rows landed f9eee3f); A-POL human gate = U1 only (exporter-generated); A-POP 39/26/13; A-POS 0.00000mm; A-STOCK 15/15 (LS1 69, delta note); M-BOM PASS; passive-value 10/10 rows 0 findings; twin exit 0, 26 OK, bodies 26/26 (--cpl); policy_audit 0 FAIL incl. M-REL vs stamped manifest; freshness PASS (bom-only mode); contracts_audit 0 violations (5 contracts re-synced, root strays removed, 08_reviews renamed to pattern); MANIFEST 58 files hashed; git_dirty false TOOL-verified"
state:   done
next:    "Order per v1.1 ORDER_README: JLC preview human gate on U1 pin-1 (CPL 270); NEVER plug into PoE/Ethernet (ADR-0005); LS1 C22359707 stock re-check on order day (69, trend 182->104->69); enclosure panel-cutout check. v-next work order: fix the 2 dead .kicad_dru rules (R-RULES waiver is REQUIRED-at-next-respin)."
op_pid:
updated: 2026-07-26T10:05:00
