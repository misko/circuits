# STATUS beacon — usb-hub-3s-v3 (live head of the journal)

<!-- reader parses from here down -->
stage:   v1.4-SEALED
step:    "SEALED: 07_releases/v1.4-2026-07-23 (source S=764c7c7, seal=bc3855e) — DOCS-ONLY supersede of v1.3 (fab/source/3d/pdf byte-identical; README polarity/F1/margin fixes). ORDER FROM v1.4."
measure: "M-BOM PASS; policy_audit 0 FAIL (PASS=28) incl. M-REL over final manifest; freshness PASS (--allow-identical x9, evidence waiver); docfix confirmation PASS; manifest self-check 30/30 bidirectional. Tolerance-incl 5VC 5.227-5.479V, headroom 597mV vs 440mV = PASS (157mV slack)."
state:   done
next:    "order-day: jlc_stock recheck (R12/F2/D5), JLC preview + mark F1/SW1 DNP (2 unmatched designators expected), SW1 pitch confirm; Q0-Q7 bench gate before Pi. Harvest flags: freshness --docs-only-supersede mode (builder in flight), power_tree.yaml tolerance-incl corner sync, proven-parts harvest, kicad_sch_parity fix."
op_pid:
updated: 2026-07-23T20:35:00-07:00
