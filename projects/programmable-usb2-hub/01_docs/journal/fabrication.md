# Fabrication journal

## 2026-07-31 20:58 — start

- did: Exported a diagnostic JLC package after the valid canonical layout seal and ran rotation, population, datum, BOM-legibility, and assembly coverage checks.
- result: MEASURED BOM 60/60 coded lines and CPL 195 placements; A-ROT blocks 25 placements over 15 codes; A-POP correctly blocks the real through-hole refs F1/J1/J2/J7. J3-J6 are source-owned as not assembled and excluded from position output.
- next: Capture order-day stock, then hand off the external fabrication decisions without treating the diagnostic package as orderable.

## 2026-07-31 21:10 — blocked

- did: Ran the five-board-minimum catalog stock snapshot and separated early deterministic PCBA-readiness checks from the order-day volatile check.
- result: MEASURED A-STOCK passes 58/60 lines; C23017 has stock 3 for quantity 2/board and C780769 has stock 1 for quantity 1/board. The deterministic rotation and process blockers could and should have been detected after part/footprint/assembly freeze, before routing; only the final stock/uploader result must remain an order-day gate.
- next: Add an early PCBA-readiness dry run to future projects; for this release, obtain measured rotations, choose the F1/J1/J2/J7 population process, and choose stocked order codes before the full staged release battery.

## 2026-07-31 21:46 — sourcing iteration

- did: Added the Q-2SOURCE pre-selection rule, ran all 26 dossiers through the Mouser API, read the necessary exact DigiKey product pages, joined them with JLC stock, and corrected R102/R202 to source the specified 0.1% C728591 instead of generic C23017.
- result: MEASURED Q-2SOURCE passes 19/26 and rejects seven MPNs. The corrected BOM improves JLC A-STOCK from 58/60 to 59/60; only C780769/AP63203WU-7 remains low at JLC. A fresh canonical seal remains P-LAND 304/304 and KiCad 0/0/0 with a valid handoff.
- next: Treat the seven rejected selections as a design-input worklist, not release-time waivers; do not order the diagnostic package while sourcing, A-ROT, and A-POP remain red.

## 2026-07-31 22:54 — canonical fabrication handoff

- did: Replaced all seven Q-2SOURCE rejects with exact, dossier-reviewed MPNs; declared U4 consigned from Mouser/DigiKey; represented F1 honestly as two post-PCBA Keystone 3568 clips; declared J1/J2/J7 for JLC post-through-hole assembly; measured the 15 missing rotation codes; fixed EasyEDA zero-padded numeric pad handling in the shared rotation tool; rebuilt from declarative source and exported strictly.
- result: MEASURED Q-2SOURCE 26/26; canonical P-LAND 303/303 and KiCad DRC 0 violations / 0 unconnected / 0 parity; strict export 59/59 BOM lines and 194 CPL placements with A-ROT 194/194; BOM-source identity PASS; JLC live stock 58/59 with only planned-consigned C5248536 at zero. Twin mounted 194/194 bodies but remains red on 21 refs requiring datasheet-backed land-pattern/model adjudication. Fifteen exact codes remain on the mandatory first-order JLC preview human gate.
- next: Do not order this diagnostic package. Resolve the 21 twin-critical refs from manufacturer recommended-land-pattern evidence, run the visual polarity/registration review, then stage and seal a clean immutable release. Repeat Q-2SOURCE and the JLC uploader check on payment day.

## 2026-07-31 23:59 — publish handoff green

- did: Rebuilt and sealed the canonical declarative layout after promoting the proven route chain; regenerated the strict JLC package; reviewed all 21 exact-code twin-critical refs against the manufacturers' recommended lands; encoded the evidence in `03_src/rules/twin_adjudications.yaml`; and reran assembly, BOM-source, rotation-authority, twin, and regression gates.
- result: MEASURED P-LAND 302/302; authoritative KiCad DRC 0 violations / 0 unconnected / 0 parity; BOM 59/59 legible and source-identical; CPL 194/194 rotation-sourced; A-POP PASS; twin bodies 194/194 with zero unadjudicated critical refs; Q-2SOURCE remains 26/26; current JLC catalog stock is 58/59 with only planned-consigned U4 at zero.
- next: Publish only the exact manifest onto a clean `origin/main` feature branch. Before paying, repeat Q-2SOURCE and JLC allocation checks and accept the mandatory first-order 15-code placement-preview gate. No commit, push, staging release, or order was performed in this checkout.
