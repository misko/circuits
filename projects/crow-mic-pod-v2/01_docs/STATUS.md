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
step:    "v1.2 SEALED: 07_releases/crow-mic-pod-v2-v1.2-2026-07-26 (seal fe5f882, input cf41646). PACKAGING supersede of v1.1 (seal c636241), chosen by the user: assembly drawing merged to the single 2-page pdf/assembly.pdf the contract requires (canon A-EVID). NOT a board change — fab/source/3d/verification byte-identical to v1.1 (diff -rq: assembly files are the only delta); v1.1 gerbers remain orderable, its SUPERSEDED.md says so."
measure: "A-EVID OK 31 required present + 1 conditional absent (3d gltf); freshness PASS in --docs-only-supersede v1.1 mode; policy_audit 0 FAIL incl. M-REL (git_sha cf41646, git_dirty false TOOL-verified, 57 files hashed); check-ignore sweep empty; assembly.pdf = 2 pages (front, back), pdfunite of v1.1's own pair"
state:   done
next:    "Order per v1.2 ORDER_README: JLC preview human gate on U1 pin-1 (CPL 270); NEVER PoE (ADR-0005); LS1 C22359707 stock re-check on order day; enclosure cutout check. Upstream owed (reported): release_git_dirty cannot excuse the MODIFIED tracked CHANGELOG a second seal produces."
op_pid:
updated: 2026-07-26T12:15:00
