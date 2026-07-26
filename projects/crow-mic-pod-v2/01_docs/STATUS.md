# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. OVERWRITTEN (not appended) at every transition; history
lives in `journal/<stage>.md`. Read by `skills/kicad-pcb/scripts/pcb_status.py`.

<!-- reader parses from here down -->
stage:   seal
step:    "v1.1 staging RE-VERIFIED 2026-07-26 (frozen 2026-07-25, digest c9804afe). Seal is BLOCKED on A-ROT: the hardened exporter demands measured per-LCSC rotation rows for 4 codes this board places (C192421 U1, C22359707 LS1, C2480 D2, C559105 D3) and the 57-row authority table has none of them. All four MEASURED this session; rows reported to the orchestrator (table owner). Secondary blocker: skills/ working tree is dirty (peer rotation-tool checkouts) so release_git_dirty cannot report clean for the stamp."
measure: "value check: 10/10 value-bearing BOM rows reconciled via ledger, 0 MISMATCH, 0 UNVERIFIABLE (21 R/C refdes); DRC --severity-all --refill-zones --schematic-parity 0/0/0 on staged source; policy_audit 0 FAIL (26 PASS/2 WAIVED/7 HUMAN/5 N-A); freshness PASS in --bom-only-supersede v1.0 mode (fab delta = 2 rows REMOVED J1,MK1, 0 added/edited; one self-inflicted kicad_prl dropping removed); P-FACT OK (3/7 yaml declare asserts, 4 graded); A-POP PASS (39 fp, 26 CPL, 13 declared); A-POS worst 0.00000mm; A-STOCK live PASS 15/15 (LS1 C22359707 stock=69); jlc_twin exit 0, 26 OK, 2 ADJUDICATED-PAD-GEOM (U1, D3, both pre-characterized), bodies 26/26; contracts_audit 187 files 0 violations"
state:   blocked
next:    "Orchestrator lands the 4 rotation rows in jlc_lcsc_rotations.csv (D2 C2480 offset 0 two-channel via diode glyph; D3 C559105 offset 0 two-channel via cathode band + corner marks; U1 C192421 270 single-channel HUMAN GATE, note twin fitted 90 vs db 270 disagreement; LS1 C22359707 0 single-channel HUMAN GATE, model pads 3/4 numbered opposite board, both NC) -> re-export to proof, diff vs staged fab (CPL must stay byte-identical to v1.0 for bom-only mode or v1.1 becomes a fuller supersede) -> peer skills/ dirt clears -> 2-commit seal + SUPERSEDED.md on v1.0"
op_pid:
updated: 2026-07-26T09:20:00
