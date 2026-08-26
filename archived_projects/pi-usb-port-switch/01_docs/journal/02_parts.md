# Parts journal

## 2026-08-14 22:38 — start
- did: entered the binding `02_parts/` contract after commission passed prompt-hash, M-BEACON, D-SPEC/E-PATH and ADR-structure checks.
- result: MEASURED seven hard part functions to resolve: USB 3 redriver, USB 2 switch, per-port VBUS switch, six-line ESD, USB 3 Type-A, USB 3 Type-B, and the local 3.3 V/control implementation; no firmware or programmable part is in scope.
- next: fetch authoritative selected-part PDFs, extract physical pin maps and layout requirements, then run Q-2SOURCE and P-ESC before schematic authoring.

## 2026-08-14 22:47 — iterate 1
- did: ran ad-hoc P-ESC checks for the selected USB 3 redriver, USB 2 switch and six-line ESD package pitches against the declared JLC tier.
- result: MEASURED the 24-pin 0.5 mm VQFN and 14-pin 0.5 mm USON as `jlc_4layer_advanced`; the 10-pin 0.4 mm USB 2 switch is conditional on outward-only local escape. ADR-0005 supersedes the standard-tier ceiling so the USB 3 attempt remains in scope.
- next: bind each exact package to its dossier and reserve outward local escape corridors in the floorplan.

## 2026-08-14 23:18 — iterate 2
- did: compared the initially considered TPS2552 against the complete 0.9A VBUS path and replaced it with active-high TPS2557DRBR; audited fuse, reverse-polarity FET, switch and connector resistance together.
- result: MEASURED TPS2557 guarantees 35mOhm at 125C and its 100kOhm ILIM setting covers 0.9A without exceeding the connector rating. The shared-path audit rejected the provisional 17mOhm DMP3013SFV-7 in favor of full-production 4.3mOhm AON6403 and proved that a 5.0V board-terminal minimum still cannot honestly guarantee 4.75V at the loaded plug, so ADR-0006 binds a regulated 5.15-5.25V input.
- next: lock active, two-source USB 3 Type-A/Type-B connector MPNs and complete the exact candidate BOM/Q-2SOURCE gate.

## 2026-08-14 23:58 — iterate 3
- did: replaced the generic GPIO header, power terminal and small-signal MOSFET catalog placeholders with exact Wurth 61304021121, Phoenix 1935161 and Diodes 2N7002-7-F identities; added exact dossiers for every selected passive and assembled a fixed-reference five-board candidate BOM.
- result: MEASURED P-ESC PASS 14/14 for the original hard-part set before the passive dossiers were added. The first composed-source run then correctly failed closed because passives without dossiers were outside its coverage denominator. It also exposed a persistent JLC API HTTP 500 and null Mouser availability record for TLV1117LV33DCYR, despite a live exact LCSC product page. That part was rejected at Q-2SOURCE rather than waived. Exact, active TLV76133DCYR retains the SOT-223 pinout, supports ceramic capacitors, and has JLC C7527500 plus live Mouser/DigiKey catalog paths.
- thermal decision: the 3.3V rail remains linear to avoid adding a switching cell beside four 5Gbps paths, but this is not treated as free. At the 0.45A bound its worst declared dissipation is about 0.904W. The OUT/tab heat spreader, 35C JEDEC-board budget, and a worst-mode first-article thermal measurement are binding; failure reopens a TO-252 or synchronous-buck revision.
- next: rerun YAML/P-ESC across the complete 27-row selected set, obtain a clean JLC stock sidecar, and compose two independent authorized source pools per exact MPN before schematic capture.

## 2026-08-14 23:59 — iterate 4
- did: treated the live source check as a selection gate rather than a paperwork exercise. DigiKey showed the selected 5% 2.2ohm resistor at zero stock, and AON6403 lifecycle evidence conflicted between a full-production manufacturer page and a distributor `Not For New Designs` classification.
- result: replaced the resistor with exact 1% YAGEO RC0402FR-072R2L (JLC C327251 and stocked DigiKey path) and replaced the input P-FET with active Diodes DMP3007SPS-13 (JLC C397981 and stocked Mouser/DigiKey paths). The P-FET's higher 16mOhm 25C maximum is accepted explicitly: the hot allocation rises to 25mOhm and the total per-port VBUS path budget rises from 320mOhm to 400mOhm, which still meets 4.75V from the bound 5.15V board-terminal minimum at 0.9A but leaves only the declared measurement margin.
- next: regenerate the JLC sidecar and composed source report with these exact identities; no schematic authoring begins until all 27 rows clear Q-2SOURCE.

## 2026-08-15 00:28 — finish
- did: regenerated the five-board candidate BOM, fresh JLC sidecar and composed authorized-pool report after both selection backtracks; re-ran dossier YAML parsing, pinned-PDF hashes, package escape grading and the shopping-list regression battery.
- result: MEASURED 27/27 exact dossiers with matching local manufacturer-document hashes, P-ESC 27/27, Q-2SOURCE composed pools 27/27 and fresh JLC stock PASS 24/24 coded rows. The three uncoded items are deliberate: the user-fit fuse and the two through-hole USB connectors qualify through independent global distributor pools rather than fake LCSC identities. `tests/t1_shopping_list.py` passes 27/27 while all 14 known-bad fixtures continue to fail their intended checkers.
- time: the expensive work was not PDF retrieval; it was resolving exact identity, lifecycle and distributor disagreement. That work prevented three weak choices from entering the schematic: TLV1117LV33DCYR, AON6403 and the zero-stock 5% 2.2-ohm resistor.
- next: enter the source/floorplan gate with the 27 exact identities frozen; do not reopen a part unless an electrical, physical or order-time gate produces evidence.
