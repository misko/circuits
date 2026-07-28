# STATUS beacon — the live head of the journal

This file is the ONE place a coordinator reads to know, in a glance, where this
board is between gates. OVERWRITTEN (not appended) at every transition; history
lives in `journal/<stage>.md`. Read by `skills/kicad-pcb/scripts/pcb_status.py`,
graded by `skills/kicad-pcb/scripts/status_beacon_check.py` (canon M-BEACON).

<!-- reader parses from here down -->
stage:   seal
step:    "v1.3 SEALED and LIVE: 07_releases/crow-mic-pod-v2-v1.3-2026-07-27 — the only release of this board with no SUPERSEDED.md. F-LEGIBLE (ADR-0006) supersede of v1.2: v1.2's fab/bom.csv carried 21 findings (15 F-MPN blank MPNs, 5 F-WORDS Comments that were LCSC codes, 1 F-ENCODE ohm sign with no BOM marker) and v1.3 ships 0. NO COPPER CHANGE, measured: source/crow_mic_pod_v2.kicad_pcb md5 c7b8512ccf0810997116c8c2e59dcad9 identical to v1.2's and to 04_kicad/'s, gerbers+drills re-plot 13/13 byte-identical, fab/cpl.csv byte-identical. v1.2 is superseded but NOT DO-NOT-ORDER."
measure: "quoted from the SEALED archive, not re-measured here — crow-mic-pod-v2-v1.3-2026-07-27/MANIFEST.txt `gates (MEASURED this release, against the STAGED archive)`: DRC --severity-all --refill-zones --schematic-parity 0/0/0; ERC 0 errors (176 warnings); A-POP PASS 39 board footprints / 26 CPL / 13 unpopulated / 13 declared; A-POS worst datum residual 0.00000 mm over 26 rows by TWO independent readers; A-ROT this board's 4 codes (U1 270, LS1 0, D2 0, D3 0) are MEASURED rows in the 61-row fleet authority table; F-LEGIBLE 0 findings, 15/15 coded rows carry an MPN."
state:   done
next:    "ORDER-DAY, from v1.3 ORDER_README: NEVER plug into PoE/Ethernet (ADR-0005 accepted waiver, section 0); JLC placement-preview eyeball on U1 pin 1 (CPL 270); LS1 C22359707 stock re-check on the day you pay (69 at seal, trend 182->104->69 over 7 days, single-source Extended); J1 pad-1 -> contact-1 continuity backstop on the first assembled board; enclosure panel cutout vs the 1.05 mm RJ45 mouth overhang."
op_pid:
updated: 2026-07-27T18:39:08
