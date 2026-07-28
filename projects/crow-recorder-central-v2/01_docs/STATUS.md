# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. It is OVERWRITTEN (not appended) at every transition —
the append-only history lives in `journal/<stage>.md`; this is only the current
frame.

Read by `skills/kicad-pcb/scripts/pcb_status.py` and graded against the tree by
`skills/kicad-pcb/scripts/status_beacon_check.py` (canon M-BEACON). Everything
below the fence is `key: value` (one per line); `#` lines and blanks are
ignored by the reader.

<!-- reader parses from here down -->
stage:   seal
step:    "v1.6 SEALED and LIVE: 07_releases/crow-recorder-central-v2-v1.6-2026-07-27 — the only release of this board with no SUPERSEDED.md. LEGIBLE-BOM supersede of v1.5 plus one rail declaration; NO COPPER CHANGE and v1.5 is NOT DO-NOT-ORDER. v1.5's fab/bom.csv was uploaded to JLCPCB and the parts 'were not being picked up by their web processing': graded as the RECIPIENT parses it (F-LEGIBLE, ADR-0006) it carries 72 findings (47 F-MPN, 24 F-WORDS, 1 F-ENCODE); v1.6 carries 0. Second half of the release: E-TOPO had reported UNGRADED CONVERTERS 2 of 3 because the 1V8 (U9) and 3V3A (U10) LDO rails lived in a COMMENT in power_tree.yaml — both now declared and graded on dropout and dissipation."
measure: "quoted from the SEALED archive, not re-measured here — crow-recorder-central-v2-v1.6-2026-07-27/MANIFEST.txt `gates:`: DRC 0/0/0 (--severity-all --refill-zones --schematic-parity) AND standalone-archive DRC on source/ alone 0/0/0; ERC 0 errors (1211 warnings, unchanged from v1.5); netlist parity 0 REAL discrepancies (116 nets, 598 connected nodes both sides); count parity 199/199/199/199; audit_board OK; A-POS worst datum residual 0.00050 mm over all 174 rows (tol 0.05); A-ROT all 174 rotations sourced, 0 ROT-DB-SUGGEST; A-POL 0 single-channel refs; A-POP 0 findings (203 footprints, 174 CPL, 29 unpopulated); A-STOCK PASS re-queried 2026-07-27. Copper identity measured three ways: .kicad_pcb md5 de39e145e856cb14d491770c77d1ec0a identical to v1.5's and to 04_kicad/'s, gerbers+drills re-plot 17/17 byte-identical, fab/cpl.csv byte-identical."
state:   done
next:    "PRE-ORDER, none of it waivable here (v1.6 MANIFEST `pre_order:` + `rework:`): F-ECHO — after uploading fab/bom.csv, save JLC's OWN resolved part table and diff it back (bom_legibility_check.py <bom> --echo <saved> vs verification/bom_echo_gate.txt, 47 lines); the A-POL JLC order-preview human gate; the order-day stock recheck on the Extended-tier parts; and the BLOCKING 33pF C0G feedforward rework on all 5 boards (one across R_fb1a, one across R_fb2a — AP61102 DS42004 Rev6-2 Table 1) before the first-article gates."
op_pid:
updated: 2026-07-27T18:39:08
