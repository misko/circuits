# Dispositions — cooksense v1.1 fresh-lens findings (2026-07-24)

Fresh zero-context lens verdict: **ORDER — 0 P0 / 0 P1 / 6 P2** (all
Accept-with-note). Lens report verbatim: `fresh_lens.md`. Independent
measurements converged with the project's own gates (creepage 6.120mm,
binding pair K_D1 intra-relay columns; keypad-copper-to-plane-fill 6.63mm;
12x 0.60mm slots; 15.24mm pitch x11 exact, strict rot180/0 alternation =
anti-parallel adjacent coils; outline 188.10 x 92.10; 0 pads outside; DRC
0/0/0).

| # | finding | sev | evidence | disposition |
|---|---|---|---|---|
| 1 | Creepage floor is intra-relay footprint geometry, 6.120mm — only 0.12mm over the 6.0mm spec | P2 | lens + audit_board both measure 6.12mm (pad columns 7.62mm c-c − 2x0.75 pad half) | Accept-with-note. The floor is FIXED by the DIP05 footprint (same floor v1.0 sealed with); it cannot erode by routing (DRC deny comb + wave keepouts). Noted for future spec tightening. |
| 2 | East-end pocket has no south milled slot (asymmetric vs west end) | P2 | measured 6.63mm construction gap at the east pocket mouth; slot skipped for edge-web integrity (<3mm to board edge) | Accept-with-note (lens: "passes as-is; do not re-race"). Documented in floorplan.yaml cutouts comment. |
| 3 | CPL carries 14 hand-solder THT rows -> JLC preview will warn unmatched | P2 | cpl.csv vs bom.csv rows | ORDER_README Assembly row now instructs: expect and IGNORE the warning; do not let JLC fix/delete. |
| 4 | ERC 1169 warnings / 0 errors | P2 | verification/erc.json | Accept-with-note: the converter .kicad_sch is the machine artifact (ADR-0002); gate is 0 ERRORS. Compensating gates: E-INV 17/17, count_parity 191x4, net_label_survival 155/155, netlist byte-identical to sealed v1.0. Same state v1.0 sealed with. |
| 5 | Thin stock: F1 C89650=244; C25744 10k line fell 192k->12.6k in a day (API also gave transient 0s) | P2 | verification/stock_check.txt + direct API probes | ORDER_README §3 order-day recheck MANDATORY; approved 10k substitute class listed (C60490). |
| 6 | Netlist-identical claim needs documentation | P2 | semantic_battery.txt: byte-identical diff vs v1.0 release source netlist | Documented in semantic_battery.txt + parity.md; licenses the scoped re-verify (carried pin/render reviews). |

v1.0 carried dispositions: `dispositions_v10_carried.md` (netlist/parts
untouched — those closures remain valid).
