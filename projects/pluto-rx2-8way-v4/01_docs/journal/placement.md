# Placement journal

## 2026-07-31 19:25 — start
- did: Generated the four-layer carrier from floorplan.yaml with all 28 footprints anchored and the RP2040-Zero underside/USB-access keepouts enforced.
- result: 28 footprints plus 4 mounting holes placed; P-COLLIDE found 0 pad shorts and 0 anchored courtyard overlaps; placement gates found 0 failures and 0 warnings.
- next: Prove that declared widths can leave the placed lands.

## 2026-07-31 19:34 — iterate 1
- did: Added bounded 0.14 mm launch clearances for the PE42482 RF/control escape and a 0.20 mm scoped width floor for its 3V3 land.
- result: P-LAND changed from two unlandable pads to PASS: 50/130 copper pads graded, 1 scoped floor, 14 scoped clearances, 0 failures.
- next: Start a fresh bounded route race; do not reuse prior-board copper.

## 2026-07-31 19:36 — finish
- did: Ran tier consistency immediately before routing.
- result: 0 failures and 2 declared scoped-clearance warnings; the final DRC owns the geometry verdict.
- next: Route three candidates and promote only the measured winner.
