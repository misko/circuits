# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame. Rewrite it at every stage enter/finish, every iterate, and IMMEDIATELY
BEFORE and AFTER every long blocking op (see SKILL.md "Journal discipline").

Read by `skills/kicad-pcb/scripts/pcb_status.py`. Everything below the fence is
`key: value` (one per line); `#` lines and blanks are ignored by the reader.

Multi-board projects: one beacon PER board, named `STATUS-<board>.md`
(mirroring the per-board `journal/<stage>.md` suffix). A single-board
project uses this bare `STATUS.md`.

## Schema

| field | meaning | vocabulary |
|---|---|---|
| `stage` | which pipeline stage the board is in | `commission` \| `parts` \| `schematic` \| `placement` \| `routing` \| `verify` \| `seal` |
| `step` | the specific thing happening RIGHT NOW, one line | free text |
| `measure` | the last MEASURED numbers (gate output, counts) — never hope | free text; the rebuild loop tees its last line here |
| `state` | the coordinator's traffic light | `working` (progressing) \| `blocked` (STOPPED, escalated to coordinator) \| `done` (this stage's gate is green) |
| `next` | what happens on the next transition | free text |
| `op_pid` | pid of the running long op, or empty when idle | integer or empty |
| `updated` | when this frame was written, ISO-8601 local | `YYYY-MM-DDTHH:MM:SS` |

`state: working` + a fresh `updated` + a live `op_pid` = progressing (coordinator
POLLS, does not interrupt). `state: working` + a STALE `updated` + no live
`op_pid` = STALLED (the reader flags it). `state: blocked` = a decision or
D-BACK wall the agent has PUSHED up — the coordinator acts. `state: done` =
terminal for this stage.

<!-- reader parses from here down -->
stage:   seal
step:    "THE ARCHIVE IS RE-STAGED AND ARTIFACT-COMPLETE at 06_build/staging/ (81 files, MANIFEST bijective both ways, 0 hash mismatches). The seal judge's blockers are CLOSED — A-EVID OK 33/33, A-STOCK and A-BUY now GRADE instead of reaching a zero denominator, fence_apertures re-run to 0, ORDER_README names the fab options, MANIFEST stamped. THE COPPER DID NOT MOVE: footprint signature, 199 tracks, 3446 vias, 6 zones IDENTICAL to the archive the lenses read. NOT SEALED and 07_releases/ is still empty. HANDOFF at a gate boundary: what remains is one converter patch outside this partition, and the fresh scoped re-gate."
measure: "A-EVID OK 33 required present, RAW EXIT 0 (was FAIL, 10 missing). release_freshness: A-STOCK 11 graded line(s) verdict=PASS, A-BUY SOURCING CLEAR over 11 coded+placed lines, SOURCING: CLEAR (both were a ZERO DENOMINATOR emitting NOTES before the exporter fix); DESIGN FAIL 10, and ALL TEN are in REVIEW DOCUMENTS — 8 EVIDENCE-PATH-MISMATCH naming the 07_releases/v1.0-2026-07-30/ that was never created, 2 REVIEW-NO-VERDICT from the 40-line header window. DRC 0/0/0 RAW EXIT 0; standalone archive DRC, on a copy of source/ OUTSIDE the repo, also 0/0/0 RAW EXIT 0 (verification/standalone_archive_drc.json). netlist parity 0 over 24 nets / 114 nodes. ERC 0 errors / 209 warnings (120 endpoint_off_grid + 89 lib_symbol_issues). fence_apertures 0 apertures over 3433 PCB_VIA + 40 PTH = 3473 elements (the pre-fix file shipped a phantom 1.9000 mm). fence_pitch worst 1.1769 vs 1.1910, 22 arm-sides 0 OVER. P-LAND 47 graded/130 pads 0 failing. R-LEN PASS 8/8. twin 26 OK/56 rows, bodies 27/27, 0 CRITICAL. A-RENDER 11/11 within 1.00 mm. A-POP PASS against the archive (RAW EXIT 0). M-BOM PASS. F-LEGIBLE OK 13 checks. P-FACT 7/8 graded (was 6/8). stock 11/11 >= 5x live. MANIFEST 81 rows <-> 81 files, 0 rows without a file, 0 files without a row, 0 hash/size mismatches on an independent re-hash; 0 of 82 paths gitignored at the 07_releases/ path they would occupy; 0 .kicad_prl anywhere. policy_audit FAIL=2 PASS=30 HUMAN=6 N-A=7. Suite in THIS worktree (/home/mouse9911/gits/circuits, main): TOTAL 1114 passed, 12 failed, 664 known-bad — the 12 are fleet-census/ratchet floors perturbed by untracked sibling state, byte-identical set to the pre-change control minus the 4 this change fixed."
state:   blocked
next:    "THREE THINGS, none of them copper. (1) S-OCCL FAIL=13 is a CONVERTER defect and is OUTSIDE this partition: 12 of the 13 are text-over-WIRE, a population sch_occlusion.py only gained on 2026-07-31, and the four text-over-TEXT pairs the r2 render lens found are GONE. The de-collision pass in circuit_json_to_kicad_sch.py must treat a wire as an obstacle. NO WAIVER — this project withdrew its S-OCCL waiver on 2026-07-30 after the render lens falsified its premise, and policy_waivers.yaml carries zero entries with that history in it. (2) THE FRESH SCOPED RE-GATE. The shipped redteam_topology.md / redteam_layout.md are the r2 files, VOID by material change, present only because the contract requires those two names and an absent required artifact is worse than a stale one; the re-gate REPLACES them. It must write its verdict keys INSIDE the first 40 lines (the r2 files state theirs at 211-212 and 77-78, which is why M-REV reports REVIEW-NO-VERDICT — a false reason for a true refusal) and must name the archive it actually graded, which is what closes the 8 EVIDENCE-PATH-MISMATCH findings. DO NOT close them by sealing under the name v1.0-2026-07-30: that turns the gate green without making one word of the evidence truer. Review files are append-only VERBATIM (08_reviews/contracts.md) — the verdicts may NOT be hoisted by editing them. (3) M-REL IS UNGRADED HERE and its verdict must not be quoted: its regex at policy_audit.py:1643-1646 admits two MANIFEST layouts and this archive ships a third, and the zero-coverage backstop at :1660 tests for the literal 'sha256:' which this banner does not contain, so it verifies ZERO of the 81 rows. Owned by task #64. ALSO OPEN: policy_audit A-POP FAIL is an artefact of 07_releases/ being empty (the same gate against the archive is PASS, exit 0) and closes at the seal; git_dirty is TRUE only because a sibling workflow holds skills/kicad-pcb/scripts/route_and_stitch_generic.py uncommitted."
op_pid:
updated: 2026-07-31T10:40:00
