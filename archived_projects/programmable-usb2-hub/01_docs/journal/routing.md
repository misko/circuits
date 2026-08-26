# Routing journal

## 2026-07-31 17:02 — iterate 1
- did: Resumed the accelerated DRC cleanup, inspected the dirty tree and reclassified the saved cleanup2/cleanup3 authoritative KiCad JSON reports.
- result: MEASURED cleanup2 at 0 unconnected and 9 electrical violations (3 clearance, 6 hole_clearance) in five independent local clusters; cleanup3 regressed to 27 electrical violations including 12 shorts and is rejected.
- next: Reproduce cleanup2 from declarative placement/route sources, batch-fix the five clusters, and use local electrical DRC between batches.

## 2026-07-31 17:31 — iterate 2
- did: Prototyped and source-integrated the five local fixes, then replayed placement/import/stitch through the fresh-reload heal barrier.
- result: MEASURED scratch cleanup9 reached 0 electrical violations with one GND zone split; first source replay was rejected because moving R204 in the pre-legalization anchor set shifted unrelated B-channel passives and produced 124 violations / 14 unconnected in the diagnostic snapshot.
- next: Apply the R204 move only as a post-anchor so the original legalizer sequence and promoted-route pad field remain unchanged, then rerun the source replay.

## 2026-07-31 18:03 — iterate 3
- did: Promoted the proven R36/R422/R204 placement, P1_DATA/FB_A/COMP_B/P4_ILIM/HUB_VBUS_DET routing geometry, USB-B silkscreen cleanup, final-fill fresh reload, constrained A*, and connected-seed-pad rescue behavior into the declarative route chain and shared routing tools; replayed the canonical board from those sources.
- result: MEASURED canonical `kicad-cli pcb drc --severity-all --refill-zones --schematic-parity` gate is green at 0 violations / 0 unconnected items / 0 schematic parity issues; report saved as `06_build/drc/gate.json`.
- next: Publish only the hub project and its required shared routing-tool changes from a clean `origin/main` feature branch; exclude unrelated dirty-tree work and intermediate routing diagnostics.

## 2026-07-31 20:50 — finish
- did: Cleared M-BOM by exact-code catalog verification of 15 unique LCSC passive codes, then ran `pcb_flow.py layout-seal` twice because the conductor changed during the first run; validated the second content-addressed handoff against the current tools.
- result: MEASURED P-ESC 26/26, P-LAND 304/304, authoritative KiCad DRC 0 violations / 0 unconnected / 0 schematic parity issues, and a valid 2070-byte `stage: layout_sealed` handoff.
- next: Enter the JLC fabrication/assembly preflight; the layout seal is not an orderable-release seal.

## 2026-08-02 04:36 — stuck / backtrack to placement and package selection
- did: Applied D-BACK after the release review proved the earlier DRC-clean board was the wrong architectural/placement state. Rebuilt the 211-component 2 A design, hardened P-ADJ with exact intended partners, repacked the TPS259470/AP63203 cells, and re-ran independent placement/pin reviews. The second layout review closed those two findings but retained P0s on the LTC3889 and LMR36510 local networks. The JLC twin independently exposed generic-footprint mismatches on U3, L6, and Q7/Q8.
- result: MEASURED the exact TI, TDK, and Diodes land drawings and replaced all three generic lands in declarative dossiers/library source. Q7/Q8 and U3 now fit JLC CAD without PAD-GEOM findings; L6 differs from JLC by only the documented 0.30 mm center-span choice and still requires manufacturer-evidence adjudication. The current regenerated placement passes P-COLLIDE, placement geometry, P-PADSEP, and the closed intended-part P-ADJ budgets. The official Analog Devices DC2595A editable PADS design was measured and added as tier-2 precedent rather than relying on qualitative courtyard proximity.
- next: Obtain fresh exact-hash SOUND topology/pin/layout verdicts on the corrected package and power-cell state. Do not resume routing unless all three are SOUND; then rebuild the route from the new pad field rather than replaying the superseded release artifact.
