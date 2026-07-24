# DISPOSITIONS — interposer (Board C) v1.0, 2026-07-24

Sources: 2026-07-24_interposer-v1.0_{pin-review_connectors, render-review_full,
redteam_topology, redteam_layout}.md. Dispositions by the interposer board lead,
2026-07-24, all pre-seal (findings cost edits, not supersedes).

| # | Finding (severity) | Disposition | Evidence / change |
|---|---|---|---|
| I1 | No seated-visible pin-1 marker on the hand-solder ZIFs (render P2) | FIXED — "1"/"10" silk numerals added to the 10FDZ footprint, outside the housing outline so they stay visible with the connector seated; captions relocated to clear them; DRC re-measured 0/0/0 | commit 4358b0c + follow-ups; render pair regenerated |
| I2 | GH ribbon harness under-specified — same-side vs opposite-side crimp variants silently swap pin1<->pin10 (lens-a P1) | FIXED-IN-DOCS — ORDER_README "KEYPAD RIBBON" section specifies: 10-way GHR-10V-S both ends, contact-k -> contact-k, both housings crimped on the SAME conductor face with pin 1 on the SAME cable edge, planar U-bend mate; continuity-verify 1->1 and 10->10 before first use | ORDER_README.md (this release) |
| I3 | 10FDZ-BT land pattern is datasheet-derived, physical fit + circuit-1/boss end unconfirmed (lens-a P1 = pin-review QUESTION; the declared order gate) | DEFERRED (USER-HELD ORDER GATE) — LOUD ORDER_README bring-up ritual: verify drill pattern + polarization-peg position + circuit-1 end against a physical 10FDZ-BT BEFORE ordering fab; same class as v1.0 J_TC/J_PWR rituals (D9, ADR-0009) | 02_parts/10FDZ-BT/part.yaml NEEDS-PHYSICAL-CONFIRM; ORDER_README |
| I4 | SM10B-GHS-TB layout.notes contradicted the corrected pins.MP float rule (pin-review LOW, lens-a P2) | FIXED — stale tie-to-isolated-ground sentence replaced with the float rule | commit 4358b0c |
| I5 | Uncoded 10FDZ rows ride bom_jlc/cpl_jlc; GH Comment column carries the LCSC code (lens-a P2) | RECORDED + ORDER_README — hand-solder lines are DELIBERATELY uncoded per the fab skill; ORDER_README instructs deleting the two 10FDZ rows from any JLC assembly upload (fab is bare-board + 1 SMD part or full hand-solder) | ORDER_README hand-solder list |
| I6 | TP labels staggered between rows, count-across ambiguity (render P2) | RECORDED — next-rev candidate (per-pad callout layout); rows are on-column with the connector pin numbers 1..10 W->E and the 1/10 numerals (I1) anchor the count | render review #2 |
| I7 | No back-side silk ID (render P2) | RECORDED — next-rev candidate; floorplan captions are F.SilkS-only in the generic backend today | render review #3 |
| I8 | J_KEY_MATRIX refdes near edge clips at oblique angles (render P2) | RECORDED — legible in orthographic views; cosmetic | render review #4 |
| I9 | 3 near-zero-angle same-net junctions; via annular 0.15 vs 0.13 floor; GH fanout wedges (lens-b P2 x3) | RECORDED — all DRC-silent, measured cosmetic; annular meets the declared jlc_2layer_default tier floor | redteam_layout |
